# -*- coding: utf-8 -*-
"""AI Workforce send lock: a plugin hook that refuses send, delete, share and booking tools
where nobody is watching.

Claude runs this before every connected-app (MCP) tool call, and when a prompt is submitted.
It reads one JSON object on standard input (the hook input) and answers with its exit code:

    0  let the call through (also on any error: the team's written rules still apply)
    2  refuse the call; the text on standard error is shown to Claude as the reason

It refuses a tool only in two situations:

1. An unattended team run: the session was started by one of the team's recurring tasks,
   whose stored instructions always begin with the tag "[AI Workforce task:".
2. A team member working as its own agent (ai-workforce:operations-manager and so on).
   Members read, research and draft; they never send, delete, share or book.

The Chief of Staff in a chat with the owner present is never affected: the owner sees and
approves what happens there.

What is refused (by tool name; see `decide`):
- sending, replying, forwarding, deleting, trashing, removing, RSVP-ing, cancelling,
  unsubscribing, publishing, paying, purchasing;
- sharing, posting, booking, refunding, charging, transferring, voiding, archiving, marking
  as spam (unless the name starts as a read, such as "get_refund");
- creating or changing calendar events, appointments, invitations and bookings;
- creating or changing invoices, payments, subscriptions, expenses and budgets;
- on an app that works through one general "run an operation" tool (HighLevel is one), any
  operation the lock can't recognise as a plain read from what the call says it will run: the
  operation's name has to begin with a reading word ("search-conversation", "get-messages"),
  so a reading word used as a noun ("set-task-home-list") doesn't pass;
- anything else but a plain read in HighLevel;
- creating, changing or starting a scheduled task: a run never changes a recurring task.
Creating drafts and writing to the Business Brain in Notion are never refused.

Limits: tools are recognised by their names; a web browser driven by Claude is not covered;
and the lock only runs where Claude runs plugin hooks and Python is available.
"""
from __future__ import print_function

import json
import os
import re
import sys
import tempfile

TAG = "[AI Workforce task:"
PLUGIN = "ai-workforce"
TEAM_AGENTS = frozenset([
    "operations-manager", "marketing-manager", "sales-manager",
    "client-success-manager", "finance-manager", "chief-of-staff",
])

# Refused whenever one of these words is part of the tool's name.
STRONG = frozenset([
    "send", "reply", "forward", "trash", "delete", "remove", "respond", "rsvp",
    "cancel", "unsubscribe", "publish", "pay", "purchase",
])
# Refused unless a reading word comes first in the name ("get_refund" is a read).
WEAK = frozenset([
    "share", "post", "book", "refund", "payout", "transfer", "charge", "void", "archive", "spam",
])
READ = frozenset([
    "get", "list", "search", "find", "fetch", "read", "query", "view", "retrieve",
    "lookup", "check", "count", "describe", "download",
])
CHANGE = frozenset(["create", "update", "upsert", "insert", "patch", "edit", "add"])
CALENDAR_CHANGE = CHANGE | frozenset(["move", "schedule", "reschedule", "accept", "decline"])
CALENDAR_THINGS = frozenset([
    "event", "events", "appointment", "appointments", "invite", "invites",
    "invitation", "invitations", "booking", "bookings",
])
MONEY_CHANGE = CHANGE | frozenset(["finalize", "issue", "record", "apply", "mark"])
MONEY_THINGS = frozenset([
    "invoice", "invoices", "expense", "expenses", "bill", "bills", "ledger", "payment", "payments",
    "subscription", "subscriptions", "charge", "charges", "refund", "refunds", "payout", "payouts",
    "transaction", "transactions", "budget", "budgets",
])
# Tools that run "an operation" named in their input rather than in their own name
# (HighLevel's execute_operation). The name says nothing, so the input is checked.
EXECUTE_VERBS = frozenset(["execute", "call", "invoke", "perform"])
EXECUTE_THINGS = frozenset([
    "operation", "operations", "action", "actions", "api", "endpoint", "request",
    "tool", "function", "command",
])
HTTP_METHODS = frozenset(["get", "post", "put", "patch", "delete", "head", "options"])
# A short product prefix may come before the reading word: "fb-get-conversation-forms".
VENDOR_PREFIXES = frozenset(["fb", "facebook", "google", "li", "linkedin", "ig", "instagram", "tiktok", "meta", "wa", "whatsapp"])
# Scheduled tasks ("triggers", "routines"): a run may list them, never create, change or start one.
SCHEDULE_THINGS = frozenset(["trigger", "triggers", "routine", "routines"])
SCHEDULE_CHANGE = CHANGE | frozenset(["fire", "run", "start", "enable", "disable", "pause", "resume", "set"])
# Input fields that hold what the owner or a customer wrote, not which operation runs.
FREE_TEXT = frozenset([
    "query", "q", "text", "message", "body", "content", "prompt", "description", "reason",
    "notes", "note", "search", "keyword", "keywords", "title", "subject", "comment",
])
NAMES_THE_OPERATION = ("operation", "action", "tool", "function", "endpoint", "method", "path", "name")
# The harness's own ways of reporting to the owner are never refused.
NOTIFY = frozenset(["notification", "notifications", "notify"])
OWNER_REPORT = re.compile(r"^send[_-]?user[_-]?(message|file)$", re.I)
READ_ONLY_APPS = ("highlevel", "leadconnector")


