/* ═══════════════════════════════════════════════════════════
   Overlay field coordinate map — CF4 (Claim Form 4, February 2020)
   Page size 612 x 1008 pt, 2 pages.

   Recalibrated for the Feb 2020 revision. The previous map was built
   against the August 2018 form, whose layout differs throughout — every
   row sat roughly 2.5% lower and several sections moved entirely, so
   exported CF4s printed out of position.

   `top` and `left` are percentages of page height / width.

   Positions come from the form itself rather than being eyeballed:
   the clinic's own filled-in copy gave the exact spot for each value it
   contained, and the remaining fields are anchored to the printed label
   or the drawn tick-box rectangle beside them (PyMuPDF: span bboxes for
   text, get_drawings() for the boxes).

   Checkboxes use checkbox:true + checkValue; the renderer draws a check
   glyph when state[key] matches checkValue. Multi-select groups (signs &
   symptoms, PE findings) use checkboxMulti:true, where state[key] is an
   array and the mark is drawn when the array contains checkValue.
═══════════════════════════════════════════════════════════ */
window.PDF_OVERLAY_CF4 = [
  /* ═══ PAGE 1 ═══ */

  // Series # — 13 digit boxes, top right
  ...[0,1,2,3,4,5,6,7,8,9,10,11,12].map(i => ({
    id:'cf4SeriesD' + (i+1), key:'cf4SeriesD' + (i+1), page:1,
    top:5.3, left:66.5 + i*2.19, w:2.0, fs:7,
    digit:i, digitKey:'cf4Series',
  })),

  // I. Health Care Institution — values sit on the rule under each label
  { id:'cf4HciName',    key:'hciName',    page:1, top:14.19, left:4.08,  w:52.0, fs:8 },
  { id:'cf4HciPAN',     key:'hciPAN',     page:1, top:14.19, left:62.09, w:32.0, fs:8 },
  // Address is one continuous rule; the parts sit over their sub-labels.
  { id:'cf4HciBldg',    key:'hciBldg',    page:1, top:16.67, left:4.9,   w:20.0, fs:7 },
  { id:'cf4HciStreet',  key:'hciStreet',  page:1, top:16.67, left:26.14, w:18.5, fs:7 },
  { id:'cf4HciBarangay',key:'hciCity',    page:1, top:16.67, left:45.75, w:23.5, fs:7 },
  { id:'cf4HciProvince',key:'hciProvince',page:1, top:16.67, left:70.26, w:17.0, fs:7 },
  { id:'cf4HciZip',     key:'hciZip',     page:1, top:16.67, left:88.24, w:9.5,  fs:7 },

  // II. Patient's Data
  { id:'cf4PatientLastName',   key:'patientLastName',   page:1, top:21.6, left:5.0,  w:21.0, fs:8 },
  { id:'cf4PatientFirstName',  key:'patientFirstName',  page:1, top:21.6, left:28.0, w:21.0, fs:8 },
  { id:'cf4PatientMiddleName', key:'patientMiddleName', page:1, top:21.6, left:50.0, w:19.0, fs:8 },
  { id:'cf4PatientPIN',        key:'memberPIN',         page:1, top:21.63, left:71.9, w:25.0, fs:8 },
  { id:'cf4PatientAge',        key:'patientAge',        page:1, top:24.11, left:72.71, w:8.0, fs:8 },

  { id:'cf4SexMale',   key:'patientSex', page:1, top:25.5, left:76.8,  w:2, fs:9, checkbox:true, checkValue:'Male' },
  { id:'cf4SexFemale', key:'patientSex', page:1, top:25.5, left:84.97, w:2, fs:9, checkbox:true, checkValue:'Female' },

  { id:'cf4ChiefComplaint', key:'cf4ChiefComplaint', page:1, top:25.0,  left:2.45,  w:66.0, fs:8, wrap:true, maxLines:3 },
  { id:'cf4AdmittingDx',    key:'admissionDx',       page:1, top:28.77, left:2.45,  w:30.0, fs:8, wrap:true, maxLines:5 },
  { id:'cf4DischargeDx',    key:'cf4FinalDiagnosis', page:1, top:28.77, left:34.31, w:36.0, fs:8, wrap:true, maxLines:5 },
  { id:'cf4CaseRate1',      key:'cf4IcdCode',        page:1, top:28.68, left:72.71, w:24.0, fs:8 },
  { id:'cf4CaseRate2',      key:'cf4RvsCode',        page:1, top:31.8,  left:72.71, w:24.0, fs:8 },

  // 9. Date / Time Admitted — mm dd yyyy, hh mm (digit boxes, step 2.45)
  ...[0,1].map(i => ({ id:'cf4AdmMM'+(i+1), key:'cf4AdmMM'+(i+1), page:1, top:36.31, left:20.1+i*2.45, w:2, fs:8, digit:i,   digitKey:'dateAdmitted', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4AdmDD'+(i+1), key:'cf4AdmDD'+(i+1), page:1, top:36.31, left:27.45+i*2.45, w:2, fs:8, digit:i+2, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' })),
  ...[0,1,2,3].map(i => ({ id:'cf4AdmYY'+(i+1), key:'cf4AdmYY'+(i+1), page:1, top:36.31, left:34.8+i*2.45, w:2, fs:8, digit:i+4, digitKey:'dateAdmitted', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4AdmHH'+(i+1), key:'cf4AdmHH'+(i+1), page:1, top:36.31, left:65.86+i*2.45, w:2, fs:8, digit:i,   digitKey:'cf4TimeAdmittedDigits' })),
  ...[0,1].map(i => ({ id:'cf4AdmMI'+(i+1), key:'cf4AdmMI'+(i+1), page:1, top:36.31, left:73.2+i*2.45,  w:2, fs:8, digit:i+2, digitKey:'cf4TimeAdmittedDigits' })),
  { id:'cf4AdmAM', key:'amPmAdmitted', page:1, top:36.0, left:78.43, w:2, fs:9, checkbox:true, checkValue:'AM' },
  { id:'cf4AdmPM', key:'amPmAdmitted', page:1, top:36.0, left:84.15, w:2, fs:9, checkbox:true, checkValue:'PM' },

  // 10. Date / Time Discharged
  ...[0,1].map(i => ({ id:'cf4DisMM'+(i+1), key:'cf4DisMM'+(i+1), page:1, top:39.6, left:20.1+i*2.45, w:2, fs:8, digit:i,   digitKey:'dateDischarge', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4DisDD'+(i+1), key:'cf4DisDD'+(i+1), page:1, top:39.6, left:27.45+i*2.45, w:2, fs:8, digit:i+2, digitKey:'dateDischarge', digitOrder:'mmddyyyy' })),
  ...[0,1,2,3].map(i => ({ id:'cf4DisYY'+(i+1), key:'cf4DisYY'+(i+1), page:1, top:39.6, left:34.8+i*2.45, w:2, fs:8, digit:i+4, digitKey:'dateDischarge', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4DisHH'+(i+1), key:'cf4DisHH'+(i+1), page:1, top:39.48, left:65.86+i*2.45, w:2, fs:8, digit:i,   digitKey:'cf4TimeDischargeDigits' })),
  ...[0,1].map(i => ({ id:'cf4DisMI'+(i+1), key:'cf4DisMI'+(i+1), page:1, top:39.48, left:73.2+i*2.45,  w:2, fs:8, digit:i+2, digitKey:'cf4TimeDischargeDigits' })),
  { id:'cf4DisAM', key:'amPmDischarge', page:1, top:39.5, left:78.43, w:2, fs:9, checkbox:true, checkValue:'AM' },
  { id:'cf4DisPM', key:'amPmDischarge', page:1, top:39.5, left:84.15, w:2, fs:9, checkbox:true, checkValue:'PM' },

  // III. Reason for Admission
  { id:'cf4HistoryPI',   key:'cf4HistoryPresentIllness', page:1, top:45.8, left:2.45, w:94.0, fs:8, wrap:true, maxLines:10 },
  { id:'cf4PastMedical', key:'cf4PastMedicalHistory',    page:1, top:54.97, left:2.45, w:94.0, fs:8, wrap:true, maxLines:7 },

  // 2.b OB/GYN history — G _ P _ ( _ - _ - _ - _ )  then LMP
  { id:'cf4ObG',        key:'gravida',    page:1, top:62.0, left:4.91,  w:2.6, fs:9 },
  { id:'cf4ObP',        key:'para',       page:1, top:62.0, left:8.18,  w:2.6, fs:9 },
  { id:'cf4ObTerm',     key:'obTerm',     page:1, top:62.0, left:11.46, w:2.6, fs:9 },
  { id:'cf4ObPreterm',  key:'obPreterm',  page:1, top:62.0, left:14.73, w:2.6, fs:9 },
  { id:'cf4ObAbortion', key:'obAbortion', page:1, top:62.0, left:18.0,  w:2.6, fs:9 },
  { id:'cf4ObLiving',   key:'obLiving',   page:1, top:62.0, left:21.28, w:2.6, fs:9 },
  { id:'cf4Lmp',        key:'lmp',        page:1, top:62.0, left:31.09, w:10.0, fs:8 },
  { id:'cf4LmpNA',      key:'cf4LmpNA',   page:1, top:62.0, left:42.48, w:2, fs:9, checkbox:true, checkValue:'NA' },

  /* 3. Pertinent signs and symptoms — 4 columns x 9 rows.
     Column lefts and row tops read from the drawn tick boxes. */
  ...(() => {
    const COLS = [3.27, 26.14, 50.65, 73.53];
    const ROWS = [65.5, 67.0, 68.5, 69.9, 71.4, 72.9, 74.4, 75.9, 77.4];
    const GRID = [
      ['Altered Mental Sensorium','Abdominal Cramp Pain','Anorexia','Bleeding Gums'],
      ['Body Weakness','Blurring Of Vision','Chest Pain/Discomfort','Conspitation'],
      ['Cough','Diarrhea','Dizziness','Dysphagia'],
      ['Dyspnea','Dysuria','Epistaxis','Fever'],
      ['Frequency in Urination','Headache','Hematemesis','Hematuria'],
      ['Hemoptysis','Irritability','Jaundice','Lower Extremity Edema'],
      ['Myalgia','Orthopnea','Palpitations','Seizure'],
      ['Skin Rashes','Stool, Bloody/Black Tarry Mucoid','Sweating','Urgency'],
      ['Vomitting','Weight Loss','Pain','Others'],
    ];
    const out = [];
    GRID.forEach((row, r) => row.forEach((label, c) => out.push({
      id:'cf4Sym_' + r + '_' + c, key:'cf4Symptoms', page:1,
      top:ROWS[r], left:COLS[c], w:2, fs:9,
      checkboxMulti:true, checkValue:label,
    })));
    return out;
  })(),
  { id:'cf4PainSite',     key:'cf4PainSite',     page:1, top:77.4, left:55.6, w:11.0, fs:7 },
  { id:'cf4SymptomOther', key:'cf4SymptomOther', page:1, top:77.4, left:79.5, w:17.0, fs:7 },

  // 4. Referred from another HCI
  { id:'cf4RefNo',  key:'cf4Referred', page:1, top:79.7, left:37.58, w:2, fs:9, checkbox:true, checkValue:'No' },
  { id:'cf4RefYes', key:'cf4Referred', page:1, top:79.7, left:44.9,  w:2, fs:9, checkbox:true, checkValue:'Yes' },
  { id:'cf4ReferralReason', key:'cf4ReferralReason', page:1, top:79.86, left:62.5, w:34.0, fs:7 },
  { id:'cf4ReferralHci',    key:'cf4ReferralHci',    page:1, top:81.35, left:62.5, w:34.0, fs:7 },

  // 5. Physical examination on admission
  { id:'cf4PeAwake',   key:'cf4GeneralSurvey',    page:1, top:85.3, left:17.97, w:2, fs:9, checkbox:true, checkValue:'Awake and alert' },
  { id:'cf4PeAltered', key:'cf4GeneralSurvey',    page:1, top:85.3, left:37.58, w:2, fs:9, checkbox:true, checkValue:'Altered sensorium' },
  { id:'cf4GsOther',   key:'cf4AlteredSensorium', page:1, top:85.3, left:57.0, w:18.0, fs:7 },
  { id:'cf4Height',    key:'cf4Height',           page:1, top:84.22, left:83.88, w:7.0, fs:8 },
  { id:'cf4Weight',    key:'cf4Weight',           page:1, top:85.8,  left:83.88, w:7.0, fs:8 },

  { id:'cf4VitalBP',   key:'cf4VitalBP',   page:1, top:87.8, left:26.6, w:10.0, fs:8 },
  { id:'cf4VitalHR',   key:'cf4VitalHR',   page:1, top:87.8, left:46.0, w:10.0, fs:8 },
  { id:'cf4VitalRR',   key:'cf4VitalRR',   page:1, top:87.8, left:65.0, w:9.0,  fs:8 },
  { id:'cf4VitalTemp', key:'cf4VitalTemp', page:1, top:87.8, left:83.0, w:9.0,  fs:8 },

  // HEENT — two rows of four
  ...(() => {
    const COLS = [17.97, 36.6, 55.56, 75.16];
    const ROWS = [90.4, 92.4];
    const GRID = [
      ['Essentially Normal','Iceteric Sclerae','Abnormal Pupillary Reaction','Pale Conjunctivae'],
      ['Cervical Lympadenopathy','Sunken Eyeballs','Dry Muccous Membrane','Sunken Fontanelle'],
    ];
    const out = [];
    GRID.forEach((row, r) => row.forEach((label, c) => out.push({
      id:'cf4Heent_' + r + '_' + c, key:'cf4Heent', page:1,
      top:ROWS[r], left:COLS[c], w:2, fs:9,
      checkboxMulti:true, checkValue:label,
    })));
    return out;
  })(),
  { id:'cf4HeentOthers', key:'cf4HeentOthers', page:1, top:94.25, left:24.0, w:40.0, fs:7 },

  /* ═══ PAGE 2 ═══
     "5. Physical Examination continued" — six systems, each a block of
     tick boxes over four columns plus its own "Others:" rule. Column
     lefts and row tops read from the drawn boxes. */
  ...(() => {
    const COLS = [17.97, 36.6, 57.19, 76.8];
    const SECTIONS = [
      { key:'cf4Chest', others:'cf4ChestOthers', othersTop:6.94, rows:[4.1, 5.6],
        grid:[['Essentially normal','Lump/s over breast(s)','Asymmetrical chest expansion','Rales/crackles/rhonchi'],
              ['Decreased breath sounds','Intercostal rib/clavicular retraction','Wheezes','']] },
      { key:'cf4Cvs', others:'cf4CvsOthers', othersTop:11.41, rows:[8.5, 10.0],
        grid:[['Essentially normal','Irregular rhythm','Displaced apex beat','Muffled heart sounds'],
              ['Heave and/or thrills','Murmur','Pericardial bulge','']] },
      { key:'cf4Abdomen', others:'cf4AbdomenOthers', othersTop:15.87, rows:[13.0, 14.5],
        grid:[['Essentially normal','Palpable mass(es)','Abdominal rigidity','Tympanitic/dull abdomen'],
              ['Abdominal tenderness','Uterine contraction','Hyperactive bowel sounds','']] },
      { key:'cf4Gu', others:'cf4GuOthers', othersTop:18.85, rows:[17.5],
        grid:[['Essentially normal','Blood stained in exam finger','Cervical dilatation','Presence of abnormal discharge']] },
      { key:'cf4Skin', others:'cf4SkinOthers', othersTop:24.80, rows:[20.4, 21.9, 23.4],
        grid:[['Essentially normal','Edema/swelling','Rashes/petechie','Clubbing'],
              ['Decreased mobility','Weak pulse','Cold clammy','Pale nailbeds'],
              ['Cyanosis/mottled skin','Poor skin turgor','','']] },
      { key:'cf4Neuro', others:'cf4NeuroOthers', othersTop:29.27, rows:[26.4, 27.9],
        grid:[['Essentially normal','Abnormal reflex(es)','Abnormal gait','Poor/altered memory'],
              ['Abnormal position sense','Poor muscle tone/strength','Abnormal/decreased senstation','Poor coordination']] },
    ];
    const out = [];
    SECTIONS.forEach(sec => {
      sec.grid.forEach((row, r) => row.forEach((label, c) => {
        if (!label) return;
        out.push({
          id:sec.key + '_' + r + '_' + c, key:sec.key, page:2,
          top:sec.rows[r], left:COLS[c], w:2, fs:9,
          checkboxMulti:true, checkValue:label,
        });
      }));
      out.push({ id:sec.others, key:sec.others, page:2,
                 top:sec.othersTop, left:24.0, w:16.0, fs:7 });
    });
    return out;
  })(),

  // IV. Course in the ward — a Date column and a wide Doctor's Order column
  { id:'cf4CourseExtraSheet', key:'cf4CourseExtraSheet', page:2, top:30.9, left:61.27, w:2, fs:9, checkbox:true, checkValue:'Yes' },
  { id:'cf4CourseDate',   key:'dateAdmitted',      page:2, top:33.6, left:3.0,  w:20.0, fs:7 },
  { id:'cf4CourseInWard', key:'cf4CourseInWard',   page:2, top:33.6, left:27.0, w:69.0, fs:8, wrap:true, maxLines:14 },

  // Surgical procedure / RVS description, written after the printed label
  { id:'cf4SurgicalProcedure', key:'cf4SurgicalProcedure', page:2, top:44.25, left:47.55, w:49.0, fs:8, wrap:true, maxLines:2 },

  // V. Drugs / medicines — generic name column
  { id:'cf4DrugsExtraSheet', key:'cf4DrugsExtraSheet', page:2, top:46.2, left:46.08, w:2, fs:9, checkbox:true, checkValue:'Yes' },
  { id:'cf4Drugs', key:'cf4DrugsAdministered', page:2, top:49.21, left:2.54, w:33.0, fs:7, wrap:true, maxLines:12 },

  // VI. Outcome of treatment — boxes sit just left of each printed word
  { id:'cf4OutImproved',    key:'disposition', page:2, top:61.71, left:3.2,  w:2, fs:9, checkbox:true, checkValue:'Improved' },
  { id:'cf4OutHama',        key:'disposition', page:2, top:61.71, left:16.4, w:2, fs:9, checkbox:true, checkValue:'HAMA' },
  { id:'cf4OutExpired',     key:'disposition', page:2, top:61.71, left:29.6, w:2, fs:9, checkbox:true, checkValue:'Expired' },
  { id:'cf4OutAbsconded',   key:'disposition', page:2, top:61.71, left:42.8, w:2, fs:9, checkbox:true, checkValue:'Absconded' },
  { id:'cf4OutTransferred', key:'disposition', page:2, top:61.71, left:57.6, w:2, fs:9, checkbox:true, checkValue:'Transferred' },
  { id:'cf4TransferReason', key:'cf4TransferReason', page:2, top:61.71, left:84.0, w:13.0, fs:7 },

  // VII. Certification — printed name sits above the signature rule
  { id:'cf4AttendingProvider', key:'cf4AttendingProvider', page:2, top:69.9, left:10.0, w:38.0, fs:8 },
  ...[0,1].map(i => ({ id:'cf4SignMM'+(i+1), key:'cf4SignMM'+(i+1), page:2, top:70.4, left:70.0+i*2.9, w:2, fs:8, digit:i,   digitKey:'cf4DateSigned', digitOrder:'mmddyyyy' })),
  ...[0,1].map(i => ({ id:'cf4SignDD'+(i+1), key:'cf4SignDD'+(i+1), page:2, top:70.4, left:77.6+i*2.9, w:2, fs:8, digit:i+2, digitKey:'cf4DateSigned', digitOrder:'mmddyyyy' })),
  ...[0,1,2,3].map(i => ({ id:'cf4SignYY'+(i+1), key:'cf4SignYY'+(i+1), page:2, top:70.4, left:85.2+i*2.9, w:2, fs:8, digit:i+4, digitKey:'cf4DateSigned', digitOrder:'mmddyyyy' })),
];
