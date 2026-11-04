"""The Patients sheet (tests 3, 4, 5 and the user sessions' reference
claims) and the participants' task packet, from the handwriting answer key.

    python -m research_tests.build_patients

20 entries chosen to cover every case type in the answer key - delivery
(mother and newborn), postpartum, well baby (the baby is the patient, the
mother the member: "Child" on CF1), prenatal, family planning - and entries
with a value missing in the logbook (no time written, a blank "went home").
Clean entries were chosen over the answer key's deliberate inconsistencies.

The confirmed values are split by hand (SPLITS below, written for these 20
names), not by the system's own parser, so the field mapping test is not
checking the code against itself. Each row has a "Split checked" column for
the team to tick.

The logbook has no PhilHealth PIN or other claim-only fields: those are
generated, clearly fictional (PINs start with 99; a newborn's PIN is all
zeros, as the system sets it), and named in "Generated (not from logbook)".
For a baby, the member is the mother as written in her own logbook entry.

Writes, inside research_tests/inputs/:
  answer_key.xlsx   its Patients sheet (the Handwriting sheet is kept)
  task_packet.xlsx  per patient, every value a participant is given -
                    the logbook entry as written, then the claim-only values -
                    so a manual claim is never marked wrong for a value its
                    maker never had
"""
import re
from datetime import date

from research_tests import INPUTS
from research_tests.common.answer_key import ANSWER_KEY, PATIENT_COLUMNS, handwriting
from research_tests.common.excel import read_rows, write_workbook

# (writer, row): case type, (last, first, middle, suffix), mother's entry (for a baby), what is missing
CHOSEN = {
    ("W02", 7): ("Delivery (mother)", ("BANDOLIA", "MARJORIE", "SALISE", ""), None, ""),
    ("W03", 7): ("Delivery (mother)", ("LAGROSA", "CRISTINA MAE", "OMPOC", ""), None, ""),
    ("W07", 4): ("Delivery (mother)", ("MANGAO", "AILEEN", "GERODIAS", ""), None, ""),
    ("W10", 2): ("Delivery (mother)", ("PAÑARES", "MYLENE", "ABARQUEZ", ""), None, ""),
    ("W02", 8): ("Delivery (newborn)", ("BANDOLIA", "BABY GIRL", "SALISE", ""), ("W02", 7), ""),
    ("W03", 10): ("Delivery (newborn)", ("DAÑO", "BABY BOY", "ALCUIZAR", ""), ("W03", 9), ""),
    ("W07", 5): ("Delivery (newborn)", ("MANGAO", "BABY GIRL", "GERODIAS", ""), ("W07", 4), ""),
    ("W02", 5): ("Postpartum", ("CAMINADE", "MARY JOY", "SABANAL", ""), None, ""),
    ("W03", 11): ("Postpartum", ("PEPITO", "ANNABELLE", "CUTANDA", ""), None, ""),
    ("W07", 8): ("Postpartum", ("YAP", "REMY", "", ""), None, "Admitted: no time written"),
    ("W02", 3): ("Well baby", ("ABELLANA", "LIAM GABRIEL", "DAGOC", ""), ("W02", 2), ""),
    ("W02", 6): ("Well baby", ("CAMINADE", "ZIA MARIE", "SABANAL", ""), ("W02", 5), ""),
    ("W07", 9): ("Well baby", ("MONTES", "MATTEO", "YAP", ""), ("W07", 8), "Went home: blank in the logbook"),
    ("W02", 4): ("Prenatal", ("DAÑO", "SHIELA MAE", "ALCUIZAR", ""), None, ""),
    ("W03", 1): ("Prenatal", ("MANLANGIT", "KIMBERLY ANN", "TERO", ""), None, ""),
    ("W02", 11): ("Prenatal", ("LUNA", "PRINCESS JOY", "BASILAN", ""), None, ""),
    ("W02", 1): ("Family planning", ("TUBALLA", "GRACE ANN", "BAJAO", ""), None, ""),
    ("W02", 9): ("Family planning", ("GABUTAN", "ARLENE", "TUMULAK", ""), None, ""),
    ("W03", 3): ("Family planning", ("ROSALES", "MA. CECILIA", "", ""), None, ""),
    ("W07", 6): ("Family planning", ("DALIS", "TESS", "", ""), None, ""),
}
# How each mother's name splits (the member of a baby's claim).
MOTHER_SPLITS = {("W02", 7): ("BANDOLIA", "MARJORIE", "SALISE"), ("W03", 9): ("DAÑO", "SHIELA MAE", "ALCUIZAR"),
                 ("W07", 4): ("MANGAO", "AILEEN", "GERODIAS"), ("W02", 2): ("ABELLANA", "CHERYL LYN", "DAGOL"),
                 ("W02", 5): ("CAMINADE", "MARY JOY", "SABANAL"), ("W07", 8): ("YAP", "REMY", "")}
