"""Tests for stop_open_work.py (AA-1024 G19). Run: python3 .claude/hooks/test_stop_open_work.py"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stop_open_work as g  # noqa: E402

CHECKLIST = """# S999 checklist
- [x] status block
- [ ] 3. Lane review of the invented demo slice
- [ ] Hẹn ngày: ≥08/11 run the tag report
- [ ] booking.job not checked (chờ DB Migrate check)
- [ ] [blocked: MFA] refresh the session
  - [ ] Write the tracker note at the close PR
"""


class StopOpenWorkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".tmp-session").mkdir()
        (self.root / ".tmp-session" / "S999-checklist.md").write_text(CHECKLIST, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def transcript(self, text: str) -> str:
        p = self.root / "t.jsonl"
        rows = [{"type": "user", "message": {"content": "go"}},
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}]
        p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        return str(p)

    def check(self, text: str, **kw) -> str | None:
        return g.check({"transcript_path": self.transcript(text), **kw}, self.root)

    def test_offer_to_stop_with_open_work_is_blocked_once(self):
        for text in ("Done with the lane. Shall I continue with the next issue?",
                     "Xong 3 issue. Anh có muốn em làm tiếp không?",
                     "I can close the session now.",
                     "Đề xuất dừng phiên ở đây.",
                     "Mọi việc chính đã xong, mình chốt phiên nhé?"):
            msg = self.check(text)
            self.assertIsNotNone(msg, text)
            self.assertIn("Lane review of the invented demo slice", msg)
            self.assertIn("Write the tracker note", msg)
            self.assertNotIn("tag report", msg)      # hẹn / ≥ date
            self.assertNotIn("booking.job", msg)     # chờ
            self.assertNotIn("refresh the session", msg)  # [blocked: MFA]
        self.assertIsNone(self.check("Shall I continue?", stop_hook_active=True))

    def test_plain_questions_and_reports_pass(self):
        for text in ("Which of the two layouts do you want for the invoice page?",
                     "Lane l3 is merged and live; /health returns 200.",
                     "Bảng nào là nguồn đúng cho số liệu này?", ""):
            self.assertIsNone(self.check(text), text)

    def test_statements_mentions_and_approval_asks_pass(self):
        # S272 reviewer strings: plain statements, a mention of the close, a paid-run / MFA approval question.
        for text in ("Script gọi trực tiếp không qua wrapper.",
                     "Bước tiếp không cần MFA",
                     "Bài học này em ghi vào log khi chốt phiên",
                     "We will close the session after the merge queue drains, then write the log. Lane l2 is live.",
                     "Should I proceed with the paid run (about 3 USD)?",
                     "Anh nhập mã MFA giúp em rồi em làm tiếp nhé?"):
            self.assertIsNone(self.check(text), text)

    def test_only_the_last_line_counts(self):
        self.assertIsNone(self.check("Shall I continue?\nLane l4 is merged; all checks green."))
        self.assertIsNotNone(self.check("Lane l4 is merged.\n\nShall I continue with l5?"))

    def test_dependency_waits_are_blocked_markers(self):
        (self.root / ".tmp-session" / "S999-checklist.md").write_text(
            "- [ ] Push l5 CIS (hook chạy ~5.000 test) chỉ khi lane CIS đã xong\n"
            "- [ ] R2 một lần sau W1/W2\n"
            "- [ ] Root PR mở sau khi l1 có policy\n"
            "- [ ] Tag report once the invented wave closes\n"
            "- [ ] Deploy khi migration xong\n", encoding="utf-8")
        self.assertIsNone(self.check("Shall I close the session?"))

    def test_no_open_items_or_stale_checklist_passes(self):
        (self.root / ".tmp-session" / "S999-checklist.md").write_text("- [x] all done\n- [ ] [blocked: tech lead]\n")
        self.assertIsNone(self.check("Shall I close the session?"))
        (self.root / ".tmp-session" / "S999-checklist.md").write_text(CHECKLIST)
        old = time.time() - 3 * 24 * 3600
        os.utime(self.root / ".tmp-session" / "S999-checklist.md", (old, old))
        self.assertIsNone(self.check("Shall I close the session?"))

    def test_newest_checklist_wins_and_message_field_is_read(self):
        (self.root / ".tmp-session" / "S998-checklist.md").write_text("- [ ] older open thing\n")
        old = time.time() - 3600
        os.utime(self.root / ".tmp-session" / "S998-checklist.md", (old, old))
        msg = g.check({"last_assistant_message": "Want me to continue?"}, self.root)
        self.assertIn("S999-checklist.md", msg)
        self.assertNotIn("older open thing", msg)

    def test_hook_exit_codes(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        sh = HERE / "stop-open-work.sh"
        self.assertTrue(os.access(sh, os.X_OK))

        def run(payload: str) -> subprocess.CompletedProcess:
            return subprocess.run([str(sh)], input=payload, text=True, capture_output=True, env=env, timeout=30)

        r = run(json.dumps({"transcript_path": self.transcript("Shall I continue?")}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("open item", r.stderr)
        self.assertEqual(run(json.dumps({"transcript_path": self.transcript("All live.")})).returncode, 0)
        self.assertEqual(run("not json").returncode, 0)
        self.assertEqual(run(json.dumps({"transcript_path": "/nonexistent.jsonl"})).returncode, 0)


if __name__ == "__main__":
    unittest.main()
