"""How each logbook column is entered and checked in the logbook review.

Pure (no DB, no Flask) - the one place that says, for every OCR'd logbook
column:
  - KIND: which input the review screen shows, mirroring the PClaimAssist
    form input it ends up in (a date picker for dates, date + hour/minute +
    AM/PM for date-and-time, separate last/first/middle/suffix boxes for the
    name, numbers only for the case number);
  - suggest_parts(): the computer's best split of the OCR text into those
    inputs, to pre-fill them;
  - check(): the safeguards - hard problems that must be fixed, and
    unusual-but-possible answers that need a "yes, this is correct";
  - claim_fields(): the reviewed parts as patient/encounter/claim columns,
    used instead of re-parsing free text once a person has reviewed them.

The browser only filters keystrokes (e.g. digits only) for convenience;
every rule here is enforced by the server on save.
"""
import re
from datetime import date, datetime

from philhealth import case_bridge, field_catalog
from philhealth.case_bridge import (
    ADDRESS, ADMISSION_DT, ADMITTING_DX, BDAY, CASE_NUMBER, DELIVERY_DT, DISCHARGE_DT, FINAL_DX, NAME,
)

CASE_NUMBER_KIND, NAME_KIND, DATE_KIND, DATETIME_KIND, TEXT_KIND = (
    "case_number", "name", "date", "datetime", "text")

KIND = {
    CASE_NUMBER: CASE_NUMBER_KIND,
    NAME: NAME_KIND,
    BDAY: DATE_KIND,
    ADDRESS: TEXT_KIND,
    ADMISSION_DT: DATETIME_KIND,
    DELIVERY_DT: DATETIME_KIND,
    DISCHARGE_DT: DATETIME_KIND,
    ADMITTING_DX: TEXT_KIND,
    FINAL_DX: TEXT_KIND,
}

FIELD_NAMES = {
    CASE_NUMBER: "Case number",
    ADMISSION_DT: "Admitted",
    NAME: "Patient name",
    BDAY: "Birthday",
    ADDRESS: "Address",
    ADMITTING_DX: "Reason for admission",
    DELIVERY_DT: "Delivered",
    FINAL_DX: "Final diagnosis",
    DISCHARGE_DT: "Went home",
}

_CASE_NUMBER_RE = re.compile(r"^\d+(-\d+)*$")
# Letters (any alphabet, so ñ/é are fine), spaces, and the punctuation
# real names use: hyphen, period, apostrophe.
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ .'\-]+[^\W\d_]*)*\.?$", re.UNICODE)
_MAX_TEXT = 255          # patients.address is VARCHAR(255)
_MAX_NAME_PART = 100     # patients name columns are VARCHAR(100)
_MAX_SUFFIX = 10         # patients.name_ext is VARCHAR(10)
_OLDEST_BIRTHDAY = date(1900, 1, 1)
_OLDEST_EVENT = date(2000, 1, 1)
_MOTHER_AGE = (10, 55)   # outside this at admission -> please confirm
_LONGEST_STAY_DAYS = 30


def kind_of(category):
    return KIND.get(category, TEXT_KIND)


# ── Suggestions from OCR text ───────────────────────────────────────────

def _split_time(text):
    """(hour 1-12 as str, minute as 2-digit str, 'AM'|'PM'|'') or blanks."""
    hhmm, am_pm = case_bridge._parse_time_flexible(text)
    if not hhmm:
        return "", "", ""
    hour, minute = (int(x) for x in hhmm.split(":"))
    if am_pm is None:
        # No AM/PM written: show the hour as read and let staff pick.
        return str(hour if 1 <= hour <= 12 else (hour % 12 or 12)), f"{minute:02d}", ""
    return str(hour % 12 or 12), f"{minute:02d}", am_pm


