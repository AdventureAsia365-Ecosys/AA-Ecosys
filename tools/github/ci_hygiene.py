#!/usr/bin/env python3
"""CI hygiene status for the session-start block (AA-1024, S273). Read-only unless --clean; stdlib + PyYAML + gh CLI.

For each of the 6 repos:
  * Actions cache usage against GitHub's 10 GB per-repo cap (above it GitHub evicts least-recently-used entries, which
    can be the default-branch caches every run restores), split by ref kind (default branch / pull request / merge
    queue / other) with the top key families by size. CodeQL default setup's own caches (codeql-*) are listed but
    cannot be limited from a workflow (repository setting, no input).
  * Stale caches: those of pull requests that are not open and of merge-queue refs idle for more than 2 h (nobody can
    read them again). --clean deletes exactly those (the logic of .github/scripts/cache_cleanup.py, which each repo's
    Cache cleanup workflow runs on pull request close and daily).
  * A static scan of the default branch's .github/workflows/*.yml and .github/actions/*/action.yml with the rules of
    .github/scripts/workflow_lint.py: WL5 (a step that downloads a binary from outside without a cache + sha256 pin, or
    an action that downloads its own binary: anchore/sbom-action, setup-trivy, ...) and WL4 (a cache that also saves
    on pull request / merge-queue refs).
  * WL7 (warn, root ADR 0021 decision 4): an actions/upload-artifact step without `retention-days`, or with more than
    14 days and no `# retention: <why>` comment in the step (or the comment lines right above it).
  * The organisation's public repositories against the known list (REPOS): a new or unknown public repository is a
    finding (ADR 0021 decision 2.1: on the Free plan members can still create public repositories).

    python3 tools/github/ci_hygiene.py                  # table; RED lines go into the opening status block
    python3 tools/github/ci_hygiene.py --json
    python3 tools/github/ci_hygiene.py --clean          # delete the stale pull request / merge-queue caches
    python3 tools/github/ci_hygiene.py --local-root .   # scan local checkouts instead of the default branches
    python3 tools/github/ci_hygiene.py --retention-scan .   # WL7 only, one checkout, GitHub warning annotations

Reads use the local `gh` login by hand, the aa-ecosys-ci-bot token (Actions read) in the root CI hygiene workflow, which
turns the --json report into one issue per finding type (tools/github/hygiene_issues.py, ADR 0021 decision 5 layer 3).
A token that cannot read a repo's Actions caches (HTTP 403) does not make the repo unreadable: its row carries
`cache_error` and its workflows are still scanned. Exit: 0 green | 1 RED (a repo over --warn-gb, default 8 GB, a WL5
finding, or an unknown public repository) | 2 a repo unreadable. --retention-scan always exits 0 (warn mode).
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ORG = "AdventureAsia365-Ecosys"
REPOS = ("AA-Ecosys", "AA-CIS-App", "AA-Booking", "AA-Partner", "AA-TripPlanner-Web", "AA-CIS-Infra")
LOCAL_DIRS = {"AA-Ecosys": ".", "AA-CIS-App": "apps/AA-CIS-App", "AA-Booking": "apps/AA-Booking",
              "AA-Partner": "apps/AA-Partner", "AA-TripPlanner-Web": "apps/AA-TripPlanner-Web",
              "AA-CIS-Infra": "infra/AA-CIS-Infra"}
CAP_GB = 10.0
SCRIPTS = Path(__file__).resolve().parents[2] / ".github" / "scripts"
SCAN_SKIP = frozenset({"WL1", "WL2", "WL3"})   # repo-local rules: each repo's Workflow Lint runs them
RETENTION_MAX_DAYS = 14
UPLOAD_ARTIFACT = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?actions/upload-artifact@")
RETENTION_DAYS = re.compile(r"^\s*retention-days:\s*['\"]?([^'\"#\s]+)")
RETENTION_WHY = re.compile(r"#\s*retention:\s*\S")
NEEDS_PERMISSION = re.compile(r"HTTP 403|Resource not accessible|must have admin|insufficient", re.I)
HASHY = re.compile(r"[0-9a-f]{12,}|\d{4}-\d{2}-\d{2}|\d+\.\d+\.\d+(?:\.\d+)?|pr-\d+|\d{6,}")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


cc = _load("cache_cleanup")
wl = _load("workflow_lint")


def ref_kind(ref: str, default_branch: str) -> str:
    if cc.pr_number(ref) is not None:
        return "pull"
    if cc.QUEUE_REF.match(ref or ""):
        return "queue"
    if ref == f"refs/heads/{default_branch}":
        return "default"
    return "other"


def family(key: str) -> str:
    """A cache key with its hashes, dates and versions folded: 'setup-uv-1-x86_64-unknown-linux-gnu-*-*'."""
    return HASHY.sub("*", key or "?")[:70]


def summarize(caches: list[dict], default_branch: str, top: int = 5) -> dict:
    by_kind: dict[str, int] = {}
    fams: dict[str, list[int]] = {}
    for c in caches:
        size = int(c.get("size_in_bytes") or 0)
        kind = ref_kind(c.get("ref") or "", default_branch)
        by_kind[kind] = by_kind.get(kind, 0) + size
        f = fams.setdefault(family(c.get("key") or ""), [0, 0])
        f[0] += 1
        f[1] += size
    top_fams = sorted(({"family": k, "entries": v[0], "bytes": v[1]} for k, v in fams.items()),
                      key=lambda r: -r["bytes"])[:top]
    return {"bytes": cc.total_bytes(caches), "entries": len(caches), "by_ref": by_kind, "top": top_fams}


def default_branch(repo: str, run=subprocess.run) -> str:
    return cc.gh(["api", f"repos/{ORG}/{repo}", "--jq", ".default_branch"], run).strip() or "main"


def is_workflow_file(path: str) -> bool:
    return bool(re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", path)
                or re.fullmatch(r"\.github/actions/[^/]+/action\.ya?ml", path))


def tree_paths(repo: str, run=subprocess.run) -> list[str]:
    """Every file path of the default branch."""
    out = cc.gh(["api", f"repos/{ORG}/{repo}/git/trees/HEAD?recursive=1", "--jq",
                 '.tree[] | select(.type == "blob") | .path'], run)
    return out.splitlines()


def read_remote(repo: str, path: str, run=subprocess.run) -> str:
    raw = cc.gh(["api", f"repos/{ORG}/{repo}/contents/{path}", "--jq", ".content"], run)
    return base64.b64decode(raw).decode("utf-8")


def remote_files(repo: str, run=subprocess.run, want=is_workflow_file) -> list[tuple[str, str]]:
    """(path, text) of the default branch's files that `want` accepts (workflow and composite action files)."""
    return [(path, read_remote(repo, path, run)) for path in tree_paths(repo, run) if want(path)]


