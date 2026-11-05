"""Test 6 - image quality check (rule IQ-01) on good and deliberately bad scans.

    python -m research_tests.iq_check [--ocr] [--samples]
    python -m research_tests.iq_check --generate     (optional: make blurry / dark / bright copies)

Main result: the REAL IQ test scans - inputs/scans/iq/ (or "handwriting_iq test/"),
the same 10 spreads as the handwriting test with some pages deliberately made
bright, dark or blurred; the expected condition of each page is in
inputs/iq_expected.csv. Each page is also compared with the same page of the
original scan. --ocr also reads them with PaddleOCR + Correction to show what
a bad page costs. Generated copies are checked only with --include-generated.

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
real image_quality.assess_logbook_page (what the Logbook Reader runs),
unchanged. Thresholds from config:
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
    from image_quality import assess_logbook_page                    # what the Logbook Reader runs
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
                iq = assess_logbook_page(image)
                fired = not iq["passed"]
                lines.append({"source": source, "file": rel, "page": page_number, "group": "bad" if is_bad else "good",
                              "reason": reason or "", "blur": iq["blur_score"], "brightness": iq["brightness_score"],
                              "ink": iq["ink_level"], "blurry": iq["is_blurry"], "dark": iq["is_too_dark"],
                              "bright": iq["is_too_bright"], "fired": fired, "expected": want,
                              "match": fired == (want == "warn"), "warnings": " | ".join(iq["warnings"])})
    return lines


# ── the real IQ test set (6a-6f): the handwriting spreads, some pages made bad ──

IQ_EXPECTED = INPUTS / "iq_expected.csv"
IQ_SCAN_FOLDERS = (INPUTS / "scans" / "iq", INPUTS / "scans" / "handwriting_iq test")
ORIGINALS = INPUTS / "scans" / "handwriting"
BAD = ("dark", "bright", "blurred")


def iq_folder():
    for folder in IQ_SCAN_FOLDERS:
        if folder.is_dir() and any(folder.glob("*.pdf")):
            return folder
    return None


def load_iq_expected(path=IQ_EXPECTED):
    """{(file, page): (label given, expected condition, evidence)}."""
    out = {}
    if path.is_file():
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                if (r.get("File") or "").strip():
                    out[(r["File"].strip(), int(r["Page"]))] = (
                        (r.get("Label given") or "").strip(), (r.get("Expected condition") or "").strip().lower(),
                        (r.get("Evidence (this page vs the same page of the original scanner scan)") or "").strip())
    return out


def why_missed_now(condition, q, config):
    """Why IQ-01 (assess_logbook_page) got a page wrong."""
    if condition == "dark":
        return (f"brightness {q['brightness_score']:.1f} is not below {config.IMAGE_QUALITY_DIM_BELOW:g}")
    if condition == "bright":
        return (f"{q['white_share'] * 100:.0f}% pure white (needs {config.IMAGE_QUALITY_WASHED_WHITE_SHARE * 100:.0f}%) "
                f"and darkest writing {q['faint_ink']:.0f} (needs {config.IMAGE_QUALITY_WASHED_INK_MIN:g} or lighter)")
    if condition == "blurred":
        return f"page sharpness {q['page_sharpness']:.1f} is not below {config.IMAGE_QUALITY_SHARPNESS_MIN:g}"
    return "warned on a normal page: " + "; ".join(w.split(" (")[0] for w in q["warnings"])


def real_iq_pages(progress, out):
    """Every page of the real IQ test scans, checked with assess_logbook_page
    (the check the Logbook Reader runs), beside the same page of the
    original scan; pictures of the original, the IQ page and - when the page
    is flagged - the evened-out copy the OCR reads."""
    import cv2
    import logbook_pipeline
    from image_quality import assess_logbook_page, enhance_for_ocr, needs_enhancing
    import config
    folder = iq_folder()
    if folder is None:
        return [], None
    expected = load_iq_expected()
    pics = out / "proof"
    pics.mkdir(parents=True, exist_ok=True)

    def save(stem, tag, img):
        small = cv2.resize(img, (560, int(img.shape[0] * 560 / img.shape[1])), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(pics / f"{stem}_{tag}.jpg"), small, [cv2.IMWRITE_JPEG_QUALITY, 70])
        h, w = img.shape[:2]
        zoom = img[int(h * 0.30):int(h * 0.30) + int(h * 0.16), int(w * 0.04):int(w * 0.04) + int(w * 0.55)]
        cv2.imwrite(str(pics / f"{stem}_{tag}_zoom.jpg"), zoom, [cv2.IMWRITE_JPEG_QUALITY, 75])

    lines = []
    files = sorted(folder.glob("*.pdf"))
    for n, path in enumerate(files):
        progress(0.05 + 0.3 * n / len(files), f"IQ-01 on {path.name}")
        original = ORIGINALS / path.name.replace("_iq.pdf", ".pdf")
        orig_pages = {p: img for p, img, _ in logbook_pipeline.load_pages(str(original))} if original.is_file() else {}
        for page, image, _parity in logbook_pipeline.load_pages(str(path)):
            now = assess_logbook_page(image)
            given, cond, evidence = expected.get((path.name, page), ("", "", ""))
            want_warn = cond in BAD
            fired = not now["passed"]
            o = assess_logbook_page(orig_pages[page]) if page in orig_pages else None
            stem = f"{path.stem}_p{page}"
            save(stem, "iq", image)
            if page in orig_pages:
                save(stem, "orig", orig_pages[page])
            enhanced = config.IMAGE_QUALITY_ENHANCE and needs_enhancing(now)
            if enhanced:
                save(stem, "enh", enhance_for_ocr(image, now))
            lines.append({
                "source": "REAL scan (IQ test set)", "file": path.name, "page": page, "label_given": given,
                "expected": cond or "(no label)", "evidence": evidence, "size": f"{image.shape[1]} x {image.shape[0]} px",
                "blur": now["blur_score"], "brightness": now["brightness_score"], "ink": now["ink_level"],
                "blurry": now["is_blurry"], "dark": now["is_too_dark"], "bright": now["is_too_bright"],
                "sharpness": now["page_sharpness"], "white_share": now["white_share"], "faint_ink": now["faint_ink"],
                "dim": now["is_dim"], "soft": now["is_soft"], "washed": now["is_washed_out"],
                "fired": fired, "should_warn": want_warn, "match": fired == want_warn,
                "why": "" if fired == want_warn else why_missed_now(cond, now, config),
                "enhanced": enhanced, "warnings": " | ".join(now["warnings"]),
                "orig_blur": o["blur_score"] if o else None, "orig_brightness": o["brightness_score"] if o else None,
                "orig_ink": o["ink_level"] if o else None, "orig_sharpness": o["page_sharpness"] if o else None,
                "orig_fired": (not o["passed"]) if o else None, "picture": stem})
    return lines, folder


def check_other_sets(progress):
    """IQ-01 on the pages not made for this test:
    the 40 original handwriting pages (scanner, phone) - which should pass -
    and the generated bad copies, if any (not used to set the thresholds)."""
    import cv2
    import logbook_pipeline
    from image_quality import assess_logbook_page
    rows = []
    sets = [("Original handwriting pages - scanner", INPUTS / "scans" / "handwriting", "pass"),
            ("Original handwriting pages - phone", INPUTS / "scans" / "handwriting_phone", "pass")]
    for label, folder, want in sets:
        pages = [img for pdf in sorted(folder.glob("*.pdf")) for _, img, _ in logbook_pipeline.load_pages(str(pdf))]
        if pages:
            progress(0.37, f"Checking {label.lower()}")
            rows.append([label, want, len(pages), sum(not assess_logbook_page(p)["passed"] for p in pages)])
    gen = INPUTS / "iq" / "generated" / "bad"
    if gen.is_dir():
        for kind in ("dark", "bright", "blurry"):
            imgs = [cv2.imread(str(f)) for f in sorted(gen.glob(f"*_{kind}.jpg"))]
            if imgs:
                rows.append([f"GENERATED {kind} copies (iq_check --generate)", "warn", len(imgs),
                             sum(not assess_logbook_page(i)["passed"] for i in imgs)])
    return rows


def iq_ocr(progress, lines, out):
    """Optional (--ocr): PaddleOCR + Correction on the IQ test scans, read
    the way the Logbook Reader reads them (a flagged page evened out first),
    scored per page against the answer key beside the same page of the
    original scanner scan - what a bad page still costs. Tesseract is not
    run. Readings are cached, and re-read when the scan, the evening-out code
    or its thresholds change."""
    from research_tests import handwriting as hw
    from research_tests.common import answer_key
    import hashlib
    import inspect
    import config
    import image_quality
    import ocr_compare
    folder = iq_folder()
    key = answer_key.handwriting(INPUTS / "answer_key.xlsx")
    writers = {w["writer"]: w for w in answer_key.writers(INPUTS / "writers.csv")}
    originals = json.loads((OUTPUTS / "handwriting" / "runs.json").read_text(encoding="utf-8"))
    cache_path = out / "runs_iq_enhanced.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    code = hashlib.sha256((inspect.getsource(image_quality.enhance_for_ocr)
                           + inspect.getsource(image_quality.needs_enhancing)
                           + inspect.getsource(image_quality.assess_logbook_page) + repr([
                               config.IMAGE_QUALITY_DIM_BELOW, config.IMAGE_QUALITY_SHARPNESS_MIN,
                               config.IMAGE_QUALITY_WASHED_WHITE_SHARE,
                               config.IMAGE_QUALITY_WASHED_INK_MIN])).encode()).hexdigest()[:16]
    reader = None

    def skip_tesseract(*_a, **_k):
        raise RuntimeError("not run in the IQ test (PaddleOCR + Correction only)")

    rows = []
    files = sorted(folder.glob("*.pdf"))
    for n, path in enumerate(files):
        writer = path.name.split("_")[0].upper()
        digest = hw._sha256(path) + "|" + code
        hit = cache.get(path.name)
        run = ocr_compare.load_run(hit["run_id"]) if hit and hit.get("sha256") == digest else None
        if run is None:
            if reader is None:
                progress(0.4, "Loading PaddleOCR and the correction model")
                reader = hw.Reader()
                reader.kwargs["tesseract_fn"] = skip_tesseract
                reader.kwargs["tesseract_corrector"] = None
            progress(0.4 + 0.55 * n / len(files), f"Reading {path.name} (PaddleOCR + Correction)")
            run = reader.read(path, lambda f, m: None)
            cache[path.name] = {"sha256": digest, "run_id": run["run_id"]}
            cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        orig_name = path.name.replace("_iq.pdf", ".pdf")
        orig_run = ocr_compare.load_run(originals[orig_name]["run_id"]) if orig_name in originals else None
        w = dict(writers.get(writer, {"writer": writer, "style": "", "set": "main"}), scan=path.name)
        mine = [k for k in key if k["writer"] == writer]
        orig_cells = hw.score_cells(dict(w, scan=orig_name), mine, orig_run)
        iq_cells = hw.score_cells(w, mine, run)
        for page in (1, 2):
            line = next((l for l in lines if l["file"] == path.name and l["page"] == page), None)
            if not line:
                continue

            def score(cs):
                s = [c for c in cs if c["page"] == page and c["detected"] and not c["blank"]]
                have = [c for c in s if "paddle_corrected_exact" in c]
                return (stats.percent(sum(c["paddle_corrected_exact"] for c in have), len(have)),
                        stats.mean(c["paddle_corrected_accuracy"] for c in have),
                        sum(1 for c in cs if c["page"] == page and not c["detected"]))
            o, a = score(orig_cells), score(iq_cells)
            rows.append([line["file"], page, line["expected"], "Yes" if line["fired"] else "No",
                         "Yes" if line["enhanced"] else "No", o[1], a[1],
                         None if o[1] is None or a[1] is None else round(a[1] - o[1], 2), o[0], a[0], o[2], a[2]])
    return rows


def run(progress, samples=False, generate_copies=False, include_generated=False, ocr=False):
    root = (INPUTS / "samples" if samples else INPUTS)
    if generate_copies:
        return generate(progress, root)
    iq_root = root / "iq"
    import config
    out = output_dir(TEST_KEY)
    import shutil
    shutil.rmtree(out / "proof", ignore_errors=True)
    real, folder = ([], None) if samples else real_iq_pages(progress, out)
    other_rows = [] if samples else check_other_sets(progress)
    if samples:
        lines = page_lines(iq_root, "sample", ("good", "bad"))
    else:
        lines = page_lines(iq_root, "real", ("good", "bad"))
        if include_generated:
            lines += page_lines(iq_root, "generated", ("generated/good", "generated/bad"))
    ocr_rows = iq_ocr(progress, real, out) if (ocr and real) else []

    rule = (f"IQ-01 = image_quality.assess_logbook_page, the check the Logbook Reader runs on every page: too dark = "
            f"brightness < {config.IMAGE_QUALITY_BRIGHTNESS_LOW:g}; dim = brightness < "
            f"{config.IMAGE_QUALITY_DIM_BELOW:g}; too bright = brightness > {config.IMAGE_QUALITY_BRIGHTNESS_HIGH:g} AND "
            f"darkest 0.1% lighter than {config.IMAGE_QUALITY_INK_MAX:g}; washed out = at least "
            f"{config.IMAGE_QUALITY_WASHED_WHITE_SHARE * 100:g}% of the page pure white AND darkest 0.1% at "
            f"{config.IMAGE_QUALITY_WASHED_INK_MIN:g} or lighter; blurry = sharpness < "
            f"{config.IMAGE_QUALITY_BLUR_THRESHOLD:g}; soft focus = sharpness at 1000 px wide < "
            f"{config.IMAGE_QUALITY_SHARPNESS_MIN:g}. A dim, washed-out or too-dark page is evened out before it is "
            f"read (enhance_for_ocr: {'on' if config.IMAGE_QUALITY_ENHANCE else 'OFF'}).")
    method = "Each page loaded as the Logbook Reader loads it (logbook_pipeline.load_pages: PDF at 2x, straightened)."
    yes = lambda b: "Yes" if b else "No"
    sheets = []
    if real:
        tp = sum(1 for l in real if l["fired"] and l["should_warn"])
        fn = sum(1 for l in real if not l["fired"] and l["should_warn"])
        fp = sum(1 for l in real if l["fired"] and not l["should_warn"])
        tn = sum(1 for l in real if not l["fired"] and not l["should_warn"])
        src = (f"REAL scans: {folder.relative_to(INPUTS.parent).as_posix()}/ - the 10 handwriting spreads, some "
               "pages deliberately made bright, dark or blurred (not generated). Expected conditions: "
               "inputs/iq_expected.csv.")
        flags = lambda l: ", ".join(k for k, f in (("too dark", l["dark"]), ("too bright", l["bright"]),
                                                    ("blurry", l["blurry"]), ("dim", l["dim"]),
                                                    ("soft focus", l["soft"]), ("washed out", l["washed"])) if f) or "-"
        per_page = [[l["file"], l["page"], l["label_given"], l["expected"], l["brightness"], l["sharpness"],
                     round(l["white_share"] * 100, 1), l["ink"], flags(l), yes(l["fired"]), yes(l["match"]),
                     yes(l["enhanced"]), l["why"]] for l in real]
        conds = ["normal"] + [c for c in BAD if any(l["expected"] == c for l in real)]
        per_cond = []
        for c in conds:
            g = [l for l in real if l["expected"] == c]
            per_cond.append([c, len(g), sum(l["fired"] for l in g), sum(l["match"] for l in g),
                             stats.percent(sum(l["match"] for l in g), len(g)),
                             stats.value_range([l["brightness"] for l in g]),
                             stats.value_range([l["sharpness"] for l in g]),
                             stats.value_range([round(l["white_share"] * 100, 1) for l in g]),
                             stats.value_range([l["ink"] for l in g])])
        misses = [[l["file"], l["page"], l["expected"], "missed" if l["should_warn"] else "false warning", l["why"]]
                  for l in real if not l["match"]]
        corrected = [[l["file"], l["page"], l["label_given"], l["expected"], l["evidence"]]
                     for l in real if l["label_given"] and l["label_given"] != l["expected"]]
        sheets += [
            {"name": "6a IQ-01 real pages", "title": "Table - IQ-01 on every page of the real IQ test scans",
             "headers": ["File", "Page", "Label given", "Expected condition", "Brightness", "Sharpness (1000 px)",
                         "Pure white %", "Darkest writing (0.1%)", "Flags", "Warning fired", "Matched expected",
                         "Evened out before reading", "Why not"], "rows": per_page, "notes": [src, rule, method]},
            {"name": "6b IQ-01 confusion", "title": "Table - Warning vs expected condition (real IQ test scans)",
             "headers": ["", "Expected: warn (bright/dark/blurred)", "Expected: pass (normal)"],
             "rows": [["Warning fired", tp, fp], ["No warning", fn, tn],
                      ["Detection rate (bad pages warned)", stats.ratio(tp, tp + fn), ""],
                      ["False warning rate (normal pages warned)", "", stats.ratio(fp, fp + tn)]],
             "notes": [src, rule]},
            {"name": "6c Per condition", "title": "Table - IQ-01 per expected condition",
             "headers": ["Expected condition", "Pages", "Warning fired", "Matched", "Matched %",
                         "Brightness (min - max)", "Sharpness 1000 px (min - max)", "Pure white % (min - max)",
                         "Darkest writing (min - max)"], "rows": per_cond, "notes": [rule]},
            {"name": "6d Misses and false warnings", "title": "Table - Every page IQ-01 gets wrong, and why",
             "headers": ["File", "Page", "Expected condition", "Error", "Why"], "rows": misses,
             "notes": ["None." if not misses else f"{len(misses)} pages."]},
            {"name": "6e Labels corrected", "title": "Table - Labels changed after comparing with the original scans",
             "headers": ["File", "Page", "Label given", "Used", "Evidence"], "rows": corrected,
             "notes": ["Each IQ page was compared with the same page of the original scanner scan "
                       "(scans/handwriting/): an untouched page changes by about -1 in brightness and +3 to +10 in ink "
                       "level (re-saving)."]},
        ]
    if other_rows:
        sheets.append({"name": "6f Other page sets", "title": "Table - IQ-01 on pages not made for this test",
                       "headers": ["Pages", "Should", "Pages checked", "Warning fired"], "rows": other_rows,
                       "notes": ["The 40 original handwriting pages should pass. The GENERATED copies (iq_check "
                                 "--generate) are computer-made dark/bright/blurry pages that were not used to choose "
                                 "the thresholds - an independent check that bad pages are caught."]})
    if ocr_rows:
        def mean_of(rows_, i):
            vals = [r[i] for r in rows_ if r[i] is not None]
            return stats.mean(vals) if vals else None
        summary_rows = []
        for c in ["normal"] + list(BAD):
            g = [r for r in ocr_rows if r[2] == c]
            if g:
                summary_rows.append([c, len(g), sum(r[4] == "Yes" for r in g), mean_of(g, 5), mean_of(g, 6),
                                     mean_of(g, 7), mean_of(g, 8), mean_of(g, 9)])
        sheets.append({"name": "6g OCR per page", "title": "Table - PaddleOCR + Correction on each IQ page vs the same "
                                                           "page of the original scan",
                       "headers": ["File", "Page", "Expected condition", "Warning fired", "Evened out",
                                   "Characters % original", "Characters % IQ page", "Change (pp)",
                                   "Exact % original", "Exact % IQ page", "Cells not found original",
                                   "Cells not found IQ page"], "rows": ocr_rows,
                       "notes": ["PaddleOCR + Correction (the value the system pre-fills), scored against the answer "
                                 "key exactly as in the handwriting test; Tesseract not run. The IQ page is read the "
                                 "way the Logbook Reader reads it (a flagged page evened out first). Original = the "
                                 "handwriting test's run of the same scanner scan."]})
        sheets.append({"name": "6h OCR per condition", "title": "Table - OCR by page condition (page means)",
                       "headers": ["Expected condition", "Pages", "Evened out", "Characters % original",
                                   "Characters % IQ page", "Change (pp)", "Exact % original", "Exact % IQ page"],
                       "rows": summary_rows})
    if lines:
        tp = sum(1 for l in lines if l["fired"] and l["expected"] == "warn")
        fn = sum(1 for l in lines if not l["fired"] and l["expected"] == "warn")
        fp = sum(1 for l in lines if l["fired"] and l["expected"] == "pass")
        tn = sum(1 for l in lines if not l["fired"] and l["expected"] == "pass")
        sheets.append({"name": "6i Other pictures", "title": "Table - IQ-01 on iq/good, iq/bad"
                                                            + (" and the GENERATED copies" if include_generated else ""),
                       "headers": ["", "Expected: warn", "Expected: pass"],
                       "rows": [["Warning fired", tp, fp], ["No warning", fn, tn]]})
    if not sheets:
        raise FileNotFoundError("No IQ test scans (inputs/scans/iq/), no pictures in inputs/iq/, and no other pages.")
    raw_rows = [[l["source"], l["file"], l["page"], l["label_given"], l["expected"], l["size"], l["blur"],
                 l["brightness"], l["ink"], l["sharpness"], l["white_share"], yes(l["blurry"]), yes(l["dark"]),
                 yes(l["bright"]), yes(l["dim"]), yes(l["soft"]), yes(l["washed"]), yes(l["fired"]), yes(l["match"]),
                 yes(l["enhanced"]), l["why"], l["orig_blur"], l["orig_brightness"], l["orig_ink"], l["orig_sharpness"],
                 "" if l["orig_fired"] is None else yes(l["orig_fired"]), l["warnings"]] for l in real]
    raw = {"name": "Raw data",
           "headers": ["Source", "File", "Page", "Label given", "Expected", "Page size", "Blur variance", "Brightness",
                       "Ink level (0.1%)", "Sharpness (1000 px)", "Pure white share", "Blurry", "Too dark",
                       "Too bright", "Dim", "Soft focus", "Washed out", "Warning fired", "Matched", "Evened out",
                       "Why not", "Original: blur variance", "Original: brightness", "Original: ink level",
                       "Original: sharpness (1000 px)", "Original: warning fired", "Warnings"],
           "rows": raw_rows}
    path = excel.write_workbook(out / "iq_check_results.xlsx", [raw] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples, "real_iq_pages": len(real),
                                                      "include_generated": include_generated, "ocr": bool(ocr_rows)})
    if real:
        (out / "proof" / "manifest.json").write_text(json.dumps(
            {"pages": real, "ocr": ocr_rows, "other": other_rows, "folder": str(folder)}, indent=1, default=str),
            encoding="utf-8")
    progress(1.0, "Done")
    head = [["Real IQ test pages", len(real)]]
    if real:
        head += [["Bad pages warned", f"{sum(l['fired'] and l['should_warn'] for l in real)} of "
                                      f"{sum(l['should_warn'] for l in real)}"],
                 ["Normal pages warned", f"{sum(l['fired'] and not l['should_warn'] for l in real)} of "
                                         f"{sum(not l['should_warn'] for l in real)}"]]
    return {"outputs": [path], "headline": head}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample pictures")
    parser.add_argument("--generate", dest="generate_copies", action="store_true",
                        help="make blurry / dark / bright copies of the real scanner pages in iq/generated/")
    parser.add_argument("--include-generated", action="store_true",
                        help="also check the generated copies (not part of the real-scan result)")
    parser.add_argument("--ocr", action="store_true",
                        help="also read the IQ test scans with PaddleOCR + Correction (about 1 minute a scan; cached)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
