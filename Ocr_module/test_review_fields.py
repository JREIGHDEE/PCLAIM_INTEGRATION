"""Tests for the logbook-review inputs and safeguards
(philhealth/review_fields.py) and their use when building a claim.

Same flat-file unittest convention as the other test_*.py files. Pure - no
DB, no Flask, no OCR model.
"""
import unittest
from datetime import date

from philhealth import case_bridge, review_fields
from philhealth.case_bridge import (
    ADDRESS, ADMISSION_DT, BDAY, CASE_NUMBER, DELIVERY_DT, DISCHARGE_DT, FINAL_DX, NAME,
)

TODAY = date(2026, 7, 1)


def _messages(found, category):
    return [p["message"] for p in found if p["category"] == category]


def _row(**overrides):
    parts = {
        CASE_NUMBER: {"number": "2026-4140"},
        NAME: {"last": "Damian", "first": "Mary Deyine", "middle": "Israel", "suffix": ""},
        BDAY: {"date": "1995-05-04"},
        ADDRESS: {"text": "Suraya Homes, Catalunan, Davao City"},
        ADMISSION_DT: {"date": "2026-06-23", "hour": "11", "minute": "15", "am_pm": "AM"},
        DELIVERY_DT: {"date": "2026-06-23", "hour": "8", "minute": "01", "am_pm": "PM"},
        DISCHARGE_DT: {"date": "2026-06-25", "hour": "10", "minute": "00", "am_pm": "AM"},
        FINAL_DX: {"text": "NSD live birth"},
    }
    parts.update(overrides)
    return parts


class SuggestPartsTests(unittest.TestCase):
    def test_case_number_keeps_only_the_numbers(self):
        self.assertEqual(review_fields.suggest_parts(CASE_NUMBER, "2026 / 4140"), {"number": "2026-4140"})
        self.assertEqual(review_fields.suggest_parts(CASE_NUMBER, "20240"), {"number": "20240"})

    def test_logbook_date_and_time_split_into_the_form_inputs(self):
        self.assertEqual(review_fields.suggest_parts(ADMISSION_DT, "06-23-26 11:15am"),
                         {"date": "2026-06-23", "hour": "11", "minute": "15", "am_pm": "AM"})
        self.assertEqual(review_fields.suggest_parts(DISCHARGE_DT, "06/25/2026 3:05 PM"),
                         {"date": "2026-06-25", "hour": "3", "minute": "05", "am_pm": "PM"})

    def test_time_without_am_pm_leaves_am_pm_for_staff(self):
        parts = review_fields.suggest_parts(DELIVERY_DT, "06/23/2026 8:01")
        self.assertEqual((parts["hour"], parts["minute"], parts["am_pm"]), ("8", "01", ""))

    def test_name_without_comma_is_a_flagged_guess(self):
        parts = review_fields.suggest_parts(NAME, "Maria Santos Dela Cruz")
        self.assertEqual((parts["last"], parts["first"], parts["middle"]), ("Dela Cruz", "Maria", "Santos"))
        self.assertTrue(parts["guessed"])
        self.assertFalse(review_fields.suggest_parts(NAME, "Dela Cruz, Maria Santos")["guessed"])

    def test_unreadable_date_suggests_nothing(self):
        self.assertEqual(review_fields.suggest_parts(BDAY, "05-O4-?9"), {"date": ""})


