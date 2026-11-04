"""Isolation for every research test process.

isolate() must run before anything imports the main backend's config:

  1. The OCR tests' working files go to research_tests/outputs/work/, not
     the clinic's uploads/: config reads its folders from the environment
     (OCR_UPLOAD_DIR, OCR_COMPARE_FOLDER, ...), so they are set first. The
     Logbook Reader's crops, the OCR comparison page's runs and its
     workbook are never touched.
  2. Read-only database. db.get_connection is wrapped in this process only
     (the file is not edited) so every connection starts with
     SET SESSION TRANSACTION READ ONLY: MariaDB itself refuses any INSERT,
     UPDATE or DELETE, whichever main module tries it.
  3. research_model(): the correction model built from the pattern and
     known-entry tables with SELECTs only. paddle_assist.load_model() is not
     used because, the first time, it fills those tables from past reviews
     (a write).

The web tabs never call isolate(): they run each test as its own process
(web/jobs.py), and that process calls it.
"""
import logging
import os
import sys

from research_tests import OUTPUTS, WORK

logger = logging.getLogger(__name__)
_state = {"isolated": False}


def _under(path, folder):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(folder)]) == os.path.abspath(folder)
    except ValueError:
        return False


def isolate():
    """Point the main config at research_tests/outputs/work and make every
    database connection read-only. Safe to call more than once."""
    if _state["isolated"]:
        return
    if "config" in sys.modules and not _under(sys.modules["config"].UPLOAD_FOLDER, WORK):
        raise RuntimeError("The research tests must start in their own process, before the main app's "
                           "config is loaded (python -m research_tests.<test>).")
    # The research database (research_tests/setup): only the reference tables
    # the correction model reads, seeded with the system's starter rows - never
    # the clinic's database, whose learned rows came from test-set pages.
    os.environ["DB_NAME"] = os.environ.get("RESEARCH_DB_NAME", "pclaimassist_research")
    os.environ["OCR_UPLOAD_DIR"] = str(WORK / "uploads")
    os.environ["OCR_COMPARE_FOLDER"] = str(WORK / "ocr_compare")
    os.environ["OCR_COMPARE_WORKBOOK"] = str(WORK / "ocr_compare_results.xlsx")
    os.environ["OCR_TESTING_WORKBOOK"] = str(WORK / "ocr_testing_results.xlsx")
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    import config
    for folder in (config.UPLOAD_FOLDER, config.REVIEW_CROPS_FOLDER, config.OCR_COMPARE_FOLDER,
                   config.OCR_COMPARE_WORKBOOK):
        if not _under(folder, WORK):
            raise RuntimeError(f"Isolation failed: {folder} is outside research_tests/outputs/work")
    config.REVIEW_CROPS_FOLDER.mkdir(parents=True, exist_ok=True)
    config.OCR_COMPARE_FOLDER.mkdir(parents=True, exist_ok=True)

    import db
    if not getattr(db.get_connection, "_research_read_only", False):
        original = db.get_connection

        def read_only_connection():
            conn = original()
            with conn.cursor() as cursor:
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
            return conn

        read_only_connection._research_read_only = True
        db.get_connection = read_only_connection

    # One correction model in the whole research process. paddle_assist builds
    # its own in two places - make_corrector() without a model, and
    # fix_saved_reading() (the known fixes ocr_compare.corrected_value applies to
    # address and diagnosis cells) - both through load_model(), which reads the
    # clinic's review tables and falls back silently. Here it is the research
    # model instead (research_model: the research database only, an error if it
    # cannot be read). The file is not edited.
    import paddle_assist
    if not getattr(paddle_assist.load_model, "_research_model", False):
        def research_load_model():
            if _state.get("model") is None:
                _state["model"], _state["model_note"] = research_model()
            return _state["model"]

        research_load_model._research_model = True
        paddle_assist.load_model = research_load_model
        paddle_assist._CACHED.update({"model": None, "at": 0.0})
    _state["isolated"] = True


def database_available():
    """True when MariaDB answers (read-only)."""
    import db
    try:
        db.test_connection()
        return True
    except Exception:
        return False


def research_model():
    """(model, note): paddle_assist's CorrectionModel from the pattern and
    common-entry tables, SELECT only - the same knowledge the Logbook
    Reader uses, without load_model()'s first-time fill (a write)."""
    import config
    import entry_store
    import paddle_assist
    import pattern_store
    # No silent fallback: a run on other knowledge than the research database's
    # would not be comparable (or reproducible on another computer).
    try:
        patterns = pattern_store.load_patterns()
        entries = entry_store.load_entries()
    except Exception as exc:
        raise RuntimeError(f"The research database {config.DB_NAME} could not be read ({exc}). Set it up with "
                           "research_tests/setup (see research_tests/SETUP.md).") from exc
    model = paddle_assist.CorrectionModel.from_patterns(patterns)
    model.add_entries(entries)
    return model, (f"database {config.DB_NAME}: {len(patterns)} correction patterns ({model.examples} observations), "
                   f"{len(entries)} common entries")
