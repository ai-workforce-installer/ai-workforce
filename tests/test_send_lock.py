"""The send lock (plugins/ai-workforce/hooks): real code, tested directly.

Unlike the reference-model tests, this is the code that actually runs. The tests call it the
way Claude does: the hook input as JSON on standard input, the answer as an exit code
(2 = refuse, 0 = let through). They don't prove Claude runs plugin hooks on every surface;
tests/README.md says where that has been seen working.
"""
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "plugins" / "ai-workforce" / "hooks"
sys.dont_write_bytecode = True          # never leave a __pycache__ folder inside the plugin
spec = importlib.util.spec_from_file_location("send_lock", HOOKS / "send_lock.py")
send_lock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(send_lock)

TAG_PROMPT = "[AI Workforce task: daily-executive-briefing | prompt version 0.5.4]\nScheduled run of the AI Workforce daily executive briefing."

ALLOWED = """
mcp__Gmail__search_threads mcp__Gmail__get_thread mcp__Gmail__get_message mcp__Gmail__create_draft mcp__Gmail__update_draft
mcp__Gmail__get_draft mcp__Gmail__list_drafts mcp__Gmail__untrash_message mcp__Gmail__label_message
mcp__Google_Calendar__list_events mcp__Google_Calendar__get_event mcp__Google_Calendar__search_events mcp__Google_Calendar__suggest_time
mcp__Google_Drive__search_files mcp__Google_Drive__read_file_content mcp__Google_Drive__download_file_content
mcp__Google_Drive__get_file_permissions mcp__Google_Drive__list_shared_drives
mcp__Notion__notion-search mcp__Notion__notion-fetch mcp__Notion__notion-create-pages mcp__Notion__notion-update-page
mcp__Notion__notion-create-database mcp__Notion__notion-create-view mcp__Notion__notion-query-data-sources mcp__Notion__notion-move-pages
mcp__Notion__notion-list-shared-pages mcp__Notion__notion-calendar-list-events mcp__Notion__notion-create-meeting-note
mcp__plugin_ai-workforce_HighLevel__conversations_search-conversation mcp__plugin_ai-workforce_HighLevel__conversations_get-messages
mcp__plugin_ai-workforce_HighLevel__contacts_get-contact mcp__plugin_ai-workforce_HighLevel__calendars_get-calendar-events
mcp__HighLevel__payments_list-transactions mcp__HighLevel__emails_fetch-template mcp__HighLevel__social-media-posting_get-posts
mcp__HighLevel__search mcp__HighLevel__fetch mcp__HighLevel__search_operations mcp__HighLevel__describe_operation mcp__HighLevel__list_locations
mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__search_operations mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__describe_operation
mcp__cowork__send_notification mcp__x__send_user_message mcp__x__SendUserFile
mcp__stripe__list_refunds mcp__stripe__get_refund mcp__stripe__list_invoices mcp__stripe__retrieve_charge
mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__search_threads
mcp__claude-code-remote__list_triggers mcp__scheduled-tasks__list_scheduled_tasks mcp__x__create_task mcp__x__get_trigger
Bash Read Write WebFetch PushNotification SendUserMessage Agent
""".split()

