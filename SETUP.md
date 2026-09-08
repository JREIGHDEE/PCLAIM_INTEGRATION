# PClaimAssist + OCR — Groupmate Setup Guide

This guide gets you from "just cloned the repo" to a fully working local copy
of **PClaimAssist** (frontend), the **OCR backend** (Flask), and the
**MariaDB database** (Phase 1). Follow it top to bottom in order — don't skip
sections even if you think you already have something installed.

You do **not** need prior backend, Python, Git, or database experience to
follow this. Every command is given exactly as you should type it.

```
YD PCLAIM/                    (this repo)
├── PClaimAssist/               the frontend — static HTML/CSS/JS, no backend of its own
├── Ocr_module/                  the OCR backend — Python + Flask + PaddleOCR + MariaDB
└── database/
    └── schema.sql                 the approved database schema (8 tables)
```

---

## PART 1 — Before Starting: What to Install

Install these once, system-wide, before touching the project:

| Software | Why you need it | Where to get it |
|---|---|---|
| **Git** | To clone the repo and share code with the team | https://git-scm.com/downloads |
| **Python 3.12** | Runs the Flask/OCR backend (`Ocr_module/`) | https://www.python.org/downloads/ — during install, **check "Add python.exe to PATH"** |
| **XAMPP** | Gives you MariaDB (the database server) + phpMyAdmin (a web UI to view/edit the database) | https://www.apachefriends.org/download.html |
| **VS Code** with the **Live Server** extension (by Ritwick Dey) | Runs the PClaimAssist frontend | https://code.visualstudio.com/ |

You do **not** need to install PHP, MySQL Workbench, or any Python packages
manually right now — those come later via a setup script, and PHP isn't used
by this project's backend at all (XAMPP is only used here for its MariaDB
server + phpMyAdmin).

---

## PART 2 — Cloning the Project

1. Open a terminal. On Windows, search the Start Menu for **PowerShell** and
   open it.
2. Pick a folder to keep your projects in, and move into it. For example:
   ```powershell
   cd "$HOME\Documents"
   ```
3. Clone the repository:
   ```powershell
   git clone https://github.com/JREIGHDEE/PCLAIM_INTEGRATION.git "YD PCLAIM"
   ```
   This creates a new folder called `YD PCLAIM` containing the whole project.
4. Move into it and open it in VS Code:
   ```powershell
   cd "YD PCLAIM"
   code .
   ```
   Always open the **`YD PCLAIM`** folder itself as your VS Code workspace —
   not just the `PClaimAssist` or `Ocr_module` subfolder. A shared
   `.vscode/settings.json` at that level fixes a real Live Server bug (see
   Part 6) and only applies if `YD PCLAIM` is your open workspace root.

If you already have an older copy of just `PClaimAssist/` from before this
database integration, don't try to patch it — delete that old folder and use
this fresh clone instead, so `Ocr_module/`, `database/`, and `PClaimAssist/`
are all in sync.

---

## PART 3 — Python Environment

The OCR backend uses its own **isolated virtual environment** (a private
copy of Python + packages, kept inside `Ocr_module/venv/`, that doesn't
touch your system-wide Python). You don't create this by hand — a script
does it for you — but it's worth understanding what's happening so you can
troubleshoot if it fails.

### 3.1 Check Python is installed correctly

```powershell
python --version
```

You should see something like `Python 3.12.x`. If instead you get an error,
or a Microsoft Store window pops up, see **Troubleshooting** (Part 9) —
Windows sometimes points `python` at a fake Microsoft Store placeholder
instead of a real install.

### 3.2 Run the one-time setup script

From the `YD PCLAIM` folder:

```powershell
cd Ocr_module
.\setup_ocr.bat
```

