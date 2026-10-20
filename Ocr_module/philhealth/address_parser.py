"""Logbook address (one line of free text) -> the PMRF/CSF address parts.

The logbook has one ADDRESS column, written however staff write it:

    "PUROK 12, BRGY. CABANTIAN, DAVAO CITY"
    "BLK 8 LOT 1 EMILY HOMES CABANTIAN, DC"
    "KM 16 FATIMA INDANGAN DAVAO CITY"
    "-DO-"                                    (ditto: same as the row above)

The forms want it in parts (claims.addr_lot / addr_street /
addr_subdivision / addr_barangay / addr_city / addr_province).
split_address() does the split with plain rules: keywords (BRGY, BLK,
LOT, PUROK, ... HOMES, ... CITY), a list of known barangays, and the city
each belongs to. It never makes up a part it can't see: a part it can't
find is left out, and whatever is left over goes to Street. Every part is
shown on the forms as "From scan - please check" (philhealth/form_prefill).

Pure (no DB). The barangay list is Davao City's, where the clinic is; a
clinic elsewhere adds its own city to KNOWN_BARANGAYS / CITIES.
"""
import difflib
import re

# City as written -> (city, province) as the forms want them.
CITIES = {
    "DAVAO CITY": ("DAVAO CITY", "DAVAO DEL SUR"),
    "TAGUM CITY": ("TAGUM CITY", "DAVAO DEL NORTE"),
    "PANABO CITY": ("PANABO CITY", "DAVAO DEL NORTE"),
    "SAMAL": ("ISLAND GARDEN CITY OF SAMAL", "DAVAO DEL NORTE"),
    "DIGOS CITY": ("DIGOS CITY", "DAVAO DEL SUR"),
    "MATI CITY": ("MATI CITY", "DAVAO ORIENTAL"),
    "CAGAYAN DE ORO CITY": ("CAGAYAN DE ORO CITY", "MISAMIS ORIENTAL"),
    "GENERAL SANTOS CITY": ("GENERAL SANTOS CITY", "SOUTH COTABATO"),
    "KIDAPAWAN CITY": ("KIDAPAWAN CITY", "COTABATO"),
}
# How the logbook writes them: "DAVAO CITY", "DAVAO", "DC", "D.C.", "TAGUM".
_CITY_PATTERNS = [
    (re.compile(r"\bDAVAO\s*CITY\b|\bDAVAO\b|\bD\.?\s?C\b\.?"), "DAVAO CITY"),
    (re.compile(r"\bTAGUM(\s*CITY)?\b"), "TAGUM CITY"),
    (re.compile(r"\bPANABO(\s*CITY)?\b"), "PANABO CITY"),
    (re.compile(r"\b(IGACOS|SAMAL(\s*ISLAND)?)\b"), "SAMAL"),
    (re.compile(r"\bDIGOS(\s*CITY)?\b"), "DIGOS CITY"),
    (re.compile(r"\bMATI(\s*CITY)?\b"), "MATI CITY"),
    (re.compile(r"\b(CAGAYAN\s+DE\s+ORO|CDO)(\s*CITY)?\b"), "CAGAYAN DE ORO CITY"),
    (re.compile(r"\b(GENERAL|GEN\.?)\s+SANTOS(\s*CITY)?\b|\bGENSAN\b"), "GENERAL SANTOS CITY"),
    (re.compile(r"\bKIDAPAWAN(\s*CITY)?\b"), "KIDAPAWAN CITY"),
]

