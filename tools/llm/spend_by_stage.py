"""Spend by stage, provider and model from the one cost source, shared.llm_call_log (AA-1024 G18). Read-only.

Lessons (skill/aa-lessons/guards.md, family 14): a cost quoted from feel ("< $1" against a real $6.42), Jev / typesafe
rows reported as LLM fallback, and totals that were too low because ledger writes had failed (S224: $7.05 in the
ledger against $11.8 on the provider's dashboard). A wave report, a session block or a Jira draft quotes spend from
this tool's output, never from memory.

Runs inside the CIS api container through the ecsx wrapper (tools/ecs/), env-style arguments:
    <ecsx> tools/llm/spend_by_stage.py [SPEND_HOURS=24] [SPEND_FROM=2026-11-06T00:00Z SPEND_TO=...]
                                       [SPEND_STAGE=s1_] [SPEND_WRITE_FAILURES=<count>]
Uses the container's DATABASE_URL (cis_app) and reads only stage / role / provider / model / status / cost columns
of shared.llm_call_log (no tenant, actor, prompt or tour text). No LLM call, no write, no cost.

Output, always grouped by stage, provider and model:
  - LLM USD (roles writer / judge / validate / embed) and non-LLM USD (decide = typesafe / Jev, data = DataForSEO /
    Geoapify, guard = Bedrock Guardrails) in separate columns; a non-LLM row is never counted as LLM;
  - shadow calls (billed, not served) marked, calls without a price counted;
  - the total line is "TOTAL" only when SPEND_WRITE_FAILURES=0 was given: the ledger misses every call whose log
    write failed (CloudWatch events *_log_write_failed). Otherwise it is "LOWER BOUND", with the one-line Logs
    Insights query that gives the count for the same window.
Exit: 0 printed | 2 bad arguments.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

LLM_ROLES = frozenset({"writer", "judge", "validate", "embed"})
NON_LLM = {"decide": "decide (typesafe / Jev)", "data": "data (DataForSEO / Geoapify)", "guard": "guard (Guardrails)"}
LOG_GROUPS = "/ecs/aa-cis-dev"  # CIS api + worker (Infra modules/ecs: /ecs/<project>-<environment>)
FAILED_EVENTS = ("llm_call_log_write_failed", "llm_call_log_pool_write_failed", "llm_call_log_write_failed_sync",
                 "decision_log_write_failed")

SQL = """
SELECT stage, coalesce(provider, '?') AS provider, model, role, coalesce(is_shadow, false) AS shadow,
       count(*) AS calls, coalesce(sum(cost_usd), 0) AS usd,
       count(*) FILTER (WHERE cost_usd IS NULL) AS unpriced,
       count(*) FILTER (WHERE coalesce(status, 'ok') <> 'ok') AS not_ok
