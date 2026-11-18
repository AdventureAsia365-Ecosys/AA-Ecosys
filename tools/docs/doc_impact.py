#!/usr/bin/env python3
"""Docs impact: which docs pages describe the code a change touches (AA-1132 A4). Warning only, never a gate.

The S283 docs audit found pages wrong because a code change in one repo never told anyone about the page that
described it, often in another repo. `docs/catalogue/doc-map.yaml` (root repo, one central map, tech lead S283) lists
`<repo>` + code globs -> the pages that describe them. This tool takes the files a change touches and reports every map
entry whose code changed while none of its pages did.

Commands:

  check     --repo <name> and the changed files (--files a b c, --files-from FILE, or --base REF for `git diff
            --name-only REF...HEAD` in the current directory) [--pr-body-file FILE]. Prints the entries hit; with
            --github also `::warning` annotations, the step summary and, with --comment-out, the sticky PR comment
            body. Exit 0 always (warn only, S283), even when the map is broken (that prints a warning); --strict
            exits 1 when an entry is open (reserved for advisory slice A8, never used in CI today).
  validate  the map's shape: unique ids, known repos, globs, pages; every root page exists. Exit 1 on a problem
            (the root docs lint runs it).
  github-pr inside the reusable workflow .github/workflows/docs-impact.yml: reads the PR's files and body through
            `gh` (GH_TOKEN, REPO, PR), runs check, writes the step summary and creates / updates / clears one sticky
            comment (marker below). A failed GitHub call is a warning, never a failure.

A page is a root path (`docs/...`, `skill/...`) or `<repo>:<path>` for a page in that app repo. An entry is
"touched" when the change edits one of its pages (possible only for pages in the same repo); it is "acknowledged" when
the PR body has a line `Docs-impact: <root PR link> | updated-here | none: <reason>`. Touched entries are not
reported; acknowledged ones are reported as notices instead of warnings.

Callers: the reusable workflow (every app repo calls it), the hooks of the S284 hooks spec advisory slice 2
(`impact()` and `load_map()` are the import API), and pre-push (advisory slice A6).

Stdlib + PyYAML. Offline except `github-pr`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP = "docs/catalogue/doc-map.yaml"
ROOT_REPO = "AA-Ecosys"
ORG = "AdventureAsia365-Ecosys"
DEFAULT_BRANCH = {ROOT_REPO: "master"}          # every app repo: main
MARKER = "<!-- docs-impact -->"
SOURCES = ("audit-s283", "hand")
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PAGE = re.compile(r"^(?:(?P<repo>[A-Za-z0-9._-]+):)?(?P<path>[A-Za-z0-9._/@()\[\]-]+)$")
ACK = re.compile(r"^\s*docs-impact\s*:\s*(?P<value>\S.*?)\s*$", re.I | re.M)
ACK_VALUE = re.compile(r"^(?:https://github\.com/\S+/pull/\d+|updated-here|none\s*:\s*\S.*)$", re.I)
MASK = (re.compile(r"(?<!\d)\d{12}(?!\d)"), re.compile(r"arn:aws"), re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"))
FILES_SHOWN = 3


class MapError(Exception):
    pass


@dataclass
class Entry:
    id: str
    repo: str
    code: list[str]
    pages: list[str]
    source: str
    why: str = ""
    patterns: list[re.Pattern] = field(default_factory=list, repr=False)


@dataclass
class Hit:
    entry: Entry
    files: list[str]
    touched: list[str]

    @property
    def open(self) -> bool:
        return not self.touched


def glob_regex(glob: str) -> re.Pattern:
    """A path glob: `**/` any folders (or none), `**` anything, `*` and `?` within one path segment."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(f"^{out}$")


def split_page(page: str, default_repo: str = ROOT_REPO) -> tuple[str, str]:
    m = PAGE.match(page)
    if not m:
        raise MapError(f"page {page!r} is not `<path>` or `<repo>:<path>`")
    return m.group("repo") or default_repo, m.group("path")


