# CH4_FACTS.md — Codebase facts for Chapter 4 (Technical Output)

Collected from the repository on **2026-10-26**, branch `forms-cf2-cf4-design-update`, HEAD `52c55cb`.
Every fact cites a file (and line where useful). Where something asked for does not exist in the code, it says **NOT FOUND**. Where the code differs from the design values you gave, it is flagged **DIFFERS** (summarised in §14).

The system is two codebases served by one Flask process:

- `Ocr_module/` — Python/Flask backend: OCR pipeline, correction, claim mapping, PDF export (PyMuPDF), MariaDB access, auth.
- `PClaimAssist/` — static HTML/CSS/JS frontend: Patient details + CSF/CF2/CF4/PMRF entry forms, the rule-based validation engine, and client-side PDF filling (pdf-lib). Flask serves these files as-is (not through Jinja2).

> Note: there is an older `CHAPTER_DETAILS.md` (dated 2026-10-02). Several of its statements are now out of date (e.g. it says CF3 exists and that fuzzy matching is not implemented). Use this file instead.

---

## 1. FOLDER TREE

Skipped: `venv/`, `node_modules/` (none exists), `__pycache__/`, `uploads/`.

```
YD PCLAIM/
├── PClaimAssist.bat               one-click start (MariaDB + Flask, opens browser)
├── SETUP.md  CHANGELOG.md  CHAPTER_DETAILS.md
├── .githooks/pre-commit           runs tools/changelog_screenshots.py
├── tools/
│   ├── autostart.ps1              adds PClaimAssist.bat /background to Windows Startup
│   └── changelog_screenshots.py
├── docs/screenshots/              18 .jpg page screenshots (2026-10-15 … 10-26)
├── database/
│   ├── schema.sql                 base schema (8 tables)
│   └── migrations/                001 … 010 (.sql)
├── PClaimAssist/                  FRONTEND (static, served by Flask)
│   ├── index.html                 main app: Home, Patient details, CSF, CF2, CF4, PMRF, Check, Profile, Settings
│   ├── login.html  ocr.html  logbook-setup.html   (ocr/logbook-setup wrap backend pages in an iframe)
│   ├── css/                       style.css, easy.css, ocr.css
│   ├── forms/                     CSF.pdf, CF2.pdf, CF4.pdf, CF4-Blank.pdf, PMRF.pdf
│   └── js/
│       ├── app.js                 state, field propagation, validation UI, dashboard, settings
│       ├── validation-rules.js    RULE-BASED VALIDATION ENGINE (31 rules)
│       ├── ocr-review.js          Accept/Edit/Reject suggestion UI (PCAReview)
│       ├── claim-loader.js        loads a claim from the OCR review, autosaves it
│       ├── mother-baby.js  dx-templates.js  entry-learning.js
│       ├── auth-client.js  login.js  sidebar.js  easy.js  ocr.js
│       ├── box-input.js  date-text.js  pin-input.js
│       └── pdf/
│           ├── pdf-overlay.js     preview + pdf-lib export of all 4 forms
│           ├── pdf-calibrate.js   drag/resize overlay calibration tool
│           └── overlays/          csf.js, cf2.js, cf4.js, pmrf.js, index.js (field coordinates)
└── Ocr_module/                    BACKEND (Flask)
    ├── app.py                     create_app(), static frontend, /ocr-workspace, /review, /db_health
    ├── config.py                  every threshold/setting (env-overridable)
    ├── auth.py  user_store.py  create_admin.py
    ├── db.py  errors.py  logging_setup.py
    ├── image_quality.py           IQ-01 blur/brightness check
    ├── ocr_engine.py              PaddleOCR wrapper (+ batched reading)
    ├── ocr_tesseract.py           Tesseract wrapper (testing/benchmark only)
    ├── logbook_pipeline.py        upload → pages → template → cells → OCR → routing → rows
    ├── logbook_layout.py          printed-header reading, column proposal
    ├── logbook_setup.py           guided "set up a logbook" (column calibration)
    ├── template_engine.py         ruling-line/row/column detection, template matching, cropping
    ├── batch_processor.py         older whole-PDF batch OCR (calibration workspace)
    ├── paddle_assist.py           CORRECTION MODULE (ensemble + patterns + fuzzy vocabulary)
    ├── review_jobs.py             background reading jobs + progress
    ├── case_session_store.py  claims_store.py  clinic_settings_store.py
    ├── pattern_store.py  entry_store.py  template_store.py  ocr_testing_store.py
    ├── philhealth/
    │   ├── field_catalog.py       THE field-to-form mapping
    │   ├── case_bridge.py         OCR text → patients/encounters/claims columns (date/time/name parsing)
    │   ├── review_fields.py       review input kinds + server-side safeguards
    │   ├── form_prefill.py        claim → form values + per-field source status
    │   ├── mapping_service.py     CF2/CSF required-field + format validation
    │   ├── address_parser.py      address → lot/street/subdivision/barangay/city/province
    │   ├── mother_baby.py         mother/baby detection and linking
    │   ├── pdf_export.py          PyMuPDF fill of CF2/CSF
    │   └── overlays/              cf2.py, csf.py (coordinates ported from the JS overlays)
    ├── routes/                    12 blueprints (auth, ocr, template, layout, crop, testing,
    │                              claims, review, settings, learning, setup, diagnostic)
    ├── templates/                 index.html, review.html, logbook_setup.html  (Jinja2)
    ├── utils/uploads.py
    ├── grid_templates/            2 saved logbook setups (left/right page) .json
    ├── ocr_models/                en_PP-OCRv3_det_infer, en_PP-OCRv4_rec_infer, ch_ppocr_mobile_v2.0_cls_infer
    ├── benchmarks/                compare_ocr_engines.py, engine_adapters.py, metrics.py, image_loader.py, test_data/
    ├── test_fixtures/grid_templates/
    ├── test_*.py                  10 unittest files, 235 test methods
    ├── requirements.txt  .env.example
    └── run_ocr.bat  setup_ocr.bat  run_phpmyadmin.sh
```

---

## 2. VERSIONS

### Python
- **Python 3.12.1** — `Ocr_module/venv/pyvenv.cfg` (`version = 3.12.1`); `SETUP.md` and `setup_ocr.bat` tell users to install Python 3.12.

### Key packages (from `Ocr_module/requirements.txt`, which is a full `pip freeze`)
| Package | Version |
|---|---|
| Flask | 3.1.3 |
| flask-cors | 6.0.5 |
| Werkzeug | 3.1.8 |
| Jinja2 | 3.1.6 |
| paddleocr | 2.8.1 |
| paddlepaddle | 2.6.2 (CPU build; `use_gpu=False`) |
| pytesseract | 0.3.13 |
| opencv-python | 4.11.0.86 |
| opencv-contrib-python | 4.10.0.84 (both are pinned) |
| numpy | 1.26.4 |
| RapidFuzz | 3.14.5 (**installed but never imported** — see §6) |
| PyMuPDF | 1.27.2.3 |
| pandas | 3.0.3 |
| openpyxl | 3.1.5 |
| **MariaDB/MySQL driver: PyMySQL** | 1.1.1 (raw DB-API with DictCursor, no ORM) |
| bcrypt | 5.0.0 |
| pillow | 12.2.0 |
| scikit-image | 0.26.0 |
| shapely | 2.1.2 |
| pyclipper | 1.4.0 |

Full pinned list (108 lines): aiohappyeyeballs 2.6.2, aiohttp 3.14.0, aiosignal 1.4.0, aistudio-sdk 0.3.8, annotated-doc 0.0.4, annotated-types 0.7.0, anyio 4.13.0, astor 0.8.1, attrs 26.1.0, bce-python-sdk 0.9.71, bcrypt 5.0.0, beautifulsoup4 4.14.3, blinker 1.9.0, certifi 2026.5.20, chardet 7.4.3, charset-normalizer 3.4.7, click 8.4.1, colorama 0.4.6, colorlog 6.10.1, contourpy 1.3.3, crc32c 2.8, cycler 0.12.1, Cython 3.2.5, decorator 5.3.1, et_xmlfile 2.0.0, filelock 3.29.1, fire 0.7.1, Flask 3.1.3, flask-cors 6.0.5, fonttools 4.63.0, frozenlist 1.8.0, fsspec 2026.4.0, future 1.0.0, h11 0.16.0, hf-xet 1.5.0, httpcore 1.0.9, httpx 0.28.1, huggingface_hub 1.17.0, idna 3.18, ImageIO 2.37.3, imagesize 2.0.0, imgaug 0.4.0, itsdangerous 2.2.0, Jinja2 3.1.6, kiwisolver 1.5.0, lazy-loader 0.5, lmdb 2.2.1, lxml 6.1.1, markdown-it-py 4.2.0, MarkupSafe 3.0.3, matplotlib 3.10.9, mdurl 0.1.2, modelscope 1.37.1, multidict 6.7.1, networkx 3.6.1, numpy 1.26.4, opencv-contrib-python 4.10.0.84, opencv-python 4.11.0.86, openpyxl 3.1.5, opt-einsum 3.3.0, packaging 26.2, paddleocr 2.8.1, paddlepaddle 2.6.2, pandas 3.0.3, pillow 12.2.0, prettytable 3.17.0, propcache 0.5.2, protobuf 3.20.2, psutil 7.2.2, PyMySQL 1.1.1, py-cpuinfo 9.0.0, pytesseract 0.3.13, pyclipper 1.4.0, pycryptodome 3.23.0, pydantic 2.13.4, pydantic_core 2.46.4, Pygments 2.20.0, PyMuPDF 1.27.2.3, pyparsing 3.3.2, pypdfium2 5.9.0, python-bidi 0.6.10, python-dateutil 2.9.0.post0, python-docx 1.2.0, PyYAML 6.0.2, RapidFuzz 3.14.5, requests 2.34.2, rich 15.0.0, ruamel.yaml 0.19.1, safetensors 0.7.0, scikit-image 0.26.0, scipy 1.17.1, setuptools 82.0.1, shapely 2.1.2, shellingham 1.5.4, six 1.17.0, soupsieve 2.8.4, termcolor 3.3.0, tifffile 2026.3.3, tqdm 4.67.3, typer 0.25.1, typing-inspection 0.4.2, typing_extensions 4.15.0, tzdata 2026.2, ujson 5.12.1, urllib3 2.7.0, wcwidth 0.7.0, Werkzeug 3.1.8, yarl 1.24.2.

