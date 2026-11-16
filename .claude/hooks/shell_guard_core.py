#!/usr/bin/env python3
"""Shell guard core: generic shell-mistake refusals for an agent's Bash tool (PreToolUse hook).

Part of the new-project kit. A project runs it as is (`python3 .claude/hooks/shell_guard_core.py`, reading the hook
JSON on stdin) or imports it and adds its own rules on top (an overlay). Keep this file free of project names: the
kit's template repo copies it byte for byte.

Rules (main session and subagents alike; exit 2 refuses, the message goes to stderr):

  PKILL-1  `pkill -f <pattern>`, and `pgrep -f` that feeds kill/xargs or drives an until/while wait loop. The pattern
           also matches the shell that runs the command (its own command line holds the pattern), so the command kills
           itself or the loop never ends. Also inside `bash -c` and bash heredocs. Use a saved PID, `wait <pid>`.
  ZSH-1    In a zsh top-level shell, `for x in $VAR` and `set -- $VAR` do not split $VAR into words: the loop runs once
           with the whole string. Only at the zsh level: the same text inside `bash -c '...'`, a bash heredoc or a
           script run by bash is fine. A zsh array (`VAR=(a b)` in the same command) is fine. Use `for x in ${=VAR}`.
  ENV-1    `export $(...)`: when the inner command fails or prints nothing, `export` prints the whole environment,
           tokens included. Pass the variables to one command with `env $(...) <command>` after checking the output.
  BG-1     A background job whose stdout goes to /dev/null (`cmd >/dev/null 2>&1 &`, `nohup ... >/dev/null`): when it
           fails nobody can tell why. Write a log file or use the tool's own background mode.
  WT-1     `git worktree add` with a path outside <project>/.tmp-session/wt/ (resolved from -C <repo> and `cd`):
           lane worktrees live in one ignored folder, never inside another checkout.
  TF-1     `terraform apply|destroy` from a lane worktree (.tmp-session/wt/**) or a checkout that is not on main/master:
           the state then holds code that is not on main, and the next apply from main reverts it.
  RAM-1    A heavy command (next build, npm ci, playwright, vitest/jest, tsc, docker build, a pytest run of a whole
           directory or with -n, a push that runs a pre-push hook) while MemAvailable is below MEM_FLOOR_MIB, or below
           MEM_BUSY_MIB with MAX_HEAVY heavy processes already running. In a lane worktree a pytest run is refused
           whatever the free memory when it asks for more than LANE_MAX_WORKERS xdist workers or collects a whole test
           directory. Override (logged): prefix `GUARD_RAM_OVERRIDE=1` (an overlay may name its own variable).

How it reads a command: a small shell lexer blanks quoted text and drops comments and heredoc bodies, so a rule never
fires on text that is only an argument (`grep 'pkill -f' x`); the bodies of `bash -c '...'` / `sh -c` and of
`bash <<EOF` heredocs are read again as bash. Static reading, so a heuristic: a command built at run time (eval, a
variable holding the program name) is not seen.

Failure: unreadable input passes (exit 0); an error inside the hook passes with a warning on stderr (the hook saves an
agent from a mistake; CI runs its tests). Refusals are appended to .tmp-session/guard-hits.log.

The numbers (memory floors, worker cap) are guard settings of the developer machine, not product thresholds.

Test: python3 .claude/hooks/test_shell_guard_core.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
HITS_LOG = ROOT / ".tmp-session" / "guard-hits.log"

MEM_FLOOR_MIB = 2048  # refuse a heavy command below this MemAvailable
MEM_BUSY_MIB = 4096  # ... or below this when MAX_HEAVY heavy processes already run
MAX_HEAVY = 3
MAX_SCRIPT_BYTES = 1_000_000

SHELLS = frozenset({"bash", "sh", "zsh", "dash"})
WRAPPERS = frozenset({"sudo", "nohup", "setsid", "command", "time", "exec", "nice", "env", "stdbuf", "builtin"})
WRAPPER_VALUE_OPTS = {"env": ("-u", "--unset", "-C", "--chdir", "-S", "--split-string"), "nice": ("-n", "--adjustment"),
                      "sudo": ("-u", "-g", "-U", "-C", "-D", "-h", "-p", "-r", "-t")}
SEPARATORS = re.compile(r"\|\||&&|[;&|\n]|\$\(|<\(|>\(|`|\(|\)|\{|\}")
KEYWORDS = frozenset({"do", "then", "else", "elif", "!", "if", "while", "until", "fi", "done", "esac"})


@dataclass
class Text:
    """One piece of shell code to check: the skeleton (quotes blanked, heredoc bodies and comments dropped)."""

    skeleton: str
    level: str  # "zsh" (the Bash tool's top-level shell) or "bash" (bash -c, bash heredoc, a script run by bash)
    origin: str = "command"
    raw: str = ""  # the code as written (quotes kept): scan() blanks a quoted API path or GraphQL query
    pipefail: bool = False  # the shell running this text was started with `-o pipefail` (bash -o pipefail -c '...')


@dataclass
class Scan:
    skeleton: str
    shell_bodies: list = field(default_factory=list)  # (body, level, started with -o pipefail)


# Overlay hooks: a project adds its own wrappers and push tools here (it imports this module, then extends them).
# DASHDASH_WRAPPERS: a program that runs the command after `--` -> the options before `--` that take a value.
DASHDASH_WRAPPERS: dict[str, tuple[str, ...]] = {}
# PUSHERS: scripts that push (each push runs the repo's pre-push hook), so RAM-1 treats them as heavy.
PUSHERS: set[str] = set()


def wt_bases() -> tuple[str, ...]:
    """Where lane worktrees may live: <ROOT>/.tmp-session/wt/."""
    return (f"{ROOT}/.tmp-session/wt/",)


# --- lexer -------------------------------------------------------------------------------------------------------

_SHELL_C = re.compile(r"(?:^|[\s;&|(`])(bash|sh|zsh|dash)(?:\s+-[A-Za-z]+(?:\s+[a-z]+)?)*?\s+-[A-Za-z]*c[A-Za-z]*\s*$")
_HEREDOC = re.compile(r"<<(-?)\s*(?:'([^']*)'|\"([^\"]*)\"|\\?([A-Za-z_][A-Za-z0-9_]*))")
_HEREDOC_SHELL = re.compile(
    r"^\s*(?:[A-Za-z_]\w*=\S*\s+)*(?:(?:timeout\s+\S+|nohup|env|time|exec)\s+)*(?:/\S*/)?(bash|sh|zsh|dash)"
    r"(?:\s+-[A-Za-z]+)*\s*(?:-s\b[^<]*)?$")


def scan(cmd: str) -> Scan:
    """Blank quoted text, drop comments and heredoc bodies; collect bash -c / bash heredoc bodies."""
    out: list[str] = []
    bodies: list[tuple[str, str]] = []
    pending: list[tuple[str, bool, str | None]] = []  # heredocs opened on this line: (delim, strip_tabs, level)
    i, n = 0, len(cmd)
    while i < n:
        c = cmd[i]
        if c == "\\" and i + 1 < n:
            out.append(cmd[i:i + 2])
            i += 2
            continue
        if c in "'\"" or (c == "$" and i + 1 < n and cmd[i + 1] == "'"):
            start = i + 2 if c == "$" else i + 1
            q = "'" if c == "$" else c
            j = start
            while j < n and cmd[j] != q:
                if cmd[j] == "\\" and (q == '"' or c == "$") and j + 1 < n:
                    j += 1
                j += 1
            lit = cmd[start:j]
            m = _SHELL_C.search("".join(out[-40:]) if out else "")
            if m:
                bodies.append((lit, "zsh" if m.group(1) == "zsh" else "bash", "pipefail" in m.group(0)))
            out.append(q + q)
            i = j + 1
            continue
        if c == "#" and (i == 0 or cmd[i - 1] in " \t\n;&|("):
            j = cmd.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "<" and cmd.startswith("<<", i) and not cmd.startswith("<<<", i):
            m = _HEREDOC.match(cmd, i)
            if m:
                delim = m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None
                                                                   else m.group(4))
                line_start = "".join(out).rfind("\n") + 1
                seg = re.split(r"\|\||&&|[;&|]", "".join(out)[line_start:])[-1]
                level = None
                sm = _HEREDOC_SHELL.match(seg)
                if sm:
                    level = "zsh" if sm.group(1) == "zsh" else "bash"
                pending.append((delim, m.group(1) == "-", level))
                out.append("<<" + delim)
                i = m.end()
                continue
        if c == "\n" and pending:
            out.append("\n")
            i += 1
            for delim, strip_tabs, level in pending:
                body: list[str] = []
                while i < n:
                    j = cmd.find("\n", i)
                    line = cmd[i:] if j < 0 else cmd[i:j]
                    i = n if j < 0 else j + 1
                    if (line.lstrip("\t") if strip_tabs else line) == delim:
                        break
                    body.append(line)
                if level:
                    bodies.append(("\n".join(body), level, False))
            pending = []
            continue
        out.append(c)
        i += 1
    return Scan("".join(out), bodies)


def texts_of(cmd: str, level: str = "zsh", origin: str = "command", depth: int = 0,
             pipefail: bool = False) -> list[Text]:
    s = scan(cmd)
    found = [Text(s.skeleton, level, origin, cmd, pipefail)]
    if depth < 4:
        for body, lvl, pf in s.shell_bodies:
            found.extend(texts_of(body, lvl, origin, depth + 1, pf))
    return found


def simple_commands(skeleton: str) -> list[list[str]]:
    """Split a skeleton into simple commands (word lists), keywords dropped."""
    cmds = []
    for part in SEPARATORS.split(skeleton):
        words = part.split()
        while words and words[0] in KEYWORDS:
            words = words[1:]
        if words:
            cmds.append(words)
    return cmds


LOOP_HEADS = frozenset({"for", "while", "until", "select"})


def commands_with_loop_depth(skeleton: str) -> list[tuple[list[str], int]]:
    """Simple commands (keywords dropped) with the number of shell loops whose body (or while/until condition) holds
    them. A command after a loop's `done` is back at depth 0 (`<step>; for s in a b; do
    <check>; done` is a step, then a check loop, not a step inside a loop)."""
    found: list[tuple[list[str], int]] = []
    depth = 0
    headers = 0  # loops whose `do` has not been read yet
    for part in SEPARATORS.split(skeleton):
        words = part.split()
        while words:
            head = words[0]
            if head in LOOP_HEADS:
                headers += 1
                if head in ("for", "select"):
                    words = []  # `for x in a b`: the word list is not a command
                    break
                words = words[1:]  # while / until: the condition runs on every turn
                continue
            if head == "do":
                if headers:
                    headers -= 1
                    depth += 1
                words = words[1:]
                continue
            if head == "done":
                depth = max(0, depth - 1)
                words = words[1:]
                continue
            if head in KEYWORDS:
                words = words[1:]
                continue
            break
        if words:
            found.append((words, depth + headers))
    return found


def program(words: list[str]) -> tuple[str, list[str]]:
    """The program a simple command runs (basename) and its arguments, past env assignments and wrappers."""
    w = list(words)
    while w:
        head = w[0]
        if re.fullmatch(r"[A-Za-z_]\w*=\S*", head):
            w = w[1:]
        elif head in WRAPPERS:
            w = w[1:]
            while w and w[0].startswith("-"):
                # options that take the next word as their value (`env -u NAME terraform ...` must not read NAME
                # as the program)
                w = w[2:] if w[0] in WRAPPER_VALUE_OPTS.get(head, ()) else w[1:]
        elif head == "timeout":
            w = w[1:]
            while w and (w[0].startswith("-") or re.fullmatch(r"\d+[smhd]?", w[0])):
                w = w[1:]
        elif head == "xargs":
            w = w[1:]
            while w and w[0].startswith("-"):
                flag = w[0]
                w = w[1:]
                if flag in ("-n", "-I", "-P", "-L", "-d", "-s", "-E") and w:
                    w = w[1:]
        elif os.path.basename(head) in DASHDASH_WRAPPERS:
            # a wrapper that runs the command after `--` (an overlay registers its own, with the options that take a
            # value); without `--`, the words after those options
            rest = w[1:]
            if "--" in rest:
                w = rest[rest.index("--") + 1:]
            else:
                while rest[:1] and rest[0] in DASHDASH_WRAPPERS[os.path.basename(head)]:
                    rest = rest[2:]
                w = rest
        elif os.path.basename(head) in SHELLS and len(w) > 1:
            # `bash script.sh args`: the script is the program. `bash -c '...'` bodies are read by texts_of().
            rest = w[1:]
            while rest and rest[0].startswith("-") and not re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", rest[0]):
                rest = rest[2:] if rest[0] in ("-o", "+o") else rest[1:]
            if not rest or rest[0].startswith("-"):
                break
            w = rest
        else:
            break
    if not w:
        return "", []
    return os.path.basename(w[0]), w[1:]



# --- rules -------------------------------------------------------------------------------------------------------


def _rule_pkill(t: Text) -> str | None:
    sk = t.skeleton
    for words in simple_commands(sk):
        prog, args = program(words)
        if prog == "pkill" and any(re.fullmatch(r"-[A-Za-z]*f[A-Za-z]*", a) for a in args):
            return "`pkill -f <pattern>`"
    if re.search(r"\b(?:until|while)\s+(?:!\s*)?pgrep\b[^\n;&|]*\s-[A-Za-z]*f", sk):
        return "an until/while loop on `pgrep -f`"
    if re.search(r"\bpgrep\b[^\n;&|]*\s-[A-Za-z]*f[^\n;&]*\|\s*(?:xargs\b|[^\n;&|]*\bkill\b)", sk):
        return "`pgrep -f` piped into kill/xargs"
    if re.search(r"\bpgrep\b[^\n;&|]*\s-[A-Za-z]*f[^\n;&]*\|\s*while\b[^\n]*\bkill\b", sk):
        return "`pgrep -f` piped into a kill loop"
    if re.search(r"\bkill\b[^\n;&|]*\$\(\s*pgrep\b[^)\n]*\s-[A-Za-z]*f", sk):
        return "`kill $(pgrep -f ...)`"
    if re.search(r"\bps\b[^\n;&]*\|\s*grep\b[^\n;&]*\|\s*(?:xargs\s+)?(?:-\S+\s+)*kill\b", sk):
        return "`ps | grep | kill`"
    return None


# zsh's own arrays: `for x in $argv` iterates them element by element.
ZSH_SPECIAL_ARRAYS = frozenset({"argv", "path", "fpath", "cdpath", "manpath", "pipestatus", "match", "mbegin", "mend",
                                "reply", "funcstack", "historywords", "signals", "commands"})


def _zsh_safe_vars(sk: str) -> set[str]:
    """Variables whose unquoted expansion is fine in zsh: arrays, and scalars only ever set to one bare word."""
    arrays = set(re.findall(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=\(", sk)) | set(
        re.findall(r"\b(?:typeset|declare|local)\s+-a\s+([A-Za-z_]\w*)", sk)) | set(
        re.findall(r"\bread\s+(?:-\w+\s+)*-A\s+([A-Za-z_]\w*)", sk))
    values: dict[str, list[str]] = {}
    for m in re.finditer(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=(\S*)", sk):
        values.setdefault(m.group(1), []).append(m.group(2))
    one_word = {v for v, vals in values.items()
                if vals and all(x and x[0] not in "$\"'`(" and "$" not in x for x in vals)}
    return arrays | one_word | ZSH_SPECIAL_ARRAYS


def _rule_zsh(t: Text) -> str | None:
    if t.level != "zsh":
        return None
    sk = t.skeleton
    safe = _zsh_safe_vars(sk)
    for m in re.finditer(r"(?:^|[\s;&|(])for\s+\w+\s+in\s+\$\{?([A-Za-z_]\w*)\}?(?=[\s;)]|$)", sk):
        if m.group(1) not in safe:
            return f"`for x in ${m.group(1)}` (zsh does not split ${m.group(1)}: the loop runs once)"
    for m in re.finditer(r"(?:^|[\s;&|(])set\s+--\s+\$\{?([A-Za-z_]\w*)\}?(?=[\s;)]|$)", sk):
        if m.group(1) not in safe:
            return f"`set -- ${m.group(1)}` (zsh does not split ${m.group(1)}: $1 gets the whole string)"
    return None


def _rule_env(t: Text) -> str | None:
    if re.search(r"(?:^|[\s;&|(])export\s+(?:\$\(|`)", t.skeleton):
        return "`export $(...)`"
    return None


UNKNOWN_DIR = Path("/unknown-dir")


def _unknown(p: Path) -> bool:
    return p == UNKNOWN_DIR or UNKNOWN_DIR in p.parents


def _cd(here: Path, args: list[str]) -> Path:
    """The directory after `cd` / `pushd <args>`. `~` is expanded; a variable, a quoted target (blanked by scan()),
    `-` or `+N` is UNKNOWN_DIR (`cd "$REPO" && git worktree add .tmp-session/wt/x` must not keep
    the old directory). `cd` alone is the home directory."""
    args = [a for a in args if a not in ("-L", "-P", "-e", "-q")]
    if not args:
        return Path.home()
    target = args[0]
    if target.startswith("~"):
        if target != "~" and not target.startswith("~/"):
            return UNKNOWN_DIR  # ~user
        target = os.path.expanduser(target)
    if target.startswith(("$", "-", '"', "'", "`", "+")) or "$" in target:
        return UNKNOWN_DIR
    if not target.startswith("/") and _unknown(here):
        return UNKNOWN_DIR
    return Path(os.path.normpath(target if target.startswith("/") else str(here / target)))


DIR_CHANGERS = frozenset({"cd", "pushd", "popd"})


def _move(here: Path, prog: str, args: list[str]) -> Path:
    """cd and pushd move like cd; popd goes back to a directory this reader does not keep: unknown."""
    return UNKNOWN_DIR if prog == "popd" else _cd(here, args)


WT_VALUE_OPTS = frozenset({"-b", "-B", "--orphan", "--reason"})


def worktree_check(t: Text, here: Path, bases: tuple[str, ...] | None = None) -> str | None:
    """WT-1: a `git worktree add` whose path, resolved from -C <repo> or the current directory (cd tracked), is not
    under one of `bases` (default: <ROOT>/.tmp-session/wt/)."""
    bases = bases or wt_bases()
    for words in simple_commands(t.skeleton):
        prog, args = program(words)
        if prog in DIR_CHANGERS:
            here = _move(here, prog, args)
            continue
        if prog != "git":
            continue
        a, base = list(args), here
        while a and a[0].startswith("-"):  # git -C <dir> / -c k=v before the subcommand
            if a[0] == "-C" and len(a) > 1:
                base = _cd(base, a[1:2])
            a = a[2:] if a[0] in ("-C", "-c") else a[1:]
        if a[:2] != ["worktree", "add"]:
            continue
        rest = a[2:]
        path = None
        while rest:
            if rest[0] in WT_VALUE_OPTS:
                rest = rest[2:]
            elif rest[0].startswith("-"):
                rest = rest[1:]
            else:
                path = rest[0]
                break
        if not path or path.startswith(("$", "~", '"', "'", "`")) or "$" in path:
            continue  # a variable or quoted path is not readable here
        if not path.startswith("/") and _unknown(base):
            return (f"`git worktree add {path}` (a relative path from a directory this guard cannot read: a variable, "
                    f"a quoted path or popd)")
        full = os.path.normpath(path if path.startswith("/") else str(base / path)) + "/"
        if not any(full.startswith(b) and "/" not in full[len(b):].rstrip("/") for b in bases):
            return f"`git worktree add {path}` (resolves to {full.rstrip('/')}, outside {bases[-1]})"
    return None



_BG_NULL = re.compile(
    r"(?:(?<![0-9&])1?>\s*/dev/null\s*2>\s*(?:&1|/dev/null)|&>\s*/dev/null|>&\s*/dev/null)\s*&(?![&>])")
_SEGMENT = re.compile(r"&&|\|\||;|\n|(?<![>&])&(?![>&])")


_BARE_WAIT_END = re.compile(r"(?:^|[;&|\n]|\bdone|\bthen|\bdo)\s*wait\s*;?\s*$")


def _rule_background(t: Text) -> str | None:
    sk = t.skeleton
    # fire-and-wait (`for u in a b; do curl -s $u >/dev/null 2>&1 & done; wait`): the same command collects every job
    # before it returns, so nothing runs on unseen
    if _BARE_WAIT_END.search(sk.rstrip()):
        return None
    for m in _BG_NULL.finditer(sk):
        start = max((x.end() for x in _SEGMENT.finditer(sk, 0, m.start())), default=0)
        if ")" in sk[start:m.start()] or "}" in sk[start:m.start()]:
            continue  # a subshell / group `( ... > log 2>&1 ) >/dev/null &` keeps its output inside
        return "a background job with its output sent to /dev/null"
    for seg in _SEGMENT.split(sk):
        words = seg.split()
        while words and (words[0] in KEYWORDS or re.fullmatch(r"[A-Za-z_]\w*=\S*", words[0])):
            words = words[1:]
        if words and words[0] in ("nohup", "setsid") and re.search(r"(?<![0-9&])1?>\s*/dev/null", seg):
            return f"`{words[0]} ... >/dev/null` (a detached job whose output is thrown away)"
    return None


def _branch(path: Path) -> str | None:
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(path), "symbolic-ref", "--short", "-q", "HEAD"], capture_output=True,
                           text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def tf_check(t: Text, here: Path) -> tuple[str | None, Path]:
    """TF-1: terraform apply/destroy from a lane worktree or a checkout off main (cd tracked). Returns (hit, the
    directory after this text)."""
    for words in simple_commands(t.skeleton):
        prog, args = program(words)
        if prog in DIR_CHANGERS:
            here = _move(here, prog, args)
            continue
        if prog != "terraform":
            continue
        chdir = next((a.split("=", 1)[1] for a in args if a.startswith("-chdir=")), None)
        sub = next((a for a in args if not a.startswith("-")), "")
        if sub not in ("apply", "destroy"):
            continue
        d = here
        if chdir and not chdir.startswith(("$", '"', "'")):
            d = Path(chdir) if chdir.startswith("/") else here / chdir
        where = os.path.normpath(str(d))
        if "/.tmp-session/wt/" in where + "/":
            return f"`terraform {sub}` from a lane worktree ({where})", here
        br = _branch(Path(where)) if Path(where).is_dir() else None
        if br and br not in ("main", "master"):
            return f"`terraform {sub}` from a checkout on branch {br}, not main", here
    return None, here


