"""Tests for aa_shell_guard.py (AA-1024 G2/G4 + G1 SHIP-1). Every rule: forms it must refuse, near-misses it must pass.

Run: python3 .claude/hooks/test_aa_shell_guard.py   (root CI: Docs lint, "Claude hook tests")
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import aa_shell_guard as g  # noqa: E402

NO_PROC = Path("/nonexistent-proc")  # memory unreadable: RAM-1 stays quiet in the rule tests


def rule(cmd: str, cwd: Path | None = None) -> str | None:
    r = g.check(cmd, cwd=cwd, proc=NO_PROC)
    return r.rule if r else None


class LexerTest(unittest.TestCase):
    def test_quotes_comments_and_heredoc_bodies_are_not_code(self):
        sk = g.scan("grep -n 'pkill -f x' a # pkill -f y\ncat > f <<'EOF'\npkill -f z\nEOF\necho done").skeleton
        self.assertNotIn("pkill", sk)
        self.assertIn("echo done", sk)

    def test_bash_c_and_bash_heredoc_bodies_are_read_as_bash(self):
        levels = [t.level for t in g.texts_of("bash -c 'echo a'; bash -euo pipefail -c \"echo b\"; zsh -c 'x'")]
        self.assertEqual(levels, ["zsh", "bash", "bash", "zsh"])
        texts = g.texts_of("bash <<'EOF'\necho in-body\nEOF")
        self.assertEqual([t.level for t in texts], ["zsh", "bash"])
        self.assertIn("echo in-body", texts[1].skeleton)

    def test_program_unwraps_wrappers(self):
        self.assertEqual(g.program("FOO=1 timeout 60 nohup gh pr view 1".split())[0], "gh")
        self.assertEqual(g.program("tools/github/as-app.sh --repos X -- gh pr merge 1".split())[:2],
                         ("gh", ["pr", "merge", "1"]))
        self.assertEqual(g.program("bash -e tools/x/run.sh a".split())[0], "run.sh")
        self.assertEqual(g.program("xargs -n1 -P 4 gh pr merge".split())[0], "gh")


class PkillTest(unittest.TestCase):
    def test_refused(self):
        for cmd in (
            "pkill -f 'next-server'",
            "sudo pkill -9 -f uvicorn",
            "bash -c 'pkill -f vite'",
            "until ! pgrep -f 'pytest tests'; do sleep 5; done",
            "while pgrep -f next >/dev/null; do sleep 2; done",
            "pgrep -f node | xargs kill",
            "pgrep -f uvicorn | while read p; do kill $p; done",
            "kill $(pgrep -f 'next dev')",
            "ps aux | grep next | awk '{print $2}' | xargs kill",
            "bash <<'EOF'\npkill -f worker\nEOF",
        ):
            self.assertEqual(rule(cmd), "PKILL-1", cmd)

    def test_near_misses_pass(self):
        for cmd in (
            "pgrep -fa node | head",
            "pgrep -f next",
            "pkill -x node",
            "kill 12345",
            "grep -n 'pkill -f' skill/aa-lessons/lessons.md",
            "echo \"never use pkill -f\"",
            "cat > /tmp/x.sh <<'EOF'\npkill -f a\nEOF",
            "kill -0 $PID 2>/dev/null && echo running",
        ):
            self.assertIsNone(rule(cmd), cmd)


class ZshTest(unittest.TestCase):
    def test_refused_at_zsh_level(self):
        for cmd in (
            "FILES=$(ls); for f in $FILES; do echo $f; done",
            "for x in ${LIST}; do echo $x; done",
            "set -- $LINE; echo $1",
        ):
            self.assertEqual(rule(cmd), "ZSH-1", cmd)

    def test_near_misses_pass(self):
        for cmd in (
            "bash -c 'for f in $FILES; do echo $f; done'",
            "bash <<'EOF'\nset -- $LINE\nfor f in $FILES; do echo; done\nEOF",
            "A=(one two); for x in $A; do echo $x; done",
            "for x in ${=LIST}; do echo $x; done",
            'for x in "$@"; do echo $x; done',
            "for i in $(seq 1 3); do echo $i; done",
            "for n in 374 375; do echo $n; done",
            'for x in "$V"; do :; done',
            "echo 'for x in $V'",
        ):
            self.assertIsNone(rule(cmd), cmd)


class EnvTest(unittest.TestCase):
    def test_refused(self):
        self.assertEqual(rule("export $(cat .env | xargs)"), "ENV-1")
        self.assertEqual(rule("bash -c 'export $(aws configure export-credentials --format env-no-export)'"), "ENV-1")
        self.assertEqual(rule("export `cat x`"), "ENV-1")

    def test_near_misses_pass(self):
        for cmd in ("export FOO=1", "export PATH=\"$HOME/.nvm/bin:$PATH\"", "grep -n 'export $(' x",
                    "C=$(aws configure export-credentials --format env-no-export </dev/null); env -u AWS_PROFILE "
                    "$(tr '\\n' ' ' <<<\"$C\") terraform plan"):
            self.assertIsNone(rule(cmd), cmd)


class ShipTest(unittest.TestCase):
    def test_raw_merges_refused(self):
        for cmd in (
            "gh pr merge 438 --squash",
            "gh pr merge 5 -R AdventureAsia365-Ecosys/AA-Ecosys --squash --admin",
            "tools/github/as-app.sh --repos AA-CIS-Infra -- gh pr merge 483 -R x/AA-CIS-Infra --squash",
            "/home/nghiep/projects/AA-Ecosys/tools/github/as-app.sh -- gh pr merge 1 --squash",
            "echo 1 2 | xargs -n1 gh pr merge",
            "bash -c 'gh pr merge 1 --squash'",
            "tools/github/mergeq.sh AA-CIS-App 1350",
            "bash tools/github/mergeq.sh AA-Booking 7",
            "timeout 600 tools/github/mergeq.sh AA-Partner 45 &",
            # merges through the API (the first form is the one found in the S271 transcripts)
            "tools/github/as-app.sh --repos AA-CIS-Infra -- gh api -X PUT "
            "repos/AdventureAsia365-Ecosys/AA-CIS-Infra/pulls/663/merge -f merge_method=squash",
            "gh api -X PUT repos/o/r/pulls/5/merge",
            "gh api --method put 'repos/o/r/pulls/5/merge'",
            "gh api -XPUT \"repos/o/r/pulls/$N/merge\"",
            "gh api repos/o/r/pulls/5/merge -f merge_method=squash",
            "gh api graphql -f query='mutation{enqueuePullRequest(input:{pullRequestId:\"x\"}){clientMutationId}}'",
            "gh api graphql -f query='mutation{mergePullRequest(input:{pullRequestId:\"x\"}){clientMutationId}}'",
            "tools/github/as-app.sh -- gh api graphql -f query=\"mutation { mergePullRequest(input: $IN) { a } }\"",
            "bash -c 'gh api -X PUT repos/o/r/pulls/5/merge'",
        ):
            self.assertEqual(rule(cmd), "SHIP-1", cmd)

    def test_serial_ship_merge_refused(self):
        for cmd in (
            "for n in 1349 1350; do python3 tools/github/ship_merge.py cis#$n; done",
            "python3 tools/github/ship_merge.py cis#1 && python3 tools/github/ship_merge.py cis#2",
            "while read n; do tools/github/ship_merge.py cis#$n; done < prs.txt",
        ):
            self.assertEqual(rule(cmd), "SHIP-1", cmd)

    def test_ship_tools_and_reads_pass(self):
        for cmd in (
            "python3 tools/github/ship_merge.py cis#1349 cis#1350 root#601 infra#480",
            "python3 tools/github/ship_merge.py --check-only cis#1349",
            "python3 tools/github/ship_wave.py cis#1350 'cis#1349>apply:cis/383' 'cis#1352@after=cis/383' "
            "--wait-deploy",
            "python3 tools/github/ship_train.py AA-Partner /x feat/a:1 feat/b:2",
            "tools/github/mergeq.sh AA-CIS-App 1350 --dequeue",
            "gh pr merge 1350 -R x --disable-auto",
            "cat tools/github/mergeq.sh",
            "grep -n 'gh pr merge' skill/aa-ship/SKILL.md",
            "gh pr view 5 --json state",
            "python -m unittest discover -s tools/github -p 'test_*.py'",
            "for n in 1 2; do gh pr checks $n; done",
            "gh api repos/o/r/pulls/5/merge",  # GET: is it merged?
            "gh api -X GET repos/o/r/pulls/5/merge",
            "gh api repos/o/r/pulls/5 --jq .mergeable_state",
            "gh api -X PATCH repos/o/r/pulls/5 -f title=x",
            "gh api graphql -f query='mutation($id:ID!){dequeuePullRequest(input:{id:$id}){clientMutationId}}'",
            "gh api graphql -f query='{repository(owner:\"o\",name:\"r\"){pullRequest(number:5){isInMergeQueue}}}'",
            "grep -n 'mergePullRequest' tools/github/README.md",
        ):
            self.assertIsNone(rule(cmd), cmd)

    def test_hand_written_scripts_that_merge_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".tmp-session" / "S999").mkdir(parents=True)
            ship = root / ".tmp-session" / "S999" / "ship_w9.sh"
            ship.write_text("#!/bin/bash\nfor n in 1 2; do\n  tools/github/mergeq.sh AA-CIS-App $n\ndone\n")
            pyship = root / ".tmp-session" / "S999" / "ship.py"
            pyship.write_text("import subprocess\nsubprocess.run(['gh', 'pr', 'merge', '1'])\n")
            reader = root / ".tmp-session" / "S999" / "report.sh"
            reader.write_text("#!/bin/bash\n# mergeq.sh is mentioned in a comment only\ngh pr checks 1\n")
            killer = root / ".tmp-session" / "S999" / "stop.sh"
            killer.write_text("#!/bin/bash\npkill -f 'next build'\n")
            api_ship = root / ".tmp-session" / "S999" / "api_ship.sh"
            api_ship.write_text("#!/bin/bash\nfor n in 1 2; do\n  gh api -X PUT \"repos/o/r/pulls/$n/merge\"\ndone\n")
            wt_tool = root / ".tmp-session" / "wt" / "s999-lane" / "tools" / "github"
            wt_tool.mkdir(parents=True)
            (wt_tool / "mergeq.sh").write_text("gh pr merge \"$N\"\n")
            old = g.ROOT
            g.ROOT = root
            try:
                abs_ship = str(ship)
                for cmd in (f"bash {abs_ship}", "bash .tmp-session/S999/ship_w9.sh", f"{abs_ship} &",
                            f"nohup bash {abs_ship} > /dev/null 2>&1 &",
                            f"source <(sed -n '1,4p' {abs_ship}); merge 1", "python3 .tmp-session/S999/ship.py",
                            "bash .tmp-session/S999/api_ship.sh"):
                    self.assertEqual(rule(cmd, cwd=root), "SHIP-1", cmd)
                # A script's command line is `bash <path>`: pkill -f inside it does not match itself.
                self.assertIsNone(rule("bash .tmp-session/S999/stop.sh", cwd=root))
                for cmd in (f"cat {abs_ship}", f"grep -n mergeq {abs_ship}", "bash .tmp-session/S999/report.sh",
                            "bash .tmp-session/S999/missing.sh",
                            "bash .tmp-session/wt/s999-lane/tools/github/mergeq.sh AA-CIS-App 1 --dequeue"):
                    self.assertIsNone(rule(cmd, cwd=root), cmd)
            finally:
                g.ROOT = old


class RamTest(unittest.TestCase):
    def fake_proc(self, d: Path, avail_mib: int, procs: list[tuple[int, str, int]]) -> Path:
        (d / "meminfo").write_text(f"MemTotal: 10000000 kB\nMemAvailable: {avail_mib * 1024} kB\n")
        for pid, cmdline, rss in procs:
            p = d / str(pid)
            p.mkdir()
            (p / "cmdline").write_bytes(cmdline.replace(" ", "\x00").encode() + b"\x00")
            (p / "status").write_text(f"Name: x\nVmRSS: {rss * 1024} kB\n")
        return d

    def test_heavy_classifier(self):
        heavy = ["npx next build", "NODE_OPTIONS=--max-old-space-size=2048 npm run build", "npm ci",
                 "npx playwright test --project smoke", "npx vitest run", "npx tsc --noEmit", "docker build .",
                 "pytest tests/unit -q", "python -m pytest -q", "pytest -n 4 tests/unit/test_a.py",
                 "node tools/uat/run_scenario.cjs"]
        light = ["pytest -x -q tests/unit/test_a.py", "python3 -m pytest tests/unit/test_a.py::test_b",
                 "npm run lint", "node script.js", "git status", "python3 -m unittest discover -s tools"]
        for c in heavy:
            self.assertTrue(g.heavy_command(c.split()), c)
        for c in light:
            self.assertIsNone(g.heavy_command(c.split()), c)

    def test_low_memory_refuses_heavy_and_names_what_runs(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 1500, [(101, "node /x/node_modules/.bin/next build", 1800),
                                                  (102, "/usr/bin/python3 -m pytest tests/unit", 900)])
            r = g.check("cd frontend && npx next build", proc=proc)
            self.assertEqual(r.rule, "RAM-1")
            self.assertIn("MemAvailable 1500 MiB", r.detail)
            self.assertIn("next build", r.detail)
            self.assertIn("pid 101", r.detail)
            self.assertIsNone(g.check("pytest -x tests/unit/test_one.py", proc=proc))
            self.assertIsNone(g.check("git status", proc=proc))
            self.assertIsNone(g.check("AA_RAM_OVERRIDE=1 npx next build", proc=proc))

    def test_busy_machine_refuses_with_three_heavy_running(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 3500, [(201, "node next build", 1500), (202, "python3 -m pytest a", 500),
                                                  (203, "node playwright test", 400)])
            self.assertEqual(g.check("npx tsc --noEmit", proc=proc).rule, "RAM-1")
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 3500, [(201, "node next build", 1500)])
            self.assertIsNone(g.check("npx tsc --noEmit", proc=proc))
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 6000, [(201, "node next build", 1500), (202, "pytest a", 1),
                                                  (203, "node playwright test", 1)])
            self.assertIsNone(g.check("npx next build", proc=proc))

    def test_shell_whose_command_line_mentions_pytest_is_not_a_heavy_process(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 3000, [])
            p = Path(d) / "300"
            p.mkdir()
            (p / "cmdline").write_bytes(b"/bin/zsh\x00-c\x00cd x && pytest tests/unit\x00")
            (p / "status").write_text("VmRSS: 4000 kB\n")
            self.assertEqual([x[2] for x in g.processes(Path(d))], [""])


class HookIoTest(unittest.TestCase):
    def run_hook(self, payload) -> subprocess.CompletedProcess:
        env = dict(os.environ, CLAUDE_PROJECT_DIR=tempfile.gettempdir())
        return subprocess.run([sys.executable, str(HERE / "aa_shell_guard.py")], input=payload, text=True,
                              capture_output=True, env=env, timeout=30)

    def test_exit_codes(self):
        r = self.run_hook(json.dumps({"tool_input": {"command": "pkill -f next"}}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("aa_shell_guard PKILL-1", r.stderr)
        self.assertEqual(self.run_hook(json.dumps({"tool_input": {"command": "git status"}})).returncode, 0)
        self.assertEqual(self.run_hook("not json").returncode, 0)
        self.assertEqual(self.run_hook(json.dumps({"tool_input": {}})).returncode, 0)

    def test_wrapper_script_runs_the_guard(self):
        sh = HERE / "aa-shell-guard.sh"
        self.assertTrue(os.access(sh, os.X_OK))
        r = subprocess.run([str(sh)], input=json.dumps({"tool_input": {"command": "export $(cat x)"}}), text=True,
                           capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
