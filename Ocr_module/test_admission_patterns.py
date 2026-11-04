"""Admission patterns: the logbook's admitting diagnosis recognised as the
clinic's reason for admission (philhealth/admission_patterns.py,
admission_pattern_store.py, routes/admission_routes.py).

The readings are real PaddleOCR misreads from the clinic's logbook scans.
The store tests run against MariaDB (skipped when it is not running, or
before migration 012) and leave the table as they found it.
"""
import unittest
from unittest import mock

import admission_pattern_store as store
from errors import InvalidRequestError
from philhealth import admission_patterns as ap

PATTERNS = [{**p, "id": i} for i, p in enumerate(ap.DEFAULT_PATTERNS, 1)]


def name_for(*readings, patterns=PATTERNS):
    found = ap.suggest(list(readings), patterns)
    return found["pattern"]["name"] if found else None


class MatchingTests(unittest.TestCase):
    def test_misread_admissions_are_recognised(self):
        cases = {
            "WEZL AISY CARE": "Well baby care",
            "FOR POJT PAKTUM UISIT": "Postpartum visit",
            "POT PARTUM UISIT": "Postpartum visit",
            "PUFT8/W CEPHALIC IN LABOR": "Labor (delivery)",
            "ECEHALINLABON": "Labor (delivery)",
            "TERM BABYBOY AGA DELIVERED NDTOAGIPIMOTERW": "Newborn (delivered here)",
            "PKENATAL CHECK UP": "Prenatal check-up",
            "FE DMPA INSERTION": "Injectable (DMPA)",
            "DNPA INJECTION": "Injectable (DMPA)",
            "FOR CIC": "Injectable (CIC)",
            "FOE PSI": "Implant insertion (PSI)",
            "FOK PSI REMO": "Implant removal (PSI)",
            "FOZ PILLS PEFILL": "Pills refill",
            "SEPCOUNSELING": "Family planning counseling",
            "13CG HEARING TEST": "Newborn screening / hearing test",
        }
        for reading, expected in cases.items():
            with self.subTest(reading=reading):
                self.assertEqual(name_for(reading), expected)

    def test_the_final_diagnosis_when_the_admitting_one_is_unreadable(self):
        self.assertEqual(name_for("P0000PU164W", "PRENATAL CHECK-UP"), "Prenatal check-up")
        self.assertEqual(name_for("S. RHWT", "DOSTPAIRTUMVIS"), "Postpartum visit")

    def test_nothing_suggested_for_scribble(self):
        for reading in ("", "ADG", "L", "RM3A3YB DEN JA NSV 0PGMON+ENWAN F"):
            with self.subTest(reading=reading):
                self.assertIsNone(name_for(reading))

    def test_short_clues_only_letter_for_letter(self):
        self.assertEqual(ap.clue_score("PSI", "FOR PSI INSERTION"), 0.9)
        self.assertEqual(ap.clue_score("PSI", "FOR PST"), 0.0)

    def test_a_reading_learned_before_wins(self):
        # "CIC SI REMON" is a CIC injection by its clue; staff said it was
        # an implant removal, so it is that from now on.
        patterns = [dict(p) for p in PATTERNS]
        self.assertEqual(name_for("CIC SI REMON", patterns=patterns), "Injectable (CIC)")
        removal = next(p for p in patterns if p["name"] == "Implant removal (PSI)")
        removal["examples"] = ap.add_example([], "CIC SI REMON")
        self.assertEqual(name_for("CIC SI REMON", patterns=patterns), "Implant removal (PSI)")
        self.assertEqual(name_for("CIC SI REMQN", patterns=patterns), "Implant removal (PSI)")  # misread again

    def test_a_pattern_switched_off_is_never_suggested(self):
        patterns = [dict(p, is_active=p["name"] != "Well baby care") for p in PATTERNS]
        self.assertNotEqual(name_for("WELL BABY CARE", patterns=patterns), "Well baby care")

    def test_examples_kept_once_newest_first(self):
        examples = ap.add_example(["FOR CIC", "OLD"], "for cic")
        self.assertEqual(examples, ["FOR CIC", "OLD"])
        self.assertEqual(ap.add_example(examples, "NEW")[0], "NEW")
        self.assertEqual(ap.drop_example(examples, " for  cic "), ["OLD"])
        self.assertEqual(len(ap.add_example([str(i) for i in range(40)], "X")), 30)


