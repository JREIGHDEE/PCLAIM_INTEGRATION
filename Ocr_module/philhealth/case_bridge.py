"""Best-effort bridge: case_sessions.reviewed_values (OCR free text) ->
patients/encounters/claims column drafts.

The OCR review UI only ever produces free text keyed by config.py's
TRAINING_CATEGORIES ("CASE #", "DATE & TIME OF ADMISSION", "NAME", "BDAY",
"ADDRESS", "ADMITTING DIAGNOSIS", "DATE & TIME OF DELIVERY",
"FINAL DIAGNOSIS", "DATE & TIME OF DISCHARGE") - handwritten/scanned dates
and names in particular are never in one predictable format. Anything this
module can't confidently parse is left out (never guessed) and reported as
a warning, per the "avoid silently generating incorrect information" rule -
the reviewer fills it in by hand instead.

Every one of the 9 logbook categories above is now drafted into some
destination column (ADDRESS -> patients.address, DATE & TIME OF DELIVERY ->
claims.delivery_date/delivery_time/am_pm_delivery) - previously these two
were captured during OCR review but had nowhere to go and were silently
dropped when a claim was generated. CASE # remains lookup-only (it is the
case_sessions.logbook_case_number key, not a patient/claim field).
"""
import difflib
import re
from datetime import datetime, timedelta

from philhealth import address_parser, field_catalog

# OCR category labels, from Ocr_module/config.py TRAINING_CATEGORIES.
CASE_NUMBER = "CASE #"
NAME = "NAME"
BDAY = "BDAY"
ADDRESS = "ADDRESS"
ADMISSION_DT = "DATE & TIME OF ADMISSION"
DISCHARGE_DT = "DATE & TIME OF DISCHARGE"
DELIVERY_DT = "DATE & TIME OF DELIVERY"
ADMITTING_DX = "ADMITTING DIAGNOSIS"
FINAL_DX = "FINAL DIAGNOSIS"

def target_fields(category):
    """[{"key", "column", "label"}, ...] for the claim fields a logbook
    category maps to. CASE # is lookup-only (case_sessions key, not a claim
    field); an unknown category maps to nothing."""
    if category == CASE_NUMBER:
        return [{"key": None, "column": "case_sessions.logbook_case_number",
                 "label": "Case # (lookup only)"}]
    targets = []
    # field_catalog.OCR_CATEGORY_KEYS must match what
    # draft_patient_and_encounter() below actually fills - keep them in sync.
    for key in field_catalog.OCR_CATEGORY_KEYS.get(category, ()):
        table, column = field_catalog.KEY_SOURCE[key]
        targets.append({
            "key": key,
            "column": f"{table}.{column}",
            "label": field_catalog.FIELD_LABELS.get(key, key),
        })
    return targets

_DATE_FORMATS = (
    "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%y",
    "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
)
# Handwriting OCR often reads a digit as a look-alike letter. Only ever
# applied inside a date or time pattern, never to names or words.
# ("h" is only a 4 upside down - _UPSIDE_DOWN - the right way up it is as
# often a misread "12".)
_OCR_DIGITS = str.maketrans({"O": "0", "o": "0", "D": "0", "Q": "0", "I": "1", "l": "1", "|": "1",
                             "i": "1", "r": "1", "Z": "2", "z": "2", "S": "5", "s": "5", "B": "8", "G": "6",
                             "b": "6", "g": "9", "q": "9", "y": "4", "Y": "4"})
_DIGITISH = r"[0-9OoDQIl|irZzSsBGbgqhyY]"
# mm-dd-yy(yy) as staff write it in the logbook, with -, / or . between.
_DATE_TOKEN = re.compile(
    rf"(?<![0-9A-Za-z])({_DIGITISH}{{1,2}})\s*[-/.]\s*({_DIGITISH}{{1,2}})\s*[-/.]\s*({_DIGITISH}{{2}}(?:{_DIGITISH}{{2}})?)(?![0-9A-Za-z])")
