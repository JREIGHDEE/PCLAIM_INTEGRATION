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
"""
import cv2
import numpy as np

import config


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


def assess_image_quality(image):
    """Returns a plain dict describing `image`'s blur/brightness and any
    resulting warnings. Never raises, never blocks OCR - purely advisory
    metadata for the caller (see module docstring).

    {
      "blur_score": float, "is_blurry": bool,
      "brightness_score": float, "is_too_dark": bool, "is_too_bright": bool,
      "warnings": [str, ...],
    }
    """
    blur_score = compute_blur_score(image)
    brightness_score = compute_brightness_score(image)

    is_blurry = blur_score < config.IMAGE_QUALITY_BLUR_THRESHOLD
    is_too_dark = brightness_score < config.IMAGE_QUALITY_BRIGHTNESS_LOW
    is_too_bright = brightness_score > config.IMAGE_QUALITY_BRIGHTNESS_HIGH

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
            f"{config.IMAGE_QUALITY_BRIGHTNESS_HIGH:.0f}) - OCR accuracy may be reduced. "
            "Consider rescanning with less glare/brightness."
        )

    return {
        "blur_score": round(blur_score, 2),
        "is_blurry": is_blurry,
        "brightness_score": round(brightness_score, 2),
        "is_too_dark": is_too_dark,
        "is_too_bright": is_too_bright,
        "warnings": warnings,
    }
