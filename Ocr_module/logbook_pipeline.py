"""
Logbook upload -> one review session per patient row.

The full server-side flow for one uploaded logbook scan (image or PDF):

  1. load pages        - images as-is; PDF pages rendered at 2x, the same
                         as ocr_engine/batch_processor
  2. IQ-01             - image_quality.assess_image_quality() per page.
                         Advisory only: warnings are shown at the top of
                         the review, OCR always runs.
  3. template match    - template_engine.match_templates() against the saved
                         grid templates, by page parity for PDFs. A page
                         scoring below config.TEMPLATE_MATCH_THRESHOLD is
                         reported and skipped - never OCR'd against a
                         template that doesn't fit.
  4. place + crop      - TemplateAutoDetector.auto_place_template(); on a
                         two-page spread the odd page's rows are carried to
                         the even page (same as BatchProcessor) so both
                         halves of one patient entry line up.
  5. PaddleOCR         - each cell crop OCR'd on its own.
  6. route             - each field routed by confidence (route_confidence).
  7. group             - cells grouped into logbook rows (both pages of a
                         spread together); the printed header row and rows
                         with too little text are dropped.

build_review_rows() is pure (no DB) so it can be tested directly;
persist_review_rows() writes one pending case_sessions row per patient row.

Column mapping: generate_cells() adds the strip left of a template's first
grid line as column 0. The calibration UI never OCRs that strip - its cell k
runs from grid line k to k+1 and is labelled segmentInfo[k] - so cell
column c here is segmentInfo[c - 1], and column 0 is ignored.
"""
import logging
import os
import re
import uuid

import cv2
import fitz
import numpy as np

import config
from image_quality import IQ_RULE_ID, assess_image_quality
from philhealth import case_bridge, field_catalog, review_fields
from template_engine import (
    TemplateAutoDetector,
    detect_ruling_lines,
    map_rows_between_pages,
    analyze_document_layout,
    extract_crop_from_cell,
    match_templates,
    Cell,
)

logger = logging.getLogger(__name__)

ACCEPTED = "accepted"
NEEDS_CHECK = "needs_check"
MANUAL = "manual_encoding_required"
# Nothing written in this logbook cell - nothing to check or type.
EMPTY = "empty"

# Printed column-header words. A leading row where at least two cells read
# like headers is the logbook's header row, not a patient.
_HEADER_RE = re.compile(
    r"\b(CASE|NAME|BDAY|BIRTH|ADDRESS|ADMISSION|ADMITTING|DIAGNOSIS|DELIVERY|DISCHARGE)\b",
    re.IGNORECASE,
)
_HEADER_SEARCH_ROWS = 3


def route_confidence(confidence):
    """Thesis confidence routing - thresholds live in config.py."""
    if confidence is None or confidence < config.OCR_CONFIDENCE_REVIEW:
        return MANUAL
    if confidence < config.OCR_CONFIDENCE_ACCEPT:
        return NEEDS_CHECK
    return ACCEPTED


def thresholds():
    return {"accept": config.OCR_CONFIDENCE_ACCEPT, "review": config.OCR_CONFIDENCE_REVIEW}


