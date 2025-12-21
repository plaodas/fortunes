from typing import Any, Dict

from jinja2 import Environment


def render_life_analysis(context: Dict[str, Any], template: str) -> str:
    """Render the life analysis template using Jinja2.

    - `context` may contain keys with non-ASCII names (e.g. '年柱').
    - Dotted keys like `年柱.干支` will resolve to nested dict values.
    """
    env = Environment()
    jtpl = env.from_string(template)
    return jtpl.render(**context)
