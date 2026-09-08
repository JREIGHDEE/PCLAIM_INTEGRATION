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
    """Return {"id", "case_id", "case_name", "values", "updated_at"} or None."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, logbook_case_number, case_name, reviewed_values, reviewed_at "
            "FROM case_sessions WHERE logbook_case_number = %s "
            "ORDER BY id DESC LIMIT 1",
            (case_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    # PyMySQL always returns JSON columns as raw text (it does not decode
    # them), so this needs an explicit parse regardless of MySQL/MariaDB
    # version.
    raw_values = row["reviewed_values"]
    try:
        values = json.loads(raw_values) if raw_values else {}
    except Exception:
        values = {}

    return {
        "id": row["id"],
        "case_id": row["logbook_case_number"],
        "case_name": row["case_name"] or "",
        "values": values if isinstance(values, dict) else {},
        "updated_at": row["reviewed_at"],
    }
