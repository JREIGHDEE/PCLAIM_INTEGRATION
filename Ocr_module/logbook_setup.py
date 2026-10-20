"""
Guided logbook setup: the simple replacement for drawing a grid template by
hand in the calibration workspace (templates/index.html).

  1. read_scan()  - one scan of the logbook (a PDF with the left and right
                    pages, or one page as a picture). Each page's columns,
                    their names and the patient rows are found automatically
                    (logbook_layout.propose_page) and a preview picture is
                    kept for the person to check.
  2. save_setup() - after the person has checked (and, if needed, moved a
                    line or renamed a column), one grid template per page is
                    saved in the same format the calibration workspace saves,
                    so logbook_pipeline reads it like any other. Older
                    setups can be put away in grid_templates/archive (moved,
                    never deleted) so only the new one is used.

A setup is needed once per kind of logbook, not per scan: matching by the
printed columns and finding the first row from the printed header
(logbook_layout) make one setup fit every scan of that logbook.
"""
import json
import logging
import os
import shutil
import time
import uuid
from datetime import datetime

import cv2

import config
import logbook_layout
from errors import InvalidRequestError
from logbook_pipeline import load_pages
from template_engine import build_template_payload, detect_ruling_lines, map_rows_between_pages
from template_store import get_template_files, save_template_payload

logger = logging.getLogger(__name__)

SETUP_FOLDER = config.UPLOAD_FOLDER / "logbook_setup"
ARCHIVE_FOLDER = config.GRID_TEMPLATES_FOLDER / "archive"
# Preview pictures are scaled down to this width: plenty to check columns.
_PREVIEW_WIDTH = 1400
# One colour per column in the saved template (the workspace shows them).
_COLUMN_COLORS = ("#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#073b4c", "#8338ec", "#fb5607")


def _setup_dir(setup_id):
    if not setup_id or not all(c in "0123456789abcdef" for c in setup_id):
        raise InvalidRequestError("This setup is not valid. Please start again.")
    return SETUP_FOLDER / setup_id


def preview_path(setup_id, page_index):
    return _setup_dir(setup_id) / f"page{int(page_index)}.jpg"


