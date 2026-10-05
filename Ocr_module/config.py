"""
Central configuration for the OCR service.

Every value can be overridden with an environment variable (or a local `.env`
file — see .env.example) without editing this file. All paths are resolved
relative to THIS file's location, not the process's current working
directory, so behavior is identical whether the app is started via
`run_ocr.bat`, `python app.py`, or `flask run` from any directory.
"""
import os
from pathlib import Path

from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path=BASE_DIR / ".env"):
    """Minimal .env loader (avoids adding python-dotenv as a dependency).

    Real environment variables always take precedence over the file.
    """
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name, default):
    value = os.environ.get(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_int(name, default):
    value = os.environ.get(name)
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _env_float(name, default):
    value = os.environ.get(name)
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


# ── Server ────────────────────────────────────────────────────────────────
HOST = os.environ.get("OCR_HOST", "127.0.0.1")
PORT = _env_int("OCR_PORT", 5000)
DEBUG = _env_bool("OCR_DEBUG", True)

# Frontend origin(s) allowed to call this API, e.g. VS Code Live Server.
# Comma-separated if more than one origin is needed.
CORS_ORIGINS = _env_list(
    "OCR_ALLOWED_ORIGINS",
    ["http://127.0.0.1:5500", "http://localhost:5500"],
)

# The PClaimAssist data-entry page that "Send to Forms" (logbook review)
# opens with ?claim=<id> - Live Server serves PClaimAssist/ at its root.
PCLAIMASSIST_FORMS_URL = os.environ.get("PCLAIMASSIST_FORMS_URL", "http://127.0.0.1:5500/index.html")

# ── Database (MariaDB/MySQL via XAMPP) ──────────────────────────────────────
# Used so far only by case_sessions persistence (Phase 1). Grid templates,
# training crops, and every other OCR storage path stay file-based.
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = _env_int("DB_PORT", 3306)
DB_NAME = os.environ.get("DB_NAME", "pclaimassist_db")
DB_USER = os.environ.get("DB_USER", "root")
# Empty string matches XAMPP's out-of-the-box MySQL/MariaDB root account
# (no password set). This is a default that mirrors that factory setup, not
# a real credential - override it via an environment variable or a local
# .env file (see .env.example) for any other setup. Never hardcode a real
# password here.
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_CONNECT_TIMEOUT = _env_int("DB_CONNECT_TIMEOUT", 5)

# ── Storage paths (always relative to this project's folder) ───────────────
UPLOAD_FOLDER = Path(os.environ.get("OCR_UPLOAD_DIR", BASE_DIR / "uploads"))
TRAINING_FOLDER = UPLOAD_FOLDER / "training"
GRID_TEMPLATES_FOLDER = Path(
    os.environ.get("OCR_TEMPLATES_DIR", BASE_DIR / "grid_templates")
)
DEBUG_CELLS_FOLDER = BASE_DIR / "debug_cells"

# ── OCR engine testing (PaddleOCR vs Tesseract, capstone comparison UI) ─────
# One running workbook that every "save to Excel" call appends rows to -
# never overwritten, so results accumulate across page navigation and across
# uploading new logbook files within the same testing session.
OCR_TESTING_WORKBOOK = Path(
    os.environ.get("OCR_TESTING_WORKBOOK", UPLOAD_FOLDER / "ocr_testing_results.xlsx")
)

# ── Uploads ──────────────────────────────────────────────────────────────
MAX_UPLOAD_MB = _env_int("OCR_MAX_UPLOAD_MB", 20)
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_UPLOAD_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_PDF_EXTENSIONS

# ── Template matching ────────────────────────────────────────────────────
TEMPLATE_MATCH_THRESHOLD = _env_float("OCR_TEMPLATE_MATCH_THRESHOLD", 0.55)

# ── Image quality assessment (advisory only - see image_quality.py) ────────
# Variance-of-Laplacian sharpness score below which an image is flagged as
# blurry. ~100 is the commonly cited rule-of-thumb cutoff for this metric on
# ordinary document/photo content - a reasonable starting default, not a
# value derived from this project's own scanned logbooks yet.
IMAGE_QUALITY_BLUR_THRESHOLD = _env_float("OCR_IMAGE_QUALITY_BLUR_THRESHOLD", 100.0)
# Mean grayscale pixel intensity (0-255) outside which an image is flagged
# as too dark / too bright (overexposed). Same "reasonable starting
# default" caveat as the blur threshold above.
IMAGE_QUALITY_BRIGHTNESS_LOW = _env_float("OCR_IMAGE_QUALITY_BRIGHTNESS_LOW", 60.0)
IMAGE_QUALITY_BRIGHTNESS_HIGH = _env_float("OCR_IMAGE_QUALITY_BRIGHTNESS_HIGH", 200.0)
# A document page is mostly white paper, so a high mean alone is normal (a
# clean, sharp logbook scan measures ~225-236). "Overexposed" therefore also
# requires the ink itself to be washed out: the darkest 0.1% of pixels must
# be lighter than this gray level. Clean logbook scans measured ~53-58 here;
# the same pages blended 65% toward white measured ~184-186.
IMAGE_QUALITY_INK_MAX = _env_float("OCR_IMAGE_QUALITY_INK_MAX", 150.0)

# ── OCR field confidence routing (see logbook_pipeline.route_confidence) ──
# Per-field PaddleOCR confidence (0-1; the lowest token confidence in the
# cell) decides how the review UI treats each field:
#   >= ACCEPT            -> "accepted"   (pre-filled, no check required)
#   >= REVIEW, < ACCEPT  -> "needs_check" (pre-filled, flagged for checking)
#   <  REVIEW / no text  -> "manual_encoding_required" (left empty, must be typed)
# Starting values from the thesis design - calibrate against real logbook
# scans and override via env without touching code.
OCR_CONFIDENCE_ACCEPT = _env_float("OCR_CONFIDENCE_ACCEPT", 0.85)
OCR_CONFIDENCE_REVIEW = _env_float("OCR_CONFIDENCE_REVIEW", 0.65)
# Share of a cell's handwriting that may fall outside every box PaddleOCR
# read before the reading counts as possibly incomplete (it then gets one
# retry with a white margin, and is never auto-accepted if still short).
# PaddleOCR can skip a whole handwritten line - typically one touching the
# crop edge - while scoring the lines it did read 0.95+.
OCR_MISSED_INK_LIMIT = _env_float("OCR_MISSED_INK_LIMIT", 0.2)

# ── Logbook upload -> per-row review sessions (see logbook_pipeline.py) ──
# Cell crops shown next to each field in the review UI.
REVIEW_CROPS_FOLDER = UPLOAD_FOLDER / "review_crops"
# A logbook row needs at least this many non-empty OCR'd fields (across both
# pages of a spread) to count as a patient entry - filters out blank rows and
# stray marks such as page numbers or footer notes.
REVIEW_MIN_FILLED_FIELDS = _env_int("OCR_REVIEW_MIN_FILLED_FIELDS", 2)

# ── Tesseract OCR (benchmarking only - see benchmarks/) ─────────────────
# Path to tesseract.exe. Leave unset to rely on Tesseract being on PATH.
# Only used by ocr_tesseract.py / benchmarks/ - the production PaddleOCR
# pipeline (ocr_engine.py) never reads this.
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")

# ── Training categories (unchanged from the original project) ───────────
TRAINING_CATEGORIES = [
    "CASE #",
    "DATE & TIME OF ADMISSION",
    "NAME",
    "BDAY",
    "ADDRESS",
    "ADMITTING DIAGNOSIS",
    "DATE & TIME OF DELIVERY",
    "FINAL DIAGNOSIS",
    "DATE & TIME OF DISCHARGE",
]
CATEGORY_FOLDERS = {
    category: str(TRAINING_FOLDER / secure_filename(category))
    for category in TRAINING_CATEGORIES
}


# ── PhilHealth claim-form population/export ─────────────────────────────
# Real PhilHealth PDF templates live in the sibling PClaimAssist project
# (checked in there, not duplicated here) - this app only reads them.
PHILHEALTH_FORMS_DIR = Path(
    os.environ.get("PHILHEALTH_FORMS_DIR", BASE_DIR.parent / "PClaimAssist" / "forms")
)

# HCI (health care institution/facility) fields are the same for every claim
# in a single-facility deployment - defaulted here rather than re-typed per
# claim, still editable per-claim via PUT /api/claims/<id>.
DEFAULT_HCI_PAN = os.environ.get("PHILHEALTH_HCI_PAN", "")
DEFAULT_HCI_NAME = os.environ.get("PHILHEALTH_HCI_NAME", "")
DEFAULT_HCI_STREET = os.environ.get("PHILHEALTH_HCI_STREET", "")
DEFAULT_HCI_CITY = os.environ.get("PHILHEALTH_HCI_CITY", "")
DEFAULT_HCI_PROVINCE = os.environ.get("PHILHEALTH_HCI_PROVINCE", "")


def ensure_directories():
    """Create every storage directory this app needs, if missing."""
    for folder in (
        UPLOAD_FOLDER,
        TRAINING_FOLDER,
        GRID_TEMPLATES_FOLDER,
        OCR_TESTING_WORKBOOK.parent,
        REVIEW_CROPS_FOLDER,
    ):
        os.makedirs(folder, exist_ok=True)
    for folder in CATEGORY_FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
