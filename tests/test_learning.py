"""Scenario tests for 0.6.0: the team learns from the owner (see learning_logic.py and run_logic.py).

These test the written design restated as code, not Claude following it (tests/README.md)."""
import sys, unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from learning_logic import (Brain, active_queue, classify_correction, save_rule, retire_rule, load_rules,
                            run, interpret_reply, apply_reply, choose_brain, write_record,
                            save_website_summary, questions_to_ask, make_draft, apply_feedback,
                            ready_check, schedule_one)
from run_logic import Message, Mailbox, quick_look, triage, next_window, last_checkpoint, owner_summary

DAY1, DAY2, DAY3 = date(2026, 11, 6), date(2026, 11, 7), date(2026, 11, 8)


def make_alert(i, kind="automation_failure", **kw):
    """A failure alert about an old client's Make automation (the live test's case)."""
    return {"id": f"m{i}", "topic": "Make scenario 'Northwind lead sync' stopped",
            "entities": {"northwind", "make"}, "kind": kind, "problem": "Northwind Make sync failing",
            "thread": "t-northwind", **kw}


def first_run_brain():
    b = Brain()
    run(b, [make_alert(1), make_alert(2)], DAY1)          # two emails, one problem → one item
    return b


class OwnerCorrections(unittest.TestCase):
    def test_kinds_of_correction(self):
        cases = {"That isn't my responsibility anymore.": "lasting",
                 "Don't keep bringing this up.": "lasting",
                 "That company is no longer one of my businesses.": "lasting",
                 "This notification isn't important to me.": "lasting",
                 "Family and school emails deserve my attention.": "lasting",
                 "I already handled that.": "item",
                 "That purchase was intentional.": "item",
                 "Ignore the launch emails until Friday.": "temporary",
                 "This sounds too formal.": "draft",
                 "I wouldn't sign that with my name.": "draft",
                 "Hmm.": "unclear"}
        for text, kind in cases.items():
            self.assertEqual(classify_correction(text), kind, text)

    def test_legacy_alert_dismissed_is_not_raised_again(self):
        b = first_run_brain()
        self.assertEqual([a["problem"] for a in active_queue(b)], ["Northwind Make sync failing"])
        self.assertEqual(b.approvals[0]["count"], 2)                     # consolidated
        ap = b.approvals[0]["ap"]
        self.assertEqual(save_rule(b, "not_mine", "Northwind Studio and its Make automations",
                                   attended=True, confirmed=True, today=DAY1, close_aps=[ap]), "saved")
        self.assertEqual(active_queue(b), [])
        report = run(b, [make_alert(3), make_alert(4)], DAY2)            # tomorrow, more emails about it
        self.assertEqual(report["raised"], [])
        self.assertEqual(report["your rules"], 2)
        self.assertEqual(active_queue(b), [])
        self.assertEqual(len(b.approvals), 1)                             # nothing recreated

    def test_new_critical_alert_still_surfaces(self):
        b = first_run_brain()
        save_rule(b, "not_mine", "Northwind Studio and its Make automations", attended=True, confirmed=True,
                  today=DAY1, close_aps=[b.approvals[0]["ap"]])
        incident = make_alert(9, kind="security_incident", problem="New sign-in to your Google account via Northwind",
                              topic="New sign-in to your account from Make (Northwind)", new=True)
        report = run(b, [make_alert(8), incident], DAY2)
        self.assertEqual(report["raised"], ["New sign-in to your Google account via Northwind"])
        self.assertTrue(any("raised because it's a new security_incident" in n for n in report["notes"]))
        self.assertEqual(report["your rules"], 1)                         # the repeat failure still hidden

    def test_narrow_rule_keeps_owners_own_items(self):
        b = Brain()
        save_rule(b, "ignore", "GitHub notifications except acme-app", attended=True, confirmed=True, today=DAY1)
        other = {"id": "g1", "topic": "GitHub: issue in someone-else/repo", "entities": {"github", "someone-else"},
                 "kind": "notification", "problem": "GitHub issue elsewhere"}
        mine = {"id": "g2", "topic": "GitHub: build failed in acme-app", "entities": {"github", "acme-app"},
                "kind": "automation_failure", "problem": "acme-app build failing"}
        report = run(b, [other, mine], DAY2)
        self.assertEqual(report["raised"], ["acme-app build failing"])
        self.assertEqual(report["your rules"], 1)

    def test_attention_rule_surfaces_family_and_school(self):
        b = Brain()
        save_rule(b, "attention", "School and family emails", attended=True, confirmed=True, today=DAY1)
        r = run(b, [{"id": "s1", "topic": "School: early dismissal Friday", "entities": {"school"},
                     "kind": "personal", "problem": "school notice"}], DAY2)
        self.assertEqual(r["attention"], ["School: early dismissal Friday"])

    def test_corrections_persist_across_separate_runs(self):
        b = first_run_brain()
        save_rule(b, "not_mine", "Northwind Studio and its Make automations", attended=True, confirmed=True,
                  today=DAY1, close_aps=[b.approvals[0]["ap"]])
        saved_page = b.priorities                                         # all that survives a session
        later = Brain(priorities=saved_page, approvals=b.approvals)       # a fresh run, days later
        self.assertIn("Northwind Studio and its Make automations · since Nov 6, 2026", later.priorities)
        self.assertEqual(run(later, [make_alert(5)], DAY3)["raised"], [])

    def test_unconfirmed_or_scheduled_corrections_save_nothing(self):
        b = first_run_brain()
        before = b.priorities
        self.assertEqual(save_rule(b, "not_mine", "Northwind", attended=True, confirmed=False, today=DAY1),
                         "needs confirmation")
        self.assertEqual(save_rule(b, "not_mine", "Northwind", attended=False, confirmed=True, today=DAY1),
                         "question for owner")
        self.assertEqual(b.priorities, before)
        self.assertEqual(active_queue(b)[0]["status"], "Pending")

    def test_temporary_rule_expires_and_retired_rule_is_kept(self):
        b = Brain()
        save_rule(b, "ignore", "Launch emails", attended=True, confirmed=True, today=DAY1, until=DAY2)
        item = {"id": "l1", "topic": "Launch reminder", "entities": {"launch"}, "kind": "promo", "problem": "launch"}
        self.assertEqual(run(b, [item], DAY2)["your rules"], 1)
        self.assertEqual(run(b, [dict(item, id="l2")], DAY3)["raised"], ["launch"])
        save_rule(b, "not_mine", "Northwind Studio", attended=True, confirmed=True, today=DAY1)
        retire_rule(b, "Northwind Studio", DAY2)
        self.assertIn("Northwind Studio · since Nov 6, 2026 · no longer applies Nov 7, 2026", b.priorities)
        self.assertEqual(load_rules(b, DAY3), [])

    def test_older_workspace_saves_under_things_to_ignore(self):
        b = Brain(priorities="## Things to ignore for now\n\n- <i>not set</i>\n")
        save_rule(b, "not_mine", "Northwind Studio", attended=True, confirmed=True, today=DAY1)
        self.assertIn("- Not my responsibility: Northwind Studio · since", b.priorities)
        self.assertEqual(run(b, [make_alert(1)], DAY2)["your rules"], 1)

    def test_handled_items_leave_queue_but_stay_in_history(self):
        b = first_run_brain()
        b.assignments.append({"title": "Check Northwind sync", "owner": "Operations", "status": "Planned",
                              "source": b.approvals[0]["source"], "created_by": "team"})
        b.assignments.append({"title": "Owner's own note", "owner": "Operations", "status": "Planned",
                              "source": b.approvals[0]["source"], "created_by": "owner"})
        apply_reply(b, interpret_reply("I already handled that one", [b.approvals[0]]), DAY1)
        self.assertEqual(active_queue(b), [])
        self.assertEqual(len(b.approvals), 1)                             # history kept
        self.assertEqual(b.approvals[0]["status"], "Done")
        self.assertIn("Owner: already handled", b.approvals[0]["owner_note"])
        self.assertEqual([a["status"] for a in b.assignments], ["Done", "Planned"])   # owner's row untouched
        self.assertEqual(run(b, [make_alert(7)], DAY2)["raised"], [])     # same thread, nothing new


