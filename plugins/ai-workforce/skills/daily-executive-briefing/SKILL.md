---
name: daily-executive-briefing
description: This skill should be used when the user asks for a "daily executive briefing", "morning briefing", "daily brief", "what do I need to know today", "run the daily briefing", or wants the AI team's consolidated status of the business. Also used by the scheduled daily briefing task.
metadata:
  version: "0.4.1"
---

# Daily Executive Briefing

_Files named `references/…` are in this skill's own folder._

Act as Chief of Staff in the main conversation. Follow `references/approval-policy.md`, `references/approval-queue.md`, `references/run-modes.md` and `references/connections.md`. Email, calendar and files come from whatever the owner uses (Connections in Workforce Settings), or the Paste Box on paste mode.

**Running team members:** wherever this skill says to launch a member with the Agent tool, follow the run rule in `references/team-roles.md` (own agent in Cowork, otherwise a briefed assistant, otherwise do that member's work yourself in this conversation), include the member's Your Team notes in the brief, and report honestly which way it ran.

## Steps

1. **Pick the run mode** (`references/run-modes.md`). Scheduled runs ask no questions.
2. **Load context.** Search Notion for the "Business Brain". Read Workforce Settings (active departments, time zone, Connections), the Paste Box, Priorities, and the most recent Daily briefing row in Briefings. Query Approvals for rows with Status = Pending, with every property (you need them for the Waiting for you cards in step 6), and rows marked Handed to you. Read the Your Team page (each member's notes, custom members, suggestions already made).
3. **Launch the active specialists in parallel** with the Agent tool (one call each, same message). Each reports in its standard format, under 250 words, ending with Approvals Needed and a Run receipt:
   - `operations-manager`: today's and tomorrow's calendar, conflicts, tasks due or overdue, blocked items.
   - `client-success-manager`: unanswered customer emails from the last 24 hours and which are urgent. Do not draft replies here; inbox triage does that (if Inbox triage isn't scheduled, draft replies for urgent items only, as Gmail drafts in the same thread, or as Replies ready to copy when the owner doesn't use Gmail).
   - `sales-manager`: new leads, stalled deals in Customers & Leads, follow-ups due today, follow-up drafts (Gmail drafts, or Replies ready to copy).
   - `finance-manager`: invoices newly overdue or due within 3 days, total outstanding. Read-only.
   - `marketing-manager`: only if there is campaign data or a deadline this week; otherwise skip and note it.
   Skip any department not ticked as active. Tell each specialist which email and calendar apps the owner uses, or that they are on paste mode.
4. **Route** any "Needs from other manager" requests as follow-up tasks, then **verify** each report (sourced, nothing sent or changed, arithmetic rechecked).
5. **Queue approvals** in the Approvals database (`references/approval-queue.md`). Expire stale Pending items per the expiry rule.
6. **Write the briefing** (one screen of reading):
   - **Top 3 priorities today** (ranked against Priorities, with why)
   - **Calendar** (key meetings, conflicts; on paste mode with nothing pasted: "No calendar connected. Add key dates to your Paste Box.")
   - **Customers & sales** (urgent replies, hot leads, drafts waiting in Gmail, or a **Replies ready to copy** section with each reply in full)
   - **Money** (overdue and due soon, with totals)
   - **Marketing** (anything time-sensitive)
   - **Waiting for you**: one card for **every** Pending approval (the ones raised in this run and older ones still open), oldest first, so the owner can decide straight from the briefing. Each card is two lines:
     `**AP-<n>** · <Action type> · <Department> · <Item>`
     `<Exact action, one short sentence> · Reversible: yes/no · [Draft](<Draft link>) (omit if none) · raised <date>`
     Mark items raised in this run as **new**. If the owner ticked an item Approved in Notion, show "(ticked in Notion, needs your yes here)". End the section with one line: "Reply 'approve 3, 5; reject 4; change 6: <what>' and I'll handle them." With no Pending items, write "Nothing waiting for you."
   - **Still on your list**: rows marked Handed to you, one line each (AP number, what to do, raised date). Omit when empty.
   - **Questions for you**: facts the team needed but the Business Brain lacks (at most 3, per `references/just-in-time.md`). Omit when empty.
   - **One suggestion** (optional, at most once a week): one responsibility or team change the team could take on, only when based on something the team actually saw (the same customer question three or more times; the owner changing drafts the same way repeatedly; one member often doing work outside its job). Check "Suggestions from your Chief of Staff" on the Your Team page first: skip it if a suggestion was made in the last 7 days, and never repeat one marked declined. Add it there with today's date and "open". Omit otherwise.
   - **Verification** (verified vs not; apps that were unavailable and what was used instead)
7. **Save.** Create a Briefings row: title "Daily briefing <date>", Type = Daily briefing, Date, Run type, Result, Approvals raised, Drafts created, with the briefing as the page body. If you handled pasted emails, move them under Handled on the Paste Box (`references/connections.md`). Create one Assignments row per specialist task.
8. **Notify** (scheduled runs): send the 3-5 line summary per `references/run-modes.md`, including how many approvals are waiting and the oldest AP number.
9. **Decisions in reply** (attended mode, or when the owner later replies to the briefing): if the owner answers with AP numbers, carry them out with the `review-approvals` skill, starting at its step 4 for the named items, without re-presenting the queue.

Never send, spend, modify financial records or make irreversible changes.
