#!/usr/bin/env python3
"""Facts read from the app and Infra repos for the generated docs blocks (AA-1132 A3). Read only, stdlib only.

gen_sections.py renders every block from docs/generated/facts.snapshot.json. Most facts of that snapshot sit in this
repo (platform.yaml, the Infra inventory, the live schema dump); the ones below live in the five other repos, so they
are collected from a workspace that has them side by side (the local workspace, or the nightly catalogue job's
checkout) and stored in the snapshot. A docs PR in this repo never needs the other repos: it renders the stored facts.

  versions     each app's `.release-please-manifest.json` ("." entry)
  job kinds    CIS: every `@job_kind(...)` registration under services/jobs/ (defaults from shared/jobs/registry.py
               JobKind); Booking and CRM: `EXPECTED_SECONDS`, `DEPLOY_BLOCKING_KINDS`, `DEPLOY_GATE_EXEMPT` and
               `TEST_KINDS` of their jobs/kinds.py; TripPlanner: `HANDLERS`, `DAILY`, `MAX_ATTEMPTS` of
               backend/jobs/handler.py
  backup       AA-CIS-Infra: `backup_retention_period` of modules/rds/main.tf and the default of
               `rds_backup_copy_max_age_days` (accounts/aa365/rds_snapshot_expiry.tf)
  workflows    the workflow file names of each repo's .github/workflows/ (the backtick check of check_code_refs.py)

Everything is read statically (Python `ast`, a regex for HCL): no app module is imported, nothing runs. A value the
reader cannot resolve (a name built at run time) is kept as an `unresolved` note with its file and line instead of
failing the collection, so a refactor in an app never turns a docs PR red; the block shows the note.

A repo is read from a folder (`--repos-root`: <root>/apps/<repo>, <root>/infra/AA-CIS-Infra) or, with `--repos-ref`,
from a git ref of that folder's repository (`git show <ref>:<path>`), so a stale or dirty local checkout is never read.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

REPO_DIRS = {
    "AA-CIS-App": "apps/AA-CIS-App",
    "AA-Booking": "apps/AA-Booking",
    "AA-Partner": "apps/AA-Partner",
    "AA-TripPlanner-Web": "apps/AA-TripPlanner-Web",
    "AA-CIS-Infra": "infra/AA-CIS-Infra",
}
APP_REPOS = ("AA-CIS-App", "AA-Booking", "AA-Partner", "AA-TripPlanner-Web")
# Package roots an app imports from: `app.jobs.kinds` is backend/app/jobs/kinds.py in Booking, api/app/... in Partner.
PACKAGE_BASES = ("", "backend/", "api/")
CIS_JOBS = "services/jobs/"
CIS_REGISTRY = "shared/jobs/registry.py"
KINDS_FILES = {"AA-Booking": "backend/app/jobs/kinds.py", "AA-Partner": "api/app/jobs/kinds.py"}
TP_HANDLER = "backend/jobs/handler.py"
RDS_MAIN = "modules/rds/main.tf"
RDS_EXPIRY = "accounts/aa365/rds_snapshot_expiry.tf"
# Folders the readers below open in each repo, imports included (CIS job modules take KIND from shared/, services/
# and api/services/). The nightly catalogue job checks the repos out sparsely (.github/workflows/catalogue.yml): its
# cone must cover these or a kind resolved through an import drops to `unresolved` (S284 review). test_repo_facts
# checks the workflow cone against this list, and against a full read of the local workspace when it is there.
READ_PATHS = {
    "AA-CIS-App": (CIS_JOBS, "shared/", "services/", "api/services/", ".github/workflows/"),
    "AA-Booking": ("backend/app/jobs/", ".github/workflows/"),
    "AA-Partner": ("api/app/jobs/", ".github/workflows/"),
    "AA-TripPlanner-Web": ("backend/", ".github/workflows/"),
    "AA-CIS-Infra": ("modules/rds/", "accounts/aa365/", ".github/workflows/"),
}
JOB_FLAGS = ("concurrency", "max_attempts", "expected_seconds", "background", "deploy_blocking", "deploy_gate_exempt")
UNRESOLVED = object()


class RepoReader:
    """Tracked files of one repo, from a folder or from a git ref of it."""

    def __init__(self, path: Path, ref: str | None = None):
        self.path = Path(path)
        self.ref = ref
        self._listing: list[str] | None = None

    def exists(self) -> bool:
        return self.path.is_dir()

    def files(self, prefix: str = "") -> list[str]:
        if self._listing is None:
            if self.ref:
                out = subprocess.run(["git", "-C", str(self.path), "ls-tree", "-r", "--name-only", self.ref],
                                     check=True, capture_output=True, text=True).stdout
                self._listing = sorted(line for line in out.splitlines() if line)
            else:
                self._listing = sorted(p.relative_to(self.path).as_posix() for p in self.path.rglob("*")
                                       if p.is_file() and ".git" not in p.relative_to(self.path).parts)
        return [f for f in self._listing if f.startswith(prefix)]

    def read(self, rel: str) -> str | None:
        if self.ref:
            res = subprocess.run(["git", "-C", str(self.path), "show", f"{self.ref}:{rel}"], capture_output=True)
            return res.stdout.decode("utf-8", "replace") if res.returncode == 0 else None
        p = self.path / rel
        try:
            return p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def head(self) -> str | None:
        try:
            out = subprocess.run(["git", "-C", str(self.path), "rev-parse", self.ref or "HEAD"], check=True,
                                 capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
        return out[:8] or None


# ------------------------------------------------------------------------------------------- static name resolver


class Resolver:
    """Resolves module-level constants across the modules of one repo: `KIND`, `ops_alerts.KIND`, `from x import Y`."""

    def __init__(self, reader: RepoReader):
        self.reader = reader
        self._modules: dict[str, ast.Module | None] = {}

    def module(self, rel: str) -> ast.Module | None:
        if rel not in self._modules:
            text = self.reader.read(rel)
            try:
                self._modules[rel] = ast.parse(text) if text is not None else None
            except SyntaxError:
                self._modules[rel] = None
        return self._modules[rel]

    def module_file(self, dotted: str, current: str, level: int = 0) -> str | None:
        """The repo path of `dotted` imported from `current` (a relative import when level > 0)."""
        parts = [p for p in dotted.split(".") if p]
        if level:
            base = current.split("/")[:-1]
            base = base[:len(base) - (level - 1)] if level > 1 else base
            candidates = ["/".join(base + parts)]
        else:
            candidates = [b + "/".join(parts) for b in PACKAGE_BASES]
        for c in candidates:
            for rel in (c + ".py", c + "/__init__.py"):
                if self.module(rel) is not None:
                    return rel
        return None

    def _bindings(self, rel: str) -> dict[str, tuple[str, object]]:
        """name -> ("value", expr) | ("module", file) | ("from", (file, name)) for the module's top level."""
        tree = self.module(rel)
        out: dict[str, tuple[str, object]] = {}
        if tree is None:
            return out
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        out[t.id] = ("value", node.value)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                out[node.target.id] = ("value", node.value)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    f = self.module_file(a.name, rel)
                    if f:
                        out[a.asname or a.name.split(".")[0]] = ("module", f)
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    name = a.asname or a.name
                    sub = self.module_file(f"{node.module or ''}.{a.name}".strip("."), rel, node.level)
                    if sub:
                        out[name] = ("module", sub)
                        continue
                    f = self.module_file(node.module or "", rel, node.level)
                    if f:
                        out[name] = ("from", (f, a.name))
        return out

    def name(self, rel: str, name: str, depth: int = 0):
        if depth > 8:
            return UNRESOLVED
        b = self._bindings(rel).get(name)
        if b is None:
            return UNRESOLVED
        kind, val = b
        if kind == "value":
            return self.value(rel, val, depth + 1)
        if kind == "module":
            return ("module", val)
        f, n = val
        return self.name(f, n, depth + 1)

    def value(self, rel: str, node: ast.AST, depth: int = 0):
        """A literal (str, int, bool, None, frozenset / tuple / list of literals, dict) or UNRESOLVED."""
        if depth > 8:
            return UNRESOLVED
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.name(rel, node.id, depth + 1)
        if isinstance(node, ast.Attribute):
            base = self.value(rel, node.value, depth + 1)
            if isinstance(base, tuple) and len(base) == 2 and base[0] == "module":
                return self.name(base[1], node.attr, depth + 1)
            return UNRESOLVED
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            items = [self.value(rel, e, depth + 1) for e in node.elts]
            return UNRESOLVED if any(i is UNRESOLVED for i in items) else items
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("frozenset", "set",
                                                                                                "tuple", "list"):
            if not node.args:
                return []
            inner = self.value(rel, node.args[0], depth + 1)
            return list(inner) if isinstance(inner, (list, dict)) else UNRESOLVED
        if isinstance(node, ast.Dict):
            out = {}
            for k, v in zip(node.keys, node.values):
                if k is None:
                    return UNRESOLVED
                key = self.value(rel, k, depth + 1)
                if not isinstance(key, (str, int)):
                    return UNRESOLVED
                out[key] = self.value(rel, v, depth + 1)
            return out
        return UNRESOLVED

    def kind_keywords(self, rel: str, name: str) -> list[str]:
        """Every `kind="..."` string keyword in the definition of `name` (module level, possibly imported)."""
        b = self._bindings(rel).get(name)
        if b is None:
            return []
        if b[0] == "from":
            f, n = b[1]
            return self.kind_keywords(f, n)
        if b[0] != "value":
            return []
        return [kw.value.value for node in ast.walk(b[1]) if isinstance(node, ast.Call) for kw in node.keywords
                if kw.arg == "kind" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)]


