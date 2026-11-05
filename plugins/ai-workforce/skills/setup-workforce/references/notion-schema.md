# Business Brain structure (build exactly this)

Root page: **Business Brain** (icon 🧠). Everything below is a direct child of it.
Never delete or overwrite existing pages or databases. For an existing Business Brain, the add-only upgrade steps in `assign-work/references/brain-upgrades.md` come first. When upgrading, add any missing page (for example Paste Box) and any missing section of Workforce Settings (for example Connections) without touching what is already there. If a v0.1 Business Brain exists (plain pages named "Assignments log" and "Briefings"), keep their content and rename them to "Assignments log (v0.1 archive)" and "Briefings (v0.1 archive)" so the new databases can use the standard names. Then add the databases below alongside them.

## Pages (create with notion-create-pages, parent = Business Brain page)

Use the template text in `page-templates.md` for each page's starting content.

| Page | Icon |
|---|---|
| Workforce Settings | ⚙️ |
| Company Profile | 🏢 |
| Priorities | 🎯 |
| Policies | 📜 |
| Brand & Tone | 🗣️ |
| FAQs | ❓ |
| Paste Box | 📥 |
| Your Team | 👥 |

## Databases (create with notion-create-database, parent = Business Brain page)

### Approvals
Description: Everything the AI team wants to do that needs your yes. The team adds items; only you decide.
```
CREATE TABLE ("Item" TITLE, "AP" UNIQUE_ID PREFIX 'AP', "Status" SELECT('Pending':yellow, 'Approved':green, 'Handed to you':blue, 'Rejected':red, 'Done':gray, 'Expired':brown), "Department" SELECT('Chief of Staff':blue, 'Operations':default, 'Marketing':pink, 'Sales':green, 'Client Success':yellow, 'Finance':red), "Action type" SELECT('Send message':blue, 'Spend money':red, 'Financial record':orange, 'Calendar with others':purple, 'Publish':pink, 'Irreversible change':red, 'Other':gray), "Exact action" RICH_TEXT, "Why" RICH_TEXT, "Risk if wrong" RICH_TEXT, "Reversible" CHECKBOX, "Draft link" URL, "Source run" RICH_TEXT, "Requested" CREATED_TIME, "Decided" DATE, "Owner note" RICH_TEXT)
```
If Notion rejects this with "Unique ID prefix is already in use" (the AP prefix can exist only once per workspace, for example when the template was also duplicated), create the same table with `"AP" UNIQUE_ID` (no prefix). Items are called AP-<number> either way.
Then add a board view named "Decision board": `GROUP BY "Status" SHOW EMPTY; SHOW "AP", "Department", "Action type", "Exact action", "Draft link"; CARD LAYOUT compact`

### Assignments
Description: Every task the Chief of Staff hands to a manager, with its result and whether it was verified.
```
CREATE TABLE ("Assignment" TITLE, "Task ID" RICH_TEXT, "Owner" SELECT('Chief of Staff':blue, 'Operations':default, 'Marketing':pink, 'Sales':green, 'Client Success':yellow, 'Finance':red), "Status" SELECT('Planned':gray, 'In progress':blue, 'Done':green, 'Failed':red), "Verification" SELECT('Verified':green, 'Unverified':yellow, 'Failed':red), "Run type" SELECT('Manual':blue, 'Scheduled':purple), "Result" RICH_TEXT, "Date" DATE)
```

### Briefings
Description: Every report your AI team produces, newest first.
```
CREATE TABLE ("Briefing" TITLE, "Date" DATE, "Type" SELECT('Daily briefing':blue, 'Inbox triage':yellow, 'Invoice review':red, 'Weekly marketing':pink, 'Assignment':green, 'Self-test':gray), "Run type" SELECT('Manual':blue, 'Scheduled':purple), "Result" SELECT('Complete':green, 'Partial':yellow, 'Failed':red), "Approvals raised" NUMBER, "Drafts created" NUMBER)
```
Then add a table view named "Newest first": `SORT BY "Date" DESC`

### Pricing & Offers
Description: What you sell and the price rules. Sales may only quote what is here; anything else goes to Approvals.
```
CREATE TABLE ("Offer" TITLE, "Price" NUMBER FORMAT 'dollar', "Billing" SELECT('One-time':blue, 'Monthly':green, 'Annual':purple, 'Free':gray), "Lowest allowed price" NUMBER FORMAT 'dollar', "Max discount %" NUMBER, "Includes" RICH_TEXT, "Link" URL, "Active" CHECKBOX, "Notes" RICH_TEXT)
```

### Customers & Leads
Description: People you sell to and support. Sales and Client Success read this to know who is who.
```
CREATE TABLE ("Name" TITLE, "Company" RICH_TEXT, "Email" EMAIL, "Stage" SELECT('Lead':gray, 'Contacted':blue, 'Proposal':purple, 'Customer':green, 'At risk':orange, 'Lost':red), "Value" NUMBER FORMAT 'dollar', "Last contact" DATE, "Next step" RICH_TEXT, "Notes" RICH_TEXT)
```

## Root page content
Put the "Start here" text from `page-templates.md` at the top of the Business Brain page (insert at start; never replace existing content).
