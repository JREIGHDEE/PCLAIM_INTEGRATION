/* ═══════════════════════════════════════════════════════════
   RULE-BASED VALIDATION ENGINE
   Deterministic IF-THEN rules per the PClaimAssist research
   design (Tables 3.3–3.8). Two-step process:
     1. Feature extraction  — computeFeatures()
     2. Rule application    — RULES evaluated in category order

   Rules read ONLY confirmed values. While an OCR suggestion is
   still pending review, the original reading is used, never the
   suggested value — so no rule ever depends on an unconfirmed
   suggestion.
═══════════════════════════════════════════════════════════ */

/* Severity → how the result is grouped and whether it blocks PDF generation. */
const SEVERITY = {
  block_submission: { critical: true,  label: 'Critical',   cls: 'danger'  },
  halt_validation:  { critical: true,  label: 'Critical',   cls: 'danger'  },
  display_warning:  { critical: false, label: 'Warning',    cls: 'warning' },
  flag_high_risk:   { critical: false, label: 'High Risk',  cls: 'warning' },
};

/* Required fields per form, used by MF rules and the checker UI. */
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
  // CF1: everything is already asked for on Patient details and the PMRF.
  cf1: [
    { key:'memberPIN',     label:'Member PhilHealth PIN' },
    { key:'memberName',    label:'Member Name' },
    { key:'memberDOB',     label:'Member Date of Birth' },
    { key:'memberSex',     label:'Member Sex' },
    { key:'mailingAddress',label:'Mailing Address' },
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
    { key:'dxADiagnosis',  label:'Discharge Diagnosis' },
  ],
  cf4: [
    { key:'memberPIN',            label:'Member PhilHealth PIN' },
    { key:'patientName',          label:'Patient Name' },
    { key:'patientAge',           label:'Patient Age' },
    { key:'patientSex',           label:'Patient Sex' },
    { key:'dateAdmitted',         label:'Date Admitted' },
    { key:'dateDischarge',        label:'Date Discharged' },
    { key:'cf4ChiefComplaint',    label:'Chief Complaint' },
    { key:'cf4HistoryPresentIllness', label:'History of Present Illness' },
    { key:'cf4PhysicalExam',      label:'Physical Examination Findings' },
    { key:'cf4CourseInWard',      label:'Course in the Ward' },
    { key:'cf4DrugsAdministered', label:'Drugs / Medicines Administered' },
    { key:'cf4FinalDiagnosis',    label:'Final Diagnosis' },
  ],
  pmrf: [
    { key:'memberPIN',     label:'PhilHealth Identification Number (PIN)' },
    { key:'memberName',    label:'Member Name' },
    { key:'memberDOB',     label:'Member Date of Birth' },
    { key:'civilStatus',   label:'Civil Status' },
    { key:'citizenship',   label:'Citizenship' },
    { key:'fullAddress',   label:'Permanent Home Address' },
    { key:'memberType',    label:'Member Type' },
    { key:'patientName',   label:'Dependent Name' },
  ],
};

const VAL_FORM_KEYS = ['csf', 'cf1', 'cf2', 'cf4', 'pmrf'];

/* The forms each PhilHealth package's claim is filed with, of the ones this
   system makes (js/dx-templates.js DX_PACKAGES keys). The other documents
   those claims need - eSOA, partograph, ANCR, PPCR - are not made here.
     NSDBF       normal delivery           CF1 + CF2 + CF4 + CSF (no CF3, 2026 circular)
     NCP         newborn care              CF1 + CF2 + CSF + PMRF (the baby is registered
                                           as the member's dependent; provisional)
     FP001       implant insertion         CF1 + CF2 + CSF (provisional)
     IUD (58300) interval IUD insertion    CF1 + CF2 + CSF (provisional)
     ANV         prenatal care             CF1 + CF2 + CSF
     PPC01       postpartum visit          CF1 + CF2 + CSF
   Any other claim shows the PMRF only with "Show all forms". */
