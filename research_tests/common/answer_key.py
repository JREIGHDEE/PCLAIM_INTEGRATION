"""The answer key (research_tests/inputs/answer_key.xlsx) and the patients
in it, turned into claims by the REAL auto-population.

Sheets:
  Handwriting  Writer ID | Style | Page | Row | Field | Ground Truth
               one line per logbook cell a writer filled in; Page is the
               scan's page (PDF page number) the cell is on, Row the entry
               line on that page (1 = first line under the header), Field
               the logbook column as the OCR comparison names it (Case
               number, Admitted, Patient name, Birthday, Address, Reason for
               admission, Delivered, Final diagnosis, Went home).
  Patients     the confirmed values of each patient, split the way staff
               confirm them in the logbook review (last/first/middle name,
               date, hour:minute, AM/PM), plus the address parts as
               confirmed on Patient details (Street, Barangay, City,
               Province - optional). Used by the field mapping, validation
               and performance tests.

Writers are listed in inputs/writers.csv (see writers()).
"""
import csv
import re
from datetime import date, datetime

from research_tests import INPUTS
from research_tests.common.excel import read_rows

ANSWER_KEY = INPUTS / "answer_key.xlsx"
WRITERS = INPUTS / "writers.csv"

# Logbook column (case_bridge category) <-> the name the comparison shows.
FIELD_TO_CATEGORY = {
    "Case number": "CASE #", "Admitted": "DATE & TIME OF ADMISSION", "Patient name": "NAME",
    "Birthday": "BDAY", "Address": "ADDRESS", "Reason for admission": "ADMITTING DIAGNOSIS",
    "Delivered": "DATE & TIME OF DELIVERY", "Final diagnosis": "FINAL DIAGNOSIS",
    "Went home": "DATE & TIME OF DISCHARGE",
}
CATEGORY_TO_FIELD = {v: k for k, v in FIELD_TO_CATEGORY.items()}
FIELDS = list(FIELD_TO_CATEGORY)

PATIENT_COLUMNS = [
    "Patient ID", "Case number", "Last name", "First name", "Middle name", "Suffix", "Birthday", "Address",
    "Admitted date", "Admitted time", "Admitted AM/PM", "Delivered date", "Delivered time", "Delivered AM/PM",
    "Went home date", "Went home time", "Went home AM/PM", "Reason for admission", "Final diagnosis",
    # The address as staff confirm it on Patient details (optional; the
    # field mapping test checks the address boxes only when these are given).
    "Street", "Barangay", "City", "Province",
]
HANDWRITING_COLUMNS = ["Writer ID", "Style", "Page", "Row", "Field", "Ground Truth"]
WRITER_COLUMNS = ["Writer ID", "Style", "Set", "Scan File", "Notes"]


def _text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def iso_date(value):
    """'2026-10-20' from 10-20-2026, 10/20/2026, 2026-10-20 or an Excel date; '' if blank."""
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _text(value)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
    m = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
    if m:
        return date(int(m[3]), int(m[1]), int(m[2])).isoformat()
    raise ValueError(f"Not a date: {value!r} (use MM-DD-YYYY)")


def display_date(iso):
    """'10-20-2026' (the forms' MM-DD-YYYY) from an ISO date."""
    return f"{iso[5:7]}-{iso[8:10]}-{iso[0:4]}" if iso else ""


def _time_parts(value, am_pm):
    """(hour '8', minute '30', 'AM') from '8:30' / '08:30' / a datetime.time."""
    if value in (None, ""):
        return "", "", ""
    if hasattr(value, "hour"):
        hour, minute = value.hour, value.minute
    else:
        m = re.fullmatch(r"(\d{1,2})[:.](\d{2})", _text(value))
        if not m:
            raise ValueError(f"Not a time: {value!r} (use hh:mm)")
        hour, minute = int(m[1]), int(m[2])
    am_pm = _text(am_pm).upper()
    if hour > 12:
        hour, am_pm = hour - 12, "PM"
    return str(hour or 12), f"{minute:02d}", am_pm or "AM"


def time_24h(hour, minute, am_pm):
    """'08:30' / '20:30' from the confirmed parts (as the database keeps it)."""
    if not hour:
        return ""
    h = int(hour) % 12 + (12 if am_pm == "PM" else 0)
    return f"{h:02d}:{minute}"


# ── reading ────────────────────────────────────────────────────────────

