"""Test 5 - performance: time per stage and for the whole pipeline, per
logbook entry.

    python -m research_tests.performance [--samples] [--scans 3]

Inputs: the scans in inputs/scans/performance/ (PDF or images); when that
folder is empty, the 10-writer handwriting scans are used.

Every stage is the real function, timed with time.perf_counter() by
wrapping it in this process only (no file is edited):
  image quality check   image_quality.assess_image_quality, per page
  table/row detection   the rest of logbook_pipeline.build_review_rows:
                        template match, ruled lines, rows, cells (the build
                        time minus the timed stages inside it)
  OCR                   PaddleOCR on every cell (ocr_engine)
  correction            the AI second look on unsure cells (its re-reads
                        included) + the Logbook Reader's text fixes
                        (ocr_compare.corrected_value)
  auto-population       case_bridge.draft_patient_and_encounter +
                        form_prefill.build_form_data (Python), then app.js
                        applyFormData in the forms page
  validation            validation-rules.js runValidationRules (in the page)
  PDF generation        pdf-overlay.js buildFilledPdf + save for each of the
                        claim's forms (in the page, pdf-lib); the server's
                        own CSF/CF2 export (philhealth.pdf_export) is timed
                        beside it
Page-level stages are shared out over the entries found on the scan. The
entry's values are what the Logbook Reader would show staff (not typed by
anyone), so this is the pipeline's speed, not a person's.
PaddleOCR is loaded and warmed up first; that load time is reported apart.
"""
import time
import uuid
from pathlib import Path

from research_tests import INPUTS, output_dir
from research_tests.common import excel, stats

TEST_KEY = "performance"
TITLE = "Performance test"
STAGES = [("iq", "Image quality check"), ("detection", "Table/row detection"), ("ocr", "OCR"),
          ("correction", "Correction"), ("autopop", "Auto-population"), ("validation", "Validation"),
          ("pdf", "PDF generation (claim's forms)")]
SCAN_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


class Clock:
    """Accumulated milliseconds per stage, with a guard so the corrector's
    own OCR re-reads count as correction, not OCR."""

    def __init__(self):
        self.ms = {}
        self.inside = None

    def add(self, stage, ms):
        self.ms[stage] = self.ms.get(stage, 0.0) + ms

    def wrap(self, stage, fn):
        def timed(*args, **kwargs):
            if self.inside:                       # called from inside another timed stage
                return fn(*args, **kwargs)
            self.inside = stage
            started = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                self.add(stage, (time.perf_counter() - started) * 1000)
                self.inside = None
        return timed


def find_scans(root, limit):
    folder = root / "scans" / "performance"
    scans = sorted(p for p in folder.glob("*") if p.suffix.lower() in SCAN_TYPES) if folder.is_dir() else []
    source = "scans/performance"
    if not scans:
        from research_tests.common import answer_key
        writers = answer_key.writers(root / "writers.csv") if (root / "writers.csv").is_file() else []
        scans = [root / "scans" / "handwriting" / w["scan"] for w in writers if w["set"] == "main"]
        scans = [p for p in scans if p.is_file()]
        source = "scans/handwriting (no scans in scans/performance)"
    if not scans:
        raise FileNotFoundError(f"No scans in {folder} or in the handwriting scans (or use --samples).")
    return scans[:limit] if limit else scans, source


