---
name: daily-executive-briefing
description: This skill should be used when the user asks for a "daily executive briefing", "morning briefing", "daily brief", "what do I need to know today", "run the daily briefing", or wants the AI team's consolidated status of the business. Also used by the scheduled daily briefing task.
metadata:
  version: "0.3.0"
---

# Daily Executive Briefing

Act as Chief of Staff in the main conversation. Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`, `approval-queue.md`, `run-modes.md` and `connections.md` (same folder). Email, calendar and files come from whatever the owner uses (Connections in Workforce Settings), or the Paste Box on paste mode.

## Steps

1. **Pick the run mode** (`run-modes.md`). Scheduled runs ask no questions.
2. **Load context.** Search Notion for the "Business Brain". Read Workforce Settings (active departments, time zone, Connections), the Paste Box, Priorities, and the most recent Daily briefing row in Briefings. Query Approvals for rows with Status = Pending, and count them.
3. **Launch the active specialists in parallel** with the Agent tool (one call each, same message). Each reports in its standard format, under 250 words, ending with Approvals Needed and a Run receipt:
   - `operations-manager`: today's and tomorrow's calendar, conflicts, tasks due or overdue, blocked items.
   - `client-success-manager`: unanswered customer emails from the last 24 hours and which are urgent. Do not draft replies here; inbox triage does that (if Inbox triage isn't scheduled, draft replies for urgent items only, as Gmail drafts in the same thread, or as Replies ready to copy when the owner doesn't use Gmail).
   - `sales-manager`: new leads, stalled deals in Customers & Leads, follow-ups due today, follow-up drafts (Gmail drafts, or Replies ready to copy).
   - `finance-manager`: invoices newly overdue or due within 3 days, total outstanding. Read-only.
   - `marketing-manager`: only if there is campaign data or a deadline this week; otherwise skip and note it.
   Skip any department not ticked as active. Tell each specialist which email and calendar apps the owner uses, or that they are on paste mode.
4. **Route** any "Needs from other manager" requests as follow-up tasks, then **verify** each report (sourced, nothing sent or changed, arithmetic rechecked).
5. **Queue approvals** in the Approvals database (`approval-queue.md`). Expire stale Pending items per the expiry rule.
6. **Write the briefing** (one screen of reading):
   - **Top 3 priorities today** (ranked against Priorities, with why)
   - **Calendar** (key meetings, conflicts; on paste mode with nothing pasted: "No calendar connected. Add key dates to your Paste Box.")
   - **Customers & sales** (urgent replies, hot leads, drafts waiting in Gmail, or a **Replies ready to copy** section with each reply in full)
   - **Money** (overdue and due soon, with totals)
   - **Marketing** (anything time-sensitive)
   - **Waiting for you** (number of Pending approvals, newest AP numbers)
   - **Verification** (verified vs not; apps that were unavailable and what was used instead)
7. **Save.** Create a Briefings row: title "Daily briefing <date>", Type = Daily briefing, Date, Run type, Result, Approvals raised, Drafts created, with the briefing as the page body. If you handled pasted emails, move them under Handled on the Paste Box (`connections.md`). Create one Assignments row per specialist task.
8. **Notify** (scheduled runs): send the 3-5 line summary per `run-modes.md`.

Never send, spend, modify financial records or make irreversible changes.
