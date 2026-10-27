"""AA-784 place-card model evaluation (S252, prepared, NOT run). Design: .tmp-session/s252/cardeval/design.md.

Runs INSIDE the aa-cis-dev-api container via the S3-mediated ECS exec pattern (DATABASE_URL = cis_app, app code at /app).
Usage (positional mode, no env vars to set):
    python3 cardeval_run.py dry     # $0: read-only sample of ~30 place groups that need a card + cost estimate -> S3
    python3 cardeval_run.py paid    # paid: drafts + checks per tier, hard cap BUDGET_USD -> S3 (results, blind panel packet)
    python3 cardeval_run.py resume  # paid, continue a run that died (task replaced): keeps done calls and spend so far
The paid mode reads the sample written by the dry run (s3 .../sample.json), so both see the same 30 groups. `paid`
refuses to start when a results.json already exists (no accidental second spend); use `resume`.

Arms differ ONLY by model: the real prompts, parsing and post-processing of services/acp_shared/place_cards.py are
imported (draft_card, check_card, _clean_facts, _clean_aliases, _representative, place_key, find_card_for_draft).
The model is chosen by a thin LLMClient subclass that sets `model_tier` (one catalog key, no route fallback) and the
stage `adhoc_aa784_cardeval`; every call is logged to shared.llm_call_log (draft role=writer, check role=validate).
Nothing is written to acp_shared.* (no card, link, alias or miss rows): the only DB writes are llm_call_log rows.
"""
import asyncio
import contextvars
import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher

sys.path.insert(0, "/app")

import structlog  # noqa: E402

# Keep the exec log short: the app loggers (role-config misses, rekind notes) would print a JSON line per call.
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))

BUCKET = "<bronze-bucket>"
PREFIX = "scripts/s252/cardeval"
STAGE = "adhoc_aa784_cardeval"
BUDGET_USD = 3.00          # hard cap for the paid mode (all tiers together)
N_SAMPLE = 30
CONCURRENCY = 6
MAX_PER_COUNTRY = 3
QUOTA = {"generic": 5, "variant": 6, "homonym": 6, "landmark": 6, "small_local": 7}
CLASS_ORDER = ("generic", "variant", "homonym", "landmark", "small_local")
# Claude 5.5 models think adaptively and the thinking counts against max_tokens (S246 place trial: Haiku 5.5 day
# calls stopped at max_tokens); the Luna models reason inside max_tokens too (place_cards.DRAFT_MAX_TOKENS comment;
# S246: gpt-6-luna had empty replies). Production asks 1500 (draft) / 1024 (check); for a CHALLENGER (key, stage) the
# request is raised to this floor. The live arms (gpt-5.6-luna draft, haiku check) keep production limits, so the
# incumbent is measured exactly as it runs. Billing is per token used, so the floor only removes truncation. A route
# switch to a floored arm needs the same bump in place_cards.py (noted in design.md).
_CHALLENGER_FLOOR = 4000
TOKEN_FLOOR = {("haiku-5-5", "*"): 4000, ("sonnet-5-5", "*"): 4000, ("opus-5-5", "*"): 4000,
               ("gpt-6-luna", "*"): 4000, ("gpt-5.6-luna", "a3_place_card_check"): 4000}
PROD_MAX_TOKENS = {"a3_place_card": 1500, "a3_place_card_check": 1024}   # place_cards.draft_card / check_card
WORST_IN_TOKENS = 2000   # budget reservation: well above the measured ~816 (draft) / ~554 (check) prompt tokens


def token_floor(key, stage):
    return max(TOKEN_FLOOR.get((key, stage), 0), TOKEN_FLOOR.get((key, "*"), 0))

DRAFTERS = {"D1": "gpt-5.6-luna",   # live route since migration 222
            "D3": "sonnet-5-5",     # strong Claude drafter
            "D4": "gpt-6-luna",     # cheaper OpenAI (S246: kept 0.83, empty replies)
            "D5": "haiku-5-5",      # cheapest Claude
            "D2": "sonnet"}         # Sonnet 4.6: S233 drafter + live fallback (tier E, only if budget is left)
CHECKERS = {"C1": "haiku",          # live checker (Haiku 4.5)
            "C2": "gpt-5.6-luna",   # S233 checker
            "C3": "sonnet-5-5",     # strong closed-book checker
            "C4": "opus-5-5"}       # strongest closed-book checker
LIVE_PAIR = ("D1#1", "C1")
LIVE_STAGE_KEYS = {"a3_place_card": "gpt-5.6-luna", "a3_place_card_check": "haiku"}   # migration 222
# Tier order = value order: a budget stop loses the later tiers only (the run stops at the first tier that does not fit).
# "P" = the planted-error cards (built from D1#1). Each checker gets its planted cards in the same tier as its natural
# cells: without them its identity recall has n < 10 and the §7 checker floor cannot be measured (C1/C2 planted are
# cheap, so they come right after A). C4 on D4#1 is the least useful cell (E); Sonnet 4.6 drafts (F) are optional.
TIERS = [
    ("A", [("D1", 1), ("D1", 2), ("D3", 1), ("D4", 1), ("D5", 1)],
          [("C1", ["D1#1", "D1#2", "D3#1", "D4#1", "D5#1"]), ("C2", ["D1#1", "D3#1", "D4#1", "D5#1"])]),
    ("B", [], [("C1", ["P"]), ("C2", ["P"])]),
    ("C", [], [("C3", ["D1#1", "D4#1", "D3#1", "P"])]),
    ("D", [], [("C4", ["D1#1", "P"])]),
    ("E", [], [("C4", ["D4#1"])]),
    ("F", [("D2", 1)], [("C1", ["D2#1"]), ("C2", ["D2#1"])]),
]
# Output-token assumptions for the estimate (reasoning/thinking included); input is measured from the prompts.
DRAFT_OUT = {"gpt-5.6-luna": 700, "gpt-6-luna": 700, "haiku": 350, "sonnet": 400,
             "haiku-5-5": 1000, "sonnet-5-5": 1000, "opus-5-5": 1000}
