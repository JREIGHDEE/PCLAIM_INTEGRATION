/* ═══════════════════════════════════════════════════════════
   PClaimAssist – The clinic's diagnosis wording, per package

   The clinic writes each PhilHealth package's diagnosis the same way
   every time, with only a few blanks changing (the clinic's template
   document - the underlined words are the blanks):

     NSDBF        PREGNANCY UTERINE FULL TERM 39 1/7 WEEKS AOG, CEPHALIC IN
                  LABOR GRAVIDA 4 PARA 3 (3003).                    O80.0
     99460/NCP    LIVE TERM BABY GIRL DELIVERED VIA NORMAL SPONTANEOUS
                  VAGINAL DELIVERY TO A GRAVIDA 3 PARA 2 MOTHER WEIGHING
                  3000 GRAMS WITH AN APGAR SCORE OF 8 & 9.          Z38.0
     FP001        FOR INSERTION OF IMPLANTABLE SUBDERMAL CONTRACEPTIVE
                                                                    Z30.1
     58300        MULTIPARITY G2 P2 (2002) FOR INTRAUTERINE DEVICE
                  INSERTION                                         Z30.1
     ANV/01/02/03 PREGNANCY UTERINE PRENATAL CARE 20 4/7 WEEKS AOG,
                  GRAVIDA 1 PARA 0 (0000)          Z34.0 primi / Z34.8 multi
     PPC01        POSTPARTUM VISITS AFTER DISCHARGE.                Z39.2

   plus, for a delivery, the CF4 course in the ward (one paragraph) and
   the usual medicines.

   On Patient details (Stay at the clinic) the package is picked
   automatically - a baby's claim is newborn care, a delivery is NSDBF -
   and can be changed. Its sentence is shown with each blank already
   filled from what the forms know (the weeks from the LMP, G, P, the
   baby's sex and weight...) and can be changed in place. Once no blank
   is left, the sentence and its codes go into the diagnosis boxes and
   keep following the blanks - until someone types something else in
   one of those boxes. Other wording already there (from the logbook) is
   only replaced with "Use this wording", after asking.

   Needs js/app.js (state, applyFormData, updateFormPreviews,
   resetFormData, formatTime12h, showToast) and, for a baby's claim,
   js/mother-baby.js (the mother's G, P and the birth weight).
═══════════════════════════════════════════════════════════ */

const DX_PACKAGES = {
  NSDBF: {
    code: 'NSDBF', title: 'NORMAL SPONTANEOUS DELIVERY', name: 'Normal delivery (mother)', icd: 'O80.0',
    text: 'PREGNANCY UTERINE FULL TERM {aog} WEEKS AOG, CEPHALIC IN LABOR GRAVIDA {g} PARA {p} ({tpal}).',
  },
  NCP: {
    code: '99460/NCP', title: 'NEWBORN CARE', name: 'Newborn care (baby)', icd: 'Z38.0', rvs: '99460', proc: 'NEWBORN CARE',
    text: 'LIVE TERM BABY {sex} DELIVERED VIA NORMAL SPONTANEOUS VAGINAL DELIVERY TO A GRAVIDA {g} ' +
          'PARA {p} MOTHER WEIGHING {weight} GRAMS WITH AN APGAR SCORE OF {apgar}.',
  },
  FP001: {
    code: 'FP001', title: 'FOR INSERTION OF IMPLANTABLE SUBDERMAL CONTRACEPTIVE', name: 'Implant insertion', icd: 'Z30.1',
    text: 'FOR INSERTION OF IMPLANTABLE SUBDERMAL CONTRACEPTIVE',
  },
  IUD: {
    code: '58300', title: 'INTRAUTERINE DEVICE INSERTION', name: 'IUD insertion', icd: 'Z30.1', rvs: '58300', proc: 'INTRAUTERINE DEVICE INSERTION',
    text: 'MULTIPARITY G{g} P{p} ({tpal}) FOR INTRAUTERINE DEVICE INSERTION',
  },
  ANV: {
    code: 'ANV/01/02/03', title: 'PRENATAL CARE', name: 'Prenatal care', icdNote: 'Z34.0 first pregnancy, Z34.8 later ones',
    icd: v => (v.g === '1' ? 'Z34.0' : 'Z34.8'),
    text: 'PREGNANCY UTERINE PRENATAL CARE {aog} WEEKS AOG, GRAVIDA {g} PARA {p} ({tpal})',
  },
  PPC01: {
    code: 'PPC01', title: 'POSTPARTUM VISITS AFTER DISCHARGE.', name: 'Postpartum visit', icd: 'Z39.2',
    text: 'POSTPARTUM VISITS AFTER DISCHARGE.',
  },
};

/* CF4 IV, for a delivery (NSDBF). */
const DX_COURSE_TEXT =
  'UPON ADMISSION PATIENT IS {cm} CM CERVIX DILATED WITH {bow} BAG OF WATER @ STATION {station} AND ' +
  '{effacement} EFFACEMENT, {aog} WEEKS AOG. AT AROUND {time} {ampm} SHE DELIVERED VIA NORMAL SPONTANEOUS ' +
  'VAGINAL DELIVERY TO A LIVE TERM BABY {sex} IN CEPHALIC PRESENTATION WEIGHING {grams} GMS. WITH AN APGAR ' +
  'SCORE OF {apgar}. THE BABY IS APPROPRIATE TO {hisher} GESTATIONAL AGE WITH MATERNAL OUTCOME OF G{g} P{p} ' +
  '({tpal}). NO UNTOWARD EVENT NOTED DURING ADMISSION, LABOR, DELIVERY AND IMMEDIATE POSTPARTUM.';

