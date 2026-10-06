"""Tests for the shared form-field mapping (philhealth/field_catalog.py
FORM_FIELDS) and claim -> PClaimAssist form prefill (philhealth/form_prefill.py).

Same flat-file unittest convention as the other test_*.py files. Pure - no
DB, no Flask. The sync tests read PClaimAssist's own files so the one
Python mapping can't silently drift from the forms it feeds.
"""
import os
import re
import unittest
from datetime import date
from decimal import Decimal

from philhealth import field_catalog, form_prefill
from philhealth.field_catalog import FORM_FIELDS, NON_FORM_KEYS, OCR_CATEGORY_KEYS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


def _state_data_keys():
    app_js = _read("PClaimAssist", "js", "app.js")
    block = app_js[app_js.index("  data: {"):app_js.index("\n  }\n};")]
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    return set(re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*:", block)) - {"data"}


def _schema_columns():
    schema = _read("database", "schema.sql")
    return {
        m.group(1): set(re.findall(r"^\s*`(\w+)`", m.group(2), re.M))
        for m in re.finditer(r"CREATE TABLE `(\w+)` \((.*?)\) ENGINE", schema, re.S)
    }


FORM_KEYS = set(FORM_FIELDS) - NON_FORM_KEYS


class MappingSyncTests(unittest.TestCase):
    def test_every_form_key_exists_in_pclaimassist_state(self):
        self.assertEqual(FORM_KEYS - _state_data_keys(), set())

    def test_every_pclaimassist_field_has_a_database_home(self):
        self.assertEqual(_state_data_keys() - FORM_KEYS, set())

    def test_every_form_key_has_an_input(self):
        inputs = set(re.findall(r'data-autofill="([A-Za-z0-9]+)"', _read("PClaimAssist", "index.html")))
        self.assertEqual(FORM_KEYS - inputs, set())

    def test_every_mapped_column_exists_in_the_schema(self):
        columns = _schema_columns()
        missing = [(k, f.table, f.column) for k, f in FORM_FIELDS.items()
                   if f.column not in columns.get(f.table, set())]
        self.assertEqual(missing, [])

    def test_ocr_targets_are_mapped_fields(self):
        for category, keys in OCR_CATEGORY_KEYS.items():
            for key in keys:
                self.assertIn(key, FORM_FIELDS, category)

    def test_claim_review_subset_comes_from_the_same_table(self):
        for key, (table, column) in field_catalog.KEY_SOURCE.items():
            self.assertEqual((FORM_FIELDS[key].table, FORM_FIELDS[key].column), (table, column))


def _rows(**claim):
    return {
        "patient": {"last_name": "Dela Cruz", "first_name": "Maria", "middle_name": None,
                    "date_of_birth": date(1995, 3, 15), "address": "123 Rizal St., Quezon City"},
        "encounter": {"date_admitted": date(2026, 6, 10), "time_admitted": "08:30",
                      "am_pm_admitted": "AM", "date_discharge": None, "time_discharge": None,
                      "am_pm_discharge": None, "admission_dx": "Pregnancy uterine full term",
                      "discharge_dx": None},
        "claim": {"hci_pan": "000001234", "hci_name": "Clinic", "delivery_date": date(2026, 6, 10),
                  "delivery_time": "09:45", "am_pm_delivery": None, "risk_asthma": 1,
                  "age_of_menarche": Decimal("13.0"), **claim},
    }


def _ocr(category, status, value, raw_text=None, edited=False, confidence=0.9):
    return {"category": category, "status": status, "value": value, "edited": edited,
            "raw_text": value if raw_text is None else raw_text, "confidence": confidence}


def _session(*fields):
    return {"id": 7, "ocr_data": {"fields": list(fields)}}


class BuildFormDataTests(unittest.TestCase):
    def test_values_are_keyed_by_form_key_and_serialized(self):
        result = form_prefill.build_form_data(
            _rows(),
            prenatal_visits=[{"visit_number": 3, "visit_date": date(2026, 2, 1), "weight": Decimal("61.50"),
                              "aog": "20 wks", "cr": None, "rr": None, "bp": "110/70", "temp": None}],
            postpartum_care=[{"care_item": "breastfeeding", "done": 1, "remarks": "Exclusive"}],
        )
        data = result["data"]
        self.assertEqual(data["patientLastName"], "Dela Cruz")
        self.assertEqual(data["patientDOB"], "1995-03-15")
        self.assertEqual(data["timeAdmitted"], "08:30")
        self.assertIs(data["riskAsthma"], True)
        self.assertEqual(data["ageOfMenarche"], "13")
        self.assertEqual(data["pncDate3"], "2026-02-01")
        self.assertEqual(data["pncWeight3"], "61.5")
        self.assertEqual(data["pncBp3"], "110/70")
        self.assertIs(data["ppBreastfeedingDone"], True)
        self.assertEqual(data["ppBreastfeedingRemarks"], "Exclusive")
        # Nulls are left out, and the logbook address is not a form field.
        self.assertNotIn("dateDischarge", data)
        self.assertNotIn("patientAddress", data)

    def test_ocr_statuses(self):
        session = _session(
            _ocr("NAME", "accepted", "Dela Cruz, Maria"),
            _ocr("ADMITTING DIAGNOSIS", "needs_check", "Pregnancy uterine full term", confidence=0.7),
            _ocr("BDAY", "manual_encoding_required", "03/15/1995", raw_text="03/1S/l995", edited=True),
            _ocr("FINAL DIAGNOSIS", "manual_encoding_required", "", raw_text="NSO"),
            _ocr("DATE & TIME OF DISCHARGE", "manual_encoding_required", ""),
            _ocr("DATE & TIME OF DELIVERY", "accepted", "06/10/2026 9:45"),
            _ocr("ADDRESS", "accepted", "123 Rizal St., Quezon City"),
        )
        fields = form_prefill.build_form_data(_rows(), session=session)["fields"]
        self.assertEqual(fields["patientLastName"]["status"], "accepted")
        self.assertEqual(fields["patientFirstName"]["status"], "accepted")
        # No middle name in the logbook is not an error.
        self.assertNotIn("patientMiddleName", fields)
        self.assertEqual(fields["admissionDx"]["status"], "needs_check")
        self.assertEqual(fields["admissionDx"]["confidence"], 0.7)
        self.assertEqual(fields["patientDOB"]["status"], "typed")
        # Manual encoding left for the forms -> required and empty.
        self.assertEqual(fields["dischargeDx"]["status"], "required")
        self.assertIn("Manual encoding required", fields["dischargeDx"]["reason"])
        self.assertEqual(fields["dischargeDx"]["raw_text"], "NSO")
        self.assertEqual(fields["dateDischarge"]["status"], "required")
        self.assertEqual(fields["timeDischarge"]["status"], "required")
        # No discharge time -> its AM/PM isn't separately required.
        self.assertNotIn("amPmDischarge", fields)
        # Time read without AM/PM -> the AM/PM must be chosen by staff.
        self.assertEqual(fields["deliveryDate"]["status"], "accepted")
        self.assertEqual(fields["amPmDelivery"]["status"], "required")
        self.assertIn("could not be read", fields["amPmDelivery"]["reason"])
        # Facility defaults are labelled as such.
        self.assertEqual(fields["hciPAN"]["status"], "default")

    def test_empty_logbook_boxes_are_tagged_empty_not_required(self):
        session = _session(
            {**_ocr("FINAL DIAGNOSIS", "manual_encoding_required", ""), "marked_empty": True},
            _ocr("DATE & TIME OF DISCHARGE", "empty", ""),
        )
        fields = form_prefill.build_form_data(_rows(), session=session)["fields"]
        self.assertEqual(fields["dischargeDx"]["status"], "empty")
        self.assertEqual(fields["dateDischarge"]["status"], "empty")
        self.assertEqual(fields["timeDischarge"]["status"], "empty")
        self.assertNotIn("amPmDischarge", fields)
        self.assertFalse(any(f["status"] == "required" for f in fields.values()))

    def test_address_is_a_reference_not_split_into_form_fields(self):
        result = form_prefill.build_form_data(
            _rows(), session=_session(_ocr("ADDRESS", "accepted", "123 Rizal St., Quezon City")))
        self.assertEqual(result["ocr_reference"], {"ADDRESS": "123 Rizal St., Quezon City"})
        self.assertFalse(any(k.startswith("addr") for k in result["fields"]))

    def test_claim_without_ocr_session_has_no_ocr_tags(self):
        fields = form_prefill.build_form_data(_rows())["fields"]
        self.assertEqual({f["status"] for f in fields.values()}, {"default"})

    def test_no_ocr_source_lists_every_other_form_field(self):
        no_source = set(form_prefill.build_form_data(_rows())["no_ocr_source"])
        self.assertIn("memberPIN", no_source)
        self.assertIn("disposition", no_source)
        self.assertIn("pncTemp12", no_source)
        self.assertNotIn("patientLastName", no_source)
        self.assertNotIn("hciPAN", no_source)
        self.assertEqual(no_source | field_catalog.AUTO_OCR_KEYS | field_catalog.AUTO_CONFIG_KEYS,
                         set(FORM_FIELDS))


if __name__ == "__main__":
    unittest.main()
