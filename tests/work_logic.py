"""Reference model of the 1.0.0 rules for finishing work.

The plugin's rules are plain language for Claude to follow. This module restates the ones added
in 1.0.0 as code, so the design can be tested against hard cases with a clock the tests control:

- open work as obligations with a stable work key, who has the next move, next checks and
  evidence-based closing            (skills/assign-work/references/run-tracking.md section 6)
- the add-only, resumable Assignments upgrade   (references/brain-upgrades.md, "Upgrade to 1.0.0")

Passing these tests shows the written procedure is sound. It does not show that Claude follows
it; the behaviour evals (with mocked apps) and the live proof mode are for that. See tests/README.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone

OPEN = ("Planned", "In progress", "Prepared", "Handed to you", "Blocked")
CLOSED_AS = ("Completed", "Sent", "Cancelled", "Dismissed", "Superseded", "Unverified")
WORK_TYPES = ("Task", "Reply", "Commitment", "Waiting on someone", "Customer case", "Deliverable", "Monitored issue")
RECENTLY_CLOSED = timedelta(days=14)


class Clock:
    """A clock the tests move. Time is kept in UTC; the owner's day is read in their own time zone
    (a fixed offset here: enough to show a check falls on the right local day and hour)."""

    def __init__(self, now_utc, utc_offset_hours=-6, working_days=(0, 1, 2, 3, 4), day_starts=time(9, 0)):
        self._now = now_utc.replace(tzinfo=timezone.utc) if now_utc.tzinfo is None else now_utc.astimezone(timezone.utc)
        self.tz = timezone(timedelta(hours=utc_offset_hours))
        self.working_days = working_days
        self.day_starts = day_starts

    @classmethod
    def at_local(cls, year, month, day, hour=9, minute=0, **kw):
        tz = timezone(timedelta(hours=kw.get("utc_offset_hours", -6)))
        return cls(datetime(year, month, day, hour, minute, tzinfo=tz), **kw)

    def now(self):
        return self._now

    def local(self, when=None):
        return (when or self._now).astimezone(self.tz)

    def advance(self, **delta):
        self._now += timedelta(**delta)
        return self._now

    def set_local(self, year, month, day, hour=9, minute=0):
        self._now = datetime(year, month, day, hour, minute, tzinfo=self.tz).astimezone(timezone.utc)
        return self._now

    def working_days_from_now(self, n):
        """The start of the owner's working day, n working days after today, as a UTC time."""
        day = self.local().date()
        while n > 0:
            day += timedelta(days=1)
            if day.weekday() in self.working_days:
                n -= 1
        return datetime.combine(day, self.day_starts, tzinfo=self.tz).astimezone(timezone.utc)

    def local_time(self, year, month, day, hour=9, minute=0):
        return datetime(year, month, day, hour, minute, tzinfo=self.tz).astimezone(timezone.utc)


# ---- the work key: what is owed, not which message or run mentioned it ----

def work_key(where, who_or_what, what_is_owed):
    parts = [str(p).strip().lower().replace(" ", "-") for p in (where, who_or_what, what_is_owed)]
    if not all(parts):
        raise ValueError("a work key names where, who or what, and what is owed")
    return ":".join(parts)


def is_a_work_key(key):
    """A Run ID (DB-20261105-0731) is never an obligation's only identity."""
    import re
    if not key or re.fullmatch(r"(DB|IT|CS|WM|IR|AS|ST)-\d{8}-\d{4}(-\d+)?(:.*)?", key):
        return False
    return key.count(":") >= 2


@dataclass
class Row:
    key: str
    title: str
    work_type: str = "Task"
    status: str = "Planned"
    owner: str = "Chief of Staff"
    sources: list = field(default_factory=list)      # message ids and run ids: evidence, not identity
    count: int = 1
    latest: datetime | None = None
    waiting_on: str = ""
    blocker: str = ""
    done_when: str = ""
    next_action: str = ""
    next_check: datetime | None = None
    check_is_suggested: bool = False
    due: datetime | None = None
    evidence: str = ""
    closed_as: str = ""
    closed_at: datetime | None = None
    result: list = field(default_factory=list)       # add-only notes
    asked_once: bool = False
    said_cant_tell: bool = False
    owner_created: bool = False

    @property
    def open(self):
        return self.status in OPEN

    @property
    def next_move(self):
        """Status says who has the next move."""
        if self.status in ("Planned", "In progress"):
            return "team"
        if self.status in ("Prepared", "Handed to you"):
            return "owner"
        if self.status == "Blocked":
            return self.waiting_on or "someone else"
        return "nobody"


