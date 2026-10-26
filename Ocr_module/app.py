"""
PClaimAssist OCR service — thin startup entrypoint.

All application wiring (config, logging, error handling, CORS, blueprints)
lives in create_app(). Route logic lives under routes/. OCR processing lives
in ocr_engine.py; image/PDF template algorithms live in template_engine.py
and batch_processor.py (both unchanged from the original project).
"""
import logging
from datetime import timedelta

from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS

import auth
import config
import crop_cleanup
from db import test_connection
from errors import register_error_handlers
from logging_setup import configure_logging
from philhealth import field_catalog
from routes import register_routes

logger = logging.getLogger(__name__)


def create_app():
    configure_logging(debug=config.DEBUG)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    # Always return our own JSON error responses, even in debug mode, so a
    # stack trace is never sent to the client — only ever logged server-side.
    app.config["PROPAGATE_EXCEPTIONS"] = False

    # Session cookie settings (see auth.py). SameSite=Lax with
    # supports_credentials lets the :5500 frontend send its session cookie to
    # this :5000 API; HttpOnly keeps the cookie out of reach of JavaScript, so
    # a scripting bug cannot steal someone's session.
    app.secret_key = config.SECRET_KEY
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Set SESSION_COOKIE_SECURE=True once the pilot runs over HTTPS;
        # a secure cookie is never sent over plain http://127.0.0.1.
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=config.SESSION_LIFETIME_HOURS),
    )

    # supports_credentials is required for the browser to send the session
    # cookie on cross-origin requests (frontend :5500 -> API :5000).
    CORS(app,
         resources={r"/*": {"origins": config.CORS_ORIGINS}},
         supports_credentials=True)

    config.ensure_directories()
    # Review crops past their keep-by date go at startup (crop_cleanup.py).
    try:
        removed = crop_cleanup.purge_old_crops(config.REVIEW_CROPS_MAX_AGE_DAYS)
        if removed:
            logger.info("Deleted %d review crop(s) older than %d days",
                        removed, config.REVIEW_CROPS_MAX_AGE_DAYS)
    except OSError:
        logger.exception("Could not clean up old review crops")

    register_error_handlers(app)
    register_routes(app)
    # Every page and API needs a signed-in account, except the sign-in page.
    auth.require_sign_in(app)

    # ── PClaimAssist frontend ─────────────────────────────────────────
    # Served from this same server so the clinic runs one process on one
    # address. Because the page and the API share an origin, the session
    # cookie is sent on every request and CORS never applies — opening the
    # HTML from the filesystem is what used to break sign-in.
    @app.route("/")
    def pclaimassist_home():
        return send_from_directory(config.PCLAIMASSIST_DIR, "login.html")

    @app.route("/<path:filename>")
    def pclaimassist_file(filename):
        return send_from_directory(config.PCLAIMASSIST_DIR, filename)

    # The OCR calibration/template workspace. This used to sit at "/"; the
    # clinic-facing app now owns that address.
    @app.route("/ocr-workspace")
    def ocr_workspace():
        return render_template(
            "index.html",
            accept=config.OCR_CONFIDENCE_ACCEPT,
            review=config.OCR_CONFIDENCE_REVIEW,
        )

    @app.route("/review")
    def review():
        return render_template(
            "review.html",
            accept=config.OCR_CONFIDENCE_ACCEPT,
            review=config.OCR_CONFIDENCE_REVIEW,
            forms_url=config.PCLAIMASSIST_FORMS_URL,
            claim_required=list(field_catalog.OCR_CLAIM_REQUIRED_CATEGORIES),
        )

    @app.route("/db_health")
    def db_health():
        """Diagnostic: confirms Flask can reach MariaDB before OCR testing.
        Raises DatabaseConnectionError (-> clean 503 JSON) on failure via the
        error handlers registered above, same as any other route.
        """
        version = test_connection()
        return jsonify({
            "success": True,
            "database": config.DB_NAME,
            "server_version": version,
        })

    logger.info("OCR app ready. Allowed frontend origins: %s", config.CORS_ORIGINS)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
