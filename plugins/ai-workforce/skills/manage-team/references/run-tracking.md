# Run tracking: one record per run, safe retries, no duplicates

Every run of every skill (briefing, inbox triage, marketing plan, invoice review, assignment, self-test) keeps one record in the **Briefings** database. That record is how the team tells a new run from a retry, avoids doing work twice, and proves what happened. No other storage is used.

## 1. The run record

**Run ID:** `<code>-<YYYYMMDD>-<HHMM>` from the start time in the owner's time zone. Codes: DB daily briefing, IT inbox triage (all email), CS customer support triage (`process-customer-inquiries` on its own), WM weekly marketing, IR invoice review, AS assignment, ST self-test. Example: `IT-20261105-1146`. If a record with that ID already exists and is not this run, add `-2`, `-3`.

**Title** (the Briefing property): `<Type> <date> <HH:MM>`, for example "Inbox triage 2026-11-05 11:46". Customer-only runs use the Inbox triage type but the title "Customer support triage <date> <HH:MM>" and the CS code, and are never used for the inbox bookmark.

**Create the record when the run starts**, before any other work, with Result empty (or `Running` if that option exists). Its body is the run record, which is the source of truth on every version of the Business Brain:

```
Run ID: IT-20261105-1146
Started: 2026-11-05 11:46 CT
Source: Scheduled | Manual | Unknown (started from a recurring task)
Status: Running
Window: <start> – <end>            (inbox triage only)
```

**The owner's report goes above it.** Create the page with the run record inside a collapsed section (a toggle titled "Run record"; `references/notion-access.md` section 4). When the run ends, put the report at the top of the page, above that toggle, and add the finishing lines inside it (or just below it, if the tool can't add inside a toggle). Whoever opens the page sees what was handled first, never Run IDs or "Status: Running". Records from before 0.9.0 begin with the run record instead; both are read the same way.

Where Briefings has the `Run ID`, `Started`, `Finished` and `Completed through` properties, fill them too; the run record alone is enough, so never fail a run over a missing property.

