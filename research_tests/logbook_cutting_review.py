"""Check the logbook cutting yourself: a page on this computer where you tag
every cut Correct, Partly or Not at all, then make the report from your tags.

    python -m research_tests.logbook_cutting_review          (opens http://127.0.0.1:8765)

Run research_tests.logbook_cutting once first (it lists the cuts). The page
shows each writer's pages the way the mosaics do - a column per category,
a row per logbook entry, each cell the cut the Logbook Reader made:
  click a cut              Correct -> Partly -> Not at all -> Correct ...
  the buttons under a      tag the whole column (or row) at once
  column / beside a row
  "Accept the suggestions  confirm every cut on the page you have not tagged
   on this page"           with the suggestion shown
Each cut starts with a SUGGESTION (dashed border) taken from the earlier visual
check (inputs/logbook_cutting_visual_check.csv); it counts only once you click
it or accept it. Every click is saved at once to
inputs/logbook_cutting_human_check.csv - close the page any time and carry on
later. "Make the report" reruns the cutting test with your tags and builds
outputs/logbook_cutting/logbook_cutting_proof_report.pdf and the workbook.

Served on 127.0.0.1 only; nothing leaves this computer.
"""
import argparse
import csv
import datetime
import json
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from research_tests import INPUTS, OUTPUTS, REPO

RESULTS = OUTPUTS / "logbook_cutting" / "logbook_cutting_results.xlsx"
CROPS = OUTPUTS / "work" / "uploads" / "review_crops"
HUMAN = INPUTS / "logbook_cutting_human_check.csv"
TAGS = ("correct", "partly", "wrong")
HUMAN_COLUMNS = ["Scan", "Writer", "Page", "Row", "Category", "Tag", "Suggested", "Note", "Tagged at"]
# The earlier visual check -> the suggestion shown (a cut of the right
# entry that only got the wrong row number is a correct cut).
SUGGEST = {"Proper": "correct", "Clipped": "partly", "Wrong column": "wrong", "Half of two entries": "wrong",
           "Empty paper": "wrong", "Not found": "wrong"}


def cut_key(scan, writer, page, row, category):
    return f"{scan}|{writer}|{int(page)}|{int(row)}|{category}"


def load_cuts():
    """Every cut of the last cutting run, in page order, with its suggestion."""
    import openpyxl
    if not RESULTS.is_file():
        raise SystemExit(f"{RESULTS} not found - run python -m research_tests.logbook_cutting first.")
    ws = openpyxl.load_workbook(RESULTS, read_only=True)["Raw data"]
    rows = ws.iter_rows(values_only=True)
    head = next(rows)
    cuts = []
    for values in rows:
        d = dict(zip(head, values))
        if not d.get("Scan"):
            continue
        cuts.append({"key": cut_key(d["Scan"], d["Writer"], d["Page"], d["Row"], d["Category"]),
                     "scan": d["Scan"], "writer": d["Writer"], "page": int(d["Page"]), "row": int(d["Row"]),
                     "category": d["Category"], "column": d.get("Column") or 99, "written": d.get("Written") or "",
                     "read": d.get("Read in the cut (PaddleOCR raw)") or "", "crop": d.get("Cut picture") or "",
                     "visual": d.get("Cut (visual)") or "", "rownum": d.get("Row number (visual)") or "",
                     "suggested": SUGGEST.get(d.get("Cut (visual)") or "", "")})
    return cuts


def load_tags():
    """{cut key: {"tag", "note", "at"}} saved so far."""
    out = {}
    if HUMAN.is_file():
        with open(HUMAN, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if (r.get("Tag") or "").strip().lower() in TAGS:
                    out[cut_key(r["Scan"], r["Writer"], r["Page"], r["Row"], r["Category"])] = {
                        "tag": r["Tag"].strip().lower(), "note": r.get("Note") or "", "at": r.get("Tagged at") or ""}
    return out


def save_tags(tags, cuts):
    by_key = {c["key"]: c for c in cuts}
    HUMAN.parent.mkdir(parents=True, exist_ok=True)
    tmp = HUMAN.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HUMAN_COLUMNS)
        for key, t in tags.items():
            c = by_key.get(key)
            if not c or t.get("tag") not in TAGS:
                continue
            w.writerow([c["scan"], c["writer"], c["page"], c["row"], c["category"], t["tag"], c["suggested"],
                        t.get("note", ""), t.get("at", "")])
    tmp.replace(HUMAN)


