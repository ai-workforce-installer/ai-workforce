---
name: review-overdue-invoices
description: This skill should be used when the user asks to "review overdue invoices", "check receivables", "who owes us money", "accounts receivable aging", "draft payment reminders", or wants an overdue invoice report. Also used by the scheduled invoice review task.
metadata:
  version: "0.5.4"
---

# Review Overdue Invoices (read-only)

_Files named `references/…` are in this skill's own folder._

_When this skill runs from a recurring task, `references/scheduled-prompts.md` holds the current instructions for that task and `references/prompt-history.md` every released version (used only to keep the task up to date safely, per `references/run-modes.md`)._

Follow `references/approval-policy.md`, `references/approval-queue.md`, `references/run-modes.md` and `references/connections.md`. Financial records are strictly read-only: never mark paid, edit, void, refund, charge or send anything.

**Running team members:** wherever this skill says to launch a member with the Agent tool, follow the run rule in `references/team-roles.md` (own agent in Cowork, otherwise a briefed assistant, otherwise do that member's work yourself in this conversation), include the member's Your Team notes in the brief, and report honestly which way it ran.

## Steps

1. **Pick the run mode and start this run's record** (`references/run-tracking.md`) (`references/run-modes.md`).
2. **Find the data.** Read Workforce Settings for where invoices are kept. Search that source first, then Notion, the owner's file app (Google Drive or OneDrive: invoice sheets or CSVs) and their email (invoice emails), per Connections. If the user attached or pasted data, use that. If no source exists: in attended mode, ask where invoices are kept; in scheduled mode, save a Briefings row with Result = Failed saying no invoice source was found, and stop. Never invent data.
3. **Delegate** to `finance-manager` (Agent tool) with the data location, today's date, Policies (payment terms, late fees) and Brand & Tone. Ask for the aging report (current, 1-30, 31-60, 61-90, 90+), top 5 overdue, anomalies, reminder drafts by tier, Approvals Needed and a Run receipt.
4. **Collaborate.** Launch `client-success-manager` to check whether any overdue customer has an open dispute or support issue before any reminder is drafted.
5. **Verify.** Recompute totals from the source rows yourself (run the arithmetic) and confirm they match. Flag mismatches and missing due dates.
6. **Drafts.** Reminder drafts follow `references/connections.md`: Gmail drafts if the owner uses Gmail, otherwise Replies ready to copy in this run's Briefings page. Never send. Skip customers with disputes.
7. **Queue approvals.** Each reminder send, late fee or write-off is an Approvals row (Action type = Send message or Financial record) with exact details and the Draft link.
8. **Save** the report in this run's record (`references/run-tracking.md`) (Type = Invoice review) and Assignments rows.
9. **Report:** totals by aging bucket, top overdue with invoice number, amount, due date and days late, anomalies, drafts created, Approvals Needed by AP number, Run receipt. Notify in scheduled runs.
