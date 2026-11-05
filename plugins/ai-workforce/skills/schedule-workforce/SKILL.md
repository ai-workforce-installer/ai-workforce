---
name: schedule-workforce
description: This skill should be used when the owner asks "can someone handle this every Friday?", "do this every morning", "make it a recurring responsibility", "schedule the team", "make the team run automatically", "schedule my briefing", "change the team's schedule", "pause the team", or wants team members to handle work on their own at set times.
metadata:
  version: "0.4.0"
---

# Schedule the Workforce

Give team members recurring responsibilities that run on their own. With the owner, call them recurring responsibilities ("Client Success handles your inbox every weekday at 10"); in tool calls they are scheduled tasks. Never say triggers, routines or cron jobs.

**One responsibility or the full set.** When called for one responsibility (from the team meeting, or "can someone handle this every Friday?"), propose and create only that one. Use the full default set below only when the owner asks to schedule the team.

**Four states, never blurred:** *proposed* (discussed, not created), *scheduled* (created, and confirmed in the list of scheduled tasks), *ran* (a Briefings row exists for that run), *succeeded or failed* (that row's Result). Only say "scheduled" after step 5's check, and never say a run happened without its Briefings row. Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`.

## Steps

1. **Find the scheduling tools.** Use ToolSearch for scheduling tools (for example "schedule trigger create list"). Go by the tool descriptions. Use only tools that create scheduled tasks that run in fresh sessions (not in-session cron tools, which disappear when the session ends). If none exist, say plainly that scheduled tasks aren't available on this account or surface, explain that the owner can still run each skill by asking, and stop.
2. **Read Workforce Settings** in the Business Brain: time zone, working hours, active departments, and the Schedule section. If the time zone is missing, ask for it.
3. **Check what already exists.** List the owner's existing scheduled tasks. Do not create duplicates; offer to update or remove the old ones instead.
4. **Propose the schedule** as a short table (task, when, what it does, departments used). Defaults, adjusted to working hours and active departments:
   - Daily briefing: weekdays, 30 minutes before the workday starts.
   - Inbox triage: weekdays, mid-morning and mid-afternoon. Skip if the owner turned Client Success off.
   - Weekly marketing plan: Mondays, early morning. Only if a marketing results source is set and Marketing isn't turned off.
   - Invoice review: Fridays, morning. Only if an invoice source is set and Finance isn't turned off.
   - Anything else (Sales follow-ups, an Operations review, a custom member's work): the cadence the owner asked for, with the "Any other responsibility" prompt.
   When proposing the full set, mention that each run uses part of their Claude usage allowance, so fewer runs is fine. Wait for the owner's yes or changes.
5. **Create each scheduled task** with the prompt from `references/scheduled-prompts.md`, filled in with the owner's Business Brain name. Write times in the owner's local time zone. For times on the hour or half hour, move the start a few minutes earlier, and avoid any busy window the tool description warns about, as it advises. Turn on push notifications if the tool supports it. **Then confirm it exists:** list the scheduled tasks again and check each new one is there, enabled, with the right time and a next run. Anything missing or wrong: say so plainly and fix it before going on.
6. **Check each result for limits.** If the result shows recurring runs won't have AI Workforce available, say so in plain words ("recurring runs may use a simpler version of your team; your results still land in Notion"); the prompts are written to work either way.
7. **Report each task's approval setting** from the tool result in one line. Explain the trade-off only when the full set is being scheduled or the owner asks, plainly and without recommending either: with approval prompts on, an unattended run pauses at the first action that needs approval and may not finish until the owner opens it; with automatic approval, runs finish on their own and rely on the plugin's written rules (drafts only, no sending, spending, deleting or booking) rather than a prompt to stop them. The owner chooses in the task's settings.
8. **Save the schedule** to Workforce Settings / Schedule, one line per responsibility, with its state: `- Inbox triage (Client Success): weekdays 10:23 AM, scheduled, confirmed <date>`. A responsibility discussed but not created is saved as `proposed, not scheduled` with the reason (for example "recurring runs aren't available on this account"). Replace `not set` lines; add a line for anything new.
9. **Offer a test run** of the responsibility just created (not a different one), so the owner sees it land in Briefings. A listed schedule only proves it exists; only a Briefings row proves a run happened. If approval prompts are on, warn that the run may wait for them.

## Changing or pausing
For "pause the team", "change my briefing time" or "stop inbox triage": list existing tasks, update or disable the matching one, and update Workforce Settings. Never delete a task unless the owner asks for deletion.
