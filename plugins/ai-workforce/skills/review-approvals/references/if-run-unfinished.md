# If an unfinished run record exists

Read this only when `references/run-tracking.md` section 3 found a record of the same responsibility from the last 24 hours with no "Run finished" line.

"Last activity" is the time on the newest `Progress` line, or `Started` if there is none.

| What you find | What it means | What to do |
|---|---|---|
| None | A new run | Create a new record. |
| An unfinished record with activity **in the last 45 minutes** | Another run is still working | Don't run alongside it. Create a short record of your own ending `Run finished: <time> / Status: Not run (run <ID> still in progress) / Result: Partial / Notified: not requested`, send no notification, and stop. Attended: tell the owner and offer to wait. |
| An unfinished record with no activity for **45 minutes or more** | That run was interrupted | Scheduled or unattended: take it over: add "Resumed <time> by a new session" to **that** record, keep its Run ID, Source and window, and finish it. Attended: tell the owner ("A run from 9:10 didn't finish. I'll finish it now.") and do the same unless they say otherwise. |
| An unfinished record older than 24 hours | Abandoned | Add `Run finished: <time> / Status: Abandoned / Result: Failed / Notified: not requested` to it (its work is picked up by normal duplicate checks and, for inbox triage, by the bookmark, which it never moved), then decide again. |
