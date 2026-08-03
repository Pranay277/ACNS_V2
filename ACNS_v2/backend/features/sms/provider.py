"""
features/sms/provider.py — TextBee provider for an Android SMS Gateway.

Delivers outbound SMS through the TextBee gateway API (https://textbee.dev),
which forwards the message to a real phone running the TextBee Android app.
A delivery through the gateway is best-effort: the caller
(``features/sms/service.py``) wraps ``send_sms`` in try/except, so a TextBee
failure is logged and can never break the issue-reporting workflow.

Configuration is read from environment variables (backend/.env):

    TEXTBEE_API_KEY   — API key for the TextBee gateway.
    TEXTBEE_DEVICE_ID — id of the connected Android device on the gateway.
    TEXTBEE_BASE_URL  — gateway base URL (default https://api.textbee.dev).

The request follows the TextBee send-sms contract:

    POST {BASE_URL}/api/v1/gateway/devices/{DEVICE_ID}/send-sms
    headers: Content-Type: application/json, x-api-key: {API_KEY}
    body:    {"recipients": ["+91XXXXXXXXXX"], "message": "..."}
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load backend/.env so the TextBee credentials are available whenever this
# provider is imported (server startup, tests, scripts). Existing process
# environment variables take precedence over the .env file.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

TEXTBEE_API_KEY = (os.getenv("TEXTBEE_API_KEY") or "").strip()
TEXTBEE_DEVICE_ID = (os.getenv("TEXTBEE_DEVICE_ID") or "").strip()
TEXTBEE_BASE_URL = (os.getenv("TEXTBEE_BASE_URL") or "https://api.textbee.dev").strip().rstrip("/")

SEND_SMS_TIMEOUT_SECONDS = 10


class TextBeeError(RuntimeError):
    """Raised when the TextBee gateway rejects or cannot reach an SMS request."""


class AndroidGatewayProvider:
    """
    Sends SMS messages through the TextBee gateway to a connected Android phone.

    Attributes:
        name (str): stable provider identifier used in logs and audit records.
    """

    name = "android_gateway"

    def send_sms(self, phone_number: str, message: str) -> dict:
        """
        POST the SMS payload to the TextBee gateway.

        Args:
            phone_number: E.164 recipient number (e.g. +91XXXXXXXXXX).
            message: the SMS body to deliver.

        Returns:
            A delivery payload including the gateway HTTP status when accepted.

        Raises:
            TextBeeError: configuration is missing, the HTTP request itself
                failed (timeout / connection error), or the gateway returned a
                non-success status. The caller is expected to catch this.
        """
        if not TEXTBEE_API_KEY or not TEXTBEE_DEVICE_ID:
            raise TextBeeError(
                "TextBee is not configured: set TEXTBEE_API_KEY and "
                "TEXTBEE_DEVICE_ID in backend/.env"
            )

        url = f"{TEXTBEE_BASE_URL}/api/v1/gateway/devices/{TEXTBEE_DEVICE_ID}/send-sms"
        payload = {
            "recipients": [phone_number],
            "message": message,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": TEXTBEE_API_KEY,
        }
        timestamp = datetime.now().isoformat()

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=SEND_SMS_TIMEOUT_SECONDS
            )
        except Exception as exc:  # noqa: BLE001 — any transport failure becomes a TextBeeError
            raise TextBeeError(
                f"TextBee request failed for {phone_number}: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise TextBeeError(
                f"TextBee rejected SMS to {phone_number}: HTTP "
                f"{response.status_code} {response.text[:300]}"
            )

        logger.info(
            "[android-gateway] sent time=%s to=%s message=%s status=%s",
            timestamp,
            phone_number,
            repr(message),
            response.status_code,
        )
        return {
            "provider": self.name,
            "to": phone_number,
            "message": message,
            "timestamp": timestamp,
            "status": "sent",
            "httpStatus": response.status_code,
        }
