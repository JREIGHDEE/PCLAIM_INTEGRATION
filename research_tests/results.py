"""The combined workbook: outputs/chapter5_results.xlsx, one summary sheet
per test (from each test's latest run), ready to copy into Chapter 5.

    python -m research_tests.results
"""
import json

from research_tests import OUTPUTS
from research_tests.common import excel
from research_tests.registry import TESTS

TEST_KEY = "results"
WORKBOOK = OUTPUTS / "chapter5_results.xlsx"


def run(progress, **_):
    contents, sheets = [], []
    for n, test in enumerate(TESTS, start=1):
        progress(n / (len(TESTS) + 1), f"Collecting {test['tab']}")
        path = OUTPUTS / test["key"] / "summary.json"
        if not path.is_file():
            contents.append([n, test["tab"], "not run yet", "", "", ""])
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        names = []
        for sheet in record["sheets"]:
            sheets.append(sheet)
            names.append(sheet["name"])
        contents.append([n, test["tab"], record["generated_at"],
                         "SAMPLE DATA - not for Chapter 5" if record.get("samples") else "inputs/",
                         ", ".join(names), f"outputs/{test['key']}/{test['workbook']}"])
    first = {"name": "Contents", "title": "Chapter 5 results - PClaimAssist research tests",
             "headers": ["#", "Test", "Last run", "Data", "Sheets here", "Full results (raw data)"],
             "rows": contents,
             "notes": ["Each sheet is the summary of that test's latest run; the raw data is in the test's own "
                       "workbook. Re-run a test (its tab, or python -m research_tests.<test>) and then this "
                       "(python -m research_tests.results) to refresh.",
                       "Rows marked SAMPLE DATA come from the computer-drawn samples (make_samples.py): re-run "
                       "those tests on the real inputs before using the numbers."]}
    excel.write_workbook(WORKBOOK, [first] + sheets)
    progress(1.0, "Done")
    done = sum(1 for c in contents if c[2] != "not run yet")
    return {"outputs": [WORKBOOK], "headline": [["Tests included", f"{done} of {len(TESTS)}"]]}


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0])