/* CF4 V, for a delivery (NSDBF): [generic name, quantity, dosage / route,
   total cost]. The form's middle column has the quantity over the dosage / route. */
const DX_DRUG_FIELDS = ['Name', 'Qty', 'Dose', 'Cost'];
const DX_DELIVERY_DRUGS = [
  ['OXYTOCIN / NONE / NONE', '1.00 PC/S', 'FREQUENCY: 1 / ROUTE: IM', '500'],
  ['MEFENAMIC ACID / NONE / NONE', '10.00 PC/S', 'FREQUENCY: EVERY 6 HOURS / ROUTE: ORAL', '500'],
  ['LIDOCAINE HYDROCHLORIDE / NONE / NONE', '1.00 PC/S', 'FREQUENCY: 1 / ROUTE: IM', '500'],
];

/* The blanks. `def` is the clinic's usual value, used when the forms
   don't know better; every blank can be changed. */
const DX_VARS = {
  aog:        { label: 'Weeks AOG, e.g. 39 1/7', w: '4.8em' },
  g:          { label: 'Gravida', w: '2.4em', digits: 2 },
  p:          { label: 'Para', w: '2.4em', digits: 2 },
  tpal:       { label: 'Term, preterm, abortion, living - 4 digits', w: '3.8em', digits: 4 },
  sex:        { label: 'Baby boy or girl', options: ['BOY', 'GIRL'] },
  weight:     { label: 'Weight in grams', w: '4.4em' },
  grams:      { label: 'Weight in grams', w: '4.4em' },
  apgar:      { label: 'APGAR score', w: '4.2em', def: '8 & 9' },
  cm:         { label: 'Cervix dilatation in cm', w: '2.6em', def: '10' },
  bow:        { label: 'Bag of water', options: ['INTACT', 'RUPTURED'], def: 'INTACT' },
  station:    { label: 'Station', w: '3.4em', def: '(-)2' },
  effacement: { label: 'Effacement', w: '3.6em', def: '100%' },
  time:       { label: 'Time of delivery, hh:mm', w: '3.8em' },
  ampm:       { label: 'AM or PM', options: ['AM', 'PM'] },
  hisher:     { label: 'His or her', options: ['HIS', 'HER'] },
};

const DX_TARGET_LABELS = {
  admissionDx: 'Admission Diagnosis', dischargeDx: 'Final Diagnosis',
  dxADiagnosis: 'CF2 diagnosis', cf4FinalDiagnosis: 'CF4 discharge diagnosis',
  dxAIcd10: 'CF2 ICD-10', cf4IcdCode: 'CF4 1st case rate code',
  cf4RvsCode: 'CF4 2nd case rate code (RVS)', dxARvsI: 'CF2 RVS', dxAProcI: 'CF2 procedure',
  csfFirstCaseRate: 'CSF 1st case rate', csfSecondCaseRate: 'CSF 2nd case rate',
};
// The form's three printed drug rows (CF4 V).
const DX_DRUG_KEYS = ['1', '2', '3'];

/* ── What the forms already know ─────────────────────────── */

function dxBlank(v) { return v === undefined || v === null || String(v).trim() === ''; }
function dxPick(...values) { const v = values.find(v => !dxBlank(v)); return v === undefined ? '' : String(v).trim(); }

function dxMotherFacts() {
  return (typeof mb !== 'undefined' && mb.fromMother && mb.fromMother.mother_facts) || {};
}

function dxIsBaby() {
  const d = state.data;
  if (typeof mb !== 'undefined' && mb.family && mb.family.role) return mb.family.role === 'baby';
  const born = Date.parse(d.patientDOB), seen = Date.parse(d.dateAdmitted || d.deliveryDate);
  return born && seen && seen >= born && (seen - born) < 365 * 86400000;
}

/* "39 1/7" from the LMP to a date. */
function dxAog(lmp, end) {
  if (!lmp || !end) return '';
  const days = Math.round((Date.parse(end) - Date.parse(lmp)) / 86400000);
  if (!(days >= 4 * 7 && days <= 45 * 7)) return '';
  return Math.floor(days / 7) + (days % 7 ? ` ${days % 7}/7` : '');
}

function dxSexWord(sex) {
  return { Male: 'BOY', Female: 'GIRL', MALE: 'BOY', FEMALE: 'GIRL' }[String(sex || '').trim()] || '';
}

function dxAutoValue(name, pkg, values) {
  const d = state.data;
  const baby = pkg === 'NCP';
  // A baby's claim names its mother's G, P and the birth weight.
  const ob = baby ? { ...dxMotherFacts(), ...pickFilled(d, ['birthWeight']) } : d;
  switch (name) {
    case 'aog': return dxAog(d.lmp, d.dateAdmitted || d.deliveryDate);
    case 'g': return dxPick(ob.gravida, d.gravida);
    case 'p': return dxPick(ob.para, d.para);
    case 'tpal': {
      const tpal = src => [src.obTerm, src.obPreterm, src.obAbortion, src.obLiving];
      const parts = tpal(ob).every(v => !dxBlank(v)) ? tpal(ob) : tpal(d);
      return parts.every(v => !dxBlank(v)) ? parts.join('') : '';
    }
    case 'sex': return dxSexWord(baby ? dxPick(d.patientSex, d.babySex, dxMotherFacts().babySex) : d.babySex);
    case 'weight': return dxPick(ob.birthWeight, d.birthWeight);
    case 'grams': {
      const g = dxPick(d.birthWeight).replace(/\D/g, '');
      return g ? Number(g).toLocaleString('en-US') : '';
    }
    case 'time': return d.deliveryTime ? formatTime12h(d.deliveryTime).replace(/\s*(AM|PM)$/, '') : '';
    case 'ampm': return d.deliveryTime ? formatTime12h(d.deliveryTime).slice(-2) : (DX_VARS.ampm.def || '');
    case 'hisher': return { BOY: 'HIS', GIRL: 'HER' }[values.sex] || '';
    default: return DX_VARS[name].def || '';
  }
}