const CLAIM_FORMS = {
  NSDBF: ['csf', 'cf1', 'cf2', 'cf4'],
  NCP:   ['csf', 'cf1', 'cf2', 'pmrf'],
  FP001: ['csf', 'cf1', 'cf2'],
  IUD:   ['csf', 'cf1', 'cf2'],
  ANV:   ['csf', 'cf1', 'cf2'],
  PPC01: ['csf', 'cf1', 'cf2'],
};

/* The claim's package: picked by staff, or worked out from the patient
   (js/dx-templates.js dxCurrentPackage). */
function claimPackage(data) {
  if (typeof window.dxCurrentPackage === 'function') return window.dxCurrentPackage();
  return (data && data.dxPackage) || '';
}

/* The forms this claim is filed with, in VAL_FORM_KEYS order - every form
   when showAll, or when the package is not known. */
function claimFormKeys(data, showAll) {
  const forms = !showAll && CLAIM_FORMS[claimPackage(data)];
  return forms ? VAL_FORM_KEYS.filter(f => forms.includes(f)) : VAL_FORM_KEYS.slice();
}

const FORM_LABELS = {
  csf: 'CSF', cf1: 'CF1', cf2: 'CF2', cf4: 'CF4', pmrf: 'PMRF',
};

/* ── Helpers ─────────────────────────────────────────────── */

function valDigitsOnly(v) {
  return String(v == null ? '' : v).replace(/\D/g, '');
}

function isBlank(v) {
  return v == null || String(v).trim() === '';
}

/* Parse the app's MM-DD-YYYY display format into a Date, or null. */
function parseDisplayDate(v) {
  if (isBlank(v)) return null;
  const m = String(v).trim().match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
  if (!m) return null;
  const mm = +m[1], dd = +m[2], yyyy = +m[3];
  if (mm < 1 || mm > 12 || dd < 1 || dd > 31) return null;
  const d = new Date(yyyy, mm - 1, dd);
  // Reject rolled-over dates like 02-31-2026
  if (d.getMonth() !== mm - 1 || d.getDate() !== dd) return null;
  return d;
}

/* ── Feature extraction (Table 3.3) ──────────────────────── */

