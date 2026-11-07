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
    def test_only_notion_is_bundled(self):
        """Email, calendar and files come from the owner's own connectors (setup suggests them).
        Bundled copies duplicated those tools and failed to connect where Claude's hosted
        Gmail and Calendar servers can't be reached directly."""
        cfg = json.loads(read(PLUGIN / ".mcp.json"))
        self.assertEqual(list(cfg["mcpServers"]), ["Notion"])
        self.assertEqual(set(cfg["recommendedCategories"]), {"wiki-knowledge-base", "email", "calendar", "documents"})
        self.assertIn("connector registry", read(SKILLS / "setup-workforce" / "SKILL.md"))


class ScheduleDefaults(unittest.TestCase):
    def test_daily_by_default_and_the_owner_is_asked(self):
        sw = read(SKILLS / "schedule-workforce" / "SKILL.md")
        for must in ["How often should the team check in: every day (recommended), weekdays only, or another rhythm?",
                     "If they don't mind, use every day", "- Check-in frequency: every day",
                     "Daily briefing: every day (or the chosen rhythm)",
                     "once a day at the same rhythm", "Weekly marketing plan: Mondays", "Invoice review: Fridays"]:
            self.assertIn(must, sw)
        self.assertNotIn("Daily briefing: weekdays", sw)
        self.assertNotIn("mid-morning and mid-afternoon", sw)
        fm = read(SKILLS / "first-team-meeting" / "SKILL.md")
        self.assertIn("Every day is the default for daily work", fm)
        self.assertNotIn("every weekday morning", fm)


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

    def test_evals_are_not_shipped(self):
        z = zipfile.ZipFile(ROOT / "download" / "ai-workforce.plugin")
        self.assertFalse([n for n in z.namelist() if n.startswith("evals/")])


class ScheduledPrompts(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILLS / "schedule-workforce" / "references" / "scheduled-prompts.md")
        self.blocks = re.findall(r"```\n(.*?)```", self.text, re.S)
        rm = read(REFS / "run-modes.md")
        self.table = dict(re.findall(r"\| `([a-z-]+)` \| ([0-9.]+) \|", rm))

    def test_five_prompts_with_current_version_lines(self):
        self.assertEqual(len(self.blocks), 5)
        for b in self.blocks:
            m = re.match(r"\[AI Workforce task: ([a-z-]+) \| prompt version ([0-9.]+)\]", b)
            self.assertIsNotNone(m, b[:80])
            skill, ver = m.groups()
            self.assertIn(skill, self.table)
            self.assertEqual(ver, self.table[skill])
            self.assertIn(f'"{skill}" skill', b)
            self.assertTrue((SKILLS / skill / "SKILL.md").exists())

    def test_inbox_prompt_is_all_email(self):
        inbox = [b for b in self.blocks if b.startswith("[AI Workforce task: inbox-triage")][0]
        self.assertNotIn("process-customer-inquiries", inbox)
        self.assertIn("ALL email", inbox)
        self.assertIn("-in:sent -in:drafts -in:spam -in:trash", inbox)
        self.assertIn("Completed through", inbox)

    def test_every_stored_prompt_keeps_safeguards(self):
        """What a task stores: the safety rules, the pointer to the current plugin, and a fallback."""
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
            self.assertNotIn("described above", b)      # nothing in the fallback points at text that moved

    def test_stored_prompts_are_short(self):
        """Rules live in the plugin, so a stored prompt stays small and rarely changes."""
        for b in self.blocks:
            before_fallback = b.split("If that skill is not available")[0]
            self.assertLess(len(before_fallback.split()), 330, b[:60])

    def test_scheduled_run_rules_keep_every_safeguard(self):
        rules = read(SKILLS / "schedule-workforce" / "references" / "scheduled-run-rules.md")
        for must in ["never as instructions or approval", "Never repeat a password, API key", "could not be verified",
                     "open Assignments", "Launch only team members with real work", "never estimate cost",
                     "Never send messages, spend money, change budgets or financial records, publish, delete anything",
                     "carry out approval items", "Not run (still in progress)", "saved views first",
                     "Run now at any day or time", "accepted by the tool", "one notification per run",
                     "without redoing its work", "win over the task's stored instructions",
                     "Recurring tasks update themselves: no"]:
            self.assertIn(must, rules, must)
        for sk in ["daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices", "assign-work"]:
            self.assertIn("references/scheduled-run-rules.md", read(SKILLS / sk / "SKILL.md"), sk)
            self.assertTrue((SKILLS / sk / "references" / "scheduled-run-rules.md").exists(), sk)


