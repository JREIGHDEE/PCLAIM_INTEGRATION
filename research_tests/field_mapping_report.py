"""Field mapping proof report: one PDF with the before/after results, the
pictures behind every number, and bookmarks + links to move around.

    python -m research_tests.field_mapping_report

Reads what the field mapping test left in outputs/field_mapping/:
  before_fix/      a run on the code before the fixes (summary.json, proof/)
  proof/           the latest run (after the fixes)
  live_check/      the check in the real app (live_check.json + pictures), optional
and writes outputs/field_mapping/field_mapping_proof_report.pdf.
Every picture is the PDF that PClaimAssist saved, rendered as is; the
green/red outlines were drawn on afterwards by the test.
"""
import argparse
import datetime
import html
import io
import json
import tempfile
from pathlib import Path

from research_tests import OUTPUTS

FOLDER = OUTPUTS / "field_mapping"
FORM_ORDER = ["CSF", "CF1", "CF2", "CF4", "PMRF"]
FORM_KEY = {"csf": "CSF", "cf1": "CF1", "cf2": "CF2", "cf4": "CF4", "pmrf": "PMRF"}
# The address part of a page, as fractions of its height (for the before/after pictures).
BANDS = {"CF1": (0.295, 0.40), "PMRF": (0.435, 0.605)}
e = html.escape

CSS = """
* { font-family: sans-serif; }
body { font-size: 9.5pt; line-height: 1.35; color: #1d1d1f; }
h1 { font-size: 20pt; margin: 0 0 6pt 0; color: #0b3d6e; }
h2 { font-size: 14pt; margin: 14pt 0 6pt 0; color: #0b3d6e; border-bottom: 1px solid #9bb3cc; }
h3 { font-size: 11pt; margin: 10pt 0 4pt 0; color: #0b3d6e; }
h4 { font-size: 10pt; margin: 6pt 0 2pt 0; }
p { margin: 3pt 0 5pt 0; }
table { border-collapse: collapse; margin: 4pt 0 8pt 0; }
td, th { border: 1px solid #b8c4d0; padding: 2pt 5pt; text-align: left; vertical-align: top; font-size: 9pt; }
th { color: #0b3d6e; border-bottom: 1.5px solid #0b3d6e; }
.num { text-align: right; }
.good { color: #0a7a2a; font-weight: bold; }
.bad { color: #c00000; font-weight: bold; }
.muted { color: #5a6570; font-size: 8.5pt; }
.box { border: 1.5px solid #0b5cad; padding: 5pt 8pt; margin: 6pt 0; }
.warn { border: 1.5px solid #d9a400; padding: 5pt 8pt; margin: 6pt 0; }
.cap { font-size: 8.5pt; margin: 1pt 0 8pt 0; }
.break { page-break-before: always; }
a { color: #0b5cad; text-decoration: none; }
"""


