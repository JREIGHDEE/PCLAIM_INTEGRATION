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
from research_tests.common.normalize import normalized_equal

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
        self.model = paddle_assist.load_model()          # the one research model (guard.isolate)
        self.model_note = guard._state["model_note"]
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
    """{variant: (exact % (Eq. 3.1), mean character accuracy %, exact % normalized)}
    over scored cells."""
    out = {}
    scored = _scored(lines)
    for v in VARIANTS:
        have = [l for l in scored if f"{v}_exact" in l]
        out[v] = (stats.percent(sum(1 for l in have if l[f"{v}_exact"]), len(have)),
                  stats.mean(l[f"{v}_accuracy"] for l in have),
                  stats.percent(sum(1 for l in have if normalized_equal(l["field"], l["truth"], l.get(v))), len(have)))
    return out


def in_place_lines(lines):
    """Only the rows the system placed on the right entry (1h)."""
    return [l for l in lines if l.get("alignment", "in place") == "in place"]


def _entries(lines):
    """{(scan method, writer, spread, row): {page: found}} - a logbook entry
    spans the left and right page of one spread."""
    entries = {}
    for l in lines:
        key = (l.get("method"), l.get("writer"), (l["page"] + 1) // 2, l["row"])
        pages = entries.setdefault(key, {})
        pages[l["page"]] = pages.get(l["page"], False) or bool(l["detected"])
    return entries


def rows_in_key(lines):
    return set(_entries(lines))


def detection(lines):
    """(entries in the key, entries found, %): an entry is found only when
    its row was found on BOTH pages of the spread."""
    entries = _entries(lines)
    got = sum(1 for pages in entries.values() if all(pages.values()))
    return len(entries), got, stats.percent(got, len(entries))


def page_row_detection(lines):
    """(page rows in the key, page rows found, %)"""
    rows = {}
    for (method, writer, _spread, row), pages in _entries(lines).items():
        for page, found in pages.items():
            rows[(method, writer, page, row)] = found
    got = sum(rows.values())
    return len(rows), got, stats.percent(got, len(rows))


def _better(p, t):
    if p is None or t is None:
        return ""
    return "Yes" if p > t else "Tie" if p == t else "No"


def writer_summary(lines_by_writer, writers):
    headers = (["Writer", "Style", "Entries in key", "Entries detected (both pages)", "Row detection rate %",
                "Page rows found", "Page rows found %", "Cells scored", "Cells not detected"]
               + [f"{VARIANT_LABELS[v]} Exact % (Eq. 3.1)" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Exact % normalized" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Character accuracy %" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Exact % (in-place rows)" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Character accuracy % (in-place rows)" for v in VARIANTS]
               + ["PaddleOCR better (raw)", "PaddleOCR better (corrected)"])
    rows, per = [], {}
    for w in writers:
        lines = lines_by_writer.get((w["writer"], w["style"]), [])
        s = variant_scores(lines)
        total, found, rate = detection(lines)
        p_total, p_found, p_rate = page_row_detection(lines)
        si = variant_scores(in_place_lines(lines))
        per[w["writer"]] = {"style": w["style"], "scores": s, "in_place": si, "rate": rate}
        rows.append([w["writer"], w["style"], total, found, rate, f"{p_found} of {p_total}", p_rate,
                     len(_scored(lines)),
                     sum(1 for l in lines if not l["detected"])]
                    + [s[v][0] for v in VARIANTS] + [s[v][2] for v in VARIANTS] + [s[v][1] for v in VARIANTS]
                    + [si[v][0] for v in VARIANTS] + [si[v][1] for v in VARIANTS]
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
        for measure, idx, which in (("Exact % (Eq. 3.1)", 0, "scores"), ("Exact % normalized", 2, "scores"),
                                    ("Character accuracy %", 1, "scores"),
                                    ("Exact % (in-place rows)", 0, "in_place"),
                                    ("Character accuracy % (in-place rows)", 1, "in_place")):
            values = {v: [p[which][v][idx] for p in group] for v in VARIANTS}
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
    headers = (["Field", "Style", "Cells scored"] + [f"{VARIANT_LABELS[v]} Exact % (Eq. 3.1)" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Exact % normalized" for v in VARIANTS]
               + [f"{VARIANT_LABELS[v]} Character accuracy %" for v in VARIANTS])
    rows = []
    for field in answer_key.FIELDS:
        for style in ("caps", "lower", "all"):
            group = [l for l in lines if l["field"] == field and (style == "all" or l["style"] == style)]
            if not _scored(group):
                continue
            s = variant_scores(group)
            rows.append([field, style, len(_scored(group))] + [s[v][0] for v in VARIANTS]
                        + [s[v][2] for v in VARIANTS] + [s[v][1] for v in VARIANTS])
    s = variant_scores(lines)
    rows.append(["All fields", "all", len(_scored(lines))] + [s[v][0] for v in VARIANTS]
                + [s[v][2] for v in VARIANTS] + [s[v][1] for v in VARIANTS])
    return headers, rows


def raw_row(l):
    yes = lambda b: "" if b is None else ("Yes" if b else "No")
    return ([l["writer"], l["style"], l["set"], l["scan"], l["page"], l["row"], l["field"], yes(l["detected"]),
             yes(l["blank"]), l["truth"]]
            + [l.get(v) for v in VARIANTS] + [yes(l.get(f"{v}_exact")) for v in VARIANTS]
            + [l.get(f"{v}_accuracy") for v in VARIANTS]
            + [l.get("paddle_confidence"), l.get("tesseract_confidence"), yes(l.get("cut_flag")), l["run_id"]])



# ── dry check: do the answer key's rows line up with the rows found? ────

ANCHORS = {1: ("Case number", "Patient name", "Birthday"), 2: ("Reason for admission", "Final diagnosis", "Went home")}


def _similarity(truth, reading):
    from benchmarks.metrics import character_accuracy_percent
    t, r = " ".join(str(truth or "").split()).upper(), " ".join(str(reading or "").split()).upper()
    if not t:
        return None
    return max(0.0, min(100.0, character_accuracy_percent(t, r)))


def dry_check(progress, writers_list, key, scans_dir):
    """Row finding with PaddleOCR only (no Tesseract, no correction), and for
    every answer-key row: was a row found with that number, and does its text
    match the key better than the rows just above and below it (a shifted
    row would match a neighbour)? -> (lines, per writer summary)"""
    import uuid
    import logbook_pipeline
    from ocr_engine import extract_tokens_from_array, read_many
    from template_store import load_template_payloads
    templates = load_template_payloads()
    lines, summary = [], []
    for n, w in enumerate(writers_list):
        path = w.get("path") or scans_dir / w["scan"]
        base = n / len(writers_list)
        progress(base, f"{w['scan']}: finding the rows (PaddleOCR only)")
        result = logbook_pipeline.build_review_rows(
            str(path), extract_tokens_from_array, templates, upload_id=uuid.uuid4().hex, batch_ocr_fn=read_many,
            progress=lambda f, m, b=base: progress(b + f / len(writers_list), f"{w['scan']}: {m}"))
        # {(page, row): {field label: reading}} of the rows found
        found = {}
        for row in result["rows"]:
            for f in row["fields"]:
                found.setdefault((int(f["page"]), row["row"] + 1), {})[
                    review_fields_name(f["category"])] = f.get("raw_text") or ""
        mine = [k for k in key if k["writer"] == w["writer"] and k["style"] in ("", w["style"])]
        key_rows = sorted({(k["page"], k["row"]) for k in mine})
        truth = {}
        for k in mine:
            truth.setdefault((k["page"], k["row"]), {})[k["field"]] = k["truth"]
        problems = 0
        for page, row in key_rows:
            anchors = [f for f in ANCHORS[page] if truth[(page, row)].get(f)]

            def score(r):
                got = found.get((page, r))
                if got is None:
                    return None
                values = [_similarity(truth[(page, row)][f], got.get(f, "")) for f in anchors]
                values = [v for v in values if v is not None]
                return round(sum(values) / len(values), 1) if values else None
            here, above, below = score(row), score(row - 1), score(row + 1)
            if (page, row) not in found:
                status = "not detected"
            elif here is None:
                status = "detected (no text to compare)"
            else:
                best = max((v, d) for v, d in ((above, -1), (below, +1)) if v is not None) if (
                    above is not None or below is not None) else None
                status = "aligned" if best is None or here >= best[0] - 10 or here >= 60 else \
                    f"shifted? row {row + best[1]} matches better"
            if status != "aligned":
                problems += 1
            lines.append([w["writer"], w["scan"], page, row, status, here, above, below,
                          " | ".join(f"{f}: {truth[(page, row)].get(f, '')}" for f in anchors),
                          " | ".join(f"{f}: {(found.get((page, row)) or {}).get(f, '')}" for f in anchors)])
        extra = sorted(k for k in found if k not in set(key_rows))
        for page, row in extra:
            lines.append([w["writer"], w["scan"], page, row, "found, not in the answer key", None, None, None, "",
                          " | ".join(f"{f}: {v}" for f, v in found[(page, row)].items() if v)[:200]])
        pages = {p["page"]: p for p in result["pages"]}
        summary.append([w["writer"], w["scan"], len(key_rows) // 2 if key_rows else 0,
                        len({r for (pg, r) in found if pg == 1}), len({r for (pg, r) in found if pg == 2}),
                        problems, len(extra),
                        "; ".join(f"p{pg}: {pages[pg].get('error')}" for pg in pages if pages[pg].get("error"))])
    return lines, summary


def review_fields_name(category):
    from philhealth import review_fields
    return review_fields.FIELD_NAMES.get(category, category)


def run_dry_check(progress, root, writers_list, key, samples, method="scanner"):
    lines, summary = dry_check(progress, writers_list, key, root / "scans" / "handwriting")
    bad = [l for l in lines if l[4] != "aligned"]
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / f"handwriting_dry_check{'' if method == 'scanner' else '_' + method}.xlsx", [
        {"name": "Per writer", "title": "Dry check - answer key rows vs rows found (PaddleOCR only)",
         "headers": ["Writer", "Scan", "Entries in key", "Rows found page 1", "Rows found page 2",
                     "Key rows not aligned", "Rows found not in key", "Page errors"], "rows": summary,
         "notes": ["Aligned = a row was found with that number and its text matches the key at least as well as "
                   "the rows above and below (within 10 points), or at 60 % character accuracy or more.",
                   "Anchors: case number, name, birthday (page 1); reason, final diagnosis, went home (page 2).",
                   "SAMPLE DATA" if samples else f"Real scans (inputs/), scan method: {method}."]},
        {"name": "Rows", "headers": ["Writer", "Scan", "Page", "Row", "Status", "Match here %", "Match row above %",
                                     "Match row below %", "Answer key (anchors)", "PaddleOCR read (anchors)"],
         "rows": lines},
    ])
    progress(1.0, "Done")
    return {"outputs": [path], "headline": [[f"{method}: key rows checked", sum(1 for l in lines if l[4] != "found, not in the answer key")],
                                            ["Not aligned / not detected", len([l for l in bad if l[4] != "found, not in the answer key"])],
                                            ["Rows found that are not in the key", len([l for l in bad if l[4] == "found, not in the answer key"])]]
            + [[f"{method} {l[0]} p{l[2]} row {l[3]}", l[4]] for l in bad[:60]]}


METHODS = ("scanner", "phone")
METHOD_NOTE = ("Scan methods: scanner = the flatbed scans (scans/handwriting/<Writer>_<style>.pdf); phone = the same "
               "pages taken with a phone camera scanner app (<Writer>_<style>_phone.pdf, in scans/handwriting_phone/ "
               "or scans/handwriting/). Both go through the real pipeline unchanged: the same image quality check, "
               "grid templates and row detection, no extra preprocessing.")


def scan_path(root, writer, method):
    """The scan file of this writer for this scan method, or the path it
    should have (for the error message)."""
    folder = root / "scans" / "handwriting"
    if method == "scanner":
        return folder / writer["scan"]
    stem = Path(writer["scan"]).stem
    name = f"{stem}_phone.pdf"
    for candidate in (root / "scans" / "handwriting_phone" / name, folder / name):
        if candidate.is_file():
            return candidate
    return root / "scans" / "handwriting_phone" / name


def page_reports(path, run):
    """Per page: IQ-01 (the pipeline's own check, on the page as the pipeline
    loads it) and how the page was matched and cut (from the run)."""
    import logbook_pipeline
    from image_quality import assess_image_quality
    found = {p["page"]: p for p in (run or {}).get("pages", [])}
    out = []
    import template_engine
    for number, image, _parity in logbook_pipeline.load_pages(str(path)):
        iq = assess_image_quality(image)
        p = found.get(number, {})
        # The pipeline's own ruled-line finding on the same (straightened) page.
        rules = template_engine.detect_ruling_lines(image)
        _regular, pitch = template_engine.regular_ruled_lines(rules["horizontal"], image.shape[0])
        gaps = [b - a for a, b in zip(rules["horizontal"], rules["horizontal"][1:])]
        spread = (round(100 * (max(gaps) - min(gaps)) / (sum(gaps) / len(gaps)), 1) if len(gaps) > 2 else None)
        out.append({"page": number, "blur": iq["blur_score"], "brightness": iq["brightness_score"],
                    "ink": iq["ink_level"], "iq": "pass" if iq["passed"] else "warn",
                    "iq_why": "; ".join(w for w, on in (("blurry", iq["is_blurry"]), ("too dark", iq["is_too_dark"]),
                                                        ("too bright", iq["is_too_bright"])) if on),
                    "template": p.get("template") or "", "match": p.get("match_score"), "rows": p.get("rows"),
                    "error": p.get("error") or "", "size": f"{image.shape[1]} x {image.shape[0]} px",
                    "h_lines": len(rules["horizontal"]), "v_lines": len(rules["vertical"]),
                    "pitch": round(pitch, 1) if pitch else None, "gap_spread": spread,
                    "skew": round(template_engine.estimate_skew(image), 2)})
    return out


ALIGN_ANCHORS = {1: ("Case number", "Patient name", "Birthday"),
                 2: ("Reason for admission", "Final diagnosis", "Went home")}


def row_alignment(lines, run):
    """For every answer-key page row: is the detected row with that number
    the right entry ("in place"), a neighbour's ("shifted"), or missing
    ("not detected")? Compared on PaddleOCR's raw readings of three anchor
    fields per page. A shifted left page against its right page pairs one
    patient's details with another's diagnoses in the Logbook Reader."""
    from benchmarks.metrics import character_accuracy_percent
    cells, found = index_run(run) if run else ({}, set())

    def sim(truth, reading):
        t, r = " ".join(str(truth or "").split()).upper(), " ".join(str(reading or "").split()).upper()
        return max(0.0, min(100.0, character_accuracy_percent(t, r))) if t else None

    truth = {}
    for l in lines:
        truth.setdefault((l["page"], l["row"]), {})[l["field"]] = l["truth"]
    out = {}
    for (page, row), fields in truth.items():
        anchors = [f for f in ALIGN_ANCHORS.get(page, ()) if fields.get(f)]

        def score(r):
            if (page, r) not in found:
                return None
            vals = [sim(fields[f], (cells.get((page, r, f)) or {}).get("paddle_raw")) for f in anchors]
            vals = [v for v in vals if v is not None]
            return sum(vals) / len(vals) if vals else None
        here = score(row)
        near = [(score(row + d), d) for d in (-1, 1)]
        near = [(v, d) for v, d in near if v is not None]
        if (page, row) not in found:
            status, moved = "not detected", None
        elif here is None or not near or here >= max(near)[0] - 10 or here >= 60:
            status, moved = "in place", 0
        else:
            status, moved = "shifted", max(near)[1]
        out[(page, row)] = {"status": status, "moved": moved, "here": None if here is None else round(here, 1)}
    return out


def correction_rows(lines):
    """Eq. 3.3-3.4 per engine on the scored cells (correction_metrics.judge)."""
    from research_tests import correction_metrics as cm
    rows = {}
    for engine, label in cm.ENGINES.items():
        m = cm.metrics([cm.judge(l, engine) for l in _scored(lines) if l.get(f"{engine}_raw") is not None])
        rows[engine] = m
    return rows


BANDS = (("<0.65", 0, 0.65), ("0.65-<0.85", 0.65, 0.85), (">=0.85", 0.85, 2), ("no reading", None, None))
THRESHOLDS = (0.65, 0.75, 0.85, 0.90, 0.95)


def band_of(line):
    c = line.get("paddle_confidence")
    if c is None or not str(line.get("paddle_raw") or "").strip():
        return "no reading"
    return next(name for name, lo, hi in BANDS[:3] if lo <= c < hi)


def confidence_tables(method, lines):
    """1i bands, 1j bands by field, 1k threshold choices - on the scored cells,
    by PaddleOCR's own confidence (the Section 3.7 routing thresholds)."""
    scored = _scored(lines)
    readings = (("paddle_raw", "PaddleOCR"), ("paddle_corrected", "PaddleOCR + Correction"))
    bands = []
    for v, label in readings:
        wrong_all = sum(1 for l in scored if not l.get(f"{v}_exact"))
        for name, _lo, _hi in BANDS:
            group = [l for l in scored if band_of(l) == name]
            wrong = sum(1 for l in group if not l.get(f"{v}_exact"))
            bands.append([method, label, name, len(group),
                          stats.percent(sum(1 for l in group if l.get(f"{v}_exact")), len(group)),
                          stats.percent(sum(1 for l in group if normalized_equal(l["field"], l["truth"], l.get(v))),
                                        len(group)),
                          stats.mean(l.get(f"{v}_accuracy") for l in group), wrong, stats.percent(wrong, wrong_all)])
    by_field = []
    for field in answer_key.FIELDS:
        for name, _lo, _hi in BANDS:
            group = [l for l in scored if l["field"] == field and band_of(l) == name]
            if not group:
                continue
            by_field.append([method, field, name, len(group),
                             stats.percent(sum(1 for l in group if l.get("paddle_raw_exact")), len(group)),
                             stats.percent(sum(1 for l in group if l.get("paddle_corrected_exact")), len(group)),
                             stats.percent(sum(1 for l in group if normalized_equal(field, l["truth"],
                                                                                    l.get("paddle_corrected"))),
                                           len(group)),
                             stats.mean(l.get("paddle_corrected_accuracy") for l in group)])
    thresholds = []
    wrong_all = [l for l in scored if not l.get("paddle_corrected_exact")]
    wrong_all_norm = [l for l in scored if not normalized_equal(l["field"], l["truth"], l.get("paddle_corrected"))]
    for t in THRESHOLDS + (None,):
        accepted = [] if t is None else [l for l in scored if band_of(l) != "no reading"
                                         and l["paddle_confidence"] >= t]
        wrong = [l for l in accepted if not l.get("paddle_corrected_exact")]
        wrong_norm = [l for l in accepted if not normalized_equal(l["field"], l["truth"], l.get("paddle_corrected"))]
        thresholds.append([method, "never (all to review)" if t is None else f"{t:.2f}" + (" (current)" if t == 0.85 else ""),
                           len(accepted), len(wrong), stats.percent(len(wrong), len(accepted)),
                           stats.percent(len(wrong), len(wrong_all)), len(wrong_norm),
                           stats.percent(len(wrong_norm), len(wrong_all_norm)), len(scored) - len(accepted)])
    return {"bands": bands, "by_field": by_field, "thresholds": thresholds}


def method_tables(method, lines, writers_list, pages, runs):
    """Every per-method table, each row starting with the scan method."""
    by_writer = {(w["writer"], w["style"]): [l for l in lines if l["writer"] == w["writer"] and l["style"] == w["style"]]
                 for w in writers_list}
    wh, wr, per = writer_summary(by_writer, writers_list)
    sh, sr = style_summary(per)
    fh, fr = field_summary(lines)
    total, found, rate = detection(lines)
    page_rows_found = page_row_detection(lines)
    blank = []
    for style in ("caps", "lower", "all"):
        group = [l for l in lines if l["detected"] and l["blank"] and style in ("all", l["style"])]
        row = [method, style, len(group)]
        for v in VARIANTS:
            have = [l for l in group if l.get(v) is not None]
            false = sum(1 for l in have if " ".join(str(l[v]).split()))
            row += [false, stats.percent(false, len(have))]
        blank.append(row)
    corr = correction_rows(lines)
    align_rows = []
    for w in writers_list:
        mine = {(l["page"], l["row"]): l["alignment"] for l in lines if l["writer"] == w["writer"]}
        for page in (1, 2):
            states = [v for (pg, _r), v in mine.items() if pg == page]
            align_rows.append([method, w["writer"], page, len(states), states.count("in place"), states.count("shifted"),
                               states.count("not detected"), stats.percent(states.count("in place"), len(states))])
    states = [l["alignment"] for l in {(l["writer"], l["page"], l["row"]): l for l in lines}.values()]
    in_place = stats.percent(states.count("in place"), len(states))
    times = []
    for w in writers_list:
        run = runs.get(w["writer"])
        if not run:
            continue
        t = run.get("timings") or {}
        entries = len({r["row"] for r in run["rows"]})
        times.append([method, w["writer"], w["scan_file"], entries, t.get("cells"), t.get("paddle_seconds"),
                      round(t["paddle_seconds"] * 1000 / entries, 1) if entries and t.get("paddle_seconds") else None,
                      t.get("tesseract_seconds"),
                      round(t["tesseract_seconds"] * 1000 / entries, 1) if entries and t.get("tesseract_seconds") else None])
    return {"writer": (wh, [[method] + r for r in wr]), "style": (sh, [[method] + r for r in sr]),
            "field": (fh, [[method] + r for r in fr]), "detection": (total, found, rate), "page_rows": page_rows_found, "per": per,
            "blank": blank, "correction": corr, "times": times, "pages": pages,
            "alignment": align_rows, "in_place": in_place,
            "scores": variant_scores(lines), "in_place_scores": variant_scores(in_place_lines(lines)),
            "confidence": confidence_tables(method, lines)}


def comparison_rows(t):
    """Scanner vs phone, each measure, and phone - scanner."""
    def diff(a, b):
        return None if a is None or b is None or isinstance(a, str) or isinstance(b, str) else round(b - a, 2)
    rows = []

    def add(measure, s, p, unit="pp"):
        rows.append([measure, s, p, diff(s, p), unit if diff(s, p) is not None else ""])

    sc, ph = t["scanner"], t["phone"]
    add("Entries detected % (row found on both pages)", sc["detection"][2], ph["detection"][2])
    add("Page rows found %", sc["page_rows"][2], ph["page_rows"][2])
    add("Page rows in place % (the detected row holds that entry)", sc["in_place"], ph["in_place"])
    for name, key in (("Pages passing IQ-01 %", "iq"),):
        s = [p for pages in sc["pages"].values() for p in pages]
        q = [p for pages in ph["pages"].values() for p in pages]
        add(name, stats.percent(sum(p["iq"] == "pass" for p in s), len(s)),
            stats.percent(sum(p["iq"] == "pass" for p in q), len(q)))
        add("Mean blur variance (Laplacian)", stats.mean(p["blur"] for p in s), stats.mean(p["blur"] for p in q), "")
        add("Mean brightness", stats.mean(p["brightness"] for p in s), stats.mean(p["brightness"] for p in q), "")
        add("Pages with no matching logbook setup", sum(1 for p in s if p["error"]), sum(1 for p in q if p["error"]), "")
    for v in VARIANTS:
        add(f"{VARIANT_LABELS[v]} exact % (all cells)", sc["scores"][v][0], ph["scores"][v][0])
    for v in VARIANTS:
        add(f"{VARIANT_LABELS[v]} exact % normalized (all cells)", sc["scores"][v][2], ph["scores"][v][2])
    for v in VARIANTS:
        add(f"{VARIANT_LABELS[v]} character accuracy % (all cells)", sc["scores"][v][1], ph["scores"][v][1])
    for v in VARIANTS:
        add(f"{VARIANT_LABELS[v]} character accuracy % (in-place rows only)", sc["in_place_scores"][v][1],
            ph["in_place_scores"][v][1])
    for style in ("caps", "lower"):
        for v in VARIANTS:
            s = [p["scores"][v][1] for p in sc["per"].values() if p["style"] == style]
            q = [p["scores"][v][1] for p in ph["per"].values() if p["style"] == style]
            add(f"{VARIANT_LABELS[v]} character accuracy % - {style}, median of writers", stats.median(s), stats.median(q))
    for engine, label in (("paddle", "PaddleOCR"), ("tesseract", "TesseractOCR")):
        add(f"{label} correction precision (Eq. 3.3)", sc["correction"][engine]["precision"],
            ph["correction"][engine]["precision"], "")
        add(f"{label} harmful correction rate (Eq. 3.4)", sc["correction"][engine]["harmful_rate"],
            ph["correction"][engine]["harmful_rate"], "")
    add("Processing time per entry, PaddleOCR pipeline (ms)", stats.mean(r[6] for r in sc["times"]),
        stats.mean(r[6] for r in ph["times"]), "ms")
    return rows


def run(progress, samples=False, writers=None, fresh=False, dry_check=False, method="scanner"):
    root = INPUTS / "samples" if samples else INPUTS
    for need in ("writers.csv", "answer_key.xlsx"):
        if not (root / need).is_file():
            raise FileNotFoundError(f"{root / need} not found - see inputs/*_template files (or use --samples).")
    if method not in ("scanner", "phone", "both"):
        raise ValueError("--method is scanner, phone or both")
    methods = list(METHODS) if method == "both" else [method]
    all_writers = answer_key.writers(root / "writers.csv")
    if writers:
        wanted = {w.strip().upper() for w in writers.split(",")}
        all_writers = [w for w in all_writers if w["writer"] in wanted]
    key = answer_key.handwriting(root / "answer_key.xlsx")
    missing = [str(scan_path(root, w, m).relative_to(root)) for m in methods for w in all_writers
               if not scan_path(root, w, m).is_file()]
    if missing:
        raise FileNotFoundError(f"Scans not found: {', '.join(missing)}")
    main_writers = [w for w in all_writers if w["set"] == "main"]

    if dry_check:
        results = []
        for n, m in enumerate(methods):
            sub = lambda f, msg, n=n, m=m: progress((n + f) / len(methods), f"{m}: {msg}")
            listed = [dict(w, path=scan_path(root, w, m), scan=scan_path(root, w, m).name) for w in all_writers]
            results.append(run_dry_check(sub, root, listed, key, samples, m))
        return {"outputs": [p for r in results for p in r["outputs"]],
                "headline": [h for r in results for h in r["headline"]]}

    # A supplementary run (e.g. the held-out learning run) writes to its own folder.
    import os
    out = output_dir(TEST_KEY + os.environ.get("RESEARCH_OUTPUT_SUFFIX", ""))
    tables, all_lines, model_note = {}, [], ""
    for n, m in enumerate(methods):
        base, width = n / len(methods), 1 / len(methods)
        sub = lambda f, msg, b=base, w=width, m=m: progress(b + w * 0.9 * f, f"{m}: {msg}")
        paths = [scan_path(root, w, m) for w in all_writers]
        cache = out / (f"runs_samples{'' if m == 'scanner' else '_' + m}.json" if samples
                       else f"runs{'' if m == 'scanner' else '_' + m}.json")
        runs_by_file, reader = read_scans(paths, cache, fresh, sub, share=1.0)
        if reader:
            model_note = reader.model_note
        progress(base + width * 0.92, f"{m}: image quality and scoring")
        runs, pages, lines = {}, {}, []
        for w, path in zip(all_writers, paths):
            run_ = runs_by_file.get(path.name)
            runs[w["writer"]] = run_
            pages[w["writer"]] = page_reports(path, run_)
            cells = [k for k in key if k["writer"] == w["writer"] and k["style"] in ("", w["style"])]
            align = row_alignment(cells, run_)
            for line in score_cells(dict(w, scan=path.name), cells, run_):
                line["method"] = m
                a = align.get((line["page"], line["row"]), {})
                line["alignment"] = a.get("status", "")
                line["moved"] = a.get("moved")
                lines.append(line)
        all_lines += lines
        listed = [dict(w, scan_file=paths[i].name) for i, w in enumerate(all_writers) if w["set"] == "main"]
        tables[m] = method_tables(m, [l for l in lines if l["set"] == "main"], listed, pages, runs)

    notes = [
        "Exact % = cells read exactly right (compared in capitals with spaces collapsed, i.e. case-insensitive). "
        "Character accuracy % = mean of 100 x (1 - CER) per cell (benchmarks/metrics.py).",
        "Readings: the OCR comparison pipeline unchanged (ocr_compare.run_comparison); Tesseract reads the same "
        "cell pictures as PaddleOCR. '+ Correction' = the Logbook Reader's corrections (AI second look, known "
        "fixes, place names, capitals).",
        "Cells whose ground truth is blank are left out of every accuracy figure and reported in '1e Blank cells' "
        "as false readings (the same rule in every test). Cells in rows the pipeline did not detect are not "
        "scored; not-detected rows are counted in the row detection rate and listed in 'Not detected'.",
        "PaddleOCR better = higher mean character accuracy than Tesseract for that writer.",
        "Exact % (Eq. 3.1) is the primary figure (strict: capitals, spaces collapsed). Exact % normalized "
        "(secondary) also: removes every space; in Admitted, Birthday, Delivered and Went home treats -, / and . "
        "as the same separator; in Case number treats a hyphen like a space. Nothing else (no leading zeros added "
        "or dropped, no letter/digit changes).",
        "Phone rows: scored against the key row with the same number, as the system presents them (primary); "
        "'(in-place rows)' columns use only the rows 1h finds in place (secondary).",
        METHOD_NOTE,
    ]
    if model_note:
        notes.append(f"Correction model: {model_note}.")
    if os.environ.get("RESEARCH_RUN_LABEL"):
        notes.insert(0, os.environ["RESEARCH_RUN_LABEL"])
    if samples:
        notes.append("COMPUTER-DRAWN SAMPLE DATA (make_samples.py) - not real handwriting; for checking the test only.")

    first = methods[0]
    sheets = []
    if len(methods) == 2:
        sheets.append({"name": "1s Scanner vs phone", "title": "Table - Scanner vs phone camera scans, same pages and "
                       "answer key", "headers": ["Measure", "Scanner", "Phone", "Difference (phone - scanner)", "Unit"],
                       "rows": comparison_rows(tables), "notes": [METHOD_NOTE,
                       "Difference in percentage points (pp) for percentages; precision and harmful rate are ratios "
                       "(0-1); time in milliseconds. Blank ground-truth cells excluded."]})
    join = lambda part: (["Scan Method"] + tables[first][part][0], [r for m in methods for r in tables[m][part][1]])
    wh, wr = join("writer")
    sh, sr = join("style")
    fh, fr = join("field")
    sheets += [
        {"name": "1a Per writer", "title": "Table - Handwriting results per writer", "headers": wh, "rows": wr,
         "notes": notes},
        {"name": "1b Per style", "title": "Table - Handwriting results per style group (median and range of "
                                          "the writers)", "headers": sh, "rows": sr, "notes": notes[:1]},
        {"name": "1c Per field", "title": "Table - Handwriting results per field", "headers": fh, "rows": fr,
         "notes": notes[:1]},
    ]
    det_rows = [[m, tables[m]["detection"][0], tables[m]["detection"][1], tables[m]["detection"][2],
                 tables[m]["page_rows"]] for m in methods]
    page_rows = [[m, w, p["page"], p["size"], p["blur"], p["brightness"], p["ink"], p["iq"], p["iq_why"],
                  p["template"], p["match"], p["rows"], p["h_lines"], p["pitch"], p["gap_spread"], p["skew"], p["error"]]
                 for m in methods for w, pages in tables[m]["pages"].items() for p in pages]
    sheets.append({"name": "1d Detection and IQ", "title": "Table - Rows detected and IQ-01 per page",
                   "headers": ["Scan Method", "Writer", "Page", "Page size", "Blur variance", "Brightness", "Ink level",
                               "IQ-01", "IQ-01 reason", "Logbook setup matched", "Match score", "Rows found",
                               "Printed lines found", "Line spacing (px)", "Line spacing spread %",
                               "Tilt left after straightening (deg)", "Why the page failed"],
                   "rows": page_rows,
                   "notes": ["Overall: " + "; ".join(f"{m}: entries {d[2]} % ({d[1]} of {d[0]} found on both pages), "
                                                     f"page rows {d[3][2]} % ({d[3][1]} of {d[3][0]})"
                                                     for m, *d in det_rows),
                             "IQ-01 = image_quality.assess_image_quality on the page as the pipeline loads it "
                             "(logbook_pipeline.load_pages). Thresholds: blur < 100, brightness < 60 or > 200 with the "
                             "ink washed out.",
                             "Why the page failed = the pipeline's own message (e.g. no logbook setup matching the "
                             "page's printed columns).",
                             "Printed lines found / line spacing / spread / tilt = the pipeline's own ruled-line finding "
                             "(template_engine.detect_ruling_lines, regular_ruled_lines, estimate_skew) on the page as "
                             "it loads it. Rows are placed on these lines, so missing lines, uneven spacing (a camera "
                             "photo's perspective) or leftover tilt is why rows go missing or shift."]})
    sheets.append({"name": "1h Row alignment", "title": "Table - Are the detected rows the right entries?",
                   "headers": ["Scan Method", "Writer", "Page", "Rows in key", "In place", "Shifted", "Not detected",
                               "In place %"],
                   "rows": [r for m in methods for r in tables[m]["alignment"]],
                   "notes": ["In place = the detected row with that number holds that entry (PaddleOCR's raw reading "
                             "of case number/name/birthday, or reason/final diagnosis/went home, matches that row of "
                             "the key at least as well as the rows next to it). Shifted = it holds a neighbouring "
                             "entry: the system numbered the rows differently from the logbook, and a left page "
                             "shifted against its right page pairs one patient's details with another's diagnoses.",
                             "Accuracy figures score each cell against the key row with the same number - how the "
                             "system presents it - so a shifted row lowers them."]})
    blank_headers = ["Scan Method", "Style", "Blank cells"]
    for v in VARIANTS:
        blank_headers += [f"{VARIANT_LABELS[v]} false readings", f"{VARIANT_LABELS[v]} false readings %"]
    sheets.append({"name": "1e Blank cells", "title": "Table - False readings on blank cells (ground truth blank)",
                   "headers": blank_headers, "rows": [r for m in methods for r in tables[m]["blank"]],
                   "notes": ["A false reading = the engine read something in a cell where nothing is written. These "
                             "cells are not part of any accuracy figure."]})
    from research_tests import correction_metrics as cm
    corr_rows = [[m, cm.ENGINES[e]] + cm.metric_row(tables[m]["correction"][e]) for m in methods for e in cm.ENGINES]
    sheets.append({"name": "1f Correction", "title": "Table - Correction module on the handwriting, per scan method",
                   "headers": ["Scan Method", "Engine"] + cm.METRIC_HEADERS, "rows": corr_rows,
                   "notes": ["Eq. 3.2-3.4 as in test 2 (correction_metrics.py), on this test's scored cells."]})
    sheets.append({"name": "1g Time per entry", "title": "Table - Processing time per entry, per scan method",
                   "headers": ["Scan Method", "Writer", "Scan", "Entries found", "Cells", "PaddleOCR pipeline (s)",
                               "PaddleOCR pipeline per entry (ms)", "Tesseract (s)", "Tesseract per entry (ms)"],
                   "rows": [r for m in methods for r in tables[m]["times"]]
                           + [[m, "Mean", "", "", "", "", stats.mean(r[6] for r in tables[m]["times"]), "",
                               stats.mean(r[8] for r in tables[m]["times"])] for m in methods],
                   "notes": ["PaddleOCR pipeline = what the Logbook Reader runs: finding the rows and cells, PaddleOCR "
                             "and the AI second look (ocr_compare.run_comparison's own timing). Tesseract reads the "
                             "same cells afterwards and is timed apart. Times are from the run that read the scan "
                             "(--fresh to read again)."]})

    conf_note = ("PaddleOCR's own confidence for the cell; bands = the Section 3.7 routing thresholds (config "
                 "OCR_CONFIDENCE_REVIEW 0.65, OCR_CONFIDENCE_ACCEPT 0.85); 'no reading' = PaddleOCR read nothing. "
                 "Scored cells only (detected rows, blank ground truth excluded). '+ Correction' keeps the cell's "
                 "original confidence, as the routing does.")
    sheets.append({"name": "1i Confidence bands", "title": "Table - Accuracy by PaddleOCR confidence band",
                   "headers": ["Scan Method", "Reading", "Confidence band", "Cells", "Exact % (Eq. 3.1)",
                               "Exact % normalized", "Character accuracy %", "Wrong values (strict)",
                               "Share of all wrong values %"],
                   "rows": [r for m in methods for r in tables[m]["confidence"]["bands"]], "notes": [conf_note]})
    sheets.append({"name": "1j Confidence by field", "title": "Table - Accuracy by confidence band and field",
                   "headers": ["Scan Method", "Field", "Confidence band", "Cells", "PaddleOCR Exact %",
                               "PaddleOCR + Correction Exact %", "Exact % normalized (corrected)",
                               "Character accuracy % (corrected)"],
                   "rows": [r for m in methods for r in tables[m]["confidence"]["by_field"]], "notes": [conf_note]})
    sheets.append({"name": "1k Threshold choices", "title": "Table - What each accept threshold would pre-fill "
                   "as accepted", "headers": ["Scan Method", "Accept threshold", "Cells pre-filled as accepted",
                                              "Of which wrong (strict)", "Wrong among accepted %",
                                              "Share of all wrong values accepted %", "Of which wrong (normalized)",
                                              "Share of all wrong values accepted % (normalized)",
                                              "Cells sent to review"],
                   "rows": [r for m in methods for r in tables[m]["confidence"]["thresholds"]],
                   "notes": [conf_note, "Accepted = confidence at or above the threshold (a cell with no reading is "
                             "never accepted). Wrong = the value staff would see (PaddleOCR + Correction) is not the "
                             "ground truth. Share = wrong values accepted / all wrong values: the errors that would "
                             "reach the forms without a 'please check' flag."]})

    raw = {"name": "Raw data", "headers": ["Scan Method"] + RAW_HEADERS + ["Row Alignment"],
           "rows": [[l["method"]] + raw_row(l) + [l.get("alignment", "")] for l in all_lines]}
    nd = {"name": "Not detected", "headers": ["Scan Method", "Writer", "Style", "Page", "Row", "Field", "Ground Truth"],
          "rows": [[l["method"], l["writer"], l["style"], l["page"], l["row"], l["field"], l["truth"]]
                   for l in all_lines if not l["detected"]],
          "notes": ["Answer-key cells whose row the pipeline did not find on the scan. Why: see '1d Detection and IQ' "
                    "(a page with no matching logbook setup, or fewer rows found than written)."]}
    workbook = excel.write_workbook(out / "handwriting_results.xlsx", [raw] + sheets + [nd])
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples, "methods": methods})
    progress(1.0, "Done")
    headline = []
    for m in methods:
        s = tables[m]["scores"]
        headline += [[f"{m}: entries detected % (both pages)", tables[m]["detection"][2]],
                     [f"{m}: page rows found %", tables[m]["page_rows"][2]],
                     [f"{m}: page rows in place %", tables[m]["in_place"]],
                     [f"{m}: PaddleOCR + Correction exact % / character %", f"{s['paddle_corrected'][0]} / {s['paddle_corrected'][1]}"],
                     [f"{m}: TesseractOCR + Correction exact % / character %", f"{s['tesseract_corrected'][0]} / {s['tesseract_corrected'][1]}"]]
    return {"outputs": [workbook], "headline": headline}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample inputs")
    parser.add_argument("--writers", help="only these writers, e.g. W01,W02")
    parser.add_argument("--method", choices=("scanner", "phone", "both"), default="scanner",
                        help="scan method: the flatbed scans, the phone camera scans, or both side by side")
    parser.add_argument("--fresh", action="store_true", help="read every scan again (ignore kept readings)")
    parser.add_argument("--dry-check", action="store_true",
                        help="only check that the answer key's rows line up with the rows found (PaddleOCR only)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
