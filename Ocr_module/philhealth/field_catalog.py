"""Canonical CF2/CSF field vocabulary.

Everything in this module is ported from PClaimAssist's own
js/app.js (state.data, VAL_FIELDS, getComputedValue, formatDate,
formatTime12h, bareTime) - these are the field names, required-field
lists, and computed-value rules PClaimAssist's client-side form/PDF
pipeline already uses. Nothing here is invented: a field is only in this
catalog because it already appears in that JS file or as a NOT NULL column
in database/schema.sql.

Pure data + pure functions only - no DB/Flask imports, so this (and anything
built on top of it) can be unit tested with plain dicts.
"""
import re
from datetime import date

# ---------------------------------------------------------------------------
# Where each field ultimately lives (table, column). Used both to build the
# mapping-table "Internal Field" column and by claims_store to know which
# table a manual correction belongs to.
# ---------------------------------------------------------------------------
KEY_SOURCE = {
    # patients
    "patientLastName": ("patients", "last_name"),
    "patientFirstName": ("patients", "first_name"),
    "patientMiddleName": ("patients", "middle_name"),
    "patientNameExt": ("patients", "name_ext"),
    "patientDOB": ("patients", "date_of_birth"),
    "patientSex": ("patients", "sex"),
    "patientPIN": ("patients", "pin"),
    # encounters
    "dateAdmitted": ("encounters", "date_admitted"),
    "timeAdmitted": ("encounters", "time_admitted"),
    "amPmAdmitted": ("encounters", "am_pm_admitted"),
    "dateDischarge": ("encounters", "date_discharge"),
    "timeDischarge": ("encounters", "time_discharge"),
    "amPmDischarge": ("encounters", "am_pm_discharge"),
    "disposition": ("encounters", "disposition"),
    "accommodation": ("encounters", "accommodation"),
    "chiefComplaint": ("encounters", "chief_complaint"),
    "admissionDx": ("encounters", "admission_dx"),
    "dischargeDx": ("encounters", "discharge_dx"),
    # claims - HCI
    "hciPAN": ("claims", "hci_pan"),
    "hciName": ("claims", "hci_name"),
    "hciStreet": ("claims", "hci_street"),
    "hciCity": ("claims", "hci_city"),
    "hciProvince": ("claims", "hci_province"),
    # claims - member
    "memberPIN": ("claims", "member_pin"),
    "memberLastName": ("claims", "member_last_name"),
    "memberFirstName": ("claims", "member_first_name"),
    "memberMiddleName": ("claims", "member_middle_name"),
    "memberNameExt": ("claims", "member_name_ext"),
    "memberDOB": ("claims", "member_dob"),
    "memberSex": ("claims", "member_sex"),
    "relationship": ("claims", "relationship"),
    # claims - employer
    "employerPEN": ("claims", "employer_pen"),
    "employerPhone": ("claims", "employer_phone"),
    "employerName": ("claims", "employer_name"),
}

# Human labels for every leaf field this catalog knows about (used for the
# review table's "PhilHealth Field" column). Required-field labels below in
# VAL_FIELDS take precedence when both exist for the same key.
FIELD_LABELS = {
    "hciPAN": "HCI Accreditation No. (PAN)",
    "hciName": "Health Care Institution Name",
    "hciStreet": "HCI Street",
    "hciCity": "HCI City",
    "hciProvince": "HCI Province",
    "patientLastName": "Patient Last Name",
    "patientFirstName": "Patient First Name",
    "patientMiddleName": "Patient Middle Name",
    "patientNameExt": "Patient Name Extension",
    "patientDOB": "Patient Date of Birth",
    "patientSex": "Patient Sex",
    "patientPIN": "Patient / Dependent PIN",
    "dateAdmitted": "Date Admitted",
    "timeAdmitted": "Time Admitted",
    "dateDischarge": "Date Discharged",
    "timeDischarge": "Time Discharged",
    "disposition": "Patient Disposition",
    "accommodation": "Type of Accommodation",
    "admissionDx": "Admission Diagnosis",
    "dischargeDx": "Discharge Diagnosis",
    "memberPIN": "Member PhilHealth PIN",
    "memberLastName": "Member Last Name",
    "memberFirstName": "Member First Name",
    "memberMiddleName": "Member Middle Name",
    "memberNameExt": "Member Name Extension",
    "memberDOB": "Member Date of Birth",
    "relationship": "Relationship to Member",
    "employerPEN": "Employer PEN",
    "employerPhone": "Employer Phone",
    "employerName": "Employer / Business Name",
}

# Ported verbatim from PClaimAssist/js/app.js VAL_FIELDS (cf2/csf only - the
# project's own per-form required-field list, not invented here).
VAL_FIELDS = {
    "cf2": [
        {"key": "hciPAN", "label": "HCI Accreditation No. (PAN)"},
        {"key": "hciName", "label": "Health Care Institution Name"},
        {"key": "patientName", "label": "Patient Name"},
        {"key": "dateAdmitted", "label": "Date Admitted"},
        {"key": "dateDischarge", "label": "Date Discharged"},
        {"key": "disposition", "label": "Patient Disposition"},
        {"key": "accommodation", "label": "Type of Accommodation"},
        {"key": "admissionDx", "label": "Admission Diagnosis"},
        {"key": "dischargeDx", "label": "Discharge Diagnosis"},
    ],
    "csf": [
        {"key": "memberPIN", "label": "Member PhilHealth PIN"},
        {"key": "memberName", "label": "Member Name"},
        {"key": "memberDOB", "label": "Member Date of Birth"},
        {"key": "patientPIN", "label": "Patient / Dependent PIN"},
        {"key": "patientName", "label": "Patient Name"},
        {"key": "relationship", "label": "Relationship to Member"},
        {"key": "dateAdmitted", "label": "Date Admitted"},
        {"key": "dateDischarge", "label": "Date Discharged"},
        {"key": "patientDOB", "label": "Patient Date of Birth"},
    ],
}

