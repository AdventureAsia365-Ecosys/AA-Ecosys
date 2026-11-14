"""AA-1106 — the code surface of every app, as the product catalogue guard sees it.

The catalogue (docs/catalogue/features.yaml) maps each page and API route group of every app to a feature. The app
code lives in five separate repos, so the root repo keeps a committed snapshot of their surface,
docs/catalogue/surface.snapshot.json, the same pattern as docs/generated/llm-routes.snapshot.json:

  page:<url path>     a Next.js page (app/**/page.tsx); route groups "(name)" are dropped, dynamic segments kept
                      as written ("[id]"), the root page is "/"
  route:<module>      a backend route group: a Python router module that declares at least one route
                      (CIS api/routers, Booking backend/app/routers, AA-Partner api/app/routers), a Next.js API
                      route group of TripPlanner ("bff/<first segment under app/api>") or a TripPlanner Lambda
                      ("lambda/<folder>")
  settings            the keys of each settings registry: CIS + TripPlanner (AA-CIS-App
                      shared/settings/compiled_defaults.json), CRM (AA-Partner api/app/platform_settings/
                      compiled_defaults.json), Booking pricing policy (AA-Booking backend/app/pricing/policy_params.py,
                      named "booking.policy.<key>")
  entitlements        the plan feature keys of shared.entitlement_feature (CIS migrations)

Commands (standard library only):

  python tools/catalogue/surface.py refresh --apps-root <workspace>      rewrite the snapshot from the checkouts
  python tools/catalogue/surface.py check --apps-root <workspace>        exit 1 when the snapshot is stale

<workspace> holds apps/AA-CIS-App, apps/AA-Booking, apps/AA-Partner and apps/AA-TripPlanner-Web (a laptop workspace,
or the nightly CI job that checks the four public repos out side by side). Names only: no value, no account ID.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO_ROOT / "docs" / "catalogue" / "surface.snapshot.json"
SCHEMA = 1

# app id -> (repo folder under apps/, frontend app dirs, router dirs)
APPS = {
    "cis": ("AA-CIS-App", ["frontend/app"], ["api/routers"]),
    "booking": ("AA-Booking", ["frontend/app"], ["backend/app/routers"]),
    "crm": ("AA-Partner", ["web/app"], ["api/app/routers"]),
    "tripplanner": ("AA-TripPlanner-Web", ["frontend/app"], []),
}
SKIP_DIRS = {"node_modules", ".next", "__pycache__", "api"}
ROUTE_DECORATOR = re.compile(r"^\s*@\w+\.(?:get|post|put|patch|delete|api_route)\(", re.M)
PARAM_KEY = re.compile(r"Param\(\s*\"([a-z0-9_]+)\"")
ENTITLEMENT_ROW = re.compile(
    r"^\s*\('([a-z][a-z0-9_]*\.[a-z0-9_.]+)',\s*'([a-z]+)',\s*'(flag|limit|seats|policy)'", re.M)


def page_route(rel_dir: str) -> str:
    """URL path of a Next.js page folder relative to app/: route groups dropped, '/' for the root."""
    parts = [p for p in rel_dir.split("/") if p and p != "." and not (p.startswith("(") and p.endswith(")"))]
    return "/" + "/".join(parts)


def pages(app_dir: Path) -> list[str]:
    out = set()
    if not app_dir.is_dir():
        return []
    for f in app_dir.rglob("page.tsx"):
        rel = f.parent.relative_to(app_dir).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        out.add(page_route(rel))
    return sorted(out)


def routers(router_dir: Path) -> list[str]:
    out = []
    if not router_dir.is_dir():
        return out
    for f in sorted(router_dir.rglob("*.py")):
        rel = f.relative_to(router_dir).as_posix()
        if "__pycache__" in rel or any(part.startswith("_") for part in rel.split("/")):
            continue
        if ROUTE_DECORATOR.search(f.read_text(encoding="utf-8", errors="replace")):
            out.append(rel[:-3])
    return out


def tripplanner_api(repo: Path) -> list[str]:
    out = set()
    api = repo / "frontend" / "app" / "api"
    if api.is_dir():
        for f in api.rglob("route.ts"):
            first = f.parent.relative_to(api).as_posix().split("/")[0]
            out.add(f"bff/{first}")
    backend = repo / "backend"
    if backend.is_dir():
        for d in backend.iterdir():
            if d.is_dir() and (d / "handler.py").is_file():
                out.add(f"lambda/{d.name}")
    return sorted(out)


def registry_keys(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {d["key"]: {"app": d.get("app"), "area": d.get("area")} for d in data.get("definitions", [])}


def collect(apps_root: Path) -> dict:
    root = apps_root / "apps" if (apps_root / "apps").is_dir() else apps_root
    out: dict = {"schema": SCHEMA, "apps": {}, "settings": {}, "entitlements": {}}
    missing = []
    for app, (folder, fe_dirs, router_dirs) in APPS.items():
        repo = root / folder
        if not repo.is_dir():
            missing.append(folder)
            continue
        surface = []
        for d in fe_dirs:
            surface += [f"page:{p}" for p in pages(repo / d)]
        for d in router_dirs:
            surface += [f"route:{r}" for r in routers(repo / d)]
        if app == "tripplanner":
            surface += [f"route:{r}" for r in tripplanner_api(repo)]
        out["apps"][app] = sorted(set(surface))
    if missing:
        raise SystemExit(f"missing app checkouts under {root}: {', '.join(missing)}")
    settings = {}
    settings.update(registry_keys(root / "AA-CIS-App" / "shared" / "settings" / "compiled_defaults.json"))
    settings.update(registry_keys(root / "AA-Partner" / "api" / "app" / "platform_settings" / "compiled_defaults.json"))
    policy = root / "AA-Booking" / "backend" / "app" / "pricing" / "policy_params.py"
    if policy.is_file():
        for key in PARAM_KEY.findall(policy.read_text(encoding="utf-8")):
            settings[f"booking.policy.{key}"] = {"app": "booking", "area": "pricing_policy"}
    out["settings"] = dict(sorted(settings.items()))
    ents = {}
    for mig in sorted((root / "AA-CIS-App" / "api" / "migrations").glob("*.sql")):
        text = mig.read_text(encoding="utf-8", errors="replace")
        if "INSERT INTO shared.entitlement_feature" not in text:
            continue
        for key, product, kind in ENTITLEMENT_ROW.findall(text):
            ents[key] = {"product": product, "kind": kind}
    out["entitlements"] = dict(sorted(ents.items()))
    return out


def dumps(snapshot: dict) -> str:
    return json.dumps(snapshot, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def load(path: Path = SNAPSHOT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diff(old: dict, new: dict) -> list[str]:
    """One line per difference between two snapshots (empty = same)."""
    lines = []
    for app in sorted(set(old.get("apps", {})) | set(new.get("apps", {}))):
        a, b = set(old.get("apps", {}).get(app, [])), set(new.get("apps", {}).get(app, []))
        lines += [f"{app}: new {s}" for s in sorted(b - a)] + [f"{app}: gone {s}" for s in sorted(a - b)]
    for part in ("settings", "entitlements"):
        a, b = set(old.get(part, {})), set(new.get(part, {}))
        lines += [f"{part}: new {k}" for k in sorted(b - a)] + [f"{part}: gone {k}" for k in sorted(a - b)]
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("refresh", "check"))
    ap.add_argument("--apps-root", required=True, type=Path)
    ap.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = ap.parse_args(argv)
    new = collect(args.apps_root)
    if args.command == "refresh":
        args.snapshot.write_text(dumps(new), encoding="utf-8")
        print(f"wrote {args.snapshot}: " + ", ".join(f"{a} {len(s)}" for a, s in new["apps"].items())
              + f", {len(new['settings'])} settings, {len(new['entitlements'])} entitlements")
        return 0
    old = load(args.snapshot) if args.snapshot.is_file() else {}
    lines = diff(old, new)
    for line in lines:
        print(f"surface drift: {line}")
    if lines:
        print("The committed surface snapshot is stale: run `python tools/catalogue/surface.py refresh --apps-root "
              "<workspace>`, map every new entry to a feature in docs/catalogue/features.yaml, and commit both.")
        return 1
    print("surface snapshot is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
