/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Saved patients (Patient details, user testing #4)

   Every patient saved with "Save patient" (Check for Missing Information),
   or made a claim from the logbook, in one list above "Mother or baby?",
   to open one again. Folded to one line - "Saved patients (8) · Show
   list" - until opened, so it does not push the form down. Opened: a
   search box (by name) and one line per patient, last saved first, with
   who they are (mother / baby / regular), when admitted, and how far the
   claim is (draft / ready / exported). "Open" loads that patient's claim
   (index.html?claim=<id>, read by js/claim-loader.js); the patient open
   now is marked instead. All / Draft / Ready / Exported show only the
   claims at that stage, each with its count. The bin deletes a patient
   after "Yes, delete" in the line itself - never on one click; the
   patient on screen deleted, the page starts a new one.

   Fetched from GET /api/claims/patients (Ocr_module claims_store
   .list_patients), deleted with DELETE /api/claims/<id>
   (claims_store.delete_patient); asked again after every "Save patient".
═══════════════════════════════════════════════════════════ */
(function setupSavedPatients() {
  const panel = document.getElementById('savedPatientsPanel');
  if (!panel) return;
  const toggle = document.getElementById('savedPatientsToggle');
  const body = document.getElementById('savedPatientsBody');
  const list = document.getElementById('savedPatientsList');
  const search = document.getElementById('savedPatientsSearch');
  const count = document.getElementById('savedPatientsCount');

  const filterBar = document.getElementById('savedPatientsFilter');

  const ROLE = { mother: 'Mother', baby: 'Baby', other: 'Regular' };
  const STATUS = { draft: 'Draft', ready: 'Ready', exported: 'Exported' };
  let patients = null;
  let filter = 'all';         // all / draft / ready / exported
  let confirming = null;      // claim id whose "Delete?" is asked

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const day = iso => {
    if (!iso) return '';
    const d = new Date(String(iso).slice(0, 10) + 'T00:00:00');
    return isNaN(d) ? '' : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };
  const openNow = () => Number(new URLSearchParams(location.search).get('claim')) || null;

  async function load() {
    try {
      const resp = await fetch(`${window.PCA_API_BASE || ''}/api/claims/patients`);
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.success) throw new Error(data.error || `status ${resp.status}`);
      patients = data.patients || [];
    } catch (err) {
      patients = null;
      count.textContent = '';
      list.innerHTML = `<div class="saved-patients-empty">The list could not be loaded (${esc(err.message)}).</div>`;
      return;
    }
    count.textContent = `(${patients.length})`;
    render();
  }

  function render() {
    if (!patients) return;
    // Each filter button with how many it holds.
    filterBar.querySelectorAll('[data-filter]').forEach(btn => {
      const f = btn.dataset.filter;
      const n = f === 'all' ? patients.length : patients.filter(p => p.status === f).length;
      btn.textContent = `${f === 'all' ? 'All' : STATUS[f]} (${n})`;
      btn.classList.toggle('active', f === filter);
      btn.setAttribute('aria-pressed', String(f === filter));
    });
    const want = search.value.trim().toUpperCase();
    const shown = patients.filter(p => (filter === 'all' || p.status === filter) &&
      (!want || String(p.name || '').toUpperCase().includes(want)));
    const current = openNow();
    if (!patients.length) {
      list.innerHTML = '<div class="saved-patients-empty">No saved patients yet. Press <strong>Save patient</strong> ' +
        'on "Check for missing information" and the patient appears here.</div>';
      return;
    }
    if (!shown.length) {
      const what = [filter !== 'all' ? `marked ${STATUS[filter]}` : '', want ? `matching "${esc(search.value.trim())}"` : '']
        .filter(Boolean).join(' and ');
      list.innerHTML = `<div class="saved-patients-empty">No saved patient ${what}.</div>`;
      return;
    }
    // Only an administrator may delete (the server refuses anyone else too).
    const canDelete = (window.currentUser || {}).role === 'admin';
    list.innerHTML = shown.map(p => {
      const isOpen = p.claim_id === current;
      const admitted = day(p.date_admitted);
      const name = esc(p.name || 'this patient');
      // "Delete" asks first, in the line itself: nothing goes on one click.
      const actions = confirming === p.claim_id
        ? `<div class="saved-patient-confirm" role="alert">
             <span>Delete <strong>${name}</strong>? This cannot be undone.</span>
             <button type="button" class="btn btn-danger btn-sm" data-delete-yes="${p.claim_id}">Yes, delete</button>
             <button type="button" class="btn btn-outline-secondary btn-sm" data-delete-no>Cancel</button>
           </div>`
        : `${isOpen
              ? '<span class="saved-patient-here"><i class="bi bi-check2 me-1"></i>Currently Open</span>'
              : `<button type="button" class="btn btn-primary btn-sm" data-open-claim="${p.claim_id}">Open</button>`}
           ${canDelete ? `<button type="button" class="btn btn-outline-danger btn-sm saved-patient-delete" data-delete-claim="${p.claim_id}"
                   title="Delete this patient" aria-label="Delete ${name}"><i class="bi bi-trash3"></i></button>` : ''}`;
      return `
        <div class="saved-patient${isOpen ? ' is-open' : ''}" role="listitem">
          <div class="saved-patient-main">
            <div class="saved-patient-name">${esc(p.name || 'No name yet')}</div>
            <div class="saved-patient-meta">
              ${p.role ? `<span class="saved-patient-role role-${esc(p.role)}">${ROLE[p.role] || esc(p.role)}</span>` : ''}
              ${admitted ? `<span>Admitted ${esc(admitted)}</span>` : ''}
              <span class="saved-patient-status status-${esc(p.status)}">${STATUS[p.status] || esc(p.status)}</span>
            </div>
          </div>
          <div class="saved-patient-actions">${actions}</div>
        </div>`;
    }).join('');
  }

  async function deletePatient(claimId) {
    const patient = (patients || []).find(p => p.claim_id === claimId);
    try {
      const resp = await fetch(`${window.PCA_API_BASE || ''}/api/claims/${claimId}`, { method: 'DELETE' });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.success) throw new Error(data.error || `status ${resp.status}`);
    } catch (err) {
      confirming = null;
      render();
      if (typeof showToast === 'function') showToast('Patient not deleted', err.message, 'danger');
      return;
    }
    const name = (patient && patient.name) || `claim #${claimId}`;
    if (typeof logActivity === 'function') logActivity(`Patient deleted: ${name} (claim #${claimId})`, 'warning');
    if (claimId === openNow()) {
      // The patient on screen is gone: a blank form for a new patient.
      const url = new URL(location.href);
      url.searchParams.delete('claim');
      location.replace(url.toString());
      return;
    }
    if (typeof showToast === 'function') showToast('Patient deleted', `${name} was deleted.`, 'success');
    confirming = null;
    load();
  }

  function setOpen(open) {
    body.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? 'Hide list' : 'Show list';
    if (open) { load(); search.focus(); }
  }

  toggle.addEventListener('click', () => setOpen(body.hidden));
  search.addEventListener('input', render);
  filterBar.addEventListener('click', e => {
    const btn = e.target.closest('[data-filter]');
    if (!btn) return;
    filter = btn.dataset.filter;
    confirming = null;
    render();
  });
  list.addEventListener('click', e => {
    const ask = e.target.closest('[data-delete-claim]');
    if (ask) { confirming = Number(ask.dataset.deleteClaim); render(); return; }
    if (e.target.closest('[data-delete-no]')) { confirming = null; render(); return; }
    const yes = e.target.closest('[data-delete-yes]');
    if (yes) { yes.disabled = true; deletePatient(Number(yes.dataset.deleteYes)); return; }
    const btn = e.target.closest('[data-open-claim]');
    if (!btn) return;
    // The patient open now saves itself on the way out (js/claim-loader.js).
    const url = new URL(location.href);
    url.searchParams.set('claim', btn.dataset.openClaim);
    location.href = url.toString();
  });
  document.addEventListener('pca:patient-saved', load);
  // "Start a new patient": nobody is open now.
  document.addEventListener('pca:new-patient', () => setTimeout(render, 0));

  load();
})();
