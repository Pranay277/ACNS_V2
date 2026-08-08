"""
features/sms/templates/english.py — English SMS template.

Produces a complete issue-assignment notification. URLs (Firebase image link,
frontend issue link) are passed in pre-resolved — this module never builds or
hardcodes a URL.
"""


def build_issue_assigned_sms(issue: dict) -> str:
    """
    Build the English SMS body for a newly assigned issue.

    Args:
        issue: resolved issue context (see features/sms/templates/__init__.py).

    Returns:
        The formatted SMS body. The image section is omitted entirely when
        ``issue["image_url"]`` is missing or empty.
    """
    lines = [
        "🚨 ACNS ALERT",
        "",
        "A new issue has been assigned to your department.",
        "",
        "🏫 Campus: " + (issue.get("campus") or "Unknown"),
        "",
        "🏢 Department: " + (issue.get("department") or "Unknown"),
        "",
        "📂 Category: " + (issue.get("category") or "Unknown"),
        "",
        "📍 Building: " + (issue.get("building") or "Unknown"),
        "",
        "📌 Location: " + (issue.get("location") or "Unknown"),
        "",
        "⚠️ Priority: " + (issue.get("priority") or "Normal"),
        "",
        "📝 Description:",
        issue.get("description") or "—",
    ]
    if issue.get("image_url"):
        lines += [
            "",
            "📷 View the uploaded photo in the SCIARS dashboard.",
        ]
    lines += [
        "",
        "🌐 View Complete Issue:",
        issue.get("issue_url") or "",
        "",
        "Please inspect and resolve this issue at the earliest.",
        "",
        "Thank you for helping maintain a safe and accessible campus.",
        "",
        "— ACNS Team",
    ]
    return "\n".join(lines)
