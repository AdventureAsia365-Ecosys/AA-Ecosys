"""Test every LLM provider connection through the gateway (the admin "Test connection" call, in bulk).

Playbook: docs/ops/playbooks/llm-access-denied.md (OPS-04-llm-access-denied), step 3.

Runs inside the CIS api container through tools/ecs/ecsx.sh:
    tools/ecs/ecsx.sh tools/llm/llm_connections_probe.py PROBE_ACTOR=<who-and-why, e.g. s261-access-check>
        [PROBE_CONNECTIONS=<key>,<key>] [PROBE_MODEL=<model_key>]

Cost: one call per connection of at most 32 output tokens on the cheapest enabled text model of that connection
(api.services.llm_connections.test_connection); a few connections cost well under 0.01 USD per run, and a refused
call costs 0. Every answered call is logged by the gateway in shared.llm_call_log (stage adhoc_conn_test, role
validate, account = the connection key). Side effects, as with the admin button: one acp_shared.audit_log row per
connection (actor = PROBE_ACTOR) and the outcome counts on the deployment's circuit (a success closes it).
Prints one JSON line per connection; a refused connection shows ok=false with its error_class.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, "/app")

import asyncpg  # noqa: E402

from api.services import llm_connections  # noqa: E402

ACTOR = os.environ.get("PROBE_ACTOR", "").strip()
ONLY = [k.strip() for k in os.environ.get("PROBE_CONNECTIONS", "").split(",") if k.strip()]
MODEL = os.environ.get("PROBE_MODEL") or None
FIELDS = ("kind", "model_key", "connection_enabled", "ok", "reply_usable", "error_class", "error", "cost_usd",
          "latency_ms")


async def main():
    if not ACTOR:
        sys.exit("PROBE_ACTOR=<who-and-why> is required (it is the audit actor of every test)")
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], ssl="require", min_size=1, max_size=2)
    try:
        async with pool.acquire() as db:
            keys = [r["connection_key"] for r in
                    await db.fetch("SELECT connection_key FROM shared.llm_provider_connection ORDER BY 1")]
        for key in (k for k in keys if not ONLY or k in ONLY):
            try:
                r = await llm_connections.test_connection(pool, key, model_key=MODEL, actor=ACTOR)
                print(json.dumps({"connection": key, **{f: r.get(f) for f in FIELDS}})[:600])
            except Exception as e:  # noqa: BLE001 - unknown key or a connection the gateway cannot test
                print(json.dumps({"connection": key, "refused": type(e).__name__, "error": str(e)[:300]}))
    finally:
        await pool.close()


asyncio.run(main())
