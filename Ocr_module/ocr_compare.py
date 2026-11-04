"""
OCR comparison (testing only): PaddleOCR vs Tesseract on the clinic's own
logbook scans, field by field, against a ground truth typed by the tester.

Shown on the "OCR comparison" page (templates/ocr_compare.html, routes/
compare_routes.py), an administrator's tool for the thesis. Nothing here
touches patients, claims, case_sessions or what the AI learns from reviews:
a run is kept as a JSON file under config.OCR_COMPARE_FOLDER, and checked
rows go to their own workbook (ocr_compare_store.py).

One scan, four readings of every cell:

  paddle_raw          PaddleOCR as the Logbook Reader reads it
  paddle_corrected    what the Logbook Reader would show staff: the AI
                      second look on unsure cells (paddle_assist), the
                      known fixes, place-name fixes, form capitals
  tesseract_raw       Tesseract on the very same cell picture
  tesseract_corrected the same corrections, with Tesseract as the reader
                      of the AI's second look

Fairness: the page layout (template match, row placement, cell crops) is
found once, by the production pipeline (logbook_pipeline.build_review_rows
with PaddleOCR), and Tesseract reads the exact cell pictures PaddleOCR did
(saved losslessly as PNG). Both engines therefore see the same pixels; the
only difference is the engine.

Scoring (score_reading), each reading against the ground truth:
  - compared in capitals with spaces collapsed (the forms store capitals);
  - exact: the whole cell right;
  - character accuracy: 100 * (1 - CER), benchmarks/metrics.py, clamped
    to 0-100. An empty ground truth (a blank cell) scores 100 when the
    reading is empty too, else 0;
  - field mapping: the reading split into the form fields it fills
    (review_fields.suggest_parts -> claim_fields: last/first/middle name,
    date, hour and AM/PM, ...), compared one form field at a time with the
    ground truth split the same way.

Spreads: the logbook is scanned two pages at a time - an odd (left) page
and the even (right) page beside it hold one patient's entry together.
The pipeline already pairs them (spread = odd page + the even page after
it); each run row says its spread as "SP-01" with its pages ("1-2"), and
each field which side it is on, so connected information reads together.

Cell cut reliability (how well the OCR module cuts the cells, apart from
how well an engine reads them): for every cell the tester says whether its
picture is cut correctly (this field's writing, whole), cut off (the right
cell, part of the writing missing) or in the wrong place (another field's
or row's writing, or the writing not in it). A cell not marked counts as
cut correctly once its row is checked. The pipeline's own warning that
writing runs outside the cut (logbook_pipeline.ocr_cell, "incomplete") is
kept beside it, to see how often the two agree.
"""
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime

import cv2

import config
import logbook_pipeline
import paddle_assist
from benchmarks.metrics import character_accuracy_percent
from philhealth import address_parser, case_bridge, review_fields

logger = logging.getLogger(__name__)

ENGINES = ("paddle", "tesseract")
VARIANTS = ("paddle_raw", "paddle_corrected", "tesseract_raw", "tesseract_corrected")
CUTS = {"correct": "Cut correctly", "cut_off": "Cut off", "wrong": "Wrong place"}
VARIANT_LABELS = {
    "paddle_raw": "PaddleOCR",
    "paddle_corrected": "PaddleOCR + correction",
    "tesseract_raw": "TesseractOCR",
    "tesseract_corrected": "TesseractOCR + correction",
}
_RUN_ID = re.compile(r"^[0-9a-f]{32}$")


# ── Scoring ──────────────────────────────────────────────────────────────

