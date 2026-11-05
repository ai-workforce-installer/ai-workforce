---
name: workforce-self-test
description: This skill should be used when the user asks to "test the workforce", "verify the subagents run", "run the self-test", "check that the AI team works", or wants proof of how the team members and connections actually run.
metadata:
  version: "0.5.2"
---

# Workforce Self-Test

_Files named `references/…` are in this skill's own folder._

Prove what actually works, and never claim more. Do not simulate anything. Follow `references/approval-policy.md`, `references/connections.md`, `references/run-tracking.md` and the run rule in `references/team-roles.md`. The test never sends anything, never changes real business records, and never deletes; every test record it creates is marked "Self-test" and left as history.

**Be exact about who ran.** Each member's result is one of:
- **Separate agent: verified.** It was launched as its own agent and returned the exact code.
- **Briefed assistant: verified.** Its named agent isn't available, a general-purpose agent was launched with that member's brief, and it returned the exact code.
- **Single assistant (no separate agents).** No agents can be launched in this session (regular chat). The Chief of Staff does every member's work itself. That's a working setup, but members aren't tested separately, and the report must say no separate agents ran.
- **Failed.** A launch was attempted and errored, or the reply was missing the code or the role.

Never label a member "separate agent" unless that launch returned the code.

## Steps

1. **Start this run's record** (`references/run-tracking.md`, Type Self-test, code ST), then **read Connections** in Workforce Settings so you know which apps this owner chose (Gmail / Outlook / Paste mode, and so on). The test checks those apps, not apps the owner never chose.
2. **Generate a code.** Create a random 6-character code (for example `K7Q2XM`) and keep it.
3. **Test the five members** (Operations, Marketing, Sales, Client Success, Finance), all at once where possible. For each, use the first option that is available:
   - The named agent (`operations-manager`, `marketing-manager`, `sales-manager`, `client-success-manager`, `finance-manager`), or, if the named agents aren't available,
   - a general-purpose agent briefed as that member.
   Brief: "Self-test. Reply with exactly: (1) your role name, (2) the code <code>, (3) for Notion and for each app the owner chose (<list from Connections, e.g. Gmail, Google Calendar, Google Drive, or Microsoft 365>), whether you can actually use it right now, marked available or unavailable after trying one harmless read-only call (skip anything on paste mode or None), (4) one sentence confirming you will not send, spend, modify financial records or make irreversible changes. Do nothing else."
   If no agents can be launched at all, don't launch anything: the session is in single-assistant mode. Test Notion and each chosen app yourself with one harmless read each.
4. **Check each reply:** correct role, exact code echoed, connections honestly reported, hard-limit sentence present. Missing code or role = Failed for that member. If one launch fails, retry that member once before marking it Failed.
5. **Check the Business Brain.** If none exists yet (a clean install), say so plainly ("Your team's workspace isn't set up yet. Say 'set up my AI team' to start."), mark the checks that need it as skipped, and still test the team members and connections. Otherwise search Notion for "Business Brain" and confirm these exist: pages Workforce Settings (with a Connections section and a Business Brain version line), Company Profile, Priorities, Policies, Brand & Tone, FAQs, Paste Box, Your Team (missing pieces from older versions: offer the upgrade in `references/brain-upgrades.md`); databases Approvals, Assignments, Briefings, Pricing & Offers, Customers & Leads. Count "not set" markers (they read back as `<i>not set</i>`) on each page as a completeness score. Count active rows in Pricing & Offers.
6. **Check the approval queue end to end, including duplicates:** create one Approvals row: Item "Self-test: queue check <code>", Department "Chief of Staff", Action type "Other", Exact action "No action. Test row. (source: selftest:<code>)", Status "Pending", Source run "<Run ID> Self-test". Read it back to confirm an AP number was assigned. Then try to queue the same item again following `references/approval-queue.md`: PASS only if the duplicate check finds the existing row by its source key and no second row is created. Then list the whole active queue (every Pending and Approved row) with the one-line reply instructions, exactly as a briefing would, and confirm the count matches the database. Set the test row's Status to "Done". Never delete it.
6b. **Check run tracking with test records.** Use only records titled "Self-test fixture <code> A/B" (Type Self-test). Real runs ignore fixtures, and these checks look only at fixtures, never at this run's own record. Apply `references/run-tracking.md` section 3 as if a run of the responsibility "fixture <code>" were starting now:
   - Create fixture A (header: Run ID ST-<code>-A, Started now, Source Manual, Status Running). PASS if section 3 says **still in progress, don't run**.
   - Finish A (Run finished, Result Complete). Create fixture B, unfinished, header saying it started 60 minutes ago with no Progress lines. PASS if section 3 says **interrupted, resume B** (add a "Resumed" section to B; no new record).
   - Finish B. PASS if section 3 now says **new run**, so two legitimate runs on one day stay separate.
   - Fetch A back by its link: PASS if it opens and the header reads back intact.
   - If anything in this step fails, still finish both fixtures before moving on, so none is left unfinished.
