---
name: manage-team
description: This skill should be used when the owner changes how the team works or who is on it, or corrects what the team thinks matters, such as "from now on…", "always…", "never…", "make those replies shorter and friendlier", "our refund policy changed", "we raised our prices", "that isn't my responsibility anymore", "stop bringing this up", "that company isn't one of my businesses anymore", "this kind of email doesn't matter to me", "family and school emails matter", "add a team member", "I'd like someone handling my podcast", "do we need another person for this?", "turn off Finance", or "remove the Podcast Producer".
metadata:
  version: "1.0.0"
---

# Manage the Team

_`references/…` files are in this skill's folder (same-named files elsewhere are identical copies). Read each once at most, the ones you need together. A file named `references/if-….md` covers one situation: read it only when it comes up._

The owner should never have to rebuild a team member. They say how they want the job done, in their own words, and you put it where the team will follow it every time. Everything is saved in the owner's Business Brain, so plugin updates never touch it. Follow `references/talking-to-the-owner.md`, `references/approval-policy.md`, `references/team-roles.md` and `references/owner-corrections.md`. This skill needs the owner present.

## A. "From now on…" (how the work should be done)

0. **Check it's safe.** No saved rule can loosen the team's safety rules (`references/approval-policy.md`), and a preference never grants new permission to send or spend: never infer one. If the request would loosen a rule, say so kindly, offer what the policy allows (for "just send the FAQ replies": the Sending setting, on the owner's yes, never in a run nobody is watching), and save only that.
1. **Work out where it belongs**, using the narrowest place that covers it:

   | The owner is changing | Save to |
   |---|---|
   | How one team member works ("Client Success: keep replies under five sentences") | Your Team → that member's section |
   | How the whole team writes (voice, sign-off, words to use or avoid) | Brand & Tone |
   | A rule for everyone ("never offer more than 20% off", "copy my assistant on VIP replies") | Workforce Settings → Extra rules for my team |
   | A policy (refunds, discounts, payment terms, response times, cancellations) | Policies |
   | Prices or offers | Pricing & Offers (update the row; add one for a new offer; untick Active for a retired one) |
   | What matters now, or what to ignore | Priorities (This month's focus; Things to ignore for now) |
   | What always deserves the owner's attention ("family and school emails") | Priorities → Always worth my attention |
   | Something that isn't the owner's anymore (a business, client, account, automation) | Priorities → Not my responsibility anymore (`references/owner-corrections.md`) |
   | An answer to a customer question | FAQs → Answered (and mark the line under Waiting for an answer "(answered <date>)") |
   | Which members take part in briefings | Workforce Settings → Active departments |
   | A one-off change to a single draft | Nowhere: just change that draft |

2. **Say the exact words you'll save.** A style or working preference the owner states outright ("use this shorter style from now on", "finish what's waiting before starting something new") is saved straight away, with no second "Save this?": confirm in one line what was saved and where, and that "undo" takes it back. Everything else is confirmed first and saved only after their yes: a price, a policy, a fact, anything you inferred, and above all a rule that hides items (part A2), because a wrong one silently buries mail. "Got it. I'll save this for Client Success: 'Keep replies under five sentences, warm and friendly.' OK?"
3. **Save it**, add-only where possible: replace a placeholder line, or add a bullet. Fetch the page first. Placeholders read back in italics (`<i>none yet</i>`, `<i>not set</i>`) and repeat under every heading, so match the heading together with its placeholder, for example `### Client Success\n\n- <i>none yet</i>`. When a section already has bullets, add yours after the last one. When the new rule contradicts an old one, show both and ask which wins; then replace the old line, except on Priorities' correction sections, where the old line gets " · no longer applies <date>" instead (`references/owner-corrections.md`). Never delete anything else.
4. **Say how it applies:** "Done. Client Success will follow this from the next reply on." If drafts made under the old rule are still waiting, offer to redo them.

## A2. "That's not mine anymore" / "stop bringing this up"
The owner is correcting what the team thinks matters. Follow `references/if-owner-corrects.md` (this item only, this thread, a lasting rule or a temporary one; the exact line confirmed before anything is saved; related items closed with their history kept), then say how it applies: "Done. The team won't raise the old Northwind automations again. A new security problem on your own accounts would still come to you."

To take a rule back ("actually, do tell me about Northwind"), add " · no longer applies <date>" to its line after the owner confirms; never delete it.

## B. Adding a team member

Reuse before expanding. Most new jobs belong to someone already on the team.

1. **Understand the job:** what work, how often, what a good result looks like, which apps or information it needs.
2. **Decide, in this order, and stop at the first yes:**
   1. **An existing member, with clearer instructions.** Podcast show notes fit Marketing; vendor follow-ups fit Operations. Offer: "Marketing can take this on. I'll add 'Podcast: research, show notes, repurposing' to Marketing's responsibilities on Your Team." Save it there (part A).
   2. **Something the owner already has.** If another installed plugin covers it, point to it. Don't search the web for agents or install anything: the owner can browse Customize → Plugins, and should check where anything from elsewhere came from.
   3. **A new custom team member**, only if the work recurs, has its own deliverables, and would crowd an existing member's job. More than three custom members usually means some should merge: say so.
3. **Draft the new member** and show it in plain language:
   - **Name and job** (one sentence)
   - **Responsibilities** (3-5 bullets)
   - **Deliverables** (what they hand back each time)
   - **What they use** (which Business Brain pages and connected apps)
   - **Limits:** "Follows every team rule: never sends, spends, publishes or deletes without your yes." Plus any extra limits the owner wants. A member's limits can be stricter than the team's, never looser.
   - **Recurring work**, if any
4. **Ask for approval:** "Add <Name> to your team with these responsibilities and limits?" Nothing is saved before a yes.
5. **Save** it under Custom team members on the Your Team page, one block per member: `### <Name>` then bullets for Status (Active), Job, Responsibilities, Deliverables, Uses, Limits, Recurring, Added (date, approved by owner).
6. **Be accurate about what it is.** In chat a custom member is a saved role your Chief of Staff takes on; in Cowork it runs as a separate assistant briefed with this role. It is never a separately installed agent; to the owner it is simply a new team member.
7. **Offer a first task** to show it working (via `assign-work`), and offer to make its recurring work a recurring responsibility (`schedule-workforce`).

## C. Changing or removing a member

- **Change a custom member:** edit its block after the owner confirms the new wording.
- **Retire one:** set Status to "Retired" (never delete the block), and offer to pause any recurring responsibility it had.
- **Core members** can't be removed, but they can sit out. Under Active departments, no ticks means the default set (`references/run-modes.md`); once anything is ticked, only ticked members take part. So to turn one off, tick every other member the owner wants; to turn it back on, tick it. Then say what changes.

## Proactive suggestions
The daily briefing may add one suggestion a week (its rule is there). When the owner answers one, mark it "accepted" or "declined" under "Suggestions from your Chief of Staff" on Your Team, and never repeat a declined one.
