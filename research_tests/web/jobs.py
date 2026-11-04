"""Each test run from a tab is its own background process:

    <the app's python> -m research_tests.<test> [options]

so a long OCR test never blocks the page or the Flask server, and the run
gets the research isolation (guard.isolate: outputs/work, read-only
database) that the main app's process must not have. The process writes
its progress to outputs/<test>/progress.json, and its output to
outputs/<test>/run.log; the tab polls the progress.

Note: the research process loads its own PaddleOCR, so an OCR test running
at the same time as a Logbook Reader upload makes both slower (they do not
share the main app's OCR_LOCK).
"""
import json
import os
import subprocess
import sys
import threading
import time

from research_tests import REPO, output_dir

_jobs = {}
_lock = threading.Lock()


def _paths(key):
    folder = output_dir(key)
    return folder / "progress.json", folder / "run.log"


def running(key):
    job = _jobs.get(key)
    return bool(job and job["proc"].poll() is None)


def start(key, args):
    """Start python -m research_tests.<key> with args. Returns False when
    that test is already running."""
    with _lock:
        if running(key):
            return False
        progress, log = _paths(key)
        progress.write_text(json.dumps({"test": key, "state": "waiting", "fraction": 0, "message": "Starting",
                                        "started": time.time()}), encoding="utf-8")
        env = dict(os.environ, RESEARCH_PROGRESS_FILE=str(progress), PYTHONIOENCODING="utf-8")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        handle = open(log, "w", encoding="utf-8")
        proc = subprocess.Popen([sys.executable, "-m", f"research_tests.{key}", *args], cwd=str(REPO), env=env,
                                stdout=handle, stderr=subprocess.STDOUT, creationflags=flags)
        _jobs[key] = {"proc": proc, "log": handle, "started": time.time(), "args": args}
        return True


def cancel(key):
    job = _jobs.get(key)
    if job and job["proc"].poll() is None:
        job["proc"].terminate()
        progress, _ = _paths(key)
        progress.write_text(json.dumps({"test": key, "state": "failed", "message": "Cancelled"}), encoding="utf-8")
        return True
    return False


def status(key):
    """The run's progress record, with a crashed process reported as failed
    (with the end of its log)."""
    progress, log = _paths(key)
    try:
        record = json.loads(progress.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = {"state": "idle"}
    job = _jobs.get(key)
    if job:
        code = job["proc"].poll()
        if code is not None:
            try:
                job["log"].close()
            except Exception:
                pass
            if record.get("state") in ("running", "waiting"):
                tail = ""
                try:
                    tail = log.read_text(encoding="utf-8", errors="replace")[-1500:]
                except OSError:
                    pass
                record = {**record, "state": "failed", "message": f"The test stopped (exit code {code}).",
                          "log": tail}
    return record