function pickFilled(obj, keys) {
  const out = {};
  keys.forEach(k => { if (!dxBlank(obj[k])) out[k] = obj[k]; });
  return out;
}

/* The package the patient's diagnosis is for: picked by staff, else
   worked out from the patient. */
function dxGuessPackage() {
  const d = state.data;
  const dx = `${d.admissionDx || ''} ${d.dischargeDx || ''}`.toUpperCase();
  if (dxIsBaby() || /\bMOTHER WEIGHING\b|\bNEWBORN\b|\bWELL\s*BABY\b/.test(dx)) return 'NCP';
  if (/\bPRE-?NATAL\b/.test(dx)) return 'ANV';
  if (/\bPOST\s*-?PARTUM\b/.test(dx) && !/DELIVER/.test(dx)) return 'PPC01';
  if (/\bINTRAUTERINE\b|\bIUD\b/.test(dx)) return 'IUD';
  if (/\bIMPLANT/.test(dx)) return 'FP001';
  return 'NSDBF';
}

function dxCurrentPackage() {
  return DX_PACKAGES[state.data.dxPackage] ? state.data.dxPackage : dxGuessPackage();
}

/* ── One sentence with blanks, put into its boxes ────────── */

let dxApplying = false;

class DxSentence {
  /* host: element to fill. opts.template(): the sentence with {blanks};
     opts.targets(text, values): {form key: value} it goes into;
     opts.pkg(): the package (for the automatic values). */
  constructor(host, opts) {
    this.host = host;
    this.opts = opts;
    this.touched = {};     // blank -> what staff typed in it
    this.following = {};   // form key -> the value last put there
    this.shownFor = null;
    this.box = document.createElement('div');
    this.box.className = 'dx-template';
    host.appendChild(this.box);
    this.box.addEventListener('input', e => this.onEdit(e));
    this.box.addEventListener('change', e => this.onEdit(e));
    this.box.addEventListener('click', e => this.onClick(e));
  }

  reset() { this.touched = {}; this.following = {}; this.shownFor = null; this.takenOut = false; this.wasAuto = false; }

  onEdit(e) {
    const name = e.target.dataset && e.target.dataset.dxVar;
    if (!name) return;
    const spec = DX_VARS[name];
    if (spec.digits) e.target.value = e.target.value.replace(/\D/g, '').slice(0, spec.digits);
    this.touched[name] = e.target.value.toUpperCase();
    this.refresh();
  }

  onClick(e) {
    if (e.target.closest('[data-dx-out]')) this.takeOut();
    else if (e.target.closest('[data-dx-use]')) this.useWording(false);
    else if (e.target.closest('[data-dx-replace]')) this.useWording(true);
    else if (e.target.closest('[data-dx-keep]')) this.box.querySelector('.dx-confirm').hidden = true;
    else if (e.target.closest('[data-dx-auto]')) { this.touched = {}; this.refresh(); }
  }

  build(template) {
    const blank = name => {
      const spec = DX_VARS[name];
      if (spec.options) {
        return `<select data-dx-var="${name}" aria-label="${spec.label}"><option value=""></option>` +
          spec.options.map(o => `<option>${o}</option>`).join('') + '</select>';
      }
      return `<input type="text" data-dx-var="${name}" aria-label="${spec.label}" title="${spec.label}"` +
        ` style="width:${spec.w}"${spec.digits ? ' inputmode="numeric"' : ''}>`;
    };
    const sentence = template.split(/(\{\w+\})/).map(part => {
      const m = part.match(/^\{(\w+)\}$/);
      return m ? blank(m[1]) : dxEscape(part);
    }).join('');
    this.box.querySelector('.dx-sentence').innerHTML = sentence;
    this.shownFor = template;
  }

  values(template) {
    const values = {};
    [...template.matchAll(/\{(\w+)\}/g)].forEach(([, name]) => {
      values[name] = name in this.touched ? this.touched[name] : dxAutoValue(name, this.opts.pkg(), values);
    });
    // "his/her" follows "boy/girl" unless changed by hand.
    if ('hisher' in values && !('hisher' in this.touched)) values.hisher = dxAutoValue('hisher', null, values);
    return values;
  }

  text(template, values) {
    return template.replace(/\{(\w+)\}/g, (_, name) => values[name] || '').toUpperCase();
  }

  /* Put in by itself? opts.auto() (the package), unless taken out by hand. */
  isAuto() {
    return !this.takenOut && (!this.opts.auto || this.opts.auto());
  }

