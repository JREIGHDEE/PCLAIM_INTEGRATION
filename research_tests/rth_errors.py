"""Test 8 - documentation errors that cause return-to-hospital (RTH): planted
mistakes, manual vs PClaimAssist (supplementary to Eq. 3.12).

    python -m research_tests.rth_errors [--samples] [--only D1,N1]

The mistakes come from the clinic's own list of common RTH reasons
(inputs/rth_mistakes.csv: dates, names, gravida and baby details, PIN,
admission reason, clinical details and examinations), not from the
validation rules, so a mistake the system cannot stop is reported as such.

Each mistake is planted in every test patient (answer key R01-R20) it
applies to, on the real forms page (PClaimAssist/index.html, offline, as in
the validation test), the way staff would make it:

  dual entry   the value is typed on one form (the first copy), then typed
               differently on another form's box (the second copy);
  typed once   the wrong value is typed once, where staff type it;
  baby claim   the baby's claim is given a value that differs from the
               mother's claim.

Outcome of each planted mistake in PClaimAssist:
  Prevented     the second copy cannot differ: the form's box is locked and
                filled from Patient details, or typing in it changes every
                form, or the page does not keep the value;
  Blocked       a critical rule fires, so "Save as PDF" refuses
                (runValidationRules canGeneratePDF = false);
  Warned        a warning fires, the PDF can still be saved;
  Gets through  the mistake is in the claim and nothing notices.
Mistakes on items printed on one form only (no second copy on the forms)
are listed, not counted.

Manual: each form is typed separately and nothing checks it, so every
planted mistake stays in the claim (manual errors = planted mistakes).

  error reduction % = (manual errors - PClaimAssist errors) / manual errors x 100
    strict:          PClaimAssist errors = Warned + Gets through
    with warnings:   PClaimAssist errors = Gets through
  per RTH reason, over all planted mistakes, and weighted by how common the
  clinic says each reason is (very common 4, common 3, slightly uncommon 2,
  uncommon 1).

This measures whether the system stops a mistake once it is made, not how
often staff make mistakes: it supplements, and does not replace, Eq. 3.12
from the user sessions (test 7).
"""
import csv
import re
import shutil
from datetime import date, timedelta

from research_tests import INPUTS, output_dir
from research_tests.common import answer_key, excel, stats

TEST_KEY = "rth_errors"
TITLE = "RTH documentation errors (planted mistakes)"
MISTAKES = INPUTS / "rth_mistakes.csv"
WEIGHTS = {"very common": 4, "common": 3, "slightly uncommon": 2, "uncommon": 1}
OUTCOMES = ["Prevented", "Blocked", "Warned", "Gets through"]
GOOD_OCR = {"active": True, "imageQualityPass": True, "pendingSuggestions": 0}
ALL_SIGNED = {"active": True, "member": True, "midwife": True, "hciRep": True, "employer": True,
              "hciAssist": True, "cf4Provider": True, "thumbmark": False}
# The mothers of the newborns in the answer key (same surname, same delivery).
MOTHER_OF = {"R05": "R01", "R07": "R03"}

TYPE_JS = """([form, key, value]) => {
    if (typeof navigateTo === 'function') navigateTo(form, {skipHash: true});
    const s = document.getElementById('section-' + form);
    if (!s) return {status: 'no form'};
    const inputs = [...s.querySelectorAll(`[data-autofill="${key}"]`)]
        .filter(e => /^(INPUT|TEXTAREA|SELECT)$/.test(e.tagName));
    const boxes = [...s.querySelectorAll(`.pca-box-group[data-box-key="${key}"] .pca-box`)];
    const all = inputs.concat(boxes);
    if (!all.length) return {status: 'no box'};
    if (all.every(e => e.readOnly || e.disabled)) return {status: 'locked', title: all[0].title || ''};
    const el = inputs.find(e => !e.readOnly && !e.disabled);
    if (!el) return {status: 'boxes only'};
    el.focus();
    el.value = value;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    el.blur();
    return {status: 'typed'};
}"""
PRINTED_ON_JS = """keys => Object.fromEntries(keys.map(k => [k, Object.keys(OVERLAY_MAP).filter(form =>
    (OVERLAY_MAP[form] || []).some(f => f.key === k || f.digitKey === k || f.computed === k))]))"""


# ── values ─────────────────────────────────────────────────────────────

def _iso(text):
    """'08-29-2026' (as getComputedValue gives it) or ISO -> ISO."""
    text = str(text or "").strip()
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", text)
    return f"{m[3]}-{m[1]}-{m[2]}" if m else text


