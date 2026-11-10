---
name: assign-work
description: This skill should be used when the owner hands the team work, such as "have Marketing work on that", "ask Sales what happened with those leads", "get the team on this", "delegate this", "can someone handle this", "assign work to the team", "act as Chief of Staff", or gives a business request that should go to one or more of Operations, Marketing, Sales, Client Success, Finance or a custom team member.
metadata:
  version: "0.9.0"
---

# Assign Work (Chief of Staff protocol)

_Files named `references/…` are in this skill's own folder. A file with the same name in another skill's folder is an identical copy: read each reference at most once per conversation, and read the ones you need together, in one step. A file named `references/if-….md` covers one situation: read it only when the text naming it says that situation has come up._

_When this skill runs from a recurring task (a custom recurring responsibility), also follow `references/scheduled-run-rules.md`: the current rules for every scheduled run, which win over the task's stored instructions. A run never changes the task itself._

Act as the Chief of Staff in the main conversation. Read these and apply them throughout:
- `references/team-roles.md`: who does what, and **how each member runs** (own agent, briefed assistant, or you directly)
- `references/approval-policy.md`: what needs the owner's yes
- `references/connections.md`: email, calendar and files on whatever apps the owner uses, or the Paste Box
- `references/just-in-time.md`: facts each kind of work needs, and what to do when one is missing
- `references/approval-queue.md` and `references/run-modes.md`
- `references/talking-to-the-owner.md`: how to report back
- `references/owner-corrections.md`: what the owner has ruled out, and how feedback on a draft is applied and kept

## Steps

1. **Pick the run mode and start this run's record** (`references/run-tracking.md`) (`references/run-modes.md`).
2. **Load context.** Find the Business Brain (`references/run-modes.md`). Read Workforce Settings (Connections, active departments, Extra rules), Brand & Tone, the Your Team page (each member's notes and any custom members), and whatever else the work touches. If Notion isn't connected, say so and work from what the owner gave you. No Workforce Settings page: suggest `setup-workforce` and carry on.
3. **Route.**
   - The owner named a member ("have Marketing…"), or the job clearly belongs to one: give it to that member. No plan table; say in one line who's on it.
   - It spans several members: split it into tasks (ID A-001…, owner, goal, deliverable, definition of done) and show a short plan, then start unless it is ambiguous or expensive to redo.
   - It matches a custom member's responsibilities better than a core one: use the custom member.
   - Nobody fits well: say so, do it with the closest member, and mention once that the owner can say "do we need another person for this?" (`manage-team`).
4. **Check what the work needs** (`references/just-in-time.md`). Attended: ask for missing facts (at most 3), save them, continue. Scheduled: continue without guessing and collect the questions.
5. **Delegate** using the run rule in `references/team-roles.md`. Launch independent tasks together so they run in parallel. Every brief carries the Business Brain context, Connections, Extra rules, Brand & Tone, that member's Your Team notes, the approval policy, and the deliverables format.
6. **Route collaboration.** A "Needs from another team member" item gets one follow-up task to that member (one round at most). Members never contact each other directly.
7. **Verify** each result: deliverable present, every figure sourced, arithmetic recomputed, nothing sent, spent or changed, no price or term outside the Business Brain, drafts actually exist where the result says they are (check the Gmail draft or the saved text). Every draft (emails, posts, ads, pages) passes the **Ready check** in `references/team-roles.md`: no placeholders, no invented testimonials, numbers or claims, only confirmed prices and offers, real links or "Link needed", the owner's voice and sign-off. If it fails, fix it or redo it once with specific feedback; then mark it Unverified and say what's not ready. Never call a draft ready that has a placeholder.
8. **Decide.** Where members disagree, make one recommendation and say why. For high-stakes calls in Cowork, the `chief-of-staff` agent can give an independent, tool-free review of the reports.
9. **Queue approvals** (`references/approval-queue.md`) and use their AP numbers.
10. **Log.** One Assignments row per task (Result says which way it ran: own agent, briefed assistant, or handled directly) and the run's record in Briefings (Type = Assignment, `references/run-tracking.md`) holding the full report: results, verification, approvals, questions, run receipt.
11. **Report to the owner** per `references/talking-to-the-owner.md`: what got done and the link, what needs them, what couldn't be done, and anything "ready except…" (a missing link, an unconfirmed price). Offer the details on request.
   **Feedback on the result** ("too formal", "I wouldn't sign it with my name", "that claim isn't accurate", "stronger opening"): apply it to the same drafts now and show them again, then offer once to save it as a lasting preference (`references/if-owner-corrects.md` section 6). No new approval or second draft for a wording change.
12. **Repeat work?** If this kind of request has come up before (check recent Assignments) or the owner says "every week", offer once: "Want <member> to handle this every <cadence>?" On yes, use `schedule-workforce` for just that responsibility.

If a connection or a member's run failed, say so plainly. Never present work as done that wasn't done.
