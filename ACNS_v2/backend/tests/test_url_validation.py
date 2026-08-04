"""
tests/test_url_validation.py — P2-01 stored-XSS regression tests.

Verifies the photo URL validator (shared/utils/validators.py) and its
application on the issue schemas (imageUrl / proofImageUrl / supervisorPhoto).
http/https URLs and raster-image base64 data URLs must pass; javascript:/file:/…
URLs, SVG/HTML data URLs, and malformed/oversized base64 must be rejected at the
schema boundary. Pure logic — no Firebase is touched.
"""

import base64

import pytest
from pydantic import ValidationError

from core.config import MAX_IMAGE_DATA_BYTES
from features.issues.schemas import IssueCreate, IssueStatusUpdate
from shared.utils.validators import validate_safe_url

SAFE_URLS = [
    "https://firebasestorage.googleapis.com/v0/b/my-app/o/images%2Fissue.jpg?alt=media&token=abc",
    "https://example.com/path/photo.jpg?q=1#frag",
    "http://localhost:5173/uploads/photo.png",
    "https://storage.googleapis.com/bucket/folder/image.jpg",
]

# Small, strictly-valid raster data URLs (camera captures are image/jpeg; the
# others cover the remaining raster types).
SAFE_DATA_URLS = [
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
    "data:image/webp;base64,UklGRg==",
    "data:image/bmp;base64,QUlNQQ==",
]

UNSAFE_URLS = [
    "javascript:alert(document.cookie)",
    "JavaScript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
    "data:image/svg+xml,<svg onload=alert(1)>",
    "data:image/png;charset=utf-8;base64,QUJD",
    "data:image/png;base64,@@@notbase64@@@",
    "data:image/png;base64,",
    "file:///etc/passwd",
    "vbscript:msgbox(1)",
    "ftp://example.com/photo.jpg",
    "//example.com/photo.jpg",
    "https://",
    "http://user:pass@example.com/photo.jpg",
    "https://user@example.com/photo.jpg",
    "not a url at all",
]

OVERSIZE_URL = "https://example.com/" + ("a" * 4000)
OVERSIZE_DATA_URL = (
    "data:image/png;base64,"
    + base64.b64encode(b"\x00" * (MAX_IMAGE_DATA_BYTES + 1)).decode()
)


def _base_issue(**overrides):
    values = {
        "userId": "u1",
        "category": "Water",
        "description": "leak",
        "lat": 17.39,
        "lng": 78.47,
        "locationText": "Block B",
    }
    values.update(overrides)
    return values


# ── validate_safe_url: unit behaviour ──────────────────────────────────────────


@pytest.mark.parametrize("url", SAFE_URLS)
def test_validate_safe_url_accepts_http_https(url):
    assert validate_safe_url(url) == url


@pytest.mark.parametrize("url", SAFE_DATA_URLS)
def test_validate_safe_url_accepts_raster_data_urls(url):
    assert validate_safe_url(url) == url


@pytest.mark.parametrize("url", UNSAFE_URLS)
def test_validate_safe_url_rejects_unsafe(url):
    with pytest.raises(ValueError):
        validate_safe_url(url)


def test_validate_safe_url_trims_and_returns_trimmed():
    assert validate_safe_url("  https://example.com/a.jpg  ") == "https://example.com/a.jpg"


def test_validate_safe_url_blank_becomes_none():
    assert validate_safe_url(None) is None
    assert validate_safe_url("") is None
    assert validate_safe_url("   ") is None


def test_validate_safe_url_rejects_oversize_http_url():
    with pytest.raises(ValueError):
        validate_safe_url(OVERSIZE_URL)


def test_validate_safe_url_rejects_oversize_data_url():
    with pytest.raises(ValueError):
        validate_safe_url(OVERSIZE_DATA_URL)


def test_validate_safe_url_rejects_non_string():
    with pytest.raises(ValueError):
        validate_safe_url(12345)


# ── IssueCreate.imageUrl schema validation ─────────────────────────────────────


def test_issue_create_accepts_https_image_url():
    issue = IssueCreate(**_base_issue(imageUrl=SAFE_URLS[0]))
    assert issue.imageUrl == SAFE_URLS[0]


def test_issue_create_accepts_raster_data_image_url():
    issue = IssueCreate(**_base_issue(imageUrl=SAFE_DATA_URLS[0]))
    assert issue.imageUrl == SAFE_DATA_URLS[0]


def test_issue_create_accepts_blank_image_url():
    issue = IssueCreate(**_base_issue(imageUrl="   "))
    assert issue.imageUrl is None


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
        "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
    ],
)
def test_issue_create_rejects_unsafe_image_url(url):
    with pytest.raises(ValidationError):
        IssueCreate(**_base_issue(imageUrl=url))


# ── IssueStatusUpdate proofImageUrl / supervisorPhoto ──────────────────────────


def test_issue_status_update_accepts_safe_photos():
    update = IssueStatusUpdate(
        status="Resolved",
        proofImageUrl="https://example.com/proof.jpg",
        supervisorPhoto="data:image/jpeg;base64,/9j/4AAQSkZJRg==",
    )
    assert update.proofImageUrl == "https://example.com/proof.jpg"
    assert update.supervisorPhoto == "data:image/jpeg;base64,/9j/4AAQSkZJRg=="


@pytest.mark.parametrize("field", ["proofImageUrl", "supervisorPhoto"])
@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
        "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
    ],
)
def test_issue_status_update_rejects_unsafe_photos(field, url):
    with pytest.raises(ValidationError):
        IssueStatusUpdate(status="Resolved", **{field: url})
