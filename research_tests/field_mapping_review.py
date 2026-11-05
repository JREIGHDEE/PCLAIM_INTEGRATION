"""Check the field mapping test's expected box table yourself: a page on this
computer showing every box of the table on the blank paper form and as
PClaimAssist fills it, where you mark each box Correct, change it, or remove
it - then make the reports with the checked table.

    python -m research_tests.field_mapping_review          (opens http://127.0.0.1:8766)

The table (inputs/field_mapping_expected.csv) says which box of each form
should hold which answer-key value, in which format. It was drafted from the
forms automatically; this check against the paper forms is what makes the
field mapping result independent of the code under test (until then it is
PROVISIONAL). For each box the page shows:
  the blank form      that spot of the paper form (PClaimAssist/forms/), the box
                      outlined - read its printed label
  as filled           the same spot on the PDF PClaimAssist saves for a test
                      patient, and the value the table expects there
Mark it Correct, or change its answer-key value / format / digit position (it
is then checked as changed), or remove it (not a logbook value). Boxes the
table left out can be added. Every change is saved at once to the table (the
original is kept as field_mapping_expected.before_review.csv). "Make the
reports" reruns the field mapping and OCR field mapping tests and their proof
reports with the checked table.

Served on 127.0.0.1 only; nothing leaves this computer.
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from research_tests import INPUTS, FORMS_DIR, OUTPUTS, REPO
from research_tests import field_mapping as fm

TABLE = fm.EXPECTED
BACKUP = TABLE.with_name("field_mapping_expected.before_review.csv")
PICS = OUTPUTS / "field_mapping" / "review"
VALUES = ["Last name", "First name", "Middle name", "Suffix", "Birthday", "Admitted date", "Admitted time",
          "Admitted AM/PM", "Went home date", "Went home time", "Went home AM/PM", "Street", "Barangay", "City",
          "Province", "Reason for admission", "Final diagnosis", "Member is patient", "Relationship"]
FORMATS = {"text": "the value in capitals", "date": "MM-DD-YYYY", "date_digit": "digit N of MMDDYYYY",
           "time_digit": "digit N of hhmm (12-hour)", "time": "h:mm when AM/PM = Position",
           "time_ampm": "h:mm AM / PM", "tick": "ticked when AM/PM = Position",
           "tick_value": "ticked when the value = Position"}


def read_table():
    with open(TABLE, newline="", encoding="utf-8-sig") as fh:
        return [dict(r) for r in csv.DictReader(fh) if (r.get("Form") or "").strip()]


def write_table(rows):
    if not BACKUP.exists():
        shutil.copyfile(TABLE, BACKUP)
    tmp = TABLE.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")          # as the file is kept in git
        w.writerow(fm.EXPECTED_COLUMNS)
        for r in rows:
            w.writerow([r.get(c, "") for c in fm.EXPECTED_COLUMNS])
    tmp.replace(TABLE)


def build_pictures(progress=print):
    """The blank form and a filled example of every box of every form ->
    PICS/<form>_<box>_blank.png / _filled.png, and PICS/boxes.json (every box
    of every form, with the example patient and what it shows there)."""
    import fitz
    from research_tests.common import answer_key
    from research_tests.common.forms_page import FormsPage
    PICS.mkdir(parents=True, exist_ok=True)
    patients = [p for p in answer_key.patients(INPUTS / "answer_key.xlsx")]
    info = {}

    def crop(doc, spot, form, box, tag):
        page = doc[spot["page"] - 1]
        rect = fm.box_rect(page, spot)
        page.draw_rect(rect, color=(0.9, 0, 0), width=1.2)
        area = fitz.Rect(rect.x0 - 120, rect.y0 - 34, rect.x1 + 120, rect.y1 + 26) & page.rect
        page.get_pixmap(dpi=150, clip=area).save(str(PICS / f"{form}_{box}_{tag}.png"))

    with FormsPage() as page:
        examples = {}                                  # form -> [(patient, data, pdf bytes, spots)]
        for p in patients:
            if all(len(examples.get(f, [])) >= 2 for f in fm.FORMS):
                break
            body, _ = answer_key.auto_populate(p)
            body["saved_values"] = answer_key.claim_values(p) or {}
            page.open_claim(body)
            baby = str(p.get("Member is patient") or "").lower() != "yes"
            for form in page.claim_forms():
                have = examples.setdefault(form, [])
                # one patient who is the member, one who is not (a newborn), per form
                if len(have) < 2 and all((str(x[0].get("Member is patient") or "").lower() != "yes") != baby
                                         for x in have):
                    progress(f"Filling {fm.FORM_NAMES[form]} for {p['Patient ID']}")
                    pdf, _ms = page.build_pdf(form)
                    have.append((p, pdf, {s["id"]: s for s in page.overlay_spots(form)}))
        for form, have in examples.items():
            if not have:
                continue
            spots = have[0][2]
            blank = FORMS_DIR / "forms" / fm.FORM_PDFS[form]
            for box, spot in spots.items():
                doc = fitz.open(str(blank))
                crop(doc, spot, form, box, "blank")
                doc.close()
                ex = [{"patient": p["Patient ID"], "member_is_patient": str(p.get("Member is patient") or ""),
                       "shows": s.get(box, {}).get("value", ""), "file": f"{form}_{box}_filled_{p['Patient ID']}.png"}
                      for p, _pdf, s in have]
                for (p, pdf, _s), e in zip(have, ex):
                    doc = fitz.open(stream=pdf, filetype="pdf")
                    crop(doc, spot, form, box, f"filled_{p['Patient ID']}")
                    doc.close()
                info[f"{form}|{box}"] = {"form": form, "box": box, "key": spot.get("key"), "page": spot["page"],
                                         "label": "", "examples": ex}
    (PICS / "boxes.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    return info


def expected_for(row, patient_id):
    """What the table row expects in its box for this patient (from the answer key)."""
    from research_tests.common import answer_key
    p = next((x for x in answer_key.patients(INPUTS / "answer_key.xlsx") if x["Patient ID"] == patient_id), None)
    if not p:
        return ""
    try:
        return fm.expected_value({"Answer-key value": row["Answer-key value"], "Format": row["Format"],
                                  "Position": row.get("Position") or "", "Note": row.get("Note") or ""}, p)
    except Exception as exc:              # an unfinished edit: say so instead of failing
        return f"(cannot work it out: {exc})"


def make_reports():
    log = []
    for module in ("research_tests.field_mapping", "research_tests.field_mapping_report",
                   "research_tests.ocr_field_mapping", "research_tests.ocr_field_mapping_report"):
        done = subprocess.run([sys.executable, "-m", module], cwd=str(REPO), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        log.append(f"$ python -m {module}\n" + "\n".join((done.stdout + done.stderr).strip().splitlines()[-6:]))
        if done.returncode:
            return False, "\n\n".join(log)
    return True, "\n\n".join(log)


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Field mapping table check</title>
<style>
 :root{--ok:#1a8f3c;--chg:#0b5cad;--bad:#d01f1f;--muted:#5a6570;--line:#d5dbe2;--bg:#f6f8fa}
 *{box-sizing:border-box} body{margin:0;font:14px system-ui,sans-serif;color:#1d1d1f;background:var(--bg)}
 header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
 header h1{font-size:16px;margin:0 10px 0 0;color:#0b3d6e}
 select,button,input{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:#fff}
 button{cursor:pointer} button.primary{background:#0b5cad;color:#fff;border-color:#0b5cad}
 main{padding:12px 16px 80px;max-width:1200px} #progress{color:var(--muted)} #saved{color:var(--ok);font-size:12px}
 .card{background:#fff;border:1px solid var(--line);border-left:6px solid #9aa6b2;border-radius:8px;padding:10px 12px;margin:10px 0}
 .card.st-correct{border-left-color:var(--ok)} .card.st-changed{border-left-color:var(--chg)} .card.st-removed{border-left-color:var(--bad);opacity:.6}
 .head{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap} .head b{font-size:15px} .muted{color:var(--muted);font-size:12px}
 .pics{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0} .pics figure{margin:0} .pics img{max-height:120px;max-width:540px;border:1px solid var(--line)}
 .pics figcaption{font-size:12px;color:var(--muted)} .edit{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
 .status{font-weight:600} .st-correct .status{color:var(--ok)} .st-changed .status{color:var(--chg)} .st-removed .status{color:var(--bad)}
 #log{white-space:pre-wrap;font:12px ui-monospace,monospace;background:#fff;border:1px solid var(--line);padding:8px;display:none;margin:10px 16px}
 .add{background:#fff;border:1px dashed var(--line);border-radius:8px;padding:10px;margin:16px 0}
</style></head><body>
<header>
 <h1>Field mapping table check</h1>
 <label>Form <select id="form"></select></label>
 <label><input type="checkbox" id="todo"> only boxes not checked yet</label>
 <button id="acceptAll" title="Mark every unchecked box on this form Correct">Mark the rest of this form Correct</button>
 <span id="progress"></span><span id="saved"></span>
 <button class="primary" id="report">Make the reports</button>
</header>
<div id="log"></div>
<main id="main"></main>
<script>
let rows = [], boxes = {}, values = [], formats = {}, saveTimer = null;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const state = r => r._removed ? 'removed' : (r.Checked || '').toLowerCase() === 'yes' ? (r._changed ? 'changed' : 'correct') : 'todo';
const STATE = {correct: 'Checked: correct', changed: 'Checked: changed', removed: 'Removed (not a logbook value)', todo: 'Not checked yet'};

function save() {
  clearTimeout(saveTimer); document.getElementById('saved').textContent = 'saving...';
  saveTimer = setTimeout(async () => {
    const r = await fetch('/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(rows)});
    const d = await r.json().catch(() => ({}));
    document.getElementById('saved').textContent = r.ok ? 'saved' : 'NOT SAVED - is the window running the tool still open?';
    if (d.expected) { d.expected.forEach((v, i) => { rows[i]._expected = v; }); render(); }
  }, 300);
}
function progress() {
  const live = rows.filter(r => !r._removed), done = rows.filter(r => state(r) !== 'todo').length;
  const f = document.getElementById('form').value, here = rows.filter(r => r.Form === f);
  document.getElementById('progress').textContent = `This form: ${here.filter(r => state(r) !== 'todo').length} of ${here.length} checked - all: ${done} of ${rows.length}`;
}
function card(r, i) {
  const b = boxes[`${r.Form.toLowerCase()}|${r['Box ID']}`] || {examples: []};
  const st = state(r);
  const pics = `<figure><img loading="lazy" src="/pic?f=${encodeURIComponent(r.Form.toLowerCase() + '_' + r['Box ID'] + '_blank.png')}"><figcaption>The blank paper form - the box in red</figcaption></figure>` +
    (b.examples || []).map((e, k) => `<figure><img loading="lazy" src="/pic?f=${encodeURIComponent(e.file)}"><figcaption>As PClaimAssist fills it for ${esc(e.patient)}${e.member_is_patient.toLowerCase() === 'yes' ? '' : ' (not the member)'}: shows <b>${esc(e.shows) || '(empty)'}</b>; the table expects <b>${esc((r._expected || [])[k]) || '(empty)'}</b></figcaption></figure>`).join('');
  const opt = (list, cur) => list.map(v => `<option ${v === cur ? 'selected' : ''}>${esc(v)}</option>`).join('');
  return `<div class="card st-${st}" data-i="${i}">
    <div class="head"><b>${esc(r.Form)} - ${esc(r['Box ID'])}</b><span class="muted">printed label (drafted): ${esc(r['Printed label (check on the paper form)']) || '-'}</span><span class="status">${STATE[st]}</span></div>
    <div class="pics">${pics}</div>
    <div class="edit">
      <label>Printed label <input data-f="Printed label (check on the paper form)" size="22" value="${esc(r['Printed label (check on the paper form)'])}"></label>
      <label>Answer-key value <select data-f="Answer-key value">${opt(values, r['Answer-key value'])}</select></label>
      <label>Format <select data-f="Format">${Object.keys(formats).map(k => `<option value="${k}" ${k === r.Format ? 'selected' : ''}>${k} - ${esc(formats[k])}</option>`).join('')}</select></label>
      <label>Position <input data-f="Position" size="6" value="${esc(r.Position)}"></label>
      <label>Note <input data-f="Note" size="34" value="${esc(r.Note)}"></label>
      <button data-act="correct">&#10003; Correct</button>
      <button data-act="remove">Remove</button>
      ${st !== 'todo' ? '<button data-act="undo">Undo</button>' : ''}
    </div></div>`;
}
function render() {
  const f = document.getElementById('form').value, todo = document.getElementById('todo').checked;
  let html = '';
  rows.forEach((r, i) => { if (r.Form === f && (!todo || state(r) === 'todo')) html += card(r, i); });
  const listed = new Set(rows.filter(r => r.Form === f).map(r => r['Box ID']));
  const others = Object.values(boxes).filter(b => b.form === f.toLowerCase() && !listed.has(b.box)).map(b => b.box).sort();
  html += `<div class="add"><b>A box the table left out?</b> <select id="addbox">${others.map(b => `<option>${esc(b)}</option>`).join('')}</select>
    <button id="addbtn">Add it to the table</button> <span class="muted">then set its answer-key value and format, and mark it Correct</span></div>`;
  document.getElementById('main').innerHTML = html || '<p>Nothing here.</p>';
  progress();
}
document.addEventListener('change', e => {
  const el = e.target.closest('[data-f]'); if (!el) return;
  const r = rows[+el.closest('.card').dataset.i];
  r[el.dataset.f] = el.value; r.Checked = 'yes'; r._changed = true; r._removed = false; save(); render();
});
document.addEventListener('click', e => {
  const b = e.target.closest('button[data-act]');
  if (b) {
    const r = rows[+b.closest('.card').dataset.i];
    if (b.dataset.act === 'correct') { r.Checked = 'yes'; r._removed = false; }
    if (b.dataset.act === 'remove') { r._removed = true; r.Checked = 'yes'; }
    if (b.dataset.act === 'undo') { Object.assign(r, r._orig); r.Checked = ''; r._removed = false; r._changed = false; }
    save(); render(); return;
  }
  if (e.target.id === 'addbtn') {
    const box = document.getElementById('addbox').value; if (!box) return;
    const r = {Form: document.getElementById('form').value, 'Box ID': box, 'Printed label (check on the paper form)': '',
               'Answer-key value': values[0], Format: 'text', Position: '', Note: 'added on the check', Checked: 'yes', _changed: true};
    r._orig = {...r}; rows.push(r); save(); render();
  }
});
document.getElementById('acceptAll').onclick = () => {
  const f = document.getElementById('form').value;
  rows.forEach(r => { if (r.Form === f && state(r) === 'todo') r.Checked = 'yes'; }); save(); render();
};
document.getElementById('form').onchange = render; document.getElementById('todo').onchange = render;
document.getElementById('report').onclick = async () => {
  const log = document.getElementById('log'); log.style.display = 'block';
  log.textContent = 'Saving, rerunning the field mapping and OCR field mapping tests with the checked table and building their reports - a few minutes...';
  await fetch('/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(rows)});
  const r = await (await fetch('/report', {method:'POST'})).json();
  log.textContent = (r.ok ? 'Done. The reports and workbooks are open (outputs/field_mapping/, outputs/ocr_field_mapping/).\n\n' : 'The reports could not be made:\n\n') + r.log;
};
(async () => {
  const d = await (await fetch('/data')).json();
  rows = d.rows; boxes = d.boxes; values = d.values; formats = d.formats;
  rows.forEach((r, i) => { r._orig = {...r}; r._expected = d.expected[i]; r._changed = !!r._changed; });
  document.getElementById('form').innerHTML = [...new Set(rows.map(r => r.Form))].map(f => `<option>${esc(f)}</option>`).join('');
  render();
})();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    rows, boxes, examples_by_box = [], {}, {}
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

    def _expected(self, rows):
        out = []
        for r in rows:
            b = Handler.boxes.get(f"{r.get('Form', '').lower()}|{r.get('Box ID')}") or {}
            out.append([expected_for(r, e["patient"]) for e in b.get("examples", [])])
        return out

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            return self._send(200, PAGE)
        if url.path == "/data":
            return self._send(200, json.dumps({"rows": Handler.rows, "boxes": Handler.boxes,
                                               "values": VALUES + ["(not a logbook value)"], "formats": FORMATS,
                                               "expected": self._expected(Handler.rows)}), "application/json")
        if url.path == "/pic":
            name = (parse_qs(url.query).get("f") or [""])[0]
            path = (PICS / name).resolve()
            if PICS.resolve() in path.parents and path.is_file() and path.suffix == ".png":
                return self._send(200, path.read_bytes(), "image/png")
            return self._send(404, "not found", "text/plain")
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/save":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                rows = json.loads(self.rfile.read(length) or b"[]")
            except ValueError:
                return self._send(400, "bad data", "text/plain")
            keep = []
            for r in rows:
                if r.get("_removed") or r.get("Answer-key value") == "(not a logbook value)":
                    continue
                if r.get("Format") not in FORMATS or not r.get("Form") or not r.get("Box ID"):
                    continue
                keep.append({c: str(r.get(c) or "") for c in fm.EXPECTED_COLUMNS})
            with Handler.lock:
                write_table(keep)
                Handler.rows = [{**{c: str(r.get(c) or "") for c in fm.EXPECTED_COLUMNS},
                                 "_removed": bool(r.get("_removed")), "_changed": bool(r.get("_changed"))}
                                for r in rows]
            return self._send(200, json.dumps({"saved": len(keep), "expected": self._expected(Handler.rows)}),
                              "application/json")
        if url.path == "/report":
            ok, log = make_reports()
            if ok:
                import os
                for f in ("field_mapping/field_mapping_proof_report.pdf", "field_mapping/field_mapping_results.xlsx",
                          "ocr_field_mapping/ocr_field_mapping_proof_report.pdf",
                          "ocr_field_mapping/ocr_field_mapping_results.xlsx"):
                    try:
                        os.startfile(str(OUTPUTS / f))
                    except (AttributeError, OSError):
                        pass
            return self._send(200, json.dumps({"ok": ok, "log": log}), "application/json")
        return self._send(404, "not found", "text/plain")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--redraw", action="store_true", help="draw the box pictures again")
    a = ap.parse_args()
    if a.redraw or not (PICS / "boxes.json").is_file():
        print("Drawing the box pictures (once, about half a minute)...")
        Handler.boxes = build_pictures(lambda m: print("  " + m))
    else:
        Handler.boxes = json.loads((PICS / "boxes.json").read_text(encoding="utf-8"))
    Handler.rows = [{**r, "_removed": False, "_changed": False} for r in read_table()]
    server = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    url = f"http://127.0.0.1:{a.port}/"
    checked = sum(1 for r in Handler.rows if (r.get("Checked") or "").lower() == "yes")
    print(f"Field mapping table check: {url}  ({len(Handler.rows)} boxes, {checked} checked so far)")
    print(f"Changes are saved to {TABLE}. Press Ctrl+C here to stop.")
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
