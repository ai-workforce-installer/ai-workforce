"""Checks on the mock-backed behaviour evals that tools/eval_scenarios.py writes.

These read the generated case files. They do not run Claude and they do not run the eval tool: they show the
cases are in step with their generator, are well formed for `claude plugin eval` as documented, and each
assert tool calls or saved state through the stand-ins. Whether Claude passes them is only known from a run.
"""
from __future__ import annotations

import re, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "ai-workforce"
EVALS = PLUGIN / "evals"
sys.path.insert(0, str(ROOT / "tools"))
sys.dont_write_bytecode = True
import eval_scenarios as gen  # noqa: E402

# What the eval tool accepts (code.claude.com/docs/en/plugin-evals, "Eval suite reference"): an unknown key is an error.
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model", "max_turns",
               "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
GRADER_KEYS = {"type", "weight", "arm", "pattern", "flags", "match", "target", "focus", "tool", "input_match", "min", "max"}
MOCK_KEYS = {"type", "expect", "error", "abort_when"}
WRITE_MARKERS = ["SENT-RECEIPT", "DRAFT-SAVED", "DRAFT-UPDATED", "DRAFT-DELETED", "LABEL-ADDED", "LABEL-REMOVED",
                 "SENSITIVE-LABEL-APPLIED", "NOTION-CREATED", "NOTION-UPDATED", "NOTION-SCHEMA-UPDATED", "TASK-CREATED",
                 "TASK-RUN-STARTED"]


def front(path):
    """(keys -> raw value, body) of a Markdown file with optional flat frontmatter."""
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text
    head, body = text[4:].split("\n---\n", 1)
    return dict(line.split(": ", 1) if ": " in line else (line.rstrip(":"), "") for line in head.splitlines()), body


def generated():
    return sorted(p.parent for p in EVALS.glob("*/prompt.md") if gen.MARK in p.read_text())


class GeneratedCasesAreInStep(unittest.TestCase):
    def test_the_files_match_the_generator(self):
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "eval_scenarios.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_every_scenario_is_on_disk_and_nothing_else_claims_to_be_generated(self):
        self.assertEqual([c.name for c in generated()], sorted(gen.CASES))
        self.assertGreaterEqual(len(gen.CASES), 20)

    def test_the_text_only_cases_are_untouched_by_stand_ins(self):
        """A suite-wide evals/mocks/ would give tools to the cases written for none, and change what they measure."""
        self.assertFalse((EVALS / "mocks").exists())
        for c in sorted(p.parent for p in EVALS.glob("*/prompt.md")):
            if c not in generated():
                self.assertFalse((c / "mocks").exists(), c.name)


class WellFormedForTheEvalTool(unittest.TestCase):
    def test_prompt_frontmatter_uses_only_documented_keys(self):
        for c in generated():
            keys, body = front(c / "prompt.md")
            self.assertLessEqual(set(keys), PROMPT_KEYS, c.name)
            self.assertTrue(body.strip(), c.name)
            self.assertTrue(keys["description"].startswith('"') and keys["description"].endswith('"'), c.name)   # colons inside
            self.assertEqual(keys["allowed_tools"], "[Skill, Read, Glob, Grep]", c.name)   # stand-in tools need no grant

    def test_graders_use_documented_keys_and_valid_patterns(self):
        for c in generated():
            for g in sorted((c / "graders").glob("*.md")):
                keys, body = front(g)
                self.assertLessEqual(set(keys), GRADER_KEYS, g)
                self.assertIn(keys["type"], ("regex", "llm", "tool_used"), g)
                if keys["type"] == "llm":
                    self.assertIn("PASS if", body, g)
                    self.assertIn("FAIL if", body, g)
                    self.assertIn(keys.get("focus", "last_message"), ("last_message", "mock_calls"), g)
                if keys["type"] == "regex":
                    self.assertFalse(body.strip(), g)
                    pattern = keys["pattern"]
                    self.assertTrue(pattern.startswith("'") and pattern.endswith("'") and "'" not in pattern[1:-1], g)
                    re.compile(pattern[1:-1])
                    self.assertNotIn("(?i)", pattern, g)                  # the tool takes flags: i, not inline flags
                    self.assertRegex(keys.get("match", "contains"), r'^(contains|not_contains|"count:\d+")$', g)
                    self.assertIn(keys.get("target", "last_message"), ("last_message", "mock_calls"), g)

    def test_mock_files_use_documented_keys_and_have_an_answer(self):
        for c in generated():
            for m in sorted((c / "mocks").glob("*/*.md")):
                keys, body = front(m)
                self.assertLessEqual(set(keys), MOCK_KEYS, m)
                self.assertTrue(body.strip(), m)
                self.assertFalse(m.name.startswith("_"), m)      # no _tools.json or _server.md: their formats are unverified here

    def test_one_property_per_grader(self):
        """A grader that checks two things can't say which one failed. Judged graders state one PASS and one FAIL."""
        for c in generated():
            for g in sorted((c / "graders").glob("*.md")):
                keys, body = front(g)
                if keys["type"] == "llm":
                    self.assertEqual(body.count("PASS if"), 1, g)
                    self.assertEqual(body.count("FAIL if"), 1, g)
                    self.assertNotRegex(g.stem, r"-and-(?!no-)", g)


