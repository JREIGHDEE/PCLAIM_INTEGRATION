/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Application Logic  |  Phase 1 Prototype
   This file keeps form data in memory only and makes no API calls
   itself; OCR, claim storage (MariaDB) and server-side PDF export are
   handled by the Ocr_module Flask backend (see js/ocr.js). A claim
   reviewed there is loaded into these forms by js/claim-loader.js.
═══════════════════════════════════════════════════════════ */

/* ── Auth guard: bounce to login if no active session ──────── */
(function requireLogin() {
  if (!sessionStorage.getItem('pca_logged_in')) {
    window.location.replace('login.html');
  }
})();

AOS.init({ duration: 500, once: true, offset: 30 });

/* ══════════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════════ */
const state = {
  currentSection: 'dashboard',
  uploadedFiles: [],
  data: {
    /* Patient (dependent / person confined) */
    patientLastName:'', patientFirstName:'', patientMiddleName:'', patientNameExt:'',
    patientDOB:'', patientSex:'', patientPIN:'',
    /* Member (PhilHealth account holder) */
    memberLastName:'', memberFirstName:'', memberMiddleName:'', memberNameExt:'',
    memberDOB:'', memberSex:'', memberPIN:'', relationship:'',
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
    /* Maternity / Delivery – CF3 */
    lmp:'', ageOfMenarche:'', gravida:'', para:'',
    expectedDD:'', deliveryDate:'', deliveryTime:'', amPmDelivery:'AM',
    mannerOfDelivery:'', fetalOutcome:'', babySex:'', birthWeight:'', apgarScore:'',
    briefHistory:'',
    /* Physical Examination – CF3 Part I, Section 7 */
    vitalBP:'', vitalCR:'', vitalRR:'', vitalTemp:'',
    peHEENT:'', peAbdomen:'', peChestLungs:'', peGU:'', peCVS:'', peSkinExtremities:'', peNeuroExam:'',
    /* Course in the Wards / Lab Findings – CF3 Part I, Sections 8–9 */
    courseInWards:'', labFindings:'',

    /* CF3 Page 2 – Part II: Maternity Care Package */
    initialPrenatalDate:'', vitalSignsNormal:false, pregnancyLowRisk:false,
    obTerm:'', obPreterm:'', obAbortion:'', obLiving:'',
    /* Obstetric risk factors (section 3) */
    riskMultiplePregnancy:false, riskOvarianCyst:false, riskMyomaUteri:false,
    riskPlacentaPrevia:false, riskMiscarriages:false, riskStillbirth:false,
    riskPreeclampsia:false, riskEclampsia:false, riskPrematureContraction:false,
    /* Medical/Surgical risk factors (section 4) */
    riskHypertension:false, riskHeartDisease:false, riskDiabetes:false,
    riskThyroidDisorder:false, riskObesity:false, riskAsthma:false,
    riskEpilepsy:false, riskRenalDisease:false, riskBleedingDisorders:false,
    riskPrevCesarian:false, riskUterineMyomectomy:false,
    /* Delivery plan */
    mcpOrientation:'',
    /* Follow-up Prenatal Consultation grid (visits 2nd–12th) */
    pncDate2:'', pncDate3:'', pncDate4:'', pncDate5:'', pncDate6:'', pncDate7:'',
    pncDate8:'', pncDate9:'', pncDate10:'', pncDate11:'', pncDate12:'',
    pncAog2:'', pncAog3:'', pncAog4:'', pncAog5:'', pncAog6:'', pncAog7:'',
    pncAog8:'', pncAog9:'', pncAog10:'', pncAog11:'', pncAog12:'',
    pncWeight2:'', pncWeight3:'', pncWeight4:'', pncWeight5:'', pncWeight6:'', pncWeight7:'',
    pncWeight8:'', pncWeight9:'', pncWeight10:'', pncWeight11:'', pncWeight12:'',
    pncCr2:'', pncCr3:'', pncCr4:'', pncCr5:'', pncCr6:'', pncCr7:'',
    pncCr8:'', pncCr9:'', pncCr10:'', pncCr11:'', pncCr12:'',
    pncRr2:'', pncRr3:'', pncRr4:'', pncRr5:'', pncRr6:'', pncRr7:'',
    pncRr8:'', pncRr9:'', pncRr10:'', pncRr11:'', pncRr12:'',
    pncBp2:'', pncBp3:'', pncBp4:'', pncBp5:'', pncBp6:'', pncBp7:'',
    pncBp8:'', pncBp9:'', pncBp10:'', pncBp11:'', pncBp12:'',
    pncTemp2:'', pncTemp3:'', pncTemp4:'', pncTemp5:'', pncTemp6:'', pncTemp7:'',
    pncTemp8:'', pncTemp9:'', pncTemp10:'', pncTemp11:'', pncTemp12:'',
    /* Maternal / Birth Outcome extras not already covered by Part I fields */
    obstetricIndex:'', pregnancyUterineAOG:'', presentation:'',
    /* Postpartum follow-up + discharge */
    postpartumFollowupDate:'',
    /* Postpartum Care checklist (sections 13–18) */
    ppPerinealDone:false, ppPerinealRemarks:'',
    ppComplicationsDone:false, ppComplicationsRemarks:'',
    ppBreastfeedingDone:false, ppBreastfeedingRemarks:'',
    ppFamilyPlanningDone:false, ppFamilyPlanningRemarks:'',
    ppFPServiceDone:false, ppFPServiceRemarks:'',
    ppReferredVSSDone:false, ppReferredVSSRemarks:'',
    ppScheduleNextDone:false, ppScheduleNextRemarks:'',
    /* Certification of Attending Physician/Midwife (section 19) */
    attendingPhysicianName:'', dateSigned:'',

    /* PMRF – Purpose / PhilSys / TIN */
    registrationPurpose:'', preferredKonsulta:'', philsysId:'', tin:'',
    /* PMRF – Name table checkboxes (Member / Mother / Spouse) */
    memberNoMiddleName:false, memberMononym:false,
    motherNoMiddleName:false, motherMononym:false,
    spouseNoMiddleName:false, spouseMononym:false,
    /* PMRF – Dependent 1 extras (shares patientLastName/FirstName/etc with CSF/CF2/CF3) */
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
  vitalBP:'120/80', vitalCR:'82', vitalRR:'18', vitalTemp:'36.5',
  peHEENT:'Anicteric sclerae, pink palpebral conjunctivae', peAbdomen:'Gravid, FH cephalic, FHT 140s',
  peChestLungs:'Clear breath sounds, no retractions', peGU:'Cervix 5cm dilated, 80% effaced',
  peCVS:'Normal rate, regular rhythm, no murmurs', peSkinExtremities:'No edema, no rashes',
  peNeuroExam:'Grossly intact, oriented to time, place, person',
  courseInWards:'Patient tolerated labor well. Delivered via NSD with no complications. Stable vital signs post-partum.',
  labFindings:'CBC: Hgb 120 g/L, Hct 0.36, WBC 10.5, Platelet 250. Urinalysis: unremarkable.',

  /* CF3 Page 2 – Part II: Maternity Care Package */
  initialPrenatalDate:'2025-11-15', vitalSignsNormal:true, pregnancyLowRisk:true,
  obTerm:'1', obPreterm:'0', obAbortion:'0', obLiving:'1',
  riskMultiplePregnancy:false, riskOvarianCyst:false, riskMyomaUteri:false,
  riskPlacentaPrevia:false, riskMiscarriages:false, riskStillbirth:false,
  riskPreeclampsia:false, riskEclampsia:false, riskPrematureContraction:false,
  riskHypertension:false, riskHeartDisease:false, riskDiabetes:false,
  riskThyroidDisorder:false, riskObesity:false, riskAsthma:false,
  riskEpilepsy:false, riskRenalDisease:false, riskBleedingDisorders:false,
  riskPrevCesarian:false, riskUterineMyomectomy:false,
  mcpOrientation:'yes',
  pncDate2:'11/15/25', pncAog2:'8', pncWeight2:'58', pncCr2:'80', pncRr2:'18', pncBp2:'110/70', pncTemp2:'36.5',
  pncDate3:'12/13/25', pncAog3:'12', pncWeight3:'60', pncCr3:'82', pncRr3:'18', pncBp3:'112/72', pncTemp3:'36.6',
  pncDate4:'', pncAog4:'', pncWeight4:'', pncCr4:'', pncRr4:'', pncBp4:'', pncTemp4:'',
  pncDate5:'', pncAog5:'', pncWeight5:'', pncCr5:'', pncRr5:'', pncBp5:'', pncTemp5:'',
  pncDate6:'', pncAog6:'', pncWeight6:'', pncCr6:'', pncRr6:'', pncBp6:'', pncTemp6:'',
  pncDate7:'', pncAog7:'', pncWeight7:'', pncCr7:'', pncRr7:'', pncBp7:'', pncTemp7:'',
  pncDate8:'', pncAog8:'', pncWeight8:'', pncCr8:'', pncRr8:'', pncBp8:'', pncTemp8:'',
  pncDate9:'', pncAog9:'', pncWeight9:'', pncCr9:'', pncRr9:'', pncBp9:'', pncTemp9:'',
  pncDate10:'', pncAog10:'', pncWeight10:'', pncCr10:'', pncRr10:'', pncBp10:'', pncTemp10:'',
  pncDate11:'', pncAog11:'', pncWeight11:'', pncCr11:'', pncRr11:'', pncBp11:'', pncTemp11:'',
  pncDate12:'', pncAog12:'', pncWeight12:'', pncCr12:'', pncRr12:'', pncBp12:'', pncTemp12:'',
  obstetricIndex:'G2P2', pregnancyUterineAOG:'Term, 39 weeks AOG', presentation:'Cephalic',
  postpartumFollowupDate:'2026-06-20',
  ppPerinealDone:true, ppPerinealRemarks:'Intact, no laceration',
  ppComplicationsDone:true, ppComplicationsRemarks:'None noted',
  ppBreastfeedingDone:true, ppBreastfeedingRemarks:'Latching well',
  ppFamilyPlanningDone:true, ppFamilyPlanningRemarks:'Discussed options',
  ppFPServiceDone:false, ppFPServiceRemarks:'',
  ppReferredVSSDone:false, ppReferredVSSRemarks:'',
  ppScheduleNextDone:true, ppScheduleNextRemarks:'1 week post-partum check',
  attendingPhysicianName:'Dr. Ana Reyes, M.D.', dateSigned:'2026-06-13',

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
    case 'deliveryTimeStr':
      return formatTime12h(d.deliveryTime);
    case 'timeAdmittedDigits':
      return time12hDigits(d.timeAdmitted);
    case 'timeDischargeDigits':
      return time12hDigits(d.timeDischarge);
    /* CF3 Time Admitted/Discharged: the PDF has two ruled hh:mm boxes per
       row, one before the printed "AM" label and one before "PM" — the
       box position itself indicates the period, so the value goes in
       whichever box matches (the other stays blank). */
    case 'timeAdmittedAM':   return isPMTime(d.timeAdmitted) === false ? bareTime(d.timeAdmitted) : '';
    case 'timeAdmittedPM':   return isPMTime(d.timeAdmitted) === true  ? bareTime(d.timeAdmitted) : '';
    case 'timeDischargeAM':  return isPMTime(d.timeDischarge) === false ? bareTime(d.timeDischarge) : '';
    case 'timeDischargePM':  return isPMTime(d.timeDischarge) === true  ? bareTime(d.timeDischarge) : '';
    /* CF3 Disposition on Discharge: a checkmark in whichever printed
       checkbox matches the selected value, instead of writing the word */
    case 'dispositionImproved':   return d.disposition === 'Improved'    ? '✓' : '';
    case 'dispositionTransferred':return d.disposition === 'Transferred' ? '✓' : '';
    case 'dispositionHAMA':       return d.disposition === 'HAMA'        ? '✓' : '';
    case 'dispositionAbsconded':  return d.disposition === 'Absconded'   ? '✓' : '';
    case 'dispositionExpired':    return d.disposition === 'Expired'     ? '✓' : '';
    /* CF3 HCI Accreditation No. (PAN): one character per ruled digit box */
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
  /* CF3 – Part I: Patient Clinical Record */
  ['cf3-hciPAN','hciPAN'],             ['cf3-patientName','patientName'],
  ['cf3-chiefComplaint','chiefComplaint'],
  ['cf3-dateAdmitted','dateAdmitted'], ['cf3-timeAdmitted','timeAdmittedStr'],
  ['cf3-dateDischarge','dateDischarge'],['cf3-timeDischarge','timeDischargeStr'],
  ['cf3-briefHistory','briefHistory'], ['cf3-disposition','disposition'],
  /* CF3 – Part II: Maternity */
  ['cf3-lmp','lmp'],                   ['cf3-ageOfMenarche','ageOfMenarche'],
  ['cf3-obHistory','obHistory'],       ['cf3-expectedDD','expectedDD'],
  ['cf3-admissionDx','admissionDx'],
  ['cf3-deliveryDate','deliveryDate'], ['cf3-deliveryTime','deliveryTimeStr'],
  ['cf3-mannerOfDelivery','mannerOfDelivery'],
  ['cf3-fetalOutcome','fetalOutcome'], ['cf3-babySex','babySex'],
  ['cf3-birthWeight','birthWeight'],   ['cf3-apgarScore','apgarScore'],
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
const VALID_SECTIONS = ['dashboard','patient','documents','csf','cf2','cf3','cf4','pmrf','validation','settings'];

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
    logoutBtn.addEventListener('click', e => {
      e.preventDefault();
      sessionStorage.removeItem('pca_logged_in');
      sessionStorage.removeItem('pca_user_email');
      window.location.href = 'login.html';
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
function updateFormPreviews() {
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
      const alreadyActive = btn.classList.contains('active');
      const newVal = alreadyActive ? '' : btn.dataset.value;
      state.data[key] = newVal;

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
const MIRRORED_FIELDS = {
  dischargeDx: ['dxADiagnosis', 'cf4FinalDiagnosis'],
  chiefComplaint: ['cf4ChiefComplaint'],
};

function propagateMirroredField(key, prevValue) {
  const targets = MIRRORED_FIELDS[key];
  if (!targets) return;
  const next = state.data[key];
  targets.forEach(t => {
    const cur = state.data[t];
    if (!cur || cur === prevValue) state.data[t] = next;
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
      else state.data[key] = el.value.trim ? el.value.trim() : el.value;
      propagateMirroredField(key, prev);
      updateFormPreviews();
    };
    el.addEventListener('input', handler);
    el.addEventListener('change', handler);
  });
}

/* ══════════════════════════════════════════════════════════
   SEGMENTED "BOX" INPUTS
   Some CF3 fields (dates, HCI Accreditation No./PAN) print as
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
    text.textContent = 'Waiting for input…';
  } else {
    dot.classList.add('active');
    text.textContent = `Syncing ${filled} of ${total} fields across CSF, CF2, CF3 and PMRF`;
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
  csf:  { title:'Claim Signature Form (CSF)',        icon:'bi-file-earmark-text',    tone:'text-primary' },
  cf2:  { title:'Confinement Form 2 (CF2)',          icon:'bi-file-earmark-medical', tone:'text-teal'    },
  cf3:  { title:'Confinement Form 3 (CF3)',          icon:'bi-file-earmark-check',   tone:'text-orange'  },
  cf4:  { title:'Clinical Record (CF4)',             icon:'bi-file-earmark-plus',    tone:'text-danger'  },
  pmrf: { title:'Member Registration Form (PMRF)',   icon:'bi-person-lines-fill',    tone:'text-purple'  },
};

function buildValidationAccordion() {
  const host = document.getElementById('valAccordion');
  if (!host) return;

  host.innerHTML = VAL_FORM_KEYS.map((form, i) => {
    const meta   = VAL_FORM_META[form];
    const fields = VAL_FIELDS[form];
    const items  = fields.map(({ key, label }) => `
      <div class="val-item" data-field="${key}" data-form="${form}">
        <i class="bi bi-x-circle-fill text-danger val-icon"></i>
        ${label}
        <span class="val-status ms-auto text-danger">Missing</span>
      </div>`).join('');

    return `
      <div class="pca-accordion-item accordion-item" data-aos="fade-up">
        <h2 class="accordion-header">
          <button class="accordion-button pca-accordion-btn${i === 0 ? '' : ' collapsed'}"
                  type="button" data-bs-toggle="collapse" data-bs-target="#val-${form}-panel">
            <i class="bi ${meta.icon} me-2 ${meta.tone}"></i>
            ${meta.title}
            <span class="ms-auto me-3 val-score" id="val-${form}-score-2">0/${fields.length} Fields</span>
          </button>
        </h2>
        <div id="val-${form}-panel" class="accordion-collapse collapse${i === 0 ? ' show' : ''}">
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
      const icon   = item.querySelector('.val-icon');
      const status = item.querySelector('.val-status');
      if (val) {
        formComplete++; totalComplete++;
        item.classList.add('complete');
        if (icon)   icon.className   = 'bi bi-check-circle-fill text-success val-icon';
        if (status) { status.textContent = 'Complete'; status.className = 'val-status ms-auto text-success'; }
      } else {
        item.classList.remove('complete');
        if (icon)   icon.className   = 'bi bi-x-circle-fill text-danger val-icon';
        if (status) { status.textContent = 'Missing';  status.className = 'val-status ms-auto text-danger'; }
      }
    });

    const scoreText = `${formComplete}/${fields.length} Fields`;
    const scoreEl   = document.getElementById(`val-${form}-score`);
    if (scoreEl)    scoreEl.textContent = scoreText;
    const scoreEl2  = document.getElementById(`val-${form}-score-2`);
    if (scoreEl2)   scoreEl2.textContent = scoreText;

    const statusEl = document.getElementById(`status-${form}`);
    if (statusEl) {
      if (formComplete === fields.length) {
        formsComplete++;
        statusEl.innerHTML = '<span class="badge badge-ready">Ready</span>';
      } else if (formComplete > 0) {
        statusEl.innerHTML = `<span class="badge badge-pending">In Progress (${formComplete}/${fields.length})</span>`;
      } else {
        statusEl.innerHTML = '<span class="badge badge-pending">Pending</span>';
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
  if (scoreCircle) scoreCircle.classList.toggle('good', overall >= 75);
  if (statForms)   statForms.textContent = `${formsComplete} / ${VAL_FORM_KEYS.length}`;
  if (statVal)     statVal.textContent   =
    overall === 0 ? 'Pending' : overall < 50 ? 'In Progress' : overall < 100 ? 'Partial' : 'Complete';

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
          `<code>${v.id}</code> ${v.message}`;
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
    ? 'Resolve ' + result.critical.length + ' critical error' +
      (result.critical.length === 1 ? '' : 's') + ' before generating the PDF'
    : '';

  VAL_FORM_KEYS.forEach(form => {
    const btn = document.getElementById('export-' + form + '-btn');
    if (!btn) return;
    btn.classList.toggle('is-blocked', blocked);
    btn.setAttribute('title', reason || 'Export the filled, print-ready PDF');
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
  resetFormData();
  showToast('Form cleared', 'All patient information has been cleared.', 'info');
  logActivity('Patient information cleared', 'warning');
});

/* ══════════════════════════════════════════════════════════
   FILE UPLOAD
══════════════════════════════════════════════════════════ */
(function setupUpload() {
  const dropZone  = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileList  = document.getElementById('fileList');
  const fileEmpty = document.getElementById('fileListEmpty');
  const fileCount = document.getElementById('fileCount');
  const statDocs  = document.getElementById('statDocs');

  dropZone.addEventListener('click', () => fileInput.click());
  ['dragenter','dragover'].forEach(e =>
    dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('drag-over'); }));
  ['dragleave','drop'].forEach(e =>
    dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('drag-over'); }));
  dropZone.addEventListener('drop', e => { e.preventDefault(); handleFiles(e.dataTransfer.files); });
  fileInput.addEventListener('change', () => { handleFiles(fileInput.files); fileInput.value = ''; });

  function handleFiles(files) {
    const allowedExt = ['.pdf','.jpg','.jpeg','.png'];
    let added = 0;
    Array.from(files).forEach(f => {
      const ext = '.' + f.name.split('.').pop().toLowerCase();
      if (!allowedExt.includes(ext)) {
        showToast('Invalid file type', `${escHtml(f.name)} is not supported.`, 'danger'); return;
      }
      if (f.size > 10*1024*1024) {
        showToast('File too large', `${escHtml(f.name)} exceeds 10 MB.`, 'danger'); return;
      }
      state.uploadedFiles.push({ name: f.name, size: f.size });
      added++;
    });
    if (added) {
      renderFileList(); simulateProgress();
      logActivity(`${added} document(s) added`, 'success');
      showToast('Files added', `${added} file(s) ready for demonstration.`, 'success');
    }
  }

  function renderFileList() {
    Array.from(fileList.querySelectorAll('.file-item')).forEach(el => el.remove());
    fileEmpty.style.display = state.uploadedFiles.length ? 'none' : '';
    if (fileCount) fileCount.textContent = state.uploadedFiles.length;
    if (statDocs)  statDocs.textContent  = state.uploadedFiles.length;
    state.uploadedFiles.forEach((f, i) => {
      const li = document.createElement('li');
      li.className = 'file-item';
      li.innerHTML = `<span class="file-item-icon">${fileIcon(f.name)}</span>
        <span class="file-item-name">${escHtml(f.name)}</span>
        <span class="file-item-size">${fmtBytes(f.size)}</span>
        <button class="file-item-remove" data-index="${i}" title="Remove"><i class="bi bi-x-lg"></i></button>`;
      fileList.appendChild(li);
    });
    fileList.querySelectorAll('.file-item-remove').forEach(btn =>
      btn.addEventListener('click', () => {
        state.uploadedFiles.splice(+btn.dataset.index, 1);
        renderFileList();
        showToast('File removed', 'File removed from the list.', 'info');
      }));
  }

  function simulateProgress() {
    const wrap = document.getElementById('uploadProgressWrap');
    const bar  = document.getElementById('uploadProgressBar');
    const pct  = document.getElementById('uploadPct');
    if (!wrap) return;
    wrap.style.display = ''; let p = 0;
    const t = setInterval(() => {
      p += Math.random()*18+8;
      if (p >= 100) { p=100; clearInterval(t); setTimeout(() => { wrap.style.display='none'; }, 600); }
      bar.style.width = p+'%'; pct.textContent = Math.round(p)+'%';
    }, 100);
  }

  function fileIcon(name) {
    const ext = name.split('.').pop().toLowerCase();
    return { pdf:'📄', jpg:'🖼️', jpeg:'🖼️', png:'🖼️' }[ext] || '📎';
  }
  function fmtBytes(b) {
    if (b < 1024) return b+' B';
    if (b < 1048576) return (b/1024).toFixed(1)+' KB';
    return (b/1048576).toFixed(1)+' MB';
  }
})();

