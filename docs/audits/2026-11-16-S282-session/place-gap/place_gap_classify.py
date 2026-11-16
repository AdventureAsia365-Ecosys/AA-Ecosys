#!/usr/bin/env python3
"""S282 read-only: classify the atom place names that have no segment research. Counts only.

Unit under test = geo.name_norm(place) over acp_contract.v_active_tour_atoms (the dfs_gap.py unit, 11,084 names,
5,589 'missing'). "Researched" = geo.name_norm(canonical_place) of a segment_research_log row, tier 'volume' (any
market), exactly as dfs_gap.py. Nothing is written; no place name is printed, only counts and country names.
Runs in the CIS api container: python3 + asyncpg, DATABASE_URL (cis_app), ssl='require'.
"""
import asyncio
import math
import os
import re
from collections import Counter, defaultdict

import asyncpg

# segment_matching.CONNECTORS (CIS origin/main): the words the Segment grouping drops.
CONNECTORS = frozenset("a an and at between by for from in into of on over the through to via with".split())

# Kind / filler words: a name made ONLY of these names a different place in every town (simple SQL-free proxy for
# place_cards.is_generic_name, which is not reachable from SQL).
GENERIC_WORDS = frozenset("""
city town village villages market markets night floating old new quarter centre center downtown countryside area
region local nearby surrounding surroundings road street streets river riverside lake lakeside beach beaches mountain
mountains hill hills island islands temple temples pagoda pagodas shrine monastery park national forest jungle valley
waterfall waterfalls falls cave caves bay coast coastal sea ocean seaside home house farm farms paddy paddies rice
field fields plantation tea garden gardens museum palace fort square bridge viewpoint view point hot spring springs
desert dunes sand camp base trail trek trekking route rural main capital your our its their hotel hotels restaurant
restaurants cafe village's family families community communities school workshop kitchen boat cruise
a an the of in at on to and with by from for
""".split())

# Non-destination patterns on name_norm (lowercase, punctuation already spaces). First match wins.
NON_DEST = (
    ("lodging", re.compile(r"\b(hotels?|resorts?|lodges?|ecolodge|guesthouses?|guest houses?|homestays?|home stay|"
                           r"hostels?|inns?|ryokan|villas?|bungalows?|campsites?|ger camp|tented camp|camps?|"
                           r"accommodations?|glamping|retreat)\b")),
    ("transport", re.compile(r"\b(airports?|airfield|airstrip|stations?|terminals?|piers?|jett(y|ies)|ports?|"
                             r"harbou?rs?|marinas?|ferry|ferries|bus|buses|trains?|railways?|rail|borders?|"
                             r"checkpoints?|check point|crossing|immigration|customs|highway|expressway)\b")),
    ("food_venue", re.compile(r"\b(restaurants?|cafes?|coffee shop|bars?|pubs?|eatery|food court|street food|"
                              r"cooking class)\b")),
    ("route_or_multi", re.compile(r"( to | and | via | between | from | or )")),
)

N_LIST = (0, 200, 500, 1000)
# Price inputs as stated in the brief (CIS mig 407 + batch.py): worst case, Standard queue.
KW_PER_PLACE, VOLUME_TASK_MAX, PROPOSE_CHUNK = 4, 1000, 15
USD_VOLUME_TASK, USD_SERP, USD_LLM_CALL_SEEN = 0.06, 0.0006, 0.007
MARKETS = 6


def rp(section, **kv):
    print("RP", section, " ".join(f"{k}={str(v).replace(' ', '_')}" for k, v in kv.items()), flush=True)


def tokens(nn):
    words = nn.split()
    kept = [w for w in words if w not in CONNECTORS]
    return frozenset(kept or words)


def non_dest_kind(nn):
    if len(nn) <= 3:
        return "very_short"
    words = nn.split()
    if words and all(w in GENERIC_WORDS for w in words):
        return "generic_only"
    for kind, rx in NON_DEST:
        if rx.search(f" {nn} "):
            return kind
    if len(words) > 6:
        return "long_phrase"
    return None


