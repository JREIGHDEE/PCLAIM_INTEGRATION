/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Application Logic
   This file keeps form data in memory only and makes no API calls
   itself; OCR, claim storage (MariaDB) and server-side PDF export are
   handled by the Ocr_module Flask backend (see js/ocr.js). A claim
   reviewed there is loaded into these forms by js/claim-loader.js.
═══════════════════════════════════════════════════════════ */

/* ── Auth guard ──────────────────────────────────────────────
   Asks the backend whether this browser holds a valid session and
   bounces to the login page if not. The check is deliberately made
   server-side: a flag kept in the browser could be set by anyone
   with the developer tools open (research design §3.4.2.9, §3.8).
   The signed-in user's name, role and email fill the navbar here.
───────────────────────────────────────────────────────────── */
(async function requireLogin() {
  if (typeof PCAAuth === 'undefined') return; // auth-client.js not loaded
  const user = await PCAAuth.requireLogin();
  if (!user) return;                          // redirecting to login.html

  window.currentUser = user;

  const set = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };
  set('navUserName',     user.full_name);
  set('navUserNameFull', user.full_name);
  set('navUserEmail',    user.email);
  document.querySelectorAll('.user-role').forEach(el => {
    el.textContent = PCAAuth.roleLabel(user.role);
  });

  // Admin-only controls stay hidden for an encoder.
  document.querySelectorAll('[data-requires-role]').forEach(el => {
    const allowed = el.dataset.requiresRole.split(',').map(r => r.trim());
    el.hidden = !allowed.includes(user.role);
  });

  // These are defined further down the file, so they only exist once the
  // whole script has run — hence the deferred call.
  setTimeout(() => {
    if (typeof fillProfileSection === 'function') fillProfileSection(user);
    if (typeof loadClinicSettings === 'function') loadClinicSettings();
    if (user.role === 'admin' && typeof loadStaffAccounts === 'function') loadStaffAccounts();
  }, 0);
})();

AOS.init({ duration: 500, once: true, offset: 30 });

/* ══════════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════════ */
const state = {
  currentSection: 'dashboard',
  data: {
    /* Patient (dependent / person confined) */
    patientLastName:'', patientFirstName:'', patientMiddleName:'', patientNameExt:'',
    patientDOB:'', patientSex:'', patientPIN:'',
    /* Member (PhilHealth account holder) */
    memberLastName:'', memberFirstName:'', memberMiddleName:'', memberNameExt:'',
    memberDOB:'', memberSex:'', memberPIN:'', relationship:'',
    memberIsPatient:false, /* "The patient is the member": member copies the patient */
    /* Address */
    addrUnit:'', addrBuilding:'', addrLot:'', addrStreet:'',
    addrSubdivision:'', addrBarangay:'', addrCity:'', addrProvince:'', addrZip:'',
    /* Contact */
    mobile:'', homePhone:'', email:'',
    /* Confinement */
    dateAdmitted:'', timeAdmitted:'', amPmAdmitted:'AM',
    dateDischarge:'', timeDischarge:'', amPmDischarge:'AM',
    disposition:'', accommodation:'', chiefComplaint:'', admissionDx:'', dischargeDx:'',
    /* Series numbers (printed top-right of each claim form) */
    csfSeries:'', cf2Series:'',
    /* CF2 – special procedures, TB-DOTS and newborn care packages */
    cf2SpecialProcedures:[], cf2SpecialProcedureDetail:'',
    cf2TbPhase:'', cf2NewbornCare:[],
    /* CF4 – Clinical Record (encoded manually; the logbook does not record these) */
    patientAge:'', cf4Series:'',
    hciBldg:'', hciZip:'',
    cf4ChiefComplaint:'', cf4HistoryPresentIllness:'', cf4PastMedicalHistory:'',
    cf4FinalDiagnosis:'', cf4IcdCode:'', cf4RvsCode:'',
    cf4TimeAdmittedDigits:'', cf4TimeDischargeDigits:'',
    /* CF4 – OB/GYN history */
    obTerm:'', obPreterm:'', obAbortion:'', obLiving:'', cf4LmpNA:false,
    /* CF4 – signs & symptoms (tick all that apply) */
    cf4Symptoms:[], cf4PainSite:'', cf4SymptomOther:'',
    /* CF4 – referral */
    cf4Referred:'', cf4ReferralReason:'', cf4ReferralHci:'',
    /* CF4 – physical examination on admission */
    cf4GeneralSurvey:'', cf4AlteredSensorium:'',
    cf4VitalBP:'', cf4VitalHR:'', cf4VitalRR:'', cf4VitalTemp:'',
    cf4Heent:[], cf4HeentOthers:'',
    /* CF4 – physical examination continued (page 2) */
    cf4Chest:[],   cf4ChestOthers:'',
    cf4Cvs:[],     cf4CvsOthers:'',
    cf4Abdomen:[], cf4AbdomenOthers:'',
    cf4Gu:[],      cf4GuOthers:'',
    cf4Skin:[],    cf4SkinOthers:'',
    cf4Neuro:[],   cf4NeuroOthers:'',
    /* CF4 – course in the ward (15 rows) + surgical procedure */
    cf4CourseExtraSheet:false, cf4SurgicalProcedure:'',
    /* CF4 – drugs / medicines (7 rows x 2 column groups) */
    cf4DrugsExtraSheet:false,
    /* CF4 – outcome + certification */
    cf4TransferReason:'',
    cf4AttendingProvider:'', cf4ProviderPAN:'', cf4ProviderSignedDate:'',
    /* CF4 course-in-ward rows */
    cf4CourseDate1:'', cf4CourseOrder1:'', cf4CourseDate2:'', cf4CourseOrder2:'', cf4CourseDate3:'', cf4CourseOrder3:'', cf4CourseDate4:'', cf4CourseOrder4:'', cf4CourseDate5:'', cf4CourseOrder5:'', cf4CourseDate6:'', cf4CourseOrder6:'', cf4CourseDate7:'', cf4CourseOrder7:'', cf4CourseDate8:'', cf4CourseOrder8:'', cf4CourseDate9:'', cf4CourseOrder9:'', cf4CourseDate10:'', cf4CourseOrder10:'', cf4CourseDate11:'', cf4CourseOrder11:'', cf4CourseDate12:'', cf4CourseOrder12:'', cf4CourseDate13:'', cf4CourseOrder13:'', cf4CourseDate14:'', cf4CourseOrder14:'', cf4CourseDate15:'', cf4CourseOrder15:'',
    /* CF4 drug rows */
    cf4DrugName1:'', cf4DrugDose1:'', cf4DrugCost1:'', cf4DrugName1b:'', cf4DrugDose1b:'', cf4DrugCost1b:'', cf4DrugName2:'', cf4DrugDose2:'', cf4DrugCost2:'', cf4DrugName2b:'', cf4DrugDose2b:'', cf4DrugCost2b:'', cf4DrugName3:'', cf4DrugDose3:'', cf4DrugCost3:'', cf4DrugName3b:'', cf4DrugDose3b:'', cf4DrugCost3b:'', cf4DrugName4:'', cf4DrugDose4:'', cf4DrugCost4:'', cf4DrugName4b:'', cf4DrugDose4b:'', cf4DrugCost4b:'', cf4DrugName5:'', cf4DrugDose5:'', cf4DrugCost5:'', cf4DrugName5b:'', cf4DrugDose5b:'', cf4DrugCost5b:'', cf4DrugName6:'', cf4DrugDose6:'', cf4DrugCost6:'', cf4DrugName6b:'', cf4DrugDose6b:'', cf4DrugCost6b:'', cf4DrugName7:'', cf4DrugDose7:'', cf4DrugCost7:'', cf4DrugName7b:'', cf4DrugDose7b:'', cf4DrugCost7b:'',
    /* CF2 – Referral */
    referredByHCI:'', referralHciName:'', referralStreet:'', referralCity:'',
    referralProvince:'', referralZip:'',
    /* CF2 – Discharge Diagnosis table (2 diagnoses x up to 3 procedures each) */
    dxADiagnosis:'', dxAIcd10:'',
    dxAProcI:'', dxARvsI:'', dxADateI:'', dxALatI:'',
    dxAProcII:'', dxARvsII:'', dxADateII:'', dxALatII:'',
    dxAProcIII:'', dxARvsIII:'', dxADateIII:'', dxALatIII:'',
    dxBDiagnosis:'', dxBIcd10:'',
    dxBProcI:'', dxBRvsI:'', dxBDateI:'', dxBLatI:'',
    dxBProcII:'', dxBRvsII:'', dxBDateII:'', dxBLatII:'',
    dxBProcIII:'', dxBRvsIII:'', dxBDateIII:'', dxBLatIII:'',
    /* HCI */
    hciPAN:'', hciName:'', hciStreet:'', hciCity:'', hciProvince:'',
    /* Employer – CSF Part II */
    employerPEN:'', employerPhone:'', employerName:'',

    /* CSF Part I – Certification of Member (signature block) */
    memberSignedDate:'', repSignedDate:'',
    memberSignerType:'', repRelationship:'', repRelationshipOther:'',
    repReason:'', repReasonOther:'',
    /* CSF Part II – Employer's Certification (signature) */
    employerSignedDate:'', employerRepName:'', employerCapacity:'',
    /* CSF Part III – Consent to Access Patient Record/s */
    patientRepName:'', patientRepSignedDate:'',
    patientSignerType:'', patientRepRelationship:'', patientRepRelationshipOther:'',
    patientReason:'', patientReasonOther:'',
    /* CSF Part IV – Health Care Professional Information (up to 3 rows) */
    hciProf1AccredNo:'', hciProf1Name:'', hciProf1DateSigned:'',
    hciProf2AccredNo:'', hciProf2Name:'', hciProf2DateSigned:'',
    hciProf3AccredNo:'', hciProf3Name:'', hciProf3DateSigned:'',
    /* CSF Part V – Provider Information and Certification */
    csfFirstCaseRate:'', csfSecondCaseRate:'',
    providerRepName:'', providerCapacity:'', providerSignedDate:'',

    /* CF2 Item 10 – Accreditation/Signature/Date Signed + Co-pay (up to 3 rows) */
    cf2Prof1AccredNo:'', cf2Prof1Name:'', cf2Prof1DateSigned:'', cf2Prof1Copay:'', cf2Prof1CopayAmount:'',
    cf2Prof2AccredNo:'', cf2Prof2Name:'', cf2Prof2DateSigned:'', cf2Prof2Copay:'', cf2Prof2CopayAmount:'',
    cf2Prof3AccredNo:'', cf2Prof3Name:'', cf2Prof3DateSigned:'', cf2Prof3Copay:'', cf2Prof3CopayAmount:'',
    /* CF2 Part III-B – Consent to Access Patient Record/s */
    cf2PatientRepName:'', cf2PatientRepSignedDate:'',
    cf2PatientRepRelationship:'', cf2PatientRepRelationshipOther:'',
    cf2PatientReason:'', cf2PatientReasonOther:'',
    /* CF2 Part IV – Certification of Consumption of Health Care Institution */
    cf2ProviderRepName:'', cf2ProviderCapacity:'', cf2ProviderSignedDate:'',
    /* Member Profile – PMRF */
    civilStatus:'', placeOfBirth:'', citizenship:'',
    motherLastName:'', motherFirstName:'', motherMiddleName:'',
    spouseLastName:'', spouseFirstName:'', spouseMiddleName:'',
    memberType:'', profession:'', monthlyIncome:'',
    /* Maternity / Delivery */
    lmp:'', ageOfMenarche:'', gravida:'', para:'',
    expectedDD:'', deliveryDate:'', deliveryTime:'', amPmDelivery:'AM',
    mannerOfDelivery:'', fetalOutcome:'', babySex:'', birthWeight:'', apgarScore:'',
    briefHistory:'',
    /* Physical Examination */
    /* Maternity Care Package */
    obTerm:'', obPreterm:'', obAbortion:'', obLiving:'',
    /* Maternal / Birth Outcome extras not already covered by Part I fields */
      /* PMRF – Purpose / PhilSys / TIN */
    registrationPurpose:'', preferredKonsulta:'', philsysId:'', tin:'',
    /* PMRF – Name table checkboxes (Member / Mother / Spouse) */
    memberNoMiddleName:false, memberMononym:false,
    motherNoMiddleName:false, motherMononym:false,
    spouseNoMiddleName:false, spouseMononym:false,
    /* PMRF – Dependent 1 extras (shares patientLastName/FirstName/etc with CSF/CF2) */
    patientCitizenship:'', dep1NoMiddleName:false, dep1Mononym:false, dep1Disability:false,
    /* PMRF – Dependents 2–4 */
    dep2LastName:'', dep2FirstName:'', dep2Ext:'', dep2MiddleName:'',
    dep2Relationship:'', dep2DOB:'', dep2Citizenship:'',
    dep2NoMiddleName:false, dep2Mononym:false, dep2Disability:false,
    dep3LastName:'', dep3FirstName:'', dep3Ext:'', dep3MiddleName:'',
    dep3Relationship:'', dep3DOB:'', dep3Citizenship:'',
    dep3NoMiddleName:false, dep3Mononym:false, dep3Disability:false,
    dep4LastName:'', dep4FirstName:'', dep4Ext:'', dep4MiddleName:'',
    dep4Relationship:'', dep4DOB:'', dep4Citizenship:'',
    dep4NoMiddleName:false, dep4Mononym:false, dep4Disability:false,
    /* PMRF – Mailing Address */
    mailingSameAsAbove:false, businessPhone:'',
    mailingAddrUnit:'', mailingAddrBuilding:'', mailingAddrLot:'', mailingAddrStreet:'',
    mailingAddrSubdivision:'', mailingAddrBarangay:'', mailingAddrCity:'',
    mailingAddrProvince:'', mailingAddrZip:'',
    /* PMRF – Member Type extras */
    pwdIdNo:'', praSrrvNo:'', acrICardNo:'', groupEnrollmentNo:'', proofOfIncome:'',
    /* PMRF Page 2 – V. Updating/Amendment */
    amendName:false, amendNameFrom:'', amendNameTo:'',
    amendDOB:false, amendDOBFrom:'', amendDOBTo:'',
    amendSex:false, amendSexFrom:'', amendSexTo:'',
    amendCivilStatus:false, amendCivilStatusFrom:'', amendCivilStatusTo:'',
    amendPersonalInfo:false, amendPersonalInfoFrom:'', amendPersonalInfoTo:'',
    /* PMRF Page 2 – Member's Signature */
    memberSignatureName:'', memberSignatureDate:'',
  }
};