/* ══════════════════════════════════════════════════════════
   ACTIVITY FEED
══════════════════════════════════════════════════════════ */
function logActivity(text, type = 'info') {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;
  const map = {
    success:{ cls:'bg-success-soft', icon:'bi-check-circle-fill text-success' },
    warning:{ cls:'bg-warning-soft', icon:'bi-exclamation-circle-fill text-warning' },
    info:   { cls:'bg-primary-soft', icon:'bi-info-circle-fill text-primary' },
    danger: { cls:'bg-warning-soft', icon:'bi-x-circle-fill text-danger' },
  };
  const { cls, icon } = map[type] || map.info;
  const li = document.createElement('li');
  li.className = 'activity-item';
  li.innerHTML = `<div class="activity-icon ${cls}"><i class="bi ${icon}"></i></div>
    <div class="activity-body">
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
  setTimeout(() => div.remove(), 4500);
}

/* ══════════════════════════════════════════════════════════
   SETTINGS
══════════════════════════════════════════════════════════ */
document.getElementById('compactMode').addEventListener('change', function () {
  document.getElementById('sidebar').classList.toggle('collapsed', this.checked);
});
document.getElementById('animationsToggle').addEventListener('change', function () {
  if (this.checked) AOS.init({ duration:500, once:true, offset:30 });
  else document.querySelectorAll('[data-aos]').forEach(el => {
    el.removeAttribute('data-aos'); el.style.opacity=1; el.style.transform='none';
  });
});
document.getElementById('themeSelect').addEventListener('change', function () {
  const themes = {
    light:{ '--primary':'#2563EB', '--sidebar-bg':'#0F172A' },
    blue: { '--primary':'#1D4ED8', '--sidebar-bg':'#1E3A5F' },
    teal: { '--primary':'#0D9488', '--sidebar-bg':'#0F2027' },
  };
  Object.entries(themes[this.value] || themes.light).forEach(([k,v]) =>
    document.documentElement.style.setProperty(k, v));
  showToast('Theme changed', `Switched to ${this.value} theme.`, 'info');
});

document.getElementById('notifBtn').addEventListener('click', () =>
  showToast('Notifications',
    '3 pending items: Missing admission date, missing physician signature, document upload required.',
    'warning'));

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