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
  Why: <"Recommend: approve / hold / reject, because …", then one sentence>
  Risk if wrong: <one sentence>
  Reversible: <yes | no>
  Draft link: <the Gmail draft's checked viewUrl, the Briefings page holding the reply text, or a document link; or "none">
```

## Writing items to Notion (orchestrator)
1. Find the Approvals database: search Notion for "Approvals" and pick the one whose parent is the Business Brain. Fetch it to get its `collection://` data source ID.
2. **Deduplicate.** Read the Approvals database's unfiltered "Decision board" view (or its default view; "Active approvals" hides finished rows), otherwise filtered rows (`references/notion-access.md`): rows with Status Pending, Approved or Handed to you, plus Done and Rejected rows from the last 14 days. If the list can't be read completely, don't add a new item that might be a duplicate: put it in the report as "to queue once the approval list can be checked". If a row already has the same source key (`references/run-tracking.md` section 4) or describes the same action for the same person or record, do not add a new row; mention the existing AP number instead (and for a Rejected or Done one, don't raise it again unless something materially new happened: a new security incident, money moving, a new deadline on the owner, or a person asking or saying something new. Another automated email repeating the same alert is not new). Before creating any row, also check the owner's saved corrections (`references/owner-corrections.md` section 5): an item they rule out is never queued. Older rows stay as they are: a row is never closed or rewritten because of the dedupe check.
3. Create one row per new item with these properties:
   - `Item` (title), `Department`, `Action type`, `Exact action`, `Why`, `Risk if wrong`
   - `Reversible`: `__YES__` or `__NO__`
   - `Draft link`: a URL if you have one; otherwise leave empty and put "Gmail draft, subject: ..." (or "Reply in Briefings <date>, subject: ...") at the start of Exact action
   - `Status`: `Pending`
   - `Source run`: the Run ID and title, e.g. `IT-20261109-1146 Inbox triage 2026-11-09 11:46`
   - End `Exact action` with the source key, e.g. `(source: gmail:<message id>)`
4. Read back the created rows to get each `AP` number, and use those numbers in the report as AP-<number> (AP-12, AP-13...), whether or not the database shows the AP prefix.
5. If Notion is not reachable, list the items in the report with temporary IDs (TEMP-1, TEMP-2) and say clearly that they were not queued.

## The active queue
The active queue is every row with Status Pending or Approved. Briefings and reviews always show all of them, not only new ones. Handed to you rows are shown separately ("Still on your list"). Done, Rejected and Expired rows stay in the database as history and never appear in the active queue. That's how "already handled" and "not mine" items leave the queue: by their status, never by deleting them.

## Expiry and duplicates
Any orchestrator may set a Pending item to `Expired` when the underlying situation has clearly passed (for example a meeting date in the past), or when it duplicates an older open item: then add "Duplicate of AP-<n>" to Owner note (never overwriting what's there). Note this in the report. Never delete rows.
