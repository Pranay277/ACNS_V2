"""
migrate_issues.py — One-time backfill for issues created before the
gamification-rule update.

Older issue documents never stored ``reportCount`` / ``reportedBy`` at
creation, and ``priority`` was only set when a report-count threshold was
crossed. To make the new rules (unique-reporter tracking, priority from unique
reporters) apply correctly to historical issues, we backfill:

  * ``reportedBy``  -> the original creator counts as the first reporter
  * ``reportCount`` -> number of unique reporters (len of reportedBy)
  * ``priority``    -> recomputed from the unique-reporter count

The script is idempotent: documents that already satisfy the invariant are
left untouched (no writes). Run from the backend directory:

    python migrate_issues.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.firebase_admin import db  # noqa: F401  (initializes the SDK)


def priority_for_count(count):
    if count >= 10:
        return "Critical"
    if count >= 5:
        return "High"
    return None


def main():
    issues_ref = db.collection("issues")
    migrated = 0
    skipped = 0
    for doc in issues_ref.stream():
        data = doc.to_dict()

        reported_by = list(data.get("reportedBy") or [])
        creator = data.get("userId")
        if creator and creator not in reported_by:
            reported_by = [creator] + reported_by

        unique_count = len(reported_by)
        expected_priority = priority_for_count(unique_count)
        current_priority = data.get("priority")

        updates = {}
        if set(reported_by) != set(data.get("reportedBy") or []):
            updates["reportedBy"] = reported_by
        if data.get("reportCount") != unique_count:
            updates["reportCount"] = unique_count
        if expected_priority and current_priority != expected_priority:
            updates["priority"] = expected_priority

        if not updates:
            skipped += 1
            print(f"[skip] {doc.id:<28} already consistent (reporters={unique_count})")
            continue

        doc.reference.update(updates)
        migrated += 1
        print(
            f"[mig] {doc.id:<28} reportCount={unique_count} "
            f"reporters={len(reported_by)} priority={expected_priority}"
        )

    print(f"\nDone. migrated: {migrated}, skipped: {skipped}")


if __name__ == "__main__":
    main()
