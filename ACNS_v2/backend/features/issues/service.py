"""
features/issues/service.py — Issue workflow business logic.

Responsibilities:
  1. Create issues (with campus/building resolution, duplicate detection and
     atomic point awards for genuinely new issues).
  2. Merge duplicate reports into existing issues (Rules 2 & 3) and escalate
     priority from the unique-reporter count.
  3. Role-based issue fetching.
  4. Status workflow (validated transitions) with in-app notifications.
  5. Admin verification (close / reopen) with atomic, idempotent awards.

The router stays thin; every Firestore mutation and cross-feature call (points,
notifications, navigation, profiles) lives here.
"""

import logging
from datetime import datetime

from fastapi import HTTPException
from firebase_admin import firestore

from core.config import (
    CATEGORY_MAP,
    DEFAULT_CAMPUS_ID,
    DUPLICATE_RADIUS_METERS,
    PRIORITY_CRITICAL_REPORTS,
    PRIORITY_HIGH_REPORTS,
    REWARD_CONFIRM_ISSUE,
    REWARD_REPORT_ISSUE,
    REWARD_VERIFIED_ISSUE,
    STATUS_TRANSITIONS,
    VALID_STATUSES,
)
from core.firebase import db
from features.gamification import service as gamification
from features.issues.duplicate_check import find_duplicate_issue, resolve_campus_id
from features.issues.schemas import IssueCreate, IssueStatusUpdate, VerifyIssue
from features.navigation.service import nearest_landmark
from features.notifications.service import create_notification, notify_issue_assigned
from features.profile.service import get_user_profile, resolve_uid
from features.sms.counters import increment_issue_counter
from features.supervisors.service import resolve_assigned_supervisor

logger = logging.getLogger(__name__)


def priority_for_count(unique_reporters: int):
    """Recalculate priority from the unique-reporter count (existing escalation)."""
    if unique_reporters >= PRIORITY_CRITICAL_REPORTS:
        return "Critical"
    if unique_reporters >= PRIORITY_HIGH_REPORTS:
        return "High"
    return None


@firestore.transactional
def _create_issue_transaction(transaction, issue_ref, new_issue):
    """
    Atomically create the issue AND award report points to its reporter.

    Points are only awarded when a genuinely new issue is created. The
    duplicate-merge path never reaches this function, so duplicate
    submissions can never award points a second time.
    """
    gamification.add_award_to_transaction(
        transaction,
        user_id=new_issue["userId"],
        points=gamification.points_for(REWARD_REPORT_ISSUE),
        reason=REWARD_REPORT_ISSUE,
        issue_id=issue_ref.id,
        issues_reported=1,
    )
    transaction.set(issue_ref, new_issue)


@firestore.transactional
def _verify_issue_transaction(transaction, issue_ref, update_data, user_id, award_verified):
    """
    Atomically apply the verification status change and, when the issue is
    verified (Closed), award verification points + resolved count. Awards are
    idempotent per issue, so re-verification can never double-grant points.
    """
    if award_verified:
        gamification.add_award_to_transaction(
            transaction,
            user_id=user_id,
            points=gamification.points_for(REWARD_VERIFIED_ISSUE),
            reason=REWARD_VERIFIED_ISSUE,
            issue_id=issue_ref.id,
            issues_resolved=1,
        )
    transaction.update(issue_ref, update_data)


@firestore.transactional
def _merge_issue_transaction(transaction, issue_ref, user_id, user_email=None):
    """
    Atomically merge a duplicate report into an existing issue (Rules 2 & 3).

    Rule 2 (this user has NEVER reported this issue):
      * do not create a new issue
      * increment reportCount by 1
      * record this user as a reporter
      * recalculate priority from the unique-reporter count
      * award 5 confirmation points (idempotent per ``confirm_issue:{issueId}``)

    Rule 3 (this user has ALREADY reported this issue):
      * perform no writes at all
      * report ``alreadyReported`` so the caller can return a clear response

    ``user_id`` is the UID primary identity; ``user_email`` is accepted for
    legacy ``reportedBy`` arrays that still store emails pre-migration.
    """
    snap = next(transaction.get(issue_ref), None)
    data = snap.to_dict() if snap is not None and snap.exists else None
    if not data:
        return {"found": False}

    reported_by = list(data.get("reportedBy") or [])
    already_reported = user_id in reported_by or (
        user_email is not None and user_email in reported_by
    )
    if already_reported:
        return {
            "found": True,
            "alreadyReported": True,
            "pointsAwarded": 0,
            "reportCount": data.get("reportCount", len(reported_by)),
        }

    # Pre-fetch the idempotency snapshot BEFORE any write: Firestore forbids
    # reads after writes within the same transaction.
    points = gamification.points_for(REWARD_CONFIRM_ISSUE)
    history_snap = gamification.pre_read_history(
        transaction, user_id, REWARD_CONFIRM_ISSUE, issue_ref.id
    )

    unique_count = len(reported_by) + 1
    updates = {
        "reportCount": unique_count,
        "reportedBy": firestore.ArrayUnion([user_id]),
    }
    priority = priority_for_count(unique_count)
    if priority:
        updates["priority"] = priority
    transaction.update(issue_ref, updates)

    gamification.add_award_to_transaction(
        transaction,
        user_id=user_id,
        points=points,
        reason=REWARD_CONFIRM_ISSUE,
        issue_id=issue_ref.id,
        issues_reported=1,
        history_snap=history_snap,
    )
    return {
        "found": True,
        "alreadyReported": False,
        "pointsAwarded": points,
        "reportCount": unique_count,
        "priority": priority,
    }