This does two things automatically:
1. Creates the virtual environment: `python -m venv venv`
2. Installs every package pinned in `requirements.txt` into it, using:
   ```
   venv\Scripts\python.exe -m pip install --upgrade pip
   venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
   (Note the `python -m pip` form, not a bare `pip` — this guarantees the
   install goes into the venv's Python, not whatever `pip` happens to
   resolve to on your PATH.)

This downloads several hundred MB (PaddleOCR/PaddlePaddle are large) and can
take several minutes. The window stays open when done — read it before
closing, in case something failed partway.

Run this **once per machine**. You don't need to repeat it just to start the
server later.

### 3.3 Activating the environment manually (optional)

`run_ocr.bat` (Part 6) calls `venv\Scripts\python.exe` directly, so you
**never need to manually activate** the environment for normal use. But if
you ever want an interactive terminal where plain `python`/`pip` refer to
this project's venv (e.g. to run a one-off command), activate it with:

```powershell
cd Ocr_module
.\venv\Scripts\Activate.ps1
```

Your prompt should now start with `(venv)`. If PowerShell refuses to run the
script with a message about "execution policies", run this once first, then
retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

To leave the venv: `deactivate`.

### 3.4 Troubleshooting: `python` points to the wrong thing

If `python --version` opens the Microsoft Store, or shows a very different
version than 3.12, Windows' "App execution alias" is intercepting it. Fix:

1. Open **Settings → Apps → Advanced app settings → App execution aliases**.
2. Turn **off** the `python.exe` / `python3.exe` toggles under "App
   Installer".
3. Re-install Python from https://www.python.org/downloads/, making sure
   **"Add python.exe to PATH"** is checked.
4. Open a **new** PowerShell window (PATH changes don't apply to already-open
   windows) and re-check `python --version`.

If your machine has multiple Python versions installed, the Python launcher
can target the right one explicitly:
```powershell
py -0
py -3.12 -m venv venv
```

---

## PART 4 — Database Setup (MariaDB via XAMPP)

The project's approved schema lives in one file: **`database/schema.sql`**
(at the repo root, not inside `Ocr_module/`). It defines 8 tables:
`patients`, `case_sessions`, `encounters`, `claims`,
`claim_prenatal_visits`, `claim_postpartum_care`, `research_ground_truth`,
`research_ocr_results`. Don't hand-edit this file or the tables it creates —
just import it as-is.

### 4.1 Start MariaDB

1. Open the **XAMPP Control Panel**.
2. Click **Start** next to **MySQL** (XAMPP's MySQL slot is actually running
   MariaDB — that's normal and is what this project uses).
3. Wait until it turns green.

If it fails to start with a port-conflict error, see **Troubleshooting**
(Part 9) — this usually means something else (often a separately-installed
MySQL/MariaDB service) already owns port 3306.

### 4.2 Open phpMyAdmin

Click **Admin** next to MySQL in the XAMPP Control Panel (or open
`http://localhost/phpmyadmin` in a browser).

### 4.3 Import the schema

1. In phpMyAdmin, click **Import** in the top navigation (make sure you're
   at the top level — not already inside a specific database).
2. Click **Choose File**, and select `database/schema.sql` from your cloned
   repo.
3. Leave the other options at their defaults and click **Go**.

The script itself contains `CREATE DATABASE IF NOT EXISTS pclaimassist_db`,
so this one Import both creates the database and every table in it — you
don't need a separate "create database" step first.

### 4.4 Verify the tables

In phpMyAdmin's left sidebar, click into **`pclaimassist_db`**. You should
see exactly these 8 tables:

```
case_sessions
claim_postpartum_care
claim_prenatal_visits
claims
encounters
patients
research_ground_truth
research_ocr_results
```

If you see fewer than 8, the import failed partway — check phpMyAdmin's
message after clicking Go, fix the reported error, and re-import.

### 4.5 Create the application database user

The Flask backend connects as a dedicated (non-root) MariaDB user rather
than `root`, named **`pclaimassist_app`**. This user isn't created by
`schema.sql` — you need to create it once on your own machine, exactly like
the project lead did on theirs. In phpMyAdmin:

1. Click **User accounts** (top navigation) → **Add user account**.
2. Username: `pclaimassist_app`, Host name: **Local** (`localhost`).
3. Password: choose one. Since this account only exists on *your own*
   machine (your `.env` file is local and never shared — see Part 5), it
   does **not** need to match anyone else's password. Either pick your own,
   or use `YOUR_SHARED_DATABASE_PASSWORD` as a placeholder to agree on a
   team convention — check with your project lead if you're unsure which
   your group prefers.
4. Under **Database for user**, choose **"Grant all privileges on database
   `pclaimassist_db`"**.
5. Click **Go**.

Equivalent raw SQL, if you prefer running it via phpMyAdmin's **SQL** tab
instead of the form above:

```sql
CREATE USER 'pclaimassist_app'@'localhost' IDENTIFIED BY 'YOUR_SHARED_DATABASE_PASSWORD';
GRANT ALL PRIVILEGES ON pclaimassist_db.* TO 'pclaimassist_app'@'localhost';
FLUSH PRIVILEGES;
```

Replace `YOUR_SHARED_DATABASE_PASSWORD` with the actual password you chose.
Whatever you pick here is exactly what goes into your local `.env` in the
next part.

---

## PART 5 — `.env` Setup

The backend reads its database connection settings from a file at
**`Ocr_module/.env`**. This file does not exist in a fresh clone — you
create it yourself from the provided example.

### 5.1 Copy the example file