def _shift(iso, days):
    return (date.fromisoformat(_iso(iso)) + timedelta(days=days)).isoformat() if iso else None


def _other_letter(word):
    """One letter changed (the last letter that has a neighbour)."""
    for i in range(len(word) - 1, -1, -1):
        if word[i].isalpha():
            c = "S" if word[i] == "Z" else chr(ord(word[i]) + 1) if word[i] < "Z" else "A"
            return word[:i] + c + word[i + 1:]
    return None


def _pin_digit(pin):
    digits = [i for i, ch in enumerate(pin) if ch.isdigit()]
    if len(digits) < 6:
        return None
    i = digits[5]
    return pin[:i] + str((int(pin[i]) + 1) % 10) + pin[i + 1:]


def _pin_swap(pin):
    digits = [i for i, ch in enumerate(pin) if ch.isdigit()]
    for a, b in zip(digits[3:], digits[4:]):
        if b == a + 1 and pin[a] != pin[b]:
            return pin[:a] + pin[b] + pin[a] + pin[b + 1:]
    return None


def _pin_11(pin):
    digits = "".join(ch for ch in pin or "" if ch.isdigit())
    return f"{digits[:2]}-{digits[2:10]}-{digits[10:11]}" if len(digits) == 12 else None


def _swap_day_month(iso):
    iso = _iso(iso)
    if not iso:
        return None
    y, m, d = iso.split("-")
    if int(d) > 12 or d == m:
        return None
    return f"{y}-{d}-{m}"


def _year_plus(iso):
    iso = _iso(iso)
    return f"{int(iso[:4]) + 1}{iso[4:]}" if iso else None


GP = re.compile(r"\bG(?:RAVIDA)?\s*(\d{1,2})\s*,?\s*P(?:ARA)?\s*(\d{1,2})\b")


def gravida_of(text):
    m = GP.search(str(text or "").upper())
    return m[1] if m else None


def para_of(text):
    m = GP.search(str(text or "").upper())
    return m[2] if m else None


def delivery_mode(text):
    t = str(text or "").upper()
    if re.search(r"CESAREAN|CAESAREAN|\bLTCS\b|\bCS\b", t):
        return "CESAREAN"
    if re.search(r"NSVD|NSD\b|SPONTANEOUS VERTEX|NORMAL SPONTANEOUS|VAGINAL", t):
        return "VAGINAL"
    return None


