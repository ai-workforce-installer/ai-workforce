---
name: team-report
description: This skill should be used when the owner asks "what's my team been working on?", "what did the team do this week?", "did the morning briefing run?", "what's scheduled?", "is the team working?", "any problems?", or wants a truthful summary of the team's actual activity, results, failures and pending decisions.
metadata:
  version: "0.5.2"
---

# Team Report

_Files named `references/…` are in this skill's own folder._

A truthful account of what the team actually did. Every line rests on a record in the Business Brain or the list of scheduled tasks. Never fill a gap with what probably happened. Speak per `references/talking-to-the-owner.md`.

## Steps

1. **Pick the period:** what the owner asked for, otherwise the last 7 days.
2. **Collect the records** from the Business Brain (`references/run-modes.md` says how to find it):
   - **Briefings** rows in the period: title, type, Source (manual, scheduled, or "started from a recurring task" when unknown), status (finished, still running, Not run because another run was working, Abandoned), Result (Complete, Partial, Failed), approvals raised, drafts created, link.
   - **Assignments** rows in the period: owner, status, verification, and how it ran.
   - **Approvals:** rows still Pending (oldest first), rows marked Handed to you (things only the owner can do), and rows decided in the period.
   - **Workforce Settings → Schedule:** each recurring responsibility and its saved state.
   - **Scheduled tasks:** if a tool to list them is available (ToolSearch for it), list them with enabled state, next run and last run. If not, say once: "I can't check the schedule itself from here, so this is based on what landed in Notion."
3. **Reconcile the schedule against what landed.** For each scheduled responsibility, compare the runs it should have made in the period with the Briefings rows that exist:
   - Expected run with a matching row → **ran**, with its Result.
   - Expected run with no row → **no record**: it didn't run, or it didn't finish. Give the last-run status from the schedule list if you have it. Don't guess which.
   - Listed in Workforce Settings but missing from the schedule list, or disabled → **not actually scheduled**.
   - Saved as "proposed, not scheduled" → **not set up yet**.
   - A record still running with no Progress for over 45 minutes → **stuck**: the next run will finish it. Not run records are normal (two runs overlapped) and aren't problems. Abandoned records are problems: say what was left undone.
   - **Never call runs duplicates because of their timing.** Several runs in one day, or a weekly task running on another day, usually mean the owner pressed Run now. Mention a duplicate schedule only if the scheduled-task list shows two tasks for the same responsibility.
   - A run that updated its recurring task's instructions: mention it once ("Your inbox triage task now uses the 0.5.2 instructions").
   - A row or task with a configuration warning, or a task whose prompt lacks the current `prompt version` line (`references/run-modes.md`, "Is the recurring task current?") → **uses older instructions**: say what it does differently and offer "update my recurring tasks".
   - Runs whose row says the plugin or an app wasn't available → say so plainly, with the fix (reconnect the app, or keep AI Workforce turned on under Customize → Plugins).
4. **Report in this order**, short and plain:
   1. **Done:** what the team finished, grouped by team member, each with a count and link ("Client Success: 12 reply drafts across 3 runs").
   2. **Needs you:** pending approvals (count, oldest AP number and age) and things handed to you that only you can do.
   3. **Problems:** failed or partial runs, missing runs, connections that were down, each with one line on what to do.
   4. **Recurring responsibilities:** each one's state (scheduled, next run, last result; or paused, proposed, not available).
   5. **Questions the team is waiting on**, if any briefings listed some.
5. If nothing ran in the period, say exactly that and why, if the records show it. Offer the most useful next step (for example "Want me to run this morning's briefing now?").

Read-only: this skill changes nothing.
