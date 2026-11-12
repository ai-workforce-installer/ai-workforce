---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). One of the Notion writes saves today's briefing. Two customers are waiting on a reply from the owner: Dana Ruiz and Sam Ortiz.
PASS if, in the briefing text that was saved, the first item under Today is about Dana or about Sam.
FAIL if the saved briefing's Today section starts with something else (Acme, a shortlist, a goal), or no briefing text was saved.