def _assignment_sms_sent(issue_id: str) -> bool:
    """
    Return True when the assignment SMS was already dispatched for the issue.

    Read from the issue document's persistent ``smsSent`` flag, so the
    one-SMS-per-issue guarantee survives server restarts.
    """
    doc = db.collection("issues").document(issue_id).get()
    if not doc.exists:
        return False
    return bool((doc.to_dict() or {}).get("smsSent"))


def _mark_assignment_sms_sent(issue_id: str) -> None:
    """Persist that the assignment SMS was dispatched for the issue."""
    db.collection("issues").document(issue_id).update(
        {"smsSent": True, "smsSentAt": datetime.utcnow().isoformat()}
    )


def _dispatch_assignment_sms_once(
    issue_id: str,
    supervisor_uid: str,
    category: str,
    location_text: str,
) -> bool:
    """
    Dispatch the assignment SMS at most once per issue.

    The persistent ``smsSent``/``smsSentAt`` flags live on the issue document,
    so duplicate reports can never trigger a second SMS and the guarantee
    survives server restarts. A new issue (a fresh document) always starts with
    ``smsSent=False`` and sends its own first SMS.

    Returns True when a dispatch was attempted, False when the SMS was already
    sent for this issue.
    """
    if _assignment_sms_sent(issue_id):
        logger.info("Assignment SMS already sent for issue %s; skipping.", issue_id)
        return False
    notify_issue_assigned(
        issue_id=issue_id,
        supervisor_uid=supervisor_uid,
        category=category,
        location_text=location_text,
    )
    _mark_assignment_sms_sent(issue_id)
    return True


