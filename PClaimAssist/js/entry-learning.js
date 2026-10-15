/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Teach the offline OCR AI from the forms

   When the Validation Checker is opened with no critical errors (the
   checking phase), or a form is exported as PDF, the patient's name,
   address and diagnoses are sent to the backend (POST /api/learning/form-entries),
   which counts them in the ocr_known_entries table. The offline AI
   (Ocr_module/paddle_assist.py) then knows which entries are common and
   can suggest them when PaddleOCR misreads a logbook scan.

   Sent once per patient: checking, then exporting CSF, CF2, CF3… for the
   same patient counts their entries only once. Never blocks or slows
   anything.
═══════════════════════════════════════════════════════════ */

const PCALearning = (function () {
  // The form keys the backend learns from (field_catalog.OCR_CATEGORY_KEYS).
  const KEYS = ['patientLastName', 'patientFirstName', 'patientMiddleName',
                'patientAddress', 'admissionDx', 'dischargeDx'];
  let lastSent = null;

  return {
    async recordFormEntries() {
      const data = (window.state && window.state.data) || {};
      const values = {};
      KEYS.forEach(k => { if (typeof data[k] === 'string' && data[k].trim()) values[k] = data[k].trim(); });
      const signature = JSON.stringify(values);
      if (!Object.keys(values).length || signature === lastSent) return;
      lastSent = signature;
      try {
        await fetch((window.PCA_API_BASE || '') + '/api/learning/form-entries', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ values }),
        });
      } catch (err) {
        // Learning is a bonus - a failed request must never bother the user.
        console.warn('[PCA] Could not send form entries for OCR learning:', err);
      }
    },
  };
})();
