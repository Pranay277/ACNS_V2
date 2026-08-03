"""
shared/constants/ — Application-wide constant values.

All runtime constants (point values, collection names, statuses, thresholds)
live in a single place: ``core/config.py``. This package is reserved for
constant definitions that are specific to a feature or shared across features
but not config/env-driven; today there are none, so the package intentionally
stays empty to avoid duplicating configuration.
"""
