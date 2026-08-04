"""
features/supervisors/router.py — REST endpoints for the supervisors feature.

Thin HTTP layer over ``features/supervisors/service.py`` (mirrors the pattern
used by the issues/notifications routers). Domain/validation errors surface as
HTTPException with the same ``{"success": False, "message": ...}`` shape the
rest of the API uses; unexpected errors map to a 500.

Authorization model:
    * Everything is ADMIN-ONLY except two self-service paths:
        GET   /{uid}                -> the supervisor's own profile (or admin)
        PATCH /{uid}/profile        -> a supervisor editing their OWN profile
    * Students are rejected from the entire supervisor surface.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import CurrentUser
from core.config import GENERIC_INTERNAL_ERROR_MESSAGE
from core.ownership import require_self_or_admin
from core.permissions import require_admin, require_authenticated, require_recent_auth, require_supervisor
from core.ratelimit import rate_limited
from features.supervisors import service
from features.supervisors.schemas import (
    ChangeEmailRequest,
    ResetPasswordRequest,
    SupervisorCreateRequest,
    SupervisorSelfUpdateRequest,
    SupervisorUpdateRequest,
)

router = APIRouter()

logger = logging.getLogger(__name__)


def _error(status_code: int, message: str):
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message},
    )


@router.get("/")
def list_supervisors(
    includeInactive: bool = Query(False, description="Include disabled accounts"),
    current_user: CurrentUser = Depends(require_admin),
):
    """List supervisor profiles (active accounts by default). Admin-only."""
    try:
        return {
            "success": True,
            "supervisors": service.list_supervisors(include_inactive=includeInactive),
        }
    except Exception as e:  # noqa: BLE001
        logger.error("List supervisors failed: %s", e)
        raise _error(500, "Failed to list supervisors")


@router.post("/")
def create_supervisor(
    payload: SupervisorCreateRequest,
    _: None = Depends(rate_limited("create_supervisor")),
    current_user: CurrentUser = Depends(require_admin),
):
    """Create a supervisor (Firebase Auth account + profile). Admin-only."""
    try:
        result = service.create_supervisor(
            email=payload.email,
            display_name=payload.displayName,
            department=payload.department,
            phone_number=payload.phoneNumber,
            preferred_language=payload.preferredLanguage,
            campus_id=payload.campusId,
            password=payload.password,
        )
        return {"success": True, "supervisor": result}
    except ValueError as e:
        raise _error(400, str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Create supervisor failed: %s", e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.get("/{uid}")
def get_supervisor(
    uid: str,
    current_user: CurrentUser = Depends(require_authenticated),
):
    """Return a single supervisor profile by uid. The owner (a supervisor) or an admin."""
    require_self_or_admin(uid, current_user)
    try:
        profile = service.get_supervisor(uid)
        if not profile:
            raise _error(404, f"Supervisor not found for '{uid}'")
        return {"success": True, "supervisor": profile}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error("Get supervisor failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.patch("/{uid}")
def update_supervisor(
    uid: str,
    payload: SupervisorUpdateRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """Edit a supervisor (department, phone, language, display name). Admin-only."""
    try:
        updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        profile = service.update_supervisor(uid, updates)
        return {"success": True, "supervisor": profile}
    except ValueError as e:
        raise _error(400, str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Update supervisor failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.patch("/{uid}/profile")
def update_self_profile(
    uid: str,
    payload: SupervisorSelfUpdateRequest,
    current_user: CurrentUser = Depends(require_supervisor),
):
    """
    Supervisor self-service profile update (own profile only).

    Reuses the shared profile update path with a self-only whitelist, so only
    displayName, phoneNumber and preferredLanguage are applied; attempts to
    modify email, department, role, uid or isActive are ignored. The caller
    must be the profile owner (or an admin).
    """
    require_self_or_admin(uid, current_user)
    try:
        updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        profile = service.update_self_profile(uid, updates)
        return {"success": True, "supervisor": profile}
    except ValueError as e:
        raise _error(400, str(e))
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error("Self profile update failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.post("/{uid}/change-email")
def change_supervisor_email(
    uid: str,
    payload: ChangeEmailRequest,
    current_user: CurrentUser = Depends(require_admin),
    _fresh: CurrentUser = Depends(require_recent_auth),
):
    """
    Admin-only email change: updates Firebase Auth + the profile email field.
    The supervisor must use the new email for future logins. Requires the
    admin's session to be freshly authenticated.
    """
    try:
        profile = service.change_supervisor_email(uid, payload.newEmail)
        return {"success": True, "supervisor": profile}
    except ValueError as e:
        raise _error(400, str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Change supervisor email failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.post("/{uid}/deactivate")
def deactivate_supervisor(
    uid: str,
    current_user: CurrentUser = Depends(require_admin),
    _fresh: CurrentUser = Depends(require_recent_auth),
):
    """Disable a supervisor (block login + soft-delete profile). Admin-only; requires fresh auth."""
    try:
        return {"success": True, "supervisor": service.deactivate_supervisor(uid)}
    except Exception as e:  # noqa: BLE001
        logger.error("Deactivate supervisor failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.post("/{uid}/activate")
def activate_supervisor(
    uid: str,
    current_user: CurrentUser = Depends(require_admin),
    _fresh: CurrentUser = Depends(require_recent_auth),
):
    """Re-enable a disabled supervisor. Admin-only; requires fresh auth."""
    try:
        return {"success": True, "supervisor": service.activate_supervisor(uid)}
    except Exception as e:  # noqa: BLE001
        logger.error("Activate supervisor failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.delete("/{uid}")
def delete_supervisor(
    uid: str,
    current_user: CurrentUser = Depends(require_admin),
    _fresh: CurrentUser = Depends(require_recent_auth),
):
    """Permanently delete a supervisor (refused while open issues are assigned). Admin-only; requires fresh auth."""
    try:
        service.delete_supervisor(uid)
        return {"success": True, "message": f"Supervisor {uid} deleted"}
    except ValueError as e:
        raise _error(400, str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Delete supervisor failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.post("/{uid}/reset-password")
def reset_supervisor_password(
    uid: str,
    payload: ResetPasswordRequest,
    _: None = Depends(rate_limited("reset_password")),
    current_user: CurrentUser = Depends(require_admin),
    _fresh: CurrentUser = Depends(require_recent_auth),
):
    """Reset a supervisor's Firebase Auth password. Admin-only; requires fresh auth."""
    try:
        service.reset_supervisor_password(uid, payload.newPassword)
        return {"success": True, "message": f"Password reset for {uid}"}
    except ValueError as e:
        raise _error(400, str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("Reset password failed for %s: %s", uid, e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)