CHECK_OUT = {"haiku": 100, "gpt-5.6-luna": 400, "gpt-6-luna": 400, "sonnet": 100,
             "haiku-5-5": 600, "sonnet-5-5": 600, "opus-5-5": 600}
LEGACY_VENDOR = {"haiku": "anthropic", "sonnet": "anthropic"}

MISSING_SQL = """
    SELECT ta.atom_id, ta.tour_id::text AS tour_id, ta.place, ta.evidence, ta.itinerary_day, ta.activity_type,
           rt.country, pt.aa_name AS tour_name
      FROM acp_contract.v_active_tour_atoms ta
      LEFT JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id
      LEFT JOIN gold_aa_internal.published_tours pt ON pt.tour_id = ta.tour_id
     WHERE ta.place IS NOT NULL AND btrim(ta.place) <> '' AND NOT ta.deleted AND NOT ta.is_empty_marker
       AND ta.owner_scope = 'platform'   -- AA catalog atoms only: no tenant-owned atom text in the sample / panel
       AND NOT EXISTS (SELECT 1 FROM acp_shared.atom_place_card k WHERE k.atom_id = ta.atom_id)
     ORDER BY ta.atom_id                -- deterministic _representative() tie-breaks
"""
ROUTE_SQL = """SELECT stage, model_id, fallback_model_ids, account_route FROM shared.llm_role_config
                WHERE stage IN ('a3_place_card', 'a3_place_card_check')"""
# Observed output tokens (thinking/reasoning included) of the eval keys on any stage, to sanity-check DRAFT_OUT/CHECK_OUT.
CALIB_MODEL_SQL = """SELECT model, count(*)::int AS n, avg(tokens_out)::int AS tout,
                            percentile_cont(0.9) WITHIN GROUP (ORDER BY tokens_out)::int AS tout_p90
                       FROM shared.llm_call_log
                      WHERE created_at > now() - interval '30 days'
                        AND (model ILIKE '%haiku-5-5%' OR model ILIKE '%sonnet-5-5%' OR model ILIKE '%opus-5-5%'
                             OR model ILIKE '%gpt-6-luna%' OR model ILIKE '%gpt-5.6-luna%')
                      GROUP BY 1 ORDER BY 2 DESC"""
MISS_SQL = "SELECT place_norm, country_norm, reason, rule_version, prompt_sha, retry_after FROM acp_shared.place_card_miss"
CARDS_SQL = "SELECT display_name, country FROM acp_shared.place_card WHERE status <> 'rejected'"
CATALOG_SQL = """SELECT model_key, vendor, enabled, blocked_reason, price_in_per_mtok::float8 AS pin,
                        price_out_per_mtok::float8 AS pout FROM shared.llm_model_catalog"""
CALIB_SQL = """SELECT stage, model, count(*)::int AS n, avg(tokens_in)::int AS tin, avg(tokens_out)::int AS tout,
                      avg(cost_usd)::float8 AS usd
                 FROM shared.llm_call_log
                WHERE stage IN ('a3_place_card', 'a3_place_card_check') AND created_at > now() - interval '90 days'
                GROUP BY 1, 2 ORDER BY 1, 3 DESC"""
LOG_SQL = """SELECT count(*)::int AS n, coalesce(sum(cost_usd), 0)::float8 AS usd FROM shared.llm_call_log
              WHERE stage = $1 AND created_at >= $2::timestamptz"""


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def h(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()


def put(name, obj):
    import boto3
    path = f"/tmp/cardeval_{name}"
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str, ensure_ascii=False)
    boto3.client("s3", region_name="us-west-1").upload_file(path, BUCKET, f"{PREFIX}/{name}")
    print(f"WROTE s3://{BUCKET}/{PREFIX}/{name}", flush=True)


def get(name):
    import boto3
    body = boto3.client("s3", region_name="us-west-1").get_object(Bucket=BUCKET, Key=f"{PREFIX}/{name}")["Body"]
    return json.loads(body.read())


def exists(name):
    import boto3
    try:
        boto3.client("s3", region_name="us-west-1").head_object(Bucket=BUCKET, Key=f"{PREFIX}/{name}")
        return True
    except Exception:  # noqa: BLE001 — 404 (or no access): treat as absent; get() then fails loudly if needed
        return False


async def open_pool():
    import asyncpg
    return await asyncpg.create_pool(os.environ["DATABASE_URL"], ssl="require", min_size=1, max_size=8,
                                     server_settings={"application_name": "aa784-cardeval"})


# ── Sample (read-only, $0) ────────────────────────────────────────────────────────────────────────

