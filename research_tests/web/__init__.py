"""The research tabs, as their own Flask blueprint (URL prefix
/ocr-testing/research), shown next to the OCR comparison tab.

The main app registers it with one marked block in Ocr_module/app.py:

    from research_tests.web import register_if_enabled
    register_if_enabled(app)

and only when ENABLE_RESEARCH_TESTS is on (environment or Ocr_module/.env:
true / 1 / yes). It is off unless set, so the clinic's launcher
(PClaimAssist.bat) never shows these tabs. With it off the blueprint is not
registered at all: its URLs answer 404 and the tab bar on the OCR
comparison page stays hidden.
"""
import os

URL_PREFIX = "/ocr-testing/research"


def enabled():
    return os.environ.get("ENABLE_RESEARCH_TESTS", "").strip().lower() in ("1", "true", "yes", "on")


def register_if_enabled(app):
    """Register the research blueprint when ENABLE_RESEARCH_TESTS is on.
    Returns True when registered."""
    if not enabled():
        return False
    if "research" in app.blueprints:          # already registered
        return True
    from research_tests.web.routes import research_bp
    app.register_blueprint(research_bp)
    return True
