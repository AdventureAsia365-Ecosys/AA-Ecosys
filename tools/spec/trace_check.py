#!/usr/bin/env python3
"""Spec trace check (AA-1137): requirement -> task -> test / live step, for Kiro-compatible specs. Stdlib only.

A spec is a folder `.kiro/specs/AA-<n>-<slug>/` in the repo that owns the work (cross-repo work: the root repo):

  requirements.md  front-matter id / issue / status / owner_repo / kind (+ approved_at, supersedes), a Problem
                   paragraph, then EARS criteria, one per line, each followed by a Verify line:
                     - R1.1 WHEN <trigger> THE SYSTEM SHALL <response>.
                       Verify: test tests/unit/test_x.py; live: GET /health returns 200
                   A bugfix spec may name this file bugfix.md (Kiro's name); never both.
  design.md        required for kind feature (migration / auth / multi-repo issues): decisions `### D1 <title>`,
                   each with a `Hard to reverse: yes|no` line; a `yes` needs an `Approved:` line before the spec
                   is in-progress (the tech lead approves those on the session decision page).
  tasks.md         Kiro checkboxes, one task per line, its requirement refs on the next line:
                     - [ ] T1 <title> - repo: AA-CIS-App - lane: l1
                       _Requirements: R1.1, R1.2_
                   [x] done, [~] carried (names the issue it moved to: "carried -> AA-<n> (reason)"),
                   [-] dropped ("dropped: <reason>"). Kiro ignores the _Requirements_ line; this tool reads it.

Lifecycle (front-matter status): draft -> approved (the session issue list is approved) -> in-progress (first
lane) -> implemented (every task [x], [~] or [-]) -> archived (moved to .kiro/specs/_archive/). After implemented a
spec is a historical contract: a later change of behaviour opens a new spec with `supersedes: spec-AA-<n>`.

Errors (exit 1) make the CI job Spec trace red; warnings are printed only. Rules:
  every task names at least one existing requirement (dropped tasks excepted), every requirement says SHALL and has a
  Verify line with a test or a live step, ids are unique, carried / dropped tasks say where / why, an implemented
  spec has no open task, a hard-to-reverse decision is approved before the work starts, no account or resource ID
  (the same patterns the public docs redaction and resource-ID lint use; specs ship in public repos), and with
  --base: a spec that was implemented (or archived) at the base is frozen (only the status line may move to archived).

Usage:
  python3 tools/spec/trace_check.py check <spec-dir> [...] [--base REF] [--json]
  python3 tools/spec/trace_check.py show <spec-dir> [--tasks T1,T2]      # the tasks + their requirements, verbatim
  python3 tools/spec/trace_check.py pr --root . [--extra-root DIR] --text-file pr.md [--base SHA] [--summary FILE]
      (CI: the specs of every AA-<n> the PR text names, plus every spec the PR changes; none -> pass)
Tests: python3 -m unittest discover -s tools/spec -p 'test_*.py'
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPECS_DIR = Path(".kiro/specs")
ARCHIVE = "_archive"
STATUSES = ("draft", "approved", "in-progress", "implemented", "archived")
STARTED = ("in-progress", "implemented", "archived")
FROZEN = ("implemented", "archived")
KINDS = ("feature", "bugfix", "quick")
REQUIRED_FM = ("id", "issue", "status", "owner_repo", "kind")
OPEN, DONE, CARRIED, DROPPED = " ", "x", "~", "-"

FENCE = re.compile(r"^\s*(```|~~~)")
REQ_LINE = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?(R\d+\.\d+)(?:\*\*)?(?=[\s:.)(]|$)\s*[:.]?\s*(.*)$")
VERIFY_LINE = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*|_)?Verify(?:\*\*|_)?\s*:\s*(.*)$", re.I)
TASK_LINE = re.compile(r"^\s*[-*]\s+\[([ xX~-])\]\s+(T\d+(?:\.\d+)?)(?=[\s:.]|$)\s*[:.]?\s*(.*)$")
REQS_REF = re.compile(r"^\s*_?Requirements\s*:\s*(.*?)_?\s*$", re.I)
DECISION = re.compile(r"^#{2,4}\s+(D\d+)\b\s*(.*)$")
HARD = re.compile(r"^\s*(?:[-*]\s+)?Hard to reverse\s*:\s*(yes|no)\b(.*)$", re.I)
APPROVED = re.compile(r"^\s*(?:[-*]\s+)?Approved\s*:\s*\S", re.I)
HEADING = re.compile(r"^#{1,6}\s")
CARRIED_TO = re.compile(r"carried\s*(?:→|->)\s*AA-\d+", re.I)
DROPPED_WHY = re.compile(r"dropped\s*:\s*\S", re.I)
REPO_FIELD = re.compile(r"\brepo:\s*([A-Za-z0-9._-]+)")
ISSUE_ID = re.compile(r"\bAA-(\d+)\b")
SPEC_DIRNAME = re.compile(r"^AA-(\d+)(?:-[A-Za-z0-9._-]+)?$")
SHALL = re.compile(r"\bshall\b", re.I)
ACCESS_KEY = ("AWS access key ID", re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"))


def _id_patterns() -> list[tuple[str, re.Pattern[str]]]:
    """The resource-ID lint patterns (tools/docs/check_docs_text.py) plus the access key redaction pattern."""
    docs = HERE.parent / "docs"
    if str(docs) not in sys.path:
        sys.path.insert(0, str(docs))
    from check_docs_text import RESOURCE_PATTERNS  # noqa: PLC0415  (sibling tool, stdlib only)
    return list(RESOURCE_PATTERNS) + [ACCESS_KEY]


@dataclass
class Requirement:
    rid: str
    text: str
    line: int
    tests: list[str] = field(default_factory=list)
    live: list[str] = field(default_factory=list)
    has_verify: bool = False
    bad_items: list[str] = field(default_factory=list)


@dataclass
class Task:
    tid: str
    state: str
    text: str
    line: int
    refs: list[str] = field(default_factory=list)
    repo: str = ""


@dataclass
class Decision:
    did: str
    title: str
    line: int
    hard: str | None = None
    approved: bool = False


@dataclass
class Finding:
    level: str  # error | warning
    file: str
    line: int
    message: str

    def render(self) -> str:
        return f"{self.level}: {self.file}:{self.line}: {self.message}"


@dataclass
class Spec:
    path: Path
    front: dict[str, str]
    req_file: str
    requirements: dict[str, Requirement]
    tasks: dict[str, Task]
    decisions: dict[str, Decision]
    has_design: bool
    findings: list[Finding]

    @property
    def status(self) -> str:
        return self.front.get("status", "")

    @property
    def spec_id(self) -> str:
        return self.front.get("id", "")


def parse_front_matter(text: str) -> tuple[dict[str, str] | None, int]:
    """`key: value` lines between two '---' lines at the top (no YAML dependency). Returns (fields, body line)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0
    front: dict[str, str] = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return front, i + 1
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if m:
            front[m.group(1)] = m.group(2).strip().strip("\"'")
    return None, 0


