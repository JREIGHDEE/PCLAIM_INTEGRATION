"""
Character Error Rate (CER) and Word Error Rate (WER) against manually
verified ground truth.

Both are the standard edit-distance definition:

    error_rate = levenshtein_distance(reference, hypothesis) / len(reference)

No ground truth is fabricated or bundled here - these functions only ever
score whatever reference text is handed to them (see
compare_ocr_engines.py's --ground-truth option and benchmarks/README.md for
the expected CSV format). No extra dependency (e.g. jiwer) is required; the
edit-distance implementation below is a plain O(n*m) dynamic-programming
Levenshtein distance, adequate for page-length OCR text.

Whitespace normalization
-------------------------
Before scoring, both the reference and the hypothesis have all runs of
whitespace (spaces, tabs, newlines) collapsed to a single space, and are
trimmed at both ends. This exists purely to cancel out a benchmark
artifact: PaddleOCR's regions are line/phrase-level while Tesseract's are
word-level, so extracted_text joins each engine's own regions with "\n" at
different granularity even when both engines recognized the exact same
words correctly. Without normalization, "Juan\nDela\nCruz" (Tesseract-style,
one region per word) and "Juan Dela Cruz" (Paddle-style, one region for the
whole line) would score as different text purely because of how many
regions each engine happened to split the line into - not because either
engine actually read anything differently. Collapsing whitespace before
diffing makes both forms equivalent for CER/WER, while leaving every other
character exactly as recognized.

Nothing else is normalized: no lowercasing, no punctuation removal, no
digit normalization, no spelling correction. Case and punctuation
differences are real potential OCR errors and are scored as such.

Accuracy percentage (matching Nazeem et al., 2024)
----------------------------------------------------
word_accuracy_percent()/character_accuracy_percent() report accuracy the
same way Nazeem, R, S, & R. R (2024, ICON - see benchmarks/README.md's
"Related literature" section) report it in their Table I: as a percentage
derived from `1 - error_rate`, using the identical WER/CER formulas above.
This is what makes a number like "92%" directly comparable to their
published figures, rather than a differently-defined "confidence."
"""
import re

_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_whitespace(text):
    """Collapse all whitespace runs to a single space; trim both ends.

    Applied identically to reference and hypothesis - see module docstring.
    Does not touch case, punctuation, digits, or any other character.
    """
    return _WHITESPACE_RUN.sub(" ", text or "").strip()


def _levenshtein(a, b):
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, item_a in enumerate(a, start=1):
        current_row = [i] + [0] * len(b)
        for j, item_b in enumerate(b, start=1):
            cost = 0 if item_a == item_b else 1
            current_row[j] = min(
                previous_row[j] + 1,      # deletion
                current_row[j - 1] + 1,   # insertion
                previous_row[j - 1] + cost,  # substitution
            )
        previous_row = current_row
    return previous_row[-1]


def character_error_rate(reference, hypothesis):
    """CER at the character level, after whitespace normalization.

    Returns None if the normalized reference is empty (undefined).
    """
    ref_norm = normalize_whitespace(reference)
    hyp_norm = normalize_whitespace(hypothesis)
    ref_chars = list(ref_norm)
    if not ref_chars:
        return None
    distance = _levenshtein(ref_chars, list(hyp_norm))
    return distance / len(ref_chars)


def word_error_rate(reference, hypothesis):
    """WER at the whitespace-tokenized word level, after whitespace normalization.

    Returns None if the normalized reference has no words (undefined).
    Note: whitespace normalization does not change WER's numeric result on
    its own (str.split() already treats any whitespace run as one word
    separator), but it's applied for the same documented reasoning as CER
    and so both metrics are computed from the same normalized text.
    """
    ref_norm = normalize_whitespace(reference)
    hyp_norm = normalize_whitespace(hypothesis)
    ref_words = ref_norm.split()
    if not ref_words:
        return None
    distance = _levenshtein(ref_words, hyp_norm.split())
    return distance / len(ref_words)


def character_accuracy_percent(reference, hypothesis):
    """Character-level accuracy as a percentage: 100 * (1 - CER).

    Same formulation as Nazeem et al. (2024) - see module docstring.
    Clamped to [0, 100]: CER can exceed 1.0 when the hypothesis has many
    more characters inserted than the reference has characters, which
    would otherwise produce a negative "accuracy" - not meaningful on a
    0-100% scale, and the cited paper's own figures are all within [0, 100].
    Returns None if CER is undefined (empty reference).
    """
    cer = character_error_rate(reference, hypothesis)
    if cer is None:
        return None
    return max(0.0, min(100.0, (1 - cer) * 100))


def word_accuracy_percent(reference, hypothesis):
    """Word-level accuracy as a percentage: 100 * (1 - WER).

    Same formulation as Nazeem et al. (2024) - see module docstring and
    character_accuracy_percent() for the clamping rationale.
    Returns None if WER is undefined (empty reference).
    """
    wer = word_error_rate(reference, hypothesis)
    if wer is None:
        return None
    return max(0.0, min(100.0, (1 - wer) * 100))
