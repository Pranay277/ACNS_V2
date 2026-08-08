"""
features/sms/templates/hindi.py — Hindi (हिन्दी) SMS template.

Natural Hindi translation of the assignment notification. URLs, the ACNS
brand, and technical identifiers are left untouched; only the surrounding
prose is localized. The image section is omitted when there is no photo.
"""


def build_issue_assigned_sms(issue: dict) -> str:
    """
    Build the Hindi SMS body for a newly assigned issue.

    Args:
        issue: resolved issue context (see features/sms/templates/__init__.py).

    Returns:
        The formatted SMS body in Hindi.
    """
    lines = [
        "🚨 ACNS अलर्ट",
        "",
        "आपके विभाग को एक नई शिकायत सौंपी गई है।",
        "",
        "🏫 कैम्पस: " + (issue.get("campus") or "अज्ञात"),
        "",
        "🏢 विभाग: " + (issue.get("department") or "अज्ञात"),
        "",
        "📂 श्रेणी: " + (issue.get("category") or "अज्ञात"),
        "",
        "📍 भवन: " + (issue.get("building") or "अज्ञात"),
        "",
        "📌 स्थान: " + (issue.get("location") or "अज्ञात"),
        "",
        "⚠️ प्राथमिकता: " + (issue.get("priority") or "सामान्य"),
        "",
        "📝 विवरण:",
        issue.get("description") or "—",
    ]
    if issue.get("image_url"):
        lines += [
            "",
            "📷 View the uploaded photo in the SCIARS dashboard.",
        ]
    lines += [
        "",
        "🌐 पूरी शिकायत देखें:",
        issue.get("issue_url") or "",
        "",
        "कृपया इस समस्या का जल्द से जल्द निरीक्षण कर समाधान करें।",
        "",
        "सुरक्षित और सुलभ कैंपस बनाए रखने में मदद करने के लिए धन्यवाद।",
        "",
        "— ACNS टीम",
    ]
    return "\n".join(lines)