# --- RAM ---------------------------------------------------------------------------------------------------------


# --- pytest in a lane worktree (RAM-1, deterministic) ------------------------------------------------------------

LANE_MAX_WORKERS = 2  # the lane brief: `-n` 2 at most
# pytest / xdist / common plugin options that take the next word as their value (so `-k name` is not a test path)
PYTEST_VALUE_OPTS = frozenset({
    "-k", "-m", "-p", "-c", "-o", "-W", "-r", "-n", "--numprocesses", "--maxprocesses", "--dist", "--rootdir",
    "--confcutdir", "--basetemp", "--deselect", "--ignore", "--ignore-glob", "--junitxml", "--junit-xml",
    "--maxfail", "--durations", "--durations-min", "--tb", "--log-level", "--log-file", "--log-cli-level",
    "--log-format", "--cov", "--cov-report", "--cov-config", "--cov-fail-under", "--import-mode", "--override-ini",
    "--capture", "--color", "--code-highlight", "--pythonwarnings", "--cache-dir", "--timeout", "--reruns", "--seed",
    "--randomly-seed", "--count", "--tx", "--rsyncdir", "--inifile", "--config-file", "--deselect-file",
})
WHOLE_TEST_DIR = re.compile(r"(?:\./)?(?:(?:backend|src|app|api|web|portal)/)?tests?(?:/(?:unit|integration|e2e))?/?|\.?/?")
RUNNERS = frozenset({"uv", "poetry", "pipenv", "pdm", "hatch", "rye"})


