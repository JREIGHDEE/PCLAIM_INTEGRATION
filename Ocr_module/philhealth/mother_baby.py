"""Mother or baby: which a maternity logbook entry is about, and what a
baby's claim takes from its mother's.

A maternity clinic files a claim for the mother and one for her newborn.
Most of the baby's forms repeat the mother's: the PhilHealth member
(usually the mother herself), the home address and contact, the member's
profile and employer. So:

  classify_entry()   mother / baby / unknown for one logbook entry, with
                     the reason in plain words for staff.
  rank_mothers()     the mother's claims a baby's claim most likely
                     belongs to, best first: she gave birth on the baby's
                     birthday, shares its surname, is just above it in
                     the logbook.
  values_for_baby()  the mother's form values a baby's claim copies, each
                     with who it is about and why, so the forms can show
                     what was applied to whom.

Pure (no DB, no Flask), like the rest of philhealth/.
"""
import difflib
import re
from datetime import date

MOTHER, BABY = "mother", "baby"
ROLES = (MOTHER, BABY, "other")

# A logbook diagnosis is handwriting read by OCR: "WEL BABY CARE",
# "WELL BAnY CAR", "PKENATAL CHECK UP", "POSR PARTUN UISIT". Words are
# matched loosely, one at a time.
_FUZZY_CUTOFF = 0.75
# Words only a (pregnant, delivering or recently delivered) woman's entry
# has. Checked before the baby words: a delivery diagnosis names the baby
# too ("DELIVERED VIA NSVD TO A LIVE TERM BABY BOY").
_MOTHER_WORDS = ("PRENATAL", "POSTPARTUM", "PARTUM", "DELIVERED", "DELIVERY", "PREGNANCY",
                 "PREGNANT", "LABOR", "LABOUR", "CESAREAN", "PUERPERIUM", "PLANNING")
_MOTHER_EXACT = re.compile(r"\bG\s?\d+\s?P\s?\d+|\bAOG\b|\bPUFT\b|\bN?SVD\b|\bPPTL\b|\bC-?SECTION\b",
                           re.IGNORECASE)
_BABY_WORDS = ("NEWBORN", "IMMUNIZATION", "VACCINATION", "SCREENING")
_BABY_EXACT = re.compile(r"\bBCG\b|\bNB\s+SCREEN", re.IGNORECASE)
# "BABY GIRL DELA CRUZ" is how a newborn without a name yet is written.
# "BABY" alone is also a common first name, so this only counts when the
# diagnosis says nothing either way.
_NEWBORN_NAME = re.compile(r"^\s*(BABY|BB\.?)\s+(GIRL|BOY)\b", re.IGNORECASE)

# Younger than this at admission: a baby. Older: not one.
_BABY_MAX_DAYS = 365
_MOTHER_MIN_YEARS = 12


def _words(text):
    return re.findall(r"[A-Z0-9]+", str(text or "").upper())


def _close(word, targets):
    return len(word) >= 3 and bool(difflib.get_close_matches(word, targets, n=1, cutoff=_FUZZY_CUTOFF))


def _mother_dx(text):
    found = _MOTHER_EXACT.search(text or "")
    if found:
        return found.group().strip()
    words = _words(text)
    # "POST PARTUM" written as two words.
    for word in words + ["".join(pair) for pair in zip(words, words[1:])]:
        if _close(word, _MOTHER_WORDS):
            return word
    return None


def _baby_dx(text):
    found = _BABY_EXACT.search(text or "")
    if found:
        return found.group().strip()
    words = _words(text)
    if any(_close(w, _BABY_WORDS) for w in words):
        return " ".join(words)
    # "WELL BABY CARE" as OCR reads it: "WEL BABY CARE", "WEZL 13AY CARE".
    baby = any(_close(w, ("BABY",)) for w in words)
    well = any(_close(w, ("WELL",)) for w in words)
    care = any(_close(w, ("CARE",)) for w in words)
    if (baby and (well or care)) or (well and care):
        return " ".join(words)
    return None


def _iso(value):
    if isinstance(value, date):
        return value
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(value or ""))
    if not match:
        return None
    try:
        return date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def _age_days(dob, on):
    dob, on = _iso(dob), _iso(on)
    if not dob or not on or dob > on:
        return None  # an OCR'd birthday after the visit is no age at all
    return (on - dob).days


