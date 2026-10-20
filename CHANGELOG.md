# PClaimAssist – Change Log

A record of every change to PClaimAssist, from the first commit to now,
newest first. Each entry gives the date, the author, and the git commit, so
you can see the exact code with `git show <commit>`.

Related documents:
- [SETUP.md](SETUP.md): how to install and run the system
- [CHAPTER_DETAILS.md](CHAPTER_DETAILS.md): codebase facts for the thesis chapters
- [Ocr_module/benchmarks/README.md](Ocr_module/benchmarks/README.md): the PaddleOCR vs Tesseract comparison tool

---

## 2026-10-21 02:40: UI update (reigh)

- Changed: review.html

**Logbook Review page**

![Logbook Review page](docs/screenshots/2026-10-21_024025_review.jpg)

## Not yet committed (2026-10-21, night)

**Patient details: clearer, and it says what is next** (`PClaimAssist/index.html`, `js/easy.js`, `css/easy.css`)
- A "Next step" line at the top names the first part with boxes still to
  fill and has a **Go there** button; when nothing required is left it
  points to "Check for missing information".
- The six parts are numbered steps in an even grid, each saying what is
  left: "5 to type", "1 from scan to check", or "Nothing missing".
- Every box that must be filled and is still empty is **red** (also radio
  buttons and the PIN boxes); it clears as soon as it is filled. No lists.
- Example text inside empty boxes that looked like real data ("DELA CRUZ",
  "456 Bonifacio Ave.", "0917-123-4567", "120/80") is gone on every page;
  format hints ("##-#########-#", "13 digits") stay.

**Less text everywhere**
- Page subtitles removed; "What to do on this page" boxes removed.
- The "Patient loaded from the logbook scan" banner and pop-up are gone;
  only the warning that a scan was not clear stays. On the boxes only the
  "From scan - please check" tag stays ("From scan", "Typed by staff",
  "Clinic default", "Empty in logbook" were notices).
- The "Which details are copied into every form" panel is closed by default.
- Read Logbook Scan and Set Up a Logbook no longer repeat their title and
  intro inside the page.

**Set Up a Logbook looks like Read Logbook Scan** (`PClaimAssist/logbook-setup.html`, `Ocr_module/templates/logbook_setup.html`, `js/ocr.js`, `js/sidebar.js`)
- Same top bar, sidebar, title and numbered tabs over a framed panel.

**Fixed: admission dates that couldn't reach the forms** (`Ocr_module/philhealth/case_bridge.py`, `logbook_pipeline.py`, `routes/review_routes.py`, `PClaimAssist/js/validation-rules.js`)
- ~20 fake-scan patients had been saved with admission text the computer
  couldn't read as a date ("08-21-2u 11:00 Am"), so no claim could carry
  the date and the forms said "Date of admission could not be read".