def _variant_keys(groups_by_country: dict, card_names_by_country: dict, pc) -> set:
    """Groups whose name is a near-spelling of another group or an existing card of the same country (Burang /
    Purang, Kuang Si Waterfall / Falls): SequenceMatcher ratio >= 0.85 on folded names (>= 0.8 up to 8 letters),
    or the same match_key."""
    out = set()
    for country, keys in groups_by_country.items():
        names = [(k, k[0]) for k in keys if not pc.is_generic_name(k[0])]
        others = [(None, pc.place_norm(n)) for n in card_names_by_country.get(country, [])]
        mkey = {}
        by_len = defaultdict(list)
        for item in names + others:
            mkey[item[1]] = pc.match_key(item[1])
            by_len[len(item[1])].append(item)
        for k, a in names:
            if len(a) < 5:
                continue
            mk = mkey[a]
            for L in range(len(a) - 2, len(a) + 3):
                for k2, b in by_len.get(L, []):
                    if b == a or k2 == k:
                        continue
                    if mkey[b] == mk:
                        out.add(k)
                        break
                    sm = SequenceMatcher(None, a, b)
                    thr = 0.8 if len(a) <= 8 else 0.85   # one letter off in a short name: burang/purang = 0.833
                    if sm.real_quick_ratio() >= thr and sm.quick_ratio() >= thr and sm.ratio() >= thr:
                        out.add(k)
                        break
                if k in out:
                    break
    return out


async def build_sample(pool, pc):
    async with pool.acquire() as conn:
        atoms = [dict(r) for r in await conn.fetch(MISSING_SQL)]
        groups = {}
        for a in atoms:
            if pc.card_skip_reason(a["place"], a.get("activity_type")):
                continue
            groups.setdefault(pc.atom_group_key(a), []).append(a)
        existing = await pc.find_existing_cards(conn, list(groups))
        existing.update(await pc.find_local_cards(conn, groups))
        misses = {(r["place_norm"], r["country_norm"]): dict(r) for r in await conn.fetch(MISS_SQL)}
        cards = [dict(r) for r in await conn.fetch(CARDS_SQL)]
    now = datetime.now(timezone.utc)
    need = {k: g for k, g in groups.items() if k not in existing and not pc.miss_is_active(misses.get(k), now)}

    by_country = defaultdict(list)
    for k in need:
        by_country[k[1]].append(k)
    card_names = defaultdict(list)
    for c in cards:
        card_names[pc.fold(c["country"])].append(c["display_name"])
    variant = _variant_keys(by_country, card_names, pc)
    core_countries = defaultdict(set)
    for k in need:
        if not pc.is_generic_name(k[0]):
            core_countries[pc.core_key(k[0])].add(k[1])
    for c in cards:
        if not pc.is_generic_name(c["display_name"]):
            core_countries[pc.core_key(c["display_name"])].add(pc.fold(c["country"]))

    def klass(k, g):
        place = g[0]["place"]
        if pc.is_generic_name(place):
            return "generic"
        if k in variant or any(ord(ch) > 127 for a in g for ch in a["place"]):
            return "variant"
        if len(core_countries[pc.core_key(k[0])]) >= 2:
            return "homonym"
        tours = {a["tour_id"] for a in g}
        if len(tours) >= 3:
            return "landmark"
        return "small_local" if len(tours) == 1 else "other"

    cands = defaultdict(lambda: defaultdict(list))
    for k, g in need.items():
        rep = pc._representative(g)
        if len((rep.get("evidence") or "").strip()) < 20:
            continue
        cands[klass(k, g)][k[1]].append(k)
    country_rank = sorted(by_country, key=lambda c: (-len(by_country[c]), c))
    picked, per_country, taken = [], defaultdict(int), set()

    def take(cls, quota, cap=MAX_PER_COUNTRY):
        got = 0
        pools = {c: sorted(cands[cls].get(c, []), key=lambda k: h(*k)) for c in country_rank}
        while got < quota and any(pools.values()):
            for c in country_rank:
                if got >= quota:
                    break
                while pools[c] and per_country[c] >= cap:
                    pools[c] = []
                while pools[c] and pools[c][0] in taken:
                    pools[c].pop(0)
                if pools[c]:
                    k = pools[c].pop(0)
                    taken.add(k)
                    picked.append((cls, k))
                    per_country[c] += 1
                    got += 1
        return got

    for cls in CLASS_ORDER:
        take(cls, QUOTA[cls])
    # A class short of candidates: fill from the others (long tail first), then relax the per-country cap.
    for cap in (MAX_PER_COUNTRY, MAX_PER_COUNTRY + 2, N_SAMPLE):
        for cls in ("small_local", "other", "landmark", "homonym", "variant", "generic"):
            if len(picked) < N_SAMPLE:
                take(cls, N_SAMPLE - len(picked), cap)

    sample = []
    for cls, k in picked[:N_SAMPLE]:
        g = need[k]
        rep = pc._representative(g)
        sample.append({
            "group_id": "G" + h(*k)[:8], "class": cls, "place_norm": k[0], "country_norm": k[1],
            "country": rep.get("country"), "place": rep["place"], "atoms": len(g),
            "tours": len({a["tour_id"] for a in g}), "atom_ids": [a["atom_id"] for a in g][:20],
            "rep": {f: rep.get(f) for f in ("atom_id", "place", "evidence", "country", "tour_name",
                                            "activity_type", "itinerary_day")},
        })
    stats = {"need_draft_groups": len(need), "countries": len(by_country),
             "class_pool": {c: sum(len(v) for v in cands[c].values()) for c in list(QUOTA) + ["other"]}}
    return sample, stats


# ── Arms, estimate ───────────────────────────────────────────────────────────────────────────────

async def load_catalog(pool):
    async with pool.acquire() as conn:
        return {r["model_key"]: dict(r) for r in await conn.fetch(CATALOG_SQL)}


