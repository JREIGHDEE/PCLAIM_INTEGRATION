"""Tests for philhealth/mother_baby.py: mother or baby from a logbook
entry, finding a baby's mother, and what a baby's claim copies from hers.

Same flat-file unittest convention as the other test_*.py files. Pure - no
DB, no Flask. The diagnoses are as OCR read them from real logbook pages.
"""
import unittest

from philhealth import mother_baby
from philhealth.mother_baby import BABY, MOTHER, classify_entry, rank_mothers, values_for_baby


class ClassifyEntryTests(unittest.TestCase):
    def role(self, **entry):
        return classify_entry(entry)["role"]

    def test_delivery_diagnosis_is_the_mother_even_though_it_names_the_baby(self):
        dx = "PUFT 39 3/7 WKS AOG DELIVERED VIA NSVD TO A LIVE TERM BABY BOY AGA W/ AS OF 4 & 1; G1P2 (1001)"
        self.assertEqual(self.role(admission_dx=dx, discharge_dx=dx), MOTHER)

    def test_misread_prenatal_and_postpartum_visits_are_the_mother(self):
        for dx in ("PKENATAL CHECK UP", "PRENATAL CYECK UP", "POSR PARTUN UISIT", "POST PARTUM VISIT"):
            with self.subTest(dx=dx):
                self.assertEqual(self.role(discharge_dx=dx), MOTHER)

    def test_misread_well_baby_care_is_the_baby(self):
        for dx in ("WEL BABY CARE", "WELL BAnY CAR", "WEZL 13AY CARE", "WELL BASY CAME", "NEWBORN SCREENING"):
            with self.subTest(dx=dx):
                self.assertEqual(self.role(discharge_dx=dx), BABY)

    def test_baby_as_a_first_name_with_a_prenatal_visit_is_the_mother(self):
        self.assertEqual(self.role(name="BABY GRACE LOPEZ", discharge_dx="PKENATAL CHECK UP"), MOTHER)

    def test_newborn_name_without_a_diagnosis_is_the_baby(self):
        self.assertEqual(self.role(name="BABY GIRL DELA CRUZ"), BABY)

    def test_under_a_year_old_is_the_baby(self):
        self.assertEqual(self.role(dob="2026-08-14", date_admitted="2026-08-23"), BABY)

    def test_birthday_after_the_visit_is_ignored(self):
        # "68-08-10" read as 2068.
        self.assertIsNone(self.role(dob="2068-08-10", date_admitted="2026-08-24"))

    def test_adult_with_a_delivery_date_is_the_mother(self):
        self.assertEqual(self.role(dob="1997-03-14", date_admitted="2026-08-20", delivery_date="2026-08-20"),
                         MOTHER)

    def test_nothing_to_go_on_asks_staff(self):
        result = classify_entry({"name": "JUAN DELA CRUZ"})
        self.assertIsNone(result["role"])
        self.assertIn("choose", result["reason"])


class RankMothersTests(unittest.TestCase):
    BABY_CLAIM = {"claim_id": 20, "last_name": "DELA CRUZ", "dob": "2026-10-20",
                  "date_admitted": "2026-10-20", "upload_id": "u1", "session_id": 50}

    def test_birthday_and_surname_rank_first(self):
        mothers = [
            {"claim_id": 11, "last_name": "SANTOS", "delivery_date": "2026-10-20"},
            {"claim_id": 12, "last_name": "DELA CRUZ", "delivery_date": "2026-10-20"},
            {"claim_id": 13, "last_name": "REYES", "delivery_date": "2026-09-01"},
        ]
        ranked = rank_mothers(self.BABY_CLAIM, mothers)
        self.assertEqual([m["claim_id"] for m in ranked], [12, 11])
        self.assertIn("Same surname", ranked[0]["reasons"])

    def test_misread_surname_still_matches(self):
        ranked = rank_mothers(self.BABY_CLAIM, [{"claim_id": 12, "last_name": "DELA CRUS"}])
        self.assertEqual(ranked[0]["reasons"], ["Same surname"])

    def test_above_in_the_same_scan_counts(self):
        ranked = rank_mothers(self.BABY_CLAIM, [
            {"claim_id": 14, "last_name": "REYES", "upload_id": "u1", "session_id": 49},
            {"claim_id": 15, "last_name": "REYES", "upload_id": "u1", "session_id": 51},
        ])
        self.assertEqual([m["claim_id"] for m in ranked], [14])

    def test_never_its_own_mother(self):
        self.assertEqual(rank_mothers(self.BABY_CLAIM, [{"claim_id": 20, "last_name": "DELA CRUZ"}]), [])


