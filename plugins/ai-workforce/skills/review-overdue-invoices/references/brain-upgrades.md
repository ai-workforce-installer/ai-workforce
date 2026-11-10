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
4. **Version line.** If Workforce Settings has no "About this workspace" heading, append it from the Workforce Settings template. Otherwise replace the existing `Business Brain version` line. Either way it ends as `- Business Brain version: 0.4.0` (then continue with 0.5.0).

## Upgrade to 0.5.0
Adds run tracking fields so the team can tell retries from new runs and keep its inbox bookmark. Nothing existing changes; runs work without these fields too (they keep the same information in each record's text).
1. **Briefings properties.** Fetch the Briefings data source. Add any that are missing: `Run ID` (text), `Started` (date), `Finished` (date), `Completed through` (date).
2. **Briefings options.** Add `Unknown` (gray) to Run type and `Running` (blue) to Result if missing, sending every existing option with them.
3. **Assignments option.** Add `Unknown` (gray) to its Run type if missing, sending every existing option with it.
4. **Version line.** Replace the `Business Brain version` line with `- Business Brain version: 0.5.0`.

## Upgrade to 0.5.1
Lets the Assignments database hold the team's open work so nothing found is forgotten between runs. Nothing existing changes; runs work without it (they keep the same details in each row's text). Safe to repeat: each step only adds what's missing.
1. **Assignments options.** Add `Prepared` (purple), `Handed to you` (orange) and `Blocked` (brown) to Status if missing, sending every existing option with them.
2. **Assignments properties.** Add `Source` (text) and `Next action` (text) if missing.
3. **Version line.** Replace the `Business Brain version` line with `- Business Brain version: 0.5.1`.

## Upgrade to 0.5.2
Adds saved views, which keep working on Notion's free plan after its query allowance runs out. Nothing existing changes: no records are edited and no existing view is changed. Safe to repeat.
1. Fetch each database to see its views. For each view below that **doesn't exist yet by that name**, create it as a table view with the notion-create-view tool (`database_id` = the database, `data_source_id` = its collection, `configure` = the line below). If one with that name exists, leave it as it is, even if its filter differs (runs check a view's filter before using it). After creating, fetch the database again and check each new view is there with that filter and sort.
   - Approvals → "Active approvals": `FILTER "Status" IN ("Pending", "Approved", "Handed to you"); SORT BY "AP" ASC`. On a workspace without the "Handed to you" option, leave that value out.
   - Assignments → "Open work": `FILTER "Status" IN ("Planned", "In progress", "Prepared", "Handed to you", "Blocked"); SORT BY "Date" ASC`, leaving out options the database doesn't have.
   - Briefings → "Newest first": `SORT BY "Date" DESC` (only if missing).
   - Pricing & Offers → "Active offers": `FILTER "Active" = TRUE; SORT BY "Offer" ASC`.
   - Customers & Leads → "All contacts": `SORT BY "Last contact" DESC`.
2. **Version line.** Only when every view above exists (created now or already there), replace the `Business Brain version` line with `- Business Brain version: 0.5.2`. If any step failed (a view couldn't be created, the database couldn't be read), leave the version line as it was, say which step failed, and the upgrade can simply be run again.

## Upgrade to 0.6.0
Gives the team a place to keep the owner's corrections about what matters, so they apply to every later run (`references/owner-corrections.md`). Nothing existing changes and no records are edited; runs work without it (corrections go under "Things to ignore for now" until then). Safe to repeat: each step only adds what's missing.
1. **Priorities sections.** Fetch Priorities. If it has no "Always worth my attention" heading, append that section from the Priorities template at the end of the page. Then, if it has no "Not my responsibility anymore" heading, append that section the same way.
2. **Version line.** Only when both headings are there, replace the `Business Brain version` line with `- Business Brain version: 0.6.0`. If Priorities couldn't be read or written, leave the version line as it was and say which step didn't finish.

Later versions add their own section here, below this one, and run in order.

**No longer used.** Workspaces set up before 0.8.0 may have a `Recurring tasks update themselves` line under Schedule. Recurring tasks no longer change their own instructions, so the line means nothing now: leave it where it is, never add it, and ignore what it says.
