"""Claim rows -> PClaimAssist form data (all four forms: PMRF, CSF, CF2, CF3).

Pure (no DB, no Flask). build_form_data() turns a claim's stored rows into
values keyed by PClaimAssist form key, using field_catalog.FORM_FIELDS as
the only mapping, and says where each OCR-sourced value came from so the
forms can tag it:

  accepted     OCR confidence >= accept threshold, unchanged      "from OCR"
  needs_check  OCR confidence in the check band, unchanged         "from OCR - check"
  typed        typed or corrected by staff during the OCR review   "typed at OCR review"
  required     the logbook column had no usable OCR value - staff  "required"
               must type it on the forms (manual encoding required,
               or OCR text that couldn't be read as a date/time)
  default      facility default from config (HCI fields)           "facility default"
  empty        nothing written in that logbook box (found blank by  "Empty in logbook"
               the computer, or marked empty by staff)

Served by GET /api/claims/<id>/form-data (routes/claims_routes.py).
"""
from datetime import date, datetime
from decimal import Decimal

from philhealth.field_catalog import (
    AUTO_CONFIG_KEYS,
    AUTO_OCR_KEYS,
    FORM_FIELDS,
    NON_FORM_KEYS,
    OCR_CATEGORY_KEYS,
)

ACCEPTED, NEEDS_CHECK, TYPED, REQUIRED, DEFAULT, EMPTY = (
    "accepted", "needs_check", "typed", "required", "default", "empty")

# Optional parts of an OCR'd value: a name may have no middle name, and an
# AM/PM marker only matters once there is a time.
_OPTIONAL_KEYS = {"patientMiddleName"}
_AM_PM_TIME = {"amPmAdmitted": "timeAdmitted", "amPmDischarge": "timeDischarge", "amPmDelivery": "deliveryTime"}

# The OCR routing statuses (logbook_pipeline.py), repeated here as plain
# strings so this module stays free of the OCR pipeline's imports.
_OCR_MANUAL, _OCR_NEEDS_CHECK, _OCR_EMPTY = "manual_encoding_required", "needs_check", "empty"


def _serialize(value, kind):
    if value is None:
        return None
    if kind == "bool":
        return bool(value)
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def _source_rows(rows, prenatal_visits, postpartum_care):
    tables = {
        "patients": rows.get("patient") or {},
        "encounters": rows.get("encounter") or {},
        "claims": rows.get("claim") or {},
    }
    prenatal = {r["visit_number"]: r for r in prenatal_visits or ()}
    postpartum = {r["care_item"]: r for r in postpartum_care or ()}
    return tables, prenatal, postpartum


def _stored_value(field, tables, prenatal, postpartum):
    if field.table == "claim_prenatal_visits":
        row = prenatal.get(field.row) or {}
    elif field.table == "claim_postpartum_care":
        row = postpartum.get(field.row) or {}
    else:
        row = tables[field.table]
    return _serialize(row.get(field.column), field.kind)


def _blank(value):
    return value is None or value == ""


def _ocr_field_status(ocr_field, key, value, data):
    """Status of one form key filled from one OCR'd logbook field."""
    if _blank(value):
        if ocr_field.get("marked_empty") or ocr_field.get("status") == _OCR_EMPTY:
            # Blank in the logbook itself - say so instead of "please type".
            return None if key in _AM_PM_TIME or key in _OPTIONAL_KEYS else EMPTY
        if key in _OPTIONAL_KEYS:
            return None
        if key in _AM_PM_TIME and _blank(data.get(_AM_PM_TIME[key])):
            return None
        return REQUIRED
    if ocr_field.get("status") == _OCR_MANUAL or ocr_field.get("edited"):
        return TYPED
    if ocr_field.get("status") == _OCR_NEEDS_CHECK:
        return NEEDS_CHECK
    return ACCEPTED


def build_form_data(rows, prenatal_visits=(), postpartum_care=(), session=None):
    """rows: {"patient", "encounter", "claim"} dicts (claims_store.get_claim).
    session: the claim's case session (case_session_store.get_session), or
    None for a claim that didn't come from an OCR review.

    Returns {
      "data":   {form_key: value} - every stored, non-null form value,
      "fields": {form_key: {"status", "category", "raw_text", "confidence",
                            "reason"}} - only keys with a source to show,
      "ocr_reference": {category: text} - OCR text with no single form field
                       (the free-text logbook address),
      "no_ocr_source": [form_key, ...] - form keys no OCR column can fill,
    }
    """
    tables, prenatal, postpartum = _source_rows(rows, prenatal_visits, postpartum_care)

    data = {}
    for key, field in FORM_FIELDS.items():
        if key in NON_FORM_KEYS:
            continue
        value = _stored_value(field, tables, prenatal, postpartum)
        if value is not None:
            data[key] = value

    fields = {}
    for key in AUTO_CONFIG_KEYS:
        if not _blank(data.get(key)):
            fields[key] = {"status": DEFAULT, "category": None, "raw_text": None,
                           "confidence": None, "reason": "Facility default from server config"}

    ocr_reference = {}
    ocr_fields = {f["category"]: f for f in ((session or {}).get("ocr_data") or {}).get("fields", [])}
    for category, ocr_field in ocr_fields.items():
        for key in OCR_CATEGORY_KEYS.get(category, ()):
            if key in NON_FORM_KEYS:
                text = _stored_value(FORM_FIELDS[key], tables, prenatal, postpartum) or ocr_field.get("value")
                if text:
                    ocr_reference[category] = text
                continue
            status = _ocr_field_status(ocr_field, key, data.get(key), data)
            if status is None:
                continue
            if status == REQUIRED:
                reason = ("Manual encoding required - OCR confidence was too low; type it from the logbook"
                          if ocr_field.get("status") == _OCR_MANUAL and _blank(ocr_field.get("value"))
                          else "The OCR text could not be read into this field - type it from the logbook")
            elif status == EMPTY:
                reason = "Nothing is written here in the logbook - fill it in only if you know it"
            else:
                reason = None
            fields[key] = {
                "status": status,
                "category": category,
                "raw_text": ocr_field.get("raw_text"),
                "confidence": ocr_field.get("confidence"),
                "reason": reason,
            }

    no_ocr_source = [
        key for key in FORM_FIELDS
        if key not in NON_FORM_KEYS and key not in AUTO_OCR_KEYS and key not in AUTO_CONFIG_KEYS
    ]
    return {"data": data, "fields": fields, "ocr_reference": ocr_reference, "no_ocr_source": no_ocr_source}
