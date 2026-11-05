#!/usr/bin/env python3
"""AI gateway guide drift guard (AA-1042, S270). Stdlib only.

docs/architecture/ai-gateway.md (ARCH-01-ai-gateway) and its Vietnamese copy ai-gateway.vi.md are the one prose source
of the AI gateway: the CIS admin page AI gateway › Guide renders them next to the live tables. A stage, model,
connection or secret the page names in backticks must still exist, or the guide tells staff about something that is
gone. This check fails when, in either page, a backticked token:

  * looks like a STAGE key (snake_case whose first part is the first part of a stage in the snapshot, e.g. `t9_write`,
    `tp_extract`) and is not a stage of the committed route snapshot;
  * looks like a MODEL or CONNECTION key (a hyphenated key whose first part starts a model or connection key of the
    snapshot, e.g. `haiku-5-5`, `openai-direct`; or `acc<N>`) and is neither a model nor a connection of the snapshot;
  * looks like a SECRET name (`<prefix>/<env>/<name>`, e.g. `aa-cis/dev/openai-key`) and has no row in
    docs/security/secrets-register.md.

The snapshot is docs/generated/llm-routes.snapshot.json (tools/docs/gen_llm_routes.py, schema 2: routes, models,
connections, deployments; names only). A snapshot without the connection list (captured before schema 2) fails:
recapture it. Templates (`aa-llm/<env>/`), tokens with spaces, dots or upper case, and anything not shaped like a key
are not checked. Public repo: the check reads names only and prints names only.

Fix a finding by correcting the page (both languages), or, when the name is new, by recapturing the snapshot
(`gen_llm_routes.py dump` in the CIS container, then `import`) or adding the secret's register row.

Usage:
  python tools/docs/check_ai_gateway_names.py
  python tools/docs/check_ai_gateway_names.py --root <repo>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from docslib import REPO_ROOT, Finding, emit

PAGES = ("docs/architecture/ai-gateway.md", "docs/architecture/ai-gateway.vi.md")
SNAPSHOT = "docs/generated/llm-routes.snapshot.json"
REGISTER = "docs/security/secrets-register.md"

TICKED = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
STAGE_SHAPE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
KEY_SHAPE = re.compile(r"^[a-z][a-z0-9.]*(?:-[a-z0-9.]+)+$")
ACC_SHAPE = re.compile(r"^acc\d+$")
SECRET_SHAPE = re.compile(r"^[a-z0-9][a-z0-9-]*/(?:dev|stg|staging|prod|ops)/[A-Za-z0-9._+=@/-]*[A-Za-z0-9]$")
REGISTER_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")


class Names:
    """The names the page may use: stages, models and connections of the snapshot, secrets of the register."""

    def __init__(self, stages: set[str], models: set[str], connections: set[str] | None, secrets: set[str]):
        self.stages, self.models, self.connections, self.secrets = stages, models, connections, secrets
        self.stage_heads = {s.split("_", 1)[0] for s in stages}
        self.key_heads = {k.split("-", 1)[0] for k in models | (connections or set()) if "-" in k}


def load_names(root: Path) -> tuple[Names | None, list[Finding]]:
    path = root / SNAPSHOT
    if not path.is_file():
        return None, [Finding(SNAPSHOT, 1, "AI gateway names", "route snapshot missing: run gen_llm_routes.py import")]
    snap = json.loads(path.read_text(encoding="utf-8"))
    findings: list[Finding] = []
    connections = None
    if snap.get("connections") is None:
        findings.append(Finding(SNAPSHOT, 1, "AI gateway names",
                                "the snapshot has no connection list (captured before schema 2): recapture it with "
                                "`gen_llm_routes.py dump` in the CIS container, then `import`"))
    else:
        connections = {c["connection_key"] for c in snap["connections"]}
    secrets: set[str] = set()
    reg = root / REGISTER
    if reg.is_file():
        for line in reg.read_text(encoding="utf-8").splitlines():
            m = REGISTER_ROW.match(line)
            if m:
                secrets.add(m.group(1).strip())
    else:
        findings.append(Finding(REGISTER, 1, "AI gateway names", "secrets register missing"))
    return Names({r["stage"] for r in snap.get("routes") or []},
                 {m["model_key"] for m in snap.get("models") or []}, connections, secrets), findings


def classify(token: str, names: Names) -> str | None:
    """'stage' | 'key' | 'secret' when the token is shaped like one the guard checks, else None."""
    if SECRET_SHAPE.match(token):
        return "secret"
    if STAGE_SHAPE.match(token) and token.split("_", 1)[0] in names.stage_heads:
        return "stage"
    if ACC_SHAPE.match(token) or (KEY_SHAPE.match(token) and token.split("-", 1)[0] in names.key_heads):
        return "key"
    return None


def problem(token: str, kind: str, names: Names) -> str | None:
    if kind == "stage" and token not in names.stages:
        return f"`{token}` is not a stage of the route snapshot"
    if kind == "key" and token not in names.models and token not in (names.connections or set()):
        if names.connections is None:
            return None                       # reported once as "no connection list"
        return f"`{token}` is neither a model nor a connection of the route snapshot"
    if kind == "secret" and token not in names.secrets:
        return f"`{token}` has no row in {REGISTER}"
    return None


def check_page(root: Path, page: str, names: Names) -> tuple[list[Finding], int]:
    """(findings, tokens checked) of one page; code fences are skipped."""
    findings: list[Finding] = []
    checked = 0
    fenced = False
    for n, line in enumerate((root / page).read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for m in TICKED.finditer(line):
            token = m.group(1).strip()
            kind = classify(token, names)
            if kind is None:
                continue
            checked += 1
            msg = problem(token, kind, names)
            if msg:
                findings.append(Finding(page, n, "AI gateway names", msg))
    return findings, checked


def check(root: Path) -> tuple[list[Finding], int]:
    names, findings = load_names(root)
    if names is None:
        return findings, 0
    total = 0
    for page in PAGES:
        if not (root / page).is_file():
            if page.endswith(".vi.md"):
                findings.append(Finding(page, 1, "AI gateway names", "the Vietnamese copy is missing"))
                continue
            findings.append(Finding(page, 1, "AI gateway names", "the guide page is missing"))
            continue
        f, n = check_page(root, page, names)
        findings += f
        total += n
    return findings, total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    args = ap.parse_args(argv)
    findings, total = check(args.root)
    emit(findings, "error")
    if not findings:
        print(f"{total} stage, model, connection and secret names in the AI gateway guide, every one exists")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
