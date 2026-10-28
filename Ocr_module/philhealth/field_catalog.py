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
    # claims - maternity / delivery
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
    # claims - physical exam
    # claims - obstetric history
    "obTerm": _claims("ob_term", "number"),
    "obPreterm": _claims("ob_preterm", "number"),
    "obAbortion": _claims("ob_abortion", "number"),
    "obLiving": _claims("ob_living", "number"),
}

# Keys that are not PClaimAssist form inputs (see patientAddress above).
NON_FORM_KEYS = {"patientAddress"}

# Every other form key is kept as typed in claims.form_values (migration 010):
# PClaimAssist saves the whole form with the claim (PUT /api/claims/<id>/
# form-values, claims_store.save_form_values) and puts it back when the claim
# is opened again (GET /api/claims/<id>/form-data "saved_values"). These are
# printed-only details and per-claim choices that nothing on the server reads
# by column, so they get no column of their own. Each one is listed here on
# purpose: a new form key must be added either to FORM_FIELDS (a column) or
# here, or test_form_prefill fails.
FORM_VALUES_KEYS = frozenset({
    # Per-claim choices and values worked out on the page (whether the member is
    # the patient, the diagnosis package, the age at admission) and the clinic's
    # building/ZIP as copied onto this claim from Clinic Details.
    "dxDrugsAdded", "dxPackage", "hciBldg", "hciZip", "memberIsPatient", "patientAge",
    # Patient details: "No contact info" (phone and email left blank).
    "noContact",
    # PMRF: the member's mother's and spouse's name suffix.
    "motherNameExt", "spouseNameExt",
    # The APGAR score at 1 minute (the 5-minute score is claims.apgar_score).
    "apgarScore1",
    # CSF: who signs Parts I and III and for whom, the employer's certification,
    # the health care professionals, the clinic's representative, case rates.
    "csfFirstCaseRate", "csfSecondCaseRate", "employerCapacity", "employerRepName",
    "employerSignedDate", "hciProf1AccredNo", "hciProf1DateSigned", "hciProf1Name",
    "hciProf2AccredNo", "hciProf2DateSigned", "hciProf2Name", "hciProf3AccredNo",
    "hciProf3DateSigned", "hciProf3Name", "memberSignedDate", "memberSignerType",
    "patientReason", "patientReasonOther", "patientRepName", "patientRepRelationship",
    "patientRepRelationshipOther", "patientRepSignedDate", "patientSignerType",
    "providerCapacity", "providerRepName", "providerSignedDate", "repReason", "repReasonOther",
    "repRelationship", "repRelationshipOther", "repSignedDate",
    # CF2: referral, the discharge diagnoses and their procedures, special
    # procedures and newborn care, the professionals and III-B consent.
    "cf2EssentialNewbornCare", "cf2NewbornCare", "cf2PatientReason", "cf2PatientReasonOther",
    "cf2PatientRepName", "cf2PatientRepRelationship", "cf2PatientRepRelationshipOther",
    "cf2PatientRepSignedDate", "cf2ProcDates1", "cf2ProcDates2", "cf2ProcDates3",
    "cf2ProcDates4", "cf2ProcDates5", "cf2ProcDates6", "cf2ProcDates7", "cf2ProcDates8",
    "cf2Prof1AccredNo", "cf2Prof1Copay", "cf2Prof1CopayAmount", "cf2Prof1DateSigned",
    "cf2Prof1Name", "cf2Prof2AccredNo", "cf2Prof2Copay", "cf2Prof2CopayAmount",
    "cf2Prof2DateSigned", "cf2Prof2Name", "cf2Prof3AccredNo", "cf2Prof3Copay",
    "cf2Prof3CopayAmount", "cf2Prof3DateSigned", "cf2Prof3Name", "cf2ProviderCapacity",
    "cf2ProviderRepName", "cf2ProviderSignedDate", "cf2SpecialProcedureDetail",
    "cf2SpecialProcedures", "cf2TbPhase", "dxADateI", "dxADateII", "dxADateIII", "dxADiagnosis",
    "dxAIcd10", "dxALatI", "dxALatII", "dxALatIII", "dxAProcI", "dxAProcII", "dxAProcIII",
    "dxARvsI", "dxARvsII", "dxARvsIII", "dxBDateI", "dxBDateII", "dxBDateIII", "dxBDiagnosis",
    "dxBIcd10", "dxBLatI", "dxBLatII", "dxBLatIII", "dxBProcI", "dxBProcII", "dxBProcIII",
    "dxBRvsI", "dxBRvsII", "dxBRvsIII", "referralCity", "referralHciName", "referralProvince",
    "referralStreet", "referralZip", "referredByHCI",
    # CF4: complaint, history, examination, vitals, course in the ward, drugs,
    # outcome and the attending provider.
    "cf4Abdomen", "cf4AbdomenOthers", "cf4AlteredSensorium", "cf4AttendingProvider", "cf4Chest",
    "cf4ChestOthers", "cf4ChiefComplaint", "cf4CourseDate1", "cf4CourseDate2",
    "cf4CourseExtraSheet", "cf4CourseOrder1", "cf4CourseOrder2", "cf4Cvs", "cf4CvsOthers",
    "cf4DrugCost1", "cf4DrugCost2", "cf4DrugCost3", "cf4DrugDose1", "cf4DrugDose2",
    "cf4DrugDose3", "cf4DrugName1", "cf4DrugName2", "cf4DrugName3", "cf4DrugQty1",
    "cf4DrugQty2", "cf4DrugQty3", "cf4DrugsExtraSheet", "cf4FinalDiagnosis", "cf4GeneralSurvey",
    "cf4Gu", "cf4GuOthers", "cf4Heent", "cf4HeentOthers", "cf4Height",
    "cf4HistoryPresentIllness", "cf4IcdCode", "cf4LmpNA", "cf4Neuro", "cf4NeuroOthers",
    "cf4PainSite", "cf4PastMedicalHistory", "cf4ProviderPAN", "cf4ProviderSignedDate",
    "cf4ReferralHci", "cf4ReferralReason", "cf4Referred", "cf4RvsCode", "cf4Skin",
    "cf4SkinOthers", "cf4SurgicalProcedure", "cf4SymptomOther", "cf4Symptoms",
    "cf4TimeAdmittedDigits", "cf4TimeDischargeDigits", "cf4TransferReason", "cf4VitalBP",
    "cf4VitalHR", "cf4VitalRR", "cf4VitalTemp", "cf4Weight",
    # PMRF: dependents, mailing address, name details (mononym, no middle
    # name), IDs, amendments, registration purpose and the member's signature.
    "acrICardNo", "amendCivilStatus", "amendCivilStatusFrom", "amendCivilStatusTo", "amendDOB",
    "amendDOBFrom", "amendDOBTo", "amendName", "amendNameFrom", "amendNameTo",
    "amendPersonalInfo", "amendPersonalInfoFrom", "amendPersonalInfoTo", "amendSex",
    "amendSexFrom", "amendSexTo", "businessPhone", "dep1Disability", "dep1Mononym",
    "dep1NoMiddleName", "dep2Citizenship", "dep2DOB", "dep2Disability", "dep2Ext",
    "dep2FirstName", "dep2LastName", "dep2MiddleName", "dep2Mononym", "dep2NoMiddleName",
    "dep2Relationship", "dep3Citizenship", "dep3DOB", "dep3Disability", "dep3Ext",
    "dep3FirstName", "dep3LastName", "dep3MiddleName", "dep3Mononym", "dep3NoMiddleName",
    "dep3Relationship", "dep4Citizenship", "dep4DOB", "dep4Disability", "dep4Ext",
    "dep4FirstName", "dep4LastName", "dep4MiddleName", "dep4Mononym", "dep4NoMiddleName",
    "dep4Relationship", "groupEnrollmentNo", "mailingAddrBarangay", "mailingAddrBuilding",
    "mailingAddrCity", "mailingAddrLot", "mailingAddrProvince", "mailingAddrStreet",
    "mailingAddrSubdivision", "mailingAddrUnit", "mailingAddrZip", "mailingSameAsAbove",
    "memberMononym", "memberNoMiddleName", "memberSignatureDate", "memberSignatureName",
    "motherMononym", "motherNoMiddleName", "patientCitizenship", "philsysId", "praSrrvNo",
    "preferredKonsulta", "proofOfIncome", "pwdIdNo", "registrationPurpose", "spouseMononym",
    "spouseNoMiddleName", "tin",
})

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
# Form keys worked out from a logbook column rather than copied from it
# (case_bridge.draft_patient_and_encounter): the address split into the
# forms' parts, and the patient's sex when the name or diagnosis makes it
# plain. Always shown as "From scan - please check", never as certain.
DERIVED_OCR_KEYS = {
    "ADDRESS": ("addrLot", "addrStreet", "addrSubdivision", "addrBarangay", "addrCity", "addrProvince"),
    "NAME": ("patientSex",),
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
# Entries omitted here - out of v1 scope (no OCR source and no
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
