"""Does this computer give the same results as the project lead's?

    Ocr_module\\venv\\Scripts\\python.exe -m research_tests.check_setup [--skip-smoke]
    ... --record      (the project lead only: write the reference from this machine)

Prints PASS / FAIL (and WARN where a difference cannot change the numbers)
for each item, with how to fix each FAIL:
  Python and every pinned package; Tesseract and Microsoft Edge versions;
  SHA-256 of the PaddleOCR model files, the logbook setups (grid templates)
  and the vendored pdf-lib; the research database and its seed checksums;
  SHA-256 of the committed test inputs; and a smoke test - writer W03's
  scanner scan through the real pipeline (PaddleOCR and Tesseract, raw and
  corrected), every cell compared with the stored reference. Differing cells
  are listed, not hidden.

Timing is never compared (it depends on the machine).
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
from pathlib import Path

from research_tests import INPUTS, OCR_DIR, ROOT, VENDOR

REFERENCE = ROOT / "setup" / "reference"
ENV_FILE = REFERENCE / "environment.json"
SMOKE_FILE = REFERENCE / "smoke_W03_scanner.json"
SMOKE_WRITER = "W03"
# Inputs every result depends on (session data and the expected box table are
# edited by groupmates, so they are reported, not required to match).
EDITED_BY_TEAM = {"field_mapping_expected.csv"}
INPUT_GLOBS = ["answer_key.xlsx", "writers.csv", "task_packet.xlsx", "field_mapping_expected.csv",
               "scans/handwriting/*.pdf", "scans/handwriting_phone/*.pdf", "*_template.xlsx", "*_template.csv"]
results = []


def report(item, status, detail="", fix=""):
    results.append((item, status, detail, fix))
    mark = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN"}[status]
    print(f"[{mark}] {item}" + (f" - {detail}" if detail else ""))
    if status == "FAIL" and fix:
        print(f"       fix: {fix}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hashes(files, base):
    return {str(p.relative_to(base)).replace("\\", "/"): sha256(p) for p in sorted(files) if p.is_file()}


def pinned_packages():
    pins = {}
    for req in (OCR_DIR / "requirements.txt", ROOT / "requirements.txt"):
        for line in req.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*([A-Za-z0-9_.\-]+)==([^\s#;]+)", line)
            if m:
                pins[m[1]] = m[2]
    return pins


def tesseract_version():
    try:
        from research_tests.common.specs import _tesseract
        return _tesseract()
    except Exception as exc:
        return f"not available ({exc})"


def edge_version():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge", headless=True)
            v = b.version
            b.close()
            return v
    except Exception as exc:
        return f"not available ({type(exc).__name__})"


def input_files():
    return [p for pattern in INPUT_GLOBS for p in INPUTS.glob(pattern)]


def environment():
    return {
        "python": platform.python_version(),
        "packages": {name: _installed(name) for name in pinned_packages()},
        "tesseract": tesseract_version(),
        "edge": edge_version(),
        "models": hashes(list((OCR_DIR / "ocr_models").rglob("*")), OCR_DIR / "ocr_models"),
        "grid_templates": hashes(list((OCR_DIR / "grid_templates").glob("*.json")), OCR_DIR / "grid_templates"),
        "pdf_lib": sha256(VENDOR / "pdf-lib.min.js"),
        "inputs": hashes(input_files(), INPUTS),
    }


def _installed(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def smoke():
    """W03's scanner scan through the pipeline, as the handwriting test reads
    it -> {cell key: {readings and scores}}."""
    from research_tests import handwriting
    from research_tests.common import answer_key
    writer = next(w for w in answer_key.writers(INPUTS / "writers.csv") if w["writer"] == SMOKE_WRITER)
    path = handwriting.scan_path(INPUTS, writer, "scanner")
    reader = handwriting.Reader()
    run = reader.read(path, lambda f, m: None)
    key = [k for k in answer_key.handwriting(INPUTS / "answer_key.xlsx") if k["writer"] == SMOKE_WRITER]
    lines = handwriting.score_cells(dict(writer, scan=path.name), key, run)
    out = {}
    for l in lines:
        cell = f"p{l['page']} r{l['row']} {l['field']}"
        out[cell] = {"detected": l["detected"], **{v: l.get(v) for v in handwriting.VARIANTS},
                     **{f"{v}_accuracy": l.get(f"{v}_accuracy") for v in handwriting.VARIANTS}}
    return {"scan": path.name, "sha256": sha256(path), "model": reader.model_note, "cells": out}


def record():
    from research_tests import guard
    from research_tests.setup import seed
    REFERENCE.mkdir(parents=True, exist_ok=True)
    env = environment()
    ENV_FILE.write_text(json.dumps(env, indent=1), encoding="utf-8")
    print(f"Recorded the environment -> {ENV_FILE}")
    from db import get_db_cursor
    with get_db_cursor() as c:
        sums = seed.table_checksums(c)
    if sums != seed.recorded():
        print("WARNING: this research database differs from seed_checksums.json - run setup.import_seed first.")
    print("Running the smoke test to record its reference ...")
    ref = smoke()
    SMOKE_FILE.write_text(json.dumps(ref, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Recorded the smoke test ({len(ref['cells'])} cells) -> {SMOKE_FILE}")
    return 0


def check(skip_smoke=False):
    if not ENV_FILE.is_file():
        print(f"No reference ({ENV_FILE}) - the project lead records it with --record.")
        return 1
    ref = json.loads(ENV_FILE.read_text(encoding="utf-8"))
    now_python = platform.python_version()
    report("Python", "PASS" if now_python == ref["python"] else
           ("WARN" if now_python.rsplit(".", 1)[0] == ref["python"].rsplit(".", 1)[0] else "FAIL"),
           f"{now_python} (reference {ref['python']})", f"install Python {ref['python']} (64-bit) and recreate the venv")
    wrong = {n: (_installed(n), v) for n, v in ref["packages"].items() if v and _installed(n) != v}
    report("Python packages", "PASS" if not wrong else "FAIL",
           f"{len(ref['packages'])} pinned" if not wrong else
           "; ".join(f"{n} {have or 'missing'} (want {want})" for n, (have, want) in list(wrong.items())[:6]),
           "Ocr_module\\venv\\Scripts\\pip.exe install -r Ocr_module\\requirements.txt -r research_tests\\requirements.txt")
    tess = tesseract_version()
    report("Tesseract", "PASS" if tess == ref["tesseract"] else "FAIL", f"{tess} (reference {ref['tesseract']})",
           "install Tesseract 5.4.0.20240606 (UB Mannheim build) and set TESSERACT_CMD in Ocr_module/.env")
    edge = edge_version()
    report("Microsoft Edge (headless)", "PASS" if edge == ref["edge"] else
           ("FAIL" if edge.startswith("not available") else "WARN"),
           f"{edge} (reference {ref['edge']}; Edge updates itself - the version is recorded with each result)",
           "install Microsoft Edge and run: Ocr_module\\venv\\Scripts\\pip.exe install playwright==1.64.1")
    for item, key, base, fix in (
            ("PaddleOCR model files", "models", OCR_DIR / "ocr_models", "git checkout -- Ocr_module/ocr_models"),
            ("Logbook setups (grid templates)", "grid_templates", OCR_DIR / "grid_templates",
             "git checkout -- Ocr_module/grid_templates (they are the clinic's shared logbook setup)")):
        files = list(base.rglob("*")) if key == "models" else list(base.glob("*.json"))
        now = hashes(files, base)
        diff = sorted(k for k in set(now) | set(ref[key]) if now.get(k) != ref[key].get(k))
        report(item, "PASS" if not diff else "FAIL", f"{len(now)} files" if not diff else f"differ: {', '.join(diff[:5])}", fix)
    pdf = sha256(VENDOR / "pdf-lib.min.js")
    report("pdf-lib 1.17.1 (vendored)", "PASS" if pdf == ref["pdf_lib"] else "FAIL", pdf[:16] + "...",
           "git checkout -- research_tests/vendor/pdf-lib.min.js")

    from research_tests import guard
    from research_tests.setup import seed
    try:
        from db import get_db_cursor
        with get_db_cursor() as c:
            sums = seed.table_checksums(c)
        want = seed.recorded()
        report("Research database seed", "PASS" if sums == want else "FAIL",
               ", ".join(f"{t} {s['rows']} rows" for t, s in sums.items()),
               "Ocr_module\\venv\\Scripts\\python.exe -m research_tests.setup.import_seed")
    except Exception as exc:
        report("Research database", "FAIL", f"not readable ({type(exc).__name__})",
               "start MariaDB in XAMPP, then: Ocr_module\\venv\\Scripts\\python.exe -m research_tests.setup.import_seed")

    now = hashes(input_files(), INPUTS)
    missing = sorted(set(ref["inputs"]) - set(now))
    changed = sorted(k for k in ref["inputs"] if k in now and now[k] != ref["inputs"][k])
    hard = [k for k in missing + changed if Path(k).name not in EDITED_BY_TEAM]
    soft = [k for k in changed if Path(k).name in EDITED_BY_TEAM]
    report("Test inputs (SHA-256)", "PASS" if not hard else "FAIL",
           f"{len(ref['inputs'])} files" + (f"; edited by the team: {', '.join(soft)}" if soft else "")
           if not hard else f"{len(missing)} missing, {len(changed)} changed: {', '.join(hard[:5])}",
           "git pull, or git checkout -- research_tests/inputs (do not edit the scans or the answer key)")

    if skip_smoke:
        report("Smoke test (W03)", "WARN", "skipped (--skip-smoke)")
    elif not SMOKE_FILE.is_file():
        report("Smoke test (W03)", "FAIL", "no stored reference", "the project lead records it with --record")
    else:
        want = json.loads(SMOKE_FILE.read_text(encoding="utf-8"))
        print("Running the smoke test (W03, about a minute) ...")
        got = smoke()
        diffs = []
        for cell, w in want["cells"].items():
            g = got["cells"].get(cell)
            if g != w:
                for k in sorted(set(w) | set(g or {})):
                    if (g or {}).get(k) != w.get(k):
                        diffs.append(f"{cell} {k}: reference {w.get(k)!r}, here {(g or {}).get(k)!r}")
        report("Smoke test (W03)", "PASS" if not diffs and got["model"] == want["model"] else "FAIL",
               f"{len(want['cells'])} cells identical" if not diffs else f"{len(diffs)} differences",
               "check the items above first (packages, models, Tesseract, seed); PaddleOCR on another processor "
               "can differ in a few cells - send the list to the project lead")
        for d in diffs[:40]:
            print("       " + d)
        if got["model"] != want["model"]:
            print(f"       correction model: reference {want['model']!r}, here {got['model']!r}")
    fails = sum(1 for r in results if r[1] == "FAIL")
    print(f"\n{len(results)} checks: {sum(1 for r in results if r[1] == 'PASS')} PASS, "
          f"{sum(1 for r in results if r[1] == 'WARN')} WARN, {fails} FAIL")
    return 1 if fails else 0


def main(argv=None):
    from research_tests import guard
    guard.isolate()
    import logging
    logging.basicConfig(level=logging.ERROR)
    parser = argparse.ArgumentParser(prog="python -m research_tests.check_setup", description=__doc__.splitlines()[0])
    parser.add_argument("--record", action="store_true", help="write the reference from this machine (project lead)")
    parser.add_argument("--skip-smoke", action="store_true", help="skip the W03 smoke test")
    args = parser.parse_args(argv)
    return record() if args.record else check(args.skip_smoke)


if __name__ == "__main__":
    sys.exit(main())
