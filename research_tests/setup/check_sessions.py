"""Pre-commit check: refuse session files that may identify a participant.

Run by .githooks/pre-commit (its RESEARCH TESTS block) on the staged files
under research_tests/inputs/sessions/; also by hand:

    Ocr_module\\venv\\Scripts\\python.exe -m research_tests.setup.check_sessions [files...]

Refused:
  - recordings, consent forms and documents (audio/video/pdf/docx/images) -
    they never belong in the repository;
  - a Participant (or Participant ID) value that is not a code P1, P2, ...;
  - any cell in a free-text column (Notes, OCR reading shown, Suggestion shown,
    Final value, ...) that contains a word on the name list below or reads like
    a person's name (two to four Capitalised words; ALL-CAPS names are not caught, so keep names out) - the test
    patients' values in the task packet are allowed (they are fictional).
"""
import re
import subprocess
import sys
from pathlib import Path

from research_tests import INPUTS, REPO

SESSIONS = INPUTS / "sessions"
NOT_ALLOWED = {".mp3", ".mp4", ".m4a", ".wav", ".mov", ".avi", ".mkv", ".webm", ".pdf", ".doc", ".docx", ".jpg",
               ".jpeg", ".png", ".heic"}
PARTICIPANT = re.compile(r"^P\d{1,2}$")
# Coded columns hold fixed words or codes (Participant is checked on its own);
# every other text column is scanned for something that reads like a name.
CODED = {"Participant", "Participant ID", "Order (manual first / system first)", "Condition", "Claim #",
         "Patient ID", "Form", "Box", "Value group", "Field", "Error type", "Error after normalization", "Choice",
         "Start", "End", "Seconds", "Recording timestamp"}
NAME_LIKE = re.compile(r"\b[A-Z][a-z]+(?:\s+(?:[A-Z]\.|[A-Z][a-z]+)){1,3}\b")
CHOICES = {"accept", "edit", "reject", "not acted on", "manual", "system", "manual first", "system first"}


def _allowed_values():
    """Values the task packet gives (fictional test patients): allowed anywhere."""
    from research_tests.common.excel import read_rows
    packet = INPUTS / "task_packet.xlsx"
    if not packet.is_file():
        return set()
    return {str(r.get("Value") or "").strip().upper() for r in read_rows(packet, "Task packet")}


def problems(path):
    path = Path(path)
    if path.suffix.lower() in NOT_ALLOWED:
        return [f"{path.name}: recordings, consent forms and documents never go in the repository"]
    if path.suffix.lower() != ".xlsx":
        return []
    from openpyxl import load_workbook
    allowed, found = _allowed_values(), []
    wb = load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        if ws.title == "Instructions":
            continue
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(h or "").strip() for h in rows[0]]
        for n, row in enumerate(rows[1:], start=2):
            for header, value in zip(headers, row):
                if not isinstance(value, str) or not value.strip():
                    continue
                text = value.strip()
                if header in ("Participant", "Participant ID"):
                    if not PARTICIPANT.match(text):
                        found.append(f"{path.name} / {ws.title} row {n}: Participant must be a code (P1 ... P5)")
                elif header in ("Choice", "Condition", "Order (manual first / system first)"):
                    if text.lower() not in CHOICES:
                        found.append(f"{path.name} / {ws.title} row {n}, {header}: not one of the allowed words")
                elif header not in CODED and text.upper() not in allowed and NAME_LIKE.search(text):
                    found.append(f"{path.name} / {ws.title} row {n}, {header}: looks like a person's name")
    wb.close()
    return found


def staged_session_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], cwd=REPO,
                         capture_output=True, text=True).stdout.splitlines()
    return [REPO / f for f in out if f.replace("\\", "/").startswith("research_tests/inputs/sessions/")]


def main(argv=None):
    files = [Path(f) for f in (argv if argv is not None else sys.argv[1:])] or staged_session_files()
    found = [p for f in files if Path(f).is_file() for p in problems(f)]
    if found:
        print("Session data refused - it may identify a participant:")
        for p in found[:30]:
            print("  " + p)
        print("Use participant codes (P1 ... P5) and no names; keep recordings and consent forms out of git.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