def usable_keys(catalog):
    out, notes = {}, []
    for key in set(DRAFTERS.values()) | set(CHECKERS.values()):
        row = catalog.get(key)
        if row is None or not row["enabled"] or row["pin"] is None:
            notes.append(f"SKIP {key}: {'not in catalog' if row is None else (row['blocked_reason'] or 'disabled/no price')}")
        else:
            out[key] = row
    return out, notes


def vendor(key, catalog):
    row = catalog.get(key) or {}
    return row.get("vendor") or LEGACY_VENDOR.get(key, "?")


def est_call(key, kind, in_tok, catalog):
    row = catalog[key]
    out = (DRAFT_OUT if kind == "draft" else CHECK_OUT).get(key, 800)
    return in_tok * row["pin"] / 1e6 + out * row["pout"] / 1e6


def max_tokens_for(key, kind):
    stage = "a3_place_card" if kind == "draft" else "a3_place_card_check"
    return max(PROD_MAX_TOKENS[stage], token_floor(key, stage))


def worst_call(key, kind, catalog):
    """Upper bound of one call's billed cost (generous prompt + the full max_tokens): the per-call budget reservation,
    so the cap holds even if every in-flight call runs to its token limit."""
    row = catalog[key]
    return WORST_IN_TOKENS * row["pin"] / 1e6 + max_tokens_for(key, kind) * row["pout"] / 1e6


def plan_calls(sample, keys):
    """[(tier, kind, arm, target)] in run order; kind 'draft' arm=D#run, kind 'check' arm=C, target=D#run|P."""
    calls = []
    for tier, drafts, checks in TIERS:
        for d, run in drafts:
            if DRAFTERS[d] in keys:
                calls += [(tier, "draft", f"{d}#{run}", s["group_id"]) for s in sample]
        for c, targets in checks:
            if CHECKERS[c] not in keys:
                continue
            for t in targets:
                if t != "P" and DRAFTERS[t.split("#")[0]] not in keys:
                    continue
                if t == "P" and DRAFTERS["D1"] not in keys:
                    continue
                calls += [(tier, "check", c, f"{t}@{s['group_id']}") for s in sample]
    return calls


def estimate(sample, keys, pc):
    draft_in = sum(len(pc._CARD_SYSTEM) + 260 + min(len(s["rep"].get("evidence") or ""), 600) for s in sample) / len(sample) / 3.5
    check_in = (len(pc._CHECK_SYSTEM) + 420 + 6 * 140) / 3.5
    by_tier = defaultdict(float)
    for tier, kind, arm, _ in plan_calls(sample, keys):
        key = DRAFTERS[arm.split("#")[0]] if kind == "draft" else CHECKERS[arm]
        by_tier[tier] += est_call(key, kind, draft_in if kind == "draft" else check_in, keys)
    return {t: round(v, 3) for t, v in by_tier.items()}, round(sum(by_tier.values()), 3), int(draft_in), int(check_in)


# ── Paid run ─────────────────────────────────────────────────────────────────────────────────────

_KEY = contextvars.ContextVar("cardeval_key", default=None)


def install_client(pc):
    from shared.llm_client.client import LLMClient

    class EvalClient(LLMClient):
        """One catalog key per call (model_tier: no route, no fallback, no shadow) under the adhoc stage."""

        def generate(self, request):
            key = _KEY.get()
            if not key:
                raise RuntimeError("cardeval: no model key bound")
            upd = {"stage": STAGE, "model_tier": key}
            floor = token_floor(key, request.stage)   # request.stage is still the production stage here
            if request.max_tokens < floor:
                upd["max_tokens"] = floor
            return super().generate(request.model_copy(update=upd))

    pc.LLMClient = EvalClient  # draft_card / check_card look LLMClient up in their module at call time


