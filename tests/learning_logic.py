"""Reference model of the 0.6.0 learning rules: owner corrections, plain-language approval replies,
choosing the Business Brain, confirmed vs. inferred facts, draft feedback and the Ready check.

Each function restates a written rule from the plugin as code:
  owner corrections ........ skills/assign-work/references/owner-corrections.md
  understanding replies .... skills/review-approvals/SKILL.md ("Understanding replies")
  choosing a Business Brain  skills/assign-work/references/run-modes.md, setup-workforce Stage 2
  confirmed vs. inferred ... setup-workforce Stage 3, references/interview.md, references/just-in-time.md
  Ready check .............. skills/assign-work/references/team-roles.md ("Ready check")
  one task per job ......... first-team-meeting (setup path), schedule-workforce step 3

Passing these tests shows the written design holds in the hard cases. It does not show that Claude
follows it in a live run; that needs the live checks in tests/README.md.
"""
import re
from dataclasses import dataclass, field
from datetime import date

# ------------------------------------------------------------------ the Business Brain (mock)
NEVER_HIDDEN = {"security_incident", "money_out", "legal", "personal_deadline"}
SECTIONS = {"not_mine": "Not my responsibility anymore", "ignore": "Things to ignore for now",
            "attention": "Always worth my attention"}
ACTIVE = ("Pending", "Approved")


@dataclass
class Brain:
    """Only what these rules touch. Priorities is plain text, exactly as Notion would hold it,
    so a 'later run' must re-read rules from the page rather than from memory."""
    priorities: str = ("## Things to ignore for now\n\n- <i>not set</i>\n\n"
                       "## Always worth my attention\n\n- <i>none yet</i>\n\n"
                       "## Not my responsibility anymore\n\n- <i>none yet</i>\n")
    approvals: list = field(default_factory=list)       # dicts: ap, item, status, source, kind, action_type, owner_note
    assignments: list = field(default_factory=list)     # dicts: title, owner, status, source, result, created_by
    brand: dict = field(default_factory=dict)           # sign_off (None = not set), voice
    pricing: dict = field(default_factory=dict)         # offer -> price (confirmed only)
    policies: dict = field(default_factory=dict)
    profile: dict = field(default_factory=dict)
    links: set = field(default_factory=set)
    writes: list = field(default_factory=list)          # every write, in order


def active_queue(brain):
    return [a for a in brain.approvals if a["status"] in ACTIVE]


# ------------------------------------------------------------------ owner-corrections.md section 1
def classify_correction(text):
    t = text.lower()
    if re.search(r"until|this week|for now|not this week", t) and re.search(r"ignore|don't|stop", t):
        return "temporary"
    if re.search(r"too formal|sign (it|that)|stronger opening|conversational|claim isn't accurate|sounds", t):
        return "draft"
    if re.search(r"isn't my responsibility|not my responsibility|no longer one of my|isn't one of my|"
                 r"don't keep bringing|stop bringing|isn't important to me|don't matter|doesn't matter|"
                 r"deserve (my )?attention|matter to me", t):
        return "lasting"
    if re.search(r"ignore this thread|stop telling me about this one", t):
        return "thread"
    if re.search(r"already (handled|checked|did|sent)|i sent it|was intentional|is fine|i looked", t):
        return "item"
    return "unclear"


# ------------------------------------------------------------------ sections 2-4: confirm, save, close
def rule_line(covers, since, until=None):
    line = f"- {covers} · since {since:%b %-d, %Y}"
    return line + (f" · until {until:%b %-d, %Y}" if until else "")


def save_rule(brain, section, covers, *, attended, confirmed, today, until=None, close_aps=()):
    """Returns 'saved' | 'needs confirmation' | 'question for owner'. Writes nothing otherwise."""
    if not attended:
        return "question for owner"                  # scheduled runs never create rules
    if not confirmed:
        return "needs confirmation"
    heading = f"## {SECTIONS[section]}\n\n"
    if heading not in brain.priorities:              # older workspace: Things to ignore for now
        heading = f"## {SECTIONS['ignore']}\n\n"
        covers = ("Not my responsibility: " if section == "not_mine" else "") + covers
    line = rule_line(covers, today, until)
    start = brain.priorities.index(heading) + len(heading)
    body_end = brain.priorities.find("\n## ", start)
    body_end = len(brain.priorities) if body_end == -1 else body_end
    body = brain.priorities[start:body_end]
    if re.fullmatch(r"- <i>(not set|none yet)</i>\n*", body):
        new_body = line + "\n"                       # replace the placeholder
    else:
        new_body = body.rstrip("\n") + "\n" + line + "\n"   # add after the last bullet
    brain.priorities = brain.priorities[:start] + new_body + "\n" + brain.priorities[body_end:].lstrip("\n")
    brain.writes.append(("priorities", line))
    for ap in close_aps:                             # only the ones listed in the same confirmation
        close_item(brain, ap, "not_mine", f"Owner: not my responsibility ({covers}, {today:%b %-d})", today)
    return "saved"


