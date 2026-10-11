/* ═══════════════════════════════════════════════════════════
   POST-OCR CORRECTION REVIEW — UI + state scaffold

   This file owns the *review* half of the correction module
   (research design §3.4.2.3): it displays each suggestion beside
   the original OCR reading with the reason, and requires an
   explicit Accept / Edit / Reject before the value is used.

   It does NOT produce suggestions. The OCR pipeline supplies them
   by calling PCAReview.load(...) with entries shaped like:

     {
       key:        'memberPIN',        // state.data key
       label:      'Member PIN',
       original:   'O2123456789O',     // raw OCR reading
       suggestion: '021234567890',     // may be null = no suggestion
       reason:     'numeric field: O read as 0',
       confidence: 0.72,               // 0..1 OCR field confidence
       correctionConfidence: 0.88      // 0..1, optional
     }

   Confidence routing (Table 3.2) is applied here:
     >= 0.85  high    — accepted as read, still editable
     0.65..0.84 medium — suggestion shown for confirmation
     <  0.65  low     — marked "Manual encoding required"

   Until a staff member resolves an entry, the CONFIRMED value is the
   ORIGINAL reading, never the suggestion — so no validation rule and
   no generated PDF can depend on an unreviewed suggestion.
═══════════════════════════════════════════════════════════ */

