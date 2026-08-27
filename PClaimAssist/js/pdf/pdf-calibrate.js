/* ═══════════════════════════════════════════════════════════
   PClaimAssist – PDF Overlay Calibration Tool
   Drag/resize overlay fields directly on the live PDF preview
   to fine-tune top/left/w %, then export the updated coordinates
   to paste back into js/pdf/overlays/{form}.js.
   Depends on: pdf-overlay.js (pdfState, OVERLAY_MAP, injectOverlaySpans,
   updateOverlayForForm) having already loaded.
═══════════════════════════════════════════════════════════ */

const FORM_KEYS = ['csf', 'cf2', 'cf3', 'pmrf'];
const calibrate = {
  active:    {},   // formKey -> bool
  overrides: {},   // formKey -> { fieldId: {top,left,w} }
  selected:  {},   // formKey -> fieldId
};
FORM_KEYS.forEach(k => { calibrate.overrides[k] = {}; });

function getField(formKey, fieldId) {
  return (OVERLAY_MAP[formKey] || []).find(f => f.id === fieldId);
}

function currentCoords(formKey, fieldId) {
  const base = getField(formKey, fieldId) || {};
  const ov   = calibrate.overrides[formKey][fieldId] || {};
  return {
    top:  ov.top  !== undefined ? ov.top  : base.top,
    left: ov.left !== undefined ? ov.left : base.left,
    w:    ov.w    !== undefined ? ov.w    : base.w,
  };
}

function setReadout(formKey, text) {
  const el = document.getElementById('calibrate-readout-' + formKey);
  if (el) el.textContent = text;
}

function selectField(formKey, fieldId) {
  const overlay = document.getElementById('overlay-' + formKey);
  if (!overlay) return;
  overlay.querySelectorAll('.pdf-field--selected').forEach(s => s.classList.remove('pdf-field--selected'));
  calibrate.selected[formKey] = fieldId;
  const span = document.getElementById('pof-' + formKey + '-' + fieldId);
  if (span) span.classList.add('pdf-field--selected');
  const c = currentCoords(formKey, fieldId);
  setReadout(formKey, `${fieldId}  top:${c.top.toFixed(2)}%  left:${c.left.toFixed(2)}%  w:${c.w.toFixed(2)}%  (arrow keys to nudge, +/- to resize)`);
}

/* ── Enter/exit calibration mode for a form ─────────────────── */
function toggleCalibrate(formKey) {
  const overlay = document.getElementById('overlay-' + formKey);
  const bar     = document.getElementById('calibrate-bar-' + formKey);
  const btn     = document.getElementById(formKey + '-calibrate-btn');
  if (!overlay) return;

  const nowActive = !calibrate.active[formKey];
  calibrate.active[formKey] = nowActive;
  overlay.classList.toggle('calibrating', nowActive);
  if (bar) bar.style.display = nowActive ? 'flex' : 'none';
  if (btn) btn.classList.toggle('calibrate-active', nowActive);

  if (nowActive) {
    ensureResizeHandles(formKey);
    labelFieldsForCalibration(formKey);
    setReadout(formKey, 'Click a field to select, drag to move, drag right edge to resize.');
  } else {
    calibrate.selected[formKey] = null;
    updateOverlayForForm(formKey);
  }
}

/* ── Add a resize handle + click-select wiring to each field span ── */
function ensureResizeHandles(formKey) {
  const overlay = document.getElementById('overlay-' + formKey);
  if (!overlay) return;
  overlay.querySelectorAll('.pdf-field').forEach(span => {
    if (span.querySelector('.pdf-field-resize')) return;
    const handle = document.createElement('div');
    handle.className = 'pdf-field-resize';
    handle.addEventListener('mousedown', e => startResize(e, formKey, span));
    span.appendChild(handle);
    span.addEventListener('mousedown', e => {
      if (e.target === handle) return;
      startDrag(e, formKey, span);
    });
  });
}

/* ── While calibrating, show field id text so empty fields are visible ── */
function labelFieldsForCalibration(formKey) {
  const fields = OVERLAY_MAP[formKey] || [];
  fields.forEach(f => {
    const span = document.getElementById('pof-' + formKey + '-' + f.id);
    if (!span) return;
    if (!span.textContent || !span.textContent.trim()) {
      span.textContent = f.id;
    }
  });
}

