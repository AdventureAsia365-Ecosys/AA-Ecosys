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
  * WL8 (RED, ADR 0021 decision 2.3): every third-party `uses:` of the workflows and composite actions, and every
    `uses:` inside a third-party composite action they call (read at the pinned SHA, followed 3 levels deep), against
    tools/github/actions-allowlist.txt, the record of the org Actions allow-list. S273: enabling the allow-list with
    the direct `uses:` only turned Docker Build Check red in every repo (trivy-action runs aquasecurity/setup-trivy).

    python3 tools/github/ci_hygiene.py                  # table; RED lines go into the opening status block
    python3 tools/github/ci_hygiene.py --json
    python3 tools/github/ci_hygiene.py --clean          # delete the stale pull request / merge-queue caches
    python3 tools/github/ci_hygiene.py --local-root .   # scan local checkouts instead of the default branches
    python3 tools/github/ci_hygiene.py --retention-scan .   # WL7 only, one checkout, GitHub warning annotations

Reads use the local `gh` login by hand, the aa-ecosys-ci-bot token (Actions read) in the root CI hygiene workflow, which
turns the --json report into one issue per finding type (tools/github/hygiene_issues.py, ADR 0021 decision 5 layer 3).
A token that cannot read a repo's Actions caches (HTTP 403) does not make the repo unreadable: its row carries
`cache_error` and its workflows are still scanned. Exit: 0 green | 1 RED (a repo over --warn-gb, default 8 GB, a WL5
or WL8 finding, or an unknown public repository) | 2 a repo unreadable. --retention-scan always exits 0 (warn mode).
"""
from __future__ import annotations

import argparse
import base64
import fnmatch
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

import yaml

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


# --- WL8: the org Actions allow-list, nested composite actions included --------------------------------------------

ALLOWLIST = Path(__file__).resolve().with_name("actions-allowlist.txt")
GITHUB_OWNED = frozenset({"actions", "github"})   # allowed by the policy itself ("allow actions created by GitHub")
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)")
NESTED_DEPTH = 3


def load_allowlist(path: Path = ALLOWLIST) -> list[str] | None:
    """The allow-list patterns; None when the file is missing (WL8 is then skipped, not failed)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def is_third_party(ref: str) -> bool:
    """A `uses:` the allow-list governs: a remote action outside GitHub's own orgs (not ./local, not docker://)."""
    if ref.startswith(("./", "../", "docker://")) or "@" not in ref:
        return False
    return ref.split("/", 1)[0].lower() not in GITHUB_OWNED


def allowed(ref: str, patterns: list[str]) -> bool:
    """GitHub's pattern semantics: `*` matches anything, a pattern names the full action path (`owner/repo@*` does not
    cover `owner/repo/sub@v1`), a pattern without `@` covers every ref of that path."""
    if not is_third_party(ref):
        return True
    path = ref.split("@", 1)[0]
    return any(fnmatch.fnmatchcase(ref, p) if "@" in p else fnmatch.fnmatchcase(path, p) for p in patterns)


def uses_of(text: str) -> list[tuple[int, str]]:
    """(line number, ref) of every `uses:` line; commented-out lines are skipped."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        m = USES.match(line)
        if m:
            out.append((i, m.group(1)))
    return out


def composite_uses(text: str | None) -> list[str]:
    """The `uses:` of a composite action's steps, whatever their `if:` (GitHub resolves them all at job set-up); a
    node / docker action has none."""
    try:
        doc = yaml.safe_load(text or "") or {}
    except yaml.YAMLError:
        return []
    runs = doc.get("runs") if isinstance(doc, dict) else None
    if not isinstance(runs, dict) or str(runs.get("using", "")).lower() != "composite":
        return []
    return [str(s["uses"]) for s in runs.get("steps") or [] if isinstance(s, dict) and s.get("uses")]


def remote_action(ref: str, run=subprocess.run) -> str | None:
    """action.yml (or action.yaml) of `owner/repo[/path]@sha`, read at that ref; None when unreadable."""
    path, at = ref.split("@", 1)
    owner, repo, *sub = path.split("/")
    prefix = "/".join(sub) + "/" if sub else ""
    for name in ("action.yml", "action.yaml"):
        try:
            raw = cc.gh(["api", f"repos/{owner}/{repo}/contents/{prefix}{name}?ref={at}", "--jq", ".content"], run)
            return base64.b64decode(raw).decode("utf-8")
        except (cc.GhError, ValueError, OSError, subprocess.TimeoutExpired):
            continue
    return None


def allowlist_findings(files: list[tuple[str, str]], patterns: list[str],
                       fetch: Callable[[str], str | None]) -> tuple[list[str], list[str]]:
    """WL8: third-party `uses:` (direct, or nested in a third-party composite action) that no pattern covers. Returns
    (findings, refs whose action file could not be read: their nested steps are unchecked, a warning, not RED)."""
    findings: list[str] = []
    unread: list[str] = []
    seen: dict[str, list[str]] = {}

    def nested(ref: str, depth: int) -> list[str]:
        if ref in seen:
            return seen[ref]
        seen[ref] = []
        found = []
        text = fetch(ref)
        if text is None:
            unread.append(ref)
        for inner in composite_uses(text):
            if not is_third_party(inner):
                continue
            if not allowed(inner, patterns):
                found.append(inner)
            if depth < NESTED_DEPTH:
                found += nested(inner, depth + 1)
        seen[ref] = found
        return found

    for path, text in files:
        for line, ref in uses_of(text):
            if not is_third_party(ref):
                continue
            if not allowed(ref, patterns):
                findings.append(f"{path}:{line}:WL8 {ref} is not on the org Actions allow-list "
                                f"(tools/github/actions-allowlist.txt)")
            for inner in dict.fromkeys(nested(ref, 1)):
                findings.append(f"{path}:{line}:WL8 {ref.split('@')[0]} runs {inner} inside itself (composite "
                                f"action), not on the org Actions allow-list: add '{inner.split('@')[0]}@*' to "
                                f"tools/github/actions-allowlist.txt and the org setting")
    return findings, unread


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
            run=subprocess.run, now=None, log=print, allowlist: list[str] | None = None,
            fetch: Callable[[str], str | None] | None = None) -> dict:
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
    patterns = load_allowlist() if allowlist is None else allowlist
    if patterns is None:
        row["wl8"], row["wl8_unread"] = [], ["tools/github/actions-allowlist.txt missing: WL8 skipped"]
    else:
        row["wl8"], row["wl8_unread"] = allowlist_findings(files, patterns, fetch or (lambda r: remote_action(r, run)))
    row["files"] = len(files)
    after = row["bytes"] - row["deleted_bytes"]
    row["red"] = [r for r, bad in ((f"cache {after / 1e9:.1f} GB > {warn_gb:g} GB (cap {CAP_GB:g})",
                                    after > warn_gb * 1e9),
                                   (f"{len(row['wl5'])} uncached external download(s)", bool(row["wl5"])),
                                   (f"{len(row['wl8'])} action(s) outside the org Actions allow-list (WL8)",
                                    bool(row["wl8"])))
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
        for f in r["wl5"] + r.get("wl8", []):
            print(f"     RED {f}")
        for ref in r.get("wl8_unread", []):
            print(f"     ??? WL8 could not read {ref} (its nested actions are unchecked)")
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
