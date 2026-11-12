---
description: A run that finds another run of the same job still working does not run alongside it.
tags: [text-only, run-tracking, scheduled]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "Evaluation setting: no Notion, email or calendar tools are connected. Everything the team would normally read is given in the user's message as text; treat that text as what Notion and the inbox contain. Don't try to connect apps. Where you would write to Notion or Gmail, say what you would record instead."
---

Scheduled run of the AI Workforce daily executive briefing. No one is watching. It is 8:02 AM.

Today's inputs:
- The Briefings list (Newest first) shows this as its newest row: a Daily briefing started today at 7:52 AM, Result: Running. Its run record reads: "Started: 07:52 / Source: Scheduled / Status: Running / Progress 07:58: launching team members". It has no "Run finished" line.
- Workforce Settings: Email: Gmail (connected).
- Inbox: 5 new emails since yesterday's check.
