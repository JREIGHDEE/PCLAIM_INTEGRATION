"""User accounts: creation, password verification and lookup.

Supports the authentication and role-based access control described in the
research design (§3.4.2.7, §3.8). Follows the same conventions as
claims_store.py / case_session_store.py: raw PyMySQL via db.get_db_cursor(),
plain dicts in and out, no ORM.

Passwords are never stored or logged. Only a bcrypt hash is kept, which can
verify a password but cannot reveal it.
"""
import logging
import re

import bcrypt

from db import get_db_cursor
from errors import InvalidRequestError

logger = logging.getLogger(__name__)

ROLES = ("encoder", "admin")

# Columns safe to return to a caller. `password_hash` is deliberately absent
# so a hash can never leak into an API response or a log line.
PUBLIC_COLUMNS = "id, email, full_name, role, is_active, last_login_at, created_at"

# Deliberately loose: real clinic addresses vary, and the account is created
# by an administrator rather than self-registered, so this only catches typos.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 8


def normalize_email(email):
    return (email or "").strip().lower()


def hash_password(password):
    """bcrypt hash of `password`, as a str safe to store in VARCHAR."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidRequestError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    # bcrypt silently truncates beyond 72 bytes, so reject rather than let a
    # long passphrase be quietly shortened.
    if len(password.encode("utf-8")) > 72:
        raise InvalidRequestError("Password must be 72 bytes or fewer.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    """True when `password` matches the stored hash. Never raises on bad input."""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # A malformed/legacy hash must read as "wrong password", not crash.
        return False


def create_user(email, password, full_name, role="encoder"):
    """Create one account and return its public record."""
    email = normalize_email(email)
    full_name = (full_name or "").strip()

    if not _EMAIL_RE.match(email):
        raise InvalidRequestError("Enter a valid email address.")
    if not full_name:
        raise InvalidRequestError("Full name is required.")
    if role not in ROLES:
        raise InvalidRequestError(f"Role must be one of: {', '.join(ROLES)}.")

    password_hash = hash_password(password)

    with get_db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            raise InvalidRequestError("An account with that email already exists.")
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name, role) "
            "VALUES (%s, %s, %s, %s)",
            (email, password_hash, full_name, role))
        user_id = cur.lastrowid

    logger.info("Created user %s (role=%s)", email, role)
    return get_user_by_id(user_id)


def get_user_by_id(user_id):
    with get_db_cursor() as cur:
        cur.execute(f"SELECT {PUBLIC_COLUMNS} FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def get_user_by_email(email):
    with get_db_cursor() as cur:
        cur.execute(f"SELECT {PUBLIC_COLUMNS} FROM users WHERE email = %s",
                    (normalize_email(email),))
        return cur.fetchone()


def authenticate(email, password):
    """Return the user's public record when the credentials are valid, else None.

    Both "no such account" and "wrong password" return None, and a dummy hash
    is verified in the no-account case so that both paths take roughly the same
    time. Without that, response timing would reveal which emails are
    registered.
    """
    email = normalize_email(email)
    with get_db_cursor() as cur:
        cur.execute(
            f"SELECT {PUBLIC_COLUMNS}, password_hash FROM users WHERE email = %s",
            (email,))
        row = cur.fetchone()

    if row is None:
        verify_password(password, _DUMMY_HASH)
        logger.info("Failed sign-in for unknown email %s", email)
        return None

    stored_hash = row.pop("password_hash")
    if not verify_password(password, stored_hash):
        logger.info("Failed sign-in for %s (wrong password)", email)
        return None
    if not row["is_active"]:
        logger.info("Blocked sign-in for deactivated account %s", email)
        return None

    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (row["id"],))

    logger.info("Successful sign-in for %s (role=%s)", email, row["role"])
    return row


# A valid bcrypt hash of a value nobody can log in with, used only to keep
# failed-lookup timing similar to a real password check.
_DUMMY_HASH = bcrypt.hashpw(b"pclaimassist-timing-guard", bcrypt.gensalt()).decode("utf-8")


def list_users():
    with get_db_cursor() as cur:
        cur.execute(f"SELECT {PUBLIC_COLUMNS} FROM users ORDER BY full_name")
        return cur.fetchall()


def change_own_password(user_id, current_password, new_password):
    """Change a user's own password after re-checking the current one.

    Requiring the current password means someone who walks up to an
    unattended, already-signed-in workstation still cannot take the account
    over (§3.8, preventing unauthorized access).
    """
    with get_db_cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()

    if row is None:
        raise InvalidRequestError("Account not found.")
    if not verify_password(current_password, row["password_hash"]):
        raise InvalidRequestError("Your current password is incorrect.")
    if current_password == new_password:
        raise InvalidRequestError("The new password must be different from the current one.")

    set_password(user_id, new_password)


def set_password(user_id, new_password):
    password_hash = hash_password(new_password)
    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET password_hash = %s WHERE id = %s",
                    (password_hash, user_id))
    logger.info("Password changed for user id %s", user_id)


def set_active(user_id, is_active):
    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE users SET is_active = %s WHERE id = %s",
                    (1 if is_active else 0, user_id))
    return get_user_by_id(user_id)


def count_users():
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM users")
        return cur.fetchone()["n"]