- Dates are now found even when the time next to them is garbled ("05-21-20
  10.COAM"), OCR look-alikes inside a date or time are read as digits
  ("O8-2I-26 1O:3O AM"), and times may be written 10.30 or 1;20. A date that
  still can't be read is never guessed.
- The review no longer saves an admission date (or birthday) it can't read:
  it asks for it in the date box ("Please type these before saving (dates in
  the date box): Admitted").
- The forms' message now says what is missing and where to type it, instead
  of blaming the logbook when no logbook was involved.

**Typing once fills the same thing on the other forms** (`PClaimAssist/js/app.js`)
- 72 boxes were already one value shared by every form. Now also linked,
  both ways: vital signs (CF3 and CF4), the three health care professionals
  (names, accreditation numbers, dates signed: CSF and CF2), the clinic's
  representative, and who signs for the patient and why (CSF and CF2), plus
  the final diagnosis and chief complaint. Choice buttons copy too.

---

## Not yet committed (2026-10-21, later)

**Send to Forms fills in more, so there is less to type** (`Ocr_module/philhealth/address_parser.py`, `case_bridge.py`, `form_prefill.py`, `field_catalog.py`, `Ocr_module/claims_store.py`, `PClaimAssist/js/claim-loader.js`)
- **Address:** the logbook's one-line address is split into the forms'
  parts: Lot/Block, Street (Purok, Km ...), Subdivision (... Homes /
  Village / Subd., with its Phase), Barangay, City and Province. Barangays
  of Davao City are recognised without "Brgy." (and with small OCR slips),
  "DC" means Davao City, and a barangay gives its city and province. A
  ditto mark ("-DO-") takes the address of the patient above in the
  logbook. Parts it can't find are left empty, never made up.
- **Sex:** filled when the logbook makes it plain: "BABY GIRL/BOY ..." or a
  pregnancy, delivery or after-birth diagnosis (not for "well baby" visits,
  where the patient may be the baby).
- These are all tagged "From scan - please check", saying where they came
  from ("Taken from the logbook address ..."). Tested on the fake-data
  patients: e.g. "Suraya Homes: Cabantian Davao City" -> Subdivision SURAYA
  HOMES, Barangay CABANTIAN, City DAVAO CITY, Province DAVAO DEL SUR.
- **Final diagnosis** now also fills CF2's diagnosis line and CF4's final
  diagnosis when a patient is loaded (before, only when typed).

**"The patient is the PhilHealth member" tick box** (`PClaimAssist/index.html`, `js/app.js`, `css/style.css`)
- On Patient Details and the CSF: one tick copies the patient's name,
  birthday, sex and PIN into the member's boxes and sets Relationship to
  "Self". While ticked the member boxes follow the patient's and are
  locked; unticking unlocks them and keeps what is there.

**Fixed: a patient sent to the forms didn't open** (`PClaimAssist/js/claim-loader.js`)
- Since the layout update (`7a6f79e`) the forms page stopped with an error
  while showing the "Patient loaded" banner (the notice it was placed after
  had been removed), so it stayed on Home instead of opening Patient
  Details with the banner.
- "Send to Forms" itself also failed with "Failed to construct 'URL'"
  (`Ocr_module/templates/review.html`): the forms address was a path, which
  now gets the page's own address as its base.

**Fixed: stray "Finish" on the review's last step** (`Ocr_module/templates/review.html`)
- On "Finish: is everything right?" the box bar still showed a "Finish"
  label next to the hidden Next button, which looked like a broken button.
  It is gone; Back now says "Back to the last box".

---

## Not yet committed (2026-10-21)

**Reading a logbook is about twice as fast** (`Ocr_module/ocr_engine.py`, `Ocr_module/logbook_pipeline.py`, `Ocr_module/paddle_assist.py`, `Ocr_module/routes/review_routes.py`)
- Before: the 2-page `fake scan 1.pdf` took 146-152 s, three quarters of it
  the AI second look, which ran PaddleOCR's whole process 4 times per unsure
  field (85 of 99 fields), finding the text lines afresh in every version
  of the same picture.
- Now the text lines are found once per field and cut from every version,
  and the lines of many fields are read in one batch
  (`ocr_engine.read_versions_many` / `read_many`); same models, same voting.
  The first read of every field is batched the same way. If a batch fails,
  fields are read one at a time as before.
- `fake scan 1.pdf`: **152 s -> 72 s**, character errors 0.340 -> 0.316
  (44 fields checked by hand), all 11 patients.
- Tried and not kept: no rotation check (changes readings), MKL-DNN, more
  threads, bigger batches (no faster).
- Noticed, not changed: fields the AI marks "sure" are often still wrong
  (2 of 16 exactly right on this scan). Staff check every AI reading anyway.

**Groupmates get the same OCR after pulling** (`Ocr_module/ocr_models/`, `.gitattributes`, `Ocr_module/.gitignore`, `Ocr_module/test_fixtures/`, `SETUP.md`)
- The PaddleOCR models (16 MB) are now in the repository and used from
  there: same models on every PC, no download on first run (identical
  readings to the downloaded ones, checked on 30 fields). Marked binary so
  git never changes their line endings.
- The logbook setup in use (`grid_templates/*.json`) is committed; setups
  put away by *Set up a logbook* (`grid_templates/archive/`) stay local.
- The tests use their own setup copies (`test_fixtures/grid_templates/`),
  so they pass whatever setup a PC is using.
- SETUP.md: what git shares and what it doesn't (learned OCR fixes stay in
  each PC's database: they come from real patients), and what to do after
  setting up a logbook or pulling a new setup.

---

## Not yet committed (2026-10-20)

**New "Set up a logbook" page replaces hand calibration** (`Ocr_module/logbook_setup.py`, `Ocr_module/logbook_layout.py`, `Ocr_module/routes/setup_routes.py`, `Ocr_module/templates/logbook_setup.html`, `PClaimAssist/js/sidebar.js`)
- Administrators open **Set up a logbook** (sidebar, Clinic section, or the
  link on the Read Logbook page) and follow four steps: choose a scan,
  check the left page, check the right page, save.
- The computer finds the columns itself: from the printed column lines,
  plus the gaps between the printed column names when a line is too faint
  to see (e.g. the red margin line). It names each column by reading the
  printed header (CASE #, NAME, ADMITTING...), and shows the patient rows
  it found as dashed boxes.
- The person only checks: each column is a numbered, named coloured stripe.
  A wrong line is dragged (anywhere along it, or by its round handle, or
  with the arrow keys) and jumps onto the nearest printed line. A wrong name
  is picked from a list in plain words. "Split in two" / "Join" for a missing
  or extra line. Two columns with the same name, or a missing Name /
  Birthday / Admission column, are pointed out before going on.
- Saving writes ordinary grid templates (the advanced calibration tool and
  the reader use them as before). "Use only this setup" moves older setups
  to `grid_templates/archive` (never deleted). Admins only.
- Tested on `fake scan 1.pdf` and `Scan.pdf`: all four pages found correctly
  with no changes by hand.

**One setup now works for every scan of the same logbook** (`Ocr_module/template_engine.py`, `Ocr_module/logbook_pipeline.py`)
- Before, the left page of `fake scan 1.pdf` was skipped (match score
  0.52-0.54, needs 0.55), and the rows started at the 3rd-4th patient.
- Pages are now matched by their printed column lines (`score_template_fit`),
  which handwriting and scan margins don't change, and the first row is found
  under the printed column header of each scan, not where it was on the
  setup scan.
- A setup made from `fake scan 1.pdf` reads all 11 of its patients and all
  12 of `Scan.pdf`, with both pages of each spread lined up.

**Plainer message when a page can't be read** (`Ocr_module/templates/review.html`)
- Numbered steps for staff (rescan flat and straight with the column names
  showing; both pages in one PDF), then "ask your administrator to set it up
  once"; technical detail under "Details for the administrator".

---

## 2026-10-15 13:17: UI update (reigh)

- Changed: review.html, style.css, index.html, app.js, login.js, sidebar.js, login.html, ocr.html

**Login page**

![Login page](docs/screenshots/2026-10-15_131721_login.jpg)

**Main app (dashboard)**

![Main app (dashboard)](docs/screenshots/2026-10-15_131721_app.jpg)

**Read Logbook Scan page**

![Read Logbook Scan page](docs/screenshots/2026-10-15_131721_ocr.jpg)

**Logbook Review page**

![Logbook Review page](docs/screenshots/2026-10-15_131721_review.jpg)

## Not yet committed (2026-10-15)

**Shorter form names in the interface** (card titles, page headings, sidebar, page titles)
- "Claim Signature Form" → **CSF**
- "Confinement Form 2 / 3 / 4" → **CSF 2 / CSF 3 / CSF 4**
- "Member Registration Form" / "Member Reg. Form" → **PMRF**
- Files: `PClaimAssist/index.html`, `PClaimAssist/js/sidebar.js`, `PClaimAssist/js/app.js`

**Offline AI for unclear OCR readings** (`Ocr_module/paddle_assist.py`)
- PaddleOCR is still the OCR engine and reads every logbook cell as before.
- Cells PaddleOCR is unsure about ("please check" or "please type") get a
  second look. It's free and offline: nothing leaves the PC.
  - **Ensemble voting:** PaddleOCR re-reads the cell from 4 enhanced versions
    of the picture (more contrast, sharpened, enlarged, black-and-white), and
    the readings vote, weighted by PaddleOCR's confidence.
  - **Pattern recognition:** known PaddleOCR mistakes are fixed per column:
    whole values, words (e.g. "N5D" -> "NSD", "Puok" -> "Purok"), and
    letter/digit mix-ups in number and date columns (e.g. "O" -> "0").
- If the result is "sure" (at least 2 readings agree, confident enough, and
  number/date columns contain no stray letters), it's filled in but still
  marked "please check". Otherwise it's shown only as a hint. The AI never
  marks a field as "looks good".
- PaddleOCR's original reading is kept on every field, so Paddle-only and
  Paddle + AI accuracy can be compared.
- The review page shows "AI double-checked the picture…" notes and an
  "AI read" row under More details.
- Adds about 1–2 seconds per unclear cell (fewer image versions:
  `AI_ENSEMBLE_VARIANTS`). Turn off with `AI_CORRECTION_ENABLED=false`.

**Form preview no longer shows a black box when zooming** (`PClaimAssist/js/pdf/pdf-overlay.js`, `PClaimAssist/css/style.css`)
- Zoomed out, part of the preview page was see-through, so the dark panel
  behind it showed as a black box that grew the further you zoomed out
  (pdf.js painted the white page background at the wrong size when the
  browser's pixel ratio dropped below 1).
- The page now always fills the panel's width and scales at once when you
  zoom or resize; it is re-drawn sharp in the background and swapped in when
  ready, so it never flashes blank. A new re-draw cancels an unfinished one,
  and forms hidden while you zoom are re-drawn when you open them.
- Checked at 33%, 50%, 67%, 100%, 150% and 200% zoom: no see-through area.

**Easier interface for older, non-technical staff** (`PClaimAssist/css/easy.css`, `PClaimAssist/js/easy.js`, `index.html`, `login.html`, `js/sidebar.js`, `js/app.js`, `js/login.js`, `js/pdf/*.js`)
- Bigger text (18px base on every page, including Read a logbook page, so
  the size never jumps) and bigger boxes and buttons; no moving or fading
  animations. The original colour scheme is kept.
- Form pages: type on the **left**, form preview on the **right**. Every
  form page and the Check page has a yellow "What to do on this page" box.
- Plain words instead of jargon and codes: "Home", "Patient Details",
  "Check for Missing Information", "Save as PDF to print", "Not started" /
  "Not finished (3 of 9)" / "Ready to print", "Not filled in yet". Rule
  codes like `MF-02` are hidden; only the message shows.
- Sidebar: the everyday job as numbered steps (1 Read a logbook page,
  2 Patient details, 3 Check for missing information), then the forms.
  From the Read a logbook page, the menu now opens the chosen page (e.g.
  Patient details) instead of always going to Home.
- Home page: three big buttons for the three main jobs.
- Patient Details: parts numbered 1-6, with **Back / Next part** buttons
  under each part.
- "Start a new patient" (was "Clear All") now asks before clearing.
- Practice/sample-data buttons and the preview calibration tool are
  administrator-only, so staff can't fill a real patient with fake data by
  accident. The red field outlines on the preview are kept.
- Removed the top "Privacy Notice" banner and the login page's "Prototype
  access — no credentials are verified" note (both no longer true), the
  notification bell (it showed a made-up message), and the login page's
  typing animation.
- Pop-up messages are bigger and stay 10 seconds instead of 4.5.
- To undo the look, remove the `css/easy.css` link from the pages.

**Case-number format learning, and training on every confirmation** (`Ocr_module/paddle_assist.py`, `Ocr_module/routes/review_routes.py`)
- Every confirmed case number is stored (in `ocr_known_entries`), and the
  offline AI learns the usual format from them: the common year prefix, and
  whether staff write spaces or dashes. Readings are reshaped to fit: a
  misread year (`2020 4043`, `702 5932`, `2o2e 8hin`) becomes `2026…`, and
  spaces are dropped when staff write case numbers without them. A year
  staff have confirmed before (e.g. last year's) is left alone.
- Case numbers are unique, so a case number staff once corrected is never
  stamped onto another patient: only letter/digit fixes and the format apply.
- The AI now trains on every confirmation on the Review page, not only the
  first. When a patient is confirmed again after a change, only the
  difference is learned: the old answer is unlearned and the new one
  learned, so the same patient never counts twice.
- The end-to-end tests can no longer write their sample patients into the
  real learning tables (they had been, and that data was removed).

**Unclear logbook fields are filled with the best guess, not left empty** (`Ocr_module/logbook_pipeline.py`, `Ocr_module/paddle_assist.py`, `Ocr_module/templates/review.html`)
- Before, a field PaddleOCR read with under 65% confidence was left empty for
  staff to type (46 of 108 fields in one real scan), even when PaddleOCR had
  read most of it. Now it's filled with the best output: the AI's reading
  when it's sure, otherwise PaddleOCR's full reading with the known pattern
  fixes applied.
- These fields are marked "Best guess" on the Review page and stay
  "please check". They are never "looks good", so staff still compare them
  with the picture.
- Only a cell PaddleOCR read nothing from is left empty to be typed.
- If staff clear a wrong guess, it counts as manual encoding again: type it
  on the Review page, or leave it for the forms with "Send to Forms".
- The original confidence routing is saved on each field (`routed_status`),
  so the thesis's OCR statistics are unchanged.

**OCR correction patterns table** (`database/migrations/006_ocr_correction_patterns.sql`, `Ocr_module/pattern_store.py`)
- New `ocr_correction_patterns` table: each row is a known PaddleOCR mistake
  for one logbook column (category, pattern type, wrong text, correct text,
  times seen, starter/learned, active).
- Seeded with 121 starter patterns: letter/digit mix-ups for case number and
  date columns, obstetric shorthand (NSD, AOG, G1P0, wks, CS), and common
  Davao address words (Purok, Davao, City, Brgy).
- Every submitted logbook review adds learned patterns (PaddleOCR's reading
  vs. what staff confirmed), so accuracy grows with use. On first run it
  also learns from all reviews already in the database.
- A fix is applied only when seen at least twice and chosen at least 60% of
  the time. Staff can switch off a bad pattern with `is_active = 0`.

**Learning common entries from every form and review** (`database/migrations/007_ocr_known_entries.sql`, `Ocr_module/entry_store.py`, `PClaimAssist/js/entry-learning.js`, `Ocr_module/routes/learning_routes.py`)
- New `ocr_known_entries` table: a vocabulary of what staff actually enter in
  the text columns (patient name, address, admitting and final diagnosis),
  with how often each word and value was entered.
- It grows from every submitted logbook review and from the PhilHealth forms
  page: when the Validation Checker is opened with no critical errors (the
  checking phase), and when a form is exported as PDF. Sent once per patient,
  so checking and then exporting CSF, CF2, CF3… for the same patient counts
  once.
- The offline AI uses it: a misread word close to a common entry is snapped
  to it ("Calinon" -> "Calinan", "Pregnacy" -> "Pregnancy"), keeping the
  original's capitalization. Whole addresses/diagnoses are suggested only
  from values confirmed in logbook reviews, since forms often word things
  differently from the logbook.
- Patient names corrected this way are only shown as a hint, never
  pre-filled, so a rare real name can't be "fixed" into a common one.
- Seeded with 98 starter words: obstetric terms for the diagnosis columns and
  Davao City districts and address words. On first run it also learns from
  all reviews already in the database.

**Automatic screenshots in this changelog** (`tools/changelog_screenshots.py`, `.githooks/pre-commit`)
- When a commit changes UI files, a pre-commit hook screenshots the affected
  pages into `docs/screenshots/` and adds an entry to the top of this file
  listing the changed UI files.
- Setup: see SETUP.md, "Changelog screenshots on commit".

---

## 2026-10-13: Layout overhaul (adawngo, `706b77d`)

- **The backend now serves the whole app.** Flask serves the PClaimAssist
  pages as well as the API, so everything runs at `http://127.0.0.1:5000/`
  (the login page opens first). Live Server (port 5500) is no longer used.
- **One-click launcher:** `PClaimAssist.bat` starts the database (XAMPP
  MariaDB) and the backend if they aren't already running, waits until the
  system answers, then opens the browser.
- **Shared sidebar:** the menu is now built by `js/sidebar.js` and used by
  both the main app and the OCR page, so they always match.
- **Removed** the Document Upload section (and its "Documents Uploaded"
  dashboard counter) and the general Settings page. The admin-only clinic
  settings are now a **Clinic Details** page.
- **OCR moved:** the OCR calibration/template workspace moved from `/` to
  `/ocr-workspace`, because the clinic app now uses `/`. In the sidebar, the
  OCR page is now called **Read Logbook Scan**.
- Updated styling throughout (`css/style.css`) and SETUP.md.

## 2026-10-12: Login and user accounts (Yutaka, `db46055`)

- **Real sign-in.** Accounts are stored in a new `users` table, and passwords
  are kept only as bcrypt hashes. The server keeps a signed session cookie,
  and every API request checks it. Pages redirect to the login screen when
  nobody is signed in.
- **Roles:** `encoder` (midwife/clerk: prepares claims) and `admin` (also
  manages accounts and clinic settings).
- **First admin account:** `Ocr_module/create_admin.py` creates it on an
  empty database.
- **My Profile** page: shows the signed-in user and lets them change their password.
- **Clinic settings stored once** (clinic name, accreditation number,
  address) in a new `clinic_settings` table and reused by CF2, CF3 and CF4
  instead of being retyped. Only an admin can edit them.
- New database migrations: `004_users_auth.sql`, `005_clinic_settings.sql`.
- New dependency: `bcrypt` (run `pip install -r requirements.txt`).

## 2026-10-11: CF4 and claim validation rules (Yutaka, `3222889`)

- **CF4 added:** a new data-entry section for PhilHealth Claim Form 4, with
  its PDF overlay (`js/pdf/overlays/cf4.js`) and the blank `forms/CF4.pdf`.
- **Validation rule engine** (`js/validation-rules.js`): checks the claim
  against the rules in research design Tables 3.3–3.8 (required fields,
  date order, consistency between forms). It sorts problems into critical
  and warnings, gives a signing checklist, and **blocks PDF generation
  while critical problems remain**.
- **OCR review inside the forms** (`js/ocr-review.js`): shows which form
  values came from OCR and which still need checking.
- Overlay coordinate fixes for CF2 and CSF.

## 2026-10-06: Logbook review workflow (reigh, `3079de7`)

- **Logbook pipeline** (`logbook_pipeline.py`): upload one logbook scan (an
  image or a PDF). The system checks image quality, matches it to a saved
  grid template, reads every cell with OCR, and creates **one review
  session per patient row**.
- **New Logbook Review page** (`/review`): staff check and correct each
  row. Each column has a matching input (a date picker for dates, separate
  boxes for last/first/middle name, numbers only for the case number) and
  safeguards: hard errors must be fixed, and unusual values need a
  "yes, this is correct".
- **Background jobs with a progress bar** (`review_jobs.py`): reading a
  logbook takes about a minute, so the page shows progress instead of
  freezing.
- **Pre-filling forms from OCR** (`philhealth/form_prefill.py`,
  `js/claim-loader.js`): a reviewed claim loads into PMRF, CSF, CF2 and CF3,
  and each value is tagged "from OCR", "from OCR – check", "typed at OCR
  review", or "required".
- `js/pin-input.js`: digit-box inputs for PIN/number fields.
- New database migration: `003_case_session_ocr_review.sql`.
- Large new test suites for the pipeline, review fields and form prefill.

## 2026-10-05: OCR-to-claim data quality (reigh)

- **Image quality warning** (`5350f09`): flags blurry, too dark or too bright
  uploads and shows a warning banner. OCR still runs; it's advisory only.
- **Address and delivery date/time carried into claims** (`5ebe784`): these
  logbook columns were read by OCR but dropped when a claim was created.
  Adds `patients.address` (migration `002_add_patient_address.sql`).
- **Automatic claim status** (`a9b5ad8`): a claim moves *draft → ready*
  once CF2 and CSF are complete, and *ready → exported* after a successful
  PDF export. Status never moves backwards.
- **Cleanup** (`5ab9396`): removed a stray text file and fixed an outdated
  comment in `app.js`.
- **CHAPTER_DETAILS.md** (`2e70621`): codebase facts for the thesis chapters.

## 2026-09-17: Grid templates (reigh, `f1bc9f4`)

- Added the saved grid templates for the left- and right-hand logbook pages
  (`Ocr_module/grid_templates/`), used to locate table cells for OCR.

## 2026-09-15: Login screen and expanded PDF forms (Yutaka, `fa84366`)

- First **login page** (`login.html`, `js/login.js`). It was a screen only;
  real accounts came on 2026-10-12.
- **Expanded form fields** for CSF, CF2, CF3 and PMRF, with realigned PDF
  overlay coordinates so text lands in the right boxes.
- `js/box-input.js`: one-character-per-box inputs, like on the paper forms.
- Fixes: the CF3 sidebar icon, and the missing 12th digit box for the
  PhilHealth Employer Number on CSF.

## 2026-09-12: OCR data → PhilHealth claims (reigh, `1c5e5e3`)

- **Claims stored in the database** (`claims_store.py`): patients,
  encounters and claims tables.
- **Case bridge** (`philhealth/case_bridge.py`): turns reviewed OCR text into
  claim fields. Anything it can't parse confidently is left blank and
  flagged rather than guessed.
- **Field catalog and mapping** (`philhealth/field_catalog.py`,
  `mapping_service.py`): one list of CF2/CSF fields and required fields,
  ported from the frontend's `app.js`.
- **Server-side PDF export** of CF2/CSF (`philhealth/pdf_export.py`).
- Claims API (`routes/claims_routes.py`) and mapping tests.
- New database migration: `001_relax_pmrf_cf3_not_null.sql`.

## 2026-09-08 to 2026-09-10: Database and OCR testing (reigh)

- **Database connection** (`03e6750`): Flask connects to MariaDB
  (`db.py`), with settings read from a local `.env` file. A temporary
  diagnostic route checks that writes work.
- **Case sessions moved to MariaDB** (`6cce5cc`): reviewed OCR results were
  JSON files and are now rows in `case_sessions`.
- **SETUP.md rewritten** (`94807a2`) with full database setup instructions
  (XAMPP, phpMyAdmin, schema import, app database user, `.env`).
- **OCR engine testing** (`8f94dec`, `175033f`): added Tesseract as a second
  engine (`ocr_tesseract.py`), a side-by-side PaddleOCR vs Tesseract panel
  that appends results to one Excel workbook, and an offline benchmark tool
  (`benchmarks/`) with accuracy metrics for the capstone comparison.

## 2026-09-02: Baseline before database work (reigh, `671e047`)

- **Database schema** (`database/schema.sql`): `patients`, `case_sessions`,
  `encounters`, `claims`, `claim_prenatal_visits`, `claim_postpartum_care`,
  `research_ground_truth`, `research_ocr_results`.
- OCR improvements: template matching by page side (left/right), automatic
  detection of handwritten content rows, and better batch PDF processing.

## 2026-08-27: Project created (reigh, `42e9aaf`, `47644dc`)

- **PClaimAssist frontend:** a single-page app (`index.html`, `app.js`,
  `style.css`) with a dashboard, patient data entry, and form previews for
  CSF, CF2, CF3 and PMRF. Filled PDFs are generated in the browser with
  pdf-lib, using per-form overlay files (`js/pdf/overlays/`) and a
  calibration tool (`pdf-calibrate.js`).
- **OCR module** (Flask + PaddleOCR, first named `my_ocr_project`, then
  renamed to `Ocr_module`): grid template editor, cell cropping, layout
  detection, batch PDF processing, and the OCR calibration UI.
- An OCR tab linking the frontend to the OCR module.
- First version of SETUP.md, plus `setup_ocr.bat` / `run_ocr.bat` for Windows.
