"""
Offline AI assist for PaddleOCR - free, no internet, nothing leaves the PC.

PaddleOCR stays the OCR engine. For the logbook cells it is unsure about
("needs_check" / "manual_encoding_required"), two extra steps run on this
machine:

  1. Ensemble voting - PaddleOCR re-reads the cell from a few enhanced
     versions of the image (contrast, sharpened, enlarged, black-and-white).
     The readings vote, weighted by PaddleOCR's own confidence; readings
     that several versions agree on win.

  2. Pattern recognition - a correction model built from the
     ocr_correction_patterns table (database/migrations/006). Each pattern
     is a known PaddleOCR mistake for one logbook column:
       value - a whole value PaddleOCR keeps misreading the same way,
       word  - a word fix (e.g. "N5D" -> "NSD", "Puok" -> "Purok"),
       char  - a letter/digit mix-up in number and date columns ("O" -> "0").
     The table starts with "starter" patterns, and every submitted review
     adds "learned" ones (PaddleOCR's reading vs. what staff confirmed), so
     the system gets more accurate as the clinic uses it. Staff can switch a
     bad pattern off in phpMyAdmin (is_active = 0).

  3. Common entries - a vocabulary of what staff actually enter per text
     column (ocr_known_entries, migration 007), counted from every logbook
     review and every exported form. A word close to a common entry but not
     quite it ("Pregnacy", "Calinon") is snapped to it, and a whole address
     or diagnosis close to one staff confirmed before is suggested. A
     corrected patient name is only ever a hint, never pre-filled, so a rare
     real name can't be "fixed" into a common one.

Safety rules: an AI reading is never auto-accepted - at best a field
becomes "needs_check", so staff still confirm it; a reading the AI isn't
sure of is only a hint (field["ai"]), not pre-filled; any failure leaves the
PaddleOCR result as it was. PaddleOCR's own reading stays on every field
(raw_text, confidence) so Paddle-only accuracy can still be measured.
"""
import logging
import re
import time
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import cv2

import config
from philhealth import review_fields

logger = logging.getLogger(__name__)

MODEL_NAME = "PaddleOCR ensemble + pattern recognition (offline)"

# Statuses, the same strings logbook_pipeline uses (not imported from there
# to avoid a circular import).
NEEDS_CHECK = "needs_check"
MANUAL = "manual_encoding_required"

VALUE, WORD, CHAR = "value", "word", "char"

# Text columns that have a vocabulary of common entries (ocr_known_entries).
_ENTRY_CATEGORIES = ("NAME", "ADDRESS", "ADMITTING DIAGNOSIS", "FINAL DIAGNOSIS")
# Whole values are only suggested for these (names are unique per patient).
_VALUE_ENTRY_CATEGORIES = ("ADDRESS", "ADMITTING DIAGNOSIS", "FINAL DIAGNOSIS")
# Code columns: every confirmed value is kept (ocr_known_entries, as a
# "value"), never suggested as such - each case number is unique - but used
# to learn the column's usual format: year prefix, separators, length.
_FORMAT_CATEGORIES = ("CASE #",)
# A format feature is used once this share of confirmed codes has it.
_FORMAT_SHARE = 0.6
_CODE_SPLIT = re.compile(r"[^0-9A-Za-z]+")
# How close a reading must be to a common entry (difflib ratio, 0-1), and
# how often the entry must have been entered, before it is suggested.
_WORD_MATCH = 0.8
_VALUE_MATCH = 0.85
_MIN_ENTRY_WEIGHT = 2
_WORD_RE = re.compile(r"^[^\W\d_]{3,}$", re.UNICODE)  # 3+ letters, no digits
# Each half of two words read as one must be this long ("CASANTAN|DAUAO").
_SPLIT_MIN = 4
# Looser match for the word right before "Davao" / "DC" - the barangay
# ("CARSANTAN" -> "Cabantian").
_BEFORE_CITY_MATCH = 0.7
# "City" shortened or misread right after "Davao": "CY", "CTY", "C1TY".
_CITY_SHORT = re.compile(r"^C[A-Z0-9]{0,3}$")

