"""OCR correction patterns (ocr_correction_patterns table, migration 006).

The memory behind paddle_assist.py's pattern recognition: how often each
PaddleOCR reading ended up as each staff-confirmed value, per logbook
column. Same conventions as the other stores: raw PyMySQL via
db.get_db_cursor(), plain tuples/dicts, no ORM.
"""
from db import get_db_cursor

# wrong_text / correct_text columns are VARCHAR(191).
_MAX_TEXT = 191


def load_patterns():
    """Every active pattern -> [(category, pattern_type, wrong_text, correct_text, times_seen)]."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT category, pattern_type, wrong_text, correct_text, times_seen "
            "FROM ocr_correction_patterns WHERE is_active = 1"
        )
        return [(r["category"], r["pattern_type"], r["wrong_text"], r["correct_text"], r["times_seen"])
                for r in cursor.fetchall() if r["times_seen"] > 0]


def has_learned_patterns():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM ocr_correction_patterns WHERE source = 'learned' LIMIT 1")
        return cursor.fetchone() is not None


def add_patterns(patterns):
    """Count observations: [(category, pattern_type, wrong_text, correct_text, count)].
    New patterns are inserted as 'learned'; known ones (including starter
    patterns) have their count raised."""
    rows = [(c, t, w, r, n) for c, t, w, r, n in patterns
            if len(w) <= _MAX_TEXT and len(r) <= _MAX_TEXT]
    if not rows:
        return
    with get_db_cursor(commit=True) as cursor:
        cursor.executemany(
            "INSERT INTO ocr_correction_patterns "
            "(category, pattern_type, wrong_text, correct_text, times_seen, source) "
            "VALUES (%s, %s, %s, %s, %s, 'learned') "
            "ON DUPLICATE KEY UPDATE times_seen = times_seen + VALUES(times_seen)",
            rows,
        )


def remove_patterns(patterns):
    """Take back observations when staff change an answer they had
    confirmed: [(category, pattern_type, wrong_text, correct_text, count)].
    Counts never go below zero."""
    rows = [(n, c, t, w, r) for c, t, w, r, n in patterns]
    if not rows:
        return
    with get_db_cursor(commit=True) as cursor:
        cursor.executemany(
            "UPDATE ocr_correction_patterns "
            "SET times_seen = GREATEST(CAST(times_seen AS SIGNED) - %s, 0) "
            "WHERE category = %s AND pattern_type = %s AND wrong_text = %s AND correct_text = %s",
            rows,
        )