# ---------------------------------------------------------------------------------------------------- collectors


def _clean(value):
    return None if value is UNRESOLVED else value


def cis_defaults(res: Resolver) -> dict:
    """The JobKind dataclass defaults of shared/jobs/registry.py (fields with a literal default)."""
    tree = res.module(CIS_REGISTRY)
    defaults = {"concurrency": 1, "max_attempts": 3, "expected_seconds": 600, "background": False,
                "deploy_blocking": False, "deploy_gate_exempt": False}
    if tree is None:
        return defaults
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "JobKind":
            for item in node.body:
                if (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                        and item.target.id in JOB_FLAGS and item.value is not None):
                    v = res.value(CIS_REGISTRY, item.value)
                    if v is not UNRESOLVED:
                        defaults[item.target.id] = v
    return defaults


def _loop_registries(tree: ast.Module) -> list[str]:
    """Names iterated by module-level `for` loops (`for spec in SPECS.values(): _register(spec)`)."""
    names = []
    for node in tree.body:
        if isinstance(node, ast.For):
            it = node.iter
            if isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute):
                it = it.func.value
            if isinstance(it, ast.Name):
                names.append(it.id)
    return names


def cis_job_kinds(reader: RepoReader) -> tuple[list[dict], list[str]]:
    res = Resolver(reader)
    defaults = cis_defaults(res)
    kinds, unresolved = [], []
    for rel in reader.files(CIS_JOBS):
        if not rel.endswith(".py") or "/" in rel[len(CIS_JOBS):]:
            continue
        tree = res.module(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and getattr(dec.func, "id", getattr(dec.func, "attr", None))
                        == "job_kind" and dec.args):
                    continue
                flags = dict(defaults)
                for kw in dec.keywords:
                    if kw.arg in JOB_FLAGS:
                        v = res.value(rel, kw.value)
                        flags[kw.arg] = v if v is not UNRESOLVED else None
                name = res.value(rel, dec.args[0])
                names = [name] if isinstance(name, str) else []
                if not names and isinstance(dec.args[0], ast.Attribute) and dec.args[0].attr == "kind":
                    # A registration in a loop over a registry (retention): the registry's kind="..." keywords.
                    names = [k for reg in _loop_registries(tree) for k in res.kind_keywords(rel, reg)]
                if not names:
                    unresolved.append(f"{rel}:{dec.lineno}")
                for n in names:
                    kinds.append({"kind": n, "code": rel, **flags})
    kinds.sort(key=lambda k: k["kind"])
    return kinds, unresolved


