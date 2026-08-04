"""
tests/test_sms_logging.py — Log-hygiene regression tests (P2-07).

Guards the rule that SMS-related logs NEVER contain a raw phone number, the
SMS body, a password, or a token. Recipients are masked before logging, and
provider-level error messages are masked too.
"""

import logging

import pytest

from features.sms import service as sms_service
from features.sms.provider import AndroidGatewayProvider, mask_phone


# ── mask_phone ─────────────────────────────────────────────────────────────────


def test_mask_phone_hides_middle():
    # "+919876543210" (13 chars) -> keep first 3, mask middle 8, keep last 2.
    assert mask_phone("+919876543210") == "+91********10"


def test_mask_phone_short_numbers_are_fully_redacted():
    assert mask_phone("123456") == "***"


def test_mask_phone_empty_is_redacted():
    assert mask_phone("") == "***"
    assert mask_phone(None) == "***"


# ── Provider success log (never the raw phone or the message body) ─────────────


def test_provider_success_log_masks_phone_and_omits_body(monkeypatch, caplog):
    import features.sms.provider as provider_mod

    class _FakeResponse:
        status_code = 200

        @property
        def text(self):
            return ""

    monkeypatch.setattr(provider_mod.requests, "post", lambda *a, **kw: _FakeResponse())

    with caplog.at_level(logging.INFO, logger="features.sms.provider"):
        AndroidGatewayProvider().send_sms("+919876543210", "TopSecretMessage123")

    records = caplog.records
    assert records, "expected a success log record"
    joined = "\n".join(r.getMessage() for r in records)
    assert "TopSecretMessage123" not in joined
    assert "+919876543210" not in joined
    assert "+91********10" in joined


# ── Provider failure logs also mask the phone ──────────────────────────────────


def test_provider_transport_error_log_masks_phone(monkeypatch):
    import features.sms.provider as provider_mod

    def _boom(*a, **kw):
        raise ConnectionError("connect refused")

    monkeypatch.setattr(provider_mod.requests, "post", _boom)

    with pytest.raises(Exception) as exc:
        AndroidGatewayProvider().send_sms("+919876543210", "TopSecretMessage123")
    message = str(exc.value)
    assert "TopSecretMessage123" not in message
    assert "+919876543210" not in message
    assert "+91********10" in message


def test_provider_http_error_log_masks_phone(monkeypatch):
    import features.sms.provider as provider_mod

    class _FakeResponse:
        status_code = 500

        @property
        def text(self):
            return "gateway exploded"

    monkeypatch.setattr(provider_mod.requests, "post", lambda *a, **kw: _FakeResponse())

    with pytest.raises(Exception) as exc:
        AndroidGatewayProvider().send_sms("+919876543210", "TopSecretMessage123")
    message = str(exc.value)
    assert "+919876543210" not in message
    assert "+91********10" in message


# ── Service-level dispatch logs ────────────────────────────────────────────────


def test_service_success_log_masks_phone(monkeypatch, caplog):
    class _FakeProvider:
        name = "fake"

        def send_sms(self, phone, message):
            return {}

    monkeypatch.setattr(sms_service, "_provider", _FakeProvider())

    with caplog.at_level(logging.INFO, logger="features.sms.service"):
        ok = sms_service.send_sms("+919876543210", "TopSecretMessage123")

    assert ok is True
    joined = "\n".join(r.getMessage() for r in caplog.records)
    assert "TopSecretMessage123" not in joined
    assert "+919876543210" not in joined
    assert "+91********10" in joined


def test_service_failure_log_masks_phone(monkeypatch, caplog):
    class _FailingProvider:
        name = "fake"

        def send_sms(self, phone, message):
            raise RuntimeError("upstream down")

    monkeypatch.setattr(sms_service, "_provider", _FailingProvider())

    with caplog.at_level(logging.ERROR, logger="features.sms.service"):
        ok = sms_service.send_sms("+919876543210", "TopSecretMessage123")

    assert ok is False
    joined = "\n".join(r.getMessage() for r in caplog.records)
    assert "TopSecretMessage123" not in joined
    assert "+919876543210" not in joined
    assert "+91********10" in joined
