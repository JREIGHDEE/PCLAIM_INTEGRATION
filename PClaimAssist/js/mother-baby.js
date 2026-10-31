/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Mother or baby (Patient details)

   A maternity clinic files a claim for the mother and one for her baby,
   and most of the baby's forms repeat the mother's: the PhilHealth
   member (usually the mother), the home address and contact, the
   member's profile and employer. On a claim opened from the logbook
   review this panel:

     - says whether the entry is the mother's or the baby's, as worked
       out from the logbook (Ocr_module/philhealth/mother_baby.py), and
       lets staff change it (Mother / Baby / Neither);
     - for a baby: picks the mother's claim (best match first) and, when
       "Copy the mother's details" is ticked, fills the baby's empty boxes
       from hers. Nothing already filled is replaced. Unticking empties
       what the tick filled in and was not changed since;
     - shows what was applied to whom - the member, the baby, the home -
       and, for a mother, who is who on her claim and which babies copy
       from it.

   Started by js/claim-loader.js (initMotherBaby) once a claim is loaded;
   what was copied is saved with the claim (motherCopyState).
   Needs js/app.js (state, applyFormData, formatDate, showToast,
   logActivity, MEMBER_LOCKED_KEYS).
═══════════════════════════════════════════════════════════ */

const MB_ROLE_LABELS = { mother: 'Mother', baby: 'Baby', other: 'Neither' };
const MB_AMPM_TIME = { amPmAdmitted: 'timeAdmitted', amPmDischarge: 'timeDischarge', amPmDelivery: 'deliveryTime' };

const mb = {
  claimId: null,
  family: null,     // GET /api/claims/<id>/family
  fromMother: null, // GET /api/claims/<id>/from-mother
  copied: null,     // {motherClaimId, values: {key: value copied}} while ticked
  picked: null,     // the mother's claim chosen in the list
  busy: false,
  pendingRole: null, // chosen before the patient is saved (no claim yet)
};

/* Saved with the claim by js/claim-loader.js. */
function motherCopyState() {
  return mb.copied ? { motherClaimId: mb.copied.motherClaimId, values: mb.copied.values } : null;
}

function mbEscape(text) {
  return String(text ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function mbBlank(key, value) {
  if (value === undefined || value === null || value === '' || value === false) return true;
  if (Array.isArray(value)) return value.length === 0;
  // AM/PM starts at "AM": it counts as filled only once there is a time.
  if (MB_AMPM_TIME[key]) return !state.data[MB_AMPM_TIME[key]];
  return false;
}

function mbEmptyValue(key) {
  if (MB_AMPM_TIME[key]) return 'AM';
  const cur = state.data[key];
  return typeof cur === 'boolean' ? false : Array.isArray(cur) ? [] : '';
}

function mbShow(value) {
  if (value === true) return 'Yes';
  if (Array.isArray(value)) return value.join(', ');
  const text = String(value ?? '');
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? formatDate(text) : text;
}

async function mbApi(path, opts) {
  const resp = await fetch(`${PCA_API_BASE}/api/claims/${mb.claimId}${path}`, opts);
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok || !body.success) throw new Error(body.error || `Request failed (${resp.status})`);
  return body;
}

/* The server, without this patient's claim (a baby typed in by hand,
   not saved yet): the mothers' claims, and what one of them gives a baby. */
async function mbGet(path) {
  const resp = await fetch(`${PCA_API_BASE}/api/claims${path}`);
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok || !body.success) throw new Error(body.error || `Request failed (${resp.status})`);
  return body;
}

/* Copy from a mother's claim before this baby's claim exists. */
async function mbCopyUnsaved(motherClaimId) {
  mb.fromMother = await mbGet(`/${motherClaimId}/for-baby`);
  const values = mbApplyFromMother(null);
  mb.copied = { motherClaimId, values };
  mbTagFields();
  updateFormPreviews();
  return Object.keys(values).length;
}

