"""Sign-in, sign-out and account management.

  POST /api/auth/login    email + password  -> starts a session
  POST /api/auth/logout                     -> ends the session
  GET  /api/auth/me                         -> who is signed in (or 401)
  GET  /api/auth/users    (admin)           -> list accounts
  POST /api/auth/users    (admin)           -> create an account

Credentials are verified against the bcrypt hash in the `users` table; the
password itself is never stored, logged or returned.
"""
import logging

from flask import Blueprint, jsonify, request

import auth
import user_store
from errors import InvalidCredentialsError, InvalidRequestError

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json_field(data, name):
    value = (data or {}).get(name)
    if not isinstance(value, str) or not value.strip():
        raise InvalidRequestError(f"{name} is required.")
    return value.strip()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = _json_field(data, "email")
    password = (data.get("password") or "")
    if not password:
        raise InvalidRequestError("password is required.")

    user = user_store.authenticate(email, password)
    if user is None:
        # One message for every failure mode, so this cannot be used to
        # discover which email addresses have accounts.
        raise InvalidCredentialsError("Incorrect email or password.")

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
