"""
OCR processing - Tesseract (via pytesseract) wrapper.

Mirrors ocr_engine.py's function names/shapes (extract_text /
extract_text_from_array / extract_pdf_text -> list of {"text", "confidence"}
tokens) so this engine is a drop-in alternative for anything written against
that interface, without touching ocr_engine.py or the production PaddleOCR
pipeline at all. Nothing in routes/ imports this module - it exists for the
benchmarking tool in benchmarks/ and for standalone manual testing.

Requires the Tesseract OCR executable to be installed separately from this
Python package - see benchmarks/README.md. Set TESSERACT_CMD in .env if it's
not already on PATH.
"""
import logging
import os
import tempfile

import cv2
import fitz
import numpy as np
import pytesseract

import config

logger = logging.getLogger(__name__)

_configured = False


def _configure_tesseract():
    """Point pytesseract at a specific tesseract.exe if TESSERACT_CMD is set.

    Safe to call repeatedly - only applies the setting once.
    """
    global _configured
    if _configured:
        return
    if config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    _configured = True


def _extract_from_array(image):
    """Run Tesseract on a BGR (OpenCV-order) numpy array.

    Converted to RGB before handing it to pytesseract, which otherwise
    interprets a raw ndarray's channels as already being RGB (PIL.Image.
    fromarray semantics) - without this, colors are swapped relative to
    what PaddleOCR sees for the same file, which would bias any comparison
    between the two engines.
    """
    _configure_tesseract()
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    data = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT)

    tokens = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        # Tesseract marks non-text detections (e.g. layout blocks) with
        # conf == -1; skip those and blank words, same as PaddleOCR's tokens
        # only ever containing detections with actual recognized text.
        if not text or conf < 0:
            continue
        tokens.append({
            "text": text,
            "confidence": round(conf / 100.0, 2),  # normalize to Paddle's 0-1 scale
        })
    return tokens


def extract_text(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise Exception(f"Could not load image: {image_path}")

    return _extract_from_array(img)


def extract_text_from_array(image):
    """Extract text from an in-memory (numpy array) image.

    Mirrors ocr_engine.extract_text_from_array: never raises, returns []
    on failure so a caller looping over many images doesn't abort the batch.
    """
    try:
        return _extract_from_array(image)
    except Exception:
        logger.exception("Tesseract extraction from image array failed")
        return []


def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)

    all_tokens = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"tesseract_page_{page_num}.png"
        )

        pix.save(temp_path)

        page_tokens = extract_text(temp_path)

        all_tokens.extend(page_tokens)

        if os.path.exists(temp_path):
            os.remove(temp_path)

    doc.close()

    return all_tokens


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "test.jpg"

    tokens = extract_text(path)

    for token in tokens:
        print(token["text"])
