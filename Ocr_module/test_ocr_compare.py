"""The OCR comparison page (ocr_compare.py, ocr_compare_store.py,
routes/compare_routes.py): scoring, reading with a second engine, runs,
cell cut reliability, spreads, the workbook, and who may use it.

No OCR engine, database or real scan needed: the readers are fakes, and
the workbook and runs go to a temporary folder.
"""
import os
import shutil
import tempfile
import unittest
from unittest import mock

import numpy as np
from openpyxl import load_workbook

import config
import logbook_pipeline
import ocr_compare
import ocr_compare_store


class ScoringTests(unittest.TestCase):
    def test_exact_in_capitals_with_spaces_collapsed(self):
        s = ocr_compare.score_reading("NAME", "DELA CRUZ, MARIA S.", "dela  cruz, maria s.")
        self.assertTrue(s["exact"])
        self.assertEqual(s["accuracy"], 100.0)

    def test_character_accuracy(self):
        s = ocr_compare.score_reading("ADDRESS", "CABANTIAN", "CABAMTIAN")
        self.assertFalse(s["exact"])
        self.assertAlmostEqual(s["accuracy"], 100 * (1 - 1 / 9), places=1)

    def test_blank_cell(self):
        self.assertEqual(ocr_compare.score_reading("FINAL DX", "", "")["accuracy"], 100.0)
        self.assertEqual(ocr_compare.score_reading("FINAL DX", "", "X")["accuracy"], 0.0)

    def test_field_mapping_counts_form_fields(self):
        right = ocr_compare.score_reading("NAME", "DELA CRUZ, MARIA SANTOS", "DELA CRUZ, MARIA SANTOS")
        wrong_first = ocr_compare.score_reading("NAME", "DELA CRUZ, MARIA SANTOS", "DELA CRUZ, MARlA SANTOS")
        self.assertGreaterEqual(right["mapped_total"], 2)
        self.assertEqual(right["mapped_right"], right["mapped_total"])
        self.assertEqual(wrong_first["mapped_right"], right["mapped_total"] - 1)

    def test_date_mapping_ignores_how_it_is_written(self):
        s = ocr_compare.score_reading("BDAY", "04-24-1994", "4/24/94")
        self.assertFalse(s["exact"])
        self.assertEqual((s["mapped_right"], s["mapped_total"]), (1, 1))

    def test_best_engine(self):
        hi, lo = {"accuracy": 100.0, "mapped_right": 1}, {"accuracy": 50.0, "mapped_right": 0}
        self.assertEqual(ocr_compare.best_engine({"paddle_corrected": hi, "tesseract_corrected": lo}), "PaddleOCR")
        self.assertEqual(ocr_compare.best_engine({"paddle_corrected": lo, "tesseract_corrected": hi}), "TesseractOCR")
        self.assertEqual(ocr_compare.best_engine({"paddle_corrected": hi, "tesseract_corrected": hi}), "Tie")
        self.assertEqual(ocr_compare.best_engine({"paddle_corrected": hi}), "PaddleOCR")


def _crop():
    image = np.full((40, 160, 3), 255, dtype=np.uint8)
    image[15:25, 20:140] = 0          # some "writing"
    return image


class SecondEngineTests(unittest.TestCase):
    def test_same_steps_as_the_pipeline(self):
        sure = lambda image: [{"text": "maria", "confidence": 0.99}]
        reads = ocr_compare.read_fields_with([{"category": "NAME"}], lambda f: _crop(), sure)
        self.assertEqual(reads[0]["raw_text"], "maria")
        self.assertEqual(reads[0]["status"], logbook_pipeline.ACCEPTED)
        self.assertEqual(reads[0]["value"], "MARIA")          # form capitals

    def test_unsure_cells_get_the_second_look(self):
        unsure = lambda image: [{"text": "mar1a", "confidence": 0.30}]
        seen = []

        def corrector(pairs, progress=None):     # as paddle_assist.apply_reading does
            for field, crop in pairs:
                seen.append(field["raw_text"])
                field["value"], field["status"] = "MARIA", logbook_pipeline.NEEDS_CHECK
        reads = ocr_compare.read_fields_with([{"category": "NAME"}], lambda f: _crop(), unsure, corrector)
        self.assertEqual(seen, ["mar1a"])
        self.assertEqual(reads[0]["raw_text"], "mar1a")       # the engine's own reading is kept
        self.assertEqual(reads[0]["value"], "MARIA")

    def test_progress_after_every_cell(self):
        seen = []
        ocr_compare.read_fields_with([{"category": "NAME"}] * 3, lambda f: _crop(),
                                     lambda i: [{"text": "x", "confidence": 0.99}],
                                     progress=lambda f, m: seen.append(m))
        self.assertEqual(seen, ["cell 1 of 3", "cell 2 of 3", "cell 3 of 3"])

    def test_missing_picture(self):
        reads = ocr_compare.read_fields_with([{"category": "NAME"}], lambda f: None, lambda i: [])
        self.assertEqual(reads[0]["ocr_error"], "No cell picture")


