"""Best-effort bridge: case_sessions.reviewed_values (OCR free text) ->
patients/encounters/claims column drafts.

The OCR review UI only ever produces free text keyed by config.py's
TRAINING_CATEGORIES ("CASE #", "DATE & TIME OF ADMISSION", "NAME", "BDAY",
"ADDRESS", "ADMITTING DIAGNOSIS", "DATE & TIME OF DELIVERY",
"FINAL DIAGNOSIS", "DATE & TIME OF DISCHARGE") - handwritten/scanned dates
and names in particular are never in one predictable format. Anything this
module can't confidently parse is left out (never guessed) and reported as
a warning, per the "avoid silently generating incorrect information" rule -
the reviewer fills it in by hand instead.

Every one of the 9 logbook categories above is now drafted into some
destination column (ADDRESS -> patients.address, DATE & TIME OF DELIVERY ->
claims.delivery_date/delivery_time/am_pm_delivery) - previously these two
were captured during OCR review but had nowhere to go and were silently
dropped when a claim was generated. CASE # remains lookup-only (it is the
case_sessions.logbook_case_number key, not a patient/claim field).
"""
import re
from datetime import datetime

from philhealth import field_catalog

# OCR category labels, from Ocr_module/config.py TRAINING_CATEGORIES.
CASE_NUMBER = "CASE #"
NAME = "NAME"
BDAY = "BDAY"
ADDRESS = "ADDRESS"
ADMISSION_DT = "DATE & TIME OF ADMISSION"
DISCHARGE_DT = "DATE & TIME OF DISCHARGE"
DELIVERY_DT = "DATE & TIME OF DELIVERY"
ADMITTING_DX = "ADMITTING DIAGNOSIS"
FINAL_DX = "FINAL DIAGNOSIS"

def target_fields(category):
    """[{"key", "column", "label"}, ...] for the claim fields a logbook
    category maps to. CASE # is lookup-only (case_sessions key, not a claim
    field); an unknown category maps to nothing."""
    if category == CASE_NUMBER:
        return [{"key": None, "column": "case_sessions.logbook_case_number",
                 "label": "Case # (lookup only)"}]
    targets = []
    # field_catalog.OCR_CATEGORY_KEYS must match what
    # draft_patient_and_encounter() below actually fills - keep them in sync.
    for key in field_catalog.OCR_CATEGORY_KEYS.get(category, ()):
        table, column = field_catalog.KEY_SOURCE[key]
        targets.append({
            "key": key,
            "column": f"{table}.{column}",
            "label": field_catalog.FIELD_LABELS.get(key, key),
        })
    return targets

_DATE_FORMATS = (
    "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%y",
    "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
)
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*([AaPp][Mm])?")


def _parse_date_flexible(text):
    """Returns 'YYYY-MM-DD' on success, or None if nothing recognizable."""
    if not text:
        return None
    candidate = _TIME_RE.sub("", text).strip(" ,.-")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_time_flexible(text):
    """Returns (HH:MM in 24h, 'AM'|'PM') on success, or (None, None)."""
    if not text:
        return None, None
    match = _TIME_RE.search(text)
    if not match:
        return None, None
    hour, minute, meridiem = match.groups()
    hour = int(hour)
    if meridiem:
        am_pm = meridiem.upper()
        if am_pm == "PM" and hour != 12:
            hour += 12
        elif am_pm == "AM" and hour == 12:
            hour = 0
    else:
        # No AM/PM in the OCR text - can't tell which half of the day this
        # is, so don't guess one; the 24h value stays as-typed and am_pm is
        # reported unknown for the reviewer to set explicitly.
        am_pm = None
    return f"{hour:02d}:{minute}", am_pm


def _split_name(raw_name):
    """Best-effort 'NAME' free text -> (last, first, middle), plus a warning
    if the split is a guess (no comma to disambiguate order)."""
    if not raw_name or not raw_name.strip():
        return None, None, None, "Patient name was blank in the OCR review - enter it manually."

    text = raw_name.strip()
    if "," in text:
        last, _, rest = text.partition(",")
        rest_parts = rest.split()
        first = rest_parts[0] if rest_parts else None
        middle = " ".join(rest_parts[1:]) or None
        return last.strip() or None, first, middle, None

    parts = text.split()
    if len(parts) == 1:
        return parts[0], None, None, (
            "Patient name had only one word with no comma - could not split "
            "into last/first name; please complete it manually."
        )
    # No comma: assume "First [Middle] Last" order (last token is the
    # surname) - flagged since this is a guess, not a confident parse.
    # Common Filipino/Spanish-origin surname particles ("Dela Cruz", "De
    # Los Santos") are two or three words, not one - a bare last-token
    # split would wrongly cut them down to just "Cruz"/"Santos", so those
    # particles are folded into the surname instead.
    surname_len = 1
    lower_parts = [p.lower() for p in parts]
    if len(parts) >= 4 and lower_parts[-3] in ("de",) and lower_parts[-2] in ("los", "las", "la"):
        surname_len = 3
    elif len(parts) >= 3 and lower_parts[-2] in (
        "dela", "de", "del", "san", "santa", "sto", "sta", "mac", "mc", "van", "von",
    ):
        surname_len = 2

    last = " ".join(parts[-surname_len:])
    first = parts[0]
    middle = " ".join(parts[1:-surname_len]) or None
    warning = (
        f"Patient name \"{text}\" had no comma to disambiguate order - "
        f"guessed \"{last}\" as last name and \"{first}\" as first name; "
        "please verify."
    )
    return last, first, middle, warning


