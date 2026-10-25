#!/usr/bin/env python3
"""AA-924 PR1c — export the S234 r1–r4 T9 pieces for the offline gate-fold replay.

READ-ONLY on the database. Runs inside the CIS api container (ECS exec, S3-mediated): asyncpg + the container's
DATABASE_URL (role cis_app, which can read acp_shared.content_piece), ssl="require", one READ ONLY transaction,
SELECT statements only. No LLM call, no write. Prints one JSON document between the markers AA924-BEGIN and
AA924-END (with --gzip: base64 of the gzipped JSON, wrapped at 76 columns). With --s3 s3://bucket/key (opt-in) the
gzipped JSON goes to S3 instead of stdout: the only write the script can make.

Selection (S234 = 4 rounds x 20 pieces on the same 6 requests, 13/10/2026): the angle requests of the 40 panel
pieces of label-pack/S234-label-40.xlsx (ANCHORS below, from panel_key.json), and every T9 piece of those requests
created between the first and last anchor's created_at, widened by --margin-hours (default 3), status approved or
held, non-empty text. Expected: 80 pieces (32 blog, 48 LinkedIn). The counts per tenant / channel / status and the
pieces without writer_input (written before AA-769 stored it) are listed in "notes"; the replay skips those.

Output: {"schema": "aa924-s234-export/1", "generated_at", "window": [from, to], "notes": [...],
         "pieces": [{piece_id, request_id, tenant_slug, tenant_name, channel, status, held_reason, attempt_number,
                     created_at, content_text, seo_title, meta_description, slug, gate_ledger, flags,
                     writer_input}]}

Usage (container):  python3 /tmp/s.py [--margin-hours 3] [--gzip] [--s3 s3://bucket/key]
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import gzip
import json
import os
import sys
import textwrap

ANCHORS = (
    "3964cb12-86c0-4dc8-992a-0a45a86fe9fc", "5e04de7a-846f-42fd-b0d6-b5b9b5a1a7f0",
    "e44b05a5-f640-4e1d-a35d-169c5caf5435", "5939df86-f8d4-491e-affc-348d0618ddcd",
    "a9f966c5-687c-4b4f-970d-ccfdbd65871a", "d5156ec3-48c3-4407-b663-3f6919de390a",
    "a084f256-4521-4113-934d-87d849a252b9", "6599b514-4fbb-4c45-ba22-f29b234e4143",
    "d1305823-aaee-4610-ae0f-a07c039b2efd", "1376c2c3-7560-4394-bed8-97063f4d5564",
    "e9f6934a-22b9-4a68-9caf-e1c07f564ad1", "68eab532-c59d-47a9-9468-b8170538cc86",
    "ca38a799-783d-4cd9-808a-a6bf80c0c374", "82af5983-b67c-4131-9e56-90f1e7c4152c",
    "2fc0a2fb-7708-4a38-a3b5-b1275c1e3089", "abdaf636-b6ae-41b0-a9ea-a41b15dadc1c",
    "71ad6b1f-9eb5-4509-915c-5c7644a5b71a", "03248f56-2542-4e92-aed2-7db0193f1f9a",
    "2b49fc6d-eb2f-4818-bc4b-154073c13fc2", "530aec31-ac34-45a2-9018-7233ad61ef2a",
    "37047c45-4940-4512-9023-7cda75a4106f", "72cc7ba9-d01d-4a8f-aef3-365f41c0b5ae",
    "0151508d-1e53-4b64-bd3e-547a36b999e6", "9bf33724-b8a5-44e1-a6d1-30e0c9d4c253",
    "edbaf7c5-3811-4ec6-aed6-0625886c4d57", "4e4f0e0f-a985-4d44-90b2-9ef3cd988756",
    "bd8cea42-8c0e-42f6-abf9-992be290e509", "d8990697-4227-4ddc-9541-793c8ae59993",
    "3affefad-88d1-481b-9c7f-158e55b98a5e", "b6fd83ba-cac8-4e37-8167-43b9f7c997da",
    "1f2b24dc-d08e-42ac-96e0-db027b2a66a2", "bb776a54-93cc-4f10-a108-6e26f9f05324",
    "ad1783e5-aef7-42ef-bf2a-e219874bd73b", "e980728e-f77a-47ba-8b59-0b63a28e301c",
    "f8494e33-b42a-47aa-95b1-d6aedb96d417", "95903c65-f5d6-485d-b47c-87bcc16a2161",
    "d614d2d5-28ce-43c3-9c39-74d73a0416d1", "863e7012-929f-416c-b785-96e0abdabbaf",
    "6eafd4d0-e815-4406-a4c2-044f6a2f74e8", "1dd0f50b-3372-4a9c-a501-6fdb32e75bb6",
)
assert len(ANCHORS) == 40

COLS = """
    cp.piece_id::text AS piece_id, cp.angle_gate_request_id::text AS request_id, t.slug AS tenant_slug,
    t.name AS tenant_name, cp.channel, cp.status, cp.held_reason, cp.attempt_number, cp.created_at,
    cp.content_text, cp.seo_title, cp.meta_description, cp.slug,
    cp.gate_ledger::text AS gate_ledger, cp.flags::text AS flags, cp.writer_input::text AS writer_input
