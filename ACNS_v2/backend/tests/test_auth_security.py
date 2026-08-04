"""
tests/test_auth_security.py — Security regression tests for the auth layer.

Verifies every endpoint family enforces the intended authorization model:

    * unauthenticated requests  -> 401 (missing / invalid / expired token)
    * disabled / deleted users  -> 403 / 401
    * admin-only surfaces       -> 403 for students and supervisors
    * ownership checks          -> 403 for cross-user access
    * client identity values    -> ignored in favor of the server-derived user

The current user is injected via ``app.dependency_overrides`` on
``core.auth.get_current_user`` (no real Firebase token needed), and every
database-touching service call is stubbed with ``monkeypatch`` so the tests
never hit Firestore.

Requires ``serviceAccountKey.json`` (Firebase bootstrap); skipped otherwise.
"""

import os
import sys
import time

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(BACKEND_DIR, "serviceAccountKey.json")),
    reason="serviceAccountKey.json not present; cannot bootstrap Firebase",
)

import main  # noqa: E402  (must run after the skip guard above)
from core.auth import CurrentUser, get_current_user  # noqa: E402


def make_user(role="user", uid="student-uid-1", email="student1@campus.edu", is_active=True, auth_time=None):
    # auth_time defaults to "now" so the sensitive-actions fresh-auth guard
    # (require_recent_auth) passes for tests that exercise admin surfaces.
    return CurrentUser(
        uid=uid,
        email=email,
        role=role,
        department="Water" if role == "supervisor" else None,
        is_active=is_active,
        preferred_language="en",
        profile={"uid": uid, "email": email, "role": role, "isActive": is_active},
        auth_time=time.time() if auth_time is None else auth_time,
    )


def _client(user=None):
    """TestClient with an optional injected current user (clears overrides)."""
    main.app.dependency_overrides.clear()
    if user is not None:
        main.app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    main.app.dependency_overrides.clear()


AUTH = {"Authorization": "Bearer some-token"}


# ── Token verification / authentication ────────────────────────────────────────


def test_protected_get_endpoints_require_token():
    client = _client()
    for method, path in [
        ("get", "/api/issues/"),
        ("get", "/api/issues/i1"),
        ("get", "/api/notifications/u1"),
        ("get", "/api/gamification/leaderboard"),
        ("get", "/api/gamification/user/u1"),
        ("get", "/api/supervisors/"),
        ("get", "/api/supervisors/s1"),
        ("get", "/api/auth/users"),
        ("get", "/api/auth/profile/u1"),
        ("get", "/api/auth/uid/u1"),
        ("get", "/api/navigation/campuses/methodist/nodes"),
    ]:
        resp = getattr(client, method)(path)
        assert resp.status_code == 401, f"{method.upper()} {path} should be 401 without a token"


def test_protected_post_endpoints_require_token():
    client = _client()
    for method, path, body in [
        ("post", "/api/issues/", {"userId": "x", "category": "Water", "description": "d",
                                 "lat": 17.39, "lng": 78.47, "locationText": "here"}),
        ("post", "/api/issues/i1/verify", {"verified": True}),
        ("post", "/api/gamification/award", {"userId": "u", "reason": "report_issue"}),
        ("post", "/api/supervisors/", {"email": "a@campus.edu", "displayName": "A", "department": "Water"}),
        ("post", "/api/navigation/route", {"campus_id": "methodist", "start_node": "a", "end_node": "b"}),
    ]:
        resp = getattr(client, method)(path, json=body)
        assert resp.status_code == 401, f"{method.upper()} {path} should be 401 without a token"


def test_invalid_token_is_rejected(monkeypatch):
    import features.auth.service as auth_service

    def _reject(token):
        raise ValueError("Invalid or expired token")

    monkeypatch.setattr(auth_service, "identity_from_token", _reject)
    client = _client()
    resp = client.get("/api/issues/", headers=AUTH)
    assert resp.status_code == 401


def test_disabled_user_is_forbidden(monkeypatch):
    import core.auth as core_auth
    import features.auth.service as auth_service

    monkeypatch.setattr(
        auth_service, "identity_from_token", lambda token: {"uid": "u1", "email": "u@campus.edu"}
    )
    monkeypatch.setattr(
        core_auth, "locate_profile", lambda uid: ({"uid": uid, "role": "user", "isActive": False}, None)
    )
    client = _client()
    resp = client.get("/api/issues/", headers=AUTH)
    assert resp.status_code == 403


def test_deleted_user_with_valid_token_is_rejected(monkeypatch):
    import core.auth as core_auth
    import features.auth.service as auth_service

    monkeypatch.setattr(
        auth_service, "identity_from_token", lambda token: {"uid": "u1", "email": "u@campus.edu"}
    )
    monkeypatch.setattr(core_auth, "locate_profile", lambda uid: (None, None))
    client = _client()
    resp = client.get("/api/issues/", headers=AUTH)
    assert resp.status_code == 401


