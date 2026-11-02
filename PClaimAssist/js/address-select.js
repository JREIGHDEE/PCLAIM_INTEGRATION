/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Province / City / Barangay / Subdivision: pick from a list

   Each box is the usual search-as-you-type box (user testing #4 asked for
   one "like the usual online sites"): click it and the list opens, type
   and the list narrows to the places that match, click one or press
   Enter to take it (Enter alone takes the first match).

   Only a place on the list is kept (adviser's revision S3: dropdowns, not
   free text). The lists are the whole country (js/ph-psgc.js, from the
   PSGC); something typed that is not on the list is put back to what was
   there, with a note under the box. A value loaded from a saved claim or
   the logbook that is not on the list stays until the box is changed.

   The three are a chain: the province narrows the cities, the city the
   barangays. A box below that no longer fits what was chosen above it is
   emptied. Subdivisions have no official list: the box offers the common
   Davao City ones and those the staff added for that barangay, and a new
   one is added only by choosing "Add ... as a new subdivision".

   Matching ignores case and spacing: every text box on this form is
   stored in capitals (toFormCase in js/app.js), so a saved claim says
   "DAVAO DEL SUR" where the list says "Davao del Sur".

   The box is the original <input>, with its data-autofill: everything
   downstream - state, the forms, the PDF overlays, validation - reads
   the same key it always did.
