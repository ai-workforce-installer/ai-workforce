"""Scenario tests for the run-tracking and inbox-checkpoint design (see run_logic.py)."""
import sys, unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_logic import (start_together, bookmark_check, pagination_check, Report, send_with_recovery, open_gaps, backfill, search_all,
                       Record, Message, Mailbox, OpenWork, decide, make_run_id, next_window,
                       triage, last_checkpoint, notify_due, morning_inbox_plan, morning_run,
                       handled_line, handled_nothing, morning_opening, quiet_streak_notice, WINDOW_OVERLAP)

T0 = datetime(2026, 11, 5, 8, 0)


def mail(n, start, step_min=5, every_important=10, archived_every=4):
    """n messages from `start`, some archived (no INBOX label), some important."""
    out = []
    for i in range(n):
        labels = () if i % archived_every == 0 else ("INBOX", "CATEGORY_PROMOTIONS")
        out.append(Message(f"m{i:04d}", start + timedelta(minutes=step_min * i), labels,
                           important=(i % every_important == 0)))
    return out


class RunIdentity(unittest.TestCase):
    def test_two_legitimate_runs_same_day_are_separate(self):
        recs = []
        msgs = mail(30, T0 - timedelta(hours=20))
        r1 = triage(recs, Mailbox(msgs), T0 + timedelta(hours=1))
        r2 = triage(recs, Mailbox(msgs), T0 + timedelta(hours=4))
        self.assertNotEqual(r1.run_id, r2.run_id)
        self.assertEqual(len(recs), 2)
        self.assertEqual(r2.window[0], r1.completed_through - timedelta(minutes=15))

    def test_overlapping_run_does_not_start(self):
        recs = [Record("IT-1", "Inbox triage", T0)]           # unfinished, started now-10min
        kind, _ = decide(recs, "Inbox triage", T0 + timedelta(minutes=10))
        self.assertEqual(kind, "overlap")

    def test_interrupted_run_is_resumed_not_duplicated(self):
        msgs = mail(40, T0 - timedelta(hours=20))
        recs, actions = [], []
        start, end, _ = next_window(recs, T0)
        stuck = Record("IT-20261105-0800", "Inbox triage", T0, window=(start, end))
        stuck.handled = {"gmail:m0000", "gmail:m0010"}
        actions += [("draft", "gmail:m0000"), ("draft", "gmail:m0010")]
        recs.append(stuck)
        r = triage(recs, Mailbox(msgs), T0 + timedelta(hours=1), actions=actions)
        self.assertIs(r, stuck)
        self.assertEqual(len(recs), 1)
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)), "a draft was created twice")
        self.assertEqual(r.resumed, 1)

    def test_long_run_with_recent_progress_is_not_taken_over(self):
        rec = Record("IT-1", "Inbox triage", T0, last_progress=T0 + timedelta(minutes=50))
        self.assertEqual(decide([rec], "Inbox triage", T0 + timedelta(minutes=70))[0], "overlap")

    def test_record_older_than_a_day_is_abandoned(self):
        rec = Record("IT-1", "Inbox triage", T0 - timedelta(hours=30))
        kind, _ = decide([rec], "Inbox triage", T0)
        self.assertEqual(kind, "new")
        self.assertEqual(rec.result, "Failed")

    def test_customer_only_runs_never_block_or_set_the_bookmark(self):
        cs = Record("CS-1", "Inbox triage", T0, code="CS")
        self.assertEqual(decide([cs], "Inbox triage", T0 + timedelta(minutes=5))[0], "new")
        cs.finished, cs.completed_through = T0, T0
        self.assertIsNone(last_checkpoint([cs]))

    def test_other_types_do_not_block(self):
        recs = [Record("DB-1", "Daily briefing", T0)]
        self.assertEqual(decide(recs, "Inbox triage", T0 + timedelta(minutes=5))[0], "new")

    def test_run_ids_unique_on_collision(self):
        recs = [Record("IT-20261105-0800", "Inbox triage", T0, finished=T0)]
        self.assertEqual(make_run_id("IT", T0, recs), "IT-20261105-0800-2")