def _result():
    field = lambda cat, raw, value: {"category": cat, "page": 1, "column": 1, "crop": "u/p1_r0_c1.png",
                                     "row_box": None, "raw_text": raw, "confidence": 0.9, "routed_status": "accepted",
                                     "value": value, "row_crop": "u/s0_r0_row.png", "possibly_incomplete": cat == "BDAY"}
    return {"upload_id": "a" * 32, "pages": [{"page": 1, "template": "t", "match_score": 0.9, "rows": 1, "error": None}],
            "image_quality": {"warnings": []},
            "rows": [{"spread": 0, "row": 0, "pages": [1, 2],
                      "fields": [field("NAME", "dela cruz maria", "DELA CRUZ MARIA"), field("BDAY", "4/24/94", "4/24/94")]}]}


class TempFolderTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for name, value in (("OCR_COMPARE_FOLDER", os.path.join(self.tmp, "runs")),
                            ("OCR_COMPARE_WORKBOOK", __import__("pathlib").Path(self.tmp, "results.xlsx"))):
            patcher = mock.patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch("paddle_assist.fix_saved_reading", side_effect=lambda cat, text: text)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def make_run(self):
        tess = [{"raw_text": "dela cruz marla", "confidence": 0.7, "status": "needs_check", "value": "DELA CRUZ MARLA"},
                {"raw_text": "4/24/94", "confidence": 0.8, "status": "accepted", "value": "4/24/94"}]
        return ocr_compare.build_run(_result(), tess, "scan.pdf", {"cells": 2})


class RunTests(TempFolderTestCase):
    def test_build_save_load(self):
        run = self.make_run()
        self.assertEqual(run["rows"][0]["key"], "0-0")
        f = run["rows"][0]["fields"][0]
        self.assertEqual((f["paddle_raw"], f["paddle_corrected"]), ("dela cruz maria", "DELA CRUZ MARIA"))
        self.assertEqual((f["tesseract_raw"], f["tesseract_corrected"]), ("dela cruz marla", "DELA CRUZ MARLA"))
        self.assertEqual(f["side"], "left")
        self.assertEqual((run["rows"][0]["spread_id"], run["rows"][0]["spread_pages"]), ("SP-01", "1-2"))
        self.assertEqual([x["cut_flag"] for x in run["rows"][0]["fields"]], [False, True])
        ocr_compare.save_run(run)
        self.assertEqual(ocr_compare.load_run(run["run_id"])["source_file"], "scan.pdf")
        self.assertEqual(ocr_compare.list_runs()[0]["rows"], 1)

    def test_without_tesseract(self):
        run = ocr_compare.build_run(_result(), None, "scan.pdf", {}, "TesseractOCR could not run")
        self.assertIsNone(run["rows"][0]["fields"][0]["tesseract_raw"])
        scored = ocr_compare.score_field(run["rows"][0]["fields"][0], "DELA CRUZ MARIA")
        self.assertNotIn("tesseract_raw", scored["scores"])
        self.assertEqual(scored["best"], "PaddleOCR")

    def test_unknown_run_ids_are_refused(self):
        for bad in ("../../etc", "abc", "A" * 32):
            with self.assertRaises(ValueError):
                ocr_compare.load_run(bad)

    def test_truth_only_for_this_runs_rows(self):
        run = ocr_compare.set_truth(self.make_run(), {"0-0": ["DELA CRUZ MARIA"], "9-9": ["X"]}, ["0-0", "9-9"])
        self.assertEqual(run["truth"], {"0-0": ["DELA CRUZ MARIA", ""]})
        self.assertEqual(run["checked"], ["0-0"])

    def test_spreads(self):
        self.assertEqual(ocr_compare.spread_id(0), "SP-01")
        self.assertEqual(ocr_compare.spread_id(11), "SP-12")
        rows = [{"spread": 0, "pages": [1, 2]}, {"spread": 0, "pages": [1]}, {"spread": 1, "pages": [3, 4]}]
        self.assertEqual(ocr_compare.spread_pages(rows), {0: "1-2", 1: "3-4"})

    def test_cuts_kept_and_unmarked_cells_count_as_correct(self):
        run = ocr_compare.set_truth(self.make_run(), {}, ["0-0"], {"0-0": ["cut_off", "nonsense"], "9-9": ["wrong"]})
        self.assertEqual(run["cuts"], {"0-0": ["cut_off", ""]})
        items = ocr_compare.scored_rows(run, ["0-0"])
        self.assertEqual([i["cut"] for i in items], ["cut_off", "correct"])
        self.assertEqual(items[0]["spread_id"], "SP-01")

    def test_scored_rows(self):
        run = ocr_compare.set_truth(self.make_run(), {"0-0": ["DELA CRUZ MARIA", "04-24-1994"]}, ["0-0"])
        items = ocr_compare.scored_rows(run, ["0-0"])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["best"], "PaddleOCR")
        self.assertTrue(items[0]["scores"]["paddle_corrected"]["exact"])


