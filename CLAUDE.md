# CLAUDE.md — working on PClaimAssist with the team

PClaimAssist: Flask backend in `Ocr_module/` (PaddleOCR, MariaDB via PyMySQL),
static frontend in `PClaimAssist/` served by the same Flask process, started
with `PClaimAssist.bat`. Setup: `SETUP.md`. What changed and what to do after
pulling: the top entries of `CHANGELOG.md`.

## The source of truth is `origin/main`

`origin/main` is the project lead's (reigh's) version. When anything differs,
**their version wins** unless the person you are working with explicitly says
to keep theirs. Never "fix" a pull by undoing what came from `origin/main`.

## Pulling — do it this way

1. `git status`. If there are local changes, ask what they are for, then commit
   them on a branch of their own (`git switch -c <name>/<topic>`) or
   `git stash push -u -m "before pull"`. Never pull over uncommitted work.
2. `git fetch origin`, then `git switch main` and `git pull --ff-only origin main`.
3. If `--ff-only` refuses, local `main` has commits that are not on
   `origin/main`. Do not merge or rebase them in on your own:
   - make a backup first: `git branch backup/main-<YYYY-MM-DD>`;
   - show the person `git log --oneline origin/main..main` and ask;
   - to take the lead's version: `git reset --hard origin/main` (the backup
     branch keeps their commits), then bring back only what they still need,
     on a new branch.
4. Merge conflicts while bringing `origin/main` into a branch: keep the
   `origin/main` side (`git checkout --theirs <file>` during
   `git merge origin/main`), then re-add the person's change on top only if
   it still makes sense. Show them what you kept.
5. After pulling, follow the newest `CHANGELOG.md` "After pulling" note, then:
   run any new `database/migrations/*.sql` (phpMyAdmin, SQL tab, as root, in
   number order; all are safe to run twice); restart the backend
   (`PClaimAssist.bat` or `Ocr_module/run_ocr.bat`); reload the forms with
   Ctrl+F5.

## Pushing

- Work on a branch, not on `main`. Before pushing, merge the latest
  `origin/main` into it (step 4 above) and run the tests.
- Push `main` only when the person asks you to.
- Add a `CHANGELOG.md` entry (newest first, with an "After pulling" note if a
  migration or restart is needed). Enable the screenshot hook once per clone:
  `git config core.hooksPath .githooks`.

## Tests — must pass before any push

From `Ocr_module/`: `venv\Scripts\python.exe -m unittest discover -p "test_*.py"`.
Expected: all pass, none failing (266 at the time of writing; the database
tests are skipped only when MariaDB is not running). Never skip or loosen a
test to make it pass. A new form field must be added either to
`philhealth/field_catalog.py` `FORM_FIELDS` (its own column) or to
`FORM_VALUES_KEYS` (kept in `claims.form_values`), or `test_form_prefill` fails.

## Things that look wrong but are intended

- **"Not read – marks where the column before it ends"** in the logbook
  setup: the left page's last column is kept on purpose. Its printed line
  stops ADDRESS running to the page edge and tells the left page from the
  right. Do not delete it unless that page really has no line there.
- Every page asks for sign-in; signed-out API calls answer 401. That is the
  server's sign-in check (`auth.require_sign_in`), not a bug.
- "Save as PDF" refuses and lists rule ids (MF-01 ...) while critical rules
  fire. That is required by the research design.
- Logbook pictures of exported claims, and any older than 30 days, are
  deleted (`crop_cleanup.py`).

## Do not

- Set `SKIP_VALIDATION_FOR_EXPORT` (js/pdf/pdf-overlay.js) to `true`, or remove
  the sign-in check, in anything committed.
- Rename files, routes or database tables: the thesis describes them.
- Replace or delete `Ocr_module/grid_templates/*.json` without telling the
  team: they are the clinic's shared logbook setup.
- Edit the XAMPP path in `PClaimAssist.bat` / `backup_db.bat` for one PC: set
  `XAMPP_DIR` in the environment instead.
- Commit `Ocr_module/.env`, `Ocr_module/.secret_key`, `Ocr_module/venv/`,
  `uploads/`, `backups/` or any real patient data (all are git-ignored).
- Change `.bat` line endings: they must stay CRLF (`.gitattributes`).
