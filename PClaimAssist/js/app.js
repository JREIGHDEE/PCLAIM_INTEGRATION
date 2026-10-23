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
  /* Parts of a form the clinic has marked as not applying to this patient,
     keyed "<form>|<heading>". Kept beside data, not inside it: these are a
     note about the claim, not a value printed on it. */
  notNeeded: {},
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
    csfSeries:'',
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
    /* Referral */
    referredByHCI:'', referralHciName:'', referralStreet:'', referralCity:'',
    referralProvince:'', referralZip:'',
    /* Discharge Diagnosis table (2 diagnoses x up to 3 procedures each) */
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
    /* PMRF – Dependent 1 extras (shares patientLastName/FirstName/etc with CSF) */
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
  csfSeries:'2026000123456',
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
  'dep2DOB','dep3DOB','dep4DOB','memberSignatureDate',
]);

/* "JUAN D. CRUZ" — the form prints this above the signature line, so it has
   to fit a narrow box. Middle name becomes a single initial. */
function signatureName(first, middle, last) {
  const f = (first || '').trim();
  const l = (last || '').trim();
  if (!f && !l) return '';
  const m = (middle || '').trim();
  const initial = m ? m.charAt(0).toUpperCase() + '.' : '';
  return [f, initial, l].filter(Boolean).join(' ');
}

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

    // Printed above a signature line. The clinic asked for the name to be
    // printed so staff only have to sign: handwriting it was running over
    // the small boxes on the form. "First M. Last" keeps it short.
    case 'memberSignName':
      return signatureName(d.memberFirstName, d.memberMiddleName, d.memberLastName);
    case 'patientSignName':
      return signatureName(d.patientFirstName, d.patientMiddleName, d.patientLastName);

    // Shown with a peso sign on the form, as it is on the printed PMRF.
    case 'monthlyIncomeDisplay': {
      const amount = (d.monthlyIncome || '').trim();
      return amount ? '₱' + amount.replace(/^₱\s*/, '') : '';
    }
    // The course in the ward is typed as dated lines, not one box. It
    // counts as filled when any line has an order written on it.
    case 'cf4CourseInWard': {
      for (let i = 1; i <= 15; i++) {
        const order = (d['cf4CourseOrder' + i] || '').trim();
        if (order) return order;
      }
      return '';
    }
    // Drugs are typed as a table, not one box. Counted as filled when any
    // line names a medicine; the left and right halves both count.
    case 'cf4DrugsAdministered': {
      for (let i = 1; i <= 7; i++) {
        const left = (d['cf4DrugName' + i] || '').trim();
        if (left) return left;
        const right = (d['cf4DrugName' + i + 'b'] || '').trim();
        if (right) return right;
      }
      return '';
    }
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
    case 'timeAdmittedAM':   return isPMTime(d.timeAdmitted) === false ? bareTime(d.timeAdmitted) : '';
    case 'timeAdmittedPM':   return isPMTime(d.timeAdmitted) === true  ? bareTime(d.timeAdmitted) : '';
    case 'timeDischargeAM':  return isPMTime(d.timeDischarge) === false ? bareTime(d.timeDischarge) : '';
    case 'timeDischargePM':  return isPMTime(d.timeDischarge) === true  ? bareTime(d.timeDischarge) : '';
    /* HCI Accreditation No. (PAN): one character per ruled digit box */
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
  /* Part I: HCI */
  /* Part II: Patient Confinement */
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
const VALID_SECTIONS = ['dashboard','patient','csf','cf4','pmrf','validation','profile','settings'];

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
  refreshRedMarksSoon();   // the form just opened shows its red boxes at once
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
  memberNoPhilhealth: 'patientNoPhilhealth',
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

/* "No PhilHealth" beside the patient's and the member's PIN on Patient
   details: that PIN is then not asked for (keyIsSkipped) and its boxes are
   greyed out. What was typed stays, and is back in use when the tick is
   taken off. The member's tick follows the patient's while the patient is
   the member (MEMBER_FROM_PATIENT). Kept with this patient only: neither is
   one of the database's claim fields. */
const NO_PHILHEALTH = { patientPIN: 'patientNoPhilhealth', memberPIN: 'memberNoPhilhealth' };

/* True for a PIN whose "No PhilHealth" is ticked (also read by js/easy.js). */
function pinNotAsked(key) {
  return !!(NO_PHILHEALTH[key] && state.data[NO_PHILHEALTH[key]]);
}

function applyNoPhilhealth() {
  Object.entries(NO_PHILHEALTH).forEach(([pinKey, tickKey]) => {
    const none = !!state.data[tickKey];
    // The member's PIN is also locked while it is copied from the patient.
    const locked = none || (pinKey === 'memberPIN' && !!state.data.memberIsPatient);
    const why = none ? 'Not needed: no PhilHealth'
              : locked ? 'Filled from the patient\'s details (the patient is the member)' : '';
    // Only the boxes on Patient details: the forms' copies are read-only
    // already (lockToPatientDetails).
    document.querySelectorAll(`#section-patient [data-autofill="${pinKey}"]`).forEach(el => {
      const pinBoxes = el.nextElementSibling;
      if (!pinBoxes || !pinBoxes.classList.contains('pin-boxes')) return;
      pinBoxes.querySelectorAll('.pin-box').forEach(box => { box.disabled = locked; box.title = why; });
    });
  });
}

function updateFormPreviews() {
  applyMemberIsPatient();
  applyNoPhilhealth();
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
  // Course-in-the-ward lines may have been filled from a saved claim, so
  // reveal as many as hold data once the boxes are written.
  if (window.PCACourseRows) setTimeout(window.PCACourseRows.refresh, 0);
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
   consistent across the forms that share them.
   A target the user has deliberately edited is left alone. */
/* Most boxes that mean the same thing on several forms are one key (e.g.
   patientLastName on Patient details, CSF, CF4, PMRF), so typing it
   anywhere fills it everywhere. These are separate keys on different
   forms for the same fact: typing in any of them fills the others (both
   ways), on the rule above. */
const LINKED_FIELD_GROUPS = [
  ['dischargeDx', 'dxADiagnosis', 'cf4FinalDiagnosis'],
  ['chiefComplaint', 'cf4ChiefComplaint'],
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
const FREE_TEXT_TYPES = new Set(['text', 'search', 'tel', 'url', 'textarea', '']);

function toFormCase(el) {
  const raw = typeof el.value === 'string' ? el.value.trim() : el.value;
  if (typeof raw !== 'string') return raw;
  // A dropdown's value comes from its own <option> list, not from typing.
  // Upper-casing it would produce a value no option carries, and assigning
  // that back clears the dropdown - which is what emptied these boxes.
  // Dates, times, email and anything marked data-keep-case are left alone
  // for the same reason: their value has a format of its own.
  const kind = el.tagName === 'TEXTAREA' ? 'textarea' : (el.type || '');
  if (el.tagName === 'SELECT' || !FREE_TEXT_TYPES.has(kind) ||
      el.dataset.keepCase !== undefined) return raw;
  // Upper-case what is in the box WITHOUT trimming it: writing the trimmed
  // text back deleted the space the moment it was typed, so no one could
  // type a second word. Trimming belongs to the stored value only.
  const shown = el.value.toUpperCase();
  if (el.value !== shown) {
    const at = el.selectionStart;
    el.value = shown;
    if (at !== null && at !== undefined && el.setSelectionRange) {
      try { el.setSelectionRange(at, at); } catch (e) { /* no text selection */ }
    }
  }
  return raw.toUpperCase();
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
const FORM_SECTIONS = ['csf', 'cf4', 'pmrf'];
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
    // No note at the top of the form: each grey box says where it is
    // changed when pointed at (its title, set in lockToPatientDetails).
  });
}

