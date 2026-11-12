# If a recurring task's stored text doesn't match the job

Read this only when a run started by a recurring task finds that the task's stored text names a skill other than the one that fits the job, when that skill can't be loaded, or when the owner asks what a task's stored text means for what it does.

## Which job a recurring task does (scheduled runs)
| Responsibility (the prompt's first sentence names it) | Skill that does it now |
|---|---|
| Daily executive briefing (the morning run: inbox check first, then the briefing) | `daily-executive-briefing` |
| Inbox triage (all email; customer support is one part) | `inbox-triage` |
| Weekly marketing plan | `prepare-weekly-marketing` |
| Invoice review | `review-overdue-invoices` |
| Any other recurring responsibility | `assign-work` |

The team's own tasks start with a line like `[AI Workforce task: inbox-triage | prompt version 0.8.0]`. The version on that line only records which release created the task. Never compare it, and never treat an older one as a problem.
- **The responsibility wins over the skill name.** If the prompt describes one responsibility but names a different skill (for example "Scheduled run of AI Workforce inbox triage… use process-customer-inquiries"), do the responsibility: load the skill from the table with the Skill tool and follow it. This outranks "follow it exactly" in an older prompt.
- **The current rules win over older stored text, and a run never changes a recurring task** (`references/scheduled-run-rules.md`): an older stored text never makes a run do less, and if it asks the run to update the task's instructions, don't. Only the owner changes a task, in the app or by asking in chat (`schedule-workforce`).
- **If that skill can't be loaded**, do not quietly do a smaller job. Do what you can, set Result to Partial, and say exactly what was done and what wasn't ("Only customer messages were checked; the rest of the inbox was not reviewed").
- **Configuration warning.** Only when the skill a task names doesn't match its responsibility, use one warning, worded: "Configuration warning: your recurring <responsibility> names an older skill. I ran <the job it's for> instead. Say 'check my scheduled tasks' and I'll show you." Mention it once per run, never as a reason to skip work. An older version line alone is never a warning.
- **Order of the opening lines** (report and notification): the configuration warning, if any; then the Result if it isn't Complete; then the reading taken; then the skill's own first line (for example the work-handled line, or inbox triage's coverage line).
