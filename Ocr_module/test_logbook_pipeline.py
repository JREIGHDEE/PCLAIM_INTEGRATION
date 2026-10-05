"""Tests for the logbook upload -> review session -> claim flow
(logbook_pipeline.py, routes/review_routes.py).

Same flat-file unittest convention as the other test_*.py files.

The unit tests are pure (no OCR model, no DB) and always run.

LogbookEndToEndTests runs a sample scan through the whole flow with the real
PaddleOCR model and the real database: upload -> IQ-01 -> template match ->
PaddleOCR -> per-row review sessions -> review -> claim. The sample scan is a
two-page logbook spread generated here (printed text laid out on the
project's own calibrated grid templates) - real logbook scans contain
patient data and are never committed. Everything it creates (DB rows, crop
images) is removed in tearDown. Skipped with a clear reason when PaddleOCR,
the database, or database/migrations/003 is not available.
"""
import json
import os
import shutil
import tempfile
import unittest
import uuid
from unittest import mock

import cv2
import numpy as np

import config
import logbook_pipeline
from logbook_pipeline import ACCEPTED, MANUAL, NEEDS_CHECK
from philhealth import case_bridge

GRID_TEMPLATES = (
    "left_pages_FINAK_1789214042272.json",
    "right_pages_finallll_1789214071747.json",
)

# Two patient entries written across a two-page spread, the same way the
# physical logbook splits one entry across its left and right pages.
SAMPLE_PATIENTS = [
    {
        "CASE #": "1001", "DATE & TIME OF ADMISSION": "06/10/2026 8:30 AM",
        "NAME": "Dela Cruz, Maria Santos", "BDAY": "03/15/1995",
        "ADDRESS": "123 Rizal St., Quezon City",
        "ADMITTING DIAGNOSIS": "Pregnancy uterine full term",
        "DATE & TIME OF DELIVERY": "06/10/2026 9:45 AM",
        "FINAL DIAGNOSIS": "NSD live birth",
        "DATE & TIME OF DISCHARGE": "06/12/2026 10:00 AM",
    },
    {
        "CASE #": "1002", "DATE & TIME OF ADMISSION": "06/11/2026 2:15 PM",
        "NAME": "Reyes, Ana Lopez", "BDAY": "11/02/1998",
        "ADDRESS": "45 Mabini Ave., Davao City",
        "ADMITTING DIAGNOSIS": "Pregnancy uterine in labor",
        "DATE & TIME OF DELIVERY": "06/11/2026 6:40 PM",
        "FINAL DIAGNOSIS": "NSD live birth",
        "DATE & TIME OF DISCHARGE": "06/13/2026 9:00 AM",
    },
]
_DATETIME_CATEGORIES = {
    "DATE & TIME OF ADMISSION", "DATE & TIME OF DELIVERY", "DATE & TIME OF DISCHARGE",
}


def _load_grid_template(filename):
    with open(os.path.join(os.path.dirname(__file__), "grid_templates", filename), encoding="utf-8") as handle:
        return json.load(handle)


def write_sample_spread(path, patients=SAMPLE_PATIENTS):
    """Write a two-page logbook spread PDF laid out on the saved left/right
    grid templates: printed header row, blue ruling lines (like the real
    ledger), one patient entry per row. Pages are half the templates'
    pixel size, since the pipeline renders PDFs at 2x."""
    import fitz

    left, right = (_load_grid_template(name) for name in GRID_TEMPLATES)
    # Both halves of a spread share the same rows - use the left (odd)
    # page's first row for both, as on the physical logbook.
    first_row_y = left["rowTemplate"]["y"] / 2
    rule = (0.45, 0.65, 0.95)

    doc = fitz.open()
    for template in (left, right):
        width, height = template["imageWidth"] / 2, template["imageHeight"] / 2
        page = doc.new_page(width=width, height=height)
        xs = [fraction * width for fraction in template["gridLines"]]
        categories = [segment["category"] for segment in template["segmentInfo"]]
        for x in xs:
            page.draw_line((x, 8), (x, height - 20), color=rule, width=0.8)

        def write(column, y, text, small):
            page.insert_text((xs[column] + 3, y), text, fontsize=8 if small else 10, fontname="helv")

        for column, category in enumerate(categories):
            write(column, first_row_y + 13, category.replace("DATE & TIME OF ", ""), False)
        y = first_row_y + 30
        page.draw_line((xs[0], y), (width - 4, y), color=rule, width=0.8)
        for patient in patients:
            for column, category in enumerate(categories):
                write(column, y + 22, patient[category], category in _DATETIME_CATEGORIES)
            y += 36
            page.draw_line((xs[0], y), (width - 4, y), color=rule, width=0.8)
    doc.save(path)
    doc.close()