/* ══════════════════════════════════════════════════════════
   PARTS THAT DO NOT APPLY TO THIS PATIENT
   Not every part of a form is wanted every time - a patient
   with no employer, no referral, no TB-DOTS or newborn care
   package. Those boxes would sit outlined red for ever, and
   the form would never read as finished. Each part heading
   carries a "Not needed" tick box: ticking it greys the part,
   stops its boxes being marked, and leaves it out of the
   count on the checker.
══════════════════════════════════════════════════════════ */
function partId(form, heading) {
  return form + '|' + heading.replace(/\s+/g, ' ').trim().toLowerCase();
}

/* Headings sit beside their fields rather than wrapping them, so each
   heading and the rows that follow it are gathered into one box first -
   there is otherwise nothing to grey out or skip. */
function groupEntryParts() {
  FORM_SECTIONS.forEach(form => {
    const section = document.getElementById('section-' + form);
    if (!section) return;
    const panel = section.querySelector('.entry-panel-body') ||
                  section.querySelector('.form-entry-panel');
    if (!panel || panel.querySelector('.entry-part')) return;

    // A heading is not always a direct child of the panel - CSF 4 and the
    // later pages of CSF 2 keep theirs inside a .pdf-page-group - so each
    // one is gathered among its own siblings rather than the panel's.
    Array.from(panel.querySelectorAll('.entry-section-title')).forEach(title => {
      if (title.closest('.entry-part')) return;
      const container = title.parentElement;
      if (!container) return;
      const heading = title.textContent.trim();
      const wrap = document.createElement('div');
      wrap.className = 'entry-part';
      wrap.dataset.partId = partId(form, heading);
      container.insertBefore(wrap, title);
      let node = title;
      // Stop at the next heading, and at any block that carries headings of
      // its own - CSF 2 keeps its later pages in such a block, and swallowing
      // it would hide those parts inside this one.
      const boundary = n => n !== title && n.nodeType === 1 &&
        (n.classList.contains('entry-section-title') ||
         n.classList.contains('entry-page-nav') ||
         n.querySelector('.entry-section-title'));
      while (node && !boundary(node)) {
        const next = node.nextSibling;
        wrap.appendChild(node);
        node = next;
      }
      addNotNeededTick(wrap, heading);
    });
  });
}

function addNotNeededTick(wrap, heading) {
  const title = wrap.querySelector('.entry-section-title');
  if (!title || title.querySelector('.part-skip')) return;
  const id = wrap.dataset.partId;
  const label = document.createElement('label');
  label.className = 'part-skip';
  label.innerHTML =
    '<input type="checkbox" class="part-skip-box">' +
    '<span>Not needed</span>';
  const box = label.querySelector('input');
  box.checked = !!state.notNeeded[id];
  box.setAttribute('aria-label', 'Mark "' + heading + '" as not needed for this patient');
  box.addEventListener('change', () => {
    if (box.checked) state.notNeeded[id] = true;
    else delete state.notNeeded[id];
    applyNotNeededParts();
    updateFormPreviews();
  });
  title.appendChild(label);
}

function applyNotNeededParts() {
  document.querySelectorAll('.entry-part').forEach(wrap => {
    const off = !!state.notNeeded[wrap.dataset.partId];
    wrap.classList.toggle('part-not-needed', off);
    const box = wrap.querySelector('.part-skip-box');
    if (box && box.checked !== off) box.checked = off;
  });
}

/* True when a key's box on this form sits in a part marked not needed -
   or it is a PIN whose "No PhilHealth" is ticked (NO_PHILHEALTH). */
function keyIsSkipped(form, key) {
  if (pinNotAsked(key)) return true;
  const name = FIX_FIELD_ALIASES[key] || key;
  const section = document.getElementById('section-' + form);
  if (!section) return false;
  const el = section.querySelector(
    `[data-autofill="${name}"], [data-box-key="${name}"]`);
  return !!(el && el.closest('.part-not-needed'));
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
   Some fields (dates, HCI Accreditation No./PAN) print as
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
      // A one-digit month or day ("3") means 03, as on paper.
      if (group.dataset.boxType === 'date' && box.maxLength === 2) {
        box.addEventListener('blur', () => {
          if (box.value.length === 1) { box.value = '0' + box.value; commitBoxGroup(group); }
        });
      }
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
  // Typed in part: the date stays empty until it is whole, and the boxes
  // keep what was typed instead of being redrawn from that empty date.
  if (!state.data[key] && boxes.some(b => b.value)) group.dataset.unfinished = '';
  else delete group.dataset.unfinished;
  updateFormPreviews();
}

