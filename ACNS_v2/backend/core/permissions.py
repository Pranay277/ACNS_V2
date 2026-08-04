"""
core/permissions.py — Role-based access guards for FastAPI endpoints.

Each guard is a FastAPI dependency built on ``get_current_user`` (401 is raised
there for missing/invalid tokens and disabled accounts). The guards here only
decide *who may call* an endpoint:

    require_authenticated  any verified, active user
    require_admin          admins only
    require_supervisor     supervisors or admins (admins may act as supervisors)
    require_student        students only (reporting/self-service surfaces)

Ownership of specific resources (e.g. an issue or a profile) is enforced
separately in ``core/ownership.py``.
"""

import time

from fastapi import Depends, HTTPException

from core.auth import CurrentUser, get_current_user
from core.config import FRESH_AUTH_MAX_AGE_SECONDS


def _forbidden(message: str):
    return HTTPException(
        status_code=403,
        detail={"success": False, "message": message},
    )


def _reauth_required():
    return HTTPException(
        status_code=403,
        detail={
            "success": False,
            "message": (
                "Your session is too old for this action. Please sign out and "
                "sign in again to confirm your identity."
            ),
            "code": "REAUTH_REQUIRED",
        },
    )


def require_authenticated(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Any verified, active user. Auth failures surface as 401/403 above."""
    return current_user


def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Admins only (supervisor/student accounts are rejected with 403)."""
    if current_user.role != "admin":
        raise _forbidden("Admin privileges required")
    return current_user


def require_supervisor(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Supervisors or admins (admins may act as supervisors)."""
    if current_user.role not in ("supervisor", "admin"):
        raise _forbidden("Supervisor privileges required")
    return current_user


def require_student(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Students only (the report-issue surface)."""
    if current_user.role != "user":
        raise _forbidden("Student privileges required")
    return current_user


def require_recent_auth(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Fresh-authentication guard for sensitive admin operations (P2-03).

    Requires the caller's ID token to have been minted within the last
    ``FRESH_AUTH_MAX_AGE_SECONDS`` (the Firebase ``auth_time`` claim). A stale
    — or unknown — sign-in is rejected with 403 + code ``REAUTH_REQUIRED`` so a
    long-lived stolen token cannot be used for account-lifecycle actions. The
    frontend responds by re-authenticating the admin and retrying the request.
    """
    auth_time = getattr(current_user, "auth_time", None)
    if not auth_time:
        raise _reauth_required()
    if (time.time() - float(auth_time)) > FRESH_AUTH_MAX_AGE_SECONDS:
        raise _reauth_required()
    return current_user