class Coverage(unittest.TestCase):
    def test_archived_and_categorized_mail_is_found(self):
        msgs = mail(20, T0 - timedelta(hours=10), every_important=1)
        recs, actions = [], []
        triage(recs, Mailbox(msgs), T0, actions=actions, draft_limit=100)
        handled = {k for _, k in actions}
        archived = {f"gmail:{m.id}" for m in msgs if "INBOX" not in m.labels}
        self.assertTrue(archived and archived <= handled)

    def test_large_inbox_all_pages(self):
        msgs = mail(230, T0 - timedelta(hours=23), step_min=6, every_important=1)
        recs, actions = [], []
        r = triage(recs, Mailbox(msgs), T0, actions=actions, draft_limit=1000)
        self.assertEqual(len(actions), 230)
        self.assertEqual(r.result, "Complete")

    def test_failed_page_keeps_bookmark_and_next_run_catches_up(self):
        msgs = mail(180, T0 - timedelta(hours=20), step_min=6, every_important=1)
        recs, actions = [], []
        first = Record("IT-0", "Inbox triage", T0 - timedelta(days=1),
                       finished=T0 - timedelta(days=1), result="Complete",
                       completed_through=T0 - timedelta(hours=21))
        recs.append(first)
        box = Mailbox(msgs, fail_on_page=2)
        box.retry_used.add(2)                       # the one retry also fails
        r1 = triage(recs, box, T0, actions=actions, draft_limit=1000)
        self.assertEqual(r1.result, "Partial")
        self.assertEqual(r1.completed_through, first.completed_through, "bookmark moved on a partial scan")
        r2 = triage(recs, Mailbox(msgs), T0 + timedelta(hours=2), actions=actions, draft_limit=1000)
        self.assertEqual(r2.result, "Complete")
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)), "a message was processed twice")
        self.assertEqual(set(keys), {f"gmail:{m.id}" for m in msgs}, "a message was missed")

    def test_transient_page_failure_is_retried_once(self):
        msgs = mail(120, T0 - timedelta(hours=20), step_min=6)
        r = triage([], Mailbox(msgs, fail_on_page=1), T0)
        # fail_on_page stays set, so the retry also fails -> Partial
        self.assertEqual(r.result, "Partial")

    def test_draft_limit_carries_over_and_next_run_picks_up(self):
        msgs = mail(40, T0 - timedelta(hours=20), every_important=1)
        recs, actions, q = [], [], OpenWork()
        r1 = triage(recs, Mailbox(msgs), T0, actions=actions, draft_limit=5, queue=q)
        self.assertEqual(len(r1.pending), 35)
        self.assertEqual(r1.result, "Complete")            # search complete, work queued
        self.assertEqual(r1.completed_through, T0)
        for i in range(1, 10):
            triage(recs, Mailbox(msgs), T0 + timedelta(hours=i), actions=actions, draft_limit=5, queue=q)
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), {f"gmail:{m.id}" for m in msgs})

    def test_overlap_window_never_duplicates(self):
        msgs = mail(60, T0 - timedelta(hours=10), step_min=10, every_important=1)
        recs, actions = [], []
        for h in (0, 3, 6, 9):
            triage(recs, Mailbox(msgs), T0 + timedelta(hours=h), actions=actions, draft_limit=1000)
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)))

    def test_long_gap_is_reported(self):
        recs = [Record("IT-0", "Inbox triage", T0 - timedelta(days=10), finished=T0 - timedelta(days=10),
                       completed_through=T0 - timedelta(days=10))]
        start, end, gap = next_window(recs, T0)
        self.assertEqual(end - start, timedelta(days=7))
        self.assertIsNotNone(gap)

    def test_first_run_uses_24_hours(self):
        start, end, gap = next_window([], T0)
        self.assertEqual(end - start, timedelta(hours=24))
        self.assertIsNone(gap)
        self.assertIsNone(last_checkpoint([]))


