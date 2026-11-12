"""Reference model of the Notion-reading, counting, judgment and secrets rules.

Restates skills/assign-work/references/notion-access.md, team-roles.md
("Work economically", "Judgment before preparing anything"), run-modes.md
("Passwords, keys and other secrets") and inbox-coverage.md section 5 as code,
with a mocked Notion connector, so the rules can be tested against hard cases.
It tests the design, not Claude's behaviour in a live run.
"""
import re

ROWS_CAP = 100


class QuotaExhausted(Exception):
    pass


class MockNotion:
    """A database with `rows`, readable three ways, each able to fail.

    sql_quota: SQL calls left (Free plan allowance). view_page_size: rows per
    view page. fail: set of modes that error (e.g. {"rows"}), or "all".
    """
    def __init__(self, rows, sql_quota=0, view_page_size=50, fail=(), has_view=True,
                 allowance_exhausted=False):
        self.rows = list(rows)
        self.sql_quota = sql_quota
        self.view_page_size = view_page_size
        self.fail = set(fail) if fail != "all" else {"view", "rows", "sql"}
        self.has_view = has_view
        self.allowance_exhausted = allowance_exhausted   # Free plan: rows + SQL stop, views work
        self.calls = []

    def view(self, cursor=0):
        self.calls.append(("view", cursor))
        if "view" in self.fail or not self.has_view:
            raise ConnectionError("view failed")
        chunk = self.rows[cursor:cursor + self.view_page_size]
        nxt = cursor + self.view_page_size
        return chunk, (nxt if nxt < len(self.rows) else None)

    def rows_mode(self, flt=lambda r: True):
        self.calls.append(("rows", None))
        if self.allowance_exhausted:
            raise QuotaExhausted("query allowance used up")
        if "rows" in self.fail:
            raise ConnectionError("rows failed")
        return [r for r in self.rows if flt(r)][:ROWS_CAP]

    def sql(self):
        self.calls.append(("sql", None))
        if "sql" in self.fail:
            raise ConnectionError("sql failed")
        if self.sql_quota <= 0 or self.allowance_exhausted:
            raise QuotaExhausted("SQL allowance used up")
        self.sql_quota -= 1
        return list(self.rows)


def read_database(db, flt=lambda r: True, need_sql=False):
    """Return (outcome, rows). outcome: read | verified_empty | incomplete | unavailable."""
    # Views first, then filtered rows. SQL only when the question truly needs it.
    methods = ["view", "rows"] + (["sql"] if need_sql else [])
    for m in methods:
        try:
            if m == "view":
                if not db.has_view:
                    continue
                out, cur = [], 0
                while True:
                    try:
                        chunk, cur = db.view(cur)
                    except ConnectionError:
                        if out:
                            return "incomplete", [r for r in out if flt(r)]
                        raise
                    out += chunk
                    if cur is None:
                        break
                rows = [r for r in out if flt(r)]
                return ("read" if rows else "verified_empty"), rows
            if m == "rows":
                rows = db.rows_mode(flt)
                if len(rows) == ROWS_CAP:
                    return "incomplete", rows
                return ("read" if rows else "verified_empty"), rows
            if m == "sql":
                rows = [r for r in db.sql() if flt(r)]
                return ("read" if rows else "verified_empty"), rows
        except (ConnectionError, QuotaExhausted):
            continue
    return "unavailable", []


def describe(source, outcome, rows):
    """How a report states the result. Never 'none' unless verified empty."""
    if outcome == "read":
        return f"{source}: {len(rows)} found"
    if outcome == "verified_empty":
        return f"No entries in {source}"
    if outcome == "incomplete":
        return f"{source}: only part could be read"
    return f"{source} could not be verified"


def run_result(outcomes, critical):
    """Complete only if every critical source was read or verified empty."""
    bad = [s for s in critical if outcomes.get(s) not in ("read", "verified_empty")]
    return ("Partial", bad) if bad else ("Complete", [])


# ---- inbox-coverage.md section 5: mutually exclusive buckets ----
BUCKET_ORDER = ["urgent", "needs_reply", "opportunity", "money", "meetings", "customer",
                "personal", "routine"]


def bucket(thread):
    """First bucket in order that the thread's signals match."""
    for b in BUCKET_ORDER:
        if b in thread["signals"]:
            return b
    return "routine"


def reconcile(threads, already_handled=()):
    counts = {b: 0 for b in BUCKET_ORDER}
    counts["already_handled"] = 0
    seen = set()
    for t in threads:
        if t["id"] in seen:
            continue                      # count threads, not messages
        seen.add(t["id"])
        if t["id"] in already_handled:
            counts["already_handled"] += 1
        else:
            counts[bucket(t)] += 1
    discovered = len(seen)
    prioritized = sum(counts[b] for b in BUCKET_ORDER[:6])
    total = prioritized + counts["personal"] + counts["routine"] + counts["already_handled"]
    return discovered, prioritized, counts, total == discovered


