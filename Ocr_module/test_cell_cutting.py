"""Cutting a logbook page into cells (template_engine, logbook_pipeline):
straightening a tilted scan, one row per entry counted in printed lines,
which side of the spread each page is, and fitting the columns.

Pages are drawn here - printed lines, entries of writing - so nothing
needs a real scan or an OCR engine.
"""
import os
import tempfile
import unittest

import cv2
import fitz
import numpy as np

import logbook_pipeline
import template_engine as te

PITCH = 40          # printed line spacing, pixels
FIRST_LINE = 120    # first printed line, under the header
LINES = 38


def ruled_page(entries=11, per_entry=3, blank_spare=True, width=1000, height=1700):
    """A logbook page: printed lines, and `entries` entries of two written
    lines each, starting on the first line, `per_entry` lines apart."""
    page = np.full((height, width, 3), 255, np.uint8)
    for k in range(LINES):
        y = FIRST_LINE + k * PITCH
        cv2.line(page, (0, y), (width, y), (200, 150, 120), 2)       # printed: light blue
    for e in range(entries):
        for line in range(per_entry - 1 if blank_spare else per_entry):
            y = FIRST_LINE + (e * per_entry + line) * PITCH + 28
            cv2.putText(page, "MARIA DELA CRUZ 08-21-26", (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (30, 30, 30), 2)
    return page


def tilt(page, degrees):
    h, w = page.shape[:2]
    turn = cv2.getRotationMatrix2D((w / 2, h / 2), degrees, 1.0)
    return cv2.warpAffine(page, turn, (w, h), borderValue=(255, 255, 255))


class StraighteningTests(unittest.TestCase):
    def test_a_tilted_page_is_straightened_and_its_lines_found_again(self):
        page = ruled_page()
        tilted = tilt(page, 1.3)
        self.assertLess(len(te.detect_ruling_lines(tilted)["horizontal"]), 10)   # the lines hide
        self.assertAlmostEqual(te.estimate_skew(tilted), -1.3, delta=0.15)
        straight, angle = te.deskew(tilted)
        self.assertAlmostEqual(angle, -1.3, delta=0.15)
        self.assertGreaterEqual(len(te.detect_ruling_lines(straight)["horizontal"]), LINES - 2)

    def test_a_level_page_is_left_as_it_is(self):
        page = ruled_page()
        straight, angle = te.deskew(page)
        self.assertEqual(angle, 0.0)
        self.assertIs(straight, page)


class TiltTestTests(unittest.TestCase):
    """The Logbook Reader's tilt test: turn a scan to see how a crooked one
    is read (logbook_pipeline.tilt_scan)."""

    def test_tilting_turns_clockwise_and_keeps_the_corners(self):
        page = ruled_page()
        turned = logbook_pipeline.tilt_image(page, 3)
        self.assertGreater(turned.shape[0], page.shape[0])
        self.assertGreater(turned.shape[1], page.shape[1])
        # Clockwise, so the reader turns it back the other way.
        self.assertAlmostEqual(te.estimate_skew(turned), 3, delta=0.15)

    def test_a_tilted_picture_is_saved_and_straightened_when_read(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = os.path.join(folder, "page.png"), os.path.join(folder, "tilted.png")
            cv2.imwrite(source, ruled_page())
            logbook_pipeline.tilt_scan(source, target, -2)
            angles = []
            pages = logbook_pipeline.load_pages(target, angles)
            self.assertEqual(len(pages), 1)
            self.assertAlmostEqual(angles[0], -2, delta=0.15)

    def test_a_tilted_pdf_stays_a_pdf_of_the_same_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = os.path.join(folder, "scan.pdf"), os.path.join(folder, "tilted.pdf")
            doc = fitz.open()
            for _ in range(2):
                ok, png = cv2.imencode(".png", ruled_page())
                page = doc.new_page(width=500, height=850)
                page.insert_image(page.rect, stream=png.tobytes())
            doc.save(source)
            doc.close()
            logbook_pipeline.tilt_scan(source, target, 1.5)
            before = logbook_pipeline.raw_pages(source)
            angles = []
            after = logbook_pipeline.load_pages(target, angles)
            self.assertEqual([(n, p) for n, _, p in after], [(1, "odd"), (2, "even")])
            # Read at about the size it was scanned, a little larger for the turn.
            self.assertAlmostEqual(after[0][1].shape[1] / before[0][1].shape[1], 1.05, delta=0.05)
            for angle in angles:
                self.assertAlmostEqual(angle, 1.5, delta=0.15)

    def test_the_first_page_picture_is_a_small_jpeg(self):
        with tempfile.TemporaryDirectory() as folder:
            source = os.path.join(folder, "page.png")
            cv2.imwrite(source, ruled_page(width=2000, height=3000))
            picture = logbook_pipeline.first_page_picture(source, width=500)
            image = cv2.imdecode(np.frombuffer(picture, np.uint8), cv2.IMREAD_COLOR)
            self.assertEqual(image.shape[1], 500)


class EntryRowTests(unittest.TestCase):
    def test_lines_filled_in_and_doubles_dropped(self):
        found = [100, 140, 180, 181, 260, 300, 340, 380]     # 220 hidden under writing, 181 a double
        lines, pitch = te.regular_ruled_lines(found, 2000)
        self.assertEqual(pitch, 40)
        self.assertEqual([round(y) for y in lines], [100, 140, 180, 220, 260, 300, 340, 380])

    def test_one_row_per_entry_from_the_header_line(self):
        page = ruled_page(entries=11)
        rows = te.entry_rows_from_ruled_lines(page, te.detect_ruling_lines(page)["horizontal"], FIRST_LINE)
        self.assertEqual(rows["per_entry"], 3)
        self.assertEqual(len(rows["rows"]), 11)
        for e, row in enumerate(rows["rows"]):
            top = FIRST_LINE + e * 3 * PITCH
            self.assertLessEqual(row["y"], top)                       # a little above the entry's first line
            self.assertGreater(row["y"], top - PITCH / 2)
            self.assertGreaterEqual(row["y"] + row["height"], top + 3 * PITCH)   # down to its last line
            self.assertLess(row["y"] + row["height"], top + 3 * PITCH + PITCH / 2)

    def test_lines_per_entry_read_from_the_page(self):
        page = ruled_page(entries=8, per_entry=4)
        rows = te.entry_rows_from_ruled_lines(page, te.detect_ruling_lines(page)["horizontal"], FIRST_LINE)
        self.assertEqual(rows["per_entry"], 4)
        self.assertEqual(len(rows["rows"]), 8)

    def test_the_other_page_of_the_spread_uses_the_same_count(self):
        page = ruled_page(entries=11, blank_spare=False)      # diagnoses fill every line
        rows = te.entry_rows_from_ruled_lines(page, te.detect_ruling_lines(page)["horizontal"], FIRST_LINE,
                                              per_entry=3)
        self.assertEqual((rows["per_entry"], len(rows["rows"])), (3, 11))

    def test_without_a_header_a_start_one_line_off_is_put_right(self):
        page = ruled_page(entries=10)
        # Writing on the line under the header too (a heading's tail): the
        # first written line is one above the first entry.
        cv2.putText(page, "TIME OF ADMISSION", (40, FIRST_LINE - PITCH + 28), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (30, 30, 30), 2)
        cv2.line(page, (0, FIRST_LINE - PITCH), (1000, FIRST_LINE - PITCH), (200, 150, 120), 2)
        lines = te.detect_ruling_lines(page)["horizontal"]
        rows = te.entry_rows_from_ruled_lines(page, lines, None)
        self.assertAlmostEqual(rows["rows"][0]["y"], FIRST_LINE - 0.25 * PITCH, delta=3)

    def test_too_few_printed_lines(self):
        page = np.full((800, 600, 3), 255, np.uint8)
        self.assertIsNone(te.entry_rows_from_ruled_lines(page, [100, 140], 100))


class ColumnFitTests(unittest.TestCase):
    TEMPLATE = [10.0, 131.0, 315.0, 521.0, 700.0, 922.0]

    def test_no_squeezing_to_land_a_double_line(self):
        # A rule drawn twice (175 and 190) once let a fit squeeze every
        # column to 61% to land on both.
        fit = te.fit_lines_to_rules(self.TEMPLATE, [15, 175, 190, 329, 700, 995], 1000)
        self.assertGreater(fit["scale"], 0.8)
        self.assertGreater(fit["lines"][-1], 850)            # ADDRESS keeps its width

    def test_no_column_off_the_page(self):
        fit = te.fit_lines_to_rules(self.TEMPLATE, [171, 688, 994], 1000)
        self.assertTrue(all(-20 <= x <= 1020 for x in fit["lines"]))

    def test_rules_on_the_template_lines_keep_them(self):
        fit = te.fit_lines_to_rules(self.TEMPLATE, [141, 297, 538, 699], 1000)
        self.assertAlmostEqual(fit["scale"], 1.0, delta=0.1)


class PageSideTests(unittest.TestCase):
    LEFT = {"tokens": [{"category": "NAME"}, {"category": "BDAY"}, {"category": "ADDRESS"}]}
    RIGHT = {"tokens": [{"category": "FINAL DIAGNOSIS"}, {"category": "DATE & TIME OF DISCHARGE"}]}

    def test_header_side(self):
        self.assertEqual(logbook_pipeline.header_side(self.LEFT), "odd")
        self.assertEqual(logbook_pipeline.header_side(self.RIGHT), "even")
        self.assertIsNone(logbook_pipeline.header_side(None))

    def test_a_pdf_starting_on_a_right_page(self):
        parities = ["odd", "even", "odd", "even"]
        self.assertEqual(logbook_pipeline.page_sides(parities, [self.RIGHT, self.LEFT, self.RIGHT, None]), 1)
        self.assertEqual(logbook_pipeline.page_sides(parities, [self.LEFT, self.RIGHT, None, None]), 0)
        self.assertEqual(logbook_pipeline.page_sides(parities, [None] * 4), 0)

    def test_a_header_far_down_the_page_is_an_entry(self):
        lines = [74 + 40 * k for k in range(30)]
        self.assertIsNone(logbook_pipeline._header_above_entries({"bottom": 233}, lines, 1600))
        self.assertIsNotNone(logbook_pipeline._header_above_entries({"bottom": 69}, lines, 1600))


if __name__ == "__main__":
    unittest.main()
