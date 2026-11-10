# Business Brain Interview (complete version)

Used when the owner says "finish my setup" or "update my Business Brain answers", and as the field map for saving any answer. The normal first-time setup does **not** run this whole interview: it learns from the website, asks one question, and the team asks the rest just in time (`references/just-in-time.md`). Ask only about fields that are still empty.

Goal: every field in the Business Brain is either answered by the owner or deliberately skipped, and every answer is saved to Notion as soon as the owner confirms it. The team relies on these answers for every draft, quote and decision, so cover all of them.

## How to run it

- **One topic at a time**, at most 3 questions per message. Use multiple-choice options when a question tool is available; otherwise ask in plain text.
- **Propose before you ask.** Use what you already know (website, earlier answers, whatever email and calendar the owner connected) to draft an answer and ask "Is this right?" Owners correct faster than they write. Say what you looked at.
- **Confirm, then save immediately.** After each topic, show the answers as 2-6 bullets, ask "Save this?", and on yes write them to Notion right away (see Saving). Then show one progress line, e.g. `Saved: Policies (topic 5 of 11)`.
- **Skipping is fine.** "Skip" or "later" leaves that field as `not set` and moves on. Keep a list of skipped fields for the end.
- **Confirmed, not inferred.** Only what the owner confirms is saved. Facts drafted from the website, an email or a calendar are proposals until then, and a yes to a summary covers its descriptive points, not prices or policies: confirm each price, offer and policy on its own line ("from your website, not confirmed: 30-day refunds. Still right?"). Never save or quote an unconfirmed one.
- **Already answered is answered.** Anything the owner said earlier in setup, in this chat, or that's already saved is not asked again; show it for a quick check instead ("You said replies within a day. Still right?").
- **The owner's words, lightly tidied.** Never invent prices, policies, facts or quotes. If an answer is vague ("depends"), save it as said and add "ask me case by case" so the team escalates.
- **Resuming.** If setup is restarted, fetch every page first and start at the first topic that still has `not set` fields. Don't re-ask answered fields; offer to review them instead.
- **Pace.** Aim for 20-30 minutes for whatever is still empty. If the owner is in a hurry, do the topics marked ★ first (the minimum for a useful team) and offer the rest later.

## Saving

- Fetch the page before writing. Unanswered fields read back as `<i>not set</i>` (or `<i>paste one here</i>`, `<i>none yet</i>`, and similar italics on FAQs and Extra rules). The same marker appears many times, so always replace the **whole line including its label** (`- Name: <i>not set</i>` → `- Name: Dana Lee`), or the **heading plus marker** for paragraph fields (`## Refunds\n\n<i>not set</i>`).
- Lists (goals, words we use, FAQs, extra rules): replace the placeholder line with one bullet or numbered line per item.
- Database rows (Pricing & Offers, Customers & Leads): create one row per item with the exact property names below.
- If a write is refused, re-fetch the page, match the text as it now stands, and retry once. If it still fails, tell the owner which field didn't save and keep going.

## Topics (ask in this order)

