"""
tests/test_schemas.py — Request-model hardening tests (P2-10, P2-08).

* Every request model rejects unknown fields (``extra="forbid"``) with a 422-
  style ``extra_forbidden`` pydantic error so client typos and sneaked-in
  fields fail fast instead of being silently ignored.
* The supervisor password / reset-password schemas enforce the password policy
  (P2-08) at the schema boundary.

Pure pydantic tests — no Firebase or app import required.
"""

import pytest
from pydantic import ValidationError

from features.auth.schemas import LoginRequest, SignupRequest, UserUpdateRequest
from features.gamification.schemas import GamificationAward
from features.issues.schemas import IssueCreate, IssueStatusUpdate, VerifyIssue
from features.navigation.schemas import NavigationRequest
from features.supervisors.schemas import (
    ChangeEmailRequest,
    ResetPasswordRequest,
    SupervisorCreateRequest,
    SupervisorSelfUpdateRequest,
    SupervisorUpdateRequest,
)


SCHEMAS_WITH_EXTRA_FORBID = [
    (LoginRequest, {"idToken": "x", "sneaky": "field"}),
    (SignupRequest, {"idToken": "x", "displayName": "N", "extraRole": "admin"}),
    (UserUpdateRequest, {"role": "admin", "rootkit": True}),
    (GamificationAward, {"userId": "u", "reason": "report_issue", "hack": 1}),
    (IssueCreate, {"userId": "u", "category": "Water", "description": "d", "lat": 1.0,
                   "lng": 1.0, "locationText": "here", "evil": "x"}),
    (IssueStatusUpdate, {"status": "Resolved", "bonus": "x"}),
    (VerifyIssue, {"verified": True, "extra": "x"}),
    (NavigationRequest, {"campus_id": "c", "start_node": "a", "end_node": "b",
                         "adminOverride": True}),
    (SupervisorCreateRequest, {"email": "a@b.c", "displayName": "A",
                               "department": "Water", "isSuperuser": True}),
    (SupervisorUpdateRequest, {"displayName": "A", "role": "admin"}),
    (SupervisorSelfUpdateRequest, {"displayName": "A", "department": "Water"}),
    (ChangeEmailRequest, {"newEmail": "b@c.d", "alsoDelete": True}),
]


@pytest.mark.parametrize("schema_cls,kwargs", SCHEMAS_WITH_EXTRA_FORBID)
def test_request_schemas_reject_unknown_fields(schema_cls, kwargs):
    with pytest.raises(ValidationError) as exc:
        schema_cls(**kwargs)
    types = [error["type"] for error in exc.value.errors()]
    assert "extra_forbidden" in types


def test_required_fields_still_enforced():
    # Rejecting extras must not relax required-field checks.
    with pytest.raises(ValidationError):
        LoginRequest(**{})
    # A fully valid payload still builds.
    assert LoginRequest(idToken="x").idToken == "x"


# ── Password policy at the schema boundary (P2-08) ─────────────────────────────


@pytest.mark.parametrize(
    "weak",
    ["short1!", "NODIGITS1!", "alllower1!", "NoSpecial1", "NoDigitsHere!"],
)
def test_reset_password_schema_rejects_weak_passwords(weak):
    with pytest.raises(ValidationError) as exc:
        ResetPasswordRequest(newPassword=weak)
    assert any("Password must include" in (e.get("msg") or "") for e in exc.value.errors())


def test_reset_password_schema_accepts_policy_compliant():
    req = ResetPasswordRequest(newPassword="StrongPass1!")
    assert req.newPassword == "StrongPass1!"


def test_create_supervisor_schema_rejects_weak_explicit_password():
    with pytest.raises(ValidationError):
        SupervisorCreateRequest(
            email="a@b.c", displayName="A", department="Water", password="weak"
        )


def test_create_supervisor_schema_accepts_omitted_password():
    req = SupervisorCreateRequest(email="a@b.c", displayName="A", department="Water")
    assert req.password is None
