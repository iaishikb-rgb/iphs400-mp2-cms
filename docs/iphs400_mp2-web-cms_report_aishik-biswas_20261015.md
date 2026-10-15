# IPHS 400 MP2 Report: A CMS for the Kenyon College Finance Club

**Aishik Biswas · October 15, 2026**  
**Repository:** [GitHub](https://github.com/iaishikb-rgb/iphs400-mp2-cms) · **Live site:** [Finance Club CMS](https://iaishikb-rgb.github.io/iphs400-mp2-cms/)

## 1. What I built, and which decisions were mine

I built a small CMS for the Kenyon College Finance Club, which I run with my two co-presidents, Lucas Flynn and Madeline Ha. Our current Wix site doesn't represent the club well. It lists no officers or meeting times, its "Contact Us" link goes back to the homepage, and a Wix ad banner sits across the top. An alum landing on it could reasonably think we'd shut down. Most of our real information goes out in club emails, so members end up digging through old messages just to find out that we meet every other week in Oden 110.

The CMS has a local admin console built with FastAPI and SQLite. Presidents and Officers sign in there and write Posts and Pages in Markdown, with a preview next to the editor. `cms publish` turns the Live content into a static site on GitHub Pages. Presidents are admins; Officers are editors. All seven required capabilities work, and the suite has more than 120 tests.

These grill decisions were mine. In most of them I changed or rejected what Claude recommended:

- **No forced password change at first sign-in.** Claude proposed it. I said no: we have about eight officers, and a President sets each password face to face. Given the deadline, another screen wasn't worth it. I kept a two-hour idle sign-out, though, because we share a laptop at meetings.
- **Only Presidents publish.** Officers write drafts. In the spring our three sector teams pitch to Kenyon alumni at William Blair, and nothing half-finished should go out under the club's name.
- **Only Presidents manage Pages.** This came straight from my sixth WordPress field note, where an Editor could move the About page to the trash. An officer posting an announcement shouldn't be able to touch Leadership or the Analyst Program page.
- **A simple "Publish this?" confirm.** Claude wanted a summary of changes before every publish run. If something wrong goes out, we unpublish and run it again.
- **Teams are credited in the body text,** not in a separate team field. The byline is just whoever posted it.
- **The next meeting is a hand-edited line on the Homepage.** One of us already updates the email reminder the night before, so updating the site is the same habit.

## 2. Where the AI drifted, and what caught it

The clearest problem wasn't caught by any tool. I caught it by clicking through the app.

Around 12:10 a.m., after T06, I tried the app by hand for the first time. `scripts/seed_demo.py` refused to run on a fresh `.env` and printed "Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env", so the server never started. Every test was green, because none of them ran the seed script. I meant to fold the fix into T07 but left it out of the prompt, so the seed still failed after T07. I opened bug issue #9 and fixed it in its own session, with a test that runs the seed as a subprocess from a fresh copy of `.env.example`.

`/code-review` caught the actual drift from the spec:

- **T01: two glossary files.** The skills I installed were newer than the ones in the manual and expected a `GLOSSARY.md`. I had already written in `CLAUDE.md` that the glossary lives in `CONTEXT.md`, but an empty `GLOSSARY.md` and a reference to it in `docs/agents/domain.md` showed up anyway. The review flagged the contradiction, and I fixed it in `1557b24`. Left alone, later tickets could have pulled vocabulary from two different files.
- **T06: a President could demote themselves.** The spec forbids this. With three co-presidents, it's exactly the kind of mistake someone makes during the spring handover. The review caught it before the commit.
- **T05: an addition I kept.** Claude counted Pages on the dashboard even though the ticket didn't ask for it. I kept it, because we do want to see which pages are still unpublished.

## 3. Skills, prompts, and resources

The pipeline was `/grill-with-docs`, `/to-spec` and `/to-tickets`, which produced seven tickets (issues #2 to #8). Then `/implement` per ticket, which ran `/tdd`, and `/code-review` at the end of each one.

The grill was the most useful part. Its questions forced me to decide how the CMS should actually work for us, and every decision in section 1 came out of it. Review came second, because it kept finding problems in work that `/implement` had already called finished.

Before submitting, I also ran Claude as a mock grader, giving it the judge prompt from Part II of the rubric. It found things I had missed: the public site still said "Knox County Historical Society" from the template, there was no "Saved." message after forms, and two claims in my first draft of this report didn't match the transcripts. I fixed all of these.

Other resources: WordPress Playground for the field trip, the manual and rubric in the starter repo, and the club's Wix site for background. I had never used Orca or this workflow, so I kept a separate Claude conversation open to guide me through the terminal and Git steps.

## 4. Budget, next steps, and reflections

The figures come from `notes/usage-ledger.csv`.

| Stage | Planned | Actual |
| --- | --- | --- |
| Grill, spec and tickets | 35% of a five-hour window (opusplan) | about 3% (Sonnet) |
| Per ticket, implement and review | about 20% | 1–7% |
| All seven tickets | about 140% | about 34% |
| Weekly cap | 25–35% guessed | about 10% |

I overestimated by roughly four times. Switching the planning to Sonnet helped, and so did `/clear` between tickets, which kept every session small. T01 was the most expensive ticket (18 turns), because it built the auth, CSRF protection and test helpers that everything after it reused.

One caveat on the numbers: `usage_report.py` misses each session's first turn, so it reports 22% for the tickets. The raw five-hour meter went from 8% before T01 to 42% after T07, which is where the 34% comes from. The meter also only records whole percentages, which is why spec and tickets show 0%.

Next, I'd add a real link to our resume-review form on the Join page. Right now it tells students to email financeclub@kenyon.edu. After that, sector tags on pitch writeups, so new members can browse by team.

What I'd change about my process: start earlier, and use the app after every ticket. The grill started at about 10:30 p.m. on October 14, most of the building happened after midnight, and I didn't click through the app until after T06. That's how the seed bug lasted as long as it did. My laptop's Git identity also wasn't configured, so my early commits show "Your Full Name"; `.mailmap` maps them to me.
