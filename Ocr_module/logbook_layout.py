"""
Reading a logbook page's own layout: its printed column header, where the
patient entries start, and (for the guided setup) where its columns are.

Used two ways:
  - logbook_pipeline: every uploaded scan finds its first patient row from
    the printed header on the page itself, so a template set up on one scan
    works on every other scan of the same logbook, whatever the margins.
  - logbook_setup: the guided "Set up a logbook" page proposes the columns
    and their names, so a person only has to check them, not draw them.
"""
import difflib
import logging
import re

import numpy as np

from template_engine import TemplateAutoDetector, detect_ruling_lines

logger = logging.getLogger(__name__)

# The logbook columns the system reads, in their usual order on each page of
# a spread (left = odd page, right = even page), with plain names for staff.
LEFT_COLUMNS = ("CASE #", "DATE & TIME OF ADMISSION", "NAME", "BDAY", "ADDRESS")
RIGHT_COLUMNS = ("ADMITTING DIAGNOSIS", "DATE & TIME OF DELIVERY", "FINAL DIAGNOSIS", "DATE & TIME OF DISCHARGE")
SIDE_COLUMNS = {"left": LEFT_COLUMNS, "right": RIGHT_COLUMNS}
SIDE_PARITY = {"left": "odd", "right": "even"}
PLAIN_NAMES = {
    "CASE #": "Case number",
    "DATE & TIME OF ADMISSION": "Date & time of admission",
    "NAME": "Patient name",
    "BDAY": "Birthday",
    "ADDRESS": "Address",
    "ADMITTING DIAGNOSIS": "Admitting diagnosis",
    "DATE & TIME OF DELIVERY": "Date & time of delivery",
    "FINAL DIAGNOSIS": "Final diagnosis",
    "DATE & TIME OF DISCHARGE": "Date & time of discharge",
}

# A word in the printed header that names a column. Matched loosely: OCR of
# printed headings drops or swaps letters ("adsmission", "B-dcuy").
_HEADER_KEYWORDS = {
    "CASE": "CASE #",
    "ADMISSION": "DATE & TIME OF ADMISSION",
    "NAME": "NAME",
    "BDAY": "BDAY",
    "BIRTHDAY": "BDAY",
    "BIRTH": "BDAY",
    "ADDRESS": "ADDRESS",
    "ADMITTING": "ADMITTING DIAGNOSIS",
    "DELIVERY": "DATE & TIME OF DELIVERY",
    "FINAL": "FINAL DIAGNOSIS",
    "DISCHARGE": "DATE & TIME OF DISCHARGE",
}
_KEYWORD_CUTOFF = 0.8
# Where on the page the printed header can be.
_HEADER_SEARCH_SHARE = 0.3
# Header words more than this far (share of page height) below the first
# one belong to an entry, not the header.
_HEADER_DEPTH = 0.08


def header_category(text):
    """The column a printed header word names, or None."""
    for word in re.findall(r"[A-Za-z][A-Za-z\-]*", str(text or "")):
        word = word.replace("-", "").upper()
        if len(word) < 4:
            continue
        match = difflib.get_close_matches(word, _HEADER_KEYWORDS, n=1, cutoff=_KEYWORD_CUTOFF)
        if match:
            return _HEADER_KEYWORDS[match[0]]
    return None


