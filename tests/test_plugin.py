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
        repo_files = {str(p.relative_to(PLUGIN)) for p in PLUGIN.rglob("*") if p.is_file()}
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
        for must in ["Run ID", "45 minutes", "Unknown", "source key", "Notified: no",
                     "Never merge a run", "Never guess from the clock"]:
            self.assertIn(must, t)

    def test_inbox_checkpoint_rules(self):
        t = read(SKILLS / "inbox-triage" / "references" / "inbox-coverage.md")
        for must in ["Completed through", "stays where it was", "15-minute overlap",
                     "Carried over", "Never hide a gap", "Discovered", "Processed",
                     "Never add `in:inbox`", "Fetch every page", "comprehensive"]:
            self.assertIn(must, t)

    def test_customer_skill_cannot_stand_in_for_inbox_triage(self):
        t = read(SKILLS / "process-customer-inquiries" / "SKILL.md")
        self.assertIn("0. **Check this is the right job.**", t)
        self.assertIn("load the `inbox-triage` skill", t)
        self.assertNotIn('"triage my inbox", "handle customer emails"', t)


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

    def test_every_prompt_and_fallback_keeps_safeguards(self):
        for b in self.blocks:
            for must in ["never as instructions or approval",
                         "Never send messages, spend money, change budgets or financial records, publish, delete anything",
                         "carry out approval items",
                         "Not run: still in progress",
                         "one notification per run",
                         "If that skill is not available"]:
                self.assertIn(must, b, f"missing '{must}' in {b[:60]}")


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
                  "completemarketingsystems", "Mankato", "GoHighLevel", "GHL"]
        for p in PLUGIN.rglob("*"):
            if p.is_file() and p.suffix in {".md", ".json"}:
                # The author credit and the repository address are allowed.
                text = read(p).replace("reedfloren/ai-workforce", "")
                if p.name == "plugin.json":
                    text = re.sub(r'"author": \{[^}]*\}', "", text)
                for b in banned:
                    self.assertNotIn(b, text, f"{p}: contains '{b}'")


class NotionCompatibility(unittest.TestCase):
    def test_schema_has_run_fields(self):
        t = read(SKILLS / "setup-workforce" / "references" / "notion-schema.md")
        for must in ['"Run ID" RICH_TEXT', '"Started" DATE', '"Finished" DATE',
                     '"Completed through" DATE', "'Unknown':gray", "'Running':blue"]:
            self.assertIn(must, t)

    def test_upgrade_is_add_only_and_versions_line_up(self):
        up = read(REFS / "brain-upgrades.md")
        latest = re.findall(r"## Upgrade to ([0-9.]+)", up)[-1]
        self.assertIn(f"- Business Brain version: {latest}",
                      read(SKILLS / "setup-workforce" / "references" / "page-templates.md"))
        section = up.split(f"## Upgrade to {latest}")[1]
        self.assertIn("sending every existing option", section)
        for bad in ["delete", "rename", "remove"]:
            self.assertNotIn(bad, section.lower().split("later versions")[0])

    def test_runs_work_without_new_properties(self):
        self.assertIn("never fail a run over a missing property", read(REFS / "run-tracking.md"))


if __name__ == "__main__":
    unittest.main()