def _field(category, raw_text, confidence, status=None):
    return {
        "category": category, "raw_text": raw_text, "confidence": confidence,
        "status": status or logbook_pipeline.route_confidence(confidence),
        "value": raw_text,
    }


class RouteConfidenceTests(unittest.TestCase):
    def test_thresholds_come_from_config(self):
        with mock.patch.object(config, "OCR_CONFIDENCE_ACCEPT", 0.9), \
                mock.patch.object(config, "OCR_CONFIDENCE_REVIEW", 0.5):
            self.assertEqual(logbook_pipeline.route_confidence(0.89), NEEDS_CHECK)
            self.assertEqual(logbook_pipeline.route_confidence(0.5), NEEDS_CHECK)
            self.assertEqual(logbook_pipeline.route_confidence(0.49), MANUAL)

    def test_thesis_bands(self):
        with mock.patch.object(config, "OCR_CONFIDENCE_ACCEPT", 0.85), \
                mock.patch.object(config, "OCR_CONFIDENCE_REVIEW", 0.65):
            self.assertEqual(logbook_pipeline.route_confidence(1.0), ACCEPTED)
            self.assertEqual(logbook_pipeline.route_confidence(0.85), ACCEPTED)
            self.assertEqual(logbook_pipeline.route_confidence(0.849), NEEDS_CHECK)
            self.assertEqual(logbook_pipeline.route_confidence(0.65), NEEDS_CHECK)
            self.assertEqual(logbook_pipeline.route_confidence(0.6499), MANUAL)
            self.assertEqual(logbook_pipeline.route_confidence(0.0), MANUAL)

    def test_no_text_needs_manual_encoding(self):
        self.assertEqual(logbook_pipeline.route_confidence(None), MANUAL)


def _two_line_cell():
    """White cell with two lines of dark 'handwriting' strokes."""
    cell = np.full((90, 240, 3), 255, dtype=np.uint8)
    cv2.putText(cell, "MARY DEYINE", (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 30), 2)
    cv2.putText(cell, "ISRAEL DAMIAN", (8, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 30), 2)
    return cell


def _box(x1, y1, x2, y2):
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


