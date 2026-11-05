"""Correction module proof report: every change the correction module made
to an OCR reading (test 2, Eq. 3.2-3.4), with the cell picture, in one PDF
with bookmarks and links (same layout as the other proof reports), and a
workbook listing every change.

    python -m research_tests.correction_report

Each cell is judged by the correction test's own code
(correction_metrics.from_handwriting + judge), on the handwriting test's
readings; nothing is re-read. A change (corrected reading differs from the
raw one, capitals and spaces aside) is:
  Helpful          wrong before, exactly right after
  Harmful          exactly right before, wrong after
  Closer / Further wrong both times, with more / fewer characters right
  No difference    wrong both times, as many characters right
Writes, in outputs/correction_metrics/:
  proof/<scan>_<engine>_<NN>.jpg      the changes, 12 to a picture
  correction_changes.xlsx             every change
  correction_proof_report.pdf
"""
import argparse
import datetime
import json
import re
from pathlib import Path

from research_tests import OUTPUTS, output_dir
from research_tests import correction_metrics as cm
from research_tests.common import excel, stats
from research_tests.field_mapping_report import CSS, Pictures, e, img, render
from research_tests.logbook_cutting import _font, _wrap
from research_tests.logbook_cutting_report import EXTRA_CSS, table
from research_tests.ocr_accuracy_report import CROPS, crop_index, pick

FOLDER = OUTPUTS / "correction_metrics"
ENGINES = {"paddle": "PaddleOCR", "tesseract": "TesseractOCR"}
OUTCOMES = ("Helpful", "Harmful", "Closer", "Further", "No difference")
COLOURS = {"Helpful": (20, 150, 50), "Harmful": (220, 0, 0), "Closer": (40, 110, 200), "Further": (235, 130, 0),
           "No difference": (140, 140, 140)}
PER_SHEET = 12


APPROVED_HANDWRITING = OUTPUTS / "approved" / "handwriting" / "handwriting_results.xlsx"


def handwriting_workbook():
    """The handwriting test's results; its approved copy when the working one is not there (read only)."""
    for path in (cm.HANDWRITING, APPROVED_HANDWRITING):
        if path.is_file():
            return path
    raise FileNotFoundError(f"{cm.HANDWRITING} not found (nor its approved copy) - run the handwriting test first")


def outcome(j):
    if j["outcome"] == "helpful":
        return "Helpful"
    if j["outcome"] == "harmful":
        return "Harmful"
    if j["corrected_exact"] and j["raw_exact"]:
        return "No difference"
    d = (j["corrected_acc"] or 0) - (j["raw_acc"] or 0)
    return "Closer" if d > 0.005 else "Further" if d < -0.005 else "No difference"


def collect():
    """[change] for every changed cell, per engine, judged by the correction test's code."""
    cells = cm.from_handwriting(handwriting_workbook())
    crops = crop_index()
    changes, totals = [], {}
    for c in cells:
        if cm.is_blank(c):
            continue                                   # blank cells: false readings, apart (as in the test)
        scan = "phone" if "phone" in c["source"] else "scanner"
        m = re.match(r"(W\d+) p(\d+) row (\d+)", c["where"])
        writer, page, row = m.group(1), int(m.group(2)), int(m.group(3))
        for eng, name in ENGINES.items():
            j = cm.judge(c, eng)
            if not j:
                continue
            totals.setdefault((scan, name), []).append(j)
            if not j["changed"]:
                continue
            changes.append({"scan": scan, "engine": name, "writer": writer, "page": page, "row": row,
                            "field": c["field"], "truth": c["truth"], "raw": c[f"{eng}_raw"] or "",
                            "corrected": c[f"{eng}_corrected"] or "", "raw_exact": j["raw_exact"],
                            "corrected_exact": j["corrected_exact"], "raw_acc": j["raw_acc"],
                            "corrected_acc": j["corrected_acc"], "outcome": outcome(j),
                            "crop": crops.get((scan, writer, page, row, c["field"]))})
    order = {o: i for i, o in enumerate(OUTCOMES)}
    changes.sort(key=lambda x: (x["scan"] != "scanner", x["engine"] != "PaddleOCR", order[x["outcome"]],
                                x["writer"], x["page"], x["row"]))
    return changes, {k: cm.metrics(v) for k, v in totals.items()}


