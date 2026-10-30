"""Sign-in, sign-out and account management.

  GET  /api/auth/status                     -> {has_accounts} for the sign-in page
  POST /api/auth/register  name/email/password -> create your own account
                                               (first one: admin, signed in;
                                               later ones: wait for approval)
  POST /api/auth/login     email + password  -> starts a session
  POST /api/auth/logout                      -> ends the session
  GET  /api/auth/me                          -> who is signed in (or 401)
  POST /api/auth/password                    -> change your own password
  GET  /api/auth/users     (admin)           -> list accounts
  POST /api/auth/users     (admin)           -> create an account
  PATCH /api/auth/users/<id> (admin)         -> {is_active}: approve / switch off
  POST /api/auth/users/<id>/password (admin) -> set a new password for someone

Credentials are verified against the bcrypt hash in the `users` table; the
password itself is never stored, logged or returned.
"""
import logging

from flask import Blueprint, jsonify, request

import auth
import sign_in_guard
import user_store
from errors import InvalidCredentialsError, InvalidRequestError

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json_field(data, name):
    value = (data or {}).get(name)
    if not isinstance(value, str) or not value.strip():
        raise InvalidRequestError(f"{name} is required.")
    return value.strip()


@auth_bp.route("/status", methods=["GET"])
def status():
    """Lets the sign-in page say "the first account will be the
    administrator" on a fresh install. Reveals nothing about who exists."""
    return jsonify({"success": True, "has_accounts": user_store.count_users() > 0})


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    if not password:
        raise InvalidRequestError("password is required.")
    if password != (data.get("confirm_password") or ""):
        raise InvalidRequestError("The two passwords do not match.")

    user = user_store.register_user(
        email=_json_field(data, "email"),
        password=password,
        full_name=_json_field(data, "full_name"),
    )
    if user["is_active"]:
        # First account on a fresh install: the administrator, signed in now.
        auth.start_session(user)
    return jsonify({
        "success": True,
        "user": auth.public_user(user),
        "signed_in": bool(user["is_active"]),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = _json_field(data, "email")
    password = (data.get("password") or "")
    if not password:
        raise InvalidRequestError("password is required.")

    # Already closed from too many wrong passwords (sign_in_guard.py).
    # `locked_seconds` and `attempts_left` are for the sign-in page's
    # counter and countdown; the sentence alone cannot drive a timer.
    waiting = sign_in_guard.seconds_locked(email)
    if waiting:
        raise InvalidCredentialsError(
            "Too many wrong passwords. Please wait "
            f"{sign_in_guard.describe_wait(waiting)} and try again.",
            details={"locked_seconds": waiting, "attempts_left": 0})

    user = user_store.authenticate(email, password)
    if user is None:
        locked = sign_in_guard.record_failure(email)
        # One message for every failure mode, so this cannot be used to
        # discover which email addresses have accounts.
        if locked:
            raise InvalidCredentialsError(
                "Too many wrong passwords. Please wait "
                f"{sign_in_guard.describe_wait(locked)} and try again.",
                details={"locked_seconds": locked, "attempts_left": 0})
        raise InvalidCredentialsError(
            "Incorrect email or password.",
            details={"locked_seconds": 0,
                     "attempts_left": sign_in_guard.attempts_left(email)})

    sign_in_guard.record_success(email)
    auth.start_session(user)
    return jsonify({"success": True, "user": auth.public_user(user)})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    auth.end_session()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
@auth.login_required
def me():
    return jsonify({"success": True, "user": auth.public_user(auth.current_user())})


@auth_bp.route("/users", methods=["GET"])
@auth.role_required("admin")
def list_users():
    return jsonify({
        "success": True,
        "users": [auth.public_user(u) for u in user_store.list_users()],
    })


@auth_bp.route("/users", methods=["POST"])
@auth.role_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    user = user_store.create_user(
        email=_json_field(data, "email"),
        password=_json_field(data, "password"),
        full_name=_json_field(data, "full_name"),
        role=(data.get("role") or "encoder"),
    )
    return jsonify({"success": True, "user": auth.public_user(user)}), 201


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
@auth.role_required("admin")
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("is_active"), bool):
        raise InvalidRequestError("is_active (true or false) is required.")
    if user_id == auth.current_user()["id"] and not data["is_active"]:
        raise InvalidRequestError("You cannot switch off your own account.")
    user = user_store.set_active(user_id, data["is_active"])
    logger.info("Account %s set active=%s by %s",
                user_id, data["is_active"], auth.current_user()["email"])
    return jsonify({"success": True, "user": auth.public_user(user)})


@auth_bp.route("/users/<int:user_id>/password", methods=["POST"])
@auth.role_required("admin")
def reset_user_password(user_id):
    """An administrator sets a new password for a staff member who forgot
    theirs (there is no email reset, see login.html)."""
    data = request.get_json(silent=True) or {}
    user_store.set_password(user_id, data.get("new_password") or "")
    logger.info("Password for account %s reset by %s",
                user_id, auth.current_user()["email"])
    return jsonify({"success": True})


@auth_bp.route("/password", methods=["POST"])
@auth.login_required
def change_password():
    """Change your own password. The current one must be supplied again."""
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    if not current_password or not new_password:
        raise InvalidRequestError(
            "Both your current and new password are required.")

    user_store.change_own_password(
        auth.current_user()["id"], current_password, new_password)
    return jsonify({"success": True})
