"""
Template-based OCR automation engine.

Handles:
1. Template loading and application
2. Smart row propagation
3. Template alignment with offset detection
4. Auto crop generation from rows/columns
5. Confidence scoring
6. Template learning and updates
"""

import cv2
import numpy as np
import json
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


@dataclass
class GridLine:
    """Represents a vertical grid line position."""
    x: float  # pixel position
    confidence: float = 1.0  # detection confidence


@dataclass
class RowTemplate:
    """Represents a row position template."""
    y: float  # y position
    height: float  # row height
    spacing: float = 0  # space to next row


@dataclass
class CropBox:
    """Represents a crop region with metadata."""
    row: int
    column: int
    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0
    ocr_text: str = ""


@dataclass
class Cell:
    """Represents a cell in the table grid."""
    row: int
    column: int
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0
    label: str = ""


class TemplateAlignmentResult:
    """Result of template alignment operation."""
    
    def __init__(self, 
                 offset_x: float = 0,
                 offset_y: float = 0,
                 scale: float = 1.0,
                 matched_lines: int = 0,
                 total_lines: int = 0,
                 alignment_score: float = 0.0):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale
        self.matched_lines = matched_lines
        self.total_lines = total_lines
        self.alignment_score = alignment_score


class TemplateEngine:
    """Main engine for template-based OCR automation."""
    
    def __init__(self):
        self.vertical_lines: List[GridLine] = []
        self.row_template: Optional[RowTemplate] = None
        self.crop_presets: List[CropBox] = []
        
    def load_template_from_dict(self, template_dict: Dict[str, Any]) -> None:
        """Load template from dictionary."""
        if "gridLines" in template_dict:
            self.vertical_lines = [
                GridLine(x=float(x), confidence=1.0)
                for x in template_dict.get("gridLines", [])
            ]
        
        if "rowTemplate" in template_dict:
            rt = template_dict["rowTemplate"]
            self.row_template = RowTemplate(
                y=float(rt.get("y", 0)),
                height=float(rt.get("height", 50)),
                spacing=float(rt.get("spacing", 0))
            )
        
        if "cropPresets" in template_dict:
            self.crop_presets = [
                CropBox(
                    row=int(c.get("row", 0)),
                    column=int(c.get("column", 0)),
                    x=float(c.get("x", 0)),
                    y=float(c.get("y", 0)),
                    width=float(c.get("width", 100)),
                    height=float(c.get("height", 50))
                )
                for c in template_dict.get("cropPresets", [])
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        result = {
            "gridLines": [line.x for line in self.vertical_lines],
        }
        
        if self.row_template:
            result["rowTemplate"] = asdict(self.row_template)
        
        if self.crop_presets:
            result["cropPresets"] = [asdict(crop) for crop in self.crop_presets]
        
        return result


def build_template_payload(name: str,
                           grid_lines: Optional[List[float]] = None,
                           segment_info: Optional[List[Dict[str, Any]]] = None,
                           crop_box_percent: Optional[Dict[str, float]] = None,
                           row_template: Optional[Dict[str, Any]] = None,
                           crop_presets: Optional[List[Dict[str, Any]]] = None,
                           image_width: Optional[int] = None,
                           image_height: Optional[int] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           active_crop_preset: Optional[Dict[str, Any]] = None,
                           active_crop_preset_id: Optional[str] = None) -> Dict[str, Any]:
    """Build a single reusable template payload containing grid, crop and row layout data."""
    payload = {
        "name": name or "Untitled Template",
        "gridLines": [float(x) for x in (grid_lines or [])],
        "segmentInfo": list(segment_info or []),
        "cropBoxPercent": crop_box_percent,
        "rowTemplate": dict(row_template or {}),
        "cropPresets": [dict(crop) for crop in (crop_presets or [])],
        "created_at": int(time.time() * 1000),
        "metadata": dict(metadata or {})
    }

    if image_width is not None:
        payload["imageWidth"] = int(image_width)
    if image_height is not None:
        payload["imageHeight"] = int(image_height)
    if active_crop_preset is not None:
        payload["activeCropPreset"] = dict(active_crop_preset)
    if active_crop_preset_id is not None:
        payload["activeCropPresetId"] = active_crop_preset_id

    return payload


def analyze_document_layout(image: np.ndarray) -> Dict[str, Any]:
    """Compute lightweight layout features from an image for template matching."""
    if image is None or image.size == 0:
        return {
            "image_width": 0,
            "image_height": 0,
            "aspect_ratio": 0.0,
            "gridLineCount": 0,
            "rowCount": 0,
            "lineSpacing": 0.0,
            "landmark_density": 0.0,
            "gridLines": []
        }

    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    vertical_projection = np.sum(edges, axis=0)
    vertical_threshold = max(1, int(np.max(vertical_projection) * 0.35))
    vertical_peaks = np.where(vertical_projection > vertical_threshold)[0]

    horizontal_projection = np.sum(edges, axis=1)
    horizontal_threshold = max(1, int(np.max(horizontal_projection) * 0.2))
    horizontal_peaks = np.where(horizontal_projection > horizontal_threshold)[0]

    row_count = max(1, len(horizontal_peaks))
    line_spacing = 0.0
    if len(horizontal_peaks) > 1:
        gaps = np.diff(horizontal_peaks)
        line_spacing = float(np.mean(gaps)) / max(1, h)

    grid_lines = []
    if len(vertical_peaks) > 0:
        grid_lines = [float(x / max(1, w)) for x in vertical_peaks if 0 < x < w]

    return {
        "image_width": int(w),
        "image_height": int(h),
        "aspect_ratio": float(w / max(1, h)),
        "gridLineCount": len(grid_lines),
        "rowCount": row_count,
        "lineSpacing": line_spacing,
        "landmark_density": float(np.mean(edges > 0)),
        "gridLines": grid_lines[:8]
    }


def score_template_match(template_payload: Optional[Dict[str, Any]], current_context: Optional[Dict[str, Any]]) -> float:
    """Return a similarity score in the range 0.0-1.0 for how well a template matches the current document layout."""
    if not template_payload:
        return 0.0
    if not current_context:
        return 0.0

    score = 0.0
    weights = 0.0

    template_width = template_payload.get("imageWidth") or template_payload.get("metadata", {}).get("image_width")
    template_height = template_payload.get("imageHeight") or template_payload.get("metadata", {}).get("image_height")
    current_width = current_context.get("image_width")
    current_height = current_context.get("image_height")
    if template_width and template_height and current_width and current_height:
        size_score = 1.0 - min(1.0, abs((template_width / max(1, template_height)) - (current_width / max(1, current_height))) / 1.5)
        score += size_score * 0.2
        weights += 0.2

    aspect_ratio_score = 0.0
    if template_width and current_width and template_height and current_height:
        template_ratio = template_width / max(1, template_height)
        current_ratio = current_width / max(1, current_height)
        aspect_ratio_score = max(0.0, 1.0 - min(1.0, abs(template_ratio - current_ratio) / 1.5))
    if aspect_ratio_score:
        score += aspect_ratio_score * 0.15
        weights += 0.15

    template_grid_lines = [float(x) for x in template_payload.get("gridLines", [])]
    current_grid_lines = [float(x) for x in current_context.get("gridLines", [])]
    if template_grid_lines and current_grid_lines:
        pair_count = min(len(template_grid_lines), len(current_grid_lines))
        if pair_count > 0:
            diffs = [abs(template_grid_lines[i] - current_grid_lines[i]) for i in range(pair_count)]
            position_score = max(0.0, 1.0 - (sum(diffs) / max(1, pair_count)))
            count_score = min(1.0, pair_count / max(1, max(len(template_grid_lines), len(current_grid_lines))))
            score += ((position_score * 0.7) + (count_score * 0.3)) * 0.25
            weights += 0.25

    template_line_spacing = None
    metadata = template_payload.get("metadata") or {}
    if metadata.get("line_spacing") is not None:
        template_line_spacing = float(metadata.get("line_spacing") or 0)
    elif metadata.get("lineSpacing") is not None:
        template_line_spacing = float(metadata.get("lineSpacing") or 0)
    current_line_spacing = current_context.get("lineSpacing")
    if template_line_spacing is not None and current_line_spacing is not None:
        spacing_gap = abs(template_line_spacing - float(current_line_spacing))
        spacing_score = max(0.0, 1.0 - min(1.0, spacing_gap / 0.08))
        score += spacing_score * 0.2
        weights += 0.2

    row_template = template_payload.get("rowTemplate") or {}
    current_row_count = current_context.get("rowCount", 0)
    if row_template:
        row_height = float(row_template.get("height", 0) or 0)
        if current_row_count and row_height > 0:
            row_score = max(0.0, 1.0 - min(1.0, abs(row_height - current_row_count) / max(1, current_row_count * 2)))
            score += row_score * 0.1
            weights += 0.1
        else:
            score += 0.05
            weights += 0.05

    crop_box = template_payload.get("cropBoxPercent") or {}
    if crop_box:
        crop_score = 0.0
        if current_context.get("cropBoxPercent"):
            crop_score = 1.0 - min(1.0, abs(float(crop_box.get("left", 0.0) or 0.0) - float(current_context["cropBoxPercent"].get("left", 0.0) or 0.0)))
        else:
            crop_score = 0.7
        score += crop_score * 0.1
        weights += 0.1

    if template_payload.get("cropPresets"):
        score += 0.05
        weights += 0.05

    if template_payload.get("segmentInfo"):
        score += 0.05
        weights += 0.05

    return round(score / max(1.0, weights), 3)


def match_templates(templates: List[Dict[str, Any]], current_context: Optional[Dict[str, Any]], page_parity: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
    """Find the best matching saved template for the active document."""
    if not templates:
        return None, None

    normalized_parity = page_parity if page_parity in {"odd", "even"} else None
    eligible_templates = []
    for template in templates:
        template_parity = (template.get("metadata") or {}).get("pageParity", "current")
        if normalized_parity and template_parity not in {"current", normalized_parity}:
            continue
        eligible_templates.append(template)
    if not eligible_templates:
        eligible_templates = templates

    best_template = None
    best_score = 0.0
    for template in eligible_templates:
        score = score_template_match(template, current_context)
        if score > best_score:
            best_score = score
            best_template = template

    return best_template, best_score


def normalize_template_for_image(template_dict: Dict[str, Any], image_width: int, image_height: int) -> Dict[str, Any]:
    """Convert the editor's normalized grid and row coordinates to image pixels."""
    placed = dict(template_dict or {})
    source_width = float(placed.get("imageWidth") or image_width or 1)
    source_height = float(placed.get("imageHeight") or image_height or 1)
    scale_y = image_height / source_height
    placed["gridLines"] = [float(x) * image_width for x in placed.get("gridLines", [])]
    row_template = placed.get("rowTemplate")
    if row_template:
        placed["rowTemplate"] = {
            **row_template,
            "y": float(row_template.get("y", 0)) * scale_y,
            "height": float(row_template.get("height", 0)) * scale_y,
            "spacing": float(row_template.get("spacing", 0)) * scale_y
        }
    return placed


def detect_vertical_lines(image: np.ndarray, 
                         threshold_ratio: float = 0.35,
                         min_gap: int = 5) -> List[GridLine]:
    """
    Detect vertical lines in an image using edge detection and projection.
    
    Args:
        image: Input image (BGR)
        threshold_ratio: Threshold for line detection (0.0-1.0)
        min_gap: Minimum pixel gap between lines
    
    Returns:
        List of detected GridLine objects
    """
    if image is None or image.size == 0:
        return []
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Vertical line detection using morphology
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, max(3, image.shape[0] // 15))
    )
    vertical = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Project to find line peaks
    projection = np.sum(vertical, axis=0)
    threshold = max(1, int(np.max(projection) * threshold_ratio))
    peaks = np.where(projection > threshold)[0]
    
    if len(peaks) < 2:
        return []
    
    # Group peaks into lines
    lines = []
    last = -100
    for x in peaks:
        if x - last > min_gap:
            lines.append(x)
            last = x
    
    # Filter lines in reasonable range
    h, w = image.shape[:2]
    lines = [x for x in lines if x > w * 0.05 and x < w * 0.95]
    
    # Convert to GridLine objects with confidence
    result = []
    for x in lines[:20]:  # Limit to 20 lines
        confidence = min(1.0, projection[x] / threshold) if threshold > 0 else 1.0
        result.append(GridLine(x=float(x), confidence=confidence))
    
    return result


def align_template(image: np.ndarray,
                  template_lines: List[GridLine],
                  max_offset: float = 50) -> TemplateAlignmentResult:
    """
    Align template to image by detecting actual lines and calculating offset.
    
    Args:
        image: Input image
        template_lines: Template line positions (in pixels)
        max_offset: Maximum allowed offset in pixels
    
    Returns:
        TemplateAlignmentResult with offset and alignment score
    """
    if not template_lines or image is None or image.size == 0:
        return TemplateAlignmentResult()
    
    # Detect actual lines in image
    detected = detect_vertical_lines(image)
    if not detected:
        return TemplateAlignmentResult()
    
    detected_x = [line.x for line in detected]
    template_x = [line.x for line in template_lines]
    
    # Calculate best offset match
    best_offset = 0
    best_matches = 0
    
    # Try different offsets
    for offset in np.linspace(-max_offset, max_offset, int(max_offset * 2) + 1):
        matches = 0
        for tx in template_x:
            adjusted = tx + offset
            # Check if adjusted line is close to any detected line
            for dx in detected_x:
                if abs(adjusted - dx) < 15:
                    matches += 1
                    break
        
        if matches > best_matches:
            best_matches = matches
            best_offset = offset
    
    alignment_score = best_matches / len(template_x) if template_x else 0
    
    return TemplateAlignmentResult(
        offset_x=best_offset,
        offset_y=0,
        scale=1.0,
        matched_lines=best_matches,
        total_lines=len(template_x),
        alignment_score=alignment_score
    )


def _compute_ink_mask(image: np.ndarray,
                     ink_thresh: int = 180,
                     blue_thresh: int = 35) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a per-pixel ink mask (and its per-row density) for a ruled ledger
    page. Two things pollute a naive "any dark pixel" mask on scans like
    this:
    - The ledger's own printed ruling lines, which are a light blue rather
      than the neutral black/gray of handwriting - excluded via a blueness
      check (B channel minus R channel) rather than brightness alone.
    - Uneven scan lighting (gutter shadow near the spine, vignetting), which
      a single global brightness threshold can't tell apart from ink -
      corrected by dividing out a large-kernel local background estimate
      before thresholding, since ink strokes are thin relative to that
      kernel but shading gradients are not.

    Returns (mask, density) where mask is a 2D boolean array (cropped to the
    2%-98% horizontal margin, to dodge binding-edge artifacts) and density is
    mask summed per row.
    """
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return np.zeros((0, 0), dtype=bool), np.zeros(0, dtype=np.float64)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bg_kernel = max(15, (min(h, w) // 15) | 1)
    background = cv2.GaussianBlur(gray, (bg_kernel, bg_kernel), 0)
    normalized = cv2.divide(gray, background, scale=255)

    b, g, r = cv2.split(image.astype(np.int16))
    blueness = b - r

    x0, x1 = int(w * 0.02), int(w * 0.98)
    dark = normalized[:, x0:x1] < ink_thresh
    not_ruled = blueness[:, x0:x1] < blue_thresh
    mask = dark & not_ruled
    density = mask.sum(axis=1).astype(np.float64)
    return mask, density


def _coarse_row_bands(density: np.ndarray, h: int) -> List[Tuple[int, int]]:
    """
    Locate roughly where rows are from a per-row ink density profile: smooth
    it, threshold against its own baseline/peak, then merge bands separated
    by a small gap (a wrapped sub-line inside one multi-line cell) while
    keeping bands separated by a real gap (several times wider, empirically -
    a genuine blank ruled line between entries) apart.

    This pass only needs to be roughly right - _wrap_bands_to_components()
    afterwards grows each band to fully contain whatever ink actually
    touches it, so a slightly-too-tight or slightly-too-loose threshold here
    gets corrected rather than baked into the final row.
    """
    smooth_k = max(3, int(h * 0.004) | 1)
    kernel = np.ones(smooth_k, dtype=np.float64) / smooth_k
    smoothed = np.convolve(density, kernel, mode='same')

    baseline = float(np.percentile(smoothed, 10))
    peak = float(np.percentile(smoothed, 90))
    threshold = baseline + max(2.0, (peak - baseline) * 0.10)
    is_text = smoothed > threshold

    raw_bands = []
    start = None
    for y in range(h):
        if is_text[y] and start is None:
            start = y
        elif not is_text[y] and start is not None:
            raw_bands.append((start, y))
            start = None
    if start is not None:
        raw_bands.append((start, h))

    merge_gap = max(4, int(h * 0.014))
    merged: List[List[int]] = []
    for band in raw_bands:
        if merged and band[0] - merged[-1][1] <= merge_gap:
            merged[-1][1] = band[1]
        else:
            merged.append([band[0], band[1]])

    min_band_px = max(6, int(h * 0.01))
    return [(b0, b1) for b0, b1 in merged if b1 - b0 >= min_band_px]


def _wrap_bands_to_components(ink_mask: np.ndarray,
                             bands: List[Tuple[int, int]],
                             h: int) -> List[Tuple[int, int]]:
    """
    Grow each row band to fully contain every ink blob (stroke/character) it
    overlaps, using connected-component analysis instead of a fixed-distance
    edge search. A distance cap can't tell "the last couple of pixels of a
    descender" apart from "a genuinely taller multi-line entry the coarse
    pass under-measured" - it just clips whichever is bigger than the cap.
    Whole connected ink blobs don't have that problem: if any part of a
    stroke overlaps a row's current range, the row grows to that stroke's
    *entire* extent in one step, above and below, however tall it turns out
    to be - so both a small clipped descender and a taller-than-expected
    wrapped line get fully included, with no arbitrary size limit.

    Two guards keep this from absorbing noise or bridging two entries
    together:
    - A blob only counts if it's more than a couple of stray pixels (dust
      specks and scan-line artifacts commonly render as a hair-thin, tall
      sliver - real handwriting strokes are wider than that even when faint)
      and isn't a long thin thread far taller than a normal stroke.
    - A blob can only pull a row's edge out to the midpoint of the gap to
      the *next* band in the list, in either direction - so it can never
      drag two neighboring rows together, only reclaim genuinely unclaimed
      space between them.
    """
    if not bands:
        return []

    mask_u8 = ink_mask.astype(np.uint8)
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8)

    max_component_height = max(20, int(h * 0.05))
    components = [
        (int(stats[i, 1]), int(stats[i, 1] + stats[i, 3]))
        for i in range(1, num_labels)
        if stats[i, 4] >= 3  # drop 1-2px specks
        and stats[i, 2] >= 2  # drop hair-thin single-pixel-wide slivers
        and stats[i, 3] <= max_component_height  # drop implausibly tall "strokes" (scan artifacts)
    ]

    n = len(bands)
    refined = []
    for i, (y0, y1) in enumerate(bands):
        prev_bottom = bands[i - 1][1] if i > 0 else 0
        next_top = bands[i + 1][0] if i < n - 1 else h
        top_guard = (y0 + prev_bottom) // 2 if i > 0 else 0
        bottom_guard = (y1 + next_top) // 2 if i < n - 1 else h

        new_top, new_bottom = y0, y1
        changed = True
        while changed:
            changed = False
            for (cy0, cy1) in components:
                cy0c, cy1c = max(cy0, top_guard), min(cy1, bottom_guard)
                if cy1c <= cy0c:
                    continue
                if cy0c < new_bottom and cy1c > new_top:
                    if cy0c < new_top:
                        new_top = cy0c
                        changed = True
                    if cy1c > new_bottom:
                        new_bottom = cy1c
                        changed = True

        refined.append((new_top, new_bottom))
    return refined


def detect_content_rows(image: np.ndarray,
                       seed_y: float,
                       seed_height: float,
                       image_bottom: Optional[float] = None,
                       max_rows: int = 100) -> List[RowTemplate]:
    """
    Detect row positions/heights from actual page content instead of blindly
    repeating a fixed height+spacing.

    Row 1's *top* is trusted from seed_y - the box the user drew (or a saved
    template's first row) - since nothing in the image says where the
    *logical* first entry starts (it may follow a header, a title, or
    nothing) - that's a human judgment call, not something detectable. Its
    bottom, and every row after it, are fully wrapped around real ink -
    above and below - via connected-component analysis (see
    _wrap_bands_to_components), so nothing gets clipped at either edge,
    including row 1 itself if the drawn seed box was a little short. If
    detection runs dry before reaching the bottom of the page (faint ink, a
    trailing blank section, a band the detector missed), the remainder is
    filled by uniform propagation using the median height/spacing of the
    rows that *were* detected, so output never regresses below the old
    blind-propagation behavior - it just no longer needs to guess for
    content it can see.
    """
    rows: List[RowTemplate] = [RowTemplate(y=float(seed_y), height=float(seed_height), spacing=0.0)]
    if image is None or image.size == 0 or max_rows <= 1:
        return rows

    h = image.shape[0]
    bottom = float(image_bottom) if image_bottom else float(h)

    seed_bottom = seed_y + seed_height
    ink_mask, density = _compute_ink_mask(image)
    coarse_bands = _coarse_row_bands(density, h)
    candidates = [
        band for band in coarse_bands
        if band[0] >= seed_bottom - max(2.0, seed_height * 0.15)
    ]

    # Wrap row 1's own seed alongside the candidates in one pass, sharing the
    # same neighbor-midpoint guard, so row 1's bottom edge is corrected
    # consistently with every other row instead of by a separate rule - and
    # so a component that would grow row 1 downward can't overshoot into
    # row 2's territory (or vice versa).
    wrapped = _wrap_bands_to_components(
        ink_mask,
        [(int(seed_y), int(seed_bottom))] + [(int(y0), int(y1)) for (y0, y1) in candidates],
        h
    )
    seed_top, seed_bottom_wrapped = wrapped[0]
    candidates = wrapped[1:]
    rows[0] = RowTemplate(y=float(seed_top), height=float(seed_bottom_wrapped - seed_top), spacing=0.0)
    seed_bottom = float(seed_bottom_wrapped)

    cursor_bottom = seed_bottom
    detected_heights = []
    for (y0, y1) in candidates:
        if len(rows) >= max_rows or y0 >= bottom:
            break
        rows[-1] = RowTemplate(y=rows[-1].y, height=rows[-1].height, spacing=max(0.0, y0 - cursor_bottom))
        band_height = float(y1 - y0)
        rows.append(RowTemplate(y=float(y0), height=band_height, spacing=0.0))
        detected_heights.append(band_height)
        cursor_bottom = float(y1)

    if len(rows) < max_rows and cursor_bottom < bottom:
        fallback_height = float(np.median(detected_heights)) if detected_heights else float(seed_height)
        gaps = [rows[i + 1].y - (rows[i].y + rows[i].height) for i in range(len(rows) - 1)]
        fallback_spacing = float(np.median(gaps)) if gaps else 0.0
        if rows:
            rows[-1] = RowTemplate(y=rows[-1].y, height=rows[-1].height, spacing=fallback_spacing)
        current_y = cursor_bottom + fallback_spacing
        while current_y < bottom and len(rows) < max_rows:
            rows.append(RowTemplate(y=current_y, height=fallback_height, spacing=fallback_spacing))
            current_y += fallback_height + fallback_spacing

    return rows


def propagate_rows(first_row_y: float,
                  row_height: float,
                  row_spacing: float,
                  image_height: float,
                  max_rows: int = 100) -> List[RowTemplate]:
    """
    Generate row positions using smart propagation.
    
    Args:
        first_row_y: Y position of first row
        row_height: Height of each row
        row_spacing: Space between rows (0 = rows touch)
        image_height: Height of image/page
        max_rows: Maximum number of rows to generate
    
    Returns:
        List of RowTemplate objects
    """
    rows = []
    current_y = first_row_y
    total_spacing = row_height + row_spacing
    
    row_num = 0
    while current_y < image_height and row_num < max_rows:
        rows.append(RowTemplate(
            y=current_y,
            height=row_height,
            spacing=row_spacing
        ))
        current_y += total_spacing
        row_num += 1
    
    return rows


def detect_rows_with_template(image: np.ndarray,
                             row_template: RowTemplate,
                             search_radius: int = 20) -> List[RowTemplate]:
    """
    Detect actual row boundaries using template as guide.
    
    Hybrid approach:
    1. Use template prediction as initial guess
    2. Look for horizontal edges nearby
    3. Snap to nearest detected line
    
    Args:
        image: Input image
        row_template: Template row parameters
        search_radius: How far to search from predicted position
    
    Returns:
        List of detected RowTemplate objects
    """
    if image is None or image.size == 0 or row_template is None:
        return []
    
    h, w = image.shape[:2]
    
    # Convert to grayscale and detect edges
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Horizontal edge detection
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(3, w // 15), 1)
    )
    horizontal = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Project to find horizontal lines
    projection = np.sum(horizontal, axis=1)
    
    # Generate predicted row positions
    detected_rows = []
    current_y = row_template.y
    row_height = row_template.height
    spacing = row_template.spacing
    total_spacing = row_height + spacing
    
    while current_y < h:
        # Search for line near predicted position
        search_start = max(0, int(current_y - search_radius))
        search_end = min(h, int(current_y + row_height + search_radius))
        
        search_window = projection[search_start:search_end]
        if len(search_window) > 0:
            threshold = np.mean(search_window)
            peaks = np.where(search_window > threshold)[0]
            
            if len(peaks) > 0:
                # Snap to nearest peak
                best_offset = 0
                best_peak = peaks[0]
                min_dist = abs(peaks[0] - search_radius)
                
                for peak in peaks:
                    dist = abs(peak - search_radius)
                    if dist < min_dist:
                        min_dist = dist
                        best_peak = peak
                
                actual_y = search_start + best_peak
            else:
                actual_y = current_y
        else:
            actual_y = current_y
        
        detected_rows.append(RowTemplate(
            y=float(actual_y),
            height=row_height,
            spacing=spacing
        ))
        
        current_y += total_spacing
    
    return detected_rows


def generate_cells(vertical_lines: List[GridLine],
                  rows: List[RowTemplate],
                  image_width: float,
                  image_height: float) -> List[Cell]:
    """
    Generate table cells from vertical lines and rows.
    
    Args:
        vertical_lines: List of vertical line positions
        rows: List of row positions
        image_width: Width of image
        image_height: Height of image
    
    Returns:
        List of Cell objects
    """
    cells = []
    
    if not vertical_lines or not rows:
        return cells
    
    # Sort lines by x position
    sorted_lines = sorted([line.x for line in vertical_lines])
    column_boundaries = [0] + sorted_lines + [image_width]
    
    for row_idx, row in enumerate(rows):
        row_start_y = row.y
        row_end_y = row.y + row.height
        
        # Skip rows outside image bounds
        if row_start_y >= image_height or row_end_y <= 0:
            continue
        
        # Create cells for this row
        for col_idx in range(len(column_boundaries) - 1):
            x1 = column_boundaries[col_idx]
            x2 = column_boundaries[col_idx + 1]
            
            cell = Cell(
                row=row_idx,
                column=col_idx,
                x1=float(x1),
                y1=float(row_start_y),
                x2=float(x2),
                y2=float(row_end_y),
                confidence=1.0
            )
            cells.append(cell)
    
    return cells


def extract_crop_from_cell(image: np.ndarray, cell: Cell) -> Optional[np.ndarray]:
    """
    Extract image crop from cell coordinates.
    
    Args:
        image: Input image
        cell: Cell definition
    
    Returns:
        Cropped image or None if invalid
    """
    if image is None or image.size == 0:
        return None
    
    h, w = image.shape[:2]
    
    # Clamp coordinates to image bounds
    x1 = max(0, int(cell.x1))
    y1 = max(0, int(cell.y1))
    x2 = min(w, int(cell.x2))
    y2 = min(h, int(cell.y2))
    
    if x2 <= x1 or y2 <= y1:
        return None
    
    return image[y1:y2, x1:x2].copy()


class TemplateAutoDetector:
    """Automatically applies templates when PDF page is loaded."""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
    
    def auto_place_template(self,
                           image: np.ndarray,
                           template_dict: Dict[str, Any],
                           auto_align: bool = True,
                           forced_rows: Optional[List[Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Automatically place all template elements on image.

        Args:
            image: Input image
            template_dict: Saved template data
            auto_align: Whether to detect and apply alignment offset
            forced_rows: If given, use these row positions verbatim instead of
                detecting/propagating rows on this image. Used to carry the
                row layout detected on one side of a two-page ledger spread
                over to its paired side, since a spread's rows are one
                physical entry split across both pages and must line up.

        Returns:
            Dictionary with placed template elements
        """
        self.template_engine.load_template_from_dict(
            normalize_template_for_image(template_dict, image.shape[1], image.shape[0])
            if image is not None and image.size else template_dict
        )
        
        result = {
            "vertical_lines": [],
            "rows": [],
            "cells": [],
            "alignment": None,
            "success": False
        }
        
        if image is None or image.size == 0:
            return result
        
        h, w = image.shape[:2]
        
        # Step 1: Align template if requested
        alignment = None
        if auto_align and self.template_engine.vertical_lines:
            alignment = align_template(image, self.template_engine.vertical_lines)
            result["alignment"] = {
                "offset_x": alignment.offset_x,
                "offset_y": alignment.offset_y,
                "alignment_score": alignment.alignment_score
            }
        
        # Step 2: Place vertical lines with offset
        offset_x = alignment.offset_x if alignment else 0
        for line in self.template_engine.vertical_lines:
            result["vertical_lines"].append({
                "x": line.x + offset_x,
                "confidence": line.confidence
            })
        
        # Step 3: Generate rows - forced (paired-page) rows take precedence over
        # detecting/propagating fresh ones on this image.
        if forced_rows is not None:
            for row in forced_rows:
                result["rows"].append({
                    "y": float(row.get("y", 0)),
                    "height": float(row.get("height", 0)),
                    "spacing": float(row.get("spacing", 0))
                })
        elif self.template_engine.row_template:
            rows = detect_content_rows(
                image,
                self.template_engine.row_template.y,
                self.template_engine.row_template.height,
                image_bottom=h
            )
            for row in rows:
                result["rows"].append({
                    "y": row.y,
                    "height": row.height,
                    "spacing": row.spacing
                })
        
        # Step 4: Generate cells
        grid_lines = [GridLine(x=line["x"]) for line in result["vertical_lines"]]
        rows = [RowTemplate(
            y=row["y"],
            height=row["height"],
            spacing=row.get("spacing", 0)
        ) for row in result["rows"]]
        
        cells = generate_cells(grid_lines, rows, w, h)
        for cell in cells:
            result["cells"].append({
                "row": cell.row,
                "column": cell.column,
                "x1": cell.x1,
                "y1": cell.y1,
                "x2": cell.x2,
                "y2": cell.y2
            })
        
        result["success"] = True
        return result
