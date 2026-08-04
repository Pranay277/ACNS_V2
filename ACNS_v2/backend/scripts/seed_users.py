"""
seed_users.py — Idempotently provision known accounts (roles + profiles).

Creates Firebase Auth accounts (when missing) and Firestore profiles for the
standard roles the application expects:

  * admin / supervisors used by the demo flows and issue assignment
  * the default student account

Run from the backend directory:

    python scripts/seed_users.py

SAFETY
======
* This script is DEVELOPMENT-ONLY. It aborts unless ``ENVIRONMENT`` is set to
  ``development`` or ``local`` (see core/config.py DEV_ENVIRONMENTS).
* No password is ever hardcoded or printed. Every seeded account uses the
  shared development password provided via the ``SEED_ACCOUNT_PASSWORD``
  environment variable. If it is missing the script aborts with an error.
* The optional development admin account is created from backend/.env
  (ADMIN_SEED_EMAIL / ADMIN_SEED_PASSWORD / ADMIN_SEED_NAME); leave those
  unset to skip it.

REQUIRED ENVIRONMENT VARIABLES (backend/.env)
=============================================
  ENVIRONMENT=development   # development or local only; anything else aborts
  SEED_ACCOUNT_PASSWORD=... # password shared by all seeded dev accounts

  # Optional development admin account:
  ADMIN_SEED_EMAIL=...
  ADMIN_SEED_PASSWORD=...
  ADMIN_SEED_NAME=...

Safe to run repeatedly — existing accounts and profiles are left untouched.
"""

import sys
import os

# Make the backend root importable when run from anywhere:
#   python scripts/seed_users.py   (from backend/)
#   python seed_users.py           (from backend/scripts/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DEFAULT_CAMPUS_ID, DEV_ENVIRONMENTS

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

# ══ Environment variable name for the shared seeded-account password ═══════════
SEED_ACCOUNT_PASSWORD_VAR = "SEED_ACCOUNT_PASSWORD"


def _die(message: str) -> None:
    """Print an error to stderr and abort the script (never any stack trace)."""
    print(f"[seed_users] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _check_environment() -> None:
    """Refuse to run outside a development/local environment."""
    environment = os.environ.get("ENVIRONMENT", "").strip().lower()
    if environment not in DEV_ENVIRONMENTS:
        _die(
            "Refusing to run: ENVIRONMENT is not set to a development environment. "
            f"Set ENVIRONMENT={' or '.join(sorted(DEV_ENVIRONMENTS))} (current: "
            f"{environment or '<unset>'}). This script creates privileged "
            "accounts and must never run in production."
        )
    print(
        f"[seed_users] WARNING: Development-only script. ENVIRONMENT={environment}. "
        "Do not run against production projects."
    )


def _require_env(name: str, description: str) -> str:
    """Read a required environment variable, aborting if it is missing/empty."""
    value = os.environ.get(name, "").strip()
    if not value:
        _die(
            f"Missing required environment variable {name} ({description}). "
            "Set it in backend/.env and re-run."
        )
    return value


def _get_or_create_auth_account(email: str, password: str):
    from firebase_admin import auth as admin_auth
    from firebase_admin.auth import UserNotFoundError

    try:
        record = admin_auth.get_user_by_email(email)
        return record, False
    except UserNotFoundError:
        pass
    record = admin_auth.create_user(
        email=email,
        password=password,
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


def _seed_admin_from_env(profile_service):
    if not ADMIN_SEED_EMAIL or not ADMIN_SEED_PASSWORD:
        print(
            "[seed_users] WARNING: ADMIN_SEED_EMAIL/ADMIN_SEED_PASSWORD not set; "
            "skipping the optional dev admin account."
        )
        return

    if profile_service.get_user_profile(ADMIN_SEED_EMAIL):
        print(f"[skip] {ADMIN_SEED_EMAIL:<30} admin profile already exists")
        return

    from firebase_admin import auth as admin_auth
    from firebase_admin.auth import UserNotFoundError

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
    # Gate first: refuse to run in production, then require the password from
    # the environment BEFORE any Firebase SDK is initialized.
    _check_environment()
    seed_password = _require_env(
        SEED_ACCOUNT_PASSWORD_VAR, "password shared by all seeded dev accounts"
    )

    from core.firebase import db  # noqa: F401  (initializes the SDK)
    from features.profile import service as profile_service

    created_auth, created_profiles, skipped = 0, 0, 0
    for email, (display_name, role, campus_id) in SEED_ACCOUNTS.items():
        record, is_new_auth = _get_or_create_auth_account(email, seed_password)

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
    print("Seeded accounts use the password from the "
          f"{SEED_ACCOUNT_PASSWORD_VAR} environment variable.")
    print("\n── Development admin (env-driven) ──")
    _seed_admin_from_env(profile_service)


if __name__ == "__main__":
    seed()
