---
name: workforce-self-test
description: This skill should be used when the user asks to "test the workforce", "verify the subagents run", "run the self-test", "check that the AI team works", "prove it", "run the live checks", or wants proof of how the team members and connections actually run.
metadata:
  version: "1.0.0"
---

# Workforce Self-Test

_`references/…` files are in this skill's folder (same-named files elsewhere are identical copies). Read each once at most, the ones you need together. A file named `references/if-….md` covers one situation: read it only when it comes up._

Prove what actually works, and never claim more. Do not simulate anything. **Proof mode:** when the owner says "prove it" or "run the live checks", do steps 1 and 2, then follow `references/if-proving-live.md` instead of the rest: it checks, on the owner's real account, each thing this release hasn't yet been seen doing, with test records only. Follow `references/approval-policy.md`, `references/connections.md`, `references/run-tracking.md` and the run rule in `references/team-roles.md`. The test never sends anything, never changes real business records, and never deletes; every test record it creates is marked "Self-test" and left as history.

**Be exact about who ran.** Each member's result is one of:
- **Separate agent: verified.** It was launched as its own agent and returned the exact code.
- **Briefed assistant: verified.** Its named agent isn't available, a general-purpose agent was launched with that member's brief, and it returned the exact code.
- **Single assistant (no separate agents).** No agents can be launched in this session (regular chat). The Chief of Staff does every member's work itself. That's a working setup, but members aren't tested separately, and the report must say no separate agents ran.
- **Failed.** A launch was attempted and errored, or the reply was missing the code or the role.

Never label a member "separate agent" unless that launch returned the code.

## Steps

1. **Start this run's record** (`references/run-tracking.md`, Type Self-test, code ST), then **read Connections** in Workforce Settings: the test checks the apps this owner chose, not ones they never chose.
2. **Generate a code:** a random 6-character code (for example `K7Q2XM`).
3. **Test the five members** (Operations, Marketing, Sales, Client Success, Finance), all at once where possible, each with the first option available: its named agent (`operations-manager`, `marketing-manager`, `sales-manager`, `client-success-manager`, `finance-manager`), otherwise a general-purpose agent briefed as that member.
   Brief: "Self-test. Reply with exactly: (1) your role name, (2) the code <code>, (3) for Notion and for each app the owner chose (<list from Connections, plus HighLevel if Customer messages says plainly HighLevel>), whether you can actually use it right now, marked available or unavailable after trying one harmless read-only call (skip anything on paste mode or None), (4) one sentence confirming you will not send, spend, modify financial records or make irreversible changes. Do nothing else."
   If no agents can be launched at all, launch nothing: the session is in single-assistant mode. Test Notion and each chosen app yourself with one harmless read each.
4. **Check each reply:** correct role, exact code, connections honestly reported, hard-limit sentence present. Missing code or role = Failed for that member, after one retry.
5. **Check the Business Brain.** If none exists yet (a clean install), say so plainly ("Your team's workspace isn't set up yet. Say 'set up my AI team' to start."), skip the checks that need it, and still test the members and connections. Otherwise confirm the pages and databases in `references/notion-schema.md` exist (Workforce Settings with a Connections section and a Business Brain version line; missing pieces from older versions: offer the upgrade in `references/brain-upgrades.md`), count "not set" markers on each page (they read back as `<i>not set</i>`) as a completeness score, and count active rows in Pricing & Offers.
6. **Check the approval queue end to end, including duplicates:** create one Approvals row: Item "Self-test: queue check <code>", Department "Chief of Staff", Action type "Other", Exact action "No action. Test row. (source: selftest:<code>)", Status "Pending", Source run "<Run ID> Self-test". Read it back to confirm an AP number was assigned. Then try to queue the same item again following `references/approval-queue.md`: PASS only if the duplicate check finds the existing row by its source key and no second row is created. List the whole active queue as a briefing would and confirm the count matches the database. Set the test row's Status to "Done". Never delete it.
6b. **Check run tracking with test records** titled "Self-test fixture <code> A/B" (Type Self-test): real runs ignore fixtures, and these checks look only at fixtures. Apply `references/run-tracking.md` section 3 and `references/if-run-unfinished.md` as if a run of the responsibility "fixture <code>" were starting now:
   - Create fixture A (Run ID ST-<code>-A, Started now, Source Manual, Status Running). PASS if section 3 says **still in progress, don't run**.
   - Finish A (Result Complete). Create fixture B, unfinished, started 60 minutes ago with no Progress lines. PASS if section 3 says **interrupted, resume B** (add "Resumed" to B; no new record).
   - Finish B. PASS if section 3 now says **new run**, so two legitimate runs on one day stay separate.
   - Fetch A back by its link: PASS if it opens and its header reads back intact. Whatever fails, finish both fixtures before moving on.