class OcrCellTests(unittest.TestCase):
    def test_confidence_is_lowest_token_not_mean(self):
        raw, confidence, tokens, error, _ = logbook_pipeline.ocr_cell(
            None, lambda _: [{"text": "123 Rizal", "confidence": 0.99}, {"text": "St.", "confidence": 0.6}]
        )
        self.assertEqual(raw, "123 Rizal St.")
        self.assertEqual(confidence, 0.6)
        self.assertEqual(len(tokens), 2)
        self.assertIsNone(error)

    def test_blank_tokens_count_as_no_text(self):
        raw, confidence, tokens, error, _ = logbook_pipeline.ocr_cell(
            None, lambda _: [{"text": "  ", "confidence": 0.9}])
        self.assertEqual((raw, confidence, tokens, error), ("", None, [], None))

    def test_ocr_failure_is_reported_not_hidden(self):
        def broken(_):
            raise RuntimeError("model crashed")
        raw, confidence, _, error, _ = logbook_pipeline.ocr_cell(None, broken)
        self.assertEqual((raw, confidence), ("", None))
        self.assertIn("OCR failed", error)

    def test_missed_line_is_retried_with_a_margin(self):
        # First read skips the top line (as PaddleOCR did on a real logbook
        # name touching the crop edge); the retry with a margin reads both.
        calls = []

        def ocr(image):
            calls.append(image.shape)
            if len(calls) == 1:
                return [{"text": "ISRAEL DAMIAN", "confidence": 0.97, "box": _box(4, 50, 236, 86)}]
            m = 16
            return [{"text": "MARY DEYINE", "confidence": 0.9, "box": _box(4 + m, 5 + m, 236 + m, 40 + m)},
                    {"text": "ISRAEL DAMIAN", "confidence": 0.97, "box": _box(4 + m, 50 + m, 236 + m, 86 + m)}]

        raw, confidence, _, _, flags = logbook_pipeline.ocr_cell(_two_line_cell(), ocr)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][:2], (90 + 32, 240 + 32))
        self.assertEqual(raw, "MARY DEYINE ISRAEL DAMIAN")
        self.assertEqual(confidence, 0.9)
        self.assertFalse(flags["incomplete"])

    def test_reading_that_still_misses_writing_is_never_auto_accepted(self):
        only_bottom = lambda image: [{"text": "ISRAEL DAMIAN", "confidence": 0.97,
                                      "box": _box(4, 50, 236, 86) if image.shape[0] == 90 else _box(20, 66, 252, 102)}]
        raw, confidence, _, _, flags = logbook_pipeline.ocr_cell(_two_line_cell(), only_bottom)
        self.assertEqual(raw, "ISRAEL DAMIAN")
        self.assertTrue(flags["incomplete"])
        self.assertEqual(logbook_pipeline.field_status("NAME", confidence, flags), NEEDS_CHECK)

    def test_fully_covered_reading_is_not_retried(self):
        calls = []

        def ocr(image):
            calls.append(1)
            return [{"text": "MARY DEYINE ISRAEL DAMIAN", "confidence": 0.95, "box": _box(0, 0, 240, 90)}]

        _, _, _, _, flags = logbook_pipeline.ocr_cell(_two_line_cell(), ocr)
        self.assertEqual(len(calls), 1)
        self.assertFalse(flags["incomplete"])

    def test_empty_logbook_cell_is_empty_not_manual(self):
        blank = np.full((90, 240, 3), 255, dtype=np.uint8)
        cv2.line(blank, (0, 45), (239, 45), (200, 150, 90), 1)  # printed ruling line only
        raw, confidence, _, _, flags = logbook_pipeline.ocr_cell(blank, lambda _: [])
        self.assertTrue(flags["blank"])
        self.assertEqual(logbook_pipeline.field_status("DATE & TIME OF DELIVERY", confidence, flags),
                         logbook_pipeline.EMPTY)
        # Every entry must have these - a blank one still needs typing.
        self.assertEqual(logbook_pipeline.field_status("NAME", confidence, flags), MANUAL)

    def test_unreadable_writing_is_manual_not_empty(self):
        _, confidence, _, _, flags = logbook_pipeline.ocr_cell(_two_line_cell(), lambda _: [])
        self.assertFalse(flags["blank"])
        self.assertEqual(logbook_pipeline.field_status("ADDRESS", confidence, flags), MANUAL)


class RowFilterTests(unittest.TestCase):
    def _row(self, row, texts):
        return {"spread": 0, "row": row, "pages": [1],
                "fields": [_field(f"C{i}", text, 0.9 if text else None) for i, text in enumerate(texts)]}

    def test_header_blank_and_stray_rows_are_dropped(self):
        rows = [
            self._row(0, ["", "", ""]),                       # empty seed band
            self._row(1, ["CASE #", "NAME", "ADDRESS"]),      # printed header
            self._row(2, ["1001", "Dela Cruz, Maria", ""]),   # patient
            self._row(3, ["", "12", ""]),                     # page number / stray mark
        ]
        kept = logbook_pipeline._drop_non_patient_rows(rows)
        self.assertEqual([r["row"] for r in kept], [2])

    def test_header_words_in_a_later_row_do_not_drop_a_patient(self):
        rows = [self._row(i, ["x", "y", ""]) for i in range(3)]
        rows.append(self._row(3, ["Normal delivery", "Admitting diagnosis noted", "Name"]))
        kept = logbook_pipeline._drop_non_patient_rows(rows)
        self.assertIn(3, [r["row"] for r in kept])


class ApplyReviewTests(unittest.TestCase):
    def _ocr_data(self):
        return {"fields": [
            _field("NAME", "Dela Cruz, Maria", 0.95),
            {**_field("ADDRESS", "l23 Rlzal", 0.4), "value": ""},
            _field("BDAY", "03/15/1995", 0.7),
        ]}

    def test_manual_field_must_be_typed(self):
        _, _, missing = logbook_pipeline.apply_review(self._ocr_data(), {"NAME": "Dela Cruz, Maria"})
        self.assertEqual(missing, ["ADDRESS"])
        _, _, missing = logbook_pipeline.apply_review(self._ocr_data(), {"ADDRESS": "   "})
        self.assertEqual(missing, ["ADDRESS"])

    def test_submitted_values_replace_ocr_values_and_mark_edits(self):
        values, ocr_data, missing = logbook_pipeline.apply_review(
            self._ocr_data(), {"ADDRESS": "123 Rizal St.", "BDAY": "03/15/1995"}
        )
        self.assertEqual(missing, [])
        self.assertEqual(values, {"NAME": "Dela Cruz, Maria", "ADDRESS": "123 Rizal St.", "BDAY": "03/15/1995"})
        by_category = {f["category"]: f for f in ocr_data["fields"]}
        self.assertTrue(by_category["ADDRESS"]["edited"])
        self.assertFalse(by_category["BDAY"]["edited"])
        # The original OCR output is kept alongside the reviewed value.
        self.assertEqual(by_category["ADDRESS"]["raw_text"], "l23 Rlzal")


