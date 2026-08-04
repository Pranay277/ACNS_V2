"""
features/sms/counters.py — Persistent usage counters for SMS abuse protection.

Implements the P2-06 guards on top of the real-money SMS gateway:

* per-user daily new-issue cap  (``SMS_ABUSE_MAX_NEW_ISSUES_PER_USER_PER_DAY``)
* per-supervisor daily SMS cap  (``SMS_ABUSE_MAX_SMS_PER_SUPERVISOR_PER_DAY``)
* per-supervisor dispatch cooldown (``SMS_ABUSE_SMS_COOLDOWN_SECONDS``)

Counters are persisted in Firestore (``usage_counters`` collection) so they
survive restarts, and incremented transactionally so concurrent requests can
not race past the caps. All guards FAIL OPEN: a counter read/write error logs
and lets the request through, so a counter outage never blocks a legitimate
report or SMS. These counters are intentionally independent from the
duplicate-SMS guard (``smsSent``/``smsSentAt``) and never weaken it.
"""

import logging
import time
from datetime import datetime

from firebase_admin import firestore

from core.config import (
    SMS_ABUSE_COUNTERS_COLLECTION,
    SMS_ABUSE_ENABLED,
    SMS_ABUSE_MAX_NEW_ISSUES_PER_USER_PER_DAY,
    SMS_ABUSE_MAX_SMS_PER_SUPERVISOR_PER_DAY,
    SMS_ABUSE_SMS_COOLDOWN_SECONDS,
)
from core.firebase import db

logger = logging.getLogger(__name__)


def _window_key() -> str:
    """UTC day key so counters roll over at midnight (e.g. ``2026-08-04``)."""
    return datetime.utcnow().strftime("%Y-%m-%d")


def _counter_ref(kind: str, uid: str, window_key: str):
    return db.collection(SMS_ABUSE_COUNTERS_COLLECTION).document(f"{kind}:{window_key}:{uid}")


def _read_count(transaction, counter_ref):
    """Read the counter document via the transaction; return its dict or {}."""
    snap = next(transaction.get(counter_ref), None)
    return snap.to_dict() if snap is not None and snap.exists else {}


def _issue_counter_impl(transaction, counter_ref, window_key, limit):
    """
    Increment the new-issue counter, capped at ``limit`` per day. Returns
    ``{"allowed": bool, "count": int, "retryAfter": None}``. When the cap is
    reached nothing is written and ``allowed`` is False (do NOT create the
    issue). No cooldown applies — the daily cap alone gates issue creation.
    """
    data = _read_count(transaction, counter_ref)
    count = int(data.get("count") or 0)
    if count >= limit:
        return {"allowed": False, "count": count, "retryAfter": None}
    transaction.set(
        counter_ref,
        {
            "count": count + 1,
            "windowKey": window_key,
            "updatedAt": datetime.utcnow().isoformat(),
        },
        merge=True,
    )
    return {"allowed": True, "count": count + 1, "retryAfter": None}


def _sms_counter_impl(transaction, counter_ref, window_key, daily_limit, cooldown_seconds):
    """
    Reserve one SMS dispatch slot. Returns ``{"allowed": bool, "count": int,
    "retryAfter": int|None}``. ``retryAfter`` is set when a cooldown is
    active; the daily cap also blocks. Nothing is written when blocked.
    """
    data = _read_count(transaction, counter_ref)
    count = int(data.get("count") or 0)
    now = time.time()
    last_sent = float(data.get("lastSentAtEpoch") or 0)
    if count >= daily_limit:
        return {"allowed": False, "count": count, "retryAfter": None}
    if last_sent and (now - last_sent) < cooldown_seconds:
        return {
            "allowed": False,
            "count": count,
            "retryAfter": int(cooldown_seconds - (now - last_sent)) + 1,
        }
    transaction.set(
        counter_ref,
        {
            "count": count + 1,
            "windowKey": window_key,
            "lastSentAtEpoch": now,
            "updatedAt": datetime.utcnow().isoformat(),
        },
        merge=True,
    )
    return {"allowed": True, "count": count + 1, "retryAfter": None}


@firestore.transactional
def _issue_counter_transaction(transaction, counter_ref, window_key, limit):
    return _issue_counter_impl(transaction, counter_ref, window_key, limit)


@firestore.transactional
def _sms_counter_transaction(transaction, counter_ref, window_key, daily_limit, cooldown_seconds):
    return _sms_counter_impl(transaction, counter_ref, window_key, daily_limit, cooldown_seconds)


def increment_issue_counter(uid: str) -> bool:
    """
    Count a new-issue creation for a user. Returns True while under the daily
    cap, False when the cap is reached (caller must NOT create the issue).
    Fails open: returns True on any counter error so reporting is never blocked
    by the guard itself.
    """
    if not SMS_ABUSE_ENABLED:
        return True
    if not uid:
        return True
    window = _window_key()
    try:
        result = _issue_counter_transaction(
            db.transaction(), _counter_ref("issues", uid, window), window, SMS_ABUSE_MAX_NEW_ISSUES_PER_USER_PER_DAY
        )
        return bool(result.get("allowed"))
    except Exception as exc:  # noqa: BLE001 — fail open
        logger.exception("Issue usage counter failed for uid=%s: %s", uid, exc)
        return True


def increment_sms_counter(uid: str):
    """
    Reserve an SMS dispatch slot for a supervisor. Returns ``(allowed,
    retry_after)`` — ``retry_after`` is an int of seconds when a cooldown is
    active, else None. Fails open: ``(True, None)`` on any counter error so an
    outage never blocks a legitimately-required SMS.
    """
    if not SMS_ABUSE_ENABLED:
        return True, None
    if not uid:
        return True, None
    window = _window_key()
    try:
        result = _sms_counter_transaction(
            db.transaction(),
            _counter_ref("sms", uid, window),
            window,
            SMS_ABUSE_MAX_SMS_PER_SUPERVISOR_PER_DAY,
            SMS_ABUSE_SMS_COOLDOWN_SECONDS,
        )
        return bool(result.get("allowed")), result.get("retryAfter")
    except Exception as exc:  # noqa: BLE001 — fail open
        logger.exception("SMS usage counter failed for supervisor uid=%s: %s", uid, exc)
        return True, None
