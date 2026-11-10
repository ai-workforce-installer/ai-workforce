# Reading Notion reliably and cheaply

The Business Brain must work on Notion's Free plan. Notion's connection offers several ways to read a database, and some are rationed by plan: on Free, SQL-style queries share a small workspace allowance that ordinary runs can use up. When a read fails, the team must never mistake "couldn't read" for "nothing there".

## 1. How to read a database (in this order)

1. **Saved view** (`mode: "view"` with the view's link): the default for routine reads. In live tests on Notion Free, saved views kept working after the plan's query allowance ran out, while both SQL and filtered rows stopped. The Business Brain has these views (added by setup or the 0.5.2 upgrade): Approvals **"Active approvals"**, Assignments **"Open work"**, Briefings **"Newest first"**, Pricing & Offers **"Active offers"**, Customers & Leads **"All contacts"**.
   - **Check what a view really shows** before relying on it: fetch the database once per run, read the view's filter and sort, and use it only if they match what you need (a view showing all offers is not an active-offers view). If the expected view is missing or its filter was changed, use another way below; never change the owner's views.
   - **Follow every page:** keep asking with the next cursor until the answer says there are no more.
2. **Rows with filters** (`mode: "rows"` with a structured `filter`, `sort` and `limit: 100`): when no suitable view exists. It may be rationed too, so don't assume it works when SQL has stopped. It returns at most 100 rows and no next page: if exactly 100 come back, the answer may be cut off, so narrow the filter or use a view, and never treat it as the full list.
3. **SQL** (`mode: "sql"`): only when the question truly needs it (joining two databases, counting across thousands of rows) and nothing else can answer it. It may be unavailable on the owner's plan; then the answer is Unavailable, not empty.

If a method fails, try the next one once; then record the outcome (section 3). Fetching a database page returns its schema and views, not its rows. A page (Workforce Settings, Priorities, Brand & Tone) is read with fetch.

**Know the limits once per run.** If the connection offers a "tool access" check, call it once at the start, note which modes and tools are restricted, and use that for the whole run instead of discovering limits by failing. Don't assume a method is unlimited because it isn't SQL.

## 2. Read each thing once per run

The Chief of Staff (the skill running the conversation) reads the shared context once at the start: Workforce Settings, Priorities, Brand & Tone, Your Team, Pricing & Offers (active rows), Policies, FAQs, the open queue (Approvals and Assignments that aren't finished), and the schemas of the databases it will write to. It keeps them for the whole run and gives each team member only the parts that member needs. Team members don't re-read what they were given. Re-read only something this run itself changed.

**Reusing a recent run's reads.** If another run finished in the last 3 hours and its record lists what it read, the stable pages (Brand & Tone, Your Team, Policies, FAQs, Company Profile) may be reused from it, marked "as of <time>", unless this run has reason to think they changed. Always read fresh (through views, which counts as fresh): Approvals, Assignments, Pricing & Offers, Workforce Settings, anything about money, security, deadlines or availability, and anything a claim to the owner depends on.

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
Create the run record once at the start and finish it once at the end; add a Progress line only when 30 minutes have passed since the run started or since the last Progress line, so another session never mistakes a working run for a stuck one; no other mid-run writes. Batch new rows into one call when the tool allows. After a write, trust the tool's answer; fetch a page back only when you need its link or the tool reported a problem.

**Collapsed sections (toggles).** Reports keep the owner's first screen short by folding the rest away. In Notion's own Markdown a toggle is written as a block: a line with `<toggle>`, the title on the next line, a blank line, the content, then `</toggle>`. Never use `<details>` (Notion saves it as plain text). If the connection's own guide says otherwise, follow the guide; if a toggle can't be created, use a plain heading in the same place.
