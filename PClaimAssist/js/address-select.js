/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Province / City / Barangay as dropdowns

   The three are a chain: picking a province narrows the cities, picking
   a city narrows the barangays. Subdivision is offered from the ones
   already typed for that barangay, since no official list exists.

   The box shows the chosen place, and clicking it opens the list again.
   Anything not on the list - a patient from outside Davao Region - is
   typed into the box underneath, which appears only when it is needed.

   Matching ignores case and spacing: every text box on this form is
   stored in capitals (toFormCase in js/app.js), so a saved claim says
   "DAVAO DEL SUR" where the list says "Davao del Sur". Comparing them
   as typed would miss every time and send every box to "type it in".

   The original <input> stays in the page and keeps its data-autofill:
   everything downstream - state, the forms, the PDF overlays,
   validation - reads the same key it always did.
═══════════════════════════════════════════════════════════ */
(function setupAddressSelects() {
  const DATA = window.PH_ADDRESS;
  if (!DATA) return;

  const TYPE_IT = '__type__';
  const SUBDIVISION_STORE = 'pca_subdivisions_v1';
  const PARTS = ['Province', 'City', 'Barangay', 'Subdivision'];

  /* "DAVAO DEL SUR", "Davao del Sur" and "davao  del sur" are one place. */
  const norm = v => String(v || '').trim().replace(/\s+/g, ' ').toUpperCase();

  /* "19-B" belongs after "2-A", not after "18-B" read as letters, so a
     name that starts with a number is ordered by that number. */
  function byName(a, b) {
    const na = /^(\d+)/.exec(a), nb = /^(\d+)/.exec(b);
    if (na && nb) return Number(na[1]) - Number(nb[1]) || a.localeCompare(b);
    if (na) return -1;            // numbered Poblacion barangays first
    if (nb) return 1;
    return a.localeCompare(b);
  }

  /* The spelling the list uses, for a value typed in any case. */
  function canonical(list, value) {
    const want = norm(value);
    if (!want) return '';
    return list.find(name => norm(name) === want) || '';
  }

  /* Subdivisions are not in the PSGC, so the clinic builds its own list:
     anything typed once is offered next time, kept per barangay. */
  function readSubdivisions() {
    try { return JSON.parse(localStorage.getItem(SUBDIVISION_STORE)) || {}; }
    catch (e) { return {}; }
  }
  function rememberSubdivision(barangay, value) {
    const key = norm(barangay), text = String(value || '').trim();
    if (!key || !text) return;
    try {
      const all = readSubdivisions();
      const list = all[key] || [];
      if (!list.some(x => norm(x) === norm(text))) { list.push(text); list.sort(); }
      all[key] = list;
      localStorage.setItem(SUBDIVISION_STORE, JSON.stringify(all));
    } catch (e) { /* not remembered; the typed value still stands */ }
  }

  function wire(block) {
    const inputs = {};
    PARTS.forEach(part => { inputs[part] = block.input(part); });
    if (!inputs.Province || !inputs.City || !inputs.Barangay) return null;

    const sel = {};
    PARTS.forEach(part => {
      const input = inputs[part];
      if (!input) return;
      const wrap = document.createElement('div');
      wrap.className = 'pca-addr-pick';
      const dropdown = document.createElement('select');
      dropdown.className = 'form-select pca-input pca-addr-select';
      dropdown.setAttribute('aria-label', part);
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(dropdown);
      wrap.appendChild(input);
      input.classList.add('pca-addr-typed');
      input.hidden = true;
      sel[part] = dropdown;
    });

    /* The list for each box, given what is chosen above it. */
    const options = {
      Province: () => Object.keys(DATA).sort(byName),
      City: () => {
        const p = canonical(Object.keys(DATA), inputs.Province.value);
        return p && DATA[p] ? Object.keys(DATA[p]).sort(byName) : [];
      },
      Barangay: () => {
        const p = canonical(Object.keys(DATA), inputs.Province.value);
        if (!p || !DATA[p]) return [];
        const c = canonical(Object.keys(DATA[p]), inputs.City.value);
        return c && DATA[p][c] ? DATA[p][c].slice().sort(byName) : [];
      },
      Subdivision: () => {
        /* The common ones first, then anything this clinic has typed
           before for that barangay. No official list exists, so the
           box still takes whatever is typed. */
        const common = window.PH_SUBDIVISIONS || [];
        const mine = readSubdivisions()[norm(inputs.Barangay.value)] || [];
        const all = common.concat(mine.filter(
          x => !common.some(c => norm(c) === norm(x))));
        return all.sort(byName);
      },
    };

    function paint(part) {
      const dropdown = sel[part];
      const input = inputs[part];
      if (!dropdown || !input) return;

      const list = options[part]();
      const current = String(input.value || '').trim();
      const known = canonical(list, current);

      /* A value the list does not hold is typed in: either the staff
         chose to, or it arrived that way from a saved claim. */
      const typing = !!current && !known;

      dropdown.innerHTML = '';
      dropdown.appendChild(new Option(
        list.length ? 'Select…' : 'Not on the list — type it in', ''));
      list.forEach(name => dropdown.appendChild(new Option(name, name)));
      // The way out of the list, named for what it does.
      dropdown.appendChild(new Option(
        list.length ? 'Not on the list — type it in' : 'Type it in', TYPE_IT));

      if (typing) {
        // Show what was typed as the chosen line, so the box is not blank.
        const mine = new Option(current, current, false, true);
        dropdown.insertBefore(mine, dropdown.options[1] || null);
        dropdown.value = current;
      } else {
        dropdown.value = known || '';
      }

      input.hidden = !typing;
      if (typing) input.placeholder = 'Type the ' + part.toLowerCase();
    }

    function paintAll() { PARTS.forEach(paint); }

    /* Writing through the input keeps state.data and every copy in step:
       bindInputListeners() is already listening on it. */
    function setValue(part, value) {
      const input = inputs[part];
      if (!input || input.value === value) return;
      input.value = value;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    PARTS.forEach(part => {
      const dropdown = sel[part];
      if (!dropdown) return;
      dropdown.addEventListener('change', () => {
        const input = inputs[part];
        if (dropdown.value === TYPE_IT) {
          setValue(part, '');
          paint(part);
          input.hidden = false;       // the box is wanted now, before anything is typed
          input.focus();
          return;
        }
        setValue(part, dropdown.value);
        // A narrower box can no longer hold what it held.
        if (part === 'Province') { setValue('City', ''); setValue('Barangay', ''); }
        if (part === 'City') setValue('Barangay', '');
        if (part === 'Barangay') setValue('Subdivision', '');
        paintAll();
      });
    });

    // Typing finished: show it as the chosen line, and remember a
    // subdivision for next time.
    PARTS.forEach(part => {
      const input = inputs[part];
      if (!input) return;
      input.addEventListener('change', () => {
        if (part === 'Subdivision') {
          rememberSubdivision(inputs.Barangay.value, input.value);
        }
        paint(part);
      });
    });

    return paintAll;
  }

  /* Every address block on the page. Each data-autofill prefix - addr,
     mailingAddr - is one block, and a prefix can appear more than once
     (Patient details, and a read-only copy on a form). */
  const refreshers = [];
  ['addr', 'mailingAddr'].forEach(prefix => {
    document.querySelectorAll(`[data-autofill="${prefix}Province"]`).forEach((_, i) => {
      const refresh = wire({
        input(part) {
          return document.querySelectorAll(`[data-autofill="${prefix}${part}"]`)[i] || null;
        },
      });
      if (refresh) refreshers.push(refresh);
    });
  });

  // A claim loaded from the database or the logbook fills these boxes
  // directly, so redraw once they are written.
  window.PCAAddressSelects = { refresh: () => refreshers.forEach(fn => fn()) };
  window.PCAAddressSelects.refresh();
})();
