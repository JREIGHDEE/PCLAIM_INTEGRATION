"""OCR accuracy proof report: the handwriting test (Objective 3 (i)) with a
picture of every cell the OCR read, in one PDF with bookmarks and links
(same layout as the other proof reports).

    python -m research_tests.ocr_accuracy_report [--no-pictures]

Reads the handwriting test's results (outputs/handwriting/: summary.json,
handwriting_results.xlsx, runs.json, runs_phone.json) and the cell
pictures it read (outputs/work/uploads/review_crops/); nothing is re-read.
If the logbook cutting test has run, its visual check is used to give the
accuracy on properly cut cells too. Writes, in outputs/handwriting/:
  proof/<scan>_<writer>_row<NN>.jpg   every row: each cell with what is written
                                      and what each engine read
  ocr_accuracy_proof_report.pdf
"""
import argparse
import datetime
import json
from pathlib import Path

from research_tests import OUTPUTS
from research_tests.common import stats
from research_tests.field_mapping_report import CSS, Pictures, e, img, render
from research_tests.logbook_cutting import _font, _wrap
from research_tests.logbook_cutting_report import EXTRA_CSS, table

FOLDER = OUTPUTS / "handwriting"
CROPS = OUTPUTS / "work" / "uploads" / "review_crops"
RUNS = {"scanner": FOLDER / "runs.json", "phone": FOLDER / "runs_phone.json"}
CUTTING = OUTPUTS / "logbook_cutting" / "logbook_cutting_results.xlsx"
ENGINES = ["PaddleOCR", "PaddleOCR + Correction", "TesseractOCR", "TesseractOCR + Correction"]
SYSTEM = "PaddleOCR + Correction"            # what the Logbook Reader pre-fills for staff
GREEN, ORANGE, RED, GREY = (20, 150, 50), (235, 130, 0), (220, 0, 0), (140, 140, 140)
CLOSE = 80.0                                  # character accuracy counted as "close"
# The reading of each engine, as the handwriting test's Raw data names it.
OUTPUT_COLUMN = {"PaddleOCR": "PaddleOCR Output", "TesseractOCR": "TesseractOCR Output"}


def read_raw(path=None):
    """The handwriting test's Raw data - its approved copy when the working one is not there (read only)."""
    import openpyxl
    if path is None:
        path = next((p for p in (FOLDER / "handwriting_results.xlsx",
                                 OUTPUTS / "approved" / "handwriting" / "handwriting_results.xlsx") if p.is_file()), None)
        if path is None:
            raise FileNotFoundError("handwriting_results.xlsx not found (nor its approved copy) - run the handwriting test")
    ws = openpyxl.load_workbook(path, read_only=True)["Raw data"]
    rows = ws.iter_rows(values_only=True)
    head = next(rows)
    return [dict(zip(head, r)) for r in rows]


def crop_index():
    """{(scan, writer, page, row, field): crop path} from the runs the test read."""
    out = {}
    for method, path in RUNS.items():
        if not path.is_file():
            continue
        for scan, info in json.loads(path.read_text(encoding="utf-8")).items():
            run_path = OUTPUTS / "work" / "ocr_compare" / f"{info['run_id']}.json"
            if not run_path.is_file():
                continue
            run = json.loads(run_path.read_text(encoding="utf-8"))
            writer = scan.split("_")[0].upper()
            for row in run.get("rows", []):
                for f in row["fields"]:
                    out[(method, writer, int(f["page"]), row["row"] + 1, f["label"])] = f.get("crop")
                if row.get("row_crop"):
                    out[(method, writer, "row", row["row"] + 1)] = row["row_crop"]
    return out


def cutting_verdicts():
    """{(scan, writer, page, row, field): (cut, row number)} from the logbook cutting test, if it ran."""
    if not CUTTING.is_file():
        return {}
    import openpyxl
    ws = openpyxl.load_workbook(CUTTING, read_only=True)["Raw data"]
    rows = ws.iter_rows(values_only=True)
    head = next(rows)
    out = {}
    for r in rows:
        d = dict(zip(head, r))
        out[(d["Scan"], d["Writer"], int(d["Page"]), int(d["Row"]), d["Category"])] = (
            d.get("Cut (visual)"), d.get("Row number (visual)"))
    return out


def scored(c):
    return c["Detected"] == "Yes" and c["Blank in Key"] != "Yes"


