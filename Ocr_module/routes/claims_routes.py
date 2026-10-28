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
import crop_cleanup
from errors import ClaimIncompleteError, InvalidRequestError
from philhealth import form_prefill, mapping_service, pdf_export

logger = logging.getLogger(__name__)

claims_bp = Blueprint("claims", __name__, url_prefix="/api/claims")

_SUPPORTED_FORMS = ("cf2", "csf")


def _finish_export(claim_id):
    """A claim's PDF was made: mark it exported, and delete the review crops
    of the logbook row it came from - they are not needed any more. A crop
    that cannot be deleted never undoes the export (startup cleanup gets it)."""
    claims_store.mark_exported(claim_id)
    try:
        source = claims_store.get_claim_form_source(claim_id)
        if source and source["session"]:
            crop_cleanup.delete_session_crops(source["session"])
    except OSError:
        logger.exception("Could not delete the review crops of claim %s", claim_id)


def _rule_values(rows):
    """The claim as the forms hold it: the stored columns, with what staff
    typed on the forms (claims.form_values) over them - the same order
    PClaimAssist loads them in (js/claim-loader.js)."""
    values = dict(form_prefill.build_form_data(rows)["data"])
    values.update({k: v for k, v in claims_store.saved_form_values(rows["claim"]).items()
                   if not k.startswith("_")})
    return values


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
    session_id = payload.get("session_id")
    case_id = str(payload.get("case_id", "")).strip()
    if session_id not in (None, ""):
        try:
            session_id = int(session_id)
        except (TypeError, ValueError):
            raise InvalidRequestError("'session_id' must be an integer")
        result = claims_store.create_or_update_claim_from_session_id(session_id)
    elif case_id:
        result = claims_store.create_or_update_claim_from_case_session(case_id)
    else:
        raise InvalidRequestError("Provide a 'session_id' or a non-empty 'case_id'")
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


@claims_bp.route("/<int:claim_id>/form-data", methods=["GET"])
def get_claim_form_data(claim_id):
    """The claim as PClaimAssist form values (PMRF, CSF, CF2, CF4), keyed by
    form key, with each OCR-sourced field's review status - see
    philhealth/form_prefill.py. PClaimAssist loads this by claim id; patient
    data never travels in a URL."""
    source = claims_store.get_claim_form_source(claim_id)
    if source is None:
        return jsonify({"success": False, "error": f"No claim found with id {claim_id}."}), 404
    prefill = form_prefill.build_form_data(source["rows"], source["session"])
    session = source["session"]
    return jsonify({
        "success": True,
        "claim_id": claim_id,
        "status": source["rows"]["claim"]["status"],
        "session_id": session["id"] if session else None,
        "image_quality": ((session or {}).get("ocr_data") or {}).get("image_quality"),
        # What staff typed on the forms last time, put back over the above.
        "saved_values": claims_store.saved_form_values(source["rows"]["claim"]),
        **prefill,
    })


@claims_bp.route("/<int:claim_id>/form-values", methods=["PUT"])
def save_claim_form_values(claim_id):
    """Everything typed on the forms for this claim, saved as staff type
    (claims.form_values), so it is there when the claim is opened again -
    and for a baby's claim copying from its mother's."""
    payload = request.get_json(silent=True) or {}
    claims_store.save_form_values(claim_id, payload.get("values"))
    return jsonify({"success": True})


@claims_bp.route("/save", methods=["POST"])
def save_patient():
    """"Save patient" (Check for Missing Information): {"claim_id": int |
    null, "values": {form key: value}}. With no claim_id, a patient typed in
    by hand gets a new claim. Returns its claim id."""
    payload = request.get_json(silent=True) or {}
    claim_id = payload.get("claim_id")
    if claim_id is not None:
        try:
            claim_id = int(claim_id)
        except (TypeError, ValueError):
            raise InvalidRequestError("'claim_id' must be an integer or null")
    claim_id = claims_store.save_patient(claim_id, payload.get("values"))
    logger.info("Saved patient on claim %s", claim_id)
    return jsonify({"success": True, "claim_id": claim_id,
                    "status": claims_store.get_claim(claim_id)["claim"]["status"]})


@claims_bp.route("/<int:claim_id>/family", methods=["GET"])
def get_claim_family(claim_id):
    """Mother or baby, and the claims this one is linked with
    (claims_store.get_family)."""
    return jsonify({"success": True, **claims_store.get_family(claim_id)})


@claims_bp.route("/<int:claim_id>/family", methods=["PUT"])
def update_claim_family(claim_id):
    """{"role": "mother" | "baby" | "other" | null} and/or
    {"mother_claim_id": int | null}: only the keys sent are changed."""
    payload = request.get_json(silent=True) or {}
    mother_claim_id = payload.get("mother_claim_id")
    if mother_claim_id is not None:
        try:
            mother_claim_id = int(mother_claim_id)
        except (TypeError, ValueError):
            raise InvalidRequestError("'mother_claim_id' must be an integer or null")
    family = claims_store.set_family(
        claim_id, role=payload.get("role"), mother_claim_id=mother_claim_id,
        set_role="role" in payload, set_mother="mother_claim_id" in payload)
    return jsonify({"success": True, **family})


@claims_bp.route("/mothers", methods=["GET"])
def get_mothers():
    """The mothers' claims a baby typed in by hand can copy from, before
    the baby's own claim is saved (claims_store.list_mothers)."""
    return jsonify({"success": True, "mothers": claims_store.list_mothers()})


@claims_bp.route("/<int:claim_id>/for-baby", methods=["GET"])
def get_values_for_baby(claim_id):
    """What a baby's claim copies from this mother's claim, without the
    baby's claim (claims_store.values_for_baby_from)."""
    return jsonify({"success": True, **claims_store.values_for_baby_from(claim_id)})


@claims_bp.route("/<int:claim_id>/from-mother", methods=["GET"])
def get_values_from_mother(claim_id):
    """What a baby's claim copies from its linked mother's claim, grouped
    by who each value is about (philhealth/mother_baby.values_for_baby)."""
    return jsonify({"success": True, **claims_store.values_from_mother(claim_id)})


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


@claims_bp.route("/<int:claim_id>/exported", methods=["POST"])
def claim_exported(claim_id):
    """PClaimAssist saved this claim's forms as a PDF in the browser
    (js/pdf/pdf-overlay.js, which checks the critical rules first): the claim
    is exported, and its review crops are deleted."""
    if claims_store.get_claim(claim_id) is None:
        return jsonify({"success": False, "error": f"No claim found with id {claim_id}."}), 404
    _finish_export(claim_id)
    return jsonify({"success": True, "status": claims_store.get_claim(claim_id)["claim"]["status"]})


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
    # The critical rules the forms check before saving a PDF (validation-rules.js).
    problems = mapping_service.critical_rule_problems(_rule_values(rows))
    if problems:
        raise ClaimIncompleteError(mapping_service.critical_rules_message(problems))

    pdf_bytes = pdf_export.export_claim_pdf(form_key, rows["patient"], rows["encounter"], rows["claim"])
    _finish_export(claim_id)
    logger.info("Exported claim %s as %s PDF", claim_id, form_key.upper())

    filename = f"PHILHEALTH_CLAIM_{claim_id}_{form_key.upper()}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )
