"""Test 2 - correction module metrics (Eq. 3.2-3.4).

    python -m research_tests.correction_metrics [--source both|workbook|handwriting] [--workbook PATH]

Sources (each read-only):
  workbook     the OCR comparison workbook already made
               (Ocr_module/uploads/ocr_compare_results.xlsx, sheet Rows)
  handwriting  outputs/handwriting/handwriting_results.xlsx (test 1) - the
               cells in rows the pipeline detected

One rule for blank cells, everywhere: a cell whose ground truth is blank
(nothing written) is left out of every accuracy figure and reported apart,
as "false readings on blank cells" (the engine read something where nothing
is written). The OCR comparison workbook is also recomputed per field this
way; its original numbers, which count blank cells, are kept beside them,
labelled "including blank cells".

For each engine, raw reading vs the reading after the correction module:
  Accuracy improvement (Eq. 3.2) = post-correction - raw, in percentage
      points, for exact-match % and for character accuracy %
  Correction precision (Eq. 3.3) = changes that produced the correct value
      / all changes
  Harmful correction rate (Eq. 3.4) = correct raw values changed to
      incorrect / all changes

A "change" is a cell whose corrected reading differs from the raw one once
both are in capitals with spaces collapsed - the comparison the scoring
uses - so putting a lowercase reading in capitals is not counted as a
correction. Exact and character accuracy are ocr_compare.score_reading.
"""
from pathlib import Path

from research_tests import OCR_DIR, OUTPUTS, output_dir
from research_tests.common import answer_key, excel, stats

TEST_KEY = "correction_metrics"
TITLE = "Correction module metrics"
ENGINES = {"paddle": "PaddleOCR", "tesseract": "TesseractOCR"}
DEFAULT_WORKBOOK = OCR_DIR / "uploads" / "ocr_compare_results.xlsx"
HANDWRITING = OUTPUTS / "handwriting" / "handwriting_results.xlsx"


def _comparable(text):
    return " ".join(str(text or "").split()).upper()


_WORKBOOK_COLUMNS = {  # variant: (reading column, its accuracy column)
    "paddle_raw": ("PaddleOCR Output", "PaddleOCR Accuracy %"),
    "paddle_corrected": ("PaddleOCR + Correction", "PaddleOCR + Correction Accuracy %"),
    "tesseract_raw": ("TesseractOCR Output", "TesseractOCR Accuracy %"),
    "tesseract_corrected": ("TesseractOCR + Correction", "TesseractOCR + Correction Accuracy %"),
}


def from_workbook(path):
    """Every line of the Rows sheet. An empty reading comes back from Excel
    as None: it is "" when the line has that reading's accuracy (the engine
    read the cell and found nothing), None only when the engine did not run."""
    out = []
    # Readings beginning with "=" were stored by the comparison workbook as
    # Excel formulas; their text is the reading.
    for r in excel.read_rows(path, "Rows", header_row=0, formulas_as_text=True):
        if not r.get("Field"):
            continue
        cell = {"source": "OCR comparison workbook", "field": r.get("Field") or "",
                "truth": r.get("Ground Truth") or "", "where": f"{r.get('Spread ID')} row {r.get('Row')}"}
        for variant, (column, accuracy) in _WORKBOOK_COLUMNS.items():
            value = r.get(column)
            cell[variant] = value if value is not None else ("" if r.get(accuracy) not in (None, "") else None)
        out.append(cell)
    return out


def from_handwriting(path):
    out = []
    for r in excel.read_rows(path, "Raw data", header_row=0):
        if r.get("Detected") != "Yes":
            continue
        cell = {"source": "Handwriting test", "field": r.get("Field") or "", "truth": r.get("Ground Truth") or "",
                "where": f"{r.get('Writer ID')} p{r.get('Page')} row {r.get('Row')}"}
        # An empty reading comes back from Excel as None: "" when the reading
        # was scored (the engine ran and read nothing), None if it did not run.
        for variant, (column, accuracy) in _HANDWRITING_COLUMNS.items():
            value = r.get(column)
            cell[variant] = value if value is not None else ("" if r.get(accuracy) not in (None, "")
                                                             or r.get(f"{accuracy[:-len(' Accuracy %')]} Exact")
                                                             else None)
        out.append(cell)
    return out