def _comparable(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().upper()


def mapped_fields(category, text):
    """{"patients.last_name": "DELA CRUZ", ...}: the form fields this text
    fills, as the review would split it. {} when it fills none."""
    try:
        parts = review_fields.suggest_parts(category, text)
        return {f"{table}.{column}": _comparable(value)
                for (table, column), value in review_fields.claim_fields(category, parts).items()}
    except Exception:
        return {}


def score_reading(category, truth, reading):
    """{"exact", "accuracy", "mapped_right", "mapped_total"} for one reading."""
    truth_c, reading_c = _comparable(truth), _comparable(reading)
    if not truth_c:
        accuracy = 100.0 if not reading_c else 0.0
    else:
        accuracy = round(character_accuracy_percent(truth_c, reading_c), 2)
    want = mapped_fields(category, truth_c)
    got = mapped_fields(category, reading_c)
    return {
        "exact": truth_c == reading_c,
        "accuracy": accuracy,
        "mapped_right": sum(1 for key, value in want.items() if got.get(key) == value),
        "mapped_total": len(want),
    }


def best_engine(scores):
    """"PaddleOCR" / "TesseractOCR" / "Tie": the corrected reading closer to
    the ground truth (character accuracy, then field mapping)."""
    p, t = scores.get("paddle_corrected"), scores.get("tesseract_corrected")
    if not p or not t:
        return "PaddleOCR" if p else "TesseractOCR" if t else ""
    key = lambda s: (s["accuracy"], s["mapped_right"])
    if key(p) == key(t):
        return "Tie"
    return "PaddleOCR" if key(p) > key(t) else "TesseractOCR"


def score_field(field, truth):
    scores = {v: score_reading(field["category"], truth, field[v]) for v in VARIANTS
              if field.get(v) is not None}
    return {"scores": scores, "best": best_engine(scores)}


# ── Corrections the Logbook Reader applies ──────────────────────────────

def corrected_value(category, value):
    """The reading as the Logbook Reader shows it to staff: the known fixes
    (paddle_assist.fix_saved_reading), place-name fixes for the address
    (address_parser.fix_place_names), form capitals - the same steps as
    review_routes._with_inputs."""
    value = paddle_assist.fix_saved_reading(category, value)
    if category == case_bridge.ADDRESS:
        value = address_parser.fix_place_names(value)
    return review_fields.in_capitals(category, value) or ""


# ── Reading with a second engine ────────────────────────────────────────

def read_fields_with(fields, crop_loader, ocr_fn, corrector=None, progress=None):
    """Read every field's cell picture again with another engine.

    fields: the production pipeline's fields (category, crop, ...).
    crop_loader(field) -> the cell picture (BGR array) or None.
    Returns one {"raw_text", "confidence", "value", "status", "seconds"}
    per field, in order: the same steps as build_review_rows - ocr_cell,
    confidence routing, the AI second look on unsure cells (corrector),
    best guesses, capitals - with ocr_fn as the engine.
    progress(fraction, message), if given, after every cell and during the
    second look."""
    out, unsure = [], []
    report = progress or (lambda fraction, message: None)
    for number, field in enumerate(fields, start=1):
        report(0.7 * number / max(1, len(fields)), f"cell {number} of {len(fields)}")
        crop = crop_loader(field)
        started = time.perf_counter()
        if crop is None:
            raw, conf, error, flags = "", None, "No cell picture", {"blank": False, "incomplete": False}
        else:
            raw, conf, _tokens, error, flags = logbook_pipeline.ocr_cell(crop, ocr_fn)
        flags["ditto"] = review_fields.is_ditto(raw)
        status = logbook_pipeline.field_status(field["category"], conf, flags)
        read = {
            "category": field["category"], "raw_text": raw, "confidence": conf, "ocr_error": error,
            "status": status, "value": "" if status in (logbook_pipeline.MANUAL, logbook_pipeline.EMPTY) else raw,
            "ai": None, "seconds": round(time.perf_counter() - started, 4),
        }
        out.append(read)
        if corrector and crop is not None and paddle_assist.wants_second_look(read, flags):
            unsure.append((read, crop))
    if corrector and unsure:
        report(0.7, f"second look at {len(unsure)} unsure cells")
        corrector(unsure, progress=lambda message, fraction: report(0.7 + 0.3 * fraction, f"second look: {message}"))
    logbook_pipeline.fill_best_guesses([{"fields": out}])
    for read in out:
        read["value"] = review_fields.in_capitals(read["category"], read["value"])
    return out


# Tesseract's page segmentation for a logbook cell: 6 = one block of text,
# which fits a one-line name as well as a diagnosis written over two lines
# (3, the default, looks for columns and pictures on what is one cell).
TESSERACT_PSM = os.environ.get("OCR_COMPARE_TESSERACT_PSM", "6")


def tesseract_available():
    """None when Tesseract can be used, else why not (plain words)."""
    try:
        import ocr_tesseract
        import pytesseract
        ocr_tesseract._configure_tesseract()
        pytesseract.get_tesseract_version()
        return None
    except Exception as exc:
        return ("TesseractOCR is not installed on this computer (or TESSERACT_CMD in .env does not "
                f"point to tesseract.exe): {type(exc).__name__}")


def tesseract_tokens(image):
    """Tesseract on a BGR cell picture -> [{"text", "confidence", "box"}],
    like ocr_engine.extract_tokens_from_array, boxes included so the
    pipeline's missed-writing check and retry apply to both engines.
    Confidence 0-1 (Tesseract gives 0-100). Errors propagate."""
    import ocr_tesseract
    import pytesseract
    ocr_tesseract._configure_tesseract()
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.ndim == 3 else image
    data = pytesseract.image_to_data(rgb, config=f"--psm {TESSERACT_PSM}",
                                     output_type=pytesseract.Output.DICT)
    tokens = []
    for i, text in enumerate(data["text"]):
        text = str(text).strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if not text or conf < 0:
            continue
        x, y, w, h = (int(data[k][i]) for k in ("left", "top", "width", "height"))
        tokens.append({"text": text, "confidence": round(conf / 100.0, 2),
                       "box": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]})
    return tokens


