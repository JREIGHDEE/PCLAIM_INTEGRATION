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
  { id:'memberPINc1', key:'memberPINc1', page:1, top:9.53, left:64.03, w:3.03, fs:9, computed:'memberPINc1', center:true },
  { id:'memberPINc2', key:'memberPINc2', page:1, top:9.53, left:66.55, w:3.03, fs:9, computed:'memberPINc2', center:true },
  { id:'memberPINc3', key:'memberPINc3', page:1, top:9.53, left:69.19, w:3.03, fs:9, computed:'memberPINc3', center:true },
  { id:'memberPINc4', key:'memberPINc4', page:1, top:9.53, left:71.71, w:3.03, fs:9, computed:'memberPINc4', center:true },
  { id:'memberPINc5', key:'memberPINc5', page:1, top:9.53, left:74.81, w:3.03, fs:9, computed:'memberPINc5', center:true },
  { id:'memberPINc6', key:'memberPINc6', page:1, top:9.53, left:77.33, w:3.03, fs:9, computed:'memberPINc6', center:true },
  { id:'memberPINc7', key:'memberPINc7', page:1, top:9.53, left:79.97, w:3.03, fs:9, computed:'memberPINc7', center:true },
  { id:'memberPINc8', key:'memberPINc8', page:1, top:9.53, left:82.49, w:3.03, fs:9, computed:'memberPINc8', center:true },
  { id:'memberPINc9', key:'memberPINc9', page:1, top:9.53, left:85.59, w:3.03, fs:9, computed:'memberPINc9', center:true },
  { id:'memberPINc10', key:'memberPINc10', page:1, top:9.53, left:88.12, w:3.03, fs:9, computed:'memberPINc10', center:true },
  { id:'memberPINc11', key:'memberPINc11', page:1, top:9.53, left:90.75, w:3.03, fs:9, computed:'memberPINc11', center:true },
  { id:'memberPINc12', key:'memberPINc12', page:1, top:9.53, left:93.27, w:3.03, fs:9, computed:'memberPINc12', center:true },

  // Purpose
  { id:'purposeRegistration', key:'registrationPurpose', page:1, top:14.44, left:59.62, w:1.25, fs:9, checkbox:true, checkValue:'Registration' },
  { id:'purposeUpdating', key:'registrationPurpose', page:1, top:14.44, left:74.69, w:1.25, fs:9, checkbox:true, checkValue:'Updating/Amendment' },
  { id:'preferredKonsulta', key:'preferredKonsulta', page:1, top:18.49, left:59.41, w:36.32, fs:8 },

  // Personal Details — Name table
  { id:'memberLastName', key:'memberLastName', page:1, top:25.82, left:14.38, w:21.94, fs:9 },
  { id:'memberFirstName', key:'memberFirstName', page:1, top:25.82, left:36.32, w:21.94, fs:9 },
  { id:'memberNameExt', key:'memberNameExt', page:1, top:25.82, left:58.26, w:6.81, fs:9 },
  { id:'memberMiddleName', key:'memberMiddleName', page:1, top:25.82, left:65.07, w:21.94, fs:9 },
  { id:'motherLastName', key:'motherLastName', page:1, top:28.49, left:14.38, w:21.94, fs:9 },
  { id:'motherFirstName', key:'motherFirstName', page:1, top:28.49, left:36.32, w:21.94, fs:9 },
  { id:'motherNameExt', key:'motherNameExt', page:1, top:28.49, left:58.26, w:6.81, fs:9 },
  { id:'motherMiddleName', key:'motherMiddleName', page:1, top:28.49, left:65.07, w:21.94, fs:9 },
  { id:'spouseLastName', key:'spouseLastName', page:1, top:31.25, left:14.38, w:21.94, fs:9 },
  { id:'spouseFirstName', key:'spouseFirstName', page:1, top:31.25, left:36.32, w:21.94, fs:9 },
  { id:'spouseNameExt', key:'spouseNameExt', page:1, top:31.25, left:58.26, w:6.81, fs:9 },
  { id:'spouseMiddleName', key:'spouseMiddleName', page:1, top:31.25, left:65.07, w:21.94, fs:9 },

  // Name table — No Middle Name / Mononym checkboxes
  { id:'memberNoMiddleName', key:'memberNoMiddleName', page:1, top:25.18, left:88.62, w:1.32, fs:9, checkbox:true },
  { id:'memberMononym', key:'memberMononym', page:1, top:25.15, left:93.44, w:1.32, fs:9, checkbox:true },
  { id:'motherNoMiddleName', key:'motherNoMiddleName', page:1, top:27.51, left:88.62, w:1.32, fs:9, checkbox:true },
  { id:'motherMononym', key:'motherMononym', page:1, top:27.49, left:93.44, w:1.32, fs:9, checkbox:true },
  { id:'spouseNoMiddleName', key:'spouseNoMiddleName', page:1, top:30.19, left:88.62, w:1.32, fs:9, checkbox:true },
  { id:'spouseMononym', key:'spouseMononym', page:1, top:30.17, left:93.44, w:1.32, fs:9, checkbox:true },

  // Date of Birth — 8 individual digit boxes (mm mm dd dd yyyy yyyy yyyy yyyy)
  { id:'memberDOBd1', key:'memberDOBd1', page:1, top:35.3, left:3.67, w:3.03, fs:8, computed:'memberDOBd1' },
  { id:'memberDOBd2', key:'memberDOBd2', page:1, top:35.3, left:6.2, w:3.03, fs:8, computed:'memberDOBd2' },
  { id:'memberDOBd3', key:'memberDOBd3', page:1, top:35.3, left:9.56, w:3.03, fs:8, computed:'memberDOBd3' },
  { id:'memberDOBd4', key:'memberDOBd4', page:1, top:35.3, left:12.05, w:3.03, fs:8, computed:'memberDOBd4' },
  { id:'memberDOBd5', key:'memberDOBd5', page:1, top:35.3, left:15.48, w:3.03, fs:8, computed:'memberDOBd5' },
  { id:'memberDOBd6', key:'memberDOBd6', page:1, top:35.3, left:18.0, w:3.03, fs:8, computed:'memberDOBd6' },
  { id:'memberDOBd7', key:'memberDOBd7', page:1, top:35.3, left:20.46, w:3.03, fs:8, computed:'memberDOBd7' },
  { id:'memberDOBd8', key:'memberDOBd8', page:1, top:35.3, left:22.99, w:3.03, fs:8, computed:'memberDOBd8' },

  // Place of Birth
  { id:'placeOfBirth', key:'placeOfBirth', page:1, top:36.45, left:27.24, w:36.32, fs:9 },

  // PhilSys ID Number — 12 individual digit boxes
  { id:'philsysIdc1', key:'philsysIdc1', page:1, top:36.14, left:64.16, w:3.03, fs:7, computed:'philsysIdc1' },
  { id:'philsysIdc2', key:'philsysIdc2', page:1, top:36.14, left:66.63, w:3.03, fs:7, computed:'philsysIdc2' },
  { id:'philsysIdc3', key:'philsysIdc3', page:1, top:36.14, left:69.15, w:3.03, fs:7, computed:'philsysIdc3' },
  { id:'philsysIdc4', key:'philsysIdc4', page:1, top:36.14, left:71.73, w:3.03, fs:7, computed:'philsysIdc4' },
  { id:'philsysIdc5', key:'philsysIdc5', page:1, top:36.14, left:75.03, w:3.03, fs:7, computed:'philsysIdc5' },
  { id:'philsysIdc6', key:'philsysIdc6', page:1, top:36.14, left:77.5, w:3.03, fs:7, computed:'philsysIdc6' },
  { id:'philsysIdc7', key:'philsysIdc7', page:1, top:36.14, left:80.02, w:3.03, fs:7, computed:'philsysIdc7' },
  { id:'philsysIdc8', key:'philsysIdc8', page:1, top:36.14, left:82.66, w:3.03, fs:7, computed:'philsysIdc8' },
  { id:'philsysIdc9', key:'philsysIdc9', page:1, top:36.14, left:85.79, w:3.03, fs:7, computed:'philsysIdc9' },
  { id:'philsysIdc10', key:'philsysIdc10', page:1, top:36.14, left:88.26, w:3.03, fs:7, computed:'philsysIdc10' },
  { id:'philsysIdc11', key:'philsysIdc11', page:1, top:36.14, left:90.78, w:3.03, fs:7, computed:'philsysIdc11' },
  { id:'philsysIdc12', key:'philsysIdc12', page:1, top:36.14, left:93.36, w:3.03, fs:7, computed:'philsysIdc12' },

  // Tax Payer Identification Number (TIN) — 9 individual digit boxes
  { id:'tinc1', key:'tinc1', page:1, top:40.92, left:64.15, w:3.03, fs:7, computed:'tinc1' },
  { id:'tinc2', key:'tinc2', page:1, top:40.92, left:66.62, w:3.03, fs:7, computed:'tinc2' },
  { id:'tinc3', key:'tinc3', page:1, top:40.92, left:69.14, w:3.03, fs:7, computed:'tinc3' },
  { id:'tinc4', key:'tinc4', page:1, top:40.92, left:72.41, w:3.03, fs:7, computed:'tinc4' },
  { id:'tinc5', key:'tinc5', page:1, top:40.92, left:74.88, w:3.03, fs:7, computed:'tinc5' },
  { id:'tinc6', key:'tinc6', page:1, top:40.92, left:77.4, w:3.03, fs:7, computed:'tinc6' },
  { id:'tinc7', key:'tinc7', page:1, top:40.92, left:80.61, w:3.03, fs:7, computed:'tinc7' },
  { id:'tinc8', key:'tinc8', page:1, top:40.92, left:83.08, w:3.03, fs:7, computed:'tinc8' },
  { id:'tinc9', key:'tinc9', page:1, top:40.92, left:85.6, w:3.03, fs:7, computed:'tinc9' },

  // Sex
  { id:'sexMale', key:'memberSex', page:1, top:39.59, left:3.59, w:1.32, fs:9, checkbox:true, checkValue:'Male' },
  { id:'sexFemale', key:'memberSex', page:1, top:41.11, left:3.59, w:1.32, fs:9, checkbox:true, checkValue:'Female' },
  // Civil Status
  { id:'civilSingle', key:'civilStatus', page:1, top:39.35, left:11.19, w:1.32, fs:9, checkbox:true, checkValue:'Single' },
  { id:'civilAnnulled', key:'civilStatus', page:1, top:39.35, left:19.14, w:1.32, fs:9, checkbox:true, checkValue:'Annulled' },
  { id:'civilMarried', key:'civilStatus', page:1, top:40.67, left:11.23, w:1.32, fs:9, checkbox:true, checkValue:'Married' },
  { id:'civilWidowed', key:'civilStatus', page:1, top:40.68, left:19.14, w:1.32, fs:9, checkbox:true, checkValue:'Widowed' },
  { id:'civilLegallySeparated', key:'civilStatus', page:1, top:42.06, left:11.2, w:1.32, fs:9, checkbox:true, checkValue:'Legally Separated' },
  // Citizenship
  { id:'citizenFilipino', key:'citizenship', page:1, top:39.75, left:30.01, w:1.32, fs:9, checkbox:true, checkValue:'FILIPINO' },
  { id:'citizenForeign', key:'citizenship', page:1, top:39.72, left:44.64, w:1.32, fs:9, checkbox:true, checkValue:'FOREIGN NATIONAL' },
  { id:'citizenDual', key:'citizenship', page:1, top:41.56, left:30.02, w:1.32, fs:9, checkbox:true, checkValue:'DUAL CITIZEN' },

  // Permanent Home Address — line 1 (Unit/Building/Lot/Street)
  { id:'addrUnit', key:'addrUnit', page:1, top:47.5, left:3.33, w:11.43, fs:9 },
  { id:'addrBuilding', key:'addrBuilding', page:1, top:47.5, left:16.36, w:10.09, fs:9 },
  { id:'addrLot', key:'addrLot', page:1, top:47.5, left:26.57, w:17.99, fs:9 },
  { id:'addrStreet', key:'addrStreet', page:1, top:47.5, left:49.75, w:15.13, fs:9 },
  { id:'homePhone', key:'homePhone', page:1, top:47.9, left:67.72, w:28.37, fs:9 },
  // Permanent Home Address — line 2 (Subdivision/Barangay/City/Province/ZIP)
  { id:'addrSubdivision', key:'addrSubdivision', page:1, top:50.74, left:3.32, w:11.1, fs:9 },
  { id:'addrBarangay', key:'addrBarangay', page:1, top:50.74, left:14.53, w:11.43, fs:9 },
  { id:'addrCity', key:'addrCity', page:1, top:50.74, left:26.11, w:11.27, fs:9 },
  { id:'addrProvince', key:'addrProvince', page:1, top:50.74, left:37.47, w:11.77, fs:9 },
  { id:'addrZip', key:'addrZip', page:1, top:50.74, left:59.9, w:7.06, fs:9 },
  { id:'mobile', key:'mobile', page:1, top:52.48, left:67.66, w:28.42, fs:9 },

  // Mailing Address
  { id:'mailingSameAsAbove', key:'mailingSameAsAbove', page:1, top:53.0, left:19.48, w:1.32, fs:9, checkbox:true },
  { id:'businessPhone', key:'businessPhone', page:1, top:55.78, left:67.72, w:28.37, fs:9 },
  { id:'mailingAddrUnit', key:'mailingAddrUnit', page:1, top:55.08, left:3.33, w:11.43, fs:9 },
  { id:'mailingAddrBuilding', key:'mailingAddrBuilding', page:1, top:55.08, left:16.36, w:10.09, fs:9 },
  { id:'mailingAddrLot', key:'mailingAddrLot', page:1, top:55.08, left:26.57, w:17.99, fs:9 },
  { id:'mailingAddrStreet', key:'mailingAddrStreet', page:1, top:55.08, left:49.75, w:15.13, fs:9 },
  { id:'email', key:'email', page:1, top:59.02, left:67.72, w:28.37, fs:9 },
  { id:'mailingAddrSubdivision', key:'mailingAddrSubdivision', page:1, top:58.93, left:3.32, w:11.1, fs:9 },
  { id:'mailingAddrBarangay', key:'mailingAddrBarangay', page:1, top:58.93, left:14.53, w:11.43, fs:9 },
  { id:'mailingAddrCity', key:'mailingAddrCity', page:1, top:58.93, left:26.11, w:11.27, fs:9 },
  { id:'mailingAddrProvince', key:'mailingAddrProvince', page:1, top:58.93, left:37.47, w:11.77, fs:9 },
  { id:'mailingAddrZip', key:'mailingAddrZip', page:1, top:58.93, left:59.9, w:7.06, fs:9 },

  // Declaration of Dependents (4 rows — row 1 reuses the shared "patient" fields)
  { id:'patientLastName', key:'patientLastName', page:1, top:67.61, left:3.03, w:17.4, fs:8 },
  { id:'patientFirstName', key:'patientFirstName', page:1, top:67.61, left:20.43, w:18.92, fs:8 },
  { id:'patientNameExt', key:'patientNameExt', page:1, top:67.61, left:39.34, w:5.3, fs:8 },
  { id:'patientMiddleName', key:'patientMiddleName', page:1, top:67.61, left:44.64, w:17.4, fs:8 },
  { id:'relationship', key:'relationship', page:1, top:67.61, left:62.04, w:7.57, fs:8 },
  { id:'patientDOB', key:'patientDOB', page:1, top:67.61, left:69.61, w:7.57, fs:7, computed:'patientDOB' },
  { id:'patientCitizenship', key:'patientCitizenship', page:1, top:67.61, left:77.18, w:6.05, fs:7 },
  { id:'dep1NoMiddleName', key:'dep1NoMiddleName', page:1, top:67.61, left:84.82, w:1.32, fs:8, checkbox:true },
  { id:'dep1Mononym', key:'dep1Mononym', page:1, top:67.61, left:89.38, w:1.32, fs:8, checkbox:true },
  { id:'dep1Disability', key:'dep1Disability', page:1, top:67.61, left:93.92, w:1.32, fs:8, checkbox:true },
  { id:'dep2LastName', key:'dep2LastName', page:1, top:69.75, left:3.03, w:17.4, fs:8 },
  { id:'dep2FirstName', key:'dep2FirstName', page:1, top:69.75, left:20.43, w:18.92, fs:8 },
  { id:'dep2Ext', key:'dep2Ext', page:1, top:69.75, left:39.34, w:5.3, fs:8 },
  { id:'dep2MiddleName', key:'dep2MiddleName', page:1, top:69.75, left:44.64, w:17.4, fs:8 },
  { id:'dep2Relationship', key:'dep2Relationship', page:1, top:69.75, left:62.04, w:7.57, fs:8 },
  { id:'dep2DOB', key:'dep2DOB', page:1, top:69.75, left:69.61, w:7.57, fs:7, computed:'dep2DOB' },
  { id:'dep2Citizenship', key:'dep2Citizenship', page:1, top:69.75, left:77.18, w:6.05, fs:7 },
  { id:'dep2NoMiddleName', key:'dep2NoMiddleName', page:1, top:69.75, left:84.82, w:1.32, fs:8, checkbox:true },
  { id:'dep2Mononym', key:'dep2Mononym', page:1, top:69.75, left:89.38, w:1.32, fs:8, checkbox:true },
  { id:'dep2Disability', key:'dep2Disability', page:1, top:69.75, left:93.92, w:1.32, fs:8, checkbox:true },
  { id:'dep3LastName', key:'dep3LastName', page:1, top:71.89, left:3.03, w:17.4, fs:8 },
  { id:'dep3FirstName', key:'dep3FirstName', page:1, top:71.89, left:20.43, w:18.92, fs:8 },
  { id:'dep3Ext', key:'dep3Ext', page:1, top:71.89, left:39.34, w:5.3, fs:8 },
  { id:'dep3MiddleName', key:'dep3MiddleName', page:1, top:71.89, left:44.64, w:17.4, fs:8 },
  { id:'dep3Relationship', key:'dep3Relationship', page:1, top:71.89, left:62.04, w:7.57, fs:8 },
  { id:'dep3DOB', key:'dep3DOB', page:1, top:71.89, left:69.61, w:7.57, fs:7, computed:'dep3DOB' },
  { id:'dep3Citizenship', key:'dep3Citizenship', page:1, top:71.89, left:77.18, w:6.05, fs:7 },
  { id:'dep3NoMiddleName', key:'dep3NoMiddleName', page:1, top:71.89, left:84.82, w:1.32, fs:8, checkbox:true },
  { id:'dep3Mononym', key:'dep3Mononym', page:1, top:71.89, left:89.38, w:1.32, fs:8, checkbox:true },
  { id:'dep3Disability', key:'dep3Disability', page:1, top:71.89, left:93.93, w:1.32, fs:8, checkbox:true },
  { id:'dep4LastName', key:'dep4LastName', page:1, top:74.04, left:3.03, w:17.4, fs:8 },
  { id:'dep4FirstName', key:'dep4FirstName', page:1, top:74.04, left:20.43, w:18.92, fs:8 },
  { id:'dep4Ext', key:'dep4Ext', page:1, top:74.04, left:39.34, w:5.3, fs:8 },
  { id:'dep4MiddleName', key:'dep4MiddleName', page:1, top:74.04, left:44.64, w:17.4, fs:8 },
  { id:'dep4Relationship', key:'dep4Relationship', page:1, top:74.04, left:62.04, w:7.57, fs:8 },
  { id:'dep4DOB', key:'dep4DOB', page:1, top:74.04, left:69.61, w:7.57, fs:7, computed:'dep4DOB' },
  { id:'dep4Citizenship', key:'dep4Citizenship', page:1, top:74.04, left:77.18, w:6.05, fs:7 },
  { id:'dep4NoMiddleName', key:'dep4NoMiddleName', page:1, top:74.04, left:84.82, w:1.32, fs:8, checkbox:true },
  { id:'dep4Mononym', key:'dep4Mononym', page:1, top:74.04, left:89.38, w:1.32, fs:8, checkbox:true },
  { id:'dep4Disability', key:'dep4Disability', page:1, top:74.04, left:93.93, w:1.32, fs:8, checkbox:true },

  // Member Type — Direct Contributor / Indirect Contributor (single-select group)
  { id:'mtEmployedPrivate', key:'memberType', page:1, top:79.36, left:3.86, w:1.32, fs:8, checkbox:true, checkValue:'Employed Private' },
  { id:'mtEmployedGovernment', key:'memberType', page:1, top:80.8, left:3.86, w:1.32, fs:8, checkbox:true, checkValue:'Employed Government' },
  { id:'mtProfessionalPractitioner', key:'memberType', page:1, top:82.32, left:3.91, w:1.32, fs:8, checkbox:true, checkValue:'Professional Practitioner' },
  { id:'mtSelfEarningIndividual', key:'memberType', page:1, top:83.92, left:3.94, w:1.32, fs:8, checkbox:true, checkValue:'Self-Earning Individual' },
  { id:'mtSelfEarningIndividualSub', key:'memberType', page:1, top:85.53, left:5.42, w:1.32, fs:8, checkbox:true, checkValue:'Self-Earning Individual — Individual' },
  { id:'mtSoleProprietor', key:'memberType', page:1, top:86.94, left:5.42, w:1.32, fs:8, checkbox:true, checkValue:'Self-Earning Individual — Sole Proprietor' },
  { id:'mtGroupEnrollmentScheme', key:'memberType', page:1, top:88.47, left:5.39, w:1.32, fs:8, checkbox:true, checkValue:'Self-Earning Individual — Group Enrollment Scheme' },
  { id:'mtKasambahay', key:'memberType', page:1, top:79.38, left:27.81, w:1.32, fs:8, checkbox:true, checkValue:'Kasambahay/Family Driver' },
  { id:'mtMigrantWorker', key:'memberType', page:1, top:80.91, left:27.86, w:1.32, fs:8, checkbox:true, checkValue:'Migrant Worker' },
  { id:'mtLandBased', key:'memberType', page:1, top:82.29, left:30.18, w:1.32, fs:8, checkbox:true, checkValue:'Migrant Worker — Land-Based' },
  { id:'mtSeaBased', key:'memberType', page:1, top:82.23, left:43.35, w:1.32, fs:8, checkbox:true, checkValue:'Migrant Worker — Sea-Based' },
  { id:'mtLifetimeMember', key:'memberType', page:1, top:83.77, left:27.81, w:1.32, fs:8, checkbox:true, checkValue:'Lifetime Member' },
  { id:'mtDualCitizenship', key:'memberType', page:1, top:85.26, left:27.81, w:1.32, fs:8, checkbox:true, checkValue:'Filipinos with Dual Citizenship/Living Abroad' },
  { id:'mtForeignNational', key:'memberType', page:1, top:86.83, left:27.81, w:1.32, fs:8, checkbox:true, checkValue:'Foreign National' },
  { id:'mtListahanan', key:'memberType', page:1, top:79.99, left:64.74, w:1.32, fs:8, checkbox:true, checkValue:'Listahanan' },
  { id:'mt4PsMcct', key:'memberType', page:1, top:81.67, left:64.72, w:1.32, fs:8, checkbox:true, checkValue:'4Ps/MCCT' },
  { id:'mtSeniorCitizen', key:'memberType', page:1, top:83.27, left:64.73, w:1.32, fs:8, checkbox:true, checkValue:'Senior Citizen' },
  { id:'mtPWD', key:'memberType', page:1, top:84.77, left:64.77, w:1.32, fs:8, checkbox:true, checkValue:'Person with Disability' },
  { id:'mtKiaKipo', key:'memberType', page:1, top:86.4, left:64.74, w:1.32, fs:8, checkbox:true, checkValue:'KIA/KIPO' },
  { id:'mtBangsamoro', key:'memberType', page:1, top:88.07, left:64.8, w:1.32, fs:8, checkbox:true, checkValue:'Bangsamoro/Normalization' },
  { id:'mtLguSponsored', key:'memberType', page:1, top:79.99, left:77.26, w:1.32, fs:8, checkbox:true, checkValue:'LGU-sponsored' },
  { id:'mtNgaSponsored', key:'memberType', page:1, top:81.55, left:77.26, w:1.32, fs:8, checkbox:true, checkValue:'NGA-sponsored' },
  { id:'mtPrivateSponsored', key:'memberType', page:1, top:83.02, left:77.26, w:1.32, fs:8, checkbox:true, checkValue:'Private-sponsored' },
  { id:'mtPamana', key:'memberType', page:1, top:84.61, left:77.26, w:1.32, fs:8, checkbox:true, checkValue:'PAMANA' },

  // Member Type — supporting text fields
  { id:'pwdIdNo', key:'pwdIdNo', page:1, top:86.34, left:85.32, w:10.42, fs:7 },
  { id:'praSrrvNo', key:'praSrrvNo', page:1, top:88.42, left:40.83, w:17.65, fs:7 },
  { id:'acrICardNo', key:'acrICardNo', page:1, top:89.63, left:40.91, w:17.65, fs:7 },
  { id:'groupEnrollmentNo', key:'groupEnrollmentNo', page:1, top:89.99, left:7.28, w:16.98, fs:7 },
  { id:'profession', key:'profession', page:1, top:95.15, left:3.03, w:29.51, fs:8 },
  { id:'monthlyIncome', key:'monthlyIncome', page:1, top:95.15, left:32.54, w:15.13, fs:8 },
  { id:'proofPOS', key:'proofOfIncome', page:1, top:92.33, left:65.07, w:1.32, fs:9, checkbox:true, checkValue:'Point of Service (POS)' },
  { id:'proofFinanciallyIncapable', key:'proofOfIncome', page:1, top:94.29, left:65.07, w:1.32, fs:9, checkbox:true, checkValue:'Financially Incapable' },

  // PAGE 2 — V. Updating/Amendment (5 rows: checkbox + FROM/TO blanks)
  { id:'amendName', key:'amendName', page:2, top:8.3, left:4.06, w:1.32, fs:9, checkbox:true },
  { id:'amendNameFrom', key:'amendNameFrom', page:2, top:8.3, left:36.32, w:28.58, fs:8 },
  { id:'amendNameTo', key:'amendNameTo', page:2, top:8.3, left:68.1, w:26.9, fs:8 },
  { id:'amendDOB', key:'amendDOB', page:2, top:10.96, left:4.06, w:1.32, fs:9, checkbox:true },
  { id:'amendDOBFrom', key:'amendDOBFrom', page:2, top:10.96, left:36.32, w:28.58, fs:8 },
  { id:'amendDOBTo', key:'amendDOBTo', page:2, top:10.96, left:68.1, w:26.9, fs:8 },
  { id:'amendSex', key:'amendSex', page:2, top:13.71, left:4.0, w:1.32, fs:9, checkbox:true },
  { id:'amendSexFrom', key:'amendSexFrom', page:2, top:13.71, left:36.32, w:28.58, fs:8 },
  { id:'amendSexTo', key:'amendSexTo', page:2, top:13.71, left:68.1, w:26.9, fs:8 },
  { id:'amendCivilStatus', key:'amendCivilStatus', page:2, top:16.58, left:3.93, w:1.32, fs:9, checkbox:true },
  { id:'amendCivilStatusFrom', key:'amendCivilStatusFrom', page:2, top:16.58, left:36.32, w:28.58, fs:8 },
  { id:'amendCivilStatusTo', key:'amendCivilStatusTo', page:2, top:16.58, left:68.1, w:26.9, fs:8 },
  { id:'amendPersonalInfo', key:'amendPersonalInfo', page:2, top:19.6, left:3.93, w:1.32, fs:9, checkbox:true },
  { id:'amendPersonalInfoFrom', key:'amendPersonalInfoFrom', page:2, top:19.6, left:36.32, w:28.58, fs:8 },
  { id:'amendPersonalInfoTo', key:'amendPersonalInfoTo', page:2, top:19.6, left:68.1, w:26.9, fs:8 },

  // PAGE 2 — Member's Signature and Date (the "FOR PHILHEALTH USE ONLY" box
  // to the right — Received By / PRO-LHIO-Branch / Date & Time — is
  // intentionally not overlaid; it's filled in by PhilHealth staff, not the encoder)
  { id:'memberSignatureName', key:'memberSignatureName', page:2, top:40.48, left:4.51, w:32.79, fs:8 },
  { id:'memberSignatureDate', key:'memberSignatureDate', page:2, top:40.48, left:38.38, w:11.43, fs:8, computed:'memberSignatureDate' },
];
