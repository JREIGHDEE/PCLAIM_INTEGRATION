"""
PClaimAssist OCR service — thin startup entrypoint.

All application wiring (config, logging, error handling, CORS, blueprints)
lives in create_app(). Route logic lives under routes/. OCR processing lives
in ocr_engine.py; image/PDF template algorithms live in template_engine.py
and batch_processor.py (both unchanged from the original project).
"""
import logging

from flask import Flask, render_template
from flask_cors import CORS

import config
from errors import register_error_handlers
from logging_setup import configure_logging
from routes import register_routes

logger = logging.getLogger(__name__)


def create_app():
    configure_logging(debug=config.DEBUG)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    # Always return our own JSON error responses, even in debug mode, so a
    # stack trace is never sent to the client — only ever logged server-side.
    app.config["PROPAGATE_EXCEPTIONS"] = False

    CORS(app, resources={r"/*": {"origins": config.CORS_ORIGINS}})

    config.ensure_directories()

    register_error_handlers(app)
    register_routes(app)

    @app.route("/")
    def home():
        return render_template("index.html")

    logger.info("OCR app ready. Allowed frontend origins: %s", config.CORS_ORIGINS)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
