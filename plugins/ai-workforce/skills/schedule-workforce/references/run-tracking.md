# Run tracking: one record per run, safe retries, no duplicates

Every run of every skill (briefing, inbox triage, marketing plan, invoice review, assignment, self-test) keeps one record in the **Briefings** database. That record is how the team tells a new run from a retry, avoids doing work twice, and proves what happened. No other storage is used.

## 1. The run record

**Run ID:** `<code>-<YYYYMMDD>-<HHMM>` from the start time in the owner's time zone. Codes: DB daily briefing, IT inbox triage (all email), CS customer support triage (`process-customer-inquiries` on its own), WM weekly marketing, IR invoice review, AS assignment, ST self-test. Example: `IT-20261105-1146`. If a record with that ID already exists and is not this run, add `-2`, `-3`.

**Title** (the Briefing property): `<Type> <date> <HH:MM>`, for example "Inbox triage 2026-11-05 11:46". Customer-only runs use the Inbox triage type but the title "Customer support triage <date> <HH:MM>" and the CS code, and are never used for the inbox bookmark.

**Create the record when the run starts**, before any other work, with Result empty (or `Running` if that option exists). The body starts with this header, which is the source of truth on every version of the Business Brain:

```
Run ID: IT-20261105-1146
Started: 2026-11-05 11:46 CT
Source: Scheduled | Manual | Unknown (started from a recurring task)
Status: Running
Window: <start> – <end>            (inbox triage only)
```

If the Briefings database has the newer properties (`Run ID`, `Started`, `Finished`, `Completed through`; added by the 0.5.0 upgrade in `references/brain-upgrades.md`), fill them too. If it doesn't, the header alone is enough; never fail a run over a missing property.

