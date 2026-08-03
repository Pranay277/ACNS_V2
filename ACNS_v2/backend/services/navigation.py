"""
services/navigation.py — A* Pathfinding Engine for ACNS_V2.

Responsibilities:
  1. Fetch campus graph (nodes + edges) from Firestore.
  2. Build an in-memory adjacency list, filtering inaccessible
     edges when accessibility_mode is True.
  3. Run the A* algorithm and return an ordered list of
     [lat, lng] coordinate pairs representing the shortest path.
"""

import heapq
from services.firebase_admin import db
from utils.geo import haversine_meters as _haversine


# ── Firestore Graph Loader ─────────────────────────────────────────────────────

def _fetch_graph(campus_id: str, accessibility_mode: bool) -> dict:
    """
    Fetches nodes and edges for the given campus from Firestore.
    Returns an adjacency list:
      { node_id: [(neighbor_id, distance_meters), ...] }
    If accessibility_mode=True, edges where is_accessible=False are excluded.
    """
    campus_ref = db.collection("campuses").document(campus_id)

    # Fetch all nodes
    nodes = {}
    for doc in campus_ref.collection("nodes").stream():
        nodes[doc.id] = doc.to_dict()

    if not nodes:
        raise ValueError(f"No nodes found for campus '{campus_id}'. Has the graph been seeded?")

    # Build adjacency list from edges
    adjacency: dict[str, list] = {node_id: [] for node_id in nodes}

    for doc in campus_ref.collection("edges").stream():
        edge = doc.to_dict()
        a = edge.get("node_a")
        b = edge.get("node_b")
        dist = edge.get("distance_meters", 0)
        accessible = edge.get("is_accessible", True)
        bidirectional = edge.get("is_bidirectional", True)

        # Skip inaccessible edges in accessibility mode
        if accessibility_mode and not accessible:
            continue

        # Skip edges referencing unknown nodes
        if a not in adjacency or b not in adjacency:
            continue

        adjacency[a].append((b, dist))
        if bidirectional:
            adjacency[b].append((a, dist))

    return nodes, adjacency


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


# ── A* Algorithm ──────────────────────────────────────────────────────────────

def _astar(start_id: str, end_id: str, nodes: dict, adjacency: dict) -> list | None:
    """
    A* pathfinding. Returns list of node IDs from start to end,
    or None if no path exists.
    """
    end_node = nodes[end_id]

    def heuristic(node_id: str) -> float:
        n = nodes[node_id]
        return _haversine(n["lat"], n["lng"], end_node["lat"], end_node["lng"])

    # Priority queue: (f_score, node_id)
    open_set = [(0 + heuristic(start_id), start_id)]
    came_from = {}
    g_score = {node_id: float("inf") for node_id in nodes}
    g_score[start_id] = 0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end_id:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start_id)
            path.reverse()
            return path

        for neighbor, weight in adjacency.get(current, []):
            tentative_g = g_score[current] + weight
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor)
                heapq.heappush(open_set, (f_score, neighbor))

    return None  # No path found


# ── Public Entry Point ─────────────────────────────────────────────────────────

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
    nodes, adjacency = _fetch_graph(campus_id, accessibility_mode)

    # Validate nodes exist in this campus
    if start_node_id not in nodes:
        raise ValueError(f"Start node '{start_node_id}' not found in campus '{campus_id}'.")
    if end_node_id not in nodes:
        raise ValueError(f"End node '{end_node_id}' not found in campus '{campus_id}'.")

    path_ids = _astar(start_node_id, end_node_id, nodes, adjacency)

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
