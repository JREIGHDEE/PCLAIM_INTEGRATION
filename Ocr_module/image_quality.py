"""Lightweight image-quality assessment (blur / brightness) for uploaded
OCR scans.

Pure OpenCV/numpy, no OCR engine involved - runs before OCR so a scan that's
too blurry or too dark/bright to OCR reliably can be flagged to the
reviewer, instead of producing low-quality OCR output with no explanation
for why. Advisory only: nothing here blocks OCR from running, and nothing
here is new *preprocessing* for OCR itself - ocr_engine.py's pipeline is
unchanged (see its own docstring and benchmarks/README.md's "Other fairness
properties" section, which documents that no preprocessing happens there).
This module is purely a diagnostic read of the image, attached to the /ocr
response alongside the OCR tokens - see routes/ocr_routes.py.

Thresholds (config.py, env-overridable):
- Blur: variance of the Laplacian - a standard, widely used sharpness
  proxy. IMAGE_QUALITY_BLUR_THRESHOLD (default 100.0) is the commonly cited
  rule-of-thumb cutoff for "noticeably blurry" on ordinary document/photo
  content. There is no universal correct value - this is a starting
  default, meant to be tuned against this project's own scanned logbooks
  once enough real samples have been reviewed.
- Brightness: mean grayscale pixel intensity (0-255).
  IMAGE_QUALITY_BRIGHTNESS_LOW/_HIGH (defaults 60.0/200.0) flag "too dark"
  and "too bright/overexposed" respectively - same caveat as blur above.
  Overexposed additionally requires the ink to be washed out (darkest 0.1%
  of pixels lighter than IMAGE_QUALITY_INK_MAX, default 150), since a clean
  scan of white paper has a high mean brightness on its own.
"""
import cv2
import numpy as np

import config

# Thesis validation-rule ID for this check (the single "IQ" rule).
IQ_RULE_ID = "IQ-01"


def compute_blur_score(image):
    """Variance of the Laplacian of `image` (BGR or single-channel).
    Higher = sharper; lower = blurrier. Returns 0.0 for an empty/invalid
    image."""
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness_score(image):
    """Mean grayscale pixel intensity of `image`, 0-255. Returns 0.0 for an
    empty/invalid image."""
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return float(np.mean(gray))


def compute_ink_level(image):
    """Gray level (0-255) of the darkest 0.1% of pixels in `image` - roughly
    how dark the ink is. Low on a normal scan; high when text is washed out.
    0.1% rather than 1% so a sparsely filled page (ink covering well under
    1% of it) still measures its ink, not its paper. Returns 255.0 for an
    empty/invalid image."""
    if image is None or image.size == 0:
        return 255.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return float(np.percentile(gray, 0.1))


def assess_image_quality(image):
    """Returns a plain dict describing `image`'s blur/brightness and any
    resulting warnings. Never raises, never blocks OCR - purely advisory
    metadata for the caller (see module docstring).

    {
      "rule_id": "IQ-01", "passed": bool,
      "blur_score": float, "is_blurry": bool,
      "brightness_score": float, "ink_level": float,
      "is_too_dark": bool, "is_too_bright": bool,
      "warnings": [str, ...],
    }
    """
    blur_score = compute_blur_score(image)
    brightness_score = compute_brightness_score(image)

    is_blurry = blur_score < config.IMAGE_QUALITY_BLUR_THRESHOLD
    is_too_dark = brightness_score < config.IMAGE_QUALITY_BRIGHTNESS_LOW
    # Overexposed = bright overall AND the ink itself washed out - a clean
    # scan of white paper is bright on average but still has dark ink (see
    # config.IMAGE_QUALITY_INK_MAX).
    ink_level = compute_ink_level(image)
    is_too_bright = (
        brightness_score > config.IMAGE_QUALITY_BRIGHTNESS_HIGH
        and ink_level > config.IMAGE_QUALITY_INK_MAX
    )

    warnings = []
    if is_blurry:
        warnings.append(
            f"Image appears blurry (sharpness {blur_score:.1f}, below the "
            f"{config.IMAGE_QUALITY_BLUR_THRESHOLD:.0f} threshold) - OCR accuracy may be "
            "reduced. Consider rescanning."
        )
    if is_too_dark:
        warnings.append(
            f"Image appears too dark (brightness {brightness_score:.1f}, below "
            f"{config.IMAGE_QUALITY_BRIGHTNESS_LOW:.0f}) - OCR accuracy may be reduced. "
            "Consider rescanning with better lighting."
        )
    if is_too_bright:
        warnings.append(
            f"Image appears overexposed (brightness {brightness_score:.1f}, above "
            f"{config.IMAGE_QUALITY_BRIGHTNESS_HIGH:.0f}, and ink washed out at "
            f"{ink_level:.0f}) - OCR accuracy may be reduced. "
            "Consider rescanning with less glare/brightness."
        )

    return {
        "rule_id": IQ_RULE_ID,
        "passed": not warnings,
        "blur_score": round(blur_score, 2),
        "is_blurry": is_blurry,
        "brightness_score": round(brightness_score, 2),
        "ink_level": round(ink_level, 2),
        "is_too_dark": is_too_dark,
        "is_too_bright": is_too_bright,
        "warnings": warnings,
    }


