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
    os.environ.get("OCR_TEMPLATES_DIR", UPLOAD_FOLDER / "grid_templates")
)
DEBUG_CELLS_FOLDER = BASE_DIR / "debug_cells"

# ── Uploads ──────────────────────────────────────────────────────────────
MAX_UPLOAD_MB = _env_int("OCR_MAX_UPLOAD_MB", 20)
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_UPLOAD_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_PDF_EXTENSIONS

# ── Template matching ────────────────────────────────────────────────────
TEMPLATE_MATCH_THRESHOLD = _env_float("OCR_TEMPLATE_MATCH_THRESHOLD", 0.55)

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


def ensure_directories():
    """Create every storage directory this app needs, if missing."""
    for folder in (
        UPLOAD_FOLDER,
        TRAINING_FOLDER,
        GRID_TEMPLATES_FOLDER,
    ):
        os.makedirs(folder, exist_ok=True)
    for folder in CATEGORY_FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