def parse_map(text: str, root: Path | None = None) -> list[Entry]:
    """The entries of doc-map.yaml; MapError on any shape problem. With `root`, root pages must exist there."""
    for pattern in MASK:
        if pattern.search(text):
            raise MapError(f"{MAP}: holds an account ID, ARN or e-mail address (public repo)")
    data = yaml.safe_load(text) or {}
    if data.get("version") != 1:
        raise MapError(f"{MAP}: version must be 1")
    repos = data.get("repos")
    if not isinstance(repos, list) or ROOT_REPO not in repos:
        raise MapError(f"{MAP}: repos must list the repo names, {ROOT_REPO} included")
    entries, seen, problems = [], set(), []
    for n, raw in enumerate(data.get("entries") or []):
        where = f"{MAP} entries[{n}]"
        if not isinstance(raw, dict):
            problems.append(f"{where}: expected a mapping")
            continue
        eid = raw.get("id")
        if not isinstance(eid, str) or not ID.match(eid):
            problems.append(f"{where}: id must be kebab-case")
            continue
        where = f"{MAP} {eid}"
        if eid in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(eid)
        repo, code, pages, source = raw.get("repo"), raw.get("code"), raw.get("pages"), raw.get("source")
        if repo not in repos:
            problems.append(f"{where}: repo {repo!r} is not in repos")
        if not isinstance(code, list) or not code or not all(isinstance(c, str) and c for c in code):
            problems.append(f"{where}: code must be a non-empty list of globs")
            code = []
        for c in code:
            if c.startswith("/") or ".." in c.split("/") or c.startswith("./"):
                problems.append(f"{where}: code glob {c!r} must be relative to the repo root")
        if not isinstance(pages, list) or not pages or not all(isinstance(p, str) for p in pages):
            problems.append(f"{where}: pages must be a non-empty list")
            pages = []
        for p in pages:
            try:
                page_repo, page_path = split_page(p)
            except MapError as exc:
                problems.append(f"{where}: {exc}")
                continue
            if page_repo not in repos:
                problems.append(f"{where}: page {p!r} names an unknown repo")
            elif p.startswith(f"{ROOT_REPO}:"):
                problems.append(f"{where}: write the root page {p!r} as a plain path")
            elif page_repo == ROOT_REPO and root is not None and not (root / page_path).is_file():
                problems.append(f"{where}: page {p!r} does not exist in the root repo")
        if source not in SOURCES:
            problems.append(f"{where}: source must be one of {', '.join(SOURCES)}")
        why = raw.get("why", "")
        if not isinstance(why, str):
            problems.append(f"{where}: why must be a string")
            why = ""
        entries.append(Entry(eid, str(repo), list(code), list(pages), str(source), why,
                             [glob_regex(c) for c in code]))
    if problems:
        raise MapError("\n".join(problems))
    if not entries:
        raise MapError(f"{MAP}: no entries")
    return entries


def load_map(path: Path | None = None, check_pages: bool = False) -> list[Entry]:
    path = path or REPO_ROOT / MAP
    root = path.resolve().parents[2] if check_pages else None
    return parse_map(path.read_text(encoding="utf-8"), root)


def impact(entries: list[Entry], repo: str, files: list[str]) -> list[Hit]:
    """Every entry of `repo` whose code matches a changed file, with the entry's pages this change touched."""
    changed = sorted({f.strip().removeprefix("./") for f in files if f.strip()})
    hits = []
    for e in entries:
        if e.repo != repo:
            continue
        matched = [f for f in changed if any(p.match(f) for p in e.patterns)]
        if not matched:
            continue
        touched = []
        for page in e.pages:
            page_repo, page_path = split_page(page)
            if page_repo == repo and page_path in changed:
                touched.append(page)
        hits.append(Hit(e, matched, touched))
    return hits


def acknowledgement(body: str) -> str | None:
    """The `Docs-impact:` value of a PR body when it is one of the accepted forms, else None."""
    for m in ACK.finditer(body or ""):
        value = m.group("value").strip().strip("`")
        if ACK_VALUE.match(value):
            return value
    return None