function syncBoxGroupsFromState() {
  document.querySelectorAll('.pca-box-group').forEach(group => {
    if (group.contains(document.activeElement)) return; // don't clobber active typing
    const key   = group.dataset.boxKey;
    const type  = group.dataset.boxType;
    const boxes = Array.from(group.querySelectorAll('.pca-box'));
    const val   = state.data[key] || '';
    if (!val && group.dataset.unfinished !== undefined) return;
    delete group.dataset.unfinished;
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
    const allFields = VAL_FIELDS[form];
    // A part the clinic marked "Not needed" is not counted as missing.
    const fields = allFields.filter(({ key }) => !keyIsSkipped(form, key));
    const skipped = allFields.length - fields.length;
    let formComplete = 0;
    totalFields += fields.length;

    allFields.forEach(({ key }) => {
      const item = document.querySelector(`.val-item[data-field="${key}"][data-form="${form}"]`);
      if (item) item.classList.toggle('skipped', keyIsSkipped(form, key));
    });

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

    const scoreText = `${formComplete} of ${fields.length} filled in`
      + (skipped ? ` · ${skipped} not needed` : '');
    const scoreEl   = document.getElementById(`val-${form}-score`);
    if (scoreEl)    scoreEl.textContent = scoreText;
    const scoreEl2  = document.getElementById(`val-${form}-score-2`);
    if (scoreEl2)   scoreEl2.textContent = scoreText;

    if (formComplete === fields.length) formsComplete++;
    const statusHtml = formComplete === fields.length
      ? '<span class="badge badge-ready">Ready to print</span>'
      : formComplete > 0
        ? `<span class="badge badge-pending">Not finished (${formComplete} of ${fields.length})</span>`
        : '<span class="badge badge-pending">Not started</span>';
    // One badge on the dashboard, one in the form's own header.
    [`status-${form}`, `status-${form}-2`].forEach(id => {
      const statusEl = document.getElementById(id);
      if (statusEl) statusEl.innerHTML = statusHtml;
    });

    // Every part switched off leaves nothing to ask for - that counts as done.
    const pct = fields.length ? Math.round((formComplete / fields.length) * 100) : 100;
    const bar = document.getElementById(`prog-${form}-bar`);
    if (bar) bar.style.width = pct + '%';
  });

  const overall     = totalFields ? Math.round((totalComplete / totalFields) * 100) : 100;
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
  renderFormIssues(result);
  applyInlineFieldFlags(result);
  updateExportGate(result, totalComplete, totalFields);
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

/* ══════════════════════════════════════════════════════════
   ON EACH FORM — what is missing, and which rules are broken
   The same findings as "Check for missing information", shown at the top
   of each form's "Type the details here" panel for that form alone, so
   staff see them while typing instead of only on that page:
     - the boxes of this form still empty (parts marked "Not needed" are
       left out), each with "Fix this";
     - the rules broken for this form (critical in red, warnings in amber):
       a rule's own form, or the form whose boxes hold its field.
   Rules about the claim as a whole (no form, no field) are counted on one
   line that leads to the checker, rather than repeated on every form.
══════════════════════════════════════════════════════════ */
const FORM_ISSUES_OPEN = {};   // folded or not, per form, while the page is open

function formHasField(form, key) {
  if ((VAL_FIELDS[form] || []).some(f => f.key === key)) return true;
  const name = FIX_FIELD_ALIASES[key] || key;
  const section = document.getElementById('section-' + form);
  return !!(section && section.querySelector(`[data-autofill="${name}"], [data-box-key="${name}"]`));
}

function renderFormIssues(result) {
  VAL_FORM_KEYS.forEach(form => {
    const section = document.getElementById('section-' + form);
    const header = section && section.querySelector('.form-entry-panel .entry-panel-header');
    if (!header) return;
    let box = section.querySelector('.form-issues');
    if (!box) {
      box = document.createElement('details');
      box.className = 'form-issues';
      header.insertAdjacentElement('afterend', box);
      box.addEventListener('click', e => {
        // Folded or opened by the person (not when the code sets it).
        if (e.target.closest('summary')) FORM_ISSUES_OPEN[form] = !box.open;
        const fix = e.target.closest('[data-fix-field]');
        if (fix) { e.preventDefault(); focusField(fix.dataset.fixField); }
        const all = e.target.closest('[data-go-validation]');
        if (all) { e.preventDefault(); navigateTo('validation'); }
      });
    }

    const missing = (VAL_FIELDS[form] || []).filter(({ key }) =>
      !keyIsSkipped(form, key) && !getComputedValue(key));
    const mine = v => (v.form && v.form === form) || (!v.form && v.field && formHasField(form, v.field));
    // A missing box already listed above is not listed again as a rule.
    const missingKeys = new Set(missing.map(m => m.key));
    const rules = result.violations.filter(v => mine(v) && !(v.field && missingKeys.has(v.field) &&
      v.category === 'Missing Field'));
    const general = result.violations.filter(v => !v.form && !v.field);
    const critical = rules.filter(v => v.severity.critical);
    const warnings = rules.filter(v => !v.severity.critical);

    const fixBtn = key => key
      ? `<button type="button" class="form-issue-fix" data-fix-field="${escHtml(key)}">Fix this</button>` : '';
    const ruleRow = v => `<li class="form-issue form-issue--${v.severity.critical ? 'critical' : 'warning'}">
        <i class="bi ${v.severity.critical ? 'bi-x-octagon-fill' : 'bi-exclamation-triangle-fill'}" aria-hidden="true"></i>
        <span><code>${escHtml(v.id)}</code> ${v.message}</span>${fixBtn(v.field)}</li>`;
    const missRow = m => `<li class="form-issue form-issue--missing">
        <i class="bi bi-dash-circle" aria-hidden="true"></i>
        <span><strong>${escHtml(m.label)}</strong> is not filled in yet</span>${fixBtn(m.key)}</li>`;

    const counts = [];
    if (missing.length) counts.push(`${missing.length} missing`);
    if (critical.length) counts.push(`${critical.length} must be fixed`);
    if (warnings.length) counts.push(`${warnings.length} to check`);
    const clean = !counts.length;
    box.classList.toggle('form-issues--clean', clean);
    box.classList.toggle('form-issues--critical', critical.length > 0);

    const html = `<summary>
        <i class="bi ${clean ? 'bi-check-circle-fill' : critical.length ? 'bi-exclamation-octagon-fill' : 'bi-exclamation-circle-fill'}" aria-hidden="true"></i>
        <span>${clean ? 'Nothing missing on this form' : 'On this form: ' + counts.join(' · ')}</span>
      </summary>
      ${clean ? '' : `<ul class="form-issue-list">
        ${critical.map(ruleRow).join('')}${missing.map(missRow).join('')}${warnings.map(ruleRow).join('')}
      </ul>`}
      ${general.length ? `<p class="form-issues-general">${general.length} more about the whole claim -
        <a href="#validation" data-go-validation>see Check for missing information</a></p>` : ''}`;
    if (box.dataset.html !== html) {
      box.innerHTML = html;
      box.dataset.html = html;
    }
    box.open = clean ? false : (FORM_ISSUES_OPEN[form] !== undefined ? FORM_ISSUES_OPEN[form] : true);
  });
}

/* Some things the checker asks for are not one box you can type in.
   "Patient Name" is built from the surname and first name; "Course in the
   Ward" and the drug list are whole tables of boxes. Those used to leave
   "Fix this" pointing at nothing, so the button did nothing at all. Each
   one is sent to the first box a person actually fills instead. */
const FIX_FIELD_ALIASES = {
  patientName:  'patientLastName',
  memberName:   'memberLastName',
  motherMaidenName: 'motherLastName',
  spouseName:   'spouseLastName',
  fullAddress:  'addrStreet',
  hciAddress:   'hciStreet',
  obHistory:    'gravida',
  timeAdmittedStr:  'timeAdmitted',
  timeDischargeStr: 'timeDischarge',
  deliveryTimeStr:  'deliveryTime',
  cf4CourseInWard:      'cf4CourseDate1',
  cf4DrugsAdministered: 'cf4DrugName1',
};

/* Where a key can actually be typed.

   A key often has several boxes: the one on Patient details, a read-only
   copy on each form, and sometimes a hidden input behind a row of
   per-character boxes. Jumping to the hidden one scrolls nowhere and
   focuses nothing, and jumping to a read-only copy offers a box that
   refuses typing - both of which made "Fix this" look broken. Prefer, in
   order: a box that takes typing, the visible box row standing in for a
   hidden input, and only then whatever carries the key. */
function editableFieldFor(key) {
  const name = FIX_FIELD_ALIASES[key] || key;
  const all = Array.from(document.querySelectorAll(
    `[data-autofill="${name}"], [data-box-key="${name}"]`));
  if (!all.length) return null;

  // Visibility is no guide here: the checker runs from its own page, so
  // every form section is hidden at the time and would look unusable. What
  // matters is whether the box would take typing once its page is open.
  const usable = el => {
    const input = el.matches('input,select,textarea') ? el
                : el.querySelector('input,select,textarea');
    if (!input) return false;
    return input.type !== 'hidden' && !input.disabled && !input.readOnly;
  };
  const inPatient = el => el.closest('#section-patient') !== null;
  // Most of these are typed on Patient details; go there by choice, so one
  // detail is always corrected in the same place.
  const typed = all.find(el => usable(el) && inPatient(el)) || all.find(usable);
  // A date is typed in the MM/DD/YYYY box standing in for it (js/date-text.js).
  if (typed) return typed.pcaDateText || typed;

  // Discharged the day after delivery: the date follows the delivery date,
  // so the place to go is that tick (keep it and fill the delivery date, or
  // untick it).
  const dayAfter = document.getElementById('dischargeDayAfter');
  if (name === 'dateDischarge' && dayAfter && dayAfter.checked) return dayAfter;

  // Hidden input: show the row of boxes that stands in for it.
  for (const el of all) {
    if (el.id) {
      const row = document.querySelector(`.box-input[data-target="#${el.id}"]`);
      if (row) return row;
    }
    const group = el.closest('.pca-box-group');
    if (group) return group;
  }
  return all[0];
}

/* Jump to where a key is typed and highlight it.

   The box can be out of sight in more than its section: on a Patient
   details tab that is not open, or on a form's other page. Going to the
   section alone then focused nothing - "Fix this" seemed to do nothing for
   dates, civil status, the address and the like - so the tab is opened and
   the page turned first. A row of choice buttons (Member Type) takes the
   focus on its first button. */
function revealForTyping(el) {
  const pane = el.closest('.tab-pane');
  if (pane && !pane.classList.contains('active') && pane.id && window.bootstrap) {
    const tab = document.querySelector(`[data-bs-target="#${pane.id}"], [href="#${pane.id}"]`);
    if (tab) bootstrap.Tab.getOrCreateInstance(tab).show();
  }
  const pageGroup = el.closest('.pdf-page-group[data-pdf-page]');
  if (pageGroup && pageGroup.hidden) {
    const form = pageGroup.closest('.content-section').id.replace('section-', '');
    const page = Number(pageGroup.dataset.pdfPage);
    if (typeof syncEntryPanelPageGroups === 'function') syncEntryPanelPageGroups(form, page);
    if (typeof renderPDFPage === 'function') renderPDFPage(form, page);
  }
}

function focusField(key) {
  const el = editableFieldFor(key);
  if (!el) return;
  const section = el.closest('.content-section');
  if (section && !section.classList.contains('active')) {
    navigateTo(section.id.replace('section-', ''));
  }
  revealForTyping(el);
  // Long enough for a tab's fade to finish, so the box can take the focus.
  setTimeout(() => {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    const target = el.matches('input,select,textarea,button') ? el
                 : el.querySelector('input:not([type=hidden]),select,textarea,button');
    if (target && !target.disabled && !target.readOnly) target.focus({ preventScroll: true });
    el.classList.add('field-flash');
    setTimeout(() => el.classList.remove('field-flash'), 1600);
  }, 350);
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
  markMissingRequiredFields();

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
   MISSING BOXES, MARKED RED ON THE FORM ITSELF
   The checker lists what a form still needs, but the form was
   the one place that didn't say. Every box the checker counts
   (VAL_FIELDS) that has nothing in it is outlined red where it
   lives - on the form, and on Patient details where most of
   them are typed - so a glance at the page shows what is left.
   A box filled from somewhere else is not marked: it is not
   the clinic's to type.
══════════════════════════════════════════════════════════ */
/* Which boxes in a form's "Type the details here" panel are the clinic's
   to fill. Grey ones came from Patient details and must not be typed into;
   everything else is theirs - but an empty white box looks the same as an
   empty box that is simply not needed yet, which is what made it unclear.
   Every box they still have to type is outlined red until it has something
   in it, so the panel reads at a glance: grey, leave it; red, type it. */
function markFieldsNeedingTyping() {
  document.querySelectorAll('.field-needs-typing').forEach(el => {
    el.classList.remove('field-needs-typing');
    if (el.dataset.typeHint !== undefined) {
      el.removeAttribute('title');
      delete el.dataset.typeHint;
    }
  });

  FORM_SECTIONS.forEach(form => {
    const section = document.getElementById('section-' + form);
    if (!section) return;
    const panel = section.querySelector('.entry-panel-body') ||
                  section.querySelector('.form-entry-panel');
    if (!panel) return;

    panel.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.type === 'hidden' || el.disabled || el.readOnly) return;
      if (el.classList.contains('from-patient-details')) return;
      if (el.closest('.from-patient-details')) return;
      // Boxes the page is keeping out of sight are not being asked for.
      if (el.classList.contains('d-none') || el.hidden ||
          el.closest('.d-none, [hidden]')) return;
      if (el.closest('.part-not-needed')) return;
      // A tick box or a choice is never "blank" in the way a typed box is.
      if (el.type === 'checkbox' || el.type === 'radio') return;
      if (String(el.value || '').trim()) return;
      // One outline around a whole row of per-character boxes, not one
      // around each box - eight red squares for a date reads as eight
      // problems rather than one date still to type.
      const row = el.closest(
        '.box-input, .box-input-date, .box-input-time, .pca-box-group');
      const mark = row || el;
      if (row && row.querySelector('.pca-box, .box-input-cell, input')) {
        const anyFilled = Array.from(row.querySelectorAll('input'))
          .some(i => String(i.value || '').trim());
        if (anyFilled) return;
      }
      mark.classList.add('field-needs-typing');
      if (!mark.getAttribute('title')) {
        mark.setAttribute('title', 'This one is for you to type');
        mark.dataset.typeHint = '';
      }
    });
  });
}

