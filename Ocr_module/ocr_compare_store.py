"""
The workbook of the OCR comparison page (ocr_compare.py): every checked row,
one line per field, and a summary of which engine reads each field best.

Like ocr_testing_store.py (the older one-row-at-a-time test, whose workbook
is left as it is), but:
  - four readings per field (PaddleOCR and TesseractOCR, each raw and with
    the Logbook Reader's corrections), each scored against the ground truth;
  - saving a row again replaces its earlier lines (same run and row), so a
    corrected ground truth never counts twice;
  - a "Summary" sheet, rewritten on every save: per field and overall, the
    share read exactly right, the mean character accuracy and the field
    mapping accuracy of each reading, and the better engine;
  - cell cut reliability: how the tester judged each cell's picture (cut
    correctly / cut off / wrong place) next to the pipeline's own warning,
    and in the summary the share cut correctly, plus each engine's accuracy
    on the correctly cut cells only - a misread apart from a bad cut.

Each line says its spread ("SP-01", pages "1-2": the left and right page
that hold one entry together), and a "Spreads" sheet gives the results per
spread.

Sheets: "Rows", "Summary", "Spreads". File: config.OCR_COMPARE_WORKBOOK.
"""
import logging
import threading
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import config
from ocr_compare import CUTS, VARIANTS

logger = logging.getLogger(__name__)

ROWS_SHEET, SUMMARY_SHEET, SPREADS_SHEET = "Rows", "Summary", "Spreads"

HEADERS = [
    "Test ID", "Run ID", "Source File", "Spread ID", "Spread Pages", "Row", "PDF Page", "Side", "Field",
    "Maps To",
    "Cell Cut", "Pipeline: Writing Outside Cut",
    "Ground Truth",
    "PaddleOCR Output", "Paddle Confidence", "PaddleOCR + Correction",
    "TesseractOCR Output", "Tesseract Confidence", "TesseractOCR + Correction",
    "PaddleOCR Accuracy %", "PaddleOCR + Correction Accuracy %",
    "TesseractOCR Accuracy %", "TesseractOCR + Correction Accuracy %",
    "PaddleOCR + Correction Exact", "TesseractOCR + Correction Exact",
    "PaddleOCR + Correction Mapped", "TesseractOCR + Correction Mapped",
    "Best Engine", "Saved At",
]
_KEY_COLS = [HEADERS.index(h) for h in ("Run ID", "Spread ID", "Row")]
_ACCURACY_HEADERS = {
    "paddle_raw": "PaddleOCR Accuracy %", "paddle_corrected": "PaddleOCR + Correction Accuracy %",
    "tesseract_raw": "TesseractOCR Accuracy %", "tesseract_corrected": "TesseractOCR + Correction Accuracy %",
}

_lock = threading.Lock()
_HEADER_FILL = PatternFill("solid", fgColor="1E3A8A")
_HEADER_FONT = Font(bold=True, color="FFFFFF")


def _yes_no(score):
    return "" if score is None else ("Yes" if score["exact"] else "No")


def _mapped(score):
    if score is None or not score["mapped_total"]:
        return ""
    return f"{score['mapped_right']}/{score['mapped_total']}"


def _line(item, saved_at):
    f, s = item["field"], item["scores"]
    acc = lambda v: "" if s.get(v) is None else s[v]["accuracy"]
    return [
        None, item["run_id"], item["source_file"], item["spread_id"], item["spread_pages"], item["row"] + 1,
        f["page"], f["side"],
        f["label"], f["maps_to"], CUTS.get(item.get("cut"), ""), "Yes" if f.get("cut_flag") else "No",
        item["truth"],
        f["paddle_raw"], f["paddle_confidence"], f["paddle_corrected"],
        f["tesseract_raw"], f["tesseract_confidence"], f["tesseract_corrected"],
        acc("paddle_raw"), acc("paddle_corrected"), acc("tesseract_raw"), acc("tesseract_corrected"),
        _yes_no(s.get("paddle_corrected")), _yes_no(s.get("tesseract_corrected")),
        _mapped(s.get("paddle_corrected")), _mapped(s.get("tesseract_corrected")),
        item["best"], saved_at,
    ]


def _read_lines(path):
    """The Rows sheet's lines, in HEADERS order - by column name, so a file
    written before a column was added still reads (the new column empty)."""
    if not path.exists():
        return []
    workbook = load_workbook(path)
    if ROWS_SHEET not in workbook.sheetnames:
        return []
    rows = list(workbook[ROWS_SHEET].iter_rows(values_only=True))
    if not rows:
        return []
    where = {name: i for i, name in enumerate(rows[0]) if name}
    return [[r[where[h]] if h in where and where[h] < len(r) else None for h in HEADERS]
            for r in rows[1:] if any(v not in (None, "") for v in r)]


