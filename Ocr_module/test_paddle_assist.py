"""Tests for paddle_assist.py (the free, offline AI). A fake OCR function
stands in for PaddleOCR and a fake pattern store for the database - no
model load, no DB. Same flat-file unittest convention as
test_image_quality.py / test_logbook_pipeline.py.
"""
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

import config
import logbook_pipeline
import paddle_assist
from paddle_assist import CHAR, VALUE, WORD


def _crop():
    return np.full((40, 120, 3), 255, dtype=np.uint8)


def _ocr_returning(*readings):
    """An ocr_fn that returns the given (text, confidence) readings in turn."""
    queue = list(readings)

    def ocr_fn(image):
        text, confidence = queue.pop(0) if queue else ("", 0)
        return [{"text": text, "confidence": confidence}] if text else []
    return ocr_fn


def _field(raw_text, confidence=0.7, category="NAME", status=paddle_assist.NEEDS_CHECK):
    return {"category": category, "raw_text": raw_text, "confidence": confidence, "status": status,
            "value": "" if status == paddle_assist.MANUAL else raw_text, "ocr_error": None, "ai": None}


def _reviewed(category, raw, final):
    return {"category": category, "raw_text": raw, "value": final}


def _trained(*fields):
    return paddle_assist.CorrectionModel.from_patterns(paddle_assist.reviewed_patterns(fields))


class EnsembleTests(unittest.TestCase):
    def test_majority_reading_wins(self):
        ocr = _ocr_returning(("Maria", 0.8), ("Maria", 0.75), ("Marla", 0.9), ("Maria", 0.7))
        vote = paddle_assist.ensemble_read(ocr, _crop(), "Marla", 0.6)
        self.assertEqual(vote["text"], "Maria")
        self.assertEqual(vote["votes"], 3)
        self.assertEqual(vote["readings"], 5)

    def test_letter_case_differences_vote_together(self):
        ocr = _ocr_returning(("MARIA", 0.9), ("maria", 0.8), ("", 0), ("", 0))
        vote = paddle_assist.ensemble_read(ocr, _crop(), "Maria", 0.7)
        self.assertEqual(vote["votes"], 3)
        self.assertEqual(vote["text"], "MARIA")  # the most confident spelling

    def test_nothing_read_anywhere(self):
        self.assertIsNone(paddle_assist.ensemble_read(_ocr_returning(), _crop(), "", None))

    def test_number_of_versions_follows_config(self):
        calls = []
        with mock.patch.object(config, "AI_ENSEMBLE_VARIANTS", 2):
            paddle_assist.ensemble_read(lambda img: calls.append(1) or [], _crop(), "x", 0.7)
        self.assertEqual(len(calls), 2)

    def test_every_version_is_a_valid_image(self):
        for name, make in paddle_assist.VARIANTS:
            out = make(np.random.default_rng(0).integers(0, 256, (40, 120, 3), dtype=np.uint8))
            self.assertEqual(out.ndim, 3, name)
            self.assertEqual(out.dtype, np.uint8, name)


class PatternExtractionTests(unittest.TestCase):
    def test_word_and_value_patterns(self):
        patterns = paddle_assist.extract_patterns("ADDRESS", "Puok 3 Davao", "Purok 3 Davao")
        self.assertIn((VALUE, "PUOK 3 DAVAO", "Purok 3 Davao"), patterns)
        self.assertIn((WORD, "PUOK", "Purok"), patterns)
        self.assertIn((WORD, "DAVAO", "Davao"), patterns)  # "PaddleOCR was right" is kept too

    def test_char_patterns_only_for_number_and_date_columns(self):
        self.assertIn((CHAR, "O", "0"), paddle_assist.extract_patterns("CASE #", "2O26", "2026"))
        self.assertFalse([p for p in paddle_assist.extract_patterns("NAME", "Olivia", "0livia") if p[0] == CHAR])

    def test_punctuation_does_not_stop_a_word_matching(self):
        patterns = paddle_assist.extract_patterns("ADDRESS", "Puok, Davao", "Purok, Davao")
        self.assertIn((WORD, "PUOK", "Purok"), patterns)

    def test_skipped_fields_teach_nothing(self):
        deferred = {**_reviewed("NAME", "Marla", "Maria"), "deferred_to_forms": True}
        empty = {**_reviewed("NAME", "x", "x"), "marked_empty": True}
        self.assertEqual(paddle_assist.reviewed_patterns([deferred, empty, _reviewed("NAME", "", "Maria")]), [])

    def test_patterns_are_counted(self):
        rows = paddle_assist.reviewed_patterns([_reviewed("NAME", "Marla", "Maria")] * 3)
        self.assertIn(("NAME", WORD, "MARLA", "Maria", 3), rows)