def _pytest_args(words: list[str]) -> list[str] | None:
    """The arguments of a pytest run (`pytest`, `py.test`, `python -m pytest`, `.venv/bin/pytest`, `uv run pytest`,
    `coverage run -m pytest`), or None when the command is not one."""
    prog, a = program(words)
    while prog in RUNNERS and a[:1] == ["run"]:
        rest = a[1:]
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0] in ("--directory", "--project", "--with", "--python", "-p", "--env-file",
                                             "--group", "--extra") else rest[1:]
        if not rest:
            return None
        prog, a = os.path.basename(rest[0]), rest[1:]
    if prog == "coverage" and a[:1] == ["run"]:
        rest = a[1:]
        while rest and rest[0].startswith("-") and rest[0] != "-m":
            rest = rest[1:]
        return rest[2:] if rest[:2] == ["-m", "pytest"] else None
    if prog == "pytest" or prog.startswith("py.test"):
        return a
    if re.fullmatch(r"python[0-9.]*", prog):
        rest = list(a)
        while rest and rest[0].startswith("-") and rest[0] != "-m":
            rest = rest[2:] if rest[0] in ("-X", "-W") else rest[1:]
        if rest[:2] == ["-m", "pytest"]:
            return rest[2:]
    return None


def _pytest_targets(args: list[str]) -> list[str]:
    """Test paths given to pytest: words that are not an option or an option's value. A quoted word (blanked by
    scan() to '' / \"\"), a variable or a command substitution stays in the list as written: it is unreadable here."""
    out, skip = [], False
    for x in args:
        if skip:
            skip = False
            continue
        if x.startswith("-"):
            skip = x in PYTEST_VALUE_OPTS
            continue
        out.append(x)
    return out


