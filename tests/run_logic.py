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
    last_progress: datetime | None = None
    search_complete: bool = False
    pending: list = field(default_factory=list)
    code: str = "IT"


# ---- run-tracking.md section 3: new run, retry, or overlap ----
def decide(records, rtype, now, code="IT"):
    """Return ('new', None) | ('overlap', rec) | ('resume', rec)."""
    for r in records:                       # older than 24h and unfinished -> abandoned
        if r.rtype == rtype and r.finished is None and now - r.started > timedelta(hours=RETRY_LOOKBACK_HOURS):
            r.finished, r.result = now, "Failed"
    open_recs = [r for r in records
                 if r.rtype == rtype and r.finished is None and r.code == code]
    if not open_recs:
        return "new", None
    rec = max(open_recs, key=lambda r: r.started)
    last = max(rec.started, rec.last_progress or rec.started)
    if now - last < timedelta(minutes=OVERLAP_MINUTES):
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
    done = [r for r in records if r.rtype == "Inbox triage" and r.code == "IT"
            and r.finished and r.completed_through]
    return max((r.completed_through for r in done), default=None)


def next_window(records, now):
    """Return (start, end, gap) where gap is (gap_start, gap_end) or None."""
    cp = last_checkpoint(records)
    if cp is None:
        # first run of the bookmark; reach back to an earlier quick look's window so nothing is skipped
        looks = [r.window[0] for r in records if getattr(r, "coverage", "").startswith("quick look")]
        return min([now - FIRST_RUN_WINDOW] + looks), now, None
    start = cp - WINDOW_OVERLAP
    if now - start > MAX_WINDOW:
        return now - MAX_WINDOW, now, (start, now - MAX_WINDOW)
    return start, now, None


class OpenWork:
    """The open-work queue (Assignments rows). Survives any gap between runs.

    key -> status; one row per (source, action). readable=False simulates
    Notion being unavailable.
    """
    def __init__(self):
        self.rows = {}
        self.readable = True
        self.writes = 0
        self.gaps = {}        # "inbox-gap:<from>" -> [from, to]; an "Inbox not scanned" row

    def add_gap(self, start, end):
        """One row per gap; an overlapping gap updates the existing row."""
        if not self.readable:
            raise ConnectionError("Assignments unavailable")
        for key, (gs, ge) in self.gaps.items():
            if start <= ge and end >= gs:
                self.gaps[key] = [min(gs, start), max(ge, end)]
                return key
        key = f"inbox-gap:{start:%Y-%m-%d %H:%M}"
        self.gaps[key] = [start, end]
        self.rows[key] = "Planned"
        return key

    def open_items(self):
        if not self.readable:
            raise ConnectionError("Assignments unavailable")
        return [k for k, st in self.rows.items() if st not in ("Done", "Failed")]

    def upsert(self, key, status):
        if self.rows.get(key) != status:
            self.rows[key] = status
            self.writes += 1


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


GAP_CATCHUP = timedelta(days=2)


def search_all(mailbox, start, end):
    """Every page, one retry per failed page. Returns (messages, complete)."""
    found, page, retried = [], 0, set()
    while True:
        try:
            chunk, more = mailbox.search(start, end, page)
        except ConnectionError:
            if page not in retried and page not in mailbox.retry_used:
                retried.add(page)
                mailbox.retry_used.add(page)
                continue
            return found, False
        found += chunk
        if not more:
            return found, True
        page += 1


def catch_up_gap(queue, mailbox):
    """After the run's own window: scan the oldest 2 days of the oldest open gap.
    Returns the messages found (empty if incomplete; the row is then unchanged)."""
    open_gaps = sorted((v[0], k) for k, v in queue.gaps.items() if queue.rows.get(k) != "Done")
    if not open_gaps:
        return []
    _, key = open_gaps[0]
    gs, ge = queue.gaps[key]
    piece_end = min(gs + GAP_CATCHUP, ge)
    found, complete = search_all(mailbox, gs, piece_end)
    if not complete:
        return []
    queue.gaps[key][0] = piece_end
    if piece_end >= ge:
        queue.rows[key] = "Done"
    return found