def draw_cards(path, title, cards, width=1300):
    from PIL import Image, ImageDraw
    cols, card_w, img_h, text_lines = 3, 416, 92, 8
    card_h = img_h + 14 + 16 * text_lines
    rows = (len(cards) + cols - 1) // cols
    sheet = Image.new("RGB", (width, 46 + rows * (card_h + 14)), "white")
    d = ImageDraw.Draw(sheet)
    title_f, label_f, text_f = _font(20, True), _font(14, True), _font(13)
    d.text((10, 10), title, fill=(11, 61, 110), font=title_f)
    for i, ch in enumerate(cards):
        x, y = 10 + (i % cols) * (card_w + 10), 46 + (i // cols) * (card_h + 14)
        colour = COLOURS[ch["outcome"]]
        d.rectangle([x, y, x + card_w, y + card_h], outline=colour, width=3)
        if ch["crop"] and (CROPS / ch["crop"]).is_file():
            im = Image.open(CROPS / ch["crop"]).convert("RGB")
            scale = min((card_w - 10) / im.width, img_h / im.height)
            im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))))
            sheet.paste(im, (x + 5, y + 5))
        cy = y + img_h + 10
        d.text((x + 6, cy), f"{ch['writer']} p{ch['page']} row {ch['row']} - {ch['field']}", fill=(20, 20, 20),
               font=label_f)
        cy += 17
        lines = []
        for label, value in (("written", ch["truth"]), ("raw", ch["raw"] or "(nothing)"),
                             ("corrected", ch["corrected"] or "(nothing)")):
            lines += _wrap(d, f"{label}: {value}", text_f, card_w - 12)[:2 if label != "written" else 1]
        for t in lines[:text_lines - 2]:
            d.text((x + 6, cy), t, fill=(50, 50, 50), font=text_f)
            cy += 15
        delta = (ch["corrected_acc"] or 0) - (ch["raw_acc"] or 0)
        d.text((x + 6, y + card_h - 20), f"{ch['outcome']}  ({ch['raw_acc']:.0f}% -> {ch['corrected_acc']:.0f}% "
                                         f"of characters, {delta:+.0f})", fill=colour, font=label_f)
    sheet = sheet.resize((1000, int(sheet.height * 1000 / width)), Image.LANCZOS)
    sheet.save(path, quality=50, optimize=True)