def _unreadable(word: str) -> bool:
    """A word whose value is only known at run time: a blanked quote, a variable, a command substitution."""
    return word in ("''", '""') or "$" in word or "`" in word


def _is_test_file(target: str) -> bool:
    return target.endswith(".py") or "::" in target


def _xdist_workers(args: list[str]) -> str | None:
    """The xdist worker count asked for (`-n 4`, `-n4`, `-n=4`, `--numprocesses 4`, `--numprocesses=auto`), or None."""
    for i, x in enumerate(args):
        if x in ("-n", "--numprocesses"):
            return args[i + 1] if i + 1 < len(args) else ""
        if x.startswith("--numprocesses="):
            return x.split("=", 1)[1]
        if re.fullmatch(r"-n=?\w+", x):
            return x[2:].lstrip("=")
    return None


def _in_lane(path: str) -> bool:
    return "/.tmp-session/wt/" in os.path.normpath(path) + "/"


_SUBST = re.compile(r"\$\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\)|`[^`]*`")
_WT_ROOT = re.compile(r"^.*?/\.tmp-session/wt/[^/]+/?")


def _in_worktree(target: str) -> str:
    """A test path relative to its worktree root: an absolute path under .tmp-session/wt/<lane>/ loses that prefix
    (the worktree root itself is ''), a relative one stays as given."""
    if target.startswith("/"):
        norm = os.path.normpath(target)
        m = _WT_ROOT.match(norm + "/")
        return (norm + "/")[m.end():].rstrip("/") if m else norm
    return target


