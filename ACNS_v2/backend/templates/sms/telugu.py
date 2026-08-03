"""
templates/sms/telugu.py — Telugu (తెలుగు) SMS template.

Natural Telugu translation of the assignment notification. URLs, the ACNS
brand, and technical identifiers are left untouched; only the surrounding
prose is localized. The image section is omitted when there is no photo.
"""


def build_issue_assigned_sms(issue: dict) -> str:
    """
    Build the Telugu SMS body for a newly assigned issue.

    Args:
        issue: resolved issue context (see templates/sms/__init__.py).

    Returns:
        The formatted SMS body in Telugu.
    """
    lines = [
        "🚨 ACNS అలర్ట్",
        "",
        "మీ విభాగానికి ఒక కొత్త ఇష్యూ కేటాయించబడింది.",
        "",
        "🏫 క్యాంపస్: " + (issue.get("campus") or "తెలియదు"),
        "",
        "🏢 విభాగం: " + (issue.get("department") or "తెలియదు"),
        "",
        "📂 కేటగిరీ: " + (issue.get("category") or "తెలియదు"),
        "",
        "📍 భవనం: " + (issue.get("building") or "తెలియదు"),
        "",
        "📌 స్థానం: " + (issue.get("location") or "తెలియదు"),
        "",
        "⚠️ ప్రాధాన్యత: " + (issue.get("priority") or "సాధారణం"),
        "",
        "📝 వివరణ:",
        issue.get("description") or "—",
    ]
    image_url = issue.get("image_url")
    if image_url:
        lines += [
            "",
            "📷 అప్‌లోడ్ చేసిన ఫోటోను చూడండి:",
            image_url,
        ]
    lines += [
        "",
        "🌐 పూర్తి ఇష్యూను చూడండి:",
        issue.get("issue_url") or "",
        "",
        "దయచేసి ఈ ఇష్యూను వీలైనంత త్వరగా పరిశీలించి పరిష్కరించండి.",
        "",
        "సురక్షితమైన మరియు అందుబాటులో ఉండే క్యాంపస్‌ను నిర్వహించడంలో మీ సహకారానికి ధన్యవాదాలు.",
        "",
        "— ACNS టీమ్",
    ]
    return "\n".join(lines)
