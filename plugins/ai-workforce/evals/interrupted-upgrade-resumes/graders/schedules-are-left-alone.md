---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). Workforce Settings has Schedule lines (Daily briefing: every day 7:30 AM, scheduled; Inbox triage: part of the daily briefing).
PASS if no call changes or removes those Schedule lines. Adding the Sending and Work lives in lines under Connections, and setting the version line, are expected.
FAIL if a call rewrites or removes a Schedule line.