def retire_rule(brain, covers, today):
    """'Actually, do tell me about X': mark the line, never delete it."""
    lines = brain.priorities.split("\n")
    for i, l in enumerate(lines):
        if l.startswith(f"- {covers} ·") and "no longer applies" not in l:
            lines[i] = l + f" · no longer applies {today:%b %-d, %Y}"
    brain.priorities = "\n".join(lines)


def close_item(brain, ap, kind, note, today):
    row = next(a for a in brain.approvals if a["ap"] == ap)
    row["status"] = {"handled": "Done", "acknowledged": "Done", "not_mine": "Rejected"}[kind]
    row["owner_note"] = (row.get("owner_note", "") + " " + note).strip()     # add, never overwrite
    row["decided"] = today
    brain.writes.append(("approval", ap, row["status"]))
    for a in brain.assignments:
        if a["source"] == row["source"] and a.get("created_by") == "team" and a["status"] not in ("Done", "Failed"):
            a["status"] = "Done"
            a["result"] = (a.get("result", "") + " Closed: " + note).strip()


# ------------------------------------------------------------------ section 5: applying rules each run
def load_rules(brain, today):
    """Re-read from the page text every run: nothing carries over in memory."""
    rules, current = [], None
    for line in brain.priorities.split("\n"):
        h = re.match(r"## (.+)", line)
        if h:
            current = next((k for k, v in SECTIONS.items() if v == h.group(1)), None)
            continue
        m = re.match(r"- (.+?) · since ([^·]+?)(?: · until ([^·]+?))?(?: · no longer applies .*)?$", line)
        if current and m and "no longer applies" not in line:
            until = m.group(3)
            if until and date.fromisoformat(_iso(until)) < today:
                continue                              # temporary rule past its date
            covers = re.sub(r"^Not my responsibility: ", "", m.group(1))
            rules.append({"section": "not_mine" if line.startswith("- Not my responsibility:") else current,
                          "covers": covers.lower()})
    return rules


def _iso(text):
    from datetime import datetime
    return datetime.strptime(text.strip(), "%b %d, %Y").date().isoformat()


GENERIC = {"and", "the", "from", "emails", "email", "notifications", "alerts", "its", "their"}


def matches(item, rule):
    """As narrow as the owner said: a rule names a thing (its first word: a business, a service, a
    kind of mail), and an 'except …' part keeps out what the owner still wants. The real judgment of
    what an email is about is Claude's; this only restates 'narrow, with exceptions'."""
    head, _, exc = rule["covers"].partition(" except ")
    key = next(w for w in re.findall(r"[a-z0-9-]+", head.lower()) if w not in GENERIC)
    excepted = set(re.findall(r"[a-z0-9-]+", exc.lower()))
    return key in item["entities"] and not (excepted & item["entities"])


def sort_item(item, rules, closed_threads):
    """Returns (bucket, note). Buckets: 'your rules', 'already handled', 'attention', or 'raise'."""
    hit = next((r for r in rules if r["section"] in ("not_mine", "ignore") and matches(item, r)), None)
    if hit:
        if item["kind"] in NEVER_HIDDEN and item.get("new", True):
            return "raise", f"matches your note '{hit['covers']}', raised because it's a new {item['kind']}"
        return "your rules", hit["covers"]
    if item.get("thread") in closed_threads and not item.get("materially_new"):
        return "already handled", item["thread"]
    if any(r["section"] == "attention" and matches(item, r) for r in rules):
        return "attention", None
    return "raise", None


def run(brain, items, today):
    """One run of inbox triage or a briefing, as far as these rules go. Queues an approval only for
    raised items, never twice for one problem, never for anything ruled out."""
    rules = load_rules(brain, today)
    closed = {a["thread"] for a in brain.approvals if a["status"] in ("Done", "Rejected") and a.get("thread")}
    report = {"raised": [], "your rules": 0, "already handled": 0, "attention": [], "notes": []}
    problems = {}
    for it in items:
        bucket, note = sort_item(it, rules, closed)
        if bucket == "raise":
            problems.setdefault(it["problem"], []).append(it)    # one problem, one item
            if note:
                report["notes"].append(note)
        elif bucket == "attention":
            report["attention"].append(it["topic"])
        else:
            report[bucket] += 1
    for problem, its in problems.items():
        if any(a["problem"] == problem and a["status"] in ACTIVE for a in brain.approvals):
            continue                                              # reuse the open item
        if any(a["problem"] == problem and a["status"] in ("Done", "Rejected")
               and not any(i.get("materially_new") or i["kind"] in NEVER_HIDDEN for i in its)
               for a in brain.approvals):
            continue                                              # repeating alert isn't new
        ap = max([a["ap"] for a in brain.approvals], default=0) + 1
        brain.approvals.append({"ap": ap, "item": problem, "problem": problem, "status": "Pending",
                                "source": f"gmail:{its[-1]['id']}", "thread": its[-1].get("thread"),
                                "kind": its[0]["kind"], "count": len(its), "action_type": "Other"})
        report["raised"].append(problem)
    return report


