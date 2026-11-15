"""Tests for reading a scan from the saved logbook setup (logbook_setup:
saved_columns, fit_saved_columns): the setup's columns and names are kept,
only moved onto the scan's printed lines."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config
import logbook_setup


class FitSavedColumnsTests(unittest.TestCase):
    def test_lines_move_onto_nearby_printed_lines(self):
        fitted = logbook_setup.fit_saved_columns([0.01, 0.13, 0.31, 0.52], [0.14, 0.305, 0.80])
        self.assertEqual(fitted, [0.01, 0.14, 0.305, 0.52])

    def test_a_stray_printed_line_adds_no_column(self):
        fitted = logbook_setup.fit_saved_columns([0.01, 0.5], [0.25, 0.5, 0.75])
        self.assertEqual(fitted, [0.01, 0.5])

    def test_lines_stay_in_order_and_on_the_page(self):
        fitted = logbook_setup.fit_saved_columns([0.01, 0.40, 0.41, 0.999], [0.39])
        self.assertEqual(fitted, sorted(fitted))
        self.assertTrue(all(0 <= x < 1 for x in fitted))


class SavedColumnsTests(unittest.TestCase):
    def _write(self, folder, name, parity, created, categories):
        payload = {
            "gridLines": [0.01 + i * 0.1 for i in range(len(categories))],
            "segmentInfo": [{"category": c} for c in categories],
            "created_at": created,
            "metadata": {"pageParity": parity},
        }
        (folder / name).write_text(json.dumps(payload), encoding="utf-8")

    def test_newest_setup_for_each_side(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self._write(folder, "old_left.json", "odd", 1, ["NAME"])
            self._write(folder, "new_left.json", "odd", 2, ["CASE #", "NAME", None])
            self._write(folder, "right.json", "even", 1, ["FINAL DIAGNOSIS"])
            with mock.patch.object(config, "GRID_TEMPLATES_FOLDER", folder):
                found = logbook_setup.saved_columns()
        self.assertEqual(found["left"]["file"], "new_left.json")
        self.assertEqual(found["left"]["categories"], ["CASE #", "NAME", ""])
        self.assertEqual(found["right"]["categories"], ["FINAL DIAGNOSIS"])


class TiltTestTests(unittest.TestCase):
    """The tilt test on the column check page (logbook_setup.tilt_pages):
    the pages of an uploaded scan are turned, each by its own angle, and
    their columns found again; the scan as uploaded is kept."""

    def test_each_page_is_turned_and_read_again(self):
        import cv2
        import fitz
        import numpy as np
        found_on = []

        def propose(image, ocr_fn, side=None):
            found_on.append(image)
            return {"side_found": True, "side": "left", "lines": [0.01], "categories": ["NAME"],
                    "rules": [], "rows": [], "height": 1}

        page = np.full((1700, 1000, 3), 255, np.uint8)
        for y in range(120, 1600, 40):
            cv2.line(page, (0, y), (1000, y), (120, 120, 120), 2)
        with tempfile.TemporaryDirectory() as tmp:
            scan = Path(tmp) / "scan.pdf"
            doc = fitz.open()
            for _ in range(2):
                ok, png = cv2.imencode(".png", page)
                doc.new_page(width=500, height=850).insert_image(fitz.Rect(0, 0, 500, 850), stream=png.tobytes())
            doc.save(str(scan))
            doc.close()
            with mock.patch.object(logbook_setup, "SETUP_FOLDER", Path(tmp) / "setups"), \
                    mock.patch.object(logbook_setup.logbook_layout, "propose_page", propose):
                first = logbook_setup.read_scan(str(scan), None, "scan.pdf")
                self.assertEqual([p["tilt"] for p in first["pages"]], [0.0, 0.0])
                self.assertEqual([p["raw_picture"] for p in first["pages"]], ["raw0.jpg", "raw1.jpg"])
                turned = logbook_setup.tilt_pages(first["setup_id"], [3, 0], None)
                self.assertEqual(turned["setup_id"], first["setup_id"])
                self.assertEqual([p["tilt"] for p in turned["pages"]], [3.0, 0.0])
                self.assertAlmostEqual(turned["pages"][0]["straightened_by"], 3, delta=0.15)
                self.assertEqual(turned["pages"][1]["straightened_by"], 0.0)
                # Turned back to straight: read from the scan as uploaded again.
                back = logbook_setup.tilt_pages(first["setup_id"], 0, None)
                self.assertEqual([p["straightened_by"] for p in back["pages"]], [0.0, 0.0])
                self.assertEqual(len(found_on), 6)


if __name__ == "__main__":
    unittest.main()
