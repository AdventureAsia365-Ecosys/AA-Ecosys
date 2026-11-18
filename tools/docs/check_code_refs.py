#!/usr/bin/env python3
"""Names inside backticks on docs pages must exist (AA-1132 A7). Warnings by default; --strict turns them into errors.

The S283 docs audit found pages that name a file, a Terraform address, a service or a job kind that no longer exists:
a runbook whose `terraform apply -target=...` hits nothing ("No changes"), a retired service name, a job kind removed
from the code. This lint reads every inline code span (and, for Terraform addresses, fenced code too) on the pages the
generated blocks scan (tools/docs/gen_sections.py: docs/ outside journals, skill/, .claude/, .kiro/steering/,
README.md; ADRs and generated pages left out: an ADR records history) and checks seven kinds of name against a source
that is already in this repo:

  path       a root path (`docs/...`, `tools/...`, `skill/...`, `scripts/...`, `.github/...`, `.claude/...`,
             `.kiro/...`, `.githooks/...`) exists in this checkout. Skipped when the text just before the span names an
             app or the Infra repo (the path is then in that repo), and for globs and placeholders.
  tf-address the address after `-target=` / `-replace=` is in the masked Terraform inventory
             (docs/generated/inventory.md: every resource of accounts/aa365), with or without its index. Lines that
             name another root (`accounts/<other>`) are skipped.
  service    `aa-<app>-dev-<name>` is a resource name of the inventory.
  (service, job-kind and workflow skip a line that says the name is gone: "retired", "deleted", "was", ...)
  job-kind   `bk_*`, `crm_*`, `tp_*` is a registered kind of its owner (facts snapshot, repo facts), a DB role of the
             schema reference is not a kind.
  setting    `<app>.<area>.<key>` (cis, booking, crm, tripplanner) is a key of the settings registries
             (docs/catalogue/surface.snapshot.json); `<schema>.<table>.<column>` of a known table is skipped.
  migration  `tp-NNN`, `bk-NNN`, `crm-NNN` and a CIS file name `NNN_*.sql` are not newer than the latest applied
             migration of their owner (facts snapshot): a page must not promise a migration that does not exist yet.
  workflow   a workflow file name (`*.yml` alone or under `.github/workflows/`) exists in one of the six repos
             (facts snapshot repo workflows + this repo's own folder). Data files (`*.yaml`) are not checked.

Add `docs-lint: ignore` to a line to skip it. Every rule only reads files of this repo: no network, no AWS.

Usage:
  python tools/docs/check_code_refs.py                      # warnings, exit 0
  python tools/docs/check_code_refs.py --strict             # exit 1 on any finding
  python tools/docs/check_code_refs.py --strict-rules tf-address   # docs lint: that rule is an error, the rest warn
  python tools/docs/check_code_refs.py --only path,service  # some rules
  python tools/docs/check_code_refs.py --summary            # counts per rule only
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from docslib import IGNORE_MARKER, REPO_ROOT, Finding, emit, is_generated

TITLE = "Docs code reference"
RULES = ("path", "tf-address", "service", "job-kind", "setting", "migration", "workflow")
SNAPSHOT = "docs/generated/facts.snapshot.json"
INVENTORY = "docs/generated/inventory.md"
SCHEMA_REF = "docs/architecture/db-schema-reference.md"
SURFACE = "docs/catalogue/surface.snapshot.json"
SKIP_PAGES = ("docs/adr/",)
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
ROOT_PATH = re.compile(r"^(?:docs|tools|skill|scripts|\.github|\.claude|\.kiro|\.githooks)/[A-Za-z0-9._/@()+-]*$")
PLACEHOLDER = re.compile(r"[*?{}<>$\[\]]|\.\.\.|YYYY|NNN|<|xxx", re.I)
OTHER_REPO = re.compile(r"(?:AA-CIS-App|AA-Booking|AA-Partner|AA-TripPlanner-Web|AA-CIS-Infra|\bCIS\b|\bBooking\b|"
                        r"\bPartner\b|\bCRM\b|\bTripPlanner\b|\bInfra\b|app repo|each repo|every repo|the app's|apps?/)")
TF_ADDR = re.compile(r"-(?:target|replace)=\s*(?:'([^']+)'|\"((?:[^\"\\]|\\.)+)\"|([^\s'\"]+))")
SERVICE = re.compile(r"^aa-(?:cis|booking|crm|tripplanner|identity)-dev-[a-z0-9-]+$")
KIND = re.compile(r"^(bk|crm|tp)_[a-z0-9_]+$")
KIND_OWNER = {"bk": "AA-Booking", "crm": "AA-Partner", "tp": "AA-TripPlanner-Web"}
SETTING = re.compile(r"^(cis|booking|crm|tripplanner)\.[a-z0-9_]+\.[a-z0-9_.]+$")
MIGRATION = re.compile(r"^(tp|bk|crm)-(\d{3})$")
CIS_MIGRATION = re.compile(r"^(?:.*/)?(\d{3})_[a-z0-9_]+\.sql$")
MIGRATION_OWNER = {"tp": "TripPlanner", "bk": "Booking", "crm": "CRM", "": "CIS"}
WORKFLOW = re.compile(r"^(?:\.github/workflows/)?([a-z0-9][a-z0-9_.-]*\.yml)$")
COUNTED_ONLY = re.compile(r"^Counted only:(.*)$", re.M)
CONTRACT_OR_HOST = re.compile(r"\.v\d+$|\.(?:com|net|org|io|it|dev|app|invalid)(?:\.|$)")
KIND_WORD = re.compile(r"\bkinds?\b", re.I)
# A line that says a name is gone mentions it on purpose: the name rules (service, job-kind, workflow) skip it.
HISTORY_WORDS = re.compile(r"\b(?:retired|retire|deleted|removed|replaced|renamed|formerly|no longer|gone|dropped|"
                           r"was|were|old|legacy)\b", re.I)
FILE_SUFFIX = re.compile(r"\.(?:ya?ml|json|md|py|sql|ts|tsx|txt|csv)$")
GENERATED_PATHS = ("docs/generated/docs-changes.md",)   # built by the docs bundle, not a file in git (rule 14)
INVENTORY_ROW = re.compile(r"^\|\s*`[a-z0-9_]+`\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|")
TABLE_HEAD = re.compile(r"^### `([a-z0-9_]+)\.([a-z0-9_]+)`")
CONTEXT_CHARS = 80


class Sources:
    """Everything the rules compare against, read once from the repo."""

    def __init__(self, root: Path):
        self.root = root
        self.tf_addresses: set[str] = set()
        self.resource_names: set[str] = set()
        inv = root / INVENTORY
        # Types the inventory only counts (records, policies, random_password): their addresses cannot be checked.
        self.counted_types: set[str] = set()
        if inv.exists():
            inv_text = inv.read_text(encoding="utf-8")
            for m in COUNTED_ONLY.finditer(inv_text):
                self.counted_types |= set(re.findall(r"`([a-z0-9_]+)`", m.group(1)))
            for line in inv_text.splitlines():
                m = INVENTORY_ROW.match(line)
                if m:
                    self.resource_names.add(m.group(1).strip())
                    self.tf_addresses.add(m.group(2))
        self.tf_bare = {strip_index(a) for a in self.tf_addresses}
        self.tables: set[str] = set()
        self.roles: set[str] = set()
        ref = root / SCHEMA_REF
        if ref.exists():
            text = ref.read_text(encoding="utf-8")
            for line in text.splitlines():
                m = TABLE_HEAD.match(line)
                if m:
                    self.tables.add(f"{m.group(1)}.{m.group(2)}")
            # Every identifier of the schema reference (roles, tables, columns): `crm_eraser` is a DB role, not a kind.
            self.roles = set(re.findall(r"[a-z][a-z0-9_]+", text))
        self.settings: set[str] = set()
        surface = root / SURFACE
        if surface.exists():
            try:
                self.settings = set((json.loads(surface.read_text(encoding="utf-8")).get("settings") or {}).keys())
            except ValueError:
                pass
        facts = {}
        snap = root / SNAPSHOT
        if snap.exists():
            try:
                facts = json.loads(snap.read_text(encoding="utf-8"))
            except ValueError:
                facts = {}
        repos = facts.get("repos") or {}
        self.kinds: dict[str, set[str]] | None = None
        if repos.get("job_kinds"):
            self.kinds = {repo: {k["kind"] for k in kinds} for repo, kinds in repos["job_kinds"].items()}
        self.latest: dict[str, int] = {}
        for o in (facts.get("migrations") or {}).get("owners") or []:
            m = re.search(r"(\d+)$", str(o.get("latest", "")))
            if m:
                self.latest[o["owner"]] = int(m.group(1))
        self.workflows: set[str] | None = None
        if repos.get("workflows"):
            self.workflows = {w for names in repos["workflows"].values() for w in names}
            wf = root / ".github" / "workflows"
            if wf.is_dir():
                self.workflows |= {p.name for p in wf.iterdir() if p.suffix in (".yml", ".yaml")}


def strip_index(address: str) -> str:
    return re.sub(r"\[[^\]]*\]", "", address)


def resource_type(address: str) -> str | None:
    """`module.environment.aws_kms_key.x["a"]` -> `aws_kms_key` (the part before the resource name)."""
    parts = [p for p in strip_index(address).split(".") if p]
    while len(parts) >= 2 and parts[0] == "module":
        parts = parts[2:]
    if parts and parts[0] == "data":
        parts = parts[1:]
    return parts[0] if len(parts) >= 2 else None


def ignored_paths(root: Path, paths: list[str]) -> set[str]:
    """The paths .gitignore ignores (git check-ignore); empty outside a git checkout."""
    if not paths:
        return set()
    try:
        # A path and the same path as a folder: a folder-only rule (`docs/backups/`) matches only the second form.
        res = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "--stdin"],
                             input="\n".join(p for path in paths for p in (path, path + "/")),
                             capture_output=True, text=True)
    except OSError:
        return set()
    return {line.strip().rstrip("/") for line in res.stdout.splitlines() if line.strip()}


def other_repo_path(root: Path, token: str) -> bool:
    """A `tools/<x>/...` or `scripts/<x>/...` path whose folder this repo does not have belongs to another repo."""
    parts = token.split("/")
    return parts[0] in ("tools", "scripts") and len(parts) > 2 and not (root / parts[0] / parts[1]).is_dir()


def spans(text: str):
    """(line number, span text, text before the span on that line, in fenced code, the whole line) of every code span;
    a fenced line is yielded whole."""
    fence = None
    for n, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if m:
            if fence is None:
                fence = m.group(1)
            elif m.group(1) == fence:
                fence = None
            continue
        if IGNORE_MARKER in line:
            continue
        if fence is not None:
            yield n, line, "", True, line
            continue
        for s in INLINE.finditer(line):
            yield n, s.group(1).strip(), line[max(0, s.start() - CONTEXT_CHARS):s.start()], False, line


def check_text(relpath: str, text: str, src: Sources, rules: tuple[str, ...] = RULES) -> list[Finding]:
    out: list[Finding] = []

    def add(n: int, rule: str, msg: str) -> None:
        out.append(Finding(relpath, n, TITLE, f"[{rule}] {msg}", kind=rule))

    for n, span, before, fenced, line in spans(text):
        if "tf-address" in rules and ("-target=" in span or "-replace=" in span) and src.tf_addresses:
            if not re.search(r"accounts/(?!aa365\b)[a-z0-9-]+", span):
                for m in TF_ADDR.finditer(span):
                    addr = (m.group(1) or m.group(2) or m.group(3)).replace('\\"', '"').strip()
                    if PLACEHOLDER.search(strip_index(addr)) or not addr or resource_type(addr) in src.counted_types:
                        continue
                    if addr not in src.tf_addresses and strip_index(addr) not in src.tf_bare and not any(
                            a.startswith(addr + ".") for a in src.tf_addresses):
                        add(n, "tf-address", f"Terraform address `{addr}` is not in the resource inventory "
                                             f"({INVENTORY}); a -target on it changes nothing")
        if fenced:
            continue
        token = span.rstrip("/").split("#", 1)[0]
        token = re.sub(r":\d+(?:-\d+)?$", "", token)
        if " " in token or not token:
            continue
        if "path" in rules and ROOT_PATH.match(token) and not PLACEHOLDER.search(token):
            known_workflow = token.startswith(".github/workflows/") and src.workflows is not None and \
                token.rsplit("/", 1)[-1] in src.workflows
            if (not OTHER_REPO.search(before) and not other_repo_path(src.root, token) and not known_workflow
                    and token not in GENERATED_PATHS and not (src.root / token).exists()):
                add(n, "path", f"`{token}` does not exist in this repo (moved or deleted?)")
        history = bool(HISTORY_WORDS.search(INLINE.sub("", line)))   # the prose, not the names in code
        if "service" in rules and src.resource_names and SERVICE.match(token) and not history:
            if token not in src.resource_names:
                add(n, "service", f"`{token}` is not a resource name in {INVENTORY} (renamed or retired?)")
        m = KIND.match(token)
        if ("job-kind" in rules and m and src.kinds is not None and token not in src.roles and KIND_WORD.search(line)
                and not history):
            owner = KIND_OWNER[m.group(1)]
            if owner in src.kinds and token not in src.kinds[owner]:
                add(n, "job-kind", f"`{token}` is not a registered {owner} job kind (facts snapshot)")
        if ("setting" in rules and src.settings and SETTING.match(token) and not CONTRACT_OR_HOST.search(token)
                and not FILE_SUFFIX.search(token)):
            table = ".".join(token.split(".")[:2])
            if table not in src.tables and token not in src.settings:
                add(n, "setting", f"`{token}` is not a key of the settings registries ({SURFACE})")
        if "migration" in rules and src.latest:
            mm = MIGRATION.match(token)
            prefix, number = (mm.group(1), int(mm.group(2))) if mm else (None, None)
            cm = CIS_MIGRATION.match(token) if not mm else None
            if cm:
                prefix, number = "", int(cm.group(1))
            owner = MIGRATION_OWNER.get(prefix) if prefix is not None else None
            if owner and owner in src.latest and number > src.latest[owner]:
                add(n, "migration", f"`{token}`: {owner} has applied up to {src.latest[owner]} on Dev (facts "
                                    "snapshot); a planned migration needs its own words, not a number")
        if "workflow" in rules and src.workflows is not None:
            wm = WORKFLOW.match(token)
            if (wm and (token.startswith(".github/") or "/" not in token) and wm.group(1) not in src.workflows
                    and not history):
                add(n, "workflow", f"`{token}` is not a workflow file of any of the six repos (facts snapshot)")
    return out


def pages(root: Path) -> list[str]:
    import gen_sections
    return [p for p in gen_sections.pages(root) if not p.startswith(SKIP_PAGES)]


def run(root: Path, files: list[str] | None = None, rules: tuple[str, ...] = RULES) -> list[Finding]:
    src = Sources(root)
    findings: list[Finding] = []
    for relpath in files or pages(root):
        try:
            text = (root / relpath).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if is_generated(text):
            continue
        findings += check_text(relpath, text, src, rules)
    missing = [f.message.split("`")[1] for f in findings if f.kind == "path"]
    ignored = ignored_paths(root, missing)
    return [f for f in findings if not (f.kind == "path" and f.message.split("`")[1] in ignored)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="repo-relative pages (default: every page in scope)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on a finding (default: warnings, exit 0)")
    ap.add_argument("--strict-rules", default="", help="comma-separated rules whose findings are errors (exit 1)")
    ap.add_argument("--only", help=f"comma-separated rules ({', '.join(RULES)})")
    ap.add_argument("--summary", action="store_true", help="print counts per rule only")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    args = ap.parse_args(argv)
    rules = tuple(r.strip() for r in args.only.split(",")) if args.only else RULES
    unknown = [r for r in rules if r not in RULES]
    if unknown:
        ap.error(f"unknown rule(s): {', '.join(unknown)}")
    strict = set(rules) if args.strict else {r.strip() for r in args.strict_rules.split(",") if r.strip()}
    unknown = [r for r in strict if r not in RULES]
    if unknown:
        ap.error(f"unknown rule(s): {', '.join(unknown)}")
    findings = run(args.root.resolve(), args.files or None, rules)
    errors = [f for f in findings if f.kind in strict]
    counts = {r: sum(1 for f in findings if f.kind == r) for r in rules}
    if not args.summary:
        emit(errors, "error")
        emit([f for f in findings if f.kind not in strict], "warning")
    print("code refs: " + ", ".join(f"{r} {c}" for r, c in counts.items()) + f" ({len(findings)} findings, "
          f"{len(errors)} errors: rules {', '.join(sorted(strict)) or 'none'} are errors)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
