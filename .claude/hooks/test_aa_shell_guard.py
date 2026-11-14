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
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import aa_shell_guard as g  # noqa: E402

# S272: a git hook (pre-push) exports GIT_DIR and friends; a git command run in a temporary repo below would then act
# on the real repo (a hook-run test once set core.bare, a fake identity and refs in an app clone). Drop git's
# repo-local variables for this whole test process (`git rev-parse --local-env-vars`; test_git_env_isolation.py).
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
        texts = g.texts_of("bash -c 'echo a'; bash -euo pipefail -c \"echo b\"; zsh -c 'x'")
        self.assertEqual([t.level for t in texts], ["zsh", "bash", "bash", "zsh"])
        self.assertEqual([t.pipefail for t in texts], [False, False, True, False])
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
            # a merge in the body of a loop that follows another loop
            "for u in a b; do curl -s $u; done; for n in 1 2; do python3 tools/github/ship_merge.py cis#$n; done",
            # nested: the merge sits in the inner loop
            "for r in a b; do for n in 1 2; do python3 tools/github/ship_merge.py $r#$n; done; done",
            "until python3 tools/github/ship_merge.py cis#1; do sleep 60; done",
        ):
            self.assertEqual(rule(cmd), "SHIP-1", cmd)

    def test_one_merge_beside_a_loop_passes(self):
        # S272 review: replayed orchestrator one-liners (06/11) that merge once, then verify in a loop, or wait for
        # checks in a loop, then merge once. The merge is outside every loop body.
        for cmd in (
            "python3 tools/github/ship_merge.py 'AA-CIS-App 1344' 2>&1 | tail -1; for s in aa-cis-dev-api "
            "aa-cis-dev-worker; do aws ecs describe-services --cluster aa-cis-dev-cluster --services $s "
            "--query 'services[0].deployments[0].rolloutState' --output text; done; "
            "curl -s https://api-cis.lumiguides.it.com/health",
            "for x in 'AA-CIS-App 1343' 'AA-Booking 203'; do gh pr checks $n --watch; done; "
            "python3 tools/github/ship_merge.py 'AA-CIS-App 1343' 'AA-Booking 203'",
            "python3 tools/github/ship_merge.py cis#1344 && for u in a b; do curl -s $u; done",
            "while ! gh pr checks 5 >/dev/null; do sleep 30; done\npython3 tools/github/ship_merge.py root#5",
        ):
            self.assertIsNone(rule(cmd), cmd)

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


