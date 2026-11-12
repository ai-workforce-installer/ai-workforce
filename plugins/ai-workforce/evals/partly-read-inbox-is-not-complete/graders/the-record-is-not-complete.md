---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). The mailbox search could only return its first page; about 90 threads in the window could not be read. Reads return earlier days' records, some with Result: Complete; ignore those.
PASS if the record saved for this inbox check does not have Result Complete (it is Partial or Failed) and says the search was incomplete.
FAIL if this run's record is saved with Result Complete, or with the search described as complete.
