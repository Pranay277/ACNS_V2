"""
shared/utils/geo.py — Shared geospatial utilities.

Single home for the Haversine great-circle distance used across the
application (duplicate detection, navigation pathfinding, graph seeding).
Modules that need coordinate math import from here instead of re-implementing
the formula, so a change in the distance model (e.g. Vincenty, a projection)
lands in exactly one place.
"""

import math

EARTH_RADIUS_METERS = 6371000


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Great-circle distance in meters between two GPS coordinates.

    Args:
        lat1, lng1: coordinates of the first point.
        lat2, lng2: coordinates of the second point.

    Returns:
        Distance in meters (unrounded). Callers that need a rounded value
        (e.g. the graph seeding script) round at the call site.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return EARTH_RADIUS_METERS * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Backwards-compatible alias — older callers imported `haversine`.
haversine = haversine_meters
