"""Fills the real CF2/CSF PhilHealth PDF templates with mapped claim data.

Uses PyMuPDF (fitz, already a project dependency - see requirements.txt),
reusing the exact field coordinates PClaimAssist's own client-side export
(js/pdf/pdf-overlay.js::exportFilledPDF, via js/pdf/overlays/*.js) already
calibrated against these templates - see philhealth/overlays/.

Coordinate note: PClaimAssist's exportFilledPDF uses pdf-lib, which places
text in PDF's native bottom-up coordinate space
(`y = height - (top% * height) - baselineOffset`). PyMuPDF's Page API uses a
top-down space instead (y increases downward from the page's top edge), so
the same "top percent of page" position is `y = (top% * height) +
baselineOffset` here - the offset direction flips along with the axis, the
on-page result is the same.
"""
import fitz  # PyMuPDF

import config
from philhealth.field_catalog import resolve_computed_value
from philhealth.mapping_service import build_flat_data
from philhealth.overlays import OVERLAYS

TEMPLATE_FILENAMES = {"cf2": "CF2.pdf", "csf": "CSF.pdf"}

# Matches the baselineOffset constant in PClaimAssist/js/pdf/pdf-overlay.js.
BASELINE_OFFSET = 6

_FONT = "helv"
_COLOR = (0, 0, 0)


def _draw_field(page, field, value, page_width, page_height):
    if not value:
        return
    text = str(value)
    fontsize = field.get("fs", 8)
    x = (field["left"] / 100) * page_width
    y = (field["top"] / 100) * page_height + BASELINE_OFFSET
    box_width = (field["w"] / 100) * page_width

    text_width = fitz.get_text_length(text, fontname=_FONT, fontsize=fontsize)
    if text_width <= box_width:
        page.insert_text((x, y), text, fontsize=fontsize, fontname=_FONT, color=_COLOR)
        return

    # Longer than its box (e.g. a full diagnosis sentence) - wrap within the
    # field instead of silently overflowing past its right edge or cutting
    # it off. Bounded to a handful of lines so it can't bleed into
    # unrelated parts of the form.
    rect = fitz.Rect(x, y - fontsize, x + box_width, y - fontsize + fontsize * 6)
    page.insert_textbox(rect, text, fontsize=fontsize, fontname=_FONT, color=_COLOR)


def export_claim_pdf(form_key, patient=None, encounter=None, claims_row=None):
    """Returns the filled PDF (bytes) for `form_key` ('cf2' or 'csf').

    Callers are expected to have already validated required fields (see
    mapping_service.map_claim()["forms"][form_key]) - this function fills
    whatever values it's given and does not itself block on missing data.
    """
    if form_key not in OVERLAYS:
        raise ValueError(f"Unknown/unsupported PhilHealth form '{form_key}'")

    template_path = config.PHILHEALTH_FORMS_DIR / TEMPLATE_FILENAMES[form_key]
    if not template_path.exists():
        raise FileNotFoundError(f"PhilHealth form template not found: {template_path}")

    data = build_flat_data(patient, encounter, claims_row)

    doc = fitz.open(template_path)
    try:
        for field in OVERLAYS[form_key]:
            value = resolve_computed_value(field.get("computed") or field["key"], data)
            page = doc[field["page"] - 1]
            rect = page.rect
            _draw_field(page, field, value, rect.width, rect.height)
        return doc.tobytes()
    finally:
        doc.close()