class Queue:
    """The Assignments database, as far as open work goes."""

    def __init__(self, readable=True):
        self.rows = []
        self.readable = readable
        self.carried_over = []                       # used only when the queue can't be written

    def find(self, key, now):
        for r in self.rows:
            if r.key == key and (r.open or (r.closed_at and now - r.closed_at <= RECENTLY_CLOSED)):
                return r
        return None

    def record(self, key, title, now, source=None, work_type="Task", materially_new=False, **fields):
        """Something about an obligation turned up: a first mention, a repeated alert, a later
        message, a retry of the same run or a later run. One obligation, one row."""
        if not is_a_work_key(key):
            raise ValueError("%r is not a work key (a Run ID alone never is)" % key)
        if not self.readable:
            if key not in [c["key"] for c in self.carried_over]:
                self.carried_over.append({"key": key, "title": title})
            return None
        row = self.find(key, now)
        if row is None:
            row = Row(key=key, title=title, work_type=work_type, latest=now, **fields)
            if source:
                row.sources.append(source)
            self.rows.append(row)
            return row
        if source and source in row.sources:
            return row                               # a retry saw the same message again: nothing new
        if source:
            row.sources.append(source)
        if not row.open:
            if not materially_new:
                return row                           # closed stays closed (cancelled work above all): a repeat doesn't reopen it
            row.status, row.closed_as, row.closed_at = "Planned", "", None
            row.result.append("Reopened: something materially new arrived")
        row.count += 1
        row.latest = now
        return row

    def open_rows(self):
        return [r for r in self.rows if r.open]

    def due(self, clock):
        """What the morning run revisits: open rows whose next check has come."""
        return [r for r in self.open_rows() if r.next_check is None or r.next_check <= clock.now()]


# ---- nothing waits without a next action and a next check ----

SUGGESTED_WORKING_DAYS = {"owner": 1, "someone": 2, "monitored": 5}


def set_next_check(row, clock, stated_deadline=None):
    """A stated deadline sets the check. With none, a suggested time in working days, in the
    owner's time zone, labelled as suggested (never presented as a deadline)."""
    if stated_deadline is not None:
        row.due = stated_deadline
        row.next_check, row.check_is_suggested = stated_deadline, False
        return row
    if row.work_type == "Monitored issue":
        kind = "monitored"
    elif row.next_move == "owner":
        kind = "owner"
    else:
        kind = "someone"
    row.next_check = clock.working_days_from_now(SUGGESTED_WORKING_DAYS[kind])
    row.check_is_suggested = True
    return row                                       # row.due stays empty: no deadline is invented


def wait_on(row, who, clock, until=None, blocker=""):
    row.status, row.waiting_on, row.blocker = "Blocked", who, blocker
    row.next_action = "Check whether %s has answered" % who
    return set_next_check(row, clock, until)


def snooze(row, until_utc):
    """Snoozing keeps the status; the row simply returns at its next check."""
    row.next_check, row.check_is_suggested = until_utc, False
    return row


def input_arrived(row):
    """A blocked row whose missing input has turned up goes back to work the team can do now."""
    if row.status == "Blocked":
        row.status, row.blocker, row.waiting_on, row.next_check = "Planned", "", "", None
    return row


def missing_tracking(queue):
    """Waiting or blocked rows with no next action or no next check: there should be none."""
    return [r for r in queue.open_rows() if r.next_move != "team" and not (r.next_action and r.next_check)]


# ---- closing needs evidence or the owner's word ----

def _close(row, closed_as, now, evidence="", words=""):
    assert closed_as in CLOSED_AS
    row.status, row.closed_as, row.closed_at = "Done", closed_as, now
    row.evidence = evidence or row.evidence
    if words:
        row.result.append("Owner: " + words)
    return row


def check_reply(row, clock, draft_exists, sent_match=None, owner_replied_in_thread=False, owner_says=None):
    """A reply draft the owner was meant to send. Returns what the run does about it."""
    now = clock.now()
    if sent_match or owner_replied_in_thread:
        _close(row, "Sent", now, evidence=sent_match or "the owner's own reply in the thread")
        return "closed: sent"
    if owner_says == "sent":
        _close(row, "Sent", now, words="I sent it")
        return "closed: sent (owner's word)"
    if owner_says in ("dropped", "not needed"):
        _close(row, "Dismissed", now, words=owner_says)
        return "closed: dismissed"
    if draft_exists:
        return "still ready"                         # ready for the owner, never finished
    # The draft is gone and nothing in Sent matches: that proves nothing.
    if not row.asked_once:
        row.asked_once = True
        set_next_check(row, clock)
        return "ask once"
    _close(row, "Unverified", now)
    return "closed: unverified"


