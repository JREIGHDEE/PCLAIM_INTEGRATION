"""Test 7 - user sessions (no OCR): time, errors and suggestion acceptance
per participant, and SUS.

    python -m research_tests.user_sessions [--samples] [--file PATH]
    python -m research_tests.user_sessions --prefill-errors    (7c reference rows from 7a's claims)

Input: inputs/sessions/session_data.xlsx (template:
inputs/session_data_template.xlsx), filled in by hand from the session
recordings. Participant codes only (P1 ... P5) - never names. Sheets:

  7a Session log     Participant | Order | Condition (manual/system) | Claim # |
                     Patient ID | Start | End | Seconds | Notes
  7c Claim errors    Participant | Condition | Claim # | Patient ID | Form | Box |
                     Value group | Field | Reference value | Claim value |
                     Error type | Error after normalization
  7d Suggestion log  Participant | Claim # | Patient ID | Field | OCR reading shown |
                     Suggestion shown | Choice | Final value | Recording timestamp
  SUS                Participant | Q1 ... Q10   (optional)

Per participant, then the median of the participants (no inferential
statistics, Section 3.6):
  Eq. 3.11 time reduction % = (median manual seconds per claim - median
           system seconds per claim) / median manual x 100
  Eq. 3.12 error reduction % = the same with errors per claim, counted two
           ways: per box (every box that differs from the reference claim) and
           per distinct value (one wrong value repeated across forms counts
           once - the Value group column)
  Eq. 3.5  acceptance rate % = accepted / suggestions shown x 100, where
           shown = accept + edit + reject + not acted on
  Eq. 3.13 SUS score: odd items (answer - 1), even items (5 - answer), x 2.5

An error is a box whose claim value differs from the reference value after
the normalization of Eq. 3.1 (common/normalize.py, so formatting alone is not
an error), a required box left blank, or a value in the wrong box (Error type
"wrong box", counted as typed). The reference claim is the task packet's
values (build_patients.py), so a manual claim is never marked wrong for a
value its maker was not given.
"""
import re
from pathlib import Path

from research_tests import INPUTS, output_dir
from research_tests.common import excel, stats
from research_tests.common.answer_key import _text
from research_tests.common.normalize import normalized

TEST_KEY = "user_sessions"
TITLE = "User session results"
SESSIONS = INPUTS / "sessions" / "session_data.xlsx"
PARTICIPANT = re.compile(r"^P\d{1,2}$")
CHOICES = ("accept", "edit", "reject", "not acted on")
LOG_COLUMNS = ["Participant", "Order (manual first / system first)", "Condition", "Claim #", "Patient ID",
               "Start", "End", "Seconds", "Notes"]
ERROR_COLUMNS = ["Participant", "Condition", "Claim #", "Patient ID", "Form", "Box", "Value group", "Field",
                 "Reference value", "Claim value", "Error type", "Error after normalization"]
SUGGESTION_COLUMNS = ["Participant", "Claim #", "Patient ID", "Field", "OCR reading shown", "Suggestion shown",
                      "Choice", "Final value", "Recording timestamp"]
SUS_COLUMNS = ["Participant"] + [f"Q{i}" for i in range(1, 11)]
# The older one-sheet layout (totals typed in) still reads.
SESSION_COLUMNS = ["Participant ID", "Role", "Manual Claims", "Manual Time (s)", "Manual Errors",
                   "System Claims", "System Time (s)", "System Errors", "Suggestions Shown",
                   "Suggestions Accepted", "Notes"]


def _num(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _seconds(row):
    """Seconds of one claim: the Seconds column, else End - Start (hh:mm:ss)."""
    s = _num(row.get("Seconds"))
    if s is not None:
        return s

    def secs(t):
        if t in (None, ""):
            return None
        if hasattr(t, "hour"):
            return t.hour * 3600 + t.minute * 60 + t.second
        m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", _text(t))
        return int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3] or 0) if m else None
    a, b = secs(row.get("Start")), secs(row.get("End"))
    return b - a if a is not None and b is not None and b >= a else None


def reduction(before, after):
    """(before - after) / before x 100, or None when before is 0/blank."""
    if before in (None, 0) or after is None:
        return None
    return round(100.0 * (before - after) / before, 2)


def check_participants(rows, sheet):
    bad = sorted({_text(r.get("Participant")) for r in rows if not PARTICIPANT.match(_text(r.get("Participant")))})
    if bad:
        raise ValueError(f"Sheet {sheet}: use participant codes P1 ... P5 only (found {len(bad)} other value(s)). "
                         "No names in the session data.")