def load_crop(field):
    if not field.get("crop"):
        return None
    path = os.path.join(config.REVIEW_CROPS_FOLDER, *field["crop"].split("/"))
    return cv2.imread(path) if os.path.exists(path) else None


# ── One run ─────────────────────────────────────────────────────────────

def _page_side(page):
    try:
        return "left" if int(page) % 2 == 1 else "right"
    except (TypeError, ValueError):
        return ""


def spread_id(spread):
    """"SP-01" for the first spread (pages 1-2), "SP-02" for the next, ..."""
    return f"SP-{int(spread) + 1:02d}"


def spread_pages(rows):
    """{spread: "1-2"}: the pages each spread's rows were read from."""
    pages = {}
    for row in rows:
        pages.setdefault(row["spread"], set()).update(row["pages"])
    return {s: "-".join(str(p) for p in sorted(ps)) for s, ps in pages.items()}


def build_run(result, tesseract_reads, source_file, timings, tesseract_error=None):
    """The run as the page shows it, from build_review_rows' result and the
    second engine's readings (same order as the fields)."""
    reads = iter(tesseract_reads or [])
    pages_of = spread_pages(result["rows"])
    rows = []
    for row in result["rows"]:
        fields = []
        for field in row["fields"]:
            tess = next(reads, None) if tesseract_reads else None
            category = field["category"]
            fields.append({
                "category": category,
                "label": review_fields.FIELD_NAMES.get(category, category),
                "maps_to": ", ".join(t["label"] for t in case_bridge.target_fields(category)),
                "page": field["page"],
                "side": _page_side(field["page"]),
                "column": field["column"],
                "crop": field.get("crop"),
                "row_box": field.get("row_box"),
                # The pipeline thought writing runs outside this cell's cut.
                "cut_flag": bool(field.get("possibly_incomplete")),
                "paddle_raw": field.get("raw_text") or "",
                "paddle_confidence": field.get("confidence"),
                "paddle_status": field.get("routed_status"),
                "paddle_corrected": corrected_value(category, field.get("value")),
                "tesseract_raw": None if tess is None else tess["raw_text"] or "",
                "tesseract_confidence": None if tess is None else tess["confidence"],
                "tesseract_status": None if tess is None else tess["status"],
                "tesseract_corrected": None if tess is None else corrected_value(category, tess["value"]),
            })
        row_crop = next((f.get("row_crop") for f in row["fields"] if f.get("row_crop")), None)
        rows.append({"key": f"{row['spread']}-{row['row']}", "spread": row["spread"], "row": row["row"],
                     "spread_id": spread_id(row["spread"]), "spread_pages": pages_of.get(row["spread"], ""),
                     "pages": row["pages"], "row_crop": row_crop, "fields": fields})
    return {
        "run_id": result["upload_id"],
        "source_file": source_file,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pages": [{k: p.get(k) for k in ("page", "template", "match_score", "rows", "error")}
                  for p in result["pages"]],
        "image_quality": result.get("image_quality", {}).get("warnings", []),
        "timings": timings,
        "tesseract_error": tesseract_error,
        "rows": rows,
        "truth": {},        # {row key: [ground truth per field]}
        "cuts": {},         # {row key: [cell cut per field: CUTS key or ""]}
        "checked": [],      # row keys the tester marked checked
        "saved": [],        # row keys written to the workbook
    }


def run_comparison(path, source_file, templates, paddle_fn, paddle_batch_fn, paddle_corrector,
                   tesseract_fn, tesseract_corrector, progress=None):
    """Read one scan with both engines -> the run (also saved to disk)."""
    report = progress or (lambda fraction, message: None)
    run_id = uuid.uuid4().hex
    started = time.perf_counter()
    result = logbook_pipeline.build_review_rows(
        path, paddle_fn, templates, upload_id=run_id, corrector=paddle_corrector, batch_ocr_fn=paddle_batch_fn,
        progress=lambda fraction, message: report(0.6 * fraction, f"PaddleOCR: {message}"))
    paddle_seconds = time.perf_counter() - started

    fields = [f for row in result["rows"] for f in row["fields"]]
    reads, tesseract_error = None, tesseract_available() if tesseract_fn is tesseract_tokens else None
    started = time.perf_counter()
    if fields and not tesseract_error:
        report(0.6, f"TesseractOCR: reading {len(fields)} cells")
        try:
            reads = read_fields_with(fields, load_crop, tesseract_fn, tesseract_corrector,
                                     progress=lambda f, m: report(0.6 + 0.4 * f, f"TesseractOCR: {m}"))
        except ValueError:                # cancelled (routes/compare_routes.py)
            raise
        except Exception as exc:          # Tesseract not installed, or failed
            logger.warning("Tesseract could not read the comparison cells: %s", exc)
            tesseract_error = f"TesseractOCR could not run: {exc}"
    tesseract_seconds = time.perf_counter() - started

    cells = max(1, len(fields))
    timings = {
        "cells": len(fields),
        "paddle_seconds": round(paddle_seconds, 2),
        "tesseract_seconds": None if reads is None else round(tesseract_seconds, 2),
        "paddle_seconds_per_cell": round(paddle_seconds / cells, 3),
        "tesseract_seconds_per_cell": None if reads is None else round(tesseract_seconds / cells, 3),
        "note": "PaddleOCR time includes finding the rows on the page; both include the AI second look.",
    }
    run = build_run(result, reads, source_file, timings, tesseract_error)
    save_run(run)
    report(1.0, "Done")
    return run