def test_public_endpoints_remain_public():
    client = _client()
    assert client.get("/").status_code == 200
    assert client.get("/api/auth/valid-roles").status_code == 200
    assert client.get("/api/auth/valid-languages").status_code == 200


def test_login_endpoint_requires_no_bearer_header(monkeypatch):
    import features.auth.service as auth_service
    import features.profile.service as profile_service

    profile = {"uid": "u1", "email": "a@campus.edu", "role": "user", "isActive": True}
    monkeypatch.setattr(auth_service, "identity_from_token", lambda token: {"uid": "u1", "email": "a@campus.edu"})
    monkeypatch.setattr(profile_service, "ensure_user_profile", lambda **kw: profile)
    monkeypatch.setattr(profile_service, "record_login", lambda *a, **kw: profile)
    client = _client()
    resp = client.post("/api/auth/login", json={"idToken": "whatever"})
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "user"


# ── Role escalation / admin-only surfaces ──────────────────────────────────────


def test_student_is_rejected_from_admin_endpoints():
    client = _client(make_user("user"))
    assert client.get("/api/auth/users").status_code == 403
    assert client.patch("/api/auth/users/u1", json={"role": "admin"}).status_code == 403
    assert client.post("/api/auth/users/u1/deactivate").status_code == 403
    assert client.post("/api/auth/users/u1/activate").status_code == 403
    assert client.get("/api/supervisors/").status_code == 403
    assert client.post("/api/supervisors/", json={"email": "a@campus.edu", "displayName": "A",
                                                  "department": "Water"}).status_code == 403
    assert client.patch("/api/supervisors/s1", json={"displayName": "X"}).status_code == 403
    assert client.post("/api/supervisors/s1/change-email", json={"newEmail": "b@campus.edu"}).status_code == 403
    assert client.post("/api/supervisors/s1/deactivate").status_code == 403
    assert client.post("/api/supervisors/s1/activate").status_code == 403
    assert client.delete("/api/supervisors/s1").status_code == 403
    assert client.post("/api/supervisors/s1/reset-password", json={"newPassword": "secret"}).status_code == 403
    assert client.post("/api/gamification/award", json={"userId": "u", "reason": "report_issue"}).status_code == 403
    assert client.post("/api/issues/i1/verify", json={"verified": True}).status_code == 403


def test_supervisor_is_rejected_from_admin_endpoints():
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu"))
    assert client.get("/api/auth/users").status_code == 403
    assert client.patch("/api/auth/users/u1", json={"role": "admin"}).status_code == 403
    assert client.get("/api/supervisors/").status_code == 403
    assert client.delete("/api/supervisors/s1").status_code == 403
    assert client.post("/api/gamification/award", json={"userId": "u", "reason": "report_issue"}).status_code == 403
    assert client.post("/api/issues/i1/verify", json={"verified": True}).status_code == 403


def test_admin_can_access_admin_surfaces(monkeypatch):
    import features.gamification.service as gamification
    import features.issues.service as issues_service
    import features.profile.service as profile_service
    import features.supervisors.service as supervisors_service

    monkeypatch.setattr(issues_service, "verify_issue", lambda iid, payload: {"success": True, "message": "Closed"})
    monkeypatch.setattr(gamification, "award_points", lambda **kw: {"userId": kw["user_id"]})
    monkeypatch.setattr(supervisors_service, "list_supervisors", lambda include_inactive=False: [])
    monkeypatch.setattr(supervisors_service, "delete_supervisor", lambda uid: None)
    monkeypatch.setattr(profile_service, "list_users", lambda include_inactive=False: [])

    client = _client(make_user("admin", uid="admin-1", email="admin@campus.edu"))
    assert client.get("/api/auth/users").status_code == 200
    assert client.get("/api/supervisors/").status_code == 200
    assert client.delete("/api/supervisors/s1").status_code == 200
    assert client.post("/api/gamification/award", json={"userId": "u", "reason": "report_issue"}).status_code == 200
    assert client.post("/api/issues/i1/verify", json={"verified": True}).status_code == 200


# ── Issue workflow authorization ───────────────────────────────────────────────


def test_student_can_create_issue_and_userId_body_is_ignored(monkeypatch):
    import features.issues.service as issues_service

    captured = {}

    def fake_create(issue, reporter_uid, reporter_email=None):
        captured["reporter_uid"] = reporter_uid
        return {"success": True, "issueId": "i1", "assignedTo": "sup-1",
                "merged": False, "alreadyReported": False, "pointsAwarded": 10, "reportCount": 1}

    monkeypatch.setattr(issues_service, "create_issue", fake_create)
    client = _client(make_user("user"))
    resp = client.post("/api/issues/", json={
        "userId": "attacker-supplied-uid",
        "category": "Water",
        "description": "leak",
        "lat": 17.39,
        "lng": 78.47,
        "locationText": "block b",
    })
    assert resp.status_code == 200
    assert captured["reporter_uid"] == "student-uid-1"