def page_link(page: str) -> str:
    repo, path = split_page(page)
    branch = DEFAULT_BRANCH.get(repo, "main")
    label = path if repo == ROOT_REPO else f"{repo}:{path}"
    return f"[{label}](https://github.com/{ORG}/{repo}/blob/{branch}/{path})"


def comment_body(hits: list[Hit], repo: str, ack: str | None) -> str:
    """The sticky PR comment (Markdown), starting with MARKER. Lists open entries only."""
    open_hits = [h for h in hits if h.open]
    lines = [MARKER, "### Docs impact (warning only)", ""]
    if not open_hits:
        lines.append("No docs impact left: every mapped page was updated or nothing mapped changed.")
        return "\n".join(lines) + "\n"
    lines += [
        "This PR changes code that the docs pages below describe "
        f"([doc map](https://github.com/{ORG}/{ROOT_REPO}/blob/master/{MAP})). Check them: update a page of this "
        f"repo in this PR, a root page in an {ROOT_REPO} PR. Then add one line to the PR body: "
        "`Docs-impact: <root PR link>`, `Docs-impact: updated-here` or `Docs-impact: none: <reason>`. "
        "This check never blocks a merge.",
        "",
    ]
    if ack:
        lines += [f"Acknowledged in the PR body: `Docs-impact: {ack}`.", ""]
    lines += ["| Map entry | Changed here | Pages to check |", "|---|---|---|"]
    for h in open_hits:
        shown = ", ".join(f"`{f}`" for f in h.files[:FILES_SHOWN])
        more = f" (+{len(h.files) - FILES_SHOWN})" if len(h.files) > FILES_SHOWN else ""
        why = f" ({h.entry.why})" if h.entry.why else ""
        lines.append(f"| `{h.entry.id}`{why} | {shown}{more} | {', '.join(page_link(p) for p in h.entry.pages)} |")
    return "\n".join(lines) + "\n"


def annotations(hits: list[Hit], ack: str | None) -> list[str]:
    level = "notice" if ack else "warning"
    out = []
    for h in hits:
        if h.open:
            pages = ", ".join(h.entry.pages)
            out.append(f"::{level} title=Docs impact ({h.entry.id})::{len(h.files)} changed file(s) map to {pages}; "
                       "update them or say why not (Docs-impact: line in the PR body). Warning only.")
    return out


def text_report(hits: list[Hit], repo: str) -> str:
    if not hits:
        return f"docs impact: no mapped code changed in {repo}"
    lines = []
    for h in hits:
        state = "touched" if not h.open else "OPEN"
        lines.append(f"{state:7} {h.entry.id}: {len(h.files)} file(s) -> {', '.join(h.entry.pages)}")
    return "\n".join(lines)


def git_changed(base: str, cwd: str | None = None) -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", "--no-renames", f"{base}...HEAD"], cwd=cwd, check=True,
                         capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line.strip()]


# ------------------------------------------------------------------------------------------------- GitHub PR flow


def _gh(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True, input=input_text).stdout


