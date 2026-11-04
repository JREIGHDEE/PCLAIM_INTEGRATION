"""The held-out learning database: "learning from one spread, evaluated on
unseen writers" (supplementary; never part of the main Chapter 5 results).

    Ocr_module\\venv\\Scripts\\python.exe -m research_tests.setup.build_heldout_db

pclaimassist_research_heldout = the starter rows (migrations 006-008) plus
the learned rows of the clinic database - all of which came from reviews and
exports of logbook pages 34-35 (the W10 spread) - except:
  - every row of the NAME column (patient names);
  - a whole value equal to a cell of W01-W09's answer key;
  - a name word that occurs in W01-W09's patient names;
  - rows learned only from reviews confirmed as a W01-W09 patient;
  - known entries that cannot be traced to a review (claims only).
The handwriting test then reads W01-W09 only (RESEARCH_DB_NAME=
pclaimassist_research_heldout, outputs/handwriting_heldout). The clinic
database is only read.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import pymysql

from research_tests import INPUTS
from research_tests.common.answer_key import handwriting
from research_tests.setup import seed

CLINIC_DB = "pclaimassist_db"
HELDOUT_DB = "pclaimassist_research_heldout"
EVAL_WRITERS = [f"W{i:02d}" for i in range(1, 10)]


def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _fold(s):
    return str(s or "").casefold()


def main():
    sys.path.append(str(INPUTS.parent.parent / "Ocr_module"))
    import paddle_assist  # the system's own learning functions, to trace each row

    held = defaultdict(dict)
    for k in handwriting(INPUTS / "answer_key.xlsx"):
        if k["writer"] in EVAL_WRITERS:
            held[(k["writer"], k["row"])][k["field"]] = k["truth"]
    held_values = {_norm(v) for e in held.values() for v in e.values() if _norm(v)}
    held_name_words = {w for e in held.values() for w in re.findall(r"[A-ZÑ]{3,}", str(e.get("Patient name", "")).upper())}

    def held_patient(values):
        name, case = _norm(values.get("NAME")), _norm(values.get("CASE #"))
        return any((case and case == _norm(e.get("Case number")))
                   or (name and SequenceMatcher(None, name, _norm(e.get("Patient name"))).ratio() >= 0.85)
                   for e in held.values())

    conn = pymysql.connect(host="127.0.0.1", user=os.environ.get("ADMIN_DB_USER", "root"),
                           password=os.environ.get("ADMIN_DB_PASSWORD", ""), charset="utf8mb4", autocommit=True,
                           cursorclass=pymysql.cursors.DictCursor)
    with conn.cursor() as c:
        c.execute(f"SELECT id, ocr_data FROM `{CLINIC_DB}`.case_sessions WHERE review_status = 'reviewed'")
        sessions = c.fetchall()
        c.execute(f"SELECT category, pattern_type, wrong_text, correct_text, times_seen, is_active "
                  f"FROM `{CLINIC_DB}`.ocr_correction_patterns WHERE source = 'learned'")
        patterns = c.fetchall()
        c.execute(f"SELECT category, entry_type, entry_key, entry_text, times_from_reviews, times_from_forms, is_active "
                  f"FROM `{CLINIC_DB}`.ocr_known_entries WHERE source = 'learned'")
        entries = c.fetchall()

    pat_src, ent_src, overlap = defaultdict(set), defaultdict(set), set()
    for s in sessions:
        fields = (json.loads(s["ocr_data"]) or {}).get("fields", [])
        if held_patient({f.get("category"): f.get("value") for f in fields}):
            overlap.add(s["id"])
        for cat, typ, w, r, _n in paddle_assist.reviewed_patterns(fields):
            pat_src[(cat, typ, _fold(w), _fold(r))].add(s["id"])
        for cat, typ, k, _t, _n in paddle_assist.reviewed_entries(fields):
            ent_src[(cat, typ, _fold(k))].add(s["id"])

    def reason(category, kind, text, sources):
        if category == "NAME":
            return "patient name"
        if kind == "value" and _norm(text) in held_values:
            return "value in W01-W09 key"
        if kind == "word" and str(text).upper() in held_name_words:
            return "name word in W01-W09 key"
        if not sources:
            return "untraceable"
        if sources <= overlap:
            return "only from a review of a W01-W09 patient"
        return "kept"

    kept_p = [p for p in patterns if reason(p["category"], p["pattern_type"], p["correct_text"], pat_src.get(
        (p["category"], p["pattern_type"], _fold(p["wrong_text"]), _fold(p["correct_text"])), set())) == "kept"]
    kept_e = [e for e in entries if reason(e["category"], e["entry_type"], e["entry_text"], ent_src.get(
        (e["category"], e["entry_type"], _fold(e["entry_key"])), set())) == "kept"]
    pc = Counter(reason(p["category"], p["pattern_type"], p["correct_text"], pat_src.get(
        (p["category"], p["pattern_type"], _fold(p["wrong_text"]), _fold(p["correct_text"])), set())) for p in patterns)
    ec = Counter(reason(e["category"], e["entry_type"], e["entry_text"], ent_src.get(
        (e["category"], e["entry_type"], _fold(e["entry_key"])), set())) for e in entries)

    with conn.cursor() as c:
        c.execute(f"DROP DATABASE IF EXISTS `{HELDOUT_DB}`")
        c.execute(f"CREATE DATABASE `{HELDOUT_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        c.execute(f"USE `{HELDOUT_DB}`")
        for stmt in seed.migration_statements():
            c.execute(stmt)
        for p in kept_p:
            c.execute("INSERT INTO ocr_correction_patterns (category, pattern_type, wrong_text, correct_text, times_seen, "
                      "source, is_active) VALUES (%s,%s,%s,%s,%s,'learned',%s)",
                      (p["category"], p["pattern_type"], p["wrong_text"], p["correct_text"], p["times_seen"], p["is_active"]))
        for e in kept_e:
            c.execute("INSERT INTO ocr_known_entries (category, entry_type, entry_key, entry_text, times_from_reviews, "
                      "times_from_forms, source, is_active) VALUES (%s,%s,%s,%s,%s,%s,'learned',%s)",
                      (e["category"], e["entry_type"], e["entry_key"], e["entry_text"], e["times_from_reviews"],
                       e["times_from_forms"], e["is_active"]))
        app = "pclaimassist_app"
        c.execute("SELECT host FROM mysql.user WHERE user = %s", (app,))
        for row in c.fetchall():
            c.execute(f"GRANT SELECT ON `{HELDOUT_DB}`.* TO %s@%s", (app, list(row.values())[0]))
    conn.close()
    print(f"{HELDOUT_DB}: starter rows + {len(kept_p)} learned patterns + {len(kept_e)} learned known entries")
    print("patterns:", dict(pc))
    print("entries:", dict(ec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
