"""Progress of one test run: printed on the command line and, when the web
tab started the run (web/jobs.py sets RESEARCH_PROGRESS_FILE), written to a
small JSON file the tab polls."""
import json
import os
import sys
import time


class Progress:
    def __init__(self, test_key):
        self.test_key = test_key
        self.path = os.environ.get("RESEARCH_PROGRESS_FILE")
        self.started = time.time()
        self._last_print = 0.0
        self._write(state="running", fraction=0.0, message="Starting")

    def _write(self, **fields):
        if not self.path:
            return
        record = {"test": self.test_key, "started": self.started, "updated": time.time(), **fields}
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(record, fh)
        os.replace(tmp, self.path)

    def __call__(self, fraction, message):
        fraction = max(0.0, min(1.0, float(fraction)))
        self._write(state="running", fraction=fraction, message=message)
        now = time.time()
        if now - self._last_print > 1.0 or fraction >= 1.0:
            print(f"[{self.test_key}] {fraction * 100:5.1f}%  {message}", flush=True)
            self._last_print = now

    def done(self, outputs, summary_rows=None):
        self._write(state="done", fraction=1.0, message="Done", outputs=[str(p) for p in outputs],
                    seconds=round(time.time() - self.started, 1), summary=summary_rows or [])
        for p in outputs:
            print(f"[{self.test_key}] wrote {p}", flush=True)

    def fail(self, error):
        self._write(state="failed", message=str(error))
        print(f"[{self.test_key}] FAILED: {error}", file=sys.stderr, flush=True)