def _env_chdir(words: list[str], here: Path) -> Path:
    """The directory an `env -C <dir>` / `env --chdir=<dir>` in front of the command moves to."""
    for i, w in enumerate(words):
        if os.path.basename(w) != "env":
            continue
        j = i + 1
        while j < len(words) and (words[j].startswith("-") or re.fullmatch(r"[A-Za-z_]\w*=\S*", words[j])):
            if words[j] in ("-C", "--chdir") and j + 1 < len(words):
                here = _cd(here, [words[j + 1]])
                j += 2
                continue
            if words[j].startswith("--chdir="):
                here = _cd(here, [words[j].split("=", 1)[1]])
            j += 2 if words[j] in ("-u", "--unset", "-S", "--split-string") else 1
        break
    return here


def lane_pytest_check(t: Text, here: Path) -> str | None:
    """RAM-1 (deterministic): a pytest run in a lane worktree with more than LANE_MAX_WORKERS xdist workers, or
    over a whole test directory, whatever the free memory. The directory is tracked through cd / pushd / env -C."""
    # a command substitution becomes one unreadable word, so `pytest -q $(git diff --name-only ...)` keeps its paths
    sk = _SUBST.sub(" $SUBST ", t.skeleton)
    for words in simple_commands(sk):
        prog, args = program(words)
        if prog in DIR_CHANGERS:
            here = _move(here, prog, args)
            continue
        pa = _pytest_args(words)
        if pa is None:
            continue
        d = _env_chdir(words, here)
        targets = _pytest_targets(pa)
        rootdir = next((pa[i + 1] for i, x in enumerate(pa[:-1]) if x == "--rootdir"), None) or next(
            (x.split("=", 1)[1] for x in pa if x.startswith("--rootdir=")), None)
        places = [str(d)] + [x for x in targets + [rootdir or ""] if x.startswith("/")]
        if not any(_in_lane(p) for p in places):
            continue
        where = next(p for p in places if _in_lane(p))
        workers = _xdist_workers(pa)
        if workers is not None and not _unreadable(workers) and not (
                workers.isdigit() and int(workers) <= LANE_MAX_WORKERS):
            return (f"`pytest -n {workers or '?'}` in a lane worktree ({where}): a lane runs at most "
                    f"{LANE_MAX_WORKERS} xdist workers, whatever the free memory")
        files = [x for x in targets if _is_test_file(x)]
        whole = [x for x in targets if not _is_test_file(x) and WHOLE_TEST_DIR.fullmatch(_in_worktree(x))]
        if not files and not any(_unreadable(x) for x in targets) and (not targets or whole):
            what = f"`pytest {whole[0]}`" if whole else "`pytest` without a test path"
            return (f"{what} in a lane worktree ({where}) collects a whole test directory: a lane runs the touched "
                    f"test files only (a whole suite can need several GB)")
    return None


