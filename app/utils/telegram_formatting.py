import html
from typing import Any, Dict, Optional


def escape_html(text: Optional[Any]) -> str:
    if text is None:
        return ""
    return html.escape(str(text))


def bold(text: Any) -> str:
    return f"<b>{escape_html(text)}</b>"


def italic(text: Any) -> str:
    return f"<i>{escape_html(text)}</i>"


def code(text: Any) -> str:
    return f"<code>{escape_html(text)}</code>"


def pre(text: Any) -> str:
    return f"<pre>{escape_html(text)}</pre>"
