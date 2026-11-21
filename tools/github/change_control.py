"""Change control in the merge gate: a risky PR needs a human approval (AA-1162, S286 decision D4, skill aa-ship §1).

The switch and the lists live in tools/github/change_control.json (next to this file), changed only through a root PR
so every switch is reviewed and in git history. OFF (today) = the merge tools behave exactly as before: no extra
GitHub read, no refusal. ON = before a merge, ship_merge.merge_one reads the PR's labels, author, changed files and
reviews, and refuses (exit 4) a risky PR that has no APPROVED review on its current head from a human reviewer:

- risky: a label in risky_labels, or a changed file (not matching ignore_paths) matching risky_paths; a renamed file
  counts with its old path too (renaming a workflow to a .md file is risky); the merge tools themselves (tools/github,
  tools/workflows) are risky paths, so the rule cannot be edited away by a PR it does not gate; a PR by an exempt
  author (the CI bot's migration copies, already approved in their app PR) is not risky;
- human: a reviewer whose GitHub user type is "User" (an App such as aa-agent is "Bot", so its comment review from
  post_agent_review.py never counts), not the PR author, in approvers (required while ON: the tools refuse an empty
  list), and with repo access (author_association OWNER, MEMBER or COLLABORATOR): the repos are public, and any
  signed-in GitHub user can submit an Approve or Request changes review on a public repo;
- approved: that reviewer's latest APPROVED / CHANGES_REQUESTED / DISMISSED review is APPROVED and on the head commit
  (a push after the approval asks for a new one); any human's latest CHANGES_REQUESTED refuses too.

There is no command-line override: switching it off again is a root PR, which is itself risky while ON.
Python stdlib only; every GitHub read goes through the Runner, so tests script it.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from ship_common import HERE, Runner, ShipError, _parse_paged_arrays, log, slug

CONFIG_PATH = HERE / "change_control.json"
DECISIVE = frozenset({"APPROVED", "CHANGES_REQUESTED", "DISMISSED"})
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
# Each changed file plus the path it was renamed from, so a rename is classified by both paths.
FILES_JQ = "[.[] | .filename, (.previous_filename // empty)]"
REVIEWS_JQ = ("[.[] | {user: {login: .user.login, type: .user.type}, author_association, state, commit_id, "
              "submitted_at}]")


def load_config(path: Path | None = None) -> dict:
    """The config file; a missing switch is OFF. An unreadable file refuses (exit 2): a broken file must not
    silently turn the control off once it was on."""
    p = path or CONFIG_PATH
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"require_human_approval_for_risky": False}
    except (OSError, json.JSONDecodeError) as e:
        raise ShipError(f"change control config {p} unreadable: {e}", 2) from e
    if not isinstance(data, dict):
        raise ShipError(f"change control config {p}: not a JSON object", 2)
    if not isinstance(data.get("require_human_approval_for_risky", False), bool):
        raise ShipError(f"change control config {p}: require_human_approval_for_risky must be true or false", 2)
    validate(data, f"change control config {p}")
    return data


def validate(cfg: dict, where: str = "change control config") -> None:
    """ON needs a non-empty approvers list: empty, any human with repo access could approve a risky PR."""
    if enabled(cfg) and not [a for a in (cfg.get("approvers") or []) if str(a).strip()]:
        raise ShipError(f"{where}: require_human_approval_for_risky is on but approvers is empty; list the tech "
                        "lead's GitHub login", 2)


def enabled(cfg: dict) -> bool:
    return cfg.get("require_human_approval_for_risky") is True


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pat) for pat in patterns)


def risky_reasons(cfg: dict, labels: list[str], files: list[str], author: str) -> list[str]:
    """Why the PR is risky ([] = not risky)."""
    if author and author in (cfg.get("exempt_authors") or []):
        return []
    wanted = {str(x).lower() for x in (cfg.get("risky_labels") or [])}
    out = [f"label '{lb}'" for lb in labels if lb.lower() in wanted]
    ignore = list(cfg.get("ignore_paths") or [])
    pats = list(cfg.get("risky_paths") or [])
    hits = [f for f in files if not _match(f, ignore) and _match(f, pats)]
    if hits:
        more = f" (+{len(hits) - 5} more)" if len(hits) > 5 else ""
        out.append(f"files {', '.join(hits[:5])}{more}")
    return out


def approval_state(reviews: list[dict], head: str, author: str, approvers: list[str]) -> tuple[list[str], list[str]]:
    """(humans who approved the head, humans whose latest decisive review requests changes)."""
    latest: dict[str, dict] = {}
    for r in reviews:
        user = r.get("user") or {}
        login = str(user.get("login") or "")
        state = str(r.get("state") or "").upper()
        if not login or user.get("type") != "User" or state not in DECISIVE:
            continue
        if str(r.get("author_association") or "").upper() not in TRUSTED_ASSOCIATIONS:
            continue  # public repo: a stranger's review neither approves nor blocks
        if login.lower() == author.lower().removeprefix("app/"):
            continue
        if approvers and login.lower() not in {str(a).lower() for a in approvers}:
            continue
        if login not in latest or str(r.get("submitted_at") or "") >= str(latest[login].get("submitted_at") or ""):
            latest[login] = r
    approved = [u for u, r in latest.items() if str(r.get("state")).upper() == "APPROVED" and r.get("commit_id") == head]
    blocked = [u for u, r in latest.items() if str(r.get("state")).upper() == "CHANGES_REQUESTED"]
    return sorted(approved), sorted(blocked)


def _pr_meta(runner: Runner, repo: str, n: int) -> tuple[list[str], str]:
    r = runner.run(["gh", "pr", "view", str(n), "-R", slug(repo), "--json", "labels,author"], timeout=60)
    if not r.ok:
        raise ShipError(f"{repo}#{n}: change control cannot read labels/author: {r.last_line()}", 2)
    try:
        data = json.loads(r.out or "{}")
    except json.JSONDecodeError as e:
        raise ShipError(f"{repo}#{n}: change control: labels/author not JSON ({e})", 2) from e
    labels = [str(x.get("name") or "") for x in (data.get("labels") or []) if isinstance(x, dict)]
    return labels, str((data.get("author") or {}).get("login") or "")


def _paged(runner: Runner, repo: str, n: int, what: str, jq: str) -> list:
    r = runner.run(["gh", "api", "--paginate", f"repos/{slug(repo)}/pulls/{n}/{what}?per_page=100", "--jq", jq],
                   timeout=60)
    if not r.ok:
        raise ShipError(f"{repo}#{n}: change control cannot list {what}: {r.last_line()}", 2)
    try:
        return _parse_paged_arrays(r.out)
    except json.JSONDecodeError as e:
        raise ShipError(f"{repo}#{n}: change control: {what} not JSON ({e})", 2) from e


def check(runner: Runner, repo: str, n: int, head: str, cfg: dict | None = None) -> None:
    """Raise ShipError(4) when the control is ON and the PR is risky without a human approval of its head.
    OFF: returns at once, reads nothing."""
    cfg = load_config() if cfg is None else cfg
    if not enabled(cfg):
        return
    validate(cfg)
    tag = f"{repo}#{n}"
    labels, author = _pr_meta(runner, repo, n)
    files = [str(x) for x in _paged(runner, repo, n, "files", FILES_JQ)]
    why = risky_reasons(cfg, labels, files, author)
    if not why:
        log(f"{tag}: change control ON, not a risky PR")
        return
    reviews = _paged(runner, repo, n, "reviews", REVIEWS_JQ)
    approved, blocked = approval_state(reviews, head, author, list(cfg.get("approvers") or []))
    if blocked:
        raise ShipError(f"{tag} REFUSED (change control): changes requested by {', '.join(blocked)}; "
                        f"risky: {'; '.join(why)}", 4)
    if not approved:
        raise ShipError(f"{tag} REFUSED (change control): risky PR ({'; '.join(why)}) needs an APPROVED review "
                        f"of head {head[:8]} by a human reviewer (the tech lead); agent reviews do not count", 4)
    log(f"{tag}: change control ON, risky PR approved by {', '.join(approved)} on head {head[:8]}")