class CorrectionModelTests(unittest.TestCase):
    def test_learns_a_repeated_word_fix(self):
        model = _trained(_reviewed("ADDRESS", "Purok 3 Bago Ap1itam", "Purok 3 Bago Aplaya"),
                         _reviewed("ADDRESS", "Purok 7 Bago Ap1itam", "Purok 7 Bago Aplaya"))
        text, notes, _ = model.correct("ADDRESS", "Purok 9 Bago Ap1itam")
        self.assertEqual(text, "Purok 9 Bago Aplaya")
        self.assertTrue(notes)

    def test_word_fix_keeps_punctuation(self):
        model = paddle_assist.CorrectionModel.from_patterns([("ADDRESS", WORD, "PUOK", "Purok", 2)])
        self.assertEqual(model.correct("ADDRESS", "Puok, Davao")[0], "Purok, Davao")

    def test_one_correction_is_not_enough(self):
        model = _trained(_reviewed("NAME", "Marla Santos", "Maria Santos"))
        self.assertEqual(model.correct("NAME", "Marla Reyes")[0], "Marla Reyes")

    def test_learns_a_whole_value(self):
        model = _trained(*[_reviewed("FINAL DIAGNOSIS", "G2P2 N5D", "G2P2 NSD")] * 2)
        text, _, whole = model.correct("FINAL DIAGNOSIS", "G2P2 N5D")
        self.assertEqual(text, "G2P2 NSD")
        self.assertTrue(whole)

    def test_fix_that_staff_usually_reject_is_not_applied(self):
        model = _trained(*[_reviewed("NAME", "Marla Cruz", "Marla Cruz")] * 3,
                         _reviewed("NAME", "Marla Cruz", "Maria Cruz"))
        self.assertEqual(model.correct("NAME", "Marla Cruz")[0], "Marla Cruz")

    def test_starter_knowledge_fixes_letters_in_numbers(self):
        model = paddle_assist.CorrectionModel.with_starter_knowledge()
        self.assertEqual(model.correct("CASE #", "2O26-O142")[0], "2026-0142")

    def test_am_pm_letters_are_left_alone(self):
        model = paddle_assist.CorrectionModel.with_starter_knowledge()
        self.assertEqual(model.correct("DATE & TIME OF DELIVERY", "O3/14/26 5:45 AM")[0], "03/14/26 5:45 AM")

    def test_letters_in_text_columns_are_not_turned_into_digits(self):
        model = paddle_assist.CorrectionModel.with_starter_knowledge()
        self.assertEqual(model.correct("NAME", "Olivia Sison")[0], "Olivia Sison")

    def test_reformatted_answers_teach_no_character_fixes(self):
        model = _trained(*[_reviewed("BDAY", "5/21/98", "1998-05-21")] * 5)
        self.assertEqual(model.correct("BDAY", "5/21/98")[0], "1998-05-21")  # whole value, yes
        self.assertEqual(model.correct("BDAY", "5/22/98")[0], "5/22/98")     # but no char fixes


