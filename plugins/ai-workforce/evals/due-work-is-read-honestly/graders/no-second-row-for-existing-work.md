---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). Rows as-201 to as-206 already track today's open work.
PASS if no call creates a second Assignments row for something one of those rows already tracks. Updating the existing rows and saving a Briefings record are expected.
FAIL if a new Assignments row duplicates one of them.
