"""
features/navigation/graph.py — Campus graph loading and the A* engine.

Pure graph mechanics: fetches nodes + edges for a campus from Firestore,
builds the adjacency list (filtering inaccessible edges in accessibility
mode), and runs the A* shortest-path search. No HTTP or routing concerns.
"""

import heapq

from core.firebase import db
from shared.utils.geo import haversine_meters as _haversine


def fetch_graph(campus_id: str, accessibility_mode: bool) -> tuple:
    """
    Fetch nodes and edges for the given campus from Firestore.

    Returns a tuple ``(nodes, adjacency)`` where ``nodes`` maps node id to its
    document data and ``adjacency`` is
      ``{ node_id: [(neighbor_id, distance_meters), ...] }``.
    In accessibility mode, edges with ``is_accessible=False`` are excluded.
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


def astar(start_id: str, end_id: str, nodes: dict, adjacency: dict) -> list | None:
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