def shown_items():
    return [{"ap": 21, "kind": "automation_failure", "action_type": "Other", "source": "gmail:a"},
            {"ap": 22, "kind": "reply", "action_type": "Send message", "source": "gmail:b"},
            {"ap": 23, "kind": "notice", "action_type": "Other", "source": "gmail:c"},
            {"ap": 24, "kind": "invitation", "action_type": "Calendar with others", "source": "gmail:d"},
            {"ap": 25, "kind": "charge", "action_type": "Other", "source": "gmail:e"},
            {"ap": 26, "kind": "invitation", "action_type": "Calendar with others", "source": "gmail:f"}]


def brain_with(items):
    return Brain(approvals=[dict(i, status="Pending", item=f"AP-{i['ap']}") for i in items])


class ThreadQuiet(unittest.TestCase):
    def test_closed_item_quiets_repeats_for_14_days_then_needs_a_rule(self):
        b = first_run_brain()
        apply_reply(b, interpret_reply("I already handled that one", [b.approvals[0]]), DAY1)
        self.assertEqual(run(b, [make_alert(5)], DAY1 + timedelta(days=10))["already handled"], 1)
        self.assertEqual(run(b, [make_alert(6)], DAY1 + timedelta(days=15))["raised"],
                         ["Northwind Make sync failing"])                 # "this item only" wears off

    def test_a_person_writing_something_new_is_new_work(self):
        b = first_run_brain()
        apply_reply(b, interpret_reply("I already handled that one", [b.approvals[0]]), DAY1)
        reply = make_alert(7, kind="person", materially_new=True, problem="Client asks a new question")
        self.assertEqual(run(b, [reply], DAY2)["raised"], ["Client asks a new question"])


