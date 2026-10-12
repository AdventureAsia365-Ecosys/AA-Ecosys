# S229 — T-series audit: kickoff, pre-audit fixes, and what the next session reads

Date: 12/10/2026. Agent: Kiro (WSL). Epic: **AA-741** (T-series end-to-end audit).

**Where the full plan lives:** `docs/architecture/t-series-audit-and-plan.md` (root). That file is
the source of truth — logic of T2/T7–T11, DFS flow, LLM gateway, ADR 0003 gaps, and the ordered
**G1–G15** backlog. This file is the session log: what shipped, what the live state is, and the
exact next step.

---

## What shipped this session (all merged, CI green, deployed to Dev)

Phase 0 of AA-741 = make the T-series measurable, then set up the 4 brand test tenants.

| PR | What | Why it mattered |
|---|---|---|
| App #655 | T-series pre-audit hardening | Jev DPA guard was fail-OPEN for T-stages missing tenant_id; A1-3 meal/time `judge_units` passed a str since #631 (every call failed open); T2 brand-load error was silent (unbranded rewrite); rewrite billing charged before validating; retry race; tenant endpoints accepted staff JWTs |
| App #656 | revalidate judges against the real source tour | `_revalidate_tour` passed only name/country/duration → every source-grounded check (judge, brand audit, A1-3 Jev) compared to an empty source. Bug since AA-234 |
| App #657 | a version can be revalidated more than once | permanent idempotency key `revalidate:{content_id}` → 2nd revalidate returned the old finished job |
| App #658 | tenant offboard never worked | `AmbiguousParameterError` on `$1` (varchar+text) → every offboard 500'd. + offboard now removes the tenant from the Jev allow-list. Integration test on real Postgres |
| App #659 | T0 brand intake | brief .docx upload never parsed (stored only); old parser folded "Should Not Write" into "Should Write"; brand fields silently cut to 300 chars; form markets never read by the pipeline (every tenant wrote for US) |
| App #660 | brand upload/parse as base64 JSON | REST API Gateway (no binaryMediaTypes) corrupted multipart: a 15,191-byte .docx arrived as 25,187 bytes. Every brand file ever archived was corrupted |
| root `5199e2d` | the plan doc | source of truth (above) |
| root (lessons) | 4 lessons | integration test for new SQL; grep callers on signature change; API Gateway binary; "saved != read by pipeline" |

Live Dev after this session: api `:533` / worker `:88`, SHA `16ceff9` (then root doc commits are
docs-only, not deployed). ADR hub-fix recompute from S228 already live.

## Tenants set up (AA-741 phase 0)
- **Offboarded** old test tenants: wanderlux-travel, exploreasia-co, test-1 (is_active=false, keys
  revoked, no data deleted, removed from Jev allow-list).
- **Created 4 brand tenants**, loaded through the real T0 flow (login → upload brief → parse →
  save). Keys only in Secrets Manager `aa-cis/dev/e2e-tenant/<slug>`.

| slug | brand | markets in use (T2 picks one) | unsupported (kept for banner) |
|---|---|---|---|
| atlas-hearth | Atlas & Hearth | US, UK (T2→US) | AE, SA, SG, HK |
| terra-family | Terra Family Expeditions | UK, AU (T2→UK) | AE, SG, HK |
| trail-pulse | Trail Pulse | US, UK, AU, DE, FR, NL (T2→US) | CA, SG |
| wildkind-travel | WildKind Travel | US, UK, AU, DE, FR, NL (T2→US) | CA, NZ |

All 4 on the Jev allow-list. Brand v3 each, style guides 1,043–1,176 chars stored whole.

## The 5 questions Nghiệp raised (answered from code/DB)
1. **DFS US-heavy** — ops gap, not a bug. See the DFS section below.
2. **Tenant 360** — it is the **inline panel inside `/admin/tenants`** (AA-666), not a separate
   page. "Expand Tenant 360" (G9) = extend that panel's tabs.
3. **Goals = 8** in code (`services/acp_angle_gate/goals.py`), mapped from Ms. Thư's "Bảng 1". If
   the source is 10, two are missing — **open question**, reconcile in the T8 audit.
