# PClaimAssist + OCR — Groupmate Setup Guide

This repo has two parts that run as **separate processes** and talk to each
other over HTTP:

```
YD PCLAIM/               (this repo)
├── PClaimAssist/          the frontend — static HTML/CSS/JS, no backend of its own
└── Ocr_module/             the OCR backend — Python + Flask + PaddleOCR
```

You need **both** running at the same time to use the OCR feature. PClaimAssist's
other pages (Dashboard, CSF, CF2, CF3, PMRF) work fine with just the frontend.

---

## 0. Prerequisites (install once, system-wide)

- **Python 3.12** — https://www.python.org/downloads/ (check "Add Python to PATH" during install)
- **VS Code** with the **Live Server** extension (by Ritwick Dey) — used to run the PClaimAssist frontend
- **Git**

---

## 1. Get the code

```
git clone https://github.com/JREIGHDEE/PCLAIM_INTEGRATION.git "YD PCLAIM"
cd "YD PCLAIM"
```

If you already have an older copy of just `PClaimAssist/` from before, don't try to
patch it — delete that old folder and clone this repo fresh instead, so you get
`Ocr_module/` and the current `PClaimAssist/` together, in sync.

Open the **`YD PCLAIM`** folder itself in VS Code (not just the `PClaimAssist`
subfolder) — a shared `.vscode/settings.json` at that level fixes a real bug
(see step 5) and only applies if that's your open workspace root.

---

## 2. One-time OCR backend setup

```
cd Ocr_module
setup_ocr.bat
```

This creates a local `venv/` folder and installs everything `Ocr_module` needs
(Flask, PaddleOCR, PaddlePaddle, OpenCV, etc.) **inside that folder only** —
nothing is installed system-wide. This step downloads a few hundred MB
(PaddlePaddle is large) and can take several minutes. The window stays open
when it's done (or if it fails) — read it before closing.

Run this **once per machine**. You don't need to repeat it just to start the
server later.

---

## 3. Running it day-to-day

Two things need to be running at once, in two separate windows:

### 3a. Start the OCR backend
```
cd Ocr_module
run_ocr.bat
```
Leave this window open — it's the server. You should see:
```
* Running on http://127.0.0.1:5000
```
If this window closes immediately or shows an error, read the error text (it
now stays open with a "Press any key to continue" prompt instead of vanishing)
and see Troubleshooting below.

### 3b. Start the PClaimAssist frontend
In VS Code, right-click `PClaimAssist/index.html` → **Open with Live Server**.
It should open at `http://127.0.0.1:5500/index.html`.

---

## 4. Confirm it all works

1. Dashboard loads, sidebar navigation between Dashboard / CSF / CF2 / CF3 / PMRF works.
2. Click **OCR Extraction** in the sidebar → you should land on `ocr.html` and
   see the full OCR workspace (Upload panel, Crop Area, etc.) load *inside* that
   page within a couple of seconds.
3. Upload any image (PDF or PNG/JPG) via that OCR workspace and try the OCR
   buttons — it should return recognized text.

If step 2 shows a spinner forever or an error saying it can't reach the OCR
backend, go back and make sure `run_ocr.bat` (step 3a) is actually still running.

---

## 5. Important gotcha: Live Server must be scoped correctly

The repo includes `.vscode/settings.json` (committed on purpose) that tells
Live Server to only serve/watch `PClaimAssist/`, not the whole repo. **This
matters**: every time you use the OCR tool, the backend writes files into
`Ocr_module/uploads/`. If Live Server is watching the whole repo instead of
just `PClaimAssist/`, it sees those writes as "a file changed" and force-reloads
your browser tab mid-use — which looks like the OCR page randomly refreshing
itself.

This is already fixed **as long as you open `YD PCLAIM` (not `PClaimAssist`) as
your VS Code workspace folder**, so the settings file applies. If you ever see
the OCR page unexpectedly refresh itself:
1. Confirm your VS Code workspace root is `YD PCLAIM`, not `PClaimAssist`.
2. Stop Live Server (status bar → "Port : 5500" → Stop Live Server).
3. `Ctrl+Shift+P` → "Developer: Reload Window".
4. Re-open with Live Server.

---

## Troubleshooting

**`run_ocr.bat` window shows an error and closes / "No virtual environment found"**
→ You skipped step 2, or it failed partway. Run `setup_ocr.bat` again — it's
safe to re-run.

**`ModuleNotFoundError` when the server starts**
→ The venv install didn't fully finish. Re-run `setup_ocr.bat`, or manually:
```
cd Ocr_module
venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Server won't start / "port already in use"**
→ Something else is already using port 5000. Close any other `run_ocr.bat`
window you may have left open, or check Task Manager for a stray `python.exe`.

**Running `python app.py` directly instead of `run_ocr.bat`**
→ Don't — a plain terminal's `python` usually points at your system-wide
Python, which doesn't have any of the OCR dependencies installed (by design —
we never install PaddleOCR globally). Always use `run_ocr.bat`, or explicitly
call `Ocr_module\venv\Scripts\python.exe app.py`.

**Live Server shows "Cannot GET /index.html"**
→ Live Server is running with the wrong root folder (see step 5) — usually
because your VS Code workspace is opened at `PClaimAssist/` instead of
`YD PCLAIM/`, or Live Server was started before the settings file existed.
Stop it, reload the window, start it again.

**OCR page keeps refreshing itself while you're using it**
→ See step 5.

---

## What NOT to commit

`venv/`, `uploads/`, `debug_cells/`, `__pycache__/` under `Ocr_module/` are all
git-ignored on purpose — they're either machine-specific (the venv) or
generated data from using the tool locally. Don't force-add them.
