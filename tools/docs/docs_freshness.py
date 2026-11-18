#!/usr/bin/env python3
"""Event-based docs freshness (AA-1132 A5): a page needs review when code it describes changed after its last change.

The S283 audit found 24 wrong pages while the calendar report ("last_reviewed + review_every_days") said 0 were due:
the drift came from code changes, not from time. This tool turns the central doc map (docs/catalogue/doc-map.yaml,
`<repo>` + code globs -> pages) into a per-page flag:

  needs_review   a commit in the entry's repo touched one of its code globs AFTER the page's own last commit.
                 {"since": <page's last change>, "count": n, "changes": [{"entry", "repo", "sha", "date", "files"}]}
                 (the newest CHANGES_SHOWN changes). Computed only for repos whose history is available; others are
                 listed as not checked, never guessed.

Files without front-matter (agent rules, skills, steering, every repo's CONTEXT.md) are registered in
docs/catalogue/doc-owners.yaml: path (a root path, a glob of root paths, or `<repo>:<path>`), owner role, optional
`review_every_days` (default DEFAULT_REVIEW_DAYS, the front-matter default), optional `last_reviewed` (default: the
file's last commit) and optional `depends_on` (doc-map entry ids, beyond the entries whose pages list the file). They
get the same flag plus the calendar check, so they appear in the freshness report too.

Commands:

  validate   doc-owners.yaml shape: known keys, a root path or glob matches a tracked file, depends_on ids exist in
             the doc map, no account ID / ARN / e-mail address. Exit 1 on a problem (docs lint).
  report     the freshness report (Markdown to --out, JSON to --json): pages and agent files that need review, agent
             files past their review date, repos checked. Exit 0 (warn only).
  verified   the `Verified:` rule (advisory L4): a PR that raises `last_reviewed` (a page's front-matter or a
             doc-owners.yaml row) must say in its body what was checked against what, on a line `Verified: ...`.
             Warn only (exit 0): prints `::warning` per page when the body has no such line.

History sources: this repo (a full clone: docs-sync and the weekly report fetch the whole history, blobless) and, with
--deps-root DIR, one git repo per app / Infra under DIR/<Repo> (a bare blobless clone in CI) or the workspace layout
DIR/apps/<Repo>, DIR/infra/<Repo>; --deps-ref picks the ref there (default HEAD; origin/main in a local workspace).

build_docs_reader.py calls `compute()` to write each published page's `needs_review` and the manifest's `freshness`.
Stdlib + PyYAML; reads git only (no network).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

import doc_impact
import repo_facts
from docslib import REPO_ROOT, split_front_matter

OWNERS = "docs/catalogue/doc-owners.yaml"
ROOT_REPO = doc_impact.ROOT_REPO
KNOWN_REPOS = {ROOT_REPO, *repo_facts.REPO_DIRS}
DEFAULT_REVIEW_DAYS = 90          # the front-matter default of review_every_days (docs/STYLE.md)
CHANGES_SHOWN = 5                 # output size of one needs_review entry, not a policy value
KEYS = {"path", "owner", "review_every_days", "last_reviewed", "depends_on", "why"}
OWNER = re.compile(r"^[a-z][a-z0-9-]*$")
VERIFIED = re.compile(r"^\s*verified\s*:\s*\S", re.I | re.M)
LAST_REVIEWED = re.compile(r"^last_reviewed:\s*['\"]?(\d{4}-\d{2}-\d{2})", re.M)


class OwnersError(Exception):
    pass


@dataclass
class Commit:
    sha: str
    date: str
    files: list[str]


@dataclass
class OwnerFile:
    path: str                     # `<path>` (root) or `<repo>:<path>`
    owner: str
    review_every_days: int = DEFAULT_REVIEW_DAYS
    last_reviewed: str | None = None
    depends_on: list[str] = field(default_factory=list)


OWNER_PATH = re.compile(r"^(?:(?P<repo>[A-Za-z0-9._-]+):)?(?P<path>[A-Za-z0-9._/@()*?\[\]-]+)$")


def split_path(path: str) -> tuple[str, str]:
    """`<repo>:<path>` or a root `<path>` (globs allowed) -> (repo, path)."""
    m = OWNER_PATH.match(path)
    if not m:
        raise OwnersError(f"path {path!r} is not `<path>` or `<repo>:<path>`")
    return m.group("repo") or ROOT_REPO, m.group("path")


def _utc(date: str) -> dt.datetime:
    d = dt.datetime.fromisoformat(date.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


# ------------------------------------------------------------------------------------------------------- git


def git_commits(repo_dir: Path, ref: str = "HEAD", paths: list[str] | None = None) -> list[Commit] | None:
    """Newest-first commits of `ref` with the files each touched; None when the history is not available (not a git
    repo, a shallow clone, an unknown ref)."""
    try:
        shallow = subprocess.run(["git", "-C", str(repo_dir), "rev-parse", "--is-shallow-repository"], check=True,
                                 capture_output=True, text=True).stdout.strip()
        if shallow != "false":
            return None
        cmd = ["git", "-C", str(repo_dir), "log", ref, "--format=%x00%H%x09%cI", "--name-only", "--no-renames"]
        if paths:
            cmd += ["--", *paths]
        out = subprocess.run(cmd, check=True, capture_output=True).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.CalledProcessError):
        return None
    commits = []
    for block in out.split("\0")[1:]:
        head, _, names = block.partition("\n")
        sha, _, date = head.partition("\t")
        commits.append(Commit(sha.strip(), date.strip(), [n.strip() for n in names.splitlines() if n.strip()]))
    return commits


def repo_dir(deps_root: Path | None, repo: str) -> Path | None:
    if repo == ROOT_REPO or deps_root is None:
        return None
    for cand in (deps_root / repo, deps_root / repo_facts.REPO_DIRS.get(repo, repo)):
        if cand.exists():
            return cand
    return None


def histories(root: Path, repos: set[str], deps_root: Path | None, deps_ref: str = "HEAD") -> dict[str, list[Commit]]:
    """{repo: commits} for every repo whose history is available (the root always, when a full clone)."""
    out: dict[str, list[Commit]] = {}
    for repo in sorted(repos | {ROOT_REPO}):
        if repo == ROOT_REPO:
            commits = git_commits(root)
        else:
            d = repo_dir(deps_root, repo)
            commits = git_commits(d, deps_ref) if d is not None else None
        if commits is not None:
            out[repo] = commits
    return out


# ---------------------------------------------------------------------------------------------------- owners


def parse_owners(text: str, root: Path | None = None, map_ids: set[str] | None = None) -> list[OwnerFile]:
    for pattern in doc_impact.MASK:
        if pattern.search(text):
            raise OwnersError(f"{OWNERS}: holds an account ID, ARN or e-mail address (public repo)")
    data = yaml.safe_load(text) or {}
    if data.get("version") != 1:
        raise OwnersError(f"{OWNERS}: version must be 1")
    problems, out = [], []
    tracked = _tracked(root) if root is not None else None
    for n, raw in enumerate(data.get("files") or []):
        where = f"{OWNERS} files[{n}]"
        if not isinstance(raw, dict):
            problems.append(f"{where}: expected a mapping")
            continue
        unknown = set(raw) - KEYS
        if unknown:
            problems.append(f"{where}: unknown key(s) {', '.join(sorted(unknown))}")
        path, owner = raw.get("path"), raw.get("owner")
        if not isinstance(path, str) or not path:
            problems.append(f"{where}: path must be a string")
            continue
        where = f"{OWNERS} {path}"
        if not isinstance(owner, str) or not OWNER.match(owner):
            problems.append(f"{where}: owner must be a role slug (tech-lead, engineer-on-duty, ...), never a name")
        days = raw.get("review_every_days", DEFAULT_REVIEW_DAYS)
        if not isinstance(days, int) or days < 1:
            problems.append(f"{where}: review_every_days must be a positive integer")
            days = DEFAULT_REVIEW_DAYS
        reviewed = raw.get("last_reviewed")
        if reviewed is not None:
            reviewed = str(reviewed)
            try:
                dt.date.fromisoformat(reviewed)
            except ValueError:
                problems.append(f"{where}: last_reviewed must be YYYY-MM-DD")
                reviewed = None
        deps = raw.get("depends_on") or []
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            problems.append(f"{where}: depends_on must be a list of doc-map entry ids")
            deps = []
        if map_ids is not None:
            for d in deps:
                if d not in map_ids:
                    problems.append(f"{where}: depends_on {d!r} is not an entry of {doc_impact.MAP}")
        try:
            prepo, ppath = split_path(path)
        except OwnersError as exc:
            problems.append(f"{where}: {exc}")
            continue
        if prepo not in KNOWN_REPOS:
            problems.append(f"{where}: unknown repo {prepo!r}")
        if prepo == ROOT_REPO and tracked is not None:
            if not [t for t in tracked if doc_impact.glob_regex(ppath).match(t)]:
                problems.append(f"{where}: matches no tracked file of this repo")
        out.append(OwnerFile(path, str(owner), days, reviewed, list(deps)))
    if problems:
        raise OwnersError("\n".join(problems))
    return out


def load_owners(root: Path = REPO_ROOT, check: bool = False) -> list[OwnerFile]:
    map_ids = {e.id for e in doc_impact.load_map(root / doc_impact.MAP)} if check else None
    return parse_owners((root / OWNERS).read_text(encoding="utf-8"), root if check else None, map_ids)


def _tracked(root: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], check=True, capture_output=True).stdout
        files = [f for f in out.decode("utf-8").split("\0") if f]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def expand(owners: list[OwnerFile], root: Path) -> list[OwnerFile]:
    """Root globs -> one OwnerFile per tracked file (app paths are kept as written)."""
    tracked = None
    out = []
    for o in owners:
        repo, path = split_path(o.path)
        if repo != ROOT_REPO or not re.search(r"[*?]", path):
            out.append(o)
            continue
        tracked = tracked if tracked is not None else _tracked(root)
        pattern = doc_impact.glob_regex(path)
        for t in tracked:
            if pattern.match(t):
                out.append(OwnerFile(t, o.owner, o.review_every_days, o.last_reviewed, list(o.depends_on)))
    return out


# --------------------------------------------------------------------------------------------------- compute


def _last_change(commits: list[Commit] | None, path: str) -> Commit | None:
    for c in commits or []:
        if path in c.files:
            return c
    return None


def entry_changes(entries: list[doc_impact.Entry], hist: dict[str, list[Commit]]) -> dict[str, list[dict]]:
    """{entry id: [{"sha", "date", "files"}] newest first} for the entries whose repo history is known."""
    out: dict[str, list[dict]] = {}
    for e in entries:
        commits = hist.get(e.repo)
        if commits is None:
            continue
        pages = {doc_impact.split_page(p)[1] for p in e.pages if doc_impact.split_page(p)[0] == e.repo}
        found = []
        for c in commits:
            hit = [f for f in c.files if f not in pages and any(p.match(f) for p in e.patterns)]
            if hit:
                found.append({"sha": c.sha, "date": c.date, "files": len(hit)})
        out[e.id] = found
    return out


def flag(page_date: str | None, entry_ids: list[str], changes: dict[str, list[dict]],
         entries_by_id: dict[str, doc_impact.Entry]) -> dict | None:
    """needs_review for a page whose last change is `page_date`: the mapped changes after it, or None."""
    if not page_date:
        return None
    since = _utc(page_date)
    after = []
    for eid in entry_ids:
        for ch in changes.get(eid, []):
            if _utc(ch["date"]) > since:
                after.append({"entry": eid, "repo": entries_by_id[eid].repo, **ch})
    if not after:
        return None
    after.sort(key=lambda c: _utc(c["date"]), reverse=True)
    return {"since": page_date, "count": len(after), "changes": after[:CHANGES_SHOWN]}


@dataclass
class Freshness:
    pages: dict[str, dict]                   # root page path -> needs_review
    agent_files: list[dict]
    repos_checked: list[str]
    repos_not_checked: list[str]

    def summary(self) -> dict:
        return {
            "repos_checked": self.repos_checked,
            "repos_not_checked": self.repos_not_checked,
            "pages_needing_review": len(self.pages),
            "agent_files": len(self.agent_files),
            "agent_files_needing_review": sum(1 for a in self.agent_files if a["needs_review"]),
            "agent_files_overdue": sum(1 for a in self.agent_files if a["overdue"]),
            "agent_files_list": [{"path": a["path"], "owner": a["owner"], "overdue": a["overdue"],
                                  "needs_review": bool(a["needs_review"])} for a in self.agent_files
                                 if a["overdue"] or a["needs_review"]],
        }


def compute(root: Path = REPO_ROOT, deps_root: Path | None = None, deps_ref: str = "HEAD",
            today: dt.date | None = None, page_dates: dict[str, str] | None = None) -> Freshness:
    """Flags for every root page the doc map names and for every doc-owners file. `page_dates` ({root path: ISO date
    of its last commit}) may come from the caller's own git walk (the bundle builder); missing ones are read here."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    entries = doc_impact.load_map(root / doc_impact.MAP)
    by_id = {e.id: e for e in entries}
    owners = expand(load_owners(root), root) if (root / OWNERS).exists() else []
    repos = {e.repo for e in entries} | {split_path(o.path)[0] for o in owners}
    hist = histories(root, repos, deps_root, deps_ref)
    changes = entry_changes(entries, hist)
    # page -> the entries that list it
    listed: dict[str, list[str]] = {}
    for e in entries:
        for p in e.pages:
            listed.setdefault(p, []).append(e.id)
    dates = dict(page_dates or {})

    def date_of(page: str) -> str | None:
        repo, path = doc_impact.split_page(page)
        if repo == ROOT_REPO and path in dates:
            return dates[path]
        c = _last_change(hist.get(repo), path)
        return c.date if c else None

    pages = {}
    for page, ids in listed.items():
        repo, path = doc_impact.split_page(page)
        if repo != ROOT_REPO:
            continue
        f = flag(date_of(page), ids, changes, by_id)
        if f:
            pages[path] = f
    agent = []
    for o in owners:
        repo, path = split_path(o.path)
        page_key = path if repo == ROOT_REPO else o.path
        ids = sorted(set(listed.get(page_key, [])) | set(o.depends_on))
        last = date_of(page_key)
        known = [d for d in (o.last_reviewed, last[:10] if last else None) if d]
        reviewed = max(known) if known else None          # a later commit counts as a look at the file too
        due = (dt.date.fromisoformat(reviewed) + dt.timedelta(days=o.review_every_days)).isoformat() if reviewed else None
        agent.append({"path": o.path, "owner": o.owner, "last_change": last, "last_reviewed": reviewed, "due": due,
                      "overdue": bool(due and due < today.isoformat()), "history_known": repo in hist,
                      "needs_review": flag(last, ids, changes, by_id)})
    checked = sorted(hist)
    return Freshness(pages, agent, checked, sorted(repos - set(checked)))


