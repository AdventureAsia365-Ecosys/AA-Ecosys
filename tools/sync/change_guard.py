#!/usr/bin/env python3
"""Change guard (AA-1136 slice 1): code changed without a test change, or without an implementation-note entry.

A heuristic, so it reminds and never blocks inside a session (S284 hooks advisory, section 4). Callers: the Claude Code
Stop / SubagentStop dispatcher (`.claude/hooks/stop_dispatch.py`), later the pre-push scripts and the CI jobs
`notes-present` / `test-cochange` of the app repos.

What it reads in one checkout (main or a lane worktree):
  - the files changed since the merge base with origin/main (origin/master in the root repo), plus the working tree
    (staged, unstaged, untracked); on main/master only the working tree;
  - the issue ids from the branch name (feat/aa-1136-...) and the `Refs AA-...` lines of those commits;
  - the implementation notes docs/implementation-notes/<ISSUE>.md and <ISSUE>-<lane>.md of those ids, for waivers.

Findings:
  no-test  a code file changed (.py .ts .tsx .js .jsx .mjs .cjs .sh) and no test file changed, and no line
           `No test needed: <reason>` in the issue's notes file
  no-note  a code or schema file changed (.sql .tf .tfvars .hcl) and the issue's notes file did not change (with no
           issue id: no notes file changed), and no line `No note needed: <reason>` in the notes file

Commands:
  check    --repo-dir DIR [--json]: the findings for one checkout. Exit 0; exit 1 on findings when AA_SYNC_HOOKS=block.
  report   [--log FILE] [--since YYYY-MM-DD] [--json]: the measuring numbers of docs/implementation-notes/AA-1136.md
           from the hook log (events per hook, p50/p95 latency, errors, lane agents seen, would-remind findings).
  commits  --repo-dir DIR [--since YYYY-MM-DD] [--ref REF] [--json]: the uncovered-commit rate on the default branch
           (code commits with no implementation-notes change and no `No note needed:` waiver).

Python stdlib + git. Offline. Test: python3 .claude/hooks/test_sync_change_guard.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hookio  # noqa: E402

GIT_TIMEOUT_S = 3
NOTES_DIR = "docs/implementation-notes"
ISSUE = re.compile(r"(?i)\b(aa)-(\d+)\b")
REFS_LINE = re.compile(r"(?im)^\s*refs\s+(.+)$")
NOTE_FILE = re.compile(r"^(?:.*/)?docs/implementation-notes/(?P<id>[A-Za-z]+-\d+)(?:-[^/]*)?\.md$")
WAIVER = {
    "test": re.compile(r"(?im)^[\s>*_`-]*no test needed[*_`]*\s*:[*_`]*\s*(?P<reason>(?!<)\S.{2,})$"),
    "note": re.compile(r"(?im)^[\s>*_`-]*no note needed[*_`]*\s*:[*_`]*\s*(?P<reason>(?!<)\S.{2,})$"),
}
IGNORED = re.compile(r"(?:^|/)(?:\.tmp-session|node_modules|\.venv|venv|__pycache__|\.next|dist|build)/")
TEST = re.compile(
    r"(?:^|/)(?:tests?|__tests__|e2e)/"
    r"|(?:^|/)test_[^/]+\.(?:py|sh)$|_test\.py$|(?:^|/)conftest\.py$"
    r"|\.(?:test|spec)\.(?:ts|tsx|js|jsx|mjs|cjs)$")
CODE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".sh", ".bash")
SCHEMA_EXT = (".sql", ".tf", ".tfvars", ".hcl")
DOC_EXT = (".md", ".mdx", ".rst", ".txt")
SHOWN = 3
# git's repo-local variables (`git rev-parse --local-env-vars`): a caller inside a git hook (pre-push) has them set, and
# `git -C <other checkout>` would then act on the hook's repo instead (S272).
_GIT_ENV_DROP = ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR")


def classify(rel: str) -> str:
    """test | note | doc | schema | code | other | ignored, for a repo-relative path."""
    rel = rel.replace("\\", "/").removeprefix("./")
    if not rel or IGNORED.search("/" + rel):
        return "ignored"
    if NOTE_FILE.match(rel):
        return "note"
    if rel.startswith("docs/") or rel.endswith(DOC_EXT):
        return "doc"
    if TEST.search(rel):
        return "test"
    if rel.endswith(SCHEMA_EXT):
        return "schema"
    if rel.endswith(CODE_EXT):
        return "code"
    return "other"


def issue_ids(branch: str, messages: str) -> list[str]:
    ids = [f"AA-{m.group(2)}" for m in ISSUE.finditer(branch or "")]
    for line in REFS_LINE.finditer(messages or ""):
        ids += [f"AA-{m.group(2)}" for m in ISSUE.finditer(line.group(1))]
    return sorted(set(ids), key=lambda s: int(s.split("-")[1]))


def find_waivers(texts: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for text in texts:
        for kind, rx in WAIVER.items():
            m = rx.search(text)
            if m and kind not in out:
                out[kind] = m.group("reason").strip()[:160]
    return out


@dataclass
class Report:
    repo: str
    top: str
    branch: str = ""
    base: str = ""
    issues: list[str] = field(default_factory=list)
    code: list[str] = field(default_factory=list)
    schema: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    waivers: dict[str, str] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)
    error: str = ""

    def summary(self) -> dict:
        """The short form that goes into the hook log (no file contents, counts and codes only)."""
        out = {"repo": self.repo, "branch": self.branch, "issues": self.issues, "code": len(self.code),
               "schema": len(self.schema), "tests": len(self.tests), "notes": len(self.notes),
               "waivers": sorted(self.waivers), "findings": self.findings}
        if self.error:
            out["error"] = self.error
        return out

    def note_path(self) -> str:
        return f"{NOTES_DIR}/{self.issues[0]}.md" if self.issues else f"{NOTES_DIR}/<ISSUE>.md"

    def message(self) -> str:
        if not self.findings:
            return ""
        where = f"{self.repo} [{self.branch}]" if self.branch else self.repo
        lines = [f"Change guard (code -> tests -> notes) for {where}:"]
        if "no-test" in self.findings:
            shown = ", ".join(self.code[:SHOWN]) + (f" (+{len(self.code) - SHOWN})" if len(self.code) > SHOWN else "")
            lines.append(f"- {len(self.code)} code file(s) changed ({shown}) and no test file: add or update a test, "
                         f"or write 'No test needed: <reason>' in {self.note_path()}.")
        if "no-note" in self.findings:
            ids = ", ".join(self.issues) or "no issue id in the branch name or a Refs line"
            lines.append(f"- no implementation-note change ({ids}): update {self.note_path()} (Decisions / Changed / "
                         "Tradeoffs / Should know), or write 'No note needed: <reason>' there (small chores only).")
        lines.append("A reminder, not a block: fix it or waive it in the note, then go on.")
        return hookio.clip("\n".join(lines))


def evaluate(report: Report, changed: list[str], note_texts: list[str]) -> Report:
    """Fill the file lists, waivers and findings of `report` from the changed files (pure; no I/O)."""
    for rel in sorted(set(changed)):
        kind = classify(rel)
        if kind == "code":
            report.code.append(rel)
        elif kind == "schema":
            report.schema.append(rel)
        elif kind == "test":
            report.tests.append(rel)
        elif kind == "note":
            report.notes.append(rel)
    report.waivers = find_waivers(note_texts)
    if report.code and not report.tests and "test" not in report.waivers:
        report.findings.append("no-test")
    if report.code or report.schema:
        wanted = set(report.issues)
        note_ids = {m.group("id").upper() for n in report.notes if (m := NOTE_FILE.match(n))}
        note_ok = bool(note_ids & wanted) if wanted else bool(report.notes)
        if not note_ok and "note" not in report.waivers:
            report.findings.append("no-note")
    return report


# --- git ----------------------------------------------------------------------------------------------------------


def git(top: Path | str, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_DROP}
    env["GIT_OPTIONAL_LOCKS"] = "0"  # git status must not take the index lock another process holds
    res = subprocess.run(["git", "-C", str(top), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S,
                         env=env, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"git {args[0]}: {res.stderr.strip()[:200]}")
    return res.stdout


def default_base(top: Path | str) -> str:
    refs = git(top, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/main",
               "refs/remotes/origin/master").split()
    return refs[0] if refs else ""


def status_files(top: Path | str) -> list[str]:
    out, files = git(top, "status", "--porcelain=v1", "-z", "--untracked-files=all"), []
    parts = out.split("\0")
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        files.append(entry[3:])
        if entry[0] in "RC":  # a rename / copy carries the old path as the next field
            i += 1
    return files


def changes(top: Path | str) -> tuple[str, str, list[str], str]:
    """(branch, base ref, changed files, commit messages) of one checkout."""
    try:
        branch = git(top, "symbolic-ref", "--short", "-q", "HEAD").strip()
    except RuntimeError:
        branch = ""  # detached HEAD
    files = status_files(top)
    base, messages = "", ""
    if branch not in ("main", "master"):
        ref = default_base(top)
        if ref:
            merge_base = git(top, "merge-base", "HEAD", ref).strip()
            files += git(top, "diff", "--name-only", merge_base, "HEAD").split("\n")
            messages = git(top, "log", "--format=%B", f"{merge_base}..HEAD")
            base = ref
    return branch, base, [f for f in files if f], messages


def note_texts(top: Path, ids: list[str], changed_notes: list[str]) -> list[str]:
    paths: set[Path] = {top / n for n in changed_notes}
    for issue in ids:
        paths.add(top / NOTES_DIR / f"{issue}.md")
        paths.update((top / NOTES_DIR).glob(f"{issue}-*.md"))
    texts = []
    for p in sorted(paths):
        try:
            texts.append(p.read_text(encoding="utf-8", errors="replace")[:200_000])
        except OSError:
            continue
    return texts


def check(top: Path | str, name: str | None = None) -> Report:
    top = Path(top)
    repo = hookio.find_repo(top)
    report = Report(repo=name or (repo.name if repo else top.name), top=str(top))
    try:
        report.branch, report.base, changed, messages = changes(top)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        report.error = f"{type(e).__name__}: {e}"[:300]
        return report
    report.issues = issue_ids(report.branch, messages)
    notes = [f for f in changed if classify(f) == "note"]
    return evaluate(report, changed, note_texts(top, report.issues, notes))


# --- report / commits (measuring, docs/implementation-notes/AA-1136.md) -------------------------------------------


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, round(q / 100 * (len(s) - 1))))
    return s[k]


def read_log(path: Path, since: str = "") -> list[dict]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and str(row.get("ts", "")) >= since:
            rows.append(row)
    return rows


def summarize_log(rows: list[dict]) -> dict:
    events: dict[str, list[float]] = {}
    walls: dict[str, list[float]] = {}
    errors = 0
    lane_agents: dict[str, set] = {}
    would: dict[str, int] = {}
    waivers: dict[str, int] = {}
    for r in rows:
        ev = str(r.get("event") or "?")
        if isinstance(r.get("latency_ms"), (int, float)):
            events.setdefault(ev, []).append(float(r["latency_ms"]))
        else:
            events.setdefault(ev, [])
        if isinstance(r.get("wall_ms"), (int, float)):
            walls.setdefault(ev, []).append(float(r["wall_ms"]))
        if r.get("error"):
            errors += 1
        if r.get("agent") and r.get("agent") != "main" and r.get("repo_kind") == "worktree":
            lane_agents.setdefault(ev, set()).add(r["agent"])
        if ev == "PostToolUse" and r.get("would") == "remind":
            would["post-edit"] = would.get("post-edit", 0) + 1
        for c in r.get("checks") or []:
            for f in c.get("findings") or []:
                would[f] = would.get(f, 0) + 1
            for w in c.get("waivers") or []:
                waivers[w] = waivers.get(w, 0) + 1
    return {
        "events": len(rows),
        "errors": errors,
        "error_rate": round(errors / len(rows), 4) if rows else 0.0,
        "latency_ms": {ev: {"n": len(v), "p50": percentile(v, 50), "p95": percentile(v, 95)}
                       for ev, v in sorted(events.items())},
        # wall_ms (from the shell wrapper's start, interpreter included) is what M2 / M3 compare with
        "wall_ms": {ev: {"n": len(v), "p50": percentile(v, 50), "p95": percentile(v, 95)}
                    for ev, v in sorted(walls.items())},
        "lane_agents": {ev: len(a) for ev, a in sorted(lane_agents.items())},
        "would_remind": would,
        "waivers": waivers,
    }


def uncovered_commits(top: Path | str, since: str = "", ref: str = "") -> dict:
    ref = ref or default_base(top) or "HEAD"
    args = ["log", ref, "--no-merges", "--format=%x1e%H%x1f%B%x1f", "--name-only"]
    if since:
        args.insert(2, f"--since={since}")
    out = git(top, *args)
    code_commits, uncovered = 0, []
    for chunk in out.split("\x1e"):
        if not chunk.strip():
            continue
        sha, body, names = (chunk.split("\x1f") + ["", ""])[:3]
        files = [n for n in names.split("\n") if n.strip()]
        kinds = {classify(f) for f in files}
        if not kinds & {"code", "schema"}:
            continue
        code_commits += 1
        if "note" in kinds:
            continue
        ids = issue_ids("", body)
        waived = False
        for issue in ids:
            try:
                listed = git(top, "ls-tree", "--name-only", sha, f"{NOTES_DIR}/").split()
            except RuntimeError:
                break
            for name in listed:
                base = name.rsplit("/", 1)[-1]
                if base == f"{issue}.md" or base.startswith(f"{issue}-"):
                    try:
                        if WAIVER["note"].search(git(top, "show", f"{sha}:{name}")):
                            waived = True
                    except RuntimeError:
                        pass
        if not waived:
            uncovered.append(sha[:10])
    return {"ref": ref, "since": since, "code_commits": code_commits, "uncovered": len(uncovered),
            "rate": round(len(uncovered) / code_commits, 3) if code_commits else None, "shas": uncovered[:50]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--repo-dir", default=".")
    c.add_argument("--json", action="store_true")
    r = sub.add_parser("report")
    r.add_argument("--log", default="")
    r.add_argument("--since", default="")
    r.add_argument("--json", action="store_true")
    m = sub.add_parser("commits")
    m.add_argument("--repo-dir", default=".")
    m.add_argument("--since", default="")
    m.add_argument("--ref", default="")
    m.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "check":
        rep = check(Path(args.repo_dir).resolve())
        print(json.dumps(asdict(rep), indent=2) if args.json else (rep.message() or f"{rep.repo}: no findings"))
        return 1 if rep.findings and hookio.mode() == "block" else 0
    if args.cmd == "report":
        out = summarize_log(read_log(Path(args.log) if args.log else hookio.log_path(), args.since))
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f"events {out['events']}, errors {out['errors']} ({out['error_rate']:.2%})")
            for ev, v in out["latency_ms"].items():
                w = out["wall_ms"].get(ev, {})
                print(f"  {ev}: n={v['n']} p50={v['p50']} ms p95={v['p95']} ms (in script); wall p50={w.get('p50')} "
                      f"p95={w.get('p95')} ms; lane agents {out['lane_agents'].get(ev, 0)}")
            print(f"would remind: {out['would_remind'] or 'none'}; waivers: {out['waivers'] or 'none'}")
        return 0
    out = uncovered_commits(Path(args.repo_dir).resolve(), args.since, args.ref)
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        rate = "n/a" if out["rate"] is None else f"{out['rate']:.1%}"
        print(f"{out['ref']} since {out['since'] or 'start'}: {out['uncovered']}/{out['code_commits']} code commits "
              f"without a note ({rate})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
