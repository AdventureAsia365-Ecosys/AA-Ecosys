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

# S272: a git hook (pre-push) exports GIT_DIR and friends; a git command run in a temporary repo below would then act
# on the real repo (a hook-run test once set core.bare, a fake identity and refs in an app clone). Drop git's
# repo-local variables for this whole test process (the list is `git rev-parse --local-env-vars`; test_git_env_isolation).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

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


class EcsExecTest(unittest.TestCase):
    """ECS-1 (AA-1024 G3): raw ECS exec loses output; tools/ecs/ecsx.sh is the way."""

    def test_refused(self):
        for cmd in (
            "aws ecs execute-command --cluster c --task $T --container api --interactive --command \"sh -c 'x'\"",
            "aws --profile aa365-admin --region us-west-1 ecs execute-command --cluster c --task t --command ls",
            "timeout 90 aws ecs execute-command --cluster c --task t --command ls --profile p",
            "bash -c 'aws ecs execute-command --cluster c --task t --command ls'",
            "AA_RAM_OVERRIDE=1 aws ecs execute-command --cluster c --task t --command ls",
        ):
            self.assertEqual(rule(cmd), "ECS-1", cmd)

    def test_near_misses_pass(self):
        for cmd in (
            "aws ecs describe-services --cluster c --services s",
            "aws ecs list-tasks --cluster c --service-name s --query 'taskArns[0]'",
            "grep -n 'aws ecs execute-command' docs/ops/runbooks/ecs-exec-s3-mediated.md",
            "cat tools/ecs/ecsx_local.py",
            "echo \"never aws ecs execute-command by hand\"",
            "tools/ecs/ecsx.sh .tmp-session/S999/check.py LIMIT=5",
            "AA_ECSX_BYPASS=1 aws ecs execute-command --cluster c --task t --command ls",
        ):
            self.assertIsNone(rule(cmd), cmd)

    def test_scripts_that_exec_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = root / ".tmp-session" / "S999"
            s.mkdir(parents=True)
            (s / "one.sh").write_text("#!/bin/bash\nT=$(aws ecs list-tasks)\naws ecs execute-command --task $T\n")
            (s / "one.py").write_text("import subprocess\nsubprocess.run(['aws', 'ecs', 'execute-command'])\n")
            (s / "note.sh").write_text("#!/bin/bash\n# aws ecs execute-command was the old way\necho hi\n")
            old = g.ROOT
            g.ROOT = root
            try:
                self.assertEqual(rule("bash .tmp-session/S999/one.sh", cwd=root), "ECS-1")
                self.assertEqual(rule("python3 .tmp-session/S999/one.py", cwd=root), "ECS-1")
                self.assertIsNone(rule("bash .tmp-session/S999/note.sh", cwd=root))
                self.assertIsNone(rule("cat .tmp-session/S999/one.sh", cwd=root))
                self.assertIsNone(rule("AA_ECSX_BYPASS=1 bash .tmp-session/S999/one.sh", cwd=root))
            finally:
                g.ROOT = old


WS = Path("/home/nghiep/projects/AA-Ecosys")  # the workspace root a session runs in (no file access needed)


class WorktreeTest(unittest.TestCase):
    """WT-1 (G2): a worktree path, resolved the way git resolves it, must be <workspace>/.tmp-session/wt/<name>."""

    def test_refused(self):
        for cmd in (
            "git -C infra/AA-CIS-Infra worktree add .tmp-session/wt/s9-x -b feat/x origin/main",
            "git worktree add -b feat/x ../wt-x origin/main",
            "git -C apps/AA-CIS-App worktree add --detach wt/x",
            "git worktree add -q /tmp/x origin/main",
            "git -C $REPO worktree add wt/x origin/main",
            "cd apps/AA-Booking && git worktree add .tmp-session/wt/s9-z origin/main",
        ):
            self.assertEqual(rule(cmd, cwd=WS), "WT-1", cmd)

    def test_near_misses_pass(self):
        base = f"{WS}/.tmp-session/wt"
        for cmd in (
            f"git -C apps/AA-CIS-App worktree add {base}/s272-l8-x -b feat/x origin/main",
            f"git worktree add -b feat/x -q {base}/s272-l8-y origin/main",
            "git -C apps/AA-Booking worktree add $W -b feat/x origin/main",
            "git worktree add \"$WT\" origin/main",
            "git worktree list --porcelain",
            "git worktree remove .tmp-session/wt/s9-x",
            "grep -n 'git worktree add wt' x.md",
            "git worktree add .tmp-session/wt/s9-rel -b x origin/master",
            "cd infra/AA-CIS-Infra && git worktree add -q ../../.tmp-session/wt/s9-y -b x origin/main",
            "git -C apps/AA-Partner worktree add ../../.tmp-session/wt/s9-p origin/main",
        ):
            self.assertIsNone(rule(cmd, cwd=WS), cmd)