# h:mm, also written h.mm or h;mm, with an optional AM/PM ("1;20pm", "10.30 Am").
_TIME_RE = re.compile(r"(\d{1,2})\s*[:.;]\s*(\d{2})\s*([AaPp])?\.?\s*[Mm]?\b")
_TIME_TOKEN = re.compile(rf"({_DIGITISH}{{1,2}})\s*[:.;]\s*({_DIGITISH}{{2}})\s*([AaPp]\.?\s*[Mm]\.?)?")
# hhmm with the colon lost ("1000AM", "10DDAM"): only taken with its AM/PM.
_COMPACT_TIME_TOKEN = re.compile(
    rf"(?<![0-9A-Za-z])({_DIGITISH}{{1,2}})({_DIGITISH}{{2}})\s*([AaPp]\.?\s*[Mm]\.?)(?![A-Za-z])")
# A date the OCR read upside down (older scans, see ocr_engine.py): its
# characters come in reverse order, each one turned over - 9 reads as "b"
# or 6, 6 as "q" or 9, 4 as "h", 7 as "L", 3 as "E". 04-24-94 read as
# "hb-hZ-ho".
_UPSIDE_DOWN = {"0": "0", "O": "0", "o": "0", "D": "0", "1": "1", "l": "1", "I": "1", "i": "1", "|": "1",
                "2": "2", "Z": "2", "z": "2", "5": "5", "S": "5", "s": "5", "6": "9", "b": "9", "9": "6",
                "q": "6", "g": "6", "8": "8", "B": "8", "h": "4", "y": "4", "Y": "4", "L": "7", "E": "3",
                "-": "-", "/": "/", ".": "."}

# How far a logbook date can be from today and still be believed: a
# birthday is never in the future; an admission, delivery or discharge is
# recent (pages are read within a few years of being written).
_EVENT_YEARS_BACK = 3
_EVENT_DAYS_AHEAD = 31


def date_kind(category):
    """"birth" for the birthday column, "event" for the other date columns."""
    return "birth" if category == BDAY else "event"


def _plausible(iso, kind):
    if not iso or not kind:
        return bool(iso)
    day = datetime.strptime(iso, "%Y-%m-%d").date()
    today = datetime.now().date()
    if kind == "birth":
        return day.year >= 1900 and day <= today
    return (today.replace(year=today.year - _EVENT_YEARS_BACK) <= day
            <= today + timedelta(days=_EVENT_DAYS_AHEAD))


def _date_from_token(match):
    month, day, year = (part.translate(_OCR_DIGITS) for part in match.groups())
    if not (month.isdigit() and day.isdigit() and year.isdigit()):
        return None
    year = int(year)
    if year < 100:  # as strptime's %y: 69-99 -> 1900s, 00-68 -> 2000s
        year += 1900 if year >= 69 else 2000
    try:
        return datetime(year, int(month), int(day)).date().isoformat()
    except ValueError:
        return None


def _turned_over(text):
    """The text as it reads turned the right way up, or None when it has a
    character with no upright reading."""
    out = []
    for char in reversed(text.strip()):
        if char.isspace():
            continue
        if char not in _UPSIDE_DOWN:
            return None
        out.append(_UPSIDE_DOWN[char])
    return "".join(out)


def _parse_date_flexible(text, kind=None):
    """Returns 'YYYY-MM-DD' on success, or None if nothing recognizable.

    Finds the date even when the rest of the text is garbled ("05-21-20
    10.COAM"), and reads OCR look-alikes inside it as digits ("0F" is not
    fixed - F is no digit - but "O8-2I-26" is 08-21-26). A date that isn't
    a real calendar date is None, never guessed. One read upside down
    ("92-h1-b0" for 09-14-26) is turned over when it can't be read as it is.

    kind ("birth" / "event", date_kind()): a date that column can't hold -
    a birthday in the future, an admission years ago - is not believed
    either, so it is left for staff to type rather than suggested."""
    if not text:
        return None
    candidate = _TIME_RE.sub("", text).strip(" ,.-")
    for fmt in _DATE_FORMATS:
        try:
            found = datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            continue
        return found if _plausible(found, kind) else None
    for match in _DATE_TOKEN.finditer(text):
        found = _date_from_token(match)
        if found and _plausible(found, kind):
            return found
        flipped = _turned_over(match.group(0))
        upright = _DATE_TOKEN.fullmatch(flipped) if flipped else None
        found = _date_from_token(upright) if upright else None
        if found and _plausible(found, kind):
            return found
    return None


