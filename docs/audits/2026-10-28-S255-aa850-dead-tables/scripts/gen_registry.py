#!/usr/bin/env python3
"""AA-850: render the registry table from scan.json + sqlctx.json + the manual verdicts below."""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
o = json.loads((HERE / "scan.json").read_text())
ctx = json.loads((HERE / "sqlctx.json").read_text())

# Files that list every table on purpose (inventories, guards, registries): a hit there is not a use.
CATALOGUE = {"services/erasure/inventory.py", "services/erasure/plan.py", "api/services/data_coverage/registry.py",
             "db/rls_catalogue_rules.py", "db/isolation_probe.py", "db/owners.yaml", "db/schema_drift_decisions.json",
             "api/services/data_coverage/queries.py"}
# data_coverage/queries.py does run SELECTs (the admin Data coverage page): counted as a use for the v_ops views below.
DATA_COVERAGE_READS = {"booking.v_ops_data_totals", "booking.v_ops_trip_plan_keys", "tripplanner.v_ops_data_totals",
                       "tripplanner.v_ops_pin_components", "tripplanner.v_ops_component_id_map",
                       "shared.v_tour_photos", "shared.v_destination_photos"}

REPO_OF = {"booking": "AA-Booking", "tripplanner": "AA-TripPlanner-Web", "crm": "AA-Partner", "public": "platform (Infra roles/)"}

W1 = "**dead** (wave 1)"
OVR = {
    "acp_contract.atom_decompose_jobs": (W1, "quarantine (wave 1)",
        "AA-302 Bedrock Batch decompose tracker (081/082); the batch path is gone; migrations + docs only"),
    "acp_contract.s1_from_atom_runs": (W1, "quarantine (wave 1)",
        "AA-289 S1-from-atom run log (088); only a docstring mention in admin_pipeline.py; FK to raw_tours"),
    "acp_contract.route_pick": (W1, "quarantine (wave 1)",
        "writer create_route_pick() retired with the route hub (AA-859 wave 4); api/main.py itself calls it a Dead Table Registry candidate"),
    "acp_shared.marketplace_portfolios": (W1, "quarantine (wave 1)",
        "pre-tenant portfolio drafts (097); flow removed by ADR-2026-038 / 119; CIS 265: 'stay revoked and dead'; no FK points at it on Dev"),
    "acp_shared.tenant_atom_state": (W1, "quarantine (wave 1)",
        "N1 seeding state (098); not part of onboarding since AA-472 (admin.py docstring); CIS 265: 'dead'; 2 integration tests name it"),
    "shared.acp_runs": (W1, "quarantine (wave 1)",
        "legacy run table (009); 0 rows ever written (services/export/handler.py comment, AA-492); test_aa751 guards against readers"),
    "shared.tenant_brand_rule_versions": (W1, "quarantine (wave 1)",
        "AA-82 brand-rule history (019); no writer or reader in any repo"),
    "shared.tenant_brand_rules_deleted_aa404": (W1, "quarantine (wave 1); archive rows to S3 before the drop",
        "AA-404 backup copy of 6 mis-attached demo brand rows (104); no reader"),
    "shared.v_batch_stats": (W1, "quarantine (wave 1)", "pre-ACP admin view (003) over raw_tours; no reader"),
    "shared.v_pipeline_summary": (W1, "quarantine (wave 1)",
        "pre-ACP admin view (003, retyped by 281) over raw_tours / generated_content / quality_scores; no reader"),
    "shared.tenant_export_config": ("**dead** (wave 2)", "remove the unused reader, then quarantine",
        "only reader TenantConfigService.get_export_config() has no runtime caller (tests only); export webhooks never built"),
    "gold_aa_internal.content_exports": ("**dead** (wave 2)", "unhook the guards, then quarantine",
        "PRD v4 S5 export jobs (006); no writer or reader; but listed as an RLS parity table in Infra owners.yaml / isolation probe / X1 checks"),
    "gold_aa_internal.webhook_deliveries": ("**dead** (wave 2)", "unhook the guards, then quarantine",
        "PRD v4 S5 webhook log (006); same as content_exports"),
    "public.checkpoint_migrations": ("**dead** (wave 2)", "drop via an Infra roles/ file (master-owned)",
        "LangGraph checkpointer bookkeeping; its data tables were dropped by 122; no PostgresSaver in code; drift decision 'keep (AA-853)' to revisit"),
    "shared.pipeline_jobs": ("read-only legacy", "keep; wave 3: retire GET /admin/jobs/{id}, archive to S3, then quarantine",
        "AA-735: read-only history (api/routers/jobs_repo.py); jobs moved to shared.job"),
    "shared.pipeline_lessons": ("read-only legacy (frozen)", "keep; dropped by WM-34 (AA-919 writing memory), not by AA-850",
        "AA-915: AA-132 lessons loop frozen behind PIPELINE_LESSONS_ENABLED (default off, no SQL sent); superseded by app ADR 0010"),
    "shared.v_tour_photos": ("live (to retire)", "keep; move CIS readers to catalog.v_tour_photo, then retire (DM-2.4)",
        "DM-2.4 says retired after X4 (X4 done 23/10); CIS data coverage still reads it"),
    "shared.v_destination_photos": ("live (to retire)", "keep; move services/photos/sync.py to catalog.v_destination_photo, then retire (DM-2.4)",
        "DM-2.4 says retired after X4; photo sync and data coverage still read it"),
    "shared.v_country_unmapped": ("live (ops report)", "keep", "AA-851 orphan report (279), read by hand / tests; expected empty"),
    "booking.customer_otps": ("reserved", "keep (ADR 0006 phase 4 customer OTP sign-in)", "bk-001 Tier A; not built yet (AA-680 customer half)"),
    "booking.customer_sessions": ("reserved", "keep (ADR 0006 phase 4)", "bk-001 Tier A; not built yet"),
    "booking.media_files": ("reserved", "keep (ui-spec FileDropzone)", "bk-001 Tier A; nothing uploads yet"),
    "crm.profile_history": ("reserved", "keep (CRM-29b writes it)", "crm-006 F2 table; writer not built; offboarding lists it"),
    "crm.v_ai_traveler_profile": ("reserved", "keep", "crm-006 view for crm_ai_reader; AI reader not built"),
    "crm.v_ai_trip_context": ("reserved", "keep", "crm-006 view for crm_ai_reader"),
    "crm.v_ai_trip_party": ("reserved", "keep", "crm-006 view for crm_ai_reader"),
    "crm.v_insight_fact": ("reserved", "keep", "crm-006 / crm-011 view for crm_insights"),
    "crm.audit_event_legacy": ("live (partition)", "keep", "crm-007: the crm-003 table attached as the MINVALUE partition of crm.audit_event"),
    "catalog.v_graph_edge": ("contract (no consumer)", "keep; review at the next catalog.graph contract version",
        "ADR 0007 contract view (228); TripPlanner reads none of the graph views today"),
    "catalog.v_tour_day_route": ("contract (no consumer)", "keep; review at the next catalog.graph contract version",
        "ADR 0007 contract view (228)"),
    "catalog._live_stop": ("live (internal)", "keep", "liveness base of the catalog place / graph views (253)"),
}


