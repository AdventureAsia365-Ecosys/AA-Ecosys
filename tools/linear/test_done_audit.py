"""Tests for done_audit.py (AA-1024 G11). Offline: no Linear call. Run: python3 -m unittest discover -s tools/linear"""
from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import done_audit as d  # noqa: E402

DESC = """## Problem
The lantern catalogue page is slow.

## Done when
- [ ] The lantern list endpoint answers under 300 ms on Dev
- [ ] Admin page shows the lantern filter chips
- The nightly export writes lanterns.csv

+++ Agent notes
- not a done-when bullet
+++
"""

EVIDENCE = """Verified live 07/11:
- PR: #12 (merged abc123), ECS aa-demo-api :41
- lantern list endpoint → 200 in 180 ms on Dev
- UI: admin page with the lantern filter chips, screenshot attached
- nightly export wrote lanterns.csv (412 rows)
"""


def issue(ident: str, description: str = DESC, comments: list[str] | None = None) -> dict:
    return {"identifier": ident, "title": "Invented lantern work", "description": description,
            "completedAt": "2026-11-07T03:00:00Z", "url": f"https://linear.app/x/{ident}",
            "comments": {"nodes": [{"body": c, "createdAt": "2026-11-07T02:59:00Z"} for c in (comments or [])]}}


class DoneAuditTest(unittest.TestCase):
    def test_bullets_of_the_done_when_section_only(self):
        self.assertEqual(d.done_when_bullets(DESC), [
            "The lantern list endpoint answers under 300 ms on Dev",
            "Admin page shows the lantern filter chips",
            "The nightly export writes lanterns.csv"])
        self.assertEqual(d.done_when_bullets("**Done-when:**\n1. first lantern step\n2) second step\n"),
                         ["first lantern step", "second step"])
        self.assertEqual(d.done_when_bullets("no section here\n- a bullet"), [])

    def test_full_evidence_passes(self):
        self.assertEqual(d.audit([issue("AA-9001", comments=["Merged.", EVIDENCE])]), [])

    def test_auto_flip_without_a_comment_is_flagged(self):
        hits = d.audit([issue("AA-9002", comments=["Linked PR #13 merged"])])
        self.assertEqual(hits[0]["id"], "AA-9002")
        self.assertIn("no evidence comment", hits[0]["findings"][0])

    def test_missing_bullet_is_flagged(self):
        partial = "Verified live 07/11:\n- lantern list endpoint → 200 in 180 ms on Dev\n"
        hits = d.audit([issue("AA-9003", comments=[partial])])
        text = " ".join(hits[0]["findings"])
        self.assertIn("filter chips", text)
        self.assertIn("lanterns.csv", text)
        self.assertNotIn("300 ms", text)

    def test_hand_closed_and_scope_forms(self):
        self.assertEqual(d.audit([issue("AA-9004", description="no done-when",
                                        comments=["Done-evidence: duplicate of an invented issue"])]), [])
        scope = ("Done-with-scope:\n- Đã giao (verify live): lantern list endpoint 180 ms on Dev; admin page lantern "
                 "filter chips\n- Còn lại: nightly export writes lanterns.csv → AA-9100")
        self.assertEqual(d.audit([issue("AA-9005", comments=[scope])]), [])

    def test_main_exit_codes_and_json(self):
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(d.main(["--since", "2026-11-07"], issues=[issue("AA-9001", comments=[EVIDENCE])]), 0)
            self.assertEqual(d.main(["--since", "2026-11-07T00:00:00Z", "--json"], issues=[issue("AA-9002")]), 1)
        data = json.loads(out.getvalue().split("\n", 1)[1])
        self.assertEqual(data["hits"][0]["id"], "AA-9002")
        with self.assertRaises(SystemExit):
            d.main(["--since", "yesterday"], issues=[])


if __name__ == "__main__":
    unittest.main()
