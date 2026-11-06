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
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    out = []
    for event, entries in (data.get("hooks") or {}).items():
        for entry in entries:
            for h in entry.get("hooks") or []:
                out.append((entry.get("matcher", ""), h.get("command", "")))
    return out


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
            for part in matcher.split("|"):
                self.assertTrue(part in KNOWN_TOOLS or part.startswith("mcp__"), f"unknown matcher tool '{part}'")

    def test_every_hook_has_a_test(self):
        tests = {p.name for p in HOOKS.glob("test_*")}
        for _, cmd in registered():
            stem = Path(cmd.split("/")[-1]).stem.replace("-", "_")
            if stem == "subagent_mcp_guardrails":  # a 20-line pattern list, red-teamed by hand (AA-1032)
                continue
            self.assertTrue(any(t.startswith(f"test_{stem}") for t in tests), f"no test_{stem}* for {cmd}")

    def test_the_guards_of_aa_1024_are_registered(self):
        cmds = " ".join(c for _, c in registered())
        for name in ("aa-shell-guard.sh", "lane-start-guard.sh", "subagent-guardrails.sh", "pilot-pii-guard.sh"):
            self.assertIn(name, cmds)


if __name__ == "__main__":
    unittest.main()
