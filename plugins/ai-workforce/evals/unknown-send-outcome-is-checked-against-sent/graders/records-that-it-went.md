---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). Row as-521 tracks a reply to Dana whose send timed out; the reply is in Sent as message m-sent-77.
PASS if a Notion update records on as-521 that the reply was sent (the sent message or its id as evidence, or the row closed as Sent).
FAIL if no Notion update touches as-521.
