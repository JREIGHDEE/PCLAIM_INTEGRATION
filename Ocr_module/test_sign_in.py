"""Server-side sign-in protection (auth.require_sign_in).

Every page and API needs a signed-in, active account, except the sign-in
page, its CSS/JS/images/fonts, sign-in, sign-up, sign-out, the "fresh
install?" status and /db_health. Pages redirect to the sign-in page; APIs
answer 401 JSON. No database needed: user lookups are patched.
"""
import unittest
from unittest import mock

from app import create_app

ADMIN = {"id": 1, "email": "admin@test.local", "full_name": "Admin", "role": "admin",
         "is_active": 1, "last_login_at": None, "created_at": None}
ENCODER = {**ADMIN, "id": 2, "email": "encoder@test.local", "role": "encoder"}


class SignInWallTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def sign_in(self, user):
        patcher = mock.patch("user_store.get_user_by_id", return_value=user)
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.client.session_transaction() as session:
            session["user_id"] = user["id"] if user else 99

    def test_sign_in_page_and_its_files_are_open(self):
        for url in ("/", "/login.html", "/css/style.css", "/js/login.js", "/js/auth-client.js"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_pages_redirect_to_sign_in(self):
        for url in ("/index.html", "/ocr.html", "/logbook-setup.html", "/review", "/ocr-workspace",
                    "/logbook-setup"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.headers["Location"].endswith("/"), response.headers["Location"])

    def test_apis_answer_401_json(self):
        calls = [("get", "/api/claims/1"), ("get", "/api/claims/1/form-data"), ("post", "/api/claims/1/exported"),
                 ("get", "/api/claims/1/export/cf2"), ("post", "/api/review/upload"), ("get", "/api/review/sessions/1"),
                 ("get", "/api/settings/clinic"), ("get", "/api/auth/me"), ("get", "/grid_templates"),
                 ("post", "/ocr"), ("get", "/export_case_session?case_id=1"), ("get", "/api/testing/summary"),
                 ("get", "/forms/CF2.pdf")]
        for method, url in calls:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 401)
                body = response.get_json()
                self.assertFalse(body["success"])
                self.assertIn("sign in", body["error"].lower())

    def test_sign_in_sign_up_status_and_health_stay_open(self):
        with mock.patch("user_store.count_users", return_value=1):
            self.assertEqual(self.client.get("/api/auth/status").status_code, 200)
        with mock.patch("user_store.authenticate", return_value=None):
            response = self.client.post("/api/auth/login", json={"email": "a@b.c", "password": "wrong"})
        self.assertEqual(response.get_json()["error"], "Incorrect email or password.")  # reached the route
        response = self.client.post("/api/auth/register", json={})
        self.assertEqual(response.status_code, 400)  # reached the route: "password is required."
        with mock.patch("app.test_connection", return_value="10.4.32-MariaDB"):
            self.assertEqual(self.client.get("/db_health").status_code, 200)

    def test_signed_in_user_gets_pages_and_apis(self):
        self.sign_in(ADMIN)
        self.assertEqual(self.client.get("/index.html").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").get_json()["user"]["email"], ADMIN["email"])

    def test_switched_off_account_is_turned_away(self):
        self.sign_in({**ADMIN, "is_active": 0})
        self.assertEqual(self.client.get("/index.html").status_code, 302)
        self.assertEqual(self.client.get("/api/claims/1").status_code, 401)

    def test_admin_only_routes_stay_admin_only(self):
        self.sign_in(ENCODER)
        self.assertEqual(self.client.get("/api/auth/users").status_code, 403)
        self.assertEqual(self.client.post("/api/settings/clinic", json={}).status_code, 403)

    def test_unknown_url_is_still_404_once_signed_in(self):
        # Signed out, it is a 401 like any other API (the catch-all file route).
        self.assertEqual(self.client.get("/api/no-such-thing").status_code, 401)
        self.sign_in(ADMIN)
        self.assertEqual(self.client.get("/api/no-such-thing").status_code, 404)


if __name__ == "__main__":
    unittest.main()
