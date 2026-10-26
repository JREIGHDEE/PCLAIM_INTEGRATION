"""Deleting the review crops the Logbook Reader shows.

Every logbook upload saves a cell picture per field and a whole-row picture
per patient row under config.REVIEW_CROPS_FOLDER/<upload_id>/ (see
logbook_pipeline._save_crop / _save_row_crops). They are only needed while
the row is being checked, so they are removed:

  delete_session_crops(session)  once the session's claim is exported - only
                                 that row's pictures; the other rows of the
                                 same upload keep theirs
  purge_old_crops(days)          at startup, any picture older than
                                 config.REVIEW_CROPS_MAX_AGE_DAYS, exported
                                 or not

Neither ever touches anything outside the crops folder, and neither raises
on a file that is already gone.
"""
import logging
import os
import time

import config

logger = logging.getLogger(__name__)


def _crop_paths(session):
    """The crop files a case session's OCR fields point at, relative to the
    crops folder ("<upload_id>/<file>.png")."""
    fields = ((session or {}).get("ocr_data") or {}).get("fields") or []
    return {field[key] for field in fields for key in ("crop", "row_crop") if field.get(key)}


def delete_session_crops(session, folder=None):
    """Delete one case session's cell and row pictures. Returns how many
    files were deleted; an upload folder left empty is removed too."""
    root = os.path.realpath(folder or config.REVIEW_CROPS_FOLDER)
    removed = 0
    emptied = set()
    for relative in _crop_paths(session):
        path = os.path.realpath(os.path.join(root, relative))
        if not path.startswith(root + os.sep):
            continue  # never outside the crops folder
        try:
            os.remove(path)
            removed += 1
        except FileNotFoundError:
            pass
        emptied.add(os.path.dirname(path))
    for directory in emptied:
        if directory != root and os.path.isdir(directory) and not os.listdir(directory):
            os.rmdir(directory)
    return removed


def purge_old_crops(days, folder=None, now=None):
    """Delete every crop older than `days` days, and upload folders left
    empty. Returns how many files were deleted. days <= 0 deletes nothing."""
    root = folder or config.REVIEW_CROPS_FOLDER
    if not days or days <= 0 or not os.path.isdir(root):
        return 0
    cutoff = (now if now is not None else time.time()) - days * 86400
    removed = 0
    for directory, _, files in os.walk(root, topdown=False):
        for name in files:
            path = os.path.join(directory, name)
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
                    removed += 1
            except OSError:
                logger.warning("Could not delete old review crop %s", path)
        if os.path.normpath(directory) != os.path.normpath(root) and not os.listdir(directory):
            os.rmdir(directory)
    return removed
