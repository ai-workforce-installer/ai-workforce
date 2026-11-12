# If the owner corrects the team or a draft

Read this only when the owner, in the chat, pushes back on something the team raised, says something isn't theirs or doesn't matter, or gives feedback on a draft. Section numbers continue from `references/owner-corrections.md`, which every run reads for applying the rules already saved (its section 5).

## 1. Work out what kind of correction it is

| The owner says (examples) | Kind | What happens |
|---|---|---|
| "I already handled that." "I sent it." "That purchase was intentional." "Two is fine." | **This item only** | Close this item (section 4). No rule, and never permission for any other action (`review-approvals`, "Understanding replies"). |
| "Ignore this thread." "Stop telling me about this one." | **Narrow lasting rule** (this one thing) | Close it, confirm one line naming just that thread or sender and subject ("Things to ignore: the 'Weekly sync failed' emails from Make"), and save it under Things to ignore for now, so it holds however long it goes on. |
| "That isn't my responsibility anymore." "That company isn't one of my businesses." "Don't keep bringing this up." | **Lasting rule** | Confirm once, then save it (sections 2-3) and close related open work (section 4). |
| "This kind of notification isn't important to me." "GitHub notifications from other repos don't matter." | **Lasting rule** (what to ignore) | Same. |
| "Family and school emails deserve my attention." | **Lasting rule** (what matters) | Same, saved under Always worth my attention. |
| "Ignore the launch emails until Friday." "Not this week." | **Temporary rule** | Saved with "until <date>"; stops applying after that date (the line stays, as history). |
| "Sounds too formal." "I wouldn't sign it with my name." "That claim isn't accurate." "Use a stronger opening." | **Draft feedback** | Fix the current draft now; offer to save it as a lasting writing preference (section 6). |

When it's not clear whether the owner means this item or a lasting rule, ask **one** short question that proposes the rule ("I'll close AP-7. Should the team stop raising alerts about the old Northwind automations from now on?"). Never turn an ambiguous remark into a lasting rule.

## 2. Confirm a lasting rule in one line

Quote the exact words you'll save, what still gets through, and the related items you'd close: "I'll save: 'Not my responsibility anymore: Northwind Studio, including its automations and their failure alerts (since Nov 6).' I'll still tell you about a new security problem or money leaving your accounts. I'll also close AP-4 and AP-9. OK?"

One yes covers the rule and the related items you listed. Save nothing before that yes.

Make the rule as narrow as what the owner said: a business, an account, an automation, a sender, a kind of notification. Never widen "the old Make automation" into "all Make emails" or "all automation alerts".

## 3. Where it's saved (existing pages only)

Priorities holds what deserves attention and what doesn't, under three headings: "Not my responsibility anymore" (businesses, clients, accounts, automations the owner no longer looks after), "Things to ignore for now" and "Always worth my attention". Writing preferences go to Brand & Tone (or that member's section on Your Team), per `manage-team` part A. A rule for everyone ("never raise anything about my old agency") can go under Extra rules for my team if the owner prefers.

One bullet per rule, in this shape:
`- <what it covers, in the owner's words> · since <date>` (add ` · until <date>` for a temporary rule).

On an older workspace without the "Not my responsibility anymore" or "Always worth my attention" headings, save the line under "Things to ignore for now" (starting it "Not my responsibility:" when that's what it is) or under This month's focus, and offer the workspace upgrade once (`references/brain-upgrades.md`). Never create the heading outside the upgrade.

Saving follows `manage-team` part A: fetch the page first, replace a placeholder or add a bullet after the last one, and when the new rule contradicts an old one, show both and ask which wins. Lines are never deleted: a rule the owner takes back gets " · no longer applies <date>" added at its end, so the history stays readable.

## 4. Close the item and related open work (history kept)

| Kind | Approvals row | Assignments row (team-created) |
|---|---|---|
| Already handled, acknowledged | Done, Owner note "Owner: already handled <date>" (or their words) | Done, with that reason in Result |
| Not mine / don't raise | Rejected, Owner note "Owner: not my responsibility (<rule>, <date>)" | Done, Result "Closed: owner says not their responsibility" |
| Temporary | Leave Pending only if it will still matter after the date; otherwise Expired with the reason | Leave open with Next action "Wait until <date>", or Done |

- Only rows the team created, and only the ones the owner named or confirmed in the same yes (section 2). Never touch rows the owner created.
- Add to Owner note and Result; never overwrite them. Never delete a row: closed rows leave the active queue and the Open work view but stay in the database as history.
- Gmail drafts the team made for a closed item stay where they are (mention them once); never delete them.
- When this happens during an inbox run, also list the item's source key in that run's Handled list, so retries and overlapping windows don't raise it again.

## 6. Draft feedback: fix it now, offer to keep it

1. **Apply it to the current draft right away** and show the changed part (or the whole draft if short). Update the same draft in place: the same Gmail draft, the same Briefings text, the same Approvals row's Draft link. Never create a new approval or a second draft for a wording change.
2. **Offer once to make it lasting** (unless the owner already said "from now on": then save it and say what was saved), quoting the line: "Want me to save 'Write conversationally; sign off with just my first name' to Brand & Tone so every draft does this?" Offer when the feedback is about style, voice, sign-off, words to use or avoid, or a fact that will come up again. Don't offer for a one-off ("make this one shorter").
3. **A factual correction** ("that claim isn't accurate", "we don't offer that") is saved where the fact lives (Company Profile, Pricing & Offers, Policies, FAQs) only after the owner gives the right version; until then the claim is simply removed from the draft.
4. **The owner keeps making the same change** (second time): offer to save it even if it looked like a one-off.
5. Saved preferences apply from the next draft on, and drafts still waiting under the old rule are offered for a redo (`manage-team` part A, step 4).