class PatternTableTests(unittest.TestCase):
    """load_model() / record_review() against a fake pattern_store."""

    def _stores(self, learned=True, rows=(), past=()):
        added = []
        pattern_store = SimpleNamespace(
            has_learned_patterns=lambda: learned,
            load_patterns=lambda: list(rows) + [r for batch in added for r in batch],
            add_patterns=added.append,
        )
        case_session_store = SimpleNamespace(list_reviewed_ocr_fields=lambda: list(past))
        self.entries = _fake_entry_store()
        return added, mock.patch.dict(sys.modules, {"pattern_store": pattern_store,
                                                    "case_session_store": case_session_store,
                                                    "entry_store": self.entries})

    def test_model_comes_from_the_table(self):
        _, stores = self._stores(rows=[("ADDRESS", WORD, "PUOK", "Purok", 2)])
        with stores:
            model = paddle_assist.load_model()
        self.assertEqual(model.correct("ADDRESS", "Puok 3")[0], "Purok 3")

    def test_first_run_fills_the_table_from_past_reviews(self):
        added, stores = self._stores(learned=False, past=[_reviewed("NAME", "Marla", "Maria")] * 2)
        with stores:
            model = paddle_assist.load_model()
        self.assertTrue(added)
        self.assertEqual(model.correct("NAME", "Marla")[0], "Maria")

    def test_without_the_table_starter_knowledge_is_used(self):
        def missing():
            raise RuntimeError("Table 'ocr_correction_patterns' doesn't exist")
        stores = {"pattern_store": SimpleNamespace(has_learned_patterns=missing),
                  "case_session_store": SimpleNamespace(list_reviewed_ocr_fields=lambda: []),
                  "entry_store": _fake_entry_store()}
        with mock.patch.dict(sys.modules, stores), self.assertLogs("paddle_assist", level="ERROR"):
            model = paddle_assist.load_model()
        self.assertEqual(model.correct("CASE #", "2O26")[0], "2026")

    def test_review_is_recorded(self):
        added, stores = self._stores()
        with stores:
            self.assertGreater(paddle_assist.record_review([_reviewed("NAME", "Marla", "Maria")]), 0)
        self.assertIn(("NAME", WORD, "MARLA", "Maria", 1), added[0])
        entries, origin = self.entries.added[0]
        self.assertEqual(origin, "reviews")
        self.assertIn(("NAME", WORD, "MARIA", "Maria", 1), entries)

    def test_recording_never_raises(self):
        def broken(*args):
            raise RuntimeError("database down")
        stores = {"pattern_store": SimpleNamespace(add_patterns=broken),
                  "entry_store": SimpleNamespace(add_entries=broken, FROM_REVIEWS="reviews")}
        with mock.patch.dict(sys.modules, stores), self.assertLogs("paddle_assist", level="ERROR"):
            self.assertEqual(paddle_assist.record_review([_reviewed("NAME", "Marla", "Maria")]), 0)


def _fake_entry_store(rows=(), learned=True):
    store = SimpleNamespace(FROM_REVIEWS="reviews", FROM_FORMS="forms", added=[], removed=[])
    store.has_review_entries = lambda: learned
    store.load_entries = lambda: list(rows)
    store.add_entries = lambda entries, origin: store.added.append((entries, origin))
    store.remove_review_entries = store.removed.append
    return store


def _with_codes(*codes):
    """A model (with the starter letter/digit fixes, like a real one) that
    has seen these case numbers confirmed (once each)."""
    model = paddle_assist.CorrectionModel.with_starter_knowledge()
    model.add_entries([("CASE #", VALUE, c.upper(), c, 1, 1) for c in codes])
    return model


class CaseNumberFormatTests(unittest.TestCase):
    def test_learns_the_usual_format(self):
        fmt = _with_codes("20266140", "20266148").code_format("CASE #")
        self.assertEqual(fmt["prefix"], "2026")
        self.assertTrue(fmt["compact"])
        self.assertEqual(fmt["samples"], 2)

    def test_misread_year_prefix_and_spaces_are_fixed(self):
        model = _with_codes("20266140", "20266148")
        for reading, expected in [("2020 4043", "20264043"), ("702 5932", "20265932"),
                                  ("2o2e 8hin", "20268h1n"), ("20206140", "20266140")]:
            self.assertEqual(model.correct("CASE #", reading)[0], expected, reading)

    def test_keeps_the_separator_staff_use(self):
        model = _with_codes("2026-6140", "2026-6148", "2026-6150")
        self.assertEqual(model.correct("CASE #", "2020 4043")[0], "2026-4043")

    def test_a_year_staff_confirmed_before_is_left_alone(self):
        model = _with_codes("20266140", "20266148", "20266150", "20251234")
        self.assertEqual(model.correct("CASE #", "2025 9999")[0], "20259999")

    def test_unrelated_first_part_is_not_turned_into_the_year(self):
        model = _with_codes("20266140", "20266148")
        self.assertEqual(model.correct("CASE #", "mnet Le023")[0], "mnetLe023")

    def test_one_confirmed_code_is_not_enough(self):
        model = _with_codes("20266140")
        self.assertEqual(model.correct("CASE #", "2020 4043")[0], "2020 4043")

    def test_a_corrected_case_number_is_never_stamped_on_another_patient(self):
        model = _with_codes("20266140", "20266148")
        model.add(*("CASE #", VALUE, "20240", "20266140"), count=3)
        model.add(*("CASE #", WORD, "20240", "20266140"), count=3)
        self.assertEqual(model.correct("CASE #", "20240")[0], "20240")

    def test_case_numbers_are_never_suggested_as_values(self):
        model = _with_codes(*["20266140"] * 5)
        self.assertEqual(model.correct("CASE #", "20266141")[0], "20266141")

    def test_codes_come_only_from_reviews(self):
        model = paddle_assist.CorrectionModel()
        model.add_entries([("CASE #", VALUE, "20266140", "20266140", 0, 5)])  # forms only
        self.assertIsNone(model.code_format("CASE #"))


