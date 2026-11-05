"""Test 3c - logbook cutting: does each cut of a logbook row hold the
writing of the category it is labelled with?

    python -m research_tests.logbook_cutting [--methods scanner,phone]

The Logbook Reader finds each patient row on the scanned spread and cuts
it into one picture per category (Case number, Admitted, Patient name,
Birthday, Address on the left page; Reason for admission, Delivered,
Final diagnosis, Went home on the right). This test checks those cuts -
the field mapping of the logbook - on the handwriting test's runs (same
scans, same pictures, nothing re-read): outputs/work/ocr_compare/<run>.json
and the cut pictures in outputs/work/uploads/review_crops/<run>/.

Each cut is judged from what PaddleOCR read in it (raw, before correction)
against the answer key's Handwriting sheet: the reading is compared (100 x
(1 - CER)) with what is written in every category of the same page, in the
same row and the rows just above and below.
  Right category      it matches its own category best (and at least 40)
  Wrong cut           it matches another category or another row clearly
                      better (by more than 10, and at least 50)
  Can't tell          nothing read, or too poor a reading to decide either way
  Blank cell: empty   nothing written there and nothing read
  Blank cell: holds writing   nothing written there, but the reading
                      matches writing from another cell (at least 50)
  Blank cell: stray marks     nothing written, a few marks read
Cut accuracy = right category / (right + wrong) x 100, on the cuts that
could be decided; the rest are counted and shown, never guessed.
The pipeline's own "writing crosses the cut edge" flag is reported beside it.

Pictures (outputs/logbook_cutting/proof/): for every row, the row as found
on the scan with its cuts below it, each labelled with its category, what
is written, what was read and the verdict (green / red / orange / grey).
"""
import csv
import json
import re
from pathlib import Path

from research_tests import INPUTS, OUTPUTS, output_dir
from research_tests.common import answer_key, excel, stats

TEST_KEY = "logbook_cutting"
TITLE = "Logbook cutting test"
WORK = OUTPUTS / "work"
RUNS = {"scanner": OUTPUTS / "handwriting" / "runs.json", "phone": OUTPUTS / "handwriting" / "runs_phone.json"}
RIGHT, WRONG, UNSURE = "Right category", "Wrong cut", "Can't tell"
BLANK_OK, BLANK_WRITING, BLANK_STRAY = "Blank cell: empty", "Blank cell: holds writing", "Blank cell: stray marks"
NOT_FOUND = "Row not found"
VERDICTS = (RIGHT, WRONG, UNSURE, BLANK_OK, BLANK_WRITING, BLANK_STRAY, NOT_FOUND)
COLOURS = {RIGHT: (20, 150, 50), WRONG: (220, 0, 0), UNSURE: (235, 130, 0), BLANK_OK: (140, 140, 140),
           BLANK_WRITING: (220, 0, 0), BLANK_STRAY: (140, 140, 140), NOT_FOUND: (220, 0, 0)}
MIN_OWN, MIN_OTHER, MARGIN = 40.0, 50.0, 10.0

VISUAL = INPUTS / "logbook_cutting_visual_check.csv"
# The cut itself, and - separately - the row number the system gave it.
V_PROPER, V_CLIPPED, V_COLUMN, V_HALF, V_EMPTY, V_MISSING = (
    "Proper", "Clipped", "Wrong column", "Half of two entries", "Empty paper", "Not found")
V_VERDICTS = (V_PROPER, V_CLIPPED, V_COLUMN, V_HALF, V_EMPTY, V_MISSING)
V_CORRECT = V_PROPER
V_COLOURS = {V_PROPER: (20, 150, 50), V_CLIPPED: (235, 130, 0), V_COLUMN: (220, 0, 0), V_HALF: (220, 0, 0),
             V_EMPTY: (220, 0, 0), V_MISSING: (220, 0, 0)}
ROW_OFF_COLOUR = (120, 60, 190)          # a proper cut numbered as another row


