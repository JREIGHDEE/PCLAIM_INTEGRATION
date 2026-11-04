"""Computer-drawn, fictional sample inputs, so every test can be run before
the real scans and session data are ready:

  python -m research_tests.make_samples

writes research_tests/inputs/samples/ (the same layout as inputs/):
  answer_key.xlsx        20 fictional patients + the handwriting answer key
  writers.csv            W01-W05 caps, W06-W10 lower, R1-R3 both styles
  scans/handwriting/     one logbook spread per scan, drawn on the clinic's
                         own logbook layout (Ocr_module/grid_templates):
                         printed lines, column rules, printed header, and
                         each "writer" in a different typeface, slant and
                         ink - NOT real handwriting
  iq/good, iq/bad        page pictures, and blurry / dark / bright copies
  iq/expected.csv        the outcome each picture should get
  session_data.xlsx      fictional usability-session numbers

Every test takes --samples to read these instead of inputs/. The samples
only show that the tests run end to end; Chapter 5's numbers must come from
the real scans.
"""
import csv
import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

from research_tests import INPUTS, OCR_DIR
from research_tests.common.answer_key import (FIELD_TO_CATEGORY, HANDWRITING_COLUMNS, PATIENT_COLUMNS,
                                              WRITER_COLUMNS)
from research_tests.common.excel import write_workbook

SAMPLES = INPUTS / "samples"
SEED = 20261104
ENTRIES_PER_SPREAD = 6

LAST = ["DELA CRUZ", "SANTOS", "REYES", "BAUTISTA", "GARCIA", "MENDOZA", "VILLANUEVA", "RAMOS", "AQUINO",
        "CASTILLO", "NAVARRO", "SALAZAR", "TORRES", "FLORES", "GONZALES", "LOPEZ", "PASCUAL", "MORALES",
        "DOMINGO", "SORIANO"]
FIRST = ["MARIA", "ANA", "JOY", "LIZA", "ROSE", "GRACE", "CARMEN", "NORA", "ELLA", "MAY", "LORNA", "JANE",
         "RUTH", "IRENE", "TESS", "LYN", "DIANA", "FE", "SOL", "AIDA"]
MIDDLE = ["SANTOS", "CRUZ", "LIM", "TAN", "DIAZ", "ROXAS", "LUNA", "ABAD", "CRUZ", "SY", "PEREZ", "YAP",
          "GO", "ONG", "UY", "CHAN", "DY", "LEE", "CO", "NG"]
PUROKS = ["PUROK 1", "PUROK 2", "PUROK 3", "PUROK 4", "PUROK 5", "PUROK 6"]
PLACES = ["CABANTIAN", "INDANGAN", "BUHANGIN", "TIGATTO", "COMMUNAL", "MANDUG"]
# (reason for admission, final diagnosis, delivered?)
VISITS = [
    ("LABOR PAINS", "PREGNANCY UTERINE DELIVERED", True),
    ("LABOR PAINS", "G2P2 (2002) PREGNANCY DELIVERED", True),
    ("NEWBORN CARE", "LIVE TERM BABY GIRL", True),
    ("FOR PSI INSERTION", "PSI INSERTION", False),
    ("POSTPARTUM VISIT", "POSTPARTUM VISIT", False),
    ("PRENATAL CHECK-UP", "PRENATAL CHECK-UP", False),
    ("FOR IUD INSERTION", "IUD INSERTION", False),
]


