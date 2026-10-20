"""
Guided logbook setup (logbook_setup.py) - administrators only.

  GET  /logbook-setup                          -> the setup page
  POST /api/logbook-setup/read      file       -> columns, names and rows found
  GET  /api/logbook-setup/<id>/<picture>       -> a page's preview picture
  POST /api/logbook-setup/save      {setup_id, pages, replace_old}
  GET  /api/logbook-setup/current              -> the setups in use
"""
import logging

from flask import Blueprint, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

import auth
import logbook_layout
import logbook_setup
import review_jobs
from errors import InvalidRequestError
from ocr_engine import extract_tokens_from_array
from utils.uploads import require_file, temp_upload_path, validate_extension

logger = logging.getLogger(__name__)

setup_bp = Blueprint("logbook_setup", __name__)


@setup_bp.route("/logbook-setup")
def setup_page():
    # The page asks who is signed in and explains if they can't use it.
    return render_template(
        "logbook_setup.html",
        sides={side: [{"value": c, "label": logbook_layout.PLAIN_NAMES[c]} for c in columns]
               for side, columns in logbook_layout.SIDE_COLUMNS.items()},
        required=["NAME", "BDAY", "DATE & TIME OF ADMISSION"],
    )


@setup_bp.route("/api/logbook-setup/read", methods=["POST"])
@auth.role_required("admin")
def read_scan():
    file = require_file(request.files, "file")
    extension = validate_extension(file.filename)
    logbook_setup.clear_old_previews()
    with temp_upload_path(file, prefix="logbook_setup", suffix=extension) as path:
        try:
            # One OCR at a time: PaddleOCR is shared with the logbook reader.
            with review_jobs.OCR_LOCK:
                result = logbook_setup.read_scan(path, extract_tokens_from_array)
        except ValueError as exc:
            raise InvalidRequestError(str(exc))
    return jsonify({"success": True, **result})


@setup_bp.route("/api/logbook-setup/<setup_id>/<picture>")
@auth.role_required("admin")
def setup_picture(setup_id, picture):
    path = logbook_setup.preview_path(setup_id, 0).parent
    return send_from_directory(path, secure_filename(picture), mimetype="image/jpeg")


@setup_bp.route("/api/logbook-setup/save", methods=["POST"])
@auth.role_required("admin")
def save_setup():
    data = request.get_json(silent=True) or {}
    result = logbook_setup.save_setup(
        data.get("setup_id") or "",
        data.get("pages") or [],
        replace_old=data.get("replace_old", True) is not False,
        saved_by=auth.current_user()["email"],
    )
    return jsonify({"success": True, **result})


@setup_bp.route("/api/logbook-setup/current")
@auth.role_required("admin")
def current_setups():
    return jsonify({"success": True, "setups": logbook_setup.current_setups()})
