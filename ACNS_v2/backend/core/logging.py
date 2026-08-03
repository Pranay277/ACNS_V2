"""
core/logging.py — Root logging configuration.

The application logs through the standard library ``logging`` package (each
module creates ``logging.getLogger(__name__)``). This module provides an
idempotent :func:`configure_logging` that installs a single root handler.

Behavior is preserved: the default level is ``WARNING`` — the same effective
level Python uses when no configuration exists — so enabling this does not
change what is printed. Raise the verbosity by setting ``LOG_LEVEL`` to
``DEBUG``, ``INFO``, ``WARNING``, or ``ERROR`` in the environment.
"""

import logging
import os

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

_configured = False


def configure_logging() -> None:
    """Install the root handler once. Safe to call multiple times."""
    global _configured
    if _configured:
        return
    level = _LEVELS.get((os.environ.get("LOG_LEVEL") or "WARNING").upper(), logging.WARNING)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _configured = True
