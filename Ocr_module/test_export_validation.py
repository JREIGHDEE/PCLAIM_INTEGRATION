"""Validation before export.

- PClaimAssist's own export (js/pdf/pdf-overlay.js) must run with
  validation on, through one gate on both export paths.
- The server's CF2/CSF export refuses while a critical rule of
  validation-rules.js fires (mapping_service.critical_rule_problems), says
  which, and on success marks the claim exported and deletes its crops.
No database needed: claim reads and writes are patched.
"""
import json
import os
import re
import unittest
from datetime import date
from unittest import mock

from app import create_app
from philhealth import mapping_service

PDF_OVERLAY_JS = os.path.join(os.path.dirname(__file__), "..", "PClaimAssist", "js", "pdf", "pdf-overlay.js")

READY = {
    "patientLastName": "CRUZ", "patientFirstName": "ANA", "memberPIN": "12-345678901-2",
    "dateAdmitted": "2026-10-20", "dateDischarge": "2026-10-21", "deliveryDate": "2026-10-20",
    "memberDOB": "1995-03-15", "cf4ChiefComplaint": "LABOR PAINS", "cf4CourseOrder1": "UPON ADMISSION ...",
    "dxADiagnosis": "PREGNANCY UTERINE", "cf4FinalDiagnosis": "pregnancy uterine",
}


def rule_ids(data):
    return [rule for rule, _ in mapping_service.critical_rule_problems(data)]


class CriticalRuleTests(unittest.TestCase):
    def test_ready_claim_has_no_problems(self):
        self.assertEqual(rule_ids(READY), [])

    def test_each_rule_fires(self):
        cases = {
            "MF-01": {"patientLastName": "", "patientFirstName": ""},
            "MF-02": {"memberPIN": ""},
            "MF-04": {"dateAdmitted": ""},
            "MF-05": {"dateDischarge": ""},
            "MF-07": {"cf4ChiefComplaint": ""},
            "MF-08": {"cf4CourseOrder1": ""},
            "IF-01": {"memberPIN": "12-3456"},
            "IF-02": {"memberPIN": "12-34567890A-2"},
            "IF-03": {"lmp": "2026-02-30"},
            "IC-03": {"dateDischarge": "2026-10-19", "deliveryDate": ""},
            "IC-04": {"memberDOB": "2026-10-25"},
            "IC-09": {"cf4FinalDiagnosis": "SOMETHING ELSE"},
            "IC-08": {"dateDischarge": "2026-10-20"},
        }
        for rule, change in cases.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, rule_ids({**READY, **change}))

    def test_short_cf2_delivery_diagnosis_matches_cf4(self):
        # CF2 "SPONTANEOUS VERTEX DELIVERY", CF4 the full final diagnosis.
        self.assertNotIn("IC-09", rule_ids({**READY, "dxADiagnosis": "SPONTANEOUS VERTEX DELIVERY",
                                            "cf4FinalDiagnosis": "PREGNANCY UTERINE FULL TERM ... DELIVERED VIA NSVD"}))

    def test_short_cf2_delivery_diagnosis_does_not_cover_a_cesarean(self):
        # The clinic's short wording stands for a normal delivery only.
        for cf4 in ("PUFT 37 WKS AOG DELIVERED VIA LOW SEGMENT CESAREAN SECTION", "ACUTE GASTROENTERITIS"):
            with self.subTest(cf4=cf4):
                self.assertIn("IC-09", rule_ids({**READY, "dxADiagnosis": "SPONTANEOUS VERTEX DELIVERY",
                                                 "cf4FinalDiagnosis": cf4}))

    def test_no_philhealth_member_needs_no_pin(self):
        self.assertEqual(rule_ids({**READY, "memberPIN": "", "memberNoPhilhealth": True}), [])

    def test_course_in_the_second_box_counts(self):
        self.assertEqual(rule_ids({**READY, "cf4CourseOrder1": "", "cf4CourseOrder2": "DISCHARGED"}), [])

    def test_message_names_each_rule(self):
        message = mapping_service.critical_rules_message([("MF-07", "CF4 chief complaint is missing.")])
        self.assertIn("MF-07 CF4 chief complaint is missing.", message)


