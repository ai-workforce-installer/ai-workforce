# Business Brain upgrades (safe, repeatable, add-only)

Plugin updates never change the owner's Business Brain on their own. What a newer plugin needs there is added by these steps, with the owner's yes.

## When to upgrade
Workforce Settings ends with an **About this workspace** section holding `- Business Brain version: <x.y.z>`. A missing section means version 0.3 or older, or a setup that didn't finish; "setup in progress" means setup didn't finish. In every one of these cases, run every upgrade section below in order (each skips what's already there), skipping their version-line steps, then the structure check, which sets the version line at the end.
- **Attended:** if the version is older than the latest below, say once, in one line: "I have a few improvements for your team's workspace in Notion. Nothing you've written changes. Add them now?" On yes, run the steps. On no, don't ask again in this conversation.
- **Newer than this file knows** (the workspace was upgraded by a newer copy of the plugin, for example on another device): change nothing and carry on. In attended mode, mention once that their AI Workforce may be out of date and they can update it from Customize → Plugins.
- **Scheduled:** never upgrade. Add one line to the briefing: "Workspace improvements are ready. Say 'update my team workspace' when you have a minute."
- `setup-workforce` offers it the same way when it finds an existing Business Brain.
- **After a plugin update,** recurring tasks need nothing: each follows the installed plugin on its next run.

## Rules
- **Check, then add.** Every step first checks whether its change is already there and skips it if so. Running the steps twice changes nothing.
- **Add only.** Never delete, rename, reorder or rewrite anything the owner or the team wrote. Never change an existing select option; only add new ones. (The only renames anywhere in the plugin: the two v0.1 archive pages in `references/notion-schema.md`, naming a copied template "Business Brain" during setup, and, when the owner chooses a fresh start over an existing Business Brain during setup, renaming the old one "Business Brain (archive <date>)"; each only with the owner's yes.)
- **Select options:** fetch the database schema first and send **every existing option** (including any the owner added) plus the new one, because a select update removes any option it doesn't list.
- **Version line last.** Update it only after every step succeeded, so a half-finished upgrade runs again next time.
- If a step fails, stop, keep the old version line, and tell the owner which step didn't finish.
- Templates for new pages and sections are in `references/page-templates.md`.

## Structure check and repair (setup, and every "update my team workspace")
Runs after any upgrade sections that are due (the version line reaches the latest version only here, at the end), and runs whatever the version line says, so a workspace that was only partly created, or lost a piece, gets repaired. Add-only and safe to repeat.
1. Fetch the Business Brain root page and each database once.
2. Compare with `references/notion-schema.md`: the eight pages, the five databases, each database's properties and select options, and the views it lists; and the headings the upgrade sections add to existing pages (Priorities: "Work I'd like to hand off", "Always worth my attention", "Not my responsibility anymore", each appended from the Priorities template at the end of the page if missing). Add only what's missing, with the rules above (select options: send every existing option). Never create a second copy of anything that exists by that name.
3. **Views:** create a missing view by its name. If a view with that name exists but its filter or sort differs from the schema, leave it exactly as it is, tell the owner once ("Your 'Active offers' view has its own filter, so I left it alone; the team will read that list another way"), and don't count it as missing. Runs already check a view's filter before using it (`references/notion-access.md`).
4. Fetch again and confirm everything added is there.
5. **Version line:** only when nothing required is missing and every upgrade section that was due finished, set it to the latest version in this file (`- Business Brain version: <latest>`). If anything is still missing, keep the old line (or "setup in progress"), say exactly what's missing, and the owner can run it again.

A version line of "setup in progress", or a missing line, means the upgrades and the structure check haven't finished: offer them when attended, mention it once when scheduled.

## Upgrades before 1.0.0 (0.4.0, 0.5.0, 0.5.1, 0.5.2, 0.6.0)
Everything those versions added is in `references/notion-schema.md` and the page templates today, so the structure check above adds whatever an older workspace is missing and they have no steps of their own: the Your Team page and the About this workspace section; the Priorities headings; the Briefings run fields; the `Unknown`, `Running`, `Prepared`, `Handed to you` and `Blocked` options (every existing option sent with them); `Source` and `Next action` on Assignments; and the five saved views, which keep working on Notion's free plan when its query allowance runs out (Approvals "Active approvals", Assignments "Open work", Briefings "Newest first", Pricing & Offers "Active offers", Customers & Leads "All contacts"). A missing view is created as a table view with the notion-create-view tool (`database_id` = the database, `data_source_id` = its collection, `configure` = that view's line in the schema, leaving out of a filter any option the database doesn't have); then fetch the database again and check each new view is there with that filter and sort. Runs work without any of this.

## Upgrade to 1.0.0 (open work tracked to a verified outcome)
Nothing existing changes: no status option, view, row or schedule is touched, and runs work without these fields (they keep the same facts in each row's text). Every step adds only what is missing, so an interrupted upgrade simply carries on when it is run again.
1. **Assignments properties.** Fetch the Assignments data source and add each of these that is missing, checking it is there before the next: `Work type` (select: Task, Reply, Commitment, Waiting on someone, Customer case, Deliverable, Monitored issue), `Due` and `Next check` (dates), `Waiting on`, `Blocker`, `Done when` and `Work key` (text), `Evidence` (URL), `Closed as` (select: Completed, Sent, Cancelled, Dismissed, Superseded, Unverified). A property of the owner's with one of these names stays as it is: say so once.
2. **Workforce Settings.** Under Connections, add `- Sending: _not set_` if there is no Sending line, and `- Work lives in: _not set_` if there is no such line. Existing owners keep things as they were (replies left for them to send) until they answer the desk's one question.
3. **Version line.** Only when all nine fields and both lines are there, set `- Business Brain version: 1.0.0`. Otherwise leave the line as it was and say what is still to add.

Later versions add their own section here, below this one, and run in order.

**No longer used.** Workspaces set up before 0.8.0 may have a `Recurring tasks update themselves` line under Schedule. Recurring tasks no longer change their own instructions, so the line means nothing now: leave it where it is, never add it, and ignore what it says.
