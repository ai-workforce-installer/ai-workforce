# Approval Queue (standard format for every agent and skill)

All approval requests go to one place: the **Approvals** database inside the owner's Business Brain in Notion. The owner clears it with the `review-approvals` skill.

## What goes in the queue
Only a decision the owner has to make: a price, discount, refund or term the Business Brain doesn't settle; a commitment to a date, a scope or a partnership; a calendar change with other people; anything about money, publishing or something that can't be undone. One row per decision.

**A reply draft is not a decision.** A reply the team could write from the Business Brain waits in Gmail drafts (or under Replies ready to copy), is listed in the report as ready, and is tracked as a Prepared row in the open-work queue (`references/run-tracking.md` section 6). The owner pressing Send is the approval, so it never gets an Approvals row. When a reply can't be written without a decision, queue the decision, and say in its Exact action which draft is waiting on it.

## Who writes to the queue
Specialists (subagents) never write to Notion: they return approval items in their report, in the item format below, under **Approvals Needed**. The orchestrator (the skill running in the main conversation, as Chief of Staff) writes them, after verifying each one and dropping any that fail.

## Item format (specialists return exactly this, one block per item)

```
- Item: <short title of the decision, e.g. "Refund $180 to Dana Lee for the late order">
  Department: <Operations | Marketing | Sales | Client Success | Finance | Chief of Staff> (custom team members: Chief of Staff, with "[Member name]" at the start of Item)
  Action type: <Send message | Spend money | Financial record | Calendar with others | Publish | Irreversible change | Other>
  Exact action: <exactly what would be done: recipient, subject, amount, record, new value>
  Why: <"Recommend: approve / hold / reject, because …", then one sentence>
  Risk if wrong: <one sentence>
  Reversible: <yes | no>
  Draft link: <the Gmail draft's checked viewUrl, the Briefings page holding the reply text, or a document link; or "none">
```

## Writing items to Notion (orchestrator)
When this run has an item to queue, follow `references/if-queuing-a-decision.md` (find the database, check for duplicates, create the row, read back its AP number, and when an old item may be set to Expired). A run with nothing to queue doesn't need it.

## The active queue
The active queue is every row with Status Pending or Approved. Briefings and reviews always account for all of them, not only new ones. Handed to you rows are counted with what is still waiting on the owner, not as decisions. Done, Rejected and Expired rows stay in the database as history: items leave the queue by their status, never by being deleted.
