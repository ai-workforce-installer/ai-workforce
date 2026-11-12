"""Tests of the 1.0.0 finishing rules, restated as code in work_logic.py, with a clock the tests move.

They check the written design in the hard cases (repeats, retries, weak evidence, time zones,
interrupted upgrades). They do not show Claude following it: see tests/README.md.
"""
from __future__ import annotations

import copy, sys, unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import work_logic as w


def monday_morning():
    return w.Clock.at_local(2026, 3, 2, 7, 30)        # Monday 7:30 AM, UTC-6


class OneObligationOneRow(unittest.TestCase):
    def setUp(self):
        self.clock, self.q = monday_morning(), w.Queue()
        self.alert = w.work_key("alert", "make", "lead sync failing")

    def test_a_failing_automation_relogged_daily_for_a_week_is_one_row(self):
        for day in range(7):
            self.q.record(self.alert, "Lead sync automation is failing", self.clock.now(),
                          source="gmail:alert-%d" % day, work_type="Monitored issue")
            self.clock.advance(days=1)
        self.assertEqual(len(self.q.rows), 1)
        row = self.q.rows[0]
        self.assertEqual((row.count, len(row.sources)), (7, 7))

    def test_a_retry_that_sees_the_same_message_changes_nothing(self):
        for _ in range(3):
            self.q.record(self.alert, "Lead sync automation is failing", self.clock.now(), source="gmail:alert-0")
        self.assertEqual((len(self.q.rows), self.q.rows[0].count), (1, 1))

    def test_a_later_message_in_a_later_run_updates_the_same_row(self):
        key = w.work_key("gmail-thread", "t81", "reply refund")
        first = self.q.record(key, "Reply to Dana about her refund", self.clock.now(), source="gmail:m1", work_type="Reply")
        self.clock.advance(days=2)
        again = self.q.record(key, "Reply to Dana about her refund", self.clock.now(), source="gmail:m2")
        self.assertIs(first, again)
        self.assertEqual(again.sources, ["gmail:m1", "gmail:m2"])
        self.assertEqual(again.latest, self.clock.now())

    def test_two_promises_in_one_thread_stay_two(self):
        self.q.record(w.work_key("gmail-thread", "t7", "send proposal"), "Send Acme the proposal", self.clock.now(), source="gmail:m5")
        self.q.record(w.work_key("gmail-thread", "t7", "intro to accountant"), "Introduce Acme to the accountant", self.clock.now(), source="gmail:m5")
        self.assertEqual(len(self.q.rows), 2)

    def test_a_run_id_is_never_an_obligations_only_identity(self):
        for bad in ["IT-20260302-0731", "DB-20260302-0731:draft", "", "reply"]:
            self.assertFalse(w.is_a_work_key(bad), bad)
            with self.assertRaises(ValueError):
                self.q.record(bad, "x", self.clock.now())
        self.assertTrue(w.is_a_work_key(self.alert))

    def test_an_unreadable_queue_is_carried_over_not_duplicated(self):
        q = w.Queue(readable=False)
        for _ in range(2):
            self.assertIsNone(q.record(self.alert, "Lead sync automation is failing", self.clock.now(), source="gmail:a"))
        self.assertEqual((q.rows, len(q.carried_over)), ([], 1))

    def test_a_row_closed_long_ago_does_not_swallow_new_work(self):
        row = self.q.record(self.alert, "Lead sync automation is failing", self.clock.now(), source="gmail:a")
        w._close(row, "Completed", self.clock.now(), evidence="success notice")
        self.clock.advance(days=30)
        fresh = self.q.record(self.alert, "Lead sync automation is failing", self.clock.now(), source="gmail:b")
        self.assertIsNot(fresh, row)


class WhoHasTheNextMove(unittest.TestCase):
    def test_status_says_who(self):
        for status, who in [("Planned", "team"), ("In progress", "team"), ("Prepared", "owner"),
                            ("Handed to you", "owner"), ("Done", "nobody")]:
            self.assertEqual(w.Row("a:b:c", "t", status=status).next_move, who)
        self.assertEqual(w.Row("a:b:c", "t", status="Blocked", waiting_on="Dana").next_move, "Dana")

    def test_a_blocked_item_resumes_when_its_input_appears(self):
        clock = monday_morning()
        row = w.wait_on(w.Row("deliverable:acme:proposal", "Acme proposal"), "the owner's price list", clock, blocker="prices not confirmed")
        self.assertEqual((row.status, row.next_move), ("Blocked", "the owner's price list"))
        w.input_arrived(row)
        self.assertEqual((row.status, row.next_move, row.blocker), ("Planned", "team", ""))

    def test_nothing_waits_without_a_next_action_and_a_next_check(self):
        clock, q = monday_morning(), w.Queue()
        a = q.record("gmail-thread:t1:reply", "Reply to Sam", clock.now(), work_type="Reply")
        a.status = "Prepared"
        self.assertEqual(w.missing_tracking(q), [a])
        a.next_action = "Owner sends the draft"
        w.set_next_check(a, clock)
        b = q.record("gmail-thread:t2:invoice", "Waiting for Dana's PO", clock.now(), work_type="Waiting on someone")
        w.wait_on(b, "Dana", clock)
        self.assertEqual(w.missing_tracking(q), [])


