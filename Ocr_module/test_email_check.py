"""The email check (email_check.py, adviser's revision S2) and "Save
patient" refusing a wrong address (POST /api/claims/save).

No internet or database needed: DNS and the Kickbox API are patched.
"""
import unittest
from unittest import mock

import email_check
from app import create_app


def _patched(resolves=True, disposable=False):
    """DNS says `resolves`, Kickbox's open API says `disposable`."""
    email_check._domain_resolves.cache_clear()
    email_check._is_disposable.cache_clear()
    answer = None if disposable is None else {"disposable": disposable}
    return (mock.patch("email_check._domain_resolves", return_value=resolves),
            mock.patch("email_check._get_json", return_value=answer))


class EmailCheckTests(unittest.TestCase):
    def check(self, address, **kwargs):
        dns, api = _patched(**kwargs)
        with dns, api as get_json:
            return email_check.check_email(address), get_json

    def test_a_good_address_passes(self):
        result, _ = self.check("maria.santos@gmail.com")
        self.assertTrue(result["ok"])

    def test_wrong_format_and_typo(self):
        self.assertFalse(self.check("maria.santos")[0]["ok"])
        result, _ = self.check("maria@gmial.com")
        self.assertFalse(result["ok"])
        self.assertEqual(result["suggestion"], "maria@gmail.com")

    def test_a_domain_that_does_not_exist(self):
        result, _ = self.check("maria@nosuchmailhost.ph", resolves=False)
        self.assertFalse(result["ok"])

    def test_a_throw_away_address_is_refused_and_only_the_domain_is_sent(self):
        result, get_json = self.check("maria.santos@mailinator.com", disposable=True)
        self.assertFalse(result["ok"])
        self.assertIn("throw-away", result["reason"])
        url = get_json.call_args[0][0]
        self.assertTrue(url.endswith("/mailinator.com"), url)
        self.assertNotIn("maria", url)

    def test_api_out_of_reach_or_offline_is_not_called_wrong(self):
        self.assertTrue(self.check("maria@gmail.com", disposable=None)[0]["ok"])
        self.assertTrue(self.check("maria@gmail.com", resolves=None)[0]["ok"])

    def test_full_mailbox_check_only_with_a_key(self):
        dns, api = _patched()
        with dns, api as get_json, mock.patch.dict("os.environ", {"KICKBOX_API_KEY": ""}):
            email_check.check_email("maria@gmail.com")
        self.assertEqual(get_json.call_count, 1)          # the domain question only
        with mock.patch.dict("os.environ", {"KICKBOX_API_KEY": "test-key"}), \
             mock.patch("email_check._is_disposable", return_value=False), \
             mock.patch("email_check._domain_resolves", return_value=True), \
             mock.patch("email_check._get_json", return_value={"result": "undeliverable"}):
            self.assertFalse(email_check.check_email("nobody@gmail.com")["ok"])

    def test_not_applicable_is_accepted_and_never_looked_up(self):
        for value in ("N/A", "n/a", " N/A ", "`"):
            with self.subTest(value=value):
                result, get_json = self.check(value)
                self.assertTrue(result["ok"])
                self.assertTrue(result.get("not_applicable"))
                get_json.assert_not_called()
                self.assertIsNone(email_check.save_problem({"email": value}))
        self.assertFalse(self.check("na@")[0]["ok"])          # an address-like typo is still checked
        for value in ("NA", "none"):                            # printing would keep these, so they are checked
            self.assertFalse(email_check.is_not_applicable(value))

    def test_save_problem(self):
        self.assertIsNone(email_check.save_problem({"email": ""}))
        self.assertIsNone(email_check.save_problem({}))
        dns, api = _patched(disposable=True)
        with dns, api:
            self.assertIn("Email address", email_check.save_problem({"email": "x@mailinator.com"}))


class SavePatientRefusesWrongEmailTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()
        user = {"id": 2, "email": "encoder@test.local", "full_name": "E", "role": "encoder",
                "is_active": 1, "last_login_at": None, "created_at": None}
        patcher = mock.patch("user_store.get_user_by_id", return_value=user)
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.client.session_transaction() as session:
            session["user_id"] = 2

    def test_not_saved_with_a_clear_error(self):
        dns, api = _patched()
        with dns, api, mock.patch("claims_store.save_patient") as save:
            response = self.client.post("/api/claims/save", json={
                "claim_id": None, "values": {"patientLastName": "X", "email": "maria@gmial.com"}})
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertFalse(body["success"])
        self.assertEqual(body["field"], "email")
        self.assertIn("maria@gmail.com", body["error"])
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
