import html
from typing import Any, Optional


def escape_html(text: Optional[Any]) -> str:
    if text is None:
        return ""
    return html.escape(str(text))
