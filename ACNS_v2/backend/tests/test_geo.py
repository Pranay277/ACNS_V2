"""
tests/test_geo.py — Regression tests for the shared Haversine utilities.
"""

import math

from shared.utils.geo import EARTH_RADIUS_METERS, haversine, haversine_meters


def test_zero_distance():
    assert haversine_meters(17.39, 78.47, 17.39, 78.47) == 0.0


def test_alias_identical():
    assert haversine == haversine_meters


def test_one_degree_of_latitude():
    # One degree of latitude is ~111.2 km (roughly 1/360th of the meridian).
    dist = haversine_meters(0.0, 0.0, 1.0, 0.0)
    assert abs(dist - (math.pi * EARTH_RADIUS_METERS / 180.0)) < 0.5


def test_known_campus_distance():
    # Roughly southward along the same longitude: ~93 m per 0.00084 deg.
    dist = haversine_meters(17.3922, 78.47855, 17.3914, 78.47855)
    assert 80 < dist < 100


def test_symmetry():
    a = (17.3922, 78.47855)
    b = (17.3906, 78.47930)
    assert haversine_meters(*a, *b) == haversine_meters(*b, *a)
