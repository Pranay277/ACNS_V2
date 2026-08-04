"""
core/logging.py — Root logging configuration.

The application logs through the standard library ``logging`` package (each
module creates ``logging.getLogger(__name__)``). This module provides an
idempotent :func:`configure_logging` that installs a single root handler.

Behavior is preserved: the default level is ``WARNING`` — the same effective
level Python uses when no configuration exists — so enabling this does not
change what is printed. Raise the verbosity by setting ``LOG_LEVEL`` to
``DEBUG``, ``INFO``, ``WARNING``, or ``ERROR`` in the environment.

Structured logging (P2-07) is available by setting ``LOG_FORMAT=json`` in the
environment. Each record is emitted as a single JSON line with ``time``,
``level``, ``logger`` and ``message`` fields (plus ``exc_info`` when an
exception is attached). The default ``text`` format is unchanged, so existing
log pipelines keep working.
"""

import json
import logging
import os
import traceback

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

_configured = False


class _JsonFormatter(logging.Formatter):
    """Emit each log record as one JSON line (structured logging)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = "".join(
                traceback.format_exception(*record.exc_info)
            ).rstrip()
        return json.dumps(payload, default=str)


def _build_formatter(log_format: str) -> logging.Formatter:
    if (log_format or "").strip().lower() == "json":
        return _JsonFormatter()
    return logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def configure_logging() -> None:
    """Install the root handler once. Safe to call multiple times."""
    global _configured
    if _configured:
        return
    level = _LEVELS.get((os.environ.get("LOG_LEVEL") or "WARNING").upper(), logging.WARNING)
    log_format = os.environ.get("LOG_FORMAT") or "text"
    handler = logging.StreamHandler()
    handler.setFormatter(_build_formatter(log_format))
    logging.basicConfig(level=level, handlers=[handler])
    _configured = True