From inside `Ocr_module/`:

```powershell
Copy-Item .env.example .env
```

### 5.2 Edit the Database section

Open the new `Ocr_module/.env` in VS Code and set its **Database** block to
match what you just set up in Part 4:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=pclaimassist_db
DB_USER=pclaimassist_app
DB_PASSWORD=YOUR_SHARED_DATABASE_PASSWORD
DB_CONNECT_TIMEOUT=5
```

Two things to check carefully:

- **`DB_PORT`** — most fresh XAMPP installs use `3306`. Only change this if
  your MariaDB is actually listening on a different port (for example, some
  machines run `3307` because another MySQL install already occupies
  `3306`). To check your actual port, look at the **MySQL** row in the
  XAMPP Control Panel, or check `phpMyAdmin → localhost:PORT` in the URL
  after logging in.
- **`DB_PASSWORD`** — use the exact password you set when creating
  `pclaimassist_app` in Part 4.5. Never put a real shared production
  password in `.env.example` or any file you commit — only in your own
  local `.env`.

Everything else in `.env.example` (server host/port, CORS origins, upload
limits) already has a working default — you don't need to touch it.

### 5.3 Why this file is special

- `.env` is **local to your machine only**.
- `.env` is listed in `.gitignore` — Git will never track it, and `git
  status` should never show it as a changed/new file.
- **Never** commit `.env`, and never paste a real password into a commit,
  issue, or chat message that isn't private to the team.
- Each group member has their **own** `.env` with their **own** local
  database credentials — they don't need to be identical across machines.

---

## PART 6 — Starting the Backend

From `Ocr_module/`:

```powershell
.\run_ocr.bat
```

This uses `venv\Scripts\python.exe` directly — you never need to manually
activate the venv to start the server this way. Leave this window open; it
**is** the running server. A successful start looks like:

```
Starting PClaimAssist OCR service from ...
* Running on http://127.0.0.1:5000
```

### Test the database connection

With the server running, open a **second** PowerShell window and run:

```powershell
curl http://127.0.0.1:5000/db_health
```

Note: in PowerShell, `curl` is actually an alias for `Invoke-WebRequest`,
which prints a lot of extra header/status noise around the JSON. If you'd
rather see just the JSON response, use PowerShell's native equivalent
instead:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/db_health
```

A successful response looks like:

```json
{
  "success": true,
  "database": "pclaimassist_db",
  "server_version": "10.4.32-MariaDB"
}
```

If `success` is `true` and `database` says `pclaimassist_db`, your backend
is correctly talking to your local database. If not, see Part 9.

---

## PART 7 — Testing the Database with the Diagnostic Route

The backend currently includes a **temporary** diagnostic endpoint used to
verify the database write path independently of any real feature:

```
POST /diagnostic/patient_crud_test
```

### 7.1 What it does

It inserts one clearly-marked test row into the `patients` table (last name
`ZZ_DIAGNOSTIC_TEST`, a made-up birthdate, and a timestamped `pin`), then
immediately reads that same row back and returns it — proving Flask can
both write to and read from MariaDB.

### 7.2 Call it

With the backend running:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/diagnostic/patient_crud_test
```

### 7.3 What success looks like

```json
{
  "success": true,
  "inserted_id": 3,
  "message": "Inserted and retrieved one test patient row. Verify it in phpMyAdmin: ...",
  "patient": {
    "id": 3,
    "last_name": "ZZ_DIAGNOSTIC_TEST",
    "first_name": "CRUD_TEST",
    "pin": "DTEST-...",
    ...
  }
}
```

### 7.4 Verify in phpMyAdmin

Open `pclaimassist_db` → `patients` → **Browse**, and look for the row with
the `id` from `inserted_id` (or filter/search for `last_name =
ZZ_DIAGNOSTIC_TEST`). You can safely delete these test rows afterward —
nothing else in the app reads them.

### 7.5 Remember: this route is temporary

`routes/diagnostic_routes.py` (and its one-line registration in
`routes/__init__.py`) exists purely for this manual verification step. It
should be **removed before final submission/production** — flag this to
whoever owns final cleanup if it's still present near your deadline.

---

## PART 8 — Testing Phase 1 OCR Persistence

This confirms that reviewing and saving an OCR result actually writes to
the `case_sessions` table in MariaDB (instead of the old JSON-file
approach), and that exporting still works from that database data.

### 8.1 Open the OCR workspace

Two ways to reach it (both require `run_ocr.bat` to be running):

- **Through PClaimAssist:** open `PClaimAssist/index.html` with Live Server,
  then click **OCR Extraction** in the sidebar. It loads the OCR workspace
  live inside the page.
- **Directly:** open `http://127.0.0.1:5000/` in a browser — this is the
  exact same workspace, served straight from the Flask backend.