/* The red marks are worked out from the boxes on screen, so boxes that
   appear later were left unmarked until the next keystroke or click: the
   per-character rows (built once the page has loaded), a form's second
   page when it is turned to, a course-in-the-ward line shown with "+".
   Each of those asks for the marks again; a burst of asks is one redo. */
function refreshRedMarksSoon() {
  clearTimeout(window.pcaRedMarksTimer);
  window.pcaRedMarksTimer = setTimeout(() => markMissingRequiredFields(), 0);
}
document.addEventListener('DOMContentLoaded', refreshRedMarksSoon);

function markMissingRequiredFields() {
  markFieldsNeedingTyping();
  document.querySelectorAll('.field-missing').forEach(el => {
    el.classList.remove('field-missing');
    if (el.dataset.missingTitle !== undefined) {
      el.removeAttribute('title');
      delete el.dataset.missingTitle;
    }
  });

  const needed = new Map();   // key -> the label the checker uses
  VAL_FORM_KEYS.forEach(form => {
    (VAL_FIELDS[form] || []).forEach(({ key, label }) => {
      if (!keyIsSkipped(form, key) && !getComputedValue(key)) needed.set(key, label);
    });
  });

  needed.forEach((label, key) => {
    const name = FIX_FIELD_ALIASES[key] || key;
    document.querySelectorAll(
      `[data-autofill="${name}"], [data-box-key="${name}"]`).forEach(el => {
      const input = el.matches('input,select,textarea') ? el
                  : el.querySelector('input,select,textarea');
      if (input && input.type === 'hidden') return;
      if (el.closest('.part-not-needed')) return;
      el.classList.add('field-missing');
      if (!el.getAttribute('title')) {
        const where = el.classList.contains('from-patient-details')
          ? ' - type it on the Patient details page'
          : ' - still needs to be filled in';
        el.setAttribute('title', label + where);
        el.dataset.missingTitle = '';
      }
    });
    // A hidden field is typed through its row of per-character boxes, or
    // (a PhilHealth PIN, js/pin-input.js) the three boxes right after it.
    document.querySelectorAll(`[data-autofill="${name}"]`).forEach(el => {
      const row = el.id && document.querySelector(`.box-input[data-target="#${el.id}"]`);
      if (row) row.classList.add('field-missing');
      const pinBoxes = el.nextElementSibling;
      if (el.type === 'hidden' && pinBoxes && pinBoxes.classList.contains('pin-boxes')) {
        pinBoxes.querySelectorAll('.pin-box').forEach(box => box.classList.add('field-missing'));
      }
    });
  });
}

