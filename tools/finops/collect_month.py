#!/usr/bin/env python3
"""Collect the monthly cost report inputs inside an app container (FIN-02 / OPS-08, AA-896).

Orchestrator only: run it through tools/ecs/ecsx.sh (ECS exec is blocked for subagents). One run per app container,
because each container's DATABASE_URL reads only its own schemas:

  PART=cis      (default; ECSX_SERVICE=aa-cis-dev-api, login cis_app)
                For every month: the cost-per-app answer of api.services.platform_cost.cost_by_app (the one cost module
                of the admin console, AA-884: acc2 Cost Explorer by App tag and service as stored by the CIS client,
                LLM spend by app, acc3 Bedrock), LLM spend by app / stage / role / account from shared.llm_call_daily +
                shared.llm_call_log, and the published-tour counts for the unit costs.
  PART=booking  (ECSX_SERVICE=aa-booking-dev-api, login booking) trip cases created per month and how many of them
                are confirmed or later (booking.trip_cases).
  PART=crm      (ECSX_SERVICE=aa-crm-dev-api, login crm_app) CRM LLM spend per month, stage and model from its own
                gateway rollup crm.llm_usage_daily (the CRM does not log to shared.llm_call_log, D12).

Environment (ecsx.sh VAR=value pairs):
  MONTHS   comma-separated YYYY-MM list; default: the three whole months before the current UTC month.
  PART     cis | booking | crm (see above).
  REFRESH  1 = PART=cis only: when the stored App-tag Cost Explorer data of a month is stale, refresh that window
           first through the CIS client (platform_cost.refresh_app_snapshot: one Cost Explorer request, about
           0.01 USD per month window). Default 0: read the stored data only, in a read-only transaction.

No new Cost Explorer client (data standard DM-10.4, S243 K-14): Cost Explorer is read only through the CIS module.
Output: one line "FINOPS_BUNDLE <json>" on stdout. Every account_id key is dropped (the root repo is public), so the
bundle can be kept next to the report. Feed it to tools/finops/monthly_cost_report.py --bundle.

Table and column names: docs/architecture/db-schema-reference.md (verified 2026-10-31).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Awaitable, Callable, Optional

MARKER = "FINOPS_BUNDLE "
BUNDLE_VERSION = 1

# Same sources and app rule as platform_cost.AI_SPEND_SQL: rolled-up days from shared.llm_call_daily, the other days
# from shared.llm_call_log, app = coalesce(app, quality_signal ->> 'app', 'cis').
LLM_BY_STAGE_SQL = """
SELECT app, stage, role, account, sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric, 4) AS cost_usd
  FROM (
        SELECT d.app, d.stage, d.role, coalesce(d.account, 'acc2') AS account, d.calls, d.cost_usd
          FROM shared.llm_call_daily d
         WHERE d.day >= $1 AND d.day < $2
        UNION ALL
        SELECT coalesce(l.app, l.quality_signal ->> 'app', 'cis'), l.stage, l.role, coalesce(l.account, 'acc2'),
               1, coalesce(l.cost_usd, 0)
          FROM shared.llm_call_log l
         WHERE l.created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')
           AND l.created_at < ($2::date::timestamp AT TIME ZONE 'UTC')
           AND NOT EXISTS (SELECT 1 FROM shared.llm_call_daily d
                            WHERE d.day = (l.created_at AT TIME ZONE 'UTC')::date)
       ) u
 GROUP BY 1, 2, 3, 4
 ORDER BY cost_usd DESC
"""

# published_at moves on a republish, so the first count is "published or republished in the month".
PUBLISHED_TOURS_SQL = """
SELECT count(*) FILTER (WHERE published_at >= ($1::date::timestamp AT TIME ZONE 'UTC')
                          AND published_at < ($2::date::timestamp AT TIME ZONE 'UTC')) AS published_tours,
       count(*) FILTER (WHERE published_at < ($2::date::timestamp AT TIME ZONE 'UTC')
                          AND (deleted_at IS NULL OR deleted_at >= ($2::date::timestamp AT TIME ZONE 'UTC')))
           AS published_tours_live
  FROM gold_aa_internal.published_tours
"""

CONFIRMED_STATUSES = ("confirmed", "supplier_confirming", "invoice_sent", "payment_pending", "paid",
                      "pre_departure", "on_trip", "completed")

TRIP_CASES_SQL = """
SELECT count(*) AS trip_cases,
       count(*) FILTER (WHERE status = ANY($3::text[])) AS bookings_confirmed
  FROM booking.trip_cases
 WHERE deleted_at IS NULL
   AND created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')
   AND created_at < ($2::date::timestamp AT TIME ZONE 'UTC')
"""

CRM_LLM_SQL = """
SELECT stage, model, sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric, 4) AS cost_usd
  FROM crm.llm_usage_daily
 WHERE day >= $1 AND day < $2
 GROUP BY 1, 2
 ORDER BY cost_usd DESC