def create_issue(issue: IssueCreate, reporter_uid: str, reporter_email: str = None) -> dict:
    if issue.category not in CATEGORY_MAP:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Invalid category. Must be one of: {list(CATEGORY_MAP.keys())}",
            },
        )

    issues_ref = db.collection("issues")

    # Reporter identity comes from the authenticated caller (CurrentUser), NEVER
    # from the request body. ``issue.userId`` is ignored entirely. The email is
    # kept only for matching pre-migration ``reportedBy`` arrays that store
    # emails instead of uids.
    reporter_email = (reporter_email or "").strip().lower() or None
    if reporter_email and "@" not in reporter_email:
        reporter_email = None

    # Campus: validate the frontend-selected college, fall back to the
    # reporter's profile campus, then to the default.
    profile = get_user_profile(reporter_uid)
    profile_campus = (profile or {}).get("campusId") or DEFAULT_CAMPUS_ID
    campus_id = resolve_campus_id(issue.college, profile_campus)

    # Building: nearest landmark node from the campus navigation graph
    # (the single source of truth — only the node id reference is stored).
    building_id = nearest_landmark(campus_id, issue.lat, issue.lng)

    dup = find_duplicate_issue(
        category=issue.category,
        campus_id=campus_id,
        building_id=building_id,
        lat=issue.lat,
        lng=issue.lng,
        radius_meters=DUPLICATE_RADIUS_METERS,
    )
    if dup is not None:
        logger.warning(
            "Duplicate detected → merging reports (campus=%s, building=%s, distance=%.1fm)",
            campus_id,
            building_id,
            dup[2],
        )
        doc_id, data, _dist = dup
        existing_ref = issues_ref.document(doc_id)
        result = _merge_issue_transaction(
            db.transaction(), existing_ref, reporter_uid, reporter_email
        )

        if result.get("alreadyReported"):
            return {
                "success": True,
                "issueId": doc_id,
                "assignedTo": data.get("assignedTo"),
                "merged": False,
                "alreadyReported": True,
                "pointsAwarded": 0,
                "reportCount": result.get("reportCount"),
                "message": "You have already reported this issue. No points were awarded.",
            }

        return {
            "success": True,
            "issueId": doc_id,
            "assignedTo": data.get("assignedTo"),
            "merged": True,
            "alreadyReported": False,
            "pointsAwarded": result.get("pointsAwarded", 0),
            "reportCount": result.get("reportCount"),
            "priority": result.get("priority"),
        }

    # Department-driven assignment (category -> department -> active supervisor),
    # falling back to the legacy CATEGORY_MAP for pre-department deployments.
    assigned_to = resolve_assigned_supervisor(issue.category)

    # P2-06: per-user daily cap on NEW issues created. Duplicate reports are
    # counted separately (they merge above) and never consume this budget.
    # The persisted counter fails open, so a counter outage can never block a
    # legitimate report.
    if not increment_issue_counter(reporter_uid):
        logger.warning(
            "Issue creation blocked by daily cap for user %s", reporter_uid
        )
        raise HTTPException(
            status_code=429,
            detail={
                "success": False,
                "message": "Daily issue limit reached. Please try again tomorrow.",
            },
        )

    new_issue = {
        "userId": reporter_uid,
        "category": issue.category,
        "subCategory": issue.subCategory,
        "description": issue.description,
        "imageUrl": issue.imageUrl,
        "campusId": campus_id,
        "buildingId": building_id,
        "location": {
            "lat": issue.lat,
            "lng": issue.lng,
            "text": issue.locationText,
        },
        "status": "Open",
        "assignedTo": assigned_to,
        "reportCount": 1,
        "reportedBy": [reporter_uid],
        "createdAt": datetime.utcnow().isoformat(),
        "resolvedAt": None,
        "proofImageUrl": None,
        "supervisorName": None,
        "supervisorEmail": None,
        "supervisorPhoto": None,
        "supervisorDescription": None,
        "smsSent": False,
        "smsSentAt": None,
    }

    issue_ref = issues_ref.document()
    _create_issue_transaction(db.transaction(), issue_ref, new_issue)
    issue_id = issue_ref.id

    create_notification(
        user_id=reporter_uid,
        title="Issue Reported",
        message=f"Your {issue.category} issue has been reported and assigned to {assigned_to}.",
        issue_id=issue_id,
    )

    _dispatch_assignment_sms_once(
        issue_id=issue_id,
        supervisor_uid=assigned_to,
        category=issue.category,
        location_text=issue.locationText,
    )

    return {
        "success": True,
        "issueId": issue_id,
        "assignedTo": assigned_to,
        "campusId": campus_id,
        "buildingId": building_id,
        "merged": False,
        "alreadyReported": False,
        "pointsAwarded": gamification.points_for(REWARD_REPORT_ISSUE),
        "reportCount": 1,
    }


def list_issues(role: str, user_id: str = None, email: str = None) -> list:
    if role not in ["user", "supervisor", "admin"]:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Invalid role. Must be: user, supervisor, or admin",
            },
        )

    issues_ref = db.collection("issues")

    if role == "user":
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail={"success": False, "message": "userId required"},
            )
        # UID-primary: resolve a legacy email to its uid so pre/post-migration
        # issues (which store uids) are both found.
        uid = resolve_uid(user_id) or user_id
        docs = issues_ref.where("userId", "==", uid).stream()
    elif role == "supervisor":
        identity = user_id or email
        if not identity:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "userId or email required for supervisor role",
                },
            )
        uid = resolve_uid(identity) or identity
        docs = issues_ref.where("assignedTo", "==", uid).stream()
    else:
        docs = issues_ref.stream()

    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)

    return result


def get_issue(issue_id: str) -> dict:
    """
    Fetch a single issue (for the Issue Details page).

    Returns the issue document enriched with display names for the campus and
    building (resolved from the ``campuses`` collection and its navigation
    graph), so the frontend never has to know internal ids. Best-effort
    enrichment — names fall back to ``None`` when the campus/building is
    unknown (legacy issues without ``campusId``/``buildingId``).
    """
    doc = db.collection("issues").document(issue_id).get()
    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Issue not found"},
        )

    data = doc.to_dict() or {}
    campus_id = data.get("campusId")
    building_id = data.get("buildingId")

    campus_name = None
    if campus_id:
        campus_doc = db.collection("campuses").document(campus_id).get()
        if campus_doc.exists:
            campus_name = campus_doc.to_dict().get("name")

    building_name = None
    if campus_id and building_id:
        node_doc = (
            db.collection("campuses")
            .document(campus_id)
            .collection("nodes")
            .document(building_id)
            .get()
        )
        if node_doc.exists:
            building_name = node_doc.to_dict().get("name")

    data["id"] = doc.id
    data["campusName"] = campus_name
    data["buildingName"] = building_name
    return {"success": True, "issue": data}


