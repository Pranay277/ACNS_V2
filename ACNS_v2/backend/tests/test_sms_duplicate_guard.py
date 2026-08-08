"""
tests/test_sms_duplicate_guard.py — Single-SMS-per-issue regression tests.

Guards the Business Logic Improvement "Prevent Duplicate Supervisor SMS":

    * first report   -> dispatches the assignment SMS exactly once and
                        persists ``smsSent``/``smsSentAt`` on the issue doc
    * duplicate      -> merges into the existing issue, bumps reportCount,
                        and NEVER dispatches another SMS
    * future reports -> keep increasing reportCount, still no SMS
    * a brand-new issue (a fresh document) starts with ``smsSent=False``
                        and sends its own first SMS

The persistence lives on the Firestore issue document, so the guarantee
survives server restarts (no in-memory state is used).

All Firestore access is stubbed with an in-memory fake; no real database is
touched.
"""

from features.issues import service as issues_service
from features.issues.schemas import IssueCreate


class _FakeSnapshot:
    """Minimal Firestore document snapshot stand-in."""

    def __init__(self, data, exists):
        self._data = data
        self.exists = exists

    def to_dict(self):
        return dict(self._data)


class _FakeDocumentRef:
    """Minimal Firestore document reference stand-in backed by a dict store."""

    def __init__(self, store, issue_id):
        self._store = store
        self.id = issue_id

    def get(self):
        exists = self.id in self._store
        return _FakeSnapshot(dict(self._store.get(self.id) or {}), exists)

    def update(self, updates):
        self._store.setdefault(self.id, {}).update(updates)


class _FakeCollection:
    """Minimal Firestore collection stand-in that auto-generates doc ids."""

    def __init__(self, store, next_id):
        self._store = store
        self._next_id = next_id

    def document(self, issue_id=None):
        if issue_id is None:
            issue_id = self._next_id()
        return _FakeDocumentRef(self._store, issue_id)


class _FakeDb:
    """In-memory stand-in for core.firebase.db (only what the flow uses)."""

    def __init__(self, issues=None):
        self._issues = issues if issues is not None else {}
        self._n = 0

    def _next_id(self):
        self._n += 1
        return f"auto-issue-{self._n}"

    def collection(self, name):
        store = self._issues if name == "issues" else {}
        return _FakeCollection(store, self._next_id)

    def transaction(self):
        return object()


def _sample_issue():
    return IssueCreate(
        userId="ignored-client-uid",
        category="Water",
        description="Leak near the entrance",
        lat=17.39,
        lng=78.47,
        locationText="Block B",
    )


def _patch_create_dependencies(monkeypatch, db, duplicate=None):
    """Patch the pre-dispatch dependencies so create_issue reaches the right path."""
    monkeypatch.setattr(issues_service, "db", db)
    monkeypatch.setattr(
        issues_service, "get_user_profile", lambda uid: {"campusId": "methodist"}
    )
    monkeypatch.setattr(
        issues_service, "resolve_campus_id", lambda college, fallback: "methodist"
    )
    monkeypatch.setattr(
        issues_service, "nearest_landmark", lambda campus, lat, lng: "e-block"
    )
    monkeypatch.setattr(
        issues_service,
        "find_duplicate_issue",
        lambda **kw: duplicate,
    )
    # P2-06: keep the SMS-abuse issue counter out of these tests (they focus on
    # the duplicate-SMS guarantee). The counter's own behaviour is covered by
    # tests/test_sms_abuse.py.
    monkeypatch.setattr(issues_service, "increment_issue_counter", lambda uid: True)


# ── Guard behaviour: one dispatch per issue ─────────────────────────────────────


def test_first_dispatch_sends_sms_and_persists(monkeypatch):
    db = _FakeDb({"i1": {"smsSent": False, "smsSentAt": None}})
    monkeypatch.setattr(issues_service, "db", db)
    dispatched = []
    monkeypatch.setattr(
        issues_service, "notify_issue_assigned", lambda **kw: dispatched.append(kw)
    )

    result = issues_service._dispatch_assignment_sms_once(
        issue_id="i1", supervisor_uid="uid-sup-1", category="Water", location_text="Block B"
    )

    assert result is True
    assert len(dispatched) == 1
    assert dispatched[0]["issue_id"] == "i1"
    assert dispatched[0]["supervisor_uid"] == "uid-sup-1"
    assert db._issues["i1"]["smsSent"] is True
    assert db._issues["i1"]["smsSentAt"]