_HANDWRITING_COLUMNS = {  # variant: (reading column, its accuracy column) in handwriting_results.xlsx
    "paddle_raw": ("PaddleOCR Output", "PaddleOCR Accuracy %"),
    "paddle_corrected": ("PaddleOCR + Correction", "PaddleOCR + Correction Accuracy %"),
    "tesseract_raw": ("TesseractOCR Output", "TesseractOCR Accuracy %"),
    "tesseract_corrected": ("TesseractOCR + Correction", "TesseractOCR + Correction Accuracy %"),
}


def judge(cell, engine):
    """Scores of one cell's raw and corrected reading for one engine, and
    what the correction did: unchanged / helpful / harmful / other."""
    import ocr_compare
    raw, corrected = cell[f"{engine}_raw"], cell[f"{engine}_corrected"]
    if raw is None or corrected is None:
        return None
    category = answer_key.FIELD_TO_CATEGORY.get(cell["field"], "")
    r = ocr_compare.score_reading(category, cell["truth"], raw)
    c = ocr_compare.score_reading(category, cell["truth"], corrected)
    changed = _comparable(raw) != _comparable(corrected)
    if not changed:
        outcome = "unchanged"
    elif c["exact"] and not r["exact"]:
        outcome = "helpful"
    elif r["exact"] and not c["exact"]:
        outcome = "harmful"
    else:
        outcome = "other"           # wrong before and after (or a change that keeps it right)
    return {"raw_exact": r["exact"], "corrected_exact": c["exact"], "raw_acc": r["accuracy"],
            "corrected_acc": c["accuracy"], "changed": changed, "outcome": outcome}


def metrics(judged):
    """The summary numbers for a list of judge() results."""
    judged = [j for j in judged if j]
    n = len(judged)
    changes = [j for j in judged if j["changed"]]
    produced_correct = sum(1 for j in changes if j["corrected_exact"])
    harmful = sum(1 for j in changes if j["outcome"] == "harmful")
    exact_raw = stats.percent(sum(j["raw_exact"] for j in judged), n)
    exact_cor = stats.percent(sum(j["corrected_exact"] for j in judged), n)
    acc_raw, acc_cor = stats.mean(j["raw_acc"] for j in judged), stats.mean(j["corrected_acc"] for j in judged)
    diff = lambda a, b: None if a is None or b is None else round(b - a, 2)
    return {
        "n": n, "exact_raw": exact_raw, "exact_corrected": exact_cor, "exact_gain": diff(exact_raw, exact_cor),
        "acc_raw": acc_raw, "acc_corrected": acc_cor, "acc_gain": diff(acc_raw, acc_cor),
        "changes": len(changes), "produced_correct": produced_correct, "harmful": harmful,
        "helpful": sum(1 for j in changes if j["outcome"] == "helpful"),
        "precision": stats.ratio(produced_correct, len(changes)),
        "harmful_rate": stats.ratio(harmful, len(changes)),
    }


METRIC_HEADERS = ["Cells", "Exact % raw", "Exact % corrected", "Exact improvement (pp, Eq. 3.2)",
                  "Character accuracy % raw", "Character accuracy % corrected",
                  "Character accuracy improvement (pp, Eq. 3.2)", "Changes made", "Changes that produced the correct value",
                  "Correct raw values made incorrect", "Correction precision (Eq. 3.3)",
                  "Harmful correction rate (Eq. 3.4)"]


def metric_row(m):
    return [m["n"], m["exact_raw"], m["exact_corrected"], m["exact_gain"], m["acc_raw"], m["acc_corrected"],
            m["acc_gain"], m["changes"], m["produced_correct"], m["harmful"], m["precision"], m["harmful_rate"]]


def is_blank(cell):
    return not _comparable(cell["truth"])


def false_reading(reading):
    return reading is not None and bool(_comparable(reading))


VARIANTS = ("paddle_raw", "paddle_corrected", "tesseract_raw", "tesseract_corrected")
VARIANT_LABELS = {"paddle_raw": "PaddleOCR", "paddle_corrected": "PaddleOCR + Correction",
                  "tesseract_raw": "TesseractOCR", "tesseract_corrected": "TesseractOCR + Correction"}


