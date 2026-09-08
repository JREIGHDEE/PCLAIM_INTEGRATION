"""
Fair, offline comparison between PaddleOCR and Tesseract on the same set of
test images/PDFs.

This is a standalone CLI tool. It does not run inside the Flask app, is not
registered as a route, and never touches the database, case_sessions, or
any reviewed-result data - it exists purely to produce documentation-ready
numbers for the capstone's OCR engine comparison. Running it does not
affect the production OCR workflow in any way.

Usage (from Ocr_module/, using this project's venv so the same PaddleOCR/
Tesseract dependencies as the app are used):

    venv\\Scripts\\python.exe -m benchmarks.compare_ocr_engines
    venv\\Scripts\\python.exe -m benchmarks.compare_ocr_engines --engines paddle
    venv\\Scripts\\python.exe -m benchmarks.compare_ocr_engines --engines tesseract
    venv\\Scripts\\python.exe -m benchmarks.compare_ocr_engines --runs 3
    venv\\Scripts\\python.exe -m benchmarks.compare_ocr_engines --ground-truth benchmarks\\ground_truth.csv

See benchmarks/README.md for the full methodology: warm-up, the exact
timing boundary, how repeated runs are reported, and CER/WER normalization.
"""
import argparse
import csv
import json
import os
import statistics
import time
import traceback

import numpy as np

from benchmarks.engine_adapters import ENGINES
from benchmarks.image_loader import iter_test_images
from benchmarks.metrics import (
    character_accuracy_percent,
    character_error_rate,
    word_accuracy_percent,
    word_error_rate,
)

DEFAULT_INPUT_DIR = os.path.join(os.path.dirname(__file__), "test_data")
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")

# One row per (image, engine): aggregated across all --runs repetitions.
AGGREGATE_FIELDNAMES = [
    "image_name", "category", "ocr_engine", "runs",
    "mean_processing_time_seconds", "min_processing_time_seconds",
    "max_processing_time_seconds", "stdev_processing_time_seconds",
    "average_confidence", "detected_text_regions", "extracted_text", "error",
]

# One row per (image, engine, run_index): the raw, unaggregated measurements
# the AGGREGATE_FIELDNAMES rows above are computed from.
RUN_FIELDNAMES = [
    "image_name", "category", "ocr_engine", "run_index",
    "processing_time_seconds", "detected_text_regions",
    "average_confidence", "extracted_text", "error",
]

# One row per (image, engine) that has ground truth available. Error rates
# (raw) plus accuracy percentages in the same 1-error_rate formulation as
# Nazeem et al. (2024, ICON) - see benchmarks/README.md's "Related
# literature" section and metrics.py's docstring.
ACCURACY_FIELDNAMES = [
    "image_name", "ocr_engine",
    "character_error_rate", "word_error_rate",
    "character_accuracy_percent", "word_accuracy_percent",
]


def _make_warmup_image():
    """A tiny synthetic image used only to trigger engine start-up costs.

    Never part of the benchmark dataset, never timed, never written to any
    output file - see run_benchmark()'s warm-up step and benchmarks/README.md.
    """
    return np.full((64, 256, 3), 255, dtype=np.uint8)


def _warm_up_engines(engines):
    """Run one throwaway OCR call per engine before any timed measurement.

    PaddleOCR (ocr_engine.get_ocr_engine()) lazily constructs its model on
    first use - without this step, whichever image happens to be processed
    first in the dataset would have that one-time model-load cost baked
    into its processing_time_seconds, which has nothing to do with
    steady-state OCR speed. This call absorbs that cost here instead, and
    its own timing/output is discarded entirely.

    Tesseract has no equivalent to exclude: pytesseract invokes tesseract.exe
    as a fresh subprocess on every single call (including this one), so
    there is no persistent in-process model state for a warm-up to prime -
    every real measurement already reflects Tesseract's normal per-call
    architecture. The warm-up call is still made for Tesseract too, purely
    so its very first real measurement isn't the one absorbing any one-time
    OS-level disk-cache warming for tessdata.
    """
    warmup_image = _make_warmup_image()
    for engine_name, engine_fn in engines.items():
        started = time.perf_counter()
        try:
            engine_fn(warmup_image)
            elapsed = time.perf_counter() - started
            print(f"Warm-up: {engine_name} took {elapsed:.4f}s (discarded, not counted in any result).")
        except Exception as exc:
            elapsed = time.perf_counter() - started
            message = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            print(f"Warm-up: {engine_name} failed after {elapsed:.4f}s: {message}")
            print(f"  ({engine_name} is likely misconfigured - real runs below will probably fail too.)")


