"""Scenario tests for the run-tracking and inbox-checkpoint design (see run_logic.py)."""
import sys, unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_logic import (Record, Message, Mailbox, OpenWork, decide, make_run_id, next_window,
                       triage, last_checkpoint)

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
        self.assertEqual(q.open_items(), [])

    def test_queue_unreadable_keeps_bookmark_and_creates_no_duplicates(self):
        msgs = mail(10, T0 - timedelta(hours=5), every_important=1)
        recs, actions, q = [], [], OpenWork()
        first = Record("IT-0", "Inbox triage", T0 - timedelta(days=1), finished=T0 - timedelta(days=1),
                       result="Complete", completed_through=T0 - timedelta(hours=6))
        recs.append(first)
        q.readable = False
        r = triage(recs, Mailbox(msgs), T0, actions=actions, draft_limit=3, queue=q)
        self.assertEqual(r.result, "Partial")
        self.assertEqual(r.completed_through, first.completed_through)
        self.assertEqual(q.rows, {})

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


if __name__ == "__main__":
    unittest.main()
