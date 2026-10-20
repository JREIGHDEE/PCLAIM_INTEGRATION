"""Tests for what Send to Forms fills in beyond the logbook columns
themselves: the address split into the forms' parts, a ditto address, the
patient's sex, and the "please check" tags they get (no database)."""
import unittest

from philhealth import case_bridge, form_prefill
from philhealth.address_parser import is_ditto, split_address


class SplitAddressTests(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual(split_address("PUROK 12, BRGY. CABANTIAN, DAVAO CITY"), {
            "addr_street": "PUROK 12", "addr_barangay": "CABANTIAN",
            "addr_city": "DAVAO CITY", "addr_province": "DAVAO DEL SUR"})

    def test_lot_subdivision_and_known_barangay_without_keywords(self):
        self.assertEqual(split_address("BLK 8 LOT 1 EMILY HOMES CABANTIAN, DC"), {
            "addr_lot": "BLK 8 LOT 1", "addr_subdivision": "EMILY HOMES", "addr_barangay": "CABANTIAN",
            "addr_city": "DAVAO CITY", "addr_province": "DAVAO DEL SUR"})

    def test_phase_goes_with_the_subdivision(self):
        parts = split_address("BLK 4 LOT 48 PHASE 1 DECA HOMES CABANTIAN, DAVAO CITY")
        self.assertEqual(parts["addr_subdivision"], "DECA HOMES PHASE 1")
        self.assertNotIn("addr_street", parts)

    def test_barangay_gives_its_city(self):
        self.assertEqual(split_address("brgy. sasa"), {
            "addr_barangay": "SASA", "addr_city": "DAVAO CITY", "addr_province": "DAVAO DEL SUR"})

    def test_province_written_out_is_not_the_city(self):
        parts = split_address("Purok 4 Communal Davao del Sur")
        self.assertEqual(parts["addr_street"], "PUROK 4")
        self.assertEqual(parts["addr_province"], "DAVAO DEL SUR")

    def test_other_city_without_guessing_its_province(self):
        self.assertEqual(split_address("123 Rizal St., Quezon City"),
                         {"addr_street": "123 RIZAL ST", "addr_city": "QUEZON CITY"})

    def test_nothing_made_up(self):
        self.assertEqual(split_address(""), {})
        self.assertEqual(split_address("PUROK 3"), {"addr_street": "PUROK 3"})

    def test_ditto_marks(self):
        for text in ("-DO-", "do", "- D0 -", "same", '"'):
            self.assertTrue(is_ditto(text), text)
            self.assertEqual(split_address(text), {})
        self.assertFalse(is_ditto("DOMINGA"))


class InferSexTests(unittest.TestCase):
    def test_newborn_name(self):
        self.assertEqual(case_bridge.infer_patient_sex("BABY GIRL LORNA QUIADO", [])[0], "Female")
        self.assertEqual(case_bridge.infer_patient_sex("Baby Boy Cruz", [])[0], "Male")

    def test_maternal_diagnosis(self):
        for dx in ("G1P1 (1001) PU 35 2/7 WKS AOG", "PRENATAL CHECK UP", "POST PARTUM VISIT",
                   "DELIVERED VIA NSVD TO A LIVE TERM BABY BOY"):
            self.assertEqual(case_bridge.infer_patient_sex("ANA REYES", [dx])[0], "Female", dx)

    def test_no_guess(self):
        self.assertEqual(case_bridge.infer_patient_sex("ANA REYES", ["WELL BABY CARE"]), (None, None))
        self.assertEqual(case_bridge.infer_patient_sex("ANA REYES", ["FAMILY PLANNING"]), (None, None))
        self.assertEqual(case_bridge.infer_patient_sex("JUAN CRUZ", ["FEVER"]), (None, None))


class DraftTests(unittest.TestCase):
    VALUES = {"NAME": "Reyes, Ana", "BDAY": "11/02/1998", "DATE & TIME OF ADMISSION": "06/11/2026 2:15 PM",
              "ADMITTING DIAGNOSIS": "PRENATAL CHECK UP"}

    def test_address_split_and_sex(self):
        patient, _, claims, _ = case_bridge.draft_patient_and_encounter(
            {**self.VALUES, "ADDRESS": "PUROK 7 BRGY. INDANGAN, DAVAO CITY"})
        self.assertEqual(patient["address"], "PUROK 7 BRGY. INDANGAN, DAVAO CITY")
        self.assertEqual(patient["sex"], "Female")
        self.assertEqual(claims["addr_barangay"], "INDANGAN")
        self.assertEqual(claims["addr_street"], "PUROK 7")

    def test_ditto_takes_the_row_above(self):
        patient, _, claims, warnings = case_bridge.draft_patient_and_encounter(
            {**self.VALUES, "ADDRESS": "-DO-"}, previous_address="SUKAYA HOMES CABANTIAN, DAVAO CITY")
        self.assertEqual(patient["address"], "SUKAYA HOMES CABANTIAN, DAVAO CITY")
        self.assertEqual(claims["addr_subdivision"], "SUKAYA HOMES")
        self.assertEqual(warnings, [])

    def test_ditto_with_nothing_above_is_left_to_type(self):
        patient, _, claims, warnings = case_bridge.draft_patient_and_encounter({**self.VALUES, "ADDRESS": "-DO-"})
        self.assertNotIn("address", patient)
        self.assertFalse(any(k.startswith("addr_") for k in claims))
        self.assertTrue(any("ditto" in w for w in warnings))


class FormTagTests(unittest.TestCase):
    def test_worked_out_values_are_please_check(self):
        rows = {
            "patient": {"last_name": "REYES", "first_name": "ANA", "sex": "Female",
                        "address": "PUROK 7 BRGY. INDANGAN, DAVAO CITY"},
            "encounter": {"admission_dx": "PRENATAL CHECK UP"},
            "claim": {"addr_street": "PUROK 7", "addr_barangay": "INDANGAN", "addr_city": "DAVAO CITY"},
        }
        out = form_prefill.build_form_data(rows)
        self.assertEqual(out["data"]["addrBarangay"], "INDANGAN")
        for key in ("addrStreet", "addrBarangay", "addrCity", "patientSex"):
            self.assertEqual(out["fields"][key]["status"], form_prefill.NEEDS_CHECK, key)
        self.assertIn("PUROK 7 BRGY. INDANGAN", out["fields"]["addrBarangay"]["reason"])
        self.assertIn("PRENATAL", out["fields"]["patientSex"]["reason"])
        self.assertNotIn("addrZip", out["fields"])  # not found: not tagged, left to type


class DateReadingTests(unittest.TestCase):
    """Logbook dates as staff write them and as OCR misreads them."""

    def test_date_found_despite_a_garbled_time(self):
        self.assertEqual(case_bridge._parse_date_flexible("05-21-20 10.COAM"), "2020-05-21")
        self.assertEqual(case_bridge._parse_date_flexible("10-01-24 :00Mm"), "2024-10-01")

    def test_ocr_look_alikes_inside_a_date(self):
        self.assertEqual(case_bridge._parse_date_flexible("O8-2I-26 1O:3O AM"), "2026-08-21")
        self.assertEqual(case_bridge._parse_time_flexible("O8-2I-26 1O:3O AM"), ("10:30", "AM"))

    def test_dots_and_semicolons_in_times(self):
        self.assertEqual(case_bridge._parse_time_flexible("10.01.26 7.30 PM"), ("19:30", "PM"))
        self.assertEqual(case_bridge._parse_date_flexible("10.01.26 7.30 PM"), "2026-10-01")
        self.assertEqual(case_bridge._parse_time_flexible("1;20 am"), ("01:20", "AM"))

    def test_unreadable_or_impossible_dates_are_not_guessed(self):
        for text in ("08-21-2u 11:00 Am", "0F-2-20 16.C0A", "13-40-26 10:00", "-23- f101PM"):
            self.assertIsNone(case_bridge._parse_date_flexible(text), text)

    def test_usual_formats_still_work(self):
        self.assertEqual(case_bridge._parse_date_flexible("06/23/2026 11:15 AM"), "2026-06-23")
        self.assertEqual(case_bridge._parse_date_flexible("June 3, 2026"), "2026-06-03")
        self.assertEqual(case_bridge._parse_date_flexible("03-14-97"), "1997-03-14")


class UnreadableAdmissionDateTests(unittest.TestCase):
    """A review can't be saved with an admission date the claim can't use."""

    def _ocr_data(self, text):
        return {"fields": [{"category": "DATE & TIME OF ADMISSION", "raw_text": text, "value": text,
                            "status": "needs_check", "confidence": 0.7}]}

    def test_unreadable_admission_date_must_be_typed(self):
        from logbook_pipeline import apply_review
        _, _, missing = apply_review(self._ocr_data("08-21-2u 11:00 Am"), {})
        self.assertEqual(missing, ["DATE & TIME OF ADMISSION"])

    def test_readable_or_typed_date_is_fine(self):
        from logbook_pipeline import apply_review
        self.assertEqual(apply_review(self._ocr_data("08-21-26 11:00 AM"), {})[2], [])
        parts = {"DATE & TIME OF ADMISSION": {"date": "2026-08-21", "hour": "11", "minute": "00", "am_pm": "AM"}}
        self.assertEqual(apply_review(self._ocr_data("08-21-2u 11:00 Am"), {}, submitted_parts=parts)[2], [])


if __name__ == "__main__":
    unittest.main()
