"""
tests/test_validators.py — Regression tests for the shared validators and the
profile payload builder (guards the extracted validation behavior and its
exact error messages).
"""

import pytest

from core.config import DEFAULT_PREFERRED_LANGUAGE, DEFAULT_ROLE, VALID_DEPARTMENTS
from features.profile.service import build_profile_payload
from shared.utils.validators import (
    validate_department,
    validate_password,
    validate_preferred_language,
    validate_role,
)


def test_validate_role_accepts_valid():
    validate_role("supervisor")


def test_validate_role_rejects_invalid_with_original_message():
    with pytest.raises(ValueError) as exc:
        validate_role("moderator")
    assert str(exc.value) == (
        "Invalid role 'moderator'. Valid roles: ['user', 'supervisor', 'admin']"
    )


def test_validate_preferred_language_accepts_valid():
    validate_preferred_language("te")


def test_validate_preferred_language_rejects_invalid_with_original_message():
    with pytest.raises(ValueError) as exc:
        validate_preferred_language("fr")
    assert str(exc.value) == (
        "Invalid preferredLanguage 'fr'. Valid languages: ['en', 'te', 'hi']"
    )


def test_build_profile_payload_defaults():
    payload = build_profile_payload(uid="uid-1", email="student@campus.edu")
    assert payload["role"] == DEFAULT_ROLE
    assert payload["preferredLanguage"] == DEFAULT_PREFERRED_LANGUAGE
    assert payload["isActive"] is True


def test_build_profile_payload_rejects_invalid_role():
    with pytest.raises(ValueError):
        build_profile_payload(uid="u", email="a@b.c", role="hacker")


def test_build_profile_payload_rejects_invalid_language():
    with pytest.raises(ValueError):
        build_profile_payload(uid="u", email="a@b.c", preferred_language="xx")


def test_validate_department_accepts_valid():
    validate_department("Electrical")


def test_validate_department_accepts_every_catalog_entry():
    # P2-09 — the department catalog is the authoritative allowlist and must be
    # accepted in full.
    for department in VALID_DEPARTMENTS:
        validate_department(department)


def test_validate_department_rejects_empty_with_original_message():
    with pytest.raises(ValueError) as exc:
        validate_department("   ")
    assert str(exc.value) == "department is required and cannot be empty"


def test_validate_department_rejects_unknown_department():
    # P2-09 — arbitrary strings / near-miss values are rejected.
    for bogus in ("Totally Fake", "electrical", "Electric", "Maintenance", "HR"):
        with pytest.raises(ValueError) as exc:
            validate_department(bogus)
        assert str(exc.value).startswith("Invalid department ")
        assert str(VALID_DEPARTMENTS) in str(exc.value)


# ── Password policy (P2-08) ─────────────────────────────────────────────────────


def test_validate_password_accepts_policy_compliant():
    returned = validate_password("StrongPass1!")
    assert returned == "StrongPass1!"


@pytest.mark.parametrize(
    "password,expected_fragment",
    [
        ("Ab1!", "at least 8 characters"),
        ("ALLCAPS1!", "a lowercase letter"),
        ("alllower1!", "an uppercase letter"),
        ("NoDigitsHere!", "a digit"),
        ("NoSpecial1", "a special character"),
    ],
)
def test_validate_password_reports_each_missing_class(password, expected_fragment):
    with pytest.raises(ValueError) as exc:
        validate_password(password)
    assert expected_fragment in str(exc.value)


def test_validate_password_rejects_missing_everything():
    # Four spaces: too short and no uppercase, lowercase, digit, or special
    # character — every requirement must be reported.
    with pytest.raises(ValueError) as exc:
        validate_password("    ")
    message = str(exc.value)
    assert "at least 8 characters" in message
    assert "an uppercase letter" in message
    assert "a lowercase letter" in message
    assert "a digit" in message
    assert "a special character" in message


def test_validate_password_returns_value_for_validation_use():
    # Returns the (possibly whitespace-stripped) password so pydantic field
    # validators can assign it back.
    assert validate_password("Abcd1234!") == "Abcd1234!"


def test_build_profile_payload_supervisor_includes_department():
    payload = build_profile_payload(
        uid="u", email="electrical@campus.edu", role="supervisor", department="Electrical"
    )
    assert payload["role"] == "supervisor"
    assert payload["department"] == "Electrical"


def test_build_profile_payload_student_has_no_department_key():
    payload = build_profile_payload(uid="u", email="student@campus.edu")
    assert "department" not in payload


def test_build_profile_payload_rejects_blank_department():
    with pytest.raises(ValueError, match="department is required"):
        build_profile_payload(uid="u", email="electrical@campus.edu", department="   ")