def _content_lines(text: str, start: int = 0):
    """(line number, line) outside fenced code blocks, from line index `start`."""
    fenced = False
    for i, line in enumerate(text.splitlines()):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or i < start:
            continue
        yield i + 1, line


def _verify_items(raw: str, req: Requirement) -> None:
    for item in (p.strip() for p in raw.split(";")):
        if not item:
            continue
        if re.match(r"^live\b", item, re.I):
            body = re.sub(r"^live\s*:?\s*", "", item, flags=re.I)
            if body:
                req.live.append(body)
            else:
                req.bad_items.append(item)
        elif re.match(r"^tests?\s*:", item, re.I):
            body = re.sub(r"^tests?\s*:\s*", "", item, flags=re.I)
            (req.tests if body else req.bad_items).append(body or item)
        elif re.match(r"^test\s+\S", item, re.I):
            req.tests.append(item[5:].strip())
        elif "/" in item or "::" in item or re.search(r"\.(py|ts|tsx|js|cjs|mjs|sh)\b", item):
            req.tests.append(item)
        else:
            req.bad_items.append(item)


def _parse_requirements(text: str, start: int, rel: str, findings: list[Finding]) -> dict[str, Requirement]:
    reqs: dict[str, Requirement] = {}
    current: Requirement | None = None
    for n, line in _content_lines(text, start):
        if HEADING.match(line):
            current = None
            continue
        m = REQ_LINE.match(line)
        if m:
            rid, body = m.group(1), m.group(2).strip()
            if rid in reqs:
                findings.append(Finding("error", rel, n, f"{rid} is defined twice"))
            current = Requirement(rid, body, n)
            reqs[rid] = current
            continue
        v = VERIFY_LINE.match(line)
        if v and current is not None:
            current.has_verify = True
            _verify_items(v.group(1), current)
        elif current is not None and not current.has_verify and line.startswith((" ", "\t")) and line.strip():
            current.text += " " + line.strip()  # a criterion wrapped onto the next line
    return reqs