# Barangays of Davao City (city -> names), for addresses written without
# "BRGY." ("... EMILY HOMES CABANTIAN, DC").
KNOWN_BARANGAYS = {
    "DAVAO CITY": (
        "ACACIA", "AGDAO", "ALAMBRE", "ANGALAN", "BAGO APLAYA", "BAGO GALLERA", "BAGO OSHIRO",
        "BAGUIO", "BALENGAENG", "BALIOK", "BANGKAS HEIGHTS", "BANTOL", "BARACATAN", "BATO",
        "BAYABAS", "BIAO ESCUELA", "BIAO GUIANGA", "BIAO JOAQUIN", "BINUGAO", "BUCANA", "BUDA",
        "BUHANGIN", "BUNAWAN", "CABANTIAN", "CADALIAN", "CALINAN", "CALLAWA", "CAMANSI",
        "CARMEN", "CATALUNAN GRANDE", "CATALUNAN PEQUENO", "CATIGAN", "CAWAYAN", "COLOSAS",
        "COMMUNAL", "CROSSING BAYABAS", "DACUDAO", "DALAG", "DALAGDAG", "DALIAO", "DUMOY",
        "EDEN", "FATIMA", "GATUNGAN", "GUMALANG", "GUMITAN", "ILANG", "INAYANGAN", "INDANGAN",
        "KILATE", "LACSON", "LAMANAN", "LAMPIANAO", "LANGUB", "LAPU-LAPU", "LASANG",
        "LEON GARCIA", "LIZADA", "LOS AMIGOS", "LUBOGAN", "LUMIAD", "MA-A", "MABUHAY",
        "MAGSAYSAY", "MAGTUOD", "MAHAYAG", "MALABOG", "MALAGOS", "MALAMBA", "MANAMBULAN",
        "MANDUG", "MANUEL GUIANGA", "MAPULA", "MARAPANGI", "MARILOG", "MATINA APLAYA",
        "MATINA BIAO", "MATINA CROSSING", "MATINA PANGI", "MEGKAWAYAN", "MINTAL", "MUDIANG",
        "MULIG", "NEW CARMEN", "NEW VALENCIA", "PAMPANGA", "PANACAN", "PANALUM", "PANDAITAN",
        "PANGYAN", "PAQUIBATO", "PARADISE EMBAK", "RIVERSIDE", "SALAPAWAN", "SALAYSAY",
        "SALOY", "SAN ANTONIO", "SAN ISIDRO", "SANTO NINO", "SASA", "SIBULAN", "SIRAWAN",
        "SIRIB", "SUBASTA", "SUMIMAO", "TACUNAN", "TAGAKPAN", "TAGLUNO", "TAGURANO",
        "TALANDANG", "TALOMO", "TAMAYONG", "TAMBOBONG", "TAMUGAN", "TAPAK", "TAWAN-TAWAN",
        "TIBULOY", "TIBUNGCO", "TIGATTO", "TORIL", "TUGBOK", "TUNGAKALAN", "UBALDE", "ULA",
        "WAAN", "WANGAN", "WILFREDO AQUINO", "WINES",
    ),
}
_BARANGAY_CITY = {name: city for city, names in KNOWN_BARANGAYS.items() for name in names}
# Longest first, so "MATINA CROSSING" wins over a shorter name inside it.
_BARANGAYS = sorted(_BARANGAY_CITY, key=len, reverse=True)

# A province written out ("DAVAO DEL SUR"): taken first, so its "DAVAO"
# isn't read as the city.
_PROVINCE = re.compile(r"\bDAVAO\s+(DEL\s+(SUR|NORTE)|ORIENTAL|OCCIDENTAL|DE\s+ORO)\b")
# Any other "<NAME> CITY": the city, province unknown. One word only: in a
# misread address the word before that is usually part of something else.
_OTHER_CITY = re.compile(r"\b([A-Z][A-Z\-]{2,})\s+CITY\b")
_PHASE = re.compile(r"\bPHASE\s*(\w+)")
_DITTO = re.compile(r"^\W*(D[O0]|DITTO|SAME(\s+AS\s+ABOVE)?|\"+|〃)\W*$")
_BARANGAY_WORD = re.compile(r"\b(BRGY|BRGY|BGY|BRG|BARANGAY|BRY)\b\.?")
_LOT = re.compile(r"\b(?:BLK|BLOCK|BL)\.?\s*(\w+)\s*,?\s*(?:LOT|LT)\.?\s*(\w+)|\b(?:LOT|LT)\.?\s*(\w+)")
_SUBDIVISION = re.compile(
    r"((?:[A-Z][A-Z\-']*\s+){1,2})(HOMES|HOMESITE|VILLAGE|VILL|SUBDIVISION|SUBD|HEIGHTS|HTS|ESTATES?|"
    r"RESIDENCES|TOWNHOMES|PARK)\b\.?(\s+PHASE\s*\w+)?")
# Words that say where something is, not part of its name ("BESIDE EMILY HOMES").
_NOT_A_NAME = {"BESIDE", "BESIDES", "NEAR", "BEHIND", "INFRONT", "FRONT", "ALONG", "OF", "AT", "THE", "IN"}


def is_ditto(text):
    """True for a ditto mark ("-DO-", "do", "same"): same as the row above."""
    return bool(_DITTO.match(str(text or "").upper()))