class CheckTests(unittest.TestCase):
    def test_a_normal_row_passes(self):
        self.assertEqual(review_fields.check(_row(), TODAY), ([], []))

    def test_case_number_must_be_numbers(self):
        problems, _ = review_fields.check(_row(**{CASE_NUMBER: {"number": "2O26-4140"}}), TODAY)
        self.assertTrue(_messages(problems, CASE_NUMBER))

    def test_names_only_letters_and_both_last_and_first(self):
        problems, _ = review_fields.check(_row(**{NAME: {"last": "Dam1an", "first": "", "middle": "", "suffix": ""}}), TODAY)
        messages = _messages(problems, NAME)
        self.assertTrue(any("letters" in m for m in messages))
        self.assertTrue(any("last name and the first name" in m for m in messages))
        ok, _ = review_fields.check(_row(**{NAME: {"last": "Dela Cruz-Peña", "first": "Ma. Liza", "middle": "O'Neil", "suffix": "Jr."}}), TODAY)
        self.assertEqual(_messages(ok, NAME), [])

    def test_impossible_and_future_dates(self):
        problems, _ = review_fields.check(_row(**{BDAY: {"date": "1995-02-30"}}), TODAY)
        self.assertTrue(any("not a real date" in m for m in _messages(problems, BDAY)))
        problems, _ = review_fields.check(_row(**{ADMISSION_DT: {"date": "2062-06-23", "hour": "", "minute": "", "am_pm": ""}}), TODAY)
        self.assertTrue(any("future" in m for m in _messages(problems, ADMISSION_DT)))

    def test_time_needs_valid_hour_minutes_and_am_pm(self):
        problems, _ = review_fields.check(_row(**{ADMISSION_DT: {"date": "2026-06-23", "hour": "13", "minute": "5", "am_pm": ""}}), TODAY)
        messages = _messages(problems, ADMISSION_DT)
        self.assertTrue(any("1 to 12" in m for m in messages))
        self.assertTrue(any("AM or PM" in m for m in messages))

    def test_time_without_a_date_is_a_problem(self):
        problems, _ = review_fields.check(_row(**{DELIVERY_DT: {"date": "", "hour": "8", "minute": "01", "am_pm": "PM"}}), TODAY)
        self.assertTrue(_messages(problems, DELIVERY_DT))

    def test_went_home_before_admitted_must_be_fixed(self):
        problems, _ = review_fields.check(_row(**{DISCHARGE_DT: {"date": "2026-06-23", "hour": "9", "minute": "00", "am_pm": "AM"}}), TODAY)
        self.assertTrue(_messages(problems, DISCHARGE_DT))

    def test_unusual_answers_are_warnings_not_problems(self):
        problems, warnings = review_fields.check(_row(**{
            BDAY: {"date": "2019-05-04"},                       # 7 years old
            DELIVERY_DT: {"date": "2026-06-20", "hour": "", "minute": "", "am_pm": ""},  # before admission
        }), TODAY)
        self.assertEqual(problems, [])
        self.assertTrue(any("7 years old" in m for m in _messages(warnings, BDAY)))
        self.assertTrue(_messages(warnings, DELIVERY_DT))

    def test_blank_optional_fields_are_fine(self):
        problems, warnings = review_fields.check(_row(**{DELIVERY_DT: {"date": "", "hour": "", "minute": "", "am_pm": ""},
                                                         ADDRESS: {"text": ""}}), TODAY)
        self.assertEqual((problems, warnings), ([], []))


class MarkedEmptyTests(unittest.TestCase):
    def test_marked_empty_field_needs_nothing_and_drops_leftover_typing(self):
        row = _row(**{DELIVERY_DT: {"empty": True, "date": "2026-06-23", "hour": "8"}})
        self.assertEqual(review_fields.check(row, TODAY), ([], []))
        parts = review_fields.normalize(DELIVERY_DT, row[DELIVERY_DT])
        self.assertEqual(parts, {"empty": True})
        self.assertTrue(review_fields.is_blank(DELIVERY_DT, parts))
        self.assertEqual(review_fields.compose_text(DELIVERY_DT, parts), "")
        self.assertEqual(review_fields.claim_fields(DELIVERY_DT, parts), {})

    def test_name_birthday_and_admission_cannot_be_marked_empty(self):
        for category in (NAME, BDAY, ADMISSION_DT):
            problems, _ = review_fields.check(_row(**{category: {"empty": True}}), TODAY)
            self.assertTrue(any("can't be left empty" in m for m in _messages(problems, category)), category)

    def test_empty_delivery_skips_the_delivery_cross_checks(self):
        _, warnings = review_fields.check(_row(**{DELIVERY_DT: {"empty": True}, BDAY: {"date": "1995-05-04"}}), TODAY)
        self.assertEqual(_messages(warnings, DELIVERY_DT), [])


class ClaimFieldsTests(unittest.TestCase):
    def test_reviewed_parts_are_used_as_typed(self):
        patient, encounter, claim, warnings = case_bridge.draft_patient_and_encounter(
            {NAME: "MARY DSYING ISRAEL DAMIAN", BDAY: "05-04-09"},
            reviewed_parts={NAME: _row()[NAME], BDAY: _row()[BDAY], ADMISSION_DT: _row()[ADMISSION_DT],
                            DELIVERY_DT: _row()[DELIVERY_DT]},
        )
        # A two-word first name stays the first name - no re-guessing.
        self.assertEqual((patient["last_name"], patient["first_name"], patient["middle_name"]),
                         ("Damian", "Mary Deyine", "Israel"))
        self.assertEqual(patient["date_of_birth"], "1995-05-04")
        self.assertEqual((encounter["date_admitted"], encounter["time_admitted"], encounter["am_pm_admitted"]),
                         ("2026-06-23", "11:15", "AM"))
        self.assertEqual((claim["delivery_time"], claim["am_pm_delivery"]), ("20:01", "PM"))
        self.assertEqual(warnings, [])

    def test_suffix_goes_to_name_extension(self):
        fields = review_fields.claim_fields(NAME, {"last": "Reyes", "first": "Jose", "middle": "", "suffix": "Jr."})
        self.assertEqual(fields[("patients", "name_ext")], "Jr.")

    def test_composed_text_reads_naturally(self):
        self.assertEqual(review_fields.compose_text(NAME, _row()[NAME]), "Damian, Mary Deyine Israel")
        self.assertEqual(review_fields.compose_text(ADMISSION_DT, _row()[ADMISSION_DT]), "06/23/2026 11:15 AM")
        self.assertEqual(review_fields.compose_text(BDAY, _row()[BDAY]), "05/04/1995")


if __name__ == "__main__":
    unittest.main()