function mbPut(body) {
  return mbApi('/family', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
}

/* ── Copying from the mother's claim ─────────────────────── */

/* Fill the baby's empty boxes from the mother's claim. Returns the values
   put in. Values already copied before (a reopened claim) count as copied
   again while they are unchanged, so they are still undone by unticking. */
function mbApplyFromMother(previous) {
  const put = {};
  const copied = {};
  // The baby is not the member: undo "The patient is the member" first.
  if (state.data.memberIsPatient) {
    put.memberIsPatient = false;
    MEMBER_LOCKED_KEYS.forEach(key => { put[key] = mbEmptyValue(key); });
  }
  mb.fromMother.groups.forEach(group => group.items.forEach(item => {
    const cur = item.key in put ? put[item.key] : state.data[item.key];
    const before = previous && previous[item.key];
    if (before !== undefined && JSON.stringify(cur) === JSON.stringify(before)) {
      put[item.key] = item.value;
      copied[item.key] = item.value;
    } else if (mbBlank(item.key, cur)) {
      put[item.key] = item.value;
      copied[item.key] = item.value;
    }
  }));
  if (Object.keys(put).length) applyFormData(put);
  return copied;
}

/* Empty what the copy filled in and is unchanged since. */
function mbUndoCopy() {
  if (!mb.copied) return;
  const put = {};
  Object.entries(mb.copied.values).forEach(([key, value]) => {
    if (JSON.stringify(state.data[key]) === JSON.stringify(value)) put[key] = mbEmptyValue(key);
  });
  mb.copied = null;
  mbUntagFields();
  if (Object.keys(put).length) applyFormData(put);
}

function mbTagFields() {
  mbUntagFields();
  if (!mb.copied) return;
  Object.keys(mb.copied.values).forEach(key => {
    document.querySelectorAll(`#section-patient [data-autofill="${key}"]`).forEach(el => {
      el.classList.add('mb-copied-field');
      const label = typeof fieldLabelFor === 'function' ? fieldLabelFor(el) : null;
      if (label && !label.querySelector('.mb-tag')) {
        const tag = document.createElement('span');
        tag.className = 'ocr-tag mb-tag';
        tag.textContent = 'From mother';
        tag.title = 'Copied from the mother\'s claim';
        label.appendChild(tag);
      }
    });
  });
}

function mbUntagFields() {
  document.querySelectorAll('.mb-tag').forEach(tag => tag.remove());
  document.querySelectorAll('.mb-copied-field').forEach(el => el.classList.remove('mb-copied-field'));
}

async function mbCopyFrom(motherClaimId, previous) {
  mb.fromMother = await mbApi('/from-mother');
  const values = mbApplyFromMother(previous);
  mb.copied = { motherClaimId, values };
  mbTagFields();
  updateFormPreviews();
  return Object.keys(values).length;
}

/* ── Panel ────────────────────────────────────────────────── */

function mbPanel() {
  let panel = document.getElementById('motherBabyPanel');
  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'motherBabyPanel';
    panel.className = 'pca-card mb-panel mb-3';
    panel.setAttribute('aria-live', 'polite');
    const section = document.getElementById('section-patient');
    const anchor = document.getElementById('claimLoadBanner') || section.querySelector('.section-header');
    anchor.insertAdjacentElement('afterend', panel);
    panel.addEventListener('click', mbOnClick);
    panel.addEventListener('change', mbOnChange);
  }
  return panel;
}

function mbMotherLabel(m) {
  const parts = [m.name || `Claim #${m.claim_id}`];
  if (m.delivery_date) parts.push(`delivered ${formatDate(m.delivery_date)}`);
  else if (m.date_admitted) parts.push(`seen ${formatDate(m.date_admitted)}`);
  return parts.join(' · ');
}

function mbRender() {
  const panel = mbPanel();
  const f = mb.family;
  const role = f.role;
  const detected = f.detected_role
    ? `The logbook entry looks like the <strong>${MB_ROLE_LABELS[f.detected_role].toLowerCase()}'s</strong>: ${mbEscape(f.detected_reason)}.`
    : `${mbEscape(f.detected_reason)}.`;
  const chosenNote = f.role_chosen && f.role_chosen !== f.detected_role
    ? ' <span class="mb-muted">(changed by staff)</span>' : '';

  let html = `
    <div class="mb-head">
      <div>
        <div class="mb-title"><i class="bi bi-people-fill me-2"></i>Mother or baby?</div>
        <div class="mb-muted">${detected}${chosenNote}</div>
      </div>
      <div class="btn-check-group" role="group" aria-label="This patient is">
        ${Object.entries(MB_ROLE_LABELS).map(([value, label]) => `
          <button type="button" class="btn-check-option btn-check-option--sm${role === value ? ' active' : ''}"
                  data-mb-role="${value}" ${mb.busy ? 'disabled' : ''}><i class="bi bi-check-lg"></i>${label}</button>`).join('')}
      </div>
    </div>`;

  if (f.unsaved && role === 'mother') {
    html += `<div class="mb-body mb-muted">Press <strong>Save patient</strong> (below) so her baby's claim can find her and copy her details.</div>`;
  } else if (f.unsaved && role === 'baby' && !f.mothersLoaded) {
    html += `<div class="mb-body mb-muted">Looking for the mothers' claims…</div>`;
  } else if (role === 'baby') html += mbBabyHtml();
  else if (role === 'mother') html += mbMotherHtml();
  panel.innerHTML = html;
  // Mother or baby decides the diagnosis package (js/dx-templates.js).
  if (typeof dxRefreshAll === 'function') dxRefreshAll();
  // ...and the package decides the forms. The wording above only re-checks
  // them when it changes a box, which a baby's wording with blanks left
  // never does, so the forms' list is re-checked here as well.
  if (typeof updateValidationSoon === 'function') updateValidationSoon();
}

