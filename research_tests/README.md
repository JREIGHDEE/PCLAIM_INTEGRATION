# Research tests (Chapter 5)

An isolated testing area for the remaining Chapter 5 evaluations. It uses
the real PClaimAssist modules — OCR, correction, auto-population,
validation, PDF generation — **without changing them**. It writes only to
`research_tests/outputs/`.

| # | Test | Command line | Tab | Equations |
|---|------|--------------|-----|-----------|
| 1 | Handwriting (10 writers) | `python -m research_tests.handwriting` | Handwriting (10 Writers) | exact match, 100 × (1 − CER) |
| 2 | Correction metrics | `python -m research_tests.correction_metrics` | Correction Metrics | 3.2–3.4 |
| 3 | Field mapping | `python -m research_tests.field_mapping` | Field Mapping | 3.6 |
| 4 | Validation (seeded errors) | `python -m research_tests.validation` | Validation (Seeded Errors) | 3.7–3.10 |
| 5 | Performance | `python -m research_tests.performance` | Performance | time per stage |
| 6 | Image quality (IQ-01) | `python -m research_tests.iq_check` | Image Quality | — |
| 7 | User sessions | `python -m research_tests.user_sessions` | User Sessions | 3.11, 3.12, 3.5 |
| — | All of them + the combined workbook | `python -m research_tests.run_all` | — | — |
| — | Combined workbook only | `python -m research_tests.results` | Results | — |

Run the commands **from the repository root** with the backend's Python,
for example:

```
Ocr_module\venv\Scripts\python.exe -m research_tests.run_all
Ocr_module\venv\Scripts\python.exe -m research_tests.handwriting --writers W01,W02
```

Each command takes `--help`. Add `--samples` to any test (except
correction metrics) to run it on the computer-drawn sample data, which
checks that it works before the real inputs are ready. First run:

```
Ocr_module\venv\Scripts\python.exe -m research_tests.make_samples
```

Sample results are marked **SAMPLE DATA** in every workbook. Chapter 5's
numbers must come from the real inputs.

## The tabs

The tabs appear beside **OCR comparison** on the *Testing → OCR comparison*
page (administrators only) when `ENABLE_RESEARCH_TESTS=true` is set in
`Ocr_module/.env` or the environment. The flag is off unless set, and the
clinic launcher `PClaimAssist.bat` does not set it.

Each tab has:
- an inputs list, with upload buttons (files go to `research_tests/inputs/`) and template links;
- the test's options, plus a "use the sample data" tick box;
- a **Run** button;
- a results table and a **Download** link.

A run is a separate background process, so the page and the server stay
free while OCR reads. The **Results** tab builds and downloads
`chapter5_results.xlsx`.

## Inputs (`research_tests/inputs/`)

All data must be fictional. The templates are in the folder. The filled-in
files are git-ignored, so they stay on this computer.

