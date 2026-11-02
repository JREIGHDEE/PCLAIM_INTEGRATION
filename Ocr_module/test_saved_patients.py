"""The "Saved patients" list on Patient details (claims_store.list_patients,
GET /api/claims/patients).

Reads the claims already in the database - nothing is written - so it is
skipped when MariaDB is not running.
"""
import unittest


def _database_available():
    try:
        import db
        db.test_connection()
        return True
    except Exception:
        return False


@unittest.skipUnless(_database_available(), "MariaDB is not reachable in this environment")
class SavedPatientsListTests(unittest.TestCase):
    def setUp(self):
        import claims_store
        self.patients = claims_store.list_patients()

    def test_each_patient_has_what_the_list_shows(self):
        for patient in self.patients:
            self.assertEqual(
                set(patient), {"claim_id", "name", "dob", "date_admitted", "delivery_date",
                               "role", "status", "updated_at"})
            self.assertIsInstance(patient["claim_id"], int)
            self.assertIn(patient["role"], ("mother", "baby", "other", None))
            self.assertIn(patient["status"], ("draft", "ready", "exported"))

    def test_last_saved_first(self):
        saved = [p["updated_at"] or "" for p in self.patients]
        self.assertEqual(saved, sorted(saved, reverse=True))

    def test_one_line_per_claim(self):
        ids = [p["claim_id"] for p in self.patients]
        self.assertEqual(len(ids), len(set(ids)))


@unittest.skipUnless(_database_available(), "MariaDB is not reachable in this environment")
class DeletePatientTests(unittest.TestCase):
    """Delete from the list: a patient made here for the test, then deleted."""

    def setUp(self):
        import claims_store
        self.store = claims_store
        self.claim_id = claims_store.save_patient(None, {
            "patientLastName": "ZZ_DELETE_TEST", "patientFirstName": "SAVED LIST",
            "patientDOB": "1990-01-01", "dateAdmitted": "2026-10-30"})

    def tearDown(self):
        # Gone already when the test passed; cleaned up if it failed part-way.
        try:
            self.store.delete_patient(self.claim_id)
        except Exception:
            pass

    def _count(self, sql, value):
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute(sql, (value,))
            return cursor.fetchone()["n"]

    def test_claim_encounter_and_patient_are_deleted(self):
        from errors import ClaimNotFoundError
        self.assertIn(self.claim_id, [p["claim_id"] for p in self.store.list_patients()])
        deleted = self.store.delete_patient(self.claim_id)
        self.assertEqual(deleted, {"claim_id": self.claim_id, "encounter_deleted": True, "patient_deleted": True})
        self.assertNotIn(self.claim_id, [p["claim_id"] for p in self.store.list_patients()])
        self.assertEqual(self._count("SELECT COUNT(*) AS n FROM claims WHERE id = %s", self.claim_id), 0)
        self.assertEqual(self._count("SELECT COUNT(*) AS n FROM patients WHERE last_name = %s", "ZZ_DELETE_TEST"), 0)
        with self.assertRaises(ClaimNotFoundError):
            self.store.delete_patient(self.claim_id)


if __name__ == "__main__":
    unittest.main()
