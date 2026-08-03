"""
seed_users.py — Idempotently provision known accounts (roles + profiles).

Creates Firebase Auth accounts (when missing) and Firestore profiles for the
standard roles the application expects:

  * admin / supervisors used by the demo flows and issue assignment
  * the default student account

Run from the backend directory:

    python seed_users.py

Safe to run repeatedly — existing accounts and profiles are left untouched.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_admin import auth as admin_auth
from firebase_admin.auth import EmailAlreadyExistsError, UserNotFoundError

from services.firebase_admin import db  # noqa: F401  (initializes the SDK)
from services import users
from config import DEFAULT_CAMPUS_ID

# default password for seeded dev accounts
SEED_PASSWORD = "SCIARS123!"

# email -> (displayName, role, campusId)
SEED_ACCOUNTS = {
    "admin@campus.edu": ("Campus Admin", "admin", DEFAULT_CAMPUS_ID),
    "supervisor@campus.edu": ("Head Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "user1@gmail.com": ("Student User", "user", DEFAULT_CAMPUS_ID),
    # category supervisors used by issue assignment (CATEGORY_MAP in issues.py)
    "electrical@campus.edu": ("Electrical Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "water@campus.edu": ("Water Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "clean@campus.edu": ("Cleanliness Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "infra@campus.edu": ("Infrastructure Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "access@campus.edu": ("Accessibility Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "safety@campus.edu": ("Safety Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "transport@campus.edu": ("Transport Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "environment@campus.edu": ("Environment Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
}

# Optional per-account SMS language (ISO 639-1). Missing accounts default to
# "en" inside build_profile_payload. Change a value to demo localized SMS.
SEED_PREFERRED_LANGUAGES = {
    "supervisor@campus.edu": "te",
    "electrical@campus.edu": "hi",
}


def _get_or_create_auth_account(email: str):
    try:
        record = admin_auth.get_user_by_email(email)
        return record, False
    except UserNotFoundError:
        pass
    record = admin_auth.create_user(
        email=email,
        password=SEED_PASSWORD,
        email_verified=True,
        display_name=SEED_ACCOUNTS[email][0],
    )
    return record, True


def seed():
    created_auth, created_profiles, skipped = 0, 0, 0
    for email, (display_name, role, campus_id) in SEED_ACCOUNTS.items():
        record, is_new_auth = _get_or_create_auth_account(email)

        profile = users.get_user_profile(email)
        if profile:
            skipped += 1
            print(f"[skip] {email:<30} auth={'created' if is_new_auth else 'exists'} profile=exists")
            continue

        users.create_user_profile(
            uid=record.uid,
            email=email,
            display_name=display_name,
            campus_id=campus_id,
            role=role,
            preferred_language=SEED_PREFERRED_LANGUAGES.get(email),
        )
        created_profiles += 1
        created_auth += 1 if is_new_auth else 0
        print(f"[ok]   {email:<30} auth={'created' if is_new_auth else 'exists'} profile=created role={role}")

    print(f"\nDone. auth created: {created_auth}, profiles created: {created_profiles}, skipped: {skipped}")
    print(f"Seeded accounts use password: {SEED_PASSWORD}")


if __name__ == "__main__":
    seed()
