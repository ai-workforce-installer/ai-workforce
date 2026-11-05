---
name: prepare-weekly-marketing
description: This skill should be used when the user asks to "prepare weekly marketing", "plan next week's marketing", "weekly marketing review", "marketing plan for the week", or wants last week's results reviewed and next week's content, tests and budget proposals prepared. Also used by the scheduled weekly marketing task.
metadata:
  version: "0.5.2"
---

# Prepare Weekly Marketing

_Files named `references/…` are in this skill's own folder._

Follow `references/approval-policy.md`, `references/approval-queue.md` and `references/run-modes.md`. Nothing is published, sent or spent; budget changes are proposals.

**Running team members:** wherever this skill says to launch a member with the Agent tool, follow the run rule in `references/team-roles.md` (own agent in Cowork, otherwise a briefed assistant, otherwise do that member's work yourself in this conversation), include the member's Your Team notes in the brief, and report honestly which way it ran.

## Steps

1. **Pick the run mode and start this run's record** (`references/run-tracking.md`) (`references/run-modes.md`).
2. **Gather inputs.** Read the Business Brain: Workforce Settings (where marketing data lives), Company Profile, Brand & Tone, Priorities, Pricing & Offers, and last week's Weekly marketing row in Briefings. Look for last week's performance data where Workforce Settings says it lives first, then in any other place the owner has named for it (Notion, their file app per Connections). Not finding it there doesn't mean it doesn't exist: say "Last week's results weren't available to the team", never "there were no results". Then:
   - Label every past metric Verified (traced to the data) or Unavailable; never estimate one.
   - Still prepare a useful plan for next week from the Business Brain, Priorities and anything verified.
   - Say exactly what's needed next time, in a few lines: the source (for example a Meta Ads Manager export), the date range (last Monday to Sunday), the columns (date, campaign, ad set, ad, amount spent, impressions, clicks, leads or results, purchases, revenue if tracked), and where to put it (the location named in Workforce Settings). Attended: offer to take a pasted or attached export now.
   - Never create folders, connect accounts or change business data to get it.
   - If the task includes reviewing last week and that couldn't be done, the run is Partial.
3. **Delegate** to `marketing-manager` (Agent tool): analyze last week, name winners and losers with numbers, then draft next week's plan: content calendar, 3-5 creative or copy variants to test with a hypothesis each, and budget change proposals with exact values. End with Approvals Needed and a Run receipt.
4. **Collaborate only when it adds something.** If the Chief of Staff already has recent findings from Sales or Client Success (open work, recent run records), pass them to Marketing in its brief instead of launching them. Launch `sales-manager` or `client-success-manager` only for a specific question Marketing can't answer from what it was given, and at most one round.
5. **Verify.** Check every metric against the source data and recompute rates (CTR, CPC, conversion rate, CPA) yourself. Mark anything unsourced as Unavailable or Unverified. Check dated promotions (date, link, terms, timing) per `references/team-roles.md`.
6. **Queue approvals.** Every publish, send or budget change becomes an Approvals row with exact values (Action type = Publish, Send message or Spend money).
7. **Save** the full plan in this run's record (`references/run-tracking.md`) (Type = Weekly marketing), plus Assignments rows. Never overwrite earlier plans.
8. **Report:** last week in 5 lines, next week's plan (content, tests, drafts), budget proposals, Approvals Needed by AP number, Run receipt. Notify in scheduled runs.
