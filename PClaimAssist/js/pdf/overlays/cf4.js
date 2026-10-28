/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map — CF4 (Claim Form 4, February 2020)
   Page size 612 x 1008 pt, 2 pages.

   The 2020 form has no fillable boxes, so positions were measured from
   the blank page itself: tick marks and digits are centred in the
   printed squares (each tick box found by the label printed beside
   it), and text sits on the baseline the clinic's own filled copy used
   or just above its ruled line. Name parts and address parts are
   centred in their columns. Course in the ward (15 lines) and the drug
   list (7 drugs, two lines each) are written as short lines inside the
   form's one course box and three drug rows.

   Checkboxes use checkbox:true + checkValue; the renderer draws a
   check glyph when state[key] matches checkValue. Multi-select
   groups (signs & symptoms, PE findings) use checkboxMulti:true,
   where state[key] is an array and the mark is drawn when the
   array contains checkValue.
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF4 = [
  // 5. Height and weight (new on the February 2020 form)
  { id:'cf4Height', key:'cf4Height', page:1, top:84.445, left:86.06, w:2.18, fs:7, center:true },
  { id:'cf4Weight', key:'cf4Weight', page:1, top:85.935, left:82.52, w:5.81, fs:7, center:true },
  /* ═══ PAGE 1 ═══ */


  // I. Health Care Institution (the address is one wide box; each part
  // goes in the column of its printed sub-label underneath)
  { id:'cf4HciName', key:'hciName', page:1, top:14.305, left:4.08, w:53.7, fs:8 },
  { id:'cf4HciPAN', key:'hciPAN', page:1, top:14.305, left:62.09, w:35.0, fs:8 },
  { id:'cf4HciBldg', key:'hciBldg', page:1, top:16.795, left:2.43, w:19.65, fs:6.5, center:true },
  { id:'cf4HciStreet', key:'hciStreet', page:1, top:16.795, left:23.68, w:18.0, fs:6.5, center:true },
  { id:'cf4HciBarangay', key:'hciCity', page:1, top:16.795, left:43.28, w:18.01, fs:6.5, center:true },
  { id:'cf4HciProvince', key:'hciProvince', page:1, top:16.795, left:62.89, w:19.64, fs:6.5, center:true },
  { id:'cf4HciZip', key:'hciZip', page:1, top:16.795, left:84.13, w:13.11, fs:6.5, center:true },

  // II. Patient's Data
  { id:'cf4PatientLastName', key:'patientLastName', page:1, top:21.755, left:2.43, w:21.28, fs:8, center:true},
  { id:'cf4PatientFirstName', key:'patientFirstName', page:1, top:21.755, left:25.31, w:21.28, fs:8, center:true},
  { id:'cf4PatientMiddleName', key:'patientMiddleName', page:1, top:21.755, left:48.19, w:21.27, fs:8, center:true},
  { id:'cf4PatientPIN', key:'memberPIN', page:1, top:21.755, left:71.9, w:25.4, fs:8 },
  { id:'cf4PatientAge', key:'patientAge', page:1, top:24.235, left:72.71, w:24.6, fs:8 },
  { id:'cf4SexMale', key:'patientSex', page:1, top:25.718, left:76.797, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Male' },
  { id:'cf4SexFemale', key:'patientSex', page:1, top:25.718, left:84.967, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Female' },
  { id:'cf4ChiefComplaint', key:'cf4ChiefComplaint', page:1, top:25.125, left:2.45, w:66.8, fs:7, wrap:true, maxLines:2, lines:2, lh:9.2 },
  { id:'cf4AdmittingDx', key:'admissionDx', page:1, top:28.895, left:2.45, w:29.2, fs:7, wrap:true, maxLines:3, lines:7, lh:9.2 },
  { id:'cf4DischargeDx', key:'cf4FinalDiagnosis', page:1, top:28.895, left:34.31, w:34.9, fs:7, wrap:true, maxLines:3, lines:7, lh:9.2 },
  { id:'cf4CaseRate1', key:'cf4IcdCode', page:1, top:28.805, left:72.71, w:24.6, fs:7, center:true },
  { id:'cf4CaseRate2', key:'cf4RvsCode', page:1, top:31.905, left:72.71, w:24.6, fs:7, center:true },

  // 9. Date / Time Admitted — mm dd yyyy, hh mm
  { id:'cf4AdmMM1', key:'cf4AdmMM1', page:1, top:36.609, left:19.608, w:2.451, fs:7, center:true, digit:0, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmMM2', key:'cf4AdmMM2', page:1, top:36.609, left:22.059, w:2.451, fs:7, center:true, digit:1, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmDD1', key:'cf4AdmDD1', page:1, top:36.609, left:26.961, w:2.451, fs:7, center:true, digit:2, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmDD2', key:'cf4AdmDD2', page:1, top:36.609, left:29.412, w:2.451, fs:7, center:true, digit:3, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmYY1', key:'cf4AdmYY1', page:1, top:36.609, left:34.314, w:2.451, fs:7, center:true, digit:4, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmYY2', key:'cf4AdmYY2', page:1, top:36.609, left:36.765, w:2.451, fs:7, center:true, digit:5, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmYY3', key:'cf4AdmYY3', page:1, top:36.609, left:39.216, w:2.451, fs:7, center:true, digit:6, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmYY4', key:'cf4AdmYY4', page:1, top:36.609, left:41.667, w:2.451, fs:7, center:true, digit:7, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' },
  { id:'cf4AdmHH1', key:'cf4AdmHH1', page:1, top:36.411, left:65.359, w:2.451, fs:7, center:true, digit:0, digitKey:'cf4TimeAdmittedDigits' },
  { id:'cf4AdmHH2', key:'cf4AdmHH2', page:1, top:36.411, left:67.81, w:2.451, fs:7, center:true, digit:1, digitKey:'cf4TimeAdmittedDigits' },
  { id:'cf4AdmMI1', key:'cf4AdmMI1', page:1, top:36.411, left:72.712, w:2.451, fs:7, center:true, digit:2, digitKey:'cf4TimeAdmittedDigits' },
  { id:'cf4AdmMI2', key:'cf4AdmMI2', page:1, top:36.411, left:75.163, w:2.451, fs:7, center:true, digit:3, digitKey:'cf4TimeAdmittedDigits' },
  { id:'cf4AdmAM', key:'amPmAdmitted', page:1, top:36.234, left:78.431, w:1.634, fs:9, center:true, checkbox:true, checkValue:'AM' },
  { id:'cf4AdmPM', key:'amPmAdmitted', page:1, top:36.234, left:84.15, w:1.634, fs:9, center:true, checkbox:true, checkValue:'PM' },

  // 10. Date / Time Discharged
  { id:'cf4DisMM1', key:'cf4DisMM1', page:1, top:39.883, left:19.608, w:2.451, fs:7, center:true, digit:0, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisMM2', key:'cf4DisMM2', page:1, top:39.883, left:22.059, w:2.451, fs:7, center:true, digit:1, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisDD1', key:'cf4DisDD1', page:1, top:39.883, left:26.961, w:2.451, fs:7, center:true, digit:2, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisDD2', key:'cf4DisDD2', page:1, top:39.883, left:29.412, w:2.451, fs:7, center:true, digit:3, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisYY1', key:'cf4DisYY1', page:1, top:39.883, left:34.314, w:2.451, fs:7, center:true, digit:4, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisYY2', key:'cf4DisYY2', page:1, top:39.883, left:36.765, w:2.451, fs:7, center:true, digit:5, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisYY3', key:'cf4DisYY3', page:1, top:39.883, left:39.216, w:2.451, fs:7, center:true, digit:6, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisYY4', key:'cf4DisYY4', page:1, top:39.883, left:41.667, w:2.451, fs:7, center:true, digit:7, digitKey:'dateDischarge', digitOrder:'mmddyyyy' },
  { id:'cf4DisHH1', key:'cf4DisHH1', page:1, top:39.883, left:65.359, w:2.451, fs:7, center:true, digit:0, digitKey:'cf4TimeDischargeDigits' },
  { id:'cf4DisHH2', key:'cf4DisHH2', page:1, top:39.883, left:67.81, w:2.451, fs:7, center:true, digit:1, digitKey:'cf4TimeDischargeDigits' },
  { id:'cf4DisMI1', key:'cf4DisMI1', page:1, top:39.883, left:72.712, w:2.451, fs:7, center:true, digit:2, digitKey:'cf4TimeDischargeDigits' },
  { id:'cf4DisMI2', key:'cf4DisMI2', page:1, top:39.883, left:75.163, w:2.451, fs:7, center:true, digit:3, digitKey:'cf4TimeDischargeDigits' },
  { id:'cf4DisAM', key:'amPmDischarge', page:1, top:39.706, left:78.431, w:1.634, fs:9, center:true, checkbox:true, checkValue:'AM' },
  { id:'cf4DisPM', key:'amPmDischarge', page:1, top:39.706, left:84.15, w:1.634, fs:9, center:true, checkbox:true, checkValue:'PM' },

  // III. Reason for Admission
  { id:'cf4HistoryPresentIllness', key:'cf4HistoryPresentIllness', page:1, top:45.405, left:2.45, w:95.0, fs:7, wrap:true, maxLines:9, lines:8, lh:9.2 },
  { id:'cf4PastMedicalHistory', key:'cf4PastMedicalHistory', page:1, top:55.095, left:2.45, w:95.0, fs:7, wrap:true, maxLines:4, lines:5, lh:9.2 },

  // 2.b OB/GYN history: G _ P _ ( _ - _ - _ - _ ) LMP: ____
  { id:'cf4Gravida', key:'gravida', page:1, top:62.305, left:4.75, w:1.6, fs:9 },
  { id:'cf4Para', key:'para', page:1, top:62.305, left:8.02, w:1.6, fs:9 },
  { id:'cf4ObT', key:'obTerm', page:1, top:62.305, left:11.3, w:1.6, fs:9 },
  { id:'cf4ObP', key:'obPreterm', page:1, top:62.305, left:14.57, w:1.6, fs:9 },
  { id:'cf4ObA', key:'obAbortion', page:1, top:62.305, left:17.84, w:1.6, fs:9 },
  { id:'cf4ObL', key:'obLiving', page:1, top:62.305, left:21.12, w:1.6, fs:9 },
  { id:'cf4Lmp', key:'lmp', page:1, top:62.205, left:31.13, w:8.3, fs:8 },
  { id:'cf4LmpNA', key:'cf4LmpNA', page:1, top:62.226, left:42.484, w:1.634, fs:9, center:true, checkbox:true, checkValue:true },

  // 3. Pertinent signs and symptoms — 4 columns x 9 rows (multi-select)
  { id:'cf4Sym_0_0', key:'cf4Symptoms', page:1, top:65.698, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Altered mental sensorium' },
  { id:'cf4Sym_0_1', key:'cf4Symptoms', page:1, top:65.698, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abdominal cramp/pain' },
  { id:'cf4Sym_0_2', key:'cf4Symptoms', page:1, top:65.698, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Anorexia' },
  { id:'cf4Sym_0_3', key:'cf4Symptoms', page:1, top:65.698, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Bleeding gums' },
  { id:'cf4Sym_0_4', key:'cf4Symptoms', page:1, top:67.187, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Body weakness' },
  { id:'cf4Sym_0_5', key:'cf4Symptoms', page:1, top:67.187, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Blurring of vision' },
  { id:'cf4Sym_0_6', key:'cf4Symptoms', page:1, top:67.187, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Chest pain/discomfort' },
  { id:'cf4Sym_0_7', key:'cf4Symptoms', page:1, top:67.187, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Constipation' },
  { id:'cf4Sym_0_8', key:'cf4Symptoms', page:1, top:68.675, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Cough' },
  { id:'cf4Sym_1_0', key:'cf4Symptoms', page:1, top:68.675, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Diarrhea' },
  { id:'cf4Sym_1_1', key:'cf4Symptoms', page:1, top:68.675, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Dizziness' },
  { id:'cf4Sym_1_2', key:'cf4Symptoms', page:1, top:68.675, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Dysphagia' },
  { id:'cf4Sym_1_3', key:'cf4Symptoms', page:1, top:70.163, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Dyspnea' },
  { id:'cf4Sym_1_4', key:'cf4Symptoms', page:1, top:70.163, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Dysuria' },
  { id:'cf4Sym_1_5', key:'cf4Symptoms', page:1, top:70.163, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Epistaxis' },
  { id:'cf4Sym_1_6', key:'cf4Symptoms', page:1, top:70.163, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Fever' },
  { id:'cf4Sym_1_7', key:'cf4Symptoms', page:1, top:71.651, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Frequency of urination' },
  { id:'cf4Sym_1_8', key:'cf4Symptoms', page:1, top:71.651, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Headache' },
  { id:'cf4Sym_2_0', key:'cf4Symptoms', page:1, top:71.651, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Hematemesis' },
  { id:'cf4Sym_2_1', key:'cf4Symptoms', page:1, top:71.651, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Hematuria' },
  { id:'cf4Sym_2_2', key:'cf4Symptoms', page:1, top:73.139, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Hemoptysis' },
  { id:'cf4Sym_2_3', key:'cf4Symptoms', page:1, top:73.139, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Irritability' },
  { id:'cf4Sym_2_4', key:'cf4Symptoms', page:1, top:73.139, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Jaundice' },
  { id:'cf4Sym_2_5', key:'cf4Symptoms', page:1, top:73.139, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Lower extremity edema' },
  { id:'cf4Sym_2_6', key:'cf4Symptoms', page:1, top:74.627, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Myalgia' },
  { id:'cf4Sym_2_7', key:'cf4Symptoms', page:1, top:74.627, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Orthopnea' },
  { id:'cf4Sym_2_8', key:'cf4Symptoms', page:1, top:77.603, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Pain' },
  { id:'cf4Sym_3_0', key:'cf4Symptoms', page:1, top:74.627, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Palpitations' },
  { id:'cf4Sym_3_1', key:'cf4Symptoms', page:1, top:74.627, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Seizures' },
  { id:'cf4Sym_3_2', key:'cf4Symptoms', page:1, top:76.115, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Skin rashes' },
  { id:'cf4Sym_3_3', key:'cf4Symptoms', page:1, top:76.115, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Stool, bloody/black tarry/mucoid' },
  { id:'cf4Sym_3_4', key:'cf4Symptoms', page:1, top:76.115, left:50.654, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Sweating' },
  { id:'cf4Sym_3_5', key:'cf4Symptoms', page:1, top:76.115, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Urgency' },
  { id:'cf4Sym_3_6', key:'cf4Symptoms', page:1, top:77.603, left:3.268, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Vomiting' },
  { id:'cf4Sym_3_7', key:'cf4Symptoms', page:1, top:77.603, left:26.144, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Weight loss' },
  { id:'cf4Sym_3_8', key:'cf4Symptoms', page:1, top:77.603, left:73.529, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Others' },
  { id:'cf4PainSite', key:'cf4PainSite', page:1, top:77.555, left:57.19, w:10.9, fs:6.5, center:true },
  { id:'cf4SymptomOther', key:'cf4SymptomOther', page:1, top:77.555, left:80.88, w:14.5, fs:6.5 },

  // 4. Referred from another HCI
  { id:'cf4RefNo', key:'cf4Referred', page:1, top:79.885, left:37.582, w:1.634, fs:9, center:true, checkbox:true, checkValue:'No' },
  { id:'cf4RefYes', key:'cf4Referred', page:1, top:80.034, left:44.118, w:2.124, fs:9, center:true, checkbox:true, checkValue:'Yes' },
  { id:'cf4RefReason', key:'cf4ReferralReason', page:1, top:80.255, left:62.09, w:33.4, fs:7 },
  { id:'cf4RefHci', key:'cf4ReferralHci', page:1, top:81.455, left:65.36, w:29.8, fs:7 },

  // 5. Physical examination on admission
  { id:'cf4PeAwake', key:'cf4GeneralSurvey', page:1, top:85.54, left:17.974, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Awake and alert' },
  { id:'cf4PeAltered', key:'cf4GeneralSurvey', page:1, top:85.54, left:37.582, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Altered sensorium' },
  { id:'cf4PeAlteredTxt', key:'cf4AlteredSensorium', page:1, top:85.705, left:55.56, w:16.7, fs:6.5 },
  { id:'cf4VsBP', key:'cf4VitalBP', page:1, top:87.885, left:20.42, w:16.0, fs:7, center:true },
  { id:'cf4VsHR', key:'cf4VitalHR', page:1, top:87.885, left:40.03, w:16.0, fs:7, center:true },
  { id:'cf4VsRR', key:'cf4VitalRR', page:1, top:87.885, left:59.64, w:14.54, fs:7, center:true },
  { id:'cf4VsTemp', key:'cf4VitalTemp', page:1, top:87.885, left:79.25, w:13.08, fs:7, center:true },
  { id:'cf4Heent0', key:'cf4Heent', page:1, top:90.599, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Heent1', key:'cf4Heent', page:1, top:90.599, left:55.556, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abnormal pupillary reaction' },
  { id:'cf4Heent2', key:'cf4Heent', page:1, top:92.583, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Cervical lymphadenopathy' },
  { id:'cf4Heent3', key:'cf4Heent', page:1, top:92.583, left:55.556, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Dry mucous membrane' },
  { id:'cf4Heent4', key:'cf4Heent', page:1, top:90.599, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Icteric sclerae' },
  { id:'cf4Heent5', key:'cf4Heent', page:1, top:90.599, left:75.163, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Pale conjunctivae' },
  { id:'cf4Heent6', key:'cf4Heent', page:1, top:92.583, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Sunken eyeballs' },
  { id:'cf4Heent7', key:'cf4Heent', page:1, top:92.583, left:75.163, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Sunken fontanelle' },
  { id:'cf4HeentOthers', key:'cf4HeentOthers', page:1, top:94.345, left:22.88, w:13.08, fs:6.5 },

  /* ═══ PAGE 2 ═══ */

  // 5. Physical examination continued — six systems, multi-select
  { id:'cf4Chest_0_0', key:'cf4Chest', page:2, top:4.29, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Chest_0_1', key:'cf4Chest', page:2, top:4.29, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Asymmetrical chest expansion' },
  { id:'cf4Chest_0_2', key:'cf4Chest', page:2, top:5.778, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Decreased breath sounds' },
  { id:'cf4Chest_0_3', key:'cf4Chest', page:2, top:5.778, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Wheezes' },
  { id:'cf4Chest_1_0', key:'cf4Chest', page:2, top:4.29, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Lump/s over breast(s)' },
  { id:'cf4Chest_1_1', key:'cf4Chest', page:2, top:4.29, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Rales/crackles/rhonchi' },
  { id:'cf4Chest_1_2', key:'cf4Chest', page:2, top:5.778, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Intercostal rib/clavicular retraction' },
  { id:'cf4ChestOthers', key:'cf4ChestOthers', page:2, top:7.045, left:22.88, w:13.08, fs:6.5 },
  { id:'cf4Cvs_0_0', key:'cf4Cvs', page:2, top:8.754, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Cvs_0_1', key:'cf4Cvs', page:2, top:8.754, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Displaced apex beat' },
  { id:'cf4Cvs_0_2', key:'cf4Cvs', page:2, top:10.242, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Heaves and/or thrills' },
  { id:'cf4Cvs_0_3', key:'cf4Cvs', page:2, top:10.242, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Pericardial bulge' },
  { id:'cf4Cvs_1_0', key:'cf4Cvs', page:2, top:8.754, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Irregular rhythm' },
  { id:'cf4Cvs_1_1', key:'cf4Cvs', page:2, top:8.754, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Muffled heart sounds' },
  { id:'cf4Cvs_1_2', key:'cf4Cvs', page:2, top:10.242, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Murmur' },
  { id:'cf4CvsOthers', key:'cf4CvsOthers', page:2, top:11.505, left:22.88, w:13.08, fs:6.5 },
  { id:'cf4Abdomen_0_0', key:'cf4Abdomen', page:2, top:13.218, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Abdomen_0_1', key:'cf4Abdomen', page:2, top:13.218, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abdominal rigidity' },
  { id:'cf4Abdomen_0_2', key:'cf4Abdomen', page:2, top:14.706, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abdomen tenderness' },
  { id:'cf4Abdomen_0_3', key:'cf4Abdomen', page:2, top:14.706, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Hyperactive bowel sounds' },
  { id:'cf4Abdomen_1_0', key:'cf4Abdomen', page:2, top:13.218, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Palpable mass(es)' },
  { id:'cf4Abdomen_1_1', key:'cf4Abdomen', page:2, top:13.218, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Tympanitic/dull abdomen' },
  { id:'cf4Abdomen_1_2', key:'cf4Abdomen', page:2, top:14.706, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Uterine contraction' },
  { id:'cf4AbdomenOthers', key:'cf4AbdomenOthers', page:2, top:15.975, left:22.88, w:13.08, fs:6.5 },
  { id:'cf4Gu_0_0', key:'cf4Gu', page:2, top:17.683, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Gu_0_1', key:'cf4Gu', page:2, top:17.683, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Blood stained in exam finger' },
  { id:'cf4Gu_0_2', key:'cf4Gu', page:2, top:17.683, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Cervical dilatation' },
  { id:'cf4Gu_0_3', key:'cf4Gu', page:2, top:17.683, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Presence of abnormal discharge' },
  { id:'cf4GuOthers', key:'cf4GuOthers', page:2, top:18.945, left:22.88, w:13.08, fs:6.5 },
  { id:'cf4Skin_0_0', key:'cf4Skin', page:2, top:20.659, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Skin_0_1', key:'cf4Skin', page:2, top:20.659, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Clubbing' },
  { id:'cf4Skin_0_2', key:'cf4Skin', page:2, top:22.147, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Cold clammy skin' },
  { id:'cf4Skin_0_3', key:'cf4Skin', page:2, top:23.635, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Cyanosis/mottled skin' },
  { id:'cf4Skin_1_0', key:'cf4Skin', page:2, top:20.659, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Edema/swelling' },
  { id:'cf4Skin_1_1', key:'cf4Skin', page:2, top:22.048, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Decreased mobility' },
  { id:'cf4Skin_1_2', key:'cf4Skin', page:2, top:22.147, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Pale nailbeds' },
  { id:'cf4Skin_1_3', key:'cf4Skin', page:2, top:23.635, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Poor skin turgor' },
  { id:'cf4Skin_2_0', key:'cf4Skin', page:2, top:20.659, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Rashes/petechiae' },
  { id:'cf4Skin_2_1', key:'cf4Skin', page:2, top:22.147, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Weak pulses' },
  { id:'cf4SkinOthers', key:'cf4SkinOthers', page:2, top:24.895, left:22.88, w:13.08, fs:6.5 },
  { id:'cf4Neuro_0_0', key:'cf4Neuro', page:2, top:26.611, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Essentially normal' },
  { id:'cf4Neuro_0_1', key:'cf4Neuro', page:2, top:26.611, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abnormal gait' },
  { id:'cf4Neuro_0_2', key:'cf4Neuro', page:2, top:28.099, left:17.974, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abnormal position sense' },
  { id:'cf4Neuro_0_3', key:'cf4Neuro', page:2, top:28.099, left:57.19, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abnormal/decreased sensation' },
  { id:'cf4Neuro_1_0', key:'cf4Neuro', page:2, top:26.611, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Abnormal reflex(es)' },
  { id:'cf4Neuro_1_1', key:'cf4Neuro', page:2, top:26.611, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Poor/altered memory' },
  { id:'cf4Neuro_1_2', key:'cf4Neuro', page:2, top:28.099, left:36.601, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Poor muscle tone/strength' },
  { id:'cf4Neuro_1_3', key:'cf4Neuro', page:2, top:28.099, left:76.797, w:1.634, fs:9, center:true, checkboxMulti:true, checkValue:'Poor coordination' },
  { id:'cf4NeuroOthers', key:'cf4NeuroOthers', page:2, top:29.365, left:22.88, w:13.08, fs:6.5 },

  // IV. Course in the ward — two boxes (date + doctor's order)
  // The form's two boxes under Date / Doctor's order: the big one (337.6-420.4pt)
  // and the small one below it (421.6-443.6pt). Each order wraps onto the lines
  // its own box holds; each date prints month-day-year.
  { id:'cf4CourseDate1', key:'cf4CourseDate1', computed:'cf4CourseDate1', page:2, top:33.58, left:2.2, w:23.4, fs:6 },
  { id:'cf4CourseOrder1', key:'cf4CourseOrder1', page:2, top:33.58, left:26.7, w:70.8, fs:6, wrap:true, lines:11, lh:6.85 },
  { id:'cf4CourseDate2', key:'cf4CourseDate2', computed:'cf4CourseDate2', page:2, top:42.02, left:2.2, w:23.4, fs:6 },
  { id:'cf4CourseOrder2', key:'cf4CourseOrder2', page:2, top:42.02, left:26.7, w:70.8, fs:6, wrap:true, lines:2, lh:7.5 },
  { id:'cf4SurgicalProcedure', key:'cf4SurgicalProcedure', page:2, top:44.365, left:47.55, w:50.3, fs:7, wrap:true, lines:2, lh:9.2 },

  // V. Drugs / medicines - the form's three printed rows, one medicine each:
  // generic name | quantity over dosage / route | total cost, near the middle
  // of each 35pt row. A long name wraps onto a second line, then prints
  // smaller, inside its own cell; a long dosage / route prints smaller.
  { id:'cf4DrugName1', key:'cf4DrugName1', page:2, top:49.82, left:2.2, w:35.0, fs:7, wrap:true, lines:2, lh:9, center:true },
  { id:'cf4DrugQty1', key:'cf4DrugQty1', page:2, top:49.424, left:38.2, w:43.0, fs:7, center:true },
  { id:'cf4DrugDose1', key:'cf4DrugDose1', page:2, top:50.317, left:38.2, w:43.0, fs:7, center:true },
  { id:'cf4DrugCost1', key:'cf4DrugCost1', page:2, top:49.82, left:82.3, w:15.2, fs:7, center:true },
  { id:'cf4DrugName2', key:'cf4DrugName2', page:2, top:53.293, left:2.2, w:35.0, fs:7, wrap:true, lines:2, lh:9, center:true },
  { id:'cf4DrugQty2', key:'cf4DrugQty2', page:2, top:52.896, left:38.2, w:43.0, fs:7, center:true },
  { id:'cf4DrugDose2', key:'cf4DrugDose2', page:2, top:53.789, left:38.2, w:43.0, fs:7, center:true },
  { id:'cf4DrugCost2', key:'cf4DrugCost2', page:2, top:53.293, left:82.3, w:15.2, fs:7, center:true },
  { id:'cf4DrugName3', key:'cf4DrugName3', page:2, top:56.765, left:2.2, w:35.0, fs:7, wrap:true, lines:2, lh:9, center:true },
  { id:'cf4DrugQty3', key:'cf4DrugQty3', page:2, top:56.368, left:38.2, w:43.0, fs:7, center:true },
  { id:'cf4DrugDose3', key:'cf4DrugDose3', page:2, top:57.261, left:38.2, w:43.0, fs:7, center:true },
  { id:'cf4DrugCost3', key:'cf4DrugCost3', page:2, top:56.765, left:82.3, w:15.2, fs:7, center:true },

  // VI. Outcome of treatment
  { id:'cf4OutImproved', key:'disposition', page:2, top:61.929, left:3.268, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Improved' },
  { id:'cf4OutHama', key:'disposition', page:2, top:61.929, left:16.34, w:1.634, fs:9, center:true, checkbox:true, checkValue:'HAMA' },
  { id:'cf4OutExpired', key:'disposition', page:2, top:61.929, left:29.412, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Expired' },
  { id:'cf4OutAbsconded', key:'disposition', page:2, top:61.929, left:42.484, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Absconded' },
  { id:'cf4OutTransferred', key:'disposition', page:2, top:61.929, left:57.19, w:1.634, fs:9, center:true, checkbox:true, checkValue:'Transferred' },
  { id:'cf4TransferReason', key:'cf4TransferReason', page:2, top:62.255, left:81.7, w:14.54, fs:6.5 },

  // VII. Certification — name is typed; the signature itself stays wet-ink
  { id:'cf4AttendingProvider', key:'cf4AttendingProvider', page:2, top:70.105, left:4.9, w:45.79, fs:7, center:true},
  { id:'cf4SignMM1', key:'cf4SignMM1', page:2, top:70.538, left:68.627, w:2.451, fs:7, center:true, digit:0, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignMM2', key:'cf4SignMM2', page:2, top:70.538, left:71.078, w:2.451, fs:7, center:true, digit:1, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignDD1', key:'cf4SignDD1', page:2, top:70.538, left:75.98, w:2.451, fs:7, center:true, digit:2, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignDD2', key:'cf4SignDD2', page:2, top:70.538, left:78.431, w:2.451, fs:7, center:true, digit:3, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignYY1', key:'cf4SignYY1', page:2, top:70.538, left:83.333, w:2.451, fs:7, center:true, digit:4, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignYY2', key:'cf4SignYY2', page:2, top:70.538, left:85.784, w:2.451, fs:7, center:true, digit:5, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignYY3', key:'cf4SignYY3', page:2, top:70.538, left:88.235, w:2.451, fs:7, center:true, digit:6, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
  { id:'cf4SignYY4', key:'cf4SignYY4', page:2, top:70.538, left:90.686, w:2.451, fs:7, center:true, digit:7, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' },
];
