---
name: workforce-self-test
description: This skill should be used when the user asks to "test the workforce", "verify the subagents run", "run the self-test", "check that the AI team works", or wants proof of how the team members and connections actually run.
metadata:
  version: "0.4.4"
---

# Workforce Self-Test

_Files named `references/…` are in this skill's own folder._

Prove what actually works, and never claim more. Do not simulate anything. Follow `references/approval-policy.md`, `references/connections.md` and the run rule in `references/team-roles.md`.

**Be exact about who ran.** Each member's result is one of:
- **Separate agent: verified.** It was launched as its own agent and returned the exact code.
- **Briefed assistant: verified.** Its named agent isn't available, a general-purpose agent was launched with that member's brief, and it returned the exact code.
- **Single assistant (no separate agents).** No agents can be launched in this session (regular chat). The Chief of Staff does every member's work itself. That's a working setup, but members aren't tested separately, and the report must say no separate agents ran.
- **Failed.** A launch was attempted and errored, or the reply was missing the code or the role.

Never label a member "separate agent" unless that launch returned the code.

## Steps

1. **Read Connections** in Workforce Settings so you know which apps this owner chose (Gmail / Outlook / Paste mode, and so on). The test checks those apps, not apps the owner never chose.
2. **Generate a code.** Create a random 6-character code (for example `K7Q2XM`) and keep it.
3. **Test the five members** (Operations, Marketing, Sales, Client Success, Finance), all at once where possible. For each, use the first option that is available:
   - The named agent (`operations-manager`, `marketing-manager`, `sales-manager`, `client-success-manager`, `finance-manager`), or, if the named agents aren't available,
   - a general-purpose agent briefed as that member.
   Brief: "Self-test. Reply with exactly: (1) your role name, (2) the code <code>, (3) for Notion and for each app the owner chose (<list from Connections, e.g. Gmail, Google Calendar, Google Drive, or Microsoft 365>), whether you can actually use it right now, marked available or unavailable after trying one harmless read-only call (skip anything on paste mode or None), (4) one sentence confirming you will not send, spend, modify financial records or make irreversible changes. Do nothing else."
   If no agents can be launched at all, don't launch anything: the session is in single-assistant mode. Test Notion and each chosen app yourself with one harmless read each.
4. **Check each reply:** correct role, exact code echoed, connections honestly reported, hard-limit sentence present. Missing code or role = Failed for that member. If one launch fails, retry that member once before marking it Failed.
5. **Check the Business Brain:** search Notion for "Business Brain" and confirm these exist: pages Workforce Settings (with a Connections section and a Business Brain version line), Company Profile, Priorities, Policies, Brand & Tone, FAQs, Paste Box, Your Team (missing pieces from older versions: offer the upgrade in `references/brain-upgrades.md`); databases Approvals, Assignments, Briefings, Pricing & Offers, Customers & Leads. Count "not set" markers (they read back as `<i>not set</i>`) on each page as a completeness score. Count active rows in Pricing & Offers.
6. **Check the approval queue end to end:** create one Approvals row: Item "Self-test: queue check <code>", Department "Chief of Staff", Action type "Other", Exact action "No action. Test row.", Status "Pending", Source run "Self-test <date>". Read it back to confirm an AP number was assigned, then set its Status to "Done". Never delete it.
7. **Report two tables and one verdict:**
   - Team members: member, how it ran (separate agent / briefed assistant / single assistant), code matched (yes/no/not applicable), Notion, then one column per chosen app (or "Paste mode" for email or calendar), result (Verified / Failed / "Not tested separately" in single-assistant mode). A chosen app that is unavailable is a warning, not a failure: the team falls back to the Paste Box.
   - Business Brain: item, present (yes/no), fields still not set.
   Plus: approval queue test PASS/FAIL with the AP number.
   - **Verdict**, one of: "PASS: your team members ran as separate agents" (every member verified as a separate agent) · "PASS: your team ran with briefed assistants" (all verified, at least one as a briefed assistant) · "PASS in single-assistant mode: no separate agents ran in this session; your Chief of Staff handles each role itself. In Cowork, members run as separate agents." · "FAIL" (any member Failed, Notion unreachable, or the approval queue test failed), with what failed.
8. **Save** a Briefings row (Type = Self-test) with the tables.
9. **Summarize what to fix** in plain language: chosen apps that aren't reachable (reconnect, or switch to paste mode by saying "finish my setup"), missing Brain pieces (offer to run `setup-workforce` to add them), members that Failed. In single-assistant mode, nothing needs fixing; say once that Cowork runs members as separate agents if the owner wants that.
