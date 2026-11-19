"""Tests for sync_post_edit.py / sync-post-edit.sh (AA-1136). Run: python3 .claude/hooks/test_sync_post_edit.py

Temp git repos with invented file names, a fake ruff and a fake doc map; no network, no AWS.
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
import sync_post_edit as pe  # noqa: E402
from test_sync_change_guard import new_repo, write  # noqa: E402

FAKE_ENTRIES = [
    {"id": "demo-orders", "repo": "Demo", "pages": ["docs/guides/orders.md", "Demo:docs/orders.md"],
     "patterns": [r"^api/orders/.*$"]},
    {"id": "other-repo", "repo": "Elsewhere", "pages": ["docs/x.md"], "patterns": [r"^.*$"]},
]
FAKE_RUFF = """#!/bin/sh
for a in "$@"; do last="$a"; done
echo "$last:1:1: F821 Undefined name \\`missing_name\\`"
echo "Found 1 error."
exit 1
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.log = self.base / "log.jsonl"
        self.env = mock.patch.dict(os.environ, {"AA_SYNC_HOOKLOG": str(self.log),
                                                "AA_SYNC_STATE_DIR": str(self.base / "state")})
        self.env.start()
        self.top = new_repo(self.base)
        self.maps = mock.patch.object(pe, "load_doc_map", return_value=FAKE_ENTRIES)
        self.maps.start()

    def tearDown(self):
        self.maps.stop()
        self.env.stop()
        self.tmp.cleanup()

    def event(self, rel: str, session: str = "s1", agent: str | None = "lane-a") -> dict:
        data = {"session_id": session, "hook_event_name": "PostToolUse", "tool_name": "Edit",
                "tool_input": {"file_path": str(self.top / rel)}}
        if agent:
            data["agent_id"] = agent
        return data

    def fake_ruff(self) -> None:
        ruff = self.top / ".venv" / "bin" / "ruff"
        ruff.parent.mkdir(parents=True)
        ruff.write_text(FAKE_RUFF, encoding="utf-8")
        ruff.chmod(0o755)


class RunTest(Base):
    def test_log_mode_records_but_says_nothing(self):
        write(self.top, "api/orders/svc.py")
        rec, text = pe.run(self.event("api/orders/svc.py"), "log")
        self.assertEqual(text, "")
        self.assertEqual((rec["repo"], rec["repo_kind"], rec["file_kind"], rec["agent"]),
                         ("Demo", "main", "code", "lane-a"))
        self.assertEqual((rec["docs_entries"], rec["would"], rec["said"]), (["demo-orders"], "remind", False))
        state = json.loads((self.base / "state" / "s1-lane-a.json").read_text(encoding="utf-8"))
        self.assertEqual(state["repos"], [str(self.top)])
        self.assertEqual(state["said"], [], "log mode marks nothing as said")

    def test_warn_mode_says_docs_impact_once(self):
        write(self.top, "api/orders/svc.py")
        _, text = pe.run(self.event("api/orders/svc.py"), "warn")
        self.assertIn("Docs impact: api/orders/svc.py is described by Demo:docs/orders.md, docs/guides/orders.md",
                      text)
        _, again = pe.run(self.event("api/orders/svc.py"), "warn")
        self.assertEqual(again, "")
        _, other_agent = pe.run(self.event("api/orders/svc.py", agent="lane-b"), "warn")
        self.assertIn("Docs impact", other_agent)

    def test_editing_the_page_itself_is_no_docs_hit(self):
        entries = [{"id": "e", "repo": "Demo", "pages": ["Demo:api/orders/README.md"], "patterns": [r"^api/orders/.*$"]}]
        self.assertEqual(pe.docs_hits(entries, "Demo", "api/orders/README.md"), [])
        self.assertEqual([h["id"] for h in pe.docs_hits(entries, "Demo", "api/orders/x.py")], ["e"])
        self.assertEqual(pe.docs_hits(entries, "Other", "api/orders/x.py"), [])

    def test_lint_findings_reach_the_agent_in_warn_mode(self):
        self.fake_ruff()
        write(self.top, "api/svc.py")
        rec, text = pe.run(self.event("api/svc.py"), "warn")
        self.assertEqual((rec["lint"], rec["lint_findings"]), ("findings", 1))
        self.assertIn("ruff on api/svc.py:", text)
        self.assertIn("api/svc.py:1:1: F821", text)
        self.assertNotIn("Found 1 error", text)
        _, again = pe.run(self.event("api/svc.py"), "warn")
        self.assertEqual(again, "", "the same findings are said once")

    def test_no_ruff_is_unavailable_not_an_error(self):
        write(self.top, "api/svc.py")
        with mock.patch.object(pe, "find_ruff", return_value=None):
            rec, text = pe.run(self.event("api/svc.py"), "warn")
        self.assertEqual((rec["lint"], text), ("unavailable", ""))

    def test_ts_files_are_not_linted(self):
        write(self.top, "web/app/page.tsx", "export const a = 1\n")
        rec, _ = pe.run(self.event("web/app/page.tsx"), "warn")
        self.assertNotIn("lint", rec)

    def test_scratch_and_outside_files(self):
        write(self.top, ".tmp-session/S1-checklist.md", "- [ ] x\n")
        rec, _ = pe.run(self.event(".tmp-session/S1-checklist.md"), "warn")
        self.assertEqual(rec["outcome"], "ignored")
        rec, _ = pe.run({"tool_input": {"file_path": str(self.base / "loose.py")}}, "warn")
        self.assertEqual(rec["outcome"], "outside-repo")
        self.assertFalse((self.base / "state" / "nosession-main.json").exists())

    def test_docs_and_notes_are_tracked_but_get_no_docs_reminder(self):
        write(self.top, "docs/implementation-notes/AA-1.md", "# n\n")
        rec, text = pe.run(self.event("docs/implementation-notes/AA-1.md"), "warn")
        self.assertEqual((rec["file_kind"], text), ("note", ""))
        state = json.loads((self.base / "state" / "s1-lane-a.json").read_text(encoding="utf-8"))
        self.assertEqual(state["repos"], [str(self.top)])

    def test_broken_doc_map_is_logged(self):
        write(self.top, "api/orders/svc.py")
        with mock.patch.object(pe, "load_doc_map", side_effect=ValueError("bad map")):
            rec, _ = pe.run(self.event("api/orders/svc.py"), "warn")
        self.assertIn("bad map", rec["docs_error"])
        self.assertEqual(rec["docs_entries"], [])