class BackgroundTest(unittest.TestCase):
    """BG-1 (G2): a background job must keep its output somewhere readable."""

    def test_refused(self):
        for cmd in (
            "python3 long.py >/dev/null 2>&1 &",
            "uvicorn app:app > /dev/null 2>&1 & echo started",
            "node server.js &>/dev/null &",
            "nohup python3 long.py > /dev/null 2>&1",
            "setsid ./run.sh >/dev/null 2>/dev/null &",
            "(bash .tmp-session/S999/wave.sh > /dev/null 2>&1 &)",
            "cd site && python3 -m http.server 8765 >/dev/null 2>&1 & echo $! > srv.pid",
        ):
            self.assertEqual(rule(cmd), "BG-1", cmd)

    def test_near_misses_pass(self):
        for cmd in (
            "mkdir -p x >/dev/null 2>&1 && cp a b",
            "command -v gitleaks >/dev/null 2>&1 || echo none",
            "python3 long.py > .tmp-session/S999/long.log 2>&1 &",
            "nohup python3 long.py > .tmp-session/S999/long.log 2>&1 &",
            "nohup x > a.log 2>&1 && cat y >/dev/null",
            "pg_ctl start -l /tmp/pg.log 2>/dev/null &",
            "echo 'cmd >/dev/null 2>&1 &'",
            "(long.sh > .tmp-session/S999/a.log 2>&1; echo rc=$? >> .tmp-session/S999/a.log) </dev/null >/dev/null 2>&1 &",
        ):
            self.assertIsNone(rule(cmd), cmd)


class TerraformTest(unittest.TestCase):
    """TF-1 (G2): terraform apply only from main, never from a lane worktree."""

    def test_refused_in_a_lane_worktree(self):
        wt = f"{g.ROOT}/.tmp-session/wt/s999-lane-infra"
        for cmd in (f"terraform -chdir={wt}/accounts/aa365 apply plan.tfplan",
                    f"cd {wt}/accounts/aa365 && terraform apply -auto-approve",
                    f"terraform -chdir={wt} destroy"):
            self.assertEqual(rule(cmd), "TF-1", cmd)
        self.assertEqual(rule("terraform apply", cwd=Path(wt)), "TF-1")

    def test_refused_off_main(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", "-b", "feat/x", d], check=True)
            self.assertEqual(rule("terraform apply plan.tfplan", cwd=Path(d)), "TF-1")
            self.assertIsNone(rule("terraform plan -out plan.tfplan", cwd=Path(d)))
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
            self.assertIsNone(rule("terraform apply plan.tfplan", cwd=Path(d)))

    def test_plans_and_reads_pass(self):
        wt = f"{g.ROOT}/.tmp-session/wt/s999-lane-infra"
        for cmd in (f"terraform -chdir={wt} plan", f"cd {wt} && terraform validate", "terraform fmt -check",
                    "grep -n 'terraform apply' README.md"):
            self.assertIsNone(rule(cmd), cmd)


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
                 "node tools/uat/run_scenario.cjs", "git push -u origin feat/x", "git -C /w/cis push origin b",
                 "tools/github/as-app.sh --repos AA-CIS-App -- git -C /w push -q -u origin b",
                 "bash scripts/pre-push.sh --full", "python3 tools/github/ship_open_prs.py wf_1",
                 "python3 tools/github/ship_wave.py cis#1 cis#2"]
        light = ["pytest -x -q tests/unit/test_a.py", "python3 -m pytest tests/unit/test_a.py::test_b",
                 "npm run lint", "node script.js", "git status", "python3 -m unittest discover -s tools",
                 "git push --no-verify origin b", "git push --dry-run origin b", "git push origin --delete b",
                 "git push origin :b", "bash scripts/pre-push.sh --self-test", "scripts/pre-push.sh --plan",
                 "python3 tools/github/ship_wave.py --dry-run cis#1", "git log --oneline"]
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

    def test_push_counts_as_heavy_and_a_running_hook_counts_as_running(self):
        # S272: a CIS push ran its pre-push hook (about 5,000 unit tests) while 5 lanes ran, and the VM died
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 1800, [(301, "bash /w/cis/scripts/pre-push.sh --hook origin u", 20),
                                                  (302, "/usr/bin/python3 -m pytest tests/unit", 1400)])
            r = g.check("git -C /w/cis push -u origin feat/x", proc=proc)
            self.assertEqual(r.rule, "RAM-1")
            self.assertIn("pre-push hook", r.detail)
            self.assertIsNone(g.check("git -C /w/cis push --no-verify origin feat/x", proc=proc))
            self.assertIsNone(g.check("AA_RAM_OVERRIDE=1 git push origin feat/x", proc=proc))
        with tempfile.TemporaryDirectory() as d:
            proc = self.fake_proc(Path(d), 6000, [])
            self.assertIsNone(g.check("git push origin feat/x", proc=proc))

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
