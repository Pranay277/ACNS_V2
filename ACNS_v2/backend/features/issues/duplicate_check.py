"""
features/issues/duplicate_check.py — Campus-aware duplicate issue detection.

Previous behaviour: two issues were duplicates when they shared a category,
were Open/In Progress, and were within a fixed 120 m radius (or had identical
free-text locations). That radius was too large for a campus, so reports in
nearby buildings (E Block vs C Block, ~75 m apart) were incorrectly merged.

New rule — a report is a duplicate only when ALL of these hold:

    1. Same campus.
    2. Same building/landmark (nearest landmark node from the navigation graph).
    3. Same category.
    4. Distance between the reports <= DUPLICATE_RADIUS_METERS (25 m).
    5. The existing issue is Open or In Progress.

The campus is resolved from the frontend ``college`` value (validated against
the ``campuses`` collection) with the reporter's profile campus as fallback.
The building is resolved to the nearest landmark node id of the campus graph.
"""

import logging

from core.config import DEFAULT_CAMPUS_ID
from core.firebase import db
from shared.utils.geo import haversine

logger = logging.getLogger(__name__)


# ── Campus resolution ───────────────────────────────────────────────────────────

_CAMPUS_INDEX = None


def _campus_index() -> list:
    """
    List of known campuses as ``(normalized_id, normalized_name, campus_id)``,
    lazily cached. The cache is rebuilt on demand so tests can add campuses.
    """
    global _CAMPUS_INDEX
    if _CAMPUS_INDEX is None:
        index = []
        for campus in db.collection("campuses").stream():
            data = campus.to_dict() or {}
            cid = campus.id
            index.append(
                (cid.strip().lower(), (data.get("name") or "").strip().lower(), cid)
            )
        _CAMPUS_INDEX = index
    return _CAMPUS_INDEX


def resolve_campus_id(college: str, fallback_campus_id: str) -> str:
    """
    Validate the frontend-selected college/campus and return a campus id.

    The frontend sends a display label (e.g. "Methodist College"); it is
    matched against known campus document ids/names — exactly, or as a
    substring of the campus name ("Methodist College" matches "Methodist
    College of Engineering & Technology"). The reporter's profile campus
    (``fallback_campus_id``) is used when the label is empty or does not
    resolve. The frontend value is never silently ignored — mismatches and
    unresolvable labels are logged.
    """
    label = (college or "").strip().lower()
    if not label:
        return fallback_campus_id or DEFAULT_CAMPUS_ID

    for norm_id, norm_name, campus_id in _campus_index():
        if (
            label == norm_id
            or label == norm_name
            or (norm_name and (label in norm_name or norm_name in label))
        ):
            if campus_id != (fallback_campus_id or DEFAULT_CAMPUS_ID):
                logger.warning(
                    "College '%s' resolves to campus '%s' but the user's profile campus is '%s'; "
                    "using the selected campus '%s'.",
                    college, campus_id, fallback_campus_id, campus_id,
                )
            return campus_id

    logger.warning(
        "College '%s' did not match any known campus; falling back to '%s'.",
        college, fallback_campus_id or DEFAULT_CAMPUS_ID,
    )
    return fallback_campus_id or DEFAULT_CAMPUS_ID


# ── Duplicate lookup ────────────────────────────────────────────────────────────

def find_duplicate_issue(
    category: str,
    campus_id: str,
    building_id: str,
    lat: float,
    lng: float,
    radius_meters: int,
) -> tuple | None:
    """
    Search for an existing issue that this report should merge into.

    Returns ``(issue_id, issue_data, distance_meters)`` when a duplicate is
    found, else ``None``. All five duplicate conditions must hold.

    Legacy data handling: an existing issue missing ``campusId`` or
    ``buildingId`` (pre-migration) is treated as a wildcard for that check, so
    backfilled history still merges correctly.
    """
    for doc in db.collection("issues").where("category", "==", category).stream():
        data = doc.to_dict()

        # 5. only Open / In Progress issues can be merged into
        if data.get("status") not in ("Open", "In Progress"):
            continue

        # 1. same campus (missing campusId = legacy wildcard)
        existing_campus = data.get("campusId")
        if existing_campus and existing_campus != campus_id:
            continue

        # 2. same building/landmark (missing buildingId = legacy wildcard)
        existing_building = data.get("buildingId")
        if building_id and existing_building and existing_building != building_id:
            continue

        # 3. same category — enforced by the Firestore query above

        # 4. distance within the duplicate radius
        loc = data.get("location") or {}
        if "lat" not in loc or "lng" not in loc:
            continue
        dist = haversine(lat, lng, loc["lat"], loc["lng"])
        if dist <= radius_meters:
            return doc.id, data, dist

    return None
