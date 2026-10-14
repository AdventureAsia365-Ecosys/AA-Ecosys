"""S235 read-only AI governance audit: Jev questions (mode, 30d volume/cost, last use), judge/shadow routes,
every route touching the OpenAI platform API, 30d llm_call_log by provider (incl. tenant content), shadow spend."""
import asyncio, asyncpg, boto3, json
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip()
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require",
                              server_settings={"default_transaction_read_only": "on"})
    out = {}
    out["jev_questions"] = [dict(r) for r in await c.fetch("""
      select q.question_key, q.stage, q.mode, q.calibration_ref is not null as calibrated, q.updated_at, q.updated_by,
        coalesce(l.n30,0) n30, coalesce(l.cost30,0) cost30, l.last_at, coalesce(l.n7,0) n7, coalesce(l.cost7,0) cost7
      from shared.decision_question q left join (
        select question_key, count(*) n30, round(sum(coalesce(cost_usd,0)),4) cost30, max(created_at) last_at,
               count(*) filter (where created_at > now()-interval '7 days') n7,
               round(sum(coalesce(cost_usd,0)) filter (where created_at > now()-interval '7 days'),4) cost7
        from shared.decision_log where created_at > now()-interval '30 days' group by 1) l using (question_key)
      order by q.mode, cost30 desc nulls last""")]
    out["jev_allowlist"] = await c.fetchval("select count(*) from shared.jev_tenant_allowlist")
    out["routes"] = [dict(r) for r in await c.fetch("""
      select r.stage, r.role, r.provider, r.model_id, r.account_route, r.fallback_model_ids, r.shadow_model_id, r.shadow_sample_pct, r.is_active, r.updated_at
      from shared.llm_role_config r order by r.stage""")]
    out["catalog"] = [dict(r) for r in await c.fetch("select model_key, vendor, provider, callable_via, enabled from shared.llm_model_catalog order by model_key")]
    out["calls_30d_by_provider"] = [dict(r) for r in await c.fetch("""
      select coalesce(provider,'?') provider, coalesce(account,'?') account, count(*) n, round(sum(coalesce(cost_usd,0)),4) cost,
             count(*) filter (where tenant_id is not null) n_tenant
      from shared.llm_call_log where created_at > now()-interval '30 days' group by 1,2 order by cost desc""")]
    out["openai_30d_by_stage"] = [dict(r) for r in await c.fetch("""
      select stage, model, count(*) n, round(sum(coalesce(cost_usd,0)),4) cost, count(*) filter (where tenant_id is not null) n_tenant, max(created_at) last_at
      from shared.llm_call_log where created_at > now()-interval '30 days' and (provider ilike '%openai%' or account ilike '%openai%')
      group by 1,2 order by n desc""")]
    out["shadow_30d"] = [dict(r) for r in await c.fetch("""
      select stage, shadow_model, count(*) n, round(sum(coalesce(shadow_cost_usd,0)),4) cost, max(created_at) last_at
      from shared.llm_shadow_log where created_at > now()-interval '30 days' group by 1,2 order by cost desc""")]
    boto3.client("s3", region_name="us-west-1").put_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/s235/ai_audit.json",
        Body=json.dumps(out, default=str, indent=1).encode())
    print("AUDIT ok", {k: (len(v) if isinstance(v, list) else v) for k, v in out.items()})
    await c.close()
asyncio.run(main())
