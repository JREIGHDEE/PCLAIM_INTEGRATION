/* ═══════════════════════════════════════════════════════════
   PClaimAssist – OCR Workspace (ocr.html only)

   This page hosts the ORIGINAL OCR interface (single source of truth:
   Ocr_module/templates/index.html, served by Flask) inside an
   <iframe>. All upload/crop/template/OCR/review logic lives inside
   that iframe's own document — this file only drives the PClaimAssist
   shell around it (mobile sidebar toggle, iframe load/error state).

   Does NOT read or write window.state / state.data, does NOT call
   navigateTo() / updateFormPreviews() / any validation or PDF-overlay
   logic from js/app.js — this page does not load app.js at all, and
   the iframe's content runs in a fully separate browsing context that
   couldn't reach any of that even by accident.
═══════════════════════════════════════════════════════════ */

const OCR_APP_URL = 'http://127.0.0.1:5000/';
const OCR_LOAD_TIMEOUT_MS = 10000;

/* ── Iframe load / error state ───────────────────────────── */
(function setupOcrIframe() {
  const iframe = document.getElementById('ocrIframe');
  const overlay = document.getElementById('ocrIframeOverlay');
  if (!iframe || !overlay) return;

  let settled = false;

  function showLoaded() {
    if (settled) return;
    settled = true;
    overlay.style.display = 'none';
  }

  function showError() {
    if (settled) return;
    settled = true;
    overlay.classList.add('ocr-iframe-overlay--error');
    overlay.innerHTML = `
      <i class="bi bi-exclamation-triangle-fill"></i>
      <strong>Could not reach the OCR backend</strong>
      <p>Expected it running at <code>${OCR_APP_URL}</code>. Start it with
        <code>run_ocr.bat</code> inside <code>Ocr_module</code>, then reload this page.</p>`;
  }

  iframe.addEventListener('load', showLoaded);
  iframe.addEventListener('error', showError);
  setTimeout(() => { if (!settled) showError(); }, OCR_LOAD_TIMEOUT_MS);

  iframe.src = OCR_APP_URL;
})();

/* ── Mobile sidebar toggle (presentational only — mirrors the
   same class names app.js uses, but is an independent copy so
   this page does not need to load app.js) ─────────────────── */
(function setupMobileSidebar() {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  if (!sidebar || !toggleBtn) return;

  let overlay = document.getElementById('sidebarOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.id = 'sidebarOverlay';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('mobile-open');
      overlay.classList.remove('active');
    });
  }

  toggleBtn.addEventListener('click', () => {
    if (window.innerWidth < 768) {
      sidebar.classList.toggle('mobile-open');
      overlay.classList.toggle('active', sidebar.classList.contains('mobile-open'));
    } else {
      sidebar.classList.toggle('collapsed');
    }
  });
})();
