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
}

document.addEventListener('input', e => {
  if (e.target.matches && e.target.matches('[data-ocr-required]')) refreshRequiredHighlights();
});
document.addEventListener('change', e => {
  if (e.target.matches && e.target.matches('[data-ocr-required]')) refreshRequiredHighlights();
});
document.getElementById('clearFormBtn').addEventListener('click', clearOcrTags);

loadClaimFromUrl();
