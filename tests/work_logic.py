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
    vendor: str = ""
    amount: float = 0.0

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


SNOOZED = "Snoozed until"


def snooze(row, until_utc):
    """Snoozing keeps the status; the row simply returns at its next check. Its Next action says it is snoozed,
    because every waiting row has a next check and only this one should stay off the desk until then."""
    row.next_check, row.check_is_suggested = until_utc, False
    if not row.next_action.startswith(SNOOZED):
        row.next_action = (SNOOZED + "; then: " + row.next_action).rstrip(": ").rstrip(";")
    return row


def on_the_desk(queue, clock):
    """Open rows waiting on the owner, without the ones snoozed to a time that hasn't come.
    A suggested next check (when the team looks again) never hides a row: only a snooze does."""
    return [r for r in queue.open_rows() if r.next_move == "owner"
            and not (r.next_action.startswith(SNOOZED) and r.next_check and r.next_check > clock.now())]


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
    if not any(line.startswith("Work lives in:") for line in ws["connections"]):
        if not can_write:
            raise Interrupted("the Work lives in line is still to add")
        ws["connections"].append("Work lives in: not set")
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


def briefing_listing(row_listed_dates, today, waited_days=0):
    """Don't nag: an untouched item is named in at most two briefings; then it leaves the daily list
    and becomes one card on the desk. An item that has already waited a week leaves it too, whatever
    its Listed lines say (rows from before the lines existed have none).
    Returns (name it today?, desk card?, the row's Listed lines)."""
    if len(row_listed_dates) >= 2 or waited_days >= 7:
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


# ---- 1.0.0 step 4: plain-language control and the one-reply fast path ----

CONSEQUENTIAL = ("price outside the Business Brain", "refund", "legal matter", "calendar change with others", "spending")


def route_request(people=1, parts=1, facts_in_brain=True, involves=()):
    """"Reply to Priya saying Thursday at 11 works" is one reply to one person: no routing, no plan."""
    if people == 1 and parts == 1 and facts_in_brain and not set(involves) & set(CONSEQUENTIAL):
        return {"path": "fast", "plan table": False, "members launched": 0, "drafts": 1, "ready check": True,
                "assignments rows": 1, "lines in the answer": 2}
    return {"path": "full procedure", "plan table": parts > 1, "ready check": True}


def fast_path_answer(first_sentence, link, settings):
    """Two lines. The offer to send appears only when the owner chose to have approved replies sent."""
    second = "Say 'send it' and it goes." if sending_choice(settings) == SEND else "It's waiting in your drafts."
    return ["%s %s" % (first_sentence, link), second]


def resolve_reference(phrase, in_view, would_differ=True):
    """"It", "this", "that one": the item just shown. Ask only when several targets would change the result."""
    if len(in_view) == 1:
        return in_view[0]
    if len(in_view) > 1 and not would_differ:
        return in_view[0]
    return None                                      # ask which


def steer(row, words, clock, until=None, who=None):
    """The owner steers one item in plain words: the same row is updated, and one line confirms it."""
    said = words.lower()
    if "snooze" in said or "not today" in said:
        snooze(row, until or clock.working_days_from_now(3))
        return "Snoozed until %s: %s" % (clock.local(row.next_check).strftime("%A %I %p").replace(" 0", " "), row.title)
    if "waiting on" in said or "remind me" in said:
        wait_on(row, who or "them", clock, until)
        note = " (a suggested check)" if row.check_is_suggested else ""
        return "Waiting on %s; I'll look %s%s: %s" % (row.waiting_on, clock.local(row.next_check).strftime("%A"), note, row.title)
    if "already done" in said or "i sent it" in said or "already handled" in said:
        _close(row, "Completed", clock.now(), words=words)
        return "Closed, as you said: " + row.title
    if "stop tracking" in said:
        owner_cancels(row, clock, words)
        return "Stopped tracking: " + row.title
    return None                                      # not a steering phrase


