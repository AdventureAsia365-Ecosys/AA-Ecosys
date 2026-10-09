"""Read-only: active brand rules of every tenant (AA-741 brand-diversity check)."""
import asyncio, json, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""SELECT t.slug, t.name, b.brand_name, b.version, b.brand_type, b.core_idea, b.customer_segment, b.target_markets,
        left(b.style_guide, 300) style, left(b.system_prompt, 200) sysp, b.forbidden_words, b.source_docx_s3_key, b.updated_at
        FROM shared.tenants t LEFT JOIN shared.tenant_brand_rules b ON b.tenant_id=t.tenant_id AND b.is_active ORDER BY t.slug""")
    for r in rows:
        fw = r["forbidden_words"]; fw = json.loads(fw) if isinstance(fw, str) else fw
        print(f"== {r['slug']} ({r['name']}) | brand={r['brand_name']} v{r['version']} | type={r['brand_type']} | markets={r['target_markets']} | docx={r['source_docx_s3_key']} | upd={r['updated_at']:%d/%m}")
        print("   core:", (r["core_idea"] or "")[:150]); print("   segment:", (r["customer_segment"] or "")[:150])
        print("   style:", (r["style"] or "").replace("\n", " ")[:250]); print("   forbidden:", (fw or [])[:15], len(fw or []))
    await c.close()
asyncio.run(main())
