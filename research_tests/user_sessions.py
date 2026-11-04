"""Test 7 - usability session calculations (no OCR).

    python -m research_tests.user_sessions [--samples] [--file PATH]

Input: inputs/session_data.xlsx, sheet "Sessions" (template:
inputs/session_data_template.xlsx), one line per participant:

  Participant ID | Role | Manual Claims | Manual Time (s) | Manual Errors |
  System Claims | System Time (s) | System Errors | Suggestions Shown |
  Suggestions Accepted | Notes

  times are each condition's total seconds over its claims, errors its
  total errors over its claims.

Per participant and the median (mean too):
  manual and system time per claim; time reduction % (Eq. 3.11)
      = (manual per claim - system per claim) / manual per claim x 100
  errors per claim; error reduction % (Eq. 3.12), the same way
      (blank when the manual condition had no errors)
  suggestion acceptance rate % (Eq. 3.5) = accepted / shown x 100

SUS is not computed unless inputs/sus.xlsx is given (sheet "SUS":
Participant ID, Q1 ... Q10 answered 1-5): standard SUS scoring.
"""
from research_tests import INPUTS, output_dir
from research_tests.common import excel, stats
from research_tests.common.answer_key import _text

TEST_KEY = "user_sessions"
TITLE = "User session results"
SESSION_COLUMNS = ["Participant ID", "Role", "Manual Claims", "Manual Time (s)", "Manual Errors",
                   "System Claims", "System Time (s)", "System Errors", "Suggestions Shown",
                   "Suggestions Accepted", "Notes"]


def _num(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def reduction(before, after):
    """(before - after) / before x 100, or None when before is 0/blank."""
    if before in (None, 0) or after is None:
        return None
    return round(100.0 * (before - after) / before, 2)


def participant(row):
    pid = _text(row.get("Participant ID"))
    mc, sc = _num(row.get("Manual Claims")), _num(row.get("System Claims"))
    mt, st = _num(row.get("Manual Time (s)")), _num(row.get("System Time (s)"))
    me, se = _num(row.get("Manual Errors")), _num(row.get("System Errors"))
    shown, accepted = _num(row.get("Suggestions Shown")), _num(row.get("Suggestions Accepted"))
    per = lambda total, claims: round(total / claims, 2) if total is not None and claims else None
    m_time, s_time = per(mt, mc), per(st, sc)
    m_err, s_err = per(me, mc), per(se, sc)
    return {
        "id": pid, "role": _text(row.get("Role")),
        "manual_time": m_time, "system_time": s_time, "time_reduction": reduction(m_time, s_time),
        "manual_errors": m_err, "system_errors": s_err, "error_reduction": reduction(m_err, s_err),
        "shown": shown, "accepted": accepted,
        "acceptance": stats.percent(accepted, shown) if shown else None,
    }


def sus_score(answers):
    """Standard SUS: odd items (x - 1), even items (5 - x), sum x 2.5."""
    total = 0
    for i, a in enumerate(answers, start=1):
        total += (a - 1) if i % 2 else (5 - a)
    return round(total * 2.5, 2)


def run(progress, samples=False, file=None):
    root = INPUTS / "samples" if samples else INPUTS
    path = file or root / "session_data.xlsx"
    from pathlib import Path
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found - fill in inputs/session_data_template.xlsx and save it as "
                                "inputs/session_data.xlsx (or run with --samples).")
    progress(0.2, f"Reading {path.name}")
    rows = [participant(r) for r in excel.read_rows(path, "Sessions") if _text(r.get("Participant ID"))
            and (_num(r.get("Manual Claims")) or _num(r.get("System Claims")))]
    if not rows:
        raise ValueError(f"No participants in {path.name} (sheet Sessions).")

    cols = ["manual_time", "system_time", "time_reduction", "manual_errors", "system_errors", "error_reduction",
            "acceptance"]
    headers = ["Participant", "Role", "Manual time per claim (s)", "System time per claim (s)",
               "Time reduction % (Eq. 3.11)", "Manual errors per claim", "System errors per claim",
               "Error reduction % (Eq. 3.12)", "Suggestions shown", "Suggestions accepted",
               "Acceptance rate % (Eq. 3.5)"]
    body = [[r["id"], r["role"], r["manual_time"], r["system_time"], r["time_reduction"], r["manual_errors"],
             r["system_errors"], r["error_reduction"], r["shown"], r["accepted"], r["acceptance"]] for r in rows]
    med = ["Median", ""] + [stats.median(r[c] for r in rows) for c in cols[:6]] + [
        stats.median(r["shown"] for r in rows), stats.median(r["accepted"] for r in rows),
        stats.median(r["acceptance"] for r in rows)]
    avg = ["Mean", ""] + [stats.mean(r[c] for r in rows) for c in cols[:6]] + [
        stats.mean(r["shown"] for r in rows), stats.mean(r["accepted"] for r in rows),
        stats.mean(r["acceptance"] for r in rows)]
    pooled_shown = sum(r["shown"] or 0 for r in rows)
    pooled_accepted = sum(r["accepted"] or 0 for r in rows)
    notes = [
        "Time reduction % = (manual time per claim - system time per claim) / manual time per claim x 100 (Eq. 3.11).",
        "Error reduction % = (manual errors per claim - system errors per claim) / manual errors per claim x 100 "
        "(Eq. 3.12); blank when the manual condition had no errors.",
        "Acceptance rate % = suggestions accepted / suggestions shown x 100 (Eq. 3.5). "
        f"Pooled over all participants: {stats.percent(pooled_accepted, pooled_shown)} % "
        f"({int(pooled_accepted)} of {int(pooled_shown)}).",
        f"Source: {path.name}, {len(rows)} participants.",
    ]
    summary = {"name": "7 User sessions", "title": "Table - Time, errors and suggestion acceptance per participant",
               "headers": headers, "rows": body + [med, avg], "notes": notes}
    sheets = [summary]

    sus_path = root / "sus.xlsx"
    if sus_path.is_file():
        progress(0.6, "Scoring SUS")
        sus_rows = []
        for r in excel.read_rows(sus_path, "SUS"):
            answers = [_num(r.get(f"Q{i}")) for i in range(1, 11)]
            if _text(r.get("Participant ID")) and all(a is not None for a in answers):
                sus_rows.append([_text(r.get("Participant ID")), sus_score(answers)])
        if sus_rows:
            scores = [s for _, s in sus_rows]
            sheets.append({"name": "7b SUS", "title": "Table - System Usability Scale scores",
                           "headers": ["Participant", "SUS score"],
                           "rows": sus_rows + [["Median", stats.median(scores)], ["Mean", stats.mean(scores)]],
                           "notes": ["Standard SUS scoring: odd items (answer - 1), even items (5 - answer), "
                                     "sum x 2.5."]})

    out = output_dir(TEST_KEY)
    raw = {"name": "Raw data", "headers": SESSION_COLUMNS,
           "rows": [[r.get(c) for c in SESSION_COLUMNS] for r in excel.read_rows(path, "Sessions")
                    if _text(r.get("Participant ID"))]}
    workbook = excel.write_workbook(out / "user_sessions_results.xlsx", [raw] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    return {"outputs": [workbook], "headline": [
        ["Participants", len(rows)], ["Median time reduction %", med[4]], ["Median error reduction %", med[7]],
        ["Median acceptance rate %", med[10]]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample inputs")
    parser.add_argument("--file", help="session workbook (default inputs/session_data.xlsx)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