def _load_ground_truth(path):
    """Load a CSV of image_name,correct_text whole-page transcriptions.

    Returns {} if path is None. Raises if the given path can't be read or
    parsed - a bad --ground-truth path should fail loudly rather than
    silently produce a benchmark with no accuracy numbers.
    """
    if not path:
        return {}
    ground_truth = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            image_name = (row.get("image_name") or "").strip()
            if image_name:
                ground_truth[image_name] = row.get("correct_text") or ""
    return ground_truth


def _run_single(engine_fn, image):
    """One timed OCR call. Returns a dict with time/regions/error - never raises."""
    started = time.perf_counter()
    try:
        regions = engine_fn(image)
        elapsed = time.perf_counter() - started
        confidences = [r["confidence"] for r in regions]
        return {
            "processing_time_seconds": round(elapsed, 4),
            "detected_text_regions": len(regions),
            "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
            "extracted_text": "\n".join(r["text"] for r in regions),
            "error": "",
            "regions": regions,
        }
    except Exception as exc:
        elapsed = time.perf_counter() - started
        message = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        return {
            "processing_time_seconds": round(elapsed, 4),
            "detected_text_regions": 0,
            "average_confidence": None,
            "extracted_text": "",
            "error": message,
            "regions": [],
        }


def _aggregate_runs(run_results):
    """Combine N _run_single() results for ONE (image, engine) pair.

    Never mixes runs across different images or engines - this is called
    once per (image, engine), with only that pair's own run_results.
    Timing stats (mean/min/max/stdev) are computed only over runs that
    succeeded (error == ""); if every run failed, all four are None.
    """
    successful = [r for r in run_results if not r["error"]]
    times = [r["processing_time_seconds"] for r in successful]

    if times:
        mean_time = round(sum(times) / len(times), 4)
        min_time = round(min(times), 4)
        max_time = round(max(times), 4)
        stdev_time = round(statistics.stdev(times), 4) if len(times) > 1 else None
    else:
        mean_time = min_time = max_time = stdev_time = None

    if successful:
        representative = successful[0]
        distinct_texts = {r["extracted_text"] for r in successful}
        consistency_note = "" if len(distinct_texts) <= 1 else (
            f"warning: extracted_text differed across {len(distinct_texts)} of "
            f"{len(successful)} successful runs - engine output may not be deterministic on this input"
        )
        average_confidence = representative["average_confidence"]
        detected_text_regions = representative["detected_text_regions"]
        extracted_text = representative["extracted_text"]
    else:
        average_confidence = None
        detected_text_regions = 0
        extracted_text = ""
        consistency_note = ""

    failed = [r for r in run_results if r["error"]]
    if not successful:
        error = failed[0]["error"] if failed else ""
    elif failed:
        error = f"{len(failed)}/{len(run_results)} runs failed: {failed[0]['error']}"
    else:
        error = consistency_note

    return {
        "runs": len(run_results),
        "mean_processing_time_seconds": mean_time,
        "min_processing_time_seconds": min_time,
        "max_processing_time_seconds": max_time,
        "stdev_processing_time_seconds": stdev_time,
        "average_confidence": average_confidence,
        "detected_text_regions": detected_text_regions,
        "extracted_text": extracted_text,
        "error": error,
    }