PREFERENCE_KINDS = {
    "style": "save now, confirm after",              # "use this shorter style from now on"
    "working": "save now, confirm after",            # "finish what's waiting before starting something new"
    "hides items": "confirm first",                  # "stop flagging X", "not mine anymore": a wrong one buries mail
    "price or policy": "confirm first",
    "inferred": "confirm first",
    "sending or spending": "never saved: offer what the policy allows",
}


def save_preference(kind, stated_outright=True):
    if kind in ("style", "working") and not stated_outright:
        return "confirm first"                       # something the team noticed is offered, not saved
    return PREFERENCE_KINDS[kind]


# ---- 1.0.0 step 5: reach the work, and keep the team running after setup ----

WORK_LIVES_CHOICES = ("Gmail", "Outlook", "A CRM or help desk", "Text messages", "Social DMs", "Somewhere else")


def unreachable_work(work_lives_in, connected):
    """The places the owner said messages reach them that no connection reads."""
    return [p for p in work_lives_in if p not in connected]


def one_fix(place, registry_has_it=False, inbox_connected=True):
    """Setup's Finish names one fix in one line: connect it, forward it, or paste it."""
    if registry_has_it:
        return "connect %s" % place
    return ("forward those messages to your connected inbox" if inbox_connected
            else "paste them into your Paste Box")


def propose_goal(priorities, seen):
    """Quiet days with no goals: the one question proposes a goal drawn only from what the team saw.
    seen: {what was observed: how many times}. Returns (the question or None, what is saved now)."""
    if priorities or not seen:
        return None, []
    what, n = max(seen.items(), key=lambda kv: kv[1])
    return "%d customers asked about %s this month; want a goal for it this quarter?" % (n, what), []   # nothing saved until yes


def morning_run_in_setup(reply, tasks, default_time="7:30 AM", tool_available=True, owner_present=True,
                         can_run_now=True, briefing_row_appears=True):
    """The morning run is on by default, confirmed in one word. tasks: the first-line tags of the owner's
    existing scheduled tasks, paused ones included. Returns (the Schedule line's state, what happened)."""
    tag = "[AI Workforce task: daily-executive-briefing"
    if any(t.startswith(tag) for t in tasks):
        return "scheduled", "already there: offer to change its time, never a second task"
    if not tool_available:
        return "not available on this account", "said plainly; the owner can still ask for a briefing any time"
    r = reply.strip().lower().rstrip(".!")
    a_time = any(ch.isdigit() for ch in r) and ("am" in r or "pm" in r or ":" in r)
    if r in ("no", "no thanks", "not now", "don't"):
        return "declined", "nothing created"
    if not (r in ("ok", "okay", "yes", "sure", "do it", "sounds good") or a_time):
        return "proposed, not scheduled", "nothing created: only a clear yes or a time schedules it"
    tasks.append(tag + " | prompt version 1.0.0]")
    listed = any(t.startswith(tag) for t in tasks)                 # schedule-workforce's list check
    if not listed:
        return "proposed, not scheduled", "the task did not appear in the list"
    if not (owner_present and can_run_now):
        return "scheduled, confirmed", "test run offered, with the reason it wasn't started"
    if briefing_row_appears:
        return "scheduled, confirmed", "test run succeeded: its Briefings row exists"
    return "scheduled, confirmed", "test run started, but no Briefings row yet: not reported as a success"


def setup_finished(first_job_done, schedule_state):
    return first_job_done and schedule_state in ("scheduled, confirmed", "scheduled", "declined", "not available on this account")


# ---- 1.1.0 step 8: setup starts from what the owner wants off their plate (skills/setup-workforce/SKILL.md) ----

FIRST_JOBS = [   # (words in the owner's hand-off answer, the first job, the one source it needs)
    (("inbox", "email", "replies", "customers", "leads", "follow"), "the quick look", "email"),
    (("meeting", "schedul", "calendar"), "the next 48 hours and one meeting prep", "calendar"),
    (("invoice", "paid", "owed", "collect"), "the overdue review", "invoices"),
    (("marketing", "content", "newsletter", "posts"), "one finished piece for the main offer", "website"),
]


