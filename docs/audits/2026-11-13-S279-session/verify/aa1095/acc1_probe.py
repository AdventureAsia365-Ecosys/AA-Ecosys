"""S279 AA-1095: manual live probe of every ENABLED deployment (daily mode) + the DISABLED acc1 deployments
(candidate mode) through llm_connection_probe; prints the acc1 rows of each matrix. < 0.01 USD."""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, "/app")
import asyncpg  # noqa: E402
from services.jobs import llm_probe_job as probe  # noqa: E402

DONE = ("succeeded", "failed", "cancelled", "stopped_budget")


async def wait(pool, job_id, wait_s=600):
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        row = await pool.fetchrow("SELECT status, error, result FROM shared.job WHERE id = $1::uuid", job_id)
        if row and row["status"] in DONE:
            r = row["result"]
            r = json.loads(r) if isinstance(r, str) else (r or {})
            return row["status"], row["error"], r
        await asyncio.sleep(5)
    return "timeout", None, {}


async def main():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], ssl="require", min_size=1, max_size=2)
    try:
        actor = "script:s279-aa1095-acc1-probe"
        for mode, kw in ((probe.MODE_DAILY, {}), (probe.MODE_CANDIDATES, {"connection_keys": ["acc1"]})):
            job_id, _ = await probe.enqueue_manual(pool, dry_run=False, actor=actor, mode=mode, **kw)
            st, err, r = await wait(pool, job_id)
            m = r.get("matrix") or []
            print(json.dumps({"mode": mode, "job": job_id, "status": st, "error": err, "cost_usd": r.get("cost_usd"),
                              "probed": r.get("probed"), "ok": r.get("ok"), "failed": r.get("failed")}, default=str))
            for x in m:
                if x.get("connection_key") == "acc1" or not x.get("ok"):
                    state = "ok" if x.get("ok") else f"FAIL {x.get('error_class')} {(x.get('error') or '')[:90]}"
                    print("  ", x.get("connection_key"), x.get("model_key"), state)
            if mode == probe.MODE_DAILY:
                print("  stage_coverage:", json.dumps(r.get("stage_coverage"), default=str)[:600])
    finally:
        await pool.close()


asyncio.run(main())
