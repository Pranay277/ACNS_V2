"""
shared/utils/validators.py — Cross-feature validation helpers.

Used by the auth and profile flows to enforce the configured role and
preferred-language allowlists. The error messages are kept identical to the
original inline checks so API responses never change.
"""

from core.config import VALID_PREFERRED_LANGUAGES, VALID_ROLES


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
    Raise ValueError when the department is missing or blank.

    Departments are open-ended strings (not an allowlist) so a future
    Firestore-driven department config never requires code changes here.
    """
    if not department or not str(department).strip():
        raise ValueError("department is required and cannot be empty")
