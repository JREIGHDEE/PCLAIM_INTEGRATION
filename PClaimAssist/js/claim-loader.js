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
   showToast, logActivity, escHtml, OVERLAY_MAP, VAL_FIELDS).
═══════════════════════════════════════════════════════════ */

const PCA_API_BASE = 'http://127.0.0.1:5000';

const OCR_TAGS = {
  accepted:    { label: 'From scan',                hint: 'Filled from the logbook scan; the computer was sure. Take a quick look.' },
  needs_check: { label: 'From scan · please check', hint: 'Filled from the logbook scan, but the computer was not sure. Compare it with the logbook.' },
  typed:       { label: 'Typed by staff',           hint: 'Typed or corrected by staff while checking the scan.' },
  required:    { label: 'Please type',              hint: 'The computer could not read this. Type it from the logbook.' },
  default:     { label: 'Clinic default',           hint: 'Filled from the clinic settings.' },
  empty:       { label: 'Empty in logbook',         hint: 'Nothing is written here in the logbook. Fill it in only if you know it.' },
};
const FORM_NAMES = { pmrf: 'PMRF', csf: 'CSF', cf2: 'CF2', cf3: 'CF3' };

/* Label element for a bound input: the field's own label, not a radio
   option's ("AM"/"PM") or a checkbox's caption. */
function fieldLabelFor(el) {
  const container = el.closest('[class*="col"]') || el.parentElement;
  return container && container.querySelector('label:not(.form-check-label)');
}

// Repeating fields listed as one entry in the "still to type" list.
const FIELD_GROUPS = [
  [/^pnc/, 'Follow-up prenatal visits grid (2nd–12th)'],
  [/^risk/, 'Obstetric / medical risk-factor checkboxes'],
  [/^pp/, 'Postpartum care checklist'],
];

function fieldLabelText(key) {
  const el = document.querySelector(`[data-autofill="${key}"]`);
  // A checkbox's own caption, when it has no separate field label.
  const label = el && (fieldLabelFor(el) || (el.id && document.querySelector(`label[for="${el.id}"]`)));
  if (!label) return key;
  const clone = label.cloneNode(true);
  clone.querySelectorAll('.required-dot, .ocr-tag').forEach(n => n.remove());
  return clone.textContent.trim() || key;
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
      const label = fieldLabelFor(el);
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

/* Which of the four forms print a given form key (from the PDF overlays). */
function formsPrinting(key) {
  return Object.keys(FORM_NAMES).filter(form =>
    (OVERLAY_MAP[form] || []).some(f => f.key === key));
}

function renderClaimBanner(body) {
  const counts = {};
  Object.values(body.fields).forEach(f => { counts[f.status] = (counts[f.status] || 0) + 1; });
  const required = Object.entries(body.fields).filter(([, f]) => f.status === 'required').map(([k]) => k);

  // Fields no logbook column can fill, grouped by the form that prints
  // them; only the ones still empty, required-for-validation ones first.
  const requiredByForm = {};
  Object.entries(VAL_FIELDS).forEach(([form, list]) => {
    requiredByForm[form] = new Set(list.map(f => f.key));
  });
  const stillToType = Object.keys(FORM_NAMES).map(form => {
    const keys = body.no_ocr_source.filter(k => formsPrinting(k).includes(form) && !state.data[k]);
    keys.sort((a, b) => requiredByForm[form].has(b) - requiredByForm[form].has(a));
    const seen = new Set();
    const items = [];
    keys.forEach(k => {
      const group = FIELD_GROUPS.find(([re]) => re.test(k));
      const text = group ? group[1] : fieldLabelText(k);
      if (seen.has(text)) return;
      seen.add(text);
      items.push(requiredByForm[form].has(k) ? `<strong>${escHtml(text)}</strong>` : escHtml(text));
    });
    return items.length
      ? `<li><span class="form-badge-inline">${FORM_NAMES[form]}</span> ${items.join(', ')}</li>`
      : '';
  }).join('');

  const iq = body.image_quality;
  const iqLine = iq && iq.passed === false
    ? `<div class="claim-banner-iq"><i class="bi bi-exclamation-triangle-fill me-1"></i>
         The logbook scan was not very clear — check the fields marked "From scan" carefully.
         <span class="claim-banner-tag">(image quality check ${escHtml(iq.rule_id)})</span></div>`
    : '';
  const address = body.ocr_reference && body.ocr_reference.ADDRESS;
  const addressLine = address
    ? `<div class="claim-banner-ref"><strong>Address from the logbook:</strong>
         ${escHtml(address)} — please type it into the parts under <em>Address &amp; Contact</em>.</div>`
    : '';
  const requiredLine = required.length
    ? `<div class="claim-banner-required"><span class="ocr-tag ocr-tag--required">Please type</span>
         The computer could not read these — type them from the logbook: ${required.map(k => escHtml(fieldLabelText(k))).join(', ')}</div>`
    : '';

  const banner = document.createElement('div');
  banner.id = 'claimLoadBanner';
  banner.className = 'claim-load-banner mb-3';
  banner.innerHTML = `
    <div class="claim-banner-head">
      <i class="bi bi-upc-scan me-2"></i>
      <strong>Patient loaded from the logbook scan</strong> <span class="claim-banner-tag">(claim #${body.claim_id})</span>
      <span class="claim-banner-legend">
        ${['accepted', 'needs_check', 'typed', 'required', 'empty', 'default']
          .filter(s => counts[s])
          .map(s => `<span class="ocr-tag ocr-tag--${s}">${OCR_TAGS[s].label}</span> ${counts[s]}`)
          .join(' &nbsp; ')}
      </span>
    </div>
    ${iqLine}${requiredLine}${addressLine}
    <details class="claim-banner-details">
      <summary>Other fields to fill in — the logbook does not have these (${body.no_ocr_source.filter(k => !state.data[k]).length} empty)</summary>
      <ul>${stillToType}</ul>
      <p class="claim-banner-note">Bold = must be filled in for that form. Changes made on these forms are not saved back to the database.</p>
    </details>`;
  const section = document.getElementById('section-patient');
  const anchor = section.querySelector('.alert-auto-populate');
  anchor.insertAdjacentElement('afterend', banner);
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
  applyFormData(values);
  tagOcrFields(body.fields);
  renderClaimBanner(body);
  navigateTo('patient');
  logActivity(`Patient loaded from the logbook scan (claim #${claimId})`, 'success');
  showToast('Patient loaded', 'Answers from the logbook are marked "From scan". Red boxes still need typing.', 'success');
}

document.addEventListener('input', e => {
  if (e.target.matches && e.target.matches('[data-ocr-required]')) refreshRequiredHighlights();
});
document.addEventListener('change', e => {
  if (e.target.matches && e.target.matches('[data-ocr-required]')) refreshRequiredHighlights();
});
document.getElementById('clearFormBtn').addEventListener('click', clearOcrTags);

loadClaimFromUrl();
