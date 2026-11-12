---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The last full inbox check left the bookmark (Completed through) at 2026-03-05 07:05. This run is a quick look at the newest emails.
PASS if no call sets Completed through to a new time: the new record says it was not moved (or leaves it out), and the earlier record is not changed.
FAIL if a call sets Completed through to around 12:40 or to any time after 07:05.
