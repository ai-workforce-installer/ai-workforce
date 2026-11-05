# Business Brain upgrades (safe, repeatable, add-only)

Plugin updates change how the team works. They never change the owner's Business Brain on their own. When a newer plugin needs something new in the Business Brain, it is added by these steps, with the owner's yes.

## When to upgrade
Workforce Settings ends with an **About this workspace** section holding `- Business Brain version: <x.y.z>`. A missing section means version 0.3 or older.
- **Attended:** if the version is older than the latest below, say once, in one line: "I have a few improvements for your team's workspace in Notion. Nothing you've written changes. Add them now?" On yes, run the steps. On no, don't ask again in this conversation.
- **Newer than this file knows** (the workspace was upgraded by a newer copy of the plugin, for example on another device): change nothing and carry on. In attended mode, mention once that their AI Workforce may be out of date and they can update it from Customize → Plugins.
- **Scheduled:** never upgrade. Add one line to the briefing: "Workspace improvements are ready. Say 'update my team workspace' when you have a minute."
- `setup-workforce` offers it the same way when it finds an existing Business Brain.
- **After an attended upgrade** (or whenever the owner mentions updating the plugin), also offer to check their recurring tasks: "Your recurring tasks may still use older instructions. Want me to check them?" (`schedule-workforce`, "Check and update recurring responsibilities"). Change nothing without a yes.

## Rules
- **Check, then add.** Every step first checks whether its change is already there and skips it if so. Running the steps twice changes nothing.
- **Add only.** Never delete, rename, reorder or rewrite anything the owner or the team wrote. Never change an existing select option; only add new ones. (The only renames anywhere in the plugin: the two v0.1 archive pages in `references/notion-schema.md`, and naming a copied template "Business Brain" during setup, each with the owner's yes.)
- **Select options:** fetch the database schema first and send **every existing option** (including any the owner added) plus the new one, because a select update removes any option it doesn't list.
- **Version line last.** Update it only after every step succeeded, so a half-finished upgrade runs again next time.
- If a step fails, stop, keep the old version line, and tell the owner which step didn't finish.
- Templates for new pages and sections are in `references/page-templates.md`.

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

Later versions add their own section here, below this one, and run in order.
