"""Create the first administrator account.

Run once per clinic install, before anyone can sign in:

    venv/bin/python create_admin.py

It asks for a name, email and password, then writes one `admin` user. After
that, further accounts are created from inside the app by an administrator,
so this script is only ever needed to bootstrap an empty database.

The password is typed invisibly (getpass) and only its bcrypt hash is stored.
"""
import getpass
import sys

import user_store
from errors import OCRAppError


def main():
    try:
        existing = user_store.count_users()
    except OCRAppError as exc:
        print(f"\nCould not reach the database: {exc}")
        print("Is MariaDB running?  brew services start mariadb\n")
        return 1

    if existing:
        print(f"\nThis database already has {existing} account(s).")
        print("Create further accounts from inside the app, signed in as an admin.\n")
        return 1

    print("\n=== Create the first PClaimAssist administrator ===\n")
    full_name = input("Full name      : ").strip()
    email = input("Email          : ").strip()
    password = getpass.getpass("Password       : ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("\nThose passwords do not match. Nothing was saved.\n")
        return 1

    try:
        user = user_store.create_user(
            email=email, password=password, full_name=full_name, role="admin")
    except OCRAppError as exc:
        print(f"\n{exc}\n")
        return 1

    print(f"\nCreated admin account for {user['email']}.")
    print("You can now sign in at the PClaimAssist login page.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