def verdict(c):
    """The colour of a cell: what the system pre-fills (PaddleOCR + Correction)."""
    if c["Blank in Key"] == "Yes":
        return GREY, "blank in the logbook"
    if c["Detected"] != "Yes":
        return RED, "row not found"
    if c[f"{SYSTEM} Exact"] == "Yes":
        return GREEN, "exact"
    acc = c[f"{SYSTEM} Accuracy %"] or 0
    return (ORANGE, f"close ({acc:.0f}% of characters)") if acc >= CLOSE else (RED, f"wrong ({acc:.0f}% of characters)")


def draw_row(path, scan, writer, row, cells, crops, width=1300):
    from PIL import Image, ImageDraw
    title_f, label_f, text_f = _font(22, True), _font(15, True), _font(13)
    strip = None
    rc = crops.get((scan, writer, "row", row))
    if rc and (CROPS / rc).is_file():
        strip = Image.open(CROPS / rc).convert("RGB")
        strip = strip.resize((width - 20, int(strip.height * (width - 20) / strip.width)))
    tile_h, slot_min, cap_lines = 90, 236, 9
    tiles = []
    for c in sorted(cells, key=lambda c: (c["Page"], ["Case number", "Admitted", "Patient name", "Birthday", "Address",
                                                       "Reason for admission", "Delivered", "Final diagnosis",
                                                       "Went home"].index(c["Field"]))):
        im = None
        cp = crops.get((scan, writer, c["Page"], row, c["Field"]))
        if cp and (CROPS / cp).is_file():
            im = Image.open(CROPS / cp).convert("RGB")
            im = im.resize((max(1, int(im.width * tile_h / im.height)), tile_h))
            if im.width > 400:
                im = im.resize((400, int(tile_h * 400 / im.width)))
        tiles.append((c, im, max(slot_min, (im.width if im else 0) + 12)))
    lines, cur, x = [], [], 0
    for t in tiles:
        if x + t[2] > width - 20 and cur:
            lines.append(cur)
            cur, x = [], 0
        cur.append(t)
        x += t[2] + 8
    if cur:
        lines.append(cur)
    cap_h = 18 + 15 * cap_lines
    height = 44 + (strip.height + 16 if strip else 30) + len(lines) * (tile_h + cap_h + 22) + 8
    sheet = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), f"{writer} - row {row} - {scan} scan: what is written and what the OCR read", fill=(11, 61, 110),
           font=title_f)
    y = 44
    if strip:
        sheet.paste(strip, (10, y))
        y += strip.height + 16
    else:
        d.text((10, y), "(row not found on this scan)", fill=RED, font=text_f)
        y += 30
    for line in lines:
        x = 10
        for c, im, slot in line:
            colour, why = verdict(c)
            d.rectangle([x, y, x + (im.width if im else slot - 12) + 8, y + tile_h + 8], outline=colour, width=4)
            if im:
                sheet.paste(im, (x + 4, y + 4))
            else:
                d.text((x + 10, y + 36), "no cell", fill=RED, font=label_f)
            cy = y + tile_h + 12
            d.text((x, cy), f"{c['Field']}", fill=(20, 20, 20), font=label_f)
            cy += 18
            texts = [("written", c["Ground Truth"] or "(blank)", (20, 20, 20))]
            for eng, short in (("PaddleOCR", "Paddle"), (SYSTEM, "Paddle+corr"), ("TesseractOCR", "Tess"),
                               ("TesseractOCR + Correction", "Tess+corr")):
                ok = c.get(f"{eng} Exact") == "Yes"
                value = c.get(OUTPUT_COLUMN.get(eng, eng))
                texts.append((short, (value or "(nothing)") + ("  [exact]" if ok else ""),
                              GREEN if ok else (60, 60, 60)))
            used = 0
            for label, value, col in texts:
                for t in _wrap(d, f"{label}: {value}", text_f, slot - 6)[:2 if label in ("written", "Paddle+corr") else 1]:
                    if used < cap_lines - 1:
                        d.text((x, cy), t, fill=col, font=text_f)
                        cy += 15
                        used += 1
            d.text((x, y + tile_h + 12 + 18 + 15 * (cap_lines - 1)), why, fill=colour, font=label_f)
            x += slot + 8
        y += tile_h + cap_h + 22
    # drawn large for crisp text, saved at 1000 px wide to keep the report light
    sheet = sheet.resize((1000, int(sheet.height * 1000 / sheet.width)), Image.LANCZOS)
    sheet.save(path, quality=50, optimize=True)


