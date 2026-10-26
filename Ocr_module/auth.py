"""Sign-in sessions and role checks.

Implements the authentication and role-based access control described in the
research design (§3.4.2.7, §3.8 Security Measures).

How a session works
-------------------
Flask's session is a cookie holding only a signed blob of {user_id, role}.
It is signed with SECRET_KEY, so a browser can read it but cannot forge or
edit it: any tampering invalidates the signature and the session is dropped.
The password is never in the cookie, and the role is re-read from the
database on every request, so deactivating an account takes effect at once
rather than when the cookie happens to expire.

Usage in a route:

    @review_bp.route("/upload", methods=["POST"])
    @login_required
    def upload_logbook():
        ...

    @admin_bp.route("/users", methods=["POST"])
    @role_required("admin")
    def create_account():
        ...
"""
import functools
import logging
import os

from flask import g, redirect, request, session, url_for

import user_store
from errors import AuthenticationRequiredError, PermissionDeniedError

logger = logging.getLogger(__name__)

_SESSION_USER_ID = "user_id"


def start_session(user):
    """Record a successful sign-in in the session cookie."""
    session.clear()
    session[_SESSION_USER_ID] = user["id"]
    session.permanent = True
    g.current_user = user


def end_session():
    session.clear()
    g.pop("current_user", None)


def current_user():
    """The signed-in user's record, or None.

    Re-read from the database once per request (cached on `g`) so that a
    deactivated or role-changed account is honoured immediately.
    """
    if "current_user" in g:
        return g.current_user

    user_id = session.get(_SESSION_USER_ID)
    if user_id is None:
        g.current_user = None
        return None

    user = user_store.get_user_by_id(user_id)
    if user is None or not user["is_active"]:
        # Account deleted or switched off since the cookie was issued.
        session.clear()
        user = None

    g.current_user = user
    return user


def login_required(view):
    """Reject the request unless someone is signed in."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            raise AuthenticationRequiredError("Please sign in to continue.")
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    """Reject the request unless the signed-in user holds one of `roles`."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                raise AuthenticationRequiredError("Please sign in to continue.")
            if user["role"] not in roles:
                logger.info("Denied %s (role=%s) access to %s",
                            user["email"], user["role"], view.__name__)
                raise PermissionDeniedError(
                    "Your account does not have permission to do this.")
            return view(*args, **kwargs)
        return wrapped
    return decorator


def public_user(user):
    """Shape a user record for an API response (never includes a hash)."""
    if not user:
        return None
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": bool(user.get("is_active")),
        "last_login_at": user["last_login_at"].isoformat()
                         if user.get("last_login_at") else None,
        "created_at": user["created_at"].isoformat()
                      if user.get("created_at") else None,
    }


# ── Signed in for everything but the sign-in page ─────────────────────────
# Every page and every API needs a signed-in, active account (current_user),
# except what the sign-in page itself uses: the page, its CSS/JS/images/
# fonts, sign-in, sign-up, sign-out, "is this a fresh install?" (status) and
# /db_health. Admin-only routes keep their own role_required check on top.
_PUBLIC_ENDPOINTS = {
    "pclaimassist_home",            # "/" - the sign-in page
    "db_health",
    "auth.login", "auth.register", "auth.status", "auth.logout",
}
_PUBLIC_FILES = {"login.html"}
_STATIC_EXTENSIONS = {
    ".css", ".js", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
}
# Pages (not JSON): someone signed out is sent to the sign-in page instead.
_PAGE_ENDPOINTS = {"ocr_workspace", "review", "logbook_setup.setup_page"}


def _requested_file():
    """The file name asked for through the frontend's file route, lower-case."""
    filename = (request.view_args or {}).get("filename") or ""
    return filename.replace("\\", "/").rsplit("/", 1)[-1].lower()


def require_sign_in(app):
    """Turn away anyone not signed in: pages redirect to the sign-in page,
    everything else answers 401 JSON (AuthenticationRequiredError)."""
    @app.before_request
    def sign_in_wall():
        endpoint = request.endpoint
        # Unknown URLs fall through to a plain 404; CORS preflights carry no cookie.
        if request.method == "OPTIONS" or endpoint is None or endpoint in _PUBLIC_ENDPOINTS:
            return None
        is_file = endpoint in ("pclaimassist_file", "static")
        name = _requested_file() if is_file else ""
        if is_file and (name in _PUBLIC_FILES or os.path.splitext(name)[1] in _STATIC_EXTENSIONS):
            return None
        if current_user() is not None:
            return None
        if endpoint in _PAGE_ENDPOINTS or (is_file and name.endswith(".html")):
            return redirect(url_for("pclaimassist_home"))
        raise AuthenticationRequiredError("Please sign in to continue.")