# ---- run-modes.md: secrets ----
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{16,}",                       # API keys like OpenAI's
    r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"(?i)bearer\s+[A-Za-z0-9._-]{20,}",
    r"\b(?:\d[ -]?){13,19}\b",                       # card-like numbers
]


def find_secrets(text):
    return [m.group(0) for p in SECRET_PATTERNS for m in re.finditer(p, text)]


def redact(text):
    for p in SECRET_PATTERNS:
        text = re.sub(p, "[secret removed]", text)
    return text


def security_flag(kind, location):
    return (f"Possible exposed {kind} in {location}. Check whether it's real, change it, "
            f"and move it somewhere private. (Handed to you)")


def actions_from_content(text):
    """Untrusted content never produces actions; requests inside it are only flagged."""
    asks = re.findall(r"(?i)\b(send|forward|pay|delete|share|ignore (?:your|previous) (?:rules|instructions))\b", text)
    return [], [f"suspicious request in content: '{a}'" for a in asks]


# ---- team-roles.md: work economically / judgment ----
def members_to_launch(work_by_member):
    return [m for m, items in work_by_member.items() if items]


def should_prepare(item, calendar, existing):
    """Return (do_it, form): form is draft | approval | note | handed_to_you | skip."""
    if not item.get("needed", True):
        return False, "skip"
    if (item.get("action"), item.get("person")) in existing:
        return False, "skip"
    if item.get("person") and any(e["with"] == item["person"] and 0 <= e["hours_away"] <= 24
                                   for e in calendar):
        return True, "note"
    if item.get("owner_only"):
        return True, "handed_to_you"
    if item.get("consequential"):
        return True, "approval"
    if item.get("small_decision"):
        return True, "note"
    return True, "draft"


# ---- views must match what they're used for ----
def view_usable(view_filter, needed_filter):
    """A view is used only if its saved filter is exactly what the read needs."""
    return view_filter == needed_filter


# ---- review-approvals.md: owner-only items on older workspaces ----
def handed_to_you_status(options):
    """Status to set for an item only the owner can finish."""
    if "Handed to you" in options:
        return "Handed to you", ""
    return "Pending", "Handed to you: "        # never Done before the owner confirms


# ---- run-tracking.md section 2: duplicate schedules ----
def duplicate_schedule_warning(task_list, responsibility):
    """Only the scheduled-task list can show duplicates; run times never do."""
    return sum(1 for t in task_list if t["responsibility"] == responsibility and t["enabled"]) > 1


# ---- run-tracking.md section 5: notification status ----
def notification_line(tool_result):
    if tool_result is None:
        return "not requested"
    if tool_result.get("error"):
        return f"failed: {tool_result['error']}"
    if tool_result.get("delivered") is True:
        return "confirmed"
    if tool_result.get("accepted") is True:
        return "requested, accepted by the tool"
    return "unknown"


# ---- prepare-weekly-marketing: missing data ----
def metric_label(value_from_source):
    return "Verified" if value_from_source is not None else "Unavailable"


# ---- run-modes.md / schedule-workforce: the team's own recurring tasks ----
def task_marker(prompt):
    """The skill a task belongs to, read only from the first line's tag (run-modes.md).
    The version on that line is never compared: tasks always follow the installed plugin."""
    first = prompt.replace("\r\n", "\n").split("\n", 1)[0].strip()
    m = re.match(r"^\[AI Workforce task: ([a-z0-9-]+) \|", first)
    return m.group(1) if m else None


def matching_tasks(tasks, skill):
    return [t for t in tasks if task_marker(t["prompt"]) == skill]


def run_may_change_task(scheduled_run):
    """run-modes.md: a run never changes a recurring task; only the owner does, in chat."""
    return not scheduled_run


def separate_inbox_task_to_pause(tasks):
    """schedule-workforce "One morning run": when a daily briefing task and a separate inbox triage
    task run at the same rhythm less than 3 hours apart, the inbox one is offered for pausing (never
    deleted, and only on the owner's yes). An inbox check at another rhythm, an extra check 3 hours
    or more away (an afternoon one), or a task already paused, is left alone."""
    briefings = [t for t in matching_tasks(tasks, "daily-executive-briefing") if t["enabled"]]
    inboxes = [t for t in matching_tasks(tasks, "inbox-triage") if t["enabled"]]
    if not briefings:
        return None
    for inbox in inboxes:
        if any(inbox["rhythm"] == b["rhythm"] and abs(inbox["hour"] - b["hour"]) < 3 for b in briefings):
            return inbox["id"]
    return None