def fictional_patients(n=20, rng=None):
    rng = rng or random.Random(SEED)
    out = []
    for i in range(n):
        reason, final, delivered = VISITS[i % len(VISITS)]
        day = 1 + (i * 3) % 27
        adm_hour = rng.choice([7, 8, 9, 10, 11, 1, 2, 3, 4, 5])
        adm_ampm = "AM" if adm_hour >= 7 else "PM"
        p = {
            "Patient ID": f"P{i + 1:02d}", "Case number": f"2026-{410 + i:04d}",
            "Last name": LAST[i], "First name": FIRST[i], "Middle name": MIDDLE[i], "Suffix": "",
            "Birthday": f"{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}-{rng.randint(1988, 2004)}",
            "Address": "",
            "Admitted date": f"10-{day:02d}-2026", "Admitted time": f"{adm_hour}:{rng.choice(['00', '15', '30', '45'])}",
            "Admitted AM/PM": adm_ampm,
            "Delivered date": "", "Delivered time": "", "Delivered AM/PM": "",
            "Went home date": f"10-{day + (1 if delivered else 0):02d}-2026",
            "Went home time": f"{rng.choice([9, 10, 11])}:{rng.choice(['00', '30'])}" if delivered
            else f"{rng.choice([2, 3, 4])}:{rng.choice(['00', '30'])}",
            "Went home AM/PM": "AM" if delivered else "PM",
            "Reason for admission": reason, "Final diagnosis": final,
            "Street": rng.choice(PUROKS), "Barangay": rng.choice(PLACES), "City": "DAVAO CITY",
            "Province": "DAVAO DEL SUR",
        }
        p["Address"] = f"{p['Street']}, {p['Barangay']}, {p['City']}"
        if reason == "NEWBORN CARE":
            p.update({"Last name": LAST[i - 1] if i else LAST[i], "First name": "BABY GIRL", "Middle name": "",
                      "Birthday": p["Admitted date"]})
        if delivered:
            p.update({"Delivered date": p["Admitted date"], "Delivered time": f"{rng.choice([1, 2, 3])}:{rng.choice(['10', '20', '40'])}",
                      "Delivered AM/PM": "PM"})
        out.append(p)
    return out


def logbook_text(p):
    """What is written in each logbook column for this patient (the ground truth)."""
    def when(prefix):
        d = p[f"{prefix} date"]
        return f"{d} {p[f'{prefix} time']} {p[f'{prefix} AM/PM']}".strip() if d else ""
    name = f"{p['Last name']}, {' '.join(x for x in (p['First name'], p['Middle name']) if x)}"
    return {"Case number": p["Case number"], "Admitted": when("Admitted"), "Patient name": name,
            "Birthday": p["Birthday"], "Address": p["Address"], "Reason for admission": p["Reason for admission"],
            "Delivered": when("Delivered"), "Final diagnosis": p["Final diagnosis"], "Went home": when("Went home")}


# ── drawing a logbook spread ───────────────────────────────────────────

SCALE = 2.0          # pages drawn at twice the setup's size (a ~200 dpi scan)
FIRST_LINE = 150     # first printed line under the header (setup pixels)
PITCH = 34           # printed line spacing (setup pixels)
PER_ENTRY = 3        # printed lines per entry