class ConversationalApprovals(unittest.TestCase):
    def test_the_six_replies_from_the_live_test(self):
        shown = shown_items()
        d = dict(interpret_reply("One isn't my problem. Two is fine. Look into three. Decline those invitations. "
                                 "I already checked five", shown))
        self.assertEqual(d, {21: "not_mine", 22: "confirm_first", 23: "investigate",
                             24: "confirm_first", 26: "confirm_first", 25: "handled"})
        b = brain_with(shown)
        self.assertEqual(apply_reply(b, list(d.items()), DAY1), [])      # nothing declined or sent yet
        # after the one-line confirmation ("Decline: … (AP-24), … (AP-26)?" → "yes"), exactly those two
        self.assertEqual(apply_reply(b, [(24, "approve"), (26, "approve")], DAY1),
                         [("do", 24, "Calendar with others"), ("do", 26, "Calendar with others")])

    def test_acknowledgement_is_never_permission(self):
        b = brain_with(shown_items())
        acts = apply_reply(b, interpret_reply("Two is fine. I looked at five. That purchase was intentional",
                                              shown_items()), DAY1)
        self.assertEqual(acts, [])                                        # nothing sent or done
        self.assertEqual(next(a for a in b.approvals if a["ap"] == 22)["status"], "Pending")
        self.assertEqual(next(a for a in b.approvals if a["ap"] == 25)["status"], "Done")

    def test_ambiguous_replies_cause_no_action(self):
        b = brain_with(shown_items())
        for text in ["Handle them", "Sure", "Do whatever makes sense", "That one's fine"]:
            d = interpret_reply(text, shown_items())
            self.assertTrue(all(m == "clarify" for _, m in d), text)
            self.assertEqual(apply_reply(b, d, DAY1), [], text)
        self.assertTrue(all(a["status"] == "Pending" for a in b.approvals))

    def test_number_that_could_mean_two_items_is_asked(self):
        shown = [{"ap": 2, "kind": "reply", "action_type": "Send message", "source": "x"},
                 {"ap": 7, "kind": "reply", "action_type": "Send message", "source": "y"}]
        self.assertEqual(interpret_reply("approve 2", shown, numbering="both"), [(None, "clarify")])
        self.assertEqual(interpret_reply("approve 2", shown, numbering="ap"), [(2, "approve")])
        self.assertEqual(interpret_reply("approve 2", shown, numbering="position"), [(7, "approve")])

    def test_investigation_creates_one_task_and_no_action(self):
        b = brain_with(shown_items())
        acts = apply_reply(b, interpret_reply("Look into three", shown_items()), DAY1)
        self.assertEqual(acts, [])
        self.assertEqual(len(b.assignments), 1)
        self.assertEqual(next(a for a in b.approvals if a["ap"] == 23)["status"], "Pending")

    def test_approved_send_is_handed_to_the_owner(self):
        b = brain_with(shown_items())
        acts = apply_reply(b, interpret_reply("approve two", shown_items()), DAY1)
        self.assertEqual(acts, [("do", 22, "Send message")])
        self.assertEqual(next(a for a in b.approvals if a["ap"] == 22)["status"], "Handed to you")


