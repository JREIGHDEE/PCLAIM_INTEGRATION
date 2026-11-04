"""Admission patterns: what the logbook's admitting diagnosis says, as the
clinic's reason for admission.

The logbook writes a handful of admissions over and over ("CEPHALIC IN
LABOR", "POST PARTUM VISIT", "WELL BABY CARE", "FOR PSI INSERTION"...), and
PaddleOCR misreads the handwriting in ways that still show them: "WEZL AISY
CARE", "FOR POJT PAKTUM UISIT". Each pattern (admission_patterns table,
migration 012; admission_pattern_store.py) has

  name      what staff call it ("Postpartum visit")
  clues     words that give it away, matched letter by letter, so a few
            misread letters still match
  reason    the clinic's wording for Chief Complaint / Reason for Admission
  package   the PhilHealth package it means (js/dx-templates.js
            DX_PACKAGES keys), or "" for none
  examples  readings staff confirmed as this pattern (learned from the
            card under Reason for admission): a reading seen before is
            recognised however badly it is misread

Pure: no database, no Flask. apply_suggestion() puts the best pattern's
reason into a claim's form data (routes/claims_routes.py form-data),
tagged "please check", with what it matched so staff can correct it.
"""
import difflib
import re

# Seeded by migration 012 too; used as they are while it has not been run.
DEFAULT_PATTERNS = [
    {"name": "Labor (delivery)", "package": "NSDBF", "reason": "LABOR PAINS",
     "clues": ["CEPHALIC IN LABOR", "IN LABOR", "CEPHALIC", "LABOR PAINS", "IN ACTIVE LABOR"]},
    {"name": "Newborn (delivered here)", "package": "NCP", "reason": "NEWBORN CARE",
     "clues": ["LIVE TERM BABY", "TERM BABY BOY", "TERM BABY GIRL", "DELIVERED VIA NSVD TO A", "MOTHER WEIGHING"]},
    {"name": "Well baby care", "package": "NCP", "reason": "WELL BABY CARE",
     "clues": ["WELL BABY CARE", "WELL BABY"]},
    {"name": "Postpartum visit", "package": "PPC01", "reason": "POSTPARTUM VISIT",
     "clues": ["POSTPARTUM VISIT", "POST PARTUM VISIT", "POSTPARTUM"]},
    {"name": "Prenatal check-up", "package": "ANV", "reason": "PRENATAL CHECK-UP",
     "clues": ["PRENATAL CHECK UP", "PRENATAL CHECKUP", "PRENATAL"]},
    {"name": "Implant insertion (PSI)", "package": "FP001", "reason": "FOR PSI INSERTION",
     "clues": ["PSI INSERTION", "PSI", "IMPLANT INSERTION", "SUBDERMAL IMPLANT"]},
    {"name": "Implant removal (PSI)", "package": "", "reason": "FOR PSI REMOVAL",
     "clues": ["PSI REMOVAL", "PSI REMOV", "IMPLANT REMOVAL"]},
    {"name": "IUD insertion", "package": "IUD", "reason": "FOR IUD INSERTION",
     "clues": ["IUD INSERTION", "IUD", "INTRAUTERINE DEVICE"]},
    {"name": "Injectable (DMPA)", "package": "", "reason": "FOR DMPA INJECTION",
     "clues": ["DMPA INJECTION", "DMPA INSERTION", "DMPA"]},
    {"name": "Injectable (CIC)", "package": "", "reason": "FOR CIC INJECTION",
     "clues": ["CIC"]},
    {"name": "Pills refill", "package": "", "reason": "FOR PILLS REFILL",
     "clues": ["PILLS REFILL", "REFILL"]},
    {"name": "Family planning", "package": "", "reason": "FAMILY PLANNING",
     "clues": ["FAMILY PLANNING"]},
    {"name": "Family planning counseling", "package": "", "reason": "FAMILY PLANNING COUNSELING",
     "clues": ["COUNSELING", "FP COUNSELING"]},
    {"name": "Newborn screening / hearing test", "package": "", "reason": "NEWBORN HEARING TEST",
     "clues": ["HEARING TEST", "NEWBORN SCREENING", "BCG"]},
]

# A pattern is suggested from this score up (0-1, how closely its best clue
# or example matches part of the reading). Calibrated on the scans' misreads
# (test_admission_patterns.py).
SUGGEST_FROM = 0.7
# Other patterns this close are offered as "or was it...".
ALTERNATIVE_FROM = 0.5
# Clues shorter than this are only taken letter for letter (DMPA, PSI): a
# short word matches too much of anything with a letter or two wrong.
_EXACT_ONLY_BELOW = 5
_MAX_EXAMPLES = 30

# Letters PaddleOCR mistakes for one another in handwriting, folded the same
# way on both sides before comparing: "UISIT" is VISIT, "B0Y" is BOY.
_FOLD = str.maketrans({"V": "U", "0": "O", "Q": "O", "1": "I", "5": "S", "6": "G", "8": "B"})


