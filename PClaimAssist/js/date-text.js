/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Typed dates (MM/DD/YYYY)

   The browser's own date picker lays its boxes out in the order of the
   computer's region setting. On the clinic's PCs that is day/month/year,
   while every PhilHealth form - and every label here - is month-day-year,
   so "03-15-2024" typed the way it is written on paper came out as
   3 December 2024, with no warning.

   Each <input type="date"> is therefore shown as a plain box typed as
   MM/DD/YYYY, with that as its example. The date input itself stays in the
   page, hidden, and still holds the date as yyyy-mm-dd, so state.data, the
   checks, the PDFs and saving see exactly what they saw before.

   The visible box follows its date input: read-only / disabled, and the
   classes and hover text other code puts on it (missing, red, locked), are
   copied across, and a value set from code reaches it through
   refreshBoxInputs() (js/box-input.js), which the app calls on every sync.
═══════════════════════════════════════════════════════════ */

const DATE_TEXT_EXAMPLE = '03/15/2024';

function isoFromTyped(text) {
  const m = String(text).match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const [, mm, dd, yyyy] = m;
  const date = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
  if (date.getFullYear() !== Number(yyyy) || date.getMonth() !== Number(mm) - 1 ||
      date.getDate() !== Number(dd)) return null;
  return `${yyyy}-${mm}-${dd}`;
}

function typedFromIso(iso) {
  const m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${m[2]}/${m[3]}/${m[1]}` : '';
}

/* As it is typed: slashes added after the month and the day, and a one-digit
   month or day padded when its slash is typed ("3/" -> "03/"). */
function formatTypedDate(value) {
  const separators = (value.match(/[^\d]+/g) || []).length;
  let mm, dd, yyyy;
  if (!separators) {
    const digits = value.replace(/\D/g, '');
    mm = digits.slice(0, 2); dd = digits.slice(2, 4); yyyy = digits.slice(4, 8);
  } else {
    const parts = value.split(/[^\d]+/);
    mm = parts[0] || ''; dd = parts[1] || ''; yyyy = (parts[2] || '').slice(0, 4);
    if (mm.length === 1 && separators >= 1) mm = '0' + mm;
    if (dd.length === 1 && separators >= 2) dd = '0' + dd;
    mm = mm.slice(0, 2); dd = dd.slice(0, 2);
  }
  let out = mm;
  if (mm.length === 2) out += '/' + dd;
  if (mm.length === 2 && dd.length === 2) out += '/' + yyyy;
  return out;
}

function initDateText(real) {
  const text = document.createElement('input');
  text.type = 'text';
  text.inputMode = 'numeric';
  text.maxLength = 10;
  text.autocomplete = 'off';
  text.placeholder = 'MM/DD/YYYY';
  text.dataset.dateFor = real.dataset.autofill || real.id || '';
  text.setAttribute('aria-label', (real.getAttribute('aria-label') || 'Date') + ', month/day/year');
  const message = document.createElement('div');
  message.className = 'date-text-msg';
  message.hidden = true;
  real.classList.add('pca-date-real');
  real.insertAdjacentElement('afterend', text);
  text.insertAdjacentElement('afterend', message);
  real.pcaDateText = text;

  // Typed but not a whole date yet (or not a real one): kept on screen, and
  // the date behind it left empty.
  let unfinished = false;

  function mirror() {
    const own = ['pca-date-text'];
    if (unfinished) own.push('date-text--invalid');
    text.className = [...real.classList].filter(c => c !== 'pca-date-real').concat(own).join(' ');
    text.readOnly = real.readOnly;
    text.disabled = real.disabled;
    const title = real.getAttribute('title');
    if (title) text.setAttribute('title', title); else text.removeAttribute('title');
  }

  function showProblem(show) {
    unfinished = show;
    message.hidden = !show;
    message.textContent = show
      ? `Type the date as month/day/year, for example ${DATE_TEXT_EXAMPLE}.` : '';
    mirror();
  }

  function setReal(iso) {
    if (real.value === iso) return;
    real.value = iso;
    real.dispatchEvent(new Event('input', { bubbles: true }));
    real.dispatchEvent(new Event('change', { bubbles: true }));
  }

  text.addEventListener('input', e => {
    const deleting = (e.inputType || '').startsWith('delete');
    if (!deleting) {
      const formatted = formatTypedDate(text.value);
      if (formatted !== text.value) text.value = formatted;
    }
    const iso = isoFromTyped(text.value);
    if (iso) { showProblem(false); setReal(iso); }
    else if (!text.value) { showProblem(false); setReal(''); }
  });

  text.addEventListener('blur', () => {
    if (!text.value) return;
    const iso = isoFromTyped(text.value);
    if (iso) { showProblem(false); return; }
    showProblem(true);
    setReal('');
  });

  function syncFromReal() {
    if (document.activeElement === text) return;
    if (real.value) {
      text.value = typedFromIso(real.value);
      showProblem(false);
    } else if (!unfinished) {
      text.value = '';
    }
  }

  // A date input changed by its own events (e.g. "same day as admitted").
  real.addEventListener('input', syncFromReal);
  real.addEventListener('change', syncFromReal);
  new MutationObserver(mirror).observe(real, {
    attributes: true, attributeFilter: ['class', 'readonly', 'disabled', 'title'],
  });

  mirror();
  syncFromReal();
  BOX_INPUT_SYNCS.push(syncFromReal);
  DATE_TEXT_RESETS.push(() => { text.value = ''; showProblem(false); });
}

/* "Start a new patient" clears half-typed dates too (see clearUnfinishedEntries). */
const DATE_TEXT_RESETS = [];

document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent =
    '.pca-date-real{display:none !important}' +
    '.pca-date-text.date-text--invalid{border-color:#dc2626 !important;background:#fef2f2}' +
    '.date-text-msg{color:#b91c1c;font-size:.8rem;font-weight:600;margin-top:4px}';
  document.head.appendChild(style);

  document.querySelectorAll('input[type="date"]').forEach(real => {
    // The CSF's per-digit date rows already stand in for theirs (box-input.js).
    if (real.id && document.querySelector(`.box-input-date[data-target="#${real.id}"]`)) return;
    initDateText(real);
  });
});
