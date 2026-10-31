# S261 AA-997: put back the model point on the 5 destinations the aa997.3 chain moved to a same-name other feature
# (S254-labelled correct before; audit L chain_wrong 'regressed'). DRY=1 (default) prints only; DRY=0 writes in one
# transaction: lat/lng := relocate.prev, located_by := 'manual' (no relocate selection takes manual rows again),
# geocoder_meta.reverted keeps the replaced point (undo), one acp_shared.audit_log row.
import asyncio, json, os, asyncpg
from datetime import datetime, timezone
NAMES = ["sheeshganj gurudwara", "janaki temple", "meherangarh fort", "chaturbhuj temple", "meharangadh fort"]
DRY = os.environ.get("DRY", "1") != "0"
SEL = """select id, name, country, lat, lng, located_by, geocoder_meta->'relocate' rl from shared.destinations
         where lower(name) = any($1::text[]) and duplicate_of is null and located_by = 'geoapify'
           and geocoder_meta->'relocate'->>'v' = 'aa997.2' and geocoder_meta->'relocate'->>'outcome' = 'confirmed'
           and jsonb_array_length(geocoder_meta->'relocate'->'prev') >= 2"""
async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    async with c.transaction():
        rows = [dict(r) for r in await c.fetch(SEL, NAMES)]
        out = []
        for r in rows:
            rl = json.loads(r["rl"]) if isinstance(r["rl"], str) else r["rl"]
            plat, plng = float(rl["prev"][0]), float(rl["prev"][1])
            out.append({"id": str(r["id"]), "name": r["name"], "from": [r["lat"], r["lng"]], "to": [plat, plng], "moved_km": rl.get("moved_km")})
            if not DRY:
                meta = {"at": datetime.now(timezone.utc).isoformat(), "by": "s261-orchestrator", "from": [r["lat"], r["lng"], r["located_by"]],
                        "reason": "aa997.3 same-name other feature (S261 audit regressed)"}
                await c.execute("""update shared.destinations set lat=$2, lng=$3, located_by='manual', geo_precision='point',
                        geocoder_meta = jsonb_set(coalesce(geocoder_meta,'{}'::jsonb), '{reverted}', $4::jsonb) where id=$1""",
                        r["id"], plat, plng, json.dumps(meta))
        print("ROWS", len(out))
        for o in out: print("ROW", json.dumps(o, default=str))
        if not DRY and out:
            from services.acp_shared.audit_log import write_audit_log
            await write_audit_log(c, tenant_id=None, actor="s261-orchestrator", action="places.relocate.revert_regressed",
                                  resource_type="places_relocate", resource_id="aa997-s261-regressed",
                                  details={"ids": [o["id"] for o in out], "rows": out})
            print("WRITTEN", len(out))
        if DRY: print("DRY RUN: nothing written")
    await c.close()
asyncio.run(main())
