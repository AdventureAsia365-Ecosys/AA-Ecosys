# How the place-card drafter/checker models were chosen (history, S233 → S252)

Read-only research, 26/10/2026. Sources are cited inline. AA-CIS-App paths are relative to `apps/AA-CIS-App/`.

## 1. Timeline

| When | What | Source |
|---|---|---|
| S232 (12/10) | Problem: 12/20 Pawangka posts put the monastery in the wrong place (Luang Prabang, Ladakh, "a monastery in China"); the writer padded thin seeds with unsourced background. | `services/acp_shared/place_cards.py` docstring; Linear AA-772 |
| S233 (13/10) | AA-772 shipped (#676, migration 220). Stages `a3_place_card` / `a3_place_card_check` were **copied from `t9_write` / `t10_judge`** ("no model choice changes"), so the draft ran on **Claude Sonnet** (writer) and the check on **GPT-5.6 Luna** (judge). No model evaluation at this point. 74 cards for 3 pilot tours (Bhutan, Laos, Mongolia), 169 Sonnet calls, $1.30 ($0.0176/card). | mig 220 header; S233 log; AA-772 comments |
| S234 (13/10) | Cost cut (#687, mig 221: rule skip, grouping, alias, miss cache). Route left on Sonnet "until the A/B". Nghiệp asked "chưa thử Luna à" → A/B with 4 drafters (§2) → **#692 + migration 222**: draft = GPT-5.6 Luna, check = Claude Haiku, both `validate` (ADR 0008), fallback Sonnet for both. | mig 222; AA-772 notes; `docs/audits/2026-10-13-S234-t-series-rounds/06-place-card-model-ab.md`; lesson #144 |
| S235 (14/10) | AA-774 (fact kinds out of the seed + fact edit endpoint), AA-808 (drafter must not append traveller clauses + post-check), AA-809 (post-draft dedup). No model change. | `docs/implementation-notes/AA-774.md`, `AA-809.md`; S235 log |
| S236 (14/10) | 3-lens agent panel on 8 suspected duplicate clusters (§4). | `docs/audits/2026-10-14-S236-design-review/dup-cards-panel.json` |
| S239 (16/10) | AA-772 closed by Nghiệp; the **thin-seed vs card A/B (Done-when) was dropped**; G7 cards moved to AA-784. | AA-772 comment |
| S246 (21/10) | Stage A/B GPT-5.6 Luna vs GPT-6 Luna on 7 stages incl. `a3_place_card`, n=10 → keep. | `docs/audits/2026-10-21-S246-bedrock-models/stage-ab-gpt6.md`, `ab-gpt6-a.json` |
| S252 (26/10) | 112 cards, all `auto_checked` (0 human-verified), total spend $0.9668; 878/25,878 place atoms linked (3.4%). AA-784 (platform build) still Backlog. | `docs/audits/2026-10-26-S252-propagation-audit/README.md` |

No migration after 222 touches the `a3_place_card*` routes (grep of `api/migrations/*.sql`; `shared/llm_client/role_config.py` SAFE_DEFAULTS mirror 222).

## 2. The S234 A/B (the only evaluation behind the drafter choice)

**Set-up** (`06-place-card-model-ab.md`, mig 222 header, AA-772 notes):
- Sample: **30 places that already had a card** (so from the S233 pilot tours: Bhutan, Laos, Mongolia), same draft prompt for every arm, one run per arm, no repeats. Script `.tmp-session/s234/pc_ab.py`, `pc_ab_luna.py`; stage `adhoc_aa772_ab`. Raw rows (`s234_pc_ab_out.json`, `s234_pc_ab_luna_out.json`) are **no longer in the workspace** (`.tmp-session/s234/` is gone).
- Metrics: "named" (draft returned a place), "identity ok", facts drafted, facts kept ("supported"), facts marked "wrong", draft cost.
- **Who judged: an LLM only.** The production checker at the time (GPT-5.6 Luna) judged every arm; the two Luna arms were also judged by Claude Haiku. Closed book: the checker gets the card and itinerary text, no web search, no reference source, no human labels.

**Results**

| Drafter | named | identity ok | facts | kept (Luna check) | wrong (Luna check) | kept / wrong (Haiku check) | draft cost (30) |
|---|---|---|---|---|---|---|---|
| Claude Sonnet | 28 | 28 | 167 | 152 (91%) | 11 | not run | $0.2734 |
| Claude Haiku | 28 | 24 | 154 | 128 (83%) | 23 | not run | $0.0724 |
| GPT-6 Luna | 26 | 25 | 104 | 98 | 2 | 92 / 1 | $0.0111 (3 empty replies) |
| GPT-5.6 Luna | 27 | 27 | 146 | 145 (99%) | 0 | 134 (92%) / 2 | $0.0226 |

Qualitative note recorded: Haiku failed identity (Takin Zoo → "National Zoo of Bhutan", spellings not normalised); "Luna facts are shorter and carry fewer risky numbers".

**Decision and stated reason** (mig 222, AA-772 notes, lesson #144): draft on GPT-5.6 Luna because identity 27/27, "2 wrong", ~12x cheaper than Sonnet per draft. The check moved from Luna to Haiku **so draft and check stay on different vendors**, not because Haiku was measured as a good checker. Both stages became `validate` because the writer/judge vendor rule would forbid an OpenAI writer + Anthropic judge. Sonnet fallback accepted (then check is same-vendor for that card). `DRAFT_MAX_TOKENS` 900 → 1500 (Luna reasoning tokens).

**Live cost after the switch:** new Nepal tour 40 drafts → 37 cards, $0.082 = **$0.0022/card** (draft + check, misses included) vs $0.0176 on Sonnet (AA-772 comment). S246: $0.0026 per draft+check sample.

## 3. Reading the A/B critically

- **The headline "Sonnet 11 wrong vs Luna 2 wrong" compares two different judges.** Sonnet's 11 come from the Luna checker; Luna's 2 come from the Haiku checker. Under the same (Luna) checker Luna scored 0 wrong, which shows a same-vendor checker is lenient on its own family's output; nobody ran Haiku on the Sonnet drafts, so a like-for-like comparison does not exist.
- On the comparable numbers, **Luna ≈ Sonnet**: identity 27/27 vs 28/28, kept rate 92% (Haiku check) vs 91% (Luna check). Luna drafted 13% fewer facts (146 vs 167). The evidence supports "same LLM-judged acceptance at ~1/12 the cost", not "Luna is more accurate".
- The two checkers disagreed on 11 Luna facts (145 vs 134 kept); the disagreement was not adjudicated.
- Haiku, chosen as the checker, was the weakest drafter in the same A/B (4 identity misses, 23 facts marked wrong). Its ability to catch errors (recall on planted false facts, wrong locality) was never measured.
- S246 re-run (n=10, golden fixture 1.1.0, Haiku check): kept rate 0.84–0.88 on GPT-5.6 Luna, identity_ok 1.0, agreement with stored card 0.9, `label_agreement: null` (no labels exist). GPT-6 Luna: kept 0.83, 1 empty reply (max_tokens) → keep 5.6.

## 4. Known failure modes since

Card origin matters: the S233 cards (~74, minus merges) were **drafted by Sonnet**; S234 Nepal (37) + Laos rebuild (13) and the S235 AA-808 trial (5) were **drafted by Luna**. The S236 Tibet clusters (Gyirong, Zhongba, Manasarovar, Rongbuk) are most likely from the Luna-drafted Nepal/Kailash tour (inference, not checked in DB).

1. **Duplicates.** S233: "Paro"/"Paro Town", Samdrup Jongkhar gate/crossing. LLM free-text locality in the key split one lake (Khövsgöl) into 5 cards → key changed to core name | country (S234). S234 DRY RUN: 8 groups / 11 extra cards + 1 orphan, merged. S235 AA-808 trial (Luna): **2 of 5 new cards duplicated existing cards** (Zorig Chusum exact name; "Kuang Si Waterfall" vs "Kuang Si Falls") → AA-809 post-draft resolver (place_key → alias → core → feature synonym → draft alias; ambiguous → insert). AA-809 verified only "resolver live 5/5 correct (read-only)". S236 panel on 8 clusters: 2 merge_partial (Paro/Paro Town; Rongbuk), 1 relink (Zhongba), rest keep + fix.
2. **Wrong locality / identity / entity mixing.** S232 origin. S234 "Sod Camp" card put a Day-3 camp on the Khövsgöl lakeshore (fixed by an `overnight_card_off_route` seed rule, not in the card). S236 panel: Gyirong card says the town is the county seat (the seat is Zongga); Rongbuk card mixes valley and monastery and holds the monastery's aliases (caused a mislink); Zhongba town card carries county aliases; Burang vs Purang locality spellings; garbled "Mapham Yutso"; Punakha town card's only what_it_is fact describes the Dzong.
3. **Unsupported / wrong / inconsistent facts that passed the check.** Khövsgöl share of world fresh water 70% / 2% / 0.4% across cards (seed-side `canonical_facts` added S234). Mongar Dzong date "20th century" vs "1930s" (panel: neither verified); Mongar elevation ~1,800 m probably high; Kharkhorin 360 vs 370 km; Karakorum "founded by Ögedei ~1235" oversimplified; Paro "only international airport" in-town overstated; Taktsang reopening 2004 vs 2005; dress-code rules stated as fact. These were found by an agent panel (no web check either), and only on 8 clusters.
4. **Traveller clauses / kind mis-tagging.** S235 two-lens audit of 110 cards / 732 facts: 31 writer-kind facts were really visiting/practical ("…making it a natural stopping point", "offers views"), 22 the other way; 54 edits applied by hand (AA-774). Drafter rule + post-check AA-808: 31/31 caught, 0/22 false hits, trial 5 cards 0 clauses.
5. **Coverage.** S252: 3.4% of place atoms linked; 112 cards; 0 human-verified.

## 5. What the evaluation did NOT measure

- **Ground truth.** No human labels, no web or reference-source verification (Wikipedia/Wikidata/official sites), no geocoder cross-check of locality. "Wrong"/"supported" is one LLM's closed-book opinion of another's.
- **Like-for-like judging.** Different checkers per arm; checker leniency (same-vendor) and checker recall/precision were not measured (no planted errors, no inter-checker adjudication).
- **Representative places.** n=30, one run, no variance; places that already had cards from 3 pilot countries, mostly well-known landmarks. The real AA-784 workload (~9.2k place groups, many small villages, passes, camps, Pakistan/Central Asia/Vietnam/India/China) is the long tail where closed-book LLMs hallucinate most.
- **Locality accuracy separately** (identity_ok lumps name, locality, region and country into one boolean judged by an LLM).
- **Duplicate/alias behaviour, kind tagging, cross-card consistency, numeric accuracy** per model.
- **Downstream effect.** The AA-772 Done-when A/B (thin seed vs card, n≥20, fidelity / light-edit / F9 hold) was dropped (S239); no measure of writer fidelity per drafter model.
- **Other options.** Not tried: a stronger closed-book model (Sonnet newer tier / Opus) as checker, a web- or source-grounded draft/check, per-fact provenance (promised in the AA-772 scope, never built), a human spot-check (AA-784 Done-when asks for 30 random cards, ≥27 correct identity, still not run).

## 6. Cost reference (current route)

- Draft GPT-5.6 Luna ≈ $0.0009/call; check Haiku ≈ $0.0012/call; ≈ $0.002–0.0026 per card (S234 live, S246).
- Sonnet draft ≈ $0.009/call in the A/B (≈ 12x Luna); S233 live $0.0176/card on Sonnet incl. repeat drafts.
- At 9,186 groups, even a Sonnet draft + stronger check would be in the order of $100–150; the quality question, not cost, is the open decision.
