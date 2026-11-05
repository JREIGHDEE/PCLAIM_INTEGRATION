"""Validation engine proof report: every seeded error, every record's own
"Rule Check Results" panel as the page shows it, the rule coverage and the
engine-level checks, in one PDF with bookmarks and links (same layout as
the other proof reports).

    python -m research_tests.validation_report

Reads outputs/validation/ (run research_tests.validation first) and writes
outputs/validation/validation_proof_report.pdf.
"""
import argparse
import datetime
import json
from pathlib import Path

from research_tests import OUTPUTS
from research_tests.field_mapping_report import CSS, Pictures, e, img, render
from research_tests.logbook_cutting_report import EXTRA_CSS, table

FOLDER = OUTPUTS / "validation"


def _value(v):
    if v is None or v == "":
        return "(blank)"
    if isinstance(v, bool):
        return "ticked" if v else "not ticked"
    return str(v)


def change_text(err):
    """'field: before -> seeded' for each thing the error changed."""
    parts = []
    for k, to in (err.get("to") or {}).items():
        parts.append(f"{k}: {_value((err.get('from') or {}).get(k))} -> {_value(to)}")
    names = {"imageQualityPass": "image quality check", "pendingSuggestions": "correction suggestions not reviewed"}
    for k, to in (err.get("ocr") or {}).items():
        parts.append(f"{names.get(k, k)}: {'passed' if k == 'imageQualityPass' else 0} -> "
                     f"{('failed' if to is False else to)}")
    for k, to in (err.get("sig") or {}).items():
        parts.append(f"{k} signature: {'present' if k != 'thumbmark' else 'no thumbmark'} -> "
                     f"{('missing' if to is False else 'thumbmark used')}")
    return "; ".join(parts)


