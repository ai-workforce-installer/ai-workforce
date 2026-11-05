---
name: prepare-weekly-marketing
description: This skill should be used when the user asks to "prepare weekly marketing", "plan next week's marketing", "weekly marketing review", "marketing plan for the week", or wants last week's results reviewed and next week's content, tests and budget proposals prepared. Also used by the scheduled weekly marketing task.
metadata:
  version: "0.5.0"
---

# Prepare Weekly Marketing

_Files named `references/…` are in this skill's own folder._

Follow `references/approval-policy.md`, `references/approval-queue.md` and `references/run-modes.md`. Nothing is published, sent or spent; budget changes are proposals.

**Running team members:** wherever this skill says to launch a member with the Agent tool, follow the run rule in `references/team-roles.md` (own agent in Cowork, otherwise a briefed assistant, otherwise do that member's work yourself in this conversation), include the member's Your Team notes in the brief, and report honestly which way it ran.

## Steps

1. **Pick the run mode** (`references/run-modes.md`).
2. **Gather inputs.** Read the Business Brain: Workforce Settings (where marketing data lives), Company Profile, Brand & Tone, Priorities, Pricing & Offers, and last week's Weekly marketing row in Briefings. Look for last week's performance data in the named location, then Notion and the owner's file app (Google Drive or OneDrive, per Connections). If none exists: attended, ask the user to paste or attach an export; scheduled, plan from the Business Brain alone and state that no performance data was found.
3. **Delegate** to `marketing-manager` (Agent tool): analyze last week, name winners and losers with numbers, then draft next week's plan: content calendar, 3-5 creative or copy variants to test with a hypothesis each, and budget change proposals with exact values. End with Approvals Needed and a Run receipt.
4. **Collaborate.** Launch `sales-manager` for which offers or lead sources are converting and what objections prospects raise, and `client-success-manager` for recurring customer questions worth content. Pass their findings to marketing for a second pass if they change the plan.
5. **Verify.** Check every metric against the source data and recompute rates (CTR, CPC, conversion rate, CPA) yourself. Mark anything unsourced as unverified.
6. **Queue approvals.** Every publish, send or budget change becomes an Approvals row with exact values (Action type = Publish, Send message or Spend money).
7. **Save** the full plan in this run's record (`references/run-tracking.md`) (Type = Weekly marketing), plus Assignments rows. Never overwrite earlier plans.
8. **Report:** last week in 5 lines, next week's plan (content, tests, drafts), budget proposals, Approvals Needed by AP number, Run receipt. Notify in scheduled runs.
