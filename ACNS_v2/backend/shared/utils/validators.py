"""
shared/utils/validators.py — Cross-feature validation helpers.

Used by the auth and profile flows to enforce the configured role and
preferred-language allowlists. The error messages are kept identical to the
original inline checks so API responses never change.
"""

import base64
import re
from urllib.parse import urlparse

from core.config import (
    ALLOWED_IMAGE_DATA_MIME_TYPES,
    ALLOWED_URL_SCHEMES,
    MAX_IMAGE_DATA_BYTES,
    MAX_URL_LENGTH,
    VALID_DEPARTMENTS,
    VALID_PREFERRED_LANGUAGES,
    VALID_ROLES,
)

# A base64 image data URL: data:image/<type>;base64,<payload>. The payload is
# intentionally left unpinned here so base64.b64decode(validate=True) does the
# strict alphabet/padding check.
_DATA_URL_PATTERN = re.compile(
    r"^data:image/(?P<mime>[a-z0-9.+-]+);base64,(?P<payload>.*)$",
    re.IGNORECASE | re.DOTALL,
)


def validate_role(role: str) -> None:
    """Raise ValueError when the role is not a configured valid role."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Valid roles: {VALID_ROLES}")


def validate_preferred_language(language: str) -> None:
    """Raise ValueError when the language code is not a supported one."""
    if language not in VALID_PREFERRED_LANGUAGES:
        raise ValueError(
            f"Invalid preferredLanguage '{language}'. "
            f"Valid languages: {VALID_PREFERRED_LANGUAGES}"
        )


def validate_department(department: str) -> None:
    """
    Raise ValueError when the department is missing or not in the catalog.

    Supervisor departments MUST come from the configured department catalog
    (``core.config.VALID_DEPARTMENTS``, derived from CATEGORY_TO_DEPARTMENT).
    Anything else — blank, unknown, or near-miss values — is rejected.
    """
    if not department or not str(department).strip():
        raise ValueError("department is required and cannot be empty")
    if department not in VALID_DEPARTMENTS:
        raise ValueError(
            f"Invalid department '{department}'. "
            f"Valid departments: {VALID_DEPARTMENTS}"
        )


# ══ Password policy (P2-08) ═════════════════════════════════════════════════════
# Minimum requirements for admin-provisioned credentials (supervisor creation
# and password resets). The same policy is mirrored by the frontend so users
# get immediate, clear feedback.
PASSWORD_MIN_LENGTH = 8
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"


def validate_password(password: str) -> str:
    """
    Validate a password against the application policy and return it.

    Requires at least 8 characters with an uppercase letter, a lowercase
    letter, a digit, and a special character. Raises ``ValueError`` listing
    every missing requirement so the caller (pydantic schema or service) can
    surface a precise, user-friendly message.
    """
    value = str(password or "")
    missing = []
    if len(value) < PASSWORD_MIN_LENGTH:
        missing.append(f"at least {PASSWORD_MIN_LENGTH} characters")
    if not any(c.isupper() for c in value):
        missing.append("an uppercase letter")
    if not any(c.islower() for c in value):
        missing.append("a lowercase letter")
    if not any(c.isdigit() for c in value):
        missing.append("a digit")
    if not any(c in PASSWORD_SPECIAL_CHARS for c in value):
        missing.append("a special character")
    if missing:
        raise ValueError("Password must include " + ", ".join(missing))
    return value


def validate_safe_url(value):
    """
    Validate a photo URL field for P2-01 (stored-XSS prevention).

    Accepts http/https URLs AND raster-image base64 data URLs. Performs trim +
    length cap + parse-level checks and rejects credentials (``user:pass@``)
    and every other scheme (``javascript:``, ``file:``, ``vbscript:``...).
    Image data URLs must be a raster MIME type (jpeg/png/gif/webp/bmp — SVG is
    rejected) with a strictly-valid base64 payload whose decoded size stays
    within ``MAX_IMAGE_DATA_BYTES``. Returns the trimmed URL, or ``None`` when
    the value is absent/blank (treated as "no image attached"). Raises
    ValueError for anything unsafe, which pydantic surfaces as a 422 on the
    field.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    value = value.strip()
    if not value:
        return None
    if value.lower().startswith("data:"):
        return validate_image_data_url(value)
    if len(value) > MAX_URL_LENGTH:
        raise ValueError(f"URL is too long (max {MAX_URL_LENGTH} characters)")
    parsed = urlparse(value)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError("Only http:// and https:// URLs are allowed")
    if not parsed.netloc:
        raise ValueError("URL is malformed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL must not contain credentials")
    return value


def validate_image_data_url(value: str) -> str:
    """
    Validate a base64 image data URL (``data:image/<type>;base64,<payload>``).

    Rejects non-raster types (SVG can embed script, HTML/other types are never
    images), malformed base64, empty payloads, and payloads that decode beyond
    ``MAX_IMAGE_DATA_BYTES``. Returns the original (trimmed) value on success.
    """
    match = _DATA_URL_PATTERN.match(value)
    if not match:
        raise ValueError("Only http/https URLs and raster image data URLs are allowed")
    mime = f"image/{match.group('mime').lower()}"
    if mime not in ALLOWED_IMAGE_DATA_MIME_TYPES:
        raise ValueError("Only JPEG, PNG, GIF, WebP, and BMP image data URLs are allowed")
    payload = match.group("payload")
    try:
        decoded = base64.b64decode(payload, validate=True)
    except (ValueError, TypeError):
        raise ValueError("Image data URL payload is not valid base64")
    if not decoded:
        raise ValueError("Image data URL payload is empty")
    if len(decoded) > MAX_IMAGE_DATA_BYTES:
        raise ValueError(
            f"Image data URL is too large (max {MAX_IMAGE_DATA_BYTES} bytes)"
        )
    return value