def load_pages(path):
    """[(page_number, BGR image, page_parity or None)] for an image or PDF."""
    if os.path.splitext(path)[1].lower() == ".pdf":
        pages = []
        doc = fitz.open(path)
        try:
            for index in range(len(doc)):
                pix = doc[index].get_pixmap(matrix=fitz.Matrix(2, 2))
                data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    image = cv2.cvtColor(data, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    image = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
                else:
                    image = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
                parity = "odd" if (index + 1) % 2 else "even"
                pages.append((index + 1, image, parity))
        finally:
            doc.close()
        return pages

    image = cv2.imread(path)
    if image is None:
        raise ValueError("Could not read the uploaded image.")
    # A single image could be either side of a spread - let template
    # matching decide rather than assuming a parity.
    return [(1, image, None)]


# A cell whose handwriting covers less than this share of the crop (and
# fewer than _MIN_INK_PIXELS) is treated as blank: specks, ruling-line
# fragments and stray dots aren't writing.
_MIN_INK_SHARE = 0.01
_MIN_INK_PIXELS = 60
# White margin added for the retry - PaddleOCR often misses a line of
# handwriting that touches the crop's edge.
_RETRY_MARGIN = 16


def _ink_mask(image):
    """Handwriting pixels in a cell crop: dark marks, minus the printed
    ruling lines and specks. None for an empty/invalid image."""
    if image is None or getattr(image, "size", 0) == 0:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    h, w = gray.shape
    ink = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 25, 15)
    rules = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, w // 3), 1)))
    rules |= cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(3, int(h * 0.7)))))
    ink = cv2.subtract(ink, cv2.dilate(rules, np.ones((3, 3), np.uint8)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(ink)
    keep = np.zeros(count, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= 12
    return keep[labels]


def _has_writing(mask):
    if mask is None:
        return True  # can't tell - don't call the cell blank
    ink = int(mask.sum())
    return ink >= _MIN_INK_PIXELS and ink >= _MIN_INK_SHARE * mask.size


def _missed_ink(mask, tokens, shift=0):
    """Share of the handwriting outside every token box (0-1), or None when
    it can't be measured (no writing, or tokens without boxes)."""
    if mask is None or not _has_writing(mask) or not all(t.get("box") for t in tokens):
        return None
    covered = np.zeros(mask.shape, dtype=np.uint8)
    for token in tokens:
        cv2.fillPoly(covered, [np.int32(np.array(token["box"]) - shift)], 255)
    covered = cv2.dilate(covered, np.ones((7, 7), np.uint8)) > 0
    return float((mask & ~covered).sum()) / float(mask.sum())


def ocr_cell(image, ocr_fn):
    """OCR one cell crop -> (raw_text, confidence, tokens, error, flags).

    Confidence is the *lowest* token confidence in the cell, not the mean:
    one misread word must not be hidden by confident neighbours when the
    result decides whether a field is auto-accepted. None when no text was
    found. An OCR failure is returned as `error` (the field then needs
    manual encoding) instead of looking like an empty cell.

    flags: {"blank": no handwriting in the cell at all,
            "incomplete": part of the handwriting is outside everything
                          PaddleOCR read (config.OCR_MISSED_INK_LIMIT) -
                          checked after one retry with a white margin}
    """
    flags = {"blank": False, "incomplete": False}
    mask = _ink_mask(image)

    def read(img):
        found = ocr_fn(img) or []
        return [t for t in found if str(t.get("text", "")).strip()]

    try:
        tokens = read(image)
        missed = _missed_ink(mask, tokens)
        if missed is not None and missed > config.OCR_MISSED_INK_LIMIT:
            padded = cv2.copyMakeBorder(image, *([_RETRY_MARGIN] * 4), cv2.BORDER_CONSTANT, value=(255, 255, 255))
            retry = read(padded)
            retry_missed = _missed_ink(mask, retry, shift=_RETRY_MARGIN)
            if retry_missed is not None and retry_missed + 0.05 < missed:
                tokens, missed = retry, retry_missed
    except Exception:
        logger.exception("OCR failed on a logbook cell")
        return "", None, [], "OCR failed on this cell", flags

    flags["incomplete"] = missed is not None and missed > config.OCR_MISSED_INK_LIMIT
    if not tokens:
        flags["blank"] = not _has_writing(mask)
        return "", None, [], None, flags
    raw_text = " ".join(str(t["text"]).strip() for t in tokens)
    confidence = round(float(min(t.get("confidence", 0) for t in tokens)), 4)
    return raw_text, confidence, [
        {"text": str(t["text"]), "confidence": round(float(t.get("confidence", 0)), 4)} for t in tokens
    ], None, flags


def field_status(category, confidence, flags):
    """Confidence routing for one OCR'd field, plus two safety rules:
    a reading that missed part of the writing is never auto-accepted, and
    a cell with no writing at all is "empty" (nothing to type) - except the
    columns every logbook entry must have, which then need typing."""
    if flags.get("blank") and category not in field_catalog.OCR_CLAIM_REQUIRED_CATEGORIES:
        return EMPTY
    status = route_confidence(confidence)
    if status == ACCEPTED and flags.get("incomplete"):
        return NEEDS_CHECK
    return status


def _first_entry_line(template, ruled_lines, height):
    """Top of the first patient row: the first ruled line in the top quarter
    of the page that lies below the template's saved first-row position -
    on a logbook page that is the line under the printed column header.
    Starting there keeps the header from being merged with (and then
    dropped together with) the first patient's entry. None (use the
    template's own position) when the page has no such line."""
    row_template = template.get("rowTemplate") or {}
    saved = float(row_template.get("y", 0)) * height / float(template.get("imageHeight") or height)
    for y in ruled_lines:
        if y > height * 0.25:
            break
        if y > saved:
            return float(y)
    return None


def _page_category_for_column(template, column):
    segments = template.get("segmentInfo") or []
    if column < 1 or column > len(segments):
        return None
    return (segments[column - 1] or {}).get("category") or None


def _save_crop(crop, upload_id, page_number, row, column):
    folder = os.path.join(config.REVIEW_CROPS_FOLDER, upload_id)
    os.makedirs(folder, exist_ok=True)
    filename = f"p{page_number}_r{row}_c{column}.png"
    cv2.imwrite(os.path.join(folder, filename), crop)
    return f"{upload_id}/{filename}"


def build_review_rows(path, ocr_fn, templates, upload_id=None, progress=None):
    """Run steps 1-7 on one uploaded file. No database access.

    ocr_fn(image) -> [{"text", "confidence"}, ...]   (ocr_engine.extract_text_from_array)
    templates     -> saved grid template payloads    (template_store.load_template_payloads)

    Returns {
      "upload_id", "thresholds",
      "image_quality": {"rule_id": "IQ-01", "passed", "warnings": [...],
                        "pages": [{"page", ...assess_image_quality()}]},
      "pages": [{"page", "parity", "template", "match_score", "rows", "error"}],
      "rows": [{"spread", "row", "pages", "fields": [field, ...]}],
    }
    progress(fraction, message), if given, is called as the work advances
    (fraction 0-1, message in plain words for the person waiting).

    where each field is {"category", "page", "row", "column", "bbox",
    "raw_text", "confidence", "tokens", "ocr_error", "possibly_incomplete",
    "status", "value", "crop", "target_fields"}.
    """
    upload_id = upload_id or uuid.uuid4().hex
    detector = TemplateAutoDetector()

    iq_pages, page_reports = [], []
    rows_by_key = {}
    spread = -1
    carried_rows = None  # odd page's rows, as fractions of page height
    carried_rules = None  # odd page's rows in pixels + its ruled lines

    report_progress = progress or (lambda fraction, message: None)
    report_progress(0.0, "Opening the scan")
    pages = load_pages(path)
    page_count = len(pages)

    for page_index, (page_number, image, parity) in enumerate(pages):
        report_progress(page_index / page_count, f"Finding the rows on page {page_number} of {page_count}")
        iq = assess_image_quality(image)
        iq_pages.append({"page": page_number, **iq})
        for warning in iq["warnings"]:
            logger.warning("%s page %s: %s", IQ_RULE_ID, page_number, warning)

        report = {"page": page_number, "parity": parity, "template": None,
                  "match_score": None, "rows": 0, "alignment": None, "error": None}
        page_reports.append(report)

        template, score = match_templates(templates, analyze_document_layout(image), page_parity=parity)
        report["match_score"] = score
        if template is None or score is None or score < config.TEMPLATE_MATCH_THRESHOLD:
            report["error"] = (
                "No saved grid template matches this page "
                f"(best score {score or 0:.2f}, needs {config.TEMPLATE_MATCH_THRESHOLD:.2f}). "
                "Calibrate a template for this page layout first."
            )
            carried_rows = carried_rules = None
            continue
        report["template"] = template.get("filename") or template.get("name")

        height = image.shape[0]
        ruled_lines = detect_ruling_lines(image)["horizontal"]
        paired = parity == "even" and carried_rows is not None
        if not paired:
            spread += 1
        forced_rows = None
        if paired:
            # Map the odd page's rows across by ruled line (the two halves
            # of a scanned spread are often vertically offset); fall back
            # to the same fraction of page height.
            if carried_rules:
                forced_rows = map_rows_between_pages(carried_rules["rows"], carried_rules["lines"], ruled_lines)
            if forced_rows is None:
                forced_rows = [{"y": r["yFrac"] * height, "height": r["heightFrac"] * height,
                                "spacing": r["spacingFrac"] * height} for r in carried_rows]

        placement = detector.auto_place_template(
            image, template, auto_align=True, forced_rows=forced_rows,
            rows_start_y=None if paired else _first_entry_line(template, ruled_lines, height),
        )
        if not placement.get("success"):
            report["error"] = "The template could not be placed on this page."
            carried_rows = carried_rules = None
            continue
        report["rows"] = len(placement["rows"])
        report["alignment"] = placement.get("alignment")
        carried_rows = [
            {"yFrac": r["y"] / height, "heightFrac": r["height"] / height,
             "spacingFrac": r.get("spacing", 0) / height}
            for r in placement["rows"]
        ] if parity == "odd" else None
        carried_rules = {"rows": placement["rows"], "lines": ruled_lines} if parity == "odd" else None

        cell_count = max(1, len(placement["cells"]))
        for cell_index, cell_data in enumerate(placement["cells"]):
            report_progress((page_index + (cell_index + 1) / cell_count) / page_count,
                            f"Reading page {page_number} of {page_count}")
            category = _page_category_for_column(template, cell_data["column"])
            if category is None:
                continue
            cell = Cell(row=cell_data["row"], column=cell_data["column"],
                        x1=cell_data["x1"], y1=cell_data["y1"], x2=cell_data["x2"], y2=cell_data["y2"])
            crop = extract_crop_from_cell(image, cell)
            if crop is None:
                continue

            raw_text, confidence, tokens, ocr_error, flags = ocr_cell(crop, ocr_fn)
            status = field_status(category, confidence, flags)
            key = (spread, cell.row)
            row = rows_by_key.setdefault(key, {"spread": spread, "row": cell.row, "pages": [], "fields": []})
            if page_number not in row["pages"]:
                row["pages"].append(page_number)
            row["fields"].append({
                "category": category,
                "page": page_number,
                "row": cell.row,
                "column": cell.column,
                "bbox": [round(cell.x1), round(cell.y1), round(cell.x2), round(cell.y2)],
                "raw_text": raw_text,
                "confidence": confidence,
                "tokens": tokens,
                "ocr_error": ocr_error,
                "possibly_incomplete": flags["incomplete"],
                "status": status,
                # Manual-encoding fields start empty: the reviewer must type
                # them - low-confidence OCR text is shown, never pre-filled.
                "value": "" if status == MANUAL else raw_text,
                "crop": _save_crop(crop, upload_id, page_number, cell.row, cell.column),
                "target_fields": case_bridge.target_fields(category),
            })

    rows = _drop_non_patient_rows([rows_by_key[k] for k in sorted(rows_by_key)])
    for report in page_reports:
        if report["error"]:
            logger.warning("Page %s skipped: %s", report["page"], report["error"])

    iq_warnings = [f"Page {p['page']}: {w}" for p in iq_pages for w in p["warnings"]]
    return {
        "upload_id": upload_id,
        "thresholds": thresholds(),
        "image_quality": {
            "rule_id": IQ_RULE_ID,
            "passed": not iq_warnings,
            "warnings": iq_warnings,
            "pages": iq_pages,
        },
        "pages": page_reports,
        "rows": rows,
    }


def _is_header_row(row):
    hits = sum(1 for f in row["fields"] if _HEADER_RE.search(f["raw_text"]))
    return hits >= 2


def _drop_non_patient_rows(rows):
    kept = []
    leading = {}
    for row in rows:
        # Only a spread's first few rows can be its printed header.
        position = leading.setdefault(row["spread"], 0)
        leading[row["spread"]] += 1
        if position < _HEADER_SEARCH_ROWS and _is_header_row(row):
            continue
        filled = sum(1 for f in row["fields"] if f["raw_text"])
        if filled < config.REVIEW_MIN_FILLED_FIELDS:
            continue
        kept.append(row)
    return kept


def session_values(fields):
    """reviewed_values dict (category -> text) from a row's fields."""
    return {f["category"]: f["value"] for f in fields}


def persist_review_rows(result, source_document):
    """One pending case_sessions row per patient row. Returns the session
    ids, in row order, and records each on its row as "session_id"."""
    import case_session_store

    ids = []
    for row in result["rows"]:
        values = session_values(row["fields"])
        page_numbers = set(row["pages"])
        ocr_data = {
            "thresholds": result["thresholds"],
            "image_quality": {
                **{k: v for k, v in result["image_quality"].items() if k != "pages"},
                "warnings": [w for p in result["image_quality"]["pages"] if p["page"] in page_numbers
                             for w in (f"Page {p['page']}: {x}" for x in p["warnings"])],
                "pages": [p for p in result["image_quality"]["pages"] if p["page"] in page_numbers],
            },
            "fields": row["fields"],
        }
        ocr_data["image_quality"]["passed"] = not ocr_data["image_quality"]["warnings"]
        session_id = case_session_store.create_ocr_session(
            values.get(case_bridge.CASE_NUMBER, ""), values, ocr_data,
            source_document, result["upload_id"], row["row"],
        )
        row["session_id"] = session_id
        ids.append(session_id)
    return ids


def apply_review(ocr_data, submitted_values, defer_manual=False, submitted_parts=None):
    """Merge a reviewer's submitted values into a session's OCR fields.

    Every MANUAL field must have been typed (non-blank) - unless
    defer_manual is set ("Send to Forms"), in which case only the logbook
    columns a claim can't be created without
    (field_catalog.OCR_CLAIM_REQUIRED_CATEGORIES) must be typed here and the
    rest are left blank, marked "deferred_to_forms", for staff to type on the
    PClaimAssist forms. A missing key keeps the field's current value.

    submitted_parts ({category: parts}, see philhealth/review_fields.py) are
    the structured inputs - name boxes, date/time pickers. When given for a
    field they win over submitted_values: the stored text is composed from
    them and the claim is later built from the parts directly. Callers check
    them with review_fields.check() first.
    Returns (values, ocr_data, missing_categories) - the caller rejects the
    submission if missing_categories is non-empty.
    """
    fields = [dict(f) for f in (ocr_data or {}).get("fields", [])]
    submitted_values = dict(submitted_values or {})
    for category, parts in (submitted_parts or {}).items():
        submitted_values[category] = review_fields.compose_text(category, review_fields.normalize(category, parts))
    missing = []
    for field in fields:
        category = field["category"]
        if category in (submitted_parts or {}):
            field["parts"] = review_fields.normalize(category, submitted_parts[category])
            field["parts_reviewed"] = True
            # Staff confirmed the logbook box is blank: nothing to type,
            # here or on the forms.
            field["marked_empty"] = review_fields.is_marked_empty(field["parts"])
        if category in submitted_values:
            new_value = str(submitted_values[category] or "").strip()
            field["edited"] = new_value != (field.get("raw_text") or "")
            field["value"] = new_value
        blank = not str(field.get("value") or "").strip()
        field["deferred_to_forms"] = False
        if field["status"] == MANUAL and blank and not field.get("marked_empty"):
            if defer_manual and category not in field_catalog.OCR_CLAIM_REQUIRED_CATEGORIES:
                field["deferred_to_forms"] = True
            else:
                missing.append(category)
    values = session_values(fields)
    # Categories the reviewer added that OCR had no cell for (shouldn't
    # happen with a matching template, but never drop typed data).
    for category, value in submitted_values.items():
        values.setdefault(category, str(value or "").strip())
    return values, {**(ocr_data or {}), "fields": fields}, missing