class OpenWorkQueue(unittest.TestCase):
    def test_unresolved_work_survives_a_long_gap(self):
        msgs = mail(20, T0 - timedelta(hours=20), every_important=1)
        recs, actions, q = [], [], OpenWork()
        triage(recs, Mailbox(msgs), T0, actions=actions, draft_limit=5, queue=q)
        later = T0 + timedelta(days=21)                  # three weeks, far past any 7-day look-back
        for i in range(4):
            triage(recs, Mailbox([]), later + timedelta(hours=i), actions=actions, draft_limit=5, queue=q)
        self.assertEqual({k for _, k in actions}, {f"gmail:{m.id}" for m in msgs})
        self.assertEqual([k for k in q.open_items() if not k.startswith("inbox-gap:")], [])
        self.assertTrue(open_gaps(q))                   # the unscanned weeks are still tracked

    def test_queue_unreadable_carries_over_durably_and_creates_no_duplicates(self):
        msgs = mail(10, T0 - timedelta(hours=5), every_important=1)
        recs, actions, q = [], [], OpenWork()
        first = Record("IT-0", "Inbox triage", T0 - timedelta(days=1), finished=T0 - timedelta(days=1),
                       result="Complete", completed_through=T0 - timedelta(hours=6))
        recs.append(first)
        q.readable = False
        r = triage(recs, Mailbox(msgs), T0, actions=actions, draft_limit=3, queue=q)
        self.assertEqual(r.result, "Partial")
        self.assertEqual(r.completed_through, T0)        # search was complete; leftovers are in Carried over
        self.assertEqual(len(r.carried_over), 7)
        self.assertEqual(q.rows, {})                     # nothing written that might duplicate
        q.readable = True
        triage(recs, Mailbox([]), T0 + timedelta(hours=2), actions=actions, draft_limit=100, queue=q)
        keys = [k for _, k in actions]
        self.assertEqual(sorted(keys), sorted(f"gmail:{m.id}" for m in msgs))   # all done, once each
        self.assertEqual(len(keys), len(set(keys)))

    def test_one_row_per_source_and_action(self):
        q = OpenWork()
        q.upsert("gmail:a", "Planned"); q.upsert("gmail:a", "Planned"); q.upsert("gmail:a", "Prepared")
        self.assertEqual(len(q.rows), 1)
        self.assertEqual(q.writes, 2)


class Notifications(unittest.TestCase):
    def test_one_notification_per_run_even_when_resumed(self):
        msgs = mail(10, T0 - timedelta(hours=5))
        recs = []
        start, end, _ = next_window(recs, T0)
        stuck = Record("IT-1", "Inbox triage", T0, window=(start, end), notified=False)
        recs.append(stuck)
        r = triage(recs, Mailbox(msgs), T0 + timedelta(hours=1))
        self.assertTrue(r.notified)
        self.assertEqual(sum(1 for x in recs if x.notified), 1)


class CheckpointPolicy(unittest.TestCase):
    """The bookmark follows email search coverage, not the overall Result (self-test 6c checks the same)."""
    def setUp(self):
        self.recs = [Record("IT-0", "Inbox triage", T0 - timedelta(hours=6), finished=T0 - timedelta(hours=6),
                            result="Complete", completed_through=T0 - timedelta(hours=6))]
        self.msgs = mail(30, T0 - timedelta(hours=5), every_important=3)

    def test_partial_run_with_complete_email_search_moves_the_bookmark(self):
        r = triage(self.recs, Mailbox(self.msgs), T0, other_sources_ok=False)   # e.g. Notion pricing unreadable
        self.assertEqual(r.result, "Partial")
        self.assertTrue(r.search_complete)
        self.assertEqual(r.completed_through, T0)
        self.assertTrue(bookmark_check(self.recs))

    def test_incomplete_email_search_keeps_the_bookmark(self):
        r = triage(self.recs, Mailbox(self.msgs * 3, fail_on_page=0), T0)
        self.assertFalse(r.search_complete)
        self.assertEqual(r.completed_through, T0 - timedelta(hours=6))
        self.assertTrue(bookmark_check(self.recs))

    def test_bookmark_check_catches_a_wrong_move(self):
        r = triage(self.recs, Mailbox(self.msgs, fail_on_page=0), T0)
        r.completed_through = T0                          # moved although the search was incomplete
        self.assertFalse(bookmark_check(self.recs))

    def test_pagination_cap_with_another_page_is_incomplete(self):
        many = [Message(f"x{i}", T0 - timedelta(minutes=i)) for i in range(300)]   # 6 pages of 50
        self.assertEqual(pagination_check(Mailbox(many), T0 - timedelta(days=7), T0), "incomplete (stopped at 5 pages)")
        few = many[:120]
        self.assertEqual(pagination_check(Mailbox(few), T0 - timedelta(days=7), T0), "PASS")