class Runner:
    def __init__(self, pool, pc, catalog, sample, started):
        self.pool, self.pc, self.catalog = pool, pc, catalog
        self.started = started
        self.sample = {s["group_id"]: s for s in sample}
        self.sem = asyncio.Semaphore(CONCURRENCY)
        self.budget = asyncio.Condition()
        self.spent = 0.0
        self.reserved = 0.0
        self.inflight = 0
        self.skipped_budget = 0
        self.done_tiers = None
        self.n_records = 0
        self.drafts, self.checks, self.planted = {}, {}, {}

    def restore(self, prev):
        """`resume`: keep every finished call (no second spend) and the money already spent."""
        self.drafts = {d["draft_id"]: d for d in prev.get("drafts", [])}
        self.checks = {c["check_id"]: c for c in prev.get("checks", [])}
        self.planted = prev.get("planted") or {}
        self.spent = float(prev.get("spent_usd") or 0.0)
        self.started = prev.get("started") or self.started

    async def _reserve(self, worst):
        """Hard cap: a call starts only if spent + every in-flight worst case + its own worst case <= BUDGET_USD.
        Near the cap it waits for in-flight calls to settle (their real cost frees the rest of their reservation);
        it is skipped only when nothing is in flight and it still does not fit. So spent never passes the cap."""
        async with self.budget:
            while self.spent + self.reserved + worst > BUDGET_USD:
                if self.inflight == 0:
                    self.skipped_budget += 1
                    return False
                await self.budget.wait()
            self.reserved += worst
            self.inflight += 1
            return True

    async def _settle(self, worst, cost):
        async with self.budget:
            self.reserved -= worst
            self.inflight -= 1
            self.spent += cost
            self.budget.notify_all()

    def _checkpoint(self):
        self.n_records += 1
        if self.n_records % 15 == 0:   # a task killed mid-tier loses at most ~15 records (+ in-flight calls)
            put("results.json", self.results(self.started, done_tiers=self.done_tiers))

    async def _call(self, key, fn, *args):
        """(result | None, meta) — meta: model, cost, tokens, latency, stop, fallback, error."""
        import shared.llm_client.client as cl
        _KEY.set(key)
        t0 = time.monotonic()
        try:
            res = await asyncio.to_thread(fn, *args)
            resp = res[-1]
            meta = {"model_used": resp.model_used, "cost": float(resp.cost_usd or 0), "tokens_in": resp.input_tokens,
                    "tokens_out": resp.output_tokens, "stop_reason": resp.stop_reason,
                    "fallback_used": resp.fallback_used, "error": None}
        except Exception as e:  # noqa: BLE001 — recorded per call; an unusable reply was billed and logged by the gateway
            res = None
            meta = {"model_used": key, "cost": cl.unusable_reply_cost(e), "error": f"{type(e).__name__}: {str(e)[:240]}",
                    "billed_unusable": isinstance(e, cl.UnusableReply)}
        meta["latency_ms"] = int((time.monotonic() - t0) * 1000)
        return res, meta

    async def draft(self, arm, gid):
        d = arm.split("#")[0]
        key, s = DRAFTERS[d], self.sample[gid]
        worst = worst_call(key, "draft", self.catalog)
        async with self.sem:
            if not await self._reserve(worst):
                return
            meta = {"cost": 0.0}   # _call catches Exception; only a cancellation leaves this default
            try:
                res, meta = await self._call(key, self.pc.draft_card, dict(s["rep"]))
            finally:
                await self._settle(worst, meta.get("cost", 0.0))
        rec = {"draft_id": f"{arm}@{gid}", "group_id": gid, "drafter": d, "model_key": key, "run": arm,
               "max_tokens": max_tokens_for(key, "draft"), **meta}
        if res is not None:
            raw, _, resp = res
            signal = {"eval": "aa784_cardeval", "kind": "draft", "arm": arm, "group_id": gid}
            await self.pc._log(self.pool, STAGE, "writer", resp, signal)
            rec["parse_ok"] = bool(raw)   # {} = no JSON object (truncation / prose): production records a no_name miss
            rec.update(self._post_draft(raw, s))
            rec["raw_excerpt"] = (resp.content or "")[:3000]
            if rec.get("card"):
                rec["would_link"] = await self._would_link(rec["card"])
        self.drafts[rec["draft_id"]] = rec
        self._checkpoint()

    def _post_draft(self, raw, s):
        """build_card_for_group's steps before the check, without any DB write."""
        pc = self.pc

        def txt(v):  # production calls .strip() on these; a non-string would raise there (an `error` miss)
            return v.strip() if isinstance(v, str) else ""

        name = txt(raw.get("display_name"))
        country = txt(raw.get("country")) or txt(s["rep"].get("country"))
        card = dict(raw)
        card["facts"] = pc._clean_facts(raw.get("facts"), name or s["place"])
        card["aliases"] = pc._clean_aliases(raw.get("aliases"))
        if not name or not country:
            return {"pre_check": "no_name", "card": None}
        locality = txt(card.get("locality")) or None
        region = txt(card.get("region")) or None
        out = {"display_name": name, "locality": locality, "region": region, "country": country,
               "naming_note": txt(card.get("naming_note")) or None, "aliases": card["aliases"],
               "facts": [dict(f, rule_leak=(pc.traveller_clause(f["text"]) or [None, None])[1]) for f in card["facts"]],
               "place_key": pc.place_key(name, country, locality or region),
               "generic_no_locality": bool(pc.is_generic_name(name) and not (locality or region))}
        return {"pre_check": "ok", "card": out}

    async def _would_link(self, card):
        """AA-809 resolver, read-only: would this draft link to an existing card instead of a new one?"""
        try:
            async with self.pool.acquire() as conn:
                hit = await self.pc.find_card_for_draft(conn, card["place_key"], card["display_name"], card["aliases"],
                                                        card["locality"], card["region"], card["country"])
                if not hit:
                    return None
                row = await conn.fetchrow("SELECT display_name, locality, region, country FROM acp_shared.place_card "
                                          "WHERE card_id = $1::uuid", hit[0])
            return {"card_id": str(hit[0]), "method": hit[1], "existing": dict(row) if row else None}
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)[:200]}

    def _card_for_check(self, card):
        return {"display_name": card["display_name"], "locality": card["locality"], "region": card["region"],
                "country": card["country"], "facts": [{"text": f["text"], "kind": f["kind"]} for f in card["facts"]]}

    async def check(self, c, target):
        t, gid = target.split("@")
        card = self.planted.get(gid) if t == "P" else (self.drafts.get(target) or {}).get("card")
        if not card:
            return
        key, s = CHECKERS[c], self.sample[gid]
        worst = worst_call(key, "check", self.catalog)
        sent = self._card_for_check(card)
        async with self.sem:
            if not await self._reserve(worst):
                return
            meta = {"cost": 0.0}
            try:
                res, meta = await self._call(key, self.pc.check_card, sent, dict(s["rep"]))
            finally:
                await self._settle(worst, meta.get("cost", 0.0))
        rec = {"check_id": f"{c}x{target}", "checker": c, "model_key": key, "target": target, "group_id": gid,
               "max_tokens": max_tokens_for(key, "check"), **meta}
        if res is not None:
            ok, verdicts, _, resp = res
            await self.pc._log(self.pool, STAGE, "validate", resp,
                               {"eval": "aa784_cardeval", "kind": "check", "checker": c, "target": target})
            # check_card turns an unparseable / misaligned reply into identity_ok=False + all "unsure" — the same
            # outcome as a real rejection. Production behaviour is kept (outcome below); `unusable` separates
            # them for §7 gate 5, so a truncating checker is not scored as a strict one.
            data = self.pc._parse_json(resp.content)
            rec["unusable"] = not (isinstance(data.get("identity_ok"), bool) and isinstance(data.get("verdicts"), list)
                                   and len(data["verdicts"]) == len(sent["facts"]))
            kept = [i for i, v in enumerate(verdicts) if v == "supported"]
            if not ok:
                outcome = "identity_rejected"
            elif card.get("generic_no_locality"):
                outcome = "no_name_generic"
            else:
                outcome = "stored"
            rec.update({"identity_ok": ok, "verdicts": verdicts, "kept_idx": kept, "outcome": outcome,
                        "raw_excerpt": (resp.content or "")[:1500]})
        else:
            rec["outcome"] = "error"
        self.checks[rec["check_id"]] = rec
        self._checkpoint()

    def build_planted(self):
        """One planted card per group from D1#1: one fact mutated (year / century / number, else a fabricated
        founding fact) and, on every other group, the locality swapped with another sample group's locality."""
        year = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")
        cent = re.compile(r"\b(\d{1,2})(st|nd|rd|th)([- ]century)\b", re.I)
        num = re.compile(r"\b(\d[\d,]*(?:\.\d+)?)(\s?)(m|metres|meters|km|kilometres|kilometers|ft|feet|hectares)\b", re.I)

        def suffix(n):
            return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

        base = {gid: (self.drafts.get(f"D1#1@{gid}") or {}).get("card") for gid in self.sample}
        gids = [g for g in sorted(self.sample) if base.get(g)]
        for i, gid in enumerate(gids):
            card = json.loads(json.dumps(base[gid]))
            facts, plant = card["facts"], None
            for j, f in enumerate(facts):
                t = f["text"]
                if year.search(t):
                    y = int(year.search(t).group(1))
                    f["text"], plant = year.sub(str(y - 137 if y > 1300 else y + 211), t, count=1), ("year", j)
                elif cent.search(t):
                    m = cent.search(t)
                    n = int(m.group(1))
                    n2 = n + 4 if n <= 15 else n - 5
                    f["text"], plant = cent.sub(f"{n2}{suffix(n2)}{m.group(3)}", t, count=1), ("century", j)
                elif num.search(t):
                    m = num.search(t)
                    v = float(m.group(1).replace(",", "")) * 1.7
                    f["text"], plant = num.sub(f"{int(round(v)):,}{m.group(2)}{m.group(3)}", t, count=1), ("number", j)
                if plant:
                    break
            if not plant:
                fake = {"text": "It was founded in 1742 by a Portuguese trading mission.", "kind": "history",
                        "rule_leak": None}
                if len(facts) >= self.pc.MAX_FACTS:
                    facts[-1] = fake
                else:
                    facts.append(fake)
                plant = ("fabricated", facts.index(fake))
            card["planted_fact"] = {"type": plant[0], "index": plant[1]}
            card["planted_identity"] = None
            if i % 2 == 0:
                donors = [base[g] for g in gids if g != gid and base[g].get("locality")
                          and self.pc.fold(base[g]["locality"]) != self.pc.fold(card.get("locality"))]
                same = [d for d in donors if self.pc.fold(d["country"]) == self.pc.fold(card["country"])]
                donor = (same or donors or [None])[0]
                if donor:
                    card["planted_identity"] = {"locality_from": card.get("locality"), "locality_to": donor["locality"]}
                    card["locality"] = donor["locality"]
            self.planted[gid] = card

    async def run(self):
        for tier, _drafts, _checks in TIERS:
            calls = [c for c in plan_calls(list(self.sample.values()), self.catalog) if c[0] == tier]
            # `resume`: only the calls not done yet count and run
            calls = [c for c in calls if (f"{c[2]}@{c[3]}" not in self.drafts if c[1] == "draft"
                                          else f"{c[2]}x{c[3]}" not in self.checks)]
            tier_est = sum(est_call(DRAFTERS[a.split("#")[0]] if k == "draft" else CHECKERS[a], k,
                                    900 if k == "draft" else 700, self.catalog) for _, k, a, _ in calls)
            if self.spent + tier_est * 1.2 > BUDGET_USD:
                print(f"TIER {tier} and later skipped: est ${tier_est:.2f} would pass the ${BUDGET_USD:.2f} cap "
                      f"(spent ${self.spent:.3f})", flush=True)
                break   # value order: never run a later (less useful) tier after skipping this one
            dr = [c for c in calls if c[1] == "draft"]
            await asyncio.gather(*(self.draft(arm, gid) for _, _, arm, gid in dr))
            if not self.planted and any(k.startswith("D1#1@") for k in self.drafts):
                self.build_planted()   # once, right after the D1#1 drafts (tier A); a resume keeps the saved set
            ck = [c for c in calls if c[1] == "check"]
            await asyncio.gather(*(self.check(c, target) for _, _, c, target in ck))
            self.done_tiers = tier
            put("results.json", self.results(self.started, done_tiers=tier))
            print(f"TIER {tier} drafts={len(dr)} checks={len(ck)} spent=${self.spent:.3f} "
                  f"skipped_budget={self.skipped_budget}", flush=True)

    def summary(self):
        """LLM-only view per cell (the panel labels give the real metrics)."""
        cells = {}
        for ch in self.checks.values():
            t, gid = ch["target"].split("@")
            card = self.planted.get(gid) if t == "P" else (self.drafts.get(ch["target"]) or {}).get("card")
            dr = self.drafts.get(ch["target"]) or {}
            e = cells.setdefault(f"{t}x{ch['checker']}", {"groups": 0, "stored": 0, "identity_rejected": 0,
                                                          "facts": 0, "kept": 0, "wrong": 0, "unsure": 0,
                                                          "errors": 0, "unusable": 0, "fallback_excluded": 0,
                                                          "check_usd": 0.0, "draft_usd": 0.0})
            e["groups"] += 1
            e["check_usd"] += ch["cost"]
            e["draft_usd"] += dr.get("cost", 0.0) if t != "P" else 0.0
            if ch["outcome"] == "error":
                e["errors"] += 1
                continue
            if ch.get("fallback_used") or dr.get("fallback_used"):
                e["fallback_excluded"] += 1   # legacy 'sonnet' fell back to Haiku: not the model under test
                continue
            e["unusable"] += bool(ch.get("unusable"))
            e["stored"] += ch["outcome"] == "stored"
            e["identity_rejected"] += ch["outcome"] == "identity_rejected"
            e["facts"] += len(card["facts"])
            e["kept"] += len(ch["kept_idx"])
            e["wrong"] += ch["verdicts"].count("wrong")
            e["unsure"] += ch["verdicts"].count("unsure")
        for k, e in cells.items():
            t, c = k.split("x")
            dkey = "planted" if t == "P" else DRAFTERS[t.split("#")[0]]
            e["drafter"], e["checker_key"] = dkey, CHECKERS[c]
            e["same_vendor"] = t != "P" and vendor(dkey, self.catalog) == vendor(CHECKERS[c], self.catalog)
            e["usd_per_card"] = round((e["check_usd"] + e["draft_usd"]) / max(e["groups"], 1), 5)
            e["projected_9186_usd"] = round(e["usd_per_card"] * 9186, 1)
        return cells

    def results(self, started, done_tiers):
        return {"as_of": now_iso(), "started": started, "done_through_tier": done_tiers, "stage": STAGE,
                "prompt_sha": self.pc.PROMPT_SHA, "budget_usd": BUDGET_USD, "spent_usd": round(self.spent, 5),
                "skipped_budget": self.skipped_budget, "drafters": DRAFTERS, "checkers": CHECKERS,
                "live_pair": LIVE_PAIR,
                "token_floor": {f"{k}|{st}": v for (k, st), v in TOKEN_FLOOR.items()}, "sample": list(self.sample.values()),
                "drafts": list(self.drafts.values()), "checks": list(self.checks.values()),
                "planted": self.planted, "cells_llm_only": self.summary()}

    def panel(self):
        """Blind packet (no model names, no checker verdicts, deterministic shuffled order) + the key."""
        pc = self.pc
        packet, key = [], {"identity": {}, "fact": {}, "link": {}, "drafts": {}}
        cards = [(d["draft_id"], d["card"]) for d in self.drafts.values() if d.get("card")]
        cards += [(f"P@{gid}", c) for gid, c in self.planted.items()]
        by_group = defaultdict(list)
        for did, c in cards:
            by_group[did.split("@")[1]].append((did, c))
        for did, d in self.drafts.items():
            key["drafts"][did] = {"drafter": d["drafter"], "model_key": d["model_key"], "run": d["run"]}
        for gid in sorted(self.sample, key=lambda g: h("order", g)):
            s = self.sample[gid]
            idents, facts, links = {}, {}, {}
            for did, c in by_group.get(gid, []):
                ident = tuple(pc.fold(c.get(f)) for f in ("display_name", "locality", "region", "country"))
                vid = "V" + h(gid, *ident)[:8]
                idents.setdefault(vid, {"vid": vid, "display_name": c["display_name"], "locality": c.get("locality"),
                                        "region": c.get("region"), "country": c["country"],
                                        "aliases": c.get("aliases") or [], "naming_note": c.get("naming_note")})
                key["identity"].setdefault(vid, []).append(did)
                for i, f in enumerate(c["facts"]):
                    fid = "F" + h(gid, pc.fold(f["text"]))[:8]
                    facts.setdefault(fid, {"fid": fid, "text": f["text"], "in_variants": []})
                    if vid not in facts[fid]["in_variants"]:
                        facts[fid]["in_variants"].append(vid)
                    key["fact"].setdefault(fid, []).append([did, i])
                wl = (self.drafts.get(did) or {}).get("would_link") or {}
                if wl.get("existing"):
                    lid = "L" + h(gid, wl["card_id"])[:8]
                    links.setdefault(lid, {"lid": lid, "existing_card": wl["existing"]})
                    key["link"].setdefault(lid, []).append(did)
            packet.append({
                "group_id": gid,
                "itinerary": {"place": s["rep"]["place"], "country_sold_as": s["rep"].get("country"),
                              "tour_name": s["rep"].get("tour_name"), "sentence": s["rep"].get("evidence")},
                "identity_variants": sorted(idents.values(), key=lambda v: h("o", v["vid"])),
                "facts": sorted(facts.values(), key=lambda f: h("o", f["fid"])),
                "link_questions": sorted(links.values(), key=lambda x: x["lid"]),
            })
        return packet, key


