# Report scratch notes

## Drift example (T01, issue #2)
- The mattpocock skills created a stray empty GLOSSARY.md and docs/agents/domain.md telling agents to use GLOSSARY.md, which contradicted my CLAUDE.md rule that the glossary is CONTEXT.md.
- Caught by /code-review on T01 (standards axis). Fixed in commit 1557b24; skill copies rewritten to say CONTEXT.md in a34b666.

## Deliberate test change (T01)
- tests/test_t00.py was edited so the test signs in first, because anonymous /admin now has to redirect to login.

## Decisions I made in review (T01)
- Accepted no @kenyon.edu email check: presidents create every account by hand.
- Secret key: review found it fell back to a forgeable default. Fixed so production refuses to start without a real key (1a3a0e0).

## Model use
- Planned opusplan for the grill but used Sonnet to save my 5h limit.

## T02 (issue #3)
- Review caught an information leak: an Officer got 404 for a missing Post but 403 for someone else's, so they could tell which Post IDs existed. Fixed: both are 403 for Officers.
- Two rules couldn't be tested yet (Officer edit reverts Published to Draft; only a President deletes a Published Post), so they were carried into T03.

## T02 (issue #3)
- Review caught an information leak: an Officer got 404 for a missing Post but 403 for someone else's, so they could tell which Post IDs existed. Fixed: both are 403 for Officers.
- Two rules couldn't be tested yet (Officer edit reverts Published to Draft; only a President deletes a Published Post), so they were carried into T03.

## T03 (issue #4)
- Review caught that title/body and slug saved in two separate transactions, so a failed slug write could leave a half-saved Post. Fixed to one transaction.
- I accepted that renaming a Live Post's slug breaks old links: that's in the spec. Presidents rarely rename, and we'd re-send the link in the club email anyway.

## T05 (issue #6)
- Drift: Claude added Pages to the dashboard counts without the ticket asking, justifying it from CONTEXT.md. I kept it because the presidents do want to see unpublished pages.
- Review caught a bad nav order ("abc" or a negative number) silently becoming 0. Now rejected with an error.

## T05 (issue #6)
- Drift: Claude added Pages to the dashboard counts without the ticket asking, justifying it from CONTEXT.md. I kept it because the presidents do want to see unpublished pages.
- Review caught a bad nav order ("abc" or a negative number) silently becoming 0. Now rejected with an error.

## T06 (issue #7)
- Drift caught by review: first version let a President demote themselves; the spec says they can't. Fixed before commit.
- Claude added an 8-character minimum password the ticket didn't ask for. Kept it.
- Gap found: users have no display name, so the public byline "By <name>" from the grill had nowhere to come from. Pushed into T07.

## T06 (issue #7)
- Drift caught by review: first version let a President demote themselves; the spec says they can't. Fixed before commit.
- Claude added an 8-character minimum password the ticket didn't ask for. Kept it.
- Gap found: users have no display name, so the public byline "By <name>" from the grill had nowhere to come from. Pushed into T07.
- Hand-testing after T06: seed_demo.py refused to run on fresh .env values, so the server never started. The unit tests never caught it because they don't run the seed script. Fixed in bug issue #9 (bbf1f5e).
