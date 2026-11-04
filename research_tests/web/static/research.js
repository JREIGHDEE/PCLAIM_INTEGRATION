/* One research tab (or the Results tab): inputs, run, progress, results.
   Text from files and results is always put in with textContent. */
(function () {
  const { key, prefix } = window.RESEARCH;
  const api = path => `${prefix}/api/${key}${path}`;
  const $ = id => document.getElementById(id);
  const el = (tag, text, cls) => { const e = document.createElement(tag); if (text != null) e.textContent = text;
                                   if (cls) e.className = cls; return e; };
  let polling = null;

  async function call(path, options) {
    const res = await fetch(api(path), Object.assign({ credentials: 'same-origin' }, options || {}));
    let body = {};
    try { body = await res.json(); } catch (e) { /* not JSON */ }
    if (!res.ok || body.success === false) throw new Error(body.error || `The server answered ${res.status}`);
    return body;
  }

  function fmt(v) {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(Math.abs(v) < 1 ? 4 : 2);
    if (Array.isArray(v)) return v.join(', ');
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
  }

  function drawResults(summary) {
    const box = $('results');
    box.replaceChildren();
    if (!summary) { box.append(el('p', key === 'results' ? '' : 'No results yet.', 'muted')); return; }
    box.append(el('p', `Last run: ${summary.generated_at}${summary.samples ? ' - SAMPLE DATA (computer-drawn), not for Chapter 5' : ''}`,
                  'small ' + (summary.samples ? 'notice' : 'muted')));
    (summary.sheets || []).forEach(sheet => {
      box.append(el('h3', sheet.title || sheet.name));
      const wrap = el('div', null, 'table-wrap');
      const table = el('table', null, 'summary');
      const head = el('tr');
      (sheet.headers || []).forEach(h => head.append(el('th', h)));
      const thead = el('thead'); thead.append(head);
      const tbody = el('tbody');
      (sheet.rows || []).forEach((row, i) => {
        const tr = el('tr');
        row.forEach(v => tr.append(el('td', fmt(v))));
        if (sheet.bold_last && i === sheet.rows.length - 1) tr.style.fontWeight = '800';
        tbody.append(tr);
      });
      table.append(thead, tbody); wrap.append(table); box.append(wrap);
      if ((sheet.notes || []).length) {
        const ul = el('ul', null, 'sheet-notes');
        sheet.notes.forEach(n => ul.append(el('li', n)));
        box.append(ul);
      }
    });
  }

  function drawInputs(inputs, samples) {
    const list = $('inputs');
    if (!list) return;
    list.replaceChildren();
    if (!inputs.length) { list.append(el('li', 'Nothing to upload: this test reads the results of the others.', 'muted')); return; }
    inputs.forEach((item, i) => {
      const li = el('li');
      li.append(el('code', item.target));
      const ok = item.count > 0;
      const sample = samples && samples[i] && samples[i].count > 0;
      li.append(el('span', ok ? (item.folder ? `${item.count} file(s)` : 'present') : 'missing',
                   'status-chip ' + (ok ? 'ok' : 'bad')));
      if (!ok && sample) li.append(el('span', 'a sample exists', 'status-chip warn'));
      const input = el('input'); input.type = 'file'; input.multiple = item.folder;
      input.accept = item.folder ? '.pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp' : item.target.slice(item.target.lastIndexOf('.'));
      const btn = el('button', 'Upload');
      btn.addEventListener('click', async () => {
        if (!input.files.length) return;
        const form = new FormData();
        Array.from(input.files).forEach(f => form.append('files', f));
        btn.disabled = true;
        try { await call(`/upload/${item.slot}`, { method: 'POST', body: form }); await refresh(); }
        catch (err) { alert(err.message); }
        finally { btn.disabled = false; }
      });
      li.append(input, btn);
      if (item.files.length && item.folder) li.append(el('span', item.files.slice(0, 6).join(', ') + (item.count > 6 ? ' ...' : ''), 'small muted'));
      list.append(li);
    });
  }

  function drawTests(tests) {
    const body = $('testRows');
    if (!body) return;
    body.replaceChildren();
    tests.forEach(t => {
      const tr = el('tr');
      tr.append(el('td', t.tab), el('td', t.generated_at || 'not run yet'),
                el('td', t.summary ? (t.samples ? 'sample data' : 'inputs/') : ''));
      body.append(tr);
    });
  }

  function drawProgress(p, running) {
    const chip = $('stateChip'), bar = $('progressBar'), text = $('progressText'), log = $('log');
    const state = running ? (p.state === 'waiting' ? 'waiting' : 'running') : (p.state || 'idle');
    const labels = { idle: key === 'results' ? 'Not built yet' : 'Not run yet', waiting: 'Starting', running: 'Running',
                     done: 'Done', failed: 'Failed' };
    chip.textContent = labels[state] || state;
    chip.className = 'status-chip ' + (state === 'done' ? 'ok' : state === 'failed' ? 'bad' : '');
    bar.classList.toggle('hidden', !(state === 'running' || state === 'waiting'));
    bar.firstElementChild.style.width = `${Math.round(100 * (p.fraction || 0))}%`;
    text.textContent = state === 'done' && p.seconds != null ? `Finished in ${p.seconds} s.` : (p.message || '');
    log.classList.toggle('hidden', !(state === 'failed' && p.log));
    log.textContent = p.log || '';
    $('runBtn').disabled = running;
    const cancel = $('cancelBtn');
    if (cancel) cancel.classList.toggle('hidden', !running);
  }

  async function refresh() {
    let s;
    try { s = await call('/status'); } catch (err) { $('progressText').textContent = err.message; return; }
    drawProgress(s.progress || {}, s.running);
    $('downloadBtn').classList.toggle('disabled', !s.workbook);
    if (s.inputs) drawInputs(s.inputs, s.sample_inputs);
    if (s.tests) drawTests(s.tests);
    drawResults(s.summary);
    clearTimeout(polling);
    if (s.running) polling = setTimeout(refresh, 1500);
  }

  function options() {
    const out = {};
    document.querySelectorAll('#options input, #options select').forEach(input => {
      out[input.name] = input.type === 'checkbox' ? input.checked : input.value;
    });
    return out;
  }

  $('runBtn').addEventListener('click', async () => {
    $('runBtn').disabled = true;
    try {
      await call('/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(options()) });
    } catch (err) { alert(err.message); }
    refresh();
  });
  const cancel = $('cancelBtn');
  if (cancel) cancel.addEventListener('click', async () => { await call('/cancel', { method: 'POST' }); refresh(); });
  refresh();
})();