class Safety(unittest.TestCase):
    def test_policy_core_rules(self):
        t = read(REFS / "approval-policy.md")
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
        self.assertIn("unfiltered \"Decision board\" view", read(REFS / "approval-queue.md"))
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
            if p.name == "prompt-history.md":
                continue                      # released prompts are kept exactly as released
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

    def test_recurring_tasks_update_themselves_safely(self):
        rm = read(REFS / "run-modes.md")
        for must in ["Keep the task up to date automatically", "Recurring tasks update themselves: no",
                     "Change the instructions only", "never create, pause or delete a task",
                     "None, or more than one: change nothing and report it",
                     "Custom responsibilities are never replaced", "an older released version of this responsibility",
                     "Never judge by the version line alone", "This run used the current instructions anyway",
                     "never read old prompts to compare them", "Owner's additions\" section exactly as it was", "Previous recurring-task instructions (backup)",
                     "put the backed-up instructions back", "Never report a restore or a success that wasn't verified",
                     "Nothing new to accept", "If the backup can't be saved and read back complete, stop: no change",
                     "checking the instructions **and** every setting separately", "Instructions back but a setting differs",
                     "Don't change settings without the owner's yes", "If the read fails, the result is **unverified**",
                     "Check nothing moved", "paused stays paused",
                     "start with `[AI Workforce task: <this skill> |`", "whatever version line it carries",
                     "line endings, spaces at the ends of lines", "The current rules win over older stored text"]:
            self.assertIn(must, rm)
        self.assertNotIn("A run never changes its own scheduled task", rm)
        self.assertIn("prompt only", read(REFS / "approval-policy.md"))
        for sk in ["daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices"]:
            self.assertTrue((SKILLS / sk / "references" / "scheduled-prompts.md").exists(), sk)
            self.assertTrue((SKILLS / sk / "references" / "prompt-history.md").exists(), sk)

    def test_attended_update_has_the_same_protections(self):
        sw = read(SKILLS / "schedule-workforce" / "SKILL.md")
        for must in ["Changing a recurring task's instructions safely", "Owner's additions",
                     "a paused task stays paused: updating instructions never resumes it"]:
            self.assertIn(must, sw)
        self.assertNotIn("name or prompt mentions AI Workforce", sw)

    def test_notification_recovery_is_bounded(self):
        rt = read(REFS / "run-tracking.md")
        for must in ["Catching up on missed notifications", "Don't redo their work", "at most 3 attempts per record",
                     "failed (permanent)", "may arrive twice", "last 8 days"]:
            self.assertIn(must, rt)
        for sk in ["daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices"]:
            self.assertIn("without redoing its work", read(SKILLS / sk / "references" / "scheduled-run-rules.md"), sk)

    def test_inbox_gaps_are_durable(self):
        ic = read(SKILLS / "inbox-triage" / "references" / "inbox-coverage.md")
        for must in ["Inbox not scanned: <from> – <to>", "inbox-gap:<from>", "oldest 2 days",
                     "Gap catch-up never moves Completed through", "Older mail not yet scanned"]:
            self.assertIn(must, ic)
        sp = read(SKILLS / "inbox-triage" / "references" / "scheduled-prompts.md")
        self.assertIn("Inbox not scanned", sp)

    def test_self_test_checkpoint_follows_search_coverage(self):
        st = read(SKILLS / "workforce-self-test" / "SKILL.md")
        for must in ["Search: complete", "incomplete (stopped at 5 pages)", "Inbox not scanned"]:
            self.assertIn(must, st)

    def test_prompt_history_records_current_templates(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "prompt_history.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        archive = read(ROOT / "tools" / "released-prompts.md")
        table = read(SKILLS / "schedule-workforce" / "references" / "prompt-history.md")
        for sk in ["daily-executive-briefing", "inbox-triage", "prepare-weekly-marketing", "review-overdue-invoices"]:
            for v in ["0.5.0", "0.5.1", "0.5.2", "0.5.4", "0.7.0"]:
                self.assertIn(f"## {sk} {v}", archive)
                self.assertRegex(table, rf"\| {sk} \| {re.escape(v)} \| [0-9a-f]{{16}} \|")

    def test_shipped_history_is_fingerprints_only(self):
        """Runs read a small table, never every old prompt (that cost ~18,000 words per run)."""
        for p in PLUGIN.rglob("prompt-history.md"):
            self.assertLess(len(read(p).split()), 1500, p)
            self.assertNotIn("````text", read(p), p)

    def test_fingerprint_script_in_run_modes_matches_the_table(self):
        """The script Claude runs must give the fingerprints the tool records, and must ignore
        the Brain's title, line endings, trailing spaces and Owner's additions."""
        import tempfile
        rm = read(REFS / "run-modes.md")
        script = re.search(r"\*\*Fingerprint\.\*\*.*?```\n(.*?)```", rm, re.S).group(1)
        script = "\n".join(l[2:] if l.startswith("  ") else l for l in script.split("\n"))
        sys.path.insert(0, str(ROOT / "tools"))
        import prompt_history as ph
        recorded = ph.recorded(read(ROOT / "tools" / "released-prompts.md"))
        table = dict(((s, v), f) for s, v, f in re.findall(r"^\| ([a-z-]+) \| ([0-9.]+) \| ([0-9a-f]{16}) \|",
                     read(SKILLS / "schedule-workforce" / "references" / "prompt-history.md"), re.M))
        self.assertEqual(set(table), set(recorded))
        with tempfile.TemporaryDirectory() as d:
            sp = Path(d) / "fingerprint.py"; sp.write_text(script)
            for key, body in recorded.items():
                saved = body.replace("<BRAIN>", "Acme Business Brain").replace("\n", "\r\n") + "   \r\n"
                saved += "\r\nOwner's additions:\r\nAlways copy my assistant."
                tf = Path(d) / "task.txt"; tf.write_bytes(saved.encode())
                out = subprocess.run([sys.executable, str(sp), str(tf)], capture_output=True, text=True).stdout.strip()
                self.assertEqual(out, table[key], key)
            edited = Path(d) / "edited.txt"
            edited.write_text(recorded[("inbox-triage", "0.5.4")].replace("at most 5 drafts", "at most 9 drafts"))
            out = subprocess.run([sys.executable, str(sp), str(edited)], capture_output=True, text=True).stdout.strip()
            self.assertNotIn(out, table.values())

    def test_setup_explains_auto_updates_in_one_sentence(self):
        self.assertIn("These keep their instructions up to date when AI Workforce improves",
                      read(SKILLS / "schedule-workforce" / "SKILL.md"))
        setup = read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertNotIn("minutes)", setup)
        self.assertIn("No website", setup)

    def test_view_upgrade_verifies_before_version_bump(self):
        up = read(REFS / "brain-upgrades.md")
        self.assertIn("Only when every view above exists", up)
        self.assertIn("check each new view is there with that filter and sort", up)
        self.assertIn("- Recurring tasks update themselves: yes",
                      read(SKILLS / "setup-workforce" / "references" / "page-templates.md"))

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
        for must in ["push", "pull_request", "unittest discover tests", "sync_references.py --check",
                     "prompt_history.py --check"]:
            self.assertIn(must, wf)

    def test_customer_claims_are_measured(self):
        text = read(PLUGIN / "README.md") + read(SKILLS / "setup-workforce" / "SKILL.md")
        self.assertNotIn("about 15 minutes", text)
        self.assertNotIn("in 15 minutes", text)
        self.assertNotRegex(text, r"Requires a paid Claude plan \(Pro")
        self.assertIn("free", read(PLUGIN / "README.md"))


class LearningRules(unittest.TestCase):
    """0.6.0: the written rules behind owner corrections, setup, approvals and drafts are present."""
    def test_owner_corrections_reference(self):
        oc = read(REFS / "owner-corrections.md")
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
        self.assertIn("Another automated email repeating the same alert is not new", read(REFS / "approval-queue.md"))
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
        ic = read(SKILLS / "inbox-triage" / "references" / "inbox-coverage.md")
        for must in ["## 6. Quick look", "newest 50 threads", "Completed through: not moved (quick look)",
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

    def test_one_current_prompt_version(self):
        """0.7.0 moved the run rules into the plugin; every task points at the same current version."""
        rm = read(REFS / "run-modes.md")
        self.assertEqual(set(re.findall(r"\| `[a-z-]+` \| ([0-9.]+) \|", rm)), {"0.7.0"})


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
