"""
Builds PClaimAssist/js/ph-psgc.js: every province, city/municipality and
barangay of the Philippines, for the address lists on Patient details
(adviser's revision S3: address dropdowns instead of free text).

The names come from the Philippine Standard Geographic Code (PSGC) of the
Philippine Statistics Authority, as published in JSON by the PSGC API
(https://psgc.gitlab.io/api/). Run again when PSA publishes a new PSGC:

    Ocr_module\\venv\\Scripts\\python.exe tools\\build_ph_address.py
    Ocr_module\\venv\\Scripts\\python.exe tools\\build_ph_address.py <folder>

With a folder, it reads regions.json, provinces.json,
cities-municipalities.json and barangays.json from there instead of
downloading them.

Written the way the forms already write them:
  - "City of Tagum" -> "Tagum City" (the zip codes in js/app.js and the
    clinic's claims say "TAGUM CITY"), and "City of Manila" -> "Manila";
  - "Davao Del Sur" -> "Davao del Sur";
  - Metro Manila's cities, which have no province, under "Metro Manila";
    Isabela City under Basilan and Cotabato City under Maguindanao, the
    provinces they stand in;
  - Davao City's Poblacion barangays as "1-A" ... "40-D", not
    "Barangay 1-A (Pob.)", as the clinic has always written them.
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

API = "https://psgc.gitlab.io/api/{}/"
OUT = Path(__file__).resolve().parent.parent / "PClaimAssist" / "js" / "ph-psgc.js"

NO_PROVINCE = {
    "099701000": "Basilan",          # City of Isabela
    "129804000": "Maguindanao",      # City of Cotabato
}
METRO_MANILA = "130000000"           # NCR region code
DAVAO_CITY = "112402000"


def load(name, folder):
    if folder:
        return json.loads((Path(folder) / f"{name}.json").read_text(encoding="utf-8"))
    with urllib.request.urlopen(API.format(name), timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def province_name(name):
    return re.sub(r"\b(Del|De)\b", lambda m: m.group(1).lower(), name)


def city_name(name):
    if name == "City of Manila":
        return "Manila"
    m = re.fullmatch(r"City of (.+)", name)
    return f"{m.group(1)} City" if m else name


def barangay_name(name, city_code):
    if city_code == DAVAO_CITY:
        m = re.fullmatch(r"Barangay (\d+-[A-D]) \(Pob\.\)", name)
        if m:
            return m.group(1)
    return name


def build(folder=None):
    provinces = {p["code"]: province_name(p["name"]) for p in load("provinces", folder)}
    cities = {}
    for c in load("cities-municipalities", folder):
        if c["provinceCode"]:
            province = provinces[c["provinceCode"]]
        elif c["regionCode"] == METRO_MANILA:
            province = "Metro Manila"
        else:
            province = NO_PROVINCE[c["code"]]   # a new one fails here, on purpose
        cities[c["code"]] = (province, city_name(c["name"]))

    data = {}
    for b in load("barangays", folder):
        code = b["cityCode"] or b["municipalityCode"]
        province, city = cities[code]
        data.setdefault(province, {}).setdefault(city, []).append(barangay_name(b["name"], code))
    # A city or municipality with no barangay listed still gets its box.
    for province, city in cities.values():
        data.setdefault(province, {}).setdefault(city, [])

    packed = {p: {c: "|".join(sorted(set(names))) for c, names in sorted(data[p].items())}
              for p in sorted(data)}
    count = sum(len(n.split("|")) for cs in packed.values() for n in cs.values() if n)
    header = (
        "/* PClaimAssist - every province, city/municipality and barangay of the\n"
        "   Philippines, from the Philippine Standard Geographic Code (Philippine\n"
        "   Statistics Authority), via https://psgc.gitlab.io/api/.\n"
        f"   Made by tools/build_ph_address.py on {date.today().isoformat()}: "
        f"{len(packed)} provinces, {len(cities)} cities and municipalities,\n"
        f"   {count} barangays. Do not edit by hand - run the tool again.\n"
        "   Each city's barangays are one string, split by js/ph-address.js. */\n")
    OUT.write_text(header + "window.PH_PSGC = " + json.dumps(packed, ensure_ascii=False, separators=(",", ":"))
                   + ";\n", encoding="utf-8")
    print(f"{OUT}: {len(packed)} provinces, {len(cities)} cities/municipalities, {count} barangays, "
          f"{OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
