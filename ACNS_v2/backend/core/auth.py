"""
core/auth.py — Centralized identity verification and current-user resolution.

The single place that turns a Firebase ID token (from the ``Authorization:
Bearer`` header) into a server-side ``CurrentUser``. The role, department and
active state are ALWAYS read from the role-scoped Firestore profile
(``students/{uid}``, ``supervisors/{uid}``, ``admins/{uid}``) — never from the
client.

Routers depend on ``get_current_user`` (any authenticated user) or the role
guards in ``core/permissions.py``:

    def my_endpoint(current_user: CurrentUser = Depends(require_authenticated)): ...

Token verification itself is delegated to ``features/auth/service.py``
(``identity_from_token``) so the app keeps a single Firebase verification path.

Error contract:
    401  missing / invalid / expired token, or a token for an account with no
         profile (deleted account)
    403  the account is disabled, or its profile has no valid role
"""

import logging

from fastapi import Header, HTTPException

from core.config import ROLE_COLLECTIONS, VALID_ROLES
from features.auth import service as auth_service
from features.profile.service import locate_profile

logger = logging.getLogger(__name__)


class CurrentUser:
    """
    Server-side identity for the current request.

    ``role``, ``department``, ``is_active`` and ``preferred_language`` come
    from the role-scoped Firestore profile, never from client input. The raw
    profile document is exposed as ``profile`` for fields not surfaced here.
    """

    def __init__(
        self,
        uid: str,
        email: str,
        role: str,
        department=None,
        is_active: bool = True,
        preferred_language=None,
        profile=None,
        auth_time=None,
    ):
        self.uid = uid
        self.email = email
        self.role = role
        self.department = department
        self.is_active = is_active
        self.preferred_language = preferred_language
        self.profile = profile or {}
        # Epoch seconds at which the ID token was minted (auth_time claim).
        # Used by core/permissions.require_recent_auth for fresh-authentication
        # checks on sensitive admin operations.
        self.auth_time = auth_time


def _unauthorized(message: str):
    return HTTPException(
        status_code=401,
        detail={"success": False, "message": message},
    )


def _forbidden(message: str):
    return HTTPException(
        status_code=403,
        detail={"success": False, "message": message},
    )


def _extract_bearer_token(authorization) -> str:
    """Pull the token out of an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        raise _unauthorized(
            "Missing authentication token. Include 'Authorization: Bearer <idToken>'."
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.strip().lower() != "bearer" or not token.strip():
        raise _unauthorized(
            "Invalid Authorization header. Expected 'Bearer <idToken>'."
        )
    return token.strip()


def get_current_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    """
    Resolve the current user from the ``Authorization: Bearer`` header.

    A valid token is not enough: the account must have a profile document
    (students/supervisors/admins collections) and must not be disabled. The
    role is derived from that profile, never from the token claims or the
    request body.
    """
    token = _extract_bearer_token(authorization)

    try:
        identity = auth_service.identity_from_token(token)
    except ValueError as e:
        raise _unauthorized(f"Invalid authentication token: {e}")

    profile, ref = locate_profile(identity["uid"])
    if profile is None:
        # Valid token but no profile -> the account was deleted or never
        # reconciled with a profile document.
        raise _unauthorized("User account not found")

    if profile.get("isActive") is False:
        raise _forbidden("Account is disabled")

    role = profile.get("role")
    if role not in VALID_ROLES:
        # Legacy profile without a role field: derive it from the collection
        # that owns the document (students -> user, etc.).
        collection = ref.parent.id if ref is not None else None
        role = next(
            (r for r, col in ROLE_COLLECTIONS.items() if col == collection),
            None,
        )
    if role not in VALID_ROLES:
        raise _forbidden("User account has no valid role")

    return CurrentUser(
        uid=identity["uid"],
        email=identity["email"],
        role=role,
        department=profile.get("department"),
        is_active=profile.get("isActive", True),
        preferred_language=profile.get("preferredLanguage"),
        profile=profile,
        auth_time=identity.get("auth_time"),
    )
