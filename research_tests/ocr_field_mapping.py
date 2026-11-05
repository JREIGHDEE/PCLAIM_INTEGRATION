"""Test 3b - OCR field mapping: from the scanned logbook to the form boxes,
with no staff correction.

    python -m research_tests.ocr_field_mapping [--scan scanner|phone] [--engine "PaddleOCR + Correction"]

The field mapping test (field_mapping.py) feeds the forms the CONFIRMED
values. This one feeds them what the OCR actually read. For each patient
of the answer key (sheet Patients), its logbook row ("Source (writer,
row)", e.g. W02 row 7) was read by the handwriting test; that reading
(outputs/handwriting/handwriting_results.xlsx, sheet Raw data, the chosen
scan and engine - by default the scanner and PaddleOCR + Correction, the
system's own pipeline) goes through the system unchanged:
  review_fields.suggest_parts (what the review page pre-fills)
  -> review_fields.normalize (staff press Submit without editing)
  -> case_bridge.draft_patient_and_encounter -> form_prefill.build_form_data
  -> the real forms page and the PDF it saves, as in field_mapping.py.

Every box of the expected box table is then scored twice:
  end-to-end    the box holds the answer-key value (OCR + mapping);
  mapping       the box holds what was READ, in the box's format - did the
                reading land in the right box? Address boxes are scored
                for mapping only when the address was read right (splitting
                a misread address has no independent answer).
A wrong box is put down to: row not detected, OCR misread (the reading is
in the right box), or mapping (the box does not hold what was read).

Typed values (the task packet: PINs, member type, ...) are given as in
field_mapping.py, except the member's name when the patient is the
member: the page then copies it from the (OCR'd) patient.
"""
import re

from research_tests import OUTPUTS, INPUTS, output_dir
from research_tests import field_mapping as fm
from research_tests.common import answer_key, excel, stats

TEST_KEY = "ocr_field_mapping"
TITLE = "OCR field mapping test"
HANDWRITING = OUTPUTS / "handwriting" / "handwriting_results.xlsx"
ENGINES = ("PaddleOCR + Correction", "PaddleOCR", "TesseractOCR + Correction", "TesseractOCR")

# Answer-key column of a box -> the logbook field it is read from.
SOURCE_FIELD = {
    "Last name": "Patient name", "First name": "Patient name", "Middle name": "Patient name",
    "Suffix": "Patient name", "Birthday": "Birthday",
    "Admitted date": "Admitted", "Admitted time": "Admitted", "Admitted AM/PM": "Admitted",
    "Went home date": "Went home", "Went home time": "Went home", "Went home AM/PM": "Went home",
    "Street": "Address", "Barangay": "Address", "City": "Address", "Province": "Address",
    "Reason for admission": "Reason for admission", "Final diagnosis": "Final diagnosis",
}
CAUSES = ("Correct", "OCR misread (in the right box)", "Mapping (not what was read)", "Row not detected",
          "Filled by a system rule (no usable reading)")


def read_ocr(scan, engine, path=HANDWRITING):
    """{(writer, row): {field: {"text", "truth", "detected", "exact"}}} from
    the handwriting test's Raw data."""
    import openpyxl
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found - run the handwriting test first.")
    ws = openpyxl.load_workbook(path, read_only=True)["Raw data"]
    rows = ws.iter_rows(values_only=True)
    head = next(rows)
    out = {}
    for values in rows:
        r = dict(zip(head, values))
        if r.get("Scan Method") != scan:
            continue
        detected = str(r.get("Detected") or "").lower() == "yes"
        out.setdefault((r["Writer ID"], int(r["Row"])), {})[r["Field"]] = {
            "text": str(r.get(engine) or "") if detected else "",
            "truth": str(r.get("Ground Truth") or ""), "detected": detected,
            "exact": str(r.get(f"{engine} Exact") or "") == "Yes"}
    return out


def source_of(p):
    m = re.fullmatch(r"\s*(W\d+)\s+row\s+(\d+)\s*", str(p.get("Source (writer, row)") or ""), re.I)
    if not m:
        raise ValueError(f"{p['Patient ID']}: no logbook row in 'Source (writer, row)'")
    return m.group(1).upper(), int(m.group(2))


