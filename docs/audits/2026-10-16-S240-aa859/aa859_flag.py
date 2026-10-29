"""AA-859 S240 — get / set / del AA-859 tenant-pool flags in the CIS Dev Redis (runs inside the api task via
S3-mediated ECS exec; driven by aa859_flip_verify.py).

    python3 aa859_flag.py <get|on|off|del> <flag> [<flag> ...]

Only the eleven tenant-pool route flags of api/core/aa544_tenant_pool.py are accepted. "on" = SET "true",
"off" = SET "false" (the rollback). S241 decision D-12: the flags FAIL CLOSED -- a missing key, any value other
than "false", or a Redis read error means ON (tenant pool), so DEL is NOT a rollback any more; "off" must write
the explicit "false". "del" removes the key (= back to the ON default), kept only for cleanup.
Writes {action, before, after} to s3://aa-cis-bronze-005097885195/scripts/out/s240_aa859_flag.json and
prints only "OK <bytes>".
"""
import asyncio
import json
import sys

import boto3
import redis.asyncio as aioredis

ALLOWED = {
    # AA-859 wave 2
    "aa859:piece_edit_pool", "aa859:t2_version_write_pool", "aa859:angle_gate_decide_pool",
    "aa859:unpublish_pool", "aa859:t2_version_reads_pool", "aa859:integration_connect_pool",
    # AA-544 / AA-815 / AA-817 (same fail-closed encoding since S241 D-12)
    "aa544:stage1:publish_pending_pool", "aa544:stage5:get_piece_pool", "aa544:publish_log_list_pool",
    "aa544:integration_disconnect_pool", "aa817:content_piece_reads_pool",
    # AA-986 L3 (S248): GET /v1/notifications + mark read, needs CIS 274
    "aa986:tenant_notifications_pool",
    # AA-814 (S257): GET / POST / PATCH / DELETE /v1/facts (tenant Facts Entries), needs CIS 302
    "aa814:facts_pool",
}
ON_VALUE, OFF_VALUE = "true", "false"   # must match FLAG_ON_VALUE / FLAG_OFF_VALUE in aa544_tenant_pool.py


def _redis_url():
    """Same host the api uses: the env lookup is read from the api's own source (api/main.py lifespan), so this
    script never hard-codes the env name or a stale default host."""
    import importlib.util
    import os
    import re
    paths = [os.path.join(d, "api", "main.py") for d in (os.getcwd(), "/app", "/code", "/srv", "/usr/src/app")]
    spec_path = next((p for p in paths if os.path.exists(p)), None)
    if spec_path is None:
        spec = importlib.util.find_spec("api.main")
        spec_path = spec.origin if spec else None
    if spec_path is None:
        raise SystemExit("api/main.py not found")
    src = open(spec_path).read()
    m = re.search(r"os\.environ\.get\('([A-Za-z0-9_]+)', '([^']+)'\)\}:6379", src)
    if not m:
        raise SystemExit("redis host lookup not found in api/main.py")
    return f"redis://{os.environ.get(m.group(1), m.group(2))}:6379"


BUCKET, KEY = "aa-cis-bronze-005097885195", "scripts/out/s240_aa859_flag.json"


async def main(action, flags):
    bad = [f for f in flags if f not in ALLOWED]
    if action not in ("get", "on", "off", "del") or bad or not flags:
        raise SystemExit(f"usage: get|on|off|del <tenant-pool flag>...; refused: {bad}")
    r = aioredis.from_url(_redis_url(), decode_responses=True)
    out = {"action": action, "before": {f: await r.get(f) for f in flags}}
    for f in flags:
        if action == "on":
            await r.set(f, ON_VALUE)
        elif action == "off":
            await r.set(f, OFF_VALUE)   # explicit OFF; a missing key would mean ON (D-12)
        elif action == "del":
            await r.delete(f)
    out["after"] = {f: await r.get(f) for f in flags}
    await (r.aclose() if hasattr(r, "aclose") else r.close())
    body = json.dumps(out).encode()
    boto3.client("s3", region_name="us-west-1").put_object(Bucket=BUCKET, Key=KEY, Body=body)
    print("OK", len(body))


try:
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
except BaseException as e:  # keep the error readable: ECS exec truncates tracebacks
    import traceback
    boto3.client("s3", region_name="us-west-1").put_object(
        Bucket=BUCKET, Key=KEY, Body=json.dumps({"error": repr(e), "trace": traceback.format_exc()[-1500:]}).encode())
    print("ERR")
