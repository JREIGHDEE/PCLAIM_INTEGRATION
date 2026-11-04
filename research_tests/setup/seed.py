"""The research database's seed and its content checksums.

The seed is the system's starter rows exactly as the migrations create them
(database/migrations/006, 007, 008): 121 correction patterns and 99 known
entries, no learned rows. The checksums cover the rows' contents only (no
ids or timestamps), so they are the same on every computer.
"""
import hashlib
import json
from pathlib import Path

from research_tests import REPO

MIGRATIONS = ["006_ocr_correction_patterns.sql", "007_ocr_known_entries.sql", "008_address_cabantian.sql"]
CHECKSUMS = Path(__file__).with_name("seed_checksums.json")
QUERIES = {
    "ocr_correction_patterns": "SELECT category, pattern_type, wrong_text, correct_text, times_seen, source, "
                               "is_active FROM ocr_correction_patterns",
    "ocr_known_entries": "SELECT category, entry_type, entry_key, entry_text, times_from_reviews, times_from_forms, "
                         "source, is_active FROM ocr_known_entries",
}


def statements(sql):
    """The SQL statements of a migration file (comments dropped)."""
    lines = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    out, current = [], []
    for line in lines:
        current.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";").strip()
            if stmt:
                out.append(stmt)
            current = []
    return out


def migration_statements():
    return [s for name in MIGRATIONS
            for s in statements((REPO / "database" / "migrations" / name).read_text(encoding="utf-8"))]


def table_checksums(cursor):
    """{table: {"rows": n, "sha256": ...}} of the rows' contents."""
    out = {}
    for table, query in QUERIES.items():
        cursor.execute(query)
        rows = sorted(json.dumps([str(v) for v in (r.values() if isinstance(r, dict) else r)], ensure_ascii=False)
                      for r in cursor.fetchall())
        out[table] = {"rows": len(rows), "sha256": hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()}
    return out


def recorded():
    return json.loads(CHECKSUMS.read_text(encoding="utf-8")) if CHECKSUMS.is_file() else None