BARANGAYS = ("CABANTIAN", "TIGATTO", "INDANGAN")
GENERATED_COLUMNS = ["Member PIN", "Patient PIN", "Member is patient", "Member last name", "Member first name",
                     "Member middle name", "Member birthday", "Member sex", "Relationship", "Civil status",
                     "Member type", "Accommodation", "Disposition", "HCI accreditation no.", "HCI name",
                     "CF4 history of present illness", "CF4 physical exam", "CF4 drug given"]
EXTRA_COLUMNS = ["Case type", "Source (writer, row)", "Missing in the logbook", "Split checked"]


def CF4_BY_TYPE(case_type, reason):
    """(history of present illness, drug given) a clinic would write - fictional,
    used only where the system puts CF4 in the claim."""
    reason = reason.upper()
    if case_type == "Delivery (mother)":
        return "G1 - PRESENT PREGNANCY", "OXYTOCIN"
    if case_type == "Delivery (newborn)":
        return "LIVE TERM NEWBORN, NO COMPLAINTS", "VITAMIN K (PHYTOMENADIONE)"
    if case_type == "Well baby":
        return "WELL BABY CHECK, NO COMPLAINTS", "NONE"
    if case_type == "Postpartum":
        return "POSTPARTUM, NO COMPLAINTS", "FERROUS SULFATE"
    if case_type == "Prenatal":
        return "PRENATAL CHECK-UP, NO COMPLAINTS", "FOLIC ACID"
    if "DMPA" in reason:
        return "FOR FAMILY PLANNING, NO COMPLAINTS", "MEDROXYPROGESTERONE ACETATE (DMPA)"
    if "PILL" in reason:
        return "FOR FAMILY PLANNING, NO COMPLAINTS", "COMBINED ORAL CONTRACEPTIVE PILLS"
    return "FOR FAMILY PLANNING COUNSELING, NO COMPLAINTS", "NONE"


def _date(text, birth=False):
    """'2026-08-29' from 08-29-26 / 8-29-26 / 08/29/26 / 8-15-2001 (+ any time)."""
    m = re.match(r"\s*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", text or "")
    if not m:
        return ""
    mm, dd, yy = int(m[1]), int(m[2]), int(m[3])
    if yy < 100:
        yy += 2000 if yy <= date.today().year % 100 else 1900
    return date(yy, mm, dd).isoformat()