═══════════════════════════════════════════════════════════ */
(function setupAddressSelects() {
  const DATA = window.PH_ADDRESS;
  if (!DATA) return;

  const SUBDIVISION_STORE = 'pca_subdivisions_v1';
  const PARTS = ['Province', 'City', 'Barangay', 'Subdivision'];
  const MAX_SHOWN = 200;

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

  /* Subdivisions are not in the PSGC, so the clinic builds its own list,
     kept per city and barangay ("San Isidro" is in many cities). Older
     entries were kept per barangay alone, all in Davao City. */
  const subdivisionKey = (city, barangay) => norm(barangay) && `${norm(city)}/${norm(barangay)}`;
  function readSubdivisions() {
    try { return JSON.parse(localStorage.getItem(SUBDIVISION_STORE)) || {}; }
    catch (e) { return {}; }
  }
  function savedSubdivisions(city, barangay) {
    const all = readSubdivisions();
    const older = norm(city) === 'DAVAO CITY' ? all[norm(barangay)] || [] : [];
    return (all[subdivisionKey(city, barangay)] || []).concat(older);
  }
  function rememberSubdivision(city, barangay, value) {
    const key = subdivisionKey(city, barangay), text = String(value || '').trim();
    if (!key || !text) return;
    try {
      const all = readSubdivisions();
      const list = all[key] || [];
      if (!list.some(x => norm(x) === norm(text))) { list.push(text); list.sort(); }
      all[key] = list;
      localStorage.setItem(SUBDIVISION_STORE, JSON.stringify(all));
    } catch (e) { /* not remembered; the typed value still stands */ }
  }

  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  let menuSeq = 0;

  function wire(block) {
    const inputs = {};
    PARTS.forEach(part => { inputs[part] = block.input(part); });
    if (!inputs.Province || !inputs.City || !inputs.Barangay) return null;

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
        if (!norm(inputs.Barangay.value)) return [];
        const common = norm(inputs.City.value) === 'DAVAO CITY' ? window.PH_SUBDIVISIONS || [] : [];
        const mine = savedSubdivisions(inputs.City.value, inputs.Barangay.value);
        return common.concat(mine.filter(x => !common.some(c => norm(c) === norm(x)))).sort(byName);
      },
    };

    /* Writing through the input keeps state.data and every copy in step:
       bindInputListeners() is already listening on it. */
    function setValue(part, value) {
      const input = inputs[part];
      if (!input || input.value === value) return;
      input.value = value;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    /* After a box changed: each box below it that is not on the new list
       for it is emptied, top down - a city cleared leaves no barangay
       list, so its barangay goes too. Still-valid ones are kept. */
    function clearBelow(part) {
      PARTS.slice(PARTS.indexOf(part) + 1).forEach(p => {
        const input = inputs[p];
        if (input && input.value && !canonical(options[p](), input.value)) setValue(p, '');
      });
    }

    PARTS.forEach(part => {
      const input = inputs[part];
      if (!input) return;
      const wrap = document.createElement('div');
      wrap.className = 'pca-addr-combo';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      const menu = document.createElement('ul');
      menu.className = 'pca-addr-menu';
      menu.id = `pcaAddrMenu${++menuSeq}`;
      menu.setAttribute('role', 'listbox');
      menu.hidden = true;
      wrap.appendChild(menu);
      input.setAttribute('role', 'combobox');
      input.setAttribute('aria-autocomplete', 'list');
      input.setAttribute('aria-controls', menu.id);
      input.setAttribute('aria-expanded', 'false');
      input.setAttribute('autocomplete', 'off');
      input.placeholder = part === 'Subdivision' ? 'Choose (if any)' : 'Choose or type to search…';
      input.classList.add('pca-addr-input');
      const note = document.createElement('div');
      note.className = 'pca-addr-note';
      note.setAttribute('role', 'status');
      note.hidden = true;
      wrap.appendChild(note);

      let active = -1, shown = [], before = input.value;
      const ABOVE = { City: 'province', Barangay: 'city', Subdivision: 'barangay' };
      const locked = () => input.readOnly || input.disabled;

      function close() {
        menu.hidden = true;
        input.setAttribute('aria-expanded', 'false');
        active = -1;
      }

      /* filter: '' shows the whole list (opened by a click), else the
         places containing what is typed, those starting with it first. */
      function open(filter) {
        if (locked()) return;
        const list = options[part]();
        const want = norm(filter);
        shown = want
          ? list.filter(n => norm(n).includes(want))
              .sort((a, b) => (norm(b).startsWith(want) - norm(a).startsWith(want)) || byName(a, b))
          : list;
        const current = norm(input.value);
        const mark = name => {
          if (!want) return escapeHtml(name);
          const i = norm(name).indexOf(want);
          return escapeHtml(name.slice(0, i)) + '<strong>' + escapeHtml(name.slice(i, i + want.length)) + '</strong>' +
            escapeHtml(name.slice(i + want.length));
        };
        let html = shown.slice(0, MAX_SHOWN).map((name, i) =>
          `<li role="option" data-i="${i}" class="${norm(name) === current ? 'is-current' : ''}">${mark(name)}</li>`).join('');
        // A subdivision not on the list is added only on purpose.
        const typed = String(filter || '').trim();
        if (part === 'Subdivision' && typed && !canonical(list, typed) && norm(inputs.Barangay.value)) {
          html += `<li role="option" data-i="${Math.min(shown.length, MAX_SHOWN)}" class="pca-addr-add">` +
            `<i class="bi bi-plus-lg me-1"></i>Add “${escapeHtml(typed)}” as a new subdivision</li>`;
          shown = shown.slice(0, MAX_SHOWN).concat([{ add: typed }]);
        } else if (!shown.length) {
          html = `<li class="pca-addr-none">${list.length ? 'Not on the list - choose one from the list'
            : ABOVE[part] ? `Choose the ${ABOVE[part]} first` : 'No list for this place'}</li>`;
        }
        menu.innerHTML = html;
        menu.hidden = false;
        // Low on the screen: the list opens upward, as it does on most sites.
        const box = input.getBoundingClientRect();
        const below = window.innerHeight - box.bottom, above = box.top;
        menu.classList.toggle('opens-up', below < 270 && above > below);
        input.setAttribute('aria-expanded', 'true');
        active = -1;
        const cur = menu.querySelector('.is-current');
        if (cur && !want) cur.scrollIntoView({ block: 'nearest' });
      }

      function highlight(i) {
        const items = menu.querySelectorAll('li[data-i]');
        if (!items.length) return;
        active = (i + items.length) % items.length;
        items.forEach((li, j) => li.classList.toggle('is-active', j === active));
        items[active].scrollIntoView({ block: 'nearest' });
      }

      function say(text) {
        note.textContent = text || '';
        note.hidden = !text;
      }

      function pick(name) {
        if (name && name.add) {
          rememberSubdivision(inputs.City.value, inputs.Barangay.value, name.add);
          name = name.add;
        }
        say('');
        const changed = norm(name) !== norm(before);
        setValue(part, name);
        before = input.value;
        close();
        if (changed) clearBelow(part);
      }

      /* Typing finished: the list's spelling if it is a listed place
         (typed in any case), and what is below is checked against it.
         Anything else typed is put back: only the list is kept. An empty
         box is fine, and so is the value it had (a saved claim's). */
      function commit() {
        const typed = input.value.trim();
        const list = options[part]();
        const known = canonical(list, typed);
        if (known) {
          if (known !== input.value) setValue(part, known);
          say('');
        } else if (typed && norm(typed) !== norm(before)) {
          setValue(part, before);
          say(part === 'Subdivision'
            ? `“${typed}” is not on the list. Choose one, or choose “Add … as a new subdivision”.`
            : list.length
              ? `“${typed}” is not on the list. Please choose the ${part.toLowerCase()} from the list.`
              : `Choose the ${ABOVE[part]} first, then the ${part.toLowerCase()} from its list.`);
        } else {
          say('');
        }
        if (norm(input.value) !== norm(before)) clearBelow(part);
        before = input.value;
      }

      input.addEventListener('focus', () => { before = input.value; open(''); });
      input.addEventListener('click', () => { if (menu.hidden) open(''); });
      // Only for the box being typed in: a value written in by the code (a
      // box below emptied, the list's spelling put in) opens no list.
      input.addEventListener('input', () => { if (document.activeElement === input) open(input.value); });
      input.addEventListener('keydown', e => {
        if (locked()) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); if (menu.hidden) open(input.value); highlight(active + 1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); if (menu.hidden) open(input.value); highlight(active - 1); }
        else if (e.key === 'Enter' && !menu.hidden && active >= 0) { e.preventDefault(); pick(shown[active]); }
        else if (e.key === 'Enter' && !menu.hidden && shown.length && input.value.trim()) { e.preventDefault(); pick(shown[0]); }
        else if (e.key === 'Escape' && !menu.hidden) { e.preventDefault(); close(); }
        else if (e.key === 'Tab') close();
      });
      // mousedown, not click: it comes before the box loses focus.
      menu.addEventListener('mousedown', e => {
        const li = e.target.closest('li[data-i]');
        e.preventDefault();
        if (li) pick(shown[Number(li.dataset.i)]);
      });
      input.addEventListener('blur', () => { close(); commit(); });
    });

    return () => {};
  }

  /* Every address block on the page. Each data-autofill prefix - addr,
     mailingAddr - is one block, and a prefix can appear more than once
     (Patient details, and a read-only copy on a form, which shows its
     text and opens no list). */
  ['addr', 'mailingAddr'].forEach(prefix => {
    document.querySelectorAll(`[data-autofill="${prefix}Province"]`).forEach((_, i) => {
      wire({
        input(part) {
          return document.querySelectorAll(`[data-autofill="${prefix}${part}"]`)[i] || null;
        },
      });
    });
  });

  // A claim loaded from the database or the logbook fills these boxes
  // directly; they are plain boxes now, so there is nothing to redraw.
  window.PCAAddressSelects = { refresh() {} };
})();
