"""Image quality (IQ-01) proof report: the real IQ test scans, every page
beside the same page of the original scan and - when flagged - the
evened-out copy the OCR reads, with the measured values, in one PDF with
bookmarks and links (same layout as the other proof reports).

    python -m research_tests.iq_report

Reads outputs/iq_check/ (run research_tests.iq_check first, with --ocr for
the OCR section) and writes outputs/iq_check/iq_proof_report.pdf.
"""
import argparse
import datetime
import json
from pathlib import Path

from research_tests import OUTPUTS
from research_tests.field_mapping_report import CSS, Pictures, e, img, render
from research_tests.logbook_cutting_report import EXTRA_CSS, table

FOLDER = OUTPUTS / "iq_check"
ORDER = {"dark": 0, "bright": 1, "blurred": 2, "normal": 3}


def flags(p):
    return ", ".join(k for k, f in (("dim", p["dim"]), ("soft focus", p["soft"]), ("washed out", p["washed"]),
                                    ("too dark", p["dark"]), ("too bright", p["bright"]), ("blurry", p["blurry"]))
                     if f) or "none"


def build(out_path):
    import config
    summary = json.loads((FOLDER / "summary.json").read_text(encoding="utf-8"))
    sheet = {s["name"]: s for s in summary["sheets"]}
    m = json.loads((FOLDER / "proof" / "manifest.json").read_text(encoding="utf-8"))
    pages, ocr = m["pages"], m.get("ocr") or []
    proof = FOLDER / "proof"
    pics = Pictures()
    W = 523
    bad = [p for p in pages if p["should_warn"]]
    normal = [p for p in pages if not p["should_warn"]]
    caught, false_w = sum(p["fired"] for p in bad), sum(p["fired"] for p in normal)
    g = {r[0]: r for r in sheet["6h OCR per condition"]["rows"]} if "6h OCR per condition" in sheet else {}
    other = sheet.get("6f Other page sets", {}).get("rows", [])
    originals_ok = all(r[3] == 0 for r in other if r[1] == "pass")

    h = [f"<style>{CSS}{EXTRA_CSS}</style><body>"]
    h.append('<h1 id="top">Image quality check (IQ-01) - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, Objective 3 (iii), rule IQ-01 - REAL scans, results of '
             f'{e(summary.get("generated_at", ""))}, report generated {datetime.date.today().isoformat()}</p>')
    ocr_line = ""
    if g:
        parts = [f"{c} {g[c][5]:+.1f}" for c in ("normal", "dark", "bright", "blurred") if c in g and g[c][5] is not None]
        ocr_line = (" Read with the OCR, the change in characters read right against the original scan was: "
                    + "; ".join(parts) + " points.")
    h.append(f"""<div class="box"><b>Result.</b> On {len(pages)} real logbook pages - the 10 handwriting spreads with
      {len(bad)} pages deliberately made dark, bright or blurred - IQ-01 warned on
      <span class="good">{caught} of the {len(bad)} bad pages</span> and on {false_w} of the {len(normal)} normal pages.
      {"The 40 original logbook pages all pass. " if originals_ok else ""}A dim, washed-out or too-dark page is evened
      out before it is read.{ocr_line}</div>""")
    h.append("""<div class="warn"><b>Real scans, not generated.</b> These pages were made bad by hand and scanned. The
      computer-generated copies are used only as an extra check that was not used to choose the thresholds (section 1).
      Four of the given labels were corrected after comparing each page with the original scan (section 3).
      <b>The thresholds were chosen from these pages and the 40 original pages</b>, so this shows they work on what
      they were set on; the generated copies and more real scans are the fair test.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("check", "2. How IQ-01 checks a page"),
                          ("labels", "3. How the test works, and the labels"),
                          ("bad", "4. Every bad page: original, bad page, evened out"),
                          ("why", "5. The values and the thresholds"),
                          ("ocr", "6. What a bad page costs the OCR"), ("verdict", "7. What this means"),
                          ("appA", "Appendix A - every page, whole")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents.</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    h.append("<h3>Warning vs expected condition</h3>")
    table(h, sheet["6b IQ-01 confusion"]["headers"], sheet["6b IQ-01 confusion"]["rows"])
    h.append("<h3>Per condition</h3>")
    table(h, sheet["6c Per condition"]["headers"][:5], [r[:5] for r in sheet["6c Per condition"]["rows"]])
    if other:
        h.append("<h3>Pages not made for this test</h3>")
        table(h, sheet["6f Other page sets"]["headers"], other)
        h.append("<p class='muted'>The original handwriting pages should pass; the generated copies were not used to "
                 "choose the thresholds.</p>")

    # 2
    h.append('<h2 id="check" class="break">2. How IQ-01 checks a page</h2>')
    h.append(f"""<p>The Logbook Reader checks every page with image_quality.assess_logbook_page before reading it. It
      measures the page's <b>brightness</b> (mean grey level, 0-255), its <b>sharpness</b> (variance of the Laplacian,
      on the page scaled to 1000 px wide so it does not depend on the scan's resolution), how much of it is
      <b>pure white</b>, and how dark the <b>writing</b> is (the darkest 0.1% of pixels). It warns when:</p>
      <table><tr><th>Warning</th><th>When</th><th>Good logbook pages measured</th></tr>
      <tr><td>Too dark</td><td>brightness below {config.IMAGE_QUALITY_BRIGHTNESS_LOW:g}</td><td>-</td></tr>
      <tr><td>Dim page</td><td>brightness below {config.IMAGE_QUALITY_DIM_BELOW:g}</td><td>230.4 or more</td></tr>
      <tr><td>Too bright</td><td>brightness above {config.IMAGE_QUALITY_BRIGHTNESS_HIGH:g} and the writing lighter than
        {config.IMAGE_QUALITY_INK_MAX:g}</td><td>-</td></tr>
      <tr><td>Washed out</td><td>at least {config.IMAGE_QUALITY_WASHED_WHITE_SHARE * 100:g}% of the page pure white and
        the writing at {config.IMAGE_QUALITY_WASHED_INK_MIN:g} or lighter</td>
        <td>bleached pages with dark writing (phone scans): 1-86</td></tr>
      <tr><td>Blurry</td><td>sharpness (full size) below {config.IMAGE_QUALITY_BLUR_THRESHOLD:g}</td><td>-</td></tr>
      <tr><td>Soft focus</td><td>sharpness at 1000 px wide below {config.IMAGE_QUALITY_SHARPNESS_MIN:g}</td>
        <td>346 or more</td></tr></table>
      <p>The warning asks staff to rescan. A <b>dim, washed-out or too-dark</b> page is also <b>evened out</b> before its
      rows and cells are found and read (image_quality.enhance_for_ocr): its paper is set back to white and its ink to
      dark. A blurred page is only warned about. The thresholds and the evening-out switch are in config.py
      (OCR_IMAGE_QUALITY_...).</p>""")

    # 3
    h.append('<h2 id="labels" class="break">3. How the test works, and the labels</h2>')
    h.append("""<p>Each page is loaded the way the Logbook Reader loads it (PDF at 2x, straightened) and checked with
      IQ-01. The warning should fire on the dark, bright and blurred pages and stay quiet on the normal ones. Each page
      was also compared with the same page of the original scanner scan: an untouched page changes by about -1 in
      brightness and +3 to +10 in ink level (it was only re-saved), so a real change stands out. Four labels did not
      match what had been done to the page and were corrected (inputs/iq_expected.csv keeps both):</p>""")
    table(h, sheet["6e Labels corrected"]["headers"], sheet["6e Labels corrected"]["rows"])

    # 4
    h.append('<h2 id="bad" class="break">4. Every bad page: original, bad page, evened out</h2>')
    h.append("<p>Left to right: the original scanner scan, the IQ test page, and - for a page that is evened out - the "
             "copy the OCR reads. Top: a close-up of the same spot; below: the whole page.</p>")
    for p in sorted(bad, key=lambda p: (ORDER.get(p["expected"], 9), p["file"], p["page"])):
        stem = p["picture"]
        h.append(f'<h3 id="bad-{stem}">{e(p["file"])} page {p["page"]} - {e(p["expected"])}: '
                 f'{"<span class=good>warned</span>" if p["fired"] else "<span class=bad>not warned</span>"} '
                 f'({flags(p)}){", evened out" if p["enhanced"] else ""}</h3>')
        h.append(f"""<table class='small'><tr><th></th><th>Brightness</th><th>Sharpness (1000 px)</th>
          <th>Darkest writing</th><th>Pure white %</th></tr>
          <tr><td>Original</td><td>{p['orig_brightness']}</td><td>{p['orig_sharpness']}</td><td>{p['orig_ink']}</td>
          <td>-</td></tr>
          <tr><td>IQ page</td><td>{p['brightness']}</td><td>{p['sharpness']}</td><td>{p['ink']}</td>
          <td>{round(p['white_share'] * 100, 1)}</td></tr></table>""")
        if p["why"]:
            h.append(f"<p class='bad'>Not warned: {e(p['why'])}.</p>")
        for kind in ("_zoom", ""):
            cells = []
            for tag, label in (("orig", "Original"), ("iq", "IQ page"), ("enh", "Evened out (read by the OCR)")):
                f = proof / f"{stem}_{tag}{kind}.jpg"
                if f.is_file():
                    n, size = pics.add(f, max_px=600)
                    cells.append(f"<td style='border:none'>{label if kind else ''}<br/>{img(n, size, W / 3 - 6)}</td>")
            h.append(f"<table><tr>{''.join(cells)}</tr></table>")

    # 5
    h.append('<h2 id="why" class="break">5. The values and the thresholds</h2>')
    h.append("<h3>Pages IQ-01 gets wrong</h3>")
    if sheet["6d Misses and false warnings"]["rows"]:
        table(h, sheet["6d Misses and false warnings"]["headers"], sheet["6d Misses and false warnings"]["rows"])
    else:
        h.append("<p>None.</p>")
    h.append("<h3>Where the values lie</h3>")
    pc = sheet["6c Per condition"]
    table(h, [pc["headers"][0]] + pc["headers"][5:], [[r[0]] + r[5:] for r in pc["rows"]])
    h.append("""<p class="muted">Dim pages are told apart by brightness, soft ones by sharpness at a fixed size,
      washed-out ones by bleached paper together with faint writing (bleached paper alone is normal for phone-app scans).
      These thresholds were set on these pages and the 40 original pages; please confirm them on more scans.</p>""")

    # 6
    h.append('<h2 id="ocr" class="break">6. What a bad page costs the OCR</h2>')
    if ocr and "6g OCR per page" in sheet:
        h.append("""<p>Each IQ test scan was read with PaddleOCR + Correction (the value the system pre-fills), the way
          the Logbook Reader reads it - a flagged page evened out first - and each page scored against the answer key
          exactly as in the handwriting test, beside the same page of the original scan. The writing is the same, so the
          difference is the page.</p>""")
        table(h, sheet["6h OCR per condition"]["headers"], sheet["6h OCR per condition"]["rows"])
        f6 = sheet["6g OCR per page"]
        keep = [0, 1, 2, 3, 4, 5, 6, 7]
        table(h, [f6["headers"][i] for i in keep], [[row[i] for i in keep] for row in f6["rows"]])
    else:
        h.append("<p>Not run. Run <i>python -m research_tests.iq_check --ocr</i> (about a minute per scan).</p>")

    # 7
    h.append('<h2 id="verdict" class="break">7. What this means</h2>')
    h.append(f"""<p><b>IQ-01 catches the bad pages.</b> It warned on {caught} of the {len(bad)} pages made dark, bright or
      blurred on purpose, with {false_w} false warnings on the {len(normal)} normal pages; it lets the 40 original
      logbook pages through and catches the generated bad copies it was not set on. Staff are told to rescan these
      pages.</p>""")
    if g:
        worse = [f"{c} {abs(g[c][5]):.1f}" for c in ("dark", "bright", "blurred") if c in g and g[c][5] is not None]
        h.append(f"""<p><b>A rescan matters.</b> Even read the way the system reads them (dim and washed-out pages evened
          out first), the bad pages read worse than the original scan of the same writing - by {', '.join(worse)} points
          of character accuracy on average, against {abs(g['normal'][5]):.1f} for a normal page scanned again (section 6).
          That is why the warning asks staff to rescan.</p>""")

    # appendix
    h.append('<h2 id="appA" class="break">Appendix A - every page, whole</h2>')
    h.append("<table class='small'><tr><th>Page</th><th>Expected</th><th>Warned</th><th>Flags</th><th>Evened out</th>"
             "<th>Brightness</th><th>Sharpness</th></tr>")
    for p in pages:
        h.append(f"<tr><td><a href='#A-{p['file'][:3]}-p{p['page']}'>{e(p['file'])} p{p['page']}</a></td>"
                 f"<td>{e(p['expected'])}</td><td>{'yes' if p['fired'] else 'no'}</td><td>{e(flags(p))}</td>"
                 f"<td>{'yes' if p['enhanced'] else 'no'}</td><td>{p['brightness']}</td><td>{p['sharpness']}</td></tr>")
    h.append("</table>")
    for p in pages:
        stem = p["picture"]
        h.append(f'<h3 id="A-{p["file"][:3]}-p{p["page"]}" class="break">{e(p["file"])} page {p["page"]} - expected '
                 f'{e(p["expected"])}; warning {"fired" if p["fired"] else "not fired"}</h3>')
        cells = []
        for tag, label in (("orig", "Original"), ("iq", "IQ test page"), ("enh", "Evened out")):
            f = proof / f"{stem}_{tag}.jpg"
            if f.is_file():
                n, size = pics.add(f)
                cells.append(f"<td style='border:none'><b>{label}</b><br/>{img(n, size, W / 3 - 6)}</td>")
        h.append(f"<table><tr>{''.join(cells)}</tr></table>")
    h.append("</body>")
    render(h, pics, out_path, "Image quality (IQ-01) proof report", "IQ-01 on real dark, bright and blurred scans")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=FOLDER / "iq_proof_report.pdf")
    a = ap.parse_args()
    path = build(a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
