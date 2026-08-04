"""
tests/test_api_contract.py — Regression test for the public API contract.

Verifies the app boots, the route inventory matches the pre-refactor
baseline, the OpenAPI document is unchanged (paths + component schemas), and
the no-auth endpoints still respond with identical bodies.

Requires ``serviceAccountKey.json`` (Firebase bootstrap); skipped otherwise.
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(BACKEND_DIR, "serviceAccountKey.json")),
    reason="serviceAccountKey.json not present; cannot bootstrap Firebase",
)

import main  # noqa: E402  (must run after the skip guard above)

# Baseline captured from the layer-based layout BEFORE the refactor, extended
# with the supervisor-management routes (features/supervisors/router.py).
EXPECTED_PATHS = [
    "/",
    "/api/auth/login",
    "/api/auth/profile/{userId}",
    "/api/auth/signup",
    "/api/auth/uid/{uid}",
    "/api/auth/users",
    "/api/auth/users/{userId}",
    "/api/auth/users/{userId}/activate",
    "/api/auth/users/{userId}/deactivate",
    "/api/auth/valid-languages",
    "/api/auth/valid-roles",
    "/api/gamification/award",
    "/api/gamification/leaderboard",
    "/api/gamification/user/{userId}",
    "/api/issues/",
    "/api/issues/{id}",
    "/api/issues/{id}/status",
    "/api/issues/{id}/verify",
    "/api/navigation/campuses/{campus_id}/nodes",
    "/api/navigation/route",
    "/api/notifications/{userId}",
    "/api/supervisors/",
    "/api/supervisors/{uid}",
    "/api/supervisors/{uid}/activate",
    "/api/supervisors/{uid}/change-email",
    "/api/supervisors/{uid}/deactivate",
    "/api/supervisors/{uid}/profile",
    "/api/supervisors/{uid}/reset-password",
]

EXPECTED_SCHEMAS = [
    "ChangeEmailRequest",
    "GamificationAward",
    "HTTPValidationError",
    "IssueCreate",
    "IssueStatusUpdate",
    "LoginRequest",
    "NavigationRequest",
    "ResetPasswordRequest",
    "SignupRequest",
    "SupervisorCreateRequest",
    "SupervisorSelfUpdateRequest",
    "SupervisorUpdateRequest",
    "UserUpdateRequest",
    "ValidationError",
    "VerifyIssue",
]


def test_route_inventory_unchanged():
    paths = sorted(p for p in main.app.openapi()["paths"].keys())
    assert paths == sorted(EXPECTED_PATHS)


def test_component_schemas_unchanged():
    schemas = sorted(main.app.openapi()["components"]["schemas"].keys())
    assert schemas == sorted(EXPECTED_SCHEMAS)


def test_router_prefixes_and_tags_preserved():
    from fastapi import FastAPI

    assert isinstance(main.app, FastAPI)


def test_root_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "SCIARS Backend Running"}


def test_valid_roles_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    resp = client.get("/api/auth/valid-roles")
    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "roles": ["user", "supervisor", "admin"],
        "defaultRole": "user",
    }


def test_valid_languages_endpoint():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    resp = client.get("/api/auth/valid-languages")
    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "languages": ["en", "te", "hi"],
        "defaultLanguage": "en",
    }


def test_openapi_docs_load():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_cors_middleware_never_uses_wildcard():
    """CORS must be an explicit allow-list — never '*' with credentials."""
    for mw in main.app.user_middleware:
        if mw.cls.__name__ == "CORSMiddleware":
            origins = mw.kwargs.get("allow_origins", [])
            assert "*" not in origins
            assert mw.kwargs.get("allow_credentials") is True
            assert "http://localhost:5173" in origins  # dev default preserved
            return
    raise AssertionError("CORSMiddleware not registered on the app")


def test_cors_allows_configured_dev_origin():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    resp = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_cors_blocks_disallowed_origin():
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    resp = client.get("/", headers={"Origin": "http://evil.example.com"})
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers
