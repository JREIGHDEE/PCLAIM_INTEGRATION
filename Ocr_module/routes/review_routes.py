"""Logbook upload -> per-row review sessions (see logbook_pipeline.py).

  POST /api/review/upload                 run the full OCR flow on one scan,
                                          create one pending session per row
  POST /api/review/jobs                   same, in the background (review page)
  GET  /api/review/jobs/<job_id>          its progress, then the same result
  GET  /api/review/uploads/<upload_id>    the sessions created by one upload
  GET  /api/review/sessions/<id>          one session with its OCR fields
  PUT  /api/review/sessions/<id>          submit the reviewer's values
                                          ({"values", "defer_manual"} - see
                                          logbook_pipeline.apply_review)
  GET  /api/review/crops/<upload_id>/<f>  a field's cell crop image

A reviewed session becomes a claim through POST /api/claims/generate with
{"session_id": <id>} (routes/claims_routes.py).

Like claims_routes, nothing here logs patient text - only ids and counts.
"""
import logging
import os
import tempfile

from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

import case_session_store
import config
import logbook_pipeline
import review_jobs
from errors import InvalidRequestError, ReviewCheckError, ReviewIncompleteError, SessionNotFoundError
from ocr_engine import extract_tokens_from_array
from philhealth import case_bridge, field_catalog, review_fields
from template_store import load_template_payloads
from utils.uploads import require_file, temp_upload_path, validate_extension

logger = logging.getLogger(__name__)

review_bp = Blueprint("review", __name__, url_prefix="/api/review")


def _with_inputs(field):
    """A field plus what the review screen needs to show its inputs: its
    kind, and its parts - as reviewed, or suggested from the current text."""
    category = field["category"]
    parts = field.get("parts") if field.get("parts_reviewed") else None
    found_blank = field.get("status") == logbook_pipeline.EMPTY
    if parts is None and found_blank and category not in field_catalog.OCR_CLAIM_REQUIRED_CATEGORIES:
        parts = {"empty": True}  # found blank by the computer - start as "empty"
    return {
        **field,
        "kind": review_fields.kind_of(category),
        "parts": parts or review_fields.suggest_parts(category, field.get("value") or field.get("raw_text")
                                                      if field.get("status") != logbook_pipeline.MANUAL
                                                      else field.get("value")),
    }


def _session_view(session):
    ocr_data = session["ocr_data"] or {}
    return {
        "session_id": session["id"],
        "case_id": session["case_id"],
        "upload_id": session["upload_id"],
        "logbook_row": session["logbook_row"],
        "source_document": session["source_document"],
        "review_status": session["review_status"],
        "values": session["values"],
        "image_quality": ocr_data.get("image_quality"),
        "thresholds": ocr_data.get("thresholds") or logbook_pipeline.thresholds(),
        "fields": [_with_inputs(f) for f in ocr_data.get("fields", [])],
    }


def _read_logbook(path, source_document, progress=None):
    """Run the full flow on one saved upload and save one pending session
    per patient row. Returns the upload response payload. Raises
    ValueError (message for the user) if the file can't be read."""
    result = logbook_pipeline.build_review_rows(
        path, extract_tokens_from_array, load_template_payloads(), progress=progress)
    if progress:
        progress(1.0, "Saving the patients")
    session_ids = logbook_pipeline.persist_review_rows(result, source_document)
    logger.info(
        "Logbook upload %s: %d page(s), %d review session(s), IQ-01 %s",
        result["upload_id"], len(result["pages"]), len(session_ids),
        "passed" if result["image_quality"]["passed"] else "flagged",
    )
    return {
        "success": True,
        "upload_id": result["upload_id"],
        "image_quality": result["image_quality"],
        "thresholds": result["thresholds"],
        "pages": result["pages"],
        "sessions": [_session_view(s) for s in case_session_store.list_upload_sessions(result["upload_id"])],
    }


def _uploaded_file():
    file = require_file(request.files, "file")
    extension = validate_extension(file.filename)
    return file, extension, secure_filename(file.filename) or f"upload{extension}"