class PipeExitTest(unittest.TestCase):
    """PIPE-1 (S272, S273): a ship step piped through tail/head/tee and chained with && runs the next step after a
    failure, because the pipeline exits with the tail's code."""

    def test_refused(self):
        for cmd in (
            # the S273 shape: the registry PR merge failed, the apply still ran
            "python3 tools/github/ship_merge.py infra#732 2>&1 | tail -5 && tools/github/dbmig.sh tp/tp-027_x.sql "
            "apply",
            # the S272 shape: merge red, copy/apply and `gh pr ready` still ran
            "python3 tools/github/ship_merge.py cis#1374 | tail -3 && python3 tools/github/ship_copy_apply.py "
            "cis/389 && gh pr ready 1368",
            "python3 tools/github/ship_wave.py cis#1 'cis#2>apply:cis/390' 2>&1 | head -40 && echo shipped",
            "tools/github/dbmig.sh cis/390_x.sql apply |& tail -2 && curl -s https://example.invalid/health",
            "python3 tools/github/ship_open_prs.py --lane x | tee .tmp-session/S999/open.log && gh pr list",
            "(python3 tools/github/ship_merge.py root#5 2>&1 | tail -1) && git -C . pull",
            "bash -c 'python3 tools/github/ship_merge.py root#5 | tail -1 && echo next'",
            "tools/github/as-app.sh --repos AA-CIS-App -- gh workflow run deploy.yml 2>&1 | tail -3 && echo next",
            "tools/github/as-app.sh --repos AA-CIS-App -- gh pr ready 5 | tail -1 && python3 tools/github/"
            "ship_merge.py cis#5",
            "tools/github/as-app.sh --repos AA-CIS-App -- gh api -X POST repos/o/r/dispatches | head -1 && echo x",
            # `+o pipefail` turns it off
            "set +o pipefail; python3 tools/github/ship_merge.py root#5 | tail -1 && echo next",
            # pipefail set AFTER the pipeline does not count
            "python3 tools/github/ship_merge.py root#5 | tail -1 && set -o pipefail",
            "bash -o pipefail -c 'true'; bash -c 'tools/github/dbmig.sh cis/1_x.sql apply | tail -1 && echo next'",
        ):
            self.assertEqual(rule(cmd), "PIPE-1", cmd)

    def test_near_misses_pass(self):
        for cmd in (
            "set -o pipefail; python3 tools/github/ship_merge.py root#5 2>&1 | tail -1 && echo next",
            "set -euo pipefail\npython3 tools/github/ship_merge.py root#5 | tail -1 && echo next",
            "setopt pipefail; tools/github/dbmig.sh cis/1_x.sql apply | tail -3 && echo next",
            "bash -o pipefail -c 'python3 tools/github/ship_merge.py root#5 | tail -1 && echo next'",
            "bash -euo pipefail -c 'tools/github/dbmig.sh cis/1_x.sql apply | head -5 && echo next'",
            # option groups before `-o pipefail` (review S274)
            "set -e -o pipefail; python3 tools/github/ship_merge.py root#5 | tail -1 && echo x",
            "set -eu -o pipefail; python3 tools/github/ship_merge.py root#5 | tail -1 && echo x",
            "set -o errexit -o pipefail; python3 tools/github/ship_merge.py root#5 | tail -1 && echo x",
            "set -euxo pipefail; python3 tools/github/ship_merge.py root#5 | tail -1 && echo x",
            # the App wrapper around a push, a PR open or a read-only gh call is not a ship step (review S274)
            "tools/github/as-app.sh --repos AA-Ecosys -- git -C . push origin HEAD 2>&1 | tail -3 && "
            "tools/github/as-app.sh --repos AA-Ecosys -- gh pr create --fill",
            "tools/github/as-app.sh --repos AA-CIS-App -- gh pr view 5 --json state | head -3 && echo x",
            "tools/github/as-app.sh --repos AA-CIS-App -- gh pr checks 5 | tail -3 && echo x",
            "tools/github/as-app.sh --repos AA-CIS-App -- gh api repos/o/r/pulls/5 | head -3 && echo x",
            # no && after the pipeline: nothing depends on its exit code
            "python3 tools/github/ship_merge.py root#5 2>&1 | tail -1; echo done",
            "python3 tools/github/ship_merge.py root#5 2>&1 | tail -1",
            "echo start && python3 tools/github/ship_merge.py root#5 2>&1 | tail -1",
            # no pipe: && sees the ship step's own code
            "python3 tools/github/ship_merge.py root#5 > .tmp-session/S999/m.log 2>&1 && tail -3 "
            ".tmp-session/S999/m.log",
            # the piped command is not a ship step
            "gh pr checks 5 | tail -3 && echo ok",
            "git log --oneline | head -5 && git status",
            # grep keeps its own exit code (and -q is the point)
            "python3 tools/github/ship_merge.py --check-only root#5 2>&1 | grep -q green && echo ok",
            # quoted text is not code
            "grep -n 'ship_merge.py root#5 | tail -1 && x' skill/aa-ship/SKILL.md && echo found",
        ):
            self.assertIsNone(rule(cmd), cmd)


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

    def test_scripts_that_only_mention_the_command_pass(self):
        # S272 review: a helper that prints the fallback was refused as a raw ECS exec
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            s = root / ".tmp-session" / "S272-x"
            s.mkdir(parents=True)
            (s / "helper.py").write_text(
                'print("If ecsx fails, the fallback is: aws ecs execute-command --cluster c --task t")\n')
            (s / "helper.sh").write_text('#!/bin/bash\necho "fallback: aws ecs execute-command --cluster c"\n')
            (s / "shell.py").write_text(
                "import subprocess\nsubprocess.run(f\"aws ecs execute-command --task {t}\", shell=True)\n")
            (s / "later.py").write_text(
                "import subprocess\ncmd = f\"aws ecs execute-command --task {t}\"\nsubprocess.run(cmd, shell=True)\n")
            (s / "argv.py").write_text("import subprocess\nsubprocess.run([\n    'aws', 'ecs', 'execute-command',\n"
                                       "    '--task', t])\n")
            (s / "split.py").write_text("import shlex, subprocess\ncmd = f\"timeout 900 aws ecs execute-command "
                                        "--task {t}\"\nsubprocess.run(shlex.split(cmd))\n")
            # S272 review (ECS-1 string literal): a message kept in a variable, or a runner on an echo, is no call
            (s / "msg.py").write_text("HELP = \"If ecsx fails: aws ecs execute-command --cluster c\"\nprint(HELP)\n"
                                      "msg = f\"run aws ecs execute-command --task {t} by hand\"\nlog.info(msg)\n")
            (s / "echo.py").write_text("import subprocess\nsubprocess.run(\"echo aws ecs execute-command\", "
                                       "shell=True)\n")
            old = g.ROOT
            g.ROOT = root
            try:
                self.assertIsNone(rule("python3 .tmp-session/S272-x/helper.py", cwd=root))
                self.assertIsNone(rule("bash .tmp-session/S272-x/helper.sh", cwd=root))
                self.assertIsNone(rule("python3 .tmp-session/S272-x/msg.py", cwd=root))
                self.assertIsNone(rule("python3 .tmp-session/S272-x/echo.py", cwd=root))
                for name in ("shell.py", "later.py", "argv.py", "split.py"):
                    self.assertEqual(rule(f"python3 .tmp-session/S272-x/{name}", cwd=root), "ECS-1", name)
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
            # S272 review: the S247 child-repo shape through ~, a variable, a quoted path and pushd
            "cd ~/projects/AA-Ecosys/apps/AA-CIS-App && git worktree add .tmp-session/wt/s272-l9-x -b fix/x origin/main",
            "cd \"$CIS\" && git worktree add .tmp-session/wt/s272-l9-x -b fix/x origin/main",
            "cd $CIS && git worktree add .tmp-session/wt/s272-l9-x -b fix/x origin/main",
            "pushd apps/AA-CIS-App && git worktree add .tmp-session/wt/s272-l9-x -b fix/x origin/main",
            "cd \"$CIS\" && cd sub && git worktree add .tmp-session/wt/s272-l9-x origin/main",
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
            # absolute lane paths pass from any directory, readable or not
            f"cd \"$CIS\" && git worktree add {base}/s272-l9-x -b fix/x origin/main",
            f"pushd apps/AA-CIS-App && git worktree add {base}/s272-l9-x -b fix/x origin/main && popd",
            f"cd ~ && git -C {WS}/apps/AA-CIS-App worktree add {base}/s272-l9-y origin/main",
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
            "cd apps/AA-CIS-App/frontend && npx next dev -p 3005 >/dev/null 2>&1 &",
            "for u in a b; do curl -s https://x/$u >/dev/null 2>&1 & done; wait; uvicorn app >/dev/null 2>&1 &",
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
            # S272 review: a parallel warm-up the same command collects with a bare wait
            "for u in a b c; do curl -s https://api-cis.lumiguides.it.com/$u >/dev/null 2>&1 & done; wait",
            "curl -s https://x/a >/dev/null 2>&1 & curl -s https://x/b >/dev/null 2>&1 &\nwait",
        ):
            self.assertIsNone(rule(cmd), cmd)