def test_supervisor_cannot_create_issue():
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu"))
    resp = client.post("/api/issues/", json={
        "userId": "sup-1", "category": "Water", "description": "d",
        "lat": 17.39, "lng": 78.47, "locationText": "here",
    })
    assert resp.status_code == 403


def test_supervisor_can_update_assigned_issue(monkeypatch):
    import core.ownership as ownership
    import features.issues.service as issues_service

    monkeypatch.setattr(ownership, "_issue_doc", lambda issue_id: {"assignedTo": "sup-1", "status": "Open"})
    monkeypatch.setattr(issues_service, "update_issue_status", lambda iid, payload: {"success": True})
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu"))
    resp = client.put("/api/issues/i1/status", json={"status": "In Progress"})
    assert resp.status_code == 200


def test_supervisor_cannot_update_unassigned_issue(monkeypatch):
    import core.ownership as ownership

    monkeypatch.setattr(ownership, "_issue_doc", lambda issue_id: {"assignedTo": "sup-OTHER", "status": "Open"})
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu"))
    resp = client.put("/api/issues/i1/status", json={"status": "In Progress"})
    assert resp.status_code == 403


def test_student_cannot_update_issue_status():
    client = _client(make_user("user"))
    resp = client.put("/api/issues/i1/status", json={"status": "In Progress"})
    assert resp.status_code == 403


def test_student_can_view_own_issue(monkeypatch):
    import core.ownership as ownership
    import features.issues.service as issues_service

    monkeypatch.setattr(ownership, "_issue_doc", lambda issue_id: {"userId": "student-uid-1", "reportedBy": ["student-uid-1"]})
    monkeypatch.setattr(issues_service, "get_issue", lambda issue_id: {"success": True, "issue": {}})
    client = _client(make_user("user"))
    assert client.get("/api/issues/i1").status_code == 200


def test_student_cannot_view_others_issue(monkeypatch):
    import core.ownership as ownership

    monkeypatch.setattr(ownership, "_issue_doc", lambda issue_id: {"userId": "other-uid", "reportedBy": ["other-uid"]})
    client = _client(make_user("user"))
    assert client.get("/api/issues/i1").status_code == 403


def test_admin_can_view_any_issue(monkeypatch):
    import core.ownership as ownership
    import features.issues.service as issues_service

    monkeypatch.setattr(ownership, "_issue_doc", lambda issue_id: {"userId": "other-uid"})
    monkeypatch.setattr(issues_service, "get_issue", lambda issue_id: {"success": True, "issue": {}})
    client = _client(make_user("admin", uid="admin-1", email="admin@campus.edu"))
    assert client.get("/api/issues/i1").status_code == 200


# ── Ownership: profiles / gamification / notifications ─────────────────────────


def test_supervisor_can_update_own_profile(monkeypatch):
    import core.ownership as ownership
    import features.supervisors.service as supervisors_service

    monkeypatch.setattr(ownership, "_resolve_target_uid", lambda identifier: "sup-1")
    monkeypatch.setattr(supervisors_service, "update_self_profile", lambda uid, updates: {"success": True})
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu"))
    resp = client.patch("/api/supervisors/sup-1/profile", json={"displayName": "New"})
    assert resp.status_code == 200


def test_supervisor_cannot_update_other_supervisors_profile(monkeypatch):
    import core.ownership as ownership

    monkeypatch.setattr(ownership, "_resolve_target_uid", lambda identifier: "sup-OTHER")
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu"))
    resp = client.patch("/api/supervisors/sup-OTHER/profile", json={"displayName": "X"})
    assert resp.status_code == 403


def test_student_cannot_access_supervisor_profile_surface(monkeypatch):
    import core.ownership as ownership

    monkeypatch.setattr(ownership, "_resolve_target_uid", lambda identifier: "sup-1")
    client = _client(make_user("user"))
    assert client.get("/api/supervisors/s1").status_code == 403
    assert client.patch("/api/supervisors/s1/profile", json={"displayName": "X"}).status_code == 403


def test_student_can_view_own_gamification_profile(monkeypatch):
    import core.ownership as ownership
    import features.gamification.service as gamification

    monkeypatch.setattr(ownership, "_resolve_target_uid", lambda identifier: "student-uid-1")
    monkeypatch.setattr(gamification, "get_user_profile", lambda uid: {"userId": uid, "totalPoints": 5})
    monkeypatch.setattr(gamification, "get_user_rank", lambda uid: 3)
    client = _client(make_user("user"))
    assert client.get("/api/gamification/user/student-uid-1").status_code == 200


