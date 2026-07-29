from fastapi import APIRouter
from services.firebase_admin import db

router = APIRouter()

@router.get("/{userId}")
def get_notifications(userId: str):
    docs = db.collection("notifications").where("userId", "==", userId).stream()

    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)

    return result