class ChoosingTheBusinessBrain(unittest.TestCase):
    def pages(self):
        return [{"id": "old", "title": "Business Brain", "settings": True},
                {"id": "new", "title": "Business Brain", "settings": True},
                {"id": "arc", "title": "Business Brain (archive 2026-11-05)", "settings": True},
                {"id": "tpl", "title": "Business Brain Template", "settings": True}]

    def test_one_with_settings_is_used(self):
        pages = [{"id": "a", "title": "Business Brain", "settings": True},
                 {"id": "b", "title": "Business Brain", "settings": False}]
        self.assertEqual(choose_brain(pages, "scheduled"), ("use", pages[0]))

    def test_two_real_candidates_attended_asks(self):
        kind, cands = choose_brain(self.pages(), "attended")
        self.assertEqual(kind, "ask")
        self.assertEqual([c["id"] for c in cands], ["old", "new"])      # archive and template ignored

    def test_two_real_candidates_scheduled_touch_neither(self):
        pages = self.pages()
        kind, msg = choose_brain(pages, "scheduled")
        self.assertEqual(kind, "stop")
        self.assertIn("didn't touch either", msg)
        self.assertTrue(all("records" not in p for p in pages))

    def test_owner_choice_keeps_records_apart(self):
        pages = self.pages()
        kind, chosen = choose_brain(pages, "attended", owner_pick="new")
        write_record(chosen, "IT-20261106-0900")
        self.assertEqual([p["id"] for p in pages if "records" in p], ["new"])


class FirstAssignmentQuickLook(unittest.TestCase):
    def mailbox(self, now):
        msgs = [Message(f"q{i}", now - timedelta(minutes=10 * i), important=(i % 20 == 0)) for i in range(140)]
        return Mailbox(msgs)

    def test_quick_look_never_advances_the_bookmark(self):
        now = datetime(2026, 11, 6, 9, 0)
        records, actions, box = [], [], self.mailbox(now)
        rec = quick_look(records, box, now, actions)
        self.assertEqual(rec.reviewed, 50)
        self.assertIsNone(rec.completed_through)
        self.assertEqual(rec.result, "Partial")
        self.assertIsNone(last_checkpoint(records))
        # the next full run starts as a first run, reaching back to the quick look's own window start
        self.assertEqual(next_window(records, now + timedelta(hours=1))[0], now - timedelta(hours=24))
        self.assertIn("haven't gone through the rest", owner_summary(rec, 140))
        self.assertNotIn("all", owner_summary(rec, 140).lower())

    def test_full_review_after_quick_look_redoes_nothing(self):
        now = datetime(2026, 11, 6, 9, 0)
        records, actions, box = [], [], self.mailbox(now)
        quick_look(records, box, now, actions)
        drafted_first = {k for _, k in actions}
        full = triage(records, box, now + timedelta(minutes=30), actions=actions)
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)))                       # no draft twice
        self.assertTrue(drafted_first)
        self.assertEqual(full.completed_through, now + timedelta(minutes=30))
        self.assertEqual(full.window[0], now - timedelta(hours=24))       # reaches back: no mail skipped


class QuickLookOnDemand(unittest.TestCase):
    """1.0.0: "just check my newest 20 emails" or "anything new since lunch" runs the same quick look at
    any time: its own record, labelled, and the bookmark stays exactly where the last full check left it."""
    def setUp(self):
        self.morning = datetime(2026, 11, 6, 7, 30)
        msgs = [Message(f"m{i}", self.morning + timedelta(minutes=9 * i - 300), important=(i % 9 == 0)) for i in range(90)]
        self.box, self.records, self.actions = Mailbox(msgs), [], []
        self.full = triage(self.records, self.box, self.morning, actions=self.actions)
        self.bookmark = last_checkpoint(self.records)
        self.assertEqual(self.bookmark, self.morning)

    def test_newest_20_makes_its_own_record_and_leaves_the_bookmark(self):
        now = self.morning + timedelta(hours=6)
        rec = quick_look(self.records, self.box, now, self.actions, threads=20)
        self.assertEqual((rec.reviewed, rec.coverage), (20, "quick look (newest 20 threads)"))
        self.assertIsNot(rec, self.full)
        self.assertEqual(len(self.records), 2)                             # its own record
        self.assertIsNone(rec.completed_through)
        self.assertEqual(last_checkpoint(self.records), self.bookmark)     # not moved
        self.assertIn("haven't gone through the rest", owner_summary(rec, 60))
        self.assertNotIn("all", owner_summary(rec, 60).lower())            # never claims the whole inbox

    def test_since_lunch_looks_only_at_that_window(self):
        now = self.morning + timedelta(hours=6)
        lunch = now.replace(hour=12, minute=0)
        rec = quick_look(self.records, self.box, now, self.actions, since=lunch)
        self.assertEqual(rec.window, (lunch, now))
        self.assertEqual(last_checkpoint(self.records), self.bookmark)

    def test_the_next_full_check_still_starts_from_the_bookmark_and_drafts_nothing_twice(self):
        now = self.morning + timedelta(hours=6)
        quick_look(self.records, self.box, now, self.actions, threads=20)
        later = triage(self.records, self.box, now + timedelta(hours=2), actions=self.actions)
        self.assertEqual(later.window[0], self.bookmark - timedelta(minutes=15))
        keys = [k for _, k in self.actions]
        self.assertEqual(len(keys), len(set(keys)))