# ------------------------------------------------------------------ review-approvals: Understanding replies
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
CONSEQUENTIAL = {"Send message", "Calendar with others", "Spend money", "Publish", "Financial record",
                 "Irreversible change"}


def _which(sentence, shown, numbering):
    # "that one", "this one" point at something, they aren't the number one
    low = re.sub(r"\b(that|this|which|the other|each) one\b", "\\1 item", sentence.lower())
    m = re.search(r"\b(\d+|" + "|".join(NUMBERS) + r")\b", low)
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else NUMBERS[m.group(1)]
        by_pos = shown[n - 1] if 0 < n <= len(shown) else None
        by_ap = next((s for s in shown if s["ap"] == n), None)
        if numbering == "position":
            return [by_pos] if by_pos else None
        if numbering == "ap":
            return [by_ap] if by_ap else None
        if by_pos and by_ap and by_pos is not by_ap:
            return None                               # could be either: ask
        return [by_pos or by_ap] if (by_pos or by_ap) else None
    for word, kind in (("invitation", "invitation"), ("purchase", "charge"), ("charge", "charge")):
        if word in sentence.lower():
            fits = [s for s in shown if s["kind"] == kind]
            if "those" in sentence.lower() or "these" in sentence.lower():
                return fits or None
            return fits if len(fits) == 1 else None
    return shown if len(shown) == 1 else None          # only one item on screen: "that one" is it


def interpret_reply(text, shown, numbering="position"):
    """Returns a list of (ap, meaning). meaning: approve | acknowledged | handled | not_mine |
    investigate | reject | confirm_first | clarify. Unmentioned items are left out (unchanged)."""
    out = []
    for s in [p.strip() for p in re.split(r"[.;\n]|, (?=[a-z]+ \w)", text) if p.strip()]:
        low = s.lower()
        targets = _which(s, shown, numbering)
        if targets is None:
            out.append((None, "clarify"))
            continue
        for item in targets:
            if re.search(r"isn't my problem|not my problem|not mine|isn't mine|don't keep bringing", low):
                meaning = "not_mine"
            elif re.search(r"already (checked|handled|did|sent)|i looked|i sent it", low):
                meaning = "handled"
            elif re.search(r"intentional|expected", low):
                meaning = "acknowledged"
            elif re.search(r"look into|find out|investigate|check on", low):
                meaning = "investigate"
            elif re.search(r"\b(reject|don't|no)\b", low):
                meaning = "reject"
            elif re.search(r"\b(approve|go ahead|send it|yes)\b", low) or low.startswith("decline"):
                meaning = "approve"
            elif re.search(r"\b(fine|ok|okay|looks good)\b", low):
                meaning = "confirm_first" if item["action_type"] in CONSEQUENTIAL else "acknowledged"
            else:
                meaning = "clarify"
            out.append((item["ap"], meaning))
    return out


def apply_reply(brain, decisions, today):
    """Acts only on clear permission. A part that couldn't be mapped ('clarify') touches nothing;
    the parts that mapped cleanly go ahead, and the owner is asked about the rest."""
    actions = []
    for ap, meaning in decisions:
        if ap is None or meaning in ("clarify", "confirm_first"):
            continue
        row = next(a for a in brain.approvals if a["ap"] == ap)
        if meaning == "approve":
            actions.append(("do", ap, row["action_type"]))
            # Calendar with others is done by the team; a send waits for the owner to press Send;
            # spending, publishing, financial and irreversible changes are always the owner's own steps.
            row["status"] = "Done" if row["action_type"] in ("Calendar with others", "Other") else "Handed to you"
        elif meaning in ("handled", "acknowledged"):
            close_item(brain, ap, meaning, "Owner: already handled" if meaning == "handled" else "Owner: acknowledged", today)
        elif meaning == "not_mine":
            close_item(brain, ap, "not_mine", "Owner: not my responsibility", today)
        elif meaning == "investigate":
            brain.assignments.append({"title": f"Look into AP-{ap}", "owner": "Operations", "status": "Planned",
                                      "source": row["source"] + ":investigate", "created_by": "team"})
            row["owner_note"] = (row.get("owner_note", "") + " Investigating").strip()
        elif meaning == "reject":
            row["status"] = "Rejected"
    return actions


