"""Checking an email address without sending it anywhere.

Two questions, in order:

  1. Is it written like an address at all? (format)
  2. Does the part after the @ exist on the internet? (domain)

The second is what catches the real mistake - "gmial.com" for
"gmail.com" - and it is answered by asking DNS whether the domain
resolves, which is a lookup, not a message. Nothing is sent to the
address and nothing is sent to a third party: the patient's address
never leaves this computer.

A clinic with no internet gets "unknown" rather than "wrong": an
address cannot be called invalid just because the line is down.
"""
import logging
import re
import socket
import subprocess
from functools import lru_cache

logger = logging.getLogger(__name__)

# Deliberately not RFC 5322 in full: that grammar accepts things no
# clinic will ever type and is famously unreadable. This is the shape of
# an address as people actually write one.
_ADDRESS = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}$"
)

_MAX_LENGTH = 254          # RFC 3696 erratum 1690
_LOOKUP_TIMEOUT = 3.0      # seconds; a clinic should never wait longer

# The usual slips, so the message can say what was probably meant.
_COMMON_TYPOS = {
    "gmial.com": "gmail.com", "gmai.com": "gmail.com", "gmil.com": "gmail.com",
    "gmail.co": "gmail.com", "gmaill.com": "gmail.com", "gamil.com": "gmail.com",
    "yahooo.com": "yahoo.com", "yaho.com": "yahoo.com", "yahoo.co": "yahoo.com",
    "hotmai.com": "hotmail.com", "hotmial.com": "hotmail.com",
    "outlok.com": "outlook.com", "outloo.com": "outlook.com",
}


def _format_problem(address):
    """What is wrong with the way it is written, or None."""
    if not address:
        return "Please type an email address."
    if len(address) > _MAX_LENGTH:
        return "That email address is too long."
    if address.count("@") != 1:
        return ("An email address needs one @ sign."
                if address.count("@") != 1 else None)
    local, _, domain = address.partition("@")
    if not local:
        return "There is nothing before the @ sign."
    if not domain:
        return "There is nothing after the @ sign."
    if ".." in address:
        return "An email address cannot have two dots together."
    if not _ADDRESS.match(address):
        return "That does not look like an email address."
    return None


def _has_mx(domain):
    """True / False / None, from the domain's MX records via nslookup.

    A mail domain needs an MX record, and need not have a web server at
    all: addu.edu.ph has Google's mail exchangers and no A record, so
    asking getaddrinfo alone would call a real address a mistake.
    """
    try:
        out = subprocess.run(
            ["nslookup", "-type=MX", domain],
            capture_output=True, text=True, timeout=_LOOKUP_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    text = (out.stdout or "") + (out.stderr or "")
    low = text.lower()
    if "mail exchanger" in low:
        return True
    # Said plainly that there is no such name.
    if "nxdomain" in low or "can't find" in low or "no answer" in low:
        return False if "nxdomain" in low or "can't find" in low else None
    if out.returncode != 0:
        return None
    return None


@lru_cache(maxsize=512)
def _domain_resolves(domain):
    """True / False / None (could not tell - no internet).

    A domain is usable for mail if it has an MX record, or failing that
    an address record (some small domains take mail on the host itself).

    Cached: the same handful of domains come up all day, and a lookup
    the clinic has already paid for should not be paid for twice.
    """
    mx = _has_mx(domain)
    if mx is True:
        return True

    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(_LOOKUP_TIMEOUT)
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror as err:
        # Name genuinely not known -> the domain does not exist.
        if err.errno in (socket.EAI_NONAME, socket.EAI_NODATA):
            return False if mx is False else None
        return None          # temporary failure: no line, DNS down
    except (socket.timeout, OSError):
        return None
    finally:
        socket.setdefaulttimeout(previous)


def check_email(address):
    """{'ok', 'reason', 'suggestion', 'checked_domain'}.

    ok=True      the address is usable as far as we can tell
    ok=False     it is wrong, and `reason` says how
    """
    address = (address or "").strip()
    problem = _format_problem(address)
    if problem:
        return {"ok": False, "reason": problem, "suggestion": None,
                "checked_domain": False}

    domain = address.rpartition("@")[2].lower()

    fixed = _COMMON_TYPOS.get(domain)
    if fixed:
        local = address.rpartition("@")[0]
        return {"ok": False,
                "reason": f"Did you mean {local}@{fixed}?",
                "suggestion": f"{local}@{fixed}",
                "checked_domain": True}

    resolves = _domain_resolves(domain)
    if resolves is False:
        return {"ok": False,
                "reason": f"No such mail provider as “{domain}”. Please check the spelling.",
                "suggestion": None, "checked_domain": True}
    if resolves is None:
        # No internet: the format was fine, so let it through and say so.
        logger.info("Email domain %s could not be checked (no connection).", domain)
        return {"ok": True, "reason": None, "suggestion": None,
                "checked_domain": False}

    return {"ok": True, "reason": None, "suggestion": None,
            "checked_domain": True}
