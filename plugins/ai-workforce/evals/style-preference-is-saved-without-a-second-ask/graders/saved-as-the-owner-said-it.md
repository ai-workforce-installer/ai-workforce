---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The owner's preference: replies of three sentences at most, and no exclamation marks.
PASS if a Notion write saves that preference with both parts (three sentences at most; no exclamation marks).
FAIL if nothing is written, or the saved text drops or changes either part.
