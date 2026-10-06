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
from collections import namedtuple
from datetime import date

# ---------------------------------------------------------------------------
# THE field mapping - single source of truth for both the Python backend and
# the PClaimAssist forms. Every key is a PClaimAssist form key (js/app.js
# state.data - the `data-autofill` key on each input), mapped to where its
# value is stored. The browser never maps database columns itself: it loads
# GET /api/claims/<id>/form-data, which is built from this table and returns
# values already keyed by form key (philhealth/form_prefill.py).
# test_form_prefill.py fails if a key here is missing from js/app.js.
#
# FormField.kind drives serialization: "text" | "date" (ISO YYYY-MM-DD) |
# "time" (24h HH:MM) | "bool" | "number". FormField.row is the child-table
# row a field lives in (prenatal visit number / postpartum care item).
# ---------------------------------------------------------------------------
FormField = namedtuple("FormField", "table column kind row", defaults=("text", None))


def _claims(column, kind="text"):
    return FormField("claims", column, kind)


FORM_FIELDS = {
    # patients
    "patientLastName": FormField("patients", "last_name"),
    "patientFirstName": FormField("patients", "first_name"),
    "patientMiddleName": FormField("patients", "middle_name"),
    "patientNameExt": FormField("patients", "name_ext"),
    "patientDOB": FormField("patients", "date_of_birth", "date"),
    "patientSex": FormField("patients", "sex"),
    "patientPIN": FormField("patients", "pin"),
    # Free-text logbook address. Not a form key: the forms split the address
    # into addrStreet/addrBarangay/... (PMRF member address), and the OCR
    # text is never split by guessing - it is shown to staff as a reference.
    "patientAddress": FormField("patients", "address"),
    # encounters
    "dateAdmitted": FormField("encounters", "date_admitted", "date"),
    "timeAdmitted": FormField("encounters", "time_admitted", "time"),
    "amPmAdmitted": FormField("encounters", "am_pm_admitted"),
    "dateDischarge": FormField("encounters", "date_discharge", "date"),
    "timeDischarge": FormField("encounters", "time_discharge", "time"),
    "amPmDischarge": FormField("encounters", "am_pm_discharge"),
    "disposition": FormField("encounters", "disposition"),
    "accommodation": FormField("encounters", "accommodation"),
    "chiefComplaint": FormField("encounters", "chief_complaint"),
    "admissionDx": FormField("encounters", "admission_dx"),
    "dischargeDx": FormField("encounters", "discharge_dx"),
    # claims - HCI
    "hciPAN": _claims("hci_pan"),
    "hciName": _claims("hci_name"),
    "hciStreet": _claims("hci_street"),
    "hciCity": _claims("hci_city"),
    "hciProvince": _claims("hci_province"),
    # claims - member
    "memberPIN": _claims("member_pin"),
    "memberLastName": _claims("member_last_name"),
    "memberFirstName": _claims("member_first_name"),
    "memberMiddleName": _claims("member_middle_name"),
    "memberNameExt": _claims("member_name_ext"),
    "memberDOB": _claims("member_dob", "date"),
    "memberSex": _claims("member_sex"),
    "relationship": _claims("relationship"),
    # claims - employer (CSF)
    "employerPEN": _claims("employer_pen"),
    "employerPhone": _claims("employer_phone"),
    "employerName": _claims("employer_name"),
    # claims - member profile (PMRF)
    "civilStatus": _claims("civil_status"),
    "placeOfBirth": _claims("place_of_birth"),
    "citizenship": _claims("citizenship"),
    "motherLastName": _claims("mother_last_name"),
    "motherFirstName": _claims("mother_first_name"),
    "motherMiddleName": _claims("mother_middle_name"),
    "spouseLastName": _claims("spouse_last_name"),
    "spouseFirstName": _claims("spouse_first_name"),
    "spouseMiddleName": _claims("spouse_middle_name"),
    "memberType": _claims("member_type"),
    "profession": _claims("profession"),
    "monthlyIncome": _claims("monthly_income"),
    # claims - member address & contact (PMRF)
    "addrUnit": _claims("addr_unit"),
    "addrBuilding": _claims("addr_building"),
    "addrLot": _claims("addr_lot"),
    "addrStreet": _claims("addr_street"),
    "addrSubdivision": _claims("addr_subdivision"),
    "addrBarangay": _claims("addr_barangay"),
    "addrCity": _claims("addr_city"),
    "addrProvince": _claims("addr_province"),
    "addrZip": _claims("addr_zip"),
    "mobile": _claims("mobile"),
    "homePhone": _claims("home_phone"),
    "email": _claims("email"),
    # claims - maternity / delivery (CF3)
    "lmp": _claims("lmp", "date"),
    "ageOfMenarche": _claims("age_of_menarche", "number"),
    "gravida": _claims("gravida", "number"),
    "para": _claims("para", "number"),
    "expectedDD": _claims("expected_dd", "date"),
    "deliveryDate": _claims("delivery_date", "date"),
    "deliveryTime": _claims("delivery_time", "time"),
    "amPmDelivery": _claims("am_pm_delivery"),
    "mannerOfDelivery": _claims("manner_of_delivery"),
    "fetalOutcome": _claims("fetal_outcome"),
    "babySex": _claims("baby_sex"),
    "birthWeight": _claims("birth_weight"),
    "apgarScore": _claims("apgar_score", "number"),
    "briefHistory": _claims("brief_history"),
    # claims - physical exam, course, labs (CF3 part I)
    "vitalBP": _claims("vital_bp"),
    "vitalCR": _claims("vital_cr"),
    "vitalRR": _claims("vital_rr"),
    "vitalTemp": _claims("vital_temp"),
    "peHEENT": _claims("pe_heent"),
    "peAbdomen": _claims("pe_abdomen"),
    "peChestLungs": _claims("pe_chest_lungs"),
    "peGU": _claims("pe_gu"),
    "peCVS": _claims("pe_cvs"),
    "peSkinExtremities": _claims("pe_skin_extremities"),
    "peNeuroExam": _claims("pe_neuro_exam"),
    "courseInWards": _claims("course_in_wards"),
    "labFindings": _claims("lab_findings"),
    # claims - maternity care package (CF3 part II)
    "initialPrenatalDate": _claims("initial_prenatal_date", "date"),
    "vitalSignsNormal": _claims("vital_signs_normal", "bool"),
    "pregnancyLowRisk": _claims("pregnancy_low_risk", "bool"),
    "obTerm": _claims("ob_term", "number"),
    "obPreterm": _claims("ob_preterm", "number"),
    "obAbortion": _claims("ob_abortion", "number"),
    "obLiving": _claims("ob_living", "number"),
    "riskMultiplePregnancy": _claims("risk_multiple_pregnancy", "bool"),
    "riskOvarianCyst": _claims("risk_ovarian_cyst", "bool"),
    "riskMyomaUteri": _claims("risk_myoma_uteri", "bool"),
    "riskPlacentaPrevia": _claims("risk_placenta_previa", "bool"),
    "riskMiscarriages": _claims("risk_miscarriages", "bool"),
    "riskStillbirth": _claims("risk_stillbirth", "bool"),
    "riskPreeclampsia": _claims("risk_preeclampsia", "bool"),
    "riskEclampsia": _claims("risk_eclampsia", "bool"),
    "riskPrematureContraction": _claims("risk_premature_contraction", "bool"),
    "riskHypertension": _claims("risk_hypertension", "bool"),
    "riskHeartDisease": _claims("risk_heart_disease", "bool"),
    "riskDiabetes": _claims("risk_diabetes", "bool"),
    "riskThyroidDisorder": _claims("risk_thyroid_disorder", "bool"),
    "riskObesity": _claims("risk_obesity", "bool"),
    "riskAsthma": _claims("risk_asthma", "bool"),
    "riskEpilepsy": _claims("risk_epilepsy", "bool"),
    "riskRenalDisease": _claims("risk_renal_disease", "bool"),
    "riskBleedingDisorders": _claims("risk_bleeding_disorders", "bool"),
    "riskPrevCesarian": _claims("risk_prev_cesarian", "bool"),
    "riskUterineMyomectomy": _claims("risk_uterine_myomectomy", "bool"),
    "mcpOrientation": _claims("mcp_orientation"),
    "obstetricIndex": _claims("obstetric_index"),
    "pregnancyUterineAOG": _claims("pregnancy_uterine_aog"),
    "presentation": _claims("presentation"),
    "postpartumFollowupDate": _claims("postpartum_followup_date", "date"),
    "attendingPhysicianName": _claims("attending_physician_name"),
    "dateSigned": _claims("date_signed", "date"),
}

