# r5 panel brief — T9 checkpoint r5 (S235), for the orchestrator

**Cost: $0 on the gateway.** Run as local Claude Code agents (Agent tool or a workflow script), the same way as S234 r1–r4 (`.tmp-session/s234/panel_r4.js`). No agent calls the API or the DB. All agents are read-only, except that they may write scratch files under `.tmp-session/s235/r5/panel/`.

**Cách chấm (how it is scored).** There are 4 independent lens raters, plus 1 fidelity auditor, plus 1 product-truth auditor (new in r5: reverse flips and invented sub-activities). The synthesis takes the majority verdict. The deterministic numbers come from `r5_measure.py`. No agent re-scores those numbers.

## 0. Inputs (prepared before the panel)

| File | What |
|---|---|
| `.tmp-session/s235/r5/pieces_r5.json` | The 20 r5 pieces, index 0..19 = piece number. It has the S234 keys (`text`, `seo_title`, `meta`, `seed`, `angle`, `brand_pack`, `keyword`, `status`, `failed`) plus `offered_lines`. `offered_lines` lists each `Status: OFFERED, NOT INCLUDED (…)` line of the seed, with the source line above it (AA-773). |
| `.tmp-session/s235/r5/measure_r5.json` | The deterministic metrics (`r5_measure.py`), r4 and r5 side by side. |
| `.tmp-session/s234/pieces_r4.json` and `docs/audits/2026-10-13-S234-t-series-rounds/07-panel-round4.md` | The r4 baseline. The r4 piece numbering differs from r5, so compare by cell, not by number. |
| `docs/audits/2026-10-13-S233-t-series-checkpoint/01-commercial-panel-round1.md` | The method reference ("Method" and the §1 table formats). |

The cells are the same as in r4:
- A&H blog ×4 and Terra blog ×4: Mongolia route, days 3–14.
- A&H LinkedIn ×3: Punakha.
- WildKind LinkedIn ×3: Punakha.
- Terra LinkedIn ×3: Paro Taktsang. **This cell uses a NEW angle (confound).** The r4 angle "The Checkpoint Before the Temple" was built on a practical card fact that AA-774 removed. Judge the Terra LinkedIn posts on their own text. Do not count a missing checkpoint/camera detail as a defect.
- Trail Pulse LinkedIn ×3: Kuang Si.

## 1. Shared preamble (BASE): give it to every agent verbatim

> Input: `/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/pieces_r5.json`. It holds 20 T9 pieces as a JSON list; index 0..19 = piece number. Each piece has `text`, `seo_title`, `meta`, `seed`, `angle`, `brand_pack`, `keyword`, `status` (approved/held) and `offered_lines`.
> - `seed` is the writer's ONLY source: its moments, the "Place background" facts, and the `Status:` lines.
> - A moment marked `Status: OFFERED, NOT INCLUDED` is an option the traveller may book. It is not part of the plan.
> - A moment marked `Status: included` must never be called optional.
>
> Method reference: `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-13-S233-t-series-checkpoint/01-commercial-panel-round1.md`. Read its "Method" and the §1 table formats, and follow them exactly so the results compare with S233 and S234 r1–r4.
> - **Light edit:** ≤10 minutes, ≤3 sentences changed, no fact research.
> - **Publish as-is:** a paying tenant would post it unchanged.
>
> Read-only: do not edit repo files. Write scratch only under `/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/panel/`. Be a demanding but fair commercial reviewer. Judge each piece on its own text; do not assume it has improved. Do not read the other lenses' outputs.

## 2. The six agents (run 1–6 in parallel)

### 2.1 Four lenses: same roles and schema as S234 r4

Each lens prompt is BASE plus: *"You are ONE lens of a 4-lens panel: `<role>`. Rate ALL 20 pieces independently (do not coordinate with other lenses). Scores /10."*

| Key | Role |
|---|---|
| `editor` | A senior travel EDITOR. Checks accuracy, structure, prose quality, repetition, clichés and AI-tells. |
| `brand-lead` | The TENANT'S BRAND LEAD; reads each piece's `brand_pack`. Asks: does it sound like this brand and fit its audience? Does it avoid the forbidden words and use the brand's CTA? Would you put your name on it? |
| `channel` | A CHANNEL SPECIALIST (LinkedIn / SEO blog). LinkedIn: 120–250 words, ≤3 hashtags, first line ≤140 chars, hook strength. Blog: SEO title, meta, headings and keyword use; scope (every place named must be in the seed SCOPE); FAQ quality. |
| `client` | A PAYING CLIENT (a tour operator) who will publish under their brand. Would you publish it, and how long would editing take? Is there any risk that could embarrass you (false promise, wrong place, invented detail)? |

Output schema for each lens (unchanged from `panel_r4.js` `VERDICT`):

```json
{"pieces": [{"idx": 0, "verdict": "as_is|light|heavy|reject", "overall": 0, "brand_voice": 0,
  "channel_fit": 0, "fidelity": 0, "ai_tells": 0, "hook": 0, "clarity": 0, "commercial_value": 0,
  "top_issues": ["..."]}]}
```

`ai_tells`: 10 = no AI tells. All 20 pieces are required, and each needs every field.

### 2.2 Fidelity auditor: unchanged from r4

Prompt: BASE plus the following.