def first_job(hand_off, available):
    """One responsibility and the one source it needs. No answer, or nothing the team can do yet: the quick look
    (calendar if there is no email; pasted emails otherwise). Returns (job, source, said_it_cannot_do_the_ask)."""
    said = (hand_off or "").lower()
    for words, job, source in FIRST_JOBS:
        if any(w in said for w in words) and source in available:
            return job, source, False
    fallback = ("the quick look", "email") if "email" in available else \
               ("the next 48 hours and one meeting prep", "calendar") if "calendar" in available else \
               ("pasted emails", "paste")
    return fallback + (bool(said),)


def connect_checklist(chosen, connected, needed):
    """Every card still needed goes in one message, under one line that says what each app is for."""
    cards = [a for a in chosen if a not in connected]
    cards.sort(key=lambda a: (a != "Notion", a != needed))                 # Notion first, then the first job's source
    notes = ["%s: %s" % (a, "needed for your first job" if a in ("Notion", needed) else "optional, skip") for a in cards]
    line = "%d of %d connected" % (len([a for a in chosen if a in connected]), len(chosen))
    return cards, " · ".join([line] + notes)


def can_start_first_job(connected, needed):
    """The first job starts as soon as Notion and its one source work, without waiting for anything else."""
    return "Notion" in connected and (needed in connected or needed in ("paste", "website"))


def setup_opening(brain):
    """An existing Business Brain opens with where things stand, not with the questions again."""
    if not brain:
        return "questions"
    apps = len([v for v in brain.get("connections", {}).values() if v not in ("None", "not set", "")])
    job = "first job done" if brain.get("finished_runs") else "first job not done yet"
    return "Found your Business Brain: %d apps connected, %s. Carry on from here?" % (apps, job)


def first_success(result):
    """A connection check or an empty report is never the first success."""
    return result.get("kind") == "job" and result.get("saved_and_fetched_back") and result.get("items", 0) > 0


# ---- 1.1.0 step 14: honest about cost (skills/team-report/SKILL.md) ----

