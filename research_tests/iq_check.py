"""Test 6 - image quality check (rule IQ-01) on good and deliberately bad scans.

    python -m research_tests.iq_check [--samples]
    python -m research_tests.iq_check --generate     (make blurry / dark / bright copies first)

Inputs (inputs/, or inputs/samples/ with --samples):
  iq/good/, iq/bad/     REAL scans - good ones, and deliberately bad ones
                        (blurry, too dark, glare, tilted); PDF pages or images
  iq/expected.csv       optional: File | Expected (pass/warn) | Reason, File
                        relative to iq/ (e.g. bad/blurry_01.jpg)
  iq/generated/         GENERATED with --generate: the real scanner pages of
                        the handwriting set (good) and blurry, dark and bright
                        copies of them (bad) - git-ignored, rebuilt any time
Without expected.csv a page in good/ should pass and one in bad/ should get
the warning; the reason is taken from the file name (blurry/dark/bright...).

Each page is loaded the way the Logbook Reader loads it
(logbook_pipeline.load_pages: PDF at 2x, straightened) and checked with the
real image_quality.assess_image_quality, unchanged. Thresholds from config:
blur variance < 100; brightness < 60 or > 200 (with the ink washed out).

Every result says its Source: real, generated, or sample. 6c adds IQ-01 on
the 40 real logbook pages of the handwriting test (scanner + phone).
"""
import csv
import json

from research_tests import INPUTS, OUTPUTS, output_dir
from research_tests.common import excel, stats

TEST_KEY = "iq_check"
TITLE = "Image quality check (IQ-01)"
TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def expected_outcomes(folder):
    out = {}
    path = folder / "expected.csv"
    if path.is_file():
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if (r.get("File") or "").strip():
                    out[r["File"].strip().replace("\\", "/")] = ((r.get("Expected") or "").strip().lower(),
                                                                 (r.get("Reason") or "").strip())
    return out


def _reason_from_name(name):
    for word in ("blurry", "blur", "dark", "bright", "glare", "overexposed", "tilt"):
        if word in name.lower():
            return {"blur": "blurry", "glare": "bright", "overexposed": "bright", "tilt": "tilted"}.get(word, word)
    return ""


