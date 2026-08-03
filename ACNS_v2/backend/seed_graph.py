"""
seed_graph.py — Idempotent seeding/upgrade script for the Methodist Campus navigation graph.

Run from backend directory (with venv activated):
    python seed_graph.py

Populates:
    campuses/methodist              (campus metadata document)
    campuses/methodist/nodes/{id}   (node subcollection)
    campuses/methodist/edges/{id}   (edge subcollection)

The Methodist graph contains two node types:
  * Landmark nodes (building entrances / destinations) — selected by users in
    the frontend dropdowns. These MUST remain untouched.
  * Route/checkpoint nodes (walkway intersections/turning points) — internal
    waypoints traversed by the A* engine to produce realistic walking paths.

This script only touches the Methodist campus document and its subcollections.
Other campuses (e.g. Osmania University) are never modified.

Edge weights are computed automatically from the node coordinates using the
Haversine formula — never hardcoded.
"""

import firebase_admin
from firebase_admin import credentials, firestore

from utils.geo import haversine_meters

# ── Firebase Init ──────────────────────────────────────────────────────────────
cred = credentials.Certificate("services/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ── Graph Data ─────────────────────────────────────────────────────────────────

CAMPUS_ID = "methodist"

CAMPUS_META = {
    "name": "Methodist College of Engineering & Technology",
    "center_lat": 17.39181094222161,
    "center_lng": 78.47856891694526,
    "zoom": 18,
    "boundary_coords": [
        {"lat": 17.39225, "lng": 78.47835},
        {"lat": 17.39225, "lng": 78.47900},
        {"lat": 17.39100, "lng": 78.47965},
        {"lat": 17.39050, "lng": 78.47930},
        {"lat": 17.39050, "lng": 78.47850},
    ],
}

# ── Landmark nodes (destinations — frontend selects ONLY these) ───────────────
# Coordinates are the existing building entrances and must remain unchanged.
LANDMARK_NODES = [
    {
        "id": "main-gate",
        "name": "Main Gate",
        "lat": 17.39220,
        "lng": 78.47855,
        "node_type": "gate",
        "is_landmark": True,
    },
    {
        "id": "a-block",
        "name": "A Block",
        "lat": 17.39187669271827,
        "lng": 78.478495032659,
        "node_type": "landmark",
        "is_landmark": True,
    },
    {
        "id": "b-block",
        "name": "B Block",
        "lat": 17.392086641041143,
        "lng": 78.47893504574874,
        "node_type": "landmark",
        "is_landmark": True,
    },
    {
        "id": "c-block",
        "name": "C Block",
        "lat": 17.390641250098902,
        "lng": 78.47929130229612,
        "node_type": "landmark",
        "is_landmark": True,
    },
    {
        "id": "d-block",
        "name": "D Block",
        "lat": 17.39157537237309,
        "lng": 78.47870037180208,
        "node_type": "landmark",
        "is_landmark": True,
    },
    {
        "id": "e-block",
        "name": "E Block",
        "lat": 17.39128050018839,
        "lng": 78.47951459282437,
        "node_type": "landmark",
        "is_landmark": True,
    },
]

# ── Route/checkpoint nodes (internal waypoints — never shown to users) ─────────
# GPS coordinates collected on campus; the actual walking path checkpoints.
ROUTE_NODES = [
    {
        "id": "methodist_main_gate",
        "name": "Main Gate Checkpoint",
        "description": "CP1 — Main Gate walkway",
        "lat": 17.392279565617674,
        "lng": 78.47863610073652,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_turn_a",
        "name": "Turning Point Near A Block",
        "description": "CP2 — Turning point near A Block",
        "lat": 17.39197050477921,
        "lng": 78.47852758839119,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_a_ground_turn",
        "name": "Turning From A Block to Ground",
        "description": "CP3 — Turning from A Block to Ground",
        "lat": 17.39189403603606,
        "lng": 78.47893781515639,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_central_intersection",
        "name": "Central Intersection",
        "description": "CP4 — Intersection between Ground, D Block and E Block",
        "lat": 17.391606082444927,
        "lng": 78.47900017651524,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_ground_center",
        "name": "Middle of the Ground",
        "description": "CP5 — Middle of the Ground",
        "lat": 17.39122302771189,
        "lng": 78.47901806280397,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_e_junction",
        "name": "Intersection Towards E Block",
        "description": "CP6 — Intersection towards E Block",
        "lat": 17.391580377351133,
        "lng": 78.47931948482595,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_e_front",
        "name": "In Front of E Block",
        "description": "CP7 — In front of E Block",
        "lat": 17.39139179855099,
        "lng": 78.47931967463172,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
    {
        "id": "methodist_c_front",
        "name": "In Front of C Block",
        "description": "CP8 — In front of C Block",
        "lat": 17.390880847095328,
        "lng": 78.47932082329075,
        "node_type": "checkpoint",
        "is_landmark": False,
    },
]

NODES = LANDMARK_NODES + ROUTE_NODES

# Edges are defined as (node_a_id, node_b_id, is_accessible, surface_type).
# distance_meters is calculated automatically via Haversine.
#
# Layout:
#   Landmark nodes connect to their NEAREST route checkpoint.
#   Route checkpoints connect only to ADJACENT checkpoints along the actual
#   walking path (Main Gate → ... → C Block) plus the ground crossing.
#   No landmark-to-landmark shortcuts, so A* always walks the checkpoint spine.
RAW_EDGES = [
    # ── Landmark ↔ nearest route checkpoint ───────────────────────────────
    ("main-gate",                 "methodist_main_gate",          True,  "paved"),
    ("a-block",                   "methodist_turn_a",             True,  "paved"),
    ("b-block",                   "methodist_a_ground_turn",      True,  "paved"),
    ("c-block",                   "methodist_c_front",            True,  "paved"),
    ("d-block",                   "methodist_central_intersection", True, "paved"),
    ("e-block",                   "methodist_e_front",            True,  "paved"),

    # ── Route spine — actual walking path ─────────────────────────────────
    ("methodist_main_gate",       "methodist_turn_a",             True,  "paved"),
    ("methodist_turn_a",          "methodist_a_ground_turn",      True,  "paved"),
    ("methodist_a_ground_turn",   "methodist_central_intersection", True, "paved"),
    ("methodist_central_intersection", "methodist_e_junction",    True,  "paved"),
    ("methodist_e_junction",      "methodist_e_front",            True,  "paved"),
    ("methodist_e_front",         "methodist_c_front",            True,  "paved"),

    # ── Ground crossing (central intersection ↔ middle of ground ↔ C Block) ─
    ("methodist_central_intersection", "methodist_ground_center", True,  "paved"),
    ("methodist_ground_center",   "methodist_c_front",            True,  "paved"),

    # ⚠ Inaccessible: stairs between D Block and C Block (accessibility reroute)
    ("d-block",                   "c-block",                      False, "stairs"),
]

# ── Seed Functions ─────────────────────────────────────────────────────────────

def seed_campus():
    print(f"📌 Writing campus metadata for '{CAMPUS_ID}'...")
    db.collection("campuses").document(CAMPUS_ID).set(CAMPUS_META)
    print("   ✅ Done.")

def seed_nodes():
    print(f"📍 Seeding {len(NODES)} nodes ({len(LANDMARK_NODES)} landmarks + {len(ROUTE_NODES)} route/checkpoints)...")
    node_map = {}
    campus_ref = db.collection("campuses").document(CAMPUS_ID)
    for node in NODES:
        node_id = node.pop("id")
        campus_ref.collection("nodes").document(node_id).set(node)
        node_map[node_id] = node
        kind = "landmark" if node.get("is_landmark") else "route"
        print(f"   ✅ Node '{node_id}' ({kind}) written.")
    return node_map

def seed_edges(node_map):
    print(f"🔗 Seeding {len(RAW_EDGES)} edges...")
    campus_ref = db.collection("campuses").document(CAMPUS_ID)
    for (a, b, accessible, surface) in RAW_EDGES:
        n_a = node_map[a]
        n_b = node_map[b]
        dist = round(haversine_meters(n_a["lat"], n_a["lng"], n_b["lat"], n_b["lng"]), 2)
        edge_id = f"edge_{a}__{b}"
        edge_doc = {
            "node_a": a,
            "node_b": b,
            "distance_meters": dist,
            "is_accessible": accessible,
            "is_bidirectional": True,
            "surface_type": surface,
        }
        campus_ref.collection("edges").document(edge_id).set(edge_doc)
        status = "♿ accessible" if accessible else "🚫 inaccessible (stairs)"
        print(f"   ✅ Edge '{a}' ↔ '{b}' | {dist}m | {status}")

def prune_stale(allowed_node_ids, allowed_edge_ids):
    """
    Remove nodes/edges in the Methodist campus that are no longer part of the
    canonical graph (e.g. the old VERIFY placeholder intersections). This keeps
    the seed script idempotent and only touches the Methodist campus.
    """
    campus_ref = db.collection("campuses").document(CAMPUS_ID)
    for doc in campus_ref.collection("nodes").stream():
        if doc.id not in allowed_node_ids:
            doc.reference.delete()
            print(f"   🗑 Removed stale node '{doc.id}'.")
    for doc in campus_ref.collection("edges").stream():
        if doc.id not in allowed_edge_ids:
            doc.reference.delete()
            print(f"   🗑 Removed stale edge '{doc.id}'.")

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Starting Methodist Campus Graph Seeding...\n")

    allowed_nodes = {n["id"] for n in NODES}
    allowed_edges = {f"edge_{a}__{b}" for (a, b, _, _) in RAW_EDGES}

    seed_campus()
    node_map = seed_nodes()
    seed_edges(node_map)
    prune_stale(allowed_nodes, allowed_edges)

    print(f"\n✅ All done! Methodist graph now has {len(NODES)} nodes and {len(RAW_EDGES)} edges.\n")
