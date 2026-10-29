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
    noContact:false,       /* "No contact info": phone and email left blank */
    /* Address */
    addrUnit:'', addrBuilding:'', addrLot:'', addrStreet:'',
    addrSubdivision:'', addrBarangay:'', addrCity:'', addrProvince:'', addrZip:'',
    /* Contact */
    mobile:'', homePhone:'', email:'',
    /* Confinement */
    dateAdmitted:'', timeAdmitted:'', amPmAdmitted:'AM',
    dateDischarge:'', timeDischarge:'', amPmDischarge:'AM',
    disposition:'', accommodation:'', chiefComplaint:'', admissionDx:'', dischargeDx:'',
    /* CF2 – special procedures, TB-DOTS and newborn care packages */
    cf2SpecialProcedures:[], cf2SpecialProcedureDetail:'',
    cf2ProcDates1:'', cf2ProcDates2:'', cf2ProcDates3:'', cf2ProcDates4:'',
    cf2ProcDates5:'', cf2ProcDates6:'', cf2ProcDates7:'', cf2ProcDates8:'',
    cf2TbPhase:'', cf2NewbornCare:[], cf2EssentialNewbornCare:[],
    /* CF4 – Clinical Record (encoded manually; the logbook does not record these) */
    patientAge:'',
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
    cf4Height:'', cf4Weight:'',
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
    cf4CourseDate1:'', cf4CourseOrder1:'', cf4CourseDate2:'', cf4CourseOrder2:'',
    /* CF4 drug rows */
    cf4DrugName1:'', cf4DrugQty1:'', cf4DrugDose1:'', cf4DrugCost1:'', cf4DrugName2:'', cf4DrugQty2:'', cf4DrugDose2:'', cf4DrugCost2:'',
    cf4DrugName3:'', cf4DrugQty3:'', cf4DrugDose3:'', cf4DrugCost3:'',
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
    motherLastName:'', motherFirstName:'', motherMiddleName:'', motherNameExt:'',
    spouseLastName:'', spouseFirstName:'', spouseMiddleName:'', spouseNameExt:'',
    memberType:'', profession:'', monthlyIncome:'',
    /* Maternity / Delivery */
    lmp:'', ageOfMenarche:'', gravida:'', para:'',
    expectedDD:'', deliveryDate:'', deliveryTime:'', amPmDelivery:'AM',
    mannerOfDelivery:'', fetalOutcome:'', babySex:'', birthWeight:'', apgarScore1:'', apgarScore:'',
    briefHistory:'',
    /* The clinic's diagnosis wording (js/dx-templates.js): the package
       picked by staff ('' = picked automatically), and whether the usual
       delivery medicines were put in the CF4 drugs list */
    dxPackage:'', dxDrugsAdded:false,
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
  patientNameExt:"N/A", patientDOB:'1995-03-15', patientSex:'Female',
  patientPIN:'12-345678901-3',
  memberLastName:'DELA CRUZ', memberFirstName:'PEDRO', memberMiddleName:'REYES',
  memberNameExt:"N/A", memberDOB:'1992-07-22', memberSex:'Male',
  memberPIN:'12-345678901-2', relationship:'Spouse',
  addrUnit:"Unit 2", addrLot:'123', addrStreet:'Rizal Street',
  addrSubdivision:'Bgy. Uno Subdivision', addrBarangay:'Barangay Uno',
  addrCity:'Quezon City', addrProvince:'Metro Manila', addrZip:'1100',
  mobile:'0917-123-4567', homePhone:'02-8123-4567', email:'pedro.delacruz@email.com',
  dateAdmitted:'2026-06-10', timeAdmitted:'08:30', amPmAdmitted:'AM',
  dateDischarge:'2026-06-13', timeDischarge:'10:00', amPmDischarge:'AM',
  disposition:'Improved', accommodation:'Non-Private',
  chiefComplaint:'Labor pains, full-term pregnancy',
  // In labor on admission, delivered at discharge (js/dx-templates.js NSDBF).
  admissionDx:'PREGNANCY UTERINE FULL TERM 40 WEEKS AOG, CEPHALIC IN LABOR GRAVIDA 2 PARA 1 (1001).',
  dischargeDx:'PREGNANCY UTERINE FULL TERM 40 WEEKS AOG GRAVIDA 2 PARA 2 (2002), DELIVERED VIA NORMAL SPONTANEOUS VAGINAL DELIVERY ' +
    'ON JUNE 10, 2026, 09:45 AM TO A LIVE TERM BABY GIRL IN CEPHALIC PRESENTATION WEIGHING 3200 GMS. WITH AN APGAR ' +
    'SCORE OF 8 AND 9 AND WITH AGA.',
  patientAge:'31',
  cf4ChiefComplaint:'Labor pains, full-term pregnancy',
  cf4HistoryPresentIllness:'G1 - 2018 - HOSPITAL\nG2 - PRESENT PREGNANCY',
  cf4PhysicalExam:'BP 120/80, HR 88, RR 18, T 36.8C. Abdomen gravid, fundic height 34 cm, '
    + 'FHT 142 bpm. Internal exam: 6 cm dilated, 80% effaced, station -1, intact membranes.',
  cf4CourseInWard:'Admitted and monitored with partograph. Progressed to full dilatation after '
    + '5 hours. Delivered a live term baby girl via normal spontaneous vaginal delivery. '
    + 'Placenta delivered complete. Perineum intact. Stable post-partum, '
    + 'ambulatory and tolerating diet. Discharged improved on the third hospital day.',
  cf4DrugsAdministered:'Oxytocin 10 units IM post-delivery; Mefenamic acid 500 mg PO q6h PRN; '
    + 'Ferrous sulfate + folic acid 1 tab PO OD',
  cf4FinalDiagnosis:'PREGNANCY UTERINE FULL TERM 40 WEEKS AOG GRAVIDA 2 PARA 2 (2002), DELIVERED VIA NORMAL SPONTANEOUS VAGINAL DELIVERY ' +
    'ON JUNE 10, 2026, 09:45 AM TO A LIVE TERM BABY GIRL IN CEPHALIC PRESENTATION WEIGHING 3200 GMS. WITH AN APGAR ' +
    'SCORE OF 8 AND 9 AND WITH AGA.',
  cf4LaboratoryFindings:'CBC: Hgb 118 g/L, WBC 9.2; Urinalysis: normal; HBsAg non-reactive',
  cf4IcdCode:'O80', cf4RvsCode:'59400',
  cf4AttendingProvider:'ROSARIO M. ALCANTARA, RM',
  cf4ProviderPAN:'110000005678', cf4ProviderSignedDate:'2026-06-13',
  dxADiagnosis:'SPONTANEOUS VERTEX DELIVERY',
  dxAIcd10:'O80',
  hciPAN:'120000012345', hciName:'Mapagpala Maternity Clinic',
  
  cf2NewbornCare:['Essential Newborn Care','Newborn Screening Test'],
  cf2EssentialNewbornCare:['Immediate drying of newborn','Early skin-to-skin contact','Timely cord clamping',
    'Eye Prophylaxis','Vitamin K administration','Weighing of the newborn'],
  hciStreet:'456 Bonifacio Avenue', hciCity:'Quezon City', hciProvince:'Metro Manila',
  employerPEN:"123456789012", 
  civilStatus:'Married', placeOfBirth:'Quezon City, Metro Manila', citizenship:'FILIPINO',
  motherLastName:'SANTOS', motherFirstName:'LILIA', motherMiddleName:'GARCIA',
  spouseLastName:'DELA CRUZ', spouseFirstName:'PEDRO', spouseMiddleName:'REYES',
  memberType:'Employed Private', profession:'Teacher', monthlyIncome:'25,000',
  lmp:'2025-09-03', ageOfMenarche:'13', gravida:'2', para:'1',
  expectedDD:'2026-06-10',
  deliveryDate:'2026-06-10', deliveryTime:'09:45', amPmDelivery:'AM',
  mannerOfDelivery:'Normal Spontaneous Delivery (NSD)',
  fetalOutcome:'Live Birth', babySex:'Female', birthWeight:'3200', apgarScore1:'8', apgarScore:'9',
  briefHistory:'G1 - 2018 - HOSPITAL\nG2 - PRESENT PREGNANCY',
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
  dep2LastName:"DELA CRUZ", 
  dep2Relationship:"Child", 
  dep2NoMiddleName:false, dep2Mononym:false, dep2Disability:false,
  dep3LastName:"DELA CRUZ", 
  dep3Relationship:"Child", 
  dep3NoMiddleName:false, dep3Mononym:false, dep3Disability:false,
  dep4LastName:"SANTOS", 
  dep4Relationship:"Parent", 
  dep4NoMiddleName:false, dep4Mononym:false, dep4Disability:false,
  /* PMRF – Mailing Address */
  mailingSameAsAbove:true, 
  mailingAddrUnit:"Unit 2", 
  mailingAddrSubdivision:"Deca Homes", 
  mailingAddrProvince:"Davao del Sur", 
  /* PMRF – Member Type extras */
  pwdIdNo:"N/A", 
  /* PMRF Page 2 – V. Updating/Amendment (left unchecked by default) */
  amendName:false, 
  amendDOB:false, 
  amendSex:false, 
  amendCivilStatus:false, 
  amendPersonalInfo:false, 
  /* PMRF Page 2 – Member's Signature */
  memberSignatureName:'Pedro R. Dela Cruz', memberSignatureDate:'2026-06-01',


  /* Every remaining box, so "Fill with practice data" leaves nothing
     empty and a test export exercises all four forms end to end.
     Fictional, but shaped like this clinic's real work: one NSD, a
     live term baby girl, and the usual post-partum orders. */
  memberIsPatient: false,
  cf2ProcDates1: "2026-06-13",
  cf2ProcDates2: "2026-06-13",
  cf2ProcDates3: "2026-06-13",
  cf2ProcDates4: "2026-06-13",
  cf2ProcDates5: "2026-06-13",
  cf2ProcDates6: "2026-06-13",
  cf2ProcDates7: "2026-06-13",
  cf2ProcDates8: "2026-06-13",
  hciBldg: "Ground Floor",
  hciZip: "8000",
  cf4PastMedicalHistory: "No known medical illness",
  cf4TimeAdmittedDigits: "",
  cf4TimeDischargeDigits: "",
  cf4LmpNA: false,
  cf4PainSite: "Lower abdomen, radiating to lower back",
  cf4SymptomOther: "Bloody show noted since 4:00 AM",
  cf4ReferralReason: "Not referred - direct admission",
  cf4ReferralHci: "N/A - direct admission",
  cf4AlteredSensorium: "N/A - awake and alert",
  cf4VitalBP: "120/80",
  cf4VitalHR: "86",
  cf4VitalRR: "18",
  cf4VitalTemp: "36.8",
  cf4Height: "158",
  cf4Weight: "62",
  cf4Heent: ["Essentially normal"],
  cf4HeentOthers: "Pink palpebral conjunctivae",
  cf4ChestOthers: "Clear breath sounds",
  cf4Cvs: ["Essentially normal"],
  cf4CvsOthers: "Regular rate and rhythm",
  cf4Abdomen: ["Essentially normal"],
  cf4AbdomenOthers: "Gravid, fundic height 32 cm",
  cf4Gu: ["Essentially normal"],
  cf4GuOthers: "Cervix 5 cm dilated on admission",
  cf4Skin: ["Essentially normal"],
  cf4SkinOthers: "Warm, good turgor",
  cf4Neuro: ["Essentially normal"],
  cf4NeuroOthers: "Oriented to time, place and person",
  cf4SurgicalProcedure: "Normal spontaneous delivery, RVS 59400",
  cf4CourseOrder1: "Admitted, 5 cm dilated. FHT 142 bpm. Partograph started.",
  cf4CourseDate2: "2026-06-13",
  cf4CourseOrder2: "Progressed to 8 cm. Ambulation and breathing encouraged.",
  cf4CourseDate3: "2026-06-13",
  cf4CourseOrder3: "Fully dilated. Transferred to delivery room.",
  cf4CourseDate4: "2026-06-13",
  cf4CourseOrder4: "NSD to a live term baby girl, APGAR 9/9. Placenta complete.",
  cf4CourseDate5: "2026-06-13",
  cf4CourseOrder5: "Post-partum monitoring. Uterus firm, lochia moderate.",
  cf4CourseDate6: "2026-06-14",
  cf4CourseOrder6: "Ambulatory, tolerating diet. Breastfeeding established.",
  cf4CourseDate7: "2026-06-14",
  cf4CourseOrder7: "Discharged well with take-home medicines and advice.",
  cf4CourseDate8: "2026-06-14",
  cf4CourseOrder8: "Vital signs stable. Fundus firm at umbilicus.",
  cf4CourseDate9: "2026-06-14",
  cf4CourseOrder9: "Baby latched well. Newborn screening explained.",
  cf4CourseDate10: "2026-06-14",
  cf4CourseOrder10: "Perineal care taught. No signs of infection.",
  cf4CourseDate11: "2026-06-14",
  cf4CourseOrder11: "Iron and vitamins dispensed with instructions.",
  cf4CourseDate12: "2026-06-14",
  cf4CourseOrder12: "Newborn screening sample taken.",
  cf4CourseDate13: "2026-06-15",
  cf4CourseOrder13: "Hearing screening done, passed both ears.",
  cf4CourseDate14: "2026-06-15",
  cf4CourseOrder14: "Follow-up booked for 1 week post-partum.",
  cf4CourseDate15: "2026-06-15",
  cf4CourseOrder15: "Home care and danger signs explained to the family.",
  cf4DrugQty1: "1.00 PC/S",
  cf4DrugDose1: "10 units IM",
  cf4DrugCost1: "350.00",
  cf4DrugName1b: "Ascorbic acid",
  cf4DrugDose1b: "500 mg PO OD",
  cf4DrugCost1b: "95.00",
  cf4DrugName2: "Mefenamic acid",
  cf4DrugQty2: "10.00 PC/S",
  cf4DrugDose2: "500 mg PO q6h PRN",
  cf4DrugCost2: "180.00",
  cf4DrugName2b: "Calcium carbonate",
  cf4DrugDose2b: "500 mg PO BID",
  cf4DrugCost2b: "110.00",
  cf4DrugName3: "Ferrous sulfate",
  cf4DrugQty3: "30.00 PC/S",
  cf4DrugDose3: "325 mg PO OD",
  cf4DrugCost3: "120.00",
  cf4DrugName3b: "Lactulose",
  cf4DrugDose3b: "30 mL PO HS PRN",
  cf4DrugCost3b: "230.00",
  cf4DrugName4: "Paracetamol",
  cf4DrugDose4: "500 mg PO q6h PRN",
  cf4DrugCost4: "90.00",
  cf4DrugName4b: "Tranexamic acid",
  cf4DrugDose4b: "500 mg IV q8h",
  cf4DrugCost4b: "310.00",
  cf4DrugName5: "Cefalexin",
  cf4DrugDose5: "500 mg PO q6h",
  cf4DrugCost5: "420.00",
  cf4DrugName5b: "Metronidazole",
  cf4DrugDose5b: "500 mg PO TID",
  cf4DrugCost5b: "175.00",
  cf4DrugName6: "Vitamin K",
  cf4DrugDose6: "1 mg IM (newborn)",
  cf4DrugCost6: "150.00",
  cf4DrugName6b: "BCG vaccine",
  cf4DrugDose6b: "0.05 mL ID (newborn)",
  cf4DrugCost6b: "260.00",
  cf4DrugName7: "Hepatitis B vaccine",
  cf4DrugDose7: "0.5 mL IM (newborn)",
  cf4DrugCost7: "280.00",
  cf4DrugName7b: "Erythromycin eye ointment",
  cf4DrugDose7b: "0.5% OU (newborn)",
  cf4DrugCost7b: "140.00",
  referralHciName: "Davao Regional Medical Center",
  referralStreet: "Apokon Road",
  referralCity: "Tagum City",
  referralProvince: "Davao del Norte",
  referralZip: "8100",
  dxAProcI: "Normal spontaneous delivery",
  dxARvsI: "59400",
  dxADateI: "2026-06-13",
  dxALatI: "both",
  dxAProcII: "Episiotomy",
  dxARvsII: "59300",
  dxADateII: "2026-06-13",
  dxALatII: "left",
  dxAProcIII: "Perineal repair",
  dxARvsIII: "59300",
  dxADateIII: "2026-06-13",
  dxALatIII: "both",
  dxBDiagnosis: "Anemia in pregnancy, mild",
  dxBIcd10: "O99.0",
  dxBProcI: "Complete blood count",
  dxBRvsI: "85025",
  dxBDateI: "2026-06-13",
  dxBLatI: "both",
  dxBProcII: "Iron supplementation",
  dxBRvsII: "99070",
  dxBDateII: "2026-06-13",
  dxBLatII: "both",
  dxBProcIII: "Dietary counselling",
  dxBRvsIII: "99402",
  dxBDateIII: "2026-06-14",
  dxBLatIII: "both",
  repSignedDate: "2026-06-14",
  memberSignerType: "Member",
  repRelationship: "Spouse",
  repRelationshipOther: "",
  repReason: "Incapacitated",
  repReasonOther: "Resting after delivery",
  employerRepName: "MA. CORAZON B. VILLAREAL",
  employerCapacity: "HR Officer",
  patientRepSignedDate: "2026-06-14",
  patientSignerType: "Patient",
  patientRepRelationship: "Parent",
  patientRepRelationshipOther: "",
  patientReason: "Incapacitated",
  patientReasonOther: "Newborn",
  hciProf1Name: "DR. LIEZL M. ANDRADA",
  hciProf1DateSigned: "2026-06-14",
  hciProf2AccredNo: "110000006789",
  hciProf2Name: "DR. RAMON T. DELA PENA",
  hciProf2DateSigned: "2026-06-14",
  hciProf3AccredNo: "110000007890",
  hciProf3Name: "MIDWIFE ROSA L. GUEVARRA",
  hciProf3DateSigned: "2026-06-14",
  csfSecondCaseRate: "2,400.00",
  providerRepName: "ANGELO D. MENDOZA",
  providerCapacity: "Clinic Administrator",
  providerSignedDate: "2026-06-14",
  cf2Prof1Name: "DR. LIEZL M. ANDRADA",
  cf2Prof1DateSigned: "2026-06-14",
  cf2Prof1Copay: "No",
  cf2Prof1CopayAmount: "",
  cf2Prof2AccredNo: "110000006789",
  cf2Prof2Name: "DR. RAMON T. DELA PENA",
  cf2Prof2DateSigned: "2026-06-14",
  cf2Prof2Copay: "No",
  cf2Prof2CopayAmount: "",
  cf2Prof3AccredNo: "110000007890",
  cf2Prof3Name: "MIDWIFE ROSA L. GUEVARRA",
  cf2Prof3DateSigned: "2026-06-14",
  cf2Prof3Copay: "No",
  cf2Prof3CopayAmount: "",
  cf2PatientRepSignedDate: "2026-06-14",
  cf2PatientRepRelationship: "Parent",
  cf2PatientRepRelationshipOther: "",
  cf2PatientReason: "Incapacitated",
  cf2PatientReasonOther: "Newborn",
  cf2ProviderCapacity: "Clinic Administrator",
  cf2ProviderSignedDate: "2026-06-14",
  dxDrugsAdded: true,

  /* Remaining boxes, so nothing on any form prints empty. */
  employerPhone: "082-224-5566",
  employerName: "Cabantian Trading Corporation",
  memberSignedDate: "2026-06-14",
  employerSignedDate: "2026-06-14",
  patientRepName: "MARIA S. DELA CRUZ",
  hciProf1AccredNo: "110000005678",
  csfFirstCaseRate: "8,000.00",
  cf2Prof1AccredNo: "110000005678",
  cf2PatientRepName: "MARIA S. DELA CRUZ",
  cf2ProviderRepName: "ANGELO D. MENDOZA",
  cf4CourseDate1: "2026-06-13",
  cf4DrugName1: "Oxytocin",
  cf4TransferReason: "N/A - not transferred",
  addrBuilding: "Mahogany Apartments",
  businessPhone: "082-224-5566",
  mailingAddrBuilding: "Mahogany Apartments",
  mailingAddrLot: "Lot 14",
  mailingAddrStreet: "Narra Street",
  mailingAddrBarangay: "Cabantian",
  mailingAddrCity: "Davao City",
  mailingAddrZip: "8000",
  dep2FirstName: "JOSE",
  dep2Ext: "N/A",
  dep2MiddleName: "SANTOS",
  dep2DOB: "2022-03-11",
  dep2Citizenship: "FILIPINO",
  dep3FirstName: "ANA",
  dep3Ext: "N/A",
  dep3MiddleName: "SANTOS",
  dep3DOB: "2024-08-02",
  dep3Citizenship: "FILIPINO",
  dep4FirstName: "ROSARIO",
  dep4Ext: "N/A",
  dep4MiddleName: "LIM",
  dep4DOB: "1962-11-20",
  dep4Citizenship: "FILIPINO",
  praSrrvNo: "N/A",
  acrICardNo: "N/A",
  groupEnrollmentNo: "N/A",
  amendNameFrom: "MARIA S. DELA CRUZ",
  amendNameTo: "MARIA SANTOS DELA CRUZ",
  amendDOBFrom: "1996-04-18",
  amendDOBTo: "1996-04-18",
  amendSexFrom: "Female",
  amendSexTo: "Female",
  amendCivilStatusFrom: "Single",
  amendCivilStatusTo: "Married",
  amendPersonalInfoFrom: "Narra Street, Cabantian",
  amendPersonalInfoTo: "Lot 14 Narra Street, Deca Homes, Cabantian",

  cf2SpecialProcedures: "No",
  cf2SpecialProcedureDetail: "N/A",
  cf2TbPhase: "",   // TB treatment does not apply to a maternity claim
  cf4Symptoms: ["Abdominal pain"],
  cf4Referred: "No",
  referredByHCI: "No",
  cf4GeneralSurvey: "Awake and alert",
  cf4Chest: ["Essentially normal"],
  dxPackage: "Maternity Care Package (MCP)",
  proofOfIncome: "Point of Service (POS)",
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
  'cf4CourseDate1','cf4CourseDate2',
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

