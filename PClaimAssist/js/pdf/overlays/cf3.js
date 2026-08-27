/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – CF3 (612×1008 pt)
   top/left are % of rendered page (0–100).
   Coordinates derived from actual PDF text/rect extraction.
   (NOTE: All top% values have been corrected using the 100-X rule)
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF3 = [
  // HCI Accreditation No. (PAN) – one character per ruled digit box
  { id:'hciPANc1', key:'hciPANc1', page:1,
    top:17.3, left:47.2, w:2.5, fs:9, computed:'hciPANc1' },

  { id:'hciPANc2', key:'hciPANc2', page:1,
    top:17.3, left:50.0, w:2.5, fs:9, computed:'hciPANc2' },

  { id:'hciPANc3', key:'hciPANc3', page:1,
    top:17.3, left:52.7, w:2.5, fs:9, computed:'hciPANc3' },

  { id:'hciPANc4', key:'hciPANc4', page:1,
    top:17.3, left:55.5, w:2.5, fs:9, computed:'hciPANc4' },

  { id:'hciPANc5', key:'hciPANc5', page:1,
    top:17.3, left:58.3, w:2.5, fs:9, computed:'hciPANc5' },

  { id:'hciPANc6', key:'hciPANc6', page:1,
    top:17.3, left:61.0, w:2.5, fs:9, computed:'hciPANc6' },

  { id:'hciPANc7', key:'hciPANc7', page:1,
    top:17.3, left:63.8, w:2.5, fs:9, computed:'hciPANc7' },

  { id:'hciPANc8', key:'hciPANc8', page:1,
    top:17.3, left:66.6, w:2.5, fs:9, computed:'hciPANc8' },

  { id:'hciPANc9', key:'hciPANc9', page:1,
    top:17.3, left:69.3, w:2.5, fs:9, computed:'hciPANc9' },

  // Patient Name
  { id:'patientLastName', key:'patientLastName', page:1,
    top:21.4, left:5, w:12, fs:8 },

  { id:'patientFirstName', key:'patientFirstName', page:1,
    top:21.4, left:18, w:11, fs:8 },

  { id:'patientMiddleName', key:'patientMiddleName', page:1,
    top:21.4, left:30.5, w:10, fs:8 },

  // Chief Complaint
  { id:'chiefComplaint', key:'chiefComplaint', page:1,
    top:22.2, left:73.5, w:22, fs:8 },

  // Date Admitted – split into the PDF's 3 separate ruled boxes (Month / Day / Year)
  { id:'dateAdmittedMM', key:'dateAdmittedMM', page:1,
    top:25.3, left:16.8, w:3.8, fs:8, computed:'dateAdmittedMM' },

  { id:'dateAdmittedDD', key:'dateAdmittedDD', page:1,
    top:25.3, left:23.3, w:3.8, fs:8, computed:'dateAdmittedDD' },

  { id:'dateAdmittedYYYY', key:'dateAdmittedYYYY', page:1,
    top:25.3, left:29.7, w:7.5, fs:8, computed:'dateAdmittedYYYY' },

  // Time Admitted – the PDF has 2 ruled hh:mm boxes on this row, one before
  // "AM" and one before "PM"; the value goes in whichever box matches
  { id:'timeAdmittedAM', key:'timeAdmittedAM', page:1,
    top:25.3, left:50.9, w:3.8, fs:7, computed:'timeAdmittedAM' },

  { id:'timeAdmittedPM', key:'timeAdmittedPM', page:1,
    top:25.3, left:59.2, w:3.8, fs:7, computed:'timeAdmittedPM' },

  // Date Discharged – same 3-box split as Date Admitted
  { id:'dateDischargeMM', key:'dateDischargeMM', page:1,
    top:28.5, left:16.8, w:3.8, fs:8, computed:'dateDischargeMM' },

  { id:'dateDischargeDD', key:'dateDischargeDD', page:1,
    top:28.5, left:23.3, w:3.8, fs:8, computed:'dateDischargeDD' },

  { id:'dateDischargeYYYY', key:'dateDischargeYYYY', page:1,
    top:28.5, left:29.7, w:7.5, fs:8, computed:'dateDischargeYYYY' },

  // Time Discharged – same 2-box AM/PM split as Time Admitted
  { id:'timeDischargeAM', key:'timeDischargeAM', page:1,
    top:28.5, left:50.9, w:3.8, fs:7, computed:'timeDischargeAM' },

  { id:'timeDischargePM', key:'timeDischargePM', page:1,
    top:28.5, left:59.2, w:3.8, fs:7, computed:'timeDischargePM' },

  // Brief History
  { id:'briefHistory', key:'briefHistory', page:1,
    top:34, left:7.8, w:88, fs:8 },

  // Physical Examination – Vital Signs (row: Vital Signs / BP / CR / RR / Temperature / Abdomen)
  { id:'vitalBP', key:'vitalBP', page:1,
    top:51.4, left:18.8, w:5.9, fs:8 },

  { id:'vitalCR', key:'vitalCR', page:1,
    top:51.4, left:27.0, w:6.9, fs:8 },

  { id:'vitalRR', key:'vitalRR', page:1,
    top:51.4, left:36.3, w:7.1, fs:8 },

  { id:'vitalTemp', key:'vitalTemp', page:1,
    top:51.4, left:50.8, w:10.5, fs:8 },

  { id:'peAbdomen', key:'peAbdomen', page:1,
    top:51.4, left:75.0, w:21.7, fs:8 },

  // Physical Examination – HEENT / GU (IE)
  { id:'peHEENT', key:'peHEENT', page:1,
    top:54.3, left:15.2, w:46.1, fs:8 },

  { id:'peGU', key:'peGU', page:1,
    top:54.3, left:75.0, w:21.7, fs:8 },

  // Physical Examination – Chest/Lungs / Skin-Extremities
  { id:'peChestLungs', key:'peChestLungs', page:1,
    top:57.1, left:15.2, w:46.1, fs:8 },

  { id:'peSkinExtremities', key:'peSkinExtremities', page:1,
    top:57.1, left:75.0, w:21.7, fs:8 },

  // Physical Examination – CVS / Neuro Examination
  { id:'peCVS', key:'peCVS', page:1,
    top:59.9, left:15.2, w:46.1, fs:8 },

  { id:'peNeuroExam', key:'peNeuroExam', page:1,
    top:59.9, left:75.0, w:21.7, fs:8 },

  // Course in the Wards
  { id:'courseInWards', key:'courseInWards', page:1,
    top:67.3, left:7.8, w:88, fs:8 },

  // Pertinent Laboratory and Diagnostic Findings
  { id:'labFindings', key:'labFindings', page:1,
    top:83.0, left:7.8, w:88, fs:8 },

  // Disposition on Discharge – checkmark in the matching printed checkbox
  { id:'dispositionImproved', key:'dispositionImproved', page:1,
    top:94.2, left:22.3, w:2.5, fs:10, computed:'dispositionImproved' },

  { id:'dispositionTransferred', key:'dispositionTransferred', page:1,
    top:94.2, left:36.2, w:2.5, fs:10, computed:'dispositionTransferred' },

  { id:'dispositionHAMA', key:'dispositionHAMA', page:1,
    top:94.2, left:50.9, w:2.5, fs:10, computed:'dispositionHAMA' },

  { id:'dispositionAbsconded', key:'dispositionAbsconded', page:1,
    top:94.2, left:64.7, w:2.5, fs:10, computed:'dispositionAbsconded' },

  { id:'dispositionExpired', key:'dispositionExpired', page:1,
    top:94.2, left:76.7, w:2.5, fs:10, computed:'dispositionExpired' },

  /* ═══════ CF3 Page 2 — PART II: MATERNITY CARE PACKAGE ═══════ */

  // 1. Initial Prenatal Consultation (date, 3 boxes)
  { id:'initialPrenatalMM', key:'initialPrenatalDate', page:2,
    top:8.88, left:31.58, w:2.94, fs:8, dateComponent:'MM' },
  { id:'initialPrenatalDD', key:'initialPrenatalDate', page:2,
    top:8.88, left:36.54, w:2.94, fs:8, dateComponent:'DD' },
  { id:'initialPrenatalYYYY', key:'initialPrenatalDate', page:2,
    top:8.88, left:41.49, w:5.75, fs:8, dateComponent:'YYYY' },

  // 2. Clinical History and Physical Examination
  { id:'vitalSignsNormal', key:'vitalSignsNormal', page:2,
    top:12.8, left:35.83, w:1.6, fs:9, checkbox:true },

  { id:'lmpMM2', key:'lmp', page:2,
    top:12.8, left:55.6, w:2.94, fs:8, dateComponent:'MM' },
  { id:'lmpDD2', key:'lmp', page:2,
    top:12.8, left:60.54, w:2.94, fs:8, dateComponent:'DD' },
  { id:'lmpYYYY2', key:'lmp', page:2,
    top:12.8, left:65.49, w:5.77, fs:8, dateComponent:'YYYY' },

  { id:'ageOfMenarche2', key:'ageOfMenarche', page:2,
    top:12.65, left:81.99, w:6.45, fs:8 },

  { id:'pregnancyLowRisk', key:'pregnancyLowRisk', page:2,
    top:15.04, left:35.83, w:1.6, fs:9, checkbox:true },

  { id:'gravida2', key:'gravida', page:2,
    top:15.04, left:54.95, w:3.55, fs:8 },
  { id:'para2', key:'para', page:2,
    top:15.04, left:61.31, w:4.25, fs:8 },
  { id:'obTerm', key:'obTerm', page:2,
    top:15.04, left:66.24, w:2.84, fs:8 },
  { id:'obPreterm', key:'obPreterm', page:2,
    top:15.04, left:69.77, w:2.84, fs:8 },
  { id:'obAbortion', key:'obAbortion', page:2,
    top:15.04, left:73.32, w:2.84, fs:8 },
  { id:'obLiving', key:'obLiving', page:2,
    top:15.04, left:76.85, w:2.84, fs:8 },

  // Obstetric risk factors (Part II, section 3)
  { id:'riskMultiplePregnancy', key:'riskMultiplePregnancy', page:2,
    top:18.07, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskOvarianCyst', key:'riskOvarianCyst', page:2,
    top:19.4, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskMyomaUteri', key:'riskMyomaUteri', page:2,
    top:20.75, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskPlacentaPrevia', key:'riskPlacentaPrevia', page:2,
    top:18.07, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskMiscarriages', key:'riskMiscarriages', page:2,
    top:19.4, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskStillbirth', key:'riskStillbirth', page:2,
    top:20.75, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskPreeclampsia', key:'riskPreeclampsia', page:2,
    top:18.07, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskEclampsia', key:'riskEclampsia', page:2,
    top:19.4, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskPrematureContraction', key:'riskPrematureContraction', page:2,
    top:20.75, left:64.77, w:1.6, fs:9, checkbox:true },

  // Medical/Surgical risk factors (Part II, section 4)
  { id:'riskHypertension', key:'riskHypertension', page:2,
    top:23.78, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskHeartDisease', key:'riskHeartDisease', page:2,
    top:25.12, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskDiabetes', key:'riskDiabetes', page:2,
    top:26.47, left:21.0, w:1.6, fs:9, checkbox:true },
  { id:'riskThyroidDisorder', key:'riskThyroidDisorder', page:2,
    top:23.78, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskObesity', key:'riskObesity', page:2,
    top:25.12, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskAsthma', key:'riskAsthma', page:2,
    top:26.47, left:43.59, w:1.6, fs:9, checkbox:true },
  { id:'riskEpilepsy', key:'riskEpilepsy', page:2,
    top:23.78, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskRenalDisease', key:'riskRenalDisease', page:2,
    top:25.12, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskBleedingDisorders', key:'riskBleedingDisorders', page:2,
    top:26.47, left:64.77, w:1.6, fs:9, checkbox:true },
  { id:'riskPrevCesarian', key:'riskPrevCesarian', page:2,
    top:23.78, left:91.6, w:1.6, fs:9, checkbox:true },
  { id:'riskUterineMyomectomy', key:'riskUterineMyomectomy', page:2,
    top:25.12, left:91.6, w:1.6, fs:9, checkbox:true },

  // 5. Admitting Diagnosis
  { id:'admissionDx2', key:'admissionDx', page:2,
    top:28.7, left:21.06, w:72.75, fs:8 },

  // 6. Delivery Plan
  { id:'mcpOrientationYes', key:'mcpOrientation', page:2,
    top:32.62, left:36.54, w:1.6, fs:9, checkbox:true, checkValue:'yes' },
  { id:'mcpOrientationNo', key:'mcpOrientation', page:2,
    top:32.62, left:39.36, w:1.6, fs:9, checkbox:true, checkValue:'no' },

  { id:'expectedDDMM', key:'expectedDD', page:2,
    top:32.62, left:65.49, w:2.94, fs:8, dateComponent:'MM' },
  { id:'expectedDDDD', key:'expectedDD', page:2,
    top:32.62, left:70.42, w:2.94, fs:8, dateComponent:'DD' },
  { id:'expectedDDYYYY', key:'expectedDD', page:2,
    top:32.62, left:75.37, w:5.77, fs:8, dateComponent:'YYYY' },

  // Follow-up Prenatal Consultation grid — Date of visit (mm/dd/yy)
  { id:'pncDate2', key:'pncDate2', page:2,
    top:38.44, left:24.53, w:5.07, fs:6 },
  { id:'pncDate3', key:'pncDate3', page:2,
    top:38.44, left:30.88, w:5.07, fs:6 },
  { id:'pncDate4', key:'pncDate4', page:2,
    top:38.44, left:37.24, w:5.07, fs:6 },
  { id:'pncDate5', key:'pncDate5', page:2,
    top:38.44, left:43.59, w:5.07, fs:6 },
  { id:'pncDate6', key:'pncDate6', page:2,
    top:38.44, left:49.95, w:5.07, fs:6 },
  { id:'pncDate7', key:'pncDate7', page:2,
    top:38.44, left:56.31, w:5.07, fs:6 },
  { id:'pncDate8', key:'pncDate8', page:2,
    top:38.44, left:62.66, w:5.07, fs:6 },
  { id:'pncDate9', key:'pncDate9', page:2,
    top:38.44, left:69.02, w:5.07, fs:6 },
  { id:'pncDate10', key:'pncDate10', page:2,
    top:38.44, left:75.38, w:5.07, fs:6 },
  { id:'pncDate11', key:'pncDate11', page:2,
    top:38.44, left:81.72, w:5.07, fs:6 },
  { id:'pncDate12', key:'pncDate12', page:2,
    top:38.44, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — AOG in weeks
  { id:'pncAog2', key:'pncAog2', page:2,
    top:39.79, left:24.53, w:5.07, fs:6 },
  { id:'pncAog3', key:'pncAog3', page:2,
    top:39.79, left:30.88, w:5.07, fs:6 },
  { id:'pncAog4', key:'pncAog4', page:2,
    top:39.79, left:37.24, w:5.07, fs:6 },
  { id:'pncAog5', key:'pncAog5', page:2,
    top:39.79, left:43.59, w:5.07, fs:6 },
  { id:'pncAog6', key:'pncAog6', page:2,
    top:39.79, left:49.95, w:5.07, fs:6 },
  { id:'pncAog7', key:'pncAog7', page:2,
    top:39.79, left:56.31, w:5.07, fs:6 },
  { id:'pncAog8', key:'pncAog8', page:2,
    top:39.79, left:62.66, w:5.07, fs:6 },
  { id:'pncAog9', key:'pncAog9', page:2,
    top:39.79, left:69.02, w:5.07, fs:6 },
  { id:'pncAog10', key:'pncAog10', page:2,
    top:39.79, left:75.38, w:5.07, fs:6 },
  { id:'pncAog11', key:'pncAog11', page:2,
    top:39.79, left:81.72, w:5.07, fs:6 },
  { id:'pncAog12', key:'pncAog12', page:2,
    top:39.79, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Weight
  { id:'pncWeight2', key:'pncWeight2', page:2,
    top:42.25, left:24.53, w:5.07, fs:6 },
  { id:'pncWeight3', key:'pncWeight3', page:2,
    top:42.25, left:30.88, w:5.07, fs:6 },
  { id:'pncWeight4', key:'pncWeight4', page:2,
    top:42.25, left:37.24, w:5.07, fs:6 },
  { id:'pncWeight5', key:'pncWeight5', page:2,
    top:42.25, left:43.59, w:5.07, fs:6 },
  { id:'pncWeight6', key:'pncWeight6', page:2,
    top:42.25, left:49.95, w:5.07, fs:6 },
  { id:'pncWeight7', key:'pncWeight7', page:2,
    top:42.25, left:56.31, w:5.07, fs:6 },
  { id:'pncWeight8', key:'pncWeight8', page:2,
    top:42.25, left:62.66, w:5.07, fs:6 },
  { id:'pncWeight9', key:'pncWeight9', page:2,
    top:42.25, left:69.02, w:5.07, fs:6 },
  { id:'pncWeight10', key:'pncWeight10', page:2,
    top:42.25, left:75.38, w:5.07, fs:6 },
  { id:'pncWeight11', key:'pncWeight11', page:2,
    top:42.25, left:81.72, w:5.07, fs:6 },
  { id:'pncWeight12', key:'pncWeight12', page:2,
    top:42.25, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Cardiac Rate
  { id:'pncCr2', key:'pncCr2', page:2,
    top:43.6, left:24.53, w:5.07, fs:6 },
  { id:'pncCr3', key:'pncCr3', page:2,
    top:43.6, left:30.88, w:5.07, fs:6 },
  { id:'pncCr4', key:'pncCr4', page:2,
    top:43.6, left:37.24, w:5.07, fs:6 },
  { id:'pncCr5', key:'pncCr5', page:2,
    top:43.6, left:43.59, w:5.07, fs:6 },
  { id:'pncCr6', key:'pncCr6', page:2,
    top:43.6, left:49.95, w:5.07, fs:6 },
  { id:'pncCr7', key:'pncCr7', page:2,
    top:43.6, left:56.31, w:5.07, fs:6 },
  { id:'pncCr8', key:'pncCr8', page:2,
    top:43.6, left:62.66, w:5.07, fs:6 },
  { id:'pncCr9', key:'pncCr9', page:2,
    top:43.6, left:69.02, w:5.07, fs:6 },
  { id:'pncCr10', key:'pncCr10', page:2,
    top:43.6, left:75.38, w:5.07, fs:6 },
  { id:'pncCr11', key:'pncCr11', page:2,
    top:43.6, left:81.72, w:5.07, fs:6 },
  { id:'pncCr12', key:'pncCr12', page:2,
    top:43.6, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Respiratory Rate
  { id:'pncRr2', key:'pncRr2', page:2,
    top:44.94, left:24.53, w:5.07, fs:6 },
  { id:'pncRr3', key:'pncRr3', page:2,
    top:44.94, left:30.88, w:5.07, fs:6 },
  { id:'pncRr4', key:'pncRr4', page:2,
    top:44.94, left:37.24, w:5.07, fs:6 },
  { id:'pncRr5', key:'pncRr5', page:2,
    top:44.94, left:43.59, w:5.07, fs:6 },
  { id:'pncRr6', key:'pncRr6', page:2,
    top:44.94, left:49.95, w:5.07, fs:6 },
  { id:'pncRr7', key:'pncRr7', page:2,
    top:44.94, left:56.31, w:5.07, fs:6 },
  { id:'pncRr8', key:'pncRr8', page:2,
    top:44.94, left:62.66, w:5.07, fs:6 },
  { id:'pncRr9', key:'pncRr9', page:2,
    top:44.94, left:69.02, w:5.07, fs:6 },
  { id:'pncRr10', key:'pncRr10', page:2,
    top:44.94, left:75.38, w:5.07, fs:6 },
  { id:'pncRr11', key:'pncRr11', page:2,
    top:44.94, left:81.72, w:5.07, fs:6 },
  { id:'pncRr12', key:'pncRr12', page:2,
    top:44.94, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Blood Pressure
  { id:'pncBp2', key:'pncBp2', page:2,
    top:46.29, left:24.53, w:5.07, fs:6 },
  { id:'pncBp3', key:'pncBp3', page:2,
    top:46.29, left:30.88, w:5.07, fs:6 },
  { id:'pncBp4', key:'pncBp4', page:2,
    top:46.29, left:37.24, w:5.07, fs:6 },
  { id:'pncBp5', key:'pncBp5', page:2,
    top:46.29, left:43.59, w:5.07, fs:6 },
  { id:'pncBp6', key:'pncBp6', page:2,
    top:46.29, left:49.95, w:5.07, fs:6 },
  { id:'pncBp7', key:'pncBp7', page:2,
    top:46.29, left:56.31, w:5.07, fs:6 },
  { id:'pncBp8', key:'pncBp8', page:2,
    top:46.29, left:62.66, w:5.07, fs:6 },
  { id:'pncBp9', key:'pncBp9', page:2,
    top:46.29, left:69.02, w:5.07, fs:6 },
  { id:'pncBp10', key:'pncBp10', page:2,
    top:46.29, left:75.38, w:5.07, fs:6 },
  { id:'pncBp11', key:'pncBp11', page:2,
    top:46.29, left:81.72, w:5.07, fs:6 },
  { id:'pncBp12', key:'pncBp12', page:2,
    top:46.29, left:88.07, w:5.07, fs:6 },

  // Follow-up Prenatal Consultation grid — Temperature
  { id:'pncTemp2', key:'pncTemp2', page:2,
    top:47.64, left:24.53, w:5.07, fs:6 },
  { id:'pncTemp3', key:'pncTemp3', page:2,
    top:47.64, left:30.88, w:5.07, fs:6 },
  { id:'pncTemp4', key:'pncTemp4', page:2,
    top:47.64, left:37.24, w:5.07, fs:6 },
  { id:'pncTemp5', key:'pncTemp5', page:2,
    top:47.64, left:43.59, w:5.07, fs:6 },
  { id:'pncTemp6', key:'pncTemp6', page:2,
    top:47.64, left:49.95, w:5.07, fs:6 },
  { id:'pncTemp7', key:'pncTemp7', page:2,
    top:47.64, left:56.31, w:5.07, fs:6 },
  { id:'pncTemp8', key:'pncTemp8', page:2,
    top:47.64, left:62.66, w:5.07, fs:6 },
  { id:'pncTemp9', key:'pncTemp9', page:2,
    top:47.64, left:69.02, w:5.07, fs:6 },
  { id:'pncTemp10', key:'pncTemp10', page:2,
    top:47.64, left:75.38, w:5.07, fs:6 },
  { id:'pncTemp11', key:'pncTemp11', page:2,
    top:47.64, left:81.72, w:5.07, fs:6 },
  { id:'pncTemp12', key:'pncTemp12', page:2,
    top:47.64, left:88.07, w:5.07, fs:6 },

  // 8. Date and Time of Delivery
  { id:'deliveryDateMM', key:'deliveryDate', page:2,
    top:52.23, left:31.58, w:2.94, fs:8, dateComponent:'MM' },
  { id:'deliveryDateDD', key:'deliveryDate', page:2,
    top:52.23, left:36.54, w:2.94, fs:8, dateComponent:'DD' },
  { id:'deliveryDateYYYY', key:'deliveryDate', page:2,
    top:52.23, left:41.49, w:5.75, fs:8, dateComponent:'YYYY' },
  { id:'deliveryTimeAM', key:'deliveryTime', page:2,
    top:52.23, left:54.9, w:2.94, fs:7, timeComponent:'AM' },
  { id:'deliveryTimePM', key:'deliveryTime', page:2,
    top:52.23, left:60.54, w:2.94, fs:7, timeComponent:'PM' },

  // 9. Maternal Outcome
  { id:'obstetricIndex', key:'obstetricIndex', page:2,
    top:55.94, left:21.06, w:7.77, fs:7 },
  { id:'pregnancyUterineAOG', key:'pregnancyUterineAOG', page:2,
    top:55.94, left:39.41, w:17.66, fs:7 },
  { id:'mannerOfDelivery2', key:'mannerOfDelivery', page:2,
    top:55.94, left:58.47, w:16.96, fs:7 },
  { id:'presentation', key:'presentation', page:2,
    top:55.94, left:76.85, w:16.97, fs:7 },

  // 10. Birth Outcome
  { id:'fetalOutcome2', key:'fetalOutcome', page:2,
    top:58.95, left:21.06, w:16.96, fs:7 },
  { id:'babySex2', key:'babySex', page:2,
    top:58.95, left:39.41, w:17.66, fs:7 },
  { id:'birthWeight2', key:'birthWeight', page:2,
    top:58.95, left:58.47, w:16.96, fs:7 },
  { id:'apgarScore2', key:'apgarScore', page:2,
    top:58.95, left:76.85, w:16.97, fs:7 },

  // 11. Scheduled Postpartum follow-up consultation
  { id:'postpartumFollowupMM', key:'postpartumFollowupDate', page:2,
    top:61.75, left:54.9, w:2.94, fs:8, dateComponent:'MM' },
  { id:'postpartumFollowupDD', key:'postpartumFollowupDate', page:2,
    top:61.75, left:59.84, w:2.94, fs:8, dateComponent:'DD' },
  { id:'postpartumFollowupYYYY', key:'postpartumFollowupDate', page:2,
    top:61.75, left:64.77, w:5.77, fs:8, dateComponent:'YYYY' },

  // 12. Date and Time of Discharge (same underlying data as CF3 page 1)
  { id:'dischargeMM2', key:'dateDischargeMM', page:2,
    top:64.0, left:31.58, w:2.94, fs:8, computed:'dateDischargeMM' },
  { id:'dischargeDD2', key:'dateDischargeDD', page:2,
    top:64.0, left:36.54, w:2.94, fs:8, computed:'dateDischargeDD' },
  { id:'dischargeYYYY2', key:'dateDischargeYYYY', page:2,
    top:64.0, left:41.49, w:5.75, fs:8, computed:'dateDischargeYYYY' },
  { id:'dischargeTimeAM2', key:'timeDischargeAM', page:2,
    top:64.0, left:55.6, w:2.94, fs:7, computed:'timeDischargeAM' },
  { id:'dischargeTimePM2', key:'timeDischargePM', page:2,
    top:64.0, left:61.24, w:2.94, fs:7, computed:'timeDischargePM' },

  // Perineal wound care
  { id:'ppPerinealDone', key:'ppPerinealDone', page:2,
    top:70.26, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppPerinealRemarks', key:'ppPerinealRemarks', page:2,
    top:70.26, left:57.8, w:36.0, fs:7 },

  // Signs of Maternal Postpartum Complications
  { id:'ppComplicationsDone', key:'ppComplicationsDone', page:2,
    top:71.61, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppComplicationsRemarks', key:'ppComplicationsRemarks', page:2,
    top:71.61, left:57.8, w:36.0, fs:7 },

  // Breastfeeding and Nutrition
  { id:'ppBreastfeedingDone', key:'ppBreastfeedingDone', page:2,
    top:74.89, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppBreastfeedingRemarks', key:'ppBreastfeedingRemarks', page:2,
    top:74.89, left:57.8, w:36.0, fs:7 },

  // Family Planning
  { id:'ppFamilyPlanningDone', key:'ppFamilyPlanningDone', page:2,
    top:75.65, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppFamilyPlanningRemarks', key:'ppFamilyPlanningRemarks', page:2,
    top:75.65, left:57.8, w:36.0, fs:7 },

  // Provided family planning service to patient
  { id:'ppFPServiceDone', key:'ppFPServiceDone', page:2,
    top:76.98, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppFPServiceRemarks', key:'ppFPServiceRemarks', page:2,
    top:76.98, left:57.8, w:36.0, fs:7 },

  // Referred to partner physician for Voluntary Surgical Sterilization
  { id:'ppReferredVSSDone', key:'ppReferredVSSDone', page:2,
    top:78.33, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppReferredVSSRemarks', key:'ppReferredVSSRemarks', page:2,
    top:78.33, left:57.8, w:36.0, fs:7 },

  // Schedule the next postpartum follow-up
  { id:'ppScheduleNextDone', key:'ppScheduleNextDone', page:2,
    top:79.67, left:54.9, w:1.6, fs:9, checkbox:true },
  { id:'ppScheduleNextRemarks', key:'ppScheduleNextRemarks', page:2,
    top:79.67, left:57.8, w:36.0, fs:7 },

  // 19. Certification of Attending Physician/Midwife
  { id:'attendingPhysicianName', key:'attendingPhysicianName', page:2,
    top:86.79, left:9.05, w:36.03, fs:8 },
  { id:'dateSignedMM', key:'dateSigned', page:2,
    top:87.32, left:58.42, w:2.94, fs:8, dateComponent:'MM' },
  { id:'dateSignedDD', key:'dateSigned', page:2,
    top:87.32, left:63.33, w:2.94, fs:8, dateComponent:'DD' },
  { id:'dateSignedYYYY', key:'dateSigned', page:2,
    top:87.32, left:68.3, w:5.77, fs:8, dateComponent:'YYYY' },
];
