"""
features/sms/templates/ — SMS template registry.

Registry mapping ISO 639-1 language codes to their template module. Each
module exposes ``build_issue_assigned_sms(issue)`` where ``issue`` is the
resolved issue context dict:

    {
        "campus":     display name of the campus,
        "department": department the issue was assigned to,
        "category":   issue category,
        "building":   display name of the building / landmark,
        "location":   exact location text,
        "priority":   issue priority,
        "description": issue description,
        "image_url":  Firebase Storage image URL or None,
        "issue_url":  frontend Issue Details link,
        "issue_id":   Firestore issue id,
    }

Adding a new language is purely additive: drop a new module here, register it
in ``_TEMPLATES`` below, and add its code to ``VALID_PREFERRED_LANGUAGES`` in
``core/config.py``. The SMS service and notify orchestrator require no changes.
"""

from . import english, hindi, telugu

_TEMPLATES = {
    "en": english,
    "te": telugu,
    "hi": hindi,
}


def get_template(language_code):
    """
    Resolve the template module for a language code.

    Missing, empty, or unsupported codes fall back to English so a supervisor
    without a ``preferredLanguage`` (or with an unknown one) always receives a
    readable notification.
    """
    return _TEMPLATES.get((language_code or "").strip().lower(), english)


__all__ = ["get_template", "english", "telugu", "hindi"]
