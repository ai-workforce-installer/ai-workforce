---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The owner asked to track two separate promises from one email thread: sending a proposal, and making an introduction.
PASS if two separate Assignments rows are created (in one call or two), one for the proposal and one for the introduction, with different work keys.
FAIL if only one row is created, or both promises are merged into one row.
