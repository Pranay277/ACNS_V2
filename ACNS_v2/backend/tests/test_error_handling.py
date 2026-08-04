"""
tests/test_error_handling.py — P2-04 error-leakage regression tests.

Unexpected exceptions must surface as a generic 500 message — never the raw
``str(e)`` which can leak internals. Domain errors (ValueError) keep their
user-facing messages. Router endpoints are invoked directly with stubbed
dependencies; no Firebase is touched.
"""

import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from core.config import GENERIC_INTERNAL_ERROR_MESSAGE
from features.gamification import router as gamification_router
from features.gamification import service as gamification_service
from features.gamification.schemas import GamificationAward
from features.issues import router as issues_router
from features.issues import service as issues_service
from features.issues.schemas import IssueCreate
from features.navigation import router as navigation_router
from features.navigation.schemas import NavigationRequest


def _throw(exc):
    def _raises(*args, **kwargs):
        raise exc

    return _raises


# ── Issues router ──────────────────────────────────────────────────────────────


def test_issues_create_issue_500_is_generic(monkeypatch):
    monkeypatch.setattr(
        issues_service,
        "create_issue",
        _throw(RuntimeError("sensitive connection string leaked: secret-dsn-123")),
    )
    issue = IssueCreate(
        userId="u1",
        category="Water",
        description="leak",
        lat=17.39,
        lng=78.47,
        locationText="Block B",
    )
    current_user = SimpleNamespace(uid="u1", email="a@b.c")
    with pytest.raises(HTTPException) as exc:
        issues_router.create_issue(issue=issue, current_user=current_user, _=None)
    assert exc.value.status_code == 500
    assert exc.value.detail["message"] == GENERIC_INTERNAL_ERROR_MESSAGE
    assert "secret-dsn-123" not in str(exc.value.detail)


# ── Navigation router ──────────────────────────────────────────────────────────


def test_navigation_route_500_is_generic(monkeypatch):
    monkeypatch.setattr(
        navigation_router,
        "calculate_route",
        _throw(RuntimeError("internal graph corruption: edge/42")),
    )
    request = NavigationRequest(campus_id="methodist", start_node="a", end_node="b")
    with pytest.raises(HTTPException) as exc:
        navigation_router.get_route(request=request, current_user=object(), _=None)
    assert exc.value.status_code == 500
    assert exc.value.detail == GENERIC_INTERNAL_ERROR_MESSAGE
    assert "edge/42" not in str(exc.value.detail)


def test_navigation_route_value_error_keeps_user_facing_message(monkeypatch):
    monkeypatch.setattr(
        navigation_router, "calculate_route", _throw(ValueError("Invalid node id: e-block"))
    )
    request = NavigationRequest(campus_id="methodist", start_node="a", end_node="b")
    with pytest.raises(HTTPException) as exc:
        navigation_router.get_route(request=request, current_user=object(), _=None)
    assert exc.value.status_code == 404
    assert "Invalid node id" in str(exc.value.detail)


# ── Gamification router ────────────────────────────────────────────────────────


def test_gamification_leaderboard_500_is_generic(monkeypatch):
    monkeypatch.setattr(
        gamification_service,
        "get_leaderboard",
        _throw(RuntimeError("firestore internal endpoint: projects/x/databases/(default)")),
    )
    with pytest.raises(HTTPException) as exc:
        gamification_router.get_leaderboard(limit=10, current_user=object())
    assert exc.value.status_code == 500
    assert exc.value.detail["message"] == GENERIC_INTERNAL_ERROR_MESSAGE
    assert "projects/x" not in str(exc.value.detail)


def test_gamification_award_500_is_generic(monkeypatch):
    monkeypatch.setattr(
        gamification_service,
        "award_points",
        _throw(RuntimeError("internal award pipeline failure")),
    )
    payload = GamificationAward(userId="u1", reason="report_issue", points=10)
    with pytest.raises(HTTPException) as exc:
        gamification_router.award(payload=payload, current_user=object(), _=None)
    assert exc.value.status_code == 500
    assert exc.value.detail["message"] == GENERIC_INTERNAL_ERROR_MESSAGE
    assert "pipeline" not in str(exc.value.detail)
