"""
tests/test_rate_limiting.py — P2-02 in-memory rate-limiting regression tests.

Exercises core/ratelimit.py directly: fixed-window semantics, per-client
isolation, window rollover, HTTP 429 enforcement, and the disabled switch.
Pure logic — no Firebase is touched.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from core.ratelimit import rate_limited, rate_limiter


class _FakeRequest:
    """Minimal stand-in for a FastAPI Request (only .client.host is used)."""

    def __init__(self, host):
        self.client = SimpleNamespace(host=host)


@pytest.fixture(autouse=True)
def _reset_limiter():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_allows_requests_within_limit():
    dep = rate_limited("login")
    for _ in range(20):
        assert dep(_FakeRequest("1.2.3.4")) is None


def test_rejects_with_429_after_limit():
    dep = rate_limited("login")
    for _ in range(20):
        dep(_FakeRequest("1.2.3.4"))
    with pytest.raises(HTTPException) as exc:
        dep(_FakeRequest("1.2.3.4"))
    assert exc.value.status_code == 429
    assert exc.value.detail["success"] is False
    assert exc.value.detail["message"]
    assert exc.value.detail["retryAfter"] > 0


def test_clients_are_isolated():
    dep = rate_limited("login")
    for _ in range(20):
        dep(_FakeRequest("1.2.3.4"))
    assert dep(_FakeRequest("5.6.7.8")) is None


def test_scopes_are_isolated():
    for _ in range(20):
        rate_limited("login")(_FakeRequest("1.2.3.4"))
    assert rate_limited("signup")(_FakeRequest("1.2.3.4")) is None


def test_window_rolls_over():
    assert rate_limiter.allow("login", "key", 1, 60, now=100.0) is True
    assert rate_limiter.allow("login", "key", 1, 60, now=100.5) is False
    assert rate_limiter.allow("login", "key", 1, 60, now=160.1) is True


def test_disabled_via_config(monkeypatch):
    import core.ratelimit as ratelimit_module

    monkeypatch.setattr(ratelimit_module, "RATE_LIMIT_ENABLED", False)
    dep = ratelimit_module.rate_limited("login")
    for _ in range(50):
        assert dep(_FakeRequest("1.2.3.4")) is None