REFUSED = """
mcp__Gmail__send_message mcp__Gmail__reply mcp__Gmail__forward mcp__Gmail__trash_message mcp__Gmail__trash_thread
mcp__Gmail__delete_draft mcp__Gmail__delete_label mcp__Gmail__mark_message_spam
mcp__Google_Calendar__create_event mcp__Google_Calendar__update_event mcp__Google_Calendar__delete_event mcp__Google_Calendar__respond_to_event
mcp__Google_Drive__share_file mcp__Google_Drive__trash_file
mcp__Notion__notion-delete-pages mcp__Notion__notion-delete-databases mcp__Notion__notion-calendar-cancel-events
mcp__Notion__notion-calendar-create-events
mcp__plugin_ai-workforce_HighLevel__conversations_send-a-new-message mcp__plugin_ai-workforce_HighLevel__contacts_add-tags
mcp__plugin_ai-workforce_HighLevel__contacts_remove-tags mcp__plugin_ai-workforce_HighLevel__contacts_update-contact
mcp__HighLevel__contacts_upsert-contact mcp__HighLevel__social-media-posting_create-post mcp__LeadConnector__some_unknown_action
mcp__stripe__create_refund mcp__stripe__create_invoice mcp__stripe__update_subscription mcp__stripe__cancel_subscription
mcp__meta__update_campaign_budget mcp__qb__void_invoice
mcp__slack__slack_send_message mcp__x__sendMessage mcp__x__create_post mcp__x__publish_page mcp__cal__book_meeting
mcp__x__unsubscribe_from_list mcp__x__archive_thread mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__send_message
mcp__claude-code-remote__create_trigger mcp__claude-code-remote__update_trigger mcp__claude-code-remote__fire_trigger
mcp__claude-code-remote__delete_trigger mcp__claude-code-remote__send_later
mcp__scheduled-tasks__create_scheduled_task mcp__scheduled-tasks__update_scheduled_task mcp__x__run_routine
mcp__HighLevel__projects_set-task-home-list
""".split()


class ToolNames(unittest.TestCase):
    def test_reading_drafting_and_the_business_brain_are_never_refused(self):
        for tool in ALLOWED:
            self.assertIsNone(send_lock.decide(tool), tool)

    def test_sending_deleting_sharing_booking_and_money_changes_are_refused(self):
        for tool in REFUSED:
            self.assertIsNotNone(send_lock.decide(tool), tool)

    def test_highlevel_is_read_only(self):
        self.assertIsNone(send_lock.decide("mcp__HighLevel__contacts_get-contacts"))
        for tool in ["mcp__HighLevel__contacts_create-contact", "mcp__HighLevel__opportunities_update-opportunity",
                     "mcp__HighLevel__calendars_do-something-new"]:
            self.assertIn("HighLevel", send_lock.decide(tool), tool)

    def test_a_reading_word_first_makes_a_money_or_sharing_word_a_read(self):
        self.assertIsNone(send_lock.decide("mcp__stripe__get_refund"))
        self.assertIsNotNone(send_lock.decide("mcp__stripe__refund_charge"))
        self.assertIsNotNone(send_lock.decide("mcp__x__get_and_send_report"))     # "send" is refused wherever it appears


class RunAnOperationTools(unittest.TestCase):
    """HighLevel's connection has one general tool, execute_operation, and the operation is named
    in the call's input. The tool's name says nothing, so the lock reads the input: a call goes
    through only when what it names is a plain read. The exact field names are HighLevel's, so
    several likely shapes are covered and anything unclear is refused."""
    TOOLS = ["mcp__HighLevel__execute_operation", "mcp__plugin_ai-workforce_HighLevel__execute_operation",
             "mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__execute_operation"]       # whatever the connection is called
    READS = [
        {"operation_id": "conversations.search", "input": {"query": "please send me the invoice"}},
        {"operationId": "getMessagesByConversationId", "locationId": "ve9EPM428h8vShlRW1KT", "params": {"conversationId": "abc"}},
        {"operation": "contacts_get-contact", "location_id": "x"},
        {"method": "GET", "path": "/conversations/abc/messages"},
        {"method": "POST", "path": "/contacts/search", "body": {"query": "delete"}},      # a search sent as POST is still a read
        {"id": "payments.transactions.list"},
        {"operation": {"id": "conversations.search-conversation"}, "arguments": {}},
        {"name": "list-calendar-events"},
        {"operation_id": "social-media-posting.get-posts"},
    ]
    CHANGES = [
        {"operation_id": "conversations_send-a-new-message", "input": {"message": "hi"}},
        {"operation_id": "conversations.messages.send"},
        {"operation": "contacts_add-tags"},
        {"operation": "contacts.update-contact"},
        {"method": "POST", "path": "/conversations/messages"},
        {"method": "DELETE", "path": "/contacts/abc"},
        {"method": "PUT", "path": "/contacts/abc"},
        {"operation_id": "calendars.events.appointments.create"},
        {"operation_id": "opportunities.upsert"},
        {"operation_id": "workflows.start"},                                  # no reading word: not clearly a read
        {"operation_id": "refund-order"},
        {"operation_id": "get-contact", "action": "delete"},                  # a read-looking name can't hide a change
        {"operation_id": "conversations.search", "x": "send-message"},
    ]
    UNCLEAR = [{}, None, "search", {"input": {"operation": "search"}}, {"locationId": "abc"}]

    def test_plain_reads_go_through(self):
        for tool in self.TOOLS:
            for call in self.READS:
                self.assertIsNone(send_lock.decide(tool, call), (tool, call))

    def test_changes_are_refused_whatever_the_connection_is_called(self):
        for tool in self.TOOLS:
            for call in self.CHANGES:
                self.assertIsNotNone(send_lock.decide(tool, call), (tool, call))

    def test_anything_unclear_is_refused(self):
        for call in self.UNCLEAR:
            self.assertIsNotNone(send_lock.decide(self.TOOLS[0], call), call)

    def test_what_a_customer_wrote_never_decides(self):
        """Free text and the payload are ignored: a search for the word "delete" is still a search,
        and a message body saying "get" doesn't make a send a read."""
        self.assertIsNone(send_lock.decide(self.TOOLS[0], {"operation_id": "conversations.search", "query": "delete my account"}))
        self.assertIsNotNone(send_lock.decide(self.TOOLS[0], {"operation_id": "conversations.messages.send",
                                                               "message": "get back to you soon", "input": {"note": "search"}}))

    def test_the_other_highlevel_tools_only_look_things_up(self):
        for name in ["search", "fetch", "search_operations", "describe_operation", "list_locations"]:
            self.assertIsNone(send_lock.decide("mcp__HighLevel__" + name, {"query": "send a message"}), name)


