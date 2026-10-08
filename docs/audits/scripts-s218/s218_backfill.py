"""AA-738 backfill: deterministic forbidden-word strip on ACTIVE masters published before the gate.
MODE=dry (default) -> counts + sample diffs, no writes.  MODE=apply -> S3 export of old values, one
transaction (published_tours + its generated_content), verify on a fresh connection."""
import asyncio, json, os, sys, difflib
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from collections import Counter
from services.content_generation.forbidden_strip import strip_forbidden
from services.content_generation.forbidden_words import all_forbidden, has_word, copy_text

COLS = {"aa_name": "name", "aa_subtitle": "subtitle", "aa_summary": "summary", "aa_description": "description",
        "aa_highlights": "highlights", "aa_itineraries": "itineraries", "seo_title": "seo_title", "seo_meta": "seo_meta"}
MODE = os.environ.get("MODE", "dry")
S3 = boto3.client("s3", region_name="us-west-1"); BUCKET = "aa-cis-bronze-005097885195"

def as_val(v, col=None):
    # only aa_highlights is jsonb; text fields can legitimately start with "["
    if col == "aa_highlights" and isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return v
    return v

def strip_row(row, tw):
    gen = {COLS[c]: as_val(row[c], c) for c in COLS if row[c] is not None}
    out, rep = strip_forbidden(gen, tw)
    changed = {c: out[COLS[c]] for c in COLS if COLS[c] in out and out[COLS[c]] != gen.get(COLS[c])}
    return changed, rep

async def connect():
    dsn = S3 and boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    return await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")

async def main():
    c = await connect()
    tw = await c.fetchval("""SELECT forbidden_words FROM shared.tenant_brand_rules WHERE tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND is_active ORDER BY (brand_name='default') DESC, version DESC LIMIT 1""")
    tw = json.loads(tw) if isinstance(tw, str) else tw
    words = all_forbidden(tw)
    cols = ", ".join(COLS)
    pubs = await c.fetch(f"""SELECT DISTINCT ON (p.tour_id) p.id, p.tour_id, p.generated_content_id, rt.country, rt.src_name, {", ".join("p."+k for k in COLS)}
        FROM gold_aa_internal.published_tours p JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id
        WHERE p.master_status='active' AND rt.source_status='active' ORDER BY p.tour_id, p.published_at DESC""")
    plan, stats, unresolved, before = [], Counter(), Counter(), []
    for p in pubs:
        if not any(has_word(copy_text(as_val(p[k], k)), w) for k in COLS if p[k] for w in words):
            continue
        g = await c.fetchrow(f"SELECT id, {cols} FROM silver_aa_internal.generated_content WHERE id=$1", p["generated_content_id"])
        pch, prep = strip_row(p, tw)
        gch, _ = strip_row(g, tw) if g else ({}, None)
        stats.update(f"replaced:{f}" for f, _ in prep["replaced"]); stats.update(f"dropped:{f}" for f, _ in prep["dropped"])
        unresolved.update(f"{f}:{w}" for f, w in prep["unresolved"])
        plan.append((p, g, pch, gch))
        before.append({"published_id": str(p["id"]), "gc_id": str(p["generated_content_id"]), "tour": p["src_name"],
                       "published_old": {k: as_val(p[k], k) for k in pch}, "gc_old": {k: as_val(g[k], k) for k in gch} if g else {}})
    print(f"MODE={MODE} | masters with a forbidden word: {len(plan)} | published rows to change: {sum(1 for x in plan if x[2])} | gc rows to change: {sum(1 for x in plan if x[3])}")
    print("edits:", dict(stats)); print("unresolved (left as is):", dict(unresolved))
    print("by country:", dict(Counter(x[0]["country"] for x in plan)))
    for p, g, pch, gch in plan[:6]:
        print(f"\n--- {p['country']} | {p['src_name'][:60]}")
        for k, new in pch.items():
            old = as_val(p[k], k); o = old if isinstance(old, str) else json.dumps(old, ensure_ascii=False); n = new if isinstance(new, str) else json.dumps(new, ensure_ascii=False)
            for d in difflib.ndiff(o.split(". "), n.split(". ")):
                if d[:1] in "-+": print("   ", k, d[:230])
    if MODE != "apply":
        await c.close(); return
    key = "scripts/s218_backfill_before.json"
    S3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(before, ensure_ascii=False, default=str).encode())
    print("rollback export:", key, len(before))
    async with c.transaction():
        for p, g, pch, gch in plan:
            for table, rid, ch in (("gold_aa_internal.published_tours", p["id"], pch), ("silver_aa_internal.generated_content", g["id"] if g else None, gch)):
                if not ch or not rid: continue
                sets = ", ".join(f"{k}=${i+2}" + ("::jsonb" if k == "aa_highlights" else "") for i, k in enumerate(ch))
                vals = [json.dumps(v, ensure_ascii=False) if k == "aa_highlights" else v for k, v in ch.items()]
                await c.execute(f"UPDATE {table} SET {sets} WHERE id=$1", rid, *vals)
    await c.close()
    c2 = await connect()   # verify on a fresh connection
    left = 0
    for p, *_ in plan:
        r = await c2.fetchrow(f"SELECT {cols} FROM gold_aa_internal.published_tours WHERE id=$1", p["id"])
        if any(has_word(copy_text(as_val(r[k], k)), w) for k in COLS if r[k] for w in words): left += 1
    print("VERIFY fresh connection: masters still containing a forbidden word:", left, "/", len(plan))
    await c2.close()
asyncio.run(main())