def table_job_kinds(reader: RepoReader, rel: str) -> tuple[list[dict], list[str]]:
    """Booking / CRM: the kinds of EXPECTED_SECONDS (+ TEST_KINDS, DEPLOY_GATE_EXEMPT) with their flags."""
    res = Resolver(reader)
    if res.module(rel) is None:
        return [], [f"{rel}: not found"]
    unresolved = []

    def get(name: str, default):
        v = res.name(rel, name)
        if v is UNRESOLVED:
            if res._bindings(rel).get(name) is not None:
                unresolved.append(f"{rel}: {name}")
            return default
        return v

    expected = get("EXPECTED_SECONDS", {})
    blocking = set(get("DEPLOY_BLOCKING_KINDS", []) or [])
    exempt = set(get("DEPLOY_GATE_EXEMPT", []) or [])
    test = set(get("TEST_KINDS", []) or [])
    if not isinstance(expected, dict):
        return [], [f"{rel}: EXPECTED_SECONDS"]
    names = sorted({k for k in expected if isinstance(k, str)} | test)
    kinds = [{"kind": n, "code": rel, "expected_seconds": _clean(expected.get(n)), "deploy_blocking": n in blocking,
              "deploy_gate_exempt": n in exempt, "test_only": n in test} for n in names]
    for k, v in expected.items():
        if v is UNRESOLVED:
            unresolved.append(f"{rel}: EXPECTED_SECONDS[{k}]")
    return kinds, unresolved


