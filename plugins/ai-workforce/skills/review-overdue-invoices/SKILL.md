---
name: review-overdue-invoices
description: This skill should be used when the user asks to "review overdue invoices", "check receivables", "who owes us money", "accounts receivable aging", "draft payment reminders", or wants an overdue invoice report. Also used by the scheduled invoice review task.
metadata:
  version: "1.0.0"
---

# Review Overdue Invoices (read-only)

_`references/…` files are in this skill's folder (same-named files elsewhere are identical copies). Read each once at most, the ones you need together. A file named `references/if-….md` covers one situation: read it only when it comes up._

_Run by a recurring task? Also follow `references/scheduled-run-rules.md`, which wins over the task's stored instructions. A run never changes the task itself._

Follow `references/approval-policy.md`, `references/approval-queue.md`, `references/run-modes.md` and `references/connections.md`. Financial records are strictly read-only: never mark paid, edit, void, refund or charge anything, even when the owner asks: say so and give them the exact step to do themselves (Handed to you, not an approval). This skill never sends: a reminder is a draft that waits on the owner's desk (`review-approvals`).

**Running team members:** by the run rule in `references/team-roles.md` (own agent, else a briefed assistant, else do that member's work yourself); report honestly which way each ran.

## Steps

1. **Pick the run mode and start this run's record** (`references/run-tracking.md`) (`references/run-modes.md`).
2. **Find the data.** Read Workforce Settings for where invoices are kept. Search that source first, then Notion, the owner's file app (Google Drive or OneDrive: invoice sheets or CSVs) and their email (invoice emails), per Connections. If the user attached or pasted data, use that. If no source exists: in attended mode, ask where invoices are kept; in scheduled mode, save a Briefings row with Result = Failed saying no invoice source was found, and stop. Never invent data.
3. **Delegate** to `finance-manager` (Agent tool) with the data location, today's date, Policies (payment terms, late fees) and Brand & Tone. Ask for the aging report (current, 1-30, 31-60, 61-90, 90+), top 5 overdue, anomalies, reminder drafts by tier, Approvals Needed and a Run receipt.
4. **Collaborate.** Launch `client-success-manager` to check whether any overdue customer has an open dispute or support issue before any reminder is drafted.
5. **Verify.** Recompute totals from the source rows yourself (run the arithmetic). Flag mismatches and missing due dates.
6. **Drafts.** Reminder drafts follow `references/connections.md` (Gmail drafts, otherwise Replies ready to copy in this run's Briefings page). A draft is never an approval; if it is later sent from the desk, the invoice is re-checked as still unpaid first. Skip customers with disputes.
7. **Queue decisions.** A late fee or write-off is an Approvals row (Action type = Financial record) with exact figures; the owner enters it.
8. **Save** the report in this run's record (`references/run-tracking.md`) (Type = Invoice review) and Assignments rows.
9. **Report:** totals by aging bucket, top overdue with invoice number, amount, due date and days late, anomalies, drafts created, Approvals Needed by AP number, Run receipt. Notify in scheduled runs.