def heavy_command(words: list[str]) -> str | None:
    """Name of the heavy work a simple command starts, or None."""
    prog, args = program(words)
    a = args
    if prog in ("npx", "pnpm", "yarn", "bunx") and a:
        if a[0] in ("dlx", "exec") and len(a) > 1:
            a = a[1:]
        prog, a = os.path.basename(a[0]), a[1:]
    if prog == "next" and a[:1] == ["build"]:
        return "next build"
    if prog in ("npm", "pnpm", "yarn") and (a[:1] == ["ci"] or a[:2] == ["run", "build"] or a[:1] == ["build"]):
        return f"{prog} {' '.join(a[:2] if a[:1] == ['run'] else a[:1])}"
    if prog == "playwright" and a[:1] == ["test"]:
        return "playwright test"
    if prog in ("vitest", "jest"):
        return prog
    if prog == "tsc":
        return "tsc"
    if prog == "docker" and ("build" in a[:2] or a[:2] == ["compose", "build"]):
        return "docker build"
    pytest_args = _pytest_args(words)
    if pytest_args is not None:
        if _xdist_workers(pytest_args) is not None:
            return "pytest -n (xdist)"
        if not any(_is_test_file(x) for x in _pytest_targets(pytest_args)):
            return "pytest over a whole directory"
        return None
    if prog == "node" and any(re.search(r"(?:^|/)uat/\S*\.cjs$", x) for x in a):
        return "UAT node scenario (Chromium)"
    # A push runs the repo's pre-push hook (often the whole fast test suite in one process). --no-verify, --dry-run and
    # a pure delete skip the hook.
    if prog == "git":
        while a and a[0] in ("-C", "-c") and len(a) > 1:
            a = a[2:]
        if a[:1] == ["push"] and not {"--no-verify", "-n", "--dry-run", "--delete", "-d"} & set(a[1:]) \
                and not any(x.startswith(":") for x in a[1:]):
            return "git push (runs the repo's pre-push hook)"
    if prog == "pre-push.sh" and not {"--self-test", "--plan", "-h", "--help"} & set(a):
        return "scripts/pre-push.sh (the repo's CI-equivalent checks)"
    name = prog if prog in PUSHERS else (os.path.basename(a[0]) if re.fullmatch(r"python[0-9.]*", prog) and a else "")
    if name in PUSHERS and not {"--dry-run", "--check-only", "-h", "--help"} & set(a):
        return f"{name} (each push runs that repo's pre-push hook)"
    return None


