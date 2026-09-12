"""Pure mapping/validation layer: internal records -> PhilHealth claim view.

map_claim() takes plain dicts (as read from patients/encounters/claims - or
None if a row doesn't exist yet) and returns a fully resolved, validated view
with per-form missing-required-field lists. It never mutates its inputs and
never touches the database or Flask - see claims_store.py for persistence
and routes/claims_routes.py for the HTTP layer built on top of this.
"""
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