HUMAN = INPUTS / "logbook_cutting_human_check.csv"
H_TAGS = {"correct": "Correct", "partly": "Partly", "wrong": "Not at all"}
H_COLOURS = {"correct": (20, 150, 50), "partly": (235, 130, 0), "wrong": (220, 0, 0)}


def load_human(path=HUMAN):
    """{(scan, writer, page, row, category): tag} - your own check of the cuts
    (research_tests.logbook_cutting_review): correct, partly or wrong."""
    out = {}
    if path.is_file():
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                tag = (r.get("Tag") or "").strip().lower()
                if tag in H_TAGS:
                    out[(r["Scan"].strip(), r["Writer"].strip().upper(), int(r["Page"]), int(r["Row"]),
                         r["Category"].strip())] = tag
    return out


def vis_colour(l):
    if l.get("human"):
        return H_COLOURS[l["human"]]
    if l.get("visual") == V_PROPER and str(l.get("rownum", "")).startswith("Off"):
        return ROW_OFF_COLOUR
    return V_COLOURS.get(l.get("visual"), COLOURS[l["verdict"]])


def vis_label(l):
    if l.get("human"):
        return f"you: {H_TAGS[l['human']]}"
    if not l.get("visual"):
        return "not checked"
    row = l.get("rownum") or ""
    return l["visual"] + (f", row {row.lower()}" if row.startswith("Off") else "")


def _rows(spec):
    spec = str(spec or "").strip().lower()
    if spec in ("", "all"):
        return None
    out = set()
    for part in spec.replace(" ", "").split(","):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def load_visual(path=VISUAL):
    """The visual check of the cuts (one line per scan, writer, page and
    category, or * for the rest of that page): [(scan, writer, page,
    category, rows or None, cut, row number, note)]."""
    import csv
    if not path.is_file():
        return []
    out = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if not (r.get("Writer") or "").strip():
                continue
            verdict = r["Cut"].strip()
            if verdict not in V_VERDICTS:
                raise ValueError(f"{path.name}: unknown cut verdict {verdict!r} (use one of {', '.join(V_VERDICTS)})")
            rownum = (r.get("Row number") or "").strip()
            if rownum in ("", "-"):
                rownum = ""
            elif rownum != "Right" and not rownum.startswith("Off by "):
                raise ValueError(f"{path.name}: Row number must be Right, Off by N or -, not {rownum!r}")
            out.append((r["Scan"].strip().lower(), r["Writer"].strip().upper(), int(r["Page"]),
                        r["Category"].strip(), _rows(r.get("Rows")), verdict, rownum, (r.get("Note") or "").strip()))
    return out


def visual_of(rules, method, writer, page, field, row):
    """(cut, row number, note) for one cut: a rule naming the category wins over *."""
    for want_star in (False, True):
        for scan, w, pg, cat, rows, verdict, rownum, note in rules:
            if (scan, w, pg) != (method, writer, page) or (cat == "*") != want_star:
                continue
            if (cat == "*" or cat == field) and (rows is None or row in rows):
                return verdict, rownum, note
    return None, "", ""


def similarity(truth, reading):
    from benchmarks.metrics import character_accuracy_percent
    t, r = " ".join(str(truth or "").split()).upper(), " ".join(str(reading or "").split()).upper()
    if not t:
        return None
    return max(0.0, min(100.0, character_accuracy_percent(t, r)))


def _norm(text):
    return " ".join(str(text or "").split()).upper()


def piece_similarity(truth, reading, min_len=8):
    """How well the reading matches a PIECE of the truth, or the truth a
    piece of the reading - a cut holding part of a column, or a column and
    a bit of the next. Windows of the longer text, as long as the shorter
    (at least min_len characters); the best 100 x (1 - CER)."""
    t, r = _norm(truth), _norm(reading)
    short, long_ = (t, r) if len(t) <= len(r) else (r, t)
    if len(short) < min_len:
        return similarity(t, r) if t else None
    best = 0.0
    for i in range(0, len(long_) - len(short) + 1):
        window = long_[i:i + len(short)]
        s = similarity(short, window) if short == t else similarity(window, short)
        best = max(best, s or 0.0)
        if best >= 99.9:
            break
    return best


