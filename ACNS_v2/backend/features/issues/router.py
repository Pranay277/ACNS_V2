"""
features/issues/router.py — REST endpoints for the issues feature.

Thin HTTP layer: every endpoint delegates to features/issues/service.py.
The service raises ``HTTPException`` for validation/domain errors (with the
same status codes and messages as before); anything unexpected is mapped to a
500 with the original message.
"""

import logging

from fastapi import APIRouter, HTTPException

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
def create_issue(issue: IssueCreate):
    try:
        logger.info(
            "Incoming issue: category=%s lat=%s lng=%s location=%s",
            issue.category,
            issue.lat,
            issue.lng,
            issue.locationText,
        )
        return service.create_issue(issue)
    except HTTPException:
        raise
    except Exception as e:
        raise _error(500, str(e))


@router.get("/")
def get_issues(role: str, userId: str = None, email: str = None):
    try:
        return service.list_issues(role, userId, email)
    except HTTPException:
        raise
    except Exception as e:
        raise _error(500, str(e))


@router.get("/{id}")
def get_issue(id: str):
    """
    Fetch a single issue (for the Issue Details page).

    Returns the issue document enriched with display names for the campus and
    building (resolved from the ``campuses`` collection and its navigation
    graph), so the frontend never has to know internal ids. Best-effort
    enrichment — names fall back to ``None`` when the campus/building is
    unknown (legacy issues without ``campusId``/``buildingId``).
    """
    try:
        return service.get_issue(id)
    except HTTPException:
        raise
    except Exception as e:
        raise _error(500, str(e))


@router.put("/{id}/status")
def update_status(id: str, payload: IssueStatusUpdate):
    try:
        return service.update_issue_status(id, payload)
    except HTTPException:
        raise
    except Exception as e:
        raise _error(500, str(e))


@router.post("/{id}/verify")
def verify_issue(id: str, payload: VerifyIssue):
    try:
        return service.verify_issue(id, payload)
    except HTTPException:
        raise
    except Exception as e:
        raise _error(500, str(e))
