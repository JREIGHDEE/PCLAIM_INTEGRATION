"""
OCR extraction endpoints (/ocr, /api/ocr) and the reviewed-result "case
session" storage/export that follows OCR review in the calibration UI
(/save_reviewed_result, /export_case_session).

Route bodies are the original app.py logic, unchanged, except:
  - the repeated "no file uploaded" check now goes through utils.uploads.require_file
  - /ocr's error responses now use proper HTTP status codes (previously always 200)
  - a new /api/ocr alias is added, sharing the exact same implementation
"""
import json
import logging
import os
import time
from io import BytesIO

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

import config
from errors import InvalidRequestError, OCRProcessingError
from ocr_engine import extract_pdf_text, extract_text
from template_store import get_case_session_path, update_template_from_session
from utils.uploads import require_file

logger = logging.getLogger(__name__)

ocr_bp = Blueprint("ocr", __name__)


def _perform_ocr():
    """Core OCR handling shared by /ocr and /api/ocr."""
    file = require_file(request.files, "image")
    category = request.form.get("category", "").strip()

    filename = secure_filename(file.filename)
    filepath = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    extension = os.path.splitext(filename)[1].lower()

    if extension == ".pdf":
        tokens = extract_pdf_text(filepath)
    else:
        tokens = extract_text(filepath)

    enriched_tokens = [
        {**token, "category": category}
        for token in tokens
    ]

    raw_text = "\n".join(token["text"] for token in enriched_tokens)

    template_filename = request.form.get("template_filename", "").strip()
    template_payload_raw = request.form.get("template_payload", "")
    if template_filename and template_payload_raw:
        try:
            template_payload = json.loads(template_payload_raw)
        except Exception:
            template_payload = None
        if isinstance(template_payload, dict):
            learned_context = {
                "category": category,
                "gridLines": template_payload.get("gridLines", []),
                "rowTemplate": template_payload.get("rowTemplate"),
                "cropBoxPercent": template_payload.get("cropBoxPercent"),
                "imageWidth": template_payload.get("imageWidth"),
                "imageHeight": template_payload.get("imageHeight"),
                "source": "ocr"
            }
            update_template_from_session(template_filename, template_payload, learned_context)

    logger.info(
        "OCR extracted %d token(s) from '%s' (category=%s)",
        len(enriched_tokens), filename, category or "-",
    )

    return jsonify({
        "success": True,
        "raw_text": raw_text,
        "category": category,
        "tokens": enriched_tokens
    })


@ocr_bp.route("/ocr", methods=["POST"])
def run_ocr():
    try:
        return _perform_ocr()
    except InvalidRequestError:
        raise
    except Exception as e:
        logger.exception("OCR request failed")
        raise OCRProcessingError(str(e)) from e


@ocr_bp.route("/api/ocr", methods=["POST"])
def run_ocr_api():
    """REST-style alias of /ocr for new clients (e.g. PClaimAssist). Identical behavior."""
    return run_ocr()


@ocr_bp.route("/save_reviewed_result", methods=["POST"])
def save_reviewed_result():
    case_id = request.form.get("case_id", "").strip()
    if not case_id:
        return jsonify({
            "success": False,
            "error": "Please enter a case ID before saving"
        }), 400

    category = request.form.get("category", "").strip()
    reviewed_text = request.form.get("reviewed_text", "")
    review_values_raw = request.form.get("review_values", "")
    review_values = {}

    if review_values_raw:
        try:
            review_values = json.loads(review_values_raw)
            if not isinstance(review_values, dict):
                raise ValueError("review_values must be an object")
        except Exception:
            return jsonify({
                "success": False,
                "error": "Invalid review_values payload"
            }), 400

    if not review_values:
        if not reviewed_text:
            return jsonify({
                "success": False,
                "error": "Please provide reviewed text before saving"
            }), 400
        # Allow arbitrary category names here (they are saved to the case session values).
        # Previously we rejected categories not present in TRAINING_CATEGORIES/CATEGORY_FOLDERS;
        # that made saving edited results fail when users used custom category labels.

    case_name = request.form.get("case_name", "").strip()
    session_path = get_case_session_path(case_id)

    session_data = {}
    if os.path.exists(session_path):
        with open(session_path, "r", encoding="utf-8") as handle:
            try:
                session_data = json.load(handle)
            except Exception:
                session_data = {}

    if not isinstance(session_data, dict):
        session_data = {}

    session_data["case_id"] = case_id
    session_data["case_name"] = case_name or session_data.get("case_name", "")
    session_data["updated_at"] = int(time.time() * 1000)
    # Replace stored values with only the reviewed/edited values provided in this request.
    # This prevents raw OCR tokens from being kept in the session when the user saved reviewed edits.
    new_values = {}
    if review_values:
        for key, value in review_values.items():
            try:
                k = str(key).strip()
            except Exception:
                continue
            new_values[k] = str(value or "")

    # If the user provided a full reviewed/edited text (and no structured per-category values),
    # store it under the chosen category or under a fallback internal key when no category
    # selected. Skip this when review_values was provided: reviewed_text is the concatenation of
    # every row and would clobber a single category's reviewed value with all the other rows too.
    if reviewed_text and not review_values:
        if category:
            new_values[category] = reviewed_text
        else:
            new_values["_reviewed_text"] = reviewed_text

    session_data["values"] = new_values

    with open(session_path, "w", encoding="utf-8") as handle:
        json.dump(session_data, handle, indent=2)

    return jsonify({
        "success": True,
        "saved_path": session_path
    })


@ocr_bp.route("/export_case_session")
def export_case_session():
    case_id = request.args.get("case_id", "").strip()
    if not case_id:
        return jsonify({
            "success": False,
            "error": "Please enter a case ID before exporting"
        }), 400

    session_path = get_case_session_path(case_id)
    if not os.path.exists(session_path):
        return jsonify({
            "success": False,
            "error": "No saved session found for that case ID"
        }), 404

    with open(session_path, "r", encoding="utf-8") as handle:
        session_data = json.load(handle)

    values = session_data.get("values", {}) or {}

    # Build export columns from the saved session values only (reviewed/edited fields).
    # This ensures raw OCR tokens that were not explicitly saved by the user are not exported.
    row = {
        "Case ID": session_data.get("case_id", case_id),
        "Case Name": session_data.get("case_name", "")
    }

    # Add all saved value keys (sorted for determinism)
    for key in sorted(values.keys()):
        # Skip empty internal placeholders
        if key in ("", None):
            continue
        row[str(key)] = values.get(key, "")

    df = pd.DataFrame([row])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"{secure_filename(case_id)}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
