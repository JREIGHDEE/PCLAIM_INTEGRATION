"""
Image/PDF layout analysis endpoints used by the calibration UI:
/detect_row_columns, /detect_vertical_lines, /align_template, /propagate_rows,
/auto_place_template, /process_pdf_batch.

Route bodies (including all OpenCV parameters — Canny thresholds, kernel
sizes, projection thresholds) are the original app.py logic, unchanged.
Only the temp-file save/cleanup boilerplate has been factored out into
utils.uploads.temp_upload_path.
"""
import json
import logging
import os
import time

import cv2
import numpy as np
from flask import Blueprint, jsonify, request

import config
from batch_processor import BatchProcessor
from ocr_engine import extract_text_from_array
from template_engine import (
    GridLine,
    TemplateAutoDetector,
    align_template,
    detect_vertical_lines,
    propagate_rows,
)
from utils.uploads import require_file, temp_upload_path

logger = logging.getLogger(__name__)

layout_bp = Blueprint("layout", __name__)


@layout_bp.route("/detect_row_columns", methods=["POST"])
def detect_row_columns():
    file = require_file(request.files, "image")

    with temp_upload_path(file, prefix="detect_row", suffix=".png") as temp_path:
        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise Exception(f"Could not load image: {temp_path}")

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 50, 150)

            vertical_kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (1, max(3, image.shape[0] // 15))
            )
            vertical = cv2.morphologyEx(
                edged,
                cv2.MORPH_CLOSE,
                vertical_kernel,
                iterations=2
            )

            projection = np.sum(vertical, axis=0)
            threshold = max(1, int(np.max(projection) * 0.35))
            peaks = np.where(projection > threshold)[0]

            if len(peaks) < 2:
                return jsonify({
                    "success": True,
                    "columns": [0.33, 0.66]
                })

            columns = []
            last = -100
            min_gap = max(5, int(image.shape[1] * 0.02))
            for x in peaks:
                if x - last > min_gap:
                    columns.append(x)
                    last = x

            columns = [
                x for x in columns
                if x > image.shape[1] * 0.05 and x < image.shape[1] * 0.95
            ]

            if not columns:
                return jsonify({
                    "success": True,
                    "columns": [0.33, 0.66]
                })

            columns = columns[:5]
            percents = [x / image.shape[1] for x in columns]
            return jsonify({
                "success": True,
                "columns": percents
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@layout_bp.route("/detect_vertical_lines", methods=["POST"])
def detect_vertical_lines_route():
    """Detect vertical lines in image for template alignment."""
    file = require_file(request.files, "image")

    with temp_upload_path(file, prefix="detect_lines", suffix=".png") as temp_path:
        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise Exception(f"Could not load image: {temp_path}")

            lines = detect_vertical_lines(image)

            return jsonify({
                "success": True,
                "lines": [{"x": line.x, "confidence": line.confidence} for line in lines]
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@layout_bp.route("/align_template", methods=["POST"])
def align_template_route():
    """Align saved template to current page image."""
    file = require_file(request.files, "image")

    data = request.form.get("template", "{}")
    try:
        template_data = json.loads(data)
    except Exception:
        return jsonify({
            "success": False,
            "error": "Invalid template data"
        }), 400

    with temp_upload_path(file, prefix="align_template", suffix=".png") as temp_path:
        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise Exception(f"Could not load image: {temp_path}")

            template_lines = [
                GridLine(x=float(x))
                for x in template_data.get("gridLines", [])
            ]

            result = align_template(image, template_lines)

            return jsonify({
                "success": True,
                "offset_x": result.offset_x,
                "offset_y": result.offset_y,
                "alignment_score": result.alignment_score,
                "matched_lines": result.matched_lines,
                "total_lines": result.total_lines
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@layout_bp.route("/propagate_rows", methods=["POST"])
def propagate_rows_route():
    """Generate rows using smart propagation."""
    try:
        data = request.get_json()
    except Exception:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400

    first_y = float(data.get("first_row_y", 0))
    height = float(data.get("row_height", 50))
    spacing = float(data.get("row_spacing", 0))
    img_height = float(data.get("image_height", 1000))
    max_rows = int(data.get("max_rows", 100))

    rows = propagate_rows(first_y, height, spacing, img_height, max_rows)

    return jsonify({
        "success": True,
        "rows": [
            {"y": row.y, "height": row.height, "spacing": row.spacing}
            for row in rows
        ]
    })


@layout_bp.route("/auto_place_template", methods=["POST"])
def auto_place_template_route():
    """Automatically place all template elements on image."""
    file = require_file(request.files, "image")

    template_data = request.form.get("template", "{}")
    try:
        template_dict = json.loads(template_data)
    except Exception:
        return jsonify({
            "success": False,
            "error": "Invalid template data"
        }), 400

    auto_align = request.form.get("auto_align", "true").lower() == "true"

    with temp_upload_path(file, prefix="auto_place", suffix=".png") as temp_path:
        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise Exception(f"Could not load image: {temp_path}")

            detector = TemplateAutoDetector()
            result = detector.auto_place_template(image, template_dict, auto_align)

            return jsonify(result)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@layout_bp.route("/process_pdf_batch", methods=["POST"])
def process_pdf_batch():
    """Batch process PDF with template."""
    file = require_file(request.files, "pdf")

    template_data = request.form.get("template", "{}")
    try:
        template_dict = json.loads(template_data)
    except Exception:
        return jsonify({
            "success": False,
            "error": "Invalid template data"
        }), 400

    auto_align = request.form.get("auto_align", "true").lower() == "true"

    output_path = os.path.join(
        config.UPLOAD_FOLDER,
        f"batch_results_{int(time.time() * 1000)}.json"
    )

    with temp_upload_path(file, prefix="batch_process", suffix=".pdf") as pdf_path:
        try:
            def ocr_wrapper(image):
                try:
                    tokens = extract_text_from_array(image)
                    if tokens:
                        text = "\n".join(token["text"] for token in tokens)
                        confidence = np.mean([token.get("confidence", 0) for token in tokens])
                        return {"text": text, "confidence": confidence}
                    return {"text": "", "confidence": 0}
                except Exception:
                    return {"text": "", "confidence": 0}

            processor = BatchProcessor(ocr_function=ocr_wrapper)
            results = processor.process_pdf(
                pdf_path,
                template_dict,
                output_path=output_path,
                auto_align=auto_align
            )

            return jsonify(results)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