**Installed vs requirements.txt:** `venv\Scripts\python -m pip freeze` matches `requirements.txt` exactly, except for 10 extra packages installed locally but not listed: playwright 1.64.0, greenlet 3.5.6, pyee 14.0.0, docstring_parser 0.18.0, httpcore2 2.13.1, httpx2 2.13.1, jiter 0.17.0, opentelemetry-api 1.45.1, sniffio 1.3.1, truststore 0.10.5. (Playwright is used by `tools/changelog_screenshots.py`.)

**MariaDB server version:** NOT FOUND in the repo (it comes from the local XAMPP install; `/db_health` reports it at runtime).

### Frontend libraries (CDN, exact versions)
| Library | Version | Where |
|---|---|---|
| Bootstrap (CSS + bundle JS) | **5.3.3** | `PClaimAssist/index.html:7,3716`; also `login.html`, `ocr.html`, `logbook-setup.html` |
| Bootstrap Icons | 1.11.3 | `PClaimAssist/index.html:8` |
| AOS | 2.3.4 | `PClaimAssist/index.html:9,3717` |
| pdf.js | 3.11.174 | `PClaimAssist/index.html:3719` (preview) |
| pdf-lib | 1.17.1 | `PClaimAssist/index.html:3721` (PDF filling) |
| Cropper.js | 1.6.2 | `Ocr_module/templates/index.html:9,12` (calibration workspace) |
| pdf.js (workspace) | 2.16.105 | `Ocr_module/templates/index.html:2905` |

The backend's Jinja pages `review.html` and `logbook_setup.html` load no CDN library (plain CSS/JS).

### Is Jinja2 used for pages?
**Partly.** Jinja2 (via Flask `render_template`) renders only the three backend pages:
- `/ocr-workspace` → `templates/index.html` (passes `accept`, `review` thresholds) — `app.py:74-80`
- `/review` → `templates/review.html` (passes `accept`, `review`, `forms_url`, `claim_required`) — `app.py:82-90`
- `/logbook-setup` → `templates/logbook_setup.html` (passes `sides`, `required`, `check_id`) — `routes/setup_routes.py:37-46`

The clinic-facing PClaimAssist pages (`login.html`, `index.html`, `ocr.html`, `logbook-setup.html`) are **static files** served by `send_from_directory` (`app.py:64-70`), not Jinja templates.

---

## 3. ROUTES

All registered in `Ocr_module/routes/__init__.py` + `app.py`. "Auth" column: **—** = no login check in code; **login** = `@auth.login_required`; **admin** = `@auth.role_required("admin")`.

### App-level (`app.py`)
| URL | Method | Auth | What it does | Returns |
|---|---|---|---|---|
| `/` | GET | — | PClaimAssist sign-in page | static `PClaimAssist/login.html` |
| `/<path:filename>` | GET | — | Any PClaimAssist file (pages, JS, CSS, `forms/*.pdf`) | static file |
| `/ocr-workspace` | GET | — | OCR calibration/template workspace | Jinja `templates/index.html` |
| `/review` | GET | — | Logbook Reader (upload → check each patient row) | Jinja `templates/review.html` |
| `/db_health` | GET | — | Tests the MariaDB connection | JSON `{success, database, server_version}` |

### `auth_routes.py` (prefix `/api/auth`)
| URL | Method | Auth | What it does |
|---|---|---|---|
| `/api/auth/status` | GET | — | `{has_accounts}` (fresh install?) |
| `/api/auth/register` | POST | — | Self-registration. First account = active admin, signed in; later accounts = inactive encoder awaiting approval |
| `/api/auth/login` | POST | — | Email + password → session cookie |
| `/api/auth/logout` | POST | — | Clears session |
| `/api/auth/me` | GET | login | Current user |
| `/api/auth/password` | POST | login | Change own password (current password required) |
| `/api/auth/users` | GET | admin | List accounts |
| `/api/auth/users` | POST | admin | Create account (`role` default `encoder`) |
| `/api/auth/users/<id>` | PATCH | admin | `{is_active}` approve / switch off (cannot switch off self) |
| `/api/auth/users/<id>/password` | POST | admin | Set a new password for someone |
All return JSON.

### `ocr_routes.py` (no prefix)
| URL | Method | Auth | What it does | Returns |
|---|---|---|---|---|
| `/ocr`, `/api/ocr` | POST | — | OCR one uploaded image/PDF; form field `engine` = `paddle` (default) or `tesseract`; adds advisory `image_quality` | JSON `{raw_text, tokens, engine, image_quality}` |
| `/save_reviewed_result` | POST | — | Saves reviewed values for a `case_id` into `case_sessions` | JSON |
| `/export_case_session?case_id=` | GET | — | One saved case session → Excel (pandas + openpyxl) | `.xlsx` download |

### `template_routes.py` (calibration workspace, no prefix)
| URL | Method | Auth | What it does |
|---|---|---|---|
| `/save_grid_template` | POST | — | Save a grid template JSON to `grid_templates/` |
| `/grid_templates` | GET | — | List saved templates |
| `/grid_template?filename=` | GET | — | Load one template |
| `/match_template` | POST | — | Best-matching saved template for an uploaded page |
| `/update_template_from_feedback` | POST | — | Update a template from a reviewed placement |
| `/delete_grid_template` | POST | — | Delete a template |
All JSON.

### `layout_routes.py` (calibration workspace, no prefix)
| URL | Method | Auth | What it does |
|---|---|---|---|
| `/detect_row_columns` | POST | — | Canny/projection column detection on an uploaded row image |
| `/detect_vertical_lines` | POST | — | Vertical line detection |
| `/align_template` | POST | — | Align a saved template to a page |
| `/propagate_rows` | POST | — | Generate repeated rows from a first row |
| `/detect_content_rows` | POST | — | Row bands from ink density |
| `/auto_place_template` | POST | — | Place a whole template (columns + rows) on a page |
| `/process_pdf_batch` | POST | — | OCR every page of a PDF with a template (`BatchProcessor`) |
All JSON.

### `crop_routes.py`, `testing_routes.py`, `diagnostic_routes.py`
| URL | Method | Auth | What it does | Returns |
|---|---|---|---|---|
| `/save_crop` | POST | — | Save a training crop into `uploads/training/<category>/` | JSON |
| `/api/testing/rows` | POST | — | Append PaddleOCR-vs-Tesseract comparison rows to the running workbook | JSON |
| `/api/testing/clear` | POST | — | Clear the workbook | JSON |
| `/api/testing/summary` | GET | — | Row count + path | JSON |
| `/api/testing/download` | GET | — | Download `uploads/ocr_testing_results.xlsx` | `.xlsx` |
| `/diagnostic/patient_crud_test` | POST | — | **TEMPORARY** Phase-1 DB test: inserts a `ZZ_DIAGNOSTIC_TEST` patient and reads it back | JSON |

### `review_routes.py` (prefix `/api/review`) — Logbook Reader
| URL | Method | Auth | What it does |
|---|---|---|---|
| `/api/review/upload` | POST | — | Synchronous: read whole scan, create one pending `case_sessions` row per patient row |
| `/api/review/jobs` | POST | — | Same, as background job → `202 {job_id}` |
| `/api/review/jobs/checked` | POST | login | Read a scan whose columns were just checked in logbook setup (`{setup_id, pages}`) → job id. Called from the "check the columns" step (`templates/logbook_setup.html:369`); review.html then polls `/jobs/<job_id>`. |
| `/api/review/jobs/<job_id>` | GET | — | Job progress, then the result payload |
| `/api/review/uploads/<upload_id>` | GET | — | All sessions from one upload |
| `/api/review/sessions/<id>` | GET | — | One session with its OCR fields |
| `/api/review/sessions/<id>` | PUT | — | Submit reviewer values (`values`, `parts`, `defer_manual`, `confirm_warnings`); runs safeguards; marks reviewed; teaches the correction model |
| `/api/review/crops/<upload_id>/<filename>` | GET | — | Cell/row crop PNG |
All JSON except the crop (PNG).

### `claims_routes.py` (prefix `/api/claims`)
| URL | Method | Auth | What it does | Returns |
|---|---|---|---|---|
| `/api/claims/generate` | POST | — | Reviewed session (`session_id` or `case_id`) → patient/encounter/claim rows | JSON `{claim_id, warnings}` |
| `/api/claims/<id>` | GET | — | Mapped + validated CF2/CSF view | JSON |
| `/api/claims/<id>` | PUT | — | Update patient/encounter/claim columns | JSON |
| `/api/claims/<id>/form-data` | GET | — | Claim as PClaimAssist form values (PMRF/CSF/CF2/CF4) + per-field source status + saved values | JSON |
| `/api/claims/<id>/form-values` | PUT | — | Autosave everything typed on the forms (`claims.form_values`) | JSON |
| `/api/claims/save` | POST | — | "Save patient": save values; with `claim_id: null` creates a new claim for a hand-typed patient | JSON |
| `/api/claims/<id>/family` | GET / PUT | — | Mother/baby role and link | JSON |
| `/api/claims/<id>/from-mother` | GET | — | Values a baby's claim copies from the mother's | JSON |
| `/api/claims/<id>/export/<cf2\|csf>` | GET | — | Server-side PyMuPDF PDF (only if required fields complete); marks claim `exported` | PDF download |

### `settings_routes.py`, `learning_routes.py`, `setup_routes.py`
| URL | Method | Auth | What it does | Returns |
|---|---|---|---|---|
| `/api/settings/clinic` | GET | login | Clinic name, PAN, address, representative, attending | JSON |
| `/api/settings/clinic` | POST | admin | Update them | JSON |
| `/api/learning/form-entries` | POST | login | On PDF export, count name/address/diagnosis values into `ocr_known_entries` | JSON |
| `/logbook-setup` | GET | — (page checks sign-in in JS) | Guided logbook setup page; `?check=<id>` = "check the columns" step | Jinja `logbook_setup.html` |
| `/api/logbook-setup/read` | POST | login | Read a scan's header → proposed columns/rows per page | JSON |
| `/api/logbook-setup/<setup_id>` | GET | login | Re-open a proposal | JSON |
| `/api/logbook-setup/<setup_id>/<picture>` | GET | login | Page preview `page<n>.jpg` | JPEG |
| `/api/logbook-setup/save` | POST | admin | Save checked columns as the logbook setup for later scans | JSON |
| `/api/logbook-setup/current` | GET | admin | Setups in use | JSON |

**Total:** 65 route handlers (5 app-level + 60 in blueprints). Most `/api/claims/*`, `/api/review/*`, OCR, template and testing endpoints have **no server-side login check**; the pages that call them check sign-in in the browser (`auth-client.js`).

---

## 4. DATABASE