class SuggestionTests(unittest.TestCase):
    def prefill(self, data, from_scan=("admissionDx",)):
        return {"data": dict(data), "fields": {k: {"status": "accepted"} for k in from_scan}}

    def test_reason_for_admission_put_in_and_tagged(self):
        out = ap.apply_suggestion(self.prefill({"admissionDx": "FOR POJT PAKTUM UISIT"}), PATTERNS)
        self.assertEqual(out["data"]["chiefComplaint"], "POSTPARTUM VISIT")
        tag = out["fields"]["chiefComplaint"]
        self.assertEqual(tag["status"], "needs_check")
        self.assertIn("FOR POJT PAKTUM UISIT", tag["reason"])
        suggestion = out["admission_suggestion"]
        self.assertEqual((suggestion["pattern"]["name"], suggestion["pattern"]["package"], suggestion["filled"]),
                         ("Postpartum visit", "PPC01", True))

    def test_a_reason_already_there_is_kept(self):
        out = ap.apply_suggestion(self.prefill({"admissionDx": "WELL BABY CARE", "chiefComplaint": "FEVER"}), PATTERNS)
        self.assertEqual(out["data"]["chiefComplaint"], "FEVER")
        self.assertNotIn("chiefComplaint", out["fields"])
        self.assertFalse(out["admission_suggestion"]["filled"])

    def test_only_diagnoses_read_from_the_logbook(self):
        out = ap.apply_suggestion(self.prefill({"admissionDx": "WELL BABY CARE"}, from_scan=()), PATTERNS)
        self.assertNotIn("chiefComplaint", out["data"])
        self.assertNotIn("admission_suggestion", out)

    def test_nothing_close_enough_changes_nothing(self):
        before = self.prefill({"admissionDx": "ADG"})
        out = ap.apply_suggestion(before, PATTERNS)
        self.assertNotIn("chiefComplaint", out["data"])
        self.assertNotIn("admission_suggestion", out)


class CleanTests(unittest.TestCase):
    def test_a_pattern_is_tidied(self):
        p = store.clean({"name": " Pills ", "clues": "pills refill\n\n refill ", "reason": "for  pills refill",
                         "package": "", "is_active": False})
        self.assertEqual(p, {"name": "Pills", "clues": ["PILLS REFILL", "REFILL"], "reason": "FOR PILLS REFILL",
                             "package": "", "is_active": False})

    def test_bad_patterns_are_refused(self):
        good = {"name": "X", "clues": "ABCDE", "reason": "Y", "package": ""}
        for change in ({"name": ""}, {"reason": " "}, {"clues": ""}, {"package": "XYZ"}, {"clues": "A" * 61}):
            with self.subTest(change=change):
                with self.assertRaises(InvalidRequestError):
                    store.clean({**good, **change})


