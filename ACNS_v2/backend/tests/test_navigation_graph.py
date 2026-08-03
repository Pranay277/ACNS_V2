"""
tests/test_navigation_graph.py — Regression tests for the A* pathfinding
engine (pure graph logic, no Firestore needed).
"""

from features.navigation.graph import astar


def _simple_graph():
    nodes = {
        "gate": {"lat": 0.0, "lng": 0.0},
        "mid": {"lat": 0.001, "lng": 0.0},
        "block": {"lat": 0.002, "lng": 0.0},
        "far": {"lat": 0.003, "lng": 0.0},
    }
    adjacency = {
        "gate": [("mid", 100.0)],
        "mid": [("gate", 100.0), ("block", 100.0)],
        "block": [("mid", 100.0), ("far", 100.0)],
        "far": [("block", 100.0)],
    }
    return nodes, adjacency


def test_astar_finds_shortest_path():
    nodes, adjacency = _simple_graph()
    assert astar("gate", "far", nodes, adjacency) == ["gate", "mid", "block", "far"]


def test_astar_reverse_path():
    nodes, adjacency = _simple_graph()
    assert astar("far", "gate", nodes, adjacency) == ["far", "block", "mid", "gate"]


def test_astar_returns_none_for_disconnected():
    nodes = {"a": {"lat": 0.0, "lng": 0.0}, "b": {"lat": 0.0, "lng": 0.001}}
    adjacency = {"a": [], "b": []}
    assert astar("a", "b", nodes, adjacency) is None


def test_astar_prefers_cheaper_direct_edge():
    nodes = {
        "a": {"lat": 0.0, "lng": 0.0},
        "b": {"lat": 0.0, "lng": 0.001},
        "c": {"lat": 0.0, "lng": 0.002},
    }
    adjacency = {
        "a": [("c", 50.0), ("b", 1000.0)],
        "b": [("a", 1000.0), ("c", 1000.0)],
        "c": [("a", 50.0), ("b", 1000.0)],
    }
    assert astar("a", "c", nodes, adjacency) == ["a", "c"]


def test_astar_start_equals_end():
    nodes, adjacency = _simple_graph()
    assert astar("mid", "mid", nodes, adjacency) == ["mid"]