def _parse_time_flexible(text):
    """Returns (HH:MM in 24h, 'AM'|'PM') on success, or (None, None)."""
    if not text:
        return None, None
    # The time is what's left once the date is taken out ("08.20.26" is a
    # date, not 08:20).
    rest = _DATE_TOKEN.sub(" ", text)
    match = _TIME_TOKEN.search(rest) or _COMPACT_TIME_TOKEN.search(rest)
    if not match:
        return None, None
    hour, minute = (part.translate(_OCR_DIGITS) for part in match.groups()[:2])
    meridiem = (match.group(3) or "").replace(".", "").replace(" ", "")
    if not (hour.isdigit() and minute.isdigit()) or int(hour) > 23 or int(minute) > 59:
        return None, None
    # A lone "0" before AM/PM is an hour that lost a digit ("0:00AM" for
    # 10:00 AM): the logbook writes midnight as 12, so it is not read.
    if hour == "0" and meridiem:
        return None, None
    meridiem = meridiem[:1].upper() + "M" if meridiem else None
    hour = int(hour)
    if meridiem:
        am_pm = meridiem.upper()
        if am_pm == "PM" and hour != 12:
            hour += 12
        elif am_pm == "AM" and hour == 12:
            hour = 0
    else:
        # No AM/PM in the OCR text - can't tell which half of the day this
        # is, so don't guess one; the 24h value stays as-typed and am_pm is
        # reported unknown for the reviewer to set explicitly.
        am_pm = None
    return f"{hour:02d}:{minute}", am_pm


# A name suffix as written in the logbook ("JR.", "Jr", "III"), with the
# periods and commas taken off, -> as it goes in patients.name_ext. Not "V"
# or "I": at the end of a name those are far more often a middle initial.
_SUFFIXES = {"JR": "JR", "JNR": "JR", "SR": "SR", "SNR": "SR", "II": "II", "III": "III", "IV": "IV",
             "2ND": "II", "3RD": "III", "4TH": "IV"}
# Words that belong to the word after them in a surname ("DELA CRUZ",
# "DE LOS SANTOS", "SAN JUAN"): one surname, never split up.
_SURNAME_PARTICLES = {"de", "dela", "del", "della", "delos", "delas", "la", "las", "los", "le",
                      "san", "santa", "sto", "sta", "mac", "mc", "van", "von", "di", "da", "du"}


# A newborn without a name yet is written "BABY GIRL <surname>" (or BOY).
# Handwriting read by OCR: "BBY GIRL", "BB. GRL", "8ABY B0Y", "13ABY GIRI",
# "BABYGIRL". Digits that look like letters are read as those letters, then
# the words are compared with what the logbook writes.
_OCR_LETTERS = str.maketrans({"0": "O", "1": "I", "8": "B", "|": "I", "!": "I"})
_BABY_SPELLINGS = {"BABY", "BBY", "BB", "BABE", "BAEY", "BABV", "BAHY", "BAB", "BABI", "BBAY", "BAYB"}
_GIRL_SPELLINGS = {"GIRL", "GRL", "GIRI", "GURL", "GRIL", "GIRLL", "GIR", "GIRK", "CIRL", "GLRL", "GIRT"}
_BOY_SPELLINGS = {"BOY", "BOI", "BOYY", "BQY", "BOV", "B0Y", "BUY"}


def _ocr_word(word):
    word = re.sub(r"[^A-Za-z0-9|!]", "", word).upper().replace("13", "B")
    return word.translate(_OCR_LETTERS)


def _is_baby_word(word):
    word = _ocr_word(word)
    return word in _BABY_SPELLINGS or (len(word) >= 4 and bool(
        difflib.get_close_matches(word, ["BABY"], n=1, cutoff=0.75)))


def _sex_word(word):
    word = _ocr_word(word)
    if word in _GIRL_SPELLINGS:
        return "GIRL"
    if word in _BOY_SPELLINGS:
        return "BOY"
    return None


