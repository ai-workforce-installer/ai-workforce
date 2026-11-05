# Page templates (Notion-flavored Markdown)
Use each block as the page's starting content. Every `_not set_` marker is a field the setup interview fills in. Notion stores the marker as italic, so when you fetch a page it reads back as `<i>not set</i>`: fetch the page first, then replace the whole line including its label (e.g. `- Name: <i>not set</i>`), or the heading plus marker for paragraph fields, because the bare marker appears many times. Leave a marker in place if the owner skips that question.

## Start here (top of the Business Brain page)

````markdown
<callout icon="👋" color="blue_bg">
**This is your AI team's shared memory.** Every member of your AI team reads these pages before doing any work, and your Chief of Staff saves the team's results here. The more accurate this page is, the better your team performs.
</callout>

## Your 15-minute daily routine

1. Read today's briefing in **Briefings**.
2. Open **Approvals** and look at everything marked Pending.
3. In Claude, say **"review my approvals"** and approve or reject each one by its AP number.

## Ground rules your team follows

- Never sends an email or message without your yes. Replies are saved as drafts for you to send: in Gmail if it is connected, otherwise in your briefing, ready to copy into your own email.
- Never spends money or changes ad budgets.
- Never creates, edits or deletes invoices or financial records.
- Never books calendar events with other people without your yes.
- Never deletes anything.
- Anything outside these rules goes to **Approvals** and waits for you.
````

## Workforce Settings

````markdown
## Owner

- Name: _not set_
- Business email: _not set_
- Time zone: _not set_
- Working hours: _not set_

## Connections

- Email: _not set_
- Calendar: _not set_
- Files: _not set_

## Active departments

- [ ] Operations
- [ ] Marketing
- [ ] Sales
- [ ] Client Success
- [ ] Finance

## Schedule

- Daily briefing: _not set_
- Inbox triage: _not set_
- Weekly marketing plan: _not set_
- Invoice review: _not set_

## Where things live

- Customer email inbox: _not set_
- Invoices are kept in: _not set_
- Marketing performance data: _not set_

## Extra rules for my team

- _none yet_

## About this workspace

- Business Brain version: 0.5.2
````

## Company Profile

````markdown
## What we do

_not set_

## Who we serve

_not set_

## Main products and services

_not set_ (details and prices go in Pricing & Offers)

## What makes us different

_not set_

## Website and key links

_not set_

## Team (humans)

_not set_
````

## Priorities

````markdown
## This quarter's goals

1. _not set_
2. _not set_
3. _not set_

## This month's focus

- _not set_

## Things to ignore for now

- _not set_

## Work I'd like to hand off

- _not set_
````

## Policies

````markdown
## Refunds

_not set_

## Discounts

_not set_

## Response times

_not set_

## Payment terms

_not set_

## Cancellations

_not set_

## Always escalate to me

- Legal threats, chargebacks, press, or anything that feels off
````

## Brand & Tone

````markdown
## Our voice in three words

_not set_

## Words and phrases we use

- _not set_

## Words and phrases we never use

- _not set_

## How I sign off

_not set_

## Example of an email that sounds like me

_paste one here_
````

## Paste Box

````markdown
<callout icon="📥" color="gray_bg">
Paste anything you want your team to handle: customer emails, forwarded messages, this week's meetings and deadlines. Your team checks this page on every run. You don't need any special format.
</callout>

## Emails to handle

_Paste each email here: who it's from, the subject, and the message._

## Upcoming schedule

_Add key meetings, calls and deadlines: date, time, what it is._

## Handled

_Your team moves emails here after writing a reply._
````

## Your Team

````markdown
<callout icon="👥" color="gray_bg">
Your team members and how you want each of them to work. Tell your Chief of Staff things like "from now on, keep customer replies short and friendly" and it's saved here. You can also edit this page yourself.
</callout>

## How each team member should work

### Operations

- _none yet_

### Marketing

- _none yet_

### Sales

- _none yet_

### Client Success

- _none yet_

### Finance

- _none yet_

## Custom team members

_None yet. Ask your Chief of Staff "do we need another person for this?"_

## Suggestions from your Chief of Staff

_Ideas for work the team could take off your plate. Your Chief of Staff adds one at most once a week and never repeats one you declined._
````

## FAQs

````markdown
## Answered

_Add questions as Q/A pairs._

## Waiting for an answer from you

_The team adds new questions here._
````
