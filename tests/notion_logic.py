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
    def __init__(self, rows, sql_quota=0, view_page_size=50, fail=(), has_view=True):
        self.rows = list(rows)
        self.sql_quota = sql_quota
        self.view_page_size = view_page_size
        self.fail = set(fail) if fail != "all" else {"view", "rows", "sql"}
        self.has_view = has_view
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
        if "rows" in self.fail:
            raise ConnectionError("rows failed")
        return [r for r in self.rows if flt(r)][:ROWS_CAP]

    def sql(self):
        self.calls.append(("sql", None))
        if "sql" in self.fail:
            raise ConnectionError("sql failed")
        if self.sql_quota <= 0:
            raise QuotaExhausted("SQL allowance used up")
        self.sql_quota -= 1
        return list(self.rows)


def read_database(db, flt=lambda r: True, need_sql=False):
    """Return (outcome, rows). outcome: read | verified_empty | incomplete | unavailable."""
    methods = ["view", "rows"] + (["sql"] if need_sql else ["sql"])
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