  /* Empty the boxes it put in that are still exactly as put in. */
  clearFollowing() {
    const put = {};
    Object.entries(this.following).forEach(([key, value]) => {
      if (String(state.data[key] ?? '') === String(value) && value !== '') put[key] = '';
    });
    this.following = {};
    if (Object.keys(put).length && !dxApplying) {
      dxApplying = true;
      try { applyFormData(put); } finally { dxApplying = false; }
      if (window.PCACourseRows) window.PCACourseRows.refresh();
    }
  }

  /* Draw the blanks, then put the sentence into its boxes where they
     still follow it. */
  refresh() {
    const template = this.opts.template();
    const auto = this.isAuto();
    // Automatic for the last package but not this one: what it put in
    // by itself comes out again.
    if (this.wasAuto && !auto && !this.takenOut) this.clearFollowing();
    this.wasAuto = auto;
    if (this.shownFor !== template) this.build(template);
    const values = this.values(template);
    const missing = [];
    this.box.querySelectorAll('[data-dx-var]').forEach(el => {
      const name = el.dataset.dxVar;
      if (document.activeElement !== el) el.value = values[name] || '';
      const empty = dxBlank(values[name]);
      el.classList.toggle('dx-empty', empty);
      if (empty) missing.push(DX_VARS[name].label);
    });
    const text = this.text(template, values);
    this.box.querySelector('.dx-preview').textContent = text;
    const targets = this.opts.targets(text, values);
    this.lastTargets = targets;
    this.complete = missing.length === 0;

    // A box already holding exactly this follows it from now on.
    Object.entries(targets).forEach(([key, value]) => {
      if (String(state.data[key] ?? '') === String(value)) this.following[key] = value;
    });
    if (this.complete && auto) this.applyFollowing(targets);
    this.renderStatus(targets, missing, auto);
  }

  isFollowing(key) {
    const now = String(state.data[key] ?? '').trim();
    // An admission diagnosis that is only the reason for admission copied
    // over (app.js DERIVED_FIELDS) gives way to the wording.
    if (key === 'admissionDx' && now !== '' && now === String(state.data.chiefComplaint ?? '').trim()) return true;
    // A package's short title put in by picking its code (setupCodeOptions).
    if (now !== '' && Object.values(DX_PACKAGES).some(p => p.title === now)) return true;
    return now === '' || (key in this.following && now === String(this.following[key]));
  }

  applyFollowing(targets) {
    const put = {};
    Object.entries(targets).forEach(([key, value]) => {
      if (this.isFollowing(key) && String(state.data[key] ?? '') !== String(value)) put[key] = value;
    });
    if (!Object.keys(put).length || dxApplying) return;
    Object.assign(this.following, put);
    dxApplying = true;
    try { applyFormData(put); } finally { dxApplying = false; }
    if (window.PCACourseRows) window.PCACourseRows.refresh();
  }

  renderStatus(targets, missing, auto) {
    const status = this.box.querySelector('.dx-status');
    const useBtn = this.box.querySelector('[data-dx-use]');
    const outBtn = this.box.querySelector('[data-dx-out]');
    const keys = Object.keys(targets).filter(k => targets[k] !== '' || !dxBlank(state.data[k]));
    const others = keys.filter(k => !this.isFollowing(k));
    const names = list => [...new Set(list.map(k => this.opts.label(k)))].join(', ');
    const differs = keys.some(k => String(state.data[k] ?? '') !== String(targets[k]));
    // In the boxes now: those holding exactly what it puts there.
    const inBoxes = keys.some(k => targets[k] !== '' && String(state.data[k] ?? '') === String(targets[k]));
    if (this.opts.outLabel) {
      useBtn.hidden = !(this.complete && differs);
      outBtn.hidden = !inBoxes;
    } else {
      useBtn.hidden = !(this.complete && others.length);
    }
    if (missing.length) {
      status.innerHTML = `<span class="text-danger">Fill in the red blank${missing.length === 1 ? '' : 's'}: ` +
        `${dxEscape(missing.join(', '))}.</span> It goes in once complete.`;
    } else if (!auto && !inBoxes) {
      status.innerHTML = `<i class="bi bi-info-circle me-1"></i>${dxEscape(this.opts.notAutoNote || 'Not put in by itself.')}`;
    } else if (!auto) {
      status.innerHTML = `<i class="bi bi-check-circle-fill text-success me-1"></i>In ${dxEscape(names(keys))}.`;
    } else if (others.length) {
      status.innerHTML = `<i class="bi bi-info-circle me-1"></i>Put in automatically: ${dxEscape(names(keys.filter(k => !others.includes(k))) || 'none')}. ` +
        `<strong>${dxEscape(names(others))}</strong> already ${others.length === 1 ? 'has' : 'have'} other wording, kept as it is.`;
    } else {
      status.innerHTML = `<i class="bi bi-check-circle-fill text-success me-1"></i>Put in automatically: ${dxEscape(names(keys))}. ` +
        'Change a blank above and they follow; type in those boxes to word it differently.';
    }
  }

  /* "Take it out": empties the boxes holding exactly this wording, and it
     stays out (not put in by itself again) until put back. */
  takeOut() {
    const put = {};
    Object.entries(this.lastTargets || {}).forEach(([key, value]) => {
      if (value !== '' && String(state.data[key] ?? '') === String(value)) put[key] = '';
    });
    this.following = {};
    this.takenOut = true;
    dxApplying = true;
    try { applyFormData(put); } finally { dxApplying = false; }
    if (window.PCACourseRows) window.PCACourseRows.refresh();
    this.refresh();
  }

