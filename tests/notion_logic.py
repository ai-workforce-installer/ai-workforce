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
SETTINGS = ("cron", "timezone", "enabled", "notifications", "model", "approval", "next_run")


def normalize(text):
    """The only differences allowed when comparing prompts: line endings and trailing spaces."""
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def vkey(v):
    return [int(x) for x in v.split(".")]


def auto_update_plan(tasks, responsibility, history, current_version, brain_version,
                     setting="yes", can_compare=True, brain_title="Business Brain", connections_in_use=None):
    """Decide what an outdated standard task may do. Returns (action, detail).

    history: {(responsibility, version): (template_text, needs_brain_version[, needed_connections])}
    Tasks are matched only by the tag on their instructions' first line.
    action: none | update | warn | ask
    """
    if setting == "no":
        return "warn", "automatic updates turned off"
    if responsibility not in STANDARD:
        return "warn", "custom responsibility"
    matches = matching_tasks(tasks, responsibility)
    if len(matches) != 1:
        return "ask", f"{len(matches)} matching tasks"
    task = matches[0]
    current_text, needs = history[(responsibility, current_version)][:2]
    needed = set(history[(responsibility, current_version)][2]) if len(history[(responsibility, current_version)]) > 2 else set()
    current_text = current_text.replace("<BRAIN>", brain_title)
    if normalize(task["prompt"]) == normalize(current_text):
        return "none", None
    if not can_compare:
        return "warn", "can't compare reliably"
    released = {v: e[0].replace("<BRAIN>", brain_title) for (r, v), e in history.items() if r == responsibility}
    found = [v for v, text in released.items() if normalize(text) == normalize(task["prompt"])]
    if not found:
        return "warn", "custom instructions"          # includes unknown old versions
    if vkey(brain_version) < vkey(needs):
        return "warn", f"needs Business Brain {needs}"
    missing = needed - set(connections_in_use or ())
    if missing:
        return "warn", f"needs connection {', '.join(sorted(missing))}"
    return "update", {"task": task["id"], "from": found[0], "to": current_version, "backup": task["prompt"],
                      "new": current_text}


def task_marker(prompt):
    """The skill a task belongs to, read only from the first line's tag (run-modes.md)."""
    first = prompt.replace("\r\n", "\n").split("\n", 1)[0].strip()
    m = re.match(r"^\[AI Workforce task: ([a-z0-9-]+) \|", first)
    return m.group(1) if m else None


def matching_tasks(tasks, skill):
    return [t for t in tasks if task_marker(t["prompt"]) == skill]


class FakeScheduler:
    """A scheduled-task list whose calls can be made to fail or misbehave.

    fail_update: the change call fails.     corrupt_setting: the change also alters a setting.
    fail_restore: the restore call fails.   restore_keeps_setting: restore fixes the text only.
    fail_reads: set of read numbers (1-based) that fail.   truncate: save only the first N chars.
    owner_edit_before_change: the owner edits the task between inspection and change.
    """
    def __init__(self, tasks, fail_update=False, corrupt_setting=None, fail_restore=False,
                 fail_reads=(), truncate=None, owner_edit_before_change=None, resumes_on_update=False):
        self.tasks = {t["id"]: dict(t) for t in tasks}
        self.fail_update, self.corrupt, self.fail_restore = fail_update, corrupt_setting, fail_restore
        self.fail_reads, self.truncate, self.owner_edit = set(fail_reads), truncate, owner_edit_before_change
        self.resumes = resumes_on_update               # a tool that switches a paused task back on
        self.calls = self.reads = 0

    def update_prompt(self, task_id, prompt):
        self.calls += 1
        restoring = self.calls > 1
        if (self.fail_update and not restoring) or (self.fail_restore and restoring):
            return False
        self.tasks[task_id]["prompt"] = prompt[:self.truncate] if (self.truncate and not restoring) else prompt
        if self.corrupt and not restoring:
            self.tasks[task_id][self.corrupt] = "changed"
        if self.resumes:
            self.tasks[task_id]["enabled"] = True
        return True

    def get(self, task_id):
        self.reads += 1
        if self.reads in self.fail_reads:
            raise ConnectionError("read failed")
        if self.owner_edit and self.reads == 2:          # the re-check just before the change
            self.tasks[task_id]["prompt"] += self.owner_edit
        return dict(self.tasks[task_id])


