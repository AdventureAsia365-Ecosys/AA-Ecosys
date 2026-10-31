import asyncio, os, asyncpg, json
NAMES = ["sheeshganj gurudwara sikh temple","sheeshganj gurudwara","janaki temple","meherangarh fort","chaturbhuj temple","meharangadh fort"]
async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    rows = await c.fetch("""select name, country, lat, lng, located_by, geo_status, review_reason,
        geocoder_meta->'relocate' rl, geocoder_meta->'label' lbl
        from shared.destinations where lower(name) = any($1::text[])""", NAMES)
    for r in rows:
        d = dict(r); 
        print("ROW", json.dumps(d, default=str)[:1500])
    await c.close()
asyncio.run(main())
