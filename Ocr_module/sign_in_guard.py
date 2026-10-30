"""Slowing down someone guessing a password.

Five wrong passwords for the same account close it for a minute. Five
more close it for five minutes, then for ten, and ten is as long as it
gets. A correct password clears the count, so a member of staff who
mistypes and then gets it right is never held up.

The count is kept per account, in this process's memory: no table, no
migration, and nothing to install. It is lost when the backend restarts,
which is the right trade for a clinic - a restart must never leave the
staff locked out of their own system - and a restart is not something a
guesser can ask for.

Counting by account, not by address: every request here comes from the
same machine, so counting by address would lock out the whole clinic the
moment one account was attacked.
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Wrong passwords allowed before the account closes.
ATTEMPTS_PER_LOCK = 5

# How long it stays closed: the first time, the second time, and after
# that. In seconds.
LOCK_SECONDS = (60, 300, 600)

# A quiet account is forgotten, so one typo this morning does not count
# towards a lock this afternoon.
FORGET_AFTER_SECONDS = 3600

_lock = threading.Lock()
_state = {}          # account -> {"wrong": int, "locks": int, "until": float, "seen": float}


def _key(email):
    return (email or "").strip().lower()


def _now():
    return time.monotonic()


def _expire(now):
    """Drop accounts nobody has touched for an hour."""
    for key in [k for k, v in _state.items()
                if now - v["seen"] > FORGET_AFTER_SECONDS and now >= v["until"]]:
        del _state[key]


def seconds_locked(email):
    """How many seconds until this account may try again (0 = it may)."""
    key = _key(email)
    if not key:
        return 0
    with _lock:
        entry = _state.get(key)
        if not entry:
            return 0
        left = entry["until"] - _now()
        return int(left) + 1 if left > 0 else 0


def attempts_left(email):
    """Wrong passwords still allowed before the account closes."""
    key = _key(email)
    if not key:
        return ATTEMPTS_PER_LOCK
    with _lock:
        entry = _state.get(key)
        wrong = entry["wrong"] if entry else 0
    return max(0, ATTEMPTS_PER_LOCK - wrong)


def record_failure(email):
    """A wrong password. Returns the seconds locked, 0 if not locked yet."""
    key = _key(email)
    if not key:
        return 0
    now = _now()
    with _lock:
        _expire(now)
        entry = _state.setdefault(key, {"wrong": 0, "locks": 0, "until": 0.0, "seen": now})
        entry["seen"] = now
        entry["wrong"] += 1
        if entry["wrong"] < ATTEMPTS_PER_LOCK:
            return 0
        # Another five wrong: close it, for longer than last time.
        wait = LOCK_SECONDS[min(entry["locks"], len(LOCK_SECONDS) - 1)]
        entry["locks"] += 1
        entry["wrong"] = 0
        entry["until"] = now + wait
        logger.warning("Sign-in closed for %s for %d seconds (%d time(s))",
                       key, wait, entry["locks"])
        return wait


def record_success(email):
    """The right password: forget everything counted against this account."""
    key = _key(email)
    if not key:
        return
    with _lock:
        _state.pop(key, None)


def describe_wait(seconds):
    """'1 minute' / '5 minutes', for telling the person what to do."""
    if seconds <= 60:
        return "1 minute"
    return f"{(seconds + 59) // 60} minutes"


def reset_all():
    """Used by the tests."""
    with _lock:
        _state.clear()
