# Reading Notion reliably and cheaply

The Business Brain must work on Notion's Free plan. Notion's connection offers several ways to read a database, and some are rationed by plan: on Free, SQL-style queries share a small workspace allowance that ordinary runs can use up. When a read fails, the team must never mistake "couldn't read" for "nothing there".

## 1. How to read a database (in this order)

1. **Saved view** (`mode: "view"` with the view's link): use it when a view already shows what you need (for example the Approvals "Decision board", or Briefings "Newest first"). Views page through results: when the answer says there are more, ask for the next page with its cursor until there are none.
2. **Rows with filters** (`mode: "rows"` with a structured `filter` and `sort`): the default for everything else, e.g. Approvals where Status is Pending or Approved; Pricing & Offers where Active is checked; Assignments where Status is not Done. Rows mode returns at most 100 rows and no next page: if exactly 100 come back, the answer may be cut off, so narrow the filter (by date or status) or use a view, and never treat it as the full list.
3. **SQL** (`mode: "sql"`): only when the question truly needs it (joining two databases, counting across thousands of rows) and nothing else can answer it. It may be unavailable on the owner's plan. If it fails, fall back to 1 or 2; never stop at the failure.

Fetching a database page returns its schema, not its rows. A page (Workforce Settings, Priorities, Brand & Tone) is read with fetch.

**Know the limits once per run.** If the connection offers a "tool access" check, call it once at the start, note which modes and tools are restricted, and use that for the whole run instead of discovering limits by failing. Don't assume a method is unlimited because it isn't SQL.

## 2. Read each thing once per run

The Chief of Staff (the skill running the conversation) reads the shared context once at the start: Workforce Settings, Priorities, Brand & Tone, Your Team, Pricing & Offers (active rows), Policies, FAQs, the open queue (Approvals and Assignments that aren't finished), and the schemas of the databases it will write to. It keeps them for the whole run and gives each team member only the parts that member needs. Team members don't re-read what they were given. Re-read only something this run itself changed.

Findings from an earlier run may be reused only when they carry a date and the source hasn't changed since (for example last week's competitor notes, marked "as of Nov 3"). Anything about money, deadlines, availability or the queue is read fresh.

## 3. Every read has one of four outcomes

| Outcome | When | How to say it |
|---|---|---|
| **Read** | The read worked and every page was retrieved | Use the rows |
| **Verified empty** | The read worked, every page was retrieved, and there are no rows | "No active offers in Pricing & Offers" |
| **Incomplete** | Some rows came back but not all (a page failed, rows mode returned exactly 100, a cursor stopped) | "Pricing & Offers: only part could be read" and treat the list as unknown beyond what was read |
| **Unavailable** | The read failed (allowance used up, error, timeout, not shared with the connection) | "Pricing & Offers could not be verified" |

Retry a failed read once, using the next method in section 1. Then record the outcome.

**Never turn Incomplete or Unavailable into "none".** Never write "there are no offers", "no approvals waiting", "no open tasks", "no customers" or "first run" unless the read was **Verified empty**.

**Critical sources.** If a source the run needs is Incomplete or Unavailable, the run is **Partial**, the report names the source and what that means ("Sales drafted no prices because Pricing & Offers could not be verified"), and nothing that depends on it is done by guessing:
- Pricing & Offers or Policies → no prices, terms or policy answers in drafts.
- Approvals → don't say how many decisions are waiting; don't add approvals that might be duplicates; say "the approval list could not be checked".
- Assignments → don't create follow-ups that might duplicate open ones; say the open-work list couldn't be checked.
- Briefings run history → don't treat the run as a first run; for inbox triage, don't move the bookmark (`references/inbox-coverage.md`).
- Customers & Leads → no claims about who is or isn't a customer.

In the run record, list each source read and its outcome in one line ("Notion: Settings read, Pricing read (8), Approvals read (5), Assignments unavailable").

## 4. Write sparingly
Create the run record once at the start and finish it once at the end; add Progress lines only at the main stages (at most three). Batch new rows into one call when the tool allows. After a write, trust the tool's answer; fetch a page back only when you need its link or the tool reported a problem.
