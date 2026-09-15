/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – CF3 (612×1008 pt)
   top/left are % of rendered page (0–100).
   Coordinates derived from actual PDF text/rect extraction.
   (NOTE: All top% values have been corrected using the 100-X rule)
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF3 = [
  // HCI Accreditation No. (PAN) – one character per ruled digit box
  { id:'hciPANc1', key:'hciPANc1', page:1,
    top:16.95, left:46.3, w:2.5, fs:9, computed:'hciPANc1', center:true },

  { id:'hciPANc2', key:'hciPANc2', page:1,
    top:16.95, left:49.07, w:2.5, fs:9, computed:'hciPANc2', center:true },

  { id:'hciPANc3', key:'hciPANc3', page:1,
    top:16.95, left:51.84, w:2.5, fs:9, computed:'hciPANc3', center:true },

  { id:'hciPANc4', key:'hciPANc4', page:1,
    top:16.95, left:54.6, w:2.5, fs:9, computed:'hciPANc4', center:true },

  { id:'hciPANc5', key:'hciPANc5', page:1,
    top:16.95, left:57.37, w:2.5, fs:9, computed:'hciPANc5', center:true },

  { id:'hciPANc6', key:'hciPANc6', page:1,
    top:16.95, left:60.14, w:2.5, fs:9, computed:'hciPANc6', center:true },

  { id:'hciPANc7', key:'hciPANc7', page:1,
    top:16.95, left:62.9, w:2.5, fs:9, computed:'hciPANc7', center:true },

  { id:'hciPANc8', key:'hciPANc8', page:1,
    top:16.95, left:65.67, w:2.5, fs:9, computed:'hciPANc8', center:true },

  { id:'hciPANc9', key:'hciPANc9', page:1,
    top:16.95, left:68.43, w:2.5, fs:9, computed:'hciPANc9', center:true },

  // Patient Name
  { id:'patientLastName', key:'patientLastName', page:1,
    top:21.43, left:5, w:12, fs:8 },

  { id:'patientFirstName', key:'patientFirstName', page:1,
    top:21.43, left:18, w:11, fs:8 },

  { id:'patientMiddleName', key:'patientMiddleName', page:1,
    top:21.43, left:30.5, w:10, fs:8 },

  // Chief Complaint – printed box has room for several lines; wrap instead
  // of clipping (matches pdf-lib's own maxWidth wrapping on export)
  { id:'chiefComplaint', key:'chiefComplaint', page:1,
    top:22.2, left:73.5, w:22, fs:8, wrap:true },

  // Date Admitted – one overlay span per ruled digit box (matches the PDF's
  // per-character boxes, same approach as CSF/CF2's dateAdmittedD1-D8)
  { id:'dateAdmittedD1', key:'dateAdmittedD1', page:1, top:24.95, left:16.8,  w:1.9,  fs:8, digit:0, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD2', key:'dateAdmittedD2', page:1, top:24.95, left:18.7,  w:1.9,  fs:8, digit:1, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD3', key:'dateAdmittedD3', page:1, top:24.95, left:23.3,  w:1.9,  fs:8, digit:2, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD4', key:'dateAdmittedD4', page:1, top:24.95, left:25.2,  w:1.9,  fs:8, digit:3, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD5', key:'dateAdmittedD5', page:1, top:24.95, left:29.7,  w:1.88, fs:8, digit:4, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD6', key:'dateAdmittedD6', page:1, top:24.95, left:31.58, w:1.88, fs:8, digit:5, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD7', key:'dateAdmittedD7', page:1, top:24.95, left:33.45, w:1.88, fs:8, digit:6, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD8', key:'dateAdmittedD8', page:1, top:24.95, left:35.33, w:1.88, fs:8, digit:7, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },

  // Time Admitted – the PDF has 2 ruled hh:mm boxes on this row, one before
  // "AM" and one before "PM"; the value goes in whichever box matches
  { id:'timeAdmittedAM', key:'timeAdmittedAM', page:1,
    top:24.95, left:50.9, w:3.8, fs:7, computed:'timeAdmittedAM' },

  { id:'timeAdmittedPM', key:'timeAdmittedPM', page:1,
    top:24.95, left:59.2, w:3.8, fs:7, computed:'timeAdmittedPM' },

  // Date Discharged – same per-digit split as Date Admitted
  { id:'dateDischargeD1', key:'dateDischargeD1', page:1, top:28.15, left:16.8,  w:1.9,  fs:8, digit:0, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD2', key:'dateDischargeD2', page:1, top:28.15, left:18.7,  w:1.9,  fs:8, digit:1, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD3', key:'dateDischargeD3', page:1, top:28.15, left:23.3,  w:1.9,  fs:8, digit:2, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD4', key:'dateDischargeD4', page:1, top:28.15, left:25.2,  w:1.9,  fs:8, digit:3, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD5', key:'dateDischargeD5', page:1, top:28.15, left:29.7,  w:1.88, fs:8, digit:4, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD6', key:'dateDischargeD6', page:1, top:28.15, left:31.58, w:1.88, fs:8, digit:5, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD7', key:'dateDischargeD7', page:1, top:28.15, left:33.45, w:1.88, fs:8, digit:6, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD8', key:'dateDischargeD8', page:1, top:28.15, left:35.33, w:1.88, fs:8, digit:7, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },

  // Time Discharged – same 2-box AM/PM split as Time Admitted
  { id:'timeDischargeAM', key:'timeDischargeAM', page:1,
    top:28.15, left:50.9, w:3.8, fs:7, computed:'timeDischargeAM' },

  { id:'timeDischargePM', key:'timeDischargePM', page:1,
    top:28.15, left:59.2, w:3.8, fs:7, computed:'timeDischargePM' },

  // Brief History – wraps within the blank area below (see Chief Complaint)
  { id:'briefHistory', key:'briefHistory', page:1,
    top:34, left:7.8, w:88, fs:8, wrap:true },

  // Physical Examination – Vital Signs (row: Vital Signs / BP / CR / RR / Temperature / Abdomen)
  { id:'vitalBP', key:'vitalBP', page:1,
    top:50.6, left:18.8, w:5.9, fs:8 },

  { id:'vitalCR', key:'vitalCR', page:1,
    top:50.6, left:27.0, w:6.9, fs:8 },

  { id:'vitalRR', key:'vitalRR', page:1,
    top:50.6, left:36.3, w:7.1, fs:8 },

  { id:'vitalTemp', key:'vitalTemp', page:1,
    top:50.6, left:50.8, w:10.5, fs:8 },

  { id:'peAbdomen', key:'peAbdomen', page:1,
    top:50.6, left:75.0, w:21.7, fs:8 },

  // Physical Examination – HEENT / GU (IE)
  { id:'peHEENT', key:'peHEENT', page:1,
    top:53.46, left:15.2, w:46.1, fs:8 },

  { id:'peGU', key:'peGU', page:1,
    top:53.46, left:75.0, w:21.7, fs:8 },

  // Physical Examination – Chest/Lungs / Skin-Extremities
  { id:'peChestLungs', key:'peChestLungs', page:1,
    top:56.26, left:15.2, w:46.1, fs:8 },

  { id:'peSkinExtremities', key:'peSkinExtremities', page:1,
    top:56.26, left:75.0, w:21.7, fs:8 },

  // Physical Examination – CVS / Neuro Examination
  { id:'peCVS', key:'peCVS', page:1,
    top:59.06, left:15.2, w:46.1, fs:8 },

  { id:'peNeuroExam', key:'peNeuroExam', page:1,
    top:59.06, left:75.0, w:21.7, fs:8 },

  // Course in the Wards – wraps within the blank area below
  { id:'courseInWards', key:'courseInWards', page:1,
    top:67.3, left:7.8, w:88, fs:8, wrap:true },

  // Pertinent Laboratory and Diagnostic Findings – wraps within the blank area below
  { id:'labFindings', key:'labFindings', page:1,
    top:83.0, left:7.8, w:88, fs:8, wrap:true },

  // Disposition on Discharge – checkmark in the matching printed checkbox
  { id:'dispositionImproved', key:'dispositionImproved', page:1,
    top:93.85, left:22.3, w:2.5, fs:10, computed:'dispositionImproved' },

  { id:'dispositionTransferred', key:'dispositionTransferred', page:1,
    top:93.85, left:36.2, w:2.5, fs:10, computed:'dispositionTransferred' },

  { id:'dispositionHAMA', key:'dispositionHAMA', page:1,
    top:93.85, left:50.9, w:2.5, fs:10, computed:'dispositionHAMA' },

  { id:'dispositionAbsconded', key:'dispositionAbsconded', page:1,
    top:93.85, left:64.7, w:2.5, fs:10, computed:'dispositionAbsconded' },

  { id:'dispositionExpired', key:'dispositionExpired', page:1,
    top:93.85, left:76.7, w:2.5, fs:10, computed:'dispositionExpired' },

  /* ═══════ CF3 Page 2 — PART II: MATERNITY CARE PACKAGE ═══════ */

  // 1. Initial Prenatal Consultation – one span per ruled digit box
  { id:'initialPrenatalD1', key:'initialPrenatalD1', page:2, top:8.53, left:31.71, w:1.47,   fs:8, digit:0, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD2', key:'initialPrenatalD2', page:2, top:8.53, left:33.18, w:1.47,   fs:8, digit:1, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD3', key:'initialPrenatalD3', page:2, top:8.53, left:36.66, w:1.47,   fs:8, digit:2, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD4', key:'initialPrenatalD4', page:2, top:8.53, left:38.13, w:1.47,   fs:8, digit:3, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD5', key:'initialPrenatalD5', page:2, top:8.53, left:41.6,  w:1.4375, fs:8, digit:4, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD6', key:'initialPrenatalD6', page:2, top:8.53, left:43.04, w:1.4375, fs:8, digit:5, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD7', key:'initialPrenatalD7', page:2, top:8.53, left:44.48, w:1.4375, fs:8, digit:6, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },
  { id:'initialPrenatalD8', key:'initialPrenatalD8', page:2, top:8.53, left:45.91, w:1.4375, fs:8, digit:7, digitKey:'initialPrenatalDate', digitOrder:'mmddyyyy', center:true },

  // 2. Clinical History and Physical Examination
  { id:'vitalSignsNormal', key:'vitalSignsNormal', page:2,
    top:12.45, left:35.83, w:1.6, fs:9, checkbox:true },

  { id:'lmpD1', key:'lmpD1', page:2, top:12.45, left:55.72, w:1.47,   fs:8, digit:0, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD2', key:'lmpD2', page:2, top:12.45, left:57.19, w:1.47,   fs:8, digit:1, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD3', key:'lmpD3', page:2, top:12.45, left:60.66, w:1.47,   fs:8, digit:2, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD4', key:'lmpD4', page:2, top:12.45, left:62.13, w:1.47,   fs:8, digit:3, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD5', key:'lmpD5', page:2, top:12.45, left:65.6,  w:1.4425, fs:8, digit:4, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD6', key:'lmpD6', page:2, top:12.45, left:67.04, w:1.4425, fs:8, digit:5, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD7', key:'lmpD7', page:2, top:12.45, left:68.49, w:1.4425, fs:8, digit:6, digitKey:'lmp', digitOrder:'mmddyyyy' },
  { id:'lmpD8', key:'lmpD8', page:2, top:12.45, left:69.93, w:1.4425, fs:8, digit:7, digitKey:'lmp', digitOrder:'mmddyyyy' },

  { id:'ageOfMenarche2', key:'ageOfMenarche', page:2,
    top:12.3, left:81.99, w:6.45, fs:8 },

  { id:'pregnancyLowRisk', key:'pregnancyLowRisk', page:2,
    top:14.69, left:35.83, w:1.6, fs:9, checkbox:true },

  { id:'gravida2', key:'gravida', page:2,
    top:14.69, left:54.95, w:3.55, fs:8 },
  { id:'para2', key:'para', page:2,
    top:14.69, left:61.31, w:4.25, fs:8 },
  { id:'obTerm', key:'obTerm', page:2,
    top:14.69, left:66.24, w:2.84, fs:8 },
  { id:'obPreterm', key:'obPreterm', page:2,
    top:14.69, left:69.77, w:2.84, fs:8 },
  { id:'obAbortion', key:'obAbortion', page:2,
    top:14.69, left:73.32, w:2.84, fs:8 },
  { id:'obLiving', key:'obLiving', page:2,
    top:14.69, left:76.85, w:2.84, fs:8 },

  // Obstetric risk factors (Part II, section 3)
  { id:'riskMultiplePregnancy', key:'riskMultiplePregnancy', page:2,
    top:17.72, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskOvarianCyst', key:'riskOvarianCyst', page:2,
    top:19.05, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskMyomaUteri', key:'riskMyomaUteri', page:2,
    top:20.40, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskPlacentaPrevia', key:'riskPlacentaPrevia', page:2,
    top:17.72, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskMiscarriages', key:'riskMiscarriages', page:2,
    top:19.05, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskStillbirth', key:'riskStillbirth', page:2,
    top:20.40, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskPreeclampsia', key:'riskPreeclampsia', page:2,
    top:17.72, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskEclampsia', key:'riskEclampsia', page:2,
    top:19.05, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskPrematureContraction', key:'riskPrematureContraction', page:2,
    top:20.40, left:64.77, w:1.6, fs:9, checkbox:true },

  // Medical/Surgical risk factors (Part II, section 4)
  { id:'riskHypertension', key:'riskHypertension', page:2,
    top:23.43, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskHeartDisease', key:'riskHeartDisease', page:2,
    top:24.77, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskDiabetes', key:'riskDiabetes', page:2,
    top:26.12, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskThyroidDisorder', key:'riskThyroidDisorder', page:2,
    top:23.43, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskObesity', key:'riskObesity', page:2,
    top:24.77, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskAsthma', key:'riskAsthma', page:2,
    top:26.12, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskEpilepsy', key:'riskEpilepsy', page:2,
    top:23.43, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskRenalDisease', key:'riskRenalDisease', page:2,
    top:24.77, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskBleedingDisorders', key:'riskBleedingDisorders', page:2,
    top:26.12, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskPrevCesarian', key:'riskPrevCesarian', page:2,
    top:23.43, left:91.6, w:1.6, fs:9, checkbox:true },
  { id:'riskUterineMyomectomy', key:'riskUterineMyomectomy', page:2,
    top:24.77, left:91.6, w:1.6, fs:9, checkbox:true },

  // 5. Admitting Diagnosis
  { id:'admissionDx2', key:'admissionDx', page:2,
    top:28.25, left:21.06, w:72.75, fs:8 },

  // 6. Delivery Plan
  { id:'mcpOrientationYes', key:'mcpOrientation', page:2,
    top:32.27, left:36.54, w:1.6, fs:9, checkbox:true, checkValue:'yes' },
  { id:'mcpOrientationNo', key:'mcpOrientation', page:2,
    top:32.27, left:39.36, w:1.6, fs:9, checkbox:true, checkValue:'no' },

  { id:'expectedDDD1', key:'expectedDDD1', page:2, top:32.27, left:65.6,  w:1.47,   fs:8, digit:0, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD2', key:'expectedDDD2', page:2, top:32.27, left:67.07, w:1.47,   fs:8, digit:1, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD3', key:'expectedDDD3', page:2, top:32.27, left:70.55, w:1.47,   fs:8, digit:2, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD4', key:'expectedDDD4', page:2, top:32.27, left:72.02, w:1.47,   fs:8, digit:3, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD5', key:'expectedDDD5', page:2, top:32.27, left:75.48, w:1.4425, fs:8, digit:4, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD6', key:'expectedDDD6', page:2, top:32.27, left:76.92, w:1.4425, fs:8, digit:5, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD7', key:'expectedDDD7', page:2, top:32.27, left:78.37, w:1.4425, fs:8, digit:6, digitKey:'expectedDD', digitOrder:'mmddyyyy' },
  { id:'expectedDDD8', key:'expectedDDD8', page:2, top:32.27, left:79.81, w:1.4425, fs:8, digit:7, digitKey:'expectedDD', digitOrder:'mmddyyyy' },

  // Follow-up Prenatal Consultation grid — Date of visit (mm/dd/yy), one
  // span per ruled digit box (matches the per-character style used by the
  // rest of the form's date fields, e.g. Date Admitted)
  { id:'pncDate2d1', key:'pncDate2d1', page:2, top:38.16, left:24.53, w:0.845, fs:5, digit:0, digitKey:'pncDate2', center:true },
  { id:'pncDate2d2', key:'pncDate2d2', page:2, top:38.16, left:25.375, w:0.845, fs:5, digit:1, digitKey:'pncDate2', center:true },
  { id:'pncDate2d3', key:'pncDate2d3', page:2, top:38.16, left:26.22, w:0.845, fs:5, digit:2, digitKey:'pncDate2', center:true },
  { id:'pncDate2d4', key:'pncDate2d4', page:2, top:38.16, left:27.065, w:0.845, fs:5, digit:3, digitKey:'pncDate2', center:true },
  { id:'pncDate2d5', key:'pncDate2d5', page:2, top:38.16, left:27.91, w:0.845, fs:5, digit:4, digitKey:'pncDate2', center:true },
  { id:'pncDate2d6', key:'pncDate2d6', page:2, top:38.16, left:28.755, w:0.845, fs:5, digit:5, digitKey:'pncDate2', center:true },

  { id:'pncDate3d1', key:'pncDate3d1', page:2, top:38.16, left:30.88, w:0.845, fs:5, digit:0, digitKey:'pncDate3', center:true },
  { id:'pncDate3d2', key:'pncDate3d2', page:2, top:38.16, left:31.725, w:0.845, fs:5, digit:1, digitKey:'pncDate3', center:true },
  { id:'pncDate3d3', key:'pncDate3d3', page:2, top:38.16, left:32.57, w:0.845, fs:5, digit:2, digitKey:'pncDate3', center:true },
  { id:'pncDate3d4', key:'pncDate3d4', page:2, top:38.16, left:33.415, w:0.845, fs:5, digit:3, digitKey:'pncDate3', center:true },
  { id:'pncDate3d5', key:'pncDate3d5', page:2, top:38.16, left:34.26, w:0.845, fs:5, digit:4, digitKey:'pncDate3', center:true },
  { id:'pncDate3d6', key:'pncDate3d6', page:2, top:38.16, left:35.105, w:0.845, fs:5, digit:5, digitKey:'pncDate3', center:true },

  { id:'pncDate4d1', key:'pncDate4d1', page:2, top:38.16, left:37.24, w:0.845, fs:5, digit:0, digitKey:'pncDate4', center:true },
  { id:'pncDate4d2', key:'pncDate4d2', page:2, top:38.16, left:38.085, w:0.845, fs:5, digit:1, digitKey:'pncDate4', center:true },
  { id:'pncDate4d3', key:'pncDate4d3', page:2, top:38.16, left:38.93, w:0.845, fs:5, digit:2, digitKey:'pncDate4', center:true },
  { id:'pncDate4d4', key:'pncDate4d4', page:2, top:38.16, left:39.775, w:0.845, fs:5, digit:3, digitKey:'pncDate4', center:true },
  { id:'pncDate4d5', key:'pncDate4d5', page:2, top:38.16, left:40.62, w:0.845, fs:5, digit:4, digitKey:'pncDate4', center:true },
  { id:'pncDate4d6', key:'pncDate4d6', page:2, top:38.16, left:41.465, w:0.845, fs:5, digit:5, digitKey:'pncDate4', center:true },

  { id:'pncDate5d1', key:'pncDate5d1', page:2, top:38.16, left:43.59, w:0.845, fs:5, digit:0, digitKey:'pncDate5', center:true },
  { id:'pncDate5d2', key:'pncDate5d2', page:2, top:38.16, left:44.435, w:0.845, fs:5, digit:1, digitKey:'pncDate5', center:true },
  { id:'pncDate5d3', key:'pncDate5d3', page:2, top:38.16, left:45.28, w:0.845, fs:5, digit:2, digitKey:'pncDate5', center:true },
  { id:'pncDate5d4', key:'pncDate5d4', page:2, top:38.16, left:46.125, w:0.845, fs:5, digit:3, digitKey:'pncDate5', center:true },
  { id:'pncDate5d5', key:'pncDate5d5', page:2, top:38.16, left:46.97, w:0.845, fs:5, digit:4, digitKey:'pncDate5', center:true },
  { id:'pncDate5d6', key:'pncDate5d6', page:2, top:38.16, left:47.815, w:0.845, fs:5, digit:5, digitKey:'pncDate5', center:true },

  { id:'pncDate6d1', key:'pncDate6d1', page:2, top:38.16, left:49.95, w:0.845, fs:5, digit:0, digitKey:'pncDate6', center:true },
  { id:'pncDate6d2', key:'pncDate6d2', page:2, top:38.16, left:50.795, w:0.845, fs:5, digit:1, digitKey:'pncDate6', center:true },
  { id:'pncDate6d3', key:'pncDate6d3', page:2, top:38.16, left:51.64, w:0.845, fs:5, digit:2, digitKey:'pncDate6', center:true },
  { id:'pncDate6d4', key:'pncDate6d4', page:2, top:38.16, left:52.485, w:0.845, fs:5, digit:3, digitKey:'pncDate6', center:true },
  { id:'pncDate6d5', key:'pncDate6d5', page:2, top:38.16, left:53.33, w:0.845, fs:5, digit:4, digitKey:'pncDate6', center:true },
  { id:'pncDate6d6', key:'pncDate6d6', page:2, top:38.16, left:54.175, w:0.845, fs:5, digit:5, digitKey:'pncDate6', center:true },

  { id:'pncDate7d1', key:'pncDate7d1', page:2, top:38.16, left:56.31, w:0.845, fs:5, digit:0, digitKey:'pncDate7', center:true },
  { id:'pncDate7d2', key:'pncDate7d2', page:2, top:38.16, left:57.155, w:0.845, fs:5, digit:1, digitKey:'pncDate7', center:true },
  { id:'pncDate7d3', key:'pncDate7d3', page:2, top:38.16, left:58.0, w:0.845, fs:5, digit:2, digitKey:'pncDate7', center:true },
  { id:'pncDate7d4', key:'pncDate7d4', page:2, top:38.16, left:58.845, w:0.845, fs:5, digit:3, digitKey:'pncDate7', center:true },
  { id:'pncDate7d5', key:'pncDate7d5', page:2, top:38.16, left:59.69, w:0.845, fs:5, digit:4, digitKey:'pncDate7', center:true },
  { id:'pncDate7d6', key:'pncDate7d6', page:2, top:38.16, left:60.535, w:0.845, fs:5, digit:5, digitKey:'pncDate7', center:true },

  { id:'pncDate8d1', key:'pncDate8d1', page:2, top:38.16, left:62.66, w:0.845, fs:5, digit:0, digitKey:'pncDate8', center:true },
  { id:'pncDate8d2', key:'pncDate8d2', page:2, top:38.16, left:63.505, w:0.845, fs:5, digit:1, digitKey:'pncDate8', center:true },
  { id:'pncDate8d3', key:'pncDate8d3', page:2, top:38.16, left:64.35, w:0.845, fs:5, digit:2, digitKey:'pncDate8', center:true },
  { id:'pncDate8d4', key:'pncDate8d4', page:2, top:38.16, left:65.195, w:0.845, fs:5, digit:3, digitKey:'pncDate8', center:true },
  { id:'pncDate8d5', key:'pncDate8d5', page:2, top:38.16, left:66.04, w:0.845, fs:5, digit:4, digitKey:'pncDate8', center:true },
  { id:'pncDate8d6', key:'pncDate8d6', page:2, top:38.16, left:66.885, w:0.845, fs:5, digit:5, digitKey:'pncDate8', center:true },

  { id:'pncDate9d1', key:'pncDate9d1', page:2, top:38.16, left:69.02, w:0.845, fs:5, digit:0, digitKey:'pncDate9', center:true },
  { id:'pncDate9d2', key:'pncDate9d2', page:2, top:38.16, left:69.865, w:0.845, fs:5, digit:1, digitKey:'pncDate9', center:true },
  { id:'pncDate9d3', key:'pncDate9d3', page:2, top:38.16, left:70.71, w:0.845, fs:5, digit:2, digitKey:'pncDate9', center:true },
  { id:'pncDate9d4', key:'pncDate9d4', page:2, top:38.16, left:71.555, w:0.845, fs:5, digit:3, digitKey:'pncDate9', center:true },
  { id:'pncDate9d5', key:'pncDate9d5', page:2, top:38.16, left:72.4, w:0.845, fs:5, digit:4, digitKey:'pncDate9', center:true },
  { id:'pncDate9d6', key:'pncDate9d6', page:2, top:38.16, left:73.245, w:0.845, fs:5, digit:5, digitKey:'pncDate9', center:true },

  { id:'pncDate10d1', key:'pncDate10d1', page:2, top:38.16, left:75.38, w:0.845, fs:5, digit:0, digitKey:'pncDate10', center:true },
  { id:'pncDate10d2', key:'pncDate10d2', page:2, top:38.16, left:76.225, w:0.845, fs:5, digit:1, digitKey:'pncDate10', center:true },
  { id:'pncDate10d3', key:'pncDate10d3', page:2, top:38.16, left:77.07, w:0.845, fs:5, digit:2, digitKey:'pncDate10', center:true },
  { id:'pncDate10d4', key:'pncDate10d4', page:2, top:38.16, left:77.915, w:0.845, fs:5, digit:3, digitKey:'pncDate10', center:true },
  { id:'pncDate10d5', key:'pncDate10d5', page:2, top:38.16, left:78.76, w:0.845, fs:5, digit:4, digitKey:'pncDate10', center:true },
  { id:'pncDate10d6', key:'pncDate10d6', page:2, top:38.16, left:79.605, w:0.845, fs:5, digit:5, digitKey:'pncDate10', center:true },

  { id:'pncDate11d1', key:'pncDate11d1', page:2, top:38.16, left:81.72, w:0.845, fs:5, digit:0, digitKey:'pncDate11', center:true },
  { id:'pncDate11d2', key:'pncDate11d2', page:2, top:38.16, left:82.565, w:0.845, fs:5, digit:1, digitKey:'pncDate11', center:true },
  { id:'pncDate11d3', key:'pncDate11d3', page:2, top:38.16, left:83.41, w:0.845, fs:5, digit:2, digitKey:'pncDate11', center:true },
  { id:'pncDate11d4', key:'pncDate11d4', page:2, top:38.16, left:84.255, w:0.845, fs:5, digit:3, digitKey:'pncDate11', center:true },
  { id:'pncDate11d5', key:'pncDate11d5', page:2, top:38.16, left:85.1, w:0.845, fs:5, digit:4, digitKey:'pncDate11', center:true },
  { id:'pncDate11d6', key:'pncDate11d6', page:2, top:38.16, left:85.945, w:0.845, fs:5, digit:5, digitKey:'pncDate11', center:true },

  { id:'pncDate12d1', key:'pncDate12d1', page:2, top:38.16, left:88.07, w:0.845, fs:5, digit:0, digitKey:'pncDate12', center:true },
  { id:'pncDate12d2', key:'pncDate12d2', page:2, top:38.16, left:88.915, w:0.845, fs:5, digit:1, digitKey:'pncDate12', center:true },
  { id:'pncDate12d3', key:'pncDate12d3', page:2, top:38.16, left:89.76, w:0.845, fs:5, digit:2, digitKey:'pncDate12', center:true },
  { id:'pncDate12d4', key:'pncDate12d4', page:2, top:38.16, left:90.605, w:0.845, fs:5, digit:3, digitKey:'pncDate12', center:true },
  { id:'pncDate12d5', key:'pncDate12d5', page:2, top:38.16, left:91.45, w:0.845, fs:5, digit:4, digitKey:'pncDate12', center:true },
  { id:'pncDate12d6', key:'pncDate12d6', page:2, top:38.16, left:92.295, w:0.845, fs:5, digit:5, digitKey:'pncDate12', center:true },

  // Follow-up Prenatal Consultation grid — AOG in weeks
  { id:'pncAog2', key:'pncAog2', page:2,
    top:39.46, left:24.53, w:5.07, fs:6 },
  { id:'pncAog3', key:'pncAog3', page:2,
    top:39.46, left:30.88, w:5.07, fs:6 },
  { id:'pncAog4', key:'pncAog4', page:2,
    top:39.46, left:37.24, w:5.07, fs:6 },
  { id:'pncAog5', key:'pncAog5', page:2,
    top:39.46, left:43.59, w:5.07, fs:6 },
  { id:'pncAog6', key:'pncAog6', page:2,
    top:39.46, left:49.95, w:5.07, fs:6 },
  { id:'pncAog7', key:'pncAog7', page:2,
    top:39.46, left:56.31, w:5.07, fs:6 },
  { id:'pncAog8', key:'pncAog8', page:2,
    top:39.46, left:62.66, w:5.07, fs:6 },
  { id:'pncAog9', key:'pncAog9', page:2,
    top:39.46, left:69.02, w:5.07, fs:6 },
  { id:'pncAog10', key:'pncAog10', page:2,
    top:39.46, left:75.38, w:5.07, fs:6 },
  { id:'pncAog11', key:'pncAog11', page:2,
    top:39.46, left:81.72, w:5.07, fs:6 },
  { id:'pncAog12', key:'pncAog12', page:2,
    top:39.46, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Weight
  { id:'pncWeight2', key:'pncWeight2', page:2,
    top:41.92, left:24.53, w:5.07, fs:6 },
  { id:'pncWeight3', key:'pncWeight3', page:2,
    top:41.92, left:30.88, w:5.07, fs:6 },
  { id:'pncWeight4', key:'pncWeight4', page:2,
    top:41.92, left:37.24, w:5.07, fs:6 },
  { id:'pncWeight5', key:'pncWeight5', page:2,
    top:41.92, left:43.59, w:5.07, fs:6 },
  { id:'pncWeight6', key:'pncWeight6', page:2,
    top:41.92, left:49.95, w:5.07, fs:6 },
  { id:'pncWeight7', key:'pncWeight7', page:2,
    top:41.92, left:56.31, w:5.07, fs:6 },
  { id:'pncWeight8', key:'pncWeight8', page:2,
    top:41.92, left:62.66, w:5.07, fs:6 },
  { id:'pncWeight9', key:'pncWeight9', page:2,
    top:41.92, left:69.02, w:5.07, fs:6 },
  { id:'pncWeight10', key:'pncWeight10', page:2,
    top:41.92, left:75.38, w:5.07, fs:6 },
  { id:'pncWeight11', key:'pncWeight11', page:2,
    top:41.92, left:81.72, w:5.07, fs:6 },
  { id:'pncWeight12', key:'pncWeight12', page:2,
    top:41.92, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Cardiac Rate
  { id:'pncCr2', key:'pncCr2', page:2,
    top:43.27, left:24.53, w:5.07, fs:6 },
  { id:'pncCr3', key:'pncCr3', page:2,
    top:43.27, left:30.88, w:5.07, fs:6 },
  { id:'pncCr4', key:'pncCr4', page:2,
    top:43.27, left:37.24, w:5.07, fs:6 },
  { id:'pncCr5', key:'pncCr5', page:2,
    top:43.27, left:43.59, w:5.07, fs:6 },
  { id:'pncCr6', key:'pncCr6', page:2,
    top:43.27, left:49.95, w:5.07, fs:6 },
  { id:'pncCr7', key:'pncCr7', page:2,
    top:43.27, left:56.31, w:5.07, fs:6 },
  { id:'pncCr8', key:'pncCr8', page:2,
    top:43.27, left:62.66, w:5.07, fs:6 },
  { id:'pncCr9', key:'pncCr9', page:2,
    top:43.27, left:69.02, w:5.07, fs:6 },
  { id:'pncCr10', key:'pncCr10', page:2,
    top:43.27, left:75.38, w:5.07, fs:6 },
  { id:'pncCr11', key:'pncCr11', page:2,
    top:43.27, left:81.72, w:5.07, fs:6 },
  { id:'pncCr12', key:'pncCr12', page:2,
    top:43.27, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Respiratory Rate
  { id:'pncRr2', key:'pncRr2', page:2,
    top:44.61, left:24.53, w:5.07, fs:6 },
  { id:'pncRr3', key:'pncRr3', page:2,
    top:44.61, left:30.88, w:5.07, fs:6 },
  { id:'pncRr4', key:'pncRr4', page:2,
    top:44.61, left:37.24, w:5.07, fs:6 },
  { id:'pncRr5', key:'pncRr5', page:2,
    top:44.61, left:43.59, w:5.07, fs:6 },
  { id:'pncRr6', key:'pncRr6', page:2,
    top:44.61, left:49.95, w:5.07, fs:6 },
  { id:'pncRr7', key:'pncRr7', page:2,
    top:44.61, left:56.31, w:5.07, fs:6 },
  { id:'pncRr8', key:'pncRr8', page:2,
    top:44.61, left:62.66, w:5.07, fs:6 },
  { id:'pncRr9', key:'pncRr9', page:2,
    top:44.61, left:69.02, w:5.07, fs:6 },
  { id:'pncRr10', key:'pncRr10', page:2,
    top:44.61, left:75.38, w:5.07, fs:6 },
  { id:'pncRr11', key:'pncRr11', page:2,
    top:44.61, left:81.72, w:5.07, fs:6 },
  { id:'pncRr12', key:'pncRr12', page:2,
    top:44.61, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Blood Pressure
  { id:'pncBp2', key:'pncBp2', page:2,
    top:45.96, left:24.53, w:5.07, fs:6 },
  { id:'pncBp3', key:'pncBp3', page:2,
    top:45.96, left:30.88, w:5.07, fs:6 },
  { id:'pncBp4', key:'pncBp4', page:2,
    top:45.96, left:37.24, w:5.07, fs:6 },
  { id:'pncBp5', key:'pncBp5', page:2,
    top:45.96, left:43.59, w:5.07, fs:6 },
  { id:'pncBp6', key:'pncBp6', page:2,
    top:45.96, left:49.95, w:5.07, fs:6 },
  { id:'pncBp7', key:'pncBp7', page:2,
    top:45.96, left:56.31, w:5.07, fs:6 },
  { id:'pncBp8', key:'pncBp8', page:2,
    top:45.96, left:62.66, w:5.07, fs:6 },
  { id:'pncBp9', key:'pncBp9', page:2,
    top:45.96, left:69.02, w:5.07, fs:6 },
  { id:'pncBp10', key:'pncBp10', page:2,
    top:45.96, left:75.38, w:5.07, fs:6 },
  { id:'pncBp11', key:'pncBp11', page:2,
    top:45.96, left:81.72, w:5.07, fs:6 },
  { id:'pncBp12', key:'pncBp12', page:2,
    top:45.96, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Temperature
  { id:'pncTemp2', key:'pncTemp2', page:2,
    top:47.31, left:24.53, w:5.07, fs:6 },
  { id:'pncTemp3', key:'pncTemp3', page:2,
    top:47.31, left:30.88, w:5.07, fs:6 },
  { id:'pncTemp4', key:'pncTemp4', page:2,
    top:47.31, left:37.24, w:5.07, fs:6 },
  { id:'pncTemp5', key:'pncTemp5', page:2,
    top:47.31, left:43.59, w:5.07, fs:6 },
  { id:'pncTemp6', key:'pncTemp6', page:2,
    top:47.31, left:49.95, w:5.07, fs:6 },
  { id:'pncTemp7', key:'pncTemp7', page:2,
    top:47.31, left:56.31, w:5.07, fs:6 },
  { id:'pncTemp8', key:'pncTemp8', page:2,
    top:47.31, left:62.66, w:5.07, fs:6 },
  { id:'pncTemp9', key:'pncTemp9', page:2,
    top:47.31, left:69.02, w:5.07, fs:6 },
  { id:'pncTemp10', key:'pncTemp10', page:2,
    top:47.31, left:75.38, w:5.07, fs:6 },
  { id:'pncTemp11', key:'pncTemp11', page:2,
    top:47.31, left:81.72, w:5.07, fs:6 },
  { id:'pncTemp12', key:'pncTemp12', page:2,
    top:47.31, left:88.07, w:5.07, fs:6 },

  // 8. Date and Time of Delivery
  { id:'deliveryDateD1', key:'deliveryDateD1', page:2, top:51.88, left:31.71, w:1.47,   fs:8, digit:0, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD2', key:'deliveryDateD2', page:2, top:51.88, left:33.18, w:1.47,   fs:8, digit:1, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD3', key:'deliveryDateD3', page:2, top:51.88, left:36.66, w:1.47,   fs:8, digit:2, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD4', key:'deliveryDateD4', page:2, top:51.88, left:38.13, w:1.47,   fs:8, digit:3, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD5', key:'deliveryDateD5', page:2, top:51.88, left:41.6,  w:1.4375, fs:8, digit:4, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD6', key:'deliveryDateD6', page:2, top:51.88, left:43.04, w:1.4375, fs:8, digit:5, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD7', key:'deliveryDateD7', page:2, top:51.88, left:44.48, w:1.4375, fs:8, digit:6, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryDateD8', key:'deliveryDateD8', page:2, top:51.88, left:45.91, w:1.4375, fs:8, digit:7, digitKey:'deliveryDate', digitOrder:'mmddyyyy' },
  { id:'deliveryTimeAM', key:'deliveryTime', page:2,
    top:51.88, left:55.01, w:2.94, fs:5, timeComponent:'AM' },
  { id:'deliveryTimePM', key:'deliveryTime', page:2,
    top:51.88, left:60.66, w:2.94, fs:5, timeComponent:'PM' },

  // 9. Maternal Outcome
  { id:'obstetricIndex', key:'obstetricIndex', page:2,
    top:55.19, left:21.06, w:7.77, fs:7 },
  { id:'pregnancyUterineAOG', key:'pregnancyUterineAOG', page:2,
    top:55.19, left:39.41, w:17.66, fs:7 },
  { id:'mannerOfDelivery2', key:'mannerOfDelivery', page:2,
    top:55.29, left:58.47, w:16.96, fs:5 },
  { id:'presentation', key:'presentation', page:2,
    top:55.19, left:76.85, w:16.97, fs:7 },

  // 10. Birth Outcome
  { id:'fetalOutcome2', key:'fetalOutcome', page:2,
    top:58.55, left:21.06, w:16.96, fs:7 },
  { id:'babySex2', key:'babySex', page:2,
    top:58.55, left:39.41, w:17.66, fs:7 },
  { id:'birthWeight2', key:'birthWeight', page:2,
    top:58.55, left:58.47, w:16.96, fs:7 },
  { id:'apgarScore2', key:'apgarScore', page:2,
    top:58.55, left:76.85, w:16.97, fs:7 },

  // 11. Scheduled Postpartum follow-up consultation
  { id:'postpartumFollowupD1', key:'postpartumFollowupD1', page:2, top:61.40, left:55.01, w:1.47,   fs:8, digit:0, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD2', key:'postpartumFollowupD2', page:2, top:61.40, left:56.48, w:1.47,   fs:8, digit:1, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD3', key:'postpartumFollowupD3', page:2, top:61.40, left:59.95, w:1.47,   fs:8, digit:2, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD4', key:'postpartumFollowupD4', page:2, top:61.40, left:61.42, w:1.47,   fs:8, digit:3, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD5', key:'postpartumFollowupD5', page:2, top:61.40, left:64.89, w:1.4425, fs:8, digit:4, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD6', key:'postpartumFollowupD6', page:2, top:61.40, left:66.33, w:1.4425, fs:8, digit:5, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD7', key:'postpartumFollowupD7', page:2, top:61.40, left:67.78, w:1.4425, fs:8, digit:6, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },
  { id:'postpartumFollowupD8', key:'postpartumFollowupD8', page:2, top:61.40, left:69.22, w:1.4425, fs:8, digit:7, digitKey:'postpartumFollowupDate', digitOrder:'mmddyyyy' },

  // 12. Date and Time of Discharge (same underlying data as CF3 page 1)
  { id:'dischargeD1_p2', key:'dischargeD1_p2', page:2, top:63.65, left:31.71, w:1.47,   fs:8, digit:0, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD2_p2', key:'dischargeD2_p2', page:2, top:63.65, left:33.18, w:1.47,   fs:8, digit:1, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD3_p2', key:'dischargeD3_p2', page:2, top:63.65, left:36.66, w:1.47,   fs:8, digit:2, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD4_p2', key:'dischargeD4_p2', page:2, top:63.65, left:38.13, w:1.47,   fs:8, digit:3, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD5_p2', key:'dischargeD5_p2', page:2, top:63.65, left:41.6,  w:1.4375, fs:8, digit:4, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD6_p2', key:'dischargeD6_p2', page:2, top:63.65, left:43.04, w:1.4375, fs:8, digit:5, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD7_p2', key:'dischargeD7_p2', page:2, top:63.65, left:44.48, w:1.4375, fs:8, digit:6, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeD8_p2', key:'dischargeD8_p2', page:2, top:63.65, left:45.91, w:1.4375, fs:8, digit:7, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'dischargeTimeAM2', key:'timeDischargeAM', page:2,
    top:63.65, left:55.72, w:2.94, fs:5, computed:'timeDischargeAM' },
  { id:'dischargeTimePM2', key:'timeDischargePM', page:2,
    top:63.65, left:61.37, w:2.94, fs:5, computed:'timeDischargePM' },

  // Perineal wound care
  { id:'ppPerinealDone', key:'ppPerinealDone', page:2,
    top:69.91, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppPerinealRemarks', key:'ppPerinealRemarks', page:2,
    top:69.86, left:57.8, w:36.0, fs:7 },

  // Signs of Maternal Postpartum Complications
  { id:'ppComplicationsDone', key:'ppComplicationsDone', page:2,
    top:71.26, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppComplicationsRemarks', key:'ppComplicationsRemarks', page:2,
    top:71.21, left:57.8, w:36.0, fs:7 },

  // Breastfeeding and Nutrition
  { id:'ppBreastfeedingDone', key:'ppBreastfeedingDone', page:2,
    top:73.95, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppBreastfeedingRemarks', key:'ppBreastfeedingRemarks', page:2,
    top:73.9, left:57.8, w:36.0, fs:7 },

  // Family Planning
  { id:'ppFamilyPlanningDone', key:'ppFamilyPlanningDone', page:2,
    top:75.30, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppFamilyPlanningRemarks', key:'ppFamilyPlanningRemarks', page:2,
    top:75.25, left:57.8, w:36.0, fs:7 },

  // Provided family planning service to patient
  { id:'ppFPServiceDone', key:'ppFPServiceDone', page:2,
    top:76.63, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppFPServiceRemarks', key:'ppFPServiceRemarks', page:2,
    top:76.58, left:57.8, w:36.0, fs:7 },

  // Referred to partner physician for Voluntary Surgical Sterilization
  { id:'ppReferredVSSDone', key:'ppReferredVSSDone', page:2,
    top:77.98, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppReferredVSSRemarks', key:'ppReferredVSSRemarks', page:2,
    top:77.93, left:57.8, w:36.0, fs:7 },

  // Schedule the next postpartum follow-up
  { id:'ppScheduleNextDone', key:'ppScheduleNextDone', page:2,
    top:79.32, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppScheduleNextRemarks', key:'ppScheduleNextRemarks', page:2,
    top:79.27, left:57.8, w:36.0, fs:7 },

  // 19. Certification of Attending Physician/Midwife
  { id:'attendingPhysicianName', key:'attendingPhysicianName', page:2,
    top:86.34, left:9.05, w:36.03, fs:8 },
  { id:'dateSignedD1', key:'dateSignedD1', page:2, top:86.97, left:58.54, w:1.47,   fs:8, digit:0, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD2', key:'dateSignedD2', page:2, top:86.97, left:60.01, w:1.47,   fs:8, digit:1, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD3', key:'dateSignedD3', page:2, top:86.97, left:63.48, w:1.47,   fs:8, digit:2, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD4', key:'dateSignedD4', page:2, top:86.97, left:64.95, w:1.47,   fs:8, digit:3, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD5', key:'dateSignedD5', page:2, top:86.97, left:68.42, w:1.4425, fs:8, digit:4, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD6', key:'dateSignedD6', page:2, top:86.97, left:69.86, w:1.4425, fs:8, digit:5, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD7', key:'dateSignedD7', page:2, top:86.97, left:71.31, w:1.4425, fs:8, digit:6, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
  { id:'dateSignedD8', key:'dateSignedD8', page:2, top:86.97, left:72.75, w:1.4425, fs:8, digit:7, digitKey:'dateSigned', digitOrder:'mmddyyyy' },
];