def _same(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().upper()


EXTRACT = {"text": _same, "date": _iso, "gravida": gravida_of, "para": para_of, "mode": delivery_mode,
           "int": lambda v: str(int(v)) if str(v or "").strip().isdigit() else _same(v)}


def _aog_weeks(text):
    m = re.search(r"(\d{2})\s*(?:\d/7)?\s*(?:WKS|WEEKS)\s*AOG", str(text or "").upper())
    return int(m[1]) if m else None


def _replace_gp(text, g=None, p=None):
    def sub(m):
        return f"G{g or m[1]}P{p or m[2]}"
    return GP.sub(sub, str(text or "").upper(), count=1)


# ── the probes, one per mistake ID of rth_mistakes.csv ────────────────
# dual(target, wrong, views, source, setup): type `source` value on the
#   first form (the first copy), then `wrong` on the target form's box.
# once(changes): the wrong value typed once (state.data, as Patient details
#   and the form boxes set it), `typed_on` says where.
# baby(field): the baby's claim differs from the mother's.
# single(keys): printed on one form only - listed, not counted.

def dual(targets, key, wrong, views, setup=None, needs=()):
    return {"kind": "dual", "targets": targets, "key": key, "wrong": wrong, "views": views, "setup": setup,
            "needs": set(needs)}


def once(changes, typed_on="Patient details", needs=(), check=None):
    return {"kind": "once", "changes": changes, "typed_on": typed_on, "needs": set(needs), "check": check}


def baby(field, needs=()):
    return {"kind": "baby", "field": field, "needs": {"baby"} | set(needs)}


def single(keys, why):
    return {"kind": "single", "keys": keys, "why": why, "needs": set()}


def _name_views(key):
    return [(f, key, "text") for f in ("csf", "cf1", "cf2", "cf4", "pmrf")]


PROBES = {
    "D1": dual(["cf2"], "dateAdmitted", lambda d: _shift(d["dateAdmitted"], -1),
               [(f, "dateAdmitted", "date") for f in ("csf", "cf2", "cf4")]),
    "D2": dual(["cf4", "cf2"], "dateDischarge", lambda d: _shift(d["dateDischarge"], 1),
               [(f, "dateDischarge", "date") for f in ("csf", "cf2", "cf4")]),
    "D3": dual(["cf1"], "patientDOB", lambda d: _year_plus(d["patientDOB"]),
               [(f, "patientDOB", "date") for f in ("csf", "cf1", "pmrf")]),
    "D4": once(lambda d: {"patientDOB": _swap_day_month(d["patientDOB"])} if _swap_day_month(d["patientDOB"])
               else None),
    "D5": once(lambda d: {"dateDischarge": _shift(d["dateAdmitted"], -2)}),
    "D6": once(lambda d: {"deliveryDate": _shift(d["dateDischarge"], 4)}, needs={"delivery"}),
    "G1": dual(["cf4"], "gravida", lambda d: str(int(d["gravida"]) + 1) if str(d.get("gravida")).isdigit() else None,
               [("cf4", "gravida", "int"), ("cf2", "admissionDx", "gravida"), ("cf4", "admissionDx", "gravida")],
               needs={"delivery"}),
    "G2": dual(["cf4"], "para", lambda d: str(int(d["para"]) + 2) if str(d.get("para")).isdigit() else None,
               [("cf4", "para", "int"), ("cf2", "admissionDx", "para"), ("cf4", "admissionDx", "para")],
               needs={"delivery"}),
    "G3": baby("gravida/para"),
    "G4": baby("birth date"),
    "G5": baby("sex"),
    "P1": dual(["cf1"], "memberPIN", lambda d: _pin_digit(d["memberPIN"]),
               [(f, "memberPIN", "text") for f in ("csf", "cf1", "cf4", "pmrf")]),
    "P2": dual(["pmrf", "cf4", "cf1"], "memberPIN", lambda d: _pin_swap(d["memberPIN"]),
               [(f, "memberPIN", "text") for f in ("csf", "cf1", "cf4", "pmrf")]),
    "P3": once(lambda d: ({"memberPIN": _pin_11(d["memberPIN"])}
                          | ({"patientPIN": _pin_11(d["memberPIN"])} if d.get("memberIsPatient") else {}))
               if _pin_11(d["memberPIN"]) else None),
    "A1": dual(["cf4"], "admissionDx", lambda d: "PREGNANCY UTERINE PRENATAL CARE",
               [("cf2", "admissionDx", "text"), ("cf4", "admissionDx", "text")]),
    "A2": once(lambda d: {"cf4ChiefComplaint": "FEVER AND COUGH"}, typed_on="CF4", needs={"delivery", "cf4"}),
    "A3": dual(["cf4"], "cf4FinalDiagnosis",
               lambda d: re.sub(r"NSVD|NORMAL SPONTANEOUS VAGINAL DELIVERY", "LOW SEGMENT CESAREAN SECTION",
                                str(d.get("cf4FinalDiagnosis") or "").upper()),
               [("cf2", "dxADiagnosis", "mode"), ("cf4", "cf4FinalDiagnosis", "mode")], needs={"delivery"}),
    "N1": dual(["cf4", "cf2"], "patientLastName", lambda d: _other_letter(d["patientLastName"]),
               _name_views("patientLastName")),
    "N2": dual(["cf2"], "patientMiddleName", lambda d: "" if d.get("patientMiddleName") else None,
               _name_views("patientMiddleName")),
    "N3": dual(["cf2"], ("patientLastName", "patientFirstName"),
               lambda d: (d["patientFirstName"], d["patientLastName"]),
               _name_views("patientLastName") + _name_views("patientFirstName")),
    "N4": dual(["cf1"], "patientNameExt", lambda d: "", _name_views("patientNameExt"),
               setup={"patientNameExt": "JR."}),
    "N5": once(lambda d: {"patientLastName": _other_letter(d["patientLastName"])}),
    "C1": single(["cf4HistoryPresentIllness", "briefHistory"],
                 "The history of present illness is printed on CF4 only; Patient details' brief history is "
                 "not printed. There is no second copy on the forms to differ."),
    "C2": dual(["cf4"], "cf4IcdCode", lambda d: "MCP01" if d.get("cf4IcdCode") != "MCP01" else "NSD01",
               [("csf", "csfFirstCaseRate", "text"), ("cf4", "cf4IcdCode", "text")],
               setup={"csf": ("csfFirstCaseRate", None)}),
    "C3": dual(["cf4"], "cf4ProviderPAN", lambda d: "1234-5678901-2",
               [("csf", "hciProf1AccredNo", "text"), ("cf2", "cf2Prof1AccredNo", "text"),
                ("cf4", "cf4ProviderPAN", "text")],
               setup={"csf": ("hciProf1AccredNo", "1234-5678901-3")}),
    "C4": once(lambda d: ({"lmp": _shift(d["dateAdmitted"], -7 * (_aog_weeks(d.get("admissionDx")) - 4))}
                          if _aog_weeks(d.get("admissionDx")) else None), needs={"delivery", "cf4"}),
    "C5": single(["cf4Abdomen", "cf4AbdomenOthers", "cf4GeneralSurvey"],
                 "The physical examination is printed on CF4 only (one form): there is no second copy on the "
                 "forms to differ."),
    "C6": once(lambda d: {"cf4CourseDate1": _shift(d["dateDischarge"], 3),
                          "cf4CourseOrder1": d.get("cf4CourseOrder1") or "VITAL SIGNS TAKEN"},
               typed_on="CF4", needs={"cf4"}),
    "C7": single(["cf4DrugName1", "cf4DrugName2", "cf4DrugName3"],
                 "The drugs given are printed on CF4 only (one form): there is no second copy on the forms to "
                 "differ."),
    "C8": single(["cf4VitalBP", "cf4VitalHR", "cf4VitalRR", "cf4VitalTemp"],
                 "The vital signs are printed in CF4's boxes only; the physical examination text and the course "
                 "in the ward do not repeat them on the forms. A mismatch with the clinic's chart is outside "
                 "the forms and is not checked."),
}


# ── reading the list ───────────────────────────────────────────────────

def load_mistakes(path=MISTAKES):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(fh)]
    out = []
    for r in rows:
        if not r.get("ID"):
            continue
        how_common = r.get("How common (clinic)", "").lower()
        if how_common and how_common not in WEIGHTS:
            raise ValueError(f"{path.name}, {r['ID']}: How common must be one of {', '.join(WEIGHTS)}.")
        r["weight"] = WEIGHTS.get(how_common)
        r["include"] = r.get("Include", "yes").lower() != "no"
        out.append(r)
    return out


