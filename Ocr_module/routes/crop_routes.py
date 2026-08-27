"""Training-crop storage endpoint used by the calibration UI: /save_crop."""
import logging
import os
import time

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

import config
from utils.uploads import require_file

logger = logging.getLogger(__name__)

crop_bp = Blueprint("crop", __name__)


@crop_bp.route("/save_crop", methods=["POST"])
def save_cropped_field():
    file = require_file(request.files, "image")

    category = request.form.get("category")
    if not category or category not in config.CATEGORY_FOLDERS:
        return jsonify({
            "success": False,
            "error": "Invalid or missing category"
        }), 400

    filename = secure_filename(file.filename) or "crop.png"
    folder_path = config.CATEGORY_FOLDERS[category]
    timestamp = int(time.time() * 1000)
    save_path = os.path.join(folder_path, f"{timestamp}_{filename}")

    file.save(save_path)

    return jsonify({
        "success": True,
        "saved_path": save_path
    })
