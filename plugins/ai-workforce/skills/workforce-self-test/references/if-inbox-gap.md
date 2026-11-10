# If the inbox has a gap, or the owner asks for another period

Read this only when the inbox window would start more than 7 days back, an "Inbox not scanned" row is open in the open-work queue, or the owner asked for a period of their own. Everything else about the window and the bookmark is in `references/inbox-coverage.md` section 1.

- **Long gaps:** if the start is more than 7 days back, scan the most recent 7 days as this run's window, and save the older days as an open-work item (`references/run-tracking.md` section 6): title "Inbox not scanned: <from> – <to>", Owner Chief of Staff, Status Planned, Source `inbox-gap:<from>`, Next action "Scan this period". One row per gap; if a row for an overlapping gap exists, update it instead. Never hide a gap: every report says "Older mail not yet scanned: <from> – <to>" until it's closed.
- **Catching up on a gap:** after its own window, each run scans the oldest 2 days of any open gap (same search, every page, same sorting and duplicate checks), then narrows the row's dates, or closes it (Status Done) once the whole gap is covered. If that catch-up search is incomplete, the row stays as it was. Gap catch-up never moves Completed through, and a run stays Complete if its own window was covered and the gap is tracked.
- **Owner-requested backfill** ("triage my inbox from Oct 20"): scan the requested period in 2-day pieces, closing or narrowing any gap row it covers; it moves Completed through only under the custom-period rule below.

**Custom periods.** A run over a period the owner chose moves the bookmark only if that period starts at or before the current Completed through; otherwise it leaves the bookmark alone.