class SuggestedCheckTimes(unittest.TestCase):
    """With no stated deadline: working-day intervals in the owner's time zone, labelled as suggested."""
    def test_a_person_waiting_on_the_owner_is_checked_the_next_working_day(self):
        clock = w.Clock.at_local(2026, 3, 6, 16, 0)                      # Friday afternoon
        row = w.set_next_check(w.Row("gmail-thread:t1:reply", "Reply to Sam", status="Prepared"), clock)
        self.assertEqual(clock.local(row.next_check).strftime("%a %Y-%m-%d %H:%M"), "Mon 2026-03-09 09:00")
        self.assertTrue(row.check_is_suggested)
        self.assertIsNone(row.due)                                       # no deadline was invented

    def test_two_working_days_for_someone_else_and_five_for_a_monitored_issue(self):
        clock = w.Clock.at_local(2026, 3, 5, 10, 0)                      # Thursday
        waiting = w.wait_on(w.Row("gmail-thread:t2:po", "Dana's PO"), "Dana", clock)
        self.assertEqual(clock.local(waiting.next_check).strftime("%a %m-%d"), "Mon 03-09")
        issue = w.set_next_check(w.Row("alert:make:sync", "Sync failing", work_type="Monitored issue"), clock)
        self.assertEqual(clock.local(issue.next_check).strftime("%a %m-%d"), "Thu 03-12")

    def test_a_stated_deadline_wins_and_is_not_called_suggested(self):
        clock = monday_morning()
        friday = clock.local_time(2026, 3, 6, 17, 0)
        row = w.wait_on(w.Row("gmail-thread:t2:po", "Dana's PO"), "Dana", clock, until=friday)
        self.assertEqual((row.next_check, row.due, row.check_is_suggested), (friday, friday, False))

    def test_the_day_is_the_owners_day_not_utc(self):
        clock = w.Clock(datetime(2026, 3, 3, 2, 0, tzinfo=timezone.utc))  # Tuesday 02:00 UTC = Monday 8 PM for the owner
        self.assertEqual(clock.local().strftime("%a"), "Mon")
        row = w.set_next_check(w.Row("gmail-thread:t1:reply", "Reply to Sam", status="Prepared"), clock)
        self.assertEqual(clock.local(row.next_check).strftime("%a %H:%M"), "Tue 09:00")


class Snooze(unittest.TestCase):
    def test_a_snoozed_item_returns_at_the_right_local_time(self):
        clock, q = monday_morning(), w.Queue()
        row = q.record("gmail-thread:t9:reply", "Reply to the landlord", clock.now(), work_type="Reply")
        row.status = "Prepared"
        w.snooze(row, clock.local_time(2026, 3, 3, 9, 0))                 # "Snooze it until Tuesday"
        self.assertEqual(row.status, "Prepared")                          # snoozing never changes the status
        clock.set_local(2026, 3, 2, 20, 0)                                # Monday evening: already Tuesday in UTC
        self.assertEqual(clock.now().strftime("%a"), "Tue")
        self.assertEqual(q.due(clock), [])
        clock.set_local(2026, 3, 3, 8, 59)
        self.assertEqual(q.due(clock), [])
        clock.set_local(2026, 3, 3, 9, 0)
        self.assertEqual(q.due(clock), [row])

    def test_a_snoozed_item_stays_off_the_desk_until_its_time_and_only_a_snooze_hides_one(self):
        clock, q = monday_morning(), w.Queue()
        landlord = q.record("gmail-thread:t9:reply", "Reply to the landlord", clock.now(), work_type="Reply")
        sam = q.record("gmail-thread:t1:reply", "Reply to Sam", clock.now(), work_type="Reply")
        landlord.status = sam.status = "Prepared"
        landlord.next_action = "Owner sends the draft"
        w.set_next_check(sam, clock)                                      # a suggested check tomorrow hides nothing
        self.assertGreater(sam.next_check, clock.now())
        w.snooze(landlord, clock.local_time(2026, 3, 3, 9, 0))
        self.assertTrue(landlord.next_action.startswith("Snoozed until"))
        self.assertIn("Owner sends the draft", landlord.next_action)      # what was to happen next is kept
        clock.set_local(2026, 3, 2, 20, 0)                                # Monday evening: already Tuesday in UTC
        self.assertEqual(w.on_the_desk(q, clock), [sam])
        clock.set_local(2026, 3, 3, 9, 5)
        self.assertEqual(w.on_the_desk(q, clock), [landlord, sam])
        w.snooze(landlord, clock.local_time(2026, 3, 6, 9, 0))            # snoozed again: one marker, not two
        self.assertEqual(landlord.next_action.count("Snoozed until"), 1)


