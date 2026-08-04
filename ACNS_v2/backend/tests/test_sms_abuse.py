"""
tests/test_sms_abuse.py — P2-06 SMS-abuse protection regression tests.

Covers the persisted usage counters (features/sms/counters.py): daily
new-issue cap, daily SMS cap, dispatch cooldown, fail-open behaviour, and the
wiring in the issue/notification flow. The counter internals run against an
in-memory fake transaction; nothing touches a real database.
"""

import pytest
from fastapi import HTTPException

from features import sms
from features.issues import service as issues_service
from features.issues.schemas import IssueCreate
from features.notifications import service as notif_service

counters = sms.counters


class _FakeSnapshot:
    def __init__(self, data, exists):
        self._data = data
        self.exists = exists

    def to_dict(self):
        return dict(self._data)


class _FakeRef:
    def __init__(self, rid):
        self.id = rid


class _FakeTxn:
    """Fake Firestore transaction: get() returns an iterator, set() merges."""

    def __init__(self, store):
        self._store = store

    def get(self, ref):
        exists = ref.id in self._store
        return iter([_FakeSnapshot(dict(self._store.get(ref.id) or {}), exists)])

    def set(self, ref, data, merge=True):
        existing = dict(self._store.get(ref.id) or {}) if merge else {}
        existing.update(data)
        self._store[ref.id] = existing


# ── Issue counter: daily cap ───────────────────────────────────────────────────


def test_issue_counter_blocks_after_daily_limit():
    store = {}
    txn = _FakeTxn(store)
    ref = _FakeRef("issues:2026-08-04:u1")
    limit = 2

    assert counters._issue_counter_impl(txn, ref, "2026-08-04", limit)["allowed"] is True
    assert counters._issue_counter_impl(txn, ref, "2026-08-04", limit)["allowed"] is True

    blocked = counters._issue_counter_impl(txn, ref, "2026-08-04", limit)
    assert blocked["allowed"] is False
    assert store[ref.id]["count"] == limit, "counter must not be incremented past the cap"


def test_issue_counter_resets_per_window_key():
    store = {}
    txn = _FakeTxn(store)
    ref = _FakeRef("issues:2026-08-04:u1")
    limit = 1

    assert counters._issue_counter_impl(txn, ref, "2026-08-04", limit)["allowed"] is True
    assert counters._issue_counter_impl(txn, ref, "2026-08-04", limit)["allowed"] is False
    # A new window key (next UTC day) starts fresh.
    ref2 = _FakeRef("issues:2026-08-05:u1")
    assert counters._issue_counter_impl(txn, ref2, "2026-08-05", limit)["allowed"] is True


# ── SMS counter: cooldown + daily cap ──────────────────────────────────────────