class TheyAssertCallsAndSavedState(unittest.TestCase):
    def test_every_case_has_the_owners_apps_standing_in(self):
        for c in generated():
            for tool in ["Notion/notion-fetch", "Notion/notion-create-pages", "Notion/notion-update-page",
                         "Gmail/search_threads", "Gmail/get_draft", "Gmail/create_draft", "Gmail/reply", "Gmail/delete_draft",
                         "Gmail/label_thread", "Gmail/unlabel_thread"]:
                self.assertTrue((c / "mocks" / (tool + ".md")).exists(), f"{c.name}: {tool}")

    def test_every_case_grades_what_was_called_or_saved(self):
        for c in generated():
            on_calls = [g for g in (c / "graders").glob("*.md") if "mock_calls" in g.read_text()]
            self.assertTrue(on_calls, f"{c.name}: no grader looks at the calls made to the stand-ins")

    def test_a_counted_marker_is_one_the_cases_stand_ins_can_give(self):
        for c in generated():
            answers = "\n".join(m.read_text() for m in (c / "mocks").glob("*/*.md"))
            for g in (c / "graders").glob("*.md"):
                keys, _ = front(g)
                if keys["type"] == "regex" and keys.get("target") == "mock_calls":
                    for marker in WRITE_MARKERS:
                        if marker in keys["pattern"]:
                            self.assertIn(marker, answers, f"{g}: no stand-in in this case answers {marker}")

    def test_every_write_answers_with_a_marker_and_every_read_with_the_state(self):
        for c in generated():
            self.assertIn("# Business Brain", (c / "mocks" / "Notion" / "notion-fetch.md").read_text(), c.name)
            for tool, marker in [("Gmail/reply", "SENT-RECEIPT"), ("Gmail/create_draft", "DRAFT-SAVED"),
                                 ("Gmail/delete_draft", "DRAFT-DELETED"), ("Notion/notion-update-page", "NOTION-")]:
                self.assertIn(marker, (c / "mocks" / (tool + ".md")).read_text(), f"{c.name}: {tool}")

    def test_a_failing_stand_in_is_a_tool_error(self):
        failing = [m for c in generated() for m in (c / "mocks").glob("*/*.md") if "-FAILED" in m.read_text()]
        self.assertTrue(failing)
        for m in failing:
            self.assertEqual(front(m)[0].get("error"), "true", m)


