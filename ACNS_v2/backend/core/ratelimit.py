"""
core/ratelimit.py — Lightweight in-memory rate limiting (P2-02).

Sliding fixed-window counters keyed by ``(scope, client_ip)``. No Redis or
external infrastructure: state lives in process memory, which is the right
fit for the current single-instance deployment. Limits are centralized in
``core.config.RATE_LIMITS`` and every value is env-overridable.

Usage — add a FastAPI dependency to an endpoint::

    from core.ratelimit import rate_limited

    @router.post("/login")
    def login(..., _: None = Depends(rate_limited("login"))):
        ...

When a limit is exceeded the dependency raises HTTP 429 with the standard
``{"success": False, "message": ...}`` error shape and the event is logged.
Setting ``RATE_LIMIT_ENABLED=false`` disables enforcement without touching
the endpoints.
"""

import logging
import threading
import time

from fastapi import HTTPException, Request

from core.config import RATE_LIMITS, RATE_LIMIT_ENABLED

logger = logging.getLogger(__name__)

RATE_LIMIT_MESSAGE = "Too many requests. Please try again later."


class InMemoryRateLimiter:
    """Thread-safe fixed-window in-memory rate limiter. O(1) per check."""

    def __init__(self):
        self._buckets = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        """Drop all counters (used by tests)."""
        with self._lock:
            self._buckets.clear()

    def allow(self, scope: str, key: str, limit: int, window_seconds: int, now: float = None) -> bool:
        """
        Record one attempt and report whether it is within ``limit`` for the
        current ``window_seconds`` fixed window. Returns False once exceeded.
        """
        now = now if now is not None else time.time()
        bucket = (scope, key)
        with self._lock:
            start, count = self._buckets.get(bucket, (0, 0))
            if now - start >= window_seconds:
                start, count = now, 0
            count += 1
            self._buckets[bucket] = (start, count)
            return count <= limit


# Shared instance used by the rate_limited dependency (and by tests).
rate_limiter = InMemoryRateLimiter()


def rate_limited(scope: str):
    """
    Dependency factory: enforce the configured limit for ``scope`` per client
    IP. Raises HTTP 429 (standard error shape) when the limit is exceeded.
    """

    def dependency(request: Request):
        if not RATE_LIMIT_ENABLED:
            return None
        client_host = request.client.host if request.client else "unknown"
        limit, window_seconds = RATE_LIMITS.get(scope, (30, 60))
        if not rate_limiter.allow(scope, client_host, limit, window_seconds):
            logger.warning(
                "Rate limit exceeded: scope=%s client=%s limit=%d window=%ds",
                scope,
                client_host,
                limit,
                window_seconds,
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "success": False,
                    "message": RATE_LIMIT_MESSAGE,
                    "retryAfter": window_seconds,
                },
            )
        return None

    return dependency
