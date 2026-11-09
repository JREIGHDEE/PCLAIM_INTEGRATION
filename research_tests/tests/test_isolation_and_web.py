"""Isolation (read-only database, outputs/work) and the research tabs
(flag on/off, administrators only, safe uploads and options)."""
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from research_tests import WORK, guard


class IsolationTests(unittest.TestCase):
    def test_main_folders_point_into_outputs_work(self):
        import config
        for folder in (config.UPLOAD_FOLDER, config.REVIEW_CROPS_FOLDER, config.OCR_COMPARE_FOLDER,
                       config.OCR_COMPARE_WORKBOOK):
            self.assertTrue(guard._under(folder, WORK), folder)

    @unittest.skipUnless(guard.database_available(), "MariaDB is not running")
    def test_the_database_refuses_writes(self):
        from db import get_db_cursor
        from errors import DatabaseError
        with self.assertRaises(DatabaseError) as caught:
            # Changes nothing even if it ran (WHERE 1 = 0), and is never committed.
            with get_db_cursor() as cursor:
                cursor.execute("UPDATE ocr_known_entries SET is_active = is_active WHERE 1 = 0")
        message = str(caught.exception).upper()
        # refused by the read-only session, or by the account's SELECT-only grant
        self.assertTrue("READ ONLY" in message or "DENIED" in message, message)

    @unittest.skipUnless(guard.database_available(), "MariaDB is not running")
    def test_reads_still_work(self):
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1 AS one")
            self.assertEqual(cursor.fetchone()["one"], 1)

    def test_research_model_reads_only_the_research_tables(self):
        import paddle_assist
        with mock.patch("pattern_store.has_learned_patterns", side_effect=AssertionError("load_model's fill")), \
             mock.patch("pattern_store.load_patterns", return_value=[]), \
             mock.patch("entry_store.load_entries", return_value=[]):
            model, note = guard.research_model()
        self.assertIsInstance(model, paddle_assist.CorrectionModel)

    def test_one_research_model_everywhere(self):
        import config
        import paddle_assist
        self.assertEqual(config.DB_NAME, os.environ.get("RESEARCH_DB_NAME", "pclaimassist_research"))
        self.assertTrue(getattr(paddle_assist.load_model, "_research_model", False))

    def test_no_silent_fallback(self):
        with mock.patch("pattern_store.load_patterns", side_effect=RuntimeError("no table")):
            with self.assertRaises(RuntimeError):
                guard.research_model()


class WebTests(unittest.TestCase):
    def app(self, flag):
        """The main app as Ocr_module/app.py builds it - its marked RESEARCH
        TESTS block registers the blueprint, or not, by the flag."""
        from app import create_app
        with mock.patch.dict(os.environ, {"ENABLE_RESEARCH_TESTS": flag}):
            app = create_app()
        return app.test_client(), "research" in app.blueprints

    def sign_in(self, client, role):
        user = {"id": 7, "email": f"{role}@test.local", "full_name": role, "role": role, "is_active": 1,
                "last_login_at": None, "created_at": None}
        patcher = mock.patch("user_store.get_user_by_id", return_value=user)
        patcher.start()
        self.addCleanup(patcher.stop)
        with client.session_transaction() as session:
            session["user_id"] = 7

    def test_flag_off_removes_everything(self):
        for flag in ("", "false", "0"):
            client, registered = self.app(flag)
            self.assertFalse(registered)
            self.sign_in(client, "admin")
            for url in ("/ocr-testing/research/api/tabs", "/ocr-testing/research/static/tabs.js",
                        "/ocr-testing/research/handwriting"):
                self.assertEqual(client.get(url).status_code, 404, url)
            # The OCR comparison page itself is still there.
            self.assertEqual(client.get("/ocr-compare").status_code, 200)

    def test_flag_on_admin_sees_the_tabs(self):
        client, registered = self.app("true")
        self.assertTrue(registered)
        self.sign_in(client, "admin")
        tabs = client.get("/ocr-testing/research/api/tabs").get_json()["tabs"]
        self.assertEqual([t["tab"] for t in tabs], [
            "Handwriting (10 Writers)", "Correction Metrics", "Field Mapping", "Validation (Seeded Errors)",
            "Performance", "Image Quality", "User Sessions", "RTH Mistakes", "Results"])
        self.assertEqual(client.get("/ocr-testing/research/static/tabs.js").status_code, 200)
        for t in tabs:
            self.assertEqual(client.get(t["url"]).status_code, 200, t["url"])
        status = client.get("/ocr-testing/research/api/validation/status").get_json()
        self.assertIn("inputs", status)

    def test_encoders_and_signed_out_are_refused(self):
        client, _ = self.app("true")
        self.assertEqual(client.get("/ocr-testing/research/api/tabs").status_code, 401)
        self.sign_in(client, "encoder")
        for method, url in (("get", "/ocr-testing/research/api/tabs"), ("get", "/ocr-testing/research/handwriting"),
                            ("post", "/ocr-testing/research/api/validation/run")):
            self.assertEqual(getattr(client, method)(url).status_code, 403, url)

    def test_options_become_safe_command_line_arguments(self):
        from research_tests.registry import BY_KEY
        from research_tests.web.routes import _cli_args
        from errors import InvalidRequestError
        self.assertEqual(_cli_args(BY_KEY["handwriting"], {"samples": True, "writers": "W01,W02", "fresh": True}),
                         ["--samples", "--writers", "W01,W02", "--fresh"])
        self.assertEqual(_cli_args(BY_KEY["correction_metrics"], {"samples": True, "source": "workbook"}),
                         ["--source", "workbook"])               # this test has no sample data
        for bad in ({"writers": "W01; rm -rf"}, ):
            with self.assertRaises(InvalidRequestError):
                _cli_args(BY_KEY["handwriting"], bad)
        with self.assertRaises(InvalidRequestError):
            _cli_args(BY_KEY["correction_metrics"], {"source": "../../etc"})
        with self.assertRaises(InvalidRequestError):
            _cli_args(BY_KEY["performance"], {"scans": "3 --fresh"})

    def test_uploads_go_to_inputs_and_only_allowed_types(self):
        client, _ = self.app("true")
        self.sign_in(client, "admin")
        with tempfile.TemporaryDirectory() as tmp, mock.patch("research_tests.web.routes.INPUTS", Path(tmp)):
            ok = client.post("/ocr-testing/research/api/handwriting/upload/scans",
                             data={"files": (BytesIO(b"%PDF-1.4"), "W01_caps.pdf")}, content_type="multipart/form-data")
            self.assertEqual(ok.status_code, 200)
            self.assertTrue((Path(tmp) / "scans" / "handwriting" / "W01_caps.pdf").is_file())
            bad = client.post("/ocr-testing/research/api/handwriting/upload/scans",
                              data={"files": (BytesIO(b"x"), "evil.py")}, content_type="multipart/form-data")
            self.assertEqual(bad.status_code, 400)
            sneaky = client.post("/ocr-testing/research/api/handwriting/upload/writers",
                                 data={"files": (BytesIO(b"a,b"), "../../writers.csv")},
                                 content_type="multipart/form-data")
            self.assertEqual(sneaky.status_code, 200)
            self.assertTrue((Path(tmp) / "writers.csv").is_file())     # always saved under its fixed name
            self.assertEqual(client.post("/ocr-testing/research/api/handwriting/upload/nope",
                                         data={"files": (BytesIO(b"x"), "a.csv")}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