# ── one planted mistake ────────────────────────────────────────────────

def _flags(page, p, d):
    forms = set(page.claim_forms())
    flags = set(forms)
    if d.get("deliveryDate") and not answer_key_is_baby(p):
        flags.add("delivery")
    if answer_key_is_baby(p) and p["Patient ID"] in MOTHER_OF:
        flags.add("baby")
    return flags


def answer_key_is_baby(p):
    return p["First name"].upper().startswith("BABY") or "NEWBORN" in p["Reason for admission"]


def _rules(page):
    return page.validate(ocr_state=GOOD_OCR, signature_state=ALL_SIGNED)


def _judge(before, after):
    """Outcome from the rules before and after the mistake."""
    new = [v for v in after["violations"] if v["id"] not in set(before["fired"])]
    critical = [v["id"] for v in new if v["action"] in ("block_submission", "halt_validation")]
    if critical or (before["canGeneratePDF"] and not after["canGeneratePDF"]):
        return "Blocked", [v["id"] for v in new]
    if new:
        return "Warned", [v["id"] for v in new]
    return "Gets through", []


def _view_values(page, views, forms):
    keys = sorted({k for _f, k, _x in views})
    computed = page.computed(keys)
    out = []
    for form, key, how in views:
        if form in forms:
            out.append((form, key, EXTRACT[how](computed.get(key))))
    return out


def run_dual(page, probe, d, forms):
    keys = probe["key"] if isinstance(probe["key"], tuple) else (probe["key"],)
    target = next((f for f in probe["targets"] if f in forms), None)
    if target is None:
        return None
    wrong = probe["wrong"](d)
    if wrong is None:
        return None
    wrong = wrong if isinstance(wrong, tuple) else (wrong,)
    setup = probe.get("setup") or {}
    steps = []
    # The first copy: typed on its own form (or on Patient details).
    for where, val in setup.items():
        if isinstance(val, tuple):
            key, value = val
            value = value if value is not None else d.get(key)
            res = page.page.evaluate(TYPE_JS, [where, key, value])
            steps.append(f"typed {value!r} in {where.upper()} {key} ({res['status']})")
        else:
            page.set_values({where: val})
            steps.append(f"typed {val!r} in Patient details {where}")
    if setup:
        page.page.wait_for_timeout(100)
    d0 = page.data()
    before = _rules(page)
    agree_before = len({v for _f, _k, v in _view_values(page, probe["views"], forms)}) <= 1
    # The second copy, typed differently on the target form.
    statuses = []
    for key, value in zip(keys, wrong):
        res = page.page.evaluate(TYPE_JS, [target, key, value])
        statuses.append(res["status"])
        steps.append(f"typed {value!r} in {target.upper()} {key} ({res['status']})")
    page.page.wait_for_timeout(100)
    after_values = _view_values(page, probe["views"], forms)
    disagree = len({v for _f, _k, v in after_values}) > 1
    d1 = page.data()
    kept = all(_same(d1.get(k)) == _same(v) for k, v in zip(keys, wrong))
    shown = "; ".join(f"{f.upper()} {k} = {v!r}" for f, k, v in after_values)
    if all(s in ("locked", "no box") for s in statuses):
        how = (f"{target.upper()}'s box is locked: it is filled from Patient details, the same value on every form"
               if "locked" in statuses else f"{target.upper()} has no box to type it in")
        return {"outcome": "Prevented", "how": how, "rules": [], "steps": steps, "values": shown,
                "agree_before": agree_before, "filled": True}
    if not disagree:
        how = ("typing on " + target.upper() + " changed every form (one value)" if kept
               else "the page did not keep the different value")
        return {"outcome": "Prevented", "how": how, "rules": [], "steps": steps, "values": shown,
                "agree_before": agree_before, "filled": True}
    after = _rules(page)
    outcome, rules = _judge(before, after)
    filled = any(_same(d0.get(k)) for k in keys)
    return {"outcome": outcome, "how": "the forms now differ: " + shown, "rules": rules, "steps": steps,
            "values": shown, "agree_before": agree_before, "filled": filled, "can_pdf": after["canGeneratePDF"]}


