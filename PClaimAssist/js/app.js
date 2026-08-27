/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Application Logic  |  Phase 1 Prototype
   Privacy-by-design: no storage, no server calls.
═══════════════════════════════════════════════════════════ */
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
    /* HCI */
    hciPAN:'', hciName:'', hciStreet:'', hciCity:'', hciProvince:'',
    /* Employer – CSF Part II */
    employerPEN:'', employerPhone:'', employerName:'',
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
  hciPAN:'000001234', hciName:'Mapagpala Maternity Clinic',
  hciStreet:'456 Bonifacio Avenue', hciCity:'Quezon City', hciProvince:'Metro Manila',
  employerPEN:'', employerPhone:'', employerName:'',
  civilStatus:'Married', placeOfBirth:'Quezon City, Metro Manila', citizenship:'Filipino',
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
};

/* ══════════════════════════════════════════════════════════
   COMPUTED VALUE RESOLVER
══════════════════════════════════════════════════════════ */
const DATE_FIELDS = new Set([
  'memberDOB','patientDOB','dateAdmitted','dateDischarge',
  'deliveryDate','expectedDD','lmp'
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
    /* CF3 Date Admitted/Discharged split into per-box Month/Day/Year
       to match the PDF's three separate ruled boxes */
    case 'dateAdmittedMM':   return d.dateAdmitted ? d.dateAdmitted.split('-')[1] : '';
    case 'dateAdmittedDD':   return d.dateAdmitted ? d.dateAdmitted.split('-')[2] : '';
    case 'dateAdmittedYYYY': return d.dateAdmitted ? d.dateAdmitted.split('-')[0] : '';
    case 'dateDischargeMM':   return d.dateDischarge ? d.dateDischarge.split('-')[1] : '';
    case 'dateDischargeDD':   return d.dateDischarge ? d.dateDischarge.split('-')[2] : '';
    case 'dateDischargeYYYY': return d.dateDischarge ? d.dateDischarge.split('-')[0] : '';
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

/* ══════════════════════════════════════════════════════════
   VALIDATION FIELDS PER FORM
══════════════════════════════════════════════════════════ */
const VAL_FIELDS = {
  csf: [
    { key:'memberPIN',     label:'Member PhilHealth PIN' },
    { key:'memberName',    label:'Member Name' },
    { key:'memberDOB',     label:'Member Date of Birth' },
    { key:'patientPIN',    label:'Patient / Dependent PIN' },
    { key:'patientName',   label:'Patient Name' },
    { key:'relationship',  label:'Relationship to Member' },
    { key:'dateAdmitted',  label:'Date Admitted' },
    { key:'dateDischarge', label:'Date Discharged' },
    { key:'patientDOB',    label:'Patient Date of Birth' },
  ],
  cf2: [
    { key:'hciPAN',        label:'HCI Accreditation No. (PAN)' },
    { key:'hciName',       label:'Health Care Institution Name' },
    { key:'patientName',   label:'Patient Name' },
    { key:'dateAdmitted',  label:'Date Admitted' },
    { key:'dateDischarge', label:'Date Discharged' },
    { key:'disposition',   label:'Patient Disposition' },
    { key:'accommodation', label:'Type of Accommodation' },
    { key:'admissionDx',   label:'Admission Diagnosis' },
    { key:'dischargeDx',   label:'Discharge Diagnosis' },
  ],
  cf3: [
    { key:'hciPAN',           label:'HCI Accreditation No. (PAN)' },
    { key:'patientName',      label:'Patient Name' },
    { key:'chiefComplaint',   label:'Chief Complaint / Reason for Admission' },
    { key:'dateAdmitted',     label:'Date Admitted' },
    { key:'lmp',              label:'Last Menstrual Period (LMP)' },
    { key:'deliveryDate',     label:'Date of Delivery' },
    { key:'mannerOfDelivery', label:'Manner of Delivery' },
    { key:'fetalOutcome',     label:'Fetal Outcome' },
    { key:'birthWeight',      label:'Birth Weight (grams)' },
  ],
  pmrf: [
    { key:'memberPIN',     label:'PhilHealth Identification Number (PIN)' },
    { key:'memberName',    label:'Member Name' },
    { key:'memberDOB',     label:'Member Date of Birth' },
    { key:'civilStatus',   label:'Civil Status' },
    { key:'citizenship',   label:'Citizenship' },
    { key:'fullAddress',   label:'Permanent Home Address' },
    { key:'mobile',        label:'Mobile Number' },
    { key:'memberType',    label:'Member Type' },
    { key:'patientName',   label:'Dependent Name' },
  ],
};

/* ══════════════════════════════════════════════════════════
   NAVIGATION
══════════════════════════════════════════════════════════ */
function navigateTo(section) {
  const prev = document.querySelector('.content-section.active');
  if (prev) prev.classList.remove('active');
  const next = document.getElementById('section-' + section);
  if (next) { next.classList.add('active'); AOS.refresh(); }
  document.querySelectorAll('.sidebar-item').forEach(el =>
    el.classList.toggle('active', el.dataset.section === section));
  state.currentSection = section;
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar.classList.contains('mobile-open')) {
    sidebar.classList.remove('mobile-open');
    overlay && overlay.classList.remove('active');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  // Trigger PDF rendering when entering a form section
  if (['csf','cf2','cf3','pmrf'].includes(section) && typeof onFormSectionActivated === 'function') {
    // Small delay lets the section become visible (display:block) before measuring width
    setTimeout(() => onFormSectionActivated(section), 60);
  }
}

document.querySelectorAll('.sidebar-item').forEach(item =>
  item.addEventListener('click', e => {
    if (!item.dataset.section) return; // external link (e.g. OCR page) — let the browser navigate normally
    e.preventDefault(); navigateTo(item.dataset.section);
  }));

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
      } else if (sibling.type === 'checkbox') {
        sibling.checked = !!state.data[key];
      } else if (sibling.tagName === 'SELECT' || sibling.tagName === 'TEXTAREA' || sibling.tagName === 'INPUT') {
        if (sibling.value !== val) sibling.value = val;
      }
    });
  });
}

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

