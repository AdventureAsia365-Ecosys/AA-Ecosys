# Jev reuse on the T series: which T checks an existing, trusted Jev verdict can serve

- Session S247, AA-779 follow-up. Read-only analysis by Claude Code. No paid calls, no DB writes, no ECS exec, no push.
- Direction (Nghiệp): evaluate the questions **already in our Jev**. If they work, apply them to the T series. No new Jev questions.
- Code: AA-CIS-App `origin/main` e042a98c (22/10, includes #934 `t9_faq_answer_fit`). Jev data: `.tmp-session/jev_existing_stats.json`,
  S246 per-question eval `docs/audits/2026-10-21-S246-jev-question-eval/README.md`, AA-779 LLM results
  `docs/audits/2026-10-22-S247-aa779-llm/`.

## 1. Answer in short

Only **platform-data inputs** on the T path can reuse Jev. The allow-list is empty, so ADR 0007 blocks every T check that judges
tenant text. Four T inputs are platform data and already overlap with verdicts that sit in `shared.decision_log`.

| # | T step | What it is today | Existing question to reuse | Expected gain | Priority |
|---|---|---|---|---|---|
| C1 | **T2** writer keywords + PAA (`tenant_market_seo`) | Deterministic `cached_ideas` / `rank_keyword_ideas`. **No Jev**, and T2 takes this path ahead of the Jev-filtered `seo_context` row | `a1_keyword_about_tour` (reject 0.40), `a3_question_about_here` (reject 0.30) | The writer stops getting keywords about other places, hotels or activities the tour does not have ("Target keywords" top 5 in the T2 prompt). This is the S246 G3 risk, and today it is open on every tenant rewrite | **High** |
| C2 | **T8** angle prompt + "PAA answered" ranking axis | The merged real-question list (≤ 12) is cleaned only by the English and off-meaning rules. The tenant sees this list | `a3_question_about_here`, `a3_landing_belongs` (reject 0.40) | Angles are no longer shaped by, or ranked up for, off-scope / homonym / generic questions. Cost is the same (1 Sonnet call) | **Medium-high** |
| C3 | **T9** blog FAQ candidates (before `paa_for_scope` / `t9_faq_filter`) | `off`: deterministic `paa_for_scope` (P 0.74, R 0.64 unbiased). `on`: Haiku filter (P 0.96, R 0.91, ~$0.010–0.012 per blog) | same two A3 questions | A $0 precision belt in front of Haiku, and a better `off`/fallback list. **Not** a Haiku replacement: Jev never judges answerability or "sensitive, no travel use". Saving ≈ $0, because Haiku cost is mostly the fixed system prompt | **Medium** |
| C4 | **T9** blog SEO keyword (`choose_keyword`) | Deterministic. Its candidates are the tour-title SERP `related_keywords`, which **no Jev question has ever seen** | `a3_demand_belongs` (reject 0.70) through the Segment's own demand keyword, or `a1_keyword_about_tour` where the related keyword was also an A1 candidate | Title/meta keyword about this moment, not about the tour title (the class of "Bhutan meditation retreat", S234). Customer-facing | **Medium**, measure coverage first |

Everything else on the T path has **no fit** with an existing question (§4). That includes all of T3, T7 brand-fit, T10 and the
new `t9_faq_answer_fit`. The S246 G6 verdict stands: the T7/T8/T9/T10 questions stay OFF. Nothing in the data argues for
re-proposing them.

**Whether this works is still unmeasured.** The table rests on code reads, plus calibration on the A3 population. Before any code,
one $0 container read (§5) must show (a) how many T inputs already have a verdict and (b) how precise "Jev reject → drop" is on
the 200 labelled FAQ questions. A re-ask of the misses would be paid (about $0.00001–0.000017 per pair) and needs Nghiệp's approval.

## 2. How reuse would work, and the guard that blocks a naive call

- **Where the verdicts are.** `shared.decision_log`, `tenant_id IS NULL`, subject keys built by the A-side call sites:
  - `a3_question_about_here`: `paa:{", ".join(sorted(segment countries))}:{q[:300]}` (`services/acp_contract/atom_ranking.py:581`), state `{question, countries}`.
  - `a3_landing_belongs`: `land:{canonical_place — canonical_action}:{q[:300]}` (`atom_ranking.py:626`), state `{query, moment}`.
  - `a3_demand_belongs`: `demand:{moment}:{keyword}` (`atom_ranking.py:253`). The owner is the first non-rejected keyword in `demand_candidates()` order. Only its volume is stored, not the keyword.
  - `a1_keyword_about_tour`: `kw:{tour_id}:{keyword.lower()}` (`services/seo_intelligence/s1_prefetch.py:137`), up to 30 candidates per tour by volume (`JEV_PER_TOUR`), research-cache ideas included.
- **The input is platform data.** It is PAA text, country names, Segment place/action and tour title words. Nothing written by a
  tenant goes to TypeSafe, and a pure read sends nothing at all. ADR 0007 allows it.
- **A naive `decide()` from a T job is a no-op.** `resolve_tenant()` (`shared/llm_client/call_log.py:89`) takes the bound job's tenant,
  `tenant_allowed()` (`shared/llm_client/decide.py:228`) returns False for a non-allow-listed tenant, and the verdict is `skipped`.
  The cache lookup (`decide.py:281`) also matches `tenant_id IS NOT DISTINCT FROM` the caller, so a tenant-scoped ask never sees
  the NULL-tenant A3 rows. Reuse therefore needs one of these:
  1. **Read-only helper (recommended first step, $0).** Something like `platform_verdicts(question_key, subject_keys)` that reads
     `decision_log` the way `_CACHE_SQL` does, but with `tenant_id IS NULL`: current `question_hash`, `NOT cached`, ≤ 180 days. It
     recomputes the zone with today's floors (`zone_for`) and acts only on enforce-mode accept/reject. It makes no TypeSafe call and
     needs no guard change. A miss keeps the stage's current rule.
  2. **Re-ask misses as platform content (later, paid, risky PR).** An explicit `platform_content=True` path in `decide()` that ignores
     the bound tenant only for an `a*_` stage key, and that writes NULL-tenant rows so A3 and T share one cache. This touches the
     AA-741 tenant guard, so it is a risky change (auth/data path) and gets an independent review before merge.
- **The A3 country scope is the Segment's country set**, not the piece's. For a multi-country Segment (Golden Triangle) the key is
  `"Laos, Myanmar, Thailand"`. The lookup should try the piece's own set first and then the sets of its Segments.

## 3. Candidates in detail

### C1. T2: tenant-market keywords and PAA bypass `a1_keyword_about_tour` (High)

- **Code.** `services/jobs/t2_rewrite_job.py:133-160`. It first reads the admin `seo_context` row (A1, US, the only one Jev-filtered),
  then **overwrites it** with `tenant_market_seo()` (`s1_prefetch.py:419`) whenever the research cache has terms for that market,
  US tenants included. `tenant_market_seo` builds `top_keywords` with `cached_ideas()` / `rank_keyword_ideas()` (`s1_prefetch.py:153`)
  and the PAA with the first 5 questions of each matching `search_demand` row. No `jev_review()` runs on that path. The T2 prompt uses
  `Target keywords: top 5` and `People also ask: 3` (`services/content_generation/prompts.py:497-498`).
- **Cost today.** $0 for the check (deterministic). What is at stake is the T2 writer call itself (`t2_generate`, about $0.10–0.18 per
  tour), which is told to use these keywords.
- **Existing question.** `a1_keyword_about_tour`, enforce, accept 0.80 / reject 0.40. S246 G3: "the only gate stopping off-topic keywords
  (other places in the same country, hotel names, activities the tour lacks) from reaching `top_keywords`, which the writer must
  use". Its state is `{tour, country, title_places, activity, keyword}`. That state is market-independent, so a US verdict for
  `kw:{tour_id}:{kw}` holds for the same keyword text in any market. For the PAA lines: `a3_question_about_here` on `paa:{country}:{q}`.
- **Input.** Platform data: the tour row, `search_demand` keywords and PAA.
- **Gain.** Closes a real gap on every tenant rewrite. It also protects tours whose `seo_context` was built in shadow (01–08/10):
  their verdicts are in the log, and today's floors apply at read time. That gives the "protect the current catalog" effect from S246
  G3 note 1 on the T2 path, with no DataForSEO rebuild.
- **Unknown.** Coverage. `tenant_market_seo` also matches on atom places (AA-741), which is broader than A1's candidates, so some
  keywords will have no verdict. §5 part C measures it.
- **Rule if built.** Drop a keyword with an enforce-mode reject (p ≤ 0.40). Keep the rest in their current order. Never add a keyword
  on accept (the S246 note: `keep.setdefault` skips the transfer/foreign filters).

### C2. T8: the angle list and ranking read questions A3 Jev never cleared (Medium-high)

- **Code.** `services/acp_angle_gate/service.py:315` `_blog_search_demand` → `collect_real_questions()`
  (`services/acp_shared/real_questions.py:497`). The tiers are, in order: `segment_match` (atom_matches, which **passed** both A3 gates
  for that Segment), `place_paa` (`real_questions.py:422`, `search_demand` PAA of any keyword sharing a place word), `serp_topup`
  (`:444`) and `tour_paa`. `merge()` (`:276`) applies only length, English and off-meaning rules. The first 12 go into the angle prompt
  (`generate_angles`, `service.py:220`) and into `rank_angles()` (`:244`), whose "PAA answered" axis counts the questions an angle
  claims. `verify_answers` (`:249`, `t8_angle_answers`) is OFF.
- **Cost today.** `t8_angle_gen` (Sonnet) is about $0.025–0.028 per call (S247 ledger: 5 calls $0.140, 10 calls $0.272). The list
  itself costs $0.
- **Existing questions.** `a3_question_about_here` (one call per (country set, question)): S246 G5 says it "does almost all of the
  country-scope filtering and is the only question that catches generic questions"; 137 drops, 2 wrong; Nghiệp flipped 1/54.
  `a3_landing_belongs` per (moment, question): 139/140; Nghiệp flipped 1/62. Their population is the same `search_demand` PAA that
  `place_paa` reads, so the calibration should transfer better than on any other T input.
- **Input.** Platform data.
- **Gain.** Questions A3 already rejected for this exact moment no longer re-enter through `place_paa` / `serp_topup` / `tour_paa`.
  The ranking axis stops rewarding angles that "answer" junk, and the tenant-visible list gets cleaner. The effect is largest when a
  piece has fewer than 12 `segment_match` questions. In the S247 coverage subject (Laos route) `segment_match` filled 12/12, so the
  gain there would be 0.
- **Rule if built.** For each non-`segment_match` question: drop it on an about_here reject for the piece's country set, or on a
  landing reject for **every** moment of the piece. A landing reject for one moment of a Route does not drop it.

### C3. T9: blog FAQ candidates (Medium, as a belt, not a replacement)

- **Code.** `services/acp_content_writing/service.py:1666` → `faq_filter.select_faq_questions()` (`faq_filter.py:302`). It always computes
  `paa_for_scope` (`quality_gates.py:1857`) and then, behind `T9_FAQ_LLM_FILTER`, runs one Haiku call per blog (stage `t9_faq_filter`,
  CIS ADR 0011). The input is the same chain as C2, re-read with up to 30 questions (`CHAIN_MAX`).
- **Cost today.** `t9_faq_filter` ≈ $0.010–0.012 per blog (live shadow: $0.0119 for 30 candidates; 2 calls $0.0204). Remeasure on the
  200-question set: $0.213, P 0.960 (Wilson LB 0.902), R 0.914; B1..B5 PASS.
- **Existing questions.** The same two, and they cover only part of the FAQ drop reasons. In the 95 panel DROPs: `off_scope_other_place`
  23, `outside_piece_scope` 5, `off_scope_homonym` 19 and generic questions are plausibly covered by about_here + landing.
  `sensitive_no_travel_use` 21 (the Tiananmen-type questions **are** about the place, so about_here keeps them), `unanswerable` 8,
  `non_english` 3 and `commercial_junk` 6 are not what either question asks.
- **Known mismatch (recall risk).** Practical country-level questions (visa, weather, safety) are FAQ KEEP by the panel rule, but
  `a3_landing_belongs` ("served by an article about this moment") will likely reject them. Landing must not drop a question that
  about_here accepts as being about the country, or the measurement has to show it does no harm.
- **Gain.**
  - With `off`: a $0 upgrade of the deterministic list.
  - With `on`: a belt for Haiku's 4 false keeps per 100, but only where it adds 0 false drops of KEEP.
  - Saving: ≈ $0. Haiku cost is dominated by the fixed system prompt, so fewer candidates barely change it.
  - No replacement: Jev alone cannot meet B1, because it never judges sensitivity or answerability.

### C4. T9: blog SEO keyword from unreviewed `related_keywords` (Medium, coverage first)

- **Code.** `service.py:1424-1430`: `related_keywords` of the T8 snapshot (`seo_context.related_keywords`, the SERP "related searches" of
  the tour-title seed, `s1_prefetch.py:385`), then `choose_keyword()` (`service.py:336`), which applies transactional, gazetteer,
  place-word and product-grounding rules. `jev_review()` runs only on `keyword_ideas`, never on `related_keywords`.
- **Cost today.** $0 (deterministic). The keyword lands in the customer-facing title and meta (F4).
- **Existing questions.** Two options, in order:
  - (a) the Segment's own demand keyword, which `a3_demand_belongs` did not reject. It is moment-level, has real volume and is
    recomputable at $0 from `demand_candidates()` plus `decision_log`. S246: 117/119 overall, 88/88 at p < 0.40, and only 18/20 in the
    0.50–0.70 band. That band's spot-check (S246 decision 6) is still open, so use only verdicts with p < 0.50 or wait for it.
  - (b) `a1_keyword_about_tour` on `kw:{tour_id}:{related keyword}` where the related keyword was also an A1 candidate. This is
    tour-level, so it only filters; it cannot pick.
- **Input.** Platform data.
- **Gain.** A keyword about this moment instead of a tour-title related search. The size is unknown: coverage of related keywords by
  any verdict is probably low, and §5 part D measures it.

## 4. T checks with NO existing-question fit

| T step | Check (file:line) | LLM / stage, cost | Why no existing question fits |
|---|---|---|---|
| T0 Brand | CTA review-claim rule (`authenticity.cta_review_claims`) | none (rule) | Tenant text; no Jev question about CTAs. |
| T1 Select | none | none | No check. |
| T2 Rewrite | writer `t2_generate`, judge `t2_judge` (brand_fit), `t2_brand_audit`, `t2_flag_fix`, `t2_itinerary_nudge` | about $0.10–0.18 per tour in total | Prose about the tenant brand. `a1_brand_fit` at the tie-break (`judge_node.py:177`) is OFF (S246 G2: does not separate good from bad). |
| T3 QA | numeric grounding + `a1_claim_supported` on `t3_grounding` (`acp_produce/tenant_pipeline.py:167`) | Jev only for allow-listed tenants (none) | Tenant draft, blocked by ADR 0007. S246 also proposes `a1_claim_supported` OFF (the accept side clears < 1%; the reject side is unusable). |
| T4 Pool | none | none | No check. |
| T5 / T6 | superseded (A3 platform) | — | Already A3: `a3_atom_in_text`, `a3_activity_type`, `a3_same_place` act before any T step sees atoms or Segments. |
| T7 Slate | contested cut (deterministic, from `atom_segment.contested`); brand-fit Luna `t7_debate_judge` (`acp_shared/debate.py:263`, cached per tenant + brand version) | Luna per cache miss | Judges a topic against the tenant brand (tenant content). `t7_topic_fits_brand` is OFF and ineffective (226/275 at p 0.6–0.9). The Slate already **consumes** A3 verdicts through Score (demand, `questions_count`, activity type). |
| T8 Angle | `t8_angle_gen` prose; `t8_angle_answers` via `verify_answers` (`acp_angle_gate/ranking.py:145`) | about $0.025–0.028 per call | Angle text is generated content. `t8_angle_answers` is OFF (n = 18, no labels). Only the question **list** (C2) is platform data. |
| T9 Write | `t9_write` (Sonnet), `t9_repair` (sentence repair, SEO fit), place cards read only | t9_write about $0.045 per call, t9_repair about $0.004 | Prose. Place cards are drafted by A3 stages; `a3_same_place` is enforced on the reject side only (0.10), so it can veto a merge but never confirms a card reuse. |
| T9 FAQ answer-fit | `t9_faq_answer_fit` (#934, `faq_answer_fit.py`, Sonnet) | about $0.004 per blog | It judges the tenant's written answer against its question. Tenant content, and no Jev question asks this (`t10_faq_restates` asked a different rule and is OFF). |
| T10 Gates | F9 claims `t10_judge` (`quality_gates.py:1149`), `t10_claims`, F10 embedding cosine, F2/F4/F16/F17 rules | t10_judge about $0.003 per call | Tenant piece text. All six `t10_*` questions are OFF with no call site (S246 G6). |
| T11 Publish | none | none | No check. |

## 5. $0 measurement before any code (orchestrator runs it)

Four reads, one container script. No LLM, no TypeSafe, no writes. Labels never go to the container.

- **A.** For each of the 200 labelled FAQ questions: every existing `a3_question_about_here` / `a3_landing_belongs` verdict for that
  question text (any scope or moment), with p and the zone at today's floors.
- **B.** Live coverage: the T9 blog pieces' `writer_input.real_questions` and the T8 blog requests' `dfs_paa_snapshot.people_also_ask`,
  by source tier.
- **C.** T2: for each (tenant, tour) with a T2 version, the `tenant_market_seo` keywords (top 5) and PAA (top 3), recomputed with the same
  pure functions, against `a1_keyword_about_tour` / `a3_question_about_here` verdicts.
- **D.** T9 keyword: `seo_context.related_keywords` of the tours with a blog request, against `kw:` verdicts.

**Go / no-go bar (ADR 0007 style).** A variant may act on a T path only when:
- its drops on the 200-set are ≥ 95% panel DROP, with ≤ 2 panel-KEEP false drops;
- its coverage on the live tiers is reported;
- as a Haiku belt, it catches ≥ 1 of Haiku's 4 false keeps with 0 new false drops of KEEP.

C1 and D are scored on coverage plus reject share (no labels exist). C1 rejects get a hand spot-check of 20 before enforcing.

### 5.1 Local: build the container input ($0)

```python
# python3 -I build_jev_t_in.py  -> .tmp-session/jev_t_in.json (questions + scope only, no labels)
import json
R = "/home/nghiep/projects/AA-Ecosys/.tmp-session"
items = [{"id": i["id"], "q": i["question"], "country": i["scope"].get("country")}
         for i in json.load(open(f"{R}/s246-eval/aa779/set.json"))["items"]]
json.dump({"items": items}, open(f"{R}/jev_t_in.json", "w"), ensure_ascii=False)
print("OK", len(items))
```

### 5.2 Container script (S3-mediated ECS exec, api container, cwd /app)

Upload both files to `s3://aa-cis-bronze-005097885195/scripts/`, presign both, then run
`sh -c 'curl -s "$URL_IN" -o /tmp/jev_t_in.json && curl -s "$URL_PY" -o /tmp/jev_t.py && python3 /tmp/jev_t.py /tmp/jev_t_in.json'`.

```python
#!/usr/bin/env python3
"""S247 AA-779 follow-up: do EXISTING Jev verdicts cover the T-series platform inputs? $0, read-only."""
import asyncio, json, os, sys, unicodedata
import asyncpg, boto3

BUCKET, KEY = "aa-cis-bronze-005097885195", "scripts/out/s247/jev_t_reuse.json"
PLATFORM = "00000000-0000-0000-0000-000000000001"
KEYS = ["a3_question_about_here", "a3_landing_belongs", "a1_keyword_about_tour", "a3_demand_belongs"]
PREFIX = {"a3_question_about_here": "paa:", "a3_landing_belongs": "land:"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(s.split()).rstrip(" ?.!")


def splits(body):
    """(head, tail) at every ':' — a scope / moment may itself hold one."""
    i = body.find(":")
    while i != -1:
        yield body[:i], body[i + 1:]
        i = body.find(":", i + 1)


async def main():
    inp = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {"items": []}
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    res = {"session": "S247", "kind": "jev_t_reuse", "read_only": True}
    try:
        fl = {r["question_key"]: dict(r) for r in await conn.fetch(
            "SELECT question_key, mode, accept_floor::float AS a, reject_ceiling::float AS r "
            "FROM shared.decision_question WHERE question_key = ANY($1::text[])", KEYS)}
        res["floors"] = fl
        rows = await conn.fetch("""
            SELECT DISTINCT ON (l.question_key, l.subject_key) l.question_key, l.subject_key, l.probability::float AS p
            FROM shared.decision_log l
            JOIN shared.decision_question q ON q.question_key = l.question_key AND q.question_hash = l.question_hash
            WHERE l.question_key = ANY($1::text[]) AND (l.tenant_id IS NULL OR l.tenant_id = $2::uuid)
              AND NOT l.cached AND l.zone IN ('accept', 'grey', 'reject') AND l.probability IS NOT NULL
              AND l.created_at > now() - interval '180 days'
            ORDER BY l.question_key, l.subject_key, l.created_at DESC""", KEYS, PLATFORM)

        def zone(k, p):
            f = fl.get(k) or {}
            if f.get("r") is not None and p <= f["r"]:
                return "reject"
            if f.get("a") is not None and p >= f["a"]:
                return "accept"
            return "grey"

        res["verdict_rows"] = {k: sum(r["question_key"] == k for r in rows) for k in KEYS}
        idx = {k: {} for k in PREFIX}
        kw = {}
        for r in rows:
            k, sk, p = r["question_key"], r["subject_key"], r["p"]
            if k in PREFIX and sk.startswith(PREFIX[k]):
                for head, tail in splits(sk[len(PREFIX[k]):]):
                    idx[k].setdefault(norm(tail), []).append([head, round(p, 4), zone(k, p)])
            elif k == "a1_keyword_about_tour" and sk.startswith("kw:"):
                tid, _, word = sk[3:].partition(":")
                kw[(tid, word)] = [round(p, 4), zone(k, p)]

        def look(q):
            n = norm(q)
            return {"about_here": idx["a3_question_about_here"].get(n, []),
                    "landing": idx["a3_landing_belongs"].get(n, [])}

        # A. the labelled FAQ set (questions only)
        res["set"] = {it["id"]: look(it["q"]) for it in inp["items"]}

        # B. live T9 pieces + T8 requests, by tier
        def tally(acc, src, v):
            t = acc.setdefault(src, {"n": 0, "about_any": 0, "about_reject": 0, "landing_any": 0, "landing_reject": 0})
            t["n"] += 1
            t["about_any"] += bool(v["about_here"])
            t["about_reject"] += any(z == "reject" for _, _, z in v["about_here"])
            t["landing_any"] += bool(v["landing"])
            t["landing_reject"] += any(z == "reject" for _, _, z in v["landing"])
        t9, t8 = {}, {}
        for r in await conn.fetch("SELECT writer_input->'real_questions' AS rq FROM acp_shared.content_piece "
                                  "WHERE channel = 'blog' AND writer_input ? 'real_questions'"):
            rq = json.loads(r["rq"]) if isinstance(r["rq"], str) else r["rq"]
            for x in rq or []:
                if isinstance(x, dict) and x.get("q"):
                    tally(t9, x.get("source") or "?", look(x["q"]))
        for r in await conn.fetch("SELECT dfs_paa_snapshot->'people_also_ask' AS paa FROM acp_shared.angle_gate_request "
                                  "WHERE channel = 'blog' AND dfs_paa_snapshot IS NOT NULL"):
            paa = json.loads(r["paa"]) if isinstance(r["paa"], str) else r["paa"]
            for q in paa or []:
                if isinstance(q, str):
                    tally(t8, "t8_list", look(q))
        res["live_t9"], res["live_t8"] = t9, t8

        # C. T2 tenant-market keywords + PAA (same pure steps as s1_prefetch.tenant_market_seo, no TenantConfigService)
        c = {"pairs": 0, "kw": 0, "kw_verdict": 0, "kw_reject": 0, "paa": 0, "paa_about": 0, "paa_reject": 0,
             "admin_row_kw": 0, "admin_row_kw_reject": 0, "examples": [], "errors": []}
        try:
            sys.path.insert(0, "/app")
            import services.seo_intelligence.s1_prefetch as P
            from services.seo_intelligence.seed_builder import resolve_buyer_market
            pairs = await conn.fetch(
                "SELECT DISTINCT ttv.tenant_id::text AS t, pt.tour_id::text AS tour FROM gold_aa_internal.tenant_tour_versions ttv "
                "JOIN gold_aa_internal.published_tours pt ON pt.id = ttv.published_tour_id")
            for pr in pairs:
                try:
                    cfg = await conn.fetchrow("SELECT target_market FROM shared.tenant_seo_config WHERE tenant_id = $1::uuid", pr["t"])
                    tm = cfg["target_market"] if cfg else None
                    tm = json.loads(tm) if isinstance(tm, str) else (tm or {})
                    market = P.LOCATION_CODE_TO_MARKET.get(resolve_buyer_market(tm)[0], "US")
                    row = await conn.fetchrow("SELECT tour_id, src_name, country, activities FROM silver_aa_internal.raw_tours "
                                              "WHERE tour_id = $1::uuid", pr["tour"])
                    if not row:
                        continue
                    spec = P.tour_spec(dict(row))
                    spec["foreign"] = await P.foreign_places(conn, spec["country"])
                    spec["places"] = list(dict.fromkeys(spec["places"] + await P.atom_places(conn, pr["tour"])))
                    terms = P.strong_terms(spec["places"]) + spec["activity"]
                    if not terms:
                        continue
                    demand = [dict(d) for d in await conn.fetch(
                        "SELECT keyword, search_volume, people_also_ask FROM acp_contract.search_demand "
                        "WHERE market = $1 AND search_volume > 0 AND keyword ILIKE ANY($2::text[])", market, [f"%{t}%" for t in terms])]
                    for d in demand:
                        if isinstance(d.get("people_also_ask"), str):
                            d["people_also_ask"] = json.loads(d["people_also_ask"])
                    ideas, paa = P.cached_ideas(spec, demand)
                    if not ideas:
                        ideas = P.rank_keyword_ideas([{"keyword": d["keyword"], "search_volume": d["search_volume"]} for d in demand],
                                                     spec["places"], activity_words=spec["activity"], country=spec["country"],
                                                     foreign_places=spec.get("foreign"))
                    top = [i["keyword"] for i in ideas if P._vol(i) > 0][:5]
                    c["pairs"] += 1
                    ex = {"tenant": pr["t"][:8], "tour": pr["tour"], "market": market, "kw": [], "paa": []}
                    for k in top:
                        v = kw.get((pr["tour"], k.lower()))
                        c["kw"] += 1
                        c["kw_verdict"] += v is not None
                        c["kw_reject"] += bool(v and v[1] == "reject")
                        ex["kw"].append([k, v])
                    for q in paa[:3]:
                        v = [x for x in look(q)["about_here"] if x[0] == spec["country"]]
                        c["paa"] += 1
                        c["paa_about"] += bool(v)
                        c["paa_reject"] += any(x[2] == "reject" for x in v)
                        ex["paa"].append([q, v[:1]])
                    adm = await conn.fetchrow("SELECT top_keywords FROM silver_aa_internal.seo_context WHERE tour_id = $1::uuid "
                                              "ORDER BY fetched_at DESC LIMIT 1", pr["tour"])
                    tk = (json.loads(adm["top_keywords"]) if adm and isinstance(adm["top_keywords"], str)
                          else (adm["top_keywords"] if adm else [])) or []
                    for k in tk[:5]:
                        v = kw.get((pr["tour"], str(k).lower()))
                        c["admin_row_kw"] += 1
                        c["admin_row_kw_reject"] += bool(v and v[1] == "reject")
                    if len(c["examples"]) < 40:
                        c["examples"].append(ex)
                except Exception as e:  # noqa: BLE001
                    c["errors"].append(f"{pr['tour']}: {type(e).__name__}: {str(e)[:120]}")
        except Exception as e:  # noqa: BLE001
            c["errors"].append(f"setup: {type(e).__name__}: {str(e)[:200]}")
        res["t2"] = c

        # D. T9 keyword: related_keywords of tours with a blog request vs kw: verdicts
        d = {"tours": 0, "related": 0, "related_verdict": 0, "related_reject": 0}
        for r in await conn.fetch("""
                SELECT DISTINCT ON (sc.tour_id) sc.tour_id::text AS tour, sc.related_keywords AS rk
                FROM silver_aa_internal.seo_context sc
                WHERE sc.tour_id IN (SELECT trip_id FROM acp_shared.angle_gate_request WHERE channel = 'blog' AND trip_id IS NOT NULL)
                ORDER BY sc.tour_id, sc.fetched_at DESC"""):
            rk = json.loads(r["rk"]) if isinstance(r["rk"], str) else (r["rk"] or [])
            d["tours"] += 1
            for k in rk:
                if isinstance(k, str):
                    v = kw.get((r["tour"], k.lower()))
                    d["related"] += 1
                    d["related_verdict"] += v is not None
                    d["related_reject"] += bool(v and v[1] == "reject")
        res["t9_keyword"] = d
    finally:
        await conn.close()
    path = "/tmp/jev_t_reuse.json"
    json.dump(res, open(path, "w"), ensure_ascii=False, indent=1, default=str)
    try:
        boto3.client("s3", region_name="us-west-1").upload_file(path, BUCKET, KEY)
    except Exception as e:  # noqa: BLE001
        print(f"ERR upload {type(e).__name__}: {str(e)[:200]} (local {path})")
        return
    s = res["set"]
    print(f"OK set={len(s)} about_any={sum(bool(v['about_here']) for v in s.values())} "
          f"landing_any={sum(bool(v['landing']) for v in s.values())} t2_pairs={res['t2']['pairs']} "
          f"t2_kw_verdict={res['t2']['kw_verdict']}/{res['t2']['kw']} t9_related_verdict="
          f"{res['t9_keyword']['related_verdict']}/{res['t9_keyword']['related']} out=s3://{BUCKET}/{KEY}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:  # noqa: BLE001
        print(f"ERR {type(e).__name__}: {str(e)[:300]}")
```

The `trip_id` of `angle_gate_request` is the tour id that `fetch_search_demand_signal(req["trip_id"])` reads (`acp_angle_gate/service.py:205`).
Check that `tenant_seo_config.target_market` has the shape `resolve_buyer_market` takes. A per-pair error is recorded and the run goes on.

### 5.3 Local: score A against the panel labels ($0)

```python
# python3 -I score_jev_t.py <jev_t_reuse.json>
import json, sys, unicodedata
R = "/home/nghiep/projects/AA-Ecosys"
E = f"{R}/.tmp-session/s246-eval/aa779"
out = json.load(open(sys.argv[1]))["set"]
sset = {i["id"]: i for i in json.load(open(f"{E}/set.json"))["items"]}
lab = json.load(open(f"{E}/final.json"))["labels"]
rm = json.load(open(f"{R}/docs/audits/2026-10-22-S247-aa779-llm/ship-bar-remeasure.json"))
haiku_fk = {d["id"] for d in rm["disagreements"] if d["llm"] == "KEEP" and d["panel"] == "DROP"}

def n(s):
    s = unicodedata.normalize("NFKD", s or "")
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).lower().split())

def own(moment, sc):
    head = n(moment.split(" — ")[0])
    names = [n(p) for p in sc.get("places") or []] + [n((sc.get("route") or "").split(" — ")[0])]
    return any(h and (h in head or head in h) for h in names)

def about_rej(i, v, exact=True):
    c = sset[i]["scope"].get("country")
    return any(z == "reject" and (not exact or h == c) for h, _, z in v["about_here"])

def about_acc(i, v):
    c = sset[i]["scope"].get("country")
    return any(z == "accept" and h == c for h, _, z in v["about_here"])

def land_rej(i, v):
    return any(z == "reject" and own(h, sset[i]["scope"]) for h, _, z in v["landing"])

variants = {
    "V1 about_here reject (piece country)": lambda i, v: about_rej(i, v),
    "V1b about_here reject (any scope)": lambda i, v: about_rej(i, v, exact=False),
    "V2 landing reject (own moment)": land_rej,
    "V3 V1 or V2": lambda i, v: about_rej(i, v) or land_rej(i, v),
    "V4 V1 or (V2 and not about_here accept)": lambda i, v: about_rej(i, v) or (land_rej(i, v) and not about_acc(i, v)),
}
print("coverage: about_here", sum(bool(v["about_here"]) for v in out.values()),
      "landing", sum(bool(v["landing"]) for v in out.values()), "of", len(out))
for name, f in variants.items():
    drops = [i for i, v in out.items() if f(i, v)]
    ok = sum(lab[i]["label"] == "DROP" for i in drops)
    fd = [(i, sset[i]["question"]) for i in drops if lab[i]["label"] == "KEEP"]
    print(f"{name}: drops={len(drops)} precision={ok / len(drops) if drops else float('nan'):.3f} "
          f"false_drops_of_KEEP={len(fd)} haiku_false_keeps_caught={len(haiku_fk & set(drops))}/{len(haiku_fk)}")
    for x in fd[:5]:
        print("   FD", x)
```

## 6. Should know

- **The calibration was measured on the A3 population, not the T one.** It transfers well for C2/C3 (same `search_demand` PAA) and
  for C1 (same keyword question, same tour state). The **label differs** for C3: FAQ fit is wider than "lands on this moment", hence
  variant V4.
- **Coverage is the main unknown.** A3 asks only about each Segment's shortlist: ≤ 20 questions sharing a claimable word, sorted by
  length. `place_paa` reads any keyword sharing a place word (up to 300 rows), so many T questions will have no verdict. A miss means
  "keep the current rule"; it never means "drop".
- **Verdict age.** The cache window is 180 days, and verdicts from the 01–10/10 runs expire around 03–04/2027. A long-lived reader
  needs the platform re-ask path (§2.2) or the next A3 recompute to refresh them.
- **Floors move only through PUT** (S246 §3). A reuse reader must take floors from `decision_question` at read time, never copy
  them into T code. The `a3_demand_belongs` 0.50–0.70 band is under review (S246 decision 6), and C4 should avoid it until then.
- **Jev credit (about $8.19 at S246).** A pure-read reuse spends nothing. A platform re-ask of misses would add about $0.00001–0.000017
  per pair; a 30-question, 12-Segment Route is at most about $0.006, still below one Haiku FAQ call.
- **Order of work, if the numbers pass.**
  1. C1, a small CIS PR: a read-only helper plus a reject filter in `tenant_market_seo`. It needs no guard change.
  2. C2 + C3 together, in the shared chain (`collect_real_questions` or a post-merge filter), so T8 and T9 see the same cleaned list.
  3. C4 after part D shows coverage.
  - The re-ask path (guard change) comes last and needs an independent review.
