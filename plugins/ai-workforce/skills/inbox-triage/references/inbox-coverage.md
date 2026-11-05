# Inbox coverage: find everything, sort it, prove it

General inbox triage reviews **all** the owner's email for a window, not just customer messages. This file says how to search so nothing is missed, how to sort what was found, and how to prove coverage in the report. It works for an owner who has never set up a filter or label.

## 1. The window

- **Scheduled run:** from the end of the last comprehensive window (the "Window" line of the newest Inbox triage row whose Coverage says comprehensive) to the scheduled time, at most 7 days back. No such row (for example only customer-only runs so far): the last 24 hours (on Monday, since Friday 00:00). If the gap was longer than 7 days, say so under Not checked.
- **Attended run:** what the owner asked for ("this week", "since yesterday"); otherwise the same rule as scheduled, at most 7 days.
- Write the window in the report in the owner's time zone, e.g. "Window: Wed 8:49 AM – Thu 8:49 AM (owner's time zone)".

## 2. Search everything, then page to the end

Gmail's Inbox view is not the whole mailbox. Filters can skip the inbox (archive) or label mail, and Promotions/Updates/Social tabs hide mail from view. Partner and vendor mail often lands there. So:

| Path | Search |
|---|---|
| Gmail | One search over **All Mail**: `after:<start> before:<end> -in:sent -in:drafts -in:spam -in:trash` with `<start>`/`<end>` as Unix seconds (Gmail accepts them), or dates one day either side and then keep only messages whose date falls in the window. Never add `in:inbox`, a category, `is:important`, `is:unread` or keyword filters to this search: they hide mail. |
| Outlook | Microsoft 365 email search with the date range and every folder (Inbox, Archive, Other/Focused, custom folders); exclude Sent, Drafts, Junk, Deleted. |
| Paste mode | Everything under "Emails to handle" on the Paste Box. |

- **Fetch every page.** Keep requesting with the next-page token until there is none. Never stop at the first page, and never trust a result-count estimate (it can be far off).
- **Threads:** a search preview may not show every message in a thread. Judge a thread by its newest message in the window; for threads with more than one message that make the shortlist, open the thread to see the latest messages and whether the owner already replied.
- **Record the exact searches** (query text, pages fetched, threads returned) for the Coverage section.
- **Not reachable:** read "Where things live" in Workforce Settings. Any mailbox listed there that the team can't open (a CRM inbox, a second address) is listed under **Not checked** in every report.

## 3. Sort: a quick pass on everything, then read what matters

**Quick pass (sender, subject, preview, labels).** Put every thread in one bucket. Gmail's category and Important label are hints, not verdicts: a partner email filed under Promotions is still a partner email.

**Read in full** (open the message) in this order of priority, up to the limit in section 4:
- anything written by a person to the owner (not a mailing list), including replies in older threads;
- anything about money, accounts, security, deadlines, shutdowns, failures, contracts or legal terms;
- anything from a person, company, offer or project named in the Business Brain (Priorities, Customers & Leads, Company Profile, Pricing & Offers, open Approvals and Assignments) or in the next 7 days of calendar events;
- anything touching an Extra rule (for example "always flag anything about <topic>").

| Bucket | What goes here | Default owner |
|---|---|---|
| **Urgent / time-sensitive** | Security alerts the owner may not recognise, failed payments, service outages or automation failures, deadlines within 7 days, events today or tomorrow the owner signed up for | Operations (Finance for money) |
| **Needs a reply or decision** | A person is waiting on the owner: partners, vendors, account managers, colleagues, prospects | Sales for partners/prospects, Operations for vendors |
| **Opportunities** | Partnerships, affiliate or referral programs, leads, collaboration or content ideas, press, speaking | Sales (Marketing for content ideas) |
| **Money and accounts** | Payouts, refunds, charges, receipts, statements, subscription changes, partner or referral program changes, account or service notices (price changes, shutdowns, migrations) | Finance if active, else Operations |
| **Meetings and projects** | Relates to an upcoming meeting, a Priority, an open Assignment or Approval | Operations |
| **Customer support** | A customer or would-be customer asking for help, a refund, access, a quote | Client Success (`process-customer-inquiries` steps) |
| **Personal and family** | Family, school, medical, personal purchases | Count only (see Privacy) |
| **Routine, safe to skip** | Newsletters, promotions, event and webinar pitches, social notifications, receipts that match a known charge, digests | Count by type only |