class WorkbookTests(TempFolderTestCase):
    def items(self, truth):
        run = ocr_compare.set_truth(self.make_run(), {"0-0": truth}, ["0-0"])
        return ocr_compare.scored_rows(run, ["0-0"])

    def test_rows_and_summary_sheets(self):
        result = ocr_compare_store.save_rows(self.items(["DELA CRUZ MARIA", "04-24-1994"]))
        self.assertEqual((result["added"], result["replaced"], result["total"]), (2, 0, 2))
        book = load_workbook(config.OCR_COMPARE_WORKBOOK)
        self.assertEqual(book.sheetnames, ["Rows", "Summary", "Spreads"])
        rows = list(book["Rows"].iter_rows(values_only=True))
        self.assertEqual(list(rows[0]), ocr_compare_store.HEADERS)
        self.assertEqual(rows[1][0], 1)                         # Test ID
        overall = [r for r in result["summary"] if r["field"] == "All fields"][0]
        self.assertEqual(overall["n"], 2)
        self.assertEqual(overall["recommended"], "PaddleOCR")

    def test_text_beginning_with_equals_is_kept_as_text(self):
        # A reading like "=z w ah" was stored as an Excel formula (an error in
        # Excel, and nothing when read back): it must stay the text it is.
        ocr_compare_store.save_rows(self.items(["=Z W AH", "04-24-1994"]))
        cell = load_workbook(config.OCR_COMPARE_WORKBOOK)["Rows"].cell(row=2, column=13)   # Ground Truth
        self.assertEqual((cell.value, cell.data_type), ("=Z W AH", "s"))
        values = list(load_workbook(config.OCR_COMPARE_WORKBOOK, data_only=True)["Rows"].iter_rows(values_only=True))
        self.assertEqual(values[1][12], "=Z W AH")
        # Saving again (lines read back from the file) keeps it as text.
        ocr_compare_store.save_rows(self.items(["=Z W AH", "04-24-1994"]))
        self.assertEqual(load_workbook(config.OCR_COMPARE_WORKBOOK)["Rows"].cell(row=2, column=13).data_type, "s")

    def test_saving_a_row_again_replaces_it(self):
        ocr_compare_store.save_rows(self.items(["WRONG", "WRONG"]))
        result = ocr_compare_store.save_rows(self.items(["DELA CRUZ MARIA", "04-24-1994"]))
        self.assertEqual((result["replaced"], result["total"]), (2, 2))
        self.assertEqual(ocr_compare_store.summary()["total"], 2)

    def test_cell_cut_reliability(self):
        run = ocr_compare.set_truth(self.make_run(), {"0-0": ["DELA CRUZ MARIA", "XX"]}, ["0-0"],
                                    {"0-0": ["correct", "cut_off"]})
        result = ocr_compare_store.save_rows(ocr_compare.scored_rows(run, ["0-0"]))
        overall = [r for r in result["summary"] if r["field"] == "All fields"][0]
        self.assertEqual((overall["cut_correct"], overall["cut_off"], overall["cut_wrong"]), (50.0, 1, 0))
        self.assertEqual((overall["pipeline_flagged"], overall["flag_agreed"]), (1, 1))   # BDAY flagged and cut off
        # Accuracy on the correctly cut cells only: the name, read exactly.
        self.assertEqual(overall["paddle_corrected_accuracy_cut_ok"], 100.0)
        line = list(load_workbook(config.OCR_COMPARE_WORKBOOK)["Rows"].iter_rows(values_only=True))[2]
        header = ocr_compare_store.HEADERS
        self.assertEqual(line[header.index("Cell Cut")], "Cut off")
        self.assertEqual(line[header.index("Pipeline: Writing Outside Cut")], "Yes")

    def test_spreads_sheet(self):
        result = ocr_compare_store.save_rows(self.items(["DELA CRUZ MARIA", "04-24-1994"]))
        self.assertEqual(len(result["spreads"]), 1)
        spread = result["spreads"][0]
        self.assertEqual((spread["field"], spread["pages"], spread["rows"], spread["n"]),
                         ("SP-01 · scan.pdf", "1-2", 1, 2))
        sheet = list(load_workbook(config.OCR_COMPARE_WORKBOOK)["Spreads"].iter_rows(values_only=True))
        self.assertEqual(sheet[1][:4], ("SP-01 · scan.pdf", "1-2", 1, 2))
        line = list(load_workbook(config.OCR_COMPARE_WORKBOOK)["Rows"].iter_rows(values_only=True))[1]
        header = ocr_compare_store.HEADERS
        self.assertEqual((line[header.index("Spread ID")], line[header.index("Spread Pages")]), ("SP-01", "1-2"))

    def test_a_workbook_from_before_new_columns_still_reads(self):
        from openpyxl import Workbook
        old = [h for h in ocr_compare_store.HEADERS if h not in ("Cell Cut", "Pipeline: Writing Outside Cut")]
        book = Workbook()
        sheet = book.active
        sheet.title = "Rows"
        sheet.append(old)
        sheet.append([1 if h == "Test ID" else "other" if h == "Run ID" else None for h in old])
        book.save(config.OCR_COMPARE_WORKBOOK)
        result = ocr_compare_store.save_rows(self.items(["A", "B"]))
        self.assertEqual(result["total"], 3)

    def test_clear(self):
        ocr_compare_store.save_rows(self.items(["A", "B"]))
        self.assertEqual(ocr_compare_store.clear()["total"], 0)
        self.assertEqual(ocr_compare_store.summary()["total"], 0)


