#!/usr/bin/env python3
"""Lessons log lint (AA-1024 G22): a new lesson line must say how the mistake is stopped next time. Stdlib only.

The tech lead (S271): writing a lesson does not stop the mistake; the same families kept coming back because a repeat
was appended to the old line instead of becoming a guard. So every NEW or CHANGED lesson line of
skill/aa-lessons/lessons.md (a top-level `- ` bullet under a `## ` section) ends with a Guard field
(skill/aa-lessons/SKILL.md section 3):

  Guard: test|hook|tool|ci|lane <path or hook rule>   the machine check that stops it; it must exist
  Guard: pending GRD-<n>|AA-<n>                      a guard not built yet; the id must be in docs/backlog/README.md
                                                     or docs/backlog/tracker/plan.json
  Guard: none: judgement|external|one-off <why>      no machine check is possible; the reason needs 3+ words

Checks: the field is there and well formed; a test/hook/tool/ci/lane target exists (a root path is checked here; a
path in a child repo, apps/... or infra/..., is checked where that checkout exists, so CI checks root paths only;
`aa_shell_guard:<RULE>` must be a rule of .claude/hooks/aa_shell_guard.py); a pending id is planned; a line that
cites two or more sessions (a repeat) cannot be `none: one-off`. Old lines are not checked (the backfill is the
guards list, skill/aa-lessons/guards.md).

Usage:
  python tools/docs/check_lessons.py --base origin/master        # CI: lines new or changed since the base ref
  python tools/docs/check_lessons.py --pending .tmp-session/S271-lessons-pending.md   # every line of a pending file
  python tools/docs/check_lessons.py --sweep                     # report: lines whose guard exists ("delete me")
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from docslib import REPO_ROOT, Finding, emit

LESSONS = Path("skill/aa-lessons/lessons.md")
HOOK_GUARD = Path(".claude/hooks/aa_shell_guard.py")
PLANNED = (Path("docs/backlog/README.md"), Path("docs/backlog/tracker/plan.json"))
KINDS = ("test", "hook", "tool", "ci", "lane")
NONE_REASONS = ("judgement", "external", "one-off")
GUARD_RE = re.compile(r"\bGuard:\s*(?P<body>.+?)\s*\.?\s*$")
SESSION_RE = re.compile(r"\bS(\d{3})\b")


def lesson_lines(text: str) -> list[tuple[int, str]]:
    """(line number, text) of every top-level bullet under a `## ` section."""
    out = []
    in_section = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            in_section = True
        elif in_section and line.startswith("- "):
            out.append((i, line))
    return out


def hook_rules(root: Path) -> set[str]:
    try:
        src = (root / HOOK_GUARD).read_text(encoding="utf-8")
    except OSError:
        return set()
    return set(re.findall(r"\"([A-Z]+-\d+)\"", src))


def child_checkout(root: Path, path: str) -> Path | None:
    """The child repo checkout a workspace path points into, when it is checked out here."""
    m = re.match(r"((?:apps|infra)/[^/]+)/", path)
    if not m:
        return None
    d = root / m.group(1)
    return d if (d / ".git").exists() else None


def check_target(kind: str, target: str, root: Path, rules: set[str]) -> str | None:
    """Why the target is not acceptable, or None."""
    tok = target.split()[0].strip("`'\",;()")
    m = re.fullmatch(r"aa_shell_guard(?:\.py)?:([A-Z]+-\d+)", tok)
    if m:
        return None if m.group(1) in rules else f"aa_shell_guard has no rule {m.group(1)} (rules: " \
                                                    f"{', '.join(sorted(rules)) or 'none found'})"
    path = re.sub(r":[\w.-]+$", "", tok)  # drop :line or ::test_name
    path = path.split("::")[0]
    if "/" not in path and "." not in path:
        return f"'{tok}' is not a path or hook rule (use e.g. tools/github/ship_wave.py or aa_shell_guard:PKILL-1)"
    if kind == "lane" and not path.startswith("tools/workflows/"):
        return f"a lane guard lives in tools/workflows/, not {path}"
    if path.startswith(("apps/", "infra/")):
        co = child_checkout(root, path)
        if co is not None and not (root / path).exists():
            return f"{path} does not exist in the {co.name} checkout"
        return None
    if not (root / path).exists():
        return f"{path} does not exist"
    return None


def check_line(text: str, root: Path, rules: set[str], planned: str) -> str | None:
    m = GUARD_RE.search(text)
    if not m:
        return ("no Guard field: end the line with 'Guard: <test|hook|tool|ci|lane> <path>', 'Guard: pending "
                "GRD-<n>' or 'Guard: none: <judgement|external|one-off> <why>' (skill/aa-lessons/SKILL.md section 3)")
    body = m.group("body")
    kind, _, rest = body.partition(" ")
    kind = kind.rstrip(":").lower()
    if kind in KINDS:
        if not rest.strip():
            return f"Guard: {kind} needs a target path or hook rule"
        return check_target(kind, rest.strip(), root, rules)
    if kind == "pending":
        pm = re.match(r"(GRD-\d+|AA-\d+)\b", rest.strip())
        if not pm:
            return "Guard: pending needs a GRD-<n> or AA-<n> id"
        if not re.search(rf"\b{re.escape(pm.group(1))}\b", planned):
            return f"{pm.group(1)} is not in docs/backlog/README.md or the tracker plan.json: plan the guard first"
        return None
    if kind == "none":
        nm = re.match(r":?\s*(\S+)\s*(.*)", rest)
        reason = (nm.group(1) if nm else "").rstrip(":,").lower()
        why = nm.group(2) if nm else ""
        if reason not in NONE_REASONS:
            return f"Guard: none: needs a reason kind ({', '.join(NONE_REASONS)}), got '{reason or '-'}'"
        if len(why.split()) < 3:
            return "Guard: none: say why no machine check fits (3+ words)"
        if reason == "one-off" and len(set(SESSION_RE.findall(text))) >= 2:
            return "the line cites two or more sessions (a repeat), so it is not one-off: build or plan a guard"
        return None
    return f"unknown Guard kind '{kind}' (use {', '.join(KINDS)}, pending or none:)"


def base_text(ref: str, root: Path) -> str:
    r = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{LESSONS.as_posix()}"], capture_output=True,
                       text=True)
    if r.returncode != 0:
        raise SystemExit(f"check_lessons: cannot read {LESSONS} at {ref}: {r.stderr.strip()}")
    return r.stdout


def lint(lines: list[tuple[int, str]], relpath: str, root: Path) -> list[Finding]:
    rules = hook_rules(root)
    planned = "\n".join((root / p).read_text(encoding="utf-8") for p in PLANNED if (root / p).exists())
    out = []
    for n, text in lines:
        why = check_line(text, root, rules, planned)
        if why:
            out.append(Finding(relpath, n, "Lesson needs a Guard", why))
    return out


def sweep(lines: list[tuple[int, str]], root: Path) -> list[str]:
    """Lines whose machine guard exists: candidates to delete (the guard replaces the line)."""
    rules = hook_rules(root)
    out = []
    for n, text in lines:
        m = GUARD_RE.search(text)
        if not m:
            continue
        kind, _, rest = m.group("body").partition(" ")
        if kind.lower() in KINDS and rest.strip() and check_target(kind.lower(), rest.strip(), root, rules) is None:
            out.append(f"{LESSONS}:{n}: delete me (guard {kind} {rest.split()[0]} exists)")
    return out


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--base", help="git ref: check the lesson lines new or changed since it")
    g.add_argument("--pending", help="a pending-lessons file: check every line")
    g.add_argument("--sweep", action="store_true", help="list lines whose guard exists (report only)")
    a = ap.parse_args(argv)
    if a.pending:
        p = Path(a.pending)
        text = p.read_text(encoding="utf-8")
        lines = [(i, x) for i, x in enumerate(text.splitlines(), 1) if x.startswith("- ")]
        findings = lint(lines, str(p), root)
    else:
        current = lesson_lines((root / LESSONS).read_text(encoding="utf-8"))
        if a.sweep:
            for line in sweep(current, root):
                print(line)
            return 0
        old = {t for _, t in lesson_lines(base_text(a.base, root))}
        new = [(n, t) for n, t in current if t not in old]
        findings = lint(new, LESSONS.as_posix(), root)
        print(f"check_lessons: {len(new)} new or changed lesson line(s) since {a.base}, {len(findings)} without a "
              f"valid Guard field")
    emit(findings, "error")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