MariaDB database `pclaimassist_db` (utf8mb4). Tables come from `database/schema.sql` (8 tables) + migrations 004–007 (4 new tables) = **12 tables**. No ORM; SQL is in the `*_store.py` modules.

### From `schema.sql` (after migrations 001–003, 010 applied)
**`patients`** — `id` PK, `last_name` VARCHAR(100) NOT NULL, `first_name` VARCHAR(100) NOT NULL, `middle_name` VARCHAR(100), `name_ext` VARCHAR(10), `date_of_birth` DATE NOT NULL, `sex` ENUM('Male','Female'), `pin` VARCHAR(20), `address` VARCHAR(255) *(migration 002)*, `created_at`, `updated_at`.

**`case_sessions`** (one logbook row / OCR review) — `id` PK, `logbook_case_number` VARCHAR(50), `case_name` VARCHAR(255), `reviewed_values` JSON NOT NULL, `ocr_data` JSON *(003: fields, confidences, statuses, image quality, AI readings)*, `source_document` VARCHAR(500), `upload_id` VARCHAR(64) *(003, indexed)*, `logbook_row` SMALLINT *(003)*, `review_status` ENUM('pending','reviewed') default 'reviewed' *(003)*, `reviewed_at`, `created_at`.

**`encounters`** — `id` PK, `patient_id` FK→patients, `case_session_id` FK→case_sessions (UNIQUE), `date_admitted` DATE NOT NULL, `time_admitted` VARCHAR(5), `am_pm_admitted` ENUM('AM','PM'), `date_discharge` DATE, `time_discharge`, `am_pm_discharge`, `disposition` ENUM('Improved','Recovered','Transferred','HAMA','Absconded','Expired'), `accommodation` ENUM('Non-Private','Private','Ward','ICU/NICU'), `chief_complaint` TEXT, `admission_dx` TEXT, `discharge_dx` TEXT, `created_at`, `updated_at`.

**`claims`** — `id` PK, `encounter_id` FK→encounters (UNIQUE), `status` ENUM('draft','ready','exported') default 'draft', `patient_role` ENUM('mother','baby','other') *(010)*, `mother_claim_id` FK→claims.id ON DELETE SET NULL *(010)*, `form_values` LONGTEXT *(010: everything typed on the forms, JSON)*, `created_at`, `updated_at`, then:
- member: `member_last_name`, `member_first_name`, `member_middle_name`, `member_name_ext`, `member_dob`, `member_sex`, `member_pin`, `relationship` ENUM('Self','Spouse','Child','Parent','Sibling') *(made nullable by 001)*
- HCI: `hci_pan` VARCHAR(20) NOT NULL, `hci_name` VARCHAR(255) NOT NULL, `hci_street`, `hci_city`, `hci_province`
- employer: `employer_pen`, `employer_phone`, `employer_name`
- PMRF profile: `civil_status` ENUM, `place_of_birth`, `citizenship`, `mother_last/first/middle_name`, `spouse_last/first/middle_name`, `member_type` ENUM(8 values), `profession`, `monthly_income`
- address/contact: `addr_unit`, `addr_building`, `addr_lot`, `addr_street`, `addr_subdivision`, `addr_barangay`, `addr_city`, `addr_province`, `addr_zip`, `mobile`, `home_phone`, `email`
- maternity: `lmp`, `age_of_menarche` DECIMAL(4,1), `gravida`, `para`, `expected_dd`, `delivery_date`, `delivery_time`, `am_pm_delivery`, `manner_of_delivery` ENUM(5), `fetal_outcome` ENUM(4), `baby_sex`, `birth_weight`, `apgar_score`, `brief_history`
- vitals / PE: `vital_bp`, `vital_cr`, `vital_rr`, `vital_temp`, `pe_heent`, `pe_abdomen`, `pe_chest_lungs`, `pe_gu`, `pe_cvs`, `pe_skin_extremities`, `pe_neuro_exam`, `course_in_wards`, `lab_findings`
- prenatal: `initial_prenatal_date`, `vital_signs_normal` BOOL, `pregnancy_low_risk` BOOL, `ob_term`, `ob_preterm`, `ob_abortion`, `ob_living`, 20 `risk_*` BOOLs (multiple_pregnancy, ovarian_cyst, myoma_uteri, placenta_previa, miscarriages, stillbirth, preeclampsia, eclampsia, premature_contraction, hypertension, heart_disease, diabetes, thyroid_disorder, obesity, asthma, epilepsy, renal_disease, bleeding_disorders, prev_cesarian, uterine_myomectomy)
- other: `mcp_orientation` ENUM('yes','no'), `obstetric_index`, `pregnancy_uterine_aog`, `presentation`, `postpartum_followup_date`, `attending_physician_name`, `date_signed`

**`claim_prenatal_visits`** — `id`, `claim_id` FK, `visit_number` TINYINT (UNIQUE with claim_id), `visit_date`, `aog`, `weight`, `cr`, `rr`, `bp`, `temp`.

**`claim_postpartum_care`** — `id`, `claim_id` FK, `care_item` ENUM('perineal','complications','breastfeeding','family_planning','fp_service','referred_vss','schedule_next'), `done` BOOL, `remarks`.

**`research_ground_truth`** — `id`, `source_image`, `field_name`, `correct_text`, `created_at`.

**`research_ocr_results`** — `id`, `ground_truth_id` FK, `engine` ENUM('paddleocr','tesseract'), `extracted_text`, `confidence`, `is_correct`, `error_type` ENUM('correct','misread_character','missed_field','wrong_segmentation','blank_output','other'), `created_at`.

### From migrations
**`users`** (004) — `id`, `email` VARCHAR(190) UNIQUE, `password_hash` VARCHAR(255), `full_name`, `role` ENUM('encoder','admin') default 'encoder', `is_active` TINYINT(1), `last_login_at`, `created_at`, `updated_at`.

**`clinic_settings`** (005 + 009; single row, `CHECK (id = 1)`) — `hci_name`, `hci_pan`, `hci_bldg`, `hci_street`, `hci_city`, `hci_province`, `hci_zip`, `provider_rep_name`, `provider_capacity`, `attending_name`, `attending_pan` *(009)*, `updated_by` FK→users, `updated_at`.

**`ocr_correction_patterns`** (006) — `id`, `category`, `pattern_type` ENUM('value','word','char'), `wrong_text`, `correct_text` (binary collation), `times_seen`, `source` ENUM('starter','learned'), `is_active`, timestamps. UNIQUE(category, pattern_type, wrong_text, correct_text).

**`ocr_known_entries`** (007 + 008) — `id`, `category`, `entry_type` ENUM('value','word'), `entry_key`, `entry_text`, `times_from_reviews`, `times_from_forms`, `source` ENUM('starter','learned'), `is_active`, timestamps.

Other migrations: 001 makes PMRF/CF3-era claim columns nullable; 008 seeds "Cabantian"; 010 adds mother/baby + `form_values`.

### Old tables
- `approved_claims` — **NOT FOUND** (no SQL, Python or JS reference)
- `rejected_claims` — **NOT FOUND**
- `ai_label` — **NOT FOUND**

Claim status is only `claims.status` ENUM('draft','ready','exported'), advanced forward-only by `claims_store._advance_status()` (`claims_store.py:281`): draft→ready when CF2 + CSF required fields are complete (`advance_status_if_forms_complete`, line 299), →exported after a server PDF export (`mark_exported`, line 317).

Not in the database (file-based): grid templates (`Ocr_module/grid_templates/*.json`), review crops, training crops, the OCR testing workbook.

---

## 5. OCR PIPELINE

Main flow: `Ocr_module/logbook_pipeline.py` → `build_review_rows()` (line 379), steps 1–7 in its docstring (lines 4–33). Called from `routes/review_routes.py::_read_logbook()` (line 88).

| Stage | File | Function(s) |
|---|---|---|
| Load pages (PDF rendered at 2×) | `logbook_pipeline.py` | `load_pages()` :97 |
| **Image quality check (IQ-01)** | `image_quality.py` | `assess_image_quality()` :68, `compute_blur_score()` :37, `compute_brightness_score()` :47, `compute_ink_level()` :56 |
| Ruling-line detection (table structure) | `template_engine.py` | `detect_ruling_lines()` :455, `_rule_peaks()` :444 |
| Template matching | `template_engine.py` | `match_templates()` :332, `score_template_match()` :217, `score_template_fit()` :302, `fit_lines_to_rules()` :479 |
| Printed header → first patient row | `logbook_layout.py` | `read_header()` :75, `first_entry_line()` :117; `logbook_pipeline._first_entry_line()` :233 |
| **Row detection / placement** | `template_engine.py` | `TemplateAutoDetector.auto_place_template()` :1089, `detect_content_rows()` :804, `propagate_rows()` :883, `detect_rows_with_template()` :918, `map_rows_between_pages()` :534 (left page rows → right page) |
| **Column segmentation → cells** | `template_engine.py` | `generate_cells()` :1003, `extract_crop_from_cell()` :1055; column→category: `logbook_pipeline._page_category_for_column()` :260 |
| Guided column setup (calibration) | `logbook_layout.py`, `logbook_setup.py` | `propose_columns()` :163, `propose_page()` :218; `read_scan()`, `save_setup()`, `checked_templates()` |
| **PaddleOCR call** | `ocr_engine.py` | `get_ocr_engine()` :163, `extract_tokens_from_array()` :205, batched `read_versions_many()` :223 / `read_many()` :266 |
| Per-cell OCR, blank & missed-ink check | `logbook_pipeline.py` | `ocr_cell()` :172, `_ink_mask()` :136, `_has_writing()` :153, `_missed_ink()` :160 |
| **Confidence scoring / routing** | `logbook_pipeline.py` | `route_confidence()` :84, `field_status()` :220, `fill_best_guesses()` :584 |
| AI second look (correction) | `paddle_assist.py` | `make_corrector()` :773 (see §6) |
| Drop header / near-empty rows | `logbook_pipeline.py` | `_drop_non_patient_rows()` :602, `_is_header_row()` :597 |
| Save one pending session per row | `logbook_pipeline.py` | `persist_review_rows()` :623 |
| Apply reviewer's answers | `logbook_pipeline.py` | `apply_review()` :667 |

