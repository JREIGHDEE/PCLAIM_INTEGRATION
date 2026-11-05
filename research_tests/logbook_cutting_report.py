"""Logbook cutting proof report: how accurately the Logbook Reader cuts each
logbook row into its categories, with the pictures of every cut, in one
PDF with bookmarks and links (same layout as field_mapping_report.py).

    python -m research_tests.logbook_cutting_report

Reads outputs/logbook_cutting/ (run research_tests.logbook_cutting first)
and writes outputs/logbook_cutting/logbook_cutting_proof_report.pdf.
"""
import argparse
import datetime
import json
from pathlib import Path

from research_tests import OUTPUTS
from research_tests.field_mapping_report import CSS, Pictures, e, img, render

FOLDER = OUTPUTS / "logbook_cutting"
EXTRA_CSS = ".clip { color: #e07800; font-weight: bold; } .small td, .small th { font-size: 8pt; padding: 1pt 4pt; }"


def table(h, headers, rows, cls="small"):
    h.append(f"<table class='{cls}'><tr>" + "".join(f"<th>{e(str(x))}</th>" for x in headers) + "</tr>")
    for r in rows:
        bold = str(r[1]).startswith("All")
        cells = "".join(f"<td>{'<b>' if bold else ''}{e('-' if x is None else str(x))}{'</b>' if bold else ''}</td>"
                        for x in r)
        h.append(f"<tr>{cells}</tr>")
    h.append("</table>")


