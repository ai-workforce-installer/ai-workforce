"""Reference model of the run-tracking and inbox-checkpoint rules.

The plugin's rules are written in plain language for Claude to follow
(skills/assign-work/references/run-tracking.md and
skills/inbox-triage/references/inbox-coverage.md). This module restates the same
rules as code so the design itself can be tested against hard cases: retries,
overlaps, partial scans, pagination failures and duplicate actions.

Passing these tests shows the written procedure is sound. It does not show that
Claude follows it in a live run; that needs the live self-test (see tests/README.md).
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

OVERLAP_MINUTES = 45      # run-tracking.md section 3
RETRY_LOOKBACK_HOURS = 24
WINDOW_OVERLAP = timedelta(minutes=15)   # inbox-coverage.md section 1
MAX_WINDOW = timedelta(days=7)
FIRST_RUN_WINDOW = timedelta(hours=24)
PAGE_SIZE = 50


@dataclass
class Record:
    """One Briefings record (one run)."""
    run_id: str
    rtype: str
    started: datetime
    finished: datetime | None = None
    result: str | None = None
    window: tuple | None = None
    completed_through: datetime | None = None
    handled: set = field(default_factory=set)
    carried_over: list = field(default_factory=list)
    notified: bool = False
    resumed: int = 0


# ---- run-tracking.md section 3: new run, retry, or overlap ----
def decide(records, rtype, now):
    """Return ('new', None) | ('overlap', rec) | ('resume', rec)."""
    open_recs = [r for r in records
                 if r.rtype == rtype and r.finished is None
                 and now - r.started <= timedelta(hours=RETRY_LOOKBACK_HOURS)]
    if not open_recs:
        return "new", None
    rec = max(open_recs, key=lambda r: r.started)
    if now - rec.started < timedelta(minutes=OVERLAP_MINUTES):
        return "overlap", rec
    return "resume", rec


def make_run_id(code, started, records):
    base = f"{code}-{started:%Y%m%d-%H%M}"
    taken = {r.run_id for r in records}
    rid, n = base, 2
    while rid in taken:
        rid, n = f"{base}-{n}", n + 1
    return rid


# ---- inbox-coverage.md section 1: window and checkpoint ----
def last_checkpoint(records):
    done = [r for r in records if r.rtype == "Inbox triage" and r.finished and r.completed_through]
    return max((r.completed_through for r in done), default=None)


def next_window(records, now):
    """Return (start, end, gap) where gap is (gap_start, gap_end) or None."""
    cp = last_checkpoint(records)
    if cp is None:
        return now - FIRST_RUN_WINDOW, now, None
    start = cp - WINDOW_OVERLAP
    if now - start > MAX_WINDOW:
        return now - MAX_WINDOW, now, (start, now - MAX_WINDOW)
    return start, now, None


def carried_over(records, now):
    keys = []
    handled = set().union(*[r.handled for r in records]) if records else set()
    for r in records:
        if r.rtype == "Inbox triage" and now - r.started <= MAX_WINDOW:
            keys += [k for k in r.carried_over if k not in handled and k not in keys]
    return keys


@dataclass
class Message:
    id: str
    at: datetime
    labels: tuple = ("INBOX",)
    important: bool = False   # would be prioritized by the sorting rules


class Mailbox:
    """All Mail search, newest first, 50 per page; can fail on a given page."""
    def __init__(self, messages, fail_on_page=None):
        self.messages = sorted(messages, key=lambda m: m.at, reverse=True)
        self.fail_on_page = fail_on_page
        self.retry_used = set()

    def search(self, start, end, page):
        """Pages are 0-based. Ignores labels: All Mail, every tab."""
        if self.fail_on_page is not None and page == self.fail_on_page:
            raise ConnectionError("page failed")
        hits = [m for m in self.messages if start <= m.at < end]
        chunk = hits[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
        more = (page + 1) * PAGE_SIZE < len(hits)
        return chunk, more


def triage(records, mailbox, now, code="IT", draft_limit=5, actions=None):
    """Run inbox triage per the written rules. Returns the record.

    actions: shared list of (kind, source_key) actually created, so tests can
    check nothing is created twice across runs.
    """
    actions = [] if actions is None else actions
    kind, rec = decide(records, "Inbox triage", now)
    if kind == "overlap":
        r = Record(make_run_id(code, now, records), "Inbox triage", now,
                   finished=now, result="Partial")
        records.append(r)
        return r
    prev_cp = last_checkpoint(records)
    if kind == "resume":
        rec.resumed += 1
        start, end = rec.window
    else:
        start, end, _gap = next_window(records, now)
        rec = Record(make_run_id(code, now, records), "Inbox triage", now, window=(start, end))
        records.append(rec)

    already = set().union(*[r.handled for r in records])
    existing_actions = {key for _, key in actions}
    todo = carried_over([r for r in records if r is not rec], now)

    found, complete, page = [], True, 0
    while True:
        try:
            chunk, more = mailbox.search(start, end, page)
        except ConnectionError:
            if page not in mailbox.retry_used:      # retry a failed page once
                mailbox.retry_used.add(page)
                continue
            complete = False
            break
        found += chunk
        if not more:
            break
        page += 1

    important = [f"gmail:{m.id}" for m in found if m.important]
    queue = todo + [k for k in important if k not in todo]
    drafted = 0
    for key in queue:
        if key in already or key in existing_actions:
            continue                               # never process twice
        if drafted >= draft_limit:
            if key not in rec.carried_over:
                rec.carried_over.append(key)
            continue
        actions.append(("draft", key))
        rec.handled.add(key)
        drafted += 1

    rec.finished = now
    if complete:
        rec.completed_through = end
        rec.result = "Complete"
    else:
        rec.completed_through = prev_cp              # bookmark stays put
        rec.result = "Partial"
    if not rec.notified:
        rec.notified = True
    return rec
