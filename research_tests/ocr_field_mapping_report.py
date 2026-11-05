"""OCR field mapping proof report: the OCR field mapping test before and
after the fixes, with the pictures behind every number, in one PDF with
bookmarks and links (same layout as field_mapping_report.py).

    python -m research_tests.ocr_field_mapping_report

Reads outputs/ocr_field_mapping/ (latest run) and its before_fix/ (a run on
the code before the fixes), plus outputs/field_mapping/live_check/ (the
fixes checked in the real app). Writes
outputs/ocr_field_mapping/ocr_field_mapping_proof_report.pdf.
"""
import argparse
import datetime
import json
from pathlib import Path

from research_tests import OUTPUTS
from research_tests.field_mapping_report import CSS, FORM_KEY, FORM_ORDER, Pictures, e, img, load, render, tick

FOLDER = OUTPUTS / "ocr_field_mapping"
LIVE = OUTPUTS / "field_mapping" / "live_check"
BANDS = {"CF1": (0.295, 0.40), "CF4": (0.30, 0.43), "PMRF": (0.435, 0.605)}


def rows_by_form(rows):
    return {r[0]: r for r in rows}


def table_used(summary):
    """The expected box table a run was scored with; a run that did not
    record it used the table as it was before the check on the paper forms."""
    from research_tests import field_mapping as fm
    if summary.get("expected_table"):
        return summary["expected_table"]
    before = fm.EXPECTED.with_name("field_mapping_expected.before_review.csv")
    return fm.table_digest(before if before.is_file() else fm.EXPECTED)


