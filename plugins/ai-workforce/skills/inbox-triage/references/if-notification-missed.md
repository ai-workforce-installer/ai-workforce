# If an earlier report's notification never went out

Read this only when a finished record of the same responsibility from the last 8 days (long enough to reach the previous weekly run) has a last Notified line of `pending`, `failed` (not permanent) or `unknown`: finished work whose notification never went out, for example because the run stopped right after finishing or the tool failed.

**Catching up on missed notifications.** For each such record:
- Don't redo their work. Add one line to this run's notification: "Also ready: your <type> report from <time>: <link>". That counts as a new attempt for the older record.
- On the older record, add `Notification attempt <n> <time>: <what the tool reported>` (add-only), and update its Notified line to the outcome.
- **Limits:** at most 3 attempts per record. A failure the tool describes as permanent (no notification tool, notifications not allowed, an invalid recipient) is recorded as `failed (permanent)` and never retried; the report says the owner can open the report from the Briefings list.
- **Unknown outcomes** may be retried once, knowing it may produce a duplicate notification; say so in the attempt line ("retried after an unclear answer; may arrive twice").
- If this run sends no notification of its own (for example a Not run record), it sends none for older records either; the next run will.
