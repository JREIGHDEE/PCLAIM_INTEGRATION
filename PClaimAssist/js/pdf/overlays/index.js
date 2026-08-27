/* ═══════════════════════════════════════════════════════════
   Combines the per-form overlay coordinate maps (csf.js, cf2.js,
   cf3.js, pmrf.js) into the single OVERLAY_MAP used by
   js/pdf/pdf-overlay.js. Must load after those files and before
   pdf-overlay.js.
═══════════════════════════════════════════════════════════ */
const OVERLAY_MAP = {
  csf:  window.PDF_OVERLAY_CSF,
  cf2:  window.PDF_OVERLAY_CF2,
  cf3:  window.PDF_OVERLAY_CF3,
  pmrf: window.PDF_OVERLAY_PMRF,
};
