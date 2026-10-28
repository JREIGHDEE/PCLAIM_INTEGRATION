/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – CF2 (612×936 pt)
   top/left are % of rendered page (0–100).
   Coordinates derived from actual PDF text/rect extraction
   (page.get_drawings() + get_text('words') via PyMuPDF).
   PAN/date/time fields use the generic `digit` resolver (see
   pdf-overlay.js resolveOverlayFieldValue) to place one character
   per printed digit box; disposition/accommodation use `checkbox`.
   Tops were moved onto the exporter's baseline (top + 6pt) the same
   way CSF and PMRF were in 58a4a3a: 6pt - 0.13em higher each.
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF2 = [
  // 1. PhilHealth Accreditation Number (PAN) of HCI — 9 digit boxes
  { id:'hciPANc1', key:'hciPANc1', page:1, top:20.898, left:53.962, w:2.006, fs:8, digit:0, digitKey:'hciPAN', center:true },
  { id:'hciPANc2', key:'hciPANc2', page:1, top:20.898, left:55.971, w:2.006, fs:8, digit:1, digitKey:'hciPAN', center:true },
  { id:'hciPANc3', key:'hciPANc3', page:1, top:20.898, left:57.972, w:2.006, fs:8, digit:2, digitKey:'hciPAN', center:true },
  { id:'hciPANc4', key:'hciPANc4', page:1, top:20.898, left:59.981, w:2.006, fs:8, digit:3, digitKey:'hciPAN', center:true },
  { id:'hciPANc5', key:'hciPANc5', page:1, top:20.898, left:61.982, w:2.006, fs:8, digit:4, digitKey:'hciPAN', center:true },
  { id:'hciPANc6', key:'hciPANc6', page:1, top:20.898, left:63.992, w:2.006, fs:8, digit:5, digitKey:'hciPAN', center:true },
  { id:'hciPANc7', key:'hciPANc7', page:1, top:20.898, left:65.993, w:2.006, fs:8, digit:6, digitKey:'hciPAN', center:true },
  { id:'hciPANc8', key:'hciPANc8', page:1, top:20.898, left:68.002,  w:2.006, fs:8, digit:7, digitKey:'hciPAN', center:true },
  { id:'hciPANc9', key:'hciPANc9', page:1, top:20.898, left:70.003,  w:2.006, fs:8, digit:8, digitKey:'hciPAN', center:true },

  // 2. Name of Health Care Institution
  { id:'hciName', key:'hciName', page:1, top:22.647, left:28.44, w:67.83, fs:8 },

  // 3. Address
  { id:'hciStreet',   key:'hciStreet',   page:1, top:24.38, left:13.27, w:33.64, fs:8, center:true },
  { id:'hciCity',     key:'hciCity',     page:1, top:24.38, left:48.42, w:23.55, fs:8, center:true },
  { id:'hciProvince', key:'hciProvince', page:1, top:24.38, left:73.83, w:22.43, fs:8, center:true },

  // PART II — 1. Name of Patient
  { id:'patientLastName',   key:'patientLastName',   page:1, top:29.37, left:20.399,  w:17.946, fs:8, center:true },
  { id:'patientFirstName',  key:'patientFirstName',  page:1, top:29.37, left:40.288, w:19.627, fs:8, center:true },
  { id:'patientNameExt',    key:'patientNameExt',    page:1, top:29.37, left:61.427, w:13.462, fs:8, center:true },
  { id:'patientMiddleName', key:'patientMiddleName', page:1, top:29.498, left:76.821, w:19.627, fs:8, center:true },

  // Was patient referred by another HCI? (Yes/No checkbox)
  { id:'referredByHCINo', key:'referredByHCI', page:1, top:35.551, left:5.311, w:2.006, fs:9, checkbox:true, checkValue:'No', center:true },
  { id:'referredByHCIYes', key:'referredByHCI', page:1, top:35.551, left:11.488, w:2.006, fs:9, checkbox:true, checkValue:'Yes', center:true },
  { id:'referralHciName',  key:'referralHciName',  page:1, top:35.361, left:18.37, w:24.10, fs:7 },
  { id:'referralStreet',   key:'referralStreet',   page:1, top:35.361, left:44.35, w:18.51, fs:7 },
  { id:'referralCity',     key:'referralCity',     page:1, top:35.361, left:64.67, w:10.67, fs:7 },
  { id:'referralProvince', key:'referralProvince', page:1, top:35.405, left:76.81, w:11.78, fs:7 },
  { id:'referralZip',      key:'referralZip',      page:1, top:35.405, left:90.11, w:6.18,  fs:7 },

  // 3. Confinement Period — a. Date Admitted (8 digits mm/dd/yyyy) + b. Time Admitted (4 digits hh:mm + AM/PM)
  { id:'dateAdmittedD1', key:'dateAdmittedD1', page:1, top:38.681, left:32.351, w:2.006, fs:7, digit:0, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD2', key:'dateAdmittedD2', page:1, top:38.681, left:34.363, w:2.006, fs:7, digit:1, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD3', key:'dateAdmittedD3', page:1, top:38.681, left:37.533, w:2.006, fs:7, digit:2, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD4', key:'dateAdmittedD4', page:1, top:38.681, left:39.545, w:2.006, fs:7, digit:3, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD5', key:'dateAdmittedD5', page:1, top:38.681, left:42.709, w:2.006, fs:7, digit:4, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD6', key:'dateAdmittedD6', page:1, top:38.681, left:44.721, w:2.006, fs:7, digit:5, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD7', key:'dateAdmittedD7', page:1, top:38.681, left:46.728, w:2.006, fs:7, digit:6, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'dateAdmittedD8', key:'dateAdmittedD8', page:1, top:38.681, left:48.74, w:2.006, fs:7, digit:7, digitKey:'dateAdmitted', digitOrder:'mmddyyyy', center:true },
  { id:'timeAdmittedD1', key:'timeAdmittedD1', page:1, top:38.667, left:63.944, w:2.006, fs:7, digit:0, digitKey:'timeAdmitted', center:true },
  { id:'timeAdmittedD2', key:'timeAdmittedD2', page:1, top:38.667, left:65.956, w:2.006, fs:7, digit:1, digitKey:'timeAdmitted', center:true },
  { id:'timeAdmittedD3', key:'timeAdmittedD3', page:1, top:38.667, left:69.125, w:2.006, fs:7, digit:2, digitKey:'timeAdmitted', center:true },
  { id:'timeAdmittedD4', key:'timeAdmittedD4', page:1, top:38.667, left:71.137, w:2.006, fs:7, digit:3, digitKey:'timeAdmitted', center:true },
  { id:'timeAdmittedAM', key:'timeAdmitted', page:1, top:38.822, left:76.979, w:2.006, fs:8, amPmCheck:'AM', center:true },
  { id:'timeAdmittedPM', key:'timeAdmitted', page:1, top:38.822, left:83.85, w:2.006, fs:8, amPmCheck:'PM', center:true },

  // c. Date Discharge (8 digits) + d. Time Discharge (4 digits + AM/PM)
  { id:'dateDischargeD1', key:'dateDischargeD1', page:1, top:40.372, left:32.351, w:2.006, fs:7, digit:0, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD2', key:'dateDischargeD2', page:1, top:40.372, left:34.363, w:2.006, fs:7, digit:1, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD3', key:'dateDischargeD3', page:1, top:40.372, left:37.533, w:2.006, fs:7, digit:2, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD4', key:'dateDischargeD4', page:1, top:40.372, left:39.545, w:2.006, fs:7, digit:3, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD5', key:'dateDischargeD5', page:1, top:40.372, left:42.709, w:2.006, fs:7, digit:4, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD6', key:'dateDischargeD6', page:1, top:40.372, left:44.721, w:2.006, fs:7, digit:5, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD7', key:'dateDischargeD7', page:1, top:40.372, left:46.728, w:2.006, fs:7, digit:6, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'dateDischargeD8', key:'dateDischargeD8', page:1, top:40.372, left:48.74, w:2.006, fs:7, digit:7, digitKey:'dateDischarge', digitOrder:'mmddyyyy', center:true },
  { id:'timeDischargeD1', key:'timeDischargeD1', page:1, top:40.388, left:63.944, w:2.006, fs:7, digit:0, digitKey:'timeDischarge', center:true },
  { id:'timeDischargeD2', key:'timeDischargeD2', page:1, top:40.388, left:65.956, w:2.006, fs:7, digit:1, digitKey:'timeDischarge', center:true },
  { id:'timeDischargeD3', key:'timeDischargeD3', page:1, top:40.388, left:69.125, w:2.006, fs:7, digit:2, digitKey:'timeDischarge', center:true },
  { id:'timeDischargeD4', key:'timeDischargeD4', page:1, top:40.388, left:71.137, w:2.006, fs:7, digit:3, digitKey:'timeDischarge', center:true },
  { id:'timeDischargeAM', key:'timeDischarge', page:1, top:40.442, left:76.979, w:2.006, fs:8, amPmCheck:'AM', center:true },
  { id:'timeDischargePM', key:'timeDischarge', page:1, top:40.442, left:83.85, w:2.006, fs:8, amPmCheck:'PM', center:true },

  // 4. Patient Disposition — checkboxes (shares the "disposition" select)
  { id:'dispImproved',   key:'disposition', page:1, top:43.852, left:5.311,  w:2.006, fs:8, checkbox:true, checkValue:'Improved', center:true },
  { id:'dispRecovered',  key:'disposition', page:1, top:45.46, left:5.311,  w:2.006, fs:8, checkbox:true, checkValue:'Recovered', center:true },
  { id:'dispHAMA',       key:'disposition', page:1, top:47.068, left:5.311,  w:2.006, fs:8, checkbox:true, checkValue:'HAMA', center:true },
  { id:'dispAbsconded',  key:'disposition', page:1, top:48.675, left:5.311,  w:2.006, fs:8, checkbox:true, checkValue:'Absconded', center:true },
  { id:'dispExpired',    key:'disposition', page:1, top:43.852, left:31.12, w:2.006, fs:8, checkbox:true, checkValue:'Expired', center:true },
  { id:'dispTransferred',key:'disposition', page:1, top:45.46, left:31.12, w:2.006, fs:8, checkbox:true, checkValue:'Transferred', center:true },

  // 5. Type of Accomodation — checkboxes
  { id:'accomPrivate',    key:'accommodation', page:1, top:50.326, left:23.532, w:2.006, fs:8, checkbox:true, checkValue:'Private', center:true },
  { id:'accomNonPrivate', key:'accommodation', page:1, top:50.326, left:32.429, w:2.006, fs:8, checkbox:true, checkValue:'Non-Private', center:true },

  // 6. Admission Diagnosis/es
  // In the middle of the space between its heading and section 7's border;
  // a long one takes a second line that still clears the border.
  { id:'admissionDx', key:'admissionDx', page:1, top:53.793, left:4.58, w:88, fs:8, wrap:true, lines:2, lh:8 },

  // Discharge Diagnosis table (7. Discharge Diagnosis/es)
  // Diagnosis A
  { id:'dxADiagnosis',     key:'dxADiagnosis',     page:1, top:59.149, left:6.96,  w:11.55, fs:7, wrap:true, lines:3, lh:13.5, center:true },
  { id:'dxAIcd10',         key:'dxAIcd10',         page:1, top:59.149, left:20.39, w:8.99,  fs:7, center:true },
  { id:'dxAProcI',         key:'dxAProcI',         page:1, top:59.149, left:32.81, w:18.59, fs:7, center:true },
  { id:'dxARvsI',          key:'dxARvsI',          page:1, top:59.149, left:53.30, w:9.62,  fs:7, center:true },
  { id:'dxADateI',         key:'dxADateI',         page:1, top:59.149, left:64.67, w:10.26, fs:7, computed:'dxADateI', center:true },
  { id:'dxALatILeft', key:'dxALatI', page:1, top:59.107, left:77.341, w:2.006, fs:8, checkbox:true, checkValue:'left', center:true },
  { id:'dxALatIRight', key:'dxALatI', page:1, top:59.107, left:83.156, w:2.006, fs:8, checkbox:true, checkValue:'right', center:true },
  { id:'dxALatIBoth', key:'dxALatI', page:1, top:59.107, left:89.549, w:2.006, fs:8, checkbox:true, checkValue:'both', center:true },
  { id:'dxAProcII',        key:'dxAProcII',        page:1, top:60.592, left:32.81, w:18.59, fs:7, center:true },
  { id:'dxARvsII',         key:'dxARvsII',         page:1, top:60.592, left:53.30, w:9.62,  fs:7, center:true },
  { id:'dxADateII',        key:'dxADateII',        page:1, top:60.592, left:64.67, w:10.26, fs:7, computed:'dxADateII', center:true },
  { id:'dxALatIILeft', key:'dxALatII', page:1, top:60.553, left:77.341, w:2.006, fs:8, checkbox:true, checkValue:'left', center:true },
  { id:'dxALatIIRight', key:'dxALatII', page:1, top:60.553, left:83.156, w:2.006, fs:8, checkbox:true, checkValue:'right', center:true },
  { id:'dxALatIIBoth', key:'dxALatII', page:1, top:60.553, left:89.549, w:2.006, fs:8, checkbox:true, checkValue:'both', center:true },
  { id:'dxAProcIII',       key:'dxAProcIII',       page:1, top:62.034,  left:32.81, w:18.59, fs:7, center:true },
  { id:'dxARvsIII',        key:'dxARvsIII',        page:1, top:62.034,  left:53.30, w:9.62,  fs:7, center:true },
  { id:'dxADateIII',       key:'dxADateIII',       page:1, top:62.034,  left:64.67, w:10.26, fs:7, computed:'dxADateIII', center:true },
  { id:'dxALatIIILeft', key:'dxALatIII', page:1, top:61.992, left:77.341, w:2.006, fs:8, checkbox:true, checkValue:'left', center:true },
  { id:'dxALatIIIRight', key:'dxALatIII', page:1, top:61.992, left:83.156, w:2.006, fs:8, checkbox:true, checkValue:'right', center:true },
  { id:'dxALatIIIBoth', key:'dxALatIII', page:1, top:61.992, left:89.549, w:2.006, fs:8, checkbox:true, checkValue:'both', center:true },
  // Diagnosis B
  { id:'dxBDiagnosis',     key:'dxBDiagnosis',     page:1, top:63.477, left:7.01,  w:11.54, fs:7, wrap:true, lines:3, lh:13.5, center:true },
  { id:'dxBIcd10',         key:'dxBIcd10',         page:1, top:63.476, left:20.39, w:8.99,  fs:7, center:true },
  { id:'dxBProcI',         key:'dxBProcI',         page:1, top:63.476, left:32.81, w:18.59, fs:7, center:true },
  { id:'dxBRvsI',          key:'dxBRvsI',          page:1, top:63.476, left:53.30, w:9.62,  fs:7, center:true },
  { id:'dxBDateI',         key:'dxBDateI',         page:1, top:63.476, left:64.67, w:10.26, fs:7, computed:'dxBDateI', center:true },
  { id:'dxBLatILeft', key:'dxBLatI', page:1, top:63.438, left:77.341, w:2.006, fs:8, checkbox:true, checkValue:'left', center:true },
  { id:'dxBLatIRight', key:'dxBLatI', page:1, top:63.438, left:83.156, w:2.006, fs:8, checkbox:true, checkValue:'right', center:true },
  { id:'dxBLatIBoth', key:'dxBLatI', page:1, top:63.438, left:89.549, w:2.006, fs:8, checkbox:true, checkValue:'both', center:true },
  { id:'dxBProcII',        key:'dxBProcII',        page:1, top:64.919, left:32.81, w:18.59, fs:7, center:true },
  { id:'dxBRvsII',         key:'dxBRvsII',         page:1, top:64.919, left:53.30, w:9.62,  fs:7, center:true },
  { id:'dxBDateII',        key:'dxBDateII',        page:1, top:64.919, left:64.67, w:10.26, fs:7, computed:'dxBDateII', center:true },
  { id:'dxBLatIILeft', key:'dxBLatII', page:1, top:64.877, left:77.341, w:2.006, fs:8, checkbox:true, checkValue:'left', center:true },
  { id:'dxBLatIIRight', key:'dxBLatII', page:1, top:64.877, left:83.156, w:2.006, fs:8, checkbox:true, checkValue:'right', center:true },
  { id:'dxBLatIIBoth', key:'dxBLatII', page:1, top:64.877, left:89.549, w:2.006, fs:8, checkbox:true, checkValue:'both', center:true },
  { id:'dxBProcIII',       key:'dxBProcIII',       page:1, top:66.64, left:32.81, w:18.59, fs:7, center:true },
  { id:'dxBRvsIII',        key:'dxBRvsIII',        page:1, top:66.64, left:53.30, w:9.62,  fs:7, center:true },
  { id:'dxBDateIII',       key:'dxBDateIII',       page:1, top:66.64, left:64.67, w:10.26, fs:7, computed:'dxBDateIII', center:true },
  { id:'dxBLatIIILeft', key:'dxBLatIII', page:1, top:66.307, left:77.341, w:2.006, fs:8, checkbox:true, checkValue:'left', center:true },
  { id:'dxBLatIIIRight', key:'dxBLatIII', page:1, top:66.307, left:83.156, w:2.006, fs:8, checkbox:true, checkValue:'right', center:true },
  { id:'dxBLatIIIBoth', key:'dxBLatIII', page:1, top:66.307, left:89.549, w:2.006, fs:8, checkbox:true, checkValue:'both', center:true },

  // ═══ PAGE 2 ═══

  // Item 10 – Accreditation/Signature/Date Signed + Co-pay (3 rows)
  { id:'cf2Prof1AccredNoD1', key:'cf2Prof1AccredNoD1', page:2, top:7.22, left:16.292, w:2.006, fs:7, digit:0, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD2', key:'cf2Prof1AccredNoD2', page:2, top:7.22, left:18.303, w:2.006, fs:7, digit:1, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD3', key:'cf2Prof1AccredNoD3', page:2, top:7.22, left:20.31, w:2.006, fs:7, digit:2, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD4', key:'cf2Prof1AccredNoD4', page:2, top:7.22, left:22.322, w:2.006, fs:7, digit:3, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD5', key:'cf2Prof1AccredNoD5', page:2, top:7.22, left:25.486, w:2.006, fs:7, digit:4, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD6', key:'cf2Prof1AccredNoD6', page:2, top:7.22, left:27.498, w:2.006, fs:7, digit:5, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD7', key:'cf2Prof1AccredNoD7', page:2, top:7.22, left:29.505, w:2.006, fs:7, digit:6, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD8', key:'cf2Prof1AccredNoD8', page:2, top:7.22, left:31.517, w:2.006, fs:7, digit:7, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD9', key:'cf2Prof1AccredNoD9', page:2, top:7.22, left:33.524, w:2.006, fs:7, digit:8, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD10', key:'cf2Prof1AccredNoD10', page:2, top:7.22, left:35.535, w:2.006, fs:7, digit:9, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD11', key:'cf2Prof1AccredNoD11', page:2, top:7.22, left:37.542, w:2.006, fs:7, digit:10, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1AccredNoD12', key:'cf2Prof1AccredNoD12', page:2, top:7.22, left:40.714, w:2.006, fs:7, digit:11, digitKey:'cf2Prof1AccredNo', center:true },
  { id:'cf2Prof1Name',     key:'cf2Prof1Name',     page:2, top:9.156, left:9.346, w:38.444, fs:7, center:true },
  { id:'cf2Prof1DateSignedD1', key:'cf2Prof1DateSignedD1', page:2, top:11.976, left:20.504, w:2.006, fs:7, digit:0, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD2', key:'cf2Prof1DateSignedD2', page:2, top:11.976, left:22.516, w:2.006, fs:7, digit:1, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD3', key:'cf2Prof1DateSignedD3', page:2, top:11.976, left:25.686, w:2.006, fs:7, digit:2, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD4', key:'cf2Prof1DateSignedD4', page:2, top:11.976, left:27.698, w:2.006, fs:7, digit:3, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD5', key:'cf2Prof1DateSignedD5', page:2, top:11.976, left:30.862, w:2.006, fs:7, digit:4, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD6', key:'cf2Prof1DateSignedD6', page:2, top:11.976, left:32.874, w:2.006, fs:7, digit:5, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD7', key:'cf2Prof1DateSignedD7', page:2, top:11.976, left:34.881, w:2.006, fs:7, digit:6, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1DateSignedD8', key:'cf2Prof1DateSignedD8', page:2, top:11.976, left:36.893, w:2.006, fs:7, digit:7, digitKey:'cf2Prof1DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof1CopayNo', key:'cf2Prof1Copay', page:2, top:9.179, left:54.335, w:2.006, fs:8, checkbox:true, checkValue:'No', center:true },
  { id:'cf2Prof1CopayYes', key:'cf2Prof1Copay', page:2, top:10.718, left:54.335, w:2.006, fs:8, checkbox:true, checkValue:'Yes', center:true },
  { id:'cf2Prof1CopayAmount', key:'cf2Prof1CopayAmount', page:2, top:10.752, left:80.67, w:14.1, fs:7 },

  { id:'cf2Prof2AccredNoD1', key:'cf2Prof2AccredNoD1', page:2, top:14.455, left:16.292, w:2.006, fs:7, digit:0, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD2', key:'cf2Prof2AccredNoD2', page:2, top:14.455, left:18.303, w:2.006, fs:7, digit:1, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD3', key:'cf2Prof2AccredNoD3', page:2, top:14.455, left:20.31, w:2.006, fs:7, digit:2, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD4', key:'cf2Prof2AccredNoD4', page:2, top:14.455, left:22.322, w:2.006, fs:7, digit:3, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD5', key:'cf2Prof2AccredNoD5', page:2, top:14.455, left:25.486, w:2.006, fs:7, digit:4, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD6', key:'cf2Prof2AccredNoD6', page:2, top:14.455, left:27.498, w:2.006, fs:7, digit:5, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD7', key:'cf2Prof2AccredNoD7', page:2, top:14.455, left:29.505, w:2.006, fs:7, digit:6, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD8', key:'cf2Prof2AccredNoD8', page:2, top:14.455, left:31.517, w:2.006, fs:7, digit:7, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD9', key:'cf2Prof2AccredNoD9', page:2, top:14.455, left:33.524, w:2.006, fs:7, digit:8, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD10', key:'cf2Prof2AccredNoD10', page:2, top:14.455, left:35.535, w:2.006, fs:7, digit:9, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD11', key:'cf2Prof2AccredNoD11', page:2, top:14.455, left:37.542, w:2.006, fs:7, digit:10, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2AccredNoD12', key:'cf2Prof2AccredNoD12', page:2, top:14.455, left:40.714, w:2.006, fs:7, digit:11, digitKey:'cf2Prof2AccredNo', center:true },
  { id:'cf2Prof2Name',     key:'cf2Prof2Name',     page:2, top:15.855, left:9.346, w:38.444, fs:7, center:true },
  { id:'cf2Prof2DateSignedD1', key:'cf2Prof2DateSignedD1', page:2, top:18.539, left:20.504, w:2.006, fs:7, digit:0, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD2', key:'cf2Prof2DateSignedD2', page:2, top:18.539, left:22.516, w:2.006, fs:7, digit:1, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD3', key:'cf2Prof2DateSignedD3', page:2, top:18.539, left:25.686, w:2.006, fs:7, digit:2, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD4', key:'cf2Prof2DateSignedD4', page:2, top:18.539, left:27.698, w:2.006, fs:7, digit:3, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD5', key:'cf2Prof2DateSignedD5', page:2, top:18.539, left:30.862, w:2.006, fs:7, digit:4, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD6', key:'cf2Prof2DateSignedD6', page:2, top:18.539, left:32.874, w:2.006, fs:7, digit:5, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD7', key:'cf2Prof2DateSignedD7', page:2, top:18.539, left:34.881, w:2.006, fs:7, digit:6, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2DateSignedD8', key:'cf2Prof2DateSignedD8', page:2, top:18.539, left:36.893, w:2.006, fs:7, digit:7, digitKey:'cf2Prof2DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof2CopayNo', key:'cf2Prof2Copay', page:2, top:15.882, left:54.335, w:2.006, fs:8, checkbox:true, checkValue:'No', center:true },
  { id:'cf2Prof2CopayYes', key:'cf2Prof2Copay', page:2, top:17.421, left:54.335, w:2.006, fs:8, checkbox:true, checkValue:'Yes', center:true },
  { id:'cf2Prof2CopayAmount', key:'cf2Prof2CopayAmount', page:2, top:17.457, left:80.67, w:14.1, fs:7 },

  { id:'cf2Prof3AccredNoD1', key:'cf2Prof3AccredNoD1', page:2, top:21.008, left:16.292, w:2.006, fs:7, digit:0, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD2', key:'cf2Prof3AccredNoD2', page:2, top:21.008, left:18.303, w:2.006, fs:7, digit:1, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD3', key:'cf2Prof3AccredNoD3', page:2, top:21.008, left:20.31, w:2.006, fs:7, digit:2, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD4', key:'cf2Prof3AccredNoD4', page:2, top:21.008, left:22.322, w:2.006, fs:7, digit:3, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD5', key:'cf2Prof3AccredNoD5', page:2, top:21.008, left:25.486, w:2.006, fs:7, digit:4, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD6', key:'cf2Prof3AccredNoD6', page:2, top:21.008, left:27.498, w:2.006, fs:7, digit:5, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD7', key:'cf2Prof3AccredNoD7', page:2, top:21.008, left:29.505, w:2.006, fs:7, digit:6, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD8', key:'cf2Prof3AccredNoD8', page:2, top:21.008, left:31.517, w:2.006, fs:7, digit:7, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD9', key:'cf2Prof3AccredNoD9', page:2, top:21.008, left:33.524, w:2.006, fs:7, digit:8, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD10', key:'cf2Prof3AccredNoD10', page:2, top:21.008, left:35.535, w:2.006, fs:7, digit:9, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD11', key:'cf2Prof3AccredNoD11', page:2, top:21.008, left:37.542, w:2.006, fs:7, digit:10, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3AccredNoD12', key:'cf2Prof3AccredNoD12', page:2, top:21.008, left:40.714, w:2.006, fs:7, digit:11, digitKey:'cf2Prof3AccredNo', center:true },
  { id:'cf2Prof3Name',     key:'cf2Prof3Name',     page:2, top:22.447, left:9.346, w:38.444, fs:7, center:true },
  { id:'cf2Prof3DateSignedD1', key:'cf2Prof3DateSignedD1', page:2, top:25.102, left:20.504, w:2.006, fs:7, digit:0, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD2', key:'cf2Prof3DateSignedD2', page:2, top:25.102, left:22.516, w:2.006, fs:7, digit:1, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD3', key:'cf2Prof3DateSignedD3', page:2, top:25.102, left:25.686, w:2.006, fs:7, digit:2, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD4', key:'cf2Prof3DateSignedD4', page:2, top:25.102, left:27.698, w:2.006, fs:7, digit:3, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD5', key:'cf2Prof3DateSignedD5', page:2, top:25.102, left:30.862, w:2.006, fs:7, digit:4, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD6', key:'cf2Prof3DateSignedD6', page:2, top:25.102, left:32.874, w:2.006, fs:7, digit:5, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD7', key:'cf2Prof3DateSignedD7', page:2, top:25.102, left:34.881, w:2.006, fs:7, digit:6, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3DateSignedD8', key:'cf2Prof3DateSignedD8', page:2, top:25.102, left:36.893, w:2.006, fs:7, digit:7, digitKey:'cf2Prof3DateSigned', digitOrder:'mmddyyyy', center:true },
  { id:'cf2Prof3CopayNo', key:'cf2Prof3Copay', page:2, top:22.449, left:54.335, w:2.006, fs:8, checkbox:true, checkValue:'No', center:true },
  { id:'cf2Prof3CopayYes', key:'cf2Prof3Copay', page:2, top:23.988, left:54.335, w:2.006, fs:8, checkbox:true, checkValue:'Yes', center:true },
  { id:'cf2Prof3CopayAmount', key:'cf2Prof3CopayAmount', page:2, top:24.05, left:80.67, w:14.1, fs:7 },

  // Part III-B – Consent to Access Patient Record/s
  { id:'cf2PatientRepName', key:'cf2PatientRepName', page:2, top:77.344, left:5.31, w:39.085, fs:7, center:true },
  { id:'cf2PatientRepSignedDateD1', key:'cf2PatientRepSignedDateD1', page:2, top:80.564, left:20.504, w:2.006, fs:7, digit:0, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD2', key:'cf2PatientRepSignedDateD2', page:2, top:80.564, left:22.516, w:2.006, fs:7, digit:1, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD3', key:'cf2PatientRepSignedDateD3', page:2, top:80.564, left:25.686, w:2.006, fs:7, digit:2, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD4', key:'cf2PatientRepSignedDateD4', page:2, top:80.564, left:27.698, w:2.006, fs:7, digit:3, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD5', key:'cf2PatientRepSignedDateD5', page:2, top:80.564, left:30.862, w:2.006, fs:7, digit:4, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD6', key:'cf2PatientRepSignedDateD6', page:2, top:80.564, left:32.874, w:2.006, fs:7, digit:5, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD7', key:'cf2PatientRepSignedDateD7', page:2, top:80.564, left:34.881, w:2.006, fs:7, digit:6, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepSignedDateD8', key:'cf2PatientRepSignedDateD8', page:2, top:80.564, left:36.893, w:2.006, fs:7, digit:7, digitKey:'cf2PatientRepSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2PatientRepRelSpouse', key:'cf2PatientRepRelationship', page:2, top:83.518, left:26.161, w:1.504, fs:8, checkbox:true, checkValue:'Spouse', center:true },
  { id:'cf2PatientRepRelChild', key:'cf2PatientRepRelationship', page:2, top:83.518, left:33.584, w:1.504, fs:8, checkbox:true, checkValue:'Child', center:true },
  { id:'cf2PatientRepRelParent', key:'cf2PatientRepRelationship', page:2, top:83.518, left:40.428, w:1.504, fs:8, checkbox:true, checkValue:'Parent', center:true },
  { id:'cf2PatientRepRelSibling', key:'cf2PatientRepRelationship', page:2, top:84.721, left:26.161, w:1.504, fs:8, checkbox:true, checkValue:'Sibling', center:true },
  { id:'cf2PatientRepRelOthers', key:'cf2PatientRepRelationship', page:2, top:84.721, left:33.584, w:1.504, fs:8, checkbox:true, checkValue:'Others', center:true },
  { id:'cf2PatientRepRelationshipOther', key:'cf2PatientRepRelationshipOther', page:2, top:84.577, left:44.23, w:12.17, fs:7 },
  { id:'cf2PatientReasonIncap', key:'cf2PatientReason', page:2, top:86.148, left:26.161, w:1.504, fs:8, checkbox:true, checkValue:'Incapacitated', center:true },
  { id:'cf2PatientReasonOther', key:'cf2PatientReason', page:2, top:87.362, left:26.161, w:1.504, fs:8, checkbox:true, checkValue:'Other', center:true },
  // Who signs: the same consent as CSF Part III, so the same answer.
  { id:'cf2PatientSignerPatient', key:'patientSignerType', page:2, top:86.228, left:58.335, w:1.504, fs:8, checkbox:true, checkValue:'Patient', center:true },
  { id:'cf2PatientSignerRep', key:'patientSignerType', page:2, top:87.432, left:58.335, w:1.504, fs:8, checkbox:true, checkValue:'Representative', center:true },
  { id:'cf2PatientReasonOtherText', key:'cf2PatientReasonOther', page:2, top:87.239, left:36.58, w:19.87, fs:7 },

  // Part IV – Certification of Consumption of Health Care Institution
  { id:'cf2ProviderRepName', key:'cf2ProviderRepName', page:2, top:94.419, left:5.31, w:33.32, fs:7, center:true },
  { id:'cf2ProviderCapacity', key:'cf2ProviderCapacity', page:2, top:94.419, left:40.288, w:26.915, fs:7, center:true },
  { id:'cf2ProviderSignedDateD1', key:'cf2ProviderSignedDateD1', page:2, top:94.507, left:76.806, w:2.006, fs:7, digit:0, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD2', key:'cf2ProviderSignedDateD2', page:2, top:94.507, left:78.818, w:2.006, fs:7, digit:1, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD3', key:'cf2ProviderSignedDateD3', page:2, top:94.507, left:81.987, w:2.006, fs:7, digit:2, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD4', key:'cf2ProviderSignedDateD4', page:2, top:94.507, left:83.999, w:2.006, fs:7, digit:3, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD5', key:'cf2ProviderSignedDateD5', page:2, top:94.507, left:87.164, w:2.006, fs:7, digit:4, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD6', key:'cf2ProviderSignedDateD6', page:2, top:94.507, left:89.176, w:2.006, fs:7, digit:5, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD7', key:'cf2ProviderSignedDateD7', page:2, top:94.507, left:91.182, w:2.006, fs:7, digit:6, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'cf2ProviderSignedDateD8', key:'cf2ProviderSignedDateD8', page:2, top:94.507, left:93.194, w:2.006, fs:7, digit:7, digitKey:'cf2ProviderSignedDate', digitOrder:'mmddyyyy', center:true },


  // Special procedures / packages — tick all that apply
  { id:'cf2Proc1', key:'cf2SpecialProcedures', page:1, top:71.283, left:6.824, w:2.006, fs:8, checkboxMulti:true, checkValue:'Hemodialysis', center:true },
  { id:'cf2Proc2', key:'cf2SpecialProcedures', page:1, top:71.283, left:51.942, w:2.006, fs:8, checkboxMulti:true, checkValue:'Blood Transfusion', center:true },
  { id:'cf2Proc3', key:'cf2SpecialProcedures', page:1, top:72.898, left:6.824, w:2.006, fs:8, checkboxMulti:true, checkValue:'Peritoneal Dialysis', center:true },
  { id:'cf2Proc4', key:'cf2SpecialProcedures', page:1, top:72.898, left:51.942, w:2.006, fs:8, checkboxMulti:true, checkValue:'Brachytherapy', center:true },
  { id:'cf2Proc5', key:'cf2SpecialProcedures', page:1, top:74.514, left:6.824, w:2.006, fs:8, checkboxMulti:true, checkValue:'Radiotherapy (LINAC)', center:true },
  { id:'cf2Proc6', key:'cf2SpecialProcedures', page:1, top:74.514, left:51.942, w:2.006, fs:8, checkboxMulti:true, checkValue:'Chemotherapy', center:true },
  { id:'cf2Proc7', key:'cf2SpecialProcedures', page:1, top:76.129, left:6.824, w:2.006, fs:8, checkboxMulti:true, checkValue:'Radiotherapy (COBALT)', center:true },
  { id:'cf2Proc8', key:'cf2SpecialProcedures', page:1, top:76.129, left:51.942, w:2.006, fs:8, checkboxMulti:true, checkValue:'Simple Debridement', center:true },
  // Each ticked procedure's dates, on the line beside it (app.js cf2ProcDetailN)
  { id:'cf2ProcDetail1', key:'cf2ProcDates1', computed:'cf2ProcDetail1', page:1, top:71.24, left:24.64, w:24.35, fs:7 },
  { id:'cf2ProcDetail2', key:'cf2ProcDates2', computed:'cf2ProcDetail2', page:1, top:71.24, left:69.13, w:24.35, fs:7 },
  { id:'cf2ProcDetail3', key:'cf2ProcDates3', computed:'cf2ProcDetail3', page:1, top:72.842, left:24.64, w:24.35, fs:7 },
  { id:'cf2ProcDetail4', key:'cf2ProcDates4', computed:'cf2ProcDetail4', page:1, top:72.842, left:69.13, w:24.35, fs:7 },
  { id:'cf2ProcDetail5', key:'cf2ProcDates5', computed:'cf2ProcDetail5', page:1, top:74.445, left:24.64, w:24.35, fs:7 },
  { id:'cf2ProcDetail6', key:'cf2ProcDates6', computed:'cf2ProcDetail6', page:1, top:74.445, left:69.13, w:24.35, fs:7 },
  { id:'cf2ProcDetail7', key:'cf2ProcDates7', computed:'cf2ProcDetail7', page:1, top:76.047, left:24.64, w:24.35, fs:7 },
  { id:'cf2ProcDetail8', key:'cf2ProcDates8', computed:'cf2ProcDetail8', page:1, top:76.047, left:69.13, w:24.35, fs:7 },

  // TB-DOTS package phase
  { id:'cf2TbIntensive', key:'cf2TbPhase', page:1, top:82.514, left:21.253, w:2.006, fs:8, checkbox:true, checkValue:'Intensive Phase', center:true },
  { id:'cf2TbMaintenance', key:'cf2TbPhase', page:1, top:82.514, left:36.841, w:2.006, fs:8, checkbox:true, checkValue:'Maintenance Phase', center:true },

  // Newborn care package — tick all that apply
  { id:'cf2Newborn1', key:'cf2NewbornCare', page:1, top:87.283, left:24.418, w:2.006, fs:8, checkboxMulti:true, checkValue:'Essential Newborn Care', center:true },
  { id:'cf2Newborn2', key:'cf2NewbornCare', page:1, top:87.283, left:39.889, w:2.006, fs:8, checkboxMulti:true, checkValue:'Newborn Hearing Screening Test', center:true },
  { id:'cf2Newborn3', key:'cf2NewbornCare', page:1, top:87.283, left:60.624, w:2.006, fs:8, checkboxMulti:true, checkValue:'Newborn Screening Test', center:true },
  // For Essential Newborn Care (check applicable boxes)
  { id:'cf2Enc1', key:'cf2EssentialNewbornCare', page:1, top:90.572, left:6.824, w:2.006, fs:8, checkboxMulti:true, checkValue:'Immediate drying of newborn', center:true },
  { id:'cf2Enc2', key:'cf2EssentialNewbornCare', page:1, top:90.572, left:26.602, w:2.006, fs:8, checkboxMulti:true, checkValue:'Timely cord clamping', center:true },
  { id:'cf2Enc3', key:'cf2EssentialNewbornCare', page:1, top:90.572, left:43.203, w:2.006, fs:8, checkboxMulti:true, checkValue:'Weighing of the newborn', center:true },
  { id:'cf2Enc4', key:'cf2EssentialNewbornCare', page:1, top:90.572, left:61.543, w:2.006, fs:8, checkboxMulti:true, checkValue:'BCG vaccination', center:true },
  { id:'cf2Enc5', key:'cf2EssentialNewbornCare', page:1, top:90.648, left:77.014, w:2.006, fs:8, checkboxMulti:true, checkValue:'Hepatitis B vaccination', center:true },
  { id:'cf2Enc6', key:'cf2EssentialNewbornCare', page:1, top:92.111, left:6.824, w:2.006, fs:8, checkboxMulti:true, checkValue:'Early skin-to-skin contact', center:true },
  { id:'cf2Enc7', key:'cf2EssentialNewbornCare', page:1, top:92.111, left:26.602, w:2.006, fs:8, checkboxMulti:true, checkValue:'Eye Prophylaxis', center:true },
  { id:'cf2Enc8', key:'cf2EssentialNewbornCare', page:1, top:92.111, left:43.203, w:2.006, fs:8, checkboxMulti:true, checkValue:'Vitamin K administration', center:true },
  { id:'cf2Enc9', key:'cf2EssentialNewbornCare', page:1, top:92.111, left:61.543, w:2.006, fs:8, checkboxMulti:true, checkValue:'Non-separation of mother/baby for early breastfeeding initiation', center:true },
];
