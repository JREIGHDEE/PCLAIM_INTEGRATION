"""The discharge (final) diagnosis worked out from the admission
(PClaimAssist/js/app.js dischargeFromAdmission / dischargeForVisit),
against the clinic's logbook as the research answer key writes it: the
kind of visit decides the wording, not the admission's words.

The functions are cut out of app.js and run under Node, so the test is of
the code the forms use. Skipped where Node is not installed (like the
database tests without MariaDB).
"""
import json
import os
import shutil
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (admission diagnosis, final diagnosis) - from research_tests/inputs/answer_key.xlsx.
ANSWER_KEY = [
    ("FOR WELL BABY CARE", "WELL BABY CARE"),
    ("FOR POSTPARTUM VISIT", "POSTPARTUM VISIT"),
    ("FOR POST PARTUM VISIT", "POSTPARTUM VISIT"),
    ("FOR POSTPARTUM VISIT & PSI INJECTION", "POSTPARTUM VISIT & FAMILY PLANNING (PSI)"),
    ("FOR POSTPARTUM VISIT & PSI INSERTION", "POSTPARTUM VISIT & FAMILY PLANNING (PSI)"),
    ("FOR PSI INSERTION", "FAMILY PLANNING"),
    ("FOR PSI REMOVAL", "FAMILY PLANNING"),
    ("FOR PSI", "FAMILY PLANNING"),
    ("FOR CIC", "FAMILY PLANNING"),
    ("FOR CIC & PSI REMOVAL", "FAMILY PLANNING"),
    ("FOR DMPA INJECTION", "FAMILY PLANNING"),
    ("FOR IUD INSERTION", "FAMILY PLANNING"),
    ("FOR PILLS REFILL", "FAMILY PLANNING"),
    ("FOR FP COUNSELING", "FAMILY PLANNING"),
    ("FOR PAPSMEAR", "FAMILY PLANNING"),
    ("FOR INSERTION OF IMPLANTABLE SUBDERMAL CONTRACEPTIVE", "FAMILY PLANNING"),
    ("G2P1 (1001) PU 13 4/7 WKS AOG", "PRENATAL CHECK-UP"),
    ("G1P0 (0000) PU 8 6/7 WKS AOG", "PRENATAL CHECK-UP"),
    ("G3P3 (3003) PU PT 38 4/7 WKS AOG", "PRENATAL CHECK-UP"),
    ("PREGNANCY UTERINE PRENATAL CARE 20 WEEKS AOG, GRAVIDA 2 PARA 1 (1001)", "PRENATAL CHECK-UP"),
    ("FOR BCG & HEARING TEST", "BCG & HEARING TEST"),
]
# A delivery's and a newborn's final diagnosis is their own wording
# (js/dx-templates.js): only the "FOR" would go.
OWN_WORDING = [
    "G2P1 (1001) PUFT 39 WKS AOG CEPHALIC IN LABOR",
    "LIVE TERM BABY GIRL AGA DELIVERED VIA NSVD TO A G3P3 MOTHER W/ AS OF 8,9",
]


def _functions():
    with open(os.path.join(ROOT, "PClaimAssist", "js", "app.js"), encoding="utf-8") as handle:
        src = handle.read()
    start = src.index("const DX_FAMILY_PLANNING")
    end = src.index("\n}\n", src.index("function dischargeForVisit")) + 3
    return src[start:end]


def _run(expression_per_case, cases):
    js = (_functions() + "\nconst cases = " + json.dumps(cases) + ";\n"
          + "console.log(JSON.stringify(cases.map(c => " + expression_per_case + ")));")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True, timeout=60)
    return json.loads(out.stdout)


def _rule(path):
    """The DX_FAMILY_PLANNING + dischargeFromAdmission text in a file."""
    with open(path, encoding="utf-8") as handle:
        src = handle.read()
    start = src.index("const DX_FAMILY_PLANNING")
    return src[start:src.index("\n}\n", src.index("function dischargeFromAdmission", start)) + 3]


class SameRuleOnBothPagesTests(unittest.TestCase):
    def test_review_page_has_the_forms_rule(self):
        # The Logbook Reader's review fills the final diagnosis too: the
        # same wording, or a claim's discharge depends on where it was typed.
        self.assertEqual(_rule(os.path.join(ROOT, "Ocr_module", "templates", "review.html")),
                         _rule(os.path.join(ROOT, "PClaimAssist", "js", "app.js")))


@unittest.skipUnless(shutil.which("node"), "Node is not installed")
class DischargeWordingTests(unittest.TestCase):
    def test_each_kind_of_visit_gets_the_clinics_wording(self):
        got = _run("dischargeFromAdmission(c)", [a for a, _ in ANSWER_KEY])
        for (admission, final), result in zip(ANSWER_KEY, got):
            self.assertEqual(result, final, admission)

    def test_delivery_and_newborn_keep_their_own_words(self):
        self.assertEqual(_run("dischargeFromAdmission(c)", OWN_WORDING), OWN_WORDING)

    def test_the_fullest_wording_of_the_visit_wins(self):
        # The postpartum package's sentence lost the PSI the logbook wrote.
        got = _run("dischargeForVisit(c)", [
            {"admissionDx": "POSTPARTUM VISITS AFTER DISCHARGE.",
             "chiefComplaint": "FOR POSTPARTUM VISIT & PSI INSERTION"},
            {"admissionDx": "FOR WELL BABY CARE", "chiefComplaint": "WELL BABY CARE"},
        ])
        self.assertEqual(got, ["POSTPARTUM VISIT & FAMILY PLANNING (PSI)", "WELL BABY CARE"])


if __name__ == "__main__":
    unittest.main()