/* CF2 8.a: each repetitive procedure has its own dates line beside it,
   typed in its own box (cf2ProcDates1-8) once it is ticked. Dates typed
   before that, in the one "Procedure details" box older claims have, go
   on the line of the first procedure ticked. */
const CF2_REPEAT_PROCEDURES = ['Hemodialysis', 'Blood Transfusion', 'Peritoneal Dialysis',
  'Brachytherapy', 'Radiotherapy (LINAC)', 'Chemotherapy', 'Radiotherapy (COBALT)', 'Simple Debridement'];

function getComputedValue(key) {
  const d = state.data;
  if (DATE_FIELDS.has(key)) return d[key] ? formatDate(d[key]) : '';
  const procLine = /^cf2ProcDetail([1-8])$/.exec(key);
  if (procLine) {
    const ticked = Array.isArray(d.cf2SpecialProcedures) ? d.cf2SpecialProcedures : [];
    const proc = CF2_REPEAT_PROCEDURES[procLine[1] - 1];
    if (!ticked.includes(proc)) return '';
    const first = CF2_REPEAT_PROCEDURES.find(p => ticked.includes(p));
    return d['cf2ProcDates' + procLine[1]] || (proc === first ? (d.cf2SpecialProcedureDetail || '') : '');
  }
  switch (key) {
    // The pregnancy lines put in by themselves ("G1 - ") are not filled in
    // until each one is finished, so the checker still asks for them.
    case 'cf4HistoryPresentIllness':
      return historyUnfinished(d[key]) ? '' : (d[key] || '');
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
    /* CSF Part I, Item 9: a name only over the line of whoever signs - the
       member's until a representative is chosen, the representative's
       (the patient, who usually signs for the member) only then. */
    case 'memberLineName':
      return d.memberSignerType === 'Representative' ? '' : getComputedValue('memberSignName');
    case 'repLineName':
      return d.memberSignerType === 'Representative' ? getComputedValue('patientSignName') : '';

    // Shown with a peso sign on the form, as it is on the printed PMRF.
    case 'monthlyIncomeDisplay': {
      const amount = (d.monthlyIncome || '').trim();
      return amount ? '₱' + amount.replace(/^₱\s*/, '') : '';
    }
    // The course in the ward is the form's two boxes (date + order). It
    // counts as filled when either box has an order written in it.
    case 'cf4CourseInWard': {
      for (let i = 1; i <= 2; i++) {
        const order = (d['cf4CourseOrder' + i] || '').trim();
        if (order) return order;
      }
      return '';
    }
    // Drugs are typed as a table, not one box. Counted as filled when any
    // of the form's three rows names a medicine.
    case 'cf4DrugsAdministered': {
      for (let i = 1; i <= 3; i++) {
        const name = (d['cf4DrugName' + i] || '').trim();
        if (name) return name;
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
      return [[d.hciBldg, d.hciStreet].filter(Boolean).join(' '),
              d.hciCity, d.hciProvince, d.hciZip].filter(Boolean).join(', ');
    // CF1 4. Mailing Address: the PMRF mailing address, or - when none was
    // given there - the home address from Patient details, part by part.
    case 'cf1MailingAddrUnit': case 'cf1MailingAddrBuilding': case 'cf1MailingAddrLot':
    case 'cf1MailingAddrStreet': case 'cf1MailingAddrSubdivision': case 'cf1MailingAddrBarangay':
    case 'cf1MailingAddrCity': case 'cf1MailingAddrProvince': case 'cf1MailingAddrZip': {
      const part = key.slice('cf1MailingAddr'.length);
      return (mailingGiven(d) ? d['mailingAddr' + part] : d['addr' + part]) || '';
    }
    case 'mailingAddress':
      return MAILING_PARTS.map(part => getComputedValue('cf1MailingAddr' + part)).filter(Boolean).join(', ');
    // The clinic's patients live in the Philippines.
    case 'mailingCountry':
      return getComputedValue('mailingAddress') ? 'PHILIPPINES' : '';
    // CF1 7. "Patient is the member?": Yes when ticked; No once a member
    // other than the patient is known.
    case 'cf1PatientIsMember':
      if (d.memberIsPatient) return 'Yes';
      return (d.memberLastName || d.memberFirstName || d.memberPIN) ? 'No' : '';
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
    // CF4 9.b / 10.b: hh and mm in four boxes, AM/PM ticked beside them.
    case 'cf4TimeAdmittedDigits':
      return time12hDigits(d.timeAdmitted);
    case 'cf4TimeDischargeDigits':
      return time12hDigits(d.timeDischarge);
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

const MAILING_PARTS = ['Unit', 'Building', 'Lot', 'Street', 'Subdivision', 'Barangay', 'City', 'Province', 'Zip'];
function mailingGiven(d) {
  return MAILING_PARTS.some(part => String(d['mailingAddr' + part] || '').trim());
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
const VALID_SECTIONS = ['dashboard','patient','csf','cf1','cf2','cf4','pmrf','validation','profile','settings'];

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
   empties them (see the change listener below). */
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

/* Unticking "The patient is the PhilHealth member" (Patient details or
   the CSF) empties what the tick copied in, so the member's boxes are
   blank for the real member rather than still showing the patient. Only
   a click does this: loading a saved claim never clears its member. */
document.addEventListener('change', e => {
  const box = e.target;
  if (!box.matches || !box.matches('input[type="checkbox"][data-autofill="memberIsPatient"]')) return;
  if (box.checked) return;
  state.data.memberIsPatient = false;
  MEMBER_LOCKED_KEYS.forEach(key => {
    state.data[key] = typeof state.data[key] === 'boolean' ? false : '';
  });
  updateFormPreviews();
});

/* PMRF "Same as Permanent Address": the mailing address copies the
   permanent one (zip code included) and is locked while ticked, the same
   way the member follows the patient above. Unticking keeps what is there. */
const MAILING_FROM_PERMANENT = {
  mailingAddrUnit: 'addrUnit', mailingAddrBuilding: 'addrBuilding',
  mailingAddrLot: 'addrLot', mailingAddrStreet: 'addrStreet',
  mailingAddrSubdivision: 'addrSubdivision', mailingAddrBarangay: 'addrBarangay',
  mailingAddrCity: 'addrCity', mailingAddrProvince: 'addrProvince',
  mailingAddrZip: 'addrZip',
};

function applyMailingSameAsAbove() {
  const same = !!state.data.mailingSameAsAbove;
  Object.entries(MAILING_FROM_PERMANENT).forEach(([mailing, permanent]) => {
    if (same) state.data[mailing] = state.data[permanent] || '';
    document.querySelectorAll(`[data-autofill="${mailing}"]`).forEach(el => {
      el.disabled = same;
      el.title = same ? 'Same as the permanent address' : '';
    });
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

/* Values worked out from others: the patient's age (CF4) from the birthday,
   as of admission (today until there is an admission date), and the
   expected date of delivery from the LMP by Naegele's rule (LMP + 280
   days). Each is filled while its box is empty or still holds what was
   last worked out, so a value typed over it by hand is kept. */
const derivedLast = {};

function ageOn(dobIso, onIso) {
  const b = String(dobIso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const o = String(onIso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!b || !o) return '';
  let age = Number(o[1]) - Number(b[1]);
  if (Number(o[2]) < Number(b[2]) || (o[2] === b[2] && Number(o[3]) < Number(b[3]))) age--;
  return age >= 0 && age <= 130 ? String(age) : '';
}

function addDaysIso(iso, days) {
  const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return '';
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]) + days);
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'),
          String(d.getDate()).padStart(2, '0')].join('-');
}

function todayIso() {
  // The clinic's own date, not UTC's (which is still yesterday before 8 AM).
  const d = new Date();
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'),
          String(d.getDate()).padStart(2, '0')].join('-');
}

/* The APGAR scores written in a diagnosis, [1 minute, 5 minutes]: the
   delivery message's "W/ AS OF 8 & 9" (typed in the Logbook Reader, or
   read from the logbook) or the wording's "APGAR SCORE OF 8 & 9". */
function apgarFromDx(d) {
  for (const text of [d.admissionDx, d.dischargeDx]) {
    const m = String(text || '').match(/\b(?:AS|APGAR(?:\s+SCORES?)?)\s+(?:OF\s+)?(\d{1,2})\s*(?:&|AND|\/|,)\s*(\d{1,2})\b/i);
    if (m && Number(m[1]) <= 10 && Number(m[2]) <= 10) return [m[1], m[2]];
  }
  return ['', ''];
}

/* The mother's G, P and T-P-A-L written in a diagnosis, before this
   delivery (as the forms keep them): the reason for admission's "GRAVIDA 3
   PARA 2 (2002)" or "G3P2 (2002)" as it is; a final diagnosis that says
   the baby was delivered counts it, so one para, term and living child
   less. A baby's own wording ("TO A GRAVIDA 3 PARA 3 MOTHER") is its
   mother's, not the patient's, and is left alone. */
const OB_IN_DX = /\bG(?:RAVIDA)?\s*(\d{1,2})\s*,?\s*P(?:ARA)?\s*(\d{1,2})(?!\d)(?!\s*MOTHER)\s*(?:\(\s*(\d)\s*-?\s*(\d)\s*-?\s*(\d)\s*-?\s*(\d)\s*\))?/i;
function obFromDx(d) {
  const none = { gravida: '', para: '', obTerm: '', obPreterm: '', obAbortion: '', obLiving: '' };
  for (const [text, delivered] of [[d.admissionDx, false], [d.dischargeDx, /\bDELIVER(ED|Y)\b/i.test(d.dischargeDx || '')]]) {
    const m = String(text || '').match(OB_IN_DX);
    if (!m) continue;
    const less = (v, by) => (v === undefined ? '' : String(Math.max(0, Number(v) - by)));
    const one = delivered ? 1 : 0;
    return { gravida: m[1], para: less(m[2], one), obTerm: less(m[3], one), obPreterm: m[4] ?? '',
             obAbortion: m[5] ?? '', obLiving: less(m[6], one) };
  }
  return none;
}

/* The baby's sex and birth weight written in a diagnosis: "... TO A LIVE
   TERM BABY BOY ... WEIGHING 2600 GMS." */
function babyFromDx(d) {
  const text = `${d.dischargeDx || ''} ${d.admissionDx || ''}`;
  const sex = text.match(/\bBABY\s+(BOY|GIRL)\b/i);
  const weight = text.match(/\bWEIGHING\s*([\d,]{3,5})\s*(?:GMS?|GRAMS?)\b/i);
  return {
    babySex: sex ? (sex[1].toUpperCase() === 'BOY' ? 'Male' : 'Female') : '',
    birthWeight: weight ? weight[1].replace(/,/g, '') : '',
  };
}

const DERIVED_FIELDS = {
  patientAge: d => ageOn(d.patientDOB, d.dateAdmitted || todayIso()),
  // The OB score and the baby's sex and weight as the diagnosis wording
  // has them (the clinic's wording, typed here or in the Logbook Reader).
  gravida: d => obFromDx(d).gravida,
  para: d => obFromDx(d).para,
  obTerm: d => obFromDx(d).obTerm,
  obPreterm: d => obFromDx(d).obPreterm,
  obAbortion: d => obFromDx(d).obAbortion,
  obLiving: d => obFromDx(d).obLiving,
  babySex: d => babyFromDx(d).babySex,
  birthWeight: d => babyFromDx(d).birthWeight,
  expectedDD: d => addDaysIso(d.lmp, 280),
  // The admission diagnosis (Patient details, CF2 6, CF4) starts as the
  // reason for admission; the clinic's wording replaces it once complete
  // (js/dx-templates.js), and anything typed there is kept.
  admissionDx: d => d.chiefComplaint || '',
  // Birth details (Patient details) start from the APGAR scores in the
  // diagnosis, so the newborn and CF4 wording (js/dx-templates.js) use them.
  apgarScore1: d => apgarFromDx(d)[0],
  apgarScore: d => apgarFromDx(d)[1],
  // PMRF: a Filipino middle name is the mother's maiden surname, and a
  // married member's spouse most often shares the member's surname.
  motherLastName: d => d.memberMiddleName || '',
  // Permanent home address: the ZIP code of the city (DAVAO CITY -> 8000),
  // typed or read from the logbook. A ZIP typed by hand is kept.
  addrZip: d => zipForCity(d.addrCity),
  // The mother being filed: her first and middle name go on the Member
  // Profile tab too (staff review 3).
  motherFirstName: d => (motherIsFiled(d) ? d.patientFirstName || '' : ''),
  motherMiddleName: d => (motherIsFiled(d) ? d.patientMiddleName || '' : ''),
  spouseLastName: d => (d.relationship === 'Spouse' ? d.patientLastName || ''
    : d.civilStatus === 'Married' ? d.memberLastName || '' : ''),
  // The patient is the member's spouse (a mother filed under her husband):
  // she is the spouse on his Member Profile.
  spouseFirstName: d => (d.relationship === 'Spouse' ? d.patientFirstName || '' : ''),
  spouseMiddleName: d => (d.relationship === 'Spouse' ? d.patientMiddleName || '' : ''),
  // Certification of Member (CSF Part I): whoever signs it - the member, or
  // the patient signing for the member - also signs the consent (CSF Part
  // III, CF2 III-B), so their name and "Signed by" follow onto those.
  // ("Signed by" itself is kept in step both ways: applySignerLink.)
  // A representative signing the consent: their relationship to the
  // patient and why they sign, from Part I (the same person signs both),
  // or else from how the patient is related to the member.
  patientRepRelationship: d => consentRepRelationship(d),
  cf2PatientRepRelationship: d => consentRepRelationship(d),
  patientRepRelationshipOther: d => (consentRepRelationship(d) === 'Others' ? d.repRelationshipOther || '' : ''),
  cf2PatientRepRelationshipOther: d => (consentRepRelationship(d) === 'Others' ? d.repRelationshipOther || '' : ''),
  patientReason: d => (d.patientSignerType === 'Representative' ? d.repReason || '' : ''),
  cf2PatientReason: d => (d.patientSignerType === 'Representative' ? d.repReason || '' : ''),
  patientReasonOther: d => (d.patientSignerType === 'Representative' && d.repReason === 'Other' ? d.repReasonOther || '' : ''),
  cf2PatientReasonOther: d => (d.patientSignerType === 'Representative' && d.repReason === 'Other' ? d.repReasonOther || '' : ''),
  patientRepName: d => consentSignerName(d),
  cf2PatientRepName: d => consentSignerName(d),
  // ...and the same day: Part I is signed on the day of discharge, and
  // the consent (CSF Part III, CF2 III-B) and the PMRF on the day Part I
  // is, so every date the member's signer writes matches. Each can still
  // be changed; a date typed by hand is kept (and followed by the others).
  memberSignedDate: d => (d.memberSignerType === 'Member' ? d.dateDischarge || '' : ''),
  repSignedDate: d => (d.memberSignerType === 'Representative' ? d.dateDischarge || '' : ''),
  patientRepSignedDate: d => memberSignerDate(d),
  cf2PatientRepSignedDate: d => memberSignerDate(d),
  memberSignatureDate: d => (d.memberSignerType === 'Member' ? d.memberSignedDate || '' : ''),
  // CF4 IV. Course in the ward, second box: the discharge, on the day of
  // discharge (staff review): "DISCHARGE AT 10:00 AM AND GIVEN DATES FOR
  // POSTPARTUM FOLLOW UP SCHEDULES." - ____ AM until the time is known.
  cf4CourseDate2: d => d.dateDischarge || '',
  cf4CourseOrder2: d => `DISCHARGE AT ${d.timeDischarge ? formatTime12h(d.timeDischarge) : '____ AM'} ` +
    'AND GIVEN DATES FOR POSTPARTUM FOLLOW UP SCHEDULES.',
  // CF4 IV. Surgical Procedure / RVS Code: CF2 Diagnosis A's related
  // procedure with the claim's 1st case rate code, so the two always match
  // ("NORMAL SPONTANEOUS DELIVERY ... / NSDBF"). Procedures ii and iii, if
  // any, follow with their own RVS codes.
  cf4SurgicalProcedure: d => ['I', 'II', 'III']
    .map(r => [r === 'I' ? d.dxAProcI || packageProcedure(firstCaseRate(d) || d.dxARvsI) : d['dxAProc' + r],
               r === 'I' ? firstCaseRate(d) || d.dxARvsI : d['dxARvs' + r]]
      .map(v => String(v || '').trim()).filter(Boolean).join(' / '))
    .filter(Boolean).join('; '),
  // PMRF "Member's Signature over Printed Name": the member's name from
  // Patient details, as it prints ("First M. Last").
  memberSignatureName: d => getComputedValue('memberSignName'),
  // Where the clinic signs (CSF Part V, CF2 Part IV): the discharge date.
  providerSignedDate: d => d.dateDischarge || '',
  cf2ProviderSignedDate: d => d.dateDischarge || '',
  // ...and the attending health care professional (Professional 1: CSF
  // Part III/IV, CF2 Part II, CF4 Part VII), who signs on the same day.
  hciProf1DateSigned: d => d.dateDischarge || '',
  cf2Prof1DateSigned: d => d.dateDischarge || '',
  cf4ProviderSignedDate: d => d.dateDischarge || '',
  // History of present illness (Patient details' brief history and CF4 1.):
  // one line per pregnancy, in the clinic's format, for staff to finish
  // (G1 - 2018 - HOSPITAL ... G3 - PRESENT PREGNANCY). Highlighted until
  // every line is (markUnfinishedHistory).
  briefHistory: d => pregnancyLines(d.gravida),
  cf4HistoryPresentIllness: d => pregnancyLines(d.gravida),
};

/* Main ZIP codes of the cities the clinic's patients come from (the same
   cities as Ocr_module/philhealth/address_parser.py CITIES). */
const CITY_ZIP_CODES = {
  'DAVAO CITY': '8000', 'TAGUM CITY': '8100', 'PANABO CITY': '8105',
  'ISLAND GARDEN CITY OF SAMAL': '8119', 'DIGOS CITY': '8002', 'MATI CITY': '8200',
  'CAGAYAN DE ORO CITY': '9000', 'GENERAL SANTOS CITY': '9500', 'KIDAPAWAN CITY': '9400',
};
function zipForCity(city) {
  let name = String(city || '').toUpperCase().replace(/[.,]/g, ' ').replace(/\s+/g, ' ').trim();
  name = name.replace(/^CITY OF (.+)$/, '$1 CITY');
  if (name === 'DAVAO' || name === 'DC') name = 'DAVAO CITY';
  if (name === 'SAMAL' || name === 'IGACOS') name = 'ISLAND GARDEN CITY OF SAMAL';
  if (CITY_ZIP_CODES[name]) return CITY_ZIP_CODES[name];
  if (CITY_ZIP_CODES[name + ' CITY']) return CITY_ZIP_CODES[name + ' CITY'];
  // More in the box than the city ("CABANTIAN DAVAO CITY").
  const inside = Object.keys(CITY_ZIP_CODES).find(c => (' ' + name + ' ').includes(' ' + c + ' '));
  return inside ? CITY_ZIP_CODES[inside] : '';
}

/* Mobile numbers are Philippine: "+63" and the 10 digits after it, shown
   "+63 917 123 4567". "0917...", "63917..." and "917..." all become that,
   and no more than 10 digits are taken. */
function formatMobile(value) {
  if (/^(`|N\/A)$/i.test(String(value || '').trim())) return 'N/A';   // left blank
  let digits = String(value || '').replace(/\D/g, '');
  if (digits.startsWith('63')) digits = digits.slice(2);
  else if (digits.startsWith('0')) digits = digits.slice(1);
  digits = digits.slice(0, 10);
  if (!digits) return '';
  return ('+63 ' + [digits.slice(0, 3), digits.slice(3, 6), digits.slice(6)].filter(Boolean).join(' ')).trim();
}
// Capture phase: the box is tidied before the app reads it.
document.addEventListener('input', e => {
  const el = e.target;
  if (!el.matches || !el.matches('[data-mobile-ph]')) return;
  // Deleting is left alone so Backspace works; it is tidied on leaving.
  if ((e.inputType || '').startsWith('delete')) return;
  const next = formatMobile(el.value);
  if (el.value !== next) el.value = next;
}, true);
document.addEventListener('focusin', e => {
  const el = e.target;
  if (el.matches && el.matches('[data-mobile-ph]') && !el.value && !el.readOnly) el.value = '+63 ';
});
document.addEventListener('focusout', e => {
  const el = e.target;
  if (!el.matches || !el.matches('[data-mobile-ph]')) return;
  const tidy = formatMobile(el.value);
  if (el.value !== tidy) {
    el.value = tidy;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
});

/* A ` typed in any text box turns it into "N/A": left blank on purpose.
   The box then counts as answered (no highlight, not missing) and prints
   empty (js/pdf/pdf-overlay.js stripNotApplicable). Window, capture
   phase: before the boxes' own tidying (mobile, amounts) and the app. */
window.addEventListener('input', e => {
  const el = e.target;
  if (!el || (el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') || !el.value.includes('`')) return;
  if (el.tagName === 'INPUT' && !['text', 'tel', 'search', 'email', ''].includes(el.type)) return;
  // Boxes with a fixed format (typed dates, PIN and per-character boxes,
  // one-digit counts) keep it.
  if (el.matches('.pca-date-text, .pca-box, .pin-box, [data-one-digit], .box-input input, .box-input-date input')) return;
  el.value = 'N/A';
}, true);

/* Amounts (monthly income) get their thousands commas as they are typed:
   25000 -> 25,000, 1500000.5 -> 1,500,000.5. Anything that is not a digit
   or the decimal point is dropped; up to two decimals are kept. */
function formatMoney(value) {
  if (/^(`|N\/A)$/i.test(String(value || '').trim())) return 'N/A';   // left blank
  const text = String(value || '').replace(/[^\d.]/g, '');
  if (!text) return '';
  const [whole, ...rest] = text.split('.');
  const digits = whole.replace(/^0+(?=\d)/, '');
  const grouped = (digits || '0').replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return rest.length ? `${grouped}.${rest.join('').slice(0, 2)}` : grouped;
}
// Capture phase: tidied before the app reads the box. The caret keeps its
// place counted in digits, so typing in the middle does not jump to the end.
document.addEventListener('input', e => {
  const el = e.target;
  if (!el.matches || !el.matches('[data-money]')) return;
  const caret = el.selectionStart ?? el.value.length;
  const digitsBefore = el.value.slice(0, caret).replace(/[^\d.]/g, '').length;
  const next = formatMoney(el.value);
  if (next === el.value) return;
  el.value = next;
  let pos = 0, seen = 0;
  while (pos < next.length && seen < digitsBefore) { if (/[\d.]/.test(next[pos])) seen++; pos++; }
  try { el.setSelectionRange(pos, pos); } catch (_) { /* not a text box */ }
}, true);

/* Is this claim the mother's own (not her baby's)? */
function motherIsFiled(d) {
  const baby = typeof dxIsBaby === 'function' && dxIsBaby();
  return !baby && (d.patientSex === 'Female' || d.patientSex === 'F' || !!d.lmp || !!d.deliveryDate);
}

/* "Signed by" on the Certification of Member (CSF Part I) and on the
   consent (CSF Part III, CF2 III-B) say the same thing, whichever is
   changed (staff asked for them to be consistent): signed by the member
   on Part I is signed by the patient on the consent, and signed by a
   representative on one is signed by a representative on the other. */
let signerLinkWas = null;
function consentSignerFor(memberSigner) {
  return { Member: 'Patient', Representative: 'Representative' }[memberSigner] || '';
}
function memberSignerFor(consentSigner) {
  return { Patient: 'Member', Representative: 'Representative' }[consentSigner] || '';
}
/* Who signs follows whether the patient is the member: she signs as the
   member herself, or - filed under someone else, usually her husband - as
   his representative. Set when that tick changes, or while nobody is
   chosen yet; a choice made by hand afterwards is kept. */
let memberIsPatientWas = null;
function applySignerFromMember() {
  const d = state.data;
  const same = !!d.memberIsPatient;
  const changed = memberIsPatientWas !== null && same !== memberIsPatientWas;
  memberIsPatientWas = same;
  const known = same || !!(d.memberLastName || d.memberFirstName || d.relationship);
  // A saved claim brings both in at once: it keeps who it says signed.
  const signerChangedToo = signerLinkWas && (d.memberSignerType || '') !== signerLinkWas.member;
  if (!known || signerChangedToo || (!changed && d.memberSignerType)) return;
  d.memberSignerType = same ? 'Member' : 'Representative';
}

function applySignerLink() {
  applySignerFromMember();
  const d = state.data;
  const now = { member: d.memberSignerType || '', consent: d.patientSignerType || '' };
  const was = signerLinkWas;
  signerLinkWas = now;
  if (!was) return;
  const memberChanged = now.member !== was.member;
  const consentChanged = now.consent !== was.consent;
  // Both changed at once (a saved claim loaded): keep what it was saved with.
  if (memberChanged && !consentChanged && now.member) d.patientSignerType = consentSignerFor(now.member, d);
  else if (consentChanged && !memberChanged && now.consent) d.memberSignerType = memberSignerFor(now.consent, d);
  else return;
  signerLinkWas = { member: d.memberSignerType || '', consent: d.patientSignerType || '' };
}

/* Relationship of the consent's representative to the patient: Part I's
   representative's, or - the member signing for the patient - the other
   side of how the patient is related to the member (her husband is her
   spouse, the member whose child she is is her parent). */
function consentRepRelationship(d) {
  if (d.patientSignerType !== 'Representative') return '';
  if (d.repRelationship) return d.repRelationship;
  return { Spouse: 'Spouse', Child: 'Parent', Parent: 'Child', Sibling: 'Sibling' }[d.relationship] || '';
}

/* The claim's 1st case rate code: CF4's, or CSF Part V's (the two are
   linked). */
function firstCaseRate(d) {
  return String(d.cf4IcdCode || d.csfFirstCaseRate || '').trim();
}

/* The full procedure description of the package with this case rate or
   RVS code (js/dx-templates.js DX_PACKAGES): "NSDBF" -> "NORMAL SPONTANEOUS
   DELIVERY (NSD), MANAGED IN A NON-HOSPITAL HEALTH FACILITY, ...". */
function packageProcedure(code) {
  if (!code || typeof DX_PACKAGES === 'undefined') return '';
  const p = Object.values(DX_PACKAGES).find(p => p.rvs === code || p.code === code);
  return (p && (p.proc || p.title)) || '';
}

/* The date whoever signs CSF Part I wrote there. */
function memberSignerDate(d) {
  if (d.memberSignerType === 'Representative') return d.repSignedDate || '';
  if (d.memberSignerType === 'Member') return d.memberSignedDate || '';
  return '';
}

function consentSignerName(d) {
  // The patient is the member, and someone else signs for her: typed by hand.
  if (d.memberSignerType === 'Representative' && d.memberIsPatient) return '';
  if (d.memberSignerType === 'Representative') return getComputedValue('patientSignName');
  if (d.memberSignerType === 'Member') return getComputedValue('memberSignName');
  return '';
}

/* CF4 1. History of Present Illness: one line per pregnancy, "G1 - " to
   "G<gravida> - ", for staff to finish (e.g. "G1 - 2018 - HOSPITAL",
   "G3 - PRESENT PREGNANCY"). Put in by itself from Gravida while the box
   is empty (DERIVED_FIELDS), and highlighted until every line is
   finished (markUnfinishedHistory). */
function pregnancyLines(gravida) {
  const g = parseInt(gravida, 10);
  if (!(g >= 1 && g <= 15)) return '';
  return Array.from({ length: g }, (_, i) => `G${i + 1} - `).join('\n');
}

/* A pregnancy line with nothing after its dash ("G2 - ") is still to be
   written. */
function historyUnfinished(text) {
  return /^\s*G\d+\s*-\s*$/im.test(String(text || ''));
}

/* Both history boxes (Patient details' brief history, CF4 1.) stay
   highlighted while a pregnancy line is unfinished. Run after the
   missing-box marking, which clears highlights first. */
function markUnfinishedHistory() {
  ['briefHistory', 'cf4HistoryPresentIllness', 'cf4PastMedicalHistory'].forEach(key => {
    const open = key === 'cf4PastMedicalHistory'
      ? pastHistoryUnchecked && state.data[key] === PAST_HISTORY_START
      : historyUnfinished(state.data[key]);
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      el.classList.toggle('field-needs-typing', open);
      const hint = key === 'cf4PastMedicalHistory'
        ? 'Check this: click in the box to keep it, or change it'
        : 'Finish each pregnancy line: the year and where (e.g. G1 - 2018 - HOSPITAL)';
      if (open) el.title = hint;
      else if (el.title === hint) el.removeAttribute('title');
    });
  });
}

/* CF4 2.a Past Medical History starts as "NO KNOWN MEDICAL ILLNESS" for a
   new patient (applyNewPatientDefaults), highlighted until someone clicks
   in the box - having looked at it - or changes it. */
const PAST_HISTORY_START = 'NO KNOWN MEDICAL ILLNESS';
let pastHistoryUnchecked = false;
document.addEventListener('focusin', e => {
  if (!pastHistoryUnchecked || !e.target.matches || !e.target.matches('[data-autofill="cf4PastMedicalHistory"]')) return;
  pastHistoryUnchecked = false;
  markUnfinishedHistory();
});

function applyDerivedFields() {
  Object.entries(DERIVED_FIELDS).forEach(([key, work]) => {
    const next = work(state.data);
    const cur = state.data[key] || '';
    if (!cur || cur === derivedLast[key]) state.data[key] = next;
    derivedLast[key] = next;
  });
}

/* CF2 8.f: what was given for Essential Newborn Care shows once that is
   ticked; unticking it clears them, so they are not printed. */
function applyEssentialNewbornCare() {
  const on = (state.data.cf2NewbornCare || []).includes('Essential Newborn Care');
  document.querySelectorAll('[data-enc-items]').forEach(box => { box.hidden = !on; });
  if (!on && (state.data.cf2EssentialNewbornCare || []).length) state.data.cf2EssentialNewbornCare = [];
}

/* CF2 8.a: a procedure's dates box shows once the procedure is ticked. */
function applyProcedureDateRows() {
  const ticked = state.data.cf2SpecialProcedures || [];
  document.querySelectorAll('[data-proc-row]').forEach(row => {
    row.hidden = !ticked.includes(row.dataset.procRow);
  });
}

/* "Signed By" on a certification: a row marked data-signer="key:Who" is
   only for that signer, so it is hidden (and not asked for, keyIsSkipped)
   until that signer is picked. Once someone is picked, what was typed in
   the other signer's rows is cleared so it is not printed. */
function applySignerFields() {
  document.querySelectorAll('[data-signer]').forEach(row => {
    const [key, who] = row.dataset.signer.split(':');
    const picked = state.data[key] || '';
    const off = picked !== who;
    row.hidden = off;
    row.classList.toggle('signer-na', off);
    if (off && picked) {
      row.querySelectorAll('[data-autofill]').forEach(el => { state.data[el.dataset.autofill] = ''; });
    }
  });
}

function updateFormPreviews() {
  // Anything may have changed: the forms' red boxes are worked out afresh.
  clearFormCheckCache();
  applyMemberIsPatient();
  applySignerLink();
  applyNoEmployer();
  applyNoContact();
  applySpecialProceduresDefault();
  if (typeof openUsedProfessionals === 'function') openUsedProfessionals();
  applyNoPhilhealth();
  applyMailingSameAsAbove();
  applyProcedureDateRows();
  applyEssentialNewbornCare();
  applySignerFields();
  applyDerivedFields();
  // ...and again now the boxes above have settled.
  clearFormCheckCache();
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
  // The checker and its counts wait until typing pauses: run on every key
  // they made typing lag.
  updateValidationSoon();
  updateDashboardStats();
  updateSyncFieldChecks();
  updateSyncIndicator();
}

function syncAllAutofillElements() {
  // Course-in-the-ward lines may have been filled from a saved claim, so
  // reveal as many as hold data once the boxes are written.
  if (window.PCACourseRows) setTimeout(window.PCACourseRows.refresh, 0);
  // Likewise the CF4 examination groups, whose findings are locked while
  // "Essentially normal" is ticked.
  if (window.PCAExamGroups) setTimeout(window.PCAExamGroups.refresh, 0);
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

/* CF4 pain site: picking one of the clinic's usual sites (Lumbar pain,
   Lower back pain) fills the site box and ticks "Pain" with it. Runs after
   the button group's own click (registered just above), which sets the site. */
document.querySelectorAll('[data-pain-sites] .btn-check-option').forEach(btn => {
  btn.addEventListener('click', () => {
    const symptoms = Array.isArray(state.data.cf4Symptoms) ? state.data.cf4Symptoms : [];
    if (!state.data.cf4PainSite || symptoms.includes('Pain')) return;
    state.data.cf4Symptoms = [...symptoms, 'Pain'];
    updateFormPreviews();
  });
});

/* CF4 blood pressure is written systolic/diastolic, and the form's BP line
   has no slash of its own, so the box puts it in: "12080" becomes "120/80",
   "9060" becomes "90/60" (a reading starting with 1 or 2 has a 3-digit
   systolic). A slash typed by hand is kept; anything but digits is dropped. */
function formatBloodPressure(raw) {
  const s = String(raw || '').replace(/[^\d/]/g, '');
  if (s.includes('/')) {
    const [sys, ...rest] = s.split('/');
    return sys.slice(0, 3) + '/' + rest.join('').slice(0, 3);
  }
  const sysLen = /^[12]/.test(s) ? 3 : 2;
  return s.length > sysLen ? s.slice(0, sysLen) + '/' + s.slice(sysLen, sysLen + 3) : s;
}
/* T-P-A-L boxes take one digit each, as the form prints them: typing
   replaces the digit there and moves on to the next box. */
const ONE_DIGIT_ORDER = ['obTerm', 'obPreterm', 'obAbortion', 'obLiving'];
document.querySelectorAll('[data-one-digit]').forEach(el => {
  el.addEventListener('input', () => {
    const digit = el.value.replace(/\D/g, '').slice(-1);
    if (el.value !== digit) el.value = digit;
    state.data[el.dataset.autofill] = digit;
    updateFormPreviews();
    if (!digit) return;
    const nextKey = ONE_DIGIT_ORDER[ONE_DIGIT_ORDER.indexOf(el.dataset.autofill) + 1];
    const section = el.closest('section.content-section');
    const next = nextKey && section && section.querySelector(`[data-one-digit][data-autofill="${nextKey}"]`);
    if (next) { next.focus(); next.select(); }
  });
  // Typed digits are put in here, not left to the browser: replacing the
  // digit already in a one-character box was emptying it instead.
  el.addEventListener('beforeinput', e => {
    if (e.inputType !== 'insertText') return;
    e.preventDefault();
    const digit = String(e.data || '').replace(/\D/g, '').slice(-1);
    if (!digit) return;
    el.value = digit;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  });
  el.addEventListener('focus', () => el.select());
});

document.querySelectorAll('[data-autofill="cf4VitalBP"]').forEach(el => {
  el.setAttribute('inputmode', 'numeric');
  el.addEventListener('input', () => {
    const bp = formatBloodPressure(el.value);
    if (el.value === bp && state.data.cf4VitalBP === bp) return;
    el.value = bp;
    state.data.cf4VitalBP = bp;
    updateFormPreviews();
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
   patientLastName on Patient details, CSF, CF2, CF4, PMRF), so typing it
   anywhere fills it everywhere. These are separate keys on different
   forms for the same fact: typing in any of them fills the others (both
   ways), on the rule above. */
const LINKED_FIELD_GROUPS = [
  ['dischargeDx', 'dxADiagnosis', 'cf4FinalDiagnosis'],
  ['chiefComplaint', 'cf4ChiefComplaint'],
  // History of present illness: Patient details' brief history and CF4 1.
  ['briefHistory', 'cf4HistoryPresentIllness'],
  // Referred from another HCI: CF2 4. and CF4, and the referring facility.
  ['referredByHCI', 'cf4Referred'], ['referralHciName', 'cf4ReferralHci'],
  // The case rate codes: CSF Part V and CF4.
  ['csfFirstCaseRate', 'cf4IcdCode'], ['csfSecondCaseRate', 'cf4RvsCode'],
  // Health care professionals: CSF Part III and CF2 Part II
  // The first of them is the attending midwife, who also signs CF4.
  ...[1, 2, 3].flatMap(n => [
    [`hciProf${n}Name`, `cf2Prof${n}Name`, ...(n === 1 ? ['cf4AttendingProvider'] : [])],
    [`hciProf${n}AccredNo`, `cf2Prof${n}AccredNo`, ...(n === 1 ? ['cf4ProviderPAN'] : [])],
    [`hciProf${n}DateSigned`, `cf2Prof${n}DateSigned`, ...(n === 1 ? ['cf4ProviderSignedDate'] : [])],
  ]),
  // The member's own signature: CSF Part I and PMRF
  ['memberSignedDate', 'memberSignatureDate'],
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
const FREE_TEXT_TYPES = new Set(['text', 'search', 'tel', 'url', 'textarea', '']);

function toFormCase(el) {
  const raw = typeof el.value === 'string' ? el.value.trim() : el.value;
  if (typeof raw !== 'string') return raw;
  // A dropdown's value comes from its own <option> list, not from typing.
  // Upper-casing it would produce a value no option carries, and assigning
  // that back clears the dropdown - which is what emptied these boxes.
  // Dates, times, email and anything marked data-keep-case are left alone
  // for the same reason: their value has a format of its own.
  // So is a button group's (a <div>, "Patient" / "Representative").
  const kind = el.tagName === 'TEXTAREA' ? 'textarea' : (el.type || '');
  if ((el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') || !FREE_TEXT_TYPES.has(kind) ||
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
   Patient details page and again inside CSF, CF2, CF4 and
   PMRF. They were already kept in step by
   syncAllAutofillElements(), but a box you can type in invites
   typing, so the same detail got entered several times and a
   form looked empty whenever the typing had been done on a
   different page.
   Those copies are now shown, filled, but not editable, with
   one line at the top of each form saying where to change
   them. Fields a form owns on its own stay editable.
══════════════════════════════════════════════════════════ */
const FORM_SECTIONS = ['csf', 'cf1', 'cf2', 'cf4', 'pmrf'];
// Switches, not details: these choose how other boxes are filled, so
// they stay usable on the form itself.
const PATIENT_PANEL_CONTROLS = new Set(['memberIsPatient']);
// Asked on Patient details but typed on the form just as often (CF4's
// OB/GYN history: G, P and T-P-A-L): left open there too. Both boxes share one key, so
// typing in either fills the other.
const EDITABLE_ON_FORMS = new Set(['gravida', 'para', 'obTerm', 'obPreterm', 'obAbortion', 'obLiving',
  // PMRF V.: the monthly income is as often typed on the form itself.
  'monthlyIncome']);

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
      if (EDITABLE_ON_FORMS.has(el.dataset.autofill)) return;
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
const PART_TONES = 6;   // css/style.css .part-tone-0 ... -5

function groupEntryParts() {
  FORM_SECTIONS.forEach(form => {
    const section = document.getElementById('section-' + form);
    if (!section) return;
    const panel = section.querySelector('.entry-panel-body') ||
                  section.querySelector('.form-entry-panel');
    if (!panel || panel.querySelector('.entry-part')) return;

    // A heading is not always a direct child of the panel - CF4 and the
    // later pages of CF2 keep theirs inside a .pdf-page-group - so each
    // one is gathered among its own siblings rather than the panel's.
    let tone = 0;
    Array.from(panel.querySelectorAll('.entry-section-title')).forEach(title => {
      if (title.closest('.entry-part')) return;
      const container = title.parentElement;
      if (!container) return;
      const heading = title.textContent.trim();
      const wrap = document.createElement('div');
      wrap.className = 'entry-part';
      // A heading whose cards each have their own tick (the health care
      // professionals) is not ticked off as a whole.
      const perCard = title.hasAttribute('data-skip-per-card');
      if (!perCard) wrap.dataset.partId = partId(form, heading);
      container.insertBefore(wrap, title);
      let node = title;
      // Stop at the next heading, and at any block that carries headings of
      // its own - CF2 keeps its later pages in such a block, and swallowing
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
      if (!perCard) addNotNeededTick(wrap, heading);
      // Each stage of the form in its own colour, so the parts read apart.
      wrap.classList.add('part-tone-' + (tone++ % PART_TONES));
    });

    // Each health care professional is its own part with its own tick:
    // a patient seen by one midwife leaves the second and third rows empty
    // without the first being marked "not needed" too.
    panel.querySelectorAll('.dx-group-card[data-own-part]').forEach(card => {
      const label = card.querySelector('.dx-group-label');
      const outer = card.closest('.entry-part');
      const heading = outer && outer.querySelector('.entry-section-title');
      const name = (heading ? heading.textContent.trim() + ' / ' : '') + label.textContent.trim();
      card.classList.add('entry-part');
      card.dataset.partId = partId(form, name);
      addNotNeededTick(card, label.textContent.trim(), label);
    });
  });
}

/* Patient details: each section of a tab (Patient, Member, Address...)
   in its own colour, like the forms' parts, so they read apart. A heading
   and the boxes after it, up to the next heading or the tab's Back/Next
   buttons (js/easy.js), are gathered into one block. */
function groupPatientParts() {
  document.querySelectorAll('#patientTabContent .tab-pane').forEach(pane => {
    let tone = 0;
    Array.from(pane.querySelectorAll(':scope > .pca-tab-section-label')).forEach(label => {
      const wrap = document.createElement('div');
      wrap.className = 'patient-part part-tone-' + (tone++ % PART_TONES);
      pane.insertBefore(wrap, label);
      let node = label;
      while (node && !(node !== label && node.nodeType === 1 &&
             (node.classList.contains('pca-tab-section-label') || node.classList.contains('tab-step-nav')))) {
        const next = node.nextSibling;
        wrap.appendChild(node);
        node = next;
      }
    });
  });
}

function addNotNeededTick(wrap, heading, title) {
  title = title || wrap.querySelector('.entry-section-title');
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

/* No employer: a member type with no employer to certify CSF Part II
   (self-earning, professional practitioner, indigent, lifetime, OFW...)
   ticks the forms' employer parts "Not needed" - CSF Part II's employer
   details and certification. Only when the member type changes, so a part
   ticked or unticked by hand on the form stays as it is. */
const EMPLOYED_MEMBER_TYPES = ['Employed Government', 'Employed Private', 'Kasambahay/Family Driver'];
let noEmployerWas = null;
function employerPartIds() {
  return [...document.querySelectorAll('.entry-part[data-part-id]')]
    .filter(wrap => /employer/i.test(wrap.querySelector('.entry-section-title, .dx-group-label')?.textContent || ''))
    .map(wrap => wrap.dataset.partId);
}
function applyNoEmployer() {
  const type = state.data.memberType || '';
  const on = !!type && !EMPLOYED_MEMBER_TYPES.includes(type);
  if (on !== noEmployerWas && noEmployerWas !== null || (noEmployerWas === null && on)) {
    employerPartIds().forEach(id => { if (on) state.notNeeded[id] = true; else delete state.notNeeded[id]; });
    applyNotNeededParts();
  }
  noEmployerWas = on;
}

/* "No contact info" (Patient details, Contact Information): no phone or
   email, so those boxes are emptied, locked, and not asked for on the
   forms (keyIsSkipped). */
const CONTACT_KEYS = ['mobile', 'homePhone', 'businessPhone', 'email'];
function applyNoContact() {
  const on = !!state.data.noContact;
  CONTACT_KEYS.forEach(key => {
    if (on && state.data[key]) state.data[key] = '';
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      el.disabled = on;
      el.title = on ? 'No contact info (ticked on Patient details)' : '';
    });
  });
}

/* CF2 Special Procedures starts "Not needed" for a new patient; a claim
   that has one ticked (loaded or read) gets the part back. */
const SPECIAL_PROCEDURES_PART = partId('cf2', 'Special Procedures / Packages');
let specialProceduresAutoOff = false;
function applySpecialProceduresDefault() {
  if (specialProceduresAutoOff && (state.data.cf2SpecialProcedures || []).length) {
    delete state.notNeeded[SPECIAL_PROCEDURES_PART];
    specialProceduresAutoOff = false;
    applyNotNeededParts();
  }
  // PMRF V. comes back once "Updating/Amendment" is the purpose ticked.
  if (amendmentAutoOff && state.data.registrationPurpose === 'Updating/Amendment') {
    delete state.notNeeded[AMENDMENT_PART];
    amendmentAutoOff = false;
    applyNotNeededParts();
  }
  // The same for PMRF Dependents 2-4 ticked "Not needed" by themselves.
  dependentsAutoOff.forEach(n => {
    if (!String(state.data[`dep${n}LastName`] || '').trim() && !String(state.data[`dep${n}FirstName`] || '').trim()) return;
    delete state.notNeeded[partId('pmrf', `Dependent ${n} (optional)`)];
    dependentsAutoOff.delete(n);
    applyNotNeededParts();
  });
}
const dependentsAutoOff = new Set();
const AMENDMENT_PART = partId('pmrf', 'Page 2 — V. Updating/Amendment');
let amendmentAutoOff = false;

/* Health care professional 2 or 3: in use once a name or accreditation
   number is typed for them on the CSF or CF2. */
function profInUse(n) {
  return ['hciProf', 'cf2Prof'].some(p =>
    ['Name', 'AccredNo'].some(f => String(state.data[`${p}${n}${f}`] || '').trim()));
}

/* Professionals 2 and 3 fold away under "+ Add professional 2 (optional)":
   most claims have one. Open when pressed, or by themselves once one of
   theirs is filled in (a saved claim). */
function setupOptionalProfessionals() {
  document.querySelectorAll('[data-optional-prof]').forEach(card => {
    const n = card.dataset.optionalProf;
    const body = [...card.children].filter(el => !el.classList.contains('dx-group-label'));
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'btn btn-outline-secondary btn-sm mt-1 optional-prof-toggle';
    card.querySelector('.dx-group-label').insertAdjacentElement('afterend', toggle);
    const show = open => {
      card.dataset.open = open ? '1' : '';
      body.forEach(el => { el.hidden = !open; });
      toggle.setAttribute('aria-expanded', String(open));
      toggle.innerHTML = open
        ? `<i class="bi bi-chevron-up me-1"></i>Hide professional ${n}`
        : `<i class="bi bi-plus-lg me-1"></i>Add professional ${n} (optional)`;
    };
    toggle.addEventListener('click', () => show(!card.dataset.open));
    card.pcaShowOptional = show;
    show(false);
  });
}
// A saved claim with a second or third professional opens their card.
function openUsedProfessionals() {
  document.querySelectorAll('[data-optional-prof]').forEach(card => {
    if (!card.dataset.open && card.pcaShowOptional && profInUse(card.dataset.optionalProf)) card.pcaShowOptional(true);
  });
}

function applyNotNeededParts() {
  document.querySelectorAll('.entry-part[data-part-id]').forEach(wrap => {
    const off = !!state.notNeeded[wrap.dataset.partId];
    wrap.classList.toggle('part-not-needed', off);
    const box = wrap.querySelector('.part-skip-box');
    if (box && box.checked !== off) box.checked = off;
  });
}

/* Lines written only for one choice: "Others, Specify", "Other reasons"
   and CF2's co-pay amount. key -> [the choice's key, the value that wants it]. */
const SPECIFY_LINES = {
  repRelationshipOther:           ['repRelationship', 'Others'],
  repReasonOther:                 ['repReason', 'Other'],
  patientRepRelationshipOther:    ['patientRepRelationship', 'Others'],
  patientReasonOther:             ['patientReason', 'Other'],
  cf2PatientRepRelationshipOther: ['cf2PatientRepRelationship', 'Others'],
  cf2PatientReasonOther:          ['cf2PatientReason', 'Other'],
  cf2Prof1CopayAmount:            ['cf2Prof1Copay', 'Yes'],
  cf2Prof2CopayAmount:            ['cf2Prof2Copay', 'Yes'],
  cf2Prof3CopayAmount:            ['cf2Prof3Copay', 'Yes'],
  // CF4: a tick-all-that-apply group holds a list, so its option is looked for in it.
  cf4SymptomOther:                ['cf4Symptoms', 'Others'],
  cf4ReferralReason:              ['cf4Referred', 'Yes'],
  cf4ReferralHci:                 ['cf4Referred', 'Yes'],
  // CF2 referral: the referring facility's details only when referred.
  referralHciName:                ['referredByHCI', 'Yes'],
  referralStreet:                 ['referredByHCI', 'Yes'],
  referralCity:                   ['referredByHCI', 'Yes'],
  referralProvince:               ['referredByHCI', 'Yes'],
  referralZip:                    ['referredByHCI', 'Yes'],
  cf4PainSite:                    ['cf4Symptoms', 'Pain'],
  cf4AlteredSensorium:            ['cf4GeneralSurvey', 'Altered sensorium'],
  cf4TransferReason:              ['disposition', 'Transferred'],
  // PMRF V. Updating/Amendment: a From / To pair only once its box is ticked.
  ...Object.fromEntries(['amendName', 'amendDOB', 'amendSex', 'amendCivilStatus', 'amendPersonalInfo']
    .flatMap(tick => [[tick + 'From', [tick, true]], [tick + 'To', [tick, true]]])),
};
/* "Others" lines with no option of their own: other physical-exam findings
   are written only when there are some, so they are never asked for. */
const OPTIONAL_LINES = new Set([
  'cf4HeentOthers', 'cf4ChestOthers', 'cf4CvsOthers', 'cf4AbdomenOthers',
  'cf4GuOthers', 'cf4SkinOthers', 'cf4NeuroOthers',
  // A second case rate only when the claim has a second package.
  'csfSecondCaseRate', 'cf4RvsCode',
  // PMRF: a PhilSys ID, a TIN, and the numbers only some members have
  // (PWD ID, PRA SRRV, ACR I-Card, group enrollment).
  'philsysId', 'tin', 'pwdIdNo', 'praSrrvNo', 'acrICardNo', 'groupEnrollmentNo',
  // A dependent's name suffix, as other suffixes.
  'dep1Ext', 'dep2Ext', 'dep3Ext', 'dep4Ext',
]);
/* Name suffixes (JR, SR, III): most people have none, so never asked for. */
const SUFFIX_KEYS = new Set([
  'patientNameExt', 'memberNameExt', 'motherNameExt', 'spouseNameExt',
  'dep2Ext', 'dep3Ext', 'dep4Ext',
]);
function specifyChosen([key, option]) {
  const value = state.data[key];
  return Array.isArray(value) ? value.includes(option) : value === option;
}

const PATIENT_REP_KEYS = new Set([
  'patientRepRelationship', 'patientRepRelationshipOther', 'patientReason', 'patientReasonOther',
  'cf2PatientRepRelationship', 'cf2PatientRepRelationshipOther', 'cf2PatientReason', 'cf2PatientReasonOther',
]);

/* True when a key's box on this form sits in a part marked not needed or
   a row for the signer who is not signing (applySignerFields) - or it is
   a PIN whose "No PhilHealth" is ticked (NO_PHILHEALTH). */
function keyIsSkipped(form, key) {
  // Asked hundreds of times per update with the same answer: remembered
  // until the next one (formCheckCache, cleared by updateFormPreviews).
  if (!formCheckCache) return keyIsSkippedNow(form, key);   // still loading
  const memo = formCheckCache.skip || (formCheckCache.skip = new Map());
  const id = form + '|' + key;
  if (!memo.has(id)) memo.set(id, keyIsSkippedNow(form, key));
  return memo.get(id);
}

function keyIsSkippedNow(form, key) {
  if (pinNotAsked(key)) return true;
  // The printed name over the signature line of whoever is not signing.
  const signer = state.data.memberSignerType;
  if (key === 'repLineName' && signer !== 'Representative') return true;
  if (key === 'memberLineName' && signer === 'Representative') return true;
  // Why and for whom a representative signs the consent (CSF Part III,
  // CF2 III-B) is not asked when the patient signs it.
  if (state.data.patientSignerType === 'Patient' && PATIENT_REP_KEYS.has(key)) return true;
  // CF4 course in the ward and drugs: a line is only asked for once it is
  // open in "Type the details here" (they open one at a time with "+").
  // The "additional sheet(s)" ticks are only for when there are more.
  if (key === 'cf4CourseExtraSheet' || key === 'cf4DrugsExtraSheet') return true;
  // "LMP not applicable" is a tick for the few it applies to, never asked
  // for; once ticked, the LMP itself is not asked for on CF4 either.
  if (key === 'cf4LmpNA') return true;
  if (form === 'cf4' && key === 'lmp' && state.data.cf4LmpNA) return true;
  if (/^cf4(Course(Date|Order)|Drug(Name|Qty|Dose|Cost))\d+$/.test(key)) {
    // Closed lines only - not the whole page group, hidden while the
    // form's other page is showing.
    const box = document.querySelector(`#section-cf4 [data-autofill="${key}"]`);
    if (box && box.closest('[hidden]:not(.pdf-page-group)')) return true;
  }
  // CF2 8.f: the Essential Newborn Care items, once that care is ticked.
  if (key === 'cf2EssentialNewbornCare' &&
      !(state.data.cf2NewbornCare || []).includes('Essential Newborn Care')) return true;
  // A "specify" line is only wanted once the option it belongs to is chosen.
  const specifies = SPECIFY_LINES[key];
  if (specifies && !specifyChosen(specifies)) return true;
  if (OPTIONAL_LINES.has(key) || SUFFIX_KEYS.has(key)) return true;
  // A name ticked "Leave blank - written by hand after printing": its line
  // on this form prints empty on purpose (PCA_HANDWRITTEN holds the
  // overlay ids, js/pdf/overlays/*.js).
  if (handwrittenKeys(form).has(key)) return true;
  // CF2 Discharge Diagnosis: one diagnosis with one procedure is the usual
  // claim. L / R / Both is only for a procedure on one side of the body;
  // a second or third procedure row only once something is typed in it;
  // and Diagnosis B only once it has a diagnosis or code of its own (or
  // not at all, ticked "Not needed").
  if (/^dx[AB]Lat(I|II|III)$/.test(key)) return true;
  // Health care professionals 2 and 3 (CSF Part III/IV, CF2 Part II) are
  // optional: asked for only once one of their boxes has something in it.
  const prof = /^(?:hciProf|cf2Prof)([23])/.exec(key);
  if (prof && !profInUse(prof[1])) return true;
  // PMRF addresses are asked for as a whole ("Permanent Home Address",
  // fullAddress): a part left empty on Patient details - no unit, no
  // building, no lot - is left empty on purpose, so it is not marked.
  if (/^(?:mailingA|a)ddr(?:Unit|Building|Lot|Street|Subdivision|Barangay|City|Province|Zip)$/.test(key)) return true;
  // PMRF spouse: only for a married member.
  if (/^spouse(LastName|FirstName|MiddleName|NameExt)$/.test(key) && state.data.civilStatus !== 'Married') return true;
  // "No contact info" ticked on Patient details.
  if (state.data.noContact && CONTACT_KEYS.includes(key)) return true;
  const procRow = /^dx([AB])(Proc|Rvs|Date)(II|III)$/.exec(key);
  if (procRow && ['Proc', 'Rvs', 'Date'].every(p => !String(state.data[`dx${procRow[1]}${p}${procRow[3]}`] || '').trim())) return true;
  if (/^dxB/.test(key) && !String(state.data.dxBDiagnosis || '').trim() && !String(state.data.dxBIcd10 || '').trim() &&
      !['ProcI', 'RvsI', 'DateI'].some(p => String(state.data['dxB' + p] || '').trim())) return true;
  // CF2 8.a: a procedure's dates are only wanted once it is ticked.
  const procDates = /^cf2ProcDates([1-8])$/.exec(key);
  if (procDates && !(state.data.cf2SpecialProcedures || [])
        .includes(CF2_REPEAT_PROCEDURES[procDates[1] - 1])) return true;
  const name = FIX_FIELD_ALIASES[key] || key;
  const section = document.getElementById('section-' + form);
  if (!section) return false;
  const el = section.querySelector(
    `[data-autofill="${name}"], [data-box-key="${name}"]`);
  return !!(el && el.closest('.part-not-needed, .signer-na'));
}

/* What a key's box is called, in the words of the form it is typed on:
   { label, part } - its label (or, for a tick box, the option) and the
   heading of the part it sits in, since "Last Name" alone could be the
   member's or the patient's. Used by the form preview's red boxes
   (js/pdf/pdf-overlay.js) when pointed at. */
function previewSpotLabel(form, key) {
  const name = FIX_FIELD_ALIASES[key] || key;
  const pick = scope => scope && scope.querySelector(`[data-autofill="${name}"], [data-box-key="${name}"]`);
  const el = pick(document.getElementById('section-' + form)) || pick(document);
  const clean = t => (t || '').replace(/\s+/g, ' ').replace(/\*/g, '').replace('Not needed', '').trim();
  let label = '', part = '';
  if (el) {
    const wrap = el.closest('.entry-part');
    const heading = wrap && wrap.querySelector('.entry-section-title');
    part = heading ? clean(heading.textContent) : '';
    const col = el.closest('[class*="col-"]');
    const fieldLabel = col && col.querySelector('.pca-label');
    const option = el.id && document.querySelector(`label[for="${el.id}"]`);
    label = clean((fieldLabel || option || {}).textContent);
  }
  if (!label) {
    for (const f of Object.values(VAL_FIELDS)) {
      const hit = f.find(x => x.key === key);
      if (hit) { label = hit.label; break; }
    }
  }
  if (!label) label = key.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase());
  return { label, part };
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
  csf:  { title:'Claim Signature Form',        abbr:'CSF'  },
  cf1:  { title:'Claim Form 1 - member details', abbr:'CF1'  },
  cf2:  { title:'Claim Form 2 - stay at the clinic', abbr:'CF2'  },
  cf4:  { title:'Claim Form 4 - clinical record',   abbr:'CF4'  },
  pmrf: { title:'Member registration',         abbr:'PMRF' },
};

/* One form open at a time (data-bs-parent), so staff work through the
   five forms one by one instead of facing every missing field at once.
   The colour matches the form's card on the dashboard. */
function buildValidationAccordion() {
  const host = document.getElementById('valAccordion');
  if (!host) return;
  if (!host.dataset.fixWired) {
    host.dataset.fixWired = '';
    host.addEventListener('click', e => {
      const fix = e.target.closest('.val-fix[data-fix-field]');
      if (fix) focusField(fix.dataset.fixField);
    });
  }

  host.innerHTML = VAL_FORM_KEYS.map((form, i) => {
    const meta   = VAL_FORM_META[form];
    const fields = VAL_FIELDS[form];
    const items  = fields.map(({ key, label }) => `
      <div class="val-item" data-field="${key}" data-form="${form}">
        <span class="val-dot"></span>
        <span class="val-label">${label}</span>
        <span class="val-status ms-auto">Missing</span>
        <button type="button" class="val-fix" data-fix-field="${key}">Fix this <i class="bi bi-arrow-right"></i></button>
      </div>`).join('');

    return `
      <div class="pca-accordion-item accordion-item fs--${form}">
        <h2 class="accordion-header">
          <button class="accordion-button pca-accordion-btn${i === 0 ? '' : ' collapsed'}"
                  type="button" data-bs-toggle="collapse" data-bs-target="#val-${form}-panel">
            <span class="val-chip">${meta.abbr}</span>
            <span class="val-title">${meta.title}</span>
            <span class="val-bar" aria-hidden="true"><span class="val-bar-fill" id="val-${form}-bar"></span></span>
            <span class="me-3 val-score" id="val-${form}-score-2">0/${fields.length} Fields</span>
          </button>
        </h2>
        <div id="val-${form}-panel"
             class="accordion-collapse collapse${i === 0 ? ' show' : ''}"
             data-bs-parent="#valAccordion">
          <div class="accordion-body p-3"><div class="val-list">${items}
            <div class="val-extra" id="val-${form}-extra" style="display:contents"></div>
            <p class="val-done-label">Filled in</p></div></div>
        </div>
      </div>`;
  }).join('');
}

/* Every box the form itself still shows red (pdf-overlay.js
   updateOverlayForForm: empty, not answered elsewhere, not skipped) that
   the required list above does not already name. Counted and listed by
   the checker too, so it never says "complete" while the form still has
   red boxes on it. Returns [{key, label}], one per key. */
function formStillRedKeys(form) {
  const listed = new Set((VAL_FIELDS[form] || []).map(f => f.key));
  return [...redKeysOnForm(form)].filter(key => !listed.has(key))
    .map(key => ({ key, label: boxLabelFor(form, key) }));
}

/* THE rule for "missing", used by the form previews (pdf-overlay.js), the
   red boxes under "Type the details here" and the checker alike, so they
   never disagree: one spot on a form is missing when it prints nothing,
   its answer is nowhere else (the other options of a tick-one row, a digit
   past the end), it is asked for (keyIsSkipped), and it is not a single
   optional tick box (an unticked "LMP not applicable" is an answer). */
function spotIsRed(form, f, val) {
  if (val === undefined) val = typeof resolveOverlayFieldValue === 'function' ? resolveOverlayFieldValue(f) : '';
  if (val) return false;
  // Printed empty on purpose (CF1 Part II while the patient is the member).
  if (f.unless && state.data[f.unless]) return false;
  // A tick-one row worked out from other boxes (CF1 "Patient is the
  // member?"): wanted only while neither is ticked.
  if (f.checkbox && f.computed) return !getComputedValue(f.computed);
  // A single tick box (no option value of its own: "No middle name",
  // "Mononym", "With disability", "Same as above"...) is an answer either
  // way. Only a tick-one row (male / female, single / married...) can be
  // left unanswered.
  if (f.checkbox && typeof f.checkValue !== 'string') return false;
  const key = spotKey(f);
  const raw = state.data[key];
  if (Array.isArray(raw) ? raw.length > 0 : !!raw) return false;
  return !keyIsSkipped(form, key);
}
window.spotIsRed = spotIsRed;

/* The field a spot belongs to. The PMRF prints the PIN, birth date,
   PhilSys ID and TIN one character per box ("memberPINc5", "memberDOBd3"):
   each box answers to its whole field, so a TIN of 9 digits does not leave
   its last boxes "missing", and the checker names the field, not a box. */
function spotKey(f) {
  const key = f.digitKey || f.key;
  const each = f.computed && /^(memberPIN|memberDOB|philsysId|tin)[cd]\d+$/.exec(key);
  if (each) return each[1];
  // A value shown dressed up ("₱25,000" from monthlyIncome) is its field.
  if (key === 'monthlyIncomeDisplay') return 'monthlyIncome';
  return key;
}

/* Worked out once per update and reused (the checker, the form's status
   line and the red boxes all ask): updateFormPreviews clears it, since
   anything may have changed. Asking afresh for every box made typing lag. */
var formCheckCache = { red: {}, handwritten: {} };
function clearFormCheckCache() { formCheckCache.red = {}; formCheckCache.handwritten = {}; formCheckCache.skip = null; }

/* The keys a form shows at least one red spot for. */
function redKeysOnForm(form) {
  if (formCheckCache.red[form]) return formCheckCache.red[form];
  const red = new Set();
  if (typeof OVERLAY_MAP === 'undefined') return red;
  (OVERLAY_MAP[form] || []).forEach(f => { if (spotIsRed(form, f)) red.add(spotKey(f)); });
  formCheckCache.red[form] = red;
  return red;
}

/* Does any form still show this box red? (Patient details' parts count it
   as left to type, js/easy.js.) */
function keyRedOnAnyForm(key) {
  return claimForms().some(form => redKeysOnForm(form).has(key));
}

/* The keys whose line on this form is ticked "Leave blank - written by
   hand" (PCA_HANDWRITTEN holds overlay ids). */
function handwrittenKeys(form) {
  if (formCheckCache.handwritten[form]) return formCheckCache.handwritten[form];
  const keys = new Set();
  const ids = window.PCA_HANDWRITTEN;
  if (ids && ids.size && typeof OVERLAY_MAP !== 'undefined') {
    (OVERLAY_MAP[form] || []).forEach(f => { if (ids.has(f.id)) keys.add(f.digitKey || f.key); });
  }
  formCheckCache.handwritten[form] = keys;
  return keys;
}

/* A required item (VAL_FIELDS) is missing only when the form shows it red.
   Items printed through other boxes are looked for in those. */
const VAL_SPOT_KEYS = {
  patientName: ['patientLastName', 'patientFirstName', 'patientMiddleName'],
  memberName: ['memberLastName', 'memberFirstName', 'memberMiddleName'],
  cf4PhysicalExam: ['cf4Heent', 'cf4Chest', 'cf4Cvs', 'cf4Abdomen', 'cf4Gu', 'cf4Skin', 'cf4Neuro', 'cf4GeneralSurvey'],
  cf4CourseInWard: ['cf4CourseDate1', 'cf4CourseOrder1'],
  cf4DrugsAdministered: ['cf4DrugName1', 'cf4DrugQty1', 'cf4DrugDose1', 'cf4DrugCost1'],
  fullAddress: ['addrUnit', 'addrBuilding', 'addrLot', 'addrStreet', 'addrSubdivision', 'addrBarangay', 'addrCity', 'addrProvince', 'addrZip'],
  mailingAddress: ['mailingAddrUnit', 'mailingAddrBuilding', 'mailingAddrLot', 'mailingAddrStreet', 'mailingAddrSubdivision',
                   'mailingAddrBarangay', 'mailingAddrCity', 'mailingAddrProvince', 'mailingAddrZip', 'mailingCountry'],
};
function valItemRed(form, key, red) {
  if (getComputedValue(key) || keyIsSkipped(form, key)) return false;
  red = red || redKeysOnForm(form);
  return (VAL_SPOT_KEYS[key] || [key]).some(k => red.has(k));
}

function escapeHtmlText(text) {
  return String(text ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* The name a box goes by where it is typed: its label on the form's
   "Type the details here" panel, or on Patient details. */
function boxLabelFor(form, key) {
  const boxes = [...document.querySelectorAll(`#section-${form} [data-autofill="${key}"], #section-${form} [data-box-key="${key}"]`),
                 ...document.querySelectorAll(`[data-autofill="${key}"], [data-box-key="${key}"]`)];
  for (const el of boxes) {
    let node = el;
    for (let i = 0; i < 4 && node; i++, node = node.parentElement) {
      const label = node.querySelector('.pca-label');
      if (label && label.textContent.trim()) return label.textContent.replace(/\*/g, '').trim();
    }
  }
  return key.replace(/^(cf1|cf2|cf4|csf|pmrf)/, '').replace(/([a-z])([A-Z0-9])/g, '$1 $2')
    .replace(/^./, c => c.toUpperCase());
}

let validationTimer = null;
function updateValidationSoon() {
  clearTimeout(validationTimer);
  validationTimer = setTimeout(() => { clearFormCheckCache(); updateValidation(); }, 150);
}

/* ══════════════════════════════════════════════════════════
   THE FORMS THIS CLAIM NEEDS
   A claim is filed with the forms its PhilHealth package asks for
   (js/validation-rules.js CLAIM_FORMS): a delivery CF1, CF2, CF4 and the
   CSF; newborn care, family planning, prenatal and postpartum visits CF1,
   CF2 and the CSF. The others are kept out of the way - sidebar, Home,
   the checker and "Save as PDF" - and out of the count, until "Show all
   forms" is pressed (for this visit only, not saved with the patient).
══════════════════════════════════════════════════════════ */
let showAllForms = false;
let claimFormsShown = null;

function claimForms() {
  return typeof claimFormKeys === 'function' ? claimFormKeys(state.data, showAllForms) : VAL_FORM_KEYS.slice();
}
window.pcaClaimForms = claimForms;

function applyClaimForms(forms) {
  const shown = new Set(forms);
  const changed = claimFormsShown !== forms.join(',');
  claimFormsShown = forms.join(',');
  VAL_FORM_KEYS.forEach(form => {
    const display = shown.has(form) ? '' : 'none';
    document.querySelectorAll(`.sidebar-item[data-section="${form}"], .form-status-card.fs--${form}`)
      .forEach(el => { el.style.display = display; });
    const item = document.getElementById(`val-${form}-panel`)?.closest('.pca-accordion-item');
    if (item) item.style.display = display;
    const chip = document.querySelector(`[data-export-form="${form}"]`);
    if (chip) {
      chip.closest('li').style.display = display;
      // Ticked to save when it joins the claim, unticked when it leaves it.
      if (changed) chip.checked = shown.has(form);
    }
  });
  if (changed && typeof labelExportButton === 'function') labelExportButton();

  const pkg = typeof dxCurrentPackage === 'function' ? dxCurrentPackage() : '';
  const p = typeof DX_PACKAGES !== 'undefined' ? DX_PACKAGES[pkg] : null;
  const label = form => (VAL_FORM_META[form] || {}).abbr || form.toUpperCase();
  const needed = typeof claimFormKeys === 'function' ? claimFormKeys(state.data, false) : forms;
  const html = !p
    ? ''
    : showAllForms
      ? `All forms are shown. A <strong>${escapeHtmlText(p.code)}</strong> claim (${escapeHtmlText(p.name)}) needs ` +
        `${needed.map(label).join(', ')}. <a href="#" data-show-all-forms>Show only those</a>`
      : `<strong>${escapeHtmlText(p.code)}</strong> (${escapeHtmlText(p.name)}): this claim needs ` +
        `${forms.map(label).join(', ')}. <a href="#" data-show-all-forms>Show all forms</a>`;
  document.querySelectorAll('.claim-forms-note').forEach(el => {
    el.innerHTML = html;
    el.style.display = html ? '' : 'none';
  });
}

document.addEventListener('click', e => {
  const link = e.target.closest && e.target.closest('[data-show-all-forms]');
  if (!link) return;
  e.preventDefault();
  showAllForms = !showAllForms;
  clearFormCheckCache();
  updateValidation();
});

function updateValidation() {
  let totalComplete = 0;
  let totalFields   = 0;
  let formsComplete = 0;
  const forms = claimForms();
  applyClaimForms(forms);

  // Step 1–2: feature extraction + rule application
  const result = runValidationRules(getComputedValue, state.data, forms);
  lastValidationResult = result;
  window.lastValidationResult = result;

  forms.forEach(form => {
    const allFields = VAL_FIELDS[form];
    // Counted: what is filled in, and what the form shows red. Anything
    // else - a part marked "Not needed", a box not asked for - is not.
    const red = redKeysOnForm(form);
    const asked = ({ key }) => !keyIsSkipped(form, key) && (!!getComputedValue(key) || valItemRed(form, key, red));
    const fields = allFields.filter(asked);
    const skipped = allFields.length - fields.length;
    let formComplete = 0;
    totalFields += fields.length;

    allFields.forEach(field => {
      const item = document.querySelector(`.val-item[data-field="${field.key}"][data-form="${form}"]`);
      if (item) item.classList.toggle('skipped', !asked(field));
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
        item.style.order = '2';
        if (status) status.textContent = 'Filled in';
      } else {
        item.classList.remove('complete');
        item.style.order = '0';
        if (status) status.textContent = 'Not filled in yet';
      }
    });

    // ...and the other boxes the form still shows red.
    const stillRed = formStillRedKeys(form);
    const extraHost = document.getElementById(`val-${form}-extra`);
    if (extraHost) {
      extraHost.innerHTML = stillRed.map(({ key, label }) => `
        <div class="val-item" data-extra-field="${key}" style="order:0">
          <span class="val-dot"></span>
          <span class="val-label">${escapeHtmlText(label)} <small class="text-muted">(red on the form)</small></span>
          <span class="val-status ms-auto">Not filled in yet</span>
          <button type="button" class="val-fix" data-fix-field="${key}">Fix this <i class="bi bi-arrow-right"></i></button>
        </div>`).join('');
    }
    totalFields += stillRed.length;
    const formTotal = fields.length + stillRed.length;

    const scoreText = `${formComplete} of ${formTotal} filled in`
      + (skipped ? ` · ${skipped} not needed` : '');
    const scoreEl   = document.getElementById(`val-${form}-score`);
    if (scoreEl)    scoreEl.textContent = scoreText;
    const scoreEl2  = document.getElementById(`val-${form}-score-2`);
    if (scoreEl2)   scoreEl2.textContent = scoreText;

    if (formComplete === formTotal) formsComplete++;
    const statusHtml = formComplete === formTotal
      ? '<span class="badge badge-ready">Ready to print</span>'
      : formComplete > 0
        ? `<span class="badge badge-pending">Not finished (${formComplete} of ${formTotal})</span>`
        : '<span class="badge badge-pending">Not started</span>';
    // One badge on the dashboard, one in the form's own header.
    [`status-${form}`, `status-${form}-2`].forEach(id => {
      const statusEl = document.getElementById(id);
      if (statusEl) statusEl.innerHTML = statusHtml;
    });

    // Every part switched off leaves nothing to ask for - that counts as done.
    const pct = formTotal ? Math.round((formComplete / formTotal) * 100) : 100;
    const valBar = document.getElementById(`val-${form}-bar`);
    if (valBar) {
      valBar.style.width = pct + '%';
      valBar.classList.toggle('done', pct === 100);
    }
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
  if (statForms)   statForms.textContent = `${formsComplete} / ${forms.length}`;
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
      'No rule problems: what is filled in agrees with itself. Empty boxes are listed under each form below.</div>';
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
   ON EACH FORM — one line saying how much is left
   The list of every missing box used to open here, and grew long
   enough to push the boxes themselves out of sight. Now the red
   boxes on the form preview say what they are when pointed at and
   go to the box when clicked (js/pdf/pdf-overlay.js), so this line
   only counts what is left on this form and, for rules that are not
   one box, leads to "Check for missing information".
══════════════════════════════════════════════════════════ */
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
      box = document.createElement('div');
      box.className = 'form-issues';
      box.setAttribute('role', 'status');
      header.insertAdjacentElement('afterend', box);
      box.addEventListener('click', e => {
        const all = e.target.closest('[data-go-validation]');
        if (all) { e.preventDefault(); navigateTo('validation'); }
      });
    }

    // Missing = shown red on the form (spotIsRed), as on the checker.
    const red = redKeysOnForm(form);
    const missing = (VAL_FIELDS[form] || []).filter(({ key }) => valItemRed(form, key, red));
    const mine = v => (v.form && v.form === form) || (!v.form && v.field && formHasField(form, v.field));
    const missingKeys = new Set(missing.map(m => m.key));
    const rules = result.violations.filter(v => mine(v) && !(v.field && missingKeys.has(v.field) &&
      v.category === 'Missing Field'));
    const critical = rules.filter(v => v.severity.critical);
    const warnings = rules.filter(v => !v.severity.critical);

    const counts = [];
    // The boxes the form shows red count too, as on the checker.
    const missingCount = missing.length + formStillRedKeys(form).length;
    if (missingCount) counts.push(`${missingCount} missing`);
    if (critical.length) counts.push(`${critical.length} must be fixed`);
    if (warnings.length) counts.push(`${warnings.length} to check`);
    const clean = !counts.length;
    box.classList.toggle('form-issues--clean', clean);
    box.classList.toggle('form-issues--critical', critical.length > 0);

    // Nothing to report: the line goes, rather than saying so (staff asked).
    box.style.display = clean ? 'none' : '';
    const html = clean ? ''
      : `<i class="bi ${critical.length ? 'bi-exclamation-octagon-fill' : 'bi-exclamation-circle-fill'}" aria-hidden="true"></i>
         <span><strong>${counts.join(' · ')}</strong> - point at a red box on the form preview to see what it
         needs; click it to go there.${rules.length ? ` <a href="#validation" data-go-validation>See every problem</a>` : ''}</span>`;
    if (box.dataset.html !== html) {
      box.innerHTML = html;
      box.dataset.html = html;
    }
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
  // CF1 prints the home address while no other mailing address is given.
  mailingAddress: 'addrStreet',
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

  // Discharged 24 hours after admission: the date follows the admission,
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
  document.querySelectorAll('.field-rule-note, .field-rule-flag').forEach(n => n.remove());
  markMissingRequiredFields();

  result.violations.forEach(v => {
    if (!v.field) return;
    const targets = document.querySelectorAll(
      `[data-autofill="${v.field}"], [data-box-key="${v.field}"]`);
    targets.forEach(el => {
      el.classList.add(v.severity.critical ? 'field-invalid' : 'field-warn');
      el.setAttribute('title', `${v.id}: ${v.message}`);
      // The message goes in a small icon on the box's label (its text shows
      // when pointed at), not in a line added under the box: a line that
      // comes and goes as a rule is broken and fixed pushed every box below
      // it up and down while staff were typing.
      const anchor = el.closest('.col-12, .col-4, .col-6, .col-md-6, .col-md-4') || el.parentElement;
      const label = anchor && anchor.querySelector('.pca-label');
      if (label && !label.querySelector('.field-rule-flag')) {
        const flag = document.createElement('span');
        flag.className = 'field-rule-flag ' +
          (v.severity.critical ? 'field-rule-flag--danger' : 'field-rule-flag--warn');
        flag.tabIndex = 0;
        flag.setAttribute('role', 'img');
        flag.setAttribute('aria-label', v.message);
        flag.dataset.tip = v.message;
        flag.innerHTML = `<i class="bi ${v.severity.critical ? 'bi-exclamation-circle-fill' : 'bi-exclamation-triangle-fill'}"></i>`;
        label.appendChild(flag);
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
      // Not asked for right now - e.g. an "Others, specify" line whose
      // option is not chosen (keyIsSkipped, as the preview and checker use).
      // A typed date (js/date-text.js) or a row of date boxes stands in for
      // its hidden date input: it is asked for only when that date is.
      const boxRow = el.closest('[data-target]');
      const key = el.dataset.autofill || el.dataset.dateFor ||
        el.closest('[data-box-key]')?.dataset.boxKey ||
        (boxRow && document.querySelector(boxRow.dataset.target)?.dataset.autofill);
      if (key && keyIsSkipped(form, key)) return;
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
  // Last, once the marks above are cleared and set again.
  setTimeout(markUnfinishedHistory, 0);
  document.querySelectorAll('.field-missing').forEach(el => {
    el.classList.remove('field-missing');
    if (el.dataset.missingTitle !== undefined) {
      el.removeAttribute('title');
      delete el.dataset.missingTitle;
    }
  });

  const needed = new Map();   // key -> the label the checker uses
  claimForms().forEach(form => {
    const red = redKeysOnForm(form);
    (VAL_FIELDS[form] || []).forEach(({ key, label }) => {
      if (valItemRed(form, key, red)) needed.set(key, label);
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
  const forms = claimForms().length;
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
/* Claims saved before the course in the ward became the form's two boxes
   kept it as up to 15 lines of one text: put those lines back together in
   the first box, rather than leave line 2 in the second box on its own. */
function joinOldCourseLines(values) {
  const old = Object.keys(values || {}).some(k =>
    /^cf4CourseOrder([3-9]|1[0-5])$/.test(k) && String(values[k] || '').trim());
  if (!old) return values;
  const text = Array.from({ length: 15 }, (_, i) => String(values['cf4CourseOrder' + (i + 1)] || '').trim())
    .filter(Boolean).join(' ');
  const out = { ...values, cf4CourseOrder1: text, cf4CourseOrder2: '', cf4CourseDate2: '' };
  for (let i = 3; i <= 15; i++) { delete out['cf4CourseOrder' + i]; delete out['cf4CourseDate' + i]; }
  return out;
}

function applyFormData(values) {
  values = joinOldCourseLines(values);
  // A number saved or read as "0917-123-4567" is shown +63 like a typed one.
  if (values.mobile) values = { ...values, mobile: formatMobile(values.mobile) };
  if (values.monthlyIncome) values = { ...values, monthlyIncome: formatMoney(values.monthlyIncome) };
  // Member types from the old Patient details list, as the PMRF names them.
  const oldType = { 'Self-Earning / Individual Paying Member': 'Self-Earning Individual',
                    'OFW': 'Migrant Worker — Land-Based', 'Indigent': 'Listahanan' }[values.memberType];
  if (oldType) values = { ...values, memberType: oldType };
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
  refreshDischargeTick(values);
  refreshFinalDxTick(values);
  applyFixedFields();
  // A saved claim's clinic address gives way to Clinic Details'.
  if (typeof seedClinicDetails === 'function') seedClinicDetails();
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
  // Discharge back to following the admission (24 hours after).
  refreshDischargeTick();
  refreshFinalDxTick();
  // A new patient still has this clinic's fixed values, and its details
  // (name, address, the representative signing Part V).
  applyFixedFields();
  applyNewPatientDefaults();
  seedClinicDetails();
  // Nothing left to recover: this patient was cleared on purpose.
  if (typeof clearDraft === 'function') clearDraft();
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
  // js/claim-loader.js lets go of the claim that was open, so the blank
  // forms are not saved over it.
  document.dispatchEvent(new CustomEvent('pca:new-patient'));
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

/* What a new patient starts with but staff can change or remove (staff
   review 3): every part of CF4 5. Physical Examination "Essentially
   normal", and the usual chief complaint with its blank to fill. Put in
   only for a new patient, so a tick taken off or wording deleted stays
   that way, and a saved claim keeps what it was saved with. */
const CF4_PE_KEYS = ['cf4Heent', 'cf4Chest', 'cf4Cvs', 'cf4Abdomen', 'cf4Gu', 'cf4Skin', 'cf4Neuro'];
const CHIEF_COMPLAINT_START = 'HYPOGASTRIC PAIN RADIATING AT THE ____';
function applyNewPatientDefaults() {
  CF4_PE_KEYS.forEach(key => {
    const list = Array.isArray(state.data[key]) ? state.data[key] : [];
    if (!list.length) state.data[key] = ['Essentially normal'];
  });
  if (!String(state.data.cf4ChiefComplaint || '').trim()) state.data.cf4ChiefComplaint = CHIEF_COMPLAINT_START;
  // Referred from another HCI (CF2 4., CF4): most patients here come in
  // themselves, so "No" until changed to "Yes".
  if (!state.data.referredByHCI && !state.data.cf4Referred) {
    state.data.referredByHCI = 'No';
    state.data.cf4Referred = 'No';
  }
  // CF2 Special Procedures / Packages: a normal delivery has none, so the
  // part starts ticked "Not needed" (untick it to fill it in).
  if (!(state.data.cf2SpecialProcedures || []).length) {
    state.notNeeded[SPECIAL_PROCEDURES_PART] = true;
    specialProceduresAutoOff = true;
  }
  // PMRF Dependents 2-4: most members list one, so the others start ticked
  // "Not needed" unless they already have a name (untick to fill one in).
  [2, 3, 4].forEach(n => {
    if (!String(state.data[`dep${n}LastName`] || '').trim() && !String(state.data[`dep${n}FirstName`] || '').trim()) {
      state.notNeeded[partId('pmrf', `Dependent ${n} (optional)`)] = true;
      dependentsAutoOff.add(n);
    }
  });
  // PMRF Page 2 V. Updating/Amendment: only for a member updating their
  // record, so it starts "Not needed" unless that is the purpose ticked.
  if (state.data.registrationPurpose !== 'Updating/Amendment') {
    state.notNeeded[AMENDMENT_PART] = true;
    amendmentAutoOff = true;
  }
  // CF4 2.a: the usual answer, highlighted until checked (markUnfinishedHistory).
  if (!String(state.data.cf4PastMedicalHistory || '').trim()) {
    state.data.cf4PastMedicalHistory = PAST_HISTORY_START;
    pastHistoryUnchecked = true;
  }
}

/* Seed them before the first updateFormPreviews() below, which would
   otherwise sync the still-empty state over these boxes. */
applyFixedFields();
applyNewPatientDefaults();

buildValidationAccordion();
bindInputListeners();
bindBoxGroupListeners();
markPatientOwnedFields();
groupEntryParts();
setupOptionalProfessionals();
groupPatientParts();
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
  // CSF Part V's signer for the clinic.
  clinicProviderRepName:  'providerRepName',
  clinicProviderCapacity: 'providerCapacity',
  // CF4 Part VII's attending professional (linked to CSF Part III row 1).
  clinicAttendingName:    'cf4AttendingProvider',
  clinicAttendingPAN:     'cf4ProviderPAN',
};

// The clinic's saved details, kept so every new patient gets them again
// (resetFormData blanks the claim, clinic details included).
var clinicSettingsCache = null;

/* The clinic's own name, accreditation number and address are the same on
   every claim: always Clinic Details', even on a claim saved before they
   changed (staff review 3: the ZIP code), and changed only there. */
const CLINIC_OWN_KEYS = new Set(['hciName', 'hciPAN', 'hciBldg', 'hciStreet', 'hciCity', 'hciProvince', 'hciZip']);

function lockClinicOwnFields() {
  if (!clinicSettingsCache) return;
  CLINIC_OWN_KEYS.forEach(key => {
    if (!clinicSettingsCache[key]) return;
    // Clinic Details' own inputs have ids, not data-autofill.
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      el.readOnly = true;
      el.title = 'From Clinic Details - change it there';
    });
  });
}

/* Fill the claim with the clinic's details, without overwriting anything
   already typed (the clinic's own details always). Returns whether
   anything changed. */
function seedClinicDetails() {
  if (!clinicSettingsCache) return false;
  let changed = false;
  Object.values(CLINIC_FIELDS).forEach(key => {
    const own = CLINIC_OWN_KEYS.has(key);
    if (clinicSettingsCache[key] && (own ? state.data[key] !== clinicSettingsCache[key] : !state.data[key])) {
      state.data[key] = clinicSettingsCache[key];
      propagateMirroredField(key, '');   // e.g. the attending midwife onto CSF/CF2
      changed = true;
    }
  });
  return changed;
}

async function loadClinicSettings() {
  if (typeof PCAAuth === 'undefined') return;
  const settings = await PCAAuth.getClinicSettings();
  if (!settings) return;
  clinicSettingsCache = settings;

  // Fill the Settings inputs...
  Object.entries(CLINIC_FIELDS).forEach(([inputId, key]) => {
    const el = document.getElementById(inputId);
    // Accreditation numbers are shown 4-7-1, as on the form (stored as digits).
    if (el) el.value = el.matches('[data-pan-format]') ? formatAccreditationNo(settings[key]) : (settings[key] || '');
  });
  const savedAt = document.getElementById('clinicSavedAt');
  if (savedAt && settings.updated_at) {
    savedAt.textContent = 'Last saved ' + new Date(settings.updated_at).toLocaleString();
  }

  // ...and seed the claim forms, without overwriting anything already typed.
  lockClinicOwnFields();
  if (seedClinicDetails()) updateFormPreviews();
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
    // Said here rather than only by the server, so it shows before saving.
    const panDigits = (payload.hciPAN || '').replace(/\D/g, '');
    const attendingDigits = (payload.cf4ProviderPAN || '').replace(/\D/g, '');
    if (payload.hciPAN && panDigits.length !== 12) {
      showToast('Check the accreditation number',
                'The PAN must be 12 digits (it has ' + panDigits.length + ').', 'warning');
      return;
    }
    if (payload.cf4ProviderPAN && attendingDigits.length !== 12) {
      showToast('Check the attending professional\'s PAN',
                'It must be 12 digits (it has ' + attendingDigits.length + ').', 'warning');
      return;
    }

    btn.disabled = true;
    const result = await PCAAuth.saveClinicSettings(payload);
    btn.disabled = false;

    if (!result.ok) {
      showToast('Could not save', result.error, 'danger');
      return;
    }
    // Apply immediately so the open forms pick the new details up.
    clinicSettingsCache = result.settings;
    lockClinicOwnFields();
    Object.entries(CLINIC_FIELDS).forEach(([, key]) => {
      if (!result.settings[key]) return;
      const prev = state.data[key];
      state.data[key] = result.settings[key];
      propagateMirroredField(key, prev);
    });
    updateFormPreviews();
    const savedAt = document.getElementById('clinicSavedAt');
    if (savedAt) savedAt.textContent = 'Last saved just now';
    showToast('Clinic details saved',
              'These now fill in automatically on CF2, CF4 and the CSF.', 'success');
    logActivity('Clinic details updated', 'success');
  });
})();

/* ══════════════════════════════════════════════════════════
   DATE DISCHARGED — "24 hours after admission"
   After a delivery the mother most often goes home 24 hours after
   she was admitted, so the discharge date, time and AM/PM follow the
   admission by default. Unticking lets staff type a later discharge
   for a longer stay. Without a delivery the tick is not offered.
══════════════════════════════════════════════════════════ */
function dayAfterIso(iso) {
  const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return '';
  const next = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]) + 1);
  return [next.getFullYear(), String(next.getMonth() + 1).padStart(2, '0'),
          String(next.getDate()).padStart(2, '0')].join('-');
}

// Called when a claim is loaded or cleared; the setup below fills in .run.
// values: what applyFormData just put in - the tick is only decided again
// when they bring a discharge date of their own.
function refreshDischargeTick(values) {
  if (refreshDischargeTick.run) refreshDischargeTick.run(values);
}

(function setupDischargeAfterAdmission() {
  const toggle = document.getElementById('dischargeDayAfter');
  if (!toggle) return;
  const row = document.getElementById('dischargeDayAfterRow');
  const field = document.querySelector('input[type="date"][data-autofill="dateDischarge"]');
  if (!field) return;

  const hasDelivery = () => !!state.data.deliveryDate;
  // 24 hours after admission: the next day, at the time of admission.
  function target() {
    const d = state.data;
    return { dateDischarge: dayAfterIso(d.dateAdmitted),
             timeDischarge: d.timeAdmitted || '', amPmDischarge: d.timeAdmitted ? (d.amPmAdmitted || '') : '' };
  }

  let busy = false;
  function apply(sync) {
    const offered = hasDelivery();
    // Kept in place when not offered, so the boxes below never move.
    if (row) row.style.visibility = offered ? '' : 'hidden';
    const follow = offered && toggle.checked;
    field.readOnly = follow;
    field.classList.toggle('is-locked', follow);
    const want = target();
    if (!follow || !want.dateDischarge || busy) return;
    const changed = Object.keys(want).filter(k => (state.data[k] || '') !== want[k]);
    if (!changed.length) return;
    changed.forEach(k => { state.data[k] = want[k]; });
    field.value = want.dateDischarge;
    busy = true;
    try { sync(); } finally { busy = false; }
  }

  // Kept in step with the admission and the delivery as they change.
  const before = updateFormPreviews;
  updateFormPreviews = function () {
    before.apply(this, arguments);
    apply(() => before.apply(this, arguments));
  };
  toggle.addEventListener('change', () => updateFormPreviews());

  // A claim loaded with its own discharge (from the logbook) keeps it: the
  // tick stays on only when that is 24 hours after admission.
  refreshDischargeTick.run = values => {
    if (values && !('dateDischarge' in values)) { updateFormPreviews(); return; }
    const given = state.data.dateDischarge;
    const want = target();
    toggle.checked = !given || (given === want.dateDischarge &&
      (!state.data.timeDischarge || state.data.timeDischarge === want.timeDischarge));
    updateFormPreviews();
  };

  apply(() => {});
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
   the field, and ticking it blanks that same person's name on every other
   form they sign as well (SAME_SIGNER below): someone who signs one form
   by hand signs them all by hand. It is the clinic's way of working rather
   than a detail of one patient, so it is remembered on this computer and
   stays for the next patient.
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

  /* One person's printed name on every form they sign (staff review): a
     member who signs outside signs every form outside, so ticking "Leave
     blank" for them on one form ticks it on the others too. Overlay ids,
     js/pdf/overlays/*.js. */
  /* Each person: their printed names (overlay ids), and the dates they
     write beside their signature (form keys) - left blank with the names,
     since whoever signs by hand dates it by hand too. */
  const SAME_SIGNER = [
    // The member (or the patient signing for the member): CSF Parts I and
    // III, CF1 Part III, CF2 III-B, PMRF.
    { names: ['csfMemberSignName', 'csfRepSignName', 'cf1MemberSignName', 'cf1RepSignName', 'patientRepName', 'cf2PatientRepName', 'memberSignatureName'],
      dates: ['memberSignedDate', 'repSignedDate', 'patientRepSignedDate', 'cf2PatientRepSignedDate', 'memberSignatureDate'] },
    // The clinic's authorized representative: CSF Part V, CF2 Part IV.
    { names: ['providerRepName', 'cf2ProviderRepName'], dates: ['providerSignedDate', 'cf2ProviderSignedDate'] },
    // Each health care professional: CSF Part III, CF2 Part II (the first also CF4 Part VII).
    { names: ['hciProf1Name', 'cf2Prof1Name', 'cf4AttendingProvider'],
      dates: ['hciProf1DateSigned', 'cf2Prof1DateSigned', 'cf4ProviderSignedDate'] },
    { names: ['hciProf2Name', 'cf2Prof2Name'], dates: ['hciProf2DateSigned', 'cf2Prof2DateSigned'] },
    { names: ['hciProf3Name', 'cf2Prof3Name'], dates: ['hciProf3DateSigned', 'cf2Prof3DateSigned'] },
    // The employer's representative: CSF Part II.
    { names: ['employerRepName'], dates: ['employerSignedDate'] },
  ];
  // A group's every overlay id: its names, and each spot (or digit box) of its dates.
  const groupIds = g => [...g.names, ...(typeof OVERLAY_MAP === 'undefined' ? [] : Object.values(OVERLAY_MAP).flat()
    .filter(f => g.dates.includes(f.digitKey || f.key)).map(f => f.id))];
  const sameSigner = ids => new Set([...ids, ...SAME_SIGNER.filter(g => g.names.some(id => ids.includes(id))).flatMap(groupIds)]);
  // Names ticked before dates went with them: their dates are left blank too.
  SAME_SIGNER.forEach(g => {
    if (g.names.some(id => PCA_HANDWRITTEN.has(id))) groupIds(g).forEach(id => PCA_HANDWRITTEN.add(id));
  });

  // A date left blank is greyed out where it is typed, as its name is.
  function showDates() {
    SAME_SIGNER.forEach(g => {
      const on = g.names.some(id => PCA_HANDWRITTEN.has(id));
      g.dates.forEach(key => document.querySelectorAll(`[data-autofill="${key}"]`).forEach(real => {
        const boxes = [real, ...(real.id ? document.querySelectorAll(
          `.box-input-date[data-target="#${real.id}"] input`) : []), real.pcaDateText].filter(Boolean);
        boxes.forEach(el => {
          el.disabled = on;
          el.classList.toggle('is-handwritten', on);
          el.title = on ? 'Left blank: dated by hand after printing' : '';
        });
      }));
    });
  }
  document.addEventListener('DOMContentLoaded', showDates);

  const slots = [];
  function showSlot(s) {
    s.tick.checked = s.ids.every(id => PCA_HANDWRITTEN.has(id));
    if (s.input) {
      const on = s.tick.checked;
      s.input.disabled = on;
      s.input.classList.toggle('is-handwritten', on);
      s.input.title = on ? 'Left blank: written by hand after printing' : '';
    }
  }

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
    const s = { tick, ids, input };
    slots.push(s);
    showSlot(s);
    tick.addEventListener('change', () => {
      const on = tick.checked;
      sameSigner(ids).forEach(id => on ? PCA_HANDWRITTEN.add(id) : PCA_HANDWRITTEN.delete(id));
      slots.forEach(showSlot);
      showDates();
      try { localStorage.setItem(STORE, JSON.stringify([...PCA_HANDWRITTEN])); } catch (e) { /* not remembered */ }
      updateFormPreviews();
    });
  });
})();

/* The diagnosis wording of each package (the clinic's template) is in
   js/dx-templates.js. */

/* ═══════════════════════════════════════════════════════════
   Long entry tables — show one line at a time

   The course in the ward (2 printed boxes) and the drugs list (3 printed
   rows) were too much to look at, so only the first line is shown.
   "Add" reveals the next, the minus button puts it away again. A line
   that has been filled in is never hidden, so nothing typed can vanish.

   Rows are grouped by their data-* key (data-course-row, data-drug-row):
   the rows of one group are revealed together.
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
    // ...on the form preview too, which only asks for open lines (keyIsSkipped)
    if (typeof updateAllOverlays === 'function') updateAllOverlays();
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
    label: 'Box', noun: 'boxes',
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

/* A health care professional's PhilHealth accreditation number is written
   0000-0000000-0 (4, 7 and 1 digits). Boxes marked data-pan-format put the
   dashes in as it is typed - before the box's own listener stores it. */
function formatAccreditationNo(value) {
  const d = String(value || '').replace(/\D/g, '').slice(0, 12);
  return [d.slice(0, 4), d.slice(4, 11), d.slice(11)].filter(Boolean).join('-');
}
document.addEventListener('input', e => {
  const el = e.target;
  if (!el.matches || !el.matches('[data-pan-format]')) return;
  const shown = formatAccreditationNo(el.value);
  if (el.value !== shown) el.value = shown;
}, true);

/* ═══════════════════════════════════════════════════════════
   KEEP WHAT HAS BEEN TYPED

   The clinic's staff are not computer people, and a claim takes a long
   time to fill in. Closing the tab by accident, or the browser falling
   over, used to lose all of it. Everything typed is written to this
   browser's own storage as it is typed, and offered back on the next
   visit.

   It is a safety net, not a filing cabinet: it lives on this one
   computer, holds one claim in progress, and is cleared the moment the
   claim is saved or a new patient is started. The claim itself is still
   saved to the database as it always was.
═══════════════════════════════════════════════════════════ */
const PCA_DRAFT_KEY = 'pca_draft_v1';
const PCA_DRAFT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;   // a week

function saveDraft() {
  try {
    /* A claim that is open is already being saved to the database by
       js/claim-loader.js, and reopening it brings everything back. The
       draft is for the gap before that: a patient typed in but not yet
       saved, which is exactly what used to be lost. */
    if (window.PCAClaim && window.PCAClaim.isOpen && window.PCAClaim.isOpen()) {
      localStorage.removeItem(PCA_DRAFT_KEY);
      return;
    }
    const hasAnything = Object.values(state.data).some(
      v => Array.isArray(v) ? v.length : (v !== '' && v !== false && v != null));
    if (!hasAnything) { localStorage.removeItem(PCA_DRAFT_KEY); return; }
    localStorage.setItem(PCA_DRAFT_KEY, JSON.stringify({
      savedAt: Date.now(),
      data: state.data,
      notNeeded: state.notNeeded,
    }));
  } catch (e) {
    // Storage full or blocked (private window): the claim is not lost,
    // it just is not held for next time. Never interrupt the staff.
  }
}

function clearDraft() {
  try { localStorage.removeItem(PCA_DRAFT_KEY); } catch (e) { /* nothing to clear */ }
}

function readDraft() {
  try {
    const raw = localStorage.getItem(PCA_DRAFT_KEY);
    if (!raw) return null;
    const draft = JSON.parse(raw);
    if (!draft || !draft.data) return null;
    if (Date.now() - (draft.savedAt || 0) > PCA_DRAFT_MAX_AGE_MS) { clearDraft(); return null; }
    return draft;
  } catch (e) {
    return null;
  }
}

/* Typing fires on every keystroke, so hold the write back a moment. */
let draftTimer = null;
function scheduleDraftSave() {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(saveDraft, 400);
}

document.addEventListener('input', scheduleDraftSave, true);
document.addEventListener('change', scheduleDraftSave, true);
// A tab being closed or hidden gets one last write, without the wait.
window.addEventListener('pagehide', saveDraft);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') saveDraft();
});

(function offerLastDraft() {
  const draft = readDraft();
  if (!draft) return;
  const when = new Date(draft.savedAt).toLocaleString();
  const filled = Object.values(draft.data).filter(
    v => Array.isArray(v) ? v.length : (v !== '' && v !== false && v != null)).length;
  if (!filled) { clearDraft(); return; }

  const keep = confirm(
    'Unsaved patient information was found on this computer.\n\n' +
    filled + ' box' + (filled === 1 ? '' : 'es') + ' were filled in on ' + when + ', ' +
    'and the page closed before they were saved.\n\n' +
    'Press OK to put them back, or Cancel to start with empty forms.');
  if (!keep) { clearDraft(); return; }

  applyFormData(draft.data);
  if (draft.notNeeded && typeof applyNotNeededParts === 'function') {
    state.notNeeded = draft.notNeeded;
    applyNotNeededParts();
  }
  if (typeof syncBoxGroupsFromState === 'function') syncBoxGroupsFromState();
  if (typeof showToast === 'function') {
    showToast('Put back what was typed',
      'The information from ' + when + ' is back in the forms. Check it before printing.', 'info');
  }
})();

/* ═══════════════════════════════════════════════════════════
   CF4 PHYSICAL EXAMINATION — "Essentially normal" stands alone

   Each examination group on the CF4 is a tick-all-that-apply list whose
   first choice is "Essentially normal". Normal and a finding cannot both
   be true, so ticking normal clears the findings and puts them out of
   reach; ticking any finding releases normal. Staff were ticking both.
═══════════════════════════════════════════════════════════ */
(function setupEssentiallyNormal() {
  const NORMAL = 'Essentially normal';
  const refreshers = [];
  const GROUPS = ['cf4Heent', 'cf4Chest', 'cf4Cvs', 'cf4Abdomen',
                  'cf4Gu', 'cf4Skin', 'cf4Neuro'];

  GROUPS.forEach(key => {
    const boxes = Array.from(
      document.querySelectorAll(`input[type="checkbox"][data-autofill="${key}"][data-multi]`));
    if (!boxes.length) return;
    const normalBox = boxes.find(b => b.value === NORMAL);
    if (!normalBox) return;
    const findings = boxes.filter(b => b !== normalBox);

    // The free-text "others" box beside the group belongs to the findings.
    const others = document.querySelector(`[data-autofill="${key}Others"]`);

    function apply() {
      const normal = normalBox.checked;
      findings.forEach(b => {
        b.disabled = normal;
        const row = b.closest('.form-check') || b.parentElement;
        if (row) row.classList.toggle('choice-blocked', normal);
      });
      if (others) {
        others.disabled = normal;
        others.classList.toggle('is-locked', normal);
      }
    }

    normalBox.addEventListener('change', () => {
      if (normalBox.checked) {
        // Untick findings through their own handler so state.data follows.
        findings.forEach(b => {
          if (b.checked) { b.checked = false; b.dispatchEvent(new Event('change', { bubbles: true })); }
        });
        if (others && others.value) {
          others.value = '';
          others.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
      apply();
    });

    findings.forEach(b => b.addEventListener('change', () => {
      if (b.checked && normalBox.checked) {
        normalBox.checked = false;
        normalBox.dispatchEvent(new Event('change', { bubbles: true }));
      }
      apply();
    }));

    // A claim loaded from the database arrives with boxes already ticked.
    refreshers.push(apply);
    apply();
  });

  // Re-checked after anything rewrites the boxes (a loaded claim, sample
  // data, a new patient), the same way the expanding rows are.
  window.PCAExamGroups = { refresh: () => refreshers.forEach(fn => fn()) };
})();

