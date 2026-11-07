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

    def test_last_paragraph_counts(self):
        # an offer followed by one more line in the same paragraph still counts (reviewer, S272)
        self.assertIsNotNone(self.check("Anh có muốn em làm tiếp không?\nLane l4 đã merge."))
        self.assertIsNotNone(self.check("Shall I continue?\nLane l4 is merged; all checks green."))
        self.assertIsNone(self.check("Shall I continue?\n\nLane l4 is merged; all checks green."))
        self.assertIsNotNone(self.check("Lane l4 is merged.\n\nShall I continue with l5?"))

    def test_real_offers_from_the_transcripts_are_blocked(self):
        # turn-final messages of earlier sessions the reviewer's replay found (S272), plus crafted shapes
        for text in (
                "Nghiệp muốn em làm tiếp (đưa 224 lên rồi tới AA-773, AA-775, r5), hay chốt phiên ở đây?",
                "Anh muốn em làm tiếp gì trong phiên này, hay dừng phiên?",
                "Giờ đã gần 23:00. Nghiệp muốn **dừng phiên** để mình chạy nghi thức cuối phiên (log, backlog, "
                "memory Notion, nháp Jira, root PR, đưa 5 repo về `main` sạch), hay làm tiếp?",
                "Anh muốn tôi chạy nghi thức kết thúc phiên luôn không?",
                "Anh muốn em vào phần kết phiên luôn không?",
                "Log phiên, memory Notion, Linear, lessons và thư mục audit đã cập nhật. Anh có muốn **dừng phiên "
                "S234** ở đây không?",
                "Em đề xuất **kết thúc phiên S224 ở đây**. Phần AA-756 chuyển sang S225. Anh muốn kết thúc, hay "
                "làm thêm việc nào?",
                "Anh có muốn em làm tiếp phần deploy CIS không?",
                "Em tiếp tục deploy nhé?"):
            self.assertIsNotNone(self.check(text), text)

    def test_approval_asks_anywhere_in_the_last_paragraph_pass(self):
        # S272 reviewer replay: the cost, MFA or DRY RUN context sits on the line above the question
        for text in (
                "Thử 3 tour xong: tổng $0.41 (llm_call_log), 0 lỗi.\nAnh cho em chạy tiếp không?",
                "Phiên MFA hết hạn (aws sts báo ExpiredToken).\nAnh chạy `aws sts get-caller-identity --profile "
                "aa365-admin` rồi nhắn em làm tiếp nhé?",
                "DRY RUN xong: 42 dòng shared.job sẽ bị xoá (md5 pin ở trên).\nAnh cho em chạy tiếp không?",
                "Thử 3 tour xong: tổng $0.41.\n\nAnh cho em chạy tiếp không?",
                "Nghiệp **duyệt $1,97/tháng** cho alarm chứ? Rồi cho mình **dừng phiên** để làm 4 việc chốt nhé?",
                "Nghiệp duyệt chạy tiếp **50 tour India** nhé? Dự kiến tốn khoảng $2, mất 15–30 phút.",
                "Anh chọn **(a)** làm tiếp trong phiên này, hay **(b)** chốt phiên ở đây?",
                "Anh có muốn em tạo issue cho việc này rồi làm tiếp không?",
                "Nghiệp chốt hướng này chứ? Phiên sau mình làm phần còn lại. Sau đó mình dừng phiên.",
                "Anh muốn làm **ngay bây giờ** hay **để đầu phiên sau**? Trong lúc chờ, tôi tiếp tục với L15."):
            self.assertIsNone(self.check(text), text)

    def test_block_text_never_pushes_a_paid_run_or_a_delete(self):
        msg = self.check("Anh có muốn em làm tiếp không?")
        self.assertIn("Never start a paid run, a delete", msg)

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