def run_once(page, probe, d, forms):
    changes = probe["changes"](d)
    if not changes or any(v is None for v in changes.values()):
        return None
    before = _rules(page)
    page.set_values(changes)
    page.page.wait_for_timeout(100)
    d1 = page.data()
    kept = {k: v for k, v in changes.items() if _same(d1.get(k)) == _same(v)}
    steps = [f"typed {v!r} in {probe['typed_on']} {k}" for k, v in changes.items()]
    if not kept:
        return {"outcome": "Prevented", "how": f"the page did not keep it (now {({k: d1.get(k) for k in changes})})",
                "rules": [], "steps": steps, "values": "", "agree_before": True, "filled": False}
    after = _rules(page)
    outcome, rules = _judge(before, after)
    return {"outcome": outcome, "how": "kept: " + ", ".join(f"{k} = {v!r}" for k, v in kept.items()),
            "rules": rules, "steps": steps, "values": "", "agree_before": True, "filled": False,
            "can_pdf": after["canGeneratePDF"]}


MOTHER_CLAIM_ID = 800001


def linked_to_mother(baby, mother, mother_data, mother_copy):
    """What the server answers for a baby's claim linked to its mother's
    (routes/claims_routes.py GET /family and /from-mother): the mother's
    claim as the forms show it, through the server's own
    philhealth.mother_baby.values_for_baby (offline: no database)."""
    def entry(p, claim_id):
        return {"claim_id": claim_id, "name": f"{p['First name']} {p['Last name']}", "dob": p["Birthday"],
                "date_admitted": p["Admitted date"], "delivery_date": p.get("Delivered date"), "reasons": []}
    return {
        "family": {"success": True, "claim_id": None, "role": "baby", "role_chosen": True, "detected_role": "baby",
                   "detected_reason": "", "mother_claim_id": MOTHER_CLAIM_ID,
                   "suggested_mother_id": MOTHER_CLAIM_ID, "mothers": [entry(mother, MOTHER_CLAIM_ID)],
                   "babies": []},
        "from-mother": {"success": True, "mother_claim_id": MOTHER_CLAIM_ID, **mother_copy, "differences": []},
    }