def read_scan(path, ocr_fn):
    """Find each page's layout. Returns {"setup_id", "pages": [...]} where
    each page is logbook_layout.propose_page()'s result plus "index" and
    "picture" (the preview's file name)."""
    pages = load_pages(path)[:2]
    setup_id = uuid.uuid4().hex
    folder = _setup_dir(setup_id)
    os.makedirs(folder, exist_ok=True)

    proposals = []
    for index, (page_number, image, parity) in enumerate(pages):
        # In a PDF the first page is the left one; a lone picture's side is
        # read from its header words.
        side_hint = None
        if parity is not None:
            side_hint = "left" if parity == "odd" else "right"
        proposal = logbook_layout.propose_page(image, ocr_fn)
        if proposal["side_found"] is False and side_hint:
            proposal = logbook_layout.propose_page(image, ocr_fn, side=side_hint)
        proposal["index"] = index
        proposal["ruled_lines"] = detect_ruling_lines(image)["horizontal"]
        scale = min(1.0, _PREVIEW_WIDTH / image.shape[1])
        preview = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else image
        cv2.imwrite(str(preview_path(setup_id, index)), preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
        proposal["picture"] = f"page{index}.jpg"
        proposals.append(proposal)

    # Both halves of a spread share rows: show the right page's rows as the
    # reader will place them, carried over from the left page.
    if len(proposals) == 2 and proposals[0]["side"] == "left" and proposals[1]["side"] == "right":
        left, right = proposals
        rows_px = [{"y": r["y"] * left["height"], "height": r["height"] * left["height"]} for r in left["rows"]]
        mapped = map_rows_between_pages(rows_px, left["ruled_lines"], right["ruled_lines"])
        if mapped:
            right["rows"] = [{"y": round(r["y"] / right["height"], 4),
                              "height": round(r["height"] / right["height"], 4)} for r in mapped]

    with open(folder / "setup.json", "w", encoding="utf-8") as handle:
        json.dump({"pages": proposals}, handle)
    for proposal in proposals:
        proposal.pop("ruled_lines", None)
        proposal.pop("row_template", None)
    logger.info("Logbook setup %s: read %d page(s): %s", setup_id, len(proposals),
                [(p["side"], p["categories"]) for p in proposals])
    return {"setup_id": setup_id, "pages": proposals}


def _clean_page(page):
    side = page.get("side")
    if side not in logbook_layout.SIDE_COLUMNS:
        raise InvalidRequestError("Say whether each page is the left or the right page.")
    lines = page.get("lines") or []
    categories = page.get("categories") or []
    if not lines or len(lines) != len(categories):
        raise InvalidRequestError("Each column needs a name (or 'Do not read').")
    try:
        lines = [float(x) for x in lines]
    except (TypeError, ValueError):
        raise InvalidRequestError("The column lines are not valid. Please start again.")
    if any(not 0 <= x < 1 for x in lines) or lines != sorted(lines):
        raise InvalidRequestError("The column lines are not valid. Please start again.")
    allowed = set(logbook_layout.SIDE_COLUMNS[side])
    named = [c for c in categories if c]
    if any(c not in allowed for c in named):
        raise InvalidRequestError(f"A column name does not belong on the {side} page.")
    if len(named) != len(set(named)):
        raise InvalidRequestError("Two columns have the same name. Give each column its own name.")
    if not named:
        raise InvalidRequestError(f"Name at least one column on the {side} page.")
    return side, lines, categories


def save_setup(setup_id, pages, replace_old=True, saved_by=None):
    """Save one grid template per checked page. Returns {"saved": [file
    names], "archived": [file names]}."""
    folder = _setup_dir(setup_id)
    try:
        with open(folder / "setup.json", encoding="utf-8") as handle:
            found = {p["index"]: p for p in json.load(handle)["pages"]}
    except FileNotFoundError:
        raise InvalidRequestError("This setup has expired. Please read the scan again.")
    if not pages:
        raise InvalidRequestError("There is nothing to save.")

    cleaned = []
    for page in pages:
        index = page.get("index")
        if index not in found:
            raise InvalidRequestError("This setup is not valid. Please start again.")
        cleaned.append((found[index],) + _clean_page(page))
    sides = [side for _, side, _, _ in cleaned]
    if len(sides) != len(set(sides)):
        raise InvalidRequestError("Both pages are marked as the same side. One must be the left page and one the right.")

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    keep = set()
    saved = []
    for proposal, side, lines, categories in cleaned:
        payload = build_template_payload(
            name=f"Logbook {side} page (set up {stamp})",
            grid_lines=lines,
            segment_info=[{"category": c or None, "color": _COLUMN_COLORS[i % len(_COLUMN_COLORS)]}
                          for i, c in enumerate(categories)],
            row_template=proposal["row_template"],
            image_width=proposal["width"],
            image_height=proposal["height"],
            metadata={
                "source": "guided_setup",
                "pageParity": logbook_layout.SIDE_PARITY[side],
                "setupId": setup_id,
                "setupBy": saved_by,
            },
        )
        filename, _ = save_template_payload(payload)
        keep.add(filename)
        saved.append(filename)
        logger.info("Logbook setup %s: saved %s page as %s (%s)", setup_id, side, filename, categories)

    archived = archive_old_setups(keep, {logbook_layout.SIDE_PARITY[s] for s in sides}) if replace_old else []
    shutil.rmtree(folder, ignore_errors=True)
    return {"saved": saved, "archived": archived}


def archive_old_setups(keep, parities):
    """Move every other template for these page sides to the archive folder,
    so only the new setup is used. Nothing is deleted: moving a file back
    into grid_templates brings it back."""
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    moved = []
    for filename in get_template_files():
        if filename in keep:
            continue
        path = config.GRID_TEMPLATES_FOLDER / filename
        try:
            with open(path, encoding="utf-8") as handle:
                parity = (json.load(handle).get("metadata") or {}).get("pageParity", "current")
        except Exception:
            continue
        if parity in parities:
            shutil.move(str(path), str(ARCHIVE_FOLDER / filename))
            moved.append(filename)
    if moved:
        logger.info("Put away older logbook setups: %s", moved)
    return moved


def current_setups():
    """The logbook setups in use: [{"file", "name", "side", "columns",
    "created_at"}], newest first."""
    sides = {v: k for k, v in logbook_layout.SIDE_PARITY.items()}
    found = []
    for filename in get_template_files():
        try:
            with open(config.GRID_TEMPLATES_FOLDER / filename, encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue
        found.append({
            "file": filename,
            "name": data.get("name") or filename,
            "side": sides.get((data.get("metadata") or {}).get("pageParity")),
            "columns": [logbook_layout.PLAIN_NAMES.get(s.get("category"), "Not read")
                        for s in data.get("segmentInfo") or []],
            "created_at": data.get("created_at"),
        })
    return sorted(found, key=lambda s: s["created_at"] or 0, reverse=True)


def clear_old_previews(max_age_hours=24):
    """Remove setup previews nobody finished, after a day."""
    if not os.path.isdir(SETUP_FOLDER):
        return
    cutoff = time.time() - max_age_hours * 3600
    for name in os.listdir(SETUP_FOLDER):
        path = SETUP_FOLDER / name
        if os.path.isdir(path) and os.path.getmtime(path) < cutoff:
            shutil.rmtree(path, ignore_errors=True)
