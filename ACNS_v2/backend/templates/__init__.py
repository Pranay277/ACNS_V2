"""
templates/ — Language-specific SMS message templates.

Each language module under ``templates/sms/`` exposes
``build_issue_assigned_sms(issue)`` and produces a fully formatted SMS body
with all language strings baked in. The notification orchestrator
(``services/notify.py``) and the SMS dispatcher (``services/sms_service.py``)
never contain language-specific text — they only resolve a language code and
delegate to the matching template module.
"""
