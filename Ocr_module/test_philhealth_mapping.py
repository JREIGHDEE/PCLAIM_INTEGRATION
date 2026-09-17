"""Tests for the PhilHealth mapping layer (philhealth/*).

Same flat-file unittest convention as test_template_matching.py.

field_catalog / mapping_service / case_bridge tests are pure (no DB, no
Flask) and always run. pdf_export tests use the real CF2/CSF templates
already checked into PClaimAssist/forms/ (no DB needed either). The
claims_store tests are the only ones that touch the live database - they
create their own case_sessions/patients/encounters/claims rows under a
distinctive test case id and delete everything they created in tearDown,
so they never leave residue in the real database. They require
database/migrations/001_relax_pmrf_cf3_not_null.sql to have been applied
(the app's configured DB user cannot run that ALTER itself - see the
implementation summary) and are skipped with a clear reason if the
database is unreachable or not yet migrated.
"""
import unittest
import uuid

from philhealth import case_bridge, mapping_service, pdf_export
from philhealth.field_catalog import format_date, format_time_12h, resolve_computed_value


class FieldCatalogTests(unittest.TestCase):
    def test_format_date_iso_to_mmddyyyy(self):
        self.assertEqual(format_date("2026-06-10"), "06-10-2026")

    def test_format_date_blank_and_unparseable(self):
        self.assertEqual(format_date(""), "")
        self.assertEqual(format_date(None), "")
        self.assertEqual(format_date("not-a-date"), "not-a-date")

    def test_format_time_12h(self):
        self.assertEqual(format_time_12h("08:30"), "08:30 AM")
        self.assertEqual(format_time_12h("00:05"), "12:05 AM")
        self.assertEqual(format_time_12h("13:00"), "01:00 PM")
        self.assertEqual(format_time_12h(""), "")

    def test_resolve_computed_patient_name_joins_present_parts(self):
        data = {"patientLastName": "Dela Cruz", "patientFirstName": "Maria", "patientNameExt": "", "patientMiddleName": "Santos"}
        self.assertEqual(resolve_computed_value("patientName", data), "Dela Cruz Maria Santos")

    def test_resolve_computed_patient_name_blank_when_all_parts_blank(self):
        self.assertEqual(resolve_computed_value("patientName", {}), "")


