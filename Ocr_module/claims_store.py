"""PhilHealth claims persistence (patients / encounters / claims tables).

Follows the same conventions as case_session_store.py: raw PyMySQL via
db.get_db_cursor(), plain dicts in/out, no ORM. Column names written to the
database are always drawn from a fixed whitelist (never built from arbitrary
caller-supplied keys), and case_bridge.py output only ever uses those same
fixed column names.
"""
import config
from db import get_db_cursor
from errors import ClaimNotFoundError, InvalidRequestError
from philhealth import case_bridge

PATIENT_EDITABLE_COLUMNS = {
    "last_name", "first_name", "middle_name", "name_ext", "date_of_birth", "sex", "pin",
}
ENCOUNTER_EDITABLE_COLUMNS = {
    "date_admitted", "time_admitted", "am_pm_admitted",
    "date_discharge", "time_discharge", "am_pm_discharge",
    "disposition", "accommodation", "chief_complaint", "admission_dx", "discharge_dx",
}
CLAIMS_EDITABLE_COLUMNS = {
    "member_last_name", "member_first_name", "member_middle_name", "member_name_ext",
    "member_dob", "member_sex", "member_pin", "relationship",
    "hci_pan", "hci_name", "hci_street", "hci_city", "hci_province",
    "employer_pen", "employer_phone", "employer_name",
}


def _whitelist(fields, allowed, label):
    if not fields:
        return {}
    unknown = set(fields) - allowed
    if unknown:
        raise InvalidRequestError(f"Unknown/unsupported {label} field(s): {', '.join(sorted(unknown))}")
    return dict(fields)


def _insert_row(cursor, table, fields):
    columns = list(fields.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    cursor.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        [fields[c] for c in columns],
    )
    return cursor.lastrowid


def _update_row(cursor, table, row_id, fields):
    if not fields:
        return
    set_clause = ", ".join(f"{c} = %s" for c in fields)
    cursor.execute(
        f"UPDATE {table} SET {set_clause} WHERE id = %s",
        [*fields.values(), row_id],
    )


def _find_encounter_by_case_session(cursor, case_session_id):
    cursor.execute(
        "SELECT id, patient_id FROM encounters WHERE case_session_id = %s",
        (case_session_id,),
    )
    return cursor.fetchone()


def _insert_claim_with_hci_defaults(cursor, encounter_id):
    return _insert_row(cursor, "claims", {
        "encounter_id": encounter_id,
        "hci_pan": config.DEFAULT_HCI_PAN,
        "hci_name": config.DEFAULT_HCI_NAME,
        "hci_street": config.DEFAULT_HCI_STREET,
        "hci_city": config.DEFAULT_HCI_CITY,
        "hci_province": config.DEFAULT_HCI_PROVINCE,
    })


def create_or_update_claim_from_case_session(case_id):
    """Bridges a reviewed OCR case_sessions row into patients/encounters/claims.

    `case_id` is the same free-text logbook case number the OCR review UI
    already uses (case_sessions.logbook_case_number).

    First run for a given case session creates new patients/encounters/claims
    rows (linked via encounters.case_session_id, the schema's own unique FK
    for this bridge). Running it again for an already-linked case session
    re-applies the OCR bridge's output to the existing rows - a deliberate
    "re-sync after fixing the OCR review" action, not an automatic one.

    Returns {"claim_id": int, "warnings": [...]}.
    Raises InvalidRequestError if no such case session exists, or if the OCR
    data can't supply the minimum fields a brand-new patient/encounter needs
    (patients.last_name/first_name/date_of_birth, encounters.date_admitted -
    the only NOT NULL columns in either table).
    """
    from case_session_store import get_reviewed_session

    session = get_reviewed_session(case_id)
    if session is None:
        raise InvalidRequestError(f"No reviewed OCR case session found for case ID '{case_id}'.")

    patient_fields, encounter_fields, warnings = case_bridge.draft_patient_and_encounter(session["values"])

    with get_db_cursor(commit=True) as cursor:
        existing = _find_encounter_by_case_session(cursor, session["id"])

        if existing is None:
            missing = [f for f in ("last_name", "first_name", "date_of_birth") if f not in patient_fields]
            if "date_admitted" not in encounter_fields:
                missing.append("date_admitted")
            if missing:
                raise InvalidRequestError(
                    "Cannot generate a claim from this case session - the OCR review did not "
                    f"produce a usable value for: {', '.join(missing)}. Correct the case session "
                    "review and try again."
                )

            patient_id = _insert_row(cursor, "patients", patient_fields)
            encounter_id = _insert_row(cursor, "encounters", {
                "patient_id": patient_id,
                "case_session_id": session["id"],
                **encounter_fields,
            })
            claim_id = _insert_claim_with_hci_defaults(cursor, encounter_id)
        else:
            encounter_id = existing["id"]
            patient_id = existing["patient_id"]

            _update_row(cursor, "patients", patient_id, patient_fields)
            _update_row(cursor, "encounters", encounter_id, encounter_fields)

            cursor.execute("SELECT id FROM claims WHERE encounter_id = %s", (encounter_id,))
            claim_row = cursor.fetchone()
            claim_id = claim_row["id"] if claim_row else _insert_claim_with_hci_defaults(cursor, encounter_id)

    return {"claim_id": claim_id, "warnings": warnings}


def get_claim(claim_id):
    """Returns {"claim", "encounter", "patient"} dicts for one claim id, or None.

    Three separate queries rather than one JOIN with SELECT * - claims/
    encounters/patients share column names (id, created_at, ...), which a
    single "SELECT c.*, e.*, p.*" would silently collide/overwrite under a
    DictCursor.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claims_row = cursor.fetchone()
        if claims_row is None:
            return None

        cursor.execute("SELECT * FROM encounters WHERE id = %s", (claims_row["encounter_id"],))
        encounter_row = cursor.fetchone()

        patient_row = None
        if encounter_row:
            cursor.execute("SELECT * FROM patients WHERE id = %s", (encounter_row["patient_id"],))
            patient_row = cursor.fetchone()

    return {"claim": claims_row, "encounter": encounter_row, "patient": patient_row}


def update_claim_fields(claim_id, patient_fields=None, encounter_fields=None, claims_fields=None):
    """Applies manual corrections. Every field name is checked against a
    fixed whitelist before being used in any SQL - never built from
    arbitrary caller-supplied keys."""
    patient_fields = _whitelist(patient_fields, PATIENT_EDITABLE_COLUMNS, "patient")
    encounter_fields = _whitelist(encounter_fields, ENCOUNTER_EDITABLE_COLUMNS, "encounter")
    claims_fields = _whitelist(claims_fields, CLAIMS_EDITABLE_COLUMNS, "claim")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT encounter_id FROM claims WHERE id = %s", (claim_id,))
        row = cursor.fetchone()
        if row is None:
            raise ClaimNotFoundError(f"No claim found with id {claim_id}.")
        encounter_id = row["encounter_id"]

        _update_row(cursor, "claims", claim_id, claims_fields)
        _update_row(cursor, "encounters", encounter_id, encounter_fields)

        if patient_fields:
            cursor.execute("SELECT patient_id FROM encounters WHERE id = %s", (encounter_id,))
            patient_id = cursor.fetchone()["patient_id"]
            _update_row(cursor, "patients", patient_id, patient_fields)
