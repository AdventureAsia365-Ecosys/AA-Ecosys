"""Mechanical checks of a Kiro task — reads the WHOLE session, costs no model tokens.

Compares what Kiro really did (session.jsonl) with what the brief asked and what result.md claims.
Writes checks.md: one line per check, FLAG lines first. The reviewer reads this before anything.

usage: python3 kiro_check.py <task-dir>
  task-dir holds: brief.md, session.jsonl, result.md, diff.patch, git_status.txt, meta.txt

Brief conventions this relies on (see brief-template.md):
  ## Files in scope      -> lines "- `path/or/glob`"   (paths relative to the workdir)
  ## Test commands       -> lines "- `exact command`"
"""
import fnmatch
import json
import os
import re
import sys

SHELL = {"shell", "execute_bash"}
FORBIDDEN = [r"\baws\s", r"\bterraform\b", r"\bpsql\b", r"\bsudo\b", r"gh\s+pr\s+merge", r"gh\s+workflow\s+run",
             r"gh\s+secret", r"git\s+push\b.*(--force|\s-f\b)", r"git\s+push\b.*\b(main|master)\b"]
RESULT_SECTIONS = ["Summary", "Files changed", "Commands run", "Test results", "Decisions not in the brief",
                   "Open questions"]


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _section_items(md: str, title: str) -> list[str]:
    m = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", md, re.S | re.M | re.I)
    return re.findall(r"^\s*-\s*`([^`]+)`", m.group(1), re.M) if m else []


def _session(path: str):
    calls, results = {}, {}
    for line in _read(path).splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        for c in (e.get("data") or {}).get("content") or []:
            if c.get("kind") == "toolUse":
                calls[c["data"]["toolUseId"]] = c["data"]
            elif c.get("kind") == "toolResult":
                results[c["data"]["toolUseId"]] = c["data"]
    return calls, results


def _shell_out(result: dict) -> tuple[str, str]:
    for c in (result or {}).get("content") or []:
        d = c.get("data")
        if c.get("kind") == "json" and isinstance(d, dict) and "exit_status" in d:
            return d.get("exit_status", ""), (d.get("stdout") or "") + (d.get("stderr") or "")
    return "", ""


def main(task_dir: str) -> int:
    brief = _read(os.path.join(task_dir, "brief.md"))
    result_md = _read(os.path.join(task_dir, "result.md"))
    diff = _read(os.path.join(task_dir, "diff.patch"))
    status = _read(os.path.join(task_dir, "git_status.txt")).strip()
    calls, results = _session(os.path.join(task_dir, "session.jsonl"))
    flags, oks = [], []

    if not calls:
        flags.append("no session.jsonl / no tool calls captured — review run.clean.log by hand")
    shell = []
    for tid, call in calls.items():
        name = call.get("name")
        res = results.get(tid)
        if res is None:
            flags.append(f"`{name}` call has no result (interrupted?)")
        elif res.get("status") != "success":
            flags.append(f"`{name}` call status={res.get('status')}: {json.dumps(call.get('input'))[:160]}")
        if name in SHELL:
            cmd = (call.get("input") or {}).get("command", "")
            code, out = _shell_out(res)
            shell.append((cmd, code, out))
            if code and not code.endswith(" 0"):
                flags.append(f"non-zero exit ({code}): `{cmd[:160]}`")
            for pat in FORBIDDEN:
                if re.search(pat, cmd):
                    flags.append(f"forbidden command attempted: `{cmd[:160]}`")
    oks.append(f"{len(calls)} tool calls, {len(shell)} shell commands")

    for test in _section_items(brief, "Test commands"):
        runs = [(c, code, out) for c, code, out in shell if test in c]
        if not runs:
            flags.append(f"brief test command never run: `{test}`")
        else:
            code = runs[-1][1]
            (oks if code.endswith(" 0") else flags).append(f"test command ran, last exit `{code}`: `{test}`")

    scope = _section_items(brief, "Files in scope")
    changed = re.findall(r"^diff --git a/(\S+) b/", diff, re.M)
    if scope:
        outside = [p for p in changed if not any(fnmatch.fnmatch(p, s) or p.startswith(s.rstrip("*")) for s in scope)]
        for p in outside:
            flags.append(f"file changed outside 'Files in scope': {p}")
    oks.append(f"{len(changed)} files in diff.patch")
    if status:
        flags.append(f"uncommitted files left: {status.splitlines()[:5]}")

    if not result_md:
        flags.append("result.md missing")
    else:
        for sec in RESULT_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(sec)}", result_md, re.M | re.I):
                flags.append(f"result.md lacks section: {sec}")
        all_out = "\n".join(out for _, _, out in shell)
        for claim in sorted(set(re.findall(r"\b\d+ (?:passed|failed|errors?)\b", result_md))):
            (oks if claim in all_out else flags).append(
                f"result.md claim '{claim}' {'found' if claim in all_out else 'NOT FOUND'} in real command output")

    lines = [f"# Mechanical checks — {os.path.basename(task_dir.rstrip('/'))}", f"FLAGS: {len(flags)}", ""]
    lines += [f"- FLAG: {f}" for f in flags] + [f"- ok: {o}" for o in oks]
    with open(os.path.join(task_dir, "checks.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:2]))
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