def run_baby(page, probe, p, mother_data, mother_copy):
    """The baby's claim is open; the mother's claim values are known."""
    field = probe["field"]
    d = page.data()
    comp = page.computed(["dxADiagnosis", "dischargeDx", "admissionDx", "patientDOB", "patientSex", "deliveryDate"])
    facts = mother_copy.get("mother_facts", {})
    copied = {i["key"] for g in mother_copy.get("groups", []) for i in g["items"]}
    m_g, m_p = mother_data.get("gravida"), mother_data.get("para")
    if field == "gravida/para":
        if not (m_g and m_p and gravida_of(comp["dischargeDx"])):
            return None
        # The baby's diagnosis names the mother after this birth: para + 1.
        wrong_g = str(int(m_g) + 1)
        changes = {k: _replace_gp(d.get(k), g=wrong_g, p=str(int(m_p) + 2))
                   for k in ("admissionDx", "dischargeDx", "dxADiagnosis", "cf4FinalDiagnosis") if gravida_of(d.get(k))}
        mother_says, ref = f"G{m_g}P{int(m_p) + 1} (mother's claim, after this birth)", "gravida" in facts
        baby_before = f"G{gravida_of(comp['dischargeDx'])}P{para_of(comp['dischargeDx'])}"
    elif field == "birth date":
        m_del = _iso(mother_data.get("deliveryDate"))
        if not m_del:
            return None
        changes = {"patientDOB": _shift(m_del, 1)}
        mother_says, ref, baby_before = f"delivered {m_del}", "patientDOB" in copied, _iso(comp["patientDOB"])
    else:
        m_sex = mother_data.get("babySex")
        if not m_sex:
            return None
        changes = {"patientSex": "Male" if m_sex == "Female" else "Female"}
        mother_says, ref, baby_before = f"baby's sex {m_sex}", "patientSex" in copied, d.get("patientSex") or "(blank)"
    before = _rules(page)
    page.set_values(changes)
    page.page.wait_for_timeout(100)
    after = _rules(page)
    outcome, rules = _judge(before, after)
    return {"outcome": outcome, "how": f"mother's claim: {mother_says}; baby's claim before: {baby_before}, "
                                       f"now {changes}", "rules": rules,
            "steps": [f"typed {v!r} in the baby's claim, Patient details {k}" for k, v in changes.items()],
            "values": "", "agree_before": True, "filled": bool(ref), "can_pdf": after["canGeneratePDF"]}


# ── the run ────────────────────────────────────────────────────────────

def run(progress, samples=False, only=None):
    from research_tests.common.forms_page import FormsPage
    from research_tests.validation import panel_shot
    root = INPUTS / "samples" if samples else INPUTS
    key_path = root / "answer_key.xlsx"
    if not key_path.is_file():
        raise FileNotFoundError(f"{key_path} not found")
    mistakes = load_mistakes()
    wanted = {s.strip().upper() for s in only.split(",")} if only else None
    patients = answer_key.patients(key_path)
    by_id = {p["Patient ID"]: p for p in patients}
    usable = [p for p in patients if not answer_key._text(p.get("Missing in the logbook"))]
    left_out = [p["Patient ID"] for p in patients if p not in usable]
    out = output_dir(TEST_KEY)
    proof = out / "proof"
    shutil.rmtree(proof, ignore_errors=True)
    proof.mkdir(parents=True)

    def body_of(p):
        body, _ = answer_key.auto_populate(p)
        body["saved_values"] = answer_key.claim_values(p) or {}
        return body

    cases, listed, printed_on = [], [], {}
    with FormsPage() as page:
        progress(0.03, "Loading the forms page")
        info = {}
        for p in usable:
            page.open_claim(body_of(p))
            d = page.data()
            info[p["Patient ID"]] = {"forms": set(page.claim_forms()), "flags": _flags(page, p, d)}
        mothers = {}
        from philhealth.mother_baby import values_for_baby
        for baby_id, mother_id in MOTHER_OF.items():
            if baby_id in info and mother_id in by_id:
                page.open_claim(body_of(by_id[mother_id]))
                md = page.data()
                mothers[baby_id] = (md, values_for_baby(md))
        single_keys = sorted({k for pr in PROBES.values() if pr["kind"] == "single" for k in pr["keys"]})
        printed_on = page.page.evaluate(PRINTED_ON_JS, single_keys)

        todo = [m for m in mistakes if m["include"] and (not wanted or m["ID"].upper() in wanted)]
        for n, m in enumerate(todo):
            probe = PROBES.get(m["ID"])
            if probe is None:
                listed.append([m["ID"], m["RTH reason"], m["Mistake"], "Not tested",
                               "No probe written for this ID yet (research_tests/rth_errors.py PROBES)."])
                continue
            if probe["kind"] == "single":
                where = {k: printed_on.get(k) or [] for k in probe["keys"]}
                listed.append([m["ID"], m["RTH reason"], m["Mistake"], "Printed on one form only",
                               probe["why"] + " Printed on: " + "; ".join(
                                   f"{k}: {', '.join(v).upper() or 'no form'}" for k, v in where.items())])
                continue
            applies = (m.get("Applies to") or "all").lower()
            count = 0
            for p in usable:
                pid = p["Patient ID"]
                flags = info[pid]["flags"]
                need = set(probe["needs"]) | ({"delivery"} if applies == "delivery" else set()) | \
                    ({"baby"} if applies == "baby" else set())
                if not need <= flags:
                    continue
                progress(0.05 + 0.9 * n / max(len(todo), 1), f"{m['ID']} on {pid}")
                if probe["kind"] == "baby" and pid in mothers:
                    # The baby's claim saved and linked to its mother's: the page
                    # gets her claim from the server (GET /family, /from-mother).
                    page.open_claim(body_of(p), api=linked_to_mother(p, by_id[MOTHER_OF[pid]], *mothers[pid]))
                    page.page.wait_for_function("() => typeof mb !== 'undefined' && mb.fromMother", timeout=15000)
                    page.page.wait_for_timeout(300)
                else:
                    page.open_claim(body_of(p))
                d = page.data()
                comp = page.computed(["dateAdmitted", "dateDischarge", "patientDOB", "deliveryDate"])
                d = {**d, **{k: _iso(v) for k, v in comp.items() if v}}
                if probe["kind"] == "dual":
                    res = run_dual(page, probe, d, info[pid]["forms"])
                elif probe["kind"] == "once":
                    res = run_once(page, probe, d, info[pid]["forms"])
                else:
                    md, copy = mothers.get(pid, (None, None))
                    res = run_baby(page, probe, p, md, copy) if md else None
                if res is None:
                    continue
                count += 1
                picture = ""
                if res["outcome"] != "Prevented":
                    picture = f"{m['ID']}_{pid}.jpg"
                    panel_shot(page, proof / picture, f"Rule Check Results - {m['ID']} on {pid}: {m['Mistake']}",
                               GOOD_OCR, ALL_SIGNED)
                cases.append({"id": m["ID"], "reason": m["RTH reason"], "weight": m["weight"],
                              "how_common": m.get("How common (clinic)", ""), "entry": m["How it happens"],
                              "mistake": m["Mistake"], "patient": pid, "forms": sorted(info[pid]["forms"]),
                              "picture": picture, **res})
            if not count:
                listed.append([m["ID"], m["RTH reason"], m["Mistake"], "No test patient it applies to",
                               f"Applies to: {applies}; needs {sorted(probe['needs'])}."])
        browser, page_errors = page.browser_version, list(page.errors)
    for m in mistakes:
        if not m["include"]:
            listed.append([m["ID"], m["RTH reason"], m["Mistake"], "Left out (Include = no)", m.get("Notes", "")])
    return report(progress, cases, listed, mistakes, samples, browser, page_errors, left_out)


