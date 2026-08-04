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


def verify_id_token(id_token: str, check_revoked: bool = True) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims (uid, email, ...).

    ``check_revoked=True`` (P2-03, always on) makes the verification consult
    the token-revocation list, so ID tokens issued before a refresh-token
    revocation (account disabled, password/email changed, refresh tokens
    revoked) are rejected immediately instead of living until expiry.

    Raises ``ValueError`` when the token is invalid, expired, or revoked. All
    firebase auth token errors are normalized to ``ValueError`` so routers can
    respond with a single 401 path.
    """
    if not id_token:
        raise ValueError("idToken is required")
    try:
        return admin_auth.verify_id_token(id_token, check_revoked=check_revoked)
    except ValueError:
        raise
    except (InvalidIdTokenError, ExpiredIdTokenError, RevokedIdTokenError,
            CertificateFetchError) as e:
        raise ValueError(str(e)) from e


def identity_from_token(id_token: str) -> dict:
    """
    Resolve an ID token to the identity the backend should persist.

    Includes the token's ``auth_time`` claim (epoch seconds) so the auth layer
    can enforce fresh-authentication checks on sensitive admin operations.
    """
    claims = verify_id_token(id_token)
    uid = claims.get("uid")
    email = (claims.get("email") or "").strip().lower()
    if not uid:
        raise ValueError("ID token is missing a uid")
    if not email:
        raise ValueError("ID token is missing an email address")
    return {
        "uid": uid,
        "email": email,
        "name": claims.get("name"),
        "auth_time": claims.get("auth_time"),
    }


def revoke_refresh_tokens(uid: str) -> None:
    """
    Revoke all of a user's refresh tokens (best-effort, never raises).

    Called when an account is disabled or deleted, or when its password or
    email changes. Because every ``verify_id_token`` call runs with
    ``check_revoked=True``, this makes existing ID tokens for the account fail
    verification on the very next request.
    """
    if not uid:
        return
    try:
        admin_auth.revoke_refresh_tokens(uid)
    except Exception as exc:  # noqa: BLE001 — revocation must never break the caller
        logger.warning("Failed to revoke refresh tokens for uid %s: %s", uid, exc)


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
