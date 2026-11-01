"""Encryption of sensitive patient details in the database (adviser's
revision S4: "sensitive patient data encrypted").

What is encrypted (ENCRYPTED_COLUMNS): everything typed on the forms
(claims.form_values), the PhilHealth PINs, phone numbers, email and the
street-level address. The barangay, city, province and ZIP stay readable -
a coarse location, not a way to find one person - and so do the names and
birth dates, which the logbook review searches and sorts by.

How: Fernet (cryptography), i.e. AES-128 in CBC mode with an HMAC-SHA256
check, so a value that was tampered with fails to decrypt instead of being
read wrong. Stored as "enc1:<token>" so an older plain value (saved before
this, or written by a test) is recognised and read as it is; it is
encrypted the next time it is saved.

The key: DATA_ENCRYPTION_KEY in the environment (.env), else the file
Ocr_module/.data_key, created on first use and git-ignored, like
.secret_key. WITHOUT THE KEY THE ENCRYPTED DETAILS CANNOT BE READ: back it
up with the database (backup_db.bat dumps the database only).
"""
import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

PREFIX = "enc1:"
_KEY_FILE = Path(__file__).resolve().parent / ".data_key"

ENCRYPTED_COLUMNS = {
    "patients": frozenset({"pin", "address"}),
    "claims": frozenset({
        "form_values",
        "member_pin",
        "mobile", "home_phone", "employer_phone",
        "email",
        "addr_unit", "addr_building", "addr_lot", "addr_street",
    }),
}

# How much plain text each encrypted column holds: its size before
# database/migrations/011 made it TEXT for the longer encrypted value.
PLAINTEXT_MAX = {
    ("patients", "pin"): 20, ("patients", "address"): 255,
    ("claims", "member_pin"): 20,
    ("claims", "mobile"): 20, ("claims", "home_phone"): 20, ("claims", "employer_phone"): 20,
    ("claims", "email"): 100,
    ("claims", "addr_unit"): 100, ("claims", "addr_building"): 100,
    ("claims", "addr_lot"): 100, ("claims", "addr_street"): 100,
}

_fernet = None


def _load_key():
    from_env = os.environ.get("DATA_ENCRYPTION_KEY", "").strip()
    if from_env:
        return from_env.encode("ascii")
    if _KEY_FILE.exists():
        key = _KEY_FILE.read_text(encoding="ascii").strip()
        if key:
            return key.encode("ascii")
    key = Fernet.generate_key()
    _KEY_FILE.write_text(key.decode("ascii"), encoding="ascii")
    try:
        _KEY_FILE.chmod(0o600)
    except OSError:
        pass
    logger.warning("Created a new data encryption key at %s - back it up with the database.", _KEY_FILE)
    return key


def _cipher():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_key())
    return _fernet


def is_encrypted(value):
    return isinstance(value, str) and value.startswith(PREFIX)


def encrypt(value):
    """str -> "enc1:<token>". None and "" are kept as they are (an empty
    box stays empty, and NULL stays NULL); a value already encrypted is
    not encrypted twice."""
    if value is None or value == "" or is_encrypted(value):
        return value
    token = _cipher().encrypt(str(value).encode("utf-8")).decode("ascii")
    return PREFIX + token


def decrypt(value):
    """"enc1:<token>" -> the text; anything else (an older plain value,
    None, a number) is returned as it is."""
    if not is_encrypted(value):
        return value
    try:
        return _cipher().decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        # Wrong key, or the value was changed: never pass the token on as
        # if it were the patient's detail.
        logger.error("A stored value could not be decrypted (wrong DATA_ENCRYPTION_KEY or a changed value).")
        raise


def encrypt_fields(table, fields):
    """A copy of {column: value} with this table's sensitive columns encrypted."""
    columns = ENCRYPTED_COLUMNS.get(table)
    if not columns or not fields:
        return fields
    return {k: (encrypt(v) if k in columns else v) for k, v in fields.items()}


def decrypt_row(table, row):
    """The same row (a dict from the database) with its sensitive columns readable."""
    columns = ENCRYPTED_COLUMNS.get(table)
    if not columns or not row:
        return row
    for key in columns & row.keys():
        row[key] = decrypt(row[key])
    return row
