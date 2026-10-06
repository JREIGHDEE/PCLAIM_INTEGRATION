"""
Reviewed OCR "case session" persistence - MariaDB-backed (case_sessions
table in pclaimassist_db).

Replaces the previous JSON-file storage at
uploads/reviewed_results/sessions/<case_id>.json. Grid templates are a
separate, unrelated concept and are unaffected - see template_store.py.

Column mapping note: the review UI's free-text "Case ID" field has no
dedicated column of its own in the approved schema - it's stored in
`logbook_case_number`. That column intentionally has no UNIQUE constraint
(handwritten/OCR'd case numbers aren't reliable keys), so "saving again
with the same case_id updates the same record" (the previous file-based
behavior) is implemented here as an explicit lookup-then-upsert rather
than a database-level constraint.

Sessions created from a logbook upload (logbook_pipeline.py) are different:
one is INSERTed per patient row, never upserted by case number (an OCR'd
CASE # can be blank or misread, so two rows could collide), they carry
per-field OCR data in `ocr_data`, and they start as review_status='pending'
until the reviewer submits them (database/migrations/003).
"""
import json

from db import get_db_cursor


def _find_session_id(cursor, case_id):
    cursor.execute(
        "SELECT id FROM case_sessions WHERE logbook_case_number = %s "
        "ORDER BY id DESC LIMIT 1",
        (case_id,),
    )
    row = cursor.fetchone()
    return row["id"] if row else None


def save_reviewed_session(case_id, case_name, values):
    """Wholesale-replace the reviewed values for `case_id` (insert if new).

    Mirrors the previous file-based behavior exactly: `values` fully
    replaces whatever was previously stored, it is never merged. A blank
    `case_name` on this save does not erase a previously saved case_name
    (same as the old "case_name or session_data.get('case_name', '')"
    logic).

    Returns the case_sessions.id row that was written to.
    """
    values_json = json.dumps(values)

    with get_db_cursor(commit=True) as cursor:
        existing_id = _find_session_id(cursor, case_id)

        if existing_id is not None:
            cursor.execute(
                """
                UPDATE case_sessions
                SET case_name = COALESCE(NULLIF(%s, ''), case_name),
                    reviewed_values = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (case_name or "", values_json, existing_id),
            )
            return existing_id

        cursor.execute(
            """
            INSERT INTO case_sessions
                (logbook_case_number, case_name, reviewed_values, reviewed_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (case_id, case_name or None, values_json),
        )
        return cursor.lastrowid


def get_reviewed_session(case_id):
    """Latest session for `case_id` as a _row_to_session() dict, or None."""
    with get_db_cursor() as cursor:
        cursor.execute(
            f"SELECT {_SESSION_COLUMNS} "
            "FROM case_sessions WHERE logbook_case_number = %s "
            "ORDER BY id DESC LIMIT 1",
            (case_id,),
        )
        row = cursor.fetchone()

    return _row_to_session(row)


_SESSION_COLUMNS = (
    "id, logbook_case_number, case_name, reviewed_values, ocr_data, "
    "source_document, upload_id, logbook_row, review_status, reviewed_at"
)


def _parse_json_dict(raw):
    # PyMySQL always returns JSON columns as raw text (it does not decode
    # them), so this needs an explicit parse regardless of MySQL/MariaDB
    # version.
    try:
        value = json.loads(raw) if raw else {}
    except Exception:
        value = {}
    return value if isinstance(value, dict) else {}


def _row_to_session(row):
    """case_sessions row -> {"id", "case_id", "case_name", "values",
    "ocr_data", "source_document", "upload_id", "logbook_row",
    "review_status", "updated_at"}, or None."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "case_id": row["logbook_case_number"],
        "case_name": row["case_name"] or "",
        "values": _parse_json_dict(row["reviewed_values"]),
        "ocr_data": _parse_json_dict(row["ocr_data"]),
        "source_document": row["source_document"],
        "upload_id": row["upload_id"],
        "logbook_row": row["logbook_row"],
        "review_status": row["review_status"],
        "updated_at": row["reviewed_at"],
    }


def create_ocr_session(case_number, values, ocr_data, source_document, upload_id, logbook_row):
    """INSERT one pending session for one logbook row. Returns its id."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO case_sessions
                (logbook_case_number, reviewed_values, ocr_data, source_document,
                 upload_id, logbook_row, review_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            """,
            (case_number or None, json.dumps(values), json.dumps(ocr_data),
             source_document, upload_id, logbook_row),
        )
        return cursor.lastrowid


def get_session(session_id):
    with get_db_cursor() as cursor:
        cursor.execute(f"SELECT {_SESSION_COLUMNS} FROM case_sessions WHERE id = %s", (session_id,))
        return _row_to_session(cursor.fetchone())


def list_upload_sessions(upload_id):
    """Every session created from one upload, in logbook row order."""
    with get_db_cursor() as cursor:
        cursor.execute(
            f"SELECT {_SESSION_COLUMNS} FROM case_sessions WHERE upload_id = %s "
            "ORDER BY logbook_row, id",
            (upload_id,),
        )
        return [_row_to_session(row) for row in cursor.fetchall()]


def mark_session_reviewed(session_id, case_number, values, ocr_data):
    """Store the reviewer's submitted values and mark the session reviewed."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE case_sessions
            SET logbook_case_number = %s,
                reviewed_values = %s,
                ocr_data = %s,
                review_status = 'reviewed',
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (case_number or None, json.dumps(values), json.dumps(ocr_data), session_id),
        )