def github_pr(entries: list[Entry] | None, map_error: str | None, dry_run: bool = False) -> int:
    """The reusable workflow's step. Never returns non-zero for a docs finding or a GitHub error."""
    full = os.environ.get("REPO", "")
    pr = os.environ.get("PR", "")
    repo = full.rsplit("/", 1)[-1]
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if map_error or entries is None:
        print(f"::warning title=Docs impact::the doc map does not load, nothing checked: {map_error}")
        return 0
    if not re.fullmatch(r"\d+", pr) or not full:
        print("::warning title=Docs impact::not a pull request run (REPO / PR unset), nothing checked")
        return 0
    try:
        listing = _gh("api", "--paginate", f"repos/{full}/pulls/{pr}/files",
                      "--jq", ".[] | .filename, (.previous_filename // empty)")
        files = [f for f in listing.splitlines() if f.strip()]
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"::warning title=Docs impact::could not list the PR files ({exc}); nothing checked")
        return 0
    body = os.environ.get("PR_BODY", "")
    ack = acknowledgement(body)
    hits = impact(entries, repo, files)
    for line in annotations(hits, ack):
        print(line)
    print(text_report(hits, repo))
    text = comment_body(hits, repo, ack)
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(text.replace(MARKER + "\n", "") + "\n")
    if dry_run:
        print(text)
        return 0
    try:
        existing = _gh("api", "--paginate", f"repos/{full}/issues/{pr}/comments", "--jq",
                       f'.[] | select(.body | startswith("{MARKER}")) | .id').split()
        if existing:
            _gh("api", "-X", "PATCH", f"repos/{full}/issues/comments/{existing[0]}", "--input", "-",
                input_text=json.dumps({"body": text}))
        elif any(h.open for h in hits):
            _gh("api", "-X", "POST", f"repos/{full}/issues/{pr}/comments", "--input", "-",
                input_text=json.dumps({"body": text}))
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        print(f"::warning title=Docs impact::could not post the PR comment ({detail.strip()[:200]}); "
              "the findings are in this run's summary")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--repo", required=True)
    src = c.add_mutually_exclusive_group(required=True)
    src.add_argument("--files", nargs="+")
    src.add_argument("--files-from")
    src.add_argument("--base")
    c.add_argument("--pr-body-file")
    c.add_argument("--map", default=str(REPO_ROOT / MAP))
    c.add_argument("--github", action="store_true", help="print ::warning annotations")
    c.add_argument("--comment-out", help="write the PR comment Markdown here")
    c.add_argument("--json", action="store_true")
    c.add_argument("--strict", action="store_true", help="exit 1 when an entry is open (advisory A8; not used in CI)")
    v = sub.add_parser("validate")
    v.add_argument("--map", default=str(REPO_ROOT / MAP))
    g = sub.add_parser("github-pr")
    g.add_argument("--map", default=str(REPO_ROOT / MAP))
    g.add_argument("--dry-run", action="store_true", help="print the comment instead of posting it")
    args = ap.parse_args(argv)

    if args.cmd == "validate":
        try:
            entries = load_map(Path(args.map), check_pages=True)
        except (MapError, OSError, yaml.YAMLError) as exc:
            for line in str(exc).splitlines():
                print(f"::error title=Doc map::{line}")
            return 1
        print(f"doc map: {len(entries)} entries, "
              f"{len({e.repo for e in entries})} repos, {len({p for e in entries for p in e.pages})} pages")
        return 0

    try:
        entries, error = load_map(Path(args.map)), None
    except (MapError, OSError, yaml.YAMLError) as exc:
        entries, error = None, str(exc).splitlines()[0]
    if args.cmd == "github-pr":
        return github_pr(entries, error, dry_run=args.dry_run)
    if entries is None:
        print(f"::warning title=Docs impact::the doc map does not load, nothing checked: {error}")
        return 0
    if args.files is not None:
        files = args.files
    elif args.files_from:
        files = Path(args.files_from).read_text(encoding="utf-8").splitlines()
    else:
        files = git_changed(args.base)
    body = Path(args.pr_body_file).read_text(encoding="utf-8") if args.pr_body_file else ""
    ack = acknowledgement(body)
    hits = impact(entries, args.repo, files)
    if args.json:
        print(json.dumps([{"id": h.entry.id, "files": h.files, "pages": h.entry.pages, "touched": h.touched,
                           "open": h.open} for h in hits], indent=1))
    else:
        print(text_report(hits, args.repo))
    if args.github:
        for line in annotations(hits, ack):
            print(line)
    if args.comment_out:
        Path(args.comment_out).write_text(comment_body(hits, args.repo, ack), encoding="utf-8")
    return 1 if args.strict and any(h.open for h in hits) else 0


if __name__ == "__main__":
    sys.exit(main())