SQL = {
    "atoms": """
        SELECT ta.atom_id, ta.tour_id::text AS tour_id, (ta.owner_scope = 'platform') AS plat, ta.activity_type,
               ta.created_at, geo.name_norm(ta.place) AS nn, coalesce(rt.country, '(none)') AS country,
               geo.name_norm(coalesce(rt.country, '')) AS cn
          FROM acp_contract.v_active_tour_atoms ta
          JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id
         WHERE ta.place IS NOT NULL AND btrim(ta.place) <> ''""",
    "log_norm": "SELECT DISTINCT geo.name_norm(canonical_place) AS nn FROM acp_contract.segment_research_log "
                "WHERE tier = 'volume'",
    "log_raw": "SELECT DISTINCT canonical_place AS cp FROM acp_contract.segment_research_log WHERE tier = 'volume'",
    "log_max": "SELECT max(researched_at) AS m FROM acp_contract.segment_research_log WHERE tier = 'volume'",
    "pk_norm": "SELECT DISTINCT geo.name_norm(subject) AS nn FROM acp_contract.place_keyword WHERE subject_kind = 'place'",
    "seg": """
        SELECT m.atom_id, s.canonical_place AS cp, geo.name_norm(s.canonical_place) AS cnn
          FROM acp_contract.atom_segment_member m
          JOIN acp_contract.atom_segment s ON s.segment_id = m.segment_id""",
    "seg_labels": "SELECT DISTINCT geo.name_norm(canonical_place) AS nn FROM acp_contract.atom_segment",
    "dest": "SELECT DISTINCT name_norm AS nn, geo.name_norm(country) AS cn FROM shared.destinations "
            "WHERE duplicate_of IS NULL AND name_norm IS NOT NULL",
    "place_name": "SELECT name_norm AS nn, country_norm AS cn, status FROM geo.place_name",
    "tour_place": "SELECT DISTINCT name_norm AS nn, country_norm AS cn, (destination_id IS NOT NULL) AS linked "
                  "FROM geo.tour_place",
    "card_alias": "SELECT DISTINCT alias_norm AS nn FROM acp_shared.place_card_alias",
    "card_name": "SELECT DISTINCT geo.name_norm(display_name) AS nn FROM acp_shared.place_card "
                 "WHERE status <> 'rejected'",
    "card_miss": "SELECT DISTINCT place_norm AS nn FROM acp_shared.place_card_miss",
}
REQUIRED = ("atoms", "log_norm", "log_raw")


async def load():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    data = {}
    try:
        await conn.execute("SET statement_timeout = '300s'")
        await conn.execute("SET default_transaction_read_only = on")
        for name, sql in SQL.items():
            try:
                data[name] = [dict(r) for r in await conn.fetch(sql)]
                rp("load", table=name, rows=len(data[name]))
            except Exception as e:  # noqa: BLE001
                print("ERR", f"load_{name}", type(e).__name__, str(e)[:200], flush=True)
                data[name] = None
    finally:
        await conn.close()
    return data


