"""Lightweight fake `litellm` module used for tests when the real package
is not installed in the test environment.

This provides the minimal API surface the application expects:
- `completion(...)` returning a simple object with `.choices[0].message.content` and `.raw`
- exception classes `AuthenticationError`, `RateLimitError`, `APIError`
- `_turn_on_debug()` no-op helper used by some tests
"""

from types import SimpleNamespace


class AuthenticationError(Exception):
    pass


class RateLimitError(Exception):
    pass


class APIError(Exception):
    pass


def completion(*args, **kwargs):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="[FAKE RESP]"))],
        raw={"id": "fake", "usage": {}},
    )


def _turn_on_debug():
    return None
