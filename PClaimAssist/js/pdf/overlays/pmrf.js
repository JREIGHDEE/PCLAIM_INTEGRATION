/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – PMRF (594.75×841.5 pt)
   top/left are % of rendered page (0–100).
   Coordinates derived from actual PDF text/rect extraction.
   (NOTE: All top% values have been corrected using the 100-X rule)
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_PMRF = [
  // PIN row
  { id:'memberPIN',        key:'memberPIN',        page:1, top:20.8, left:3,   w:90, fs:9 },
  // Member name row
  { id:'memberLastName',   key:'memberLastName',   page:1, top:26.2, left:3,   w:11, fs:9 },
  { id:'memberFirstName',  key:'memberFirstName',  page:1, top:26.2, left:14.4,w:22, fs:9 },
  { id:'memberMiddleName', key:'memberMiddleName', page:1, top:26.2, left:36.3,w:22, fs:9 },
  { id:'memberNameExt',    key:'memberNameExt',    page:1, top:26.2, left:58.3,w:7,  fs:9 },
  // Mother's maiden name row
  { id:'motherLastName',   key:'motherLastName',   page:1, top:28.8, left:3,   w:11, fs:9 },
  { id:'motherFirstName',  key:'motherFirstName',  page:1, top:28.8, left:14.4,w:22, fs:9 },
  { id:'motherMiddleName', key:'motherMiddleName', page:1, top:28.8, left:36.3,w:22, fs:9 },
  // Spouse name row
  { id:'spouseLastName',   key:'spouseLastName',   page:1, top:31.6, left:3,   w:11, fs:9 },
  { id:'spouseFirstName',  key:'spouseFirstName',  page:1, top:31.6, left:14.4,w:22, fs:9 },
  { id:'spouseMiddleName', key:'spouseMiddleName', page:1, top:31.6, left:36.3,w:22, fs:9 },
  // DOB block
  { id:'memberDOB',        key:'memberDOB',        page:1, top:36.8, left:3,   w:28, fs:9, computed:'memberDOB' },
  { id:'placeOfBirth',     key:'placeOfBirth',     page:1, top:36.8, left:36,  w:54, fs:9 },
  // Sex/Civil Status/Citizenship
  { id:'memberSex',        key:'memberSex',        page:1, top:42.9, left:3,   w:11, fs:9 },
  { id:'civilStatus',      key:'civilStatus',      page:1, top:42.9, left:14,  w:22, fs:9 },
  { id:'citizenship',      key:'citizenship',      page:1, top:42.9, left:36,  w:22, fs:9 },
  // Permanent address
  { id:'addrStreet',       key:'addrStreet',       page:1, top:48.9, left:3,   w:63, fs:9 },
  { id:'mobile',           key:'mobile',           page:1, top:50.9, left:68,  w:28, fs:9 },
  { id:'addrSubdivision',  key:'addrSubdivision',  page:1, top:49.9, left:3,   w:11, fs:9 },
  { id:'addrBarangay',     key:'addrBarangay',     page:1, top:49.9, left:14.5,w:12, fs:9 },
  { id:'addrCity',         key:'addrCity',         page:1, top:49.9, left:26.1,w:11, fs:9 },
  { id:'addrProvince',     key:'addrProvince',     page:1, top:49.9, left:37.4,w:22, fs:9 },
  { id:'addrZip',          key:'addrZip',          page:1, top:49.9, left:59.9,w:7,  fs:9 },
  { id:'homePhone',        key:'homePhone',        page:1, top:46.3, left:68,  w:28, fs:9 },
  // Dependent row 1
  { id:'patientLastName',  key:'patientLastName',  page:1, top:65.8, left:3,   w:17, fs:9 },
  { id:'patientFirstName', key:'patientFirstName', page:1, top:65.8, left:20.4,w:19, fs:9 },
  { id:'patientMiddleName',key:'patientMiddleName',page:1, top:65.8, left:48.1,w:14, fs:9 },
  { id:'relationship',     key:'relationship',     page:1, top:65.8, left:62.8,w:15, fs:9 },
  { id:'patientDOB',       key:'patientDOB',       page:1, top:65.8, left:78,  w:19, fs:9, computed:'patientDOB' },
  // Member type section
  { id:'memberType',       key:'memberType',       page:1, top:77.5, left:3,   w:92, fs:9 },
  // Profession / Income
  { id:'profession',       key:'profession',       page:1, top:93.5, left:3,   w:35, fs:9 },
  { id:'monthlyIncome',    key:'monthlyIncome',    page:1, top:93.5, left:40,  w:25, fs:9 },
];
