"""Test 1 - handwriting: 10 writers (5 capitals, 5 lowercase), PaddleOCR vs
Tesseract, raw and with the correction module.

    python -m research_tests.handwriting [--samples] [--writers W01,W02] [--fresh]

Inputs (inputs/, or inputs/samples/ with --samples):
  writers.csv               Writer ID | Style (caps/lower) | Set (main /
                            same_writer) | Scan File | Notes
  scans/handwriting/<file>  each writer's scanned logbook pages (PDF), on
                            the clinic's printed logbook layout
  answer_key.xlsx           sheet Handwriting: Writer ID | Style | Page |
                            Row | Field | Ground Truth

Each scan is read by the OCR comparison's own pipeline, unchanged
(ocr_compare.run_comparison): the production pipeline finds the rows and
cuts the cells, PaddleOCR reads them, TesseractOCR reads the very same cell
pictures, and both get the Logbook Reader's corrections. Every answer-key
cell is then scored with ocr_compare.score_reading (capitals, spaces
collapsed): exact match and character accuracy = 100 x (1 - CER).

A row of the answer key the pipeline did not find is "not detected": its
cells are listed, not scored, and each writer gets a row detection rate.
Cells left blank in the answer key (nothing written, e.g. no delivery) are
listed but not scored - there is no handwriting to read in them.

Runs are kept in outputs/work/ and reused when the same scan is scored
again (an answer-key fix needs no new OCR); --fresh reads them again.
"""
import hashlib
import json
from pathlib import Path

from research_tests import INPUTS, output_dir
from research_tests.common import answer_key, excel, stats

TEST_KEY = "handwriting"
TITLE = "Handwriting test (10 writers)"
VARIANTS = ("paddle_raw", "paddle_corrected", "tesseract_raw", "tesseract_corrected")
VARIANT_LABELS = {"paddle_raw": "PaddleOCR", "paddle_corrected": "PaddleOCR + Correction",
                  "tesseract_raw": "TesseractOCR", "tesseract_corrected": "TesseractOCR + Correction"}
RAW_HEADERS = (["Writer ID", "Style", "Set", "Scan File", "Page", "Row", "Field", "Detected", "Blank in Key",
                "Ground Truth"] + [f"{VARIANT_LABELS[v]} Output" if v.endswith("raw") else VARIANT_LABELS[v]
                                   for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Exact" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Accuracy %" for v in VARIANTS]
               + ["Paddle Confidence", "Tesseract Confidence", "Pipeline: Writing Outside Cut", "Run ID"])


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Reader:
    """The OCR comparison's pipeline with the research correction model
    (guard.research_model: SELECT only)."""

    def __init__(self):
        import ocr_compare
        import paddle_assist
        from ocr_engine import extract_tokens_from_array, read_many, read_versions_many
        from template_store import load_template_payloads
        from research_tests import guard
        self.ocr_compare = ocr_compare
        self.model, self.model_note = guard.research_model()
        self.templates = load_template_payloads()
        self.kwargs = dict(
            paddle_fn=extract_tokens_from_array, paddle_batch_fn=read_many,
            paddle_corrector=paddle_assist.make_corrector(extract_tokens_from_array, model=self.model,
                                                          batch_reader=read_versions_many),
            tesseract_fn=ocr_compare.tesseract_tokens,
            tesseract_corrector=paddle_assist.make_corrector(ocr_compare.tesseract_tokens, model=self.model))
        self.tesseract_error = ocr_compare.tesseract_available()

    def read(self, path, progress):
        return self.ocr_compare.run_comparison(str(path), path.name, self.templates, progress=progress, **self.kwargs)


def read_scans(scans, cache_path, fresh, progress, share=0.85):
    """{scan file: run} - each scan read once (or taken from the cache)."""
    import ocr_compare
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    runs, reader = {}, None
    for n, path in enumerate(scans):
        base = share * n / max(1, len(scans))
        digest = _sha256(path)
        hit = cache.get(path.name)
        run = None
        if hit and hit.get("sha256") == digest and not fresh:
            try:
                run = ocr_compare.load_run(hit["run_id"])
            except ValueError:
                run = None
        if run is None:
            if reader is None:
                progress(base, "Loading PaddleOCR and the correction model")
                reader = Reader()
            run = reader.read(path, lambda f, m, b=base: progress(b + share * f / len(scans), f"{path.name}: {m}"))
            cache[path.name] = {"sha256": digest, "run_id": run["run_id"]}
            cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        else:
            progress(base, f"{path.name}: using the reading kept from before")
        runs[path.name] = run
    return runs, reader