HEAVY_PROC = (
    ("next build", re.compile(r"(?:^|[/\x00])next(?:\.js)?\x00build(?:\x00|$)")),
    ("playwright", re.compile(r"playwright(?:/cli\.js)?\x00test")),
    ("pytest", re.compile(r"(?:^|\x00|/)(?:-m\x00)?pytest(?:\x00|$)")),
    ("vitest", re.compile(r"(?:^|[/\x00])vitest")),
    ("jest", re.compile(r"(?:^|[/\x00])jest(?:\.js)?(?:\x00|$)")),
    ("tsc", re.compile(r"(?:^|[/\x00])tsc(?:\x00|$)")),
    ("docker build", re.compile(r"(?:^|[/\x00])docker\x00(?:buildx\x00)?build")),
    ("pre-push hook", re.compile(r"(?:^|[/\x00])pre-push(?:\.sh)?(?:\x00|$)")),
)


def mem_available_mib(proc: Path = Path("/proc")) -> int | None:
    try:
        for line in (proc / "meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def processes(proc: Path = Path("/proc")) -> list[tuple[int, int, str, str]]:
    """(pid, rss MiB, heavy label or '', short command line) per process; reads /proc directly (never pgrep -f)."""
    out = []
    try:
        entries = [e for e in os.listdir(proc) if e.isdigit()]
    except OSError:
        return out
    me = os.getpid()
    for e in entries:
        pid = int(e)
        if pid == me:
            continue
        try:
            raw = (proc / e / "cmdline").read_bytes().rstrip(b"\x00").decode("utf-8", "replace")
            rss = 0
            for line in (proc / e / "status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1]) // 1024
                    break
        except (OSError, ValueError, IndexError):
            continue
        if not raw:
            continue
        label = next((name for name, rx in HEAVY_PROC if rx.search(raw)), "")
        out.append((pid, rss, label, raw.replace("\x00", " ")[:90]))
    return out


def ram_check(texts: list[Text], override: bool, proc: Path = Path("/proc"), fix: str | None = None,
              log=None) -> tuple[str, str] | None:
    """(detail, fix) when a heavy command meets low memory, else None. An override is logged through `log`."""
    heavy = None
    for t in texts:
        for words in simple_commands(t.skeleton):
            heavy = heavy or heavy_command(words)
    if not heavy:
        return None
    avail = mem_available_mib(proc)
    if avail is None:
        return None
    procs = processes(proc)
    running = [p for p in procs if p[2]]
    if avail >= MEM_FLOOR_MIB and not (avail < MEM_BUSY_MIB and len(running) >= MAX_HEAVY):
        return None
    top = sorted(procs, key=lambda p: -p[1])[:5]
    lines = [f"MemAvailable {avail} MiB (floor {MEM_FLOOR_MIB}; {MEM_BUSY_MIB} with {MAX_HEAVY}+ heavy running). "
             f"Heavy processes running: {len(running)}."]
    lines += [f"  heavy pid {p[0]} {p[1]} MiB {p[2]}: {p[3]}" for p in running[:6]]
    lines += [f"  top pid {p[0]} {p[1]} MiB: {p[3]}" for p in top]
    detail = f"{heavy} with low memory. " + "\n".join(lines)
    if override:
        (log or _log)("RAM-1 override", lines[0])
        return None
    return detail, fix or FIX["RAM-1"]


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
    guard: str = "shell_guard_core"
    footer: str = ""

    def message(self) -> str:
        return f"BLOCKED by {self.guard} {self.rule}: {self.detail}.\n{self.fix}{self.footer}"


FIX = {
    "PKILL-1": "The pattern also matches the shell running this command (its command line holds the pattern). Stop a "
               "background task with the tool's own stop action, kill a PID you saved (`echo $! > pidfile`; "
               "`kill $(cat pidfile)`), wait with `wait <pid>` or a loop on `kill -0 <pid>`, or match the exact "
               "name with `pkill -x <name>`.",
    "ZSH-1": "zsh does not split an unquoted $VAR. Use `for x in ${=VAR}`, a real array (`A=(a b)`), or wrap the loop "
             "in `bash -c '...'` / a bash script.",
    "ENV-1": "When the inner command fails or prints nothing, `export` prints the whole environment (tokens "
             "included). Capture the output first, check it is not empty, then pass it to one command: "
             "C=$(<command>); [ -n \"$C\" ] || exit 1; env $(tr '\\n' ' ' <<<\"$C\") <command>  (inside bash -c).",
    "RAM-1": "Wait for the heavy step that is running to finish (or stop a stale one) and run it then; a lane runs "
             "targeted tests, not a whole suite. Override, logged: prefix the command with GUARD_RAM_OVERRIDE=1.",
    "WT-1": "Give an absolute lane path: git -C <repo> worktree add <project>/.tmp-session/wt/<session>-<lane> "
            "-b <branch> origin/main.",
    "BG-1": "Keep the output: `cmd > .tmp-session/<name>.log 2>&1 &` (or the tool's own background mode), then read "
            "the log when it ends. Jobs the same command collects with a final bare `wait` pass.",
    "TF-1": "Apply from the main checkout on main, after the PR merged (or from CI).",
}

RULES = (("PKILL-1", _rule_pkill), ("ZSH-1", _rule_zsh), ("ENV-1", _rule_env), ("BG-1", _rule_background))
RULE_IDS = tuple(r for r, _ in RULES) + ("RAM-1", "WT-1", "TF-1")


def prefixed(cmd: str, var: str) -> bool:
    """The command starts with `<var>=1` (after other assignments): an override switch."""
    return bool(re.match(rf"\s*(?:\w+=\S*\s+)*{var}=1\b", cmd))


def check(cmd: str, cwd: Path | None = None, proc: Path = Path("/proc")) -> Refusal | None:
    """The generic rules only. An overlay calls the pieces itself to add its rules in its own order."""
    cwd = cwd or ROOT
    texts = texts_of(cmd)
    override = prefixed(cmd, "GUARD_RAM_OVERRIDE")
    for t in texts:
        where = "" if t.origin == "command" else f" (in {Path(t.origin).name})"
        for rule, fn in RULES:
            hit = fn(t)
            if hit:
                return Refusal(rule, hit + where, FIX[rule])
    here = cwd
    lane_pytest = None
    for t in texts:
        where = "" if t.origin == "command" else f" (in {Path(t.origin).name})"
        hit = worktree_check(t, here)
        if hit:
            return Refusal("WT-1", hit + where, FIX["WT-1"])
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
    ram = ram_check(texts, override, proc)
    if ram:
        return Refusal("RAM-1", ram[0], ram[1])
    return None


def run_hook(checker, log=None) -> int:
    """Read the PreToolUse JSON on stdin and run `checker(cmd, cwd)`; exit code 2 refuses."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    if not cmd.strip():
        return 0
    try:
        refusal = checker(cmd, Path(data.get("cwd") or ROOT))
    except Exception as e:  # noqa: BLE001 - never block on a hook bug; CI runs the tests
        print(f"shell guard: internal error {type(e).__name__}: {e} (command allowed)", file=sys.stderr)
        return 0
    if refusal:
        (log or _log)(refusal.rule, cmd)
        print(refusal.message(), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(run_hook(check))