def local_files(root: Path) -> list[tuple[str, str]]:
    found = sorted([*root.glob(".github/workflows/*.y*ml"), *root.glob(".github/actions/*/action.y*ml")])
    return [(str(p.relative_to(root)), p.read_text(encoding="utf-8")) for p in found]


def scan(files: list[tuple[str, str]]) -> list[str]:
    findings = []
    for path, text in files:
        try:
            if path.startswith(".github/actions/"):
                findings += wl.lint_action(path, text, SCAN_SKIP)
            else:
                findings += wl.lint_workflow(path.rsplit("/", 1)[-1], text, ".", SCAN_SKIP)
        except Exception as exc:  # noqa: BLE001 - a file that does not parse is a finding, not a crash
            findings.append(f"{path}:-:WL0 cannot parse: {type(exc).__name__}")
    return findings


def _step_block(lines: list[str], i: int) -> tuple[int, int]:
    """(first, end) line indexes of the YAML list item that holds line i, the comment lines right above it included."""
    indent = len(lines[i]) - len(lines[i].lstrip())
    start = i
    if not lines[i].lstrip().startswith("-"):
        start = next((j for j in range(i - 1, -1, -1) if lines[j].lstrip().startswith("- ")
                      and len(lines[j]) - len(lines[j].lstrip()) < indent), i)
    dash = len(lines[start]) - len(lines[start].lstrip())
    first = start
    while first > 0 and lines[first - 1].lstrip().startswith("#"):
        first -= 1
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= dash:
            break
        end += 1
    while end > start + 1 and lines[end - 1].lstrip().startswith("#"):   # those belong to the next step
        end -= 1
    return first, end


