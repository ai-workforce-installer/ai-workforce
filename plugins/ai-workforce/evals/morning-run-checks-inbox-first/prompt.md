---
description: The daily briefing goes through the inbox itself, in the same run, and reports once, opening with what was handled.
tags: [morning-run, scheduled]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "Evaluation setting: no Notion, email or calendar tools are connected. Everything the team would normally read is given in the user's message as text; treat that text as what Notion and the inbox contain. Don't try to connect apps. Where you would write to Notion or Gmail, say what you would record instead."
---

Scheduled run of the AI Workforce daily executive briefing. No one is watching.

Today's inputs:
- Workforce Settings: Email: Gmail (connected). The last inbox check finished yesterday at 8:05 AM; none has run since.
- Inbox since then, 3 emails:
  1. From Dana (a client): "Can you send me the updated proposal before Thursday?"
  2. A newsletter from a software vendor.
  3. From the bank: "Your statement is ready to view."
- Calendar today and tomorrow: nothing with other people.
- Approvals: none open. Open work: none.