def typical_usage(usage_lines):
    """What a recurring job typically takes, from the Usage lines of its last runs: tool calls and minutes, never cost."""
    import re
    runs = [tuple(int(n) for n in m.groups()) for m in
            (re.search(r"Usage: (\d+) tool calls.*?(\d+) minutes", line) for line in usage_lines) if m]
    if not runs:
        return None                                   # nothing recorded: say nothing, never estimate
    calls, minutes = sorted(c for c, _ in runs), sorted(m for _, m in runs)
    return "about %d tool calls and %d minutes a run" % (calls[len(calls) // 2], minutes[len(minutes) // 2])


def sent_within_a_day(rows):
    """Of the replies the team prepared, how many went out within a day. None when the records can't show it."""
    replies = [r for r in rows if r.work_type == "Reply" and r.latest]
    if not replies:
        return None
    quick = [r for r in replies if r.closed_as == "Sent" and r.closed_at and r.closed_at - r.latest <= timedelta(days=1)]
    return "%d of %d replies went out within a day" % (len(quick), len(replies))


def notifications_may_not_arrive(last_notified, already_said=False):
    """Said once, when the last three finished runs all ended unknown or failed."""
    last_three = last_notified[-3:]
    bad = len(last_three) == 3 and all(n.startswith(("unknown", "failed")) for n in last_three)
    return bad and not already_said


# ---- 1.1.0 step 7: where the team saves its own work (references/notion-access.md section 4) ----

class TeamWork:
    """The owner's one private page for what the team makes, as far as writing goes."""

    def __init__(self, designated=True):
        self.designated = designated
        self.pages = {}                              # page id -> {"team": text the team wrote, "owner": the owner's own edits}
        self.fail_next_save = False

    def known_ids(self, queue):
        """Only IDs the team holds: the rows that link a page. A search result is never one."""
        return {r.evidence for r in queue.rows if r.evidence in self.pages}


def save_work_product(area, queue, row, text, who="Chief of Staff", page_id=None, found_by_search=False, long=True):
    """Returns where it was saved: "page:<id>", "briefing" (the fallback), or raises on a rule broken."""
    if who != "Chief of Staff":
        raise PermissionError("members are read-only in Notion: they return work to the Chief of Staff")
    if not area.designated or not long:
        return "briefing"                            # no Team work line, or a few lines: it stays in the run's page
    if page_id is None:
        page_id = "tw-%d" % (len(area.pages) + 1)    # a new page under Team work
        area.pages[page_id] = {"team": "", "owner": ""}
    elif found_by_search or page_id not in area.known_ids(queue):
        raise PermissionError("only page IDs the team knows: never a page a search turned up")
    if area.fail_next_save:
        area.fail_next_save = False
        return "not saved"                           # fetched back and it isn't there: never reported as saved
    area.pages[page_id]["team"] = text               # only the team's own part is replaced
    row.evidence = page_id
    return "page:" + page_id


# ---- 1.1.0 step 11: HighLevel beyond reading, attended only (skills/review-approvals/SKILL.md) ----

HIGHLEVEL_ON_A_YES = ("send reply", "add tag", "remove tag", "move stage")
HIGHLEVEL_NEVER = ("delete contact", "delete opportunity", "delete pipeline", "broadcast", "campaign", "workflow", "booking", "payment")


def highlevel_change(kind, answer, owner_present=True, who="Chief of Staff", connection_allows=True, said_before=False):
    """What happens to one HighLevel change on the desk. Returns (done, what the owner is told)."""
    if kind in HIGHLEVEL_NEVER or kind not in HIGHLEVEL_ON_A_YES:
        return False, "never: the owner does that in HighLevel themselves"
    if not owner_present or who != "Chief of Staff":
        return False, "read only here: it waits for the owner at the desk"
    if not is_a_yes(answer):
        return False, "nothing changed: that wasn't a yes to this item"
    if not connection_allows:
        return False, "" if said_before else "To let me do that, reconnect HighLevel and allow editing contacts and opportunities."
    return True, "done"


# ---- 1.1.0 step 9: a smaller inbox (references/inbox-coverage.md section 4; skills/review-approvals/SKILL.md) ----

NEEDS_YOU, DRAFT_READY = "Team/Needs you", "Team/Draft ready"


def team_labels(row, has_saved_draft=False):
    """The labels a thread should carry for one open-work row. A closed row carries none."""
    if not row.open or row.next_move != "owner":
        return set()
    return {NEEDS_YOU} | ({DRAFT_READY} if has_saved_draft else set())


def relabel(thread_labels, row, has_saved_draft=False):
    """Only the team's two labels are ever added or removed; whatever else is on the thread stays."""
    return (set(thread_labels) - {NEEDS_YOU, DRAFT_READY}) | team_labels(row, has_saved_draft)


def archive_card(routine, in_inbox, open_row_threads=()):
    """The desk's one card for yesterday's routine mail. `routine` is the inbox record's own list:
    (thread id, kind). Returns (the card's sentence, the ids a tap would archive), or (None, [])."""
    ids = [(t, kind) for t, kind in routine if t in in_inbox and t not in open_row_threads]
    if not ids:
        return None, []
    kinds = {}
    for _, kind in ids:
        kinds[kind] = kinds.get(kind, 0) + 1
    parts = ", ".join("%d %s" % (n, k) for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]))
    return "Archive the %d routine emails from yesterday? %s." % (len(ids), parts), [t for t, _ in ids]


def archive_on_tap(card_ids, tapped, owner_present=True):
    """Archived only on that tap, only with the owner there, and only the ids the card held."""
    return list(card_ids) if (tapped and owner_present) else []


