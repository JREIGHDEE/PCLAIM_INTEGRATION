/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map – CF1, Claim Form 1, revised September
   2018 (612×936 pt, the same page as CSF). top/left are % of the
   rendered page (0–100), measured on forms/CF1.pdf with PyMuPDF
   (page.get_drawings() + get_text('words')) and placed the way CSF's
   are: a digit or tick box's top edge + 3 pt. Parts I–III sit in the
   same columns as CSF's.

   Everything comes from what the other forms already hold - nothing is
   typed for CF1 alone. Part V (For PhilHealth use only) and the Series #
   are left empty.

   unless:'<key>'  printed empty while state.data[key] is true (Part II,
                   "to be filled-out only if the patient is a dependent").
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF1 = [
  // ═══ Part I – Member Information ═══
  // 1. PIN of Member — 12 digit boxes
  { id:'memberPINc1', key:'memberPINc1', page:1, top:23.24, left:42.392, w:2.006, fs:8, digit:0, digitKey:'memberPIN', center:true },
  { id:'memberPINc2', key:'memberPINc2', page:1, top:23.24, left:44.401, w:2.006, fs:8, digit:1, digitKey:'memberPIN', center:true },
  { id:'memberPINc3', key:'memberPINc3', page:1, top:23.24, left:47.68, w:2.006, fs:8, digit:2, digitKey:'memberPIN', center:true },
  { id:'memberPINc4', key:'memberPINc4', page:1, top:23.24, left:49.689, w:2.006, fs:8, digit:3, digitKey:'memberPIN', center:true },
  { id:'memberPINc5', key:'memberPINc5', page:1, top:23.24, left:51.69, w:2.006, fs:8, digit:4, digitKey:'memberPIN', center:true },
  { id:'memberPINc6', key:'memberPINc6', page:1, top:23.24, left:53.7, w:2.006, fs:8, digit:5, digitKey:'memberPIN', center:true },
  { id:'memberPINc7', key:'memberPINc7', page:1, top:23.24, left:55.701, w:2.006, fs:8, digit:6, digitKey:'memberPIN', center:true },
  { id:'memberPINc8', key:'memberPINc8', page:1, top:23.24, left:57.71, w:2.006, fs:8, digit:7, digitKey:'memberPIN', center:true },
  { id:'memberPINc9', key:'memberPINc9', page:1, top:23.24, left:59.711, w:2.006, fs:8, digit:8, digitKey:'memberPIN', center:true },
  { id:'memberPINc10', key:'memberPINc10', page:1, top:23.24, left:61.72, w:2.006, fs:8, digit:9, digitKey:'memberPIN', center:true },
  { id:'memberPINc11', key:'memberPINc11', page:1, top:23.24, left:63.721, w:2.006, fs:8, digit:10, digitKey:'memberPIN', center:true },
  { id:'memberPINc12', key:'memberPINc12', page:1, top:23.24, left:66.888, w:2.006, fs:8, digit:11, digitKey:'memberPIN', center:true },

  // 2. Name of Member
  { id:'memberLastName', key:'memberLastName', page:1, top:26.31, left:4.126, w:16.265, fs:8, center:true },
  { id:'memberFirstName', key:'memberFirstName', page:1, top:26.31, left:22.223, w:16.265, fs:8, center:true },
  { id:'memberNameExt', key:'memberNameExt', page:1, top:26.31, left:40.111, w:16.265, fs:8, center:true },
  { id:'memberMiddleName', key:'memberMiddleName', page:1, top:26.31, left:58.155, w:13.462, fs:8, center:true },

  // 3. Date of Birth — mm dd yyyy
  { id:'memberDOBd1', key:'memberDOBd1', page:1, top:26.339, left:74.863, w:2.006, fs:8, digit:0, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd2', key:'memberDOBd2', page:1, top:26.339, left:76.875, w:2.006, fs:8, digit:1, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd3', key:'memberDOBd3', page:1, top:26.339, left:80.044, w:2.006, fs:8, digit:2, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd4', key:'memberDOBd4', page:1, top:26.339, left:82.056, w:2.006, fs:8, digit:3, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd5', key:'memberDOBd5', page:1, top:26.339, left:85.221, w:2.006, fs:8, digit:4, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd6', key:'memberDOBd6', page:1, top:26.339, left:87.233, w:2.006, fs:8, digit:5, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd7', key:'memberDOBd7', page:1, top:26.339, left:89.24, w:2.006, fs:8, digit:6, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },
  { id:'memberDOBd8', key:'memberDOBd8', page:1, top:26.339, left:91.251, w:2.006, fs:8, digit:7, digitKey:'memberDOB', digitOrder:'mmddyyyy', center:true },

  // 4. Mailing Address — the PMRF mailing address, or the home address
  // when no other mailing address was given (getComputedValue
  // cf1MailingAddr...); the country is worked out.
  { id:'cf1MailingAddrUnit', key:'mailingAddrUnit', page:1, top:32.4, left:4.12, w:16.26, fs:7, computed:'cf1MailingAddrUnit', center:true },
  { id:'cf1MailingAddrBuilding', key:'mailingAddrBuilding', page:1, top:32.4, left:22.21, w:16.26, fs:7, computed:'cf1MailingAddrBuilding', center:true },
  { id:'cf1MailingAddrLot', key:'mailingAddrLot', page:1, top:32.4, left:40.1, w:16.26, fs:7, computed:'cf1MailingAddrLot', center:true },
  { id:'cf1MailingAddrStreet', key:'mailingAddrStreet', page:1, top:32.4, left:58.14, w:13.46, fs:7, computed:'cf1MailingAddrStreet', center:true },
  { id:'cf1MailingAddrSubdivision', key:'mailingAddrSubdivision', page:1, top:32.4, left:73.56, w:22.43, fs:7, computed:'cf1MailingAddrSubdivision', center:true },
  { id:'cf1MailingAddrBarangay', key:'mailingAddrBarangay', page:1, top:35.69, left:4.12, w:16.26, fs:7, computed:'cf1MailingAddrBarangay', center:true },
  { id:'cf1MailingAddrCity', key:'mailingAddrCity', page:1, top:35.69, left:22.21, w:16.26, fs:7, computed:'cf1MailingAddrCity', center:true },
  { id:'cf1MailingAddrProvince', key:'mailingAddrProvince', page:1, top:35.69, left:40.1, w:16.26, fs:7, computed:'cf1MailingAddrProvince', center:true },
  { id:'cf1MailingCountry', key:'mailingCountry', page:1, top:35.69, left:58.14, w:13.46, fs:7, computed:'mailingCountry', center:true },
  { id:'cf1MailingAddrZip', key:'mailingAddrZip', page:1, top:35.69, left:73.56, w:22.43, fs:7, computed:'cf1MailingAddrZip', center:true },

  // 5. Sex
  { id:'cf1MemberSexMale', key:'memberSex', page:1, top:30.584, left:78.888, w:2.006, fs:8, checkbox:true, checkValue:'Male', center:true },
  { id:'cf1MemberSexFemale', key:'memberSex', page:1, top:30.584, left:84.728, w:2.006, fs:8, checkbox:true, checkValue:'Female', center:true },

  // 6. Contact Information
  { id:'cf1HomePhone', key:'homePhone', page:1, top:40.5, left:3.88, w:30.84, fs:8, center:true },
  { id:'cf1Mobile', key:'mobile', page:1, top:40.5, left:36.41, w:26.35, fs:8, center:true },
  { id:'cf1Email', key:'email', page:1, top:40.5, left:64.63, w:31.4, fs:8, center:true },

  // 7. Patient is the member? - "No" only once the member is known
  // (getComputedValue cf1PatientIsMember).
  { id:'cf1PatientIsMemberYes', key:'memberIsPatient', page:1, top:43.977, left:22.841, w:2.006, fs:8, checkbox:true, checkValue:'Yes', center:true, computed:'cf1PatientIsMember' },
  { id:'cf1PatientIsMemberNo', key:'memberIsPatient', page:1, top:43.977, left:37.999, w:2.006, fs:8, checkbox:true, checkValue:'No', center:true, computed:'cf1PatientIsMember' },

  // ═══ Part II – Patient Information ═══
  // Filled out only if the patient is a dependent: empty while the patient
  // is the member (`unless`).
  // 1. PIN of Dependent — 12 digit boxes
  { id:'patientPINc1', key:'patientPINc1', page:1, top:47.926, left:44.274, w:2.006, fs:8, digit:0, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc2', key:'patientPINc2', page:1, top:47.926, left:46.283, w:2.006, fs:8, digit:1, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc3', key:'patientPINc3', page:1, top:47.926, left:49.562, w:2.006, fs:8, digit:2, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc4', key:'patientPINc4', page:1, top:47.926, left:51.571, w:2.006, fs:8, digit:3, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc5', key:'patientPINc5', page:1, top:47.926, left:53.573, w:2.006, fs:8, digit:4, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc6', key:'patientPINc6', page:1, top:47.926, left:55.582, w:2.006, fs:8, digit:5, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc7', key:'patientPINc7', page:1, top:47.926, left:57.583, w:2.006, fs:8, digit:6, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc8', key:'patientPINc8', page:1, top:47.926, left:59.592, w:2.006, fs:8, digit:7, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc9', key:'patientPINc9', page:1, top:47.926, left:61.593, w:2.006, fs:8, digit:8, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc10', key:'patientPINc10', page:1, top:47.926, left:63.602, w:2.006, fs:8, digit:9, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc11', key:'patientPINc11', page:1, top:47.926, left:65.604, w:2.006, fs:8, digit:10, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },
  { id:'patientPINc12', key:'patientPINc12', page:1, top:47.926, left:68.771, w:2.006, fs:8, digit:11, digitKey:'patientPIN', center:true, unless:'memberIsPatient' },

  // 2. Name of Patient
  { id:'patientLastName', key:'patientLastName', page:1, top:51.06, left:4.126, w:16.265, fs:8, center:true, unless:'memberIsPatient' },
  { id:'patientFirstName', key:'patientFirstName', page:1, top:51.06, left:22.223, w:16.265, fs:8, center:true, unless:'memberIsPatient' },
  { id:'patientNameExt', key:'patientNameExt', page:1, top:51.06, left:40.111, w:16.265, fs:8, center:true, unless:'memberIsPatient' },
  { id:'patientMiddleName', key:'patientMiddleName', page:1, top:51.06, left:58.155, w:13.462, fs:8, center:true, unless:'memberIsPatient' },

  // 3. Date of Birth
  { id:'patientDOBd1', key:'patientDOBd1', page:1, top:51.206, left:74.863, w:2.006, fs:8, digit:0, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd2', key:'patientDOBd2', page:1, top:51.206, left:76.875, w:2.006, fs:8, digit:1, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd3', key:'patientDOBd3', page:1, top:51.206, left:80.044, w:2.006, fs:8, digit:2, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd4', key:'patientDOBd4', page:1, top:51.206, left:82.056, w:2.006, fs:8, digit:3, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd5', key:'patientDOBd5', page:1, top:51.206, left:85.221, w:2.006, fs:8, digit:4, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd6', key:'patientDOBd6', page:1, top:51.206, left:87.233, w:2.006, fs:8, digit:5, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd7', key:'patientDOBd7', page:1, top:51.206, left:89.24, w:2.006, fs:8, digit:6, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },
  { id:'patientDOBd8', key:'patientDOBd8', page:1, top:51.206, left:91.251, w:2.006, fs:8, digit:7, digitKey:'patientDOB', digitOrder:'mmddyyyy', center:true, unless:'memberIsPatient' },

  // 4. Relationship to Member
  { id:'relChild', key:'relationship', page:1, top:54.936, left:23.804, w:2.006, fs:8, checkbox:true, checkValue:'Child', center:true, unless:'memberIsPatient' },
  { id:'relParent', key:'relationship', page:1, top:54.936, left:30.157, w:2.006, fs:8, checkbox:true, checkValue:'Parent', center:true, unless:'memberIsPatient' },
  { id:'relSpouse', key:'relationship', page:1, top:54.936, left:37.32, w:2.006, fs:8, checkbox:true, checkValue:'Spouse', center:true, unless:'memberIsPatient' },

  // 5. Sex
  { id:'cf1PatientSexMale', key:'patientSex', page:1, top:54.997, left:78.888, w:2.006, fs:8, checkbox:true, checkValue:'Male', center:true, unless:'memberIsPatient' },
  { id:'cf1PatientSexFemale', key:'patientSex', page:1, top:54.997, left:84.728, w:2.006, fs:8, checkbox:true, checkValue:'Female', center:true, unless:'memberIsPatient' },

  // ═══ Part III – Member Certification ═══
  // The same signer, dates and ticks as CSF Part I (one set of boxes), so
  // "Leave blank" on either form leaves both blank (app.js SAME_SIGNER).
  { id:'cf1MemberSignName', key:'memberLineName', page:1, top:61.041, left:9.709, w:32.042, fs:7, computed:'memberLineName', center:true },
  { id:'cf1RepSignName', key:'repLineName', page:1, top:61.041, left:51.851, w:41.65, fs:7, computed:'repLineName', center:true },
  { id:'memberSignedDateD1', key:'memberSignedDateD1', page:1, top:64.121, left:17.122, w:2.006, fs:7, digit:0, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD2', key:'memberSignedDateD2', page:1, top:64.121, left:19.134, w:2.006, fs:7, digit:1, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD3', key:'memberSignedDateD3', page:1, top:64.121, left:22.303, w:2.006, fs:7, digit:2, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD4', key:'memberSignedDateD4', page:1, top:64.121, left:24.315, w:2.006, fs:7, digit:3, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD5', key:'memberSignedDateD5', page:1, top:64.121, left:27.48, w:2.006, fs:7, digit:4, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD6', key:'memberSignedDateD6', page:1, top:64.121, left:29.492, w:2.006, fs:7, digit:5, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD7', key:'memberSignedDateD7', page:1, top:64.121, left:31.498, w:2.006, fs:7, digit:6, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignedDateD8', key:'memberSignedDateD8', page:1, top:64.121, left:33.51, w:2.006, fs:7, digit:7, digitKey:'memberSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD1', key:'repSignedDateD1', page:1, top:64.121, left:60.181, w:2.006, fs:7, digit:0, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD2', key:'repSignedDateD2', page:1, top:64.121, left:62.192, w:2.006, fs:7, digit:1, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD3', key:'repSignedDateD3', page:1, top:64.121, left:65.362, w:2.006, fs:7, digit:2, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD4', key:'repSignedDateD4', page:1, top:64.121, left:67.374, w:2.006, fs:7, digit:3, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD5', key:'repSignedDateD5', page:1, top:64.121, left:70.539, w:2.006, fs:7, digit:4, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD6', key:'repSignedDateD6', page:1, top:64.121, left:72.55, w:2.006, fs:7, digit:5, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD7', key:'repSignedDateD7', page:1, top:64.121, left:74.557, w:2.006, fs:7, digit:6, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'repSignedDateD8', key:'repSignedDateD8', page:1, top:64.121, left:76.569, w:2.006, fs:7, digit:7, digitKey:'repSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'memberSignerTypeMember', key:'memberSignerType', page:1, top:72.16, left:3.986, w:2.006, fs:9, checkbox:true, checkValue:'Member', center:true },
  { id:'memberSignerTypeRep', key:'memberSignerType', page:1, top:72.16, left:11.982, w:2.006, fs:9, checkbox:true, checkValue:'Representative', center:true },
  { id:'repRelSpouse', key:'repRelationship', page:1, top:67.316, left:64.745, w:2.006, fs:8, checkbox:true, checkValue:'Spouse', center:true },
  { id:'repRelChild', key:'repRelationship', page:1, top:67.316, left:72.33, w:2.006, fs:8, checkbox:true, checkValue:'Child', center:true },
  { id:'repRelParent', key:'repRelationship', page:1, top:67.316, left:78.627, w:2.006, fs:8, checkbox:true, checkValue:'Parent', center:true },
  { id:'repRelSibling', key:'repRelationship', page:1, top:68.854, left:64.745, w:2.006, fs:8, checkbox:true, checkValue:'Sibling', center:true },
  { id:'repRelOthers', key:'repRelationship', page:1, top:68.854, left:72.33, w:2.006, fs:8, checkbox:true, checkValue:'Others', center:true },
  { id:'repRelationshipOther', key:'repRelationshipOther', page:1, top:68.716, left:82.58, w:12.17, fs:7 },
  { id:'repReasonIncap', key:'repReason', page:1, top:70.735, left:64.745, w:2.006, fs:8, checkbox:true, checkValue:'Incapacitated', center:true },
  { id:'repReasonOther', key:'repReason', page:1, top:72.273, left:64.745, w:2.006, fs:8, checkbox:true, checkValue:'Other', center:true },
  { id:'repReasonOtherText', key:'repReasonOther', page:1, top:71.916, left:74.92, w:19.86, fs:7 },

  // ═══ Part IV – Employer's Certification (employed members only) ═══
  // 1. PhilHealth Employer Number (PEN) — 12 digit boxes
  { id:'employerPENc1', key:'employerPENc1', page:1, top:76.61, left:32.124, w:2.006, fs:8, digit:0, digitKey:'employerPEN', center:true },
  { id:'employerPENc2', key:'employerPENc2', page:1, top:76.61, left:34.133, w:2.006, fs:8, digit:1, digitKey:'employerPEN', center:true },
  { id:'employerPENc3', key:'employerPENc3', page:1, top:76.61, left:37.412, w:2.006, fs:8, digit:2, digitKey:'employerPEN', center:true },
  { id:'employerPENc4', key:'employerPENc4', page:1, top:76.61, left:39.421, w:2.006, fs:8, digit:3, digitKey:'employerPEN', center:true },
  { id:'employerPENc5', key:'employerPENc5', page:1, top:76.61, left:41.422, w:2.006, fs:8, digit:4, digitKey:'employerPEN', center:true },
  { id:'employerPENc6', key:'employerPENc6', page:1, top:76.61, left:43.431, w:2.006, fs:8, digit:5, digitKey:'employerPEN', center:true },
  { id:'employerPENc7', key:'employerPENc7', page:1, top:76.61, left:45.432, w:2.006, fs:8, digit:6, digitKey:'employerPEN', center:true },
  { id:'employerPENc8', key:'employerPENc8', page:1, top:76.61, left:47.442, w:2.006, fs:8, digit:7, digitKey:'employerPEN', center:true },
  { id:'employerPENc9', key:'employerPENc9', page:1, top:76.61, left:49.443, w:2.006, fs:8, digit:8, digitKey:'employerPEN', center:true },
  { id:'employerPENc10', key:'employerPENc10', page:1, top:76.61, left:51.452, w:2.006, fs:8, digit:9, digitKey:'employerPEN', center:true },
  { id:'employerPENc11', key:'employerPENc11', page:1, top:76.61, left:53.453, w:2.006, fs:8, digit:10, digitKey:'employerPEN', center:true },
  { id:'employerPENc12', key:'employerPENc12', page:1, top:76.61, left:56.62, w:2.006, fs:8, digit:11, digitKey:'employerPEN', center:true },
  { id:'employerPhone', key:'employerPhone', page:1, top:76.24, left:74.94, w:21.31, fs:8 },
  { id:'employerName', key:'employerName', page:1, top:79.96, left:11.37, w:77.35, fs:8, center:true },
  { id:'employerRepName', key:'employerRepName', page:1, top:88.84, left:4.19, w:36.04, fs:7, center:true },
  { id:'employerCapacity', key:'employerCapacity', page:1, top:88.84, left:42.36, w:24.84, fs:7, center:true },
  { id:'employerSignedDateD1', key:'employerSignedDateD1', page:1, top:88.674, left:76.598, w:2.006, fs:7, digit:0, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD2', key:'employerSignedDateD2', page:1, top:88.674, left:78.61, w:2.006, fs:7, digit:1, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD3', key:'employerSignedDateD3', page:1, top:88.674, left:81.78, w:2.006, fs:7, digit:2, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD4', key:'employerSignedDateD4', page:1, top:88.674, left:83.791, w:2.006, fs:7, digit:3, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD5', key:'employerSignedDateD5', page:1, top:88.674, left:86.956, w:2.006, fs:7, digit:4, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD6', key:'employerSignedDateD6', page:1, top:88.674, left:88.968, w:2.006, fs:7, digit:5, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD7', key:'employerSignedDateD7', page:1, top:88.674, left:90.975, w:2.006, fs:7, digit:6, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
  { id:'employerSignedDateD8', key:'employerSignedDateD8', page:1, top:88.674, left:92.986, w:2.006, fs:7, digit:7, digitKey:'employerSignedDate', digitOrder:'mmddyyyy', center:true },
];