def test_second_dispatch_is_skipped_when_sms_already_sent(monkeypatch):
    db = _FakeDb({"i1": {"smsSent": True, "smsSentAt": "2026-08-04T10:00:00"}})
    monkeypatch.setattr(issues_service, "db", db)
    dispatched = []
    monkeypatch.setattr(
        issues_service, "notify_issue_assigned", lambda **kw: dispatched.append(kw)
    )

    result = issues_service._dispatch_assignment_sms_once(
        issue_id="i1", supervisor_uid="uid-sup-1", category="Water", location_text="Block B"
    )

    assert result is False
    assert dispatched == []
    assert db._issues["i1"]["smsSentAt"] == "2026-08-04T10:00:00"


# ── First report: create + assign + SMS + persist ──────────────────────────────


def test_first_report_sends_sms_once_and_persists_flag(monkeypatch):
    db = _FakeDb()
    _patch_create_dependencies(monkeypatch, db, duplicate=None)
    monkeypatch.setattr(
        issues_service, "resolve_assigned_supervisor", lambda category: "uid-sup-1"
    )

    created = {}

    def fake_create_transaction(transaction, issue_ref, new_issue):
        created["issue_id"] = issue_ref.id
        created["new_issue"] = new_issue
        db._issues[issue_ref.id] = dict(new_issue)

    monkeypatch.setattr(issues_service, "_create_issue_transaction", fake_create_transaction)
    reporter_notifications = []
    monkeypatch.setattr(
        issues_service, "create_notification", lambda **kw: reporter_notifications.append(kw)
    )
    dispatches = []
    monkeypatch.setattr(
        issues_service, "notify_issue_assigned", lambda **kw: dispatches.append(kw)
    )

    result = issues_service.create_issue(_sample_issue(), reporter_uid="student-1")

    assert result["merged"] is False
    assert created["new_issue"]["smsSent"] is False
    assert created["new_issue"]["smsSentAt"] is None

    assert len(dispatches) == 1
    assert dispatches[0]["issue_id"] == created["issue_id"]
    assert dispatches[0]["supervisor_uid"] == "uid-sup-1"
    assert dispatches[0]["category"] == "Water"

    assert db._issues[created["issue_id"]]["smsSent"] is True
    assert db._issues[created["issue_id"]]["smsSentAt"]


# ── Duplicate report: merge, bump count, NO second SMS ─────────────────────────


def test_duplicate_report_merges_and_never_sends_sms(monkeypatch):
    db = _FakeDb()
    _patch_create_dependencies(
        monkeypatch,
        db,
        duplicate=("i1", {"assignedTo": "uid-sup-1", "smsSent": True,
                          "smsSentAt": "2026-08-04T10:00:00"}, 4.2),
    )
    monkeypatch.setattr(
        issues_service,
        "_merge_issue_transaction",
        lambda *args, **kwargs: {
            "found": True,
            "alreadyReported": False,
            "pointsAwarded": 5,
            "reportCount": 2,
        },
    )
    dispatches = []
    monkeypatch.setattr(
        issues_service, "_dispatch_assignment_sms_once", lambda **kw: dispatches.append(kw)
    )

    result = issues_service.create_issue(_sample_issue(), reporter_uid="student-2")

    assert result["merged"] is True
    assert result["reportCount"] == 2
    assert result["pointsAwarded"] == 5
    assert dispatches == [], "duplicate report must never dispatch an SMS"


def test_already_reported_report_never_sends_sms(monkeypatch):
    db = _FakeDb()
    _patch_create_dependencies(
        monkeypatch,
        db,
        duplicate=("i1", {"assignedTo": "uid-sup-1", "smsSent": True,
                          "smsSentAt": "2026-08-04T10:00:00"}, 1.1),
    )
    monkeypatch.setattr(
        issues_service,
        "_merge_issue_transaction",
        lambda *args, **kwargs: {
            "found": True,
            "alreadyReported": True,
            "pointsAwarded": 0,
            "reportCount": 1,
        },
    )
    dispatches = []
    monkeypatch.setattr(
        issues_service, "_dispatch_assignment_sms_once", lambda **kw: dispatches.append(kw)
    )

    result = issues_service.create_issue(_sample_issue(), reporter_uid="student-2")

    assert result["alreadyReported"] is True
    assert result["pointsAwarded"] == 0
    assert dispatches == [], "already-reported report must never dispatch an SMS"