def _parse_tasks(text: str, rel: str, findings: list[Finding]) -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    current: Task | None = None
    for n, line in _content_lines(text):
        m = TASK_LINE.match(line)
        if m:
            state, tid, body = m.group(1).lower(), m.group(2), m.group(3).strip()
            if tid in tasks:
                findings.append(Finding("error", rel, n, f"{tid} is defined twice"))
            repo = REPO_FIELD.search(body)
            current = Task(tid, state, body, n, repo=repo.group(1) if repo else "")
            tasks[tid] = current
            continue
        if HEADING.match(line) or re.match(r"^\s*[-*]\s+\[", line):
            current = None
            continue
        r = REQS_REF.match(line)
        if r and current is not None:
            current.refs += [x for x in re.split(r"[,\s]+", r.group(1).strip().strip("_")) if x]
    return tasks


def _parse_design(text: str) -> dict[str, Decision]:
    decisions: dict[str, Decision] = {}
    current: Decision | None = None
    for n, line in _content_lines(text):
        m = DECISION.match(line)
        if m:
            current = Decision(m.group(1), m.group(2).strip(), n)
            decisions[current.did] = current
            continue
        if HEADING.match(line):
            current = None
            continue
        if current is None:
            continue
        h = HARD.match(line)
        if h:
            current.hard = h.group(1).lower()
        elif APPROVED.match(line):
            current.approved = True
    return decisions


def _resolve_ref(ref: str, reqs: dict[str, Requirement]) -> list[str]:
    """R1.1 / 1.1 -> [R1.1]; R1 / 1 -> every R1.x; unknown -> []."""
    ref = ref.strip().rstrip(".")
    if not ref:
        return []
    if not ref.upper().startswith("R"):
        ref = "R" + ref
    ref = "R" + ref[1:]
    if ref in reqs:
        return [ref]
    if re.fullmatch(r"R\d+", ref):
        return [r for r in reqs if r.startswith(ref + ".")]
    return []


def _rel(path: Path, base: Path | None) -> str:
    try:
        return str(path.relative_to(base)) if base else str(path)
    except ValueError:
        return str(path)


