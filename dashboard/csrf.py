"""CSRF token helpers for the dashboard's forms."""

from __future__ import annotations

import secrets

from flask import session


CSRF_SESSION_KEY = "_csrf_token"


def generate_csrf_token() -> str:
    """Return this session's CSRF token, creating one if needed."""
    token = session.get(CSRF_SESSION_KEY)

    if not token:
        token = secrets.token_hex(16)
        session[CSRF_SESSION_KEY] = token

    return token


def validate_csrf_token(submitted_token: str | None) -> bool:
    expected = session.get(CSRF_SESSION_KEY)

    return bool(expected) and secrets.compare_digest(
        expected,
        submitted_token or "",
    )