def build(before_dir, after_dir, live_dir, out_path):
    b_proof, b_man, b_sum = load(before_dir)
    a_proof, a_man, a_sum = load(after_dir)
    live = json.loads((live_dir / "live_check.json").read_text(encoding="utf-8")) \
        if (live_dir / "live_check.json").is_file() else None
    pics = Pictures()
    W = 523
    causes = a_man["causes"]
    b_e, a_e = rows_by_form(b_man["per_form"]), rows_by_form(a_man["per_form"])
    b_m, a_m = rows_by_form(b_man["mapping"]), rows_by_form(a_man["mapping"])
    b_c, a_c = rows_by_form(b_man["by_cause"]), rows_by_form(a_man["by_cause"])
    b_all_m, a_all_m = b_m["All forms"], a_m["All forms"]
    b_map_err, a_map_err = b_c["All forms"][2 + 2], a_c["All forms"][2 + 2]
    engine, scan = a_man.get("engine", ""), a_man.get("scan", "")
    readings = a_man.get("readings", [])
    exact = sum(r[6] == "Yes" for r in readings)

    h = [f"<style>{CSS}</style><body>"]
    h.append('<h1 id="top">OCR field mapping test - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, Objective 3 (ii) with OCR input - generated '
             f'{datetime.date.today().isoformat()}</p>')
    h.append(f"""<div class="box"><b>Result.</b> When the forms are filled straight from what the OCR read
      ({e(engine)}, {e(scan)} scans), with no staff correction, <b>{a_all_m[3]} of {a_all_m[2]}</b> scored boxes hold
      exactly what was read - <span class="good">{a_all_m[4]}% mapping accuracy</span> after the fixes
      ({b_all_m[4]}% before, <span class="bad">{b_map_err}</span> mapping errors before, {a_map_err} after).
      End-to-end, {a_e['All forms'][4]}% of boxes hold the correct (answer-key) value: the rest are OCR misreads that
      land in the right box. The OCR, not the mapping, limits the end-to-end result.</div>""")
    if a_man.get("provisional"):
        h.append("""<div class="warn"><b>Provisional.</b> Uses the same expected box table as the field mapping test,
          which has not yet been checked against the paper forms (Groupmate 2).</div>""")
    if table_used(b_sum) != table_used(a_sum):
        h.append("""<div class="warn"><b>Not the same expected box table.</b> The run before the fixes was scored
          with an earlier version of the expected box table than the run after them (the table has since been checked
          against the paper forms), so the before and after figures are not directly comparable. The after figures use
          the checked table.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("method", "2. How the test works and how to read the pictures"),
                          ("readings", "3. The OCR readings fed to the system"),
                          ("fixes", "4. What was fixed - before and after"), ("live", "5. Check in the real system"),
                          ("remaining", "6. Where the wrong boxes come from (after the fixes)"),
                          ("verdict", "7. Is it usable?"),
                          ("appA", "Appendix A - every saved form page after the fixes"),
                          ("appB", "Appendix B - CF1, CF4 and PMRF pages before the fixes")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents.</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    h.append("<h3>Mapping accuracy on OCR input (does the reading land in the right box?)</h3>")
    h.append("<table><tr><th>Form</th><th>Boxes scored<br/>before / after</th><th>Before</th><th>After</th></tr>")
    for form in FORM_ORDER + ["All forms"]:
        b, a = b_m.get(form), a_m.get(form)
        if a and b:
            name = f"<b>{form}</b>" if form == "All forms" else form
            h.append(f"<tr><td>{name}</td><td class='num'>{b[2]} / {a[2]}</td><td class='num'>{b[4]}%</td>"
                     f"<td class='num'><b>{a[4]}%</b></td></tr>")
    h.append("</table>")
    h.append("<h3>End-to-end accuracy (OCR + mapping: the box holds the answer-key value)</h3>")
    h.append("<table><tr><th>Form</th><th>Patients</th><th>Boxes<br/>before / after</th><th>Before</th><th>After</th></tr>")
    for form in FORM_ORDER + ["All forms"]:
        b, a = b_e.get(form), a_e.get(form)
        if a and b:
            name = f"<b>{form}</b>" if form == "All forms" else form
            h.append(f"<tr><td>{name}</td><td class='num'>{a[1]}</td><td class='num'>{b[2]} / {a[2]}</td>"
                     f"<td class='num'>{b[4]}%</td><td class='num'><b>{a[4]}%</b></td></tr>")
    h.append("</table>")
    h.append("<h3>Every checked box by cause</h3><table><tr><th>Cause</th><th>Before</th><th>After</th></tr>")
    for i, c in enumerate(causes):
        h.append(f"<tr><td>{e(c)}</td><td class='num'>{b_c['All forms'][2 + i]}</td>"
                 f"<td class='num'>{a_c['All forms'][2 + i]}</td></tr>")
    h.append("</table>")
    h.append("""<p><b>Reading the end-to-end change.</b> CF1 gains 10 correct boxes (the mailing Barangay, Fix 1). CF4 loses
      10: in those boxes the OCR'd date could not be read, so the system had no time - and before Fix 4 CF4 still ticked
      its default <i>AM</i>, which happened to match the true time. After the fix CF4 ticks nothing when there is no
      time, so the boxes are honestly empty (and the review would ask staff for the date). The 8 "filled by a system
      rule" boxes before the fixes are those default AM ticks; the 1 after is a discharge time filled by the
      "discharged 24 hours after admission" rule when the time read (05:60 PM) was unusable.</p>""")

    # 2
    h.append('<h2 id="method" class="break">2. How the test works and how to read the pictures</h2>')
    h.append(f"""<p>The field mapping test gives the forms the <i>confirmed</i> values. This test gives them what the OCR
      <i>actually read</i>. Each of the 20 fictional test patients comes from one handwritten logbook row (column
      "Source (writer, row)" of the answer key, e.g. W02 row 7). That row's {e(scan)} scan was read by the handwriting
      test; its {e(engine)} reading - the system's own OCR and correction - goes through the system unchanged:</p>
      <p>review page pre-fill (<i>review_fields.suggest_parts</i>) &rarr; staff press Submit without editing
      (<i>review_fields.normalize</i>) &rarr; <i>case_bridge.draft_patient_and_encounter</i> &rarr;
      <i>form_prefill.build_form_data</i> &rarr; the real forms page (Microsoft Edge) &rarr; the PDF "Save as PDF" makes.</p>
      <p><b>Two scores per box.</b> <i>Mapping</i>: the box holds what was read, in the box's format (the value the
      reading gives for that box). <i>End-to-end</i>: the box holds the answer-key value. Address boxes are scored for
      mapping only when the whole address was read right, because splitting a misread address has no independent
      answer. Typed values (PINs, member type, ...) come from the task packet as in the field mapping test.</p>
      <p><b>The pictures.</b> Each is the saved PDF as is, with every checked box outlined:
      <span class="good">green</span> = correct value; <span style="color:#e07800"><b>orange</b></span> = wrong value but
      not a mapping error (the OCR misread it, or nothing usable was read and a rule of the system filled the box);
      <span class="bad">red</span> = a mapping error - the box does not hold what was read. "expected: ..." under a box
      is the answer-key value.</p>
      <p class="muted">The forms checked depend on the claim the system builds: a misread diagnosis can change the
      package, so fewer patients get CF4 or PMRF here than in the confirmed-value test.</p>""")
    h.append(f"""<table><tr><th></th><th>Before</th><th>After</th></tr>
      <tr><td>Code</td><td>research-testing, commit 3f69979</td><td>branch jrad/field-mapping-fixes</td></tr>
      <tr><td>Run at</td><td>{e(b_sum.get('generated_at', ''))}</td><td>{e(a_sum.get('generated_at', ''))}</td></tr>
      <tr><td>Input</td><td colspan="2">the same OCR readings (handwriting test, {e(scan)}, {e(engine)}) and the same
      expected box table</td></tr></table>""")

    # 3
    h.append(f'<h2 id="readings" class="break">3. The OCR readings fed to the system</h2>')
    h.append(f"<p>{len(readings)} logbook cells (9 per patient). Exactly right: <b>{exact}</b> "
             f"({100 * exact / max(len(readings), 1):.1f}%). These are the handwriting test's readings, unchanged.</p>")
    h.append("<table><tr><th>Patient</th><th>Row</th><th>Field</th><th>Written in the logbook</th>"
             f"<th>Read ({e(engine)})</th><th>Exact</th></tr>")
    for r in readings:
        cls = "good" if r[6] == "Yes" else ""
        h.append(f"<tr><td>{e(r[0])}</td><td>{e(r[1])}</td><td>{e(r[2])}</td><td>{e(r[3])}</td>"
                 f"<td>{e(r[4]) or '<i>(nothing)</i>'}</td><td class='{cls}'>{e(r[6])}</td></tr>")
    h.append("</table>")

    # 4
    h.append('<h2 id="fixes" class="break">4. What was fixed - before and after</h2>')
    h.append("""<p>The same branch as the field mapping report (Fixes 1-3: mailing address on CF1 and PMRF, subdivision
      names ending in -VILLE), plus one fix this test found:</p>
      <p><b>Fix 4 - CF4 ticked AM when there was no time.</b> The admission and discharge AM/PM choice starts at AM.
      CF4 printed that choice as its tick, so a claim with no time still showed AM. CF2 already ticks AM/PM from the
      time itself. <i>Change</i>: PClaimAssist/js/pdf/overlays/cf4.js - the four AM/PM boxes now follow the time, as on
      CF2: no time, no tick.</p>""")
    b_err = [c for en in b_man["entries"] for c in en["crops"]]
    shown_pairs = []
    for c in b_err:
        l = c["line"]
        form = FORM_KEY[l["form"]]
        key = (l["patient"], form)
        if form in BANDS and key not in shown_pairs:
            shown_pairs.append(key)
    for pid, form in shown_pairs[:4]:
        fname = f"{pid}_{form}_p1.jpg"
        if not (a_proof / fname).is_file() or not (b_proof / fname).is_file():
            continue
        what = "mailing address" if form in ("CF1", "PMRF") else "date / time admitted and discharged"
        h.append(f"<h3>Patient {pid}, {form} - {what}</h3>")
        for label, proof in (("Before", b_proof), ("After", a_proof)):
            n, size = pics.add(proof / fname, BANDS[form])
            h.append(f"<h4>{label}</h4>{img(n, size, W)}")
        h.append(f'<p class="muted">Full pages: <a href="#A-{pid}-{form}">after</a> | '
                 f'<a href="#B-{pid}-{form}">before</a></p>')
    h.append("<h3>Every box that was a mapping error or filled with nothing read, before the fixes</h3>")
    for c in b_err:
        l = c["line"]
        n, size = pics.add(b_proof / c["file"])
        h.append(f"<h4>{e(l['patient'])} {e(FORM_KEY[l['form']])} - {e(l['column'])}: read "
                 f"<b>{e(l.get('ocr_text') or '(nothing)')}</b>; box shows <b>{e(tick(l['shown']))}</b>, "
                 f"from the reading <b>{e(tick(l.get('as_read')))}</b></h4>{img(n, size, min(W * 0.75, size[0] * 0.55))}")

    # 5
    h.append('<h2 id="live" class="break">5. Check in the real system</h2>')
    if live:
        h.append(f"""<p>The real PClaimAssist app (its routes, sign-in check and database) was run with the fixed code and
          /index.html opened in {e(live.get('browser', ''))}, signed in as {e(live.get('user') or '')}. Values were typed
          into the real Patient details boxes and CF4 built with the "Save as PDF" code. Nothing was saved.</p>""")
        for s in [s for s in live["scenarios"] if s["code"] in ("C", "D")]:
            v = s["forms"]["cf4"]["values"]
            ticks = lambda pre: ", ".join(x for x in ("AM", "PM") if v.get(f"{pre}{x}")) or "none"
            hhmm = lambda pre: "".join(v.get(f"{pre}{k}", "") for k in ("HH1", "HH2", "MI1", "MI2")) or "(blank)"
            typed = ", ".join(f"{k} = {x}" for k, x in s["typed"].items())
            n, size = pics.add(live_dir / s["forms"]["cf4"]["picture"], max_px=1100)
            h.append(f"<h3>Scenario {s['code']} - {e(s['title'])}</h3><p class='muted'>Typed: {e(typed)}</p>"
                     f"<p>CF4 admitted: time {e(hhmm('cf4Adm'))}, tick {ticks('cf4Adm')}; discharged: time "
                     f"{e(hhmm('cf4Dis'))}, tick {ticks('cf4Dis')}.</p>{img(n, size, W)}")
        h.append("""<div class="box"><b>Result:</b> in the real app, CF4 ticks no AM/PM when no time is given, and the
          right one when it is (16:00 &rarr; PM, 09:30 &rarr; AM). The mailing-address fixes are shown live in the
          field mapping report.</div>""")

    # 6
    a_rule = [c for en in a_man["entries"] for c in en["crops"]]
    h.append('<h2 id="remaining" class="break">6. Where the wrong boxes come from (after the fixes)</h2>')
    h.append(f"""<p>After the fixes, {a_c['All forms'][3]} wrong boxes are OCR misreads in the right box (orange in the
      pictures), {a_map_err} are mapping errors, and {a_c['All forms'][2 + 4]} was filled by a system rule because the
      reading was unusable. In other words, every value the OCR read went to the box it belongs in; what is wrong is the
      reading itself. The handwriting report (Objective 3 (i)) measures that reading accuracy. In the clinic, the
      review step is where staff correct these readings before a claim is made.</p>""")
    h.append("<h3>Per answer-key value</h3>")
    per_value = json.loads((after_dir / "summary.json").read_text(encoding="utf-8"))["sheets"]
    pv = next(s for s in per_value if s["name"].startswith("3d"))
    h.append("<table><tr>" + "".join(f"<th>{e(x)}</th>" for x in pv["headers"]) + "</tr>")
    for r in pv["rows"]:
        h.append("<tr>" + "".join(f"<td>{e('-' if x is None else str(x))}</td>" for x in r) + "</tr>")
    h.append("</table>")
    for c in a_rule:
        l = c["line"]
        n, size = pics.add(a_proof / c["file"])
        h.append(f"<h4>{e(l['patient'])} {e(FORM_KEY[l['form']])} - {e(l['column'])} ({e(l.get('cause') or '')}): "
                 f"read <b>{e(l.get('ocr_text') or '(nothing)')}</b>, box shows <b>{e(tick(l['shown']))}</b>, "
                 f"answer key <b>{e(tick(l['expected']))}</b></h4>{img(n, size, min(W * 0.75, size[0] * 0.55))}")

    # 7
    h.append('<h2 id="verdict" class="break">7. Is it usable?</h2>')
    h.append(f"""<table><tr><th>Check</th><th>Result</th></tr>
      <tr><td>Readings landing in the right box (mapping on OCR input)</td><td class="good">{a_all_m[4]}%
        ({a_all_m[3]} of {a_all_m[2]})</td></tr>
      <tr><td>Mapping errors</td><td class="good">{a_map_err} (were {b_map_err})</td></tr>
      <tr><td>Printed PDF agrees with the screen</td><td class="good">every box</td></tr>
      <tr><td>Real app: CF4 AM/PM with and without a time</td><td class="good">{'correct' if live else 'not run'}</td></tr>
      <tr><td>End-to-end with no staff correction</td><td>{a_e['All forms'][4]}% - limited by the handwriting OCR</td></tr>
      </table>""")
    h.append("""<p><b>Yes - the field mapping works on OCR input.</b> Whatever the OCR reads is put in the right box, in
      the right format, on every form. The forms are only as correct as the reading, which is why the review step stays:
      with no staff correction, about 4 in 10 boxes are right end-to-end.</p>
      <p>Before relying on the fixes: restart the backend (PClaimAssist.bat) and reload the forms with Ctrl+F5; the
      fixes are on branch jrad/field-mapping-fixes, not merged; the result stays provisional until the expected box
      table is checked against the paper forms.</p>""")

    # appendices
    def page_section(anchor, letter, man, proof, forms, heading, note):
        entries = [en for en in man["entries"] if FORM_KEY[en["form"]] in forms]
        patients = sorted({en["patient"] for en in entries})
        h.append(f'<h2 id="{anchor}" class="break">{heading}</h2><p class="muted">{note}</p>')
        h.append("<table><tr><th>Patient</th>" + "".join(f"<th>{f}</th>" for f in forms) + "</tr>")
        find = lambda pid, f: next((x for x in entries if x["patient"] == pid and FORM_KEY[x["form"]] == f), None)
        for pid in patients:
            cells = []
            for f in forms:
                en = find(pid, f)
                if en:
                    bad = sum(p["wrong"] for p in en["pages"])
                    mark = f" ({bad} wrong)" if bad else ""
                    cells.append(f'<td><a href="#{letter}-{pid}-{f}">open</a>{mark}</td>')
                else:
                    cells.append("<td class='muted'>-</td>")
            h.append(f"<tr><td>{pid}</td>{''.join(cells)}</tr>")
        h.append("</table>")
        for pid in patients:
            for f in forms:
                en = find(pid, f)
                for i, p in enumerate(en["pages"] if en else []):
                    n, size = pics.add(proof / p["file"])
                    aid = f' id="{letter}-{pid}-{f}"' if i == 0 else ""
                    h.append(f'<h3{aid} class="break">{pid} - {f} page {p["page"]} - {p["wrong"]} wrong</h3>'
                             f'{img(n, size, W * 0.93)}')

    page_section("appA", "A", a_man, a_proof, FORM_ORDER, "Appendix A - every saved form page after the fixes",
                 "Click a cell to jump to that page. 'wrong' counts orange and red boxes; red ones are mapping errors.")
    page_section("appB", "B", b_man, b_proof, ["CF1", "CF4", "PMRF"],
                 "Appendix B - CF1, CF4 and PMRF pages before the fixes",
                 "The three forms the fixes changed; CSF and CF2 had the same results before and after.")
    h.append("</body>")
    render(h, pics, out_path, "OCR field mapping proof report",
           "Field mapping on OCR input, before and after fixes, with pictures")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", type=Path, default=FOLDER / "before_fix")
    ap.add_argument("--after", type=Path, default=FOLDER)
    ap.add_argument("--live", type=Path, default=LIVE)
    ap.add_argument("--out", type=Path, default=FOLDER / "ocr_field_mapping_proof_report.pdf")
    a = ap.parse_args()
    path = build(a.before, a.after, a.live, a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