### Numeric thresholds (all in `Ocr_module/config.py`, env-overridable)
| Setting | Value | Line |
|---|---|---|
| Laplacian-variance blur threshold | **100.0** (`< 100` = blurry) | 170 |
| Brightness low (mean gray) | **60.0** (`< 60` = too dark) | 174 |
| Brightness high | **200.0** | 175 |
| Ink level max (0.1th-percentile gray) | **150.0**; "overexposed" needs mean > 200 **and** ink > 150 | 181; `image_quality.py:90-93` |
| Confidence ACCEPT | **0.85** (≥ 0.85 → `accepted`) | 191 |
| Confidence REVIEW | **0.65** (0.65–<0.85 → `needs_check`; < 0.65 or no text → `manual_encoding_required`) | 192 |
| Missed-ink limit | **0.2** (> 20% of handwriting outside every OCR box → retry with 16-px white margin; never auto-accepted) | 198; margin `logbook_pipeline.py:133` |
| Template match threshold | **0.55** | 163 |
| Min filled fields per patient row | **2** | 217 |
| Blank cell | ink < 1% of crop or < 60 px | `logbook_pipeline.py:129-130` |
| Max upload | 20 MB | 156 |
| AI ensemble variants | 4 | 208 |
| AI max fields per upload | 300 | 209 |

**Field confidence = the lowest token confidence in the cell**, not the mean (`logbook_pipeline.py:178-183, 214`). The AI never makes a field `accepted` (`paddle_assist.apply_reading()` :710). `fill_best_guesses()` puts PaddleOCR's text into low-confidence fields as a `best_guess`, status `needs_check`, instead of leaving them empty; the original routing is kept as `routed_status` (`logbook_pipeline.py:536-541, 584-594`).

The image quality check is **advisory only**: it never blocks OCR (`image_quality.py:7-8`, `logbook_pipeline.py:8-10`).

