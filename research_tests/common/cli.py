"""Command line for every test: python -m research_tests.<test> [options].

Each test module has run(progress, **options) -> {"outputs": [paths],
"headline": [[label, value], ...]} and calls main() under __main__.
"""
import argparse
import logging
import sys
import traceback

from research_tests.common.progress import Progress


def main(test_key, run, description, add_arguments=None, argv=None):
    from research_tests import guard
    guard.isolate()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("ppocr", "paddle", "PIL"):
        logging.getLogger(noisy).setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(prog=f"python -m research_tests.{test_key}", description=description)
    if add_arguments:
        add_arguments(parser)
    options = vars(parser.parse_args(argv))
    progress = Progress(test_key)
    try:
        result = run(progress, **options)
    except Exception as exc:
        traceback.print_exc()
        progress.fail(f"{type(exc).__name__}: {exc}")
        sys.exit(1)
    progress.done(result.get("outputs", []), result.get("headline"))
    for label, value in result.get("headline") or []:
        print(f"  {label}: {value}")
    return result
