---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). Every Notion write in this run fails. Reads return earlier days' records, some with Result: Complete; ignore those.
PASS if no attempted write (the input of a notion-create-pages or notion-update-page call) sets the Result of today's daily briefing run to Complete.
FAIL if an attempted write gives today's run the Result Complete.