def reviewed(cells):
    """The logbook values and the parts the review submits, from the OCR text
    alone: {category: text}, {category: parts}."""
    from philhealth import review_fields
    values, parts = {}, {}
    for field, cell in cells.items():
        category = answer_key.FIELD_TO_CATEGORY.get(field)
        text = cell["text"].strip()
        if not category or not text:
            continue
        values[category] = text
        parts[category] = review_fields.normalize(category, review_fields.suggest_parts(category, text))
    return values, parts


def as_read(p, parts):
    """The patient as the OCR read it (what the boxes should hold if the
    reading is mapped right): the answer-key row with the logbook columns
    replaced by the reviewed parts."""
    q = dict(p)
    name = parts.get("NAME") or {}
    q.update({"Last name": name.get("last", ""), "First name": name.get("first", ""),
              "Middle name": name.get("middle", ""), "Suffix": name.get("suffix", "")})
    q["Birthday"] = (parts.get("BDAY") or {}).get("date", "")
    for prefix, category in (("Admitted", "DATE & TIME OF ADMISSION"), ("Delivered", "DATE & TIME OF DELIVERY"),
                             ("Went home", "DATE & TIME OF DISCHARGE")):
        d = parts.get(category) or {}
        # A time is kept with its date (one datetime): a date that could not
        # be read takes its time with it (case_bridge), and the review would
        # ask staff for the date.
        timed = bool(d.get("date"))
        q[f"{prefix} date"], q[f"{prefix} hour"] = d.get("date", ""), d.get("hour", "") if timed else ""
        q[f"{prefix} minute"] = d.get("minute", "") if timed else ""
        q[f"{prefix} AM/PM"] = d.get("am_pm", "") if timed else ""
    q["Reason for admission"] = (parts.get("ADMITTING DIAGNOSIS") or {}).get("text", "")
    q["Final diagnosis"] = (parts.get("FINAL DIAGNOSIS") or {}).get("text", "")
    return q


def _plain(text):
    """Address text compared as written, punctuation aside ("PUROK 7, CABANTIAN" = "PUROK 7 CABANTIAN",
    but not "PUROK7 CABANTIAN")."""
    return " ".join(re.sub(r"[^A-Z0-9]", " ", str(text or "").upper()).split())


