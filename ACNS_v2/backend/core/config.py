"""
core/config.py — Centralized configuration.

All point values, collection names, limits, and env-driven settings live here
so that tuning a value (e.g. the reward for a valid report, the frontend base
URL used in SMS links) requires editing ONLY this file — no other module should
hard-code them.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # backend/.env holds secrets + env-driven settings (gitignored).
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # pragma: no cover — dotenv is optional in bare envs
    pass


def _int_env(name: str, default: int) -> int:
    """Read an integer setting from the environment; fall back to ``default``."""
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default

# ── Reward reasons ─────────────────────────────────────────────────────────────
REWARD_REPORT_ISSUE = "report_issue"
REWARD_CONFIRM_ISSUE = "confirm_issue"
REWARD_VERIFIED_ISSUE = "verified_issue"
REWARD_DUPLICATE_REPORT = "duplicate_report"

# ── Point values (single source of truth) ─────────────────────────────────────
#   report_issue  = new issue created by the user (Rule 1)
#   confirm_issue = existing issue confirmed by a *different* user (Rule 2)
#   duplicate_report = same user reporting the same issue again (Rule 3) -> 0
POINTS_BY_REWARD = {
    REWARD_REPORT_ISSUE: 10,
    REWARD_CONFIRM_ISSUE: 5,
    REWARD_VERIFIED_ISSUE: 20,
    REWARD_DUPLICATE_REPORT: 0,
}

# ── Firestore layout ───────────────────────────────────────────────────────────
# One document per user, keyed by the Firebase Auth UID, e.g.
#   gamification_users/{uid}
#     . totalPoints, issuesReported, issuesResolved, displayName, lastUpdated
#   gamification_users/{uid}/points_history/{event_key}   (idempotency/audit)
GAMIFICATION_COLLECTION = "gamification_users"
GAMIFICATION_HISTORY_SUBCOLLECTION = "points_history"

# ── Leaderboard limits ─────────────────────────────────────────────────────────
LEADERBOARD_DEFAULT_LIMIT = 10
LEADERBOARD_MAX_LIMIT = 100

# ── Duplicate detection ─────────────────────────────────────────────────────────
# Campus-friendly duplicate radius in meters. Issues are duplicates only when
# they share the same campus, building/landmark and category, are Open or
# In Progress, and sit within this distance of each other.
DUPLICATE_RADIUS_METERS = 25

# ══ Issue workflow / supervisor assignment ══════════════════════════════════════
# Department is the PRIMARY lookup key for issue assignment. A new issue is
# routed category -> department -> the active supervisor whose ``supervisors/{uid}``
# profile carries that ``department`` field (resolved by
# ``features/supervisors/service.py``). The addresses below are mirrored by the
# ``seed_users.py`` accounts and the demo flows, so keep them in sync.
CATEGORY_TO_DEPARTMENT = {
    "Electrical": "Electrical",
    "Water": "Water",
    "Cleanliness": "Cleanliness",
    "Infrastructure": "Infrastructure",
    "Accessibility": "Accessibility",
    "Safety": "Safety",
    "Transport": "Transport",
    "Environment": "Environment",
}

# ══ Department catalog (P2-09) ═════════════════════════════════════════════════
# The authoritative list of departments a supervisor may be assigned to. It is
# derived from CATEGORY_TO_DEPARTMENT so the catalog can never drift from the
# routing table (frontend mirrors it in constants/departments.js — keep in sync
# when either side changes). Supervisor departments MUST come from this catalog;
# anything else is rejected by shared/utils/validators.validate_department.
VALID_DEPARTMENTS = sorted(set(CATEGORY_TO_DEPARTMENT.values()))

# LEGACY static category -> supervisor email fallback. Kept only so existing
# data and pre-department deployments keep routing identically. The
# department-driven lookup in features/supervisors/service.py supersedes it; a
# future Firestore "departments" config can replace this mapping (and
# CATEGORY_TO_DEPARTMENT) without touching any business logic.
CATEGORY_MAP = {
    "Electrical": "electrical@campus.edu",
    "Water": "water@campus.edu",
    "Cleanliness": "clean@campus.edu",
    "Infrastructure": "infra@campus.edu",
    "Accessibility": "access@campus.edu",
    "Safety": "safety@campus.edu",
    "Transport": "transport@campus.edu",
    "Environment": "environment@campus.edu",
}

# Last-resort recipient when neither a department supervisor nor a category
# mapping exists. Mirrors the pre-refactor hardcoded fallback.
DEFAULT_SUPERVISOR_EMAIL = "default@campus.edu"

VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

# Allowed transitions per status (used to validate status updates).
STATUS_TRANSITIONS = {
    "Open": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed", "In Progress"],
    "Closed": [],
}

# Priority escalation thresholds — based on the NUMBER OF UNIQUE REPORTERS.
PRIORITY_HIGH_REPORTS = 5
PRIORITY_CRITICAL_REPORTS = 10


def points_for(reason: str) -> int:
    """Resolve the configured point value for a reward reason (0 if unknown)."""
    return POINTS_BY_REWARD.get(reason, 0)


# ══ User profiles & authentication ═════════════════════════════════════════════
# Identity is the Firebase Authentication UID. Each role's profiles live in its
# own collection keyed by uid:
#   students/{uid}  supervisors/{uid}  admins/{uid}
#     . uid, email, displayName, campusId, role, phoneNumber, isActive,
#       createdAt, lastLogin, updatedAt (+ department on supervisors)
# The email address is an EDITABLE profile field, never the primary key.
ROLE_COLLECTIONS = {
    "user": "students",
    "supervisor": "supervisors",
    "admin": "admins",
}
STUDENTS_COLLECTION = ROLE_COLLECTIONS["user"]
SUPERVISORS_COLLECTION = ROLE_COLLECTIONS["supervisor"]
ADMINS_COLLECTION = ROLE_COLLECTIONS["admin"]

# Legacy ``users/{email}`` collection. Retained ONLY as a rollback/read fallback
# during the migration window — new writes never go here (see
# scripts/migrate_uid_collections.py for the one-time move).
USERS_COLLECTION = "users"

# Valid application roles. The seeded order is meaningful: the first role is the
# default assigned to newly registered accounts.
VALID_ROLES = ["user", "supervisor", "admin"]
DEFAULT_ROLE = VALID_ROLES[0]

# Default campus for self-registration (matches a document id in `campuses`).
DEFAULT_CAMPUS_ID = "methodist"

# Passed through to firebase_admin.auth.create_user for new signups.
# Defaults keep the account usable without requiring extra fields.
DEFAULT_DISPLAY_NAME = "SCIARS User"

# ══ Fresh authentication for sensitive admin operations (P2-03) ════════════════
# Admin-only account-lifecycle endpoints (deactivate/activate/delete, email
# change, password reset) require the caller's ID token to have been minted
# within this many seconds (the Firebase ``auth_time`` claim). Stale sessions
# receive 403 with code REAUTH_REQUIRED and the frontend re-authenticates the
# admin before retrying. A value of 300 matches the Firebase-recommended 5
# minute window for sensitive operations.
FRESH_AUTH_MAX_AGE_SECONDS = _int_env("FRESH_AUTH_MAX_AGE_SECONDS", 300)

# ══ SMS notifications ═════════════════════════════════════════════════════════
# Provider used for outbound SMS. The active provider sends real SMS through
# the TextBee gateway (features/sms/provider.py) to a connected Android
# phone. Credentials are read from backend/.env (TEXTBEE_API_KEY,
# TEXTBEE_DEVICE_ID, TEXTBEE_BASE_URL). To switch providers, register the new
# class in features/sms/service.py and change this constant.
SMS_PROVIDER = "android_gateway"

# ══ Frontend base URL (SMS issue links) ════════════════════════════════════════
# Prefix for the clickable issue link embedded in SMS messages. Read from
# backend/.env (FRONTEND_BASE_URL) so it can be swapped to the production
# origin without touching code. The full link becomes
#   {FRONTEND_BASE_URL}/issues/{campus_id}/{issue_id}
FRONTEND_BASE_URL = (
    os.environ.get("FRONTEND_BASE_URL") or "https://acns-v2.vercel.app"
).rstrip("/")

# ══ SMS language support ═══════════════════════════════════════════════════════
# ISO 639-1 codes a supervisor can choose for their SMS notifications. The
# message body for each code lives in a dedicated template module under
# ``features/sms/templates/`` (english.py, telugu.py, hindi.py); adding a new
# language means registering a new template there (and in
# features/sms/templates/__init__.py) — the SMS service itself never contains
# language-specific strings.
VALID_PREFERRED_LANGUAGES = ["en", "te", "hi"]
DEFAULT_PREFERRED_LANGUAGE = "en"

# ══ Application environment ════════════════════════════════════════════════════
# Read from backend/.env (ENVIRONMENT). Controls environment-specific behavior
# such as seed-script safety and CORS defaults. Allowed values:
#   development / local / production
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip().lower()
DEV_ENVIRONMENTS = {"development", "local"}

# ══ CORS (Cross-Origin Resource Sharing) ═══════════════════════════════════════
# Allowed browser origins for the API. NEVER use "*" with credentials enabled.
#
# Read from backend/.env as a comma-separated list, e.g.
#   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://app.example.com
#
# * development / local : defaults to the local Vite dev origins below when the
#   variable is unset (keeps frontend development working out of the box).
# * production            : CORS_ALLOWED_ORIGINS MUST be set explicitly —
#   main.py refuses to boot otherwise (fail-closed).
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _split_origins(raw: str):
    """Split a comma-separated origin list; drop blanks, strip trailing slashes."""
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


# Raw (possibly empty) list from the environment — main.py resolves the final
# value so it can enforce the production fail-closed guard.
CORS_ALLOWED_ORIGINS = _split_origins(os.environ.get("CORS_ALLOWED_ORIGINS", ""))

# ══ Photo URL validation (P2-01) ═══════════════════════════════════════════════
# Photo fields (imageUrl / proofImageUrl / supervisorPhoto) accept either an
# http/https URL or a raster-image base64 data URL.
#   * http/https: externally-hosted links (e.g. legacy storage URLs). Anything
#     else — javascript:, file:, ftp:... — is rejected at the schema boundary
#     so a stored URL can never execute in a victim's browser.
#   * data:image/...: photos submitted as base64. Firebase Storage is not
#     available on the Spark (free) plan, so images travel in the API payload
#     instead. ONLY raster MIME types are allowed — SVG/HTML are rejected
#     because SVG can embed script. The decoded payload is capped at
#     MAX_IMAGE_DATA_BYTES so a document stays well under Firestore's 1MB
#     document size limit and request payloads remain bounded. The frontend
#     mirrors this cap in src/utils/imageDataUrl.js — keep both in sync.
ALLOWED_URL_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = _int_env("MAX_URL_LENGTH", 2048)
ALLOWED_IMAGE_DATA_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
}
MAX_IMAGE_DATA_BYTES = _int_env("MAX_IMAGE_DATA_BYTES", 512 * 1024)

# ══ Rate limiting (P2-02) ══════════════════════════════════════════════════════
# Lightweight in-memory rate limiting (core/ratelimit.py) keyed by client IP.
# Each scope maps to (limit, window_seconds). Defaults are tuned so legitimate
# campus usage is never blocked; every value is env-overridable. This layer is
# stateless-on-purpose: no Redis or external infrastructure required.
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

RATE_LIMITS = {
    "login": (
        _int_env("RATE_LIMIT_LOGIN", 20),
        _int_env("RATE_LIMIT_LOGIN_WINDOW_SECONDS", 60),
    ),
    "signup": (
        _int_env("RATE_LIMIT_SIGNUP", 10),
        _int_env("RATE_LIMIT_SIGNUP_WINDOW_SECONDS", 3600),
    ),
    "create_issue": (
        _int_env("RATE_LIMIT_CREATE_ISSUE", 30),
        _int_env("RATE_LIMIT_CREATE_ISSUE_WINDOW_SECONDS", 3600),
    ),
    "create_supervisor": (
        _int_env("RATE_LIMIT_CREATE_SUPERVISOR", 20),
        _int_env("RATE_LIMIT_CREATE_SUPERVISOR_WINDOW_SECONDS", 3600),
    ),
    "reset_password": (
        _int_env("RATE_LIMIT_RESET_PASSWORD", 10),
        _int_env("RATE_LIMIT_RESET_PASSWORD_WINDOW_SECONDS", 3600),
    ),
    "verify_issue": (
        _int_env("RATE_LIMIT_VERIFY_ISSUE", 30),
        _int_env("RATE_LIMIT_VERIFY_ISSUE_WINDOW_SECONDS", 60),
    ),
    "gamification_award": (
        _int_env("RATE_LIMIT_GAMIFICATION_AWARD", 30),
        _int_env("RATE_LIMIT_GAMIFICATION_AWARD_WINDOW_SECONDS", 60),
    ),
    "navigation_route": (
        _int_env("RATE_LIMIT_NAVIGATION_ROUTE", 60),
        _int_env("RATE_LIMIT_NAVIGATION_ROUTE_WINDOW_SECONDS", 60),
    ),
}

# ══ SMS abuse protection (P2-06) ════════════════════════════════════════════════
# Guards the real-money SMS gateway against scripted abuse. Persisted counters
# (features/sms/counters.py) live in the ``usage_counters`` collection. All
# guards FAIL OPEN: a counter outage never blocks a legitimate report. Limits
# are per-user (new-issue cap) and per-supervisor (daily SMS cap + dispatch
# cooldown) — the latter two are enforced independently of the duplicate-SMS
# guard (smsSent/smsSentAt) and never weaken it.
SMS_ABUSE_ENABLED = os.environ.get("SMS_ABUSE_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SMS_ABUSE_COUNTERS_COLLECTION = "usage_counters"
SMS_ABUSE_MAX_NEW_ISSUES_PER_USER_PER_DAY = _int_env(
    "SMS_ABUSE_MAX_NEW_ISSUES_PER_USER_PER_DAY", 10
)
SMS_ABUSE_MAX_SMS_PER_SUPERVISOR_PER_DAY = _int_env(
    "SMS_ABUSE_MAX_SMS_PER_SUPERVISOR_PER_DAY", 30
)
SMS_ABUSE_SMS_COOLDOWN_SECONDS = _int_env("SMS_ABUSE_SMS_COOLDOWN_SECONDS", 60)

# ══ Error handling (P2-04) ══════════════════════════════════════════════════════
# User-facing message returned for unexpected 500s. Exception details and
# tracebacks are written to the backend logs only — never to API consumers.
GENERIC_INTERNAL_ERROR_MESSAGE = "An unexpected error occurred. Please try again later."