def _tidy(text):
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(" ,.-")


def _take(text, match):
    """text with a match blanked out (kept apart from its neighbours)."""
    return text[:match.start()] + " , " + text[match.end():]


def _find_barangay(text, city=None):
    """(name, match span) of a known barangay in text - of `city` when the
    address names one - allowing one or two OCR letter slips in a long name
    ("PATIMA" for "FATIMA")."""
    names = [n for n in _BARANGAYS if city is None or _BARANGAY_CITY[n] == city]
    for name in names:
        found = re.search(r"\b" + re.escape(name) + r"\b", text)
        if found:
            return name, found.span()
    words = list(re.finditer(r"[A-Z][A-Z\-]{4,}", text))
    singles = [n for n in names if " " not in n and len(n) >= 5]
    for word in words:
        close = difflib.get_close_matches(word.group(), singles, n=1, cutoff=0.82)
        if close:
            return close[0], word.span()
    return None, None


def split_address(text):
    """{"addr_lot", "addr_street", "addr_subdivision", "addr_barangay",
    "addr_city", "addr_province"} - only the parts found - for one logbook
    address. A known barangay written without its city gets that city.
    {} for a blank address or a ditto mark (the caller uses the row above
    instead)."""
    raw = str(text or "").upper().strip()
    if not raw or is_ditto(raw):
        return {}
    rest = re.sub(r"\s+", " ", raw.replace(";", ","))
    parts = {}

    found = _PROVINCE.search(rest)
    if found:
        parts["addr_province"] = re.sub(r"\s+", " ", found.group())
        rest = _take(rest, found)

    for pattern, key in _CITY_PATTERNS:
        found = pattern.search(rest)
        if found:
            parts["addr_city"], province = CITIES[key]
            parts.setdefault("addr_province", province)
            rest = _take(rest, found)
            break
    else:
        found = _OTHER_CITY.search(rest)
        if found:
            parts["addr_city"] = f"{found.group(1)} CITY"
            rest = _take(rest, found)

    phase = _PHASE.search(rest)
    if phase:
        rest = _take(rest, phase)

    found = _LOT.search(rest)
    if found:
        block, lot, lone = found.groups()
        parts["addr_lot"] = f"BLK {block} LOT {lot}" if block else f"LOT {lone}"
        rest = _take(rest, found)

    found = _SUBDIVISION.search(rest)
    if found:
        words = [w for w in found.group(1).split() if w not in _NOT_A_NAME]
        if words:
            # "PHASE 1" belongs to the subdivision, before or after its name.
            phase_text = (found.group(3) or "").strip() or (f"PHASE {phase.group(1)}" if phase else "")
            parts["addr_subdivision"] = " ".join(words + [found.group(2)] + ([phase_text] if phase_text else []))
            rest = _take(rest, found)
            phase = None
    if phase:  # a phase with no subdivision found: keep it in the street
        rest = rest + " " + phase.group()

    # "BRGY. CABANTIAN": the name after the word, up to a comma.
    found = _BARANGAY_WORD.search(rest)
    if found:
        after = re.match(r"\s*([A-Z0-9][A-Z0-9\-\. ]*?)\s*(,|$)", rest[found.end():])
        name = after.group(1).strip(" .") if after else ""
        if name:
            parts["addr_barangay"] = name
            rest = rest[:found.start()] + " , " + rest[found.end() + after.end(1):]
        else:
            rest = _take(rest, found)  # "BRGY." with the name lost: look it up below
    if "addr_barangay" not in parts:
        name, span = _find_barangay(rest, parts.get("addr_city"))
        if name:
            parts["addr_barangay"] = name
            rest = rest[:span[0]] + " , " + rest[span[1]:]

    # A known barangay written without its city: that barangay's city.
    barangay_city = _BARANGAY_CITY.get(parts.get("addr_barangay"))
    if "addr_city" not in parts and barangay_city in CITIES:
        parts["addr_city"], province = CITIES[barangay_city]
        parts.setdefault("addr_province", province)

    # Whatever is left (PUROK 12, KM 16, a street name) is the street.
    leftover = [w for w in _tidy(rest).replace(",", " ").split()
                if w not in _NOT_A_NAME and re.search(r"[A-Z0-9]", w)]
    if leftover:
        parts["addr_street"] = _tidy(" ".join(leftover))
    return {k: v for k, v in parts.items() if v}