def after_reply_sent(case, clock, sent_link):
    """A sent reply proves sending, not that a customer case is resolved."""
    case.result.append("Reply sent: " + sent_link)
    case.status, case.waiting_on = "Blocked", "the customer"
    case.next_action = "See whether the customer is satisfied"
    set_next_check(case, clock)
    return case


def close_case(case, clock, customer_confirmed=False, owner_says=False, evidence=""):
    if customer_confirmed or owner_says:
        return _close(case, "Completed", clock.now(), evidence=evidence, words="resolved" if owner_says else "")
    return case


def meeting_time_passed(prep, actions, clock, notes_found=False, owner_says_held=False):
    """A meeting's time passing proves neither that it was held nor that its actions were done."""
    if notes_found or owner_says_held:
        _close(prep, "Completed", clock.now(), evidence="meeting notes" if notes_found else "",
               words="it was held" if owner_says_held else "")
    else:
        _close(prep, "Unverified", clock.now())
    return prep, [a for a in actions if a.open]      # the action items are untouched, whatever happened


def alert_went_quiet(issue, clock, success_notice=False, owner_says_fixed=False):
    """An alert going quiet doesn't prove a repair."""
    if success_notice or owner_says_fixed:
        return _close(issue, "Completed", clock.now(), evidence="success notice" if success_notice else "",
                      words="fixed" if owner_says_fixed else "")
    if issue.next_check is None or issue.next_check <= clock.now():
        set_next_check(issue, clock)
    return issue


def outcome_not_visible(row, clock):
    """No connected app can show the outcome: say so once, keep the row open, don't raise it daily.
    Returns the sentence to say, or None when it has been said already."""
    if row.next_check is None or row.next_check <= clock.now():
        set_next_check(row, clock)
    if row.said_cant_tell:
        return None
    row.said_cant_tell = True
    return "I can't see whether this is done: " + row.title


def owner_cancels(row, clock, words):
    return _close(row, "Cancelled", clock.now(), words=words)


def supersede(row, by, clock):
    row.result.append("Superseded by " + by.key)
    return _close(row, "Superseded", clock.now())


# ---- the add-only, resumable Assignments upgrade ----

NEW_PROPERTIES = ["Work type", "Due", "Next check", "Waiting on", "Blocker", "Done when", "Evidence", "Closed as", "Work key"]


class Interrupted(Exception):
    pass


def old_workspace():
    """An Assignments database as 0.9.0 left it, with things the owner added, plus the schedule."""
    return {
        "version": "0.6.0",
        "properties": ["Assignment", "Task ID", "Owner", "Status", "Source", "Next action", "Verification",
                       "Run type", "Result", "Date", "My priority"],                     # the last one is the owner's
        "status_options": ["Planned", "In progress", "Prepared", "Handed to you", "Blocked", "Done", "Failed", "On hold"],
        "views": {"Open work": 'FILTER "Status" IN ("Planned", "In progress", "Prepared", "Handed to you", "Blocked")',
                  "My board": "GROUP BY Owner"},
        "rows": [{"Assignment": "Reply to Dana", "Status": "Prepared", "Result": "Draft saved"},
                 {"Assignment": "Owner's own note", "Status": "On hold", "Result": ""}],
        "schedule": ["Daily briefing: every day 7:23 AM, scheduled, confirmed 2026-11-02"],
        "connections": ["Email: Gmail", "Calendar: Google Calendar", "Files: None", "Customer messages: None"],
    }


def upgrade_to_1_0_0(ws, stop_after=None, can_write=True):
    """Add each missing property, checking as it goes. Nothing else is touched. The version line
    moves only when all nine are there, so an interrupted upgrade carries on when run again."""
    added = []
    for name in NEW_PROPERTIES:
        if name in ws["properties"]:
            continue                                 # check, then add: already there (even if the owner's)
        if not can_write or (stop_after is not None and len(added) >= stop_after):
            raise Interrupted("stopped before adding %r; still to add: %s"
                              % (name, [n for n in NEW_PROPERTIES if n not in ws["properties"]]))
        ws["properties"].append(name)
        added.append(name)
    if not any(line.startswith("Sending:") for line in ws["connections"]):
        if not can_write:
            raise Interrupted("the Sending line is still to add")
        ws["connections"].append("Sending: not set")   # existing owners keep the old behaviour until they answer
    if all(n in ws["properties"] for n in NEW_PROPERTIES):
        ws["version"] = "1.0.0"
    return added


# ---- 1.0.0 step 2: the desk, and sending on the owner's yes (skills/review-approvals/SKILL.md) ----

