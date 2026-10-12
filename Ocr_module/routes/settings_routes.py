"""Clinic-wide settings.

  GET  /api/settings/clinic             the clinic's name, PAN and address
  POST /api/settings/clinic   (admin)   update them

Table 3.1 of the research design lists clinic name, accreditation number
and address as "System settings (entered once)", shared by CF2, CF3 and
CF4. Reading is open to any signed-in user because every claim form needs
these values; only an administrator may change them.
"""
import logging

from flask import Blueprint, jsonify, request

import auth
import clinic_settings_store

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