# ---------------------------------------------------------------------------------------------------- report


def render(fr: Freshness, today: dt.date) -> str:
    lines = ["# Docs freshness (event-based)", "",
             f"Generated {today.isoformat()} by `tools/docs/docs_freshness.py`. A page needs review when code its doc-map "
             "entries describe changed after the page's own last commit. Repos checked: "
             + (", ".join(fr.repos_checked) or "none") + "."]
    if fr.repos_not_checked:
        lines.append(f"Not checked (no history here): {', '.join(fr.repos_not_checked)}.")
    lines += ["", f"## Pages that need review ({len(fr.pages)})", ""]
    if fr.pages:
        lines += ["| Page | Last change | Code changes after it (newest) |", "|---|---|---|"]
        for path in sorted(fr.pages):
            f = fr.pages[path]
            newest = ", ".join(f"{c['entry']} {c['repo']}@{c['sha'][:8]} {c['date'][:10]}" for c in f["changes"][:2])
            lines.append(f"| `{path}` | {f['since'][:10]} | {f['count']}: {newest} |")
    else:
        lines.append("None.")
    flagged = [a for a in fr.agent_files if a["needs_review"] or a["overdue"]]
    lines += ["", f"## Agent files and CONTEXT.md ({len(flagged)} of {len(fr.agent_files)} flagged)", ""]
    if flagged:
        lines += ["| File | Owner | Last change | Review due | Needs review |", "|---|---|---|---|---|"]
        for a in flagged:
            nr = a["needs_review"]
            lines.append(f"| `{a['path']}` | {a['owner']} | {(a['last_change'] or '?')[:10]} | "
                         f"{a['due'] or '?'}{' (overdue)' if a['overdue'] else ''} | "
                         f"{str(nr['count']) + ' change(s)' if nr else 'no'} |")
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------------------------------------- verified


