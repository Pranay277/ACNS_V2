"""
tests/test_sms_templates.py — Regression tests for the localized SMS templates.
"""

import pytest

from features.sms import templates as sms_templates
from features.sms.service import build_issue_assigned_message

ISSUE = {
    "campus": "Methodist College of Engineering & Technology",
    "department": "Electrical",
    "category": "Electrical",
    "building": "A Block",
    "location": "Near Main Gate",
    "priority": "High",
    "description": "Flickering light in corridor",
    "image_url": "https://storage.example/photo.jpg",
    "issue_url": "https://acns-v2.vercel.app/issues/methodist/abc123",
    "issue_id": "abc123",
}


@pytest.mark.parametrize("language", ["en", "te", "hi"])
def test_all_languages_render(language):
    message = build_issue_assigned_message(ISSUE, language)
    assert isinstance(message, str)
    assert len(message) > 100
    assert ISSUE["issue_url"] in message
    assert ISSUE["building"] in message


def test_unknown_language_falls_back_to_english():
    message = build_issue_assigned_message(ISSUE, "xx")
    assert message == build_issue_assigned_message(ISSUE, "en")


def test_missing_language_falls_back_to_english():
    assert build_issue_assigned_message(ISSUE, None) == build_issue_assigned_message(ISSUE, "en")


def test_english_includes_photo_notice_without_image_data():
    message = build_issue_assigned_message(ISSUE, "en")
    assert "View the uploaded photo in the SCIARS dashboard." in message
    assert "View Uploaded Photo" not in message
    assert ISSUE["image_url"] not in message
    assert "data:image" not in message


def test_english_omits_photo_notice_when_missing():
    issue = dict(ISSUE, image_url=None)
    message = build_issue_assigned_message(issue, "en")
    assert "View the uploaded photo in the SCIARS dashboard." not in message
    assert "data:image" not in message


def test_message_never_contains_base64_or_localhost():
    for language in ["en", "te", "hi"]:
        message = build_issue_assigned_message(ISSUE, language)
        assert "data:image" not in message
        assert "base64" not in message
        assert "localhost" not in message
        assert len(message) < 4096


def test_registry_get_template():
    assert sms_templates.get_template("en") is sms_templates.english
    assert sms_templates.get_template("te") is sms_templates.telugu
    assert sms_templates.get_template("hi") is sms_templates.hindi
    assert sms_templates.get_template("") is sms_templates.english
