"""Categories and tags: how the two form fields are cleaned and turned into page names.

A Post has one category (a single field) and tags (one comma-separated field). Names
that slugify alike ("Pitches", "pitches") are the same category or tag.
"""
from __future__ import annotations

import re


def term_slug(name: str) -> str:
    """The address-name of a category or tag; empty when it has no letters or digits."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def clean_category(raw: str) -> str:
    return " ".join(raw.split())


def parse_tags(raw: str) -> list[str]:
    """Comma-separated names, trimmed, without blanks or repeats (first spelling wins)."""
    seen, tags = set(), []
    for part in raw.split(","):
        name = " ".join(part.split())
        key = term_slug(name) or name.lower()
        if name and key not in seen:
            seen.add(key)
            tags.append(name)
    return tags


def clean_tags(raw: str) -> str:
    """The stored form of the tags field."""
    return ", ".join(parse_tags(raw))