class ResubmitLearningTests(unittest.TestCase):
    def _record(self, fields, previous=None):
        patterns = SimpleNamespace(added=[], removed=[])
        patterns.add_patterns = patterns.added.append
        patterns.remove_patterns = patterns.removed.append
        entries = _fake_entry_store()
        with mock.patch.dict(sys.modules, {"pattern_store": patterns, "entry_store": entries}):
            paddle_assist.record_review(fields, previous_fields=previous)
        return patterns, entries

    def test_first_confirmation_is_learned(self):
        patterns, entries = self._record([_reviewed("CASE #", "2020 4043", "20264043")])
        self.assertTrue(patterns.added)
        self.assertIn(("CASE #", VALUE, "20264043", "20264043", 1), entries.added[0][0])

    def test_confirming_again_unchanged_learns_nothing_new(self):
        fields = [_reviewed("NAME", "Marla", "Maria")]
        patterns, entries = self._record(fields, previous=fields)
        self.assertEqual((patterns.added, patterns.removed, entries.added, entries.removed), ([], [], [], []))

    def test_a_corrected_answer_replaces_the_old_one(self):
        before = [_reviewed("NAME", "Marla", "Marla")]
        after = [_reviewed("NAME", "Marla", "Maria")]
        patterns, entries = self._record(after, previous=before)
        self.assertIn(("NAME", WORD, "MARLA", "Maria", 1), patterns.added[0])
        self.assertIn(("NAME", WORD, "MARLA", "Marla", 1), patterns.removed[0])
        self.assertIn(("NAME", WORD, "MARIA", "Maria", 1), entries.added[0][0])
        self.assertIn(("NAME", WORD, "MARLA", "Marla", 1), entries.removed[0])


def _with_entries(*rows):
    """A model knowing the given common entries:
    (category, entry_type, text, times_from_reviews, total_weight)."""
    model = paddle_assist.CorrectionModel()
    model.add_entries([(c, t, text.upper(), text, r, w) for c, t, text, r, w in rows])
    return model