class InboxGaps(unittest.TestCase):
    """inbox-coverage.md: a gap over 7 days becomes a durable row and is caught up 2 days per run."""
    def setUp(self):
        self.cp = T0 - timedelta(days=12)
        self.recs = [Record("IT-0", "Inbox triage", self.cp, finished=self.cp, result="Complete",
                            completed_through=self.cp)]
        # one important email every 6 hours across the whole 12 days
        self.msgs = [Message(f"m{i}", self.cp + timedelta(hours=6 * i), important=True) for i in range(48)]

    def test_gap_over_7_days_is_saved_and_reported(self):
        q = OpenWork()
        r = triage(self.recs, Mailbox(self.msgs), T0, queue=q, draft_limit=1000)
        self.assertEqual(r.window[1] - r.window[0], timedelta(days=7))
        self.assertEqual(len(open_gaps(q)), 1)           # still open after the first catch-up
        self.assertEqual(r.completed_through, T0)        # search coverage of its own window
        self.assertTrue(r.gaps_open)                     # so the report can't imply full coverage

    def test_later_runs_close_the_gap_without_missing_or_duplicating(self):
        q, actions = OpenWork(), []
        for d in range(5):
            triage(self.recs, Mailbox(self.msgs), T0 + timedelta(days=d), queue=q, actions=actions, draft_limit=1000)
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)))       # nothing twice
        self.assertEqual(set(keys), {f"gmail:{m.id}" for m in self.msgs})   # nothing missed
        self.assertEqual(open_gaps(q), [])
        self.assertEqual(len(q.gaps), 1)                  # one row, closed

    def test_failed_catch_up_leaves_the_gap_row_as_it_was(self):
        q = OpenWork()
        triage(self.recs, Mailbox(self.msgs), T0, queue=q, draft_limit=1000)
        before = open_gaps(q)
        class Flaky(Mailbox):
            def search(self, start, end, page):
                if end <= T0 - timedelta(days=6):         # only the gap searches fail
                    raise ConnectionError("down")
                return super().search(start, end, page)
        r = triage(self.recs, Flaky(self.msgs), T0 + timedelta(hours=2), queue=q, draft_limit=1000)
        self.assertEqual(open_gaps(q), before)
        self.assertEqual(r.result, "Complete")           # its own window was covered; the gap is tracked

    def test_overlapping_gaps_share_one_row(self):
        q = OpenWork()
        q.add_gap(T0 - timedelta(days=20), T0 - timedelta(days=10))
        q.add_gap(T0 - timedelta(days=12), T0 - timedelta(days=8))
        self.assertEqual(len(q.gaps), 1)
        self.assertEqual(open_gaps(q), [(T0 - timedelta(days=20), T0 - timedelta(days=8))])

    def test_owner_backfill_covers_the_requested_period(self):
        q, actions = OpenWork(), []
        q.add_gap(self.cp, T0 - timedelta(days=7))
        self.assertTrue(backfill(q, Mailbox(self.msgs), self.cp, T0 - timedelta(days=7), self.recs, actions))
        wanted = {f"gmail:{m.id}" for m in self.msgs if m.at < T0 - timedelta(days=7)}
        self.assertEqual({k for _, k in actions}, wanted)
        self.assertEqual(open_gaps(q), [])

    def test_unreadable_queue_reports_the_gap_instead(self):
        q = OpenWork(); q.readable = False
        r = triage(self.recs, Mailbox(self.msgs), T0, queue=q)
        self.assertTrue(any(c.startswith("inbox-gap") for c in r.carried_over))
        self.assertEqual(r.result, "Partial")


