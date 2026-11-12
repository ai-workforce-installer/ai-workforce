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


if __name__ == "__main__":
    unittest.main()