def _reviewed_in(text: str | None) -> str | None:
    if not text:
        return None
    fm, _ = split_front_matter(text)
    m = LAST_REVIEWED.search(fm or "")
    return m.group(1) if m else None


def raised_reviews(root: Path, base: str) -> list[str]:
    """Pages (and doc-owners rows) whose last_reviewed rose between `base` and the working tree."""
    out = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "--no-renames", "--diff-filter=M", base, "--",
                          "*.md", OWNERS], check=True, capture_output=True, text=True).stdout
    raised = []
    for path in [p for p in out.splitlines() if p.strip()]:
        old = subprocess.run(["git", "-C", str(root), "show", f"{base}:{path}"], capture_output=True, text=True)
        new_text = (root / path).read_text(encoding="utf-8") if (root / path).exists() else ""
        if path == OWNERS:
            try:
                before = {f.get("path"): str(f.get("last_reviewed") or "") for f in
                          (yaml.safe_load(old.stdout) or {}).get("files") or [] if isinstance(f, dict)}
                after = {f.get("path"): str(f.get("last_reviewed") or "") for f in
                         (yaml.safe_load(new_text) or {}).get("files") or [] if isinstance(f, dict)}
            except yaml.YAMLError:
                continue
            raised += [f"{OWNERS}: {p}" for p, d in after.items() if d and d > before.get(p, "")]
            continue
        a, b = _reviewed_in(old.stdout if old.returncode == 0 else None), _reviewed_in(new_text)
        if a and b and b > a:
            raised.append(path)
    return raised


