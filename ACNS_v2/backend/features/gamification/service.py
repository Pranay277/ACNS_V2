"""
features/gamification/service.py — Gamification business logic.

Responsibilities:
  1. Award points and update user statistics (atomically).
  2. Maintain an append-only points history used for idempotency and audit.
  3. Fetch user profiles and calculate ranks efficiently.
  4. Fetch the leaderboard efficiently.
  5. Leave room for future reward types (badges, achievements, levels,
     daily streaks, event rewards) without further refactoring — all of
     these can be added as new fields on the user document.

Routers stay thin: every Firestore mutation lives in this module.
"""

import logging
from datetime import datetime, timezone

from firebase_admin import firestore

from core.config import (
    GAMIFICATION_COLLECTION,
    GAMIFICATION_HISTORY_SUBCOLLECTION,
    LEADERBOARD_DEFAULT_LIMIT,
    POINTS_BY_REWARD,
)
from core.firebase import db
from features.profile.service import resolve_uid

logger = logging.getLogger(__name__)


def points_for(reason: str) -> int:
    """Resolve the configured point value for a reward reason (0 if unknown)."""
    return POINTS_BY_REWARD.get(reason, 0)


def _collection():
    return db.collection(GAMIFICATION_COLLECTION)


def _normalize_id(user_id: str) -> str:
    """
    Normalize an email or uid to the UID-keyed gamification doc id.

    Emails (legacy callers) are resolved through Firebase Auth to their uid;
    uids are used as-is (no auth round-trip on the hot path).
    """
    if user_id and "@" in str(user_id):
        return resolve_uid(user_id) or str(user_id)
    return str(user_id or "")


def _profile_ref(user_id: str):
    return _collection().document(_normalize_id(user_id))


def _history_ref(user_id: str, event_key: str):
    return _profile_ref(user_id).collection(GAMIFICATION_HISTORY_SUBCOLLECTION).document(event_key)


def _event_key(reason: str, issue_id: str):
    """Deterministic, unique key per reward event → makes awards idempotent."""
    return f"{reason}:{issue_id}" if issue_id else None


def pre_read_history(transaction, user_id: str, reason: str, issue_id: str):
    """
    Pre-fetch the idempotency history snapshot inside an open transaction.

    Firestore forbids reads *after* a write within the same transaction, so a
    caller that must award points atomically with another write (e.g. merging
    a duplicate report into an issue) should call this BEFORE its own write
    and pass the returned snapshot to :func:`add_award_to_transaction`.
    """
    key = _event_key(reason, issue_id)
    if key is None:
        return None
    return next(transaction.get(_history_ref(user_id, key)), None)


def add_award_to_transaction(
    transaction,
    user_id: str,
    points: int,
    reason: str,
    issue_id: str = None,
    display_name: str = None,
    issues_reported: int = 0,
    issues_resolved: int = 0,
    history_snap=None,
) -> bool:
    """
    Stage an award inside an already-open Firestore transaction.

    Idempotent: when ``issue_id`` is provided, the award is recorded in the
    user's points history under a deterministic event key. If that event was
    already granted, nothing is written and ``False`` is returned — this is
    what prevents duplicate submissions from awarding points twice.

    ``history_snap`` may be a snapshot previously returned by
    :func:`pre_read_history`. Pass it when the caller has already written
    inside this transaction (Firestore forbids read-after-write), so the
    idempotency check reuses the pre-fetched snapshot instead of re-reading.

    Use this when the caller needs the award to be atomic with another write
    (e.g. creating the issue document itself).

    Returns ``True`` if the award was applied, ``False`` if skipped.
    """
    key = _event_key(reason, issue_id)
    if key is not None:
        history = _history_ref(user_id, key)
        if history_snap is None:
            history_snap = next(transaction.get(history), None)
        if history_snap is not None and history_snap.exists:
            logger.info("Award skipped (already granted): user=%s key=%s", user_id, key)
            return False
        transaction.set(
            history,
            {
                "reason": reason,
                "points": points,
                "issueId": issue_id,
                "createdAt": firestore.SERVER_TIMESTAMP,
            },
        )

    profile_updates = {
        "userId": user_id,
        "totalPoints": firestore.Increment(points),
        "issuesReported": firestore.Increment(issues_reported),
        "issuesResolved": firestore.Increment(issues_resolved),
        "lastUpdated": firestore.SERVER_TIMESTAMP,
    }
    if display_name:
        profile_updates["displayName"] = display_name

    transaction.set(_profile_ref(user_id), profile_updates, merge=True)
    return True