def tripplanner_job_kinds(reader: RepoReader) -> tuple[list[dict], list[str]]:
    res = Resolver(reader)
    rel = TP_HANDLER
    tree = res.module(rel)
    if tree is None:
        return [], [f"{rel}: not found"]
    unresolved = []
    raw = {}
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target, value = node.targets[0].id, node.value
        if target in ("HANDLERS", "DAILY", "MAX_ATTEMPTS") and isinstance(value, ast.Dict):
            raw[target] = {}
            for k, v in zip(value.keys, value.values):
                key = res.value(rel, k) if k is not None else UNRESOLVED
                if not isinstance(key, str):
                    unresolved.append(f"{rel}:{getattr(k, 'lineno', node.lineno)} {target} key")
                    continue
                raw[target][key] = res.value(rel, v) if target == "MAX_ATTEMPTS" else True
    handlers = raw.get("HANDLERS", {})
    daily = raw.get("DAILY", {})
    attempts = raw.get("MAX_ATTEMPTS", {})
    kinds = [{"kind": n, "code": rel, "daily": n in daily, "max_attempts": _clean(attempts.get(n))}
             for n in sorted(handlers)]
    return kinds, unresolved


def versions(reader: RepoReader) -> str | None:
    text = reader.read(".release-please-manifest.json")
    if not text:
        return None
    try:
        v = json.loads(text).get(".")
    except (ValueError, AttributeError):
        return None
    return v if isinstance(v, str) else None


def _hcl_number(text: str, pattern: str) -> int | None:
    m = re.search(pattern, text, re.S)
    return int(m.group(1)) if m else None


def backup(reader: RepoReader) -> dict:
    rds = reader.read(RDS_MAIN) or ""
    expiry = reader.read(RDS_EXPIRY) or ""
    return {
        "rds_pitr_days": _hcl_number(rds, r"(?m)^\s*backup_retention_period\s*=\s*(\d+)"),
        "rds_pitr_source": RDS_MAIN,
        "copy_max_age_days": _hcl_number(
            expiry, r'variable\s+"rds_backup_copy_max_age_days"\s*\{[^}]*?default\s*=\s*(\d+)'),
        "copy_max_age_source": RDS_EXPIRY,
    }


def workflows(reader: RepoReader) -> list[str]:
    return sorted({Path(f).name for f in reader.files(".github/workflows/")
                   if f.endswith((".yml", ".yaml")) and f.count("/") == 2})


def collect(readers: dict[str, RepoReader]) -> dict:
    """{"collected_from", "versions", "job_kinds", "backup", "workflows", "unresolved"} from the readers given."""
    out = {"collected_from": {}, "versions": {}, "job_kinds": {}, "backup": None, "workflows": {}, "unresolved": []}
    for repo, reader in readers.items():
        if not reader.exists():
            continue
        out["collected_from"][repo] = reader.head()
        out["workflows"][repo] = workflows(reader)
        if repo in APP_REPOS:
            out["versions"][repo] = versions(reader)
        if repo == "AA-CIS-App":
            kinds, bad = cis_job_kinds(reader)
        elif repo in KINDS_FILES:
            kinds, bad = table_job_kinds(reader, KINDS_FILES[repo])
        elif repo == "AA-TripPlanner-Web":
            kinds, bad = tripplanner_job_kinds(reader)
        else:
            kinds, bad = None, []
        if kinds is not None:
            out["job_kinds"][repo] = kinds
        out["unresolved"] += [f"{repo} {b}" for b in bad]
        if repo == "AA-CIS-Infra":
            out["backup"] = backup(reader)
    return out


def facts_of(facts: dict | None, repo: str) -> dict:
    """The facts of one repo inside a collect() result, without its head (what a page block can show for it)."""
    facts = facts or {}
    return {
        "versions": (facts.get("versions") or {}).get(repo),
        "job_kinds": (facts.get("job_kinds") or {}).get(repo),
        "workflows": (facts.get("workflows") or {}).get(repo),
        "backup": facts.get("backup") if repo == "AA-CIS-Infra" else None,
        "unresolved": sorted(u for u in facts.get("unresolved") or [] if u.startswith(repo + " ")),
    }


def keep_heads(new: dict, previous: dict | None) -> dict:
    """`new` with the previous `collected_from` head of every repo whose facts did not change.

    A head moves on every merge while the facts mostly stay put; printing the new head would rewrite the page blocks
    (and move each page's last-commit date, which clears its needs-review flag) for nothing. The head kept is the one
    the unchanged facts were first read at, so "read from main at <sha>" stays true."""
    old_heads = (previous or {}).get("collected_from") or {}
    heads = dict(new.get("collected_from") or {})
    for repo in heads:
        if old_heads.get(repo) and facts_of(new, repo) == facts_of(previous, repo):
            heads[repo] = old_heads[repo]
    return {**new, "collected_from": heads}


def readers_for(root: Path, ref: str | None = None) -> dict[str, RepoReader]:
    return {repo: RepoReader(Path(root) / rel, ref) for repo, rel in REPO_DIRS.items()}