def index_run(run):
    """{(page, row, field label): field} and the set of (page, row) found."""
    cells, found = {}, set()
    for row in run["rows"]:
        for f in row["fields"]:
            key = (int(f["page"]), row["row"] + 1, f["label"])
            cells[key] = f
            found.add((int(f["page"]), row["row"] + 1))
    return cells, found


def score_cells(writer, key_cells, run):
    """One raw line (dict) per answer-key cell of this writer."""
    import ocr_compare
    cells, _ = index_run(run) if run else ({}, set())
    lines = []
    for k in key_cells:
        field = cells.get((k["page"], k["row"], k["field"]))
        line = {"writer": writer["writer"], "style": writer["style"], "set": writer["set"], "scan": writer["scan"],
                "page": k["page"], "row": k["row"], "field": k["field"], "truth": k["truth"],
                "detected": field is not None, "blank": not k["truth"].strip(), "run_id": run["run_id"] if run else ""}
        if field is not None:
            category = answer_key.FIELD_TO_CATEGORY[k["field"]]
            for v in VARIANTS:
                reading = field.get(v)
                line[v] = reading
                if reading is not None:
                    s = ocr_compare.score_reading(category, k["truth"], reading)
                    line[f"{v}_exact"], line[f"{v}_accuracy"] = s["exact"], s["accuracy"]
            line["paddle_confidence"] = field.get("paddle_confidence")
            line["tesseract_confidence"] = field.get("tesseract_confidence")
            line["cut_flag"] = field.get("cut_flag")
        lines.append(line)
    return lines


def _scored(lines):
    return [l for l in lines if l["detected"] and not l["blank"]]


def variant_scores(lines):
    """{variant: (exact %, mean character accuracy %)} over scored cells."""
    out = {}
    scored = _scored(lines)
    for v in VARIANTS:
        have = [l for l in scored if f"{v}_exact" in l]
        out[v] = (stats.percent(sum(1 for l in have if l[f"{v}_exact"]), len(have)),
                  stats.mean(l[f"{v}_accuracy"] for l in have))
    return out