"""


def month_start(month: str) -> date:
    try:
        return datetime.strptime(month, "%Y-%m").date()
    except ValueError:
        raise SystemExit(f"MONTHS: {month!r} is not YYYY-MM") from None


def next_month(d: date) -> date:
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def default_months(today: date, count: int = 3) -> list[str]:
    """The ``count`` whole months before ``today``'s month, oldest first."""
    out: list[str] = []
    d = today.replace(day=1)
    for _ in range(count):
        d = date(d.year - (d.month == 1), (d.month - 2) % 12 + 1, 1)
        out.append(d.strftime("%Y-%m"))
    return sorted(out)


def parse_months(raw: Optional[str], today: date) -> list[str]:
    if not raw or not raw.strip():
        return default_months(today)
    months = sorted({m.strip() for m in raw.split(",") if m.strip()})
    for m in months:
        if month_start(m) > today:
            raise SystemExit(f"MONTHS: {m} is in the future")
    return months


def window(month: str, today: date) -> tuple[date, date]:
    """[first day, end) with end = the first of the next month, or tomorrow for the current month."""
    start = month_start(month)
    return start, min(next_month(start), date.fromordinal(today.toordinal() + 1))


def scrub(obj: Any) -> Any:
    """Drop every ``account_id`` key, at any depth (the root repo is public)."""
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items() if k != "account_id"}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    return obj


def jsonable(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    raise TypeError(f"not JSON serialisable: {type(v).__name__}")


def rows(records: Any) -> list[dict[str, Any]]:
    return [{k: (float(v) if isinstance(v, Decimal) else v) for k, v in dict(r).items()} for r in records]


CostFn = Callable[..., Awaitable[dict]]
RefreshFn = Callable[[Any, date, date], Awaitable[dict]]


async def collect_cis(pool: Any, months: list[str], today: date, *, cost_fn: CostFn,
                      refresh_fn: Optional[RefreshFn] = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for m in months:
        start, end = window(m, today)
        cost = await cost_fn(pool, m, refresh_if_stale=False)
        refreshed = None
        if refresh_fn is not None and (cost.get("refresh") or {}).get("stale"):
            refreshed = await refresh_fn(pool, start, end)
            cost = await cost_fn(pool, m, refresh_if_stale=False)
        units = dict((await pool.fetch(PUBLISHED_TOURS_SQL, start, end))[0])
        out[m] = {
            "period_start": start.isoformat(), "period_end_exclusive": end.isoformat(),
            "platform_cost": cost,
            "llm_by_stage": rows(await pool.fetch(LLM_BY_STAGE_SQL, start, end)),
            "units": {k: int(v or 0) for k, v in units.items()},
            "refreshed": refreshed,
        }
    return out


async def collect_booking(conn: Any, months: list[str], today: date) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for m in months:
        start, end = window(m, today)
        r = dict((await conn.fetch(TRIP_CASES_SQL, start, end, list(CONFIRMED_STATUSES)))[0])
        out[m] = {"units": {"trip_cases": int(r["trip_cases"] or 0),
                            "bookings_confirmed": int(r["bookings_confirmed"] or 0)}}
    return out


async def collect_crm(conn: Any, months: list[str], today: date) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for m in months:
        start, end = window(m, today)
        by = rows(await conn.fetch(CRM_LLM_SQL, start, end))
        out[m] = {"crm_llm": {"calls": sum(int(r["calls"] or 0) for r in by),
                              "cost_usd": round(sum(float(r["cost_usd"] or 0) for r in by), 4),
                              "by_stage_model": by}}
    return out


def bundle(part: str, months_data: dict[str, Any], now: datetime) -> dict[str, Any]:
    return scrub({"kind": "finops_bundle", "version": BUNDLE_VERSION, "part": part,
                  "generated_at": now.isoformat(timespec="seconds"), "months": months_data})


async def run(part: str, months: list[str], refresh: bool, now: datetime) -> dict[str, Any]:
    import asyncpg  # in the container image; not needed by the tests

    dsn = os.environ["DATABASE_URL"]
    settings = None if (refresh and part == "cis") else {"default_transaction_read_only": "on"}
    today = now.date()
    if part == "cis":
        from api.services import platform_cost  # the container's /app is on sys.path (ecsx_runner)

        pool = await asyncpg.create_pool(dsn, ssl="require", min_size=1, max_size=2, server_settings=settings)
        try:
            data = await collect_cis(pool, months, today, cost_fn=platform_cost.cost_by_app,
                                     refresh_fn=platform_cost.refresh_app_snapshot if refresh else None)
        finally:
            await pool.close()
    else:
        conn = await asyncpg.connect(dsn, ssl="require", server_settings=settings)
        try:
            data = await (collect_booking if part == "booking" else collect_crm)(conn, months, today)
        finally:
            await conn.close()
    return bundle(part, data, now)


def main() -> int:
    part = os.environ.get("PART", "cis").strip().lower()
    if part not in ("cis", "booking", "crm"):
        raise SystemExit("PART must be cis, booking or crm")
    now = datetime.now(timezone.utc)
    months = parse_months(os.environ.get("MONTHS"), now.date())
    refresh = os.environ.get("REFRESH", "0").strip() == "1"
    out = asyncio.run(run(part, months, refresh, now))
    sys.stdout.write(MARKER + json.dumps(out, default=jsonable, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
