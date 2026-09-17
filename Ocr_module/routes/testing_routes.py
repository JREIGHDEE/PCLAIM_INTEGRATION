"""
OCR engine testing endpoints - the "compile both OCRs for testing" workflow.

The calibration UI already lets a user OCR a selected row's cells with one
engine at a time (see /ocr, /api/ocr in ocr_routes.py). The testing panel in
templates/index.html calls /ocr twice per cell (engine=paddle, then
engine=tesseract) client-side and shows both outputs side by side - nothing
new is needed on the OCR-running side for that.

What's new here is only the "save to Excel" half: a single running workbook
that every save appends rows to, so results keep accumulating across row
navigation, PDF page navigation, and new file uploads within the same
session, instead of a fresh file each time (see ocr_testing_store.py).
"""
import logging

from flask import Blueprint, jsonify, request, send_file

import ocr_testing_store
from errors import InvalidRequestError

logger = logging.getLogger(__name__)

testing_bp = Blueprint("testing", __name__, url_prefix="/api/testing")


def _page_side(pdf_page):
    """Odd pages are the left side of a spread, even pages the right side -
    same convention as the page_parity computation in batch_processor.py.
    Derived server-side so it's authoritative regardless of what (if
    anything) the client sends.
    """
    try:
        page_num = int(pdf_page)
    except (TypeError, ValueError):
        return ""
    return "left" if page_num % 2 == 1 else "right"


def _clean_row(raw):
    if not isinstance(raw, dict):
        raise InvalidRequestError("Each item in 'rows' must be an object")
    field = str(raw.get("field", "")).strip()
    if not field:
        raise InvalidRequestError("Each row needs a non-empty 'field'")
    pdf_page = raw.get("pdf_page", "")
    best_engine = str(raw.get("best_engine", "")).strip().lower()
    if best_engine not in ("paddle", "tesseract", "neither"):
        best_engine = ""
    return {
        "spread_id": str(raw.get("spread_id", "")).strip(),
        "source_file": str(raw.get("source_file", "")).strip(),
        "pdf_page": pdf_page,
        "side": _page_side(pdf_page),
        "patient_id": str(raw.get("patient_id", "")).strip(),
        "field": field,
        "ground_truth": str(raw.get("ground_truth", "")).strip(),
        "paddle_output": str(raw.get("paddle_output", "")),
        "paddle_confidence": raw.get("paddle_confidence", ""),
        "tesseract_output": str(raw.get("tesseract_output", "")),
        "tesseract_confidence": raw.get("tesseract_confidence", ""),
        "best_engine": best_engine,
    }


@testing_bp.route("/rows", methods=["POST"])
def append_testing_rows():
    payload = request.get_json(silent=True) or {}
    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise InvalidRequestError("Provide a non-empty 'rows' list")

    rows = [_clean_row(item) for item in raw_rows]
    result = ocr_testing_store.append_rows(rows)

    return jsonify({
        "success": True,
        "added": result["added"],
        "total_rows": result["total_rows"],
    })


@testing_bp.route("/clear", methods=["POST"])
def clear_testing_rows():
    result = ocr_testing_store.clear_rows()
    return jsonify({
        "success": True,
        "total_rows": result["total_rows"],
    })


@testing_bp.route("/summary")
def testing_summary():
    return jsonify({
        "success": True,
        "total_rows": ocr_testing_store.count_rows(),
        "path": str(ocr_testing_store.get_workbook_path()),
    })


@testing_bp.route("/download")
def download_testing_workbook():
    path = ocr_testing_store.get_workbook_path()
    if not path.exists():
        return jsonify({
            "success": False,
            "error": "No OCR test results have been saved yet."
        }), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=path.name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