class ValuesForBabyTests(unittest.TestCase):
    MOTHER_CLAIM = {
        "patientLastName": "DELA CRUZ", "patientFirstName": "MARIA", "patientMiddleName": "SANTOS",
        "patientDOB": "1997-03-14", "patientSex": "Female", "patientPIN": "12-345678901-2",
        "memberIsPatient": True,
        "addrBarangay": "CABANTIAN", "addrCity": "DAVAO CITY", "mobile": "09171234567",
        "civilStatus": "Married", "deliveryDate": "2026-10-20", "babySex": "Male",
        "lmp": "2026-01-13", "gravida": "2",
    }

    def items(self, result):
        return {item["key"]: (group["who"], item["value"]) for group in result["groups"] for item in group["items"]}

    def test_mother_as_member(self):
        result = values_for_baby(self.MOTHER_CLAIM)
        items = self.items(result)
        self.assertTrue(result["member_is_mother"])
        self.assertEqual(items["memberLastName"], ("member", "DELA CRUZ"))
        self.assertEqual(items["memberPIN"], ("member", "12-345678901-2"))
        self.assertEqual(items["memberSex"], ("member", "Female"))
        self.assertEqual(items["relationship"], ("member", "Child"))
        self.assertEqual(items["addrBarangay"], ("home", "CABANTIAN"))
        self.assertEqual(items["patientDOB"], ("baby", "2026-10-20"))
        self.assertEqual(items["patientSex"], ("baby", "Male"))
        self.assertEqual(items["patientRepName"], ("baby", "MARIA SANTOS DELA CRUZ"))
        self.assertEqual(items["patientRepRelationship"], ("baby", "Parent"))

    def test_mothers_facts_for_the_newborn_wording(self):
        facts = values_for_baby({**self.MOTHER_CLAIM, "para": "1", "birthWeight": "3000"})["mother_facts"]
        self.assertEqual((facts["gravida"], facts["para"], facts["birthWeight"]), ("2", "1", "3000"))

    def test_nothing_about_the_mothers_own_body(self):
        items = self.items(values_for_baby(self.MOTHER_CLAIM))
        for key in ("lmp", "gravida", "patientLastName", "patientFirstName", "admissionDx"):
            self.assertNotIn(key, items)

    def test_father_as_member(self):
        mother = {**self.MOTHER_CLAIM, "memberIsPatient": False, "relationship": "Spouse",
                  "memberLastName": "DELA CRUZ", "memberFirstName": "JUAN", "memberSex": "Male",
                  "memberPIN": "98-765432109-8"}
        result = values_for_baby(mother)
        items = self.items(result)
        self.assertFalse(result["member_is_mother"])
        self.assertEqual(items["memberFirstName"], ("member", "JUAN"))
        self.assertEqual(items["memberPIN"], ("member", "98-765432109-8"))
        self.assertEqual(items["relationship"], ("member", "Child"))
        self.assertIn("JUAN DELA CRUZ", result["groups"][0]["who_label"])

    def test_every_copied_key_is_a_form_key(self):
        import test_form_prefill
        form_keys = test_form_prefill._state_data_keys() | {"patientNoPhilhealth", "memberNoPhilhealth",
                                                           "motherNameExt", "spouseNameExt",
                                                           "memberSignatureName", "memberSignatureDate"}
        everything = {k: "x" for k in form_keys}
        for group in values_for_baby(everything)["groups"]:
            for item in group["items"]:
                self.assertIn(item["key"], form_keys)


