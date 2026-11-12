---
name: process-customer-inquiries
description: This skill should be used when the user asks to "process customer inquiries", "handle customer emails", "answer my support emails", "draft replies to customers", "check support requests", or wants only customer messages sorted, answered in draft, and escalated. For reviewing all email ("triage my inbox"), use inbox-triage, which runs these steps for its customer items.
metadata:
  version: "0.9.0"
---

# Process Customer Inquiries

_`references/…` files are in this skill's own folder; a same-named file in another skill's folder is an identical copy. Read each at most once per conversation, the ones you need together. A file named `references/if-….md` covers one situation: read it only when it comes up._

This is **customer support triage**: only messages from customers and would-be customers. It is not general inbox triage, and it never stands in for it.

Follow `references/approval-policy.md`, `references/approval-queue.md`, `references/run-modes.md` and `references/connections.md`. Replies are drafts only (Gmail drafts, or Replies ready to copy for Outlook, paste mode and HighLevel); nothing is sent.

**Running team members:** launch each member by the run rule in `references/team-roles.md` (own agent, otherwise a briefed assistant, otherwise do that member's work yourself) and report honestly which way it ran.

## Steps

0. **Check this is the right job.** If the scheduled task's prompt or the owner's request describes general inbox triage ("inbox triage", "triage my inbox", "go through my email"), stop here and load the `inbox-triage` skill with the Skill tool; it reviews all email and uses steps 3-9 below for its customer items. This outranks a task prompt telling you to follow this skill exactly (`references/if-old-task.md`). If `inbox-triage` can't be loaded, run these steps, set Result to Partial, and give the configuration warning from `references/if-old-task.md`, ending "Only customer messages were checked; the rest of your inbox was not reviewed. Say 'check my scheduled tasks' and I'll show you."
1. **Pick the run mode and start this run's record** (`references/run-tracking.md`) (`references/run-modes.md`).
2. **Collect inquiries.** Read Workforce Settings for the email app (Connections) and where customer email lives (inbox, folder, label). Find unanswered customer messages the way `references/connections.md` says for that path (Gmail, Outlook, or the Paste Box): last 24 hours for scheduled runs, last 7 days otherwise. Search everywhere mail can land, not only the inbox (archived, labeled and every tab), and fetch every page of results. Customer mail can come from addresses not yet in Customers & Leads: judge by what the message asks. Skip messages already handled in an earlier run (`references/connections.md`, Avoiding duplicates). If Customer messages in Connections is HighLevel, also collect unanswered HighLevel conversations as `references/connections.md` says (read only, same time window, its own duplicate check). If there are none and you are in attended mode, invite the owner to paste a few into the chat or the Paste Box. In scheduled mode with nothing to do, save a short row saying "No customer emails visible in <app>", naming any place under Where things live the team can't reach. Never write "inbox clear" or "nothing to do": other email wasn't reviewed by this skill. When HighLevel is checked, say so too ("none visible in Gmail or HighLevel").
3. **Load knowledge.** From the Business Brain: FAQs, Policies, Brand & Tone, Pricing & Offers, and Customers & Leads (to recognize existing customers).
4. **Delegate** to `client-success-manager` (Agent tool) with the messages and the Business Brain context. Tell it which email app the owner uses, and which messages came from HighLevel (with their channel). Ask for the triage table, reply drafts, escalations, new FAQ questions, Approvals Needed and a Run receipt.
5. **Collaborate when needed.** Billing, refund or invoice questions: also launch `finance-manager` (read-only) for the facts. Pricing, deal or prospect questions: launch `sales-manager`. Merge their answers into the drafts.
6. **Verify.** Each reply draft must cite its basis (FAQ entry, policy, thread). Remove any promise of refunds, credits, discounts, prices or exceptions not in the Business Brain and turn it into an approval item instead.
7. **Save the drafts** the way `references/connections.md` says for the owner's path: a checked Gmail draft in the same thread (**Saved in Gmail**, with its link), or the full reply under **Replies ready to copy** in this run's Briefings page for Outlook, paste mode and HighLevel (**Suggested text, not saved**; for HighLevel add the contact, channel and conversation ID). This skill never sends: never send or change anything in HighLevel. On paste mode, move handled emails under Handled on the Paste Box.
8. **Queue decisions.** A reply never needs an Approvals row just to be sent: it waits in Gmail drafts, or in Replies ready to copy, and the owner pressing Send is the approval. Mark a sensitive one "read carefully before sending" with the reason. Only a reply that depends on a decision (a refund, credit, discount or exception, or anything the Business Brain doesn't settle) raises an Approvals row, for that decision, with the Draft link filled in.
9. **Grow the FAQ.** Add new unanswered questions under "Waiting for an answer from you" on the FAQs page (append only; skip questions already on the page).
10. **Save** the report in this run's record (`references/run-tracking.md`): Type Inbox triage, title "Customer support triage <date> <HH:MM>", Run ID code CS. It never sets the inbox bookmark. Plus Assignments rows with source keys.
11. **Report:** start with the scope, "Customer support triage: customer messages only, not a full inbox review", then what is ready (each draft with its link), decisions by AP number, escalations and FAQ questions added. The full triage table and the Run receipt go in the Briefings page. In scheduled runs, notify.
