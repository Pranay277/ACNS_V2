"""
features/navigation/service.py — Campus navigation business logic.

Responsibilities:
  1. Resolve the nearest landmark node for a GPS coordinate (used by issue
     reporting to stamp a building id).
  2. Compute the shortest accessible path between two campus nodes.

The graph loading + A* search live in features/navigation/graph.py.
"""

from core.firebase import db
from features.navigation.graph import astar, fetch_graph
from shared.utils.geo import haversine_meters as _haversine


def nearest_landmark(campus_id: str, lat: float, lng: float) -> str | None:
    """
    Return the id of the landmark node nearest to a GPS coordinate.

    Uses the campus navigation graph as the single source of truth for
    buildings/landmarks — no coordinate data is duplicated in issue documents.
    Returns ``None`` when the campus has no landmark nodes (or none readable).
    """
    campus_ref = db.collection("campuses").document(campus_id)
    best_id, best_dist = None, float("inf")
    for doc in campus_ref.collection("nodes").stream():
        data = doc.to_dict()
        if not data.get("is_landmark"):
            continue
        node_lat, node_lng = data.get("lat"), data.get("lng")
        if node_lat is None or node_lng is None:
            continue
        dist = _haversine(lat, lng, node_lat, node_lng)
        if dist < best_dist:
            best_dist, best_id = dist, doc.id
    return best_id


def calculate_route(
    campus_id: str,
    start_node_id: str,
    end_node_id: str,
    accessibility_mode: bool,
) -> dict:
    """
    Main function called by the FastAPI router.
    Returns a dict with path coordinates and metadata.
    """
    nodes, adjacency = fetch_graph(campus_id, accessibility_mode)

    # Validate nodes exist in this campus
    if start_node_id not in nodes:
        raise ValueError(f"Start node '{start_node_id}' not found in campus '{campus_id}'.")
    if end_node_id not in nodes:
        raise ValueError(f"End node '{end_node_id}' not found in campus '{campus_id}'.")

    path_ids = astar(start_node_id, end_node_id, nodes, adjacency)

    if path_ids is None:
        return {
            "success": False,
            "message": "No path found. The destination may be unreachable with current accessibility settings.",
            "path": [],
            "path_node_ids": [],
            "total_distance_meters": 0,
        }

    # Build coordinate list and calculate total distance
    path_coords = [[nodes[nid]["lat"], nodes[nid]["lng"]] for nid in path_ids]
    total_dist = sum(
        _haversine(
            nodes[path_ids[i]]["lat"], nodes[path_ids[i]]["lng"],
            nodes[path_ids[i + 1]]["lat"], nodes[path_ids[i + 1]]["lng"],
        )
        for i in range(len(path_ids) - 1)
    )

    return {
        "success": True,
        "message": "Route calculated successfully.",
        "path": path_coords,
        "path_node_ids": path_ids,
        "total_distance_meters": round(total_dist, 2),
        "accessibility_mode": accessibility_mode,
    }
