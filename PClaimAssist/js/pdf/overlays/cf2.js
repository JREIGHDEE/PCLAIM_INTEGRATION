/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – CF2 (612×936 pt)
   top/left are % of rendered page (0–100).
   Coordinates derived from actual PDF text/rect extraction.
   (NOTE: All top% values have been corrected using the 100-X rule)
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF2 = [
  // HCI Accreditation No (PAN)
  { id:'hciPAN',           key:'hciPAN',           page:1, top:23.5, left:32,  w:65, fs:8 },
  // HCI Name
  { id:'hciName',          key:'hciName',          page:1, top:25.2, left:6,   w:90, fs:8 },
  // HCI Address row
  { id:'hciStreet',        key:'hciStreet',        page:1, top:28.2, left:6,   w:44, fs:8 },
  { id:'hciCity',          key:'hciCity',          page:1, top:28.2, left:52,  w:24, fs:8 },
  { id:'hciProvince',      key:'hciProvince',      page:1, top:28.2, left:78,  w:19, fs:8 },
  // Patient name
  { id:'patientLastName',  key:'patientLastName',  page:1, top:33.2, left:6,   w:20, fs:8 },
  { id:'patientFirstName', key:'patientFirstName', page:1, top:33.2, left:28,  w:18, fs:8 },
  { id:'patientMiddleName',key:'patientMiddleName',page:1, top:33.2, left:47,  w:18, fs:8 },
  { id:'patientNameExt',   key:'patientNameExt',   page:1, top:33.2, left:67,  w:9,  fs:8 },
  // Date/Time Admitted
  { id:'dateAdmitted',     key:'dateAdmitted',     page:1, top:40.9, left:6,   w:32, fs:8, computed:'dateAdmitted' },
  { id:'timeAdmitted',     key:'timeAdmitted',     page:1, top:40.9, left:56,  w:24, fs:8, computed:'timeAdmittedStr' },
  // Date/Time Discharged
  { id:'dateDischarge',    key:'dateDischarge',    page:1, top:42.6, left:6,   w:32, fs:8, computed:'dateDischarge' },
  { id:'timeDischarge',    key:'timeDischarge',    page:1, top:42.6, left:56,  w:24, fs:8, computed:'timeDischargeStr' },
  // Disposition
  { id:'disposition',      key:'disposition',      page:1, top:45.2, left:6,   w:55, fs:8 },
  // Accommodation
  { id:'accommodation',    key:'accommodation',    page:1, top:45.2, left:64,  w:33, fs:8 },
  // Admission diagnosis
  { id:'admissionDx',      key:'admissionDx',      page:1, top:54.8, left:6,   w:91, fs:8 },
  // Discharge diagnosis
  { id:'dischargeDx',      key:'dischargeDx',      page:1, top:59.0, left:6,   w:91, fs:8 },
];