def generate(progress, root):
    """Blurry, dark and bright copies of the real scanner pages (as the
    pipeline loads them, at half size) -> iq/generated/{good,bad}/."""
    import cv2
    import numpy as np
    import logbook_pipeline
    from research_tests.common import answer_key
    writers = [w for w in answer_key.writers(root / "writers.csv") if w["set"] == "main"]
    good, bad = root / "iq" / "generated" / "good", root / "iq" / "generated" / "bad"
    good.mkdir(parents=True, exist_ok=True)
    bad.mkdir(parents=True, exist_ok=True)
    made = 0
    for n, w in enumerate(writers):
        progress(n / len(writers), f"Generating from {w['scan']}")
        for page, image, _parity in logbook_pipeline.load_pages(str(root / "scans" / "handwriting" / w["scan"])):
            small = cv2.resize(image, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            stem = f"{w['writer']}_p{page}"
            cv2.imwrite(str(good / f"{stem}.jpg"), small, [cv2.IMWRITE_JPEG_QUALITY, 92])
            variants = {
                "blurry": cv2.GaussianBlur(small, (0, 0), 6),
                "dark": np.clip(small.astype(np.float32) * 0.22, 0, 255).astype(np.uint8),
                "bright": np.clip(small.astype(np.float32) * 0.25 + 215, 0, 255).astype(np.uint8),
            }
            for kind, img in variants.items():
                cv2.imwrite(str(bad / f"{stem}_{kind}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            made += 4
    progress(1.0, "Done")
    return {"outputs": [good.parent], "headline": [["Pictures generated", made],
                                                   ["From", f"{len(writers)} real scanner scans"]]}


def page_lines(root, source_label, folders):
    import logbook_pipeline
    from image_quality import assess_image_quality
    expected = expected_outcomes(root)
    lines = []
    for group in folders:
        folder = root / group
        files = sorted(p for p in folder.glob("*") if p.suffix.lower() in TYPES) if folder.is_dir() else []
        for path in files:
            rel = f"{group}/{path.name}"
            is_bad = group.endswith("bad")
            want, reason = expected.get(rel, ("warn" if is_bad else "pass", _reason_from_name(path.name)))
            source = source_label if not (source_label == "generated" and not is_bad) else "real (scanner page)"
            for page_number, image, _parity in logbook_pipeline.load_pages(str(path)):
                iq = assess_image_quality(image)
                fired = not iq["passed"]
                lines.append({"source": source, "file": rel, "page": page_number, "group": "bad" if is_bad else "good",
                              "reason": reason or "", "blur": iq["blur_score"], "brightness": iq["brightness_score"],
                              "ink": iq["ink_level"], "blurry": iq["is_blurry"], "dark": iq["is_too_dark"],
                              "bright": iq["is_too_bright"], "fired": fired, "expected": want,
                              "match": fired == (want == "warn"), "warnings": " | ".join(iq["warnings"])})
    return lines


def handwriting_pages():
    """6c: IQ-01 on the real logbook pages of the handwriting test (its 1d sheet)."""
    path = OUTPUTS / "handwriting" / "summary.json"
    if not path.is_file():
        return [], "The handwriting test has not been run yet."
    record = json.loads(path.read_text(encoding="utf-8"))
    sheet = next((s for s in record["sheets"] if s["name"] == "1d Detection and IQ"), None)
    if not sheet:
        return [], "The handwriting results have no 1d sheet (re-run it)."
    h = sheet["headers"]
    i = {k: h.index(k) for k in ("Scan Method", "Blur variance", "Brightness", "IQ-01")}
    rows = []
    for method in dict.fromkeys(r[i["Scan Method"]] for r in sheet["rows"]):
        group = [r for r in sheet["rows"] if r[i["Scan Method"]] == method]
        blur = [r[i["Blur variance"]] for r in group]
        bright = [r[i["Brightness"]] for r in group]
        rows.append([method, len(group), sum(1 for r in group if r[i["IQ-01"]] == "pass"),
                     sum(1 for r in group if r[i["IQ-01"]] != "pass"), stats.value_range(blur),
                     stats.value_range(bright)])
    return rows, f"From outputs/handwriting (run {record['generated_at']})."


def run(progress, samples=False, generate_copies=False):
    root = (INPUTS / "samples" if samples else INPUTS)
    if generate_copies:
        return generate(progress, root)
    iq_root = root / "iq"
    import config
    progress(0.1, "Checking the pages")
    if samples:
        lines = page_lines(iq_root, "sample", ("good", "bad"))
    else:
        lines = page_lines(iq_root, "real", ("good", "bad")) + page_lines(iq_root, "generated",
                                                                          ("generated/good", "generated/bad"))
    real_bad = sum(1 for l in lines if l["source"] == "real" and l["group"] == "bad")
    gen_bad = sum(1 for l in lines if l["source"] == "generated")
    hw_rows, hw_note = handwriting_pages() if not samples else ([], "")

    thresholds = (f"Thresholds (config.py): blur = Laplacian variance < {config.IMAGE_QUALITY_BLUR_THRESHOLD:g}; "
                  f"too dark = mean brightness < {config.IMAGE_QUALITY_BRIGHTNESS_LOW:g}; too bright = mean "
                  f"brightness > {config.IMAGE_QUALITY_BRIGHTNESS_HIGH:g} and ink washed out (darkest 0.1% lighter "
                  f"than {config.IMAGE_QUALITY_INK_MAX:g}).")
    caught = ("Deliberately bad pages: " + (f"{real_bad} real" if real_bad else "no real ones") +
              (f", {gen_bad} generated (blurry/dark/bright copies of real scanner pages)" if gen_bad else "") +
              ("." if real_bad else " - the warning's ability to catch bad pages was tested only on "
               + ("generated copies." if gen_bad else "computer-drawn samples (make_samples.py).")))
    notes = [thresholds, caught,
             "Each page loaded as the Logbook Reader loads it (logbook_pipeline.load_pages) and checked with "
             "image_quality.assess_image_quality, unchanged.",
             "Matched = the warning fired on a page expected to get it, or stayed quiet on one expected to pass."]
    if samples:
        notes.append("COMPUTER-DRAWN SAMPLE PICTURES (make_samples.py).")
    sheets = []
    if lines:
        group_rows = []
        for source in dict.fromkeys(l["source"] for l in lines):
            mine = [l for l in lines if l["source"] == source]
            labels = [("Good pages", lambda l: l["expected"] == "pass")] + [
                (f"Bad - {r or 'unspecified'}", (lambda r: lambda l: l["expected"] == "warn" and l["reason"] == r)(r))
                for r in sorted({l["reason"] for l in mine if l["expected"] == "warn"})]
            for label, pick in labels:
                group = [l for l in mine if pick(l)]
                if group:
                    group_rows.append([source, label, len(group), sum(l["fired"] for l in group),
                                       sum(l["match"] for l in group),
                                       stats.percent(sum(l["match"] for l in group), len(group)),
                                       stats.mean(l["blur"] for l in group), stats.mean(l["brightness"] for l in group)])
        group_rows.append(["All", "All pages", len(lines), sum(l["fired"] for l in lines),
                           sum(l["match"] for l in lines), stats.percent(sum(l["match"] for l in lines), len(lines)),
                           stats.mean(l["blur"] for l in lines), stats.mean(l["brightness"] for l in lines)])
        tp = sum(1 for l in lines if l["fired"] and l["expected"] == "warn")
        fn = sum(1 for l in lines if not l["fired"] and l["expected"] == "warn")
        fp = sum(1 for l in lines if l["fired"] and l["expected"] == "pass")
        tn = sum(1 for l in lines if not l["fired"] and l["expected"] == "pass")
        sheets += [
            {"name": "6a IQ-01 per group", "title": "Table - Image quality check results",
             "headers": ["Source", "Group", "Pages", "Warning fired", "Matched expected", "Matched %",
                         "Mean blur variance", "Mean brightness"], "rows": group_rows, "bold_last": True,
             "notes": notes},
            {"name": "6b IQ-01 confusion", "title": "Table - Warning vs expected outcome",
             "headers": ["", "Expected: warn", "Expected: pass"],
             "rows": [["Warning fired", tp, fp], ["No warning", fn, tn],
                      ["Detection rate (bad pages warned)", stats.ratio(tp, tp + fn), ""],
                      ["False warning rate (good pages warned)", "", stats.ratio(fp, fp + tn)]],
             "notes": [caught]},
        ]
    if hw_rows:
        sheets.append({"name": "6c IQ-01 real logbook pages", "title": "Table - IQ-01 on the real handwriting pages",
                       "headers": ["Scan Method", "Pages", "Passed", "Warned", "Blur variance (min - max)",
                                   "Brightness (min - max)"], "rows": hw_rows,
                       "notes": [hw_note, "These are the test set's real logbook pages; none was made bad on purpose. "
                                 + caught]})
    if not sheets:
        raise FileNotFoundError(f"No pictures in {iq_root}/good, bad or generated, and no handwriting results "
                                "(run with --generate, or add real scans).")
    yes = lambda b: "Yes" if b else "No"
    raw = {"name": "Raw data",
           "headers": ["Source", "File", "Page", "Group", "Reason", "Blur variance", "Brightness", "Ink level",
                       "Blurry", "Too dark", "Too bright", "Warning fired", "Expected", "Matched", "Warnings"],
           "rows": [[l["source"], l["file"], l["page"], l["group"], l["reason"], l["blur"], l["brightness"], l["ink"],
                     yes(l["blurry"]), yes(l["dark"]), yes(l["bright"]), yes(l["fired"]), l["expected"],
                     yes(l["match"]), l["warnings"]] for l in lines]}
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "iq_check_results.xlsx", [raw] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples,
                                                      "bad_pages": {"real": real_bad, "generated": gen_bad}})
    progress(1.0, "Done")
    return {"outputs": [path], "headline": [["Pages checked", len(lines)], ["Real bad pages", real_bad],
                                            ["Generated bad pages", gen_bad],
                                            ["Matched %", stats.percent(sum(l["match"] for l in lines), len(lines))]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample pictures")
    parser.add_argument("--generate", dest="generate_copies", action="store_true",
                        help="make blurry / dark / bright copies of the real scanner pages in iq/generated/")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
