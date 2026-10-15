"""Teaching the offline AI from the PhilHealth forms.

  POST /api/learning/form-entries   {"values": {form key: text, ...}}

Called by PClaimAssist (js/entry-learning.js) when a form is exported as
PDF. The patient name, address and diagnosis values are counted in the
ocr_known_entries table (migration 007), so the offline AI
(paddle_assist.py) learns which entries are common and can suggest them
when PaddleOCR misreads them in a logbook scan. Only those text fields are
used; everything else in the payload is ignored.
"""
import logging

from flask import Blueprint, jsonify, request

import auth
import paddle_assist
from errors import InvalidRequestError
from philhealth import field_catalog

logger = logging.getLogger(__name__)

learning_bp = Blueprint("learning", __name__, url_prefix="/api/learning")

# The form keys that feed the vocabulary (name, address, diagnoses).
_LEARNED_KEYS = {key for category in ("NAME", "ADDRESS", "ADMITTING DIAGNOSIS", "FINAL DIAGNOSIS")
                 for key in field_catalog.OCR_CATEGORY_KEYS.get(category, ())}
_MAX_VALUE = 255


@learning_bp.route("/form-entries", methods=["POST"])
@auth.login_required
def record_form_entries():
    values = (request.get_json(silent=True) or {}).get("values")
    if not isinstance(values, dict):
        raise InvalidRequestError("Provide 'values' (form key -> text).")
    kept = {key: value.strip() for key, value in values.items()
            if key in _LEARNED_KEYS and isinstance(value, str) and 0 < len(value.strip()) <= _MAX_VALUE}
    recorded = paddle_assist.record_form(kept)
    logger.info("Form entries recorded for the offline AI: %d", recorded)
    return jsonify({"success": True, "recorded": recorded})
