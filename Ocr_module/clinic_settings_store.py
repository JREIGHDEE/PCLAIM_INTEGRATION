"""The clinic's own details, stored once and reused on every claim.

Implements the "System settings (entered once)" source in the research
design's Table 3.1 for clinic name, accreditation number and address, which
CF2 and CF4 need, the authorized HCI representative signing CSF Part V,
and the attending health care professional certifying CF4 Part VII.
Previously these were retyped per form.

Same conventions as the other stores: raw PyMySQL via db.get_db_cursor(),
plain dicts, a fixed column whitelist (never column names built from
caller input).
"""
import logging

from db import get_db_cursor
from errors import InvalidRequestError

logger = logging.getLogger(__name__)

# The only columns a caller may write. Anything else is rejected rather
# than silently ignored, so a typo surfaces instead of vanishing.
EDITABLE_COLUMNS = (
    "hci_name", "hci_pan", "hci_bldg", "hci_street",
    "hci_city", "hci_province", "hci_zip",
    "provider_rep_name", "provider_capacity",
    "attending_name", "attending_pan",
)

# Database column -> the form field key the frontend uses.
_TO_FORM_KEY = {
    "hci_name": "hciName",
    "hci_pan": "hciPAN",
    "hci_bldg": "hciBldg",
    "hci_street": "hciStreet",
    "hci_city": "hciCity",
    "hci_province": "hciProvince",
    "hci_zip": "hciZip",
    "provider_rep_name": "providerRepName",
    "provider_capacity": "providerCapacity",
    "attending_name": "cf4AttendingProvider",
    "attending_pan": "cf4ProviderPAN",
}
_TO_COLUMN = {v: k for k, v in _TO_FORM_KEY.items()}

MAX_LENGTHS = {
    "hci_name": 255, "hci_pan": 20, "hci_bldg": 255, "hci_street": 255,
    "hci_city": 100, "hci_province": 100, "hci_zip": 10,
    "provider_rep_name": 255, "provider_capacity": 255,
    "attending_name": 255, "attending_pan": 20,
}


def get_settings():
    """The clinic record as form-field keys (hciName, hciPAN, ...)."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT hci_name, hci_pan, hci_bldg, hci_street, hci_city, "
            "hci_province, hci_zip, provider_rep_name, provider_capacity, "
            "attending_name, attending_pan, "
            "updated_at FROM clinic_settings WHERE id = 1")
        row = cur.fetchone()

    if row is None:
        # The migration seeds row 1; this only happens if it was deleted.
        return {key: "" for key in _TO_COLUMN}

    out = {form_key: (row.get(col) or "")
           for col, form_key in _TO_FORM_KEY.items()}
    out["updated_at"] = row["updated_at"].isoformat() if row.get("updated_at") else None
    return out


def update_settings(values, updated_by=None):
    """Write the clinic record. `values` is keyed by form field (hciName...)."""
    if not isinstance(values, dict) or not values:
        raise InvalidRequestError("No clinic settings were provided.")

    unknown = set(values) - set(_TO_COLUMN)
    if unknown:
        raise InvalidRequestError(
            "Unknown clinic setting(s): " + ", ".join(sorted(unknown)))

    columns = {}
    for form_key, raw in values.items():
        column = _TO_COLUMN[form_key]
        text = ("" if raw is None else str(raw)).strip()
        limit = MAX_LENGTHS[column]
        if len(text) > limit:
            raise InvalidRequestError(
                f"{form_key} must be {limit} characters or fewer.")
        columns[column] = text

    # The PAN is printed into fixed digit boxes, so reject
    # anything that would not fit them rather than truncate silently.
    pan = columns.get("hci_pan")
    if pan:
        digits = "".join(ch for ch in pan if ch.isdigit())
        if len(digits) != 12:
            raise InvalidRequestError(
                "Accreditation number (PAN) must be 12 digits.")
        columns["hci_pan"] = digits

    # The attending professional's accreditation number fills the CSF's
    # 12 digit boxes (Part III), so the same rule applies.
    attending_pan = columns.get("attending_pan")
    if attending_pan:
        digits = "".join(ch for ch in attending_pan if ch.isdigit())
        if len(digits) != 12:
            raise InvalidRequestError(
                "Attending professional's accreditation number must be 12 digits.")
        columns["attending_pan"] = digits

    assignments = ", ".join(f"{c} = %s" for c in columns)
    params = list(columns.values()) + [updated_by]

    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE clinic_settings SET {assignments}, updated_by = %s WHERE id = 1",
            params)

    logger.info("Clinic settings updated by user id %s", updated_by)
    return get_settings()
