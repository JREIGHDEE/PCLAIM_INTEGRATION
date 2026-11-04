"""Test 4 - validation engine with seeded errors (Eq. 3.7-3.10).

    python -m research_tests.validation [--samples] [--seed 20261104]

40 records from the answer key's patients: 20 clean, and 20 with 40 seeded
errors (2 per record) across every rule category the engine can detect.
Each record is loaded into the real forms page offline (the patient's
confirmed values through the real auto-population, plus fictional details
staff would type on the forms), the errors are typed in, and the real
validation-rules.js runs (runValidationRules, as the page runs it). Its
flags are compared with the seeded-error manifest:

  for each record: R = rules the seeded errors must fire, A = rules they may
  also fire as a direct consequence (e.g. a discharge before admission is
  also on or before the delivery), F = rules fired
  TP = |F and R|, FN = |R - F|, FP = |F - R - A|
  precision = TP / (TP + FP)  (Eq. 3.7)    recall = TP / (TP + FN)  (Eq. 3.8)
  F1 = 2PR / (P + R)  (Eq. 3.9)
  false alarm rate = clean records with any flag / clean records  (Eq. 3.10)

Every record runs with the OCR state and the signature check switched on
(image quality passed, no pending suggestions, all signatures present), so
the image-quality, correction-status and signature rules are exercised on
the clean records too; a seeded error then changes one of those.

Not seeded (written in the manifest and the summary): IC-01, IC-02, IC-07 -
names, PIN and dates are consistent across forms by construction (all five
forms fill from one entry, so the engine fixes these features at "match");
MF-08 - the page always writes the discharge line into an empty course in
the ward, so it cannot be blank; and no attachment rule exists (the
attachment count is not used by any rule).

Errors are typed where staff would type them: while the patient is the
member, the PIN and birth date go in the patient's boxes (the member's
follow them, app.js applyMemberIsPatient). The manifest says, for every
error, whether the page kept the seeded value.

The manifest (outputs/validation/seeded_errors_manifest.csv) is the same for
the same answer key and seed.
"""
import random
from datetime import date, timedelta

from research_tests import INPUTS, output_dir
from research_tests.common import answer_key, excel, stats

TEST_KEY = "validation"
TITLE = "Validation engine test (seeded errors)"
SEED = 20261104
NOT_SEEDED = [
    ("IC-01", "Patient name not consistent across the five forms",
     "Consistent by construction: all five forms fill from one entry (the engine fixes name_match_across_forms = 1)."),
    ("IC-02", "PIN not consistent across CSF, CF4 and PMRF",
     "Consistent by construction: one PIN feeds every form (pin_match_across_forms = 1)."),
    ("IC-07", "Admission/discharge dates not the same across CSF, CF2, CF4",
     "Consistent by construction: one pair of dates feeds every form (dates_match_across_forms = 1)."),
    ("MF-08", "CF4 course in the ward missing",
     "CF4 course in the ward is auto-filled with a discharge line: the page writes it whenever the course is "
     "empty (app.js DERIVED_FIELDS cf4CourseOrder2), so the engine never sees it blank."),
    ("MF-09 (delivery claims)", "CF4 drugs not indicated, on a delivery claim",
     "Seeded only on CF4 claims whose drugs the page leaves blank: on a delivery claim the package's drugs "
     "(oxytocin, mefenamic acid, lidocaine) are put back whenever the drugs are emptied, so MF-09 cannot fire there."),
    ("(none)", "Attachment / supporting documents",
     "No attachment rule exists: the attachment count is computed but no rule uses it."),
]
GOOD_OCR = {"active": True, "imageQualityPass": True, "pendingSuggestions": 0}
ALL_SIGNED = {"active": True, "member": True, "midwife": True, "hciRep": True, "employer": True,
              "hciAssist": True, "cf4Provider": True, "thumbmark": False}


def _shift(iso, days):
    return (date.fromisoformat(iso) + timedelta(days=days)).isoformat()


# ── the seeded errors ──────────────────────────────────────────────────
# Each: key, seeded category, error type, field, needs (cf4 / delivery),
# touches (no two errors in a record touch the same thing), required and
# allowed rules, and seed(data) -> (state.data changes, ocr changes, signature changes).

