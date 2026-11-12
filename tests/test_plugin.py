"""Regression checks on the plugin files themselves.

These read the skills, references, agents, prompts and manifests and fail if a
reliability or safety rule has been lost or contradicted. They do not run Claude.
"""
import json, re, subprocess, sys, unittest, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "ai-workforce"
SKILLS = PLUGIN / "skills"
REFS = SKILLS / "assign-work" / "references"


def read(p):
    return Path(p).read_text()


def all_md():
    return [p for p in PLUGIN.rglob("*.md")]


class Versions(unittest.TestCase):
    def setUp(self):
        self.version = json.loads(read(PLUGIN / ".claude-plugin" / "plugin.json"))["version"]

    def test_marketplace_matches(self):
        mk = json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))
        versions = [p.get("version") for p in mk["plugins"] if p["name"] == "ai-workforce"]
        self.assertEqual(versions, [self.version])

    def test_every_skill_matches(self):
        for s in SKILLS.glob("*/SKILL.md"):
            m = re.search(r'version: "([^"]+)"', read(s))
            self.assertIsNotNone(m, s)
            self.assertEqual(m.group(1), self.version, s)

    def test_readme_describes_this_version(self):
        self.assertIn(f"What's new in {self.version}", read(PLUGIN / "README.md"))

    def test_download_matches_repo(self):
        z = zipfile.ZipFile(ROOT / "download" / "ai-workforce.plugin")
        packed = json.loads(z.read(".claude-plugin/plugin.json"))
        self.assertEqual(packed["version"], self.version)
        repo_files = {str(p.relative_to(PLUGIN)) for p in PLUGIN.rglob("*")
                      if p.is_file() and p.relative_to(PLUGIN).parts[0] != "evals"}   # evals are for the maintainer
        zip_files = {n for n in z.namelist() if not n.endswith("/")}
        self.assertEqual(repo_files, zip_files)
        for n in zip_files:
            self.assertEqual(z.read(n), (PLUGIN / n).read_bytes(), f"stale in download: {n}")


