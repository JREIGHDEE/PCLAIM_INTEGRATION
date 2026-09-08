"""
Shared image/PDF loading for the OCR engine benchmark.

Each test file is decoded exactly once here and the identical in-memory
array is then handed to every engine under comparison - this matters for
fairness, since decoding the same file twice (once per engine) could in
principle produce slightly different arrays depending on how each engine's
own loader handles color/orientation.
"""
import os

import cv2
import fitz
import numpy as np

import config

IMAGE_EXTENSIONS = config.ALLOWED_IMAGE_EXTENSIONS
PDF_EXTENSIONS = config.ALLOWED_PDF_EXTENSIONS


def _render_pdf_pages(path):
    """Yield (display_name, BGR ndarray) for every page for one PDF file."""
    filename = os.path.basename(path)
    doc = fitz.open(path)
    try:
        for page_num in range(len(doc)):
            pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = np.frombuffer(pix.samples, dtype=np.uint8)
            img_data = img_data.reshape((pix.height, pix.width, pix.n))

            if pix.n == 4:
                image = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                image = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            else:
                image = img_data

            yield f"{filename}#page{page_num + 1}", image
    finally:
        doc.close()


def iter_test_images(root_dir):
    """Yield (category, display_name, image_or_None) for every supported
    file found recursively under root_dir.

    `category` is the file's top-level subfolder name relative to root_dir
    (e.g. "clean_scans"), or "" if the file sits directly in root_dir. A PDF
    yields one entry per page. `image_or_None` is a BGR numpy array, or None
    if the file couldn't be decoded (the caller is expected to record that
    as an error row rather than skip it silently).
    """
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        return

    for dirpath, _dirnames, filenames in sorted(os.walk(root_dir)):
        for filename in sorted(filenames):
            if filename.startswith(".") or filename.lower() == "readme.md":
                continue

            ext = os.path.splitext(filename)[1].lower()
            full_path = os.path.join(dirpath, filename)
            rel_dir = os.path.relpath(dirpath, root_dir)
            category = "" if rel_dir == "." else rel_dir.split(os.sep)[0]

            if ext in IMAGE_EXTENSIONS:
                image = cv2.imread(full_path)
                yield category, filename, image
            elif ext in PDF_EXTENSIONS:
                try:
                    for display_name, image in _render_pdf_pages(full_path):
                        yield category, display_name, image
                except Exception:
                    yield category, filename, None
