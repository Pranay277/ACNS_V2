"""
features/supervisors/service.py — Supervisor account management and assignment.

Supervisors are provisioned by ADMINS, never through public signup (see
``features/auth/router.py`` — signup only ever creates the default ``user``
role). Each supervisor is a profile document in the ``supervisors/{uid}``
collection (UID-keyed; ``email`` is an editable profile field). No separate
collection exists and no ``users/`` doc is written for supervisors.

Issue assignment uses Department as the PRIMARY lookup key:

    category ──▶ CATEGORY_TO_DEPARTMENT ──▶ active supervisors/{uid} with
                                             matching department ──▶ uid
                                           └─ (fallback) CATEGORY_MAP email
                                              ── resolved to uid at runtime
                                           └─ (final) DEFAULT_SUPERVISOR_EMAIL
                                              ── resolved to uid at runtime

The department query lives in one function (``resolve_supervisor_for_department``)
so a future Firestore "departments" config collection can replace the static
category/department mappings without touching issue business logic.

Admin surface (all keyed by uid):

    POST   /api/supervisors                  -> create_supervisor
    GET    /api/supervisors                  -> list_supervisors
    GET    /api/supervisors/{uid}            -> get_supervisor
    PATCH  /api/supervisors/{uid}            -> update_supervisor
    POST   /api/supervisors/{uid}/change-email -> change_supervisor_email
    POST   /api/supervisors/{uid}/deactivate -> deactivate_supervisor
    POST   /api/supervisors/{uid}/activate   -> activate_supervisor
    DELETE /api/supervisors/{uid}            -> delete_supervisor
    POST   /api/supervisors/{uid}/reset-password -> reset_supervisor_password
"""

import logging
import secrets

from firebase_admin import auth as admin_auth

from core.config import (
    CATEGORY_MAP,
    CATEGORY_TO_DEPARTMENT,
    DEFAULT_SUPERVISOR_EMAIL,
    SUPERVISORS_COLLECTION,
)
from core.firebase import db
from features.auth import service as auth_service
from features.profile import service as profile_service
from features.profile.service import resolve_uid
from shared.utils.validators import validate_department, validate_preferred_language

logger = logging.getLogger(__name__)

# Fields an admin may change on a supervisor via the update path.
# ``email`` is deliberately excluded — email changes are an admin-only,
# dedicated operation (change_supervisor_email) that updates Firebase Auth too.
SUPERVISOR_UPDATABLE_FIELDS = {
    "displayName",
    "campusId",
    "department",
    "phoneNumber",
    "preferredLanguage",
}

# Fields a supervisor may change on their OWN profile (self-service). Email,
# department, role, uid and isActive are admin-managed and deliberately absent.
SELF_UPDATABLE_FIELDS = {
    "displayName",
    "phoneNumber",
    "preferredLanguage",
}

# Statuses that still require a supervisor's attention (delete guard).
_OPEN_STATUSES = ("Open", "In Progress")


# ── Assignment resolution (Department = primary lookup key) ─────────────────────


def resolve_supervisor_for_department(department: str) -> dict | None:
    """
    Return the ACTIVE supervisor profile for a department, or ``None``.

    Queries the ``supervisors`` collection by ``department`` and filters
    ``isActive`` in Python so no composite Firestore index is required. When
    department config moves to Firestore, this function is the only place that
    changes.
    """
    if not department:
        return None
    docs = db.collection(SUPERVISORS_COLLECTION).where("department", "==", department).stream()
    for doc in docs:
        data = doc.to_dict() or {}
        if data.get("role") != "supervisor":
            continue
        if data.get("isActive") is False:
            continue
        data["userId"] = doc.id
        return data
    return None


def resolve_assigned_supervisor(category: str) -> str:
    """
    Resolve the supervisor identity (uid) a new issue in ``category`` is
    assigned to.

    1. Department lookup: category -> department -> active supervisor profile.
    2. Legacy fallback: the static ``CATEGORY_MAP`` keeps pre-department data;
       its email values are resolved to uids at runtime.
    3. Final fallback: ``DEFAULT_SUPERVISOR_EMAIL`` resolved to a uid.

    Returns the uid when resolvable, otherwise the raw email (legacy/unknown
    account) so issue assignment and SMS still function.
    """
    department = CATEGORY_TO_DEPARTMENT.get(category)
    supervisor = resolve_supervisor_for_department(department) if department else None
    if supervisor:
        return supervisor.get("uid") or supervisor.get("userId")
    email = CATEGORY_MAP.get(category, DEFAULT_SUPERVISOR_EMAIL)
    return resolve_uid(email) or email


# ── Lifecycle (admin-managed, UID-keyed) ───────────────────────────────────────


