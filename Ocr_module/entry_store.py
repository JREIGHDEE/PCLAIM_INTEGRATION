"""Common entries (ocr_known_entries table, migration 007).

The vocabulary behind paddle_assist.py's common-entry suggestions: what
staff actually enter per logbook column, and how often - counted from
logbook reviews and from exported forms. Same conventions as the other
stores: raw PyMySQL via db.get_db_cursor(), plain tuples, no ORM.
"""
from db import get_db_cursor

# entry_key / entry_text are VARCHAR(191).
_MAX_TEXT = 191
# A starter entry counts as if entered this many times.
STARTER_WEIGHT = 2

FROM_REVIEWS, FROM_FORMS = "reviews", "forms"


def load_entries():
    """Every active entry -> [(category, entry_type, entry_key, entry_text,
    times_from_reviews, total_weight)]."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT category, entry_type, entry_key, entry_text, times_from_reviews, "
            "times_from_forms, source FROM ocr_known_entries WHERE is_active = 1"
        )
        return [(r["category"], r["entry_type"], r["entry_key"], r["entry_text"], r["times_from_reviews"],
                 r["times_from_reviews"] + r["times_from_forms"]
                 + (STARTER_WEIGHT if r["source"] == "starter" else 0))
                for r in cursor.fetchall()]


def has_review_entries():
    """Whether any logbook review has been counted yet (form exports don't
    count: they may come first, before the one-time fill from past reviews)."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM ocr_known_entries WHERE times_from_reviews > 0 LIMIT 1")
        return cursor.fetchone() is not None


def add_entries(entries, origin):
    """Count entries: [(category, entry_type, entry_key, entry_text, count)],
    all from one origin (FROM_REVIEWS or FROM_FORMS)."""
    review = origin == FROM_REVIEWS
    rows = [(c, t, k, text, n if review else 0, 0 if review else n)
            for c, t, k, text, n in entries if len(k) <= _MAX_TEXT and len(text) <= _MAX_TEXT]
    if not rows:
        return
    with get_db_cursor(commit=True) as cursor:
        cursor.executemany(
            "INSERT INTO ocr_known_entries "
            "(category, entry_type, entry_key, entry_text, times_from_reviews, times_from_forms) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "times_from_reviews = times_from_reviews + VALUES(times_from_reviews), "
            "times_from_forms = times_from_forms + VALUES(times_from_forms), "
            "entry_text = VALUES(entry_text)",
            rows,
        )


def remove_review_entries(entries):
    """Take back review counts when staff change an answer they had
    confirmed: [(category, entry_type, entry_key, entry_text, count)].
    Counts never go below zero."""
    rows = [(n, c, t, k) for c, t, k, _text, n in entries]
    if not rows:
        return
    with get_db_cursor(commit=True) as cursor:
        cursor.executemany(
            "UPDATE ocr_known_entries "
            "SET times_from_reviews = GREATEST(CAST(times_from_reviews AS SIGNED) - %s, 0) "
            "WHERE category = %s AND entry_type = %s AND entry_key = %s",
            rows,
        )