# ── Logbook pages ────────────────────────────────────────────────────────────
# assess_image_quality() is for any picture and only trips on extreme ones.
# A logbook page is known to be white paper with handwriting, so it can also
# be held to what a good logbook scan looks like - milder problems that still
# cost the OCR (research_tests iq_check). Thresholds: config.py, "Logbook
# page checks".

def compute_page_sharpness(image, width=1000):
    """Variance of the Laplacian with the page scaled to `width` pixels wide,
    so the same page scores about the same at any scan resolution."""
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    if gray.shape[1] != width:
        gray = cv2.resize(gray, (width, max(1, round(gray.shape[0] * width / gray.shape[1]))),
                          interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def assess_logbook_page(image):
    """assess_image_quality() plus the logbook-page checks: a dim page, soft
    focus, and washed-out writing on bleached paper. Same shape of result,
    with "is_dim", "is_soft", "is_washed_out", "page_sharpness",
    "white_share" and "faint_ink" added; "passed" covers them all. Never
    raises, never blocks OCR."""
    report = assess_image_quality(image)
    if image is None or image.size == 0:
        report.update({"page_sharpness": 0.0, "white_share": 0.0, "faint_ink": 255.0,
                       "is_dim": False, "is_soft": False, "is_washed_out": False})
        return report
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    sharpness = compute_page_sharpness(gray)
    white_share = float(np.mean(gray >= 250))
    # The writing's darkness: the darkest 0.1%, as compute_ink_level - a page
    # with little writing on it has under 1% ink, so a wider share would
    # measure its paper.
    faint_ink = report["ink_level"]
    brightness = report["brightness_score"]
    is_dim = not report["is_too_dark"] and brightness < config.IMAGE_QUALITY_DIM_BELOW
    is_soft = not report["is_blurry"] and sharpness < config.IMAGE_QUALITY_SHARPNESS_MIN
    is_washed_out = (not report["is_too_bright"]
                     and white_share >= config.IMAGE_QUALITY_WASHED_WHITE_SHARE
                     and faint_ink >= config.IMAGE_QUALITY_WASHED_INK_MIN)
    warnings = report["warnings"]
    if is_dim:
        warnings.append(
            f"The page is dim (brightness {brightness:.1f}; a good logbook scan is above "
            f"{config.IMAGE_QUALITY_DIM_BELOW:.0f}) - the writing is harder to read. Consider rescanning "
            "with more light.")
    if is_soft:
        warnings.append(
            f"The page is out of focus (sharpness {sharpness:.1f}; a good logbook scan is above "
            f"{config.IMAGE_QUALITY_SHARPNESS_MIN:.0f}) - the writing is harder to read. Consider rescanning.")
    if is_washed_out:
        warnings.append(
            f"The writing is washed out ({white_share * 100:.0f}% of the page is pure white and even the "
            f"darkest writing is {faint_ink:.0f} of 255) - it is harder to read. Consider rescanning with less "
            "brightness.")
    report.update({"passed": not warnings, "page_sharpness": round(sharpness, 2),
                   "white_share": round(white_share, 4), "faint_ink": round(faint_ink, 2),
                   "is_dim": is_dim, "is_soft": is_soft, "is_washed_out": is_washed_out})
    return report


def needs_enhancing(report):
    """True when a page flagged by assess_logbook_page is one enhance_for_ocr
    evens out: dim, washed out or too dark. A blurred page is only warned
    about - sharpening it did not help the OCR (research_tests iq_check)."""
    return bool(report and (report.get("is_dim") or report.get("is_washed_out") or report.get("is_too_dark")))


def enhance_for_ocr(image, report):
    """A copy of a dim, washed-out or too-dark logbook page evened out for
    reading: the paper made white and the ink dark again. Any other page is
    returned unchanged. Only the copy the OCR reads changes - the warning
    about the page stays."""
    if image is None or image.size == 0 or not needs_enhancing(report):
        return image
    out = image
    if needs_enhancing(report):
        gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY) if out.ndim == 3 else out
        ink, paper = float(np.percentile(gray, 0.5)), float(np.percentile(gray, 75))
        if paper - ink >= 20:
            # ink -> 20, paper -> 245: the range of a good scan
            scale = 225.0 / (paper - ink)
            lut = np.clip((np.arange(256, dtype=np.float32) - ink) * scale + 20.0, 0, 255).astype(np.uint8)
            out = cv2.LUT(out, lut)
    return out