def test_student_cannot_view_other_users_gamification(monkeypatch):
    import core.ownership as ownership

    monkeypatch.setattr(ownership, "_resolve_target_uid", lambda identifier: "other-uid")
    client = _client(make_user("user"))
    assert client.get("/api/gamification/user/other-uid").status_code == 403


def test_admin_can_view_any_gamification_profile(monkeypatch):
    import features.gamification.service as gamification

    monkeypatch.setattr(gamification, "get_user_profile", lambda uid: {"userId": uid, "totalPoints": 5})
    monkeypatch.setattr(gamification, "get_user_rank", lambda uid: 3)
    client = _client(make_user("admin", uid="admin-1", email="admin@campus.edu"))
    assert client.get("/api/gamification/user/other-uid").status_code == 200


def test_notifications_are_scoped_to_current_user(monkeypatch):
    import features.notifications.service as notifications_service

    captured = {}
    monkeypatch.setattr(
        notifications_service,
        "get_user_notifications",
        lambda uid: captured.setdefault("uid", uid) or [],
    )
    client = _client(make_user("user", uid="student-uid-1"))
    resp = client.get("/api/notifications/someone-elses-uid")
    assert resp.status_code == 200
    assert captured["uid"] == "student-uid-1"


# ── Fresh-authentication guard (P2-03) ────────────────────────────────────────


def _fresh_client(monkeypatch, auth_time):
    import features.supervisors.service as supervisors_service

    # Stub the underlying service so a 200 proves the guard passed (not that
    # Firestore happened to answer). Construct the admin directly so auth_time
    # can be None (make_user treats None as "now").
    monkeypatch.setattr(supervisors_service, "deactivate_supervisor", lambda uid: None)
    user = CurrentUser(
        uid="admin-1",
        email="admin@campus.edu",
        role="admin",
        is_active=True,
        preferred_language="en",
        profile={"uid": "admin-1", "email": "admin@campus.edu", "role": "admin", "isActive": True},
        auth_time=auth_time,
    )
    return _client(user)


def test_stale_admin_session_is_rejected_for_sensitive_action(monkeypatch):
    stale = time.time() - 7200  # 2 hours ago, far past FRESH_AUTH_MAX_AGE_SECONDS (300)
    resp = _fresh_client(monkeypatch, stale).post("/api/supervisors/s1/deactivate")
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "REAUTH_REQUIRED"


def test_missing_auth_time_is_rejected_for_sensitive_action(monkeypatch):
    resp = _fresh_client(monkeypatch, None).post("/api/supervisors/s1/deactivate")
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "REAUTH_REQUIRED"


def test_fresh_admin_session_passes_sensitive_action(monkeypatch):
    resp = _fresh_client(monkeypatch, time.time()).post("/api/supervisors/s1/deactivate")
    assert resp.status_code == 200


def test_sensitive_actions_all_require_fresh_auth(monkeypatch):
    import features.supervisors.service as supervisors_service

    for name in ("activate_supervisor", "delete_supervisor", "deactivate_supervisor"):
        monkeypatch.setattr(supervisors_service, name, lambda uid: None)
    monkeypatch.setattr(
        supervisors_service, "change_supervisor_email", lambda uid, new_email: {"success": True}
    )
    monkeypatch.setattr(
        supervisors_service, "reset_supervisor_password", lambda uid, new_password: {"success": True}
    )

    client = _client(
        CurrentUser(
            uid="admin-1",
            email="admin@campus.edu",
            role="admin",
            is_active=True,
            preferred_language="en",
            profile={"uid": "admin-1", "email": "admin@campus.edu", "role": "admin", "isActive": True},
            auth_time=None,
        )
    )
    for method, path, body in [
        ("post", "/api/supervisors/s1/deactivate", None),
        ("post", "/api/supervisors/s1/activate", None),
        ("delete", "/api/supervisors/s1", None),
        ("post", "/api/supervisors/s1/change-email", {"newEmail": "b@campus.edu"}),
        ("post", "/api/supervisors/s1/reset-password", {"newPassword": "StrongPass1!"}),
        ("post", "/api/auth/users/u1/deactivate", None),
        ("post", "/api/auth/users/u1/activate", None),
    ]:
        kwargs = {} if body is None else {"json": body}
        resp = getattr(client, method)(path, **kwargs)
        assert resp.status_code == 403, f"{method.upper()} {path} should require fresh auth"
        assert resp.json()["detail"]["code"] == "REAUTH_REQUIRED"


def test_stale_supervisor_cannot_use_fresh_auth_surface():
    # Non-admins are rejected regardless of auth freshness.
    stale = time.time() - 7200
    client = _client(make_user("supervisor", uid="sup-1", email="sup1@campus.edu", auth_time=stale))
    resp = client.post("/api/supervisors/s1/deactivate")
    assert resp.status_code == 403