def _err(key, category, kind, field, required, allowed=(), needs=(), touches=(), seed=None):
    return {"key": key, "category": category, "kind": kind, "field": field, "required": list(required),
            "allowed": list(allowed), "needs": set(needs), "touches": set(touches) | {key}, "seed": seed}


def _pin(d, value):
    """The PIN as staff type it: while the patient is the member there is one
    PIN for one person (app.js applyMemberIsPatient copies it to both boxes),
    so it is typed in the patient's box and the member's follows."""
    if d.get("memberIsPatient"):
        return {"patientPIN": value, "memberPIN": value}
    return {"memberPIN": value}


def _member_dob(d, value):
    """The member's birth date as staff type it: the patient's box while the
    patient is the member (the member's box follows it, app.js)."""
    return {"patientDOB": value} if d.get("memberIsPatient") else {"memberDOB": value}


def _pin_11(d):
    digits = "".join(ch for ch in d["memberPIN"] if ch.isdigit())[:11]
    return _pin(d, f"{digits[:2]}-{digits[2:10]}-{digits[10:]}"), {}, {}


def _pin_letter(d):
    pin = d["memberPIN"]
    return _pin(d, pin[:5] + "O" + pin[5:]), {}, {}                  # still 12 digits, one letter


def _unreadable_date(d):
    """A birth date kept as the text OCR read, with a letter O for a zero."""
    iso = d.get("patientDOB") or "1995-03-05"
    return {"patientDOB": f"O{iso[6:7]}-{iso[8:10]}-{iso[0:4]}"}, {}, {}


def _digit_name(d):
    first = d["patientFirstName"] or "ANA"
    return {"patientFirstName": first[0] + "1" + first[2:] if len(first) > 1 else first + "1"}, {}, {}


