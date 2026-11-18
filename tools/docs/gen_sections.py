#!/usr/bin/env python3
"""Generated blocks inside hand-written docs pages, rendered from one facts snapshot (AA-1132 A2).

The S283 docs audit found the same facts (which account serves the chat models, which ECS services run) copied by hand
into dozens of pages, each copy drifting on its own. A page now holds such a fact as a marked block that this tool
renders; prose around it explains "why" and never repeats the numbers and names:

    <!-- gen:ecs-services -->
    (rendered Markdown: never edit by hand)
    <!-- /gen -->

A block renders from `docs/generated/facts.snapshot.json` only, so `--check` is deterministic. The snapshot is collected
from files that are already in this repo, never from a live AWS call:

  docs/catalogue/platform.yaml          decisions people make (account roles, LLM route order, app tags); labels only
  docs/generated/inventory.md           the Terraform-state resource inventory AA-CIS-Infra Docs Gen commits here (ECS)
  docs/architecture/db-schema-reference.md  the live schema dump (DB Schema Dump bot PR): latest migration per owner

Two more groups come from outside this repo and are stored in the snapshot when collected (AA-1132 A3):

  repos            app versions, job kinds, backup days, workflow names, read statically from the five other repos
                   (repo_facts.py) with --repos-root <workspace> [--repos-ref origin/main]
  required_checks  the required status checks of each repo's default branch, read through `gh api` with --github
                   (classic branch protection or rulesets; public repos, read only)

Without those options --write keeps the stored values, so a docs PR never needs the other repos or the GitHub API.

Blocks (BLOCKS below; add one by adding a renderer and its facts):

  accounts           the AWS accounts by label: what each holds, whether it serves chat models, its Terraform root
  llm-route-order    the provider order per model family
  ecs-services       the ECS cluster and its services, with the app that owns each
  latest-migrations  the latest migration applied on Dev per owner (live schema dump)
  app-versions       each app's release version (release-please)
  job-kinds-cis, job-kinds-booking, job-kinds-crm, job-kinds-tripplanner
                     the registered job kinds of each owner job table with their limits and deploy-gate flags
  required-checks    the required status checks per repo
  backup-days        the RDS backup windows (point-in-time recovery, the longest a backup copy may live)

Commands:

  --check   exit 1 when a block differs from its render of the committed snapshot, a block name is unknown or a
            marker is unbalanced, the snapshot or platform.yaml holds an account ID, ARN or e-mail address, or the
            snapshot no longer matches platform.yaml. When only a collected source moved on (the inventory or the
            schema dump of a nightly bot PR, which must stay green to merge itself; the other repos with
            --repos-root; GitHub with --github) it is a warning: run --write in the next docs PR (the session close
            step runs it with the workspace, skill/aa-session).
  --write   collect the snapshot from its sources, then rewrite every block.
  --list    print each block and the page it is on.

Public repo (masking): account IDs, ARNs, e-mail addresses and profiles never go into platform.yaml or the snapshot;
the account map with IDs stays in docs/onboarding.md (owner tier). Journals (sessions, audits, notes, backlog, research,
archive, Linear export) are never scanned, and a marker inside a fenced code block is text, not a block.

Run: python tools/docs/gen_sections.py --check   (PyYAML, tools/docs/requirements.txt)
     python tools/docs/gen_sections.py --write --repos-root ../.. --repos-ref origin/main --github   (workspace)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path

import yaml

import repo_facts
from check_docs_text import RESOURCE_PATTERNS
from docslib import REPO_ROOT, list_markdown

SCHEMA = "aa1132-facts/2"
PLATFORM = "docs/catalogue/platform.yaml"
INVENTORY = "docs/generated/inventory.md"
SCHEMA_REF = "docs/architecture/db-schema-reference.md"
ORG = "AdventureAsia365-Ecosys"
CHECK_REPOS = {"AA-Ecosys": "master", "AA-CIS-App": "main", "AA-Booking": "main", "AA-Partner": "main",
               "AA-TripPlanner-Web": "main", "AA-CIS-Infra": "main"}
OWNER_PREFIX = {"CIS": "", "TripPlanner": "tp-", "Booking": "bk-", "CRM": "crm-"}
SNAPSHOT = "docs/generated/facts.snapshot.json"
GENERATOR = "tools/docs/gen_sections.py"
SCAN_ROOTS = ["docs", "skill", ".claude", ".kiro/steering", "README.md"]
SKIP_PREFIXES = ("docs/sessions/", "docs/audits/", "docs/implementation-notes/", "docs/backlog/", "docs/research/",
                 "docs/calib/", "docs/backups/", "docs/archive/", "docs/linear-export/", "docs/templates/")

OPEN = re.compile(r"^<!--\s*gen:([a-z0-9-]+)\s*-->\s*$")
CLOSE = re.compile(r"^<!--\s*/gen\s*-->\s*$")
ANY_MARKER = re.compile(r"<!--\s*/?gen\b")
FENCE = re.compile(r"^\s*(```|~~~)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
INVENTORY_ROW = re.compile(r"^\|\s*`(aws_ecs_service|aws_ecs_cluster)`\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|")
INVENTORY_APP = re.compile(r"^##\s+([a-z0-9_-]+)\s*$")
INVENTORY_SOURCE = re.compile(r"from AA-CIS-Infra@([0-9a-f]{7,40})")
SCHEMA_VERIFIED = re.compile(r"\*\*Verified:\*\*\s*(\d{4}-\d{2}-\d{2})")
SCHEMA_LATEST = re.compile(r"Latest migration per owner:\s*([^\n(]+)")
SCHEMA_OWNER = re.compile(r"([A-Za-z]+)\s+\*\*([a-z]*-?\d+)\*\*")


class GenError(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------- facts


def masking_problems(text: str) -> list[str]:
    """What must never be in a public facts file: account IDs, ARNs, resource IDs, e-mail addresses."""
    found = [label for label, pattern in RESOURCE_PATTERNS if pattern.search(text)]
    if re.search(r"(?<!\d)\d{12}(?!\d)", text) and "12-digit account ID" not in found:
        found.append("12-digit account ID")
    if EMAIL.search(text):
        found.append("e-mail address")
    return found


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _str(value, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GenError(f"{where}: expected a non-empty string")
    return " ".join(value.split())


def parse_platform(text: str) -> dict:
    """platform.yaml -> {"accounts", "llm_routes", "app_tags"}, shape-checked."""
    problems = masking_problems(text)
    if problems:
        raise GenError(f"{PLATFORM}: holds {', '.join(problems)} (public repo: labels only)")
    data = yaml.safe_load(text) or {}
    if data.get("version") != 1:
        raise GenError(f"{PLATFORM}: version must be 1")
    accounts = []
    for i, a in enumerate(data.get("accounts") or []):
        where = f"{PLATFORM} accounts[{i}]"
        if not isinstance(a, dict):
            raise GenError(f"{where}: expected a mapping")
        accounts.append({
            "label": _str(a.get("label"), where + ".label"),
            "name": _str(a.get("name"), where + ".name"),
            "holds": _str(a.get("holds"), where + ".holds"),
            "chat_models": _str(a.get("chat_models"), where + ".chat_models"),
            "terraform_root": a.get("terraform_root") if isinstance(a.get("terraform_root"), str) else None,
            "state": _str(a.get("state"), where + ".state"),
            "decision": _str(a.get("decision"), where + ".decision"),
        })
    if not accounts:
        raise GenError(f"{PLATFORM}: no accounts")
    routes = []
    for i, r in enumerate(data.get("llm_routes") or []):
        where = f"{PLATFORM} llm_routes[{i}]"
        if not isinstance(r, dict) or not isinstance(r.get("order"), list) or not r["order"]:
            raise GenError(f"{where}: expected family, order (a non-empty list) and note")
        routes.append({
            "family": _str(r.get("family"), where + ".family"),
            "order": [_str(x, where + ".order") for x in r["order"]],
            "note": " ".join(str(r.get("note") or "").split()),
        })
    if not routes:
        raise GenError(f"{PLATFORM}: no llm_routes")
    tags = data.get("app_tags") or {}
    if not isinstance(tags, dict) or not tags:
        raise GenError(f"{PLATFORM}: app_tags must map an inventory App tag to a repo name")
    return {
        "accounts": accounts,
        "llm_routes": routes,
        "llm_routes_decision": _str(data.get("llm_routes_decision"), f"{PLATFORM} llm_routes_decision"),
        "app_tags": {str(k): _str(v, f"{PLATFORM} app_tags.{k}") for k, v in tags.items()},
    }


def parse_inventory(text: str, app_tags: dict[str, str]) -> dict:
    """The ECS cluster and services of the Terraform-state inventory (AA-CIS-Infra Docs Gen), grouped by App tag."""
    app = None
    cluster = None
    services = []
    for line in text.splitlines():
        m = INVENTORY_APP.match(line)
        if m:
            app = m.group(1)
            continue
        m = INVENTORY_ROW.match(line)
        if not m:
            continue
        kind, name, address = m.group(1), m.group(2).strip(), m.group(3)
        if kind == "aws_ecs_cluster":
            cluster = name
        else:
            services.append({"name": name, "app_tag": app, "app": app_tags.get(app or "", app or "untagged"),
                             "address": address})
    if not services or not cluster:
        raise GenError(f"{INVENTORY}: no aws_ecs_cluster / aws_ecs_service rows (has the inventory format changed?)")
    src = INVENTORY_SOURCE.search(text)
    return {"cluster": cluster, "services": sorted(services, key=lambda s: (s["app"], s["name"])),
            "infra_commit": src.group(1)[:8] if src else None}


def parse_migrations(text: str) -> dict | None:
    """{"as_of", "owners": [{"owner", "latest"}]} from the "Verified" line of the live schema reference, or None."""
    verified = SCHEMA_VERIFIED.search(text)
    latest = SCHEMA_LATEST.search(text)
    if not verified or not latest:
        return None
    owners = [{"owner": o, "latest": v} for o, v in SCHEMA_OWNER.findall(latest.group(1))]
    return {"as_of": verified.group(1), "owners": owners} if owners else None


def gh_required_checks(repo: str, branch: str, runner=None) -> list[str]:
    """The required status check names of `repo`'s default branch: classic branch protection plus rulesets. Read only;
    `runner(args) -> stdout` is injectable for tests (default: the gh CLI)."""
    def run(args: list[str]) -> str:
        if runner is not None:
            return runner(args)
        return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout

    names: set[str] = set()
    classic = run(["api", f"repos/{ORG}/{repo}/branches/{branch}", "--jq",
                   ".protection.required_status_checks.contexts // [] | .[]"])
    names |= {line.strip() for line in classic.splitlines() if line.strip()}
    rules = run(["api", f"repos/{ORG}/{repo}/rules/branches/{branch}", "--jq",
                 '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'])
    names |= {line.strip() for line in rules.splitlines() if line.strip()}
    return sorted(names)


def collect_required_checks(runner=None) -> dict:
    out = {}
    for repo, branch in CHECK_REPOS.items():
        try:
            out[repo] = {"branch": branch, "checks": gh_required_checks(repo, branch, runner)}
        except (OSError, subprocess.CalledProcessError) as exc:
            raise GenError(f"required checks of {repo}: gh api failed ({exc})") from exc
    return out


def collect(root: Path = REPO_ROOT, previous: dict | None = None, repos: dict | None = None,
            required_checks: dict | None = None) -> dict:
    """The snapshot. `repos` (repo_facts.collect output) and `required_checks` replace the stored values when given;
    otherwise the values of `previous` (the committed snapshot) are kept. A repo whose facts did not change keeps its
    stored head (repo_facts.keep_heads), so a heads-only move rewrites neither the snapshot nor a page."""
    previous = previous or {}
    platform_text = (root / PLATFORM).read_text(encoding="utf-8")
    inventory_text = (root / INVENTORY).read_text(encoding="utf-8")
    platform = parse_platform(platform_text)
    schema_path = root / SCHEMA_REF
    migrations = parse_migrations(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else None
    return {
        "schema": SCHEMA,
        "generator": GENERATOR,
        "sources": {PLATFORM: _sha256(platform_text), INVENTORY: _sha256(inventory_text)},
        "accounts": platform["accounts"],
        "llm_routes": platform["llm_routes"],
        "llm_routes_decision": platform["llm_routes_decision"],
        "ecs": parse_inventory(inventory_text, platform["app_tags"]),
        "migrations": migrations if migrations is not None else previous.get("migrations"),
        "repos": repo_facts.keep_heads(repos, previous.get("repos")) if repos is not None else previous.get("repos"),
        "required_checks": required_checks if required_checks is not None else previous.get("required_checks"),
    }


def dumps(facts: dict) -> str:
    return json.dumps(facts, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def facts_masking_problems(facts: dict) -> list[str]:
    """masking_problems over every value a page can show (the source sha256 fingerprints are hex, not shown, and a
    64-character hash may hold a 12-digit run)."""
    return masking_problems(json.dumps({k: v for k, v in facts.items() if k != "sources"}, ensure_ascii=False))


def load_snapshot(root: Path = REPO_ROOT) -> dict:
    path = root / SNAPSHOT
    if not path.exists():
        raise GenError(f"{SNAPSHOT}: missing (run python {GENERATOR} --write)")
    facts = json.loads(path.read_text(encoding="utf-8"))
    problems = facts_masking_problems(facts)
    if problems:
        raise GenError(f"{SNAPSHOT}: holds {', '.join(problems)} (public repo)")
    if facts.get("schema") != SCHEMA:
        raise GenError(f"{SNAPSHOT}: schema is {facts.get('schema')!r}, expected {SCHEMA!r}")
    return facts


# -------------------------------------------------------------------------------------------------------- renders


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|")


def _code(text: str) -> str:
    return f"`{text}`"


def render_accounts(f: dict) -> str:
    lines = ["| Account | Name | Holds | Chat models | Terraform root (AA-CIS-Infra) | State | Decision |",
             "|---|---|---|---|---|---|---|"]
    for a in f["accounts"]:
        root = _code(a["terraform_root"]) if a["terraform_root"] else "none"
        lines.append(f"| {_cell(a['label'])} | {_cell(a['name'])} | {_cell(a['holds'])} | {_cell(a['chat_models'])} "
                     f"| {root} | {_cell(a['state'])} | {_cell(a['decision'])} |")
    lines += ["", "Labels only: account IDs and CLI profiles are in the account map of the onboarding page "
              "(owner tier), never in a repo page."]
    return "\n".join(lines)


def render_llm_route_order(f: dict) -> str:
    lines = ["| Model family | Route order (first to last) | Note |", "|---|---|---|"]
    for r in f["llm_routes"]:
        lines.append(f"| {_cell(r['family'])} | {_cell(' → '.join(r['order']))} | {_cell(r['note'] or '-')} |")
    lines += ["", f"Decision: {f['llm_routes_decision']}. The live routes per stage are in the "
              "[LLM routes table](generated/llm-routes.md) and CIS admin AI providers."]
    return "\n".join(lines)


def render_ecs_services(f: dict) -> str:
    ecs = f["ecs"]
    lines = [f"Cluster {_code(ecs['cluster'])}, {len(ecs['services'])} services:", "",
             "| Service | App |", "|---|---|"]
    for s in ecs["services"]:
        lines.append(f"| {_code(s['name'])} | {_cell(s['app'])} |")
    source = f" at AA-CIS-Infra {_code(ecs['infra_commit'])}" if ecs.get("infra_commit") else ""
    lines += ["", f"From the Terraform state{source} (resource inventory, AA-CIS-Infra Docs Gen)."]
    return "\n".join(lines)


NOT_COLLECTED = ("Not collected yet: run python tools/docs/gen_sections.py --write {opts} from the workspace "
                 "(skill/aa-session, session close).")


def _repos(f: dict) -> dict | None:
    return f.get("repos") if isinstance(f.get("repos"), dict) else None


def _yes(value) -> str:
    if value is None:
        return "?"
    return "**yes**" if value is True else ("no" if value is False else _cell(value))


def _num(value) -> str:
    return "?" if value is None else _cell(value)


def _collected_note(f: dict, repo: str) -> str:
    sha = ((_repos(f) or {}).get("collected_from") or {}).get(repo)
    return f"Read statically from {repo} main" + (f" at {_code(sha)}" if sha else "") + " (tools/docs/repo_facts.py)."


def render_latest_migrations(f: dict) -> str:
    m = f.get("migrations")
    if not m:
        return "No live schema dump found (docs/architecture/db-schema-reference.md)."
    lines = ["| Owner | Migration key | Latest applied on Dev |", "|---|---|---|"]
    for o in m["owners"]:
        prefix = OWNER_PREFIX.get(o["owner"], "")
        key = f"`{prefix}NNN`" if prefix else "`NNN`"
        lines.append(f"| {_cell(o['owner'])} | {key} | {_code(o['latest'])} |")
    lines += ["", f"From the live schema dump of {m['as_of']} ([DB schema reference]"
              "(architecture/db-schema-reference.md), refreshed by the DB Schema Dump bot PR). A new migration takes the "
              "next number on its owner's main; the owner list is in "
              "[schema ownership](database/schema-ownership.md)."]
    return "\n".join(lines)


def render_app_versions(f: dict) -> str:
    repos = _repos(f)
    if not repos or not repos.get("versions"):
        return NOT_COLLECTED.format(opts="--repos-root <workspace> --repos-ref origin/main")
    lines = ["| Repo | Release version |", "|---|---|"]
    for repo in sorted(repos["versions"]):
        v = repos["versions"][repo]
        lines.append(f"| {repo} | {_code(v) if v else '?'} |")
    shas = ", ".join(f"{r} {_code(s)}" for r, s in sorted((repos.get("collected_from") or {}).items())
                     if r in repos["versions"] and s)
    lines += ["", "From each repo's `.release-please-manifest.json` on main" + (f" ({shas})" if shas else "")
              + "; release-please raises it when its release PR merges."]
    return "\n".join(lines)


def _kinds(f: dict, repo: str) -> list[dict] | None:
    repos = _repos(f)
    if not repos:
        return None
    return (repos.get("job_kinds") or {}).get(repo)


def _unresolved_note(f: dict, repo: str) -> list[str]:
    bad = [u.split(" ", 1)[1] for u in (_repos(f) or {}).get("unresolved") or [] if u.startswith(repo + " ")]
    if not bad:
        return []
    return ["", "Registrations the static reader could not resolve (check the code): "
            + ", ".join(_code(b) for b in bad) + "."]


def render_job_kinds_cis(f: dict) -> str:
    kinds = _kinds(f, "AA-CIS-App")
    if kinds is None:
        return NOT_COLLECTED.format(opts="--repos-root <workspace> --repos-ref origin/main")
    lines = [f"{len(kinds)} kinds registered with `@job_kind` (`shared/jobs/registry.py`); a kind registered only when "
             "`JOB_TEST_KINDS` is on is not listed.", "",
             "| Kind | Code | Concurrency | Max attempts | Expected (s) | Background | Blocks deploys | Gate exempt |",
             "|---|---|---|---|---|---|---|---|"]
    for k in kinds:
        lines.append(f"| {_code(k['kind'])} | {_code(k['code'])} | {_num(k.get('concurrency'))} "
                     f"| {_num(k.get('max_attempts'))} | {_num(k.get('expected_seconds'))} | {_yes(k.get('background'))} "
                     f"| {_yes(k.get('deploy_blocking'))} | {_yes(k.get('deploy_gate_exempt'))} |")
    lines += ["", _collected_note(f, "AA-CIS-App")] + _unresolved_note(f, "AA-CIS-App")
    return "\n".join(lines)


def _render_table_kinds(f: dict, repo: str, source: str) -> str:
    kinds = _kinds(f, repo)
    if kinds is None:
        return NOT_COLLECTED.format(opts="--repos-root <workspace> --repos-ref origin/main")
    lines = [f"{len(kinds)} kinds in `{source}` (`EXPECTED_SECONDS`, `DEPLOY_BLOCKING_KINDS`, `DEPLOY_GATE_EXEMPT`, "
             "`TEST_KINDS`).", "",
             "| Kind | Expected (s) | Blocks deploys | Gate exempt | Test only |", "|---|---|---|---|---|"]
    for k in kinds:
        lines.append(f"| {_code(k['kind'])} | {_num(k.get('expected_seconds'))} | {_yes(k.get('deploy_blocking'))} "
                     f"| {_yes(k.get('deploy_gate_exempt'))} | {_yes(k.get('test_only'))} |")
    lines += ["", _collected_note(f, repo)] + _unresolved_note(f, repo)
    return "\n".join(lines)


def render_job_kinds_booking(f: dict) -> str:
    return _render_table_kinds(f, "AA-Booking", repo_facts.KINDS_FILES["AA-Booking"])


def render_job_kinds_crm(f: dict) -> str:
    return _render_table_kinds(f, "AA-Partner", repo_facts.KINDS_FILES["AA-Partner"])


def render_job_kinds_tripplanner(f: dict) -> str:
    kinds = _kinds(f, "AA-TripPlanner-Web")
    if kinds is None:
        return NOT_COLLECTED.format(opts="--repos-root <workspace> --repos-ref origin/main")
    lines = [f"{len(kinds)} kinds in `HANDLERS` of `{repo_facts.TP_HANDLER}`; `DAILY` = queued by the daily tick.", "",
             "| Kind | Daily | Max attempts |", "|---|---|---|"]
    for k in kinds:
        lines.append(f"| {_code(k['kind'])} | {_yes(k.get('daily'))} | {_num(k.get('max_attempts'))} |")
    lines += ["", _collected_note(f, "AA-TripPlanner-Web")] + _unresolved_note(f, "AA-TripPlanner-Web")
    return "\n".join(lines)


def render_required_checks(f: dict) -> str:
    rc = f.get("required_checks")
    if not rc:
        return NOT_COLLECTED.format(opts="--github")
    lines = ["| Repo | Branch | Required checks |", "|---|---|---|"]
    for repo in sorted(rc):
        checks = rc[repo].get("checks") or []
        shown = ", ".join(_code(c) for c in checks) if checks else "none"
        lines.append(f"| {repo} | {_code(rc[repo].get('branch', '?'))} | {shown} |")
    lines += ["", "Read from GitHub (branch protection and rulesets of the default branch) with "
              "`gen_sections.py --write --github`. A check skipped by a path filter counts as passed only where the "
              "workflow says so; the merge-queue repos run every required check in the queue."]
    return "\n".join(lines)


def render_backup_days(f: dict) -> str:
    b = (_repos(f) or {}).get("backup")
    if not b:
        return NOT_COLLECTED.format(opts="--repos-root <workspace> --repos-ref origin/main")
    lines = ["| Backup window (Dev RDS) | Days | Set in AA-CIS-Infra |", "|---|---|---|",
             f"| Automated backups, point-in-time recovery | {_num(b.get('rds_pitr_days'))} "
             f"| {_code(b.get('rds_pitr_source'))} (`backup_retention_period`) |",
             f"| Longest any backup copy may live (alarm above it) | {_num(b.get('copy_max_age_days'))} "
             f"| {_code(b.get('copy_max_age_source'))} (`rds_backup_copy_max_age_days`) |",
             "", _collected_note(f, "AA-CIS-Infra")]
    return "\n".join(lines)


BLOCKS = {
    "accounts": render_accounts,
    "llm-route-order": render_llm_route_order,
    "ecs-services": render_ecs_services,
    "latest-migrations": render_latest_migrations,
    "app-versions": render_app_versions,
    "job-kinds-cis": render_job_kinds_cis,
    "job-kinds-booking": render_job_kinds_booking,
    "job-kinds-crm": render_job_kinds_crm,
    "job-kinds-tripplanner": render_job_kinds_tripplanner,
    "required-checks": render_required_checks,
    "backup-days": render_backup_days,
}
# Links in a render are written relative to docs/; a page elsewhere gets them rewritten by depth (_relink).
LINK = re.compile(r"\]\((?!https?:|#|/)([^)\s]+)\)")


def _relink(text: str, page: str) -> str:
    here = posixpath.dirname(page) or "."
    return LINK.sub(lambda m: f"]({posixpath.relpath(posixpath.join('docs', m.group(1)), here)})", text)


def render(name: str, facts: dict, page: str = "docs/x.md") -> str:
    if name not in BLOCKS:
        raise GenError(f"unknown block gen:{name} (known: {', '.join(sorted(BLOCKS))})")
    return _relink(BLOCKS[name](facts), page)


# ---------------------------------------------------------------------------------------------------------- pages


def find_blocks(text: str, page: str) -> list[tuple[str, int, int]]:
    """(name, open line index, close line index) of every block; markers inside fenced code are text."""
    lines = text.split("\n")
    blocks = []
    fence = None
    current = None
    for i, line in enumerate(lines):
        m = FENCE.match(line)
        if m:
            if fence is None:
                fence = m.group(1)
            elif m.group(1) == fence:
                fence = None
            continue
        if fence is not None:
            continue
        o, c = OPEN.match(line), CLOSE.match(line)
        if o:
            if current is not None:
                raise GenError(f"{page}:{i + 1}: gen:{o.group(1)} opens inside gen:{current[0]} (no nesting)")
            current = (o.group(1), i)
        elif c:
            if current is None:
                raise GenError(f"{page}:{i + 1}: <!-- /gen --> without an open block")
            blocks.append((current[0], current[1], i))
            current = None
    if current is not None:
        raise GenError(f"{page}:{current[1] + 1}: gen:{current[0]} is never closed (<!-- /gen -->)")
    return blocks


def rewrite(text: str, page: str, facts: dict) -> str:
    lines = text.split("\n")
    for name, start, end in reversed(find_blocks(text, page)):
        body = render(name, facts, page).split("\n")
        lines[start + 1:end] = ["", *body, ""]
    return "\n".join(lines)


def pages(root: Path = REPO_ROOT) -> list[str]:
    return [p for p in list_markdown(SCAN_ROOTS, root) if not p.startswith(SKIP_PREFIXES)]


def _with_blocks(root: Path) -> list[tuple[str, str]]:
    out = []
    for page in pages(root):
        text = (root / page).read_text(encoding="utf-8")
        if ANY_MARKER.search(text):
            out.append((page, text))
    return out


def _without_heads(repos: dict | None) -> dict | None:
    """The repo facts without `collected_from` (the heads move on every merge; the facts may not)."""
    return None if repos is None else {k: v for k, v in repos.items() if k != "collected_from"}


def check(root: Path = REPO_ROOT, repos: dict | None = None,
          required_checks: dict | None = None) -> tuple[list[str], list[str]]:
    """(errors, warnings). `repos` / `required_checks`, when given, are compared with the snapshot (warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        facts = load_snapshot(root)
    except (GenError, ValueError) as exc:
        return [str(exc)], []
    try:
        fresh = collect(root, previous=facts, repos=repos, required_checks=required_checks)
    except (GenError, OSError) as exc:
        errors.append(str(exc))
        fresh = None
    if fresh is not None:
        for key in ("accounts", "llm_routes", "llm_routes_decision"):
            if fresh[key] != facts.get(key):
                errors.append(f"{SNAPSHOT}: `{key}` differs from {PLATFORM}; run python {GENERATOR} --write")
        if fresh["ecs"] != facts.get("ecs"):
            warnings.append(f"{SNAPSHOT}: the ECS services differ from {INVENTORY} (Infra Docs Gen moved on); run "
                            f"python {GENERATOR} --write in the next docs PR")
        if fresh.get("migrations") != facts.get("migrations"):
            warnings.append(f"{SNAPSHOT}: the latest migrations differ from {SCHEMA_REF} (a schema dump bot PR moved "
                            f"on); run python {GENERATOR} --write in the next docs PR")
        if repos is not None and _without_heads(repos) != _without_heads(facts.get("repos")):
            changed = sorted(k for k in set(repos) | set(facts.get("repos") or {}) if k != "collected_from"
                             and repos.get(k) != (facts.get("repos") or {}).get(k))
            warnings.append(f"{SNAPSHOT}: the repo facts ({', '.join(changed)}) differ from the repos on main; run "
                            f"python {GENERATOR} --write --repos-root <workspace> --repos-ref origin/main")
        if required_checks is not None and required_checks != facts.get("required_checks"):
            warnings.append(f"{SNAPSHOT}: the required checks differ from GitHub; run python {GENERATOR} --write "
                            "--github")
    for page, text in _with_blocks(root):
        try:
            if rewrite(text, page, facts) != text:
                names = ", ".join(sorted({n for n, _, _ in find_blocks(text, page)}))
                errors.append(f"{page}: generated block(s) {names} differ from the facts snapshot; "
                              f"run python {GENERATOR} --write (never edit a block by hand)")
        except GenError as exc:
            errors.append(str(exc))
    return errors, warnings


def write(root: Path = REPO_ROOT, repos: dict | None = None, required_checks: dict | None = None) -> list[str]:
    try:
        previous = json.loads((root / SNAPSHOT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = {}
    facts = collect(root, previous=previous, repos=repos, required_checks=required_checks)
    text = dumps(facts)
    problems = facts_masking_problems(facts)
    if problems:
        raise GenError(f"{SNAPSHOT}: would hold {', '.join(problems)}")
    (root / SNAPSHOT).write_text(text, encoding="utf-8")
    changed = [SNAPSHOT]
    for page, old in _with_blocks(root):
        new = rewrite(old, page, facts)
        if new != old:
            (root / page).write_text(new, encoding="utf-8")
            changed.append(page)
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--list", action="store_true")
    ap.add_argument("--repos-root", help="workspace holding apps/<repo> and infra/AA-CIS-Infra (repo facts, A3)")
    ap.add_argument("--repos-ref", help="read each repo at this git ref (e.g. origin/main) instead of its working tree")
    ap.add_argument("--github", action="store_true", help="read the required checks through gh api (read only)")
    ap.add_argument("--root", default=str(REPO_ROOT), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    root = Path(args.root)
    repos = required = None
    try:
        if args.repos_root and not args.list:
            readers = repo_facts.readers_for(Path(args.repos_root), args.repos_ref)
            missing = [r for r, rd in readers.items() if not rd.exists()]
            if missing:
                raise GenError(f"--repos-root {args.repos_root}: missing {', '.join(missing)}")
            repos = repo_facts.collect(readers)
        if args.github and not args.list:
            required = collect_required_checks()
    except (GenError, OSError, subprocess.CalledProcessError) as exc:
        print(f"::error title=Generated docs blocks::{exc}")
        return 1
    if args.list:
        for page, text in _with_blocks(root):
            for name, start, _ in find_blocks(text, page):
                print(f"{page}:{start + 1}: gen:{name}")
        return 0
    if args.write:
        try:
            changed = write(root, repos, required)
        except GenError as exc:
            print(f"::error title=Generated docs blocks::{exc}")
            return 1
        print("gen_sections: wrote " + ", ".join(changed))
        return 0
    errors, warnings = check(root, repos, required)
    for w in warnings:
        print(f"::warning title=Generated docs blocks::{w}")
    for e in errors:
        print(f"::error title=Generated docs blocks::{e}")
    blocks = sum(len(find_blocks(t, p)) for p, t in _with_blocks(root)) if not errors else 0
    if not errors:
        print(f"gen_sections: {blocks} generated blocks match {SNAPSHOT}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