def suggest_parts(category, text):
    """Pre-fill for the review inputs, from (OCR or previously typed) text."""
    text = (text or "").strip()
    kind = kind_of(category)
    if kind == CASE_NUMBER_KIND:
        return {"number": "-".join(re.findall(r"\d+", text))}
    if kind == NAME_KIND:
        last, first, middle, warning = case_bridge._split_name(text) if text else (None, None, None, None)
        return {"last": last or "", "first": first or "", "middle": middle or "", "suffix": "",
                "guessed": bool(text) and bool(warning)}
    if kind == DATE_KIND:
        return {"date": case_bridge._parse_date_flexible(text) or ""}
    if kind == DATETIME_KIND:
        hour, minute, am_pm = _split_time(text)
        return {"date": case_bridge._parse_date_flexible(text) or "", "hour": hour, "minute": minute,
                "am_pm": am_pm}
    return {"text": text}


# ── Normalizing, composing, blank ───────────────────────────────────────

def _s(value):
    return str(value if value is not None else "").strip()


def is_marked_empty(parts):
    """Staff pressed "Nothing is written here" for this field."""
    return bool((parts or {}).get("empty"))


def normalize(category, parts):
    """Trimmed, canonical parts (only the keys this kind uses). A field
    marked empty keeps only {"empty": True} - any leftover typing in its
    boxes is dropped, so "empty" can never carry a stale value."""
    parts = parts or {}
    if is_marked_empty(parts):
        return {"empty": True}
    kind = kind_of(category)
    if kind == CASE_NUMBER_KIND:
        return {"number": re.sub(r"\s+", "", _s(parts.get("number")))}
    if kind == NAME_KIND:
        return {k: re.sub(r"\s+", " ", _s(parts.get(k))) for k in ("last", "first", "middle", "suffix")}
    if kind == DATE_KIND:
        return {"date": _s(parts.get("date"))}
    if kind == DATETIME_KIND:
        minute = _s(parts.get("minute"))
        return {
            "date": _s(parts.get("date")),
            "hour": _s(parts.get("hour")).lstrip("0") or ("" if not _s(parts.get("hour")) else "0"),
            "minute": minute.zfill(2) if minute.isdigit() and len(minute) == 1 else minute,
            "am_pm": _s(parts.get("am_pm")).upper(),
        }
    return {"text": re.sub(r"[ \t]+", " ", _s(parts.get("text")))}


def is_blank(category, parts):
    if is_marked_empty(parts):
        return True
    kind = kind_of(category)
    if kind == NAME_KIND:
        return not (parts.get("last") or parts.get("first"))
    if kind in (DATE_KIND, DATETIME_KIND):
        return not parts.get("date")
    if kind == CASE_NUMBER_KIND:
        return not parts.get("number")
    return not parts.get("text")


def _us_date(iso):
    y, m, d = iso.split("-")
    return f"{m}/{d}/{y}"


def compose_text(category, parts):
    """Readable one-line value stored as the reviewed text (and shown in
    exports); the parts themselves are what the claim is built from."""
    kind = kind_of(category)
    if is_blank(category, parts):
        return ""
    if kind == CASE_NUMBER_KIND:
        return parts["number"]
    if kind == NAME_KIND:
        given = " ".join(p for p in (parts.get("first"), parts.get("middle")) if p)
        text = f"{parts.get('last', '')}, {given}".strip(", ")
        return f"{text} {parts['suffix']}" if parts.get("suffix") else text
    if kind == DATE_KIND:
        return _us_date(parts["date"])
    if kind == DATETIME_KIND:
        text = _us_date(parts["date"])
        if parts.get("hour"):
            text += f" {parts['hour']}:{parts.get('minute') or '00'} {parts.get('am_pm', '')}".rstrip()
        return text
    return parts["text"]


# ── Safeguards ──────────────────────────────────────────────────────────

