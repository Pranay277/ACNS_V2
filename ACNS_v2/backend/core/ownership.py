"""
core/ownership.py — Resource ownership checks.

Role guards (core/permissions.py) decide WHO may call an endpoint; these
helpers decide WHICH resource a caller may touch. They are plain functions that
raise ``HTTPException`` (403/404) and are called inside endpoint bodies with
the already-resolved ``CurrentUser``:

    require_self_or_admin(identifier, current_user)   profile-type resources
    require_issue_view_access(issue_id, current_user) GET /api/issues/{id}
    require_issue_assigned(issue_id, current_user)    PUT /api/issues/{id}/status

Issue ownership follows the existing model:
    admin        -> any issue
    supervisor   -> issues assigned to them (assignedTo uid, email resolved)
    student      -> issues they reported (userId or reportedBy)
"""

from fastapi import HTTPException

from core.auth import CurrentUser
from core.firebase import db
from features.profile.service import locate_profile, resolve_uid


def _forbidden(message: str):
    return HTTPException(
        status_code=403,
        detail={"success": False, "message": message},
    )


def _not_found(message: str):
    return HTTPException(
        status_code=404,
        detail={"success": False, "message": message},
    )


def _resolve_target_uid(identifier: str) -> str | None:
    """Resolve an email or uid identifier to the owner's uid via the profile store."""
    if not identifier:
        return None
    profile, _ref = locate_profile(identifier)
    return profile.get("uid") if profile else None


def require_self_or_admin(identifier: str, current_user: CurrentUser) -> None:
    """
    Allow the resource owner (identified by email or uid) or any admin.

    Used for profile-type reads/writes (user profiles, supervisor profiles,
    gamification profiles) where the caller may only touch their own data.
    """
    if current_user.role == "admin":
        return
    target_uid = _resolve_target_uid(identifier)
    if target_uid and target_uid == current_user.uid:
        return
    raise _forbidden("You do not have access to this resource")


def _issue_doc(issue_id: str) -> dict:
    doc = db.collection("issues").document(issue_id).get()
    if not doc.exists:
        raise _not_found("Issue not found")
    return doc.to_dict() or {}


def _is_assigned(data: dict, current_user: CurrentUser) -> bool:
    """True when the issue's assignedTo resolves to the current user's uid."""
    assigned = data.get("assignedTo")
    if not assigned:
        return False
    if assigned == current_user.uid:
        return True
    if "@" in str(assigned):
        return resolve_uid(assigned) == current_user.uid
    return False


def _is_reporter(data: dict, current_user: CurrentUser) -> bool:
    """True when the current user is the issue reporter."""
    if data.get("userId") == current_user.uid:
        return True
    return current_user.uid in (data.get("reportedBy") or [])


def require_issue_view_access(issue_id: str, current_user: CurrentUser) -> None:
    """
    Gate GET /api/issues/{id}: admin any; supervisor assigned-or-reporter;
    student reporter only.
    """
    data = _issue_doc(issue_id)
    if current_user.role == "admin":
        return
    if _is_assigned(data, current_user) or _is_reporter(data, current_user):
        return
    raise _forbidden("You do not have access to this issue")


def require_issue_assigned(issue_id: str, current_user: CurrentUser) -> None:
    """
    Gate PUT /api/issues/{id}/status: admin any; otherwise only the assigned
    supervisor may move the issue through its workflow.
    """
    data = _issue_doc(issue_id)
    if current_user.role == "admin":
        return
    if current_user.role != "supervisor":
        raise _forbidden("Only the assigned supervisor may update this issue")
    if not _is_assigned(data, current_user):
        raise _forbidden("Only the assigned supervisor may update this issue")