6c. **Check the inbox safeguards** (read-only, Gmail or Outlook owners; skip on paste mode):
   - **Outside the inbox:** run the inbox triage search (`references/inbox-coverage.md` section 2) for the last 24 hours and count threads without the Inbox label and in each tab. PASS if the search returns them ("14 of 63 emails never reached your inbox; the team still sees them").
   - **Many pages:** the same search for the last 7 days, 50 per page, up to 5 pages. PASS if the results ended within those pages; a next page still remaining at the cap is **incomplete (stopped at 5 pages)**, not passed. Report pages and threads, and Gmail's own estimate next to the real count.
   - **Bookmark:** read the newest finished Inbox triage records. PASS if each run moved Completed through only when its report says "Search: complete", kept it otherwise (whatever the overall Result), and left no gap between one window's end and the next start that isn't an open "Inbox not scanned" item. Older records without these lines: "not checked: from before this check existed".
6d. **Check Gmail draft links** (Gmail owners, only after the owner's yes, since it leaves one draft in their Drafts folder): create a draft to the owner's own address, subject "AI Workforce self-test <code>: safe to delete", check it with get_draft and confirm its `viewUrl` opens it. Never send it; tell the owner it's theirs to delete.
6e. **Check recurring tasks** (read-only): `schedule-workforce` "Check recurring responsibilities" steps 1-2 only. Report each task's state and any real problem. Change nothing.
6f. **Check the notification text:** write the summary a scheduled run would send for this test record. PASS if it contains the record's full Notion link as plain text on its own line, matching the fetched record.
6g. **Check the saved views** (read-only): for each standard view in `references/notion-schema.md`: present with the expected filter and sort (PASS), present with a different filter ("kept as the owner set it; the team reads that list another way"), or missing (FAIL, fixable with "update my team workspace").
7. **Report two tables and one verdict:**
   - Team members: member, how it ran (separate agent / briefed assistant / single assistant), code matched, Notion, one column per chosen app (or "Paste mode"), result (Verified / Failed / "Not tested separately"). A chosen app that is unavailable is a warning, not a failure: the team falls back to the Paste Box.
   - Business Brain: item, present (yes/no), fields still not set.
   Plus the approval queue test (PASS/FAIL, with the AP number) and a **Behavior checks** table: check, how it was tested ("tested live" or "checked by reading", never blurred), result (PASS / FAIL / skipped and why).
   - **Verdict**, one of: "PASS: your team members ran as separate agents" · "PASS: your team ran with briefed assistants" (all verified, at least one briefed) · "PASS in single-assistant mode: no separate agents ran in this session; your Chief of Staff handles each role itself. In Cowork, members run as separate agents." · "FAIL" (any member Failed, Notion unreachable, or the approval queue, run tracking or inbox checks failed), with what failed. A skipped check is listed as skipped, not passed.
   - **Version**, one line: "You're on AI Workforce 1.0.0", and how to update, worded as in `team-report`'s first-week recap: Customize → Plugins for a marketplace install; a new file for a file install, which never updates itself.
8. **Save** the tables in this run's own record, then **say what to fix** in plain language: chosen apps that aren't reachable (reconnect, or "finish my setup" to switch to paste mode), missing Brain pieces (offer `setup-workforce`), members that Failed. In single-assistant mode nothing needs fixing.