ERRORS = [
    _err("MF-name", "Missing field", "Patient name left blank", "patientName", ["MF-01"],
         touches={"name"}, seed=lambda d: ({"patientLastName": "", "patientFirstName": "", "patientMiddleName": "",
                                            "patientNameExt": ""}, {}, {})),
    _err("MF-pin", "Missing field", "Member PIN left blank", "memberPIN", ["MF-02"], touches={"pin"},
         seed=lambda d: (_pin(d, ""), {}, {})),
    _err("MF-dob", "Missing field", "Member date of birth left blank", "memberDOB", ["MF-03"],
         touches={"memberdob", "patientdob"}, seed=lambda d: (_member_dob(d, ""), {}, {})),
    _err("MF-admit", "Missing field", "Date admitted left blank", "dateAdmitted", ["MF-04"], touches={"admit"},
         seed=lambda d: ({"dateAdmitted": ""}, {}, {})),
    _err("MF-discharge", "Missing field", "Date discharged left blank", "dateDischarge", ["MF-05"],
         touches={"discharge"}, seed=lambda d: ({"dateDischarge": ""}, {}, {})),
    _err("MF-many", "Missing field", "Four required fields left blank (accommodation, disposition, HCI "
         "accreditation no., HCI name)", "accommodation, disposition, hciPAN, hciName", ["MF-06"], touches={"cf2"},
         seed=lambda d: ({"accommodation": "", "disposition": "", "hciPAN": "", "hciName": ""}, {}, {})),
    _err("MF-cc", "Missing CF4 field", "CF4 chief complaint left blank", "cf4ChiefComplaint", ["MF-07"],
         needs={"cf4"}, seed=lambda d: ({"cf4ChiefComplaint": ""}, {}, {})),
    _err("MF-drugs", "Missing CF4 field", "CF4 drugs administered left blank", "cf4DrugName1-3", ["MF-09"],
         needs={"cf4", "cf4_drugs_kept_blank"},
         seed=lambda d: ({"cf4DrugName1": "", "cf4DrugName2": "", "cf4DrugName3": ""}, {}, {})),
    _err("IF-11", "Invalid format", "PIN with 11 digits", "memberPIN", ["IF-01"], touches={"pin"}, seed=_pin_11),
    _err("IF-letter", "Invalid format", "Letter in the PIN", "memberPIN", ["IF-02"], touches={"pin"}, seed=_pin_letter),
    _err("IF-date", "Invalid format", "Birth date kept as unreadable text (OCR's letter O for a zero)", "patientDOB",
         ["IF-03"], touches={"patientdob", "memberdob"}, seed=_unreadable_date),
    _err("IF-digit", "Invalid format", "Digit in the patient's first name", "patientFirstName", ["IF-04"],
         touches={"name"}, seed=_digit_name),
    _err("IC-dis-before", "Inconsistent entry", "Discharge date before admission", "dateDischarge", ["IC-03"],
         allowed=["IC-05", "IC-08"], touches={"admit", "discharge", "delivery"},
         seed=lambda d: ({"dateDischarge": _shift(d["dateAdmitted"], -2)}, {}, {})),
    _err("IC-dob-after", "Inconsistent entry", "Member born after admission", "memberDOB", ["IC-04"],
         touches={"admit", "memberdob", "patientdob"},
         seed=lambda d: (_member_dob(d, _shift(d["dateAdmitted"], 30)), {}, {})),
    _err("IC-delivery", "Inconsistent entry", "Delivery date before admission", "deliveryDate", ["IC-05"],
         needs={"delivery"}, touches={"admit", "delivery", "discharge"},
         seed=lambda d: ({"deliveryDate": _shift(d["dateAdmitted"], -1)}, {}, {})),
    _err("IC-relationship", "Inconsistent entry", "Member differs from patient, relationship blank", "relationship",
         ["IC-06"], touches={"relationship", "member", "name", "pin", "memberdob"},
         seed=lambda d: ({"memberIsPatient": False, "memberFirstName": "ROLANDO", "memberLastName":
                          (d["patientLastName"] or "CRUZ"), "memberSex": "Male", "relationship": ""}, {}, {})),
    _err("IC-dx", "Inconsistent entry", "CF2 and CF4 diagnoses differ", "dxADiagnosis / cf4FinalDiagnosis",
         ["IC-09"], needs={"cf4"}, touches={"dx"},
         seed=lambda d: ({"dxADiagnosis": "PREGNANCY UTERINE", "cf4FinalDiagnosis": "ACUTE GASTROENTERITIS"}, {}, {})),
    _err("IC-same-day", "Inconsistent entry", "Discharged the same day as the delivery", "dateDischarge", ["IC-08"],
         needs={"delivery"}, touches={"discharge", "delivery", "dischargetime"},
         seed=lambda d: ({"dateDischarge": d["deliveryDate"]}, {}, {})),
    _err("SP-member", "Signature", "Member signature missing (signed form checked)", "member signature", ["SP-01"],
         seed=lambda d: ({}, {}, {"member": False})),
    _err("SP-midwife", "Signature", "Attending midwife signature missing on CF4", "midwife signature", ["SP-02"],
         needs={"cf4"}, seed=lambda d: ({}, {}, {"midwife": False})),
    _err("SP-hcirep", "Signature", "HCI representative signature missing", "HCI representative signature",
         ["SP-03"], seed=lambda d: ({}, {}, {"hciRep": False})),
    _err("SP-employer", "Signature", "Employer signature missing for an employed member", "employer signature",
         ["SP-04"], touches={"membertype"},
         seed=lambda d: ({"memberType": "Employed Private"}, {}, {"employer": False})),
    _err("SP-thumb", "Signature", "Thumbmark without the HCI assisting representative", "thumbmark",
         ["SP-05"], seed=lambda d: ({}, {}, {"thumbmark": True, "hciAssist": False})),
    _err("SP-provider", "Signature", "Attending provider signature missing on CF4", "CF4 provider signature",
         ["SP-06"], needs={"cf4"}, seed=lambda d: ({}, {}, {"cf4Provider": False})),
    _err("IQ-blurry", "Image quality / correction status", "Logbook page failed the image quality check",
         "scan", ["IQ-01"], touches={"iq"}, seed=lambda d: ({}, {"imageQualityPass": False}, {})),
    _err("CR-one", "Image quality / correction status", "One correction suggestion not yet reviewed",
         "OCR suggestion", ["CR-01"], touches={"cr"}, seed=lambda d: ({}, {"pendingSuggestions": 1}, {})),
    _err("CR-many", "Image quality / correction status", "Five correction suggestions not yet reviewed",
         "OCR suggestions", ["CR-02"], allowed=["CR-01"], touches={"cr"},
         seed=lambda d: ({}, {"pendingSuggestions": 5}, {})),
]
# A blank seeded into a required field adds to the blank-field count, so two
# such errors (or one with a field the forms copy, like the member's name
# while the patient is the member) can pass MF-06's "more than 3 blank": a
# direct consequence, never a false alarm.
for _e in ERRORS:
    if _e["key"].startswith("MF-") and _e["key"] != "MF-many" and "MF-06" not in _e["allowed"]:
        _e["allowed"].append("MF-06")