> FIDELITY AUDIT: for every piece, list every factual claim that is NOT supported by that piece's seed (moments, Place background lines, `brand_pack`). Factual claims include place facts, trip facts, numbers, times, services, promises and social proof.
>
> Classify each claim as one of: `invented_trip_detail`, `invented_place_fact`, `wrong_place_or_scope`, `number_not_in_source`, `social_proof`, `promise`. Also note any contradictions with the seed. Return, per piece, the unsupported claims and a fidelity score /10.

Schema:

```json
{"pieces": [{"idx": 0, "fidelity": 0, "unsupported": [{"claim": "...", "kind": "..."}]}]}
```

### 2.3 Product-truth auditor: NEW in r5 (AA-773 / AA-774 / AA-775 checks)

Prompt: BASE plus the following.

> PRODUCT-TRUTH AUDIT. For each piece:
> 1. Print the piece's `offered_lines`. For a route blog, also list each moment the seed marks `Status: included`.
> 2. Find every **reverse flip** in BOTH directions:
>    - **(a) offered → included:** an OFFERED activity written as part of the plan, as something the reader will do. Examples: "you'll take a boat across the lake", or a list of plan items that includes it, or "on foot, by boat and optionally on horseback", where only the horse is hedged.
>    - **(b) included → optional:** an included activity hedged as optional or as an add-on. Example: "an optional day with the Tsaatan" when the seed has the Tsaatan as a day-5 moment.
>
>    For each flip, quote the exact sentence and name the seed line it contradicts. A sentence that hedges the option ("you can add…", "optional boat rides are available") is NOT a flip.
> 3. Find every **invented sub-activity**: a concrete thing the traveller does that no seed line states. Examples: a rim walk, a town tour, lunch "at" a place the seed says the route passes "near", a sunrise viewing, or a "first night in a ger". Background facts about a place are not sub-activities. Quote the sentence.
> 4. Find every **permit / access / logistics sentence** (permit, "access requires", multi-hour ride, checkpoint, dress code, "visitors must"). Say whether the seed still contains that fact. Since AA-774, the practical card facts should be gone from the seed.
> 5. Find every **pace or rest promise** ("full without being relentless", "not rushed", "time to rest", "a manageable pace"). Mark each one `seed_supported` or `unsupported`, and exclude the CTA line.
>
> Be literal. Count only what the text says, not what it might imply.

Schema:

```json
{"pieces": [{"idx": 0, "offered": ["..."], "included_flagged": ["..."],
  "reverse_flips": [{"sentence": "...", "direction": "offered_as_included|included_as_optional", "seed_line": "..."}],
  "invented_sub_activities": [{"sentence": "...", "activity": "..."}],
  "permit_access": [{"sentence": "...", "in_seed": true}],
  "pace_promises": [{"sentence": "...", "seed_supported": false}]}]}
```

### 2.4 Hard errors: NOT an agent in r5

Instead of a hard-error agent, take `measure_r5.json` (`r5_measure.py`). It runs the unchanged S234 `measure_r4.py` on all 20 pieces, so the counts compare with the r4 table §1.5 (core total 4, 18/20 clean).

## 3. Synthesis (one agent, after §2)

Prompt: BASE plus the 6 JSON outputs plus `measure_r5.json`, plus the following.

> SYNTHESIS. Write `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-14-S235-ecosystem-team-pilot/r5/01-panel-r5.md`. Use the SAME structure as `07-panel-round4.md`:
> - §0 Bottom line.
> - §1.1 overall, §1.2 by cell and tenant, §1.3 per piece.
> - §1.4 r1–r4 vs r5. Add a column to the r4 table.
> - §1.5 hard errors.
> - §2 defect classes, §3 gate behaviour, §4 next fixes.
>
> Rules:
> - Verdict per piece = majority of the 4 lenses. A 2–2 tie takes the stricter label. A piece is as-is only with ≥3 as-is votes.
> - Gate status per piece is the `status` field.
>
> Add a new **§1.6 "Issue checks (AA-773/774/775/776/786)"** table. Its columns are issue | metric | r4 | r5 | target | met/not met:
> - The deterministic rows come from `measure_r5.json` `verdicts` and from the r4 column of its summary.
> - The panel rows come from the product-truth auditor:
>   - reverse flips in r5 (target 0; r4 = 4/8 blogs: #5, #14, #17 offered→included, #18 included→optional);
>   - invented sub-activities per blog (target ≤1/8);
>   - permit/access sentences per blog (target 0/8);
>   - unsupported pace promises (Terra ≤2, A&H ≤1).
> - Also add LinkedIn light (target ≥10/12, r4 10/12), blog light and held, and false passes / false holds.
>
> Caveats to state:
> - n=8 blogs is small. Trust only large deltas (8/8 → ≤2/8, 7/8 → 0/8, 12 → ≤2), and see the A/A′ lesson S224/AA-346.
> - The Terra LinkedIn angle was regenerated (confound).
> - r5 also includes the S234 card merge (122 → 110 cards).
> - Different agent instances than in r4: read changes of about ±0.2 overall or ±1 piece per cell as noise.
>
> Return the report text.

## 4. Orchestrator after the panel
- Draft one Linear comment for each of AA-773, AA-774, AA-775, AA-776 and AA-786. Each comment marks each Done-when bullet met / not met with the number, and links `01-panel-r5.md` and `measure_r5.json`. **Do not post them.** Nghiệp reviews them first.
- Add "chạy bằng gì" (how it ran) to the report: the pieces came from tenant API → `t9_write` on the worker; the regen came from admin → `t8_angles` on the worker; the export ran through ECS exec as a read-only SELECT; the measure ran locally ($0); the panel ran as local agents ($0). Also add the cost from `r5_run.py status`.
