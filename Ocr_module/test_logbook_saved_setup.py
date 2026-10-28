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


if __name__ == "__main__":
    unittest.main()