def pick(h, sheet_, columns):
    """A table of only these columns (so it fits the page width); missing ones are skipped."""
    keep = [sheet_["headers"].index(c) for c in columns if c in sheet_["headers"]]
    table(h, [sheet_["headers"][i] for i in keep], [[r[i] for i in keep] for r in sheet_["rows"]])


def build(out_path, pictures=True):
    raw = read_raw()
    summary = json.loads((FOLDER / "summary.json").read_text(encoding="utf-8"))
    sheet = {s["name"][:2]: s for s in summary["sheets"]}
    crops = crop_index()
    cuts = cutting_verdicts()
    proof = FOLDER / "proof"
    if pictures:
        import shutil
        shutil.rmtree(proof, ignore_errors=True)
        proof.mkdir(parents=True)
    rows = {}
    for c in raw:
        c["Page"], c["Row"] = int(c["Page"]), int(c["Row"])
        rows.setdefault((c["Scan Method"], c["Writer ID"], c["Row"]), []).append(c)
    files = {}
    for (scan, writer, row), cells in sorted(rows.items()):
        name = f"{scan}_{writer}_row{row:02d}.jpg"
        if pictures:
            draw_row(proof / name, scan, writer, row, cells, crops)
        files[(scan, writer, row)] = name

    def headline(cells):
        s = [c for c in cells if scored(c)]
        out = {"cells": len(s)}
        for eng in ENGINES:
            out[eng] = (stats.percent(sum(c[f"{eng} Exact"] == "Yes" for c in s), len(s)),
                        round(sum(c[f"{eng} Accuracy %"] or 0 for c in s) / max(len(s), 1), 2))
        out["close"] = stats.percent(sum((c[f"{SYSTEM} Accuracy %"] or 0) >= CLOSE for c in s), len(s))
        return out

    by_scan = {m: headline([c for c in raw if c["Scan Method"] == m]) for m in ("scanner", "phone")}
    proper = {}
    if cuts:
        for m in ("scanner", "phone"):
            good = [c for c in raw if c["Scan Method"] == m and cuts.get(
                (m, c["Writer ID"], c["Page"], c["Row"], c["Field"])) == ("Proper", "Right")]
            bad = [c for c in raw if c["Scan Method"] == m and cuts.get(
                (m, c["Writer ID"], c["Page"], c["Row"], c["Field"])) not in (None, ("Proper", "Right"))]
            proper[m] = (headline(good), headline(bad))

    pics = Pictures()
    W = 523
    sc, ph = by_scan["scanner"], by_scan["phone"]
    h = [f"<style>{CSS}{EXTRA_CSS}</style><body>"]
    h.append('<h1 id="top">OCR accuracy (handwriting test) - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, Objective 3 (i), Eq. 3.1 - results of '
             f'{e(summary.get("generated_at", ""))}, report generated {datetime.date.today().isoformat()}</p>')
    h.append(f"""<div class="box"><b>Result.</b> On the 10 writers' logbook pages (scanner, {sc['cells']} cells with
      writing), the value the system pre-fills - <b>PaddleOCR + Correction</b> - is <b>exactly right in
      {sc[SYSTEM][0]}%</b> of cells, with <b>{sc[SYSTEM][1]}% of characters right</b> on average; {sc['close']}% of cells
      have at least {CLOSE:.0f}% of their characters right. Tesseract on the same cells: {sc['TesseractOCR + Correction'][0]}%
      exact, {sc['TesseractOCR + Correction'][1]}% of characters. Phone photos: {ph[SYSTEM][0]}% exact,
      {ph[SYSTEM][1]}% of characters.</div>""")
    if proper:
        g, b = proper["scanner"]
        h.append(f"""<div class="box"><b>Cutting matters.</b> On scanner cells that were cut properly (logbook cutting
          test), PaddleOCR + Correction gets {g[SYSTEM][1]}% of characters right ({g[SYSTEM][0]}% exact, {g['cells']}
          cells); on cells cut badly, {b[SYSTEM][1]}% ({b[SYSTEM][0]}% exact, {b['cells']} cells).</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("method", "2. How the test works and how to read the pictures"),
                          ("fields", "3. Per category and per writing style"), ("why", "4. Where the errors come from"),
                          ("verdict", "5. What this means"),
                          ("appA", "Appendix A - every row, scanner"), ("appB", "Appendix B - every row, phone")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents. "
             "The numbers are the handwriting test's (handwriting_results.xlsx, approved copy in "
             "outputs/approved/handwriting/).</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    h.append("<table><tr><th>Engine</th><th>Scanner exact %</th><th>Scanner characters %</th><th>Phone exact %</th>"
             "<th>Phone characters %</th></tr>")
    for eng in ENGINES:
        b = "<b>" if eng == SYSTEM else ""
        h.append(f"<tr><td>{b}{e(eng)}{'</b> (pre-filled)' if b else ''}</td><td class='num'>{sc[eng][0]}</td>"
                 f"<td class='num'>{sc[eng][1]}</td><td class='num'>{ph[eng][0]}</td><td class='num'>{ph[eng][1]}</td></tr>")
    h.append(f"</table><p class='muted'>Exact % (Eq. 3.1) = cells read exactly right / cells with writing in a "
             f"detected row. Characters % = mean of 100 x (1 - CER) per cell. Scanner {sc['cells']} cells, phone "
             f"{ph['cells']}.</p>")
    s1 = sheet["1s"]
    h.append("<h3>Scanner vs phone</h3>")
    table(h, s1["headers"], s1["rows"])
    a1 = sheet["1a"]
    keep = [a1["headers"].index(x) for x in ("Scan Method", "Writer", "Style", "Cells scored",
                                              "PaddleOCR + Correction Exact % (Eq. 3.1)",
                                              "PaddleOCR + Correction Character accuracy %",
                                              "TesseractOCR + Correction Exact % (Eq. 3.1)",
                                              "TesseractOCR + Correction Character accuracy %") if x in a1["headers"]]
    h.append("<h3>Per writer</h3>")
    table(h, [a1["headers"][i] for i in keep], [[r[i] for i in keep] for r in a1["rows"]])

    # 2
    h.append('<h2 id="method" class="break">2. How the test works and how to read the pictures</h2>')
    h.append(f"""<p>Ten people each wrote 11 fictional patients into a real logbook layout (W01-W05 in capitals, W06-W10
      in lower case). Each spread was scanned with a flatbed scanner and photographed with a phone. The Logbook Reader
      found the rows, cut each into its cells, and PaddleOCR read every cell; its correction step (the AI second look and
      the known-value lists) gives the value staff see. Tesseract read the very same cell pictures for comparison. Every
      cell is compared with what the writer actually wrote (the answer key).</p>
      <p><b>The pictures</b> (appendices): for each logbook row, the row as found on the scan, then each cell picture with
      what is written and the four readings. The frame is the value the system pre-fills (PaddleOCR + Correction):
      <span class="good">green</span> = exact, <span class="clip">orange</span> = close (at least {CLOSE:.0f}% of the
      characters right), <span class="bad">red</span> = wrong or row not found, grey = nothing written in the logbook
      (scored separately as false readings). A reading marked [exact] matched the answer key.</p>
      <p><b>Exact match is strict</b>: one wrong character - a missing hyphen, "0" for "O" - makes the cell wrong. That is
      Eq. 3.1 and the main measure; character accuracy shows how close the readings are.</p>""")

    # 3
    h.append('<h2 id="fields" class="break">3. Per category and per writing style</h2>')
    c1 = sheet["1c"]
    keep = [c1["headers"].index(x) for x in ("Scan Method", "Field", "Style", "Cells scored",
                                              "PaddleOCR + Correction Exact % (Eq. 3.1)",
                                              "PaddleOCR + Correction Exact % normalized",
                                              "PaddleOCR + Correction Character accuracy %",
                                              "TesseractOCR + Correction Character accuracy %") if x in c1["headers"]]
    table(h, [c1["headers"][i] for i in keep], [[r[i] for i in keep] for r in c1["rows"] if r[2] == "all"])
    b1 = sheet["1b"]
    h.append("<h3>Capitals vs lower case (median and range of the writers)</h3>")
    table(h, b1["headers"], b1["rows"])

    # 4
    h.append('<h2 id="why" class="break">4. Where the errors come from</h2>')
    if proper:
        h.append("<h3>4.1 Cutting (from the logbook cutting test)</h3>")
        h.append("<table><tr><th>Scan</th><th>Cells</th><th>Cut</th><th>Exact %</th><th>Characters %</th></tr>")
        for m in ("scanner", "phone"):
            g, b = proper[m]
            h.append(f"<tr><td>{m}</td><td class='num'>{g['cells']}</td><td>proper, right row</td>"
                     f"<td class='num'>{g[SYSTEM][0]}</td><td class='num'>{g[SYSTEM][1]}</td></tr>")
            h.append(f"<tr><td>{m}</td><td class='num'>{b['cells']}</td><td>clipped, shifted or wrong row</td>"
                     f"<td class='num'>{b[SYSTEM][0]}</td><td class='num'>{b[SYSTEM][1]}</td></tr>")
        h.append("</table><p class='muted'>PaddleOCR + Correction. A cell that holds only part of its writing, or "
                 "another row's, cannot be read right however good the OCR is.</p>")
    h.append("<h3>4.2 PaddleOCR's own confidence</h3>")
    table(h, sheet["1i"]["headers"], sheet["1i"]["rows"])
    h.append("<h3>4.3 The correction step</h3>")
    pick(h, sheet["1f"], ("Scan Method", "Engine", "Cells", "Exact % raw", "Exact % corrected",
                          "Character accuracy % raw", "Character accuracy % corrected",
                          "Correction precision (Eq. 3.3)", "Harmful correction rate (Eq. 3.4)"))
    h.append("<h3>4.4 Cells with nothing written (false readings)</h3>")
    pick(h, sheet["1e"], ("Scan Method", "Style", "Blank cells", "PaddleOCR false readings %",
                          "PaddleOCR + Correction false readings %", "TesseractOCR false readings %",
                          "TesseractOCR + Correction false readings %"))

    # 5
    h.append('<h2 id="verdict" class="break">5. What this means</h2>')
    h.append(f"""<p><b>The OCR does not read handwriting reliably enough to be used without review.</b> Exactly right
      cells: {sc[SYSTEM][0]}% on the scanner, {ph[SYSTEM][0]}% on the phone. Most readings are close but not exact
      ({sc[SYSTEM][1]}% of characters right on average on the scanner): useful as a starting point that staff correct, not
      as final values. That is how PClaimAssist uses them - every reading goes through the review page, and its
      confidence decides what is pre-filled - and why the review step is part of the design.</p>
      <p>Scanner scans are clearly better than phone photos; capitals better than lower case (section 3); and part of the
      error is the cutting, not the reading (section 4.1).</p>""")

    # appendices
    for anchor, letter, scan, title in (("appA", "A", "scanner", "Appendix A - every row, scanner"),
                                        ("appB", "B", "phone", "Appendix B - every row, phone")):
        h.append(f'<h2 id="{anchor}" class="break">{title}</h2>')
        writers = sorted({w for s, w, r in files if s == scan})
        h.append("<table class='small'><tr><th>Writer</th><th>Rows (exact cells of the cells with writing)</th></tr>")
        for w in writers:
            links = []
            for (s, ww, r) in sorted(files):
                if s == scan and ww == w:
                    cells = [c for c in rows[(s, ww, r)] if scored(c)]
                    ok = sum(c[f"{SYSTEM} Exact"] == "Yes" for c in cells)
                    links.append(f'<a href="#{letter}-{w}-r{r:02d}">{r}</a> ({ok}/{len(cells)})')
            h.append(f"<tr><td>{w}</td><td>{', '.join(links)}</td></tr>")
        h.append("</table>")
        for (s, w, r), name in sorted(files.items()):
            if s != scan:
                continue
            cells = [c for c in rows[(s, w, r)] if scored(c)]
            ok = sum(c[f"{SYSTEM} Exact"] == "Yes" for c in cells)
            n, size = pics.add(proof / name)
            h.append(f'<h3 id="{letter}-{w}-r{r:02d}" class="break">{w} - row {r} - {scan}: {ok} of {len(cells)} cells '
                     f'exact</h3>{img(n, size, W)}')
    h.append("</body>")
    render(h, pics, out_path, "OCR accuracy proof report", "Handwriting OCR accuracy, with a picture of every cell")
    return out_path, by_scan, proper


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=FOLDER / "ocr_accuracy_proof_report.pdf")
    ap.add_argument("--no-pictures", action="store_true", help="reuse the pictures already drawn")
    a = ap.parse_args()
    path, by_scan, proper = build(a.out, pictures=not a.no_pictures)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")
    print(json.dumps({"by_scan": by_scan, "proper_cut": proper}, indent=1))


if __name__ == "__main__":
    main()
