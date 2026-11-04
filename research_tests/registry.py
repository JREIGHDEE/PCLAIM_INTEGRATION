"""The tests, in tab order - plain data, shared by run_all.py and the web
tabs (which never import the test modules themselves: each run is its own
process, see web/jobs.py)."""

TESTS = [
    {"key": "handwriting", "tab": "Handwriting (10 Writers)", "workbook": "handwriting_results.xlsx",
     "summary": "PaddleOCR vs Tesseract, raw and corrected, on 10 writers' scans (5 capitals, 5 lowercase): exact "
                "match and character accuracy per writer, style group and field, row detection rate.",
     "inputs": ["writers.csv", "scans/handwriting/*.pdf", "answer_key.xlsx (sheet Handwriting)"],
     "uploads": {"writers": "writers.csv", "answer_key": "answer_key.xlsx", "scans": "scans/handwriting/"},
     "options": [{"name": "writers", "label": "Only these writers (e.g. W01,W02)", "type": "text"},
                 {"name": "fresh", "label": "Read every scan again", "type": "check"}], "ocr": True},
    {"key": "correction_metrics", "tab": "Correction Metrics", "workbook": "correction_metrics_results.xlsx",
     "summary": "Eq. 3.2-3.4 from the OCR comparison workbook and the handwriting results: accuracy improvement, "
                "correction precision, harmful correction rate.",
     "inputs": ["Ocr_module/uploads/ocr_compare_results.xlsx (read-only)", "outputs/handwriting (test 1)"],
     "uploads": {},
     "options": [{"name": "source", "label": "Source", "type": "select",
                  "choices": ["both", "workbook", "handwriting"]}], "ocr": False, "samples": False},
    {"key": "field_mapping", "tab": "Field Mapping", "workbook": "field_mapping_results.xlsx",
     "summary": "Eq. 3.6: about 20 patients' confirmed values through the real auto-population; each value checked "
                "in its box on CSF, CF1, CF2, CF4 and PMRF, on screen and on the saved PDF.",
     "inputs": ["answer_key.xlsx (sheet Patients)", "field_mapping_expected.csv (check it against the paper forms)"],
     "uploads": {"answer_key": "answer_key.xlsx", "expected": "field_mapping_expected.csv"},
     "options": [{"name": "limit", "label": "Patients", "type": "number", "default": 20}], "ocr": False},
    {"key": "validation", "tab": "Validation (Seeded Errors)", "workbook": "validation_results.xlsx",
     "summary": "Eq. 3.7-3.10: 40 records (20 clean, 20 with 40 seeded errors) through the real validation "
                "engine; TP, FP, FN, precision, recall, F1, false alarm rate.",
     "inputs": ["answer_key.xlsx (sheet Patients)"], "uploads": {"answer_key": "answer_key.xlsx"},
     "options": [{"name": "seed", "label": "Seed", "type": "number", "default": 20261104}], "ocr": False},
    {"key": "performance", "tab": "Performance", "workbook": "performance_results.xlsx",
     "summary": "Time per stage (image quality, detection, OCR, correction, auto-population, validation, PDF) and "
                "for the whole pipeline per logbook entry, with the machine's specs.",
     "inputs": ["scans/performance/* (or the handwriting scans)"], "uploads": {"scans": "scans/performance/"},
     "options": [{"name": "scans", "label": "Scans to time (0 = all)", "type": "number", "default": 3}],
     "ocr": True},
    {"key": "iq_check", "tab": "Image Quality", "workbook": "iq_check_results.xlsx",
     "summary": "Rule IQ-01 on good and deliberately bad scans: blur variance, brightness, whether the warning "
                "fired and whether that matched the expected outcome.",
     "inputs": ["iq/good/*", "iq/bad/*", "iq/expected.csv (optional)"],
     "uploads": {"good": "iq/good/", "bad": "iq/bad/", "expected": "iq/expected.csv"}, "options": [], "ocr": False},
    {"key": "user_sessions", "tab": "User Sessions", "workbook": "user_sessions_results.xlsx",
     "summary": "Eq. 3.11, 3.12, 3.5 per participant and the median: time per claim and its reduction, errors per "
                "claim and their reduction, suggestion acceptance rate.",
     "inputs": ["session_data.xlsx (template: session_data_template.xlsx)", "sus.xlsx (optional)"],
     "uploads": {"sessions": "session_data.xlsx", "sus": "sus.xlsx"}, "options": [], "ocr": False},
]
BY_KEY = {t["key"]: t for t in TESTS}
RESULTS = {"key": "results", "tab": "Results", "workbook": "chapter5_results.xlsx"}