def build(folder, out_path):
    m = json.loads((folder / "proof" / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    proof = folder / "proof"
    pics = Pictures()
    W = 523
    vw = {(r[0], r[1]): r for r in m["v_writer"]}
    sc, ph = vw[("scanner", "All writers")], vw[("phone", "All writers")]
    vh = m["v_headers"]

    def mosaic(method, writer, page, width=W):
        n, size = pics.add(proof / f"mosaic_{method}_{writer}_p{page}.jpg")
        return img(n, size, min(width, size[0] * 0.75))

    hum = m.get("human") or {}
    h = [f"<style>{CSS}{EXTRA_CSS}</style><body>"]
    h.append('<h1 id="top">Logbook cutting test - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests - how accurately the Logbook Reader cuts each logbook row '
             f'into its categories - generated {datetime.date.today().isoformat()}</p>')
    if hum:
        hw = {(r[0], r[1]): r for r in hum["4-You per writer"]["rows"]}
        parts = []
        for scan in ("scanner", "phone"):
            r = hw.get((scan, "All writers"))     # [scan, label, cuts, tagged, correct, partly, not at all, untagged, %, %]
            if not r:
                continue
            if not r[3]:
                parts.append(f"<b>{scan}</b>: not tagged yet")
            else:
                parts.append(f"<b>{scan}</b>: {r[3]} of {r[2]} cuts tagged - {r[8]}% correct, {r[9]}% correct or "
                             f"partly" + (f" ({r[7]} not tagged yet)" if r[7] else ""))
        h.append(f"""<div class="box"><b>Your check.</b> Cuts tagged by a person on the review page
          (research_tests.logbook_cutting_review): {'; '.join(parts)}. Section <a href="#yours">Your check</a> has the
          details; the rest of this report shows the earlier visual check and the pictures.</div>""")
    h.append(f"""<div class="box"><b>{'Earlier visual check (by Claude, before your check).' if hum else 'Result.'}</b> <b>Proper cuts</b> (one whole entry, its own column, nothing missing):
      <b>{sc[-4]}%</b> of the {sc[2]} cuts on the <b>scanner</b> scans ({sc[-3]}% counting cuts of the right column that
      clip part of the writing) and <b>{ph[-4]}%</b> on the <b>phone</b> photos ({ph[-3]}% with clipped).
      Row numbering is a separate problem: on the scanner every cut got the right row number; on the phone only
      {ph[-2]}% did - several phone pages are cut properly but numbered one to three rows off, which pairs one patient's
      details with another's diagnoses. Proper <i>and</i> on the right row: {sc[-1]}% scanner, {ph[-1]}% phone.
      <br/>The left page is cut well on the scanner except the Case number, which often loses its first digit; on the
      right page the grid was placed one step too far right for 4 of the 10 writers (Reason for admission holds the
      delivery date).</div>""")
    h.append("""<div class="warn"><b>How this was judged.</b> Every cut was looked at, in the page mosaics in this report,
      and judged by Claude (inputs/logbook_cutting_visual_check.csv) - the earlier check, used as the suggestion on the
      review page, where a person confirms or changes each cut. The judgement is a checkable input: please
      confirm it against the pictures, correct the CSV where needed, and rerun.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in ([("yours", "Your check (tagged on the review page)")] if hum else []) + [
                          ("glance", "1. Result at a glance"), ("method", "2. How the test works and how to read the pictures"),
                          ("findings", "3. What goes wrong, with pictures"), ("auto", "4. Automatic judging vs the visual check"),
                          ("verdict", "5. Is it usable?"),
                          ("appA", "Appendix A - every page, scanner (mosaics)"),
                          ("appB", "Appendix B - every page, phone (mosaics)"),
                          ("appC", "Appendix C - every row, scanner (each cut with what is written and read)")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents. "
             "The phone row pictures are in outputs/logbook_cutting/proof/ (phone_W*_row*.jpg).</p>")

    if hum:
        h.append('<h2 id="yours" class="break">Your check (tagged on the review page)</h2>')
        h.append("<p>Each cut tagged Correct (its own column's writing, whole), Partly (part of it, or with some of "
                 "another column) or Not at all. Percentages are of the cuts tagged.</p>")
        for name, title in (("4-You per writer", "Per writer"), ("4-You per category", "Per category"),
                            ("4-You vs earlier check", "Your tags against the earlier visual check")):
            sh = hum[name]
            h.append(f"<h3>{title}</h3>")
            table(h, sh["headers"], sh["rows"])
        ch = hum["4-You partly or not"]
        h.append(f"<h3>Cuts you tagged Partly or Not at all ({len(ch['rows'])})</h3>")
        if ch["rows"]:
            table(h, ch["headers"], ch["rows"][:400])
            if len(ch["rows"]) > 400:
                h.append(f"<p class='muted'>The first 400 of {len(ch['rows'])}; all are in the workbook "
                         "(sheet 4-You partly or not).</p>")
        h.append("<p class='muted'>The mosaics and row pictures in the appendices are framed by your tags "
                 "(green correct, orange partly, red not at all).</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    h.append("<h3>Per writer</h3>")
    table(h, ["Scan", "Writer"] + vh, m["v_writer"])
    h.append("<h3>Per category</h3>")
    table(h, ["Scan", "Category"] + vh, m["v_field"])
    h.append("<p class='muted'>Proper cuts % = proper / all cuts x 100 - how well the cutting works. 'Proper or "
             "clipped' also counts cuts of the right column that lose part of the writing (e.g. the first digit of the "
             "case number). Right row number % = cuts numbered as the right logbook row / cuts holding an entry. "
             "Proper and right row % = both.</p>")

    # 2
    h.append('<h2 id="method" class="break">2. How the test works and how to read the pictures</h2>')
    h.append("""<p>The Logbook Reader finds each patient's row on the scanned spread and cuts it into one picture per category:
      Case number, Admitted, Patient name, Birthday and Address on the left page; Reason for admission, Delivered, Final
      diagnosis and Went home on the right. This test checks those cuts - the field mapping of the logbook - on the
      handwriting test's runs (the same 10 writers, scanner and phone, the same pictures; nothing is re-read).</p>
      <p><b>Visual check (the result).</b> Each cut gets two judgements. First, <b>the cut itself</b>:</p>
      <table><tr><th>Cut</th><th>Meaning</th></tr>
      <tr><td class="good">Proper</td><td>one whole entry, its own column, nothing missing</td></tr>
      <tr><td class="clip">Clipped</td><td>its own column, but part of the writing is outside the cut</td></tr>
      <tr><td class="bad">Wrong column</td><td>holds (part of) another column's writing</td></tr>
      <tr><td class="bad">Half of two entries</td><td>the bottom of one entry and the top of the next</td></tr>
      <tr><td class="bad">Empty paper</td><td>below the last entry - nothing to cut</td></tr>
      <tr><td class="bad">Not found</td><td>no cut was made for that row</td></tr></table>
      <p>Second, <b>the row number</b> the system gave it: <i>Right</i>, or <i>Off by N</i> - a proper cut of another
      row's entry. The left and right pages are joined by row number, so a page numbered one row off pairs every patient's
      details with the next patient's diagnoses, even though each cut is proper.</p>
      <p><b>The pictures.</b> A <i>page mosaic</i> shows every cut of one page: a column per category, a row per logbook
      entry, framed green (proper), <span style="color:#783cbe"><b>purple</b></span> (proper, but numbered as another
      row), <span class="clip">orange</span> (clipped) or <span class="bad">red</span> (wrong column, half of two entries,
      empty paper, not found). A shifted column or a row off by one shows at a glance. A <i>row sheet</i> shows one row as the system found it on the scan, then each of its cuts with what is
      written in the logbook (answer key), what PaddleOCR read in it, the visual verdict and the automatic one.</p>
      <p><b>Automatic judging (support).</b> PaddleOCR's raw reading of each cut is compared with what is written in
      every category of the same page, in the same row and the rows above and below; a cut is "wrong" when another
      category or row clearly matches better. Section 4 shows where it agrees with the visual check.</p>""")

    # 3
    h.append('<h2 id="findings" class="break">3. What goes wrong, with pictures</h2>')
    h.append("""<h3>3.1 Right page: the grid placed one step too far right (scanner: W05, W08, W09, W10)</h3>
      <p>On these pages the cut for <i>Reason for admission</i> holds the end of the reason and the delivery date and
      time; <i>Delivered</i> holds the start of the final diagnosis; <i>Final diagnosis</i> loses its first letters. It
      happens on every row of the page. Below: W10 (shifted) and W01 (correct) for comparison.</p>""")
    h.append("<h4>W10, scanner, right page - shifted</h4>" + mosaic("scanner", "W10", 2))
    h.append("<h4>W01, scanner, right page - correct</h4>" + mosaic("scanner", "W01", 2))
    h.append("""<p><b>It is the grid, not the writer.</b> W05's same handwritten page is cut correctly from the phone photo
      but shifted on the scanner scan (and W07 the other way round). So the column positions the system places on the
      right page are not reliable from scan to scan.</p>""")
    h.append("<h4>W05, scanner, right page - shifted</h4>" + mosaic("scanner", "W05", 2))
    h.append("<h4>W05, phone, right page - the same page, correct</h4>" + mosaic("phone", "W05", 2))
    h.append("""<h3>3.2 Left page: the Case number loses its first digit</h3>
      <p>The case number is written at the very left of the page. Its cut often starts a little too far right, so the
      first digit (W05, W06, W09) or half the number (W07) is outside it. W02's whole left page is placed slightly too far
      left, which clips the first character of Case number, Admitted and Patient name instead.</p>""")
    h.append("<h4>W07, scanner, left page</h4>" + mosaic("scanner", "W07", 1))
    h.append("<h4>W02, scanner, left page</h4>" + mosaic("scanner", "W02", 1))
    h.append("""<h3>3.3 Phone photos: proper cuts, but rows numbered off</h3>
      <p>On many phone pages the cutting itself works: each cut holds one whole entry in its own column (W03, W04, W06,
      W08, W09 and W10 left pages, most right pages, and all of W05). What goes wrong is the row <i>numbering</i>: the left
      page is numbered one to three rows off from the right page (purple), and the empty paper below the last entry is
      cut as rows. Two phone left pages are cut badly - every cut half an entry off, holding the bottom of one patient and
      the top of the next (W01, W02) - and some rows are not found at all (W01, W06).</p>""")
    h.append("<h4>W10, phone, left page - every cut proper, numbered one row off (purple)</h4>" + mosaic("phone", "W10", 1))
    h.append("<h4>W05, phone, left page - proper and on the right rows</h4>" + mosaic("phone", "W05", 1))
    h.append("<h4>W01, phone, left page - half of two entries in every cut, rows 7-11 not found</h4>"
             + mosaic("phone", "W01", 1))

    # 4
    h.append('<h2 id="auto" class="break">4. Automatic judging vs the visual check</h2>')
    h.append("""<p>What the automatic judging said for the cuts in each visual verdict. It never called a correct cut
      wrong, but it misses most wrong-column cuts: with a poor reading, a cut holding part of two columns matches neither
      clearly, so it says "can't tell". That is why the result is the visual check.</p>""")
    agree_headers = ["Scan", "Visual verdict", "Cuts"] + m["verdicts"]
    table(h, agree_headers, m["agree"])
    auto = next(s for s in summary["sheets"] if s["name"].startswith("4d"))
    h.append("<h3>Automatic judging per writer</h3>")
    table(h, auto["headers"], auto["rows"])

    # 5
    h.append('<h2 id="verdict" class="break">5. Is it usable?</h2>')
    h.append(f"""<table><tr><th>Part</th><th>Result</th></tr>
      <tr><td>Scanner, left page: Admitted, Patient name, Birthday, Address</td><td class="good">correct, except W02's
        first characters (clipped)</td></tr>
      <tr><td>Scanner, left page: Case number</td><td class="clip">60% whole; the rest lose the first digit(s)</td></tr>
      <tr><td>Scanner, right page: Went home</td><td class="good">100% correct</td></tr>
      <tr><td>Scanner, right page: Reason, Delivered, Final diagnosis</td><td class="bad">60% correct - shifted for
        4 of 10 writers</td></tr>
      <tr><td>Phone photos: the cutting</td><td class="clip">{ph[-4]}% proper ({ph[-3]}% with clipped)</td></tr>
      <tr><td>Phone photos: row numbering</td><td class="bad">{ph[-2]}% right - left page often one to three rows off
        </td></tr></table>""")
    h.append(f"""<p><b>Scanner: usable with the review step, not on its own.</b> {sc[-4]}% of cuts are proper and
      {sc[-3]}% hold the right column, all on the right rows. The review page shows staff each cut, so a clipped digit or a
      shifted right page is visible and can be fixed there - but on a shifted page, three of the nine fields need retyping
      for every patient. <b>Phone photos: the cutting partly works ({ph[-4]}% proper), the row numbering does not</b>
      (only {ph[-1]}% proper and on the right row): a page numbered one row off silently pairs one patient's details with
      another's diagnoses, so phone photos are not safe to use as they are.</p>
      <p><b>What would fix most of it</b> (for the team to decide): place the right-page columns from the printed
      column lines of each scan rather than from fixed positions; start the Case number cut a little further left; for
      phone photos, find the rows from the printed lines after straightening the photo, and refuse a photo whose rows
      do not line up between the two pages.</p>""")

    # appendices
    for anchor, letter, method, title in (("appA", "A", "scanner", "Appendix A - every page, scanner (mosaics)"),
                                          ("appB", "B", "phone", "Appendix B - every page, phone (mosaics)")):
        h.append(f'<h2 id="{anchor}" class="break">{title}</h2>')
        writers = sorted({x["writer"] for x in m["mosaics"] if x["method"] == method})
        h.append("<table><tr><th>Writer</th><th>Left page</th><th>Right page</th></tr>")
        for w in writers:
            r = vw[(method, next(k[1] for k in vw if k[0] == method and k[1].startswith(w)))]
            h.append(f'<tr><td>{w} - {r[-4]}% proper, {r[-2]}% right row</td><td><a href="#{letter}-{w}-left">open</a></td>'
                     f'<td><a href="#{letter}-{w}-right">open</a></td></tr>')
        h.append("</table>")
        for w in writers:
            for page, side in ((1, "left"), (2, "right")):
                h.append(f'<h3 id="{letter}-{w}-{side}" class="break">{w} - {method} - {side} page</h3>'
                         + mosaic(method, w, page, W))
    h.append('<h2 id="appC" class="break">Appendix C - every row, scanner (each cut with what is written and read)</h2>')
    rows = [x for x in m["sheets"] if x["method"] == "scanner"]
    writers = sorted({x["writer"] for x in rows})
    h.append("<table class='small'><tr><th>Writer</th><th>Rows (red = a cut that is not proper or not on its row)</th></tr>")
    for w in writers:
        links = " ".join(f'<a href="#C-{w}-r{x["row"]:02d}">{"<span class=bad>" if x["wrong"] else ""}{x["row"]}'
                         f'{"</span>" if x["wrong"] else ""}</a>' for x in rows if x["writer"] == w)
        h.append(f"<tr><td>{w}</td><td>{links}</td></tr>")
    h.append("</table>")
    for x in rows:
        n, size = pics.add(proof / x["file"])
        h.append(f'<h3 id="C-{x["writer"]}-r{x["row"]:02d}" class="break">{x["writer"]} - row {x["row"]} - '
                 f'{x["wrong"]} of 9 cuts not proper or not on their row</h3>{img(n, size, W)}')
    h.append("</body>")
    render(h, pics, out_path, "Logbook cutting proof report", "Logbook cutting accuracy per category, with pictures")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--folder", type=Path, default=FOLDER)
    ap.add_argument("--out", type=Path, default=FOLDER / "logbook_cutting_proof_report.pdf")
    a = ap.parse_args()
    path = build(a.folder, a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