def retention_findings(path: str, text: str) -> list[str]:
    """WL7 (warn): every actions/upload-artifact step sets retention-days <= 14, or says why it keeps longer in a
    `# retention: <why>` comment (ADR 0021 decision 4). An expression value cannot be checked and passes."""
    findings, lines = [], text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#") or not UPLOAD_ARTIFACT.match(line):
            continue
        first, end = _step_block(lines, i)
        block = lines[first:end]
        days = next((m.group(1) for m in map(RETENTION_DAYS.match, block) if m), None)
        why = any(RETENTION_WHY.search(b) for b in block)
        if days is None:
            findings.append(f"{path}:{i + 1}:WL7 actions/upload-artifact without retention-days (the repository "
                            f"default applies, 90 days unless changed): set retention-days: {RETENTION_MAX_DAYS} or "
                            "less, or say why in a '# retention:' comment")
        elif days.isdigit() and int(days) > RETENTION_MAX_DAYS and not why:
            findings.append(f"{path}:{i + 1}:WL7 actions/upload-artifact keeps {days} days (> {RETENTION_MAX_DAYS}) "
                            "without a '# retention: <why>' comment in the step")
    return findings


def retention_scan(files: list[tuple[str, str]]) -> list[str]:
    out = []
    for path, text in files:
        out += retention_findings(path, text)
    return out


def org_repos(run=subprocess.run) -> list[dict]:
    """name / visibility / archived of every repository of the org the token can see (all public ones)."""
    out = cc.gh(["api", "--paginate", f"orgs/{ORG}/repos?per_page=100", "--jq",
                 '.[] | {name, visibility, archived}'], run)
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def unknown_public(repos: list[dict], known=REPOS) -> list[str]:
    return sorted(r["name"] for r in repos if r.get("visibility") == "public" and r.get("name") not in known)