  useWording(confirmed) {
    if (!this.complete) return;
    const targets = this.lastTargets;
    const replaced = Object.keys(targets).filter(k => !this.isFollowing(k) && String(state.data[k]) !== String(targets[k]));
    const ask = this.box.querySelector('.dx-confirm');
    if (replaced.length && !confirmed) {
      ask.querySelector('.dx-confirm-old').innerHTML = replaced.map(k =>
        `<div><strong>${dxEscape(this.opts.label(k))}:</strong> ${dxEscape(state.data[k])}</div>`).join('');
      ask.hidden = false;
      ask.querySelector('[data-dx-replace]').focus();
      return;
    }
    ask.hidden = true;
    this.takenOut = false;
    // Every box follows the wording from now on.
    this.following = Object.fromEntries(Object.keys(targets).map(k => [k, state.data[k] ?? '']));
    this.applyFollowing(targets);
    this.refresh();
    showToast('Wording put in', this.opts.putNote || 'The clinic\'s wording is now in the diagnosis boxes.', 'success');
  }
}

function dxEscape(text) {
  return String(text ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function dxShell(title, extra, buttons) {
  const b = buttons || {};
  return `
    <div class="dx-head">
      <div class="dx-title"><i class="bi bi-card-text me-2"></i>${title}</div>
      ${extra || ''}
    </div>
    <div class="dx-sentence"></div>
    <div class="dx-preview" aria-live="polite"></div>
    <div class="dx-status small"></div>
    <div class="dx-actions">
      <button type="button" class="btn btn-primary btn-sm" data-dx-use hidden><i class="bi bi-plus-lg me-1"></i>${b.use || 'Use this wording'}</button>
      ${b.out ? `<button type="button" class="btn btn-outline-secondary btn-sm" data-dx-out hidden><i class="bi bi-dash-lg me-1"></i>${b.out}</button>` : ''}
      <button type="button" class="btn btn-link btn-sm" data-dx-auto>Fill the blanks again from the forms</button>
    </div>
    <div class="dx-confirm" role="alertdialog" hidden>
      <div class="dx-confirm-title"><i class="bi bi-exclamation-triangle-fill me-2"></i>Replace what is there?</div>
      <div class="dx-confirm-old"></div>
      <div class="dx-actions">
        <button type="button" class="btn btn-warning btn-sm" data-dx-replace>Replace it</button>
        <button type="button" class="btn btn-outline-secondary btn-sm" data-dx-keep>Keep what is there</button>
      </div>
    </div>`;
}

/* ── The diagnosis (Patient details → Stay at the clinic) ── */

const dxDiagnosis = (function setupDiagnosisWording() {
  const host = document.getElementById('admissionDxTemplate');
  if (!host) return null;
  const options = Object.entries(DX_PACKAGES).map(([key, p]) =>
    `<option value="${key}">${p.code} — ${p.name} · ${typeof p.icd === 'function' ? 'Z34.0 / Z34.8' : p.icd}</option>`).join('');
  const sentence = new DxSentence(host, {
    template: () => DX_PACKAGES[dxCurrentPackage()].text,
    pkg: dxCurrentPackage,
    label: key => DX_TARGET_LABELS[key] || key,
    targets: (text, values) => {
      const p = DX_PACKAGES[dxCurrentPackage()];
      const icd = typeof p.icd === 'function' ? p.icd(values) : p.icd;
      return {
        admissionDx: text, dischargeDx: text, dxADiagnosis: text, cf4FinalDiagnosis: text,
        dxAIcd10: icd, cf4IcdCode: icd, csfFirstCaseRate: icd,
        cf4RvsCode: p.rvs || '', csfSecondCaseRate: p.rvs || '', dxARvsI: p.rvs || '', dxAProcI: p.proc || '',
      };
    },
  });
  sentence.box.insertAdjacentHTML('afterbegin', dxShell('The clinic\'s wording',
    `<label class="dx-package"><span>Package</span>
       <select class="form-select form-select-sm" data-dx-package>${options}</select></label>`));
  const select = sentence.box.querySelector('[data-dx-package]');
  select.addEventListener('change', () => {
    state.data.dxPackage = select.value;
    // The new package's codes and wording replace the old ones where they
    // were put in automatically.
    sentence.touched = {};
    updateFormPreviews();
  });
  return {
    refresh() {
      select.value = dxCurrentPackage();
      const auto = !state.data.dxPackage;
      sentence.box.querySelector('.dx-package span').textContent = auto ? 'Package (picked automatically)' : 'Package';
      sentence.refresh();
    },
    reset() { sentence.reset(); },
  };
})();

/* ── CF4 IV. Course in the ward (a delivery) ─────────────── */

const dxCourse = (function setupCourseWording() {
  const host = document.getElementById('courseWardTemplate');
  if (!host) return null;
  // Shown for every package, so it can always be put in with its button;
  // put in by itself only for a delivery (NSDBF).
  const sentence = new DxSentence(host, {
    template: () => DX_COURSE_TEXT,
    auto: () => dxCurrentPackage() === 'NSDBF',
    outLabel: true,
    notAutoNote: 'Put in by itself only for a normal delivery (NSDBF). Press "Put it in the course in the ward" to use it anyway.',
    putNote: 'The paragraph is now in the first box of the course in the ward below.',
    pkg: dxCurrentPackage,
    label: key => (key === 'cf4CourseDate1' ? 'the first date' : 'the first box'),
    // The whole paragraph goes in the form's first (big) box, dated the day
    // of admission; the print wraps it onto that box's lines.
    targets: text => ({ cf4CourseDate1: state.data.dateAdmitted || '', cf4CourseOrder1: text }),
  });
  sentence.box.insertAdjacentHTML('afterbegin', dxShell('The clinic\'s course in the ward (normal delivery)', '',
    { use: 'Put it in the course in the ward', out: 'Take it out' }));
  return { refresh: () => sentence.refresh(), reset: () => sentence.reset() };
})();

/* ── CF4 V. The usual delivery medicines ─────────────────── */

const dxDrugs = (function setupDeliveryDrugs() {
  const host = document.getElementById('drugsTemplate');
  if (!host) return null;
  const box = document.createElement('div');
  box.className = 'dx-template';
  box.innerHTML = `
    <div class="dx-head"><div class="dx-title"><i class="bi bi-capsule me-2"></i>The usual delivery medicines</div></div>
    <table class="dx-drugs"><thead><tr><th>Generic name</th><th>Quantity</th><th>Dosage / route</th><th>Total cost</th></tr></thead>
      <tbody>${DX_DELIVERY_DRUGS.map(r => `<tr>${r.map(c => `<td>${dxEscape(c) || '—'}</td>`).join('')}</tr>`).join('')}</tbody></table>
    <div class="dx-status small"></div>
    <div class="dx-actions">
      <button type="button" class="btn btn-primary btn-sm" data-dx-add-drugs><i class="bi bi-plus-lg me-1"></i>Add them to the list</button>
      <button type="button" class="btn btn-outline-secondary btn-sm" data-dx-remove-drugs><i class="bi bi-dash-lg me-1"></i>Take them out of the list</button>
    </div>`;
  host.appendChild(box);

  const names = () => DX_DRUG_KEYS.map(k => state.data[`cf4DrugName${k}`]).filter(v => !dxBlank(v));
  // Put in by themselves (for a delivery) rather than with the button:
  // only then do they come out again when the package changes.
  let autoPut = false;
  function add(auto) {
    // Into the first free lines, so nothing typed is replaced.
    const free = DX_DRUG_KEYS.filter(k => DX_DRUG_FIELDS.every(f => dxBlank(state.data[`cf4Drug${f}${k}`])));
    const put = { dxDrugsAdded: true };
    let next = 0;
    DX_DELIVERY_DRUGS.forEach(row => {
      if (names().includes(row[0]) || next >= free.length) return;
      const k = free[next++];
      DX_DRUG_FIELDS.forEach((f, i) => { put[`cf4Drug${f}${k}`] = row[i]; });
    });
    autoPut = !!auto;
    dxApplying = true;
    try { applyFormData(put); } finally { dxApplying = false; }
    if (window.PCACourseRows) window.PCACourseRows.refresh();
    if (!auto) dxRefreshAll();
  }
  box.querySelector('[data-dx-add-drugs]').addEventListener('click', () => add(false));
  // Taken out by hand: they stay out (dxDrugsAdded stays true, so they are
  // not put in again automatically).
  box.querySelector('[data-dx-remove-drugs]').addEventListener('click', () => takeOut(true));

  // The usual medicines that are still exactly as put in come out: by
  // hand, or because it is not a delivery after all.
  function takeOut(byHand) {
    const put = { dxDrugsAdded: !!byHand };
    autoPut = false;
    DX_DRUG_KEYS.forEach(k => {
      const row = DX_DELIVERY_DRUGS.find(r => r[0] === state.data[`cf4DrugName${k}`]);
      if (row && DX_DRUG_FIELDS.every((f, i) => row[i] === String(state.data[`cf4Drug${f}${k}`] ?? ''))) {
        DX_DRUG_FIELDS.forEach(f => { put[`cf4Drug${f}${k}`] = ''; });
      }
    });
    dxApplying = true;
    try { applyFormData(put); } finally { dxApplying = false; }
    if (window.PCACourseRows) window.PCACourseRows.refresh();
    if (byHand) dxRefreshAll();
  }

  let lastPackage = null;

  return {
    refresh() {
      // Shown for every package, so they can always be added by hand; put
      // in by themselves only for a delivery.
      const pkg = dxCurrentPackage();
      const delivery = pkg === 'NSDBF';
      const leftDelivery = lastPackage === 'NSDBF' && !delivery;
      lastPackage = pkg;
      box.querySelector('.dx-title').lastChild.textContent = delivery
        ? 'The usual delivery medicines' : 'The usual delivery medicines (for a normal delivery, NSDBF)';
      if (!delivery) {
        // Switched away from a delivery: what it put in by itself comes out.
        if (leftDelivery && autoPut && !dxApplying) takeOut(false);
      }
      // Put in once for a delivery, while the list is still empty - a
      // delivery the forms know of, not only the package guessed for a
      // patient with nothing filled in yet.
      const delivered = delivery && (state.data.dxPackage === 'NSDBF' || !dxBlank(state.data.deliveryDate));
      if (delivered && !state.data.dxDrugsAdded && !names().length && !dxApplying) add(true);
      const inList = DX_DELIVERY_DRUGS.filter(r => names().includes(r[0])).length;
      const all = inList === DX_DELIVERY_DRUGS.length;
      box.querySelector('.dx-status').innerHTML = all
        ? '<i class="bi bi-check-circle-fill text-success me-1"></i>All 3 are in the list below. Change the quantity or cost there.'
        : `${inList} of ${DX_DELIVERY_DRUGS.length} are in the list below.`;
      box.querySelector('[data-dx-add-drugs]').hidden = all;
      box.querySelector('[data-dx-remove-drugs]').hidden = inList === 0;
    },
  };
})();

/* ── Codes to choose from on the ICD-10 and RVS boxes ────── */

/* A package's wording with its blanks filled from the forms, or its short
   title while a blank is still unknown. */
function dxPackageWording(pkg) {
  const p = DX_PACKAGES[pkg];
  const values = {};
  let complete = true;
  [...p.text.matchAll(/\{(\w+)\}/g)].forEach(([, name]) => {
    values[name] = dxAutoValue(name, pkg, values);
    if (dxBlank(values[name])) complete = false;
  });
  return complete ? p.text.replace(/\{(\w+)\}/g, (_, name) => values[name]).toUpperCase() : p.title;
}

/* One row per package (two packages can share a code). */
const DX_ICD_OPTIONS = Object.entries(DX_PACKAGES).flatMap(([pkg, p]) => (typeof p.icd === 'function'
  ? [{ code: 'Z34.0', pkg, label: `${p.name}, first pregnancy` }, { code: 'Z34.8', pkg, label: `${p.name}, later pregnancy` }]
  : [{ code: p.icd, pkg, label: p.name }]));
const DX_RVS_OPTIONS = Object.entries(DX_PACKAGES).filter(([, p]) => p.rvs)
  .map(([pkg, p]) => ({ code: p.rvs, pkg, label: p.name, proc: p.proc }));

/* What a picked code fills beside it, while that box is empty or still
   holds what an earlier pick put there: the diagnosis for an ICD-10 code,
   the related procedure for an RVS code (CF2 Diagnosis A/B). */
const DX_NAME_BOX = {
  dxAIcd10: 'dxADiagnosis', dxBIcd10: 'dxBDiagnosis',
  dxARvsI: 'dxAProcI', dxARvsII: 'dxAProcII', dxARvsIII: 'dxAProcIII',
  dxBRvsI: 'dxBProcI', dxBRvsII: 'dxBProcII', dxBRvsIII: 'dxBProcIII',
};
const dxPickedNames = {};   // name box -> what a pick put there

function dxPickCode(key, option) {
  const put = { [key]: option.code };
  const nameKey = DX_NAME_BOX[key];
  if (nameKey) {
    const name = option.proc || dxPackageWording(option.pkg);
    const now = String(state.data[nameKey] ?? '').trim();
    if (!now || now === dxPickedNames[nameKey]) {
      put[nameKey] = name;
      dxPickedNames[nameKey] = name;
      // The final diagnosis boxes that copy Diagnosis A (CSF, CF4) get it
      // too while they are empty.
      (MIRRORED_FIELDS[nameKey] || []).forEach(k => { if (dxBlank(state.data[k])) put[k] = name; });
    }
  }
  // Diagnosis A's code is the claim's package: the clinic's wording follows it.
  if (key === 'dxAIcd10') state.data.dxPackage = option.pkg;
  applyFormData(put);
}

/* A dropdown under a code box: opens on click or typing, filters as you
   type, arrow keys and Enter to choose, Esc to close. */
const dxCodeMenu = document.createElement('div');
dxCodeMenu.className = 'dropdown-menu dx-code-menu';
dxCodeMenu.setAttribute('role', 'listbox');
document.body.appendChild(dxCodeMenu);

function dxPlaceCodeMenu() {
  if (!dxCodeMenu.owner) return;
  const r = dxCodeMenu.owner.getBoundingClientRect();
  dxCodeMenu.style.left = `${r.left}px`;
  dxCodeMenu.style.top = `${r.bottom + 2}px`;
  dxCodeMenu.style.minWidth = `${Math.max(r.width, 320)}px`;
}

function dxAttachCodeMenu(input, options) {
  const key = input.dataset.autofill;
  input.setAttribute('autocomplete', 'off');
  input.removeAttribute('list');
  let shown = [];
  let active = -1;
  // Clicked: every code, to pick from or change to. Typed: those that match.
  function render(typed) {
    const q = typed ? input.value.trim().toUpperCase() : '';
    shown = options.filter(o => !q || o.code.toUpperCase().includes(q) || o.label.toUpperCase().includes(q) ||
                                (o.proc || '').includes(q));
    if (!shown.length) shown = options;
    active = Math.min(active, shown.length - 1);
    dxCodeMenu.innerHTML = shown.map((o, i) => `
      <button type="button" class="dropdown-item${i === active ? ' active' : ''}" role="option" data-i="${i}">
        <span class="dx-code">${dxEscape(o.code)}</span>
        <span class="dx-code-name">${dxEscape(o.proc || o.label)}</span>
        <span class="dx-code-pkg">${dxEscape(DX_PACKAGES[o.pkg].code)}</span>
      </button>`).join('');
    dxCodeMenu.owner = input;
    dxCodeMenu.choose = i => { const o = shown[i]; if (o) { dxPickCode(key, o); close(); } };
    dxPlaceCodeMenu();
    dxCodeMenu.classList.add('show');
  }
  const close = () => { if (dxCodeMenu.owner === input) dxCodeMenu.classList.remove('show'); };
  if (input.readOnly || input.disabled) return;
  let filtering = false;
  input.addEventListener('focus', () => { active = -1; filtering = false; render(false); });
  input.addEventListener('click', () => { filtering = false; render(false); });
  input.addEventListener('input', () => { active = -1; filtering = true; render(true); });
  input.addEventListener('blur', () => setTimeout(close, 150));
  input.addEventListener('keydown', e => {
    if (!dxCodeMenu.classList.contains('show') || dxCodeMenu.owner !== input) return;
    if (e.key === 'ArrowDown') { active = (active + 1) % shown.length; render(filtering); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { active = (active - 1 + shown.length) % shown.length; render(filtering); e.preventDefault(); }
    else if (e.key === 'Enter' && active >= 0) { dxCodeMenu.choose(active); e.preventDefault(); }
    else if (e.key === 'Escape') close();
  });
}
// One listener for the shared menu: mousedown, so the pick lands before
// the box loses focus and the menu closes.
dxCodeMenu.addEventListener('mousedown', e => {
  const item = e.target.closest('[data-i]');
  if (!item || !dxCodeMenu.choose) return;
  e.preventDefault();
  dxCodeMenu.choose(Number(item.dataset.i));
});
window.addEventListener('scroll', () => {
  if (dxCodeMenu.classList.contains('show')) dxPlaceCodeMenu();
}, true);
window.addEventListener('resize', () => {
  if (dxCodeMenu.classList.contains('show')) dxPlaceCodeMenu();
});

document.querySelectorAll('[data-autofill="dxAIcd10"], [data-autofill="dxBIcd10"], [data-autofill="cf4IcdCode"], [data-autofill="csfFirstCaseRate"]')
  .forEach(el => dxAttachCodeMenu(el, DX_ICD_OPTIONS));
document.querySelectorAll('[data-autofill^="dxARvs"], [data-autofill^="dxBRvs"], [data-autofill="cf4RvsCode"], [data-autofill="csfSecondCaseRate"]')
  .forEach(el => dxAttachCodeMenu(el, DX_RVS_OPTIONS));

/* ── CF4 2.a: "No known medical illness" ──────────────────── */

/* A fixed phrase put into a box, or taken out, in the same card as the
   other wordings. Never replaces what someone typed: without `append` it is
   offered only while the box is empty; with it, it is added to the end of
   what is there. "Take it out" removes only the phrase. */
const DX_PHRASE_SEP = ', ';
function dxPhraseCard(section, key, phrase, title, append) {
  const field = document.querySelector(`#section-${section} [data-autofill="${key}"]`);
  if (!field) return null;
  const card = document.createElement('div');
  card.className = 'dx-template';
  card.innerHTML = `
    <div class="dx-head"><div class="dx-title"><i class="bi bi-card-text me-2"></i>${dxEscape(title)}</div></div>
    <div class="dx-preview">${dxEscape(phrase)}</div>
    <div class="dx-status small"></div>
    <div class="dx-actions">
      <button type="button" class="btn btn-primary btn-sm" data-phrase-put><i class="bi bi-plus-lg me-1"></i><span></span></button>
      <button type="button" class="btn btn-outline-secondary btn-sm" data-phrase-out hidden><i class="bi bi-dash-lg me-1"></i>Take it out</button>
    </div>`;
  field.insertAdjacentElement('afterend', card);
  const putBtn = card.querySelector('[data-phrase-put]');
  const outBtn = card.querySelector('[data-phrase-out]');
  const now = () => String(state.data[key] ?? '').trim();
  const has = () => now() === phrase || (append && now().endsWith(DX_PHRASE_SEP + phrase));
  const part = {
    refresh() {
      const text = now();
      const inBox = has();
      putBtn.hidden = inBox || (!append && text !== '');
      putBtn.querySelector('span').textContent = text ? 'Add it to the end' : 'Put it in';
      outBtn.hidden = !inBox;
      card.querySelector('.dx-status').textContent = inBox ? 'It is in the box below.'
        : (!append && text ? 'Something else is written in the box, so this is not offered.' : '');
    },
  };
  const put = value => {
    dxApplying = true;
    try { applyFormData({ [key]: value }); } finally { dxApplying = false; }
    part.refresh();
  };
  putBtn.addEventListener('click', () => put(now() ? now() + DX_PHRASE_SEP + phrase : phrase));
  outBtn.addEventListener('click', () => {
    const text = now();
    put(text === phrase ? '' : text.slice(0, text.length - (DX_PHRASE_SEP + phrase).length));
  });
  return part;
}

// CF4 2.a: on its own only - it would contradict any other history.
const dxPastHistory = dxPhraseCard('cf4', 'cf4PastMedicalHistory', 'NO KNOWN MEDICAL ILLNESS',
  'The usual wording: no known medical illness', false);
// Patient details: the brief history, added to whatever is written there.
const dxLaborPains = dxPhraseCard('patient', 'briefHistory', 'LABOR PAINS',
  'The usual wording: labor pains', true);

/* ── Kept in step with the forms ─────────────────────────── */

function dxRefreshAll() {
  if (dxApplying) return;
  [dxDiagnosis, dxCourse, dxDrugs, dxPastHistory, dxLaborPains].forEach(part => { if (part) part.refresh(); });
}

const updateFormPreviewsBeforeDx = updateFormPreviews;
updateFormPreviews = function () {
  updateFormPreviewsBeforeDx.apply(this, arguments);
  dxRefreshAll();
};

// A new or reloaded patient: what was typed in the blanks was for the last one.
const resetFormDataBeforeDx = resetFormData;
resetFormData = function () {
  [dxDiagnosis, dxCourse].forEach(part => { if (part) part.reset(); });
  resetFormDataBeforeDx.apply(this, arguments);
};

dxRefreshAll();
