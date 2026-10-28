# CH4_FACTS_2.md — Remaining facts for Chapter 4

Collected on **2026-10-26** on this PC, from the repository at branch `forms-cf2-cf4-design-update` (HEAD `52c55cb`). No source code was changed. The only repo changes are the new `thesis_figures/` folder and one line in `.gitignore` (see §9). Where something could not be verified it says **NOT FOUND**, with what a person would need to check.

---

## 1. MariaDB version

| Item | Result | How it was found |
|---|---|---|
| MariaDB client | `mysql.exe Ver 15.1 Distrib 10.4.32-MariaDB, for Win64 (AMD64)` | `E:\xamp\mysql\bin\mysql.exe --version` |
| MariaDB server | **MariaDB 10.4.32** (`mysqld.exe Ver 10.4.32-MariaDB for Win64 on AMD64 (mariadb.org binary distribution)`) | `E:\xamp\mysql\bin\mysqld.exe --version` |
| XAMPP | **XAMPP 8.2.12** (`base_stack_version=8.2.12-0`, `base_stack_platform=windows-x64`) | `E:\xamp\properties.ini` |
| Running server version | **10.4.32-MariaDB** | `db.test_connection()` (the same call `/db_health` uses), run against the live database on 2026-10-26. The Flask app itself was not running, so `/db_health` was not called over HTTP. |

**Note: XAMPP install path.** On this PC XAMPP is installed at **`E:\xamp`**, but `PClaimAssist.bat` looks for it at `C:\xampp` (`set "XAMPP_DIR=C:\xampp"`). Started from this PC, the launcher would stop with "MariaDB was not found" unless MariaDB is already running. `XAMPP_DIR` at the top of `PClaimAssist.bat` must be edited on this machine. (`C:\Program Files\MySQL` and `C:\Program Files (x86)\MySQL` folders also exist; nothing in the project uses them.)

---

## 2. Machine specs (this PC)

Collected with `Get-CimInstance` (`Win32_Processor`, `Win32_OperatingSystem`, `Win32_ComputerSystem`, `Win32_PhysicalMemory`, `Win32_VideoController`).

| Item | Value |
|---|---|
| CPU | **AMD Ryzen 5 3400G with Radeon Vega Graphics**, 4 cores / 8 threads, 3.7 GHz base (`MaxClockSpeed` 3700 MHz) |
| RAM | **16 GB** (2 × 8 GB, 2667 MHz; Windows reports 15.9 GB usable) |
| OS | **Microsoft Windows 10 Pro, 64-bit, version 22H2, build 10.0.19045** |
| GPU | **NVIDIA GeForce GTX 1650** (4 GB, driver 32.0.15.9579). A "SuperDisplay Virtual Adapter" (a virtual display driver) is also listed. |
| Python | 3.12.1 (project venv) |

**PaddleOCR runs on the CPU.** The GPU is not used: `ocr_engine.py:174` creates PaddleOCR with `use_gpu=False`, and `requirements.txt` installs `paddlepaddle==2.6.2` (the CPU package, not `paddlepaddle-gpu`).

This is the development PC that holds the repository (`C:\Users\GAMING PC\...`). Whether it is the same PC the clinic uses is **NOT FOUND** in the repo. If the clinic PC is different, run the same commands there.

---

## 3. Why CF3 was removed

### Commit 3b48e87, full message
```
Remove CF3

The form, its PDF, its overlay map, its section of the page, its
sidebar entry and validation rules, and the fields only it collected:
the prenatal visit table, the postpartum care checklist, the obstetric
risk factors and the physical examination. 129 state keys in all, with
their catalog entries and the claim_prenatal_visits /
claim_postpartum_care plumbing that read them.

Fields CF3 shared with a surviving form are kept, since CF2 and CF4
still print them - the maternity and delivery details, the obstetric
index, the admission and discharge times, and the PAN digit boxes.
Their comments now name the form that still uses them.

The two tables stay in the schema; nothing writes them any more, so
dropping them is a separate decision about existing claims.

test_every_form_key_has_an_input passes again: dateSigned,
initialPrenatalDate and postpartumFollowupDate were CF3 fields that
had already lost their inputs.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```
Author: adawngo, Wed 2026-10-21 10:04 +0800. Made on the branch `dawn/remove-cf3-and-blank-forms`.

