"""The OCR comparison page (testing only, administrators): PaddleOCR vs
Tesseract on a logbook scan, with a ground truth typed by the tester
(ocr_compare.py, ocr_compare_store.py).

  GET  /ocr-compare                          the page (inside ocr-compare.html)
  GET  /api/ocr-compare/status               Tesseract installed? AI on? rows saved
  POST /api/ocr-compare/jobs                 read a scan with both engines (file);
                                             answers with a job id - the same job
                                             again for a file already waiting/reading
  GET  /api/ocr-compare/jobs/<job_id>        its progress, how many readings are
                                             ahead of it, then {"run_id"}
  POST /api/ocr-compare/jobs/<job_id>/cancel stop it (waiting: never starts; reading:
                                             stops at the next cell)

Readings take turns with the Logbook Reader's (review_jobs.OCR_LOCK: the
PaddleOCR model reads one thing at a time), so a comparison waiting or
reading holds up a logbook upload - cancel one that is not needed.
  GET  /api/ocr-compare/runs                 earlier runs, newest first
  GET  /api/ocr-compare/runs/<run_id>        one run, with its ground truth
  PUT  /api/ocr-compare/runs/<run_id>/truth  keep the ground truth typed so far
                                             ({"truth": {row: [text...]}, "cuts": {row: [cut...]},
                                               "checked": [row...]}; cut = correct/cut_off/wrong)
  POST /api/ocr-compare/runs/<run_id>/save   write rows to the workbook ({"rows": [row...]})
  GET  /api/ocr-compare/summary              the workbook's summary
  GET  /api/ocr-compare/results.xlsx         the workbook
  POST /api/ocr-compare/clear                empty the workbook

Cell and row pictures are the Logbook Reader's (GET /api/review/crops/...).
Nothing here writes patients, claims or case_sessions, or teaches the AI.
"""
import hashlib
import logging
import os
import tempfile
import threading

from flask import Blueprint, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

import auth
import config
import ocr_compare
import ocr_compare_store
import paddle_assist
import review_jobs
from errors import InvalidRequestError
from ocr_engine import extract_tokens_from_array, read_many, read_versions_many
from template_store import load_template_payloads
from utils.uploads import require_file, validate_extension

logger = logging.getLogger(__name__)

compare_bp = Blueprint("ocr_compare", __name__)
admin_only = auth.role_required("admin")

# {file fingerprint: job id} for jobs waiting or reading, so uploading the
# same scan again (e.g. after a reload) follows that job instead of queuing
# a second one; and the jobs asked to stop.
_active, _cancelled = {}, set()
_active_lock = threading.Lock()


class _Cancelled(ValueError):
    """Raised inside a cancelled job; review_jobs reports it as failed."""


def _run_or_404(run_id):
    try:
        run = ocr_compare.load_run(run_id)
    except ValueError as exc:
        raise InvalidRequestError(str(exc))
    if run is None:
        raise InvalidRequestError("This comparison run is not on this computer any more.")
    return run


@compare_bp.route("/ocr-compare")
def compare_page():
    # The page asks who is signed in and explains if they can't use it.
    return render_template("ocr_compare.html", variants=ocr_compare.VARIANT_LABELS, cuts=ocr_compare.CUTS)


@compare_bp.route("/api/ocr-compare/status")
@admin_only
def compare_status():
    return jsonify({"success": True, "tesseract_error": ocr_compare.tesseract_available(),
                    "tesseract_psm": ocr_compare.TESSERACT_PSM, "ai_correction": config.AI_CORRECTION_ENABLED,
                    "templates": len(load_template_payloads()), **ocr_compare_store.summary()})


