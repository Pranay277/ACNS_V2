"""
migrate_duplicate_fields.py — Backfill campusId + buildingId on existing issues.

Issues created before the campus-aware duplicate detection shipped store no
``campusId`` / ``buildingId``. This script stamps both:

  * ``campusId``   -> resolved from the reporter's profile (users/{userId}),
                      falling back to the default campus when absent.
  * ``buildingId`` -> the nearest landmark node id from the campus navigation
                      graph (campuses/{campusId}/nodes), computed from the
                      issue's stored lat/lng.

Idempotent: documents that already have both fields are left untouched.
Run from the backend directory:

    python migrate_duplicate_fields.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.firebase_admin import db  # noqa: F401  (initializes the SDK)
from services import users
from services.navigation import nearest_landmark
from config import DEFAULT_CAMPUS_ID


def main():
    issues_ref = db.collection("issues")
    migrated = 0
    skipped = 0
    for doc in issues_ref.stream():
        data = doc.to_dict()

        if data.get("campusId") and data.get("buildingId"):
            skipped += 1
            print(f"[skip] {doc.id:<28} already has campusId + buildingId")
            continue

        loc = data.get("location") or {}
        lat, lng = loc.get("lat"), loc.get("lng")

        profile = users.get_user_profile(data.get("userId"))
        campus_id = (profile or {}).get("campusId") or DEFAULT_CAMPUS_ID
        building_id = (
            nearest_landmark(campus_id, lat, lng)
            if lat is not None and lng is not None
            else None
        )

        updates = {}
        if not data.get("campusId"):
            updates["campusId"] = campus_id
        if not data.get("buildingId"):
            updates["buildingId"] = building_id

        if not updates:
            skipped += 1
            print(f"[skip] {doc.id:<28} nothing to write")
            continue

        doc.reference.update(updates)
        migrated += 1
        print(f"[mig] {doc.id:<28} campusId={campus_id} buildingId={building_id}")

    print(f"\nDone. migrated: {migrated}, skipped: {skipped}")


if __name__ == "__main__":
    main()
