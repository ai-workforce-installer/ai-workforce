# Approval Queue (standard format for every agent and skill)

All approval requests go to one place: the **Approvals** database inside the owner's Business Brain in Notion. The owner clears it once a day with the `review-approvals` skill.

## Who writes to the queue
- **Specialists (subagents) do not write to Notion.** They return approval items in their report, in the item format below, under a heading **Approvals Needed**.
- **The orchestrator (the skill running in the main conversation, acting as Chief of Staff) writes them**, after verifying each one. This keeps one writer, avoids duplicates and lets the Chief drop items that fail verification.

## Item format (specialists return exactly this, one block per item)

```
- Item: <short title, e.g. "Send reply to Dana Lee about refund">
  Department: <Operations | Marketing | Sales | Client Success | Finance | Chief of Staff> (custom team members: Chief of Staff, with "[Member name]" at the start of Item)
  Action type: <Send message | Spend money | Financial record | Calendar with others | Publish | Irreversible change | Other>
  Exact action: <exactly what would be done: recipient, subject, amount, record, new value>
  Why: <one sentence>
  Risk if wrong: <one sentence>
  Reversible: <yes | no>
  Draft link: <link to the Gmail thread, the Briefings page holding the reply, or a document; otherwise "Gmail draft, subject: <subject>"; or "none">
```

## Writing items to Notion (orchestrator)
1. Find the Approvals database: search Notion for "Approvals" and pick the one whose parent is the Business Brain. Fetch it to get its `collection://` data source ID.
2. **Deduplicate.** Query rows with Status Pending, Approved or Handed to you, plus Done and Rejected rows from the last 14 days. If a row already describes the same action for the same person or record, do not add a new row; mention the existing AP number instead (and for a Rejected one, don't raise it again unless something new happened).
3. Create one row per new item with these properties:
   - `Item` (title), `Department`, `Action type`, `Exact action`, `Why`, `Risk if wrong`
   - `Reversible`: `__YES__` or `__NO__`
   - `Draft link`: a URL if you have one; otherwise leave empty and put "Gmail draft, subject: ..." (or "Reply in Briefings <date>, subject: ...") at the start of Exact action
   - `Status`: `Pending`
   - `Source run`: run name and date, e.g. `Daily briefing 2026-11-09 (scheduled)`
4. Read back the created rows to get each `AP` number, and use those numbers in the report as AP-<number> (AP-12, AP-13...), whether or not the database shows the AP prefix.
5. If Notion is not reachable, list the items in the report with temporary IDs (TEMP-1, TEMP-2) and say clearly that they were not queued.

## Expiry
Any orchestrator may set a Pending item older than 7 days to `Expired` when the underlying situation has clearly passed (for example a meeting date in the past). Note this in the report. Never delete rows.
