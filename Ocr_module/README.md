# PClaimAssist OCR Service

Standalone Flask + PaddleOCR backend used for template-based extraction from
scanned PhilHealth forms, plus a browser-based calibration UI for building
and correcting extraction templates. This service is intentionally separate
from the PClaimAssist frontend (a static HTML/CSS/JS app) — they communicate
over HTTP, not by being merged into one codebase.

## Requirements

- **Python 3.12** (the project was built and tested against 3.12.1)
- Windows (the provided `.bat` scripts are Windows-specific; the app itself
  is pure Python and runs anywhere Python + the dependencies below run)

## First-time setup

From this folder (`Ocr_module/`):

```
setup_ocr.bat
```

This creates a local `venv/` (nothing is installed globally — PaddleOCR and
PaddlePaddle stay isolated inside this project) and installs everything
pinned in `requirements.txt` into it.

Optional: copy `.env.example` to `.env` and adjust host/port/CORS/upload
limits. Nothing in `.env.example` is a secret; every value has a sensible
default in `config.py` if you skip this step.

## Starting the server

```
run_ocr.bat
```

This works from any directory — it locates the project folder itself and
uses `venv\Scripts\python.exe` directly, so **you never need to run
`Activate.ps1` manually**. By default the server listens on
`http://127.0.0.1:5000`.

Run the PClaimAssist frontend separately (e.g. VS Code Live Server, default
`http://127.0.0.1:5500`) — the two are independent processes. `OCR_ALLOWED_ORIGINS`
in `config.py` / `.env` controls which frontend origin(s) may call this API.

## Testing the API

With the server running, from a second terminal:

```
curl -X POST http://127.0.0.1:5000/api/ocr -F "image=@path\to\a\scan.png"
```

Or open `http://127.0.0.1:5000/` in a browser for the calibration UI, which
exercises every endpoint interactively.

## Running the test suite

```
venv\Scripts\python.exe -m unittest test_template_matching.py
```

## Project layout

```
app.py                 Flask app factory + startup (thin entrypoint)
config.py               All configuration (paths, host/port, CORS, limits)
errors.py                Custom exceptions + centralized JSON error handling
logging_setup.py          Logging configuration
ocr_engine.py              PaddleOCR wrapper (lazy-loaded singleton model)
template_engine.py          Template-matching / grid-detection algorithms
template_store.py            Grid template + case-session persistence (JSON files)
batch_processor.py            Batch PDF processing using a saved template
routes/
  ocr_routes.py                /ocr, /api/ocr, /save_reviewed_result, /export_case_session
  template_routes.py            grid template CRUD + /match_template
  layout_routes.py               row/column/line detection, alignment, batch PDF
  crop_routes.py                  /save_crop (training data capture)
utils/uploads.py                   shared upload validation + temp-file handling
templates/index.html                 calibration UI (Cropper.js-based, standalone)
uploads/                              generated data (grid templates, sessions, training crops)
```

## Notes

- All existing endpoints keep their original paths and JSON response shapes
  (see `templates/index.html`, which calls them directly). `/api/ocr` is a
  REST-style alias of `/ocr` added for the PClaimAssist integration.
- PClaimAssist's `ocr.html` page shows this app's `templates/index.html`
  live inside an `<iframe>` pointed at `http://127.0.0.1:5000/` — this
  backend must be running for that page to work. Nothing is copied; the UI
  served here is the single source of truth.
- Error responses are always JSON — `{"success": false, "error": "...",
  "error_code": "..."}` — never a raw Python traceback, even with
  `OCR_DEBUG=true`.
- The venv shipped in this copy was created for this project. If you clone
  this repo fresh elsewhere, always run `setup_ocr.bat` rather than reusing
  a copied `venv/` folder — a venv is not portable between machines/paths.