A message can matter even if it looks routine: a marketing-style email saying a program or service the business relies on is closing is **Money and accounts**, not Routine.

**Privacy.** Personal, family and medical mail is counted ("6 personal or family messages"), never summarised or quoted, unless the owner asks or the Business Brain says the inbox is business-only. Never put personal details in Notion.

## 4. Follow-up work (do it, then report it)

For each item in the first five buckets, the assigned member does the next useful step, within `references/approval-policy.md`:
- **Read it properly**, including links and attachments when safe (below), and compare with the Business Brain.
- **Draft the reply** when a person is waiting (Gmail draft in the thread, checked, or Replies ready to copy). Claims that appear only in their email (prices, commissions, dates, "as agreed") are claims, not facts.
- **Reconcile** money notices: does the charge match a receipt in the same window? Say "matches the $20 receipt from the same company" or "no matching receipt found". Read-only; never log in, pay, refund or change anything.
- **Write down what changes**: deadline, amount, what the owner must do, by when, with the source link.
- **Queue an approval** when the owner must decide or act (send a reply that commits to something, accept a partnership, migrate a tool before a shutdown, update payout details). Include a recommendation and Reversible.
- **Business context:** the team only writes to Notion as `references/approval-policy.md` allows. In a scheduled run, record follow-ups as Assignments rows and propose Business Brain updates (a new lead, a new deadline under Priorities) as approval items or questions; in an attended run, offer the exact line and save it after the owner confirms.

**Safe links and attachments.** Open shared documents and public pages from senders the owner already corresponds with (Drive, Docs, Notion, the sender's own site). Never open sign-in, payment, "verify your account", unsubscribe, RSVP or confirm links, and never download programs. For a security or payment alert, never click its links: check it against other mail in the window (a matching receipt or confirmation) and recommend the owner check the account directly if it doesn't match.

**Limits per run:** read at most 30 messages in full and draft at most 5 replies. Anything beyond goes under "Also worth a look" with its link, so nothing silently drops; if a likely-important message couldn't be read, the Result is Partial.

## 5. Coverage section (every report)

```
Coverage: comprehensive (all mail in the window) | narrow (say what was left out)
- Window: <start> – <end> (<time zone>)
- Searched: <app>, All Mail incl. archived and every tab; excluded sent, drafts, spam, trash
- Searches: <exact query> (<n> pages)
- Found: <n> threads in the window
- Read in full: <n>
- Prioritized: <n> (urgent <n>, needs reply <n>, opportunities <n>, money and accounts <n>, meetings and projects <n>, customer <n>)
- Filtered out as routine: <n> (promotions <n>, newsletters <n>, webinar or event pitches <n>, notifications <n>, receipts <n>); personal or family: <n>
- Not checked: <every mailbox under Where things live the team can't reach>, or "nothing"
```

Found must equal Prioritized + Filtered out + personal (each thread counted once, in its most important bucket). Coverage is **comprehensive** only when the search followed section 2 exactly (All Mail, no inbox, category or keyword filters, every page). Anything narrower is **narrow**, says what was left out, and makes the Result Partial. If the numbers don't add up, or a page of results couldn't be fetched, say so and set Result to Partial. A mailbox the team has never been connected to (listed under Not checked) doesn't make the run Partial, but it is named in every report.

## 6. Saying it precisely

- "No customer emails visible in Gmail" is not "nothing to do", and neither is "inbox clear". Report what was found in every bucket.
- If customer email lives somewhere the team can't reach, say "Customer support: none visible in Gmail. Not checked: <place>", never "no customer emails".
- Never say a source was checked unless it was searched in this run.