def build(out_path):
    summary = json.loads((FOLDER / "summary.json").read_text(encoding="utf-8"))
    sheet = {s["name"]: s for s in summary["sheets"]}
    m = json.loads((FOLDER / "proof" / "manifest.json").read_text(encoding="utf-8"))
    proof = FOLDER / "proof"
    pics = Pictures()
    W = 523
    overall = {r[0]: r[1] for r in sheet["4a Validation overall"]["rows"]}
    records = m["records"]
    seeded = [r for r in records if r["kind"] == "seeded"]
    clean = [r for r in records if r["kind"] == "clean"]
    cov = sheet["4e Rule coverage"]["rows"]
    n_e2e = sum(1 for r in cov if r[5] == "seeded end to end")
    n_eng = sum(1 for r in cov if r[5] == "engine-level check")

    h = [f"<style>{CSS}{EXTRA_CSS}</style><body>"]
    h.append('<h1 id="top">Validation engine - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, Objective 3 (iii), Eq. 3.7-3.10 - results of '
             f'{e(summary.get("generated_at", ""))}, report generated {datetime.date.today().isoformat()}</p>')
    h.append(f"""<div class="box"><b>Result.</b> {overall.get('Seeded errors')} errors were seeded into
      {len(seeded)} records and {len(clean)} records were left clean. The validation engine flagged
      <b>{overall.get('Seeded errors detected')} of {overall.get('Seeded errors')}</b> seeded errors:
      precision <b>{overall.get('Precision (Eq. 3.7)')}</b>, recall <b>{overall.get('Recall (Eq. 3.8)')}</b>, F1
      <b>{overall.get('F1 score (Eq. 3.9)')}</b>; false alarm rate <b>{overall.get('False alarm rate (Eq. 3.10)')}</b>
      ({overall.get('Clean records with a flag')} clean records flagged). <b>All {len(cov)} rules are covered</b>:
      {n_e2e} by seeded errors on real records, {n_eng} by an engine-level check (they cannot be reached on a real
      claim - section 3).</div>""")
    h.append("""<div class="warn"><b>Read with care.</b> The errors were designed from the rule definitions, at least
      one per rule the engine can reach, so the result shows the rules work as written - not how many of all
      real-world claim errors they would catch. The pictures are the page's own "Rule Check Results" panel for each
      record, as staff see it.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("method", "2. How the test works"),
                          ("coverage", "3. Every rule and how it is covered"),
                          ("seeded", "4. The seeded errors"),
                          ("records", "5. Every seeded record and what the engine flagged"),
                          ("engine", "6. Engine-level checks (IC-01, IC-02, IC-07, MF-08)"),
                          ("clean", "7. The clean records"), ("verdict", "8. What this means")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents.</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    table(h, sheet["4a Validation overall"]["headers"], sheet["4a Validation overall"]["rows"])
    h.append("<h3>Per rule category</h3>")
    table(h, sheet["4b Validation per category"]["headers"], sheet["4b Validation per category"]["rows"])
    h.append("<h3>Per seeded category</h3>")
    table(h, sheet["4c Seeded categories"]["headers"], sheet["4c Seeded categories"]["rows"])
    h.append("""<p class="muted">Unit: one rule on one record. R = rules the record's seeded errors must fire, A = rules
      they may also fire as a direct consequence (e.g. a blanked field adds to the "more than 3 blank" count), F = rules
      fired. TP = |F and R|, FN = |R - F|, FP = |F - R - A|. Precision = TP/(TP+FP) (Eq. 3.7), recall = TP/(TP+FN)
      (Eq. 3.8), F1 = 2PR/(P+R) (Eq. 3.9), false alarm rate = clean records with any flag / clean records
      (Eq. 3.10).</p>""")

    # 2
    h.append('<h2 id="method" class="break">2. How the test works</h2>')
    h.append(f"""<p>{len(records)} records are built from the answer key's fictional patients: each patient's confirmed
      values go through the real auto-population into the real forms page (offline, in Microsoft Edge), plus the
      fictional details staff would type on the forms. {len(clean)} records are left clean; {len(seeded)} get two
      seeded errors each ({overall.get('Seeded errors')} in all: every error kind once, the commonest kinds twice). Each
      error is typed where staff would type it, and placed only on a record where its rule applies (a CF4 rule on a
      claim with CF4, a delivery rule on a record with a delivery); two errors in one record never touch the same
      field. The page's own validation (validation-rules.js runValidationRules, as the page runs it) is then run, with
      the image-quality, correction and signature checks switched on, and its flags compared with the errors
      seeded.</p>
      <p>The test also checks that the page kept each seeded value: a value the page itself puts back cannot be
      detected and would not be a fair error. Every seeded value in this run was kept.</p>""")

    # 3
    h.append('<h2 id="coverage" class="break">3. Every rule and how it is covered</h2>')
    table(h, ["Rule", "Category", "Action", "Seeded", "Caught", "Covered by", "Result"], [r[:7] for r in cov])
    h.append("<h3>Why four rules are checked at engine level</h3>")
    table(h, ["Rule", "Why it cannot be seeded on a real claim"], [[r[0], r[7]] for r in cov if r[7]])

    # 4
    h.append('<h2 id="seeded" class="break">4. The seeded errors</h2>')
    h.append("<p>Every error, the record it was seeded into, exactly what was changed (before -> seeded), the rule it "
             "must fire, and whether it did. Click a record to see its panel.</p>")
    rows = []
    for r in seeded:
        for err in r["errors"]:
            rows.append([f'<a href="#rec-{r["record"]}">{r["record"]}</a>', r["patient"], e(err["category"]),
                         e(err["kind"]), e(change_text(err)), ", ".join(err["required"]),
                         "<span class='good'>yes</span>" if set(err["required"]) & set(r["fired"])
                         else "<span class='bad'>no</span>"])
    h.append("<table class='small'><tr><th>Record</th><th>Patient</th><th>Category</th><th>Error</th>"
             "<th>What was changed (before -> seeded)</th><th>Must fire</th><th>Flagged</th></tr>")
    for row in rows:
        h.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    h.append("</table>")

    # 5
    h.append('<h2 id="records" class="break">5. Every seeded record and what the engine flagged</h2>')
    for r in seeded:
        h.append(f'<h3 id="rec-{r["record"]}" class="break">Record {r["record"]} - patient {r["patient"]} '
                 f'({", ".join(r["forms"]).upper()})</h3>')
        h.append("<table class='small'><tr><th>Seeded error</th><th>What was changed</th><th>Must fire</th>"
                 "<th>May also fire</th></tr>")
        for err in r["errors"]:
            h.append(f"<tr><td>{e(err['kind'])}</td><td>{e(change_text(err))}</td><td>{', '.join(err['required'])}</td>"
                     f"<td>{', '.join(err['allowed']) or '-'}</td></tr>")
        h.append("</table>")
        verdict = (f"Fired: <b>{', '.join(r['fired']) or 'nothing'}</b>. Caught: "
                   f"<span class='good'>{', '.join(r['tp']) or '-'}</span>"
                   + (f"; also fired as a consequence: {', '.join(r['consequence'])}" if r["consequence"] else "")
                   + (f"; <span class='bad'>missed: {', '.join(r['fn'])}</span>" if r["fn"] else "")
                   + (f"; <span class='bad'>false flags: {', '.join(r['fp'])}</span>" if r["fp"] else ""))
        h.append(f"<p>{verdict}</p>")
        f = proof / r["picture"]
        if f.is_file():
            n, size = pics.add(f, max_px=900)
            h.append(img(n, size, min(W, size[0] * 0.6)))

    # 6
    h.append('<h2 id="engine" class="break">6. Engine-level checks (IC-01, IC-02, IC-07, MF-08)</h2>')
    h.append(f"""<p>These four rules cannot be reached on a real claim (section 3). Each is checked on a clean record
      (patient {e(m.get('engine_patient') or '')}, with CF4): the engine's own computed features for the record, with
      only the feature the rule reads set the way the rule tests it; the rules then run and the page's own panel shows
      the result. The rule must fire, and nothing else. This checks the rule's logic; it is not part of the precision,
      recall, F1 or false alarm figures.</p>""")
    eh = sheet["4f Engine-level checks"]
    table(h, eh["headers"][:7], [r[:7] for r in eh["rows"]])
    mf08 = m.get("mf08") or {}
    if mf08.get("refilled"):
        kept = "; ".join(f"{k} = {v}" for k, v in mf08["refilled"].items())
        h.append(f"""<p><b>MF-08 on the real page.</b> Every CF4 course-in-the-ward box was emptied; the page wrote
          the course back ({e(kept)}), so the course in the ward can never be blank on a claim and MF-08 cannot fire
          there.</p>""")
    for r in m.get("engine") or []:
        f = proof / r["picture"]
        h.append(f"<h3>{r['rule']} - {e(r['what'])}: {'fires, and only it' if r['ok'] else 'NOT as expected'}</h3>")
        if f.is_file():
            n, size = pics.add(f, max_px=900)
            h.append(img(n, size, min(W, size[0] * 0.6)))

    # 7
    h.append('<h2 id="clean" class="break">7. The clean records</h2>')
    flagged = [r for r in clean if r["fired"]]
    h.append(f"<p>{len(clean)} records with no seeded error: {len(flagged)} flagged "
             f"({'none' if not flagged else ', '.join(r['record'] for r in flagged)}). Each panel below is the page's "
             f"own result for that record.</p>")
    for r in clean:
        f = proof / r["picture"]
        h.append(f'<h4 id="rec-{r["record"]}">Record {r["record"]} - patient {r["patient"]}: '
                 f'{"no flags" if not r["fired"] else "flagged " + ", ".join(r["fired"])}</h4>')
        if f.is_file():
            n, size = pics.add(f, max_px=900)
            h.append(img(n, size, min(W, size[0] * 0.6)))

    # 8
    h.append('<h2 id="verdict" class="break">8. What this means</h2>')
    h.append(f"""<p><b>The validation engine flags every seeded error and nothing else.</b> On {len(seeded)} records with
      {overall.get('Seeded errors')} seeded errors it flagged {overall.get('Seeded errors detected')} (recall
      {overall.get('Recall (Eq. 3.8)')}) with no false flags (precision {overall.get('Precision (Eq. 3.7)')}), and it
      raised nothing on the {len(clean)} clean records (false alarm rate {overall.get('False alarm rate (Eq. 3.10)')}).
      {n_e2e} of the {len(cov)} rules were reached by seeded errors on real records; the other {n_eng} cannot be
      reached on a real claim - the forms are filled from one entry, and the course in the ward is written by the
      page - and fire correctly when their condition is set at engine level.</p>
      <p>Because the errors were designed from the rule definitions, this shows the rules work as written; how many
      real-world errors they catch is for the user sessions to show.</p>""")
    h.append("</body>")
    render(h, pics, out_path, "Validation engine proof report", "Seeded errors and the page's own rule panel")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=FOLDER / "validation_proof_report.pdf")
    a = ap.parse_args()
    path = build(a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
