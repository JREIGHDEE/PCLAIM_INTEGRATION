"""
Shared file-upload handling.

Several routes in app.py used to repeat the same "save uploaded file to a
timestamped temp path, process it, remove it in a finally block" pattern.
This module centralizes that (temp_upload_path) plus the "is there actually
a file here" / "is this an extension we accept" checks (require_file,
validate_extension) that previously varied route to route.
"""
import os
import tempfile
import time
from contextlib import contextmanager

import config
from errors import InvalidRequestError, UnsupportedFileTypeError


def require_file(request_files, field_name="image"):
    """Return the uploaded file for field_name, or raise a 400 error."""
    file = request_files.get(field_name)
    if not file or not file.filename:
        raise InvalidRequestError(f"No file uploaded under field '{field_name}'.")
    return file


def validate_extension(filename, allowed_extensions=None):
    """Raise a 415 error if filename's extension isn't in allowed_extensions."""
    allowed = allowed_extensions or config.ALLOWED_UPLOAD_EXTENSIONS
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed:
        raise UnsupportedFileTypeError(
            f"File type '{ext or 'unknown'}' is not supported. "
            f"Allowed types: {', '.join(sorted(allowed))}"
        )
    return ext


@contextmanager
def temp_upload_path(file, prefix="upload", suffix=".png"):
    """Save an uploaded file to a uniquely named temp path; remove it after use.

    Mirrors the exact save/process/cleanup pattern the original routes used
    inline (same tempfile.gettempdir() + millisecond-timestamp naming).
    """
    temp_path = os.path.join(
        tempfile.gettempdir(),
        f"{prefix}_{int(time.time() * 1000)}{suffix}",
    )
    file.save(temp_path)
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
