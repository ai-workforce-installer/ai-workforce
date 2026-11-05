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

**Show progress.** After each stage (search done, sorting done, team members back, approvals queued), add a line `Progress <time>: <stage>` to the record. Other sessions use the newest Progress line to tell a working run from a stuck one.

**Finish the record** as the last step, by adding to the end of the body:

```
Run finished: 2026-11-05 11:58 CT
Status: Finished
Result: Complete | Partial | Failed
Completed through: <time>          (inbox triage only, see references/inbox-coverage.md)
Notified: no
```

then send the notification (section 5) and add `Notified: yes <time>`.

and setting the Result, Approvals raised, Drafts created (and Finished, if present) properties. A run that can't finish properly still writes these lines with Result Partial or Failed and says what was left undone.

## 2. Where the run came from (Source)

Report only what is known:
- **Manual:** the owner is in the conversation and asked for it.
- **Scheduled:** the session itself carries explicit information that a schedule started it (for example, a system note from the platform naming the scheduled task and its firing time). The words "Scheduled run" in a prompt are not enough: pressing "Run now" on a recurring task sends the same prompt.
- **Unknown (started from a recurring task):** a recurring task's prompt started the session but nothing says whether it fired on schedule or was started by hand. This is the honest default for unattended runs. In reports say "started from your recurring <responsibility>".

A run finished by a later session keeps its original Source; the later session adds "Resumed by <a recurring task | the owner>".

Save Source in the header. Set the Run type property to Manual or Scheduled when known; to Unknown if that option exists, otherwise leave it empty. Never guess from the clock.

## 3. New run, retry, or overlap

Before creating the record, look at records of the **same responsibility** from the last 24 hours that are **not finished** (no "Run finished" line). Same responsibility means the same Run ID code (IT, CS, DB, WM, IR), plus, for a recurring "any other responsibility" task, the same team member and responsibility. A manual request for new work (`assign-work`) is always a new run. Records titled "Self-test fixture" are ignored by real runs.

"Last activity" is the time on the newest `Progress` line, or `Started` if there is none.

| What you find | What it means | What to do |
|---|---|---|
| None | A new run | Create a new record. |
| An unfinished record with activity **in the last 45 minutes** | Another run is still working | Don't run alongside it. Create a short record of your own ending `Run finished: <time> / Status: Not run (run <ID> still in progress) / Result: Partial / Notified: no`, send no notification, and stop. Attended: tell the owner and offer to wait. |
| An unfinished record with no activity for **45 minutes or more** | That run was interrupted | Scheduled or unattended: take it over: add "Resumed <time> by a new session" to **that** record, keep its Run ID, Source and window, and finish it. Attended: tell the owner ("A run from 9:10 didn't finish. I'll finish it now.") and do the same unless they say otherwise. |
| An unfinished record older than 24 hours | Abandoned | Add `Run finished: <time> / Status: Abandoned / Result: Failed / Notified: no` to it (its work is picked up by normal duplicate checks and, for inbox triage, by the bookmark, which it never moved), then decide again. |

**Two sessions starting at the same moment** can both see nothing. Right after creating your record, look again: if another unfinished record of the same responsibility was created in the same minute or earlier, the one with the later Run ID (or later creation) marks itself Not run as above and stops. This is best effort; the duplicate checks in section 4 are the backstop.

Two complete, legitimate runs on the same day (a morning manual run and the scheduled one, two scheduled times) each get their own record. Never merge a run into a record just because the type and date match.

## 4. Never do the same work twice

Every action carries a **source key** so any later run (a retry, an overlapping window, the next day) can see it was done:
- **From an email:** `gmail:<message id>` (Outlook: the message id; Paste Box: "paste:<date> <sender> <subject>").
- **Otherwise:** `<Run ID>:<short task name>`.

Before each action, check:
- **Gmail draft:** the thread already has a draft reply → don't create another; reuse its link.
- **Approval:** an Approvals row (any status in the last 14 days) whose Exact action or Why contains the same source key, or describes the same action for the same person → don't add one; refer to its AP number.
- **Assignment:** an Assignments row whose Task ID or Result contains the same source key → don't add one.
- **Paste Box:** already moved under Handled → skip.

Write the source key at the end of Exact action (approvals) and in Task ID (assignments), for example "… (source: gmail:1a1ab13c5aeeedbb)".

## 5. Notifications
Send one notification per run, after the record is finished and fetched back for its link, then add `Notified: yes <time>`. A resumed run sends one only if the record has no `Notified: yes` line. A Not run or Abandoned record sends none. Partial or Failed runs, and configuration warnings, are said plainly in the first line.