class NotificationRecovery(unittest.TestCase):
    """run-tracking.md section 5: finished work whose notification never went out."""
    NOW = T0 + timedelta(days=1)

    def notifier(self, *outcomes):
        calls, seq = [], list(outcomes)
        def send(links):
            calls.append(links)
            return seq.pop(0)
        return send, calls

    def test_interrupted_before_notifying_is_caught_up_without_redoing_work(self):
        old = Report("IT-1", "IT", T0, notified="pending")
        cur = Report("IT-2", "IT", self.NOW)
        send, calls = self.notifier("accepted")
        send_with_recovery(cur, [old], "IT", self.NOW, send)
        self.assertEqual(calls, [["IT-2", "IT-1"]])       # one notification, both links
        self.assertEqual((old.notified, old.work_done), ("accepted", 1))
        self.assertNotEqual(old.notified, "confirmed")   # accepted by the tool is not delivery

    def test_explicit_failure_is_retried_up_to_three_times(self):
        old = Report("IT-1", "IT", T0, notified="failed", attempts=["attempt 1: failed"])
        for i, outcome in enumerate(["failed", "failed", "failed"]):
            send, calls = self.notifier(outcome)
            send_with_recovery(Report(f"IT-{i+2}", "IT", self.NOW), [old], "IT", self.NOW, send)
        self.assertEqual(len(old.attempts), 3)           # the third run left it alone

    def test_permanent_failure_is_never_retried(self):
        old = Report("IT-1", "IT", T0, notified="failed (permanent)")
        send, calls = self.notifier("accepted")
        send_with_recovery(Report("IT-2", "IT", self.NOW), [old], "IT", self.NOW, send)
        self.assertEqual(calls, [["IT-2"]])

    def test_successful_retry(self):
        old = Report("IT-1", "IT", T0, notified="failed", attempts=["attempt 1: failed"])
        send, _ = self.notifier("confirmed")
        send_with_recovery(Report("IT-2", "IT", self.NOW), [old], "IT", self.NOW, send)
        self.assertEqual(old.notified, "confirmed")
        send, calls = self.notifier("accepted")
        send_with_recovery(Report("IT-3", "IT", self.NOW), [old], "IT", self.NOW, send)
        self.assertEqual(calls, [["IT-3"]])               # never sent again

    def test_unknown_outcome_retried_once_with_duplicate_warning(self):
        old = Report("IT-1", "IT", T0, notified="unknown", attempts=["attempt 1: unknown"])
        send, _ = self.notifier("unknown")
        send_with_recovery(Report("IT-2", "IT", self.NOW), [old], "IT", self.NOW, send)
        self.assertIn("may arrive twice", old.attempts[-1])
        send, calls = self.notifier("accepted")
        send_with_recovery(Report("IT-3", "IT", self.NOW), [old], "IT", self.NOW, send)
        self.assertEqual(calls, [["IT-3"]])

    def test_bounded_to_same_responsibility_and_8_days(self):
        other = Report("DB-1", "DB", T0, notified="pending")
        stale = Report("IT-0", "IT", self.NOW - timedelta(days=8, hours=1), notified="pending")
        send, calls = self.notifier("accepted")
        send_with_recovery(Report("IT-2", "IT", self.NOW), [other, stale], "IT", self.NOW, send)
        self.assertEqual(calls, [["IT-2"]])

    def test_weekly_report_missed_last_week_is_caught_up(self):
        old = Report("WM-1", "WM", self.NOW - timedelta(days=7), notified="failed", attempts=["attempt 1: failed"])
        send, calls = self.notifier("accepted")
        send_with_recovery(Report("WM-2", "WM", self.NOW), [old], "WM", self.NOW, send)
        self.assertEqual(calls, [["WM-2", "WM-1"]])

    def test_not_run_record_sends_nothing(self):
        old = Report("IT-1", "IT", T0, notified="pending")
        send, calls = self.notifier()
        self.assertIsNone(send_with_recovery(Report("IT-2", "IT", self.NOW), [old], "IT", self.NOW, send,
                                             sends_own=False))
        self.assertEqual((calls, old.notified), ([], "pending"))


