"""
Normalized OCR engine adapters for the benchmark.

Both adapters take the SAME in-memory BGR image array and return a list of
regions in the SAME shape:

    {"text": str, "confidence": float in [0, 1], "bbox": [x1, y1, x2, y2]}

so PaddleOCR and Tesseract can be compared apples-to-apples on region count,
confidence, and text - without either engine's native output format leaking
into the comparison. Neither adapter modifies or duplicates the production
OCR code:

- run_paddle() calls ocr_engine.get_ocr_engine() - the exact same lazily
  loaded singleton the production /ocr route uses - and only adds bounding
  boxes on top (PaddleOCR's raw result already includes them; ocr_engine.py's
  own extract_text() just doesn't keep them, since production has never
  needed them).
- run_tesseract() reuses ocr_tesseract._configure_tesseract() so TESSERACT_CMD
  is honored the same way as the standalone ocr_tesseract.py module.
"""
import cv2
import pytesseract

import ocr_tesseract
from ocr_engine import get_ocr_engine


def run_paddle(image):
    raw = get_ocr_engine().ocr(image, cls=True)

    regions = []
    if raw and raw[0]:
        for box, (text, conf) in raw[0]:
            xs = [point[0] for point in box]
            ys = [point[1] for point in box]
            regions.append({
                "text": text,
                "confidence": round(float(conf), 4),
                "bbox": [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))],
            })
    return regions


def run_tesseract(image):
    ocr_tesseract._configure_tesseract()
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    data = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT)

    regions = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if not text or conf < 0:
            continue

        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        regions.append({
            "text": text,
            "confidence": round(conf / 100.0, 4),
            "bbox": [float(x), float(y), float(x + w), float(y + h)],
        })
    return regions


# The "ocr_engine = paddle | tesseract" selector Phase 2 asked for - kept at
# the benchmark layer rather than wired into the Flask routes, since nothing
# in this preparation phase needs production request handling to switch
# engines (see benchmarks/README.md for the reasoning).
ENGINES = {
    "paddle": run_paddle,
    "tesseract": run_tesseract,
}