### 8.2 Process a case and review results

1. Upload any scanned image or PDF and run OCR on it (the existing upload/
   crop/extract flow — unchanged by this database work).
2. In the **Review & Edit** section, type something into the **Case ID**
   field (e.g. `TESTCASE-001`) and optionally a **Case Name**.
3. Edit any of the extracted text values directly in the table if you like.

### 8.3 Save and verify

1. Click **Save Reviewed Result**. You should see a green **"Saved to case
   session."** message.
2. In phpMyAdmin, open `pclaimassist_db` → `case_sessions` → **Browse**.
   Find the row where `logbook_case_number` matches the Case ID you typed
   (e.g. `TESTCASE-001`) — its `reviewed_values` column holds your edited
   values as JSON.

### 8.4 Confirm updates don't duplicate

1. Go back to the same Case ID, change one of the values, and click **Save
   Reviewed Result** again.
2. Refresh the `case_sessions` browse view in phpMyAdmin. You should still
   see only **one row** for that Case ID — same `id`, but `reviewed_values`
   updated and `reviewed_at` bumped to the new save time. It must **not**
   create a second row.

### 8.5 Test export

Click **Export Case to Excel**. It should download an `.xlsx` file whose
contents match the values currently stored in `case_sessions` for that Case
ID (this button also re-saves your current edits first, then downloads).

---

## PART 9 — Troubleshooting

| Problem | What's happening | Fix |
|---|---|---|
| `pip` is not recognized | `pip` alone isn't reliably on PATH, especially inside a venv context | Always use `python -m pip ...`, or fully: `Ocr_module\venv\Scripts\python.exe -m pip ...` |
| `python` points to the wrong install / opens Microsoft Store | Windows' App Execution Alias is intercepting `python` | See Part 3.4 — disable the alias in Settings, reinstall Python with "Add to PATH" checked, open a new terminal |
| `ModuleNotFoundError: No module named flask` (or `pymysql`, etc.) | The venv's dependency install didn't finish, or you're running the wrong `python.exe` | Re-run `Ocr_module\setup_ocr.bat`, or manually: `Ocr_module\venv\Scripts\python.exe -m pip install -r Ocr_module\requirements.txt` |
| Running `python app.py` directly instead of `run_ocr.bat` | A plain terminal's `python` is your system-wide Python, which doesn't have the project's dependencies installed (by design) | Always use `run_ocr.bat`, or explicitly call `Ocr_module\venv\Scripts\python.exe app.py` |
| Flask cannot connect to the database / `/db_health` says unable to connect | MariaDB isn't running, or `.env` doesn't match your local setup | Confirm MySQL is green in the XAMPP Control Panel; double-check `DB_HOST`/`DB_PORT`/`DB_USER`/`DB_PASSWORD` in `Ocr_module\.env` |
| `Access denied for user 'pclaimassist_app'@...` | Wrong password in `.env`, or the user wasn't granted privileges on `pclaimassist_db` | Re-check the password matches what you set in phpMyAdmin (Part 4.5); re-run the `GRANT ALL PRIVILEGES` statement |
| MariaDB is running on a different port than expected | Some machines have MariaDB on `3307` (or another port) instead of the default `3306`, often because another MySQL service already used `3306` | Check the **MySQL** row's port in the XAMPP Control Panel and set `DB_PORT` in `.env` to match |
| XAMPP says port 3306 is already in use | Another MySQL/MariaDB service (or a previous XAMPP session) is already using that port | In XAMPP Control Panel, click **Config → my.ini** for MySQL and change the `port=` line to an unused port (e.g. `3307`), then update `DB_PORT` in `.env` to match; or stop the other service using port 3306 |
| `.env` changes aren't taking effect | The server process only reads `.env` once, at startup | Stop `run_ocr.bat` (Ctrl+C or close the window) and start it again — Flask must be restarted after any `.env` change |
| Live Server shows "Cannot GET /index.html" | Live Server's root folder is wrong — usually because VS Code's workspace is opened at `PClaimAssist/` instead of `YD PCLAIM/` | Reopen the `YD PCLAIM` folder as your VS Code workspace, stop Live Server, reload the window, start it again |
| OCR page inside PClaimAssist keeps refreshing itself while you use it | Live Server is watching the whole repo (including `Ocr_module/uploads/`, which changes on every OCR action) instead of just `PClaimAssist/` | Make sure your VS Code workspace root is `YD PCLAIM` (its committed `.vscode/settings.json` scopes Live Server correctly) — reload the window if you opened `PClaimAssist/` directly first |
| `run_ocr.bat` window shows an error and closes / "No virtual environment found" | Setup was skipped or failed partway | Run `Ocr_module\setup_ocr.bat` again — it's safe to re-run |