class CommonEntryTests(unittest.TestCase):
    def test_entries_from_a_value(self):
        entries = paddle_assist.extract_entries("ADDRESS", "Purok 3, Calinan")
        self.assertIn((VALUE, "PUROK 3, CALINAN", "Purok 3, Calinan"), entries)
        self.assertIn((WORD, "CALINAN", "Calinan"), entries)
        self.assertNotIn((WORD, "3", "3"), entries)  # numbers and short words aren't vocabulary

    def test_no_vocabulary_for_dates_or_whole_names(self):
        self.assertEqual(paddle_assist.extract_entries("BDAY", "05/21/98"), [])
        self.assertFalse([e for e in paddle_assist.extract_entries("NAME", "Dela Cruz, Maria") if e[0] == VALUE])

    def test_case_numbers_are_kept_whole_for_format_learning(self):
        self.assertEqual(paddle_assist.extract_entries("CASE #", "20266140"), [(VALUE, "20266140", "20266140")])

    def test_form_values_map_to_logbook_columns(self):
        rows = paddle_assist.form_entries({"patientLastName": "DELA CRUZ", "patientFirstName": "MARIA",
                                           "dischargeDx": "Pregnancy uterine", "pin": "1234"})
        self.assertIn(("NAME", WORD, "MARIA", "MARIA", 1), rows)
        self.assertIn(("FINAL DIAGNOSIS", WORD, "PREGNANCY", "Pregnancy", 1), rows)
        self.assertFalse([r for r in rows if r[2] == "1234"])  # unrelated keys are ignored

    def test_misread_word_snaps_to_common_entry(self):
        model = _with_entries(("ADDRESS", WORD, "Calinan", 0, 5))
        text, notes, _ = model.correct("ADDRESS", "Purok 3, Calinon")
        self.assertEqual(text, "Purok 3, Calinan")
        self.assertIn("common entry", notes[0])

    def test_snapped_word_keeps_the_writing_style(self):
        model = _with_entries(("FINAL DIAGNOSIS", WORD, "Pregnancy", 0, 3))
        self.assertEqual(model.correct("FINAL DIAGNOSIS", "PREGNACY UTERINE")[0], "PREGNANCY UTERINE")

    def test_rare_entries_are_not_suggested(self):
        model = _with_entries(("ADDRESS", WORD, "Calinan", 0, 1))
        self.assertEqual(model.correct("ADDRESS", "Calinon")[0], "Calinon")

    def test_far_away_words_are_left_alone(self):
        model = _with_entries(("ADDRESS", WORD, "Calinan", 0, 9))
        self.assertEqual(model.correct("ADDRESS", "Catalunan")[0], "Catalunan")

    def test_whole_values_only_count_logbook_reviews(self):
        from_forms = _with_entries(("FINAL DIAGNOSIS", VALUE, "G2P2 NSD live baby boy", 0, 9))
        self.assertEqual(from_forms.correct("FINAL DIAGNOSIS", "G2P2 NSD live baby bey")[0],
                         "G2P2 NSD live baby bey")
        from_reviews = _with_entries(("FINAL DIAGNOSIS", VALUE, "G2P2 NSD live baby boy", 3, 3))
        self.assertEqual(from_reviews.correct("FINAL DIAGNOSIS", "G2P2 NSD live baby bey")[0],
                         "G2P2 NSD live baby boy")

    def test_snapped_name_is_never_sure(self):
        model = _with_entries(("NAME", WORD, "Maria", 0, 8))
        ocr = _ocr_returning(("Marla", 0.9), ("Marla", 0.9), ("", 0), ("", 0))
        field = _field("Marla", confidence=0.7, status=paddle_assist.MANUAL)
        reading = paddle_assist.assist_field(field, _crop(), ocr, model)
        paddle_assist.apply_reading(field, reading)
        self.assertEqual(reading["text"], "Maria")
        self.assertFalse(reading["sure"])
        self.assertTrue(field["best_guess"])  # filled, but flagged to check carefully

    def test_form_is_recorded(self):
        store = _fake_entry_store()
        with mock.patch.dict(sys.modules, {"entry_store": store}):
            self.assertGreater(paddle_assist.record_form({"admissionDx": "Term pregnancy"}), 0)
        entries, origin = store.added[0]
        self.assertEqual(origin, "forms")
        self.assertIn(("ADMITTING DIAGNOSIS", WORD, "PREGNANCY", "pregnancy", 1), entries)

    def test_model_loads_common_entries(self):
        stores = {"pattern_store": SimpleNamespace(has_learned_patterns=lambda: True, load_patterns=lambda: []),
                  "case_session_store": SimpleNamespace(list_reviewed_ocr_fields=lambda: []),
                  "entry_store": _fake_entry_store(rows=[("ADDRESS", WORD, "CALINAN", "Calinan", 0, 4)])}
        with mock.patch.dict(sys.modules, stores):
            model = paddle_assist.load_model()
        self.assertEqual(model.correct("ADDRESS", "Calinon")[0], "Calinan")