def _time(text):
    """('6:48', 'PM') from '... 06:48 PM'; ('', '') when no time is written."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*([AP])\.?\s*M", text or "", re.I)
    return (f"{int(m[1])}:{m[2]}", m[3].upper() + "M") if m else ("", "")


def _mmddyyyy(iso):
    return f"{iso[5:7]}-{iso[8:10]}-{iso[:4]}" if iso else ""


def _address_parts(address):
    words = address.upper()
    barangay = next((b for b in BARANGAYS if b in words), "")
    street = re.match(r"\s*(PUROK\s+\d+)", words)
    davao = "DAVAO" in words
    return (street.group(1) if street else "", barangay, "DAVAO CITY" if davao else "",
            "DAVAO DEL SUR" if davao else "")


def _pin(n):
    return f"99-{(123456700 + n * 7919) % 10**9:09d}-{n % 10}"


def entries(key):
    out = {}
    for k in key:
        out.setdefault((k["writer"], k["row"]), {})[k["field"]] = k["truth"]
    return out


def resolve_ditto(all_entries, writer, row):
    """A '-DO-' address is the address of the entry above it (as case_bridge does)."""
    while row >= 1:
        address = all_entries.get((writer, row), {}).get("Address", "")
        if address and not re.fullmatch(r"\s*-?\s*DO\s*-?\s*", address, re.I):
            return address
        row -= 1
    return ""


def build():
    key = handwriting(ANSWER_KEY)
    all_entries = entries(key)
    rows, packet = [], []
    for n, ((writer, row), (case_type, (last, first, middle, suffix), mother, missing)) in enumerate(CHOSEN.items(), start=1):
        e = all_entries[(writer, row)]
        address = resolve_ditto(all_entries, writer, row)
        street, barangay, city, province = _address_parts(address)
        p = {"Patient ID": f"R{n:02d}", "Case number": e.get("Case number", ""), "Last name": last,
             "First name": first, "Middle name": middle, "Suffix": suffix,
             "Birthday": _mmddyyyy(_date(e.get("Birthday"), birth=True)), "Address": address,
             "Reason for admission": e.get("Reason for admission", ""), "Final diagnosis": e.get("Final diagnosis", ""),
             "Street": street, "Barangay": barangay, "City": city, "Province": province}
        for prefix, field in (("Admitted", "Admitted"), ("Delivered", "Delivered"), ("Went home", "Went home")):
            text = e.get(field, "")
            t, ampm = _time(text)
            p[f"{prefix} date"], p[f"{prefix} time"], p[f"{prefix} AM/PM"] = _mmddyyyy(_date(text)), t, ampm
        baby = mother is not None
        pin = _pin(n)
        if baby:
            m_last, m_first, m_middle = MOTHER_SPLITS[mother]
            m_birthday = _mmddyyyy(_date(all_entries[mother].get("Birthday"), birth=True))
            p.update({"Member PIN": pin, "Patient PIN": "00-000000000-0", "Member is patient": "No",
                      "Member last name": m_last, "Member first name": m_first, "Member middle name": m_middle,
                      "Member birthday": m_birthday, "Member sex": "Female", "Relationship": "Child"})
            generated = ["Member PIN", "Patient PIN"]
        else:
            p.update({"Member PIN": pin, "Patient PIN": pin, "Member is patient": "Yes", "Member last name": last,
                      "Member first name": first, "Member middle name": middle, "Member birthday": p["Birthday"],
                      "Member sex": "Female", "Relationship": "Self"})
            generated = ["Member PIN"]
        history, drug = CF4_BY_TYPE(case_type, e.get("Reason for admission", ""))
        p.update({"Civil status": "Married", "Member type": "Indirect Contributor", "Accommodation": "Non-Private",
                  "Disposition": "Improved", "HCI accreditation no.": "H99999999", "HCI name": "SAMPLE LYING-IN CLINIC",
                  "CF4 history of present illness": history, "CF4 physical exam": "ESSENTIALLY NORMAL",
                  "CF4 drug given": drug})
        generated += ["Civil status", "Member type", "Accommodation", "Disposition", "HCI accreditation no.",
                      "HCI name", "CF4 history of present illness", "CF4 physical exam", "CF4 drug given"]
        p.update({"Case type": case_type, "Source (writer, row)": f"{writer} row {row}",
                  "Missing in the logbook": missing, "Split checked": "",
                  "Generated (not from logbook)": ", ".join(generated)})
        rows.append(p)
        for field in ("Case number", "Admitted", "Patient name", "Birthday", "Address", "Reason for admission",
                      "Delivered", "Final diagnosis", "Went home"):
            packet.append([p["Patient ID"], case_type, f"Logbook: {field}", e.get(field, ""), "logbook (as written)"])
        if address != e.get("Address", ""):
            packet.append([p["Patient ID"], case_type, "Logbook: Address (the ditto mark means)", address, "logbook"])
        for col in GENERATED_COLUMNS:
            if p.get(col):
                packet.append([p["Patient ID"], case_type, col, p[col],
                               "generated (fictional)" if col in generated else "from the logbook / clinic"])
    return rows, packet


def main():
    rows, packet = build()
    headers = PATIENT_COLUMNS + GENERATED_COLUMNS + ["Generated (not from logbook)"] + EXTRA_COLUMNS
    hw = read_rows(ANSWER_KEY, "Handwriting", header_row=0)
    hw_headers = list(hw[0]) if hw else []
    write_workbook(ANSWER_KEY, [
        {"name": "Handwriting", "headers": hw_headers, "rows": [[r.get(h) for h in hw_headers] for r in hw]},
        {"name": "Patients", "headers": headers, "rows": [[p.get(h, "") for h in headers] for p in rows],
         "notes": ["Built by research_tests/build_patients.py from the Handwriting sheet: 20 entries covering every "
                   "case type; names split by hand; '-DO-' addresses resolved to the entry above.",
                   "Generated (not from logbook) = fictional claim-only values (PINs start with 99; a newborn's PIN "
                   "is all zeros). The same values are in task_packet.xlsx for the participants.",
                   "Split checked: tick when the team has checked the name, date and time split."]},
    ])
    write_workbook(INPUTS / "task_packet.xlsx", [
        {"name": "Task packet", "title": "Task packet - the values each participant is given (all fictional)",
         "headers": ["Patient ID", "Case type", "Item", "Value", "Source"], "rows": packet,
         "notes": ["Give each participant the rows of the patients in their claims. Manual and system claims are "
                   "scored against these values only."]}])
    print(f"Patients sheet: {len(rows)} patients -> {ANSWER_KEY}")
    print(f"Task packet -> {INPUTS / 'task_packet.xlsx'}")
    for p in rows:
        print(f"  {p['Patient ID']} {p['Case type']:<19} {p['First name']} {p['Middle name']} {p['Last name']} | "
              f"adm {p['Admitted date']} {p['Admitted time']} {p['Admitted AM/PM']} | home {p['Went home date']} "
              f"{p['Went home time']} {p['Went home AM/PM']} | {p['Street']}/{p['Barangay']} {p['Missing in the logbook']}")


if __name__ == "__main__":
    main()