def verified_findings(raised: list[str], body: str) -> list[str]:
    if not raised or VERIFIED.search(body or ""):
        return []
    return [f"::warning title=Verified line::{p}: last_reviewed rose, but the PR body has no `Verified: <what was "
            "checked against which code or live state>` line (AA-1132 A5; warn only)" for p in raised]


# ------------------------------------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--root", type=Path, default=REPO_ROOT)
    r = sub.add_parser("report")
    r.add_argument("--root", type=Path, default=REPO_ROOT)
    r.add_argument("--deps-root", type=Path)
    r.add_argument("--deps-ref", default="HEAD")
    r.add_argument("--out", type=Path, help="write the Markdown report here (default: stdout)")
    r.add_argument("--json", type=Path, help="also write the report as JSON")
    r.add_argument("--today", type=dt.date.fromisoformat, default=dt.datetime.now(dt.timezone.utc).date())
    w = sub.add_parser("verified")
    w.add_argument("--root", type=Path, default=REPO_ROOT)
    w.add_argument("--base", required=True)
    w.add_argument("--pr-body-file", type=Path)
    args = ap.parse_args(argv)

    if args.cmd == "validate":
        try:
            owners = load_owners(args.root, check=True)
        except (OwnersError, doc_impact.MapError, OSError, yaml.YAMLError) as exc:
            for line in str(exc).splitlines():
                print(f"::error title=Doc owners::{line}")
            return 1
        print(f"doc owners: {len(owners)} rows, {len(expand(owners, args.root))} files")
        return 0
    if args.cmd == "verified":
        body = args.pr_body_file.read_text(encoding="utf-8") if args.pr_body_file and args.pr_body_file.exists() else ""
        try:
            raised = raised_reviews(args.root, args.base)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"::warning title=Verified line::could not diff against {args.base}: {exc}")
            return 0
        for line in verified_findings(raised, body):
            print(line)
        print(f"verified: {len(raised)} page(s) raised last_reviewed; "
              + ("a Verified: line is present" if VERIFIED.search(body) else "no Verified: line"))
        return 0
    try:
        fr = compute(args.root, args.deps_root, args.deps_ref, args.today)
    except (doc_impact.MapError, OwnersError, OSError, yaml.YAMLError) as exc:
        print(f"::warning title=Docs freshness::not computed: {exc}")
        return 0
    text = render(fr, args.today)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"generated": args.today.isoformat(), "pages": fr.pages,
                                         "agent_files": fr.agent_files, **fr.summary()}, indent=1) + "\n",
                             encoding="utf-8")
    s = fr.summary()
    print(f"freshness: {s['pages_needing_review']} pages need review, {s['agent_files_needing_review']} agent files "
          f"need review, {s['agent_files_overdue']} overdue; repos checked: {', '.join(fr.repos_checked)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
