"""Encryption of sensitive patient details (field_crypto.py, adviser's
revision S4).

The first tests need no database. The last one saves a patient made for
the test through "Save patient", checks the database holds the details
encrypted and the app reads them back, then deletes it; it is skipped when
MariaDB is not running.
"""
import json
import unittest

import field_crypto


class FieldCryptoTests(unittest.TestCase):
    def test_round_trip(self):
        for text in ("12-345678901-3", "maria@gmail.com", "BLK 4 LOT 9, PUROK 19", "Señora Ñiño"):
            stored = field_crypto.encrypt(text)
            self.assertTrue(stored.startswith(field_crypto.PREFIX))
            self.assertNotIn(text, stored)
            self.assertEqual(field_crypto.decrypt(stored), text)

    def test_same_text_is_stored_differently_each_time(self):
        self.assertNotEqual(field_crypto.encrypt("12-345678901-3"), field_crypto.encrypt("12-345678901-3"))

    def test_empty_and_older_plain_values_pass_through(self):
        for value in (None, ""):
            self.assertEqual(field_crypto.encrypt(value), value)
        self.assertEqual(field_crypto.decrypt("an older plain value"), "an older plain value")
        stored = field_crypto.encrypt("x")
        self.assertEqual(field_crypto.encrypt(stored), stored)   # never twice

    def test_a_changed_value_is_refused(self):
        stored = field_crypto.encrypt("12-345678901-3")
        tampered = stored[:-6] + ("A" if stored[-6] != "A" else "B") + stored[-5:]
        with self.assertRaises(Exception):
            field_crypto.decrypt(tampered)

    def test_only_the_sensitive_columns_are_encrypted(self):
        fields = field_crypto.encrypt_fields("claims", {"member_pin": "12-345678901-2", "addr_city": "DAVAO CITY"})
        self.assertTrue(field_crypto.is_encrypted(fields["member_pin"]))
        self.assertEqual(fields["addr_city"], "DAVAO CITY")


def _database_available():
    try:
        import db
        db.test_connection()
        return True
    except Exception:
        return False


@unittest.skipUnless(_database_available(), "MariaDB is not reachable in this environment")
class StoredEncryptedTests(unittest.TestCase):
    def setUp(self):
        import claims_store
        self.store = claims_store
        self.claim_id = claims_store.save_patient(None, {
            "patientLastName": "ZZ_CRYPTO_TEST", "patientFirstName": "STORED",
            "patientDOB": "1990-01-01", "dateAdmitted": "2026-10-30",
            "patientPIN": "12-345678901-3", "memberPIN": "12-345678901-2",
            "mobile": "09171234567", "email": "zz.crypto@gmail.com", "addrStreet": "PUROK 19"})

    def tearDown(self):
        try:
            self.store.delete_patient(self.claim_id)
        except Exception:
            pass

    def test_database_holds_them_encrypted_and_the_app_reads_them(self):
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute("SELECT member_pin, mobile, email, addr_street, form_values, encounter_id "
                           "FROM claims WHERE id = %s", (self.claim_id,))
            raw = cursor.fetchone()
        for column in ("member_pin", "mobile", "email", "addr_street", "form_values"):
            if raw[column] is not None:
                self.assertTrue(field_crypto.is_encrypted(raw[column]), column)
        self.assertNotIn("zz.crypto@gmail.com", raw["form_values"])
        self.assertNotIn("12-345678901-2", raw["form_values"])

        rows = self.store.get_claim(self.claim_id)
        self.assertEqual(rows["claim"]["member_pin"], "12-345678901-2")
        self.assertEqual(rows["patient"]["pin"], "12-345678901-3")
        # The mobile number and email are kept with the typed form details
        # (form_values) - "Save patient" writes a fixed list of columns, and
        # these are not on it - encrypted all the same.
        self.assertEqual(json.loads(rows["claim"]["form_values"])["mobile"], "09171234567")
        self.assertEqual(self.store.claim_form_values(self.claim_id)["email"], "zz.crypto@gmail.com")


if __name__ == "__main__":
    unittest.main()