def add_owner_instruction(prompt, words):
    """schedule-workforce "Adding the owner's own instruction": everything before stays exactly
    as it was; the owner's words go at the end under "Owner's additions:"."""
    body = prompt.rstrip("\n")
    if re.search(r"(?m)^Owner's additions:", body):
        return body + "\n" + words.strip()
    return body + "\n\nOwner's additions:\n" + words.strip()


# ---- brain-upgrades.md: saved views, structure check and repair ----
def vkey(v):
    return [int(x) for x in v.split(".")]


STANDARD_VIEWS = {
    "Approvals": ("Active approvals", 'FILTER "Status" IN ("Pending", "Approved", "Handed to you"); SORT BY "AP" ASC'),
    "Assignments": ("Open work", 'FILTER "Status" IN ("Planned", "In progress", "Prepared", "Handed to you", "Blocked"); SORT BY "Date" ASC'),
    "Briefings": ("Newest first", 'SORT BY "Date" DESC'),
    "Pricing & Offers": ("Active offers", 'FILTER "Active" = TRUE; SORT BY "Offer" ASC'),
    "Customers & Leads": ("All contacts", 'SORT BY "Last contact" DESC'),
}
REQUIRED_DBS = tuple(STANDARD_VIEWS)
# Headings the upgrade sections add to existing pages (Priorities), checked and added by the repair too.
REQUIRED_HEADINGS = ("Work I'd like to hand off", "Always worth my attention", "Not my responsibility anymore")
LATEST_BRAIN = "1.0.0"       # the newest "## Upgrade to" section in brain-upgrades.md


def check_and_repair(workspace, fail_on=()):
    """Structure check and repair: add only what's missing, never touch what exists, set the
    version only when everything required is verified. Returns (complete, report)."""
    report = {"added": [], "kept_owner_view": [], "missing": []}
    headings = workspace.setdefault("headings", set(REQUIRED_HEADINGS))   # a fresh setup has them all
    for h in REQUIRED_HEADINGS:
        if h not in headings and ("heading", h) not in fail_on:
            headings.add(h)                                        # appended from the template, add-only
            report["added"].append(f"Priorities/{h}")
    for db in REQUIRED_DBS:
        if db not in workspace["dbs"]:
            if ("db", db) in fail_on:
                continue
            workspace["dbs"].add(db)
            report["added"].append(db)
    for db, (name, config) in STANDARD_VIEWS.items():
        if db not in workspace["dbs"]:
            continue
        views = workspace["views"].setdefault(db, {})
        if name in views:
            if views[name] != config:
                report["kept_owner_view"].append(f"{db}/{name}")   # left alone, reported once
            continue
        if ("view", db) in fail_on:
            continue
        views[name] = config
        report["added"].append(f"{db}/{name}")
    report["missing"] += [f"Priorities/{h}" for h in REQUIRED_HEADINGS if h not in headings]
    for db, (name, _) in STANDARD_VIEWS.items():                  # re-fetch to confirm
        if db not in workspace["dbs"]:
            report["missing"].append(db)
        elif name not in workspace["views"].get(db, {}):
            report["missing"].append(f"{db}/{name}")
    complete = not report["missing"]
    if complete:
        workspace["version"] = LATEST_BRAIN
    return complete, report


def upgrade_views(workspace, fail_on=()):
    workspace.setdefault("dbs", set(REQUIRED_DBS))
    return check_and_repair(workspace, {("view", d) for d in fail_on})[0]


SECTIONS_WITH_STEPS = ("1.0.0",)


def version_looks_current(workspace):
    v = workspace.get("version")
    return v not in (None, "setup in progress") and vkey(v) >= vkey(LATEST_BRAIN)


def update_my_team_workspace(workspace, fail_on=(), sections_run=None):
    """setup-workforce "Update my team workspace": due upgrade sections first (all of them when the
    line is missing or "setup in progress"), then the structure check, whatever the version says.
    Since 1.1.0 the sections for 0.4.0 to 0.6.0 have no steps of their own: everything they added is in
    the schema, so the structure check adds it. Only sections from 1.0.0 on still have steps."""
    sections_run = [] if sections_run is None else sections_run
    v = workspace.get("version")
    for section in SECTIONS_WITH_STEPS:
        if v in (None, "setup in progress") or vkey(v) < vkey(section):
            sections_run.append(section)              # each is check-then-add; version moves only below
    return check_and_repair(workspace, fail_on)


def self_test_views(workspace):
    """Self-test 6g: PASS, owner's filter kept, or FAIL for each standard view."""
    out = {}
    for db, (name, config) in STANDARD_VIEWS.items():
        have = workspace["views"].get(db, {}).get(name)
        out[f"{db}/{name}"] = "PASS" if have == config else ("FAIL" if have is None else "owner's filter kept")
    return out
