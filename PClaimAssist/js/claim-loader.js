/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Load a claim from the OCR review (index.html?claim=<id>)

   "Send to Forms" in the OCR backend's logbook review opens this page
   with only the claim's id in the URL. The data itself is fetched from
   GET /api/claims/<id>/form-data, which returns values already keyed by
   form key (Ocr_module/philhealth/field_catalog.py FORM_FIELDS is the one
   mapping - nothing here maps database columns).

   Every OCR-sourced field is tagged, in plain words, so staff know what
   to double-check:
     accepted    "From scan"                (green)
     needs_check "From scan · please check" (amber)
     typed       "Typed by staff"           (blue)
     required    "Please type"              (red, left empty - type it here)
     default     "Clinic default"           (gray)
     empty       "Empty in logbook"         (gray, dashed - blank in the logbook)
   Needs js/app.js (state, applyFormData, resetFormData, navigateTo,
   updateFormPreviews, MIRRORED_FIELDS, showToast, logActivity).
═══════════════════════════════════════════════════════════ */

/* Empty string = same origin; the backend serves this page too. */
const PCA_API_BASE = '';

const OCR_TAGS = {
  accepted:    { label: 'From scan',                hint: 'Filled from the logbook scan; the computer was sure. Take a quick look.' },
  needs_check: { label: 'From scan · please check', hint: 'Filled from the logbook scan, but the computer was not sure. Compare it with the logbook.' },
  typed:       { label: 'Typed by staff',           hint: 'Typed or corrected by staff while checking the scan.' },
  required:    { label: 'Please type',              hint: 'The computer could not read this. Type it from the logbook.' },
  default:     { label: 'Clinic default',           hint: 'Filled from the clinic settings.' },
  empty:       { label: 'Empty in logbook',         hint: 'Nothing is written here in the logbook. Fill it in only if you know it.' },
};

/* Label element for a bound input: the field's own label, not a radio
   option's ("AM"/"PM") or a checkbox's caption. */
function fieldLabelFor(el) {
  const container = el.closest('[class*="col"]') || el.parentElement;
  return container && container.querySelector('label:not(.form-check-label)');
}

function describeField(info) {
  const tag = OCR_TAGS[info.status];
  const parts = [info.reason || tag.hint];
  if (info.raw_text) parts.push(`The computer read: "${info.raw_text}"`);
  if (info.confidence !== null && info.confidence !== undefined) {
    parts.push(`${Math.round(info.confidence * 100)}% sure`);
  }
  return parts.join(' · ');
}

function tagOcrFields(fields) {
  Object.entries(fields).forEach(([key, info]) => {
    const tag = OCR_TAGS[info.status];
    if (!tag) return;
    const labelsDone = new Set();
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      el.classList.add('ocr-field', `ocr-field--${info.status}`);
      if (info.status === 'required') {
        el.dataset.ocrRequired = '1';
        el.setAttribute('aria-required', 'true');
      }
      // Only the tag that asks for something is shown on the box: "please
      // check". "From scan", "Typed by staff", "Clinic default" and "Empty in
      // logbook" are just notices, and a box still to type is already red.
      const label = info.status === 'needs_check' ? fieldLabelFor(el) : null;
      if (label && !labelsDone.has(label) && !label.querySelector('.ocr-tag')) {
        labelsDone.add(label);
        const span = document.createElement('span');
        span.className = `ocr-tag ocr-tag--${info.status}`;
        span.textContent = tag.label;
        span.title = describeField(info);
        label.appendChild(span);
      }
    });
  });
  refreshRequiredHighlights();
}

/* A required field stops being highlighted once something is typed in. */
function refreshRequiredHighlights() {
  document.querySelectorAll('[data-ocr-required]').forEach(el => {
    const key = el.dataset.autofill;
    const empty = el.type === 'radio' ? !state.data[key] : !String(el.value || '').trim();
    el.classList.toggle('ocr-field--missing', empty);
  });
}

function clearOcrTags() {
  document.querySelectorAll('.ocr-tag').forEach(n => n.remove());
  document.querySelectorAll('.ocr-field').forEach(el => {
    [...el.classList].filter(c => c.startsWith('ocr-field')).forEach(c => el.classList.remove(c));
    delete el.dataset.ocrRequired;
    el.removeAttribute('aria-required');
  });
  const banner = document.getElementById('claimLoadBanner');
  if (banner) banner.remove();
}

/* Only what staff must see: a warning when the scan was not clear, so
   they check the "From scan" boxes more carefully. What the scan filled in
   is shown on each box (its "From scan" tag), and what is left is shown
   by the red boxes and the parts' counts on Patient details. */
