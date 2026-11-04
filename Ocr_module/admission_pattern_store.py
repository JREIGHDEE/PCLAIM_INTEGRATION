"""Admission patterns (admission_patterns table, migration 012).

The table behind philhealth/admission_patterns.py: which admissions the
logbook writes, the clinic's wording for each, and the readings staff
confirmed. Same conventions as the other stores: raw PyMySQL via
db.get_db_cursor(), plain dicts, no ORM.

Until migration 012 is run the table is missing: load() then gives the
starting patterns (admission_patterns.DEFAULT_PATTERNS) so suggestions
still work, and changing them asks for the migration.
"""
import json
import logging

from db import get_db_cursor
from errors import DatabaseError, InvalidRequestError
from philhealth import admission_patterns

logger = logging.getLogger(__name__)

PACKAGES = ("", "NSDBF", "NCP", "ANV", "PPC01", "FP001", "IUD")
_MAX_NAME, _MAX_REASON, _MAX_CLUE, _MAX_CLUES = 80, 191, 60, 20
_COLUMNS = ("id, name, clues, reason, package, examples, is_active, sort_order, "
            "times_confirmed, times_corrected, updated_by, updated_at")
_NO_TABLE = ("Run database/migrations/012_admission_patterns.sql (phpMyAdmin, SQL tab, as root) "
             "to change the admission patterns.")


def _row(r):
    try:
        examples = json.loads(r["examples"]) if r["examples"] else []
    except (TypeError, ValueError):
        examples = []
    return {
        "id": r["id"], "name": r["name"], "reason": r["reason"], "package": r["package"] or "",
        "clues": [c.strip() for c in (r["clues"] or "").splitlines() if c.strip()],
        "examples": examples if isinstance(examples, list) else [],
        "is_active": bool(r["is_active"]), "sort_order": r["sort_order"],
        "times_confirmed": r["times_confirmed"], "times_corrected": r["times_corrected"],
        "updated_by": r["updated_by"],
        "updated_at": r["updated_at"].isoformat(sep=" ") if r["updated_at"] else None,
    }


def _defaults():
    return [{**p, "id": None, "examples": [], "is_active": True, "sort_order": i * 10,
             "times_confirmed": 0, "times_corrected": 0, "updated_by": None, "updated_at": None}
            for i, p in enumerate(admission_patterns.DEFAULT_PATTERNS, 1)]