class RouteTests(TempFolderTestCase):
    def setUp(self):
        super().setUp()
        from app import create_app
        self.client = create_app().test_client()

    def sign_in(self, role):
        user = {"id": 7, "email": f"{role}@test.local", "full_name": role, "role": role, "is_active": 1,
                "last_login_at": None, "created_at": None}
        patcher = mock.patch("user_store.get_user_by_id", return_value=user)
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.client.session_transaction() as session:
            session["user_id"] = 7

    def test_encoders_are_refused(self):
        self.sign_in("encoder")
        for method, url in (("get", "/api/ocr-compare/status"), ("get", "/api/ocr-compare/runs"),
                            ("post", "/api/ocr-compare/jobs"), ("post", "/api/ocr-compare/clear")):
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 403)

    def test_admin_status_and_saving(self):
        self.sign_in("admin")
        with mock.patch("ocr_compare.tesseract_available", return_value="not installed"), \
             mock.patch("routes.compare_routes.load_template_payloads", return_value=[]):
            body = self.client.get("/api/ocr-compare/status").get_json()
        self.assertEqual(body["tesseract_error"], "not installed")
        run = self.make_run()
        ocr_compare.save_run(run)
        response = self.client.post(f"/api/ocr-compare/runs/{run['run_id']}/save", json={
            "rows": ["0-0"], "truth": {"0-0": ["DELA CRUZ MARIA", "04-24-1994"]}, "checked": ["0-0"]})
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["run_saved"], ["0-0"])
        self.assertEqual(ocr_compare.load_run(run["run_id"])["saved"], ["0-0"])
        self.assertEqual(self.client.get("/api/ocr-compare/results.xlsx").status_code, 200)

    def test_queue_same_scan_once_and_cancel(self):
        import io
        import time
        import review_jobs
        self.sign_in("admin")

        def fake_start(work, path):               # a job that never gets its turn
            job_id = "job-%d" % len(review_jobs._jobs)
            review_jobs._jobs[job_id] = {"state": "waiting", "progress": 0.0, "message": "Waiting to start",
                                         "result": None, "error": None, "updated_at": time.time(),
                                         "created_at": time.time()}
            self.addCleanup(review_jobs._jobs.pop, job_id, None)
            if os.path.exists(path):
                os.remove(path)
            return job_id
        post = lambda data: self.client.post("/api/ocr-compare/jobs", content_type="multipart/form-data",
                                             data={"file": (io.BytesIO(data), "scan.png")})
        with mock.patch("review_jobs.start", side_effect=fake_start):
            first = post(b"same scan").get_json()
            again = post(b"same scan").get_json()
            other = post(b"another scan").get_json()
        self.assertEqual(again["job_id"], first["job_id"])
        self.assertTrue(again["already"])
        self.assertNotEqual(other["job_id"], first["job_id"])
        job = self.client.get(f"/api/ocr-compare/jobs/{other['job_id']}").get_json()
        self.assertEqual(job["ahead"], 1)                       # waits for the first
        self.assertEqual(self.client.post(f"/api/ocr-compare/jobs/{first['job_id']}/cancel").get_json()["state"],
                         "cancelling")
        self.assertTrue(self.client.get(f"/api/ocr-compare/jobs/{first['job_id']}").get_json()["cancelling"])

    def test_page_is_behind_sign_in(self):
        self.assertEqual(self.client.get("/ocr-compare").status_code, 302)


if __name__ == "__main__":
    unittest.main()