def build(out_path):
    summary = json.loads((FOLDER / "summary.json").read_text(encoding="utf-8"))
    sheet = {s["name"][:2]: s for s in summary["sheets"]}
    changes, totals = collect()
    proof = FOLDER / "proof"
    import shutil
    shutil.rmtree(proof, ignore_errors=True)
    proof.mkdir(parents=True)
    groups = {}
    for ch in changes:
        groups.setdefault((ch["scan"], ch["engine"]), []).append(ch)
    files = {}
    for (scan, eng), chs in groups.items():
        files[(scan, eng)] = []
        for k in range(0, len(chs), PER_SHEET):
            part = chs[k:k + PER_SHEET]
            name = f"{scan}_{eng.replace('OCR', '').lower()}_{k // PER_SHEET + 1:02d}.jpg"
            title = (f"{eng} - {scan}: changes {k + 1}-{k + len(part)} of {len(chs)}  "
                     f"({', '.join(sorted({c['outcome'] for c in part}, key=OUTCOMES.index))})")
            draw_cards(proof / name, title, part)
            for c in part:
                c["picture"] = name
            files[(scan, eng)].append((name, part))

    # the workbook: every change
    counts = []
    for (scan, eng), chs in groups.items():
        m = totals[(scan, eng)]
        counts.append([scan, eng, m["n"], len(chs)] + [sum(c["outcome"] == o for c in chs) for o in OUTCOMES]
                      + [m["precision"], m["harmful_rate"], m["exact_gain"], m["acc_gain"]])
    count_headers = ["Scan", "Engine", "Cells", "Changes"] + list(OUTCOMES) + [
        "Correction precision (Eq. 3.3)", "Harmful correction rate (Eq. 3.4)", "Exact improvement (pp, Eq. 3.2)",
        "Character accuracy improvement (pp, Eq. 3.2)"]
    out = output_dir("correction_metrics")
    excel.write_workbook(out / "correction_changes.xlsx", [
        {"name": "Every change", "headers": ["Scan", "Engine", "Writer", "Page", "Row", "Category", "Written",
                                              "Raw reading", "Corrected reading", "Raw exact", "Corrected exact",
                                              "Raw characters %", "Corrected characters %", "Change (pp)", "Outcome",
                                              "Picture"],
         "rows": [[c["scan"], c["engine"], c["writer"], c["page"], c["row"], c["field"], c["truth"], c["raw"],
                   c["corrected"], "Yes" if c["raw_exact"] else "No", "Yes" if c["corrected_exact"] else "No",
                   round(c["raw_acc"] or 0, 2), round(c["corrected_acc"] or 0, 2),
                   round((c["corrected_acc"] or 0) - (c["raw_acc"] or 0), 2), c["outcome"], c.get("picture")]
                  for c in changes]},
        {"name": "Outcomes", "title": "Table - What each change did, per scan and engine", "headers": count_headers,
         "rows": counts, "notes": ["Judged by research_tests/correction_metrics.py (judge), on the handwriting "
                                   "test's readings; blank cells left out, as in the test. Helpful = wrong before, "
                                   "exactly right after; Harmful = exactly right before, wrong after; Closer / "
                                   "Further = wrong both times, with more / fewer characters right."]},
    ])

    pics = Pictures()
    W = 523
    ps, pp = totals[("scanner", "PaddleOCR")], totals[("phone", "PaddleOCR")]
    cnt = {(r[0], r[1]): r for r in counts}
    sp = cnt[("scanner", "PaddleOCR")]
    o = {name: sp[4 + i] for i, name in enumerate(OUTCOMES)}
    h = [f"<style>{CSS}{EXTRA_CSS}</style><body>"]
    h.append('<h1 id="top">Correction module - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, Objective 3 (i), Eq. 3.2-3.4 - results of '
             f'{e(summary.get("generated_at", ""))}, report generated {datetime.date.today().isoformat()}</p>')
    h.append(f"""<div class="box"><b>Result.</b> On the scanner scans the correction module changed
      <b>{ps['changes']}</b> of PaddleOCR's {ps['n']} readings. <b>{ps['produced_correct']}</b> of those changes produced
      the correct value and <b>{ps['harmful']}</b> turned a correct reading wrong: correction precision
      <b>{ps['precision']}</b> (Eq. 3.3), harmful correction rate <b>{ps['harmful_rate']}</b> (Eq. 3.4). Exact matches
      went up by {ps['exact_gain']} percentage points and character accuracy by {ps['acc_gain']} (Eq. 3.2). Most changes
      leave the reading wrong but different: {o['Closer']} brought it closer to what is written, {o['Further']} moved it
      further away. Phone photos: {pp['changes']} changes, precision {pp['precision']}, harmful rate
      {pp['harmful_rate']}.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("method", "2. How the test works and how to read the pictures"),
                          ("helpful", "3. Every helpful change"), ("harmful", "4. Every harmful change"),
                          ("fields", "5. Per category"), ("blank", "6. Cells with nothing written"),
                          ("verdict", "7. What this means"),
                          ("appA", "Appendix A - every PaddleOCR change, scanner"),
                          ("appB", "Appendix B - every PaddleOCR change, phone"),
                          ("appC", "Appendix C - every TesseractOCR change, scanner"),
                          ("appD", "Appendix D - every TesseractOCR change, phone")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks, and every page links back to these contents. Every "
             "change is also listed in correction_changes.xlsx.</p>")

    # 1
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    a = sheet["2a"]
    pick(h, a, ("Source", "Engine", "Cells", "Exact % raw", "Exact % corrected", "Exact improvement (pp, Eq. 3.2)",
                "Character accuracy improvement (pp, Eq. 3.2)", "Changes made", "Correction precision (Eq. 3.3)",
                "Harmful correction rate (Eq. 3.4)"))
    h.append("<h3>What each change did</h3>")
    table(h, ["Scan", "Engine", "Cells", "Changes"] + list(OUTCOMES), [r[:4 + len(OUTCOMES)] for r in counts])
    check = all(totals[k]["changes"] == len(groups.get(k, [])) for k in totals)
    h.append(f"<p class='muted'>The changes pictured here are exactly the ones the test counted "
             f"({'checked: the counts match' if check else 'WARNING: the counts differ'}).</p>")

    # 2
    h.append('<h2 id="method" class="break">2. How the test works and how to read the pictures</h2>')
    h.append("""<p>For every handwritten cell the OCR read (handwriting test, rows the system found, cells with writing),
      the reading straight from the engine (<i>raw</i>) is compared with the reading after the Logbook Reader's correction
      module (<i>corrected</i>): the AI second look on unsure cells (a re-read of an enhanced picture), known fixes, place
      names and capitals. Both are scored against what the writer wrote.</p>
      <p><b>Eq. 3.2</b> accuracy improvement = corrected minus raw, in percentage points. <b>Eq. 3.3</b> correction
      precision = changes that produced the correct value / all changes. <b>Eq. 3.4</b> harmful correction rate =
      correct raw values made incorrect / all changes. A change = the corrected reading differs from the raw one, capitals
      and spaces aside.</p>
      <p><b>The pictures.</b> Each card is one change: the cell as the OCR saw it, what is written, the raw and the
      corrected reading, and the share of characters right before and after. Frame: <span class="good">green</span>
      helpful, <span class="bad">red</span> harmful, <span style="color:#286ec8"><b>blue</b></span> closer,
      <span class="clip">orange</span> further, grey no difference.</p>""")

    def cards_of(outcome_name, anchor, title):
        h.append(f'<h2 id="{anchor}" class="break">{title}</h2>')
        sel = [c for c in changes if c["outcome"] == outcome_name]
        if not sel:
            h.append("<p>None.</p>")
            return
        for (scan, eng) in [("scanner", "PaddleOCR"), ("phone", "PaddleOCR"), ("scanner", "TesseractOCR"),
                            ("phone", "TesseractOCR")]:
            part = [c for c in sel if (c["scan"], c["engine"]) == (scan, eng)]
            if not part:
                continue
            name = f"{outcome_name.lower()}_{scan}_{eng.lower()}.jpg"
            draw_cards(proof / name, f"{outcome_name} changes - {eng}, {scan} ({len(part)})", part)
            n, size = pics.add(proof / name)
            h.append(f"<h3>{eng}, {scan}: {len(part)}</h3>{img(n, size, W)}")

    cards_of("Helpful", "helpful", "3. Every helpful change (wrong before, exactly right after)")
    cards_of("Harmful", "harmful", "4. Every harmful change (right before, wrong after)")
    harm = [c for c in changes if c["outcome"] == "Harmful"]
    if harm and all(c["field"] == "Address" and re.fullmatch(r"\W*D[O0]\W*", c["truth"].strip(), re.I)
                    for c in harm):
        h.append("""<div class="warn"><b>All harmful changes are ditto marks.</b> Each is an Address where the writer
          wrote "-DO-" (same as the row above), the OCR read it right, and the "corrected" value is empty. That is by
          design: the Logbook Reader treats a cell holding only a ditto mark as "nothing to type"
          (logbook_pipeline.field_status), and case_bridge replaces a "-DO-" address with the address of the patient
          above. So these are counted as harmful by Eq. 3.4, but no reading was damaged. Worth confirming with the team
          that the address above is filled in when the review marks a ditto cell as empty.</div>""")

    # 5, 6
    h.append('<h2 id="fields" class="break">5. Per category</h2>')
    b = sheet["2b"]
    rows_b = [r for r in b["rows"] if r[2] == "PaddleOCR"]
    keep = [b["headers"].index(x) for x in ("Source", "Field", "Cells", "Exact improvement (pp, Eq. 3.2)",
                                             "Character accuracy improvement (pp, Eq. 3.2)", "Changes made",
                                             "Changes that produced the correct value",
                                             "Correct raw values made incorrect")]
    table(h, [b["headers"][i] for i in keep], [[r[i] for i in keep] for r in rows_b])
    h.append("<p class='muted'>PaddleOCR (the engine the system uses). Both engines are in correction_metrics_"
             "results.xlsx, sheet 2b.</p>")
    h.append('<h2 id="blank">6. Cells with nothing written</h2>')
    table(h, sheet["2c"]["headers"][:6], [r[:6] for r in sheet["2c"]["rows"]])
    h.append("<p class='muted'>A false reading = something read where nothing is written. Left out of every figure "
             "above, as in the test.</p>")

    # 7
    h.append('<h2 id="verdict" class="break">7. What this means</h2>')
    h.append(f"""<p><b>The correction module is safe but does little on handwriting.</b> It rarely breaks a correct
      reading ({ps['harmful']} of {ps['changes']} changes on the scanner) and fixes a few completely
      ({ps['produced_correct']}), so exact matches rise only {ps['exact_gain']} points. Its effect is mostly small:
      {o['Closer']} changes bring a reading closer to what is written and {o['Further']} move it further, for a net
      {ps['acc_gain']} points of character accuracy. It cannot repair a reading that is far off - and many are, because
      handwriting is hard to read and some cells were cut badly (see the logbook cutting and OCR accuracy reports).
      Staff review remains where readings are made right.</p>
      <p>These results are for the correction model as it starts (the system's starter rows only). The supplementary
      held-out comparison (outputs/approved/supplementary/) shows the effect once it has learned from one corrected
      spread.</p>""")

    # appendices
    for anchor, letter, scan, eng in (("appA", "A", "scanner", "PaddleOCR"), ("appB", "B", "phone", "PaddleOCR"),
                                      ("appC", "C", "scanner", "TesseractOCR"), ("appD", "D", "phone", "TesseractOCR")):
        h.append(f'<h2 id="{anchor}" class="break">Appendix {letter} - every {eng} change, {scan} '
                 f'({len(groups.get((scan, eng), []))})</h2>')
        h.append("<p class='muted'>In order: helpful, harmful, closer, further, no difference.</p>")
        for i, (name, part) in enumerate(files.get((scan, eng), [])):
            n, size = pics.add(proof / name)
            kinds = ", ".join(sorted({c["outcome"] for c in part}, key=OUTCOMES.index))
            h.append(f'<h3 id="{letter}-{scan}-{i + 1:02d}" class="break">{eng}, {scan}: changes '
                     f'{i * PER_SHEET + 1}-{i * PER_SHEET + len(part)} ({kinds})</h3>{img(n, size, W)}')
    h.append("</body>")
    render(h, pics, out_path, "Correction module proof report", "Every change the correction module made, with pictures")
    return out_path, counts, check


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=FOLDER / "correction_proof_report.pdf")
    a = ap.parse_args()
    path, counts, check = build(a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB); counts match the test: {check}")
    for r in counts:
        print(r)


if __name__ == "__main__":
    main()
