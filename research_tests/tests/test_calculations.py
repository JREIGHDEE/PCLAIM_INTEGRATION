"""The research tests' own calculations, on hand-made numbers."""
import unittest

from research_tests import correction_metrics as cm
from research_tests import field_mapping as fm
from research_tests import handwriting as hw
from research_tests import user_sessions as us
from research_tests import validation as val
from research_tests.common import answer_key, stats


class CorrectionMetricTests(unittest.TestCase):
    def cell(self, truth, raw, corrected, field="Reason for admission"):
        return {"field": field, "truth": truth, "paddle_raw": raw, "paddle_corrected": corrected,
                "tesseract_raw": None, "tesseract_corrected": None}

    def test_outcomes(self):
        self.assertEqual(cm.judge(self.cell("LABOR PAINS", "LAB0R PAINS", "LABOR PAINS"), "paddle")["outcome"], "helpful")
        self.assertEqual(cm.judge(self.cell("LABOR PAINS", "LABOR PAINS", "LABOUR PAINS"), "paddle")["outcome"], "harmful")
        self.assertEqual(cm.judge(self.cell("LABOR PAINS", "LABR", "LABOUR"), "paddle")["outcome"], "other")
        self.assertIsNone(cm.judge(self.cell("X", "X", "X"), "tesseract"))

    def test_capitals_alone_are_not_a_change(self):
        j = cm.judge(self.cell("LABOR PAINS", "labor  pains", "LABOR PAINS"), "paddle")
        self.assertFalse(j["changed"])
        self.assertEqual(j["outcome"], "unchanged")

    def test_equations(self):
        cells = [self.cell("A B", "A 8", "A B"),        # helpful
                 self.cell("A B", "A B", "A C"),        # harmful
                 self.cell("A B", "X", "Y"),            # changed, still wrong
                 self.cell("A B", "A B", "A B")]        # unchanged
        m = cm.metrics([cm.judge(c, "paddle") for c in cells])
        self.assertEqual((m["n"], m["changes"], m["produced_correct"], m["harmful"]), (4, 3, 1, 1))
        self.assertEqual(m["exact_raw"], 50.0)             # 2 of 4 right before
        self.assertEqual(m["exact_corrected"], 50.0)       # 2 of 4 right after
        self.assertEqual(m["exact_gain"], 0.0)
        self.assertAlmostEqual(m["precision"], round(1 / 3, 4))      # Eq. 3.3
        self.assertAlmostEqual(m["harmful_rate"], round(1 / 3, 4))   # Eq. 3.4


class BlankCellRuleTests(unittest.TestCase):
    def test_blank_truth_and_false_readings(self):
        self.assertTrue(cm.is_blank({"truth": "  "}))
        self.assertFalse(cm.is_blank({"truth": "X"}))
        self.assertTrue(cm.false_reading("|"))
        self.assertFalse(cm.false_reading("   "))
        self.assertFalse(cm.false_reading(None))         # the engine did not run

    def test_recomputed_accuracy_leaves_blank_cells_out(self):
        cells = [{"field": "Delivered", "truth": "", "paddle_raw": "", "paddle_corrected": "",
                  "tesseract_raw": "|", "tesseract_corrected": "|"},
                 {"field": "Reason for admission", "truth": "LABOR PAINS", "paddle_raw": "LABOR PAINS",
                  "paddle_corrected": "LABOR PAINS", "tesseract_raw": "LAB", "tesseract_corrected": "LAB"}]
        nonblank = [c for c in cells if not cm.is_blank(c)]
        exact = cm.variant_accuracy(nonblank)[:4]
        self.assertEqual(exact, [100.0, 100.0, 0.0, 0.0])
        including = cm.variant_accuracy(cells)[:4]        # the workbook's original counting
        self.assertEqual(including, [100.0, 100.0, 0.0, 0.0])
        self.assertEqual(cm.variant_accuracy(cells)[4], 100.0)   # Paddle: blank read blank scores 100 there


class HandwritingTests(unittest.TestCase):
    def line(self, page, row, detected=True, truth="X", exact=True, acc=100.0):
        line = {"page": page, "row": row, "detected": detected, "blank": not truth, "truth": truth}
        if detected:
            for v in hw.VARIANTS:
                line[v] = truth if exact else "?"
                line[f"{v}_exact"], line[f"{v}_accuracy"] = exact, acc
        return line

    def test_detection_counts_entries_across_both_pages(self):
        lines = [self.line(1, 1), self.line(2, 1), self.line(1, 2, detected=False), self.line(2, 2, detected=False)]
        self.assertEqual(hw.detection(lines), (2, 1, 50.0))

    def test_blank_and_undetected_cells_are_not_scored(self):
        lines = [self.line(1, 1, exact=True), self.line(1, 2, exact=False, acc=50.0), self.line(1, 3, truth=""),
                 self.line(1, 4, detected=False)]
        scores = hw.variant_scores(lines)
        self.assertEqual(scores["paddle_raw"], (50.0, 75.0))


