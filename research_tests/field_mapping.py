"""Test 3 - field mapping (Eq. 3.6): do the confirmed values land in the
right box of each form?

    python -m research_tests.field_mapping [--samples] [--limit 20]
    python -m research_tests.field_mapping --draft-expected     (re-draft the expected box table)

For each patient of the answer key (sheet Patients, about 20), the
CONFIRMED values go through the real auto-population, unedited:
  case_bridge.draft_patient_and_encounter (with the parts staff confirmed)
  -> form_prefill.build_form_data -> the forms page itself, offline
  (claim-loader.js, app.js, the overlay maps of pdf-overlay.js).
Then, for every box in inputs/field_mapping_expected.csv on the claim's
forms (CSF, CF1, CF2, CF4, PMRF - each patient has the forms its package
needs), the value the form shows in that box is compared with the value
worked out from the answer key alone, and the PDF the page saves
(buildFilledPdf, pdf-lib) is read back with PyMuPDF to check the value is
printed at that box.

  Eq. 3.6: field mapping accuracy = boxes with the correct value /
           boxes checked x 100, per form and overall.

A box is checked when the answer key gives it a value, or when the form
fills it although the answer key leaves it empty. Every mismatch is listed.

The expected box table (inputs/field_mapping_expected.csv) says, for each
form, which box should hold which answer-key value, in which format:
  text        the value in capitals
  date        MM-DD-YYYY
  date_digit  digit N of MMDDYYYY (one digit per printed box)
  time_digit  digit N of hhmm, 12-hour, hour with a leading zero
  time        h:mm (12-hour), shown only when the AM/PM column is Position
  time_ampm   h:mm AM / h:mm PM
  tick        a tick when the AM/PM column equals Position
It was drafted from the boxes' printed labels (--draft-expected); check it
against the paper forms - that check is what makes it independent of the
code under test.
"""
import csv
import re
from pathlib import Path

from research_tests import FORMS_DIR, INPUTS, output_dir
from research_tests.common import answer_key, excel, stats

TEST_KEY = "field_mapping"
TITLE = "Field mapping test"
FORMS = ("csf", "cf1", "cf2", "cf4", "pmrf")
FORM_NAMES = {"csf": "CSF", "cf1": "CF1", "cf2": "CF2", "cf4": "CF4", "pmrf": "PMRF"}
FORM_PDFS = {"csf": "CSF.pdf", "cf1": "CF1.pdf", "cf2": "CF2.pdf", "cf4": "CF4.pdf", "pmrf": "PMRF.pdf"}
EXPECTED = INPUTS / "field_mapping_expected.csv"
EXPECTED_COLUMNS = ["Form", "Box ID", "Printed label (check on the paper form)", "Answer-key value", "Format",
                    "Position", "Note", "Checked"]
TICK = "✓"


# ── the expected values, from the answer key alone ─────────────────────

def _upper(text):
    return " ".join(str(text or "").split()).upper()


def _mmddyyyy(iso):
    return f"{iso[5:7]}{iso[8:10]}{iso[0:4]}" if iso else ""


def _time_key(column):
    """'Admitted time' -> 'Admitted' (the answer-key prefix)."""
    return column.rsplit(" ", 1)[0]


def expected_value(row, patient):
    """What this box should show for this patient ('' = should be empty)."""
    column, fmt, pos = row["Answer-key value"], row["Format"], row["Position"]
    if fmt == "text":
        return _upper(patient.get(column))
    if fmt == "date":
        iso = patient.get(column)
        return answer_key.display_date(iso) if iso else ""
    if fmt == "date_digit":
        digits = _mmddyyyy(patient.get(column))
        i = int(pos) - 1
        return digits[i] if i < len(digits) else ""
    prefix = _time_key(column)
    hour, minute, ampm = (patient.get(f"{prefix} hour"), patient.get(f"{prefix} minute"),
                          patient.get(f"{prefix} AM/PM"))
    if fmt == "time_digit":
        digits = f"{int(hour):02d}{minute}" if hour else ""
        i = int(pos) - 1
        return digits[i] if i < len(digits) else ""
    if fmt == "time":
        return f"{int(hour)}:{minute}" if hour and ampm == pos else ""
    if fmt == "time_ampm":
        return f"{int(hour)}:{minute} {ampm}" if hour else ""
    if fmt == "tick":
        return TICK if hour and ampm == pos else ""
    raise ValueError(f"Unknown format {fmt!r} in the expected box table")


def load_expected(path=EXPECTED):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("Form") or "").strip()]
    for r in rows:
        r["Form"] = r["Form"].strip().lower()
        r["Format"] = r["Format"].strip()
        r["Position"] = (r.get("Position") or "").strip()
    return rows


# ── reading the printed PDF back ───────────────────────────────────────

_TEMPLATE_WORDS = {}