# Ported from PClaimAssist/js/app.js DATE_FIELDS (CF3-only entries -
# deliveryDate/expectedDD/lmp - omitted, out of v1 scope).
DATE_FIELDS = {"memberDOB", "patientDOB", "dateAdmitted", "dateDischarge"}

# Schema ENUM columns this catalog validates against (database/schema.sql).
ENUM_CHOICES = {
    "disposition": ("Improved", "Recovered", "Transferred", "HAMA", "Absconded", "Expired"),
    "accommodation": ("Non-Private", "Private", "Ward", "ICU/NICU"),
    "relationship": ("Self", "Spouse", "Child", "Parent", "Sibling"),
}

# Keys the OCR bridge (case_bridge.py) can fill from a reviewed case_session,
# vs. keys defaulted from a fixed facility config, vs. everything else - which
# requires manual/provider input because no source data exists anywhere in
# the system for it. Used to annotate the review UI's "Source" column.
AUTO_OCR_KEYS = {
    "patientLastName", "patientFirstName", "patientMiddleName", "patientNameExt",
    "patientDOB", "dateAdmitted", "timeAdmitted", "amPmAdmitted",
    "dateDischarge", "timeDischarge", "amPmDischarge", "admissionDx", "dischargeDx",
}
AUTO_CONFIG_KEYS = {"hciPAN", "hciName", "hciStreet", "hciCity", "hciProvince"}


def source_kind(key):
    """'auto_ocr' | 'auto_config' | 'manual' - for the review UI's Source column."""
    if key in AUTO_OCR_KEYS:
        return "auto_ocr"
    if key in AUTO_CONFIG_KEYS:
        return "auto_config"
    return "manual"


# From PClaimAssist/index.html's own PIN input placeholders
# ("12-345678901-2" / "##-#########-#") - not an invented format.
PIN_PATTERN = re.compile(r"^\d{2}-\d{9}-\d{1}$")


def format_date(iso_date):
    """Port of app.js formatDate: 'YYYY-MM-DD' -> 'MM-DD-YYYY'.

    Returns '' for falsy input, and the original string unchanged if it
    doesn't parse (mirrors the JS's `if (isNaN(d)) return iso`).
    """
    if not iso_date:
        return ""
    try:
        y, m, d = str(iso_date).split("-")[:3]
        parsed = date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return str(iso_date)
    return f"{parsed.month:02d}-{parsed.day:02d}-{parsed.year}"


def format_time_12h(hhmm):
    """Port of app.js formatTime12h: 'HH:MM' (24h) -> 'hh:mm AM/PM'."""
    if not hhmm:
        return ""
    parts = str(hhmm).split(":")
    if len(parts) < 2:
        return str(hhmm)
    try:
        h = int(parts[0])
    except ValueError:
        return str(hhmm)
    period = "PM" if h >= 12 else "AM"
    h = h % 12 or 12
    return f"{h:02d}:{parts[1]} {period}"


def bare_time(hhmm):
    """Port of app.js bareTime: formatTime12h() with the AM/PM suffix stripped."""
    return re.sub(r"\s*(AM|PM)$", "", format_time_12h(hhmm))


def is_valid_date_string(value):
    """True if `value` parses as an ISO 'YYYY-MM-DD' date."""
    if not value:
        return False
    try:
        y, m, d = str(value).split("-")[:3]
        date(int(y), int(m), int(d))
        return True
    except (ValueError, TypeError):
        return False


def resolve_computed_value(key, data):
    """Port of app.js getComputedValue, restricted to CF2/CSF's computed keys.

    `data` is a flat dict of camelCase field values (never mutated). Falls
    back to a plain `data.get(key, '')` lookup for any key that isn't one of
    the special cases below, exactly like the JS version's `default` case.
    """
    if key in DATE_FIELDS:
        value = data.get(key)
        return format_date(value) if value else ""

    if key == "patientName":
        parts = [data.get("patientLastName"), data.get("patientFirstName"),
                 data.get("patientNameExt"), data.get("patientMiddleName")]
        return " ".join(p.strip() for p in parts if p and p.strip())

    if key == "memberName":
        parts = [data.get("memberLastName"), data.get("memberFirstName"),
                 data.get("memberNameExt"), data.get("memberMiddleName")]
        return " ".join(p.strip() for p in parts if p and p.strip())

    if key == "hciAddress":
        parts = [data.get("hciStreet"), data.get("hciCity"), data.get("hciProvince")]
        return ", ".join(p for p in parts if p)

    if key == "timeAdmittedStr":
        return format_time_12h(data.get("timeAdmitted"))

    if key == "timeDischargeStr":
        return format_time_12h(data.get("timeDischarge"))

    return data.get(key) or ""
