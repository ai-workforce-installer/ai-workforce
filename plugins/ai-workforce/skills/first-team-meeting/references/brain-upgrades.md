# Business Brain upgrades (safe, repeatable, add-only)

Plugin updates change how the team works. They never change the owner's Business Brain on their own. When a newer plugin needs something new in the Business Brain, it is added by these steps, with the owner's yes.

## When to upgrade
Workforce Settings ends with an **About this workspace** section holding `- Business Brain version: <x.y.z>`. A missing section means version 0.3 or older, or a setup that didn't finish; "setup in progress" means setup didn't finish. In every one of these cases, run every upgrade section below in order (each skips what's already there), skipping their version-line steps, then the structure check, which sets the version line at the end.
- **Attended:** if the version is older than the latest below, say once, in one line: "I have a few improvements for your team's workspace in Notion. Nothing you've written changes. Add them now?" On yes, run the steps. On no, don't ask again in this conversation.
- **Newer than this file knows** (the workspace was upgraded by a newer copy of the plugin, for example on another device): change nothing and carry on. In attended mode, mention once that their AI Workforce may be out of date and they can update it from Customize → Plugins.
- **Scheduled:** never upgrade. Add one line to the briefing: "Workspace improvements are ready. Say 'update my team workspace' when you have a minute."
- `setup-workforce` offers it the same way when it finds an existing Business Brain.
- **After a plugin update,** recurring tasks need nothing: each one follows the installed plugin on its next run. If the owner has both a daily briefing task and a separate inbox triage task, offer once to combine them (`schedule-workforce`, "One morning run"). Change nothing without a yes.

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

## Upgrade to 0.4.0
1. **Your Team page.** If the Business Brain has no child page titled "Your Team", create it (icon 👥) from the Your Team template.
2. **Work to hand off.** If Priorities has no "Work I'd like to hand off" heading, append that section from the Priorities template at the end of the page.
3. **Handed to you.** If the Approvals Status property has no "Handed to you" option, add it (blue), keeping every existing option.
4. **Version line.** If Workforce Settings has no "About this workspace" heading, append it from the Workforce Settings template; otherwise replace the existing `Business Brain version` line. It ends as `- Business Brain version: 0.4.0`.

## Upgrade to 0.5.0 (run tracking fields; runs work without them)
1. **Briefings properties.** Add any that are missing: `Run ID` (text), `Started`, `Finished` and `Completed through` (dates).
2. **Options.** Add `Unknown` (gray) to Run type in Briefings and in Assignments, and `Running` (blue) to Briefings' Result, if missing, sending every existing option with them.
3. **Version line:** `- Business Brain version: 0.5.0`.

## Upgrade to 0.5.1 (open work in Assignments; runs work without it)
1. **Assignments options.** Add `Prepared` (purple), `Handed to you` (orange) and `Blocked` (brown) to Status if missing, sending every existing option with them.
2. **Assignments properties.** Add `Source` (text) and `Next action` (text) if missing.
3. **Version line:** `- Business Brain version: 0.5.1`.

## Upgrade to 0.5.2 (saved views, which keep working on Notion's free plan when its query allowance runs out)
1. Fetch each database to see its views. For each view below that **doesn't exist yet by that name**, create it as a table view with the notion-create-view tool (`database_id` = the database, `data_source_id` = its collection, `configure` = the line below). If one with that name exists, leave it as it is, even if its filter differs (runs check a view's filter before using it). After creating, fetch the database again and check each new view is there with that filter and sort.
   - Approvals → "Active approvals": `FILTER "Status" IN ("Pending", "Approved", "Handed to you"); SORT BY "AP" ASC`. On a workspace without the "Handed to you" option, leave that value out.
   - Assignments → "Open work": `FILTER "Status" IN ("Planned", "In progress", "Prepared", "Handed to you", "Blocked"); SORT BY "Date" ASC`, leaving out options the database doesn't have.
   - Briefings → "Newest first": `SORT BY "Date" DESC` (only if missing).
   - Pricing & Offers → "Active offers": `FILTER "Active" = TRUE; SORT BY "Offer" ASC`.
   - Customers & Leads → "All contacts": `SORT BY "Last contact" DESC`.
2. **Version line.** Only when every view above exists (created now or already there), set `- Business Brain version: 0.5.2`. If any step failed, leave the version line as it was, say which step failed, and the upgrade can simply be run again.

## Upgrade to 0.6.0 (a place for the owner's corrections, `references/owner-corrections.md`)
1. **Priorities sections.** Fetch Priorities. If it has no "Always worth my attention" heading, append that section from the Priorities template at the end of the page. Then, if it has no "Not my responsibility anymore" heading, append that section the same way.
2. **Version line.** Only when both headings are there, set `- Business Brain version: 0.6.0`. If Priorities couldn't be read or written, leave the version line as it was and say which step didn't finish.

## Upgrade to 1.0.0 (open work tracked to a verified outcome)
Nothing existing changes: no status option, view, row or schedule is touched, and runs work without these fields (they keep the same facts in each row's text). Every step adds only what is missing, so an interrupted upgrade simply carries on when it is run again.
1. **Assignments properties.** Fetch the Assignments data source and add each of these that is missing, checking it is there before the next: `Work type` (select: Task, Reply, Commitment, Waiting on someone, Customer case, Deliverable, Monitored issue), `Due` and `Next check` (dates), `Waiting on`, `Blocker`, `Done when` and `Work key` (text), `Evidence` (URL), `Closed as` (select: Completed, Sent, Cancelled, Dismissed, Superseded, Unverified). A property of the owner's with one of these names stays as it is: say so once.
2. **Workforce Settings.** Under Connections, add `- Sending: _not set_` if there is no Sending line. Existing owners keep things as they were (replies left for them to send) until they answer the desk's one question.
3. **Version line.** Only when all nine fields and that line are there, set `- Business Brain version: 1.0.0`. Otherwise leave the line as it was and say what is still to add.

Later versions add their own section here, below this one, and run in order.

**No longer used.** Workspaces set up before 0.8.0 may have a `Recurring tasks update themselves` line under Schedule. Recurring tasks no longer change their own instructions, so the line means nothing now: leave it where it is, never add it, and ignore what it says.