/* ══════════════════════════════════════════════════════════
   EXPORT GATE — PDFs generate only once every critical error
   is resolved (research design §3.4.2.5, step 10).
══════════════════════════════════════════════════════════ */
function updateExportGate(result, totalComplete, totalFields) {
  const blocked = !result.canGeneratePDF;
  const reason  = blocked
    ? 'Not ready yet: ' + result.critical.length + ' important thing' +
      (result.critical.length === 1 ? ' is' : 's are') + ' still missing or wrong'
    : '';

  const banner = document.getElementById('exportGateBanner');
  if (banner) {
    banner.style.display = blocked ? '' : 'none';
    const txt = document.getElementById('exportGateText');
    if (txt) txt.textContent = reason;
  }

  // The forms can be saved at any time, one by one or together; the card
  // says whether anything is still missing. Ready means nothing left to
  // report: every box the checker counts is filled, and no rule is still
  // complaining. Parts marked "Not needed" are already out of that count.
  const ready = !blocked && totalFields > 0 && totalComplete >= totalFields;
  const card  = document.getElementById('exportAllCard');
  if (card) card.classList.toggle('export-all-card--missing', !ready);
  const title = document.getElementById('exportAllTitle');
  const sub   = document.getElementById('exportAllSub');
  const forms = (typeof PDF_FORM_KEYS !== 'undefined' ? PDF_FORM_KEYS : VAL_FORM_KEYS).length;
  if (title) title.innerHTML = ready
    ? '<i class="bi bi-check-circle-fill me-2" aria-hidden="true"></i>Everything is filled in'
    : '<i class="bi bi-exclamation-circle-fill me-2" aria-hidden="true"></i>Some boxes are still empty';
  if (sub) sub.textContent = ready
    ? `All ${forms} forms are ready. Save them, then print.`
    : 'The list below shows what is missing. A form saved now prints with those boxes blank.';
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
    else {
      el.value = values[key];
      // A claim sent from the OCR review is in capitals like anything typed
      // here (toFormCase leaves dates, dropdowns and the like alone).
      if (typeof values[key] === 'string') state.data[key] = toFormCase(el);
    }
  });
  refreshDischargeTick();
  refreshFinalDxTick(values);
  applyFixedFields();
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
  // ...and any date typed only in part.
  document.querySelectorAll('.pca-box-group[data-unfinished]').forEach(group => {
    delete group.dataset.unfinished;
  });
  if (typeof clearUnfinishedEntries === 'function') clearUnfinishedEntries();
  // Discharge back to following the delivery date.
  refreshDischargeTick();
  refreshFinalDxTick();
  // A new patient still has this clinic's fixed values.
  applyFixedFields();
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
/* Fields whose value is fixed for this clinic (manner of delivery, fetal
   outcome). The value lives in the HTML as the input's value attribute,
   and the box is readonly so nobody can change it.

   Read from getAttribute('value'), not el.value: by the time anything
   runs, syncAllAutofillElements() may already have written the empty
   state over the live value, and reading the property back would capture
   that blank for good. The attribute keeps what the markup declared.

   These must show at all times - before a logbook is read, on a brand-new
   patient, and after "Start a new patient" - so applyFixedFields() is
   called again by anything that rewrites the boxes wholesale. */
const FIXED_FIELD_VALUES = (function readFixedFields() {
  const fixed = {};
  document.querySelectorAll('input[readonly][data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    const value = el.getAttribute('value');
    if (value && !(key in fixed)) fixed[key] = value;
  });
  return fixed;
})();

/* Fields that start with a usual value but stay editable (citizenship:
   almost every patient here is FILIPINO). Declared as data-default on the
   input; filled in only while the field is empty, so whatever was typed or
   loaded from a claim is never overwritten. */
const DEFAULT_FIELD_VALUES = (function readDefaultFields() {
  const defaults = {};
  document.querySelectorAll('[data-default][data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    if (!(key in defaults)) defaults[key] = el.dataset.default;
  });
  return defaults;
})();

function applyFixedFields() {
  Object.entries(FIXED_FIELD_VALUES).forEach(([key, value]) => {
    state.data[key] = value;
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      if (el.value !== value) el.value = value;
    });
  });
  Object.entries(DEFAULT_FIELD_VALUES).forEach(([key, value]) => {
    if (String(state.data[key] ?? '').trim()) return;
    state.data[key] = value;
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => { el.value = value; });
  });
}

/* Seed them before the first updateFormPreviews() below, which would
   otherwise sync the still-empty state over these boxes. */
applyFixedFields();

buildValidationAccordion();
bindInputListeners();
bindBoxGroupListeners();
markPatientOwnedFields();
groupEntryParts();
applyNotNeededParts();
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
   fields on CF4, so they are never retyped per claim.
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
              'These now fill in automatically on CF4.', 'success');
    logActivity('Clinic details updated', 'success');
  });
})();

/* ══════════════════════════════════════════════════════════
   DATE DISCHARGED — "the day after delivery"
   A mother goes home the day after delivering at the earliest
   (rule IC-08), most often exactly then, so the date follows the
   delivery date by default. Unticking lets staff type a later
   date for a longer stay.
══════════════════════════════════════════════════════════ */
function dayAfterIso(iso) {
  const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return '';
  const next = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]) + 1);
  return [next.getFullYear(), String(next.getMonth() + 1).padStart(2, '0'),
          String(next.getDate()).padStart(2, '0')].join('-');
}

// Called when a claim is loaded or cleared; the setup below fills in .run.
function refreshDischargeTick() {
  if (refreshDischargeTick.run) refreshDischargeTick.run();
}

