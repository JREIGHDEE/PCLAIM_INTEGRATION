"""The input templates in research_tests/inputs/ (rebuilt by
python -m research_tests.make_templates; existing filled-in inputs are never
touched - only the *_template files are written).

  answer_key_template.xlsx    sheets Handwriting, Patients, Instructions
  writers_template.csv        the 10 writers + the 3 same-writer pairs
  session_data_template.xlsx  sheet Sessions, Instructions
  sus_template.xlsx           sheet SUS (optional)
"""
import csv

from research_tests import INPUTS
from research_tests.common.answer_key import FIELDS, HANDWRITING_COLUMNS, PATIENT_COLUMNS, WRITER_COLUMNS
from research_tests.common.excel import write_workbook
from research_tests.user_sessions import SESSION_COLUMNS


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
    write_workbook(INPUTS / "session_data_template.xlsx", [
        {"name": "Sessions", "headers": SESSION_COLUMNS,
         "rows": [["U01", "Claims encoder", 3, 2400, 5, 3, 900, 1, 26, 22, "example - replace"]]},
        {"name": "Instructions", "headers": ["Column", "What to put in it"], "rows": [
            ["Manual Claims / System Claims", "claims the participant prepared by hand / with PClaimAssist"],
            ["Manual Time (s) / System Time (s)", "total seconds for those claims in that condition"],
            ["Manual Errors / System Errors", "total errors found in those claims in that condition"],
            ["Suggestions Shown / Accepted", "OCR/correction suggestions shown during the system condition, and "
                                             "how many the participant accepted unchanged"],
        ]},
    ])
    write_workbook(INPUTS / "sus_template.xlsx", [
        {"name": "SUS", "headers": ["Participant ID"] + [f"Q{i}" for i in range(1, 11)],
         "rows": [["U01", 4, 2, 4, 1, 5, 2, 4, 2, 4, 2]],
         "notes": ["Optional. Answers 1-5; save as inputs/sus.xlsx to have SUS scored."]},
    ])
    print(f"Templates written to {INPUTS}")


if __name__ == "__main__":
    main()
