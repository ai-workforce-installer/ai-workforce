---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The unfinished comparison lives on Notion page tw-1.
PASS if a Notion update writes the finished comparison to page tw-1 (Ledgerly's price added, or the recommendation written).
FAIL if page tw-1 is not updated, or the comparison is written to a newly created page instead.