def load_spec(spec_dir: Path, display_base: Path | None = None) -> Spec:
    """Parse a spec folder and run every check that needs only its files."""
    spec_dir = Path(spec_dir)
    f: list[Finding] = []
    rel_dir = _rel(spec_dir, display_base)
    req_path = spec_dir / "requirements.md"
    bug_path = spec_dir / "bugfix.md"
    if req_path.is_file() and bug_path.is_file():
        f.append(Finding("error", rel_dir, 0, "has both requirements.md and bugfix.md; keep one"))
    if not req_path.is_file() and bug_path.is_file():
        req_path = bug_path
    req_rel = _rel(req_path, display_base)
    if not req_path.is_file():
        f.append(Finding("error", rel_dir, 0, "no requirements.md (or bugfix.md)"))
        return Spec(spec_dir, {}, req_rel, {}, {}, {}, False, f)
    text = req_path.read_text(encoding="utf-8")
    front, body = parse_front_matter(text)
    if front is None:
        f.append(Finding("error", req_rel, 1, "no front-matter block (--- id / issue / status / owner_repo / kind ---)"))
        front = {}
    reqs = _parse_requirements(text, body, req_rel, f)

    tasks: dict[str, Task] = {}
    tasks_path = spec_dir / "tasks.md"
    tasks_rel = _rel(tasks_path, display_base)
    if tasks_path.is_file():
        tasks = _parse_tasks(tasks_path.read_text(encoding="utf-8"), tasks_rel, f)
    else:
        f.append(Finding("error", rel_dir, 0, "no tasks.md"))

    design_path = spec_dir / "design.md"
    decisions = _parse_design(design_path.read_text(encoding="utf-8")) if design_path.is_file() else {}
    spec = Spec(spec_dir, front, req_rel, reqs, tasks, decisions, design_path.is_file(), f)
    _check_front(spec, rel_dir)
    _check_requirements(spec)
    _check_tasks(spec, tasks_rel)
    _check_design(spec, _rel(design_path, display_base))
    _check_public_safety(spec, display_base)
    return spec


def _check_front(spec: Spec, rel_dir: str) -> None:
    fm, f, rel = spec.front, spec.findings, spec.req_file
    if not fm:
        return
    missing = [k for k in REQUIRED_FM if not fm.get(k)]
    if missing:
        f.append(Finding("error", rel, 1, f"front-matter lacks {', '.join(missing)}"))
    if fm.get("status") and fm["status"] not in STATUSES:
        f.append(Finding("error", rel, 1, f"status {fm['status']!r} is not one of {', '.join(STATUSES)}"))
    if fm.get("kind") and fm["kind"] not in KINDS:
        f.append(Finding("error", rel, 1, f"kind {fm['kind']!r} is not one of {', '.join(KINDS)}"))
    issue = fm.get("issue", "")
    if issue and not re.fullmatch(r"AA-\d+", issue):
        f.append(Finding("error", rel, 1, f"issue {issue!r} is not an AA-<n> key"))
    elif issue:
        if fm.get("id") and fm["id"] != f"spec-{issue}":
            f.append(Finding("error", rel, 1, f"id {fm['id']!r} should be 'spec-{issue}' (one issue, one spec)"))
        m = SPEC_DIRNAME.match(spec.path.name)
        if not m or f"AA-{m.group(1)}" != issue:
            f.append(Finding("error", rel_dir, 0, f"folder name {spec.path.name!r} should be '{issue}-<slug>'"))
    if fm.get("status") in STATUSES[1:] and not fm.get("approved_at"):
        f.append(Finding("error", rel, 1, f"status {fm['status']} needs approved_at (the date the session list "
                                          "with this issue was approved)"))
    if fm.get("supersedes") and not re.fullmatch(r"spec-AA-\d+", fm["supersedes"]):
        f.append(Finding("error", rel, 1, f"supersedes {fm['supersedes']!r} should be spec-AA-<n>"))


def _check_requirements(spec: Spec) -> None:
    f, rel = spec.findings, spec.req_file
    if not spec.requirements and spec.front:
        f.append(Finding("error", rel, 0, "no requirement lines (R1.1 WHEN ... THE SYSTEM SHALL ...)"))
    for r in spec.requirements.values():
        if not SHALL.search(r.text):
            f.append(Finding("error", rel, r.line, f"{r.rid} is not an EARS criterion (no SHALL)"))
        if not r.has_verify:
            f.append(Finding("error", rel, r.line, f"{r.rid} has no Verify line (a test or a live step)"))
        elif not (r.tests or r.live):
            f.append(Finding("error", rel, r.line, f"{r.rid}: its Verify line names no test and no live step"))
        for item in r.bad_items:
            f.append(Finding("error", rel, r.line, f"{r.rid}: Verify item {item!r} is neither a test (a path, or "
                                                   "'test: ...') nor a live step ('live: ...')"))


