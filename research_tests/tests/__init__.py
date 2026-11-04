"""Unit tests of the research tests themselves (not part of the main
suite's 266+). Run from the repository root:

    Ocr_module\\venv\\Scripts\\python.exe -m unittest discover -s research_tests/tests -t .
"""
from research_tests import guard

guard.isolate()
