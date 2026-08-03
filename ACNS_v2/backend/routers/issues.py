from fastapi import APIRouter, HTTPException
from models.schemas import IssueCreate, IssueStatusUpdate, VerifyIssue
from firebase_admin import firestore
from services.firebase_admin import db
from services.duplicate_check import resolve_campus_id, find_duplicate_issue
from services.navigation import nearest_landmark
from services.users import get_user_profile
from services import gamification, notify
from services.notify import create_notification
from config import (
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
from datetime import datetime

router = APIRouter()


def _priority_for_count(unique_reporters: int):
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
def _merge_issue_transaction(transaction, issue_ref, user_id):
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
    """
    snap = next(transaction.get(issue_ref), None)
    data = snap.to_dict() if snap is not None and snap.exists else None
    if not data:
        return {"found": False}

    reported_by = list(data.get("reportedBy") or [])
    if user_id in reported_by:
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
    priority = _priority_for_count(unique_count)
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


@router.post("/")
def create_issue(issue: IssueCreate):
    try:
        print("Incoming issue:", issue.category, issue.lat, issue.lng, issue.locationText)
        if issue.category not in CATEGORY_MAP:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Invalid category. Must be one of: {list(CATEGORY_MAP.keys())}",
                },
            )

        issues_ref = db.collection("issues")

        # Campus: validate the frontend-selected college, fall back to the
        # reporter's profile campus, then to the default.
        profile = get_user_profile(issue.userId)
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
            print(f"Duplicate detected → merging reports (campus={campus_id}, building={building_id}, distance={dup[2]:.1f}m)")
            doc_id, data, _dist = dup
            existing_ref = issues_ref.document(doc_id)
            result = _merge_issue_transaction(db.transaction(), existing_ref, issue.userId)

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

        assigned_to = CATEGORY_MAP.get(issue.category, "default@campus.edu")

        new_issue = {
            "userId": issue.userId,
            "category": issue.category,
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
            "reportedBy": [issue.userId],
            "createdAt": datetime.utcnow().isoformat(),
            "resolvedAt": None,
            "proofImageUrl": None,
            "supervisorName": None,
            "supervisorEmail": None,
            "supervisorPhoto": None,
            "supervisorDescription": None,
        }

        issue_ref = issues_ref.document()
        _create_issue_transaction(db.transaction(), issue_ref, new_issue)
        issue_id = issue_ref.id

        create_notification(
            user_id=issue.userId,
            title="Issue Reported",
            message=f"Your {issue.category} issue has been reported and assigned to {assigned_to}.",
            issue_id=issue_id,
        )

        notify.notify_issue_assigned(
            issue_id=issue_id,
            supervisor_email=assigned_to,
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"success": False, "message": str(e)}
        )


@router.get("/")
def get_issues(role: str, userId: str = None, email: str = None):
    try:
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
            if not userId:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "message": "userId required"},
                )
            docs = issues_ref.where("userId", "==", userId).stream()
        elif role == "supervisor":
            if not email:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "message": "email required for supervisor role",
                    },
                )
            docs = issues_ref.where("assignedTo", "==", email).stream()
        else:
            docs = issues_ref.stream()

        result = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            result.append(data)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"success": False, "message": str(e)}
        )


@router.get("/{id}")
def get_issue(id: str):
    """
    Fetch a single issue (for the Issue Details page).

    Returns the issue document enriched with display names for the campus and
    building (resolved from the ``campuses`` collection and its navigation
    graph), so the frontend never has to know internal ids. Best-effort
    enrichment — names fall back to ``None`` when the campus/building is
    unknown (legacy issues without ``campusId``/``buildingId``).
    """
    try:
        doc = db.collection("issues").document(id).get()
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"success": False, "message": str(e)}
        )


@router.put("/{id}/status")
def update_status(id: str, payload: IssueStatusUpdate):
    try:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Invalid status. Must be one of: {VALID_STATUSES}",
                },
            )

        issue_ref = db.collection("issues").document(id)
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
            issue_id=id,
        )

        if payload.status in ["In Progress", "Resolved"]:
            create_notification(
                user_id=assigned_to,
                title=f"Issue Update",
                message=f"Issue status changed to: {payload.status}",
                issue_id=id,
            )

        return {"success": True, "message": f"Status updated to {payload.status}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"success": False, "message": str(e)}
        )


@router.post("/{id}/verify")
def verify_issue(id: str, payload: VerifyIssue):
    try:
        issue_ref = db.collection("issues").document(id)
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
                issue_id=id,
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
                issue_id=id,
            )
            new_status = "In Progress"

        return {"success": True, "message": f"Issue {new_status}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"success": False, "message": str(e)}
        )
