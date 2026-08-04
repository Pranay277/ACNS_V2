"""
features/notifications/router.py — REST endpoints for notifications.

Read logic lives in features/notifications/service.py; this router only maps
the path parameter to the service call.

The path ``userId`` is intentionally IGNORED: a user can only ever read their
OWN notifications. The recipient is always derived from the authenticated
caller's uid, so cross-user notification reads are impossible.
"""

from fastapi import APIRouter, Depends

from core.auth import CurrentUser
from core.permissions import require_authenticated
from features.notifications import service

router = APIRouter()


@router.get("/{userId}")
def get_notifications(
    userId: str,
    current_user: CurrentUser = Depends(require_authenticated),
):
    return service.get_user_notifications(current_user.uid)