class ReviewJobTests(unittest.TestCase):
    def _wait(self, job_id):
        import time
        import review_jobs
        for _ in range(200):
            job = review_jobs.get(job_id)
            if job["state"] in ("done", "failed"):
                return job
            time.sleep(0.02)
        self.fail("job did not finish")

    def _temp_file(self):
        handle, path = tempfile.mkstemp(suffix=".pdf")
        os.close(handle)
        return path

    def test_progress_then_result_and_temp_file_removed(self):
        import threading
        import review_jobs
        seen = []
        started = threading.Event()
        ids = []

        def work(progress):
            started.wait(5)
            for fraction in (0.25, 0.5, 1.0):
                progress(fraction, "Reading page 1 of 1")
                seen.append(review_jobs.get(ids[0])["progress"])
            return {"success": True, "sessions": []}

        path = self._temp_file()
        job_id = review_jobs.start(work, path)
        ids.append(job_id)
        started.set()
        job = self._wait(job_id)
        self.assertEqual(job["state"], "done")
        self.assertEqual(job["progress"], 1.0)
        self.assertEqual(job["result"], {"success": True, "sessions": []})
        # Rising, and below 100% until the work has really finished.
        self.assertEqual(seen, sorted(seen))
        self.assertLess(seen[-1], 1.0)
        self.assertFalse(os.path.exists(path))

    def test_failure_message_is_kept_for_the_user(self):
        import review_jobs

        def work(progress):
            raise ValueError("Could not read the uploaded image.")

        job = self._wait(review_jobs.start(work, self._temp_file()))
        self.assertEqual(job["state"], "failed")
        self.assertEqual(job["error"], "Could not read the uploaded image.")

    def test_unexpected_errors_are_not_shown_raw(self):
        import review_jobs

        def work(progress):
            raise RuntimeError("paddle internals: tensor shape mismatch")

        job = self._wait(review_jobs.start(work, self._temp_file()))
        self.assertEqual(job["state"], "failed")
        self.assertNotIn("tensor", job["error"])


class DeferManualToFormsTests(unittest.TestCase):
    def _ocr_data(self):
        return {"fields": [
            {**_field("NAME", "Dela Cruz, Maria", 0.95)},
            {**_field("ADDRESS", "l23 Rlzal", 0.4), "value": ""},
            {**_field("FINAL DIAGNOSIS", "NSO", 0.3), "value": ""},
        ]}

    def test_send_to_forms_may_leave_manual_fields_for_the_forms(self):
        _, ocr_data, missing = logbook_pipeline.apply_review(self._ocr_data(), {}, defer_manual=True)
        self.assertEqual(missing, [])
        deferred = {f["category"] for f in ocr_data["fields"] if f["deferred_to_forms"]}
        self.assertEqual(deferred, {"ADDRESS", "FINAL DIAGNOSIS"})

    def test_fields_a_claim_needs_must_still_be_typed_in_the_review(self):
        ocr_data = {"fields": [{**_field("NAME", "Dela Cruz", 0.3), "value": ""},
                               {**_field("BDAY", "", None), "value": ""}]}
        _, _, missing = logbook_pipeline.apply_review(ocr_data, {}, defer_manual=True)
        self.assertEqual(missing, ["NAME", "BDAY"])

    def test_manual_field_marked_empty_is_not_missing(self):
        values, ocr_data, missing = logbook_pipeline.apply_review(
            self._ocr_data(), {}, submitted_parts={"ADDRESS": {"empty": True}, "FINAL DIAGNOSIS": {"empty": True}})
        self.assertEqual(missing, [])
        by_category = {f["category"]: f for f in ocr_data["fields"]}
        self.assertTrue(by_category["ADDRESS"]["marked_empty"])
        self.assertEqual(values["ADDRESS"], "")

    def test_without_defer_every_manual_field_is_required(self):
        _, _, missing = logbook_pipeline.apply_review(self._ocr_data(), {})
        self.assertEqual(missing, ["ADDRESS", "FINAL DIAGNOSIS"])