class ConcurrentStarts(unittest.TestCase):
    """Best effort only: there is no atomic lock. The look-again step settles most same-minute starts;
    the duplicate checks are the backstop for retries."""
    def test_same_minute_starts_leave_one_session_working(self):
        recs = []
        proceed = start_together(recs, T0)
        self.assertEqual(len(proceed), 1)
        self.assertEqual(proceed[0].run_id, "IT-20261105-0800")
        self.assertEqual(sorted(r.result for r in recs if r.finished), ["Partial"])   # the other: Not run
        self.assertEqual(len({r.run_id for r in recs}), 2)

    def test_immediate_retry_creates_no_duplicate_work(self):
        msgs = mail(10, T0 - timedelta(hours=5), every_important=1)
        recs, actions, q = [], [], OpenWork()
        triage(recs, Mailbox(msgs), T0, actions=actions, queue=q, draft_limit=1000)
        triage(recs, Mailbox(msgs), T0, actions=actions, queue=q, draft_limit=1000)   # retry, same minute
        keys = [k for _, k in actions]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len({r.run_id for r in recs}), len(recs))

class MorningRun(unittest.TestCase):
    """0.8.0: the daily briefing does the inbox check itself. One run, one notification."""
    def test_one_run_two_records_one_notification(self):
        recs, actions = [], []
        briefing, inbox, sent = morning_run(recs, Mailbox(mail(60, T0 - timedelta(hours=20))), T0, actions=actions)
        self.assertEqual(sent, 1)
        self.assertEqual((briefing.rtype, briefing.result, inbox.rtype, inbox.result),
                         ("Daily briefing", "Complete", "Inbox triage", "Complete"))
        self.assertEqual(inbox.completed_through, T0)            # the inbox check keeps its own bookmark
        self.assertEqual(inbox.included_in, briefing.run_id)
        self.assertFalse(inbox.notified)
        self.assertTrue(actions)                                  # and it did the drafting

    def test_a_recent_separate_inbox_check_is_reused_not_repeated(self):
        recs, actions = [], []
        box = Mailbox(mail(40, T0 - timedelta(hours=10)))
        triage(recs, box, T0, actions=actions)                    # an owner who still has the separate task
        before = list(actions)
        briefing, inbox, sent = morning_run(recs, box, T0 + timedelta(minutes=10), actions=actions)
        self.assertEqual((briefing.inbox_plan, inbox, sent), ("reuse", None, 1))
        self.assertEqual(actions, before)
        self.assertEqual(len([r for r in recs if r.rtype == "Inbox triage"]), 1)
        self.assertEqual(briefing.result, "Complete")

    def test_an_old_check_means_the_briefing_checks_the_inbox_itself(self):
        recs, actions = [], []
        box = Mailbox(mail(80, T0 - timedelta(hours=20), step_min=20))
        first = triage(recs, box, T0, actions=actions)
        later = T0 + timedelta(hours=5)
        briefing, inbox, sent = morning_run(recs, box, later, actions=actions)
        self.assertEqual(briefing.inbox_plan, "run")
        self.assertEqual(inbox.window[0], first.completed_through - WINDOW_OVERLAP)
        self.assertEqual(len(actions), len({key for _, key in actions}))      # nothing drafted twice
        self.assertEqual(sent, 1)

    def test_an_inbox_check_in_progress_is_never_doubled_or_waited_for(self):
        running = Record("IT-20261105-0755", "Inbox triage", T0 - timedelta(minutes=5))
        recs = [running]
        briefing, inbox, sent = morning_run(recs, Mailbox(mail(10, T0 - timedelta(hours=2))), T0)
        self.assertEqual((briefing.inbox_plan, inbox, sent), ("running", None, 1))
        self.assertEqual(len([r for r in recs if r.rtype == "Inbox triage"]), 1)
        self.assertEqual(briefing.result, "Partial")              # email wasn't part of this briefing

    def test_no_inbox_at_all_is_still_a_complete_briefing(self):
        briefing, inbox, sent = morning_run([], Mailbox([]), T0, has_inbox=False)
        self.assertEqual((briefing.inbox_plan, inbox, briefing.result, sent), ("none", None, "Complete", 1))

    def test_a_failed_inbox_search_makes_the_morning_run_partial_and_keeps_the_bookmark(self):
        recs = []
        briefing, inbox, sent = morning_run(recs, Mailbox(mail(120, T0 - timedelta(hours=20)), fail_on_page=1), T0)
        self.assertEqual((inbox.result, briefing.result, sent), ("Partial", "Partial", 1))
        self.assertIsNone(inbox.completed_through)                # so the next run scans this window again

    def test_an_included_inbox_record_is_never_a_missed_notification(self):
        included = Report("IT-20261105-0800", "IT", T0, notified="not requested")
        self.assertFalse(notify_due(included, "IT", T0 + timedelta(days=1)))

    def test_an_extra_afternoon_check_still_works_and_notifies_on_its_own(self):
        recs, actions = [], []
        box = Mailbox(mail(100, T0 - timedelta(hours=20), step_min=20))
        _, morning_inbox, _ = morning_run(recs, box, T0, actions=actions)
        afternoon = triage(recs, box, T0 + timedelta(hours=7), actions=actions)
        self.assertEqual(afternoon.window[0], morning_inbox.completed_through - WINDOW_OVERLAP)
        self.assertTrue(afternoon.notified)
        self.assertEqual(len(actions), len({key for _, key in actions}))

    def test_plan_ignores_customer_only_and_quick_look_records(self):
        cs = Record("CS-20261105-0700", "Inbox triage", T0 - timedelta(hours=1), finished=T0 - timedelta(hours=1),
                    completed_through=T0 - timedelta(hours=1), code="CS")
        self.assertEqual(morning_inbox_plan([cs], T0), "run")     # customer-only runs never set the bookmark