def _condition(value):
    v = _text(value).lower()
    return "manual" if v.startswith("man") else "system" if v.startswith(("sys", "pclaim")) else v


def is_error(row):
    """Error after normalization (7c), worked out unless typed."""
    typed = _text(row.get("Error after normalization")).lower()
    if typed in ("yes", "no"):
        return typed == "yes"
    if _text(row.get("Error type")).lower() == "wrong box":
        return True
    ref, got = _text(row.get("Reference value")), _text(row.get("Claim value"))
    field = _text(row.get("Field"))
    if ref and not got:
        return True                                   # required box left blank
    return normalized(field, ref) != normalized(field, got)


def time_table(log):
    """{participant: {"manual": [seconds...], "system": [...]}}"""
    out = {}
    for r in log:
        s = _seconds(r)
        if s is not None:
            out.setdefault(_text(r["Participant"]), {"manual": [], "system": []}).setdefault(
                _condition(r.get("Condition")), []).append(s)
    return out


def error_table(rows):
    """{participant: {condition: {claim: {"boxes": n, "values": n}}}}"""
    out = {}
    for r in rows:
        p, cond, claim = _text(r.get("Participant")), _condition(r.get("Condition")), _text(r.get("Claim #"))
        c = out.setdefault(p, {}).setdefault(cond, {}).setdefault(claim, {"boxes": 0, "groups": set()})
        if is_error(r):
            c["boxes"] += 1
            c["groups"].add(_text(r.get("Value group")) or f"{_text(r.get('Form'))}/{_text(r.get('Box'))}")
    return out


def sus_score(answers):
    total = 0
    for i, a in enumerate(answers, start=1):
        total += (a - 1) if i % 2 else (5 - a)
    return round(total * 2.5, 2)


def _sheet(path, name):
    try:
        return excel.read_rows(path, name)
    except KeyError:
        return []