def patients(path=ANSWER_KEY):
    out = []
    for row in read_rows(path, "Patients"):
        if not _text(row.get("Patient ID")):
            continue
        p = {k: row.get(k) for k in PATIENT_COLUMNS}
        p["Patient ID"] = _text(p["Patient ID"])
        for prefix in ("Admitted", "Delivered", "Went home"):
            p[f"{prefix} date"] = iso_date(p.get(f"{prefix} date"))
            p[f"{prefix} hour"], p[f"{prefix} minute"], p[f"{prefix} AM/PM"] = _time_parts(
                p.get(f"{prefix} time"), p.get(f"{prefix} AM/PM"))
        p["Birthday"] = iso_date(p.get("Birthday"))
        for k in ("Case number", "Last name", "First name", "Middle name", "Suffix", "Address",
                  "Reason for admission", "Final diagnosis", "Street", "Barangay", "City", "Province"):
            p[k] = _text(p.get(k)).upper()
        out.append(p)
    return out


def handwriting(path=ANSWER_KEY):
    out = []
    for row in read_rows(path, "Handwriting"):
        writer = _text(row.get("Writer ID")).upper()
        field = _text(row.get("Field"))
        if not writer or not field:
            continue
        if field not in FIELD_TO_CATEGORY:
            raise ValueError(f"Unknown field {field!r} in the Handwriting sheet (use one of: {', '.join(FIELDS)})")
        out.append({"writer": writer, "style": _text(row.get("Style")).lower(), "page": int(row["Page"]),
                    "row": int(row["Row"]), "field": field, "truth": _text(row.get("Ground Truth"))})
    return out


def writers(path=WRITERS):
    """[{"writer", "style", "set", "scan", "notes"}] from writers.csv."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        writer = _text(r.get("Writer ID")).upper()
        if not writer:
            continue
        style = _text(r.get("Style")).lower()
        if style not in ("caps", "lower"):
            raise ValueError(f"{writer}: Style must be caps or lower, not {style!r}")
        out.append({"writer": writer, "style": style, "set": (_text(r.get("Set")) or "main").lower(),
                    "scan": _text(r.get("Scan File")), "notes": _text(r.get("Notes"))})
    return out


# ── a patient through the real auto-population ─────────────────────────

def logbook_entry(p):
    """(values, reviewed_parts) for case_bridge.draft_patient_and_encounter:
    the logbook text per column and the parts staff confirmed in the
    review (review_fields.claim_fields' shape)."""
    def when(prefix):
        d, h, m, ap = (p[f"{prefix} date"], p[f"{prefix} hour"], p[f"{prefix} minute"], p[f"{prefix} AM/PM"])
        text = (display_date(d) + (f" {h}:{m} {ap}" if h else "")).strip()
        return text, {"date": d, "hour": h, "minute": m, "am_pm": ap}

    name_text = ", ".join(x for x in (p["Last name"], " ".join(x for x in (p["First name"], p["Middle name"],
                                                                            p["Suffix"]) if x)) if x)
    values, parts = {}, {}
    if p["Case number"]:
        values["CASE #"] = p["Case number"]
    if name_text:
        values["NAME"] = name_text
        parts["NAME"] = {"last": p["Last name"], "first": p["First name"], "middle": p["Middle name"],
                         "suffix": p["Suffix"]}
    if p["Birthday"]:
        values["BDAY"] = display_date(p["Birthday"])
        parts["BDAY"] = {"date": p["Birthday"]}
    for prefix, category in (("Admitted", "DATE & TIME OF ADMISSION"), ("Delivered", "DATE & TIME OF DELIVERY"),
                             ("Went home", "DATE & TIME OF DISCHARGE")):
        if p[f"{prefix} date"]:
            values[category], parts[category] = when(prefix)
    for col, category in (("Address", "ADDRESS"), ("Reason for admission", "ADMITTING DIAGNOSIS"),
                          ("Final diagnosis", "FINAL DIAGNOSIS")):
        if p[col]:
            values[category] = p[col]
            parts[category] = {"text": p[col]}
    return values, parts


def auto_populate(p):
    """The real auto-population of one patient's confirmed values:
    case_bridge.draft_patient_and_encounter -> form_prefill.build_form_data.
    -> (form-data body as GET /api/claims/<id>/form-data answers, warnings)"""
    from philhealth import case_bridge, form_prefill
    values, parts = logbook_entry(p)
    patient, encounter, claim, warnings = case_bridge.draft_patient_and_encounter(values, reviewed_parts=parts)
    built = form_prefill.build_form_data({"patient": patient, "encounter": encounter, "claim": claim})
    return {"data": built["data"], "fields": built["fields"], "ocr_reference": built["ocr_reference"],
            "saved_values": {}}, warnings
