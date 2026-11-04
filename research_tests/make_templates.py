"""The input templates in research_tests/inputs/ (rebuilt by
python -m research_tests.make_templates; existing filled-in inputs are never
touched - only the *_template files are written).

  answer_key_template.xlsx    sheets Handwriting, Patients, Instructions
  writers_template.csv        the 10 writers + the 3 same-writer pairs
  session_data_template.xlsx  sheets 7a, 7c, 7d, SUS, Instructions (copy to inputs/sessions/)
  sus_template.xlsx           sheet SUS (optional)
"""
import csv

from research_tests import INPUTS
from research_tests.common.answer_key import FIELDS, HANDWRITING_COLUMNS, PATIENT_COLUMNS, WRITER_COLUMNS
from research_tests.common.excel import write_workbook


def session_sheets(example=True):
    """The session workbook's sheets (template, or fictional samples)."""
    from research_tests.user_sessions import ERROR_COLUMNS, LOG_COLUMNS, SUGGESTION_COLUMNS, SUS_COLUMNS
    log = [["P1", "manual first", "manual", 1, "R04", "09:02:10", "09:13:55", 705, "example - replace"],
           ["P1", "manual first", "system", 1, "R09", "09:40:00", "09:44:30", 270, "example - replace"]]
    errors = [["P1", "manual", 1, "R04", "CF2", "dateAdmittedD1-8", "Admitted date", "Admitted", "09-11-2026",
               "09-14-2026", "wrong value", ""]]
    suggestions = [["P1", 1, "R09", "Address", "PUROK 7 CABANTAN", "PUROK 7 CABANTIAN DAVAO CITY", "accept",
                    "PUROK 7 CABANTIAN DAVAO CITY", "00:14:32"]]
    sus = [["P1", 4, 2, 4, 1, 5, 2, 4, 2, 4, 2]]
    return [
        {"name": "7a Session log", "headers": LOG_COLUMNS, "rows": log if example else []},
        {"name": "7c Claim errors", "headers": ERROR_COLUMNS, "rows": errors if example else []},
        {"name": "7d Suggestion log", "headers": SUGGESTION_COLUMNS, "rows": suggestions if example else []},
        {"name": "SUS", "headers": SUS_COLUMNS, "rows": sus if example else []},
        {"name": "Instructions", "headers": ["Sheet / column", "What to put in it"], "rows": [
            ["Participant", "P1 ... P5 only - never a name (the tests refuse anything else)"],
            ["7a: one row per claim", "Condition = manual or system; Patient ID = the task packet's R01 ... R20; "
                                       "Seconds, or Start and End (hh:mm:ss) from the recording"],
            ["7c: one row per box", "Run python -m research_tests.user_sessions --prefill-errors after 7a: it "
                                     "writes the reference rows; type each Claim value from the printed claim. "
                                     "Error type = wrong value / wrong box / required blank; leave 'Error after "
                                     "normalization' empty and the test works it out"],
            ["7c: Value group", "the same value repeated across forms (e.g. Last name): counted once in the "
                                "per-value error count"],
            ["7d: one row per suggestion shown", "Choice = accept / edit / reject / not acted on"],
            ["SUS", "optional: answers 1-5 to the ten SUS items"],
            ["Do not store here", "recordings, consent forms, names, or anything that identifies a participant"],
        ]},
    ]


def main():
    INPUTS.mkdir(parents=True, exist_ok=True)
    example_key = [["W01", "caps", 1, 1, "Case number", "2026-0410"],
                   ["W01", "caps", 1, 1, "Patient name", "DELA CRUZ, MARIA SANTOS"],
                   ["W01", "caps", 2, 1, "Reason for admission", "LABOR PAINS"],
                   ["W06", "lower", 1, 1, "Patient name", "santos, ana cruz"]]
    example_patients = [["P01", "2026-0410", "DELA CRUZ", "MARIA", "SANTOS", "", "06-12-2003",
                         "PUROK 5, CABANTIAN, DAVAO CITY", "10-01-2026", "10:15", "AM", "10-01-2026", "3:40", "PM",
                         "10-02-2026", "9:30", "AM", "LABOR PAINS", "PREGNANCY UTERINE DELIVERED",
                         "PUROK 5", "CABANTIAN", "DAVAO CITY", "DAVAO DEL SUR"]]
    write_workbook(INPUTS / "answer_key_template.xlsx", [
        {"name": "Handwriting", "headers": HANDWRITING_COLUMNS, "rows": example_key,
         "notes": ["Example rows - replace them. One line per logbook cell a writer filled in."]},
        {"name": "Patients", "headers": PATIENT_COLUMNS, "rows": example_patients,
         "notes": ["Example row - replace it. About 20 fictional patients, values as confirmed by staff."]},
        {"name": "Instructions", "headers": ["Column", "What to put in it"], "rows": [
            ["Handwriting: Writer ID", "W01 ... W10 for the 10 writers; R1 ... R3 for the same-writer pages"],
            ["Handwriting: Style", "caps or lower - the style that page is written in"],
            ["Handwriting: Page", "the PDF page of the scan the cell is on (1 = left page, 2 = right page, ...)"],
            ["Handwriting: Row", "the entry line on that page, as the OCR comparison page numbers it (1 = first "
                                 "entry under the printed header)"],
            ["Handwriting: Field", "one of: " + ", ".join(FIELDS)],
            ["Handwriting: Ground Truth", "exactly what is written (capitals and spaces do not matter: scoring "
                                          "compares in capitals with spaces collapsed); leave empty for a blank cell"],
            ["Patients: dates", "MM-DD-YYYY (or an Excel date)"],
            ["Patients: times", "h:mm with the AM/PM column (or a 24-hour time)"],
            ["Patients: Street ... Province", "optional - the address as confirmed on Patient details; the address "
                                              "boxes are checked only when given"],
            ["All data", "fictional - no real patient data"],
        ]},
    ])
    with open(INPUTS / "writers_template.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(WRITER_COLUMNS)
        for i in range(1, 11):
            style = "caps" if i <= 5 else "lower"
            w.writerow([f"W{i:02d}", style, "main", f"W{i:02d}_{style}.pdf", ""])
        for i in range(1, 4):
            for style in ("caps", "lower"):
                w.writerow([f"R{i}", style, "same_writer", f"R{i}_{style}.pdf", "researcher, both styles"])
    write_workbook(INPUTS / "session_data_template.xlsx", session_sheets())
    write_workbook(INPUTS / "sus_template.xlsx", [
        {"name": "SUS", "headers": ["Participant"] + [f"Q{i}" for i in range(1, 11)],
         "rows": [["P1", 4, 2, 4, 1, 5, 2, 4, 2, 4, 2]],
         "notes": ["Optional. Answers 1-5; save as inputs/sus.xlsx to have SUS scored."]},
    ])
    print(f"Templates written to {INPUTS}")


if __name__ == "__main__":
    main()