# Columns whose values are digits and separators - where single-character
# confusions can be fixed safely.
_DIGIT_KINDS = {review_fields.CASE_NUMBER_KIND, review_fields.DATE_KIND, review_fields.DATETIME_KIND}
# Letters that legitimately appear in date-and-time values ("10:30 AM").
_DATETIME_LETTERS = set("AaPpMm")

# Starter knowledge for number/date columns, used only when the patterns
# table isn't there yet (migration 006 seeds the same list into the table).
_STARTER_WEIGHT = 2
_STARTER_CHARS = {"O": "0", "o": "0", "D": "0", "Q": "0", "l": "1", "I": "1", "i": "1", "|": "1",
                  "Z": "2", "z": "2", "S": "5", "s": "5", "G": "6", "b": "6", "T": "7", "B": "8", "g": "9", "q": "9"}

# A pattern is used only when seen at least this often, and when it was the
# outcome at least this share of the time.
_MIN_SEEN = 2
_MIN_SHARE = 0.6
# Punctuation around a word that shouldn't stop it matching a word pattern.
_EDGE_PUNCT = ".,;:()"


def _norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


# ── 1. Ensemble voting ────────────────────────────────────────────────────

def _gray(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image


def _bgr(gray):
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def _contrast(image):
    return _bgr(cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(_gray(image)))


def _sharpen(image):
    blurred = cv2.GaussianBlur(image, (0, 0), 1.5)
    return cv2.addWeighted(image, 1.6, blurred, -0.6, 0)


def _enlarge(image):
    return cv2.resize(image, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)


def _black_and_white(image):
    gray = cv2.GaussianBlur(_gray(image), (3, 3), 0)
    return _bgr(cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12))


VARIANTS = [("contrast", _contrast), ("sharpened", _sharpen), ("enlarged", _enlarge),
            ("black_and_white", _black_and_white)]


def _combine(tokens):
    """(text, confidence) the same way logbook_pipeline.ocr_cell combines
    tokens: joined text, lowest token confidence. None when nothing read."""
    tokens = [t for t in (tokens or []) if str(t.get("text", "")).strip()]
    if not tokens:
        return None
    return (" ".join(str(t["text"]).strip() for t in tokens),
            float(min(t.get("confidence", 0) for t in tokens)))


def _read(ocr_fn, image):
    return _combine(ocr_fn(image))


def versions(crop):
    """The enhanced versions of a crop the ensemble reads, in VARIANTS order."""
    return [make(crop) for _, make in VARIANTS[:config.AI_ENSEMBLE_VARIANTS]]


def ensemble_read(ocr_fn, crop, original_text, original_confidence, version_tokens=None):
    """Vote over PaddleOCR's readings of the original and enhanced crops.
    Returns {"text", "votes", "readings", "confidence"} or None if no
    version produced any text.

    version_tokens: the versions' tokens already read in one batch for many
    fields (ocr_engine.read_versions_many, see make_corrector); otherwise
    each version is read with ocr_fn here."""
    readings = []
    if _norm(original_text):
        readings.append((_norm(original_text), float(original_confidence or 0)))
    for index, (name, make) in enumerate(VARIANTS[:config.AI_ENSEMBLE_VARIANTS]):
        try:
            if version_tokens is not None:
                reading = _combine(version_tokens[index] if index < len(version_tokens) else None)
            else:
                reading = _read(ocr_fn, make(crop))
        except Exception:
            logger.exception("Ensemble read failed on the %s version", name)
            continue
        if reading:
            readings.append((_norm(reading[0]), reading[1]))
    if not readings:
        return None

    # Group readings that differ only in letter case; the group's score is
    # the sum of its confidences, so agreement and confidence both count.
    groups = defaultdict(list)
    for text, confidence in readings:
        groups[text.upper()].append((text, confidence))
    best = max(groups.values(), key=lambda g: (sum(c for _, c in g), len(g)))
    text = max(best, key=lambda r: r[1])[0]
    return {
        "text": text,
        "votes": len(best),
        "readings": len(readings),
        "confidence": round(sum(c for _, c in best) / len(best), 4),
    }


# ── 2. Pattern recognition ────────────────────────────────────────────────

def _split_edges(word):
    """'(Davao,' -> ('(', 'Davao', ',') so punctuation doesn't stop a match."""
    core = word.strip(_EDGE_PUNCT)
    if not core:
        return "", word, ""
    start = word.index(core)
    return word[:start], core, word[start + len(core):]