"""
FROM = "FROM acp_shared.content_piece cp JOIN shared.tenants t ON t.tenant_id = cp.tenant_id"


def _j(v):
    return json.loads(v) if isinstance(v, str) and v else v


async def export(margin_hours: float) -> dict:
    import asyncpg

    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        async with conn.transaction(readonly=True):
            anchors = await conn.fetch(
                "SELECT angle_gate_request_id::text AS request_id, created_at FROM acp_shared.content_piece "
                "WHERE piece_id = ANY($1::uuid[])", list(ANCHORS))
            notes = [f"anchors found: {len(anchors)}/40"]
            if not anchors:
                raise SystemExit("no anchor piece found")
            requests = sorted({r["request_id"] for r in anchors})
            margin = dt.timedelta(hours=margin_hours)
            lo, hi = min(r["created_at"] for r in anchors) - margin, max(r["created_at"] for r in anchors) + margin
            rows = await conn.fetch(
                f"""SELECT {COLS} {FROM}
                    WHERE cp.angle_gate_request_id = ANY($1::uuid[]) AND cp.created_at BETWEEN $2 AND $3
                      AND cp.status IN ('approved', 'held') AND length(cp.content_text) > 0
                    ORDER BY cp.created_at, cp.piece_id""", requests, lo, hi)
    finally:
        await conn.close()
    pieces = []
    for r in rows:
        d = dict(r)
        d["created_at"] = r["created_at"].isoformat()
        for k in ("gate_ledger", "flags", "writer_input"):
            d[k] = _j(d[k])
        pieces.append(d)
    counts = {}
    for p in pieces:
        key = f"{p['tenant_slug']}/{p['channel']}/{p['status']}"
        counts[key] = counts.get(key, 0) + 1
    notes += [f"requests: {len(requests)}", f"pieces: {len(pieces)} (expected 80)",
              f"without writer_input: {sum(1 for p in pieces if not p['writer_input'])}",
              *[f"{k}: {v}" for k, v in sorted(counts.items())]]
    missing = set(ANCHORS) - {p["piece_id"] for p in pieces}
    if missing:
        notes.append(f"anchor pieces outside the selection: {sorted(missing)}")
    return {"schema": "aa924-s234-export/1", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "window": [lo.isoformat(), hi.isoformat()], "notes": notes, "pieces": pieces}


def main() -> None:
    ap = argparse.ArgumentParser(description="AA-924 S234 piece export (read-only)")
    ap.add_argument("--margin-hours", type=float, default=3.0)
    ap.add_argument("--gzip", action="store_true")
    ap.add_argument("--s3", help="s3://bucket/key — write the gzipped JSON there instead of stdout")
    args = ap.parse_args()
    data = asyncio.run(export(args.margin_hours))
    body = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
    for n in data["notes"]:
        print(n, file=sys.stderr)
    if args.s3:
        import boto3

        bucket, _, key = args.s3[len("s3://"):].partition("/")
        boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=gzip.compress(body),
                                      ContentType="application/gzip")
        print(f"wrote s3://{bucket}/{key} ({len(data['pieces'])} pieces)")
        return
    print("AA924-BEGIN")
    if args.gzip:
        print("\n".join(textwrap.wrap(base64.b64encode(gzip.compress(body)).decode("ascii"), 76)))
    else:
        print(body.decode("utf-8"))
    print("AA924-END")


if __name__ == "__main__":
    main()
