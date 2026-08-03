"""
features/profile/service.py — User profile business logic.

Identity model (UID-based):
  * Firebase Authentication UID is the PRIMARY, immutable identifier.
  * Email is an editable profile field, never the document key.
  * Each role's profiles live in its own collection keyed by uid:
      students/{uid}  supervisors/{uid}  admins/{uid}
  * The legacy ``users/{email}`` collection is retained ONLY as a read/rollback
    fallback so the app keeps working before/during the migration window — new
    writes never go there.

Responsibilities:
  1. Reconcile a Firebase account with its role-scoped profile (idempotent —
     never creates duplicate profiles, never overwrites another role's doc).
  2. Create / update / fetch profiles by uid (email accepted for compatibility).
  3. Manage `lastLogin` bookkeeping and account activation state.
  4. Resolve email or uid identifiers to a uid for cross-feature use.

Design notes:
  * ``ensure_user_profile`` looks the uid up across the three role collections
    FIRST. A profile that already exists is returned untouched — a student
    login can never create or modify a supervisor/admin document (identity
    boundaries enforced by construction). Missing profiles are created under
    the requested/default role (always ``user`` on self-registration).
  * Registration is idempotent: ``ensure_user_profile`` uses a Firestore
    transaction so concurrent signups can never create duplicate documents.
  * Token verification lives in ``features/auth/service.py``; this module only
    manages profile documents.
"""

import logging

from firebase_admin import firestore

from core.config import (
    DEFAULT_CAMPUS_ID,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_PREFERRED_LANGUAGE,
    DEFAULT_ROLE,
    ROLE_COLLECTIONS,
    USERS_COLLECTION,
    VALID_ROLES,
)
from core.firebase import db
from features.auth import service as auth_service
from shared.utils.validators import (
    validate_department,
    validate_preferred_language,
    validate_role,
)

logger = logging.getLogger(__name__)

FIRESTORE_TS = firestore.SERVER_TIMESTAMP

LEGACY_COLLECTION = USERS_COLLECTION


def _normalize_email(value):
    return str(value or "").strip().lower()


def resolve_uid(identifier) -> str | None:
    """
    Resolve an email or Firebase uid to a uid (``None`` when unknown).

    Emails are resolved through Firebase Auth (the authoritative email->uid
    mapping); non-email identifiers are treated as uids and verified. This is
    the single function that turns legacy email identifiers into uids.
    """
    if not identifier:
        return None
    identifier = str(identifier).strip()
    if not identifier:
        return None
    if "@" in identifier:
        record = auth_service.auth_record_from_email(_normalize_email(identifier))
        return record.uid if record is not None else None
    record = auth_service.auth_record_from_uid(identifier)
    return record.uid if record is not None else None


def _role_collection(role):
    collection = ROLE_COLLECTIONS.get(role)
    if collection is None:
        raise ValueError(f"Invalid role '{role}'. Valid roles: {VALID_ROLES}")
    return db.collection(collection)


def _role_ref(role, uid):
    return _role_collection(role).document(uid)


def _legacy_collection():
    return db.collection(LEGACY_COLLECTION)


def _legacy_ref(email):
    return _legacy_collection().document(_normalize_email(email))


def get_profile_by_uid(uid):
    """Return a profile from the role-scoped collections by uid, or None."""
    if not uid:
        return None
    for role in ROLE_COLLECTIONS:
        doc = _role_ref(role, uid).get()
        if doc.exists:
            return doc.to_dict()
    return None


def _locate_profile(identifier):
    """
    Return (profile_dict, DocumentReference) for an email or uid.

    Checks the UID-keyed role collections first (primary identity), then the
    legacy ``users/`` collection so reads keep working during/after the
    migration window.
    """
    identifier = str(identifier or "").strip()
    if not identifier:
        return None, None

    uid = None
    if "@" in identifier:
        record = auth_service.auth_record_from_email(_normalize_email(identifier))
        uid = record.uid if record is not None else None
    else:
        uid = identifier

    if uid:
        for role in ROLE_COLLECTIONS:
            ref = _role_ref(role, uid)
            doc = ref.get()
            if doc.exists:
                return doc.to_dict(), ref
        # Pre-migration fallback: legacy doc whose ``uid`` field matches.
        for legacy_doc in _legacy_collection().where("uid", "==", uid).stream():
            return legacy_doc.to_dict(), legacy_doc.reference

    if "@" in identifier:
        legacy_ref = _legacy_ref(identifier)
        doc = legacy_ref.get()
        if doc.exists:
            return doc.to_dict(), legacy_ref

    return None, None