def run(progress, samples=False, file=None, prefill_errors=False):
    if prefill_errors:
        return prefill(progress, Path(file) if file else SESSIONS)
    root = INPUTS / "samples" if samples else INPUTS
    path = Path(file) if file else (root / "session_data.xlsx" if samples else SESSIONS)
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found - copy inputs/session_data_template.xlsx to "
                                "inputs/sessions/session_data.xlsx and fill it in from the recordings.")
    progress(0.2, f"Reading {path.name}")
    log, errs, sugg = _sheet(path, "7a Session log"), _sheet(path, "7c Claim errors"), _sheet(path, "7d Suggestion log")
    log = [r for r in log if _text(r.get("Participant"))]
    errs = [r for r in errs if _text(r.get("Participant"))]
    sugg = [r for r in sugg if _text(r.get("Participant"))]
    if not (log or errs or sugg):
        return run_totals(progress, path, samples)
    for rows, sheet in ((log, "7a"), (errs, "7c"), (sugg, "7d")):
        check_participants(rows, sheet)

    times, errors = time_table(log), error_table(errs)
    participants = sorted(set(times) | set(errors) | {_text(r["Participant"]) for r in sugg},
                          key=lambda p: int(p[1:]))
    rows = []
    for p in participants:
        t = times.get(p, {})
        m_t, s_t = stats.median(t.get("manual", [])), stats.median(t.get("system", []))
        e = errors.get(p, {})
        per = lambda cond, kind: stats.median([(c["boxes"] if kind == "boxes" else len(c["groups"]))
                                               for c in e.get(cond, {}).values()])
        m_b, s_b, m_v, s_v = per("manual", "boxes"), per("system", "boxes"), per("manual", "values"), per("system", "values")
        choices = [_text(r.get("Choice")).lower() for r in sugg if _text(r["Participant"]) == p]
        unknown = [c for c in choices if c not in CHOICES]
        if unknown:
            raise ValueError(f"7d: Choice must be one of {', '.join(CHOICES)} (participant {p}).")
        shown, accepted = len(choices), choices.count("accept")
        rows.append([p, len(t.get("manual", [])), m_t, len(t.get("system", [])), s_t, reduction(m_t, s_t),
                     m_b, s_b, reduction(m_b, s_b), m_v, s_v, reduction(m_v, s_v),
                     shown, accepted, choices.count("edit"), choices.count("reject"), choices.count("not acted on"),
                     stats.percent(accepted, shown) if shown else None])
    med = ["Median", "", stats.median(r[2] for r in rows), "", stats.median(r[4] for r in rows),
           stats.median(r[5] for r in rows)] + [stats.median(r[i] for r in rows) for i in range(6, 12)] + \
          [stats.median(r[i] for r in rows) for i in range(12, 17)] + [stats.median(r[17] for r in rows)]
    headers = ["Participant", "Manual claims", "Manual time per claim (s, median)", "System claims",
               "System time per claim (s, median)", "Time reduction % (Eq. 3.11)",
               "Manual errors per claim (per box)", "System errors per claim (per box)",
               "Error reduction % per box (Eq. 3.12)", "Manual errors per claim (per value)",
               "System errors per claim (per value)", "Error reduction % per value (Eq. 3.12)",
               "Suggestions shown", "Accepted", "Edited", "Rejected", "Not acted on",
               "Acceptance rate % (Eq. 3.5)"]
    notes = [
        "Per participant, then the median of the participants (no inferential statistics, Section 3.6). Times and "
        "errors per claim are each participant's median over their claims in that condition.",
        "Eq. 3.11: (manual - system) / manual x 100, on the median seconds per claim.",
        "Eq. 3.12: the same on errors per claim. Per box = every box that differs from the reference claim (the "
        "task packet's values) after the normalization of Eq. 3.1, a required box left blank, or a value in the "
        "wrong box; per value = one wrong value repeated across forms counts once (Value group).",
        "Eq. 3.5: accepted / suggestions shown x 100; shown = accepted + edited + rejected + not acted on.",
        f"Source: {path.name} (participant codes only).",
    ]
    if samples:
        notes.append("FICTIONAL SAMPLE NUMBERS.")
    sheets = [{"name": "7 User sessions", "title": "Table - Time, errors and suggestion acceptance per participant",
               "headers": headers, "rows": rows + [med], "bold_last": True, "notes": notes}]
    claim_rows = []
    for p in participants:
        for cond in ("manual", "system"):
            for claim, c in sorted(errors.get(p, {}).get(cond, {}).items()):
                secs = next((_seconds(r) for r in log if _text(r["Participant"]) == p
                             and _condition(r.get("Condition")) == cond and _text(r.get("Claim #")) == claim), None)
                claim_rows.append([p, cond, claim, secs, c["boxes"], len(c["groups"])])
    sheets.append({"name": "7c Errors per claim", "title": "Table - Time and errors per claim",
                   "headers": ["Participant", "Condition", "Claim #", "Seconds", "Errors (per box)",
                               "Errors (per distinct value)"], "rows": claim_rows})
    sus_rows = []
    for r in _sheet(path, "SUS") or (_sheet(root / "sus.xlsx", "SUS") if (root / "sus.xlsx").is_file() else []):
        answers = [_num(r.get(f"Q{i}")) for i in range(1, 11)]
        pid = _text(r.get("Participant") or r.get("Participant ID"))
        if pid and all(a is not None for a in answers):
            if not PARTICIPANT.match(pid):
                raise ValueError("SUS: participant codes P1 ... P5 only.")
            sus_rows.append([pid, sus_score(answers)])
    if sus_rows:
        scores = [s for _, s in sus_rows]
        sheets.append({"name": "7b SUS", "title": "Table - System Usability Scale score per participant (Eq. 3.13)",
                       "headers": ["Participant", "SUS score (Eq. 3.13)"],
                       "rows": sus_rows + [["Median", stats.median(scores)]], "bold_last": True,
                       "notes": ["Eq. 3.13 - standard SUS scoring: odd items (answer - 1), even items (5 - answer), "
                                 "sum x 2.5. Per participant + median."]})
    out = output_dir(TEST_KEY)
    workbook = excel.write_workbook(out / "user_sessions_results.xlsx", [
        {"name": "7a Session log", "headers": LOG_COLUMNS, "rows": [[r.get(c) for c in LOG_COLUMNS] for r in log]},
        {"name": "7c Claim errors", "headers": ERROR_COLUMNS + ["Counted as error"],
         "rows": [[r.get(c) for c in ERROR_COLUMNS] + ["Yes" if is_error(r) else "No"] for r in errs]},
        {"name": "7d Suggestion log", "headers": SUGGESTION_COLUMNS,
         "rows": [[r.get(c) for c in SUGGESTION_COLUMNS] for r in sugg]}] + sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    return {"outputs": [workbook], "headline": [["Participants", len(rows)], ["Median time reduction %", med[5]],
                                                ["Median error reduction % (per box)", med[8]],
                                                ["Median acceptance rate %", med[17]]]}


def run_totals(progress, path, samples):
    """The older layout: one Sessions sheet of totals per participant."""
    rows = [r for r in _sheet(path, "Sessions") if _text(r.get("Participant ID"))]
    if not rows:
        raise ValueError(f"{path.name} has no session data (sheets 7a, 7c, 7d - see the template).")
    body = []
    for r in rows:
        mc, sc = _num(r.get("Manual Claims")), _num(r.get("System Claims"))
        per = lambda total, n: round(total / n, 2) if total is not None and n else None
        m_t, s_t = per(_num(r.get("Manual Time (s)")), mc), per(_num(r.get("System Time (s)")), sc)
        m_e, s_e = per(_num(r.get("Manual Errors")), mc), per(_num(r.get("System Errors")), sc)
        shown, acc = _num(r.get("Suggestions Shown")), _num(r.get("Suggestions Accepted"))
        body.append([_text(r.get("Participant ID")), m_t, s_t, reduction(m_t, s_t), m_e, s_e, reduction(m_e, s_e),
                     shown, acc, stats.percent(acc, shown) if shown else None])
    med = ["Median"] + [stats.median(b[i] for b in body) for i in range(1, 10)]
    sheets = [{"name": "7 User sessions", "title": "Table - Time, errors and suggestion acceptance per participant",
               "headers": ["Participant", "Manual time per claim (s)", "System time per claim (s)",
                           "Time reduction % (Eq. 3.11)", "Manual errors per claim", "System errors per claim",
                           "Error reduction % (Eq. 3.12)", "Suggestions shown", "Accepted",
                           "Acceptance rate % (Eq. 3.5)"],
               "rows": body + [med], "bold_last": True,
               "notes": ["Older layout (totals per participant)." + (" FICTIONAL SAMPLE NUMBERS." if samples else "")]}]
    out = output_dir(TEST_KEY)
    workbook = excel.write_workbook(out / "user_sessions_results.xlsx", sheets)
    excel.save_summary(out, TEST_KEY, TITLE, sheets, {"samples": samples})
    progress(1.0, "Done")
    return {"outputs": [workbook], "headline": [["Participants", len(body)], ["Median time reduction %", med[3]]]}


def prefill(progress, path):
    """7c reference rows for every claim listed in 7a: one row per box of the
    expected box table (logbook values) and one per claim-only value of the
    task packet, with the reference value filled in - the researcher only
    types the Claim value (and Error type for a value in the wrong box)."""
    from research_tests import field_mapping
    from research_tests.common import answer_key
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found (fill in 7a first).")
    log = [r for r in _sheet(path, "7a Session log") if _text(r.get("Participant"))]
    check_participants(log, "7a")
    patients = {p["Patient ID"]: p for p in answer_key.patients()}
    expected = field_mapping.load_expected()
    form_names = field_mapping.FORM_NAMES
    claim_only = list(answer_key.CLAIM_COLUMNS) + ["Member is patient", "Member birthday"]
    out_rows = []
    for r in log:
        pid = _text(r.get("Patient ID")).upper()
        p = patients.get(pid)
        if p is None:
            raise ValueError(f"7a: Patient ID {pid!r} is not in the answer key's Patients sheet.")
        for e in expected:
            ref = field_mapping.expected_value(e, p)
            if ref:
                out_rows.append([_text(r["Participant"]), _condition(r.get("Condition")), _text(r.get("Claim #")), pid,
                                 form_names.get(e["Form"], e["Form"]), e["Box ID"], e["Answer-key value"],
                                 e["Answer-key value"] if e["Answer-key value"] in
                                 ("Case number", "Admitted", "Birthday", "Delivered", "Went home") else "",
                                 ref, "", "", ""])
        for col in claim_only:
            if _text(p.get(col)):
                out_rows.append([_text(r["Participant"]), _condition(r.get("Condition")), _text(r.get("Claim #")), pid,
                                 "(each form that prints it)", col, col, "", _text(p.get(col)), "", "", ""])
    target = path.with_name("claim_errors_prefilled.xlsx")
    excel.write_workbook(target, [{"name": "7c Claim errors", "headers": ERROR_COLUMNS, "rows": out_rows,
                                   "notes": ["Copy these rows into session_data.xlsx, sheet 7c Claim errors, and "
                                             "type each Claim value from the claim's printed forms."]}])
    progress(1.0, "Done")
    return {"outputs": [target], "headline": [["Reference rows", len(out_rows)], ["Claims", len(log)]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the fictional sample numbers")
    parser.add_argument("--file", help="session workbook (default inputs/sessions/session_data.xlsx)")
    parser.add_argument("--prefill-errors", action="store_true",
                        help="write 7c reference rows for the claims in 7a (claim_errors_prefilled.xlsx)")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