def _check_tasks(spec: Spec, rel: str) -> None:
    f = spec.findings
    if (spec.path / "tasks.md").is_file() and not spec.tasks:
        f.append(Finding("error", rel, 0, "no task lines (- [ ] T1 ...)"))
    covered: set[str] = set()
    for t in spec.tasks.values():
        resolved: list[str] = []
        for ref in t.refs:
            hit = _resolve_ref(ref, spec.requirements)
            if not hit:
                f.append(Finding("error", rel, t.line, f"{t.tid} names {ref!r}, which is not a requirement of "
                                                       "this spec"))
            resolved += hit
        if t.state != DROPPED:
            covered.update(resolved)
            if not t.refs:
                f.append(Finding("error", rel, t.line, f"{t.tid} names no requirement (_Requirements: R1.1_ on "
                                                       "the next line)"))
        if t.state == CARRIED and not CARRIED_TO.search(t.text):
            f.append(Finding("error", rel, t.line, f"{t.tid} is carried but names no issue ('carried -> AA-<n> "
                                                   "(reason)')"))
        if t.state == DROPPED and not DROPPED_WHY.search(t.text):
            f.append(Finding("error", rel, t.line, f"{t.tid} is dropped without a reason ('dropped: <reason>')"))
        if t.state == OPEN and spec.status in FROZEN:
            f.append(Finding("error", rel, t.line, f"{t.tid} is still open but the spec is {spec.status}: tick it, "
                                                   "carry it to an issue or drop it with a reason"))
    for rid, r in spec.requirements.items():
        if rid not in covered and spec.tasks:
            f.append(Finding("warning", spec.req_file, r.line, f"{rid} is not named by any task that is not "
                                                               "dropped"))


def _check_design(spec: Spec, rel: str) -> None:
    f = spec.findings
    if spec.front.get("kind") == "feature" and not spec.has_design:
        f.append(Finding("error", _rel(spec.path, None), 0, "a feature spec needs design.md (decisions D1 ...)"))
        return
    if spec.front.get("kind") == "feature" and not spec.decisions:
        f.append(Finding("error", rel, 0, "design.md has no decision (### D1 <title>)"))
    for d in spec.decisions.values():
        if d.hard is None:
            f.append(Finding("error", rel, d.line, f"{d.did} lacks a 'Hard to reverse: yes|no' line"))
        elif d.hard == "yes" and not d.approved and spec.status in STARTED:
            f.append(Finding("error", rel, d.line, f"{d.did} is hard to reverse and has no 'Approved:' line; the "
                                                   "tech lead approves it on the decision page before the work "
                                                   "starts"))


def _check_public_safety(spec: Spec, display_base: Path | None) -> None:
    patterns = _id_patterns()
    for path in sorted(spec.path.glob("*.md")):
        rel = _rel(path, display_base)
        for n, line in _content_lines(path.read_text(encoding="utf-8")):
            for label, pattern in patterns:
                if pattern.search(line):
                    spec.findings.append(Finding("error", rel, n, f"{label} in a spec (specs ship in public repos; "
                                                                  "name the resource instead)"))
                    break


