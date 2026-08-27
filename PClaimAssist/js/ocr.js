/* ═══════════════════════════════════════════════════════════
   PClaimAssist – OCR Workspace (ocr.html only)

   Fully self-contained: does NOT read or write window.state / state.data,
   does NOT call navigateTo() / updateFormPreviews() / any validation or
   PDF-overlay logic from js/app.js. This page does not load app.js at all.

   Talks to the already-tested Flask OCR backend at OCR_API_URL. Does not
   map results onto any PhilHealth form and does not modify Flask code.
═══════════════════════════════════════════════════════════ */

const OCR_API_URL = 'http://127.0.0.1:5000/api/ocr';
const OCR_ALLOWED_EXT = ['.png', '.jpg', '.jpeg', '.pdf'];
const OCR_MAX_SIZE_BYTES = 20 * 1024 * 1024; // mirrors the backend's default OCR_MAX_UPLOAD_MB

const ocrState = {
  file: null,
  status: 'idle', // idle | processing | success | error
};

/* ── DOM refs ─────────────────────────────────────────────── */
const dropZone      = document.getElementById('ocrDropZone');
const fileInput     = document.getElementById('ocrFileInput');
const fileChipWrap   = document.getElementById('ocrFileChip');
const categoryInput  = document.getElementById('ocrCategory');
const runBtn          = document.getElementById('ocrRunBtn');
const statusPill        = document.getElementById('ocrStatusPill');
const processingBlock    = document.getElementById('ocrProcessingBlock');
const errorBlock          = document.getElementById('ocrErrorBlock');
const resultsWrap           = document.getElementById('ocrResultsWrap');
const rawTextEl               = document.getElementById('ocrRawText');
const tokenTableBody            = document.getElementById('ocrTokenTableBody');
const emptyState                  = document.getElementById('ocrEmptyState');

/* ── Utilities ────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function fmtBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  return { pdf: 'bi-file-earmark-pdf-fill', png: 'bi-file-earmark-image-fill', jpg: 'bi-file-earmark-image-fill', jpeg: 'bi-file-earmark-image-fill' }[ext] || 'bi-file-earmark-fill';
}

function confidenceClass(conf) {
  const c = Number(conf) || 0;
  if (c >= 0.85) return 'confidence-badge--high';
  if (c >= 0.6) return 'confidence-badge--mid';
  return 'confidence-badge--low';
}

/* ── Status pill rendering ───────────────────────────────── */
function setStatus(status, label) {
  ocrState.status = status;
  statusPill.className = 'ocr-status ocr-status--' + status;
  statusPill.innerHTML = `<span class="dot"></span>${escHtml(label)}`;
}
setStatus('idle', 'Waiting for a file');

/* ── File selection ──────────────────────────────────────── */
function validateFile(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!OCR_ALLOWED_EXT.includes(ext)) {
    return `"${file.name}" is not a supported type. Allowed: ${OCR_ALLOWED_EXT.join(', ')}`;
  }
  if (file.size > OCR_MAX_SIZE_BYTES) {
    return `"${file.name}" is too large (${fmtBytes(file.size)}). Maximum is ${fmtBytes(OCR_MAX_SIZE_BYTES)}.`;
  }
  return null;
}

function selectFile(file) {
  const problem = validateFile(file);
  if (problem) {
    showError(problem);
    return;
  }
  ocrState.file = file;
  hideError();
  renderFileChip();
  clearResults();
  setStatus('idle', 'Ready to process');
  runBtn.disabled = false;
}

function clearFile() {
  ocrState.file = null;
  fileInput.value = '';
  fileChipWrap.innerHTML = '';
  fileChipWrap.style.display = 'none';
  runBtn.disabled = true;
  setStatus('idle', 'Waiting for a file');
}

function renderFileChip() {
  const file = ocrState.file;
  fileChipWrap.style.display = '';
  fileChipWrap.innerHTML = `
    <div class="ocr-file-chip">
      <i class="bi ${fileIcon(file.name)}"></i>
      <div>
        <div class="name">${escHtml(file.name)}</div>
        <div class="size">${fmtBytes(file.size)}</div>
      </div>
      <button type="button" class="remove-btn" title="Remove file"><i class="bi bi-x-lg"></i></button>
    </div>`;
  fileChipWrap.querySelector('.remove-btn').addEventListener('click', clearFile);
}

/* ── Drop zone wiring ─────────────────────────────────────── */
dropZone.addEventListener('click', () => fileInput.click());
['dragenter', 'dragover'].forEach(evt =>
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('drag-over'); }));
['dragleave', 'drop'].forEach(evt =>
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); }));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) selectFile(file);
});
fileInput.addEventListener('change', () => {
  const file = fileInput.files && fileInput.files[0];
  if (file) selectFile(file);
});

/* ── Results rendering ───────────────────────────────────── */
function clearResults() {
  resultsWrap.style.display = 'none';
  rawTextEl.textContent = '';
  tokenTableBody.innerHTML = '';
  emptyState.style.display = '';
}

function renderResults(data) {
  emptyState.style.display = 'none';
  resultsWrap.style.display = '';
  rawTextEl.textContent = data.raw_text || '(no text extracted)';

  const tokens = Array.isArray(data.tokens) ? data.tokens : [];
  if (!tokens.length) {
    tokenTableBody.innerHTML = `<tr><td colspan="3" class="text-muted">No individual tokens returned.</td></tr>`;
    return;
  }
  tokenTableBody.innerHTML = tokens.map(t => `
    <tr>
      <td>${escHtml(t.text ?? '')}</td>
      <td><span class="confidence-badge ${confidenceClass(t.confidence)}">${(Number(t.confidence) || 0).toFixed(2)}</span></td>
      <td class="text-muted">${escHtml(t.category ?? '')}</td>
    </tr>`).join('');
}

/* ── Error rendering ──────────────────────────────────────── */
function showError(message) {
  errorBlock.style.display = '';
  errorBlock.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i>${escHtml(message)}`;
}
function hideError() {
  errorBlock.style.display = 'none';
  errorBlock.innerHTML = '';
}

/* ── Submit to the OCR backend ────────────────────────────── */
async function runOcr() {
  if (!ocrState.file) return;

  hideError();
  clearResults();
  runBtn.disabled = true;
  processingBlock.style.display = '';
  setStatus('processing', 'Processing…');

  const formData = new FormData();
  formData.append('image', ocrState.file);
  const category = categoryInput.value.trim();
  if (category) formData.append('category', category);

  try {
    const response = await fetch(OCR_API_URL, {
      method: 'POST',
      body: formData,
    });

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(`OCR server returned an unexpected (non-JSON) response — HTTP ${response.status}.`);
    }

    if (!response.ok || !data.success) {
      throw new Error(data.error || `OCR request failed — HTTP ${response.status}.`);
    }

    setStatus('success', 'Extraction complete');
    renderResults(data);
  } catch (err) {
    setStatus('error', 'Failed');
    const isNetworkError = err instanceof TypeError;
    const message = isNetworkError
      ? `Could not reach the OCR server at ${OCR_API_URL}. Make sure the backend is running ` +
        `(run_ocr.bat inside my_ocr_project) and check the browser console for CORS or network errors.`
      : err.message;
    showError(message);
  } finally {
    processingBlock.style.display = 'none';
    runBtn.disabled = false;
  }
}

runBtn.addEventListener('click', runOcr);
runBtn.disabled = true;

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
