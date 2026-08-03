"""
tests/test_issues_service.py — Regression tests for the issues feature wiring.

Exercises the validation paths that raise before any Firestore access, so
these tests never touch the database. They guard that the business logic
moved out of the router still produces the exact same HTTP errors.
"""

import pytest
from fastapi import HTTPException

from features.issues.schemas import IssueCreate, IssueStatusUpdate, VerifyIssue
from features.issues.service import (
    create_issue,
    list_issues,
    priority_for_count,
    update_issue_status,
)


def test_priority_escalation_thresholds():
    assert priority_for_count(1) is None
    assert priority_for_count(4) is None
    assert priority_for_count(5) == "High"
    assert priority_for_count(9) == "High"
    assert priority_for_count(10) == "Critical"
    assert priority_for_count(11) == "Critical"


def test_create_issue_rejects_invalid_category():
    issue = IssueCreate(
        userId="user@campus.edu",
        category="UFO Sighting",
        description="test",
        lat=17.39,
        lng=78.47,
        locationText="somewhere",
    )
    with pytest.raises(HTTPException) as exc:
        create_issue(issue)
    assert exc.value.status_code == 400
    assert "Invalid category. Must be one of:" in exc.value.detail["message"]


def test_list_issues_rejects_invalid_role():
    with pytest.raises(HTTPException) as exc:
        list_issues("hacker")
    assert exc.value.status_code == 400
    assert exc.value.detail["message"] == (
        "Invalid role. Must be: user, supervisor, or admin"
    )


def test_list_issues_requires_user_id_for_user_role():
    with pytest.raises(HTTPException) as exc:
        list_issues("user")
    assert exc.value.status_code == 400
    assert exc.value.detail["message"] == "userId required"


def test_list_issues_requires_email_for_supervisor_role():
    with pytest.raises(HTTPException) as exc:
        list_issues("supervisor")
    assert exc.value.status_code == 400
    assert exc.value.detail["message"] == "userId or email required for supervisor role"


def test_update_status_rejects_invalid_status():
    with pytest.raises(HTTPException) as exc:
        update_issue_status("some-id", IssueStatusUpdate(status="Exploded"))
    assert exc.value.status_code == 400
    assert "Invalid status. Must be one of:" in exc.value.detail["message"]
