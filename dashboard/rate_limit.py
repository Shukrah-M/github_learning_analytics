"""
Small in-memory rate limiter for the add-repository endpoint.

Its purpose is narrow: blunt casual abuse of the GitHub token if the
dashboard is reachable publicly (anyone could otherwise trigger
unlimited extraction runs). State is per-process — if deployed behind
multiple worker processes, each enforces its own limit independently,
so the effective limit scales with worker count. That's an accepted
trade-off for a single lightweight file with no extra dependency; a
shared store (e.g. Redis) would be needed for a strict global limit.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        timestamps = self._requests[key]

        while timestamps and now - timestamps[0] > self.window_seconds:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            return False

        timestamps.append(now)
        return True
