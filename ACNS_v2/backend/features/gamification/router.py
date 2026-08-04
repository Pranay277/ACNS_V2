"""
features/gamification/router.py — REST endpoints for the Gamification module.

All business logic lives in features/gamification/service.py; this router only
validates input and maps results to HTTP responses.

Authorization model:
    * GET /leaderboard      any authenticated user (public leaderboard).
    * GET /user/{userId}    the profile owner or an admin.
    * POST /award           admin only (manual point awards).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import CurrentUser
from core.config import GENERIC_INTERNAL_ERROR_MESSAGE, LEADERBOARD_DEFAULT_LIMIT, LEADERBOARD_MAX_LIMIT, POINTS_BY_REWARD
from core.ownership import require_self_or_admin
from core.permissions import require_admin, require_authenticated
from core.ratelimit import rate_limited
from features.gamification import service as gamification
from features.gamification.schemas import GamificationAward

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(LEADERBOARD_DEFAULT_LIMIT, ge=1, le=LEADERBOARD_MAX_LIMIT),
    current_user: CurrentUser = Depends(require_authenticated),
):
    """Top users by total points. Each entry includes rank, points, and report counts."""
    try:
        entries = gamification.get_leaderboard(limit=limit)
        return {"success": True, "leaderboard": entries}
    except Exception as e:
        logger.error("Failed to fetch leaderboard: %s", e)
        raise HTTPException(status_code=500, detail={"success": False, "message": GENERIC_INTERNAL_ERROR_MESSAGE})


@router.get("/user/{userId}")
def get_user(
    userId: str,
    current_user: CurrentUser = Depends(require_authenticated),
):
    """Gamification profile (points, stats, current rank). Only the owner or an admin."""
    require_self_or_admin(userId, current_user)
    try:
        profile = gamification.get_user_profile(userId)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": "User gamification profile not found"},
            )
        profile["rank"] = gamification.get_user_rank(userId)
        return {"success": True, "user": profile}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch gamification profile for %s: %s", userId, e)
        raise HTTPException(status_code=500, detail={"success": False, "message": GENERIC_INTERNAL_ERROR_MESSAGE})


@router.post("/award")
def award(
    payload: GamificationAward,
    _: None = Depends(rate_limited("gamification_award")),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Award points to a user (idempotent per ``issueId``). Admin-only.

    If ``points`` is omitted, the value configured for ``reason`` is used.
    This endpoint is the general hook for future reward types.
    """
    try:
        points = payload.points if payload.points is not None else gamification.points_for(payload.reason)
        if points == 0 and payload.points is None and payload.reason not in POINTS_BY_REWARD:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Unknown reward reason '{payload.reason}'. Known reasons: {list(POINTS_BY_REWARD.keys())}",
                },
            )
        profile = gamification.award_points(
            user_id=payload.userId,
            points=points,
            reason=payload.reason,
            issue_id=payload.issueId,
            display_name=payload.displayName,
        )
        return {"success": True, "user": profile}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to award points: %s", e)
        raise HTTPException(status_code=500, detail={"success": False, "message": GENERIC_INTERNAL_ERROR_MESSAGE})