# ── Profile creation / reconciliation ──────────────────────────────────────────


def build_profile_payload(
    uid: str,
    email: str,
    display_name: str = None,
    campus_id: str = None,
    role: str = None,
    phone_number: str = None,
    preferred_language: str = None,
    department: str = None,
):
    """Construct the default user profile document for a new account."""
    if role:
        validate_role(role)
    if preferred_language:
        validate_preferred_language(preferred_language)
    if department:
        validate_department(department)
    if display_name:
        default_name = display_name
    elif email:
        default_name = email.split("@")[0]
    else:
        default_name = DEFAULT_DISPLAY_NAME
    payload = {
        "uid": uid,
        "email": email,
        "displayName": default_name,
        "campusId": campus_id or DEFAULT_CAMPUS_ID,
        "role": role or DEFAULT_ROLE,
        "phoneNumber": phone_number or None,
        "preferredLanguage": preferred_language or DEFAULT_PREFERRED_LANGUAGE,
        "isActive": True,
        "createdAt": FIRESTORE_TS,
        "lastLogin": FIRESTORE_TS,
        "updatedAt": FIRESTORE_TS,
    }
    # Only supervisors carry a department; students keep the standard shape.
    if department:
        payload["department"] = department
    return payload


@firestore.transactional
def _ensure_profile_transaction(transaction, user_ref, profile):
    """Create the profile only when it does not already exist."""
    existing = next(transaction.get(user_ref), None)
    if existing is not None and existing.exists:
        return False
    transaction.set(user_ref, profile)
    return True


def ensure_user_profile(
    uid: str,
    email: str,
    display_name: str = None,
    campus_id: str = None,
    role: str = None,
    phone_number: str = None,
    preferred_language: str = None,
    department: str = None,
    allow_role_escalation: bool = False,
) -> dict:
    """
    Reconcile a Firebase account with its role-scoped profile.

    * An existing profile for the uid (any role collection, then legacy) is
      returned untouched — this enforces the identity boundary: a student login
      never modifies a supervisor/admin document.
    * A missing profile is created under the requested/default role (always
      ``user`` on self-registration).
    * ``allow_role_escalation`` may apply an explicitly requested role to an
      existing profile (admin flows) without moving collections.
    """
    existing = get_profile_by_uid(uid)
    if existing is not None:
        if allow_role_escalation and role and existing.get("role") != role:
            ref = _role_ref(existing.get("role") or DEFAULT_ROLE, uid)
            ref.update({"role": role, "updatedAt": FIRESTORE_TS})
            return ref.get().to_dict()
        return existing

    # Pre-migration legacy profile: return it as-is (the migration script is
    # responsible for moving legacy profiles into the role collections).
    if email:
        for doc in _legacy_collection().where("uid", "==", uid).stream():
            return doc.to_dict()

    role = role or DEFAULT_ROLE
    profile = build_profile_payload(
        uid=uid,
        email=email,
        display_name=display_name,
        campus_id=campus_id,
        role=role,
        phone_number=phone_number,
        preferred_language=preferred_language,
        department=department,
    )
    user_ref = _role_ref(role, uid)
    _ensure_profile_transaction(db.transaction(), user_ref, profile)
    return user_ref.get().to_dict()


def record_login(identifier: str, uid: str = None):
    """
    Update a user's lastLogin timestamp (and backfill uid when missing).

    Updates whichever document currently holds the profile (role collection or
    legacy). Returns the updated profile dict, or None if absent.
    """
    profile, ref = _locate_profile(identifier)
    if profile is None:
        return None
    updates = {"lastLogin": FIRESTORE_TS, "updatedAt": FIRESTORE_TS}
    if uid:
        updates["uid"] = uid
    ref.update(updates)
    return ref.get().to_dict()