def newborn_words(words):
    """("BABY GIRL" | "BABY BOY", the words after it) when a name starts
    with a newborn's "BABY GIRL/BOY" however it was misread, else None."""
    if not words:
        return None
    joined = _ocr_word(words[0])
    for baby in sorted(_BABY_SPELLINGS, key=len, reverse=True):
        # Written as one word: "BABYGIRL", "BBBOY".
        if joined.startswith(baby) and len(joined) > len(baby) and _sex_word(joined[len(baby):]):
            return f"BABY {_sex_word(joined[len(baby):])}", list(words[1:])
    if len(words) >= 2 and _is_baby_word(words[0]) and _sex_word(words[1]):
        return f"BABY {_sex_word(words[1])}", list(words[2:])
    return None


def newborn_of(name):
    """"BABY GIRL" / "BABY BOY" when the name is a newborn's - at its start
    or after the comma ("QUIADO, BB GIRL") - else None."""
    before, comma, after = str(name or "").partition(",")
    found = (newborn_words(after.split()) if comma else None) or newborn_words(before.split())
    return found[0] if found else None


def clean_newborn_name(text):
    """The name with a misread "BABY GIRL/BOY" at its start written properly
    ("BBY GRL DELA CRUZ" -> "BABY GIRL DELA CRUZ"), also after a comma
    ("DELA CRUZ, BB BOY"). Any other name is returned as it was."""
    if not text:
        return text
    before, comma, after = str(text).partition(",")
    if comma:
        found = newborn_words(after.split())
        return f"{before.strip()}, {' '.join([found[0], *found[1]])}" if found else text
    found = newborn_words(str(text).split())
    return " ".join([found[0], *found[1]]) if found else text


# The OCR's character set has no Ñ: PAÑARES is read "PANARES", QUIÑONES
# "QUINONES". Names the clinic's patients have that are written with Ñ are
# put back when a name word matches one exactly with N in its place. Names
# as common without it (NINA, MONTANO, CANADA) are not on the list. Names
# staff have typed with Ñ are added to it (remember_enye_names).
_ENYE_NAMES = {
    "ACUÑA", "BAÑAGA", "BAÑEZ", "BUÑAG", "CABAÑAS", "CABAÑERO", "CAÑEDO", "CAÑETE", "CASTAÑEDA",
    "DAÑO", "DUEÑAS", "ESPAÑA", "ESPAÑOL", "IBAÑEZ", "MAÑAGO", "MAÑALAC", "MIÑOZA", "MUÑOZ", "NIÑO",
    "NUÑEZ", "OÑATE", "ORDOÑEZ", "PAÑARES", "PEÑA", "PEÑAFLOR", "PEÑARANDA", "PIÑOL", "PIÑON",
    "QUIÑONES", "SALDAÑA", "VIÑAS", "YBAÑEZ", "ZUÑIGA",
}
_LEARNED_ENYE = set()


def remember_enye_names(names):
    """Add the words written with Ñ in these names (as staff typed them) to
    the ones put back in OCR readings."""
    for name in names or ():
        for word in re.findall(r"[^\W\d_]+", str(name or "").upper()):
            if "Ñ" in word:
                _LEARNED_ENYE.add(word)


def restore_enye(text):
    """(text with Ñ put back in known names, whether anything changed):
    "MYLENE ABARQUEZ PANARES" -> "MYLENE ABARQUEZ PAÑARES"."""
    if not text:
        return text, False
    known = {name.replace("Ñ", "N"): name for name in _ENYE_NAMES | _LEARNED_ENYE}
    changed = False

    def put_back(match):
        nonlocal changed
        word = match.group(0)
        name = known.get(word.upper())
        if not name:
            return word
        changed = True
        # Written as the word was: PANARES, panares, Panares.
        return name if word.isupper() else name.lower() if word.islower() else name.capitalize()
    return re.sub(r"[A-Za-z]+", put_back, str(text)), changed


def _suffix_of(word):
    return _SUFFIXES.get(word.strip(".,").upper())


def _name_units(words):
    """The words of a name grouped into names: a surname particle goes with
    the word after it ("DE", "LOS", "SANTOS" -> "DE LOS SANTOS"); one left
    at the very end stays with the word before it."""
    units, particles = [], []
    for word in words:
        if word.lower().strip(".") in _SURNAME_PARTICLES:
            particles.append(word)
            continue
        units.append(" ".join(particles + [word]))
        particles = []
    if particles:
        if units:
            units[-1] = " ".join([units[-1]] + particles)
        else:
            units.append(" ".join(particles))
    return units