class RealHighLevelOperations(unittest.TestCase):
    """Operation names as HighLevel's own connection lists them (looked up on a connected account,
    2026-11-10), in the shape its execute_operation tool takes: operationId, params, and a free-text
    reason. HighLevel labels each one read, write or delete; the lock has to reach the same answer
    from the name alone."""
    TOOL = "mcp__HighLevel__execute_operation"
    READS = """search-conversation get-conversation get-messages get-message get-message-transcription
        get-message-recording get-email-by-id fb-get-conversation-forms get-conversation-channel
        download-message-transcription search-opportunities-advanced""".split()
    POST_READS = """google-get-keyword-ideas get-tags-by-ids get-statistics getSitemapPreview get-posts
        fetchCalendarList get-comment-list fetchQueues fetchQueueItems fetchSlots""".split()   # labelled "write": they read by POST
    WRITES = """send-a-new-message add-an-inbound-message add-an-outbound-message create-conversation
        update-conversation update-message-status add-message-attachments live-chat-agent-typing
        fb-create-conversation-form send-invoice send-estimate send-documents-contracts
        google-create-offline-user-list-job create-projects-list-task add-projects-list-task
        create-projects-folder-list update-projects-list create-projects-space-list
        set-projects-task-home-list updateProject create-pipeline google-upsert-segment li-create-lead-form
        li-create-integration create-contact update-contact create-task create update
        bulk-delete-social-planner-posts schedule-campaign planProjectChange create-projects-recurring-task
        promoteProjectToProduction submitAgentRun google-upsert-campaign locations.create-custom-field
        locations.update-custom-field bulkUpdate cliSandboxRegisterExtensionRoute fb-publish-campaign
        publishAppCustomization restoreMobileCustomizationRevision create-enrollment discoverWebsite
        create-projects-space create-projects-space-folder upsert-projects-space-statuses
        create-watermark-template update-watermark-template apply-watermark-to-image create-comment
        mark-payout-method-primary create-workflow update-workflow-definition validate-workflow-definition""".split()
    DELETES = """remove-projects-list-task delete-projects-list-user delete-projects-list
        deleteTrainedUrlsForKnowledgeBase delete-enrollment knowledge-base.delete deleteFile
        delete-projects-task-comment delete-like delete-redirect-by-id""".split()

    def call(self, operation, **extra):
        asked = {"operationId": operation, "params": {"query": {"limit": 20}},
                 "reason": "Find customers waiting on a reply so the owner can send the suggested replies"}
        asked.update(extra)
        return send_lock.decide(self.TOOL, asked)

    def test_the_reads_the_team_needs_go_through(self):
        for op in self.READS + self.POST_READS:
            self.assertIsNone(self.call(op), op)

    def test_every_write_and_delete_is_refused(self):
        self.assertEqual(len(self.WRITES) + len(self.DELETES), 66)
        for op in self.WRITES + self.DELETES:
            self.assertIsNotNone(self.call(op), op)

    def test_a_reading_word_used_as_a_thing_does_not_make_a_read(self):
        """0.8.1 let "set-projects-task-home-list" (which moves a task) through, because "list" is
        a reading word. The name has to begin with one."""
        for op in ["set-projects-task-home-list", "move-list-item", "mark-as-read", "assign-saved-search", "toggle-view"]:
            self.assertIsNotNone(self.call(op), op)
        for name, reads in [("search-conversation", True), ("fb-get-conversation-forms", True), ("getSitemapPreview", True),
                            ("conversations.search", True), ("contacts_get-contact", True), ("payments.transactions.list", True),
                            ("social-media-posting_get-posts", True), ("list", True),
                            ("set-projects-task-home-list", False), ("projects_set-task-home-list", False),
                            ("export-messages-by-location", False), ("", False), (None, False)]:
            self.assertEqual(send_lock.begins_as_a_read(name), reads, name)

    def test_what_the_reason_says_never_decides(self):
        self.assertIsNone(self.call("get-conversation", reason="so the owner can send, delete or refund as they see fit"))
        self.assertIsNotNone(self.call("send-a-new-message", reason="only to get and read the conversation"))

    def test_an_idempotency_key_marks_a_change(self):
        """HighLevel requires one for writes and never for reads."""
        self.assertIsNotNone(self.call("get-conversation", idempotencyKey="reply-2026-11-10"))
        self.assertIsNone(self.call("get-conversation", idempotencyKey=""))
        self.assertIsNotNone(self.call("send-a-new-message", dryRun=True))            # a preview of a send is still not a read

    def test_looking_up_operations_is_always_allowed(self):
        for tool in ["search_operations", "describe_operation", "list_locations"]:
            self.assertIsNone(send_lock.decide("mcp__HighLevel__" + tool, {"query": "send a message", "kind": "write"}), tool)