# ------------------------------------------------------------------ run-modes.md: finding the Business Brain
def choose_brain(pages, mode, owner_pick=None):
    """Returns ('use', page) | ('ask', candidates) | ('stop', message)."""
    cands = [p for p in pages if p["title"] == "Business Brain"]
    if not cands:
        return "stop", "no Business Brain"
    if len(cands) == 1:
        return "use", cands[0]
    with_settings = [p for p in cands if p.get("settings")]
    if len(with_settings) == 1:
        return "use", with_settings[0]
    if mode == "attended":
        if owner_pick is not None:
            return "use", next(p for p in cands if p["id"] == owner_pick)
        return "ask", with_settings or cands
    return "stop", "Two Business Brains found in Notion, so I didn't touch either."


def write_record(brain_page, record):
    brain_page.setdefault("records", []).append(record)


# ------------------------------------------------------------------ setup Stage 3: confirmed vs. inferred
def save_website_summary(brain, facts, summary_yes, confirmed_items=()):
    """facts: (field, value, kind) with kind 'description' | 'price' | 'policy'. A yes to the summary
    saves descriptions only; prices and policies need their own confirmation."""
    for fld, value, kind in facts:
        if kind == "description" and summary_yes:
            brain.profile[fld] = value
        elif kind == "price" and fld in confirmed_items:
            brain.pricing[fld] = value
        elif kind == "policy" and fld in confirmed_items:
            brain.policies[fld] = value


def questions_to_ask(needed, brain_fields, said_in_chat):
    """Never ask what's saved or what the owner already said in this chat."""
    return [q for q in needed if q not in brain_fields and q not in said_in_chat]


# ------------------------------------------------------------------ team-roles.md: drafts and the Ready check
def make_draft(brain, body, owner_name="Owner"):
    voice = brain.brand.get("voice", "neutral")
    sign = brain.brand.get("sign_off")              # None = not set: never sign as the owner
    text = body if voice != "conversational" else body.replace("I am writing to", "Quick note:")
    if sign:
        text += f"\n\n{sign}"
    return {"text": text, "voice": voice, "sign_off": sign}


def apply_feedback(brain, draft, feedback, save=False):
    """Fix this draft now (same draft, no new approval); save as a preference only on a yes."""
    if "sign" in feedback:
        if draft["sign_off"]:
            draft["text"] = draft["text"].rsplit("\n\n", 1)[0]
        draft["sign_off"] = None
        if save:
            brain.brand["sign_off"] = ""             # owner chose: no signature
    if "formal" in feedback or "conversational" in feedback:
        draft["text"] = draft["text"].replace("I am writing to", "Quick note:")
        draft["voice"] = "conversational"
        if save:
            brain.brand["voice"] = "conversational"
    return draft


PLACEHOLDER = re.compile(r"\[[^\]]+\]|\{[^}]+\}|<[a-z ]+>|\bTBD\b|\bXX+\b|lorem ipsum|\binsert\b", re.I)
PROOF = re.compile(r"\d+%|\d[\d,]* (customers|users|members|marketers)|“[^”]+”\s*[-—]|\"[^\"]+\"\s*[-—]|rated #?\d", re.I)


def ready_check(text, brain, sources=()):
    """Returns the list of problems; an empty list means Ready."""
    problems = []
    if PLACEHOLDER.search(text):
        problems.append("placeholder")
    for claim in [m.group(0) for m in PROOF.finditer(text)]:
        if claim not in sources:
            problems.append(f"unsourced claim: {claim}")
    for price in re.findall(r"\$\d+(?:\.\d\d)?", text):
        if price not in {f"${v:g}" if isinstance(v, (int, float)) else v for v in brain.pricing.values()}:
            problems.append(f"unconfirmed price: {price}")
    for link in re.findall(r"https?://\S+", text):
        if link.rstrip(".,)") not in brain.links:
            problems.append(f"unknown link: {link}")
    if "Link needed" in text:
        problems.append("link needed")
    return problems


# ------------------------------------------------------------------ one recurring task per responsibility
def schedule_one(tasks, skill, when):
    """first-team-meeting / schedule-workforce: never a second task for one that exists (paused too)."""
    from notion_logic import matching_tasks
    if matching_tasks(tasks, skill):
        return tasks, "exists: offer to change its time"
    tasks.append({"prompt": f"[AI Workforce task: {skill} | prompt version 0.5.4]\n...", "when": when, "paused": False})
    return tasks, "created"
