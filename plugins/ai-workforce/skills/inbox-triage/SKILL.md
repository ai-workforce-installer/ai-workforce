---
name: inbox-triage
description: This skill should be used when the owner asks to "triage my inbox", "go through my email", "check my email", "what's in my inbox", "anything important in my email?", "what did I miss?", or wants all their email reviewed, sorted and followed up, not only customer messages. Also used by the scheduled inbox triage task.
metadata:
  version: "0.4.4"
---

# Inbox Triage (all email, not just customers)

_Files named `references/…` are in this skill's own folder._

General inbox triage reviews everything that arrived, catches what matters (deadlines, people waiting, opportunities, money and account notices, meeting context, customer questions), does the follow-up work, and proves how much was reviewed. Customer support is one part of it, handled with the `process-customer-inquiries` steps.

Follow `references/inbox-coverage.md` (how to search, sort and count), `references/approval-policy.md`, `references/approval-queue.md`, `references/run-modes.md`, `references/connections.md`, `references/team-roles.md` and `references/talking-to-the-owner.md`. Nothing is sent, deleted, paid or changed: replies are drafts, decisions are approval items.

## Steps

1. **Pick the run mode and Run type** (`references/run-modes.md`, including "Manual or Scheduled?").
2. **Load context.** Workforce Settings (Connections, Where things live, Schedule, Extra rules, Active departments), Priorities, Company Profile, Brand & Tone, Pricing & Offers, Customers & Leads, open Approvals and Assignments, the Your Team page, and the next 7 days of calendar events. This is what tells important mail from noise.
3. **Find everything in the window** exactly as `references/inbox-coverage.md` sections 1-2 say: All Mail, every page, exact searches recorded. List what can't be reached under Not checked.
4. **Sort and read** (section 3): a quick pass on every thread, then open every message that might matter. Skip threads already reported in an earlier Inbox triage row unless a new message arrived since.
5. **Hand out the follow-up work** (section 4). Group items by member and launch them together, using the run rule in `references/team-roles.md`:
   - **Client Success:** customer support items, following `process-customer-inquiries` steps 3-9 (FAQ-grounded drafts, escalations, FAQ questions).
   - **Sales:** people waiting on the owner about partnerships, affiliate or referral programs, deals and leads; opportunities worth a look.
   - **Operations:** vendors and account managers, software and service notices (shutdowns, failures, migrations), security notices, meeting and project context.
   - **Finance** (if active): payouts, refunds, charges and statements, reconciled read-only. If Finance is off, Operations lists them with amounts quoted from the email and its source.
   - **Marketing** only for a clear content or campaign idea tied to Priorities.
   Each brief carries the messages (sender, date, subject, link, key text), the Business Brain context, the safe-links rule and limits from section 4, and the deliverables format. Nobody gets an empty brief: skip members with nothing to do and say so.
6. **Verify** as Chief of Staff: every claim traces to a message; drafts exist (get_draft) and say nothing outside the Business Brain; money figures match the email; nothing was sent, clicked through a sign-in or payment link, or changed.
7. **Queue approvals** for every decision or consequential next step (`references/approval-queue.md`), each with a recommendation, Reversible, and the email or draft link.
8. **Log** one Assignments row per member task and one Briefings row (Type = Inbox triage, Run type per step 1) with the report below. Result: Complete when every page was fetched, the coverage counts add up, every likely-important message was read and every member's work was checked; Partial otherwise. A mailbox the team has never been connected to doesn't make the run Partial, but it is always named under Not checked (`references/inbox-coverage.md` section 5).
9. **Report** in this order, short, every item with its link (email `viewUrl`, checked Gmail draft link, AP number, Notion page):
   1. **One line on coverage:** "Reviewed 247 threads from Wed 8:49 AM to Thu 8:49 AM (all of Gmail). 9 need you, 6 prepared, 228 routine."
   2. **Needs you:** decisions and replies, each with what the team recommends.
   3. **Prepared by the team:** drafts (Saved in Gmail, with link), research notes, reconciliations.
   4. **Worth knowing:** money and account notices, deadlines, meeting context, with dates.
   5. **Customer support:** results, worded per section 6 of `references/inbox-coverage.md`.
   6. **Waiting for your decision:** every Pending approval (oldest first, AP number, one line, link), then: "Reply in one message, for example: approve 3, 5; reject 4; change 6: <instructions>."
   7. **Coverage** (section 5 block), then how each part ran and the Run receipt. In chat, show items 1-6 and the Notion link; the full Coverage block and receipt live in the Briefings page unless the owner asks.
   In scheduled runs, notify per `references/run-modes.md` with the coverage line, the top 3 items and the Briefings URL.