BY_KEY = {e["key"]: e for e in ERRORS}
# The 13 errors seeded a second time to make 40 (27 kinds + 13): missing fields, formats and
# inconsistencies are the commonest return-to-hospital reasons.
SECOND_TIME = ["MF-pin", "MF-admit", "MF-discharge", "MF-cc", "IF-11", "IF-letter", "IF-date",
               "IC-dis-before", "IC-dob-after", "IC-same-day", "MF-dob", "MF-name",
               "MF-drugs"]


# ── records ────────────────────────────────────────────────────────────

def is_baby(p):
    return p["First name"].upper().startswith("BABY") or "NEWBORN" in p["Reason for admission"]


def fictional_details(p, index):
    """What staff would type on the forms for this patient - fictional,
    the same every run (from the patient's position)."""
    rng = random.Random(f"{SEED}-{p['Patient ID']}")
    pin = f"{12 + index % 80:02d}-{rng.randint(10**8, 10**9 - 1)}-{rng.randint(0, 9)}"
    base = {"memberPIN": pin, "accommodation": "Non-Private", "disposition": "Improved",
            "hciPAN": "H12345678", "hciName": "SAMPLE LYING-IN CLINIC", "memberSex": "Female",
            "civilStatus": "Married", "memberType": "Indirect Contributor",
            "cf4HistoryPresentIllness": "G1 - PRESENT PREGNANCY",
            "cf4PhysicalExam": "BP 110/70, HR 82, RR 18, T 36.7C. ESSENTIALLY NORMAL."}
    if is_baby(p):
        base.update({"memberIsPatient": False, "memberLastName": p["Last name"], "memberFirstName": "LORNA",
                     "memberMiddleName": "REYES", "memberDOB": f"{1990 + index % 10}-05-1{index % 9}",
                     "relationship": "Child", "patientPIN": "00-000000000-0"})
    else:
        base.update({"memberIsPatient": True, "memberLastName": p["Last name"], "memberFirstName": p["First name"],
                     "memberMiddleName": p["Middle name"], "memberDOB": p["Birthday"], "relationship": "Self",
                     "patientPIN": pin})
    return base


def assign(errors, records, seed):
    """Two errors per seeded record, every error placed where it can be
    detected (a CF4 rule on a claim with CF4, a delivery rule on a record
    with a delivery), no two errors in one record touching the same thing."""
    for attempt in range(200):
        rng = random.Random(seed + attempt)
        order = sorted(errors, key=lambda e: (-len(e["needs"]), rng.random()))
        slots = {r["record"]: [] for r in records}
        ok = True
        for e in order:
            fits = [r for r in records if len(slots[r["record"]]) < 2 and e["needs"] <= r["has"]
                    and not any(e["touches"] & o["touches"] for o in slots[r["record"]])]
            if not fits:
                ok = False
                break
            fits.sort(key=lambda r: (len(slots[r["record"]]), rng.random()))
            slots[fits[0]["record"]].append(e)
        if ok and all(len(v) == 2 for v in slots.values()):
            return slots
    raise RuntimeError("Could not place the 40 errors - the answer key needs more patients with CF4 "
                       "(labor/newborn) and with a delivery date.")