def rows_in_key(lines):
    """Answer-key entries as (spread, row): a logbook entry spans the left
    and right page of one spread."""
    return {((l["page"] + 1) // 2, l["row"]) for l in lines}


def detection(lines):
    want = rows_in_key(lines)
    got = {((l["page"] + 1) // 2, l["row"]) for l in lines if l["detected"]}
    return len(want), len(got), stats.percent(len(got), len(want))


def _better(p, t):
    if p is None or t is None:
        return ""
    return "Yes" if p > t else "Tie" if p == t else "No"


def writer_summary(lines_by_writer, writers):
    headers = (["Writer", "Style", "Entries in key", "Entries detected", "Row detection rate %",
                "Cells scored", "Cells not detected"]
               + [f"{VARIANT_LABELS[v]} Exact %" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Character accuracy %" for v in VARIANTS]
               + ["PaddleOCR better (raw)", "PaddleOCR better (corrected)"])
    rows, per = [], {}
    for w in writers:
        lines = lines_by_writer.get((w["writer"], w["style"]), [])
        s = variant_scores(lines)
        total, found, rate = detection(lines)
        per[w["writer"]] = {"style": w["style"], "scores": s, "rate": rate}
        rows.append([w["writer"], w["style"], total, found, rate, len(_scored(lines)),
                     sum(1 for l in lines if not l["detected"])]
                    + [s[v][0] for v in VARIANTS] + [s[v][1] for v in VARIANTS]
                    + [_better(s["paddle_raw"][1], s["tesseract_raw"][1]),
                       _better(s["paddle_corrected"][1], s["tesseract_corrected"][1])])
    return headers, rows, per


def style_summary(per):
    headers = ["Style", "Writers", "Measure"] + [f"{VARIANT_LABELS[v]}" for v in VARIANTS]
    rows = []
    for style in ("caps", "lower"):
        group = [p for p in per.values() if p["style"] == style]
        if not group:
            continue
        for measure, idx in (("Exact %", 0), ("Character accuracy %", 1)):
            values = {v: [p["scores"][v][idx] for p in group] for v in VARIANTS}
            rows.append([style, len(group), f"{measure} - median"] + [stats.median(values[v]) for v in VARIANTS])
            rows.append([style, len(group), f"{measure} - range"] + [stats.value_range(values[v]) for v in VARIANTS])
        wins_raw = sum(1 for p in group if (p["scores"]["paddle_raw"][1] or 0) > (p["scores"]["tesseract_raw"][1] or 0))
        wins = sum(1 for p in group
                   if (p["scores"]["paddle_corrected"][1] or 0) > (p["scores"]["tesseract_corrected"][1] or 0))
        rows.append([style, len(group), "Writers where PaddleOCR beats Tesseract (raw / corrected)",
                     f"{wins_raw} of {len(group)}", "", f"{wins} of {len(group)}", ""])
        rows.append([style, len(group), "Row detection rate % - median",
                     stats.median(p["rate"] for p in group), "", "", ""])
    return headers, rows


def field_summary(lines):
    headers = (["Field", "Style", "Cells scored"] + [f"{VARIANT_LABELS[v]} Exact %" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Character accuracy %" for v in VARIANTS])
    rows = []
    for field in answer_key.FIELDS:
        for style in ("caps", "lower", "all"):
            group = [l for l in lines if l["field"] == field and (style == "all" or l["style"] == style)]
            if not _scored(group):
                continue
            s = variant_scores(group)
            rows.append([field, style, len(_scored(group))] + [s[v][0] for v in VARIANTS] + [s[v][1] for v in VARIANTS])
    s = variant_scores(lines)
    rows.append(["All fields", "all", len(_scored(lines))] + [s[v][0] for v in VARIANTS] + [s[v][1] for v in VARIANTS])
    return headers, rows


def raw_row(l):
    yes = lambda b: "" if b is None else ("Yes" if b else "No")
    return ([l["writer"], l["style"], l["set"], l["scan"], l["page"], l["row"], l["field"], yes(l["detected"]),
             yes(l["blank"]), l["truth"]]
            + [l.get(v) for v in VARIANTS] + [yes(l.get(f"{v}_exact")) for v in VARIANTS]
            + [l.get(f"{v}_accuracy") for v in VARIANTS]
            + [l.get("paddle_confidence"), l.get("tesseract_confidence"), yes(l.get("cut_flag")), l["run_id"]])


def run(progress, samples=False, writers=None, fresh=False):
    root = INPUTS / "samples" if samples else INPUTS
    for need in ("writers.csv", "answer_key.xlsx"):
        if not (root / need).is_file():
            raise FileNotFoundError(f"{root / need} not found - see inputs/*_template files (or use --samples).")
    all_writers = answer_key.writers(root / "writers.csv")
    if writers:
        wanted = {w.strip().upper() for w in writers.split(",")}
        all_writers = [w for w in all_writers if w["writer"] in wanted]
    key = answer_key.handwriting(root / "answer_key.xlsx")
    scans_dir = root / "scans" / "handwriting"
    missing = [w["scan"] for w in all_writers if not (scans_dir / w["scan"]).is_file()]
    if missing:
        raise FileNotFoundError(f"Scans not found in {scans_dir}: {', '.join(missing)}")

    out = output_dir(TEST_KEY)
    cache = out / ("runs_samples.json" if samples else "runs.json")
    runs, reader = read_scans([scans_dir / w["scan"] for w in all_writers], cache, fresh, progress)

    progress(0.9, "Scoring against the answer key")
    lines_by_writer, all_lines = {}, []
    for w in all_writers:
        cells = [k for k in key if k["writer"] == w["writer"] and (k["style"] in ("", w["style"]))]
        lines = score_cells(w, cells, runs.get(w["scan"]))
        lines_by_writer[(w["writer"], w["style"])] = lines
        all_lines += lines
    main = [w for w in all_writers if w["set"] == "main"]
    same = [w for w in all_writers if w["set"] != "main"]
    main_lines = [l for l in all_lines if l["set"] == "main"]

    wh, wr, per = writer_summary(lines_by_writer, main)
    sh, sr = style_summary(per)
    fh, fr = field_summary(main_lines)
    notes = [
        "Exact % = cells read exactly right (compared in capitals with spaces collapsed, i.e. case-insensitive). "
        "Character accuracy % = mean of 100 x (1 - CER) per cell (benchmarks/metrics.py).",
        "Readings: the OCR comparison pipeline unchanged (ocr_compare.run_comparison); Tesseract reads the same "
        "cell pictures as PaddleOCR. '+ Correction' = the Logbook Reader's corrections (AI second look, known "
        "fixes, place names, capitals).",
        "Cells whose ground truth is blank are left out of every accuracy figure and reported in '1e Blank cells' "
        "as false readings (the same rule in every test). Cells in rows the pipeline did not detect are not "
        "scored; not-detected rows are counted in the row detection rate.",
        "PaddleOCR better = higher mean character accuracy than Tesseract for that writer.",
    ]
    if reader:
        notes.append(f"Correction model: {reader.model_note}.")
    if samples:
        notes.append("COMPUTER-DRAWN SAMPLE DATA (make_samples.py) - not real handwriting; for checking the test only.")
    sheets = [
        {"name": "1a Per writer", "title": "Table - Handwriting results per writer", "headers": wh, "rows": wr,
         "notes": notes},
        {"name": "1b Per style", "title": "Table - Handwriting results per style group (median and range of "
                                          "the writers)", "headers": sh, "rows": sr, "notes": notes[:1]},
        {"name": "1c Per field", "title": "Table - Handwriting results per field", "headers": fh, "rows": fr,
         "bold_last": True, "notes": notes[:1]},
    ]
    not_detected = [[l["writer"], l["style"], l["page"], l["row"], l["field"], l["truth"]]
                    for l in all_lines if not l["detected"]]
    if same:
        same_rows = []
        for w in same:
            mine = lines_by_writer[(w["writer"], w["style"])]
            s = variant_scores(mine)
            total, found, rate = detection(mine)
            same_rows.append([w["writer"], w["style"], rate] + [s[v][0] for v in VARIANTS] + [s[v][1] for v in VARIANTS])
        diff_rows = []
        for writer in sorted({w["writer"] for w in same}):
            by_style = {r[1]: r for r in same_rows if r[0] == writer}
            if "caps" in by_style and "lower" in by_style:
                diff_rows.append([writer, "lower - caps", ""] + [
                    None if by_style["lower"][i] is None or by_style["caps"][i] is None
                    else round(by_style["lower"][i] - by_style["caps"][i], 2) for i in range(3, 3 + 2 * len(VARIANTS))])
        sheets.append({
            "name": "1d Same writer", "title": "Supplementary - the same writers in both styles",
            "headers": ["Writer", "Style", "Row detection rate %"] + [f"{VARIANT_LABELS[v]} Exact %" for v in VARIANTS]
                       + [f"{VARIANT_LABELS[v]} Character accuracy %" for v in VARIANTS],
            "rows": same_rows + diff_rows,
            "notes": ["Reported separately from the 10-writer test: each of these writers wrote pages in both styles.",
                      "'lower - caps' rows: percentage points, positive = lowercase read better."]})

    blank_rows = []
    for style in ("caps", "lower", "all"):
        group = [l for l in main_lines if l["detected"] and l["blank"] and style in ("all", l["style"])]
        row = [style, len(group)]
        for v in VARIANTS:
            have = [l for l in group if l.get(v) is not None]
            false = sum(1 for l in have if " ".join(str(l[v]).split()))
            row += [false, stats.percent(false, len(have))]
        blank_rows.append(row)
    blank_headers = ["Style", "Blank cells"]
    for v in VARIANTS:
        blank_headers += [f"{VARIANT_LABELS[v]} false readings", f"{VARIANT_LABELS[v]} false readings %"]
    sheets.append({"name": "1e Blank cells", "title": "Table - False readings on blank cells (ground truth blank)",
                   "headers": blank_headers, "rows": blank_rows,
                   "notes": ["A false reading = the engine read something in a cell where nothing is written "
                             "(detected rows of the 10 writers). These cells are not part of any accuracy figure."]})

    raw = {"name": "Raw data", "headers": RAW_HEADERS, "rows": [raw_row(l) for l in all_lines]}
    nd = {"name": "Not detected", "headers": ["Writer", "Style", "Page", "Row", "Field", "Ground Truth"],
          "rows": not_detected, "notes": ["Answer-key cells whose row the pipeline did not find on the scan."]}
    workbook = excel.write_workbook(out / "handwriting_results.xlsx", [raw] + sheets + [nd])
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    s = variant_scores(main_lines)
    return {"outputs": [workbook], "headline": [
        ["Writers", len(main)], ["Cells scored", len(_scored(main_lines))],
        ["PaddleOCR + Correction exact %", s["paddle_corrected"][0]],
        ["TesseractOCR + Correction exact %", s["tesseract_corrected"][0]],
        ["PaddleOCR + Correction character accuracy %", s["paddle_corrected"][1]],
        ["TesseractOCR + Correction character accuracy %", s["tesseract_corrected"][1]]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample inputs")
    parser.add_argument("--writers", help="only these writers, e.g. W01,W02")
    parser.add_argument("--fresh", action="store_true", help="read every scan again (ignore kept readings)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
