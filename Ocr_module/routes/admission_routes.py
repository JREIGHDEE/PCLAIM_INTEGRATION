"""Admission patterns: the table behind the reason for admission suggested
from the logbook (admission_pattern_store.py, philhealth/admission_patterns.py).

  GET    /api/admission-patterns                 every pattern, and whether it can be changed
  POST   /api/admission-patterns                 add one
  PUT    /api/admission-patterns/<id>            change one
  DELETE /api/admission-patterns/<id>            delete one
  POST   /api/admission-patterns/try             {"text"} -> the patterns, best first
  POST   /api/admission-patterns/suggest         {"readings"} -> the best one, for the logbook review
  POST   /api/admission-patterns/<id>/learn      {"reading", "suggested_id"} - staff said the
                                                 reading is this pattern
  POST   /api/admission-patterns/<id>/forget     {"reading"} - take a learned reading off

Every signed-in account may change them: the encoders are the ones who see
a wrong suggestion (PClaimAssist's "Admission patterns" page, and the card
under Reason for admission on Patient details).
"""
import logging

from flask import Blueprint, jsonify, request

import admission_pattern_store
import auth
from errors import InvalidRequestError
from philhealth import admission_patterns

logger = logging.getLogger(__name__)

admission_bp = Blueprint("admission_patterns", __name__, url_prefix="/api/admission-patterns")
_MAX_TEXT = 500


def _who():
    return (auth.current_user() or {}).get("email", "unknown")


def _text(payload, key):
    value = payload.get(key)
    if not isinstance(value, str) or len(value) > _MAX_TEXT:
        raise InvalidRequestError(f"Provide '{key}' as text (up to {_MAX_TEXT} characters).")
    return value


@admission_bp.route("", methods=["GET"])
@auth.login_required
def list_patterns():
    patterns, editable = admission_pattern_store.load()
    return jsonify({"success": True, "patterns": patterns, "editable": editable,
                    "packages": list(admission_pattern_store.PACKAGES)})


@admission_bp.route("", methods=["POST"])
@auth.login_required
def add_pattern():
    new_id = admission_pattern_store.create(request.get_json(silent=True) or {}, _who())
    logger.info("Admission pattern %s added by %s", new_id, _who())
    return jsonify({"success": True, "id": new_id}), 201


@admission_bp.route("/<int:pattern_id>", methods=["PUT"])
@auth.login_required
def change_pattern(pattern_id):
    admission_pattern_store.update(pattern_id, request.get_json(silent=True) or {}, _who())
    logger.info("Admission pattern %s changed by %s", pattern_id, _who())
    return jsonify({"success": True})


@admission_bp.route("/<int:pattern_id>", methods=["DELETE"])
@auth.login_required
def delete_pattern(pattern_id):
    admission_pattern_store.delete(pattern_id)
    logger.info("Admission pattern %s deleted by %s", pattern_id, _who())
    return jsonify({"success": True})


@admission_bp.route("/try", methods=["POST"])
@auth.login_required
def try_reading():
    text = _text(request.get_json(silent=True) or {}, "text")
    ranked = admission_patterns.rank(text, admission_pattern_store.load_active())
    return jsonify({"success": True, "ranked": ranked, "suggest_from": admission_patterns.SUGGEST_FROM})


@admission_bp.route("/suggest", methods=["POST"])
@auth.login_required
def suggest_for_entry():
    """{"readings": [admitting diagnosis, final diagnosis]} -> the best
    pattern for the first one that has one, and every pattern in use (for
    "Not right? It is..."). For the logbook review (templates/review.html)."""
    readings = (request.get_json(silent=True) or {}).get("readings")
    if not isinstance(readings, list) or not all(isinstance(r, str) and len(r) <= _MAX_TEXT for r in readings):
        raise InvalidRequestError(f"Provide 'readings' as a list of texts (each up to {_MAX_TEXT} characters).")
    patterns = admission_pattern_store.load_active()
    return jsonify({"success": True, "suggestion": admission_patterns.suggest(readings[:2], patterns),
                    "patterns": [{k: p.get(k) for k in ("id", "name", "reason", "package")} for p in patterns]})


@admission_bp.route("/<int:pattern_id>/learn", methods=["POST"])
@auth.login_required
def learn_reading(pattern_id):
    payload = request.get_json(silent=True) or {}
    suggested = payload.get("suggested_id")
    admission_pattern_store.learn(pattern_id, _text(payload, "reading"), _who(),
                                  suggested_id=suggested if isinstance(suggested, int) else None)
    logger.info("Admission pattern %s learned a reading (suggested: %s) from %s", pattern_id, suggested, _who())
    return jsonify({"success": True})


@admission_bp.route("/<int:pattern_id>/forget", methods=["POST"])
@auth.login_required
def forget_reading(pattern_id):
    admission_pattern_store.forget_example(pattern_id, _text(request.get_json(silent=True) or {}, "reading"), _who())
    return jsonify({"success": True})