def analyse(data):
    for name in REQUIRED:
        if data.get(name) is None:
            print("ERR", "analyse", "missing_required", name, flush=True)
            return
    atoms = data["atoms"]
    researched = {r["nn"] for r in data["log_norm"]}
    log_raw = {r["cp"] for r in data["log_raw"]}
    log_max = (data.get("log_max") or [{}])[0].get("m")
    pk = {r["nn"] for r in (data.get("pk_norm") or [])}

    # ── per name aggregates ──────────────────────────────────────────────────────────────────────────────────────
    tours_of = defaultdict(set)          # nn -> active tour ids (any owner scope)
    atoms_of = Counter()
    plat_of = defaultdict(bool)
    cn_of = defaultdict(set)             # nn -> name_norm(country)
    country_of = defaultdict(set)        # nn -> raw_tours.country (display)
    newest_of = {}
    atom_nn, atom_plat, atom_type = {}, {}, {}
    names_of_tour = defaultdict(set)
    plat_names_of_tour = defaultdict(set)
    for a in atoms:
        nn = a["nn"]
        if not nn:
            continue
        tours_of[nn].add(a["tour_id"])
        atoms_of[nn] += 1
        plat_of[nn] = plat_of[nn] or bool(a["plat"])
        cn_of[nn].add(a["cn"])
        country_of[nn].add(a["country"])
        if a["created_at"] is not None and (nn not in newest_of or a["created_at"] > newest_of[nn]):
            newest_of[nn] = a["created_at"]
        atom_nn[a["atom_id"]], atom_plat[a["atom_id"]], atom_type[a["atom_id"]] = nn, bool(a["plat"]), a["activity_type"]
        names_of_tour[a["tour_id"]].add(nn)
        if a["plat"]:
            plat_names_of_tour[a["tour_id"]].add(nn)

    names = set(tours_of)
    miss = names - researched
    try:
        rp("baseline", distinct_names=len(names), researched_names_in_log=len(researched),
           missing=len(miss), missing_with_any_place_keyword=len(miss & pk), missing_le3_chars=sum(len(n) <= 3 for n in miss),
           active_tours_with_places=len(names_of_tour), tenant_only_names=sum(1 for n in names if not plat_of[n]),
           last_volume_research=log_max)
    except Exception as e:  # noqa: BLE001
        print("ERR", "baseline", type(e).__name__, str(e)[:200], flush=True)

    # ── segment membership (platform atoms only: research never scopes tenant atoms) ─────────────────────────────
    in_seg = defaultdict(bool)
    seg_researched = defaultdict(bool)
    seg_types = defaultdict(set)
    seg_label_norm_eq = defaultdict(bool)
    if data.get("seg") is not None:
        for s in data["seg"]:
            aid = s["atom_id"]
            nn = atom_nn.get(aid)
            if nn is None or not atom_plat.get(aid):
                continue
            in_seg[nn] = True
            seg_types[nn].add(atom_type.get(aid))
            if s["cp"] in log_raw:
                seg_researched[nn] = True
            if s["cnn"] == nn:
                seg_label_norm_eq[nn] = True
    seg_labels = {r["nn"] for r in (data.get("seg_labels") or [])}

    # ── normalisation duplicates of a researched name ────────────────────────────────────────────────────────────
    r_tok = {}
    for r in researched:
        if r:
            r_tok.setdefault(tokens(r), r)
    r_tokset = set(r_tok)
    inv = defaultdict(set)
    r_list = list(r_tokset)
    for i, t in enumerate(r_list):
        for w in t:
            inv[w].add(i)

    def token_dup(nn):
        return tokens(nn) in r_tokset

    def near_dup(nn):
        m = tokens(nn)
        if not m:
            return False
        # a researched name inside this one (needs a distinctive word, not just 'temple')
        if len(m) <= 10:
            ml = sorted(m)
            for k in range(1, len(ml)):
                for idx in _combos(len(ml), k):
                    sub = frozenset(ml[j] for j in idx)
                    if sub in r_tokset and any(w not in GENERIC_WORDS for w in sub):
                        return True
        # this name inside a researched one
        if any(w not in GENERIC_WORDS for w in m):
            cand = None
            for w in m:
                cand = inv[w] if cand is None else cand & inv[w]
                if not cand:
                    break
            if cand:
                return True
        return False

    # ── gazetteer lookups ────────────────────────────────────────────────────────────────────────────────────────
    def _set(name, key="nn"):
        rows = data.get(name)
        return None if rows is None else {r[key] for r in rows}

    dest_any = _set("dest")
    dest_pair = None if data.get("dest") is None else {(r["nn"], r["cn"]) for r in data["dest"]}
    pn_status = defaultdict(set)
    pn_pair_status = defaultdict(set)
    for r in data.get("place_name") or []:
        pn_status[r["nn"]].add(r["status"])
        pn_pair_status[(r["nn"], r["cn"])].add(r["status"])
    tp_any = _set("tour_place")
    tp_linked = None if data.get("tour_place") is None else {r["nn"] for r in data["tour_place"] if r["linked"]}
    card_alias = _set("card_alias") or set()
    card_name = _set("card_name") or set()
    card_miss = _set("card_miss") or set()

    def same_country_dest(nn):
        return bool(dest_pair) and any((nn, c) in dest_pair for c in cn_of[nn])

    def pn_same_country(nn):
        out = set()
        for c in cn_of[nn]:
            out |= pn_pair_status.get((nn, c), set())
        return out

    def gaz_bucket(nn):
        if same_country_dest(nn):
            return "destination_same_country"
        if "resolved" in pn_same_country(nn):
            return "place_name_resolved_same_country"
        if dest_any and nn in dest_any:
            return "destination_other_country"
        if nn in card_alias or nn in card_name:
            return "place_card"
        if "resolved" in pn_status.get(nn, ()):
            return "place_name_resolved_other_country"
        if tp_linked and nn in tp_linked:
            return "tour_place_linked"
        if "unknown" in pn_status.get(nn, ()):
            return "place_name_unknown"
        if pn_status.get(nn, set()) & {"pending", "suspect"}:
            return "place_name_pending_or_suspect"
        if tp_any and nn in tp_any:
            return "tour_place_unlinked"
        if nn in card_miss:
            return "place_card_miss"
        if nn in seg_labels:
            return "segment_label_only"
        return "no_match"

    # ── primary bucket per missing name (first match wins) ───────────────────────────────────────────────────────
    FALSE_GAP = {"covered_via_segment_label", "token_dup_of_researched", "near_dup_of_researched"}
    BY_DESIGN = {"tenant_only", "no_segment_transit_typed", "no_segment_other"}

    def primary(nn):
        if not plat_of[nn]:
            return "tenant_only"
        if seg_researched[nn]:
            return "covered_via_segment_label"
        if token_dup(nn):
            return "token_dup_of_researched"
        if near_dup(nn):
            return "near_dup_of_researched"
        k = non_dest_kind(nn)
        if k:
            return "non_destination_" + k
        if not in_seg[nn]:
            return "no_segment_transit_typed" if _all_transit(nn) else "no_segment_other"
        if seg_types[nn] and seg_types[nn] <= {"transit", None}:
            return "segment_unresearched_transit_like"
        return "segment_unresearched_real"

    atype_of = defaultdict(set)
    for a in atoms:
        if a["nn"] and a["plat"]:
            atype_of[a["nn"]].add(a["activity_type"])

    def _all_transit(nn):
        t = atype_of[nn]
        return bool(t) and t <= {"transit", None}

    bucket = {}
    try:
        for nn in miss:
            bucket[nn] = primary(nn)
        c = Counter(bucket.values())
        for b, n in sorted(c.items(), key=lambda x: -x[1]):
            kind = ("false_gap" if b in FALSE_GAP else "by_design" if b in BY_DESIGN
                    else "non_destination" if b.startswith("non_destination") else "real_gap_candidate")
            rp("primary_bucket", bucket=b, group=kind, names=n,
               tour_mentions=sum(len(tours_of[x]) for x in bucket if bucket[x] == b))
        g = Counter()
        for b, n in c.items():
            g["false_gap" if b in FALSE_GAP else "by_design" if b in BY_DESIGN
              else "non_destination" if b.startswith("non_destination") else "real_gap_candidate"] += n
        rp("primary_group", **dict(g), total=sum(g.values()))
    except Exception as e:  # noqa: BLE001
        print("ERR", "primary_bucket", type(e).__name__, str(e)[:200], flush=True)

    # ── non-exclusive flags across all missing names ─────────────────────────────────────────────────────────────
    try:
        f = Counter()
        for nn in miss:
            f["platform"] += plat_of[nn]
            f["in_segment"] += in_seg[nn]
            f["segment_label_researched"] += seg_researched[nn]
            f["is_a_segment_label_norm"] += nn in seg_labels
            f["token_dup"] += token_dup(nn)
            f["non_dest_pattern"] += non_dest_kind(nn) is not None
            f["destination_any"] += bool(dest_any and nn in dest_any)
            f["destination_same_country"] += same_country_dest(nn)
            f["place_name_any"] += bool(pn_status.get(nn))
            f["place_name_resolved"] += "resolved" in pn_status.get(nn, ())
            f["place_name_unknown"] += "unknown" in pn_status.get(nn, ())
            f["tour_place_any"] += bool(tp_any and nn in tp_any)
            f["place_card_alias_or_name"] += (nn in card_alias or nn in card_name)
            f["place_card_miss"] += nn in card_miss
            f["multi_country"] += len(country_of[nn]) > 1
            f["newer_than_last_research"] += bool(log_max and newest_of.get(nn) and newest_of[nn] > log_max)
        rp("flags_all_missing", **dict(f))
        nd = Counter(non_dest_kind(nn) or "none" for nn in miss)
        rp("non_dest_pattern_all_missing", **dict(nd))
    except Exception as e:  # noqa: BLE001
        print("ERR", "flags_all_missing", type(e).__name__, str(e)[:200], flush=True)

    real = {nn for nn, b in bucket.items() if b == "segment_unresearched_real"}
    real_like = {nn for nn, b in bucket.items() if b.startswith("segment_unresearched")}

    # ── gazetteer match of the real-gap candidates (and of every missing name) ───────────────────────────────────
    try:
        for label, pool in (("real_gap", real), ("all_missing", miss)):
            gb = Counter(gaz_bucket(nn) for nn in pool)
            rp("gazetteer_" + label, names=len(pool), **dict(gb))
        rp("real_gap_extra", names=len(real),
           newer_than_last_research=sum(1 for nn in real if log_max and newest_of.get(nn) and newest_of[nn] > log_max),
           is_a_segment_label_norm=sum(1 for nn in real if nn in seg_labels),
           label_norm_equals_name=sum(1 for nn in real if seg_label_norm_eq[nn]),
           multi_country=sum(1 for nn in real if len(country_of[nn]) > 1))
    except Exception as e:  # noqa: BLE001
        print("ERR", "gazetteer", type(e).__name__, str(e)[:200], flush=True)

    # ── mentions (distinct active tours) x bucket ────────────────────────────────────────────────────────────────
    def mband(nn):
        n = len(tours_of[nn])
        return "t1" if n == 1 else "t2_5" if n <= 5 else "t6p"

    try:
        rp("mentions_all_missing", **dict(Counter(mband(nn) for nn in miss)))
        for b in sorted(set(bucket.values())):
            rp("mentions_by_bucket", bucket=b, **dict(Counter(mband(nn) for nn, x in bucket.items() if x == b)))
    except Exception as e:  # noqa: BLE001
        print("ERR", "mentions", type(e).__name__, str(e)[:200], flush=True)

    # ── per country of the tour (a name counted once per country it appears in) ──────────────────────────────────
    try:
        per = defaultdict(Counter)
        for nn in names:
            for c in country_of[nn]:
                per[c]["names"] += 1
                if nn in miss:
                    per[c]["missing"] += 1
                    b = bucket.get(nn, "")
                    per[c]["real_gap"] += b == "segment_unresearched_real"
                    per[c]["false_gap"] += b in FALSE_GAP
                    per[c]["by_design"] += b in BY_DESIGN
                    per[c]["non_dest"] += b.startswith("non_destination")
        tours_per_c = defaultdict(set)
        for a in atoms:
            tours_per_c[a["country"]].add(a["tour_id"])
        for c, cnt in sorted(per.items(), key=lambda x: -x[1]["missing"]):
            rp("by_country", country=c, tours=len(tours_per_c[c]), **dict(cnt))
    except Exception as e:  # noqa: BLE001
        print("ERR", "by_country", type(e).__name__, str(e)[:200], flush=True)

    # ── tour coverage simulation ─────────────────────────────────────────────────────────────────────────────────
    def full_count(tour_names, covered):
        full = some = none = 0
        for ns in tour_names.values():
            if not ns:
                continue
            k = sum(1 for n in ns if n in covered)
            if k == len(ns):
                full += 1
            elif k == 0:
                none += 1
            else:
                some += 1
        return full, some, none

    def ranked(pool):
        return sorted(pool, key=lambda n: (-len(tours_of[n]), -atoms_of[n], n))

    def cost(n):
        tasks = math.ceil(n * KW_PER_PLACE / VOLUME_TASK_MAX) if n else 0
        return dict(llm_calls=math.ceil(n / PROPOSE_CHUNK), kw_worst=n * KW_PER_PLACE, tasks_per_market=tasks,
                    est_usd_6mkts=round(tasks * USD_VOLUME_TASK * MARKETS + n * USD_SERP
                                        + math.ceil(n / PROPOSE_CHUNK) * USD_LLM_CALL_SEEN, 2))

    try:
        base_cov = set(researched)
        # A) raw metric: add the top-N most-mentioned missing names, whatever they are.
        order = ranked(miss)
        for n in tuple(x for x in N_LIST if x < len(order)) + (len(order),):
            cov = base_cov | set(order[:n])
            f_, s_, z_ = full_count(names_of_tour, cov)
            rp("coverage_raw_topN", n=n if n < len(order) else f"all_{n}", tours_full=f_, tours_some=s_,
               tours_none=z_, **cost(n))
        # B) adjusted: false gaps + by-design + non-destination count as covered (never bought);
        #    add the top-N real-gap candidates (incl. transit-like segments last).
        settled = {nn for nn, b in bucket.items() if not b.startswith("segment_unresearched")}
        cov0 = base_cov | settled
        order_r = ranked(real) + ranked(real_like - real)
        for n in tuple(x for x in N_LIST if x < len(order_r)) + (len(order_r),):
            cov = cov0 | set(order_r[:n])
            f_, s_, z_ = full_count(names_of_tour, cov)
            rp("coverage_adjusted_topN", n=n if n < len(order_r) else f"all_{n}", tours_full=f_, tours_some=s_,
               tours_none=z_, **cost(n))
        # C) the same two baselines on platform atoms only
        f_, s_, z_ = full_count(plat_names_of_tour, base_cov)
        rp("coverage_platform_only", basis="raw", tours_full=f_, tours_some=s_, tours_none=z_)
        f_, s_, z_ = full_count(plat_names_of_tour, cov0)
        rp("coverage_platform_only", basis="adjusted", tours_full=f_, tours_some=s_, tours_none=z_)
    except Exception as e:  # noqa: BLE001
        print("ERR", "coverage", type(e).__name__, str(e)[:200], flush=True)


def _combos(n, k):
    from itertools import combinations
    return combinations(range(n), k)


async def main():
    data = await load()
    try:
        analyse(data)
    except Exception as e:  # noqa: BLE001
        print("ERR", "analyse", type(e).__name__, str(e)[:200], flush=True)


if __name__ == "__main__":
    asyncio.run(main())
