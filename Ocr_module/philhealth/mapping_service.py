"""Pure mapping/validation layer: internal records -> PhilHealth claim view.

map_claim() takes plain dicts (as read from patients/encounters/claims - or
None if a row doesn't exist yet) and returns a fully resolved, validated view
with per-form missing-required-field lists. It never mutates its inputs and
never touches the database or Flask - see claims_store.py for persistence
and routes/claims_routes.py for the HTTP layer built on top of this.
"""
from datetime import date

from philhealth.field_catalog import (
    DATE_FIELDS,
    ENUM_CHOICES,
    FIELD_LABELS,
    KEY_SOURCE,
    PIN_PATTERN,
    VAL_FIELDS,
    is_valid_date_string,
    resolve_computed_value,
    source_kind,
)

_COMPUTED_KEYS = ("patientName", "memberName", "hciAddress", "timeAdmittedStr", "timeDischargeStr")
_PIN_KEYS = ("memberPIN", "patientPIN")


def build_flat_data(patient, encounter, claims_row):
    """Flat camelCase dict pulled from the three source rows - a fresh dict,
    the inputs are only ever read, never written to."""
    patient = patient or {}
    encounter = encounter or {}
    claims_row = claims_row or {}
    tables = {"patients": patient, "encounters": encounter, "claims": claims_row}

    data = {}
    for key, (table, column) in KEY_SOURCE.items():
        data[key] = tables[table].get(column)
    return data


def _validate(data):
    """Returns {key: message} for every field that has a value but fails
    format/enum validation. Fields that are simply blank are not errors here
    - blank-and-required is handled separately as "missing", per Phase 6's
    distinction between "invalid" and "missing"."""
    errors = {}

    for key in DATE_FIELDS:
        value = data.get(key)
        if value and not is_valid_date_string(value):
            errors[key] = f"{FIELD_LABELS.get(key, key)} is not a valid date"

    for key, choices in ENUM_CHOICES.items():
        value = data.get(key)
        if value and value not in choices:
            errors[key] = f"{FIELD_LABELS.get(key, key)} must be one of: {', '.join(choices)}"

    for key in _PIN_KEYS:
        value = data.get(key)
        if value and not PIN_PATTERN.match(value):
            errors[key] = f"{FIELD_LABELS.get(key, key)} must be in the format ##-#########-#"

    return errors


def _form_status(form, data, errors):
    missing = []
    blocking_errors = []
    for field in VAL_FIELDS[form]:
        key, label = field["key"], field["label"]
        if key in errors:
            blocking_errors.append(errors[key])
        elif not resolve_computed_value(key, data):
            missing.append(label)
    return {
        "missing_required": missing,
        "validation_errors": blocking_errors,
        "complete": not missing and not blocking_errors,
    }


def map_claim(patient=None, encounter=None, claims_row=None):
    """Build the full mapped/validated view for a claim.

    `patient`/`encounter`/`claims_row` are plain dicts (e.g. DictCursor rows)
    or None. Returns a dict:
      - "fields": [{key, label, value, resolved, source, table, column}, ...]
        one entry per known field, in a stable, catalog-defined order.
      - "forms": {"cf2": {...}, "csf": {...}} - see _form_status.
    Does not mutate any of its inputs.
    """
    data = build_flat_data(patient, encounter, claims_row)
    errors = _validate(data)

    fields = []
    for key in KEY_SOURCE:
        table, column = KEY_SOURCE[key]
        fields.append({
            "key": key,
            "label": FIELD_LABELS.get(key, key),
            "value": data.get(key),
            "resolved": resolve_computed_value(key, data),
            "source": source_kind(key),
            "table": table,
            "column": column,
            "error": errors.get(key),
            "choices": list(ENUM_CHOICES[key]) if key in ENUM_CHOICES else None,
        })
    for key in _COMPUTED_KEYS:
        fields.append({
            "key": key,
            "label": FIELD_LABELS.get(key, key),
            "value": None,
            "resolved": resolve_computed_value(key, data),
            "source": "computed",
            "table": None,
            "column": None,
            "error": None,
            "choices": None,
        })

    return {
        "fields": fields,
        "forms": {form: _form_status(form, data, errors) for form in VAL_FIELDS},
    }