function mbBabyHtml() {
  const f = mb.family;
  if (!f.mothers.length) {
    return `<div class="mb-body mb-muted"><i class="bi bi-info-circle me-1"></i>
      No mother's claim found yet. Send the mother's logbook entry to the forms first, then open this baby again.</div>`;
  }
  const listed = id => f.mothers.some(m => m.claim_id === id) ? id : null;
  const selected = (mb.copied && mb.copied.motherClaimId) || listed(mb.picked) || listed(f.mother_claim_id)
    || f.suggested_mother_id || f.mothers[0].claim_id;
  mb.picked = selected;
  const options = f.mothers.map(m => {
    const best = m.claim_id === f.suggested_mother_id ? ' (best match)' : '';
    return `<option value="${m.claim_id}" ${m.claim_id === selected ? 'selected' : ''}>${mbEscape(mbMotherLabel(m) + best)}</option>`;
  }).join('');
  const pick = f.mothers.find(m => m.claim_id === selected);
  const why = pick && pick.reasons.length ? pick.reasons.join(' · ') : 'No match found from the logbook - check it is the right mother';
  const ticked = !!mb.copied;
  return `
    <div class="mb-body">
      <label class="pca-label" for="mbMotherSelect">Mother's claim</label>
      <select class="form-select pca-input" id="mbMotherSelect" ${mb.busy ? 'disabled' : ''}>${options}</select>
      <div class="mb-muted mt-1">${mbEscape(why)}</div>
      <div class="form-check pca-checkbox member-is-patient mt-2">
        <input type="checkbox" class="form-check-input" id="mbCopyTick" ${ticked ? 'checked' : ''} ${mb.busy ? 'disabled' : ''}>
        <label class="form-check-label" for="mbCopyTick">
          <strong>Copy the mother's details</strong> to this baby's claim — the member, home address and contact,
          birth details and who signs for the baby. Boxes already filled are kept.
        </label>
      </div>
      ${ticked ? mbAppliedHtml() : ''}
    </div>`;
}

/* What the tick applied to whom: each group of the mother's values, who
   it is about, and per value whether it was copied or this claim's own
   value was kept. */
function mbAppliedHtml() {
  const copied = mb.copied.values;
  const groups = mb.fromMother.groups.map(group => {
    const rows = group.items.map(item => {
      const now = state.data[item.key];
      let status;
      if (item.key in copied && JSON.stringify(now) === JSON.stringify(copied[item.key])) {
        status = '<span class="mb-chip mb-chip--copied">Copied</span>';
      } else if (item.key in copied) {
        status = '<span class="mb-chip mb-chip--kept">Copied, then changed</span>';
      } else {
        status = `<span class="mb-chip mb-chip--kept" title="The mother's claim has ${mbEscape(mbShow(item.value))}">Kept this claim's own</span>`;
      }
      return `<tr><td>${mbEscape(item.label)}</td><td>${mbEscape(mbShow(mbBlank(item.key, now) ? item.value : now))}</td><td>${status}</td></tr>`;
    }).join('');
    return `
      <div class="mb-group">
        <div class="mb-group-title">${mbEscape(group.title)} <span class="mb-arrow">→</span>
          <span class="mb-who mb-who--${group.who}">${mbEscape(group.who_label)}</span></div>
        <table class="mb-table"><tbody>${rows}</tbody></table>
      </div>`;
  }).join('');
  const count = Object.keys(copied).length;
  return `
    <div class="mb-applied">
      <div class="mb-applied-head"><i class="bi bi-arrow-left-right me-1"></i>
        What was applied to whom (${count} box${count === 1 ? '' : 'es'} filled from the mother's claim)</div>
      ${groups}
    </div>`;
}

