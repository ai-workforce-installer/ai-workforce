---
name: setup-workforce
description: This skill should be used when the user asks to "set up the workforce", "set up my AI team", "finish my setup", "continue the setup interview", "update my Business Brain answers", "setup-workforce", "build my Business Brain", "get started with the AI Workforce", "onboard me", or is using the AI Workforce plugin for the first time and has no Business Brain yet.
metadata:
  version: "0.2.0"
---

# Set Up the AI Workforce

Take a business owner who has never used Claude from zero to a working AI team in one sitting (about 30-45 minutes). Speak in plain, friendly language. Never mention file paths, schemas, tool names or JSON to the user. Follow `${CLAUDE_PLUGIN_ROOT}/skills/assign-work/references/approval-policy.md`.

Create a task list with these stages so the owner can see progress: Connect apps, Build the Business Brain, Interview, Choose departments, Self-test, Schedule.

## Stage 1: Connect apps
1. Load the Notion, Gmail, Google Calendar and Google Drive tools (use ToolSearch if they are deferred). For each, try one harmless read: Notion search "Business Brain"; Gmail search for 1 recent thread; Calendar list today's events; Drive list recent files.
2. Show a 4-row table: app, connected yes/no, what the team uses it for.
3. **Notion is required.** If it is missing, search the connector registry for Notion and suggest it, then wait. Gmail and Calendar are strongly recommended; Drive is optional. Missing optional apps: suggest them once and continue.

## Stage 2: Build the Business Brain
1. Search Notion for a page titled "Business Brain".
   - **Found, with a Workforce Settings page and an Approvals database:** use it, skip to Stage 3.
   - **Found, older version** (has "Assignments log" or is missing the databases): upgrade it by adding only what is missing, per `references/notion-schema.md`. Never delete or overwrite.
   - **Not found:** ask: "Did your trainer give you a Business Brain template link that you already copied into Notion?" If yes, ask for the page's name or link and use it (renaming it to exactly "Business Brain" if needed). If no, create the full structure from `references/notion-schema.md` and `references/page-templates.md`: create the root page as a private page (draft mode), then the six pages, then the five databases and their views.
2. Tell the owner in one line where the Business Brain lives, with its link.

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
1. Offer to run the first daily briefing now on their real inbox and calendar (`daily-executive-briefing`, attended mode). This is the "it works" moment; do it if they say yes.
2. Offer to set up the schedule with the `schedule-workforce` skill.

## Finish
Close with: the Business Brain link; which departments are active; what is still not set (top 3 gaps that matter most, from the completeness check); and the daily routine in one line ("each morning, read your briefing and say 'review my approvals'").