class WorkHandled(unittest.TestCase):
    """0.8.0: a run is judged by what it handled, said first, never padded."""
    def test_reading_sorting_and_checking_never_count(self):
        looked = {"emails reviewed": 148, "calendar events checked": 12, "searches": 3}
        self.assertTrue(handled_nothing(looked))
        self.assertEqual(handled_line(looked, "nobody is waiting on a reply"),
                         "Handled: nothing: nobody is waiting on a reply")

    def test_real_work_is_counted_in_a_fixed_order(self):
        self.assertEqual(handled_line({"prepared": 1, "reply drafts": 3, "items closed": 2}),
                         "Handled: 3 reply drafts, 2 items closed, 1 prepared")

    def test_morning_opening_adds_the_inbox_work_and_nothing_is_counted_twice(self):
        briefing, inbox = {"prepared": 1}, {"reply drafts": 3, "approvals raised": 2}
        self.assertEqual(morning_opening(briefing, inbox, needs_you=2),
                         "Handled: 3 reply drafts, 2 approvals raised, 1 prepared. Needs you: 2 decisions")
        per_record = sum(sum(w.values()) for w in (briefing, inbox))    # what a team report adds up
        self.assertEqual(per_record, 6)

    def test_a_complete_run_can_still_have_handled_nothing(self):
        self.assertEqual(morning_opening({}, {"emails reviewed": 148}, reason="your customer messages are somewhere the team can't reach"),
                         "Handled: nothing: your customer messages are somewhere the team can't reach")

    def test_three_quiet_briefings_lead_with_the_fix_at_most_weekly(self):
        quiet, busy = {"emails reviewed": 90}, {"reply drafts": 2}
        today = T0.date()
        self.assertFalse(quiet_streak_notice([quiet, quiet], today))
        self.assertFalse(quiet_streak_notice([quiet, busy, quiet], today))
        self.assertTrue(quiet_streak_notice([quiet, quiet, quiet, busy], today))
        self.assertFalse(quiet_streak_notice([quiet, quiet, quiet], today, last_said=today - timedelta(days=3)))
        self.assertTrue(quiet_streak_notice([quiet, quiet, quiet], today, last_said=today - timedelta(days=7)))


if __name__ == "__main__":
    unittest.main()
