"""Test 6 - image quality check (rule IQ-01) on good and deliberately bad scans.

    python -m research_tests.iq_check [--samples]

Inputs: inputs/iq/good/ and inputs/iq/bad/ (PDF pages or images), and
optionally inputs/iq/expected.csv (File | Expected = pass/warn | Reason,
File relative to inputs/iq/). Without the CSV a picture in good/ is expected
to pass and one in bad/ to get the warning; the reason (blurry / dark /
bright) is taken from the file name when it says so.

Each page is loaded the way the Logbook Reader loads it
(logbook_pipeline.load_pages: PDF at 2x, straightened) and checked with the
real image_quality.assess_image_quality, unchanged. Thresholds come from
config: Laplacian variance below 100 = blurry; mean brightness below 60 =
too dark, above 200 = too bright (overexposed also needs the ink washed out:
darkest 0.1% of pixels lighter than 150).
"""
import csv
from pathlib import Path

from research_tests import INPUTS, output_dir
from research_tests.common import excel, stats

TEST_KEY = "iq_check"
TITLE = "Image quality check (IQ-01)"
TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def expected_outcomes(folder):
    """{relative path: (expected, reason)}"""
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
    for word in ("blurry", "blur", "dark", "bright", "glare", "overexposed"):
        if word in name.lower():
            return {"blur": "blurry", "glare": "bright", "overexposed": "bright"}.get(word, word)
    return ""


def run(progress, samples=False):
    root = (INPUTS / "samples" if samples else INPUTS) / "iq"
    files = [p for group in ("good", "bad") for p in sorted((root / group).glob("*"))
             if (root / group).is_dir() and p.suffix.lower() in TYPES]
    if not files:
        raise FileNotFoundError(f"No pictures in {root / 'good'} or {root / 'bad'} (or use --samples).")
    import config
    import logbook_pipeline
    from image_quality import assess_image_quality
    expected = expected_outcomes(root)
    lines = []
    for n, path in enumerate(files):
        progress(0.05 + 0.9 * n / len(files), f"Checking {path.name}")
        rel = f"{path.parent.name}/{path.name}"
        want, reason = expected.get(rel, ("pass" if path.parent.name == "good" else "warn",
                                          _reason_from_name(path.name)))
        for page_number, image, _parity in logbook_pipeline.load_pages(str(path)):
            iq = assess_image_quality(image)
            fired = not iq["passed"]
            lines.append({"file": rel, "page": page_number, "group": path.parent.name, "reason": reason or "",
                          "blur": iq["blur_score"], "brightness": iq["brightness_score"], "ink": iq["ink_level"],
                          "blurry": iq["is_blurry"], "dark": iq["is_too_dark"], "bright": iq["is_too_bright"],
                          "fired": fired, "expected": want, "match": fired == (want == "warn"),
                          "warnings": " | ".join(iq["warnings"])})

    tp = sum(1 for l in lines if l["fired"] and l["expected"] == "warn")
    fn = sum(1 for l in lines if not l["fired"] and l["expected"] == "warn")
    fp = sum(1 for l in lines if l["fired"] and l["expected"] == "pass")
    tn = sum(1 for l in lines if not l["fired"] and l["expected"] == "pass")
    group_rows = []
    for label, pick in [("Good scans", lambda l: l["expected"] == "pass")] + [
            (f"Bad - {r}", (lambda r: lambda l: l["expected"] == "warn" and l["reason"] == r)(r))
            for r in sorted({l["reason"] for l in lines if l["expected"] == "warn"})] + [("All", lambda l: True)]:
        group = [l for l in lines if pick(l)]
        if not group:
            continue
        group_rows.append([label, len(group), sum(l["fired"] for l in group), sum(l["match"] for l in group),
                           stats.percent(sum(l["match"] for l in group), len(group)),
                           stats.mean(l["blur"] for l in group), stats.mean(l["brightness"] for l in group)])
    thresholds = (f"Thresholds (config.py): blur = Laplacian variance < {config.IMAGE_QUALITY_BLUR_THRESHOLD:g}; "
                  f"too dark = mean brightness < {config.IMAGE_QUALITY_BRIGHTNESS_LOW:g}; too bright = mean "
                  f"brightness > {config.IMAGE_QUALITY_BRIGHTNESS_HIGH:g} and ink washed out (darkest 0.1% lighter "
                  f"than {config.IMAGE_QUALITY_INK_MAX:g}).")
    notes = [thresholds,
             "Each page loaded as the Logbook Reader loads it (logbook_pipeline.load_pages) and checked with "
             "image_quality.assess_image_quality, unchanged.",
             "Matched = the warning fired on a picture expected to get it, or stayed quiet on one expected to pass."]
    if samples:
        notes.append("COMPUTER-DRAWN SAMPLE PICTURES (make_samples.py): blurry/dark/bright copies of drawn pages.")
    sheets = [
        {"name": "6a IQ-01 per group", "title": "Table - Image quality check results",
         "headers": ["Group", "Pages", "Warning fired", "Matched expected", "Matched %", "Mean blur variance",
                     "Mean brightness"], "rows": group_rows, "bold_last": True, "notes": notes},
        {"name": "6b IQ-01 confusion", "title": "Table - Warning vs expected outcome",
         "headers": ["", "Expected: warn", "Expected: pass"],
         "rows": [["Warning fired", tp, fp], ["No warning", fn, tn],
                  ["Detection rate (bad pages warned)", stats.ratio(tp, tp + fn), ""],
                  ["False warning rate (good pages warned)", "", stats.ratio(fp, fp + tn)]]},
    ]
    yes = lambda b: "Yes" if b else "No"
    raw = {"name": "Raw data",
           "headers": ["File", "Page", "Group", "Reason", "Blur variance", "Brightness", "Ink level", "Blurry",
                       "Too dark", "Too bright", "Warning fired", "Expected", "Matched", "Warnings"],
           "rows": [[l["file"], l["page"], l["group"], l["reason"], l["blur"], l["brightness"], l["ink"],
                     yes(l["blurry"]), yes(l["dark"]), yes(l["bright"]), yes(l["fired"]), l["expected"],
                     yes(l["match"]), l["warnings"]] for l in lines]}
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "iq_check_results.xlsx", [raw] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    return {"outputs": [path], "headline": [["Pages", len(lines)],
                                            ["Matched %", stats.percent(sum(l["match"] for l in lines), len(lines))],
                                            ["Bad pages warned", f"{tp} of {tp + fn}"],
                                            ["Good pages warned", f"{fp} of {fp + tn}"]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample pictures")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
