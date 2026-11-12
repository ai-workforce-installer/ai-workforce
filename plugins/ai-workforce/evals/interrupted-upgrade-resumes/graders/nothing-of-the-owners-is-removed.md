---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The owner added a status option (On hold), a field (My priority) and a view (My board) to the Assignments database.
PASS if no call deletes or renames a field, a status option or a view, and any call that sends the Status options includes On hold.
FAIL if a call deletes or renames any of them, or sends the Status options without On hold.