class MappingServiceTests(unittest.TestCase):
    def _complete_rows(self):
        patient = {
            "last_name": "Dela Cruz", "first_name": "Maria", "middle_name": "Santos",
            "name_ext": "", "date_of_birth": "1995-03-15", "sex": "Female", "pin": "12-345678901-3",
        }
        encounter = {
            "date_admitted": "2026-06-10", "time_admitted": "08:30", "am_pm_admitted": "AM",
            "date_discharge": "2026-06-13", "time_discharge": "10:00", "am_pm_discharge": "AM",
            "disposition": "Improved", "accommodation": "Non-Private",
            "admission_dx": "Term pregnancy in active labor", "discharge_dx": "NSD, live birth",
        }
        claims_row = {
            "hci_pan": "000001234", "hci_name": "Mapagpala Maternity Clinic",
            "hci_street": "456 Bonifacio Ave", "hci_city": "Quezon City", "hci_province": "Metro Manila",
            "member_pin": "12-345678901-2", "member_last_name": "Dela Cruz", "member_first_name": "Pedro",
            "member_middle_name": "Reyes", "member_name_ext": "", "member_dob": "1992-07-22",
            "relationship": "Spouse", "employer_pen": "", "employer_phone": "", "employer_name": "",
        }
        return patient, encounter, claims_row

    def test_complete_data_maps_cleanly_with_no_missing_fields(self):
        patient, encounter, claims_row = self._complete_rows()
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertTrue(result["forms"]["cf2"]["complete"])
        self.assertTrue(result["forms"]["csf"]["complete"])
        self.assertEqual(result["forms"]["cf2"]["missing_required"], [])
        self.assertEqual(result["forms"]["csf"]["missing_required"], [])

    def test_missing_required_patient_info_is_reported(self):
        patient, encounter, claims_row = self._complete_rows()
        # patientName resolves from last/first/ext/middle together (any one
        # present is enough), so all four must be blanked to make it
        # actually report missing - matches the ported getComputedValue
        # behavior exactly, not a simplification of it.
        patient["last_name"] = None
        patient["first_name"] = None
        patient["middle_name"] = None
        patient["name_ext"] = None
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertFalse(result["forms"]["cf2"]["complete"])
        self.assertIn("Patient Name", result["forms"]["cf2"]["missing_required"])

    def test_missing_philhealth_member_info_blocks_csf_only(self):
        patient, encounter, claims_row = self._complete_rows()
        claims_row["member_pin"] = None
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertTrue(result["forms"]["cf2"]["complete"])
        self.assertFalse(result["forms"]["csf"]["complete"])
        self.assertIn("Member PhilHealth PIN", result["forms"]["csf"]["missing_required"])

    def test_missing_diagnosis_blocks_cf2_only(self):
        patient, encounter, claims_row = self._complete_rows()
        encounter["admission_dx"] = None
        encounter["discharge_dx"] = ""
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertFalse(result["forms"]["cf2"]["complete"])
        self.assertIn("Admission Diagnosis", result["forms"]["cf2"]["missing_required"])
        self.assertIn("Discharge Diagnosis", result["forms"]["cf2"]["missing_required"])
        self.assertTrue(result["forms"]["csf"]["complete"])

    def test_invalid_date_is_a_validation_error_not_a_silent_pass(self):
        patient, encounter, claims_row = self._complete_rows()
        encounter["date_admitted"] = "not-a-real-date"
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertFalse(result["forms"]["cf2"]["complete"])
        self.assertTrue(any("not a valid date" in e for e in result["forms"]["cf2"]["validation_errors"]))

    def test_invalid_pin_format_is_a_validation_error(self):
        patient, encounter, claims_row = self._complete_rows()
        claims_row["member_pin"] = "not-a-pin"
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertFalse(result["forms"]["csf"]["complete"])
        self.assertTrue(any("format" in e for e in result["forms"]["csf"]["validation_errors"]))

    def test_optional_fields_omitted_does_not_block_export(self):
        patient, encounter, claims_row = self._complete_rows()
        claims_row["employer_pen"] = None
        claims_row["employer_phone"] = None
        claims_row["employer_name"] = None
        result = mapping_service.map_claim(patient, encounter, claims_row)
        self.assertTrue(result["forms"]["csf"]["complete"])

    def test_no_rows_at_all_reports_everything_missing_without_crashing(self):
        result = mapping_service.map_claim(None, None, None)
        self.assertFalse(result["forms"]["cf2"]["complete"])
        self.assertFalse(result["forms"]["csf"]["complete"])
        self.assertGreater(len(result["forms"]["cf2"]["missing_required"]), 0)

    def test_mapping_does_not_mutate_input_dicts(self):
        patient, encounter, claims_row = self._complete_rows()
        patient_copy = dict(patient)
        encounter_copy = dict(encounter)
        claims_copy = dict(claims_row)

        mapping_service.map_claim(patient, encounter, claims_row)

        self.assertEqual(patient, patient_copy)
        self.assertEqual(encounter, encounter_copy)
        self.assertEqual(claims_row, claims_copy)


