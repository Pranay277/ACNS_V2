"""
migrate_preferred_language.py — Backfill preferredLanguage on existing profiles.

User profiles created before the SMS language feature never stored
``preferredLanguage``. This migration adds the default ("en") to every profile
that is missing it, so the SMS service can always resolve a supervisor's
language without special-casing legacy documents.

The script is idempotent: profiles that already have a value are left
untouched (no writes). Run from the backend directory:

    python migrations/migrate_preferred_language.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DEFAULT_PREFERRED_LANGUAGE
from core.firebase import db  # noqa: F401  (initializes the SDK)


def main():
    users_ref = db.collection("users")
    migrated = 0
    skipped = 0
    for doc in users_ref.stream():
        data = doc.to_dict() or {}
        current = data.get("preferredLanguage")
        if current:
            skipped += 1
            print(f"[skip] {doc.id:<35} preferredLanguage={current}")
            continue
        doc.reference.update({"preferredLanguage": DEFAULT_PREFERRED_LANGUAGE})
        migrated += 1
        print(f"[mig] {doc.id:<35} preferredLanguage={DEFAULT_PREFERRED_LANGUAGE}")

    print(f"\nDone. migrated: {migrated}, skipped: {skipped}")


if __name__ == "__main__":
    main()
