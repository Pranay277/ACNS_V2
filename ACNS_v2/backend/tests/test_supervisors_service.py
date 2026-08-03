"""
tests/test_supervisors_service.py — Regression tests for the admin-managed
supervisor feature.

Covers the pure decision logic (department-based assignment + fallbacks) and the
validation guards that run before any Firestore write. Firestore/auth-touching
branches are monkeypatched so these tests never hit the database.
"""

import pytest

from core.config import CATEGORY_MAP, DEFAULT_SUPERVISOR_EMAIL
from features.supervisors import service as supervisors
from features.supervisors.service import (
    resolve_assigned_supervisor,
    resolve_supervisor_for_department,
)


class _FakeStream:
    """Minimal chainable stand-in: db.collection(...).where(...).stream()."""

    def __init__(self, docs):
        self._docs = docs

    def where(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def stream(self):
        yield from self._docs


class _FakeDoc:
    """Minimal Firestore document snapshot stand-in."""

    def __init__(self, doc_id, data):
        self.id = doc_id
        self.exists = True
        self._data = data

    def to_dict(self):
        return dict(self._data)


def _active_electrical_doc():
    return _FakeDoc(
        "electrical@campus.edu",
        {
            "department": "Electrical",
            "role": "supervisor",
            "isActive": True,
            "email": "electrical@campus.edu",
        },
    )


def test_resolve_supervisor_for_department_returns_active_supervisor(monkeypatch):
    monkeypatch.setattr(
        supervisors.db, "collection", lambda name: _FakeStream([_active_electrical_doc()])
    )
    result = resolve_supervisor_for_department("Electrical")
    assert result["email"] == "electrical@campus.edu"


def test_resolve_supervisor_for_department_skips_inactive(monkeypatch):
    doc = _FakeDoc(
        "electrical@campus.edu",
        {
            "department": "Electrical",
            "role": "supervisor",
            "isActive": False,
            "email": "electrical@campus.edu",
        },
    )
    monkeypatch.setattr(supervisors.db, "collection", lambda name: _FakeStream([doc]))
    assert resolve_supervisor_for_department("Electrical") is None


def test_resolve_assigned_supervisor_prefers_department_lookup(monkeypatch):
    monkeypatch.setattr(
        supervisors,
        "resolve_supervisor_for_department",
        lambda department: {"email": "electrical@campus.edu", "userId": "uid-electrical"},
    )
    assert resolve_assigned_supervisor("Electrical") == "uid-electrical"


def test_resolve_assigned_supervisor_falls_back_to_category_map(monkeypatch):
    monkeypatch.setattr(
        supervisors, "resolve_supervisor_for_department", lambda department: None
    )
    monkeypatch.setattr(
        supervisors, "resolve_uid", lambda email: "uid-" + email
    )
    assert resolve_assigned_supervisor("Water") == "uid-" + CATEGORY_MAP["Water"]


def test_resolve_assigned_supervisor_unknown_category_uses_default(monkeypatch):
    monkeypatch.setattr(
        supervisors, "resolve_supervisor_for_department", lambda department: None
    )
    monkeypatch.setattr(
        supervisors, "resolve_uid", lambda email: "uid-" + email
    )
    assert resolve_assigned_supervisor("UFO Sighting") == "uid-" + DEFAULT_SUPERVISOR_EMAIL


def test_create_supervisor_rejects_blank_department(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: None
    )
    with pytest.raises(ValueError, match="department is required"):
        supervisors.create_supervisor(
            email="electrical@campus.edu", display_name="E", department="   "
        )


def test_create_supervisor_rejects_existing_profile(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: {"role": "user"}
    )
    with pytest.raises(ValueError, match="already exists"):
        supervisors.create_supervisor(
            email="user1@gmail.com", display_name="U", department="Electrical"
        )


def test_update_supervisor_rejects_non_supervisor(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: {"role": "user"}
    )
    with pytest.raises(ValueError, match="not a supervisor"):
        supervisors.update_supervisor("user1@gmail.com", {"department": "Electrical"})


def test_update_supervisor_rejects_missing_profile(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: None
    )
    with pytest.raises(ValueError, match="No profile found"):
        supervisors.update_supervisor("ghost@campus.edu", {"phoneNumber": "123"})


def test_delete_supervisor_guards_open_issues(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: {"role": "supervisor"}
    )
    monkeypatch.setattr(supervisors, "_has_open_issues", lambda email: True)
    with pytest.raises(ValueError, match="Open/In Progress"):
        supervisors.delete_supervisor("electrical@campus.edu")


def test_supervisor_updatable_fields_whitelist():
    assert "department" in supervisors.SUPERVISOR_UPDATABLE_FIELDS
    assert "role" not in supervisors.SUPERVISOR_UPDATABLE_FIELDS


def test_update_self_profile_rejects_missing_profile(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: None
    )
    with pytest.raises(ValueError, match="No profile found"):
        supervisors.update_self_profile("ghost@campus.edu", {"displayName": "X"})


def test_update_self_profile_rejects_non_supervisor(monkeypatch):
    monkeypatch.setattr(
        supervisors.profile_service, "get_user_profile", lambda email: {"role": "user"}
    )
    with pytest.raises(ValueError, match="not a supervisor"):
        supervisors.update_self_profile("user1@gmail.com", {"displayName": "X"})


def test_update_self_profile_only_allows_whitelisted_fields(monkeypatch):
    captured = {}

    def fake_update(user_id, updates, restricted_fields):
        captured["user_id"] = user_id
        captured["updates"] = updates
        captured["restricted_fields"] = restricted_fields
        return {"role": "supervisor", "displayName": "New Name"}

    monkeypatch.setattr(
        supervisors.profile_service,
        "get_user_profile",
        lambda email: {"role": "supervisor"},
    )
    monkeypatch.setattr(
        supervisors.profile_service, "update_user_profile", fake_update
    )
    result = supervisors.update_self_profile(
        "uid-electrical",
        {
            "displayName": "New Name",
            "phoneNumber": "+919999999999",
            "preferredLanguage": "te",
            "email": "hacker@evil.com",
            "department": "Hacked",
            "role": "admin",
            "uid": "other-uid",
            "isActive": False,
        },
    )
    assert captured["user_id"] == "uid-electrical"
    assert captured["restricted_fields"] == {
        "displayName",
        "phoneNumber",
        "preferredLanguage",
    }
    assert result == {"role": "supervisor", "displayName": "New Name"}