class TerraformTest(unittest.TestCase):
    """TF-1 (G2): terraform apply only from main, never from a lane worktree."""

    def test_refused_in_a_lane_worktree(self):
        wt = f"{g.ROOT}/.tmp-session/wt/s999-lane-infra"
        for cmd in (f"terraform -chdir={wt}/accounts/aa365 apply plan.tfplan",
                    f"cd {wt}/accounts/aa365 && terraform apply -auto-approve",
                    f"terraform -chdir={wt} destroy",
                    # S272 review: env -u took AWS_PROFILE as the program
                    f"env -u AWS_PROFILE terraform -chdir={wt}/accounts/aa365 apply tfplan",
                    f"env --unset AWS_PROFILE -C /tmp terraform -chdir={wt} apply tfplan",
                    f"nice -n 10 terraform -chdir={wt} apply tfplan"):
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
                 # S272 review: without `--` the words after the helper are still the command
                 "tools/github/as-app.sh git push origin HEAD",
                 "tools/github/as-app.sh --repos AA-CIS-App git push origin HEAD",
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


class LanePytestTest(unittest.TestCase):
    """RAM-1, deterministic part (S276): in a lane worktree, pytest with more than 2 xdist workers or over a whole
    test directory is refused whatever the free memory (the S276 lane ran `pytest -n 8 tests/unit` with RAM fine at
    the start)."""

    WT = "/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/s999-l1-x-cis"
    MAIN = Path("/home/nghiep/projects/AA-Ecosys")

    def lane_rule(self, cmd: str, cwd: Path | None = None) -> str | None:
        return rule(cmd, cwd=cwd or self.MAIN)

    def test_refused_in_a_lane_worktree(self):
        wt = self.WT
        for cmd in (
            f"cd {wt} && pytest -n 8 tests/unit",  # the S276 command
            f"cd {wt} && pytest -n 8 tests/unit/test_a.py",
            f"cd {wt} && pytest -n3 -x tests/unit/test_a.py",
            f"cd {wt} && pytest -n=4 tests/unit/test_a.py",
            f"cd {wt} && pytest --numprocesses 4 tests/unit/test_a.py",
            f"cd {wt} && pytest --numprocesses=auto tests/unit/test_a.py",
            f"cd {wt} && pytest -n auto tests/unit/test_a.py",
            f"cd {wt} && pytest -n logical tests/unit/test_a.py",
            f"cd {wt} && pytest tests/unit",
            f"cd {wt} && pytest -x -q tests/unit/",
            f"cd {wt} && pytest tests",
            f"cd {wt} && pytest tests/integration -q",
            f"cd {wt} && pytest .",
            f"cd {wt} && pytest -q",  # no path: the whole testpaths
            f"cd {wt} && pytest -k gateway",  # -k takes a value, not a path
            f"cd {wt} && pytest --deselect tests/unit/test_a.py::t tests/unit",
            f"cd {wt}/backend && python -m pytest -q tests",
            f"cd {wt} && pytest backend/tests",
            f"pytest {wt}/tests/unit -q",  # an absolute path into a lane
            f"pytest {wt}",
            f"pytest --rootdir {wt} -n 8 {wt}/tests/unit/test_a.py",
            f"pytest --rootdir={wt}",
            f"env -C {wt} pytest tests/unit",
            f"cd {wt} && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_EC2_METADATA_DISABLED=true "
            f".venv/bin/python -m pytest -n 8 tests/unit/test_a.py",
            f"cd {wt} && python3 -X dev -m pytest tests/unit",
            f"cd {wt} && uv run pytest tests/unit",
            f"cd {wt} && uv run --with pytest-xdist pytest -n 4 tests/unit/test_a.py",
            f"cd {wt} && coverage run -m pytest tests/unit",
            f"bash -c 'cd {wt} && pytest -n 8 tests/unit'",
            f"pushd {wt} && pytest tests",
        ):
            self.assertEqual(self.lane_rule(cmd), "RAM-1", cmd)
        self.assertEqual(self.lane_rule("pytest -n 8 tests/unit/test_a.py", cwd=Path(wt)), "RAM-1")
        self.assertEqual(self.lane_rule("pytest tests/unit", cwd=Path(wt)), "RAM-1")

    def test_message_names_the_rule_and_keeps_the_fix(self):
        r = g.check(f"cd {self.WT} && pytest -n 8 tests/unit", cwd=self.MAIN, proc=NO_PROC)
        self.assertEqual(r.rule, "RAM-1")
        self.assertIn("-n 8", r.detail)
        self.assertIn("at most 2", r.detail)
        self.assertEqual(r.fix, g.FIX["RAM-1"])
        r = g.check(f"cd {self.WT} && pytest tests/unit", cwd=self.MAIN, proc=NO_PROC)
        self.assertIn("whole test directory", r.detail)

    def test_near_misses_pass(self):
        wt = self.WT
        for cmd in (
            f"cd {wt} && pytest -x -q tests/unit/test_a.py",
            f"cd {wt} && pytest -n 2 tests/unit/test_a.py tests/unit/test_b.py",
            f"cd {wt} && pytest -n2 tests/unit/test_a.py",
            f"cd {wt} && pytest -n 0 tests/unit/test_a.py",
            f"cd {wt} && pytest tests/unit/test_a.py::test_one",
            f"cd {wt} && pytest -k gateway tests/unit/test_a.py",
            f"cd {wt} && pytest tests/unit/llm_gateway",  # a sub-package, not the whole suite
            f"cd {wt} && pytest tests/integration/test_x.py -m integration",
            f"pytest {wt}/tests/unit/test_a.py",
            f"cd {wt} && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null .venv/bin/python -m pytest -x -q "
            f"tests/unit/test_a.py",
            f"cd {wt} && scripts/pre-push.sh --plan",
            f"cd {wt} && grep -n 'pytest -n 8 tests/unit' README.md",
            f"cd {wt} && python3 .claude/hooks/test_aa_shell_guard.py",
            f"cd {wt} && python3 -m unittest discover -s tools",
            # paths known only at run time (replay S272: both were file lists)
            f"cd {wt} && python -m pytest -q $(ls tests/unit/test_aa795*.py) 2>&1 | tail -3",
            f"cd {wt}/backend && python3 -m pytest -q $(git diff --name-only | sed 's#^backend/##' | grep test) -p x",
            f"cd {wt} && pytest -q $FILES",
            f'cd {wt} && pytest -q "tests/unit/test_a.py"',
            f"cd {wt} && pytest -q `git diff --name-only | grep test_`",
            # outside a lane worktree the deterministic part does not apply (RAM-1 still checks free memory)
            "pytest -n 8 tests/unit",
            "cd /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App && pytest tests/unit",
            # the override, logged
            f"AA_RAM_OVERRIDE=1 pytest -n 8 {wt}/tests/unit",
            f"AA_RAM_OVERRIDE=1 bash -c 'cd {wt} && pytest tests/unit'",
        ):
            self.assertIsNone(self.lane_rule(cmd), cmd)

    def test_pytest_argument_readers(self):
        self.assertEqual(g._pytest_args("uv run --directory x pytest -q a.py".split()), ["-q", "a.py"])
        self.assertEqual(g._pytest_args("python3 -I -m pytest a.py".split()), ["a.py"])
        self.assertIsNone(g._pytest_args("python3 -m unittest a".split()))
        self.assertIsNone(g._pytest_args("uv run ruff check".split()))
        self.assertEqual(g._pytest_targets(["-k", "x", "-p", "no:cacheprovider", "tests/a.py", "-q"]),
                         ["tests/a.py"])
        self.assertEqual(g._xdist_workers(["-q", "-n", "8"]), "8")
        self.assertEqual(g._xdist_workers(["-n4"]), "4")
        self.assertEqual(g._xdist_workers(["--numprocesses=auto"]), "auto")
        self.assertIsNone(g._xdist_workers(["-q", "--no-header"]))
        self.assertEqual(g._in_worktree(f"{self.WT}/tests/unit/"), "tests/unit")
        self.assertEqual(g._in_worktree(self.WT), "")