SEND, LEAVE = "Send the ones I approve", "Leave them for me to send"
DESK_ORDER = ["reply", "decision", "prepared", "handed", "still-want"]      # people waiting first
ACKNOWLEDGEMENTS = ("looks good", "ok", "okay", "fine", "thanks", "ok thanks", "great", "sure", "all good", "👍")


@dataclass
class Card:
    kind: str                       # reply | decision | prepared | handed | still-want
    who: str
    subject: str = ""
    text: str = ""
    recipient: str = ""
    thread: str = ""
    attachments: tuple = ()
    waiting_since: datetime | None = None
    draft_id: str = ""
    channel: str = "gmail"          # gmail | highlevel | outlook | paste
    row: Row | None = None
    case: Row | None = None         # the customer case this reply belongs to, if any
    invoice: str = ""               # set for a payment reminder

    def shown(self):
        """What the owner saw on the card and said yes to."""
        return (self.recipient, self.thread, self.text, tuple(self.attachments))


def desk(cards):
    """Everything waiting on the owner as one list: people waiting first, the longest wait first.
    It takes the lists only: the desk never searches the inbox."""
    far_future = datetime.max.replace(tzinfo=timezone.utc)
    return sorted(cards, key=lambda c: (DESK_ORDER.index(c.kind), c.waiting_since or far_future))


def is_a_yes(answer):
    """"Looks good" or "ok" is never a send, for one item or many."""
    a = answer.strip().lower().rstrip(".!")
    if a in ACKNOWLEDGEMENTS:
        return False
    return a in ("send", "send it", "yes, send it", "yes send it", "approve", "send all", "yes, send all", "yes")


def sending_choice(settings):
    """Existing owners keep the old behaviour until they answer the one question."""
    return settings.get("Sending") if settings.get("Sending") in (SEND, LEAVE) else None


class Timeout(Exception):
    pass


class Outbox:
    """A mailbox (or a HighLevel conversation list) as far as sending goes, with failures the tests choose."""

    def __init__(self, allows_send=True):
        self.drafts = {}             # draft_id -> (recipient, thread, text, attachments)
        self.sent = []               # (recipient, thread, text, attachments)
        self.newer_message = set()   # threads where the person wrote again after the card was made
        self.fail = None             # None | "timeout after sending" | "timeout before sending" | "error"
        self.allows_send = allows_send
        self.send_calls = 0
        self.deleted = []

    def add_draft(self, card):
        self.drafts[card.draft_id] = card.shown()

    def send(self, recipient, thread, text, attachments):
        self.send_calls += 1
        if not self.allows_send:
            raise PermissionError("the connection does not allow sending")
        if self.fail == "error":
            raise RuntimeError("the app said no")
        if self.fail == "timeout before sending":
            raise Timeout()
        self.sent.append((recipient, thread, text, tuple(attachments)))
        if self.fail == "timeout after sending":
            raise Timeout()
        return "sent:%d" % len(self.sent)

    def find_sent(self, shown):
        return "sent:%d" % (self.sent.index(shown) + 1) if shown in self.sent else None

    def delete_draft(self, draft_id):
        self.drafts.pop(draft_id, None)
        self.deleted.append(draft_id)


def send_on_yes(card, outbox, settings, clock, answer="send", attended=True, started_by_task=False,
                as_agent=None, invoice_unpaid=None):
    """What happens when the owner answers a reply card. Returns the outcome in a few words."""
    if started_by_task or not attended:
        return "refused: this conversation was started by a recurring task. Open a new chat and say 'clear my desk'"
    if as_agent:
        return "refused: team members never send"
    if not is_a_yes(answer):
        return "nothing sent: ask which"
    if sending_choice(settings) is None:
        return "ask once: send the ones I approve, or leave them for me to send?"
    if sending_choice(settings) == LEAVE or card.channel in ("outlook", "paste"):
        if card.row:
            card.row.status = "Handed to you"
        return "left for the owner to send"
    if card.invoice and invoice_unpaid is not True:
        return "not sent: the invoice is paid, disputed or unclear"
    # 1. re-read right before sending
    current = outbox.drafts.get(card.draft_id)
    if current is None:
        return "not sent: the draft is gone (follow the closing rule)"
    if current != card.shown() or card.thread in outbox.newer_message:
        return "show the card again as it now stands: a fresh yes is needed"
    # 2. send exactly what was shown, once
    try:
        receipt = outbox.send(*card.shown())
    except PermissionError:
        return "not sent: give the text to copy, and say once how to allow sending"
    except Timeout:
        # 3. unknown outcome: look in Sent before anything else, never retry blind
        receipt = outbox.find_sent(card.shown())
        if receipt is None:
            return "unknown: not in Sent. Say so and ask before trying again"
    except RuntimeError:
        return "not sent: the app refused it"
    # 4. receipt, move the row, remove the team's own leftover draft
    if card.row:
        card.row.result.append("Sent on the owner's yes: %s to %s" % (receipt, card.recipient))
        _close(card.row, "Sent", clock.now(), evidence=receipt)
    if card.case:
        after_reply_sent(card.case, clock, receipt)
    outbox.delete_draft(card.draft_id)
    return "sent"