def judge(field, truth_here, reading, candidates):
    """(verdict, best other (label, similarity) or None, own similarity).
    Own and other scores take the better of the whole text and a piece of
    it, so a cut holding part of a column - or a column and part of the
    next - is caught. A category whose writing is nearly the same as this
    one's ("FOR WELL BABY CARE" / "WELL BABY CARE") cannot tell them apart
    and is left out of the comparison."""
    has_reading = len(re.sub(r"[^A-Za-z0-9]", "", reading or "")) >= 2
    usable = [(label, t) for label, t in candidates if t
              and not (truth_here and similarity(truth_here, t) >= 60)
              and not (truth_here and (piece_similarity(truth_here, t) or 0) >= 85)]
    scored = [(label, max(similarity(t, reading) or 0, piece_similarity(t, reading) or 0)) for label, t in usable]
    best = max(scored, key=lambda x: x[1]) if scored and has_reading else None
    if not truth_here:
        if not has_reading:
            return BLANK_OK, None, None
        if best and best[1] >= 75:
            return BLANK_WRITING, best, None
        return BLANK_STRAY, best, None
    if not has_reading:
        return UNSURE, None, 0.0
    own = max(similarity(truth_here, reading) or 0, piece_similarity(truth_here, reading) or 0)
    if best and best[1] >= 75 and best[1] > own + MARGIN:
        return WRONG, best, own
    if own >= MIN_OWN and (best is None or own >= best[1]):
        return RIGHT, best, own
    return UNSURE, best, own


