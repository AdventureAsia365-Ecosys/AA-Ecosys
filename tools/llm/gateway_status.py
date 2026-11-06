"""AI gateway status for the session-start block (skill aa-session, "Bắt đầu phiên" step 2). Read-only, no cost.

Runs inside the CIS api container through tools/ecs/ecsx.sh:
    tools/ecs/ecsx.sh tools/llm/gateway_status.py
Uses the container's DATABASE_URL (cis_app). Reads only configuration and ledger columns that carry no personal
data (shared.llm_provider_connection, shared.llm_model_deployment, shared.llm_route_config_version,
shared.llm_call_log: keys, states, timestamps, costs, status / error class); never a tenant id, actor or note, so
the pilot PII hook (.claude/hooks/pilot_pii_guard.py) accepts it. No LLM call, no write.

Prints, in order:
  - per connection: enabled, access_state, last probe, monthly cap, month-to-date spend (shadow calls excluded),
    calls in the last 24 h ok / error / expected refusals;
  - per connection: enabled model deployments ok / access_denied / other, with the denied model keys;
  - the latest route control version (action, preset, time);
  - month-to-date spend over every connection;
  - the top 24 h error groups (stage, connection, error class), expected refusals left out;
  - the 24 h expected refusals (no access yet) by connection and model, on one line each.

Expected refusal (AA-900, S271 lane l11; the same rule as CIS shared/llm_client/expected_refusal.py): a refused row
with error class access_denied whose deployment's access_state is access_denied (its last probe found no access) on a
connection whose access_state is ok (the account answers). The routing already moves past such a model, so it is not
an error. An account-wide refusal (connection access_state not ok) or a model whose last probe answered still counts
as an error. Rows are only counted, never changed.
"""
import asyncio
import os

import asyncpg

# Keep in step with AA-CIS-App shared/llm_client/expected_refusal.py (expected_sql); ``l`` is the ledger row.
EXPECTED = """(l.status = 'refused' AND l.error_class = 'access_denied' AND EXISTS (
    SELECT 1 FROM shared.llm_model_deployment xr_d
      JOIN shared.llm_provider_connection xr_c ON xr_c.connection_key = xr_d.connection_key
     WHERE xr_d.connection_key = l.connection_key AND xr_d.model_key = l.model
       AND xr_d.access_state = 'access_denied' AND xr_c.access_state = 'ok'))"""

CONNECTIONS_SQL = f"""
SELECT p.connection_key, p.enabled, p.access_state, p.last_probe_at, p.monthly_budget_usd,
       (SELECT coalesce(sum(l.cost_usd), 0) FROM shared.llm_call_log l
         WHERE l.connection_key = p.connection_key AND l.created_at >= date_trunc('month', now())
           AND coalesce(l.is_shadow, false) = false) AS mtd,
       (SELECT count(*) FILTER (WHERE coalesce(l.status, 'ok') = 'ok') FROM shared.llm_call_log l
         WHERE l.connection_key = p.connection_key AND l.created_at > now() - interval '24 hours') AS ok24,
       (SELECT count(*) FILTER (WHERE coalesce(l.status, 'ok') <> 'ok' AND NOT {EXPECTED}) FROM shared.llm_call_log l
         WHERE l.connection_key = p.connection_key AND l.created_at > now() - interval '24 hours') AS err24,
       (SELECT count(*) FILTER (WHERE {EXPECTED}) FROM shared.llm_call_log l
         WHERE l.connection_key = p.connection_key AND l.created_at > now() - interval '24 hours') AS exp24
FROM shared.llm_provider_connection p
ORDER BY p.enabled DESC, p.connection_key
"""

DEPLOYMENTS_SQL = """
SELECT connection_key,
       count(*) FILTER (WHERE access_state = 'ok') AS ok,
       count(*) FILTER (WHERE access_state = 'access_denied') AS denied,
       count(*) FILTER (WHERE access_state NOT IN ('ok', 'access_denied')) AS other,
       string_agg(model_key, ',' ORDER BY model_key) FILTER (WHERE access_state = 'access_denied') AS denied_models
FROM shared.llm_model_deployment
WHERE enabled
GROUP BY 1 ORDER BY 1
"""

ROUTE_SQL = """
SELECT version, created_at, action, preset
FROM shared.llm_route_config_version
ORDER BY version DESC LIMIT 1
"""

MONTH_SQL = """
SELECT coalesce(sum(cost_usd), 0) FROM shared.llm_call_log
WHERE created_at >= date_trunc('month', now()) AND coalesce(is_shadow, false) = false
"""

ERRORS_SQL = f"""
SELECT l.stage, l.connection_key, l.error_class, count(*) AS n
FROM shared.llm_call_log l
WHERE l.created_at > now() - interval '24 hours' AND coalesce(l.status, 'ok') <> 'ok' AND NOT {EXPECTED}
GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 6
"""

EXPECTED_SQL = f"""
SELECT l.connection_key, l.model, count(*) AS n
FROM shared.llm_call_log l
WHERE l.created_at > now() - interval '24 hours' AND {EXPECTED}
GROUP BY 1, 2 ORDER BY 1, 2
"""


async def main() -> None:
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        print("== connections (enabled / access / last probe / cap / MTD spend / 24h calls ok-err-expected)",
              flush=True)
        for r in await c.fetch(CONNECTIONS_SQL):
            cap = f"{r['monthly_budget_usd']:.0f}" if r["monthly_budget_usd"] is not None else "-"
            lp = r["last_probe_at"].strftime("%d/%m %H:%MZ") if r["last_probe_at"] else "-"
            print(f"  {r['connection_key']:<18} {'ON ' if r['enabled'] else 'off'} {r['access_state']:<14} "
                  f"probe {lp:<12} cap {cap:>5} USD  MTD {float(r['mtd']):.4f} USD  "
                  f"24h {r['ok24']} ok / {r['err24']} err / {r['exp24']} expected", flush=True)

        print("== model deployments by connection (enabled only): ok / denied / other", flush=True)
        for r in await c.fetch(DEPLOYMENTS_SQL):
            denied = f"denied: {r['denied_models']}" if r["denied_models"] else ""
            print(f"  {r['connection_key']:<18} {r['ok']} ok / {r['denied']} denied / {r['other']} other  {denied}",
                  flush=True)

        v = await c.fetchrow(ROUTE_SQL)
        if v:
            preset = f", preset {v['preset']}" if v["preset"] else ""
            print(f"== route control: version {v['version']} ({v['action']}{preset}) {v['created_at']:%d/%m %H:%MZ}",
                  flush=True)
        else:
            print("== route control: no version", flush=True)

        total = await c.fetchval(MONTH_SQL)
        print(f"== spend this month (all connections, excl. shadow): {float(total):.4f} USD", flush=True)

        print("== top stages by 24h errors (expected refusals left out)", flush=True)
        for r in await c.fetch(ERRORS_SQL):
            print(f"  {r['stage']:<26} {r['connection_key'] or '-':<16} {r['error_class'] or '-':<18} {r['n']}",
                  flush=True)

        print("== 24h expected refusals (no access yet; the route moves on, not errors)", flush=True)
        for r in await c.fetch(EXPECTED_SQL):
            print(f"  {r['connection_key']:<18} {r['model']:<26} {r['n']}", flush=True)
    finally:
        await c.close()


if __name__ == "__main__":
    asyncio.run(main())