def create_supervisor(
    email: str,
    display_name: str,
    department: str,
    phone_number: str = None,
    preferred_language: str = None,
    campus_id: str = None,
    password: str = None,
) -> dict:
    """
    Provision a supervisor: Firebase Auth account + ``supervisors/{uid}`` profile.

    The Firebase Auth account is created with a temporary password (supplied or
    auto-generated) that the admin hands to the supervisor; it is returned in
    the response as ``temporaryPassword`` only when this call creates it. An
    email that already has a profile raises ``ValueError`` (admins should use
    ``update_supervisor`` instead).
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError(f"Invalid email '{email}'")
    validate_department(department)
    if preferred_language:
        validate_preferred_language(preferred_language)

    if profile_service.get_user_profile(email):
        raise ValueError(f"A profile already exists for {email}")

    temporary_password = None
    record = auth_service.auth_record_from_email(email)
    if record is None:
        temporary_password = password or _generate_temporary_password()
        record = admin_auth.create_user(
            email=email,
            password=temporary_password,
            display_name=display_name,
            email_verified=True,
        )

    profile = profile_service.create_user_profile(
        uid=record.uid,
        email=email,
        display_name=display_name,
        campus_id=campus_id,
        role="supervisor",
        phone_number=phone_number,
        preferred_language=preferred_language,
        department=department,
    )
    result = dict(profile)
    if temporary_password:
        result["temporaryPassword"] = temporary_password
    return result


def get_supervisor(uid: str) -> dict | None:
    """Return the supervisor profile for a uid (email accepted for compat)."""
    return profile_service.get_user_profile(uid)


def update_supervisor(uid: str, updates: dict) -> dict:
    """Apply whitelisted admin updates to a supervisor profile (uid-keyed)."""
    profile = profile_service.get_user_profile(uid)
    if not profile:
        raise ValueError(f"No profile found for {uid}")
    if profile.get("role") != "supervisor":
        raise ValueError(f"{uid} is not a supervisor")
    return profile_service.update_user_profile(
        uid, updates, restricted_fields=SUPERVISOR_UPDATABLE_FIELDS
    )


def update_self_profile(uid: str, updates: dict) -> dict:
    """
    Self-service update of a supervisor's OWN profile.

    Reuses the shared profile update path with a self-only whitelist
    (``displayName``, ``phoneNumber``, ``preferredLanguage``). Attempts to
    modify email, department, role, uid or isActive are filtered out. The
    identifier must resolve to a supervisor profile — students, admins and
    other supervisors are rejected.
    """
    profile = profile_service.get_user_profile(uid)
    if not profile:
        raise ValueError(f"No profile found for {uid}")
    if profile.get("role") != "supervisor":
        raise ValueError(f"{uid} is not a supervisor")
    return profile_service.update_user_profile(
        uid, updates, restricted_fields=SELF_UPDATABLE_FIELDS
    )


def change_supervisor_email(uid: str, new_email: str) -> dict:
    """
    Admin-only supervisor email change.

    1. Updates the Firebase Auth email (the supervisor must use the new email
       for future logins).
    2. Updates the ``email`` field on the ``supervisors/{uid}`` document.
    3. The uid, department, phone, language, issue assignments and SMS history
       are untouched.

    Raises ``ValueError`` when the new email is already in use or the target is
    not a supervisor.
    """
    profile = profile_service.get_user_profile(uid)
    if not profile:
        raise ValueError(f"No profile found for {uid}")
    if profile.get("role") != "supervisor":
        raise ValueError(f"{uid} is not a supervisor")

    new_email = (new_email or "").strip().lower()
    if not new_email or "@" not in new_email:
        raise ValueError(f"Invalid email '{new_email}'")
    if new_email == (profile.get("email") or "").strip().lower():
        return profile

    existing = auth_service.auth_record_from_email(new_email)
    if existing is not None and existing.uid != uid:
        raise ValueError(f"Email '{new_email}' is already in use by another account")

    admin_auth.update_user(uid, email=new_email)
    return profile_service.set_user_email(uid, new_email)


def deactivate_supervisor(uid: str) -> dict:
    """Disable a supervisor: block Firebase Auth login + soft-delete profile."""
    _set_auth_disabled(uid, disabled=True)
    return profile_service.set_user_active(uid, False)


def activate_supervisor(uid: str) -> dict:
    """Re-enable a disabled supervisor account."""
    _set_auth_disabled(uid, disabled=False)
    return profile_service.set_user_active(uid, True)


def delete_supervisor(uid: str) -> None:
    """
    Permanently remove a supervisor (profile + Firebase Auth account).

    Refuses to delete while the supervisor still has Open/In Progress issues.
    """
    profile = profile_service.get_user_profile(uid)
    if not profile:
        raise ValueError(f"No profile found for {uid}")
    if profile.get("role") != "supervisor":
        raise ValueError(f"{uid} is not a supervisor")
    if _has_open_issues(uid):
        raise ValueError(
            f"Cannot delete supervisor {uid}: they still have Open/In Progress issues"
        )
    profile_service.delete_user_profile(uid)
    record = auth_service.auth_record_from_uid(uid)
    if record is not None:
        admin_auth.delete_user(record.uid)
    logger.info("Deleted supervisor %s", uid)


def reset_supervisor_password(uid: str, new_password: str) -> None:
    """Reset a supervisor's Firebase Auth password."""
    record = auth_service.auth_record_from_uid(uid)
    if record is None:
        raise ValueError(f"No auth account found for {uid}")
    admin_auth.update_user(record.uid, password=new_password)
    logger.info("Reset password for %s", uid)


def list_supervisors(include_inactive: bool = False) -> list:
    """List supervisor profiles (optionally including deactivated accounts)."""
    result = []
    for doc in db.collection(SUPERVISORS_COLLECTION).stream():
        data = doc.to_dict() or {}
        if not include_inactive and data.get("isActive") is False:
            continue
        data["userId"] = doc.id
        result.append(data)
    result.sort(key=lambda u: (u.get("displayName") or "").lower())
    return result


# ── Private helpers ────────────────────────────────────────────────────────────


def _generate_temporary_password() -> str:
    """Generate a temporary password that satisfies common password policies."""
    return secrets.token_urlsafe(12) + "A1!"


def _set_auth_disabled(uid: str, disabled: bool) -> None:
    """Flip the Firebase Auth ``disabled`` flag (best-effort)."""
    record = auth_service.auth_record_from_uid(uid)
    if record is not None:
        admin_auth.update_user(record.uid, disabled=disabled)


def _has_open_issues(uid: str) -> bool:
    """Return True when the supervisor still has Open/In Progress issues."""
    docs = db.collection("issues").where("assignedTo", "==", uid).stream()
    for doc in docs:
        if (doc.to_dict() or {}).get("status") in _OPEN_STATUSES:
            return True
    return False