def _split_given(units):
    """The names before the surname -> (first, middle). The clinic's
    patients most often have one or two given names and one middle name:
      MARY                      first MARY
      MARY MAE                  first MARY, middle MAE
      MARY ANN DENISE           first MARY ANN, middle DENISE
      MA LOURDES ANN SANTOS     first MA LOURDES ANN, middle SANTOS
    The middle name is always the last of them."""
    if not units:
        return None, None
    if len(units) == 1:
        return units[0], None
    if len(units) == 2:
        return units[0], units[1]
    return " ".join(units[:-1]), units[-1]


def _split_name(raw_name):
    """_split_name_parts() with Ñ put back in names the OCR can only read
    with N (restore_enye) - said in the warning, so it is checked."""
    last, first, middle, suffix, warning = _split_name_parts(raw_name)
    restored = False
    parts = []
    for part in (last, first, middle):
        fixed, changed = restore_enye(part)
        parts.append(fixed)
        restored = restored or changed
    if restored:
        note = "Ñ was put back in the name (the computer reads it as N) - please check it."
        warning = f"{warning} {note}" if warning else note
    return parts[0], parts[1], parts[2], suffix, warning


def _split_name_parts(raw_name):
    """Best-effort 'NAME' free text -> (last, first, middle, suffix), plus a
    warning if the split is a guess (no comma to disambiguate order).

    "LAST, FIRST MIDDLE" is taken as written. Without a comma the order is
    "FIRST [MIDDLE] LAST", and how many names there are decides the rest:
      MARY MABEL                    first MARY, last MABEL
      MARY MAE JONAS                first MARY, middle MAE, last JONAS
      MARY ANN DENISE ALCANTARA     first MARY ANN, middle DENISE, last ALCANTARA
    A surname with particles ("DELA CRUZ", "DE LOS SANTOS") counts as one
    name. A suffix (JR, SR, II, III, IV) is taken off wherever the logbook
    put it - at the end, before the comma, or alone after a comma."""
    if not raw_name or not raw_name.strip():
        return None, None, None, None, "Patient name was blank in the OCR review - enter it manually."

    text = " ".join(raw_name.split())
    suffix = None

    # A newborn: "BABY GIRL" (or BOY) is the first name, the last name is
    # the surname, and the words between are its middle name - the mother's
    # maiden surname ("BABY BOY ABARQUEZ PANARES", as staff confirm them).
    # Sometimes they are the mother's first name instead ("BABY GIRL LORNA
    # QUIADO"), so the reviewer is asked to check.
    before, comma, after = text.partition(",")
    found = newborn_words(after.split()) if comma else newborn_words(text.split())
    if found:
        first, rest = found
        if comma:
            last, between = before.strip() or None, rest
        else:
            units = _name_units(rest)
            last, between = (units[-1] if units else None), units[:-1]
        warning = None
        if not last:
            warning = f"Patient name \"{raw_name.strip()}\" has no surname after \"{first}\" - please add it."
        elif between:
            warning = (f"Patient name \"{raw_name.strip()}\" is a newborn's: \"{first}\" as first name, "
                       f"\"{' '.join(between)}\" as middle name, \"{last}\" as last name. If "
                       f"\"{' '.join(between)}\" is the mother's first name, take it out of the middle name.")
        return last, first, " ".join(between) or None, None, warning

    def take_suffix(words):
        nonlocal suffix
        while len(words) > 1 and _suffix_of(words[-1]):
            suffix = suffix or _suffix_of(words[-1])
            words = words[:-1]
        return words

    if "," in text:
        before, _, after = text.partition(",")
        after_words = after.replace(",", " ").split()
        # "JUAN DELA CRUZ, JR": the comma only sets the suffix off.
        if after_words and all(_suffix_of(w) for w in after_words):
            suffix = _suffix_of(after_words[0])
            text = before.strip()
        else:
            last_words = take_suffix(before.split())          # "DELA CRUZ JR., JUAN"
            given_words = after_words
            if len(given_words) > 1 and _suffix_of(given_words[-1]):
                suffix = suffix or _suffix_of(given_words[-1])  # "DELA CRUZ, JUAN JR."
                given_words = given_words[:-1]
            first, middle = _split_given(_name_units(given_words))
            return " ".join(last_words) or None, first, middle, suffix, None

    words = take_suffix(text.split())
    units = _name_units(words)
    if len(units) == 1:
        return units[0], None, None, suffix, (
            "Patient name had only one word with no comma - could not split "
            "into last/first name; please complete it manually."
        )
    last = units[-1]
    first, middle = _split_given(units[:-1])
    guessed = f"\"{first}\" as first name"
    if middle:
        guessed += f", \"{middle}\" as middle name"
    if suffix:
        guessed += f", \"{suffix}\" as suffix"
    warning = (
        f"Patient name \"{raw_name.strip()}\" had no comma to disambiguate order - "
        f"guessed \"{last}\" as last name and {guessed}; please verify."
    )
    return last, first, middle, suffix, warning


