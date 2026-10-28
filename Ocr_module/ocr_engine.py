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
import numpy as np
from paddleocr import PaddleOCR
from paddleocr.tools.infer.predict_system import sorted_boxes
from paddleocr.tools.infer.utility import get_rotate_crop_image

logger = logging.getLogger(__name__)

_ocr_instance = None

# PaddleOCR's angle classifier turns a text line it takes for upside down
# by 180 degrees before reading it. A logbook cell is never upside down - a
# page only matches its logbook setup's printed columns the right way up -
# but short handwritten digits look much the same either way up, so dates
# were often flipped and read as nonsense: 04-24-94 came out "hb-hZ-ho"
# (each digit upside down, in reverse order), 09-14-26 "92-h1-b0". The
# logbook readers below (cells, row strips, the AI second look) therefore
# read every line as it is. extract_text() keeps the classifier for
# arbitrary images.
FLIP_UPSIDE_DOWN_LINES = False

# The PaddleOCR models, kept in the repository (ocr_models/, 16 MB) so every
# groupmate's PC reads with exactly the same models and needs no internet
# on first run. They are the models paddleocr 2.8.1 downloads for lang="en"
# (to ~/.paddleocr); if the folder is missing, PaddleOCR downloads them.
_MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_models")
_MODEL_DIRS = {
    "det_model_dir": os.path.join(_MODELS, "en_PP-OCRv3_det_infer"),
    "rec_model_dir": os.path.join(_MODELS, "en_PP-OCRv4_rec_infer"),
    "cls_model_dir": os.path.join(_MODELS, "ch_ppocr_mobile_v2.0_cls_infer"),
}


def get_ocr_engine():
    """Return the shared PaddleOCR instance, creating it on first use."""
    global _ocr_instance
    if _ocr_instance is None:
        bundled = {k: v for k, v in _MODEL_DIRS.items()
                   if os.path.isfile(os.path.join(v, "inference.pdmodel"))}
        logger.info("Loading PaddleOCR model (use_angle_cls=True, lang=en, cpu, %s)...",
                    "models from ocr_models/" if len(bundled) == 3 else "downloaded models")
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=False,
            show_log=False,
            **(bundled if len(bundled) == 3 else {}),
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


def extract_tokens_from_array(image):
    """OCR an in-memory (numpy array) image -> [{"text", "confidence", "box"}],
    box being the token's four corner points [[x, y], ...] in image pixels.

    Unlike extract_text_from_array(), errors propagate: the logbook review
    pipeline must not mistake an OCR failure for an empty cell."""
    result = get_ocr_engine().ocr(image, cls=FLIP_UPSIDE_DOWN_LINES)
    tokens = []
    if result and result[0]:
        for item in result[0]:
            tokens.append({
                "text": item[1][0],
                "confidence": round(item[1][1], 2),
                "box": [[float(x), float(y)] for x, y in item[0]],
            })
    return tokens


def read_versions_many(jobs):
    """Batch OCR for many small images (logbook cells) at once.

    jobs: [(image, [version, ...]), ...] - each version is the image itself
    or an enhanced copy of it (same picture, possibly resized). Returns, per
    job, per version, tokens like extract_tokens_from_array().

    Same PaddleOCR models and steps as extract_tokens_from_array(), but the
    text lines are found once per image (on the image itself) and cut from
    every version, and all lines of all jobs are read in one batched call.
    Finding lines takes about a third of a single ocr() call and reading
    them two thirds, mostly per-call overhead: batching makes reading a
    line about twice as fast, and versions skip finding lines altogether.
    Errors propagate, as in extract_tokens_from_array().
    """
    engine = get_ocr_engine()
    lines, owners = [], []
    for job_index, (image, versions) in enumerate(jobs):
        boxes = engine.text_detector(image)[0]
        boxes = sorted_boxes(boxes) if boxes is not None and len(boxes) else []
        for version_index, version in enumerate(versions):
            scale = np.array([version.shape[1] / image.shape[1], version.shape[0] / image.shape[0]],
                             dtype=np.float32)
            for box in boxes:
                box = (np.array(box, dtype=np.float32) * scale).astype(np.float32)
                lines.append(get_rotate_crop_image(version, box))
                owners.append((job_index, version_index, box))
    results = [[[] for _ in versions] for _, versions in jobs]
    if not lines:
        return results
    if FLIP_UPSIDE_DOWN_LINES:
        lines, _, _ = engine.text_classifier(lines)
    readings, _ = engine.text_recognizer(lines)
    for (job_index, version_index, box), (text, confidence) in zip(owners, readings):
        if confidence < engine.drop_score:
            continue  # what ocr() drops too
        results[job_index][version_index].append({
            "text": text,
            "confidence": round(float(confidence), 2),
            "box": [[float(x), float(y)] for x, y in box],
        })
    return results


def read_many(images):
    """extract_tokens_from_array() for many images, batched
    (read_versions_many)."""
    return [versions[0] for versions in read_versions_many([(image, [image]) for image in images])]


def extract_text_from_array(image):
    """Extract text from an in-memory (numpy array) image.

    Moved here from app.py, where it lived as a module-level helper used only
    by the /process_pdf_batch route's OCR callback. Behavior is unchanged:
    any OCR error is logged and returned as no tokens.
    """
    try:
        return extract_tokens_from_array(image)
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
