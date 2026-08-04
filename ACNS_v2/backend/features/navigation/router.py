"""
features/navigation/router.py — FastAPI router for campus navigation.

Endpoint:
    POST /api/navigation/route
    Body: NavigationRequest (campus_id, start_node, end_node, accessibility_mode)
    Returns: path coordinates list and route metadata.

Business logic lives in features/navigation/service.py.

Both endpoints require an authenticated user (campus maps and routing are an
authenticated feature).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import CurrentUser
from core.config import GENERIC_INTERNAL_ERROR_MESSAGE
from core.firebase import db
from core.permissions import require_authenticated
from core.ratelimit import rate_limited
from features.navigation.schemas import NavigationRequest
from features.navigation.service import calculate_route

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/route")
def get_route(
    request: NavigationRequest,
    _: None = Depends(rate_limited("navigation_route")),
    current_user: CurrentUser = Depends(require_authenticated),
):
    """
    Calculate the shortest accessible path between two campus nodes using A*.
    """
    try:
        result = calculate_route(
            campus_id=request.campus_id,
            start_node_id=request.start_node,
            end_node_id=request.end_node,
            accessibility_mode=request.accessibility_mode,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Navigation route unexpected error: %s", e)
        raise HTTPException(status_code=500, detail=GENERIC_INTERNAL_ERROR_MESSAGE)


@router.get("/campuses/{campus_id}/nodes")
def get_campus_nodes(
    campus_id: str,
    current_user: CurrentUser = Depends(require_authenticated),
):
    """
    Returns all landmark nodes for a given campus (used to populate frontend dropdowns).
    """
    campus_ref = db.collection("campuses").document(campus_id)
    nodes = []
    for doc in campus_ref.collection("nodes").stream():
        data = doc.to_dict()
        if data.get("is_landmark", False):
            nodes.append({"id": doc.id, **data})
    return {"campus_id": campus_id, "nodes": nodes}
