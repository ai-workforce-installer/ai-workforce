---
description: Asked to connect HighLevel with no sign-in or card on offer, the owner gets the four short steps and the address, and nothing is called connected.
tags: [text-only, setup, highlevel]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "Evaluation setting: no Notion, email, calendar or HighLevel tools are connected and there is no connector registry to search, so treat a HighLevel lookup as 'no such tool' and a registry search as 'no card for HighLevel'. Everything the team would normally read is given in the user's message as text; treat that text as what Notion contains. Don't try to connect apps. Where you would write to Notion, say what you would record instead."
---

Connect HighLevel.

My Business Brain is already set up: Workforce Settings shows Business Brain version 0.8.1 and the team has finished several runs. Its Connections section says:
- Email: Gmail
- Calendar: Google Calendar
- Files: Google Drive
- Customer messages: not set
