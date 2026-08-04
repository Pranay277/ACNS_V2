"""
features/issues/router.py — REST endpoints for the issues feature.

Thin HTTP layer: every endpoint delegates to features/issues/service.py.
The service raises ``HTTPException`` for validation/domain errors (with the
same status codes and messages as before); anything unexpected is mapped to a
generic 500 message (details go to the backend logs only, never to clients).

Authorization model:
    * POST /            student-only; the reporter identity is CurrentUser.uid
      (the client-supplied ``userId`` in the body is ignored).
    * GET  /            any authenticated user; results are role-scoped from
      the token (admin -> all, supervisor -> assigned, student -> own).
    * GET  /{id}        admin any; supervisor assigned-or-reporter; student
      reporter only (enforced in core/ownership.py).
    * PUT  /{id}/status assigned supervisor (or admin) only.
    * POST /{id}/verify admin only.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import CurrentUser
from core.config import GENERIC_INTERNAL_ERROR_MESSAGE
from core.ownership import require_issue_assigned, require_issue_view_access
from core.permissions import require_admin, require_authenticated, require_student, require_supervisor
from core.ratelimit import rate_limited
from features.issues import service
from features.issues.schemas import IssueCreate, IssueStatusUpdate, VerifyIssue

logger = logging.getLogger(__name__)

router = APIRouter()


def _error(status_code: int, message: str):
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message},
    )


@router.post("/")
def create_issue(
    issue: IssueCreate,
    _: None = Depends(rate_limited("create_issue")),
    current_user: CurrentUser = Depends(require_student),
):
    try:
        logger.info(
            "Incoming issue: category=%s lat=%s lng=%s location=%s",
            issue.category,
            issue.lat,
            issue.lng,
            issue.locationText,
        )
        return service.create_issue(
            issue,
            reporter_uid=current_user.uid,
            reporter_email=current_user.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Issues API unexpected error: %s", e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.get("/")
def get_issues(current_user: CurrentUser = Depends(require_authenticated)):
    """
    List issues for the current user. The role and identity come from the
    token — any client-supplied ``role``/``userId`` query params are ignored.
    """
    try:
        return service.list_issues(current_user.role, current_user.uid)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Issues API unexpected error: %s", e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.get("/{id}")
def get_issue(
    id: str,
    current_user: CurrentUser = Depends(require_authenticated),
):
    """
    Fetch a single issue (for the Issue Details page).

    Returns the issue document enriched with display names for the campus and
    building (resolved from the ``campuses`` collection and its navigation
    graph), so the frontend never has to know internal ids. Best-effort
    enrichment — names fall back to ``None`` when the campus/building is
    unknown (legacy issues without ``campusId``/``buildingId``).
    """
    require_issue_view_access(id, current_user)
    try:
        return service.get_issue(id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Issues API unexpected error: %s", e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.put("/{id}/status")
def update_status(
    id: str,
    payload: IssueStatusUpdate,
    current_user: CurrentUser = Depends(require_supervisor),
):
    require_issue_assigned(id, current_user)
    try:
        return service.update_issue_status(id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Issues API unexpected error: %s", e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)


@router.post("/{id}/verify")
def verify_issue(
    id: str,
    payload: VerifyIssue,
    _: None = Depends(rate_limited("verify_issue")),
    current_user: CurrentUser = Depends(require_admin),
):
    try:
        return service.verify_issue(id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Issues API unexpected error: %s", e)
        raise _error(500, GENERIC_INTERNAL_ERROR_MESSAGE)