def make_report():
    """Rerun the cutting test with the tags, then its proof report."""
    log = []
    for module in ("research_tests.logbook_cutting", "research_tests.logbook_cutting_report"):
        done = subprocess.run([sys.executable, "-m", module], cwd=str(REPO), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        log.append(f"$ python -m {module}\n" + "\n".join((done.stdout + done.stderr).strip().splitlines()[-6:]))
        if done.returncode:
            return False, "\n\n".join(log)
    return True, "\n\n".join(log)


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Logbook cutting check</title>
<style>
 :root{--ok:#1a8f3c;--part:#e08a00;--bad:#d01f1f;--ink:#1d1d1f;--muted:#5a6570;--line:#d5dbe2;--bg:#f6f8fa}
 *{box-sizing:border-box} body{margin:0;font:14px system-ui,sans-serif;color:var(--ink);background:var(--bg)}
 header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:10px 16px;
        display:flex;flex-wrap:wrap;gap:10px;align-items:center}
 header h1{font-size:16px;margin:0 12px 0 0;color:#0b3d6e}
 select,button{font:inherit;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;cursor:pointer}
 button.primary{background:#0b5cad;color:#fff;border-color:#0b5cad}
 .legend span{display:inline-block;margin-right:10px} .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}
 #progress{color:var(--muted)} main{padding:12px 16px 60px}
 h2{font-size:15px;margin:18px 0 6px;color:#0b3d6e}
 table.grid{border-collapse:separate;border-spacing:6px} table.grid th{font-size:12px;text-align:left;vertical-align:bottom}
 .colbtns button,.rowbtns button{padding:1px 6px;font-size:12px;margin-right:2px}
 td.cell{vertical-align:top}
 .cut{position:relative;border:3px dashed #9aa6b2;border-radius:6px;background:#fff;cursor:pointer;padding:2px;display:inline-block}
 .cut img{display:block;height:64px;max-width:280px} .cut .nocut{height:64px;width:120px;display:flex;align-items:center;justify-content:center;color:var(--bad)}
 .cut .tag{position:absolute;right:3px;bottom:3px;font-size:11px;font-weight:700;background:#fff;padding:0 4px;border-radius:4px}
 .cut.s-correct{border-color:var(--ok)} .cut.s-partly{border-color:var(--part)} .cut.s-wrong{border-color:var(--bad)}
 .cut.confirmed{border-style:solid} .cut.confirmed .tag::before{content:"\2713 "}
 .cut:not(.confirmed) .tag{opacity:.75;font-weight:400}
 .rowlabel{font-weight:700;white-space:nowrap;vertical-align:middle} .note{color:var(--muted);font-size:12px}
 #log{white-space:pre-wrap;font:12px ui-monospace,monospace;background:#fff;border:1px solid var(--line);padding:8px;display:none;margin:10px 16px}
 #saved{color:var(--ok);font-size:12px}
</style></head><body>
<header>
 <h1>Logbook cutting check</h1>
 <label>Scan <select id="scan"></select></label>
 <label>Writer <select id="writer"></select></label>
 <button id="prev">&larr; Previous</button><button id="next">Next &rarr;</button>
 <button id="accept">Accept the suggestions on this page</button>
 <span class="legend"><span><i class="dot" style="background:var(--ok)"></i>Correct</span>
  <span><i class="dot" style="background:var(--part)"></i>Partly</span>
  <span><i class="dot" style="background:var(--bad)"></i>Not at all</span>
  <span class="note">dashed = suggestion, solid = yours</span></span>
 <span id="progress"></span><span id="saved"></span>
 <button class="primary" id="report">Make the report</button>
</header>
<div id="log"></div>
<main id="main"></main>
<script>
const LABEL = {correct: 'Correct', partly: 'Partly', wrong: 'Not at all'};
const NEXT = {correct: 'partly', partly: 'wrong', wrong: 'correct'};
let cuts = [], tags = {}, saveTimer = null;

function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function shown(c) { return tags[c.key] ? tags[c.key].tag : c.suggested; }

function setTag(keys, tag) {
  const at = new Date().toISOString().slice(0, 19).replace('T', ' ');
  keys.forEach(k => { tags[k] = {tag, note: (tags[k] || {}).note || '', at}; });
  render(); scheduleSave();
}
function scheduleSave() {
  clearTimeout(saveTimer);
  document.getElementById('saved').textContent = 'saving...';
  saveTimer = setTimeout(async () => {
    const r = await fetch('/save', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags)});
    document.getElementById('saved').textContent = r.ok ? 'saved' : 'NOT SAVED - is the window running the tool still open?';
  }, 300);
}

function pageCuts() {
  const s = document.getElementById('scan').value, w = document.getElementById('writer').value;
  return cuts.filter(c => c.scan === s && c.writer === w);
}
function progress() {
  const s = document.getElementById('scan').value;
  const mine = cuts.filter(c => c.scan === s), all = cuts.length;
  const done = Object.keys(tags).length, here = pageCuts().filter(c => tags[c.key]).length;
  document.getElementById('progress').textContent =
    `This writer: ${here} of ${pageCuts().length} tagged - all: ${done} of ${all}`;
}

function render() {
  const main = document.getElementById('main');
  const list = pageCuts();
  let html = '';
  for (const page of [1, 2]) {
    const pc = list.filter(c => c.page === page);
    if (!pc.length) continue;
    const cats = [...new Set(pc.sort((a, b) => a.column - b.column).map(c => c.category))];
    const rows = [...new Set(pc.map(c => c.row))].sort((a, b) => a - b);
    html += `<h2>${page === 1 ? 'Left' : 'Right'} page</h2><table class="grid"><tr><th></th>`;
    cats.forEach(cat => {
      html += `<th>${esc(cat)}<div class="colbtns">` + ['correct', 'partly', 'wrong'].map(t =>
        `<button data-col="${page}|${esc(cat)}" data-tag="${t}" title="Tag the whole column ${LABEL[t]}">${{correct:'✓',partly:'~',wrong:'✗'}[t]}</button>`).join('') + `</div></th>`;
    });
    html += '</tr>';
    rows.forEach(row => {
      html += `<tr><td class="rowlabel">${row}<div class="rowbtns">` + ['correct', 'partly', 'wrong'].map(t =>
        `<button data-row="${page}|${row}" data-tag="${t}" title="Tag the whole row ${LABEL[t]}">${{correct:'✓',partly:'~',wrong:'✗'}[t]}</button>`).join('') + '</div></td>';
      cats.forEach(cat => {
        const c = pc.find(x => x.row === row && x.category === cat);
        if (!c) { html += '<td></td>'; return; }
        const t = shown(c), conf = !!tags[c.key];
        const tip = `${c.category}, row ${c.row}\nWritten: ${c.written || '(blank)'}\nRead: ${c.read || '(nothing)'}` +
                    `\nSuggestion: ${LABEL[c.suggested] || '-'} (earlier check: ${c.visual}${c.rownum && c.rownum !== 'Right' && c.rownum !== '-' ? ', row ' + c.rownum.toLowerCase() : ''})`;
        html += `<td class="cell"><div class="cut s-${t} ${conf ? 'confirmed' : ''}" data-key="${esc(c.key)}" title="${esc(tip)}">` +
                (c.crop ? `<img loading="lazy" src="/crop?path=${encodeURIComponent(c.crop)}">` : '<div class="nocut">no cut</div>') +
                `<span class="tag">${LABEL[t] || '?'}</span></div></td>`;
      });
      html += '</tr>';
    });
    html += '</table>';
  }
  main.innerHTML = html || '<p>No cuts for this writer.</p>';
  progress();
}

document.addEventListener('click', e => {
  const cut = e.target.closest('.cut');
  if (cut) {
    const c = cuts.find(x => x.key === cut.dataset.key);
    // The first click confirms the suggestion; later clicks go Correct -> Partly -> Not at all.
    setTag([c.key], tags[c.key] ? NEXT[tags[c.key].tag] : (c.suggested || 'correct'));
    return;
  }
  const b = e.target.closest('button[data-tag]');
  if (b) {
    const list = pageCuts();
    let keys = [];
    if (b.dataset.col) { const [p, cat] = b.dataset.col.split('|'); keys = list.filter(c => c.page == p && c.category === cat).map(c => c.key); }
    if (b.dataset.row) { const [p, r] = b.dataset.row.split('|'); keys = list.filter(c => c.page == p && c.row == r).map(c => c.key); }
    setTag(keys, b.dataset.tag);
  }
});
document.getElementById('accept').onclick = () => {
  const todo = pageCuts().filter(c => !tags[c.key] && c.suggested);
  todo.forEach(c => { tags[c.key] = {tag: c.suggested, note: '', at: new Date().toISOString().slice(0, 19).replace('T', ' ')}; });
  render(); scheduleSave();
};
function step(d) {
  const w = document.getElementById('writer');
  const i = w.selectedIndex + d;
  if (i >= 0 && i < w.options.length) { w.selectedIndex = i; render(); window.scrollTo(0, 0); }
  else if (d > 0) { const s = document.getElementById('scan'); if (s.selectedIndex + 1 < s.options.length) { s.selectedIndex++; fillWriters(); w.selectedIndex = 0; render(); window.scrollTo(0, 0); } }
}
document.getElementById('prev').onclick = () => step(-1);
document.getElementById('next').onclick = () => step(1);
document.getElementById('report').onclick = async () => {
  const log = document.getElementById('log');
  log.style.display = 'block'; log.textContent = 'Saving, rerunning the cutting test with your tags and building the report - about a minute...';
  await fetch('/save', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags)});
  const r = await (await fetch('/report', {method: 'POST'})).json();
  log.textContent = (r.ok ? 'Done. The report and the workbook are open (outputs/logbook_cutting/).\n\n' : 'The report could not be made:\n\n') + r.log;
};
function fillWriters() {
  const s = document.getElementById('scan').value;
  const ws = [...new Set(cuts.filter(c => c.scan === s).map(c => c.writer))].sort();
  document.getElementById('writer').innerHTML = ws.map(w => `<option>${esc(w)}</option>`).join('');
}
document.getElementById('scan').onchange = () => { fillWriters(); render(); };
document.getElementById('writer').onchange = render;
(async () => {
  const d = await (await fetch('/data')).json();
  cuts = d.cuts; tags = d.tags;
  const scans = [...new Set(cuts.map(c => c.scan))];
  document.getElementById('scan').innerHTML = scans.map(s => `<option>${esc(s)}</option>`).join('');
  fillWriters(); render();
})();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    cuts = []
    tags = {}
    lock = threading.Lock()

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            return self._send(200, PAGE)
        if url.path == "/data":
            return self._send(200, json.dumps({"cuts": Handler.cuts, "tags": Handler.tags}), "application/json")
        if url.path == "/crop":
            rel = (parse_qs(url.query).get("path") or [""])[0]
            path = (CROPS / rel).resolve()
            if CROPS.resolve() in path.parents and path.is_file() and path.suffix.lower() in (".png", ".jpg"):
                return self._send(200, path.read_bytes(), "image/png" if path.suffix.lower() == ".png" else "image/jpeg")
            return self._send(404, "not found", "text/plain")
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/save":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                tags = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._send(400, "bad data", "text/plain")
            known = {c["key"] for c in Handler.cuts}
            with Handler.lock:
                Handler.tags = {k: v for k, v in tags.items() if k in known and v.get("tag") in TAGS}
                save_tags(Handler.tags, Handler.cuts)
            return self._send(200, json.dumps({"saved": len(Handler.tags)}), "application/json")
        if url.path == "/report":
            ok, log = make_report()
            if ok:
                import os
                for f in ("logbook_cutting_proof_report.pdf", "logbook_cutting_results.xlsx"):
                    try:
                        os.startfile(str(OUTPUTS / "logbook_cutting" / f))          # Windows: open it
                    except (AttributeError, OSError):
                        pass
                Handler.cuts = load_cuts()                                         # the rerun's cuts
            return self._send(200, json.dumps({"ok": ok, "log": log}), "application/json")
        return self._send(404, "not found", "text/plain")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    Handler.cuts = load_cuts()
    Handler.tags = load_tags()
    server = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    url = f"http://127.0.0.1:{a.port}/"
    print(f"Logbook cutting check: {url}  ({len(Handler.cuts)} cuts, {len(Handler.tags)} tagged so far)")
    print(f"Your tags are saved to {HUMAN}. Press Ctrl+C here to stop.")
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