def split_tool(tool_name):
    """'mcp__Gmail__send_message' -> ('Gmail', 'send_message'). Anything else -> (None, None)."""
    if not isinstance(tool_name, str) or not tool_name.startswith("mcp__"):
        return None, None
    rest = tool_name[len("mcp__"):]
    if "__" not in rest:
        return rest, ""
    server, tool = rest.rsplit("__", 1)
    return server, tool


def words(tool):
    """'conversations_send-a-new-message' -> ['conversations', 'send', 'a', 'new', 'message'].
    Splits camelCase too, so 'sendMessage' is ['send', 'message']."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", tool)
    return [w.lower() for w in re.split(r"[^A-Za-z0-9]+", spaced) if w]


def _first(ws, group):
    """Position of the first word of `ws` that is in `group`, or len(ws) if none is."""
    for i, w in enumerate(ws):
        if w in group:
            return i
    return len(ws)


def _operation_fields(tool_input):
    """The short text fields of a call's input that say which operation it runs.
    Free text, ids of records, and the payload (nested objects) are left out."""
    fields = []
    if not isinstance(tool_input, dict):
        return fields
    for key, value in tool_input.items():
        k = re.sub(r"[^a-z0-9]", "", str(key).lower())
        if isinstance(value, dict) and any(n in k for n in ("operation", "action")):
            fields.extend(_operation_fields(value))           # {"operation": {"id": "..."}}
            continue
        if not isinstance(value, str) or not value.strip() or len(value) > 300:
            continue
        if k in FREE_TEXT:
            continue
        names_it = any(n in k for n in NAMES_THE_OPERATION)
        if k.endswith("id") and k != "id" and not names_it:
            continue                                          # locationId, contactId: a record, not an operation
        fields.append(value)
    return fields


def begins_as_a_read(name):
    """True when a tool or operation name begins with a reading word.

    A reading word later in the name doesn't count: in "set-projects-task-home-list" (which moves
    a task) "list" is a thing, not what the operation does. What may come before the reading word:
    - a namespace ending in "." "/" or ":"       conversations.search, payments.transactions.list
    - a domain joined by "_" to a hyphenated name contacts_get-contact, calendars_get-calendar-events
    - one short product prefix                    fb-get-conversation-forms, google-get-keyword-ideas
    """
    if not isinstance(name, str):
        return False
    last = re.split(r"[./:]+", name.strip().strip("./:"))[-1]
    if "_" in last and "-" in last:
        last = last.split("_", 1)[1]
    ws = words(last)
    if ws and ws[0] in VENDOR_PREFIXES:
        ws = ws[1:]
    return bool(ws) and ws[0] in READ


def operation_is_a_plain_read(tool_input):
    """For a "run an operation" tool: (True, None) only when the input names an operation that
    reads and nothing in it names a change. Anything unclear is not a plain read."""
    if isinstance(tool_input, dict):
        for key, value in tool_input.items():
            if "idempotency" in re.sub(r"[^a-z]", "", str(key).lower()) and value not in (None, "", False):
                return False, "it carries an idempotency key, which only a change needs"
    fields = _operation_fields(tool_input)
    if not fields:
        return False, "it doesn't say which operation it would run"
    reads = False
    for field in fields:
        name, ws = field, words(field)
        if ws and ws[0] in HTTP_METHODS:                      # "GET /conversations/search", or a method field
            method, ws = ws[0], ws[1:]
            if method in ("put", "patch", "delete"):
                return False, "it would change something (%s)" % method.upper()
            reads = reads or method == "get"
            name = field.strip()[len(method):]
        read_at = _first(ws, READ)
        for i, w in enumerate(ws):
            if w in STRONG or w in CHANGE:
                return False, "it would %s something" % w
            if w in WEAK and i < read_at:
                return False, "it would %s something" % w
        reads = reads or begins_as_a_read(name)
    if not reads:
        return False, "the lock can't tell that the operation only reads"
    return True, None


def decide(tool_name, tool_input=None):
    """Return a short reason if this tool call is one the lock refuses, else None."""
    server, tool = split_tool(tool_name)
    if server is None:
        return None                                   # only connected-app tools are checked
    ws = words(tool)
    if not ws:
        return None
    if OWNER_REPORT.match(tool) or NOTIFY.intersection(ws):
        return None                                   # reporting to the owner is always allowed

    if EXECUTE_VERBS.intersection(ws) and EXECUTE_THINGS.intersection(ws):
        plain_read, why = operation_is_a_plain_read(tool_input)
        return None if plain_read else why

    read_at = _first(ws, READ)
    scheduled = SCHEDULE_THINGS.intersection(ws) or ("scheduled" in ws and {"task", "tasks"}.intersection(ws))
    if scheduled and _first(ws, SCHEDULE_CHANGE) < read_at:
        return "it would create, change or start a scheduled task"

    whole = re.sub(r"[^a-z0-9]", "", (server + tool).lower())
    if any(app in whole for app in READ_ONLY_APPS):
        if not begins_as_a_read(tool) or STRONG.intersection(ws) or CHANGE.intersection(ws):
            return "it is not a plain read, and the team only reads HighLevel"
        return None

    for i, w in enumerate(ws):
        if w in STRONG:
            return "it would %s something" % w
        if w in WEAK and i < read_at:
            return "it would %s something" % w
    if CALENDAR_THINGS.intersection(ws) and _first(ws, CALENDAR_CHANGE) < read_at:
        return "it would create or change a calendar event"
    if MONEY_THINGS.intersection(ws) and _first(ws, MONEY_CHANGE) < read_at:
        return "it would create or change a financial record or budget"
    return None


# ---- is this an unattended team run? ----

def marker_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "", str(session_id or ""))[:80]
    if not safe:
        return None
    return os.path.join(tempfile.gettempdir(), "ai-workforce-send-lock", safe)


def set_marker(session_id):
    path = marker_path(session_id)
    if not path:
        return
    try:
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "w") as fh:
            fh.write("unattended AI Workforce run\n")
    except (OSError, IOError):
        pass


def has_marker(session_id):
    path = marker_path(session_id)
    return bool(path) and os.path.isfile(path)


def _text_of(content):
    """The typed text of a transcript message; '' for tool results and anything else."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def first_prompts(transcript_path, limit=3, max_lines=400):
    """The first few things the user side typed in this session, read from the transcript."""
    found = []
    try:
        with open(transcript_path, "rb") as fh:
            for n, raw in enumerate(fh):
                if n >= max_lines or len(found) >= limit:
                    break
                try:
                    entry = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if not isinstance(entry, dict):
                    continue
                message = entry.get("message") if isinstance(entry.get("message"), dict) else entry
                role = message.get("role") or entry.get("type")
                if role != "user" or entry.get("type") not in (None, "user"):
                    continue
                text = _text_of(message.get("content"))
                if text.strip():
                    found.append(text)
    except (OSError, IOError):
        pass
    return found


