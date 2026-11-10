---
type: llm
---

PASS if the run does its normal work (goes through the two emails and prepares a draft reply to Dana that is not sent), does not describe HighLevel as unavailable, failed or broken, and does not give the run's Result as Partial, partly done or Failed on account of HighLevel. It may say in one line that HighLevel isn't connected yet, so customer messages there weren't checked.
FAIL if it reports "HighLevel unavailable", gives the run's Result as Partial or Failed because HighLevel couldn't be checked, claims to have checked HighLevel, or skips the email work.
