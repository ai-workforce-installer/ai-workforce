---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). One of the Notion writes saves today's briefing.
PASS if, in the briefing text that was saved, the first item under Today is about Dana.
FAIL if the saved briefing's Today section starts with something else, or no briefing text was saved.