def org_check(run=subprocess.run) -> dict:
    try:
        repos = org_repos(run)
    except (cc.GhError, json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        return {"public": [], "unknown_public": [], "error": str(exc)[:200]}
    return {"public": sorted(r["name"] for r in repos if r.get("visibility") == "public"),
            "unknown_public": unknown_public(repos), "error": None}


def collect(repo: str, *, warn_gb: float, clean: bool = False, local_root: Path | None = None,
            run=subprocess.run, now=None, log=print) -> dict:
    branch = default_branch(repo, run)
    cache_error = None
    try:
        caches = cc.list_caches(f"{ORG}/{repo}", run)
    except cc.GhError as exc:
        if not NEEDS_PERMISSION.search(str(exc)):
            raise
        caches, cache_error = [], "the token cannot read this repository's Actions caches (needs Actions: read)"
    open_prs = cc.open_pull_requests(f"{ORG}/{repo}", run)
    stale = cc.select(caches, "stale", open_prs=open_prs, now=now)
    row = {"repo": repo, "default_branch": branch, **summarize(caches, branch), "stale": len(stale),
           "stale_bytes": cc.total_bytes(stale), "deleted": 0, "deleted_bytes": 0, "cache_error": cache_error}
    if clean and stale:
        failed = cc.delete(f"{ORG}/{repo}", stale, run, log)
        row["deleted"] = len(stale) - failed
        row["deleted_bytes"] = row["stale_bytes"] if not failed else 0
    files = local_files(local_root / LOCAL_DIRS[repo]) if local_root else remote_files(repo, run)
    findings = scan(files)
    row["wl5"] = [f for f in findings if ":WL5 " in f or ":WL0 " in f]
    row["wl4"] = [f for f in findings if ":WL4 " in f]
    row["wl7"] = retention_scan(files)
    row["files"] = len(files)
    after = row["bytes"] - row["deleted_bytes"]
    row["red"] = [r for r, bad in ((f"cache {after / 1e9:.1f} GB > {warn_gb:g} GB (cap {CAP_GB:g})",
                                    after > warn_gb * 1e9),
                                   (f"{len(row['wl5'])} uncached external download(s)", bool(row["wl5"])))
                  if bad]
    return row


def print_table(rows: list[dict], unreadable: list[str], warn_gb: float, clean: bool, verbose: bool = False,
                org: dict | None = None) -> None:
    red = [r for r in rows if r["red"]]
    print(f"CI hygiene (Actions cache vs {CAP_GB:g} GB cap, RED above {warn_gb:g} GB; external downloads): "
          f"{len(red)} red of {len(rows)} repos")
    if org and org.get("error"):
        print(f"??? org repositories unreadable: {org['error']}")
    elif org and org.get("unknown_public"):
        print(f"RED  public repositories not in the known list: {', '.join(org['unknown_public'])}")
    for r in rows:
        refs = ", ".join(f"{k} {v / 1e9:.2f}" for k, v in sorted(r["by_ref"].items(), key=lambda kv: -kv[1]))
        mark = "RED " if r["red"] else "    "
        print(f"{mark}{r['repo']:<20} {r['bytes'] / 1e9:5.2f} GB in {r['entries']:>3} caches ({refs or 'none'}); "
              f"stale {r['stale']} ({r['stale_bytes'] / 1e9:.2f} GB)"
              + (f", deleted {r['deleted']}" if clean else "") + f"; {r['files']} workflow/action files scanned")
        if r.get("cache_error"):
            print(f"     ???: {r['cache_error']}")
        for why in r["red"]:
            print(f"     RED: {why}")
        for t in r["top"]:
            note = "  (CodeQL default setup: not configurable)" if t["family"].startswith("codeql") else ""
            print(f"       {t['bytes'] / 1e9:5.2f} GB {t['entries']:>3}x {t['family']}{note}")
        for f in r["wl5"]:
            print(f"     RED {f}")
        for f in r["wl4"] if verbose else []:
            print(f"     warn {f}")
        if r["wl4"] and not verbose:
            print(f"     warn: {len(r['wl4'])} cache step(s) that also save on pull request / queue refs (WL4; --verbose)")
        for f in r.get("wl7", []) if verbose else []:
            print(f"     warn {f}")
        if r.get("wl7") and not verbose:
            print(f"     warn: {len(r['wl7'])} artifact upload(s) without a short retention (WL7; --verbose)")
    for repo in unreadable:
        print(f"??? {repo}: gh could not read its caches or workflows (login, rate limit)")
    if any(r["stale"] for r in rows) and not clean:
        print("Stale caches: python3 tools/github/ci_hygiene.py --clean deletes them (pull request / queue refs only).")


def main(argv: list[str] | None = None, run=subprocess.run, now=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="list every WL4 warning")
    ap.add_argument("--clean", action="store_true", help="delete stale pull request / merge-queue caches")
    ap.add_argument("--warn-gb", type=float, default=8.0, help="RED above this many GB of caches (8)")
    ap.add_argument("--local-root", type=Path, help="scan local checkouts under this workspace root")
    ap.add_argument("--repos", nargs="+", choices=REPOS, default=list(REPOS))
    ap.add_argument("--no-org", action="store_true", help="skip the org public-repository check")
    ap.add_argument("--retention-scan", type=Path, metavar="CHECKOUT",
                    help="WL7 only: print ::warning annotations for one checkout's workflows; exit 0")
    a = ap.parse_args(argv)
    if a.retention_scan:
        found = retention_scan(local_files(a.retention_scan))
        for f in found:
            path, line, msg = f.split(":", 2)
            print(f"::warning file={path},line={line}::{msg}")
        print(f"WL7 artifact retention: {len(found)} warning(s) in {a.retention_scan}")
        return 0
    rows, unreadable = [], []
    quiet = (lambda m: None) if a.json else print
    for repo in a.repos:
        try:
            rows.append(collect(repo, warn_gb=a.warn_gb, clean=a.clean, local_root=a.local_root, run=run, now=now,
                                log=quiet))
        except (cc.GhError, json.JSONDecodeError, ValueError, OSError, subprocess.TimeoutExpired):
            unreadable.append(repo)
    org = None if a.no_org else org_check(run)
    org_red = bool(org and org["unknown_public"])
    if a.json:
        print(json.dumps({"rows": rows, "red": sum(bool(r["red"]) for r in rows) + org_red, "unreadable": unreadable,
                          "org": org, "warn_gb": a.warn_gb}, indent=1))
    else:
        print_table(rows, unreadable, a.warn_gb, a.clean, a.verbose, org)
    if any(r["red"] for r in rows) or org_red:
        return 1
    return 2 if unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
