/* ═══════════════════════════════════════════════════════════
   Combines the per-form overlay coordinate maps (csf.js,
   cf4.js, pmrf.js) into the single OVERLAY_MAP used by
   js/pdf/pdf-overlay.js. Must load after those files and before
   pdf-overlay.js.
═══════════════════════════════════════════════════════════ */
const OVERLAY_MAP = {
  csf:  window.PDF_OVERLAY_CSF,
  cf4:  window.PDF_OVERLAY_CF4,
  pmrf: window.PDF_OVERLAY_PMRF,
};
