"""Overlay field coordinate map - CSF (612x936 pt).

Ported field-for-field from PClaimAssist/js/pdf/overlays/csf.js
(window.PDF_OVERLAY_CSF). top/left/w are percent of the rendered page
(0-100); do not re-derive these by hand - they came from actual PDF
text/rect extraction against the real CSF.pdf template.
"""

CSF_OVERLAY = [
    # Member PIN
    {"id": "memberPIN", "key": "memberPIN", "page": 1, "top": 19.7, "left": 29, "w": 68, "fs": 8},
    # Member name row
    {"id": "memberLastName", "key": "memberLastName", "page": 1, "top": 21.2, "left": 4, "w": 19, "fs": 8},
    {"id": "memberFirstName", "key": "memberFirstName", "page": 1, "top": 21.2, "left": 24, "w": 19, "fs": 8},
    {"id": "memberNameExt", "key": "memberNameExt", "page": 1, "top": 21.2, "left": 44, "w": 7, "fs": 8},
    {"id": "memberMiddleName", "key": "memberMiddleName", "page": 1, "top": 21.2, "left": 52, "w": 21, "fs": 8},
    # Member DOB
    {"id": "memberDOB", "key": "memberDOB", "page": 1, "top": 20.9, "left": 75, "w": 22, "fs": 8, "computed": "memberDOB"},
    # Patient PIN row
    {"id": "patientPIN", "key": "patientPIN", "page": 1, "top": 25.9, "left": 29, "w": 68, "fs": 8},
    # Patient name row
    {"id": "patientLastName", "key": "patientLastName", "page": 1, "top": 28.1, "left": 4, "w": 19, "fs": 8},
    {"id": "patientFirstName", "key": "patientFirstName", "page": 1, "top": 28.1, "left": 24, "w": 19, "fs": 8},
    {"id": "patientNameExt", "key": "patientNameExt", "page": 1, "top": 28.1, "left": 44, "w": 7, "fs": 8},
    {"id": "patientMiddleName", "key": "patientMiddleName", "page": 1, "top": 28.1, "left": 52, "w": 21, "fs": 8},
    # Relationship
    {"id": "relationship", "key": "relationship", "page": 1, "top": 27.8, "left": 75, "w": 22, "fs": 8},
    # Confinement dates
    {"id": "dateAdmitted", "key": "dateAdmitted", "page": 1, "top": 34.5, "left": 10, "w": 26, "fs": 8, "computed": "dateAdmitted"},
    {"id": "dateDischarge", "key": "dateDischarge", "page": 1, "top": 34.5, "left": 40, "w": 26, "fs": 8, "computed": "dateDischarge"},
    # Patient DOB
    {"id": "patientDOB", "key": "patientDOB", "page": 1, "top": 34.5, "left": 76, "w": 21, "fs": 8, "computed": "patientDOB"},
    # Employer section
    {"id": "employerPEN", "key": "employerPEN", "page": 1, "top": 53.5, "left": 27, "w": 36, "fs": 8},
    {"id": "employerPhone", "key": "employerPhone", "page": 1, "top": 53.5, "left": 66, "w": 32, "fs": 8},
    # Business name
    {"id": "employerName", "key": "employerName", "page": 1, "top": 55.2, "left": 21, "w": 76, "fs": 8},
]
