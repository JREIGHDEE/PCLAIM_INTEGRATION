"""Small statistics helpers (no numpy needed for these)."""
import statistics


def _numbers(values):
    return [float(v) for v in values if v is not None and v != ""]


def mean(values):
    values = _numbers(values)
    return round(sum(values) / len(values), 2) if values else None


def median(values):
    values = _numbers(values)
    return round(statistics.median(values), 2) if values else None


def low(values):
    values = _numbers(values)
    return round(min(values), 2) if values else None


def high(values):
    values = _numbers(values)
    return round(max(values), 2) if values else None


def value_range(values):
    """"min - max" as text, for a summary table."""
    values = _numbers(values)
    return f"{min(values):.2f} - {max(values):.2f}" if values else ""


def percent(part, whole):
    return round(100.0 * part / whole, 2) if whole else None


def ratio(part, whole):
    return round(part / whole, 4) if whole else None


def f1(precision, recall):
    if not precision or not recall:
        return 0.0 if precision is not None and recall is not None else None
    return round(2 * precision * recall / (precision + recall), 4)
