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
           (c) ship_merge.py inside a shell loop or more than once in one command (one call takes every target and
               runs the queue repos in parallel);
           (d) running or sourcing a hand-written .tmp-session / scratchpad script that merges (mergeq / gh pr merge /
               ship_merge / ship_train inside).
           ship_wave.py (parallel by default, chains only for migration -> copy -> apply -> code) and ship_merge.py
           with all targets are the way; neither is refused.
  RAM-1    A heavy command (next build, npm ci, playwright, vitest/jest, tsc, docker build, a pytest run of a whole
           directory or with -n, a UAT node .cjs scenario) while MemAvailable < 2 GiB, or < 4 GiB with 3 or more heavy
           processes already running: the WSL VM ran out of memory and killed Claude Code and every lane (S237, S248,
           S251, S252, S261). The message names what is running. Override (logged): prefix `AA_RAM_OVERRIDE=1`.

How it reads a command: a small shell lexer blanks quoted text and drops comments and heredoc bodies, so a rule never
fires on text that is only an argument (`grep 'pkill -f' x`); the bodies of `bash -c '...'` / `sh -c` and of
`bash <<EOF` heredocs are read again as bash. Static reading, so a heuristic: a command built at run time (eval, a
variable holding the program name) is not seen.

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
SEPARATORS = re.compile(r"\|\||&&|[;&|\n]|\$\(|<\(|>\(|`|\(|\)|\{|\}")
KEYWORDS = frozenset({"do", "then", "else", "elif", "!", "if", "while", "until", "fi", "done", "esac"})


@dataclass
class Text:
    """One piece of shell code to check: the skeleton (quotes blanked, heredoc bodies and comments dropped)."""

    skeleton: str
    level: str  # "zsh" (the Bash tool's top-level shell) or "bash" (bash -c, bash heredoc, a script run by bash)
    origin: str = "command"
    raw: str = ""  # the code as written (quotes kept): scan() blanks a quoted API path or GraphQL query


@dataclass
class Scan:
    skeleton: str
    shell_bodies: list = field(default_factory=list)  # (body, level)


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
                bodies.append((lit, "zsh" if m.group(1) == "zsh" else "bash"))
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
                    bodies.append(("\n".join(body), level))
            pending = []
            continue
        out.append(c)
        i += 1
    return Scan("".join(out), bodies)


def texts_of(cmd: str, level: str = "zsh", origin: str = "command", depth: int = 0) -> list[Text]:
    s = scan(cmd)
    found = [Text(s.skeleton, level, origin, cmd)]
    if depth < 4:
        for body, lvl in s.shell_bodies:
            found.extend(texts_of(body, lvl, origin, depth + 1))
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
                w = w[1:]
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
        elif os.path.basename(head) == "as-app.sh":
            w = w[w.index("--") + 1:] if "--" in w else []
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

LESSONS = "skill/aa-lessons/guards.md"


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


def _rule_ship_command(t: Text) -> str | None:
    sk = t.skeleton
    cmds = simple_commands(sk)
    merges = 0
    for words in cmds:
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
    if merges >= 2:
        return ("ship_merge.py called more than once in one command (serial shipping); give ONE call every target "
                "(queue repos run in parallel), or `ship_wave.py` for migration chains")
    if merges and re.search(r"(?:^|[\s;&|(])(?:for|while|until)\s", sk) and re.search(r"(?:^|[\s;&|])done\b", sk):
        return ("ship_merge.py inside a shell loop (one PR after the other); give ONE call every target, or "
                "`ship_wave.py` for migration chains")
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


# --- RAM ---------------------------------------------------------------------------------------------------------


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
    pytest_args = None
    if prog == "pytest" or prog.startswith("py.test"):
        pytest_args = a
    elif re.fullmatch(r"python[0-9.]*", prog) and a[:2] == ["-m", "pytest"]:
        pytest_args = a[2:]
    if pytest_args is not None:
        targets = [x for x in pytest_args if not x.startswith("-")]
        if "-n" in pytest_args or any(x.startswith("-n") and x[2:].isdigit() for x in pytest_args):
            return "pytest -n (xdist)"
        if not any(x.endswith(".py") or "::" in x for x in targets):
            return "pytest over a whole directory"
        return None
    if prog == "node" and any(re.search(r"(?:^|/)uat/\S*\.cjs$", x) for x in a):
        return "UAT node scenario (Chromium)"
    return None


HEAVY_PROC = (
    ("next build", re.compile(r"(?:^|[/\x00])next(?:\.js)?\x00build(?:\x00|$)")),
    ("playwright", re.compile(r"playwright(?:/cli\.js)?\x00test")),
    ("pytest", re.compile(r"(?:^|\x00|/)(?:-m\x00)?pytest(?:\x00|$)")),
    ("vitest", re.compile(r"(?:^|[/\x00])vitest")),
    ("jest", re.compile(r"(?:^|[/\x00])jest(?:\.js)?(?:\x00|$)")),
    ("tsc", re.compile(r"(?:^|[/\x00])tsc(?:\x00|$)")),
    ("docker build", re.compile(r"(?:^|[/\x00])docker\x00(?:buildx\x00)?build")),
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


def ram_check(texts: list[Text], override: bool, proc: Path = Path("/proc")) -> tuple[str, str] | None:
    """(detail, fix) when a heavy command meets low memory, else None."""
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
        _log("RAM-1 override", lines[0])
        return None
    return detail, FIX["RAM-1"]


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
}


RULES = (("PKILL-1", _rule_pkill), ("ZSH-1", _rule_zsh), ("ENV-1", _rule_env), ("SHIP-1", _rule_ship_command))
RULE_IDS = tuple(r for r, _ in RULES) + ("RAM-1",)


def check(cmd: str, cwd: Path | None = None, proc: Path = Path("/proc")) -> Refusal | None:
    cwd = cwd or ROOT
    texts = texts_of(cmd)
    override = bool(re.match(r"\s*(?:\w+=\S*\s+)*AA_RAM_OVERRIDE=1\b", cmd))
    # Scripts the command runs are checked for merges (SHIP-1 d). Not for PKILL-1: a script's own command line is
    # `bash <path>`, so a `pgrep -f <other script>` inside it does not match itself (replay S271: 2 such waits).
    for t in list(texts):
        for path in _scripts_run(t, cwd):
            body = _read(path)
            if body is None:
                continue
            if MERGE_IN_SCRIPT.search(_strip_comments(body)):
                return Refusal("SHIP-1", f"{path.name} is a hand-written ship script (it merges PRs itself: "
                               f"serial waits, gate skipped)", FIX["SHIP-1"])
    for t in texts:
        where = "" if t.origin == "command" else f" (in {Path(t.origin).name})"
        for rule, fn in RULES:
            hit = fn(t)
            if hit:
                return Refusal(rule, hit + where, FIX[rule])
    ram = ram_check(texts, override, proc)
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
