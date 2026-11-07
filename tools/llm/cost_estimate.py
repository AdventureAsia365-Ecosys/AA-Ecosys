"""Cost estimate for a planned run, from the measured $/call (or $/tour) of the last days (AA-1024 G18). Read-only.

A paid run is announced with a number from this tool, never from feel (lesson family 14: "< $1" quoted for a wave that
cost $6.42). The estimate states its source query and window, so a reader can check it.

Runs inside the CIS api container through the ecsx wrapper (tools/ecs/), env-style arguments:
    <ecsx> tools/llm/cost_estimate.py COST_STAGE=s1_generate COST_N=50 [COST_PER=tour|call] [COST_DAYS=7]
COST_STAGE is a stage name or a prefix ending in '_' or '%' (s1_ = every stage starting with s1_). COST_PER=tour
divides by distinct tour_id (the unit of a wave), call by calls. Reads stage / role / model / cost / tour_id columns of
shared.llm_call_log (cis_app); shadow calls count (they are billed). No LLM call, no write, no cost.

Exit: 0 estimate printed | 2 bad arguments | 3 no basis (no priced call of that stage in the window: say so, do not
guess a number).
"""

from __future__ import annotations

import asyncio
import os
import sys

SQL = """
SELECT model, role, count(*) AS calls, count(DISTINCT tour_id) AS tours, coalesce(sum(cost_usd), 0) AS usd,
       count(*) FILTER (WHERE cost_usd IS NULL) AS unpriced
FROM shared.llm_call_log
WHERE created_at > now() - make_interval(days => $2) AND stage LIKE $1
GROUP BY 1, 2
ORDER BY 5 DESC
"""

TOURS_SQL = """
SELECT count(DISTINCT tour_id) FROM shared.llm_call_log
WHERE created_at > now() - make_interval(days => $2) AND stage LIKE $1
"""


def stage_pattern(stage: str) -> str:
    s = stage.strip()
    if not s:
        raise ValueError("COST_STAGE is required (a stage, or a prefix ending in '_' or '%')")
    if s.endswith("%"):
        return s
    return s + "%" if s.endswith("_") else s


def parse(env: dict) -> tuple[str, float, str, int]:
    pattern = stage_pattern(env.get("COST_STAGE") or "")
    try:
        n = float(env.get("COST_N") or "")
    except ValueError:
        raise ValueError("COST_N is required: how many tours (COST_PER=tour) or calls the run makes") from None
    per = (env.get("COST_PER") or "tour").strip()
    if per not in ("tour", "call"):
        raise ValueError("COST_PER is tour or call")
    days = int(env.get("COST_DAYS") or 7)
    if n <= 0 or days <= 0:
        raise ValueError("COST_N and COST_DAYS must be > 0")
    return pattern, n, per, days


def estimate(rows: list[dict], tours: int, n: float, per: str) -> dict | None:
    """Projection from the window's rows (tours: distinct tour_id over all of them), or None when there is no basis."""
    usd = sum(float(r["usd"] or 0) for r in rows)
    calls = sum(int(r["calls"]) for r in rows)
    units = tours if per == "tour" else calls
    if usd <= 0 or units <= 0:
        return None
    unit_cost = usd / units
    return {"usd": usd, "calls": calls, "units": units, "unit_cost": unit_cost, "projected": unit_cost * n,
            "unpriced": sum(int(r["unpriced"]) for r in rows)}


def render(rows: list[dict], tours: int, pattern: str, n: float, per: str, days: int) -> tuple[list[str], int]:
    est = estimate(rows, tours, n, per)
    head = f"== cost estimate: stage LIKE '{pattern}', last {days} days of shared.llm_call_log, per {per}"
    if est is None:
        return [head, f"== NO BASIS: no priced call of stage '{pattern}' in the last {days} days. Do not quote a "
                      f"number: run a trial of about 3 tours and estimate from it."], 3
    lines = [head, f"  {'model':<34} {'role':<9} {'calls':>7} {'tours':>6} {'USD':>10}"]
    for r in rows:
        lines.append(f"  {r['model'][:34]:<34} {r['role']:<9} {int(r['calls']):>7} {int(r['tours']):>6} "
                     f"{float(r['usd'] or 0):>10.4f}")
    lines.append(f"== basis: {est['usd']:.4f} USD over {est['units']} {per}s ({est['calls']} calls) = "
                 f"{est['unit_cost']:.5f} USD per {per}")
    if est["unpriced"]:
        lines.append(f"== {est['unpriced']} calls without a price in the basis: the estimate is low by those")
    lines.append(f"== ESTIMATE for {n:g} {per}s: {est['projected']:.2f} USD (measured, not a quote; the actual "
                 f"comes from spend_by_stage.py after the run)")
    lines.append("   source query: " + " ".join(SQL.split()) + f"   [$1='{pattern}', $2={days}]")
    return lines, 0


async def fetch(pattern: str, days: int) -> tuple[list[dict], int]:
    import asyncpg  # in the container only; the unit tests never import it

    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        return [dict(r) for r in await c.fetch(SQL, pattern, days)], int(await c.fetchval(TOURS_SQL, pattern, days))
    finally:
        await c.close()


def main(env: dict | None = None, rows: list[dict] | None = None, tours: int = 0) -> int:
    env = dict(os.environ if env is None else env)
    try:
        pattern, n, per, days = parse(env)
    except ValueError as e:
        print(f"cost_estimate: {e}", file=sys.stderr)
        return 2
    if rows is None:
        rows, tours = asyncio.run(fetch(pattern, days))
    lines, code = render(rows, tours, pattern, n, per, days)
    for line in lines:
        print(line, flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
