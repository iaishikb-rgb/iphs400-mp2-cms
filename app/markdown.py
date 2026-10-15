"""Markdown -> sanitized HTML. Every rendered body goes through here."""
from __future__ import annotations

import nh3
from markdown_it import MarkdownIt

# html=False: raw HTML in the source is shown as text, never parsed.
_md = MarkdownIt("commonmark", {"html": False})

ALLOWED_TAGS = {"p", "br", "strong", "em", "code", "pre", "blockquote", "ul", "ol", "li",
                "h1", "h2", "h3", "h4", "h5", "h6", "a", "hr"}


def _relative_links_only(tag: str, attr: str, value: str) -> str | None:
    """Drop root-absolute and protocol-relative hrefs: they break on a Pages subfolder."""
    if attr == "href" and value.lstrip().startswith("/"):
        return None
    return value


def render_markdown(text: str) -> str:
    return nh3.clean(
        _md.render(text),
        tags=ALLOWED_TAGS,
        attributes={"a": {"href"}},
        url_schemes={"http", "https", "mailto"},
        attribute_filter=_relative_links_only,
        link_rel="noopener noreferrer",
    )