class BrowserExportGateTests(unittest.TestCase):
    def setUp(self):
        with open(PDF_OVERLAY_JS, encoding="utf-8") as handle:
            self.js = handle.read()

    def test_validation_is_on(self):
        self.assertRegex(self.js, r"const SKIP_VALIDATION_FOR_EXPORT = false;")

    def test_both_export_paths_use_the_gate(self):
        for function in ("exportFilledPDF", "exportAllForms"):
            body = re.search(r"async function %s\([^)]*\) \{(.*?)\n\}" % function, self.js, re.S).group(1)
            self.assertIn("if (exportBlocked()) return;", body, function)

    def test_only_printable_text_is_drawn(self):
        # The PMRF's monthly income ("₱25,000") stopped every newborn's PDF:
        # Helvetica (WinAnsi) has no peso sign.
        build = re.search(r"async function buildFilledPdf\(.*?\n\}", self.js, re.S).group(0)
        self.assertIn("const printable = new Set(font.getCharacterSet());", build)
        self.assertIn(".replace(/₱\\s*/g, 'PHP ')", build)
        self.assertRegex(build, r"const safeVal = pdfSafeText\(")
        for draw in re.findall(r"drawText\((\w+)", build):
            self.assertIn(draw, ("text", "row"), "every drawn text comes from safeVal")

    def test_empty_and_not_applicable_boxes_print_blank(self):
        # N/A never appears on the saved forms: an empty box is not filled
        # with N/A, and a box marked N/A ("N/A", "n/a", "NA", "N.A.", `) prints empty.
        build = re.search(r"async function buildFilledPdf\(.*?\n\}", self.js, re.S).group(0)
        self.assertNotIn("val = 'N/A'", build)
        self.assertIn("if (!val) return;", build)
        strip = re.search(r"function stripNotApplicable\(value\) \{.*?\n\}", self.js, re.S).group(0)
        self.assertIn(r"/^\s*N\.?\s?A\.?\s*$/i", strip)

    def test_server_export_prints_not_applicable_blank(self):
        from philhealth import pdf_export
        drawn = []
        page = mock.Mock(insert_textbox=lambda *a, **k: drawn.append(a), insert_text=lambda *a, **k: drawn.append(a))
        field = {"left": 10, "top": 10, "w": 50, "fs": 8}
        for value in ("N/A", "n/a", "NA", "N.A.", "`", ""):
            drawn.clear()
            pdf_export._draw_field(page, field, value, 600, 800)
            self.assertEqual(drawn, [], value)
        pdf_export._draw_field(page, field, "DELA CRUZ", 600, 800)       # a real value still prints
        self.assertEqual(len(drawn), 1)

    def test_gate_runs_the_rules_fresh(self):
        gate = re.search(r"function exportBlocked\(\) \{(.*?)\n\}", self.js, re.S).group(1)
        self.assertIn("runValidationRules(getComputedValue, state.data)", gate)
        self.assertNotIn("lastValidationResult", gate)


def _rows(form_values):
    return {
        "patient": {"id": 7, "last_name": "CRUZ", "first_name": "ANA", "middle_name": None, "name_ext": None,
                    "date_of_birth": date(1995, 3, 15), "sex": "Female", "pin": None, "address": None},
        "encounter": {"id": 8, "patient_id": 7, "case_session_id": 9, "date_admitted": date(2026, 10, 20),
                      "time_admitted": "10:00", "am_pm_admitted": "AM", "date_discharge": date(2026, 10, 21),
                      "time_discharge": "10:00", "am_pm_discharge": "AM", "disposition": "Improved",
                      "accommodation": "Non-Private", "chief_complaint": "LABOR PAINS",
                      "admission_dx": "PREGNANCY UTERINE", "discharge_dx": "PREGNANCY UTERINE"},
        "claim": {"id": 5, "encounter_id": 8, "status": "ready", "hci_pan": "120000012345",
                  "hci_name": "SAMPLE CLINIC", "member_pin": "12-345678901-2",
                  "delivery_date": date(2026, 10, 20), "form_values": json.dumps(form_values)},
    }


SESSION = {"id": 9, "ocr_data": {"fields": [{"category": "NAME", "crop": "up1/p1_r2_c3.png"}]}}


class ServerExportTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()
        patcher = mock.patch("user_store.get_user_by_id", return_value={
            "id": 1, "email": "t@test.local", "full_name": "T", "role": "admin", "is_active": 1,
            "last_login_at": None, "created_at": None})
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.client.session_transaction() as session:
            session["user_id"] = 1
        self.marked = self.patch("claims_store.mark_exported")
        self.deleted = self.patch("crop_cleanup.delete_session_crops", return_value=2)
        self.patch("claims_store.get_claim_form_source", return_value={"rows": None, "session": SESSION})

    def patch(self, target, **kwargs):
        patcher = mock.patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_refused_while_a_critical_rule_fires(self):
        self.patch("claims_store.get_claim", return_value=_rows({}))   # no CF4 details yet
        response = self.client.get("/api/claims/5/export/cf2")
        self.assertEqual(response.status_code, 400)
        error = response.get_json()["error"]
        self.assertIn("MF-07", error)
        self.assertIn("MF-08", error)
        self.marked.assert_not_called()
        self.deleted.assert_not_called()

    def test_exports_marks_exported_and_deletes_crops(self):
        self.patch("claims_store.get_claim", return_value=_rows(
            {"cf4ChiefComplaint": "LABOR PAINS", "cf4CourseOrder1": "UPON ADMISSION ..."}))
        response = self.client.get("/api/claims/5/export/cf2")
        self.assertEqual(response.status_code, 200,
                         None if response.status_code == 200 else response.get_json())
        self.assertEqual(response.mimetype, "application/pdf")
        self.marked.assert_called_once_with(5)
        self.deleted.assert_called_once_with(SESSION)

    def test_browser_export_marks_exported_and_deletes_crops(self):
        self.patch("claims_store.get_claim", return_value=_rows({}))
        response = self.client.post("/api/claims/5/exported")
        self.assertEqual(response.status_code, 200)
        self.marked.assert_called_once_with(5)
        self.deleted.assert_called_once_with(SESSION)

    def test_browser_export_of_unknown_claim(self):
        self.patch("claims_store.get_claim", return_value=None)
        self.assertEqual(self.client.post("/api/claims/404/exported").status_code, 404)
        self.marked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
