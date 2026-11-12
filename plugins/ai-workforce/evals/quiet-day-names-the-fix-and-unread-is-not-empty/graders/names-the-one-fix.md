---
type: llm
focus: mock_calls
---

You are shown the calls a test run made to stand-in tools (tool, input, answer). This is an unattended morning run on a day with nothing to prepare. The owner has said their customer and lead messages reach them in a CRM or help desk, which is not connected. Look at the briefing text the run saved to Notion (the content of its notion-create-pages or notion-update-page calls).
PASS if that saved briefing points to this (messages or leads living in a CRM or help desk the team can't read) and gives one step that would fix it, such as connecting it, forwarding those messages to the connected inbox, or pasting them in.
FAIL if the saved briefing does not mention it, or gives no step.