FROM shared.llm_call_log
WHERE created_at >= $1 AND created_at < $2 AND ($3::text IS NULL OR stage LIKE $3 || '%')
GROUP BY 1, 2, 3, 4, 5
ORDER BY 7 DESC, 1, 2, 3
"""


def kind(role: str | None) -> str:
    """'llm' or the non-LLM column a role belongs to. An unknown role is not LLM (it would inflate the LLM total)."""
    if role in LLM_ROLES:
        return "llm"
    return NON_LLM.get(role or "", f"other ({role or 'no role'})")


def parse_time(raw: str) -> datetime:
    t = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def window(env: dict, now: datetime) -> tuple[datetime, datetime]:
    if env.get("SPEND_FROM"):
        start = parse_time(env["SPEND_FROM"])
        end = parse_time(env["SPEND_TO"]) if env.get("SPEND_TO") else now
    else:
        end = now
        start = end - timedelta(hours=float(env.get("SPEND_HOURS") or 24))
    if start >= end:
        raise ValueError(f"empty window {start:%Y-%m-%dT%H:%MZ} .. {end:%Y-%m-%dT%H:%MZ}")
    return start, end


def write_failures(env: dict) -> int | None:
    raw = (env.get("SPEND_WRITE_FAILURES") or "").strip()
    if raw == "":
        return None
    n = int(raw)
    if n < 0:
        raise ValueError("SPEND_WRITE_FAILURES must be >= 0")
    return n


def aggregate(rows: list[dict]) -> dict:
    """Totals per column; rows are the SQL result (dicts with stage, provider, model, role, shadow, calls, usd...)."""
    out = {"llm": 0.0, "non_llm": {}, "shadow_usd": 0.0, "calls": 0, "unpriced": 0, "not_ok": 0}
    for r in rows:
        usd = float(r["usd"] or 0)
        k = kind(r["role"])
        if k == "llm":
            out["llm"] += usd
        else:
            out["non_llm"][k] = out["non_llm"].get(k, 0.0) + usd
        if r["shadow"]:
            out["shadow_usd"] += usd
        out["calls"] += int(r["calls"])
        out["unpriced"] += int(r["unpriced"])
        out["not_ok"] += int(r["not_ok"])
    out["total"] = out["llm"] + sum(out["non_llm"].values())
    return out


def insights_query(start: datetime, end: datetime) -> str:
    events = "|".join(FAILED_EVENTS)
    return (f"aws logs start-query --log-group-names {LOG_GROUPS} --start-time {int(start.timestamp())} "
            f"--end-time {int(end.timestamp())} --query-string \"filter @message like /{events}/ | stats count() as n\" "
            f"--profile aa365-admin --region us-west-1")


def total_label(failures: int | None) -> str:
    if failures == 0:
        return "TOTAL"
    if failures is None:
        return "LOWER BOUND (log-write failures not checked: run the query below, then SPEND_WRITE_FAILURES=<n>)"
    return (f"LOWER BOUND ({failures} ledger writes failed in the window: those calls were billed but are not here; "
            f"compare the provider dashboards)")


def render(rows: list[dict], start: datetime, end: datetime, stage: str | None, failures: int | None) -> list[str]:
    agg = aggregate(rows)
    cols = list(NON_LLM.values()) + sorted(k for k in agg["non_llm"] if k not in NON_LLM.values())
    lines = [f"== spend {start:%Y-%m-%dT%H:%MZ} .. {end:%Y-%m-%dT%H:%MZ}"
             + (f", stages {stage}*" if stage else ", all stages") + " (source: shared.llm_call_log)"]
    lines.append(f"  {'stage':<28} {'provider':<14} {'model':<34} {'calls':>7} {'LLM USD':>10} {'non-LLM USD':>12}")
    for r in rows:
        usd = float(r["usd"] or 0)
        k = kind(r["role"])
        llm, other = (f"{usd:.4f}", "") if k == "llm" else ("", f"{usd:.4f} {k.split(' ')[0]}")
        flags = (" shadow" if r["shadow"] else "") + (f" {r['unpriced']} unpriced" if r["unpriced"] else "")
        lines.append(f"  {r['stage'][:28]:<28} {r['provider'][:14]:<14} {r['model'][:34]:<34} {int(r['calls']):>7} "
                     f"{llm:>10} {other:>12}{flags}")
    lines.append(f"== LLM: {agg['llm']:.4f} USD")
    for c in cols:
        if c in agg["non_llm"]:
            lines.append(f"== non-LLM {c}: {agg['non_llm'][c]:.4f} USD")
    if agg["shadow_usd"]:
        lines.append(f"== of which shadow calls (billed, not served): {agg['shadow_usd']:.4f} USD")
    if agg["unpriced"]:
        lines.append(f"== {agg['unpriced']} calls carry no price (cost_usd NULL): the total misses them")
    lines.append(f"== {total_label(failures)}: {agg['total']:.4f} USD over {agg['calls']} calls "
                 f"({agg['not_ok']} not ok)")
    if failures != 0:
        lines.append(f"   write-failure count for this window: {insights_query(start, end)}")
    return lines


async def fetch(start: datetime, end: datetime, stage: str | None) -> list[dict]:
    import asyncpg  # in the container only; the unit tests never import it

    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        return [dict(r) for r in await c.fetch(SQL, start, end, stage)]
    finally:
        await c.close()


def main(env: dict | None = None, now: datetime | None = None, rows: list[dict] | None = None) -> int:
    env = dict(os.environ if env is None else env)
    try:
        start, end = window(env, now or datetime.now(timezone.utc))
        failures = write_failures(env)
    except ValueError as e:
        print(f"spend_by_stage: {e}", file=sys.stderr)
        return 2
    stage = (env.get("SPEND_STAGE") or "").strip() or None
    if rows is None:
        rows = asyncio.run(fetch(start, end, stage))
    for line in render(rows, start, end, stage, failures):
        print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