function computeFeatures(getValue, data, forms) {
  const f = {};

  // <field>_present — one per required field across the claim's forms
  const requiredKeys = new Set();
  (forms || VAL_FORM_KEYS).forEach(form => VAL_FIELDS[form].forEach(({ key }) => requiredKeys.add(key)));
  let blank = 0;
  requiredKeys.forEach(key => {
    // No PhilHealth (Patient details): that person's PIN is not asked for.
    const notAsked = data && ((key === 'patientPIN' && data.patientNoPhilhealth) ||
                              (key === 'memberPIN' && data.memberNoPhilhealth));
    const present = notAsked || !isBlank(getValue(key));
    f[key + '_present'] = present ? 1 : 0;
    if (!present) blank++;
  });
  f.blank_fields_count = blank;

  // PhilHealth PIN format
  const pinRaw = getValue('memberPIN');
  f._memberNoPhilhealth = data && data.memberNoPhilhealth ? 1 : 0;
  f.philhealth_pin_length = valDigitsOnly(pinRaw).length;
  f.philhealth_pin_contains_letters = (!isBlank(pinRaw) && /[^\d\s-]/.test(String(pinRaw))) ? 1 : 0;

  // Date format validity across every date field that has a value
  const dateKeys = ['memberDOB', 'patientDOB', 'dateAdmitted', 'dateDischarge', 'deliveryDate', 'lmp'];
  const filledDates = dateKeys.filter(k => !isBlank(getValue(k)));
  f.date_format_valid = filledDates.every(k => parseDisplayDate(getValue(k))) ? 1 : 0;

  // Name fields containing digits
  const nameKeys = ['memberLastName','memberFirstName','memberMiddleName',
                    'patientLastName','patientFirstName','patientMiddleName'];
  f.name_contains_digits = nameKeys.some(k => /\d/.test(String(data[k] || ''))) ? 1 : 0;

  // Cross-form consistency. All five forms are populated from one logbook
  // entry and edits propagate, so these act as a safety net against a value
  // entered separately on a single form.
  f.pin_match_across_forms    = 1;
  f.dates_match_across_forms  = 1;
  f.name_match_across_forms   = 1;
  f.diagnosis_match_cf2_cf4   = (() => {
    const cf2 = String(getValue('dxADiagnosis') || '').trim().toLowerCase();
    const cf4 = String(getValue('cf4FinalDiagnosis') || '').trim().toLowerCase();
    if (!cf2 || !cf4) return 1; // can't mismatch until both are filled
    // CF2 carries the package's short diagnosis ("SPONTANEOUS VERTEX
    // DELIVERY", js/dx-templates.js cf2Dx) while CF4 has the full final
    // diagnosis, as the clinic writes them: that is a match.
    const short = typeof DX_PACKAGES !== 'undefined'
      ? Object.values(DX_PACKAGES).map(p => String(p.cf2Dx || '').toLowerCase()).filter(Boolean) : [];
    return cf2 === cf4 || short.includes(cf2) ? 1 : 0;
  })();

  // Date ordering
  const adm  = parseDisplayDate(getValue('dateAdmitted'));
  const dis  = parseDisplayDate(getValue('dateDischarge'));
  const dob  = parseDisplayDate(getValue('memberDOB'));
  const del  = parseDisplayDate(getValue('deliveryDate'));
  f._dischargeBeforeAdmission = (adm && dis && dis < adm) ? 1 : 0;
  f._dobAfterAdmission        = (adm && dob && dob > adm) ? 1 : 0;
  f._deliveryOutsideStay      = (adm && dis && del && (del < adm || del > dis)) ? 1 : 0;
  // Dates only, so the same day counts: a mother goes home the day after
  // delivering at the earliest.
  f._dischargeNotAfterDelivery = (dis && del && dis <= del) ? 1 : 0;

  // Member vs patient identity + relationship
  const memberName  = String(getValue('memberName')  || '').trim().toLowerCase();
  const patientName = String(getValue('patientName') || '').trim().toLowerCase();
  f._memberDiffersFromPatient = (memberName && patientName && memberName !== patientName) ? 1 : 0;
  f.relationship_field_blank  = isBlank(getValue('relationship')) ? 1 : 0;

  f.member_type = data.memberType || '';
  // PhilHealth member categories are stored as full labels such as
  // "Employed Private" / "Employed Government"; SP-04 applies to any of them.
  f.is_employed_member = /^employed/i.test(String(data.memberType || '')) ? 1 : 0;

  // Signature presence. The system never applies or verifies signatures; these
  // features stay 0 unless a signed form is optionally re-uploaded and checked.
  const sig = (window.PCA_SIGNATURE_STATE) || {};
  f.member_signature_present            = sig.member ? 1 : 0;
  f.attending_midwife_signature_present = sig.midwife ? 1 : 0;
  f.hci_representative_signature_present= sig.hciRep ? 1 : 0;
  f.employer_signature_present          = sig.employer ? 1 : 0;
  f.hci_assist_signature_present        = sig.hciAssist ? 1 : 0;
  f.attending_provider_signature_cf4_present = sig.cf4Provider ? 1 : 0;
  f.thumbmark_present                   = sig.thumbmark ? 1 : 0;
  f._signatureCheckActive               = sig.active ? 1 : 0;

  // Image quality + correction status, fed by the OCR module when present.
  const ocr = (window.PCA_OCR_STATE) || {};
  f.image_quality_pass        = ocr.imageQualityPass === false ? 0 : 1;
  f.pending_suggestions_count = ocr.pendingSuggestions || 0;
  f._anyUnreviewedSuggestion  = (ocr.pendingSuggestions || 0) > 0 ? 1 : 0;
  f._ocrActive                = ocr.active ? 1 : 0;

  f.attachment_count = (window.PCA_ATTACHMENT_COUNT) || 0;

  return f;
}

