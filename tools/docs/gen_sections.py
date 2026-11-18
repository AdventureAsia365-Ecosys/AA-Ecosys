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

  docs/catalogue/platform.yaml   decisions people make (account roles, LLM route order, app tags); labels only
  docs/generated/inventory.md    the Terraform-state resource inventory AA-CIS-Infra Docs Gen commits here (ECS)

Blocks (BLOCKS below; add one by adding a renderer and its facts):

  accounts           the AWS accounts by label: what each holds, whether it serves chat models, its Terraform root
  llm-route-order    the provider order per model family
  ecs-services       the ECS cluster and its services, with the app that owns each

Commands:

  --check   exit 1 when a block differs from its render of the committed snapshot, a block name is unknown or a
            marker is unbalanced, the snapshot or platform.yaml holds an account ID, ARN or e-mail address, or the
            snapshot no longer matches platform.yaml. When only the inventory moved on (the nightly Infra Docs Gen PR,
            which must stay green to merge itself) it is a warning: run --write in the next docs PR.
  --write   collect the snapshot from its sources, then rewrite every block.
  --list    print each block and the page it is on.

Public repo (masking): account IDs, ARNs, e-mail addresses and profiles never go into platform.yaml or the snapshot;
the account map with IDs stays in docs/onboarding.md (owner tier). Journals (sessions, audits, notes, backlog, research,
archive, Linear export) are never scanned, and a marker inside a fenced code block is text, not a block.

Run: python tools/docs/gen_sections.py --check   (PyYAML, tools/docs/requirements.txt)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path

import yaml

from check_docs_text import RESOURCE_PATTERNS
from docslib import REPO_ROOT, list_markdown

SCHEMA = "aa1132-facts/1"
PLATFORM = "docs/catalogue/platform.yaml"
INVENTORY = "docs/generated/inventory.md"
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


def collect(root: Path = REPO_ROOT) -> dict:
    platform_text = (root / PLATFORM).read_text(encoding="utf-8")
    inventory_text = (root / INVENTORY).read_text(encoding="utf-8")
    platform = parse_platform(platform_text)
    return {
        "schema": SCHEMA,
        "generator": GENERATOR,
        "sources": {PLATFORM: _sha256(platform_text), INVENTORY: _sha256(inventory_text)},
        "accounts": platform["accounts"],
        "llm_routes": platform["llm_routes"],
        "llm_routes_decision": platform["llm_routes_decision"],
        "ecs": parse_inventory(inventory_text, platform["app_tags"]),
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


BLOCKS = {
    "accounts": render_accounts,
    "llm-route-order": render_llm_route_order,
    "ecs-services": render_ecs_services,
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


def check(root: Path = REPO_ROOT) -> tuple[list[str], list[str]]:
    """(errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        facts = load_snapshot(root)
    except (GenError, ValueError) as exc:
        return [str(exc)], []
    try:
        fresh = collect(root)
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
    for page, text in _with_blocks(root):
        try:
            if rewrite(text, page, facts) != text:
                names = ", ".join(sorted({n for n, _, _ in find_blocks(text, page)}))
                errors.append(f"{page}: generated block(s) {names} differ from the facts snapshot; "
                              f"run python {GENERATOR} --write (never edit a block by hand)")
        except GenError as exc:
            errors.append(str(exc))
    return errors, warnings


def write(root: Path = REPO_ROOT) -> list[str]:
    facts = collect(root)
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
    ap.add_argument("--root", default=str(REPO_ROOT), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.list:
        for page, text in _with_blocks(root):
            for name, start, _ in find_blocks(text, page):
                print(f"{page}:{start + 1}: gen:{name}")
        return 0
    if args.write:
        try:
            changed = write(root)
        except GenError as exc:
            print(f"::error title=Generated docs blocks::{exc}")
            return 1
        print("gen_sections: wrote " + ", ".join(changed))
        return 0
    errors, warnings = check(root)
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
