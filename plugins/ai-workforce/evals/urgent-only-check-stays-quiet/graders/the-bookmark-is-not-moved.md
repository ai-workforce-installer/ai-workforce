---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The morning's inbox check left the bookmark (Completed through) at 2026-03-05 07:31. This run is an urgent-only check, which never moves it.
PASS if no call sets Completed through to a later time (the new record says not moved, or leaves it out).
FAIL if a call sets Completed through to around 15:00 or any time after 07:31.