def _as_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _field_problems(category, parts, today):
    """Hard problems in one field: [message, ...] in plain words."""
    kind = kind_of(category)
    problems = []
    if is_blank(category, parts):
        if kind == NAME_KIND and any(parts.get(k) for k in ("middle", "suffix")):
            problems.append("Please type both the last name and the first name.")
        if kind == DATETIME_KIND and any(parts.get(k) for k in ("hour", "minute", "am_pm")):
            problems.append("Please choose the date too, not only the time.")
        return problems

    if kind == CASE_NUMBER_KIND:
        if not _CASE_NUMBER_RE.match(parts["number"]):
            problems.append("The case number can only have numbers (a dash between groups is fine).")
        elif len(parts["number"]) > 20:
            problems.append("The case number is too long.")

    elif kind == NAME_KIND:
        if not parts.get("last") or not parts.get("first"):
            problems.append("Please type both the last name and the first name.")
        for key, label, limit in (("last", "Last name", _MAX_NAME_PART), ("first", "First name", _MAX_NAME_PART),
                                  ("middle", "Middle name", _MAX_NAME_PART), ("suffix", "Suffix", _MAX_SUFFIX)):
            value = parts.get(key)
            if not value:
                continue
            if not _NAME_RE.match(value):
                problems.append(f"{label} can only have letters (no numbers or symbols).")
            elif len(value) > limit:
                problems.append(f"{label} is too long.")

    elif kind in (DATE_KIND, DATETIME_KIND):
        day = _as_date(parts["date"])
        if day is None:
            problems.append("That is not a real date. Please choose it again.")
        elif day > today:
            problems.append("This date is in the future. Please check the year.")
        elif kind == DATE_KIND and day < _OLDEST_BIRTHDAY:
            problems.append("This birthday is too long ago. Please check the year.")
        if kind == DATETIME_KIND and (parts.get("hour") or parts.get("minute") or parts.get("am_pm")):
            hour, minute = parts.get("hour", ""), parts.get("minute", "")
            if not (hour.isdigit() and 1 <= int(hour) <= 12):
                problems.append("The hour must be a number from 1 to 12.")
            if not (minute.isdigit() and len(minute) == 2 and 0 <= int(minute) <= 59):
                problems.append("The minutes must be a number from 00 to 59.")
            if parts.get("am_pm") not in ("AM", "PM"):
                problems.append("Please press AM or PM.")

    elif len(parts["text"]) > _MAX_TEXT:
        problems.append(f"This is too long - keep it under {_MAX_TEXT} letters.")
    return problems


def _moment(parts):
    """datetime for a filled datetime field (time optional), or None."""
    day = _as_date(parts.get("date"))
    if day is None:
        return None
    hour, minute, am_pm = parts.get("hour"), parts.get("minute"), parts.get("am_pm")
    if hour and minute and am_pm in ("AM", "PM") and hour.isdigit() and minute.isdigit():
        h = int(hour) % 12 + (12 if am_pm == "PM" else 0)
        return datetime(day.year, day.month, day.day, h, int(minute))
    return datetime(day.year, day.month, day.day)


