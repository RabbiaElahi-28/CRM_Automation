"""Session-level timing for HTML report duration fallback."""

from __future__ import annotations

import time

SESSION_START_KEY = "_automation_session_start_perf"


def mark_session_start(session) -> None:
    session.config.stash[SESSION_START_KEY] = time.perf_counter()


def resolve_session_duration_seconds(session) -> float:
    """Return elapsed session seconds from perf_counter fallback."""
    start = session.config.stash.get(SESSION_START_KEY, None)
    if start is None:
        return 0.0
    return max(0.0, time.perf_counter() - start)