def classify_entry(entry):
    """entry: {"name", "dob", "date_admitted", "delivery_date",
    "admission_dx", "discharge_dx"} (ISO dates, any may be missing).

    Returns {"role": "mother" | "baby" | None, "reason": str}. None means
    the entry doesn't say - staff choose."""
    dx = " ".join(str(entry.get(k) or "") for k in ("admission_dx", "discharge_dx"))
    found = _mother_dx(dx)
    if found:
        return {"role": MOTHER, "reason": f"The diagnosis says \"{found}\" (pregnancy or birth care)"}
    found = _baby_dx(dx)
    if found:
        return {"role": BABY, "reason": f"The diagnosis says \"{found}\" (care for a baby)"}
    age = _age_days(entry.get("dob"), entry.get("date_admitted") or entry.get("delivery_date"))
    if age is not None and age < _BABY_MAX_DAYS:
        return {"role": BABY, "reason": "The birthday is less than a year before the visit"}
    name = str(entry.get("name") or "")
    if _NEWBORN_NAME.match(name):
        return {"role": BABY, "reason": f"The logbook names the patient \"{name.strip()}\""}
    if entry.get("delivery_date") and age is not None and age >= _MOTHER_MIN_YEARS * 365:
        return {"role": MOTHER, "reason": "The logbook has a delivery date for this patient"}
    return {"role": None, "reason": "The logbook entry does not say - choose Mother or Baby"}


def _surname_matches(a, b):
    a, b = " ".join(_words(a)), " ".join(_words(b))
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def rank_mothers(baby, mothers):
    """The mothers' claims a baby's claim may belong to, best first.

    baby: {"claim_id", "last_name", "dob", "date_admitted", "upload_id",
    "session_id"}. mothers: the same plus "delivery_date", for every claim
    taken as a mother's. Returns [{"claim_id", "score", "reasons"}] for
    each with any match; one with none is left out (staff can still pick
    it from the full list)."""
    born = _iso(baby.get("dob"))
    seen = _iso(baby.get("date_admitted"))
    ranked = []
    for mother in mothers:
        if mother["claim_id"] == baby.get("claim_id"):
            continue
        score, reasons = 0, []
        delivered = _iso(mother.get("delivery_date"))
        if delivered and born and delivered == born:
            score += 3
            reasons.append("She gave birth on the baby's birthday")
        elif delivered and seen and 0 <= (seen - delivered).days <= 3:
            score += 1
            reasons.append("She gave birth just before the baby's visit")
        if _surname_matches(baby.get("last_name"), mother.get("last_name")):
            score += 2
            reasons.append("Same surname")
        if (baby.get("upload_id") and mother.get("upload_id") == baby.get("upload_id")
                and (mother.get("session_id") or 0) < (baby.get("session_id") or 0)):
            score += 1
            reasons.append("Above the baby in the same logbook scan")
        if score:
            ranked.append({"claim_id": mother["claim_id"], "score": score, "reasons": reasons})
    ranked.sort(key=lambda m: (-m["score"], -m["claim_id"]))
    return ranked


