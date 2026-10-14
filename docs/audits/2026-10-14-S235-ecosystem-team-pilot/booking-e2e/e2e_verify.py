import asyncio, asyncpg, boto3, json
from urllib.parse import urlparse
T = "c14c07ae-7cc4-4bf9-945b-8c5922b23c89"
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip()
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require",
                              server_settings={"default_transaction_read_only": "on"})
    q = lambda s, *a: c.fetch(s, *a)
    o = await q("select idempotency_key, schema_version, payload->'customer' customer, jsonb_array_length(payload->'itinerary'->'legs') legs, jsonb_array_length(payload->'itinerary'->'days') days from tripplanner.v_inquiry_outbox where trip_id=$1::uuid", T)
    print("E2E outbox", [dict(r) for r in o])
    keys = [r["idempotency_key"] for r in o]
    print("E2E inbox", [dict(r) for r in await q("select status, contract_version, processed_at, error from booking.inbox_events where idempotency_key = any($1::text[])", keys)])
    tc = await q("select id, code, status, source_system, customer_id from booking.trip_cases where idempotency_key = any($1::text[])", keys)
    print("E2E case", [dict(r) for r in tc])
    if tc:
        print("E2E legs", [dict(r) for r in await q("select position, source_tour_id, day_from, day_to from booking.trip_case_legs where trip_case_id=$1 order by position", tc[0]["id"])])
        print("E2E customer", [dict(r) for r in await q("select name, email, verified, source, needs_merge_review from booking.customers where id=$1", tc[0]["customer_id"])])
        print("E2E notif", [dict(r) for r in await q("select type, title, recipient_type from booking.notifications order by created_at desc limit 2")])
    print("E2E jobs", [dict(r) for r in await q("select kind, status, count(*) n from booking.job group by 1,2")])
    await c.close()
asyncio.run(main())