class ClosingNeedsEvidence(unittest.TestCase):
    def setUp(self):
        self.clock = monday_morning()
        self.reply = w.Row("gmail-thread:t1:reply-refund", "Reply to Dana about her refund", work_type="Reply", status="Prepared")

    def test_a_vanished_draft_with_no_sent_match_is_not_counted_as_sent(self):
        self.assertEqual(w.check_reply(self.reply, self.clock, draft_exists=False), "ask once")
        self.assertTrue(self.reply.open)
        self.clock.advance(days=1)
        self.assertEqual(w.check_reply(self.reply, self.clock, draft_exists=False), "closed: unverified")
        self.assertEqual((self.reply.status, self.reply.closed_as), ("Done", "Unverified"))
        self.assertNotEqual(self.reply.closed_as, "Sent")

    def test_a_draft_still_in_drafts_is_ready_never_finished(self):
        self.assertEqual(w.check_reply(self.reply, self.clock, draft_exists=True), "still ready")
        self.assertTrue(self.reply.open)

    def test_a_matching_message_in_sent_closes_it_as_sent_with_the_evidence(self):
        self.assertEqual(w.check_reply(self.reply, self.clock, draft_exists=False, sent_match="gmail:sent-77"), "closed: sent")
        self.assertEqual((self.reply.closed_as, self.reply.evidence), ("Sent", "gmail:sent-77"))

    def test_the_owners_word_closes_it_too(self):
        self.assertEqual(w.check_reply(self.reply, self.clock, draft_exists=False, owner_says="sent"), "closed: sent (owner's word)")
        self.assertIn("Owner: I sent it", self.reply.result)

    def test_a_sent_reply_leaves_the_customer_case_open(self):
        case = w.Row("case:dana:double-charge", "Dana was charged twice", work_type="Customer case", status="In progress")
        w.after_reply_sent(case, self.clock, "gmail:sent-77")
        self.assertTrue(case.open)
        self.assertEqual(case.next_move, "the customer")
        self.assertIsNotNone(case.next_check)
        w.close_case(case, self.clock)                                    # nobody confirmed anything
        self.assertTrue(case.open)
        w.close_case(case, self.clock, customer_confirmed=True, evidence="gmail:m-thanks")
        self.assertEqual(case.closed_as, "Completed")

    def test_a_passed_meeting_does_not_prove_it_was_held_or_close_its_actions(self):
        prep = w.Row("meeting:2026-03-02:acme:prep", "Prep for the Acme call", work_type="Deliverable", status="Prepared")
        actions = [w.Row("meeting:2026-03-02:acme:send-proposal", "Send Acme the proposal", work_type="Commitment"),
                   w.Row("meeting:2026-03-02:acme:intro", "Introduce Acme to the accountant", work_type="Commitment")]
        self.clock.advance(days=1)
        prep, still_open = w.meeting_time_passed(prep, actions, self.clock)
        self.assertEqual(prep.closed_as, "Unverified")
        self.assertEqual(len(still_open), 2)
        prep2 = w.Row("meeting:2026-03-03:bo:prep", "Prep for Bo", status="Prepared")
        prep2, still_open = w.meeting_time_passed(prep2, actions, self.clock, notes_found=True)
        self.assertEqual((prep2.closed_as, len(still_open)), ("Completed", 2))   # held, and its actions are still owed

    def test_an_alert_going_quiet_is_not_a_repair(self):
        issue = w.Row("alert:make:lead-sync", "Lead sync failing", work_type="Monitored issue")
        w.alert_went_quiet(issue, self.clock)
        self.assertTrue(issue.open)
        self.assertIsNotNone(issue.next_check)
        w.alert_went_quiet(issue, self.clock, success_notice=True)
        self.assertEqual(issue.closed_as, "Completed")

    def test_an_outcome_no_app_can_show_is_said_once_and_not_nagged(self):
        row = w.Row("invoice:1042:payment", "Invoice 1042 paid?", status="Blocked", waiting_on="the customer")
        self.assertIn("can't see", w.outcome_not_visible(row, self.clock))
        self.assertTrue(row.open)
        self.assertGreater(row.next_check, self.clock.now())              # it is not due again tomorrow morning by default
        self.clock.advance(days=1)
        self.assertIsNone(w.outcome_not_visible(row, self.clock))

    def test_cancelled_work_stays_cancelled(self):
        q = w.Queue()
        key = "alert:oldco:automation-failing"
        row = q.record(key, "OldCo automation failing", self.clock.now(), source="gmail:a1", work_type="Monitored issue")
        w.owner_cancels(row, self.clock, "stop tracking this")
        for day in range(1, 4):
            self.clock.advance(days=1)
            self.assertIs(q.record(key, "OldCo automation failing", self.clock.now(), source="gmail:a%d" % (day + 1)), row)
        self.assertEqual((row.status, row.closed_as, len(q.rows)), ("Done", "Cancelled", 1))
        q.record(key, "OldCo automation failing", self.clock.now(), source="gmail:new-signin", materially_new=True)
        self.assertTrue(row.open)                                          # only something materially new reopens it

    def test_superseded_names_the_row_that_replaced_it(self):
        old, new = w.Row("deliverable:acme:proposal-v1", "Proposal v1"), w.Row("deliverable:acme:proposal-v2", "Proposal v2")
        w.supersede(old, new, self.clock)
        self.assertEqual(old.closed_as, "Superseded")
        self.assertIn("deliverable:acme:proposal-v2", old.result[-1])