# What a baby's claim copies from its mother's, by group: (group, who it
# is about, [(baby's key, mother's key or None, label)]). Nothing about
# the mother's own body (LMP, gravida, para, her diagnosis) and nothing
# the baby's own logbook entry gives (its name, stay, diagnosis) - those
# only fill a box the baby's claim left empty, see values_for_baby().
_MEMBER_NAME_KEYS = (
    ("memberLastName", "Last name"), ("memberFirstName", "First name"),
    ("memberMiddleName", "Middle name"), ("memberNameExt", "Suffix"),
    ("memberDOB", "Date of birth"), ("memberSex", "Sex"), ("memberPIN", "PhilHealth PIN"),
    ("memberNoPhilhealth", "No PhilHealth"),
)
_PATIENT_FOR_MEMBER = {
    "memberLastName": "patientLastName", "memberFirstName": "patientFirstName",
    "memberMiddleName": "patientMiddleName", "memberNameExt": "patientNameExt",
    "memberDOB": "patientDOB", "memberSex": "patientSex", "memberPIN": "patientPIN",
    "memberNoPhilhealth": "patientNoPhilhealth",
}
_SAME_KEY_GROUPS = (
    ("Member profile (PMRF)", "member", (
        ("civilStatus", "Civil status"), ("citizenship", "Citizenship"),
        ("placeOfBirth", "Place of birth"),
        ("motherLastName", "Member's mother - last name"), ("motherFirstName", "Member's mother - first name"),
        ("motherMiddleName", "Member's mother - middle name"), ("motherNameExt", "Member's mother - suffix"),
        ("motherNoMiddleName", "Member's mother - no middle name"), ("motherMononym", "Member's mother - mononym"),
        ("spouseLastName", "Spouse - last name"), ("spouseFirstName", "Spouse - first name"),
        ("spouseMiddleName", "Spouse - middle name"), ("spouseNameExt", "Spouse - suffix"),
        ("spouseNoMiddleName", "Spouse - no middle name"), ("spouseMononym", "Spouse - mononym"),
        ("memberNoMiddleName", "Member - no middle name"), ("memberMononym", "Member - mononym"),
        ("memberType", "Member type"), ("profession", "Profession"), ("monthlyIncome", "Monthly income"),
        ("proofOfIncome", "Proof of income"), ("pwdIdNo", "PWD ID no."), ("praSrrvNo", "PRA SRRV no."),
        ("acrICardNo", "ACR I-Card no."), ("groupEnrollmentNo", "Group enrollment no."),
        ("preferredKonsulta", "Preferred KonSulTa provider"),
    )),
    ("Home address & contact", "home", (
        ("addrUnit", "Unit / room"), ("addrBuilding", "Building"), ("addrLot", "Lot / block / house no."),
        ("addrStreet", "Street"), ("addrSubdivision", "Subdivision"), ("addrBarangay", "Barangay"),
        ("addrCity", "City / municipality"), ("addrProvince", "Province"), ("addrZip", "ZIP code"),
        ("mailingSameAsAbove", "Mailing address same as home"),
        ("mailingAddrUnit", "Mailing - unit / room"), ("mailingAddrBuilding", "Mailing - building"),
        ("mailingAddrLot", "Mailing - lot / block"), ("mailingAddrStreet", "Mailing - street"),
        ("mailingAddrSubdivision", "Mailing - subdivision"), ("mailingAddrBarangay", "Mailing - barangay"),
        ("mailingAddrCity", "Mailing - city"), ("mailingAddrProvince", "Mailing - province"),
        ("mailingAddrZip", "Mailing - ZIP code"),
        ("mobile", "Mobile number"), ("homePhone", "Home phone"), ("businessPhone", "Business phone"),
        ("email", "Email"),
    )),
    ("Member's employer (CSF Part II)", "member", (
        ("employerName", "Employer name"), ("employerPEN", "Employer PEN"), ("employerPhone", "Employer phone"),
        ("employerRepName", "Employer representative"), ("employerCapacity", "Representative's position"),
    )),
    ("Member's signature (CSF Part I)", "member", (
        ("memberSignerType", "Signed by"), ("memberSignedDate", "Date signed (member)"),
        ("repSignedDate", "Date signed (representative)"), ("repRelationship", "Representative's relationship"),
        ("repRelationshipOther", "Representative's relationship - other"), ("repReason", "Reason"),
        ("repReasonOther", "Reason - other"), ("memberSignatureName", "Member's printed name (PMRF)"),
        ("memberSignatureDate", "Date signed (PMRF)"),
    )),
    ("Birth details", "baby", (
        ("deliveryDate", "Date of delivery"), ("deliveryTime", "Time of delivery"),
        ("amPmDelivery", "AM/PM of delivery"), ("mannerOfDelivery", "Manner of delivery"),
        ("fetalOutcome", "Fetal outcome"), ("babySex", "Baby's sex"), ("birthWeight", "Birth weight"),
        ("apgarScore", "APGAR score"),
    )),
    ("Clinic staff who attended", "staff", tuple(
        item for n in (1, 2, 3) for item in (
            (f"hciProf{n}Name", f"Health care professional {n} - name"),
            (f"hciProf{n}AccredNo", f"Health care professional {n} - accreditation no."),
        )
    )),
    ("Stay at the clinic", "baby", (
        ("accommodation", "Type of accommodation"),
    )),
)
WHO_LABELS = {
    "member": "the member",
    "home": "mother and baby (same home)",
    "baby": "the baby",
    "staff": "the clinic",
}


def _full_name(values, prefix):
    parts = [values.get(f"{prefix}FirstName"), values.get(f"{prefix}MiddleName"),
             values.get(f"{prefix}LastName"), values.get(f"{prefix}NameExt")]
    return " ".join(str(p).strip() for p in parts if p and str(p).strip())


def _filled(value):
    return value not in (None, "", False, [])