def template_words(form):
    """{(page, x0, y0, text)} printed on the blank form itself, so the read-back
    sees only what PClaimAssist added."""
    if form not in _TEMPLATE_WORDS:
        import fitz
        doc = fitz.open(str(FORMS_DIR / "forms" / FORM_PDFS[form]))
        _TEMPLATE_WORDS[form] = {(i + 1, round(w[0]), round(w[1]), w[4]) for i, page in enumerate(doc)
                                 for w in page.get_text("words")}
        doc.close()
    return _TEMPLATE_WORDS[form]


def printed_text(doc, spot, form=None):
    """The words PyMuPDF finds at this box on the saved PDF (the blank
    form's own words left out)."""
    blank = template_words(form) if form else set()
    page = doc[spot["page"] - 1]
    w, h = page.rect.width, page.rect.height
    x0 = spot["left"] / 100 * w - 1.5
    x1 = x0 + max(spot["w"] / 100 * w, 6) + 3
    top = spot["top"] / 100 * h
    lines = max(1, int(spot.get("lines") or 1)) if spot.get("wrap") or spot.get("lh") else 1
    line_h = spot.get("lh") or (spot.get("fs") or 7) + 1
    y0, y1 = top - 2.5, top + 6 + 2.5 + (lines - 1) * line_h
    words = [wd for wd in page.get_text("words")
             if x0 <= (wd[0] + wd[2]) / 2 <= x1 and y0 <= (wd[1] + wd[3]) / 2 <= y1
             and (spot["page"], round(wd[0]), round(wd[1]), wd[4]) not in blank]
    words.sort(key=lambda wd: (round(wd[1]), wd[0]))
    return " ".join(wd[4] for wd in words)


def _same(expected, got, fmt):
    if fmt == "tick":
        return bool(expected) == bool(got.strip())
    return _upper(expected) == _upper(got)


def _printed_same(expected, got, fmt):
    if fmt == "tick":           # pdf-lib prints the tick as "X" (WinAnsi has no tick)
        return bool(expected) == bool(got.strip())
    return _upper(expected) == _upper(got)


# ── the test ───────────────────────────────────────────────────────────

