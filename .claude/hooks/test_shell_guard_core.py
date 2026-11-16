"""Tests for shell_guard_core.py, the generic shell guard of the new-project kit.

Every generic rule: forms it must refuse, near-misses it must pass. Invented paths and names only; no project names
(the kit's template repo copies this file byte for byte).

Run: python3 .claude/hooks/test_shell_guard_core.py
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shell_guard_core as c  # noqa: E402

# A git hook (pre-push) exports GIT_DIR and friends; a git command run in a temporary repo below would then act on the
# real repo. Drop git's repo-local variables for this whole test process.
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

NO_PROC = Path("/nonexistent-proc")  # memory unreadable: RAM-1's memory part stays quiet
PROJECT = Path("/work/sample-project")  # an invented project root (no file access needed)


def rule(cmd: str, cwd: Path | None = None, proc: Path = NO_PROC) -> str | None:
    with unittest.mock.patch.object(c, "ROOT", PROJECT):
        r = c.check(cmd, cwd=cwd or PROJECT, proc=proc)
    return r.rule if r else None


class LexerTest(unittest.TestCase):
    def test_quotes_comments_and_heredoc_bodies_are_not_code(self):
        sk = c.scan("grep -n 'pkill -f x' a # pkill -f y\ncat > f <<'EOF'\npkill -f z\nEOF\necho done").skeleton
        self.assertNotIn("pkill", sk)
        self.assertIn("echo done", sk)

    def test_bash_c_and_heredoc_bodies_are_read_as_bash(self):
        texts = c.texts_of("bash -c 'echo a'; bash -euo pipefail -c \"echo b\"; zsh -c 'x'")
        self.assertEqual([t.level for t in texts], ["zsh", "bash", "bash", "zsh"])
        self.assertEqual([t.pipefail for t in texts], [False, False, True, False])
        texts = c.texts_of("bash <<'EOF'\necho in-body\nEOF")
        self.assertEqual([t.level for t in texts], ["zsh", "bash"])

    def test_program_unwraps_wrappers(self):
        self.assertEqual(c.program("FOO=1 timeout 60 nohup make test".split())[0], "make")
        self.assertEqual(c.program("env -u NAME terraform plan".split())[0], "terraform")
        self.assertEqual(c.program("bash -e tools/run.sh a".split())[0], "run.sh")
        self.assertEqual(c.program("xargs -n1 -P 4 rm".split())[0], "rm")

    def test_dashdash_wrapper_registry(self):
        words = "tools/wrap.sh --target x -- make build".split()
        self.assertEqual(c.program(words)[0], "wrap.sh")
        with unittest.mock.patch.dict(c.DASHDASH_WRAPPERS, {"wrap.sh": ("--target",)}):
            self.assertEqual(c.program(words), ("make", ["build"]))
            self.assertEqual(c.program("tools/wrap.sh --target x make".split())[0], "make")

    def test_loop_depth(self):
        found = c.commands_with_loop_depth("a; for x in 1 2; do b; done; c")
        self.assertEqual([(w[0], d) for w, d in found], [("a", 0), ("b", 1), ("c", 0)])


class GenericRulesTest(unittest.TestCase):
    def test_pkill(self):
        for cmd in ("pkill -f 'next build'", "until ! pgrep -f worker; do sleep 1; done",
                    "pgrep -f server | xargs kill", "kill $(pgrep -f server)", "bash -c 'pkill -f x'"):
            self.assertEqual(rule(cmd), "PKILL-1", cmd)
        for cmd in ("pkill -x node", "pgrep -f server", "grep 'pkill -f' notes.md", "kill 1234"):
            self.assertIsNone(rule(cmd), cmd)

    def test_zsh_word_splitting(self):
        self.assertEqual(rule('FILES="a b"; for f in $FILES; do echo $f; done'), "ZSH-1")
        self.assertEqual(rule('set -- $ARGS'), "ZSH-1")
        for cmd in ('FILES=(a b); for f in $FILES; do echo $f; done', 'for f in ${=FILES}; do echo $f; done',
                    "bash -c 'for f in $FILES; do echo $f; done'", "for f in a b; do echo $f; done"):
            self.assertIsNone(rule(cmd), cmd)

    def test_export_substitution(self):
        self.assertEqual(rule("export $(cat .env)"), "ENV-1")
        self.assertIsNone(rule("export NAME=value"))
        self.assertIsNone(rule("echo 'export $(x)'"))

    def test_background_to_dev_null(self):
        for cmd in ("make serve >/dev/null 2>&1 &", "make serve &>/dev/null &", "nohup make serve >/dev/null"):
            self.assertEqual(rule(cmd), "BG-1", cmd)
        for cmd in ("make serve > .tmp-session/serve.log 2>&1 &", "make a >/dev/null 2>&1 && make b",
                    "for u in a b; do curl -s $u >/dev/null 2>&1 & done; wait"):
            self.assertIsNone(rule(cmd), cmd)

    def test_worktree_path(self):
        base = f"{PROJECT}/.tmp-session/wt"
        for cmd in ("git worktree add ../wt-x -b feat/x origin/main", "git worktree add -q /tmp/x origin/main",
                    "git -C child worktree add .tmp-session/wt/s1-x origin/main",
                    "cd \"$REPO\" && git worktree add .tmp-session/wt/s1-x origin/main"):
            self.assertEqual(rule(cmd), "WT-1", cmd)
        for cmd in (f"git worktree add {base}/s1-lane -b feat/x origin/main",
                    "git worktree add .tmp-session/wt/s1-rel origin/main", "git worktree add \"$WT\" origin/main",
                    "git worktree list"):
            self.assertIsNone(rule(cmd), cmd)

    def test_worktree_extra_bases(self):
        t = c.texts_of("git worktree add /shared/.tmp-session/wt/s1-x origin/main")[0]
        self.assertIsNotNone(c.worktree_check(t, PROJECT, (f"{PROJECT}/.tmp-session/wt/",)))
        self.assertIsNone(c.worktree_check(t, PROJECT, (f"{PROJECT}/.tmp-session/wt/", "/shared/.tmp-session/wt/")))

    def test_terraform_from_lane_or_branch(self):
        self.assertEqual(rule("cd .tmp-session/wt/s1-x/infra && terraform apply"), "TF-1")
        self.assertIsNone(rule("terraform plan", cwd=PROJECT / ".tmp-session/wt/s1-x"))
        with tempfile.TemporaryDirectory() as d:
            run = {"cwd": d, "check": True, "capture_output": True}
            subprocess.run(["git", "init", "-q", "-b", "feature"], **run)
            self.assertEqual(rule("terraform apply", cwd=Path(d)), "TF-1")
            subprocess.run(["git", "checkout", "-q", "-b", "main"], **run)
            self.assertIsNone(rule("terraform apply", cwd=Path(d)))


class RamTest(unittest.TestCase):
    def fake_proc(self, d: Path, avail_kib: int, heavy: int = 0) -> Path:
        (d / "meminfo").write_text(f"MemTotal: 9000000 kB\nMemAvailable: {avail_kib} kB\n")
        for i in range(heavy):
            p = d / str(10 + i)
            p.mkdir()
            (p / "cmdline").write_bytes(b"node\x00next\x00build\x00")
            (p / "status").write_text("VmRSS: 512000 kB\n")
        return d

    def test_heavy_commands(self):
        for cmd, name in (("npx next build", "next build"), ("npm ci", "npm ci"), ("tsc --noEmit", "tsc"),
                          ("pytest -n 4 tests/unit/test_a.py", "pytest -n (xdist)"),
                          ("python -m pytest tests", "pytest over a whole directory")):
            self.assertEqual(c.heavy_command(cmd.split()), name, cmd)
        self.assertIsNone(c.heavy_command("pytest tests/unit/test_a.py".split()))
        self.assertIsNone(c.heavy_command("ls -la".split()))

    def test_pushers_registry(self):
        self.assertIsNone(c.heavy_command("python3 tools/release_all.py".split()))
        with unittest.mock.patch.object(c, "PUSHERS", {"release_all.py"}):
            self.assertIsNotNone(c.heavy_command("python3 tools/release_all.py".split()))
            self.assertIsNone(c.heavy_command("python3 tools/release_all.py --dry-run".split()))

    def test_low_memory_refuses_heavy_and_override_passes(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 1024 * 1024)  # 1 GiB available
            self.assertEqual(rule("npm ci", proc=proc), "RAM-1")
            self.assertIsNone(rule("ls", proc=proc))
            with unittest.mock.patch.object(c, "HITS_LOG", Path(d) / "hits.log"):
                self.assertIsNone(rule("GUARD_RAM_OVERRIDE=1 npm ci", proc=proc))

    def test_busy_machine_refuses_and_free_machine_passes(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 3 * 1024 * 1024, heavy=c.MAX_HEAVY)
            self.assertEqual(rule("npm ci", proc=proc), "RAM-1")
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 8 * 1024 * 1024)
            self.assertIsNone(rule("npm ci", proc=proc))

    def test_lane_pytest_is_refused_whatever_the_memory(self):
        lane = PROJECT / ".tmp-session/wt/s1-lane"
        for cmd in ("pytest -n 8 tests/unit/test_a.py", "pytest tests/unit", "python -m pytest", "pytest -n auto x.py"):
            self.assertEqual(rule(cmd, cwd=lane), "RAM-1", cmd)
        for cmd in ("pytest -n 2 tests/unit/test_a.py", "pytest tests/unit/test_a.py::test_x", "pytest -q $FILES"):
            self.assertIsNone(rule(cmd, cwd=lane), cmd)
        self.assertIsNone(rule("pytest tests/unit", cwd=PROJECT))  # outside a lane: only the memory part applies


class HookTest(unittest.TestCase):
    def run_hook(self, payload: str) -> tuple[int, str]:
        err = io.StringIO()
        with unittest.mock.patch.object(sys, "stdin", io.StringIO(payload)), \
                unittest.mock.patch.object(sys, "stderr", err), \
                tempfile.TemporaryDirectory() as d, \
                unittest.mock.patch.object(c, "HITS_LOG", Path(d) / "hits.log"):
            code = c.run_hook(lambda cmd, cwd: c.check(cmd, cwd, NO_PROC))
        return code, err.getvalue()

    def test_refusal_exits_2_with_the_fix(self):
        code, err = self.run_hook(json.dumps({"tool_input": {"command": "export $(cat x)"}, "cwd": str(PROJECT)}))
        self.assertEqual(code, 2)
        self.assertIn("ENV-1", err)
        self.assertIn(c.FIX["ENV-1"], err)

    def test_unreadable_input_and_internal_errors_pass(self):
        self.assertEqual(self.run_hook("not json")[0], 0)
        self.assertEqual(self.run_hook(json.dumps({"tool_input": {}}))[0], 0)
        err = io.StringIO()
        payload = json.dumps({"tool_input": {"command": "ls"}})
        with unittest.mock.patch.object(sys, "stdin", io.StringIO(payload)), \
                unittest.mock.patch.object(sys, "stderr", err):
            self.assertEqual(c.run_hook(lambda cmd, cwd: 1 / 0), 0)
        self.assertIn("internal error", err.getvalue())

    def test_every_rule_has_a_fix(self):
        for r in c.RULE_IDS:
            self.assertIn(r, c.FIX)


if __name__ == "__main__":
    unittest.main()
