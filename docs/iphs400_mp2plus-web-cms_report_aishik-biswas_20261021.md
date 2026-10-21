# IPHS 400 MP2plus Report: Kenyon College Finance Club CMS

Aishik Biswas · October 21, 2026 · MP2plus extension of the Kenyon College Finance Club CMS (F2, P1, S2, P3, P4).

## Evidence

| Id | Evidence |
|----|----------|
| F2 | issue #11; tests/test_taxonomy.py; mp2plus-categories-1280.png, mp2plus-categories-390.png |
| P1 | PR #12 closing issue #11; carries F2 |
| S2 | tests/test_login_hardening.py; fixture reset_login_limiter in tests/conftest.py |
| P3 | CONTEXT.md Decisions table; docs/adr/ADR-003-public-url-scheme.md |
| P4 | before: commit eb10c3a; after: the commit "P4: after" that adds the P4 section; see the P4 section |

## Left broken or worth knowing

- **F2:** Category and tag names with no ASCII letters or digits (for example, non-Latin scripts) get no page of their own, because the slug function keeps only `a-z0-9`.
- **P1:** The PR (#12) carried F2 only, no MP2 repair, and its body is just `Closes #11`.
- **S2:** Giving a wrong password and an unknown email the same message already worked from MP2 T01, so that test only pins existing behaviour and the per-account rate limiter (5 failures in 15 minutes, then 429) is the only new work.
- **P3:** ADR-003 records the public URL scheme; the Decisions table in CONTEXT.md holds the other decisions.
- **P4:** The "after" commit does not exist yet, so the row names it by message instead of by sha.

## P4

Command: uv run python scripts/usage_report.py --remaining 1 (no exercises are actually left; 1 makes the script print a forecast line)
Tickets done: 8 · average weekly cost per ticket: 0.6%
Forecast: 1 tickets need ~1% of the weekly cap; 91% remains → FITS

| Phase | Turns | 5h spent | Weekly |
|---|---|---|---|
| T11 (F2, shipped through P1) | 7 | 6.0% | 2.0% |
| TN (start of the F2 session, before I fixed the phase label) | 1 | 0.0% | 0.0% |
| S2 | 2 | 0.0% | 1.0% |
| P3 | 1 | 0.0% | 0.0% |
| P4 | 1 | 0.0% | 0.0% |

My "before" forecast assumed about 0.5% of the weekly cap per exercise (4 tickets for ~2%), but F2 alone (phase T11) cost 2.0% weekly and 6.0% of a 5-hour window, about four times the forecast. F2 was much bigger than an average MP2 ticket: a schema change, two new kinds of published pages and over 20 new tests, plus the pull request added a second /code-review round, a fix commit, and a Playwright screenshot run that downloaded Chromium inside the session. S2, P3 and P4 barely registered (0–1%), because the meter only records whole percentages and usage_report.py misses each session's first turn, so small sessions round down to zero.