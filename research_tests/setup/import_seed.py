"""Create the research database and load its seed.

    Ocr_module\\venv\\Scripts\\python.exe -m research_tests.setup.import_seed [--user root] [--password ""]
    ... --record     (the project lead only: write seed_checksums.json from this machine)

As the MariaDB administrator (XAMPP: root, no password): creates
pclaimassist_research, applies migrations 006, 007 and 008 to it (the
starter rows only), grants the app account in Ocr_module/.env (DB_USER)
SELECT on it, and checks the rows against seed_checksums.json. Safe to run
twice. The clinic database (pclaimassist_db) is never touched.
"""
import argparse
import os
import sys

import pymysql

from research_tests import OCR_DIR
from research_tests.setup import seed

DB = os.environ.get("RESEARCH_DB_NAME", "pclaimassist_research")


def app_user():
    """DB_USER from Ocr_module/.env (or the environment), default root."""
    user = os.environ.get("DB_USER")
    env = OCR_DIR / ".env"
    if not user and env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("DB_USER="):
                user = line.split("=", 1)[1].strip()
    return user or "root"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m research_tests.setup.import_seed", description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root", help="MariaDB administrator (default root)")
    parser.add_argument("--password", default="", help="its password (XAMPP default: none)")
    parser.add_argument("--record", action="store_true", help="write seed_checksums.json from this database")
    args = parser.parse_args(argv)

    conn = pymysql.connect(host=args.host, port=args.port, user=args.user, password=args.password, charset="utf8mb4",
                           autocommit=True)
    with conn.cursor() as c:
        c.execute(f"CREATE DATABASE IF NOT EXISTS `{DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        c.execute(f"USE `{DB}`")
        for stmt in seed.migration_statements():
            c.execute(stmt)
        c.execute("SELECT COUNT(*) FROM ocr_correction_patterns WHERE source = 'learned'")
        learned = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM ocr_known_entries WHERE source = 'learned'")
        learned += c.fetchone()[0]
        user = app_user()
        if user != "root":
            c.execute("SELECT host FROM mysql.user WHERE user = %s", (user,))
            hosts = [r[0] for r in c.fetchall()]
            for host in hosts:
                c.execute(f"GRANT SELECT ON `{DB}`.* TO %s@%s", (user, host))
            print(f"SELECT on {DB} granted to {user} ({', '.join(hosts) or 'no such account yet - create it first'})")
        sums = seed.table_checksums(c)
    conn.close()

    for table, s in sums.items():
        print(f"{table}: {s['rows']} rows")
    if learned:
        print(f"WARNING: {learned} learned rows are in {DB} - it should hold the starter rows only. "
              f"Drop the database and run this again.")
    if args.record:
        import json
        seed.CHECKSUMS.write_text(json.dumps(sums, indent=1), encoding="utf-8")
        print(f"Recorded -> {seed.CHECKSUMS}")
        return 0
    want = seed.recorded()
    if want is None:
        print("No seed_checksums.json to compare with.")
        return 1
    ok = all(sums[t] == want.get(t) for t in sums) and not learned
    print("Seed matches the project's: PASS" if ok else "Seed does NOT match the project's: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