def unattended_run(data):
    """True when this session was started by one of the team's recurring tasks."""
    session_id = data.get("session_id")
    if has_marker(session_id):
        return True
    path = data.get("transcript_path")
    if isinstance(path, str) and path and any(TAG in text for text in first_prompts(path)):
        set_marker(session_id)                        # so team members' own transcripts are covered too
        return True
    return False


def team_agent(data):
    """The member's name when the call comes from one of this plugin's agents, else None."""
    agent = data.get("agent_type")
    if not isinstance(agent, str) or ":" not in agent:
        return None
    plugin, name = agent.rsplit(":", 1)
    if plugin == PLUGIN and name in TEAM_AGENTS:
        return name
    return None


def handle(data):
    """Return (exit_code, message for Claude or None)."""
    event = data.get("hook_event_name")
    if event == "UserPromptSubmit":
        prompt = data.get("prompt")
        if isinstance(prompt, str) and TAG in prompt:
            set_marker(data.get("session_id"))
        return 0, None
    if event != "PreToolUse":
        return 0, None

    tool_name = data.get("tool_name")
    reason = decide(tool_name, data.get("tool_input"))
    if not reason:
        return 0, None
    member = team_agent(data)
    if member:
        why = ("team members read, research and draft only. Return the draft or your recommendation "
               "to the Chief of Staff instead")
    elif unattended_run(data):
        why = ("this conversation was started by a recurring task, where the team only reads, drafts and "
               "prepares. Save a draft or leave it for the owner instead. If the owner is here now and asked "
               "for this, tell them it can't be done from this conversation and to ask again in a new chat")
    else:
        return 0, None
    _, tool = split_tool(tool_name)
    return 2, ("AI Workforce send lock: \"%s\" was refused because %s, and %s. Do not retry this call "
               "and do not use another tool to do the same thing; say what was refused in your report."
               % (tool, reason, why))


def main():
    if sys.version_info[0] < 3:
        return 0
    try:
        data = json.loads(sys.stdin.read() or "{}")
        if not isinstance(data, dict):
            return 0
        code, message = handle(data)
    except Exception:                                 # never break a session over the lock itself
        return 0
    if code == 2 and message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