---

## PART 10 — Git Workflow for Groupmates

Keep this simple and consistent so nobody overwrites each other's work.

1. **Always pull before starting work:**
   ```powershell
   git checkout main
   git pull origin main
   ```
2. **Check which branch you're on:**
   ```powershell
   git branch
   ```
   (the current branch has a `*` next to it)
3. **Create a feature branch before making changes:**
   ```powershell
   git checkout -b your-name/short-description
   ```
4. **Make your changes** in VS Code as normal.
5. **Check what changed before staging anything:**
   ```powershell
   git status
   ```
   Confirm `.env` is **not** listed. If it ever shows up here, something is
   wrong with your `.gitignore` setup — stop and ask before committing.
6. **Stage and commit:**
   ```powershell
   git add <the specific files you changed>
   git commit -m "Short description of what you did"
   ```
   Avoid `git add .` or `git add -A` unless you've just reviewed `git
   status` and are sure everything listed is meant to be committed.
7. **Push your branch:**
   ```powershell
   git push -u origin your-name/short-description
   ```
8. **Open a pull request** on GitHub (or coordinate directly with the group)
   before merging into `main` — don't push directly to `main`.

### Never commit

- `.env` (already gitignored — verify with `git status` anyway)
- Database passwords or personal credentials, anywhere (code, commit
  messages, issues)
- Local database dumps/exports that contain real or sample patient
  information
- The `venv/`, `uploads/`, `debug_cells/`, `__pycache__/` folders under
  `Ocr_module/` — all machine-specific or generated, and already gitignored

---

## PART 11 — Final Pre-Coding Checklist

Work through this before you start making changes:

- [ ] Repository cloned (`YD PCLAIM` opened as VS Code workspace root)
- [ ] `python --version` shows 3.12.x
- [ ] `Ocr_module\setup_ocr.bat` completed without errors
- [ ] XAMPP MySQL (MariaDB) is running (green in XAMPP Control Panel)
- [ ] `database/schema.sql` imported via phpMyAdmin
- [ ] All 8 tables visible in `pclaimassist_db`
- [ ] `pclaimassist_app` database user created with privileges on `pclaimassist_db`
- [ ] `Ocr_module\.env` created from `.env.example` and Database section filled in
- [ ] `run_ocr.bat` starts cleanly and stays open
- [ ] `Invoke-RestMethod http://127.0.0.1:5000/db_health` returns `"success": true`
- [ ] `POST /diagnostic/patient_crud_test` succeeds and the row is visible in phpMyAdmin
- [ ] Save/update/export test in Part 8 works and the row in `case_sessions` updates rather than duplicates

---

## WHAT IS READY NOW

- Flask ↔ MariaDB connection (`GET /db_health`)
- Temporary diagnostic CRUD test against `patients` (`POST
  /diagnostic/patient_crud_test`) — to be removed before final submission
- OCR reviewed-result persistence, fully migrated from JSON session files to
  the `case_sessions` table:
  - `POST /save_reviewed_result` (insert-or-update by Case ID, no duplicates)
  - `GET /export_case_session` (exports from database-stored values)
- The full approved 8-table schema exists and is import-ready
  (`database/schema.sql`)
- OCR extraction, cropping, grid/template calibration, and batch processing
  are all unchanged and still fully file-based (by design — not part of
  this database work)

## WHAT IS NOT IMPLEMENTED YET

These do not exist in the codebase yet — don't assume they work:

- Patient search/create workflow (the `patients` table exists, but nothing
  in the app creates real patient records yet outside the diagnostic test)
- Encounter creation (the `encounters` table exists but nothing writes to it)
- An OCR-to-PClaimAssist import bridge (OCR results stay in `case_sessions`;
  nothing currently pushes them into `patients`/`encounters`/`claims`)
- Claims CRUD (the `claims` table and its related tables — prenatal visits,
  postpartum care — exist in the schema but have no backend routes yet)
- PClaimAssist autosave (the frontend's form state — CSF/CF2/CF3/PMRF — is
  still purely client-side JavaScript with no calls to the backend at all)
- Claim loading from the database into PClaimAssist's forms
- Export status tracking/updates (the `claims.status` column exists —
  `draft`/`ready`/`exported` — but nothing currently transitions it)
- Tesseract/research integration (`research_ground_truth` and
  `research_ocr_results` tables exist in the schema for future OCR-accuracy
  research, but no code reads or writes them yet)