def backfill(queue, mailbox, start, end, records, actions):
    """Owner-requested backfill: the whole requested period, in 2-day pieces."""
    t, complete = start, True
    already = set().union(*[r.handled for r in records]) | {k for _, k in actions}
    while t < end:
        found, ok = search_all(mailbox, t, min(t + GAP_CATCHUP, end))
        if not ok:
            complete = False
            break
        for m in found:
            key = f"gmail:{m.id}"
            if m.important and key not in already:
                actions.append(("draft", key)); already.add(key)
        for k, (gs, ge) in list(queue.gaps.items()):        # narrow or close covered gaps
            if gs >= t and gs < min(t + GAP_CATCHUP, end):
                queue.gaps[k][0] = min(t + GAP_CATCHUP, end, ge)
                if queue.gaps[k][0] >= ge:
                    queue.rows[k] = "Done"
        t = min(t + GAP_CATCHUP, end)
    return complete


def open_gaps(queue):
    return [tuple(v) for k, v in queue.gaps.items() if queue.rows.get(k) != "Done"]


def triage(records, mailbox, now, code="IT", draft_limit=5, actions=None, queue=None, other_sources_ok=True):
    """Run inbox triage per the written rules. Returns the record.

    actions: shared list of (kind, source_key) actually created, so tests can
    check nothing is created twice across runs.
    """
    actions = [] if actions is None else actions
    queue = OpenWork() if queue is None else queue
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
        start, end, gap = next_window(records, now)
        rec = Record(make_run_id(code, now, records), "Inbox triage", now, window=(start, end))
        records.append(rec)
        if gap:
            try:
                queue.add_gap(*gap)                   # durable: an "Inbox not scanned" row
            except ConnectionError:
                rec.carried_over.append(f"inbox-gap {gap[0]:%Y-%m-%d} - {gap[1]:%Y-%m-%d}")

    already = set().union(*[r.handled for r in records])
    existing_actions = {key for _, key in actions}
    try:
        todo = [k for k in queue.open_items() if not k.startswith("inbox-gap:")]
        queue_ok = True
    except ConnectionError:
        todo, queue_ok = [], False
    # the last finished run's Carried over list (queue was unreadable then) is read back
    prev = [r for r in records if r is not rec and r.rtype == "Inbox triage" and r.code == code and r.finished]
    if prev:
        for key in max(prev, key=lambda r: r.finished).carried_over:
            if key.startswith("gmail:") and key not in todo:
                todo.append(key)
                if queue_ok:
                    queue.upsert(key, "Planned")      # moved into the queue once it's readable

    found, complete = search_all(mailbox, start, end)
    if complete and queue_ok:
        found += catch_up_gap(queue, mailbox)       # never moves Completed through

    important = [f"gmail:{m.id}" for m in found if m.important]
    worklist = todo + [k for k in important if k not in todo]
    drafted = 0
    for key in worklist:
        if key in already or key in existing_actions:
            continue                               # never process twice
        if drafted >= draft_limit:
            if queue_ok:
                queue.upsert(key, "Planned")       # stays in the queue, any gap
            else:
                rec.carried_over.append(key)       # reported; nothing that might duplicate
            continue
        actions.append(("draft", key))
        rec.handled.add(key)
        if queue_ok:
            queue.upsert(key, "Done")
        drafted += 1

    rec.finished = now
    rec.search_complete = complete
    rec.pending = [k for k in (queue.rows if queue_ok else {})
                   if queue.rows[k] not in ("Done", "Failed") and not k.startswith("inbox-gap:")]
    # The bookmark follows search coverage, with unfinished work kept durably (queue or Carried over);
    # the overall Result also depends on the queue and every other source the run needed.
    if complete:
        rec.completed_through = end
    else:
        rec.completed_through = prev_cp              # bookmark stays put
    rec.result = "Complete" if (complete and queue_ok and other_sources_ok) else "Partial"
    rec.gaps_open = open_gaps(queue) if queue_ok else []
    if not rec.notified:
        rec.notified = True
    return rec


# ---- run-tracking.md section 3: two sessions starting in the same minute (best effort) ----
def start_together(records, now, rtype="Inbox triage", code="IT"):
    """Both sessions look before either writes, so both see nothing; each creates its record, then
    looks again, and the later Run ID marks itself Not run. Returns the sessions that proceed."""
    seen = [decide(records, rtype, now, code)[0] for _ in range(2)]
    assert seen == ["new", "new"]
    mine = []
    for _ in range(2):
        r = Record(make_run_id(code, now, records), rtype, now, code=code)
        records.append(r); mine.append(r)
    proceed = []
    for r in mine:                                         # the look-again step
        rivals = [o for o in records if o is not r and o.rtype == rtype and o.code == code
                  and o.finished is None and o.started <= r.started]
        if any(o.run_id < r.run_id for o in rivals):
            r.finished, r.result = now, "Partial"           # Status: Not run (run <ID> still in progress)
        else:
            proceed.append(r)
    return proceed