def effective(fq, x):
    out = []
    for k, v in x["hits"]["qualified"].items():
        repo, cat = k.split(":")
        if cat in ("runtime", "script", "infra-tool", "frozen", "ci-agent"):
            for p in v:
                if p in CATALOGUE and not (fq in DATA_COVERAGE_READS and p.startswith("api/services/data_coverage")):
                    continue
                out.append((repo, cat, p))
    prio = {"runtime": 0, "script": 1, "infra-tool": 2, "ci-agent": 3, "frozen": 4}
    return sorted(out, key=lambda t: (prio[t[1]], t[0] != "CIS", t[2]))


def refs_text(x):
    agg = defaultdict(int)
    for k, v in x["hits"]["qualified"].items():
        repo, cat = k.split(":")
        label = {"runtime": "code", "script": "scripts", "infra-tool": "infra tools", "frozen": "frozen portal",
                 "ci-agent": "ci", "test": "tests", "migration": "migrations", "docs": "docs"}[cat]
        agg[(repo, label)] += len(v)
    parts = []
    for repo in ("CIS", "Booking", "TripPlanner", "Partner", "Infra"):
        items = [f"{label} {n}" for (r, label), n in sorted(agg.items()) if r == repo and label != "docs"]
        if items:
            parts.append(f"{repo}: " + ", ".join(items))
    return "; ".join(parts) or "none"


def verdict(fq, x):
    if fq in OVR:
        return OVR[fq]
    eff = effective(fq, x)
    kind = x["kind"]
    if fq.startswith("crm.audit_event_p"):
        return ("live (partition)", "keep", "monthly partition of crm.audit_event (crm-007)")
    if not eff:
        if fq.startswith("catalog."):
            return ("contract (no consumer)", "keep", "catalog contract view")
        return ("unknown", "review", "no code reference found")
    writes = sum(x.get(k) or 0 for k in ("ins", "upd", "del"))
    if kind == "table" and writes == 0:
        how = "a code writer exists" if x["hits"]["writes"] else "read by code; rows come from migrations or a dormant path"
        return ("live (idle)", "keep", f"no write counted since the stats reset; {how}")
    return ("live", "keep", "")


def rows_text(x):
    if x["rows"] is not None:
        return f"~{x['rows']:,}"
    return "n/a"


def main():
    by_schema = defaultdict(list)
    stats = defaultdict(int)
    for fq in sorted(o):
        x = o[fq]
        v, action, note = verdict(fq, x)
        stats[v.replace("*", "")] += 1
        eff = effective(fq, x)
        ex = ""
        if eff:
            r, c, p = eff[0]
            ex = f" e.g. `{p}`" if r in ("CIS", "Booking", "TripPlanner", "Partner") else f" e.g. Infra `{p}`"
        counters = "-" if x["kind"] == "VIEW" else f"{x.get('ins', 0)}/{x.get('upd', 0)}/{x.get('del', 0)}"
        repo = REPO_OF.get(x["schema"], "AA-CIS-App")
        kind = {"table": "table", "VIEW": "view", "partitioned table": "part. table"}[x["kind"]]
        by_schema[x["schema"]].append(
            f"| `{fq}` | {kind} | {repo} (`{x['owner']}`) | {rows_text(x)} | {counters} | "
            f"{refs_text(x)}{ex} | {v} | {action}{(' — ' + note) if note else ''} |")
    print("<!-- generated by gen_registry.py from scan.json; verdict overrides in OVR -->")
    print()
    print("| verdict | objects |")
    print("|---|---|")
    for k, n in sorted(stats.items(), key=lambda t: -t[1]):
        print(f"| {k} | {n} |")
    print()
    for schema in sorted(by_schema):
        print(f"### `{schema}` ({len(by_schema[schema])})")
        print()
        print("| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |")
        print("|---|---|---|---|---|---|---|---|")
        for line in by_schema[schema]:
            print(line)
        print()


if __name__ == "__main__":
    main()