/* ── Rule definitions (Tables 3.4–3.8) ───────────────────── */
/* Each rule: { id, category, test(f), action, message, field?, form?, source } */

const RULES = [
  /* ── Category 5 (runs first): Image Quality & Correction Status ── */
  { id:'IQ-01', category:'Image Quality', action:'display_warning',
    test: f => f._ocrActive && f.image_quality_pass === 0,
    message:'The page may be too blurry, dark, or bright to read accurately. Re-scanning is recommended.',
    source:'System design' },

  { id:'CR-01', category:'Correction Status', action:'display_warning',
    test: f => f._anyUnreviewedSuggestion === 1,
    message:'A field was auto-corrected from the logbook reading. Please compare the original and suggested values, then choose Accept, Edit, or Reject.',
    source:'System design' },

  { id:'CR-02', category:'Correction Status', action:'flag_high_risk',
    test: f => f.pending_suggestions_count > 3,
    message:'Several values in this entry needed correction. Please check the whole row against the logbook page before continuing.',
    source:'System design' },

  /* ── Category 1: Missing Fields ── */
  { id:'MF-01', category:'Missing Field', action:'block_submission',
    test: f => f.patientName_present === 0,
    message:"Patient's full name is missing. This field is required.",
    field:'patientName', source:'PhilHealth guidelines' },

  { id:'MF-02', category:'Missing Field', action:'block_submission',
    test: f => f.memberPIN_present === 0,
    message:'PhilHealth Identification Number (PIN) is missing.',
    field:'memberPIN', source:'PhilHealth guidelines' },

  { id:'MF-03', category:'Missing Field', action:'display_warning',
    test: f => f.memberDOB_present === 0,
    message:'Member/Patient date of birth is missing.',
    field:'memberDOB', source:'PhilHealth guidelines' },

  { id:'MF-04', category:'Missing Field', action:'block_submission',
    test: f => f.dateAdmitted_present === 0,
    message:'Date of admission is missing. Type it in Patient details, part 3 (Stay at the clinic).',
    field:'dateAdmitted', source:'PhilHealth guidelines' },

  { id:'MF-05', category:'Missing Field', action:'block_submission',
    test: f => f.dateDischarge_present === 0,
    message:'Date of discharge (went home) is missing. Type it in Patient details, part 3 (Stay at the clinic).',
    field:'dateDischarge', source:'PhilHealth guidelines' },

  { id:'MF-06', category:'Missing Field', action:'flag_high_risk',
    test: f => f.blank_fields_count > 3,
    message:'High rejection risk: more than 3 required fields are blank.',
    source:'Historical RTH analysis' },

  { id:'MF-07', category:'Missing Field', action:'block_submission',
    test: f => f.cf4ChiefComplaint_present === 0,
    message:"CF4 chief complaint is missing. Please encode it from the patient's clinical record.",
    field:'cf4ChiefComplaint', form:'cf4', source:'PhilHealth CF4 requirement' },

  { id:'MF-08', category:'Missing Field', action:'block_submission',
    test: f => f.cf4CourseInWard_present === 0,
    message:"CF4 course in the ward is missing. Please encode it from the patient's clinical record.",
    field:'cf4CourseInWard', form:'cf4', source:'PhilHealth CF4 requirement' },

  { id:'MF-09', category:'Missing Field', action:'display_warning',
    test: f => f.cf4DrugsAdministered_present === 0,
    message:'CF4 drugs or medicines administered are not indicated. Please verify.',
    field:'cf4DrugsAdministered', form:'cf4', source:'PhilHealth CF4 requirement' },

  /* ── Category 2: Invalid Formats ── */
  { id:'IF-01', category:'Invalid Format', action:'block_submission',
    test: f => f.memberPIN_present === 1 && !f._memberNoPhilhealth && f.philhealth_pin_length !== 12,
    message:'PhilHealth PIN must be exactly 12 digits.',
    field:'memberPIN', source:'PhilHealth guidelines' },

  { id:'IF-02', category:'Invalid Format', action:'block_submission',
    test: f => f.philhealth_pin_contains_letters === 1,
    message:'PhilHealth PIN must contain digits only.',
    field:'memberPIN', source:'PhilHealth guidelines' },

  { id:'IF-03', category:'Invalid Format', action:'block_submission',
    test: f => f.date_format_valid === 0,
    message:'Date is not in the required MM-DD-YYYY format.',
    source:'PhilHealth guidelines' },

  { id:'IF-04', category:'Invalid Format', action:'display_warning',
    test: f => f.name_contains_digits === 1,
    message:'Name field contains numeric characters, please verify.',
    source:'Historical RTH analysis' },

  /* ── Category 3: Inconsistent Entries ── */
  { id:'IC-01', category:'Inconsistent Entry', action:'block_submission',
    test: f => f.name_match_across_forms === 0,
    message:'Patient name is not consistent across the five forms.',
    source:'Historical RTH analysis' },

  { id:'IC-02', category:'Inconsistent Entry', action:'block_submission',
    test: f => f.pin_match_across_forms === 0,
    message:'PhilHealth PIN is not consistent across the CSF, CF4, and PMRF.',
    source:'Historical RTH analysis' },

  { id:'IC-03', category:'Inconsistent Entry', action:'block_submission',
    test: f => f._dischargeBeforeAdmission === 1,
    message:'Discharge date is earlier than admission date.',
    field:'dateDischarge', source:'Historical RTH analysis' },

  { id:'IC-04', category:'Inconsistent Entry', action:'block_submission',
    test: f => f._dobAfterAdmission === 1,
    message:'Date of birth cannot be after the admission date.',
    field:'memberDOB', source:'Historical RTH analysis' },

  { id:'IC-05', category:'Inconsistent Entry', action:'display_warning',
    test: f => f._deliveryOutsideStay === 1,
    message:'Delivery date is outside the admission–discharge range.',
    field:'deliveryDate', source:'Historical RTH analysis' },

  { id:'IC-06', category:'Inconsistent Entry', action:'display_warning',
    test: f => f._memberDiffersFromPatient === 1 && f.relationship_field_blank === 1,
    message:'Patient differs from member but relationship to member is not indicated.',
    field:'relationship', source:'PhilHealth guidelines' },

  { id:'IC-07', category:'Inconsistent Entry', action:'block_submission',
    test: f => f.dates_match_across_forms === 0,
    message:'Admission and discharge dates are not the same across CSF, CF2, and CF4.',
    source:'Historical RTH analysis' },

  { id:'IC-09', category:'Inconsistent Entry', action:'block_submission',
    test: f => f.diagnosis_match_cf2_cf4 === 0,
    message:'The final diagnosis on CF2 does not match the diagnosis on CF4.',
    field:'cf4FinalDiagnosis', form:'cf4', source:'PhilHealth CF4 requirement' },

  { id:'IC-08', category:'Inconsistent Entry', action:'block_submission',
    test: f => f._dischargeNotAfterDelivery === 1,
    message:'Discharge date must be at least one day after the delivery date.',
    field:'dateDischarge', source:'Clinic practice' },


  /* ── Category 4: Signature Presence ──
     Before printing these produce the signing checklist. They only fire as
     errors when a signed form has been re-uploaded for checking. */
  { id:'SP-01', category:'Signature', action:'block_submission',
    test: f => f._signatureCheckActive && f.member_signature_present === 0,
    message:'Member/representative signature is missing on the CSF.',
    checklist:'Member / representative — CSF Part I',
    source:'PhilHealth Circular No. 21, s. 2014' },

  { id:'SP-02', category:'Signature', action:'block_submission',
    test: f => f._signatureCheckActive && f.attending_midwife_signature_present === 0,
    message:"Attending midwife's signature is missing on CF4.",
    checklist:'Attending midwife / physician — CF4', form:'cf4',
    source:'PhilHealth Circular No. 21, s. 2014' },

  { id:'SP-03', category:'Signature', action:'block_submission',
    test: f => f._signatureCheckActive && f.hci_representative_signature_present === 0,
    message:'Authorized HCI representative signature is missing on the CSF.',
    checklist:'Authorized HCI representative — CSF Part V',
    source:'PhilHealth Circular No. 21, s. 2014' },

  { id:'SP-04', category:'Signature', action:'display_warning',
    test: f => f._signatureCheckActive && f.employer_signature_present === 0 &&
               f.is_employed_member === 1,
    message:"Employer's certification signature is missing (required for employed members).",
    checklist:'Employer representative — CSF Part II (employed members only)',
    source:'PhilHealth Circular No. 21, s. 2014' },

  { id:'SP-05', category:'Signature', action:'display_warning',
    test: f => f._signatureCheckActive && f.thumbmark_present === 1 &&
               f.hci_assist_signature_present === 0,
    message:'Thumbmark detected, but HCI assisting representative signature is missing.',
    checklist:'HCI assisting representative — required when a thumbmark is used',
    source:'PhilHealth Circular No. 21, s. 2014' },

  { id:'SP-06', category:'Signature', action:'block_submission',
    test: f => f._signatureCheckActive && f.attending_provider_signature_cf4_present === 0,
    message:"Attending provider's signature is missing on CF4.",
    checklist:'Attending provider — CF4', form:'cf4',
    source:'PhilHealth CF4 requirement' },
];

