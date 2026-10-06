/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Segmented Box Input
   Renders per-character boxes (PIN / PEN / date groups) that
   stay in sync with a hidden real <input data-autofill> so the
   rest of the app (state.data, PDF overlay, export) is unaffected.
═══════════════════════════════════════════════════════════ */

/* groups: array of digit-group sizes, e.g. [2,9,1] or [2,2,4] */
function initBoxInput(wrapEl) {
  const groups = wrapEl.dataset.groups.split(',').map(Number);
  const totalLen = groups.reduce((a, b) => a + b, 0);
  const targetSelector = wrapEl.dataset.target;
  const realInput = document.querySelector(targetSelector);
  if (!realInput) return;

  const boxes = [];
  groups.forEach((groupSize, gi) => {
    if (gi > 0) {
      const dash = document.createElement('span');
      dash.className = 'box-input-dash';
      dash.textContent = '–';
      wrapEl.appendChild(dash);
    }
    for (let i = 0; i < groupSize; i++) {
      const box = document.createElement('input');
      box.type = 'text';
      box.inputMode = 'numeric';
      box.maxLength = 1;
      box.className = 'box-input-cell';
      box.autocomplete = 'off';
      wrapEl.appendChild(box);
      boxes.push(box);
    }
  });

  function syncFromReal() {
    const val = (realInput.value || '').replace(/\D/g, '').slice(0, totalLen);
    boxes.forEach((box, i) => { box.value = val[i] || ''; });
  }

  function syncToReal() {
    const val = boxes.map(b => b.value).join('');
    realInput.value = val;
    realInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  boxes.forEach((box, i) => {
    box.addEventListener('input', () => {
      box.value = box.value.replace(/\D/g, '').slice(-1);
      syncToReal();
      if (box.value && i < boxes.length - 1) boxes[i + 1].focus();
    });
    box.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !box.value && i > 0) {
        boxes[i - 1].focus();
      } else if (e.key === 'ArrowLeft' && i > 0) {
        boxes[i - 1].focus();
      } else if (e.key === 'ArrowRight' && i < boxes.length - 1) {
        boxes[i + 1].focus();
      }
    });
    box.addEventListener('paste', e => {
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
      if (!text) return;
      let cursor = i;
      for (const ch of text) {
        if (cursor >= boxes.length) break;
        boxes[cursor].value = ch;
        cursor++;
      }
      syncToReal();
      boxes[Math.min(cursor, boxes.length - 1)].focus();
    });
  });

  realInput.addEventListener('input', () => {
    if (boxes.includes(document.activeElement)) return;
    syncFromReal();
  });

  syncFromReal();
}

/* groups: array of digit-group sizes for a date, always [2,2,4] (MM-DD-YYYY),
   backed by a real <input type="date" data-autofill> storing ISO yyyy-mm-dd */
function initDateBoxInput(wrapEl) {
  const targetSelector = wrapEl.dataset.target;
  const realInput = document.querySelector(targetSelector);
  if (!realInput) return;

  const specs = [
    { size: 2, label: 'month' },
    { size: 2, label: 'day' },
    { size: 4, label: 'year' },
  ];
  const groupBoxes = [];

  specs.forEach((spec, gi) => {
    if (gi > 0) {
      const dash = document.createElement('span');
      dash.className = 'box-input-dash';
      dash.textContent = '–';
      wrapEl.appendChild(dash);
    }
    const boxes = [];
    for (let i = 0; i < spec.size; i++) {
      const box = document.createElement('input');
      box.type = 'text';
      box.inputMode = 'numeric';
      box.maxLength = 1;
      box.className = 'box-input-cell';
      box.autocomplete = 'off';
      wrapEl.appendChild(box);
      boxes.push(box);
    }
    groupBoxes.push(boxes);
  });

  const allBoxes = groupBoxes.flat();

  function syncFromReal() {
    const iso = realInput.value || '';
    const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    const mm = m ? m[2] : '';
    const dd = m ? m[3] : '';
    const yyyy = m ? m[1] : '';
    const digits = (mm + dd + yyyy).split('');
    allBoxes.forEach((box, i) => { box.value = digits[i] || ''; });
  }

  function syncToReal() {
    const mm = groupBoxes[0].map(b => b.value).join('');
    const dd = groupBoxes[1].map(b => b.value).join('');
    const yyyy = groupBoxes[2].map(b => b.value).join('');
    if (mm.length === 2 && dd.length === 2 && yyyy.length === 4) {
      realInput.value = `${yyyy}-${mm}-${dd}`;
    } else {
      realInput.value = '';
    }
    realInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  allBoxes.forEach((box, i) => {
    box.addEventListener('input', () => {
      box.value = box.value.replace(/\D/g, '').slice(-1);
      syncToReal();
      if (box.value && i < allBoxes.length - 1) allBoxes[i + 1].focus();
    });
    box.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !box.value && i > 0) {
        allBoxes[i - 1].focus();
      } else if (e.key === 'ArrowLeft' && i > 0) {
        allBoxes[i - 1].focus();
      } else if (e.key === 'ArrowRight' && i < allBoxes.length - 1) {
        allBoxes[i + 1].focus();
      }
    });
    box.addEventListener('paste', e => {
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
      if (!text) return;
      let cursor = i;
      for (const ch of text) {
        if (cursor >= allBoxes.length) break;
        allBoxes[cursor].value = ch;
        cursor++;
      }
      syncToReal();
      allBoxes[Math.min(cursor, allBoxes.length - 1)].focus();
    });
  });

  realInput.addEventListener('input', () => {
    if (allBoxes.includes(document.activeElement)) return;
    syncFromReal();
  });

  syncFromReal();
}