# ---- 1.1.0 step 13: an optional urgent-only check (references/if-urgent-only.md) ----

URGENT_WORDS = (("security alert", ("new sign-in", "password reset", "suspicious", "security alert")),
                ("failed payment", ("payment failed", "failed payment", "card was declined", "could not be charged")),
                ("outage or failure", ("outage", "is down", "failed again", "service disruption")),
                ("deadline within 48 hours", ("due tomorrow", "expires today", "final notice", "ends tonight")))


def urgent_only_check(threads, bookmark, now, queue, enabled=True, not_the_owners=()):
    """Subjects only, from the bookmark to now. Returns what the run did: the bookmark it leaves, the rows it
    made or updated, drafts (always none), and the one notification it sends, or None when it stays quiet."""
    if not enabled:
        return None                                   # off by default: nothing runs
    seen, urgent = 0, []
    for t in threads:
        if not (bookmark < t["at"] <= now):
            continue
        seen += 1
        subject = t["subject"].lower()
        if any(name in subject for name in not_the_owners):
            continue                                  # the owner's corrections apply as always
        for kind, words in URGENT_WORDS:
            if any(wd in subject for wd in words):
                urgent.append((t, kind))
                break
    rows = [queue.record("alert:%s:%s" % (t["from"], kind), t["subject"], t["at"], work_type="Monitored issue", source=t["id"])
            for t, kind in urgent]
    record = {"coverage": "urgent-only", "completed_through": bookmark, "drafts": 0,
              "line": "Urgent-only check: %s in %d emails" % ("%d urgent" % len(urgent) if urgent else "nothing urgent", seen)}
    record["notified"] = "requested" if urgent else "not requested (nothing urgent)"
    notification = ("Urgent: " + "; ".join(t["subject"] for t, _ in urgent)) if urgent else None
    return {"record": record, "rows": rows, "notification": notification}


# ---- 1.1.0 step 6: cases and deliverables (references/if-case.md; the briefing's due-work step) ----

def continue_deliverable(queue, key, title, now):
    """"Finish this" continues the row that exists. A new generic piece each day is the failure this prevents."""
    row = queue.record(key, title, now, work_type="Deliverable")
    return row, row.count > 1                         # (the one row, whether it already existed)


def priority_choice(due_commitments, open_deliverables, next_goal_step):
    """The morning's one piece: a due commitment first, then a deliverable that exists, then a new step.
    Nothing is made for a count: with none of the three, there is no piece."""
    if due_commitments:
        return "finish", due_commitments[0]
    if open_deliverables:
        return "continue", open_deliverables[0]
    return ("new", next_goal_step) if next_goal_step else (None, None)


def after_meeting(queue, clock, meeting, notes=None):
    """The morning after a meeting with another person. Returns (follow-up draft or None, rows added, what to ask)."""
    if not notes:
        return None, [], "Paste a few notes from your call with %s and I'll draft the follow-up." % meeting["with"]
    rows = []
    for item in notes["action_items"]:
        row = queue.record("meeting:%s:%s:%s" % (meeting["date"], meeting["with"].lower(), item["what"]), item["what"], clock.now(),
                           work_type="Commitment", owner=item["owner"])
        row.due = item.get("due")                     # a date only when the notes give one
        if row.due is None:
            set_next_check(row, clock)                # otherwise a suggested check, called that
        rows.append(row)
    return "Follow-up to %s: %d action items" % (meeting["with"], len(rows)), rows, None


def handed_item_closes(row, messages, clock):
    """A Handed to you item closes on matching evidence the team can read, never by doing the step itself."""
    if row.status != "Handed to you":
        return False
    for m in messages:
        if m["kind"] == "payment succeeded" and m["vendor"] == row.vendor and m["amount"] == row.amount and m["at"] > row.latest:
            _close(row, "Completed", clock.now(), evidence=m["id"])
            return True
    return False


