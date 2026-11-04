---
name: schedule-workforce
description: This skill should be used when the user asks to "schedule the workforce", "make the team run automatically", "go autonomous", "set up the daily schedule", "schedule my briefing", "change the team's schedule", or wants the AI team's skills to run on their own at set times.
metadata:
  version: "0.2.0"
---

# Schedule the Workforce

Turn the team's skills into scheduled tasks that run on their own. Speak in plain language and call them "scheduled tasks" (never triggers, routines or cron jobs). Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`.

## Steps

1. **Find the scheduling tools.** Use ToolSearch for scheduling tools (for example "schedule trigger create list"). Go by the tool descriptions. Use only tools that create scheduled tasks that run in fresh sessions (not in-session cron tools, which disappear when the session ends). If none exist, say plainly that scheduled tasks aren't available on this account or surface, explain that the owner can still run each skill by asking, and stop.
2. **Read Workforce Settings** in the Business Brain: time zone, working hours, active departments, and the Schedule section. If the time zone is missing, ask for it.
3. **Check what already exists.** List the owner's existing scheduled tasks. Do not create duplicates; offer to update or remove the old ones instead.
4. **Propose the schedule** as a short table (task, when, what it does, departments used). Defaults, adjusted to working hours and active departments:
   - Daily briefing: weekdays, 30 minutes before the workday starts.
   - Inbox triage: weekdays, mid-morning and mid-afternoon. Only if Client Success is active.
   - Weekly marketing plan: Mondays, early morning. Only if Marketing is active.
   - Invoice review: Fridays, morning. Only if Finance is active and an invoice source is set.
   Point out that each run uses part of their Claude usage allowance, so fewer runs is fine. Wait for the owner's yes or changes.
5. **Create each scheduled task** with the prompt from `references/scheduled-prompts.md`, filled in with the owner's Business Brain name. Write times in the owner's local time zone. For times on the hour or half hour, move the start a few minutes earlier, and avoid any busy window the tool description warns about, as it advises. Turn on push notifications if the tool supports it.
6. **Check plugins and approval setting in each result.** If the result shows the task runs without this plugin enabled, say so plainly: the prompts are written to work anyway (they fall back to general-purpose subagents), but the owner gets the full skill behavior only when the plugin is available to scheduled runs.
7. **Report each task's approval setting** from the tool result, and explain the trade-off plainly without recommending either: with approval prompts on, an unattended run pauses at the first action that needs approval and may not finish until the owner opens it; with automatic approval, runs finish on their own and rely on the plugin's written rules (drafts only, no sending, spending, deleting or booking) rather than a prompt to stop them. The owner chooses in the task's settings.
8. **Save the schedule** to Workforce Settings / Schedule (replace the `_not set_` lines).
9. **Offer a test fire** of the daily briefing task now, so the owner sees a scheduled run land in Briefings.

## Changing or pausing
For "pause the team", "change my briefing time" or "stop inbox triage": list existing tasks, update or disable the matching one, and update Workforce Settings. Never delete a task unless the owner asks for deletion.