**Show progress.** Add `Progress <time>: <stage>` when 30 minutes have passed since the start or the last such line, and just before launching team members if 15 or more have (the run can't write while it waits for them). No other mid-run writes: other sessions tell a working run from a stuck one by the newest Progress line.

**Check before finishing.** Verify, and fix or report anything that fails:
- **Sources:** each source the run needed and its outcome (`references/notion-access.md` section 3: read, verified empty, incomplete, unavailable).
- **Counts:** recomputed, not copied, so totals add up (inbox triage: `references/inbox-coverage.md` section 5, with the window and whether the bookmark moved and why).
- **Who ran:** which team members actually ran, and how (own agent, briefed assistant, or done directly).
- **Saved and checked:** each draft, approval and task this run saved, checked against the tool's answer and against existing ones (section 4).
- **Outstanding:** the open work this run leaves in the queue (section 6).

**Finish the record** as the last step, by adding to the end of the run record:

```
Run finished: 2026-11-05 11:58 CT
Status: Finished
Result: Complete | Partial | Failed
Completed through: <time>          (inbox triage only, see references/inbox-coverage.md)
Handled: <n> finished, <n> reply drafts ready, <n> prepared, <n> decisions raised | nothing: <the plain reason>
Usage: <n> tool calls, <n> team members launched, <n> emails or records processed, <n> minutes
Notified: pending
```

and set the Result, Approvals raised, Drafts created (and Finished, if present) properties. Then send the notification (section 5) and replace `Notified: pending` with what the tool reported.

Count tool calls and launches yourself; add model or token usage only if the platform shows it. Never estimate credits or cost. A run that can't finish properly still writes these lines with Result Partial or Failed and says what was left undone.

**Work handled** is how the owner judges a run: four counts, said first and never added into one number.
- **Finished:** verified outcomes only: open items closed on evidence or the owner's word (section 6). Updating a row, re-checking or carrying something forward is not closing it.
- **Ready for you:** what this run made and checked that now waits on the owner: reply drafts (a reply drafted but not sent is Ready, never Finished) and prepared pieces usable as they are (a meeting prep, the priority piece, a plan, a reconciliation, a research note).
- **Needs you:** everything waiting on the owner, new and old: decisions, ready replies and pieces, things handed to them. **Waiting on someone:** open rows whose next move is someone else's.
- **What never counts:** reading, searching, sorting, counting, re-checking and "nothing needed". A run that reviewed 148 emails and prepared nothing handled nothing.
- The record's **Handled** line holds this run's own counts (a record counts only its own work), or `Handled: nothing` with the plain reason when nothing was finished, made ready or raised. Never pad it or create work to fill it. Result and Handled are separate: a run can be Complete and have handled nothing.

**Result means the same everywhere:** Complete = the whole job was done, every source it needed was read, and the checks above passed. Work saved in the open-work queue because it was past a per-run limit counts as done for this purpose (it's tracked, not dropped); work that couldn't be saved anywhere does not. Partial = useful work was done but something was skipped, unreadable, incomplete or unchecked (name it). Failed = nothing useful was produced. Never claim nothing was missed when a source, a page of results or a check could not be verified.

## 2. Where the run came from (Source)

Report only what is known. Never guess from the clock.
- **Manual:** the owner is in the conversation and asked for it.
- **Scheduled:** the session itself says a schedule started it (for example a system note naming the scheduled task and its firing time). The words "Scheduled run" in a prompt are not enough: pressing "Run now" on a recurring task sends the same prompt.
- **Unknown (started from a recurring task):** a recurring task's prompt started the session, but nothing says whether it fired on schedule or was started by hand. This is the honest default for unattended runs. In reports say "started from your recurring <responsibility>".

A run finished by a later session keeps its Source and adds "Resumed by <a recurring task | the owner>". Save Source in the run record and, where the option exists, in Run type.

**Never infer a duplicate schedule from timing.** A Monday task running on Thursday, or two briefings in one day, usually means someone pressed Run now. Only warn about duplicate recurring tasks when the scheduled-task list itself shows two tasks for the same responsibility.

## 3. New run, retry, or overlap

Before creating the record, look at records of the **same responsibility** from the last 24 hours that are **not finished** (no "Run finished" line). Same responsibility means the same Run ID code (IT, CS, DB, WM, IR), plus, for a recurring "any other responsibility" task, the same team member and responsibility. A manual request for new work (`assign-work`) is always a new run. Records titled "Self-test fixture" are ignored by real runs.

None found: this is a new run, so create a new record. **One found: follow `references/if-run-unfinished.md`** before doing anything else. In short, a run that is still working (activity in the last 45 minutes) is never run alongside, and an interrupted one is finished, not started again.

**Two sessions starting at the same moment** can both see nothing. Right after creating your record, look again: if another unfinished record of the same responsibility was created in the same minute or earlier, the later one (by Run ID or creation) marks itself Not run (`references/if-run-unfinished.md`) and stops. This is best effort; section 4's duplicate checks are the backstop.

Two complete runs on the same day (a manual one and the scheduled one, two scheduled times) each get their own record. Never merge a run into a record because the type and date match.

## 4. Never do the same work twice

Every action carries a **source key** so any later run (a retry, an overlapping window, the next day) can see it was done:
- **From an email:** `gmail:<message id>` (Outlook: the message id; Paste Box: "paste:<date> <sender> <subject>").
- **Otherwise:** `<Run ID>:<short task name>`.

Before each action, check:
- **Gmail draft:** the thread already has a draft reply → don't create another; reuse its link.
- **Approval:** an Approvals row (any status in the last 14 days) whose Exact action or Why contains the same source key, or describes the same action for the same person → don't add one; refer to its AP number.
- **Assignment:** an Assignments row with the same work key (section 6), or the same source key (Source, Task ID or Result) and intended action, open or finished in the last 14 days (read the database's default view, not "Open work", which hides finished rows) → update or refer to it instead of adding one.
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

**A run inside another run sends none.** When the daily briefing does the inbox check itself (the morning run), the inbox record ends `Notified: not requested (included in <the briefing's Run ID>)` and the briefing's one notification covers both. "Not requested" is never a missed notification, so nothing catches it up later.

**A notification that never went out.** At the start of every run, look at finished records of the **same responsibility** from the last 8 days. If one's last Notified line is `pending`, `failed` (not permanent) or `unknown`, follow `references/if-notification-missed.md`: its link is added to this run's notification, without redoing its work.

## 6. The open-work queue (unfinished work never disappears)

Work the team found but hasn't finished lives in the **Assignments** database, not in run reports, so it survives any gap between runs. One row is one **obligation**: something the team, the owner or someone else still owes, tracked until it is closed with evidence.
- **When to add a row:** something worth doing was found and this run won't finish it, or it was prepared and now waits on the owner. Routine items don't get rows.
- **Fields:** Assignment (short title), Owner (team member), Status, Source (`gmail:<id>`, `notion:<page>`, `<Run ID>:<task>`), Next action (one line: who does what next), Date (when found). With the 1.0.0 upgrade (`references/brain-upgrades.md`): Work type, Due (only a deadline someone stated, never an invented one), Next check, Waiting on, Blocker, Done when (the outcome that closes it), Evidence (link), Closed as, Work key; detail goes in the row's body. Without a field, keep the same fact in Next action or Result (before 0.5.1: the source key in Task ID).
- **Work key: what is owed, not which message or run mentioned it.** `<where>:<who or what>:<what is owed>`, for example `gmail-thread:<id>:reply-refund`, `alert:<service>:<what is failing>`, `meeting:<date>:<who>:send-proposal`. Message IDs stay in Source as evidence; a Run ID is never an obligation's only identity. Before adding a row, look for the key (older rows: the same source and intended action) among open rows and rows closed in the last 14 days: a repeated alert, a later message, a retry or a later run about the same obligation **updates that row** (count, latest date, newest link). Still one row per source and action; separate promises in one thread are separate rows.
- **Status says who has the next move.** Planned or In progress: the team can do it now. Prepared (a draft or recommendation is ready) or Handed to you (only the owner can do it, e.g. update payout details in their account): waiting on the owner. Blocked: waiting on someone else or a missing input; Waiting on names who, Blocker what. Done or Failed: closed. Without those options (before 0.5.1): Planned, In progress, Done or Failed, with Result beginning "[Prepared]", "[Handed to you]" or "[Blocked]". Things only the owner can do go in Assignments (Handed to you); Approvals is only for decisions.
- **Nothing waits without a next action and a next check.** A stated deadline sets Next check. With none, use a suggested check time and call it that: the next working day for a person waiting on the owner, 2 working days for someone the owner is waiting on, 5 for a monitored issue, in the owner's time zone and working days. A snoozed row keeps its status and returns at its Next check. Checks happen in the morning run, never through a scheduled task per item.
- **Every run starts with the queue:** read open Assignments (the "Open work" view if its filter matches, otherwise filtered rows where Status isn't Done or Failed; `references/notion-access.md`), whatever their age. Each run works only the rows for its own job (inbox triage: rows whose Source is an email; a recurring member task: that member's rows); the daily briefing lists the rest under what's waiting, without redoing them. Finish what can be finished now, put a Blocked row whose input has arrived back to Planned, and leave the rest with an up-to-date Next action.
- **If the queue can't be read or written**, don't create rows that might duplicate it. List the unfinished items under **Carried over** in the run record instead (work key, owner, next action); the next run moves them into the queue once it's readable.
- **Older rows:** unfinished rows are never closed because of their age. Rows the owner created are never changed without their say-so.
- **Reply drafts and prepared pieces wait here, not in Approvals.** Each gets a Prepared row with its link in Next action (the checked Gmail draft, or the page that holds it), so later briefings can say what is still waiting without raising it again.
- **Closing needs evidence or the owner's word.** Set Done with Closed as, and the Evidence link or the owner's words in Result:
  - **Sent:** a matching message is in Sent, or the thread shows the owner's own reply. A draft that vanished proves nothing: look in Sent, and with no match ask once ("Did the reply to Dana go out?"); still unknown at the next check, close it as Unverified, never as sent.
  - **Completed:** the outcome in Done when can be seen (the payment succeeded, the document exists, the person confirmed), or the owner confirmed it. A sent reply proves sending, not that a customer case is resolved: the case stays open, waiting on the customer. A meeting's time passing proves neither that it was held nor that its actions were done: the prep closes as Unverified unless notes, a reply or the owner show it happened, and its actions stay open. An alert going quiet doesn't prove a repair: the issue stays open until a success notice or the owner's word.
  - **Cancelled** or **Dismissed:** the owner said so (their words), and it stays closed: only something materially new reopens it, never a repeat. **Superseded:** another row replaced it (name it).
  - **No connected app can show the outcome:** say so once ("I can't see whether that invoice was paid"), keep the row open with its Next check, and don't raise it again each day.
  Check all of this in one look at Drafts, Sent and the calendar per run, never draft by draft.
- **Waiting too long.** A waiting item the owner hasn't touched is named in at most two briefings, then becomes one card on the desk (`daily-executive-briefing`, "Don't nag"). They are never closed for age alone.
