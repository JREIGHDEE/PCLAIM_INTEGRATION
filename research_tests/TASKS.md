# Who runs what (Chapter 5, Objective 3)

The final Chapter 5 numbers come from **one machine, the project lead's (JRAD)**,
after the last `run_all`. Groupmates prepare inputs and check them on their own
laptops. Performance timing depends on the computer, so **only the project
lead's timing is reported**.

| Who | What | Files you edit | Run |
|---|---|---|---|
| **JRAD (project lead)** | Handwriting (scanner + phone), correction metrics, IQ-01, performance, final `run_all` | — (owns everything not listed below) | `python -m research_tests.run_all`, then the Results tab |
| **Groupmate 1** | Session data: times (7a), errors per claim (7c), suggestion counts (7d), SUS; usability severity list | `research_tests/inputs/sessions/session_data.xlsx` only | `python -m research_tests.user_sessions` (User Sessions tab) |
| **Groupmate 2** | Check the expected box table against the paper forms, then rerun field mapping | `research_tests/inputs/field_mapping_expected.csv` only | `python -m research_tests.field_mapping` (Field Mapping tab) |

Run the commands from the repository root with `Ocr_module\venv\Scripts\python.exe`.
SETUP.md explains the first-time setup.

## Rules so that our work merges cleanly

- Edit only the files in your row of the table. They are separate files, so
  merges don't conflict.
- Never commit `research_tests/outputs/` (it's git-ignored): results are
  remade on the lead's machine.
- Don't edit the scans, the answer keys, `writers.csv` or the task packet.
  `check_setup` flags any change.
- Session data uses **participant codes P1–P5 only**. Never put in names,
  recordings, consent forms or anything else that identifies a participant.
  The pre-commit hook refuses a session file with a name-like value (enable
  it once with `git config core.hooksPath .githooks`).
- Work on `research-testing` (or a branch off it), commit your one file, push,
  and tell the project lead.

## Groupmate 1 — session data

1. Copy `research_tests/inputs/session_data_template.xlsx` to
   `research_tests/inputs/sessions/session_data.xlsx`.
2. **7a Session log:** one row per claim. Participant (P1–P5), order, condition
   (manual / system), claim number, the patient from the task packet (R01–R20),
   and the seconds (or the start and end times) from the recording.
3. Run `python -m research_tests.user_sessions --prefill-errors`. It writes
   `inputs/sessions/claim_errors_prefilled.xlsx` with every reference value of
   every claim. Copy those rows into **7c Claim errors** and type each claim's
   value from its printed forms. Leave "Error after normalization" empty; the
   test works it out.
4. **7d Suggestion log:** one row per suggestion the system showed, with
   Choice = accept / edit / reject / not acted on.
5. **SUS** (optional): each participant's ten answers (1–5).
6. Run `python -m research_tests.user_sessions` and check the "7 User sessions"
   sheet in `outputs/user_sessions/`.
7. The usability severity list is a separate document. Keep it out of the
   repository if it quotes participants.

## Groupmate 2 — expected box table

1. Open `research_tests/inputs/field_mapping_expected.csv`. Each row says
   which box of which form should hold which answer-key value, and in what
   format.
2. For each row, find the box on the paper form (the "Printed label" column
   is a hint). Fix the row if needed, then put `yes` in **Checked**.
3. Add a row for any box the paper form has for a logbook value that the
   table is missing.
4. Run `python -m research_tests.field_mapping`. The PROVISIONAL label
   disappears once every row is checked.
