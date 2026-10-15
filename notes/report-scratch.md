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
