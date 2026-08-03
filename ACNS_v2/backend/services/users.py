"""
services/users.py — User profile business logic.

Responsibilities:
  1. Verify Firebase ID tokens and resolve them to a user identity.
  2. Ensure a Firestore profile exists for any authenticated user
     (idempotent — never creates duplicate profiles).
  3. Create / update / fetch user profiles.
  4. Manage `lastLogin` bookkeeping.

Design notes:
  * Profiles live in ``users/{userId}`` where ``userId`` is the email — the
    convention already used by issues, notifications, and gamification, so no
    existing code needs to change. The Firebase Auth ``uid`` is stored as a
    field and is also addressable via ``get_user_by_uid``.
  * Registration is idempotent: ``ensure_user_profile`` uses a Firestore
    transaction so concurrent signups can never create duplicate documents.
    Because Firestore and Firebase Auth are separate systems, a failed signup
    leaves at most an Auth account without a profile — which the login flow
    self-heals by calling ``ensure_user_profile`` again.
  * Routers stay thin; every Firestore mutation lives here.
"""

import logging

from firebase_admin import auth as admin_auth
from firebase_admin import firestore
from firebase_admin.auth import (
    CertificateFetchError,
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
    UserRecord,
)

from config import (
    DEFAULT_CAMPUS_ID,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_PREFERRED_LANGUAGE,
    DEFAULT_ROLE,
    USERS_COLLECTION,
    VALID_PREFERRED_LANGUAGES,
    VALID_ROLES,
)
from services.firebase_admin import db

logger = logging.getLogger(__name__)

FIRESTORE_TS = firestore.SERVER_TIMESTAMP


def _collection():
    return db.collection(USERS_COLLECTION)


def _profile_ref(user_id: str):
    return _collection().document(user_id)


# ── Token verification ─────────────────────────────────────────────────────────


def verify_id_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims (uid, email, ...).

    Raises ``ValueError`` when the token is invalid or expired. All firebase
    auth token errors are normalized to ``ValueError`` so routers can respond
    with a single 401 path.
    """
    if not id_token:
        raise ValueError("idToken is required")
    try:
        return admin_auth.verify_id_token(id_token)
    except ValueError:
        raise
    except (InvalidIdTokenError, ExpiredIdTokenError, RevokedIdTokenError,
            CertificateFetchError) as e:
        raise ValueError(str(e)) from e


def identity_from_token(id_token: str) -> dict:
    """Resolve an ID token to the identity the backend should persist."""
    claims = verify_id_token(id_token)
    uid = claims.get("uid")
    email = (claims.get("email") or "").strip().lower()
    if not uid:
        raise ValueError("ID token is missing a uid")
    if not email:
        raise ValueError("ID token is missing an email address")
    return {"uid": uid, "email": email, "name": claims.get("name")}


# ── Profile creation / reconciliation ──────────────────────────────────────────


def build_profile_payload(
    uid: str,
    email: str,
    display_name: str = None,
    campus_id: str = None,
    role: str = None,
    phone_number: str = None,
    preferred_language: str = None,
):
    """Construct the default user profile document for a new account."""
    if role and role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Valid roles: {VALID_ROLES}")
    if preferred_language and preferred_language not in VALID_PREFERRED_LANGUAGES:
        raise ValueError(
            f"Invalid preferredLanguage '{preferred_language}'. "
            f"Valid languages: {VALID_PREFERRED_LANGUAGES}"
        )
    return {
        "uid": uid,
        "email": email,
        "displayName": display_name or email.split("@")[0],
        "campusId": campus_id or DEFAULT_CAMPUS_ID,
        "role": role or DEFAULT_ROLE,
        "phoneNumber": phone_number or None,
        "preferredLanguage": preferred_language or DEFAULT_PREFERRED_LANGUAGE,
        "isActive": True,
        "createdAt": FIRESTORE_TS,
        "lastLogin": FIRESTORE_TS,
        "updatedAt": FIRESTORE_TS,
    }


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
    allow_role_escalation: bool = False,
) -> dict:
    """
    Reconcile a Firebase account with its Firestore profile.

    * Creates the profile if it is missing (atomic, no duplicates).
    * Returns the existing profile untouched when present, unless
      ``allow_role_escalation`` is set, in which case an explicitly requested
      role may be applied to the existing document (used by admins).
    """
    profile = build_profile_payload(
        uid=uid,
        email=email,
        display_name=display_name,
        campus_id=campus_id,
        role=role,
        phone_number=phone_number,
        preferred_language=preferred_language,
    )
    user_ref = _profile_ref(email)

    _ensure_profile_transaction(db.transaction(), user_ref, profile)

    if allow_role_escalation and role:
        current = user_ref.get().to_dict() or {}
        if current.get("role") != role:
            user_ref.update(
                {"role": role, "updatedAt": FIRESTORE_TS}
            )
            logger.info("Role updated for %s -> %s", email, role)

    return user_ref.get().to_dict()


def record_login(email: str, uid: str = None):
    """
    Update a user's lastLogin timestamp (and backfill uid when missing).
    Returns the updated profile dict, or None if the profile is absent.
    """
    user_ref = _profile_ref(email)
    updates = {"lastLogin": FIRESTORE_TS, "updatedAt": FIRESTORE_TS}
    if uid:
        updates["uid"] = uid
    user_ref.update(updates)
    doc = user_ref.get()
    return doc.to_dict() if doc.exists else None


def create_user_profile(
    uid: str,
    email: str,
    display_name: str = None,
    campus_id: str = None,
    role: str = None,
    phone_number: str = None,
    preferred_language: str = None,
) -> dict:
    """
    Explicitly create a profile, failing if one already exists.

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
    )
    user_ref = _profile_ref(email)
    created = _ensure_profile_transaction(db.transaction(), user_ref, profile)
    if not created:
        raise ValueError(f"A profile already exists for {email}")
    return user_ref.get().to_dict()


