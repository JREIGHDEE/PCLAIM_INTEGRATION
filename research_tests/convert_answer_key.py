"""Turn a combined-scan answer key into the Handwriting test's inputs.

    python -m research_tests.convert_answer_key inputs/answer_key_fake_scan_updated_10.xlsx [--scans DIR]

The source workbook (made for the OCR comparison of one combined PDF):
  sheet "Answer Key": Source File | Spread ID | PDF Page | Side | Logbook Page |
                      Row | Field | Ground Truth | ... (Writer ID / Style are
                      formulas looking up the Writers sheet)
  sheet "Writers":    Spread ID | PDF pages | Logbook pages | Patients |
                      Writer ID | Style (caps / lower) | Notes
Each spread SP-nn was scanned on its own as <Writer>_<style>.pdf (2 pages):
the left side is page 1 of that file, the right side page 2.

Writes (inside research_tests/inputs/):
  answer_key.xlsx  sheet Handwriting (Writer ID | Style | Page | Row | Field |
                   Ground Truth), plus the original Spread ID, PDF Page, Side and
                   Note columns for tracing; an existing Patients sheet is kept
  writers.csv      W01 ... W10 with their scan file
  scans/handwriting/<Writer>_<style>.pdf  copied from --scans (default
                   inputs/scans/), where a file may carry a download suffix such
                   as "W01_caps (2).pdf"; the originals are left in place
"""
import argparse
import csv
import re
import shutil
from pathlib import Path

from openpyxl import load_workbook

from research_tests import INPUTS
from research_tests.common.answer_key import FIELDS, HANDWRITING_COLUMNS, WRITER_COLUMNS
from research_tests.common.excel import read_rows, write_workbook


def _text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def convert(source, scans_dir):
    wb = load_workbook(source, read_only=True, data_only=True)
    writers = {}
    for row in wb["Writers"].iter_rows(min_row=2, values_only=True):
        spread = _text(row[0])
        if re.fullmatch(r"SP-\d+", spread):
            writers[spread] = {"writer": _text(row[4]).upper(), "style": _text(row[5]).lower(),
                               "pages": _text(row[1]), "patients": int(row[3] or 0), "notes": _text(row[6])}
    rows = list(wb["Answer Key"].iter_rows(values_only=True))
    wb.close()
    head = [_text(h) for h in rows[0]]
    col = {h: i for i, h in enumerate(head)}
    problems, out, odd = [], [], []
    for n, r in enumerate(rows[1:], start=2):
        spread = _text(r[col["Spread ID"]])
        if not spread:
            continue
        w = writers.get(spread)
        if w is None:
            problems.append(f"row {n}: {spread} is not in the Writers sheet")
            continue
        side = _text(r[col["Side"]]).lower()
        field = _text(r[col["Field"]])
        if field not in FIELDS:
            problems.append(f"row {n}: unknown field {field!r}")
            continue
        truth = r[col["Ground Truth"]]
        if truth is not None and not isinstance(truth, str):
            odd.append(f"row {n}: ground truth {truth!r} is a {type(truth).__name__}, not text")
        first, _ = (int(p) for p in w["pages"].split("-"))
        pdf_page = int(r[col["PDF Page"]])
        page = {"left": 1, "right": 2}.get(side)
        if page is None or pdf_page != first + page - 1:
            problems.append(f"row {n}: {spread} side {side!r} on PDF page {pdf_page} does not match pages {w['pages']}")
        out.append([w["writer"], w["style"], page, int(r[col["Row"]]), field, _text(truth),
                    spread, pdf_page, side, _text(r[col["Note"]]) if "Note" in col else ""])
    if problems:
        raise ValueError("The answer key does not line up:\n  " + "\n  ".join(problems[:20]))

    # The Handwriting sheet (with tracing columns), keeping any Patients sheet.
    target = INPUTS / "answer_key.xlsx"
    sheets = [{"name": "Handwriting", "headers": HANDWRITING_COLUMNS + ["Spread ID", "Original PDF Page", "Side", "Note"],
               "rows": out, "notes": [f"Converted from {Path(source).name} by research_tests/convert_answer_key.py."]}]
    if target.is_file():
        try:
            patients = read_rows(target, "Patients", header_row=0)
            if patients:
                headers = list(patients[0])
                sheets.append({"name": "Patients", "headers": headers,
                               "rows": [[p.get(h) for h in headers] for p in patients]})
        except KeyError:
            pass
    write_workbook(target, sheets)

    copied, missing = [], []
    (INPUTS / "scans" / "handwriting").mkdir(parents=True, exist_ok=True)
    with open(INPUTS / "writers.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(WRITER_COLUMNS)
        for spread, w in sorted(writers.items()):
            scan = f"{w['writer']}_{w['style']}.pdf"
            wr.writerow([w["writer"], w["style"], "main", scan, f"{spread}; {w['patients']} patients; {w['notes']}"])
            found = [p for p in sorted(Path(scans_dir).glob(f"{w['writer']}_{w['style']}*.pdf"))]
            dest = INPUTS / "scans" / "handwriting" / scan
            if found:
                shutil.copy2(found[0], dest)
                copied.append(f"{found[0].name} -> scans/handwriting/{scan}")
            elif not dest.is_file():
                missing.append(scan)
    return {"cells": len(out), "blank": sum(1 for r in out if not r[5]), "writers": len(writers),
            "copied": copied, "missing": missing, "odd": odd,
            "rows_per_writer": {w["writer"]: len({r[3] for r in out if r[0] == w["writer"]}) for w in writers.values()}}


def main():
    parser = argparse.ArgumentParser(prog="python -m research_tests.convert_answer_key", description=__doc__.splitlines()[0])
    parser.add_argument("source", help="the combined-scan answer key workbook")
    parser.add_argument("--scans", default=str(INPUTS / "scans"), help="folder with the writers' PDFs")
    args = parser.parse_args()
    result = convert(args.source, args.scans)
    print(f"{result['cells']} cells ({result['blank']} blank) for {result['writers']} writers")
    print("entries per writer:", result["rows_per_writer"])
    for line in result["copied"]:
        print("copied", line)
    for line in result["missing"]:
        print("MISSING scan", line)
    for line in result["odd"][:10]:
        print("note:", line)


if __name__ == "__main__":
    main()