function bindInputListeners() {
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    const handler = () => {
      if (el.type === 'radio') { if (el.checked) state.data[key] = el.value; }
      else if (el.type === 'checkbox') state.data[key] = el.checked;
      else state.data[key] = el.value.trim ? el.value.trim() : el.value;
      updateFormPreviews();
    };
    el.addEventListener('input', handler);
    el.addEventListener('change', handler);
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
function updateValidation() {
  let totalComplete = 0;
  let totalFields   = 0;
  let formsComplete = 0;

  ['csf','cf2','cf3','pmrf'].forEach(form => {
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

    const scoreEl  = document.getElementById(`val-${form}-score`);
    if (scoreEl)   scoreEl.textContent = `${formComplete}/${fields.length} Fields`;

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
  if (statForms)   statForms.textContent = `${formsComplete} / 4`;
  if (statVal)     statVal.textContent   =
    overall === 0 ? 'Pending' : overall < 50 ? 'In Progress' : overall < 100 ? 'Partial' : 'Complete';
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
function loadSampleData() {
  Object.assign(state.data, SAMPLE_DATA);
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    if (!(key in SAMPLE_DATA)) return;
    if (el.type === 'radio') el.checked = el.value === SAMPLE_DATA[key];
    else if (el.type === 'checkbox') el.checked = !!SAMPLE_DATA[key];
    else el.value = SAMPLE_DATA[key];
  });
  updateFormPreviews();
  showToast('Sample data loaded', 'All fields populated with fictional demo data.', 'success');
  logActivity('Sample data loaded for demonstration', 'success');
  navigateTo('patient');
}


document.getElementById('clearFormBtn').addEventListener('click', () => {
  const AM_DEFAULTS = { amPmAdmitted:'AM', amPmDischarge:'AM', amPmDelivery:'AM' };
  Object.keys(state.data).forEach(k => { state.data[k] = AM_DEFAULTS[k] || ''; });
  document.querySelectorAll('[data-autofill]').forEach(el => {
    const key = el.dataset.autofill;
    if (el.type === 'radio') el.checked = false;
    else if (el.type === 'checkbox') el.checked = false;
    else if (AM_DEFAULTS[key]) el.value = AM_DEFAULTS[key];
    else el.value = '';
  });
  updateFormPreviews();
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
bindInputListeners();
updateFormPreviews();
navigateTo('dashboard');

// Add this at the very bottom of js/app.js
window.state = state;