class CompareWithMotherTests(unittest.TestCase):
    """A baby's claim against its mother's (the clinic's RTH reasons G3-G5;
    the forms' rule IC-13 does the same)."""
    FACTS = {"gravida": "3", "para": "2", "deliveryDate": "2026-08-29", "babySex": "Female", "birthWeight": "2800"}
    BABY = {"patientDOB": "2026-08-29", "patientSex": "Female",
            "dischargeDx": "LIVE TERM BABY GIRL AGA DELIVERED VIA NSVD TO A G3P3 MOTHER WEIGHING 2800 GRAMS"}

    def whats(self, baby):
        return [d["what"] for d in mother_baby.compare_with_mother(baby, self.FACTS)]

    def test_a_baby_that_matches_its_mother(self):
        self.assertEqual(self.whats(self.BABY), [])

    def test_each_difference(self):
        self.assertEqual(self.whats({**self.BABY, "patientDOB": "2026-08-30"}),
                         ["Baby's date of birth / mother's date of delivery"])
        self.assertEqual(self.whats({**self.BABY, "patientSex": "Male"}), ["Baby's sex"])
        self.assertEqual(self.whats({**self.BABY, "dischargeDx": self.BABY["dischargeDx"].replace("G3P3", "G4P4")}),
                         ["Mother's G and P in the baby's diagnosis"])
        self.assertEqual(self.whats({**self.BABY, "dischargeDx": self.BABY["dischargeDx"].replace("2800", "3100")}),
                         ["Birth weight in the baby's diagnosis"])
        self.assertEqual(self.whats({**self.BABY, "dischargeDx": self.BABY["dischargeDx"].replace("GIRL", "BOY")}),
                         ["Baby's sex in the diagnosis"])

    def test_only_what_both_claims_have(self):
        self.assertEqual(mother_baby.compare_with_mother({"patientDOB": "2026-08-30"}, {}), [])
        self.assertEqual(self.whats({"dischargeDx": "WELL BABY CARE"}), [])


def _database_available():
    try:
        import db
        db.test_connection()
        return True
    except Exception:
        return False


@unittest.skipUnless(_database_available(), "MariaDB is not reachable in this environment")
class MotherThenBabyInTheDatabaseTests(unittest.TestCase):
    """Save a mother's claim, then her baby's, link them, and read back what
    the baby's saved claim says differently (claims_store.values_from_mother).
    Both claims are made for the test and deleted after it."""

    def setUp(self):
        import claims_store
        self.store = claims_store
        self.mother = claims_store.save_patient(None, {
            "patientLastName": "ZZ_RTH_TEST", "patientFirstName": "MOTHER", "patientDOB": "1995-03-15",
            "patientSex": "Female", "dateAdmitted": "2026-08-29", "dateDischarge": "2026-08-30",
            "deliveryDate": "2026-08-29", "gravida": "3", "para": "2", "babySex": "Female", "birthWeight": "2800",
            "admissionDx": "G3P2 (2002) PUFT 37 WKS AOG CEPHALIC IN LABOR"})
        self.baby = None

    def tearDown(self):
        for claim_id in (self.baby, self.mother):
            if claim_id:
                try:
                    self.store.delete_patient(claim_id)
                except Exception:
                    pass

    def save_baby(self, **changes):
        values = {"patientLastName": "ZZ_RTH_TEST", "patientFirstName": "BABY GIRL", "patientDOB": "2026-08-29",
                  "patientSex": "Female", "dateAdmitted": "2026-08-29", "dateDischarge": "2026-08-30",
                  "dischargeDx": "LIVE TERM BABY GIRL AGA DELIVERED VIA NSVD TO A G3P3 MOTHER WEIGHING 2800 GRAMS",
                  **changes}
        self.baby = self.store.save_patient(self.baby, values)
        self.store.set_family(self.baby, role="baby", mother_claim_id=self.mother, set_role=True, set_mother=True)
        return [d["what"] for d in self.store.values_from_mother(self.baby)["differences"]]

    def test_matching_baby_has_no_differences(self):
        self.assertEqual(self.save_baby(), [])

    def test_baby_saved_with_other_details_is_caught(self):
        self.save_baby()
        found = self.save_baby(patientDOB="2026-08-30", patientSex="Male",
                               dischargeDx="LIVE TERM BABY GIRL AGA DELIVERED VIA NSVD TO A G4P4 MOTHER "
                                           "WEIGHING 3100 GRAMS")
        self.assertEqual(found, ["Baby's date of birth / mother's date of delivery", "Baby's sex",
                                 "Mother's G and P in the baby's diagnosis", "Birth weight in the baby's diagnosis"])


if __name__ == "__main__":
    unittest.main()