class AssistFieldTests(unittest.TestCase):
    def test_agreeing_readings_are_sure_but_never_accepted(self):
        ocr = _ocr_returning(("Maria", 0.8), ("Maria", 0.8), ("", 0), ("", 0))
        field = _field("Marla", confidence=0.5, status=paddle_assist.MANUAL)
        reading = paddle_assist.assist_field(field, _crop(), ocr, paddle_assist.CorrectionModel())
        paddle_assist.apply_reading(field, reading)
        self.assertTrue(reading["sure"])
        self.assertEqual(field["value"], "Maria")
        self.assertEqual(field["status"], paddle_assist.NEEDS_CHECK)
        self.assertEqual(field["raw_text"], "Marla")  # PaddleOCR's own reading is kept

    def test_disagreeing_readings_fill_in_a_best_guess(self):
        ocr = _ocr_returning(("Maria", 0.5), ("Mario", 0.4), ("Marie", 0.3), ("Marta", 0.2))
        field = _field("Marla", confidence=0.6, status=paddle_assist.MANUAL)
        reading = paddle_assist.assist_field(field, _crop(), ocr, paddle_assist.CorrectionModel())
        paddle_assist.apply_reading(field, reading)
        self.assertFalse(reading["sure"])
        self.assertEqual(field["value"], "Marla")
        self.assertEqual(field["status"], paddle_assist.NEEDS_CHECK)  # never "accepted"
        self.assertTrue(field["best_guess"])

    def test_best_guess_is_the_full_paddle_reading_with_known_fixes(self):
        # The vote picks a partial reading; the guess keeps PaddleOCR's
        # whole reading, with the pattern fixes applied.
        ocr = _ocr_returning(("8g/7", 0.7), ("8g/7", 0.6), ("", 0), ("", 0))
        model = paddle_assist.CorrectionModel.from_patterns([("ADMITTING DIAGNOSIS", WORD, "N5D", "NSD", 2)])
        field = _field("QODg N5D 8g/7", confidence=0.5, category="ADMITTING DIAGNOSIS",
                       status=paddle_assist.MANUAL)
        reading = paddle_assist.assist_field(field, _crop(), ocr, model)
        reading["sure"] = False
        paddle_assist.apply_reading(field, reading)
        self.assertEqual(field["value"], "QODg NSD 8g/7")

    def test_sure_reading_is_not_marked_as_a_guess(self):
        ocr = _ocr_returning(("Maria", 0.8), ("Maria", 0.8), ("", 0), ("", 0))
        field = _field("Marla", confidence=0.5, status=paddle_assist.MANUAL)
        paddle_assist.apply_reading(field, paddle_assist.assist_field(field, _crop(), ocr,
                                                                      paddle_assist.CorrectionModel()))
        self.assertFalse(field["best_guess"])

    def test_number_with_leftover_letters_is_never_sure(self):
        ocr = _ocr_returning(("202e 18an", 0.9), ("202e 18an", 0.9), ("", 0), ("", 0))
        field = _field("202e 18an", confidence=0.7, category="CASE #")
        reading = paddle_assist.assist_field(field, _crop(), ocr, paddle_assist.CorrectionModel())
        self.assertFalse(reading["sure"])

    def test_corrector_survives_ocr_errors(self):
        def broken(image):
            raise RuntimeError("paddle crashed")
        field = _field("Marla")
        corrector = paddle_assist.make_corrector(broken, model=paddle_assist.CorrectionModel())
        with self.assertLogs("paddle_assist", level="ERROR"):
            corrector([(field, _crop())])
        self.assertEqual(field["value"], "Marla")

    def test_number_of_fields_is_capped(self):
        calls = []
        corrector = paddle_assist.make_corrector(lambda img: calls.append(1) or [],
                                                 model=paddle_assist.CorrectionModel())
        with mock.patch.object(config, "AI_CORRECTION_MAX_FIELDS", 2), \
                mock.patch.object(config, "AI_ENSEMBLE_VARIANTS", 1):
            corrector([(_field("x"), _crop()) for _ in range(5)])
        self.assertEqual(len(calls), 2)

    def test_switched_off_means_paddle_only(self):
        with mock.patch.object(config, "AI_CORRECTION_ENABLED", False):
            self.assertIsNone(paddle_assist.make_corrector(lambda img: []))


class WhichFieldsTests(unittest.TestCase):
    def test_only_unsure_fields_with_writing(self):
        self.assertTrue(paddle_assist.wants_second_look(_field("x", status=paddle_assist.NEEDS_CHECK), {"blank": False}))
        self.assertTrue(paddle_assist.wants_second_look(_field("x", status=paddle_assist.MANUAL), {"blank": False}))
        self.assertFalse(paddle_assist.wants_second_look(_field("x", status=logbook_pipeline.ACCEPTED), {"blank": False}))
        self.assertFalse(paddle_assist.wants_second_look(_field("", status=paddle_assist.MANUAL), {"blank": True}))
        failed = {**_field("", status=paddle_assist.MANUAL), "ocr_error": "OCR failed on this cell"}
        self.assertFalse(paddle_assist.wants_second_look(failed, {"blank": False}))

    def test_statuses_match_the_pipeline(self):
        self.assertEqual(paddle_assist.NEEDS_CHECK, logbook_pipeline.NEEDS_CHECK)
        self.assertEqual(paddle_assist.MANUAL, logbook_pipeline.MANUAL)


if __name__ == "__main__":
    unittest.main()
