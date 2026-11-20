"""S286 AA-1051 follow-up — repair shared.job.cost_usd of jobs whose LLM spend was counted twice (CIS api container,
role cis_app via the container DATABASE_URL; cis_app has SELECT/UPDATE on shared.job, SELECT on shared.llm_call_log).

Why: since AA-1078 (S277) shared.job.cost_usd = the handler's ctx.add_cost total + the job's llm_call_log sum, and the
stamp progress.cost_stamp.llm_usd keeps the LLM part. Six job kinds also passed their LLM spend to ctx.add_cost (fixed
in the CIS PR of this lane), so their handler part (cost_usd - stamp) equals the stamped LLM part: the Jobs page shows
twice the ledger (W5 proofs: S1 6.22 vs 3.11 USD, T2 4.99 vs 2.50 USD).

Selection (class "stamped", always): a finished job (succeeded / failed / stopped_budget / cancelled) of an affected
kind whose stamp is > 0 and whose handler part equals the stamped LLM part within TOLERANCE_USD, not already repaired.
Rows without a stamp were written before the AA-1078 deploy; with INCLUDE_LEGACY=1 the class "legacy" adds those
whose cost_usd (then the handler part) equals the job's live ledger sum (the read side doubled them too).
Rows whose handler part is close to but not equal to the LLM part are only COUNTED ("near", never changed).

Repair: stamped -> cost_usd := the stamped LLM part (handler part 0); legacy -> cost_usd := 0. Both keep the old value
in progress.aa1051_cost_fix {before_usd, class, at} (reversible, and a second run skips the row). The Jobs page then
reads handler part (0) + the live ledger sum = the ledger once.

Modes (destructive-ops style, skill aa-cis-schema references/destructive-ops.md):
  DRY RUN (default)          prints counts per kind and class, the top rows by excess, and FINGERPRINT (md5 of the
                             selected ids + updated_at). Changes nothing.
  APPLY=1 FINGERPRINT=<pin>  one transaction: re-selects, refuses unless the pin matches the DRY RUN, updates exactly
                             those rows (re-checking the predicate), refuses unless the updated count equals the
                             selected count, commits; then verifies on a NEW connection.
Prints ids, kinds, statuses and amounts only (no payload / result text). Exit 1 on a refusal or a failed check.
"""
import asyncio
import json
import os
import sys
from decimal import Decimal

import asyncpg

KINDS = ["writing_memory_r2", "writing_memory_shadow", "writing_memory_mine", "supply_content_draft", "place_dedupe",
         "embedding_reembed"]
FINISHED = ["succeeded", "failed", "stopped_budget", "cancelled"]
TOLERANCE_USD = Decimal("0.000002")         # add_cost rounds to 6 dp; the ledger is numeric(10,6)
NEAR_RATIO = 0.05                 # "near": handler part within 5 % of the stamp (reported only)
FIX_MARKER = "aa1051_cost_fix"
APPLY = os.environ.get("APPLY") == "1"
PIN = os.environ.get("FINGERPRINT", "")
LEGACY = os.environ.get("INCLUDE_LEGACY") == "1"
# S286 review: in these six kinds the handler part was only ever LLM spend, so with ALL_HANDLER=1 every stamped row
# with a handler part > 0 is a double (rounding over many calls can exceed TOLERANCE_USD).
ALL_HANDLER = os.environ.get("ALL_HANDLER") == "1"
if ALL_HANDLER:
    TOLERANCE_USD = Decimal("1000000")

STAMP = "(j.progress->'cost_stamp'->>'llm_usd')::numeric"
LEDGER = "(SELECT coalesce(sum(l.cost_usd), 0) FROM shared.llm_call_log l WHERE l.job_id = j.id)"

# $1 kinds, $2 finished statuses, $3 tolerance, $4 include legacy
SELECTED_CTE = f"""
WITH cand AS (
    SELECT j.id, j.kind, j.status, j.updated_at, j.cost_usd,
           CASE WHEN j.progress ? 'cost_stamp' THEN 'stamped' ELSE 'legacy' END AS klass,
           CASE WHEN j.progress ? 'cost_stamp' THEN {STAMP} ELSE {LEDGER} END AS llm_usd
      FROM shared.job j
     WHERE j.kind = ANY($1::text[]) AND j.status = ANY($2::text[]) AND NOT j.progress ? '{FIX_MARKER}'
       AND j.cost_usd > 0
), sel AS (
    SELECT c.*, (c.cost_usd - CASE WHEN c.klass = 'stamped' THEN c.llm_usd ELSE 0 END) AS handler_usd
      FROM cand c
     WHERE c.llm_usd > 0 AND (c.klass = 'stamped' OR $4::boolean)
)
"""
DOUBLE = "(handler_usd > 0.0000005 AND abs(handler_usd - llm_usd) <= $3::numeric)"

