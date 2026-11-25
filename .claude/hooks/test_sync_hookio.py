"""Tests for tools/sync/hookio.py (AA-1136). Run: python3 .claude/hooks/test_sync_hookio.py"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "sync"))
import hookio  # noqa: E402


class ModeTest(unittest.TestCase):
    def test_default_is_log(self):
        self.assertEqual(hookio.mode({}), "log")

    def test_known_values_and_case(self):
        for raw, want in (("off", "off"), ("LOG", "log"), (" warn ", "warn"), ("block", "block")):
            self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": raw}), want)

    def test_unknown_value_falls_back_to_log(self):
        self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": "loud"}), "log")

    def test_subagent_stop_stays_silent_unless_its_own_switch_says_so(self):
        self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": "warn"}, event="SubagentStop"), "log")
        self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": "block"}, event="SubagentStop"), "log")
        self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": "off"}, event="SubagentStop"), "off")
        self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": "warn", "AA_SYNC_HOOKS_SUBAGENT": "warn"},
                                     event="SubagentStop"), "warn")
        self.assertEqual(hookio.mode({"AA_SYNC_HOOKS": "warn"}, event="Stop"), "warn")

    def test_only_warn_and_block_speak(self):
        self.assertEqual([m for m in hookio.MODES if hookio.speaks(m)], ["warn", "block"])


class EventTest(unittest.TestCase):
    def test_read_event_tolerates_bad_input(self):
        self.assertEqual(hookio.read_event(io.StringIO("not json")), {})
        self.assertEqual(hookio.read_event(io.StringIO("[1, 2]")), {})
        self.assertEqual(hookio.read_event(io.StringIO("")), {})
        self.assertEqual(hookio.read_event(io.StringIO('{"a": 1}')), {"a": 1})

    def test_keys_are_sanitized(self):
        self.assertEqual(hookio.agent_key({}), "main")
        self.assertEqual(hookio.agent_key({"agent_id": "a/../b c"}), "a_b_c")
        self.assertEqual(hookio.session_key({"session_id": "x:y"}), "x_y")

    def test_edited_path(self):
        self.assertEqual(hookio.edited_path({"tool_input": {"file_path": "/a/b.py"}}), "/a/b.py")
        self.assertEqual(hookio.edited_path({"tool_input": {"notebook_path": "/a/n.ipynb"}}), "/a/n.ipynb")
        self.assertEqual(hookio.edited_path({"tool_input": "oops"}), "")
        self.assertEqual(hookio.edited_path({}), "")


class WallTest(unittest.TestCase):
    def test_wall_ms_from_the_wrapper_start(self):
        self.assertEqual(hookio.wall_ms({"AA_SYNC_T0": "100.000000"}, now=100.25), 250.0)
        self.assertEqual(hookio.wall_ms({"AA_SYNC_T0": "100,5"}, now=101.0), 500.0)  # a comma locale
        self.assertIsNone(hookio.wall_ms({}, now=1.0))
        self.assertIsNone(hookio.wall_ms({"AA_SYNC_T0": "soon"}, now=1.0))


class FindRepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        # main checkout: <base>/Proj with a .git dir; a child repo inside it; a worktree under .tmp-session/wt/
        self.main = self.base / "Proj"
        (self.main / ".git" / "worktrees" / "lane-root").mkdir(parents=True)
        (self.main / "apps" / "Child" / ".git").mkdir(parents=True)
        (self.main / "apps" / "Child" / ".git" / "worktrees" / "lane-child").mkdir(parents=True)
        self.wt = self.main / ".tmp-session" / "wt" / "lane-root"
        self.wt.mkdir(parents=True)
        (self.wt / ".git").write_text(f"gitdir: {self.main}/.git/worktrees/lane-root\n", encoding="utf-8")
        self.wt_child = self.main / ".tmp-session" / "wt" / "lane-child"
        self.wt_child.mkdir(parents=True)
        (self.wt_child / ".git").write_text(f"gitdir: {self.main}/apps/Child/.git/worktrees/lane-child\n",
                                            encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_main_checkout(self):
        r = hookio.find_repo(self.main / "tools" / "x.py")
        self.assertEqual((r.name, r.kind, r.rel, r.main), ("Proj", "main", "tools/x.py", self.main))

    def test_child_repo_inside_the_root_checkout(self):
        r = hookio.find_repo(self.main / "apps" / "Child" / "api" / "m.py")
        self.assertEqual((r.name, r.kind, r.rel), ("Child", "main", "api/m.py"))

    def test_worktree_names_its_main_repo(self):
        r = hookio.find_repo(self.wt / "tools" / "sync" / "a.py")
        self.assertEqual((r.name, r.kind, r.rel, r.top, r.main), ("Proj", "worktree", "tools/sync/a.py", self.wt,
                                                                    self.main))
        r = hookio.find_repo(self.wt_child / "backend" / "b.py")
        self.assertEqual((r.name, r.kind), ("Child", "worktree"))

    def test_scratch_of_the_main_checkout_resolves_to_it(self):
        r = hookio.find_repo(self.main / ".tmp-session" / "S999-checklist.md")
        self.assertEqual((r.name, r.rel), ("Proj", ".tmp-session/S999-checklist.md"))

    def test_outside_or_relative(self):
        self.assertIsNone(hookio.find_repo(""))
        self.assertIsNone(hookio.find_repo("relative/x.py"))

    def test_bad_gitdir_file_falls_back_to_folder_name(self):
        odd = self.base / "odd"
        odd.mkdir()
        (odd / ".git").write_text("nonsense\n", encoding="utf-8")
        r = hookio.find_repo(odd / "f.py")
        self.assertEqual((r.name, r.kind, r.main), ("odd", "worktree", None))


class StateAndLogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.env = mock.patch.dict(os.environ, {"AA_SYNC_HOOKLOG": str(d / "log.jsonl"),
                                                "AA_SYNC_STATE_DIR": str(d / "state")})
        self.env.start()
        self.dir = d

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_state_round_trip_and_first_time(self):
        data = {"session_id": "s1", "agent_id": "ag"}
        st = hookio.load_state(data)
        self.assertEqual((st["repos"], st["said"]), ([], []))
        self.assertTrue(hookio.first_time(st, "k"))
        self.assertFalse(hookio.first_time(st, "k"))
        st["repos"].append("/x")
        hookio.save_state(data, st)
        again = hookio.load_state(data)
        self.assertEqual((again["repos"], again["said"]), (["/x"], ["k"]))
        self.assertTrue(hookio.state_file(data).name.startswith("s1-ag"))
        # another agent of the same session has its own state
        self.assertEqual(hookio.load_state({"session_id": "s1", "agent_id": "other"})["said"], [])

    def test_corrupt_state_starts_empty(self):
        data = {"session_id": "s2"}
        hookio.state_file(data).parent.mkdir(parents=True, exist_ok=True)
        hookio.state_file(data).write_text("{broken", encoding="utf-8")
        self.assertEqual(hookio.load_state(data)["repos"], [])

    def test_log_event_appends_json_lines(self):
        hookio.log_event({"event": "PostToolUse", "latency_ms": 1.5})
        hookio.log_event({"event": "Stop", "latency_ms": 2})
        rows = [json.loads(x) for x in (self.dir / "log.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["event"] for r in rows], ["PostToolUse", "Stop"])
        self.assertIn("ts", rows[0])

    def test_log_event_never_raises(self):
        with mock.patch.dict(os.environ, {"AA_SYNC_HOOKLOG": "/proc/forbidden/dir/log.jsonl"}):
            hookio.log_event({"event": "x"})  # no exception

    def test_clip_and_context_output(self):
        self.assertEqual(hookio.clip("short"), "short")
        long = hookio.clip("x" * 5000)
        self.assertLessEqual(len(long), hookio.MAX_MESSAGE)
        self.assertTrue(long.endswith("(... cut)"))
        out = json.loads(hookio.context_output("PostToolUse", "hello"))
        self.assertEqual(out, {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "hello"}})


if __name__ == "__main__":
    unittest.main()
