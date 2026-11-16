#!/usr/bin/env python3
"""PreToolUse guard for Bash (AA-1024, S271): the shell and ship mistakes that kept repeating become refusals.

The tech lead (S271): writing a lesson line does not stop the mistake; a machine check does. Each rule below cites the
lesson family it replaces (skill/aa-lessons/guards.md) and its message gives the correct form. A lesson line names its
guard as `Guard: hook aa_shell_guard:<RULE-ID>` (skill/aa-lessons/SKILL.md).

Rules (main session and subagents alike; exit 2 refuses, the message goes to stderr):

  PKILL-1  `pkill -f <pattern>`, and `pgrep -f` that feeds kill/xargs or drives an until/while wait loop. The pattern
           also matches the shell that runs the command (its own command line holds the pattern), so the command kills
           itself or the loop never ends (S262 hang, 13 repeats). Also inside `bash -c` and bash heredocs (both are on
           the calling shell's command line; a script file run by path is not). Use TaskStop, `kill <pid>` from a
           PID file, `wait <pid>`.
  ZSH-1    In the Bash tool's top-level shell (zsh here), `for x in $VAR` and `set -- $VAR` do not split $VAR into
           words: the loop runs once with the whole string (S261 silent non-run APPLY loop, S269 wait loop that never
           waited; 14 repeats). Only at the zsh level: the same text inside `bash -c '...'`, a bash heredoc or a script
           run by bash is fine. A zsh array (`VAR=(a b)` in the same command) is fine. Use `for x in ${=VAR}`, a
           `bash -c '...'` wrapper, or a real array.
  ENV-1    `export $(...)`: when the inner command fails or prints nothing, `export` prints the whole environment,
           tokens included (S244). Use the env-no-export pattern (`env -u AWS_PROFILE $(tr ...) <cmd>`, steering
           session-workflow.md).
  SHIP-1   Merges that skip the ship gate or run one PR after the other (S257, S263, S271: 48 hand-written ship
           scripts; a serial wave took ~4 h instead of ~1 h):
           (a) a raw `gh pr merge` (also through `as-app.sh -- gh pr merge`, xargs, bash -c), except `--disable-auto`,
               and the same merge through the API: `gh api` with a writing method on `pulls/<n>/merge`, or
               `gh api graphql` with a mergePullRequest / enqueuePullRequest mutation (dequeuePullRequest stays open);
           (b) the merge-queue wrapper run by hand without --dequeue (it waits for REQUIRED checks only: S263 #1225);
           (c) ship_merge.py inside a shell loop body (between `do` and its `done`) or more than once in one command
               (one call takes every target and runs the queue repos in parallel); a loop before or after the one
               merge call (a checks wait, a deploy check) passes;
           (d) running or sourcing a hand-written .tmp-session / scratchpad script that merges (mergeq / gh pr merge /
               ship_merge / ship_train inside).
           ship_wave.py (parallel by default, chains only for migration -> copy -> apply -> code) and ship_merge.py
           with all targets are the way; neither is refused.
  RAM-1    A heavy command (next build, npm ci, playwright, vitest/jest, tsc, docker build, a pytest run of a whole
           directory or with -n, a UAT node .cjs scenario; a push, the PR opener or ship_wave too, since a push runs
           the repo's pre-push hook: CIS fast mode is about 5,000 unit tests, the S272 crash) while MemAvailable
           < 2 GiB, or < 4 GiB with 3 or more heavy processes already running: the WSL VM ran out of memory and
           killed Claude Code and every lane (S237, S248, S251, S252, S261, S272). The message names what is running.
           In a lane worktree (.tmp-session/wt/**: the current directory after `cd`, `env -C`, `--rootdir` or a test
           path there) a pytest run is refused whatever the free memory when it asks for more than 2 xdist workers
           (`-n N` / `-nN` / `--numprocesses N` with N > 2, or `-n auto|logical`) or collects a whole test
           directory (no test path at all, or `.`, `tests`, `tests/unit`, `tests/integration`, `backend/tests`, ...):
           S276 a lane ran `pytest -n 8 tests/unit` while memory was still fine at the start and the VM swapped.
           A lane runs the touched test files, `-n` 2 at most. Override (logged): prefix `AA_RAM_OVERRIDE=1`.
  ECS-1    A raw `aws ecs execute-command`, typed or inside a .tmp-session / scratchpad script the command runs (S237 ...
           S269, 10 repeats): the SSM terminal cuts long output silently and a dropped session can kill the script.
           tools/ecs/ecsx.sh runs the script detached and brings ALL its output back (and resumes a lost start).
           Read-only mentions (grep, cat) pass. Override, logged (the tech lead only): prefix `AA_ECSX_BYPASS=1`.
  WT-1     `git worktree add` with a literal relative path, or an absolute one outside .tmp-session/wt/: the path is
           resolved from `-C <repo>` or the current directory, and worktrees landed inside child repos (S246, S247).
           A variable path ($W) passes (it cannot be read statically).
  UAT-1    `git worktree remove <path>` or `rm -r <path>` of a directory whose tools/uat/out/ still holds a PASS UAT take
           (out/<stem>.mp4 + result.json verdict PASS) with no zip in out/packages/ or no .uploaded marker of a clean
           `rclone check` (tools/uat/check_takes_uploaded.py): the take dies with the worktree (S280 REH-08a PASS lost,
           recorded again in S281). Override, logged: prefix `AA_UAT_DISCARD_TAKES=1`.
  BG-1     A background job whose stdout goes to /dev/null (`cmd >/dev/null 2>&1 &`, `&>/dev/null &`, `nohup ...
           >/dev/null`): when it fails nobody can tell why (S236, S270). Write a log file under .tmp-session/ or use
           the Bash tool's run_in_background. `&&` after a redirect is not a background job.
  TF-1     `terraform apply|destroy` from a lane worktree (.tmp-session/wt/**) or a checkout that is not on
           main/master: the state then holds code that is not on main, and the next apply from main reverts it.
  PIPE-1   A ship step (ship_*.py, dbmig.sh, the merge-queue wrapper, as-app.sh around `gh pr merge|ready`, `gh workflow
           run`, `gh run rerun` or a writing `gh api`) piped through `| tail`, `| head` or `| tee` and chained on with
           `&&`, without pipefail: the pipeline's exit code is the tail's (0), so the next
           step runs after a failed one (S272 copy_apply after a red merge; S273 tp-027 applied before its registry
           PR merged). Pipefail counts when set earlier in the same shell text (`set -o pipefail`, `set -euo
           pipefail`, zsh `setopt pipefail`) or on the `bash -o pipefail -c` that runs it. Better: one ship_wave.py
           call with a chain (`'cis#N>apply:cis/NNN'`), which stops at the first red step itself.

How it reads a command: a small shell lexer blanks quoted text and drops comments and heredoc bodies, so a rule never
fires on text that is only an argument (`grep 'pkill -f' x`); the bodies of `bash -c '...'` / `sh -c` and of
`bash <<EOF` heredocs are read again as bash. Static reading, so a heuristic: a command built at run time (eval, a
variable holding the program name) is not seen.

Split (AA-1103, new-project kit): the generic block (lexer, PKILL-1, ZSH-1, ENV-1, BG-1, WT-1's path check, TF-1,
RAM-1) lives in shell_guard_core.py, which the kit's template repo copies byte for byte and which must stay free of AA
names; this file is the AA block: SHIP-1, ECS-1, UAT-1, PIPE-1, the AA workspace path for WT-1, the AA fix texts and
the AA wrappers (as-app.sh) and push tools registered on the core. A generic rule change goes into the core (with a
test in test_shell_guard_core.py); an AA rule stays here.

Failure: unreadable input passes (exit 0); an error inside the hook passes with a warning on stderr (this hook saves an
agent from a mistake; root CI runs its tests, AA-1024 G5). Refusals are appended to .tmp-session/guard-hits.log.

Test: python3 .claude/hooks/test_aa_shell_guard.py. Replay over past transcripts (hit counts and false
positives): python3 .claude/hooks/replay_shell_guard.py.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import shell_guard_core as core
from shell_guard_core import (  # noqa: F401  (re-exported: the tests, lane_start_guard and replay use them from here)
    DIR_CHANGERS, KEYWORDS, MAX_SCRIPT_BYTES, UNKNOWN_DIR, Scan, Text, _cd, _in_worktree, _move, _pytest_args,
    _pytest_targets, _rule_background, _rule_env, _rule_pkill, _rule_zsh, _unknown, _xdist_workers,
    commands_with_loop_depth, heavy_command, lane_pytest_check, mem_available_mib, processes, program, scan,
    simple_commands, tf_check, texts_of, worktree_check,
)

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
HITS_LOG = ROOT / ".tmp-session" / "guard-hits.log"

# AA wrappers and push tools the generic rules must see through (RAM-1 heavy commands, program()).
core.DASHDASH_WRAPPERS["as-app.sh"] = ("--repos",)
core.PUSHERS.update({"ship_open_prs.py", "ship_wave.py"})


# --- AA rules ----------------------------------------------------------------------------------------------------

LESSONS = "skill/aa-lessons/guards.md"




MERGE_IN_SCRIPT = re.compile(
    r"mergeq\.sh|\bgh\s+pr\s+merge\b|[\"']gh[\"']\s*,\s*[\"']pr[\"']\s*,\s*[\"']merge[\"']|\bship_(?:merge|train)\b"
    r"|\b(?:merge|enqueue)PullRequest\b|\bpulls/[^\s/'\"]+/merge\b(?!/)")
# A merge through the API (S271 review: `as-app.sh -- gh api -X PUT repos/<org>/<repo>/pulls/<n>/merge`, 3 times in
# the transcripts). Read from the raw text: scan() blanks a quoted path or GraphQL query.
API_REST_MERGE = re.compile(r"\bpulls/[^\s/'\"]+/merge\b(?!/)")
API_GQL_MERGE = re.compile(r"\b(?:merge|enqueue)PullRequest\b")
API_FIELD_FLAGS = ("-f", "-F", "--field", "--raw-field", "--input")


def _api_method(args: list[str]) -> str:
    """The HTTP method of a `gh api` call: -X/--method, else POST when fields are given, else GET."""
    for i, a in enumerate(args):
        if a in ("-X", "--method") and i + 1 < len(args):
            return args[i + 1].upper()
        if a.startswith("--method="):
            return a.split("=", 1)[1].upper()
        if a.startswith("-X") and len(a) > 2:
            return a[2:].upper()
    if any(a in API_FIELD_FLAGS or a.startswith(("-f", "-F", "--field=", "--raw-field=", "--input=")) for a in args):
        return "POST"
    return "GET"


def _is_ship_merge(prog: str, args: list[str]) -> bool:
    if prog == "ship_merge.py":
        return True
    if re.fullmatch(r"python[0-9.]*", prog):
        return any(os.path.basename(a) == "ship_merge.py" for a in args[:3]) or (
            "-m" in args[:2] and "ship_merge" in args[:3])
    return False


def _aws_service_op(args: list[str]) -> tuple[str, str]:
    """(service, operation) of an aws CLI call, past its global options."""
    w = [a for a in args if a]
    i = 0
    while i < len(w) and w[i].startswith("-"):
        # --profile x / --region x take a value; --debug / --no-cli-pager do not (a value never starts with '-')
        i += 2 if "=" not in w[i] and i + 1 < len(w) and not w[i + 1].startswith("-") and w[i] not in (
            "--debug", "--no-cli-pager", "--no-paginate", "--no-verify-ssl", "--no-sign-request") else 1
    rest = w[i:]
    return (rest[0] if rest else "", rest[1] if len(rest) > 1 else "")


def _rule_ecs_exec(t: Text) -> str | None:
    for words in simple_commands(t.skeleton):
        prog, args = program(words)
        if prog == "aws" and _aws_service_op(args) == ("ecs", "execute-command"):
            return "a raw `aws ecs execute-command`"
    return None


# A Python script runs ECS exec through an argv list (["aws", ..., "ecs", "execute-command", ...]) or a command string
# handed to subprocess / os.system on the same line. A string that only mentions the command (a print, a help text) is
# not a call (S272 review: print("If ecsx fails, the fallback is: aws ecs execute-command ...") was refused).
PY_ECS_ARGV = re.compile(r"[\"']ecs[\"']\s*,\s*[\"']execute-command[\"']")
PY_RUNNER = r"(?:\bsubprocess\.\w+|\bos\.(?:system|popen)|\bPopen|\bcheck_output|\bcheck_call|\brun)\s*\(\s*"
# The command string must START with aws (a `timeout N` in front allowed): `run("echo aws ecs execute-command")` and a
# message that only mentions the command are not calls (S272 review, the ECS-1 string-literal minor).
PY_ECS_CMD = r"[rfbuRFBU]*[\"']\s*(?:timeout\s+\S+\s+)?aws\b[^\n]*\becs\s+execute-command\b"
PY_ECS_SHELL = re.compile(PY_RUNNER + PY_ECS_CMD)
# A command string assigned to a variable counts only when that variable is then handed to a runner
# (`cmd = f"aws ecs execute-command ..."` + `subprocess.run(cmd, shell=True)`), never a HELP / log message.
PY_ECS_ASSIGN = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*" + PY_ECS_CMD, re.MULTILINE)


def script_runs_ecs_exec(path: Path, code: str) -> bool:
    """ECS-1 inside a script: a shell script is read like a typed command (quoted text blanked, so an `echo "...aws ecs
    execute-command..."` is not a call); a Python script only through an argv list, a subprocess / os.system call on
    an aws command string, or such a string kept in a variable that a runner (or shlex.split) then gets."""
    if path.suffix == ".py":
        if PY_ECS_ARGV.search(code) or PY_ECS_SHELL.search(code):
            return True
        for m in PY_ECS_ASSIGN.finditer(code):
            name = re.escape(m.group(1))
            if re.search(PY_RUNNER + r"(?:shlex\.split\(\s*)?" + name + r"\b", code):
                return True
        return False
    return any(_rule_ecs_exec(t) for t in texts_of(code, "bash", str(path)))


WORKSPACE = "/home/nghiep/projects/AA-Ecosys"  # the canonical lane path the lane template prescribes


def _wt_bases() -> tuple[str, ...]:
    return tuple(dict.fromkeys(f"{r}/.tmp-session/wt/" for r in (str(ROOT), WORKSPACE)))



TAKES_TOOL = Path(__file__).resolve().parents[2] / "tools" / "uat" / "check_takes_uploaded.py"
RM_RECURSIVE = re.compile(r"^-(?:[a-zA-Z]*[rR][a-zA-Z]*)$|^--recursive$")


def _pending_takes(path: Path) -> list[str]:
    """PASS UAT takes under <path>/tools/uat/out without a checked upload (tools/uat/check_takes_uploaded.py); [] when
    the tool cannot be loaded (fail open, like every rule here)."""
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("check_takes_uploaded", TAKES_TOOL)
        if spec is None or spec.loader is None:
            return []
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return [t.stem for t in mod.pending_takes(mod.uat_dir(path))]
    except Exception:  # noqa: BLE001 - a broken tool must not block every worktree removal
        return []


def takes_check(t: Text, here: Path) -> str | None:
    """UAT-1: `git worktree remove <path>` or `rm -r <path>` of a directory whose tools/uat/out still holds a PASS take
    that was never packaged + rclone-checked (lesson S280/S281: REH-08a lost with its worktree). cd / -C tracked; a
    variable or quoted path is not readable here and passes."""
    for words in simple_commands(t.skeleton):
        prog, args = program(words)
        if prog in DIR_CHANGERS:
            here = _move(here, prog, args)
            continue
        targets: list[tuple[str, Path]] = []
        if prog == "git":
            a, base = list(args), here
            while a and a[0].startswith("-"):
                if a[0] == "-C" and len(a) > 1:
                    base = _cd(base, a[1:2])
                a = a[2:] if a[0] in ("-C", "-c") else a[1:]
            if a[:2] != ["worktree", "remove"]:
                continue
            paths = [x for x in a[2:] if not x.startswith("-")][:1]
            targets = [("git worktree remove", base) for _ in paths]
            what = paths
        elif prog == "rm" and any(RM_RECURSIVE.match(x) for x in args):
            what = [x for x in args if not x.startswith("-")]
            targets = [("rm -r", here) for _ in what]
        else:
            continue
        for path, (verb, base) in zip(what, targets):
            if path.startswith(("$", '"', "'", "`")) or "$" in path or "*" in path:
                continue
            if path.startswith("~"):
                path = os.path.expanduser(path)
            if not path.startswith("/") and _unknown(base):
                continue
            full = Path(os.path.normpath(path if path.startswith("/") else str(base / path)))
            if not (full / "tools" / "uat" / "out").is_dir():
                continue
            pending = _pending_takes(full)
            if pending:
                more = f" (+{len(pending) - 5} more)" if len(pending) > 5 else ""
                return (f"`{verb} {path}`: {len(pending)} PASS UAT take(s) in {full}/tools/uat/out not packaged + "
                        f"uploaded: {', '.join(pending[:5])}{more}")
    return None



def _rule_ship_command(t: Text) -> str | None:
    merges = 0
    looped = 0
    for words, depth in commands_with_loop_depth(t.skeleton):
        prog, args = program(words)
        if prog == "gh" and args[:2] == ["pr", "merge"] and "--disable-auto" not in args:
            return ("a raw `gh pr merge` (it skips the ship gate: every check green, settle re-read, deletions, DIRTY); "
                    "use `python3 tools/github/ship_merge.py <Repo>#<pr> ...` or `ship_wave.py`")
        if prog == "gh" and args[:1] == ["api"]:
            if "graphql" in args and API_GQL_MERGE.search(t.raw):
                return ("a merge through `gh api graphql` (mergePullRequest / enqueuePullRequest skips the ship gate); "
                        "use `python3 tools/github/ship_merge.py <Repo>#<pr> ...` or `ship_wave.py`")
            if API_REST_MERGE.search(t.raw) and _api_method(args[1:]) != "GET":
                return ("a merge through `gh api ... pulls/<n>/merge` (the REST merge skips the ship gate); "
                        "use `python3 tools/github/ship_merge.py <Repo>#<pr> ...` or `ship_wave.py`")
        if prog == "mergeq.sh" and "--dequeue" not in args:
            return ("the merge-queue wrapper run by hand (it waits for required checks only); use "
                    "`python3 tools/github/ship_merge.py <Repo>#<pr> ...` or `ship_wave.py` (--dequeue stays open)")
        if _is_ship_merge(prog, args):
            merges += 1
            looped += depth > 0
    if merges >= 2:
        return ("ship_merge.py called more than once in one command (serial shipping); give ONE call every target "
                "(queue repos run in parallel), or `ship_wave.py` for migration chains")
    if looped:  # only a merge between a loop's `do` and its `done` (or in a while/until condition)
        return ("ship_merge.py inside a shell loop (one PR after the other); give ONE call every target, or "
                "`ship_wave.py` for migration chains")
    return None


SHIP_STEPS = frozenset({"ship_merge.py", "ship_wave.py", "ship_train.py", "ship_copy_apply.py", "ship_open_prs.py",
                        "dbmig.sh", "mergeq.sh", "as-app.sh"})
EXIT_SWALLOWERS = frozenset({"tail", "head", "tee"})
# `set -o pipefail`, `set -euo pipefail`, `set -e -o pipefail`, `set -o errexit -o pipefail`, zsh `setopt pipefail` /
# `setopt PIPE_FAIL`. Any option groups may come before `-o pipefail` (review S274); `+o pipefail` turns it off.
_PIPEFAIL_ON = re.compile(
    r"(?:^|[\s;&|(])(?:set(?:\s+[-+][A-Za-z]+(?:\s+(?!pipefail\b)[a-z]+)?)*\s+-[A-Za-z]*o\s+pipefail\b"
    r"|setopt\s+(?:pipefail|pipe_fail)\b)",
    re.IGNORECASE)
# What the App wrapper runs that a later step depends on (review S274): a merge, a ready flip, a dispatch, a rerun, a
# writing API call. A push, `gh pr create` and the read-only gh calls (view/checks/list/api GET) are not ship steps.
_APP_SHIP_GH = frozenset({("pr", "merge"), ("pr", "ready"), ("workflow", "run"), ("run", "rerun")})
# Redirections that hold '&' or '|' but are not operators: 2>&1, >&2, &>log, &>>log, <&3, >|file.
_REDIRECT_OPS = re.compile(r"\d*>&\d*-?|&>>?|<&\d*-?|>\|")
_CHAIN_OPS = re.compile(r"(\|\||&&|\|&|\||;|\n|&)")


def _ship_step(words: list[str]) -> str | None:
    """The ship tool a simple command runs (as itself, through python, bash or as-app.sh), else None."""
    if not words:
        return None
    prog, args = program(words)
    if prog in SHIP_STEPS:
        return prog
    if re.fullmatch(r"python[0-9.]*", prog) and args and os.path.basename(args[0]) in SHIP_STEPS:
        return os.path.basename(args[0])
    # program() looks past as-app.sh to the command after `--`: the wrapper counts only around a gh call that changes
    # state a later step builds on (merge / ready / workflow run / rerun / a writing `gh api`)
    if prog == "gh" and any(os.path.basename(w) == "as-app.sh" for w in words[:4]):
        if tuple(args[:2]) in _APP_SHIP_GH:
            return "as-app.sh"
        if args[:1] == ["api"]:
            method = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-X", "--method")), None)
            method = method or next((a.split("=", 1)[1] for a in args if a.startswith(("-X=", "--method="))), None)
            if method and method.upper() != "GET":
                return "as-app.sh"
    return None


def _rule_pipe_exit(t: Text) -> str | None:
    """PIPE-1: `<ship step> | tail ... && <next step>` without pipefail."""
    if t.pipefail:
        return None
    sk = _REDIRECT_OPS.sub(" ", t.skeleton)
    sk = re.sub(r"\$\(|[(){}`]", " ", sk)  # a subshell / group / substitution returns its pipeline's status
    parts = _CHAIN_OPS.split(sk)
    pipeline: list[list[str]] = []
    pos = 0  # offset of parts[i] in sk
    pipe_start = 0  # offset where the current pipeline began
    for i in range(0, len(parts), 2):
        words = parts[i].split()
        while words and words[0] in KEYWORDS:
            words = words[1:]
        pipeline.append(words)
        op = parts[i + 1] if i + 1 < len(parts) else ""
        pos += len(parts[i]) + len(op)
        if op in ("|", "|&"):
            continue
        stages, pipeline, begin, pipe_start = pipeline, [], pipe_start, pos
        if op != "&&" or len(stages) < 2:
            continue
        step = next((s for s in (_ship_step(w) for w in stages[:-1]) if s), None)
        sink = next((program(w)[0] for w in stages[1:] if w and program(w)[0] in EXIT_SWALLOWERS), None)
        if not step or not sink or _PIPEFAIL_ON.search(sk[:begin]):
            continue
        return (f"`{step} ... | {sink} ... && <next step>` without pipefail (the pipeline exits with {sink}'s code, so "
                f"the next step runs even when {step} failed)")
    return None


_SCRIPT_PATH = re.compile(
    r"(?<![\w.-])((?:/[^\s'\"<>|;&()]*)?\.tmp-session/[^\s'\"<>|;&()]+\.(?:sh|bash|py)"
    r"|/tmp/claude-[^\s'\"<>|;&()]+\.(?:sh|bash|py))")
EXECUTORS = frozenset({"bash", "sh", "zsh", "dash", "source", ".", "python", "python3"})


def _scripts_run(t: Text, cwd: Path) -> list[Path]:
    """.tmp-session / scratchpad scripts this text runs or sources (not those it only reads)."""
    sk = t.skeleton
    paths = []
    for m in _SCRIPT_PATH.finditer(sk):
        p = m.group(1)
        if "/wt/" in p:  # worktree files are repository files (the ship tools themselves), not hand-written scripts
            continue
        paths.append(p)
    if not paths:
        return []
    sourced_subst = "<(" in sk and any(program(w)[0] in ("source", ".") for w in simple_commands(sk))
    run = []
    for words in simple_commands(sk):
        prog, args = program(words)
        full = words[0] if words else ""
        for p in paths:
            hit_prog = os.path.basename(p) == prog and any(w.endswith(p) for w in words)
            hit_arg = (prog in EXECUTORS or re.fullmatch(r"python[0-9.]*", prog or "")) and any(
                a.endswith(p) for a in args)
            if hit_prog or hit_arg or (sourced_subst and any(w.endswith(p) for w in words)) or full.endswith(p):
                run.append(p)
    out = []
    for p in dict.fromkeys(run):
        path = Path(p)
        if not path.is_absolute():
            path = (ROOT / p) if p.startswith(".tmp-session/") else (cwd / p)
        out.append(path)
    return out


def _read(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_SCRIPT_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))



# --- driver ------------------------------------------------------------------------------------------------------


def _log(rule: str, what: str) -> None:
    try:
        HITS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(HITS_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"rule": rule, "what": what[:300]}, ensure_ascii=False) + "\n")
    except OSError:
        pass


@dataclass
class Refusal:
    rule: str
    detail: str
    fix: str

    def message(self) -> str:
        return f"BLOCKED by aa_shell_guard {self.rule}: {self.detail}.\n{self.fix}\n(lessons: {LESSONS})"


FIX = {
    "PKILL-1": "The pattern also matches the shell running this command (its command line holds the pattern). Stop a "
               "background task with TaskStop, kill a PID you saved (`echo $! > pidfile`; `kill $(cat pidfile)`), "
               "wait with `wait <pid>` or a loop on `kill -0 <pid>`, or match the exact name with `pkill -x <name>`.",
    "ZSH-1": "The Bash tool runs zsh, which does not split an unquoted $VAR. Use `for x in ${=VAR}`, a real array "
             "(`A=(a b)`), or wrap the loop in `bash -c '...'` / a bash script.",
    "ENV-1": "When the inner command fails or prints nothing, `export` prints the whole environment (tokens "
             "included). Use: C=$(aws configure export-credentials --profile aa365-admin --format env-no-export "
             "</dev/null); grep -q '^AWS_ACCESS_KEY_ID=' <<<\"$C\" || exit 1; env -u AWS_PROFILE "
             "$(tr '\\n' ' ' <<<\"$C\") <command>  (inside bash -c).",
    "RAM-1": "Wait for a lane's heavy step to finish (or stop a stale one with TaskStop) and run it then; a lane runs "
             "targeted tests, not a whole suite. Override, logged: prefix the command with AA_RAM_OVERRIDE=1.",
    "SHIP-1": "Ship a wave with ONE call:python3 tools/github/ship_wave.py cis#1350 cis#1352 'cis#1349>apply:cis/383' "
              "'cis#1353@after=cis/383' --wait-deploy (independent PRs in parallel; only migration -> copy -> apply "
              "-> code is sequenced). One PR: python3 tools/github/ship_merge.py <Repo>#<pr>.",
    "ECS-1": "Run the script with tools/ecs/ecsx.sh <script.py> [VAR=value ...] (ECSX_SERVICE=<service> for "
             "Booking/CRM/worker): it runs detached, keeps ALL output (also in .tmp-session/ecsx/<run id>.out) and "
             "resumes a lost start. Override, logged, tech lead only: prefix AA_ECSX_BYPASS=1.",
    "WT-1": "Give the absolute lane path: git -C <repo> worktree add "
            "/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/<session>-<lane>-<slug> -b <branch> origin/main.",
    "BG-1": "Keep the output: `cmd > .tmp-session/<S>/<name>.log 2>&1 &` (or the Bash tool's run_in_background), "
            "then read the log when it ends. Jobs the same command collects with a final bare `wait` pass.",
    "PIPE-1": "Set pipefail first (`set -o pipefail; <step> 2>&1 | tail -20 && <next>`, or `bash -o pipefail -c "
              "'...'`), drop the `| tail`, or better ship the chain as ONE ship_wave.py call "
              "(`'cis#N>apply:cis/NNN'`), which stops at the first red step itself.",
    "TF-1": "Apply from the main checkout on main (git switch main && git pull), after the PR merged; Infra applies "
            "normally run in CI (terraform-apply.yml).",
    "UAT-1": "Package each take (python3 -I tools/uat/package.py uat <stem> \"<title>\" in that worktree), then "
             "python3 tools/uat/check_takes_uploaded.py upload --remote \"<rclone dir>\" --uat <worktree>/tools/uat "
             "<stem> (or verify after a hand upload: it writes the .uploaded marker on 0 differences); copy the zips "
             "out of the worktree too. Discard on purpose, logged: prefix AA_UAT_DISCARD_TAKES=1.",
}


RULES = (("PKILL-1", _rule_pkill), ("ZSH-1", _rule_zsh), ("ENV-1", _rule_env), ("SHIP-1", _rule_ship_command),
         ("ECS-1", _rule_ecs_exec), ("BG-1", _rule_background), ("PIPE-1", _rule_pipe_exit))
RULE_IDS = tuple(r for r, _ in RULES) + ("RAM-1", "WT-1", "TF-1", "UAT-1")


def _prefixed(cmd: str, var: str) -> bool:
    return bool(re.match(rf"\s*(?:\w+=\S*\s+)*{var}=1\b", cmd))


def check(cmd: str, cwd: Path | None = None, proc: Path = Path("/proc")) -> Refusal | None:
    cwd = cwd or ROOT
    texts = texts_of(cmd)
    override = _prefixed(cmd, "AA_RAM_OVERRIDE")
    ecs_bypass = _prefixed(cmd, "AA_ECSX_BYPASS")
    # Scripts the command runs are checked for merges (SHIP-1 d) and raw ECS exec (ECS-1). Not for PKILL-1: a
    # script's own command line is `bash <path>`, so a `pgrep -f <other script>` inside it does not match itself
    # (replay S271: 2 such waits).
    for t in list(texts):
        for path in _scripts_run(t, cwd):
            body = _read(path)
            if body is None:
                continue
            code = _strip_comments(body)
            if MERGE_IN_SCRIPT.search(code):
                return Refusal("SHIP-1", f"{path.name} is a hand-written ship script (it merges PRs itself: "
                               f"serial waits, gate skipped)", FIX["SHIP-1"])
            if script_runs_ecs_exec(path, code):
                if ecs_bypass:
                    _log("ECS-1 override", f"{path}: {cmd}")
                    continue
                return Refusal("ECS-1", f"{path.name} runs a raw `aws ecs execute-command`", FIX["ECS-1"])
    for t in texts:
        where = "" if t.origin == "command" else f" (in {Path(t.origin).name})"
        for rule, fn in RULES:
            hit = fn(t)
            if hit:
                if rule == "ECS-1" and ecs_bypass:
                    _log("ECS-1 override", cmd)
                    continue
                return Refusal(rule, hit + where, FIX[rule])
    # WT-1 / TF-1 resolve paths: walk the texts in order, carrying the directory `cd` moved to (the outer text
    # first, then the bash -c / heredoc bodies it runs).
    here = cwd
    lane_pytest = None
    for t in texts:
        where = "" if t.origin == "command" else f" (in {Path(t.origin).name})"
        hit = worktree_check(t, here, _wt_bases())
        if hit:
            return Refusal("WT-1", hit + where, FIX["WT-1"])
        hit = takes_check(t, here)
        if hit:
            if not _prefixed(cmd, "AA_UAT_DISCARD_TAKES"):
                return Refusal("UAT-1", hit + where, FIX["UAT-1"])
            _log("UAT-1 override", hit)
        if not lane_pytest:
            hit = lane_pytest_check(t, here)
            lane_pytest = hit + where if hit else None
        hit, here = tf_check(t, here)
        if hit:
            return Refusal("TF-1", hit + where, FIX["TF-1"])
    if lane_pytest:
        if not override:
            return Refusal("RAM-1", lane_pytest, FIX["RAM-1"])
        _log("RAM-1 override", lane_pytest)
    ram = core.ram_check(texts, override, proc, FIX["RAM-1"], _log)
    if ram:
        return Refusal("RAM-1", ram[0], ram[1])
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    if not cmd.strip():
        return 0
    try:
        refusal = check(cmd, Path(data.get("cwd") or ROOT))
    except Exception as e:  # noqa: BLE001 - never block on a hook bug; CI runs the tests
        print(f"aa_shell_guard: internal error {type(e).__name__}: {e} (command allowed)", file=sys.stderr)
        return 0
    if refusal:
        _log(refusal.rule, cmd)
        print(refusal.message(), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