def variant_accuracy(cells):
    """[exact % x4, character accuracy % x4] over these cells."""
    import ocr_compare
    exact, acc = [], []
    for v in VARIANTS:
        scores = [ocr_compare.score_reading(answer_key.FIELD_TO_CATEGORY.get(c["field"], ""), c["truth"], c[v])
                  for c in cells if c[v] is not None]
        exact.append(stats.percent(sum(s["exact"] for s in scores), len(scores)))
        acc.append(stats.mean(s["accuracy"] for s in scores))
    return exact + acc


def run(progress, source="both", workbook=None):
    cells, used = [], []
    if source in ("both", "workbook"):
        path = Path(workbook) if workbook else DEFAULT_WORKBOOK
        if path.is_file():
            progress(0.1, f"Reading {path.name}")
            got = from_workbook(path)
            cells += got
            used.append(f"{path} ({len(got)} cells)")
        elif source == "workbook":
            raise FileNotFoundError(f"{path} not found")
    if source in ("both", "handwriting"):
        if HANDWRITING.is_file():
            progress(0.3, "Reading the handwriting results")
            got = from_handwriting(HANDWRITING)
            cells += got
            used.append(f"{HANDWRITING.name} ({len(got)} cells)")
        elif source == "handwriting":
            raise FileNotFoundError(f"{HANDWRITING} not found - run the handwriting test first")
    if not cells:
        raise FileNotFoundError("No source found: neither the OCR comparison workbook nor the handwriting results.")

    progress(0.5, f"Judging {len(cells)} cells")
    judged = [{e: judge(c, e) for e in ENGINES} for c in cells]
    sources = sorted({c["source"] for c in cells})
    scored = [i for i, c in enumerate(cells) if not is_blank(c)]

    overall_rows, field_rows = [], []
    for src in sources + (["All sources"] if len(sources) > 1 else []):
        idx = [i for i in scored if src == "All sources" or cells[i]["source"] == src]
        for e, label in ENGINES.items():
            m = metrics([judged[i][e] for i in idx])
            if m["n"]:
                overall_rows.append([src, label] + metric_row(m))
        for field in answer_key.FIELDS:
            fidx = [i for i in idx if cells[i]["field"] == field]
            for e, label in ENGINES.items():
                m = metrics([judged[i][e] for i in fidx])
                if m["n"]:
                    field_rows.append([src, field, label] + metric_row(m))

    # False readings on blank cells (ground truth blank, the engine read something).
    blank_rows = []
    for src in sources + (["All sources"] if len(sources) > 1 else []):
        group = [c for c in cells if is_blank(c) and (src == "All sources" or c["source"] == src)]
        row = [src, len(group)]
        for v in VARIANTS:
            have = [c for c in group if c[v] is not None]
            false = sum(1 for c in have if false_reading(c[v]))
            row += [false, stats.percent(false, len(have))]
        blank_rows.append(row)
    blank_headers = ["Source", "Blank cells"]
    for v in VARIANTS:
        blank_headers += [f"{VARIANT_LABELS[v]} false readings", f"{VARIANT_LABELS[v]} false readings %"]

    # The OCR comparison workbook recomputed: per field without blank cells,
    # and the original way (blank cells included) beside it.
    workbook_rows, workbook_including = [], []
    wb_cells = [c for c in cells if c["source"] == "OCR comparison workbook"]
    if wb_cells:
        for field in answer_key.FIELDS:
            group = [c for c in wb_cells if c["field"] == field and not is_blank(c)]
            if group:
                workbook_rows.append([field, "excluding blank cells", len(group)] + variant_accuracy(group))
        nonblank = [c for c in wb_cells if not is_blank(c)]
        workbook_rows.append(["All fields", "excluding blank cells", len(nonblank)] + variant_accuracy(nonblank))
        workbook_rows.append(["All fields", "including blank cells (original)", len(wb_cells)]
                             + variant_accuracy(wb_cells))
        all_idx = [i for i, c in enumerate(cells) if c["source"] == "OCR comparison workbook"]
        for e, label in ENGINES.items():
            m = metrics([judged[i][e] for i in all_idx])
            if m["n"]:
                workbook_including.append(["OCR comparison workbook (including blank cells)", label] + metric_row(m))

    notes = [
        "Eq. 3.2: accuracy improvement = post-correction minus raw, in percentage points (pp).",
        "Eq. 3.3: correction precision = changes that produced the correct value / all changes.",
        "Eq. 3.4: harmful correction rate = correct raw values changed to incorrect / all changes.",
        "A change = corrected reading differs from the raw reading in capitals with spaces collapsed (the scoring's "
        "comparison), so capitalising alone is not a change. '+ Correction' = the Logbook Reader's corrections: AI "
        "second look on unsure cells (re-read of enhanced pictures), known fixes, place names, capitals.",
        "Blank cells (ground truth blank) are left out of every figure here and reported in '2c Blank cells' as "
        "false readings. The workbook's original figures, which count blank cells, are in 2d and 2e, labelled "
        "'including blank cells'.",
        "Handwriting test: cells in rows the pipeline detected. Readings the comparison workbook stored as Excel "
        "formulas (Tesseract readings beginning with '=') are read as text.",
        "Sources: " + "; ".join(used),
    ]
    sheets = [
        {"name": "2a Correction overall", "title": "Table - Correction module metrics per engine",
         "headers": ["Source", "Engine"] + METRIC_HEADERS, "rows": overall_rows, "notes": notes},
        {"name": "2b Correction per field", "title": "Table - Correction module metrics per field",
         "headers": ["Source", "Field", "Engine"] + METRIC_HEADERS, "rows": field_rows, "notes": notes[:3]},
        {"name": "2c Blank cells", "title": "Table - False readings on blank cells (ground truth blank)",
         "headers": blank_headers, "rows": blank_rows,
         "notes": ["A false reading = the engine read something in a cell where nothing is written. These cells are "
                   "not part of any accuracy figure."]},
    ]
    if workbook_rows:
        sheets.append({"name": "2d Workbook recomputed", "title": "Table - OCR comparison workbook recomputed "
                       "without blank cells (original, including blank cells, last)",
                       "headers": ["Field", "Cells", "Count"] + [f"{VARIANT_LABELS[v]} Exact %" for v in VARIANTS]
                                  + [f"{VARIANT_LABELS[v]} Character accuracy %" for v in VARIANTS],
                       "rows": workbook_rows,
                       "notes": ["Exact % and character accuracy % (100 x (1 - CER)) by ocr_compare.score_reading. "
                                 "The 'including blank cells' line is the workbook's own way of counting (its Summary "
                                 "sheet)."]})
        sheets.append({"name": "2e Workbook incl. blanks", "title": "Table - Correction metrics on the OCR "
                       "comparison workbook, including blank cells (original counting)",
                       "headers": ["Source", "Engine"] + METRIC_HEADERS, "rows": workbook_including,
                       "notes": ["For comparison with the workbook's own Summary sheet only; the Chapter 5 figures "
                                 "exclude blank cells (2a)."]})
    raw_headers = ["Source", "Where", "Field", "Ground Truth"]
    for label in ENGINES.values():
        raw_headers += [f"{label} raw", f"{label} corrected", f"{label} changed", f"{label} outcome"]
    raw_rows = []
    for c, j in zip(cells, judged):
        line = [c["source"], c["where"], c["field"], c["truth"]]
        for e in ENGINES:
            jj = j[e] or {}
            line += [c[f"{e}_raw"], c[f"{e}_corrected"], "Yes" if jj.get("changed") else "No" if jj else "",
                     jj.get("outcome", "")]
        raw_rows.append(line)
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "correction_metrics_results.xlsx",
                                [{"name": "Raw data", "headers": raw_headers, "rows": raw_rows}] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets)
    progress(1.0, "Done")
    headline = [[f"{r[0]} - {r[1]}", f"exact {r[5]:+} pp, precision {r[12]}, harmful {r[13]}"]
                for r in overall_rows if r[5] is not None]
    return {"outputs": [path], "headline": headline}


def add_arguments(parser):
    parser.add_argument("--source", choices=("both", "workbook", "handwriting"), default="both")
    parser.add_argument("--workbook", help=f"OCR comparison workbook (default {DEFAULT_WORKBOOK})")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