function renderClaimBanner(body) {
  const iq = body.image_quality;
  if (!iq || iq.passed !== false) return;
  const banner = document.createElement('div');
  banner.id = 'claimLoadBanner';
  banner.className = 'claim-load-banner claim-banner-iq mb-3';
  banner.setAttribute('role', 'alert');
  banner.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i>
    The logbook scan was not very clear — check the boxes marked "From scan" carefully.`;
  // Under the Patient Details heading.
  const section = document.getElementById('section-patient');
  const anchor = section.querySelector('.section-header');
  if (anchor) anchor.insertAdjacentElement('afterend', banner);
  else section.prepend(banner);
}

async function loadClaimFromUrl() {
  const claimId = new URLSearchParams(location.search).get('claim');
  if (!claimId) return;
  if (!/^\d+$/.test(claimId)) {
    showToast('Invalid claim link', 'The claim id in the link is not a number.', 'danger');
    return;
  }
  let body;
  try {
    const resp = await fetch(`${PCA_API_BASE}/api/claims/${claimId}/form-data`);
    body = await resp.json();
  } catch (err) {
    showToast('Could not reach the logbook reader',
      `Start it with run_ocr.bat (expected at ${PCA_API_BASE}), then reload this page.`, 'danger');
    return;
  }
  if (!body.success) {
    showToast('Claim not loaded', body.error || 'Unknown error', 'danger');
    return;
  }

  clearOcrTags();
  resetFormData();
  const values = { ...body.data };
  // Required fields start empty, even ones with a default (e.g. AM/PM).
  Object.entries(body.fields).forEach(([key, f]) => { if (f.status === 'required') values[key] = ''; });
  // What was typed on the forms last time is put back over the logbook's
  // values. A box changed from what the scan read is no longer "from scan".
  const saved = { ...(body.saved_values || {}) };
  const copiedFromMother = saved[MOTHER_COPY_KEY] || null;
  delete saved[MOTHER_COPY_KEY];
  Object.entries(saved).forEach(([key, value]) => {
    if (!(key in state.data)) return;
    if (body.fields[key] && String(value ?? '') !== String(values[key] ?? '')) {
      body.fields[key] = { ...body.fields[key], status: 'typed', reason: null };
    }
    values[key] = value;
  });
  // Boxes on other forms that repeat a logbook value (the final diagnosis
  // on CF4's diagnosis line) are filled from it too, with the same
  // tag, instead of being typed again (app.js MIRRORED_FIELDS - normally
  // copied only as someone types).
  Object.entries(MIRRORED_FIELDS).forEach(([source, targets]) => {
    if (!values[source]) return;
    targets.forEach(target => {
      if (values[target]) return;
      values[target] = values[source];
      if (body.fields[source]) body.fields[target] = { ...body.fields[source] };
    });
  });
  applyFormData(values);
  tagOcrFields(body.fields);
  renderClaimBanner(body);
  navigateTo('patient');
  // Once the tags are on, so Patient details' parts count "from scan to
  // check" too (js/easy.js refreshes them on every update).
  updateFormPreviews();
  logActivity(`Patient loaded from the logbook scan (claim #${claimId})`, 'success');

  openClaimId = Number(claimId);
  lastSavedJson = claimSaveJson();
  renderSavePatient('This patient is kept with the logbook claim and saves as you type. ' +
    'Press Save patient when the forms are done.', false);
  // Mother or baby, and copying a baby's details from its mother's claim
  // (js/mother-baby.js).
  if (typeof initMotherBaby === 'function') initMotherBaby(claimId, copiedFromMother);
}

/* ── Saving what is typed with the claim ──────────────────────
   Everything typed on the forms is saved with the open claim
   (PUT /api/claims/<id>/form-values) a moment after the last change, so
   it is back when the claim is opened again - and a baby's claim can
   copy it from its mother's. */
const MOTHER_COPY_KEY = '_copiedFromMother';
const CLAIM_SAVE_DELAY_MS = 1200;
let openClaimId = null;
let lastSavedJson = null;
let claimSaveTimer = null;

function claimSaveJson() {
  const values = { ...state.data };
  const copied = typeof motherCopyState === 'function' ? motherCopyState() : null;
  if (copied) values[MOTHER_COPY_KEY] = copied;
  return JSON.stringify(values);
}

/* The open claim's forms were saved as a PDF (js/pdf/pdf-overlay.js, after
   the critical rules passed): the server marks the claim exported and
   deletes the logbook pictures it no longer needs. The PDF is saved either
   way, so a failure here is only logged. */
async function reportClaimExported() {
  if (!openClaimId) return;
  try {
    await fetch(`${PCA_API_BASE}/api/claims/${openClaimId}/exported`, { method: 'POST' });
  } catch (err) {
    console.warn('[PCA] Could not mark the claim exported', err);
  }
}

async function saveOpenClaim(opts = {}) {
  clearTimeout(claimSaveTimer);
  if (!openClaimId) return;
  const json = claimSaveJson();
  if (json === lastSavedJson) return;
  const claimId = openClaimId;
  try {
    const resp = await fetch(`${PCA_API_BASE}/api/claims/${claimId}/form-values`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: `{"values":${json}}`,
      keepalive: !!opts.leaving,
    });
    if (resp.ok && claimId === openClaimId) lastSavedJson = json;
    if (!resp.ok && !claimSaveWarned) {
      // Said once (e.g. the database still needs an update), not on every key.
      claimSaveWarned = true;
      const body = await resp.json().catch(() => ({}));
      showToast('Not saved', body.error || `The patient could not be saved (${resp.status}).`, 'warning');
    }
  } catch (err) { /* tried again on the next change */ }
}
let claimSaveWarned = false;