class RuffConfigTest(unittest.TestCase):
    def test_nearest_config_inside_the_checkout(self):
        with tempfile.TemporaryDirectory() as d:
            top = Path(d)
            write(top, "backend/pyproject.toml", "[tool.ruff]\nline-length = 120\n")
            write(top, "backend/app/x.py")
            write(top, "other/y.py")
            self.assertEqual(pe.ruff_config_dir(top / "backend" / "app" / "x.py", top), top / "backend")
            self.assertIsNone(pe.ruff_config_dir(top / "other" / "y.py", top))


class DocMapCacheTest(unittest.TestCase):
    def test_real_map_is_cached_as_json(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML not installed (CI installs tools/docs/requirements.txt)")
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"AA_SYNC_STATE_DIR": d}):
            entries = pe.load_doc_map()
            self.assertGreater(len(entries), 0)
            self.assertTrue({"id", "repo", "pages", "patterns"} <= set(entries[0]))
            cache = Path(d) / "doc-map-cache.json"
            data = json.loads(cache.read_text(encoding="utf-8"))
            data["entries"] = [{"id": "from-cache", "repo": "R", "pages": [], "patterns": []}]
            cache.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual([e["id"] for e in pe.load_doc_map()], ["from-cache"])


class MainTest(Base):
    def call_main(self, data, mode: str) -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"AA_SYNC_HOOKS": mode}), \
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps(data) if isinstance(data, dict) else data)), \
                mock.patch.object(sys, "stdout", out):
            rc = pe.main()
        return rc, out.getvalue()

    def rows(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(x) for x in self.log.read_text(encoding="utf-8").splitlines()]

    def test_off_does_nothing(self):
        write(self.top, "api/orders/svc.py")
        self.assertEqual(self.call_main(self.event("api/orders/svc.py"), "off"), (0, ""))
        self.assertEqual(self.rows(), [])

    def test_log_is_silent_and_logs_latency(self):
        write(self.top, "api/orders/svc.py")
        self.assertEqual(self.call_main(self.event("api/orders/svc.py"), "log"), (0, ""))
        (row,) = self.rows()
        self.assertEqual((row["event"], row["mode"], row["would"]), ("PostToolUse", "log", "remind"))
        self.assertIsInstance(row["latency_ms"], float)

    def test_warn_prints_additional_context(self):
        write(self.top, "api/orders/svc.py")
        rc, out = self.call_main(self.event("api/orders/svc.py"), "warn")
        self.assertEqual(rc, 0)
        self.assertIn("Docs impact", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_internal_error_passes_and_is_logged(self):
        with mock.patch.object(pe, "run", side_effect=RuntimeError("boom")):
            self.assertEqual(self.call_main({"session_id": "s"}, "warn"), (0, ""))
        self.assertIn("boom", self.rows()[0]["error"])

    def test_wrapper_exits_zero_on_garbage(self):
        env = {**os.environ, "AA_SYNC_HOOKS": "warn"}
        res = subprocess.run(["bash", str(HERE / "sync-post-edit.sh")], input="{not json", capture_output=True,
                             text=True, env=env, timeout=30, check=False)
        self.assertEqual((res.returncode, res.stdout), (0, ""))
        row = self.rows()[-1]
        self.assertEqual(row["outcome"], "outside-repo")
        self.assertIsInstance(row["wall_ms"], float, "the wrapper passes its start time")


if __name__ == "__main__":
    unittest.main()