class AssignmentsUpgrade(unittest.TestCase):
    """Add-only and resumable: an interrupted upgrade loses nothing and carries on."""
    def untouched(self, before, after):
        for part in ["status_options", "views", "rows", "schedule"]:
            self.assertEqual(before[part], after[part], part)
        self.assertEqual(after["properties"][:len(before["properties"])], before["properties"])

    def test_it_adds_the_nine_fields_and_touches_nothing_else(self):
        ws = w.old_workspace(); before = copy.deepcopy(ws)
        self.assertEqual(w.upgrade_to_1_0_0(ws), w.NEW_PROPERTIES)
        self.assertEqual(ws["version"], "1.0.0")
        self.untouched(before, ws)
        self.assertIn("On hold", ws["status_options"])                     # the owner's own option is still there
        self.assertIn("My board", ws["views"])

    def test_an_interrupted_upgrade_resumes_without_losing_anything(self):
        ws = w.old_workspace(); before = copy.deepcopy(ws)
        with self.assertRaises(w.Interrupted):
            w.upgrade_to_1_0_0(ws, stop_after=3)
        self.assertEqual(ws["version"], "0.6.0")                           # the version line did not move
        self.assertEqual(len(ws["properties"]), len(before["properties"]) + 3)
        self.untouched(before, ws)
        self.assertEqual(w.upgrade_to_1_0_0(ws), w.NEW_PROPERTIES[3:])    # only what was still missing
        self.assertEqual(ws["version"], "1.0.0")
        self.assertEqual(len(ws["properties"]), len(set(ws["properties"])))
        self.untouched(before, ws)

    def test_it_resumes_from_an_interruption_at_any_field(self):
        for done in range(len(w.NEW_PROPERTIES)):
            ws = w.old_workspace(); before = copy.deepcopy(ws)
            with self.assertRaises(w.Interrupted):
                w.upgrade_to_1_0_0(ws, stop_after=done)
            self.assertEqual(ws["version"], "0.6.0", done)
            self.assertNotIn("Sending: not set", ws["connections"], done)   # the lines come after the fields
            self.assertEqual(w.upgrade_to_1_0_0(ws), w.NEW_PROPERTIES[done:], done)
            self.assertEqual(ws["version"], "1.0.0", done)
            self.assertEqual(ws["connections"].count("Sending: not set"), 1, done)
            self.untouched(before, ws)

    def test_existing_owners_keep_the_old_sending_behaviour_until_they_answer(self):
        ws = w.old_workspace(); w.upgrade_to_1_0_0(ws)
        self.assertEqual(ws["connections"][-2:], ["Sending: not set", "Work lives in: not set"])
        self.assertEqual(ws["connections"][:4], w.old_workspace()["connections"])      # nothing the owner chose was touched
        self.assertIsNone(w.sending_choice({"Sending": "not set"}))                    # not set: replies are left for them

    def test_running_it_twice_changes_nothing(self):
        ws = w.old_workspace(); w.upgrade_to_1_0_0(ws); once = copy.deepcopy(ws)
        self.assertEqual(w.upgrade_to_1_0_0(ws), [])
        self.assertEqual(ws, once)

    def test_a_failed_write_is_never_reported_as_done(self):
        ws = w.old_workspace(); before = copy.deepcopy(ws)
        with self.assertRaises(w.Interrupted):
            w.upgrade_to_1_0_0(ws, can_write=False)
        self.assertEqual(ws, before)

    def test_a_field_of_the_owners_with_the_same_name_is_kept(self):
        ws = w.old_workspace(); ws["properties"].append("Due")
        added = w.upgrade_to_1_0_0(ws)
        self.assertNotIn("Due", added)
        self.assertEqual(ws["properties"].count("Due"), 1)


def reply_card(who, clock, days_waiting=0, **kw):
    kw.setdefault("recipient", who.lower() + "@example.com")
    kw.setdefault("thread", "t-" + who.lower())
    kw.setdefault("text", "Hi %s, Thursday at 11 works." % who)
    kw.setdefault("draft_id", "d-" + who.lower())
    kw.setdefault("row", w.Row("gmail-thread:%s:reply" % kw["thread"], "Reply to " + who, work_type="Reply", status="Prepared"))
    return w.Card("reply", who, subject="Re: Thursday", waiting_since=clock.now() - w.timedelta(days=days_waiting), **kw)


class TheDesk(unittest.TestCase):
    def test_waiting_people_first_oldest_first_as_one_list(self):
        clock = monday_morning()
        cards = [w.Card("decision", "Refund for Omar", waiting_since=clock.now() - w.timedelta(days=5)),
                 w.Card("prepared", "Priority: workshop email", waiting_since=clock.now() - w.timedelta(days=6)),
                 reply_card("Sam", clock, days_waiting=1), reply_card("Dana", clock, days_waiting=2),
                 w.Card("handed", "Update the card on file", waiting_since=clock.now() - w.timedelta(days=7)),
                 w.Card("still-want", "Vendor shortlist", waiting_since=clock.now() - w.timedelta(days=9))]
        self.assertEqual([c.who for c in w.desk(cards)],
                         ["Dana", "Sam", "Refund for Omar", "Priority: workshop email", "Update the card on file", "Vendor shortlist"])

    def test_the_desk_reads_lists_only_and_never_the_inbox(self):
        import inspect
        self.assertEqual(list(inspect.signature(w.desk).parameters), ["cards"])