class ScheduledTasks(unittest.TestCase):
    """A run never changes a recurring task (older tasks' stored text still asks runs to update
    their own instructions). The lock refuses the tools that would."""
    def test_a_run_can_list_tasks_but_not_create_change_or_start_one(self):
        for tool in ["mcp__claude-code-remote__list_triggers", "mcp__scheduled-tasks__list_scheduled_tasks"]:
            self.assertIsNone(send_lock.decide(tool), tool)
        for tool in ["mcp__claude-code-remote__create_trigger", "mcp__claude-code-remote__update_trigger",
                     "mcp__claude-code-remote__fire_trigger", "mcp__scheduled-tasks__update_scheduled_task"]:
            self.assertIn("scheduled task", send_lock.decide(tool), tool)

    def test_ordinary_tasks_and_notes_are_not_mistaken_for_scheduled_ones(self):
        for tool in ["mcp__x__create_task", "mcp__Notion__notion-create-pages", "mcp__x__update_task_status"]:
            self.assertIsNone(send_lock.decide(tool), tool)


class Hook(unittest.TestCase):
    """Runs the launcher exactly as hooks.json does."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.env = dict(os.environ, TMPDIR=str(self.dir / "tmp"))
        (self.dir / "tmp").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def transcript(self, *prompts, name="t.jsonl"):
        p = self.dir / name
        lines = [json.dumps({"type": "queue-operation"})]
        for text in prompts:
            lines.append(json.dumps({"type": "user", "isSidechain": False, "message": {"role": "user", "content": text}}))
            lines.append(json.dumps({"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "x", "content": "[AI Workforce task: inbox-triage | prompt version 0.5.4]"}]}}))
        p.write_text("\n".join(lines) + "\n")
        return str(p)

    def run_hook(self, **data):
        r = subprocess.run(["sh", str(HOOKS / "send-lock.sh")], input=json.dumps(data), capture_output=True,
                           text=True, env=self.env, timeout=20)
        return r.returncode, r.stderr, r.stdout

    def pre(self, tool, session="s1", **extra):
        return self.run_hook(hook_event_name="PreToolUse", tool_name=tool, tool_input={}, session_id=session, **extra)

    def test_a_run_started_by_a_recurring_task_cannot_send(self):
        t = self.transcript(TAG_PROMPT)
        code, err, out = self.pre("mcp__Gmail__send_message", transcript_path=t)
        self.assertEqual(code, 2)
        self.assertIn("send lock", err)
        self.assertIn("draft", err)
        self.assertIn("ask again in a new chat", err)           # what to tell an owner who joined this conversation
        self.assertEqual(out, "")                               # nothing is ever printed for Claude to read as context

    def test_a_run_started_by_a_recurring_task_cannot_rewrite_or_start_tasks(self):
        t = self.transcript(TAG_PROMPT)
        for tool in ["mcp__claude-code-remote__update_trigger", "mcp__claude-code-remote__create_trigger", "mcp__claude-code-remote__fire_trigger"]:
            code, err, _ = self.pre(tool, transcript_path=t)
            self.assertEqual(code, 2, tool)
            self.assertIn("scheduled task", err)
        self.assertEqual(self.pre("mcp__claude-code-remote__list_triggers", transcript_path=t)[0], 0)
        owner_chat = self.transcript("Move my briefing to 7 AM", name="o.jsonl")     # the owner may always change their own tasks
        self.assertEqual(self.pre("mcp__claude-code-remote__update_trigger", session="s3", transcript_path=owner_chat)[0], 0)

    def test_the_same_run_can_still_read_and_draft(self):
        t = self.transcript(TAG_PROMPT)
        for tool in ["mcp__Gmail__create_draft", "mcp__Gmail__search_threads", "mcp__Notion__notion-create-pages"]:
            self.assertEqual(self.pre(tool, transcript_path=t)[0], 0, tool)

    def test_a_chat_with_the_owner_is_not_affected(self):
        t = self.transcript("What's on my calendar today?")
        self.assertEqual(self.pre("mcp__Gmail__send_message", transcript_path=t)[0], 0)

    def test_the_tag_in_a_tool_result_does_not_lock_an_owner_chat(self):
        """Listing scheduled tasks shows their stored text; that must not look like an unattended run."""
        t = self.transcript("check my scheduled tasks")       # the helper adds a tool result containing the tag
        self.assertEqual(self.pre("mcp__Gmail__send_message", transcript_path=t)[0], 0)

    def test_prompt_submit_marks_the_session_and_prints_nothing(self):
        code, err, out = self.run_hook(hook_event_name="UserPromptSubmit", session_id="s9", prompt=TAG_PROMPT)
        self.assertEqual((code, out), (0, ""))
        # no transcript available at all: the mark alone is enough
        self.assertEqual(self.pre("mcp__Google_Drive__share_file", session="s9", transcript_path="/nonexistent")[0], 2)
        self.assertEqual(self.pre("mcp__Google_Drive__share_file", session="other", transcript_path="/nonexistent")[0], 0)

    def test_an_ordinary_prompt_marks_nothing(self):
        self.run_hook(hook_event_name="UserPromptSubmit", session_id="s8", prompt="Draft a reply to Sam")
        self.assertEqual(self.pre("mcp__Gmail__send_message", session="s8")[0], 0)

    def test_team_members_cannot_send_even_in_an_owner_chat(self):
        t = self.transcript("Have Sales follow up with the new leads")
        code, err, _ = self.pre("mcp__Gmail__send_message", transcript_path=t, agent_type="ai-workforce:sales-manager", agent_id="a1")
        self.assertEqual(code, 2)
        self.assertIn("Chief of Staff", err)
        self.assertEqual(self.pre("mcp__Gmail__create_draft", transcript_path=t, agent_type="ai-workforce:sales-manager")[0], 0)

    def test_other_agents_are_left_alone_in_an_owner_chat(self):
        t = self.transcript("Send the note to Sam")
        for agent in ["general-purpose", "other-plugin:sales-manager", "sales-manager"]:
            self.assertEqual(self.pre("mcp__Gmail__send_message", transcript_path=t, agent_type=agent)[0], 0, agent)

    def test_a_team_member_in_an_unattended_run_is_covered_by_the_run(self):
        """Hook input for an agent carries the parent session's id and transcript."""
        t = self.transcript(TAG_PROMPT)
        self.assertEqual(self.pre("mcp__Gmail__reply", transcript_path=t, agent_type="general-purpose", agent_id="a2")[0], 2)

    def test_a_scheduled_run_can_read_highlevel_but_not_change_it(self):
        t = self.transcript(TAG_PROMPT)
        tool = "mcp__HighLevel__execute_operation"
        def call(tool_input, **extra):
            return self.run_hook(hook_event_name="PreToolUse", tool_name=tool, tool_input=tool_input,
                                 session_id="s1", transcript_path=t, **extra)
        self.assertEqual(call({"operation_id": "conversations.search", "input": {"locationId": "abc"}})[0], 0)
        self.assertEqual(call({"operationId": "search-conversation", "params": {"query": {"limit": 20}},
                               "reason": "Find customers waiting on a reply"})[0], 0)             # HighLevel's real shape
        self.assertEqual(call({"operationId": "set-projects-task-home-list", "params": {}})[0], 2)
        code, err, _ = call({"operation_id": "conversations.messages.send", "input": {"message": "hi"}})
        self.assertEqual(code, 2)
        self.assertIn("send", err)
        self.assertEqual(call({"input": {}})[0], 2)                                  # unclear: refused
        self.assertEqual(self.pre("mcp__HighLevel__search_operations", transcript_path=t)[0], 0)
        # with the owner present, the Chief of Staff isn't locked; a team member still is
        owner_chat = self.transcript("Reply to Dana in HighLevel", name="o.jsonl")
        send = {"operation_id": "conversations.messages.send"}
        self.assertEqual(self.run_hook(hook_event_name="PreToolUse", tool_name=tool, tool_input=send,
                                       session_id="s2", transcript_path=owner_chat)[0], 0)
        self.assertEqual(self.run_hook(hook_event_name="PreToolUse", tool_name=tool, tool_input=send, session_id="s2",
                                       transcript_path=owner_chat, agent_type="ai-workforce:client-success-manager")[0], 2)

    def test_broken_input_lets_the_call_through(self):
        for raw in ["", "not json", "[]", '{"hook_event_name": "PreToolUse"}', '{"hook_event_name": "Stop"}']:
            r = subprocess.run(["sh", str(HOOKS / "send-lock.sh")], input=raw, capture_output=True, text=True, env=self.env)
            self.assertEqual(r.returncode, 0, raw)

    def test_other_events_and_other_tools_are_ignored(self):
        t = self.transcript(TAG_PROMPT)
        self.assertEqual(self.pre("Bash", transcript_path=t)[0], 0)
        self.assertEqual(self.run_hook(hook_event_name="PostToolUse", tool_name="mcp__Gmail__send_message",
                                       session_id="s1", transcript_path=t)[0], 0)


class Packaging(unittest.TestCase):
    def test_hooks_file_runs_the_launcher_before_every_connected_app_tool(self):
        cfg = json.loads((HOOKS / "hooks.json").read_text())["hooks"]
        pre = cfg["PreToolUse"][0]
        self.assertEqual(pre["matcher"], "mcp__.*")
        for group in (pre, cfg["UserPromptSubmit"][0]):
            hook = group["hooks"][0]
            self.assertEqual(hook["type"], "command")
            self.assertIn('"${CLAUDE_PLUGIN_ROOT}/hooks/send-lock.sh"', hook["command"])
            self.assertNotIn("onFailure", hook)                 # a broken lock must never block the owner's own chats
        self.assertTrue((HOOKS / "send-lock.sh").exists() and (HOOKS / "send_lock.py").exists())

    def test_the_lock_never_refuses_without_one_of_its_two_reasons(self):
        code, _ = send_lock.handle({"hook_event_name": "PreToolUse", "tool_name": "mcp__Gmail__send_message", "session_id": "zz"})
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