function scheduleClaimSave() {
  if (!openClaimId) return;
  clearTimeout(claimSaveTimer);
  claimSaveTimer = setTimeout(saveOpenClaim, CLAIM_SAVE_DELAY_MS);
}

/* ── "Save patient" (Check for Missing Information) ─────────
   Saves everything typed with the patient's claim and copies the core of
   it (name, birthday, stay, delivery) into the claim itself, so a baby's
   claim finds its mother there. A patient typed in by hand, not from the
   logbook, gets its own claim here; from then on it saves as it is typed,
   like a claim from the logbook. */
const ROLE_NOTES = {
  mother: 'Saved as a mother: her baby\'s claim can copy her details (Patient details → Mother or baby?).',
  baby: 'Saved as a baby.',
  other: 'Saved.',
};

function renderSavePatient(text, saved) {
  const card = document.getElementById('savePatientCard');
  if (!card) return;
  card.classList.toggle('is-saved', !!saved);
  document.getElementById('savePatientNote').textContent = text ||
    'Keeps every detail of this patient, so it can be opened again and her baby\'s claim can copy it.';
  document.getElementById('savePatientLabel').textContent = openClaimId ? 'Save again' : 'Save patient';
}

async function savePatient() {
  const btn = document.getElementById('savePatientBtn');
  clearTimeout(claimSaveTimer);
  const json = claimSaveJson();
  btn.disabled = true;
  try {
    const resp = await fetch(`${PCA_API_BASE}/api/claims/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: `{"claim_id":${openClaimId || 'null'},"values":${json}}`,
    });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok || !body.success) throw new Error(body.error || `Could not save (${resp.status})`);
    const isNew = body.claim_id !== openClaimId;
    openClaimId = body.claim_id;
    lastSavedJson = json;
    if (isNew) {
      const url = new URL(location.href);
      url.searchParams.set('claim', String(body.claim_id));
      history.replaceState(null, '', url);
      // Now a claim: Patient details can say mother or baby, and link a baby.
      if (typeof initMotherBaby === 'function') await initMotherBaby(body.claim_id, null);
    }
    const role = typeof mb !== 'undefined' && mb.family ? mb.family.role : null;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const name = [state.data.patientFirstName, state.data.patientLastName].filter(Boolean).join(' ');
    renderSavePatient(`${name || 'Patient'} saved at ${time}. ${ROLE_NOTES[role] ||
      'Mark mother or baby on Patient details so a baby\'s claim can find her.'} Changes from now on save by themselves.`, true);
    showToast('Patient saved', `${name || 'The patient'} is saved and can be opened again.`, 'success');
    logActivity(`Patient saved (claim #${body.claim_id})`, 'success');
  } catch (err) {
    showToast('Patient not saved', err.message, 'danger');
  } finally {
    btn.disabled = false;
  }
}

document.getElementById('savePatientBtn').addEventListener('click', savePatient);

// Every change on the forms ends in updateFormPreviews() (js/app.js).
const updateFormPreviewsUnsaved = updateFormPreviews;
updateFormPreviews = function () {
  updateFormPreviewsUnsaved.apply(this, arguments);
  // A "Please type" box filled by something other than typing (the
  // clinic's wording, the mother's details) is no longer red.
  refreshRequiredHighlights();
  scheduleClaimSave();
};

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') saveOpenClaim({ leaving: true });
});

document.addEventListener('pca:new-patient', () => {
  // Let go of the claim: the blank forms belong to a new patient.
  openClaimId = null;
  lastSavedJson = null;
  clearTimeout(claimSaveTimer);
  renderSavePatient(null, false);
  clearOcrTags();
  if (typeof closeMotherBaby === 'function') closeMotherBaby();
  const url = new URL(location.href);
  if (url.searchParams.has('claim')) {
    url.searchParams.delete('claim');
    history.replaceState(null, '', url);
  }
});

document.addEventListener('input', e => {
  if (e.target.matches && e.target.matches('[data-ocr-required]')) refreshRequiredHighlights();
});
document.addEventListener('change', e => {
  if (e.target.matches && e.target.matches('[data-ocr-required]')) refreshRequiredHighlights();
});

loadClaimFromUrl();