class CaseBridgeTests(unittest.TestCase):
    def test_name_with_comma_splits_confidently_with_no_warning(self):
        patient_fields, _, warnings = case_bridge.draft_patient_and_encounter({"NAME": "Dela Cruz, Maria Santos"})
        self.assertEqual(patient_fields["last_name"], "Dela Cruz")
        self.assertEqual(patient_fields["first_name"], "Maria")
        self.assertEqual(patient_fields["middle_name"], "Santos")
        self.assertEqual(warnings, [])

    def test_name_without_comma_guesses_and_warns(self):
        patient_fields, _, warnings = case_bridge.draft_patient_and_encounter({"NAME": "Maria Santos Dela Cruz"})
        self.assertEqual(patient_fields["last_name"], "Dela Cruz")
        self.assertTrue(any("no comma" in w for w in warnings))

    def test_blank_name_produces_no_fields_and_a_warning(self):
        patient_fields, _, warnings = case_bridge.draft_patient_and_encounter({"NAME": ""})
        self.assertNotIn("last_name", patient_fields)
        self.assertTrue(warnings)

    def test_bday_parses_common_format(self):
        # NAME is intentionally omitted here (this test is only about BDAY) -
        # that alone produces its own "name was blank" warning, so this
        # checks for the absence of a birth-date warning specifically
        # rather than asserting an empty warnings list.
        patient_fields, _, warnings = case_bridge.draft_patient_and_encounter({"BDAY": "03/15/1995"})
        self.assertEqual(patient_fields["date_of_birth"], "1995-03-15")
        self.assertFalse(any("birth date" in w for w in warnings))

    def test_unparseable_bday_is_left_out_and_warned_not_guessed(self):
        patient_fields, _, warnings = case_bridge.draft_patient_and_encounter({"BDAY": "sometime in March"})
        self.assertNotIn("date_of_birth", patient_fields)
        self.assertTrue(any("Could not parse birth date" in w for w in warnings))

    def test_admission_datetime_splits_date_and_time(self):
        # NAME is intentionally omitted (see test_bday_parses_common_format).
        _, encounter_fields, warnings = case_bridge.draft_patient_and_encounter(
            {"DATE & TIME OF ADMISSION": "06/10/2026 8:30 AM"}
        )
        self.assertEqual(encounter_fields["date_admitted"], "2026-06-10")
        self.assertEqual(encounter_fields["time_admitted"], "08:30")
        self.assertEqual(encounter_fields["am_pm_admitted"], "AM")
        self.assertFalse(any("admission" in w.lower() for w in warnings))

    def test_diagnosis_fields_pass_through_as_is(self):
        _, encounter_fields, _ = case_bridge.draft_patient_and_encounter({
            "ADMITTING DIAGNOSIS": "Term pregnancy in active labor",
            "FINAL DIAGNOSIS": "NSD, live birth",
        })
        self.assertEqual(encounter_fields["admission_dx"], "Term pregnancy in active labor")
        self.assertEqual(encounter_fields["discharge_dx"], "NSD, live birth")

    def test_does_not_mutate_input_values_dict(self):
        values = {"NAME": "Dela Cruz, Maria", "BDAY": "03/15/1995"}
        values_copy = dict(values)
        case_bridge.draft_patient_and_encounter(values)
        self.assertEqual(values, values_copy)


class PdfExportTests(unittest.TestCase):
    """Uses the real CF2/CSF templates already in PClaimAssist/forms/ - no
    database needed, mirrors PClaimAssist's own client-side export inputs."""

    def _complete_rows(self):
        return MappingServiceTests._complete_rows(self)

    def test_export_cf2_produces_a_pdf(self):
        patient, encounter, claims_row = self._complete_rows()
        pdf_bytes = pdf_export.export_claim_pdf("cf2", patient, encounter, claims_row)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_export_csf_produces_a_pdf(self):
        patient, encounter, claims_row = self._complete_rows()
        pdf_bytes = pdf_export.export_claim_pdf("csf", patient, encounter, claims_row)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_export_unsupported_form_raises(self):
        with self.assertRaises(ValueError):
            pdf_export.export_claim_pdf("cf3", *self._complete_rows())


def _database_available():
    try:
        import db
        db.test_connection()
        return True
    except Exception:
        return False


