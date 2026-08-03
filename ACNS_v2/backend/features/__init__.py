"""
features/ — Vertical slices organized by business capability.

Each subpackage owns its HTTP layer (``router.py``), business logic
(``service.py``), request/response schemas (``schemas.py``), and any
feature-specific helpers. Cross-feature concerns live in ``core/`` and
``shared/``.
"""