class SendingOnTheOwnersYes(unittest.TestCase):
    def setUp(self):
        self.clock, self.out = monday_morning(), w.Outbox()
        self.on = {"Sending": w.SEND}
        self.card = reply_card("Priya", self.clock, days_waiting=1)
        self.out.add_draft(self.card)

    def test_a_yes_on_one_card_sends_exactly_the_shown_text_once(self):
        self.assertEqual(w.send_on_yes(self.card, self.out, self.on, self.clock), "sent")
        self.assertEqual(self.out.sent, [self.card.shown()])
        self.assertEqual(self.out.send_calls, 1)
        self.assertEqual((self.card.row.status, self.card.row.closed_as), ("Done", "Sent"))
        self.assertTrue(self.card.row.evidence)                                    # the receipt
        self.assertEqual(self.out.deleted, [self.card.draft_id])                   # the one deletion: its own leftover draft
        self.assertNotIn(self.card.draft_id, self.out.drafts)

    def test_looks_good_or_ok_is_never_a_send(self):
        for word in ["looks good", "ok", "OK.", "fine", "thanks", "ok thanks", "Great!"]:
            self.assertEqual(w.send_on_yes(self.card, self.out, self.on, self.clock, answer=word), "nothing sent: ask which", word)
        self.assertEqual((self.out.sent, self.out.send_calls), ([], 0))

    def test_existing_owners_keep_the_old_behaviour_until_they_answer(self):
        for settings in [{}, {"Sending": "not set"}, {"Sending": ""}]:
            self.assertTrue(w.send_on_yes(self.card, self.out, settings, self.clock).startswith("ask once"))
        self.assertEqual(w.send_on_yes(self.card, self.out, {"Sending": w.LEAVE}, self.clock), "left for the owner to send")
        self.assertEqual(self.out.sent, [])
        self.assertEqual(self.card.row.status, "Handed to you")
        self.assertIn(self.card.draft_id, self.out.drafts)                         # their draft is where it was

    def test_any_material_change_needs_a_fresh_yes(self):
        self.out.drafts[self.card.draft_id] = (self.card.recipient, self.card.thread, self.card.text + " PS: bring the contract.", ())
        self.assertTrue(w.send_on_yes(self.card, self.out, self.on, self.clock).startswith("show the card again"))   # the owner's own edit counts
        self.out.add_draft(self.card)
        self.out.newer_message.add(self.card.thread)                               # the person wrote again
        self.assertTrue(w.send_on_yes(self.card, self.out, self.on, self.clock).startswith("show the card again"))
        self.assertEqual(self.out.sent, [])

    def test_a_vanished_draft_is_not_sent_from_memory(self):
        self.out.drafts.clear()
        self.assertTrue(w.send_on_yes(self.card, self.out, self.on, self.clock).startswith("not sent: the draft is gone"))
        self.assertEqual(self.out.send_calls, 0)

    def test_a_sent_reply_moves_the_case_to_waiting_on_the_customer(self):
        self.card.case = w.Row("case:priya:late-order", "Priya's late order", work_type="Customer case", status="In progress")
        w.send_on_yes(self.card, self.out, self.on, self.clock)
        self.assertTrue(self.card.case.open)
        self.assertEqual(self.card.case.next_move, "the customer")

    def test_highlevel_without_permission_falls_back_to_copying(self):
        out = w.Outbox(allows_send=False)
        card = reply_card("Lena", self.clock, channel="highlevel"); out.add_draft(card)
        self.assertTrue(w.send_on_yes(card, out, self.on, self.clock).startswith("not sent: give the text to copy"))
        self.assertTrue(card.row.open)

    def test_never_in_an_unattended_run_or_by_a_team_member_even_with_the_setting_on(self):
        self.assertTrue(w.send_on_yes(self.card, self.out, self.on, self.clock, attended=False).startswith("refused"))
        self.assertTrue(w.send_on_yes(self.card, self.out, self.on, self.clock, started_by_task=True).startswith("refused"))
        self.assertIn("clear my desk", w.send_on_yes(self.card, self.out, self.on, self.clock, started_by_task=True))   # the shortest way back
        self.assertTrue(w.send_on_yes(self.card, self.out, self.on, self.clock, as_agent="sales-manager").startswith("refused"))
        self.assertEqual(self.out.send_calls, 0)


class UnknownSendOutcome(unittest.TestCase):
    def setUp(self):
        self.clock, self.out = monday_morning(), w.Outbox()
        self.card = reply_card("Dana", self.clock); self.out.add_draft(self.card)

    def test_it_is_reconciled_against_sent_before_any_retry(self):
        self.out.fail = "timeout after sending"                                    # it went, but the answer never came back
        self.assertEqual(w.send_on_yes(self.card, self.out, {"Sending": w.SEND}, self.clock), "sent")
        self.assertEqual((len(self.out.sent), self.out.send_calls), (1, 1))        # found in Sent: no second send

    def test_not_in_sent_means_ask_never_send_twice_blind(self):
        self.out.fail = "timeout before sending"
        outcome = w.send_on_yes(self.card, self.out, {"Sending": w.SEND}, self.clock)
        self.assertTrue(outcome.startswith("unknown"))
        self.assertEqual((self.out.sent, self.out.send_calls), ([], 1))            # one attempt, no blind retry
        self.assertTrue(self.card.row.open)                                        # and nothing is recorded as sent
        self.assertIn(self.card.draft_id, self.out.drafts)                         # the draft is only removed after a confirmed send


class SendAllReady(unittest.TestCase):
    def setUp(self):
        self.clock, self.out, self.on = monday_morning(), w.Outbox(), {"Sending": w.SEND}
        self.listed = [reply_card("Dana", self.clock, 2), reply_card("Sam", self.clock, 1), reply_card("Lena", self.clock, 0)]
        for c in self.listed:
            self.out.add_draft(c)

    def test_one_yes_sends_exactly_the_listed_items_and_nothing_added_later(self):
        late = reply_card("Marco", self.clock); self.out.add_draft(late)           # joined the desk after the card was shown
        result = w.send_all_ready(self.listed, self.out, self.on, self.clock)
        self.assertEqual(result["went"], ["Dana", "Sam", "Lena"])
        self.assertEqual([s[0] for s in self.out.sent], [c.recipient for c in self.listed])
        self.assertIn(late.draft_id, self.out.drafts)
        self.assertTrue(late.row.open)

    def test_an_item_that_changed_is_left_unsent_and_named(self):
        self.out.newer_message.add(self.listed[1].thread)
        result = w.send_all_ready(self.listed, self.out, self.on, self.clock)
        self.assertEqual(result["went"], ["Dana", "Lena"])
        self.assertEqual(result["did not"][0][0], "Sam")

    def test_ok_over_several_items_sends_nothing_and_asks_which(self):
        result = w.send_all_ready(self.listed, self.out, self.on, self.clock, answer="looks good")
        self.assertEqual((result["went"], self.out.sent), ([], []))
        self.assertEqual(len(result["did not"]), 3)

    def test_a_paid_invoices_reminder_is_not_sent(self):
        paid = reply_card("Brightside", self.clock, invoice="INV-1043"); self.out.add_draft(paid)
        owed = reply_card("Harbor", self.clock, invoice="INV-1051"); self.out.add_draft(owed)
        unknown = reply_card("Northside", self.clock, invoice="INV-1060"); self.out.add_draft(unknown)
        result = w.send_all_ready([paid, owed, unknown], self.out, self.on, self.clock,
                                  invoice_unpaid={"INV-1043": False, "INV-1051": True})       # re-checked right before sending
        self.assertEqual(result["went"], ["Harbor"])
        self.assertEqual({who for who, why in result["did not"]}, {"Brightside", "Northside"})

    def test_unattended_stays_blocked_for_every_item(self):
        result = w.send_all_ready(self.listed, self.out, self.on, self.clock, attended=False)
        self.assertEqual((result["went"], self.out.send_calls), ([], 0))


