# IPHS 400 MP2 Report: A CMS for the Kenyon College Finance Club

**Aishik Biswas · October 15, 2026**  
**Repository:** [GitHub](https://github.com/iaishikb-rgb/iphs400-mp2-cms) · **Live site:** [Finance Club CMS](https://iaishikb-rgb.github.io/iphs400-mp2-cms/)

## 1. What I built, and which decisions were mine

I built a small CMS for the Kenyon College Finance Club, which I run alongside my two co-presidents, Lucas Flynn and Madeline Ha. Our current Wix website does not adequately represent the club’s activities. It lists no current officers or meeting times, its “Contact Us” link leads back to the homepage, and a Wix advertising banner appears across the top. For an alumnus visiting the website, this could suggest that the club is no longer active. Most of our information is communicated through club emails, which means members often have to search earlier messages for basic details, including our meetings every other week in Oden 110.

The CMS provides a local admin console built with FastAPI and SQLite, where Presidents and Officers can sign in, write Posts and Pages in Markdown, and preview their work. The `cms publish` command generates a static site from Live content for publication on GitHub Pages. Presidents have administrator access, while Officers have editor access. The implementation covers all seven required capabilities, with 123 tests in the final suite.

Several decisions emerged from my responses to the grill, particularly where I changed or rejected Claude’s recommendations:

- **No required password change at first sign-in.** Claude proposed this additional step, but I decided it was unnecessary for our setup. There are approximately eight officers, and a President sets each password face to face. Given the deadline, I did not think another screen was justified. I retained a two-hour idle sign-out because we share a laptop during meetings.
- **Only Presidents can publish.** Officers can prepare drafts, but publication requires a President. In the spring, our three sector teams present stock pitches to Kenyon alumni working at William Blair. Material published under the club’s name should therefore be complete and reviewed.
- **Only Presidents can manage Pages.** This decision came directly from my sixth WordPress field note, where I found that an Editor could move the About page to the trash. Officers contributing announcements should not also have control over official pages such as Leadership and the Analyst Program.
- **Publishing uses a simple confirmation.** Claude suggested displaying a summary of changes before every publish run. I chose a straightforward “Publish this?” confirmation, with the option to unpublish content and run the command again if a correction is needed.
- **Pitch writeups credit teams in the body text.** I decided against adding a separate team field. The byline identifies whoever posted the writeup, while the text credits the members who contributed.
- **The next meeting appears as a manually edited line on the Homepage.** I chose this over automatic date logic because one of us already updates the email reminder before each meeting. Updating the website can follow the same routine.

## 2. Where the AI drifted, and what caught it

The clearest problem was an explicitly requested fix that Claude reported as complete without resolving it. In my T07 prompt, I explained that `scripts/seed_demo.py` would not run with a fresh `.env` file and displayed “Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env.” I asked Claude to fix the issue and add a test. It subsequently reported T07 as complete, with all 111 tests passing.

However, when I ran the seed script myself at approximately 12:20 a.m., it produced the same error and exited, preventing the server from starting. None of the unit tests actually ran the script, which explains why the suite passed. I discovered the problem while manually trying to use the app. I then opened bug issue #9 and addressed it with a test that runs the seed script as a subprocess using a fresh copy of `.env.example`.

Other departures from the specification were identified through `/code-review`:

- **T01: conflicting glossary files.** The installed skills were newer than those described in the manual and expected a `GLOSSARY.md` file. Although I had already specified in `CLAUDE.md` that the glossary belonged in `CONTEXT.md`, an empty `GLOSSARY.md` and a reference to it in `docs/agents/domain.md` still appeared. The review identified this contradiction, which I corrected in commit `1557b24`. Leaving it unresolved could have caused later tickets to rely on different sources for the project’s vocabulary.
- **T06: President self-demotion.** The initial user management implementation allowed a President to demote themselves, despite the specification prohibiting this. With three co-presidents managing accounts, this seemed like a plausible mistake during the spring leadership transition. The review caught it before the commit.
- **T05: an addition I retained.** Claude included Pages in the dashboard counts even though the ticket did not request this. I kept the addition because it helps the Presidents identify unpublished pages.

## 3. Skills, prompts, and resources

I followed the sequence `/grill-with-docs`, `/to-spec`, and `/to-tickets`, which produced seven tickets corresponding to issues #2–#8. I then used `/implement` for each ticket, which invoked `/tdd`, followed by `/code-review`.

The grill was the most useful part of the process. Its 18 questions required me to make specific decisions about how the CMS should serve the club, including the choices described above. The review stage was also valuable because it identified problems in work that `/implement` had already reported as finished.

One source of confusion was the difference between ticket labels and GitHub issue numbers. Since the specification occupied issue #1, tickets T01–T07 corresponded to issues #2–#8. When I first entered `/implement #3`, Claude asked whether I meant T02 or T03. After that, I included both identifiers, such as `/implement #4 (T03)`.

I also used WordPress Playground for the field trip, the manual and rubric in the starter repository, and the club’s existing Wix website for background information. Since I had not used Orca or this workflow before, I kept a separate Claude conversation open for guidance on terminal commands and Git steps.

## 4. Budget, next steps, and reflections

The following figures come from `notes/usage-ledger.csv`, processed through `scripts/usage_report.py`.

| Stage | Planned usage | Actual usage |
| --- | --- | --- |
| Grill, specification, and tickets | 35% of a five-hour window using opusplan | 3% using Sonnet |
| Implementation and review per ticket | Approximately 20% | 1–7%, averaging approximately 3% |
| All seven tickets | Approximately 140% | 22% |
| Weekly cap | Estimated at 25–35% | Approximately 5% |

My estimate for the seven tickets was roughly six times the recorded usage. Switching the planning stages from opusplan to Sonnet and using `/clear` between tickets likely contributed to the lower usage. T01 was the most expensive ticket at 7% across 18 turns, since it established authentication, CSRF protection, and test helpers reused throughout the project.

These figures have limited precision. The meter records whole percentage points at the end of each turn, so the specification and ticket-generation stages appear as 0%. Those entries should not be read as evidence that the stages used no resources.

My next priorities would be to add a direct link to our resume-review form on the Join page, which currently directs students to financeclub@kenyon.edu; introduce sector tags so members can browse pitch writeups by team; and refactor the deliberately duplicated Post and Page code.

The main change I would make to my process is to begin earlier and check the app more regularly. The grill started at approximately 10:30 p.m. on October 14, and most implementation took place after midnight. I did not manually test the app until after T06, allowing the seed problem to remain unresolved longer than it should have. I also had not configured my laptop’s Git identity, so early commits display “Your Full Name”; `.mailmap` corrects how that authorship is displayed.

The seed failure made the limits of automated verification particularly clear to me. A passing suite establishes that the tested behavior works, but it can leave an essential part of the user’s experience unexamined. In a future project, I would use the app after each ticket and check that the completed work functions as expected.