def run(progress, samples=False, scans=3):
    root = INPUTS / "samples" if samples else INPUTS
    paths, source = find_scans(root, scans)

    import cv2
    import numpy as np
    import logbook_pipeline
    import ocr_compare
    import paddle_assist
    from ocr_engine import extract_tokens_from_array, get_ocr_engine, read_many, read_versions_many
    from philhealth import case_bridge, form_prefill, pdf_export
    from template_store import load_template_payloads
    from research_tests import guard
    from research_tests.common.forms_page import FormsPage
    from research_tests.common.specs import machine_specs

    progress(0.02, "Loading PaddleOCR")
    started = time.perf_counter()
    get_ocr_engine()
    blank = np.full((60, 200, 3), 255, np.uint8)
    cv2.putText(blank, "WARM UP", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    extract_tokens_from_array(blank)
    model_load_ms = (time.perf_counter() - started) * 1000
    model, model_note = guard.research_model()
    templates = load_template_payloads()

    entries, pages_done = [], []
    original_iq = logbook_pipeline.assess_image_quality
    with FormsPage() as page:
        for n, path in enumerate(paths):
            base = 0.05 + 0.9 * n / len(paths)
            progress(base, f"{path.name}: reading the scan")
            clock = Clock()
            logbook_pipeline.assess_image_quality = clock.wrap("iq", original_iq)
            try:
                ocr_fn = clock.wrap("ocr", extract_tokens_from_array)
                batch_fn = clock.wrap("ocr", read_many)
                corrector = paddle_assist.make_corrector(extract_tokens_from_array, model=model,
                                                         batch_reader=read_versions_many)
                if corrector:
                    corrector = clock.wrap("correction", corrector)
                t0 = time.perf_counter()
                result = logbook_pipeline.build_review_rows(str(path), ocr_fn, templates, upload_id=uuid.uuid4().hex,
                                                            corrector=corrector, batch_ocr_fn=batch_fn)
                build_ms = (time.perf_counter() - t0) * 1000
            finally:
                logbook_pipeline.assess_image_quality = original_iq
            rows = result["rows"]
            second_look_ms = clock.ms.get("correction", 0.0)          # inside build_review_rows
            t0 = time.perf_counter()
            for row in rows:                                            # the Logbook Reader's text fixes
                for f in row["fields"]:
                    f["value"] = ocr_compare.corrected_value(f["category"], f.get("value"))
            fixes_ms = (time.perf_counter() - t0) * 1000
            page_stage = {"iq": clock.ms.get("iq", 0.0), "ocr": clock.ms.get("ocr", 0.0),
                          "correction": second_look_ms + fixes_ms}
            page_stage["detection"] = max(0.0, build_ms - page_stage["iq"] - page_stage["ocr"] - second_look_ms)
            pages_done.append({"scan": path.name, "pages": len(result["pages"]), "rows": len(rows),
                               "build_ms": build_ms, **page_stage})
            share = max(1, len(rows))
            for r_index, row in enumerate(rows):
                progress(base + 0.9 / len(paths) * (r_index + 1) / share, f"{path.name}: entry {r_index + 1} of {len(rows)}")
                values = logbook_pipeline.session_values(row["fields"])
                t0 = time.perf_counter()
                patient, encounter, claim, _w = case_bridge.draft_patient_and_encounter(values)
                built = form_prefill.build_form_data({"patient": patient, "encounter": encounter, "claim": claim})
                python_ms = (time.perf_counter() - t0) * 1000
                body = {"data": built["data"], "fields": built["fields"], "ocr_reference": built["ocr_reference"]}
                if not (body["data"].get("patientLastName") or body["data"].get("dateAdmitted")):
                    continue                          # nothing the page can be waited on for
                try:
                    page.open_claim(body)
                except Exception:
                    continue
                apply_ms = page.page.evaluate("""data => { const t = performance.now(); applyFormData(data);
                                                           return performance.now() - t; }""", body["data"])
                validation_ms = page.validate()["ms"]
                forms = page.claim_forms()
                pdf_ms = sum(page.build_pdf(form)[1] for form in forms)
                server_pdf = []
                for form in ("csf", "cf2"):
                    t0 = time.perf_counter()
                    try:
                        pdf_export.export_claim_pdf(form, patient, encounter, claim)
                        server_pdf.append((time.perf_counter() - t0) * 1000)
                    except Exception:
                        pass
                e = {"scan": path.name, "row": row["row"] + 1, "forms": ", ".join(forms),
                     "iq": page_stage["iq"] / share, "detection": page_stage["detection"] / share,
                     "ocr": page_stage["ocr"] / share, "correction": page_stage["correction"] / share,
                     "autopop": python_ms + apply_ms, "autopop_python": python_ms, "autopop_page": apply_ms,
                     "validation": validation_ms, "pdf": pdf_ms,
                     "server_pdf": sum(server_pdf) if server_pdf else None}
                e["total"] = sum(e[k] for k, _ in STAGES)
                entries.append(e)
        browser = page.browser_version

    if not entries:
        raise RuntimeError("No entries were found on the scans - check the logbook setup matches them.")
    progress(0.97, "Summarising")
    summary_rows = []
    for key, label in STAGES + [("total", "Full pipeline (per entry)")]:
        values = [e[key] for e in entries]
        summary_rows.append([label, len(values), stats.mean(values), stats.low(values), stats.high(values),
                             stats.value_range(values)])
    extra_rows = [["Auto-population: Python (draft + build_form_data)", len(entries),
                   stats.mean(e["autopop_python"] for e in entries), stats.low(e["autopop_python"] for e in entries),
                   stats.high(e["autopop_python"] for e in entries), ""],
                  ["Auto-population: forms page (applyFormData)", len(entries),
                   stats.mean(e["autopop_page"] for e in entries), stats.low(e["autopop_page"] for e in entries),
                   stats.high(e["autopop_page"] for e in entries), ""],
                  ["Server CSF + CF2 export (philhealth.pdf_export)", len(entries),
                   stats.mean(e["server_pdf"] for e in entries), stats.low(e["server_pdf"] for e in entries),
                   stats.high(e["server_pdf"] for e in entries), ""]]
    page_rows = [[p["scan"], p["pages"], p["rows"], round(p["build_ms"] / 1000, 2), round(p["iq"], 1),
                  round(p["detection"], 1), round(p["ocr"], 1), round(p["correction"], 1)] for p in pages_done]
    specs = machine_specs([["Microsoft Edge (forms page)", browser],
                           ["Validation engine", f"PClaimAssist/js/validation-rules.js, run in headless {browser} "
                                                 "(the real forms page, offline)"],
                           ["PDF export", f"PClaimAssist/js/pdf/pdf-overlay.js buildFilledPdf with pdf-lib 1.17.1 "
                                          f"(research_tests/vendor), run in headless {browser}; the server's CSF/CF2 "
                                          "export (philhealth.pdf_export) in Python"],
                           ["PaddleOCR load + warm-up", f"{model_load_ms / 1000:.1f} s (not counted per entry)"],
                           ["AI correction", f"on - {model_note}" if paddle_assist.config.AI_CORRECTION_ENABLED
                            else "off (AI_CORRECTION_ENABLED=false)"],
                           ["Scans", f"{len(paths)} from {source}"]])
    notes = ["Milliseconds per logbook entry, timed with time.perf_counter() around the real functions (wrapped in "
             "the test process only). Page-level stages (image quality, detection, OCR, correction) are the scan's "
             "time shared out over the entries found on it.",
             "Validation and PDF generation are timed inside the forms page with performance.now() (the page's own "
             "JavaScript in Microsoft Edge, offline).",
             "Full pipeline = the seven stages added up, per entry; the PaddleOCR model load is reported apart (once "
             "per start of the system)."]
    if samples:
        notes.append("COMPUTER-DRAWN SAMPLE SCANS (make_samples.py).")
    sheets = [
        {"name": "5a Performance per stage", "title": "Table - Processing time per stage, per logbook entry (ms)",
         "headers": ["Stage", "Entries", "Mean (ms)", "Min (ms)", "Max (ms)", "Range (ms)"],
         "rows": summary_rows + extra_rows, "notes": notes},
        {"name": "5b Machine specs", "title": "Table - Test machine", "headers": ["Item", "Value"], "rows": specs},
    ]
    raw = {"name": "Raw data",
           "headers": ["Scan", "Row", "Forms"] + [label + " (ms)" for _, label in STAGES]
                      + ["Full pipeline (ms)", "Auto-population Python (ms)", "Auto-population page (ms)",
                         "Server CSF+CF2 export (ms)"],
           "rows": [[e["scan"], e["row"], e["forms"]] + [round(e[k], 2) for k, _ in STAGES]
                    + [round(e["total"], 2), round(e["autopop_python"], 2), round(e["autopop_page"], 2),
                       None if e["server_pdf"] is None else round(e["server_pdf"], 2)] for e in entries]}
    per_scan = {"name": "Per scan", "headers": ["Scan", "Pages", "Entries", "build_review_rows (s)",
                                                "Image quality (ms)", "Detection (ms)", "OCR (ms)", "Correction (ms)"],
                "rows": page_rows}
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "performance_results.xlsx", [raw, per_scan] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    total = summary_rows[-1]
    return {"outputs": [path], "headline": [["Entries", len(entries)], ["Full pipeline mean (ms)", total[2]],
                                            ["Range (ms)", total[5]]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample scans")
    parser.add_argument("--scans", type=int, default=3, help="how many scans to time (default 3, 0 = all)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
