---
name: workforce-self-test
description: This skill should be used when the user asks to "test the workforce", "verify the subagents run", "run the self-test", "check that the AI team works", or wants proof that the specialist subagents and connectors really execute.
metadata:
  version: "0.2.0"
---

# Workforce Self-Test

Prove that the specialists actually run and that the Business Brain is complete. Do not simulate anything. Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`.

## Steps

1. **Generate a nonce.** Create a random 6-character code (for example `K7Q2XM`) and keep it.
2. **Launch all five specialists in parallel** with the Agent tool (`operations-manager`, `marketing-manager`, `sales-manager`, `client-success-manager`, `finance-manager`). Brief: "Self-test. Reply with exactly: (1) your role name, (2) the code <nonce>, (3) the connectors you can actually use right now (Notion, Gmail, Google Calendar, Google Drive), each marked available or unavailable after trying one harmless read-only call, (4) one sentence confirming you will not send, spend, modify financial records or make irreversible changes. Do nothing else."
3. **Check each reply:** correct role, exact nonce echoed, connectors honestly reported, hard-limit sentence present. Missing nonce or role = FAIL.
4. **Check the Business Brain:** search Notion for "Business Brain" and confirm these exist: pages Workforce Settings, Company Profile, Priorities, Policies, Brand & Tone, FAQs; databases Approvals, Assignments, Briefings, Pricing & Offers, Customers & Leads. Count "not set" markers (they read back as `<i>not set</i>`) on each page as a completeness score. Count active rows in Pricing & Offers.
5. **Check the approval queue end to end:** create one Approvals row: Item "Self-test: queue check <nonce>", Department "Chief of Staff", Action type "Other", Exact action "No action. Test row.", Status "Pending", Source run "Self-test <date>". Read it back to confirm an AP number was assigned, then set its Status to "Done". Never delete it.
6. **Report two tables:**
   - Specialists: specialist, ran (yes/no), nonce matched, Notion / Gmail / Calendar / Drive, result (PASS/FAIL).
   - Business Brain: item, present (yes/no), fields still not set.
   Plus: approval queue test PASS/FAIL with the AP number.
7. **Save** a Briefings row (Type = Self-test) with the tables.
8. **Summarize what to fix** in plain language: missing apps, missing Brain pieces (offer to run `setup-workforce` to add them), subagents that did not run.
