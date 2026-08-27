"""
OCR processing — PaddleOCR wrapper.

The extraction logic (extract_text / extract_pdf_text) is unchanged from the
original main.py. The only behavioral change is *when* the PaddleOCR model
loads: previously it loaded at import time (so simply `import main` anywhere
— including test collection — paid the model-load cost). Now it loads lazily,
once, on first actual use, via get_ocr_engine().
"""
import logging
import os
import tempfile

import cv2
import fitz
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

_ocr_instance = None


def get_ocr_engine():
    """Return the shared PaddleOCR instance, creating it on first use."""
    global _ocr_instance
    if _ocr_instance is None:
        logger.info("Loading PaddleOCR model (use_angle_cls=True, lang=en, cpu)...")
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=False,
            show_log=False,
        )
        logger.info("PaddleOCR model loaded.")
    return _ocr_instance


def extract_text(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise Exception(f"Could not load image: {image_path}")

    result = get_ocr_engine().ocr(img, cls=True)

    tokens = []

    if result and result[0]:
        for item in result[0]:
            text = item[1][0]
            conf = item[1][1]

            tokens.append({
                "text": text,
                "confidence": round(conf, 2)
            })

    return tokens


def extract_text_from_array(image):
    """Extract text from an in-memory (numpy array) image.

    Moved here from app.py, where it lived as a module-level helper used only
    by the /process_pdf_batch route's OCR callback. Behavior is unchanged.
    """
    try:
        result = get_ocr_engine().ocr(image, cls=True)
        tokens = []
        if result and result[0]:
            for item in result[0]:
                text = item[1][0]
                conf = item[1][1]
                tokens.append({
                    "text": text,
                    "confidence": round(conf, 2)
                })
        return tokens
    except Exception:
        logger.exception("OCR extraction from image array failed")
        return []


def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)

    all_tokens = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"ocr_page_{page_num}.png"
        )

        pix.save(temp_path)

        page_tokens = extract_text(temp_path)

        all_tokens.extend(page_tokens)

        if os.path.exists(temp_path):
            os.remove(temp_path)

    doc.close()

    return all_tokens


if __name__ == "__main__":
    path = "test.jpg"

    tokens = extract_text(path)

    for token in tokens:
        print(token["text"])
