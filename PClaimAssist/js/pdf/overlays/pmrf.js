/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – PMRF (594.75×841.5 pt, 2 pages)
   top/left are % of rendered page (0–100).
   Coordinates derived from actual PDF text/rect extraction
   (page.get_drawings() + get_text('words') via PyMuPDF).
   Fields marked `checkbox:true` render a checkmark when
   state.data[key] is truthy (or equals checkValue, for the
   multi-option groups like Member Type / Civil Status).
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_PMRF = [
  // PhilHealth Identification Number (PIN) — 12 individual digit boxes
  { id:'memberPINc1', key:'memberPINc1', page:1, top:8.57, left:64.081, w:2.522, fs:9, computed:'memberPINc1', center:true },
  { id:'memberPINc2', key:'memberPINc2', page:1, top:8.57, left:66.603, w:2.606, fs:9, computed:'memberPINc2', center:true },
  { id:'memberPINc3', key:'memberPINc3', page:1, top:8.57, left:69.209, w:2.522, fs:9, computed:'memberPINc3', center:true },
  { id:'memberPINc4', key:'memberPINc4', page:1, top:8.57, left:71.731, w:2.69, fs:9, computed:'memberPINc4', center:true },
  { id:'memberPINc5', key:'memberPINc5', page:1, top:8.57, left:74.842, w:2.522, fs:9, computed:'memberPINc5', center:true },
  { id:'memberPINc6', key:'memberPINc6', page:1, top:8.57, left:77.364, w:2.65, fs:9, computed:'memberPINc6', center:true },
  { id:'memberPINc7', key:'memberPINc7', page:1, top:8.57, left:80.013, w:2.522, fs:9, computed:'memberPINc7', center:true },
  { id:'memberPINc8', key:'memberPINc8', page:1, top:8.57, left:82.536, w:2.69, fs:9, computed:'memberPINc8', center:true },
  { id:'memberPINc9', key:'memberPINc9', page:1, top:8.57, left:85.646, w:2.522, fs:9, computed:'memberPINc9', center:true },
  { id:'memberPINc10', key:'memberPINc10', page:1, top:8.57, left:88.168, w:2.606, fs:9, computed:'memberPINc10', center:true },
  { id:'memberPINc11', key:'memberPINc11', page:1, top:8.57, left:90.774, w:2.522, fs:9, computed:'memberPINc11', center:true },
  { id:'memberPINc12', key:'memberPINc12', page:1, top:8.57, left:93.296, w:2.69, fs:9, computed:'memberPINc12', center:true },

  // Purpose
  { id:'purposeRegistration', key:'registrationPurpose', page:1, top:13.923, left:59.623, w:1.251, fs:9, center:true, checkbox:true, checkValue:'Registration' },
  { id:'purposeUpdating', key:'registrationPurpose', page:1, top:13.923, left:74.694, w:1.251, fs:9, center:true, checkbox:true, checkValue:'Updating/Amendment' },
  { id:'preferredKonsulta', key:'preferredKonsulta', page:1, top:17.399, left:59.743, w:35.645, fs:8 },

  // Personal Details — Name table
  { id:'memberLastName', key:'memberLastName', page:1, top:24.501, left:14.628, w:21.438, fs:9, center:true },
  { id:'memberFirstName', key:'memberFirstName', page:1, top:24.503, left:36.57, w:21.438, fs:9, center:true },
  { id:'memberNameExt', key:'memberNameExt', page:1, top:24.503, left:58.512, w:6.305, fs:9, center:true },
  { id:'memberMiddleName', key:'memberMiddleName', page:1, top:24.5, left:65.322, w:21.438, fs:9, center:true },
  { id:'motherLastName', key:'motherLastName', page:1, top:27.176, left:14.628, w:21.438, fs:9, center:true },
  { id:'motherFirstName', key:'motherFirstName', page:1, top:27.177, left:36.57, w:21.438, fs:9, center:true },
  { id:'motherNameExt', key:'motherNameExt', page:1, top:27.177, left:58.512, w:6.305, fs:9, center:true },
  { id:'motherMiddleName', key:'motherMiddleName', page:1, top:27.177, left:65.334, w:21.425, fs:9, center:true },
  { id:'spouseLastName', key:'spouseLastName', page:1, top:29.892, left:14.628, w:21.438, fs:9, center:true },
  { id:'spouseFirstName', key:'spouseFirstName', page:1, top:29.892, left:36.57, w:21.424, fs:9, center:true },
  { id:'spouseNameExt', key:'spouseNameExt', page:1, top:29.897, left:58.512, w:6.305, fs:9, center:true },
  { id:'spouseMiddleName', key:'spouseMiddleName', page:1, top:29.894, left:65.334, w:21.426, fs:9, center:true },

  // Name table — No Middle Name / Mononym checkboxes
  { id:'memberNoMiddleName', key:'memberNoMiddleName', page:1, top:24.66, left:88.619, w:1.324, fs:9, center:true, checkbox:true },
  { id:'memberMononym', key:'memberMononym', page:1, top:24.637, left:93.443, w:1.324, fs:9, center:true, checkbox:true },
  { id:'motherNoMiddleName', key:'motherNoMiddleName', page:1, top:26.998, left:88.619, w:1.324, fs:9, center:true, checkbox:true },
  { id:'motherMononym', key:'motherMononym', page:1, top:26.977, left:93.443, w:1.324, fs:9, center:true, checkbox:true },
  { id:'spouseNoMiddleName', key:'spouseNoMiddleName', page:1, top:29.676, left:88.619, w:1.324, fs:9, center:true, checkbox:true },
  { id:'spouseMononym', key:'spouseMononym', page:1, top:29.654, left:93.443, w:1.324, fs:9, center:true, checkbox:true },

  // Date of Birth — 8 individual digit boxes (mm mm dd dd yyyy yyyy yyyy yyyy)
  { id:'memberDOBd1', key:'memberDOBd1', page:1, top:34.002, left:3.719, w:2.522, fs:8, center:true, computed:'memberDOBd1' },
  { id:'memberDOBd2', key:'memberDOBd2', page:1, top:34.002, left:6.241, w:2.69, fs:8, center:true, computed:'memberDOBd2' },
  { id:'memberDOBd3', key:'memberDOBd3', page:1, top:34.002, left:9.604, w:2.482, fs:8, center:true, computed:'memberDOBd3' },
  { id:'memberDOBd4', key:'memberDOBd4', page:1, top:34.002, left:12.086, w:2.69, fs:8, center:true, computed:'memberDOBd4' },
  { id:'memberDOBd5', key:'memberDOBd5', page:1, top:34.002, left:15.533, w:2.522, fs:8, center:true, computed:'memberDOBd5' },
  { id:'memberDOBd6', key:'memberDOBd6', page:1, top:34.002, left:18.055, w:2.438, fs:8, center:true, computed:'memberDOBd6' },
  { id:'memberDOBd7', key:'memberDOBd7', page:1, top:34.002, left:20.493, w:2.522, fs:8, center:true, computed:'memberDOBd7' },
  { id:'memberDOBd8', key:'memberDOBd8', page:1, top:34.002, left:23.015, w:2.69, fs:8, center:true, computed:'memberDOBd8' },

  // Place of Birth
  { id:'placeOfBirth', key:'placeOfBirth', page:1, top:35.701, left:27.24, w:36.32, fs:9 },

  // PhilSys ID Number — 12 individual digit boxes
  { id:'philsysIdc1', key:'philsysIdc1', page:1, top:34.791, left:64.208, w:2.478, fs:7, center:true, computed:'philsysIdc1' },
  { id:'philsysIdc2', key:'philsysIdc2', page:1, top:34.791, left:66.687, w:2.522, fs:7, center:true, computed:'philsysIdc2' },
  { id:'philsysIdc3', key:'philsysIdc3', page:1, top:34.791, left:69.209, w:2.566, fs:7, center:true, computed:'philsysIdc3' },
  { id:'philsysIdc4', key:'philsysIdc4', page:1, top:34.791, left:71.775, w:2.69, fs:7, center:true, computed:'philsysIdc4' },
  { id:'philsysIdc5', key:'philsysIdc5', page:1, top:34.791, left:75.094, w:2.438, fs:7, center:true, computed:'philsysIdc5' },
  { id:'philsysIdc6', key:'philsysIdc6', page:1, top:34.791, left:77.532, w:2.522, fs:7, center:true, computed:'philsysIdc6' },
  { id:'philsysIdc7', key:'philsysIdc7', page:1, top:34.791, left:80.054, w:2.65, fs:7, center:true, computed:'philsysIdc7' },
  { id:'philsysIdc8', key:'philsysIdc8', page:1, top:34.791, left:82.704, w:2.69, fs:7, center:true, computed:'philsysIdc8' },
  { id:'philsysIdc9', key:'philsysIdc9', page:1, top:34.791, left:85.814, w:2.478, fs:7, center:true, computed:'philsysIdc9' },
  { id:'philsysIdc10', key:'philsysIdc10', page:1, top:34.791, left:88.293, w:2.522, fs:7, center:true, computed:'philsysIdc10' },
  { id:'philsysIdc11', key:'philsysIdc11', page:1, top:34.791, left:90.815, w:2.566, fs:7, center:true, computed:'philsysIdc11' },
  { id:'philsysIdc12', key:'philsysIdc12', page:1, top:34.791, left:93.38, w:2.69, fs:7, center:true, computed:'philsysIdc12' },

  // Tax Payer Identification Number (TIN) — 9 individual digit boxes
  { id:'tinc1', key:'tinc1', page:1, top:39.575, left:64.208, w:2.438, fs:7, center:true, computed:'tinc1' },
  { id:'tinc2', key:'tinc2', page:1, top:39.575, left:66.646, w:2.522, fs:7, center:true, computed:'tinc2' },
  { id:'tinc3', key:'tinc3', page:1, top:39.575, left:69.169, w:2.69, fs:7, center:true, computed:'tinc3' },
  { id:'tinc4', key:'tinc4', page:1, top:39.575, left:72.447, w:2.478, fs:7, center:true, computed:'tinc4' },
  { id:'tinc5', key:'tinc5', page:1, top:39.575, left:74.926, w:2.522, fs:7, center:true, computed:'tinc5' },
  { id:'tinc6', key:'tinc6', page:1, top:39.575, left:77.448, w:2.69, fs:7, center:true, computed:'tinc6' },
  { id:'tinc7', key:'tinc7', page:1, top:39.575, left:80.642, w:2.482, fs:7, center:true, computed:'tinc7' },
  { id:'tinc8', key:'tinc8', page:1, top:39.575, left:83.124, w:2.522, fs:7, center:true, computed:'tinc8' },
  { id:'tinc9', key:'tinc9', page:1, top:39.575, left:85.646, w:2.69, fs:7, center:true, computed:'tinc9' },

  // Sex
  { id:'sexMale', key:'memberSex', page:1, top:39.076, left:3.594, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Male' },
  { id:'sexFemale', key:'memberSex', page:1, top:40.598, left:3.594, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Female' },
  // Civil Status
  { id:'civilSingle', key:'civilStatus', page:1, top:38.832, left:11.192, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Single' },
  { id:'civilAnnulled', key:'civilStatus', page:1, top:38.832, left:19.136, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Annulled' },
  { id:'civilMarried', key:'civilStatus', page:1, top:40.151, left:11.234, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Married' },
  { id:'civilWidowed', key:'civilStatus', page:1, top:40.165, left:19.136, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Widowed' },
  { id:'civilLegallySeparated', key:'civilStatus', page:1, top:41.543, left:11.201, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Legally Separated' },
  // Citizenship
  { id:'citizenFilipino', key:'citizenship', page:1, top:39.154, left:30.013, w:1.324, fs:9, center:true, checkbox:true, checkValue:'FILIPINO' },
  { id:'citizenForeign', key:'citizenship', page:1, top:39.124, left:44.641, w:1.324, fs:9, center:true, checkbox:true, checkValue:'FOREIGN NATIONAL' },
  { id:'citizenDual', key:'citizenship', page:1, top:40.963, left:30.018, w:1.324, fs:9, center:true, checkbox:true, checkValue:'DUAL CITIZEN' },

  // Permanent Home Address — line 1 (Unit/Building/Lot/Street)
  { id:'addrUnit', key:'addrUnit', page:1, top:47.652, left:3.329, w:12.694, fs:9 },
  { id:'addrBuilding', key:'addrBuilding', page:1, top:47.652, left:16.36, w:9.87, fs:9 },
  { id:'addrLot', key:'addrLot', page:1, top:47.652, left:26.566, w:22.85, fs:9 },
  { id:'addrStreet', key:'addrStreet', page:1, top:47.652, left:49.752, w:16.873, fs:9 },
  { id:'homePhone', key:'homePhone', page:1, top:46.972, left:68.054, w:27.701, fs:9 },
  // Permanent Home Address — line 2 (Subdivision/Barangay/City/Province/ZIP)
  { id:'addrSubdivision', key:'addrSubdivision', page:1, top:50.712, left:3.329, w:10.862, fs:9 },
  { id:'addrBarangay', key:'addrBarangay', page:1, top:50.712, left:14.527, w:11.248, fs:9 },
  { id:'addrCity', key:'addrCity', page:1, top:50.712, left:26.112, w:11.03, fs:9 },
  { id:'addrProvince', key:'addrProvince', page:1, top:50.712, left:37.478, w:22.093, fs:9 },
  { id:'addrZip', key:'addrZip', page:1, top:50.712, left:59.908, w:6.717, fs:9 },
  { id:'mobile', key:'mobile', page:1, top:51.552, left:67.997, w:27.758, fs:9 },

  // Mailing Address
  { id:'mailingSameAsAbove', key:'mailingSameAsAbove', page:1, top:52.598, left:19.482, w:1.324, fs:9, center:true, checkbox:true },
  { id:'businessPhone', key:'businessPhone', page:1, top:54.853, left:68.054, w:27.701, fs:9 },
  { id:'mailingAddrUnit', key:'mailingAddrUnit', page:1, top:55.109, left:3.329, w:12.711, fs:9 },
  { id:'mailingAddrBuilding', key:'mailingAddrBuilding', page:1, top:55.109, left:16.377, w:9.853, fs:9 },
  { id:'mailingAddrLot', key:'mailingAddrLot', page:1, top:55.109, left:26.566, w:22.833, fs:9 },
  { id:'mailingAddrStreet', key:'mailingAddrStreet', page:1, top:55.109, left:49.735, w:16.889, fs:9 },
  { id:'email', key:'email', page:1, top:58.088, left:68.054, w:27.701, fs:9 },
  { id:'mailingAddrSubdivision', key:'mailingAddrSubdivision', page:1, top:58.389, left:3.279, w:10.862, fs:9 },
  { id:'mailingAddrBarangay', key:'mailingAddrBarangay', page:1, top:58.389, left:14.477, w:11.248, fs:9 },
  { id:'mailingAddrCity', key:'mailingAddrCity', page:1, top:58.389, left:26.061, w:11.03, fs:9 },
  { id:'mailingAddrProvince', key:'mailingAddrProvince', page:1, top:58.389, left:37.427, w:22.093, fs:9 },
  { id:'mailingAddrZip', key:'mailingAddrZip', page:1, top:58.389, left:59.857, w:6.768, fs:9 },

  // Declaration of Dependents (4 rows — row 1 reuses the shared "patient" fields)
  { id:'patientLastName', key:'patientLastName', page:1, top:66.521, left:3.279, w:16.898, fs:8, center:true },
  { id:'patientFirstName', key:'patientFirstName', page:1, top:66.521, left:20.681, w:18.411, fs:8, center:true },
  { id:'patientNameExt', key:'patientNameExt', page:1, top:66.523, left:39.596, w:4.792, fs:8, center:true },
  { id:'patientMiddleName', key:'patientMiddleName', page:1, top:66.523, left:44.893, w:16.898, fs:8, center:true },
  { id:'relationship', key:'relationship', page:1, top:66.521, left:62.379, w:6.894, fs:8 },
  { id:'patientDOB', key:'patientDOB', page:1, top:66.478, left:69.945, w:6.894, fs:7, computed:'patientDOB' },
  { id:'patientCitizenship', key:'patientCitizenship', page:1, top:66.478, left:77.512, w:5.38, fs:7 },
  { id:'dep1NoMiddleName', key:'dep1NoMiddleName', page:1, top:66.788, left:84.817, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep1Mononym', key:'dep1Mononym', page:1, top:66.788, left:89.375, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep1Disability', key:'dep1Disability', page:1, top:66.788, left:93.915, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep2LastName', key:'dep2LastName', page:1, top:68.657, left:3.279, w:16.898, fs:8, center:true },
  { id:'dep2FirstName', key:'dep2FirstName', page:1, top:68.662, left:20.681, w:18.411, fs:8, center:true },
  { id:'dep2Ext', key:'dep2Ext', page:1, top:68.661, left:39.596, w:4.792, fs:8, center:true },
  { id:'dep2MiddleName', key:'dep2MiddleName', page:1, top:68.658, left:44.893, w:16.898, fs:8, center:true },
  { id:'dep2Relationship', key:'dep2Relationship', page:1, top:68.657, left:62.379, w:6.894, fs:8 },
  { id:'dep2DOB', key:'dep2DOB', page:1, top:68.617, left:69.945, w:6.894, fs:7, computed:'dep2DOB' },
  { id:'dep2Citizenship', key:'dep2Citizenship', page:1, top:68.615, left:77.512, w:5.38, fs:7 },
  { id:'dep2NoMiddleName', key:'dep2NoMiddleName', page:1, top:68.928, left:84.817, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep2Mononym', key:'dep2Mononym', page:1, top:68.928, left:89.375, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep2Disability', key:'dep2Disability', page:1, top:68.928, left:93.915, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep3LastName', key:'dep3LastName', page:1, top:70.799, left:3.279, w:16.898, fs:8, center:true },
  { id:'dep3FirstName', key:'dep3FirstName', page:1, top:70.799, left:20.681, w:18.411, fs:8, center:true },
  { id:'dep3Ext', key:'dep3Ext', page:1, top:70.8, left:39.596, w:4.792, fs:8, center:true },
  { id:'dep3MiddleName', key:'dep3MiddleName', page:1, top:70.799, left:44.893, w:16.898, fs:8, center:true },
  { id:'dep3Relationship', key:'dep3Relationship', page:1, top:70.799, left:62.379, w:6.894, fs:8 },
  { id:'dep3DOB', key:'dep3DOB', page:1, top:70.756, left:69.945, w:6.894, fs:7, computed:'dep3DOB' },
  { id:'dep3Citizenship', key:'dep3Citizenship', page:1, top:70.757, left:77.512, w:5.38, fs:7 },
  { id:'dep3NoMiddleName', key:'dep3NoMiddleName', page:1, top:71.068, left:84.817, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep3Mononym', key:'dep3Mononym', page:1, top:71.068, left:89.375, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep3Disability', key:'dep3Disability', page:1, top:71.054, left:93.934, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep4LastName', key:'dep4LastName', page:1, top:72.941, left:3.279, w:16.898, fs:8, center:true },
  { id:'dep4FirstName', key:'dep4FirstName', page:1, top:72.941, left:20.681, w:18.411, fs:8, center:true },
  { id:'dep4Ext', key:'dep4Ext', page:1, top:72.941, left:39.596, w:4.792, fs:8, center:true },
  { id:'dep4MiddleName', key:'dep4MiddleName', page:1, top:72.941, left:44.893, w:16.898, fs:8, center:true },
  { id:'dep4Relationship', key:'dep4Relationship', page:1, top:72.941, left:62.379, w:6.894, fs:8 },
  { id:'dep4DOB', key:'dep4DOB', page:1, top:72.898, left:69.945, w:6.894, fs:7, computed:'dep4DOB' },
  { id:'dep4Citizenship', key:'dep4Citizenship', page:1, top:72.898, left:77.512, w:5.38, fs:7 },
  { id:'dep4NoMiddleName', key:'dep4NoMiddleName', page:1, top:72.914, left:84.817, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep4Mononym', key:'dep4Mononym', page:1, top:72.928, left:89.375, w:1.324, fs:8, center:true, checkbox:true },
  { id:'dep4Disability', key:'dep4Disability', page:1, top:72.928, left:93.934, w:1.324, fs:8, center:true, checkbox:true },

  // Member Type — Direct Contributor / Indirect Contributor (single-select group)
  { id:'mtEmployedPrivate', key:'memberType', page:1, top:78.801, left:3.862, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Employed Private' },
  { id:'mtEmployedGovernment', key:'memberType', page:1, top:80.237, left:3.862, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Employed Government' },
  { id:'mtProfessionalPractitioner', key:'memberType', page:1, top:81.758, left:3.91, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Professional Practitioner' },
  { id:'mtSelfEarningIndividual', key:'memberType', page:1, top:83.362, left:3.944, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Self-Earning Individual' },
  { id:'mtSelfEarningIndividualSub', key:'memberType', page:1, top:84.966, left:5.417, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Self-Earning Individual — Individual' },
  { id:'mtSoleProprietor', key:'memberType', page:1, top:86.378, left:5.417, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Self-Earning Individual — Sole Proprietor' },
  { id:'mtGroupEnrollmentScheme', key:'memberType', page:1, top:87.914, left:5.391, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Self-Earning Individual — Group Enrollment Scheme' },
  { id:'mtKasambahay', key:'memberType', page:1, top:78.816, left:27.807, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Kasambahay/Family Driver' },
  { id:'mtMigrantWorker', key:'memberType', page:1, top:80.353, left:27.859, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Migrant Worker' },
  { id:'mtLandBased', key:'memberType', page:1, top:81.728, left:30.182, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Migrant Worker — Land-Based' },
  { id:'mtSeaBased', key:'memberType', page:1, top:81.667, left:43.351, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Migrant Worker — Sea-Based' },
  { id:'mtLifetimeMember', key:'memberType', page:1, top:83.213, left:27.807, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Lifetime Member' },
  { id:'mtDualCitizenship', key:'memberType', page:1, top:84.706, left:27.807, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Filipinos with Dual Citizenship/Living Abroad' },
  { id:'mtForeignNational', key:'memberType', page:1, top:86.273, left:27.807, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Foreign National' },
  { id:'mtListahanan', key:'memberType', page:1, top:79.434, left:64.745, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Listahanan' },
  { id:'mt4PsMcct', key:'memberType', page:1, top:81.109, left:64.718, w:1.324, fs:8, center:true, checkbox:true, checkValue:'4Ps/MCCT' },
  { id:'mtSeniorCitizen', key:'memberType', page:1, top:82.707, left:64.731, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Senior Citizen' },
  { id:'mtPWD', key:'memberType', page:1, top:84.056, left:77.258, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Person with Disability' },
  { id:'mtKiaKipo', key:'memberType', page:1, top:85.844, left:64.745, w:1.324, fs:8, center:true, checkbox:true, checkValue:'KIA/KIPO' },
  { id:'mtBangsamoro', key:'memberType', page:1, top:87.512, left:64.797, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Bangsamoro/Normalization' },
  { id:'mtLguSponsored', key:'memberType', page:1, top:79.434, left:77.258, w:1.324, fs:8, center:true, checkbox:true, checkValue:'LGU-sponsored' },
  { id:'mtNgaSponsored', key:'memberType', page:1, top:80.988, left:77.258, w:1.324, fs:8, center:true, checkbox:true, checkValue:'NGA-sponsored' },
  { id:'mtPrivateSponsored', key:'memberType', page:1, top:82.461, left:77.258, w:1.324, fs:8, center:true, checkbox:true, checkValue:'Private-sponsored' },
  { id:'mtPamana', key:'memberType', page:1, top:84.213, left:64.77, w:1.324, fs:8, center:true, checkbox:true, checkValue:'PAMANA' },

  // Member Type — supporting text fields
  { id:'pwdIdNo', key:'pwdIdNo', page:1, top:85.758, left:85.32, w:10.42, fs:7 },
  { id:'praSrrvNo', key:'praSrrvNo', page:1, top:87.838, left:40.83, w:17.65, fs:7 },
  { id:'acrICardNo', key:'acrICardNo', page:1, top:89.048, left:40.91, w:17.65, fs:7 },
  { id:'groupEnrollmentNo', key:'groupEnrollmentNo', page:1, top:89.408, left:7.28, w:16.98, fs:7 },
  { id:'profession', key:'profession', page:1, top:94.008, left:3.363, w:28.836, fs:8 },
  { id:'monthlyIncome', key:'monthlyIncomeDisplay', computed:'monthlyIncomeDisplay', page:1, top:93.68, left:32.871, w:14.46, fs:8 },
  { id:'proofPOS', key:'proofOfIncome', page:1, top:91.812, left:65.069, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Point of Service (POS)' },
  { id:'proofFinanciallyIncapable', key:'proofOfIncome', page:1, top:93.772, left:65.069, w:1.324, fs:9, center:true, checkbox:true, checkValue:'Financially Incapable' },

  // PAGE 2 — V. Updating/Amendment (5 rows: checkbox + FROM/TO blanks)
  { id:'amendName', key:'amendName', page:2, top:7.43, left:4.061, w:1.324, fs:9, center:true, checkbox:true },
  { id:'amendNameFrom', key:'amendNameFrom', page:2, top:7.433, left:35.292, w:31.105, fs:8 },
  { id:'amendNameTo', key:'amendNameTo', page:2, top:7.433, left:67.07, w:29.592, fs:8 },
  { id:'amendDOB', key:'amendDOB', page:2, top:10.098, left:4.065, w:1.324, fs:9, center:true, checkbox:true },
  { id:'amendDOBFrom', key:'amendDOBFrom', page:2, top:10.191, left:35.292, w:31.106, fs:8 },
  { id:'amendDOBTo', key:'amendDOBTo', page:2, top:10.191, left:67.07, w:29.592, fs:8 },
  { id:'amendSex', key:'amendSex', page:2, top:12.849, left:3.998, w:1.324, fs:9, center:true, checkbox:true },
  { id:'amendSexFrom', key:'amendSexFrom', page:2, top:12.957, left:35.292, w:31.106, fs:8 },
  { id:'amendSexTo', key:'amendSexTo', page:2, top:12.957, left:67.07, w:29.592, fs:8 },
  { id:'amendCivilStatus', key:'amendCivilStatus', page:2, top:15.712, left:3.935, w:1.324, fs:9, center:true, checkbox:true },
  { id:'amendCivilStatusFrom', key:'amendCivilStatusFrom', page:2, top:15.716, left:35.292, w:31.106, fs:8 },
  { id:'amendCivilStatusTo', key:'amendCivilStatusTo', page:2, top:15.72, left:67.07, w:29.592, fs:8 },
  { id:'amendPersonalInfo', key:'amendPersonalInfo', page:2, top:18.733, left:3.935, w:1.324, fs:9, center:true, checkbox:true },
  { id:'amendPersonalInfoFrom', key:'amendPersonalInfoFrom', page:2, top:18.843, left:35.292, w:31.106, fs:8 },
  { id:'amendPersonalInfoTo', key:'amendPersonalInfoTo', page:2, top:18.847, left:67.07, w:29.592, fs:8 },

  // PAGE 2 — Member's Signature and Date (the "FOR PHILHEALTH USE ONLY" box
  // to the right — Received By / PRO-LHIO-Branch / Date & Time — is
  // intentionally not overlaid; it's filled in by PhilHealth staff, not the encoder)
  { id:'memberSignatureName', key:'memberSignName', computed:'memberSignName', page:2, top:39.815, left:4.515, w:32.838, fs:8, center:true },
  { id:'memberSignatureDate', key:'memberSignatureDate', page:2, top:39.815, left:38.38, w:11.43, fs:8, computed:'memberSignatureDate' },
];