class TheClock(unittest.TestCase):
    CLOCK = re.compile(r"Evaluation clock: it is now (\w+day) (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) \(([\w/]+)\)\.")

    def test_every_case_states_the_time_and_whether_anyone_is_there(self):
        import datetime
        for c in generated():
            system = front(c / "prompt.md")[0]["append_system_prompt"]
            m = self.CLOCK.search(system)
            self.assertIsNotNone(m, c.name)
            self.assertEqual(datetime.date.fromisoformat(m.group(2)).strftime("%A"), m.group(1), c.name)   # the weekday is right
            self.assertEqual(m.group(4), gen.TZ, c.name)
            self.assertEqual(("No one is watching this run." in system), ("scheduled" in front(c / "prompt.md")[0]["tags"]), c.name)

    def test_a_scenario_over_several_runs_moves_only_the_clock(self):
        """Run 2 has to see the state run 1 left: the same stand-ins and the same request, at a later time."""
        self.assertTrue(gen.RUNS)
        for scenario, names in gen.RUNS.items():
            self.assertGreaterEqual(len(names), 2, scenario)
            cases = [EVALS / n for n in names]
            states, clocks, prompts = set(), [], set()
            for c in cases:
                states.add(tuple((str(m.relative_to(c)), m.read_text()) for m in sorted((c / "mocks").glob("*/*.md"))))
                keys, body = front(c / "prompt.md")
                m = self.CLOCK.search(keys["append_system_prompt"])
                clocks.append(m.group(2) + " " + m.group(3))
                prompts.add(body)
            self.assertEqual(len(states), 1, scenario)
            self.assertEqual(len(prompts), 1, scenario)
            self.assertEqual(clocks, sorted(set(clocks)), scenario)          # strictly later each run


class UnattendedCasesUseWhatATaskReallyStores(unittest.TestCase):
    def setUp(self):
        self.stored = (PLUGIN / "skills" / "schedule-workforce" / "references" / "scheduled-prompts.md").read_text()

    def test_unattended_prompts_are_the_stored_blocks(self):
        seen = 0
        for c in generated():
            keys, body = front(c / "prompt.md")
            first = body.strip().splitlines()[0]
            if "scheduled" in keys["tags"]:
                seen += 1
                self.assertTrue(first.startswith("[AI Workforce task: "), c.name)
                self.assertIn(first, self.stored, c.name)                        # the tag line, version and all
                safety = "Never send messages, spend money, change budgets or financial records, publish, delete anything"
                self.assertIn(safety, body, c.name)
                self.assertIn("If that skill is not available: do not do this job from memory", body, c.name)
            else:
                self.assertNotIn("[AI Workforce task:", body, c.name)            # the desk refuses a task's conversation
        self.assertGreaterEqual(seen, 6)

    def test_extra_instructions_go_under_owners_additions_only(self):
        for c in generated():
            body = front(c / "prompt.md")[1]
            if "Lock test" in body or "send any replies that are ready" in body:
                self.assertLess(body.index("Owner's additions:"), body.index("Lock test" if "Lock test" in body else "send any replies"), c.name)


class NothingFromARealBusiness(unittest.TestCase):
    def test_stand_in_people_use_reserved_example_addresses(self):
        for c in generated():
            for f in c.rglob("*.md"):
                for address in re.findall(r"[\w.+-]+@([\w.-]+)", f.read_text()):
                    self.assertTrue(address.rstrip(".").endswith(".example"), f"{f}: {address}")
                for host in re.findall(r"https?://([\w.-]+)", f.read_text()):
                    self.assertTrue(host.endswith(".example"), f"{f}: {host}")

    def test_no_owner_details_in_tests_or_tools(self):
        banned = ["reedfloren", "Floren", "Lawrence", "Loik", "businesssuccesssystems", "completemarketingsystems", "Mankato",
                  "GoHighLevel", "Larry", "ffiliate"]
        for p in list((ROOT / "tests").glob("*.py")) + list((ROOT / "tools").glob("*.py")):
            text = p.read_text()
            if p.name in ("test_plugin.py", "test_eval_scenarios.py"):          # these two hold the lists themselves
                text = re.sub(r"banned = \[[^\]]*\]", "", text)
            for b in banned:
                self.assertNotIn(b, text, f"{p}: contains '{b}'")


if __name__ == "__main__":
    unittest.main()