def _words_and_gaps(category, text):
    """text -> (words, the gaps between them). Addresses and diagnoses are
    also split where a period, comma or semicolon joins two words with no
    space ("CABANNAN.DAVAOC"); that gap becomes ", ". Other columns split on
    spaces only, so a date or time ("11:15") is never taken apart."""
    if category not in _VALUE_ENTRY_CATEGORIES:
        words = text.split(" ")
        return words, [" "] * (len(words) - 1)
    pieces = re.split(r"(\s+|(?<=[^\W\d_])[.,;]+(?=[^\W\d_]))", text, flags=re.UNICODE)
    words, gaps = pieces[0::2], pieces[1::2]
    return words, [gap if gap.isspace() else ", " for gap in gaps]


def _is_davao(word):
    """'DAVAO', a close misreading ('DAUAO', 'DAAO'), or 'DC'."""
    word = word.upper()
    return word == "DC" or word.startswith("DAVAO") or SequenceMatcher(None, word, "DAVAO").ratio() >= _WORD_MATCH


def _davao_city(word):
    """'DAVAOC', 'DAUAOCY', 'DAVAOCITY': Davao with City run onto it."""
    word = word.upper()
    for cut in range(4, min(len(word), 7)):
        left, right = word[:cut], word[cut:]
        if ((right == "CITY" or _CITY_SHORT.match(right))
                and SequenceMatcher(None, left, "DAVAO").ratio() >= _WORD_MATCH):
            return True
    return False


def extract_patterns(category, raw, final):
    """What one reviewed field teaches: [(pattern_type, wrong_key, correct)].
    Includes "no change" patterns (wrong == correct) too - they are what
    stop a fix being applied when staff usually keep PaddleOCR's reading."""
    raw, final = _norm(raw), _norm(final)
    if not raw or not final:
        return []
    patterns = [(VALUE, raw.upper(), final)]
    # Pairs that were re-formatted rather than corrected (e.g. a date typed
    # in a different layout) align meaninglessly - keep only the whole value.
    if SequenceMatcher(None, raw.upper(), final.upper()).ratio() < 0.5:
        return patterns
    raw_words = [_split_edges(w)[1] for w in raw.split(" ")]
    final_words = [_split_edges(w)[1] for w in final.split(" ")]
    for op, i1, i2, j1, j2 in SequenceMatcher(None, [w.upper() for w in raw_words],
                                              [w.upper() for w in final_words]).get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for wrong, right in zip(raw_words[i1:i2], final_words[j1:j2]):
                if wrong and right:
                    patterns.append((WORD, wrong.upper(), right))
    if review_fields.kind_of(category) in _DIGIT_KINDS:
        for op, i1, i2, j1, j2 in SequenceMatcher(None, raw, final).get_opcodes():
            if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
                for wrong, right in zip(raw[i1:i2], final[j1:j2]):
                    patterns.append((CHAR, wrong, right))
    return patterns


def reviewed_patterns(fields):
    """Patterns from a list of reviewed OCR fields, with counts:
    [(category, pattern_type, wrong_key, correct, count)]."""
    counts = Counter()
    for field in fields:
        category = field.get("category")
        if not category or field.get("deferred_to_forms") or field.get("marked_empty"):
            continue
        for pattern in extract_patterns(category, field.get("raw_text"), field.get("value")):
            counts[(category, *pattern)] += 1
    return [(*key, count) for key, count in counts.items()]


def extract_entries(category, text):
    """Common-entry candidates in one entered value:
    [(entry_type, entry_key, entry_text)]. Text columns, plus the whole
    value of code columns (for format learning)."""
    text = _norm(text)
    if category in _FORMAT_CATEGORIES:
        return [(VALUE, text.upper(), text)] if text else []
    if category not in _ENTRY_CATEGORIES:
        return []
    if not text:
        return []
    entries = [(VALUE, text.upper(), text)] if category in _VALUE_ENTRY_CATEGORIES else []
    for word in text.split(" "):
        core = _split_edges(word)[1]
        if _WORD_RE.match(core):
            entries.append((WORD, core.upper(), core))
    return entries


