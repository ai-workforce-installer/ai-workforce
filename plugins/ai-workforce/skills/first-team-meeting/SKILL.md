---
name: first-team-meeting
description: This skill should be used at the end of setup, and when the owner asks "what can my team take off my plate?", "what should my team work on?", "let's have a team meeting", "what else can you handle?", or wants the Chief of Staff to recommend responsibilities and get the team doing real work.
metadata:
  version: "0.4.3"
---

# Team Meeting

_Files named `references/…` are in this skill's own folder._

The owner should leave with real work done, not a plan. Recommend a few responsibilities grounded in this business, do one now, show the result, and offer to make it recurring. Speak like a Chief of Staff in a short meeting (`references/talking-to-the-owner.md`). Follow `references/approval-policy.md`, `references/team-roles.md`, `references/just-in-time.md` and `references/connections.md`. This skill needs the owner present.

## Steps

1. **Look at what you know.** From the Business Brain: Company Profile, Priorities (especially "Work I'd like to hand off"), Connections, Workforce Settings / Schedule, Customers & Leads, and the Your Team page (existing custom members, and suggestions already made or declined). If email or calendar is connected, take a quick read-only look to ground the recommendations: count recent customer and prospect emails and how many look unanswered (last 14 days), and how busy the next 7 days of the calendar are. Use senders and subjects only; don't read through private messages, and never store their contents. On paste mode, look at the Paste Box; if it's empty, invite the owner to paste two or three real customer emails and this week's key dates (into the Paste Box or right here), so the team has something real to work on.

2. **Recommend up to three responsibilities**, choosing from what the team can actually do today:

   | Responsibility | Team member | Runs with |
   |---|---|---|
   | Review all email, catch what matters and prepare replies | Chief of Staff with the team | `inbox-triage` |
   | Morning briefing: today's priorities, meetings, what needs you | Chief of Staff + team | `daily-executive-briefing` |
   | Find leads that need a follow-up and draft them | Sales | `assign-work` (Sales) |
   | Check the next week of commitments and flag problems | Operations | `assign-work` (Operations) |
   | Weekly marketing plan from last week's results | Marketing | `prepare-weekly-marketing` (needs a results source) |
   | Overdue invoice report and reminder drafts | Finance | `review-overdue-invoices` (needs an invoice source) |

   Rules:
   - Put the owner's own answer ("what do you spend too much time on?") first when it maps to one of these. If it maps to none, say plainly what the team can and can't do about it today, offer the closest fit, and mention that a custom team member is possible later (`manage-team`).
   - For each recommendation, give the reason in one line, using only what you actually saw or the owner said: "You have 14 customer emails from the last two weeks, 6 with no reply yet." With no evidence, say so: "A common place to start; I don't have numbers yet."
   - Leave out anything that needs a missing connection or data source, unless the owner asked for it; then say what's needed in one line.
   - Skip anything already set up as a recurring responsibility, and anything the owner declined before.

   Present them as a short numbered list and ask: "Which should we take on first?"

3. **Fill only the gaps this job needs** (`references/just-in-time.md`): at most 3 questions, proposing answers where you can. Save them.

4. **Do the work now** with the skill in the table, in attended mode, for a small real slice (for example, this week's emails, or the next five leads). Tell the owner in one line who's on it.

5. **Check the work actually happened.** Fetch the Briefings row back from Notion; check drafts exist where the result says they are (search Gmail drafts, or open the Replies ready to copy section); check any Approvals rows got AP numbers. If something didn't happen, say so plainly, fix it if you can, and never present it as done.

6. **Show the result:** what was done (counts, for example "4 reply drafts ready in Gmail"), the link to where it's saved, what needs the owner, and anything the team couldn't do and why. The first time approvals appear, explain them in one line: "Anything that needs your yes gets a number. Reply 'approve 3' or 'change 3: shorter' and I'll take care of it."

7. **Offer to make it recurring:** "Want the team to do this every weekday morning?" Suggest a sensible cadence. On yes, use `schedule-workforce` for this one responsibility only, which creates the recurring run, then confirms it exists. If recurring runs aren't available on their account, say so plainly and tell them they can ask for this any time ("Triage my inbox").

8. **Save the meeting** without creating a second record: add a short "Team meeting" section at the top of the Briefings row the work just created, with the recommendations and their reasons, what was chosen, and whether it's now recurring. Add the recommendations not chosen to "Suggestions from your Chief of Staff" on the Your Team page, each with today's date and "open", so they aren't lost or repeated.

9. **Close** in 3-4 lines: "Your team just handled its first assignment." Then how to talk to the team from here ("Have Sales work on…", "What's waiting for my approval?", "What's my team been working on?"), and one line on the next suggestion they could try when ready.