def run(progress, samples=False, limit=20, draft_expected=False, no_pdf=False):
    if draft_expected:
        return draft(progress)
    root = INPUTS / "samples" if samples else INPUTS
    key_path = root / "answer_key.xlsx"
    if not key_path.is_file():
        raise FileNotFoundError(f"{key_path} not found (template: inputs/answer_key_template.xlsx; or --samples)")
    if not EXPECTED.is_file():
        raise FileNotFoundError(f"{EXPECTED} not found - run with --draft-expected first, then check it.")
    import fitz
    from research_tests.common.forms_page import FormsPage

    expected = load_expected()
    patients = answer_key.patients(key_path)[:limit]
    if not patients:
        raise ValueError("No patients in the answer key (sheet Patients).")
    lines, pdf_errors = [], []
    with FormsPage() as page:
        for n, p in enumerate(patients):
            progress(0.05 + 0.9 * n / len(patients), f"Patient {p['Patient ID']}: auto-populating the forms")
            body, warnings = answer_key.auto_populate(p)
            page.open_claim(body)
            forms = page.claim_forms()
            for form in FORMS:
                if form not in forms:
                    continue
                spots = {s["id"]: s for s in page.overlay_spots(form)}
                doc = None
                if not no_pdf:
                    try:
                        pdf, _ms = page.build_pdf(form)
                        doc = fitz.open(stream=pdf, filetype="pdf")
                    except Exception as exc:
                        pdf_errors.append(f"{p['Patient ID']} {form}: {exc}")
                for row in (r for r in expected if r["Form"] == form):
                    want = expected_value(row, p)
                    spot = spots.get(row["Box ID"])
                    shown = spot["value"] if spot else None
                    if not want and not (shown or "").strip():
                        continue                      # nothing expected, nothing shown
                    printed = printed_text(doc, spot, form) if doc is not None and spot else None
                    lines.append({
                        "patient": p["Patient ID"], "form": form, "box": row["Box ID"],
                        "label": row["Printed label (check on the paper form)"], "column": row["Answer-key value"],
                        "format": row["Format"], "position": row["Position"], "expected": want,
                        "shown": shown, "printed": printed,
                        "correct": spot is not None and _same(want, shown or "", row["Format"]),
                        "printed_ok": None if printed is None else _printed_same(want, printed, row["Format"]),
                        "warnings": "; ".join(warnings)})
                if doc is not None:
                    doc.close()
        browser = page.browser_version
        page_errors = list(page.errors)

    progress(0.96, "Summarising")
    per_form = []
    for form in FORMS + ("all",):
        group = [l for l in lines if form == "all" or l["form"] == form]
        if not group:
            continue
        printed = [l for l in group if l["printed_ok"] is not None]
        per_form.append([FORM_NAMES.get(form, "All forms"), len({l["patient"] for l in group}), len(group),
                         sum(l["correct"] for l in group), stats.percent(sum(l["correct"] for l in group), len(group)),
                         len(printed), stats.percent(sum(l["printed_ok"] for l in printed), len(printed))])
    per_value = []
    for column in dict.fromkeys(l["column"] for l in lines):
        group = [l for l in lines if l["column"] == column]
        per_value.append([column, len(group), stats.percent(sum(l["correct"] for l in group), len(group))])
    mismatches = [[l["patient"], FORM_NAMES[l["form"]], l["box"], l["label"], l["column"], l["expected"],
                   l["shown"] if l["shown"] is not None else "(box not on the form's map)", l["printed"],
                   "on screen" if not l["correct"] else "printed only"]
                  for l in lines if not l["correct"] or l["printed_ok"] is False]
    notes = [
        "Eq. 3.6: field mapping accuracy = boxes holding the correct value / boxes checked x 100.",
        "On screen = the value the form shows in the box (pdf-overlay.js resolveOverlayFieldValue); printed = the "
        "text PyMuPDF reads at that box on the PDF the page saves (buildFilledPdf, pdf-lib).",
        "Each patient is checked on the forms its claim needs (pcaClaimForms); PMRF only with the newborn package.",
        "The delivery date and time have no box of their own on these forms, so they are not part of this test.",
        f"Expected boxes: {EXPECTED.name} ({len(expected)} rows) - drafted from the printed labels; verify against "
        "the paper forms before reporting.",
        f"Run offline in {browser} with the real PClaimAssist/index.html; page errors: {len(page_errors)}.",
    ]
    if samples:
        notes.append("FICTIONAL SAMPLE PATIENTS (make_samples.py).")
    if pdf_errors:
        notes.append("PDF errors: " + "; ".join(pdf_errors[:5]))
    sheets = [
        {"name": "3a Field mapping per form", "title": "Table - Field mapping accuracy per form (Eq. 3.6)",
         "headers": ["Form", "Patients", "Boxes checked", "Correct on screen", "Field mapping accuracy %",
                     "Boxes read on the PDF", "Printed correctly %"],
         "rows": per_form, "bold_last": True, "notes": notes},
        {"name": "3b Field mapping per value", "title": "Table - Field mapping accuracy per answer-key value",
         "headers": ["Answer-key value", "Boxes checked", "Correct on screen %"], "rows": per_value},
        {"name": "3c Mismatches", "title": "Every mismatch",
         "headers": ["Patient", "Form", "Box", "Printed label", "Answer-key value", "Expected", "On screen",
                     "Printed", "Wrong"],
         "rows": mismatches, "notes": ["None." if not mismatches else f"{len(mismatches)} mismatches."]},
    ]
    raw = {"name": "Raw data",
           "headers": ["Patient", "Form", "Box", "Printed label", "Answer-key value", "Format", "Position",
                       "Expected", "On screen", "Printed", "Correct", "Printed correctly", "Auto-population warnings"],
           "rows": [[l["patient"], FORM_NAMES[l["form"]], l["box"], l["label"], l["column"], l["format"],
                     l["position"], l["expected"], l["shown"], l["printed"], "Yes" if l["correct"] else "No",
                     "" if l["printed_ok"] is None else "Yes" if l["printed_ok"] else "No", l["warnings"]]
                    for l in lines]}
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "field_mapping_results.xlsx", [raw] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    overall = per_form[-1] if per_form else None
    return {"outputs": [path], "headline": [
        ["Patients", len(patients)], ["Boxes checked", overall[2] if overall else 0],
        ["Field mapping accuracy % (on screen)", overall[4] if overall else None],
        ["Printed correctly %", overall[6] if overall else None], ["Mismatches", len(mismatches)]]}


# ── drafting the expected box table ────────────────────────────────────

_NAME_KEYS = {"patientLastName": "Last name", "patientFirstName": "First name", "patientMiddleName": "Middle name",
              "patientNameExt": "Suffix"}
_ADDRESS_PARTS = {"Street": "Street", "Barangay": "Barangay", "City": "City", "Province": "Province"}
_TIMES = {"Admitted": ("Admitted", "dateAdmitted", ("timeAdmitted",), ("cf4TimeAdmittedDigits", "timeAdmittedDigits"),
                       "amPmAdmitted", "timeAdmittedStr"),
          "Went home": ("Went home", "dateDischarge", ("timeDischarge",),
                        ("cf4TimeDischargeDigits", "timeDischargeDigits"), "amPmDischarge", "timeDischargeStr")}