/* 12-hour time as 2 boxed groups (hour, minute), backed by a real
   <input type="time" data-autofill> storing 24-hour HH:MM. AM/PM is
   handled separately by a sibling btn-check-group. */
function initTimeBoxInput(wrapEl) {
  const targetSelector = wrapEl.dataset.target;
  const realInput = document.querySelector(targetSelector);
  if (!realInput) return;

  const specs = [
    { size: 2, label: 'hour' },
    { size: 2, label: 'min' },
  ];
  const groupBoxes = [];

  specs.forEach((spec, gi) => {
    if (gi > 0) {
      const dash = document.createElement('span');
      dash.className = 'box-input-dash';
      dash.textContent = ':';
      wrapEl.appendChild(dash);
    }
    const boxes = [];
    for (let i = 0; i < spec.size; i++) {
      const box = document.createElement('input');
      box.type = 'text';
      box.inputMode = 'numeric';
      box.maxLength = 1;
      box.className = 'box-input-cell';
      box.autocomplete = 'off';
      wrapEl.appendChild(box);
      boxes.push(box);
    }
    groupBoxes.push(boxes);
  });

  const allBoxes = groupBoxes.flat();

  function syncFromReal() {
    const hhmm = realInput.value || '';
    const m = hhmm.match(/^(\d{2}):(\d{2})$/);
    let hh = '', mm = '';
    if (m) {
      let h = parseInt(m[1], 10);
      h = h % 12 || 12;
      hh = String(h).padStart(2, '0');
      mm = m[2];
    }
    const digits = (hh + mm).split('');
    allBoxes.forEach((box, i) => { box.value = digits[i] || ''; });
  }

  function syncToReal() {
    const hh = groupBoxes[0].map(b => b.value).join('');
    const mm = groupBoxes[1].map(b => b.value).join('');
    if (hh.length === 2 && mm.length === 2) {
      const hNum = parseInt(hh, 10);
      if (hNum >= 1 && hNum <= 12) {
        // Preserve whichever AM/PM half the existing 24h value was in,
        // defaulting to AM (00) if unset.
        const prev = realInput.value || '';
        const prevH = parseInt((prev.match(/^(\d{2}):/) || [])[1], 10);
        const wasPM = !isNaN(prevH) && prevH >= 12;
        let h24 = hNum % 12;
        if (wasPM) h24 += 12;
        realInput.value = `${String(h24).padStart(2, '0')}:${mm}`;
      } else {
        realInput.value = '';
      }
    } else {
      realInput.value = '';
    }
    realInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  allBoxes.forEach((box, i) => {
    box.addEventListener('input', () => {
      box.value = box.value.replace(/\D/g, '').slice(-1);
      syncToReal();
      if (box.value && i < allBoxes.length - 1) allBoxes[i + 1].focus();
    });
    box.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !box.value && i > 0) {
        allBoxes[i - 1].focus();
      } else if (e.key === 'ArrowLeft' && i > 0) {
        allBoxes[i - 1].focus();
      } else if (e.key === 'ArrowRight' && i < allBoxes.length - 1) {
        allBoxes[i + 1].focus();
      }
    });
    box.addEventListener('paste', e => {
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
      if (!text) return;
      let cursor = i;
      for (const ch of text) {
        if (cursor >= allBoxes.length) break;
        allBoxes[cursor].value = ch;
        cursor++;
      }
      syncToReal();
      allBoxes[Math.min(cursor, allBoxes.length - 1)].focus();
    });
  });

  realInput.addEventListener('input', () => {
    if (allBoxes.includes(document.activeElement)) return;
    syncFromReal();
  });

  syncFromReal();
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.box-input[data-groups]').forEach(initBoxInput);
  document.querySelectorAll('.box-input-date').forEach(initDateBoxInput);
  document.querySelectorAll('.box-input-time').forEach(initTimeBoxInput);
});