def run(progress, samples=False, seed=SEED):
    root = INPUTS / "samples" if samples else INPUTS
    key_path = root / "answer_key.xlsx"
    if not key_path.is_file():
        raise FileNotFoundError(f"{key_path} not found (template: inputs/answer_key_template.xlsx; or --samples)")
    from research_tests.common.forms_page import FormsPage
    patients = answer_key.patients(key_path)
    if len(patients) < 2:
        raise ValueError("The answer key needs patients (sheet Patients).")
    # A clean record must be error-free: patients with a value missing in the
    # logbook (e.g. no discharge date) are left out of the records.
    usable = [p for p in patients if not answer_key._text(p.get("Missing in the logbook"))]
    left_out = [p["Patient ID"] for p in patients if p not in usable]
    chosen = [usable[i % len(usable)] for i in range(20)]
    instances = ERRORS + [dict(BY_KEY[k], key=k) for k in SECOND_TIME]
    assert len(instances) == 40

    results, rules = [], {}
    with FormsPage() as page:
        progress(0.05, "Loading the forms page")
        # Which forms each patient's claim has (for placing CF4 errors).
        has = {}
        for p in chosen:
            if p["Patient ID"] in has:
                continue
            body, _ = answer_key.auto_populate(p)
            body["saved_values"] = answer_key.claim_values(p) or fictional_details(p, chosen.index(p))
            page.open_claim(body)
            d = page.data()
            has[p["Patient ID"]] = set(page.claim_forms()) | ({"delivery"} if d.get("deliveryDate") else set())
            # Does the page keep CF4's drugs blank? (A delivery package puts its drugs back.)
            page.set_values({"cf4DrugName1": "", "cf4DrugName2": "", "cf4DrugName3": ""})
            after = page.data()
            if not any(str(after.get(f"cf4DrugName{k}") or "").strip() for k in (1, 2, 3)):
                has[p["Patient ID"]].add("cf4_drugs_kept_blank")
        rules = {r["id"]: r for r in page.rules()}
        records = [{"record": f"C{i + 1:02d}", "patient": p, "kind": "clean", "errors": []}
                   for i, p in enumerate(chosen)]
        seeded = [{"record": f"S{i + 1:02d}", "patient": p, "kind": "seeded", "has": has[p["Patient ID"]]}
                  for i, p in enumerate(chosen)]
        slots = assign(instances, seeded, seed)
        for r in seeded:
            r["errors"] = slots[r["record"]]
        records += seeded

        for n, rec in enumerate(records):
            p = rec["patient"]
            progress(0.1 + 0.85 * n / len(records), f"Record {rec['record']} ({p['Patient ID']})")
            body, _ = answer_key.auto_populate(p)
            body["saved_values"] = answer_key.claim_values(p) or fictional_details(p, chosen.index(p))
            page.open_claim(body)
            before = page.data()
            ocr, sig, changes, details = dict(GOOD_OCR), dict(ALL_SIGNED), {}, []
            for e in rec["errors"]:
                c, o, s = e["seed"](before)
                changes.update(c)
                ocr.update(o)
                sig.update(s)
                details.append({"error": e, "from": {k: before.get(k) for k in c}, "to": c, "ocr": o, "sig": s})
            if changes:
                page.set_values(changes)
            after = page.data()
            for det in details:
                det["reverted"] = {k: after.get(k) for k, v in det["to"].items() if after.get(k) != v}
            out = page.validate(ocr_state=ocr, signature_state=sig)
            rec.update({"fired": out["fired"], "violations": out["violations"], "details": details,
                        "forms": page.claim_forms(), "ms": out["ms"]})
            results.append(rec)
        browser, page_errors = page.browser_version, list(page.errors)

    return report(progress, results, rules, samples, seed, browser, page_errors, left_out)


def score(rec):
    required = {r for e in rec["errors"] for r in e["required"]}
    allowed = {r for e in rec["errors"] for r in e["allowed"]} - required
    fired = set(rec["fired"])
    return {"tp": fired & required, "fn": required - fired, "fp": fired - required - allowed,
            "consequence": fired & allowed}


def _prf(tp, fp, fn):
    p = stats.ratio(tp, tp + fp)
    r = stats.ratio(tp, tp + fn)
    return p, r, stats.f1(p, r)