**Show progress.** Add a line `Progress <time>: <stage>` when 30 minutes have passed since the start or the last Progress line, and also just before launching team members if 15 minutes or more have passed (the run can't write while it waits for them). No other mid-run writes. Other sessions use the newest Progress line to tell a working run from a stuck one.

**Check before finishing.** Verify, and fix or report anything that fails:
- **Sources:** each source the run needed and its outcome (`references/notion-access.md` section 3: read, verified empty, incomplete, unavailable).
- **Counts:** totals add up (for inbox triage, `references/inbox-coverage.md` section 5). Recompute them; don't copy them.
- **Window and bookmark** (inbox triage): the window used, and whether the bookmark moved and why.
- **Who ran:** which team members actually ran, and how (own agent, briefed assistant, or done directly).
- **Saved and checked:** each draft, approval and task this run saved, checked against the tool's answer.
- **Outstanding:** the open work this run leaves in the queue (section 6).
- **No duplicates:** each new draft, approval and task was checked against existing ones (section 4).

**Finish the record** as the last step, by adding to the end of the body:

```
Run finished: 2026-11-05 11:58 CT
Status: Finished
Result: Complete | Partial | Failed
Completed through: <time>          (inbox triage only, see references/inbox-coverage.md)
Usage: <n> tool calls, <n> team members launched, <n> emails or records processed, <n> minutes
Notified: pending
```

and set the Result, Approvals raised, Drafts created (and Finished, if present) properties. Then send the notification (section 5) and replace `Notified: pending` with what the tool reported.

Count tool calls and launches yourself; add model or token usage only if the platform shows it. Never estimate credits or cost. A run that can't finish properly still writes these lines with Result Partial or Failed and says what was left undone.

**Result means the same everywhere:** Complete = the whole job was done, every source it needed was read, and the checks above passed. Work saved in the open-work queue because it was past a per-run limit counts as done for this purpose (it's tracked, not dropped); work that couldn't be saved anywhere does not. Partial = useful work was done but something was skipped, unreadable, incomplete or unchecked (name it). Failed = nothing useful was produced. Never claim nothing was missed when a source, a page of results or a check could not be verified.

## 2. Where the run came from (Source)

Report only what is known:
- **Manual:** the owner is in the conversation and asked for it.
- **Scheduled:** the session itself carries explicit information that a schedule started it (for example, a system note from the platform naming the scheduled task and its firing time). The words "Scheduled run" in a prompt are not enough: pressing "Run now" on a recurring task sends the same prompt.
- **Unknown (started from a recurring task):** a recurring task's prompt started the session but nothing says whether it fired on schedule or was started by hand. This is the honest default for unattended runs. In reports say "started from your recurring <responsibility>".

A run finished by a later session keeps its original Source; the later session adds "Resumed by <a recurring task | the owner>".

**Never infer a duplicate schedule from timing.** A Monday task running on Thursday, or two briefings in one day, usually means someone pressed Run now. Only warn about duplicate recurring tasks when the scheduled-task list itself shows two tasks for the same responsibility. Whenever a recurring task starts, do the responsibility its prompt names, whatever the day or time.

Save Source in the header. Set the Run type property to Manual or Scheduled when known; to Unknown if that option exists, otherwise leave it empty. Never guess from the clock.

## 3. New run, retry, or overlap

Before creating the record, look at records of the **same responsibility** from the last 24 hours that are **not finished** (no "Run finished" line). Same responsibility means the same Run ID code (IT, CS, DB, WM, IR), plus, for a recurring "any other responsibility" task, the same team member and responsibility. A manual request for new work (`assign-work`) is always a new run. Records titled "Self-test fixture" are ignored by real runs.

"Last activity" is the time on the newest `Progress` line, or `Started` if there is none.

| What you find | What it means | What to do |
|---|---|---|
| None | A new run | Create a new record. |
| An unfinished record with activity **in the last 45 minutes** | Another run is still working | Don't run alongside it. Create a short record of your own ending `Run finished: <time> / Status: Not run (run <ID> still in progress) / Result: Partial / Notified: not requested`, send no notification, and stop. Attended: tell the owner and offer to wait. |
| An unfinished record with no activity for **45 minutes or more** | That run was interrupted | Scheduled or unattended: take it over: add "Resumed <time> by a new session" to **that** record, keep its Run ID, Source and window, and finish it. Attended: tell the owner ("A run from 9:10 didn't finish. I'll finish it now.") and do the same unless they say otherwise. |
| An unfinished record older than 24 hours | Abandoned | Add `Run finished: <time> / Status: Abandoned / Result: Failed / Notified: not requested` to it (its work is picked up by normal duplicate checks and, for inbox triage, by the bookmark, which it never moved), then decide again. |

**Two sessions starting at the same moment** can both see nothing. Right after creating your record, look again: if another unfinished record of the same responsibility was created in the same minute or earlier, the one with the later Run ID (or later creation) marks itself Not run as above and stops. This is best effort; the duplicate checks in section 4 are the backstop.

Two complete, legitimate runs on the same day (a morning manual run and the scheduled one, two scheduled times) each get their own record. Never merge a run into a record just because the type and date match.

## 4. Never do the same work twice

Every action carries a **source key** so any later run (a retry, an overlapping window, the next day) can see it was done:
- **From an email:** `gmail:<message id>` (Outlook: the message id; Paste Box: "paste:<date> <sender> <subject>").
- **Otherwise:** `<Run ID>:<short task name>`.

Before each action, check:
- **Gmail draft:** the thread already has a draft reply → don't create another; reuse its link.
- **Approval:** an Approvals row (any status in the last 14 days) whose Exact action or Why contains the same source key, or describes the same action for the same person → don't add one; refer to its AP number.
- **Assignment:** an Assignments row with the same source key (Source, Task ID or Result) and the same intended action, open or finished in the last 14 days (read the database's default view, not "Open work", which hides finished rows) → update or refer to it instead of adding one.
- **Paste Box:** already moved under Handled → skip.

Write the source key at the end of Exact action (approvals) and in Task ID (assignments), for example "… (source: gmail:18f3a2b4c5d6e7f8)".

## 5. Notifications
Send one notification per run, after the record is finished and fetched back for its link; the notification always includes that full Notion link as plain text. Then replace the `Notified: pending` line with what actually happened:
- `Notified: not requested` (no notification tool, or none due)
- `Notified: requested <time>, accepted by the tool`: the tool took the request. This is not proof the owner received it; never call it "delivered".
- `Notified: confirmed <time>`: only if the tool's answer explicitly says it was delivered.
- `Notified: failed <time>: <reason>`
- `Notified: unknown` (the tool gave no clear answer)

A resumed run sends a notification only if the record still says `Notified: pending`, `failed` or `unknown`. A Not run or Abandoned record sends none.

## 6. The open-work queue (unfinished work never disappears)

Work the team found but hasn't finished lives in the **Assignments** database, not in run reports, so it survives any gap between runs.
- **When to add a row:** something worth doing was found (an email needing a reply, a deadline, a document to review) and this run won't finish it, or it was prepared and now waits on the owner. Routine items don't get rows.
- **Fields:** Assignment (short title), Owner (team member), Status, Source (`gmail:<id>`, `notion:<page>`, `<Run ID>:<task>`), Next action (one line: who does what next), Date. If the database doesn't have Source and Next action yet (0.5.1 upgrade), put the source key in Task ID and start Result with the next action.
- **Status:** Planned (to do), In progress, Prepared (a draft or recommendation is ready and waiting on the owner), Handed to you (only the owner can do it, e.g. update payout details in their account), Blocked (missing access or information; say what's missing), Done, Failed. Without the 0.5.1 options, use Planned, In progress, Done or Failed and begin Result with "[Prepared]", "[Handed to you]" or "[Blocked]". Use Assignments for things only the owner can do (Handed to you); use Approvals only for decisions.
- **Every run starts with the queue:** read open Assignments (the "Open work" view if its filter matches, otherwise filtered rows where Status isn't Done or Failed; `references/notion-access.md`), whatever their age. Each run works only the rows for its own job (inbox triage: rows whose Source is an email; a recurring member task: that member's rows); the daily briefing lists the rest under what's waiting, without redoing them. Finish what can be finished now; leave the rest with an up-to-date Next action.
- **If the queue can't be read or written**, don't create rows that might duplicate it. List the unfinished items under **Carried over** in the run record instead (source key, owner, next action); the next run reads the last run's Carried over list and moves those items into the queue once it's readable.
- **Older rows:** unfinished rows are never closed because of their age. Rows from before 0.5.1 (no Source) that look like old logs rather than open work are listed once, in the daily briefing, under "Please check: old open tasks" with their links, so the owner can say which to close; nothing changes until they do. Rows the owner created are never changed without their say-so.
- **Deduplicate** by source and intended action: one row per source and action. Update the existing row (Status, Next action, Result) instead of adding another.
- **Close rows** only when the work is done, the owner confirmed they handled it, or the owner said it no longer matters (Status Done, with a one-line reason).