/* ══════════════════════════════════════════════════════════
   SAMPLE DATA  (fictional – Maria Dela Cruz, maternity)
══════════════════════════════════════════════════════════ */
const SAMPLE_DATA = {
  patientLastName:'DELA CRUZ', patientFirstName:'MARIA', patientMiddleName:'SANTOS',
  patientNameExt:'', patientDOB:'1995-03-15', patientSex:'Female',
  patientPIN:'12-345678901-3',
  memberLastName:'DELA CRUZ', memberFirstName:'PEDRO', memberMiddleName:'REYES',
  memberNameExt:'', memberDOB:'1992-07-22', memberSex:'Male',
  memberPIN:'12-345678901-2', relationship:'Spouse',
  addrUnit:'', addrBuilding:'', addrLot:'123', addrStreet:'Rizal Street',
  addrSubdivision:'Bgy. Uno Subdivision', addrBarangay:'Barangay Uno',
  addrCity:'Quezon City', addrProvince:'Metro Manila', addrZip:'1100',
  mobile:'0917-123-4567', homePhone:'02-8123-4567', email:'pedro.delacruz@email.com',
  dateAdmitted:'2026-06-10', timeAdmitted:'08:30', amPmAdmitted:'AM',
  dateDischarge:'2026-06-13', timeDischarge:'10:00', amPmDischarge:'AM',
  disposition:'Improved', accommodation:'Non-Private',
  chiefComplaint:'Labor pains, full-term pregnancy',
  admissionDx:'Term Pregnancy in Active Labor, 39 weeks AOG',
  dischargeDx:'Normal Spontaneous Delivery, Full Term, Live Birth',
  patientAge:'31',
  cf4ChiefComplaint:'Labor pains, full-term pregnancy',
  cf4HistoryPresentIllness:'G2P1 at 39 weeks AOG presented with regular uterine contractions '
    + 'every 5 minutes onset 6 hours prior to admission, with watery vaginal discharge. '
    + 'No bleeding, no fever. Prenatal care complete with 8 visits.',
  cf4PhysicalExam:'BP 120/80, HR 88, RR 18, T 36.8C. Abdomen gravid, fundic height 34 cm, '
    + 'FHT 142 bpm. Internal exam: 6 cm dilated, 80% effaced, station -1, intact membranes.',
  cf4CourseInWard:'Admitted and monitored with partograph. Progressed to full dilatation after '
    + '5 hours. Delivered a live term baby boy via normal spontaneous delivery. '
    + 'Placenta delivered complete. Perineum intact. Stable post-partum, '
    + 'ambulatory and tolerating diet. Discharged improved on the third hospital day.',
  cf4DrugsAdministered:'Oxytocin 10 units IM post-delivery; Mefenamic acid 500 mg PO q6h PRN; '
    + 'Ferrous sulfate + folic acid 1 tab PO OD',
  cf4FinalDiagnosis:'Normal Spontaneous Delivery, Full Term, Live Birth',
  cf4LaboratoryFindings:'CBC: Hgb 118 g/L, WBC 9.2; Urinalysis: normal; HBsAg non-reactive',
  cf4IcdCode:'O80', cf4RvsCode:'59400',
  cf4AttendingProvider:'ROSARIO M. ALCANTARA, RM',
  cf4ProviderPAN:'000005678', cf4ProviderSignedDate:'2026-06-13',
  dxADiagnosis:'Normal Spontaneous Delivery, Full Term, Live Birth',
  dxAIcd10:'O80',
  hciPAN:'000001234', hciName:'Mapagpala Maternity Clinic',
  csfSeries:'2026000123456', cf2Series:'2026000123457',
  cf2SpecialProcedures:[], cf2SpecialProcedureDetail:'',
  cf2TbPhase:'', cf2NewbornCare:['Essential Newborn Care','Newborn Screening Test'],
  hciStreet:'456 Bonifacio Avenue', hciCity:'Quezon City', hciProvince:'Metro Manila',
  employerPEN:'', employerPhone:'', employerName:'',
  civilStatus:'Married', placeOfBirth:'Quezon City, Metro Manila', citizenship:'FILIPINO',
  motherLastName:'SANTOS', motherFirstName:'LILIA', motherMiddleName:'GARCIA',
  spouseLastName:'DELA CRUZ', spouseFirstName:'PEDRO', spouseMiddleName:'REYES',
  memberType:'Employed Private', profession:'Teacher', monthlyIncome:'25,000',
  lmp:'2025-09-03', ageOfMenarche:'13', gravida:'2', para:'1',
  expectedDD:'2026-06-10',
  deliveryDate:'2026-06-10', deliveryTime:'09:45', amPmDelivery:'AM',
  mannerOfDelivery:'Normal Spontaneous Delivery (NSD)',
  fetalOutcome:'Live Birth', babySex:'Female', birthWeight:'3200', apgarScore:'9',
  briefHistory:'G2P1 (1001), 39 weeks AOG by LMP. Admitted for active labor with regular uterine contractions every 5 minutes. No previous complications noted.',
  /* Maternity Care Package */
  obTerm:'1', obPreterm:'0', obAbortion:'0', obLiving:'1',
    /* PMRF – Purpose / PhilSys / TIN */
  registrationPurpose:'Registration', preferredKonsulta:'Mapagpala Maternity Clinic',
  philsysId:'1234-5678-9012', tin:'123-456-789-000',
  /* PMRF – Name table checkboxes */
  memberNoMiddleName:false, memberMononym:false,
  motherNoMiddleName:false, motherMononym:false,
  spouseNoMiddleName:false, spouseMononym:false,
  /* PMRF – Dependent 1 extras */
  patientCitizenship:'FILIPINO', dep1NoMiddleName:false, dep1Mononym:false, dep1Disability:false,
  /* PMRF – Dependents 2–4 (left blank by default) */
  dep2LastName:'', dep2FirstName:'', dep2Ext:'', dep2MiddleName:'',
  dep2Relationship:'', dep2DOB:'', dep2Citizenship:'',
  dep2NoMiddleName:false, dep2Mononym:false, dep2Disability:false,
  dep3LastName:'', dep3FirstName:'', dep3Ext:'', dep3MiddleName:'',
  dep3Relationship:'', dep3DOB:'', dep3Citizenship:'',
  dep3NoMiddleName:false, dep3Mononym:false, dep3Disability:false,
  dep4LastName:'', dep4FirstName:'', dep4Ext:'', dep4MiddleName:'',
  dep4Relationship:'', dep4DOB:'', dep4Citizenship:'',
  dep4NoMiddleName:false, dep4Mononym:false, dep4Disability:false,
  /* PMRF – Mailing Address */
  mailingSameAsAbove:true, businessPhone:'',
  mailingAddrUnit:'', mailingAddrBuilding:'', mailingAddrLot:'', mailingAddrStreet:'',
  mailingAddrSubdivision:'', mailingAddrBarangay:'', mailingAddrCity:'',
  mailingAddrProvince:'', mailingAddrZip:'',
  /* PMRF – Member Type extras */
  pwdIdNo:'', praSrrvNo:'', acrICardNo:'', groupEnrollmentNo:'', proofOfIncome:'',
  /* PMRF Page 2 – V. Updating/Amendment (left unchecked by default) */
  amendName:false, amendNameFrom:'', amendNameTo:'',
  amendDOB:false, amendDOBFrom:'', amendDOBTo:'',
  amendSex:false, amendSexFrom:'', amendSexTo:'',
  amendCivilStatus:false, amendCivilStatusFrom:'', amendCivilStatusTo:'',
  amendPersonalInfo:false, amendPersonalInfoFrom:'', amendPersonalInfoTo:'',
  /* PMRF Page 2 – Member's Signature */
  memberSignatureName:'Pedro R. Dela Cruz', memberSignatureDate:'2026-06-01',
};