# CF3 follow-up prenatal visits 2-12: pncDate2..pncTemp12 -> one
# claim_prenatal_visits row per visit number.
_PRENATAL_COLUMNS = {
    "Date": ("visit_date", "date"), "Aog": ("aog", "text"), "Weight": ("weight", "number"),
    "Cr": ("cr", "text"), "Rr": ("rr", "text"), "Bp": ("bp", "text"), "Temp": ("temp", "number"),
}
for _visit in range(2, 13):
    for _suffix, (_column, _kind) in _PRENATAL_COLUMNS.items():
        FORM_FIELDS[f"pnc{_suffix}{_visit}"] = FormField("claim_prenatal_visits", _column, _kind, _visit)

# CF3 postpartum care checklist: pp<Item>Done / pp<Item>Remarks -> one
# claim_postpartum_care row per care_item.
_POSTPARTUM_ITEMS = {
    "Perineal": "perineal", "Complications": "complications", "Breastfeeding": "breastfeeding",
    "FamilyPlanning": "family_planning", "FPService": "fp_service",
    "ReferredVSS": "referred_vss", "ScheduleNext": "schedule_next",
}
for _item, _care_item in _POSTPARTUM_ITEMS.items():
    FORM_FIELDS[f"pp{_item}Done"] = FormField("claim_postpartum_care", "done", "bool", _care_item)
    FORM_FIELDS[f"pp{_item}Remarks"] = FormField("claim_postpartum_care", "remarks", "text", _care_item)

