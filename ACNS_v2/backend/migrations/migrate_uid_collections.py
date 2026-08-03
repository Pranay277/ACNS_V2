"""
migrate_uid_collections.py — Migrate identity from email to Firebase UID.

The application now treats the Firebase Authentication UID as the PRIMARY,
immutable identity and splits profiles into role-scoped collections keyed by
uid:

    users/{email}      ──▶   students/{uid} | supervisors/{uid} | admins/{uid}

This migration performs the one-time move:

  1. Copies each ``users/{email}`` profile into the collection of its role,
     keyed by uid (preserving every field).
  2. Rewrites email-keyed REFERENCES to uids:
       issues.userId / issues.assignedTo / issues.reportedBy[]
       notifications.userId
       gamification_users/{email} -> gamification_users/{uid} (+ subcollections)
  3. Verifies counts and uid uniqueness, and writes a JSON manifest.

Safety guarantees:

  * DRY-RUN by default — pass ``--apply`` to write anything.
  * Idempotent + resumable: destination documents are checked before writing;
    re-running completes the remaining work without creating duplicates.
  * The legacy ``users/`` collection is NEVER deleted (marked ``_migratedTo``)
    so a rollback is always possible during the rollout window.
  * Documents whose uid/email do not match Firebase Auth are reported and
    SKIPPED unless ``--force`` is passed.

Run from the backend directory:

    python migrations/migrate_uid_collections.py                  # dry-run
    python migrations/migrate_uid_collections.py --apply          # real run
    python migrations/migrate_uid_collections.py --manifest x.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_admin import auth as admin_auth  # noqa: E402

from core.config import (  # noqa: E402
    ADMINS_COLLECTION,
    GAMIFICATION_COLLECTION,
    ROLE_COLLECTIONS,
    STUDENTS_COLLECTION,
    SUPERVISORS_COLLECTION,
    USERS_COLLECTION,
)
from core.firebase import db  # noqa: E402  (initializes the SDK)

DEFAULT_MANIFEST = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "migrate_uid_manifest.json"
)

ROLE_BY_COLLECTION = {
    STUDENTS_COLLECTION: "user",
    SUPERVISORS_COLLECTION: "supervisor",
    ADMINS_COLLECTION: "admin",
}


def _auth_maps():
    email_to_uid = {}
    uid_to_email = {}
    for record in admin_auth.list_users().iterate_all():
        email = (record.email or "").strip().lower()
        email_to_uid[email] = record.uid
        uid_to_email[record.uid] = email
    return email_to_uid, uid_to_email


def _looks_like_email(value):
    return bool(value) and "@" in str(value)


def _map_value(value, email_to_uid):
    """Map an email reference to its uid; leave uids/unknowns untouched."""
    if _looks_like_email(value):
        return email_to_uid.get(str(value).strip().lower(), value)
    return value


def _map_array(values, email_to_uid):
    return [_map_value(v, email_to_uid) for v in (values or [])]


# ── Phase 1: profile analysis ─────────────────────────────────────────────────


def analyze_profiles(email_to_uid, uid_to_email):
    """Classify every legacy users/{email} doc for migration."""
    profiles = []
    stats = {"valid": 0, "skip_existing": 0, "bad_role": 0,
             "missing_uid": 0, "orphan_uid": 0, "email_mismatch": 0}
    dest_collections = list(ROLE_COLLECTIONS.values())

    for doc in db.collection(USERS_COLLECTION).stream():
        data = doc.to_dict() or {}
        role = data.get("role")
        email = (data.get("email") or "").strip().lower()
        uid = data.get("uid")
        entry = {
            "source": f"{USERS_COLLECTION}/{doc.id}",
            "docId": doc.id,
            "role": role,
            "email": email,
            "uid": uid,
            "status": "valid",
            "detail": "",
        }

        if role not in ROLE_COLLECTIONS:
            entry["status"] = "bad_role"
            stats["bad_role"] += 1
            profiles.append(entry)
            continue

        if not uid:
            entry["status"] = "missing_uid"
            stats["missing_uid"] += 1
            profiles.append(entry)
            continue

        if uid not in uid_to_email:
            entry["status"] = "orphan_uid"
            stats["orphan_uid"] += 1
            profiles.append(entry)
            continue

        if email and uid_to_email[uid] != email:
            entry["status"] = "email_mismatch"
            entry["detail"] = f"auth email is {uid_to_email[uid]}"
            stats["email_mismatch"] += 1
            profiles.append(entry)
            continue

        dest = ROLE_COLLECTIONS[role]
        # uid already present in ANOTHER role collection = identity collision.
        collision = [
            c for c in dest_collections
            if c != dest and db.collection(c).document(uid).get().exists
        ]
        if collision:
            entry["status"] = "collision"
            entry["detail"] = f"uid exists in {collision}"
            stats["skip_existing"] += 1
            profiles.append(entry)
            continue

        if db.collection(dest).document(uid).get().exists:
            entry["status"] = "skip_existing"
            entry["detail"] = f"already in {dest}/{uid}"
            stats["skip_existing"] += 1
            profiles.append(entry)
            continue

        entry["destination"] = f"{dest}/{uid}"
        stats["valid"] += 1
        profiles.append(entry)

    return profiles, stats


# ── Phase 2: reference analysis ───────────────────────────────────────────────


def analyze_references(email_to_uid):
    plan = {
        "issues": {"updated": 0, "skipped": 0},
        "notifications": {"updated": 0, "skipped": 0},
        "gamification": {"moved": 0, "skip_existing": 0, "unresolved": 0},
    }
    issue_ids = []
    for doc in db.collection("issues").stream():
        data = doc.to_dict() or {}
        changed = _looks_like_email(data.get("userId")) and _map_value(data.get("userId"), email_to_uid) != data.get("userId")
        changed = changed or (_looks_like_email(data.get("assignedTo")) and _map_value(data.get("assignedTo"), email_to_uid) != data.get("assignedTo"))
        for v in (data.get("reportedBy") or []):
            if _looks_like_email(v):
                changed = True
                break
        if changed:
            issue_ids.append(doc.id)
    plan["issues"]["updated"] = len(issue_ids)

    for doc in db.collection("notifications").stream():
        data = doc.to_dict() or {}
        if _looks_like_email(data.get("userId")):
            plan["notifications"]["updated"] += 1

    for doc in db.collection(GAMIFICATION_COLLECTION).stream():
        if not _looks_like_email(doc.id):
            continue
        uid = email_to_uid.get(doc.id.strip().lower())
        if not uid:
            plan["gamification"]["unresolved"] += 1
            continue
        if db.collection(GAMIFICATION_COLLECTION).document(uid).get().exists:
            plan["gamification"]["skip_existing"] += 1
        else:
            plan["gamification"]["moved"] += 1

    return plan, issue_ids


# ── Phase 3: apply ────────────────────────────────────────────────────────────


def _commit(batch, operations):
    """Flush a Firestore batch when it reaches the operation limit."""
    if operations >= 350:
        batch.commit()
        return db.batch(), 0
    return batch, operations


def apply_profiles(profiles, force):
    migrated, skipped, marked = 0, 0, 0
    batch = db.batch()
    ops = 0
    for entry in profiles:
        if entry["status"] != "valid":
            skipped += 1
            continue
        if entry["status"] == "email_mismatch" and not force:
            skipped += 1
            continue

        source_ref = db.document(entry["source"])
        data = source_ref.get().to_dict() or {}
        dest_path = entry["destination"]  # {collection}/{uid}
        dest_ref = db.document(dest_path)

        if dest_ref.get().exists:
            skipped += 1
            continue

        batch.set(dest_ref, data)
        ops += 1
        batch, ops = _commit(batch, ops)

        now = datetime.now(timezone.utc).isoformat()
        batch.update(source_ref, {"_migratedTo": dest_path, "_migratedAt": now})
        ops += 1
        batch, ops = _commit(batch, ops)

        migrated += 1
        print(f"[mig] {entry['source']:<32} -> {dest_path}")
    batch.commit()
    return migrated, skipped


def apply_references(email_to_uid, issue_ids):
    # issues
    updated = 0
    batch = db.batch()
    ops = 0
    for issue_id in issue_ids:
        ref = db.collection("issues").document(issue_id)
        data = ref.get().to_dict() or {}
        updates = {}
        if _looks_like_email(data.get("userId")):
            updates["userId"] = _map_value(data["userId"], email_to_uid)
        if _looks_like_email(data.get("assignedTo")):
            updates["assignedTo"] = _map_value(data["assignedTo"], email_to_uid)
        mapped_reported_by = _map_array(data.get("reportedBy"), email_to_uid)
        if mapped_reported_by != (data.get("reportedBy") or []):
            updates["reportedBy"] = mapped_reported_by
        if updates:
            batch.update(ref, updates)
            ops += 1
            batch, ops = _commit(batch, ops)
            updated += 1
            print(f"[ref] issue {issue_id}: {list(updates.keys())}")
    batch.commit()

    # notifications
    notified = 0
    batch = db.batch()
    ops = 0
    for doc in db.collection("notifications").stream():
        uid = doc.to_dict() or {}
        if _looks_like_email(uid.get("userId")):
            mapped = _map_value(uid["userId"], email_to_uid)
            if mapped != uid["userId"]:
                batch.update(doc.reference, {"userId": mapped})
                ops += 1
                batch, ops = _commit(batch, ops)
                notified += 1
    batch.commit()

    # gamification_users/{email} -> {uid}
    moved, skip_existing, unresolved = 0, 0, 0
    batch = db.batch()
    ops = 0
    for doc in db.collection(GAMIFICATION_COLLECTION).stream():
        if not _looks_like_email(doc.id):
            continue
        uid = email_to_uid.get(doc.id.strip().lower())
        if not uid:
            unresolved += 1
            continue
        dest_ref = db.collection(GAMIFICATION_COLLECTION).document(uid)
        if dest_ref.get().exists:
            skip_existing += 1
            continue
        data = doc.to_dict() or {}
        data["userId"] = uid
        batch.set(dest_ref, data)
        ops += 1
        _copy_subcollections(batch, doc.reference, dest_ref)
        ops += 1
        now = datetime.now(timezone.utc).isoformat()
        batch.update(doc.reference, {"_migratedTo": f"{GAMIFICATION_COLLECTION}/{uid}", "_migratedAt": now})
        ops += 1
        batch, ops = _commit(batch, ops)
        moved += 1
        print(f"[mig] gamification/{doc.id} -> gamification/{uid}")
    batch.commit()
    return {"issues": updated, "notifications": notified,
            "gamification": {"moved": moved, "skip_existing": skip_existing,
                             "unresolved": unresolved}}


def _copy_subcollections(batch, src_ref, dst_ref):
    for sub in src_ref.collections():
        sub_dst = dst_ref.collection(sub.id)
        for subdoc in sub.stream():
            batch.set(sub_dst.document(subdoc.id), subdoc.to_dict() or {})


# ── Phase 4: verification ─────────────────────────────────────────────────────


def verify_counts(profiles, apply):
    counts = {}
    for collection in ROLE_COLLECTIONS.values():
        counts[collection] = len(list(db.collection(collection).stream()))

    expected = {}
    for entry in profiles:
        if entry["status"] == "valid":
            role = entry["role"]
            expected[ROLE_COLLECTIONS[role]] = expected.get(ROLE_COLLECTIONS[role], 0) + 1
        elif entry["status"] in ("skip_existing", "collision"):
            role = entry["role"]
            expected[ROLE_COLLECTIONS[role]] = expected.get(ROLE_COLLECTIONS[role], 0) + 1

    ok = True
    for collection in ROLE_COLLECTIONS.values():
        exp = expected.get(collection, 0)
        got = counts[collection]
        match = "OK" if (not apply or got >= exp) else "MISMATCH"
        if match != "OK":
            ok = False
        print(f"  {collection:<14} expected>={exp:<3} present={got:<3} {match}")

    # uid uniqueness across role collections (no identity collision)
    seen = {}
    collisions = []
    for collection in ROLE_COLLECTIONS.values():
        for doc in db.collection(collection).stream():
            if doc.id in seen:
                collisions.append((doc.id, seen[doc.id], collection))
            else:
                seen[doc.id] = collection
    if collisions:
        ok = False
        print("  COLLISION: uid present in multiple role collections:")
        for uid, c1, c2 in collisions:
            print(f"    {uid}: {c1} + {c2}")
    else:
        print("  uid uniqueness: OK (no uid in more than one role collection)")
    return ok


# ── entrypoint ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Migrate users/{email} -> role collections/{uid}")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    parser.add_argument("--force", action="store_true", help="Migrate docs whose email does not match Firebase Auth")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path for the JSON manifest")
    args = parser.parse_args()

    print("Loading Firebase Auth identity map...")
    email_to_uid, uid_to_email = _auth_maps()
    print(f"  auth users: {len(email_to_uid)}")

    print("\nAnalyzing legacy users/ profiles...")
    profiles, stats = analyze_profiles(email_to_uid, uid_to_email)
    for status, count in stats.items():
        print(f"  {status}: {count}")
    for entry in profiles:
        if entry["status"] != "valid":
            print(f"  [{entry['status']}] {entry['source']} {entry['detail']}")

    print("\nAnalyzing references...")
    plan, issue_ids = analyze_references(email_to_uid)
    print(f"  issues to rewrite: {plan['issues']['updated']}")
    print(f"  notifications to rewrite: {plan['notifications']['updated']}")
    print(f"  gamification to move: {plan['gamification']['moved']} "
          f"(skip_existing={plan['gamification']['skip_existing']}, "
          f"unresolved={plan['gamification']['unresolved']})")

    if not args.apply:
        print("\n── DRY RUN (no writes). Re-run with --apply to migrate. ──")
        manifest = {
            "mode": "dry-run",
            "auth_users": len(email_to_uid),
            "profiles": stats,
            "profile_entries": profiles,
            "references": plan,
            "issues_to_rewrite": issue_ids,
            "email_to_uid": email_to_uid,
        }
        with open(args.manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, default=str)
        print(f"  manifest written to {args.manifest}")
        verify_counts(profiles, apply=False)
        return

    print("\nApplying migration...")
    migrated, skipped = apply_profiles(profiles, force=args.force)
    print(f"  profiles migrated: {migrated}, skipped: {skipped}")

    ref_results = apply_references(email_to_uid, issue_ids)
    print(f"  issues rewritten: {ref_results['issues']}")
    print(f"  notifications rewritten: {ref_results['notifications']}")
    print(f"  gamification: {ref_results['gamification']}")

    print("\nVerification:")
    ok = verify_counts(profiles, apply=True)

    manifest = {
        "mode": "apply",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "auth_users": len(email_to_uid),
        "profiles": stats,
        "profile_entries": profiles,
        "migrated_profiles": migrated,
        "skipped_profiles": skipped,
        "references": ref_results,
        "issues_to_rewrite": issue_ids,
        "email_to_uid": email_to_uid,
        "verified": ok,
    }
    with open(args.manifest, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)
    print(f"\nManifest written to {args.manifest}")
    print("LEGACY users/ collection kept intact for rollback (marked _migratedTo).")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
