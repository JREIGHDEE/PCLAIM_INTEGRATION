"""The normalized comparison reported beside Eq. 3.1's strict exact match
(Chapter 3 keeps the strict one as the primary figure).

What it does, and nothing else:
  1. compares in capitals;
  2. removes every space;
  3. in the date/time fields (Admitted, Birthday, Delivered, Went home),
     treats "-", "/" and "." as the same separator;
  4. in Case number, treats a hyphen like a space (so "2026 1018" and
     "2026-1018" are the same - the answer key writes both).
It does not add or drop leading zeros, change letters or digits, or touch
hyphens in any other field. The user-session error count (7c) uses the same
comparison so that formatting alone is never an error.
"""
import re

DATE_FIELDS = {"Admitted", "Birthday", "Delivered", "Went home"}


def normalized(field, text):
    value = str(text or "").upper()
    if field in DATE_FIELDS:
        value = re.sub(r"[-/.]", "-", value)
    if field == "Case number":
        value = value.replace("-", " ")
    return re.sub(r"\s+", "", value)


def normalized_equal(field, truth, reading):
    return normalized(field, truth) == normalized(field, reading)