def normalize(text):
    """Capitals and single spaces, anything but letters and digits a space."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", str(text or "").upper())).strip()


def _squash(text):
    return normalize(text).replace(" ", "").translate(_FOLD)


def clue_score(clue, text):
    """How well `clue` matches some part of `text`: 1.0 when it is there
    letter for letter, else the best likeness of any stretch of the reading
    about as long as the clue."""
    c, t = _squash(clue), _squash(text)
    if not c or not t:
        return 0.0
    short = len(normalize(clue).replace(" ", "")) < _EXACT_ONLY_BELOW
    if c in t:
        # A short word found is less sure than a long one: "PSI" in
        # "FOR PSI REMOVAL" gives way to "PSI REMOV".
        return 0.9 if short else 1.0
    if short:
        return 0.0
    best = 0.0
    matcher = difflib.SequenceMatcher(autojunk=False)
    matcher.set_seq2(c)
    for size in range(max(1, len(c) - 2), len(c) + 3):
        for start in range(0, max(1, len(t) - size + 1)):
            matcher.set_seq1(t[start:start + size])
            if matcher.real_quick_ratio() <= best or matcher.quick_ratio() <= best:
                continue
            best = max(best, matcher.ratio())
    return best


def example_score(example, text):
    """A reading staff confirmed before, against this one, whole."""
    a, b = _squash(example), _squash(text)
    if not a or not b:
        return 0.0
    return 1.0 if a == b else difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def pattern_score(pattern, text):
    """(score, why): the best clue or example, and which it was."""
    best, why = 0.0, ""
    for clue in pattern.get("clues") or []:
        score = clue_score(clue, text)
        # A longer clue matched is surer than a short one: "POSTPARTUM VISIT"
        # over "POSTPARTUM" when both are there.
        score -= 0.001 * max(0, 30 - len(_squash(clue)))
        if score > best:
            best, why = score, f'looks like "{normalize(clue)}"'
    for example in pattern.get("examples") or []:
        score = example_score(example, text)
        if score >= 0.85 and score + 0.01 > best:
            best, why = min(1.0, score + 0.01), "read like this before"
    return max(0.0, best), why


def rank(text, patterns):
    """Every active pattern against one reading, best first:
    [{"id", "name", "reason", "package", "score", "why"}]."""
    out = []
    for pattern in patterns:
        if pattern.get("is_active") is False or pattern.get("is_active") == 0:
            continue
        score, why = pattern_score(pattern, text)
        out.append({"id": pattern.get("id"), "name": pattern["name"], "reason": pattern["reason"],
                    "package": pattern.get("package") or "", "score": round(score, 3), "why": why})
    return sorted(out, key=lambda r: r["score"], reverse=True)


def suggest(readings, patterns):
    """The best pattern for the first reading that has one (the admitting
    diagnosis, then the final diagnosis): {"pattern": ranked row, "reading",
    "alternatives": [ranked rows]}, or None when nothing is close enough."""
    best = None
    for reading in readings:
        if not normalize(reading):
            continue
        ranked = rank(reading, patterns)
        if ranked and ranked[0]["score"] >= SUGGEST_FROM and (best is None or ranked[0]["score"] > best[0][0]["score"]):
            best = (ranked, reading)
        if best:
            break
    if not best:
        return None
    ranked, reading = best
    return {"pattern": ranked[0], "reading": reading,
            "alternatives": [r for r in ranked[1:4] if r["score"] >= ALTERNATIVE_FROM]}


def add_example(examples, reading):
    """examples with `reading` added (normalised, once, newest kept)."""
    reading = normalize(reading)[:191]
    kept = [e for e in (examples or []) if normalize(e) != reading]
    return ([reading] + kept)[:_MAX_EXAMPLES] if reading else kept


def drop_example(examples, reading):
    reading = normalize(reading)
    return [e for e in (examples or []) if normalize(e) != reading]


def apply_suggestion(prefill, patterns):
    """form_prefill.build_form_data()'s result, with the reason for
    admission suggested from the logbook's admitting (else final)
    diagnosis: put in when Chief Complaint is empty, tagged "please check",
    and described in prefill["admission_suggestion"] for the card on
    Patient details. Only for diagnoses read from the logbook."""
    data, fields = prefill.get("data") or {}, prefill.get("fields") or {}
    readings = [data.get(key) for key in ("admissionDx", "dischargeDx") if key in fields and data.get(key)]
    found = suggest(readings, patterns)
    if not found:
        return prefill
    pattern = found["pattern"]
    filled = not str(data.get("chiefComplaint") or "").strip()
    if filled:
        data["chiefComplaint"] = pattern["reason"]
        fields["chiefComplaint"] = {
            "status": "needs_check", "category": "ADMITTING DIAGNOSIS", "raw_text": found["reading"],
            "confidence": pattern["score"],
            "reason": f'Suggested from the logbook\'s "{found["reading"]}" ({pattern["name"]}, '
                      f'{pattern["why"]}) - check it',
        }
    prefill["admission_suggestion"] = {**found, "filled": filled}
    return prefill