/* ══════════════════════════════════════════════════════════
   COMPUTED VALUE RESOLVER
══════════════════════════════════════════════════════════ */
const DATE_FIELDS = new Set([
  'memberDOB','patientDOB','dateAdmitted','dateDischarge',
  'deliveryDate','expectedDD','lmp',
  'dxADateI','dxADateII','dxADateIII','dxBDateI','dxBDateII','dxBDateIII',
  'memberSignedDate','repSignedDate','employerSignedDate','patientRepSignedDate',
  'hciProf1DateSigned','hciProf2DateSigned','hciProf3DateSigned','providerSignedDate',
  'cf2Prof1DateSigned','cf2Prof2DateSigned','cf2Prof3DateSigned',
  'cf2PatientRepSignedDate','cf2ProviderSignedDate',
  'dep2DOB','dep3DOB','dep4DOB','memberSignatureDate',
]);

function getComputedValue(key) {
  const d = state.data;
  if (DATE_FIELDS.has(key)) return d[key] ? formatDate(d[key]) : '';
  switch (key) {
    case 'patientName':
      return [d.patientLastName, d.patientFirstName, d.patientNameExt, d.patientMiddleName]
        .filter(x => x && x.trim()).join(' ');
    case 'memberName':
      return [d.memberLastName, d.memberFirstName, d.memberNameExt, d.memberMiddleName]
        .filter(x => x && x.trim()).join(' ');
    case 'motherMaidenName':
      return [d.motherLastName, d.motherFirstName, d.motherMiddleName]
        .filter(x => x && x.trim()).join(' ');
    case 'spouseName':
      return [d.spouseLastName, d.spouseFirstName, d.spouseMiddleName]
        .filter(x => x && x.trim()).join(' ');
    case 'hciAddress':
      return [d.hciStreet, d.hciCity, d.hciProvince].filter(Boolean).join(', ');
    case 'fullAddress':
      return [
        [d.addrLot, d.addrStreet].filter(Boolean).join(' '),
        d.addrSubdivision, d.addrBarangay, d.addrCity, d.addrProvince,
        d.addrZip
      ].filter(Boolean).join(', ');
    case 'obHistory':
      return (d.gravida || d.para) ? `G${d.gravida||'?'} P${d.para||'?'}` : '';
    case 'timeAdmittedStr':
      return formatTime12h(d.timeAdmitted);
    case 'timeDischargeStr':
      return formatTime12h(d.timeDischarge);
    case 'timeAdmittedDigits':
      return time12hDigits(d.timeAdmitted);
    case 'timeDischargeDigits':
      return time12hDigits(d.timeDischarge);
    /* CF2 Time Admitted/Discharged: the PDF has two ruled hh:mm boxes per
       row, one before the printed "AM" label and one before "PM" — the
       box position itself indicates the period, so the value goes in
       whichever box matches (the other stays blank). */
    case 'timeAdmittedAM':   return isPMTime(d.timeAdmitted) === false ? bareTime(d.timeAdmitted) : '';
    case 'timeAdmittedPM':   return isPMTime(d.timeAdmitted) === true  ? bareTime(d.timeAdmitted) : '';
    case 'timeDischargeAM':  return isPMTime(d.timeDischarge) === false ? bareTime(d.timeDischarge) : '';
    case 'timeDischargePM':  return isPMTime(d.timeDischarge) === true  ? bareTime(d.timeDischarge) : '';
    /* CF2 HCI Accreditation No. (PAN): one character per ruled digit box */
    case 'hciPANc1': return (d.hciPAN || '').charAt(0);
    case 'hciPANc2': return (d.hciPAN || '').charAt(1);
    case 'hciPANc3': return (d.hciPAN || '').charAt(2);
    case 'hciPANc4': return (d.hciPAN || '').charAt(3);
    case 'hciPANc5': return (d.hciPAN || '').charAt(4);
    case 'hciPANc6': return (d.hciPAN || '').charAt(5);
    case 'hciPANc7': return (d.hciPAN || '').charAt(6);
    case 'hciPANc8': return (d.hciPAN || '').charAt(7);
    case 'hciPANc9': return (d.hciPAN || '').charAt(8);
    /* PMRF Date of Birth: 8 individual digit boxes in mm-dd-yyyy order
       (state stores the ISO "YYYY-MM-DD" value from the date input) */
    case 'memberDOBd1': return (d.memberDOB || '').slice(5,7).charAt(0);
    case 'memberDOBd2': return (d.memberDOB || '').slice(5,7).charAt(1);
    case 'memberDOBd3': return (d.memberDOB || '').slice(8,10).charAt(0);
    case 'memberDOBd4': return (d.memberDOB || '').slice(8,10).charAt(1);
    case 'memberDOBd5': return (d.memberDOB || '').slice(0,4).charAt(0);
    case 'memberDOBd6': return (d.memberDOB || '').slice(0,4).charAt(1);
    case 'memberDOBd7': return (d.memberDOB || '').slice(0,4).charAt(2);
    case 'memberDOBd8': return (d.memberDOB || '').slice(0,4).charAt(3);
    /* PMRF PIN / PhilSys ID / TIN: one character per ruled digit box
       (non-digit separators like "-" are stripped first) */
    case 'memberPINc1': case 'memberPINc2': case 'memberPINc3': case 'memberPINc4':
    case 'memberPINc5': case 'memberPINc6': case 'memberPINc7': case 'memberPINc8':
    case 'memberPINc9': case 'memberPINc10': case 'memberPINc11': case 'memberPINc12':
      return digitsOnly(d.memberPIN).charAt(Number(key.slice(10)) - 1);
    case 'philsysIdc1': case 'philsysIdc2': case 'philsysIdc3': case 'philsysIdc4':
    case 'philsysIdc5': case 'philsysIdc6': case 'philsysIdc7': case 'philsysIdc8':
    case 'philsysIdc9': case 'philsysIdc10': case 'philsysIdc11': case 'philsysIdc12':
      return digitsOnly(d.philsysId).charAt(Number(key.slice(10)) - 1);
    case 'tinc1': case 'tinc2': case 'tinc3': case 'tinc4': case 'tinc5':
    case 'tinc6': case 'tinc7': case 'tinc8': case 'tinc9':
      return digitsOnly(d.tin).charAt(Number(key.slice(4)) - 1);
    default:
      return d[key] || '';
  }
}

function isPMTime(hhmm) {
  if (!hhmm) return null;
  const h = parseInt(hhmm.split(':')[0], 10);
  return isNaN(h) ? null : h >= 12;
}

function bareTime(hhmm) {
  return formatTime12h(hhmm).replace(/\s*(AM|PM)$/, '');
}

function digitsOnly(str) {
  return (str || '').replace(/\D/g, '');
}