def _style_header(sheet):
    for cell in sheet[1]:
        cell.fill, cell.font = _HEADER_FILL, _HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    sheet.freeze_panes = "A2"


def summarize(lines, by_spread=False):
    """[{"field", "n", per variant: exact %, accuracy %, mapped %}, ..., overall]
    from the Rows sheet's lines - per field, or with by_spread per spread
    ("SP-01 · scan.pdf", with its pages) and no overall line."""
    index = {h: i for i, h in enumerate(HEADERS)}
    acc_cols = {v: index[_ACCURACY_HEADERS[v]] for v in VARIANTS}
    groups, pages = {}, {}
    for line in lines:
        if by_spread:
            name = f"{line[index['Spread ID']] or ''} · {line[index['Source File']] or ''}"
            pages[name] = line[index["Spread Pages"]] or ""
        else:
            name = line[index["Field"]] or ""
        groups.setdefault(name, []).append(line)
    if not by_spread:
        groups["All fields"] = list(lines)

    def mean(values):
        values = [float(v) for v in values if v not in (None, "")]
        return round(sum(values) / len(values), 2) if values else None

    def share(values):
        values = [v for v in values if v in ("Yes", "No")]
        return round(100 * values.count("Yes") / len(values), 2) if values else None

    def mapped(values):
        right = total = 0
        for v in values:
            if v and "/" in str(v):
                a, b = str(v).split("/")
                right, total = right + int(a), total + int(b)
        return round(100 * right / total, 2) if total else None

    out = []
    for name, group in groups.items():
        if not group or (name == "All fields" and len(groups) == 1):
            continue
        row = {"field": name, "n": len(group), "pages": pages.get(name, ""),
               "rows": len({tuple(l[i] for i in _KEY_COLS) for l in group})}
        for v in VARIANTS:
            row[f"{v}_accuracy"] = mean(l[acc_cols[v]] for l in group)
        for v, col in (("paddle_corrected", "PaddleOCR + Correction Exact"),
                       ("tesseract_corrected", "TesseractOCR + Correction Exact")):
            row[f"{v}_exact"] = share(l[index[col]] for l in group)
        for v, col in (("paddle_corrected", "PaddleOCR + Correction Mapped"),
                       ("tesseract_corrected", "TesseractOCR + Correction Mapped")):
            row[f"{v}_mapped"] = mapped(l[index[col]] for l in group)
        cuts = [l[index["Cell Cut"]] for l in group if l[index["Cell Cut"]]]
        row["cut_correct"] = round(100 * cuts.count(CUTS["correct"]) / len(cuts), 2) if cuts else None
        row["cut_off"], row["cut_wrong"] = cuts.count(CUTS["cut_off"]), cuts.count(CUTS["wrong"])
        flagged = [l for l in group if l[index["Pipeline: Writing Outside Cut"]] == "Yes"]
        row["pipeline_flagged"] = len(flagged)
        row["flag_agreed"] = sum(1 for l in flagged if l[index["Cell Cut"]] == CUTS["cut_off"])
        well_cut = [l for l in group if l[index["Cell Cut"]] == CUTS["correct"]]
        for v in ("paddle_corrected", "tesseract_corrected"):
            row[f"{v}_accuracy_cut_ok"] = mean(l[acc_cols[v]] for l in well_cut)
        best = [l[index["Best Engine"]] for l in group]
        row.update({"paddle_wins": best.count("PaddleOCR"), "tesseract_wins": best.count("TesseractOCR"),
                    "ties": best.count("Tie")})
        p, t = row["paddle_corrected_accuracy"], row["tesseract_corrected_accuracy"]
        row["recommended"] = ("" if p is None and t is None else "PaddleOCR" if t is None or (p or 0) > t
                              else "TesseractOCR" if p is None or t > p else "Either")
        out.append(row)
    return out


_SUMMARY_HEADERS = [
    ("field", "Field"), ("n", "Cells"),
    ("paddle_raw_accuracy", "PaddleOCR Accuracy %"),
    ("paddle_corrected_accuracy", "PaddleOCR + Correction Accuracy %"),
    ("tesseract_raw_accuracy", "TesseractOCR Accuracy %"),
    ("tesseract_corrected_accuracy", "TesseractOCR + Correction Accuracy %"),
    ("paddle_corrected_exact", "PaddleOCR + Correction Exact %"),
    ("tesseract_corrected_exact", "TesseractOCR + Correction Exact %"),
    ("paddle_corrected_mapped", "PaddleOCR + Correction Field Mapping %"),
    ("tesseract_corrected_mapped", "TesseractOCR + Correction Field Mapping %"),
    ("paddle_wins", "PaddleOCR Better"), ("tesseract_wins", "TesseractOCR Better"), ("ties", "Tie"),
    ("recommended", "Recommended Engine"),
    ("cut_correct", "Cells Cut Correctly %"), ("cut_off", "Cut Off"), ("cut_wrong", "Wrong Place"),
    ("pipeline_flagged", "Pipeline Flagged"), ("flag_agreed", "Flagged and Cut Off"),
    ("paddle_corrected_accuracy_cut_ok", "PaddleOCR + Correction Accuracy % (cut correctly)"),
    ("tesseract_corrected_accuracy_cut_ok", "TesseractOCR + Correction Accuracy % (cut correctly)"),
]