def load():
    """(patterns, editable): every pattern, in the table's order; editable
    is False when the table is not there yet (the starting patterns)."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT {_COLUMNS} FROM admission_patterns ORDER BY sort_order, id")
            return [_row(r) for r in cursor.fetchall()], True
    except DatabaseError as exc:
        logger.warning("Admission patterns table not readable (%s) - using the starting patterns", exc)
        return _defaults(), False


def load_active():
    return [p for p in load()[0] if p["is_active"]]


def _get(cursor, pattern_id):
    cursor.execute(f"SELECT {_COLUMNS} FROM admission_patterns WHERE id = %s", (pattern_id,))
    row = cursor.fetchone()
    if not row:
        raise InvalidRequestError("That admission pattern no longer exists - reload the page.")
    return _row(row)


def clean(payload):
    """The editable parts of a pattern, checked: name, clues, reason,
    package, is_active. Raises InvalidRequestError for a bad one."""
    name = str(payload.get("name") or "").strip()
    reason = " ".join(str(payload.get("reason") or "").split()).upper()
    raw = payload.get("clues")
    clues = raw.splitlines() if isinstance(raw, str) else (raw or [])
    clues = [str(c).strip().upper() for c in clues if str(c).strip()]
    package = str(payload.get("package") or "").strip().upper()
    if not name or len(name) > _MAX_NAME:
        raise InvalidRequestError(f"Give the pattern a name (up to {_MAX_NAME} letters).")
    if not reason or len(reason) > _MAX_REASON:
        raise InvalidRequestError(f"Give the reason for admission it puts in (up to {_MAX_REASON} letters).")
    if not clues:
        raise InvalidRequestError("Give at least one clue: a word the logbook writes for this admission.")
    if len(clues) > _MAX_CLUES or any(len(c) > _MAX_CLUE for c in clues):
        raise InvalidRequestError(f"Up to {_MAX_CLUES} clues, each up to {_MAX_CLUE} letters.")
    if package not in PACKAGES:
        raise InvalidRequestError("Unknown package.")
    return {"name": name, "reason": reason, "clues": clues, "package": package,
            "is_active": bool(payload.get("is_active", True))}


def _write(sql, args):
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(sql, args)
            return cursor.lastrowid
    except DatabaseError as exc:
        if "1146" in str(exc) or "doesn't exist" in str(exc):
            raise InvalidRequestError(_NO_TABLE) from exc
        if "1062" in str(exc) or "Duplicate" in str(exc):
            raise InvalidRequestError("There is already a pattern with that name.") from exc
        raise


def create(payload, user):
    p = clean(payload)
    return _write(
        "INSERT INTO admission_patterns (name, clues, reason, package, is_active, sort_order, updated_by) "
        "SELECT %s, %s, %s, %s, %s, COALESCE(MAX(sort_order), 0) + 10, %s FROM admission_patterns",
        (p["name"], "\n".join(p["clues"]), p["reason"], p["package"], int(p["is_active"]), user))


def update(pattern_id, payload, user):
    p = clean(payload)
    _write("UPDATE admission_patterns SET name = %s, clues = %s, reason = %s, package = %s, is_active = %s, "
           "updated_by = %s WHERE id = %s",
           (p["name"], "\n".join(p["clues"]), p["reason"], p["package"], int(p["is_active"]), user, pattern_id))


def delete(pattern_id):
    _write("DELETE FROM admission_patterns WHERE id = %s", (pattern_id,))


def forget_example(pattern_id, reading, user):
    """Take one learned reading off a pattern (it was confirmed wrongly)."""
    with get_db_cursor(commit=True) as cursor:
        pattern = _get(cursor, pattern_id)
        cursor.execute("UPDATE admission_patterns SET examples = %s, updated_by = %s WHERE id = %s",
                       (json.dumps(admission_patterns.drop_example(pattern["examples"], reading)), user, pattern_id))


def learn(pattern_id, reading, user, suggested_id=None):
    """Staff said `reading` is pattern `pattern_id`: kept as its example
    (and taken off any other pattern), so the same misread is recognised
    next time. suggested_id: the pattern that was suggested, counted as
    confirmed when it is the same one, corrected when not."""
    if not admission_patterns.normalize(reading):
        raise InvalidRequestError("Nothing was read from the logbook to learn from.")
    try:
        with get_db_cursor(commit=True) as cursor:
            pattern = _get(cursor, pattern_id)
            cursor.execute(f"SELECT {_COLUMNS} FROM admission_patterns WHERE id <> %s", (pattern_id,))
            for other in map(_row, cursor.fetchall()):
                kept = admission_patterns.drop_example(other["examples"], reading)
                if len(kept) != len(other["examples"]):
                    cursor.execute("UPDATE admission_patterns SET examples = %s WHERE id = %s",
                                   (json.dumps(kept), other["id"]))
            cursor.execute(
                "UPDATE admission_patterns SET examples = %s, updated_by = %s, "
                "times_confirmed = times_confirmed + %s WHERE id = %s",
                (json.dumps(admission_patterns.add_example(pattern["examples"], reading)), user,
                 int(suggested_id == pattern_id), pattern_id))
            if suggested_id and suggested_id != pattern_id:
                cursor.execute("UPDATE admission_patterns SET times_corrected = times_corrected + 1 WHERE id = %s",
                               (suggested_id,))
    except DatabaseError as exc:
        if "1146" in str(exc) or "doesn't exist" in str(exc):
            raise InvalidRequestError(_NO_TABLE) from exc
        raise
