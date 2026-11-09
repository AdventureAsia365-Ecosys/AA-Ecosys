#!/usr/bin/env python3
"""One GitHub issue per CI hygiene finding type (root ADR 0021 decision 5 layers 3 and 4, AA-1024, S273). Stdlib + gh.

Reads a JSON report and keeps the root repo's issues in step with it:

  --kind hygiene  report of `ci_hygiene.py --json` (daily): cache use above the threshold (8 GB of the 10 GB cap),
                  stale pull request / merge-queue caches (1 GB or more in a repo), uncached external downloads (WL5),
                  public repositories not in the known list, and "needs permission" when the token could not read a
                  repo's Actions caches.
  --kind pins     report of `pin_freshness.py --json` (weekly): one issue per outdated self-managed pin. An issue, never
                  a PR: moving a pin is a reviewed change in every repo that carries it (no auto-merge).

Each finding type has one open issue at most, found by its label (`ci-hygiene` / `ci-pin-update`) and the stable marker
at the end of its title (`[ci-hygiene:<type>]` / `[ci-pin:<key>]`). Per type the status is:
  present  open the issue, or update its title/body when the finding changed (no edit when nothing changed);
  absent   close the open issue with a comment ("cleared");
  unknown  leave the issue as it is (a repo, the org list or an upstream release could not be read: never close on a
           failed read).
Two open issues with one marker (a race): the oldest is kept, the others are closed as duplicates.

    python3 tools/github/hygiene_issues.py sync --kind hygiene --report hygiene.json --repo <org>/AA-Ecosys
    python3 tools/github/hygiene_issues.py sync --kind pins --report pins.json --repo <org>/AA-Ecosys --apply

Without --apply it prints the plan and writes nothing. The plan and a status table are printed as Markdown (the
workflow appends them to the run summary). Issue text is public: repo names, workflow paths, sizes and versions only.
Exit: 0 planned/applied | 1 a write failed | 2 the report cannot be read.

    python3 tools/github/hygiene_issues.py read-failures --kind pins --report pins.json

prints one line per failed read in the report (a repo, the org list or an upstream release) and exits 3 when there is
one, 0 when the report is complete, 2 when it cannot be read. The workflow turns the run red from this, not from the
check's exit code: both checks exit 1 for a finding before they look at failed reads, so a day with a finding and a
failed read would otherwise stay green. A cache list that returned HTTP 403 is not a failed read here: it has its own
"needs permission" issue.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ORG = "AdventureAsia365-Ecosys"
CAP_GB = 10.0
APP = "aa-ecosys-ci-bot"
ENVIRONMENT = "ci-hygiene"           # holds the App key; deployment branches: master only (the key can write elsewhere)
FOOTER = ("_Kept up to date by the root CI hygiene workflow (`.github/workflows/ci-hygiene.yml`, root ADR 0021 "
          "decision 5). It updates this issue while the finding is present and closes it when the finding clears._")
LAST_CHANGE = "_Last change:"
KINDS = {
    "hygiene": {"label": "ci-hygiene", "marker": "ci-hygiene", "color": "d93f0b",
                "description": "CI hygiene finding (root ADR 0021 decision 5 layer 3), kept by a workflow"},
    "pins": {"label": "ci-pin-update", "marker": "ci-pin", "color": "fbca04",
             "description": "A self-managed CI pin has a newer release (root ADR 0021 decision 5 layer 4)"},
}


@dataclass
class Finding:
    key: str
    status: str                      # present | absent | unknown
    title: str = ""
    lines: list[str] = field(default_factory=list)
    fix: str = ""
    note: str = ""


@dataclass
class Action:
    kind: str                        # create | update | close | keep | leave | duplicate
    key: str
    number: int | None = None
    title: str = ""
    body: str = ""
    comment: str = ""
    why: str = ""


def gb(n: float) -> str:
    return f"{n / 1e9:.2f} GB"


# --------------------------------------------------------------------------------------------- hygiene findings

def _unmeasured(rows: list[dict], unreadable: list[str], cache: bool) -> list[str]:
    """Repos whose data for a finding type was not read (the whole repo, or only its caches)."""
    return sorted([*unreadable, *([r["repo"] for r in rows if r.get("cache_error")] if cache else [])])


def _status(present: bool, unmeasured: list[str]) -> str:
    return "present" if present else ("unknown" if unmeasured else "absent")


def hygiene_findings(report: dict, *, stale_min_gb: float = 1.0, token_source: str = "unknown") -> dict:
    rows, unreadable = report.get("rows") or [], report.get("unreadable") or []
    warn_gb = float(report.get("warn_gb") or 8.0)
    out = {}

    missing = _unmeasured(rows, unreadable, cache=True)
    over = [r for r in rows if not r.get("cache_error") and r["bytes"] > warn_gb * 1e9]
    note = f"Not measured this run: {', '.join(missing)}." if missing else ""
    lines = []
    for r in over:
        refs = ", ".join(f"{k} {gb(v)}" for k, v in sorted(r["by_ref"].items(), key=lambda kv: -kv[1]))
        tops = "; ".join(f"`{t['family']}` {gb(t['bytes'])} in {t['entries']}" for t in r.get("top", [])[:3])
        lines.append(f"**{r['repo']}**: {gb(r['bytes'])} in {r['entries']} caches ({refs}). Largest: {tops}")
    out["cache-over-threshold"] = Finding(
        "cache-over-threshold", _status(bool(over), missing),
        f"Actions cache above {warn_gb:g} GB of the {CAP_GB:g} GB cap", lines,
        "Above 10 GB GitHub evicts the least recently used entries, which can be the default-branch caches every "
        "run restores. Find the largest key families above, check that only the default branch saves them (WL4), and "
        "run `python3 tools/github/ci_hygiene.py --clean` for pull request / merge-queue leftovers.", note)

    stale = [r for r in rows if not r.get("cache_error") and r["stale_bytes"] >= stale_min_gb * 1e9]
    out["stale-caches"] = Finding(
        "stale-caches", _status(bool(stale), missing),
        f"Stale pull request / merge-queue caches above {stale_min_gb:g} GB",
        [f"**{r['repo']}**: {r['stale']} stale caches, {gb(r['stale_bytes'])}" for r in stale],
        "Each repo's Cache cleanup workflow deletes these on pull request close and daily: check its latest runs. "
        "`python3 tools/github/ci_hygiene.py --clean` deletes them by hand (pull request / queue refs only).", note)

    gone = _unmeasured(rows, unreadable, cache=False)
    dl = [(r["repo"], f) for r in rows for f in r.get("wl5", [])]
    out["external-downloads"] = Finding(
        "external-downloads", _status(bool(dl), gone), "Uncached external downloads in CI (WL5)",
        [f"**{repo}**: `{f}`" for repo, f in dl],
        "A step that fetches a binary on every run fails when GitHub throttles release downloads. Use "
        "`./.github/actions/release-bin` (cached, sha256-pinned, authenticated fetch) or `./.github/actions/lychee`.",
        f"Not scanned this run: {', '.join(gone)}." if gone else "")

    na = [(r["repo"], f) for r in rows for f in r.get("wl8", [])]
    out["actions-not-allowed"] = Finding(
        "actions-not-allowed", _status(bool(na), gone), "Actions outside the org allow-list (WL8)",
        [f"**{repo}**: `{f}`" for repo, f in na],
        "The org Actions policy allows GitHub-owned actions plus `tools/github/actions-allowlist.txt`. An action that "
        "is not listed, or one that a listed composite action runs inside itself (trivy-action runs setup-trivy), "
        "fails the job at set-up. Add its line to the file and the same pattern to the org setting (org owner), or "
        "replace the action.",
        f"Not scanned this run: {', '.join(gone)}." if gone else "")

    org = report.get("org")
    if not org or org.get("error"):
        why = (org or {}).get("error") or "not run"
        out["unknown-public-repo"] = Finding("unknown-public-repo", "unknown", note=f"Org repository list unreadable: {why}")
    else:
        names = org.get("unknown_public") or []
        out["unknown-public-repo"] = Finding(
            "unknown-public-repo", "present" if names else "absent",
            "Public repository not in the known list",
            [f"**{n}** (https://github.com/{ORG}/{n})" for n in names],
            "On GitHub Free members can still create public repositories (ADR 0021 decision 2.1). The org owner checks "
            "each one: delete it or make it private if it is a mistake; if it is meant to stay, add it to `REPOS` in "
            "`tools/github/ci_hygiene.py` and turn on secret scanning and push protection for it.")

    blocked = [r["repo"] for r in rows if r.get("cache_error")]
    if blocked:
        grant = needs_permission_fix(token_source, blocked)
        out["needs-permission"] = Finding(
            "needs-permission", "present", "CI hygiene cannot read Actions caches (needs permission)",
            [f"**{repo}**: the token cannot read its Actions caches (HTTP 403)" for repo in blocked],
            grant, f"Token used this run: {token_source}.")
    else:
        out["needs-permission"] = Finding("needs-permission", "unknown" if not rows else "absent")
    return out


def needs_permission_fix(token_source: str, repos: list[str]) -> str:
    steps = []
    if token_source in ("github-token", "unknown"):
        steps.append(f"In the root repo create the environment `{ENVIRONMENT}` with deployment branches limited to "
                     f"`master`, store the secret `AA_CI_BOT_PRIVATE_KEY` in that environment (never at repo level) "
                     f"and set the repo variable `AA_CI_BOT_APP_ID` (GitHub App `{APP}`, docs/security/github-apps.md "
                     "part 5), so the workflow can mint an App token; the default `GITHUB_TOKEN` reads only this "
                     "repository's caches.")
    if token_source in ("github-token", "app", "unknown"):
        steps.append(f"App settings of `{APP}` → Permissions → Repository → **Actions: Read-only** → Save, then accept "
                     "the new permission on the org installation (Org settings → GitHub Apps → Configure → Review "
                     "request). The workflow mints its token with only Actions, Contents and Pull requests read.")
    steps.append(f"Install `{APP}` on every repo listed here ({', '.join(repos)}): Org settings → GitHub Apps → "
                 "Configure → Repository access.")
    return " ".join(f"{i}. {s}" for i, s in enumerate(steps, 1))


# ------------------------------------------------------------------------------------------------ pin findings

def pin_findings(report: dict) -> tuple[dict, bool]:
    """(findings by pin key, complete): complete is False when a repo was unreadable (a pin that vanished from the
    report then stays open instead of closing)."""
    out = {}
    for g in report.get("pins") or []:
        if g["status"] == "manual":
            continue
        key = re.sub(r"[^a-z0-9_.-]+", "-", g["key"].lower())
        if g["status"] == "unknown":
            out[key] = Finding(key, "unknown", note=g.get("error") or "")
            continue
        current = ", ".join(g["versions"])
        lines = [f"Pinned: **{current}**; newest release of `{g['upstream']}`: **{g['latest']}** ({g['latest_url']})"]
        lines += [f"`{w}`" for w in g["where"]]
        disagree = len(g["versions"]) > 1
        out[key] = Finding(
            key, "present" if g["status"] == "outdated" else "absent",
            f"Pinned tool update: {g['key']} {current} -> {g['latest']}", lines,
            "Read the release notes, then move every line of this pin in every repo listed, in one wave: new version, "
            "new sha256 checked against the release's own checksums file (never computed from a download alone), CI "
            "green in each repo before merge. No auto-merge."
            + (" The repos disagree on the version: bring them to one." if disagree else "")
            + (" A spaCy model's major.minor must match the pinned spaCy library." if "spacy-models" in g["upstream"]
               else ""))
    return out, not (report.get("unreadable") or [])


# ------------------------------------------------------------------------------------------- failed reads

def read_failures(report: dict, kind: str) -> list[str]:
    """What the report could not read, one line each (empty: complete). Decides the run colour (see the module doc)."""
    out = [f"{repo}: unreadable" for repo in report.get("unreadable") or []]
    if kind == "hygiene":
        org = report.get("org")
        if org is None:
            out.append("org repository list: not read")
        elif org.get("error"):
            out.append(f"org repository list: {org['error']}")
    else:
        out += [f"pin {g.get('key')}: upstream release unreadable ({g.get('error') or 'no detail'})"
                for g in report.get("pins") or [] if g.get("status") == "unknown"]
    return out


# ------------------------------------------------------------------------------------------------- planning

def title_for(f: Finding, marker: str) -> str:
    return f"{f.title} [{marker}:{f.key}]"


def body_for(f: Finding, marker: str) -> str:
    parts = [f"<!-- {marker}:{f.key} -->", f"**{f.title}**", "", *[f"- {line}" for line in f.lines]]
    if f.note:
        parts += ["", f.note]
    if f.fix:
        parts += ["", f"**What to do:** {f.fix}"]
    return "\n".join([*parts, "", FOOTER]).strip() + "\n"


def _core(body: str) -> str:
    return "\n".join(line for line in (body or "").replace("\r\n", "\n").splitlines()
                     if not line.startswith(LAST_CHANGE)).strip()


def key_of(title: str, marker: str) -> str | None:
    m = re.search(rf"\[{re.escape(marker)}:([^\]]+)\]\s*$", title or "")
    return m.group(1) if m else None


def plan(findings: dict, issues: list[dict], marker: str, *, complete: bool = True, run_url: str = "") -> list[Action]:
    by_key: dict[str, list[dict]] = {}
    for issue in sorted(issues, key=lambda i: i["number"]):
        k = key_of(issue.get("title", ""), marker)
        if k:
            by_key.setdefault(k, []).append(issue)
    stamp = f"\n{LAST_CHANGE} {run_url}_\n" if run_url else ""
    actions = []
    for key in sorted(set(findings) | set(by_key)):
        f, open_ = findings.get(key), by_key.get(key, [])
        keep = open_[0] if open_ else None
        for dup in open_[1:]:
            actions.append(Action("duplicate", key, dup["number"], comment=f"Duplicate of #{keep['number']} (same "
                                  f"marker `[{marker}:{key}]`); closed by the CI hygiene workflow."))
        if f is None:
            if keep and complete:
                actions.append(Action("close", key, keep["number"], why="no longer reported",
                                      comment="Closed: this finding type is no longer reported by the check"
                                      + (f" ({run_url})." if run_url else ".")))
            elif keep:
                actions.append(Action("leave", key, keep["number"], why="not in an incomplete report"))
            continue
        if f.status == "unknown":
            actions.append(Action("leave", key, keep["number"] if keep else None, why=f"unknown: {f.note}"[:200]))
        elif f.status == "absent":
            if keep:
                actions.append(Action("close", key, keep["number"], why="cleared",
                                      comment="Cleared: the latest CI hygiene run no longer finds this"
                                      + (f" ({run_url})." if run_url else ".")))
        else:
            title, body = title_for(f, marker), body_for(f, marker)
            if not keep:
                actions.append(Action("create", key, title=title, body=body + stamp, why="new finding"))
            elif keep.get("title") != title or _core(keep.get("body", "")) != _core(body):
                actions.append(Action("update", key, keep["number"], title=title, body=body + stamp,
                                      why="finding changed"))
            else:
                actions.append(Action("keep", key, keep["number"], why="unchanged"))
    return actions


# ------------------------------------------------------------------------------------------------ gh writes

def _gh(args: list[str], run, stdin: str | None = None) -> subprocess.CompletedProcess:
    return run(["gh", *args], input=stdin, capture_output=True, text=True, timeout=120)


def list_open(repo: str, label: str, run=subprocess.run) -> list[dict]:
    proc = _gh(["issue", "list", "--repo", repo, "--label", label, "--state", "open", "--limit", "200",
                "--json", "number,title,body"], run)
    if proc.returncode != 0:
        if "not found" in (proc.stderr or "").lower() and "label" in (proc.stderr or "").lower():
            return []
        raise RuntimeError(f"gh issue list: {(proc.stderr or '').strip()[:300]}")
    return json.loads(proc.stdout or "[]")


def apply(actions: list[Action], repo: str, kind: str, run=subprocess.run, log=print) -> int:
    meta = KINDS[kind]
    writes = [a for a in actions if a.kind in ("create", "update", "close", "duplicate")]
    failed = 0
    if any(a.kind == "create" for a in writes):
        proc = _gh(["label", "create", meta["label"], "--repo", repo, "--color", meta["color"], "--description",
                    meta["description"], "--force"], run)
        if proc.returncode != 0:
            log(f"- label {meta['label']}: {(proc.stderr or '').strip()[:200]}")
    for a in writes:
        if a.kind == "create":
            cmd = ["issue", "create", "--repo", repo, "--title", a.title, "--label", meta["label"], "--body-file", "-"]
            proc = _gh(cmd, run, a.body)
        elif a.kind == "update":
            proc = _gh(["issue", "edit", str(a.number), "--repo", repo, "--title", a.title, "--body-file", "-"], run,
                       a.body)
        else:
            reason = "not planned" if a.kind == "duplicate" else "completed"
            proc = _gh(["issue", "close", str(a.number), "--repo", repo, "--reason", reason, "--comment", a.comment],
                       run)
        if proc.returncode != 0:
            failed += 1
            log(f"- FAILED {a.kind} {a.key}: {(proc.stderr or '').strip()[:200]}")
        elif a.kind == "create":
            log(f"- opened {a.key}: {(proc.stdout or '').strip()}")
    return failed


def summary(findings: dict, actions: list[Action], kind: str, applied: bool) -> str:
    out = [f"### CI hygiene issues ({kind}){'' if applied else ' - plan only, nothing written'}", "",
           "| Finding | Status | Issue action |", "|---|---|---|"]
    acts = {a.key: a for a in actions if a.kind != "duplicate"}
    for key in sorted(set(findings) | set(acts)):
        f, a = findings.get(key), acts.get(key)
        status = f.status if f else "not reported"
        what = "-" if not a else f"{a.kind}" + (f" #{a.number}" if a.number else "") + (f" ({a.why})" if a.why else "")
        out.append(f"| {key} | {status} | {what} |")
    dups = [a for a in actions if a.kind == "duplicate"]
    out += [f"- duplicate #{a.number} of {a.key} closed" for a in dups]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None, run=subprocess.run) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="open / update / close the issues from a report")
    s.add_argument("--kind", choices=sorted(KINDS), required=True)
    s.add_argument("--report", type=Path, required=True)
    s.add_argument("--repo", default=f"{ORG}/AA-Ecosys")
    s.add_argument("--apply", action="store_true", help="write the issues (default: print the plan)")
    s.add_argument("--stale-min-gb", type=float, default=1.0,
                   help="stale caches below this per repo are no finding (clean-ups leave a few queue entries)")
    s.add_argument("--token-source", default="unknown", choices=["app+actions", "app", "github-token", "unknown"])
    s.add_argument("--run-url", default="")
    r = sub.add_parser("read-failures", help="list the failed reads in a report; exit 3 when there is one")
    r.add_argument("--kind", choices=sorted(KINDS), required=True)
    r.add_argument("--report", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        report = json.loads(a.report.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("not a JSON object")
    except (OSError, ValueError) as exc:
        print(f"cannot read the report {a.report}: {exc}", file=sys.stderr)
        return 2
    if a.cmd == "read-failures":
        failures = read_failures(report, a.kind)
        for line in failures:
            print(line)
        return 3 if failures else 0
    meta = KINDS[a.kind]
    if a.kind == "hygiene":
        findings, complete = hygiene_findings(report, stale_min_gb=a.stale_min_gb, token_source=a.token_source), True
    else:
        findings, complete = pin_findings(report)
    try:
        issues = list_open(a.repo, meta["label"], run)
    except (RuntimeError, json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"cannot list the open issues: {exc}", file=sys.stderr)
        return 1
    actions = plan(findings, issues, meta["marker"], complete=complete, run_url=a.run_url)
    failed = apply(actions, a.repo, a.kind, run) if a.apply else 0
    print(summary(findings, actions, a.kind, a.apply))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
