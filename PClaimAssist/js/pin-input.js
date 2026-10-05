/* ═══════════════════════════════════════════════════════════
   PClaimAssist – PhilHealth PIN boxes

   A PhilHealth PIN is 12 digits written ##-#########-#. Each patient /
   member PIN input (data-autofill="patientPIN" / "memberPIN") is shown as
   three boxes of 2, 9 and 1 digits that only take numbers, jump to the
   next box when one is full, accept a whole pasted PIN, and say how many
   digits are missing. The original input stays (hidden) as the value
   holder, so js/app.js keeps reading and writing it as before; it calls
   refreshPinBoxes() whenever values change, to keep the boxes in step.
   Load before js/app.js.
═══════════════════════════════════════════════════════════ */
(function setupPinBoxes() {
  const GROUPS = [2, 9, 1];
  const TOTAL = GROUPS.reduce((a, b) => a + b, 0);
  const enhanced = [];

  function digitsOf(value) {
    return String(value || '').replace(/\D/g, '').slice(0, TOTAL);
  }

  function splitDigits(digits) {
    let at = 0;
    return GROUPS.map(len => { const part = digits.slice(at, at + len); at += len; return part; });
  }

  function enhance(input) {
    const label = (input.closest('[class*="col"]') || input.parentElement).querySelector('label');
    const name = label ? label.textContent.replace('*', '').trim() : 'PhilHealth PIN';

    const wrap = document.createElement('div');
    wrap.className = 'pin-boxes';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', `${name}: 12 numbers in three boxes`);

    const boxes = GROUPS.map((len, i) => {
      const box = document.createElement('input');
      box.type = 'text';
      box.inputMode = 'numeric';
      box.autocomplete = 'off';
      // No maxLength: a stray letter would count towards it and push a
      // digit out. Extra digits spill into the next box instead.
      box.className = `form-control pca-input pin-box pin-box--${len}`;
      box.placeholder = '0'.repeat(len);
      box.setAttribute('aria-label', `${name}, part ${i + 1} of 3 (${len} ${len === 1 ? 'number' : 'numbers'})`);
      return box;
    });
    boxes.forEach((box, i) => {
      if (i) {
        const dash = document.createElement('span');
        dash.className = 'pin-dash';
        dash.setAttribute('aria-hidden', 'true');
        dash.textContent = '–';
        wrap.appendChild(dash);
      }
      wrap.appendChild(box);
    });

    const note = document.createElement('div');
    note.className = 'form-hint pin-note';
    note.setAttribute('aria-live', 'polite');
    note.textContent = '12 numbers: 2 – 9 – 1';

    input.type = 'hidden';
    input.after(wrap, note);
    // The old placeholder/format hint under the input is replaced by the boxes.
    const oldHint = note.nextElementSibling;
    if (oldHint && oldHint.classList.contains('form-hint')) oldHint.remove();

    function write() {
      const parts = boxes.map(b => b.value);
      const count = parts.join('').length;
      input.value = count ? parts.filter(Boolean).join('-') : '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      note.classList.remove('pin-note--bad');
      note.textContent = count === 0 || count === TOTAL
        ? '12 numbers: 2 – 9 – 1'
        : `${count} of 12 numbers typed`;
    }

    function onlyNumbersNote() {
      note.classList.add('pin-note--bad');
      note.textContent = 'Only numbers can go in the PIN.';
    }

    function fill(digits, from) {
      // Spread digits across the boxes, starting at box `from`.
      let rest = digits;
      for (let i = from; i < boxes.length && rest; i++) {
        boxes[i].value = rest.slice(0, GROUPS[i]);
        rest = rest.slice(GROUPS[i]);
      }
    }

    boxes.forEach((box, i) => {
      box.addEventListener('input', () => {
        const cleaned = box.value.replace(/\D/g, '');
        const hadLetters = cleaned !== box.value.replace(/\s/g, '');
        if (cleaned.length > GROUPS[i]) fill(cleaned, i); else box.value = cleaned;
        const typed = cleaned.length > GROUPS[i];
        write();
        if (hadLetters) onlyNumbersNote();
        if (typed) {
          // Digits spilled over: carry on in the first box that isn't full.
          const next = boxes.find((b, k) => b.value.length < GROUPS[k]);
          (next || boxes[boxes.length - 1]).focus();
        } else if (box.value.length === GROUPS[i] && boxes[i + 1]) {
          boxes[i + 1].focus();
        }
      });
      box.addEventListener('keydown', e => {
        if (e.key === 'Backspace' && !box.value && boxes[i - 1]) {
          boxes[i - 1].focus();
        }
      });
      box.addEventListener('paste', e => {
        const digits = digitsOf((e.clipboardData || window.clipboardData).getData('text'));
        if (!digits) return;
        e.preventDefault();
        fill(digits, digits.length >= TOTAL ? 0 : i);
        write();
      });
      box.addEventListener('blur', () => {
        const count = boxes.map(b => b.value).join('').length;
        if (count && count < TOTAL && !wrap.contains(document.activeElement)) {
          note.classList.add('pin-note--bad');
          note.textContent = `The PIN needs 12 numbers — ${TOTAL - count} more to type.`;
        }
      });
    });

    enhanced.push({ input, boxes });
  }

  window.refreshPinBoxes = function refreshPinBoxes() {
    enhanced.forEach(({ input, boxes }) => {
      if (boxes.includes(document.activeElement)) return; // don't fight the typist
      splitDigits(digitsOf(input.value)).forEach((part, i) => { boxes[i].value = part; });
    });
  };

  document.querySelectorAll('input[data-autofill="patientPIN"], input[data-autofill="memberPIN"]').forEach(enhance);
})();
