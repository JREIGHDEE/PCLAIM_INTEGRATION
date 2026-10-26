"""PhilHealth claims persistence (patients / encounters / claims tables).

Follows the same conventions as case_session_store.py: raw PyMySQL via
db.get_db_cursor(), plain dicts in/out, no ORM. Column names written to the
database are always drawn from a fixed whitelist (never built from arbitrary
caller-supplied keys), and case_bridge.py output only ever uses those same
fixed column names.
"""
import json
import re

import config
from db import get_db_cursor
from errors import ClaimNotFoundError, InvalidRequestError, ReviewIncompleteError, SessionNotFoundError
from philhealth import address_parser, case_bridge, field_catalog, form_prefill, mother_baby

# claims.status's three values, in forward order - used to make status
# transitions monotonic (see _advance_status).
_STATUS_ORDER = ("draft", "ready", "exported")

PATIENT_EDITABLE_COLUMNS = {
    "last_name", "first_name", "middle_name", "name_ext", "date_of_birth", "sex", "pin",
    "address",
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
    "delivery_date", "delivery_time", "am_pm_delivery",
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


def _insert_claim_with_hci_defaults(cursor, encounter_id, claims_fields=None):
    return _insert_row(cursor, "claims", {
        "encounter_id": encounter_id,
        "hci_pan": config.DEFAULT_HCI_PAN,
        "hci_name": config.DEFAULT_HCI_NAME,
        "hci_street": config.DEFAULT_HCI_STREET,
        "hci_city": config.DEFAULT_HCI_CITY,
        "hci_province": config.DEFAULT_HCI_PROVINCE,
        **(claims_fields or {}),
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
    return _create_or_update_claim_from_session(session)


def create_or_update_claim_from_session_id(session_id):
    """Same as create_or_update_claim_from_case_session(), addressed by
    case_sessions.id - the only reliable key for sessions created per
    logbook row by an upload, whose OCR'd CASE # may be blank or repeated."""
    from case_session_store import get_session

    session = get_session(session_id)
    if session is None:
        raise SessionNotFoundError(f"No case session found with id {session_id}.")
    return _create_or_update_claim_from_session(session)


def _session_address(session):
    """The ADDRESS a session's review ended with: typed in parts, or text."""
    for field in (session.get("ocr_data") or {}).get("fields") or []:
        if field.get("category") == case_bridge.ADDRESS and field.get("parts_reviewed"):
            return ((field.get("parts") or {}).get("text") or "").strip()
    return str((session.get("values") or {}).get(case_bridge.ADDRESS) or "").strip()


def _previous_address(session):
    """For an address written as a ditto mark ("-DO-"): the address of the
    nearest patient above it in the same logbook upload that has one."""
    if not session.get("upload_id"):
        return None
    if not address_parser.is_ditto(_session_address(session)):
        return None
    from case_session_store import list_upload_sessions

    # Sessions are created in logbook order, so a lower id is a row above
    # (logbook_row restarts on each two-page spread of a longer upload).
    above = sorted((s for s in list_upload_sessions(session["upload_id"]) if s["id"] < session["id"]),
                   key=lambda s: s["id"])
    for other in reversed(above):
        address = _session_address(other)
        if address and not address_parser.is_ditto(address):
            return address
    return None


def _create_or_update_claim_from_session(session):
    if session["review_status"] == "pending":
        raise ReviewIncompleteError(
            "This case session still has unreviewed OCR fields - submit its review "
            "before generating a claim."
        )

    reviewed_parts = {
        f["category"]: f["parts"]
        for f in ((session.get("ocr_data") or {}).get("fields") or [])
        if f.get("parts_reviewed") and f.get("parts")
    }
    patient_fields, encounter_fields, claims_fields, warnings = case_bridge.draft_patient_and_encounter(
        session["values"], reviewed_parts, previous_address=_previous_address(session))

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
            claim_id = _insert_claim_with_hci_defaults(cursor, encounter_id, claims_fields)
        else:
            encounter_id = existing["id"]
            patient_id = existing["patient_id"]

            _update_row(cursor, "patients", patient_id, patient_fields)
            _update_row(cursor, "encounters", encounter_id, encounter_fields)

            # SELECT *: works on a database without update 010 too.
            cursor.execute("SELECT * FROM claims WHERE encounter_id = %s", (encounter_id,))
            claim_row = cursor.fetchone()
            if claim_row:
                claim_id = claim_row["id"]
                _update_row(cursor, "claims", claim_id, claims_fields)
                # The corrected logbook review wins over what the forms
                # saved for the same boxes.
                if claim_row.get("form_values"):
                    _drop_saved_logbook_values(cursor, claim_id, claim_row["form_values"])
            else:
                claim_id = _insert_claim_with_hci_defaults(cursor, encounter_id, claims_fields)

    advance_status_if_forms_complete(claim_id)
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


def get_claim_form_source(claim_id):
    """Everything philhealth/form_prefill.build_form_data() needs for one
    claim: its rows and the OCR case session it was generated from
    (None for a manual claim). Returns None if the claim doesn't exist."""
    from case_session_store import get_session

    rows = get_claim(claim_id)
    if rows is None:
        return None
    session_id = (rows["encounter"] or {}).get("case_session_id")
    return {
        "rows": rows,
        "session": get_session(session_id) if session_id else None,
    }


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

    advance_status_if_forms_complete(claim_id)


def _advance_status(claim_id, new_status):
    """Moves claims.status forward along _STATUS_ORDER only - never
    regresses an already-'ready'/'exported' claim back to an earlier status,
    even if whatever triggered this call would otherwise point that way (a
    later edit making a required field blank again does not un-export a
    claim that was already exported; re-export is always available
    regardless of the stored status label, since export itself re-validates
    required fields every time - see routes/claims_routes.py export_claim()).
    No-op if the claim doesn't exist or is already at/past `new_status`.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT status FROM claims WHERE id = %s", (claim_id,))
        row = cursor.fetchone()
        if row is None or _STATUS_ORDER.index(new_status) <= _STATUS_ORDER.index(row["status"]):
            return
        cursor.execute("UPDATE claims SET status = %s WHERE id = %s", (new_status, claim_id))


def advance_status_if_forms_complete(claim_id):
    """Moves a 'draft' claim to 'ready' once its CF2 and CSF forms (the only
    two forms this backend currently maps/exports - see
    philhealth/overlays/__init__.py) are both complete per
    mapping_service.map_claim(). Called after every write that could change
    completeness (claim generation/sync, manual field correction). No-op if
    the forms aren't complete yet, or the claim is already 'ready'/'exported'.
    """
    from philhealth import mapping_service

    rows = get_claim(claim_id)
    if rows is None:
        return
    mapped = mapping_service.map_claim(rows["patient"], rows["encounter"], rows["claim"])
    if mapped["forms"]["cf2"]["complete"] and mapped["forms"]["csf"]["complete"]:
        _advance_status(claim_id, "ready")


def mark_exported(claim_id):
    """Moves a claim to 'exported' - called once a PDF export has actually
    succeeded (see routes/claims_routes.py export_claim()). Idempotent;
    never regresses an already-'exported' claim."""
    _advance_status(claim_id, "exported")


# ---------------------------------------------------------------------------
# What staff type on the forms, kept with the claim (claims.form_values)
# ---------------------------------------------------------------------------
_FORM_VALUES_MAX_BYTES = 256 * 1024
# What a baby's claim copied from its mother's (js/mother-baby.js), kept
# so unticking can undo it on a reopened claim: {"motherClaimId": int,
# "values": {form key: value}}.
_MOTHER_COPY_KEY = "_copiedFromMother"
# Boxes the logbook fills: a re-sync from a corrected review replaces them.
_LOGBOOK_KEYS = field_catalog.AUTO_OCR_KEYS | {
    key for keys in field_catalog.DERIVED_OCR_KEYS.values() for key in keys}


_MIGRATION_010 = "database/migrations/010_claim_mother_baby.sql"
_has_migration_010 = False


def _require_migration_010():
    """Saving the forms and mother/baby need update 010's columns. A
    database without them gets a message saying what to run, not a bare
    "Unknown column" error (once found, not checked again)."""
    global _has_migration_010
    if _has_migration_010:
        return
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS n FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'claims' AND COLUMN_NAME IN ('patient_role', 'mother_claim_id', 'form_values')")
        found = cursor.fetchone()["n"]
    if found < 3:
        raise InvalidRequestError(
            f"The database needs an update before patients can be saved: run {_MIGRATION_010} "
            "in phpMyAdmin (SQL tab, as root), then try again. See SETUP.md.")
    _has_migration_010 = True


def _parse_form_values(raw):
    try:
        value = json.loads(raw) if raw else {}
    except ValueError:
        value = {}
    return value if isinstance(value, dict) else {}


def _drop_saved_logbook_values(cursor, claim_id, raw):
    saved = _parse_form_values(raw)
    kept = {k: v for k, v in saved.items() if k not in _LOGBOOK_KEYS}
    if kept != saved:
        cursor.execute("UPDATE claims SET form_values = %s WHERE id = %s",
                       (json.dumps(kept), claim_id))


def _clean_form_values(values):
    clean = {}
    for key, value in values.items():
        if key == _MOTHER_COPY_KEY:
            continue
        if not isinstance(key, str) or not key.isidentifier():
            raise InvalidRequestError(f"Not a form key: {key!r}")
        if isinstance(value, list):
            value = [str(v) for v in value]
        elif value is not None and not isinstance(value, (str, bool, int, float)):
            raise InvalidRequestError(f"Unsupported value for {key}")
        clean[key] = value
    return clean


def save_form_values(claim_id, values):
    """Replaces what is kept as typed on the forms for this claim.
    values: {form key: str | bool | number | list of str}."""
    _require_migration_010()
    if not isinstance(values, dict):
        raise InvalidRequestError("'values' must be an object of form key -> value")
    clean = _clean_form_values(values)
    copied = values.get(_MOTHER_COPY_KEY)
    if copied is not None:
        if not (isinstance(copied, dict) and isinstance(copied.get("motherClaimId"), int)
                and isinstance(copied.get("values"), dict)):
            raise InvalidRequestError(f"Unsupported value for {_MOTHER_COPY_KEY}")
        clean[_MOTHER_COPY_KEY] = {"motherClaimId": copied["motherClaimId"],
                                   "values": _clean_form_values(copied["values"])}
    raw = json.dumps(clean)
    if len(raw.encode("utf-8")) > _FORM_VALUES_MAX_BYTES:
        raise InvalidRequestError("Too much form data to save")
    if get_claim(claim_id) is None:
        raise ClaimNotFoundError(f"No claim found with id {claim_id}.")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE claims SET form_values = %s WHERE id = %s", (raw, claim_id))


# ---------------------------------------------------------------------------
# "Save patient" (Check for Missing Information)
# ---------------------------------------------------------------------------
# Form keys copied into the claim's own columns on save, so the claim is
# found and recognised (mother / baby) without opening its forms: the
# whitelisted columns above, as field_catalog.FORM_FIELDS maps them.
_SAVE_TABLE_COLUMNS = {
    "patients": PATIENT_EDITABLE_COLUMNS - {"address"},
    "encounters": ENCOUNTER_EDITABLE_COLUMNS,
    "claims": CLAIMS_EDITABLE_COLUMNS,
}
_SAVE_KEYS = {
    key: field for key, field in field_catalog.FORM_FIELDS.items()
    if field.column in _SAVE_TABLE_COLUMNS.get(field.table, ())
}
_REQUIRED_TO_CREATE = {
    "patientLastName": "the patient's last name",
    "patientFirstName": "the patient's first name",
    "patientDOB": "the patient's date of birth",
    "dateAdmitted": "the date admitted",
}
_column_info = None


def _columns():
    """{(table, column): {"max": int | None, "choices": tuple | None,
    "required": bool}} for the columns a save writes, read once from the
    database itself so a value never breaks a column's size or ENUM."""
    global _column_info
    if _column_info is None:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH, COLUMN_TYPE, IS_NULLABLE "
                "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME IN ('patients', 'encounters', 'claims')")
            info = {}
            for row in cursor.fetchall():
                kind = row["COLUMN_TYPE"]
                choices = tuple(re.findall(r"'((?:[^']|'')*)'", kind)) if kind.startswith("enum(") else None
                info[(row["TABLE_NAME"], row["COLUMN_NAME"])] = {
                    "max": row["CHARACTER_MAXIMUM_LENGTH"], "choices": choices,
                    "required": row["IS_NULLABLE"] == "NO",
                }
        _column_info = info
    return _column_info


def _column_value(field, value):
    """A form value as its column takes it, or None (empty, or not a value
    the column can hold - the form value itself is kept in form_values)."""
    if value in (None, "", [], False):
        return None
    text = str(value).strip()
    if field.kind == "date":
        return text if field_catalog.is_valid_date_string(text) and len(text) == 10 else None
    if field.kind == "time":
        return text if re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", text) else None
    info = _columns().get((field.table, field.column), {})
    if info.get("choices"):
        match = next((c for c in info["choices"] if c.lower() == text.lower()), None)
        return match
    if info.get("max") and len(text) > info["max"]:
        return None
    return text


def _columns_from_form(values):
    tables = {"patients": {}, "encounters": {}, "claims": {}}
    for key, field in _SAVE_KEYS.items():
        if key not in values:
            continue
        value = _column_value(field, values[key])
        required = _columns().get((field.table, field.column), {}).get("required")
        if value is None and required:
            continue  # a NOT NULL column keeps what it has
        tables[field.table][field.column] = value
    return tables


def save_patient(claim_id, values):
    """The "Save patient" button: keeps everything typed on the forms, and
    copies the core of it into the claim's columns. With no claim_id (a
    patient typed in by hand, not from the logbook), creates the patient,
    encounter and claim first. Returns the claim id."""
    _require_migration_010()
    if not isinstance(values, dict):
        raise InvalidRequestError("'values' must be an object of form key -> value")
    tables = _columns_from_form(values)
    if claim_id is None:
        missing = [label for key, label in _REQUIRED_TO_CREATE.items()
                   if tables[_SAVE_KEYS[key].table].get(_SAVE_KEYS[key].column) is None]
        if missing:
            raise InvalidRequestError("To save this patient, first fill in " + ", ".join(missing) + ".")
        with get_db_cursor(commit=True) as cursor:
            patient_id = _insert_row(cursor, "patients", tables["patients"])
            encounter_id = _insert_row(cursor, "encounters", {"patient_id": patient_id, **tables["encounters"]})
            claim_id = _insert_claim_with_hci_defaults(cursor, encounter_id, tables["claims"])
    else:
        update_claim_fields(claim_id, tables["patients"], tables["encounters"], tables["claims"])
    save_form_values(claim_id, values)
    advance_status_if_forms_complete(claim_id)
    return claim_id


def saved_form_values(claims_row):
    """What was typed on the forms, from a claims row ({} if nothing yet)."""
    return _parse_form_values((claims_row or {}).get("form_values"))


def claim_form_values(claim_id):
    """The claim as the forms show it: what the logbook gave
    (form_prefill), overlaid with what staff typed and saved."""
    source = get_claim_form_source(claim_id)
    if source is None:
        raise ClaimNotFoundError(f"No claim found with id {claim_id}.")
    values = form_prefill.build_form_data(source["rows"], source["session"])["data"]
    values.update(saved_form_values(source["rows"]["claim"]))
    values.pop(_MOTHER_COPY_KEY, None)
    return values


# ---------------------------------------------------------------------------
# Mother and baby (philhealth/mother_baby.py)
# ---------------------------------------------------------------------------
# How many recent claims are looked through for a baby's mother.
_FAMILY_LOOKBACK = 300


def _family_rows(cursor, claim_id=None):
    where, params = ("WHERE c.id = %s", (claim_id,)) if claim_id else ("", ())
    cursor.execute(
        "SELECT c.id AS claim_id, c.patient_role, c.mother_claim_id, c.delivery_date, "
        "p.last_name, p.first_name, p.middle_name, p.date_of_birth AS dob, "
        "e.date_admitted, e.admission_dx, e.discharge_dx, "
        "s.id AS session_id, s.upload_id "
        "FROM claims c JOIN encounters e ON e.id = c.encounter_id "
        "JOIN patients p ON p.id = e.patient_id "
        f"LEFT JOIN case_sessions s ON s.id = e.case_session_id {where} "
        "ORDER BY c.id DESC LIMIT %s",
        (*params, _FAMILY_LOOKBACK),
    )
    return cursor.fetchall()


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _family_entry(row):
    """A _family_rows row with its role worked out: staff's choice, else
    what the logbook entry says."""
    given = " ".join(p for p in (row["first_name"], row["middle_name"]) if p)
    detected = mother_baby.classify_entry({
        "name": " ".join(p for p in (given, row["last_name"]) if p),
        "dob": row["dob"], "date_admitted": row["date_admitted"],
        "delivery_date": row["delivery_date"],
        "admission_dx": row["admission_dx"], "discharge_dx": row["discharge_dx"],
    })
    return {
        "claim_id": row["claim_id"],
        "name": ", ".join(p for p in (row["last_name"], given) if p),
        "last_name": row["last_name"],
        "dob": _iso(row["dob"]),
        "date_admitted": _iso(row["date_admitted"]),
        "delivery_date": _iso(row["delivery_date"]),
        "upload_id": row["upload_id"],
        "session_id": row["session_id"],
        "mother_claim_id": row["mother_claim_id"],
        "role": row["patient_role"] or detected["role"],
        "role_chosen": row["patient_role"],
        "detected_role": detected["role"],
        "detected_reason": detected["reason"],
    }


def _public(entry, **extra):
    return {k: entry[k] for k in ("claim_id", "name", "dob", "date_admitted", "delivery_date")} | extra


def get_family(claim_id):
    """Who this claim's patient is (mother / baby), and the claims it is
    linked with: for a baby, its mother's (chosen or best match) and the
    others to choose from; for a mother, the babies copying from her."""
    _require_migration_010()
    with get_db_cursor() as cursor:
        own = _family_rows(cursor, claim_id)
        if not own:
            raise ClaimNotFoundError(f"No claim found with id {claim_id}.")
        others = [_family_entry(r) for r in _family_rows(cursor)]
    me = _family_entry(own[0])
    by_id = {e["claim_id"]: e for e in others}

    mothers = [e for e in others if e["role"] == mother_baby.MOTHER and e["claim_id"] != claim_id]
    ranked = mother_baby.rank_mothers(me, mothers) if me["role"] == mother_baby.BABY else []
    reasons = {m["claim_id"]: m["reasons"] for m in ranked}
    # Then every other mother, those who have delivered first (newest first,
    # as _family_rows lists them).
    rest = sorted((m for m in mothers if m["claim_id"] not in reasons), key=lambda m: not m["delivery_date"])
    order = [m["claim_id"] for m in ranked] + [m["claim_id"] for m in rest]
    linked = me["mother_claim_id"]
    if linked and linked not in order and linked in by_id:
        order.insert(0, linked)

    return {
        "claim_id": claim_id,
        "role": me["role"],
        "role_chosen": me["role_chosen"],
        "detected_role": me["detected_role"],
        "detected_reason": me["detected_reason"],
        "mother_claim_id": linked,
        "suggested_mother_id": ranked[0]["claim_id"] if ranked else None,
        "mothers": [_public(by_id[i], reasons=reasons.get(i, [])) for i in order if i in by_id],
        "babies": [_public(e) for e in others if e["mother_claim_id"] == claim_id],
    }


def set_family(claim_id, role=None, mother_claim_id=None, *, set_role=False, set_mother=False):
    """Staff's choice of who the patient is, and of the mother's claim a
    baby's claim copies from (None to unlink)."""
    _require_migration_010()
    fields = {}
    if set_role:
        if role not in (None, *mother_baby.ROLES):
            raise InvalidRequestError(f"'role' must be one of: {', '.join(mother_baby.ROLES)}")
        fields["patient_role"] = role
    if set_mother:
        if mother_claim_id is not None:
            if not isinstance(mother_claim_id, int) or mother_claim_id == claim_id:
                raise InvalidRequestError("'mother_claim_id' must be another claim's id")
            if get_claim(mother_claim_id) is None:
                raise ClaimNotFoundError(f"No claim found with id {mother_claim_id}.")
        fields["mother_claim_id"] = mother_claim_id
    if get_claim(claim_id) is None:
        raise ClaimNotFoundError(f"No claim found with id {claim_id}.")
    with get_db_cursor(commit=True) as cursor:
        _update_row(cursor, "claims", claim_id, fields)
    return get_family(claim_id)


def values_from_mother(claim_id):
    """What this (baby's) claim copies from its linked mother's claim:
    philhealth/mother_baby.values_for_baby() of her claim as the forms
    show it."""
    _require_migration_010()
    rows = get_claim(claim_id)
    if rows is None:
        raise ClaimNotFoundError(f"No claim found with id {claim_id}.")
    mother_id = rows["claim"].get("mother_claim_id")
    if not mother_id:
        raise InvalidRequestError("This claim is not linked to a mother's claim yet.")
    return {"mother_claim_id": mother_id, **mother_baby.values_for_baby(claim_form_values(mother_id))}
