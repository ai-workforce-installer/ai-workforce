# Tests

Run everything (no installs, standard Python 3.10+). GitHub Actions (`.github/workflows/ci.yml`) runs the first three on every push and pull request; `claude plugin validate` needs the Claude CLI and is run locally before each release:

```
python3 -m unittest discover tests
python3 tools/sync_references.py --check
python3 tools/prompt_history.py --check
claude plugin validate . && claude plugin validate plugins/ai-workforce
```

Build the download after any change inside `plugins/ai-workforce` (evals stay out of it):

```
rm download/ai-workforce.plugin && (cd plugins/ai-workforce && zip -qr ../../download/ai-workforce.plugin . -x "*.DS_Store" "evals/*")
```

## Behaviour evals (real Claude runs)

`plugins/ai-workforce/evals/` holds cases that run the plugin in real Claude sessions and grade what Claude actually does: an "ok thanks" approves nothing, an ambiguous number is asked about, instructions inside an email aren't followed, secrets aren't repeated, a dismissed alert stays quiet while a new security alert surfaces, a missing price is asked for rather than invented, a scheduled run drafts but never sends or pays, and financial records aren't edited. No Notion or Gmail is connected: each case gives the inputs as text. They use your Claude login or API key and cost real usage (about $0.40 for one run of each case; the default is 3 runs each), so they aren't in CI. Run them before each release:

```
cd plugins/ai-workforce && claude plugin eval . --trust-plugin --ablation none --no-publish --max-cost-usd 5
```

While working on one case: `claude plugin eval . --case <name> --runs 1 --ablation none --no-publish --trust-plugin`. Prefer judge (`type: llm`) graders with concrete PASS/FAIL wording; regex checks on wording misfire on replies like "nothing has been sent".

These are for the maintainer. Customers never run anything; their checks happen inside Claude with the `workforce-self-test` skill ("test the workforce").

## What each kind of test proves

Three kinds, never to be confused: **source checks** (the rules are written down), **reference-model tests** (the written design, restated as code, survives hard cases) and **real Claude runs** (Claude actually does it). Only the last kind shows Claude following the rules, and only the live self-test and the acceptance checklist below are that kind.

| Test | What it runs | What it proves | What it does not prove |
|---|---|---|---|
| `test_plugin.py` | Reads the plugin files | Rules that fixed past failures are still written down and not contradicted: version consistency, the download matches the repo, references in sync, old "merge by date" and "guess from the clock" rules gone, inbox triage can't be replaced by customer-only triage, every scheduled prompt and fallback keeps the safety lines and a current version line, the Notion upgrade is add-only, no owner-specific details | That Claude follows the rules |
| `test_run_logic.py` + `run_logic.py` | A code model of the written run-tracking and inbox-bookmark rules, with fake mailboxes | The design itself is sound in the hard cases: two runs on one day, overlapping runs, interrupted runs resumed, pages that fail, 200+ emails over many pages, archived mail, the draft limit carrying work over, overlapping windows, long gaps saved as an "Inbox not scanned" row and caught up 2 days per run with nothing missed or duplicated, a failed catch-up leaving the row unchanged, owner backfill covering the requested period, missed notifications caught up within 8 days without redoing work (including a weekly report; pending, explicit failure, at most 3 attempts, permanent failures never retried, unknown outcomes retried once with a duplicate warning), two sessions starting in the same minute (both look before either writes) leaving one working after the look-again step, and an immediate retry creating no duplicate work (best effort: there is no atomic lock; the duplicate checks are the backstop), the bookmark following email search coverage rather than the overall Result (a Partial run with a complete search moves it; an incomplete search keeps it; work left over when the queue was unreadable is carried over and done by the next run), the self-test's bookmark and 5-page pagination checks, one notification per run. Mutation checks: breaking the bookmark or duplicate rules makes these tests fail | That Claude follows the rules, or how real Gmail paginates |
| `test_reliability.py` + `notion_logic.py` | A code model of the Notion-reading, counting, judgment and secrets rules, with a mocked Notion connection | Free-plan SQL allowance used up → saved views still read everything, and filtered rows are treated as possibly rationed too (a used-up filtered read is "could not be verified", never "none"); databases with rows that error are "could not be verified", never "none"; views paged to the end; rows mode's 100-row cap reported as incomplete; complete vs incomplete approval queues; overlapping categories counted once and totals reconciled; secrets found and never repeated; hidden instructions produce no actions; only members with work launched; no draft for someone the owner meets soon; near-duplicate drafts consolidated; owner-only work marked Handed to you; recurring-task updates: backup write, read-back and truncation failures block the change, an owner edit between inspection and change stops it, a failed verification read is never success, a corrupted setting is reported as "instructions back, setting changed" and not silently fixed, a failed restore is "not confirmed", task markers matched only on the first line, owner's additions kept and a truncated save rejected, paused stays paused, next run, schedule and time zone must be unchanged; the update plan matches tasks only by their first-line tag and waits for a needed connection; workspace setup and repair: older workspaces run their upgrade sections before the version moves, failed view creation stays "setup in progress", interrupted setup resumes without duplicates, repair works when the version already looks current, repeated repair changes nothing, a same-named owner view is kept and reported, the self-test views check | That Claude follows the rules, or how the real Notion connection behaves on every plan |
| `test_learning.py` + `learning_logic.py` (and the quick look in `run_logic.py`) | A code model of the 0.6.0 learning rules, with a mock Business Brain whose Priorities page is plain text | A dismissed legacy alert isn't raised again when more emails about it arrive, and isn't recreated; a new security incident that resembles it still surfaces (with a note), while the repeat failure stays hidden; a rule is as narrow as the owner said ("except …"); corrections are re-read from the page in a later run, so they persist; unconfirmed or scheduled corrections save nothing; temporary rules expire and taken-back rules are marked, never deleted; older workspaces save under Things to ignore; already-handled items leave the active queue but stay as history, and the owner's own rows are untouched; plain-language replies map to the right items (the six from the live test), acknowledgements are never permission, ambiguous replies cause no action, a number that could mean two items is asked, investigation creates one task; two Business Brains: attended asks, scheduled touches neither, the chosen one alone gets records; a quick look never moves the inbox bookmark or claims all email, and the full review afterwards drafts nothing twice; website prices and policies don't become confirmed; answered questions aren't asked again; writing preferences apply to later drafts, unsaved feedback only to this one, no sign-off is invented; placeholders, invented proof, unknown links and "Link needed" block Ready; repeating the team meeting or setup creates one recurring task per job. Mutation checks: disabling the security exception, the confirmation step, the bookmark rule, the acknowledgement rule or the two-Brains stop makes these tests fail | That Claude follows the rules, or how well Claude matches a real email to a saved correction (the model matches by name; Claude judges meaning) |
| `workforce-self-test` skill (live, in Claude) | Real Notion, Gmail and agents on the owner's account, with test records only | Agents vs. fallback mode, connections, approval queue and duplicate check, run records and retry rules on Self-test records, mail outside the inbox and pagination on the real mailbox, the inbox bookmark history, Gmail draft links (with the owner's OK), recurring tasks current, notification link | Long-term behaviour across days |

