"""
services/sms_service.py — SMS dispatch abstraction.

The notification service (``services/notify.py``) calls :func:`send_sms`; the
actual delivery is delegated to a provider selected via ``config.SMS_PROVIDER``.
Only the placeholder :class:`AndroidGatewayProvider` exists in this phase, so
``send_sms`` logs the request instead of delivering a real SMS.

``send_sms`` is intentionally best-effort: it never raises for provider
failures, so the issue-reporting workflow is never broken by an SMS problem.

Localization lives in dedicated template modules (``templates/sms/``), never
here. :func:`send_issue_assigned_sms` resolves a supervisor's preferred
language, loads the matching template, builds the body, and dispatches it.
"""

import logging

from config import SMS_PROVIDER
from providers.android_gateway import AndroidGatewayProvider
from templates import sms as sms_templates

logger = logging.getLogger(__name__)

_PROVIDERS = {
    "android_gateway": AndroidGatewayProvider,
}

_provider = _PROVIDERS.get(SMS_PROVIDER, AndroidGatewayProvider)()


def set_provider(provider) -> None:
    """
    Swap the active provider.

    Used by tests and by the future wiring step that connects the real
    Android SMS Gateway app.
    """
    global _provider
    _provider = provider


def get_provider():
    """Return the active provider instance (for inspection/tests)."""
    return _provider


def send_sms(phone_number: str, message: str) -> bool:
    """
    Dispatch an SMS through the active provider.

    Args:
        phone_number: recipient number (E.164 preferred).
        message: the SMS body.

    Returns:
        True if the provider accepted the request (or logged it), False when
        the recipient is missing or the provider raised.
    """
    if not phone_number or not str(phone_number).strip():
        logger.warning("send_sms skipped: no recipient phone number")
        return False

    try:
        _provider.send_sms(str(phone_number).strip(), message)
        logger.info("SMS dispatched to %s via %s", phone_number, type(_provider).__name__)
        return True
    except Exception as exc:  # noqa: BLE001 — provider failures must not break the workflow
        logger.error("SMS dispatch failed for %s: %s", phone_number, exc)
        return False


def build_issue_assigned_message(issue: dict, language: str = None) -> str:
    """
    Load the template for ``language`` and render the issue-assignment SMS.

    Args:
        issue: resolved issue context (see templates/sms/__init__.py).
        language: ISO 639-1 code; missing or unsupported codes fall back to
            English (handled by the template registry).

    Returns:
        The formatted SMS body in the requested language.
    """
    template = sms_templates.get_template(language)
    return template.build_issue_assigned_sms(issue)


def send_issue_assigned_sms(phone_number: str, issue: dict, language: str = None) -> bool:
    """
    Best-effort dispatch of a localized issue-assignment SMS.

    Flow: read preferredLanguage -> load template -> generate message ->
    send via TextBee. Provider failures are caught by :func:`send_sms` and
    never break the notification workflow.

    Args:
        phone_number: recipient number (E.164 preferred).
        issue: resolved issue context (see templates/sms/__init__.py).
        language: ISO 639-1 code; missing/unsupported falls back to English.

    Returns:
        True when the provider accepted the request, False otherwise.
    """
    message = build_issue_assigned_message(issue, language)
    return send_sms(phone_number, message)
