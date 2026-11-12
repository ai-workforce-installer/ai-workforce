---
name: inbox-triage
description: This skill should be used when the owner asks to "triage my inbox", "go through my email", "check my email", "what's in my inbox", "anything important in my email?", "what did I miss?", or wants all their email reviewed, sorted and followed up, not only customer messages; also for a quick look ("just check my newest 20 emails", "anything new since lunch"). Also used by the daily briefing as its inbox check, and by a scheduled extra inbox check.
metadata:
  version: "1.0.0"
---

# Inbox Triage (all email, not just customers)

_`references/…` files are in this skill's folder (same-named files elsewhere are identical copies). Read each once at most, the ones you need together. A file named `references/if-….md` covers one situation: read it only when it comes up._

_Run by a recurring task? Also follow `references/scheduled-run-rules.md`, which wins over the task's stored instructions. A run never changes the task itself._

General inbox triage reviews everything that arrived, catches what matters (deadlines, people waiting, opportunities, money and account notices, meeting context, customer questions), does the follow-up work, and proves how much was reviewed. Customer support is one part of it, handled with the `process-customer-inquiries` steps.

Follow `references/inbox-coverage.md` (how to search, sort and count), `references/owner-corrections.md`, `references/approval-policy.md`, `references/approval-queue.md`, `references/run-modes.md`, `references/connections.md`, `references/team-roles.md` and `references/talking-to-the-owner.md`. Nothing is sent, deleted, paid or changed: replies are drafts, decisions are approval items.

**Inside the morning run:** when `daily-executive-briefing` runs this skill as its inbox check, do every step below exactly as written (its own run record with an IT Run ID, window, bookmark, Handled list, coverage counts, open-work rows and approvals), with three differences. Reuse the context the briefing already loaded instead of reading it again. Send no notification and write no chat report: the step 9 report goes in the record only, which ends `Notified: not requested (included in <the briefing's Run ID>)`. And hand the briefing a short summary to build on: the coverage line, urgent and needs-you items, what was prepared (with links), worth-knowing items, anything not checked, and the Result.

**Quick look:** when the owner asks for one at any time ("just check my newest 20 emails", "anything new since lunch"), or `first-team-meeting` asks for one during setup, follow `references/if-quick-look.md` instead of the full window: its own record labelled a quick look, bookmark not moved, never said to cover the whole inbox, the full check offered in one line. Every other run, attended or scheduled, is the full triage below.

**Urgent-only check:** a recurring task whose Owner's additions begin `Urgent-only check`, or the owner asking "anything urgent?", follows `references/if-urgent-only.md` instead: subjects only, nothing drafted, bookmark not moved, a notification only when something is urgent.

## Steps

1. **Pick the run mode and start the run record** (`references/run-modes.md`, `references/run-tracking.md`): Run ID, Source, and whether this is a new run, an interrupted one to finish, or an overlap to skip. Set the window from the checkpoint (`references/inbox-coverage.md` section 1).
2. **Load context once** (`references/notion-access.md`; never "none" unless verified empty), then the open-work queue (`references/run-tracking.md` section 6). Workforce Settings (Connections, Where things live, Schedule, Extra rules, Active departments), Priorities, Company Profile, Brand & Tone, Pricing & Offers, Customers & Leads, open Approvals and Assignments, the Your Team page, and the next 7 days of calendar events. This is what tells important mail from noise.
3. **Find everything in the window** exactly as `references/inbox-coverage.md` sections 1-2 say: All Mail, every page, exact searches recorded. List what can't be reached under Not checked.
   If Customer messages in Connections is HighLevel, also collect its unanswered customer conversations for the same window, read only, as `references/connections.md` says. They go to Client Success with the customer items and are reported under Customer support ("2 HighLevel conversations, replies ready to copy"). They are not email: they never count toward the email coverage numbers and never move the inbox bookmark. If HighLevel is unavailable, say so under Not checked and the run is Partial.
4. **Sort and read** (section 3): the owner's corrections first, then a quick pass on every thread, then open every message that might matter. Skip messages already in an earlier run's Handled list (`references/inbox-coverage.md` section 1); a new message in the same thread is new work, unless the owner closed that thread as handled or not theirs and the new message says nothing materially new. Group threads about the same underlying problem into one item.
5. **Hand out the follow-up work** (section 4), after the judgment check in `references/team-roles.md` (skip what the owner is already handling, consolidate duplicates). Launch only members with items; a handful of simple items can be done by the Chief of Staff directly. Group items by member and launch them together, using the run rule in `references/team-roles.md`:
   - **Client Success:** customer support items, following `process-customer-inquiries` steps 3-9 (FAQ-grounded drafts, escalations, FAQ questions).
   - **Sales:** people waiting on the owner about partnerships, affiliate or referral programs, deals and leads; opportunities worth a look.
   - **Operations:** vendors and account managers, software and service notices (shutdowns, failures, migrations), security notices, meeting and project context.
   - **Finance** (if active): payouts, refunds, charges and statements, reconciled read-only. If Finance is off, Operations lists them with amounts quoted from the email and its source.
   - **Marketing** only for a clear content or campaign idea tied to Priorities.
   Each brief carries the messages (sender, date, subject, link, key text), the Business Brain context, section 4's safe-links rule and limits, and the deliverables format.
6. **Verify** as Chief of Staff: every claim traces to a message; drafts exist (get_draft) and say nothing outside the Business Brain; money figures match the email; nothing was sent, clicked through a sign-in or payment link, or changed.
7. **Queue decisions** (`references/approval-queue.md`), each with a recommendation, Reversible, and the email or draft link. A reply draft by itself is never one: the owner pressing Send is the approval.
8. **Log** one Assignments row per member task (with its work key and source), each reply draft and prepared piece as a Prepared row (`references/run-tracking.md` section 6), and finish the run record with the report below, its work-handled line, the Handled list, unfinished follow-ups saved in the open-work queue, and Completed through (moved forward only if the search was complete). Result: Complete when every page was fetched, the coverage counts add up, every prioritized message was handled or queued in open work, every source was read, and every member's work was checked; Partial otherwise. Items queued past the per-run limit are normal and don't make it Partial.
9. **Report** for a phone: short, every item with its link (email `viewUrl`, checked Gmail draft link, AP number, Notion page), and everything past the first screen inside a collapsed section (a toggle; `references/notion-access.md` section 4). In this order:
   1. **The work-handled line** (`references/run-tracking.md`, "Work handled"), then **one line on coverage:** "Reviewed 247 threads from Wed 8:49 AM to Thu 8:49 AM (all of Gmail). 9 need you, 6 prepared, 228 routine."
   2. **Urgent, then what needs you:** anything urgent first; then each decision this run raised, with what the team recommends. Several emails about one problem are one item.
   3. **Ready for you:** reply drafts (Saved in Gmail, with link) and, each in a toggle named for it, Replies ready to copy, research notes and reconciliations. Customer support results are worded per section 6 of `references/inbox-coverage.md`.
   4. **Worth knowing:** at most 5 one-line items: money and account notices, deadlines, meeting context, with dates, and anything matching Always worth my attention.
   5. **Details** (one toggle): what wasn't raised and why ("Not raised: 3 emails about the old Northwind automations, per your note"), the Coverage block (section 5), how each part ran and the Run receipt.
   A run on its own (not inside the morning run) also says in one line what is still waiting on the owner ("5 things are waiting on you, the oldest since Monday. Say 'clear my desk'.").
   Open the chat reply or notification with the work-handled line, then the coverage line. A scheduled inbox check running on its own notifies with those two lines, the top 3 items and the Briefings URL.
