# Research test reports - 5 November 2026

A copy of the finished proof reports and workbooks, so the group has them
without rerunning the tests. They were made on branch `jrad/field-mapping-fixes`
(research_tests/README.md has the commands to make them again). All data is
fictional (the answer key's test patients and the 10 writers' pages).

Each PDF has clickable contents and bookmarks; every number comes with the
pictures it was measured on.

| Test | Report | Workbook | Status |
|---|---|---|---|
| Field mapping (Eq. 3.6) | `field_mapping_proof_report.pdf` | `field_mapping_results.xlsx` (after the fixes), `field_mapping_results_before_fixes.xlsx` | **Provisional**: the expected box table is still being checked against the paper forms (`python -m research_tests.field_mapping_review`). 99.58% after the fixes, 96.99% before. |
| OCR field mapping | `ocr_field_mapping_proof_report.pdf` | `ocr_field_mapping_results.xlsx`, `ocr_field_mapping_results_before_fixes.xlsx` | **Provisional** (same table). Readings land in the right box 100%; end-to-end 39.93% (limited by the handwriting OCR). |
| Logbook cutting | `logbook_cutting_proof_report.pdf` | `logbook_cutting_results.xlsx` | **Checked by a person**: all 1980 cuts tagged on the review page (sheets "4-You ..."). Scanner 71.6% correct / 91.1% correct or partly; phone 59.2% / 68.0%. |
| OCR accuracy (handwriting, Eq. 3.1) | `ocr_accuracy_proof_report.pdf` | `ocr_accuracy_handwriting_results.xlsx` | Final (the approved handwriting run). PaddleOCR + Correction: scanner 4.62% exact, 60.67% of characters. |
| Correction module (Eq. 3.2-3.4) | `correction_proof_report.pdf` | `correction_metrics_results.xlsx`, `correction_changes.xlsx` (every change) | Final. Scanner: 294 changes, precision 0.0238, harmful rate 0.0102 (the 4 harmful changes are "-DO-" ditto marks, see section 4). |
| Image quality (IQ-01) | `iq_proof_report.pdf` | `iq_check_results.xlsx` | Final, with the new logbook-page checks: 10 of 10 bad pages warned, 0 of 10 normal. Real scans; 4 labels corrected (inputs/iq_expected.csv) - please confirm. Thresholds were set on these pages. |
| Validation engine (Eq. 3.7-3.10) | `validation_proof_report.pdf` | `validation_results.xlsx`, `seeded_errors_manifest.xlsx` | Final. 40 of 40 seeded errors flagged, precision/recall/F1 1.0, false alarm rate 0; all 31 rules covered (27 seeded, 4 engine-level). The errors were designed from the rule definitions. |

These are a snapshot: rerunning a test updates `research_tests/outputs/`, not this folder.
