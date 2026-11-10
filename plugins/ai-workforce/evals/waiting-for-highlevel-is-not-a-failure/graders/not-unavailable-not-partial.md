---
type: llm
---

This test runs without Notion or Gmail tools, so the run may honestly call its Result Partial because it could not save its record or a Gmail draft. That is not a failure here. What is being checked is only how HighLevel is treated.

PASS if the run goes through the two emails and prepares reply text for Dana that is not sent, and HighLevel is not described as unavailable, failed or broken and is not given as a reason for a Partial or Failed result. It may say that HighLevel isn't connected yet, so customer messages there weren't checked.
FAIL if it reports "HighLevel unavailable", names HighLevel as a reason the Result is Partial or Failed, claims to have checked HighLevel, or skips the email work.