/* ══════════════════════════════════════════════════════════
   PREVIEW ELEMENT MAP  [elementId, computedKey]
══════════════════════════════════════════════════════════ */
const PREVIEW_MAP = [
  /* CSF – Part I: Member & Patient */
  ['csf-memberPIN','memberPIN'],       ['csf-memberName','memberName'],
  ['csf-memberDOB','memberDOB'],       ['csf-patientPIN','patientPIN'],
  ['csf-patientName','patientName'],   ['csf-patientDOB','patientDOB'],
  ['csf-relationship','relationship'], ['csf-dateAdmitted','dateAdmitted'],
  ['csf-dateDischarge','dateDischarge'],
  /* CSF – Part II: Employer */
  ['csf-employerPEN','employerPEN'],   ['csf-employerPhone','employerPhone'],
  ['csf-employerName','employerName'],
  /* CF2 – Part I: HCI */
  ['cf2-hciPAN','hciPAN'],             ['cf2-hciName','hciName'],
  ['cf2-hciAddress','hciAddress'],
  /* CF2 – Part II: Patient Confinement */
  ['cf2-patientName','patientName'],
  ['cf2-dateAdmitted','dateAdmitted'], ['cf2-timeAdmitted','timeAdmittedStr'],
  ['cf2-dateDischarge','dateDischarge'],['cf2-timeDischarge','timeDischargeStr'],
  ['cf2-disposition','disposition'],   ['cf2-accommodation','accommodation'],
  ['cf2-admissionDx','admissionDx'],   ['cf2-dischargeDx','dischargeDx'],
  /* PMRF – Section I: Personal Details */
  ['pmrf-memberPIN','memberPIN'],      ['pmrf-memberName','memberName'],
  ['pmrf-memberDOB','memberDOB'],      ['pmrf-memberSex','memberSex'],
  ['pmrf-placeOfBirth','placeOfBirth'],['pmrf-civilStatus','civilStatus'],
  ['pmrf-citizenship','citizenship'],  ['pmrf-motherName','motherMaidenName'],
  ['pmrf-spouseName','spouseName'],
  /* PMRF – Section II: Address & Contact */
  ['pmrf-fullAddress','fullAddress'],  ['pmrf-mobile','mobile'],
  ['pmrf-homePhone','homePhone'],      ['pmrf-email','email'],
  /* PMRF – Section III: Dependents */
  ['pmrf-depName','patientName'],      ['pmrf-depRelationship','relationship'],
  ['pmrf-depDOB','patientDOB'],        ['pmrf-depSex','patientSex'],
  /* PMRF – Section IV: Member Type */
  ['pmrf-memberType','memberType'],    ['pmrf-profession','profession'],
  ['pmrf-monthlyIncome','monthlyIncome'],
];

/* VAL_FIELDS, VAL_FORM_KEYS and the rule tables live in js/validation-rules.js,
   which loads before this file. */

/* ══════════════════════════════════════════════════════════
   NAVIGATION
══════════════════════════════════════════════════════════ */
const VALID_SECTIONS = ['dashboard','patient','csf','cf2','cf4','pmrf','validation','profile','settings'];

function navigateTo(section, opts) {
  opts = opts || {};
  const prev = document.querySelector('.content-section.active');
  if (prev) prev.classList.remove('active');
  const next = document.getElementById('section-' + section);
  if (next) { next.classList.add('active'); AOS.refresh(); }
  document.querySelectorAll('.sidebar-item').forEach(el =>
    el.classList.toggle('active', el.dataset.section === section));
  state.currentSection = section;
  if (!opts.skipHash) {
    history.replaceState(null, '', '#' + section);
  }
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar.classList.contains('mobile-open')) {
    sidebar.classList.remove('mobile-open');
    overlay && overlay.classList.remove('active');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  // Checking phase: once the Validation Checker shows no critical errors,
  // teach the offline OCR AI the entries (js/entry-learning.js; sent once
  // per patient, so a later PDF export doesn't count them again).
  if (section === 'validation' && lastValidationResult && lastValidationResult.canGeneratePDF
      && typeof PCALearning !== 'undefined') {
    PCALearning.recordFormEntries();
  }
  // Trigger PDF rendering when entering a form section
  if (VAL_FORM_KEYS.includes(section) && typeof onFormSectionActivated === 'function') {
    // Small delay lets the section become visible (display:block) before measuring width
    setTimeout(() => onFormSectionActivated(section), 60);
  }
}

document.querySelectorAll('.sidebar-item').forEach(item =>
  item.addEventListener('click', e => {
    if (!item.dataset.section) return; // external link (e.g. OCR page) — let the browser navigate normally
    e.preventDefault(); navigateTo(item.dataset.section);
  }));

/* ══════════════════════════════════════════════════════════
   PROFILE MENU & LOGOUT
══════════════════════════════════════════════════════════ */
(function setupProfileMenu() {
  const email = sessionStorage.getItem('pca_user_email') || 'staff@clinic.ph';
  const emailEl = document.getElementById('navUserEmail');
  if (emailEl) emailEl.textContent = email;

  document.querySelectorAll('.profile-dropdown-menu [data-section]').forEach(item =>
    item.addEventListener('click', e => { e.preventDefault(); navigateTo(item.dataset.section); }));

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async e => {
      e.preventDefault();
      // Ask the backend to destroy the session. Clearing only the browser
      // would leave the server-side session valid and still usable.
      if (typeof PCAAuth !== 'undefined') await PCAAuth.logout();
      window.location.replace('login.html');
    });
  }
})();

(function setupMobileSidebar() {
  if (!document.getElementById('sidebarOverlay')) {
    const o = document.createElement('div');
    o.className = 'sidebar-overlay'; o.id = 'sidebarOverlay';
    document.body.appendChild(o);
    o.addEventListener('click', () => {
      document.getElementById('sidebar').classList.remove('mobile-open');
      o.classList.remove('active');
    });
  }
  document.getElementById('sidebarToggle').addEventListener('click', () => {
    const sb = document.getElementById('sidebar');
    const ov = document.getElementById('sidebarOverlay');
    if (window.innerWidth < 768) {
      sb.classList.toggle('mobile-open');
      ov.classList.toggle('active', sb.classList.contains('mobile-open'));
    } else {
      sb.classList.toggle('collapsed');
    }
  });
})();

/* ══════════════════════════════════════════════════════════
   AUTO-POPULATION ENGINE
══════════════════════════════════════════════════════════ */
/* "The patient is the PhilHealth member": the member's boxes copy the
   patient's (name, birthday, sex, PIN) and the relationship is "Self", so
   nothing is typed twice. While ticked they follow the patient's boxes and
   are locked, so the two can't drift apart; unticking unlocks them and
   keeps what is there. */
const MEMBER_FROM_PATIENT = {
  memberLastName: 'patientLastName', memberFirstName: 'patientFirstName',
  memberMiddleName: 'patientMiddleName', memberNameExt: 'patientNameExt',
  memberDOB: 'patientDOB', memberSex: 'patientSex',
};
const MEMBER_LOCKED_KEYS = [...Object.keys(MEMBER_FROM_PATIENT), 'memberPIN', 'relationship'];

function applyMemberIsPatient() {
  const same = !!state.data.memberIsPatient;
  if (same) {
    Object.entries(MEMBER_FROM_PATIENT).forEach(([member, patient]) => {
      state.data[member] = state.data[patient] || '';
    });
    // One PIN for one person: whichever box has it.
    const pin = state.data.patientPIN || state.data.memberPIN || '';
    state.data.patientPIN = pin;
    state.data.memberPIN = pin;
    state.data.relationship = 'Self';
  }
  MEMBER_LOCKED_KEYS.forEach(key => {
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      if (el.type === 'hidden') return;
      if (el.classList.contains('btn-check-group')) el.classList.toggle('is-locked', same);
      else el.disabled = same;
      el.title = same ? 'Filled from the patient\'s details (the patient is the member)' : '';
    });
  });
  document.querySelectorAll('.box-input[data-target]').forEach(group => {
    const target = document.querySelector(group.dataset.target);
    if (target && target.dataset.autofill === 'memberPIN') {
      group.querySelectorAll('input').forEach(i => { i.disabled = same; });
    }
  });
}

function updateFormPreviews() {
  applyMemberIsPatient();
  PREVIEW_MAP.forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    const val = getComputedValue(key);
    const wasEmpty = el.textContent === '—';
    el.textContent = val || '—';
    if (val) {
      el.classList.add('populated');
      if (wasEmpty) {
        el.style.animation = 'none';
        requestAnimationFrame(() => { el.style.animation = ''; });
      }
    } else {
      el.classList.remove('populated');
    }
  });
  // Sync all duplicate data-autofill elements (e.g. split-screen right panels)
  syncAllAutofillElements();
  // Keep the three-box PIN inputs in step (js/pin-input.js)
  if (typeof refreshPinBoxes === 'function') refreshPinBoxes();
  // Sync segmented box-group inputs (dates, PAN) from state
  syncBoxGroupsFromState();
  // ...and the per-character box rows (CSF/PMRF PIN, dates), which mirror a
  // real input and so never saw a value that was set rather than typed.
  if (typeof refreshBoxInputs === 'function') refreshBoxInputs();
  // Update PDF canvas overlays
  if (typeof updateAllOverlays === 'function') updateAllOverlays();
  updateValidation();
  updateDashboardStats();
  updateSyncFieldChecks();
  updateSyncIndicator();
}

function syncAllAutofillElements() {
  const seen = new Set();
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    if (seen.has(key)) return; // only process each key once
    seen.add(key);
    const val = state.data[key] || '';
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(sibling => {
      if (sibling === document.activeElement) return; // don't clobber the field being typed in
      if (sibling.type === 'radio') {
        sibling.checked = sibling.value === val;
      } else if (sibling.type === 'checkbox' && sibling.dataset.multi !== undefined) {
        const list = Array.isArray(state.data[key]) ? state.data[key] : [];
        sibling.checked = list.includes(sibling.value);
      } else if (sibling.type === 'checkbox') {
        sibling.checked = !!state.data[key];
      } else if (sibling.tagName === 'SELECT' || sibling.tagName === 'TEXTAREA' || sibling.tagName === 'INPUT') {
        if (sibling.value !== val) sibling.value = val;
      }
    });
  });
  syncBtnCheckGroups();
}

/* ══════════════════════════════════════════════════════════
   BUTTON-CHECK GROUPS (e.g. CSF Relationship: child/parent/spouse)
══════════════════════════════════════════════════════════ */
function syncBtnCheckGroups() {
  document.querySelectorAll('.btn-check-group[data-autofill]').forEach(group => {
    const key = group.dataset.autofill;
    const val = state.data[key] || '';
    group.querySelectorAll('.btn-check-option').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.value === val);
    });
  });

  const referralDetails = document.getElementById('cf2-referral-details');
  if (referralDetails) referralDetails.style.display = state.data.referredByHCI === 'Yes' ? '' : 'none';
}

