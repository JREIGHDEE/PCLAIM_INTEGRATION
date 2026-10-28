/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Easy-to-use helpers (goes with css/easy.css)

   For older clinic staff who are not computer experts, on Patient
   details:
     • "Back" / "Next part" buttons under each part, so nobody has to
       find the small tabs at the top;
     • each part says what is left in it, the boxes still to fill are
       red, and a "Next step" line says where to go.
   Only adds things to the page - it never changes the form fields or
   how they are saved.
═══════════════════════════════════════════════════════════ */

(function () {
  function addTabSteps() {
    const tabs = [...document.querySelectorAll('#patientTabs .nav-link')];
    tabs.forEach((tab, i) => {
      const pane = document.querySelector(tab.dataset.bsTarget);
      if (!pane || pane.querySelector('.tab-step-nav')) return;
      const nav = document.createElement('div');
      nav.className = 'tab-step-nav';
      const back = i > 0
        ? `<button type="button" class="btn btn-outline-secondary" data-go="${i - 1}">
             <i class="bi bi-arrow-left me-2"></i>Back</button>`
        : '<span></span>';
      const next = i < tabs.length - 1
        ? `<button type="button" class="btn btn-primary" data-go="${i + 1}">
             Next part: ${tabs[i + 1].textContent.trim().replace(/^\d+\.\s*/, '')}
             <i class="bi bi-arrow-right ms-2"></i></button>`
        : `<button type="button" class="btn btn-success" data-section-go="validation">
             Done &mdash; check for missing information <i class="bi bi-arrow-right ms-2"></i></button>`;
      nav.innerHTML = back + next;
      pane.appendChild(nav);
    });

    document.addEventListener('click', e => {
      const go = e.target.closest('[data-go]');
      if (go) {
        const tab = tabs[Number(go.dataset.go)];
        if (tab && window.bootstrap) {
          bootstrap.Tab.getOrCreateInstance(tab).show();
          tab.scrollIntoView({ block: 'start' });
          window.scrollBy(0, -100);
        }
      }
      const section = e.target.closest('[data-section-go]');
      if (section && typeof navigateTo === 'function') navigateTo(section.dataset.sectionGo);
    });
  }

  /* ── Patient details: what is left, and what to do next ──────────
     Every box that must be filled (a red *, or one the scan could not
     read) and is still empty is shown in red. Each part (tab) says how
     many are left in it ("2 to type", "3 from scan to check", or
     "Nothing missing"), and the "Next step" line above them goes to the
     first part with something to type. */
  function isEmpty(key) {
    const value = window.state && state.data[key];
    return Array.isArray(value) ? value.length === 0 : !String(value ?? '').trim();
  }

  // What to colour red for a box: the box itself, or around radio buttons,
  // choice buttons and the three-part PIN boxes.
  function highlightTarget(el) {
    if (el.type === 'radio') return el.closest('.pca-radio') || el.parentElement;
    if (el.type === 'hidden') {
      // PIN boxes (js/pin-input.js put them right after the hidden input),
      // or segmented boxes pointing at it.
      if (el.nextElementSibling?.classList.contains('pin-boxes')) return el.nextElementSibling;
      return el.id ? document.querySelector(`.box-input[data-target="#${el.id}"]`) : null;
    }
    return el;
  }

  function partStatus(pane) {
    const toType = [];
    const seen = new Set();
    pane.querySelectorAll('[data-autofill]').forEach(el => {
      const key = el.dataset.autofill;
      if (seen.has(key) || el.disabled) return;
      // A PIN with "No PhilHealth" ticked is not asked for, and that tick is
      // a choice beside the PIN, not a box to type (js/app.js).
      if (typeof pinNotAsked === 'function' && pinNotAsked(key)) return;
      if (typeof NO_PHILHEALTH === 'object' && Object.values(NO_PHILHEALTH).includes(key)) return;
      const box = el.closest('[class*="col"]') || el.parentElement;
      // Asked for: a red *, a box the scan could not read, or a box a form
      // still shows red (the employer while the member is employed...) -
      // the same rule as the forms and the checker (js/app.js keyRedOnAnyForm).
      const required = el.dataset.ocrRequired || (box && box.querySelector('label .required-dot')) ||
        (typeof keyRedOnAnyForm === 'function' && keyRedOnAnyForm(key));
      if (!required || !isEmpty(key)) return;
      seen.add(key);
      toType.push({ key, target: highlightTarget(el) });
    });
    const toCheck = pane.querySelectorAll('.ocr-tag--needs_check').length;
    return { toType, toCheck };
  }

  function addPartProgress() {
    const tabs = [...document.querySelectorAll('#patientTabs .nav-link')];
    if (!tabs.length) return;
    const names = tabs.map(t => t.textContent.trim().replace(/^\d+\.\s*/, ''));
    tabs.forEach((tab, i) => {
      tab.innerHTML = `<span class="part-num">${i + 1}</span>` +
        `<span class="part-text"><span class="part-name">${names[i]}</span>` +
        '<span class="part-status"></span></span>';
    });

    function refresh() {
      let next = null;
      document.querySelectorAll('#patientTabContent .box-missing').forEach(el => el.classList.remove('box-missing'));
      tabs.forEach((tab, i) => {
        const pane = document.querySelector(tab.dataset.bsTarget);
        if (!pane) return;
        const { toType, toCheck } = partStatus(pane);
        toType.forEach(t => t.target && t.target.classList.add('box-missing'));
        const bits = [];
        if (toType.length) bits.push(`<span class="st-type">${toType.length} to type</span>`);
        if (toCheck) bits.push(`<span class="st-check">${toCheck} from scan to check</span>`);
        tab.querySelector('.part-status').innerHTML = bits.length ? bits.join(' · ')
          : '<span class="st-done"><i class="bi bi-check-circle-fill"></i> Nothing missing</span>';
        tab.classList.toggle('part-done', !toType.length);
        if (toType.length && next === null) next = { i, toType };
      });

      const box = document.getElementById('patientNextStep');
      if (!box) return;
      if (next) {
        const many = next.toType.length === 1 ? '1 red box' : `${next.toType.length} red boxes`;
        box.className = 'next-step';
        // Says where to go; moving there is done with the part's own
        // next / previous buttons (no second button here).
        box.innerHTML = `<i class="bi bi-arrow-right-circle-fill"></i>
          <div><strong>Next step:</strong> Part ${next.i + 1}, ${names[next.i]} — ${many} to fill in</div>`;
      } else {
        box.className = 'next-step next-step--done';
        box.innerHTML = `<i class="bi bi-check-circle-fill"></i>
          <div><strong>Everything that must be filled in is done.</strong></div>`;
      }
    }

    // Refresh whenever the form data changes (app.js calls
    // updateFormPreviews after every change and after loading a patient).
    if (typeof window.updateFormPreviews === 'function') {
      const original = window.updateFormPreviews;
      window.updateFormPreviews = function () {
        original.apply(this, arguments);
        refresh();
      };
    }
    document.addEventListener('shown.bs.tab', refresh);
    refresh();
  }

  /* Example text inside empty boxes ("DELA CRUZ", "Jr.", "Unit 4B") looks
     like real data to someone in a hurry - only format hints stay. */
  function clearDataLikePlaceholders() {
    document.querySelectorAll('.main-content input[placeholder], .main-content textarea[placeholder]').forEach(el => {
      // Kept: format hints ("##-#########-#", "13 digits", "000", and a
      // date's "MM/DD/YYYY", "MM", "DD", "YYYY", or M / D / Y in one digit box).
      // Example values ("0917-123-4567", "120/80") look real and go.
      const hint = /#|digit|number|yyyy|^0+$/i.test(el.placeholder) ||
                   /^(?:MM|DD|[MDY])$/.test(el.placeholder);
      if (!hint) el.placeholder = '';
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    addTabSteps();
    clearDataLikePlaceholders();
    addPartProgress();
  });
})();
