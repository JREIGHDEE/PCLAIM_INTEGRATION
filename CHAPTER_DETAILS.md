# CHAPTER_DETAILS.md

Extracted directly from the `YD PCLAIM` codebase on 2026-10-02 (branch `database-integration`). Every item below is cited to a file (and line number where useful). Nothing is invented. Where the code doesn't match the assumptions in the chapter outline you gave me, it's flagged **MISMATCH**. Where something described in the outline doesn't exist anywhere in the repo, it's flagged **NOT IMPLEMENTED**.

Two codebases make up the system:
- `Ocr_module/` — Python/Flask backend: OCR, template calibration, PhilHealth claim mapping/export, MariaDB access.
- `PClaimAssist/` — static HTML/CSS/JS frontend: the CSF/CF2/CF3/PMRF data-entry forms and client-side PDF fill.

---

## 1. TECH STACK

### Backend framework
**Flask** (not FastAPI). `Flask==3.1.3`, `flask-cors==6.0.5` — [Ocr_module/requirements.txt:27-28](Ocr_module/requirements.txt#L27-L28). App factory in [Ocr_module/app.py:23](Ocr_module/app.py#L23) (`create_app()`), blueprints registered in [Ocr_module/routes/__init__.py](Ocr_module/routes/__init__.py).

### OCR engine
**PaddleOCR 2.8.1** (`paddleocr==2.8.1`, `paddlepaddle==2.6.2`) — [Ocr_module/requirements.txt:61-62](Ocr_module/requirements.txt#L61-L62). Initialized with `use_angle_cls=True, lang="en", use_gpu=False` — [Ocr_module/ocr_engine.py:28-33](Ocr_module/ocr_engine.py#L28-L33).

**PP-Structure / table detection: NOT IMPLEMENTED.** Only the plain `PaddleOCR(...).ocr()` text-detection/recognition API is used. Table/row/column structure is instead detected by this project's own OpenCV heuristics in `template_engine.py` (grid-line projection, ink-density row bands — see §13), not PaddleOCR's PP-Structure module.

**Tesseract** also exists as a second engine for benchmarking/manual A-B comparison only — `pytesseract==0.3.13` — [Ocr_module/ocr_tesseract.py](Ocr_module/ocr_tesseract.py). Not used by the production pipeline (`routes/` only imports it lazily when `engine=tesseract` is explicitly requested — [Ocr_module/routes/ocr_routes.py:46-55](Ocr_module/routes/ocr_routes.py#L46-L55)).

### Image preprocessing
**OpenCV** — `opencv-python==4.11.0.86`, `opencv-contrib-python==4.10.0.84` — [Ocr_module/requirements.txt:56-57](Ocr_module/requirements.txt#L56-L57).

**MISMATCH against a typical OCR-pipeline assumption:** there is **no image enhancement preprocessing before OCR at all.** `ocr_engine.py` loads the image with `cv2.imread` and passes it straight to PaddleOCR — [Ocr_module/ocr_engine.py:39-44](Ocr_module/ocr_engine.py#L39-L44). No grayscale conversion, no deskew, no perspective correction, no denoising, no contrast adjustment is applied anywhere before either OCR engine runs. This is explicitly documented as a deliberate fairness property of the benchmark, not an oversight: *"No extra preprocessing (denoising, thresholding, deskewing, etc.) is applied before either engine — this matches how the production PaddleOCR pipeline already works (`ocr_engine.py` does no preprocessing either)."* — [Ocr_module/benchmarks/README.md:311-313](Ocr_module/benchmarks/README.md#L311-L313).

The only OpenCV grayscale/blur/edge operations in the codebase are for **grid-line and row detection** (template calibration), not OCR-quality preprocessing — see §13:
- `cv2.cvtColor(..., COLOR_BGR2GRAY)` + `cv2.GaussianBlur(gray, (5,5), 0)` + `cv2.Canny(blurred, 50, 150)` — [Ocr_module/template_engine.py:183-185](Ocr_module/template_engine.py#L183-L185), repeated in [Ocr_module/routes/layout_routes.py:49-51](Ocr_module/routes/layout_routes.py#L49-L51).
- Morphological closing to emphasize vertical/horizontal lines — [Ocr_module/template_engine.py:370-375](Ocr_module/template_engine.py#L370-L375).
- A custom "ink mask" (background-divide normalization + blue-channel ruling-line exclusion) used only for row-boundary detection on ledger scans — [Ocr_module/template_engine.py:462-499](Ocr_module/template_engine.py#L462-L499).

So: **grayscale — yes (for layout detection only), deskew — NOT IMPLEMENTED, perspective correction — NOT IMPLEMENTED, denoise — NOT IMPLEMENTED, contrast adjustment — NOT IMPLEMENTED.**

### Fuzzy matching library
**NOT IMPLEMENTED for OCR text correction.** `RapidFuzz==3.14.5` is pinned in requirements — [Ocr_module/requirements.txt:84](Ocr_module/requirements.txt#L84) — but a repo-wide search found **zero imports or calls of `rapidfuzz`, `fuzzywuzzy`, or `difflib`** anywhere in `Ocr_module/` or `PClaimAssist/`. It appears to be a transitive dependency only (likely pulled in by another package), not used by any application code. **If Chapter 4 claims a RapidFuzz-based fuzzy-matching correction step, that is a MISMATCH — no such code exists.**

Template-matching *does* use a scoring function (`score_template_match`, §13), but it's hand-written numeric layout-similarity scoring (aspect ratio, grid-line offsets, line spacing), not string fuzzy-matching.

### PDF generation
**Two different libraries, in two different places — not ReportLab anywhere:**
- **Server-side (Python, `Ocr_module/`): PyMuPDF (`fitz`)**, not ReportLab. `PyMuPDF==1.27.2.3` — [Ocr_module/requirements.txt:77](Ocr_module/requirements.txt#L77). Used in [Ocr_module/philhealth/pdf_export.py:16](Ocr_module/philhealth/pdf_export.py#L16) to fill the real CF2/CSF PDF templates (`page.insert_text` / `page.insert_textbox` — [Ocr_module/philhealth/pdf_export.py:43,51](Ocr_module/philhealth/pdf_export.py#L43)). `fitz` is also used for PDF→image rendering in OCR (`ocr_engine.extract_pdf_text`, `batch_processor.py`).
- **Client-side (JS, `PClaimAssist/`): pdf-lib 1.17.1** (CDN) — `<script src="https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js">` — [PClaimAssist/index.html:2381](PClaimAssist/index.html#L2381), used by `js/pdf/pdf-overlay.js`. **pdf.js 3.11.174** (CDN) is used to *render* a PDF preview in the browser — [PClaimAssist/index.html:2379](PClaimAssist/index.html#L2379).

**If the chapter says "ReportLab," that is a MISMATCH** — ReportLab is not in `requirements.txt` and is not imported anywhere.

### Pandas
`pandas==3.0.3` — [Ocr_module/requirements.txt:63](Ocr_module/requirements.txt#L63). Used only for one Excel export (`/export_case_session` → `pd.DataFrame([row]).to_excel(...)`) — [Ocr_module/routes/ocr_routes.py:236-240](Ocr_module/routes/ocr_routes.py#L236-L240). Not used for data validation, feature engineering, or bulk analytics anywhere.

### MySQL connector
**PyMySQL** (`PyMySQL==1.1.1` — [Ocr_module/requirements.txt:69](Ocr_module/requirements.txt#L69)), used as a raw DB-API driver with `DictCursor` (no ORM) — [Ocr_module/db.py:15-16,32-42](Ocr_module/db.py#L15-L16).

### Frontend libraries (PClaimAssist, all via CDN — [PClaimAssist/index.html:7-9,2376-2389](PClaimAssist/index.html#L7-L9))
| Library | Version |
|---|---|
| Bootstrap | 5.3.3 |
| Bootstrap Icons | 1.11.3 |
| AOS (scroll animation) | 2.3.4 |
| pdf.js | 3.11.174 |
| pdf-lib | 1.17.1 |

No `package.json` exists anywhere in the repo — the frontend has no build step/bundler/npm dependency management; every library is a plain `<script src>` CDN tag.

### Excel/spreadsheet
`openpyxl==3.1.5` — [Ocr_module/requirements.txt:58](Ocr_module/requirements.txt#L58) — used for the OCR engine-comparison testing workbook ([Ocr_module/ocr_testing_store.py:22](Ocr_module/ocr_testing_store.py#L22)) and the case-session export.

### Other notable pinned deps
`pytesseract==0.3.13`, `PyMuPDF==1.27.2.3`, `scikit-image==0.26.0`, `imgaug==0.4.0`, `pycryptodome==3.23.0` — all in [Ocr_module/requirements.txt](Ocr_module/requirements.txt). `scikit-image`/`imgaug` appear to be unused transitive PaddleOCR dependencies — no direct imports found in application code.

---

## 2. FIELD SOURCE MAPPING MATRIX (Table 3.1)

Two independent field catalogs exist and they are **not the same scope**:
- **Python catalog** ([Ocr_module/philhealth/field_catalog.py](Ocr_module/philhealth/field_catalog.py)) — CF2/CSF only, ported deliberately from the JS (see file's own docstring, lines 1-13). This is what the backend's `/api/claims` endpoints actually validate/export against.
- **JS catalog** (`PClaimAssist/js/app.js`) — covers all four forms (CSF, CF2, CF3, PMRF) client-side, but **has no server bridge for CF3/PMRF** (confirmed in §9/§10 — the `OVERLAYS` dict and `_SUPPORTED_FORMS` in the backend only contain `cf2`/`csf`).

**Source** column values used below follow the codebase's own three-way distinction ([Ocr_module/philhealth/field_catalog.py:150-156](Ocr_module/philhealth/field_catalog.py#L150-L156)):
- `auto_ocr` — filled from a reviewed OCR case session (`case_bridge.py`)
- `auto_config` — filled from a fixed per-facility config default (`.env`)
- `manual` — no source anywhere in the system; a human must type it
- `computed` — derived from other fields at render/export time (not stored)

| Field (code key) | Label on form | Forms | Source | Citation |
|---|---|---|---|---|
| patientLastName | Patient Last Name | CF2, CSF | auto_ocr | [field_catalog.py:25,73,143](Ocr_module/philhealth/field_catalog.py#L143) |
| patientFirstName | Patient First Name | CF2, CSF | auto_ocr | field_catalog.py:25,143 |
| patientMiddleName | Patient Middle Name | CF2, CSF | auto_ocr | field_catalog.py:26,143 |
| patientNameExt | Patient Name Extension | CF2, CSF | auto_ocr | field_catalog.py:27,143 |
| patientDOB | Patient Date of Birth | CF2, CSF | auto_ocr | field_catalog.py:28,143 |
| patientSex | Patient Sex | (catalog only; not in any VAL_FIELDS list) | manual | field_catalog.py:29 |
| patientPIN | Patient / Dependent PIN | CSF | manual | field_catalog.py:30 (not in AUTO_OCR_KEYS) |
| dateAdmitted | Date Admitted | CF2, CSF | auto_ocr | field_catalog.py:33,144 |
| timeAdmitted | Time Admitted | CF2 (computed display) | auto_ocr | field_catalog.py:34,144 |
| amPmAdmitted | — | internal | auto_ocr | field_catalog.py:35,144 |
| dateDischarge | Date Discharged | CF2, CSF | auto_ocr | field_catalog.py:36,144 |
| timeDischarge | Time Discharged | CF2 | auto_ocr | field_catalog.py:37,144 |
| amPmDischarge | — | internal | auto_ocr | field_catalog.py:38,144 |
| disposition | Patient Disposition | CF2 | manual | field_catalog.py:39 (not in AUTO_OCR_KEYS) |
| accommodation | Type of Accommodation | CF2 | manual | field_catalog.py:40 |
| chiefComplaint | — | (CF3 field, not in Python catalog's VAL_FIELDS) | manual | field_catalog.py:41 (KEY_SOURCE only) |
| admissionDx | Admission Diagnosis | CF2 | auto_ocr | field_catalog.py:42,145 |
| dischargeDx | Discharge Diagnosis | CF2 | auto_ocr | field_catalog.py:42,145 |
| hciPAN | HCI Accreditation No. (PAN) | CF2 | auto_config | field_catalog.py:45,147 |
| hciName | Health Care Institution Name | CF2 | auto_config | field_catalog.py:46,147 |
| hciStreet | HCI Street | CF2 | auto_config | field_catalog.py:47,147 |
| hciCity | HCI City | CF2 | auto_config | field_catalog.py:48,147 |
| hciProvince | HCI Province | CF2 | auto_config | field_catalog.py:48,147 |
| memberPIN | Member PhilHealth PIN | CSF | manual | field_catalog.py:51 (not auto) |
| memberLastName | Member Last Name | CSF | manual | field_catalog.py:52 |
| memberFirstName | Member First Name | CSF | manual | field_catalog.py:53 |
| memberMiddleName | Member Middle Name | CSF | manual | field_catalog.py:54 |
| memberNameExt | Member Name Extension | CSF | manual | field_catalog.py:55 |
| memberDOB | Member Date of Birth | CSF | manual | field_catalog.py:56 |
| memberSex | — | (catalog only) | manual | field_catalog.py:57 |
| relationship | Relationship to Member | CSF | manual | field_catalog.py:58 |
| employerPEN | Employer PEN | CSF | manual | field_catalog.py:60 |
| employerPhone | Employer Phone | CSF | manual | field_catalog.py:60 |
| employerName | Employer / Business Name | CSF | manual | field_catalog.py:61 |
| patientName (computed) | Patient Name | CF2, CSF | computed | field_catalog.py:224-227 (concat last/first/ext/middle) |
| memberName (computed) | Member Name | CSF | computed | field_catalog.py:229-232 |
| hciAddress (computed) | — | CF2 | computed | field_catalog.py:234-236 |
| timeAdmittedStr (computed) | — | CF2 | computed | field_catalog.py:238-239 |
| timeDischargeStr (computed) | — | CF2 | computed | field_catalog.py:241-242 |
| patientAddress | Patient Address | (catalog only; not required by any VAL_FIELDS list) | auto_ocr | **Added post-initial-scan** — field_catalog.py KEY_SOURCE/FIELD_LABELS, [Ocr_module/philhealth/case_bridge.py](Ocr_module/philhealth/case_bridge.py) |
| deliveryDate | Date of Delivery | (catalog only; CF3 field, captured ahead of full CF3 support) | auto_ocr | **Added post-initial-scan** — same citation |
| deliveryTime | Time of Delivery | (catalog only) | auto_ocr | **Added post-initial-scan** — same citation |
| amPmDelivery | — | (catalog only) | auto_ocr | **Added post-initial-scan** — same citation |

**CF3/PMRF fields — client-side (JS) only, no backend persistence/mapping.** These exist in `state.data` and `VAL_FIELDS.cf3` / `VAL_FIELDS.pmrf` in [PClaimAssist/js/app.js:337-358](PClaimAssist/js/app.js#L337-L358), matched by `claims` table columns in the schema (§9), but **no Python code reads/writes them** — not in `field_catalog.py`'s `KEY_SOURCE`, not in `claims_store.py`'s editable-column whitelists. Source for all of them is therefore **manual (client-side form entry) only** — there is no OCR or system-derived source for any CF3/PMRF field:

CF3 required fields (label, from JS): hciPAN, patientName, chiefComplaint, dateAdmitted, lmp, deliveryDate, mannerOfDelivery, fetalOutcome, birthWeight — [PClaimAssist/js/app.js:337-347](PClaimAssist/js/app.js#L337-L347).

PMRF required fields: memberPIN, memberName, memberDOB, civilStatus, citizenship, fullAddress, mobile, memberType, patientName (dependent) — [PClaimAssist/js/app.js:348-358](PClaimAssist/js/app.js#L348-L358).

Beyond the required-field lists, CF3 also carries ~60 additional detail fields in `state.data` (vitals, physical exam, risk-factor checkboxes, 11-visit prenatal grid, postpartum checklist) — [PClaimAssist/js/app.js:38-91](PClaimAssist/js/app.js#L38-L91) — all manual-entry, all client-side only, none bridged to the database.

**Important scope note (MISMATCH risk):** if Chapter 3 presents one unified mapping table claiming OCR sourcing for CF3/PMRF fields, that's incorrect — only CF2/CSF fields listed in `AUTO_OCR_KEYS` (patient name parts, DOB, admission/discharge date-time, admission/discharge diagnosis — 11 keys total, [field_catalog.py:142-146](Ocr_module/philhealth/field_catalog.py#L142-L146)) have any OCR source at all.

---

## 3. LOGBOOK COLUMNS the OCR reads

Nine training categories are defined in config, representing the logbook's columns — [Ocr_module/config.py:128-138](Ocr_module/config.py#L128-L138):

```
"CASE #", "DATE & TIME OF ADMISSION", "NAME", "BDAY", "ADDRESS",
"ADMITTING DIAGNOSIS", "DATE & TIME OF DELIVERY", "FINAL DIAGNOSIS",
"DATE & TIME OF DISCHARGE"
```

These are split across a **two-page ledger spread** (confirmed from the two saved calibration templates actually checked into the repo):

- **Left page** (odd), 5 columns, in this left-to-right order — [Ocr_module/grid_templates/left_pages_FINAK_1789214042272.json:11-31](Ocr_module/grid_templates/left_pages_FINAK_1789214042272.json#L11-L31):
  `CASE #` → `DATE & TIME OF ADMISSION` → `NAME` → `BDAY` → `ADDRESS`
- **Right page** (even), 4 columns — [Ocr_module/grid_templates/right_pages_finallll_1789214071747.json:9-26](Ocr_module/grid_templates/right_pages_finallll_1789214071747.json#L9-L26):
  `ADMITTING DIAGNOSIS` → `DATE & TIME OF DELIVERY` → `FINAL DIAGNOSIS` → `DATE & TIME OF DISCHARGE`

Row boundaries carry over from the odd page to the even page of the same spread so both halves of one physical logbook entry line up — [Ocr_module/batch_processor.py:61-67](Ocr_module/batch_processor.py#L61-L67).

**Update (post-initial-scan):** 8 of these 9 columns are now consumed by the OCR→database bridge (`case_bridge.py`): `NAME`, `BDAY`, `ADDRESS`, `DATE & TIME OF ADMISSION`, `DATE & TIME OF DISCHARGE`, `DATE & TIME OF DELIVERY`, `ADMITTING DIAGNOSIS`, `FINAL DIAGNOSIS` — [Ocr_module/philhealth/case_bridge.py](Ocr_module/philhealth/case_bridge.py). `ADDRESS` now maps to the newly-added `patients.address` column ([database/migrations/002_add_patient_address.sql](database/migrations/002_add_patient_address.sql)); `DATE & TIME OF DELIVERY` now maps to `claims.delivery_date`/`delivery_time`/`am_pm_delivery` (columns that already existed in the schema but were never populated before). **`CASE #` remains lookup-only by design** — it's the `case_sessions.logbook_case_number` key, not a patient/claim field, so it's still correctly the only column with no destination.

---

## 4. CONFIDENCE THRESHOLDS

Found in the calibration UI's review-table rendering — [Ocr_module/templates/index.html:2779-2816](Ocr_module/templates/index.html#L2779-L2816):

| Level | Threshold | Visual treatment | What happens |
|---|---|---|---|
| High | `confidence >= 0.85` | Green badge (`#dcfce7` bg / `#166534` text) | Displayed in the review table; no other automated action |
| Medium | `0.65 <= confidence < 0.85` | Amber badge (`#fef3c7` bg / `#92400e` text) | Displayed in the review table; no other automated action |
| Low | `confidence < 0.65` | Red badge (`#fee2e2` bg / `#991b1b` text) | Displayed in the review table; no other automated action |
| Unknown | `null`/`undefined`/`""` | Gray badge (`#f3f4f6` bg / `#6b7280` text) | Confidence missing/unparseable |

**MISMATCH / important limitation:** these thresholds are purely a **visual heatmap cue for the human reviewer** ([Ocr_module/templates/index.html:2812-2816](Ocr_module/templates/index.html#L2812-L2816)). There is **no automated behavior gated on confidence level anywhere in the codebase** — no auto-accept at high confidence, no auto-reject/flag-for-correction at low confidence, no routing to a correction module. The OCR review workflow always requires the human to manually accept/edit every field regardless of confidence (`/save_reviewed_result` just persists whatever text the reviewer submits — [Ocr_module/routes/ocr_routes.py:138-201](Ocr_module/routes/ocr_routes.py#L138-L201)).

A second, unrelated threshold exists for **template matching** (not OCR text confidence): `TEMPLATE_MATCH_THRESHOLD = 0.55`, env-overridable via `OCR_TEMPLATE_MATCH_THRESHOLD` — [Ocr_module/config.py:119](Ocr_module/config.py#L119). At/above this layout-similarity score, a saved grid template is auto-applied to a new page — [Ocr_module/routes/template_routes.py:133-135](Ocr_module/routes/template_routes.py#L133-L135). This is unrelated to per-field OCR text confidence.

---

## 5. CORRECTION MODULE

**NOT IMPLEMENTED as described in the outline.** There is no character-substitution map, no regex-based text-correction patterns, no fuzzy-matching-based correction, no cross-field inference, and no confusion-table ranking anywhere in the codebase. A repo-wide search for `confusion`, `fuzz`, `RapidFuzz`, `substitution` found zero matches in application code (only `requirements.txt` lists `RapidFuzz` as an unused dependency — see §1).

What *does* exist, and could be mistaken for a correction module, is **free-text parsing/normalization** in `case_bridge.py` — this is format parsing (turning OCR free text into a structured date/time/name), not error correction of misrecognized characters:

- **Date parsing** — tries a fixed list of format strings in order, first match wins: `"%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%y", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"` — [Ocr_module/philhealth/case_bridge.py:25-28,32-42](Ocr_module/philhealth/case_bridge.py#L25-L28). No fallback guessing: unparseable text is left blank and reported as a warning, never silently corrected — [case_bridge.py:147-148](Ocr_module/philhealth/case_bridge.py#L147-L148).
- **Time parsing regex**: `r"(\d{1,2}):(\d{2})\s*([AaPp][Mm])?"` — [case_bridge.py:29](Ocr_module/philhealth/case_bridge.py#L29). Converts to 24h HH:MM + AM/PM; if no AM/PM marker is present in the OCR text, it is explicitly left `None`/unknown rather than guessed — [case_bridge.py:60-64](Ocr_module/philhealth/case_bridge.py#L60-L64).
- **Name splitting** (`_split_name`) — [case_bridge.py:68-111](Ocr_module/philhealth/case_bridge.py#L68-L111): if the OCR text has a comma, splits on it (`Last, First Middle`). If no comma, assumes `First [Middle] Last` order and pulls the last 1-3 tokens as the surname, with a small hardcoded list of Filipino/Spanish surname particles checked to avoid cutting compound surnames short: `("dela","de","del","san","santa","sto","sta","mac","mc","van","von")` for 2-word surnames, and `"de los/las/la"` for 3-word surnames — [case_bridge.py:94-101](Ocr_module/philhealth/case_bridge.py#L94-L101). Every no-comma split emits an explicit warning that it's a guess needing verification — [case_bridge.py:106-111](Ocr_module/philhealth/case_bridge.py#L106-L111).

**Validation/format checking (the closest thing to a "correction module" that actually exists)** is in `mapping_service.py`'s `_validate()` — [Ocr_module/philhealth/mapping_service.py:39-61](Ocr_module/philhealth/mapping_service.py#L39-L61) — and is purely pass/fail, never auto-corrects:
1. Date-string validity check (`is_valid_date_string`) for every field in `DATE_FIELDS`.
2. Enum membership check against `ENUM_CHOICES` (`disposition`, `accommodation`, `relationship`).
3. PIN format regex: `r"^\d{2}-\d{9}-\d{1}$"` (pattern `##-#########-#`) — [Ocr_module/philhealth/field_catalog.py:161](Ocr_module/philhealth/field_catalog.py#L161), applied to `memberPIN`/`patientPIN`.

No ranking, no confidence-weighted correction ordering, no OCR-confusion table exists to rank candidate corrections.

---

## 6. FEATURES computed by the validation engine

**NOT IMPLEMENTED** as a distinct feature-engineering layer (binary/numeric/categorical features feeding rules). The "validation engine" (`mapping_service.py`) computes only the following per-field outputs, which are checks, not reusable named features:

| Output | Type | Description | Used by |
|---|---|---|---|
| `errors[key]` | per-field string message | Set when a field has a value but fails date/enum/PIN-format validation | `_form_status()` → blocking_errors list |
| `resolve_computed_value(key, data)` truthy/falsy | binary (implicit) | Whether a required field resolves to a non-empty value | `_form_status()` → missing_required list |
| `form_status.complete` | binary | `not missing and not blocking_errors` | `/api/claims/<id>/export/<form>` gate ([claims_routes.py:88-90](Ocr_module/routes/claims_routes.py#L88-L90)) |

That's the entire "feature" surface: field-presence (binary) and field-format-validity (binary), computed per field, per form. There is no numeric feature (e.g. OCR confidence score, edit distance, date-plausibility delta) and no categorical feature (e.g. error-type classification) computed anywhere. If Chapter 3 lists named features like "confidence_score", "date_delta_days", "field_completeness_ratio" etc., **those do not exist in code — flag as NOT IMPLEMENTED.**

---

## 7. VALIDATION RULES

**MAJOR MISMATCH: the MF/IF/IC/SP/IQ/CR rule-ID taxonomy does not exist anywhere in the codebase.** A repo-wide search for `MF-0`, `IF-0`, `IC-0`, `SP-0`, `IQ-0`, `CR-0` and for any rules/rule-engine module found **zero matches**. There is no `rules.py`, no rules table, no rule-ID constants, no categorized rule list of any kind.

What actually exists is a **single generic, un-categorized validation function**, `mapping_service._validate()` and `_form_status()` ([Ocr_module/philhealth/mapping_service.py:39-77](Ocr_module/philhealth/mapping_service.py#L39-L77)), equivalent to exactly three rule *types*, applied uniformly to every field rather than as distinct numbered rules:

| Rule (as implemented) | IF condition | THEN action | Message |
|---|---|---|---|
| Required-field check | `resolve_computed_value(key, data)` is falsy for a field in `VAL_FIELDS[form]` | Field key/label added to `missing_required` list; `complete=False` | Field label appended to: `"Cannot generate claim form. The following required information is missing: ..."` — [mapping_service.py:126-130](Ocr_module/philhealth/mapping_service.py#L126-L130) |
| Date format check | Field in `DATE_FIELDS` has a value that doesn't parse as `YYYY-MM-DD` | Added to `errors[key]`; blocks export | `"{label} is not a valid date"` — [mapping_service.py:49](Ocr_module/philhealth/mapping_service.py#L49) |
| Enum check | Field value present but not in `ENUM_CHOICES[key]` | Added to `errors[key]`; blocks export | `"{label} must be one of: {choices}"` — [mapping_service.py:54](Ocr_module/philhealth/mapping_service.py#L54) |
| PIN format check | `memberPIN`/`patientPIN` present but doesn't match `##-#########-#` | Added to `errors[key]`; blocks export | `"{label} must be in the format ##-#########-#"` — [mapping_service.py:59](Ocr_module/philhealth/mapping_service.py#L59) |

Enforcement point: `GET /api/claims/<id>/export/<form_key>` raises `ClaimIncompleteError` (HTTP 400) if `form_status["complete"]` is false, blocking PDF export — [Ocr_module/routes/claims_routes.py:88-91](Ocr_module/routes/claims_routes.py#L88-L91).

**Client-side (JS), separately:** `PClaimAssist/js/app.js` has its own, independent copy of the same required-field-presence check (`VAL_FIELDS`, used to highlight missing fields in the UI — see line 534 area), for all 4 forms (csf/cf2/cf3/pmrf), but this is presentational only — it does not call the backend and cannot block anything server-side since CF3/PMRF have no backend route at all.

If Chapter 3/4 presents 9 MF rules, 4 IF rules, 8 IC rules, 5 SP rules, 1 IQ rule, 2 CR rules (29 total), **all 29 must be flagged as NOT IMPLEMENTED** relative to current code — the only rule logic that exists is the 4 generic checks in the table above, applied to whichever fields are in each form's `VAL_FIELDS`/`DATE_FIELDS`/`ENUM_CHOICES` list.

---

## 8. IMAGE QUALITY CHECK

**Implemented (added after the initial scan — blur and brightness only; skew/deskew is still NOT IMPLEMENTED).** New module `Ocr_module/image_quality.py`, wired into `POST /ocr` / `POST /api/ocr` for plain image uploads (not PDFs — a PDF page is rendered internally by the PDF-text-extraction function and isn't available there as a decoded image array).

- **Blur**: variance of the Laplacian (`cv2.Laplacian(gray, cv2.CV_64F).var()`), a standard sharpness proxy — [Ocr_module/image_quality.py:27-33](Ocr_module/image_quality.py#L27-L33). Threshold `IMAGE_QUALITY_BLUR_THRESHOLD = 100.0` (env-overridable) — [Ocr_module/config.py](Ocr_module/config.py). Below this, `is_blurry = true`.
- **Brightness**: mean grayscale pixel intensity, 0–255 — [Ocr_module/image_quality.py:36-41](Ocr_module/image_quality.py#L36-L41). Thresholds `IMAGE_QUALITY_BRIGHTNESS_LOW = 60.0` / `IMAGE_QUALITY_BRIGHTNESS_HIGH = 200.0` (env-overridable) flag `is_too_dark` / `is_too_bright`.
- **Skew-angle measurement: still NOT IMPLEMENTED.**

**Important framing for the thesis:** these thresholds are explicitly documented in the code itself as *"a reasonable starting default, not a value derived from this project's own scanned logbooks yet"* — [Ocr_module/image_quality.py:16-23](Ocr_module/image_quality.py#L16-L23). They are commonly-cited rule-of-thumb values for these two well-known metrics, not numbers calibrated against this project's own dataset — don't present them in Chapter 4 as empirically derived without first validating them against real logbook scans.

**Behavior is advisory only, matching the project's existing confidence-badge pattern (§4) — it never blocks OCR or rejects an upload.** The result is attached to the JSON response as `"image_quality": {blur_score, is_blurry, brightness_score, is_too_dark, is_too_bright, warnings: [...]}` — [Ocr_module/routes/ocr_routes.py](Ocr_module/routes/ocr_routes.py). The calibration UI (`templates/index.html`) shows any warnings in a small amber banner next to the existing OCR summary line (`renderImageQualityBanner()`), styled consistently with the existing confidence heatmap (§4). Unit-tested on synthetic images (flat/solid-color, random-noise) in `Ocr_module/test_image_quality.py`.

The only other "quality"-adjacent numeric score in the codebase is the **template layout-match score** (`score_template_match`, 0.0–1.0, weighted combination of aspect-ratio/grid-line/row-count similarity) used to auto-select a calibration template — [Ocr_module/template_engine.py:217-299](Ocr_module/template_engine.py#L217-L299) — which is about matching a saved grid template to a new page, not image quality.

---

## 9. DATABASE SCHEMA

Source: [database/schema.sql](database/schema.sql) (8 tables, MariaDB/MySQL, InnoDB, utf8mb4) + [database/migrations/001_relax_pmrf_cf3_not_null.sql](database/migrations/001_relax_pmrf_cf3_not_null.sql).

### 9.1 `patients`
| Column | Type | Key | Description |
|---|---|---|---|
| id | INT UNSIGNED AUTO_INCREMENT | PK | |
| last_name | VARCHAR(100) NOT NULL | | |
| first_name | VARCHAR(100) NOT NULL | | |
| middle_name | VARCHAR(100) NULL | | |
| name_ext | VARCHAR(10) NULL | | |
| date_of_birth | DATE NOT NULL | | |
| sex | ENUM('Male','Female') NULL | | |
| pin | VARCHAR(20) NULL | | |
| address | VARCHAR(255) NULL | | **Added post-initial-scan** — [database/migrations/002_add_patient_address.sql](database/migrations/002_add_patient_address.sql). Now populated from the OCR logbook's `ADDRESS` column via `case_bridge.py`. |
| created_at / updated_at | DATETIME | | auto timestamps |

[schema.sql:29-41](database/schema.sql#L29-L41)

### 9.2 `case_sessions`
| Column | Type | Key | Description |
|---|---|---|---|
| id | INT UNSIGNED AI | PK | |
| logbook_case_number | VARCHAR(50) NULL | | free-text Case ID, **no UNIQUE constraint** (handled via app-level upsert) |
| case_name | VARCHAR(255) NULL | | |
| reviewed_values | JSON NOT NULL | | the OCR-reviewed free text per category |
| source_document | VARCHAR(500) NULL | | |
| reviewed_at / created_at | DATETIME | | |

[schema.sql:46-55](database/schema.sql#L46-L55)

### 9.3 `encounters`
| Column | Type | Key | Description |
|---|---|---|---|
| id | INT UNSIGNED AI | PK | |
| patient_id | INT UNSIGNED NOT NULL | FK → patients.id | |
| case_session_id | INT UNSIGNED NULL | FK → case_sessions.id, UNIQUE | links one OCR session to one encounter |
| date_admitted | DATE NOT NULL | | |
| time_admitted | VARCHAR(5) NULL | | |
| am_pm_admitted | ENUM('AM','PM') NULL | | |
| date_discharge / time_discharge / am_pm_discharge | DATE/VARCHAR(5)/ENUM | NULL | |
| disposition | ENUM('Improved','Recovered','Transferred','HAMA','Absconded','Expired') NULL | | |
| accommodation | ENUM('Non-Private','Private','Ward','ICU/NICU') NULL | | |
| chief_complaint / admission_dx / discharge_dx | TEXT NULL | | |
| created_at / updated_at | DATETIME | | |

[schema.sql:60-85](database/schema.sql#L60-L85)

### 9.4 `claims`
Largest table — ~85 columns spanning CF2/CSF/CF3/PMRF. PK `id`, FK `encounter_id` → `encounters.id` (UNIQUE). `status` ENUM('draft','ready','exported') DEFAULT 'draft' — [schema.sql:94](database/schema.sql#L94). Grouped sections: member info (CSF/PMRF), HCI/facility (CF2/CF3), employer (CSF), member profile (PMRF: civil_status, citizenship, mother/spouse names, member_type, profession, monthly_income), address/contact (PMRF), maternity/delivery (CF3: lmp, gravida, para, delivery_date, manner_of_delivery, fetal_outcome, birth_weight, apgar_score), physical exam (CF3), 20 fixed risk-factor BOOLEAN flags (CF3 page 2), MCP header fields, attending physician/date_signed. Full column list: [schema.sql:90-247](database/schema.sql#L90-L247). Per the file's own header comment, 8 CF3/PMRF-only columns were relaxed from NOT NULL to nullable so a draft claim can exist from CF2/CSF data alone — [schema.sql:8-14](database/schema.sql#L8-L14), [migrations/001_relax_pmrf_cf3_not_null.sql](database/migrations/001_relax_pmrf_cf3_not_null.sql).

### 9.5 `claim_prenatal_visits`
| Column | Type | Key |
|---|---|---|
| id | INT UNSIGNED AI | PK |
| claim_id | INT UNSIGNED NOT NULL | FK → claims.id |
| visit_number | TINYINT UNSIGNED NOT NULL | UNIQUE with claim_id (expected 2-12) |
| visit_date, aog, weight, cr, rr, bp, temp | DATE/VARCHAR/DECIMAL, all NULL | |

[schema.sql:252-268](database/schema.sql#L252-L268)

### 9.6 `claim_postpartum_care`
| Column | Type | Key |
|---|---|---|
| id | INT UNSIGNED AI | PK |
| claim_id | INT UNSIGNED NOT NULL | FK → claims.id |
| care_item | ENUM('perineal','complications','breastfeeding','family_planning','fp_service','referred_vss','schedule_next') NOT NULL | UNIQUE with claim_id |
| done | BOOLEAN DEFAULT FALSE | |
| remarks | TEXT NULL | |

[schema.sql:273-287](database/schema.sql#L273-L287)

### 9.7 `research_ground_truth`
| Column | Type | Key |
|---|---|---|
| id | INT UNSIGNED AI | PK |
| source_image | VARCHAR(500) NOT NULL | UNIQUE with field_name |
| field_name | VARCHAR(100) NOT NULL | |
| correct_text | TEXT NOT NULL | |
| created_at | DATETIME | |

[schema.sql:292-300](database/schema.sql#L292-L300). **Not currently written or read by any application code** — confirmed by [Ocr_module/benchmarks/README.md:150-156](Ocr_module/benchmarks/README.md#L150-L156) ("a natural next step, but out of scope"). Note a **MISMATCH within the repo's own docs**: [Ocr_module/ocr_testing_store.py:13-16](Ocr_module/ocr_testing_store.py#L13-L16) says *"there is no schema for this data in the project's MariaDB instance... documented ... as future intent only"*, which is itself stale — the tables are in fact already defined in `schema.sql` (this is a documentation inconsistency, not a code bug).

### 9.8 `research_ocr_results`
| Column | Type | Key |
|---|---|---|
| id | INT UNSIGNED AI | PK |
| ground_truth_id | INT UNSIGNED NOT NULL | FK → research_ground_truth.id, UNIQUE with engine |
| engine | ENUM('paddleocr','tesseract') NOT NULL | |
| extracted_text | TEXT NULL | |
| confidence | FLOAT NULL | |
| is_correct | BOOLEAN NULL | |
| error_type | ENUM('correct','misread_character','missed_field','wrong_segmentation','blank_output','other') NULL | |
| created_at | DATETIME | |

[schema.sql:305-322](database/schema.sql#L305-L322). Same "defined but unused" status as 9.7.

### Reference tables requested but NOT IMPLEMENTED
- **Diagnosis list** — NOT IMPLEMENTED. `admission_dx`/`discharge_dx` are free-text `TEXT` columns ([schema.sql:73-74](database/schema.sql#L73-L74)); no lookup/reference table of diagnosis codes or names exists.
- **Place names reference table** — NOT IMPLEMENTED. Addresses are free-text VARCHAR columns.
- **Confusion table** (OCR character-confusion pairs) — NOT IMPLEMENTED (see §5).
- **Format specs reference table** — NOT IMPLEMENTED as a DB table; format rules are hardcoded constants/regex in Python (`PIN_PATTERN`, `ENUM_CHOICES`, `_DATE_FORMATS` — §5/§7).
- **Rules table** — NOT IMPLEMENTED (see §7).
- **Validation logs table** — NOT IMPLEMENTED. Validation results are computed on-the-fly by `mapping_service.map_claim()` on every request/response; nothing is persisted to a log table.
- **Users table** — NOT IMPLEMENTED. No `users` table in `schema.sql`, no authentication code anywhere in the repo (confirmed by repo-wide search for `login`/`password`/`auth` — only hits were `DB_PASSWORD` env var and unrelated HTML `role=` ARIA attributes). See §12.
- **`approved_claims` / `rejected_claims` tables** — still NOT IMPLEMENTED as separate tables. The only status tracking is `claims.status ENUM('draft','ready','exported')` ([schema.sql:94](database/schema.sql#L94)). **Update (post-initial-scan):** this status now does transition — `SETUP.md`'s claim that *"nothing currently transitions it"* ([SETUP.md:579-580](SETUP.md#L579-L580)) is now stale. `claims_store.advance_status_if_forms_complete()` moves `draft → ready` once CF2 and CSF are both complete (called after claim generation/sync and after manual field correction), and `claims_store.mark_exported()` moves `ready → exported` once a PDF export actually succeeds (called from `routes/claims_routes.py`'s export route) — [Ocr_module/claims_store.py](Ocr_module/claims_store.py). The transition is deliberately monotonic (never regresses `ready`/`exported` back to an earlier status even if a later edit makes a field incomplete again) — this is a design choice, not a limitation, documented in the function's own docstring.

### Patient data written to the DB?
**Yes**, but only via two paths: (1) the **temporary diagnostic test route** `POST /diagnostic/patient_crud_test`, which inserts a clearly-marked fake row (`last_name='ZZ_DIAGNOSTIC_TEST'`) purely to verify DB connectivity, explicitly flagged for removal before submission — [Ocr_module/routes/diagnostic_routes.py:1-12,41-69](Ocr_module/routes/diagnostic_routes.py#L41-L69); and (2) the real OCR→claim bridge, `claims_store.create_or_update_claim_from_case_session()`, which inserts real `patients`/`encounters`/`claims` rows from reviewed OCR data — [Ocr_module/claims_store.py:78-136](Ocr_module/claims_store.py#L78-L136). **Note:** `SETUP.md`'s "WHAT IS NOT IMPLEMENTED YET" section ([SETUP.md:565-583](SETUP.md#L565-L583)) says *"nothing in the app creates real patient records yet outside the diagnostic test"* and *"Claims CRUD... have no backend routes yet"* — **this is now stale documentation; the current code contradicts it** (claims_store.py, case_bridge.py, and claims_routes.py all exist and implement exactly this bridge). Flag this as an outdated-docs MISMATCH if Chapter 3/4 cites SETUP.md's limitations list as current.

---

## 10. API ENDPOINTS / ROUTES

All registered in [Ocr_module/routes/__init__.py](Ocr_module/routes/__init__.py), plus two routes defined directly in `app.py`.

| Method | Route | Purpose | Citation |
|---|---|---|---|
| GET | `/` | Serves the OCR calibration UI (`templates/index.html`) | [app.py:39-41](Ocr_module/app.py#L39-L41) |
| GET | `/db_health` | DB connectivity diagnostic | [app.py:43-54](Ocr_module/app.py#L43-L54) |
| POST | `/ocr` | Run OCR on an uploaded image/PDF (engine=paddle/tesseract) | [routes/ocr_routes.py:121-129](Ocr_module/routes/ocr_routes.py#L121-L129) |
| POST | `/api/ocr` | Alias of `/ocr` | [routes/ocr_routes.py:132-135](Ocr_module/routes/ocr_routes.py#L132-L135) |
| POST | `/save_reviewed_result` | Persist reviewed OCR text to `case_sessions` | [routes/ocr_routes.py:138-201](Ocr_module/routes/ocr_routes.py#L138-L201) |
| GET | `/export_case_session` | Export a case session's reviewed values to `.xlsx` | [routes/ocr_routes.py:204-248](Ocr_module/routes/ocr_routes.py#L204-L248) |
| POST | `/save_grid_template` | Save a new calibration grid template (JSON file) | [routes/template_routes.py:37-66](Ocr_module/routes/template_routes.py#L37-L66) |
| GET | `/grid_templates` | List saved templates | [routes/template_routes.py:69-89](Ocr_module/routes/template_routes.py#L69-L89) |
| GET | `/grid_template` | Fetch one saved template by filename | [routes/template_routes.py:92-115](Ocr_module/routes/template_routes.py#L92-L115) |
| POST | `/match_template` | Score/auto-select best-matching template for an image | [routes/template_routes.py:118-147](Ocr_module/routes/template_routes.py#L118-L147) |
| POST | `/update_template_from_feedback` | Merge corrections back into a saved template | [routes/template_routes.py:150-168](Ocr_module/routes/template_routes.py#L150-L168) |
| POST | `/delete_grid_template` | Delete a saved template file | [routes/template_routes.py:171-192](Ocr_module/routes/template_routes.py#L171-L192) |
| POST | `/detect_row_columns` | Detect column x-positions via vertical-edge projection | [routes/layout_routes.py:39-103](Ocr_module/routes/layout_routes.py#L39-L103) |
| POST | `/detect_vertical_lines` | Detect vertical grid lines | [routes/layout_routes.py:106-127](Ocr_module/routes/layout_routes.py#L106-L127) |
| POST | `/align_template` | Align a saved template's grid lines to a new page | [routes/layout_routes.py:130-170](Ocr_module/routes/layout_routes.py#L130-L170) |
| POST | `/propagate_rows` | Generate evenly-spaced row positions | [routes/layout_routes.py:173-198](Ocr_module/routes/layout_routes.py#L173-L198) |
| POST | `/detect_content_rows` | Detect row boundaries from actual ink content | [routes/layout_routes.py:201-240](Ocr_module/routes/layout_routes.py#L201-L240) |
| POST | `/auto_place_template` | Place full template (lines+rows+cells) on an image | [routes/layout_routes.py:243-273](Ocr_module/routes/layout_routes.py#L243-L273) |
| POST | `/process_pdf_batch` | Run template+OCR across every page of a PDF | [routes/layout_routes.py:276-344](Ocr_module/routes/layout_routes.py#L276-L344) |
| POST | `/save_crop` | Save a manually-cropped training image | [routes/crop_routes.py:17-38](Ocr_module/routes/crop_routes.py#L17-L38) |
| POST | `/api/testing/rows` | Append rows to the PaddleOCR-vs-Tesseract comparison workbook | [routes/testing_routes.py:66-80](Ocr_module/routes/testing_routes.py#L66-L80) |
| POST | `/api/testing/clear` | Wipe the comparison workbook | [routes/testing_routes.py:83-89](Ocr_module/routes/testing_routes.py#L83-L89) |
| GET | `/api/testing/summary` | Row count / workbook path | [routes/testing_routes.py:92-98](Ocr_module/routes/testing_routes.py#L92-L98) |
| GET | `/api/testing/download` | Download the comparison workbook (.xlsx) | [routes/testing_routes.py:101-115](Ocr_module/routes/testing_routes.py#L101-L115) |
| POST | `/api/claims/generate` | Bridge a reviewed case session into patients/encounters/claims | [routes/claims_routes.py:39-53](Ocr_module/routes/claims_routes.py#L39-L53) |
| GET | `/api/claims/<id>` | Get mapped/validated claim view | [routes/claims_routes.py:56-61](Ocr_module/routes/claims_routes.py#L56-L61) |
| PUT | `/api/claims/<id>` | Apply manual corrections to patient/encounter/claim fields | [routes/claims_routes.py:64-74](Ocr_module/routes/claims_routes.py#L64-L74) |
| GET | `/api/claims/<id>/export/<form_key>` | Export filled CF2/CSF PDF (form_key ∈ {cf2, csf} only) | [routes/claims_routes.py:77-101](Ocr_module/routes/claims_routes.py#L77-L101) |
| POST | `/diagnostic/patient_crud_test` | **Temporary** — INSERT+SELECT test row in `patients` | [routes/diagnostic_routes.py:41-80](Ocr_module/routes/diagnostic_routes.py#L41-L80) |

**No routes exist for CF3 or PMRF export/mapping** — `_SUPPORTED_FORMS = ("cf2", "csf")` — [routes/claims_routes.py:25](Ocr_module/routes/claims_routes.py#L25) and `OVERLAYS = {"cf2": ..., "csf": ...}` — [Ocr_module/philhealth/overlays/__init__.py:13-16](Ocr_module/philhealth/overlays/__init__.py#L13-L16). All 4 real PDF templates exist on disk ([PClaimAssist/forms/CF2.pdf, CF3.pdf, CSF.pdf, PMRF.pdf](PClaimAssist/forms)), and the frontend has JS overlay coordinate maps for all 4 forms ([PClaimAssist/js/pdf/overlays/{csf,cf2,cf3,pmrf}.js](PClaimAssist/js/pdf/overlays)), but server-side mapping/validation/PDF-fill is CF2/CSF only.

---

## 11. SAMPLE DATA

**Diagnosis list sample data: NOT IMPLEMENTED** — no such table/file exists (§9). Diagnoses appear only as free-text example strings in fixture/sample data:
- `admissionDx: 'Term Pregnancy in Active Labor, 39 weeks AOG'`, `dischargeDx: 'Normal Spontaneous Delivery, Full Term, Live Birth'` — [PClaimAssist/js/app.js:112-114](PClaimAssist/js/app.js#L112-L114) (fictional `SAMPLE_DATA` patient "Maria Dela Cruz", explicitly labeled fictional in the file — [app.js:96](PClaimAssist/js/app.js#L96)).

**OCR confusion table sample data: NOT IMPLEMENTED** — no confusion table exists anywhere (§5/§9). There is nothing to sample for Figure 3.2 as described; if the figure requires confusion-table rows, that data must be newly authored, not extracted from this codebase.

Closest real artifacts available instead:
- `benchmarks/compare_ocr_engines.py`'s `accuracy_results.csv` output format (`image_name, ocr_engine, character_error_rate, word_error_rate, character_accuracy_percent, word_accuracy_percent`) — [Ocr_module/benchmarks/compare_ocr_engines.py:65-69](Ocr_module/benchmarks/compare_ocr_engines.py#L65-L69) — this is a per-image engine accuracy comparison, not a character-confusion table.
- `ocr_testing_store.py`'s per-field comparison sheet columns (`Test ID, Spread ID, Source File, PDF Page, Side, Patient ID, Field, Ground Truth, PaddleOCR Output, Paddle Confidence, TesseractOCR Output, Tesseract Confidence, Best Engine, Saved At`) — [Ocr_module/ocr_testing_store.py:28-43](Ocr_module/ocr_testing_store.py#L28-L43) — a real, implemented artifact, but it's a manual side-by-side comparison tool, not an automated confusion table.

---

## 12. USER ROLES

**NOT IMPLEMENTED.** There is no authentication, no login/session system, no role-based access control anywhere in the repo. Confirmed by a repo-wide search for `login`, `password`, `auth`, `role`, `session[` — the only hits were: the `DB_PASSWORD` config variable ([config.py:92](Ocr_module/config.py#L92), a DB credential, not a user password), HTML `role="tablist"`/`role="presentation"` ARIA attributes (accessibility markup, unrelated to app roles), and one **static, hardcoded** UI label:

```html
<div class="user-name">Clinic Staff</div>
<div class="user-role">Claims Encoder</div>
```
— [PClaimAssist/index.html:52-53](PClaimAssist/index.html#L52-L53)

This is plain decorative text in the navbar — not backed by any login, user table, session, or permission check. There is exactly one "role" shown and it never changes. If Chapter 3/4 describes multiple user roles (e.g. Encoder vs. Reviewer vs. Admin) with different permissions, **that entire feature is NOT IMPLEMENTED** — flag it accordingly.

---

## 13. PROCESSING PIPELINE

Actual module call order, traced from the routes:

**A. OCR extraction (`POST /ocr` or `/api/ocr`)**
1. `utils.uploads.require_file()` — validate a file was uploaded — [routes/ocr_routes.py:60](Ocr_module/routes/ocr_routes.py#L60)
2. Engine selection (`paddle` default, or `tesseract`) — [routes/ocr_routes.py:63-68](Ocr_module/routes/ocr_routes.py#L63-L68)
3. File saved to `config.UPLOAD_FOLDER` — [routes/ocr_routes.py:70-72](Ocr_module/routes/ocr_routes.py#L70-L72)
4. `ocr_engine.extract_text()` (image) or `extract_pdf_text()` (PDF, via `fitz` page-to-image rendering at 2x matrix then per-page OCR) — [ocr_engine.py:38-58,84-110](Ocr_module/ocr_engine.py#L38-L58) — **no preprocessing step between load and OCR call** (§1/§8)
5. Tokens tagged with the selected `category` — [routes/ocr_routes.py:81-84](Ocr_module/routes/ocr_routes.py#L81-L84)
6. If a template payload was supplied, `template_store.update_template_from_session()` merges learned grid-line/row offsets back into the saved template — [routes/ocr_routes.py:88-105](Ocr_module/routes/ocr_routes.py#L88-L105)
7. JSON response with tokens + per-token confidence returned to the review UI

**B. Template calibration / batch PDF processing** (`/match_template`, `/auto_place_template`, `/process_pdf_batch`)
1. `analyze_document_layout()` — grayscale → Gaussian blur → Canny edges → vertical/horizontal projection → coarse layout features — [template_engine.py:168-214](Ocr_module/template_engine.py#L168-L214)
2. `match_templates()` → `score_template_match()` picks the best saved template by weighted layout similarity — [template_engine.py:217-325](Ocr_module/template_engine.py#L217-L325)
3. `align_template()` — brute-force offset search (±50px) to snap template grid lines to actually-detected vertical lines — [template_engine.py:406-459](Ocr_module/template_engine.py#L406-L459)
4. `detect_content_rows()` — ink-mask → coarse row bands (smoothed density thresholding) → connected-component band refinement → uniform-propagation fallback for any remaining page height — [template_engine.py:462-692](Ocr_module/template_engine.py#L462-L692)
5. `generate_cells()` — cartesian product of column boundaries × row bands → `Cell` objects — [template_engine.py:815-864](Ocr_module/template_engine.py#L815-L864)
6. `extract_crop_from_cell()` / `BatchProcessor._extract_cell_image()` — crop each cell from the full-page image — [template_engine.py:867-892](Ocr_module/template_engine.py#L867-L892), [batch_processor.py:250-264](Ocr_module/batch_processor.py#L250-L264)
7. (Batch only) each cropped cell passed to `ocr_engine.extract_text_from_array()` via the `ocr_wrapper` callback — [routes/layout_routes.py:303-312](Ocr_module/routes/layout_routes.py#L303-L312)
8. For 2-page spreads: odd-page row positions (as height-relative fractions) are carried forward and forced onto the paired even page instead of re-detecting — [batch_processor.py:61-101](Ocr_module/batch_processor.py#L61-L101)

**C. Review → persistence** (`/save_reviewed_result`)
1. Reviewed free text (keyed by category) replaces — never merges with — any prior stored values for that Case ID — [routes/ocr_routes.py:176-196](Ocr_module/routes/ocr_routes.py#L176-L196)
2. `case_session_store.save_reviewed_session()` — lookup-then-upsert against `case_sessions.logbook_case_number` — [case_session_store.py:32-69](Ocr_module/case_session_store.py#L32-L69)

**D. OCR → PhilHealth claim bridge** (`POST /api/claims/generate`)
1. `case_session_store.get_reviewed_session(case_id)` — fetch the reviewed values — [claims_store.py:96-100](Ocr_module/claims_store.py#L96-L100)
2. `case_bridge.draft_patient_and_encounter(values)` — parse NAME/BDAY/dates/times/diagnoses into structured `patients`/`encounters` fields, collecting warnings for anything unparseable — [case_bridge.py:114-179](Ocr_module/philhealth/case_bridge.py#L114-L179)
3. Insert-or-update `patients` → `encounters` (linked via `case_session_id`) → `claims` (HCI defaults applied) in one transaction — [claims_store.py:104-136](Ocr_module/claims_store.py#L104-L136)

**E. Claim view / export** (`GET/PUT /api/claims/<id>`, `GET /api/claims/<id>/export/<form>`)
1. `claims_store.get_claim()` — 3 separate SELECTs (patients/encounters/claims) — [claims_store.py:139-161](Ocr_module/claims_store.py#L139-L161)
2. `mapping_service.map_claim()` — build flat data → validate → resolve computed values → per-form completeness status — [mapping_service.py:80-123](Ocr_module/philhealth/mapping_service.py#L80-L123)
3. (Export only) gate on `form_status["complete"]`, then `pdf_export.export_claim_pdf()` — PyMuPDF opens the real CF2/CSF template, overlays resolved field values at pre-calibrated coordinates, returns bytes — [pdf_export.py:54-79](Ocr_module/philhealth/pdf_export.py#L54-L79)

---

## 14. OTHER IMPLEMENTED FEATURES NOT ELSEWHERE IN THIS LIST

- **PaddleOCR vs. Tesseract benchmarking suite** — a standalone CLI (`python -m benchmarks.compare_ocr_engines`), not wired into the Flask app, with its own warm-up methodology, CER/WER scoring (via `benchmarks/metrics.py`, matching the WER/CER formulas of Nazeem et al. 2024 ICON), and documented literature comparison — [Ocr_module/benchmarks/compare_ocr_engines.py](Ocr_module/benchmarks/compare_ocr_engines.py), [Ocr_module/benchmarks/README.md](Ocr_module/benchmarks/README.md).
- **Side-by-side OCR engine testing UI** inside the calibration page, saving results to an ever-accumulating `.xlsx` workbook (not the database) — [Ocr_module/routes/testing_routes.py](Ocr_module/routes/testing_routes.py), [Ocr_module/ocr_testing_store.py](Ocr_module/ocr_testing_store.py).
- **Template "learning" from feedback** — every OCR run and every manual feedback submission can merge corrected grid-line/row positions back into a saved template's `learnedOffsets` history — [Ocr_module/template_store.py:53-94](Ocr_module/template_store.py#L53-L94).
- **Per-row Filipino surname-particle handling** in name splitting (§5) — a specific heuristic for "Dela Cruz", "De Los Santos", etc., not a generic Western-name assumption.
- **Manual field-training/crop-capture tool** — lets a user crop and label individual logbook fields into `uploads/training/<CATEGORY>/` for future model training (folders already populated for 8 of the 9 categories, confirmed on disk: ADDRESS, ADMITTING_DIAGNOSIS, BDAY, CASE, DATE__TIME_OF_ADMISSION, DATE__TIME_OF_DELIVERY, DATE__TIME_OF_DISCHARGE, FINAL_DIAGNOSIS, NAME) — [Ocr_module/routes/crop_routes.py](Ocr_module/routes/crop_routes.py), [Ocr_module/config.py:128-142](Ocr_module/config.py#L128-L142).
- **Centralized JSON error-handling layer** — every route error (expected or not) returns the same flat `{"success": false, "error": "...", "error_code": "..."}` shape, including Flask/Werkzeug HTTP errors (404/413/405) — [Ocr_module/errors.py](Ocr_module/errors.py).
- **PII-safe routing discipline** — claims endpoints are explicitly documented/designed to never put patient/member identifiers in a URL or log line, addressed only by opaque integer claim id — [Ocr_module/routes/claims_routes.py:9-11](Ocr_module/routes/claims_routes.py#L9-L11).
- **"Draft" claim status model** — `claims.status` defaults to `'draft'` to represent a CF2/CSF-only claim before CF3/PMRF data exists, per the migration's stated rationale — [database/schema.sql:94](database/schema.sql#L94), [database/migrations/001_relax_pmrf_cf3_not_null.sql:1-19](database/migrations/001_relax_pmrf_cf3_not_null.sql#L1-L19). **Now transitions** `draft → ready → exported` (see §9's updated note).
- **Image quality assessment** (blur + brightness, advisory only) — added post-initial-scan; see updated §8.
- **OCR logbook → database field coverage extended** — `ADDRESS` and `DATE & TIME OF DELIVERY` (previously silently dropped) now reach `patients.address` and `claims.delivery_date`/`delivery_time`/`am_pm_delivery` respectively; see updated §3 and §9.
- **Frontend "privacy-by-design" claim retired**: `PClaimAssist/js/app.js`'s file header used to say *"Privacy-by-design: no storage, no server calls"*, which stopped being true for the system as a whole once `/api/claims/*` started persisting claim data to MariaDB. The header now says app.js itself keeps form data in memory only and makes no API calls, while OCR, claim storage and server-side PDF export are handled by the Flask backend — [PClaimAssist/js/app.js:1-5](PClaimAssist/js/app.js#L1-L5). Don't describe the system as "no storage, no server calls" in the paper.
