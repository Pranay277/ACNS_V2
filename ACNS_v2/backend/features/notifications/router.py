"""
features/notifications/router.py — REST endpoints for notifications.

Read logic lives in features/notifications/service.py; this router only maps
the path parameter to the service call.
"""

from fastapi import APIRouter

from features.notifications import service

router = APIRouter()


@router.get("/{userId}")
def get_notifications(userId: str):
    return service.get_user_notifications(userId)
