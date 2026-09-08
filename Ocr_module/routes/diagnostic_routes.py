"""
TEMPORARY diagnostic route for the Phase 1 database integration.

/diagnostic/patient_crud_test performs one INSERT followed by one SELECT
against the existing `patients` table, using a clearly-marked test record,
so the Flask <-> MariaDB write path can be verified (including a look in
phpMyAdmin) before any real OCR data is wired into `patients`.

This file and its blueprint registration in routes/__init__.py are meant to
be deleted once verification is done. It does not touch `patients` schema,
any other table, or any existing route.
"""
import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify

from db import get_db_cursor

logger = logging.getLogger(__name__)

diagnostic_bp = Blueprint("diagnostic", __name__)

# Recognizable in phpMyAdmin: filter/sort `patients` by last_name to find
# every row this test endpoint has ever created.
_TEST_LAST_NAME = "ZZ_DIAGNOSTIC_TEST"
_TEST_FIRST_NAME = "CRUD_TEST"


def _serialize_patient(row):
    if row is None:
        return None
    serialized = dict(row)
    for key in ("date_of_birth", "created_at", "updated_at"):
        value = serialized.get(key)
        if value is not None and hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
    return serialized


@diagnostic_bp.route("/diagnostic/patient_crud_test", methods=["POST"])
def patient_crud_test():
    """Insert one marked test patient row, then read it back by id.

    Safe to call repeatedly: each call inserts a new row (the `pin` carries
    a UTC timestamp so repeated calls are distinguishable in phpMyAdmin) and
    never reads or modifies any other row.
    """
    # pin is varchar(20): keep the prefix+timestamp within that limit so it
    # isn't silently truncated by MySQL/MariaDB.
    stamp = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    test_pin = f"DTEST-{stamp}"

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO patients
                (last_name, first_name, middle_name, name_ext, date_of_birth, sex, pin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (_TEST_LAST_NAME, _TEST_FIRST_NAME, None, None, "2000-01-01", "Male", test_pin),
        )
        new_id = cursor.lastrowid

    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM patients WHERE id = %s", (new_id,))
        row = cursor.fetchone()

    logger.info("Diagnostic patient_crud_test inserted patients.id=%s (pin=%s)", new_id, test_pin)

    return jsonify({
        "success": True,
        "message": (
            "Inserted and retrieved one test patient row. Verify it in phpMyAdmin: "
            "pclaimassist_db -> patients table -> look for this id, or filter "
            f"last_name = '{_TEST_LAST_NAME}'."
        ),
        "inserted_id": new_id,
        "patient": _serialize_patient(row),
    })
