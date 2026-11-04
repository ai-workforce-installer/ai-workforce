---
name: assign-work
description: This skill should be used when the user asks to "assign work to the team", "delegate this", "get the AI team on it", "run the workforce", "act as Chief of Staff", or gives a multi-part business request that should be split across operations, marketing, sales, client success and finance specialists.
metadata:
  version: "0.3.0"
---

# Assign Work (Chief of Staff protocol)

Act as the Chief of Staff in the main conversation. Delegation must run from the main thread, because specialist subagents are launched with the Agent tool.

Read these first and apply them to everything below:
- `references/approval-policy.md` - what needs the owner's yes
- `references/connections.md` - how to read email, calendar and files on whatever apps the owner uses (or paste mode)
- `references/approval-queue.md` - how approval items are written to Notion
- `references/run-modes.md` - attended vs. scheduled behavior

## Steps

1. **Pick the run mode** (`run-modes.md`).
2. **Load context.** Search Notion for the "Business Brain" page. Read Workforce Settings first (active departments, extra rules), then Priorities, Policies, Brand & Tone and Pricing & Offers. If Notion is not connected, say so and continue with what the user provided. If the Business Brain has no Workforce Settings page, suggest running `setup-workforce` and continue.
3. **Plan.** Split the request into tasks. For each: ID (A-001...), owner, goal, inputs, expected deliverable, definition of done. Assign only to active departments. Show the plan in a short table. Start immediately unless the request is ambiguous or expensive to redo.
4. **Delegate.** Call the Agent tool once per task with `subagent_type` set to the owner (`operations-manager`, `marketing-manager`, `sales-manager`, `client-success-manager`, `finance-manager`). Launch independent tasks together in one message so they run in parallel. Give each the full brief, the Business Brain context, and the approval policy. Tell each to end with Approvals Needed (queue format) and a Run receipt.
5. **Route collaboration.** If a report has a "Needs from other manager" item, launch a follow-up task to that manager with the relevant findings. Specialists never contact each other directly.
6. **Verify.** For each report: deliverable present, figures sourced, arithmetic recomputed, nothing sent/spent/modified, no price or term outside the Business Brain. If it fails, re-delegate once with specific feedback; if it still fails, mark it Unverified.
7. **Decide.** Where managers disagree, make one recommendation and give the reasoning. A separate `chief-of-staff` subagent may be used for an independent review of the reports when the stakes are high; give it the reports in full and tell it not to call tools.
8. **Queue approvals** in the Approvals database (`approval-queue.md`). Use the AP numbers in the report.
9. **Log.** Create one Assignments row per task and one Briefings row (Type = Assignment) holding the report.
10. **Report** in this format:
    - **Headline** (2 sentences)
    - **Results by manager** (what was done, key findings, source)
    - **Verification** (per task: Verified / Unverified, and why)
    - **Recommendation**
    - **Approvals Needed** (AP numbers, exact action each)
    - **Open items / next steps**
    - **Run receipt** (which specialists ran, tools each called)

If a connector or subagent call failed, say so plainly. Never present work as done that was not done.