/* ── Drag to reposition (top/left) ──────────────────────────── */
function startDrag(e, formKey, span) {
  if (!calibrate.active[formKey]) return;
  e.preventDefault();
  const overlay  = document.getElementById('overlay-' + formKey);
  const rect     = overlay.getBoundingClientRect();
  const fieldId  = span.id.replace('pof-' + formKey + '-', '');
  selectField(formKey, fieldId);

  const startX = e.clientX, startY = e.clientY;
  const startCoords = currentCoords(formKey, fieldId);

  function onMove(ev) {
    const dxPct = ((ev.clientX - startX) / rect.width)  * 100;
    const dyPct = ((ev.clientY - startY) / rect.height) * 100;
    const top  = Math.max(0, startCoords.top  + dyPct);
    const left = Math.max(0, startCoords.left + dxPct);
    applyCoords(formKey, fieldId, { top, left });
  }
  function onUp() {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  }
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

/* ── Drag right edge to resize width ────────────────────────── */
function startResize(e, formKey, span) {
  if (!calibrate.active[formKey]) return;
  e.preventDefault();
  e.stopPropagation();
  const overlay  = document.getElementById('overlay-' + formKey);
  const rect     = overlay.getBoundingClientRect();
  const fieldId  = span.id.replace('pof-' + formKey + '-', '');
  selectField(formKey, fieldId);

  const startX = e.clientX;
  const startCoords = currentCoords(formKey, fieldId);

  function onMove(ev) {
    const dxPct = ((ev.clientX - startX) / rect.width) * 100;
    const w = Math.max(2, startCoords.w + dxPct);
    applyCoords(formKey, fieldId, { w });
  }
  function onUp() {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  }
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

/* ── Apply new coords: update override, span style, readout ───── */
function applyCoords(formKey, fieldId, patch) {
  const c = currentCoords(formKey, fieldId);
  const next = { ...c, ...patch };
  calibrate.overrides[formKey][fieldId] = next;

  const span = document.getElementById('pof-' + formKey + '-' + fieldId);
  if (span) {
    span.style.top   = next.top   + '%';
    span.style.left  = next.left  + '%';
    span.style.width = next.w     + '%';
  }
  setReadout(formKey, `${fieldId}  top:${next.top.toFixed(2)}%  left:${next.left.toFixed(2)}%  w:${next.w.toFixed(2)}%  (arrow keys to nudge, +/- to resize)`);
}

/* ── Keyboard nudge for the selected field ──────────────────── */
document.addEventListener('keydown', e => {
  const formKey = FORM_KEYS.find(k => calibrate.active[k] && calibrate.selected[k]);
  if (!formKey) return;
  const fieldId = calibrate.selected[formKey];
  const step = e.shiftKey ? 1 : 0.1;

  let patch = null;
  if (e.key === 'ArrowUp')    patch = { top:  Math.max(0, currentCoords(formKey, fieldId).top  - step) };
  if (e.key === 'ArrowDown')  patch = { top:  currentCoords(formKey, fieldId).top  + step };
  if (e.key === 'ArrowLeft')  patch = { left: Math.max(0, currentCoords(formKey, fieldId).left - step) };
  if (e.key === 'ArrowRight') patch = { left: currentCoords(formKey, fieldId).left + step };
  if (e.key === '+' || e.key === '=') patch = { w: currentCoords(formKey, fieldId).w + step };
  if (e.key === '-' || e.key === '_') patch = { w: Math.max(2, currentCoords(formKey, fieldId).w - step) };

  if (patch) {
    e.preventDefault();
    applyCoords(formKey, fieldId, patch);
  }
});

/* ── Reset all overrides for a form back to source coordinates ── */
function resetCalibration(formKey) {
  calibrate.overrides[formKey] = {};
  calibrate.selected[formKey] = null;
  injectOverlaySpans(formKey);
  ensureResizeHandles(formKey);
  labelFieldsForCalibration(formKey);
  setReadout(formKey, 'Reset to source coordinates.');
}

/* ── Build the updated OVERLAY_MAP source text for copy/paste ── */
function buildCalibratedSource(formKey) {
  const fields = OVERLAY_MAP[formKey] || [];
  const varName = 'PDF_OVERLAY_' + formKey.toUpperCase();
  const lines = [`window.${varName} = [`];

  fields.forEach(f => {
    const c = currentCoords(formKey, f.id);
    const parts = [
      `id:'${f.id}'`,
      `key:'${f.key}'`,
      `page:${f.page}`,
      `top:${round2(c.top)}`,
      `left:${round2(c.left)}`,
      `w:${round2(c.w)}`,
      `fs:${f.fs || 8}`,
    ];
    if (f.computed) parts.push(`computed:'${f.computed}'`);
    lines.push(`  { ${parts.join(', ')} },`);
  });

  lines.push('];');
  return lines.join('\n');
}

function round2(n) {
  return Math.round(n * 100) / 100;
}

/* ── Export overrides as pasteable source, shown in a modal ─── */
function exportCalibration(formKey) {
  const src = buildCalibratedSource(formKey);
  showCalibrationModal(formKey, src);
}

function showCalibrationModal(formKey, src) {
  let modal = document.getElementById('calibrate-export-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'calibrate-export-modal';
    modal.style.cssText = 'position:fixed;inset:0;z-index:2000;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:2rem;';
    modal.innerHTML = `
      <div style="background:#0F172A;color:#E5E7EB;border-radius:8px;max-width:720px;width:100%;max-height:80vh;display:flex;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.5);">
        <div style="padding:.8rem 1rem;border-bottom:1px solid #1E293B;font-family:sans-serif;font-weight:700;font-size:.85rem;display:flex;justify-content:space-between;align-items:center;">
          <span id="calibrate-modal-title">Calibrated coordinates</span>
          <button id="calibrate-modal-close" style="background:none;border:none;color:#94A3B8;font-size:1.1rem;cursor:pointer;">&times;</button>
        </div>
        <textarea id="calibrate-modal-textarea" readonly style="flex:1;min-height:320px;background:#020617;color:#BEF264;border:none;padding:1rem;font-family:'Courier New',monospace;font-size:.78rem;resize:vertical;"></textarea>
        <div style="padding:.6rem 1rem;border-top:1px solid #1E293B;display:flex;justify-content:flex-end;gap:.5rem;">
          <button id="calibrate-modal-copy" style="background:#16A34A;color:#fff;border:none;border-radius:6px;padding:.4rem .9rem;font-size:.8rem;cursor:pointer;">Copy to clipboard</button>
        </div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelector('#calibrate-modal-close').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
  }
  modal.querySelector('#calibrate-modal-title').textContent =
    `Calibrated coordinates — ${formKey.toUpperCase()} (paste into js/pdf/overlays/${formKey}.js)`;
  const ta = modal.querySelector('#calibrate-modal-textarea');
  ta.value = src;
  modal.querySelector('#calibrate-modal-copy').onclick = async () => {
    ta.select();
    try {
      await navigator.clipboard.writeText(src);
      showToast && showToast('Copied', 'Coordinates copied to clipboard.', 'success');
    } catch (err) {
      /* clipboard API may be unavailable (e.g. file:// origin) — text is already selected for manual copy */
    }
  };
}

/* ── Inject calibrate button + bar into each form's PDF panel ── */
function setupCalibrationUI(formKey) {
  const toolbar = document.querySelector(`#pdf-wrap-${formKey}`)?.closest('.pdf-preview-panel')?.querySelector('.pdf-panel-toolbar > .d-flex');
  const wrap    = document.getElementById('pdf-wrap-' + formKey);
  if (!toolbar || !wrap) return;

  const btn = document.createElement('button');
  btn.className = 'pdf-nav-btn';
  btn.id = formKey + '-calibrate-btn';
  btn.title = 'Calibrate overlay alignment';
  btn.innerHTML = '<i class="bi bi-bullseye"></i>';
  btn.addEventListener('click', () => toggleCalibrate(formKey));
  toolbar.appendChild(btn);

  const bar = document.createElement('div');
  bar.className = 'pdf-calibrate-bar';
  bar.id = 'calibrate-bar-' + formKey;
  bar.style.display = 'none';
  bar.innerHTML = `
    <span class="calibrate-readout" id="calibrate-readout-${formKey}">Click a field to select</span>
    <button id="calibrate-copy-${formKey}">Copy Coordinates</button>
    <button class="calibrate-danger" id="calibrate-reset-${formKey}">Reset</button>`;
  wrap.appendChild(bar);

  bar.querySelector('#calibrate-copy-' + formKey).addEventListener('click', () => exportCalibration(formKey));
  bar.querySelector('#calibrate-reset-' + formKey).addEventListener('click', () => resetCalibration(formKey));
}

document.addEventListener('DOMContentLoaded', () => {
  FORM_KEYS.forEach(setupCalibrationUI);
});

/* ── Re-apply calibration labels/handles after page nav or resize ── */
const _origRenderPDFPage = window.renderPDFPage;
window.renderPDFPage = async function (formKey, pageNum) {
  await _origRenderPDFPage(formKey, pageNum);
  if (calibrate.active[formKey]) {
    ensureResizeHandles(formKey);
    labelFieldsForCalibration(formKey);
  }
};
