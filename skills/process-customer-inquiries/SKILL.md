---
name: process-customer-inquiries
description: This skill should be used when the user asks to "process customer inquiries", "triage my inbox", "handle customer emails", "draft replies to customers", "check support requests", or wants customer messages sorted, answered in draft, and escalated. Also used by the scheduled inbox triage task.
metadata:
  version: "0.2.0"
---

# Process Customer Inquiries

Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`, `approval-queue.md` and `run-modes.md` (same folder). Replies are Gmail drafts only; nothing is sent.

## Steps

1. **Pick the run mode** (`run-modes.md`).
2. **Collect inquiries.** Read Workforce Settings for where customer email lives (inbox, label). Search Gmail for unanswered customer messages: last 24 hours for scheduled runs, last 7 days otherwise. Skip threads that already have a draft reply from an earlier run. In attended mode, if Gmail is not connected, ask the user to paste the messages.
3. **Load knowledge.** From the Business Brain: FAQs, Policies, Brand & Tone, Pricing & Offers, and Customers & Leads (to recognize existing customers).
4. **Delegate** to `client-success-manager` (Agent tool) with the messages and the Business Brain context. Ask for the triage table, reply drafts, escalations, new FAQ questions, Approvals Needed and a Run receipt.
5. **Collaborate when needed.** Billing, refund or invoice questions: also launch `finance-manager` (read-only) for the facts. Pricing, deal or prospect questions: launch `sales-manager`. Merge their answers into the drafts.
6. **Verify.** Each reply draft must cite its basis (FAQ entry, policy, thread). Remove any promise of refunds, credits, discounts, prices or exceptions not in the Business Brain and turn it into an approval item instead.
7. **Create Gmail drafts** for verified replies as replies in the same thread, so later runs can see a draft already exists (drafts only, never send). Record each draft's subject.
8. **Queue approvals.** Every reply that needs the owner's yes before sending (escalations, anything sensitive) becomes an Approvals row with Action type = Send message and the Draft link filled in. Routine, fully grounded replies do not need a row; they wait in Gmail drafts for the owner to send.
9. **Grow the FAQ.** Add new unanswered questions under "Waiting for an answer from you" on the FAQs page (append only; skip questions already on the page).
10. **Save** a Briefings row (Type = Inbox triage) with the report, plus Assignments rows.
11. **Report:** triage table (sender, topic, urgency, status), drafts created (count and where), escalations, FAQ questions added, Approvals Needed by AP number, Run receipt. In scheduled runs, notify per `run-modes.md`.
