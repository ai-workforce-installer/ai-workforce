# Tests

Run everything (no installs, standard Python 3.10+). GitHub Actions (`.github/workflows/ci.yml`) runs the first two on every push and pull request; `claude plugin validate` needs the Claude CLI and is run locally before each release:

```
python3 -m unittest discover tests
python3 tools/sync_references.py --check
claude plugin validate . && claude plugin validate plugins/ai-workforce
```

These are for the maintainer. Customers never run anything; their checks happen inside Claude with the `workforce-self-test` skill ("test the workforce").

## What each kind of test proves

| Test | What it runs | What it proves | What it does not prove |
|---|---|---|---|
| `test_plugin.py` | Reads the plugin files | Rules that fixed past failures are still written down and not contradicted: version consistency, the download matches the repo, references in sync, old "merge by date" and "guess from the clock" rules gone, inbox triage can't be replaced by customer-only triage, every scheduled prompt and fallback keeps the safety lines and a current version line, the Notion upgrade is add-only, no owner-specific details | That Claude follows the rules |
| `test_run_logic.py` + `run_logic.py` | A code model of the written run-tracking and inbox-bookmark rules, with fake mailboxes | The design itself is sound in the hard cases: two runs on one day, overlapping runs, interrupted runs resumed, pages that fail, 200+ emails over many pages, archived mail, the draft limit carrying work over, overlapping windows, long gaps, one notification per run. Mutation checks: breaking the bookmark or duplicate rules makes these tests fail | That Claude follows the rules, or how real Gmail paginates |
| `test_reliability.py` + `notion_logic.py` | A code model of the Notion-reading, counting, judgment and secrets rules, with a mocked Notion connection | Free-plan SQL allowance used up → views/filtered rows still read everything; databases with rows that error are "could not be verified", never "none"; views paged to the end; rows mode's 100-row cap reported as incomplete; complete vs incomplete approval queues; overlapping categories counted once and totals reconciled; secrets found and never repeated; hidden instructions produce no actions; only members with work launched; no draft for someone the owner meets soon; near-duplicate drafts consolidated; owner-only work marked Handed to you | That Claude follows the rules, or how the real Notion connection behaves on every plan |
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
