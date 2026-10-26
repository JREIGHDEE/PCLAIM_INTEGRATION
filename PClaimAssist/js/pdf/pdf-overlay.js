/* ═══════════════════════════════════════════════════════════
   PClaimAssist – PDF Rendering & Live Overlay Engine
   Uses PDF.js (render) + pdf-lib (export)
   Privacy-by-design: no server calls.
═══════════════════════════════════════════════════════════ */

/* ── PDF.js worker setup ─────────────────────────────────── */
if (typeof pdfjsLib !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

/* ── Per-form state ──────────────────────────────────────── */
const pdfState = {
  csf:  { doc: null, page: 1, totalPages: 1, rendered: false },
  cf2:  { doc: null, page: 1, totalPages: 2, rendered: false },
  cf4:  { doc: null, page: 1, totalPages: 2, rendered: false },
  pmrf: { doc: null, page: 1, totalPages: 2, rendered: false },
};

/* Every form the PDF layer manages. CF4 is included ahead of the file
   being supplied; until forms/CF4.pdf exists its panel shows the
   standard "PDF not found" state. */
const PDF_FORM_KEYS = ['csf', 'cf2', 'cf4', 'pmrf'];

/* ── Overlay field coordinate maps ──────────────────────────
   OVERLAY_MAP itself is defined in js/pdf/overlays/index.js,
   built from the per-form maps in js/pdf/overlays/{csf,cf2,cf4,pmrf}.js.
   Those files must be loaded before this one (see index.html).
─────────────────────────────────────────────────────────── */

/* ── PDF file paths ──────────────────────────────────────── */
/* ═══════════════════════════════════════════════════════════
   Research design §3.4.2.5 step 10: a PDF is generated only once every
   critical (block_submission) error has been resolved. Set to true only
   to check the printed layout without filling in every box; it must stay
   false in the system that is used and demonstrated. It affects both
   "Save as PDF to print" and saving several forms as one PDF.
═══════════════════════════════════════════════════════════ */
const SKIP_VALIDATION_FOR_EXPORT = false;

/* True (and says why) when a PDF must not be made yet. The rules are run
   again here rather than trusting the last on-screen check, which may not
   have run yet; if they cannot be run at all, nothing is saved. */
function exportBlocked() {
  if (SKIP_VALIDATION_FOR_EXPORT) return false;
  const v = (typeof runValidationRules === 'function' && typeof getComputedValue === 'function' &&
             typeof state !== 'undefined')
    ? runValidationRules(getComputedValue, state.data) : null;
  if (v && v.canGeneratePDF) return false;
  const critical = v ? v.critical : [];
  const n = critical.length;
  const reasons = critical.slice(0, 3).map(c => `${c.id}: ${c.message}`).join(' ');
  showToast('Not ready to print yet', n
    ? `${n} important thing${n === 1 ? ' is' : 's are'} still missing or wrong. ${reasons}` +
      `${n > 3 ? ` …and ${n - 3} more.` : ''} The full list is shown now - fix those, then try again.`
    : 'The missing-information check could not run. Reload the page, then try again.', 'danger');
  if (typeof navigateTo === 'function') navigateTo('validation');
  return true;
}

/* ── One source of truth for preview/export placement ──────
   Both renderers must agree exactly, or the printed form will not match
   what the staff checked on screen.

   BASELINE_OFFSET_PT  how far below a field's `top` the text baseline sits.
   HELVETICA_BASELINE_EM  where the baseline falls inside a line-height:1
     span, from standard Helvetica's own metrics: 1.075 / (1.075 + 0.299).
     The preview is styled in Helvetica (css .pdf-field) so that the glyph
     widths it shows are the widths pdf-lib will print.
═══════════════════════════════════════════════════════════ */
const BASELINE_OFFSET_PT = 6;
const HELVETICA_BASELINE_EM = 1.075 / (1.075 + 0.299);
/* pdf-lib draws wrapped text with this leading, so the preview uses it too. */
const WRAP_LINE_HEIGHT_PT = fs => fs + 1;

const PDF_PATHS = {
  csf:  'forms/CSF.pdf',
  cf2:  'forms/CF2.pdf',
  cf4:  'forms/CF4.pdf?v=2020-02',   // the February 2020 edition
  pmrf: 'forms/PMRF.pdf',
};

/* ── Render a PDF page to a canvas ──────────────────────────
   The canvas and its overlay are sized by CSS to the panel's full width
   (canvas width:100%, overlay inset:0), so when the browser is zoomed or
   the window resized the page scales at once - no dark gap opens around
   it. This function then re-draws it sharp for the new size:
     • drawn off-screen first and copied over when finished, so the
       preview never flashes blank;
     • a newer render cancels an unfinished one (pdf.js refuses two
       renders on one canvas, which used to leave a stale, wrong-sized
       page inside a bigger panel when zooming in several steps);
     • a form whose page is hidden has no width - it is only marked
       "stale" and re-drawn when its page is opened. */
async function renderPDFPage(formKey, pageNum) {
  const st = pdfState[formKey];
  if (!st.doc) return;
  const id = (st.renderId = (st.renderId || 0) + 1);

  const canvas = document.getElementById('canvas-' + formKey);
  const wrap   = document.getElementById('pdf-wrap-' + formKey);
  if (!canvas || !wrap) return;

  const targetW = wrap.clientWidth;
  if (!targetW) {               // page not visible: draw it when it is opened
    st.page  = pageNum;
    st.stale = true;
    return;
  }

  const page = await st.doc.getPage(pageNum);
  if (id !== st.renderId) return;

  const dpr      = window.devicePixelRatio || 1;
  // Never draw below 1x: zoomed out, devicePixelRatio drops under 1.
  const res      = Math.max(dpr, 1);
  const viewport = page.getViewport({ scale: 1 });
  const scaled   = page.getViewport({ scale: targetW / viewport.width });

  const offscreen  = document.createElement('canvas');
  offscreen.width  = Math.floor(scaled.width  * res);
  offscreen.height = Math.floor(scaled.height * res);
  const offCtx = offscreen.getContext('2d');
  // Paint the whole page white first. The zoom factor goes to pdf.js as
  // its `transform` option, NOT via ctx.setTransform: pdf.js fills the
  // page background in the context's own coordinates, so a pre-set scale
  // below 1 left part of the page transparent - the dark panel showed
  // through as a "black box" that grew the more the browser zoomed out.
  offCtx.fillStyle = '#FFFFFF';
  offCtx.fillRect(0, 0, offscreen.width, offscreen.height);

  if (st.renderTask) st.renderTask.cancel();
  const task = (st.renderTask = page.render({
    canvasContext: offCtx,
    viewport: scaled,
    transform: res !== 1 ? [res, 0, 0, res, 0, 0] : null,
  }));
  try {
    await task.promise;
  } catch (err) {
    if (err && err.name === 'RenderingCancelledException') return;
    throw err;
  } finally {
    if (st.renderTask === task) st.renderTask = null;
  }
  if (id !== st.renderId) return;

  canvas.width  = offscreen.width;
  canvas.height = offscreen.height;
  canvas.style.width  = '100%';
  canvas.style.height = 'auto';
  canvas.getContext('2d').drawImage(offscreen, 0, 0);
  st.drawnWidth = targetW;
  st.drawnDpr   = dpr;
  st.stale      = false;

  const overlay = document.getElementById('overlay-' + formKey);
  if (overlay) {
    overlay.style.width  = '100%';
    overlay.style.height = '100%';
  }

  // The page is turned from the foot of the data-entry panel
  // (renderEntryPageNav), which also shows which page is being looked at.
  st.page = pageNum;
  scaleOverlayFonts(formKey);
  updateOverlayForForm(formKey);
  syncEntryPanelPageGroups(formKey, pageNum);
}

/* ── Show only the Data Entry fields for the currently viewed PDF page ── */
function syncEntryPanelPageGroups(formKey, pageNum) {
  const panel = document.querySelector(`#section-${formKey} .entry-panel-body`);
  if (!panel) return;
  // Only some forms keep their boxes in per-page blocks; the turner below
  // is drawn for every form of more than one page either way.
  panel.querySelectorAll('.pdf-page-group[data-pdf-page]').forEach(group => {
    group.hidden = Number(group.dataset.pdfPage) !== pageNum;
  });
  renderEntryPageNav(panel, formKey, pageNum);
  // The page's boxes were out of sight until now, so they were not marked.
  if (typeof refreshRedMarksSoon === 'function') refreshRedMarksSoon();
}

/* ── A page turner at the foot of "Type the details here" ──
   A form of two pages only showed the second page's boxes when the small
   arrows above the preview were used, so the second page was easy to miss
   entirely. The same turn is offered where it is noticed: at the end of
   the boxes, where someone who has filled the last one is looking. */
function renderEntryPageNav(panel, formKey, pageNum) {
  // The form's own page count decides this, not how the boxes happen to be
  // arranged: PMRF shows all of its boxes in one scroll but is still a form
  // of two pages, and the turner moves the preview to the page being
  // checked. A form of one page has nothing to turn to.
  const total = (pdfState[formKey] && pdfState[formKey].totalPages) || 1;
  let nav = panel.querySelector('.entry-page-nav');

  if (total < 2) {
    if (nav) nav.remove();
    return;
  }
  if (!nav) {
    nav = document.createElement('div');
    nav.className = 'entry-page-nav';
    panel.appendChild(nav);
  }
  panel.appendChild(nav);          // always the last thing on the panel

  const back = pageNum > 1
    ? `<button type="button" class="entry-page-btn entry-page-btn--back" data-go="${pageNum - 1}">
         <i class="bi bi-arrow-left" aria-hidden="true"></i> Previous page
       </button>`
    : '<span></span>';
  const forward = pageNum < total
    ? `<button type="button" class="entry-page-btn entry-page-btn--next" data-go="${pageNum + 1}">
         Next page <i class="bi bi-arrow-right" aria-hidden="true"></i>
       </button>`
    : '<span class="entry-page-done">This is the last page of this form.</span>';

  nav.innerHTML =
    `<div class="entry-page-count">Page ${pageNum} of ${total}</div>
     <div class="entry-page-actions">${back}${forward}</div>`;

  nav.querySelectorAll('[data-go]').forEach(btn => {
    btn.addEventListener('click', () => {
      renderPDFPage(formKey, Number(btn.dataset.go));
      panel.scrollTop = 0;
      const head = panel.closest('.form-entry-panel') || panel;
      head.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

/* ── Load PDF and show first page ───────────────────────── */
async function loadFormPDF(formKey) {
  if (!window.pdfjsLib) return;

  const loadingEl = document.getElementById('pdf-loading-' + formKey);
  const wrapEl    = document.getElementById('pdf-wrap-'    + formKey);
  const nofileEl  = document.getElementById('pdf-nofile-'  + formKey);

  if (loadingEl) loadingEl.style.display = '';
  if (wrapEl)    wrapEl.style.display    = 'none';
  if (nofileEl)  nofileEl.style.display  = 'none';

  try {
    const doc = await pdfjsLib.getDocument(PDF_PATHS[formKey]).promise;
    pdfState[formKey].doc        = doc;
    pdfState[formKey].totalPages = doc.numPages;
    pdfState[formKey].rendered   = true;

    if (loadingEl) loadingEl.style.display = 'none';
    if (wrapEl)    wrapEl.style.display    = '';

    injectOverlaySpans(formKey);
    await renderPDFPage(formKey, 1);
  } catch (err) {
    if (loadingEl) loadingEl.style.display = 'none';
    if (nofileEl)  nofileEl.style.display  = '';
    console.warn('[PCA] PDF load failed for', formKey, '–', err.message);
  }
}

/* ── Inject overlay <span> elements into overlay div ────── */
function injectOverlaySpans(formKey) {
  const overlay = document.getElementById('overlay-' + formKey);
  if (!overlay) return;
  overlay.innerHTML = '';

  const PAGE_H = { csf: 936, cf2: 936, cf4: 1008, pmrf: 841.5 };
  const refH = PAGE_H[formKey] || 936;

  (OVERLAY_MAP[formKey] || []).forEach(f => {
    const span = document.createElement('span');
    span.className     = 'pdf-field' + (f.wrap ? ' pdf-field--wrap' : '') + (f.center ? ' pdf-field--center' : '');
    span.id            = 'pof-' + formKey + '-' + f.id;
    span.dataset.page  = f.page;
    const fs = f.fs || 8;
    span.dataset.fsPct = fs / refH;
    /* Line the preview up with what exportFilledPDF actually prints.
       The exporter puts the text BASELINE at (top% of the page) + 6pt,
       so the span has to shift by (6pt - <its own baseline offset>).
       Expressed in em — 6pt is (6 / fs) em — the offset survives the font
       scaling scaleOverlayFonts() applies and stays put as text wraps,
       which a percentage offset would not (it is relative to the span's
       own growing height).

       HELVETICA_BASELINE_EM is the real metric, not a guess: with
       line-height:1 the baseline sits ascent/(ascent+descent) down the
       box, and standard Helvetica's are 1.075 and -0.299. */
    const dy = (BASELINE_OFFSET_PT / fs) - HELVETICA_BASELINE_EM;
    /* A wrapped field gets the same line budget and line height the
       exporter uses, so the preview breaks where the print breaks. */
    const wrapVars = f.wrap
      ? `--pdf-max-lines:${f.maxLines || 8};--pdf-line-height:${(WRAP_LINE_HEIGHT_PT(fs) / fs).toFixed(4)};`
      : '';
    span.style.cssText =
      `top:${f.top}%;left:${f.left}%;width:${f.w}%;transform:translateY(${dy.toFixed(3)}em);${wrapVars}`;
    // Spread over the form's own ruled lines, as the export does
    // (fitOverlayLines sizes it).
    if (f.lines && f.lh) {
      span.dataset.lines = f.lines;
      span.dataset.lhPct = f.lh / refH;
    }
    overlay.appendChild(span);
  });
  scaleOverlayFonts(formKey);
}

/* ── Scale font sizes relative to current canvas height ── */
function scaleOverlayFonts(formKey) {
  const overlay = document.getElementById('overlay-' + formKey);
  if (!overlay) return;
  // The overlay is sized by CSS (100% of the page), so measure it.
  const h = overlay.getBoundingClientRect().height || 800;
  overlay.querySelectorAll('.pdf-field').forEach(span => {
    const fsPct = parseFloat(span.dataset.fsPct) || (8 / 936);
    span.style.fontSize = Math.max(5, Math.round(fsPct * h)) + 'px';
  });
  fitOverlayLines(formKey);
}

/* A value laid onto the form's own ruled lines (CF2's diagnoses): the
   lines are a fixed distance apart on the page, and the words have to fit
   on as many lines as the form has. When they would not, the font is made
   smaller here until it fits - as the export does - instead of running on
   over the next row. */
function fitOverlayLines(formKey) {
  const overlay = document.getElementById('overlay-' + formKey);
  if (!overlay) return;
  const h = overlay.getBoundingClientRect().height || 800;
  overlay.querySelectorAll('.pdf-field[data-lines]').forEach(span => {
    const lineH = parseFloat(span.dataset.lhPct) * h;
    const lines = Number(span.dataset.lines);
    span.style.lineHeight = lineH + 'px';
    let size = Math.max(5, Math.round((parseFloat(span.dataset.fsPct) || (8 / 936)) * h));
    span.style.fontSize = size + 'px';
    span.style.maxHeight = 'none';
    while (span.textContent && span.scrollHeight > lineH * lines + 1 && size > 4) {
      size -= 0.5;
      span.style.fontSize = size + 'px';
    }
  });
}

/* ── Resolve one overlay field's display value ───────────────────
   Supports plain computed/key lookups plus generic field shapes, used to
   avoid a getComputedValue case per field:
     checkbox:true        → '✓' if state.data[f.key] is truthy, or
                             (with checkValue set) equals checkValue
     dateComponent:'MM'|'DD'|'YYYY' → part of an ISO date at state.data[f.key]
     timeComponent:'AM'|'PM'        → bare hh:mm at state.data[f.key],
                             shown only when that period applies
     digit:N               → one character (0-indexed) out of state.data[f.key]
                             (or f.digitKey, if the id differs from the key),
                             digits only — non-digit separators are stripped.
                             With digitOrder:'mmddyyyy', f.digitKey is treated
                             as an ISO "YYYY-MM-DD" date and reordered to
                             MM+DD+YYYY (matching printed mm/dd/yyyy digit boxes)
                             before indexing.
─────────────────────────────────────────────────────────────── */
function resolveOverlayFieldValue(f) {
  const data = window.state?.data || {};

  // A name to be written by hand after printing ("Leave blank", js/app.js).
  if (window.PCA_HANDWRITTEN && window.PCA_HANDWRITTEN.has(f.id)) return '';

  if (f.checkbox) {
    const raw = data[f.key];
    const match = f.checkValue !== undefined ? raw === f.checkValue : !!raw;
    return match ? '✓' : '';
  }

  // checkboxMulti: one box out of a tick-all-that-apply group, where
  // state.data[f.key] is an array of the selected labels (CF4's signs &
  // symptoms and physical-examination findings).
  if (f.checkboxMulti) {
    const raw = data[f.key];
    const list = Array.isArray(raw) ? raw : (raw ? [raw] : []);
    return list.includes(f.checkValue) ? '✓' : '';
  }

  if (f.dateComponent) {
    const parts = (data[f.key] || '').split('-'); // ISO: [YYYY, MM, DD]
    if (f.dateComponent === 'YYYY') return parts[0] || '';
    if (f.dateComponent === 'MM')   return parts[1] || '';
    return parts[2] || '';
  }

  if (f.digit !== undefined) {
    // A stored value, or one worked out from others (e.g. CF4's hhmm).
    const k = f.digitKey || f.key;
    const raw = data[k] || (typeof window.getComputedValue === 'function' ? window.getComputedValue(k) : '') || '';
    let digits;
    if (f.digitOrder === 'mmddyyyy') {
      const parts = raw.split('-'); // ISO: [YYYY, MM, DD]
      digits = (parts[1] || '') + (parts[2] || '') + (parts[0] || '');
    } else {
      digits = raw.replace(/\D/g, '');
    }
    return digits.charAt(f.digit) || '';
  }

  if (f.timeComponent) {
    const raw = data[f.key] || '';
    const h = parseInt(raw.split(':')[0], 10);
    if (isNaN(h)) return '';
    const isPM = h >= 12;
    if ((f.timeComponent === 'PM') !== isPM) return '';
    return typeof window.bareTime === 'function' ? window.bareTime(raw) : raw;
  }

  // amPmCheck: a literal AM/PM checkbox (distinct from timeComponent, which
  // shows the time value itself in whichever of two alternate boxes applies)
  if (f.amPmCheck) {
    const raw = data[f.key] || '';
    const h = parseInt(raw.split(':')[0], 10);
    if (isNaN(h)) return '';
    const isPM = h >= 12;
    return (f.amPmCheck === 'PM') === isPM ? '✓' : '';
  }

  const gcv = window.getComputedValue;
  if (f.computed && typeof gcv === 'function') return gcv(f.computed);
  return data[f.key] || '';
}

/* ── Update overlay text for one form ───────────────────── */
function updateOverlayForForm(formKey) {
  const st      = pdfState[formKey];
  const curPage = st ? st.page : 1;
  const fields  = OVERLAY_MAP[formKey] || [];
  let refit = false;

  fields.forEach(f => {
    const span = document.getElementById('pof-' + formKey + '-' + f.id);
    if (!span) return;

    span.classList.toggle('pdf-field--hidden', f.page !== curPage);

    const val = resolveOverlayFieldValue(f);
    const changed = span.textContent !== val;
    span.textContent = val;
    span.classList.toggle('pdf-field--filled', !!val);
    if (changed && span.dataset.lines) refit = true;

    // Red only where something is still wanted: not a part marked "Not
    // needed" (or otherwise not asked for, app.js keyIsSkipped), and not an
    // empty spot whose answer is already elsewhere - the other options of a
    // tick-one row, the AM box when the time is PM, a digit past the end.
    const key = f.digitKey || f.key;
    const raw = state.data[key];
    const answered = Array.isArray(raw) ? raw.length > 0 : !!raw;
    const skipped = typeof keyIsSkipped === 'function' && keyIsSkipped(formKey, key);
    const missing = !val && !answered && !skipped;
    span.classList.toggle('pdf-field--missing', missing);
    span.dataset.key = key;
  });
  if (refit) fitOverlayLines(formKey);
}

/* Pointing at a red box on the preview says what it still needs; clicking
   it goes to the box where that is typed (app.js focusField), the same
   jump "Fix this" made from the list that used to sit above the boxes. */
(function missingSpotTips() {
  let tip = null;
  const spotAt = e => {
    const span = e.target.closest && e.target.closest('.pdf-field--missing');
    if (!span || span.closest('.pdf-overlay.calibrating')) return null;
    return span;
  };
  const formOf = span => span.closest('.pdf-overlay').id.replace('overlay-', '');
  const place = e => {
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(e.clientX + pad, innerWidth - w - 8) + 'px';
    tip.style.top = (e.clientY + pad + h > innerHeight ? e.clientY - h - pad : e.clientY + pad) + 'px';
  };

  document.addEventListener('mouseover', e => {
    const span = spotAt(e);
    if (!span) return;
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'pdf-missing-tip';
      tip.setAttribute('role', 'tooltip');
      document.body.appendChild(tip);
    }
    const spot = typeof previewSpotLabel === 'function'
      ? previewSpotLabel(formOf(span), span.dataset.key) : { label: span.dataset.key, part: '' };
    tip.innerHTML = '<small></small><strong></strong><span>Still missing. Click to go to this box.</span>';
    tip.querySelector('small').textContent = spot.part;
    tip.querySelector('small').hidden = !spot.part;
    tip.querySelector('strong').textContent = spot.label;
    tip.hidden = false;
    place(e);
  });
  document.addEventListener('mousemove', e => { if (tip && !tip.hidden && spotAt(e)) place(e); });
  document.addEventListener('mouseout', e => { if (tip && spotAt(e)) tip.hidden = true; });
  document.addEventListener('click', e => {
    const span = spotAt(e);
    if (!span) return;
    if (tip) tip.hidden = true;
    if (typeof focusField === 'function') focusField(span.dataset.key);
  });
})();

/* ── Update all form overlays ────────────────────────────── */
function updateAllOverlays() {
  PDF_FORM_KEYS.forEach(key => {
    if (pdfState[key].rendered) updateOverlayForForm(key);
  });
}

/* ── Page navigation ───────────────────────────────────────
   The arrows that used to sit above the preview are gone: the page is
   turned at the foot of "Type the details here", where someone who has
   filled the last box is already looking. */
function setupPageNav() { /* nothing to wire up any more */ }

/* ── Lazy load: only render PDF when its section opens ───── */
function onFormSectionActivated(formKey) {
  const st = pdfState[formKey];
  if (!st.rendered) {
    loadFormPDF(formKey);
  } else if (needsRedraw(formKey)) {
    // Zoomed or resized while this form's page was hidden.
    renderPDFPage(formKey, st.page);
  } else {
    updateOverlayForForm(formKey);
  }
}

/* True when the form's page is visible and was drawn for a different
   width or zoom level than it has now. */
function needsRedraw(formKey) {
  const st   = pdfState[formKey];
  const wrap = document.getElementById('pdf-wrap-' + formKey);
  if (!st.doc || !wrap || !wrap.clientWidth) return false;
  return st.stale || Math.abs(wrap.clientWidth - (st.drawnWidth || 0)) >= 2
      || (window.devicePixelRatio || 1) !== st.drawnDpr;
}

/* ── Fillable PDFs: bake the empty boxes into the page ──────
   (The February 2020 CF4 now in use has no form fields, so this does
   nothing for it; it stays for any fillable form put in forms/.)
   The 2018 CF4.pdf was a fillable form. Its boxes are form fields that sit ABOVE
   the page, and its tick boxes paint a white square - so every value the
   exporter draws on the page was hidden under (or printed beside) the
   box it belonged in. The blank form also came with stale values saved
   in it ("28" in Age). Clear those and flatten the fields into the page
   first; the values are then drawn on top, like CSF and PMRF. */
function flattenBlankForm(pdfDoc) {
  const form = pdfDoc.getForm();
  const fields = form.getFields();
  if (!fields.length) return;
  fields.forEach(field => {
    if (field instanceof PDFLib.PDFTextField) field.setText('');
  });
  form.flatten();
  // flatten() deletes every widget but leaves a few that share a field
  // name listed in their page's /Annots, pointing at nothing; drop those.
  pdfDoc.getPages().forEach(page => {
    const annots = page.node.Annots();
    if (!annots) return;
    for (let i = annots.size() - 1; i >= 0; i--) {
      if (!pdfDoc.context.lookup(annots.get(i))) annots.remove(i);
    }
  });
}

/* ── Export: filled PDF via pdf-lib ─────────────────────── */
/* One form, filled: the blank PDF with every overlay value drawn on it.
   Used for saving a single form and for putting all of them into one
   document (exportAllForms). */
/* ── Make the print clip and wrap the way the screen does ──
   The preview is a CSS box: a plain field is one line with the overflow
   hidden, and a `wrap` field breaks on spaces and stops after maxLines.
   pdf-lib does neither on its own, so these two do it with the very font
   the PDF embeds - the same measurements the browser is now using, since
   .pdf-field is styled in Helvetica too. */
function clipToWidth(text, font, size, maxW) {
  if (font.widthOfTextAtSize(text, size) <= maxW) return text;
  let out = '';
  for (const ch of text) {
    if (font.widthOfTextAtSize(out + ch, size) > maxW) break;
    out += ch;
  }
  return out;
}

function wrapToLines(text, font, size, maxW, maxLines) {
  const lines = [];
  let line = '';
  for (const word of String(text).split(/\s+/).filter(Boolean)) {
    const next = line ? line + ' ' + word : word;
    if (font.widthOfTextAtSize(next, size) <= maxW) {
      line = next;
      continue;
    }
    if (line) lines.push(line);
    if (lines.length >= maxLines) return lines.slice(0, maxLines);
    // A single word too long for the box: clip it rather than overflow.
    line = font.widthOfTextAtSize(word, size) > maxW
      ? clipToWidth(word, font, size, maxW)
      : word;
  }
  if (line && lines.length < maxLines) lines.push(line);
  return lines.slice(0, maxLines);
}

async function buildFilledPdf(formKey) {
  const bytes = await fetch(PDF_PATHS[formKey]).then(r => {
    if (!r.ok) throw new Error('PDF not found: ' + formKey);
    return r.arrayBuffer();
  });
  const pdfDoc = await PDFLib.PDFDocument.load(bytes, { ignoreEncryption: true });
    flattenBlankForm(pdfDoc);
    const pages = pdfDoc.getPages();
    const { StandardFonts } = PDFLib;
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);

    const fields = OVERLAY_MAP[formKey] || [];
    fields.forEach(f => {
      const pg = pages[f.page - 1];
      if (!pg) return;
      const { width, height } = pg.getSize();

      const val = resolveOverlayFieldValue(f);
      if (!val) return;
      // pdf-lib's standard Helvetica uses WinAnsi encoding, which can't
      // represent '✓' — substitute a safe ASCII mark for the exported PDF
      // (the on-screen overlay still renders the real checkmark glyph).
      const safeVal = String(val).replace(/✓/g, 'X');

      const y = height - ((f.top / 100) * height) - BASELINE_OFFSET_PT;
      const boxW = (f.w / 100) * width;
      // A one-line box keeps its value on one line: a long street or
      // subdivision is printed smaller rather than wrapped down into the
      // labels under it. Only boxes made for several lines (`wrap`) wrap.
      let fs = f.fs || 7;
      if (!f.wrap) {
        const wide = font.widthOfTextAtSize(safeVal, fs);
        if (wide > boxW) fs = Math.max(4.5, fs * boxW / wide * 0.98);
      }

      /* Only a `wrap` field may run onto more lines. Everything else is a
         single line in the preview (white-space:nowrap, overflow:hidden),
         so passing maxWidth here would let pdf-lib wrap text the staff saw
         on one line - the printed form would not match the screen. Past
         the smallest size, the rest is clipped rather than overflowing. */
      let text = safeVal;
      if (f.wrap) {
        const lines = wrapToLines(safeVal, font, fs, boxW, f.maxLines || 8);
        text = lines.join('\n');
      } else {
        text = clipToWidth(safeVal, font, fs, boxW);
      }

      // `center` fields (digit cells, tick boxes, a name over a signature
      // line) are centred in the preview by CSS; centre them here too, or
      // every one of them prints hugging the left edge of its box.
      const firstLine = text.split('\n')[0];
      const textW = f.center ? font.widthOfTextAtSize(firstLine, fs) : 0;
      const x = (f.left / 100) * width + (f.center ? Math.max(0, (boxW - textW) / 2) : 0);

      // Ruled lines of their own (`lines` of them, `lh` pt apart, e.g. CF2's
      // diagnoses): the words are laid onto those lines, smaller only if
      // they would need more lines than the form has.
      if (f.lines && f.lh) {
        const layout = size => {
          const rows = [''];
          safeVal.split(/\s+/).forEach(word => {
            const tryRow = rows[rows.length - 1] ? rows[rows.length - 1] + ' ' + word : word;
            if (font.widthOfTextAtSize(tryRow, size) <= boxW || !rows[rows.length - 1]) rows[rows.length - 1] = tryRow;
            else rows.push(word);
          });
          return rows;
        };
        let rows = layout(fs);
        while (rows.length > f.lines && fs > 4.5) rows = layout(fs -= 0.5);
        // A centred field centres each of its lines, as the preview does.
        const left = (f.left / 100) * width;
        rows.forEach((row, i) => pg.drawText(row, {
          x: f.center ? left + Math.max(0, (boxW - font.widthOfTextAtSize(row, fs)) / 2) : x,
          y: y - i * f.lh, size: fs, font: font, color: PDFLib.rgb(0, 0, 0),
        }));
        return;
      }

      pg.drawText(text, {
        x: x,
        y: y,
        size: fs,
        font: font,
        color: PDFLib.rgb(0, 0, 0),
        lineHeight: WRAP_LINE_HEIGHT_PT(fs),
      });
    });

  return pdfDoc;
}

/* `button`: the one pressed - the form's own "Save as PDF to print", or its
   line on the "Check for missing information" page. */
async function exportFilledPDF(formKey, button) {
  if (!window.PDFLib) {
    showToast('Cannot make the PDF right now', 'Check that the computer is connected to the internet, then reload the page.', 'danger');
    return;
  }

  if (exportBlocked()) return;
  const btn = button || document.getElementById('export-' + formKey + '-btn');
  const label = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Making the PDF, please wait…'; }

  try {
    const pdfDoc = await buildFilledPdf(formKey);
    const pdfBytes = await pdfDoc.save();
    const blob = new Blob([pdfBytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${formKey.toUpperCase()}_filled_${Date.now()}.pdf`;
    a.click();
    
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    showToast('PDF saved', `The filled ${formKey.toUpperCase()} was saved to your Downloads folder. Open it there to print.`, 'success');
    // Teach the offline OCR AI which entries are common (js/entry-learning.js).
    if (typeof PCALearning !== 'undefined') PCALearning.recordFormEntries();
    if (typeof reportClaimExported === 'function') reportClaimExported();
  } catch (err) {
    showToast('The PDF could not be made', 'Please try again. If it keeps happening, tell the clinic administrator.', 'danger');
    console.error('[PCA] Export error:', err);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = label; }
  }
}

/* ── Every form, in one document ─────────────────────────
   A claim is not sent one form at a time, so there is one button for the
   lot of it, on the "Check for missing information" page, and it appears
   only once nothing is missing. The forms are put into a single PDF in
   the order they are filed rather than downloaded as four files: a
   browser blocks a burst of downloads, and one document prints in one
   go. */
/* "Check for missing information": tick the forms, press one button. One
   form ticked saves that form; more are saved together as one file. */
function tickedExportForms() {
  return PDF_FORM_KEYS.filter(key =>
    document.querySelector(`[data-export-form="${key}"]`)?.checked);
}

function labelExportButton() {
  const btn = document.getElementById('exportAllBtn');
  const label = document.getElementById('exportAllLabel');
  if (!btn || !label || btn.dataset.busy) return;
  const keys = tickedExportForms();
  const name = key => document.querySelector(`[data-export-form="${key}"]`).dataset.label;
  btn.disabled = !keys.length;
  label.textContent =
    !keys.length ? 'Tick a form to save' :
    keys.length === 1 ? `Save ${name(keys[0])} as PDF` :
    keys.length === PDF_FORM_KEYS.length ? `Save all ${keys.length} forms as one PDF` :
    `Save ${keys.map(name).join(' + ')} as one PDF`;
}

function exportTickedForms() {
  const keys = tickedExportForms();
  if (!keys.length) return;
  const btn = document.getElementById('exportAllBtn');
  return keys.length === 1 ? exportFilledPDF(keys[0], btn) : exportAllForms(keys);
}

document.addEventListener('change', e => {
  if (e.target.matches && e.target.matches('[data-export-form]')) labelExportButton();
});
document.addEventListener('DOMContentLoaded', labelExportButton);

async function exportAllForms(keys) {
  const formKeys = keys && keys.length ? keys : PDF_FORM_KEYS;
  if (!window.PDFLib) {
    showToast('Cannot make the PDF right now',
      'Check that the computer is connected to the internet, then reload the page.', 'danger');
    return;
  }
  if (exportBlocked()) return;

  const btn = document.getElementById('exportAllBtn');
  const label = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Making the forms, please wait…'; }

  try {
    const merged = await PDFLib.PDFDocument.create();
    for (const formKey of formKeys) {
      const filled = await buildFilledPdf(formKey);
      const pages = await merged.copyPages(filled, filled.getPageIndices());
      pages.forEach(page => merged.addPage(page));
    }
    const pdfBytes = await merged.save();
    const blob = new Blob([pdfBytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `PClaimAssist_forms_${claimFileStamp()}.pdf`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    const many = formKeys.length === 1 ? 'The form was' : `${formKeys.length} forms were`;
    showToast(formKeys.length === PDF_FORM_KEYS.length ? 'All forms saved' : 'Forms saved',
      `${many} saved to your Downloads folder as one file. Open it there to print.`, 'success');
    if (typeof PCALearning !== 'undefined') PCALearning.recordFormEntries();
    if (typeof reportClaimExported === 'function') reportClaimExported();
  } catch (err) {
    showToast('The forms could not be made',
      'Please try again. If it keeps happening, tell the clinic administrator.', 'danger');
    console.error('[PCA] Export-all error:', err);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = label; }
  }
}

/* The patient's surname and today's date, so the saved file says whose
   claim it is without having to be opened. */
function claimFileStamp() {
  const data = (typeof state !== 'undefined' && state.data) ? state.data : {};
  const name = String(data.patientLastName || '').trim().replace(/[^A-Za-z0-9]+/g, '');
  const today = new Date();
  const date = today.getFullYear() + '-' +
    String(today.getMonth() + 1).padStart(2, '0') + '-' +
    String(today.getDate()).padStart(2, '0');
  return (name ? name + '_' : '') + date;
}

/* ── Init: setup nav buttons + resize handler ────────────── */
document.addEventListener('DOMContentLoaded', () => {
  PDF_FORM_KEYS.forEach(setupPageNav);
});

let _resizeTimer;
// Browser zoom fires 'resize' too. Only the visible form is re-drawn;
// hidden ones are re-drawn when their page is opened (needsRedraw).
window.addEventListener('resize', () => {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(() => {
    PDF_FORM_KEYS.forEach(key => {
      if (needsRedraw(key)) renderPDFPage(key, pdfState[key].page);
      else if (pdfState[key].rendered) scaleOverlayFonts(key);
    });
  }, 150);
});
/* ── Preview zoom, one setting for every form ──────────────
   Each preview fills its panel's width, so the four forms already show
   at the same scale - but at that size the print is small, and making
   it bigger meant zooming the whole browser, which moved everything
   else too. These buttons enlarge only the page (the panel scrolls
   sideways when it is wider), and the size chosen is kept for every
   form and for the next visit. renderPDFPage re-draws it sharp. */
const PDF_ZOOM_STEPS = [1, 1.25, 1.5, 1.75, 2];
const PDF_ZOOM_STORE = 'pclaimassist.previewZoom';
let pdfZoom = 1;
try {
  const saved = parseFloat(localStorage.getItem(PDF_ZOOM_STORE));
  if (PDF_ZOOM_STEPS.includes(saved)) pdfZoom = saved;
} catch (e) { /* storage blocked: start at fit-to-width */ }

function applyPdfZoom() {
  document.documentElement.style.setProperty('--pdf-zoom', pdfZoom);
  const i = PDF_ZOOM_STEPS.indexOf(pdfZoom);
  document.querySelectorAll('.pdf-zoom').forEach(box => {
    box.querySelector('.pdf-zoom-value').textContent = pdfZoom === 1 ? 'Fit' : Math.round(pdfZoom * 100) + '%';
    box.querySelector('[data-zoom="out"]').disabled = i <= 0;
    box.querySelector('[data-zoom="in"]').disabled = i >= PDF_ZOOM_STEPS.length - 1;
  });
  PDF_FORM_KEYS.forEach(key => {
    if (needsRedraw(key)) renderPDFPage(key, pdfState[key].page);
  });
}

(function setupPdfZoom() {
  document.querySelectorAll('.pdf-panel-toolbar').forEach(bar => {
    if (bar.querySelector('.pdf-zoom')) return;
    const box = document.createElement('div');
    box.className = 'pdf-zoom';
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', 'Preview size');
    box.innerHTML =
      '<button type="button" data-zoom="out" aria-label="Smaller"><i class="bi bi-dash-lg"></i></button>' +
      '<button type="button" data-zoom="fit" class="pdf-zoom-value" title="Fit the page to the panel">Fit</button>' +
      '<button type="button" data-zoom="in" aria-label="Bigger"><i class="bi bi-plus-lg"></i></button>';
    bar.appendChild(box);
  });
  document.addEventListener('click', e => {
    const btn = e.target.closest && e.target.closest('.pdf-zoom button');
    if (!btn) return;
    const i = PDF_ZOOM_STEPS.indexOf(pdfZoom);
    const step = btn.dataset.zoom;
    pdfZoom = step === 'fit' ? 1
            : PDF_ZOOM_STEPS[Math.max(0, Math.min(PDF_ZOOM_STEPS.length - 1, i + (step === 'in' ? 1 : -1)))];
    try { localStorage.setItem(PDF_ZOOM_STORE, String(pdfZoom)); } catch (err) { /* not kept */ }
    applyPdfZoom();
  });
  applyPdfZoom();
})();
