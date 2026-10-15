# IPHS 400 — Mini-Project #2 starter (Web CMS)

Click **Use this template** → name your repo **`iphs400-mp2-cms`** → make it **Public**.
Do not fork: a fork arrives without an Issues tab, and your tickets live in Issues.

## Start here

1. `docs/manual_iphs400_mp2-web-cms_20260922.md` — the manual. Read Part 0 and Part 1 first.
2. `docs/mp2-grading-rubric_20260922.md` — how you are graded. Read it **before** you build or revise.
3. `docs/mp2-setup_context-threshold-hook_20260922.md` — Exercise A, in Part 4 of the manual.

## Live URL

https://iaishikb-rgb.github.io/iphs400-mp2-cms/ — the Kenyon College Finance Club public site, served from the `gh-pages` branch.

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

## What is here

```text
.claude/hooks/     the context meter and usage ledger (Exercise A lives in ctx_guard.py)
scripts/           usage_report.py (Exercise B lives in spend()), check_submission.py, seed_demo.py
tests/             the exercise tests, plus helpers such as client_as("editor")
app/, templates/   the T00 skeleton — every CMS feature is yours to build
docs/adr/          two example decision records
```

Two functions are deliberately unfinished and their tests fail until you write them:
`decide()` in `.claude/hooks/ctx_guard.py` and `spend()` in `scripts/usage_report.py`.
Both are graded in Stage 2. Use `/tdd`, as the manual says.

## Deadlines

Stage 1 (`mp2-mvp` tag): Tue Sep 29, 2:40 pm Eastern. A preliminary checkpoint, past and ungraded; its 15 points are credited for the tag.
Stage 2 (`mp2-final` tag): the final, graded submission, due Thu Oct 15, 2:40 pm Eastern, grace until Fri Oct 16, 2:40 pm. The first round (due Oct 6) was graded and returned on Oct 8; the deadline was extended so you can revise after feedback, and one revised `mp2-final` by Oct 15 replaces the earlier grade.
MP2plus (optional extra credit): assigned Sun Oct 11, due Tue Oct 20, 2:40 pm Eastern, grace until Wed Oct 21, 2:40 pm. Each exercise is worth 5–10 points, added to your MP2 grade, up to +30.
MP2 is graded as a score out of 100, scaled to 5% of the course grade.

Run `uv run python scripts/check_submission.py --stage 2` before you submit.

## Generative AI Use Statement

## Generative AI Use Statement

I built this project using Claude Code inside Orca, with `--dangerously-skip-permissions`, following the setup we used in class. Claude wrote nearly all of the code. My role was to determine what the club needed, respond to the questions raised during the grill, read the tests and reviews, and identify where the implementation fell short.

**Models.** I used Claude Sonnet for most of the project, including the grill, specification, ticket generation, implementation of all seven tickets, and reviews. One early setup session used Haiku because I had not noticed which model was selected. Although my budget plan originally called for opusplan during the planning stages, I switched the grill to Sonnet on the night of October 14 because I was concerned about reaching my five-hour usage limit before beginning implementation.

**Skills.** I used the mattpocock skills: `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`, which invoked `/tdd`, and `/code-review`. I also used `/ask-matt` once to check the workflow. Alongside these, I used the course hooks for the context meter, usage ledger, and transcript saver.

**Two prompts I sent**

1. To begin the grill:

   > /grill-with-docs I am building a small CMS for the Kenyon College Finance Club, which my two co-presidents and I run. My field notes are in notes/cms-field-notes.md and my client brief is in notes/client-brief.md. The 7 required capabilities are in docs/manual_iphs400_mp2-web-cms_20260922.md, Part 3.3. Help me decide what they mean for this club. Write the glossary to CONTEXT.md. Ask one question at a time.

2. In response to the grill’s proposed sign-in process, at question 14:

   > Partly. Yes to signing in with a Kenyon email plus password, and yes to admin-assisted resets. We'd do that in person at a board meeting in Oden anyway. But no forced password change at first sign-in: there are only ~8 officers, a president sets the password face to face, and I'd rather not build an extra screen with the deadline this week. Keep a simple idle sign-out, about 2 hours, because we do share a laptop at meetings.

**A model failure.** In my T07 prompt, I explicitly told Claude that `seed_demo.py` would not run with a fresh `.env` file. It displayed the message “Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env,” and I asked Claude to fix the problem and add a test. Claude subsequently reported that T07 was complete, with all 111 tests passing. However, when I ran the seed script myself, it produced the same error and exited, leaving the server unable to start.

None of the tests actually ran the seed script, which explains why they passed despite the unresolved problem. I opened bug issue #9 and addressed it in a separate session, this time adding a test that runs the seed script as a subprocess using a fresh copy of `.env.example`. This made me more aware of the limits of a passing test suite: it only establishes that the behavior covered by those tests works. Going forward, I should also use the app myself after each ticket, instead of waiting until the end.

**Other issues caught during review.** The `/code-review` skill identified a separate `GLOSSARY.md` created during T01, despite my requirement that the glossary belong in `CONTEXT.md`. It also caught a problem in T06: the initial user management implementation allowed a President to demote themselves, which the specification explicitly prohibited.

**Authorship note.** Commits made before October 15 display the placeholder author “Your Full Name” because I had not configured my Git identity on this laptop. The `.mailmap` file maps those commits to me. Every commit in this repository is mine.

I drafted this statement with Claude’s help and then edited and rephrased it.

### Development backends used

| Provider | Models | Use |
| --- | --- | --- |
| Anthropic (Claude Pro) | Sonnet, Haiku | All project development. No backup provider was used. |
