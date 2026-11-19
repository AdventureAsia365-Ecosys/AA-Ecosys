"""Every hook .claude/settings.json registers exists, is executable and has its tests (AA-1024 G5).

A broken hook path fails open (Claude Code reports a hook error and goes on) or blocks every call, and nobody notices.
Run: python3 .claude/hooks/test_settings_hooks.py   (root CI: Docs lint, "Claude hook tests")
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / ".claude" / "settings.json"
HOOKS = ROOT / ".claude" / "hooks"
# Tool names the matchers may use (built-in tools; mcp__ names are matched by pattern).
KNOWN_TOOLS = {"Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "Read", "Workflow", "Agent", "Task", "WebFetch"}


def registered() -> list[tuple[str, str]]:
    return [(matcher, h.get("command", "")) for _, matcher, h in registered_by_event()]


def registered_by_event() -> list[tuple[str, str, dict]]:
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    out = []
    for event, entries in (data.get("hooks") or {}).items():
        for entry in entries:
            for h in entry.get("hooks") or []:
                out.append((event, entry.get("matcher", ""), h))
    return out


def commands_of(event: str) -> list[str]:
    return [h.get("command", "") for ev, _, h in registered_by_event() if ev == event]


class SettingsHooksTest(unittest.TestCase):
    def test_every_registered_hook_exists_and_is_executable(self):
        hooks = registered()
        self.assertGreater(len(hooks), 0)
        for matcher, cmd in hooks:
            m = re.fullmatch(r'"\$CLAUDE_PROJECT_DIR"/(\.claude/hooks/[\w.-]+)', cmd)
            self.assertIsNotNone(m, f"hook command must be \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<file>: {cmd}")
            path = ROOT / m.group(1)
            self.assertTrue(path.is_file(), f"missing hook {path}")
            self.assertTrue(os.access(path, os.X_OK), f"hook not executable: {path}")

    def test_matchers_name_real_tools(self):
        for matcher, _ in registered():
            if not matcher:  # Stop / SessionStart entries have no tool matcher
                continue
            for part in matcher.split("|"):
                self.assertTrue(part in KNOWN_TOOLS or part.startswith("mcp__"), f"unknown matcher tool '{part}'")

    def test_every_hook_has_a_test(self):
        tests = {p.name for p in HOOKS.glob("test_*")}
        for _, cmd in registered():
            stem = Path(cmd.split("/")[-1]).stem.replace("-", "_")
            self.assertTrue(any(t.startswith(f"test_{stem}") for t in tests), f"no test_{stem}* for {cmd}")

    def test_the_guards_of_aa_1024_are_registered(self):
        cmds = " ".join(c for _, c in registered())
        for name in ("aa-shell-guard.sh", "lane-start-guard.sh", "subagent-guardrails.sh", "pilot-pii-guard.sh",
                     "stop-dispatch.sh"):
            self.assertIn(name, cmds)
        # AA-1136: stop-open-work.sh (G19) runs inside the merged Stop dispatcher, not as a second Stop hook
        self.assertIn("stop_open_work.check(", (HOOKS / "stop_dispatch.py").read_text(encoding="utf-8"))


class SyncHooksTest(unittest.TestCase):
    """AA-1136: the sync hooks are wired once, with a timeout, and Stop has exactly one hook (one dispatcher)."""

    DISPATCH = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/stop-dispatch.sh'

    def test_one_stop_dispatcher_for_stop_and_subagent_stop(self):
        # Hooks of one event run in parallel and each may take the single block turn (S284 advisory, section 7).
        self.assertEqual(commands_of("Stop"), [self.DISPATCH])
        self.assertEqual(commands_of("SubagentStop"), [self.DISPATCH])

    def test_post_edit_hook_on_edit_tools(self):
        entries = [(m, h) for ev, m, h in registered_by_event() if ev == "PostToolUse"
                   and h.get("command", "").endswith("/sync-post-edit.sh")]
        self.assertEqual(len(entries), 1)
        self.assertEqual(set(entries[0][0].split("|")), {"Edit", "Write", "MultiEdit"})

    def test_sync_hooks_have_a_timeout(self):
        for ev, _, h in registered_by_event():
            if h.get("command", "").endswith(("/sync-post-edit.sh", "/stop-dispatch.sh")):
                self.assertIsInstance(h.get("timeout"), int, ev)
                self.assertLessEqual(h["timeout"], 10, ev)

    def test_wrappers_never_fail_closed(self):
        post = (HOOKS / "sync-post-edit.sh").read_text(encoding="utf-8")
        self.assertTrue(post.rstrip().endswith("exit 0"))
        stop = (HOOKS / "stop-dispatch.sh").read_text(encoding="utf-8")
        self.assertIn('[ "$rc" -eq 2 ] && exit 2', stop)
        self.assertTrue(stop.rstrip().endswith("exit 0"))


if __name__ == "__main__":
    unittest.main()
