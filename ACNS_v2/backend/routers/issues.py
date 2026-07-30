from fastapi import APIRouter, HTTPException
from models.schemas import IssueCreate, IssueStatusUpdate, VerifyIssue
from firebase_admin import firestore
from services.firebase_admin import db
from services.duplicate_check import haversine
from datetime import datetime

router = APIRouter()

CATEGORY_MAP = {
    "Electrical": "electrical@campus.edu",
    "Water": "water@campus.edu",
    "Cleanliness": "clean@campus.edu",
    "Infrastructure": "infra@campus.edu",
    "Accessibility": "access@campus.edu",
    "Safety": "safety@campus.edu",
    "Transport": "transport@campus.edu",
    "Environment": "environment@campus.edu",
}

VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

STATUS_TRANSITIONS = {
    "Open": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed", "In Progress"],
    "Closed": [],
}


def create_notification(user_id: str, title: str, message: str, issue_id: str):
    notification = {
        "userId": user_id,
        "title": title,
        "message": message,
        "issueId": issue_id,
        "read": False,
        "createdAt": datetime.utcnow().isoformat(),
    }
    db.collection("notifications").add(notification)


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
        existing_issues = issues_ref.where("category", "==", issue.category).stream()

        for doc in existing_issues:
            data = doc.to_dict()
            if data.get("status") in ["Open", "In Progress"]:
                loc = data.get("location", {})
                if "lat" in loc and "lng" in loc:
                    dist = haversine(issue.lat, issue.lng, loc["lat"], loc["lng"])
                    print("Checking existing issue:", data.get("location"))
                    print("Distance:", dist)
                    if dist < 120 or issue.locationText.strip().lower() == loc.get("text", "").strip().lower():
                        print("Duplicate detected → merging reports")
                        existing_ref = issues_ref.document(doc.id)
                        
                        existing_ref.update({
                            "reportCount": firestore.Increment(1),
                            "reportedBy": firestore.ArrayUnion([issue.userId])
                        })
                        
                        updated_doc = existing_ref.get().to_dict()
                        count = updated_doc.get("reportCount", 1)

                        if count >= 10:
                            existing_ref.update({"priority": "Critical"})
                        elif count >= 5:
                            existing_ref.update({"priority": "High"})
                            
                        return {
                            "success": True,
                            "issueId": doc.id,
                            "assignedTo": data.get("assignedTo")
                        }

        assigned_to = CATEGORY_MAP.get(issue.category, "default@campus.edu")

        new_issue = {
            "userId": issue.userId,
            "category": issue.category,
            "description": issue.description,
            "imageUrl": issue.imageUrl,
            "location": {
                "lat": issue.lat,
                "lng": issue.lng,
                "text": issue.locationText,
            },
            "status": "Open",
            "assignedTo": assigned_to,
            "createdAt": datetime.utcnow().isoformat(),
            "resolvedAt": None,
            "proofImageUrl": None,
            "supervisorName": None,
            "supervisorEmail": None,
            "supervisorPhoto": None,
            "supervisorDescription": None,
        }

        doc_ref = issues_ref.add(new_issue)
        issue_id = doc_ref[1].id

        create_notification(
            user_id=issue.userId,
            title="Issue Reported",
            message=f"Your {issue.category} issue has been reported and assigned to {assigned_to}.",
            issue_id=issue_id,
        )

        create_notification(
            user_id=assigned_to,
            title="New Issue Assigned",
            message=f"New {issue.category} issue reported at {issue.locationText}",
            issue_id=issue_id,
        )

        return {"success": True, "issueId": issue_id, "assignedTo": assigned_to}

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
            issue_ref.update(
                {"status": "Closed", "resolvedAt": datetime.utcnow().isoformat()}
            )
            create_notification(
                user_id=user_id,
                title="Issue Closed",
                message="Your issue has been verified and closed.",
                issue_id=id,
            )
            new_status = "Closed"
        else:
            issue_ref.update({"status": "In Progress"})
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