def check(parts_by_category, today=None):
    """Safeguards for one patient row.

    Returns (problems, warnings), each [{"category", "message"}]:
      problems - must be fixed before saving (wrong format, impossible date,
                 went home before being admitted, ...);
      warnings - possible but unusual (mother's age, a long stay, delivery
                 outside the stay); saved only once staff confirm.
    """
    today = today or date.today()
    parts = {c: normalize(c, p) for c, p in (parts_by_category or {}).items()}
    problems, warnings = [], []
    for category, p in parts.items():
        if is_marked_empty(p):
            if category in field_catalog.OCR_CLAIM_REQUIRED_CATEGORIES:
                problems.append({"category": category, "message":
                                 "This can't be left empty - the forms need it. "
                                 "If the logbook really has nothing here, get it from the patient's records."})
            continue
        problems += [{"category": category, "message": m} for m in _field_problems(category, p, today)]
    bad = {p["category"] for p in problems}

    def ok(category):
        return category in parts and category not in bad and not is_blank(category, parts[category])

    admitted = _moment(parts[ADMISSION_DT]) if ok(ADMISSION_DT) else None
    went_home = _moment(parts[DISCHARGE_DT]) if ok(DISCHARGE_DT) else None
    delivered = _moment(parts[DELIVERY_DT]) if ok(DELIVERY_DT) else None
    birthday = _as_date(parts[BDAY]["date"]) if ok(BDAY) else None

    if admitted and went_home:
        if went_home < admitted:
            problems.append({"category": DISCHARGE_DT,
                             "message": "\"Went home\" is before \"Admitted\". Please check both dates and times."})
        elif (went_home - admitted).days > _LONGEST_STAY_DAYS:
            warnings.append({"category": DISCHARGE_DT,
                             "message": f"The stay is {(went_home - admitted).days} days long. Is that right?"})
    if delivered and admitted and delivered.date() < admitted.date():
        warnings.append({"category": DELIVERY_DT,
                         "message": "The baby was delivered before the admission date. Is that right?"})
    if delivered and went_home and delivered > went_home:
        warnings.append({"category": DELIVERY_DT,
                         "message": "The baby was delivered after \"Went home\". Is that right?"})
    if birthday and admitted:
        on = admitted.date()
        age = on.year - birthday.year - ((on.month, on.day) < (birthday.month, birthday.day))
        if not _MOTHER_AGE[0] <= age <= _MOTHER_AGE[1]:
            warnings.append({"category": BDAY,
                             "message": f"This makes the patient {age} years old when admitted. Is the birthday right?"})
    for category in (ADMISSION_DT, DELIVERY_DT, DISCHARGE_DT):
        if ok(category) and _as_date(parts[category]["date"]) < _OLDEST_EVENT:
            warnings.append({"category": category,
                             "message": "This date is very old for this logbook. Please check the year."})
    return problems, warnings


# ── Reviewed parts -> claim columns ─────────────────────────────────────

def _time_24h(parts):
    if not (parts.get("hour") and parts.get("minute") and parts.get("am_pm") in ("AM", "PM")):
        return None, None
    h = int(parts["hour"]) % 12 + (12 if parts["am_pm"] == "PM" else 0)
    return f"{h:02d}:{parts['minute']}", parts["am_pm"]


def claim_fields(category, parts):
    """{(table, column): value} for one reviewed field - no guessing, the
    person already split it. Only filled values are returned."""
    parts = normalize(category, parts)
    if is_blank(category, parts):
        return {}
    kind = kind_of(category)
    out = {}
    if category == NAME:
        for key, column in (("last", "last_name"), ("first", "first_name"),
                            ("middle", "middle_name"), ("suffix", "name_ext")):
            if parts.get(key):
                out[("patients", column)] = parts[key]
    elif category == BDAY:
        out[("patients", "date_of_birth")] = parts["date"]
    elif kind == DATETIME_KIND:
        table, prefix = {ADMISSION_DT: ("encounters", "admitted"), DISCHARGE_DT: ("encounters", "discharge"),
                         DELIVERY_DT: ("claims", "delivery")}[category]
        date_col = {"admitted": "date_admitted", "discharge": "date_discharge", "delivery": "delivery_date"}[prefix]
        time_col = {"admitted": "time_admitted", "discharge": "time_discharge", "delivery": "delivery_time"}[prefix]
        out[(table, date_col)] = parts["date"]
        hhmm, am_pm = _time_24h(parts)
        if hhmm:
            out[(table, time_col)] = hhmm
            out[(table, f"am_pm_{prefix}")] = am_pm
    elif category == ADDRESS:
        out[("patients", "address")] = parts["text"]
    elif category == ADMITTING_DX:
        out[("encounters", "admission_dx")] = parts["text"]
    elif category == FINAL_DX:
        out[("encounters", "discharge_dx")] = parts["text"]
    return out
