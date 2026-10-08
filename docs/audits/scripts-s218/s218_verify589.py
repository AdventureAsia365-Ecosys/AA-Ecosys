import asyncio, json, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from datetime import datetime
from urllib.parse import urlparse
from services.content_generation.forbidden_words import all_forbidden, has_word
async def main():
    since = datetime.fromisoformat(open("/tmp/since.txt").read().strip().replace("Z", "+00:00")) if False else None
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    tw = await c.fetchval("""SELECT forbidden_words FROM shared.tenant_brand_rules WHERE tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND is_active ORDER BY (brand_name='default') DESC, version DESC LIMIT 1""")
    words = all_forbidden(json.loads(tw) if isinstance(tw, str) else tw)
    S = datetime.fromisoformat("2026-10-08T05:15:00+00:00")
    at = await c.fetch("SELECT text FROM acp_contract.v_active_tour_atoms WHERE created_at >= $1", S)
    print("new atoms since deploy", len(at), "| with forbidden word", sum(1 for a in at if any(has_word(a[0] or "", w) for w in words)))
    r = await c.fetchrow("SELECT count(*) n, count(revalidate_passed) set_, count(*) FILTER (WHERE revalidate_passed) t FROM silver_aa_internal.generated_content WHERE created_at >= $1", S)
    print("new versions", dict(r))
    await c.close()
asyncio.run(main())