4. **Per-piece cost** — the earlier $0.03–0.06 was 7 short social test writes only; blog costs more
   (JSON envelope + T8 + T10 judges + repair/buffer-retry + HTML export). Real numbers from the
   pilot (G3). Do not quote a figure until then.
5. **LLM per-tenant cost under-counted** (`tenant_id=None`): s1_judge 3/8,393, s1_brand_audit
   0/37, t10_judge 0/23, f10_embed 0/2,861 → G1 fixes it.

## DFS — the design is: admin buys once, tenants only read (confirmed with Nghiệp S229)
This is the original design, verified in code:
- **A tenant NEVER triggers DFS.** 0 tenant-tagged DFS rows since 29/09 (AA-646). Admin buys the
  per-market data once (`segment_research`); tenants only READ it to filter topics, pick
  goal/angle, and write.
- **Unknown / unresearched market — how the system reacts (verified):**
  - **T2 keywords** (`s1_prefetch.tenant_market_seo`): resolves the tenant's market; queries
    `acp_contract.search_demand` for that market; **if nothing matches, returns `(market, None)`**
    → the tour is rewritten with no keywords and logs `t2_seo_context_missing`. The brand voice
    still applies; only SEO keywords are missing. It never falls back to buying DFS.
  - **T7 Slate**: a market with low/zero demand means blog candidates fail the `needs_demand ≥
    1000` bar (fewer/no blog topics); social channels (said-based) still work. Declared-but-
    unsupported countries are returned as `unmatched_markets` and recorded in
    `unmapped_market_requests` for admin to see the demand.
  - **T8/T9**: use whatever PAA/keywords exist; with none, angles/writing proceed on atom text
    without SEO signal.
- **So the gap for DE/FR/NL is purely:** admin only ran `segment_research` for US/UK/AU (DE/FR/NL
  stuck at 96 keywords from a 1–3 Sep trial). Fix = run it for DE/FR/NL (G2), no code change.
- **Product question still open (not a bug):** T2 writes for ONE market (highest-ranked). If AA
  wants a tenant's content generated for several of its markets, that is a product change to add
  to the backlog — flagged, not assumed.

## Linear
AA-741 In Progress, comments added (phase 0 evidence, DFS/goals/Tenant-360/cost clarifications,
plan-doc pointer). AA-670 split → AA-759 (PortalShell) + AA-760 (page audit); AA-672 split →
AA-761 (Account) + AA-762 (Team & roles). AA-696 is now parent of AA-699/700/701; premises of
AA-699 (parser in-process) and AA-701 (WanderLux retired) corrected.

## NEXT SESSION — start here
1. **G1 [backend, $0]** — set `tenant_id` in the gateway via ContextVar (like `job_id`); remove
   `tenant_id=None` at the 9 call sites (judge, brand_audit, flag_fix ×2, itinerary_nudge,
   grounding, source_facts, t10_judge, f10_embed). Test: one T2 + one T9 log a tenant on every
   row. This must be done BEFORE the pilot or the pilot cost numbers are wrong.
2. **Confirm with Nghiệp:** goal count (8 vs 10); whether T2 should write for multiple markets.
3. **G2 [Nghiệp runs]** — `segment_research` for DE/FR/NL (DFS budget $5/run hard-stop; Kiro gives
   an estimate first).
4. **G3** — pilot: 3 tours × 4 tenants + one slate→angle→blog→social per tenant; measure real cost
   per stage (blog vs social separately) and T7/T8 request latency; collect ground-truth labels.

Full ordered backlog G1–G15 + dependency graph: `docs/architecture/t-series-audit-and-plan.md` §7.

## Scripts (in .tmp-session, gitignored — re-create if needed)
`s229_tenant_dry.py` (tenant row inventory), `s229_offboard.py`, `s229_brief_parse.py` +
`s229_t0_load.py` (T0 load via live flow), `s229_allow.py` (Jev allow-list), `s229_cost_routes.py`
(routes + real cost per stage), `s229_dfs_markets.py` (research coverage), `run_script.sh` (ECS
exec runner). Brand briefs: `apps/AA-CIS-App/docs/AI-gent-for automation works/brand identify for
tenant trip content testing/*.docx`.