# Diagnoses only a woman can have (pregnancy, delivery, after-birth care):
# the patient is then female. A newborn's entry names it "BABY GIRL/BOY".
_MATERNAL_DX = re.compile(
    r"\bG\s?\d+\s?P\s?\d+|\bAOG\b|\bPRE-?NATAL\b|\bPOST-?\s?PARTUM\b|\bN?SVD\b|\bDELIVER(Y|ED)\b|"
    r"\bLABOU?R\b|\bPREGNAN|\bCESAREAN\b|\bC-?SECTION\b|\bPUERPER|\bANTE-?PARTUM\b|\bPPTL\b",
    re.IGNORECASE)
# Entries about the baby's own care ("WELL BABY CARE"): the patient may be
# the baby, so no sex guess. (A delivery diagnosis mentioning "BABY BOY"
# is still about the mother.)
_BABY_CARE = re.compile(r"\bWELL\s*-?\s*BABY\b|\bNEWBORN\b|\bNB\s+SCREEN|\bIMMUNI[SZ]|\bVACCIN|\bBCG\b",
                        re.IGNORECASE)


def infer_patient_sex(name, diagnoses):
    """(sex, reason) when the logbook makes it plain, else (None, None):
    a "BABY GIRL/BOY ..." name, or a pregnancy/delivery/after-birth
    diagnosis (only a woman has those) - unless the entry is about a baby."""
    newborn = newborn_of(name)
    if newborn:
        return ("Female" if newborn == "BABY GIRL" else "Male",
                f"The logbook names the patient \"{name.strip()}\"")
    text = " ".join(d for d in diagnoses if d)
    if _BABY_CARE.search(text):
        return None, None
    found = _MATERNAL_DX.search(text)
    if found:
        return "Female", f"The diagnosis mentions \"{found.group().strip()}\" (pregnancy or birth care)"
    return None, None


