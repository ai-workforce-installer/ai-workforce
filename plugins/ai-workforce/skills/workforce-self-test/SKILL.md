---
name: workforce-self-test
description: This skill should be used when the user asks to "test the workforce", "verify the subagents run", "run the self-test", "check that the AI team works", or wants proof that the specialist subagents and connectors really execute.
metadata:
  version: "0.3.0"
---

# Workforce Self-Test

Prove that the specialists actually run and that the Business Brain is complete. Do not simulate anything. Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md` and `connections.md` (same folder).

## Steps

1. **Read Connections** in Workforce Settings so you know which apps this owner chose (Gmail / Outlook / Paste mode, and so on). The test checks those apps, not apps the owner never chose.
2. **Generate a nonce.** Create a random 6-character code (for example `K7Q2XM`) and keep it.
3. **Launch all five specialists in parallel** with the Agent tool (`operations-manager`, `marketing-manager`, `sales-manager`, `client-success-manager`, `finance-manager`). Brief: "Self-test. Reply with exactly: (1) your role name, (2) the code <nonce>, (3) for Notion and for each app the owner chose (<list from Connections, e.g. Gmail, Google Calendar, Google Drive, or Microsoft 365>), whether you can actually use it right now, marked available or unavailable after trying one harmless read-only call (skip anything on paste mode or None), (4) one sentence confirming you will not send, spend, modify financial records or make irreversible changes. Do nothing else."
4. **Check each reply:** correct role, exact nonce echoed, connectors honestly reported, hard-limit sentence present. Missing nonce or role = FAIL.
5. **Check the Business Brain:** search Notion for "Business Brain" and confirm these exist: pages Workforce Settings (with a Connections section), Company Profile, Priorities, Policies, Brand & Tone, FAQs, Paste Box; databases Approvals, Assignments, Briefings, Pricing & Offers, Customers & Leads. Count "not set" markers (they read back as `<i>not set</i>`) on each page as a completeness score. Count active rows in Pricing & Offers.
6. **Check the approval queue end to end:** create one Approvals row: Item "Self-test: queue check <nonce>", Department "Chief of Staff", Action type "Other", Exact action "No action. Test row.", Status "Pending", Source run "Self-test <date>". Read it back to confirm an AP number was assigned, then set its Status to "Done". Never delete it.
7. **Report two tables:**
   - Specialists: specialist, ran (yes/no), nonce matched, Notion, then one column per chosen app (or "Paste mode" for email or calendar, which always passes), result (PASS/FAIL). A chosen app that is unavailable is a warning, not a FAIL: the team falls back to the Paste Box.
   - Business Brain: item, present (yes/no), fields still not set.
   Plus: approval queue test PASS/FAIL with the AP number.
8. **Save** a Briefings row (Type = Self-test) with the tables.
9. **Summarize what to fix** in plain language: chosen apps that aren't reachable (reconnect, or switch to paste mode by saying "finish my setup"), missing Brain pieces (offer to run `setup-workforce` to add them), subagents that did not run.