6c. **Check the inbox safeguards** (read-only, Gmail or Outlook owners; skip on paste mode):
   - **Outside the inbox:** run the inbox triage search (`references/inbox-coverage.md` section 2) for the last 24 hours and count threads without the Inbox label (archived by filters) and in each tab. PASS if the search returns them; report the counts ("14 of 63 emails never reached your inbox; the team still sees them").
   - **Many pages:** run the same search for the last 7 days with 50 per page, following next-page tokens up to 5 pages. PASS if every token was followed; report pages and threads, and Gmail's own estimate next to the real count.
   - **Bookmark:** read the newest finished Inbox triage records. PASS if each Partial or Failed run kept the previous Completed through, and no finished run left a gap between one window's end and the next start (older records without these lines: "not checked: from before this check existed").
6d. **Check Gmail draft links** (attended, Gmail owners, only after the owner says yes, since it leaves one draft in their Drafts folder): create a draft to the owner's own address, subject "AI Workforce self-test <code>: safe to delete", body one line. Check it with get_draft and confirm the `viewUrl` opens that draft. Never send it. Tell the owner it's there to delete whenever they like.
6e. **Check recurring tasks** (read-only): follow `schedule-workforce` "Check and update recurring responsibilities" steps 1-3 only. Report each task as current or using older instructions. Change nothing.
6f. **Check the notification text:** write the summary a scheduled run would send for this test record. PASS if it contains the record's full Notion link as plain text on its own line and that link matches the fetched record.
7. **Report two tables and one verdict:**
   - Team members: member, how it ran (separate agent / briefed assistant / single assistant), code matched (yes/no/not applicable), Notion, then one column per chosen app (or "Paste mode" for email or calendar), result (Verified / Failed / "Not tested separately" in single-assistant mode). A chosen app that is unavailable is a warning, not a failure: the team falls back to the Paste Box.
   - Business Brain: item, present (yes/no), fields still not set.
   Plus: approval queue test PASS/FAIL with the AP number, and a **Behavior checks** table: check, how it was tested ("tested live" or "checked by reading", never blurred), result (PASS / FAIL / skipped and why).
   - **Verdict**, one of: "PASS: your team members ran as separate agents" (every member verified as a separate agent) · "PASS: your team ran with briefed assistants" (all verified, at least one as a briefed assistant) · "PASS in single-assistant mode: no separate agents ran in this session; your Chief of Staff handles each role itself. In Cowork, members run as separate agents." · "FAIL" (any member Failed, Notion unreachable, or the approval queue, run tracking or inbox checks failed), with what failed. A skipped check (for example draft links without the owner's yes) is listed as skipped, not passed.
8. **Save** the tables in this run's own record (Type = Self-test, `references/run-tracking.md`).
9. **Summarize what to fix** in plain language: chosen apps that aren't reachable (reconnect, or switch to paste mode by saying "finish my setup"), missing Brain pieces (offer to run `setup-workforce` to add them), members that Failed. In single-assistant mode, nothing needs fixing; say once that Cowork runs members as separate agents if the owner wants that.
