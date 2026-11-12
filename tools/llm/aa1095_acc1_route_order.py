"""AA-1095 (S278): switch Bedrock serving to the acc1 connection with the per-family provider order, as ONE audited
route-control version. DRY RUN (preview) by default.

Decision (tech lead, 12/11/2026, root ADR 0001a Note S278): AWS refuses the gateway's chat models on acc3; acc1
answers all of them. Order per model family:
  - Claude: Anthropic API first (free for us now), then Bedrock on acc1, then acc3;
  - GPT on Bedrock: acc1 first, then the OpenAI API, then acc3.
The order itself is computed by AA-CIS-App api/services/llm_family_order.py (pure, unit tested there); this script
only checks the preconditions, prints the chain per stage before / after, and saves.

Runs inside the CIS api container through tools/ecs/ecsx.sh (after migration 413 is applied, the CIS code that knows
BEDROCK_ACCT_PAYER is deployed and AA-CIS-Infra has set that env on the api task):
    tools/ecs/ecsx.sh tools/llm/aa1095_acc1_route_order.py ROUTE_ACTOR=<who-and-why, e.g. s278-acc1-switch>
        [APPLY=1]

Without APPLY=1 nothing is written: the env and connection checks, the provider order that would be saved, the chain
of every active stage (model@connection in the model-first order; "(off)" = a deployment or connection switched off,
so the gateway skips it) and the route-control preview with the connection still off.
With APPLY=1: (1) connection acc1 switched on (llm_connections.set_enabled, audited); (2) one
llm_route_control.apply(action="save", provider_order=..., order_mode="model_first", break_glass_reason=REASON)
(a new version: one-click revert on the admin Route control page, break-glass bell per changed writer / judge stage).
If (2) is refused, (1) is undone (the connection goes back off unless it was already on). $0: no model call.
Rollback later: revert the version on the Route control page, then switch acc1 off (Connections page).
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Any, Mapping, Optional

LEAD = "acc1"
PAYER_ENV = "BEDROCK_ACCT_PAYER"
REASON = ("tech lead S278 12/11: Claude via Anthropic API first (free), GPT via Bedrock acc1 first; "
          "acc3 blocked by AWS")
NOTE = "AA-1095 (S278): Bedrock serving on acc1, provider order per model family (root ADR 0001a Note S278)"
CONNECTION_SQL = ("SELECT connection_key, kind, auth_mode, account_id_env, enabled "
                  "FROM shared.llm_provider_connection WHERE connection_key = $1")
DEPLOYMENTS_SQL = "SELECT model_key, enabled FROM shared.llm_model_deployment WHERE connection_key = $1 ORDER BY 1"


def env_problem(environ: Mapping[str, str]) -> Optional[str]:
    """None when the payer account env holds a 12-digit account ID (never printed)."""
    value = (environ.get(PAYER_ENV) or "").strip()
    if not value:
        return f"{PAYER_ENV} is not set on this task (AA-CIS-Infra env, Infra PR of AA-1095)"
    if not re.fullmatch(r"[0-9]{12}", value):
        return f"{PAYER_ENV} is not a 12-digit account ID"
    return None


def connection_problems(row: Optional[Mapping[str, Any]], deployments: list) -> list[str]:
    """What stops the switch: the registry row of migration 413 and its deployments."""
    if row is None:
        return [f"no connection {LEAD!r} (migration 413 not applied)"]
    out = []
    if row["kind"] != "bedrock" or row["auth_mode"] != "assume_role":
        out.append(f"connection {LEAD!r} is {row['kind']}/{row['auth_mode']}, not bedrock/assume_role")
    if row["account_id_env"] != PAYER_ENV:
        out.append(f"connection {LEAD!r} reads {row['account_id_env']!r}, not {PAYER_ENV}")
    if not deployments:
        out.append(f"connection {LEAD!r} has no deployment")
    return out


def provider_orders(priorities: Mapping[str, Mapping[str, int]]) -> dict[str, list[str]]:
    """model -> connection keys by priority, then key (route_versions.provider_order)."""
    return {m: [c for c, _ in sorted(p.items(), key=lambda kv: (int(kv[1]), kv[0]))] for m, p in priorities.items()}


def off_pairs(deployments: list, connections: Mapping[str, Mapping], lead_on: bool = False) -> set:
    """(model, connection) the gateway skips: a deployment or its connection switched off. ``lead_on``: count the lead
    connection as on (what the chain looks like after APPLY=1)."""
    out = set()
    for d in deployments:
        c = connections.get(d["connection_key"]) or {}
        conn_on = bool(c.get("enabled")) or (lead_on and d["connection_key"] == LEAD)
        if not d.get("enabled") or not conn_on:
            out.add((d["model_key"], d["connection_key"]))
    return out


def chain_text(chain: list, orders: Mapping[str, list], off: set) -> str:
    parts = []
    for m in dict.fromkeys(chain):
        for c in orders.get(m, []):
            parts.append(f"{m}@{c}" + (" (off)" if (m, c) in off else ""))
    return " > ".join(parts) or "(no deployment)"


def chain_report(stages: list, routes: Mapping[str, Any], before: Mapping[str, list], after: Mapping[str, list],
                 off_before: set, off_after: set) -> list[str]:
    """Two lines per active stage whose model@connection walk changes; one line for the others."""
    lines = []
    for s in sorted(stages, key=lambda r: r["stage"]):
        if s.get("is_active") is False:
            continue
        r = routes.get(s["stage"]) or {}
        chain = [r.get("model_id") or s.get("model_id")] + list(r.get("fallback_model_ids") or [])
        chain = [k for k in chain if k]
        b, a = chain_text(chain, before, off_before), chain_text(chain, after, off_after)
        if a == b:
            lines.append(f"  {s['stage']} ({s.get('role')}): unchanged: {b}")
        else:
            lines.append(f"  {s['stage']} ({s.get('role')}):\n      before: {b}\n      after:  {a}")
    return lines


async def run(pool, *, actor: str, apply: bool, environ: Mapping[str, str], rc, fo, lc, out=print) -> int:
    """``rc`` = api.services.llm_route_control, ``fo`` = api.services.llm_family_order, ``lc`` =
    api.services.llm_connections (injected so the tests use fakes). Returns the exit code."""
    problem = env_problem(environ)
    if problem:
        out(f"REFUSED: {problem}")
        return 2
    async with pool.acquire() as db:
        row = await db.fetchrow(CONNECTION_SQL, LEAD)
        deps = [dict(r) for r in await db.fetch(DEPLOYMENTS_SQL, LEAD)]
    problems = connection_problems(dict(row) if row is not None else None, deps)
    if problems:
        for p in problems:
            out(f"REFUSED: {p}")
        return 2
    was_on = bool(row["enabled"])
    out(f"env {PAYER_ENV}: set (12 digits); connection {LEAD}: {'on' if was_on else 'off'}, "
        f"{len(deps)} deployments ({sum(1 for d in deps if d['enabled'])} on)")

    world = await rc.read_world(pool)
    families = {m.model_key: m.family_key for m in world.models}
    order = fo.family_provider_order(world.live["priorities"], families, world.connections, LEAD)
    before = provider_orders(world.live["priorities"])
    after = {**before, **order}
    out(f"order mode: {world.live['order_mode']} -> {fo.ORDER_MODE}")
    out(f"provider order changes ({len(order)} models):")
    for m, o in sorted(order.items()):
        out(f"  {m}: {' > '.join(before.get(m, []))}  ->  {' > '.join(o)}")
    out("chain per active stage (model@connection, model first):")
    for line in chain_report(world.stages, world.live["routes"], before, after,
                             off_pairs(world.deployments, world.connections),
                             off_pairs(world.deployments, world.connections, lead_on=True)):
        out(line)

    if not order and world.live["order_mode"] == fo.ORDER_MODE and was_on:
        out("nothing to change: the order and the connection are already in place")
        return 0
    preview = await rc.preview(pool, order_mode=fo.ORDER_MODE, provider_order=order)
    out(f"preview (connection {LEAD} as it is now): valid={preview['valid']} version={preview['version']} "
        f"needs_evidence={preview['needs_evidence']} frozen_by_waves={len(preview.get('frozen_by_waves') or [])}")
    for e in preview["errors"]:
        out(f"  ERROR {e.get('stage') or ''} {e['rule']}: {e['message']}")
    for w in preview["warnings"]:
        if not w.get("existing"):
            out(f"  warning {w.get('stage') or ''} {w['rule']}: {w['message']}")
    if not preview["valid"] or preview.get("frozen_by_waves"):
        out("REFUSED: the preview has errors or a rerun wave is open; nothing written")
        return 1
    if not apply:
        out("DRY RUN: nothing written. Run again with APPLY=1 to switch the connection on and save the version.")
        return 0

    if not was_on:
        async with pool.acquire() as db:
            await lc.set_enabled(db, LEAD, enabled=True, actor=actor)
        out(f"connection {LEAD} switched on")
    try:
        if order or world.live["order_mode"] != fo.ORDER_MODE:
            saved = await rc.apply(pool, actor=actor, action="save", expected_version=preview["version"], note=NOTE,
                                   break_glass_reason=REASON, order_mode=fo.ORDER_MODE, provider_order=order)
            out(f"saved route-control version {saved['version']} ({len(saved.get('diff') or [])} changes); "
                f"changed stages: {', '.join(saved.get('changed_stages') or []) or '(none, provider order only)'}")
            for w in saved.get("warnings") or []:
                out(f"  warning: {w}")
    except Exception as e:
        if not was_on:
            async with pool.acquire() as db:
                await lc.set_enabled(db, LEAD, enabled=False, actor=actor)
            out(f"connection {LEAD} switched back off")
        out(f"REFUSED: {type(e).__name__}: {e}")
        return 1

    served = await rc.serving(await rc.read_world(pool))
    out("serving now (first model@connection the gateway would call, refused rungs skipped):")
    for stage in sorted(served):
        out(f"  {stage}: {(served[stage] or {}).get('first')}")
    return 0


async def main() -> int:
    actor = os.environ.get("ROUTE_ACTOR", "").strip()
    if not actor:
        sys.exit("ROUTE_ACTOR=<who-and-why> is required (the audit actor of the switch and the version)")
    sys.path.insert(0, "/app")
    import asyncpg

    from api.services import llm_connections, llm_family_order, llm_route_control

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], ssl="require", min_size=1, max_size=3)
    try:
        return await run(pool, actor=actor, apply=os.environ.get("APPLY") == "1", environ=os.environ,
                         rc=llm_route_control, fo=llm_family_order, lc=llm_connections)
    finally:
        await pool.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