def report(progress, results, rules, samples, seed, browser, page_errors, left_out=()):
    from research_tests.common.specs import machine_specs
    progress(0.96, "Comparing the flags with the manifest")
    scored = [(rec, score(rec)) for rec in results]
    tp = sum(len(s["tp"]) for _, s in scored)
    fp = sum(len(s["fp"]) for _, s in scored)
    fn = sum(len(s["fn"]) for _, s in scored)
    precision, recall, f1 = _prf(tp, fp, fn)
    clean = [(rec, s) for rec, s in scored if rec["kind"] == "clean"]
    flagged_clean = [rec for rec, s in clean if rec["fired"]]
    false_alarm = stats.ratio(len(flagged_clean), len(clean))

    category_of = lambda rule: rules.get(rule, {}).get("category", "?")
    cats = {}
    for rec, s in scored:
        for kind in ("tp", "fn", "fp"):
            for rule in s[kind]:
                cats.setdefault(category_of(rule), {"tp": 0, "fp": 0, "fn": 0})[kind] += 1
    cat_rows = []
    for cat in ["Missing Field", "Invalid Format", "Inconsistent Entry", "Signature", "Image Quality",
                "Correction Status"] + sorted(set(cats) - {"Missing Field", "Invalid Format", "Inconsistent Entry",
                                                           "Signature", "Image Quality", "Correction Status"}):
        c = cats.get(cat)
        if not c:
            continue
        p, r, f = _prf(c["tp"], c["fp"], c["fn"])
        cat_rows.append([cat, c["tp"] + c["fn"], c["tp"], c["fp"], c["fn"], p, r, f])
    cat_rows.append(["All rules", tp + fn, tp, fp, fn, precision, recall, f1])

    seeded_rows = []
    by_cat = {}
    for rec, s in scored:
        for e in rec["errors"]:
            hit = bool(set(e["required"]) & set(rec["fired"]))
            by_cat.setdefault(e["category"], [0, 0])
            by_cat[e["category"]][0] += 1
            by_cat[e["category"]][1] += hit
    for cat, (n, hit) in by_cat.items():
        seeded_rows.append([cat, n, hit, n - hit, stats.ratio(hit, n)])
    total_errors = sum(v[0] for v in by_cat.values())
    total_hit = sum(v[1] for v in by_cat.values())
    seeded_rows.append(["All seeded errors", total_errors, total_hit, total_errors - total_hit,
                        stats.ratio(total_hit, total_errors)])

    not_seeded_note = "Not seeded: " + "; ".join(f"{r} - {why}" for r, _, why in NOT_SEEDED)
    notes = [
        "Unit: one rule on one record. R = rules the record's seeded errors must fire, A = rules they may fire as a "
        "direct consequence, F = rules fired. TP = |F and R|, FN = |R - F|, FP = |F - R - A|.",
        "Precision = TP / (TP + FP) (Eq. 3.7); recall = TP / (TP + FN) (Eq. 3.8); F1 = 2PR / (P + R) (Eq. 3.9); "
        "false alarm rate = clean records with any flag / clean records (Eq. 3.10).",
        "Engine: PClaimAssist/js/validation-rules.js runValidationRules, run in the real forms page offline "
        f"({browser}); OCR state and signature check on for every record (all passing on clean records).",
        not_seeded_note,
        f"Seed {seed}; manifest: seeded_errors_manifest.csv."
        + (f" Patients left out of the records because a value is missing in their logbook entry (a clean record "
           f"must be error-free): {', '.join(left_out)}." if left_out else ""),
        "The seeded errors were designed from the rule definitions (Tables 3.4-3.8), one or more per rule the "
        "engine can detect, so the result shows that the rules work as written - not how many of all real-world "
        "claim errors they would catch.",
    ]
    if samples:
        notes.append("FICTIONAL SAMPLE PATIENTS (make_samples.py).")
    summary = [
        {"name": "4a Validation overall", "title": "Table - Validation engine results (seeded errors)",
         "headers": ["Measure", "Value"],
         "rows": [["Records (clean / seeded)", f"{len(clean)} / {len(results) - len(clean)}"],
                  ["Seeded errors", total_errors], ["Seeded errors detected", total_hit],
                  ["True positives (TP)", tp], ["False positives (FP)", fp], ["False negatives (FN)", fn],
                  ["Precision (Eq. 3.7)", precision], ["Recall (Eq. 3.8)", recall], ["F1 score (Eq. 3.9)", f1],
                  ["Clean records with a flag", f"{len(flagged_clean)} of {len(clean)}"],
                  ["False alarm rate (Eq. 3.10)", false_alarm]],
         "notes": notes},
        {"name": "4b Validation per category", "title": "Table - Validation results per rule category",
         "headers": ["Rule category", "Seeded errors (expected flags)", "TP", "FP", "FN", "Precision", "Recall",
                     "F1"], "rows": cat_rows, "bold_last": True,
         "notes": notes[:1] + ["Seeded errors = the flags the seeded errors must raise in that category. Some "
                               "categories have only 1-3, so one miss moves their recall a lot."]},
        {"name": "4c Seeded categories", "title": "Table - Seeded errors detected per seeded category",
         "headers": ["Seeded category", "Errors", "Detected", "Missed", "Detection rate"], "rows": seeded_rows,
         "bold_last": True, "notes": [not_seeded_note]},
        {"name": "4d Run environment", "title": "Table - Where the validation engine ran",
         "headers": ["Item", "Value"], "rows": machine_specs([["Validation engine", f"PClaimAssist/js/validation-rules.js, run in headless {browser} (the real forms page, offline)"],
                    ["PDF export", f"PClaimAssist/js/pdf/pdf-overlay.js buildFilledPdf with pdf-lib 1.17.1 "
                                   f"(research_tests/vendor), run in headless {browser}"]])},
    ]
    manifest_headers = ["Record", "Patient", "Error #", "Seeded category", "Error type", "Field", "Original value",
                        "Seeded value", "Kept by the page", "Expected rule(s)", "Also allowed (consequence)",
                        "Detected"]
    manifest = []
    for rec, s in scored:
        for i, d in enumerate(rec.get("details") or [], start=1):
            e = d["error"]
            seeded_value = {**d["to"], **({"ocr": d["ocr"]} if d["ocr"] else {}),
                            **({"signatures": d["sig"]} if d["sig"] else {})}
            manifest.append([rec["record"], rec["patient"]["Patient ID"], i, e["category"], e["kind"], e["field"],
                             d["from"] or "", seeded_value,
                             "Yes" if not d.get("reverted") else f"No - the page put back {d['reverted']}",
                             ", ".join(e["required"]), ", ".join(e["allowed"]),
                             "Yes" if set(e["required"]) & set(rec["fired"]) else "No"])
    manifest_notes = [f"{r}: {what} - NOT SEEDED. {why}" for r, what, why in NOT_SEEDED]
    raw_rows = []
    for rec, s in scored:
        raw_rows.append([rec["record"], rec["kind"], rec["patient"]["Patient ID"], ", ".join(rec["forms"]),
                         ", ".join(e["key"] for e in rec["errors"]), ", ".join(sorted(rec["fired"])),
                         ", ".join(sorted(s["tp"])), ", ".join(sorted(s["fp"])), ", ".join(sorted(s["fn"])),
                         ", ".join(sorted(s["consequence"])), round(rec["ms"], 3)])
    out = output_dir(TEST_KEY)
    excel.write_workbook(out / "seeded_errors_manifest.xlsx",
                         [{"name": "Manifest", "headers": manifest_headers, "rows": manifest, "notes": manifest_notes}])
    import csv
    with open(out / "seeded_errors_manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(manifest_headers)
        for row in manifest:
            w.writerow([excel._cell_value(v) for v in row])
        w.writerow([])
        for note in manifest_notes:
            w.writerow([note])
    path = excel.write_workbook(out / "validation_results.xlsx", [
        {"name": "Raw data", "headers": ["Record", "Kind", "Patient", "Forms", "Seeded errors", "Rules fired", "TP",
                                         "FP", "FN", "Allowed consequences", "Engine ms"], "rows": raw_rows,
         "notes": [f"Page errors: {len(page_errors)}"] + page_errors[:3]},
        {"name": "Manifest", "headers": manifest_headers, "rows": manifest, "notes": manifest_notes},
    ] + summary)
    excel.save_summary(out, TEST_KEY, TITLE, summary, {"samples": samples})
    progress(1.0, "Done")
    return {"outputs": [path, out / "seeded_errors_manifest.csv"], "headline": [
        ["TP / FP / FN", f"{tp} / {fp} / {fn}"], ["Precision", precision], ["Recall", recall], ["F1", f1],
        ["False alarm rate (clean records)", false_alarm]]}


def add_arguments(parser):
    parser.add_argument("--samples", action="store_true", help="use the fictional sample patients")
    parser.add_argument("--seed", type=int, default=SEED, help="seed for placing the errors")


if __name__ == "__main__":
    from research_tests.common.cli import main
    main(TEST_KEY, run, __doc__.splitlines()[0], add_arguments)