@compare_bp.route("/api/ocr-compare/jobs", methods=["POST"])
@admin_only
def start_compare_job():
    file = require_file(request.files, "file")
    extension = validate_extension(file.filename)
    source = secure_filename(file.filename) or f"scan{extension}"
    handle, path = tempfile.mkstemp(prefix="ocr_compare_", suffix=extension)
    os.close(handle)
    file.save(path)
    with open(path, "rb") as fh:
        fingerprint = hashlib.sha256(fh.read()).hexdigest()
    with _active_lock:
        running = _active.get(fingerprint)
        job = review_jobs.get(running) if running else None
        if job and job["state"] in ("waiting", "running") and running not in _cancelled:
            os.remove(path)
            return jsonify({"success": True, "job_id": running, "already": True}), 202
    me = {}

    def check(progress):
        def guarded(fraction, message):
            if me.get("id") in _cancelled:
                raise _Cancelled("Stopped - you cancelled this reading.")
            progress(fraction, message)
        return guarded

    def work(progress):
        try:
            return read(check(progress))
        finally:
            with _active_lock:
                if _active.get(fingerprint) == me.get("id"):
                    del _active[fingerprint]
                _cancelled.discard(me.get("id"))

    def read(progress):
        progress(0.0, "Starting")
        run = ocr_compare.run_comparison(
            path, source, load_template_payloads(),
            paddle_fn=extract_tokens_from_array, paddle_batch_fn=read_many,
            paddle_corrector=paddle_assist.make_corrector(extract_tokens_from_array, batch_reader=read_versions_many),
            tesseract_fn=ocr_compare.tesseract_tokens,
            tesseract_corrector=paddle_assist.make_corrector(ocr_compare.tesseract_tokens),
            progress=progress)
        if not run["rows"]:
            problems = [p["error"] for p in run["pages"] if p.get("error")]
            raise ValueError("No patient rows were found on this scan. " + (problems[0] if problems else ""))
        return {"run_id": run["run_id"], "rows": len(run["rows"])}

    with _active_lock:
        job_id = review_jobs.start(work, path)
        me["id"] = job_id
        _active[fingerprint] = job_id
    return jsonify({"success": True, "job_id": job_id}), 202


@compare_bp.route("/api/ocr-compare/jobs/<job_id>")
@admin_only
def get_compare_job(job_id):
    job = review_jobs.get(job_id)
    if job is None:
        raise InvalidRequestError("This reading job is unknown or has expired - please upload the scan again.")
    return jsonify({"success": True, "job_id": job_id, "ahead": review_jobs.ahead_of(job_id),
                    "seconds": review_jobs.seconds_since_start(job_id), "cancelling": job_id in _cancelled, **job})


@compare_bp.route("/api/ocr-compare/jobs/<job_id>/cancel", methods=["POST"])
@admin_only
def cancel_compare_job(job_id):
    job = review_jobs.get(job_id)
    if job is None or job["state"] in ("done", "failed"):
        return jsonify({"success": True, "state": job["state"] if job else "gone"})
    _cancelled.add(job_id)
    logger.info("OCR comparison job %s cancelled by %s", job_id, (auth.current_user() or {}).get("email", "unknown"))
    return jsonify({"success": True, "state": "cancelling"})


@compare_bp.route("/api/ocr-compare/runs")
@admin_only
def list_compare_runs():
    return jsonify({"success": True, "runs": ocr_compare.list_runs()})


@compare_bp.route("/api/ocr-compare/runs/<run_id>")
@admin_only
def get_compare_run(run_id):
    return jsonify({"success": True, "run": _run_or_404(run_id)})


@compare_bp.route("/api/ocr-compare/runs/<run_id>/truth", methods=["PUT"])
@admin_only
def save_compare_truth(run_id):
    data = request.get_json(silent=True) or {}
    run = ocr_compare.set_truth(_run_or_404(run_id), data.get("truth"), data.get("checked"), data.get("cuts"))
    ocr_compare.save_run(run)
    return jsonify({"success": True, "checked": run["checked"]})


@compare_bp.route("/api/ocr-compare/runs/<run_id>/save", methods=["POST"])
@admin_only
def save_compare_rows(run_id):
    data = request.get_json(silent=True) or {}
    run = _run_or_404(run_id)
    if "truth" in data or "checked" in data or "cuts" in data:
        ocr_compare.set_truth(run, data.get("truth"), data.get("checked"), data.get("cuts"))
    keys = [k for k in data.get("rows") or [] if isinstance(k, str)]
    items = ocr_compare.scored_rows(run, keys)
    if not items:
        raise InvalidRequestError("Tick at least one row as checked before saving.")
    result = ocr_compare_store.save_rows(items)
    run["saved"] = list(dict.fromkeys(run.get("saved", []) + [i["row_key"] for i in items]))
    ocr_compare.save_run(run)
    return jsonify({"success": True, "saved_rows": sorted({i["row_key"] for i in items}),
                    "run_saved": run["saved"], **result})


@compare_bp.route("/api/ocr-compare/summary")
@admin_only
def compare_summary():
    return jsonify({"success": True, **ocr_compare_store.summary()})


@compare_bp.route("/api/ocr-compare/results.xlsx")
@admin_only
def download_compare_workbook():
    path = config.OCR_COMPARE_WORKBOOK
    if not path.exists():
        return jsonify({"success": False, "error": "No rows have been saved yet."}), 404
    return send_file(path, as_attachment=True, download_name=path.name,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@compare_bp.route("/api/ocr-compare/clear", methods=["POST"])
@admin_only
def clear_compare_workbook():
    logger.info("OCR comparison workbook cleared by %s", (auth.current_user() or {}).get("email", "unknown"))
    return jsonify({"success": True, **ocr_compare_store.clear()})