# --- frozen check against a base revision -------------------------------------------------------------------------


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def _git_root(path: Path) -> Path | None:
    p = _git(path if path.is_dir() else path.parent, "rev-parse", "--show-toplevel")
    return Path(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else None


def _without_status(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not re.match(r"^status\s*:", line))


def check_frozen(spec: Spec, base: str) -> list[Finding]:
    """A spec implemented (or archived) at `base` may only change its status line to archived."""
    root = _git_root(spec.path)
    if root is None:
        return [Finding("warning", str(spec.path), 0, "not in a git checkout; frozen check skipped")]
    rel_dir = spec.path.resolve().relative_to(root.resolve())
    base_req = None
    for name in ("requirements.md", "bugfix.md"):
        p = _git(root, "show", f"{base}:{(rel_dir / name).as_posix()}")
        if p.returncode == 0:
            base_req = p.stdout
            break
    if base_req is None:
        return []
    base_front, _ = parse_front_matter(base_req)
    if not base_front or base_front.get("status") not in FROZEN:
        return []
    out: list[Finding] = []
    for path in sorted(spec.path.glob("*.md")):
        rel = (rel_dir / path.name).as_posix()
        old = _git(root, "show", f"{base}:{rel}")
        new = path.read_text(encoding="utf-8")
        if old.returncode != 0:
            out.append(Finding("error", rel, 0, f"frozen: the spec was {base_front['status']} at the base; a new file "
                                                "is a change (open a new spec with supersedes: "
                                                f"{base_front.get('id', 'spec-AA-<n>')})"))
            continue
        if old.stdout == new:
            continue
        status_only = _without_status(old.stdout) == _without_status(new) and spec.status == "archived"
        if not status_only:
            out.append(Finding("error", rel, 0, f"frozen: the spec was {base_front['status']} at the base and may "
                                                "only move to archived; a change of behaviour is a new spec with "
                                                f"supersedes: {base_front.get('id', 'spec-AA-<n>')}"))
    return out


# --- finding specs for a PR -----------------------------------------------------------------------------------------


def spec_dirs_for_issue(root: Path, number: str) -> list[Path]:
    base = root / SPECS_DIR
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and (m := SPEC_DIRNAME.match(p.name)) and
                  m.group(1) == number)


def changed_spec_dirs(root: Path, base: str) -> list[Path]:
    p = _git(root, "diff", "--name-only", base, "HEAD", "--", str(SPECS_DIR))
    if p.returncode != 0:
        raise RuntimeError(f"git diff against {base} failed: {p.stderr.strip()[:200]}")
    dirs: set[Path] = set()
    for name in p.stdout.splitlines():
        parts = Path(name).parts
        # .kiro/specs/<spec>/<file> or .kiro/specs/_archive/<spec>/<file>
        if len(parts) >= 4 and parts[2] != ARCHIVE:
            d = root / Path(*parts[:3])
        elif len(parts) >= 5 and parts[2] == ARCHIVE:
            d = root / Path(*parts[:4])
        else:
            continue
        if d.is_dir():
            dirs.add(d)
    return sorted(dirs)


def run_checks(dirs: list[Path], base: str | None, display_base: Path | None = None) -> list[tuple[Spec, list[Finding]]]:
    results = []
    for d in dirs:
        spec = load_spec(d, display_base)
        findings = list(spec.findings)
        if base:
            findings += check_frozen(spec, base)
        results.append((spec, findings))
    return results


def _report(results: list[tuple[Spec, list[Finding]]], as_json: bool) -> int:
    errors = sum(1 for _, fs in results for x in fs if x.level == "error")
    if as_json:
        print(json.dumps([{"spec": str(s.path), "id": s.spec_id, "status": s.status,
                           "requirements": len(s.requirements), "tasks": len(s.tasks),
                           "findings": [x.__dict__ for x in fs]} for s, fs in results], indent=1))
    else:
        for s, fs in results:
            for x in fs:
                print(x.render())
            open_tasks = sum(1 for t in s.tasks.values() if t.state == OPEN)
            print(f"{s.path}: {s.spec_id or '?'} status={s.status or '?'} requirements={len(s.requirements)} "
                  f"tasks={len(s.tasks)} open={open_tasks} errors={sum(1 for x in fs if x.level == 'error')} "
                  f"warnings={sum(1 for x in fs if x.level == 'warning')}")
    return 1 if errors else 0


