"""Every test, then the combined workbook.

    python -m research_tests.run_all [--samples] [--skip performance,handwriting]

Order: user sessions, image quality, field mapping, validation, handwriting,
correction metrics (uses the handwriting results), performance, RTH mistakes,
results.
A test that fails is reported and the rest still run.
"""
import importlib
import traceback

from research_tests.registry import BY_KEY

ORDER = ["user_sessions", "iq_check", "field_mapping", "validation", "handwriting", "correction_metrics",
         "performance", "rth_errors"]
NO_SAMPLES = {"correction_metrics"}


def run(progress, samples=False, skip=None):
    skipped = {s.strip() for s in (skip or "").split(",") if s.strip()}
    todo = [k for k in ORDER if k not in skipped]
    outputs, headline = [], []
    for n, key in enumerate(todo):
        module = importlib.import_module(f"research_tests.{key}")
        base, width = n / (len(todo) + 1), 1 / (len(todo) + 1)
        sub = lambda f, m, b=base, w=width, k=key: progress(b + w * f, f"{BY_KEY[k]['tab']}: {m}")
        try:
            options = {} if key in NO_SAMPLES else {"samples": samples}
            result = module.run(sub, **options)
            outputs += result.get("outputs", [])
            headline.append([BY_KEY[key]["tab"], "done"])
        except Exception as exc:
            traceback.print_exc()
            headline.append([BY_KEY[key]["tab"], f"FAILED: {type(exc).__name__}: {exc}"])
    from research_tests import results
    outputs += results.run(lambda f, m: progress(len(todo) / (len(todo) + 1) + f / (len(todo) + 1), m))["outputs"]
    return {"outputs": outputs, "headline": headline}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the computer-drawn sample inputs")
    parser.add_argument("--skip", help="tests to leave out, e.g. performance,handwriting")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main("run_all", run, __doc__.splitlines()[0], add_arguments)