(function setupDayAfterDischarge() {
  const toggle = document.getElementById('dischargeDayAfter');
  if (!toggle) return;
  const field = document.querySelector('input[type="date"][data-autofill="dateDischarge"]');
  if (!field) return;

  function apply() {
    const follow = toggle.checked;
    field.readOnly = follow;
    field.classList.toggle('is-locked', follow);
    const next = dayAfterIso(state.data.deliveryDate);
    if (follow && next) {
      state.data.dateDischarge = next;
      field.value = next;
      updateFormPreviews();
    }
  }

  toggle.addEventListener('change', apply);

  // Keep it in step while the delivery date is still being typed.
  document.querySelectorAll('[data-autofill="deliveryDate"]').forEach(el =>
    el.addEventListener('change', () => { if (toggle.checked) apply(); }));

  // A claim loaded with its own discharge date (from the logbook) keeps
  // it: the tick stays on only when that date is the day after delivery.
  refreshDischargeTick.run = () => {
    const given = state.data.dateDischarge;
    toggle.checked = !given || given === dayAfterIso(state.data.deliveryDate);
    apply();
  };

  apply();
})();

/* ══════════════════════════════════════════════════════════
   FINAL DIAGNOSIS — "same as the admission diagnosis"
   Ticked, the final diagnosis is the admission diagnosis and keeps
   following it. It is written as if typed, so the CSF and CF4 copies
   (LINKED_FIELD_GROUPS) follow too. Off by default: the two usually
   differ (in labour on admission, delivered at discharge).
══════════════════════════════════════════════════════════ */
// Called when a claim is loaded or cleared; the setup below fills in .run.
function refreshFinalDxTick(values) {
  if (refreshFinalDxTick.run) refreshFinalDxTick.run(values);
}