def source_of(spot):
    """(answer-key value, format, position, note) this box should hold, or
    None when it holds nothing from the logbook. Decided from what the box
    is for (its key), never from what it shows now."""
    key, src = spot["key"], spot["digitKey"] or spot["computed"] or spot["key"]
    note = "printed only when the patient is not the member" if spot["unless"] == "memberIsPatient" else ""
    if key in _NAME_KEYS and not spot["checkbox"]:
        return _NAME_KEYS[key], "text", "", note
    if src == "patientDOB":
        if spot["digit"] is not None:
            return "Birthday", "date_digit", str(spot["digit"] + 1), note
        return "Birthday", "date", "", note
    for prefix, date_key, time_keys, digit_keys, ampm_key, str_key in _TIMES.values():
        if src == date_key:
            if spot["digit"] is not None:
                return f"{prefix} date", "date_digit", str(spot["digit"] + 1), note
            return f"{prefix} date", "date", "", note
        if src in digit_keys and spot["digit"] is not None:
            return f"{prefix} time", "time_digit", str(spot["digit"] + 1), note
        if key == ampm_key and spot["checkbox"] and spot["checkValue"] in ("AM", "PM"):
            return f"{prefix} AM/PM", "tick", spot["checkValue"], note
        if key in time_keys and spot["amPmCheck"]:
            return f"{prefix} AM/PM", "tick", spot["amPmCheck"], note
        if key in time_keys and spot["timeComponent"]:
            return f"{prefix} time", "time", spot["timeComponent"], note
        if src == str_key:
            return f"{prefix} time", "time_ampm", "", note
    if key == "admissionDx":
        return "Reason for admission", "text", "", note
    if key in ("cf4FinalDiagnosis", "dischargeDx"):
        return "Final diagnosis", "text", "", note
    m = re.fullmatch(r"(?:cf1)?(?:addr|mailingAddr|cf1MailingAddr)(Street|Barangay|City|Province)", src) \
        or re.fullmatch(r"(?:addr|mailingAddr)(Street|Barangay|City|Province)", key)
    if m:
        part = _ADDRESS_PARTS[m.group(1)]
        mailing = "ailing" in src or "ailing" in key
        return part, "text", "", ("mailing address: the home address when no other is given" if mailing else note)
    return None


def label_near(doc, spot):
    """The printed words just left of / above the box - a hint for checking."""
    page = doc[spot["page"] - 1]
    w, h = page.rect.width, page.rect.height
    x, y = spot["left"] / 100 * w, spot["top"] / 100 * h
    words = [wd for wd in page.get_text("words") if re.search(r"[A-Za-z0-9]", wd[4])]   # not blank lines
    left = [wd for wd in words if abs((wd[1] + wd[3]) / 2 - (y + 4)) < 6 and x - 160 < wd[2] <= x + 2]
    above = [wd for wd in words if y - 14 < wd[3] <= y + 1 and x - 4 <= wd[0] < x + max(spot["w"] / 100 * w, 30)]
    pick = left[-6:] if left else above[:6]
    pick.sort(key=lambda wd: (round(wd[1]), wd[0]))
    return " ".join(wd[4] for wd in pick)[:90]


def draft(progress):
    import fitz
    from research_tests.common.forms_page import FormsPage
    rows = []
    with FormsPage() as page:
        page.page.goto("http://pclaimassist.research/index.html")
        page.page.wait_for_function("() => typeof OVERLAY_MAP !== 'undefined'")
        for n, form in enumerate(FORMS):
            progress(0.1 + 0.8 * n / len(FORMS), f"Drafting {FORM_NAMES[form]}")
            doc = fitz.open(str(FORMS_DIR / "forms" / FORM_PDFS[form]))
            for spot in page.overlay_spots(form):
                src = source_of(spot)
                if src:
                    column, fmt, pos, note = src
                    rows.append([FORM_NAMES[form], spot["id"], label_near(doc, spot), column, fmt, pos, note, ""])
            doc.close()
    out = output_dir(TEST_KEY)
    draft_path = out / "field_mapping_expected_DRAFT.csv"
    targets = [draft_path] + ([] if EXPECTED.exists() else [EXPECTED])   # a checked table is never overwritten
    for path in targets:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(EXPECTED_COLUMNS)
            w.writerows(rows)
    progress(1.0, "Done")
    return {"outputs": [draft_path], "headline": [["Boxes in the draft", len(rows)], ["Draft", str(draft_path)],
                                                   ["Expected box table used by the test", str(EXPECTED)]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the fictional sample patients")
    parser.add_argument("--limit", type=int, default=20, help="patients to check (default 20)")
    parser.add_argument("--no-pdf", action="store_true", help="skip reading the saved PDFs back")
    parser.add_argument("--draft-expected", action="store_true",
                        help="draft inputs/field_mapping_expected.csv from the forms (not overwritten if present)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