def draft_patient_and_encounter(values, reviewed_parts=None, previous_address=None):
    """values: the case_sessions.reviewed_values dict (OCR review free text).

    Returns (patient_fields, encounter_fields, claims_fields, warnings):
      - patient_fields: dict of patients columns this bridge could confidently
        fill (last_name, first_name, middle_name, date_of_birth, address) -
        only keys it actually resolved, never a full dict with blanks/guesses
        baked in.
      - encounter_fields: dict of encounters columns (date_admitted,
        time_admitted, am_pm_admitted, date_discharge, time_discharge,
        am_pm_discharge, admission_dx, discharge_dx), same rule.
      - claims_fields: dict of claims columns this bridge could confidently
        fill (delivery_date, delivery_time, am_pm_delivery), same rule. Only
        ever populated when case_bridge can actually parse a value - a claim
        can exist without any of these (see database/schema.sql's 'draft'
        status), so an empty dict here is normal and expected, not an error.
      - warnings: list of human-readable strings for anything skipped or
        guessed, so the review UI can surface them.

    Never mutates `values`.
    """
    values = dict(values or {})
    warnings = []
    patient_fields = {}
    encounter_fields = {}
    claims_fields = {}

    # Fields a person split into their parts in the logbook review
    # (philhealth/review_fields.py) are used as typed - their free text is
    # not re-parsed, so nothing is guessed and no parse warning applies.
    reviewed_parts = reviewed_parts or {}
    if reviewed_parts:
        from philhealth import review_fields
        tables = {"patients": patient_fields, "encounters": encounter_fields, "claims": claims_fields}
        for category, parts in reviewed_parts.items():
            for (table, column), value in review_fields.claim_fields(category, parts).items():
                tables[table][column] = value
            values.pop(category, None)

    if NAME in reviewed_parts:
        last, first, middle, suffix, name_warning = None, None, None, None, None
    else:
        last, first, middle, suffix, name_warning = _split_name(values.get(NAME))
    if last:
        patient_fields["last_name"] = last
    if first:
        patient_fields["first_name"] = first
    if middle:
        patient_fields["middle_name"] = middle
    if suffix:
        patient_fields["name_ext"] = suffix
    if name_warning:
        warnings.append(name_warning)

    dob = _parse_date_flexible(values.get(BDAY), "birth")
    if dob:
        patient_fields["date_of_birth"] = dob
    elif values.get(BDAY):
        warnings.append(f"Could not parse birth date \"{values.get(BDAY)}\" - please enter it manually.")

    # Free text, no format to parse - passed through as-is, same as the
    # diagnosis fields below (and split into its parts at the end).
    address_raw = values.get(ADDRESS)
    if address_raw and address_raw.strip():
        patient_fields["address"] = address_raw.strip()

    admission_raw = values.get(ADMISSION_DT)
    admission_date = _parse_date_flexible(admission_raw, "event")
    admission_time, admission_ampm = _parse_time_flexible(admission_raw)
    if admission_date:
        encounter_fields["date_admitted"] = admission_date
    elif admission_raw:
        warnings.append(f"Could not parse admission date \"{admission_raw}\" - please enter it manually.")
    if admission_time:
        encounter_fields["time_admitted"] = admission_time
    if admission_ampm:
        encounter_fields["am_pm_admitted"] = admission_ampm

    discharge_raw = values.get(DISCHARGE_DT)
    discharge_date = _parse_date_flexible(discharge_raw, "event")
    discharge_time, discharge_ampm = _parse_time_flexible(discharge_raw)
    if discharge_date:
        encounter_fields["date_discharge"] = discharge_date
    elif discharge_raw:
        warnings.append(f"Could not parse discharge date \"{discharge_raw}\" - please enter it manually.")
    if discharge_time:
        encounter_fields["time_discharge"] = discharge_time
    if discharge_ampm:
        encounter_fields["am_pm_discharge"] = discharge_ampm

    delivery_raw = values.get(DELIVERY_DT)
    delivery_date = _parse_date_flexible(delivery_raw, "event")
    delivery_time, delivery_ampm = _parse_time_flexible(delivery_raw)
    if delivery_date:
        claims_fields["delivery_date"] = delivery_date
    elif delivery_raw:
        warnings.append(f"Could not parse delivery date \"{delivery_raw}\" - please enter it manually.")
    if delivery_time:
        claims_fields["delivery_time"] = delivery_time
    if delivery_ampm:
        claims_fields["am_pm_delivery"] = delivery_ampm

    if values.get(ADMITTING_DX):
        encounter_fields["admission_dx"] = values[ADMITTING_DX]
    if values.get(FINAL_DX):
        encounter_fields["discharge_dx"] = values[FINAL_DX]

    # What the logbook says without a column of its own, so staff check it
    # on the forms instead of typing it (philhealth/form_prefill tags these
    # "From scan - please check"):
    # - the address split into the forms' parts; a ditto mark ("-DO-")
    #   means the address of the patient above it in the logbook
    address = patient_fields.get("address")
    if address and address_parser.is_ditto(address):
        if previous_address:
            patient_fields["address"] = address = previous_address
        else:
            patient_fields.pop("address")
            address = None
            warnings.append("The address is a ditto mark (\"-DO-\") but the patient above it was not found "
                            "- please type the address.")
    if address:
        claims_fields.update(address_parser.split_address(address))
    # - the patient's sex, when the name or diagnosis makes it plain
    if "sex" not in patient_fields:
        name = " ".join(patient_fields.get(k) or "" for k in ("first_name", "middle_name", "last_name"))
        sex, _ = infer_patient_sex(values.get(NAME) or name,
                                   [encounter_fields.get("admission_dx"), encounter_fields.get("discharge_dx")])
        if sex:
            patient_fields["sex"] = sex

    return patient_fields, encounter_fields, claims_fields, warnings
