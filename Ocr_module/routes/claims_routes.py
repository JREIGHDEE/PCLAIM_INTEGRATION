"""PhilHealth claim generation/review/export endpoints.

Bridges a reviewed OCR case_sessions row into patients/encounters/claims
(claims_store.py), maps/validates the result onto the CF2/CSF field
vocabulary (philhealth/mapping_service.py), and exports a filled PDF
(philhealth/pdf_export.py) once required fields are present. See
philhealth/__init__.py for the overall pipeline.

No patient/member name, PIN, or other PII is ever logged or put in a URL -
every route here is addressed only by an opaque integer claim id.
"""
import io
import logging

from flask import Blueprint, jsonify, request, send_file

import claims_store
from errors import ClaimIncompleteError, InvalidRequestError
from philhealth import mapping_service, pdf_export

logger = logging.getLogger(__name__)

claims_bp = Blueprint("claims", __name__, url_prefix="/api/claims")

_SUPPORTED_FORMS = ("cf2", "csf")


def _mapped_view(claim_id, rows):
    mapped = mapping_service.map_claim(rows["patient"], rows["encounter"], rows["claim"])
    return {
        "success": True,
        "claim_id": claim_id,
        "status": rows["claim"]["status"],
        "fields": mapped["fields"],
        "forms": mapped["forms"],
    }


@claims_bp.route("/generate", methods=["POST"])
def generate_claim():
    payload = request.get_json(silent=True) or {}
    case_id = str(payload.get("case_id", "")).strip()
    if not case_id:
        raise InvalidRequestError("Provide a non-empty 'case_id'")

    result = claims_store.create_or_update_claim_from_case_session(case_id)
    logger.info("Generated/updated claim %s from case session", result["claim_id"])

    return jsonify({
        "success": True,
        "claim_id": result["claim_id"],
        "warnings": result["warnings"],
    })


@claims_bp.route("/<int:claim_id>", methods=["GET"])
def get_claim(claim_id):
    rows = claims_store.get_claim(claim_id)
    if rows is None:
        return jsonify({"success": False, "error": f"No claim found with id {claim_id}."}), 404
    return jsonify(_mapped_view(claim_id, rows))


@claims_bp.route("/<int:claim_id>", methods=["PUT"])
def update_claim(claim_id):
    payload = request.get_json(silent=True) or {}
    claims_store.update_claim_fields(
        claim_id,
        patient_fields=payload.get("patient"),
        encounter_fields=payload.get("encounter"),
        claims_fields=payload.get("claim"),
    )
    rows = claims_store.get_claim(claim_id)
    return jsonify(_mapped_view(claim_id, rows))


@claims_bp.route("/<int:claim_id>/export/<form_key>", methods=["GET"])
def export_claim(claim_id, form_key):
    form_key = form_key.lower()
    if form_key not in _SUPPORTED_FORMS:
        raise InvalidRequestError(f"Unsupported form '{form_key}' - supported: {', '.join(_SUPPORTED_FORMS)}")

    rows = claims_store.get_claim(claim_id)
    if rows is None:
        return jsonify({"success": False, "error": f"No claim found with id {claim_id}."}), 404

    mapped = mapping_service.map_claim(rows["patient"], rows["encounter"], rows["claim"])
    form_status = mapped["forms"][form_key]
    if not form_status["complete"]:
        raise ClaimIncompleteError(mapping_service.missing_fields_message(form_status))

    pdf_bytes = pdf_export.export_claim_pdf(form_key, rows["patient"], rows["encounter"], rows["claim"])
    logger.info("Exported claim %s as %s PDF", claim_id, form_key.upper())

    filename = f"PHILHEALTH_CLAIM_{claim_id}_{form_key.upper()}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )
