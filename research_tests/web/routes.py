"""Routes of the research tabs (administrators only, like the OCR
comparison page). Everything is under /ocr-testing/research:

  GET  /api/tabs                     the tabs, for the tab bar (static/tabs.js)
  GET  /<test>                       a test's tab (inside the shell's iframe)
  GET  /results                      the Results tab
  GET  /api/<test>/status            its run's progress, inputs, latest summary
  POST /api/<test>/run               start it (JSON options) - a background process
  POST /api/<test>/cancel            stop it
  POST /api/<test>/upload/<slot>     put input files into research_tests/inputs/
  GET  /api/<test>/download          its results workbook
  GET  /api/templates/<name>         an input template
Nothing here touches the main app's tables, uploads or sessions.
"""
import json
import re
from pathlib import Path

from flask import Blueprint, abort, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

import auth
from errors import InvalidRequestError
from research_tests import INPUTS, OUTPUTS, output_dir
from research_tests.registry import BY_KEY, RESULTS, TESTS
from research_tests.web import URL_PREFIX, jobs

research_bp = Blueprint("research", __name__, url_prefix=URL_PREFIX, template_folder="templates",
                        static_folder="static", static_url_path="/static")
admin_only = auth.role_required("admin")

SCAN_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
TEMPLATES = {"answer_key_template.xlsx", "writers_template.csv", "session_data_template.xlsx",
             "field_mapping_expected.csv", "sus_template.xlsx"}
ALL_KEYS = {t["key"] for t in TESTS} | {"results"}


def _test(key):
    if key == "results":
        return RESULTS
    test = BY_KEY.get(key)
    if test is None:
        abort(404)
    return test


def _inputs_status(test, root):
    out = []
    for slot, target in (test.get("uploads") or {}).items():
        path = root / target
        if target.endswith("/"):
            files = sorted(p.name for p in path.glob("*") if p.is_file()) if path.is_dir() else []
            out.append({"slot": slot, "target": target, "folder": True, "count": len(files), "files": files[:40]})
        else:
            out.append({"slot": slot, "target": target, "folder": False, "count": 1 if path.is_file() else 0,
                        "files": [path.name] if path.is_file() else []})
    return out


def _summary(key):
    path = OUTPUTS / key / "summary.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


@research_bp.route("/api/tabs")
@admin_only
def tabs():
    return jsonify({"success": True, "tabs": [{"key": t["key"], "tab": t["tab"], "url": f"{URL_PREFIX}/{t['key']}"}
                                              for t in TESTS + [RESULTS]]})


@research_bp.route("/<key>")
@admin_only
def tab_page(key):
    if key not in ALL_KEYS:
        abort(404)
    if key == "results":
        return render_template("research/results.html", tests=TESTS, prefix=URL_PREFIX)
    return render_template("research/tab.html", test=_test(key), prefix=URL_PREFIX)


@research_bp.route("/api/<key>/status")
@admin_only
def status(key):
    test = _test(key)
    workbook = OUTPUTS / test["workbook"] if key == "results" else OUTPUTS / key / test["workbook"]
    body = {"success": True, "running": jobs.running(key), "progress": jobs.status(key),
            "workbook": workbook.is_file(), "summary": _summary(key)}
    if key != "results":
        body["inputs"] = _inputs_status(test, INPUTS)
        body["sample_inputs"] = _inputs_status(test, INPUTS / "samples")
    else:
        body["tests"] = [{"key": t["key"], "tab": t["tab"], "summary": bool(_summary(t["key"])),
                          "generated_at": (_summary(t["key"]) or {}).get("generated_at"),
                          "samples": (_summary(t["key"]) or {}).get("samples", False)} for t in TESTS]
    return jsonify(body)


def _cli_args(test, options):
    args = []
    if options.get("samples") and test.get("samples", True):
        args.append("--samples")
    for opt in test.get("options", []):
        value = options.get(opt["name"])
        flag = "--" + opt["name"].replace("_", "-")
        if opt["type"] == "check":
            if value:
                args.append(flag)
        elif value not in (None, ""):
            value = str(value).strip()
            if opt["type"] == "number" and not re.fullmatch(r"\d{1,9}", value):
                raise InvalidRequestError(f"{opt['label']}: a whole number, please.")
            if opt["type"] == "select" and value not in opt["choices"]:
                raise InvalidRequestError(f"{opt['label']}: not one of the choices.")
            if opt["type"] == "text" and not re.fullmatch(r"[A-Za-z0-9,\s_-]{1,200}", value):
                raise InvalidRequestError(f"{opt['label']}: letters, digits and commas only.")
            args += [flag, value]
    return args


@research_bp.route("/api/<key>/run", methods=["POST"])
@admin_only
def run(key):
    test = _test(key)
    args = [] if key == "results" else _cli_args(test, request.get_json(silent=True) or {})
    if not jobs.start(key, args):
        return jsonify({"success": False, "error": "This test is already running."}), 409
    return jsonify({"success": True}), 202


@research_bp.route("/api/<key>/cancel", methods=["POST"])
@admin_only
def cancel(key):
    _test(key)
    return jsonify({"success": True, "cancelled": jobs.cancel(key)})


@research_bp.route("/api/<key>/upload/<slot>", methods=["POST"])
@admin_only
def upload(key, slot):
    test = _test(key)
    target = (test.get("uploads") or {}).get(slot)
    if target is None:
        abort(404)
    files = [f for f in request.files.getlist("files") if f and f.filename]
    if not files:
        raise InvalidRequestError("Choose a file first.")
    saved = []
    if target.endswith("/"):
        folder = INPUTS / target
        folder.mkdir(parents=True, exist_ok=True)
        for f in files:
            name = secure_filename(f.filename)
            if not name or Path(name).suffix.lower() not in SCAN_TYPES:
                raise InvalidRequestError(f"{f.filename}: only PDF or image files go here.")
            f.save(folder / name)
            saved.append(name)
    else:
        if len(files) != 1:
            raise InvalidRequestError("One file here, please.")
        want = Path(target).suffix.lower()
        if Path(files[0].filename).suffix.lower() != want:
            raise InvalidRequestError(f"This needs a {want} file ({target}).")
        path = INPUTS / target
        path.parent.mkdir(parents=True, exist_ok=True)
        files[0].save(path)
        saved.append(target)
    return jsonify({"success": True, "saved": saved})


@research_bp.route("/api/<key>/download")
@admin_only
def download(key):
    test = _test(key)
    path = OUTPUTS / test["workbook"] if key == "results" else output_dir(key) / test["workbook"]
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name=test["workbook"])


@research_bp.route("/api/templates/<name>")
@admin_only
def template(name):
    if name not in TEMPLATES or not (INPUTS / name).is_file():
        abort(404)
    return send_file(INPUTS / name, as_attachment=True, download_name=name)
