"""
Grid template persistence.

This is plain file I/O (JSON files under config.GRID_TEMPLATES_FOLDER) —
distinct from template_engine.py, which holds the actual image-processing/
matching algorithms. Moved out of app.py unchanged except for reading
folder paths from config instead of module-level constants.

Reviewed OCR "case session" persistence lives separately in
case_session_store.py (MariaDB-backed, not file-based).
"""
import json
import os
import time

from werkzeug.utils import secure_filename

import config


def get_template_files():
    try:
        return sorted(os.listdir(config.GRID_TEMPLATES_FOLDER))
    except Exception:
        return []


def load_template_payloads():
    templates = []
    for filename in get_template_files():
        path = os.path.join(config.GRID_TEMPLATES_FOLDER, filename)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                data.setdefault("filename", filename)
                templates.append(data)
        except Exception:
            continue
    return templates


def save_template_payload(payload):
    name = (payload or {}).get("name") or "template"
    safe_name = secure_filename(name) or "template"
    filename = f"{safe_name}_{int(time.time() * 1000)}.json"
    path = os.path.join(config.GRID_TEMPLATES_FOLDER, filename)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return filename, path


def update_template_from_session(template_filename, template_payload, learned_context):
    if not template_filename:
        return None

    safe_name = secure_filename(template_filename)
    path = os.path.join(config.GRID_TEMPLATES_FOLDER, safe_name)
    if not os.path.exists(path):
        for filename in get_template_files():
            if secure_filename(filename) == safe_name:
                path = os.path.join(config.GRID_TEMPLATES_FOLDER, filename)
                break

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as handle:
            existing = json.load(handle)
    except Exception:
        existing = {}

    if not isinstance(existing, dict):
        existing = {}

    merged = dict(existing)
    if isinstance(template_payload, dict):
        merged.update({k: v for k, v in template_payload.items() if v is not None})

    metadata = dict(merged.get("metadata") or {})
    metadata.update({
        "lastImprovedAt": int(time.time() * 1000),
        "lastLearnedOffsets": learned_context
    })
    merged["metadata"] = metadata

    if learned_context:
        merged.setdefault("learnedOffsets", []).append(learned_context)

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2)

    return merged
