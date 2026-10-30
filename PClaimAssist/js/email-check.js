/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Is that email address real?

   Asks the backend (POST /api/settings/check-email) a short moment
   after typing stops. The backend checks how it is written and whether
   the part after the @ exists, by looking up the domain's mail servers.

   Nothing is sent to the address, and nothing is sent to a company
   outside: the patient's email never leaves this computer.

   A wrong address is said plainly under the box and never blocks
   typing - the staff decide, the system only points.
═══════════════════════════════════════════════════════════ */
(function setupEmailCheck() {
  const boxes = Array.from(document.querySelectorAll('input[type="email"][data-autofill]'));
  if (!boxes.length) return;

  const API = (window.PCA_API_BASE || '') + '/api/settings/check-email';
  const WAIT_MS = 600;
  const seen = new Map();          // address -> result, so it is asked once

  function noteFor(box) {
    let note = box.parentNode.querySelector('.pca-email-note');
    if (!note) {
      note = document.createElement('div');
      note.className = 'pca-email-note';
      box.insertAdjacentElement('afterend', note);
    }
    return note;
  }

  function show(box, result) {
    const note = noteFor(box);
    box.classList.toggle('is-email-bad', result && result.ok === false);
    if (!result || result.ok) { note.textContent = ''; note.hidden = true; return; }
    note.hidden = false;
    note.textContent = result.reason || 'Please check that email address.';
    // A likely typo can be put right with one press.
    if (result.suggestion) {
      const fix = document.createElement('button');
      fix.type = 'button';
      fix.className = 'btn btn-link btn-sm pca-email-fix';
      fix.textContent = 'Use it';
      fix.addEventListener('click', () => {
        box.value = result.suggestion;
        box.dispatchEvent(new Event('input', { bubbles: true }));
        box.dispatchEvent(new Event('change', { bubbles: true }));
        check(box);
      });
      note.appendChild(fix);
    }
  }

  async function check(box) {
    const address = (box.value || '').trim();
    if (!address) { show(box, null); return; }
    if (seen.has(address)) { show(box, seen.get(address)); return; }
    try {
      const resp = await fetch(API, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: address }),
      });
      if (!resp.ok) return;              // signed out or offline: say nothing
      const result = await resp.json();
      seen.set(address, result);
      // Only answer for what is in the box now.
      if ((box.value || '').trim() === address) show(box, result);
    } catch (err) {
      // No connection: the address is not wrong, it is just unchecked.
    }
  }

  boxes.forEach(box => {
    let timer = null;
    box.addEventListener('input', () => {
      box.classList.remove('is-email-bad');
      noteFor(box).hidden = true;
      clearTimeout(timer);
      timer = setTimeout(() => check(box), WAIT_MS);
    });
    box.addEventListener('blur', () => { clearTimeout(timer); check(box); });
  });
})();
