/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Reason for admission from the logbook (user testing #5)

   The logbook writes a handful of admissions over and over ("CEPHALIC IN
   LABOR", "POST PARTUM VISIT", "WELL BABY CARE"...). When a claim is
   opened from a scan, the server matches its admitting diagnosis against
   the admission patterns - letter by letter, so "FOR POJT PAKTUM UISIT"
   is still POST PARTUM VISIT - and puts the clinic's wording into Chief
   Complaint / Reason for Admission, "please check"
   (Ocr_module/philhealth/admission_patterns.py).

     • Patient details: the reason is filled in by itself; a card under
       it says what was read and which pattern it was taken for. Picking
       the right one when it is wrong teaches the table that reading, so
       the same misread is recognised next time. The pattern's package helps pick the
       claim's package (js/dx-templates.js dxGuessPackage).
     • Clinic → Admission patterns: the table itself - clues, the wording,
       the package, what it has learned - with a box to try a reading.

   Needs js/app.js (state, applyFormData, navigateTo, escapeHtmlText,
   showToast) and PCA_API_BASE.
═══════════════════════════════════════════════════════════ */

const PCAAdmission = (function () {
  const API = () => `${window.PCA_API_BASE || ''}/api/admission-patterns`;
  const esc = text => escapeHtmlText(text == null ? '' : String(text));
  const PACKAGE_NAMES = {
    '': 'None', NSDBF: 'Normal delivery (NSDBF)', NCP: 'Newborn care (NCP)', ANV: 'Prenatal care (ANV)',
    PPC01: 'Postpartum visit (PPC01)', FP001: 'Implant (FP001)', IUD: 'IUD insertion (IUD)',
  };

  async function call(path, opts) {
    const resp = await fetch(API() + path, {
      credentials: 'include',
      ...(opts || {}),
      headers: { 'Content-Type': 'application/json', ...((opts || {}).headers || {}) },
    });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok || body.success === false) throw new Error(body.error || `Request failed (${resp.status})`);
    return body;
  }

  /* ── The card under Reason for admission ──────────────────── */

  let shown = null;      // {suggestion, chosen: pattern row, patterns, done}
  let card = null;

  function host() {
    if (card && document.body.contains(card)) return card;
    const field = document.querySelector('#section-patient [data-autofill="chiefComplaint"]');
    if (!field) return null;
    card = document.createElement('div');
    card.className = 'dx-template admission-card';
    card.hidden = true;
    field.insertAdjacentElement('afterend', card);
    return card;
  }

  async function show(suggestion) {
    shown = null;
    const box = host();
    if (!box) return;
    box.hidden = true;
    if (!suggestion || !suggestion.pattern) return;
    // Only while the reason is still the suggested one: a reason staff
    // typed themselves (saved with the claim) is theirs, with no card.
    if (String(state.data.chiefComplaint || '').trim() !== suggestion.pattern.reason) return;
    let patterns = [];
    try { patterns = (await call('')).patterns.filter(p => p.is_active); } catch (err) { /* card still shows */ }
    shown = { suggestion, chosen: suggestion.pattern, patterns, done: false };
    render();
  }

  function render() {
    const box = host();
    if (!box || !shown) return;
    const { suggestion, chosen, patterns, done } = shown;
    const learnable = chosen.id != null && patterns.some(p => p.id != null);
    const others = patterns.filter(p => p.id !== chosen.id);
    box.hidden = false;
    box.innerHTML = `
      <div class="dx-head"><div class="dx-title"><i class="bi bi-magic me-2"></i>Filled in by itself from the logbook</div></div>
      <div class="small">
        The admitting diagnosis reads <strong class="admission-reading">"${esc(suggestion.reading)}"</strong>:
        that is <strong>${esc(chosen.name)}</strong>, so the reason for admission is <em>${esc(chosen.reason)}</em>
        ${chosen.why ? `<span class="text-muted">(${esc(chosen.why)})</span>` : ''}
      </div>
      ${done ? `<div class="dx-status small text-success mt-2"><i class="bi bi-check-circle-fill me-1"></i>${esc(done)}</div>` : ''}
      <div class="dx-actions mt-2">
        ${others.length ? `<label class="d-inline-flex align-items-center gap-2 small mb-0">Not right? It is
            <select class="form-select form-select-sm w-auto" data-adm-pick>
              <option value="">- choose -</option>
              ${others.map(p => `<option value="${p.id ?? ''}" data-name="${esc(p.name)}">${esc(p.name)}: ${esc(p.reason)}</option>`).join('')}
              <option value="none">None of these</option>
            </select></label>` : ''}
        <button type="button" class="btn btn-link btn-sm" data-adm-table>Edit the patterns</button>
      </div>
      ${learnable ? '' : '<div class="small text-muted mt-1">The patterns are the starting ones until migration 012 is run, so corrections are not remembered yet.</div>'}`;
  }

  async function learn(pattern, message) {
    try {
      if (pattern.id != null) {
        await call(`/${pattern.id}/learn`, {
          method: 'POST',
          body: JSON.stringify({ reading: shown.suggestion.reading, suggested_id: shown.suggestion.pattern.id }),
        });
      }
      shown.done = message;
    } catch (err) {
      shown.done = null;
      showToast('Not remembered', err.message, 'warning');
    }
    render();
  }

  document.addEventListener('click', e => {
    if (!card || !card.contains(e.target)) return;
    if (e.target.closest('[data-adm-table]')) openTable(shown && shown.suggestion.reading);
  });

  document.addEventListener('change', e => {
    if (!card || !e.target.matches('[data-adm-pick]')) return;
    const value = e.target.value;
    if (!value) return;
    const was = shown.chosen;
    if (value === 'none') {
      // Only take out the wording this card put in.
      if (String(state.data.chiefComplaint || '').trim() === was.reason) applyFormData({ chiefComplaint: '' });
      shown.chosen = { ...was, id: null, name: 'none of the patterns', reason: '(type it yourself)', why: '', package: '' };
      shown.done = 'Type the reason for admission yourself - or add a pattern for it with "Edit the patterns".';
      render();
      updateFormPreviews();
      return;
    }
    const pattern = shown.patterns.find(p => String(p.id) === value);
    if (!pattern) return;
    shown.chosen = { ...pattern, why: 'chosen by you' };
    const now = String(state.data.chiefComplaint || '').trim();
    if (!now || now === was.reason) applyFormData({ chiefComplaint: pattern.reason });
    updateFormPreviews();
    learn(pattern, `Remembered: "${shown.suggestion.reading}" is ${pattern.name} - it will be suggested next time.`);
  });

  /* The package of the admission on the card, for the claim's package
     while none is picked by hand (js/dx-templates.js dxGuessPackage). */
  function suggestedPackage() {
    return shown && shown.chosen && shown.chosen.package ? shown.chosen.package : '';
  }

  function clear() {
    shown = null;
    if (card) card.hidden = true;
  }
  document.addEventListener('pca:new-patient', clear);

  /* ── Clinic → Admission patterns ───────────────────────────── */

  let table = { patterns: [], editable: false, packages: [] };

  function packageSelect(value, attrs) {
    return `<select class="form-select form-select-sm" ${attrs}>
      ${(table.packages.length ? table.packages : Object.keys(PACKAGE_NAMES)).map(k =>
        `<option value="${esc(k)}"${k === (value || '') ? ' selected' : ''}>${esc(PACKAGE_NAMES[k] || k)}</option>`).join('')}
    </select>`;
  }

  function rowHtml(p) {
    const id = p.id == null ? 'new' : p.id;
    const examples = (p.examples || []).map(x =>
      `<span class="admission-example">${esc(x)}${table.editable && p.id != null
        ? ` <button type="button" class="btn btn-link btn-sm p-0" data-adm-forget="${esc(x)}" title="Forget this reading" aria-label="Forget this reading">&times;</button>` : ''}</span>`).join(' ');
    return `
      <tr data-adm-row="${id}"${p.is_active === false ? ' class="admission-off"' : ''}>
        <td><input class="form-control form-control-sm" data-f="name" value="${esc(p.name)}" maxlength="80" aria-label="Name"></td>
        <td><textarea class="form-control form-control-sm" data-f="clues" rows="3" aria-label="Clues, one per line">${esc((p.clues || []).join('\n'))}</textarea></td>
        <td><input class="form-control form-control-sm" data-f="reason" value="${esc(p.reason)}" maxlength="191" aria-label="Reason for admission"></td>
        <td>${packageSelect(p.package, 'data-f="package" aria-label="Package"')}</td>
        <td class="text-center"><input type="checkbox" class="form-check-input" data-f="is_active"${p.is_active === false ? '' : ' checked'} aria-label="In use"></td>
        <td class="small">${examples || '<span class="text-muted">none yet</span>'}
          ${p.id != null ? `<div class="text-muted mt-1">Right ${p.times_confirmed || 0} &middot; corrected ${p.times_corrected || 0}</div>` : ''}</td>
        <td class="text-nowrap">
          <button type="button" class="btn btn-primary btn-sm" data-adm-save${table.editable ? '' : ' disabled'}>${p.id == null ? 'Add' : 'Save'}</button>
          ${p.id != null ? `<button type="button" class="btn btn-outline-danger btn-sm" data-adm-delete${table.editable ? '' : ' disabled'} title="Delete" aria-label="Delete"><i class="bi bi-trash"></i></button>` : ''}
        </td>
      </tr>`;
  }

  function drawTable() {
    const body = document.getElementById('admissionPatternRows');
    if (!body) return;
    body.innerHTML = table.patterns.map(rowHtml).join('') +
      rowHtml({ id: null, name: '', clues: [], reason: '', package: '', is_active: true, examples: [] });
    const note = document.getElementById('admissionPatternsNote');
    if (note) note.hidden = table.editable;
  }

  async function loadTable() {
    try {
      table = await call('');
      drawTable();
    } catch (err) {
      showToast('Admission patterns not loaded', err.message, 'danger');
    }
  }

  function readRow(row) {
    const get = f => row.querySelector(`[data-f="${f}"]`);
    return { name: get('name').value, clues: get('clues').value, reason: get('reason').value,
             package: get('package').value, is_active: get('is_active').checked };
  }

  document.addEventListener('click', async e => {
    const row = e.target.closest('[data-adm-row]');
    if (!row) return;
    const id = row.dataset.admRow;
    try {
      if (e.target.closest('[data-adm-save]')) {
        if (id === 'new') await call('', { method: 'POST', body: JSON.stringify(readRow(row)) });
        else await call(`/${id}`, { method: 'PUT', body: JSON.stringify(readRow(row)) });
        showToast('Saved', 'The admission pattern is saved.', 'success');
        await loadTable();
        tryReading();
      } else if (e.target.closest('[data-adm-delete]')) {
        const name = row.querySelector('[data-f="name"]').value;
        if (!confirm(`Delete the pattern "${name}"? Switching it off (untick "In use") keeps what it learned.`)) return;
        await call(`/${id}`, { method: 'DELETE' });
        await loadTable();
        tryReading();
      } else if (e.target.closest('[data-adm-forget]')) {
        await call(`/${id}/forget`, { method: 'POST', body: JSON.stringify({ reading: e.target.closest('[data-adm-forget]').dataset.admForget }) });
        await loadTable();
      }
    } catch (err) {
      showToast('Not saved', err.message, 'danger');
    }
  });

  /* "Try a reading": the patterns against what was typed, best first. */
  let tryTimer = null;
  async function tryReading() {
    const input = document.getElementById('admissionTry');
    const out = document.getElementById('admissionTryResult');
    if (!input || !out) return;
    const text = input.value.trim();
    if (!text) { out.innerHTML = ''; return; }
    try {
      const { ranked, suggest_from: from } = await call('/try', { method: 'POST', body: JSON.stringify({ text }) });
      const top = ranked.slice(0, 3);
      out.innerHTML = top.length && top[0].score >= from
        ? `Suggests <strong>${esc(top[0].name)}</strong>: <em>${esc(top[0].reason)}</em>
           <span class="text-muted">(${Math.round(top[0].score * 100)}%, ${esc(top[0].why)})</span>` +
          (top.slice(1).filter(r => r.score >= 0.5).length
            ? `<div class="text-muted">Next: ${top.slice(1).filter(r => r.score >= 0.5)
                .map(r => `${esc(r.name)} ${Math.round(r.score * 100)}%`).join(', ')}</div>` : '')
        : `<span class="text-muted">Nothing close enough (best: ${top.length ? `${esc(top[0].name)} ${Math.round(top[0].score * 100)}%` : 'none'}).
           Add a clue to the right pattern below, or a new pattern.</span>`;
    } catch (err) {
      out.textContent = err.message;
    }
  }
  document.addEventListener('input', e => {
    if (e.target.id !== 'admissionTry') return;
    clearTimeout(tryTimer);
    tryTimer = setTimeout(tryReading, 250);
  });

  function openTable(reading) {
    navigateTo('admission-patterns');
    const input = document.getElementById('admissionTry');
    if (input && reading) { input.value = reading; tryReading(); }
  }

  // The table is read each time its page is opened.
  const navigateToBeforeAdmission = navigateTo;
  navigateTo = function (section) {
    navigateToBeforeAdmission.apply(this, arguments);
    if (section === 'admission-patterns') loadTable();
  };
  document.addEventListener('DOMContentLoaded', () => {
    if (location.hash === '#admission-patterns') loadTable();
  });

  return { show, clear, package: suggestedPackage, openTable };
})();