(function setupFinalDxSameAsAdmission() {
  const toggle = document.getElementById('finalDxSameAsAdmission');
  if (!toggle) return;
  const field = document.querySelector('#section-patient [data-autofill="dischargeDx"]');
  if (!field) return;

  function apply() {
    const follow = toggle.checked;
    field.readOnly = follow;
    field.classList.toggle('is-locked', follow);
    const admission = state.data.admissionDx || '';
    if (follow && field.value !== admission) {
      field.value = admission;
      field.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }

  toggle.addEventListener('change', apply);

  // Keep it in step with the admission diagnosis, wherever that is typed
  // (Patient details, CF4, or "Put this in the box").
  document.addEventListener('input', e => {
    if (toggle.checked && e.target.dataset && e.target.dataset.autofill === 'admissionDx') apply();
  });

  // A loaded claim (values with a final diagnosis): ticked only when both
  // diagnoses are there and the same. Other updates, such as the delivery
  // message put in the admission diagnosis, leave the tick as it is.
  refreshFinalDxTick.run = values => {
    if (!values || 'dischargeDx' in values) {
      const admission = state.data.admissionDx, final = state.data.dischargeDx;
      toggle.checked = !!admission && admission === final;
    }
    apply();
  };
})();

/* ══════════════════════════════════════════════════════════
   NAMES WRITTEN BY HAND — "leave blank" tick boxes
   The printed name over a signature line is usually written in pen after
   the forms are printed. Each name box (and CSF Part I's two lines) has a
   tick box that leaves that line blank on the form: the box is greyed out
   and no longer asked for, and the line prints empty. What was typed is
   kept, and comes back when the tick is taken off.

   A tick names the overlay lines it blanks (js/pdf/overlays/*.js ids), not
   the field: CSF and PMRF print the member's name from the same field, and
   leaving one form's line blank must not blank the other's. It is the
   clinic's way of working rather than a detail of one patient, so it is
   remembered on this computer and stays for the next patient.
══════════════════════════════════════════════════════════ */
const PCA_HANDWRITTEN = new Set();
(function setupHandwrittenNames() {
  const STORE = 'pclaimassist.handwrittenNames';
  try { (JSON.parse(localStorage.getItem(STORE)) || []).forEach(id => PCA_HANDWRITTEN.add(id)); }
  catch (e) { /* storage off: nothing ticked */ }
  window.PCA_HANDWRITTEN = PCA_HANDWRITTEN;
  const style = document.createElement('style');
  style.textContent = '.handwritten-check-label{display:flex;gap:8px;align-items:flex-start;' +
    'margin:6px 0 0;font-size:.85rem;cursor:pointer}' +
    '.handwritten-check-label .form-check-input{margin:2px 0 0;flex:none}' +
    '.pca-input.is-handwritten{background:#f1f5f9;color:#94a3b8;text-decoration:line-through}';
  document.head.appendChild(style);

  document.querySelectorAll('.handwritten-check[data-handwritten]').forEach(slot => {
    const ids = slot.dataset.handwritten.split(',');
    const input = slot.dataset.handwrittenInput
      ? slot.parentElement.querySelector(`[data-autofill="${slot.dataset.handwrittenInput}"]`) : null;
    const label = document.createElement('label');
    label.className = 'form-check pca-check handwritten-check-label';
    label.innerHTML = '<input type="checkbox" class="form-check-input">' +
      '<span class="form-check-label"></span>';
    label.querySelector('span').textContent = slot.dataset.handwrittenLabel ||
      'Leave blank - the name is written by hand after printing';
    const tick = label.querySelector('input');
    slot.appendChild(label);

    function apply() {
      const on = tick.checked;
      ids.forEach(id => on ? PCA_HANDWRITTEN.add(id) : PCA_HANDWRITTEN.delete(id));
      if (input) {
        input.disabled = on;
        input.classList.toggle('is-handwritten', on);
        input.title = on ? 'Left blank: written by hand after printing' : '';
      }
    }
    tick.checked = ids.every(id => PCA_HANDWRITTEN.has(id));
    apply();
    tick.addEventListener('change', () => {
      apply();
      try { localStorage.setItem(STORE, JSON.stringify([...PCA_HANDWRITTEN])); } catch (e) { /* not remembered */ }
      updateFormPreviews();
    });
  });
})();

/* ══════════════════════════════════════════════════════════
   ADMISSION DIAGNOSIS — the doctors' usual wording
   A claim is only made for a delivery, so the admitting diagnosis is
   nearly always the same sentence (as the clinic's doctors write it):
     PUFT 39 3/7 wks AOG delivered via NSVD to a live term baby boy AGA
     w/ AS of 8 & 9; G2P2 (2002)
   "Use the delivery message" opens it with only its blanks to fill, each
   already filled from what is typed elsewhere where it can be: the weeks
   from the LMP to the delivery (or admission) date, the baby's sex, G, P,
   the term/preterm/abortion/living count and the APGAR score. A blank
   typed here fills that field too, if it was still empty.
══════════════════════════════════════════════════════════ */
(function setupAdmissionDxTemplate() {
  const host = document.getElementById('admissionDxTemplate');
  if (!host) return;

  const style = document.createElement('style');
  style.textContent =
    '.dx-template{margin-top:8px;padding:12px 14px;border:2px solid #bfdbfe;border-radius:10px;background:#f8fbff}' +
    '.dx-template .dx-sentence{line-height:2.6;font-size:.95rem}' +
    '.dx-template input,.dx-template select{display:inline-block;width:3.4em;padding:2px 4px;margin:0 2px;' +
    'border:1px solid #93c5fd;border-radius:6px;text-align:center;font-weight:600;background:#fff}' +
    '.dx-template select{width:auto}' +
    '.dx-template .dx-empty{border-color:#dc2626;background:#fef2f2}' +
    '.dx-template .dx-preview{margin:10px 0;padding:8px 10px;background:#fff;border:1px dashed #94a3b8;border-radius:8px;font-weight:600}' +
    '.dx-template .dx-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}' +
    '.dx-template .dx-confirm{margin-top:10px;padding:10px 12px;border:2px solid #f59e0b;border-radius:10px;background:#fffbeb}' +
    '.dx-template .dx-confirm-title{font-weight:700;color:#92400e;margin-bottom:6px}' +
    '.dx-template .dx-confirm-old{margin-bottom:8px;padding:6px 8px;background:#fff;border-radius:6px;font-size:.88rem;color:#475569}';
  document.head.appendChild(style);

  const open = document.createElement('button');
  open.type = 'button';
  open.className = 'btn btn-outline-primary btn-sm mt-2';
  open.innerHTML = '<i class="bi bi-magic me-1"></i>Use the delivery message';
  host.appendChild(open);

  const box = document.createElement('div');
  box.className = 'dx-template';
  box.hidden = true;
  const num = (name, label, w) =>
    `<input type="text" inputmode="numeric" maxlength="2" data-dx="${name}" aria-label="${label}"${w ? ` style="width:${w}"` : ''}>`;
  box.innerHTML =
    '<div class="dx-sentence">PUFT ' + num('weeks', 'Weeks AOG') + ' ' + num('days', 'Days (out of 7)', '2.6em') +
    '/7 wks AOG delivered via NSVD to a live term baby ' +
    '<select data-dx="sex" aria-label="Baby boy or girl"><option value="">boy / girl</option>' +
    '<option value="boy">boy</option><option value="girl">girl</option></select> ' +
    '<select data-dx="size" aria-label="Size for gestational age"><option>AGA</option><option>SGA</option><option>LGA</option></select>' +
    ' w/ AS of ' + num('apgar1', 'APGAR score at 1 minute', '2.6em') + ' &amp; ' + num('apgar5', 'APGAR score at 5 minutes', '2.6em') +
    '; G' + num('g', 'Gravida', '2.6em') + 'P' + num('p', 'Para', '2.6em') + ' (' +
    num('t', 'Term', '2.2em') + num('pre', 'Preterm', '2.2em') + num('a', 'Abortion', '2.2em') + num('l', 'Living', '2.2em') + ')</div>' +
    '<div class="dx-preview" aria-live="polite"></div>' +
    '<div class="dx-actions"><button type="button" class="btn btn-primary btn-sm" data-dx-use>' +
    'Put this in Admission Diagnosis</button><button type="button" class="btn btn-link btn-sm" data-dx-close>Close</button>' +
    '<span class="text-danger small" data-dx-note></span></div>' +
    // Asked here, in the page - not with the browser's own pop-up.
    '<div class="dx-confirm" role="alertdialog" aria-labelledby="dxConfirmTitle" hidden>' +
    '<div class="dx-confirm-title" id="dxConfirmTitle"><i class="bi bi-exclamation-triangle-fill me-2"></i>' +
    'Admission Diagnosis already has something in it</div>' +
    '<div class="dx-confirm-old" data-dx-old></div>' +
    '<div class="dx-actions"><button type="button" class="btn btn-warning btn-sm" data-dx-replace>Replace it</button>' +
    '<button type="button" class="btn btn-outline-secondary btn-sm" data-dx-keep>Keep what is there</button></div></div>';
  host.appendChild(box);

  const f = name => box.querySelector(`[data-dx="${name}"]`);
  const val = name => String(f(name).value || '').trim();
  const PARTS = ['weeks', 'days', 'sex', 'apgar1', 'apgar5', 'g', 'p', 't', 'pre', 'a', 'l'];

  // Weeks + days from the LMP to the delivery (or admission) date.
  function aogFromDates() {
    const d = state.data;
    const end = d.deliveryDate || d.dateAdmitted;
    if (!d.lmp || !end) return null;
    const days = Math.round((new Date(end) - new Date(d.lmp)) / 86400000);
    if (!(days >= 20 * 7 && days <= 45 * 7)) return null;
    return { weeks: Math.floor(days / 7), days: days % 7 };
  }

  function prefill() {
    const d = state.data;
    const aog = aogFromDates();
    const set = (name, value) => { if (value !== undefined && value !== null && value !== '') f(name).value = String(value); };
    PARTS.forEach(name => { f(name).value = ''; });
    f('size').value = 'AGA';
    if (aog) { set('weeks', aog.weeks); set('days', aog.days); }
    set('sex', d.babySex === 'Male' ? 'boy' : d.babySex === 'Female' ? 'girl' : '');
    set('apgar5', d.apgarScore);
    set('g', d.gravida); set('p', d.para);
    set('t', d.obTerm); set('pre', d.obPreterm); set('a', d.obAbortion); set('l', d.obLiving);
    // Anything still blank, from what is already in the box (usually read
    // from the logbook): "PUFT 38 2/7 WKS ... G3P2 (2002)".
    const found = readDxWording(d.admissionDx);
    Object.entries(found).forEach(([name, value]) => {
      if (!f(name).value || (name === 'size' && /AGA|SGA|LGA/.test(String(d.admissionDx).toUpperCase()))) set(name, value);
    });
  }

  // The same reading as the Logbook Reader's (templates/review.html readDx).
  function readDxWording(text) {
    const t = String(text || '').toUpperCase();
    const out = {};
    let m;
    if ((m = t.match(/\b(\d{2})\s*(?:(\d)\s*\/\s*7)?\s*W/))) { out.weeks = m[1]; if (m[2]) out.days = m[2]; }
    if ((m = t.match(/\b(BOY|GIRL)\b/))) out.sex = m[1].toLowerCase();
    if ((m = t.match(/\b(AGA|SGA|LGA)\b/))) out.size = m[1];
    if ((m = t.match(/AS\s*(?:OF)?\s*(\d{1,2})\s*(?:&|AND|,|\/)\s*(\d{1,2})/))) { out.apgar1 = m[1]; out.apgar5 = m[2]; }
    if ((m = t.match(/G\s*(\d{1,2})\s*P\s*(\d{1,2})/))) { out.g = m[1]; out.p = m[2]; }
    if ((m = t.match(/\(\s*(\d)\s*-?\s*(\d)\s*-?\s*(\d)\s*-?\s*(\d)\s*\)/))) {
      out.t = m[1]; out.pre = m[2]; out.a = m[3]; out.l = m[4];
    }
    return out;
  }

  function sentence() {
    const days = val('days');
    const age = val('weeks') + (days && days !== '0' ? ` ${days}/7` : '');
    // In capitals, like everything typed into the forms.
    return (`PUFT ${age} wks AOG delivered via NSVD to a live term baby ${val('sex')} ${val('size')} ` +
      `w/ AS of ${val('apgar1')} & ${val('apgar5')}; G${val('g')}P${val('p')} ` +
      `(${val('t')}${val('pre')}${val('a')}${val('l')})`).toUpperCase();
  }

  function missing() {
    return PARTS.filter(name => name !== 'days' && !val(name));
  }

  function refresh() {
    box.querySelectorAll('input[data-dx]').forEach(input => {
      input.value = input.value.replace(/\D/g, '');
      input.classList.toggle('dx-empty', input.dataset.dx !== 'days' && !input.value);
    });
    f('sex').classList.toggle('dx-empty', !f('sex').value);
    box.querySelector('.dx-preview').textContent = sentence();
    const left = missing().length;
    box.querySelector('[data-dx-use]').disabled = left > 0;
    box.querySelector('[data-dx-note]').textContent =
      left ? `Fill in the ${left} red blank${left === 1 ? '' : 's'} first.` : '';
  }

  open.addEventListener('click', () => {
    prefill();
    box.querySelector('.dx-confirm').hidden = true;
    box.hidden = false;
    refresh();
    const first = box.querySelector('input.dx-empty');
    (first || f('weeks')).focus();
  });
  box.addEventListener('input', refresh);
  box.addEventListener('change', refresh);
  box.querySelector('[data-dx-close]').addEventListener('click', () => { box.hidden = true; });

  const ask = box.querySelector('.dx-confirm');
  box.querySelector('[data-dx-use]').addEventListener('click', () => {
    const current = String(state.data.admissionDx || '').trim();
    if (current && current !== sentence()) {
      box.querySelector('[data-dx-old]').textContent = current;
      ask.hidden = false;
      box.querySelector('[data-dx-replace]').focus();
      return;
    }
    putIn();
  });
  box.querySelector('[data-dx-replace]').addEventListener('click', putIn);
  box.querySelector('[data-dx-keep]').addEventListener('click', () => {
    ask.hidden = true;
    box.querySelector('[data-dx-use]').focus();
  });

  function putIn() {
    ask.hidden = true;
    const values = { admissionDx: sentence() };
    // Blanks filled here also fill their own fields, if those are empty.
    const fillIfEmpty = (key, value) => { if (value && !String(state.data[key] || '').trim()) values[key] = value; };
    fillIfEmpty('gravida', val('g')); fillIfEmpty('para', val('p'));
    fillIfEmpty('obTerm', val('t')); fillIfEmpty('obPreterm', val('pre'));
    fillIfEmpty('obAbortion', val('a')); fillIfEmpty('obLiving', val('l'));
    fillIfEmpty('apgarScore', val('apgar5'));
    fillIfEmpty('babySex', { boy: 'Male', girl: 'Female' }[val('sex')]);
    applyFormData(values);
    box.hidden = true;
    showToast('Delivery message put in',
      'Admission Diagnosis now has the delivery message. CSF 4 prints it as the admitting diagnosis.', 'success');
  }
})();

/* ═══════════════════════════════════════════════════════════
   Long entry tables — show one line at a time

   The course in the ward (15 dated lines) and the drugs list (7 printed
   lines) were too much to look at, so only the first line is shown.
   "Add" reveals the next, the minus button puts it away again. A line
   that has been filled in is never hidden, so nothing typed can vanish.

   A printed line can be more than one row on screen: on the CF4 the
   drugs table has a left and a right half that share the same line on
   paper, and both are revealed together via data-drug-row.
═══════════════════════════════════════════════════════════ */
function setupExpandingRows(opts) {
  const wrap = document.getElementById(opts.wrapId);
  const addBtn = document.getElementById(opts.addId);
  const delBtn = document.getElementById(opts.removeId);
  const count = document.getElementById(opts.countId);
  if (!wrap || !addBtn || !delBtn) return null;

  const all = Array.from(wrap.querySelectorAll('.' + opts.rowClass));
  if (!all.length) return null;

  // Group the rows by the printed line they belong to, keeping order.
  const groups = [];
  const seen = new Map();
  all.forEach(row => {
    const id = row.dataset[opts.dataKey] || String(groups.length + 1);
    if (!seen.has(id)) { seen.set(id, []); groups.push(seen.get(id)); }
    seen.get(id).push(row);
  });

  const TOTAL = groups.length + 1;          // + the always-visible first line
  const filled = group => group.some(row =>
    Array.from(row.querySelectorAll('[data-autofill]'))
         .some(el => (el.value || '').trim() !== ''));

  let shown = 0;
  const lastFilled = () => {
    let n = 0;
    groups.forEach((g, i) => { if (filled(g)) n = i + 1; });
    return n;
  };

  function render() {
    shown = Math.max(shown, lastFilled());
    groups.forEach((g, i) => g.forEach(row => { row.hidden = i >= shown; }));
    wrap.hidden = shown === 0;
    addBtn.hidden = shown >= groups.length;
    addBtn.setAttribute('aria-expanded', shown > 0 ? 'true' : 'false');
    // Only offer to hide a line that is still empty.
    delBtn.hidden = shown === 0 || shown <= lastFilled();
    refreshRedMarksSoon();   // a line just shown is marked if empty
    if (count) {
      count.textContent = shown + 1 === TOTAL
        ? 'All ' + TOTAL + ' ' + opts.noun + ' shown'
        : (opts.label || 'Line') + ' ' + (shown + 1) + ' of ' + TOTAL;
    }
  }

  addBtn.addEventListener('click', () => {
    if (shown < groups.length) shown++;
    render();
    const group = groups[shown - 1];
    const first = group && group[0] && group[0].querySelector('[data-autofill]');
    if (first) first.focus();
  });

  delBtn.addEventListener('click', () => {
    if (shown > lastFilled()) shown--;
    render();
  });

  // Loading a saved claim or the sample data fills these boxes directly,
  // so re-check after anything writes to them.
  wrap.addEventListener('input', render);
  render();
  return { refresh: render };
}

(function setupLongTables() {
  const course = setupExpandingRows({
    wrapId: 'cf4CourseExtraRows', addId: 'cf4CourseAddRow',
    removeId: 'cf4CourseRemoveRow', countId: 'cf4CourseRowCount',
    rowClass: 'course-row', dataKey: 'courseRow',
    label: 'Line', noun: 'lines',
  });
  const drugs = setupExpandingRows({
    wrapId: 'cf4DrugExtraRows', addId: 'cf4DrugAddRow',
    removeId: 'cf4DrugRemoveRow', countId: 'cf4DrugRowCount',
    rowClass: 'drug-row', dataKey: 'drugRow',
    label: 'Medicine', noun: 'medicines',
  });
  window.PCACourseRows = {
    refresh() {
      if (course) course.refresh();
      if (drugs) drugs.refresh();
    },
  };
})();