class RouteTests(unittest.TestCase):
    def setUp(self):
        from app import create_app
        self.client = create_app().test_client()

    def sign_in(self, role="encoder"):
        user = {"id": 7, "email": f"{role}@test.local", "full_name": role, "role": role, "is_active": 1,
                "last_login_at": None, "created_at": None}
        patcher = mock.patch("user_store.get_user_by_id", return_value=user)
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.client.session_transaction() as session:
            session["user_id"] = 7

    def test_signed_out_is_refused(self):
        self.assertEqual(self.client.get("/api/admission-patterns").status_code, 401)
        self.assertEqual(self.client.post("/api/admission-patterns/try", json={"text": "X"}).status_code, 401)

    def test_try_a_reading(self):
        self.sign_in()
        with mock.patch("admission_pattern_store.load_active", return_value=PATTERNS):
            body = self.client.post("/api/admission-patterns/try", json={"text": "WEZL AISY CARE"}).get_json()
        self.assertEqual(body["ranked"][0]["name"], "Well baby care")

    def test_suggestion_for_the_logbook_review(self):
        self.sign_in()
        with mock.patch("admission_pattern_store.load_active", return_value=PATTERNS):
            body = self.client.post("/api/admission-patterns/suggest",
                                    json={"readings": ["HLPOTPARTGM VISIT", ""]}).get_json()
            self.assertEqual(body["suggestion"]["pattern"]["name"], "Postpartum visit")
            self.assertEqual(len(body["patterns"]), len(PATTERNS))
            nothing = self.client.post("/api/admission-patterns/suggest", json={"readings": ["ADG"]}).get_json()
            self.assertIsNone(nothing["suggestion"])
            self.assertEqual(self.client.post("/api/admission-patterns/suggest", json={"readings": "X"}).status_code, 400)

    def test_an_encoder_teaches_a_reading(self):
        self.sign_in()
        with mock.patch("admission_pattern_store.learn") as learn:
            resp = self.client.post("/api/admission-patterns/4/learn", json={"reading": "POT PARTUM UISIT", "suggested_id": 3})
        self.assertEqual(resp.status_code, 200)
        learn.assert_called_once_with(4, "POT PARTUM UISIT", "encoder@test.local", suggested_id=3)

    def test_the_patterns_without_the_table(self):
        self.sign_in()
        from errors import DatabaseError

        class NoTable:
            def __enter__(self):
                raise DatabaseError("(1146, \"Table 'pclaimassist_db.admission_patterns' doesn't exist\")")

            def __exit__(self, *a):
                return False

        with mock.patch("admission_pattern_store.get_db_cursor", return_value=NoTable()):
            body = self.client.get("/api/admission-patterns").get_json()
            self.assertFalse(body["editable"])
            self.assertEqual(len(body["patterns"]), len(ap.DEFAULT_PATTERNS))
            resp = self.client.post("/api/admission-patterns", json={"name": "X", "clues": "ABCDE", "reason": "Y"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("012_admission_patterns.sql", resp.get_json()["error"])


def _table_available():
    try:
        return store.load()[1]
    except Exception:
        return False


@unittest.skipUnless(_table_available(), "MariaDB is not running, or migration 012 is not applied")
class StoreTests(unittest.TestCase):
    NAME = "Test pattern (unit test)"

    def setUp(self):
        self.addCleanup(self._remove)

    def _remove(self):
        for p in store.load()[0]:
            if p["name"] == self.NAME:
                store.delete(p["id"])

    def test_add_learn_and_take_back(self):
        new_id = store.create({"name": self.NAME, "clues": "ZZQQ TEST", "reason": "TEST", "package": ""}, "unit@test")
        other = next(p for p in store.load()[0] if p["name"] != self.NAME)
        before = list(other["examples"])
        store.learn(other["id"], "ZZQQ READING", "unit@test")
        store.learn(new_id, "ZZQQ READING", "unit@test", suggested_id=other["id"])
        rows = {p["id"]: p for p in store.load()[0]}
        self.assertIn("ZZQQ READING", rows[new_id]["examples"])
        self.assertEqual(rows[other["id"]]["examples"], before)   # moved, not kept twice
        self.assertEqual(rows[other["id"]]["times_corrected"], other["times_corrected"] + 1)
        store.forget_example(new_id, "ZZQQ READING", "unit@test")
        self.assertEqual(next(p for p in store.load()[0] if p["id"] == new_id)["examples"], [])
        # Put the other pattern's count back as it was.
        from db import get_db_cursor
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("UPDATE admission_patterns SET times_corrected = %s WHERE id = %s",
                           (other["times_corrected"], other["id"]))

    def test_names_are_unique(self):
        store.create({"name": self.NAME, "clues": "ZZQQ", "reason": "TEST"}, "unit@test")
        with self.assertRaises(InvalidRequestError):
            store.create({"name": self.NAME, "clues": "ZZQQ", "reason": "TEST"}, "unit@test")


if __name__ == "__main__":
    unittest.main()
