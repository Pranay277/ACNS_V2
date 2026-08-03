"""
features/notifications/service.py — Notification orchestrator.

Keeps the existing in-app notification workflow unchanged (a Firestore
``notifications`` document per recipient) and, on top of it, dispatches an SMS
to the assigned supervisor whenever a new issue is created.

The SMS body is enriched with the issue's campus, department, category,
building, exact location, priority, description, the uploaded image URL (when
present) and a clickable link to the frontend Issue Details page. The frontend
origin is config-driven (``FRONTEND_BASE_URL``) and the full link becomes
``{FRONTEND_BASE_URL}/issues/{campus_id}/{issue_id}`` — never hardcoded.

Localization is fully delegated to dedicated template modules
(``features/sms/templates/``): the supervisor's ``preferredLanguage`` is read
from the ``users`` profile, the matching template is loaded, and the body is
generated.
Missing or unsupported languages automatically fall back to English. This file
contains no language-specific strings.

Recipient resolution is campus-aware and never hardcodes a phone number: the
assigned supervisor uid (resolved from the issue's department/category) is
looked up in the ``supervisors/{uid}`` collection and the SMS is sent to that
profile's ``phoneNumber`` using its ``preferredLanguage``. A missing profile or
a missing phone number only logs a warning — the issue reporting flow continues
normally.
"""

import logging
from datetime import datetime

from core.config import DEFAULT_CAMPUS_ID, DEFAULT_PREFERRED_LANGUAGE, FRONTEND_BASE_URL
from core.firebase import db
from features.profile.service import get_user_profile, resolve_uid
from features.sms import service as sms_service

logger = logging.getLogger(__name__)


def create_notification(user_id: str, title: str, message: str, issue_id: str) -> dict:
    """
    Write an in-app notification document (existing behavior, unchanged).
    """
    notification = {
        "userId": user_id,
        "title": title,
        "message": message,
        "issueId": issue_id,
        "read": False,
        "createdAt": datetime.utcnow().isoformat(),
    }
    db.collection("notifications").add(notification)
    return notification


def get_user_notifications(user_id: str) -> list:
    """Return the in-app notifications for a user (uid primary, email accepted)."""
    candidates = [user_id]
    uid = resolve_uid(user_id)
    if uid and uid != user_id:
        candidates.append(uid)
    docs = db.collection("notifications").where("userId", "in", candidates).stream()

    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)

    return result


def notify_issue_assigned(
    issue_id: str,
    supervisor_uid: str,
    category: str,
    location_text: str,
) -> None:
    """
    Fire the full notification workflow for a newly assigned issue.

    1. In-app Firestore notification for the supervisor (existing behavior).
    2. Best-effort SMS to the supervisor's phone number.

    SMS dispatch is additive — an SMS failure or a missing phone number never
    affects the in-app notification or the issue creation result.
    """
    create_notification(
        user_id=supervisor_uid,
        title="New Issue Assigned",
        message=f"New {category} issue reported at {location_text}",
        issue_id=issue_id,
    )

    _dispatch_assignment_sms(issue_id, supervisor_uid, category)


def _phone_from_profile(supervisor_uid: str, profile) -> str | None:
    """
    Resolve the supervisor's SMS number from their profile.

    Returns the normalized phone number or ``None`` (with a logged warning)
    when the profile is missing or has no phone number. A non-string value
    (e.g. an int stored by an older client) is coerced to a string so an SMS
    dispatch can never fail issue creation.
    """
    if not profile:
        logger.warning(
            "No user profile found for supervisor '%s'; SMS skipped.", supervisor_uid
        )
        return None
    phone = profile.get("phoneNumber")
    if phone is None:
        logger.warning(
            "Supervisor '%s' has no phoneNumber on file; SMS skipped.", supervisor_uid
        )
        return None
    if not isinstance(phone, str):
        logger.warning(
            "Supervisor '%s' phoneNumber is not a string (%s); coercing to string.",
            supervisor_uid, type(phone).__name__,
        )
        phone = str(phone)
    phone = phone.strip()
    if not phone:
        logger.warning(
            "Supervisor '%s' has an empty phoneNumber on file; SMS skipped.",
            supervisor_uid,
        )
        return None
    return phone