@review_bp.route("/upload", methods=["POST"])
def upload_logbook():
    """Synchronous: responds when the whole scan has been read."""
    file, extension, source_document = _uploaded_file()
    with temp_upload_path(file, prefix="logbook_review", suffix=extension) as path:
        try:
            with review_jobs.OCR_LOCK:
                payload = _read_logbook(path, source_document)
        except ValueError as exc:
            raise InvalidRequestError(str(exc))
    return jsonify(payload)


@review_bp.route("/jobs", methods=["POST"])
def start_logbook_job():
    """Same as /upload, but answers at once with a job id; poll
    GET /jobs/<id> for progress and, when done, the same payload."""
    file, extension, source_document = _uploaded_file()
    handle, path = tempfile.mkstemp(prefix="logbook_review_", suffix=extension)
    os.close(handle)
    file.save(path)
    job_id = review_jobs.start(lambda progress: _read_logbook(path, source_document, progress), path)
    return jsonify({"success": True, "job_id": job_id}), 202


@review_bp.route("/jobs/<job_id>", methods=["GET"])
def get_logbook_job(job_id):
    job = review_jobs.get(job_id)
    if job is None:
        raise InvalidRequestError("This reading job is unknown or has expired - please upload the scan again.")
    return jsonify({"success": True, "job_id": job_id, **job})


@review_bp.route("/uploads/<upload_id>", methods=["GET"])
def get_upload(upload_id):
    sessions = case_session_store.list_upload_sessions(upload_id)
    if not sessions:
        raise SessionNotFoundError(f"No review sessions found for upload {upload_id}.")
    return jsonify({"success": True, "upload_id": upload_id,
                    "sessions": [_session_view(s) for s in sessions]})


@review_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_review_session(session_id):
    session = case_session_store.get_session(session_id)
    if session is None:
        raise SessionNotFoundError(f"No case session found with id {session_id}.")
    return jsonify({"success": True, **_session_view(session)})


@review_bp.route("/sessions/<int:session_id>", methods=["PUT"])
def submit_review(session_id):
    payload = request.get_json(silent=True) or {}
    submitted = payload.get("values") or {}
    parts = payload.get("parts") or {}
    if not isinstance(submitted, dict) or not isinstance(parts, dict):
        raise InvalidRequestError("Provide 'parts' (category -> inputs) and/or 'values' (category -> text).")

    problems, warnings = review_fields.check(parts)
    if problems:
        raise ReviewCheckError("Some answers need fixing - see the boxes marked in red.", problems, warnings)
    if warnings and not payload.get("confirm_warnings"):
        raise ReviewCheckError("Some answers look unusual. Please confirm they are correct.",
                               warnings=warnings, needs_confirmation=True)

    session = case_session_store.get_session(session_id)
    if session is None:
        raise SessionNotFoundError(f"No case session found with id {session_id}.")

    defer_manual = bool(payload.get("defer_manual"))
    values, ocr_data, missing = logbook_pipeline.apply_review(session["ocr_data"], submitted, defer_manual, parts)
    if missing:
        raise ReviewIncompleteError(
            ("A claim can't be created without these - type them here before sending to the forms: "
             if defer_manual else
             "These fields need manual encoding before the review can be submitted: ")
            + ", ".join(missing)
        )

    case_session_store.mark_session_reviewed(
        session_id, values.get(case_bridge.CASE_NUMBER, "") or session["case_id"],
        values, ocr_data,
    )
    logger.info("Review submitted for case session %s", session_id)
    return jsonify({"success": True, **_session_view(case_session_store.get_session(session_id))})


@review_bp.route("/crops/<upload_id>/<filename>", methods=["GET"])
def get_crop(upload_id, filename):
    folder = os.path.join(config.REVIEW_CROPS_FOLDER, secure_filename(upload_id))
    return send_from_directory(folder, secure_filename(filename), mimetype="image/png")
