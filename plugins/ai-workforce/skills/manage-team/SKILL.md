---
name: manage-team
description: This skill should be used when the owner changes how the team works or who is on it, such as "from now on…", "always…", "never…", "make those replies shorter and friendlier", "our refund policy changed", "we raised our prices", "add a team member", "I'd like someone handling my podcast", "do we need another person for this?", "turn off Finance", or "remove the Podcast Producer".
metadata:
  version: "0.5.2"
---

# Manage the Team

_Files named `references/…` are in this skill's own folder._

The owner should never have to rebuild a team member. They say how they want the job done, in their own words, and you put it where the team will follow it every time. Everything is saved in the owner's Business Brain, so plugin updates never touch it. Follow `references/talking-to-the-owner.md`, `references/approval-policy.md` and `references/team-roles.md`. This skill needs the owner present.

## A. "From now on…" (how the work should be done)

0. **Check it's safe.** No saved rule can loosen the team's safety rules (`references/approval-policy.md`): the team still never sends, spends, publishes, deletes or changes financial records without the owner. If the request would loosen one, say so kindly, offer the closest safe version, and save only that.
1. **Work out where it belongs**, using the narrowest place that covers it:

   | The owner is changing | Save to |
   |---|---|
   | How one team member works ("Client Success: keep replies under five sentences") | Your Team → that member's section |
   | How the whole team writes (voice, sign-off, words to use or avoid) | Brand & Tone |
   | A rule for everyone ("never offer more than 20% off", "copy my assistant on VIP replies") | Workforce Settings → Extra rules for my team |
   | A policy (refunds, discounts, payment terms, response times, cancellations) | Policies |
   | Prices or offers | Pricing & Offers (update the row; add one for a new offer; untick Active for a retired one) |
   | What matters now, or what to ignore | Priorities |
   | An answer to a customer question | FAQs → Answered (and mark the line under Waiting for an answer "(answered <date>)") |
   | Which members take part in briefings | Workforce Settings → Active departments |
   | A one-off change to a single draft | Nowhere: just change that draft |

2. **Confirm in one line**, quoting the exact words you'll save: "Got it. I'll save this for Client Success: 'Keep replies under five sentences, warm and friendly.' OK?" Save only after they say yes.
3. **Save it**, add-only where possible: replace a placeholder line, or add a bullet. Fetch the page first. Placeholders read back in italics (`<i>none yet</i>`, `<i>not set</i>`) and repeat under every heading, so match the heading together with its placeholder, for example `### Client Success\n\n- <i>none yet</i>`. When a section already has bullets, add yours after the last one. When the new rule contradicts an old one, show both and ask which wins; then replace the old line. Never delete anything else.
4. **Say how it applies:** "Done. Client Success will follow this from the next reply on." If drafts made under the old rule are still waiting (pending approvals, Replies ready to copy), offer to redo them.

The team also learns this way from the review step: when the owner keeps changing drafts the same way, `review-approvals` offers to save the change here.

## B. Adding a team member

Reuse before expanding. Most new jobs belong to someone already on the team.

1. **Understand the job:** what work, how often, what a good result looks like, which apps or information it needs.
2. **Decide, in this order, and stop at the first yes:**
   1. **An existing member, with clearer instructions.** Podcast show notes fit Marketing; vendor follow-ups fit Operations. Offer: "Marketing can take this on. I'll add 'Podcast: research, show notes, repurposing' to Marketing's responsibilities on Your Team." Save it there (part A).
   2. **Something the owner already has.** If another installed plugin covers it, point the owner to it and let them use it themselves. The team doesn't hand its work to tools outside these rules.
   3. **A trusted outside source.** Don't search the web for agents and don't install anything. If the owner wants to look, they can browse Customize → Plugins → Discover; plugins in Anthropic's directory are reviewed by Anthropic, others are not. Anything from elsewhere needs the owner to check where it came from first.
   4. **A new custom team member**, only if the work recurs, has its own deliverables, and would crowd an existing member's job. More than three custom members usually means some should merge: say so.
3. **Draft the new member** and show it in plain language:
   - **Name and job** (one sentence)
   - **Responsibilities** (3-5 bullets)
   - **Deliverables** (what they hand back each time)
   - **What they use** (which Business Brain pages and connected apps)
   - **Limits:** "Follows every team rule: never sends, spends, publishes or deletes without your yes." Plus any extra limits the owner wants. A member's limits can be stricter than the team's, never looser.
   - **Recurring work**, if any
4. **Ask for approval:** "Add <Name> to your team with these responsibilities and limits?" Nothing is saved before a yes.
5. **Save** it under Custom team members on the Your Team page, one block per member: `### <Name>` then bullets for Status (Active), Job, Responsibilities, Deliverables, Uses, Limits, Recurring, Added (date, approved by owner).
6. **Be accurate about what it is.** In chat a custom member is a saved role your Chief of Staff takes on; in Cowork it runs as a separate assistant briefed with this role. It is not a separately installed agent, so never call it one. The owner can just think of it as a new team member.
7. **Offer a first task** to show it working (via `assign-work`), and offer to make its recurring work a recurring responsibility (`schedule-workforce`).

## C. Changing or removing a member

- **Change a custom member:** edit its block after the owner confirms the new wording.
- **Retire one:** set Status to "Retired" (never delete the block), and offer to pause any recurring responsibility it had.
- **Core members** can't be removed, but they can sit out. Under Active departments, no ticks means the default set (`references/run-modes.md`); once anything is ticked, only ticked members take part. So to turn one off, tick every other member the owner wants and leave that one unticked; to turn one back on, tick it. Check the result, then say what changes: "Finance won't appear in your briefings until you turn it back on."

## Proactive suggestions (used by the daily briefing)
At most once a week, the Chief of Staff may suggest one new responsibility or one new team member in the briefing, only when it rests on something the team actually saw. Examples: the same customer question answered three or more times; the owner changing drafts the same way repeatedly; one member repeatedly doing work outside its job. Record each suggestion under "Suggestions from your Chief of Staff" on Your Team with the date and "open". Mark it "accepted" or "declined" when the owner answers, and never repeat a declined one.