def test_sms_counter_enforces_cooldown_then_daily_limit(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(counters.time, "time", lambda: now[0])

    store = {}
    txn = _FakeTxn(store)
    ref = _FakeRef("sms:2026-08-04:sup1")
    limit, cooldown = 3, 60

    first = counters._sms_counter_impl(txn, ref, "2026-08-04", limit, cooldown)
    assert first["allowed"] is True

    second = counters._sms_counter_impl(txn, ref, "2026-08-04", limit, cooldown)
    assert second["allowed"] is False
    assert second["retryAfter"] == cooldown + 1

    now[0] = 1061.0
    third = counters._sms_counter_impl(txn, ref, "2026-08-04", limit, cooldown)
    assert third["allowed"] is True

    now[0] = 2000.0
    assert counters._sms_counter_impl(txn, ref, "2026-08-04", limit, cooldown)["allowed"] is True
    blocked = counters._sms_counter_impl(txn, ref, "2026-08-04", limit, cooldown)
    assert blocked["allowed"] is False
    assert blocked["retryAfter"] is None
    assert store[ref.id]["count"] == limit


# ── Public wrappers: fail-open + disable switch ────────────────────────────────


def test_issue_counter_fails_open_on_transaction_error(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("firestore unavailable")

    monkeypatch.setattr(counters, "_issue_counter_transaction", boom)
    assert counters.increment_issue_counter("u1") is True


def test_sms_counter_fails_open_on_transaction_error(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("firestore unavailable")

    monkeypatch.setattr(counters, "_sms_counter_transaction", boom)
    assert counters.increment_sms_counter("sup1") == (True, None)


def test_issue_counter_reports_blocked(monkeypatch):
    monkeypatch.setattr(
        counters, "_issue_counter_transaction", lambda *a, **k: {"allowed": False}
    )
    assert counters.increment_issue_counter("u1") is False


def test_sms_counter_reports_blocked_with_retry(monkeypatch):
    monkeypatch.setattr(
        counters,
        "_sms_counter_transaction",
        lambda *a, **k: {"allowed": False, "retryAfter": 30},
    )
    assert counters.increment_sms_counter("sup1") == (False, 30)


def test_counters_disabled_via_config(monkeypatch):
    monkeypatch.setattr(counters, "SMS_ABUSE_ENABLED", False)
    assert counters.increment_issue_counter("u1") is True
    assert counters.increment_sms_counter("sup1") == (True, None)


def test_counters_without_uid_fail_open(monkeypatch):
    monkeypatch.setattr(counters, "SMS_ABUSE_ENABLED", True)
    assert counters.increment_issue_counter("") is True
    assert counters.increment_sms_counter(None) == (True, None)


# ── Wiring: create_issue respects the daily new-issue cap ─────────────────────


class _FakeDb:
    def collection(self, name):
        return object()

    def transaction(self):
        raise AssertionError("create_issue must not reach real Firestore")


def test_create_issue_blocked_when_daily_cap_reached(monkeypatch):
    monkeypatch.setattr(issues_service, "db", _FakeDb())
    monkeypatch.setattr(issues_service, "get_user_profile", lambda uid: {"campusId": "methodist"})
    monkeypatch.setattr(issues_service, "resolve_campus_id", lambda college, fallback: "methodist")
    monkeypatch.setattr(issues_service, "nearest_landmark", lambda campus, lat, lng: "e-block")
    monkeypatch.setattr(issues_service, "find_duplicate_issue", lambda **kw: None)
    monkeypatch.setattr(issues_service, "resolve_assigned_supervisor", lambda category: "uid-sup-1")
    monkeypatch.setattr(issues_service, "increment_issue_counter", lambda uid: False)

    issue = IssueCreate(
        userId="client-ignored",
        category="Water",
        description="leak",
        lat=17.39,
        lng=78.47,
        locationText="Block B",
    )
    with pytest.raises(HTTPException) as exc:
        issues_service.create_issue(issue, reporter_uid="student-1")
    assert exc.value.status_code == 429
    assert exc.value.detail["success"] is False


# ── Wiring: notify_issue_assigned honours the SMS counter ──────────────────────


def test_assigned_sms_skipped_when_counter_blocks(monkeypatch):
    monkeypatch.setattr(notif_service, "create_notification", lambda **kw: None)
    monkeypatch.setattr(notif_service, "get_user_profile", lambda uid: {"phoneNumber": "+911234567890"})
    monkeypatch.setattr(counters, "increment_sms_counter", lambda uid: (False, 30))

    sent = []
    monkeypatch.setattr(
        notif_service.sms_service, "send_issue_assigned_sms", lambda *a, **k: sent.append(a)
    )

    notif_service.notify_issue_assigned(
        issue_id="i1", supervisor_uid="sup1", category="Water", location_text="Block B"
    )
    assert sent == [], "SMS must be skipped when the counter blocks"


def test_assigned_sms_sent_when_counter_allows(monkeypatch):
    monkeypatch.setattr(notif_service, "create_notification", lambda **kw: None)
    monkeypatch.setattr(notif_service, "get_user_profile", lambda uid: {"phoneNumber": "+911234567890"})
    monkeypatch.setattr(counters, "increment_sms_counter", lambda uid: (True, None))

    sent = []
    monkeypatch.setattr(
        notif_service.sms_service, "send_issue_assigned_sms", lambda *a, **k: sent.append(a)
    )

    notif_service.notify_issue_assigned(
        issue_id="i1", supervisor_uid="sup1", category="Water", location_text="Block B"
    )
    assert len(sent) == 1