def values_for_baby(mother):
    """mother: the mother's claim as form values (form key -> value): what
    the logbook gave, overlaid with what staff typed on her forms.

    Returns {"member_is_mother": bool, "member_name": str,
    "groups": [{"title", "who", "who_label", "items": [{"key", "label",
    "value", "reason"}]}]} - only values the mother's claim has. The forms
    apply each to the baby's claim where the baby's box is still empty."""
    mother_name = _full_name(mother, "patient") or "the mother"
    has_member = any(_filled(mother.get(k)) for k in ("memberLastName", "memberFirstName"))
    member_is_mother = bool(mother.get("memberIsPatient")) or not has_member or (
        _full_name(mother, "member") == _full_name(mother, "patient"))

    groups = []
    member_items = []
    for key, label in _MEMBER_NAME_KEYS:
        source = _PATIENT_FOR_MEMBER[key] if member_is_mother else key
        value = mother.get(source)
        if not _filled(value) and member_is_mother:
            value = mother.get(key)
        if key == "memberSex" and member_is_mother and not _filled(value):
            value = "Female"
        if _filled(value):
            member_items.append({"key": key, "label": label, "value": value,
                                 "reason": f"From {mother_name}'s claim"})
    member_name = mother_name if member_is_mother else (_full_name(mother, "member") or "the member")
    member_items.append({"key": "relationship", "label": "Relationship to member", "value": "Child",
                         "reason": "The baby is the member's child"})
    groups.append({"title": "PhilHealth member", "who": "member",
                   "who_label": f"the member - {member_name}" + (" (the mother)" if member_is_mother else ""),
                   "items": member_items})

    for title, who, keys in _SAME_KEY_GROUPS:
        items = [{"key": key, "label": label, "value": mother[key], "reason": f"From {mother_name}'s claim"}
                 for key, label in keys if _filled(mother.get(key))]
        if items:
            groups.append({"title": title, "who": who, "who_label": WHO_LABELS[who], "items": items})

    # The baby itself, from what the mother's claim says about the birth.
    baby_items = []
    if _filled(mother.get("deliveryDate")):
        baby_items.append({"key": "patientDOB", "label": "Baby's date of birth", "value": mother["deliveryDate"],
                           "reason": "The mother's date of delivery"})
    if _filled(mother.get("babySex")):
        baby_items.append({"key": "patientSex", "label": "Baby's sex", "value": mother["babySex"],
                           "reason": "The baby's sex on the mother's claim"})
    if _filled(mother.get("citizenship")) and member_is_mother:
        baby_items.append({"key": "patientCitizenship", "label": "Baby's citizenship",
                           "value": mother["citizenship"], "reason": "The mother's citizenship"})
    # The baby can't sign: the mother signs the consent (CSF Part III,
    # CF2 Part III-B) for it, as its parent.
    if mother_name != "the mother":
        baby_items += [
            {"key": "patientSignerType", "label": "Consent signed by", "value": "Representative",
             "reason": "A baby can't sign; its mother signs for it"},
            {"key": "patientRepName", "label": "Representative's name", "value": mother_name,
             "reason": "The mother"},
            {"key": "patientRepRelationship", "label": "Representative's relationship", "value": "Parent",
             "reason": "The mother is the baby's parent"},
            {"key": "patientReason", "label": "Reason for signing for the patient", "value": "Other",
             "reason": "The patient is a baby"},
            {"key": "patientReasonOther", "label": "Other reason", "value": "PATIENT IS A MINOR",
             "reason": "The patient is a baby"},
        ]
    if baby_items:
        groups.insert(1, {"title": "The baby (patient)", "who": "baby", "who_label": WHO_LABELS["baby"],
                          "items": baby_items})

    # Not copied into the baby's boxes (they are the mother's own), but its
    # newborn diagnosis names them: "... TO A GRAVIDA 3 PARA 2 MOTHER
    # WEIGHING 3000 GRAMS" (js/dx-templates.js).
    facts = {key: mother[key] for key in _MOTHER_FACT_KEYS if _filled(mother.get(key))}
    return {"member_is_mother": member_is_mother, "member_name": member_name, "groups": groups,
            "mother_facts": facts}


_MOTHER_FACT_KEYS = ("gravida", "para", "obTerm", "obPreterm", "obAbortion", "obLiving",
                     "birthWeight", "apgarScore", "babySex", "lmp", "deliveryDate", "deliveryTime",
                     "amPmDelivery")