def create_user_profile(
    uid: str,
    email: str,
    display_name: str = None,
    campus_id: str = None,
    role: str = None,
    phone_number: str = None,
    preferred_language: str = None,
    department: str = None,
) -> dict:
    """
    Explicitly create a profile in the role collection, failing if one exists.

    Prefer ``ensure_user_profile`` for request-driven flows; this is used by
    seed scripts and admin provisioning where a duplicate is an error.
    """
    profile = build_profile_payload(
        uid=uid,
        email=email,
        display_name=display_name,
        campus_id=campus_id,
        role=role,
        phone_number=phone_number,
        preferred_language=preferred_language,
        department=department,
    )
    role = role or DEFAULT_ROLE
    if get_profile_by_uid(uid) is not None:
        raise ValueError(f"A profile already exists for {email}")
    user_ref = _role_ref(role, uid)
    created = _ensure_profile_transaction(db.transaction(), user_ref, profile)
    if not created:
        raise ValueError(f"A profile already exists for {email}")
    return user_ref.get().to_dict()


# ── Reads ──────────────────────────────────────────────────────────────────────


def get_user_profile(user_id: str) -> dict:
    """Return a profile by email or uid, or None if absent (compat + UID)."""
    if not user_id:
        return None
    profile, _ref = _locate_profile(user_id)
    return profile


def get_user_by_uid(uid: str) -> dict:
    """Resolve a profile by Firebase Auth uid, or None if absent."""
    if not uid:
        return None
    profile, _ref = _locate_profile(uid)
    return profile


def list_users(include_inactive: bool = False) -> list:
    """Return all profiles across the role collections (active by default)."""
    result = []
    for role in ROLE_COLLECTIONS:
        for doc in _role_collection(role).stream():
            data = doc.to_dict() or {}
            if not include_inactive and data.get("isActive") is False:
                continue
            data["userId"] = doc.id
            result.append(data)
    result.sort(key=lambda u: (u.get("displayName") or "").lower())
    return result


def update_user_profile(user_id: str, updates: dict, restricted_fields: set) -> dict:
    """Apply a whitelisted set of field updates to a user profile (email or uid)."""
    allowed = {}
    for key in updates:
        if key not in restricted_fields:
            continue
        value = updates[key]
        if key == "role":
            validate_role(value)
        if key == "preferredLanguage":
            validate_preferred_language(value)
        if key == "department":
            validate_department(value)
        if key == "campusId" and not value:
            continue
        allowed[key] = value
    if not allowed:
        raise ValueError("No valid fields to update")

    profile, ref = _locate_profile(user_id)
    if profile is None:
        raise ValueError(f"No profile found for '{user_id}'")

    allowed["updatedAt"] = FIRESTORE_TS
    ref.update(allowed)
    return ref.get().to_dict()


def delete_user_profile(user_id: str):
    """Hard-delete a user profile (does not touch the Firebase Auth account)."""
    profile, ref = _locate_profile(user_id)
    if profile is None:
        raise ValueError(f"No profile found for '{user_id}'")
    ref.delete()
    logger.info("Deleted profile for %s", user_id)


def set_user_active(user_id: str, is_active: bool) -> dict:
    """Enable or disable a user account."""
    profile, ref = _locate_profile(user_id)
    if profile is None:
        raise ValueError(f"No profile found for '{user_id}'")
    ref.update({"isActive": bool(is_active), "updatedAt": FIRESTORE_TS})
    return ref.get().to_dict()


def set_user_email(user_id: str, new_email: str) -> dict:
    """
    Update the editable ``email`` field of a profile (admin-only operation).

    Never touches the document id (the immutable uid). The caller is
    responsible for updating the Firebase Auth email beforehand.
    """
    email = _normalize_email(new_email)
    if "@" not in email:
        raise ValueError(f"Invalid email '{new_email}'")
    profile, ref = _locate_profile(user_id)
    if profile is None:
        raise ValueError(f"No profile found for '{user_id}'")
    ref.update({"email": email, "updatedAt": FIRESTORE_TS})
    return ref.get().to_dict()