def read_header(image, ocr_fn):
    """The printed column header at the top of a page.

    Returns {"bottom": y, "tokens": [{"text", "x0", "x1", "y0", "y1",
    "category"}]} in page pixels, or None when no header is found (fewer
    than two header words). ocr_fn(image) -> [{"text", "box"}, ...]."""
    height = image.shape[0]
    try:
        found = ocr_fn(image[:int(height * _HEADER_SEARCH_SHARE)]) or []
    except Exception:
        logger.exception("Could not read the logbook header")
        return None
    tokens = []
    for token in found:
        box = token.get("box")
        if not box or not str(token.get("text", "")).strip():
            continue
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        tokens.append({"text": str(token["text"]), "x0": min(xs), "x1": max(xs),
                       "y0": min(ys), "y1": max(ys), "category": header_category(token["text"])})
    named = [t for t in tokens if t["category"]]
    if len(named) < 2:
        return None
    # The header is the topmost run of header words, above the first ruled
    # line under them; the first entry just below ("WELL BABY CARE",
    # "DELIVERED ...") may hold a word that looks like a heading.
    first = min(named, key=lambda t: t["y0"])
    first_middle = (first["y0"] + first["y1"]) / 2
    below = [y for y in detect_ruling_lines(image)["horizontal"] if y > first_middle]
    cut = below[0] if below else first["y0"] + height * _HEADER_DEPTH
    named = [t for t in named if (t["y0"] + t["y1"]) / 2 < cut]
    first_top = first["y0"]
    top = first_top - height * 0.03
    bottom = max(t["y1"] for t in named)
    # Every word in that band - "DATE &" above "TIME OF ADMISSION" too -
    # except a bare page number, and the first entry's writing where it
    # crosses into the header (mostly below the header's bottom).
    band = [t for t in tokens
            if t["y1"] > top and (t["y0"] + t["y1"]) / 2 < bottom and not t["text"].strip().isdigit()]
    return {"bottom": float(bottom), "tokens": band}


def first_entry_line(ruled_lines, height, header_bottom):
    """Top of the first patient row: the ruled line under the printed
    header, or the header's bottom when its lettering dips below that line
    (whichever is lower, so no header lettering ends up in the first
    patient's row, which would then be dropped as a header) - or the
    header's bottom alone when no ruled line is near. None without a
    header."""
    if header_bottom is None:
        return None
    gaps = np.diff(ruled_lines) if len(ruled_lines) > 1 else []
    gap = float(np.median(gaps)) if len(gaps) else height * 0.03
    for y in ruled_lines:
        if header_bottom - gap * 0.35 <= y <= header_bottom + gap * 1.5:
            return float(max(y, header_bottom))
    return float(header_bottom)


def guess_side(header):
    """'left' or 'right' from the header words, or None if unclear."""
    if not header:
        return None
    named = [t["category"] for t in header["tokens"] if t["category"]]
    left = sum(1 for c in named if c in LEFT_COLUMNS)
    right = sum(1 for c in named if c in RIGHT_COLUMNS)
    if left == right:
        return None
    return "left" if left > right else "right"


def _header_clusters(tokens, width):
    """Header words grouped into one group per column heading: words that
    overlap or nearly touch side by side belong together."""
    clusters = []
    for token in sorted(tokens, key=lambda t: t["x0"]):
        if clusters and token["x0"] - clusters[-1]["x1"] < width * 0.015:
            last = clusters[-1]
            last["x1"] = max(last["x1"], token["x1"])
            last["categories"].add(token["category"])
        else:
            clusters.append({"x0": token["x0"], "x1": token["x1"], "categories": {token["category"]}})
    for cluster in clusters:
        named = cluster["categories"] - {None}
        cluster["category"] = next(iter(named)) if len(named) == 1 else None
    return clusters


