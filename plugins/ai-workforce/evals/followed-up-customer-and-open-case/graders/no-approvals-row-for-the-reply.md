---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). PASS if no call creates an Approvals row (an approval item, AP number) for the reply to Dana about the workbook. Creating a Briefings record, updating a draft, and updating Assignments rows are all fine.
FAIL if a call creates an Approvals row for the reply to Dana.
