"""Chapter 5 research tests for PClaimAssist - an isolated testing area.

Nothing in this package changes the main system. It imports the main
modules (Ocr_module/) read-only, never writes a main-site table (every
database connection it opens is READ ONLY - guard.py), and writes only to
research_tests/outputs/. See README.md.

Paths are worked out here so every test and the web tabs agree on them.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # research_tests/
REPO = ROOT.parent                              # the repository
OCR_DIR = REPO / "Ocr_module"                   # the main backend (read-only)
FORMS_DIR = REPO / "PClaimAssist"               # the main frontend (read-only)
INPUTS = ROOT / "inputs"
OUTPUTS = ROOT / "outputs"
WORK = OUTPUTS / "work"                         # crops and runs of the OCR tests
VENDOR = ROOT / "vendor"

# The main backend's modules are imported by name (config, ocr_compare, ...),
# as Ocr_module/app.py does. Appended, so nothing of ours shadows them.
if str(OCR_DIR) not in sys.path:
    sys.path.append(str(OCR_DIR))


def output_dir(test_key):
    """research_tests/outputs/<test>/ (created)."""
    folder = OUTPUTS / test_key
    folder.mkdir(parents=True, exist_ok=True)
    return folder
