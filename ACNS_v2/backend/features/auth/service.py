"""
features/auth/service.py — Identity verification for the auth feature.

Responsibilities:
  1. Verify Firebase ID tokens and resolve them to a user identity.
  2. Look up Firebase Auth records (used by admin flows and seed scripts).

All firebase auth token errors are normalized to ``ValueError`` so the router
can respond with a single 401 path.

Profile document management lives in ``features/profile/service.py``.
"""

import logging

from firebase_admin import auth as admin_auth
from firebase_admin.auth import (
    CertificateFetchError,
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
)

logger = logging.getLogger(__name__)


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