_SPREAD_HEADERS = [
    ("field", "Spread · Source File"), ("pages", "Pages"), ("rows", "Rows"), ("n", "Cells"),
    ("paddle_raw_accuracy", "PaddleOCR Accuracy %"),
    ("paddle_corrected_accuracy", "PaddleOCR + Correction Accuracy %"),
    ("tesseract_raw_accuracy", "TesseractOCR Accuracy %"),
    ("tesseract_corrected_accuracy", "TesseractOCR + Correction Accuracy %"),
    ("paddle_corrected_mapped", "PaddleOCR + Correction Field Mapping %"),
    ("tesseract_corrected_mapped", "TesseractOCR + Correction Field Mapping %"),
    ("cut_correct", "Cells Cut Correctly %"), ("cut_off", "Cut Off"), ("cut_wrong", "Wrong Place"),
    ("recommended", "Recommended Engine"),
]


def _write(lines):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = ROWS_SHEET
    sheet.append(HEADERS)
    for number, line in enumerate(lines, start=1):
        line[0] = number
        sheet.append(line)
    _style_header(sheet)
    for i, header in enumerate(HEADERS, start=1):
        sheet.column_dimensions[get_column_letter(i)].width = max(10, min(32, len(header) + 2))

    summary = workbook.create_sheet(SUMMARY_SHEET)
    summary.append([label for _, label in _SUMMARY_HEADERS])
    for row in summarize(lines):
        summary.append([row.get(key) for key, _ in _SUMMARY_HEADERS])
    _style_header(summary)
    summary.append([])
    summary.append(["Accuracy % = 100 x (1 - character error rate), compared in capitals with spaces "
                    "collapsed; a blank ground truth scores 100 only when the reading is blank too."])
    summary.append(["Field mapping % = form fields (last/first/middle name, date, hour, AM/PM, ...) "
                    "filled right from the reading, out of those the ground truth fills."])
    summary.append(["Both engines read the same cell pictures; correction = the Logbook Reader's AI "
                    "second look and known fixes."])
    summary.append(["Cells cut correctly % = cells whose picture holds this field's writing, whole (tester's "
                    "judgement; a cell not marked counts as correct once its row is checked). Cut off = part of "
                    "the writing missing; wrong place = another field's or row's writing. Pipeline flagged = the "
                    "OCR module itself warned that writing runs outside the cut."])
    for i in range(1, len(_SUMMARY_HEADERS) + 1):
        summary.column_dimensions[get_column_letter(i)].width = 20 if i > 1 else 24

    spreads = workbook.create_sheet(SPREADS_SHEET)
    spreads.append([label for _, label in _SPREAD_HEADERS])
    for row in summarize(lines, by_spread=True):
        spreads.append([row.get(key) for key, _ in _SPREAD_HEADERS])
    _style_header(spreads)
    spreads.append([])
    spreads.append(["A spread is the left (odd) and right (even) page scanned together: one patient's "
                    "entry runs across both."])
    for i in range(1, len(_SPREAD_HEADERS) + 1):
        spreads.column_dimensions[get_column_letter(i)].width = 20 if i > 1 else 30
    config.OCR_COMPARE_WORKBOOK.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(config.OCR_COMPARE_WORKBOOK)


def save_rows(items):
    """Write scored fields (ocr_compare.scored_rows) to the workbook,
    replacing earlier lines of the same run and row. Returns the summary
    and {"added", "replaced", "total"}."""
    with _lock:
        lines = _read_lines(config.OCR_COMPARE_WORKBOOK)
        keys = {(i["run_id"], i["spread_id"], i["row"] + 1) for i in items}
        kept = [l for l in lines if tuple(l[c] for c in _KEY_COLS) not in keys]
        saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        replaced = len(lines) - len(kept)
        kept.extend(_line(i, saved_at) for i in items)
        _write(kept)
    logger.info("OCR comparison: %d field line(s) saved, %d replaced", len(items), replaced)
    return {"added": len(items), "replaced": replaced, "total": len(kept), "summary": summarize(kept),
            "spreads": summarize(kept, by_spread=True)}


def summary():
    with _lock:
        lines = _read_lines(config.OCR_COMPARE_WORKBOOK)
    return {"total": len(lines), "summary": summarize(lines), "spreads": summarize(lines, by_spread=True)}


def clear():
    with _lock:
        _write([])
    return {"total": 0, "summary": [], "spreads": []}