# ── Main ─────────────────────────────────────────────────────────────────────────────────────────

async def main(mode):
    from services.acp_shared import place_cards as pc
    pool = await open_pool()
    catalog = await load_catalog(pool)
    keys, notes = usable_keys(catalog)
    for n in notes:
        print(n, flush=True)
    if mode == "dry":
        sample, stats = await build_sample(pool, pc)
        if not sample:
            print(f"SAMPLE empty: {stats}", flush=True)
            await pool.close()
            return
        by_tier, total, din, cin = estimate(sample, keys, pc)
        async with pool.acquire() as conn:
            calib = [dict(r) for r in await conn.fetch(CALIB_SQL)]
            calib_models = [dict(r) for r in await conn.fetch(CALIB_MODEL_SQL)]
            routes = {r["stage"]: dict(r) for r in await conn.fetch(ROUTE_SQL)}
        for st, want in LIVE_STAGE_KEYS.items():
            got = (routes.get(st) or {}).get("model_id")
            print(f"ROUTE {st} live={got} fallbacks={(routes.get(st) or {}).get('fallback_model_ids')}"
                  + ("" if got == want else f"  WARNING: design assumes {want} — the incumbent arm is not live"),
                  flush=True)
        for r in calib_models[:10]:
            print(f"CALIB_MODEL {r['model'][:36]} n={r['n']} out_avg={r['tout']} out_p90={r['tout_p90']}", flush=True)
        print(f"SAMPLE n={len(sample)} countries={len({s['country_norm'] for s in sample})} "
              f"need_draft_groups={stats['need_draft_groups']} pool={stats['class_pool']}", flush=True)
        for s in sample:
            print(f"  {s['group_id']} {s['class']:<11} {(s['country'] or '?')[:12]:<12} {s['place'][:40]!r} "
                  f"atoms={s['atoms']} tours={s['tours']}", flush=True)
        for r in calib[:8]:
            print(f"CALIB {r['stage']} {r['model'][:28]} n={r['n']} in={r['tin']} out={r['tout']} "
                  f"usd={r['usd']:.5f}", flush=True)
        print(f"EST tokens draft_in~{din} check_in~{cin}; by tier {by_tier}", flush=True)
        print(f"EST total ${total:.2f} (cap ${BUDGET_USD:.2f}; tiers past the cap are skipped in order)", flush=True)
        put("sample.json", {"as_of": now_iso(), "prompt_sha": pc.PROMPT_SHA, "stats": stats, "sample": sample})
        put("estimate.json", {"as_of": now_iso(), "by_tier": by_tier, "total_usd": total, "keys": sorted(keys),
                              "skipped_keys": notes, "calibration": calib, "calibration_models": calib_models,
                              "live_routes": routes, "draft_in": din, "check_in": cin})
        print("DRY RUN done, $0", flush=True)
    elif mode in ("paid", "resume"):
        started = now_iso()
        sample_doc = get("sample.json")
        if sample_doc.get("prompt_sha") != pc.PROMPT_SHA:
            print(f"ABORT: place_cards prompts changed since the dry run ({sample_doc.get('prompt_sha')} -> "
                  f"{pc.PROMPT_SHA}); run `dry` again", flush=True)
            await pool.close()
            return
        prev = get("results.json") if exists("results.json") else None
        if mode == "paid" and prev is not None:
            print(f"ABORT: results.json already exists (done_through_tier={prev.get('done_through_tier')}, "
                  f"spent ${prev.get('spent_usd')}). Use `resume`, or archive that file first.", flush=True)
            await pool.close()
            return
        install_client(pc)
        runner = Runner(pool, pc, keys, sample_doc["sample"], started)
        if mode == "resume" and prev is not None:
            runner.restore(prev)
            # A killed task (SIGKILL: no finally) under-reports spent in results.json; llm_call_log has every billed
            # call of this stage since the first start, so the cap is enforced on the larger of the two.
            async with pool.acquire() as conn:
                logged = await conn.fetchrow(LOG_SQL, STAGE, datetime.fromisoformat(runner.started))
            runner.spent = max(runner.spent, float(logged["usd"] or 0.0))
            print(f"RESUME drafts={len(runner.drafts)} checks={len(runner.checks)} spent=${runner.spent:.3f}",
                  flush=True)
        try:
            await runner.run()
            runner.done_tiers = "end"
        finally:
            put("results.json", runner.results(runner.started, done_tiers=runner.done_tiers if runner.done_tiers
                                               == "end" else f"aborted_after_{runner.done_tiers}"))
        packet, key = runner.panel()
        put("panel_packet.json", {"as_of": now_iso(), "groups": packet})
        put("panel_key.json", key)
        for cell, e in sorted(runner.summary().items()):
            print(f"CELL {cell:<10} stored={e['stored']}/{e['groups']} kept={e['kept']}/{e['facts']} "
                  f"wrong={e['wrong']} err={e['errors']} unusable={e['unusable']} ${e['usd_per_card']:.4f}/card",
                  flush=True)
        async with pool.acquire() as conn:
            log = await conn.fetchrow(LOG_SQL, STAGE, datetime.fromisoformat(runner.started))
        print(f"SPENT ${runner.spent:.3f} (llm_call_log {log['n']} rows ${log['usd']:.3f}); "
              f"skipped_budget={runner.skipped_budget}", flush=True)
    else:
        print("usage: cardeval_run.py dry|paid|resume", flush=True)
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "dry"))
