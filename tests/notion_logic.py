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


# ---- run-modes.md: recurring tasks keep themselves up to date ----
STANDARD = {"daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices"}
SETTINGS = ("cron", "timezone", "enabled", "notifications", "model", "approval")


def normalize(text):
    """The only differences allowed when comparing prompts: line endings and trailing spaces."""
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def vkey(v):
    return [int(x) for x in v.split(".")]


def auto_update_plan(tasks, responsibility, history, current_version, brain_version,
                     setting="yes", can_compare=True, brain_title="Business Brain"):
    """Decide what an outdated standard task may do. Returns (action, detail).

    history: {(responsibility, version): (template_text, needs_brain_version)}
    action: none | update | warn | ask
    """
    if setting == "no":
        return "warn", "automatic updates turned off"
    if responsibility not in STANDARD:
        return "warn", "custom responsibility"
    matches = [t for t in tasks if t["responsibility"] == responsibility]
    if len(matches) != 1:
        return "ask", f"{len(matches)} matching tasks"
    task = matches[0]
    current_text, needs = history[(responsibility, current_version)]
    current_text = current_text.replace("<BRAIN>", brain_title)
    if normalize(task["prompt"]) == normalize(current_text):
        return "none", None
    if not can_compare:
        return "warn", "can't compare reliably"
    released = {v: t.replace("<BRAIN>", brain_title) for (r, v), (t, _) in history.items() if r == responsibility}
    found = [v for v, text in released.items() if normalize(text) == normalize(task["prompt"])]
    if not found:
        return "warn", "custom instructions"          # includes unknown old versions
    if vkey(brain_version) < vkey(needs):
        return "warn", f"needs Business Brain {needs}"
    return "update", {"task": task["id"], "from": found[0], "to": current_version, "backup": task["prompt"],
                      "new": current_text}


class FakeScheduler:
    """A scheduled-task list whose update can be made to fail or misbehave."""
    def __init__(self, tasks, fail_update=False, corrupt_setting=None, fail_restore=False):
        self.tasks = {t["id"]: dict(t) for t in tasks}
        self.fail_update, self.corrupt, self.fail_restore = fail_update, corrupt_setting, fail_restore
        self.calls = 0

    def update_prompt(self, task_id, prompt):
        self.calls += 1
        restoring = self.calls > 1
        if (self.fail_update and not restoring) or (self.fail_restore and restoring):
            return False
        self.tasks[task_id]["prompt"] = prompt
        if self.corrupt and not restoring:
            self.tasks[task_id][self.corrupt] = "changed"
        return True

    def get(self, task_id):
        return dict(self.tasks[task_id])


def apply_update(scheduler, plan):
    """Back up, update the prompt only, verify, restore on failure. Returns the report line."""
    tid, backup, new = plan["task"], plan["backup"], plan["new"]
    before = scheduler.get(tid)
    scheduler.update_prompt(tid, new)
    after = scheduler.get(tid)
    ok = after["prompt"] == new and all(after.get(k) == before.get(k) for k in SETTINGS)
    if ok:
        return "updated", after
    scheduler.update_prompt(tid, backup)
    restored = scheduler.get(tid)
    if restored["prompt"] == backup:
        return "restored", restored
    return "restore unconfirmed", restored


# ---- brain-upgrades.md 0.5.2: saved views ----
STANDARD_VIEWS = {
    "Approvals": ("Active approvals", 'FILTER "Status" IN ("Pending", "Approved", "Handed to you"); SORT BY "AP" ASC'),
    "Assignments": ("Open work", 'FILTER "Status" IN ("Planned", "In progress", "Prepared", "Handed to you", "Blocked"); SORT BY "Date" ASC'),
    "Briefings": ("Newest first", 'SORT BY "Date" DESC'),
    "Pricing & Offers": ("Active offers", 'FILTER "Active" = TRUE; SORT BY "Offer" ASC'),
    "Customers & Leads": ("All contacts", 'SORT BY "Last contact" DESC'),
}


def upgrade_views(workspace, fail_on=()):
    """Add missing views by name; never touch existing ones; bump version only if all present."""
    for db, (name, config) in STANDARD_VIEWS.items():
        views = workspace["views"].setdefault(db, {})
        if name in views:
            continue                                  # leave the owner's view as it is
        if db in fail_on:
            continue
        views[name] = config
    complete = all(STANDARD_VIEWS[db][0] in workspace["views"].get(db, {}) for db in STANDARD_VIEWS)
    if complete:
        workspace["version"] = "0.5.2"
    return complete
