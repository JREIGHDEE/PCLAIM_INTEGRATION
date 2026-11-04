# Research tests — setup on a new laptop

This guide takes a fresh clone to a working **Testing → OCR comparison** page
with the research tabs, and to a `check_setup` that passes. It's written for
a groupmate who hasn't seen the code; follow it top to bottom. Allow about
45 minutes, most of it installs.

You need Windows 10/11 and internet for the installs only. The tests
themselves run offline.

---

## 1. Install (once)

| What | Version | Where |
|---|---|---|
| Git | any | https://git-scm.com |
| Python | **3.12.1, 64-bit** (tick "Add python.exe to PATH") | https://www.python.org/downloads/release/python-3121/ |
| XAMPP | any current (we use its MariaDB) | https://www.apachefriends.org |
| Tesseract OCR | **5.4.0.20240606** (UB Mannheim Windows build) | https://github.com/UB-Mannheim/tesseract/wiki |
| Microsoft Edge | already on Windows | — |

The OCR models (PaddleOCR), the logbook setups and pdf-lib are already in the
repository, so there's nothing else to download.

## 2. Get the code

```
git clone https://github.com/JREIGHDEE/PCLAIM_INTEGRATION.git
cd PCLAIM_INTEGRATION
git checkout research-testing
git config core.hooksPath .githooks
```

The last line turns on the project's commit checks, including the one that
refuses session files containing names.

## 3. Python environment

From the repository folder:

```
cd Ocr_module
python -m venv venv
venv\Scripts\pip.exe install -r requirements.txt
venv\Scripts\pip.exe install -r ..\research_tests\requirements.txt
cd ..
```

(`Ocr_module\setup_ocr.bat` creates the venv too; the second `pip` line is
still needed for the research tests.)

## 4. Databases (XAMPP)

Start **MySQL** in the XAMPP Control Panel. There are two databases: the
clinic app's and the research one.

**a) The clinic app's database** (so the website runs the same as on the
lead's laptop). In phpMyAdmin (http://localhost/phpmyadmin), on the SQL tab,
as root:

1. Import `database/schema.sql`. It creates `pclaimassist_db`.
2. Select `pclaimassist_db`, then import every file in `database/migrations/`
   in number order, `001_...` to `012_...`. All of them are safe to run twice.
3. Create your own sign-in account:
   `Ocr_module\venv\Scripts\python.exe Ocr_module\create_admin.py`.
   No accounts are shared between laptops.

This database starts empty: no patients, and no learned OCR rows.

**b) The research database** (what the tests read):

```
Ocr_module\venv\Scripts\python.exe -m research_tests.setup.import_seed
```

It creates `pclaimassist_research` with the system's starter rows only
(migrations 006–008: 121 correction patterns, 99 known entries). It also gives
the app account read access and checks the rows against the project's
checksums. It should end with **"Seed matches the project's: PASS"**. If your
MariaDB root has a password, add `--password YOURPASSWORD`.

## 5. Settings (`Ocr_module\.env`)

```
copy Ocr_module\.env.example Ocr_module\.env
```

Then open `Ocr_module\.env` in a text editor and check three things:
- `DB_USER` / `DB_PASSWORD`: root and an empty password on a fresh XAMPP.
- `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe` (where the
  installer put it).
- `ENABLE_RESEARCH_TESTS=true` and `RESEARCH_DB_NAME=pclaimassist_research`
  (already in the example).

Never commit `.env`; it's git-ignored. The first start creates
`Ocr_module\.secret_key` and `.data_key` by itself; never commit those either.

## 6. Start the system

Double-click `PClaimAssist.bat`. Or, for development:
`cd Ocr_module` then `venv\Scripts\python.exe app.py`.

Open http://127.0.0.1:5000, sign in with the account from step 4a, and go to
**Testing → OCR comparison**. Press **Ctrl+F5** once. The research tabs
(Handwriting, Correction Metrics, Field Mapping, Validation, Performance, Image
Quality, User Sessions, Results) appear beside "OCR comparison".

> `PClaimAssist.bat` sets `OCR_DEBUG=false` but not `ENABLE_RESEARCH_TESTS`.
> The tabs come from your `.env`. On the clinic's own computer, leave the
> flag out of `.env` (or set it to `false`) and they disappear.

## 7. Check that your setup matches

```
Ocr_module\venv\Scripts\python.exe -m research_tests.check_setup
```

It takes a few minutes. You should see **PASS** for Python, the packages,
Tesseract, the model files, the logbook setups, pdf-lib, the research
database, the test inputs and the W03 smoke test. WARN for Edge is fine: Edge
updates itself, and the version is recorded with each result. For every
FAIL, it prints the fix.

If only the smoke test fails with a handful of differing cells, the other
items pass, and your processor differs from the lead's, PaddleOCR may read a
few cells differently on your CPU. Send the printed list to the project lead.
The final numbers come from the lead's machine anyway (see TASKS.md).

## 8. Your part

See **TASKS.md** for who runs what, and the one file each groupmate edits.
README.md describes every test and its inputs.

---

### Troubleshooting

| Problem | Fix |
|---|---|
| The tabs don't appear | `ENABLE_RESEARCH_TESTS=true` in `Ocr_module\.env`, restart the server, then Ctrl+F5. Tabs are for administrator accounts only. |
| "The research database pclaimassist_research could not be read" | Start MySQL in XAMPP and run step 4b again |
| "Access denied … pclaimassist_research" | Run step 4b again: it grants the account in your `.env` read access |
| `playwright` / msedge errors | `Ocr_module\venv\Scripts\pip.exe install playwright==1.64.1`, and make sure Edge is installed |
| Tesseract "not available" | Install 5.4.0.20240606 and set `TESSERACT_CMD` in `.env` |
| A commit is refused for session data | Use participant codes P1–P5 only, and remove names, recordings and consent forms |