class BackupStore:
    """The Briefings record that holds the backup. Write or read-back can fail or truncate."""
    def __init__(self, fail_write=False, fail_read=False, truncate=None):
        self.fail_write, self.fail_read, self.truncate = fail_write, fail_read, truncate
        self.saved = None

    def save(self, text):
        if self.fail_write:
            return False
        self.saved = text[:self.truncate] if self.truncate else text
        return True

    def read(self):
        if self.fail_read:
            raise ConnectionError("read failed")
        return self.saved


def safe_change(scheduler, task_id, new_prompt, backup_store=None):
    """run-modes.md "Changing a recurring task's instructions safely". Returns (status, detail).

    status: updated | stopped | restored | restored_settings_changed | unconfirmed
    """
    backup_store = BackupStore() if backup_store is None else backup_store
    try:
        before = scheduler.get(task_id)                         # 1. capture everything
    except ConnectionError:
        return "stopped", "couldn't read the task"
    if not backup_store.save(before["prompt"]):                 # 2. back up and read back
        return "stopped", "backup not saved"
    try:
        if backup_store.read() != before["prompt"]:
            return "stopped", "backup incomplete"
    except ConnectionError:
        return "stopped", "backup not readable"
    try:
        now = scheduler.get(task_id)                            # 3. re-check
    except ConnectionError:
        return "stopped", "couldn't re-check the task"
    if now != before:
        return "stopped", "task changed since inspection"
    scheduler.update_prompt(task_id, new_prompt)                # 4. change the instructions only
    try:
        after = scheduler.get(task_id)                          # 5. verify everything
        changed = [k for k in SETTINGS if after.get(k) != before.get(k)]
        if after["prompt"] == new_prompt and not changed:
            return "updated", after
    except ConnectionError:
        pass                                                    # unverified counts as failed
    scheduler.update_prompt(task_id, before["prompt"])          # 6. restore, re-verify separately
    try:
        restored = scheduler.get(task_id)
    except ConnectionError:
        return "unconfirmed", "couldn't read the task after restoring"
    if restored["prompt"] != before["prompt"]:
        return "unconfirmed", "instructions not confirmed restored"
    changed = [k for k in SETTINGS if restored.get(k) != before.get(k)]
    if changed:
        return "restored_settings_changed", changed             # ask before setting them back
    return "restored", restored


def apply_update(scheduler, plan, backup_store=None):
    return safe_change(scheduler, plan["task"], plan["new"], backup_store)


def merged_prompt(template, owner_additions):
    """schedule-workforce attended update: the new template plus the owner's approved additions."""
    if not owner_additions:
        return template
    return template.rstrip() + "\n\nOwner's additions:\n" + owner_additions.strip()


# ---- brain-upgrades.md: saved views, structure check and repair ----
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
LATEST_BRAIN = "0.6.0"


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


def version_looks_current(workspace):
    v = workspace.get("version")
    return v not in (None, "setup in progress") and vkey(v) >= vkey(LATEST_BRAIN)


def update_my_team_workspace(workspace, fail_on=(), sections_run=None):
    """setup-workforce "Update my team workspace": due upgrade sections first (all of them when the
    line is missing or "setup in progress"), then the structure check, whatever the version says."""
    sections_run = [] if sections_run is None else sections_run
    v = workspace.get("version")
    for section in ("0.4.0", "0.5.0", "0.5.1", "0.5.2", "0.6.0"):
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