def count_entries(pairs):
    """[(category, text)] -> [(category, entry_type, entry_key, entry_text, count)]."""
    counts, display = Counter(), {}
    for category, text in pairs:
        for entry_type, key, shown in extract_entries(category, text):
            counts[(category, entry_type, key)] += 1
            display[(category, entry_type, key)] = shown
    return [(*key, display[key], n) for key, n in counts.items()]


def reviewed_entries(fields):
    """Common entries confirmed in a list of reviewed OCR fields."""
    return count_entries((f.get("category"), f.get("value")) for f in fields
                         if not f.get("deferred_to_forms") and not f.get("marked_empty"))


def form_entries(values):
    """Common entries in PhilHealth form values ({form key: text}), mapped to
    logbook columns via field_catalog.OCR_CATEGORY_KEYS."""
    from philhealth import field_catalog
    pairs = []
    for category in _ENTRY_CATEGORIES:
        for key in field_catalog.OCR_CATEGORY_KEYS.get(category, ()):
            value = values.get(key)
            if isinstance(value, str) and value.strip():
                pairs.append((category, value))
    return count_entries(pairs)


def _match_case(original, replacement):
    """Write the replacement the way the original was written."""
    if original.isupper():
        return replacement.upper()
    if original.islower():
        return replacement.lower()
    if original.istitle():
        return replacement[:1].upper() + replacement[1:].lower()
    return replacement