def send_all_ready(listed, outbox, settings, clock, answer="send all", invoice_unpaid=None, **where):
    """One yes to a card listing every ready reply sends exactly the items listed, one at a time,
    each with its own re-read and receipt. Nothing that joined the desk afterwards is sent."""
    if not is_a_yes(answer):
        return {"went": [], "did not": [(c.who, "nothing sent: ask which") for c in listed]}
    went, did_not = [], []
    for card in list(listed):                        # the list as it was shown, not the desk as it is now
        unpaid = (invoice_unpaid or {}).get(card.invoice) if card.invoice else None
        outcome = send_on_yes(card, outbox, settings, clock, invoice_unpaid=unpaid, **where)
        (went if outcome == "sent" else did_not).append(card.who if outcome == "sent" else (card.who, outcome))
    return {"went": went, "did not": did_not}


# ---- 1.0.0 step 3: a briefing that leads with what matters (skills/daily-executive-briefing/SKILL.md) ----

def working_days_waited(clock, since_utc):
    """Whole working days between when someone wrote and now, in the owner's own days."""
    day, today, n = clock.local(since_utc).date(), clock.local().date(), 0
    while day < today:
        day += timedelta(days=1)
        if day.weekday() in clock.working_days:
            n += 1
    return n


def today_lines(cards, clock, other_priorities=()):
    """Up to three lines for Today. A person who has waited more than one working day comes first,
    with their wait; if they wrote again since the draft was made, the line says so."""
    waiting = [(working_days_waited(clock, c.waiting_since), c) for c in cards if c.kind == "reply" and c.waiting_since]
    lines = []
    for days, c in sorted([x for x in waiting if x[0] > 1], key=lambda x: -x[0]):
        again = "followed up again" if getattr(c, "followed_up", False) else "has waited %d days" % days
        lines.append("%s %s; reply ready" % (c.who, again))
    return (lines + list(other_priorities))[:3]


def follow_up_arrived(card, new_message_text):
    """Someone wrote again while their reply sat unsent: the same draft is refreshed to answer the new
    message. It stays a ready reply: no Approvals row is created for it."""
    card.followed_up = True
    card.text = card.text + "\n(answers: %s)" % new_message_text
    return {"drafts": 1, "approvals rows created": 0, "kind": card.kind}


def needs_you_count(approvals_pending, ready_replies, prepared_pieces, handed_to_owner):
    """Everything waiting on the owner, not only Approvals rows."""
    return approvals_pending + ready_replies + prepared_pieces + handed_to_owner


def briefing_listing(row_listed_dates, today):
    """Don't nag: an untouched item is named in at most two briefings; then it leaves the daily list
    and becomes one card on the desk. Returns (name it today?, desk card?, the row's Listed lines)."""
    if len(row_listed_dates) >= 2:
        return False, True, row_listed_dates
    return True, False, row_listed_dates + [today]


def optional_work_allowed(prepared_waiting):
    """Clear first: with more than five prepared items waiting, the morning run makes no new optional work."""
    return prepared_waiting <= 5


def reply_draft_limit(waiting_now, waiting_at_last_briefing, cleared_all_yesterday):
    """The cap follows how fast the owner clears them: 5 to start, 8 after a day they cleared the
    queue, 3 while it grows."""
    if cleared_all_yesterday:
        return 8
    if waiting_at_last_briefing is not None and waiting_now > waiting_at_last_briefing:
        return 3
    return 5


def missed_runs(expected, records, clock, already_said=()):
    """expected: {responsibility: when the window of its last expected run began}.
    records: {responsibility: time of its newest record, or None}. A job with no record since that
    window began is said once until fixed, and only ever by a run that did happen: nothing here
    claims an alert the failed scheduler couldn't send."""
    out = []
    for job, window_began in sorted(expected.items()):
        last = records.get(job)
        if (last is None or last < window_began) and job not in already_said:
            out.append("Your %s hasn't left a record since %s" % (job, clock.local(last).strftime("%A") if last else "it was set up"))
    return out
