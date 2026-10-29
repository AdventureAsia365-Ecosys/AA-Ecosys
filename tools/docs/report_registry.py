#!/usr/bin/env python3
"""Report registry: import and lint of docs/reports/catalog.yaml and docs/reports/kpis.yaml (AA-1003 R1).

The registry is the machine-readable list of every recurring report (catalog.yaml) and of every KPI those reports
show (kpis.yaml). It was imported once from the AA-1001 advisory (docs/audits/2026-10-29-S258-report-catalog/
catalog.json, the 63-report catalog) and is edited by hand from then on: the YAML is the source of truth, the
advisory JSON is history. The CIS report engine (AA-CIS-App services/reports/, job kinds kpi_snapshot_daily and
report_generate, page /admin/reports) reads a byte copy of both files.

Subcommands
-----------
  check   (default) lint the two files; run by the root Docs lint workflow on every docs PR:
            * shape: required fields, unique IDs, allowed values (family, schedule, automation, status, priority,
              generator, unit);
            * every KPI a report lists exists in kpis.yaml, and each KPI's used_by is exactly the reports that list it;
            * every template path exists in this repo;
            * every DB relation a KPI names in `sources` is a table or view of docs/architecture/db-schema-reference.md
              (the live dump), or is listed in `planned_sources` (proposed, not built yet). A planned source that the
              dump now has is a warning (move it out of the list), never an error: the schema-dump bot PR changes the
              reference and must not fail on it.
            --copy DIR also compares the two files byte for byte with the copies in DIR (the CIS vendored copy:
            apps/AA-CIS-App/services/reports/registry/).
  import  rebuild both files from the advisory catalog.json (one-off; kept so the import is reproducible). It
          overwrites hand edits, so it refuses to run when the files exist unless --force is given.

Stdlib + PyYAML (tools/docs/requirements.txt).

Usage:
  python tools/docs/report_registry.py check
  python tools/docs/report_registry.py check --copy apps/AA-CIS-App/services/reports/registry
  python tools/docs/report_registry.py import --force
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from docslib import REPO_ROOT, Finding

CATALOG = "docs/reports/catalog.yaml"
KPIS = "docs/reports/kpis.yaml"
SCHEMA_REFERENCE = "docs/architecture/db-schema-reference.md"
ADVISORY_DIR = "docs/audits/2026-10-29-S258-report-catalog"
ADVISORY_JSON = f"{ADVISORY_DIR}/catalog.json"

REPORT_ID = re.compile(r"^[A-Z]{2,4}-\d{2}$")
KPI_ID = re.compile(r"^K-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
FAMILIES = ("executive", "finops", "app-ops", "ai-quality", "reliability", "security", "incident", "release",
            "data-quality", "growth", "customer", "agency", "readiness", "on-demand")
SCHEDULES = ("hourly", "daily", "weekly", "monthly", "quarterly", "live", "event", "on_demand")
AUTOMATION = ("auto", "semi", "manual", "on_demand")
STATUSES = ("exists", "partial", "planned", "missing")
PRIORITIES = ("P0", "P1", "P2", "P3")
GENERATORS = (None, "cis")
UNITS = ("count", "ratio", "usd", "seconds", "hours", "days", "score", "status", "text")
REPORT_FIELDS = ("id", "family", "name_en", "name_vi", "audience", "owner_role", "decision", "cadence", "schedule",
                 "channel", "automation", "status", "priority", "template", "generator", "kpis", "sections")
KPI_FIELDS = ("id", "version", "name", "definition", "unit", "threshold", "sources", "defined_in", "used_by")
DB_SCHEMAS = ("shared", "booking", "tripplanner", "crm", "gold_aa_internal", "silver_aa_internal", "acp_shared",
              "acp_contract", "acp_deliver", "catalog", "geo")
# schema.relation in prose; a contract name (crm.ops.v1, catalog.http.v1) is not a relation.
RELATION = re.compile(r"(?<![\w.])(" + "|".join(DB_SCHEMAS) + r")\.([a-z_][a-z0-9_]*)(?![\w]*\.v\d)")
REFERENCE_HEADING = re.compile(r"^### `([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*)`")

HEADER_CATALOG = """\
# Report registry: every recurring report of the AA ecosystem (AA-1003 R1; catalog from the AA-1001 advisory).
#
# Source of truth for report IDs, cadence, owner role, channel and template. Edit by hand; the lint
# (tools/docs/report_registry.py check, root Docs lint) checks the shape, the KPI references (kpis.yaml) and the
# template paths. The CIS report engine reads a byte copy (AA-CIS-App services/reports/registry/catalog.yaml):
# change both in the same session (the CIS copy in its own PR).
#
# Fields: id, family, name_en, name_vi, audience, owner_role, decision (what the reader decides with it), cadence
# (words), schedule (one of hourly/daily/weekly/monthly/quarterly/live/event/on_demand), channel, automation
# (auto/semi/manual/on_demand), status (state of the report today: exists/partial/planned/missing), priority (P0-P3),
# template (path of its Markdown template, or null for a product page), generator (cis = the CIS engine renders it
# with job kind report_generate; null = not automated yet), kpis (IDs in kpis.yaml), sections (what it contains).
"""

HEADER_KPIS = """\
# KPI registry: every KPI the reports of catalog.yaml show (AA-1003 R1; imported from the AA-1001 advisory).
#
# One entry per KPI ID. A KPI is defined once (defined_in = the report that owns the definition) and reused by the
# reports in used_by. `sources` lists the DB tables and views the definition reads; the lint checks each against
# docs/architecture/db-schema-reference.md, except the names in planned_sources (proposed, not built yet).
# `unit` was inferred at import for KPIs nothing computes yet: correct it when the KPI is built. `snapshot` says which
# job writes the KPI's daily value to shared.kpi_daily (scope keys: all, app:<app>, provider:<provider>), and
# `alert` the value bounds a generated report colours (amber_gte / red_gte); a threshold in words stays in `threshold`.
# Edit by hand; the CIS report engine reads a byte copy (AA-CIS-App services/reports/registry/kpis.yaml).
"""

# automation-plan.md section 6: family template -> the report IDs it is used by (ranges expanded).
TEMPLATE_DIR = f"{ADVISORY_DIR}/templates"
FAMILY_TEMPLATE = {
    "executive": "business-review.md", "finops": "cost-finops-review.md", "app-ops": "app-ops-report.md",
    "ai-quality": "ai-content-quality.md", "reliability": "slo-db-performance.md", "security": "security-review.md",
    "incident": "incident-postmortem.md", "release": "delivery-dora-report.md", "data-quality": "data-quality-report.md",
    "growth": "customer-growth-report.md", "customer": "customer-growth-report.md", "readiness": "readiness-signoff.md",
}
TEMPLATE_USED_BY = {
    "business-review.md": "EX-01 EX-02 EX-05",
    "cost-finops-review.md": "FI-01 FI-03 FI-05 FI-06 FI-07 BK-03",
    "app-ops-report.md": "CIS-01 CIS-03 TP-01 BK-01 BK-02 BK-04 BK-05 BK-06 OPS-14 OPS-15",
    "ai-content-quality.md": "CIS-05 CIS-06 CIS-07",
    "slo-db-performance.md": "OPS-13 OPS-14 DATA-02",
    "security-review.md": "SEC-03 SEC-08 SEC-09 SEC-10",
    "incident-postmortem.md": "OPS-04",
    "delivery-dora-report.md": "DEV-01 DEV-02 DEV-03",
    "data-quality-report.md": "DATA-01 DATA-02 DATA-03 DATA-04 TP-03 CIS-02",
    "customer-growth-report.md": "MKT-01 MKT-02 EX-07 CX-01",
    "readiness-signoff.md": "OPS-17 DEV-04 SEC-10",
}
# Reports the CIS engine renders in R1 (README section 7: EX-04 scorecard, EX-06 register).
CIS_GENERATED = ("EX-04", "EX-06")

# Display names of the KPIs the catalog lists only as a pair of IDs ("K-TP-TRIPS / K-TP-INQ").
SPLIT_NAMES = {"K-TP-TRIPS": "TripPlanner trips started", "K-TP-INQ": "TripPlanner inquiries sent",
               "K-BK-INQ": "Booking inquiries received", "K-BK-CONF": "Booking cases confirmed"}

# KPIs the CIS job kpi_snapshot_daily computes from its own tables in R1 (CIS-owned data only; Booking, TripPlanner
# and CRM values come in later slices through their contract views). The definition here is what the job computes.
SNAPSHOT_KPIS: dict[str, dict[str, Any]] = {
    "K-JOB-FAIL": {
        "unit": "count",
        "snapshot": {"job": "kpi_snapshot_daily", "scopes": ["app:cis"],
                     "computes": "shared.job rows with status failed and finished_at in the ICT day (app:cis); "
                                 "booking.job, tripplanner.job and crm.job join in a later slice"},
        "alert": {"amber_gte": 1, "red_gte": 5},
    },
    "K-JOB-QUEUEAGE": {
        "unit": "seconds",
        "snapshot": {"job": "kpi_snapshot_daily", "scopes": ["app:cis"],
                     "computes": "p95 of started_at - greatest(created_at, run_after) over shared.job rows started in "
                                 "the ICT day (all kinds; the per-kind split stays in OPS-14)"},
        "alert": {"amber_gte": 300},
    },
    "K-LLM-COST-DAY": {
        "unit": "usd",
        "snapshot": {"job": "kpi_snapshot_daily", "scopes": ["all", "app:<app>", "provider:<provider>"],
                     "computes": "sum shared.llm_call_log.cost_usd with created_at in the ICT day, in total, by app "
                                 "(quality_signal.app, default cis) and by provider; shadow calls included (the ledger "
                                 "has no shadow column; shared.llm_call_daily is the rollup of days older than the "
                                 "180-day raw window, outside the 90-day backfill)"},
    },
    "K-LLM-FALLBACK-24H": {
        "unit": "ratio",
        "snapshot": {"job": "kpi_snapshot_daily", "scopes": ["all"],
                     "computes": "shared.llm_call_log rows with fallback_used / all rows, created_at in the ICT day "
                                 "(no value on a day without calls)"},
        "alert": {"red_gte": 0.05},
    },
    "K-CAT-LIVE": {
        "unit": "count",
        "snapshot": {"job": "kpi_snapshot_daily", "scopes": ["all"],
                     "computes": "rows of gold_aa_internal.v_tour_liveness with state 'live' when the job runs (a "
                                 "point-in-time count: written for the latest day only, never back-filled)"},
    },
    "K-RPT-FAILED": {
        "unit": "count",
        "snapshot": {"job": "kpi_snapshot_daily", "scopes": ["all"],
                     "computes": "shared.report_run rows with status failed and finished_at in the 7 ICT days ending "
                                 "with the day"},
        "alert": {"red_gte": 1},
    },
}


# ── import ──────────────────────────────────────────────────────────────────────────────────────────────────────


def _expand(ids: str) -> list[str]:
    return ids.split()


def template_for(report: dict) -> str | None:
    rid, family = report["id"], report["family"]
    using = [t for t, ids in TEMPLATE_USED_BY.items() if rid in _expand(ids)]
    if not using:
        return None
    pick = FAMILY_TEMPLATE.get(family) if FAMILY_TEMPLATE.get(family) in using else using[0]
    return f"{TEMPLATE_DIR}/{pick}"


def schedule_of(cadence: str) -> str:
    c = cadence.strip().lower()
    for word, value in (("on demand", "on_demand"), ("hourly", "hourly"), ("daily", "daily"), ("nightly", "daily"),
                        ("weekly", "weekly"), ("monthly", "monthly"), ("quarterly", "quarterly"), ("live", "live"),
                        ("event", "event"), ("every session", "event"), ("when ", "event")):
        if c.startswith(word):
            return value
    return "event"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", text.upper()).strip("-")


def _unit_guess(name: str, definition: str) -> str:
    n = name.lower()
    if any(w in n for w in ("usd", "cost", "spend", "mrr", "gmv", "cash", "revenue", "value", "amount", "billable")):
        if not any(w in n for w in ("vs budget", "/ budget", "accuracy", "share", "margin", "variance", "trend")):
            return "usd"
    if any(w in n for w in ("(days)", "runway", "dso")):
        return "days"
    if any(w in n for w in ("lcp", "p95", "latency", "duration")):
        return "seconds"
    if any(w in n for w in ("time to", "lead time", "age", "ttr", "ttd")):
        return "hours"
    if any(w in n for w in ("rate", "share", "coverage", "accuracy", "ratio", "margin", "utilisation", "vs ",
                            "variance", "pass", "on time", "depth", "conversion", " to ", "csat", "%", "/")):
        return "ratio"
    if any(w in n for w in ("score", "kappa", "nps")):
        return "score"
    if any(w in n for w in ("status", "flag", "verify", "mix", "reasons", "buckets", "events", "readiness",
                            "trend", "health")):
        return "status"
    return "count"


def _sources(definition: str) -> list[str]:
    out: list[str] = []
    for m in RELATION.finditer(definition):
        name = f"{m.group(1)}.{m.group(2)}"
        if name not in out:
            out.append(name)
    return out


def _split_kpi(raw_name: str, rid: str) -> list[tuple[str, str]]:
    """[(kpi_id, display name)] of one catalog KPI name: 'K-X Name', 'K-A / K-B', or a bare name (agency reports)."""
    name = raw_name.replace("(canonical definition)", "").strip()
    if name.startswith("K-"):
        ids = re.findall(r"K-[A-Z0-9]+(?:-[A-Z0-9]+)*", name)
        rest = re.sub(r"K-[A-Z0-9]+(?:-[A-Z0-9]+)*", "", name).replace("/", "").strip()
        if len(ids) > 1:
            return [(i, SPLIT_NAMES.get(i, i)) for i in ids]
        return [(ids[0], rest or ids[0])]
    return [(f"K-{rid.replace('-', '')}-{_slug(name)}", name)]


def build(catalog: list[dict], reference: set[str]) -> tuple[dict, dict]:
    kpis: dict[str, dict] = {}
    named: dict[tuple[str, str], str] = {}     # (report id, bare name) -> kpi id, for "Defined in CRM-01"
    report_kpis: dict[str, list[str]] = {}
    pending_refs: list[tuple[str, str, str]] = []
    for r in catalog:
        refs: list[str] = []
        for k in r["kpis"]:
            for kid, display in _split_kpi(k["name"], r["id"]):
                definition = k["definition"].strip()
                is_ref = bool(re.match(r"^Defined (once )?in [A-Z]{2,4}-\d{2}\b", definition))
                if not k["name"].startswith("K-"):
                    target = re.match(r"^Defined (?:once )?in ([A-Z]{2,4}-\d{2})", definition)
                    if target:
                        pending_refs.append((r["id"], display, target.group(1)))
                        refs.append(f"@{target.group(1)}:{display}")
                        continue
                    named[(r["id"], display)] = kid
                canonical = "(canonical definition)" in k["name"]
                entry = kpis.get(kid)
                if entry is None:
                    entry = kpis[kid] = {"id": kid, "version": 1, "name": display, "definition": None, "unit": None,
                                         "threshold": None, "sources": [], "defined_in": None, "used_by": [],
                                         "_canonical": False, "_thresholds": {}}
                entry["_thresholds"][r["id"]] = k["target_or_threshold"].strip()
                if not is_ref and (entry["definition"] is None or (canonical and not entry["_canonical"])):
                    entry.update(definition=definition, defined_in=r["id"], name=display,
                                 threshold=k["target_or_threshold"].strip(), _canonical=canonical)
                if kid not in refs:
                    refs.append(kid)
        report_kpis[r["id"]] = refs
    # resolve "Defined in <report>" of the bare-named agency KPIs
    for rid, refs in report_kpis.items():
        out = []
        for ref in refs:
            if ref.startswith("@"):
                target, display = ref[1:].split(":", 1)
                ref = named.get((target, display)) or f"K-{target.replace('-', '')}-{_slug(display)}"
            if ref not in out:
                out.append(ref)
        report_kpis[rid] = out
    for rid, refs in report_kpis.items():
        for kid in refs:
            if rid not in kpis[kid]["used_by"]:
                kpis[kid]["used_by"].append(rid)
    planned: dict[str, str] = {}
    out_kpis = []
    for kid in sorted(kpis):
        e = kpis[kid]
        if e["definition"] is None:      # only ever referenced: keep the first report's words
            first = e["used_by"][0]
            e.update(definition=f"Not defined in the catalog yet (first used by {first})", defined_in=first,
                     threshold=e["_thresholds"][first])
        e["sources"] = _sources(e["definition"])
        e["unit"] = _unit_guess(e["name"], e["definition"])
        extra = {rid: t for rid, t in e["_thresholds"].items() if rid != e["defined_in"] and t != e["threshold"]}
        item = {k: e[k] for k in KPI_FIELDS}
        if extra:
            item["report_thresholds"] = extra
        snap = SNAPSHOT_KPIS.get(kid)
        if snap:
            item["unit"] = snap["unit"]
            item["snapshot"] = snap["snapshot"]
            if "alert" in snap:
                item["alert"] = snap["alert"]
            for s in _sources(snap["snapshot"]["computes"]):
                if s not in item["sources"]:
                    item["sources"].append(s)
        for s in item["sources"]:
            if s not in reference:
                planned.setdefault(s, f"named by {kid}; not in {SCHEMA_REFERENCE} at import (proposed in the catalog)")
        out_kpis.append(item)
    reports = []
    for r in catalog:
        reports.append({
            "id": r["id"], "family": r["family"], "name_en": r["name_en"], "name_vi": r["name_vi"],
            "audience": r["audience"], "owner_role": r["owner_role"], "decision": r["decision"],
            "cadence": r["cadence"], "schedule": schedule_of(r["cadence"]), "channel": r["channel"],
            "automation": r["automation"], "status": r["status_today"], "priority": r["priority"],
            "template": template_for(r), "generator": "cis" if r["id"] in CIS_GENERATED else None,
            "kpis": report_kpis[r["id"]], "sections": r["sections"],
        })
    catalog_doc = {"version": 1, "imported_from": ADVISORY_JSON, "reports": reports}
    kpis_doc = {"version": 1, "imported_from": ADVISORY_JSON,
                "planned_sources": [{"name": n, "reason": planned[n]} for n in sorted(planned)],
                "kpis": out_kpis}
    return catalog_doc, kpis_doc


# Person handles in the advisory text: the registry is vendored into the public CIS repo, so it names roles only.
REPLACEMENTS = (("@thule mention node", "business owner mention node"),)


def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        for old, new in REPLACEMENTS:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    return value


def dump(doc: dict, header: str) -> str:
    body = yaml.safe_dump(_scrub(doc), sort_keys=False, allow_unicode=True, width=118, default_flow_style=False)
    return header + "\n" + body


# ── check ───────────────────────────────────────────────────────────────────────────────────────────────────────


def reference_relations(root: Path) -> set[str]:
    path = root / SCHEMA_REFERENCE
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = REFERENCE_HEADING.match(line)
        if m:
            out.add(m.group(1))
    return out


def _load(path: Path, findings: list[Finding], rel: str) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(Finding(rel, 1, "Report registry", f"{rel} is missing"))
    except yaml.YAMLError as e:
        findings.append(Finding(rel, 1, "Report registry", f"{rel} is not valid YAML: {e}"))
    return None


def check(root: Path, copy_dir: Path | None = None) -> tuple[list[Finding], list[Finding]]:
    """(errors, warnings) of the registry under `root`."""
    errors: list[Finding] = []
    warnings: list[Finding] = []
    cat = _load(root / CATALOG, errors, CATALOG)
    kp = _load(root / KPIS, errors, KPIS)
    if not isinstance(cat, dict) or not isinstance(kp, dict):
        if cat is not None or kp is not None:
            errors.append(Finding(CATALOG, 1, "Report registry", "both files must be YAML mappings"))
        return errors, warnings

    def err(path: str, msg: str) -> None:
        errors.append(Finding(path, 1, "Report registry", msg))

    for doc, path in ((cat, CATALOG), (kp, KPIS)):
        if doc.get("version") != 1:
            err(path, "version must be 1")
    reports = cat.get("reports")
    kpis = kp.get("kpis")
    if not isinstance(reports, list) or not reports:
        err(CATALOG, "reports must be a non-empty list")
        reports = []
    if not isinstance(kpis, list) or not kpis:
        err(KPIS, "kpis must be a non-empty list")
        kpis = []

    kpi_by_id: dict[str, dict] = {}
    for k in kpis:
        kid = k.get("id") if isinstance(k, dict) else None
        if not isinstance(kid, str) or not KPI_ID.match(kid):
            err(KPIS, f"KPI id {kid!r} must match {KPI_ID.pattern}")
            continue
        if kid in kpi_by_id:
            err(KPIS, f"KPI {kid} is listed twice")
        kpi_by_id[kid] = k
        missing = [f for f in KPI_FIELDS if f not in k]
        if missing:
            err(KPIS, f"KPI {kid} lacks {', '.join(missing)}")
        for f in ("name", "definition", "threshold"):
            if f in k and (not isinstance(k[f], str) or not k[f].strip()):
                err(KPIS, f"KPI {kid}: {f} must be a non-empty string")
        if k.get("unit") not in UNITS:
            err(KPIS, f"KPI {kid}: unit {k.get('unit')!r} is not one of {', '.join(UNITS)}")
        if not isinstance(k.get("version"), int) or k.get("version", 0) < 1:
            err(KPIS, f"KPI {kid}: version must be an integer >= 1")
        if not isinstance(k.get("sources"), list):
            err(KPIS, f"KPI {kid}: sources must be a list")
        alert = k.get("alert")
        if alert is not None and (not isinstance(alert, dict) or not alert
                                  or set(alert) - {"amber_gte", "red_gte"}
                                  or not all(isinstance(v, (int, float)) for v in alert.values())):
            err(KPIS, f"KPI {kid}: alert takes only numeric amber_gte / red_gte")
        snap = k.get("snapshot")
        if snap is not None and (not isinstance(snap, dict) or not snap.get("job") or not snap.get("scopes")):
            err(KPIS, f"KPI {kid}: snapshot needs job and scopes")

    report_ids: dict[str, dict] = {}
    for r in reports:
        rid = r.get("id") if isinstance(r, dict) else None
        if not isinstance(rid, str) or not REPORT_ID.match(rid):
            err(CATALOG, f"report id {rid!r} must match {REPORT_ID.pattern}")
            continue
        if rid in report_ids:
            err(CATALOG, f"report {rid} is listed twice")
        report_ids[rid] = r
        missing = [f for f in REPORT_FIELDS if f not in r]
        if missing:
            err(CATALOG, f"report {rid} lacks {', '.join(missing)}")
        for field, allowed in (("family", FAMILIES), ("schedule", SCHEDULES), ("automation", AUTOMATION),
                               ("status", STATUSES), ("priority", PRIORITIES), ("generator", GENERATORS)):
            if field in r and r[field] not in allowed:
                err(CATALOG, f"report {rid}: {field} {r[field]!r} is not one of {', '.join(map(str, allowed))}")
        for f in ("name_en", "name_vi", "owner_role", "cadence", "channel"):
            if f in r and (not isinstance(r[f], str) or not r[f].strip()):
                err(CATALOG, f"report {rid}: {f} must be a non-empty string")
        tpl = r.get("template")
        if tpl is not None and (not isinstance(tpl, str) or not (root / tpl).is_file()):
            err(CATALOG, f"report {rid}: template {tpl!r} does not exist")
        refs = r.get("kpis")
        if not isinstance(refs, list):
            err(CATALOG, f"report {rid}: kpis must be a list")
            continue
        for kid in refs:
            if kid not in kpi_by_id:
                err(CATALOG, f"report {rid} lists KPI {kid}, which kpis.yaml does not define")

    for kid, k in kpi_by_id.items():
        listed_by = sorted(rid for rid, r in report_ids.items() if kid in (r.get("kpis") or []))
        used_by = sorted(k.get("used_by") or [])
        if used_by != listed_by:
            err(KPIS, f"KPI {kid}: used_by {used_by} differs from the reports that list it {listed_by}")
        if k.get("defined_in") not in report_ids:
            err(KPIS, f"KPI {kid}: defined_in {k.get('defined_in')!r} is not a report of catalog.yaml")

    reference = reference_relations(root)
    planned_list = kp.get("planned_sources") or []
    planned = {p.get("name") for p in planned_list if isinstance(p, dict)}
    if not reference:
        warnings.append(Finding(KPIS, 1, "Report registry", f"{SCHEMA_REFERENCE} not found: sources not checked"))
    else:
        for kid, k in kpi_by_id.items():
            for s in k.get("sources") or []:
                if s not in reference and s not in planned:
                    err(KPIS, f"KPI {kid}: source {s} is not in {SCHEMA_REFERENCE} (typo, or add it to "
                              f"planned_sources with a reason)")
        for name in sorted(n for n in planned if n in reference):
            warnings.append(Finding(KPIS, 1, "Report registry",
                                    f"planned source {name} is in {SCHEMA_REFERENCE} now: remove it from "
                                    f"planned_sources"))

    if copy_dir is not None:
        for name, path in (("catalog.yaml", CATALOG), ("kpis.yaml", KPIS)):
            other = copy_dir / name
            if not other.exists() or other.read_bytes() != (root / path).read_bytes():
                err(path, f"{other} is not a byte copy of {path}")
    return errors, warnings


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", nargs="?", default="check", choices=("check", "import"))
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--copy", type=Path, default=None, help="directory holding a vendored copy to compare (check)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files (import)")
    args = ap.parse_args(argv)
    root = args.root
    if args.command == "import":
        targets = [root / CATALOG, root / KPIS]
        if any(t.exists() for t in targets) and not args.force:
            print("the registry exists and is edited by hand; pass --force to overwrite it", file=sys.stderr)
            return 2
        catalog = json.loads((root / ADVISORY_JSON).read_text(encoding="utf-8"))
        cat_doc, kpi_doc = build(catalog, reference_relations(root))
        targets[0].parent.mkdir(parents=True, exist_ok=True)
        targets[0].write_text(dump(cat_doc, HEADER_CATALOG), encoding="utf-8")
        targets[1].write_text(dump(kpi_doc, HEADER_KPIS), encoding="utf-8")
        print(f"wrote {CATALOG} ({len(cat_doc['reports'])} reports) and {KPIS} ({len(kpi_doc['kpis'])} KPIs, "
              f"{len(kpi_doc['planned_sources'])} planned sources)")
        return 0
    errors, warnings = check(root, args.copy)
    for w in warnings:
        print(w.annotate("warning"))
    for e in errors:
        print(e.annotate("error"))
    if errors:
        print(f"report registry: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"report registry: ok ({CATALOG}, {KPIS})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