class CorrectionModel:
    """How often each PaddleOCR reading ended up as each confirmed value,
    per logbook column and pattern type."""

    def __init__(self):
        self.patterns = {VALUE: defaultdict(Counter), WORD: defaultdict(Counter), CHAR: defaultdict(Counter)}
        self.examples = 0
        # Common entries: (category, entry_type) -> {KEY: (text, weight)}.
        self.entries = defaultdict(dict)
        # Confirmed codes per code column: [(text, times confirmed)].
        self.codes = defaultdict(list)

    def add_entry(self, category, entry_type, key, text, weight):
        if weight >= _MIN_ENTRY_WEIGHT:
            self.entries[(category, entry_type)][key] = (text, weight)

    def add_entries(self, rows):
        """rows: [(category, entry_type, entry_key, entry_text, times_from_reviews, total_weight)].
        Whole values count only logbook reviews; words count everything.
        Confirmed codes (case numbers) only teach the column's format."""
        for category, entry_type, key, text, from_reviews, total in rows:
            if category in _FORMAT_CATEGORIES:
                if entry_type == VALUE and from_reviews > 0:
                    self.codes[category].append((text, from_reviews))
                continue
            self.add_entry(category, entry_type, key, text, from_reviews if entry_type == VALUE else total)

    def code_format(self, category):
        """The usual format of confirmed codes in this column, learned from
        every confirmed value: {"prefix", "known_prefixes", "compact",
        "separator", "samples"}, or None with fewer than 2 confirmed codes."""
        samples = self.codes.get(category) or []
        total = sum(w for _, w in samples)
        if total < 2:
            return None
        prefixes, separators = Counter(), Counter()
        compact = 0
        for text, weight in samples:
            if re.fullmatch(r"[0-9A-Za-z]+", text):
                compact += weight
            else:
                separators[re.search(r"[^0-9A-Za-z]+", text).group()[0]] += weight
            digits = re.sub(r"\D", "", text)
            if len(digits) >= 6:
                prefixes[digits[:4]] += weight
        prefix = None
        if prefixes:
            top, count = prefixes.most_common(1)[0]
            if count / total >= _FORMAT_SHARE:
                prefix = top
        return {
            "prefix": prefix,
            "known_prefixes": set(prefixes),
            "compact": compact / total >= _FORMAT_SHARE,
            "separator": separators.most_common(1)[0][0] if separators else "",
            "samples": total,
        }

    def _apply_code_format(self, category, text, notes):
        """Reshape a code reading to the learned format: a misread year
        prefix ("2020", "702", "2o2e") becomes the usual one, and spaces or
        stray marks are dropped or kept the way staff write the codes."""
        fmt = self.code_format(category)
        groups = [g for g in _CODE_SPLIT.split(text) if g]
        if not fmt or not groups:
            return text

        def prefix_like(part):
            # A year staff have confirmed before (e.g. last year's 2025) is
            # left alone; otherwise anything resembling the prefix is it.
            return (part != fmt["prefix"] and part not in fmt["known_prefixes"]
                    and SequenceMatcher(None, part.upper(), fmt["prefix"]).ratio() >= 0.5)

        if fmt["prefix"]:
            if len(groups) >= 2 and 2 <= len(groups[0]) <= 5 and prefix_like(groups[0]):
                groups[0] = fmt["prefix"]
            elif len(groups) == 1 and len(groups[0]) >= 6 and prefix_like(groups[0][:4]):
                groups[0] = fmt["prefix"] + groups[0][4:]
        shaped = ("" if fmt["compact"] else (fmt["separator"] or " ")).join(groups)
        if shaped != text:
            notes.append(f"'{text}' -> '{shaped}' (usual case-number format, learned from "
                         f"{fmt['samples']} confirmed)")
        return shaped

    def _closest_entry(self, category, entry_type, text, cutoff):
        """The common entry closest to `text` -> (entry text, weight), or None
        when `text` is itself a common entry or nothing is close enough."""
        known = self.entries.get((category, entry_type))
        if not known:
            return None
        key = text.upper()
        if key in known:
            return None
        best = None
        for candidate, (shown, weight) in known.items():
            if abs(len(candidate) - len(key)) > max(2, len(key) // 4):
                continue
            score = SequenceMatcher(None, key, candidate).ratio()
            if score >= cutoff and (best is None or (score, weight) > best[0]):
                best = ((score, weight), shown)
        return (best[1], best[0][1]) if best else None

    def _split_run_together(self, category, word):
        """Two common words read as one ("CASANTANDAUAO" -> ("Cabantian",
        "Davao")), or None. Both halves must be close to a common word and
        at least _SPLIT_MIN letters long, so a real word that is simply not
        in the vocabulary is left as read."""
        known = self.entries.get((category, WORD)) or {}

        def match(part):
            if part.upper() in known:
                return known[part.upper()][0], 1.0
            found = self._closest_entry(category, WORD, part, _WORD_MATCH)
            if not found:
                return None
            return found[0], SequenceMatcher(None, part.upper(), found[0].upper()).ratio()

        best = None
        for cut in range(_SPLIT_MIN, len(word) - _SPLIT_MIN + 1):
            left, right = match(word[:cut]), match(word[cut:])
            if left and right:
                score = min(left[1], right[1])
                if best is None or score > best[0]:
                    best = (score, (left[0], right[0]))
        return best[1] if best else None

    def add(self, category, pattern_type, wrong, correct, count=1):
        self.patterns[pattern_type][(category, wrong)][correct] += count
        self.examples += count

    @classmethod
    def from_patterns(cls, rows):
        """rows: [(category, pattern_type, wrong_key, correct, count)]."""
        model = cls()
        for category, pattern_type, wrong, correct, count in rows:
            if pattern_type in model.patterns:
                model.add(category, pattern_type, wrong, correct, count)
        return model

    @classmethod
    def with_starter_knowledge(cls, fields=()):
        """No patterns table: the built-in starter list + past reviews."""
        rows = [(category, CHAR, wrong, right, _STARTER_WEIGHT)
                for category, kind in review_fields.KIND.items() if kind in _DIGIT_KINDS
                for wrong, right in _STARTER_CHARS.items()]
        return cls.from_patterns(rows + reviewed_patterns(fields))

    def _best(self, pattern_type, category, wrong, current):
        """The pattern's replacement for `current`, or None."""
        counter = self.patterns[pattern_type].get((category, wrong))
        if not counter:
            return None
        seen = sum(counter.values())
        if seen < _MIN_SEEN:
            return None
        value, count = counter.most_common(1)[0]
        if value == current or count / seen < _MIN_SHARE:
            return None
        return value

    def correct(self, category, text):
        """-> (corrected text, [notes], whole_value_pattern_used)."""
        text = _norm(text)
        if category in _FORMAT_CATEGORIES:
            # Codes are unique per patient: a reading staff once corrected
            # to a code must not stamp that code on another patient - only
            # character fixes and the learned format apply.
            notes = []
            text = self._fix_chars(category, text, notes)
            return self._apply_code_format(category, text, notes), notes, False
        whole = self._best(VALUE, category, text.upper(), text)
        if whole:
            return whole, [f"staff have corrected '{text}' to '{whole}' before"], True
        common = (self._closest_entry(category, VALUE, text, _VALUE_MATCH)
                  if category in _VALUE_ENTRY_CATEGORIES else None)
        if common:
            return common[0], [f"close to a common entry, '{common[0]}' (entered {common[1]} times)"], False

        notes = []
        words, gaps = _words_and_gaps(category, text)
        cores = [_split_edges(word)[1].upper() for word in words]
        previous = ""
        for i, word in enumerate(words):
            before, core, after = _split_edges(word)
            address = category == "ADDRESS"
            fixed = self._best(WORD, category, core.upper(), core) if core else None
            if fixed:
                notes.append(f"'{core}' -> '{fixed}'")
            elif (address and previous == "DAVAO" and core.upper() != "CITY"
                  and _CITY_SHORT.match(core.upper())):
                fixed = _match_case(core, "City")
                notes.append(f"'{core}' -> '{fixed}' (after Davao)")
            elif address and _davao_city(core):
                fixed = _match_case(core, "Davao City")
                notes.append(f"'{core}' -> '{fixed}' (Davao City run together)")
            elif _WORD_RE.match(core):
                # The word just before "Davao" / "DC" is nearly always the
                # barangay, so a looser match is enough there.
                before_city = address and i + 1 < len(cores) and _is_davao(cores[i + 1])
                common = self._closest_entry(category, WORD, core,
                                             _BEFORE_CITY_MATCH if before_city else _WORD_MATCH)
                if common:
                    fixed = _match_case(core, common[0])
                    notes.append(f"'{core}' -> '{fixed}' (common entry)")
                elif category in _VALUE_ENTRY_CATEGORIES:
                    split = self._split_run_together(category, core)
                    if split:
                        fixed = " ".join(_match_case(core, part) for part in split)
                        notes.append(f"'{core}' -> '{fixed}' (two common entries run together)")
            words[i] = before + (fixed or core) + after
            previous = (fixed or core).split(" ")[-1].upper()
        text = "".join(word + gap for word, gap in zip(words, gaps + [""]))

        return self._fix_chars(category, text, notes), notes, False

    def _fix_chars(self, category, text, notes):
        """Letter/digit mix-ups in number and date columns ("O" -> "0")."""
        kind = review_fields.kind_of(category)
        if kind not in _DIGIT_KINDS:
            return text
        chars = []
        for char in text:
            fixed = None
            if char.isalpha() and not (kind == review_fields.DATETIME_KIND and char in _DATETIME_LETTERS):
                fixed = self._best(CHAR, category, char, char)
            if fixed:
                notes.append(f"'{char}' -> '{fixed}'")
            chars.append(fixed or char)
        return "".join(chars)


_CACHED = {"model": None, "at": 0.0}
_CACHE_SECONDS = 300


def fix_saved_reading(category, text):
    """A reading saved before the current rules, with the known fixes
    applied - so scans read earlier get the fixes added since when they are
    opened for checking. Address and diagnosis columns only (names are never
    pre-filled from common entries); the model is rebuilt every few minutes
    to pick up what reviews have taught. Any failure returns the text as is."""
    if not text or category not in _VALUE_ENTRY_CATEGORIES or not config.AI_CORRECTION_ENABLED:
        return text
    try:
        if _CACHED["model"] is None or time.monotonic() - _CACHED["at"] > _CACHE_SECONDS:
            _CACHED["model"], _CACHED["at"] = load_model(), time.monotonic()
        return _CACHED["model"].correct(category, text)[0]
    except Exception:
        logger.exception("Could not apply the known fixes to a saved %s reading", category)
        return text


def load_model():
    """Build the model from the patterns table. The first time the table has
    no learned patterns yet, it is filled from the reviews already in the
    database. Without the table (migration 006 not applied) the model uses
    the built-in starter list + past reviews instead."""
    import case_session_store
    import pattern_store
    try:
        if not pattern_store.has_learned_patterns():
            past = reviewed_patterns(case_session_store.list_reviewed_ocr_fields())
            if past:
                pattern_store.add_patterns(past)
                logger.info("Pattern table filled from %d patterns in past reviews", len(past))
        model = CorrectionModel.from_patterns(pattern_store.load_patterns())
        logger.info("Pattern recognition: %d observations from ocr_correction_patterns", model.examples)
    except Exception:
        logger.exception("ocr_correction_patterns unavailable (run database/migrations/006) - "
                         "using the built-in starter patterns")
        try:
            fields = case_session_store.list_reviewed_ocr_fields()
        except Exception:
            logger.exception("Could not load past reviews")
            fields = []
        model = CorrectionModel.with_starter_knowledge(fields)
    _load_entries(model, case_session_store)
    return model


def _load_entries(model, case_session_store):
    """Add the common entries (ocr_known_entries) to the model. The first
    time, the table is filled from the reviews already in the database."""
    import entry_store
    try:
        if not entry_store.has_review_entries():
            past = reviewed_entries(case_session_store.list_reviewed_ocr_fields())
            if past:
                entry_store.add_entries(past, entry_store.FROM_REVIEWS)
                logger.info("Common entries filled from %d entries in past reviews", len(past))
        rows = entry_store.load_entries()
        model.add_entries(rows)
        logger.info("Common entries: %d known", len(rows))
    except Exception:
        logger.exception("ocr_known_entries unavailable (run database/migrations/007) - "
                         "no common-entry suggestions")


def _changes(new_rows, old_rows, key_size):
    """What a re-submitted review changes: (rows to add, rows to take away),
    comparing count rows on their first key_size columns."""
    new = {tuple(r[:key_size]): r for r in new_rows}
    old = {tuple(r[:key_size]): r for r in old_rows}
    added, removed = [], []
    for key in new.keys() | old.keys():
        n = new[key][-1] if key in new else 0
        o = old[key][-1] if key in old else 0
        row = new.get(key) or old.get(key)
        if n > o:
            added.append((*row[:-1], n - o))
        elif o > n:
            removed.append((*row[:-1], o - n))
    return added, removed


def record_review(fields, previous_fields=None):
    """Teach the pattern and entry tables from a submitted review - every
    time staff confirm a patient. previous_fields: what this session's last
    submission confirmed, when it is being re-submitted; only the
    difference is learned (fixed answers are unlearned, new ones learned),
    so confirming the same patient twice never counts twice. Never raises -
    a failure here must not block saving the review."""
    recorded = 0
    try:
        import pattern_store
        added, removed = _changes(reviewed_patterns(fields), reviewed_patterns(previous_fields or []), 4)
        if added:
            pattern_store.add_patterns(added)
        if removed:
            pattern_store.remove_patterns(removed)
        recorded += len(added) + len(removed)
    except Exception:
        logger.exception("Could not record correction patterns from this review")
    try:
        import entry_store
        added, removed = _changes(reviewed_entries(fields), reviewed_entries(previous_fields or []), 3)
        if added:
            entry_store.add_entries(added, entry_store.FROM_REVIEWS)
        if removed:
            entry_store.remove_review_entries(removed)
        recorded += len(added) + len(removed)
    except Exception:
        logger.exception("Could not record common entries from this review")
    return recorded


def record_form(values):
    """Count the common entries on an exported PhilHealth form
    ({form key: text}). Returns how many were recorded; never raises."""
    try:
        import entry_store
        entries = form_entries(values)
        if entries:
            entry_store.add_entries(entries, entry_store.FROM_FORMS)
        return len(entries)
    except Exception:
        logger.exception("Could not record common entries from a form")
        return 0


# ── Putting it together ───────────────────────────────────────────────────

def wants_second_look(field, flags):
    """Fields PaddleOCR was unsure about and that have writing in them."""
    return (field["status"] in (NEEDS_CHECK, MANUAL)
            and not field.get("ocr_error")
            and not flags.get("blank"))


def apply_reading(field, reading):
    """Record the AI's reading on a field and fill in the best output: the
    AI's reading when it's sure, otherwise its best guess. Never makes a
    field "accepted" - a filled field is at most "needs_check", and a guess
    for a field PaddleOCR couldn't read well is marked best_guess so the
    review screen asks staff to compare it with the picture carefully."""
    field["ai"] = reading
    value = reading["text"] if reading["sure"] else (reading.get("best_guess") or reading["text"])
    if not value:
        return
    field["value"] = value
    if field["status"] == MANUAL:
        field["status"] = NEEDS_CHECK
        field["best_guess"] = not reading["sure"]


def _looks_right(category, text):
    """Number and date columns can't contain stray letters (only AM/PM in
    date-and-time); a reading that still has some is never "sure"."""
    kind = review_fields.kind_of(category)
    if kind not in _DIGIT_KINDS:
        return True
    allowed = _DATETIME_LETTERS if kind == review_fields.DATETIME_KIND else set()
    return not any(c.isalpha() and c not in allowed for c in text)


def assist_field(field, crop, ocr_fn, model, version_tokens=None):
    """The offline AI's reading of one unsure field -> {"text", "sure",
    "note", "model", ...}, or None when there is nothing to suggest."""
    category = field["category"]
    vote = ensemble_read(ocr_fn, crop, field.get("raw_text"), field.get("confidence"), version_tokens)
    if vote is None:
        return None
    text, notes, whole_pattern = model.correct(category, vote["text"])
    agreed = (vote["votes"] >= 2 and vote["confidence"] >= config.OCR_CONFIDENCE_REVIEW
              and _looks_right(category, text))
    if category == "NAME" and any("common entry" in n for n in notes):
        # A rare real name must not be "fixed" into a common one unseen.
        agreed = whole_pattern = False
    note_parts = [f"{vote['votes']} of {vote['readings']} PaddleOCR readings agreed"]
    if notes:
        note_parts.append("known patterns: " + ", ".join(notes))
    # Best output when the AI isn't sure: PaddleOCR's full reading with the
    # known fixes applied - the vote can pick a shorter, partial reading.
    raw = _norm(field.get("raw_text"))
    best_guess = model.correct(category, raw)[0] if raw else text
    return {
        "text": text,
        "sure": bool(text) and (agreed or whole_pattern),
        "best_guess": best_guess,
        "note": "; ".join(note_parts),
        "model": MODEL_NAME,
        "votes": vote["votes"],
        "readings": vote["readings"],
        "learned_fixes": notes,
    }


# Fields whose versions are read in one batch (make_corrector): big enough
# for batching to pay off, small enough for the progress bar to keep moving.
_BATCH_FIELDS = 12


def make_corrector(ocr_fn, model=None, batch_reader=None):
    """A corrector for logbook_pipeline.build_review_rows(corrector=...), or
    None when the AI is switched off (AI_CORRECTION_ENABLED=false).

    batch_reader: ocr_engine.read_versions_many - reads every version of a
    group of fields in one batch, about twice as fast as reading each
    version with ocr_fn (same accuracy on the fake-data scan: 0.335 vs 0.340
    character errors). Without it, or if a batch fails, each version is read
    with ocr_fn."""
    if not config.AI_CORRECTION_ENABLED:
        return None

    def read_ahead(group):
        if batch_reader is None:
            return [None] * len(group)
        try:
            return batch_reader([(crop, versions(crop)) for _, crop in group])
        except Exception:
            logger.exception("Batch reading failed; reading these fields one version at a time")
            return [None] * len(group)

    def correct_fields(candidates, progress=None):
        candidates = candidates[:config.AI_CORRECTION_MAX_FIELDS]
        if not candidates:
            return 0
        active = model or load_model()
        done = 0
        ahead = []
        for index, (field, crop) in enumerate(candidates):
            if progress:
                progress(f"Double-checking hard-to-read entries ({index + 1} of {len(candidates)})",
                         index / len(candidates))
            if index % _BATCH_FIELDS == 0:
                ahead = read_ahead(candidates[index:index + _BATCH_FIELDS])
            try:
                reading = assist_field(field, crop, ocr_fn, active, ahead[index % _BATCH_FIELDS])
            except Exception:
                logger.exception("Offline AI failed on %s", field.get("category"))
                continue
            if reading is not None:
                apply_reading(field, reading)
                done += 1
        logger.info("Offline AI: %d of %d unclear fields re-read", done, len(candidates))
        return done

    return correct_fields