### PaddleOCR settings (`ocr_engine.py:171-177`)
- `use_angle_cls=True`, `lang="en"`, `use_gpu=False`, `show_log=False`; `ocr(image, cls=True)`.
- Models bundled in `Ocr_module/ocr_models/` (≈16 MB): detection **en_PP-OCRv3_det_infer**, recognition **en_PP-OCRv4_rec_infer**, angle classifier **ch_ppocr_mobile_v2.0_cls_infer** (`ocr_engine.py:155-160`). If the folder is missing, PaddleOCR downloads its defaults.
- Model is loaded lazily, once, and shared; one reading job at a time (`review_jobs.OCR_LOCK`).
- Batched reading of 12 cells at a time (`_BATCH_CELLS = 12`, `logbook_pipeline.py:364`).
- PP-Structure (PaddleOCR's table module): **NOT FOUND** — tables/rows/columns are found by the project's own OpenCV code (adaptive threshold + morphological opening with long thin kernels: vertical h/8, horizontal w/4; `template_engine.py:455-476`).

### Preprocessing before OCR
No preprocessing on the first read (crop goes straight to PaddleOCR). Only unsure cells get enhanced versions in the AI second look: CLAHE contrast (clipLimit 2.0, tile 4×4), unsharp mask (σ 1.5, 1.6/−0.6), 2× bicubic enlarge, adaptive Gaussian threshold (31, 12) — `paddle_assist.py:119-138`.

### Is Tesseract used at runtime?
**No — only for testing/benchmarking.**
- `ocr_tesseract.py` (`pytesseract.image_to_data`, default config, no `--psm`/`--oem` set — line 55) is imported lazily only when `/ocr` receives `engine=tesseract` (`routes/ocr_routes.py:42-59`). That is used by the PaddleOCR-vs-Tesseract testing panel in the calibration workspace (`templates/index.html`, saved via `/api/testing/rows`) and by `benchmarks/compare_ocr_engines.py`.
- The Logbook Reader (`/api/review/*`) uses PaddleOCR only. `config.py:219-223`: "the production PaddleOCR pipeline (ocr_engine.py) never reads this."

---

## 6. CORRECTION MODULE

Main file: **`Ocr_module/paddle_assist.py`** ("Offline AI assist for PaddleOCR"). It runs only on cells routed `needs_check` / `manual_encoding_required` (`wants_second_look()` :703). Also relevant: `philhealth/case_bridge.py` (date/time regex + digit look-alikes), `philhealth/review_fields.py` (format checks), `philhealth/address_parser.py`, `philhealth/mother_baby.py`, `logbook_layout.py`.

| Technique | Where | Details |
|---|---|---|
| **Ensemble voting** | `ensemble_read()` :160, `VARIANTS` :137 | Original + 4 enhanced crops read by PaddleOCR; readings grouped case-insensitively, group score = sum of confidences |
| **Character substitution** (number/date columns) | `CorrectionModel._fix_chars()` :556; starter map `_STARTER_CHARS` :94; `case_bridge._OCR_DIGITS` :61 | O/o/D/Q→0, l/I/i/\|→1, Z/z→2, S/s→5, G/b→6, T→7, B→8, g/q→9. Only in CASE #, BDAY and DATE & TIME columns (`_DIGIT_KINDS` :87); A/P/M kept in date-times |
| **Word / whole-value patterns** | `CorrectionModel.correct()` :501, `_best()` :488 | Used when seen ≥ 2 times (`_MIN_SEEN`) and the outcome ≥ 60% of the time (`_MIN_SHARE = 0.6`) |
| **Learning from reviews** | `extract_patterns()` :241, `record_review()` :656, `record_form()` :687 | Each confirmed review adds `learned` patterns + known entries; re-submits learn only the difference |
| **Case-number format learning** | `code_format()` :368, `_apply_code_format()` :399 | Learns year prefix / separator once ≥ 60% of confirmed codes share it |
| **Regex — PIN** | `field_catalog.PIN_PATTERN` :272 → `^\d{2}-\d{9}-\d{1}$`; frontend IF-01/IF-02 (12 digits, digits only) | PIN is **not** OCR'd (no logbook column); format check only |
| **Regex — dates** | `case_bridge._DATE_TOKEN` :66 (mm-dd-yy(yy) with `-`, `/` or `.`, look-alike letters allowed), `_DATE_FORMATS` :55 (9 strptime formats), `_parse_date_flexible()` :86 | Impossible calendar dates → None (never guessed) |
| **Regex — times** | `case_bridge._TIME_RE` :69, `_TIME_TOKEN` :70, `_parse_time_flexible()` :105 | `h:mm`, `h.mm`, `h;mm`, optional AM/PM; no AM/PM → left for staff |
| **Regex — case no. / names** | `review_fields._CASE_NUMBER_RE` :66 `^\d+(-\d+)*$`; `_NAME_RE` :70 | |
| **Fuzzy matching** | `CorrectionModel._closest_entry()` :425 with **`difflib.SequenceMatcher`** | **Not RapidFuzz** — RapidFuzz is in requirements.txt but no file imports it |
| Run-together words | `_split_run_together()` :443 | e.g. "CASANTANDAUAO" → "Cabantian Davao" (each half ≥ 4 letters) |
| Davao/City fixes | `_is_davao()` :224, `_davao_city()` :230, `_CITY_SHORT` :83 | "CY"/"CTY" after Davao → City |

### Fuzzy similarity thresholds (all `difflib` ratio, 0–1)
| Use | Value | Where |
|---|---|---|
| Word → common entry | **0.80** (`_WORD_MATCH`) | `paddle_assist.py:73` |
| Whole address/diagnosis → common entry | **0.85** (`_VALUE_MATCH`) | `paddle_assist.py:74` |
| Word right before "Davao"/"DC" (barangay) | **0.70** (`_BEFORE_CITY_MATCH`) | `paddle_assist.py:81` |
| Entry must have been seen | ≥ 2 times (`_MIN_ENTRY_WEIGHT`) | `paddle_assist.py:75` |
| Learn word/char patterns only if whole strings similar | ≥ 0.5 | `paddle_assist.py:251` |
| Barangay names (address parser) | **0.82** | `address_parser.py:123` |
| Header keywords (logbook setup) | **0.80** | `logbook_layout.py:55` |
| Mother/baby diagnosis words | **0.75** | `mother_baby.py:31` |
| Mother/baby name similarity | 0.80 | `mother_baby.py:136` |

AI reading counts as "sure" only if ≥ 2 versions agree, average confidence ≥ 0.65, and a number/date has no stray letters (`assist_field()` :744-745). A NAME corrected from the common-entry list is never "sure" (:746-748) — it stays a hint.

### Cross-field inference
- **Patient sex** from name ("BABY GIRL/BOY …") or maternal diagnosis regex (G#P#, AOG, NSVD, delivery, labor, postpartum…) — `case_bridge.infer_patient_sex()` :195; shown as "From scan – please check".
- **Address parts** (lot, street, subdivision, barangay, city, province) from one address line; barangay → city → province lookup; ditto mark "-DO-" copies the row above — `address_parser.split_address()`, `case_bridge.draft_patient_and_encounter()` :322-332.
- **Mother vs baby** role from diagnosis words / "BABY GIRL" name / age; suggests the mother's claim for a baby — `philhealth/mother_baby.py`.
- **Date logic checks** across columns (discharge vs admission vs delivery, age at admission) — `review_fields.check()` :299 (see §8).
- Frontend: discharge date "day after delivery" tick, diagnosis wording from G/P/LMP/baby weight (`app.js:2549-2630`, `dx-templates.js`).

### Confusion ranking
**NOT FOUND as a separate ranking step.** The nearest equivalent: patterns are counted (`times_seen`) and `_best()` picks the most common correction (`Counter.most_common(1)`) if it meets `_MIN_SEEN`/`_MIN_SHARE`; `_closest_entry()` ranks candidates by `(similarity, weight)`.

### Where the lists are stored
| List | Storage |
|---|---|
| **Confusion table** (char + word mistakes) | DB table `ocr_correction_patterns`, seeded by `database/migrations/006_ocr_correction_patterns.sql` (char map above for 5 columns; word seeds N5D→NSD, NS0→NSD, A0G/AO6/A06→AOG, GIPO/G1PO/GIP0→G1P0, G2PI→G2P1, WK5→wks, C5→CS for the diagnosis columns). Fallback in code: `paddle_assist._STARTER_CHARS` :94 |
| **Diagnosis vocabulary** | DB table `ocr_known_entries` (seed words in migration 007: Pregnancy, Uterine, Term, Labor, Cephalic, Delivery, …) + everything learned from reviews and exported forms |
| **Diagnosis wording packages** (clinic templates) | Frontend code `PClaimAssist/js/dx-templates.js` `DX_PACKAGES`: NSDBF, NCP, FP001, IUD, ANV, PPC01 (ICD codes O80.0, Z38.0, Z30.1, Z34.0/Z34.8, Z39.2) |
| **Place names** | Code: `philhealth/address_parser.py` — `CITIES` (9 cities with provinces), `_CITY_PATTERNS`, `KNOWN_BARANGAYS["DAVAO CITY"]` (Davao City barangays). DB: address words in `ocr_known_entries` (migrations 007, 008) |

---

## 7. AUTO-POPULATION

### Where the mapping is defined
**`Ocr_module/philhealth/field_catalog.py`** — the comment at lines 18–30 calls it "THE field mapping - single source of truth for both the Python backend and the PClaimAssist forms."
- `FORM_FIELDS` (:36) — every PClaimAssist form key (the `data-autofill` attribute on each input) → `(table, column, kind)`.
- `OCR_CATEGORY_KEYS` (:151) — which form keys each logbook column fills (e.g. `NAME` → patientLastName/FirstName/MiddleName; `DATE & TIME OF ADMISSION` → dateAdmitted/timeAdmitted/amPmAdmitted).
- `DERIVED_OCR_KEYS` (:165) — keys inferred, not copied (address parts, patientSex).
- `OCR_CLAIM_REQUIRED_CATEGORIES` (:173) — NAME, BDAY, DATE & TIME OF ADMISSION must be typed at review.
- `test_form_prefill.py` fails if a key here is missing from `js/app.js`.

### Flow
1. Logbook review saved → `PUT /api/review/sessions/<id>` (`review_routes.py:191`).
2. "Send to Forms" → `POST /api/claims/generate` → `claims_store._create_or_update_claim_from_session()` (:154) → `case_bridge.draft_patient_and_encounter()` (:212) writes patients/encounters/claims rows. Pending (unreviewed) sessions are refused (`claims_store.py:155-156`).
3. `index.html?claim=<id>` → `claim-loader.js` → `GET /api/claims/<id>/form-data` → `form_prefill.build_form_data()` (`form_prefill.py:442`) returns values keyed by form key + a status per field: accepted / needs_check / typed / required / default / empty, shown as tags ("From scan", "From scan · please check", "Typed by staff", "Please type", "Clinic default", "Empty in logbook") — `claim-loader.js:24-31`.
4. `applyFormData()` (`app.js:2088`) writes `state.data` and every `[data-autofill]` input.

### How edits propagate across forms
- **One key, many inputs:** the same `data-autofill` key appears on Patient details, CSF, CF2, CF4 and PMRF. `bindInputListeners()` (`app.js:1321`) writes `state.data[key]`; `updateFormPreviews()` (`app.js:813`) → `syncAllAutofillElements()` (:854) refreshes every input with that key and every PDF preview overlay.
- **Different keys for the same fact:** `LINKED_FIELD_GROUPS` (`app.js:964`), e.g. `['dischargeDx','dxADiagnosis','cf4FinalDiagnosis']`, `['chiefComplaint','cf4ChiefComplaint']`, health-professional name/accreditation/date rows (CSF ↔ CF2 ↔ CF4), signer names/dates. `propagateMirroredField()` (:989) copies a new value into a linked key only if that key is empty or still equals the old value.
- **Derived values:** `applyMemberIsPatient()` (:640, member = patient), `applyMailingSameAsAbove()` (:694), `applyNoPhilhealth()` (:718), `applyDerivedFields()` (:771), `applySignerFields()` (:800).
- **Mother → baby:** `mother-baby.js` fills a baby's empty boxes from the linked mother's claim (`GET /api/claims/<id>/from-mother`).
- **Persistence:** `claim-loader.js` autosaves to `PUT /api/claims/<id>/form-values` 1200 ms after the last change (`CLAIM_SAVE_DELAY_MS`, line 193).

---

## 8. VALIDATION ENGINE

### Where
- **Rules are in code, not the database:** `PClaimAssist/js/validation-rules.js`, array `RULES` (lines 199–370). Engine: `runValidationRules()` (:378). Features: `computeFeatures()` (:103). Called from `app.js::updateValidation()` (:1529) on every change.
- Severity mapping (:15-20): `block_submission` / `halt_validation` = Critical (block); `display_warning` = Warning; `flag_high_risk` = High Risk. `canGeneratePDF = critical.length === 0` (:420).

### Every rule implemented (31)
| ID | Category | Condition (feature test) | Action | Message |
|---|---|---|---|---|
| IQ-01 | Image Quality | OCR active and `image_quality_pass === 0` | display_warning | The page may be too blurry, dark, or bright to read accurately. Re-scanning is recommended. |
| CR-01 | Correction Status | any unreviewed suggestion | display_warning | A field was auto-corrected from the logbook reading. Please compare the original and suggested values, then choose Accept, Edit, or Reject. |
| CR-02 | Correction Status | `pending_suggestions_count > 3` | flag_high_risk | Several values in this entry needed correction. Please check the whole row against the logbook page before continuing. |
| MF-01 | Missing Field | patientName blank | block_submission | Patient's full name is missing. This field is required. |
| MF-02 | Missing Field | memberPIN blank (unless "No PhilHealth") | block_submission | PhilHealth Identification Number (PIN) is missing. |
| MF-03 | Missing Field | memberDOB blank | display_warning | Member/Patient date of birth is missing. |
| MF-04 | Missing Field | dateAdmitted blank | block_submission | Date of admission is missing. Type it in Patient details, part 3 (Stay at the clinic). |
| MF-05 | Missing Field | dateDischarge blank | block_submission | Date of discharge (went home) is missing. Type it in Patient details, part 3 (Stay at the clinic). |
| MF-06 | Missing Field | `blank_fields_count > 3` | flag_high_risk | High rejection risk: more than 3 required fields are blank. |
| MF-07 | Missing Field | cf4ChiefComplaint blank | block_submission | CF4 chief complaint is missing. Please encode it from the patient's clinical record. |
| MF-08 | Missing Field | cf4CourseInWard blank | block_submission | CF4 course in the ward is missing. Please encode it from the patient's clinical record. |
| MF-09 | Missing Field | cf4DrugsAdministered blank | display_warning | CF4 drugs or medicines administered are not indicated. Please verify. |
| IF-01 | Invalid Format | PIN present and digit count ≠ 12 | block_submission | PhilHealth PIN must be exactly 12 digits. |
| IF-02 | Invalid Format | PIN has characters other than digits, spaces, `-` | block_submission | PhilHealth PIN must contain digits only. |
| IF-03 | Invalid Format | any filled date (memberDOB, patientDOB, dateAdmitted, dateDischarge, deliveryDate, lmp) not a real MM-DD-YYYY date | block_submission | Date is not in the required MM-DD-YYYY format. |
| IF-04 | Invalid Format | any member/patient name part contains a digit | display_warning | Name field contains numeric characters, please verify. |
| IC-01 | Inconsistent Entry | `name_match_across_forms === 0` | block_submission | Patient name is not consistent across the five forms. |
| IC-02 | Inconsistent Entry | `pin_match_across_forms === 0` | block_submission | PhilHealth PIN is not consistent across the CSF, CF4, and PMRF. |
| IC-03 | Inconsistent Entry | discharge < admission | block_submission | Discharge date is earlier than admission date. |
| IC-04 | Inconsistent Entry | memberDOB > admission | block_submission | Date of birth cannot be after the admission date. |
| IC-05 | Inconsistent Entry | delivery outside admission–discharge | display_warning | Delivery date is outside the admission–discharge range. |
| IC-06 | Inconsistent Entry | member ≠ patient and relationship blank | display_warning | Patient differs from member but relationship to member is not indicated. |
| IC-07 | Inconsistent Entry | `dates_match_across_forms === 0` | block_submission | Admission and discharge dates are not the same across CSF, CF2, and CF4. |
| IC-09 | Inconsistent Entry | CF2 final dx ≠ CF4 final dx (both filled, case-insensitive) | block_submission | The final diagnosis on CF2 does not match the diagnosis on CF4. |
| IC-08 | Inconsistent Entry | discharge date ≤ delivery date | block_submission | Discharge date must be at least one day after the delivery date. |
| SP-01 | Signature | signature check active and member signature absent | block_submission | Member/representative signature is missing on the CSF. |
| SP-02 | Signature | … attending midwife signature absent | block_submission | Attending midwife's signature is missing on CF4. |
| SP-03 | Signature | … HCI representative signature absent | block_submission | Authorized HCI representative signature is missing on the CSF. |
| SP-04 | Signature | … employer signature absent and member is employed | display_warning | Employer's certification signature is missing (required for employed members). |
| SP-05 | Signature | … thumbmark present and HCI assisting signature absent | display_warning | Thumbmark detected, but HCI assisting representative signature is missing. |
| SP-06 | Signature | … CF4 attending provider signature absent | block_submission | Attending provider's signature is missing on CF4. |

### Count per category
| Category | Count | IDs |
|---|---|---|
| Missing Field (MF) | 9 | MF-01 … MF-09 |
| Invalid Format (IF) | 4 | IF-01 … IF-04 |
| Inconsistent Entry (IC) | 9 | IC-01 … IC-09 |
| Signature Presence (SP) | 6 | SP-01 … SP-06 |
| Image Quality (IQ) | 1 | IQ-01 |
| Correction Status (CR) | 2 | CR-01, CR-02 |
| **Total** | **31** | 20 block_submission, 9 display_warning, 2 flag_high_risk |

The code labels 6 category strings, but the comment groups IQ + CR as "Category 5 … Image Quality & Correction Status" (:200), i.e. **5 categories / 31 rules**.

### Rules that cannot fire in the current code
- **IC-01, IC-02, IC-07** — their features are hard-coded to 1 (`validation-rules.js:139-141`), because every form reads the same `state.data` key (comment :136-138).
- **SP-01 … SP-06** — fire only when `window.PCA_SIGNATURE_STATE.active` is set; nothing in the repo sets it (signature re-upload checking: NOT FOUND). Before printing they instead produce the **signing checklist** (see §9).
- **IQ-01, CR-01, CR-02** — read `window.PCA_OCR_STATE`, which only `ocr-review.js` sets, inside `PCAReview.load()`; **nothing in the repo calls `PCAReview.load()`**. In practice image quality and unreviewed readings are handled earlier, in the Logbook Reader (§5, and server checks below).

### How it ensures only confirmed values are used
1. **Server, logbook stage:** a claim can only be created from a session whose `review_status` is `reviewed` (`claims_store.py:155-156`, raises `ReviewIncompleteError`). Every `manual_encoding_required` field must be typed (or deferred to the forms, except NAME/BDAY/ADMISSION) before saving (`logbook_pipeline.apply_review()` :667). Reviewer-split parts are used as typed, never re-parsed (`case_bridge.py:239-249`).
2. **Server safeguards on review submit** (`review_fields.check()` :299, called in `review_routes.py:199-204`): problems (must fix) — case no. digits/dashes only and ≤ 20 chars; last + first name required, letters only, length limits; real date, not in the future, birthday not before 1900; hour 1–12, minute 00–59, AM/PM chosen; text ≤ 255; required columns can't be marked empty; discharge before admission; discharge not at least a day after delivery. Warnings (need "confirm") — stay > 30 days; delivery before admission; age at admission outside 10–55; event dates before 2000.
3. **AI never auto-accepts:** best case a field becomes `needs_check` (`paddle_assist.apply_reading()` :710).
4. **Frontend design:** `ocr-review.js` keeps an unreviewed suggestion out of `state.data`; until Accept/Edit/Reject the confirmed value is the original reading (`confirmedValue()` :46-50). As noted above, this module is not fed by the current pipeline.
5. **Server export check:** `/api/claims/<id>/export/<form>` refuses an incomplete CF2/CSF (`mapping_service._form_status()`; `_validate()` checks dates, ENUM choices, PIN `##-#########-#`).

### PDF gate is currently switched off
`PClaimAssist/js/pdf/pdf-overlay.js:44`: `const SKIP_VALIDATION_FOR_EXPORT = true;` with the comment "TEMPORARY - FOR LAYOUT CHECKING ONLY. SET BACK TO false BEFORE THE CAPSTONE DEFENSE." While it is `true`, critical errors do **not** block "Save as PDF" (`pdf-overlay.js:693-694, 777-778`).

---

## 9. PDF GENERATION

There are **two** PDF writers.

### (a) Client-side, pdf-lib 1.17.1 — what clinic staff actually print (all 4 forms)
- `PClaimAssist/js/pdf/pdf-overlay.js`: `buildFilledPdf()` :596 loads the template with `PDFLib.PDFDocument.load`, clears any AcroForm text fields (`flattenBlankForm()` :537), embeds Helvetica, and `drawText()`s each overlay field at `y = height − top% × height − 6pt` (`BASELINE_OFFSET_PT = 6`, :56). Long text shrinks to ≥ 4.5 pt or wraps for `wrap` fields. `exportFilledPDF()` :687 downloads one form; `exportAllForms()` :770 merges the ticked forms into one PDF.
- Coordinates: `js/pdf/overlays/{csf,cf2,cf4,pmrf}.js` (percent of page: `top`, `left`, `w`, `fs`), combined in `overlays/index.js`.
- Same Helvetica metrics in preview and export so "the printed form matches the screen" (:46-57).

### (b) Server-side, PyMuPDF — CF2 and CSF only
- `Ocr_module/philhealth/pdf_export.py`: `export_claim_pdf(form_key, …)` :54 opens `PClaimAssist/forms/CF2.pdf` or `CSF.pdf` with `fitz.open`, resolves each overlay field's value (`resolve_computed_value`), and `_draw_field()` :32 writes it with `page.insert_text((x, y), …, fontname="helv")`, at `y = top% × height + 6` (PyMuPDF's y runs downward). Text wider than its box goes into `page.insert_textbox()` (≤ 6 lines). Returns `doc.tobytes()`.
- Coordinates: `philhealth/overlays/cf2.py` (CF2, 612×936 pt) and `csf.py`, "ported field-for-field" from the JS overlays.
- Reached only via `GET /api/claims/<id>/export/<cf2|csf>` (`claims_routes.py:166`), called from the calibration workspace (`templates/index.html`), not from the PClaimAssist forms.
- PyMuPDF is also used to render PDF uploads to images at 2× (`fitz.Matrix(2, 2)`) for OCR (`ocr_engine.py:294`, `logbook_pipeline.py:104`).

### Template files (`PClaimAssist/forms/`)
`CSF.pdf`, `CF2.pdf`, `CF4.pdf` (served as `CF4.pdf?v=2020-02`, the February 2020 edition — `pdf-overlay.js:64`), `CF4-Blank.pdf`, `PMRF.pdf`.
**CF3: NOT FOUND** — removed in commit `3b48e87` (2026-10-21, "Remove CF3"); only migration 001's name and old schema comments mention it.

### Signing checklist
Produced by `runValidationRules()` (`validation-rules.js:406-412`) from every `Signature` rule's `checklist` text, regardless of whether a signed form exists. SP-04 is listed only for employed members, SP-05 only when a thumbmark is used. Rendered by `renderSigningChecklist()` (`app.js:2060`) into `#signingChecklist` (`index.html:3444`). Items:
- Member / representative — CSF Part I (SP-01)
- Attending midwife / physician — CF4 (SP-02)
- Authorized HCI representative — CSF Part V (SP-03)
- Employer representative — CSF Part II (employed members only) (SP-04)
- HCI assisting representative — required when a thumbmark is used (SP-05)
- Attending provider — CF4 (SP-06)

The system never applies or verifies signatures (`validation-rules.js:172-173`).

### Overlay calibration tool
`PClaimAssist/js/pdf/pdf-calibrate.js`: drag/resize overlay fields on the live preview to adjust `top/left/w %`, then export the coordinates to paste into `overlays/{form}.js`.

---

## 10. AUTH & OTHER FEATURES

### Login & accounts
- Email + password, `POST /api/auth/login`. Flask signed session cookie holding only `user_id` (`auth.py:183-188`); `SESSION_COOKIE_HTTPONLY=True`, `SAMESITE="Lax"`, `SECURE=False`, lifetime **12 h** (`app.py:38-46`, `config.py:137`). The role is re-read from the DB on every request (`auth.current_user()`), so a deactivated account loses access at once.
- `SECRET_KEY` from env or generated once into `Ocr_module/.secret_key` (`config.py:112-134`).
- **Password hashing: bcrypt** (`bcrypt.hashpw(…, bcrypt.gensalt())`, `user_store.py:47`; cost factor = library default, not set in code). Minimum 8 characters, maximum 72 bytes (`user_store.py:30-46`). A dummy hash equalises timing for unknown emails (:155-157). One generic "Incorrect email or password." message (`auth_routes.py:79-82`).
- **Roles:** `encoder`, `admin` (`user_store.py:21`). The first account registered is an active admin; later self-registrations are inactive until an admin approves them (`user_store.py:99-100`). `create_admin.py` creates the first admin from the command line.
- Admin can list/create accounts, approve/switch off, reset passwords; anyone can change their own password. Forgot-password by email: NOT FOUND.
- Frontend guard: `auth-client.js` checks `/api/auth/me` and redirects to `login.html`. "Remember email" uses `localStorage` (`login.js:28,199`).

### Drafts
- A named "save draft" feature: **NOT FOUND**.
- Equivalents: `claims.status` defaults to `'draft'`; form values autosave to `claims.form_values` (1.2 s debounce) and are restored when the claim reopens (`saved_values` in `/form-data`); "Save patient" (`POST /api/claims/save`) creates a claim for a hand-typed patient. Logbook review can "Send to Forms" with remaining manual fields deferred (`defer_manual`).

### Template calibration
1. **Guided logbook setup** (`/logbook-setup`, `logbook_setup.py`, `logbook_layout.py`): reads the printed header with PaddleOCR, proposes the columns (left page: CASE #, DATE & TIME OF ADMISSION, NAME, BDAY, ADDRESS; right page: ADMITTING DIAGNOSIS, DATE & TIME OF DELIVERY, FINAL DIAGNOSIS, DATE & TIME OF DISCHARGE), staff check them, admin saves as the setup for later scans (old ones archived to `grid_templates/archive/`). Every scan in the Logbook Reader goes through this "check the columns" step.
2. **OCR calibration workspace** (`/ocr-workspace`): manual grid templates, row propagation, auto-place, template matching, crops.
3. **PDF overlay calibration** (`pdf-calibrate.js`, §9).

### Excel export
- `GET /export_case_session?case_id=` — one case session → `.xlsx` via `pandas.DataFrame.to_excel(engine="openpyxl")` (`ocr_routes.py:220-264`).
- `GET /api/testing/download` — running PaddleOCR-vs-Tesseract workbook (openpyxl; `ocr_testing_store.py`).
- Excel export of claims/patients: NOT FOUND.

### Dashboard (Home, `index.html` `#section-dashboard`)
Form status cards for CSF, CF2, CF4, PMRF ("Not started" …); stat cards "Boxes filled in" (`updateDashboardStats()`, `app.js:2074`), "Forms Ready" (`0 / 5`), "Missing information check"; an in-page activity feed that keeps the last 8 actions (`logActivity()`, `app.js:2156`, not stored).

### Settings
- **Clinic settings** (admin edits, everyone reads): name, PAN, building, street, city, province, ZIP, provider representative name/capacity, attending name/PAN (`clinic_settings` table; `settings_routes.py`). They prefill the HCI parts of CF2/CSF/CF4.
- **Profile** section: name, email, role, last sign-in; staff accounts list for admins (`app.js:2287-2343`).

### Notifications
**NOT FOUND** (no email/push/notification table). Only in-page toast messages (`showToast()`, `app.js:2176`) and the activity feed.

### Other things a user can do
- **Logbook Reader** (`/review`): upload a scan (JPG/PNG/PDF, ≤ 20 MB), watch progress, review each patient row with the cell crop + whole-row picture, typed boxes (name parts, date picker, hour/minute/AM-PM), "Nothing is written here", then "Send to Forms".
- **Mother and baby** linking and copying (`mother-baby.js`, `/api/claims/<id>/family`, `/from-mother`).
- **Diagnosis wording** per PhilHealth package with filled-in blanks and ICD codes (`dx-templates.js`).
- Mark a form part "Not needed" (`addNotNeededTick()`, `app.js:1200`); "No PhilHealth" for member/patient PIN; member-is-patient; mailing-same-as-permanent.
- Sample data loader (`loadSampleData()`, `app.js:2135`).
- The correction model learns from exported forms (`entry-learning.js` → `/api/learning/form-entries`).
- PaddleOCR-vs-Tesseract testing panel and `benchmarks/compare_ocr_engines.py` (CER/WER, `benchmarks/metrics.py`).
- `/db_health` check; temporary `/diagnostic/patient_crud_test`.

---

## 11. DEPLOYMENT

- **Server:** Flask's built-in development server, `app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)` (`app.py:112-113`). Waitress / gunicorn: **NOT FOUND** (not in requirements, not referenced). `flask run` is not used by the scripts.
- **Host / port:** `127.0.0.1:5000` by default (`config.py:70-71`, `.env.example`). `DEBUG` defaults to `True` (`config.py:72`); `PClaimAssist.bat` sets `OCR_DEBUG=false`.
- **LAN:** **not reachable by default** — it binds to loopback `127.0.0.1`. It would need `OCR_HOST=0.0.0.0` (env/.env); no script or doc in the repo sets that. CORS allows only `http://127.0.0.1:5500` and `http://localhost:5500` (Live Server), but since the frontend is served by Flask itself on :5000, everything is same-origin.
- **How it is started:**
  - `PClaimAssist.bat` (repo root): starts XAMPP MariaDB (`C:\xampp\mysql\bin\mysqld.exe --standalone`) if not running, starts `Ocr_module\venv\Scripts\python.exe app.py` minimised, polls `/db_health` (up to 40 tries), opens `http://127.0.0.1:5000/`. `/background` = same without the browser.
  - `tools/autostart.ps1` puts that `/background` shortcut in the Windows Startup folder.
  - `Ocr_module/run_ocr.bat` — just `venv\Scripts\python.exe app.py`. `setup_ocr.bat` creates the venv and `pip install -r requirements.txt`.
- **One process** serves both the API and the PClaimAssist frontend (`app.py:59-70`).

### Uploaded images: memory vs disk, deleted after?
| Path | What happens | Deleted? |
|---|---|---|
| Logbook setup scan (`/api/logbook-setup/read`) | Saved to a temp file (`utils/uploads.temp_upload_path`), copied to `uploads/logbook_setup/<setup_id>/scan.*` with preview JPEGs (width 1400, quality 85) | Temp file deleted at once; setup folder deleted after the checked scan is read (`logbook_setup.remove_scan()` in `review_routes.py:159-160`), and folders older than 24 h are cleared (`clear_old_previews()`) |
| Logbook reading job (`/api/review/jobs`) | Saved to a `tempfile.mkstemp` file | Deleted when the job finishes (`review_jobs.py:88-90`) |
| Synchronous `/api/review/upload` | Temp file | Deleted after use (`temp_upload_path`) |
| Pages/cells during OCR | Decoded into NumPy arrays **in memory**; PDF pages rendered in memory | — |
| Cell crops + whole-row pictures | Written to `uploads/review_crops/<upload_id>/*.png` for the review screen | **Not deleted** (no cleanup code found) |
| Calibration `/ocr` uploads | Saved to `uploads/<filename>` | **Not deleted** |
| Training crops `/save_crop` | `uploads/training/<category>/` | Kept on purpose |
| Background jobs | In memory only; forgotten 1 h after finishing (`JOB_TTL_SECONDS = 3600`) | — |

---

## 12. CODE EXCERPTS (verbatim)

### (a) Image quality check — `Ocr_module/image_quality.py`
Lines 37–44:
```python
def compute_blur_score(image):
    """Variance of the Laplacian of `image` (BGR or single-channel).
    Higher = sharper; lower = blurrier. Returns 0.0 for an empty/invalid
    image."""
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())
```
Lines 81–101:
```python
    blur_score = compute_blur_score(image)
    brightness_score = compute_brightness_score(image)

    is_blurry = blur_score < config.IMAGE_QUALITY_BLUR_THRESHOLD
    is_too_dark = brightness_score < config.IMAGE_QUALITY_BRIGHTNESS_LOW
    # Overexposed = bright overall AND the ink itself washed out - a clean
    # scan of white paper is bright on average but still has dark ink (see
    # config.IMAGE_QUALITY_INK_MAX).
    ink_level = compute_ink_level(image)
    is_too_bright = (
        brightness_score > config.IMAGE_QUALITY_BRIGHTNESS_HIGH
        and ink_level > config.IMAGE_QUALITY_INK_MAX
    )

    warnings = []
    if is_blurry:
        warnings.append(
            f"Image appears blurry (sharpness {blur_score:.1f}, below the "
            f"{config.IMAGE_QUALITY_BLUR_THRESHOLD:.0f} threshold) - OCR accuracy may be "
            "reduced. Consider rescanning."
        )
```

### (b) Per-cell OCR + confidence routing — `Ocr_module/logbook_pipeline.py`
Lines 84–90:
```python
def route_confidence(confidence):
    """Thesis confidence routing - thresholds live in config.py."""
    if confidence is None or confidence < config.OCR_CONFIDENCE_REVIEW:
        return MANUAL
    if confidence < config.OCR_CONFIDENCE_ACCEPT:
        return NEEDS_CHECK
    return ACCEPTED
```
Lines 196–217 (inside `ocr_cell()`):
```python
    try:
        tokens = read(image, first_read)
        missed = _missed_ink(mask, tokens)
        if missed is not None and missed > config.OCR_MISSED_INK_LIMIT:
            padded = cv2.copyMakeBorder(image, *([_RETRY_MARGIN] * 4), cv2.BORDER_CONSTANT, value=(255, 255, 255))
            retry = read(padded)
            retry_missed = _missed_ink(mask, retry, shift=_RETRY_MARGIN)
            if retry_missed is not None and retry_missed + 0.05 < missed:
                tokens, missed = retry, retry_missed
    except Exception:
        logger.exception("OCR failed on a logbook cell")
        return "", None, [], "OCR failed on this cell", flags

    flags["incomplete"] = missed is not None and missed > config.OCR_MISSED_INK_LIMIT
    if not tokens:
        flags["blank"] = not _has_writing(mask)
        return "", None, [], None, flags
    raw_text = " ".join(str(t["text"]).strip() for t in tokens)
    confidence = round(float(min(t.get("confidence", 0) for t in tokens)), 4)
    return raw_text, confidence, [
        {"text": str(t["text"]), "confidence": round(float(t.get("confidence", 0)), 4)} for t in tokens
    ], None, flags
```

### (c) Character substitution + fuzzy match — `Ocr_module/paddle_assist.py`
Lines 425–441 (fuzzy match):
```python
    def _closest_entry(self, category, entry_type, text, cutoff):
        """The common entry closest to `text` -> (entry text, weight), or None
        when `text` is itself a common entry or nothing is close enough."""
        known = self.entries.get((category, entry_type))
        if not known:
            return None
        key = text.upper()
        if key in known:
            return None
        best = None
        for candidate, (shown, weight) in known.items():
            if abs(len(candidate) - len(key)) > max(2, len(key) // 4):
                continue
            score = SequenceMatcher(None, key, candidate).ratio()
            if score >= cutoff and (best is None or (score, weight) > best[0]):
                best = ((score, weight), shown)
        return (best[1], best[0][1]) if best else None
```
Lines 556–569 (character substitution):
```python
    def _fix_chars(self, category, text, notes):
        """Letter/digit mix-ups in number and date columns ("O" -> "0")."""
        kind = review_fields.kind_of(category)
        if kind not in _DIGIT_KINDS:
            return text
        chars = []
        for char in text:
            fixed = None
            if char.isalpha() and not (kind == review_fields.DATETIME_KIND and char in _DATETIME_LETTERS):
                fixed = self._best(CHAR, category, char, char)
            if fixed:
                notes.append(f"'{char}' -> '{fixed}'")
            chars.append(fixed or char)
        return "".join(chars)
```

### (d) Field mapping — `Ocr_module/philhealth/field_catalog.py`
Lines 151–173:
```python
OCR_CATEGORY_KEYS = {
    "NAME": ("patientLastName", "patientFirstName", "patientMiddleName"),
    "BDAY": ("patientDOB",),
    "ADDRESS": ("patientAddress",),
    "DATE & TIME OF ADMISSION": ("dateAdmitted", "timeAdmitted", "amPmAdmitted"),
    "DATE & TIME OF DISCHARGE": ("dateDischarge", "timeDischarge", "amPmDischarge"),
    "DATE & TIME OF DELIVERY": ("deliveryDate", "deliveryTime", "amPmDelivery"),
    "ADMITTING DIAGNOSIS": ("admissionDx",),
    "FINAL DIAGNOSIS": ("dischargeDx",),
}
# Form keys worked out from a logbook column rather than copied from it
# (case_bridge.draft_patient_and_encounter): the address split into the
# forms' parts, and the patient's sex when the name or diagnosis makes it
# plain. Always shown as "From scan - please check", never as certain.
DERIVED_OCR_KEYS = {
    "ADDRESS": ("addrLot", "addrStreet", "addrSubdivision", "addrBarangay", "addrCity", "addrProvince"),
    "NAME": ("patientSex",),
}

# Logbook columns a claim can't be created without (the NOT NULL patient/
# encounter columns) - staff must type these in the OCR review itself;
# any other "manual encoding required" field may be left for the forms.
OCR_CLAIM_REQUIRED_CATEGORIES = ("NAME", "BDAY", "DATE & TIME OF ADMISSION")
```
Cross-form propagation — `PClaimAssist/js/app.js` lines 989–997:
```javascript
function propagateMirroredField(key, prevValue) {
  const targets = MIRRORED_FIELDS[key];
  if (!targets) return;
  const next = state.data[key];
  targets.forEach(t => {
    const cur = state.data[t];
    if (!cur || cur === prevValue) state.data[t] = next;
  });
}
```

### (e) Rule evaluation loop — `PClaimAssist/js/validation-rules.js`
Lines 378–404:
```javascript
function runValidationRules(getValue, data) {
  const features = computeFeatures(getValue, data);
  const violations = [];

  RULES.forEach(rule => {
    let fired = false;
    try {
      fired = !!rule.test(features);
    } catch (err) {
      console.warn('Validation rule ' + rule.id + ' failed to evaluate', err);
    }
    if (fired) {
      violations.push({
        id: rule.id,
        category: rule.category,
        action: rule.action,
        message: rule.message,
        field: rule.field || null,
        form: rule.form || null,
        source: rule.source || '',
        severity: SEVERITY[rule.action],
      });
    }
  });

  const critical = violations.filter(v => v.severity.critical);
  const warnings = violations.filter(v => !v.severity.critical);
```

### (f) PyMuPDF writing to a template — `Ocr_module/philhealth/pdf_export.py`
Lines 32–51:
```python
def _draw_field(page, field, value, page_width, page_height):
    if not value:
        return
    text = str(value)
    fontsize = field.get("fs", 8)
    x = (field["left"] / 100) * page_width
    y = (field["top"] / 100) * page_height + BASELINE_OFFSET
    box_width = (field["w"] / 100) * page_width

    text_width = fitz.get_text_length(text, fontname=_FONT, fontsize=fontsize)
    if text_width <= box_width:
        page.insert_text((x, y), text, fontsize=fontsize, fontname=_FONT, color=_COLOR)
        return

    # Longer than its box (e.g. a full diagnosis sentence) - wrap within the
    # field instead of silently overflowing past its right edge or cutting
    # it off. Bounded to a handful of lines so it can't bleed into
    # unrelated parts of the form.
    rect = fitz.Rect(x, y - fontsize, x + box_width, y - fontsize + fontsize * 6)
    page.insert_textbox(rect, text, fontsize=fontsize, fontname=_FONT, color=_COLOR)
```
Lines 70–77:
```python
    doc = fitz.open(template_path)
    try:
        for field in OVERLAYS[form_key]:
            value = resolve_computed_value(field.get("computed") or field["key"], data)
            page = doc[field["page"] - 1]
            rect = page.rect
            _draw_field(page, field, value, rect.width, rect.height)
        return doc.tobytes()
```

---

## 13. GIT HISTORY

### Commands run
- `git log --format='%ad' --date=short | sort | uniq | head -1` → **2026-08-27**
- `git log --format='%ad' --date=short | sort | uniq | tail -1` → **2026-10-26**
- Commits on the current branch: **51** (58 across all branches). Active days: 17.

### `git log --oneline --reverse | head -100`
```
42e9aaf Create integrated PClaimAssist and OCR project
47644dc Rename OCR project to Ocr_module and integrate OCR tab
671e047 Baseline before database integration and OCR Changes
03e6750 Verify Flask database CRUD connection
6cce5cc Migrate OCR case sessions to MariaDB
94807a2 Please Check SETUP for database instructions
5559647 Merge pull request #1 from JREIGHDEE/database-integration
8f94dec OCR testing module
650a386 Merge pull request #2 from JREIGHDEE/database-integration
175033f OCR testing more updates
88b98d3 Merge pull request #3 from JREIGHDEE/database-integration
1c5e5e3 OCR data integration
fa84366 Add login system and updated PDF overlays from yutaka/PClaimAssist
735c5f2 Merge pull request #4 from JREIGHDEE/database-integration
f1bc9f4 grid templates
75e9aea Merge pull request #5 from JREIGHDEE/database-integration
5350f09 Add advisory image quality check for OCR uploads
5ebe784 Carry OCR address and delivery date/time into claims
a9b5ad8 Advance claim status draft -> ready -> exported automatically
5ab9396 Remove stray text file and fix outdated app.js header
2e70621 Add CHAPTER_DETAILS.md: codebase facts for thesis chapters
3079de7 OCR improvements
6231600 Merge branch 'main' into database-integration
6dfa563 Merge pull request #6 from JREIGHDEE/database-integration
3222889 CF4 Added
db46055 Imporved Login
706b77d Imporved layout, Removed Document Upload and Settings, Moved OCR Placement
7a6f79e OCR and UI Improvements
6bd5300 Account sign-up with admin approval, sign-in fixes
4949909 Guided logbook setup, faster logbook reading, shared OCR models
bc3a7f1 Send to Forms fills more, dates read reliably, new logbook setup
4437b36 Clearer Patient details, less text, linked forms, always-on backend
5ef3f0c Windows scripts always get Windows line endings on every PC
96e0523 Merge pull request #7 from JREIGHDEE/reigh/logbook-setup-and-speed
3b48e87 Remove CF3
a660bcf Capitals on entry, and stop asking for the same detail twice
c32be30 Keep a dropdown's choice when it is picked
0e5f918 Make "Fix this" land somewhere you can type, and mark what is missing
9b5770e Show which boxes on a form are the clinic's to type
cc043bf Let a clinic mark a part of a form as not needed
10a2179 Offer the next page where the boxes run out
000be6e One page turner per form, at the foot of the boxes
47458fe Save the whole claim at once, once nothing is missing
9d41150 Use the clinic's own logbook setup
58a4a3a Apply staff user-testing changes and fix export alignment
dd84cf6 Apply the second round of staff feedback and print CF4/PMRF in their boxes
318b10b Bring back CF2, switch CF4 to the 2020 form and tidy the form design
ade2705 Print each form exactly as the live preview shows it
f3b053c Merge main: print each form exactly as the live preview shows it
b7e20f9 Tick boxes in the form's order, clinic owner for Part V, coloured clinic details
52c55cb Mother and baby, Save patient, and the clinic's diagnosis wording
```

### Development timeline
| Period | What happened |
|---|---|
| 2026-08-27 → 09-02 | Integrated repo created from the separate PClaimAssist frontend and OCR project (`my_ocr_project` → `Ocr_module`); baseline. |
| 09-08 → 09-17 | Database phase: Flask↔MariaDB CRUD check, OCR case sessions moved to MariaDB, SETUP guide, PaddleOCR-vs-Tesseract testing module, OCR data integration, grid templates. Login system + updated PDF overlays (09-15). PRs #1–#5. |
| 10-05 → 10-06 | Advisory image-quality check (IQ-01), address/delivery carried into claims, automatic claim status, CHAPTER_DETAILS.md, OCR improvements. PR #6. |
| 10-11 → 10-15 | CF4 added, login improved, layout rework (document upload and settings removed, OCR moved), OCR/UI improvements. |
| 10-21 (17 commits, busiest day) | Sign-up with admin approval; guided logbook setup; faster batched reading; bundled OCR models; Send to Forms; linked forms; always-on backend (PR #7). CF3 removed; capitals on entry; "not needed" parts; save whole claim; staff user-testing changes. |
| 10-23 → 10-26 | Second round of staff feedback; CF4/PMRF printed in their boxes; CF2 restored and CF4 switched to the 2020 edition; print = live preview; Part V clinic owner; mother & baby, Save patient, diagnosis wording. |

### Who worked on what (git author names as recorded)
| Author | Commits (non-merge) | Main areas touched |
|---|---|---|
| reigh | 26 (+1 merge) | Backend almost entirely: `Ocr_module/routes`, `philhealth/`, OCR pipeline, config, benchmarks, `database/`; plus much of `PClaimAssist/js` (validation, claim loading, mother-baby, dx templates). Line count (+39,982 / −3,785) includes the initial import of both projects. |
| adawngo | 18 | Frontend UX: `PClaimAssist/js`, `index.html`, `ocr.html`, `login.html`, `logbook-setup.html`, CSS; removed CF3; "not needed" parts; save whole claim; using the clinic's logbook setup (+1,643 / −2,329). |
| Yutaka (also as yutakerz) | 5 (+2 merges as yutakerz: PR #6 and main → database-integration) | Login system, PDF overlays, CF4, export alignment, print-as-preview; `PClaimAssist/js`, some `philhealth/`, `clinic_settings_store.py`, `user_store.py` (+8,473 / −2,539). |
| JREIGHDEE | 6 (all merges) | GitHub pull-request merges #1–#5 and #7. |

---

## 14. DIFFERENCES from the stated design

| Design value | In the code | Verdict |
|---|---|---|
| Confidence **85 / 65** | `OCR_CONFIDENCE_ACCEPT = 0.85`, `OCR_CONFIDENCE_REVIEW = 0.65` (`config.py:191-192`); the same in `ocr-review.js:33` | **Matches.** Details to mention: a field's confidence is the **lowest** token confidence; a reading that missed > 20% of the ink is never auto-accepted; low-confidence fields that have some text are pre-filled as a **best guess** marked `needs_check` instead of being left empty (the original routing is kept as `routed_status`); the AI second look never makes a field `accepted`. |
| Laplacian **100** | `IMAGE_QUALITY_BLUR_THRESHOLD = 100.0` (`config.py:170`) | **Matches.** Advisory only — never blocks OCR. |
| Brightness **60–200** | `BRIGHTNESS_LOW = 60.0`, `BRIGHTNESS_HIGH = 200.0` (`config.py:174-175`) | **DIFFERS slightly:** "too bright" also needs the ink to be washed out (0.1th-percentile gray > **150**, `config.py:181`), because clean logbook scans measure ~225–236 mean brightness. |
| Fuzzy threshold **80%** | `_WORD_MATCH = 0.8` (words), but `_VALUE_MATCH = 0.85` (whole address/diagnosis), `_BEFORE_CITY_MATCH = 0.7` (barangay before "Davao"), 0.82 (address-parser barangays), 0.75 (mother/baby words) | **DIFFERS:** several thresholds, not one; implemented with Python's **`difflib.SequenceMatcher`**, **not RapidFuzz** (RapidFuzz 3.14.5 is installed but never imported). |
| **30 rules in 5 categories** (MF, IF, IC, SP, IQ/CR) | **31 rules**: MF 9, IF 4, IC 9, SP 6, IQ 1 + CR 2 (= 3) | **DIFFERS by one rule** (IC-08 "discharge at least one day after delivery" and IC-09 "CF2 vs CF4 diagnosis" are both present; IC-08 is listed after IC-09 in the array). Rules are stored in JS code, not the DB. |
| Rules block PDF generation on critical errors | `canGeneratePDF` is computed, but `SKIP_VALIDATION_FOR_EXPORT = true` (`pdf-overlay.js:44`) | **DIFFERS (temporary):** the gate is switched off "FOR LAYOUT CHECKING ONLY"; the comment says to set it back to `false` before the defense. |
| IC-01/IC-02/IC-07 (cross-form name, PIN, date consistency) | Features hard-coded to 1 | **Never fire**: all forms share one `state.data` key, so they cannot disagree. |
| SP-01…SP-06 (signature presence) | Need `PCA_SIGNATURE_STATE`, which nothing sets | **Never fire as errors**; used only to build the signing checklist. Signed-form re-upload/verification: NOT FOUND. |
| IQ-01, CR-01, CR-02 in the rule engine | Need `PCAReview.load()`, which nothing calls | **Never fire in the forms**; image quality and unconfirmed readings are handled in the Logbook Reader (warnings banner, needs_check/manual statuses, `review_status`). |
| Forms CSF/CF2/**CF3**/CF4/PMRF | Four PDF forms: CSF, CF2, CF4 (2020 edition), PMRF | **DIFFERS:** CF3 removed 2026-10-21 (`3b48e87`). Some UI text still says "five forms" (IC-01 message; dashboard `0 / 5`). |
| PDF generation with PyMuPDF | Staff-facing printing uses **pdf-lib (browser)** for all four forms; PyMuPDF server export covers **CF2 and CSF only**, reached from the calibration workspace | **DIFFERS** in scope. |
| Tesseract | Testing panel / benchmarks only | Not in the production pipeline. |
| LAN access | Binds to `127.0.0.1:5000`, Flask dev server | **Not reachable on the LAN** without setting `OCR_HOST`. |
| Server-side access control | Many API routes (claims, review, OCR, templates, testing) have no `login_required` | Sign-in is enforced in the browser for these pages, not on those API routes. |