const PCAReview = (function () {
  const HIGH = 0.85, LOW = 0.65;

  /* entries: key -> { ...entry, status, confirmedValue } */
  const entries = new Map();

  function tier(conf) {
    if (conf == null) return 'high';
    if (conf >= HIGH) return 'high';
    if (conf >= LOW)  return 'medium';
    return 'low';
  }

  /* The value rules and PDFs may use right now. */
  function confirmedValue(e) {
    if (e.status === 'accepted') return e.suggestion;
    if (e.status === 'edited' || e.status === 'rejected') return e.confirmedValue;
    return e.original; // pending — fall back to the raw reading
  }

  function pendingCount() {
    let n = 0;
    entries.forEach(e => {
      const needsReview = e.tier === 'medium' && e.suggestion && e.suggestion !== e.original;
      if (needsReview && e.status === 'pending') n++;
    });
    return n;
  }

  /* Publish state the rule engine reads (CR-01, CR-02, IQ-01). */
  function publish() {
    window.PCA_OCR_STATE = {
      active: entries.size > 0,
      pendingSuggestions: pendingCount(),
      imageQualityPass: window.PCA_OCR_STATE ? window.PCA_OCR_STATE.imageQualityPass : true,
    };
    if (typeof updateFormPreviews === 'function') updateFormPreviews();
  }

  /* Write a confirmed value into app state. */
  function commit(key, value) {
    if (typeof state === 'undefined') return;
    state.data[key] = value == null ? '' : value;
    document.querySelectorAll(`[data-autofill="${key}"]`).forEach(el => {
      if (el.type === 'radio')         el.checked = el.value === value;
      else if (el.type === 'checkbox') el.checked = !!value;
      else                             el.value   = value == null ? '' : value;
    });
  }

  function load(list, opts) {
    entries.clear();
    (list || []).forEach(raw => {
      const e = Object.assign({}, raw);
      e.tier = tier(e.confidence);
      e.status = 'pending';
      e.confirmedValue = e.original;
      // High-confidence readings are accepted as read; low-confidence
      // values are blanked so staff must encode them by hand.
      if (e.tier === 'high')      commit(e.key, e.original);
      else if (e.tier === 'low')  commit(e.key, '');
      else                        commit(e.key, e.original);
      entries.set(e.key, e);
    });
    if (opts && typeof opts.imageQualityPass === 'boolean') {
      window.PCA_OCR_STATE = Object.assign({}, window.PCA_OCR_STATE,
        { imageQualityPass: opts.imageQualityPass });
    }
    render();
    publish();
  }

  function resolve(key, action, editedValue) {
    const e = entries.get(key);
    if (!e) return;
    if (action === 'accept')      { e.status = 'accepted'; e.confirmedValue = e.suggestion; }
    else if (action === 'reject') { e.status = 'rejected'; e.confirmedValue = e.original; }
    else if (action === 'edit')   { e.status = 'edited';   e.confirmedValue = editedValue; }
    commit(key, confirmedValue(e));
    render();
    publish();
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function render() {
    const host = document.getElementById('ocrReviewList');
    if (!host) return;

    if (!entries.size) {
      host.innerHTML =
        '<p class="text-muted mb-0" style="font-size:.84rem;">' +
        'No OCR results loaded. Extract a logbook row in the OCR workspace to review ' +
        'suggested corrections here.</p>';
      return;
    }

    const rows = [];
    entries.forEach(e => {
      const resolved = e.status !== 'pending';
      const statusBadge =
        e.status === 'accepted' ? '<span class="ocr-badge ocr-badge-ok">Accepted</span>' :
        e.status === 'edited'   ? '<span class="ocr-badge ocr-badge-ok">Edited</span>'   :
        e.status === 'rejected' ? '<span class="ocr-badge ocr-badge-muted">Kept original</span>' :
        e.tier === 'low'        ? '<span class="ocr-badge ocr-badge-danger">Manual encoding required</span>' :
        e.tier === 'medium'     ? '<span class="ocr-badge ocr-badge-warn">Needs review</span>' :
                                  '<span class="ocr-badge ocr-badge-ok">High confidence</span>';

      const pct = e.confidence == null ? '—' : Math.round(e.confidence * 100) + '%';
      const showSuggestion = e.tier === 'medium' && e.suggestion && e.suggestion !== e.original;

      rows.push(`
        <div class="ocr-review-item ${resolved ? 'is-resolved' : ''}" data-key="${esc(e.key)}">
          <div class="ocr-review-head">
            <strong>${esc(e.label || e.key)}</strong>
            ${statusBadge}
            <span class="ocr-conf ms-auto">OCR confidence ${pct}</span>
          </div>

          ${showSuggestion ? `
            <div class="ocr-compare">
              <div class="ocr-side">
                <div class="ocr-side-label">Original reading</div>
                <div class="ocr-side-value ocr-original">${esc(e.original) || '<em>blank</em>'}</div>
              </div>
              <i class="bi bi-arrow-right ocr-arrow"></i>
              <div class="ocr-side">
                <div class="ocr-side-label">Suggested</div>
                <div class="ocr-side-value ocr-suggested">${esc(e.suggestion)}</div>
              </div>
            </div>
            ${e.reason ? `<div class="ocr-reason"><i class="bi bi-info-circle me-1"></i>${esc(e.reason)}</div>` : ''}
            ${resolved ? '' : `
              <div class="ocr-actions">
                <button class="ocr-btn ocr-btn-accept" data-act="accept">Accept</button>
                <button class="ocr-btn ocr-btn-edit"   data-act="edit">Edit</button>
                <button class="ocr-btn ocr-btn-reject" data-act="reject">Reject</button>
              </div>`}
          ` : `
            <div class="ocr-single">
              <span class="ocr-side-label">Value</span>
              <span class="ocr-side-value">${esc(confirmedValue(e)) || '<em>blank — encode manually</em>'}</span>
            </div>
          `}

          ${resolved ? `<div class="ocr-confirmed">Confirmed value: <strong>${esc(confirmedValue(e)) || '(blank)'}</strong></div>` : ''}
        </div>`);
    });

    host.innerHTML = rows.join('');

    host.querySelectorAll('[data-act]').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.closest('.ocr-review-item').dataset.key;
        const act = btn.dataset.act;
        if (act === 'edit') {
          const e = entries.get(key);
          const val = window.prompt(`Enter the correct value for ${e.label || key}:`,
                                    e.suggestion || e.original || '');
          if (val === null) return;
          resolve(key, 'edit', val.trim());
        } else {
          resolve(key, act);
        }
      });
    });
  }

  return {
    load,
    resolve,
    render,
    getConfirmed(key) {
      const e = entries.get(key);
      return e ? confirmedValue(e) : undefined;
    },
    pendingCount,
    setImageQuality(pass) {
      window.PCA_OCR_STATE = Object.assign({}, window.PCA_OCR_STATE, { imageQualityPass: !!pass });
      publish();
    },
    clear() { entries.clear(); render(); publish(); },
  };
})();

window.PCAReview = PCAReview;
document.addEventListener('DOMContentLoaded', () => PCAReview.render());