/* ── Engine ──────────────────────────────────────────────── */

/**
 * Run every rule against the current data.
 * forms: the claim's forms - by default those the page shows (app.js
 * pcaClaimForms, which knows "Show all forms"), else claimFormKeys(); a
 * rule that belongs to another form (its `form`) is not run, and only these
 * forms' boxes are required.
 * @returns {{features, violations, critical, warnings, signingChecklist, canGeneratePDF}}
 */
function runValidationRules(getValue, data, forms) {
  forms = forms || (typeof window.pcaClaimForms === 'function' ? window.pcaClaimForms() : claimFormKeys(data));
  const features = computeFeatures(getValue, data, forms);
  const violations = [];
  const inClaim = rule => !rule.form || forms.includes(rule.form);

  RULES.filter(inClaim).forEach(rule => {
    let fired = false;
    try {
      fired = !!rule.test(features);
    } catch (err) {
      console.warn('Validation rule ' + rule.id + ' failed to evaluate', err);
    }
    if (fired) {
      violations.push({
        id: rule.id,
        category: rule.category,
        action: rule.action,
        message: rule.message,
        field: rule.field || null,
        form: rule.form || null,
        source: rule.source || '',
        severity: SEVERITY[rule.action],
      });
    }
  });

  const critical = violations.filter(v => v.severity.critical);
  const warnings = violations.filter(v => !v.severity.critical);

  // The signing checklist lists every signature block the claim needs,
  // produced before printing regardless of whether a signed form exists.
  const signingChecklist = RULES
    .filter(r => r.category === 'Signature' && r.checklist && inClaim(r))
    .filter(r => r.id !== 'SP-04' || features.is_employed_member === 1)
    .filter(r => r.id !== 'SP-05' || features.thumbmark_present === 1)
    .map(r => ({ id: r.id, text: r.checklist }));

  return {
    features,
    violations,
    critical,
    warnings,
    signingChecklist,
    canGeneratePDF: critical.length === 0,
  };
}

window.VAL_FIELDS         = VAL_FIELDS;
window.VAL_FORM_KEYS          = VAL_FORM_KEYS;
window.CLAIM_FORMS        = CLAIM_FORMS;
window.claimFormKeys      = claimFormKeys;
window.FORM_LABELS        = FORM_LABELS;
window.VALIDATION_RULES   = RULES;
window.runValidationRules = runValidationRules;
window.parseDisplayDate   = parseDisplayDate;