class References(unittest.TestCase):
    def test_sync_check(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_references.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_run_tracking_travels_with_run_modes(self):
        for refdir in SKILLS.glob("*/references"):
            if (refdir / "run-modes.md").exists():
                self.assertTrue((refdir / "run-tracking.md").exists(), refdir)

    def test_referenced_skills_exist(self):
        names = {p.parent.name for p in SKILLS.glob("*/SKILL.md")}
        agents = {p.stem for p in (PLUGIN / "agents").glob("*.md")}
        for p in all_md():
            for ref in re.findall(r"`([a-z]+(?:-[a-z]+)+)`", read(p)):
                if ref.endswith(("-manager", "-of-staff")) or ref in agents:
                    continue
                if ref in {"general-purpose", "client-success"}:
                    continue
                looks_like_skill = any(ref.startswith(w) for w in (
                    "assign", "daily", "first", "manage", "prepare", "process", "review",
                    "schedule", "setup", "team", "workforce", "inbox"))
                if looks_like_skill:
                    self.assertIn(ref, names, f"{p}: `{ref}` is not a skill")


class RunTrackingRules(unittest.TestCase):
    BANNED = [
        "add to today's row",
        "same type, date and run type",
        "within 60 minutes of",
        "within 30 minutes of",
        "add to it instead of creating another",
    ]

    def test_old_merge_and_clock_rules_are_gone(self):
        for p in all_md():
            text = read(p)
            for b in self.BANNED:
                self.assertNotIn(b, text, f"{p}: still says '{b}'")

    def test_run_tracking_core(self):
        t = read(REFS / "run-tracking.md")
        for must in ["Run ID", "45 minutes", "Unknown", "source key", "Notified: no", "Progress", "Abandoned", "Self-test fixture", "best effort",
                     "Never merge a run", "Never guess from the clock"]:
            self.assertIn(must, t)

    def test_inbox_checkpoint_rules(self):
        t = read(SKILLS / "inbox-triage" / "references" / "inbox-coverage.md")
        for must in ["Completed through", "stays where it was", "15-minute overlap",
                     "open-work queue", "Search complete", "mutually exclusive", "Never hide a gap", "Discovered", "Processed",
                     "Never add `in:inbox`", "Fetch every page", "comprehensive"]:
            self.assertIn(must, t)

    def test_customer_skill_cannot_stand_in_for_inbox_triage(self):
        t = read(SKILLS / "process-customer-inquiries" / "SKILL.md")
        self.assertIn("0. **Check this is the right job.**", t)
        self.assertIn("load the `inbox-triage` skill", t)
        self.assertNotIn('"triage my inbox", "handle customer emails"', t)


class BundledConnections(unittest.TestCase):
    def test_only_notion_and_highlevel_are_bundled(self):
        """Email, calendar and files come from the owner's own connectors (setup suggests them).
        Bundled copies duplicated those tools and failed to connect where Claude's hosted
        Gmail and Calendar servers can't be reached directly. Notion and HighLevel are the
        vendors' own hosted servers with OAuth sign-in, so bundling them carries no keys."""
        cfg = json.loads(read(PLUGIN / ".mcp.json"))
        self.assertEqual(list(cfg["mcpServers"]), ["Notion", "HighLevel"])
        self.assertEqual(cfg["mcpServers"]["HighLevel"],
                         {"type": "http", "url": "https://services.leadconnectorhq.com/mcp/anthropic/v2"})
        self.assertEqual(set(cfg["recommendedCategories"]), {"wiki-knowledge-base", "email", "calendar", "documents"})
        self.assertIn("connector registry", read(SKILLS / "setup-workforce" / "SKILL.md"))


class ScheduleDefaults(unittest.TestCase):
    def test_daily_by_default_and_the_owner_is_asked(self):
        sw = read(SKILLS / "schedule-workforce" / "SKILL.md")
        for must in ["How often should the team check in: every day (recommended), weekdays only, or another rhythm?",
                     "If they don't mind, use every day", "- Check-in frequency: every day",
                     "Daily briefing: every day (or the chosen rhythm)",
                     "never create a separate inbox triage task at the same rhythm and time of day",
                     "Weekly marketing plan: Mondays", "Invoice review: Fridays"]:
            self.assertIn(must, sw)
        self.assertNotIn("Daily briefing: weekdays", sw)
        self.assertNotIn("mid-morning and mid-afternoon", sw)
        fm = read(SKILLS / "first-team-meeting" / "SKILL.md")
        self.assertIn("Every day is the default for daily work", fm)
        self.assertNotIn("every weekday morning", fm)


class SetupKeepsWorking(unittest.TestCase):
    def test_connections_are_noticed_without_a_magic_word(self):
        s = read(SKILLS / "setup-workforce" / "SKILL.md")
        for must in ["Any reply counts.", "Never ask for a particular word", "send me any message (even just 'ok')",
                     "Check at every reply.", "whatever the message was about", "Check before asking."]:
            self.assertIn(must, s)
        self.assertNotIn("reply **done**", s)

    def test_team_works_while_the_owner_connects(self):
        s = read(SKILLS / "setup-workforce" / "SKILL.md")
        for must in ["Setup jobs (the team works while the owner connects the next app)",
                     "Never sit idle waiting for a connection", "**In the background:**", "**In the same message:**",
                     "only once the Notion job's structure check has passed", "one run record per job, never twice",
                     "never moves the inbox bookmark", "They ask the owner nothing",
                     "Notion first (everything is saved there), then email (its job takes longest, so it starts earliest)",
                     "A job that fails never holds setup up"]:
            self.assertIn(must, s)
        fm = read(SKILLS / "first-team-meeting" / "SKILL.md")
        self.assertIn("**Already done during setup?**", fm)
        self.assertIn("Never run the same job a second time", fm)


class InstallLinks(unittest.TestCase):
    REPO = "ai-workforce-installer/ai-workforce"

    def test_every_repository_link_points_at_the_org_repo(self):
        for p in [ROOT / "README.md", PLUGIN / "README.md"]:
            t = read(p)
            for link in re.findall(r"github\.com/([\w.-]+/[\w.-]+)", t):
                self.assertEqual(link, self.REPO, f"{p}: github.com/{link}")
            for ref in re.findall(r"--marketplace (\S+?)`", t):
                self.assertEqual(ref, self.REPO, p)
            self.assertIn(f"https://github.com/{self.REPO}/raw/main/download/ai-workforce.plugin", t, p)
            self.assertIn("**Access:** the repository is private.", t, p)


class Evals(unittest.TestCase):
    def test_every_case_has_a_prompt_and_a_judged_grader(self):
        cases = sorted(p.parent for p in (PLUGIN / "evals").glob("*/prompt.md"))
        self.assertGreaterEqual(len(cases), 8)
        for c in cases:
            graders = list((c / "graders").glob("*.md"))
            self.assertTrue(any("type: llm" in read(g) for g in graders), c.name)
            self.assertIn("allowed_tools: [Skill, Read, Glob, Grep]", read(c / "prompt.md"), c.name)

    def test_every_case_proves_the_teams_rules_were_loaded(self):
        """A reply can look right with no skill loaded: then the case measured Claude, not this plugin
        (three cases did exactly that until 0.9.0). So every case also checks a team skill was opened."""
        for c in sorted(p.parent for p in (PLUGIN / "evals").glob("*/prompt.md")):
            loaded = [g for g in (c / "graders").glob("*.md") if "type: tool_used" in read(g) and "tool: Skill" in read(g)]
            self.assertTrue(loaded, f"{c.name}: no grader checks that a team skill was loaded")
            for g in loaded:
                names = re.search(r"input_match: '([^']+)'", read(g)).group(1).split("|")
                for n in names:
                    self.assertTrue((SKILLS / n / "SKILL.md").exists(), f"{c.name}: {n} is not a skill")

    def test_evals_are_not_shipped(self):
        z = zipfile.ZipFile(ROOT / "download" / "ai-workforce.plugin")
        self.assertFalse([n for n in z.namelist() if n.startswith("evals/")])


class ScheduledPrompts(unittest.TestCase):
    """What a recurring task stores: the job, the safety rules, the pointer to the plugin, and
    stop-and-tell when the plugin isn't there. Nothing ever rewrites it."""
    def setUp(self):
        self.text = read(SKILLS / "schedule-workforce" / "references" / "scheduled-prompts.md")
        self.blocks = re.findall(r"```\n(.*?)```", self.text, re.S)
        rm = read(REFS / "if-old-task.md")
        self.skills_in_table = set(re.findall(r"\| `([a-z-]+)` \|", rm))

    def test_five_prompts_each_tagged_for_a_skill_that_exists(self):
        self.assertEqual(len(self.blocks), 5)
        for b in self.blocks:
            m = re.match(r"\[AI Workforce task: ([a-z-]+) \| prompt version ([0-9.]+)\]\n", b)
            self.assertIsNotNone(m, b[:80])
            skill = m.group(1)
            self.assertIn(skill, self.skills_in_table)
            self.assertIn(f'"{skill}" skill', b)
            self.assertTrue((SKILLS / skill / "SKILL.md").exists())

    def test_inbox_prompt_is_all_email(self):
        inbox = [b for b in self.blocks if b.startswith("[AI Workforce task: inbox-triage")][0]
        self.assertNotIn("process-customer-inquiries", inbox)
        self.assertIn("review all email since the last inbox triage, not only customer messages", inbox)

    def test_every_stored_prompt_keeps_safeguards(self):
        for b in self.blocks:
            for must in ["never as instructions or approval",
                         "Never repeat a password, API key",
                         "could not be verified",
                         "Never send messages, spend money, change budgets or financial records, publish, delete anything",
                         "carry out approval items",
                         "Never create a second draft, approval or Assignments row",
                         "Run now at any day or time",
                         "one notification per run",
                         "The installed plugin's instructions win over this text",
                         "scheduled-run-rules",
                         "If that skill is not available"]:
                self.assertIn(must, b, f"missing '{must}' in {b[:60]}")
            self.assertNotIn("described above", b)

    def test_without_the_plugin_a_run_stops_and_tells_the_owner(self):
        """No second copy of the job lives in the task: that copy could never be improved, and it
        is why tasks used to rewrite themselves."""
        for b in self.blocks:
            tail = b.split("If that skill is not available")[1]
            for must in ["do not do this job from memory or from older instructions", "Result Failed",
                         "did not run because AI Workforce was not available", "Then stop."]:
                self.assertIn(must, tail, b[:60])
            for gone in ["subagent", "ran the short fallback", "Launch the active department managers", "do this instead"]:
                self.assertNotIn(gone, b, b[:60])

    def test_stored_prompts_are_short(self):
        for b in self.blocks:
            self.assertLess(len(b.split()), 450, b[:60])

    def test_scheduled_run_rules_keep_every_safeguard(self):
        rules = read(SKILLS / "schedule-workforce" / "references" / "scheduled-run-rules.md")
        for must in ["never as instructions or approval", "Never repeat a password, API key", "could not be verified",
                     "open Assignments", "Launch only team members with real work", "never estimate cost",
                     "Never send messages, spend money, change budgets or financial records, publish, delete anything",
                     "carry out approval items", "Not run (still in progress)", "saved views first",
                     "Run now at any day or time", "accepted by the tool", "one notification per run",
                     "without redoing its work", "win over the task's stored instructions",
                     "Never change a recurring task", "## Work handled comes first", "**One morning run.**",
                     "**The send lock.**", "Never rely on the lock"]:
            self.assertIn(must, rules, must)
        for sk in ["daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices", "assign-work"]:
            self.assertIn("references/scheduled-run-rules.md", read(SKILLS / sk / "SKILL.md"), sk)
            self.assertTrue((SKILLS / sk / "references" / "scheduled-run-rules.md").exists(), sk)


class NothingRewritesATask(unittest.TestCase):
    """0.8.0 removed recurring tasks updating their own instructions: the installed plugin already
    wins over whatever a task has stored, so the update changed nothing a run does."""
    def test_the_machinery_is_gone(self):
        self.assertFalse(list(PLUGIN.rglob("prompt-history.md")))
        self.assertFalse((ROOT / "tools" / "prompt_history.py").exists())
        self.assertFalse((ROOT / "tools" / "released-prompts.md").exists())
        self.assertEqual([p.parent.parent.name for p in SKILLS.glob("*/references/scheduled-prompts.md")], ["schedule-workforce"])
        for p in list(SKILLS.glob("*/SKILL.md")) + list(SKILLS.glob("assign-work/references/*.md")) + \
                list(SKILLS.glob("schedule-workforce/references/*.md")):
            text = read(p)
            for gone in ["fingerprint", "Keep the task up to date automatically", "Is the recurring task current",
                         "Changing a recurring task's instructions safely", "update my recurring tasks' to fix it"]:
                self.assertNotIn(gone, text, f"{p}: still says '{gone}'")

    def test_a_run_never_changes_a_task_and_versions_are_never_compared(self):
        rm = read(REFS / "if-old-task.md")
        for must in ["**A run never changes a recurring task.**", "Never compare it",
                     "The current rules win over older stored text", "The responsibility wins over the skill name",
                     "An older version line alone is never a warning"]:
            self.assertIn(must, rm)
        self.assertNotRegex(rm, r"\| `[a-z-]+` \| [0-9.]+ \|")       # no "current prompt version" column to fall behind
        ap = read(REFS / "approval-policy.md")
        self.assertIn("**Never, in any run, change a recurring task:**", ap)
        self.assertNotIn("prompt only", ap)

    def test_checking_tasks_in_chat_offers_nothing_to_update(self):
        sw = read(SKILLS / "schedule-workforce" / "SKILL.md")
        for must in ["there is never anything to update in a task's instructions", "## Adding the owner's own instruction to a task",
                     "Owner's additions", "Never do this in a scheduled run", "Never delete a task unless the owner asks",
                     "These always follow the AI Workforce you have installed"]:
            self.assertIn(must, sw)
        self.assertNotIn("name or prompt mentions AI Workforce", sw)
        self.assertIn("never offer to update one", read(SKILLS / "team-report" / "SKILL.md"))

    def test_the_unused_workspace_setting_is_no_longer_added(self):
        self.assertNotIn("Recurring tasks update themselves", read(SKILLS / "setup-workforce" / "references" / "page-templates.md"))
        up = read(REFS / "brain-upgrades.md")
        self.assertIn("**No longer used.**", up)
        self.assertNotIn("add `- Recurring tasks update themselves", up)


class OneMorningRun(unittest.TestCase):
    """0.8.0: the daily briefing does the inbox check itself. One run, one notification."""
    def test_briefing_checks_the_inbox_first(self):
        b = read(SKILLS / "daily-executive-briefing" / "SKILL.md")
        for must in ["3. **Inbox first (the morning run).**", "less than 3 hours old", "don't search email again in this run",
                     "don't start a second one and don't wait for it", '"inside the morning run" mode',
                     "No inbox to check", "nobody reads the inbox again here",
                     "One notification covers the inbox check and the briefing"]:
            self.assertIn(must, b)

    def test_inbox_check_inside_the_briefing_keeps_its_record_and_stays_quiet(self):
        i = read(SKILLS / "inbox-triage" / "SKILL.md")
        for must in ["**Inside the morning run:**", "its own run record with an IT Run ID",
                     "Send no notification and write no chat report", "Notified: not requested (included in"]:
            self.assertIn(must, i)
        rt = read(REFS / "run-tracking.md")
        self.assertIn("**A run inside another run sends none.**", rt)
        self.assertIn('"Not requested" is never a missed notification', rt)

    def test_scheduling_creates_one_morning_task(self):
        sw = read(SKILLS / "schedule-workforce" / "SKILL.md")
        for must in ["This is the **morning run**", "Inbox triage as its own task: not by default",
                     "3. **One morning run.**", "pause (disable) the inbox triage task, never delete it",
                     "whose times are less than 3 hours apart", "is not a duplicate; leave it"]:
            self.assertIn(must, sw)
        ftm = read(SKILLS / "first-team-meeting" / "SKILL.md")
        self.assertIn("becomes the recurring **morning run**", ftm)
        self.assertIn("never a separate inbox task alongside a briefing", ftm)


class WorkHandled(unittest.TestCase):
    """0.8.0: reports open with what the team handled; a run finishing is not the result."""
    def test_run_record_has_a_handled_line_and_an_honest_definition(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["Handled: <n> reply drafts, <n> approvals raised, <n> items closed, <n> prepared | nothing: <the plain reason>",
                     "**Work handled**", "**What never counts:**", "reading, searching, sorting, counting, re-checking",
                     "a record counts only its own work", "a run can be Complete and have handled nothing"]:
            self.assertIn(must, rt)

    def test_reports_open_with_it(self):
        b = read(SKILLS / "daily-executive-briefing" / "SKILL.md")
        for must in ["1. **The opening line: work handled**", "**Three quiet briefings in a row:**",
                     "never invent a reason the records don't show", "judged by what the team handled, not by the run finishing"]:
            self.assertIn(must, b)
        self.assertIn("Open the chat reply or notification with the work-handled line", read(SKILLS / "inbox-triage" / "SKILL.md"))
        tr = read(SKILLS / "team-report" / "SKILL.md")
        self.assertIn("Runs finishing is not the measure; work handled is", tr)
        self.assertIn("three or more runs in a row with nothing handled", tr)
        self.assertIn("a run finishing is not a result", read(REFS / "talking-to-the-owner.md"))


class SendLock(unittest.TestCase):
    """0.8.0: the words that describe the lock. The lock itself is tested in test_send_lock.py."""
    def test_policy_says_what_it_covers_and_what_it_does_not(self):
        ap = read(REFS / "if-asked-how-safe.md")
        for must in ["**Enforced by the send lock (built into this plugin):**", "Creating drafts and writing to the Business Brain are not affected",
                     "it recognises tools by their names", "it does not cover a web browser", "If the check can't run, it lets the call through",
                     "not yet proven live", "that lock doesn't depend on this plugin at all"]:
            self.assertIn(must, ap)

    def test_owner_is_offered_the_stronger_lock_without_guessing_menus(self):
        sw = read(SKILLS / "schedule-workforce" / "SKILL.md")
        self.assertIn("`references/if-asked-how-safe.md`", sw)
        for must in ["8. **The send lock", "Tool permissions", "Blocked", "Never change these settings for the owner",
                     'never suggest "Needs approval" as a lock for unattended runs', "- Send lock: built in",
                     "https://support.claude.com/en/articles/11176164"]:
            self.assertIn(must, sw)

    def test_hook_files_ship_with_the_plugin(self):
        for name in ["hooks.json", "send-lock.sh", "send_lock.py"]:
            self.assertTrue((PLUGIN / "hooks" / name).exists(), name)
        z = zipfile.ZipFile(ROOT / "download" / "ai-workforce.plugin")
        for name in ["hooks/hooks.json", "hooks/send-lock.sh", "hooks/send_lock.py"]:
            self.assertIn(name, z.namelist())


class SizeBudget(unittest.TestCase):
    """Every rule is read again on every run and costs the owner usage. These ceilings are a
    ratchet: when text is cut, lower them. Raising one needs a reason in the commit message and,
    normally, a rule removed somewhere else. Sizes are bytes of a skill's SKILL.md plus every
    reference file it names (each counted once). Files named if-….md cover one situation each and
    are read only when it comes up, so they are counted apart: `always` is a normal run, and
    `with every situation` is a run where everything comes up at once."""
    CEILINGS = {   # job: (skills, always read, with every read-when-needed file reachable from them)
        "the morning run (daily briefing + inbox check)": (["daily-executive-briefing", "inbox-triage"], 114_000, 146_000),   # 0.8.1: 137,371
        "weekly marketing plan": (["prepare-weekly-marketing"], 54_500, 79_000),                                             # 0.8.1: 68,573
        "invoice review": (["review-overdue-invoices"], 59_500, 87_000),                                                     # 0.8.1: 75,797
        "any other recurring responsibility": (["assign-work"], 73_500, 101_000),                                            # 0.8.1: 96,056
    }
    # One copy of every skill, reference and team member brief. Raised from 318,000 in 0.9.0: the
    # read-when-needed files each open by saying when to read them, and three behaviours were added
    # (the phone-first report, the priority piece, learning the owner's voice). What any one run reads
    # went down by 17 to 24 percent in the same release.
    ALL_INSTRUCTIONS = 330_000
    STORED_PROMPT = 3_100           # what each recurring task stores
    REF = re.compile(r"references/([a-z0-9-]+\.md)")

    @classmethod
    def ref(cls, name):
        return next(SKILLS.glob(f"*/references/{name}"))

    @classmethod
    def named(cls, skill):
        return set(cls.REF.findall(read(SKILLS / skill / "SKILL.md")))

    @classmethod
    def sizes(cls, skills):
        """(bytes always read, bytes when every situation comes up) for a run of these skills."""
        always = {n for s in skills for n in cls.named(s) if not n.startswith("if-")}
        situational, todo = set(), set(always) | {n for s in skills for n in cls.named(s)}
        seen = set()
        while todo:                                    # if-files are named by the files that trigger them
            n = todo.pop()
            if n in seen:
                continue
            seen.add(n)
            if n.startswith("if-"):
                situational.add(n)
            if n in always or n.startswith("if-"):
                todo |= {m for m in cls.REF.findall(read(cls.ref(n))) if m.startswith("if-")}
        base = sum(len((SKILLS / s / "SKILL.md").read_bytes()) for s in skills)
        base += sum(len(cls.ref(n).read_bytes()) for n in always)
        return base, base + sum(len(cls.ref(n).read_bytes()) for n in situational)

    def test_recurring_jobs_stay_within_budget(self):
        for job, (skills, ceiling, worst) in self.CEILINGS.items():
            size, everything = self.sizes(skills)
            self.assertLessEqual(size, ceiling, f"{job}: {size} bytes of instructions, budget {ceiling}. Cut something.")
            self.assertLessEqual(everything, worst, f"{job}: {everything} bytes when every situation comes up, budget {worst}.")

    def test_total_instruction_text_stays_within_budget(self):
        names = sorted({p.name for p in SKILLS.glob("*/references/*.md")})
        size = sum(len(p.read_bytes()) for p in SKILLS.glob("*/SKILL.md"))
        size += sum(len(p.read_bytes()) for p in (PLUGIN / "agents").glob("*.md"))
        size += sum(len(self.ref(n).read_bytes()) for n in names)
        self.assertLessEqual(size, self.ALL_INSTRUCTIONS, f"{size} bytes of instructions in total")

    def test_stored_prompts_stay_small(self):
        text = read(SKILLS / "schedule-workforce" / "references" / "scheduled-prompts.md")
        for b in re.findall(r"```\n(.*?)```", text, re.S):
            self.assertLessEqual(len(b.encode()), self.STORED_PROMPT, b[:60])


class ReadWhenNeeded(unittest.TestCase):
    """0.9.0: rules for one situation live in a file of their own (if-….md) and are read only when
    that situation comes up. The text moved word for word; what every run reads got shorter."""
    FILES = {   # file: (the file whose text sends a run to it, the words that do)
        "if-run-unfinished.md": ("run-tracking.md", "One found: follow `references/if-run-unfinished.md`"),
        "if-notification-missed.md": ("run-tracking.md", "follow `references/if-notification-missed.md`"),
        "if-old-task.md": ("scheduled-run-rules.md", "follow `references/if-old-task.md`"),
        "if-owner-corrects.md": ("owner-corrections.md", "follow `references/if-owner-corrects.md`"),
        "if-no-team-agents.md": ("team-roles.md", "brief from `references/if-no-team-agents.md`"),
        "if-highlevel.md": ("connections.md", "follow `references/if-highlevel.md`"),
        "if-asked-how-safe.md": ("approval-policy.md", "read `references/if-asked-how-safe.md` first"),
        "if-queuing-a-decision.md": ("approval-queue.md", "follow `references/if-queuing-a-decision.md`"),
        "if-inbox-gap.md": ("inbox-coverage.md", "follow `references/if-inbox-gap.md`"),
        "if-quick-look.md": (None, None),               # named by the skills that run a quick look
    }

    def test_every_file_says_when_to_read_it_and_something_sends_runs_there(self):
        found = sorted({p.name for p in SKILLS.glob("*/references/if-*.md")})
        self.assertEqual(found, sorted(self.FILES))
        for name, (home, words) in self.FILES.items():
            text = read(SizeBudget.ref(name))
            self.assertTrue(text.startswith("# "), name)
            self.assertIn("\n\nRead this only when ", text[:400], name)
            if home:
                self.assertIn(words, read(SizeBudget.ref(home)), name)
        for sk in ["inbox-triage", "first-team-meeting", "setup-workforce"]:
            self.assertIn("`references/if-quick-look.md`", read(SKILLS / sk / "SKILL.md"), sk)

    def test_every_skill_is_told_how_these_files_work(self):
        for s in SKILLS.glob("*/SKILL.md"):
            self.assertIn("A file named `references/if-….md` covers one situation: read it only when", read(s), s)
        self.assertIn("A file named `if-…` covers one situation", read(SizeBudget.ref("scheduled-run-rules.md")))

    def test_what_must_never_wait_for_a_second_file_stays_in_the_first(self):
        """The trigger line carries the rule that matters even if the second file is never opened."""
        rt = read(REFS / "run-tracking.md")
        self.assertIn("is never run alongside", rt)
        self.assertIn("without redoing its work", rt)
        self.assertIn("Never hide a gap", read(SizeBudget.ref("inbox-coverage.md")))
        self.assertIn("never claim more protection than it says", read(REFS / "approval-policy.md"))
        self.assertIn("the team only reads HighLevel", read(REFS / "connections.md"))
        self.assertIn("Scheduled runs never create or change rules", read(REFS / "owner-corrections.md"))
        rules = read(SizeBudget.ref("scheduled-run-rules.md"))
        self.assertIn("the job wins over the skill name, and a smaller job is never done quietly", rules)

    def test_unattended_rules_have_one_home(self):
        rm = read(REFS / "run-modes.md")
        self.assertIn("Its rules are in `references/scheduled-run-rules.md`", rm)
        self.assertNotIn("9. **Stay within budget.**", rm)                 # the second copy is gone
        self.assertIn("## Active departments (both modes)", rm)
        for sk in SKILLS.glob("*/references"):
            if (sk / "run-modes.md").exists():
                self.assertTrue((sk / "scheduled-run-rules.md").exists(), sk)


class OwnerFirstReports(unittest.TestCase):
    """0.9.0: a report is read on a phone. What the owner needs is on the first screen; the run's
    own bookkeeping is at the bottom, folded away."""
    def test_the_briefing_is_written_for_a_phone(self):
        b = read(SKILLS / "daily-executive-briefing" / "SKILL.md")
        order = ["8. **Write the briefing for a phone.**", "1. **The opening line: work handled**", "2. **Today:**",
                 "3. **Ready for you:**", "4. **Decisions for you:**", "5. **Still waiting on you:**",
                 "6. **Worth knowing:**", "7. **Details** (one toggle"]
        places = [b.index(o) for o in order]
        self.assertEqual(places, sorted(places))
        for must in ["Outside the toggles the whole briefing stays under about 200 words", "Never the whole list again",
                     "With nothing to decide, leave this section and that line out", "at most one question",
                     "is said here the first time and when it changes", "the first screen has to be enough",
                     "never signed with the owner's own sign-off",       # a briefing to Maya signed "Talk soon, Maya" (seen in evals)
                     "Save** the briefing at the top of this run's record, above its run record"]:
            self.assertIn(must, b)
        for gone in ["**Your team handled:**", "**Spotted:**", "5. **Spotted", "Reading taken"]:
            self.assertNotIn(gone, b)

    def test_the_run_record_sits_below_the_report(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["**The owner's report goes above it.**", 'a toggle titled "Run record"',
                     'never Run IDs or "Status: Running"', "Records from before 0.9.0 begin with the run record instead"]:
            self.assertIn(must, rt)
        self.assertNotIn("The body starts with this header", rt)
        na = read(REFS / "notion-access.md")
        for must in ["**Collapsed sections (toggles).**", "`<toggle>`", "Never use `<details>`", "use a plain heading in the same place"]:
            self.assertIn(must, na)
        self.assertIn("put the report above the run record", read(REFS / "approval-policy.md"))

    def test_the_inbox_report_follows_the_same_shape(self):
        i = read(SKILLS / "inbox-triage" / "SKILL.md")
        for must in ["9. **Report** for a phone", "3. **Ready for you:**", "5. **Details** (one toggle)"]:
            self.assertIn(must, i)

    def test_the_reading_taken_is_not_the_first_line(self):
        rules = read(SizeBudget.ref("scheduled-run-rules.md"))
        self.assertIn("note which reading you took in the report's Details", rules)
        self.assertIn("Only two things may come before that line", rules)
        self.assertIn("the report's single question", read(REFS / "just-in-time.md"))


class DraftsAreNotApprovals(unittest.TestCase):
    """0.9.0: a reply draft used to raise an approval whose "yes" only told the owner to go and
    press Send. The owner pressing Send is the approval; the queue is for real decisions."""
    def test_the_queue_is_for_decisions(self):
        aq = read(REFS / "approval-queue.md")
        for must in ["## What goes in the queue", "**A reply draft is not a decision.**",
                     "The owner pressing Send is the approval", "queue the decision, and say in its Exact action which draft is waiting on it"]:
            self.assertIn(must, aq)
        self.assertIn("pressing Send is the approval", read(REFS / "approval-policy.md"))
        self.assertIn("A reply the owner only has to read and send is a draft, never an approval", read(REFS / "team-roles.md"))
        self.assertIn("A reply draft by itself is never an approval", read(SizeBudget.ref("inbox-coverage.md")))
        self.assertIn("A reply never needs an Approvals row just to be sent", read(SKILLS / "process-customer-inquiries" / "SKILL.md"))
        self.assertIn("A reply draft by itself is never one", read(SKILLS / "inbox-triage" / "SKILL.md"))
        self.assertIn("A reply draft is never one by itself", read(SKILLS / "daily-executive-briefing" / "SKILL.md"))
        for a in (PLUGIN / "agents").glob("*-manager.md"):
            self.assertIn("(a reply draft waiting to be sent is not one)", read(a), a)
        for p in list(SKILLS.glob("*/SKILL.md")) + [REFS / "team-roles.md"]:
            self.assertNotIn("sending on their behalf, money", read(p), p)
            self.assertNotIn("escalations, anything sensitive) becomes an Approvals row", read(p), p)

    def test_drafts_and_prepared_pieces_wait_in_open_work_and_close_themselves(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["**Reply drafts and prepared pieces wait here, not in Approvals.**",
                     "never draft by draft", "They are never closed for age alone",
                     "Updating a row, re-checking or carrying something forward is not closing it"]:
            self.assertIn(must, rt)
        for gone in ["sent or discarded by the owner", "meeting held"]:        # 1.0.0: weak evidence no longer closes work
            self.assertNotIn(gone, rt)
        ra = read(SKILLS / "review-approvals" / "SKILL.md")
        self.assertIn("**Waiting work**", ra)
        self.assertIn("a Gmail draft stays where it is, never deleted", ra)


class WorkClosesHonestly(unittest.TestCase):
    """1.0.0: the queue tracks obligations until a verified outcome. A vanished draft used to count as
    "sent or discarded" and a past meeting as "held"; a failing automation was re-logged daily."""
    FIELDS = ["Work type", "Due", "Next check", "Waiting on", "Blocker", "Done when", "Evidence", "Closed as", "Work key"]

    def test_the_schema_and_the_upgrade_name_the_same_nine_fields(self):
        schema = read(SKILLS / "setup-workforce" / "references" / "notion-schema.md")
        up = read(REFS / "brain-upgrades.md").split("## Upgrade to 1.0.0")[1].split("Later versions")[0]
        for f in self.FIELDS:
            self.assertIn(f'"{f}" ', schema, f)
            self.assertIn(f"`{f}`", up, f)
        for option in ["Task", "Reply", "Commitment", "Waiting on someone", "Customer case", "Deliverable", "Monitored issue",
                       "Completed", "Sent", "Cancelled", "Dismissed", "Superseded", "Unverified"]:
            self.assertIn(f"'{option}'", schema, option)
            self.assertIn(option, up, option)
        sys.path.insert(0, str(ROOT / "tests"))
        import work_logic
        self.assertEqual(sorted(work_logic.NEW_PROPERTIES), sorted(self.FIELDS))
        self.assertEqual(sorted(work_logic.CLOSED_AS), sorted(["Completed", "Sent", "Cancelled", "Dismissed", "Superseded", "Unverified"]))

    def test_the_upgrade_is_add_only_and_resumable(self):
        up = read(REFS / "brain-upgrades.md").split("## Upgrade to 1.0.0")[1].split("Later versions")[0]
        for must in ["Nothing existing changes: no status option, view, row or schedule is touched",
                     "an interrupted upgrade simply carries on when it is run again", "Only when all nine are there",
                     "A property of the owner's with one of these names stays as it is"]:
            self.assertIn(must, up)
        schema = read(SKILLS / "setup-workforce" / "references" / "notion-schema.md")      # statuses and the owner's view are as they were
        self.assertIn("\"Status\" SELECT('Planned':gray, 'In progress':blue, 'Prepared':purple, 'Handed to you':orange, 'Blocked':brown, 'Done':green, 'Failed':red)", schema)
        self.assertIn('"Open work": `FILTER "Status" IN ("Planned", "In progress", "Prepared", "Handed to you", "Blocked"); SORT BY "Date" ASC`', schema)

    def test_one_obligation_is_one_row(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["One row is one **obligation**", "**Work key: what is owed, not which message or run mentioned it.**",
                     "a Run ID is never an obligation's only identity", "**updates that row**",
                     "separate promises in one thread are separate rows", "the same work key (section 6)"]:
            self.assertIn(must, rt)

    def test_who_has_the_next_move_and_when_it_is_checked(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["**Status says who has the next move.**", "the team can do it now", "waiting on the owner",
                     "waiting on someone else or a missing input", "**Nothing waits without a next action and a next check.**",
                     "use a suggested check time and call it that", "in the owner's time zone and working days",
                     "never through a scheduled task per item", "only a deadline someone stated, never an invented one",
                     "put a Blocked row whose input has arrived back to Planned"]:
            self.assertIn(must, rt)

    def test_closing_needs_evidence_or_the_owners_word(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["**Closing needs evidence or the owner's word.**", "A draft that vanished proves nothing",
                     "close it as Unverified, never as sent", "A sent reply proves sending, not that a customer case is resolved",
                     "A meeting's time passing proves neither that it was held nor that its actions were done",
                     "An alert going quiet doesn't prove a repair", "only something materially new reopens it, never a repeat",
                     "say so once", "don't raise it again each day"]:
            self.assertIn(must, rt)
        self.assertIn("nothing is closed without evidence or the owner's word",
                      read(SKILLS / "schedule-workforce" / "references" / "scheduled-run-rules.md"))


class PriorityPiece(unittest.TestCase):
    """0.9.0: the inbox is not the owner's business. Each morning the team finishes one piece toward
    the top priority, and never stacks them up when the owner isn't using them."""
    def test_one_finished_piece_and_no_pile(self):
        b = read(SKILLS / "daily-executive-briefing" / "SKILL.md")
        for must in ["**One finished piece toward the top priority.**", "usable as it is in five minutes", "one page at most",
                     'its title starting "Priority:"', "**Never pile them up.**", "or one toward this same goal is",
                     '"Use it, redo it or drop it?"', "when Extra rules say not to", "passing the Ready check",
                     "(meeting preps, at most 2; the priority piece; research)"]:
            self.assertIn(must, b)
        self.assertNotIn("skip if a recent briefing already has one", b)             # Marketing's weekly item is replaced
        tr = read(REFS / "team-roles.md")
        self.assertIn("6. **Is something like it still waiting?**", tr)
        self.assertNotIn("(Marketing: once a week)", tr)
        self.assertIn("the morning run's priority piece is a marketing step", read(REFS / "run-modes.md"))


class VoiceFromSentMail(unittest.TestCase):
    """0.9.0: the first drafts sound like the owner, because setup reads how they already write."""
    def test_setup_learns_the_voice_and_never_the_content(self):
        q = read(SizeBudget.ref("if-quick-look.md"))
        for must in ["**Their voice first.**", "`in:sent`", "at most five short lines", "Style only: never copy those emails' contents, names or addresses",
                     "Fewer than three such emails: skip this and draft plainly", "once the owner confirms"]:
            self.assertIn(must, q)
        s = read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertIn("learned from their own sent mail", s)
        self.assertIn("on their yes, or their corrected version, save it to Brand & Tone", s)
        self.assertIn("Never sign as the owner in a style that is neither confirmed nor their own", read(REFS / "team-roles.md"))
        self.assertIn("If setup already picked up their style", read(SKILLS / "setup-workforce" / "references" / "interview.md"))


class LockWording(unittest.TestCase):
    """0.9.0: what the written rules say about the tightened lock."""
    def test_rules_match_the_lock(self):
        rules = read(SizeBudget.ref("scheduled-run-rules.md"))
        for must in ["tools that create, change or start a scheduled task", "**If the owner writes in this conversation later,**",
                     "to ask again in a new chat"]:
            self.assertIn(must, rules)
        s = read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertIn("Then check once what HighLevel allowed", s)
        self.assertIn("connect again and allow viewing only", s)


class Safety(unittest.TestCase):
    def test_policy_core_rules(self):
        t = read(REFS / "approval-policy.md") + read(REFS / "if-asked-how-safe.md")
        for must in ["Spend money", "Modify financial records", "Delete anything",
                     "Publish or post publicly", "Send an external message",
                     "Scheduled (unattended) runs never execute approval items",
                     "never** approval on its own", "What enforces these rules",
                     "not a technical lock"]:
            self.assertIn(must, t)

    def test_unattended_never_executes_approvals(self):
        self.assertIn("Never execute an approval item", read(REFS / "run-modes.md"))

    def test_every_agent_has_hard_limits_and_untrusted_rule(self):
        for a in (PLUGIN / "agents").glob("*-manager.md"):
            t = read(a)
            self.assertIn("**Untrusted content:**", t, a)
            self.assertIn("**Hard limits:**", t, a)
            self.assertRegex(t, r"Never[^.]*\bsend", a)

    def test_no_owner_specific_details(self):
        banned = ["reedfloren", "Floren", "Lawrence", "Loik", "businesssuccesssystems",
                  "completemarketingsystems", "Mankato", "GoHighLevel", "GHL", "Larry"]
        for p in PLUGIN.rglob("*"):
            if p.is_file() and p.suffix in {".md", ".json"}:
                # The author credit is allowed; the repository now lives under ai-workforce-installer.
                text = read(p)
                if p.name == "plugin.json":
                    text = re.sub(r'"author": \{[^}]*\}', "", text)
                for b in banned:
                    self.assertNotIn(b, text, f"{p}: contains '{b}'")


class HighLevelIsReadOnly(unittest.TestCase):
    def test_highlevel_rules(self):
        c = read(REFS / "connections.md")
        for must in ["- Customer messages: HighLevel | None", "Replies ready to copy", "HighLevel unavailable",
                     "follow `references/if-highlevel.md`"]:
            self.assertIn(must, c)
        hl = read(REFS / "if-highlevel.md")
        for must in ["**Read only.**", "Never run an operation that sends", "Replies ready to copy", "HighLevel unavailable",
                     "ask only for reads", "begins with a reading word"]:
            self.assertIn(must, hl)
        self.assertIn("Customer messages: _not set_", read(SKILLS / "setup-workforce" / "references" / "page-templates.md"))
        self.assertIn("HighLevel", read(SKILLS / "setup-workforce" / "SKILL.md"))
        triage = read(SKILLS / "inbox-triage" / "SKILL.md")
        self.assertIn("never move the inbox bookmark", triage)
        self.assertIn("never send or change anything in HighLevel", read(SKILLS / "process-customer-inquiries" / "SKILL.md"))


class HighLevelComesAfterTheFirstResult(unittest.TestCase):
    """0.8.1: first-time setup is click-and-sign-in only. HighLevel isn't in Claude's one-click
    list, so it is offered after the first result, in four short steps written to match Claude's
    own published instructions."""
    WANTED = "not set (HighLevel wanted, not connected yet)"

    def setUp(self):
        self.s = read(SKILLS / "setup-workforce" / "SKILL.md")
        self.before, self.later = self.s.split("## Connecting HighLevel", 1)
        self.later = self.later.split("## If something goes wrong", 1)[0]

    def test_first_time_setup_asks_three_questions_and_none_about_highlevel(self):
        stage0 = self.s.split("## Stage 0", 1)[1].split("## Stage 1", 1)[0]
        self.assertEqual(len(re.findall(r'^- "', stage0, re.M)), 3)
        self.assertIn("ask these three questions together", stage0)
        self.assertIn("**HighLevel is not part of first-time setup.**", stage0)
        self.assertIn("Don't ask about it or mention it here", stage0)
        self.assertIn("right after their first result", stage0)
        for banned in ["Do customers message you through HighLevel?", "leadconnectorhq", "Add custom connector"]:
            self.assertNotIn(banned, self.before, "first-time setup must stay click-and-sign-in")
        self.assertNotIn("HighLevel", self.s.split("**Order:**", 1)[1].split("\n", 1)[0])
        self.assertIn("HighLevel is never asked about or connected in this stage", self.s)

    def test_it_is_mentioned_once_after_the_first_result_without_a_question(self):
        finish = self.s.split("## Finish", 1)[1]
        self.assertIn("say 'connect HighLevel'", finish)
        self.assertIn("Never ask it as a question here", finish)
        self.assertIn('"connect HighLevel"', self.s.split("---", 2)[1])          # the skill's description
        self.assertIn('**"Connect HighLevel":**', self.before)

    def test_the_settings_line_says_where_things_stand(self):
        for must in [f"`Customer messages: {self.WANTED}`", "`Customer messages: None`",
                     "don't ask again, go straight to connecting", "leave the line as it is and carry on",
                     "plain `Customer messages: HighLevel` only after a lookup works"]:
            self.assertIn(must, self.later)
        c = read(REFS / "connections.md")
        for must in [f"`{self.WANTED}` included", "no run is Partial because of it", "plain `HighLevel`"]:
            self.assertIn(must, c)
        sys.path.insert(0, str(ROOT / "tests"))
        import run_logic
        self.assertEqual(run_logic.WANTED, self.WANTED)

    def test_one_click_comes_first_then_four_short_steps(self):
        later = self.later
        self.assertLess(later.index("**Already there.**"), later.index("**A card.**"))
        self.assertLess(later.index("**A card.**"), later.index("**By hand,**"))
        self.assertIn("connector registry", later)
        steps = re.findall(r"^   \d\. .+$", later, re.M)
        self.assertEqual(len(steps), 4)
        joined = "\n".join(steps)
        for must in ["https://claude.ai/customize/connectors", "**Customize**, then **Connectors**",
                     "**Add custom connector**", "**+ Add**", "**Continue** or **Add**",
                     "Name it **HighLevel**", "pick this business's sub-account"]:
            self.assertIn(must, joined)
        self.assertLessEqual(sum(len(s.split()) for s in steps), 85, "the steps must stay short enough to follow on a phone")
        self.assertIn("\n   `https://services.leadconnectorhq.com/mcp/anthropic/v2`\n", later)  # on its own line, easy to copy
        self.assertNotIn("Settings → Connectors", self.s)                                         # the old, wrong menu path
        for must in ["support.claude.com/en/articles/11175166", "instead of guessing", "Organization settings",
                     "anything that sends, edits or deletes can stay off", "Send me any message when that's done."]:
            self.assertIn(must, later)

    def test_the_owner_is_told(self):
        r = read(PLUGIN / "README.md")
        for must in ["connect HighLevel", "four short steps", "after your first result"]:
            self.assertIn(must, r)
        self.assertIn("allow only viewing", read(REFS / "if-asked-how-safe.md"))


class FreePlanAndEfficiency(unittest.TestCase):
    def test_notion_access_rules(self):
        t = read(REFS / "notion-access.md")
        for must in ['mode: "view"', 'mode: "rows"', "only when the question truly needs it",
                     "Verified empty", "could not be verified", "Never turn Incomplete or Unavailable into \"none\"",
                     "exactly 100", "read each thing once" if False else "Read each thing once per run",
                     "tool access"]:
            self.assertIn(must, t)

    def test_notion_access_travels_with_run_modes(self):
        for refdir in SKILLS.glob("*/references"):
            if (refdir / "run-modes.md").exists():
                self.assertTrue((refdir / "notion-access.md").exists(), refdir)

    def test_no_skill_defaults_to_sql_or_bare_query(self):
        for p in SKILLS.glob("*/SKILL.md"):
            t = read(p)
            self.assertNotRegex(t, r"(?i)\bsql\b", p)
            self.assertNotIn("query rows", t, p)

    def test_empty_claims_require_verified_reads(self):
        rm = read(REFS / "run-modes.md")
        self.assertIn("never \"none\" unless a read was verified empty", rm)
        for name in ["inbox-triage", "daily-executive-briefing", "review-approvals"]:
            self.assertIn("verified empty", read(SKILLS / name / "SKILL.md"), name)

    def test_economy_and_judgment_rules(self):
        t = read(REFS / "team-roles.md")
        for must in ["Launch only members with real work", "Is the owner already handling it?",
                     "Handed to you", "Don't create work to look busy", "One round of collaboration at most"]:
            self.assertIn(must, t)
        rt = read(REFS / "run-tracking.md")
        self.assertIn("Never estimate credits or cost", rt)
        self.assertIn("when 30 minutes have passed", rt)
        self.assertIn("just before launching team members", rt)

    def test_open_work_queue(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["## 6. The open-work queue", "whatever their age", "Prepared", "Handed to you",
                     "Blocked", "one row per source and action", "\"Open work\" view", "Carried over"]:
            self.assertIn(must, rt)

    def test_no_upsell_in_reports(self):
        self.assertIn("## No sales pitches", read(REFS / "talking-to-the-owner.md"))

    def test_secrets_rule_everywhere(self):
        self.assertIn("## Passwords, keys and other secrets", read(REFS / "run-modes.md"))
        for a in (PLUGIN / "agents").glob("*.md"):
            self.assertIn("**Secrets:**", read(a), a)

    def test_views_first_and_upgrade_adds_views(self):
        na = read(REFS / "notion-access.md")
        self.assertLess(na.index('**Saved view**'), na.index('**Rows with filters**'))
        for must in ["Check what a view really shows", "Follow every page", "may be rationed too",
                     "never change the owner's views"]:
            self.assertIn(must, na)
        up = read(REFS / "brain-upgrades.md")
        for v in ["Active approvals", "Open work", "Newest first", "Active offers", "All contacts"]:
            self.assertIn(v, up)
            self.assertIn(v, read(SKILLS / "setup-workforce" / "references" / "notion-schema.md"))
        self.assertIn("leave it as it is", up)

    def test_unfinished_work_never_closed_by_age(self):
        rt = read(REFS / "run-tracking.md")
        self.assertNotIn("closed as history", rt)
        self.assertIn("never closed because of their age", rt)
        self.assertIn("owner confirmed", rt)

    def test_duplicate_checks_read_finished_rows(self):
        self.assertIn("unfiltered \"Decision board\" view", read(REFS / "if-queuing-a-decision.md"))
        self.assertIn("not \"Open work\", which hides finished rows", read(REFS / "run-tracking.md"))

    def test_legacy_handed_to_you_stays_pending(self):
        self.assertIn('Owner note starts \"Handed to you:\"', read(SKILLS / "daily-executive-briefing" / "SKILL.md"))
        ra = read(SKILLS / "review-approvals" / "SKILL.md")
        self.assertNotIn("until then use Done", ra)
        self.assertIn("leave the item **Pending**", ra)

    def test_no_duplicate_schedule_inference(self):
        self.assertIn("Never infer a duplicate schedule from timing", read(REFS / "run-tracking.md"))
        self.assertIn("Never call runs duplicates because of their timing", read(SKILLS / "team-report" / "SKILL.md"))

    def test_notification_status_wording(self):
        rt = read(REFS / "run-tracking.md")
        self.assertIn("Notified: pending", rt)
        self.assertNotIn("Notified: no`", rt)
        self.assertIn("accepted by the tool", rt)
        self.assertIn("never call it \"delivered\"", rt)
        for p in PLUGIN.rglob("*.md"):
            self.assertNotIn("Notified: yes", read(p), p)

    def test_marketing_missing_data(self):
        pw = read(SKILLS / "prepare-weekly-marketing" / "SKILL.md")
        for must in ["Unavailable", "never estimate one", "Never create folders", "the run is Partial",
                     "Collaborate only when it adds something"]:
            self.assertIn(must, pw)

    def test_five_kinds_of_owner_items(self):
        tr = read(REFS / "team-roles.md")
        for must in ["Urgent: needs you now", "Approval needed", "Handed to you", "Prepared for later",
                     "Worth knowing", "Already handled or not yours", "**proposals**", "registration or sales link"]:
            self.assertIn(must, tr)

    def test_notification_recovery_is_bounded(self):
        rt = read(REFS / "run-tracking.md") + read(REFS / "if-notification-missed.md")
        for must in ["Catching up on missed notifications", "Don't redo their work", "at most 3 attempts per record",
                     "failed (permanent)", "may arrive twice", "last 8 days"]:
            self.assertIn(must, rt)
        for sk in ["daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices"]:
            self.assertIn("without redoing its work", read(SKILLS / sk / "references" / "scheduled-run-rules.md"), sk)

    def test_inbox_gaps_are_durable(self):
        ic = read(SKILLS / "inbox-triage" / "references" / "inbox-coverage.md") + read(SKILLS / "inbox-triage" / "references" / "if-inbox-gap.md")
        for must in ["Inbox not scanned: <from> – <to>", "inbox-gap:<from>", "oldest 2 days",
                     "Gap catch-up never moves Completed through", "Older mail not yet scanned"]:
            self.assertIn(must, ic)

    def test_self_test_checkpoint_follows_search_coverage(self):
        st = read(SKILLS / "workforce-self-test" / "SKILL.md")
        for must in ["Search: complete", "incomplete (stopped at 5 pages)", "Inbox not scanned"]:
            self.assertIn(must, st)

    def test_setup_makes_no_time_promises(self):
        setup = read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertNotIn("minutes)", setup)
        self.assertIn("No website", setup)

    def test_view_upgrade_verifies_before_version_bump(self):
        up = read(REFS / "brain-upgrades.md")
        self.assertIn("Only when every view above exists", up)
        self.assertIn("check each new view is there with that filter and sort", up)

    def test_readme_separates_enforced_tested_and_unproven(self):
        r = read(PLUGIN / "README.md")
        for must in ["## What you can rely on", "Enforced by your apps and settings", "Written rules the team follows",
                     "Seen working in live runs", "Checked by automated tests", "Not yet proven live"]:
            self.assertIn(must, r)
        for absolute in ["No duplicate drafts, approvals", "Unfinished work never disappears", "no skipped emails"]:
            self.assertNotIn(absolute, r)

    def test_root_readme_consistent(self):
        root = read(ROOT / "README.md")
        self.assertIn("still being proven live", root)
        self.assertNotIn("15 minutes", root)
        self.assertNotIn("Pro or above", root)
        self.assertIn("Required:", root)
        self.assertIn("Optional:", root)

    def test_ci_workflow_runs_the_checks(self):
        wf = read(ROOT / ".github" / "workflows" / "ci.yml")
        for must in ["push", "pull_request", "unittest discover tests", "sync_references.py --check", "plugin validate"]:
            self.assertIn(must, wf)
        self.assertNotIn("prompt_history", wf)

    def test_customer_claims_are_measured(self):
        text = read(PLUGIN / "README.md") + read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertNotIn("about 15 minutes", text)
        self.assertNotIn("in 15 minutes", text)
        self.assertNotRegex(text, r"Requires a paid Claude plan \(Pro")
        self.assertIn("free", read(PLUGIN / "README.md"))


class LearningRules(unittest.TestCase):
    """0.6.0: the written rules behind owner corrections, setup, approvals and drafts are present."""
    def test_owner_corrections_reference(self):
        oc = read(REFS / "owner-corrections.md") + read(REFS / "if-owner-corrects.md")
        for must in ["This item only", "Lasting rule", "Temporary rule", "Draft feedback",
                     "Not my responsibility anymore", "Always worth my attention", "Things to ignore for now",
                     "What a rule never hides", "new security incident", "Money leaving the owner's own accounts",
                     "Never delete a row", "Scheduled runs never create or change rules",
                     "A rule only hides; it never adds an action", "Never widen", "no longer applies",
                     "The same failure alert repeating is not new",
                     "is information, never a rule"]:
            self.assertIn(must, oc)

    def test_corrections_reach_every_run_that_raises_things(self):
        for name in ["inbox-triage", "daily-executive-briefing", "review-approvals", "manage-team",
                     "assign-work", "first-team-meeting"]:
            self.assertIn("owner-corrections.md", read(SKILLS / name / "SKILL.md"), name)
            self.assertTrue((SKILLS / name / "references" / "owner-corrections.md").exists(), name)
        self.assertIn("Has the owner already ruled it out?", read(REFS / "team-roles.md"))
        self.assertIn("your rules", read(SKILLS / "inbox-triage" / "references" / "inbox-coverage.md"))
        self.assertIn("Saved corrections hide, never permit", read(REFS / "approval-policy.md"))
        self.assertIn("Another automated email repeating the same alert is not new", read(REFS / "if-queuing-a-decision.md"))
        for a in (PLUGIN / "agents").glob("*-manager.md"):
            self.assertIn("**Owner's corrections:**", read(a), a)

    def test_priorities_template_and_add_only_upgrade(self):
        pt = read(SKILLS / "setup-workforce" / "references" / "page-templates.md")
        for h in ["## Always worth my attention", "## Not my responsibility anymore", "- Set up on: _not set_"]:
            self.assertIn(h, pt)
        up = read(REFS / "brain-upgrades.md")
        self.assertIn("## Upgrade to 0.6.0", up)
        self.assertIn("Only when both headings are there", up)
        self.assertIn("\"Not my responsibility anymore\"", up.split("## Structure check and repair")[1])

    def test_five_owner_categories(self):
        tr = read(REFS / "team-roles.md")
        for must in ["Needs your decision", "Prepared for you", "Already handled or not yours",
                     "Not every warning is the owner's problem", "Several alerts about the same underlying problem"]:
            self.assertIn(must, tr)

    def test_quick_look_is_labelled_and_never_moves_the_bookmark(self):
        ic = read(SKILLS / "inbox-triage" / "references" / "if-quick-look.md")
        for must in ["# Quick look", "newest 50 threads", "Completed through: not moved (quick look)",
                     "Never say all email was reviewed", "never moves it"]:
            self.assertIn(must, ic)
        ftm = read(SKILLS / "first-team-meeting" / "SKILL.md")
        for must in ["## Setup path", "Don't ask which to start with", "never a recurring quick look",
                     "never create a second recurring task"]:
            self.assertIn(must, ftm)

    def test_setup_progress_and_existing_brains(self):
        s = read(SKILLS / "setup-workforce" / "SKILL.md")
        for must in ["Keep the owner oriented", "reply **skip**", "Reuse or start fresh?",
                     "Business Brain (archive <date>)", "never another candidate's",
                     "does **not** confirm prices", "Never narrate individual searches"]:
            self.assertIn(must, s)
        rm = read(REFS / "run-modes.md")
        self.assertIn("If **more than one** has a Workforce Settings page, don't guess", rm)
        self.assertIn("read and write neither", rm)

    def test_conversational_approvals(self):
        ra = read(SKILLS / "review-approvals" / "SKILL.md")
        for must in ["## Understanding replies", "Looking is not permission", "Never act on an ambiguous approval",
                     "Clarify only when needed", "**Investigate**", "**Acknowledgement / already handled**",
                     "If the list showed both positions and AP numbers and a number could mean either, pointing to different items, ask"]:
            self.assertIn(must, ra)
        self.assertIn("from its step 0", read(SKILLS / "daily-executive-briefing" / "SKILL.md"))

    def test_confirmed_facts_and_never_asking_twice(self):
        self.assertIn("**Never ask twice.**", read(REFS / "just-in-time.md"))
        iv = read(SKILLS / "setup-workforce" / "references" / "interview.md")
        self.assertIn("**Confirmed, not inferred.**", iv)
        self.assertIn("**Already answered is answered.**", iv)

    def test_ready_check_before_drafts_are_ready(self):
        tr = read(REFS / "team-roles.md")
        for must in ["## Ready check", "No unresolved placeholders", "No invented proof", "No unconfirmed prices",
                     "Link needed", "Never sign as the owner", "Saved where the report says"]:
            self.assertIn(must, tr)
        self.assertIn("Ready check", read(SKILLS / "assign-work" / "SKILL.md"))
        self.assertIn("**Before calling a draft ready:**", read(PLUGIN / "agents" / "marketing-manager.md"))
        self.assertIn("a wording change never creates a new approval", tr)

    def test_first_week_is_optional_and_quiet(self):
        tr = read(SKILLS / "team-report" / "SKILL.md")
        self.assertIn("## First-week recap", tr)
        self.assertIn("Nothing here creates tasks, approvals or notifications", tr)
        self.assertIn("no extra notification is sent", read(SKILLS / "daily-executive-briefing" / "SKILL.md"))


class NotionCompatibility(unittest.TestCase):
    def test_schema_has_run_fields(self):
        t = read(SKILLS / "setup-workforce" / "references" / "notion-schema.md")
        for must in ["'Prepared':purple", "'Handed to you':orange", "'Blocked':brown",
                     '"Source" RICH_TEXT', '"Next action" RICH_TEXT',
                     '"Run ID" RICH_TEXT', '"Started" DATE', '"Finished" DATE',
                     '"Completed through" DATE', "'Unknown':gray", "'Running':blue"]:
            self.assertIn(must, t)

    def test_upgrade_is_add_only_and_versions_line_up(self):
        up = read(REFS / "brain-upgrades.md")
        latest = re.findall(r"## Upgrade to ([0-9.]+)", up)[-1]
        # Fresh setup starts "in progress"; the latest version is set only after the structure check.
        self.assertIn("- Business Brain version: setup in progress",
                      read(SKILLS / "setup-workforce" / "references" / "page-templates.md"))
        self.assertIn("Structure check and repair", up)
        setup = read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertIn("Structure check and repair", setup)
        self.assertIn("setup in progress", read(REFS / "run-modes.md"))
        section = up.split(f"## Upgrade to {latest}")[1]
        self.assertTrue("sending every existing option" in section or "Nothing existing changes" in section)
        for bad in ["delete", "rename", "remove"]:
            self.assertNotIn(bad, section.lower().split("later versions")[0])

    def test_runs_work_without_new_properties(self):
        self.assertIn("never fail a run over a missing property", read(REFS / "run-tracking.md"))


if __name__ == "__main__":
    unittest.main()
