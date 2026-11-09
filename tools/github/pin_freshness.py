#!/usr/bin/env python3
"""Self-managed pin freshness (root ADR 0021 decision 5 layer 4, AA-1024, S273). Read-only; stdlib + gh CLI.

Dependabot moves the action SHAs and the pip / npm pins. It does not see the pins this org manages by hand, which S273
moved into cached, sha256-checked downloads (no per-job fetch from github.com). This tool finds them in the six repos
and compares each with the newest GitHub release of its upstream:

  * .github/actions/release-bin/pins.txt   "<tool> <version> <arch> <sha256> <url> <member>"  (syft, trivy,
                                            actionlint, oasdiff, ...; a URL outside GitHub releases is listed as
                                            "manual", e.g. the Session Manager plugin on S3)
  * .github/actions/lychee/pins.txt        "<version> <target> <sha256>"  (lycheeverse/lychee, tags lychee-vX.Y.Z)
  * requirements*.txt                      "<name> @ https://github.com/<o>/<r>/releases/download/<tag>/...#sha256="
                                            (the spaCy model wheel)
  * workflow / composite action files      "ghcr.io/<o>/<n>:<tag>@sha256:<digest>"  (the gitleaks image)

A pin is outdated when any repo carries a version lower than the newest non-draft, non-prerelease release whose tag
has the same prefix ("v", "lychee-v", "en_core_web_sm-"). The root CI hygiene workflow (weekly) turns the --json
report into one issue per outdated pin (tools/github/hygiene_issues.py sync --kind pins): never a PR, never a merge.
Moving a pin stays a person's or the orchestrator's change: every line of the tool, in every repo, in one wave, the
new sha256 checked against the release's own checksums file.

    python3 tools/github/pin_freshness.py                  # table
    python3 tools/github/pin_freshness.py --json
    python3 tools/github/pin_freshness.py --local-root .   # read local checkouts instead of the default branches

Exit: 0 every pin current | 1 an outdated pin | 2 a repo or an upstream unreadable (nothing outdated).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_hygiene as h  # noqa: E402

GH_RELEASE = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/releases/download/([^/\s]+)/")
REQ_PIN = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*@\s*(https://github\.com/\S+)")
IMAGE_PIN = re.compile(r"\bghcr\.io/([\w.-]+)/([\w.-]+):([\w.+-]+)@sha256:[0-9a-f]{64}")
PIN_FILES = {".github/actions/release-bin/pins.txt": "release-bin", ".github/actions/lychee/pins.txt": "lychee"}


def is_requirements(path: str) -> bool:
    return bool(re.search(r"(?:^|/)requirements[^/]*\.txt$", path)) and "node_modules/" not in path


def wants(path: str) -> bool:
    return path in PIN_FILES or is_requirements(path) or h.is_workflow_file(path)


def split_tag(tag: str) -> tuple[str, str]:
    """('lychee-v', '0.24.2') from 'lychee-v0.24.2': the prefix is everything before the first digit."""
    m = re.search(r"\d", tag)
    return (tag[:m.start()], tag[m.start():]) if m else (tag, "")


def vkey(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", version))


def parse_pins(repo: str, path: str, text: str) -> list[dict]:
    """The self-managed pins of one file: {key, upstream, prefix, version, where} (upstream None = not on GitHub)."""
    pins = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{repo}:{path}:{n}"
        kind = PIN_FILES.get(path)
        if kind == "release-bin":
            parts = line.split()
            if len(parts) < 5:
                continue
            m = GH_RELEASE.match(parts[4])
            if m:
                prefix, version = split_tag(m.group(3))
                pins.append({"key": parts[0], "upstream": f"{m.group(1)}/{m.group(2)}", "prefix": prefix,
                             "version": version, "where": where})
            else:
                pins.append({"key": parts[0], "upstream": None, "prefix": "", "version": parts[1], "where": where})
        elif kind == "lychee":
            parts = line.split()
            if parts:
                prefix, version = split_tag(f"lychee-{parts[0]}")
                pins.append({"key": "lychee", "upstream": "lycheeverse/lychee", "prefix": prefix, "version": version,
                             "where": where})
        elif is_requirements(path):
            m = REQ_PIN.match(line)
            r = GH_RELEASE.search(m.group(2)) if m else None
            if r:
                prefix, version = split_tag(r.group(3))
                pins.append({"key": m.group(1), "upstream": f"{r.group(1)}/{r.group(2)}", "prefix": prefix,
                             "version": version, "where": where})
        else:
            for m in IMAGE_PIN.finditer(line):
                prefix, version = split_tag(m.group(3))
                pins.append({"key": m.group(2), "upstream": f"{m.group(1)}/{m.group(2)}", "prefix": prefix,
                             "version": version, "where": where})
    return pins


def group(pins: list[dict]) -> list[dict]:
    """One entry per (key, upstream, prefix), with every version and every place it is pinned."""
    out: dict[tuple, dict] = {}
    for p in pins:
        g = out.setdefault((p["key"], p["upstream"], p["prefix"]),
                           {"key": p["key"], "upstream": p["upstream"], "prefix": p["prefix"], "versions": [],
                            "where": []})
        if p["version"] not in g["versions"]:
            g["versions"].append(p["version"])
        g["where"].append(p["where"])
    for g in out.values():
        g["versions"].sort(key=vkey)
    return sorted(out.values(), key=lambda g: g["key"])


IP_ALLOW_LIST = re.compile(r"IP allow list", re.I)


def _anonymous_get(url: str) -> list:
    """GET a public GitHub REST URL with no token (60 requests / hour per runner IP)."""
    import urllib.request
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "aa-ecosys-pin-freshness"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed https://api.github.com URL)
        return json.loads(resp.read().decode("utf-8"))


def latest_release(upstream: str, prefix: str, run=subprocess.run, fetch=_anonymous_get) -> tuple[str, str]:
    """(version, url) of the newest non-draft, non-prerelease release whose tag is <prefix><digit>...

    An upstream org with an IP allow list (aquasecurity, S274) refuses EVERY token from outside its list, the
    App's installation token included, even for a public repo; its public releases are then read with no token."""
    try:
        out = h.cc.gh(["api", f"repos/{upstream}/releases?per_page=100", "--jq",
                       '.[] | select((.draft | not) and (.prerelease | not)) | [.tag_name, .html_url] | @tsv'], run)
    except h.cc.GhError as exc:
        if not IP_ALLOW_LIST.search(str(exc)):
            raise
        rows = fetch(f"https://api.github.com/repos/{upstream}/releases?per_page=100")
        out = "\n".join(f"{r.get('tag_name', '')}\t{r.get('html_url', '')}" for r in rows
                        if isinstance(r, dict) and not r.get("draft") and not r.get("prerelease"))
    best = None
    for line in out.splitlines():
        tag, _, url = line.partition("\t")
        pre, version = split_tag(tag)
        if pre == prefix and version and (best is None or vkey(version) > vkey(best[0])):
            best = (version, url)
    if best is None:
        raise ValueError(f"no release of {upstream} with a tag {prefix}<version>")
    return best