# ---- workforce-self-test 6c: the live checks, restated ----
def bookmark_check(records):
    """PASS if every finished IT run moved Completed through only when its search was complete."""
    done = sorted((r for r in records if r.rtype == "Inbox triage" and r.code == "IT" and r.finished),
                  key=lambda r: r.finished)
    prev = None
    for r in done:
        if not r.window:                                 # older record: only its bookmark is known
            prev = r.completed_through
            continue
        if r.search_complete and r.completed_through != r.window[1]:
            return False
        if not r.search_complete and r.completed_through != prev:
            return False
        prev = r.completed_through
    return True


def pagination_check(mailbox, start, end, cap=5):
    for page in range(cap):
        _, more = mailbox.search(start, end, page)
        if not more:
            return "PASS"
    return "incomplete (stopped at 5 pages)"


# ---- run-tracking.md section 5: catching up on missed notifications ----
MAX_NOTIFY_ATTEMPTS = 3
NOTIFY_LOOKBACK = timedelta(days=8)   # reaches the previous weekly run


@dataclass
class Report:
    """A finished record as far as notifications are concerned."""
    run_id: str
    code: str
    finished: datetime
    notified: str = "pending"     # pending | accepted | confirmed | failed | failed (permanent) | unknown | not requested
    attempts: list = field(default_factory=list)
    work_done: int = 1            # times its work ran; recovery must never raise it


def notify_due(r, code, now):
    if r.code != code or r.finished is None or now - r.finished > NOTIFY_LOOKBACK:
        return False
    if r.notified in ("accepted", "confirmed", "not requested", "failed (permanent)"):
        return False
    if len(r.attempts) >= MAX_NOTIFY_ATTEMPTS:
        return False
    if r.notified == "unknown" and any("unclear" in a for a in r.attempts):
        return False                                  # an unknown outcome is retried once only
    return r.notified in ("pending", "failed", "unknown")


def send_with_recovery(current, older, code, now, notifier, sends_own=True):
    """One notification for this run, carrying the links of older reports still due.

    notifier(links) -> accepted | confirmed | failed | failed_permanent | unknown
    Returns the outcome (None if nothing was sent).
    """
    if not sends_own:
        return None                                   # a Not run record sends nothing, for anyone
    due = [r for r in older if notify_due(r, code, now)]
    outcome = notifier([current.run_id] + [r.run_id for r in due])
    state = {"failed_permanent": "failed (permanent)"}.get(outcome, outcome)
    for r in [current] + due:
        note = f"attempt {len(r.attempts) + 1}: {outcome}"
        if r is not current and r.notified == "unknown":
            note += " (retried after an unclear answer; may arrive twice)"
        r.attempts.append(note)
        r.notified = state
    return outcome


# ---- inbox-coverage.md section 6: quick look (first assignment during setup) ----
QUICK_LOOK_THREADS = 50
QUICK_LOOK_DRAFTS = 3


def quick_look(records, mailbox, now, actions=None):
    """Newest 50 threads of the last 24 hours, at most 3 drafts. A normal IT record that never sets
    Completed through and is never 'comprehensive', so the bookmark doesn't move."""
    actions = [] if actions is None else actions
    rec = Record(make_run_id("IT", now, records), "Inbox triage", now, window=(now - FIRST_RUN_WINDOW, now))
    records.append(rec)
    newest, page = [], 0
    while len(newest) < QUICK_LOOK_THREADS:
        chunk, more = mailbox.search(now - FIRST_RUN_WINDOW, now, page)
        newest += chunk
        if not more:
            break
        page += 1
    newest = newest[:QUICK_LOOK_THREADS]
    rec.coverage = f"quick look (newest {len(newest)} threads)"
    rec.reviewed = len(newest)
    for m in [m for m in newest if m.important][:QUICK_LOOK_DRAFTS]:
        key = f"gmail:{m.id}"
        actions.append(("draft", key))
        rec.handled.add(key)
    rec.finished = now
    rec.completed_through = None             # "Completed through: not moved (quick look)"
    rec.search_complete = False              # intentionally limited: never comprehensive
    rec.result = "Partial"
    return rec


def owner_summary(rec, total_in_window):
    """What the owner is told: never 'all email' unless the whole window was searched."""
    if getattr(rec, "coverage", "").startswith("quick look"):
        return (f"I looked at your {rec.reviewed} newest emails. "
                f"I haven't gone through the rest of the last 24 hours yet.")
    return f"Reviewed all {total_in_window} emails in the window."
