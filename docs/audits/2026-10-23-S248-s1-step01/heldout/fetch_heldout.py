#!/usr/bin/env python3
# S248 S1-first step 1 — read-only fetch of live published master S1 pages outside the golden set ($0, SELECT only).
import asyncio, gzip, json, os, uuid
import asyncpg, boto3

GOLDEN = ["00dd2fe6-4e2a-499c-b0a8-2ff3eef27a36", "00f15c2d-e48b-4ebe-b0cf-d097b4ea54b3", "0a832593-8acd-4a87-8f87-7660a69c86a6", "15b02210-7782-4bb1-aa2b-f18af98ef8d1", "196df8e7-2cd4-4674-9563-f9e14f459169", "282df69a-fcdb-41d9-af95-8dcd97c1e229", "2c19e7fd-[phone removed]-ab6bc51a089f", "3053caa1-9879-41bf-b2ec-f4416c4e7a78", "34164145-16a8-46d1-92f0-433bdc62ab4f", "3d359266-2e20-4afc-9708-c17bc903f8bf", "3fa33633-8502-4b53-a775-a0491fd2e509", "44281611-10a6-43f2-8e17-4090812cb7ae", "44e9daef-5b53-4c37-8e45-d21e33a2d2db", "533425cc-7bc4-4164-9900-3eb888603752", "5744141a-16f5-4b6b-9e86-58146cf1164e", "59a0d961-14e8-4634-9913-7d164fe627df", "59b776f2-a160-48e4-8771-30f33892195e", "59b9edf6-bdc3-45a2-92f3-6989b362d396", "5efdeb73-5101-4c81-80d7-e70dc73782a9", "636b2e2d-92b9-4380-96d4-64086133a97e", "69f731ca-a77d-4fb1-87b2-9d98c6ad010f", "71cacbb0-467a-4b4c-abf9-e55e651be427", "770a38dd-4e7b-4b55-9ded-0e9ced757301", "7d64faca-c732-4d83-8471-9383c99fd7c6", "81e811f9-8bb3-4c8a-a478-d0a2a200f003", "83e3b208-05e4-449b-8dc1-4eef21a7a223", "849bd896-c50d-45c6-acf1-cb7eb00eb046", "86f4dc83-4fbd-49e1-84df-4acd7598bc37", "870d52e7-8f24-45d0-ae12-66fe9da7ec64", "8c423737-e288-4c95-a4b4-953447c92551", "909e5f93-aef1-4c8d-92aa-13b2776e558d", "913bde35-1cbf-4c5f-8497-77da759d2b9e", "9c688b7d-a73a-4e81-adac-948fc34e4411", "[phone removed]-4e38-b75d-dc6da6eba301", "a54844fe-e54b-4c3f-8ded-6a0dec747177", "a69a844c-0b9f-455c-ae1f-1f2e640f4094", "a6f6512e-40a7-4617-ae5d-106699d0dd8c", "abfb4275-1ec2-484b-b375-1a3882747971", "b4d315a6-21cb-4d2b-9a2f-9d654388078a", "be66c919-cd9e-48c8-a20d-329e84c6bfc4", "c8905ad0-e675-4cd1-99aa-13fe9d064cbe", "cb970f00-01ca-4911-939f-7c7f56c36213", "d398ffe0-3caa-4763-aa66-0fc81576a2bd", "da3ca995-471f-4178-9619-bd84c5342ae7", "e8235227-901e-4023-a7e8-721552dbe2e8", "ea36f9c3-cd92-4923-bc38-6d936696056d", "eabff259-d69e-411d-8cd2-d09a24a1ab7c", "efb52e00-fef9-4630-967b-64950f417514", "fbadec01-765a-46fc-96ce-c92a9db823e8", "fed8d5e8-9a63-4c77-b766-df2f8f62b726"]
SQL = """
SELECT rt.tour_id::text AS tour_id, rt.country, rt.duration, rt.price_raw, rt.inclusions, rt.exclusions,
       rt.src_name, rt.src_subtitle, rt.src_summary, rt.src_description, rt.src_highlights, rt.src_itineraries,
       rt.group_size, rt.period, rt.best_time_to_go,
       gc.id::text AS gc_id, gc.version_num, gc.aa_name, gc.aa_subtitle, gc.aa_summary, gc.aa_description,
       gc.aa_highlights, gc.aa_itineraries, gc.seo_title, gc.seo_meta, gc.created_at::text AS gc_created_at,
       pt.master_status::text AS master_status
FROM gold_aa_internal.published_tours pt
JOIN silver_aa_internal.generated_content gc ON gc.id = pt.generated_content_id
JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id AND rt.deleted_at IS NULL
WHERE pt.deleted_at IS NULL AND NOT (rt.tour_id::text = ANY($1::text[]))
ORDER BY md5(rt.tour_id::text || 's248')
LIMIT 80
"""
STATS = """
SELECT count(*) AS live,
       count(*) FILTER (WHERE coalesce(trim(rt.group_size),'') <> '') AS with_group_size,
       count(*) FILTER (WHERE coalesce(trim(rt.best_time_to_go),'') <> '') AS with_best_time,
       count(*) FILTER (WHERE coalesce(trim(rt.exclusions),'') <> '') AS with_exclusions,
       count(*) FILTER (WHERE coalesce(trim(rt.price_raw),'') <> '') AS with_price
FROM gold_aa_internal.published_tours pt
JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id AND rt.deleted_at IS NULL
WHERE pt.deleted_at IS NULL
"""

async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        rows = [dict(r) for r in await conn.fetch(SQL, GOLDEN)]
        stats = dict(await conn.fetchrow(STATS))
    finally:
        await conn.close()
    body = gzip.compress(json.dumps({"stats": stats, "rows": rows}, default=str).encode())
    key = f"scripts/out/s248-s1-step01/{uuid.uuid4()}.json.gz"
    boto3.client("s3").put_object(Bucket="aa-cis-bronze-005097885195", Key=key, Body=body)
    print("ROWS", len(rows), "STATS", json.dumps(stats), "KEY", key, flush=True)

asyncio.run(main())
