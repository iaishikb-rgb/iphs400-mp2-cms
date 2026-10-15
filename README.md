# Kenyon College Finance Club CMS (IPHS 400 Mini-Project #2)

A small content management system for the Kenyon College Finance Club. Presidents and Officers write Posts and Pages in a local admin console (FastAPI, Jinja, SQLite), and `cms publish` turns the Live content into a static site on GitHub Pages. The admin console never goes on the public internet.

## Live URL

https://iaishikb-rgb.github.io/iphs400-mp2-cms/ (the club's public site, served from the `gh-pages` branch)

## Run locally

Needs [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync
cp .env.example .env                      # demo passwords; change them for anything real
uv run python scripts/seed_demo.py        # demo users, club Pages and Posts (safe to re-run)
uv run pytest -q                          # optional: run the test suite
uv run cms serve                          # admin console at http://localhost:8000/login
```

Demo sign-ins (from `.env.example`): `admin@example.test` / `change-me-admin` (President, Admin)
and `editor@example.test` / `change-me-editor` (Officer, Editor).

To refresh the public site: `uv run cms publish` writes `site/`, and `uv run cms deploy` pushes it
to `gh-pages`.

## Where things are

```text
app/, templates/   the CMS: models, routes, admin and public templates
tests/             the test suite, including tests/test_access_control.py (every admin route)
scripts/           seed_demo.py, usage_report.py, check_submission.py
.claude/hooks/     context meter, usage ledger, transcript saver
CONTEXT.md         the project glossary
docs/              report, screenshots, transcripts, handoff, compaction log, ADRs
notes/             field notes, client brief, token budget plan, usage ledger
```

## Generative AI Use Statement

I built this project with Claude Code inside Orca, using `--dangerously-skip-permissions` the way we set it up in class. Claude wrote nearly all of the code. My part was deciding what the club actually needed and answering the grill. I also read the tests and reviews, and caught the places where the implementation fell short.

**Models.** I used Claude Sonnet for most of the project: the grill, the spec, the tickets, all seven tickets and the reviews. One early setup session ran on Haiku because I hadn't noticed which model was selected. My budget plan called for opusplan during planning, but on the night of October 14 I switched the grill to Sonnet. I was worried about hitting my five-hour limit before I even started the tickets.

**Skills.** The mattpocock skills: `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement` (which ran `/tdd`) and `/code-review`. I used `/ask-matt` once to check the workflow. I also relied on the course hooks for the context meter, the usage ledger and the transcript saver.

**Two prompts I sent**

1. To begin the grill:

   > /grill-with-docs I am building a small CMS for the Kenyon College Finance Club, which my two co-presidents and I run. My field notes are in notes/cms-field-notes.md and my client brief is in notes/client-brief.md. The 7 required capabilities are in docs/manual_iphs400_mp2-web-cms_20260922.md, Part 3.3. Help me decide what they mean for this club. Write the glossary to CONTEXT.md. Ask one question at a time.

2. In response to the grill's proposed sign-in process, at question 14:

   > Partly. Yes to signing in with a Kenyon email plus password, and yes to admin-assisted resets. We'd do that in person at a board meeting in Oden anyway. But no forced password change at first sign-in: there are only ~8 officers, a president sets the password face to face, and I'd rather not build an extra screen with the deadline this week. Keep a simple idle sign-out, about 2 hours, because we do share a laptop at meetings.

**A model failure.** In T06, Claude's first version of user management let a President demote themselves, even though the spec says they can't. With three co-presidents, someone would do that by accident during the spring handover and lock themselves out of user management. `/code-review` caught it before the commit, and the fix has a test (issue #7).

**One I caught myself.** After T06 I finally clicked through the app by hand, and `seed_demo.py` refused to run on a fresh `.env`, so the server never started. Every test was green because none of them ran the seed script. I opened bug issue #9 and fixed it with a test that runs the seed as a subprocess from a fresh `.env.example`. Green tests are not the same as a working app. I should have been using the app after every ticket.

**Also caught in review.** In T01, the skills created a stray `GLOSSARY.md` even though my `CLAUDE.md` says the glossary is `CONTEXT.md` (fixed in `1557b24`).

**Authorship note.** Commits made before October 15 show the placeholder author "Your Full Name" because my Git identity wasn't configured on this laptop. The `.mailmap` file maps those commits to me. Every commit in this repository is mine.

I drafted this statement with Claude's help and then edited and rephrased it.

### Backends used

| Provider | Models | Use |
| --- | --- | --- |
| Anthropic (Claude Pro) | Sonnet, Haiku | All project development. No backup provider was used. |