def _claims_not_null_relaxed():
    """True once database/migrations/001_relax_pmrf_cf3_not_null.sql has
    been applied - the claims_store integration tests need it, but the
    app's own DB user cannot run that ALTER itself (see final summary)."""
    try:
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM claims WHERE Field = 'member_pin'")
            row = cursor.fetchone()
        return bool(row) and row["Null"] == "YES"
    except Exception:
        return False


@unittest.skipUnless(_database_available(), "MariaDB is not reachable in this environment")
@unittest.skipUnless(_claims_not_null_relaxed(), "Apply database/migrations/001_relax_pmrf_cf3_not_null.sql first")
class ClaimsStoreIntegrationTests(unittest.TestCase):
    """Touches the real database. Creates its own case_sessions/patients/
    encounters/claims rows under a unique test case id and deletes
    everything it created in tearDown, leaving the database unchanged."""

    def setUp(self):
        import case_session_store
        import claims_store
        self.case_session_store = case_session_store
        self.claims_store = claims_store
        self.case_id = f"TEST-PHILHEALTH-{uuid.uuid4().hex[:8]}"
        self._created_ids = None

    def tearDown(self):
        if not self._created_ids:
            return
        from db import get_db_cursor
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM claims WHERE id = %s", (self._created_ids["claim_id"],))
            cursor.execute("DELETE FROM encounters WHERE id = %s", (self._created_ids["encounter_id"],))
            cursor.execute("DELETE FROM patients WHERE id = %s", (self._created_ids["patient_id"],))
            cursor.execute("DELETE FROM case_sessions WHERE id = %s", (self._created_ids["case_session_id"],))

    def _record_created_ids(self, claim_id):
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute("SELECT encounter_id FROM claims WHERE id = %s", (claim_id,))
            encounter_id = cursor.fetchone()["encounter_id"]
            cursor.execute("SELECT patient_id, case_session_id FROM encounters WHERE id = %s", (encounter_id,))
            enc_row = cursor.fetchone()
        self._created_ids = {
            "claim_id": claim_id,
            "encounter_id": encounter_id,
            "patient_id": enc_row["patient_id"],
            "case_session_id": enc_row["case_session_id"],
        }

    def test_generate_from_case_session_then_fetch_mapped_view(self):
        self.case_session_store.save_reviewed_session(self.case_id, "Test Case", {
            "NAME": "Dela Cruz, Maria Santos",
            "BDAY": "03/15/1995",
            "DATE & TIME OF ADMISSION": "06/10/2026 8:30 AM",
            "DATE & TIME OF DISCHARGE": "06/13/2026 10:00 AM",
            "ADMITTING DIAGNOSIS": "Term pregnancy in active labor",
            "FINAL DIAGNOSIS": "NSD, live birth",
        })

        result = self.claims_store.create_or_update_claim_from_case_session(self.case_id)
        self._record_created_ids(result["claim_id"])

        rows = self.claims_store.get_claim(result["claim_id"])
        self.assertIsNotNone(rows)
        self.assertEqual(rows["patient"]["last_name"], "Dela Cruz")
        self.assertEqual(rows["encounter"]["date_admitted"].isoformat(), "2026-06-10")

        mapped = mapping_service.map_claim(rows["patient"], rows["encounter"], rows["claim"])
        # Disposition/accommodation/member info have no OCR source - expected missing.
        self.assertFalse(mapped["forms"]["cf2"]["complete"])
        self.assertIn("Patient Disposition", mapped["forms"]["cf2"]["missing_required"])

    def test_missing_ocr_data_blocks_generation_with_a_clear_error(self):
        self.case_session_store.save_reviewed_session(self.case_id, "Test Case", {"NAME": ""})
        with self.assertRaises(Exception) as ctx:
            self.claims_store.create_or_update_claim_from_case_session(self.case_id)
        self.assertIn("last_name", str(ctx.exception))

    def test_nonexistent_claim_id_returns_none_not_someone_elses_data(self):
        rows = self.claims_store.get_claim(2_147_483_647)
        self.assertIsNone(rows)


if __name__ == "__main__":
    unittest.main()