def run_benchmark(input_dir, output_dir, engine_names, num_runs=1, ground_truth_path=None):
    ground_truth = _load_ground_truth(ground_truth_path)
    engines = {name: ENGINES[name] for name in engine_names}

    os.makedirs(output_dir, exist_ok=True)
    raw_dir = os.path.join(output_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    _warm_up_engines(engines)

    aggregate_rows = []
    run_rows = []
    accuracy_rows = []
    found_any = False

    for category, display_name, image in iter_test_images(input_dir):
        found_any = True

        if image is None:
            decode_error = "Could not read/decode this file."
            aggregate_rows.append({
                "image_name": display_name, "category": category,
                "ocr_engine": ",".join(engines), "runs": 0,
                "mean_processing_time_seconds": None, "min_processing_time_seconds": None,
                "max_processing_time_seconds": None, "stdev_processing_time_seconds": None,
                "average_confidence": None, "detected_text_regions": 0,
                "extracted_text": "", "error": decode_error,
            })
            run_rows.append({
                "image_name": display_name, "category": category,
                "ocr_engine": ",".join(engines), "run_index": 1,
                "processing_time_seconds": 0, "detected_text_regions": 0,
                "average_confidence": None, "extracted_text": "", "error": decode_error,
            })
            continue

        for engine_name, engine_fn in engines.items():
            run_results = [_run_single(engine_fn, image) for _ in range(num_runs)]

            for run_index, result in enumerate(run_results, start=1):
                run_rows.append({
                    "image_name": display_name,
                    "category": category,
                    "ocr_engine": engine_name,
                    "run_index": run_index,
                    "processing_time_seconds": result["processing_time_seconds"],
                    "detected_text_regions": result["detected_text_regions"],
                    "average_confidence": result["average_confidence"],
                    "extracted_text": result["extracted_text"],
                    "error": result["error"],
                })

            aggregate = _aggregate_runs(run_results)
            aggregate_rows.append({
                "image_name": display_name,
                "category": category,
                "ocr_engine": engine_name,
                **aggregate,
            })

            raw_name = f"{os.path.splitext(display_name)[0]}__{engine_name}.json".replace("#", "_")
            with open(os.path.join(raw_dir, raw_name), "w", encoding="utf-8") as handle:
                json.dump({
                    "image_name": display_name,
                    "category": category,
                    "ocr_engine": engine_name,
                    "runs": [
                        {
                            "run_index": i + 1,
                            "processing_time_seconds": r["processing_time_seconds"],
                            "error": r["error"],
                            "regions": r["regions"],
                        }
                        for i, r in enumerate(run_results)
                    ],
                }, handle, indent=2, ensure_ascii=False)

            if display_name in ground_truth:
                reference = ground_truth[display_name]
                hypothesis = aggregate["extracted_text"]
                accuracy_rows.append({
                    "image_name": display_name,
                    "ocr_engine": engine_name,
                    "character_error_rate": character_error_rate(reference, hypothesis),
                    "word_error_rate": word_error_rate(reference, hypothesis),
                    # Same accuracy-percentage formulation as Nazeem et al.
                    # (2024, ICON) - see benchmarks/README.md's "Related
                    # literature" section and metrics.py's docstring.
                    "character_accuracy_percent": character_accuracy_percent(reference, hypothesis),
                    "word_accuracy_percent": word_accuracy_percent(reference, hypothesis),
                })

    if not found_any:
        print(
            f"No test images found under '{input_dir}'.\n"
            "This tool never fabricates test data - add real (or properly "
            "anonymized) scans first. See benchmarks/README.md for the "
            "expected folder layout."
        )
        return

    agg_path = os.path.join(output_dir, "comparison_results.csv")
    with open(agg_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AGGREGATE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(aggregate_rows)
    print(f"Wrote {len(aggregate_rows)} aggregated result row(s) (one per image x engine) to {agg_path}")

    runs_path = os.path.join(output_dir, "comparison_results_runs.csv")
    with open(runs_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_FIELDNAMES)
        writer.writeheader()
        writer.writerows(run_rows)
    print(f"Wrote {len(run_rows)} individual run row(s) to {runs_path}")
    print(f"Raw per-image/per-engine/per-run OCR output saved under {raw_dir}")

    if accuracy_rows:
        accuracy_path = os.path.join(output_dir, "accuracy_results.csv")
        with open(accuracy_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=ACCURACY_FIELDNAMES)
            writer.writeheader()
            writer.writerows(accuracy_rows)
        print(f"Wrote {len(accuracy_rows)} accuracy row(s) to {accuracy_path}")
    elif ground_truth_path:
        print(
            "A --ground-truth file was given, but none of its image_name "
            "values matched a processed file - no accuracy_results.csv was written."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare PaddleOCR and Tesseract on the same set of test images."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT_DIR,
                         help="Folder of test images/PDFs, searched recursively (default: benchmarks/test_data).")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR,
                         help="Folder to write comparison_results.csv and raw output into (default: benchmarks/results).")
    parser.add_argument("--engines", default="paddle,tesseract",
                         help="Comma-separated engines to run: paddle, tesseract, or both (default: both).")
    parser.add_argument("--runs", type=int, default=1,
                         help="Times to run OCR on each (image, engine) pair (default: 1). "
                              "Warm-up (see benchmarks/README.md) is separate and never counted here.")
    parser.add_argument("--ground-truth", default=None,
                         help="Optional CSV of image_name,correct_text for CER/WER scoring.")
    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be at least 1")

    engine_names = [name.strip() for name in args.engines.split(",") if name.strip()]
    unknown = [name for name in engine_names if name not in ENGINES]
    if unknown:
        parser.error(f"Unknown engine(s): {', '.join(unknown)}. Valid options: {', '.join(ENGINES)}")

    run_benchmark(args.input, args.output, engine_names, args.runs, args.ground_truth)


if __name__ == "__main__":
    main()
