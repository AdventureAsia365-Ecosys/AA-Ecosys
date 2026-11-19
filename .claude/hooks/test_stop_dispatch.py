"""Tests for stop_dispatch.py / stop-dispatch.sh (AA-1136). Run: python3 .claude/hooks/test_stop_dispatch.py

Part 1 proves the merged dispatcher keeps stop_open_work.py's behaviour byte for byte (same exit code, same stderr,
in every AA_SYNC_HOOKS mode); part 2 covers the change guard at Stop / SubagentStop. Invented texts and file names.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stop_dispatch as sd  # noqa: E402
from test_stop_open_work import CHECKLIST  # noqa: E402
from test_sync_change_guard import git, new_repo, write  # noqa: E402

hookio = sd.hookio  # tools/sync/hookio.py, put on sys.path by stop_dispatch

TEXTS = (
    "Done with the lane. Shall I continue with the next issue?",
    "Xong 3 issue. Anh có muốn em làm tiếp không?",
    "I can close the session now.",
    "Which of the two layouts do you want for the invoice page?",
    "Should I proceed with the paid run (about 3 USD)?",
    "Lane l4 is merged.\n\nShall I continue with l5?",
    "",
)


def transcript(root: Path, text: str) -> str:
    p = root / "t.jsonl"
    rows = [{"type": "user", "message": {"content": "go"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}]
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(p)


class ParityWithStopOpenWorkTest(unittest.TestCase):
    """The dispatcher returns exactly what stop-open-work.sh returned on its own, whatever the sync mode."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".tmp-session").mkdir()
        (self.root / ".tmp-session" / "S999-checklist.md").write_text(CHECKLIST, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, script: str, data: dict, mode: str) -> tuple[int, str]:
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root), "AA_SYNC_HOOKS": mode,
               "AA_SYNC_HOOKLOG": str(self.root / "log.jsonl"), "AA_SYNC_STATE_DIR": str(self.root / "state")}
        res = subprocess.run(["bash", str(HERE / script)], input=json.dumps(data), capture_output=True, text=True,
                             env=env, timeout=30, check=False)
        return res.returncode, res.stderr

    def test_same_exit_and_message(self):
        blocked = 0
        for text in TEXTS:
            for extra in ({}, {"stop_hook_active": True}):
                data = {"session_id": "s", "hook_event_name": "Stop",
                        "transcript_path": transcript(self.root, text), **extra}
                want = self.run_hook("stop-open-work.sh", data, "log")
                blocked += want[0] == 2
                for mode in ("off", "log", "warn", "block"):
                    self.assertEqual(self.run_hook("stop-dispatch.sh", data, mode), want, (text, extra, mode))
        self.assertGreater(blocked, 0, "the fixture must exercise the blocking path")

    def test_last_assistant_message_field_and_missing_event_name(self):
        data = {"last_assistant_message": "Shall I continue with the next issue?"}
        code, err = self.run_hook("stop-dispatch.sh", data, "off")
        self.assertEqual(code, 2)
        self.assertIn("Lane review of the invented demo slice", err)

    def test_subagent_stop_never_runs_the_checklist_check(self):
        data = {"session_id": "s", "agent_id": "lane-1", "hook_event_name": "SubagentStop",
                "last_assistant_message": "Shall I continue with the next issue?"}
        self.assertEqual(self.run_hook("stop-dispatch.sh", data, "warn"), (0, ""))

    def test_garbage_input_passes(self):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root), "AA_SYNC_HOOKLOG": str(self.root / "log.jsonl"),
               "AA_SYNC_STATE_DIR": str(self.root / "state")}
        res = subprocess.run(["bash", str(HERE / "stop-dispatch.sh")], input="{nope", capture_output=True,
                             text=True, env=env, timeout=30, check=False)
        self.assertEqual(res.returncode, 0)


class ChangeGuardAtStopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.log = self.base / "log.jsonl"
        self.env = mock.patch.dict(os.environ, {"AA_SYNC_HOOKLOG": str(self.log),
                                                "AA_SYNC_STATE_DIR": str(self.base / "state")})
        self.env.start()
        self.top = new_repo(self.base)
        self.wt = self.top / ".tmp-session" / "wt" / "lane-x"
        git(self.top, "worktree", "add", "-q", str(self.wt), "-b", "feat/aa-88-demo", "origin/main")
        write(self.wt, "api/demo.py")

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def data(self, **kw) -> dict:
        return {"session_id": "s1", "agent_id": "lane-x", "hook_event_name": "SubagentStop", **kw}

    def wrote(self, *tops: Path) -> None:
        state = hookio.load_state(self.data())
        state["repos"] = [str(t) for t in tops]
        hookio.save_state(self.data(), state)

    def test_agent_that_wrote_nothing_is_not_checked(self):
        rec, text = sd.sync_check(self.data(), "warn")
        self.assertEqual((rec["outcome"], text), ("no-writes", ""))

    def test_log_mode_records_findings_silently(self):
        self.wrote(self.wt)
        rec, text = sd.sync_check(self.data(), "log")
        self.assertEqual(text, "")
        self.assertEqual((rec["would"], rec["repo_kind"]), ("remind", "worktree"))
        (check,) = rec["checks"]
        self.assertEqual((check["repo"], check["issues"], check["findings"]), ("Demo", ["AA-88"], ["no-test",
                                                                                                    "no-note"]))

    def test_warn_says_it_once(self):
        self.wrote(self.wt)
        rec, text = sd.sync_check(self.data(), "warn")
        self.assertIn("Change guard (code -> tests -> notes) for Demo [feat/aa-88-demo]", text)
        self.assertIn("docs/implementation-notes/AA-88.md", text)
        self.assertTrue(rec["said"])
        _, again = sd.sync_check(self.data(), "warn")
        self.assertEqual(again, "")

    def test_stop_hook_active_lets_the_stop_through(self):
        self.wrote(self.wt)
        _, text = sd.sync_check(self.data(stop_hook_active=True), "warn")
        self.assertEqual(text, "")

    def test_fixed_change_is_quiet(self):
        write(self.wt, "tests/test_demo.py")
        write(self.wt, "docs/implementation-notes/AA-88.md", "# AA-88\n")
        self.wrote(self.wt)
        rec, text = sd.sync_check(self.data(), "warn")
        self.assertEqual((rec["would"], text), ("none", ""))

    def test_removed_worktree_is_skipped(self):
        self.wrote(self.base / "gone")
        rec, _ = sd.sync_check(self.data(), "warn")
        self.assertEqual(rec["outcome"], "no-writes")

    def call_main(self, data: dict, mode: str) -> tuple[int, str]:
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"AA_SYNC_HOOKS": mode}), \
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps(data))), mock.patch.object(sys, "stderr", err):
            rc = sd.main()
        return rc, err.getvalue()

    def rows(self) -> list[dict]:
        return [json.loads(x) for x in self.log.read_text(encoding="utf-8").splitlines()]

    def test_main_warn_refuses_once_and_logs(self):
        self.wrote(self.wt)
        rc, err = self.call_main(self.data(), "warn")
        self.assertEqual(rc, 2)
        self.assertIn("No test needed: <reason>", err)
        self.assertEqual(self.call_main(self.data(), "warn"), (0, ""))
        rows = self.rows()
        self.assertEqual([r["event"] for r in rows], ["SubagentStop", "SubagentStop"])
        self.assertTrue(all(isinstance(r["latency_ms"], float) for r in rows))

    def test_main_log_and_off(self):
        self.wrote(self.wt)
        self.assertEqual(self.call_main(self.data(), "log"), (0, ""))
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.call_main(self.data(), "off"), (0, ""))
        self.assertEqual(len(self.rows()), 1, "off writes no log line")

    def test_main_internal_error_passes_and_is_logged(self):
        self.wrote(self.wt)
        with mock.patch.object(sd.change_guard, "check", side_effect=RuntimeError("kaput")):
            self.assertEqual(self.call_main(self.data(), "warn"), (0, ""))
        self.assertIn("kaput", self.rows()[0]["error"])


if __name__ == "__main__":
    unittest.main()
