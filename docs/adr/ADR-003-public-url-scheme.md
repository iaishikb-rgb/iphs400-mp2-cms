# ADR-003: Public URL scheme, with slugs fixed at creation

**Status:** accepted
**Date:** 2026-10-21

## Context

We share links to Posts and Pages in club emails and with alumni, so links must
stay stable. GitHub Pages serves the static site from a subfolder, so links must
be relative. A Post and a Page must never share a file name.

## Decision

- Posts are published at `posts/<slug>.html`, Pages at `<slug>.html`.
- A slug is generated once from the title when the item is first saved. Editing
  the title never changes it. Only a President (Admin role) can edit a slug by hand.
- Old slugs are not redirected.
- A duplicate title gets `-1`, `-2`, ... appended; `index` is reserved.

## Options rejected

- **One shared namespace for Posts and Pages:** a Post and a Page both called
  "about" would collide on one file name.
- **Date-based URLs (`2026/10/slug.html`):** longer; our Posts are announcements,
  not a dated blog.
- **Regenerating the slug on every title edit:** breaks links already sent in emails.

## Consequences

- Links in emails survive title edits.
- A President who changes a slug by hand breaks the old link for good.
