"""AA-1106 — the product catalogue: load, check and bundle docs/catalogue/{features,integrations}.yaml.

  python tools/catalogue/catalogue.py check                         every rule below; exit 1 on any problem
  python tools/catalogue/catalogue.py bundle --out DIR [--sha S] [--ref R]
                                                                    check, then write DIR/catalogue.json, the bundle
                                                                    the CIS admin page Platform › Product map reads
                                                                    (uploaded by the Docs sync workflow next to the
                                                                    docs reader manifest)

Rules (each problem is one line; the workflow "Catalogue" runs `check` on every pull request that touches the
catalogue, the contracts, the UAT catalogue or this tool):

  C1  shape: format 1, required fields, known values (status, kind, owner), unique ids of the right form
      (<APP>-F<nnn> with the app's prefix, INT-<nnn>, J-<nn>), no internal issue id in any text value (the admin
      page shows them all; YAML comments may name issues)
  C2  every contract file in docs/contracts/ (top level and rules/, README.md and samples/ excluded) is named by at
      least one integration, and every contract an integration names exists
  C3  every UAT scenario that is not retired (tools/uat/catalogue.json) names at least one feature id, and every
      feature id a scenario names exists
  C4  every setting, entitlement, AI gateway connection and secret named in a condition exists: settings and
      entitlements in docs/catalogue/surface.snapshot.json, connections in docs/generated/llm-routes.snapshot.json,
      secrets in docs/security/secrets-register.md
  C5  every page and API route group of the surface snapshot maps to at least one feature of its app, and every
      surface pattern matches at least one entry (no stale pattern)
  C6  every feature, integration and UAT id a journey, a depends_on or an integration names exists; every guide page
      exists under docs/
  C7  public repo: no 12-digit run (an AWS account ID), no ARN, no e-mail address in either YAML file or the bundle

Standard library + PyYAML (tools/docs/requirements.txt pins it).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_DIR = Path("docs/catalogue")
FEATURES = CATALOGUE_DIR / "features.yaml"
INTEGRATIONS = CATALOGUE_DIR / "integrations.yaml"
SURFACE = CATALOGUE_DIR / "surface.snapshot.json"
CONTRACTS = Path("docs/contracts")
UAT = Path("tools/uat/catalogue.json")
LLM_ROUTES = Path("docs/generated/llm-routes.snapshot.json")
SECRETS_REGISTER = Path("docs/security/secrets-register.md")
BUNDLE_FORMAT = 1

APP_PREFIX = {"cis": "CIS", "booking": "BK", "crm": "CRM", "tripplanner": "TP", "infra": "INF"}
STATUSES = ("live", "beta", "planned", "retired")
OWNERS = ("tech_lead", "business_owner", "content_lead", "customer_success", "finance", "ai_ops")
KINDS = ("db_view", "http_api", "event_outbox", "webhook", "m2m", "provider")
TENANT_KINDS = ("demo", "pilot", "agency")
CONDITION_KEYS = ("entitlements", "settings", "connections", "secrets", "tenant_kinds", "note")
EXTERNAL = "external"

FEATURE_ID = re.compile(r"^(CIS|BK|CRM|TP|INF)-F\d{3}$")
INTEGRATION_ID = re.compile(r"^INT-\d{3}$")
JOURNEY_ID = re.compile(r"^J-\d{2}$")
SURFACE_ITEM = re.compile(r"^(page:/[A-Za-z0-9_\-\[\]./*]*|route:[A-Za-z0-9_\-/]+)$")
ISSUE_ID = re.compile(r"\bAA-?\d{2,4}\b")
ACCOUNT_ID = re.compile(r"(?<!\d)\d{12}(?!\d)")
ARN = re.compile(r"\barn:aws", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+")


class Catalogue:
    def __init__(self, root: Path = REPO_ROOT):
        self.root = root
        self.features_doc = self._yaml(FEATURES)
        self.integrations_doc = self._yaml(INTEGRATIONS)
        self.surface = self._json(SURFACE, {"apps": {}, "settings": {}, "entitlements": {}})
        self.uat = self._json(UAT, {"scenarios": []})
        self.llm = self._json(LLM_ROUTES, {"connections": []})

    def _yaml(self, rel: Path) -> dict:
        data = yaml.safe_load((self.root / rel).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def _json(self, rel: Path, default: dict) -> dict:
        path = self.root / rel
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default

    @property
    def apps(self) -> list[dict]:
        return [a for a in self.features_doc.get("apps") or [] if isinstance(a, dict)]

    @property
    def features(self) -> list[dict]:
        return [f for f in self.features_doc.get("features") or [] if isinstance(f, dict)]

    @property
    def journeys(self) -> list[dict]:
        return [j for j in self.features_doc.get("journeys") or [] if isinstance(j, dict)]

    @property
    def integrations(self) -> list[dict]:
        return [i for i in self.integrations_doc.get("integrations") or [] if isinstance(i, dict)]

    @property
    def scenarios(self) -> list[dict]:
        return [s for s in self.uat.get("scenarios") or [] if isinstance(s, dict)]

    def contract_files(self) -> list[str]:
        base = self.root / CONTRACTS
        out = []
        for f in sorted(base.rglob("*")):
            rel = f.relative_to(base).as_posix()
            if not f.is_file() or rel == "README.md" or rel.startswith("samples/"):
                continue
            if f.suffix in (".json", ".yaml", ".yml", ".md"):
                out.append(rel)
        return out

    def connection_keys(self) -> set[str]:
        return {c.get("connection_key") for c in self.llm.get("connections") or [] if isinstance(c, dict)}

    def secret_names(self) -> str:
        path = self.root / SECRETS_REGISTER
        return path.read_text(encoding="utf-8") if path.is_file() else ""


# ── checks ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def _str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) and x for x in value)


def surface_matches(pattern: str, entry: str) -> bool:
    """`page:/a/**` matches page:/a and everything below it; otherwise fnmatch on the whole string, where `*` stays
    inside one path segment."""
    if pattern.endswith("/**"):
        base = pattern[:-3]
        return entry == base or entry.startswith(base + "/")
    if "*" not in pattern:
        return pattern == entry
    regex = "^" + re.escape(pattern).replace(r"\*", "[^/]*") + "$"
    return re.match(regex, entry) is not None


def check_conditions(where: str, cond, cat: Catalogue, connections: set[str], secrets_text: str) -> list[str]:
    if cond is None:
        return []
    if not isinstance(cond, dict):
        return [f"{where}: conditions is not a mapping"]
    errs = []
    for k in cond:
        if k not in CONDITION_KEYS:
            errs.append(f"{where}: unknown condition {k} (allowed: {', '.join(CONDITION_KEYS)})")
    for k in ("entitlements", "settings", "connections", "secrets", "tenant_kinds"):
        if k in cond and not _str_list(cond[k]):
            errs.append(f"{where}: conditions.{k} is not a list of names")
    for key in cond.get("settings") or []:
        if key not in cat.surface.get("settings", {}):
            errs.append(f"{where}: setting {key} is in no settings registry (surface snapshot)")
    for key in cond.get("entitlements") or []:
        if key not in cat.surface.get("entitlements", {}):
            errs.append(f"{where}: entitlement {key} is not a plan feature key (shared.entitlement_feature)")
    for key in cond.get("connections") or []:
        if key not in connections:
            errs.append(f"{where}: connection {key} is not an AI gateway connection (llm-routes snapshot)")
    for name in cond.get("secrets") or []:
        if f"`{name}`" not in secrets_text:
            errs.append(f"{where}: secret {name} has no row in docs/security/secrets-register.md")
    for kind in cond.get("tenant_kinds") or []:
        if kind not in TENANT_KINDS:
            errs.append(f"{where}: unknown tenant kind {kind}")
    if "note" in cond and not (isinstance(cond["note"], str) and cond["note"].strip()):
        errs.append(f"{where}: conditions.note is empty")
    return errs


def check(cat: Catalogue) -> list[str]:
    errs: list[str] = []
    for doc, rel in ((cat.features_doc, FEATURES), (cat.integrations_doc, INTEGRATIONS)):
        if doc.get("format") != 1:
            errs.append(f"{rel}: format must be 1")
    connections = cat.connection_keys()
    secrets_text = cat.secret_names()

    # C1 apps
    app_ids = []
    for a in cat.apps:
        aid = a.get("id")
        if aid not in APP_PREFIX:
            errs.append(f"app {aid}: unknown app id (allowed: {', '.join(APP_PREFIX)})")
        for k in ("name", "name_vi", "repo", "summary", "summary_vi", "owner"):
            if not (isinstance(a.get(k), str) and a[k].strip()):
                errs.append(f"app {aid}: {k} missing")
        app_ids.append(aid)
    if len(set(app_ids)) != len(app_ids):
        errs.append("apps: duplicate app id")
    known_apps = set(app_ids)

    # C1 features
    feature_ids: dict[str, dict] = {}
    for f in cat.features:
        fid = f.get("id")
        where = f"feature {fid}"
        if not (isinstance(fid, str) and FEATURE_ID.match(fid)):
            errs.append(f"{where}: id must be <APP>-F<nnn>")
        elif fid in feature_ids:
            errs.append(f"{where}: duplicate id")
        else:
            feature_ids[fid] = f
        app = f.get("app")
        if app not in known_apps:
            errs.append(f"{where}: unknown app {app}")
        elif isinstance(fid, str) and not fid.startswith(APP_PREFIX[app] + "-"):
            errs.append(f"{where}: id prefix does not match app {app} ({APP_PREFIX[app]}-F<nnn>)")
        for k in ("module", "name", "name_vi", "summary"):
            if not (isinstance(f.get(k), str) and f[k].strip()):
                errs.append(f"{where}: {k} missing")
        if not (_str_list(f.get("roles")) and f["roles"]):
            errs.append(f"{where}: roles must be a non-empty list")
        if f.get("status") not in STATUSES:
            errs.append(f"{where}: status must be one of {', '.join(STATUSES)}")
        if f.get("owner") not in OWNERS:
            errs.append(f"{where}: owner must be one of {', '.join(OWNERS)}")
        surface = f.get("surface", [])
        if not _str_list(surface) and surface != []:
            errs.append(f"{where}: surface must be a list")
            surface = []
        for item in surface:
            if not SURFACE_ITEM.match(item):
                errs.append(f"{where}: surface item {item!r} is not page:/<path> or route:<module>")
        if app == "infra" and surface:
            errs.append(f"{where}: an infra feature has no app surface")
        if app not in (None, "infra") and f.get("status") in ("live", "beta") and not surface:
            errs.append(f"{where}: a live or beta app feature needs a surface (its pages or API route groups)")
        errs += check_conditions(where, f.get("conditions"), cat, connections, secrets_text)
        guide = f.get("guide")
        if guide is not None:
            problem = guide_problem(cat.root, guide)
            if problem:
                errs.append(f"{where}: guide {guide} {problem}")

    # C1 integrations
    integration_ids: dict[str, dict] = {}
    named_contracts: set[str] = set()
    endpoints = known_apps | {EXTERNAL}
    for i in cat.integrations:
        iid = i.get("id")
        where = f"integration {iid}"
        if not (isinstance(iid, str) and INTEGRATION_ID.match(iid)):
            errs.append(f"{where}: id must be INT-<nnn>")
        elif iid in integration_ids:
            errs.append(f"{where}: duplicate id")
        else:
            integration_ids[iid] = i
        if i.get("producer") not in endpoints:
            errs.append(f"{where}: unknown producer {i.get('producer')}")
        consumers = i.get("consumers")
        if not (_str_list(consumers) and consumers) or any(c not in endpoints for c in consumers):
            errs.append(f"{where}: consumers must be a non-empty list of app ids or external")
        if i.get("kind") not in KINDS:
            errs.append(f"{where}: kind must be one of {', '.join(KINDS)}")
        if i.get("status") not in STATUSES:
            errs.append(f"{where}: status must be one of {', '.join(STATUSES)}")
        if i.get("owner") not in OWNERS:
            errs.append(f"{where}: owner must be one of {', '.join(OWNERS)}")
        if not isinstance(i.get("personal_data"), bool):
            errs.append(f"{where}: personal_data must be true or false")
        for k in ("name", "auth", "cadence", "failure", "kill_switch"):
            if not (isinstance(i.get(k), str) and i[k].strip()):
                errs.append(f"{where}: {k} missing")
        contracts = i.get("contracts")
        if not isinstance(contracts, list):
            errs.append(f"{where}: contracts must be a list (empty when there is no contract file)")
            contracts = []
        for c in contracts:
            if not (isinstance(c, dict) and isinstance(c.get("file"), str) and isinstance(c.get("version"), str)):
                errs.append(f"{where}: each contract is {{file, version}}")
                continue
            named_contracts.add(c["file"])
            if not (cat.root / CONTRACTS / c["file"]).is_file():
                errs.append(f"{where}: contract {c['file']} does not exist in docs/contracts/")
        if not (_str_list(i.get("features")) and i["features"]):
            errs.append(f"{where}: features must name at least one feature")
        errs += check_conditions(where, i.get("conditions"), cat, connections, secrets_text)

    # C6 references
    for f in cat.features:
        for dep in f.get("depends_on") or []:
            if dep not in feature_ids:
                errs.append(f"feature {f.get('id')}: depends_on {dep} is not a feature")
    for i in cat.integrations:
        for fid in i.get("features") or []:
            if fid not in feature_ids:
                errs.append(f"integration {i.get('id')}: feature {fid} does not exist")

    # C2 contracts coverage
    for rel in cat.contract_files():
        if rel not in named_contracts:
            errs.append(f"contract {rel}: no integration names it (add it to docs/catalogue/integrations.yaml)")

    # C3 UAT
    scenario_ids = set()
    for s in cat.scenarios:
        sid = s.get("id")
        scenario_ids.add(sid)
        feats = s.get("features")
        if feats is not None and not _str_list(feats):
            errs.append(f"UAT {sid}: features is not a list of feature ids")
            continue
        if s.get("status") != "retired" and not feats:
            errs.append(f"UAT {sid}: names no feature id (add \"features\" to tools/uat/catalogue.json)")
        for fid in feats or []:
            if fid not in feature_ids:
                errs.append(f"UAT {sid}: feature {fid} does not exist")

    # C6 journeys
    journey_ids = set()
    for j in cat.journeys:
        jid = j.get("id")
        where = f"journey {jid}"
        if not (isinstance(jid, str) and JOURNEY_ID.match(jid)) or jid in journey_ids:
            errs.append(f"{where}: id must be a unique J-<nn>")
        journey_ids.add(jid)
        for k in ("name", "name_vi", "summary", "summary_vi"):
            if not (isinstance(j.get(k), str) and j[k].strip()):
                errs.append(f"{where}: {k} missing")
        steps = j.get("steps")
        if not (isinstance(steps, list) and steps):
            errs.append(f"{where}: steps must be a non-empty list")
            steps = []
        for n, step in enumerate(steps, 1):
            if not (isinstance(step, dict) and isinstance(step.get("name"), str)
                    and isinstance(step.get("name_vi"), str)):
                errs.append(f"{where} step {n}: name and name_vi required")
                continue
            if not (_str_list(step.get("features")) and step["features"]):
                errs.append(f"{where} step {n}: features required")
            for fid in step.get("features") or []:
                if fid not in feature_ids:
                    errs.append(f"{where} step {n}: feature {fid} does not exist")
            for iid in step.get("integrations") or []:
                if iid not in integration_ids:
                    errs.append(f"{where} step {n}: integration {iid} does not exist")
        for sid in j.get("uat") or []:
            if sid not in scenario_ids:
                errs.append(f"{where}: UAT scenario {sid} does not exist")
        prefix = j.get("uat_prefix")
        if prefix is not None and not any(isinstance(s, str) and s.startswith(prefix) for s in scenario_ids):
            errs.append(f"{where}: uat_prefix {prefix} matches no UAT scenario")

    # C5 surface coverage
    snapshot_apps = cat.surface.get("apps", {})
    for app, entries in snapshot_apps.items():
        patterns = [(f.get("id"), p) for f in cat.features if f.get("app") == app for p in f.get("surface") or []]
        for entry in entries:
            if not any(surface_matches(p, entry) for _, p in patterns):
                errs.append(f"surface {app} {entry}: maps to no feature (add it to a feature's surface)")
        for fid, p in patterns:
            if not any(surface_matches(p, e) for e in entries):
                errs.append(f"feature {fid}: surface {p} matches nothing in the {app} snapshot (stale?)")
    for f in cat.features:
        if f.get("surface") and f.get("app") not in snapshot_apps and f.get("app") != "infra":
            errs.append(f"feature {f.get('id')}: app {f.get('app')} has no surface snapshot")

    # C1 the admin page shows every text value: no internal issue id anywhere in the rows (comments may name them)
    for kind, rows in (("app", cat.apps), ("feature", cat.features), ("integration", cat.integrations),
                       ("journey", cat.journeys)):
        for row in rows:
            if any(ISSUE_ID.search(s) for s in _strings(row)):
                errs.append(f"{kind} {row.get('id')}: a text value names an internal issue id "
                            "(the admin page shows it)")

    # C7 public safety
    for rel in (FEATURES, INTEGRATIONS):
        errs += [f"{rel}: {p}" for p in public_problems((cat.root / rel).read_text(encoding="utf-8"))]
    return errs


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    return []


FRONT_MATTER_ID = re.compile(r"\A---\n(?:.*\n)*?id:\s*([A-Z]+-[0-9]{2}[a-z0-9-]*)\s*\n(?:.*\n)*?---\n")


def guide_problem(root: Path, guide) -> str | None:
    """Why a guide path cannot be opened from the admin page by every admin (None = fine): it must be a published
    docs reader page (a catalog page with a front-matter id, outside the never-published folders) of the staff tier
    (tools/docs/build_docs_reader.py publication rule v1)."""
    if not (isinstance(guide, str) and guide.startswith("docs/") and guide.endswith(".md")):
        return "is not a docs/*.md path"
    path = root / guide
    if not path.is_file():
        return "does not exist"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))
    try:
        from build_docs_reader import OWNER_ONLY_ID_PREFIXES, is_never  # noqa: E402 (sibling tool)
    finally:
        sys.path.pop(0)
    if is_never(guide):
        return "is in a folder the docs reader never publishes"
    m = FRONT_MATTER_ID.match(path.read_text(encoding="utf-8"))
    if not m:
        return "has no front-matter id, so the docs reader does not publish it"
    if m.group(1).startswith(OWNER_ONLY_ID_PREFIXES):
        return f"is an owner-only page ({m.group(1)}): most admins cannot open it"
    return None


def public_problems(text: str) -> list[str]:
    out = []
    if ACCOUNT_ID.search(text):
        out.append("holds a 12-digit number (an AWS account ID?)")
    if ARN.search(text):
        out.append("holds an ARN")
    if EMAIL.search(text):
        out.append("holds an e-mail address")
    return out


# ── bundle ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def _uat_by_feature(cat: Catalogue) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in cat.scenarios:
        if s.get("status") == "retired":
            continue
        for fid in s.get("features") or []:
            out.setdefault(fid, []).append(s["id"])
    return out


def build_bundle(cat: Catalogue, sha: str = "", ref: str = "") -> dict:
    uat = _uat_by_feature(cat)
    settings = cat.surface.get("settings", {})
    used_settings: dict[str, dict] = {}
    links_by_feature: dict[str, list[str]] = {}
    for i in cat.integrations:
        for fid in i.get("features") or []:
            links_by_feature.setdefault(fid, []).append(i["id"])

    def cond(c):
        c = dict(c or {})
        for key in c.get("settings") or []:
            used_settings[key] = settings.get(key, {})
        return c

    features = []
    for f in cat.features:
        features.append({
            "id": f["id"], "app": f["app"], "module": f["module"], "name": f["name"], "name_vi": f["name_vi"],
            "summary": f["summary"], "roles": f["roles"], "status": f["status"], "owner": f["owner"],
            "surface": f.get("surface") or [], "conditions": cond(f.get("conditions")),
            "depends_on": f.get("depends_on") or [], "guide": f.get("guide"),
            "uat": uat.get(f["id"], []), "integrations": links_by_feature.get(f["id"], []),
        })
    integrations = []
    for i in cat.integrations:
        integrations.append({k: i.get(k) for k in (
            "id", "name", "producer", "consumers", "kind", "auth", "cadence", "failure", "kill_switch",
            "personal_data", "features", "owner", "status")} | {
            "contracts": i.get("contracts") or [], "conditions": cond(i.get("conditions"))})
    scenarios = {s["id"]: {"story": s.get("story"), "status": s.get("status"), "app": s.get("app")}
                 for s in cat.scenarios if s.get("features")}
    journeys = []
    for j in cat.journeys:
        ids = list(j.get("uat") or [])
        if j.get("uat_prefix"):
            ids += [s["id"] for s in cat.scenarios if s["id"].startswith(j["uat_prefix"]) and s["id"] not in ids]
        journeys.append({k: j.get(k) for k in ("id", "name", "name_vi", "summary", "summary_vi")} | {
            "steps": j.get("steps") or [], "uat": ids})
    apps = []
    for a in cat.apps:
        own = [f for f in features if f["app"] == a["id"]]
        apps.append({k: a.get(k) for k in ("id", "name", "name_vi", "repo", "kind", "summary", "summary_vi", "owner")}
                    | {"features": len(own), "live": sum(1 for f in own if f["status"] == "live"),
                       "surface": len(cat.surface.get("apps", {}).get(a["id"], []))})
    return {
        "format": BUNDLE_FORMAT,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {"repo": "AA-Ecosys", "sha": sha, "ref": ref},
        "apps": apps,
        "features": features,
        "integrations": integrations,
        "journeys": journeys,
        "scenarios": scenarios,
        "settings": dict(sorted(used_settings.items())),
        "counts": {"features": len(features), "integrations": len(integrations), "journeys": len(journeys),
                   "contracts": len(cat.contract_files()), "uat_linked": len(scenarios)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("check", "bundle"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--sha", default="")
    ap.add_argument("--ref", default="")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    args = ap.parse_args(argv)
    cat = Catalogue(args.root)
    problems = check(cat)
    for p in problems:
        print(f"catalogue: {p}")
    if problems:
        print(f"{len(problems)} problem(s); format and rules: docs/catalogue/README.md")
        return 1
    if args.command == "check":
        print(f"catalogue OK: {len(cat.features)} features, {len(cat.integrations)} integrations, "
              f"{len(cat.journeys)} journeys, {len(cat.contract_files())} contracts covered")
        return 0
    if not args.out:
        ap.error("bundle needs --out")
    bundle = build_bundle(cat, args.sha, args.ref)
    text = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
    leaks = public_problems(text)
    if leaks:
        print("catalogue bundle: " + "; ".join(leaks))
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "catalogue.json").write_text(text, encoding="utf-8")
    print(f"wrote {args.out / 'catalogue.json'} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