def case_status(research_done, outcome_seen):
    """Research is not a fix."""
    return "Resolved" if outcome_seen else ("Researched: answer prepared, not resolved" if research_done else "Open")


# ---- 1.1.0 step 5: commitments and waiting-on (references/if-commitments.md) ----

NOT_OBLIGATIONS = ("marketing", "receipt", "quoted", "invite", "idle idea")
PER_RUN_THREADS, PER_RUN_READ, FOLLOW_UPS_A_DAY = 50, 15, 2


def commitments_review(sent, checked_through, now, queue, clock, enabled=True, until=None):
    """One bounded pass over sent mail after the review's own checkpoint. `sent` is a list of threads:
    {"id", "at", "kind", "who", "what", "due" (a datetime the thread states, or None), "sure" (bool)}.
    Returns (rows added or updated, the new checkpoint). The inbox bookmark is not an argument: it is never touched."""
    if not enabled:
        return [], checked_through                    # off until the owner turns it on
    end = until or now
    window = sorted((t for t in sent if checked_through < t["at"] <= end), key=lambda t: t["at"])[:PER_RUN_THREADS]
    rows, read, new_checkpoint = [], 0, checked_through
    for t in window:
        if t["kind"] in NOT_OBLIGATIONS:
            new_checkpoint = t["at"]                  # seen and set aside: no row
            continue
        if read == PER_RUN_READ:
            break                                     # the rest waits; the checkpoint stops where reading stopped
        read += 1
        new_checkpoint = t["at"]
        owner_owes = t["kind"] in ("promise", "open customer work", "stalled follow-up")
        row = queue.record("gmail-thread:%s:%s" % (t["id"], t["what"]), t["what"], t["at"], source=t["id"],
                           work_type="Commitment" if owner_owes else "Waiting on someone")
        if row is None:
            continue
        if not owner_owes:
            row.status, row.waiting_on = "Blocked", t["who"]
        row.due = t["due"]                            # only a date the thread states
        if t["due"]:
            row.next_check, row.check_is_suggested = t["due"], False
        else:
            set_next_check(row, clock)                # "no date given": a suggested check, called that
        if not t.get("sure", True) and "may be a promise" not in row.title:
            row.title = "may be a promise: " + row.title
        rows.append(row)
    return rows, new_checkpoint


def follow_ups_due(queue, clock, replied=(), cancelled=(), drafted_today=0):
    """At a row's next check: a reply or a cancellation closes it and nothing is drafted; otherwise a follow-up,
    two a day at most, the oldest first."""
    drafts = []
    due = sorted((r for r in queue.open_rows() if r.work_type in ("Commitment", "Waiting on someone")
                  and r.next_check and r.next_check <= clock.now()), key=lambda r: r.latest)
    for row in due:
        if row.key in replied:
            _close(row, "Completed", clock.now(), evidence="the reply in the thread")
        elif row.key in cancelled:
            _close(row, "Cancelled", clock.now(), words="cancelled in the thread")
        elif drafted_today + len(drafts) < FOLLOW_UPS_A_DAY:
            drafts.append(row)
    return drafts


class CatchUp:
    """One catch-up, offered once, for one of the two kinds, with its own checkpoint, resumed across runs."""

    def __init__(self, now, days=7):
        self.start, self.end = now - timedelta(days=days), now
        self.checked_through = self.start
        self.offered, self.accepted = False, False

    def offer(self):
        if self.offered:
            return None                               # never offered twice
        self.offered = True
        return "Want me to go back over the last %d days of sent mail?" % (self.end - self.start).days

    def run(self, sent, queue, clock):
        if not self.accepted or self.done:
            return []                                 # only on the owner's yes, and never past the range
        rows, self.checked_through = commitments_review(sent, self.checked_through, clock.now(), queue, clock, until=self.end)
        if not [t for t in sent if self.checked_through < t["at"] <= self.end]:
            self.checked_through = self.end
        return rows

    @property
    def done(self):
        return self.checked_through >= self.end