class UatTakesTest(unittest.TestCase):
    """UAT-1 (lesson S280/S281): a worktree with a PASS UAT take never packaged + rclone-checked is not removed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="uat1-")
        self.base = Path(self.tmp.name)
        self.wt = self.base / "wt" / "s999-l2-lanterns"
        out = self.wt / "tools" / "uat" / "out"
        (out / "packages").mkdir(parents=True)
        (out / "LANTERN-01_20261101_v1.mp4").write_bytes(b"x")
        (out / "LANTERN-01_20261101_v1.result.json").write_text(json.dumps({"verdict": "PASS"}), encoding="utf-8")
        (out / "LANTERN-02_20261101_v1.mp4").write_bytes(b"x")
        (out / "LANTERN-02_20261101_v1.result.json").write_text(json.dumps({"verdict": "FAIL"}), encoding="utf-8")
        self.out = out
        self.clean = self.base / "wt" / "s999-l3-clean"
        (self.clean / "tools" / "uat" / "out").mkdir(parents=True)
        self.log = mock_hits(self)

    def tearDown(self):
        self.tmp.cleanup()

    def test_refused(self):
        wt, base = str(self.wt), self.base
        for cmd, cwd in (
            (f"git worktree remove {wt}", None),
            (f"git worktree remove --force {wt}", None),
            (f"git -C {base} worktree remove -f wt/s999-l2-lanterns", None),
            ("git worktree remove wt/s999-l2-lanterns", base),
            (f"cd {base}/wt && git worktree remove s999-l2-lanterns", None),
            (f"rm -rf {wt}", None),
            (f"rm -r --one-file-system {wt} {self.clean}", None),
            (f"bash -c 'git worktree remove {wt}'", None),
        ):
            self.assertEqual(rule(cmd, cwd=cwd), "UAT-1", cmd)
        r = g.check(f"git worktree remove {wt}", proc=NO_PROC)
        self.assertIn("LANTERN-01_20261101_v1", r.message())
        self.assertNotIn("LANTERN-02", r.message())  # a FAIL take is re-recorded, not kept
        self.assertIn("check_takes_uploaded.py upload", r.message())

    def test_near_misses_pass(self):
        wt = str(self.wt)
        for cmd in (
            f"git worktree remove {self.clean}",
            f"rm -f {wt}/tools/uat/out/LANTERN-01_20261101_v1.mp4",  # not recursive
            f"rm -rf {wt}/tools/uat/out/packages",  # no tools/uat/out under it
            "git worktree remove \"$WT\"",
            "git worktree remove $WT",
            f"ls {wt}",
            f"grep -n 'git worktree remove {wt}' notes.md",
            "git worktree list --porcelain",
            f"AA_UAT_DISCARD_TAKES=1 git worktree remove {wt}",
        ):
            self.assertIsNone(rule(cmd), cmd)

    def test_packaged_and_checked_take_passes(self):
        sys.path.insert(0, str(g.TAKES_TOOL.parent))
        import check_takes_uploaded as ctu
        (self.out / "packages" / "LANTERN-01_20261101_v1.zip").write_bytes(b"zip")
        self.assertEqual(rule(f"git worktree remove {self.wt}"), "UAT-1")  # zipped, never checked
        err = ctu.verify(self.wt / "tools" / "uat", "LANTERN-01_20261101_v1", "drive:L", lambda argv: (0, "ok"))
        self.assertIsNone(err)
        self.assertIsNone(rule(f"git worktree remove {self.wt}"))

    def test_broken_tool_fails_open(self):
        with unittest.mock.patch.object(g, "TAKES_TOOL", self.base / "missing.py"):
            self.assertIsNone(rule(f"git worktree remove {self.wt}"))


def mock_hits(case: unittest.TestCase):
    """Keep guard-hits.log writes (refusals and overrides) inside the test's temporary directory."""
    p = unittest.mock.patch.object(g, "HITS_LOG", Path(case.tmp.name) / "guard-hits.log")
    p.start()
    case.addCleanup(p.stop)
    return p


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