class TheBriefing(unittest.TestCase):
    def test_a_customer_waiting_two_days_is_the_first_line_of_today(self):
        clock = w.Clock.at_local(2026, 3, 5, 7, 30)                               # Thursday morning
        dana = reply_card("Dana", clock); dana.waiting_since = clock.local_time(2026, 3, 3, 8, 0)   # wrote Tuesday
        sam = reply_card("Sam", clock); sam.waiting_since = clock.local_time(2026, 3, 4, 16, 0)     # wrote yesterday
        lines = w.today_lines([sam, dana], clock, other_priorities=["Prep for the 2 PM Acme call"])
        self.assertEqual(lines[0], "Dana has waited 2 days; reply ready")
        self.assertEqual(lines[1], "Prep for the 2 PM Acme call")                  # one working day is not yet "waiting"

    def test_a_weekend_is_not_counted_as_waiting(self):
        clock = w.Clock.at_local(2026, 3, 9, 7, 30)                                # Monday
        self.assertEqual(w.working_days_waited(clock, clock.local_time(2026, 3, 6, 17, 0)), 1)    # wrote Friday evening

    def test_a_customer_who_followed_up_again_leads_today_and_gets_no_approvals_row(self):
        clock = w.Clock.at_local(2026, 3, 5, 7, 30)
        dana = reply_card("Dana", clock); dana.waiting_since = clock.local_time(2026, 3, 2, 9, 0)
        made = w.follow_up_arrived(dana, "Any update on my refund?")
        self.assertEqual(made, {"drafts": 1, "approvals rows created": 0, "kind": "reply"})        # still one ready reply
        self.assertIn("Any update on my refund?", dana.text)                       # the same draft, refreshed
        self.assertEqual(w.today_lines([dana], clock)[0], "Dana followed up again; reply ready")

    def test_needs_you_counts_everything_waiting_on_the_owner(self):
        self.assertEqual(w.needs_you_count(approvals_pending=0, ready_replies=6, prepared_pieces=3, handed_to_owner=2), 11)

    def test_an_item_named_in_two_briefings_becomes_one_desk_card(self):
        clock, listed = monday_morning(), []
        seen = []
        for _ in range(5):                                                         # five mornings, untouched
            name_it, desk_card, listed = w.briefing_listing(listed, clock.local().date())
            seen.append((name_it, desk_card))
            clock.advance(days=1)
        self.assertEqual(seen, [(True, False), (True, False), (False, True), (False, True), (False, True)])
        self.assertEqual(len(listed), 2)                                            # two "Listed <date>" lines, never more

    def test_clear_first(self):
        self.assertTrue(w.optional_work_allowed(5))
        self.assertFalse(w.optional_work_allowed(6))

    def test_the_draft_cap_follows_how_fast_the_owner_clears_them(self):
        self.assertEqual(w.reply_draft_limit(waiting_now=2, waiting_at_last_briefing=None, cleared_all_yesterday=False), 5)
        self.assertEqual(w.reply_draft_limit(waiting_now=0, waiting_at_last_briefing=4, cleared_all_yesterday=True), 8)
        self.assertEqual(w.reply_draft_limit(waiting_now=7, waiting_at_last_briefing=4, cleared_all_yesterday=False), 3)
        self.assertEqual(w.reply_draft_limit(waiting_now=3, waiting_at_last_briefing=4, cleared_all_yesterday=False), 5)

    def test_a_recurring_job_that_left_no_record_is_said_once(self):
        clock = w.Clock.at_local(2026, 3, 9, 7, 30)                                # Monday
        expected = {"invoice review": clock.local_time(2026, 3, 6, 8, 0), "daily briefing": clock.local_time(2026, 3, 8, 7, 0)}
        records = {"invoice review": clock.local_time(2026, 2, 27, 9, 5), "daily briefing": clock.local_time(2026, 3, 8, 7, 31)}
        self.assertEqual(w.missed_runs(expected, records, clock), ["Your invoice review hasn't left a record since Friday"])
        self.assertEqual(w.missed_runs(expected, records, clock, already_said=("invoice review",)), [])
        records["invoice review"] = clock.local_time(2026, 3, 6, 9, 0)             # it ran after all
        self.assertEqual(w.missed_runs(expected, records, clock), [])
        self.assertEqual(w.missed_runs({"weekly marketing plan": clock.local_time(2026, 3, 9, 6, 0)}, {}, clock),
                         ["Your weekly marketing plan hasn't left a record since it was set up"])


