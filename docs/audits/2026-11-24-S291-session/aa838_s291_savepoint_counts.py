"""AA-838 S291 lane i-followups: savepoint-like pg_stat_statements entries per role on the shared RDS. READ-ONLY,
counts only.

Run like aa838_s291_crm_load_counts.py: AA-CIS-Infra DB Migrate `mode=run-script` (master login, so every role's
statement texts are visible; READ_ONLY = True makes the runner open the session read-only; the runner awaits
`main(conn)`). Takes two snapshots WINDOW_S apart. Never writes, never resets pg_stat_statements, never reads a table
row: only pg_stat_statements / pg_stat_statements_info counters and pg_roles. Prints no statement text.

Per role (crm_app, booking, cis_app and any other role that has such entries) it counts the entries whose text is a
savepoint statement (SAVEPOINT / RELEASE [SAVEPOINT] / ROLLBACK TO), split into:
  asyncpg = asyncpg's counter names (__asyncpg_savepoint_<n>__): one new text per nested transaction (the churn);
  depth   = the S291 depth names (crm_sp_<n> AA-Partner #389, bk_sp_<n> AA-Booking, cis_sp_<n> AA-CIS-App);
and how many asyncpg-named entries appeared during the window (new_asyncpg_per_min).

Expected once the three deploys are live: new_asyncpg_per_min falls to 0 for every role; depth entries stay a handful
(at most 3 x the deepest nesting per role); the old asyncpg entries are evicted over time (dealloc_per_min drops).
Every line starts with "COUNTS ".
"""

import asyncio

READ_ONLY = True
WINDOW_S = 120

ROLE_SQL = """
WITH sp AS (
  SELECT r.rolname, s.query, s.calls
    FROM pg_stat_statements s JOIN pg_roles r ON r.oid = s.userid
   WHERE s.query ~* '^\\s*(SAVEPOINT|RELEASE|ROLLBACK\\s+TO)\\s'
)
SELECT rolname,
       count(*)::int AS entries,
       count(*) FILTER (WHERE position('__asyncpg_savepoint_' IN query) > 0)::int AS asyncpg,
       count(*) FILTER (WHERE query ~ '(crm|bk|cis)_sp_[0-9]+')::int AS depth,
       coalesce(sum(calls) FILTER (WHERE query ~ '(crm|bk|cis)_sp_[0-9]+'), 0)::bigint AS depth_calls
  FROM sp
 GROUP BY rolname
 ORDER BY rolname
"""
TOTAL_SQL = "SELECT count(*)::int AS n FROM pg_stat_statements"
DEALLOC_SQL = "SELECT dealloc::bigint AS d FROM pg_stat_statements_info"
ROLES = ("crm_app", "booking", "cis_app")


def out(*parts):
    print("COUNTS", *parts, flush=True)


async def snapshot(conn):
    rows = {r["rolname"]: dict(r) for r in await conn.fetch(ROLE_SQL)}
    return rows, await conn.fetchval(DEALLOC_SQL), await conn.fetchval(TOTAL_SQL)


async def main(conn):
    first, dealloc_1, _ = await snapshot(conn)
    await asyncio.sleep(WINDOW_S)
    second, dealloc_2, total = await snapshot(conn)
    minutes = WINDOW_S / 60
    empty = {"entries": 0, "asyncpg": 0, "depth": 0, "depth_calls": 0}
    for role in sorted(set(ROLES) | set(first) | set(second)):
        a, b = first.get(role, empty), second.get(role, empty)
        new_asyncpg = max(b["asyncpg"] - a["asyncpg"], 0)
        out(f"[role] {role} savepoint_entries={b['entries']} asyncpg_named={b['asyncpg']} depth_named={b['depth']} "
            f"depth_calls={b['depth_calls']} new_asyncpg_per_min={new_asyncpg / minutes:.1f}")
    out(f"[evictions] dealloc_per_min={(dealloc_2 - dealloc_1) / minutes:.2f} all_entries={total}")
    out(f"[window] seconds={WINDOW_S}")


if __name__ == "__main__":
    raise SystemExit("run through AA-CIS-Infra DB Migrate mode=run-script (it awaits main(conn))")
