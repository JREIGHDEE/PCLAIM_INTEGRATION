/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map — CF4 (Claim Form 4, Aug 2018)
   Page size 612 x 1008 pt, 2 pages.

   Coordinates derived from the actual PDF via PyMuPDF
   (page.get_text('words') for labels, page.get_drawings() for
   the checkbox rects and table rules), so they line up with the
   printed form rather than being eyeballed.

   Checkboxes use checkbox:true + checkValue; the renderer draws a
   check glyph when state[key] matches checkValue. Multi-select
   groups (signs & symptoms, PE findings) use checkboxMulti:true,
   where state[key] is an array and the mark is drawn when the
   array contains checkValue.
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF4 = [
  /* ═══ PAGE 1 ═══ */

  // Series # — 13 digit boxes across the top
  ...[0,1,2,3,4,5,6,7,8,9,10,11,12].map(i => ({
    id:'cf4SeriesD' + (i+1), key:'cf4SeriesD' + (i+1), page:1,
    top:9.25, left:66.2 + i*2.19, w:2.0, fs:7,
    digit:i, digitKey:'cf4Series',
  })),

  // I. Health Care Institution
  { id:'cf4HciName',    key:'hciName',    page:1, top:16.3, left:6.3,  w:50.0, fs:8 },
  { id:'cf4HciPAN',     key:'hciPAN',     page:1, top:16.3, left:61.2, w:30.0, fs:8 },
  { id:'cf4HciBldg',    key:'hciBldg',    page:1, top:20, left:4.5,  w:16.0, fs:6.5 },
  { id:'cf4HciStreet',  key:'hciStreet',  page:1, top:20, left:21.5, w:17.0, fs:6.5 },
  { id:'cf4HciBarangay',key:'hciCity',    page:1, top:20, left:39.5, w:21.0, fs:6.5 },
  { id:'cf4HciProvince',key:'hciProvince',page:1, top:20, left:61.5, w:19.0, fs:6.5 },
  { id:'cf4HciZip',     key:'hciZip',     page:1, top:20, left:81.5, w:12.0, fs:6.5 },

  // II. Patient's Data
  { id:'cf4PatientLastName',   key:'patientLastName',   page:1, top:24.2, left:5.0,  w:21.0, fs:8 },
  { id:'cf4PatientFirstName',  key:'patientFirstName',  page:1, top:24.2, left:26.5, w:21.0, fs:8 },
  { id:'cf4PatientMiddleName', key:'patientMiddleName', page:1, top:24.2, left:48.5, w:21.0, fs:8 },
  { id:'cf4PatientPIN',        key:'memberPIN',         page:1, top:24.3, left:72.2, w:25.0, fs:8 },
  { id:'cf4PatientAge',        key:'patientAge',        page:1, top:26.6, left:76.5, w:8.0,  fs:8 },

  { id:'cf4SexMale',   key:'patientSex', page:1, top:27.95, left:79.5, w:2, fs:9, checkbox:true, checkValue:'Male' },
  { id:'cf4SexFemale', key:'patientSex', page:1, top:27.95, left:85.4, w:2, fs:9, checkbox:true, checkValue:'Female' },

  { id:'cf4ChiefComplaint', key:'cf4ChiefComplaint', page:1, top:27.3, left:6.3, w:62.0, fs:7, wrap:true, maxLines:2 },
  { id:'cf4AdmittingDx',    key:'admissionDx',       page:1, top:30.7, left:6.3, w:31.0, fs:7, wrap:true, maxLines:3 },
  { id:'cf4DischargeDx',    key:'cf4FinalDiagnosis', page:1, top:30.7, left:39.0, w:33.0, fs:7, wrap:true, maxLines:3 },
  { id:'cf4CaseRate1',      key:'cf4IcdCode',        page:1, top:30.9, left:75.7, w:22.0, fs:7 },
  { id:'cf4CaseRate2',      key:'cf4RvsCode',        page:1, top:33.2, left:76.1, w:22.0, fs:7 },

  // 9. Date / Time Admitted — mm dd yyyy, hh mm
  ...[0,1].map(i => ({ id:'cf4AdmMM'+(i+1), key:'cf4AdmMM'+(i+1), page:1, top:35.15, left:19.2+i*2.18, w:2, fs:7, digit:i,   digitKey:'dateAdmitted', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4AdmDD'+(i+1), key:'cf4AdmDD'+(i+1), page:1, top:35.15, left:24.9+i*2.18, w:2, fs:7, digit:i+2, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' })),
  ...[0,1,2,3].map(i => ({ id:'cf4AdmYY'+(i+1), key:'cf4AdmYY'+(i+1), page:1, top:35.15, left:30.6+i*2.18, w:2, fs:7, digit:i+4, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4AdmHH'+(i+1), key:'cf4AdmHH'+(i+1), page:1, top:35.15, left:68.8+i*2.18, w:2, fs:7, digit:i,   digitKey:'cf4TimeAdmittedDigits' })),
  ...[0,1].map(i => ({ id:'cf4AdmMI'+(i+1), key:'cf4AdmMI'+(i+1), page:1, top:35.15, left:74.5+i*2.18, w:2, fs:7, digit:i+2, digitKey:'cf4TimeAdmittedDigits' })),
  { id:'cf4AdmAM', key:'amPmAdmitted', page:1, top:35.05, left:79.3, w:2, fs:9, checkbox:true, checkValue:'AM' },
  { id:'cf4AdmPM', key:'amPmAdmitted', page:1, top:35.05, left:83.75, w:2, fs:9, checkbox:true, checkValue:'PM' },

  // 10. Date / Time Discharged
  ...[0,1].map(i => ({ id:'cf4DisMM'+(i+1), key:'cf4DisMM'+(i+1), page:1, top:37.48, left:19.2+i*2.18, w:2, fs:7, digit:i,   digitKey:'dateDischarge', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4DisDD'+(i+1), key:'cf4DisDD'+(i+1), page:1, top:37.48, left:24.9+i*2.18, w:2, fs:7, digit:i+2, digitKey:'dateDischarge', digitOrder:'mmddyyyy' })),
  ...[0,1,2,3].map(i => ({ id:'cf4DisYY'+(i+1), key:'cf4DisYY'+(i+1), page:1, top:37.48, left:30.6+i*2.18, w:2, fs:7, digit:i+4, digitKey:'dateDischarge', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4DisHH'+(i+1), key:'cf4DisHH'+(i+1), page:1, top:37.48, left:68.8+i*2.18, w:2, fs:7, digit:i,   digitKey:'cf4TimeDischargeDigits' })),
  ...[0,1].map(i => ({ id:'cf4DisMI'+(i+1), key:'cf4DisMI'+(i+1), page:1, top:37.48, left:74.5+i*2.18, w:2, fs:7, digit:i+2, digitKey:'cf4TimeDischargeDigits' })),
  { id:'cf4DisAM', key:'amPmDischarge', page:1, top:37.42, left:79.3, w:2, fs:9, checkbox:true, checkValue:'AM' },
  { id:'cf4DisPM', key:'amPmDischarge', page:1, top:37.42, left:83.75, w:2, fs:9, checkbox:true, checkValue:'PM' },

  // III. Reason for Admission
  { id:'cf4HistoryPresentIllness', key:'cf4HistoryPresentIllness', page:1, top:42.1, left:5.5, w:89.0, fs:7, wrap:true, maxLines:9 },
  { id:'cf4PastMedicalHistory',    key:'cf4PastMedicalHistory',    page:1, top:53, left:5.5, w:89.0, fs:7, wrap:true, maxLines:4 },

  // 2.b OB/GYN history: G _ P _ ( _ - _ - _ - _ ) LMP: ____
  { id:'cf4Gravida', key:'gravida', page:1, top:59.15, left:9.6,  w:4.0, fs:7 },
  { id:'cf4Para',    key:'para',    page:1, top:59.15, left:15.3, w:4.0, fs:7 },
  { id:'cf4ObT',     key:'obTerm',      page:1, top:59.15, left:21.0, w:3.5, fs:7 },
  { id:'cf4ObP',     key:'obPreterm',   page:1, top:59.15, left:25.8, w:3.5, fs:7 },
  { id:'cf4ObA',     key:'obAbortion',  page:1, top:59.15, left:30.3, w:3.5, fs:7 },
  { id:'cf4ObL',     key:'obLiving',    page:1, top:59.15, left:34.8, w:3.5, fs:7 },
  { id:'cf4Lmp',     key:'lmp',         page:1, top:59.15, left:40.0, w:16.0, fs:7 },
  { id:'cf4LmpNA',   key:'cf4LmpNA',    page:1, top:59, left:51.7, w:2, fs:9, checkbox:true, checkValue:true },

  // 3. Pertinent signs and symptoms — 4 columns x 12 rows (multi-select)
  ...(() => {
    const COLS = [
      { left:5.78,  items:['Altered mental sensorium','Abdominal cramp/pain','Anorexia','Bleeding gums','Body weakness','Blurring of vision','Chest pain/discomfort','Constipation','Cough'] },
      { left:26.39, items:['Diarrhea','Dizziness','Dysphagia','Dyspnea','Dysuria','Epistaxis','Fever','Frequency of urination','Headache'] },
      { left:45.84, items:['Hematemesis','Hematuria','Hemoptysis','Irritability','Jaundice','Lower extremity edema','Myalgia','Orthopnea','Pain'] },
      { left:65.73, items:['Palpitations','Seizures','Skin rashes','Stool, bloody/black tarry/mucoid','Sweating','Urgency','Vomiting','Weight loss','Others'] },
    ];
    const TOPS = [63.36, 64.98, 66.62, 68.25, 69.96, 71.58, 73.23, 74.85, 76.61];
    const out = [];
    COLS.forEach((col, ci) => col.items.forEach((label, ri) => out.push({
      id: `cf4Sym_${ci}_${ri}`, key:'cf4Symptoms', page:1,
      top: TOPS[ri], left: col.left, w:2, fs:9,
      checkboxMulti:true, checkValue:label,
    })));
    return out;
  })(),
  { id:'cf4PainSite',    key:'cf4PainSite',    page:1, top:76.65, left:49.5, w:12.0, fs:6.5 },
  { id:'cf4SymptomOther',key:'cf4SymptomOther',page:1, top:76.65, left:69.5, w:24.0, fs:6.5 },

  // 4. Referred from another HCI
  { id:'cf4RefNo',  key:'cf4Referred', page:1, top:80.42, left:37.3, w:2, fs:9, checkbox:true, checkValue:'No' },
  { id:'cf4RefYes', key:'cf4Referred', page:1, top:80.42, left:43.3, w:2, fs:9, checkbox:true, checkValue:'Yes' },
  { id:'cf4RefReason', key:'cf4ReferralReason', page:1, top:80.5, left:62.0, w:32.0, fs:7 },
  { id:'cf4RefHci',    key:'cf4ReferralHci',    page:1, top:82.25, left:62.0, w:32.0, fs:7 },

  // 5. Physical examination on admission
  { id:'cf4PeAwake',    key:'cf4GeneralSurvey', page:1, top:86.73, left:19.0, w:2, fs:9, checkbox:true, checkValue:'Awake and alert' },
  { id:'cf4PeAltered',  key:'cf4GeneralSurvey', page:1, top:86.73, left:37.1, w:2, fs:9, checkbox:true, checkValue:'Altered sensorium' },
  { id:'cf4PeAlteredTxt', key:'cf4AlteredSensorium', page:1, top:86.75, left:48.5, w:26.0, fs:6.5 },

  { id:'cf4VsBP',   key:'cf4VitalBP',   page:1, top:88.45, left:23.0, w:13.0, fs:7 },
  { id:'cf4VsHR',   key:'cf4VitalHR',   page:1, top:88.45, left:41.0, w:10.0, fs:7 },
  { id:'cf4VsRR',   key:'cf4VitalRR',   page:1, top:88.45, left:56.0, w:11.0, fs:7 },
  { id:'cf4VsTemp', key:'cf4VitalTemp', page:1, top:88.45, left:72.5, w:12.0, fs:7 },

  ...(() => {
    const HEENT = [
      { top:90.15, left:19.01, v:'Essentially normal' },
      { top:90.15, left:37.11, v:'Abnormal pupillary reaction' },
      { top:90.15, left:56.81, v:'Cervical lymphadenopathy' },
      { top:90.15, left:74.99, v:'Dry mucous membrane' },
      { top:91.88, left:19.09, v:'Icteric sclerae' },
      { top:91.88, left:37.12, v:'Pale conjunctivae' },
      { top:91.88, left:56.84, v:'Sunken eyeballs' },
      { top:91.88, left:75.08, v:'Sunken fontanelle' },
    ];
    return HEENT.map((b,i) => ({ id:'cf4Heent'+i, key:'cf4Heent', page:1, top:b.top, left:b.left, w:2, fs:9, checkboxMulti:true, checkValue:b.v }));
  })(),
  { id:'cf4HeentOthers', key:'cf4HeentOthers', page:1, top:93.85, left:27.5, w:26.0, fs:6.5 },

  /* ═══ PAGE 2 ═══ */

  // 5. Physical examination continued — six systems, multi-select
  ...(() => {
    const SYS = [
      { key:'cf4Chest', rows:[
        { top:6.6, cells:[[18.90,'Essentially normal'],[36.96,'Asymmetrical chest expansion'],[56.60,'Decreased breath sounds'],[74.83,'Wheezes']] },
        { top:8.26, cells:[[18.90,'Lump/s over breast(s)'],[36.97,'Rales/crackles/rhonchi'],[56.60,'Intercostal rib/clavicular retraction']] },
      ], others:{ key:'cf4ChestOthers', top:10.08, left:27.5 } },
      { key:'cf4Cvs', rows:[
        { top:11.67, cells:[[18.92,'Essentially normal'],[36.98,'Displaced apex beat'],[56.62,'Heaves and/or thrills'],[74.85,'Pericardial bulge']] },
        { top:13.32, cells:[[18.92,'Irregular rhythm'],[36.99,'Muffled heart sounds'],[56.63,'Murmur']] },
      ], others:{ key:'cf4CvsOthers', top:15.2, left:27.5 } },
      { key:'cf4Abdomen', rows:[
        { top:16.77, cells:[[19.00,'Essentially normal'],[36.90,'Abdominal rigidity'],[56.70,'Abdomen tenderness'],[74.93,'Hyperactive bowel sounds']] },
        { top:18.42, cells:[[19.00,'Palpable mass(es)'],[36.90,'Tympanitic/dull abdomen'],[56.70,'Uterine contraction']] },
      ], others:{ key:'cf4AbdomenOthers', top:20.34, left:27.5 } },
      { key:'cf4Gu', rows:[
        { top:22.03, cells:[[18.91,'Essentially normal'],[36.82,'Blood stained in exam finger'],[56.62,'Cervical dilatation'],[74.85,'Presence of abnormal discharge']] },
      ], others:{ key:'cf4GuOthers', top:23.96, left:27.5 } },
      { key:'cf4Skin', rows:[
        { top:25.67, cells:[[18.99,'Essentially normal'],[36.73,'Clubbing'],[56.70,'Cold clammy skin'],[74.93,'Cyanosis/mottled skin']] },
        { top:27.26, cells:[[19.00,'Edema/swelling'],[36.74,'Decreased mobility'],[56.70,'Pale nailbeds'],[74.84,'Poor skin turgor']] },
        { top:28.85, cells:[[18.91,'Rashes/petechiae'],[36.81,'Weak pulses']] },
      ], others:{ key:'cf4SkinOthers', top:30.61, left:27.5 } },
      { key:'cf4Neuro', rows:[
        { top:32.19, cells:[[18.90,'Essentially normal'],[36.96,'Abnormal gait'],[56.60,'Abnormal position sense'],[74.83,'Abnormal/decreased sensation']] },
        { top:33.8, cells:[[18.90,'Abnormal reflex(es)'],[36.97,'Poor/altered memory'],[56.60,'Poor muscle tone/strength'],[74.86,'Poor coordination']] },
      ], others:{ key:'cf4NeuroOthers', top:35.72, left:27.5 } },
    ];
    const out = [];
    SYS.forEach(sys => {
      sys.rows.forEach((row, ri) => row.cells.forEach(([left, v], ci) => out.push({
        id: `${sys.key}_${ri}_${ci}`, key: sys.key, page:2,
        top: row.top, left, w:2, fs:9, checkboxMulti:true, checkValue:v,
      })));
      out.push({ id: sys.others.key, key: sys.others.key, page:2,
                 top: sys.others.top, left: sys.others.left, w:26.0, fs:6.5 });
    });
    return out;
  })(),

  // IV. Course in the ward — 15 rows (date + doctor's order)
  { id:'cf4CourseExtra', key:'cf4CourseExtraSheet', page:2, top:38.3, left:61.8, w:2, fs:9, checkbox:true, checkValue:true },
  ...(() => {
    const TOPS = [42, 43.9, 45.6, 47.3, 49, 50.8, 52.5, 54.3, 56, 57.8, 59.6, 61.4, 63.1, 64.9, 66.6];
    const out = [];
    TOPS.forEach((top, i) => {
      out.push({ id:`cf4CourseDate${i+1}`,  key:`cf4CourseDate${i+1}`,  page:2, top, left:5.0,  w:13.0, fs:6.5 });
      out.push({ id:`cf4CourseOrder${i+1}`, key:`cf4CourseOrder${i+1}`, page:2, top, left:20.0, w:73.0, fs:6.5 });
    });
    return out;
  })(),
  { id:'cf4SurgicalProcedure', key:'cf4SurgicalProcedure', page:2, top:68.3, left:36.0, w:58.0, fs:7 },

  // V. Drugs / medicines — 7 rows x 2 column-groups
  { id:'cf4DrugsExtra', key:'cf4DrugsExtraSheet', page:2, top:70.45, left:44.7, w:2, fs:9, checkbox:true, checkValue:true },
  ...(() => {
    const TOPS = [73.8, 75.4, 77.1, 78.7, 80.4, 82.1, 83.7];
    const out = [];
    TOPS.forEach((top, i) => {
      const n = i + 1;
      out.push({ id:`cf4DrugName${n}`,  key:`cf4DrugName${n}`,  page:2, top, left:5.0,  w:13.0, fs:6.5 });
      out.push({ id:`cf4DrugDose${n}`,  key:`cf4DrugDose${n}`,  page:2, top, left:19.5, w:19.0, fs:6.5 });
      out.push({ id:`cf4DrugCost${n}`,  key:`cf4DrugCost${n}`,  page:2, top, left:40.5, w:8.0,  fs:6.5 });
      out.push({ id:`cf4DrugName${n}b`, key:`cf4DrugName${n}b`, page:2, top, left:50.0, w:13.0, fs:6.5 });
      out.push({ id:`cf4DrugDose${n}b`, key:`cf4DrugDose${n}b`, page:2, top, left:64.8, w:19.0, fs:6.5 });
      out.push({ id:`cf4DrugCost${n}b`, key:`cf4DrugCost${n}b`, page:2, top, left:85.0, w:8.0,  fs:6.5 });
    });
    return out;
  })(),

  // VI. Outcome of treatment
  { id:'cf4OutImproved',   key:'disposition', page:2, top:87.48, left:5.71,  w:2, fs:9, checkbox:true, checkValue:'Improved' },
  { id:'cf4OutHama',       key:'disposition', page:2, top:87.48, left:17.31, w:2, fs:9, checkbox:true, checkValue:'HAMA' },
  { id:'cf4OutExpired',    key:'disposition', page:2, top:87.48, left:27.79, w:2, fs:9, checkbox:true, checkValue:'Expired' },
  { id:'cf4OutAbsconded',  key:'disposition', page:2, top:87.48, left:39.75, w:2, fs:9, checkbox:true, checkValue:'Absconded' },
  { id:'cf4OutTransferred',key:'disposition', page:2, top:87.48, left:53.20, w:2, fs:9, checkbox:true, checkValue:'Transferred' },
  { id:'cf4TransferReason',key:'cf4TransferReason', page:2, top:87.5, left:76.0, w:18.0, fs:6.5 },

  // VII. Certification — name is typed; the signature itself stays wet-ink
  { id:'cf4AttendingProvider', key:'cf4AttendingProvider', page:2, top:94.1, left:18.0, w:40.0, fs:7 },
  ...[0,1].map(i => ({ id:'cf4SignMM'+(i+1), key:'cf4SignMM'+(i+1), page:2, top:94.25, left:74.3+i*2.18, w:2, fs:7, digit:i,   digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4SignDD'+(i+1), key:'cf4SignDD'+(i+1), page:2, top:94.25, left:80.3+i*2.18, w:2, fs:7, digit:i+2, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' })),
  ...[0,1,2,3].map(i => ({ id:'cf4SignYY'+(i+1), key:'cf4SignYY'+(i+1), page:2, top:94.25, left:86.3+i*2.18, w:2, fs:7, digit:i+4, digitKey:'cf4ProviderSignedDate', digitOrder:'mmddyyyy' })),
];
