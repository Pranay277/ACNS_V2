"""
tests/test_auth_revocation.py — Token-revocation regression tests (P2-03).

Pure unit tests: ``firebase_admin.auth`` is patched, so no Firebase project or
service account is required.
"""

import pytest

from features.auth import service as auth_service


def test_verify_id_token_always_checks_revocation(monkeypatch):
    captured = {}

    def _fake_verify(token, check_revoked):
        captured["check_revoked"] = check_revoked
        return {"uid": "u1", "email": "a@campus.edu"}

    monkeypatch.setattr(auth_service.admin_auth, "verify_id_token", _fake_verify)
    auth_service.verify_id_token("some-token")
    assert captured["check_revoked"] is True


def test_identity_from_token_surfaces_auth_time(monkeypatch):
    monkeypatch.setattr(
        auth_service.admin_auth,
        "verify_id_token",
        lambda token, check_revoked: {"uid": "u1", "email": "a@campus.edu", "auth_time": 123456},
    )
    identity = auth_service.identity_from_token("some-token")
    assert identity["uid"] == "u1"
    assert identity["auth_time"] == 123456


def test_identity_from_token_normalizes_missing_auth_time(monkeypatch):
    monkeypatch.setattr(
        auth_service.admin_auth,
        "verify_id_token",
        lambda token, check_revoked: {"uid": "u1", "email": "a@campus.edu"},
    )
    assert auth_service.identity_from_token("t")["auth_time"] is None


def test_identity_from_token_rejects_token_without_uid(monkeypatch):
    monkeypatch.setattr(
        auth_service.admin_auth,
        "verify_id_token",
        lambda token, check_revoked: {"email": "a@campus.edu"},
    )
    with pytest.raises(ValueError):
        auth_service.identity_from_token("t")


def test_revoke_refresh_tokens_calls_admin_sdk(monkeypatch):
    captured = []

    def _fake_revoke(uid):
        captured.append(uid)

    monkeypatch.setattr(auth_service.admin_auth, "revoke_refresh_tokens", _fake_revoke)
    auth_service.revoke_refresh_tokens("uid-123")
    assert captured == ["uid-123"]


def test_revoke_refresh_tokens_skips_empty_uid(monkeypatch):
    called = []

    def _fake_revoke(uid):
        called.append(uid)

    monkeypatch.setattr(auth_service.admin_auth, "revoke_refresh_tokens", _fake_revoke)
    auth_service.revoke_refresh_tokens("")
    auth_service.revoke_refresh_tokens(None)
    assert called == []


def test_revoke_refresh_tokens_never_raises(monkeypatch, caplog):
    def _boom(uid):
        raise RuntimeError("firebase unavailable")

    monkeypatch.setattr(auth_service.admin_auth, "revoke_refresh_tokens", _boom)
    # Must not raise — revocation is best-effort.
    auth_service.revoke_refresh_tokens("uid-123")