| # | Topic | Ask | Saves to |
|---|---|---|---|
| 1 ★ | **You** | Your name; the email address customers write to; your time zone (suggest one from the session); your working hours | Workforce Settings → Owner: `Name`, `Business email`, `Time zone`, `Working hours` |
| 2 ★ | **Your business** | Offer the fast start: "Give me your website and I'll draft this, then you correct me." Then confirm or ask: what you do in 1-2 sentences; who your ideal customer is and the problem you solve; what makes you different; your website plus any key links (booking page, store, socials) | Company Profile: `What we do`, `Who we serve`, `What makes us different`, `Website and key links` |
| 3 | **Your people** | Who else works in the business (name, role)? Who should the team escalate to for what? | Company Profile: `Team (humans)` |
| 4 ★ | **What you sell** | List every product or service. For each: price; billing (one-time, monthly, annual, free); what's included; a link if there is one; the lowest price you'd ever accept; the most you'd ever discount, in %; anything else the team should know. Then summarize all offers in one sentence for `Main products and services`. | Pricing & Offers: one row each with `Offer`, `Price`, `Billing`, `Includes`, `Link`, `Lowest allowed price`, `Max discount %`, `Notes`, `Active` = yes. Company Profile: `Main products and services` |
| 5 ★ | **Your rules** | Refunds (offer: no refunds / 14-day / 30-day / case by case); discounts (who qualifies, how much, what you want in return); how fast customers and new leads should hear back; payment terms (when due, accepted methods, late fees); cancellations (notice, what happens to access); what should always come straight to you | Policies: `Refunds`, `Discounts`, `Response times`, `Payment terms`, `Cancellations`, `Always escalate to me` (keep the existing first bullet, add theirs) |
| 6 ★ | **Your voice** | Your voice in three words; how you sign off emails; words or phrases you like to use; words you never want used. If setup already picked up their style from their sent mail and they confirmed it, ask only for what is still empty. Otherwise offer: "Want me to learn your style from a few emails you've sent?" If yes, read the 5-10 most recent sent emails, summarize the style (greeting, length, formality, sign-off, phrases), and save only what the owner confirms: the style, never those emails' contents, names or addresses. Finally ask them to paste or write one short example email that sounds like them (skippable). | Brand & Tone: `Our voice in three words`, `How I sign off`, `Words and phrases we use`, `Words and phrases we never use`, `Example of an email that sounds like me` |
| 7 ★ | **Common questions** | What do customers ask you most? Aim for 5-10, each with the answer you want given. Offer to find candidates in their inbox (recent customer emails with repeated questions) and propose them. | FAQs → `Answered`: one `**Q:** …` / `A: …` pair per question |
| 8 | **Your focus** | Top 3 goals this quarter; this month's focus; what the team should ignore for now; what always deserves your attention (for example family or school emails); any business, client, account or automation that isn't yours anymore; the work you'd most like to hand off | Priorities: numbered goals, `This month's focus`, `Things to ignore for now`, `Always worth my attention`, `Not my responsibility anymore` (each line "… · since <date>", per `references/owner-corrections.md`), `Work I'd like to hand off` |
| 9 | **Where things live** | Which inbox, folder or label holds customer emails (on paste mode: write "Paste Box")? Where are invoices kept? Where are marketing results? The team can only read the apps connected in Stage 1 plus Notion: if invoices or ad results live in another tool (Stripe, QuickBooks, Meta Ads Manager), suggest a weekly CSV export into one Drive or OneDrive folder and save its name; with no file app, suggest pasting the export into a Notion page and save that page's name. | Workforce Settings → Where things live: `Customer email inbox`, `Invoices are kept in`, `Marketing performance data` |
| 10 | **Key customers** (optional) | Your 5-10 most important current customers or open leads: name, company, email, stage, rough value, last contact, next step | Customers & Leads: one row each with `Name`, `Company`, `Email`, `Stage`, `Value`, `Last contact`, `Next step`, `Notes` |
| 11 | **House rules** | "Anything your team should always or never do?" (e.g. "never offer more than 20% off", "always copy my assistant on VIP replies") | Workforce Settings → `Extra rules for my team` |

These are filled elsewhere, not by the interview:
- **Connections** (Workforce Settings): Stage 1 and 2 of the setup skill fill them. Don't ask again.
- **Active departments** (Workforce Settings): left unticked by setup (the team then uses its default set); the owner changes them by asking (`manage-team`).
- **Your Team** page: filled by `manage-team` when the owner says how a member should work or adds a team member.
- **Schedule** (Workforce Settings): the `schedule-workforce` skill fills it. If the owner doesn't schedule now, write `not scheduled yet` on each line.

## Completeness check (end of interview)

1. Re-fetch every page (Workforce Settings, Company Profile, Priorities, Policies, Brand & Tone, FAQs) and count the remaining `not set`-style markers. Count rows in Pricing & Offers.
2. Show a short table: page, fields saved, fields still empty.
3. If any ★ field is still empty, or Pricing & Offers has no rows, say plainly what the team can't do without it (for example "Sales can't quote anything until at least one offer is saved"), and offer to fill those now. Ask only about the empty fields.
4. Finish with the Business Brain link and one line: "You can change any answer by editing the page in Notion, or by telling me."
