"""
features/auth/router.py — REST endpoints for authentication and user profiles.

Identity verification lives in features/auth/service.py and profile document
management in features/profile/service.py; this router only validates input,
verifies the caller's identity where required, and maps results to HTTP
responses.

The client owns credentials: it signs in/up with the Firebase client SDK and
passes the resulting ID token here. The backend never sees a password.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from core.config import (
    DEFAULT_PREFERRED_LANGUAGE,
    DEFAULT_ROLE,
    VALID_PREFERRED_LANGUAGES,
    VALID_ROLES,
)
from features.auth import service as auth_service
from features.auth.schemas import LoginRequest, SignupRequest, UserUpdateRequest
from features.profile import service as profile_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Fields an (admin) caller may mutate via PATCH /users/{userId}.
ADMIN_UPDATABLE_FIELDS = {
    "displayName",
    "campusId",
    "role",
    "phoneNumber",
    "preferredLanguage",
    "department",
}


def _error(status_code: int, message: str):
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message},
    )


@router.post("/login")
def login(payload: LoginRequest):
    """
    Authenticate a Firebase ID token and return the user profile.

    Flow:
      1. Verify the ID token.
      2. Ensure a Firestore profile exists (creates it when missing — this
         self-heals accounts that have no profile yet). Never duplicates.
      3. Update lastLogin.
    """
    try:
        identity = auth_service.identity_from_token(payload.idToken)
        profile = profile_service.ensure_user_profile(
            uid=identity["uid"], email=identity["email"]
        )
        profile = profile_service.record_login(profile["email"], uid=identity["uid"])
        if profile is None:
            raise _error(500, "Profile could not be read back after login")
        return {"success": True, "user": profile}
    except ValueError as e:
        raise _error(401, f"Invalid authentication token: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed: %s", e)
        raise _error(500, "Login failed. Please try again.")


@router.post("/signup")
def signup(payload: SignupRequest):
    """
    Register a new user.

    Flow:
      1. Verify the ID token (the Firebase Auth account was created by the
         client SDK with createUserWithEmailAndPassword).
      2. Create the Firestore profile atomically. If a profile already exists
         the existing one is returned (no duplicate profiles are ever created).
      3. Set lastLogin and return the full profile.

    Self-registration ALWAYS creates the default ``user`` role — the schema
    carries no role field, so supervisors can never self-register. Supervisor
    accounts are provisioned by admins via ``features/supervisors/service.py``.
    """
    try:
        identity = auth_service.identity_from_token(payload.idToken)
        profile = profile_service.ensure_user_profile(
            uid=identity["uid"],
            email=identity["email"],
            display_name=payload.displayName or identity.get("name"),
            campus_id=payload.campusId,
            phone_number=payload.phoneNumber,
            preferred_language=payload.preferredLanguage,
        )
        profile = profile_service.record_login(profile["email"], uid=identity["uid"])
        return {"success": True, "user": profile}
    except ValueError as e:
        raise _error(401, f"Invalid authentication token: {e}")
    except Exception as e:
        logger.error("Signup failed: %s", e)
        raise _error(500, "Signup failed. Please try again.")


@router.get("/profile/{userId}")
def get_profile(userId: str):
    """Return a single user profile by email (doc id)."""
    profile = profile_service.get_user_profile(userId)
    if not profile:
        raise _error(404, f"User profile not found for '{userId}'")
    return {"success": True, "user": profile}


@router.get("/uid/{uid}")
def get_profile_by_uid(uid: str):
    """Return a single user profile by Firebase Auth uid."""
    profile = profile_service.get_user_by_uid(uid)
    if not profile:
        raise _error(404, f"User profile not found for uid '{uid}'")
    return {"success": True, "user": profile}


@router.get("/users")
def list_users(
    includeInactive: bool = Query(False, description="Include disabled accounts"),
):
    """List user profiles (defaults to active accounts only)."""
    return {"success": True, "users": profile_service.list_users(include_inactive=includeInactive)}


@router.patch("/users/{userId}")
def update_user(userId: str, payload: UserUpdateRequest):
    """
    Update profile fields (displayName, campusId, role, phoneNumber).
    Role changes are restricted to valid roles; disallowed keys are ignored.
    """
    try:
        updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        profile = profile_service.update_user_profile(
            userId, updates, restricted_fields=ADMIN_UPDATABLE_FIELDS
        )
        return {"success": True, "user": profile}
    except ValueError as e:
        raise _error(400, str(e))
    except Exception as e:
        logger.error("Update profile failed for %s: %s", userId, e)
        raise _error(500, "Failed to update user profile")


@router.post("/users/{userId}/deactivate")
def deactivate_user(userId: str):
    """Disable a user account (soft delete)."""
    profile = profile_service.set_user_active(userId, False)
    return {"success": True, "user": profile}


@router.post("/users/{userId}/activate")
def activate_user(userId: str):
    """Re-enable a disabled user account."""
    profile = profile_service.set_user_active(userId, True)
    return {"success": True, "user": profile}


@router.get("/valid-roles")
def valid_roles():
    """Expose the valid role list (used by the frontend for role selection)."""
    return {"success": True, "roles": VALID_ROLES, "defaultRole": DEFAULT_ROLE}


@router.get("/valid-languages")
def valid_languages():
    """
    Expose the supported SMS notification languages.

    Returns the ISO 639-1 codes and their display labels. The message bodies
    for these codes live in dedicated template modules (templates/sms/) — the
    SMS service never contains language-specific strings.
    """
    return {
        "success": True,
        "languages": VALID_PREFERRED_LANGUAGES,
        "defaultLanguage": DEFAULT_PREFERRED_LANGUAGE,
    }