def load_run(run_id):
    path = WORK / "ocr_compare" / f"{run_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def run(progress, methods="scanner,phone", writers=None, no_pictures=False):
    key = answer_key.handwriting(INPUTS / "answer_key.xlsx")
    rules = load_visual()
    human = load_human()
    wanted = {w.strip().upper() for w in writers.split(",")} if writers else None
    out = output_dir(TEST_KEY)
    proof = out / "proof"
    if not no_pictures:
        import shutil
        shutil.rmtree(proof, ignore_errors=True)
        proof.mkdir(parents=True)
    lines, sheets_index, flags = [], [], []
    method_list = [m.strip() for m in methods.split(",") if m.strip()]
    jobs = []
    for method in method_list:
        runs = json.loads(RUNS[method].read_text(encoding="utf-8"))
        for scan, info in sorted(runs.items()):
            writer = scan.split("_")[0].upper()
            if wanted and writer not in wanted:
                continue
            jobs.append((method, scan, writer, info["run_id"]))
    for n, (method, scan, writer, run_id) in enumerate(jobs):
        progress(0.02 + 0.9 * n / max(len(jobs), 1), f"{method} {writer}: judging the cuts")
        run_ = load_run(run_id)
        cells, rows_found, row_crops = {}, set(), {}
        for row in (run_ or {}).get("rows", []):
            if row.get("row_crop"):
                row_crops[row["row"] + 1] = row["row_crop"]
            for f in row["fields"]:
                cells[(int(f["page"]), row["row"] + 1, f["label"])] = f
                rows_found.add((int(f["page"]), row["row"] + 1))
        mine = [k for k in key if k["writer"] == writer]
        truth = {}
        for k in mine:
            truth.setdefault((k["page"], k["row"]), {})[k["field"]] = k["truth"]
        row_lines = {}
        for k in mine:
            page, row, field = k["page"], k["row"], k["field"]
            f = cells.get((page, row, field))
            candidates = []
            for r in (row - 1, row, row + 1):
                for other, t in truth.get((page, r), {}).items():
                    if (r, other) != (row, field):
                        where = "" if r == row else (" (row above)" if r < row else " (row below)")
                        candidates.append((f"{other}{where}", t))
            if f is None:
                verdict, best, own = NOT_FOUND, None, None
                reading = ""
            else:
                reading = f.get("paddle_raw") or ""
                verdict, best, own = judge(field, k["truth"], reading, candidates)
            line = {"method": method, "writer": writer, "style": k["style"], "scan": scan, "page": page, "row": row,
                    "field": field, "column": f.get("column") if f else None, "truth": k["truth"], "read": reading,
                    "own": own, "best_other": best[0] if best else "", "best_sim": best[1] if best else None,
                    "verdict": verdict, "cut_flag": bool(f and f.get("cut_flag")),
                    "crop": f.get("crop") if f else None, "run_id": run_id}
            line["visual"], line["rownum"], line["visual_note"] = visual_of(rules, method, writer, page, field, row)
            line["human"] = human.get((method, writer, page, row, field))
            lines.append(line)
            row_lines.setdefault(row, []).append(line)
        if not no_pictures:
            for row in sorted(row_lines):
                name = f"{method}_{writer}_row{row:02d}.jpg"
                draw_row_sheet(proof / name, method, writer, row, row_crops.get(row), row_lines[row])
                bad = sum(l["visual"] is not None and (l["visual"] != V_PROPER or l["rownum"] != "Right")
                          for l in row_lines[row])
                unsure = sum(l["visual"] is None for l in row_lines[row])
                sheets_index.append({"file": name, "method": method, "writer": writer, "row": row,
                                     "wrong": bad, "unsure": unsure,
                                     "verdicts": {l["field"]: l["visual"] for l in row_lines[row]}})

    mosaics = []
    if not no_pictures:
        progress(0.93, "Drawing the page mosaics")
        for method in method_list:
            for writer in sorted({l["writer"] for l in lines if l["method"] == method}):
                for page in (1, 2):
                    name = f"mosaic_{method}_{writer}_p{page}.jpg"
                    draw_page_mosaic(proof / name, method, writer, page, lines)
                    mosaics.append({"file": name, "method": method, "writer": writer, "page": page})

    progress(0.95, "Summarising")
    decided = lambda g: [l for l in g if l["verdict"] in (RIGHT, WRONG)]

    def summary_row(label, g):
        d = decided(g)
        return [label, len(g)] + [sum(l["verdict"] == v for l in g) for v in VERDICTS] + [
            len(d), stats.percent(sum(l["verdict"] == RIGHT for l in d), len(d)),
            sum(l["cut_flag"] for l in g)]

    def visual_row(label, g):
        numbered = [l for l in g if l["rownum"]]
        return [label, len(g)] + [sum(l["visual"] == v for l in g) for v in V_VERDICTS] + [
            sum(l["visual"] is None for l in g),
            stats.percent(sum(l["visual"] == V_PROPER for l in g), len(g)),
            stats.percent(sum(l["visual"] in (V_PROPER, V_CLIPPED) for l in g), len(g)),
            stats.percent(sum(l["rownum"] == "Right" for l in numbered), len(numbered)),
            stats.percent(sum(l["visual"] == V_PROPER and l["rownum"] == "Right" for l in g), len(g))]

    def grouped(fn, by):
        out_rows = []
        for method in method_list:
            g_m = [l for l in lines if l["method"] == method]
            if by == "writer":
                keys = sorted({l["writer"] for l in g_m})
            else:
                keys = [f for f in answer_key.FIELDS if any(l["field"] == f for l in g_m)]
            for k in keys:
                g = [l for l in g_m if (l["writer"] if by == "writer" else l["field"]) == k]
                label = f"{k} ({g[0]['style']})" if by == "writer" else k
                out_rows.append([method] + fn(label, g))
            if g_m:
                out_rows.append([method] + fn("All writers" if by == "writer" else "All categories", g_m))
        return out_rows

    v_writer, v_field = grouped(visual_row, "writer"), grouped(visual_row, "field")
    per_writer, per_field = grouped(summary_row, "writer"), grouped(summary_row, "field")
    agree = []
    for method in method_list:
        g = [l for l in lines if l["method"] == method]
        for v in V_VERDICTS:
            gv = [l for l in g if l["visual"] == v]
            agree.append([method, v, len(gv)] + [sum(l["verdict"] == a for l in gv) for a in VERDICTS])
    problems = [[l["method"], l["writer"], l["page"], l["row"], l["field"], l["visual"], l["rownum"] or "-",
                 l["visual_note"], l["truth"], l["read"], l["verdict"]]
                for l in lines if l["visual"] is not None and (l["visual"] != V_PROPER or l["rownum"] != "Right")]
    v_headers = ["Cuts"] + list(V_VERDICTS) + ["Not checked", "Proper cuts %", "Proper or clipped %",
                                               "Right row number %", "Proper and right row %"]
    headers = ["Cuts"] + list(VERDICTS) + ["Cuts decided", "Cut accuracy %", "Writing crosses the cut edge"]
    v_notes = [
        "Visual check (inputs/logbook_cutting_visual_check.csv): every cut was looked at in the page mosaics "
        "(outputs/logbook_cutting/proof/mosaic_*.jpg). The CUT: Proper (one whole entry, its own column, nothing "
        "missing), Clipped (its own column, but part of the writing is outside), Wrong column (holds another column's "
        "writing), Half of two entries (the bottom of one entry and the top of the next), Empty paper (below the last "
        "entry), Not found (no cut). Separately, the ROW NUMBER the system gave it: Right, or Off by N (a proper cut "
        "of another row's entry - the left page is then paired with the wrong right-page row).",
        "Proper cuts % = Proper / all cuts x 100 (how well the cutting works). Right row number % = cuts numbered as "
        "the right logbook row / cuts holding an entry. Proper and right row % = both.",
        "The visual check was made by Claude from the mosaics; it is a checkable input - confirm or correct it, "
        "then rerun.",
    ]
    notes = [
        "Automatic judging, for support: PaddleOCR's raw reading of each cut compared (100 x (1 - CER), whole text "
        "or a piece of it) with what is written in every category of the same page, in the same row and the rows "
        "above and below. Wrong: another category or row matches clearly better. It cannot see a cut that holds "
        "part of two columns when the reading is poor, so it says 'can't tell' there - see 4e.",
    ]
    human_sheets = []
    if any(l["human"] for l in lines):
        def human_row(label, g):
            t = [l for l in g if l["human"]]
            n = lambda tag: sum(l["human"] == tag for l in t)
            return [label, len(g), len(t), n("correct"), n("partly"), n("wrong"), len(g) - len(t),
                    stats.percent(n("correct"), len(t)), stats.percent(n("correct") + n("partly"), len(t))]
        h_headers = ["Cuts", "Tagged by you", "Correct", "Partly", "Not at all", "Not tagged yet", "Correct %",
                     "Correct or partly %"]
        h_notes = ["Your own check (inputs/logbook_cutting_human_check.csv, made with research_tests."
                   "logbook_cutting_review): every cut tagged Correct (its own column's writing, whole), Partly (part "
                   "of it, or with some of another column) or Not at all. Percentages are of the cuts you tagged.",
                   f"Tagged: {sum(1 for l in lines if l['human'])} of {len(lines)} cuts."]
        suggested = {"Proper": "correct", "Clipped": "partly", "Wrong column": "wrong",
                     "Half of two entries": "wrong", "Empty paper": "wrong", "Not found": "wrong"}
        agree_rows = []
        for method in method_list:
            t = [l for l in lines if l["method"] == method and l["human"]]
            for tag in ("correct", "partly", "wrong"):
                g = [l for l in t if suggested.get(l["visual"]) == tag]
                agree_rows.append([method, H_TAGS[tag], len(g)] + [sum(l["human"] == x for l in g)
                                                                    for x in ("correct", "partly", "wrong")])
        changed = [[l["method"], l["writer"], l["page"], l["row"], l["field"], H_TAGS[l["human"]], l["visual"],
                    l["truth"], l["read"]] for l in lines if l["human"] in ("partly", "wrong")]
        human_sheets = [
            {"name": "4-You per writer", "title": "Table - Logbook cutting per writer (your check)",
             "headers": ["Scan", "Writer"] + h_headers, "rows": grouped(human_row, "writer"), "notes": h_notes},
            {"name": "4-You per category", "title": "Table - Logbook cutting per category (your check)",
             "headers": ["Scan", "Category"] + h_headers, "rows": grouped(human_row, "field"), "notes": h_notes},
            {"name": "4-You vs earlier check", "title": "Table - Your tags against the earlier visual check",
             "headers": ["Scan", "Earlier check suggested", "Cuts", "You: Correct", "You: Partly", "You: Not at all"],
             "rows": agree_rows, "notes": ["Earlier check = inputs/logbook_cutting_visual_check.csv (made by Claude "
                                           "from the mosaics), shown on the review page as the suggestion."]},
            {"name": "4-You partly or not", "title": "Every cut you tagged Partly or Not at all",
             "headers": ["Scan", "Writer", "Page", "Row", "Category", "Your tag", "Earlier check", "Written",
                         "Read in the cut"], "rows": changed,
             "notes": ["None." if not changed else f"{len(changed)} cuts."]},
        ]
    sheets = human_sheets + [
        {"name": "4a Visual per writer", "title": "Table - Logbook cutting per writer (visual check of every cut)",
         "headers": ["Scan", "Writer"] + v_headers, "rows": v_writer, "notes": v_notes},
        {"name": "4b Visual per category", "title": "Table - Logbook cutting per category (visual check)",
         "headers": ["Scan", "Category"] + v_headers, "rows": v_field},
        {"name": "4c Problem cuts", "title": "Every cut that is not proper, or numbered as another row",
         "headers": ["Scan", "Writer", "Page", "Row", "Category", "Cut", "Row number", "What is wrong", "Written",
                     "Read in the cut", "Automatic verdict"], "rows": problems,
         "notes": ["None." if not problems else f"{len(problems)} cuts."]},
        {"name": "4d Automatic per writer", "title": "Table - Automatic judging per writer (support)",
         "headers": ["Scan", "Writer"] + headers, "rows": per_writer, "notes": notes},
        {"name": "4e Visual vs automatic", "title": "Table - What the automatic judging said, per visual verdict",
         "headers": ["Scan", "Visual verdict", "Cuts"] + list(VERDICTS), "rows": agree},
        {"name": "4f Automatic per category", "title": "Table - Automatic judging per category (support)",
         "headers": ["Scan", "Category"] + headers, "rows": per_field},
    ]
    raw = {"name": "Raw data", "headers": ["Scan", "Writer", "Style", "Scan file", "Page", "Row", "Category",
                                           "Column", "Written", "Read in the cut (PaddleOCR raw)", "Your tag",
                                           "Cut (visual)",
                                           "Row number (visual)", "Visual note", "Automatic verdict", "Own similarity",
                                           "Best match elsewhere", "Its similarity",
                                           "Writing crosses the cut edge", "Cut picture", "Run ID"],
           "rows": [[l["method"], l["writer"], l["style"], l["scan"], l["page"], l["row"], l["field"], l["column"],
                     l["truth"], l["read"], H_TAGS.get(l["human"], ""), l["visual"], l["rownum"] or "-",
                     l["visual_note"], l["verdict"], l["own"], l["best_other"],
                     l["best_sim"], "Yes" if l["cut_flag"] else "No", l["crop"], l["run_id"]] for l in lines]}
    path = excel.write_workbook(out / "logbook_cutting_results.xlsx", [raw] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"methods": method_list})
    outputs = [path]
    if not no_pictures:
        (proof / "manifest.json").write_text(json.dumps({"sheets": sheets_index, "mosaics": mosaics,
                                                         "human": {s_["name"]: s_ for s_ in human_sheets},
                                                         "v_writer": v_writer, "v_field": v_field,
                                                         "v_headers": v_headers, "per_writer": per_writer,
                                                         "per_field": per_field, "verdicts": list(VERDICTS),
                                                         "headers": headers, "agree": agree,
                                                         "problems": problems},
                                                        indent=1, default=str), encoding="utf-8")
    progress(1.0, "Done")
    head = [r for r in v_writer if r[1] == "All writers"]
    return {"outputs": outputs, "headline": [[f"{r[0]}: proper cuts %", r[-4]] for r in head]
            + [[f"{r[0]}: proper or clipped %", r[-3]] for r in head]
            + [[f"{r[0]}: right row number %", r[-2]] for r in head]
            + [[f"{r[0]}: proper and right row %", r[-1]] for r in head]
            + [[f"{r[0]}: cuts / " + " / ".join(V_VERDICTS).lower(), " / ".join(str(x) for x in r[2:9])]
               for r in head]}