# ── Runs on disk ────────────────────────────────────────────────────────

def _run_path(run_id):
    if not _RUN_ID.match(str(run_id or "")):
        raise ValueError("Unknown comparison run.")
    return os.path.join(config.OCR_COMPARE_FOLDER, f"{run_id}.json")


def save_run(run):
    os.makedirs(config.OCR_COMPARE_FOLDER, exist_ok=True)
    path = _run_path(run["run_id"])
    with open(path + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(run, fh, ensure_ascii=False)
    os.replace(path + ".tmp", path)


def load_run(run_id):
    path = _run_path(run_id)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run_ids():
    """The ids of every saved run - also the names of their cell-picture
    folders under config.REVIEW_CROPS_FOLDER, which the startup clean-up
    keeps (crop_cleanup.purge_old_crops)."""
    if not os.path.isdir(config.OCR_COMPARE_FOLDER):
        return []
    return [name[:-5] for name in os.listdir(config.OCR_COMPARE_FOLDER)
            if name.endswith(".json") and _RUN_ID.match(name[:-5])]


def list_runs():
    """Every saved run, newest first: id, file, date, rows, checked, saved."""
    if not os.path.isdir(config.OCR_COMPARE_FOLDER):
        return []
    runs = []
    for name in os.listdir(config.OCR_COMPARE_FOLDER):
        if not name.endswith(".json"):
            continue
        try:
            run = load_run(name[:-5])
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        if run:
            runs.append({"run_id": run["run_id"], "source_file": run["source_file"],
                         "created_at": run["created_at"], "rows": len(run["rows"]),
                         "checked": len(run.get("checked", [])), "saved": len(run.get("saved", []))})
    return sorted(runs, key=lambda r: r["created_at"], reverse=True)


def set_truth(run, truth, checked, cuts=None):
    """Keep the tester's ground truth ({row key: [text per field]}), how
    each cell was cut ({row key: [CUTS key or "" per field]}) and the rows
    marked checked. Only rows of this run, one entry per field."""
    sizes = {row["key"]: len(row["fields"]) for row in run["rows"]}

    def fit(values, size, clean):
        return [clean(v) for v in values[:size]] + [""] * max(0, size - len(values))

    for key, texts in (truth or {}).items():
        if key in sizes and isinstance(texts, list):
            run["truth"][key] = fit(texts, sizes[key], lambda t: str(t or "")[:500])
    run.setdefault("cuts", {})
    for key, marks in (cuts or {}).items():
        if key in sizes and isinstance(marks, list):
            run["cuts"][key] = fit(marks, sizes[key], lambda m: m if m in CUTS else "")
    if checked is not None:
        run["checked"] = [k for k in dict.fromkeys(checked) if k in sizes]
    return run


def scored_rows(run, keys):
    """The rows `keys` with every field scored against its ground truth,
    for the workbook (ocr_compare_store.save_rows)."""
    wanted = set(keys)
    out = []
    for row in run["rows"]:
        if row["key"] not in wanted:
            continue
        truth = run["truth"].get(row["key"]) or [""] * len(row["fields"])
        cuts = (run.get("cuts") or {}).get(row["key"]) or [""] * len(row["fields"])
        for field, gt, cut in zip(row["fields"], truth, cuts):
            out.append({"run_id": run["run_id"], "source_file": run["source_file"], "row_key": row["key"],
                        "spread": row["spread"], "row": row["row"], "field": field, "truth": gt,
                        "spread_id": row.get("spread_id") or spread_id(row["spread"]),
                        "spread_pages": row.get("spread_pages", ""),
                        # A cell not marked is taken as cut correctly: its row was checked.
                        "cut": cut or "correct", **score_field(field, gt)})
    return out