SUMMARY_SQL = SELECTED_CTE + f"""
SELECT kind, klass, count(*) FILTER (WHERE {DOUBLE})::int AS n_double,
       coalesce(sum(handler_usd) FILTER (WHERE {DOUBLE}), 0)::float AS excess_usd,
       count(*) FILTER (WHERE NOT {DOUBLE} AND handler_usd > 0
                        AND abs(handler_usd - llm_usd) <= llm_usd * {NEAR_RATIO})::int AS n_near
  FROM sel GROUP BY kind, klass ORDER BY kind, klass
"""
PIN_SQL = SELECTED_CTE + f"""
SELECT count(*)::int AS n, coalesce(sum(handler_usd), 0)::float AS excess_usd,
       md5(coalesce(string_agg(id::text || updated_at::text, ',' ORDER BY id), '')) AS pin,
       coalesce(array_agg(id ORDER BY id), '{{}}') AS ids
  FROM sel WHERE {DOUBLE}
"""
TOP_SQL = SELECTED_CTE + f"""
SELECT id::text AS id, kind, status, klass, cost_usd::float AS cost_usd, llm_usd::float AS llm_usd,
       handler_usd::float AS handler_usd
  FROM sel WHERE {DOUBLE} ORDER BY handler_usd DESC, id LIMIT 15
"""
# Re-checks the predicate per row: a row that changed since the DRY RUN is not touched (the count check then refuses).
UPDATE_SQL = f"""
UPDATE shared.job j SET
    cost_usd = CASE WHEN j.progress ? 'cost_stamp' THEN {STAMP} ELSE 0 END,
    progress = j.progress || jsonb_build_object('{FIX_MARKER}', jsonb_build_object(
        'before_usd', j.cost_usd, 'at', now(),
        'class', CASE WHEN j.progress ? 'cost_stamp' THEN 'stamped' ELSE 'legacy' END))
 WHERE j.id = ANY($1::uuid[]) AND j.status = ANY($2::text[]) AND NOT j.progress ? '{FIX_MARKER}'
   AND CASE WHEN j.progress ? 'cost_stamp'
            THEN abs((j.cost_usd - {STAMP}) - {STAMP}) <= $3::numeric AND {STAMP} > 0 AND j.cost_usd - {STAMP} > 0.0000005
            ELSE $4::boolean AND abs(j.cost_usd - {LEDGER}) <= $3::numeric AND {LEDGER} > 0 END
"""
# After the repair: every repaired row has handler part 0, so the Jobs page reads 0 + live ledger = the ledger once.
VERIFY_SQL = f"""
SELECT count(*)::int AS repaired,
       count(*) FILTER (WHERE j.cost_usd - coalesce({STAMP}, 0) > $2::numeric)::int AS still_off
  FROM shared.job j WHERE j.id = ANY($1::uuid[]) AND j.progress ? '{FIX_MARKER}'
"""


def out(step: str, **kw) -> None:
    print(json.dumps({"step": step, **kw}, default=str), flush=True)


async def connect() -> asyncpg.Connection:
    return await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")


async def main() -> int:
    args = (KINDS, FINISHED, TOLERANCE_USD, LEGACY)
    conn = await connect()
    try:
        for r in await conn.fetch(SUMMARY_SQL, *args):
            out("summary", **dict(r))
        for r in await conn.fetch(TOP_SQL, *args):
            out("row", **dict(r))
        pin = await conn.fetchrow(PIN_SQL, *args)
        out("dry_run", n=pin["n"], excess_usd=round(pin["excess_usd"], 6), FINGERPRINT=pin["pin"],
            include_legacy=LEGACY, apply=APPLY)
        if not APPLY:
            return 0
        if pin["n"] == 0:
            out("apply_refused", reason="nothing selected")
            return 1
        async with conn.transaction():
            again = await conn.fetchrow(PIN_SQL, *args)
            if not PIN or again["pin"] != PIN:
                out("apply_refused", reason="FINGERPRINT does not match the current selection: run the DRY RUN again",
                    expected=PIN, current=again["pin"])
                return 1
            status = await conn.execute(UPDATE_SQL, list(again["ids"]), FINISHED, TOLERANCE_USD, LEGACY)
            updated = int(status.split()[-1])
            if updated != again["n"]:
                out("apply_refused", reason="updated count differs from the DRY RUN (rolled back)",
                    selected=again["n"], updated=updated)
                raise RuntimeError("rollback")
            out("applied", updated=updated, excess_removed_usd=round(again["excess_usd"], 6))
        ids = list(again["ids"])
    except RuntimeError as e:
        if str(e) == "rollback":
            return 1
        raise
    finally:
        await conn.close()
    check = await connect()          # verify on a new connection, never the transaction's
    try:
        v = await check.fetchrow(VERIFY_SQL, ids, Decimal("0.000002"))
        left = await check.fetchrow(PIN_SQL, *args)
    finally:
        await check.close()
    ok = v["repaired"] == len(ids) and v["still_off"] == 0 and left["n"] == 0
    out("verify", ok=ok, repaired=v["repaired"], still_off=v["still_off"], still_selected=left["n"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