## Still needs a real Claude account

Each of these has to be watched on a real account; nothing in this folder can do it:
1. **A real scheduled firing** of each recurring task after updating to 0.5.0: record created at start, Source shown honestly, finished record, one notification with the right link.
2. **"Run now" on a recurring task** close to its scheduled time: labelled "started from your recurring task", not guessed.
3. **A real interrupted run** (for example a session that runs out of usage midway), then the next run finishing it without duplicate drafts or approvals.
4. **Two inbox runs on the same day** on the real mailbox: two records, the second window starting 15 minutes before the first one's bookmark.
5. **An outdated recurring task** (an old prompt) running against 0.5.0: configuration warning, correct job done.
6. **The Business Brain upgrade to 0.5.0** on an existing workspace: new Briefings fields added, nothing changed or lost.
7. **Gmail draft links** opening the right draft on desktop and phone.
8. **Regular chat (single-assistant mode)** running the same skills with the same safeguards.
9. **Notion Free plan behaviour** of saved views and filtered rows (whether they're also rationed, and how the connection reports a used-up allowance), and that a run with Notion partly unreachable says "could not be verified" and finishes as Partial.
10. **Usage per run** on a real account (tool calls, team members started, time) for each recurring task, before saying anything about which Claude plan is enough.
11. **The 0.5.1 and 0.5.2 workspace upgrades** on an existing Business Brain, each run twice to confirm they're safe to repeat, and that the new saved views keep working after the Free plan's query allowance runs out.
12. **A recurring task started with Run now on an unusual day**: no duplicate-schedule warning, Source "Unknown (started from a recurring task)", the right job done.
13. **What the notification tool actually returns** (whether it ever confirms delivery), so the Notified line matches it.
15. **A recurring task updating itself**: after a plugin update, the next run of an outdated standard task changes only its prompt (time, on/off, notifications and approval setting unchanged), says so in its report, and the run after it shows no configuration warning. This depends on the scheduling tools being available inside a scheduled session, which hasn't been confirmed yet.
14. **Weekly marketing with no ad export available**: Partial, past metrics Unavailable, a usable plan, and the exact export request.

## Live acceptance checklist for 0.6.0

On a test Claude account and a test Notion workspace (never the live business workspace or its recurring tasks). No full inbox reviews are needed for items 2-6; use a quiet test mailbox.
1. **A correction that sticks.** Let a run raise an alert you don't care about (for example an automation for a business you no longer run). Reply "that isn't my responsibility anymore". Expect: one confirmation quoting the exact line and the related AP numbers; after yes, the line on Priorities under "Not my responsibility anymore", the items Rejected with your words (still in Approvals), and the next run (ideally a real scheduled one, after another email about it arrives) showing it only in the "Not raised" count.
2. **The exception.** Send the test mailbox a new sign-in or password-reset email mentioning the same business. Expect it raised once, with a line naming the rule it would otherwise have matched.
3. **Six replies in one message.** With six pending items on screen, reply in plain words as in the live test ("One isn't my problem. Two is fine. Look into three. Decline those invitations. I already checked five."). Expect: no send or decline for "fine" without a short check, an Assignments row for three, five Done with your words, a question about anything ambiguous, and nothing else acted on.
4. **Quick-look first job on a fresh account.** Run setup on a mailbox with 200+ threads in the last day. Time from "Set up my AI team" to the first result; expect the quick-look wording, the record's "Completed through: not moved (quick look)", and the next full inbox check starting as a first run without redrafting.
5. **Two Business Brains.** Duplicate the test Business Brain (both titled "Business Brain"), then say "Set up my AI team" and let a recurring task fire. Expect a reuse-or-start-fresh question in chat, and the recurring run writing to neither and saying why.
6. **Draft feedback.** Ask Marketing for an email, reply "too formal, and I wouldn't sign it with my name", say yes to saving it, then ask for another email. Expect the same draft fixed (no new approval), Brand & Tone updated, and the second email following it.
7. **Upgrade an existing 0.5.x workspace** with "update my team workspace", twice. Expect two new headings on Priorities, the version 0.6.0, nothing else changed, and nothing added the second time.

## Live acceptance checklist for 0.5.4

Run on a test Claude account and a test Notion workspace, never on a live business workspace or its recurring tasks. Record what you saw for each item, with links.
1. **Clean install to a useful first assignment, with failed-view repair.** Install from the marketplace (README). Say "Set up my AI team" and finish setup. Before the first assignment, delete one standard saved view (for example Open work) in Notion. Then check Workforce Settings still shows the right version only after "update my team workspace" adds the view back. Repeat the command: nothing added twice, your own views untouched.
2. **A genuine scheduled firing with an automatic prompt upgrade.** Create a standard recurring task from an older released prompt (0.5.4 text from `tools/released-prompts.md`), note every setting (schedule, time zone, on/off, notifications, model, approval), and let it fire on schedule (not Run now). Expect: a backup in that run's record, the instructions now the 0.7.0 template, every setting unchanged, and the report line "now uses the current instructions".
3. **Customized and paused tasks.** Add a sentence to one test task's instructions and pause another. Let a run happen, then say "update my recurring tasks". Expect: the customized task left alone automatically and updated in chat only with your OK, its sentence under "Owner's additions"; the paused task still paused after updating.
4. **Interrupted-run recovery and two same-day inbox runs.** Stop an inbox run midway (close the session), then run it again more than 45 minutes later: the old record is finished, not duplicated. Run inbox triage twice in one day: two records, the second window starting 15 minutes before the first one's bookmark, no duplicate drafts, approvals or Assignments rows.
5. **Notification recovery.** Interrupt a run right after its record shows "Run finished" but before the Notified line changes (or use a session without a notification tool). The next run of the same job should include the older link, add an attempt line to the older record, and record "accepted by the tool" rather than "delivered" unless the tool confirms delivery.
6. **Typical-day usage and saved views after Notion's allowance runs out.** On the intended customer plan, run a normal day (briefing plus one inbox triage) and record each run's Usage line and how much of the plan's allowance it used. On a day the Notion free plan's query allowance has run out, ask "what's waiting for my approval?": answered through the Active approvals view, or "could not be verified", never "nothing waiting" when items exist.

## Live check: the 0.5.2 saved-view upgrade on an existing Free workspace

About 10 minutes; changes nothing except adding views and two lines in Workforce Settings.
1. In Notion, note the views each Business Brain database has today (Approvals, Assignments, Briefings, Pricing & Offers, Customers & Leads).
2. In a new Claude chat, say **"update my team workspace"** and approve the upgrade.
3. Check in Notion: each database now has its standard view (Active approvals, Open work, Newest first, Active offers, All contacts), every view you had before is still there and unchanged, no records changed, and Workforce Settings shows `Business Brain version: 0.5.2` and `Recurring tasks update themselves: yes`.
4. Open each new view and confirm it shows what its name says (for example Active offers shows only offers with Active ticked).
5. Run **"update my team workspace"** again: it should report nothing to add and create no second copies.
6. After the free plan's query allowance has run out (any busy day), say **"what's waiting for my approval?"**: the list should come back through the Active approvals view, or say it "could not be verified", never "nothing waiting" when items exist.

## Live check: clean-account beginner install

Use a Claude account and Notion workspace that have never seen AI Workforce. Time it and note every question you had to think about.
1. Install from the marketplace link in the README.
2. New chat: "Set up my AI team. My website is …" (try once with no website too).
3. Connect Notion when asked; try skipping email to confirm paste mode works.
4. Confirm the Business Brain appears in Notion with its pages, databases and views.
5. Answer the website summary check and the one "what takes too much time" question.
6. Watch the first assignment finish, with a link to its result.
7. Say yes to one recurring task; confirm the one-sentence note about automatic updates appears and the task shows up in your scheduled tasks.
8. Record: total time, Claude usage shown by the app, any step that was confusing or failed.
