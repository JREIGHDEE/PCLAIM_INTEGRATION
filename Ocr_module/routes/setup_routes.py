"""
Guided logbook setup (logbook_setup.py).

  GET  /logbook-setup                          -> the setup page; with
                                                  ?check=<id>, the "Check the
                                                  columns" step of reading a scan
  POST /api/logbook-setup/read      file [, tilt] -> columns, names and rows found
                                                  (tilt: degrees to turn the
                                                  scan first - the tilt test)
  POST /api/logbook-setup/first-page file      -> its first page as a JPEG
  GET  /api/logbook-setup/<id>                 -> the same again (reopening a check)
  GET  /api/logbook-setup/<id>/<picture>       -> a page's preview picture
  POST /api/logbook-setup/save      {setup_id, pages, replace_old}   (admin)
  GET  /api/logbook-setup/current              -> the setups in use  (admin)

Every scan read by the Logbook Reader has its columns found and checked
here first, so finding and checking need only a signed-in user. Saving a
setup for every later scan stays with the administrator. Reading the
checked scan: POST /api/review/jobs/checked (routes/review_routes.py).
"""
import logging
import math
import re

from flask import Blueprint, Response, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

import auth
import logbook_layout
import logbook_pipeline
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
        check_id=request.args.get("check") or None,
        sides={side: [{"value": c, "label": logbook_layout.PLAIN_NAMES[c]} for c in columns]
               for side, columns in logbook_layout.CHOICE_COLUMNS.items()},
        required=["NAME", "BDAY", "DATE & TIME OF ADMISSION"],
    )


def _tilt(text):
    """The tilt test's angle in degrees (0 when not given)."""
    if not text:
        return 0.0
    try:
        degrees = float(text)
    except ValueError:
        raise InvalidRequestError("The tilt must be a number of degrees.")
    if not math.isfinite(degrees) or abs(degrees) > logbook_pipeline.TILT_MAX_DEGREES:
        raise InvalidRequestError(f"The tilt must be between -{logbook_pipeline.TILT_MAX_DEGREES} "
                                  f"and {logbook_pipeline.TILT_MAX_DEGREES} degrees.")
    return degrees


@setup_bp.route("/api/logbook-setup/read", methods=["POST"])
@auth.login_required
def read_scan():
    file = require_file(request.files, "file")
    extension = validate_extension(file.filename)
    source_document = secure_filename(file.filename) or f"upload{extension}"
    logbook_setup.clear_old_previews()
    with temp_upload_path(file, prefix="logbook_setup", suffix=extension) as path:
        try:
            # One OCR at a time: PaddleOCR is shared with the logbook reader.
            with review_jobs.OCR_LOCK:
                result = logbook_setup.read_scan(path, extract_tokens_from_array, source_document,
                                                 use_saved=request.form.get("use_saved") == "1",
                                                 tilt=_tilt(request.form.get("tilt")))
        except ValueError as exc:
            raise InvalidRequestError(str(exc))
    return jsonify({"success": True, **result})


@setup_bp.route("/api/logbook-setup/first-page", methods=["POST"])
@auth.login_required
def first_page():
    """The chosen scan's first page as a picture, for the tilt test's
    preview (a PDF cannot be shown by the browser as a picture)."""
    file = require_file(request.files, "file")
    extension = validate_extension(file.filename)
    with temp_upload_path(file, prefix="logbook_first_page", suffix=extension) as path:
        try:
            picture = logbook_pipeline.first_page_picture(path)
        except (ValueError, RuntimeError) as exc:
            raise InvalidRequestError(str(exc) or "The scan could not be opened.")
    return Response(picture, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


@setup_bp.route("/api/logbook-setup/<setup_id>")
@auth.login_required
def get_setup(setup_id):
    return jsonify({"success": True, **logbook_setup.get_setup(setup_id)})


@setup_bp.route("/api/logbook-setup/<setup_id>/<picture>")
@auth.login_required
def setup_picture(setup_id, picture):
    path = logbook_setup.preview_path(setup_id, 0).parent
    # Only the preview pictures: the scan itself is kept in the same folder.
    if not re.fullmatch(r"page\d+\.jpg", picture):
        raise InvalidRequestError("Unknown picture.")
    return send_from_directory(path, picture, mimetype="image/jpeg")


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
