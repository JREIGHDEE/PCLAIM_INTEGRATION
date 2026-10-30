"""Clinic-wide settings.

  GET  /api/settings/clinic             the clinic's name, PAN and address
  POST /api/settings/clinic   (admin)   update them
  POST /api/settings/check-email        is an email address written and
                                        spelled correctly (email_check.py)

Table 3.1 of the research design lists clinic name, accreditation number
and address as "System settings (entered once)", shared by CF2 and
CF4. Reading is open to any signed-in user because every claim form needs
these values; only an administrator may change them.
"""
import logging

from flask import Blueprint, jsonify, request

import auth
import clinic_settings_store
import email_check

logger = logging.getLogger(__name__)

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@settings_bp.route("/clinic", methods=["GET"])
@auth.login_required
def get_clinic_settings():
    return jsonify({"success": True, "settings": clinic_settings_store.get_settings()})


@settings_bp.route("/clinic", methods=["POST"])
@auth.role_required("admin")
def update_clinic_settings():
    data = request.get_json(silent=True) or {}
    settings = clinic_settings_store.update_settings(
        data.get("settings") or {}, updated_by=auth.current_user()["id"])
    return jsonify({"success": True, "settings": settings})


@settings_bp.route("/check-email", methods=["POST"])
@auth.login_required
def check_email_address():
    """Is this a real address? Checked here, not by a service elsewhere:
    the patient's email never leaves this computer (email_check.py)."""
    address = (request.get_json(silent=True) or {}).get("email") or ""
    return jsonify({"success": True, **email_check.check_email(address)})