def draft_patient_and_encounter(values, reviewed_parts=None):
    """values: the case_sessions.reviewed_values dict (OCR review free text).

    Returns (patient_fields, encounter_fields, claims_fields, warnings):
      - patient_fields: dict of patients columns this bridge could confidently
        fill (last_name, first_name, middle_name, date_of_birth, address) -
        only keys it actually resolved, never a full dict with blanks/guesses
        baked in.
      - encounter_fields: dict of encounters columns (date_admitted,
        time_admitted, am_pm_admitted, date_discharge, time_discharge,
        am_pm_discharge, admission_dx, discharge_dx), same rule.
      - claims_fields: dict of claims columns this bridge could confidently
        fill (delivery_date, delivery_time, am_pm_delivery), same rule. Only
        ever populated when case_bridge can actually parse a value - a claim
        can exist without any of these (see database/schema.sql's 'draft'
        status), so an empty dict here is normal and expected, not an error.
      - warnings: list of human-readable strings for anything skipped or
        guessed, so the review UI can surface them.

    Never mutates `values`.
    """
    values = dict(values or {})
    warnings = []
    patient_fields = {}
    encounter_fields = {}
    claims_fields = {}

    # Fields a person split into their parts in the logbook review
    # (philhealth/review_fields.py) are used as typed - their free text is
    # not re-parsed, so nothing is guessed and no parse warning applies.
    reviewed_parts = reviewed_parts or {}
    if reviewed_parts:
        from philhealth import review_fields
        tables = {"patients": patient_fields, "encounters": encounter_fields, "claims": claims_fields}
        for category, parts in reviewed_parts.items():
            for (table, column), value in review_fields.claim_fields(category, parts).items():
                tables[table][column] = value
            values.pop(category, None)

    if NAME in reviewed_parts:
        last, first, middle, name_warning = None, None, None, None
    else:
        last, first, middle, name_warning = _split_name(values.get(NAME))
    if last:
        patient_fields["last_name"] = last
    if first:
        patient_fields["first_name"] = first
    if middle:
        patient_fields["middle_name"] = middle
    if name_warning:
        warnings.append(name_warning)

    dob = _parse_date_flexible(values.get(BDAY))
    if dob:
        patient_fields["date_of_birth"] = dob
    elif values.get(BDAY):
        warnings.append(f"Could not parse birth date \"{values.get(BDAY)}\" - please enter it manually.")

    # Free text, no format to parse - passed through as-is, same as the
    # diagnosis fields below.
    address_raw = values.get(ADDRESS)
    if address_raw and address_raw.strip():
        patient_fields["address"] = address_raw.strip()

    admission_raw = values.get(ADMISSION_DT)
    admission_date = _parse_date_flexible(admission_raw)
    admission_time, admission_ampm = _parse_time_flexible(admission_raw)
    if admission_date:
        encounter_fields["date_admitted"] = admission_date
    elif admission_raw:
        warnings.append(f"Could not parse admission date \"{admission_raw}\" - please enter it manually.")
    if admission_time:
        encounter_fields["time_admitted"] = admission_time
    if admission_ampm:
        encounter_fields["am_pm_admitted"] = admission_ampm

    discharge_raw = values.get(DISCHARGE_DT)
    discharge_date = _parse_date_flexible(discharge_raw)
    discharge_time, discharge_ampm = _parse_time_flexible(discharge_raw)
    if discharge_date:
        encounter_fields["date_discharge"] = discharge_date
    elif discharge_raw:
        warnings.append(f"Could not parse discharge date \"{discharge_raw}\" - please enter it manually.")
    if discharge_time:
        encounter_fields["time_discharge"] = discharge_time
    if discharge_ampm:
        encounter_fields["am_pm_discharge"] = discharge_ampm

    delivery_raw = values.get(DELIVERY_DT)
    delivery_date = _parse_date_flexible(delivery_raw)
    delivery_time, delivery_ampm = _parse_time_flexible(delivery_raw)
    if delivery_date:
        claims_fields["delivery_date"] = delivery_date
    elif delivery_raw:
        warnings.append(f"Could not parse delivery date \"{delivery_raw}\" - please enter it manually.")
    if delivery_time:
        claims_fields["delivery_time"] = delivery_time
    if delivery_ampm:
        claims_fields["am_pm_delivery"] = delivery_ampm

    if values.get(ADMITTING_DX):
        encounter_fields["admission_dx"] = values[ADMITTING_DX]
    if values.get(FINAL_DX):
        encounter_fields["discharge_dx"] = values[FINAL_DX]

    return patient_fields, encounter_fields, claims_fields, warnings