### Summary of the diff (17 files, +49 / −1,360)
- **Deleted:** `PClaimAssist/forms/CF3.pdf` (176 KB) and `PClaimAssist/js/pdf/overlays/cf3.js` (594 lines of field coordinates).
- **`PClaimAssist/index.html`** (−≈490 lines): the CF3 page section and its dashboard card.
- **`PClaimAssist/js/app.js`** (−≈140 lines): CF3 state keys and logic.
- **`PClaimAssist/js/validation-rules.js`:** removed `VAL_FIELDS.cf3` (hciPAN, patientName, chiefComplaint, dateAdmitted, lmp, deliveryDate, mannerOfDelivery, fetalOutcome, birthWeight); `VAL_FORM_KEYS` became `['csf','cf2','cf4','pmrf']`; IC-07's message dropped "CF3"; SP-02 changed from "CF2/CF3" to "CF2".
- **Smaller edits:** `sidebar.js` (menu entry), `overlays/index.js`, `pdf-overlay.js`, `pdf-calibrate.js`, `entry-learning.js`.
- **Backend:** `philhealth/field_catalog.py` (−81: CF3 form keys, including the prenatal-visit and postpartum child rows), `form_prefill.py`, `claims_store.py`, `clinic_settings_store.py`, `routes/claims_routes.py`, `routes/settings_routes.py`, `test_form_prefill.py`.
- **Database:** no migration. `claim_prenatal_visits` and `claim_postpartum_care` stay in `schema.sql`, but nothing writes to them.

### Other mentions of CF3
- **CHANGELOG.md:641-647:** "The CF3 form, PDF, overlay map, page section, sidebar entry, validation rules and the 129 fields only it collected are gone. Fields CF3 shared with other forms stay. The prenatal-visit and postpartum-care tables stay in the database schema, though nothing writes to them any more." (No reason given.)
- **CHANGELOG.md:567** and commit `58a4a3a`, under "From the clinic staff's user testing session": "CF2 is removed, as CF3 already was". This places CF3's removal *before* that session's list (10:04 vs 20:09 the same day) and does not give CF3's reason. (CF2 was later restored on 2026-10-24/25, `318b10b`.)
- **Migration 001 / schema.sql:8-14:** the CF3/PMRF columns were made nullable because "the auto-population feature builds CF2+CSF first; CF3/PMRF are a later phase". This is about the database build order, not about removing CF3.
- **CHAPTER_DETAILS.md** and **SETUP.md:662** still describe CF3 as present (written before the removal).

### Is the reason stated anywhere?
**No.** The commit, CHANGELOG, SETUP, CHAPTER_DETAILS, code comments and migrations all say *what* was removed, but none says *why*. Please supply the reason yourselves (for example, ask adawngo, who made the commit).

---

## 4. Staff feedback rounds

### Round 1: commit `58a4a3a` (Yutaka, 2026-10-21 20:09), "From the clinic staff's user testing session"
Changes requested by staff:
1. The mobile number is optional everywhere.
2. "Date discharged" can be ticked as the same day as admitted, which copies the admission date and locks the box. (Changed again in round 2.)
3. Manner of delivery and fetal outcome are fixed to Normal Spontaneous Delivery and Live Birth ("a maternity clinic cannot claim for anything else"). Citizenship is fixed to FILIPINO. (Citizenship was relaxed in round 2.)
4. "Senior Citizen" is removed from Member Type.
5. Monthly income shows a peso sign, on screen and on the printed PMRF.
6. The name is printed above each signature line, so staff only sign ("handwriting it was running over the narrow boxes").
7. CF2 is removed (restored later in `318b10b`), and the dashboard cards re-centre.
8. The admitting and discharge diagnoses are stacked full width instead of sharing a cramped row.
9. Course in the ward and the drugs list open one line at a time (+ to add, − to hide); a filled line never hides.