def _templates():
    out = {}
    for path in sorted((OCR_DIR / "grid_templates").glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        out[t["metadata"]["pageParity"]] = t
    return out


WRITER_LOOKS = [  # (font, scale, thickness, slant, ink BGR)
    (cv2.FONT_HERSHEY_SIMPLEX, 0.95, 2, 0.00, (40, 30, 30)),
    (cv2.FONT_HERSHEY_DUPLEX, 0.90, 2, 0.12, (120, 40, 20)),
    (cv2.FONT_HERSHEY_COMPLEX, 0.85, 2, -0.08, (30, 30, 30)),
    (cv2.FONT_HERSHEY_TRIPLEX, 0.85, 2, 0.18, (110, 50, 30)),
    (cv2.FONT_HERSHEY_SIMPLEX | cv2.FONT_ITALIC, 0.95, 2, 0.05, (20, 20, 20)),
    (cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.25, 2, 0.10, (130, 60, 20)),
    (cv2.FONT_HERSHEY_DUPLEX, 0.85, 3, -0.05, (35, 35, 35)),
    (cv2.FONT_HERSHEY_SIMPLEX, 1.00, 3, 0.15, (100, 45, 25)),
    (cv2.FONT_HERSHEY_TRIPLEX | cv2.FONT_ITALIC, 0.85, 2, 0.00, (25, 25, 25)),
    (cv2.FONT_HERSHEY_COMPLEX, 0.90, 2, 0.20, (125, 55, 30)),
]


def _lines_for(text, width, font, scale, thickness, most=2):
    words, lines = text.split(), [""]
    for word in words:
        trial = f"{lines[-1]} {word}".strip()
        if cv2.getTextSize(trial, font, scale, thickness)[0][0] <= width or not lines[-1]:
            lines[-1] = trial
        else:
            lines.append(word)
    while len(lines) > most:                 # squeeze the rest onto the last line
        lines[-2] = f"{lines[-2]} {lines.pop()}"
    return lines


def draw_page(template, cells, look, rng):
    """One page: printed header and lines, column rules, entries.
    cells: [{category: text}] per entry."""
    w, h = int(template["imageWidth"] * SCALE), int(template["imageHeight"] * SCALE)
    page = np.full((h, w, 3), 252, np.uint8)
    xs = [int(f * w) for f in template["gridLines"]] + [int(0.995 * w)]
    first, pitch = int(FIRST_LINE * SCALE), int(PITCH * SCALE)
    lines = (h - first) // pitch
    for k in range(lines):
        y = first + k * pitch
        cv2.line(page, (0, y), (w, y), (205, 160, 125), 2)
    for x in xs:
        cv2.line(page, (x, int(first - 2.4 * pitch)), (x, h - 10), (90, 70, 60), 3)
    cv2.line(page, (0, int(first - 2.4 * pitch)), (w, int(first - 2.4 * pitch)), (90, 70, 60), 3)
    for i, seg in enumerate(template["segmentInfo"]):
        if not seg.get("category") or i + 1 >= len(xs):
            continue
        cv2.putText(page, seg["category"], (xs[i] + 8, int(first - 1.25 * pitch)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (60, 50, 40), 2)
    font, scale, thickness, slant, ink = look
    for e, entry in enumerate(cells):
        for i, seg in enumerate(template["segmentInfo"]):
            text = entry.get(seg.get("category"))
            if not text or i + 1 >= len(xs):
                continue
            x1, x2 = xs[i] + 10, xs[i + 1] - 10
            for n, line in enumerate(_lines_for(text, x2 - x1, font, scale, thickness)):
                y = first + (e * PER_ENTRY + n) * pitch + int(pitch * 0.72) + rng.randint(-3, 3)
                cv2.putText(page, line, (x1 + rng.randint(0, 6), y), font, scale, ink, thickness, cv2.LINE_AA)
    if slant:
        shear = np.float32([[1, -slant * 0.15, slant * 0.15 * h / 2], [0, 1, 0]])
        page = cv2.warpAffine(page, shear, (w, h), borderValue=(252, 252, 252))
    noise = np.random.default_rng(rng.randint(0, 10**6)).normal(0, 3, page.shape)
    return np.clip(cv2.GaussianBlur(page, (3, 3), 0) + noise, 0, 255).astype(np.uint8)


def save_pdf(images, path):
    import fitz
    doc = fitz.open()
    for image in images:
        ok, png = cv2.imencode(".png", image)
        hgt, wid = image.shape[:2]
        page = doc.new_page(width=wid / 2, height=hgt / 2)   # load_pages renders at 2x
        page.insert_image(page.rect, stream=png.tobytes())
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


def draw_spread(patients, look, style, rng):
    templates = _templates()
    entries = []
    for p in patients:
        text = logbook_text(p)
        if style == "lower":
            text = {k: v.lower() for k, v in text.items()}
        entries.append({FIELD_TO_CATEGORY[k]: v for k, v in text.items()})
    left = draw_page(templates["odd"], entries, look, rng)
    right = draw_page(templates["even"], entries, look, rng)
    return [left, right], entries


# ── image quality samples ──────────────────────────────────────────────

def iq_variants(image):
    small = cv2.resize(image, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    return {
        "blurry": cv2.GaussianBlur(small, (0, 0), 6),
        "dark": np.clip(small.astype(np.float32) * 0.22, 0, 255).astype(np.uint8),
        "bright": np.clip(small.astype(np.float32) * 0.25 + 215, 0, 255).astype(np.uint8),
    }


def main():
    rng = random.Random(SEED)
    if SAMPLES.exists():
        shutil.rmtree(SAMPLES)
    (SAMPLES / "scans" / "handwriting").mkdir(parents=True)
    patients = fictional_patients(20, rng)

    writers, key_rows, iq_good = [], [], []
    plan = [(f"W{i:02d}", "caps" if i <= 5 else "lower", "main") for i in range(1, 11)]
    plan += [(f"R{i}", style, "same_writer") for i in range(1, 4) for style in ("caps", "lower")]
    for n, (writer, style, group) in enumerate(plan):
        look_index = (n if group == "main" else 10 + int(writer[1:])) % len(WRITER_LOOKS)
        chosen = [patients[(n * 3 + k) % len(patients)] for k in range(ENTRIES_PER_SPREAD)]
        images, entries = draw_spread(chosen, WRITER_LOOKS[look_index], style, rng)
        scan = f"{writer}_{style}.pdf"
        save_pdf(images, SAMPLES / "scans" / "handwriting" / scan)
        writers.append({"Writer ID": writer, "Style": style, "Set": group, "Scan File": scan,
                        "Notes": "computer-drawn sample"})
        for row, entry in enumerate(entries, start=1):
            for field, category in FIELD_TO_CATEGORY.items():
                page = 1 if category in ("CASE #", "DATE & TIME OF ADMISSION", "NAME", "BDAY", "ADDRESS") else 2
                key_rows.append([writer, style, page, row, field, entry.get(category, "")])
        if group == "main" and len(iq_good) < 4:
            iq_good.append((writer, images[0]))

    write_workbook(SAMPLES / "answer_key.xlsx", [
        {"name": "Handwriting", "headers": HANDWRITING_COLUMNS, "rows": key_rows},
        {"name": "Patients", "headers": PATIENT_COLUMNS, "rows": [[p[c] for c in PATIENT_COLUMNS] for p in patients]},
    ])
    with open(SAMPLES / "writers.csv", "w", newline="", encoding="utf-8") as fh:
        out = csv.DictWriter(fh, WRITER_COLUMNS)
        out.writeheader()
        out.writerows(writers)

    good, bad = SAMPLES / "iq" / "good", SAMPLES / "iq" / "bad"
    good.mkdir(parents=True)
    bad.mkdir(parents=True)
    expected = []
    for writer, image in iq_good:
        small = cv2.resize(image, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(good / f"{writer}_page1.png"), small)
        expected.append([f"good/{writer}_page1.png", "pass", "clear computer-drawn page"])
        for kind, variant in iq_variants(image).items():
            cv2.imwrite(str(bad / f"{writer}_page1_{kind}.png"), variant)
            expected.append([f"bad/{writer}_page1_{kind}.png", "warn", kind])
    with open(SAMPLES / "iq" / "expected.csv", "w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh)
        out.writerow(["File", "Expected", "Reason"])
        out.writerows(expected)

    from research_tests.make_templates import session_sheets
    sheets = session_sheets(example=False)
    log, errors, sugg, sus = sheets[0]["rows"], sheets[1]["rows"], sheets[2]["rows"], sheets[3]["rows"]
    for i in range(1, 6):
        pid = f"P{i}"
        for cond, base in (("manual", 700), ("system", 260)):
            for claim in (1, 2, 3):
                log.append([pid, "manual first" if i % 2 else "system first", cond, claim, f"R{claim + i:02d}",
                            "", "", base + rng.randint(-120, 120), "fictional sample"])
                for box in range(8):
                    wrong = rng.random() < (0.35 if cond == "manual" else 0.08)
                    errors.append([pid, cond, claim, f"R{claim + i:02d}", "CF1", f"box{box}", f"value{box % 5}", "",
                                   "REFERENCE", "WRONG" if wrong else "REFERENCE", "wrong value" if wrong else "", ""])
        for n in range(rng.randint(18, 26)):
            sugg.append([pid, 1 + n % 3, f"R{1 + n % 3 + i:02d}", "Address", "", "", rng.choice(
                ["accept"] * 6 + ["edit", "reject", "not acted on"]), "", ""])
        sus.append([pid] + [rng.choice([4, 5]) if q % 2 else rng.choice([1, 2]) for q in range(1, 11)])
    write_workbook(SAMPLES / "session_data.xlsx", sheets[:4])
    print(f"Sample inputs written to {SAMPLES}")


if __name__ == "__main__":
    main()