# ── the picture of one row ─────────────────────────────────────────────

def _font(size, bold=False):
    from PIL import ImageFont
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, width):
    words, out, line = str(text).split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=font) <= width or not line:
            line = test
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out or [""]


def draw_row_sheet(path, method, writer, row, row_crop, lines, width=1300):
    """The row as found, then its cuts in page order, each labelled."""
    from PIL import Image, ImageDraw
    crops_dir = WORK / "uploads" / "review_crops"
    title_f, label_f, text_f = _font(22, True), _font(15, True), _font(13)
    parts = []
    strip = None
    if row_crop and (crops_dir / row_crop).is_file():
        strip = Image.open(crops_dir / row_crop).convert("RGB")
        strip = strip.resize((width - 20, int(strip.height * (width - 20) / strip.width)))
    pages = {}
    for l in sorted(lines, key=lambda l: (l["page"], l["column"] or 99)):
        pages.setdefault(l["page"], []).append(l)
    tile_h, slot_min, cap_h = 96, 236, 110
    tile_rows = []
    for page in sorted(pages):
        x, current = 0, []
        for l in pages[page]:
            img = None
            if l["crop"] and (crops_dir / l["crop"]).is_file():
                img = Image.open(crops_dir / l["crop"]).convert("RGB")
                img = img.resize((max(1, int(img.width * tile_h / img.height)), tile_h))
                if img.width > 420:
                    img = img.resize((420, int(tile_h * 420 / img.width)))
            slot = max(slot_min, (img.width if img else 0) + 12)
            if x + slot > width - 20 and current:
                tile_rows.append(current)
                current, x = [], 0
            current.append((l, img, slot))
            x += slot + 8
        if current:
            tile_rows.append(current)
    height = 44 + (strip.height + 16 if strip else 30) + len(tile_rows) * (tile_h + cap_h + 20) + 10
    sheet = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), f"{writer} - row {row} - {method} scan", fill=(11, 61, 110), font=title_f)
    y = 44
    if strip:
        sheet.paste(strip, (10, y))
        y += strip.height + 16
    else:
        d.text((10, y), "(row picture not kept)", fill=(120, 120, 120), font=text_f)
        y += 30
    for tiles in tile_rows:
        x = 10
        for l, img, slot in tiles:
            colour = vis_colour(l)
            box_w = (img.width if img else slot - 12) + 8
            d.rectangle([x, y, x + box_w, y + tile_h + 8], outline=colour, width=4)
            if img:
                sheet.paste(img, (x + 4, y + 4))
            else:
                d.text((x + 10, y + 36), "no cut", fill=(200, 0, 0), font=label_f)
            cy = y + tile_h + 12
            d.text((x, cy), f"{l['field']} (p{l['page']})", fill=(20, 20, 20), font=label_f)
            cy += 18
            for t in (_wrap(d, f"written: {l['truth'] or '(blank)'}", text_f, slot - 6)[:2]
                      + _wrap(d, f"read: {l['read'] or '(nothing)'}", text_f, slot - 6)[:2]):
                d.text((x, cy), t, fill=(60, 60, 60), font=text_f)
                cy += 15
            d.text((x, min(cy, y + tile_h + cap_h - 16)), f"Cut: {vis_label(l)}", fill=colour,
                   font=label_f)
            auto = l["verdict"] + (f": {l['best_other']}" if l["verdict"] in (WRONG, BLANK_WRITING) else "")
            d.text((x, min(cy + 17, y + tile_h + cap_h)), _wrap(d, f"auto: {auto}", text_f, slot - 6)[0],
                   fill=(110, 110, 110), font=text_f)
            x += slot + 8
        y += tile_h + cap_h + 20
    sheet.save(path, quality=58, optimize=True)