class PlainLanguageControl(unittest.TestCase):
    def setUp(self):
        self.clock = monday_morning()
        self.row = w.Row("gmail-thread:t9:reply-landlord", "the reply to your landlord", work_type="Reply", status="Prepared")

    def test_one_reply_to_one_person_takes_the_fast_path(self):
        fast = w.route_request()
        self.assertEqual((fast["path"], fast["plan table"], fast["members launched"], fast["drafts"], fast["assignments rows"]),
                         ("fast", False, 0, 1, 1))
        self.assertTrue(fast["ready check"])                                       # the draft is still checked
        for involves in w.CONSEQUENTIAL:
            self.assertEqual(w.route_request(involves=(involves,))["path"], "full procedure", involves)
        self.assertEqual(w.route_request(parts=3)["path"], "full procedure")
        self.assertEqual(w.route_request(people=4)["path"], "full procedure")
        self.assertEqual(w.route_request(facts_in_brain=False)["path"], "full procedure")

    def test_the_answer_is_two_lines_and_offers_to_send_only_when_the_setting_is_on(self):
        on = w.fast_path_answer("Hi Priya, Thursday at 11 works.", "(draft link)", {"Sending": w.SEND})
        self.assertEqual((len(on), on[1]), (2, "Say 'send it' and it goes."))
        for settings in [{}, {"Sending": w.LEAVE}]:
            self.assertNotIn("send it", w.fast_path_answer("Hi Priya, Thursday at 11 works.", "(draft link)", settings)[1])

    def test_a_clear_reference_is_resolved_directly(self):
        other = w.Row("gmail-thread:t3:reply-sam", "the reply to Sam")
        self.assertIs(w.resolve_reference("it", [self.row]), self.row)
        self.assertIsNone(w.resolve_reference("it", [self.row, other]))            # several, and it matters: ask
        self.assertIs(w.resolve_reference("this", [self.row, other], would_differ=False), self.row)

    def test_the_same_item_is_updated_and_confirmed_in_one_line(self):
        line = w.steer(self.row, "Snooze it until Tuesday", self.clock, until=self.clock.local_time(2026, 3, 3, 9, 0))
        self.assertEqual(line, "Snoozed until Tuesday 9 AM: the reply to your landlord")
        self.assertEqual(self.row.status, "Prepared")
        line = w.steer(self.row, "I'm waiting on Dana until Friday", self.clock, who="Dana", until=self.clock.local_time(2026, 3, 6, 9, 0))
        self.assertEqual((self.row.status, self.row.waiting_on), ("Blocked", "Dana"))
        self.assertIn("Friday", line); self.assertNotIn("suggested", line)
        line = w.steer(self.row, "Remind me if they haven't replied", self.clock, who="Dana")
        self.assertIn("a suggested check", line)                                   # no day was given, and it says so
        w.steer(self.row, "That's already done", self.clock)
        self.assertEqual(self.row.closed_as, "Completed")
        again = w.Row("alert:oldco:sync", "the OldCo sync alerts")
        self.assertEqual(w.steer(again, "Stop tracking this", self.clock), "Stopped tracking: the OldCo sync alerts")
        self.assertEqual(again.closed_as, "Cancelled")

    def test_a_style_preference_is_saved_without_a_second_ask_but_a_hiding_rule_is_confirmed(self):
        self.assertEqual(w.save_preference("style"), "save now, confirm after")
        self.assertEqual(w.save_preference("working"), "save now, confirm after")
        self.assertEqual(w.save_preference("hides items"), "confirm first")
        self.assertEqual(w.save_preference("price or policy"), "confirm first")
        self.assertEqual(w.save_preference("style", stated_outright=False), "confirm first")
        self.assertTrue(w.save_preference("sending or spending").startswith("never saved"))   # a preference grants no permission


class ReachTheWork(unittest.TestCase):
    def test_the_question_is_neutral_and_names_no_product(self):
        self.assertEqual(len(w.WORK_LIVES_CHOICES), 6)
        for choice in w.WORK_LIVES_CHOICES:
            self.assertNotIn("highlevel", choice.lower())

    def test_finish_names_one_fix_for_a_place_the_team_cannot_read(self):
        self.assertEqual(w.unreachable_work(["Gmail", "A CRM or help desk"], connected=["Gmail"]), ["A CRM or help desk"])
        self.assertEqual(w.unreachable_work(["Gmail"], connected=["Gmail"]), [])
        self.assertEqual(w.one_fix("your help desk", registry_has_it=True), "connect your help desk")
        self.assertEqual(w.one_fix("Text messages"), "forward those messages to your connected inbox")
        self.assertEqual(w.one_fix("Text messages", inbox_connected=False), "paste them into your Paste Box")

    def test_a_goal_is_proposed_only_from_what_the_team_saw_and_nothing_is_saved(self):
        question, saved = w.propose_goal([], {"pricing": 6, "refunds": 2})
        self.assertIn("6 customers asked about pricing", question)
        self.assertEqual(saved, [])
        self.assertEqual(w.propose_goal([], {}), (None, []))                       # nothing seen: no invented goal
        self.assertEqual(w.propose_goal(["Fill the March workshop"], {"pricing": 6}), (None, []))


