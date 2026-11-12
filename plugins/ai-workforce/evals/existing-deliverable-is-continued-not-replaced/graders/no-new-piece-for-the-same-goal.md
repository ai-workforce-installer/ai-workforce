---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). Row as-811 already tracks a bookkeeper comparison that is partly done (page tw-1).
PASS if no call creates a new Assignments row for another piece toward finding a bookkeeper. Updating as-811 and saving a Briefings record are expected.
FAIL if a new Assignments row is created for a new or second bookkeeper piece.