def _issue_priority(issue_data: dict) -> str:
    """
    Read the issue's current priority for the SMS body.

    Returns the priority value (e.g. ``High``/``Critical``) or ``Normal`` when
    the issue has no priority yet.
    """
    priority = (issue_data.get("priority") or "").strip()
    return priority or "Normal"


def _issue_doc(issue_id: str) -> dict:
    """
    Best-effort read of an issue document. Returns the raw document data, or
    ``{}`` (with a logged warning) on any read failure — the SMS body must
    never break the issue creation workflow.
    """
    try:
        doc = db.collection("issues").document(issue_id).get()
        if doc.exists:
            return doc.to_dict() or {}
    except Exception as exc:  # noqa: BLE001 — SMS body must never break the workflow
        logger.warning("Could not read issue %s: %s", issue_id, exc)
    return {}


def _campus_display_name(campus_id) -> str | None:
    """
    Resolve the campus display name from the ``campuses`` collection (e.g.
    ``methodist`` -> "Methodist College of Engineering & Technology"). Returns
    ``None`` when the campus id is missing/unknown — callers fall back to the
    raw id. Best-effort; any failure only logs a warning.
    """
    if not campus_id:
        return None
    try:
        doc = db.collection("campuses").document(campus_id).get()
        if doc.exists:
            name = (doc.to_dict().get("name") or "").strip()
            if name:
                return name
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read campus '%s': %s", campus_id, exc)
    return None


def _building_display_name(campus_id, building_id) -> str | None:
    """
    Resolve the building/landmark display name from the campus navigation
    graph node (e.g. ``e-block`` -> "E Block"). Returns ``None`` when the
    building id is missing/unknown. Best-effort; any failure only logs a
    warning.
    """
    if not campus_id or not building_id:
        return None
    try:
        doc = (
            db.collection("campuses")
            .document(campus_id)
            .collection("nodes")
            .document(building_id)
            .get()
        )
        if doc.exists:
            name = (doc.to_dict().get("name") or "").strip()
            if name:
                return name
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read building '%s/%s': %s", campus_id, building_id, exc)
    return None


def _issue_context(issue_id: str, category: str, issue_data: dict) -> dict:
    """
    Resolve a plain-language issue context for the SMS templates.

    Gathers display names (campus, building) from Firestore lookups, the exact
    location text, priority, description, the uploaded image URL (only when
    present) and the config-driven Issue Details URL
    (``{FRONTEND_BASE_URL}/issues/{campus_id}/{issue_id}``). No hardcoded URLs
    and no language-specific strings live here — those belong to the templates.
    """
    campus_id = issue_data.get("campusId")
    campus_name = _campus_display_name(campus_id)
    building_name = _building_display_name(campus_id, issue_data.get("buildingId"))
    location = (issue_data.get("location") or {})
    location_text = (location.get("text") or issue_data.get("locationText") or "").strip()
    # Legacy issues may lack campusId; the frontend route needs a campus, so
    # fall back to the configured default campus for the link only.
    url_campus_id = campus_id or DEFAULT_CAMPUS_ID

    return {
        "campus": campus_name or campus_id or "Unknown",
        "department": category,
        "category": category,
        "building": building_name or issue_data.get("buildingId") or "Unknown",
        "location": location_text or "Unknown",
        "priority": _issue_priority(issue_data),
        "description": (issue_data.get("description") or "").strip() or "—",
        "image_url": (issue_data.get("imageUrl") or "").strip() or None,
        "issue_url": f"{FRONTEND_BASE_URL}/issues/{url_campus_id}/{issue_id}",
        "issue_id": issue_id,
    }


def _dispatch_assignment_sms(
    issue_id: str,
    supervisor_uid: str,
    category: str,
) -> None:
    profile = get_user_profile(supervisor_uid)
    phone = _phone_from_profile(supervisor_uid, profile)
    if not phone:
        return

    # Preferred language comes from the supervisor's profile. Missing or
    # unsupported values fall back to English via the template registry.
    language = (profile or {}).get("preferredLanguage") or DEFAULT_PREFERRED_LANGUAGE

    issue_data = _issue_doc(issue_id)
    issue = _issue_context(issue_id, category, issue_data)
    sms_service.send_issue_assigned_sms(phone, issue, language)