def show(spec: Spec, task_ids: list[str]) -> str:
    """The named tasks (all when empty) with the requirements they name, verbatim, for a lane brief."""
    out = [f"spec {spec.spec_id} ({spec.status}) {spec.path}"]
    wanted = task_ids or list(spec.tasks)
    for tid in wanted:
        t = spec.tasks.get(tid)
        if t is None:
            out.append(f"{tid}: not in tasks.md")
            continue
        out.append(f"- [{t.state}] {t.tid} {t.text}")
        for ref in t.refs:
            for rid in _resolve_ref(ref, spec.requirements):
                r = spec.requirements[rid]
                out.append(f"    {rid} {r.text}")
                out.append(f"      Verify: {'; '.join(r.tests + ['live: ' + x for x in r.live])}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check spec folders")
    c.add_argument("dirs", nargs="+", type=Path)
    c.add_argument("--base", help="git revision for the frozen check")
    c.add_argument("--json", action="store_true")
    s = sub.add_parser("show", help="print tasks with their requirements")
    s.add_argument("dir", type=Path)
    s.add_argument("--tasks", default="", help="comma-separated task ids (default: all)")
    p = sub.add_parser("pr", help="CI: check the specs of the issues a PR names and the specs it changes")
    p.add_argument("--root", type=Path, default=Path("."), help="the checked-out repo")
    p.add_argument("--extra-root", type=Path, action="append", default=[],
                   help="another checkout whose .kiro/specs also counts (the root repo, for cross-repo specs)")
    p.add_argument("--text-file", type=Path, required=True, help="PR title + body (and commit messages)")
    p.add_argument("--base", help="base revision: changed specs + frozen check")
    p.add_argument("--summary", type=Path, help="append a Markdown summary here (GITHUB_STEP_SUMMARY)")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        return _report(run_checks(a.dirs, a.base), a.json)
    if a.cmd == "show":
        spec = load_spec(a.dir)
        print(show(spec, [t.strip() for t in a.tasks.split(",") if t.strip()]))
        return 0

    root = a.root.resolve()
    text = a.text_file.read_text(encoding="utf-8") if a.text_file.is_file() else ""
    issues = sorted(set(ISSUE_ID.findall(text)), key=int)
    dirs: list[Path] = []
    for number in issues:
        dirs += spec_dirs_for_issue(root, number)
        for extra in a.extra_root:
            dirs += spec_dirs_for_issue(extra.resolve(), number)
    if a.base:
        try:
            dirs += changed_spec_dirs(root, a.base)
        except RuntimeError as e:
            print(f"error: {e}")
            return 1
    dirs = sorted(set(d.resolve() for d in dirs))
    lines = [f"Issues named: {', '.join('AA-' + i for i in issues) or 'none'}"]
    if not dirs:
        lines.append("No spec for these issues and no spec changed: pass (the check blocks only issues with a spec).")
        print("\n".join(lines))
        if a.summary:
            with open(a.summary, "a", encoding="utf-8") as fh:
                fh.write("### Spec trace\n\n" + "\n\n".join(lines) + "\n")
        return 0
    # The frozen check compares this repo's files with the base; a spec of the extra root is checked as it is.
    results = []
    for d in dirs:
        spec = load_spec(d)
        findings = list(spec.findings)
        if a.base and d.is_relative_to(root):
            findings += check_frozen(spec, a.base)
        results.append((spec, findings))
    rc = _report(results, False)
    if a.summary:
        rows = ["| Spec | Status | Requirements | Tasks open | Errors | Warnings |", "|---|---|---|---|---|---|"]
        for s, fs in results:
            rows.append(f"| {s.spec_id or s.path.name} | {s.status} | {len(s.requirements)} | "
                        f"{sum(1 for t in s.tasks.values() if t.state == OPEN)}/{len(s.tasks)} | "
                        f"{sum(1 for x in fs if x.level == 'error')} | {sum(1 for x in fs if x.level == 'warning')} |")
        errs = [x.render() for _, fs in results for x in fs if x.level == "error"]
        with open(a.summary, "a", encoding="utf-8") as fh:
            fh.write("### Spec trace\n\n" + "\n".join(lines) + "\n\n" + "\n".join(rows) + "\n")
            if errs:
                fh.write("\n```text\n" + "\n".join(errs[:50]) + "\n```\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