def update_issue_status(issue_id: str, payload: IssueStatusUpdate) -> dict:
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Invalid status. Must be one of: {VALID_STATUSES}",
            },
        )

    issue_ref = db.collection("issues").document(issue_id)
    doc = issue_ref.get()

    if not doc.exists:
        raise HTTPException(
            status_code=404, detail={"success": False, "message": "Issue not found"}
        )

    current_status = doc.to_dict().get("status")
    user_id = doc.to_dict().get("userId")
    assigned_to = doc.to_dict().get("assignedTo")

    if payload.status not in STATUS_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Invalid transition from '{current_status}' to '{payload.status}'. Allowed: {STATUS_TRANSITIONS.get(current_status, [])}",
            },
        )

    update_data = {"status": payload.status}

    if payload.status == "In Progress":
        if payload.supervisorName:
            update_data["supervisorName"] = payload.supervisorName
        if payload.supervisorEmail:
            update_data["supervisorEmail"] = payload.supervisorEmail
        if payload.supervisorPhoto:
            update_data["supervisorPhoto"] = payload.supervisorPhoto
        if payload.supervisorDescription:
            update_data["supervisorDescription"] = payload.supervisorDescription

    if payload.status == "Resolved":
        if not payload.proofImageUrl:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "proofImageUrl required for Resolved status",
                },
            )
        update_data["proofImageUrl"] = payload.proofImageUrl
        if payload.supervisorName:
            update_data["supervisorName"] = payload.supervisorName
        if payload.supervisorEmail:
            update_data["supervisorEmail"] = payload.supervisorEmail
        if payload.supervisorPhoto:
            update_data["supervisorPhoto"] = payload.supervisorPhoto
        if payload.supervisorDescription:
            update_data["supervisorDescription"] = payload.supervisorDescription

    if payload.status == "Closed":
        update_data["resolvedAt"] = datetime.utcnow().isoformat()
        if payload.supervisorName:
            update_data["supervisorName"] = payload.supervisorName
        if payload.supervisorEmail:
            update_data["supervisorEmail"] = payload.supervisorEmail
        if payload.supervisorPhoto:
            update_data["supervisorPhoto"] = payload.supervisorPhoto
        if payload.supervisorDescription:
            update_data["supervisorDescription"] = payload.supervisorDescription

    issue_ref.update(update_data)

    create_notification(
        user_id=user_id,
        title=f"Issue {payload.status}",
        message=f"Your issue status has been updated to: {payload.status}",
        issue_id=issue_id,
    )

    if payload.status in ["In Progress", "Resolved"]:
        create_notification(
            user_id=assigned_to,
            title=f"Issue Update",
            message=f"Issue status changed to: {payload.status}",
            issue_id=issue_id,
        )

    return {"success": True, "message": f"Status updated to {payload.status}"}


def verify_issue(issue_id: str, payload: VerifyIssue) -> dict:
    issue_ref = db.collection("issues").document(issue_id)
    doc = issue_ref.get()

    if not doc.exists:
        raise HTTPException(
            status_code=404, detail={"success": False, "message": "Issue not found"}
        )

    current_status = doc.to_dict().get("status")
    user_id = doc.to_dict().get("userId")

    if current_status != "Resolved":
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Can only verify issues with 'Resolved' status. Current: '{current_status}'",
            },
        )

    if payload.verified:
        _verify_issue_transaction(
            db.transaction(),
            issue_ref,
            {"status": "Closed", "resolvedAt": datetime.utcnow().isoformat()},
            user_id,
            True,
        )
        create_notification(
            user_id=user_id,
            title="Issue Closed",
            message="Your issue has been verified and closed.",
            issue_id=issue_id,
        )
        new_status = "Closed"
    else:
        _verify_issue_transaction(
            db.transaction(),
            issue_ref,
            {"status": "In Progress"},
            user_id,
            False,
        )
        create_notification(
            user_id=user_id,
            title="Issue Reopened",
            message="Your issue has been reopened. Please check with the supervisor.",
            issue_id=issue_id,
        )
        new_status = "In Progress"

    return {"success": True, "message": f"Issue {new_status}"}
