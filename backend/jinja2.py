"""Tiny stub of jinja2 used for tests when the real package isn't installed.

It implements a minimal `Environment` with `from_string()` returning an
object that exposes `.render(**context)` and simply returns the template
string unchanged. This is enough for tests that only need the template
to be a string passed to the LLM adapter or to exist during imports.
"""

from types import SimpleNamespace


class Environment:
    def __init__(self, *args, **kwargs):
        pass

    def from_string(self, template: str):
        def render(**context):
            # Return template unchanged — tests that require full rendering
            # should use the real jinja2 package.
            return template

        return SimpleNamespace(render=render)
