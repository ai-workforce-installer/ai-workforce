---
name: setup-workforce
description: This skill should be used when the user asks to "set up the workforce", "set up my AI team", "finish my setup", "continue the setup interview", "update my Business Brain answers", "setup-workforce", "build my Business Brain", "get started with the AI Workforce", "onboard me", or is using the AI Workforce plugin for the first time and has no Business Brain yet.
metadata:
  version: "0.3.0"
---

# Set Up the AI Workforce

Take a business owner who has never used Claude from zero to a working AI team in one sitting (about 30-45 minutes). Speak in plain, friendly language. Never mention file paths, schemas, tool names or JSON to the user. Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`.

Create a task list with these stages so the owner can see progress: Connect apps, Build the Business Brain, Interview, Choose departments, Self-test, Schedule.

## Stage 1: Connect apps (one at a time; do not move on until each is settled)
Only Notion is required. For email, calendar and files the owner picks what they already use, or paste mode if they use something else or would rather not connect. Every path gives a working team; `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/connections.md` explains how each one works. Never make the owner feel they did something wrong by not using Google.

**The connect loop** (used for every app below):
a. Say in one or two plain sentences what the team uses the app for.
b. Search the connector registry for that one app and suggest it, so the owner sees a one-click Connect card. Tell them: "Click Connect, sign in, allow access, then come back here and reply **done**."
c. Stop and wait for the owner's reply. Ask nothing else in that message.
d. When they reply, reload that app's tools (ToolSearch again) and try one harmless read: Notion search "Business Brain"; Gmail search for 1 recent thread; Google Calendar list today's events; Google Drive list recent files; Microsoft 365 search email for one recent message. Newly connected apps can take a moment to appear, so if the tools are still missing, ask them to wait a few seconds and reply **done** again before treating it as a failure.
e. **Verified:** confirm in one line ("Notion connected ✓") and move on.
f. **Still not working after a second try:** walk them through it plainly: finished signing in and clicked Allow; for Notion, gave access to the workspace (or pages) where the Business Brain should live; signed in with the account their business uses. Offer to wait again. If it still won't appear, for Notion ask them to start a **new** chat and send "Set up my AI team" again (setup resumes where it left off); for any other app, offer paste mode for now and tell them they can connect it later and say "finish my setup".

**Steps:**
1. **Quick check.** Load whatever Notion, Gmail, Google Calendar, Google Drive and Microsoft 365 tools exist (ToolSearch if deferred) and try the harmless reads above. Note what already works.
2. **Notion (required).** If it is not connected, run the connect loop. Notion cannot be skipped: it is where the team's Business Brain lives and every result is saved. If the owner wants to stop, tell them setup will pick up from here whenever they connect it (a free Notion account is fine), and end.
3. **Ask what they use.** If a Business Brain already exists with Connections filled in (setup restarted, or "finish my setup"), show those choices and ask only whether to change any; otherwise ask in one AskUserQuestion with three questions (pre-select nothing; mark an option "(connected)" if the quick check found it working):
   - "Which email do you use for your business?" Gmail or Google Workspace / Outlook or Microsoft 365 / Something else / I'd rather not connect my email
   - "Which calendar do you use?" Google Calendar / Outlook calendar / Something else or none / I'd rather not connect my calendar
   - "Where do you keep business documents?" Google Drive / OneDrive or SharePoint / Somewhere else or nowhere
4. **Connect each choice that isn't connected yet, one at a time** with the connect loop: Gmail, then Google Calendar, then Google Drive. Microsoft 365 is one connection that covers Outlook email, Outlook calendar and OneDrive, so connect it once. Skip any app already verified in step 1.
5. **Paste mode** for any "something else", "rather not" or app that wouldn't connect. Explain it once, warmly: "No problem. Your team still works. When you want help with emails or your schedule, paste them into your Paste Box page in Notion (or straight into the chat) and the team will triage them and write replies for you to copy into your own email." Microsoft 365 users: say once that replies will be ready to copy into Outlook, since the team can read Outlook but can't save drafts there.
6. **Remember the choices** (Email, Calendar, Files) and save them to the Connections section of Workforce Settings as soon as the Business Brain exists in Stage 2.
7. End the stage with a table: job (Business Brain, Email, Calendar, Files), app or "Paste mode" / "None", working yes/no, what the team will do with it.

## Stage 2: Build the Business Brain
1. Search Notion for a page titled "Business Brain".
   - **Found, with a Workforce Settings page and an Approvals database:** use it. Add the Paste Box page and the Connections section of Workforce Settings if either is missing (per `references/notion-schema.md` and `references/page-templates.md`); never change anything else. Then go to Stage 3.
   - **Found, older version** (has "Assignments log" or is missing the databases): upgrade it by adding only what is missing, per `references/notion-schema.md`. Never delete or overwrite.
   - **Not found:** ask: "Did your trainer give you a Business Brain template link that you already copied into Notion?" If yes, ask for the page's name or link and use it (renaming it to exactly "Business Brain" if needed). If no, create the full structure from `references/notion-schema.md` and `references/page-templates.md`: create the root page as a private page (draft mode), then the seven pages, then the five databases and their views.
2. Fill in the Connections section of Workforce Settings with the Stage 1 choices (add the section if an older Business Brain lacks it).
3. Tell the owner in one line where the Business Brain lives, with its link.

## Stage 3: Interview (fill the Brain)
Follow `references/interview.md` exactly. It lists 11 topics, the questions for each, and the exact Notion field every answer is saved to. Key rules:
- Every field in the Business Brain gets a question. Nothing is left `not set` unless the owner chooses to skip it.
- Propose answers from the website and the owner's connected apps where possible; the owner confirms or corrects.
- Save each topic to Notion **as soon as the owner confirms it**, then show a one-line progress note (`Saved: Policies (topic 5 of 11)`). Nothing waits until the end.
- Never invent prices, policies or facts.
- End with the completeness check in `references/interview.md` and offer to fill any important gaps.
- If setup is restarted, resume at the first topic with unanswered fields.

## Stage 4: Choose departments
Recommend departments from what the owner said (for example: no invoices → leave Finance off; no ads → Marketing optional). Ask with a multi-select AskUserQuestion, then tick the chosen boxes under "Active departments" in Workforce Settings.

## Stage 5: Self-test
Run the `workforce-self-test` skill. Show its table and explain any failure in one plain sentence with the fix.

## Stage 6: First real run and schedule
1. Offer to run the first daily briefing now (`daily-executive-briefing`, attended mode). This is the "it works" moment; do it if they say yes. On paste mode, first invite them to paste two or three real customer emails and today's key meetings into the Paste Box (or the chat), so the first briefing has something real to work on.
2. Offer to set up the schedule with the `schedule-workforce` skill.

## Finish
Close with: the Business Brain link; which departments are active; how email, calendar and files are handled (connected app or paste mode, and that they can connect an app any time and say "finish my setup"); what is still not set (top 3 gaps that matter most, from the completeness check); and the daily routine in one line ("each morning, read your briefing and say 'review my approvals'").