# Keys that are not PClaimAssist form inputs (see patientAddress above).
NON_FORM_KEYS = {"patientAddress"}

# The CF2/CSF subset the server-side claim review/export works on
# (mapping_service.map_claim, GET /api/claims/<id>), in display order.
_CLAIM_REVIEW_KEYS = (
    "patientLastName", "patientFirstName", "patientMiddleName", "patientNameExt",
    "patientDOB", "patientSex", "patientPIN", "patientAddress",
    "dateAdmitted", "timeAdmitted", "amPmAdmitted", "dateDischarge", "timeDischarge",
    "amPmDischarge", "disposition", "accommodation", "chiefComplaint", "admissionDx",
    "dischargeDx",
    "hciPAN", "hciName", "hciStreet", "hciCity", "hciProvince",
    "memberPIN", "memberLastName", "memberFirstName", "memberMiddleName", "memberNameExt",
    "memberDOB", "memberSex", "relationship",
    "employerPEN", "employerPhone", "employerName",
    "deliveryDate", "deliveryTime", "amPmDelivery",
)
KEY_SOURCE = {key: (FORM_FIELDS[key].table, FORM_FIELDS[key].column) for key in _CLAIM_REVIEW_KEYS}

# Which form keys each OCR'd logbook column fills (case_bridge.py drafts
# these; the logbook review shows them as each field's target). CASE # is
# lookup-only - it keys the case session, not a form field.
OCR_CATEGORY_KEYS = {
    "NAME": ("patientLastName", "patientFirstName", "patientMiddleName"),
    "BDAY": ("patientDOB",),
    "ADDRESS": ("patientAddress",),
    "DATE & TIME OF ADMISSION": ("dateAdmitted", "timeAdmitted", "amPmAdmitted"),
    "DATE & TIME OF DISCHARGE": ("dateDischarge", "timeDischarge", "amPmDischarge"),
    "DATE & TIME OF DELIVERY": ("deliveryDate", "deliveryTime", "amPmDelivery"),
    "ADMITTING DIAGNOSIS": ("admissionDx",),
    "FINAL DIAGNOSIS": ("dischargeDx",),
}
# Logbook columns a claim can't be created without (the NOT NULL patient/
# encounter columns) - staff must type these in the OCR review itself;
# any other "manual encoding required" field may be left for the forms.
OCR_CLAIM_REQUIRED_CATEGORIES = ("NAME", "BDAY", "DATE & TIME OF ADMISSION")

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
    "patientAddress": "Patient Address",
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
    "deliveryDate": "Date of Delivery",
    "deliveryTime": "Time of Delivery",
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

# Ported from PClaimAssist/js/app.js DATE_FIELDS, plus deliveryDate (added
# once case_bridge.py started capturing "DATE & TIME OF DELIVERY" from the
# OCR logbook - see field_catalog KEY_SOURCE above). expectedDD/lmp remain
# CF3-only entries omitted here - out of v1 scope (no OCR source and no
# backend route reads/writes them yet).
DATE_FIELDS = {"memberDOB", "patientDOB", "dateAdmitted", "dateDischarge", "deliveryDate"}

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
AUTO_OCR_KEYS = {key for keys in OCR_CATEGORY_KEYS.values() for key in keys}
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