def missing_fields_message(form_status):
    """Builds the Phase 6 "Cannot generate claim form..." message from one
    form's status dict (as returned in map_claim()["forms"][form])."""
    problems = list(form_status["missing_required"]) + list(form_status["validation_errors"])
    return "Cannot generate claim form. The following required information is missing: " + "; ".join(problems)


# ---------------------------------------------------------------------------
# The critical rules, checked again before a server-side export
# ---------------------------------------------------------------------------
# The block_submission rules of PClaimAssist/js/validation-rules.js that a
# claim's stored values can answer, with the same ids and messages. The
# browser refuses to save a PDF while any of them fires; the server's
# CF2/CSF export (routes/claims_routes.py) refuses the same way. Not here:
# IC-01/IC-02/IC-07 (never fire - every form reads the same value) and the
# signature rules SP-* (only fire for a re-uploaded signed form).
_RULE_DATES = ("memberDOB", "patientDOB", "dateAdmitted", "dateDischarge", "deliveryDate", "lmp")


def _blank(value):
    return value is None or str(value).strip() == ""


def _iso(value):
    """A date from an ISO 'YYYY-MM-DD' value, or None."""
    if _blank(value) or not is_valid_date_string(value):
        return None
    y, m, d = str(value).split("-")[:3]
    return date(int(y), int(m), int(d))


def _truthy(value):
    return value is True or str(value).strip().lower() in ("true", "1", "yes", "on")


def critical_rule_problems(data):
    """[(rule id, message), ...] for every critical rule firing on `data`
    (form key -> value, as the forms hold them). [] when the claim may be
    exported."""
    problems = []
    pin = data.get("memberPIN")
    no_philhealth = _truthy(data.get("memberNoPhilhealth"))
    admitted, discharged = _iso(data.get("dateAdmitted")), _iso(data.get("dateDischarge"))
    delivered, member_dob = _iso(data.get("deliveryDate")), _iso(data.get("memberDOB"))
    course = any(not _blank(data.get(f"cf4CourseOrder{n}")) for n in (1, 2))

    if not resolve_computed_value("patientName", data):
        problems.append(("MF-01", "Patient's full name is missing. This field is required."))
    if _blank(pin) and not no_philhealth:
        problems.append(("MF-02", "PhilHealth Identification Number (PIN) is missing."))
    if _blank(data.get("dateAdmitted")):
        problems.append(("MF-04", "Date of admission is missing. Type it in Patient details, part 3 (Stay at the clinic)."))
    if _blank(data.get("dateDischarge")):
        problems.append(("MF-05", "Date of discharge (went home) is missing. Type it in Patient details, part 3 (Stay at the clinic)."))
    if _blank(data.get("cf4ChiefComplaint")):
        problems.append(("MF-07", "CF4 chief complaint is missing. Please encode it from the patient's clinical record."))
    if not course:
        problems.append(("MF-08", "CF4 course in the ward is missing. Please encode it from the patient's clinical record."))
    if not _blank(pin) and not no_philhealth and len("".join(ch for ch in str(pin) if ch.isdigit())) != 12:
        problems.append(("IF-01", "PhilHealth PIN must be exactly 12 digits."))
    if not _blank(pin) and any(not (ch.isdigit() or ch in " -") for ch in str(pin)):
        problems.append(("IF-02", "PhilHealth PIN must contain digits only."))
    if any(not _blank(data.get(k)) and _iso(data.get(k)) is None for k in _RULE_DATES):
        problems.append(("IF-03", "Date is not in the required MM-DD-YYYY format."))
    if admitted and discharged and discharged < admitted:
        problems.append(("IC-03", "Discharge date is earlier than admission date."))
    if admitted and member_dob and member_dob > admitted:
        problems.append(("IC-04", "Date of birth cannot be after the admission date."))
    cf2_dx = str(data.get("dxADiagnosis") or "").strip().lower()
    cf4_dx = str(data.get("cf4FinalDiagnosis") or "").strip().lower()
    if cf2_dx and cf4_dx and cf2_dx != cf4_dx:
        problems.append(("IC-09", "The final diagnosis on CF2 does not match the diagnosis on CF4."))
    if discharged and delivered and discharged <= delivered:
        problems.append(("IC-08", "Discharge date must be at least one day after the delivery date."))
    return problems


def critical_rules_message(problems):
    """The refusal shown when critical rules fire: each rule id and message."""
    return ("Cannot generate claim form. Fix these first: "
            + "; ".join(f"{rule} {message}" for rule, message in problems))