| File | Used by | Format |
|------|---------|--------|
| `answer_key.xlsx` — sheet **Handwriting** | 1 | Writer ID, Style (caps/lower), Page (PDF page), Row (entry line, as the OCR comparison numbers it), Field (Case number, Admitted, Patient name, Birthday, Address, Reason for admission, Delivered, Final diagnosis, Went home), Ground Truth |
| `answer_key.xlsx` — sheet **Patients** | 3, 4 | Confirmed values, about 20 patients: Patient ID, Case number, Last/First/Middle name, Suffix, Birthday, Address, Admitted/Delivered/Went home date + time + AM/PM, Reason for admission, Final diagnosis; optional Street, Barangay, City, Province |
| `writers.csv` | 1 | Writer ID, Style, Set (`main` for W01–W10, `same_writer` for the 3 researchers' pages in both styles), Scan File, Notes |
| `scans/handwriting/*.pdf` | 1, 5 | Scanner (flatbed) scan per writer, `W01_caps.pdf` … `W10_lower.pdf`, on the printed logbook layout |
| `scans/handwriting_phone/*_phone.pdf` | 1, 5 | The same pages taken with a phone scanner app (`W01_caps_phone.pdf` …) |
| `answer_key_fake_scan_updated_10.xlsx` | — | Your original answer key; `python -m research_tests.convert_answer_key` turns it into `answer_key.xlsx` + `writers.csv` |
| `answer_key.xlsx` — sheet **Patients** | 3, 4, 7 | Built by `python -m research_tests.build_patients`: 20 entries R01–R20 covering every case type, names split by hand, claim-only values generated (fictional) and marked |
| `task_packet.xlsx` | 7 | Every value a session participant is given, per patient (logbook + generated claim-only values) |
| `scans/performance/*` | 5 | Optional; the handwriting scans are used when empty |
| `iq/good/*`, `iq/bad/*`, `iq/expected.csv` | 6 | REAL good and deliberately bad scans; expected.csv optional (File, Expected pass/warn, Reason). `iq_check --generate` adds blurry/dark/bright copies of the real scanner pages in `iq/generated/` (git-ignored); every result says real or generated |
| `sessions/session_data.xlsx` | 7 | From `session_data_template.xlsx`: sheets **7a Session log** (time per claim), **7c Claim errors** (per box, with Value group; `user_sessions --prefill-errors` writes the reference rows), **7d Suggestion log** (accept / edit / reject / not acted on), **SUS** (optional). Participant codes P1–P5 only — checked by the pre-commit hook |
| `field_mapping_expected.csv` | 3 | Which box of each form holds which answer-key value, and in which format — **check every row against the paper forms** |

The expected box table was drafted from the boxes' printed labels (`python
-m research_tests.field_mapping --draft-expected`). It must be checked
against the paper forms, because that check is what makes it independent
of the code under test. A table that already exists is never overwritten.
New drafts go to `outputs/field_mapping/`.

## Outputs (`research_tests/outputs/`, git-ignored)

- `<test>/<test>_results.xlsx`: a **Raw data** sheet plus summary sheets.
- `<test>/summary.json`: the summary sheets, which `results.py` collects.
- `validation/seeded_errors_manifest.csv` / `.xlsx`: every seeded error: record, field, original and seeded value, the expected rule, and whether the page kept the value. It also lists what was not seeded and why. The same answer key and seed always give the same manifest.
- `chapter5_results.xlsx`: one summary sheet per test, plus a Contents sheet.
- `work/`: the OCR tests' cell pictures and runs, and the handwriting test's kept readings, reused when only the answer key changes; `--fresh` reads again.
- `<test>/run.log`, `<test>/progress.json`: written by runs started from a tab.

## How each test uses the real system

**Handwriting.**
- `ocr_compare.run_comparison` runs unchanged: the production pipeline finds the rows and cuts the cells, PaddleOCR reads them, Tesseract reads the same cell pictures, and both get the Logbook Reader's corrections.
- `ocr_compare.score_reading` does the scoring: capitals, spaces collapsed.
- Rows the pipeline did not find are reported as *not detected* and count in each writer's row detection rate. Cells left blank in the key are not scored.

**Blank cells, one rule everywhere.** A cell whose ground truth is blank is
left out of every accuracy figure and reported separately as *false readings
on blank cells*: the engine read something where nothing is written. The
comparison workbook's original numbers, which do count blank cells, are kept
in the correction metrics workbook, labelled "including blank cells".

**Correction metrics.**
- Reads the comparison workbook (read-only) and/or the handwriting results.
- Recomputes the comparison workbook per field without blank cells (sheet 2d), with the original figures beside them (2d, 2e).
- A *change* means the reading differs after capitals and space-collapsing, so capitalising alone is not counted as a correction.
- Readings that the comparison workbook stored as Excel formulas (Tesseract readings beginning with "=") are read as text.
- Counted the original way (2e), the numbers match the comparison workbook's own Summary sheet.

**Field mapping.**
- Confirmed values go through `case_bridge.draft_patient_and_encounter`, then `form_prefill.build_form_data`, then the real forms page.
- Each box is checked twice: the value the form shows, and the text read back from the PDF the page saves.

**Validation.**
- The real `validation-rules.js` runs in the real forms page.
- Errors are typed where staff would type them.
- Not seeded, and stated in the manifest and summary:
  - IC-01, IC-02, IC-07: consistent by construction.
  - MF-08: the CF4 course in the ward is auto-filled with a discharge line.
  - Attachments: no rule exists.
- The seeded errors were designed from the rule definitions, so the result shows the rules work as written, not how much of all real-world errors they cover.
- The run environment (headless Edge for the JS engine and the PDF export) is recorded in the workbook.

**Performance.**
- The real functions are wrapped with `time.perf_counter()` in the test process only.
- Validation and PDF times are measured inside the page.
- Machine specs are recorded.

**Image quality.** The real `assess_image_quality`, run on pages loaded the way the Logbook Reader loads them.

**User sessions.** Calculations only.

## Isolation

- **Database: the research database, read-only.** The research processes read `pclaimassist_research` (`RESEARCH_DB_NAME`), never the clinic's database: it holds only the two reference tables the correction model reads, seeded with the system's starter rows (migrations 006–008: 121 patterns, 99 known entries; `setup/import_seed.py`, checked against `setup/seed_checksums.json`). The clinic database's learned rows were traced to a test-set page (logbook pages 34–35) and are not used. Every connection starts with `SET SESSION TRANSACTION READ ONLY` and the app account has SELECT only.
- **One correction model.** `guard.isolate()` makes `paddle_assist.load_model()` return the research model in research processes, so the AI second look and the known fixes (`fix_saved_reading`) use the same knowledge; it stops with an error if the research database cannot be read (no silent fallback).
- **Files.** The research processes point the main config's folders at `outputs/work/`. The clinic's `uploads/`, the Logbook Reader's crops and the OCR comparison workbook are never written.
- **Offline.**
  - The forms page runs in headless Microsoft Edge (Playwright), and every request is answered locally.
  - pdf-lib 1.17.1, the version `index.html` names, is in `vendor/`. It was downloaded once from jsDelivr; SHA-256 `0f9a5cad07941f0826586c94e089d89b918c46e5c17cf2d5a3c6f666e3bc694f`.
  - Bootstrap's and AOS's scripts are small stand-ins, and anything else external gets an empty answer.
- **Main code.** The only changes outside this folder are two blocks marked `RESEARCH TESTS (removable) START … END`:
  - `Ocr_module/app.py` registers the blueprint when the flag is on;
  - `PClaimAssist/ocr-compare.html` adds the tab bar.

  Delete those two blocks, or this folder, and the main system is as it was.

## Requirements

Already in the backend's venv: PaddleOCR, pytesseract (with Tesseract
installed), openpyxl, PyMuPDF, psutil and Playwright. The forms page needs
Microsoft Edge, which is installed with Windows. Playwright is not in
`Ocr_module/requirements.txt`. On a new PC, install it with
`Ocr_module\venv\Scripts\pip.exe install playwright`. It uses the installed
Edge, so no browser download is needed.

## Setting up another laptop, and checking it matches

See **SETUP.md** (step by step) and **TASKS.md** (who runs what). Then:

```
Ocr_module\venv\Scripts\python.exe -m research_tests.check_setup
```

PASS/FAIL for Python and packages, Tesseract, Edge, model and pdf-lib hashes,
the research database seed, the test inputs, and a W03 smoke test against the
reference in `setup/reference/` (recorded on the project lead's machine with
`--record`). Superseded results are kept in `outputs/superseded/` with a note
saying why.

## Tests of this folder

```
Ocr_module\venv\Scripts\python.exe -m unittest discover -s research_tests/tests -t .
```