@firestore.transactional
def _award_points_transaction(
    transaction,
    user_id: str,
    points: int,
    reason: str,
    issue_id: str,
    display_name: str,
    issues_reported: int,
    issues_resolved: int,
):
    add_award_to_transaction(
        transaction,
        user_id=user_id,
        points=points,
        reason=reason,
        issue_id=issue_id,
        display_name=display_name,
        issues_reported=issues_reported,
        issues_resolved=issues_resolved,
    )


def award_points(
    user_id: str,
    points: int,
    reason: str,
    issue_id: str = None,
    display_name: str = None,
    issues_reported: int = 0,
    issues_resolved: int = 0,
):
    """
    Award points and update user statistics atomically.

    Returns the updated user profile dict, or ``None`` if the user id is
    unknown (should not happen, since a profile is created on first award).
    """
    if not user_id:
        raise ValueError("userId is required")
    if points < 0:
        raise ValueError("points must be non-negative")

    _award_points_transaction(
        db.transaction(),
        user_id,
        int(points),
        reason,
        issue_id,
        display_name,
        int(issues_reported),
        int(issues_resolved),
    )
    return get_user_profile(user_id)


def get_user_profile(user_id: str):
    """Return the gamification profile for a user, or ``None`` if absent."""
    doc = _profile_ref(user_id).get()
    return doc.to_dict() if doc.exists else None


def get_user_rank(user_id: str):
    """
    Calculate the user's rank using a single aggregation read.

    Competition ranking is used: rank = (count of users with strictly more
    points) + 1, so tied scores share the same rank. This is O(1) Firestore
    reads (one document read + one index-only count), independent of the
    number of users in the system.
    """
    profile = get_user_profile(user_id)
    if not profile:
        return None
    points = profile.get("totalPoints", 0)
    count = _collection().where("totalPoints", ">", points).count().get()
    ahead = int(count[0][0].value)
    return ahead + 1


def _timestamp_key(value):
    """
    Normalize a Firestore timestamp into a comparable value for tie-breaking.

    ``lastUpdated`` is written with SERVER_TIMESTAMP on every award, so it
    reflects *when the user's total points reached its current value*. The user
    who reached a given total earlier ranks higher, hence ascending order.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.min.replace(tzinfo=timezone.utc)


def get_leaderboard(limit: int = LEADERBOARD_DEFAULT_LIMIT):
    """
    Return the top ``limit`` users ordered by total points.

    Ranking rules:
      1. Highest totalPoints.
      2. On a tie, the user who reached that point total *earlier* ranks higher
         (tie-break on the ``lastUpdated`` timestamp ascending).
      3. Remaining ties fall back to a deterministic userId ascending order.

    Strategy: a single Firestore query ordered by ``totalPoints`` descending and
    limited to ``limit`` documents (≤ limit reads regardless of user count),
    then the tie-breaks are applied in Python.
    """
    query = (
        _collection()
        .order_by("totalPoints", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    entries = [doc.to_dict() for doc in query.stream()]

    entries.sort(
        key=lambda u: (
            -(u.get("totalPoints") or 0),
            _timestamp_key(u.get("lastUpdated")),
            u.get("userId") or "",
        )
    )
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1
    return entries