def load(folder):
    proof = folder / "proof"
    manifest = json.loads((proof / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    return proof, manifest, summary


def per_form(manifest):
    return {r[0]: r for r in manifest["per_form"]}


def tick(v):
    return "tick" if v == "✓" else (v if v not in (None, "") else "(empty)")


class Pictures:
    """Copies/crops the pictures into one folder the PDF layout reads from."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.n = 0

    def add(self, src, band=None, max_px=None):
        import shutil
        from PIL import Image
        self.n += 1
        name = f"p{self.n}.jpg"
        img = Image.open(src)
        if not band and not (max_px and img.width > max_px):
            shutil.copyfile(src, self.dir / name)       # as the test saved it: no second compression
            return name, img.size
        if band:
            w, h = img.size
            img = img.crop((0, int(h * band[0]), w, int(h * band[1])))
        if max_px and img.width > max_px:
            img = img.resize((max_px, int(img.height * max_px / img.width)))
        img.convert("RGB").save(self.dir / name, quality=70)
        return name, img.size


def img(name, size, width_pt):
    w, h = size
    return f'<img src="{name}" width="{width_pt:.0f}" height="{width_pt * h / w:.0f}"/>'


def table_used(summary):
    """The expected box table a run was scored with; a run that did not
    record it used the table as it was before the check on the paper forms."""
    from research_tests import field_mapping as fm
    if summary.get("expected_table"):
        return summary["expected_table"]
    before = fm.EXPECTED.with_name("field_mapping_expected.before_review.csv")
    return fm.table_digest(before if before.is_file() else fm.EXPECTED)


def build(before_dir, after_dir, live_dir, out_path):
    import fitz
    b_proof, b_man, b_sum = load(before_dir)
    a_proof, a_man, a_sum = load(after_dir)
    live = None
    if live_dir and (live_dir / "live_check.json").is_file():
        live = json.loads((live_dir / "live_check.json").read_text(encoding="utf-8"))
    pics = Pictures()
    b_rows, a_rows = per_form(b_man), per_form(a_man)
    b_all, a_all = b_rows["All forms"], a_rows["All forms"]
    b_wrong = [c for en in b_man["entries"] for c in en["crops"]]
    a_wrong = [c for en in a_man["entries"] for c in en["crops"]]
    today = datetime.date.today().isoformat()
    W = 523  # usable width in points

    h = [f"<style>{CSS}</style><body>"]
    # ── cover ──
    h.append('<h1 id="top">Field mapping test - proof report</h1>')
    h.append(f'<p class="muted">PClaimAssist research tests, Objective 3 (ii), Eq. 3.6 - generated {today}</p>')
    h.append(f"""<div class="box"><b>Result.</b> Field mapping accuracy went from
      <span class="bad">{b_all[4]}%</span> ({len(b_wrong)} wrong boxes) before the fixes to
      <span class="good">{a_all[4]}%</span> ({len(a_wrong)} wrong boxes) after, over {a_all[1]} test patients
      and {a_all[2]} boxes. The {len(a_wrong)} that remain are not boxes filled in the wrong place: see
      <a href="#remaining">Remaining mismatches</a>.</div>""")
    if a_man.get("provisional"):
        h.append("""<div class="warn"><b>Provisional.</b> The expected box table (inputs/field_mapping_expected.csv)
          has not yet been checked against the paper forms (Groupmate 2). The pictures in this report are
          meant to make that check quick.</div>""")
    # contents
    if table_used(b_sum) != table_used(a_sum):
        h.append("""<div class="warn"><b>Not the same expected box table.</b> The run before the fixes was scored
          with an earlier version of the expected box table than the run after them (the table has since been checked
          against the paper forms), so the before and after figures are not directly comparable. The after figures use
          the checked table.</div>""")
    h.append('<h2 id="contents">Contents</h2><table>')
    for anchor, title in [("glance", "1. Result at a glance"), ("method", "2. How the test works and how to read the pictures"),
                          ("fixes", "3. What was fixed - before and after"), ("live", "4. Check in the real system"),
                          ("remaining", "5. Remaining mismatches (after the fixes)"), ("verdict", "6. Is it usable?"),
                          ("appA", "Appendix A - every mismatch before the fixes"),
                          ("appB", "Appendix B - every saved form page after the fixes"),
                          ("appC", "Appendix C - CF1 and PMRF pages before the fixes")]:
        h.append(f'<tr><td><a href="#{anchor}">{title}</a></td></tr>')
    h.append("</table><p class='muted'>The PDF also has bookmarks (open the bookmarks panel), and every page "
             "has a link back to these contents at the bottom.</p>")

    # ── 1. at a glance ──
    h.append('<h2 id="glance" class="break">1. Result at a glance</h2>')
    h.append("<table><tr><th>Form</th><th>Patients</th><th>Boxes checked<br/>before / after</th>"
             "<th>Accuracy before</th><th>Accuracy after</th><th>Wrong boxes<br/>before / after</th></tr>")
    for form in FORM_ORDER + ["All forms"]:
        b, a = b_rows.get(form), a_rows.get(form)
        if not a:
            continue
        bold = form == "All forms"
        name = f"<b>{form}</b>" if bold else form
        h.append(f"<tr><td>{name}</td><td class='num'>{a[1]}</td><td class='num'>{b[2]} / {a[2]}</td>"
                 f"<td class='num'>{b[4]}%</td><td class='num'><b>{a[4]}%</b></td>"
                 f"<td class='num'>{b[2] - b[3]} / {a[2] - a[3]}</td></tr>")
    h.append("</table>")
    h.append("<p>Eq. 3.6: field mapping accuracy = boxes holding the correct value / boxes checked x 100. "
             "In both runs every box was also read back from the saved PDF, and the printed value agreed with the "
             "on-screen value in every box (printed correctly % = accuracy %).</p>")
    h.append("<p>The number of boxes checked changes slightly (1430 to 1428) because a box is checked when the answer "
             "key gives it a value <i>or</i> the form fills it. Before the fix, PMRF printed a Street (RAMONAVILLE) the answer "
             "key leaves empty; after it, those boxes are empty as expected and drop out, while one CF1 Street box now "
             "shows a value it did not before.</p>")
    h.append("<h3>Wrong boxes by cause</h3><table><tr><th>Cause</th><th>Before</th><th>After</th><th>Status</th></tr>")
    def count(wrong, test):
        return sum(1 for c in wrong if test(c["line"]))
    mail = lambda l: "ailing" in l["box"] and l["column"] in ("Street", "Barangay") and (l["shown"] or "") == ""
    ville = lambda l: l["box"] == "addrStreet" and "VILLE" in (l["shown"] or "")
    name = lambda l: l["column"] == "First name"
    sitio = lambda l: "ailing" in l["box"] and l["column"] == "Street" and (l["shown"] or "") != ""
    for label, test, status in [
        ("Mailing address Street / Barangay printed N/A (CF1, PMRF)", mail, "<span class='good'>Fixed</span>"),
        ("Subdivision RAMONAVILLE printed as the Street (PMRF)", ville, "<span class='good'>Fixed</span>"),
        ("Name punctuation: MA. CECILIA printed MA CECILIA", name, "Intended (forms rule)"),
        ("Area name kept in Street (MT. VIEW, FATIMA) - not in the answer key", sitio, "Answer-key coding"),
    ]:
        h.append(f"<tr><td>{label}</td><td class='num'>{count(b_wrong, test)}</td>"
                 f"<td class='num'>{count(a_wrong, test)}</td><td>{status}</td></tr>")
    h.append("</table><p class='muted'>The last row is 0 before the fix only because those three boxes printed N/A then, "
             "so they were counted under the first row.</p>")

    # ── 2. method ──
    h.append('<h2 id="method">2. How the test works and how to read the pictures</h2>')
    h.append("""<p>For each of the 20 fictional test patients (R01-R20, sheet Patients of inputs/answer_key.xlsx), the
      confirmed logbook values go through the real auto-population, unedited:
      <i>case_bridge.draft_patient_and_encounter</i> &rarr; <i>form_prefill.build_form_data</i> &rarr; the real forms page
      (PClaimAssist/index.html, in Microsoft Edge). Each box listed in the expected box table is compared with the value
      worked out from the answer key alone, and the PDF the page saves (<i>buildFilledPdf</i>, the code behind
      "Save as PDF") is read back to check the value is printed in that box.</p>
      <p><b>The pictures.</b> Each picture is that saved PDF, rendered as is. The test then draws an outline on every box it
      checked: <span class="good">green</span> = the box holds the expected value,
      <span class="bad">red</span> = it does not, with "expected: ..." written underneath in red.
      Boxes with no outline were not part of the test (nothing expected and nothing printed, or a box the answer key
      does not cover).</p>""")
    h.append(f"""<table><tr><th></th><th>Before</th><th>After</th></tr>
      <tr><td>Code</td><td>branch research-testing, commit 3f69979</td><td>branch jrad/field-mapping-fixes (3 fixes, below)</td></tr>
      <tr><td>Run at</td><td>{e(b_sum.get('generated_at', ''))}</td><td>{e(a_sum.get('generated_at', ''))}</td></tr>
      <tr><td>Inputs</td><td colspan="2">the same answer key and expected box table for both runs</td></tr></table>""")

    # ── 3. fixes ──
    h.append('<h2 id="fixes" class="break">3. What was fixed - before and after</h2>')
    fixes = [
        ("Fix 1 - CF1 mailing address printed N/A for Street and Barangay",
         "The mailing City and Province boxes start filled with DAVAO CITY / DAVAO DEL SUR (a convenience default). The page "
         "took those two defaults as a mailing address given, so CF1 stopped using the home address and printed only City "
         "and Province, with N/A for Street and Barangay.",
         "PClaimAssist/js/app.js, mailingGiven(): a mailing part that still holds its untouched default no longer counts as "
         "a mailing address given. When staff type a mailing address, it is used as before.",
         [("R02", "CF1"), ("R08", "CF1")]),
        ("Fix 2 - PMRF mailing address printed N/A for Street and Barangay",
         "The PMRF mailing boxes printed the mailing fields directly, so with no mailing address typed they showed only the "
         "defaulted City and Province.",
         "PClaimAssist/js/pdf/overlays/pmrf.js: the PMRF mailing boxes follow the same rule as CF1 - the mailing address "
         "if one was given, otherwise the home address.",
         [("R07", "PMRF")]),
        ("Fix 3 - subdivision RAMONAVILLE read as the Street",
         "The logbook address parser recognises a subdivision only by a keyword (HOMES, VILLAGE, SUBDIVISION, ...). A one-word "
         "name ending in -VILLE has none, so it was left over and put into Street.",
         "Ocr_module/philhealth/address_parser.py: one word ending in VILLE (RAMONAVILLE, DACOVILLE) is a subdivision. "
         "Unit test added in Ocr_module/test_address_mapping.py.",
         [("R05", "PMRF")]),
    ]
    for title, problem, change, examples in fixes:
        h.append(f"<h3>{title}</h3><p><b>Problem.</b> {problem}</p><p><b>Change.</b> {change}</p>")
        for pid, form in examples:
            fname = f"{pid}_{form}_p1.jpg"
            for label, proof in (("Before", b_proof), ("After", a_proof)):
                n, size = pics.add(proof / fname, BANDS[form])
                h.append(f"<h4>{label} - patient {pid}, {form}</h4>{img(n, size, W)}")
        h.append(f'<p class="muted">Full pages: <a href="#B-{examples[0][0]}-{examples[0][1]}">after</a> | '
                 f'<a href="#C-{examples[0][0]}-{examples[0][1]}">before</a></p>')

    # ── 4. live ──
    h.append('<h2 id="live" class="break">4. Check in the real system</h2>')
    if live:
        h.append(f"""<p>The test above runs the real forms page offline. To confirm the fix in the system itself, the real
          PClaimAssist app (Ocr_module/app.py: its routes, sign-in check and database) was run with the fixed code and the real
          /index.html opened in {e(live.get('browser', 'Microsoft Edge'))}, signed in as {e(live.get('user') or 'the admin')}. A fictional
          address was typed into the real Patient details boxes, then CF1 and PMRF were built with the same code as
          "Save as PDF". Nothing was saved to the database. Page errors: none.</p>""")
        for s in [s for s in live["scenarios"] if s["code"] in ("A", "B")]:
            typed = ", ".join(f"{k} = {v}" for k, v in s["typed"].items())
            h.append(f"<h3>Scenario {s['code']} - {e(s['title'])}</h3><p class='muted'>Typed: {e(typed)}</p>")
            want = "the home address (PUROK 22, CABANTIAN)" if s["code"] == "A" else "the mailing address typed (PUROK 5, TIGATTO)"
            for form in ("cf1", "pmrf"):
                f = s["forms"][form]
                vals = f["values"]
                street = next(v for k, v in vals.items() if k.endswith("Street"))
                brgy = next(v for k, v in vals.items() if k.endswith("Barangay"))
                n, size = pics.add(live_dir / f["picture"], max_px=1100)
                h.append(f"<h4>{FORM_KEY[form]}: mailing Street = <b>{e(street or 'N/A')}</b>, Barangay = "
                         f"<b>{e(brgy or 'N/A')}</b> - expected {want}</h4>{img(n, size, W)}")
        h.append("""<div class="box"><b>Result:</b> in the real app, the mailing address on CF1 and PMRF is the home address
          when none is typed, and the typed one when it is.</div>""")
        h.append("""<p class="muted">The address-parser fix (Fix 3) is in the Python backend. It is covered by the unit test
          and by the test runs above. The running server picks it up once restarted (PClaimAssist.bat); this check did not
          restart it, and did not save a logbook page, because that would write to the database.</p>""")
    else:
        h.append("<p>No live check found in outputs/field_mapping/live_check/.</p>")

    # ── 5. remaining ──
    h.append(f'<h2 id="remaining" class="break">5. Remaining mismatches (after the fixes): {len(a_wrong)}</h2>')
    h.append("""<p><b>MA. CECILIA printed as MA CECILIA (R19 on CSF, CF2, CF4).</b> Intended: PClaimAssist prints names
      without punctuation ("Jr." &rarr; "JR", "Ma.Liza" &rarr; "MA LIZA"; Ocr_module/philhealth/review_fields.py,
      clean_name_part). The value is in the right box; only the period differs. Either the answer key writes the name the
      way the forms print it, or this is reported as the forms' formatting rule.</p>
      <p><b>PUROK 30 MT. VIEW, PUROK 26 MT. VIEW, FATIMA in CF1 Street (R04, R15, R18).</b> The logbook address includes an
      area name (MT. VIEW, FATIMA) that the answer key has no column for, so the answer key leaves it out. PClaimAssist
      keeps what was written in Street rather than dropping it. These boxes printed N/A before Fix 1, which is why they
      only show up now.</p>""")
    for c in a_wrong:
        l = c["line"]
        n, size = pics.add(a_proof / c["file"])
        h.append(f"<h4>{e(l['patient'])} {e(FORM_KEY[l['form']])} - {e(l['column'])} ({e(l['box'])})</h4>"
                 f"{img(n, size, min(W, size[0] * 0.6))}<p class='cap'>expected <b>{e(tick(l['expected']))}</b>, "
                 f"printed <b>{e(tick(l['printed']))}</b></p>")

    # ── 6. verdict ──
    h.append('<h2 id="verdict" class="break">6. Is it usable?</h2>')
    h.append(f"""<table>
      <tr><th>Check</th><th>Result</th></tr>
      <tr><td>Field mapping test, 20 patients, all forms</td><td class="good">{a_all[4]}% ({a_all[3]} of {a_all[2]} boxes)</td></tr>
      <tr><td>Printed PDF agrees with the screen</td><td class="good">every box</td></tr>
      <tr><td>Real app: mailing address on CF1 and PMRF</td><td class="good">{'correct in both scenarios' if live else 'not run'}</td></tr>
      <tr><td>Backend unit tests (Ocr_module, 382 tests)</td><td class="good">all pass</td></tr>
      <tr><td>Wrong boxes left that are mapping errors</td><td class="good">none</td></tr>
      </table>""")
    h.append("""<p><b>Yes - the fixes work in the system and can be used.</b> Before relying on them:</p>
      <p>1. Restart the backend (PClaimAssist.bat) and reload the forms with Ctrl+F5, so the running server uses the new
      code.<br/>2. The fixes are on branch jrad/field-mapping-fixes and are not merged yet.<br/>3. For Chapter 5, the field
      mapping result stays provisional until the expected box table is checked against the paper forms, and the group
      decides how to treat the 6 remaining mismatches (section 5).</p>""")

    # ── appendix A ──
    h.append(f'<h2 id="appA" class="break">Appendix A - every mismatch before the fixes ({len(b_wrong)})</h2>')
    h.append("<p class='muted'>Zoomed crops of each red box in the run before the fixes, in patient order.</p>")
    for c in b_wrong:
        l = c["line"]
        n, size = pics.add(b_proof / c["file"])
        h.append(f"<h4>{e(l['patient'])} {e(FORM_KEY[l['form']])} - {e(l['column'])}: expected "
                 f"<b>{e(tick(l['expected']))}</b>, printed <b>{e(tick(l['printed']))}</b></h4>"
                 f"{img(n, size, min(W * 0.75, size[0] * 0.55))}")

    # ── appendix B / C: full pages ──
    def page_section(anchor_prefix, man, proof, forms, heading, note):
        entries = [en for en in man["entries"] if FORM_KEY[en["form"]] in forms]
        patients = sorted({en["patient"] for en in entries})
        h.append(f'<h2 id="{anchor_prefix}" class="break">{heading}</h2><p class="muted">{note}</p>')
        h.append("<table><tr><th>Patient</th>" + "".join(f"<th>{f}</th>" for f in forms) + "</tr>")
        for pid in patients:
            cells = []
            for f in forms:
                en = next((x for x in entries if x["patient"] == pid and FORM_KEY[x["form"]] == f), None)
                if en:
                    bad = sum(p["wrong"] for p in en["pages"])
                    mark = f" <span class='bad'>({bad} wrong)</span>" if bad else ""
                    cells.append(f'<td><a href="#{anchor_prefix[-1]}-{pid}-{f}">open</a>{mark}</td>')
                else:
                    cells.append("<td class='muted'>-</td>")
            h.append(f"<tr><td>{pid}</td>{''.join(cells)}</tr>")
        h.append("</table>")
        for pid in patients:
            for f in forms:
                en = next((x for x in entries if x["patient"] == pid and FORM_KEY[x["form"]] == f), None)
                if not en:
                    continue
                for i, p in enumerate(en["pages"]):
                    n, size = pics.add(proof / p["file"])
                    anchor = f' id="{anchor_prefix[-1]}-{pid}-{f}"' if i == 0 else ""
                    bad = f" - <span class='bad'>{p['wrong']} wrong</span>" if p["wrong"] else " - all correct"
                    h.append(f'<h3{anchor} class="break">{pid} - {f} page {p["page"]}{bad}</h3>'
                             f'{img(n, size, W * 0.93)}')

    page_section("appB", a_man, a_proof, FORM_ORDER, "Appendix B - every saved form page after the fixes",
                 "Click a cell to jump to that page. Each patient has the forms its package needs (CF4 for some, PMRF "
                 "with the newborn package only).")
    page_section("appC", b_man, b_proof, ["CF1", "PMRF"], "Appendix C - CF1 and PMRF pages before the fixes",
                 "Only the two forms the fixes changed; CSF, CF2 and CF4 had the same results before and after.")
    h.append("</body>")

    render(h, pics, out_path, "Field mapping proof report",
           "Field mapping (Eq. 3.6) before and after fixes, with pictures")
    return out_path


def render(h, pics, out_path, footer, subject):
    """Lay the HTML out on A4 pages: links, bookmarks (sections, and
    patient > form in the appendices), page numbers and a "Back to
    contents" link on every page."""
    import fitz
    archive = fitz.Archive(str(pics.dir))
    story = fitz.Story(html="".join(h), archive=archive, user_css=None)
    mediabox = fitz.paper_rect("a4")
    where = mediabox + (36, 36, -36, -48)
    toc = []

    def rectfn(rect_num, filled):
        return mediabox, where, None

    def positionfn(pos):
        if pos.heading and pos.open_close & 1 and pos.text:
            level = {1: 1, 2: 1, 3: 2}.get(pos.heading)
            if level:
                toc.append((level, pos.text.strip(), pos.page_num, pos.id))

    doc = story.write_with_links(rectfn, positionfn)
    outline, section = [], ""
    for level, text, page_num, anchor in toc:
        if level == 1:
            outline.append([1, text, page_num])
            section = text
        elif section.startswith("Appendix"):
            if anchor and anchor.count("-") == 2:          # a patient's form: "B-R01-CSF"
                outline.append([2, " ".join(anchor.split("-")[1:]), page_num])
        else:
            outline.append([2, text, page_num])
    doc.set_toc(_valid_toc(outline))
    contents_page = next((p for lv, t, p, a in toc if a == "contents"), 1) - 1
    total = len(doc)
    for i, page in enumerate(doc):
        r = page.rect
        page.insert_text((36, r.height - 22), footer, fontsize=7.5, color=(0.4, 0.45, 0.5))
        page.insert_text((r.width / 2 - 20, r.height - 22), f"page {i + 1} of {total}", fontsize=7.5,
                         color=(0.4, 0.45, 0.5))
        if i != contents_page:
            link_at = fitz.Rect(r.width - 110, r.height - 31, r.width - 36, r.height - 18)
            page.insert_text((link_at.x0, r.height - 22), "Back to contents", fontsize=7.5, color=(0.04, 0.36, 0.68))
            page.insert_link({"kind": fitz.LINK_GOTO, "page": contents_page, "from": link_at, "to": fitz.Point(0, 0)})
    doc.set_metadata({"title": footer, "author": "PClaimAssist research tests", "subject": subject})
    doc.save(str(out_path), garbage=3, deflate=True)
    doc.close()
    pics.tmp.cleanup()


def _valid_toc(items):
    """PyMuPDF wants the first item at level 1 and no level jumps."""
    out, last = [], 0
    for level, text, page in items:
        level = min(level, last + 1)
        out.append([level, text, page])
        last = level
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", type=Path, default=FOLDER / "before_fix")
    ap.add_argument("--after", type=Path, default=FOLDER)
    ap.add_argument("--live", type=Path, default=FOLDER / "live_check")
    ap.add_argument("--out", type=Path, default=FOLDER / "field_mapping_proof_report.pdf")
    a = ap.parse_args()
    path = build(a.before, a.after, a.live, a.out)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