class LearningTheBusiness(unittest.TestCase):
    FACTS = [("What we do", "Workshops for first-time managers", "description"),
             ("Who we serve", "New team leads", "description"),
             ("Pro plan", 49, "price"),
             ("Refunds", "30-day money-back guarantee", "policy")]

    def test_website_facts_are_not_confirmed_pricing_or_policy(self):
        b = Brain()
        save_website_summary(b, self.FACTS, summary_yes=True)
        self.assertEqual(b.profile["What we do"], "Workshops for first-time managers")
        self.assertEqual(b.pricing, {})
        self.assertEqual(b.policies, {})
        self.assertEqual(ready_check("Get Pro for $49 today.", b), ["unconfirmed price: $49"])

    def test_confirmed_price_becomes_usable(self):
        b = Brain()
        save_website_summary(b, self.FACTS, summary_yes=True, confirmed_items={"Pro plan"})
        self.assertEqual(b.pricing, {"Pro plan": 49})
        self.assertEqual(ready_check("Get Pro for $49 today.", b), [])
        self.assertEqual(b.policies, {})

    def test_questions_already_answered_are_not_asked(self):
        asked = questions_to_ask(["sign-off", "refund rule", "time zone"], brain_fields={"time zone"},
                                 said_in_chat={"refund rule"})
        self.assertEqual(asked, ["sign-off"])


class DraftsAndFeedback(unittest.TestCase):
    def test_no_sign_off_set_means_no_name_signed(self):
        b = Brain()
        d = make_draft(b, "I am writing to share our new tool.")
        self.assertIsNone(d["sign_off"])
        self.assertNotIn("Owner", d["text"])

    def test_writing_preferences_apply_to_later_drafts(self):
        b = Brain(brand={"sign_off": "Best regards,\nThe Owner", "voice": "formal"})
        d1 = make_draft(b, "I am writing to share our new tool.")
        apply_feedback(b, d1, "I wouldn't sign that with my name", save=True)
        apply_feedback(b, d1, "This sounds too formal, I usually write more conversationally", save=True)
        self.assertNotIn("The Owner", d1["text"])                         # this draft fixed now
        d2 = make_draft(b, "I am writing to invite you to a webinar.")    # a later, different draft
        self.assertNotIn("The Owner", d2["text"])
        self.assertTrue(d2["text"].startswith("Quick note:"))

    def test_feedback_not_saved_affects_only_this_draft(self):
        b = Brain(brand={"sign_off": "Cheers", "voice": "formal"})
        d1 = make_draft(b, "I am writing to say hi.")
        apply_feedback(b, d1, "too formal", save=False)
        self.assertEqual(make_draft(b, "I am writing to follow up.")["voice"], "formal")

    def test_placeholders_and_invented_proof_block_ready(self):
        b = Brain(links={"https://example.com/start"})
        self.assertIn("placeholder", ready_check("Hi [First Name], grab it here: {link}", b))
        self.assertIn("placeholder", ready_check("Launching on TBD", b))
        self.assertTrue(any(p.startswith("unsourced claim") for p in
                            ready_check('Join 10,000 marketers. "It doubled my sales" — Sam', b)))
        self.assertIn("unknown link: https://example.com/other",
                      ready_check("Start at https://example.com/other", b))
        self.assertIn("link needed", ready_check("Start free. Link needed: signup page", b))
        self.assertEqual(ready_check("Start free at https://example.com/start", b), [])


class RecurringWorkDuringOnboarding(unittest.TestCase):
    def test_repeated_meeting_or_setup_creates_one_task(self):
        tasks = []
        tasks, r1 = schedule_one(tasks, "inbox-triage", "weekdays 10:23")
        tasks, r2 = schedule_one(tasks, "inbox-triage", "weekdays 10:23")    # meeting run again
        tasks[0]["paused"] = True
        tasks, r3 = schedule_one(tasks, "inbox-triage", "weekdays 2:47")     # setup resumed later
        self.assertEqual((r1, len(tasks)), ("created", 1))
        self.assertEqual(r2, r3)
        self.assertTrue(r2.startswith("exists"))
        tasks, r4 = schedule_one(tasks, "daily-executive-briefing", "weekdays 8:23")
        self.assertEqual((r4, len(tasks)), ("created", 2))


if __name__ == "__main__":
    unittest.main()