class TargetFieldTests(unittest.TestCase):
    def test_every_logbook_category_has_a_destination(self):
        for category in config.TRAINING_CATEGORIES:
            self.assertTrue(case_bridge.target_fields(category), category)

    def test_targets_name_real_columns(self):
        columns = [t["column"] for t in case_bridge.target_fields("DATE & TIME OF DELIVERY")]
        self.assertEqual(columns, ["claims.delivery_date", "claims.delivery_time", "claims.am_pm_delivery"])
        self.assertEqual(case_bridge.target_fields("CASE #")[0]["key"], None)
        self.assertEqual(case_bridge.target_fields("SOMETHING ELSE"), [])


def _paddle_available():
    try:
        import paddleocr  # noqa: F401
        return True
    except Exception:
        return False


def _database_ready():
    """Database reachable and migrations 001-003 applied."""
    try:
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM case_sessions WHERE Field = 'review_status'")
            if not cursor.fetchone():
                return False
            cursor.execute("SHOW COLUMNS FROM patients WHERE Field = 'address'")
            return bool(cursor.fetchone())
    except Exception:
        return False


@unittest.skipUnless(_paddle_available(), "PaddleOCR is not installed in this environment")
@unittest.skipUnless(_database_ready(), "Database unreachable or migrations 001-003 not applied")
class LogbookEndToEndTests(unittest.TestCase):
    """upload scan -> IQ-01 -> template match -> PaddleOCR -> review
    sessions -> review -> claim, through the real Flask routes."""

    # Printed text OCRs with ~0.95+ confidence. To exercise the other two
    # routing bands deterministically, these sample values come back from
    # the (otherwise real) PaddleOCR call at handwriting-like confidence.
    SIMULATED_CONFIDENCE = {"Rizal": 0.72, "Mabini": 0.41, "6:40": 0.38}

    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.client = create_app().test_client()

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="logbook_e2e_")
        templates_dir = os.path.join(self.tmp, "grid_templates")
        os.makedirs(templates_dir)
        for name in GRID_TEMPLATES:
            shutil.copy(os.path.join(os.path.dirname(__file__), "grid_templates", name), templates_dir)
        self.sample_pdf = os.path.join(self.tmp, "sample_spread.pdf")
        write_sample_spread(self.sample_pdf)

        from ocr_engine import extract_tokens_from_array

        def ocr(image):
            tokens = extract_tokens_from_array(image)
            for token in tokens:
                for marker, confidence in self.SIMULATED_CONFIDENCE.items():
                    if marker in token["text"]:
                        token["confidence"] = confidence
            return tokens

        self.patches = [
            # Only the two calibrated templates - a groupmate's extra local
            # templates must not change which one matches.
            mock.patch.object(config, "GRID_TEMPLATES_FOLDER", templates_dir),
            mock.patch.object(config, "REVIEW_CROPS_FOLDER", os.path.join(self.tmp, "crops")),
            mock.patch("routes.review_routes.extract_tokens_from_array", ocr),
        ]
        for patch in self.patches:
            patch.start()
        self.session_ids = []
        self.claim_ids = []

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        from db import get_db_cursor
        with get_db_cursor(commit=True) as cursor:
            for claim_id in self.claim_ids:
                cursor.execute("SELECT encounter_id FROM claims WHERE id = %s", (claim_id,))
                encounter_id = cursor.fetchone()["encounter_id"]
                cursor.execute("SELECT patient_id FROM encounters WHERE id = %s", (encounter_id,))
                patient_id = cursor.fetchone()["patient_id"]
                cursor.execute("DELETE FROM claims WHERE id = %s", (claim_id,))
                cursor.execute("DELETE FROM encounters WHERE id = %s", (encounter_id,))
                cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
            for session_id in self.session_ids:
                cursor.execute("DELETE FROM case_sessions WHERE id = %s", (session_id,))
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _upload(self, path, filename):
        with open(path, "rb") as handle:
            response = self.client.post(
                "/api/review/upload",
                data={"file": (handle, filename)},
                content_type="multipart/form-data",
            )
        body = response.get_json()
        self.session_ids.extend(s["session_id"] for s in body.get("sessions", []))
        return response, body

    def test_sample_scan_through_the_whole_flow(self):
        response, body = self._upload(self.sample_pdf, "sample_spread.pdf")
        self.assertEqual(response.status_code, 200, body)

        # IQ-01 ran on both pages and passed on a clean scan.
        self.assertEqual(body["image_quality"]["rule_id"], "IQ-01")
        self.assertTrue(body["image_quality"]["passed"], body["image_quality"]["warnings"])
        self.assertEqual([p["page"] for p in body["image_quality"]["pages"]], [1, 2])

        # Each page matched its own calibrated template.
        self.assertEqual([p["template"] for p in body["pages"]], list(GRID_TEMPLATES))
        self.assertTrue(all(p["error"] is None for p in body["pages"]))

        # One pending review session per patient row - header row dropped,
        # both pages of the spread merged into the same session.
        sessions = body["sessions"]
        self.assertEqual(len(sessions), len(SAMPLE_PATIENTS))
        for session, expected in zip(sessions, SAMPLE_PATIENTS):
            self.assertEqual(session["review_status"], "pending")
            fields = {f["category"]: f for f in session["fields"]}
            self.assertEqual(set(fields), set(config.TRAINING_CATEGORIES))
            for category, field in fields.items():
                # Every field carries raw OCR text, confidence, its crop and
                # the claim field(s) it maps to.
                self.assertIn("raw_text", field)
                self.assertIn("confidence", field)
                self.assertEqual(field["target_fields"], case_bridge.target_fields(category))
                crop = self.client.get(f"/api/review/crops/{field['crop']}")
                self.assertEqual(crop.status_code, 200, field["crop"])
                self.assertEqual(crop.mimetype, "image/png")
                image = cv2.imdecode(np.frombuffer(crop.data, np.uint8), cv2.IMREAD_COLOR)
                self.assertGreater(image.shape[0] * image.shape[1], 0)
                crop.close()
            self.assertEqual(fields["CASE #"]["raw_text"], expected["CASE #"])
            self.assertEqual(fields["NAME"]["raw_text"], expected["NAME"])
            self.assertEqual(fields["NAME"]["status"], ACCEPTED)
            self.assertEqual(fields["NAME"]["value"], expected["NAME"])
            self.assertEqual(session["case_id"], expected["CASE #"])

        first = {f["category"]: f for f in sessions[0]["fields"]}
        second = {f["category"]: f for f in sessions[1]["fields"]}
        # 65-84%: pre-filled but flagged for checking.
        self.assertEqual(first["ADDRESS"]["status"], NEEDS_CHECK)
        self.assertEqual(first["ADDRESS"]["value"], first["ADDRESS"]["raw_text"])
        # <65%: OCR text kept for reference, value left empty to be typed.
        self.assertEqual(second["ADDRESS"]["status"], MANUAL)
        self.assertEqual(second["ADDRESS"]["value"], "")
        self.assertIn("Mabini", second["ADDRESS"]["raw_text"])

        # The upload can be reopened later with the same data.
        reopened = self.client.get(f"/api/review/uploads/{body['upload_id']}").get_json()
        self.assertEqual([s["session_id"] for s in reopened["sessions"]], self.session_ids)
        self.assertEqual(reopened["sessions"][0]["image_quality"]["rule_id"], "IQ-01")

        # A pending session can't become a claim.
        session_id = sessions[1]["session_id"]
        response = self.client.post("/api/claims/generate", json={"session_id": session_id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_code"], "review_incomplete")

        # Submitting without typing the manual-encoding field is refused.
        response = self.client.put(f"/api/review/sessions/{session_id}", json={"values": {}})
        self.assertEqual(response.status_code, 400)
        self.assertIn("ADDRESS", response.get_json()["error"])

        # Review: confirm/correct every field from the scan, as a person would.
        for session, expected in zip(sessions, SAMPLE_PATIENTS):
            response = self.client.put(f"/api/review/sessions/{session['session_id']}", json={"values": expected})
            self.assertEqual(response.status_code, 200, response.get_json())
            self.assertEqual(response.get_json()["review_status"], "reviewed")

        # Reviewed session -> claim.
        for session, expected in zip(sessions, SAMPLE_PATIENTS):
            response = self.client.post("/api/claims/generate", json={"session_id": session["session_id"]})
            body = response.get_json()
            self.assertEqual(response.status_code, 200, body)
            self.claim_ids.append(body["claim_id"])
            self.assertEqual(body["warnings"], [])

            claim = self.client.get(f"/api/claims/{body['claim_id']}").get_json()
            self.assertEqual(claim["status"], "draft")
            fields = {f["key"]: f["value"] for f in claim["fields"]}
            last, first_and_middle = expected["NAME"].split(", ")
            self.assertEqual(fields["patientLastName"], last)
            self.assertEqual(fields["patientFirstName"], first_and_middle.split()[0])
            self.assertEqual(fields["patientAddress"], expected["ADDRESS"])
            self.assertEqual(fields["admissionDx"], expected["ADMITTING DIAGNOSIS"])
            self.assertEqual(fields["dischargeDx"], expected["FINAL DIAGNOSIS"])

    def test_send_to_forms_saves_the_claim_and_serves_tagged_form_data(self):
        response, body = self._upload(self.sample_pdf, "sample_spread.pdf")
        self.assertEqual(response.status_code, 200, body)
        session = body["sessions"][1]
        fields = {f["category"]: f for f in session["fields"]}
        self.assertEqual(fields["ADDRESS"]["status"], MANUAL)
        self.assertEqual(fields["DATE & TIME OF DELIVERY"]["status"], MANUAL)

        # The review page's "Send to Forms": submit what's on screen, leaving
        # the manual-encoding fields blank for the forms...
        values = {f["category"]: f["value"] for f in session["fields"]}
        values["DATE & TIME OF DISCHARGE"] = SAMPLE_PATIENTS[1]["DATE & TIME OF DISCHARGE"]
        response = self.client.put(f"/api/review/sessions/{session['session_id']}",
                                   json={"values": values, "defer_manual": True})
        self.assertEqual(response.status_code, 200, response.get_json())
        # ...then save the patient/encounter/claim through the existing API.
        response = self.client.post("/api/claims/generate", json={"session_id": session["session_id"]})
        self.assertEqual(response.status_code, 200, response.get_json())
        claim_id = response.get_json()["claim_id"]
        self.claim_ids.append(claim_id)

        # PClaimAssist loads the claim by id - all four forms' keys.
        response = self.client.get(f"/api/claims/{claim_id}/form-data",
                                   headers={"Origin": "http://127.0.0.1:5500"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:5500")
        form = response.get_json()
        self.assertEqual(form["session_id"], session["session_id"])
        self.assertEqual(form["data"]["patientLastName"], "Reyes")
        self.assertEqual(form["data"]["patientDOB"], "1998-11-02")
        self.assertEqual(form["data"]["dateAdmitted"], "2026-06-11")
        self.assertEqual(form["data"]["timeAdmitted"], "14:15")
        self.assertEqual(form["data"]["amPmAdmitted"], "PM")
        self.assertEqual(form["data"]["admissionDx"], SAMPLE_PATIENTS[1]["ADMITTING DIAGNOSIS"])

        tags = form["fields"]
        self.assertEqual(tags["patientLastName"]["status"], "accepted")
        self.assertEqual(tags["admissionDx"]["status"], "accepted")
        # The reviewer's discharge value counts as a correction only if OCR
        # didn't already read it exactly.
        typed_discharge = values["DATE & TIME OF DISCHARGE"]
        self.assertEqual(tags["dateDischarge"]["status"],
                         "accepted" if fields["DATE & TIME OF DISCHARGE"]["raw_text"] == typed_discharge else "typed")
        # Manual encoding deferred to the forms: empty and required there.
        for key in ("deliveryDate", "deliveryTime"):
            self.assertEqual(tags[key]["status"], "required", key)
            self.assertNotIn(key, form["data"])
        self.assertEqual(form["ocr_reference"], {})
        self.assertIn("memberPIN", form["no_ocr_source"])
        self.assertIn("mannerOfDelivery", form["no_ocr_source"])

    def test_single_dark_page_image_warns_but_still_runs_ocr(self):
        # One page as a photo/scan image (not PDF), darkened so IQ-01 fails.
        page_image = logbook_pipeline.load_pages(self.sample_pdf)[0][1]
        dark = (page_image.astype(np.float32) * 0.22).astype(np.uint8)
        image_path = os.path.join(self.tmp, f"dark_{uuid.uuid4().hex[:6]}.png")
        cv2.imwrite(image_path, dark)

        response, body = self._upload(image_path, "dark_page.png")
        self.assertEqual(response.status_code, 200, body)
        self.assertEqual(body["image_quality"]["rule_id"], "IQ-01")
        self.assertFalse(body["image_quality"]["passed"])
        self.assertTrue(any("too dark" in w for w in body["image_quality"]["warnings"]))

        # Advisory only: the page was still matched, OCR'd and turned into
        # review sessions, and every session carries the warning.
        self.assertIsNone(body["pages"][0]["error"])
        self.assertEqual(len(body["sessions"]), len(SAMPLE_PATIENTS))
        for session in body["sessions"]:
            self.assertFalse(session["image_quality"]["passed"])
            self.assertEqual({f["category"] for f in session["fields"]},
                             {"CASE #", "DATE & TIME OF ADMISSION", "NAME", "BDAY", "ADDRESS"})

    def test_background_reading_reports_progress_then_the_same_result(self):
        import time
        with open(self.sample_pdf, "rb") as handle:
            response = self.client.post("/api/review/jobs", data={"file": (handle, "sample_spread.pdf")},
                                        content_type="multipart/form-data")
        self.assertEqual(response.status_code, 202, response.get_json())
        job_id = response.get_json()["job_id"]

        progress = []
        for _ in range(600):
            job = self.client.get(f"/api/review/jobs/{job_id}").get_json()
            progress.append(job["progress"])
            if job["state"] in ("done", "failed"):
                break
            time.sleep(0.2)
        self.assertEqual(job["state"], "done", job.get("error"))
        result = job["result"]
        self.session_ids.extend(s["session_id"] for s in result["sessions"])
        self.assertEqual(progress, sorted(progress))
        self.assertEqual(progress[-1], 1.0)
        self.assertTrue(any(0 < p < 1 for p in progress))
        self.assertEqual(len(result["sessions"]), len(SAMPLE_PATIENTS))
        self.assertEqual(result["image_quality"]["rule_id"], "IQ-01")

    def test_structured_review_safeguards_and_claim(self):
        response, body = self._upload(self.sample_pdf, "sample_spread.pdf")
        self.assertEqual(response.status_code, 200, body)
        session = body["sessions"][0]
        kinds = {f["category"]: f["kind"] for f in session["fields"]}
        self.assertEqual(kinds["NAME"], "name")
        self.assertEqual(kinds["DATE & TIME OF ADMISSION"], "datetime")
        self.assertEqual(kinds["CASE #"], "case_number")
        parts = {f["category"]: f["parts"] for f in session["fields"]}
        self.assertEqual(parts["DATE & TIME OF ADMISSION"],
                         {"date": "2026-06-10", "hour": "8", "minute": "30", "am_pm": "AM"})
        url = f"/api/review/sessions/{session['session_id']}"

        # Problems: letters in the case number, went home before admitted.
        bad = {**parts, "CASE #": {"number": "10O1"},
               "DATE & TIME OF DISCHARGE": {"date": "2026-06-09", "hour": "", "minute": "", "am_pm": ""}}
        response = self.client.put(url, json={"parts": bad})
        self.assertEqual(response.status_code, 400)
        problems = {p["category"] for p in response.get_json()["problems"]}
        self.assertEqual(problems, {"CASE #", "DATE & TIME OF DISCHARGE"})

        # Unusual but possible: needs a confirmation, then saves.
        name = {"last": "Dela Cruz", "first": "Maria Liza", "middle": "Santos", "suffix": ""}
        odd = {**parts, "NAME": name, "BDAY": {"date": "2019-03-15"}}
        response = self.client.put(url, json={"parts": odd})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error_code"], "review_needs_confirmation")
        response = self.client.put(url, json={"parts": {**odd, "BDAY": {"date": "1995-03-15"}}})
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["values"]["NAME"], "Dela Cruz, Maria Liza Santos")

        response = self.client.post("/api/claims/generate", json={"session_id": session["session_id"]})
        self.assertEqual(response.status_code, 200, response.get_json())
        self.claim_ids.append(response.get_json()["claim_id"])
        claim = {f["key"]: f["value"] for f in self.client.get(f"/api/claims/{self.claim_ids[-1]}").get_json()["fields"]}
        # Two-word first name kept exactly as the person split it.
        self.assertEqual((claim["patientLastName"], claim["patientFirstName"], claim["patientMiddleName"]),
                         ("Dela Cruz", "Maria Liza", "Santos"))
        self.assertEqual((claim["timeAdmitted"], claim["amPmAdmitted"]), ("08:30", "AM"))

    def test_review_page_shows_iq_banner_slot_at_the_top(self):
        html = self.client.get("/review").get_data(as_text=True)
        self.assertLess(html.index('id="iqBanner"'), html.index('id="sessions"'))


if __name__ == "__main__":
    unittest.main()
