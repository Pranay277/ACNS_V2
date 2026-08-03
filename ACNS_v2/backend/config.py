"""
config.py — Centralized configuration.

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
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:  # pragma: no cover — dotenv is optional in bare envs
    pass

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
# One document per user, keyed by userId (email), e.g.
#   gamification_users/{userId}
#     . totalPoints, issuesReported, issuesResolved, displayName, lastUpdated
#   gamification_users/{userId}/points_history/{event_key}   (idempotency/audit)
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

# ══ Issue workflow ═════════════════════════════════════════════════════════════
# Category -> supervisor email used to auto-assign new issues.
#   Note: addresses are also mirrored by the ``seed_users.py`` accounts and the
#   demo flows, so keep them in sync when changing either side.
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
# One document per user, keyed by userId (email) — the convention already used by
# issues, notifications, and gamification. The Firebase Auth ``uid`` is stored as
# a field so it stays addressable by both identities.
#   users/{email}
#     . uid, email, displayName, campusId, role, phoneNumber, isActive,
#       createdAt, lastLogin, updatedAt
#   users/{email}/achievements (optional subcollection for future badges)
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

# ══ SMS notifications ═════════════════════════════════════════════════════════
# Provider used for outbound SMS. The active provider sends real SMS through
# the TextBee gateway (providers/android_gateway.py) to a connected Android
# phone. Credentials are read from backend/.env (TEXTBEE_API_KEY,
# TEXTBEE_DEVICE_ID, TEXTBEE_BASE_URL). To switch providers, register the new
# class in services/sms_service.py and change this constant.
SMS_PROVIDER = "android_gateway"

# ══ Frontend base URL (SMS issue links) ════════════════════════════════════════
# Prefix for the clickable issue link embedded in SMS messages. Read from
# backend/.env (FRONTEND_BASE_URL) so it can be swapped to the production
# origin without touching code. The full link becomes
#   {FRONTEND_BASE_URL}/issues/{campus_id}/{issue_id}
FRONTEND_BASE_URL = os.environ.get(
    "FRONTEND_BASE_URL", "http://localhost:5173"
).rstrip("/")

# ══ SMS language support ═══════════════════════════════════════════════════════
# ISO 639-1 codes a supervisor can choose for their SMS notifications. The
# message body for each code lives in a dedicated template module under
# ``templates/sms/`` (english.py, telugu.py, hindi.py); adding a new language
# means registering a new template here (and in templates/sms/__init__.py) —
# the SMS service itself never contains language-specific strings.
VALID_PREFERRED_LANGUAGES = ["en", "te", "hi"]
DEFAULT_PREFERRED_LANGUAGE = "en"
