"""
seed_users.py — Idempotently provision known accounts (roles + profiles).

Creates Firebase Auth accounts (when missing) and Firestore profiles for the
standard roles the application expects:

  * admin / supervisors used by the demo flows and issue assignment
  * the default student account

Run from the backend directory:

    python scripts/seed_users.py

Safe to run repeatedly — existing accounts and profiles are left untouched.
An optional development admin account is created from backend/.env
(ADMIN_SEED_EMAIL / ADMIN_SEED_PASSWORD / ADMIN_SEED_NAME); leave those
unset to skip it.
"""

import sys
import os

# Make the backend root importable when run from anywhere:
#   python scripts/seed_users.py   (from backend/)
#   python seed_users.py           (from backend/scripts/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_admin import auth as admin_auth
from firebase_admin.auth import EmailAlreadyExistsError, UserNotFoundError

from core.config import DEFAULT_CAMPUS_ID
from core.firebase import db  # noqa: F401  (initializes the SDK)
from features.profile import service as profile_service

# default password for seeded dev accounts
SEED_PASSWORD = "SCIARS123!"

# email -> (displayName, role, campusId)
SEED_ACCOUNTS = {
    "admin@campus.edu": ("Campus Admin", "admin", DEFAULT_CAMPUS_ID),
    "supervisor@campus.edu": ("Head Supervisor", "supervisor", DEFAULT_CAMPUS_ID),
    "user1@gmail.com": ("Student User", "user", DEFAULT_CAMPUS_ID),
    # category supervisors used by issue assignment (department routing in
    # features/supervisors/service.py, category map in core/config.py)
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

# Department each category supervisor owns — the PRIMARY lookup key used by
# issue assignment (CATEGORY_TO_DEPARTMENT in core/config.py). The head
# supervisor has no department; it is not reachable via category routing.
SEED_DEPARTMENTS = {
    "electrical@campus.edu": "Electrical",
    "water@campus.edu": "Water",
    "clean@campus.edu": "Cleanliness",
    "infra@campus.edu": "Infrastructure",
    "access@campus.edu": "Accessibility",
    "safety@campus.edu": "Safety",
    "transport@campus.edu": "Transport",
    "environment@campus.edu": "Environment",
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


# ══ Env-driven development admin ══════════════════════════════════════════════
# Read from backend/.env — credentials are NEVER hardcoded in application
# logic. Leave ADMIN_SEED_EMAIL / ADMIN_SEED_PASSWORD empty to skip. If the
# account already exists it is left untouched (idempotent).
ADMIN_SEED_EMAIL = os.environ.get("ADMIN_SEED_EMAIL", "").strip().lower()
ADMIN_SEED_PASSWORD = os.environ.get("ADMIN_SEED_PASSWORD", "").strip()
ADMIN_SEED_NAME = os.environ.get("ADMIN_SEED_NAME", "Pranay").strip() or "Pranay"


def _seed_admin_from_env():
    if not ADMIN_SEED_EMAIL or not ADMIN_SEED_PASSWORD:
        print("[skip] No ADMIN_SEED_EMAIL/ADMIN_SEED_PASSWORD set; skipping env admin.")
        return

    if profile_service.get_user_profile(ADMIN_SEED_EMAIL):
        print(f"[skip] {ADMIN_SEED_EMAIL:<30} admin profile already exists")
        return

    try:
        record = admin_auth.get_user_by_email(ADMIN_SEED_EMAIL)
        is_new_auth = False
    except UserNotFoundError:
        record = admin_auth.create_user(
            email=ADMIN_SEED_EMAIL,
            password=ADMIN_SEED_PASSWORD,
            email_verified=True,
            display_name=ADMIN_SEED_NAME,
        )
        is_new_auth = True

    profile_service.create_user_profile(
        uid=record.uid,
        email=ADMIN_SEED_EMAIL,
        display_name=ADMIN_SEED_NAME,
        campus_id=DEFAULT_CAMPUS_ID,
        role="admin",
    )
    print(
        f"[ok]   {ADMIN_SEED_EMAIL:<30} auth={'created' if is_new_auth else 'exists'} "
        f"profile=created role=admin"
    )


def seed():
    created_auth, created_profiles, skipped = 0, 0, 0
    for email, (display_name, role, campus_id) in SEED_ACCOUNTS.items():
        record, is_new_auth = _get_or_create_auth_account(email)

        profile = profile_service.get_user_profile(email)
        if profile:
            skipped += 1
            print(f"[skip] {email:<30} auth={'created' if is_new_auth else 'exists'} profile=exists")
            continue

        profile_service.create_user_profile(
            uid=record.uid,
            email=email,
            display_name=display_name,
            campus_id=campus_id,
            role=role,
            preferred_language=SEED_PREFERRED_LANGUAGES.get(email),
            department=SEED_DEPARTMENTS.get(email),
        )
        created_profiles += 1
        created_auth += 1 if is_new_auth else 0
        print(f"[ok]   {email:<30} auth={'created' if is_new_auth else 'exists'} profile=created role={role}")

    print(f"\nDone. auth created: {created_auth}, profiles created: {created_profiles}, skipped: {skipped}")
    print(f"Seeded accounts use password: {SEED_PASSWORD}")
    print("\n── Development admin (env-driven) ──")
    _seed_admin_from_env()


if __name__ == "__main__":
    seed()