function mbMotherHtml() {
  const d = state.data;
  const name = (prefix) => [d[`${prefix}FirstName`], d[`${prefix}MiddleName`], d[`${prefix}LastName`], d[`${prefix}NameExt`]]
    .filter(Boolean).join(' ');
  const patient = name('patient') || '—';
  const member = d.memberIsPatient ? `${patient} (the mother herself)` : (name('member') || 'not filled in yet');
  const birth = [
    d.deliveryDate && `delivered ${formatDate(d.deliveryDate)}`,
    d.babySex && `baby ${d.babySex.toLowerCase()}`,
    d.birthWeight && `${d.birthWeight} g`,
  ].filter(Boolean).join(' · ') || 'not filled in yet';
  const babies = mb.family.babies.length
    ? mb.family.babies.map(b => `<li><a href="index.html?claim=${b.claim_id}">${mbEscape(b.name || `Claim #${b.claim_id}`)}</a></li>`).join('')
    : '<li class="mb-muted">None yet. Open the baby\'s entry, choose Baby and tick "Copy the mother\'s details".</li>';
  return `
    <div class="mb-body">
      <table class="mb-table mb-table--who"><tbody>
        <tr><td><span class="mb-who mb-who--baby">Patient</span></td><td>${mbEscape(patient)} (the mother)</td></tr>
        <tr><td><span class="mb-who mb-who--member">PhilHealth member</span></td><td>${mbEscape(member)}</td></tr>
        <tr><td><span class="mb-who mb-who--home">Her baby's birth</span></td><td>${mbEscape(birth)}</td></tr>
      </tbody></table>
      <div class="mb-muted mt-2">Her baby's claim can copy the member, home address and contact, member profile,
        employer and birth details from this claim. Babies copying from her:</div>
      <ul class="mb-babies">${babies}</ul>
    </div>`;
}

/* ── Actions ─────────────────────────────────────────────── */

async function mbRun(work) {
  if (mb.busy) return;
  mb.busy = true;
  mbRender();
  try {
    await work();
  } catch (err) {
    showToast('Mother and baby', err.message, 'danger');
  } finally {
    mb.busy = false;
    mbRender();
  }
}

function mbOnClick(e) {
  const btn = e.target.closest('[data-mb-role]');
  if (!btn) return;
  const role = btn.dataset.mbRole;
  if (mb.family && mb.family.unsaved) {
    if (mb.family.role === 'baby' && role !== 'baby' && mb.copied) { mbUndoCopy(); updateFormPreviews(); }
    mb.pendingRole = mb.family.role === role ? null : role;
    mb.family.role = mb.pendingRole || '';
    if (mb.family.role === 'baby' && !mb.family.mothersLoaded) {
      mbRun(async () => {
        mb.family.mothers = (await mbGet('/mothers')).mothers;
        mb.family.mothersLoaded = true;
      });
      return;
    }
    mbRender();
    return;
  }
  mbRun(async () => {
    const leavingBaby = mb.family.role === 'baby' && role !== 'baby';
    if (leavingBaby && mb.copied) {
      mbUndoCopy();
      mb.family = await mbPut({ role, mother_claim_id: null });
    } else {
      mb.family = await mbPut({ role });
    }
    logActivity(`Patient marked as ${MB_ROLE_LABELS[role].toLowerCase()} (claim #${mb.claimId})`, 'info');
  });
}

function mbOnChange(e) {
  if (mb.family && mb.family.unsaved) return mbOnChangeUnsaved(e);
  if (e.target.id === 'mbCopyTick') {
    const tick = e.target.checked;
    const select = document.getElementById('mbMotherSelect');
    const motherId = Number(select && select.value);
    mbRun(async () => {
      if (tick) {
        mb.family = await mbPut({ mother_claim_id: motherId });
        const n = await mbCopyFrom(motherId, null);
        showToast('Copied from the mother', `${n} box${n === 1 ? '' : 'es'} filled from the mother's claim.`, 'success');
        logActivity(`Baby's details copied from the mother's claim #${motherId}`, 'success');
      } else {
        mbUndoCopy();
        mb.family = await mbPut({ mother_claim_id: null });
        updateFormPreviews();
        logActivity('Copy from the mother\'s claim undone', 'warning');
      }
    });
  } else if (e.target.id === 'mbMotherSelect' && mb.copied) {
    // A different mother while ticked: undo the first copy, copy hers.
    const motherId = Number(e.target.value);
    mbRun(async () => {
      mbUndoCopy();
      mb.family = await mbPut({ mother_claim_id: motherId });
      await mbCopyFrom(motherId, null);
    });
  } else if (e.target.id === 'mbMotherSelect') {
    mb.picked = Number(e.target.value);
    mbRender();
  }
}

/* The same for a baby not saved yet: copied now, linked on Save patient. */
function mbOnChangeUnsaved(e) {
  const select = document.getElementById('mbMotherSelect');
  const motherId = Number(select && select.value);
  if (e.target.id === 'mbCopyTick') {
    if (e.target.checked) {
      mbRun(async () => {
        const n = await mbCopyUnsaved(motherId);
        showToast('Copied from the mother', `${n} box${n === 1 ? '' : 'es'} filled from the mother's claim.`, 'success');
      });
    } else {
      mbUndoCopy();
      updateFormPreviews();
      mbRender();
    }
  } else if (e.target.id === 'mbMotherSelect') {
    mb.picked = motherId;
    if (mb.copied) mbRun(async () => { mbUndoCopy(); await mbCopyUnsaved(motherId); });
    else mbRender();
  }
}

/* ── Start / stop ────────────────────────────────────────── */

async function initMotherBaby(claimId, saved) {
  const pending = mb.pendingRole;
  const pendingCopy = mb.family && mb.family.unsaved ? mb.copied : null;
  closeMotherBaby();
  mb.claimId = claimId;
  try {
    mb.family = (await mbApi('/family'));
    // Chosen before the patient was saved: now kept with the claim.
    if (pending && !mb.family.role_chosen) mb.family = await mbPut({ role: pending });
    // ...and the mother's claim it copied from, still tracked as copied.
    if (pendingCopy && pending === 'baby') {
      mb.family = await mbPut({ mother_claim_id: pendingCopy.motherClaimId });
      saved = { motherClaimId: pendingCopy.motherClaimId, values: pendingCopy.values };
    }
    // Ticked before: copy again into boxes still empty (the mother's claim
    // may have more filled in since), keeping track of what came from her.
    if (mb.family.role === 'baby' && mb.family.mother_claim_id) {
      const previous = saved && saved.motherClaimId === mb.family.mother_claim_id ? saved.values : null;
      await mbCopyFrom(mb.family.mother_claim_id, previous);
    }
  } catch (err) {
    showToast('Mother and baby', `Could not check mother or baby: ${err.message}`, 'warning');
    return;
  }
  mbRender();
}

function closeMotherBaby() {
  mbUntagFields();
  Object.assign(mb, { claimId: null, family: null, fromMother: null, copied: null, picked: null, busy: false, pendingRole: null });
  const panel = document.getElementById('motherBabyPanel');
  if (panel) panel.remove();
}

/* Keep "what was applied to whom" and the mother's "who is who" in step
   with the forms: every change ends in updateFormPreviews() (js/app.js). */
const updateFormPreviewsBeforeMotherBaby = updateFormPreviews;
updateFormPreviews = function () {
  updateFormPreviewsBeforeMotherBaby.apply(this, arguments);
  if (mb.family && !mb.busy) mbRefreshSoon();
};
let mbRefreshTimer = null;
function mbRefreshSoon() {
  clearTimeout(mbRefreshTimer);
  mbRefreshTimer = setTimeout(() => { if (mb.family && !mb.busy) mbRender(); }, 400);
}

/* A patient typed in by hand, with no claim yet (not from the logbook, not
   saved): the panel still asks mother or baby. The choice is remembered,
   decides the diagnosis package (js/dx-templates.js dxIsBaby), and is
   kept with the claim when it is saved (initMotherBaby). */
function initUnsavedMotherBaby() {
  if (mb.claimId) return;
  mb.family = {
    unsaved: true, role: mb.pendingRole || '', role_chosen: null, detected_role: null,
    detected_reason: 'Not saved yet - choose who this patient is', mothers: [], babies: [],
  };
  mbRender();
}
document.addEventListener('DOMContentLoaded', () => {
  if (!new URLSearchParams(location.search).get('claim')) initUnsavedMotherBaby();
});
// "Start a new patient": after the claim is let go (js/claim-loader.js).
document.addEventListener('pca:new-patient', () => setTimeout(initUnsavedMotherBaby, 0));