const AMPM_TIME_KEY = { amPmAdmitted: 'timeAdmitted', amPmDischarge: 'timeDischarge', amPmDelivery: 'deliveryTime' };

document.querySelectorAll('.btn-check-group[data-autofill]').forEach(group => {
  const key = group.dataset.autofill;
  group.querySelectorAll('.btn-check-option').forEach(btn => {
    btn.addEventListener('click', () => {
      // A copy of a Patient details field is shown here, not edited here.
      if (group.classList.contains('from-patient-details')) return;
      const alreadyActive = btn.classList.contains('active');
      const newVal = alreadyActive ? '' : btn.dataset.value;
      const prev = state.data[key];
      state.data[key] = newVal;
      propagateMirroredField(key, prev);

      const timeKey = AMPM_TIME_KEY[key];
      if (timeKey && newVal && state.data[timeKey]) {
        const [hStr, mStr] = state.data[timeKey].split(':');
        let h = parseInt(hStr, 10);
        if (!isNaN(h)) {
          h = h % 12;
          if (newVal === 'PM') h += 12;
          state.data[timeKey] = `${String(h).padStart(2, '0')}:${mStr}`;
        }
      }
      updateFormPreviews();
    });
  });
});

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + 'T00:00:00');
  if (isNaN(d)) return iso;
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${mm}-${dd}-${d.getFullYear()}`;
}

function formatTime12h(hhmm) {
  if (!hhmm) return '';
  const [hStr, mStr] = hhmm.split(':');
  let h = parseInt(hStr, 10);
  if (isNaN(h)) return hhmm;
  const period = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return `${String(h).padStart(2, '0')}:${mStr} ${period}`;
}

function time12hDigits(hhmm) {
  if (!hhmm) return '';
  const [hStr, mStr] = hhmm.split(':');
  let h = parseInt(hStr, 10);
  if (isNaN(h)) return '';
  h = h % 12 || 12;
  return `${String(h).padStart(2, '0')}${mStr}`;
}

/* Fields that describe the same clinical fact on more than one form.
   Editing the source propagates to each target that is still empty or
   still holds the previous source value, so the five forms stay
   consistent and IC-08 (CF2 vs CF4 diagnosis) does not fire spuriously.
   A target the user has deliberately edited is left alone. */
/* Most boxes that mean the same thing on several forms are one key (e.g.
   patientLastName on Patient details, CSF, CF2, CF4, PMRF), so typing it
   anywhere fills it everywhere. These are separate keys on different
   forms for the same fact: typing in any of them fills the others (both
   ways), on the rule above. */
const LINKED_FIELD_GROUPS = [
  ['dischargeDx', 'dxADiagnosis', 'cf4FinalDiagnosis'],
  ['chiefComplaint', 'cf4ChiefComplaint'],
  // Health care professionals: CSF Part III and CF2 Part II
  ...[1, 2, 3].flatMap(n => [
    [`hciProf${n}Name`, `cf2Prof${n}Name`],
    [`hciProf${n}AccredNo`, `cf2Prof${n}AccredNo`],
    [`hciProf${n}DateSigned`, `cf2Prof${n}DateSigned`],
  ]),
  // The clinic's authorized representative: CSF and CF2
  ['providerRepName', 'cf2ProviderRepName'], ['providerCapacity', 'cf2ProviderCapacity'],
  ['providerSignedDate', 'cf2ProviderSignedDate'],
  // Who signs for the patient, and why: CSF and CF2
  ['patientRepName', 'cf2PatientRepName'], ['patientRepRelationship', 'cf2PatientRepRelationship'],
  ['patientRepRelationshipOther', 'cf2PatientRepRelationshipOther'], ['patientReason', 'cf2PatientReason'],
  ['patientReasonOther', 'cf2PatientReasonOther'], ['patientRepSignedDate', 'cf2PatientRepSignedDate'],
];
const MIRRORED_FIELDS = {};
LINKED_FIELD_GROUPS.forEach(group => group.forEach(key => {
  MIRRORED_FIELDS[key] = group.filter(other => other !== key);
}));

function propagateMirroredField(key, prevValue) {
  const targets = MIRRORED_FIELDS[key];
  if (!targets) return;
  const next = state.data[key];
  targets.forEach(t => {
    const cur = state.data[t];
    if (!cur || cur === prevValue) state.data[t] = next;
  });
}

/* PhilHealth forms are completed in capital letters ("PLEASE WRITE IN
   CAPITAL LETTERS" on the CSF itself), so every typed value is stored
   upper-cased and the boxes are drawn that way. An email address is left
   as typed - it is a login, not something printed on a form - and so is
   anything the page marks data-keep-case. The caret is put back where it
   was, otherwise replacing the value would send it to the end of the line
   on every keystroke. */
function toFormCase(el) {
  const raw = typeof el.value === 'string' ? el.value.trim() : el.value;
  if (typeof raw !== 'string') return raw;
  if (el.type === 'email' || el.type === 'password' || el.type === 'date' ||
      el.type === 'time' || el.dataset.keepCase !== undefined) return raw;
  const upper = raw.toUpperCase();
  if (el.value !== upper && el.value.trim() === raw) {
    const at = el.selectionStart;
    el.value = upper;
    if (at !== null && el.setSelectionRange) {
      try { el.setSelectionRange(at, at); } catch (e) { /* not a text input */ }
    }
  }
  return upper;
}

/* ══════════════════════════════════════════════════════════
   FIELDS THAT BELONG TO "PATIENT DETAILS"
   Ninety boxes are the same fact asked twice: the patient's
   name, PIN, address and confinement dates appear both on the
   Patient details page and again inside CSF, CSF 2, CSF 4 and
   PMRF. They were already kept in step by
   syncAllAutofillElements(), but a box you can type in invites
   typing, so the same detail got entered several times and a
   form looked empty whenever the typing had been done on a
   different page.
   Those copies are now shown, filled, but not editable, with
   one line at the top of each form saying where to change
   them. Fields a form owns on its own stay editable.
══════════════════════════════════════════════════════════ */
const FORM_SECTIONS = ['csf', 'cf2', 'cf4', 'pmrf'];
// Switches, not details: these choose how other boxes are filled, so
// they stay usable on the form itself.
const PATIENT_PANEL_CONTROLS = new Set(['memberIsPatient']);

function patientOwnedKeys() {
  const keys = new Set();
  document.querySelectorAll('#section-patient [data-autofill]').forEach(el => {
    keys.add(el.dataset.autofill);
  });
  document.querySelectorAll('#section-patient .pca-box-group[data-box-key]').forEach(el => {
    keys.add(el.dataset.boxKey);
  });
  return keys;
}

function lockToPatientDetails(el) {
  if (el.dataset.fromPatient !== undefined) return;
  el.dataset.fromPatient = '';
  el.classList.add('from-patient-details');
  // readOnly keeps the value selectable and copyable; radios, checkboxes
  // and selects have no readOnly, so those are disabled instead.
  if (el.tagName === 'SELECT' || el.type === 'radio' || el.type === 'checkbox') {
    el.disabled = true;
  } else {
    el.readOnly = true;
  }
  el.setAttribute('title', 'Entered on the Patient details page - change it there');
}

function markPatientOwnedFields() {
  const owned = patientOwnedKeys();
  FORM_SECTIONS.forEach(form => {
    const section = document.getElementById('section-' + form);
    if (!section) return;
    section.querySelectorAll('[data-autofill]').forEach(el => {
      if (PATIENT_PANEL_CONTROLS.has(el.dataset.autofill)) return;
      if (owned.has(el.dataset.autofill)) lockToPatientDetails(el);
    });
    section.querySelectorAll('.pca-box-group[data-box-key]').forEach(group => {
      if (!owned.has(group.dataset.boxKey)) return;
      group.classList.add('from-patient-details');
      group.querySelectorAll('.pca-box').forEach(lockToPatientDetails);
    });
    // A button-check group (e.g. Relationship) is a row of divs, so it is
    // switched off with a class the stylesheet and the click handler read.
    section.querySelectorAll('.btn-check-group[data-autofill]').forEach(group => {
      if (owned.has(group.dataset.autofill)) group.classList.add('from-patient-details');
    });
    addPatientDetailsNote(section);
  });
}

function addPatientDetailsNote(section) {
  const panel = section.querySelector('.entry-panel-body') ||
                section.querySelector('.form-entry-panel');
  if (!panel || panel.querySelector('.from-patient-note')) return;
  if (!section.querySelector('.from-patient-details')) return;
  const note = document.createElement('div');
  note.className = 'from-patient-note';
  note.innerHTML =
    '<i class="bi bi-info-circle" aria-hidden="true"></i>' +
    '<span>The grey boxes were filled in from <strong>Patient details</strong>. ' +
    'To change them, <a href="#patient" class="from-patient-link">open Patient details</a>.</span>';
  panel.insertBefore(note, panel.firstChild);
  note.querySelector('.from-patient-link').addEventListener('click', e => {
    e.preventDefault();
    navigateTo('patient');
  });
}

function bindInputListeners() {
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    const handler = () => {
      const prev = state.data[key];
      if (el.type === 'radio') { if (el.checked) state.data[key] = el.value; }
      else if (el.type === 'checkbox' && el.dataset.multi !== undefined) {
        // Tick-all-that-apply group (CF4 signs & symptoms, PE findings):
        // state.data[key] is the array of selected labels.
        const list = Array.isArray(state.data[key]) ? state.data[key].slice() : [];
        const i = list.indexOf(el.value);
        if (el.checked && i === -1) list.push(el.value);
        if (!el.checked && i !== -1) list.splice(i, 1);
        state.data[key] = list;
      }
      else if (el.type === 'checkbox') state.data[key] = el.checked;
      else state.data[key] = toFormCase(el);
      propagateMirroredField(key, prev);
      updateFormPreviews();
    };
    el.addEventListener('input', handler);
    el.addEventListener('change', handler);
  });
}

/* ══════════════════════════════════════════════════════════
   SEGMENTED "BOX" INPUTS
   Some CF2 fields (dates, HCI Accreditation No./PAN) print as
   individual ruled boxes on the PDF. These groups render as
   separate per-character/segment boxes in the data-entry panel
   to match, while still feeding the same state.data[key] the
   rest of the app (overlays, validation, previews) expects.
══════════════════════════════════════════════════════════ */
function bindBoxGroupListeners() {
  document.querySelectorAll('.pca-box-group').forEach(group => {
    const boxes = Array.from(group.querySelectorAll('.pca-box'));
    boxes.forEach((box, i) => {
      box.addEventListener('input', () => {
        box.value = box.value.replace(/\D/g, '').slice(0, box.maxLength);
        if (box.value.length >= box.maxLength && boxes[i + 1]) boxes[i + 1].focus();
        commitBoxGroup(group);
      });
      box.addEventListener('keydown', e => {
        if (e.key === 'Backspace' && !box.value && boxes[i - 1]) boxes[i - 1].focus();
      });
      box.addEventListener('paste', e => {
        const text = (e.clipboardData || window.clipboardData).getData('text');
        if (!text) return;
        e.preventDefault();
        let idx = i;
        text.replace(/\D/g, '').split('').forEach(ch => {
          if (boxes[idx]) { boxes[idx].value = ch; idx++; }
        });
        (boxes[idx] || box).focus();
        commitBoxGroup(group);
      });
    });
  });
}

function commitBoxGroup(group) {
  const key   = group.dataset.boxKey;
  const type  = group.dataset.boxType;
  const boxes = Array.from(group.querySelectorAll('.pca-box'));
  if (type === 'date') {
    const mm = boxes[0].value, dd = boxes[1].value, yyyy = boxes[2].value;
    state.data[key] = (mm.length === 2 && dd.length === 2 && yyyy.length === 4)
      ? `${yyyy}-${mm}-${dd}` : '';
  } else if (type === 'date8') {
    // 8 single-digit boxes: MM MM DD DD YYYY YYYY YYYY YYYY
    const d = boxes.map(b => b.value);
    state.data[key] = d.every(c => c.length === 1)
      ? `${d[4]}${d[5]}${d[6]}${d[7]}-${d[0]}${d[1]}-${d[2]}${d[3]}` : '';
  } else {
    state.data[key] = boxes.map(b => b.value).join('');
  }
  updateFormPreviews();
}

function syncBoxGroupsFromState() {
  document.querySelectorAll('.pca-box-group').forEach(group => {
    if (group.contains(document.activeElement)) return; // don't clobber active typing
    const key   = group.dataset.boxKey;
    const type  = group.dataset.boxType;
    const boxes = Array.from(group.querySelectorAll('.pca-box'));
    const val   = state.data[key] || '';
    if (type === 'date') {
      const [yyyy, mm, dd] = val ? val.split('-') : ['', '', ''];
      boxes[0].value = mm || '';
      boxes[1].value = dd || '';
      boxes[2].value = yyyy || '';
    } else if (type === 'date8') {
      const [yyyy, mm, dd] = val ? val.split('-') : ['', '', ''];
      const chars = `${mm}${dd}${yyyy}`.split('');
      boxes.forEach((b, i) => { b.value = chars[i] || ''; });
    } else {
      // strip separators like "-" that plain-text sample/typed values may
      // carry (e.g. "12-345678901-2") — boxes hold one digit each
      const chars = digitsOnly(val).split('');
      boxes.forEach((b, i) => { b.value = chars[i] || ''; });
    }
  });
}

function updateSyncIndicator() {
  const AM_DEFAULTS = new Set(['amPmAdmitted','amPmDischarge','amPmDelivery']);
  const filled = Object.entries(state.data)
    .filter(([k,v]) => v && !(AM_DEFAULTS.has(k) && v === 'AM')).length;
  const total  = Object.keys(state.data).length;
  const dot  = document.getElementById('syncDot');
  const text = document.getElementById('syncText');
  if (!dot || !text) return;
  if (filled === 0) {
    dot.classList.remove('active');
    text.textContent = 'No patient details typed yet.';
  } else {
    dot.classList.add('active');
    text.textContent = `${filled} boxes filled in. They are copied into every form.`;
  }
}

function updateSyncFieldChecks() {
  document.querySelectorAll('.sync-field-item[data-check]').forEach(item => {
    const val = getComputedValue(item.dataset.check);
    const icon = item.querySelector('.sync-icon');
    item.classList.toggle('complete', !!val);
    if (icon) icon.className = val
      ? 'bi bi-check-circle-fill text-success sync-icon'
      : 'bi bi-circle text-muted sync-icon';
  });
}

/* ══════════════════════════════════════════════════════════
   VALIDATION
══════════════════════════════════════════════════════════ */
/* Latest engine result, shared with the PDF export gate. */
let lastValidationResult = null;

/* ══════════════════════════════════════════════════════════
   VALIDATION CHECKLIST MARKUP
   Built from VAL_FIELDS so the checklist can never drift out of
   sync with the keys the engine actually evaluates.
══════════════════════════════════════════════════════════ */
const VAL_FORM_META = {
  csf:  { title:'CSF',      abbr:'CSF'  },
  cf2:  { title:'CSF 2',        abbr:'CF2'  },
  cf4:  { title:'Clinical Record',           abbr:'CF4'  },
  pmrf: { title:'PMRF',  abbr:'PMRF' },
};

/* One form open at a time (data-bs-parent), so staff work through the
   five forms one by one instead of facing every missing field at once.
   The colour matches the form's card on the dashboard. */
function buildValidationAccordion() {
  const host = document.getElementById('valAccordion');
  if (!host) return;

  host.innerHTML = VAL_FORM_KEYS.map((form, i) => {
    const meta   = VAL_FORM_META[form];
    const fields = VAL_FIELDS[form];
    const items  = fields.map(({ key, label }) => `
      <div class="val-item" data-field="${key}" data-form="${form}">
        <span class="val-dot"></span>
        <span class="val-label">${label}</span>
        <span class="val-status ms-auto">Missing</span>
      </div>`).join('');

    return `
      <div class="pca-accordion-item accordion-item fs--${form}">
        <h2 class="accordion-header">
          <button class="accordion-button pca-accordion-btn${i === 0 ? '' : ' collapsed'}"
                  type="button" data-bs-toggle="collapse" data-bs-target="#val-${form}-panel">
            <span class="val-chip">${meta.abbr}</span>
            <span class="val-title">${meta.title}</span>
            <span class="ms-auto me-3 val-score" id="val-${form}-score-2">0/${fields.length} Fields</span>
          </button>
        </h2>
        <div id="val-${form}-panel"
             class="accordion-collapse collapse${i === 0 ? ' show' : ''}"
             data-bs-parent="#valAccordion">
          <div class="accordion-body p-3"><div class="val-list">${items}</div></div>
        </div>
      </div>`;
  }).join('');
}

function updateValidation() {
  let totalComplete = 0;
  let totalFields   = 0;
  let formsComplete = 0;

  // Step 1–2: feature extraction + rule application
  const result = runValidationRules(getComputedValue, state.data);
  lastValidationResult = result;
  window.lastValidationResult = result;

  VAL_FORM_KEYS.forEach(form => {
    const fields = VAL_FIELDS[form];
    let formComplete = 0;
    totalFields += fields.length;

    fields.forEach(({ key }) => {
      const val  = getComputedValue(key);
      const item = document.querySelector(`.val-item[data-field="${key}"][data-form="${form}"]`);
      if (!item) return;
      const status = item.querySelector('.val-status');
      if (val) {
        formComplete++; totalComplete++;
        item.classList.add('complete');
        // Done items sink below the ones still needing attention.
        item.style.order = '1';
        if (status) status.textContent = 'Filled in';
      } else {
        item.classList.remove('complete');
        item.style.order = '0';
        if (status) status.textContent = 'Not filled in yet';
      }
    });

    const scoreText = `${formComplete} of ${fields.length} filled in`;
    const scoreEl   = document.getElementById(`val-${form}-score`);
    if (scoreEl)    scoreEl.textContent = scoreText;
    const scoreEl2  = document.getElementById(`val-${form}-score-2`);
    if (scoreEl2)   scoreEl2.textContent = scoreText;

    const statusEl = document.getElementById(`status-${form}`);
    if (statusEl) {
      if (formComplete === fields.length) {
        formsComplete++;
        statusEl.innerHTML = '<span class="badge badge-ready">Ready to print</span>';
      } else if (formComplete > 0) {
        statusEl.innerHTML = `<span class="badge badge-pending">Not finished (${formComplete} of ${fields.length})</span>`;
      } else {
        statusEl.innerHTML = '<span class="badge badge-pending">Not started</span>';
      }
    }

    const pct = Math.round((formComplete / fields.length) * 100);
    const bar = document.getElementById(`prog-${form}-bar`);
    if (bar) bar.style.width = pct + '%';
  });

  const overall     = Math.round((totalComplete / totalFields) * 100);
  const scoreVal    = document.getElementById('scoreValue');
  const scoreCircle = document.getElementById('scoreCircle');
  const legComp     = document.getElementById('legendComplete');
  const legMiss     = document.getElementById('legendMissing');
  const legTotal    = document.getElementById('legendTotal');
  const progBar     = document.getElementById('overallProgress');
  const progPct     = document.getElementById('progressPct');
  const statVal     = document.getElementById('statValidation');
  const statForms   = document.getElementById('statForms');

  if (scoreVal)    scoreVal.textContent  = overall + '%';
  if (legComp)     legComp.textContent   = totalComplete;
  if (legMiss)     legMiss.textContent   = totalFields - totalComplete;
  if (legTotal)    legTotal.textContent  = totalFields;
  if (progBar)     progBar.style.width   = overall + '%';
  if (progPct)     progPct.textContent   = overall + '%';
  if (scoreCircle) {
    // --score drives the ring's conic-gradient; the state class picks the
    // colour so the number is never the only thing carrying the message.
    scoreCircle.style.setProperty('--score', overall);
    scoreCircle.classList.remove('is-low', 'is-mid', 'is-good', 'is-done');
    scoreCircle.classList.add(
      overall === 100 ? 'is-done' : overall >= 75 ? 'is-good'
      : overall >= 40 ? 'is-mid' : 'is-low');
  }
  if (statForms)   statForms.textContent = `${formsComplete} / ${VAL_FORM_KEYS.length}`;
  if (statVal)     statVal.textContent   =
    overall === 0 ? 'Not started' : overall < 50 ? 'Just started' : overall < 100 ? 'Almost done' : 'All done';

  // Steps 7–8: compile and dispatch rule feedback
  renderRuleFeedback(result);
  applyInlineFieldFlags(result);
  updateExportGate(result);
  renderSigningChecklist(result);
}

/* ══════════════════════════════════════════════════════════
   RULE FEEDBACK — critical errors first, then warnings
══════════════════════════════════════════════════════════ */
function renderRuleFeedback(result) {
  const host = document.getElementById('ruleFeedback');
  if (!host) return;

  const { critical, warnings } = result;

  if (!critical.length && !warnings.length) {
    host.innerHTML =
      '<div class="rule-ok"><i class="bi bi-check-circle-fill me-2"></i>' +
      'No validation issues found. All required fields are complete and consistent.</div>';
    return;
  }

  const row = v => `
    <div class="rule-item rule-${v.severity.cls}" data-rule="${v.id}">
      <div class="rule-item-head">
        <span class="rule-badge rule-badge-${v.severity.cls}">${v.severity.label}</span>
        <code class="rule-id">${v.id}</code>
        <span class="rule-category">${v.category}</span>
      </div>
      <div class="rule-message">${v.message}</div>
      ${v.field ? `<button class="rule-fix-btn" data-fix-field="${v.field}">Fix this <i class="bi bi-arrow-right"></i></button>` : ''}
    </div>`;

  host.innerHTML = `
    ${critical.length ? `
      <div class="rule-group-label text-danger">
        <i class="bi bi-exclamation-octagon-fill me-1"></i>
        Critical errors — these block PDF generation (${critical.length})
      </div>
      ${critical.map(row).join('')}` : ''}
    ${warnings.length ? `
      <div class="rule-group-label text-warning-emphasis mt-3">
        <i class="bi bi-exclamation-triangle-fill me-1"></i>
        Warnings — review before printing (${warnings.length})
      </div>
      ${warnings.map(row).join('')}` : ''}
  `;

  host.querySelectorAll('[data-fix-field]').forEach(btn => {
    btn.addEventListener('click', () => focusField(btn.dataset.fixField));
  });
}

/* Jump to the first input bound to a key and highlight it. */
function focusField(key) {
  const el = document.querySelector(`[data-autofill="${key}"]`) ||
             document.querySelector(`[data-box-key="${key}"]`);
  if (!el) return;
  const section = el.closest('.content-section');
  if (section && !section.classList.contains('active')) {
    navigateTo(section.id.replace('section-', ''));
  }
  setTimeout(() => {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const target = el.matches('input,select,textarea') ? el : el.querySelector('input,select,textarea');
    if (target) target.focus({ preventScroll: true });
    el.classList.add('field-flash');
    setTimeout(() => el.classList.remove('field-flash'), 1600);
  }, 120);
}

/* ══════════════════════════════════════════════════════════
   INLINE FIELD FLAGS — mark offending inputs where they live,
   so staff see problems during encoding and not only on the
   Validation Checker page.
══════════════════════════════════════════════════════════ */
function applyInlineFieldFlags(result) {
  document.querySelectorAll('.field-invalid, .field-warn').forEach(el => {
    el.classList.remove('field-invalid', 'field-warn');
    el.removeAttribute('title');
  });
  document.querySelectorAll('.field-rule-note').forEach(n => n.remove());

  result.violations.forEach(v => {
    if (!v.field) return;
    const targets = document.querySelectorAll(
      `[data-autofill="${v.field}"], [data-box-key="${v.field}"]`);
    targets.forEach(el => {
      el.classList.add(v.severity.critical ? 'field-invalid' : 'field-warn');
      el.setAttribute('title', `${v.id}: ${v.message}`);
      const anchor = el.closest('.col-12, .col-4, .col-6, .col-md-6, .col-md-4') || el.parentElement;
      if (anchor && !anchor.querySelector('.field-rule-note')) {
        const note = document.createElement('div');
        note.className = 'field-rule-note ' +
          (v.severity.critical ? 'field-rule-note--danger' : 'field-rule-note--warn');
        note.innerHTML =
          `<i class="bi ${v.severity.critical ? 'bi-exclamation-circle-fill' : 'bi-exclamation-triangle-fill'} me-1"></i>` +
          `${v.message}`;
        anchor.appendChild(note);
      }
    });
  });
}

/* ══════════════════════════════════════════════════════════
   EXPORT GATE — PDFs generate only once every critical error
   is resolved (research design §3.4.2.5, step 10).
══════════════════════════════════════════════════════════ */
function updateExportGate(result) {
  const blocked = !result.canGeneratePDF;
  const reason  = blocked
    ? 'Not ready yet: ' + result.critical.length + ' important thing' +
      (result.critical.length === 1 ? ' is' : 's are') + ' still missing or wrong'
    : '';

  VAL_FORM_KEYS.forEach(form => {
    const btn = document.getElementById('export-' + form + '-btn');
    if (!btn) return;
    btn.classList.toggle('is-blocked', blocked);
    btn.setAttribute('title', reason || 'Save the filled form as a PDF, ready to print');
  });

  const banner = document.getElementById('exportGateBanner');
  if (banner) {
    banner.style.display = blocked ? '' : 'none';
    const txt = document.getElementById('exportGateText');
    if (txt) txt.textContent = reason;
  }
}

/* ══════════════════════════════════════════════════════════
   SIGNING CHECKLIST — produced before printing; lists the
   wet-ink signatures the claim requires.
══════════════════════════════════════════════════════════ */
function renderSigningChecklist(result) {
  const host = document.getElementById('signingChecklist');
  if (!host) return;
  host.innerHTML = result.signingChecklist.map(item => `
    <div class="signing-item">
      <i class="bi bi-pen me-2 text-primary"></i>
      <span>${item.text}</span>
      <code class="rule-id ms-auto">${item.id}</code>
    </div>`).join('');
}

/* ══════════════════════════════════════════════════════════
   DASHBOARD STATS
══════════════════════════════════════════════════════════ */
function updateDashboardStats() {
  const el = document.getElementById('statFields');
  if (!el) return;
  let total = 0;
  PREVIEW_MAP.forEach(([, key]) => { if (getComputedValue(key)) total++; });
  el.textContent = total;
}

/* ══════════════════════════════════════════════════════════
   SAMPLE DATA
══════════════════════════════════════════════════════════ */
/* Set state.data and every bound input from `values` (form key -> value);
   keys not in `values` are left as they are. Shared by the sample data
   loader and js/claim-loader.js (claims loaded from the OCR review). */
function applyFormData(values) {
  Object.assign(state.data, values);
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    if (!(key in values)) return;
    if (el.type === 'radio') el.checked = el.value === values[key];
    else if (el.type === 'checkbox') el.checked = !!values[key];
    else el.value = values[key];
  });
  updateFormPreviews();
}

/* Blank every field (AM/PM radios back to their AM default). */
function resetFormData() {
  const AM_DEFAULTS = { amPmAdmitted:'AM', amPmDischarge:'AM', amPmDelivery:'AM' };
  Object.keys(state.data).forEach(k => {
    state.data[k] = AM_DEFAULTS[k] || (typeof state.data[k] === 'boolean' ? false : '');
  });
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    if (el.type === 'radio') el.checked = el.value === AM_DEFAULTS[key];
    else if (el.type === 'checkbox') el.checked = false;
    else el.value = '';
  });
  updateFormPreviews();
}

function loadSampleData() {
  applyFormData(SAMPLE_DATA);
  showToast('Sample data loaded', 'All fields populated with fictional demo data.', 'success');
  logActivity('Sample data loaded for demonstration', 'success');
  navigateTo('patient');
}

document.getElementById('clearFormBtn').addEventListener('click', () => {
  if (!confirm('Start a new patient?\n\nThis clears everything typed for the current patient. ' +
               'Press OK to clear, or Cancel to keep it.')) return;
  resetFormData();
  showToast('Form cleared', 'All patient information has been cleared.', 'info');
  logActivity('Patient information cleared', 'warning');
});

/* ══════════════════════════════════════════════════════════
   ACTIVITY FEED
══════════════════════════════════════════════════════════ */
function logActivity(text, type = 'info') {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;
  // A coloured left edge replaces the old status icon: the same four states
  // stay distinguishable without adding another symbol to read.
  const states = ['success', 'warning', 'info', 'danger'];
  const li = document.createElement('li');
  li.className = 'activity-item activity-item--' +
                 (states.includes(type) ? type : 'info');
  li.innerHTML = `<div class="activity-body">
      <div class="activity-text">${escHtml(text)}</div>
      <div class="activity-time">Just now</div>
    </div>`;
  feed.insertBefore(li, feed.firstChild);
  while (feed.children.length > 8) feed.removeChild(feed.lastChild);
}

/* ══════════════════════════════════════════════════════════
   TOAST
══════════════════════════════════════════════════════════ */
function showToast(title, message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const c = {
    success:{ bg:'#F0FDF4', border:'#86EFAC', title:'#166534', icon:'bi-check-circle-fill text-success' },
    info:   { bg:'#EFF6FF', border:'#BFDBFE', title:'#1E40AF', icon:'bi-info-circle-fill text-primary' },
    danger: { bg:'#FEF2F2', border:'#FECACA', title:'#991B1B', icon:'bi-x-circle-fill text-danger' },
    warning:{ bg:'#FFFBEB', border:'#FDE68A', title:'#78350F', icon:'bi-exclamation-triangle-fill text-warning' },
  }[type] || {};
  const div = document.createElement('div');
  div.className = 'toast pca-toast show'; div.setAttribute('role','alert');
  div.style.cssText = `background:${c.bg};border:1px solid ${c.border};`;
  div.innerHTML = `<div class="toast-header" style="background:${c.bg};color:${c.title};">
    <i class="bi ${c.icon} me-2"></i><strong class="me-auto">${escHtml(title)}</strong>
    <button type="button" class="btn-close btn-close-sm ms-2" onclick="this.closest('.toast').remove()"></button>
  </div><div class="toast-body" style="color:${c.title};">${escHtml(message)}</div>`;
  container.appendChild(div);
  setTimeout(() => div.remove(), 10000);
}

/* ══════════════════════════════════════════════════════════
   UTILITIES
══════════════════════════════════════════════════════════ */
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ══════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════ */
buildValidationAccordion();
bindInputListeners();
bindBoxGroupListeners();
markPatientOwnedFields();
updateFormPreviews();

const initialSection = VALID_SECTIONS.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'dashboard';
navigateTo(initialSection);

window.addEventListener('hashchange', () => {
  const section = location.hash.slice(1);
  if (VALID_SECTIONS.includes(section) && section !== state.currentSection) {
    navigateTo(section, { skipHash: true });
  }
});

// Add this at the very bottom of js/app.js
window.state = state;
/* ══════════════════════════════════════════════════════════
   MY PROFILE
   Account details are read-only (an administrator sets them,
   §3.8); the password is the one thing a user changes here.
══════════════════════════════════════════════════════════ */
function fillProfileSection(user) {
  if (!user) return;
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
  set('profileFullName', user.full_name);
  set('profileEmail',    user.email);
  set('profileRole',     PCAAuth.roleLabel(user.role));
  set('profileLastLogin',
      user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'First sign-in');
}

(function setupPasswordChange() {
  const btn = document.getElementById('changePasswordBtn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const current = document.getElementById('pwCurrent').value;
    const next    = document.getElementById('pwNew').value;
    const confirm = document.getElementById('pwConfirm').value;

    if (!current || !next) {
      showToast('Missing details', 'Enter your current and new password.', 'warning');
      return;
    }
    if (next !== confirm) {
      showToast('Passwords do not match', 'The new password and its confirmation differ.', 'warning');
      return;
    }

    btn.disabled = true;
    const result = await PCAAuth.changePassword(current, next);
    btn.disabled = false;

    if (!result.ok) {
      showToast('Could not update password', result.error, 'danger');
      return;
    }
    ['pwCurrent', 'pwNew', 'pwConfirm'].forEach(id => {
      document.getElementById(id).value = '';
    });
    showToast('Password updated', 'Use your new password the next time you sign in.', 'success');
    logActivity('Account password changed', 'success');
  });
})();

/* ══════════════════════════════════════════════════════════
   STAFF ACCOUNTS (administrators)
   New sign-ups are switched off until approved here (§3.8).
   The backend re-checks the admin role on every call; hiding
   this card from encoders is only for tidiness.
══════════════════════════════════════════════════════════ */
function escapeAccountText(value) {
  const div = document.createElement('div');
  div.textContent = value == null ? '' : String(value);
  return div.innerHTML;
}

async function loadStaffAccounts() {
  const body = document.getElementById('usersTableBody');
  if (!body) return;
  const result = await PCAAuth.listUsers();
  if (!result.ok) {
    body.innerHTML = `<tr><td colspan="6" class="text-danger">${escapeAccountText(result.error)}</td></tr>`;
    return;
  }
  const me = window.currentUser && window.currentUser.id;
  // Accounts waiting for approval first, so they are not missed.
  const users = result.users.slice().sort((a, b) =>
    (!a.last_login_at && !a.is_active ? 0 : 1) - (!b.last_login_at && !b.is_active ? 0 : 1));

  body.innerHTML = users.map(u => {
    const pending = !u.is_active && !u.last_login_at;
    const status = u.is_active
      ? '<span class="badge bg-success-subtle text-success-emphasis">Active</span>'
      : pending
        ? '<span class="badge bg-warning-subtle text-warning-emphasis">Waiting for approval</span>'
        : '<span class="badge bg-secondary-subtle text-secondary-emphasis">Switched off</span>';
    const self = u.id === me;
    const toggle = u.is_active
      ? (self ? '' : `<button class="btn btn-sm btn-outline-danger" data-action="deactivate" data-id="${u.id}">Switch off</button>`)
      : `<button class="btn btn-sm btn-success" data-action="activate" data-id="${u.id}">${pending ? 'Approve' : 'Switch on'}</button>`;
    return `<tr>
      <td>${escapeAccountText(u.full_name)}${self ? ' <span class="text-muted small">(you)</span>' : ''}</td>
      <td>${escapeAccountText(u.email)}</td>
      <td>${escapeAccountText(PCAAuth.roleLabel(u.role))}</td>
      <td>${status}</td>
      <td class="small">${u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—'}</td>
      <td class="text-end text-nowrap">
        ${toggle}
        ${self ? '' : `<button class="btn btn-sm btn-outline-secondary ms-1" data-action="password" data-id="${u.id}"
            data-name="${escapeAccountText(u.full_name)}">New password</button>`}
      </td>
    </tr>`;
  }).join('') || '<tr><td colspan="6" class="text-muted">No accounts yet.</td></tr>';
}

(function setupStaffAccounts() {
  const body = document.getElementById('usersTableBody');
  if (!body) return;
  let resetUserId = null;

  document.getElementById('refreshUsersBtn').addEventListener('click', loadStaffAccounts);

  body.addEventListener('click', async e => {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const id = Number(btn.dataset.id);

    if (btn.dataset.action === 'password') {
      resetUserId = id;
      document.getElementById('resetPwFor').textContent = btn.dataset.name;
      document.getElementById('resetPwNew').value = '';
      document.getElementById('resetPwConfirm').value = '';
      bootstrap.Modal.getOrCreateInstance(document.getElementById('resetPasswordModal')).show();
      return;
    }

    const activate = btn.dataset.action === 'activate';
    btn.disabled = true;
    const result = await PCAAuth.setUserActive(id, activate);
    if (!result.ok) {
      btn.disabled = false;
      showToast('Could not update the account', result.error, 'danger');
      return;
    }
    showToast(activate ? 'Account approved' : 'Account switched off',
              `${escapeAccountText(result.user.full_name)} ${activate ? 'can now sign in.' : 'can no longer sign in.'}`,
              activate ? 'success' : 'info');
    loadStaffAccounts();
  });

  document.getElementById('resetPwSaveBtn').addEventListener('click', async function () {
    const pw = document.getElementById('resetPwNew').value;
    const confirm = document.getElementById('resetPwConfirm').value;
    if (!pw) { showToast('Missing password', 'Type the new password.', 'warning'); return; }
    if (pw !== confirm) { showToast('Passwords do not match', 'Type the same password in both boxes.', 'warning'); return; }

    this.disabled = true;
    const result = await PCAAuth.resetUserPassword(resetUserId, pw);
    this.disabled = false;
    if (!result.ok) { showToast('Could not set the password', result.error, 'danger'); return; }
    bootstrap.Modal.getInstance(document.getElementById('resetPasswordModal')).hide();
    showToast('Password set', 'Give the new password to the staff member in person.', 'success');
  });
})();

/* ══════════════════════════════════════════════════════════
   CLINIC SETTINGS
   Table 3.1 lists clinic name, accreditation number and address as
   "System settings (entered once)". Loading them here fills the same
   fields on CF2/CF4, so they are never retyped per claim.
══════════════════════════════════════════════════════════ */
const CLINIC_FIELDS = {
  clinicName:     'hciName',
  clinicPAN:      'hciPAN',
  clinicBldg:     'hciBldg',
  clinicStreet:   'hciStreet',
  clinicCity:     'hciCity',
  clinicProvince: 'hciProvince',
  clinicZip:      'hciZip',
};

async function loadClinicSettings() {
  if (typeof PCAAuth === 'undefined') return;
  const settings = await PCAAuth.getClinicSettings();
  if (!settings) return;

  // Fill the Settings inputs...
  Object.entries(CLINIC_FIELDS).forEach(([inputId, key]) => {
    const el = document.getElementById(inputId);
    if (el) el.value = settings[key] || '';
  });
  const savedAt = document.getElementById('clinicSavedAt');
  if (savedAt && settings.updated_at) {
    savedAt.textContent = 'Last saved ' + new Date(settings.updated_at).toLocaleString();
  }

  // ...and seed the claim forms, without overwriting anything already typed.
  let changed = false;
  Object.values(CLINIC_FIELDS).forEach(key => {
    if (settings[key] && !state.data[key]) { state.data[key] = settings[key]; changed = true; }
  });
  if (changed) updateFormPreviews();
}

(function setupClinicSettings() {
  const btn = document.getElementById('saveClinicBtn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const payload = {};
    Object.entries(CLINIC_FIELDS).forEach(([inputId, key]) => {
      const el = document.getElementById(inputId);
      if (el) payload[key] = el.value.trim();
    });

    btn.disabled = true;
    const result = await PCAAuth.saveClinicSettings(payload);
    btn.disabled = false;

    if (!result.ok) {
      showToast('Could not save', result.error, 'danger');
      return;
    }
    // Apply immediately so the open forms pick the new details up.
    Object.entries(CLINIC_FIELDS).forEach(([, key]) => {
      if (result.settings[key]) state.data[key] = result.settings[key];
    });
    updateFormPreviews();
    const savedAt = document.getElementById('clinicSavedAt');
    if (savedAt) savedAt.textContent = 'Last saved just now';
    showToast('Clinic details saved',
              'These now fill in automatically on CF2 and CF4.', 'success');
    logActivity('Clinic details updated', 'success');
  });
})();