def _reduction(cases):
    n = len(cases)
    c = {o: sum(1 for x in cases if x["outcome"] == o) for o in OUTCOMES}
    strict_left = c["Warned"] + c["Gets through"]
    lenient_left = c["Gets through"]
    return n, c, strict_left, stats.percent(n - strict_left, n), lenient_left, stats.percent(n - lenient_left, n)


def report(progress, cases, listed, mistakes, samples, browser, page_errors, left_out):
    from research_tests.common.specs import machine_specs
    progress(0.96, "Writing the workbook")
    reasons = []
    for m in mistakes:
        if m["RTH reason"] not in reasons:
            reasons.append(m["RTH reason"])
    how_common = {m["RTH reason"]: (m.get("How common (clinic)", ""), m["weight"]) for m in mistakes}
    rows, weighted = [], []
    for r in reasons:
        sub = [c for c in cases if c["reason"] == r]
        if not sub:
            continue
        n, c, sl, sr, ll, lr = _reduction(sub)
        hc, w = how_common[r]
        rows.append([r, hc, w, len({x["id"] for x in sub}), n, n, c["Prevented"], c["Blocked"], c["Warned"],
                     c["Gets through"], sl, sr, ll, lr])
        if w:
            weighted.append((w, sr, lr))
    n, c, sl, sr, ll, lr = _reduction(cases)
    total = {"n": n, "strict": sr, "lenient": lr}
    rows.append(["All planted mistakes (each counts once)", "", "", len({x["id"] for x in cases}), n, n,
                 c["Prevented"], c["Blocked"], c["Warned"], c["Gets through"], sl, sr, ll, lr])
    wsum = sum(w for w, _s, _l in weighted)
    w_strict = round(sum(w * s for w, s, _l in weighted) / wsum, 2) if wsum else None
    w_len = round(sum(w * l for w, _s, l in weighted) / wsum, 2) if wsum else None
    rows.append(["Weighted by how common each reason is", "", "", "", "", "", "", "", "", "", "", w_strict, "", w_len])
    headers = ["RTH reason", "How common (clinic)", "Weight", "Mistakes", "Planted", "Manual errors",
               "Prevented", "Blocked", "Warned", "Gets through", "PClaimAssist errors (strict)",
               "Error reduction % (strict)", "PClaimAssist errors (warnings count as caught)",
               "Error reduction % (warnings count as caught)"]
    notes = [
        "Mistakes: the clinic's list of common return-to-hospital reasons (inputs/rth_mistakes.csv), each planted "
        "in every test patient it applies to, on the real forms page (offline, " + browser + ").",
        "Manual: each form typed separately, nothing checks it - every planted mistake stays in the claim. "
        "This is the assumption of the comparison, not a measurement of staff.",
        "Prevented = the second copy cannot differ (locked box filled from Patient details, one value for every "
        "form, or not kept); Blocked = a critical rule fires and Save as PDF refuses; Warned = a warning only; "
        "Gets through = in the claim, nothing notices.",
        "Error reduction % = (manual errors - PClaimAssist errors) / manual errors x 100 (the form of Eq. 3.12). "
        "Strict: Warned counts as an error left; the other: a warning counts as caught.",
        "Weighted: the mean of the reasons' reductions, weighted by how common the clinic says each reason is "
        f"({', '.join(f'{k} {v}' for k, v in WEIGHTS.items())}) - the clinic's estimate, not counted from "
        "returned claims.",
        "Supplementary: shows whether the system stops a mistake once made, not how often staff make mistakes. "
        "Eq. 3.12 proper comes from the user sessions (test 7).",
    ]
    if left_out:
        notes.append(f"Patients left out (a value missing in the logbook): {', '.join(left_out)}.")
    if samples:
        notes.append("FICTIONAL SAMPLE PATIENTS.")
    per = []
    for m in mistakes:
        sub = [c for c in cases if c["id"] == m["ID"]]
        if not sub:
            continue
        n, c, sl, sr, ll, lr = _reduction(sub)
        hows = sorted({x["how"] if x["outcome"] == "Prevented" else x["outcome"] for x in sub})
        fired = sorted({r for x in sub for r in x["rules"]})
        per.append([m["ID"], m["RTH reason"], m["How it happens"], m["Mistake"], n, c["Prevented"], c["Blocked"],
                    c["Warned"], c["Gets through"], sr, ", ".join(fired) or "none",
                    hows[0] if len(hows) == 1 else "; ".join(hows)[:300],
                    "Yes" if all(x["filled"] for x in sub) else "No" if not any(x["filled"] for x in sub) else "Some"])
    summary = [
        {"name": "8a RTH error reduction", "title": "Table - Planted RTH mistakes: manual vs PClaimAssist",
         "headers": headers, "rows": rows, "bold_last": True, "notes": notes},
        {"name": "8b Per mistake", "title": "Table - Each RTH mistake and what PClaimAssist did with it",
         "headers": ["ID", "RTH reason", "How it happens", "Mistake", "Planted", "Prevented", "Blocked", "Warned",
                     "Gets through", "Error reduction % (strict)", "Rules that fired", "How",
                     "Filled for staff (no second typing)"],
         "rows": per, "notes": ["Filled for staff: the second copy was already filled from the first (or from the "
                                "mother's claim) when the claim opened, so staff need not type it again."]},
        {"name": "8c Not counted", "title": "Table - Mistakes listed but not counted",
         "headers": ["ID", "RTH reason", "Mistake", "Why not counted", "Detail"], "rows": listed},
        {"name": "8d Run environment", "title": "Table - Where the test ran", "headers": ["Item", "Value"],
         "rows": machine_specs([["Forms page", f"PClaimAssist/index.html in headless {browser}, offline"],
                                ["Rules", "PClaimAssist/js/validation-rules.js runValidationRules"]])},
    ]
    raw = [[c["id"], c["reason"], c["entry"], c["mistake"], c["patient"], ", ".join(c["forms"]), c["outcome"],
            ", ".join(c["rules"]), c["how"], " | ".join(c["steps"]), c["values"],
            "Yes" if c["agree_before"] else "No", "Yes" if c["filled"] else "No", c["picture"]] for c in cases]
    out = output_dir(TEST_KEY)
    path = excel.write_workbook(out / "rth_errors_results.xlsx", [
        {"name": "Raw data", "headers": ["ID", "RTH reason", "How it happens", "Mistake", "Patient", "Forms",
                                         "Outcome", "New rules fired", "How", "What was typed",
                                         "Values on the forms after", "Forms agreed before", "Filled for staff",
                                         "Panel picture"], "rows": raw,
         "notes": [f"Page errors: {len(page_errors)}"] + page_errors[:3]}] + summary)
    excel.save_summary(out, TEST_KEY, TITLE, summary, {"samples": samples})
    progress(1.0, "Done")
    return {"outputs": [path], "headline": [["Planted mistakes", total["n"]],
                                            ["Error reduction % (strict)", total["strict"]],
                                            ["Error reduction % (warnings count as caught)", total["lenient"]],
                                            ["Weighted by how common (strict)", w_strict]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the fictional sample patients")
    parser.add_argument("--only", help="only these mistake IDs, e.g. D1,N1")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