# ── Reads ──────────────────────────────────────────────────────────────────────


def get_user_profile(user_id: str) -> dict:
    """Return the profile for a user by email (doc id), or None if absent."""
    if not user_id:
        return None
    doc = _profile_ref(user_id.lower().strip()).get()
    return doc.to_dict() if doc.exists else None


def get_user_by_uid(uid: str) -> dict:
    """Resolve a profile by Firebase Auth uid, or None if absent."""
    if not uid:
        return None
    docs = _collection().where("uid", "==", uid).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None


def list_users(include_inactive: bool = False) -> list:
    """Return all user profiles (optionally including deactivated accounts)."""
    query = _collection()
    if not include_inactive:
        query = query.where("isActive", "==", True)
    result = []
    for doc in query.stream():
        data = doc.to_dict()
        data["userId"] = doc.id
        result.append(data)
    result.sort(key=lambda u: (u.get("displayName") or "").lower())
    return result


def update_user_profile(user_id: str, updates: dict, restricted_fields: set) -> dict:
    """Apply a whitelisted set of field updates to a user profile."""
    allowed = {}
    for key in updates:
        if key not in restricted_fields:
            continue
        value = updates[key]
        if key == "role" and value not in VALID_ROLES:
            raise ValueError(f"Invalid role '{value}'. Valid roles: {VALID_ROLES}")
        if key == "preferredLanguage" and value not in VALID_PREFERRED_LANGUAGES:
            raise ValueError(
                f"Invalid preferredLanguage '{value}'. Valid languages: {VALID_PREFERRED_LANGUAGES}"
            )
        if key == "campusId" and not value:
            continue
        allowed[key] = value
    if not allowed:
        raise ValueError("No valid fields to update")

    allowed["updatedAt"] = FIRESTORE_TS
    _profile_ref(user_id).update(allowed)
    return _profile_ref(user_id).get().to_dict()


def delete_user_profile(user_id: str):
    """Hard-delete a user profile (does not touch the Firebase Auth account)."""
    _profile_ref(user_id).delete()
    logger.info("Deleted profile for %s", user_id)


def set_user_active(user_id: str, is_active: bool) -> dict:
    """Enable or disable a user account."""
    _profile_ref(user_id).update(
        {"isActive": bool(is_active), "updatedAt": FIRESTORE_TS}
    )
    return _profile_ref(user_id).get().to_dict()


def auth_record_from_email(email: str):
    """Look up the Firebase Auth record for an email (or None)."""
    try:
        return admin_auth.get_user_by_email(email)
    except admin_auth.UserNotFoundError:
        return None


def auth_record_from_uid(uid: str):
    """Look up the Firebase Auth record for a uid (or None)."""
    try:
        return admin_auth.get_user(uid)
    except admin_auth.UserNotFoundError:
        return None