def draw_page_mosaic(path, method, writer, page, lines, tile_h=64, max_w=300):
    """Every cut of one logbook page: a column per category (in page order),
    a row per logbook row - a shifted or clipped column shows at a glance."""
    from PIL import Image, ImageDraw
    crops_dir = WORK / "uploads" / "review_crops"
    mine = [l for l in lines if l["method"] == method and l["writer"] == writer and l["page"] == page]
    fields = [f for f in answer_key.FIELDS if any(l["field"] == f for l in mine)]
    fields.sort(key=lambda f: min((l["column"] or 99) for l in mine if l["field"] == f))
    rows = sorted({l["row"] for l in mine})
    cell = {(l["row"], l["field"]): l for l in mine}
    imgs, widths = {}, {f: 120 for f in fields}
    for (r, f), l in cell.items():
        if l["crop"] and (crops_dir / l["crop"]).is_file():
            im = Image.open(crops_dir / l["crop"]).convert("RGB")
            im = im.resize((max(1, int(im.width * tile_h / im.height)), tile_h))
            if im.width > max_w:
                im = im.resize((max_w, int(tile_h * max_w / im.width)))
            imgs[(r, f)] = im
            widths[f] = max(widths[f], im.width + 8)
    head_f, row_f = _font(15, True), _font(14, True)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for f in fields:        # a column is at least as wide as its heading, so headings never run together
        widths[f] = max(widths[f], int(measure.textlength(f, font=head_f)) + 16)
    left, top = 46, 64
    width = left + sum(widths[f] + 6 for f in fields) + 10
    height = top + len(rows) * (tile_h + 10) + 10
    sheet = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), f"{writer} - {method} scan - {'left' if page == 1 else 'right'} page: every cut, by category",
           fill=(11, 61, 110), font=_font(18, True))
    x = left
    for f in fields:
        d.text((x, 38), f, fill=(20, 20, 20), font=head_f)
        x += widths[f] + 6
    for i, r in enumerate(rows):
        y = top + i * (tile_h + 10)
        d.text((8, y + tile_h // 2 - 8), f"{r}", fill=(20, 20, 20), font=row_f)
        x = left
        for f in fields:
            l = cell.get((r, f))
            colour = vis_colour(l) if l else (220, 0, 0)
            im = imgs.get((r, f))
            d.rectangle([x, y, x + (im.width if im else widths[f] - 8) + 4, y + tile_h + 4], outline=colour, width=2)
            if im:
                sheet.paste(im, (x + 2, y + 2))
            else:
                d.text((x + 8, y + tile_h // 2 - 8), "no cut", fill=(200, 0, 0), font=row_f)
            x += widths[f] + 6
    sheet.save(path, quality=60, optimize=True)


def add_arguments(parser):
    parser.add_argument("--methods", default="scanner,phone", help="scanner, phone or both (default)")
    parser.add_argument("--writers", default=None, help="e.g. W01,W02 (default all)")
    parser.add_argument("--no-pictures", action="store_true")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