class FieldMappingTests(unittest.TestCase):
    P = {"Birthday": "2003-06-12", "Admitted date": "2026-10-01", "Admitted hour": "8", "Admitted minute": "05",
         "Admitted AM/PM": "AM", "Last name": "dela  cruz"}

    def row(self, column, fmt, pos=""):
        return {"Answer-key value": column, "Format": fmt, "Position": pos}

    def test_formats(self):
        self.assertEqual(fm.expected_value(self.row("Last name", "text"), self.P), "DELA CRUZ")
        self.assertEqual(fm.expected_value(self.row("Birthday", "date"), self.P), "06-12-2003")
        self.assertEqual(fm.expected_value(self.row("Birthday", "date_digit", "3"), self.P), "1")
        self.assertEqual(fm.expected_value(self.row("Admitted time", "time_digit", "2"), self.P), "8")
        self.assertEqual(fm.expected_value(self.row("Admitted time", "time_ampm"), self.P), "8:05 AM")
        self.assertEqual(fm.expected_value(self.row("Admitted time", "time", "PM"), self.P), "")
        self.assertEqual(fm.expected_value(self.row("Admitted AM/PM", "tick", "AM"), self.P), fm.TICK)
        self.assertEqual(fm.expected_value(self.row("Admitted AM/PM", "tick", "PM"), self.P), "")

    def test_box_purpose_comes_from_its_key_not_its_value(self):
        spot = {"key": "dateAdmittedD3", "digitKey": "dateAdmitted", "computed": "", "digit": 2, "unless": "",
                "checkbox": False, "checkValue": None, "amPmCheck": "", "timeComponent": ""}
        self.assertEqual(fm.source_of(spot)[:3], ("Admitted date", "date_digit", "3"))
        self.assertIsNone(fm.source_of(dict(spot, key="hciPAN", digitKey="")))


class ValidationScoringTests(unittest.TestCase):
    def test_tp_fp_fn_with_allowed_consequences(self):
        rec = {"fired": ["IC-03", "IC-08", "IF-04"],
               "errors": [val.BY_KEY["IC-dis-before"], val.BY_KEY["MF-pin"]]}
        s = val.score(rec)
        self.assertEqual((s["tp"], s["fn"], s["fp"], s["consequence"]), ({"IC-03"}, {"MF-02"}, {"IF-04"}, {"IC-08"}))

    def test_forty_errors_are_placed_where_they_can_be_detected(self):
        instances = val.ERRORS + [dict(val.BY_KEY[k], key=k) for k in val.SECOND_TIME]
        self.assertEqual(len(instances), 40)
        records = [{"record": f"S{i:02d}", "has": {"csf", "cf1", "cf2"} | ({"cf4", "delivery"} if i % 3 == 0 else set())}
                   for i in range(20)]
        slots = val.assign(instances, records, val.SEED)
        by = {r["record"]: r for r in records}
        for record, errors in slots.items():
            self.assertEqual(len(errors), 2)
            self.assertFalse(errors[0]["touches"] & errors[1]["touches"])
            for e in errors:
                self.assertLessEqual(e["needs"], by[record]["has"])

    def test_the_not_seeded_list_names_the_rules_and_why(self):
        rules = {r for r, _, _ in val.NOT_SEEDED}
        self.assertTrue({"IC-01", "IC-02", "IC-07", "MF-08"} <= rules)
        seeded = {r for e in val.ERRORS for r in e["required"]}
        self.assertFalse(seeded & {"IC-01", "IC-02", "IC-07", "MF-08"})


class SessionTests(unittest.TestCase):
    def test_equations(self):
        p = us.participant({"Participant ID": "U1", "Manual Claims": 2, "Manual Time (s)": 1200, "Manual Errors": 4,
                            "System Claims": 2, "System Time (s)": 300, "System Errors": 1,
                            "Suggestions Shown": 20, "Suggestions Accepted": 15})
        self.assertEqual((p["manual_time"], p["system_time"], p["time_reduction"]), (600.0, 150.0, 75.0))
        self.assertEqual((p["manual_errors"], p["system_errors"], p["error_reduction"]), (2.0, 0.5, 75.0))
        self.assertEqual(p["acceptance"], 75.0)
        self.assertIsNone(us.reduction(0, 1))

    def test_sus(self):
        self.assertEqual(us.sus_score([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]), 100.0)
        self.assertEqual(us.sus_score([3] * 10), 50.0)


class HelperTests(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(answer_key.iso_date("10-02-2026"), "2026-10-02")
        self.assertEqual(answer_key.iso_date("2026-10-02"), "2026-10-02")
        self.assertEqual(answer_key.display_date("2026-10-02"), "10-02-2026")
        self.assertEqual(answer_key._time_parts("20:30", ""), ("8", "30", "PM"))

    def test_stats(self):
        self.assertEqual(stats.median([1, 3, 100]), 3)
        self.assertEqual(stats.value_range([2, 5]), "2.00 - 5.00")
        self.assertEqual(stats.f1(1.0, 0.5), round(2 / 3, 4))


if __name__ == "__main__":
    unittest.main()
