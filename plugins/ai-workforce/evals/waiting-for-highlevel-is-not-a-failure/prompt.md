---
description: An owner who said yes to HighLevel but hasn't connected it yet gets a normal run; nothing is reported unavailable or partly done because of it.
tags: [text-only, scheduled, highlevel]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "Evaluation setting: no Notion, email or calendar tools are connected. Everything the team would normally read is given in the user's message as text; treat that text as what Notion and the inbox contain. Don't try to connect apps. Where you would write to Notion or Gmail, say what you would record instead."
---

Scheduled run of the AI Workforce daily executive briefing. No one is watching.

Today's inputs:
- Workforce Settings: Email: Gmail (connected). Customer messages: not set (HighLevel wanted, not connected yet). No HighLevel tools exist in this session.
- The last inbox check finished yesterday at 8:05 AM; none has run since.
- Inbox since then, 2 emails:
  1. From Dana (a client): "Can you send me the updated proposal before Thursday?"
  2. A newsletter from a software vendor.
- Calendar today and tomorrow: nothing with other people.
- Approvals: none open. Open work: none.