def run(progress, scan="scanner", engine="PaddleOCR + Correction", limit=20, no_pdf=False):
    if engine not in ENGINES:
        raise ValueError(f"engine must be one of: {', '.join(ENGINES)}")
    key_path = INPUTS / "answer_key.xlsx"
    expected = fm.load_expected()
    provisional = not all((r.get("Checked") or "").strip().lower() in ("yes", "y", "checked") for r in expected)
    patients = answer_key.patients(key_path)[:limit]
    ocr = read_ocr(scan, engine)
    info = {}                                   # Patient ID -> what was read

    for p in patients:
        cells = ocr.get(source_of(p), {})
        values, parts = reviewed(cells)
        info[p["Patient ID"]] = {
            "source": "{} row {}".format(*source_of(p)), "cells": cells, "values": values, "parts": parts,
            "read": as_read(p, parts),
            "address_ok": _plain(values.get("ADDRESS")) == _plain(p.get("Address")) and bool(p.get("Address")),
            "detected": any(c["detected"] for c in cells.values())}

    def populate(p):
        from philhealth import case_bridge, form_prefill
        i = info[p["Patient ID"]]
        patient, encounter, claim, warnings = case_bridge.draft_patient_and_encounter(
            dict(i["values"]), reviewed_parts=dict(i["parts"]))
        built = form_prefill.build_form_data({"patient": patient, "encounter": encounter, "claim": claim})
        saved = answer_key.claim_values(p) or {}
        if str(p.get("Member is patient") or "").lower() == "yes":    # the member follows the patient
            for k in ("memberLastName", "memberFirstName", "memberMiddleName"):
                saved.pop(k, None)
        return {"data": built["data"], "fields": built["fields"], "ocr_reference": built["ocr_reference"],
                "saved_values": saved}, warnings

    def line_extra(row, p, on_map, shown):
        i = info[p["Patient ID"]]
        field = SOURCE_FIELD.get(row["Answer-key value"])
        cell = i["cells"].get(field) if field else None
        if field == "Address" and not i["address_ok"]:
            read_value = None                   # misread address: its split has no independent answer
        else:
            read_value = fm.expected_value(row, i["read"]) if field else fm.expected_value(row, p)
        # Nothing usable was read for this box, yet it holds a value: a rule of
        # the system filled it (e.g. discharged 24 hours after admission ->
        # the admission time). Not a mapping of the reading: not scored for it.
        by_rule = bool(field) and read_value == "" and bool(shown.strip()) and bool(cell and cell["text"].strip())
        map_ok = None if read_value is None or by_rule else on_map and fm._same(read_value, shown, row["Format"])
        return {"keep": bool(read_value), "as_read": read_value, "map_ok": map_ok, "source_field": field or "(typed)",
                "ocr_text": cell["text"] if cell else "", "truth_text": cell["truth"] if cell else "",
                "row_detected": i["detected"], "by_rule": by_rule}

    lines, proof_entries, pdf_errors, browser, page_errors = fm.check_patients(
        progress, patients, populate, expected, output_dir(TEST_KEY), no_pdf, line_extra)

    progress(0.96, "Summarising")
    for l in lines:
        if l["correct"]:
            l["cause"] = CAUSES[0]
        elif not l["row_detected"]:
            l["cause"] = CAUSES[3]
        elif l["by_rule"]:
            l["cause"] = CAUSES[4]
        elif l["map_ok"] is False:
            l["cause"] = CAUSES[2]
        else:
            l["cause"] = CAUSES[1]
    end_to_end = fm.per_form_rows(lines)
    mapped = [l for l in lines if l["map_ok"] is not None]
    mapping = [r[:5] for r in fm.per_form_rows(mapped, key="map_ok")]
    by_cause = []
    for form in fm.FORMS + ("all",):
        group = [l for l in lines if form == "all" or l["form"] == form]
        if group:
            by_cause.append([fm.FORM_NAMES.get(form, "All forms"), len(group)]
                            + [sum(l["cause"] == c for l in group) for c in CAUSES])
    per_value = []
    for column in dict.fromkeys(l["column"] for l in lines):
        g = [l for l in lines if l["column"] == column]
        gm = [l for l in g if l["map_ok"] is not None]
        per_value.append([column, SOURCE_FIELD.get(column, "(typed)"), len(g),
                          stats.percent(sum(l["correct"] for l in g), len(g)), len(gm),
                          stats.percent(sum(bool(l["map_ok"]) for l in gm), len(gm))])
    readings = []
    for p in patients:
        i = info[p["Patient ID"]]
        for field in answer_key.FIELDS:
            c = i["cells"].get(field)
            if c:
                readings.append([p["Patient ID"], i["source"], field, c["truth"], c["text"],
                                 "Yes" if c["detected"] else "No", "Yes" if c["exact"] else "No"])
    mapping_errors = [l for l in lines if l["cause"] == CAUSES[2]]
    banner = ("PROVISIONAL - the expected box table (field_mapping_expected.csv) has not been checked against the "
              "paper forms yet (its Checked column).") if provisional else ""
    all_e, all_m = end_to_end[-1], mapping[-1] if mapping else None
    notes = ([banner] if banner else []) + [
        f"Input: what {engine} read on the {scan} scans of each patient's logbook row (handwriting test), "
        "through review_fields.suggest_parts + normalize as if staff submitted the review unedited.",
        "End-to-end = the box holds the answer-key value (Eq. 3.6 with OCR input).",
        "Mapping = the box holds what was read, in the box's format; address boxes only where the address was "
        "read right.",
        f"Run offline in {browser} with the real PClaimAssist/index.html; page errors: {len(page_errors)}.",
    ] + (["PDF errors: " + "; ".join(pdf_errors[:5])] if pdf_errors else [])
    sheets = [
        {"name": "3a End-to-end per form", "title": "Table - OCR to forms, end-to-end accuracy per form"
                                                     + (" - PROVISIONAL" if provisional else ""),
         "headers": ["Form", "Patients", "Boxes checked", "Correct", "End-to-end accuracy %",
                     "Boxes read on the PDF", "Printed = on screen %"],
         "rows": end_to_end, "bold_last": True, "notes": notes},
        {"name": "3b Mapping per form", "title": "Table - Field mapping accuracy on OCR input (did the reading land "
                                               "in the right box?)",
         "headers": ["Form", "Patients", "Boxes checked", "Holding what was read", "Mapping accuracy %"],
         "rows": mapping, "bold_last": True,
         "notes": ["Address boxes are left out where the address was misread."]},
        {"name": "3c Wrong boxes by cause", "title": "Table - Every box by cause",
         "headers": ["Form", "Boxes"] + list(CAUSES), "rows": by_cause, "bold_last": True},
        {"name": "3d Per value", "title": "Table - Accuracy per answer-key value",
         "headers": ["Answer-key value", "Logbook field", "Boxes", "End-to-end %", "Boxes scored for mapping",
                     "Mapping %"], "rows": per_value},
        {"name": "3e OCR readings used", "title": "Table - The OCR readings fed to the system",
         "headers": ["Patient", "Logbook row", "Field", "Ground truth", f"{engine} reading", "Detected", "Exact"],
         "rows": readings},
        {"name": "3f Mapping errors", "title": "Boxes that do not hold what was read",
         "headers": ["Patient", "Form", "Box", "Answer-key value", "OCR text", "Expected from the reading",
                     "On screen", "Printed"],
         "rows": [[l["patient"], fm.FORM_NAMES[l["form"]], l["box"], l["column"], l["ocr_text"], l["as_read"],
                   l["shown"], l["printed"]] for l in mapping_errors],
         "notes": ["None." if not mapping_errors else f"{len(mapping_errors)} boxes."]},
    ]
    raw = {"name": "Raw data",
           "headers": ["Patient", "Form", "Box", "Printed label", "Answer-key value", "Logbook field", "OCR text",
                       "Format", "Position", "Expected (answer key)", "Expected from the reading", "On screen",
                       "Printed", "End-to-end correct", "Mapping correct", "Cause"],
           "rows": [[l["patient"], fm.FORM_NAMES[l["form"]], l["box"], l["label"], l["column"], l["source_field"],
                     l["ocr_text"], l["format"], l["position"], l["expected"], l["as_read"], l["shown"], l["printed"],
                     "Yes" if l["correct"] else "No",
                     "" if l["map_ok"] is None else "Yes" if l["map_ok"] else "No", l["cause"]] for l in lines]}
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "ocr_field_mapping_results.xlsx", [raw] + sheets)
    fm_table_digest = fm.table_digest
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"scan": scan, "engine": engine, "provisional": provisional,
                                                      "expected_table": fm_table_digest()})
    outputs = [path]
    if not no_pdf:
        outputs.append(fm.write_proof_index(out / "proof", proof_entries, end_to_end, provisional))
        import json
        manifest = out / "proof" / "manifest.json"
        m = json.loads(manifest.read_text(encoding="utf-8"))
        m.update({"mapping": mapping, "by_cause": by_cause, "causes": list(CAUSES), "scan": scan, "engine": engine,
                  "readings": readings})
        manifest.write_text(json.dumps(m, indent=1, default=str), encoding="utf-8")
    progress(1.0, "Done")
    return {"outputs": outputs, "headline": [
        ["Patients", len(patients)], ["Boxes checked", all_e[2]],
        ["End-to-end accuracy % (OCR + mapping)", all_e[4]],
        ["Mapping accuracy % (holding what was read)", all_m[4] if all_m else None],
        ["Mapping errors", len(mapping_errors)]]}


def add_arguments(parser):
    parser.add_argument("--scan", default="scanner", choices=("scanner", "phone"))
    parser.add_argument("--engine", default="PaddleOCR + Correction", choices=ENGINES)
    parser.add_argument("--limit", type=int, default=20, help="patients to check (default 20)")
    parser.add_argument("--no-pdf", action="store_true", help="skip the saved PDFs and pictures")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
