---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). Row as-401 already tracks the failing lead-sync automation.
PASS if no call creates a new Assignments row about the lead-sync automation failing. An update to as-401 (count, latest date, newest link) is expected, and creating a Briefings record is fine.
FAIL if a call creates a new Assignments row for the lead-sync failure.
