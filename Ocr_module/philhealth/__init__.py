"""PhilHealth claim-form field mapping, validation, and PDF export.

Bridges data already stored by the OCR/case-session pipeline (case_sessions,
patients, encounters) onto the claims-table field vocabulary the database
schema already defines, then fills/exports the real CF2/CSF PhilHealth PDF
templates in PClaimAssist/forms/.

See field_catalog.py for the field lists (ported from PClaimAssist's own
js/app.js VAL_FIELDS/getComputedValue - not invented here), mapping_service.py
for the pure mapping/validation layer, case_bridge.py for the OCR-to-schema
bridge, and pdf_export.py for the PyMuPDF-based fill/export.
"""