def propose_columns(width, vertical_rules, header, side):
    """Where the columns are, and which is which.

    Returns {"lines": [left edge of each column, as a share of page width],
    "categories": [column name or "" for "don't read"]}. The first column
    starts at the page edge. Column dividers are the page's printed column
    rules; a heading with no printed rule between it and the next (a faint
    or red margin line the scan lost) gets a divider in the gap between the
    two headings. Names come from the header words, then the usual order
    for that side of the logbook.
    """
    expected = list(SIDE_COLUMNS[side])
    rules = sorted(x for x in vertical_rules if width * 0.03 < x < width * 0.97)
    dividers = list(rules)
    clusters = _header_clusters(header["tokens"], width) if header else []

    def unbounded_gaps():
        gaps = []
        for a, b in zip(clusters, clusters[1:]):
            # Headings often run a little past their printed line, so a
            # line anywhere between the two headings' middles separates them.
            middles = ((a["x0"] + a["x1"]) / 2, (b["x0"] + b["x1"]) / 2)
            if b["x0"] <= a["x1"] or any(middles[0] < x < middles[1] for x in dividers):
                continue
            different = bool(a["category"] and b["category"] and a["category"] != b["category"])
            gaps.append((different, b["x0"] - a["x1"], (a["x1"] + b["x0"]) / 2))
        return sorted(gaps, reverse=True)

    # Two differently named headings in one column always need a divider;
    # otherwise add dividers in the widest heading gaps until the page has
    # as many columns as that side of the logbook should.
    for different, gap, middle in unbounded_gaps():
        if different or (len(dividers) + 1 < len(expected) and gap >= width * 0.02):
            dividers.append(middle)
    dividers.sort()

    edges = [0.0] + dividers + [float(width)]
    named_words = [t for t in (header["tokens"] if header else []) if t["category"] in expected]
    categories = []
    for left, right in zip(edges, edges[1:]):
        # Each heading word names the column its middle is in.
        named = [t["category"] for t in named_words if left <= (t["x0"] + t["x1"]) / 2 < right]
        name = max(sorted(set(named)), key=named.count) if named else None
        categories.append(name if name not in categories else None)
    # Fill the rest in the usual order.
    unused = [c for c in expected if c not in categories]
    for index, name in enumerate(categories):
        if name is None and unused:
            categories[index] = unused.pop(0)
    # A column this system has no use for - a code, a remark, a tick - is
    # still proposed, named "" so nothing reads it. It is not clutter: its
    # line is what stops the column before it running to the page edge, and
    # a template whose lines match every rule the page prints is how the
    # reader tells this side of the logbook from the other
    # (score_template_fit). Drop it and the wrong page's setup can win.
    return {
        "lines": [0.01] + [round(x / width, 4) for x in dividers],
        "categories": [c or "" for c in categories],
    }


def propose_page(image, ocr_fn, side=None):
    """Everything the guided setup shows for one page: the side, the
    proposed columns, and the patient rows found with them.

    Returns {"side", "side_found", "width", "height", "lines", "categories",
    "rules", "rows": [{"y", "height"} as shares of page height],
    "row_template"}."""
    height, width = image.shape[:2]
    header = read_header(image, ocr_fn)
    found = guess_side(header)
    side = side or found or "left"
    rules = detect_ruling_lines(image)
    columns = propose_columns(width, rules["vertical"], header, side)

    start = first_entry_line(rules["horizontal"], height, header["bottom"] if header else None)
    gaps = np.diff(rules["horizontal"]) if len(rules["horizontal"]) > 1 else []
    line_gap = float(np.median(gaps)) if len(gaps) else height * 0.03
    draft = {
        "gridLines": columns["lines"],
        "segmentInfo": [{"category": c} for c in columns["categories"]],
        "rowTemplate": {"y": start if start is not None else height * 0.15,
                        "height": line_gap, "spacing": 0},
        "imageWidth": width,
        "imageHeight": height,
    }
    placement = TemplateAutoDetector().auto_place_template(
        image, draft, auto_align=False, rows_start_y=start)
    rows = [r for r in placement["rows"] if r["height"] > 0]
    row_template = dict(draft["rowTemplate"])
    if rows:
        spacing = [b["y"] - (a["y"] + a["height"]) for a, b in zip(rows, rows[1:])]
        row_template = {"y": rows[0]["y"], "height": rows[0]["height"],
                        "spacing": max(0.0, float(np.median(spacing))) if spacing else 0.0}
    return {
        "side": side,
        "side_found": found is not None,
        "width": width,
        "height": height,
        "lines": columns["lines"],
        "categories": columns["categories"],
        # The printed column lines, so a line moved by hand can snap to one.
        "rules": [round(x / width, 4) for x in rules["vertical"]],
        "rows": [{"y": round(r["y"] / height, 4), "height": round(r["height"] / height, 4)} for r in rows],
        "row_template": row_template,
    }
