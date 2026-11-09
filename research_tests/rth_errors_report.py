"""RTH mistakes proof report: the results of test 8 (the clinic's common
return-to-hospital mistakes planted on the real forms page) in one PDF with
bookmarks and links (same layout as the other proof reports).

    python -m research_tests.rth_errors_report

Reads outputs/rth_errors/ (run research_tests.rth_errors first) and writes
outputs/rth_errors/rth_errors_proof_report.pdf.
"""
import argparse
import datetime
import json
from pathlib import Path

from research_tests import OUTPUTS
from research_tests.common import excel
from research_tests.field_mapping_report import CSS, Pictures, e, img, render
from research_tests.logbook_cutting_report import EXTRA_CSS, table

FOLDER = OUTPUTS / "rth_errors"
OUTCOME_CLASS = {"Prevented": "good", "Blocked": "good", "Warned": "clip", "Gets through": "bad"}


def _pct(v):
    return "-" if v in (None, "") else f"{float(v):.1f}%"


def build(out_path):
    summary = json.loads((FOLDER / "summary.json").read_text(encoding="utf-8"))
    sheet = {s["name"]: s for s in summary["sheets"]}
    raw = [r for r in excel.read_rows(FOLDER / "rth_errors_results.xlsx", "Raw data") if r.get("ID")]
    proof = FOLDER / "proof"
    pics = Pictures()
    W = 523

    red = sheet["8a RTH error reduction"]
    rows = red["rows"]
    total = next(r for r in rows if str(r[0]).startswith("All planted"))
    weighted = next(r for r in rows if str(r[0]).startswith("Weighted"))
    reasons = [r for r in rows if r not in (total, weighted)]
    per = sheet["8b Per mistake"]["rows"]
    listed = sheet["8c Not counted"]["rows"]
    n, prevented, blocked, warned, through = total[4], total[6], total[7], total[8], total[9]

    h = [f"<style>{CSS}{EXTRA_CSS} .clip {{ color: #b45309; font-weight: bold; }}</style><body>"]
    h.append('<h1 id="top">RTH mistakes - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, test 8, supplementary to Eq. 3.12 (documentation error '
             f'reduction) - results of {e(summary.get("generated_at", ""))}, report generated '
             f'{datetime.date.today().isoformat()}</p>')
    h.append(f"""<div class="box"><b>Result.</b> The clinic's common return-to-hospital mistakes were planted
      <b>{n}</b> times on the real forms page. PClaimAssist <b>prevented {prevented}</b>, <b>blocked {blocked}</b>
      (Save as PDF refuses), <b>warned on {warned}</b>, and <b>let {through} through</b>.
      Error reduction against manual typing: <b>{_pct(total[11])}</b> counting a warning as an error left,
      <b>{_pct(total[13])}</b> counting a warning as caught. Weighted by how common the clinic says each reason is:
      <b>{_pct(weighted[11])}</b> and <b>{_pct(weighted[13])}</b>.</div>""")
    h.append("""<div class="warn"><b>Read with care.</b> Manual = each form typed separately with nothing checking it,
      so every planted mistake stays in the claim: that is the assumption of the comparison, not a measurement of
      staff. The result shows whether the system stops a mistake once it is made, not how often staff make
      mistakes; Eq. 3.12 proper comes from the user sessions. The weights are the clinic's estimate, not counted
      from returned claims.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("reasons", "2. Per RTH reason"),
                          ("mistakes", "3. Per mistake"), ("through", "4. What still gets through"),
                          ("proof", "5. Proof: the page's own rule panel"),
                          ("notcounted", "6. Listed but not counted"), ("verdict", "7. What this means")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents.</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    table(h, ["Outcome", "Planted mistakes", "Share", "What it means"], [
        ["Prevented", prevented, _pct(100 * prevented / n), "The second copy cannot differ: locked box filled from "
                                                             "Patient details, or one value for every form"],
        ["Blocked", blocked, _pct(100 * blocked / n), "A critical rule fires: Save as PDF refuses"],
        ["Warned", warned, _pct(100 * warned / n), "A warning fires: staff are told, the PDF can still be saved"],
        ["Gets through", through, _pct(100 * through / n), "In the claim, and nothing notices"],
        ["All planted mistakes", n, "100.0%", ""]])
    table(h, ["Error reduction", "Warning = error left (strict)", "Warning = caught"], [
        ["All planted mistakes (each counts once)", _pct(total[11]), _pct(total[13])],
        ["Weighted by how common each reason is", _pct(weighted[11]), _pct(weighted[13])]])
    h.append("<p class='muted'>Error reduction % = (manual errors - PClaimAssist errors) / manual errors x 100, "
             "the form of Eq. 3.12. Weights: very common 4, common 3, slightly uncommon 2, uncommon 1.</p>")

    # 2
    h.append('<h2 id="reasons" class="break">2. Per RTH reason</h2>')
    table(h, ["RTH reason", "How common", "Planted", "Prevented", "Blocked", "Warned", "Gets through",
              "Reduction (strict)", "Reduction (warning = caught)"],
          [[r[0], r[1], r[4], r[6], r[7], r[8], r[9], _pct(r[11]), _pct(r[13])] for r in reasons]
          + [["All planted mistakes", "", n, prevented, blocked, warned, through, _pct(total[11]), _pct(total[13])]])

    # 3
    h.append('<h2 id="mistakes" class="break">3. Per mistake</h2>')
    h.append("<p>Each mistake was planted in every test patient it applies to. <i>Rules</i> are the rules that "
             "fired; <i>How</i> is what the page did.</p>")
    h.append("<table class='small'><tr><th>ID</th><th>Mistake</th><th>How it happens</th><th>Planted</th>"
             "<th>Outcome</th><th>Rules</th><th>How</th></tr>")
    for r in per:
        outs = [(o, c) for o, c in zip(["Prevented", "Blocked", "Warned", "Gets through"], r[5:9]) if c]
        out = ", ".join(f"<span class='{OUTCOME_CLASS[o]}'>{o} {c}</span>" for o, c in outs)
        h.append(f"<tr><td>{e(r[0])}</td><td>{e(r[3])}</td><td>{e(r[2])}</td><td>{r[4]}</td><td>{out}</td>"
                 f"<td>{e(r[10])}</td><td>{e(str(r[11])[:160])}</td></tr>")
    h.append("</table>")

    # 4
    h.append('<h2 id="through" class="break">4. What still gets through</h2>')
    left = [r for r in per if r[8]]
    if not left:
        h.append("<p>Nothing: every planted mistake was prevented, blocked or warned.</p>")
    else:
        h.append("<p>These mistakes are in the claim and no check notices them. They are limits of the system.</p>")
        why = {"D4": "A swapped day and month is still a real date; nothing else on the forms says which is right.",
               "N5": "The forms agree with each other; only the patient's ID shows the right spelling."}
        table(h, ["ID", "Mistake", "Planted", "Gets through", "Why"],
              [[r[0], r[3], r[4], r[8], why.get(r[0], "")] for r in left])

    # 5
    h.append('<h2 id="proof" class="break">5. Proof: the page\'s own rule panel</h2>')
    h.append("<p>For each mistake that was not prevented, the page's own \"Rule Check Results\" panel after the "
             "mistake was made, on the first patient it was planted in (every picture is in outputs/rth_errors/proof/). "
             "Prevented mistakes have no panel: the box could not be typed differently (see section 3).</p>")
    seen = set()
    for c in raw:
        if c["ID"] in seen or not c.get("Panel picture"):
            continue
        seen.add(c["ID"])
        f = proof / c["Panel picture"]
        h.append(f'<h3>{e(c["ID"])} on {e(c["Patient"])} - {e(c["Mistake"])}: '
                 f'<span class="{OUTCOME_CLASS.get(c["Outcome"], "")}">{e(c["Outcome"])}</span>'
                 f'{" (" + e(c["New rules fired"]) + ")" if c.get("New rules fired") else ""}</h3>')
        h.append(f"<p class='small'>{e(str(c.get('What was typed') or '')[:300])}</p>")
        if f.is_file():
            pn, size = pics.add(f, max_px=900)
            h.append(img(pn, size, min(W, size[0] * 0.6)))

    # 6
    h.append('<h2 id="notcounted" class="break">6. Listed but not counted</h2>')
    table(h, ["ID", "RTH reason", "Mistake", "Why not counted", "Detail"], listed)

    # 7
    h.append('<h2 id="verdict" class="break">7. What this means</h2>')
    h.append(f"""<p><b>Typing a value once stops the dual-entry mistakes.</b> Names, PIN, dates and the admission
      diagnosis are typed once on Patient details and locked on every form, so a second copy cannot differ; the
      case rate codes and the attending midwife copy to every form. Impossible values (an 11-digit PIN, a discharge
      before the admission, a delivery outside the stay, a cesarean on CF4 against a normal delivery on CF2) block
      Save as PDF. The OB score, the course in the ward, the LMP and a baby's claim against its mother's are
      warned on.</p>
      <p>Of {n} planted mistakes, {prevented + blocked} were stopped and {warned} warned on; {through} got through:
      a value that is wrong the same way everywhere (a misspelled name, a swapped day and month). Those need the
      patient's ID or record to catch, which the forms do not have.</p>""")
    h.append("</body>")
    render(h, pics, out_path, "RTH mistakes proof report", "Planted RTH mistakes and the page's own rule panel")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=FOLDER / "rth_errors_proof_report.pdf")
    a = ap.parse_args()
    path = build(a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
