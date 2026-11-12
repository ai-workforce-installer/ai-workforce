# If the owner asks for live proof

Read this only when the owner says "prove it" or "run the live checks" (`workforce-self-test`). It is the live acceptance script: each check is something not yet proven on a real account.

With the owner present, on their real account, record each check in this run's record as **seen** (with the link that shows it), **not seen** (what was expected, what happened) or **couldn't test** (why, and what would make it testable). Never round up: a check that needs something that hasn't happened yet is "couldn't test".

**Limits, without exception.** Nothing is sent to anyone. No recurring task is created, changed or started. The only records written are this run's own, titled "Self-test proof <code>", closed as Dismissed at the end and left as history. Real work is looked at, never touched.

| # | Check | How, and what counts as seen |
|---|---|---|
| P1 | The 1.0.0 workspace upgrade | Read-only: Assignments has the nine new fields, and Connections has the `Sending` and `Work lives in` lines |
| P2 | One obligation, one row | Create a proof row with a Work key, then apply the duplicate check to a repeat of it: the row is found by its key and updated, none is added |
| P3 | Closing needs evidence | With the owner's yes, save one draft to their own address (never sent). Its proof row stays open: in Drafts it is ready, and nothing in Sent matches |
| P4 | The lock, in a run nobody watched | Read-only: a scheduled run's record lists a send, or a Trash, Spam or archive label call, as refused. None was tried: couldn't test |
| P5 | The desk | Show the proof row as one card with choices to tap: the owner answered by tapping, without an AP number |
| P6 | A reply sent on a yes | Read-only: a row closed as Sent whose receipt is in Sent (or the HighLevel conversation) and whose draft is gone; and one sent through "send all ready". None yet: couldn't test until the owner sends a real reply from the desk |
| P7 | The briefing on a phone | The newest Daily briefing opens with the four counts, has about 200 words outside its collapsed sections, and the owner confirms what their phone shows |
| P8 | Waiting people, and no nagging | Read-only, from the last three briefings and open work: someone waiting over a working day led Today, and no untouched item was named a third time |
| P9 | Runs that left no record | Read-only, from the task list and run history: each recurring job's last expected run left a record, or the briefing said so once. HighLevel was read in a scheduled run |
| P10 | Plain words | Steer the proof row: "snooze it until tomorrow", then "stop tracking this". One row, updated twice, each confirmed in one line |
| P11 | A quick look on request | "Check my newest 5 emails": its own record, labelled a quick look, and the bookmark is where it was |
| P12 | The morning run from setup | Read-only: one daily briefing task in the list, its Schedule line, and a Briefings row it produced |
| P13 | The first quiet day | Read-only: a briefing that handled nothing while `Work lives in` named an unconnected place led Worth knowing with the fix |
| P14 | A link that opens Claude | Put `claude://claude.ai/new?q=clear%20my%20desk` in this run's record and ask the owner to tap it in Notion on their phone, and say what happened |
| P15 | Earlier releases | Read-only, seen only where the records show it: an interrupted run finished by the next one; two inbox runs in one day; a missed notification caught up; an inbox gap over a week; a saved correction holding across scheduled runs |

**Report:** the table (check, result, evidence or reason) under "Live proof <date>" in this run's record, then for the owner: how many were seen, not seen and couldn't be tested, the one thing that would make the most checks testable, and the record's link.
