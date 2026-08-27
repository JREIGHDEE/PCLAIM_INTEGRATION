"""
Grid template CRUD + template-matching endpoints used by the calibration UI
(templates/index.html): /save_grid_template, /grid_templates, /grid_template,
/match_template, /update_template_from_feedback, /delete_grid_template.

Route bodies are the original app.py logic, unchanged, aside from routing
through config/template_store/utils.uploads instead of module-level globals.
"""
import json
import logging
import os

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

import config
from errors import InvalidRequestError, TemplateNotFoundError
from template_engine import analyze_document_layout, build_template_payload, match_templates
from template_store import (
    get_template_files,
    load_template_payloads,
    save_template_payload,
    update_template_from_session,
)
from utils.uploads import require_file, temp_upload_path

try:
    import cv2
except ImportError:  # pragma: no cover - cv2 is a hard requirement, mirrors original import style
    cv2 = None

logger = logging.getLogger(__name__)

template_bp = Blueprint("templates", __name__)


@template_bp.route("/save_grid_template", methods=["POST"])
def save_grid_template():
    try:
        data = request.get_json(force=True)
    except Exception:
        data = None

    if not data:
        return jsonify({"success": False, "error": "Template payload is required"}), 400

    name = data.get("name")
    if not name:
        return jsonify({"success": False, "error": "Template name is required"}), 400

    payload = build_template_payload(
        name=name,
        grid_lines=data.get("gridLines", []),
        segment_info=data.get("segmentInfo", []),
        crop_box_percent=data.get("cropBoxPercent"),
        row_template=data.get("rowTemplate"),
        crop_presets=data.get("cropPresets", []),
        image_width=data.get("imageWidth"),
        image_height=data.get("imageHeight"),
        metadata=data.get("metadata") or {},
        active_crop_preset=data.get("activeCropPreset"),
        active_crop_preset_id=data.get("activeCropPresetId")
    )

    filename, _ = save_template_payload(payload)
    return jsonify({"success": True, "filename": filename, "template": payload})


@template_bp.route("/grid_templates")
def list_grid_templates():
    templates = []
    for filename in get_template_files():
        path = os.path.join(config.GRID_TEMPLATES_FOLDER, filename)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            templates.append({
                "filename": filename,
                "name": data.get("name", filename),
                "gridLines": data.get("gridLines", []),
                "segmentInfo": data.get("segmentInfo", []),
                "rowTemplate": data.get("rowTemplate"),
                "cropPresets": data.get("cropPresets", [])
            })
        except Exception:
            continue

    return jsonify({"success": True, "templates": templates})


@template_bp.route("/grid_template")
def get_grid_template():
    filename = request.args.get("filename", "").strip()
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400

    safe = secure_filename(filename)
    path = os.path.join(config.GRID_TEMPLATES_FOLDER, safe)
    if not os.path.exists(path):
        for candidate in get_template_files():
            if secure_filename(candidate) == safe:
                path = os.path.join(config.GRID_TEMPLATES_FOLDER, candidate)
                break

    if not os.path.exists(path):
        return jsonify({"success": False, "error": "Template not found"}), 404

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "template": data})


@template_bp.route("/match_template", methods=["POST"])
def match_template_route():
    file = require_file(request.files, "image")

    with temp_upload_path(file, prefix="match_template", suffix=".png") as temp_path:
        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise Exception(f"Could not load image: {temp_path}")

            current_context = analyze_document_layout(image)
            templates = load_template_payloads()
            best_template, best_score = match_templates(templates, current_context)

            auto_apply = False
            if best_template and best_score is not None:
                auto_apply = best_score >= config.TEMPLATE_MATCH_THRESHOLD

            return jsonify({
                "success": True,
                "templates": templates,
                "bestTemplate": best_template,
                "bestScore": best_score,
                "autoApply": auto_apply,
                "threshold": config.TEMPLATE_MATCH_THRESHOLD,
                "context": current_context
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


@template_bp.route("/update_template_from_feedback", methods=["POST"])
def update_template_from_feedback():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}

    template_filename = (data.get("template_filename") or "").strip()
    template_payload = data.get("updates") or data.get("template_payload") or {}
    if not template_filename:
        return jsonify({"success": False, "error": "template_filename is required"}), 400

    learned_context = {
        "gridLines": template_payload.get("gridLines", []),
        "rowTemplate": template_payload.get("rowTemplate"),
        "cropBoxPercent": template_payload.get("cropBoxPercent")
    }
    updated = update_template_from_session(template_filename, template_payload, learned_context)
    return jsonify({"success": True, "template": updated})


@template_bp.route("/delete_grid_template", methods=["POST"])
def delete_grid_template():
    try:
        data = request.get_json(force=True)
    except Exception:
        data = None

    filename = (data or {}).get("filename", "")
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400

    safe = secure_filename(filename)
    path = os.path.join(config.GRID_TEMPLATES_FOLDER, safe)
    if not os.path.exists(path):
        return jsonify({"success": False, "error": "Template not found"}), 404

    try:
        os.remove(path)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True})