def check(groups: list[dict], run=subprocess.run) -> list[dict]:
    seen: dict[tuple, tuple] = {}
    for g in groups:
        g.update(latest=None, latest_url=None, error=None)
        if not g["upstream"]:
            g["status"] = "manual"
            continue
        k = (g["upstream"], g["prefix"])
        try:
            if k not in seen:
                seen[k] = latest_release(g["upstream"], g["prefix"], run)
            g["latest"], g["latest_url"] = seen[k]
        except (h.cc.GhError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
            g["status"], g["error"] = "unknown", str(exc)[:200]
            continue
        g["status"] = "outdated" if any(vkey(v) < vkey(g["latest"]) for v in g["versions"]) else "current"
    return groups


def collect_pins(repos, *, local_root: Path | None = None, run=subprocess.run) -> tuple[list[dict], list[str]]:
    pins, unreadable = [], []
    for repo in repos:
        try:
            if local_root:
                root = local_root / h.LOCAL_DIRS[repo]
                files = [(str(p.relative_to(root)), p.read_text(encoding="utf-8"))
                         for p in sorted(root.rglob("*")) if p.is_file() and wants(str(p.relative_to(root)))
                         and ".git/" not in str(p.relative_to(root))]
            else:
                files = h.remote_files(repo, run, want=wants)
        except (h.cc.GhError, OSError, UnicodeDecodeError, ValueError, subprocess.TimeoutExpired):
            unreadable.append(repo)
            continue
        for path, text in files:
            pins += parse_pins(repo, path, text)
    return pins, unreadable


def main(argv: list[str] | None = None, run=subprocess.run) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--local-root", type=Path, help="read local checkouts under this workspace root")
    ap.add_argument("--repos", nargs="+", choices=h.REPOS, default=list(h.REPOS))
    a = ap.parse_args(argv)
    pins, unreadable = collect_pins(a.repos, local_root=a.local_root, run=run)
    groups = check(group(pins), run)
    if a.json:
        print(json.dumps({"pins": groups, "unreadable": unreadable}, indent=1))
    else:
        print(f"Self-managed pins: {sum(g['status'] == 'outdated' for g in groups)} outdated of {len(groups)}")
        for g in groups:
            mark = {"outdated": "OLD ", "unknown": "??? ", "manual": "man "}.get(g["status"], "    ")
            print(f"{mark}{g['key']:<24} {', '.join(g['versions']):<20} latest {g['latest'] or '-':<12} "
                  f"{g['upstream'] or 'not a GitHub release (check by hand)'}; {len(g['where'])} place(s)"
                  + (f"; {g['error']}" if g["error"] else ""))
        for repo in unreadable:
            print(f"??? {repo}: gh could not read its files")
    if any(g["status"] == "outdated" for g in groups):
        return 1
    return 2 if unreadable or any(g["status"] == "unknown" for g in groups) else 0


if __name__ == "__main__":
    sys.exit(main())
