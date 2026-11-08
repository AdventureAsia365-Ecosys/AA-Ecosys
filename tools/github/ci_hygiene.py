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

    python3 tools/github/ci_hygiene.py                  # table; RED lines go into the opening status block
    python3 tools/github/ci_hygiene.py --json
    python3 tools/github/ci_hygiene.py --clean          # delete the stale pull request / merge-queue caches
    python3 tools/github/ci_hygiene.py --local-root .   # scan local checkouts instead of the default branches

Reads use the local `gh` login (no App token; public repos). Exit: 0 green | 1 RED (a repo over --warn-gb, default 8
GB, or a WL5 finding) | 2 a repo unreadable.
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


def remote_files(repo: str, run=subprocess.run) -> list[tuple[str, str]]:
    """(path, text) of the default branch's workflow files and composite action files."""
    out = cc.gh(["api", f"repos/{ORG}/{repo}/git/trees/HEAD?recursive=1", "--jq",
                 '.tree[] | select(.type == "blob") | .path'], run)
    paths = [p for p in out.splitlines() if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", p)
             or re.fullmatch(r"\.github/actions/[^/]+/action\.ya?ml", p)]
    files = []
    for path in paths:
        raw = cc.gh(["api", f"repos/{ORG}/{repo}/contents/{path}", "--jq", ".content"], run)
        files.append((path, base64.b64decode(raw).decode("utf-8")))
    return files


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


def collect(repo: str, *, warn_gb: float, clean: bool = False, local_root: Path | None = None,
            run=subprocess.run, now=None, log=print) -> dict:
    branch = default_branch(repo, run)
    caches = cc.list_caches(f"{ORG}/{repo}", run)
    open_prs = cc.open_pull_requests(f"{ORG}/{repo}", run)
    stale = cc.select(caches, "stale", open_prs=open_prs, now=now)
    row = {"repo": repo, "default_branch": branch, **summarize(caches, branch), "stale": len(stale),
           "stale_bytes": cc.total_bytes(stale), "deleted": 0, "deleted_bytes": 0}
    if clean and stale:
        failed = cc.delete(f"{ORG}/{repo}", stale, run, log)
        row["deleted"] = len(stale) - failed
        row["deleted_bytes"] = row["stale_bytes"] if not failed else 0
    files = local_files(local_root / LOCAL_DIRS[repo]) if local_root else remote_files(repo, run)
    findings = scan(files)
    row["wl5"] = [f for f in findings if ":WL5 " in f or ":WL0 " in f]
    row["wl4"] = [f for f in findings if ":WL4 " in f]
    row["files"] = len(files)
    after = row["bytes"] - row["deleted_bytes"]
    row["red"] = [r for r, bad in ((f"cache {after / 1e9:.1f} GB > {warn_gb:g} GB (cap {CAP_GB:g})",
                                    after > warn_gb * 1e9),
                                   (f"{len(row['wl5'])} uncached external download(s)", bool(row["wl5"])))
                  if bad]
    return row


def print_table(rows: list[dict], unreadable: list[str], warn_gb: float, clean: bool, verbose: bool = False) -> None:
    red = [r for r in rows if r["red"]]
    print(f"CI hygiene (Actions cache vs {CAP_GB:g} GB cap, RED above {warn_gb:g} GB; external downloads): "
          f"{len(red)} red of {len(rows)} repos")
    for r in rows:
        refs = ", ".join(f"{k} {v / 1e9:.2f}" for k, v in sorted(r["by_ref"].items(), key=lambda kv: -kv[1]))
        mark = "RED " if r["red"] else "    "
        print(f"{mark}{r['repo']:<20} {r['bytes'] / 1e9:5.2f} GB in {r['entries']:>3} caches ({refs or 'none'}); "
              f"stale {r['stale']} ({r['stale_bytes'] / 1e9:.2f} GB)"
              + (f", deleted {r['deleted']}" if clean else "") + f"; {r['files']} workflow/action files scanned")
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
    a = ap.parse_args(argv)
    rows, unreadable = [], []
    quiet = (lambda m: None) if a.json else print
    for repo in a.repos:
        try:
            rows.append(collect(repo, warn_gb=a.warn_gb, clean=a.clean, local_root=a.local_root, run=run, now=now,
                                log=quiet))
        except (cc.GhError, json.JSONDecodeError, ValueError, OSError, subprocess.TimeoutExpired):
            unreadable.append(repo)
    if a.json:
        print(json.dumps({"rows": rows, "red": sum(bool(r["red"]) for r in rows), "unreadable": unreadable},
                         indent=1))
    else:
        print_table(rows, unreadable, a.warn_gb, a.clean, a.verbose)
    if any(r["red"] for r in rows):
        return 1
    return 2 if unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