class MorningRunByDefault(unittest.TestCase):
    def test_one_ok_schedules_it_and_the_test_run_is_only_a_success_with_its_record(self):
        tasks = []
        self.assertEqual(w.morning_run_in_setup("ok", tasks), ("scheduled, confirmed", "test run succeeded: its Briefings row exists"))
        self.assertEqual(len(tasks), 1)
        state, what = w.morning_run_in_setup("OK!", [], briefing_row_appears=False)
        self.assertIn("not reported as a success", what)

    def test_a_different_time_is_a_yes(self):
        self.assertEqual(w.morning_run_in_setup("7:15 am", [])[0], "scheduled, confirmed")
        self.assertEqual(w.morning_run_in_setup("make it 8 AM", [])[0], "scheduled, confirmed")

    def test_an_unclear_reply_leaves_it_proposed_never_silently_scheduled(self):
        for reply in ["hmm", "what would it cost?", "maybe later", "tell me more", ""]:
            tasks = []
            self.assertEqual(w.morning_run_in_setup(reply, tasks)[0], "proposed, not scheduled", reply)
            self.assertEqual(tasks, [])
        self.assertEqual(w.morning_run_in_setup("no thanks", [])[0], "declined")

    def test_a_second_setup_never_creates_a_second_task(self):
        tasks = []
        w.morning_run_in_setup("ok", tasks)
        again = w.morning_run_in_setup("ok", tasks)
        self.assertEqual(len(tasks), 1)
        self.assertIn("never a second task", again[1])
        paused = ["[AI Workforce task: daily-executive-briefing | prompt version 0.8.0]"]          # an older, paused one counts too
        w.morning_run_in_setup("ok", paused)
        self.assertEqual(len(paused), 1)

    def test_without_run_now_the_offer_stays_and_says_why(self):
        self.assertEqual(w.morning_run_in_setup("ok", [], can_run_now=False),
                         ("scheduled, confirmed", "test run offered, with the reason it wasn't started"))
        self.assertEqual(w.morning_run_in_setup("ok", [], tool_available=False)[0], "not available on this account")

    def test_setup_is_finished_only_when_the_morning_run_is_settled(self):
        for state in ["scheduled, confirmed", "declined", "not available on this account"]:
            self.assertTrue(w.setup_finished(True, state), state)
        self.assertFalse(w.setup_finished(True, "proposed, not scheduled"))
        self.assertFalse(w.setup_finished(False, "scheduled, confirmed"))


class SetupStartsFromTheHandOff(unittest.TestCase):
    """1.1.0 step 8."""
    def test_one_responsibility_and_the_one_source_it_needs(self):
        self.assertEqual(w.first_job("answering customer emails", {"email", "calendar"}), ("the quick look", "email", False))
        self.assertEqual(w.first_job("scheduling meetings", {"email", "calendar"})[:2], ("the next 48 hours and one meeting prep", "calendar"))
        self.assertEqual(w.first_job("chasing invoices", {"email", "invoices"})[1], "invoices")

    def test_no_answer_or_nothing_the_team_can_do_yet_falls_back_and_says_so(self):
        self.assertEqual(w.first_job("", {"email"}), ("the quick look", "email", False))
        self.assertEqual(w.first_job("chasing invoices", {"email"}), ("the quick look", "email", True))     # no invoice source yet: say so
        self.assertEqual(w.first_job("doing my taxes", {"calendar"}), ("the next 48 hours and one meeting prep", "calendar", True))
        self.assertEqual(w.first_job("", set())[:2], ("pasted emails", "paste"))

    def test_every_card_in_one_message_under_one_checklist(self):
        chosen = ["Notion", "Gmail", "Google Calendar", "Google Drive"]
        cards, line = w.connect_checklist(chosen, {"Notion", "Google Calendar"}, needed="Gmail")
        self.assertEqual(cards, ["Gmail", "Google Drive"])                           # both at once, the needed one first
        self.assertEqual(line, "2 of 4 connected · Gmail: needed for your first job · Google Drive: optional, skip")
        cards, line = w.connect_checklist(chosen, set(), needed="Gmail")
        self.assertEqual(cards[:2], ["Notion", "Gmail"])
        self.assertEqual(w.connect_checklist(chosen, set(chosen), "Gmail")[0], [])   # nothing left to show

    def test_the_first_job_does_not_wait_for_optional_apps(self):
        self.assertTrue(w.can_start_first_job({"Notion", "Gmail"}, "Gmail"))         # calendar and files still waiting
        self.assertFalse(w.can_start_first_job({"Gmail"}, "Gmail"))                  # nowhere to save it yet
        self.assertFalse(w.can_start_first_job({"Notion", "Google Calendar"}, "Gmail"))

    def test_an_existing_workspace_opens_with_where_things_stand(self):
        brain = {"connections": {"Email": "Gmail", "Calendar": "Google Calendar", "Files": "None", "Notion": "Notion"}, "finished_runs": 1}
        self.assertEqual(w.setup_opening(brain), "Found your Business Brain: 3 apps connected, first job done. Carry on from here?")
        self.assertEqual(w.setup_opening(None), "questions")

    def test_a_connection_check_or_an_empty_report_is_never_the_first_success(self):
        self.assertFalse(w.first_success({"kind": "connection check", "saved_and_fetched_back": True, "items": 4}))
        self.assertFalse(w.first_success({"kind": "job", "saved_and_fetched_back": True, "items": 0}))
        self.assertFalse(w.first_success({"kind": "job", "saved_and_fetched_back": False, "items": 2}))
        self.assertTrue(w.first_success({"kind": "job", "saved_and_fetched_back": True, "items": 2}))


if __name__ == "__main__":
    unittest.main()
