"""Tests for logbook_layout: header words, where entries start, and the
columns the guided setup proposes (no OCR - header words are given)."""
import unittest

import logbook_layout as L


def _word(text, x0, x1, y0=30, y1=60):
    return {"text": text, "x0": x0, "x1": x1, "y0": y0, "y1": y1, "category": L.header_category(text)}


class HeaderCategoryTests(unittest.TestCase):
    def test_printed_headings_despite_ocr_slips(self):
        self.assertEqual(L.header_category("case#"), "CASE #")
        self.assertEqual(L.header_category("adsmission"), "DATE & TIME OF ADMISSION")
        self.assertEqual(L.header_category("nAmE"), "NAME")
        self.assertEqual(L.header_category("DISCHARGE"), "DATE & TIME OF DISCHARGE")
        self.assertEqual(L.header_category("FinAL"), "FINAL DIAGNOSIS")

    def test_entry_words_are_not_headings(self):
        # Close to CASE / DELIVERY, but written in patient entries.
        self.assertIsNone(L.header_category("CARE"))
        self.assertIsNone(L.header_category("2026"))
        self.assertIsNone(L.header_category("PUROK"))


class FirstEntryLineTests(unittest.TestCase):
    def test_ruled_line_under_header(self):
        self.assertEqual(L.first_entry_line([67.0, 107.0, 147.0], 1476, 66.0), 67.0)

    def test_header_lettering_below_its_line_wins(self):
        # The printed header dips under its ruled line: start below the
        # lettering so it isn't read as part of the first patient.
        self.assertEqual(L.first_entry_line([156.0, 196.0, 236.0], 1684, 161.0), 161.0)

    def test_no_header(self):
        self.assertIsNone(L.first_entry_line([67.0, 107.0], 1476, None))


class ProposeColumnsTests(unittest.TestCase):
    width = 1000.0

    def test_columns_from_printed_lines_named_by_headings(self):
        header = {"bottom": 60, "tokens": [
            _word("ADMITTING", 40, 170), _word("DELIVERY", 360, 470),
            _word("FINAL", 590, 660), _word("DISCHARGE", 860, 980)]}
        result = L.propose_columns(self.width, [14, 339, 490, 851, 996], header, "right")
        self.assertEqual(result["lines"], [0.01, 0.339, 0.49, 0.851])
        self.assertEqual(result["categories"], list(L.RIGHT_COLUMNS))

    def test_lost_printed_line_found_from_heading_gap(self):
        # The faint line between CASE # and DATE & TIME wasn't detected; the
        # TIME OF ADMISSION heading also runs a little past its own line.
        header = {"bottom": 66, "tokens": [
            _word("CASE#", 14, 114), _word("TmEFAP", 135, 281),
            _word("nAmE", 324, 414), _word("BDAY", 531, 602), _word("AoOaes", 690, 805)]}
        result = L.propose_columns(self.width, [272, 506, 660, 994], header, "left")
        self.assertEqual(len(result["lines"]), 5)
        self.assertAlmostEqual(result["lines"][1], 0.1245, places=3)
        self.assertEqual(result["lines"][2:], [0.272, 0.506, 0.66])
        self.assertEqual(result["categories"], list(L.LEFT_COLUMNS))

    def test_no_header_uses_usual_order(self):
        result = L.propose_columns(self.width, [150, 300, 550, 700], None, "left")
        self.assertEqual(result["categories"], list(L.LEFT_COLUMNS))

    def test_heading_names_win_over_usual_order(self):
        # A logbook that puts NAME first.
        header = {"bottom": 60, "tokens": [_word("NAME", 40, 120), _word("CASE", 340, 420)]}
        result = L.propose_columns(self.width, [300], header, "left")
        self.assertEqual(result["categories"], ["NAME", "CASE #"])

    def test_guess_side(self):
        left = {"tokens": [_word("CASE", 0, 1), _word("NAME", 2, 3)]}
        right = {"tokens": [_word("FINAL", 0, 1), _word("DISCHARGE", 2, 3)]}
        self.assertEqual(L.guess_side(left), "left")
        self.assertEqual(L.guess_side(right), "right")
        self.assertIsNone(L.guess_side(None))


if __name__ == "__main__":
    unittest.main()
