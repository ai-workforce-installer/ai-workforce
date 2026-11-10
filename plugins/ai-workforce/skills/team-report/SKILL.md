---
name: team-report
description: This skill should be used when the owner asks "what's my team been working on?", "what did the team do this week?", "did the morning briefing run?", "what's scheduled?", "is the team working?", "any problems?", "how's my first week going?", or wants a truthful summary of the team's actual activity, results, failures and pending decisions.
metadata:
  version: "0.8.0"
---

# Team Report

_Files named `references/…` are in this skill's own folder. A file with the same name in another skill's folder is an identical copy: read each reference at most once per conversation._

A truthful account of what the team actually did. Every line rests on a record in the Business Brain or the list of scheduled tasks. Never fill a gap with what probably happened. Speak per `references/talking-to-the-owner.md`.

## Steps

1. **Pick the period:** what the owner asked for, otherwise the last 7 days.
2. **Collect the records** from the Business Brain (`references/run-modes.md` says how to find it):
   - **Briefings** rows in the period: title, type, Source (manual, scheduled, or "started from a recurring task" when unknown), status (finished, still running, Not run because another run was working, Abandoned), Result (Complete, Partial, Failed), its Handled line (older records: approvals raised and drafts created), link.
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
   - A row with a configuration warning → say what the run did about it. An older `prompt version` line on a task is never a problem: every task follows the installed plugin (`references/run-modes.md`, "Which job a recurring task does"), so never offer to update one.
   - A daily briefing task and a separate inbox triage task that runs within 3 hours of it → mention once that the morning briefing now checks the inbox itself, and offer to combine them (`schedule-workforce`, "One morning run").
   - An Inbox triage record that says it was included in a daily briefing is part of that morning run, not a second run. A Schedule line reading "part of the daily briefing" is not a separate task: its runs are those records.
   - Runs whose row says the plugin or an app wasn't available → say so plainly, with the fix (reconnect the app, or keep AI Workforce turned on under Customize → Plugins).
4. **Report in this order**, short and plain:
   1. **Handled:** first the period's totals in one line, added up from the records' Handled lines ("This week: 14 reply drafts, 3 meeting preps, 6 items closed, 5 decisions raised"), then what the team finished, grouped by team member, each with a count and link ("Client Success: 12 reply drafts across 3 runs"). Runs finishing is not the measure; work handled is. If the total is zero, or the records show three or more runs in a row with nothing handled, say that first and plainly, with the reason the reports give (usually a place the work lives that isn't connected, named under Blocked or Not checked) and the one step that would change it. Never soften it with a count of runs that completed.
   2. **Needs your decision:** pending approvals (count, oldest AP number and age) and things handed to you that only you can do.
   3. **Problems:** failed or partial runs, missing runs, connections that were down, each with one line on what to do.
   4. **Recurring responsibilities:** each one's state (scheduled, next run, last result; or paused, proposed, not available).
   5. **Questions the team is waiting on**, if any briefings listed some.
5. If nothing ran in the period, say exactly that and why, if the records show it. Offer the most useful next step (for example "Want me to run this morning's briefing now?").

## First-week recap ("how's my first week going?")
Optional, on request (the daily briefing mentions it once, between day 5 and 10). Same records as above, from "Set up on" in Workforce Settings to today, answered in at most six short lines, each resting on a record:
1. **First assignment:** did it produce something useful? Its Briefings row and Result, and what came out of it (with the link). If it was a quick look, say whether the full inbox review has happened since.
2. **First recurring run:** for each recurring responsibility, did a run actually land (a Briefings row from the recurring task) and how did it end? "Scheduled but no run recorded yet" is said as that.
3. **Your first decisions:** how many approvals are waiting and the oldest; offer to go through them now (`review-approvals`).
4. **What the team has learned:** the owner preferences and corrections saved so far (Brand & Tone, Your Team notes, Priorities). If none, ask the one question that would help most, for example "How do you usually sign off?" or "Is there anything in your inbox the team should stop flagging?"
5. **One thing to hand off next:** one suggestion grounded in what the team saw (a request that came up more than once in Assignments, or the owner's own answer under "Work I'd like to hand off"), and offer to make it recurring (`schedule-workforce`, one responsibility only, never a second task for one already scheduled).
6. **In one line:** what the team did this week (counts, from the records).
Nothing here creates tasks, approvals or notifications; anything the owner agrees to is done by the skill named.

Read-only: this skill changes nothing.
