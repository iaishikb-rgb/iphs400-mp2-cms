# CONTEXT.md glossary

Project vocabulary for the Kenyon College Finance Club (KCFC) website. One word per concept; if a better word appears, change it here.

## People and roles

**President**: One of the three students who run KCFC. Every President holds the Admin role.

**Officer**: A club member other than a President who helps run the club. Every Officer holds the Editor role while in office.

**Admin**: The role held by the three Presidents. Can create, edit, publish and delete Posts and Pages, and manage Users.

**Editor**: The role held by Officers. Can create and edit Posts and save them as Drafts. Cannot publish, cannot delete a published Post, cannot touch Pages, and cannot see User management. An Editor sees and edits only their own Posts, so a sector team's writeup changes only through its own author until a President reviews it. Admins see and edit every Post.

**User**: Anyone with an individual account on the admin console. Only Presidents and Officers are Users. Never shared between people.

**Visitor**: Anyone reading the public site: prospective members, current members, alumni, recruiters. Visitors never log in, and everything on the public site is visible to all of them. There is no members-only content.

**Sign-in**: A User signs in with their Kenyon email address and a password. A President creates the account and sets the first password face to face; there is no forced change at first sign-in. A lost password is reset by an Admin in person, never by email.

**Idle sign-out**: A User is signed out automatically after about 2 hours without activity, because the Club laptop is shared at meetings.

**Display name**: The name a User is known by publicly, e.g. "Kim Lee". A President sets it when creating the User and can edit it later. It is the only name used in a Byline; the email address is never shown.

**Deactivated**: A User switched off by an Admin when their time in office ends. They can no longer sign in, and any open session ends at their next action. Their Posts keep their name as author. An Admin can reactivate them. Users are never deleted. At least one President must always stay active, and a President cannot deactivate themselves.

## Content

**Post**: The one kind of dated club material: a meeting announcement, a pitch writeup, or an alumni call recap. There is a single kind of Post; it can carry one Category and any number of Tags.

**Category**: One optional label on a Post, a single free-text field, e.g. "Pitches" or "Recaps". Names that differ only in case or punctuation are the same Category (the newest Post's spelling names the page), and a name is cut at 60 characters. A name with no ASCII letters or digits stays on the Post but gets no page. Pages have no Category. Added by MP2plus F2, so the earlier "no categories" decision no longer holds.

**Tag**: A free-text label on a Post; a Post's Tags are one comma-separated field, with blanks and repeats dropped. Same matching rule as a Category.

**Category page / Tag page**: The public list of Published Posts with one Category or Tag, at `category/<slug>.html` or `tag/<slug>.html`, written by the Publish run (title and date, newest first). A Category or Tag used only by Drafts has no page, so nothing about a Draft reaches the public site. Each Published Post links to its own Category page and Tag pages.

**Pitch writeup**: A Post presenting a stock pitch. Spring pitches are group work by sector teams, so the team members are listed in the body text. It stays a Draft until a President has reviewed it.

**Sector team**: One of the three groups in the spring stock pitch competition, each covering a sector and led by one President. Teams present to Kenyon alumni working in equity research at William Blair.

**Analyst Program**: The club's program for newer members. Its lasting description is an Admin-only Page.

**Page**: Lasting club information: About, Leadership, Analyst Program, Join, Recruiting. Only Admins may create, edit or delete a Page; Editors cannot touch them at all.

**Join Page**: The Page for prospective members: what the club does, whether prior experience is needed, how to come to a meeting.

**Recruiting Page**: The Page for current members: the resume review form link and standing guides. Kept separate from the Join Page (one Page, one audience).

**Homepage**: A Page edited by Admins, found by its slug `homepage`, which never changes (do not edit it). The next meeting (every other week, Oden 110) is the first thing a Visitor sees, followed by the contact email and the latest Posts.

**Next-meeting line**: Plain text at the top of the Homepage, e.g. "Next meeting: Wed Oct 28, 7 pm, Oden 110". A President updates it the night before each meeting, the same habit as the email reminder. There is no calendar or automatic date logic.

**Navigation**: The public menu. It lists Published Pages in an order an Admin sets, plus a link to the Posts listing.

**Byline**: The public line on a Post, "By <name>, <date>", naming whoever posted it, never an email address. A Deactivated User's name still shows on their old Posts. Pages show no byline. Group work (such as the spring pitches by three sector teams, each led by a President) has no team field: the poster is the byline and the team members are listed in the body text.

**Posts listing**: The public list of Published Posts, newest first, showing title and date.

**Title convention**: A club habit, not enforced by the system: Post titles for pitches and recaps start with "Pitch:" or "Recap:" (e.g. "Pitch: NVDA, Spring 2026") so the Posts listing is scannable. Admins hand-link standout archive Posts from the Recruiting Page.

**Event**: Not a separate thing. An event is announced in a Post.

**Slug**: The short address-name of a Post or Page (e.g. `spring-stock-pitch`). Made from the title once, when first saved, and unchanged when the title is edited. Only an Admin can edit it; an old slug is not redirected.

**Public paths**: Pages are published at `<slug>.html` and Posts at `posts/<slug>.html`, so a Post slug and a Page slug can never collide. The slug `index` is reserved. Category pages are `category/<slug>.html` and Tag pages `tag/<slug>.html`.

**Unpublish**: An Admin returns a Published Post or Page to Draft. It leaves the public site at the next Publish run but is kept.

**Delete**: Permanent removal of a Post or Page, after an "are you sure?" step. Only an Admin can delete a Published Post or any Page; an Editor can delete only their own Drafts. Users are never deleted, only Deactivated (for example when seniors graduate in May: their old Posts keep their name, but they cannot log in).

**Draft**: A Post that has been saved but not published. Visible only to signed-in Users, never on the public site. A Published Post returns to Draft when an Editor edits it, and stays out of the public site until an Admin publishes it again. An Admin's edit leaves it Published.

**Published**: The status of a Post or Page that an Admin has approved for the public site. Approved is not the same as Live.

**Publish run**: Running `cms publish`, which only an Admin does, usually right before a meeting. It rebuilds the public site from everything Published and deploys it, with no change summary. Marking an item Published has a simple "Publish this?" confirm on the button. A mistake is fixed by unpublishing it and running it again.

**Live**: On the public site as of the last Publish run. A Published item becomes Live only at the next Publish run.

**Pending changes**: Changes made since the last Publish run, which the console shows in a banner so nobody assumes saved work is already Live.

**Dashboard**: The console's first screen. Shows counts of Drafts, Published items and Pending changes (Admins also see active and Deactivated Users), and a one-click "New Post" button.

**Content list**: The console's list of Posts and Pages, newest first, filterable by status (with counts), type and Category (a Category filter shows Posts only). Editors see Posts only.

**Preview**: The editor's side-by-side view of how the sanitized Markdown will look on the public site, labelled "Draft, not Live" when it is not.

**Club laptop**: The one computer that runs the admin console. The console is never on the public internet; Officers sign in on it with their own accounts.

## Out of scope

Comments, image uploads, scheduled posts, email newsletters, member logins.
