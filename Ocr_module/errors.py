"""
Centralized application exceptions and JSON error handling.

Every error response — whether raised deliberately by a route, raised by
Flask/Werkzeug (404, 413, ...), or an unexpected exception — is turned into
the same flat shape the app already used before this refactor:

    {"success": false, "error": "<human-readable string>"}

`error_code` is added on top as an *additive* field for newer clients (e.g.
PClaimAssist) that want to branch on error type. The existing calibration UI
(templates/index.html) only ever reads `data.error` as plain text, so keeping
it a string (not a nested object) is required for that UI to keep working
unmodified.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class OCRAppError(Exception):
    """Base class for errors that should produce a clean JSON response."""

    status_code = 500
    error_code = "internal_error"

    def __init__(self, message, status_code=None, error_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code

    def to_response_body(self):
        return {"success": False, "error": self.message, "error_code": self.error_code}


class InvalidRequestError(OCRAppError):
    """Missing/malformed request data (bad substitute for a 400)."""

    status_code = 400
    error_code = "invalid_request"


class UnsupportedFileTypeError(OCRAppError):
    """Uploaded file extension isn't one this service accepts."""

    status_code = 415
    error_code = "unsupported_file_type"


class TemplateNotFoundError(OCRAppError):
    """Requested grid template does not exist on disk."""

    status_code = 404
    error_code = "template_not_found"


class OCRProcessingError(OCRAppError):
    """OCR or image/PDF processing failed for a reason worth surfacing."""

    status_code = 500
    error_code = "ocr_processing_failed"


class DatabaseConnectionError(OCRAppError):
    """Could not establish a connection to MariaDB/MySQL."""

    status_code = 503
    error_code = "database_unavailable"


class DatabaseError(OCRAppError):
    """A database query failed after a connection was successfully established."""

    status_code = 500
    error_code = "database_error"


def register_error_handlers(app):
    """Attach JSON error handlers so no route ever leaks a raw traceback."""

    @app.errorhandler(OCRAppError)
    def handle_app_error(err):
        logger.warning("%s: %s", err.error_code, err.message)
        return jsonify(err.to_response_body()), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # Covers Flask/Werkzeug-raised errors (404 on unknown routes, 413 from
        # MAX_CONTENT_LENGTH, 405 method not allowed, etc.) with the same flat
        # JSON shape as the rest of the API instead of Werkzeug's HTML pages.
        logger.info("HTTP exception %s: %s", err.code, err.description)
        return jsonify({
            "success": False,
            "error": err.description or err.name,
            "error_code": (err.name or "http_error").lower().replace(" ", "_"),
        }), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # Anything not already handled above (bare Python exceptions from
        # OpenCV/PaddleOCR/etc). Full details go to the server log only —
        # the client never sees a stack trace.
        logger.exception("Unhandled exception while processing request")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while processing the request.",
            "error_code": "internal_error",
        }), 500
