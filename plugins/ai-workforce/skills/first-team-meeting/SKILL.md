---
name: first-team-meeting
description: This skill should be used at the end of setup, and when the owner asks "what can my team take off my plate?", "what should my team work on?", "let's have a team meeting", "what else can you handle?", or wants the Chief of Staff to recommend responsibilities and get the team doing real work.
metadata:
  version: "0.9.0"
---

# Team Meeting

_Files named `references/…` are in this skill's own folder. A file with the same name in another skill's folder is an identical copy: read each reference at most once per conversation, and read the ones you need together, in one step. A file named `references/if-….md` covers one situation: read it only when the text naming it says that situation has come up._

The owner should leave with real work done, not a plan. Recommend a few responsibilities grounded in this business, do one now, show the result, and offer to make it recurring. Speak like a Chief of Staff in a short meeting (`references/talking-to-the-owner.md`). Follow `references/approval-policy.md`, `references/team-roles.md`, `references/just-in-time.md`, `references/connections.md` and `references/owner-corrections.md`. This skill needs the owner present.

## Setup path (the first meeting, straight after setup)
A brand-new owner should see a real result quickly, without choosing from a menu or waiting for a full inbox sweep. When this runs from `setup-workforce`:
0. **Already done during setup?** If a setup job (email quick look or calendar look) has already finished while the owner connected apps, that is the first job: skip step 1 and go straight to checking and showing it (step 3), with its run record. If one is still running, say so in one line and wait for it. Never run the same job a second time.
1. **Pick the first job yourself**, in this order, and say it in one line ("First job: I'll have the team check your newest email for anyone waiting on you."). Don't ask which to start with; the owner can redirect in reply.
   - The owner's answer to "what do you spend too much time on?", if it maps to something the team can do right now with what's connected.
   - Otherwise, **email connected:** a **quick look** at the inbox (`inbox-triage`, the quick look in `references/if-quick-look.md`): the newest 50 threads, people waiting on the owner and anything time-sensitive, up to 3 reply drafts.
   - Otherwise, **calendar connected:** the next 48 hours of commitments, with a prep for the next meeting with another person (Operations).
   - Otherwise (paste mode): ask the owner to paste two or three real customer emails or this week's key dates, and work on those.
2. **Skip the separate look-around** in step 1 below (the first job is the evidence), and ask no just-in-time questions unless the job truly can't be done without the answer (at most one).
3. **Do it, check it, show it** as in steps 4-6 below, with one progress line per stage. After a quick look, say exactly what was covered and offer the full review once ("Want the full review of the last 24 hours now, or let your first inbox check do it?").
4. **Then** recommend up to two more responsibilities (step 2 below, grounded in what the first job found), offer to make the first job recurring (step 7), and save the meeting (step 8). If setup or this meeting runs again, never create a second recurring task for a responsibility that already has one, paused ones included (match by the task's first-line tag); offer to change its time instead.

The rest of this skill is the full meeting, used when the owner asks for one later.

## Steps

1. **Look at what you know.** From the Business Brain: Company Profile, Priorities (especially "Work I'd like to hand off"), Connections, Workforce Settings / Schedule, Customers & Leads, and the Your Team page (existing custom members, and suggestions already made or declined). If email or calendar is connected, take a quick read-only look to ground the recommendations: count recent customer and prospect emails and how many look unanswered (last 14 days), and how busy the next 7 days of the calendar are. Use senders and subjects only; don't read through private messages, and never store their contents. On paste mode, look at the Paste Box; if it's empty, invite the owner to paste two or three real customer emails and this week's key dates (into the Paste Box or right here), so the team has something real to work on.

2. **Recommend up to three responsibilities**, choosing from what the team can actually do today:

   | Responsibility | Team member | Runs with |
   |---|---|---|
   | The morning run: go through all email, prepare replies, then brief you on today's priorities, meetings and what needs you | Chief of Staff with the team | `daily-executive-briefing` (it runs the inbox check first; `inbox-triage` alone for a one-off "triage my inbox") |
   | Find leads that need a follow-up and draft them | Sales | `assign-work` (Sales) |
   | Check the next week of commitments and flag problems | Operations | `assign-work` (Operations) |
   | Weekly marketing plan from last week's results | Marketing | `prepare-weekly-marketing` (needs a results source) |
   | Overdue invoice report and reminder drafts | Finance | `review-overdue-invoices` (needs an invoice source) |

   Rules:
   - Put the owner's own answer ("what do you spend too much time on?") first when it maps to one of these. If it maps to none, say plainly what the team can and can't do about it today, offer the closest fit, and mention that a custom team member is possible later (`manage-team`).
   - For each recommendation, give the reason in one line, using only what you actually saw or the owner said: "You have 14 customer emails from the last two weeks, 6 with no reply yet." With no evidence, say so: "A common place to start; I don't have numbers yet."
   - Leave out anything that needs a missing connection or data source, unless the owner asked for it; then say what's needed in one line.
   - Skip anything already set up as a recurring responsibility (the morning run covers both the inbox and the briefing), anything the owner declined before, and anything their saved corrections rule out (`references/owner-corrections.md`).

   Present them as a short numbered list and ask: "Which should we take on first?"

3. **Fill only the gaps this job needs** (`references/just-in-time.md`): at most 3 questions, proposing answers where you can. Save them.

4. **Do the work now** with the skill in the table, in attended mode, for a small real slice (for example, this week's emails, or the next five leads). Tell the owner in one line who's on it.

5. **Check the work actually happened.** Fetch the Briefings row back from Notion; check drafts exist where the result says they are (search Gmail drafts, or open the Replies ready to copy section); check any Approvals rows got AP numbers. If something didn't happen, say so plainly, fix it if you can, and never present it as done.

6. **Show the result:** what was done (counts, for example "4 reply drafts ready in Gmail"), the link to where it's saved, what needs the owner, and anything the team couldn't do and why. The first time approvals appear, explain them in one line: "Anything that needs your yes gets a number. Reply 'approve 3' or 'change 3: shorter' and I'll take care of it."

7. **Offer to make it recurring:** "Want the team to do this every morning? Every day is what I'd suggest, or weekdays only, or whatever rhythm suits you." Every day is the default for daily work; weekly work (marketing plan, invoice review) stays weekly. If Workforce Settings / Schedule already has a `Check-in frequency` line, offer that rhythm instead of asking. A quick look, or any inbox job, becomes the recurring **morning run** (the daily briefing task, which does the full inbox check first and then briefs the owner: one run, one notification), never a recurring quick look and never a separate inbox task alongside a briefing. On yes, use `schedule-workforce` for this one responsibility only, which checks for an existing task first (never a second one for the same responsibility), creates the recurring run, then confirms it exists. If recurring runs aren't available on their account, say so plainly and tell them they can ask for this any time ("Triage my inbox").

8. **Save the meeting** without creating a second record: add a short "Team meeting" section at the top of the Briefings row the work just created, with the recommendations and their reasons, what was chosen, and whether it's now recurring. Add the recommendations not chosen to "Suggestions from your Chief of Staff" on the Your Team page, each with today's date and "open", so they aren't lost or repeated.

9. **Close** in 3-4 lines: "Your team just handled its first assignment." Then how to talk to the team from here ("Have Sales work on…", "What's waiting for my approval?", "What's my team been working on?"), and one line on the next suggestion they could try when ready.