Bugs fixed in the same commit:
- A space could not be typed in any text box.
- The fixed values were being blanked on load.
- Rules MF-08 and MF-09 always reported "missing".
- Read-only boxes showed grey text on grey.

Also in this commit: CSF/PMRF print alignment, the "Save as PDF to print" buttons restored, and `SKIP_VALIDATION_FOR_EXPORT` temporarily set to `true`.

### Round 2: commit `dd84cf6` (reigh, 2026-10-23), "Apply the second round of staff feedback"
Forms:
1. The PhilHealth PIN boxes turn red while empty. A "No PhilHealth" tick beside the patient's and the member's PIN stops that PIN being asked for.
2. Each PIN is asked for only once on the CSF (it used to show two rows of boxes), and the status badges in the form headers now update.
3. One tick, "Same as the admission diagnosis", makes the final diagnosis follow the admission diagnosis.
4. The discharge date must be at least one day after delivery (new rule **IC-08**). The date tick now means "the day after delivery".
5. Every date box is typed as MM/DD/YYYY (the clinic PCs' day/month setting was silently turning 03-15-2024 into 3 December).
6. Each form lists what is missing and which rules are broken. Red marks appear at once and only where something is missing. "Fix this" always lands on a box you can type in (all 28 "Fix this" buttons checked).
7. The forms can be saved one by one or together, as one PDF.
8. A name over a signature line can be left blank for writing by pen.
9. Citizenship starts as FILIPINO but can be changed.
10. "Use the delivery message" offers the doctors' usual admission diagnosis as a sentence with blanks to fill.
11. CF4 signs & symptoms appear in the printed form's own order (4 columns of 9).
12. CF4 and PMRF values print inside their boxes (CF4's tick marks were hidden under the form's white boxes; six PMRF ticks marked the wrong option; the blank CF4 had "28" stuck in its Age box).

Logbook Reader:
1. OCR output is shown in capitals. The case number box starts with the year ("2026-"). The usual admission wording is available as a template.
2. The columns are checked on each scan before it is read ("Check the columns" step).
3. Clicking the scan opens the whole row without the red box.
4. A "Went home" date on or before the delivery date is a problem that must be fixed.
5. "Cabantian" is added as a starter address word (migration 008), and run-together words are split ("CASANTANDAUAO CY" → "CABANTIAN DAVAO CITY").

### Other CHANGELOG entries, 2026-10-21 to 10-26
- **10-21 (adawngo, morning):**
  - Capitals on entry, and 90 repeated boxes made read-only copies of Patient details (`a660bcf`).
  - Dropdowns keep their choice (`c32be30`).
  - "Fix this" lands on a typeable box (`0e5f918`).
  - Boxes still to type are outlined red (`9b5770e`).
  - "Not needed" ticks on 49 form parts (`cc043bf`).
  - "Next page" offered where the boxes run out, and one page turner per form (`10a2179`, `000be6e`).
  - The whole claim is saved as one PDF (`47458fe`).
  - The clinic's own logbook setup: six column rules, 80 px rows (`9d41150`).
  These entries are not labelled as staff feedback.
- **10-24, "Steadier, clearer forms"** (later committed in `318b10b`). This is labelled **"client feedback: boxes moved while typing, the parts ran together, the preview was hard to read"**. Changes:
  - Nothing moves while typing (rule warnings became an icon on the box's label).
  - Each part of a form has its own colour.
  - The missing-information list shows missing boxes first, with filled ones as small green chips.
  - Preview zoom (Fit, 125–200%).

  The same entry also brings back CF2, switches CF4 to the February 2020 edition, fixes print alignment, adds one "Not needed" tick per health care professional, and adds the clinic representative and attending professional to Clinic Details (migration 009).
- **10-26 (`52c55cb`):**
  - Mother and baby linking.
  - "Save patient".
  - The clinic's diagnosis wording per package (NSDBF, NCP, FP001, 58300, ANV, PPC01).
  - Accreditation-number boxes.
  These are not labelled as feedback.

### Who gave the feedback, how many people, how it was collected
**NOT FOUND.** The repo only says "the clinic staff's user testing session" (`58a4a3a`), "the second round of staff feedback" (`dd84cf6`) and "client feedback" (CHANGELOG.md:128). It names no people, gives no number of testers, no date of the session, no method (interview, questionnaire, observation) and no forms or notes. To check: the team members who ran the sessions (the commit authors are Yutaka for round 1 and reigh for round 2), or your own data-gathering records.

---

## 5. How the Logbook Reader shows a suggested correction

### What the backend puts in each field
1. PaddleOCR reads the cell. `route_confidence()` sets the status: `accepted` (≥ 0.85), `needs_check` (0.65–0.85) or `manual_encoding_required` (< 0.65) (`logbook_pipeline.py:84-90`).
2. For `needs_check` / `manual_encoding_required` cells that have writing, the AI second look runs (`paddle_assist.assist_field()`, lines 736-765). It returns `{"text", "sure", "best_guess", "note", "votes", "readings", "learned_fixes"}`. The note reads like `"3 of 5 PaddleOCR readings agreed; known patterns: 'O' -> '0'"` (lines 749-751).
3. `apply_reading()` (lines 710-723) stores the AI reading on `field["ai"]` and **writes a value into the field**: the AI text if it is sure, otherwise its best guess (PaddleOCR's own reading with the known fixes applied). A `manual_encoding_required` field becomes `needs_check`, with `best_guess = true` when the AI is not sure. A field is **never** made `accepted`.
4. `fill_best_guesses()` (`logbook_pipeline.py:584-594`) does the same for any remaining manual field that has OCR text.
5. When the patient is opened, `routes/review_routes.py:48-69` (`_with_inputs`) applies newer known fixes to unsure address and diagnosis values (`paddle_assist.fix_saved_reading`). It then splits the value into the input parts (name boxes, date, hour, minute, AM/PM) with `review_fields.suggest_parts()`.

PaddleOCR's own reading stays in `raw_text`, and its confidence in `confidence`.

### What the staff member sees (`Ocr_module/templates/review.html`)
- **The suggested value is pre-filled in the box.** The inputs are filled from `f.parts`, which come from the corrected `value`. Only a `manual_encoding_required` box with nothing read is empty, with the placeholder "Type what you see in the picture" (line 829).
- **The status chip** at the top of each field shows an icon + word + percentage (line 946). Labels (lines 400-423):

| Status | Chip | Help text under it | Colours (CSS lines 12-14, 188-195) |
|---|---|---|---|
| accepted | ✓ **Looks good** (computer is N% sure) | "The computer is sure about this. Take a quick look at the picture." | green text `#166534` on `#dcfce7` |
| needs_check | ! **Please check** | "The computer is not sure. Compare the words in the box with the picture, and fix them if needed." | amber text `#854d0e` on `#fef9c3`, field border `#ca8a04` |
| needs_check + best_guess | ? **Best guess** | "The writing was hard to read, so this is the computer's best guess. Compare it with the picture carefully and fix anything that is wrong." | amber (same class as needs_check) |
| manual_encoding_required | ✎ **Please type** | "The computer could not read this. Look at the picture and type what you see." | red text `#991b1b` on `#fee2e2`, border `#dc2626` |
| empty | – **Empty in the logbook** | "Nothing is written here in the logbook. Leave it empty, or type it if you know it." | grey |

  The page's own comment (line 10) says status is "shown with an icon and words - never colour alone". When part of the writing may have been missed, the help line adds "Part of the writing may be missing from the box. Look at the whole picture." (line 424).
- **The AI line** under the help text (`renderAiNote`, lines 913-922). It is shown only when the AI reading differs from PaddleOCR's:
  - AI sure: *"AI double-checked the picture and filled in **X**. Please confirm it matches."*
  - AI not sure, and its reading differs from what is in the box: *"Another possible reading: **X**"*
- **The scanned cell picture** sits under it: "From the logbook (click the picture to see the whole row)". Clicking opens the whole row (lines 950-955).
- **The original OCR reading and the reason are shown only under a folded "More details" panel** (lines 962-968):
  - "Computer read": PaddleOCR's original text.
  - "How sure": % (looks good from 85%, please check from 65%).
  - "AI read: X (sure / not sure) — *note*". This is where the reason appears (e.g. "… known patterns: 'O' -> '0'").
  - "Goes to": the form fields the value fills.

  So the per-character reason **is shown, but only after opening "More details"**, not next to the box.
- **The box row** at the top lists every field of the patient with a mark: ✓ looks good, ! please check, ✎ please type, – empty, ✗ needs fixing (lines 1032-1034).

### How the staff member confirms, changes or rejects
There are **no per-field Accept / Edit / Reject buttons** in the Logbook Reader.
- **Confirm:** leave the pre-filled value as it is.
- **Change:** type over the box.
- **Reject:** type the original reading back in. It can be copied from "More details → Computer read".
- **Mark empty:** press "Nothing is written here (empty in the logbook)" (not offered for name, birthday or admission date; lines 873-882).

Confirmation happens for the whole patient row at once, with **"Save"** / **"Save and choose the next patient"** or **"Send to Forms ➜"** (lines 1001-1002). The server then checks the answers (`review_fields.check`). Problems must be fixed. Unusual values need a "yes, this is correct" confirmation (`confirm_warnings`). The server records `edited = true` when the saved value differs from PaddleOCR's reading (`logbook_pipeline.py:699-702`). Only after saving does the session become `reviewed`, and only reviewed sessions can become claims.

### Code excerpts (verbatim)
`Ocr_module/templates/review.html:913-922`
```javascript
function renderAiNote(f){
    if(!f.ai || !f.ai.text || f.ai.text === f.raw_text) return "";
    const text = shownAs(f, f.ai.text);
    if(f.ai.sure)
        return `<p class="field-ai">AI double-checked the picture and filled in <strong>${escapeHtml(text)}</strong>. Please confirm it matches.</p>`;
    // Not sure: the box holds the best guess; show the AI's other reading
    // only when it differs from what was filled in.
    if(text === f.value) return "";
    return `<p class="field-ai">Another possible reading: <strong>${escapeHtml(text)}</strong></p>`;
}
```
`Ocr_module/templates/review.html:944-948`
```javascript
        <div class="field-head">
            <span class="field-title" id="${id}-title">${escapeHtml(nameOf(f.category))}</span>
            <span class="chip chip--${f.status}"><span aria-hidden="true">${status.icon}</span> ${status.label}${sureText}</span>
        </div>
        <p class="field-help">${status.help}${neededHere}${f.possibly_incomplete ? ` <strong>${MAYBE_MISSING}</strong>` : ""}</p>
```
`Ocr_module/templates/review.html:962-966`
```javascript
        <details class="more"><summary>More details</summary><dl>
            <dt>Computer read</dt><dd>${f.raw_text ? escapeHtml(shownAs(f, f.raw_text)) : "(nothing)"}</dd>
            <dt>How sure</dt><dd>${sure === null ? "—" : sure + "%"} (looks good from ${Math.round(ACCEPT * 100)}%, please check from ${Math.round(REVIEW * 100)}%)</dd>
            ${f.ai ? `<dt>AI read</dt><dd>${f.ai.text ? escapeHtml(shownAs(f, f.ai.text)) : "(nothing)"} (${f.ai.sure ? "sure" : "not sure"})${f.ai.note ? ` — ${escapeHtml(f.ai.note)}` : ""}</dd>` : ""}
            <dt>Goes to</dt><dd>${targets}</dd>
```
`Ocr_module/paddle_assist.py:716-723`
```python
    field["ai"] = reading
    value = reading["text"] if reading["sure"] else (reading.get("best_guess") or reading["text"])
    if not value:
        return
    field["value"] = value
    if field["status"] == MANUAL:
        field["status"] = NEEDS_CHECK
        field["best_guess"] = not reading["sure"]
```

### Difference from the frontend design module
`PClaimAssist/js/ocr-review.js` describes a design where the suggestion is **not** used until staff press Accept / Edit / Reject. The Logbook Reader does not work that way: the suggestion **is pre-filled**, the field stays flagged (Please check / Best guess), and saving the row is the confirmation. `ocr-review.js` is not called by anything (see CH4_FACTS.md §8).

---

## 6. Crop cleanup

**Confirmed: nothing deletes them.**
- `uploads/review_crops/<upload_id>/` is written by `logbook_pipeline._save_crop()` (`logbook_pipeline.py:267-272`) and `_save_row_crops()` (line 340), and read by `GET /api/review/crops/...` (`review_routes.py:237-240`). Those are the only references to `REVIEW_CROPS_FOLDER` (besides `config.py:213, 267`, which define and create it). No code removes it. On this PC the folder already holds **35 upload folders, 158 MB**.
- `uploads/<filename>` from the calibration route `/ocr` is saved at `routes/ocr_routes.py:74-76` and never removed:
  ```python
      filename = secure_filename(file.filename)
      filepath = os.path.join(config.UPLOAD_FOLDER, filename)
      file.save(filepath)
  ```
  (`uploads/` on this PC holds e.g. `Scan.pdf`, `blob`, `batch_results_1783066850881.json`.) `/process_pdf_batch` also leaves a `batch_results_<ms>.json` in `uploads/` (`layout_routes.py:296-299`).
- The only deletions in the backend are temporary files and the logbook-setup folder:

| Code | What it deletes |
|---|---|
| `utils/uploads.py:55` | `os.remove(temp_path)`: temp copy of an upload, after use |
| `review_jobs.py:88-90` | the reading job's temp upload |
| `ocr_engine.py:182`, `ocr_tesseract.py:120` | temp PNG of a rendered PDF page |
| `logbook_setup.py:211` | `shutil.rmtree(_setup_dir(setup_id))`: the setup scan, after it is read |
| `logbook_setup.py:290` | setup folders older than 24 h (`clear_old_previews`) |
| `logbook_setup.py:233` | old saved setups, when replaced |
| `routes/template_routes.py:188` | a grid template, when the user deletes it |

---

## 7. PDF gate

`PClaimAssist/js/pdf/pdf-overlay.js:44`:
```javascript
const SKIP_VALIDATION_FOR_EXPORT = true;
```
**It is still `true`**, so critical validation errors do not block "Save as PDF" (checked at lines 694 and 778). The comment above it says "TEMPORARY - FOR LAYOUT CHECKING ONLY. SET BACK TO false BEFORE THE CAPSTONE DEFENSE." It was set in `58a4a3a` (2026-10-21).

This flag is in the browser code. The separate **server-side** export, `GET /api/claims/<id>/export/<cf2|csf>`, has its own check that is always on: it refuses an incomplete CF2/CSF (`routes/claims_routes.py:176-179`).

---

## 8. Git authors

`git log --all --format='%an <%ae>' | sort | uniq -c`:
```
      6 JREIGHDEE <153227036+JREIGHDEE@users.noreply.github.com>
      5 Yutaka <ytkk17@gmail.com>
     18 adawngo <angeliquedawng@gmail.com>
     27 reigh <jreighdenolan@gmail.com>
      2 yutakerz <ytkk17@gmail.com>
```
`Yutaka` and `yutakerz` share an email. `JREIGHDEE`'s 6 commits are all GitHub pull-request merges. Several commits also carry `Co-Authored-By: Claude …` lines (AI-assisted). Map these to your real names yourselves.

---

## 9. Screenshots for the thesis

`docs/screenshots/` has only four kinds of page, all in their empty starting state (no patients loaded): the **login** page, the **Home dashboard**, the **Read Logbook Scan** upload step, and the **Logbook Reader** upload step. Screenshots from 2026-10-15 still show CF3 ("CSF 3"), so only the newest ones were used. **None of them contain patient data.**

`thesis_figures/` was created at the repo root and added to `.gitignore`. Each figure was converted from .jpg to .png (1366 × 768) from the closest image available. **Only fig4-8 is a real match.** The others are placeholders and must be replaced before use.

| Figure | Source screenshot | What it shows | Verdict |
|---|---|---|---|
| fig4-8.png | `2026-10-25_225406_login.jpg` | Sign-in page: "Welcome", email/password, Remember my email, Forgot your password?, Sign In | **GOOD MATCH** |
| fig4-10.png | `2026-10-25_225406_ocr.jpg` | Read Logbook Scan, step 1 "Upload the scan" (no file chosen) | **NEEDS A NEW SCREENSHOT**: upload a sample scan, wait for "Check the columns", and capture the left page with the coloured column stripes, the draggable lines and the column names, before pressing "Yes, read the logbook". |
| fig4-11.png | `2026-10-21_024025_review.jpg` | Logbook Reader, step 1 upload (empty) | **NEEDS A NEW SCREENSHOT**: after reading, open step 2 "Check the patient" on a row that shows the box row (✓ ! ✎), a field with a "! Please check" or "? Best guess" chip, the cell picture, and "More details" opened. |
| fig4-12.png | `2026-10-26_090244_app.jpg` | Home dashboard (CSF/CF2/CF4/PMRF cards) | **NEEDS A NEW SCREENSHOT**: press "Send to Forms" for a sample patient, then capture Patient details or CF2 with tags visible ("From scan", "From scan · please check", "Please type", "Clinic default", "Empty in logbook"). |
| fig4-13.png | `2026-10-26_090244_app.jpg` | Home dashboard ("Not finished (2 of 9)") | **NEEDS A NEW SCREENSHOT**: "Check for missing information" with an incomplete sample claim, showing red critical rules (e.g. MF-02, IC-08) and amber warnings, with "Fix this". |
| fig4-14.png | `2026-10-26_090244_app.jpg` | Home dashboard | **NEEDS A NEW SCREENSHOT**: the live PDF preview of a filled CF2 or CSF (or the exported PDF opened in a viewer), using sample data. |
| fig4-15.png | `2026-10-26_090244_app.jpg` | Home dashboard | **NEEDS A NEW SCREENSHOT**: the signing checklist (`#signingChecklist`) on "Check for missing information", showing the SP-01 … SP-06 items. |

For the new screenshots, use only made-up data. The app has a **sample data loader** (`loadSampleData()`, `app.js:2135`) with fictional demo values. For the Logbook Reader you need a logbook scan with made-up entries; I could not find one in the repo that is confirmed to be fictional, so check before using any scan in `Ocr_module/uploads/` or `benchmarks/test_data/`.

---

## 10. Consistency list: "five forms", "0 / 5", CF3

### User-facing text (visible in the app)
| File:line | Text | Visible? |
|---|---|---|
| `PClaimAssist/index.html:158` | `<div class="stat-value" id="statForms">0 / 5</div>` | Only for a moment: `app.js:1626` replaces it with `` `${formsComplete} / ${VAL_FORM_KEYS.length}` `` (= "x / 4") once validation runs on load. The HTML default is still "0 / 5". |
| `PClaimAssist/index.html:3388` | "All five forms pull from the same data. Fill in Patient Information once and every form updates automatically." | **Yes**, in a help panel |
| `PClaimAssist/js/validation-rules.js:286` | IC-01 message: "Patient name is not consistent across the five forms." | Would show only if IC-01 fired; it cannot fire (its feature is hard-coded to 1) |

### Code comments and styles only (not visible to users)
| File:line | Text |
|---|---|
| `PClaimAssist/css/style.css:441` | comment "the five forms, side by side" |
| `PClaimAssist/css/style.css:508` | `.fs--cf3 { --fs-color: var(--purple); }` (unused style) |
| `PClaimAssist/css/style.css:640` | comment "CF3 Page 2: sub-headings, checkbox groups" |
| `PClaimAssist/css/style.css:896` | `.form-badge-header.cf3 { … }` (unused style) |
| `PClaimAssist/js/app.js:956` | comment "so the five forms stay" |
| `PClaimAssist/js/app.js:1484` | comment "five forms one by one" |
| `PClaimAssist/js/validation-rules.js:106` | comment "across all five forms" |
| `PClaimAssist/js/validation-rules.js:136` | comment "All five forms are populated from one logbook entry" |

### Backend / tests / docs
| File:line | Text |
|---|---|
| `Ocr_module/test_philhealth_mapping.py:250` | test expects `export_claim_pdf("cf3", …)` to be rejected (correct behaviour) |
| `database/migrations/001_relax_pmrf_cf3_not_null.sql` | file name and comments (historical) |
| `database/schema.sql:8-14, 124, 134, 149, 185-186` | comments calling columns "CF3" fields |
| `database/migrations/005_clinic_settings.sql:6` | comment "used by CF2, CF3 and CF4" |
| `SETUP.md:662` | "CSF/CF2/CF3/PMRF" |
| `CHAPTER_DETAILS.md` (many lines, e.g. 7, 76, 130-142, 417) | describes CF3 as present (outdated) |

`Ocr_module/templates/*.html` (the Logbook Reader and setup pages) contain no "five forms", "0 / 5" or CF3 text.

---

## Answers for the thesis

1. **MariaDB version.** The system's database runs on MariaDB 10.4.32, installed with XAMPP 8.2.12 for Windows (64-bit).
2. **Machine specs.** The system was developed and tested on a desktop PC with an AMD Ryzen 5 3400G processor (4 cores, 8 threads, 3.7 GHz), 16 GB of RAM and Windows 10 Pro 64-bit (version 22H2, build 19045). An NVIDIA GeForce GTX 1650 is installed but not used: PaddleOCR runs on the CPU (`use_gpu=False`).
3. **CF3.** The CF3 form, together with the 129 fields only it collected, was removed from PClaimAssist on 21 October 2026, while the details it shared with CF2 and CF4 were kept. *(The reason is not recorded in the project files; please add it here.)*
4. **Staff feedback.** Clinic staff tested the system in two rounds (21 and 23 October 2026), and their feedback led to changes such as optional mobile numbers, printed names above signature lines, a "No PhilHealth" option, MM/DD/YYYY date entry, a rule that discharge must be at least one day after delivery, and "Fix this" links that jump to the box to correct. *(Add who took part and how the feedback was collected; this is not recorded in the project files.)*
5. **Suggested corrections.** In the Logbook Reader, a value the offline AI corrected is pre-filled in its box and marked "Please check" or "Best guess", with a note such as "AI double-checked the picture and filled in …"; the original OCR reading and the reason for the correction are listed under "More details". Staff compare the box with the scanned picture, keep or retype the value, and confirm the whole patient row by saving it. A corrected value is never accepted automatically.
6. **Crop cleanup.** The temporary copies of uploaded scans are deleted once they have been read, but the cell and row images cut from each scan for the review screen are kept in the server's `uploads/review_crops` folder and are not deleted automatically.
