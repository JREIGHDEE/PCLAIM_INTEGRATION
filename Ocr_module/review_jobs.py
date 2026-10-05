"""Background logbook-reading jobs, so the review page can show progress.

Reading a logbook spread takes about a minute (one PaddleOCR call per cell),
which is too long to leave someone staring at a page with no feedback.
POST /api/review/jobs starts the same work as POST /api/review/upload in a
background thread and returns a job id at once; GET /api/review/jobs/<id>
reports how far along it is ({"state", "progress", "message"}) and, when
finished, the same payload the synchronous upload returns.

Jobs live in this process's memory only - they're a progress channel, not
storage: every result is saved to case_sessions as usual, and a finished
job is forgotten after JOB_TTL_SECONDS. One job reads at a time, because
the shared PaddleOCR model is not safe to call from two threads at once.
"""
import logging
import os
import threading
import time
import uuid

logger = logging.getLogger(__name__)

JOB_TTL_SECONDS = 3600

_jobs = {}
_jobs_lock = threading.Lock()
# Held while reading a logbook - also by the synchronous upload route.
OCR_LOCK = threading.Lock()


def _update(job_id, **changes):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None:
            job.update(changes, updated_at=time.time())


def _forget_old_jobs():
    cutoff = time.time() - JOB_TTL_SECONDS
    with _jobs_lock:
        for job_id in [j for j, job in _jobs.items()
                       if job["state"] in ("done", "failed") and job["updated_at"] < cutoff]:
            del _jobs[job_id]


def start(work, path):
    """Run work(progress) in the background; `path` (the uploaded temp file)
    is deleted when it finishes. work returns the result payload and may
    raise ValueError with a message meant for the person waiting.
    Returns the new job id."""
    _forget_old_jobs()
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {"state": "waiting", "progress": 0.0, "message": "Waiting to start",
                         "result": None, "error": None, "updated_at": time.time()}

    def progress(fraction, message):
        # Leave the last bit for saving, so 100% really means finished.
        _update(job_id, state="running", progress=round(min(fraction, 1.0) * 0.95, 4), message=message)

    def run():
        try:
            with OCR_LOCK:
                progress(0.0, "Starting")
                result = work(progress)
            _update(job_id, state="done", progress=1.0, message="Done", result=result)
        except ValueError as exc:
            _update(job_id, state="failed", message="Could not read the scan", error=str(exc))
        except Exception:
            logger.exception("Logbook reading job %s failed", job_id)
            _update(job_id, state="failed", message="Could not read the scan",
                    error="Something went wrong while reading the scan. Please try again.")
        finally:
            if os.path.exists(path):
                os.remove(path)

    threading.Thread(target=run, name=f"logbook-job-{job_id[:8]}", daemon=True).start()
    return job_id


def get(job_id):
    """A copy of the job's public state, or None."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        return None if job is None else {k: v for k, v in job.items() if k != "updated_at"}
