# T9 social and blog writing audit (S232): 49 pieces scored by a 4-lens commercial panel

**Scope.** 49 T9 pieces generated on 12/10 between 07:41Z and 11:17Z, in 9 waves (W1–W9). Each wave re-ran the same 5 briefs from S231 after one of the fixes #665–#673.

| Tenant / channel | Pieces |
|---|---|
| Atlas & Hearth (A&H) blog: Craft Bazaar | 10 |
| A&H LinkedIn: Pawangka | 10 |
| Terra blog: Laos cycling route | 10 |
| Terra LinkedIn: Pawangka | 10 |
| Trail Pulse LinkedIn: Tiger's Nest | 9 |
| WildKind | 0 |

**Method.**
- **Panel:** 4 lenses (editor, tenant brand lead, channel specialist, paying client), 196 votes in total.
- **Piece verdict:** the majority vote. The 6 pieces with a 2–2 tie get the stricter label. Light = light edit, Heavy = heavy edit, Reject = do not publish.
- **Evidence:** gate results and Jev logs from `jevinv_cmp.txt`, 127 flagged claims from F9, a reading of the prompt and gate code, and text metrics I computed on every piece.

---

## 0. Bottom line

1. **Not commercial-grade.** No piece is publish-as-is (0/49 pieces, 0/196 votes).
   - Light edit 12 (24%), heavy edit 33 (67%), reject 4 (8%).
   - The best piece scores 7.0/10 (#23). No piece reaches 7 on AI-tells, and only 3 reach 7 on fidelity.
2. **The gates do not measure what a client pays for.**
   - Approved pieces are light-edit 33% of the time; held pieces 22.5%.
   - 6 of the 9 approved pieces need a heavy edit, and 9 of the 12 light-edit pieces were held.
   - "Hold everything" would agree with the panel more often (37/49) than the gates do (34/49).
   - F9_cta_fact fired on 80% of pieces and is in practice the only switch that decides approval.
3. **The quality limit is set before the gates.**
   - Neither the angle step (T8) nor the writer (T9) receives the tenant's brand pack.
   - Every prompt carries "Adventure Asia (AA)" and "premium" defaults.
   - All 5 angle briefs tell the writer to invent detail or to break a rule in the tenant's own brand guide.
   - The seeds hold about 4–25 facts for pieces of 250–1,300 words.
4. **Quality follows how many facts the seed provides.**
   - Trail Pulse has about 3.6 seed facts per 100 words: 4 of 6 pieces light-edit after #669.
   - The Pawangka posts have about 1.5: 0 of 12 light-edit.
5. **The S232 fixes removed the fatal errors but did not close the gap to publishable.**
   - Rejects fell from 21% to 0% after #669, but the light-edit share only moved from 21% to 27%.
   - Later fixes loosened the gates faster than quality improved: of 7 approvals in W6–W9, the panel rated only 1 as light-edit.
   - Some fixes created new defects:
     - 21-character SEO titles on 5/5 recent A&H blogs
     - meta descriptions cut mid-phrase (2/10)
     - "a monastery in China" (5/8 recent Pawangka posts)
     - Thimphu no longer named (0/4)
6. **What works.**
   - Hooks score 6.4.
   - The Terra blog's structure and practical content are sound.
   - Trail Pulse posts written from a richer seed come close to publishable.
   - About 80% of the claims F9 flags are genuinely unsupported.

**Decision.** Do not sell or expand T9 on its current inputs. Fix the inputs (P0 in §E) before tuning the gates any further, then re-measure on a fixed golden set against the bar in §D.

---

## A. Commercial verdict

**A1. Overall**

| | Publish as-is | Light edit | Heavy edit | Reject |
|---|---|---|---|---|
| Pieces (n=49) | 0 (0%) | 12 (24%) | 33 (67%) | 4 (8%) |
| Lens votes (n=196) | 0% | 31% | 61% | 8% |

**A2. By tenant, channel and gate decision**

Panel verdicts are shown as Light / Heavy / Reject.

| Cell | n | Approved | Approved: L/H/R | Held: L/H/R | Light votes | Overall /10 |
|---|---|---|---|---|---|---|
| A&H blog | 10 | 2 | 1/1/0 | 0/8/0 | 25% | 5.45 |
| A&H LinkedIn | 10 | 2 | 0/2/0 | 1/6/1 | 12% | 4.56 |
| Terra blog | 10 | 0 | – | 4/6/0 | 45% | 6.03 |
| Terra LinkedIn | 10 | 2 | 0/2/0 | 1/5/2 | 12% | 4.47 |
| Trail Pulse LinkedIn | 9 | 3 | 2/1/0 | 3/2/1 | 61% | 5.52 |
| **Blog** | 20 | 2 | 1/1/0 | 4/14/0 | 35% | 5.74 |
| **LinkedIn** | 29 | 7 | 2/5/0 | 5/13/4 | 28% | 4.83 |
| **All** | 49 | 9 (18%) | 3/6/0 | 9/27/4 | 31% | 5.20 |

**A3. Score by dimension (/10)**
- Fidelity 5.0 · specificity 5.2 · AI-tells **4.75** (lowest) · CTA 5.6 · channel craft 5.8 · brand voice 6.4 · hook 6.4.
- Correlation of each dimension with the overall score: fidelity r=0.78, specificity 0.71, channel craft 0.64, brand voice 0.62, AI-tells 0.60, CTA 0.26.
- LinkedIn is much weaker on specificity (4.4 vs 6.4) and brand voice (5.75 vs 7.33).
- Same tenant, different channel: Terra's brand voice is 7.35 on the blog and 5.18 on LinkedIn.

**A4. Effect of the code changes, waves W1–W3 (n=19) vs W4–W9 (n=30)**

| Metric | W1–W3 | W4–W9 |
|---|---|---|
| Reject | 21% | 0% |
| Light edit | 21% | 27% |
| Fidelity | 4.48 | 5.35 |
| AI-tells | 5.02 | 4.58 |
| Approvals | 0 | 9 |

Of the approvals that the panel rated light-edit: W4–W5 had 2 of 2; W6–W9 had only 1 of 7.

**What this means for a client:**
- **Trail Pulse LinkedIn** is closest to sellable. Its weaknesses are a voice that is too reflective and the missing social side of the brand.
- **Terra blog** is second (45% light votes), but all 10 were held. They promise "to Hanoi" while the content stays in Laos, invent operational reassurance, and barely mention safety.
- **A&H blog** pads with unsourced cultural claims, and 4 of the 10 are truncated.
- **A&H LinkedIn and Terra LinkedIn** are the worst (12% light votes, 3 of the 4 rejects). Each is built on a single-fact seed and an angle that breaks the brand's own rules.

---

## B. Gate accuracy vs the panel

**B1. Confusion matrix**

| | Panel light | Panel heavy | Panel reject |
|---|---|---|---|
| Approved (9) | 3 | 6 (3 of them 2–2 ties) | 0 |
| Held (40) | 9 | 27 | 4 |

- Approval precision is 33%, against a base rate of 24%.
- Only 25% of light-edit pieces were approved.

**B2. False holds: held, but the panel majority says light edit (9 pieces)**

| # | Cell / wave | Held by | Assessment |
|---|---|---|---|
| 1 | A&H LinkedIn W1 | F9 FACT_CHECK with no reason given | Not really a false hold. The piece moves Pawangka to Luang Prabang, and the panel split 2L/1H/1R. |
| 2 | Terra blog W1 | F9 with no reason given (the judge had no source) | False hold. Fixed by #665. |
| 6 | Terra LinkedIn W1 | F1 on "7–16", the brand's own audience ages | False hold. Fixed by #665. |
| 31 | Terra blog W6 | F9 "judge unavailable" (token cap on the Luna route) | Infrastructure false hold. Fixed by #672. |
| 26 | Terra blog W5 | F3 (no one-sentence paragraph) + F9 (4 claims: "hilly", "the only way in", rest days) | The F3 failure is cosmetic. The F9 claims are real but take about 5 minutes to fix. |
| 28 | Trail LinkedIn W5 | F9: "making this climb for centuries" | Correct flag, wrong action: a one-clause fix. |
| 38 | Trail LinkedIn W7 | F9: "among the most sacred sites in Vajrayana Buddhism" | Correct flag, wrong action: a one-clause fix. |
| 18 | Trail LinkedIn W3 | F9 flagged 3 phrases: the required CTA itself (a judge error), a misreading of prayer flags (a real error), and "most hikers pause" | Mixed. |
| 41 | Terra blog W8 | F9: 5 claims, including the invented testimonial "parents most often describe…" | Correct flags; a light edit fixes them. |

- 3 of these were already fixed during S232.
- 5 are "correct flag, wrong action": the system holds the whole piece when 1–5 sentences need cutting or softening.
- On the second attempt, the repair fixed F9 in only 7 of 35 cases (20%).

**B3. False passes: approved, but the panel says heavy edit (6 pieces: 3 clear, 3 ties)**

| # | Cell / wave | What the panel found | Why no gate caught it |
|---|---|---|---|
| 29 | A&H blog W6 | Unsourced craft claims ("among the most technically complex in Asia", "passed through family lines"); 8 "X is not Y" frames; Thimphu never named; title "Bhutan's Craft Bazaar" | The "widely known background" allowance in #671 lets the judge pass cultural generalisations. There is no check on SEO quality, and the title fitter produced the 21-character title. |
| 32 | Terra LinkedIn W6 | Reads like a school trip; no pace, safety or altitude for a site near Lhasa | The tenant's brand rules reach neither the writer nor the judge. F9 uses the Adventure Asia rubric, and nothing checks the brand's core themes. |
| 45 | A&H LinkedIn W9 | "a monastery in China"; the one seed fact appears twice in about 225 words | The seed's location is "China", and the #671 rule forbids naming Lhasa or Tibet. Nothing checks repetition or thinness. |
| 33 (tie) | Trail LinkedIn W6 | Reflective tone, agency jargon ("experience design"); no group, food or people | F9_brand_style did flag it, but that check does not block and uses the AA rubric. |
| 35 (tie) | A&H LinkedIn W7 | "There is a monastery in China … by a Tibetan royal king"; overreaches on history | Same as #45. |
| 47 (tie) | Terra LinkedIn W9 | The writing-origin fact 3 times; "structured curricula"; LinkedIn asterisks | No check for repetition, brand themes or LinkedIn formatting. |

The mechanism: F9 approves pieces that invent nothing. With a 4-fact seed, those are the pieces that repeat the seed. **Thin pieces pass, rich-but-invented pieces are held.**

**B4. Each gate on the final attempt**

| Gate | Blocking? | Fired | Panel overall when fired vs passed | Reading |
|---|---|---|---|---|
| F9_cta_fact (LLM) | yes | 39/49 (80%) | 5.15 vs 5.40; light 23% vs 30% | Flags are mostly real (about 80% of the 127 claims are unsupported, about 14% are rhetoric, about 5% are wrong). It fires on almost everything, so it cannot rank pieces. |
| F9_brand_style (LLM) | no | 9/49 | 4.89 vs 5.27; caught 3 of 4 rejects | Uses the AA rubric. It flagged lines that are on-brand for Trail Pulse ("a small teahouse where everyone quietly reassesses their life choices", "grinning at the absurdity…") but passed "At Arcadia Adventures". |
| F8_framework (LLM) | no | 13/49 | 5.52 vs 5.08 (inverse) | Noise. |
| F3_structural_variance | yes (blog) | 10/20 | 5.67 vs 5.81 | No quality signal. |
| F4_seo_surface | yes (blog) | 5/20 | 5.78 vs 5.73 | Checks format only. Since #670 the fitter makes it pass by damaging the title or meta. |
| F1_grounding (numbers) | yes | 5/49 | 5.44 vs 5.17 (inverse) | Flags true but unsourced numbers (3,120 m, 900 m). Cannot see invented facts that contain no numbers. |
| F5_atom_density | yes (blog) | 2/20 | 5.25 vs 5.79 | A symptom of the thin seed. |
| F2, F4_extreme_length, F6, F7, F10, promises_an_option | – | 0/49 | – | Never fired (details below). |

On the gates that never fired:
- F6 only checks that a CTA string was configured, so it passed #0 and #39 even though their CTA was cut off.
- F10 measures similarity to other tenants' text, not names, so it missed both brand-name leaks.
- F7 missed the FAQs that repeat the body.

**B5. Jev shadow signals (observe-only)**
- `t10_brand_voice` vs the panel's brand voice: r=0.11 (Spearman 0.17). It ranks Terra blog lowest (0.51) where the panel ranks it highest (7.3). Because it uses the AA rubric, it measures how close a piece is to Adventure Asia's voice.
- `t10_rubric_met` vs overall: r=0.05–0.15.
- `t10_cta_clear` is almost constant (0.93–0.97), while the panel's CTA score ranges from 1.3 to 7.5.
- **`t10_faq_restates` is the one promising signal.** It scored ≥0.83 on #16, #21, #44 and #46, where the panel saw the FAQ repeating the body.

**B6. Repair loop**
- 43 of 49 pieces needed a second attempt.
- F9_cta_fact went from fail to pass in 7 of 35 cases.
- F3 went from fail to pass in 4 of 8.
- F9_brand_style flipped in both directions (6 fail→pass, 4 pass→fail), which is noise.

---

## C. Top quality gaps, ranked by impact

### C1. Inventing specifics to fill thin seeds
Fidelity averages 5.0 and is the strongest predictor of the overall score (r=0.78).

**Impact**
- F9 flagged unsupported claims in 39 of 49 pieces.
- In W5–W9 alone there are 127 unique flagged sentences across 25 pieces (final and discarded attempts); 48 of them come from the 5 A&H blogs.
- 24 of 49 pieces have a panel fidelity of 5 or below.

**Evidence**
- 9/10 Terra blogs mention a map. The angle brief prescribed "the guide unrolling a map"; the seed has no map.
- 7/10 A&H blogs build on weaver or vendor behaviour, but the seed contains only place names.
- Invented claims:
  - "Pacing is built in. Rest is planned, not squeezed in." (#36)
  - "It is the part of the trip that parents most often describe…" (#41)
  - "There is no reconstruction." (#22). The panel says the monastery was damaged and rebuilt, so this is very likely false.
  - "At Atlas & Hearth, we work with a small number of travelers each year" (#20)

**Root causes**
- **Angle briefs (T8) prescribe detail the seed does not have:**
  - Terra blog: "the guide unrolling a map"
  - Terra LinkedIn: "sound of prayer wheels, smell of incense"
  - A&H blog: "one precise, unexpected detail … a specific craft object or transaction" and "why Bhutan is one of the only places…"
  
  The writer follows the brief over the fidelity rule.
- **Seed vs length:** no rule ties the length of a piece to how much the seed contains. The blog band is 4,700–13,000 characters.

**Seed density vs quality (W4–W9; facts hand-counted, so approximate)**

| Brief | Usable seed facts | Words | Facts per 100 words | Overall | Light edit |
|---|---|---|---|---|---|
| Trail LinkedIn (Tiger's Nest) | ~10 | ~276 | ~3.6 | 6.10 | 4/6 |
| Terra blog (Laos route) | ~22 | ~855 | ~2.6 | 5.98 | 3/6 |
| A&H blog (Craft Bazaar) | ~16 (only ~3 on the angle's topic) | ~1,030 | ~1.6 (~0.3 on topic) | 5.03 | 1/6 |
| A&H LinkedIn (Pawangka) | ~4 | ~250 | ~1.6 | 4.67 | 0/6 |
| Terra LinkedIn (Pawangka) | ~4 | ~300 | ~1.3 | 4.60 | 0/6 |

The pattern supports this within one brief as well: Trail Pulse fidelity went from 4.3 to 6.8 once #669 added the trail details (dirt track, midpoint café, steps, 3,120 m).

### C2. Briefs and prompts that contradict the tenant's own brand
Brand voice is 5.2 for Terra LinkedIn and 5.6 for Trail Pulse.

**Impact.** 3 of the 5 briefs (29 pieces, 59% of the sample) rest on an angle that breaks an explicit "Avoid" rule in the tenant's guide.

| Brief | Angle | Brand rule it breaks | Result |
|---|---|---|---|
| Terra LinkedIn | "What Pawangka Teaches Kids That Classrooms Can't" | "Do not make the tour sound like a school trip" | 9/10 use classroom, curriculum or lesson framing |
| A&H LinkedIn | "The Monastery That Refuses to Be Found Easily … positions **AA** as the curator of access" | "Do not overpromise rare access" | 9/10 claim exclusive or private access |
| Trail LinkedIn | "the hike itself as the transformative part" | "Do not overpromise … transformation" | Solitary, reflective posts; group or social words in only 4/9 |

The brand's core themes are mostly missing:
- **Terra LinkedIn:** pace 4/10, rest 3/10, safety 1/10, altitude 0/10 (Lhasa is about 3,650 m).
- **Terra blog:** safety 1/10.
- **A&H blog:** private guiding 2/10, stays 2/10.

25 of 29 LinkedIn posts contain a self-positioning line such as "At Trail Pulse, we…", often with invented brand facts.

**Root causes**
- **Writer inputs:** T8 and T9 receive only `customer_segment`, `customer_mindset`, and (since #669) the brand name. They never receive `core_idea`, the voice examples, forbidden words, good examples or the style guide (`brand_audience.py`).
- **Hardcoded platform brand in the prompts:**
  - The T8 system prompt opens: "senior content strategist for **Adventure Asia (AA)**".
  - The goal description "…quan điểm AA" is sent verbatim, in Vietnamese, inside the English writer prompt.
  - The LinkedIn spec contains "→**AA positioning**→" and "premium không kiêu", which produces the "At <Brand>, we" paragraphs.
  - The writer's system prompt says "a **premium** travel brand" for every tenant.
- **Judge rubric:** F9 and Jev judge every tenant against `AA_BRAND_IDENTITY_PROMPT` ("Senior professionals 40–60, $250k+ … FORBIDDEN: fun, explore…"). This happens because `tenant_brand_rules.system_prompt` is empty; the T0 brand intake fills only the structured fields.

### C3. Place and scope integrity
This caused 3 of the 4 rejects.

**Evidence**
- **Pawangka (20 posts):**
  - placed in Luang Prabang in 6 (W1–W3)
  - placed in Ladakh in 1 (W5)
  - called "a monastery in China" in 5 (W6–W9)
  - Lhasa is named only once (#3)
- **Terra blog:** 10/10 titles promise "Laos to Vietnam" or "to Hanoi", but every seed moment is in Laos.
- **A&H blog:** 10/10 say the trip runs "east to west", but every seed moment is in Thimphu or Paro (western Bhutan). After #671, 0 of 4 name Thimphu, which loses the main SEO keyword.

**Root causes (seed and prompt rules)**
- **Location data:** the seed's location line is only "place, country", and Pawangka's country is "China". The #671 rule ("never place it in another town, region") then forbids naming Lhasa, Tibet or Thimphu.
- **Sibling lines:** the "Other itineraries with the same moment" lines bring in other countries — Alchi and Dat (Ladakh), Gandan and Erdene Zuu (Mongolia), even a Seoul city tour under Ta Dzong.
- **Route scope:** a route seed covers only part of the trip, but the full trip name is passed with no limit on scope.
- **Facts block:** in W1 the Laos e-visa fact appears in A&H Pawangka posts (#1 and #5 quote it). It is the likely anchor for the Luang Prabang placement.

### C4. Thin, repetitive LinkedIn posts
LinkedIn specificity is 4.4; the Pawangka cells score 3.4–3.8.

**Evidence**
- The Pawangka seed has one substantive fact: 7th century, Songtsen Gampo, origins of Tibetan writing.
- 7 of 12 posts after #669 repeat it 2–3 times in about 250 words. #45 has "built in the seventh century" twice and "Songtsen Gampo" twice.
- The W1–W3 posts never mention this fact, which fits a seed that then held only the label. Those posts invented everything else.
- 4 of the 9 approvals are Pawangka posts, and the panel rates every one heavy-edit or a tie.

**Root cause.** Nothing checks for a minimum amount of information. The LinkedIn length band is 20–6,000 characters, and no gate checks repetition.

### C5. AI-sounding phrasing and the same template across samples
AI-tells average 4.75, and 0 of 49 pieces score 7 or more.

**Evidence**
- 48/49 pieces contain "not X but Y" or "isn't X. It's Y" frames, and 23/49 contain three or more (137 in total, by a conservative regex).
- Blogs use "genuine(ly)" 1.6 times on average.
- Stock lines recur: "That's the point", "Here's the insight…", "That distinction matters…".
- **The same brief produces the same skeleton:**
  - 10/10 Terra LinkedIn posts open with "There is a moment…" or "There's a moment…" (7 of them with "a child goes quiet").
  - 9/10 A&H LinkedIn posts open with "There is a…".
  - 6/9 Trail posts open on the hiker's legs.
  - "Not bored-quiet. Still-quiet." appears word for word in #27 and #47.
- #672 cut the contrast frames from 3.1 to 2.1 per piece, but the panel's AI-tells score did not improve (4.87 → 4.47).

**Root causes**
- The writer's banned-phrase list targets older clichés ("nestled", "tapestry").
- F9's GENERIC_AI_WORDING example only targets superlative filler, and says "do not flag calm, precise, unhurried writing", which is exactly where these patterns sit.
- F9_brand_style does not block, and its findings are not sent to the rewrite.

### C6. Production defects
CTA scores 5.6 and channel craft 5.8.

**Truncation.** 5 of 20 blogs end mid-sentence or with an artifact. One of them (#24) was approved.

| # | How the piece ends |
|---|---|
| #0 | "…unobstructed t" |
| #21 | "…— starting" |
| #39 | "…and that the traveller" |
| #19 | trailing "\" |
| #24 | final FAQ answer has no closing punctuation |

- **Cause:** the writer's `max_tokens` is 2048. That is too small for a 950–1,300-word blog plus the JSON wrapper plus citation tags, and it contradicts the 4,096 rule quoted in the same code comment.
- `json_repair` silently rescues the cut-off body, and nothing checks whether the model stopped because it hit the token limit.

**SEO fitter (#670)**
- `fit_seo_title` was built for tour names. It cuts at the colon, so every A&H blog after #670 (5/5) gets the 21-character title "Bhutan's Craft Bazaar".
- The meta fitter cuts mid-phrase: "…explored on a 10-day." (#34) and "…a country that has kept." (#39).
- 7/10 A&H metas reuse the same template line, "more than a market — it's a living index/record of the country's values".

**CTA**
- 13 of 20 blogs have no CTA in the body: 11 have it only inside the FAQ, and 2 lost it to truncation.
- **Cause:** the format rule "put the FAQ LAST" conflicts with the channel structure "…FAQ→CTA".
- All 29 LinkedIn posts include the CTA.

**LinkedIn format**
- 3/29 posts contain markdown asterisks, which LinkedIn shows as literal characters.
- 8/29 have a first line longer than 140 characters, so it is cut at "…see more".
- 0/29 end with a question, and none use hashtags.

### C7. Brand-name integrity
Fatal when it happens. Now patched in the prompt, but no gate checks it.

**Evidence**
- #4 says "At Arcadia Adventures, we build…" and #13 says "At Adventurous Afternoons…".
- Discarded attempts also invented "Adventure Airlines" and "Authentic Asia".
- Every invented name is an expansion of "AA".

**Root cause**
- "AA" appears in the goal text, the channel text and the T8 prompt.
- Before #669 the writer was never given the tenant's name.
- #669 added that name, and there have been no leaks since (0/30). There is still no deterministic check, and F9 passed #4.

### C8. Channel fit
LinkedIn uses one spec for every tenant: "thought leadership … B2B … premium positioning".
- **Trail Pulse (ages 25–40) and Terra (parents):** that spec forces an essay register. The panel calls these posts "essays" with "no reason to comment".
- **A&H:** its audience (advisors, family offices) does fit LinkedIn, yet its posts give an advisor nothing to use.

---

## D. A measurable "commercial-grade" bar

**D1. Release acceptance on a fixed golden set**

The golden set:
- at least 50 pieces covering 4 tenants × 2 channels × at least 6 briefs, mixing thin and rich seeds;
- scored by the 4-lens panel, plus a human editor on a stratified 20% sample.

| Ship only when | Today |
|---|---|
| 0 fatal defects | Reject 8%; truncation in 25% of blogs |
| ≥80% publish-as-is or light edit (light = ≤10 minutes, ≤3 sentences changed, no fact research) | 24% |
| ≥30% publish-as-is | 0% |
| Mean overall ≥7.0, and no dimension averages below 6.5 | 5.2; AI-tells 4.75 |
| Gate precision (approved pieces that are as-is or light) ≥85%, recall ≥70% | 33% / 25% |
| Human–panel agreement on the verdict ≥75% | Not measured |

**D2. Hard fails for both channels (deterministic where possible; any one means never deliver)**

| Check | Rule | Today |
|---|---|---|
| Brand integrity | Only the tenant's own name; no other tenant name, no "AA" expansion, no invented "At X, we" | 2/49 (before #669) |
| Place integrity | Every named place is in the seed's place data (city, region, country) and is not moved | 7/20 Pawangka posts mislocated |
| Scope | Places and promises in the title, H1 and meta are covered by the seed | 10/10 Terra blogs ("to Hanoi") |
| Product truth | No unsupported promise about the trip (activities, pacing or rest days, support, private access, guides, inclusions, times, prices); no invented testimonials or "most visitors" claims | About 80% of pieces flagged |
| Completeness | The model finished normally; the text ends with punctuation; every FAQ question has a complete answer; no escape artifacts | 5/20 blogs fail |
| CTA | The tenant's CTA appears once, in the last body paragraph (for blogs, before `## FAQ`), in the brand's voice | 13/20 blogs fail |
| Sensitive naming | Each place uses its display name from the place data (for example "Lhasa, Tibet") | 5/8 recent Pawangka posts say "in China" |

**D3. LinkedIn bar**

| Dimension | Measurable rule | Today |
|---|---|---|
| Length | 120–250 words (A&H up to 300) | 183–330 |
| Hook | First line ≤140 characters and built on a concrete seed detail; no "There is a moment" | 21/29 ≤140; 19/20 Pawangka posts open "There is…" |
| Information | ≥2.5 verified facts per 100 words; no fact repeated except the place name | Pawangka ~1.5; 7/12 repeat |
| Brand | Tenant-rubric score ≥7.5; at least 2 of the brand's core themes; 0 forbidden words; at most 1 self-positioning sentence, with no invented brand facts | 5.75; 25/29 contain "At <Brand>, we…" |
| AI-tells | ≤1 contrast frame per 150 words; 0 stock phrases; "genuinely" at most once | ~2.4 frames per post |
| Format | No markdown; paragraphs of ≤2 sentences; 0–3 hashtags; ends with the CTA or a genuine question | Markdown 3/29; questions 0/29 |

**D4. Blog bar**

| Dimension | Measurable rule | Today |
|---|---|---|
| Length | 900–1,500 words, capped at about 40 words per usable fact | A&H: ~1,000 words on ~3 on-topic facts |
| Fidelity | 0 hard unsupported claims; at most 1 soft background claim per 300 words, each traceable to a place card | 48 flags across 5 A&H blogs |
| SEO | Title 45–60 characters with keyword and city; meta 140–155 characters, one complete sentence, not shared with other pieces; H1 present; keyword in the first 100 words and in at least 1 H2 | A&H titles 21 characters; Thimphu missing; no H1 |
| FAQ | 3–5 questions, each answer adding a fact not in the body (Jev `faq_restates` <0.6) | Several ≥0.83 |
| CTA | Before `## FAQ`, written as "we", appears once | 7/20 |
| Route fidelity | The order and direction of places follows the seed | "east to west" in 10/10 A&H blogs |
| Brand themes | Per-tenant checklist (Terra: pace, rest, safety, food, the children's view; A&H: private guiding, stays, privacy; Trail: group, food, active verbs) | Terra safety 1/10; A&H guiding 2/10 |
| Structure (warning only) | 4–7 H2s; one section clearly the deepest; at most 1 list | F3 already measures this, with no effect on readers |

---

## E. Prioritized fixes and expected effect

The expected effects are my estimates. Each one should be confirmed by re-running the golden set.

| # | Fix | Effort | Addresses | Expected effect |
|---|---|---|---|---|
| **P0-1** | **Brand pack everywhere.** Send `core_idea`, voice examples, forbidden words, good examples, style guide and `brand_type` to both T8 and T9. Compile a per-tenant rubric at T0 intake into `system_prompt`, so F9 and Jev stop falling back to the AA rubric. Block T9 for any tenant whose rubric is still the fallback. Remove "Adventure Asia (AA)", "AA positioning", "quan điểm AA" and "premium" from `acp_angle_gate/prompts.py`, `goals.py`, `channel_style.py` and `acp_content_writing/prompts.py`, and translate the Vietnamese text the writer receives. | M | C2, C7, C8 | Terra LinkedIn and Trail brand voice rise from 5.2–5.6 toward the blog level (~7.3). F9_brand_style and Jev brand voice become meaningful (today r=0.11). |
| **P0-2** | **Angle contract check.** Regenerate any angle that (a) breaks a tenant "Avoid" rule, or (b) names a concrete object, scene, number or form of access that is not in the seed. | M | C1, C2 | Removes the brief-driven violations in 29/49 pieces (school trip, exclusivity, transformation) and the invented map and weaver scenes (9/10 and 7/10). |
| **P0-3** | **Deterministic fatal gates.** Raise blog `max_tokens` to ≥4,096 and retry when the model hits the limit; add a completeness gate; add a brand-name gate (only the tenant's name, catching "At <Proper Noun>, we", other tenant names and AA expansions); strip markdown from LinkedIn. Replace SEO truncation with a small call that regenerates only the title and meta (title ≥45 characters including keyword and city; never cut mid-phrase). | S–M | C6, C7 | Truncated blogs 5/20 → 0. Stub titles 5/5 → 0. Cut-off metas 2/10 → 0. Brand-name leaks can no longer ship. |
| **P0-4** | **Place and scope in the seed.** The location line becomes a display name with city or region from the place data (fix Pawangka → "Pabongka/Pawangka Monastery, Lhasa, Tibet"). Filter the sibling lines to the same place, or mark them "other trips, never this trip". Pass a scope line ("covers Luang Prabang → Nong Khiaw; do not promise later legs") and gate that title and meta places are in the seed. Facts only for the seed's country. | M | C3 | Removes 3 of the 4 reject causes and the scope errors (Terra "to Hanoi" 10/10, A&H "east to west" 10/10). Brings back Thimphu and Lhasa as SEO keywords. |
| **P1-5** | **Place cards (the biggest lever).** For each place, 6–12 verified facts (city/region, altitude, era, what to see, typical visit length, practical and safety notes, naming sensitivities). Generate once, verify with Jev plus a human sample, store as platform Facts, and cite them. Background claims may come only from the card; this replaces the "widely known background" allowance from #671. Target ≥2.5 facts per 100 words. | L | C1, C4 | Pawangka LinkedIn moves from 0/12 light-edit toward the Trail Pulse level (4/6). Fidelity on those posts ~4.8 → ~6.8. F9 hold rate 80% → ~30–40%. Confirm with an A/B test on the same 5 briefs, thin seed vs place card. |
| **P1-6** | **Tie length to information.** Words per piece no more than ~40 times the number of usable facts. If the seed cannot support a channel's minimum, the slate does not offer that channel, or asks the tenant for more facts. | S | C1, C4 | Removes the padding where most invented claims sit (blog words 900+ in the A&H blogs). |
| **P1-7** | **Channel specs by brand type.** LinkedIn variants: advisor/B2B (A&H) and parent-trust (Terra); for youth brands such as Trail Pulse, LinkedIn is off by default in favour of Instagram, TikTok or Facebook. At most one sentence of brand positioning; hook rules; end on the CTA or a question. Blog: CTA before `## FAQ`, an H1, keyword and city in place, FAQ answers must add new facts. | M | C2, C6, C8 | Channel craft 5.8 → ≥7. Blog CTA in body 7/20 → 20/20. |
| **P1-8** | **Repair instead of hold.** For product-truth flags, repair at sentence level for up to 3 rounds, falling back to deleting the sentence and re-running the gates. Soften comparatives automatically ("among the most sacred…" → "a revered pilgrimage site"). Soft background claims ship with a visible "verify" note instead of a hold. | M | B2 | The "correct flag, wrong action" holds (#18, #26, #28, #38, #41) become approvals. Repair success 20% → ≥70%. |
| **P2-9** | **Reweight the gates.** F3 becomes a warning only. Drop or rebuild F8. F9_brand_style uses the tenant rubric plus current AI-tell examples (contrast frames, "There is a moment", "Here's the insight", "At <Brand>, we"), with a calibrated blocking threshold. Replace F7 with Jev `faq_restates`. `t10_cta_clear` checks that the CTA is in the last body paragraph. Cheap metrics (contrast-frame density, stock-phrase list, fact repetition, sentence length per brand, coverage of the brand's core themes) become warnings that feed the repair. | M | B4, C5 | Approval precision 33% → ≥70%. |
| **P2-10** | **Measurement loop.** Freeze these 49 pieces and their labels as golden set v1, adding WildKind and 2 more regions. Every T9 pull request reports the D1 metrics. Have humans label 15–20 pieces to measure the panel's reliability before calibrating Jev on these labels. | M | All | No more improvements that only make the gate pass (W6–W9: approvals rose while light-edit stayed at 1/7). |

**Expected trajectory (estimate):**
- After P0: rejects at 0%, light or as-is ~35–40%.
- After P1: ~60–70%, and approval precision ≥70%.
- After P2: reaches the D1 bar (≥80% light or as-is, ≥30% as-is).

**Decisions for the product owner**
1. Treat T9 as a drafting aid, not a sellable product, until the D1 bar is met.
2. Approve P0-1 to P0-4 now (small to medium code changes).
3. Fact policy: use verified place cards rather than "widely known background".
4. Decide which channels each brand type may use (LinkedIn for Trail Pulse or not).
5. Holds only for hard fails; everything else is repaired or flagged.

**What the UI build must show**
- **Scorecard:** a per-piece scorecard on the D2–D4 bar (hard fails in red, each scored dimension against its threshold), not gate codes.
- **Flagged sentences:**
  - each flagged sentence highlighted in the text, with the reason and the seed or place-card line it was checked against;
  - one-click actions: cut, rewrite the sentence, or "I verified this" (logged).
- **What the writer knew:** the seed, the place card, the brand pack and the angle brief, with a warning when the seed is thin or the brand rubric is still the fallback.
- **Previews:** a search-result preview (title and meta with character counts) and a LinkedIn mobile preview showing the 140-character fold.
- **Attempt history:** a diff between attempt 1 and attempt 2, and the hold reason in plain language.

---

## Caveats
- **The panel is 4 AI lenses, not human editors, and it makes its own factual errors.** One lens put Pawangka in Sikkim (#6) and another near Shigatse (#22); Pabongka is just north of Lhasa. 6 pieces split 2–2. Check the panel against a human sample before calibrating any threshold on these labels.
- **The sample is narrow.** It is 5 briefs × ~10 samples spread over 9 code versions: strong on variation within a brief, weak on breadth (3 tenants, 3 places, 2 channels, WildKind 0). The seed-density pattern rests on 5 briefs and is mixed up with tenant and channel; confirm it with the A/B test in P1-5.
- **Claim categories are hand-assigned.** The 127 claims were flagged by F9 and grouped by me: ~33% cultural generalisation, ~21% invented scene, ~14% trip promises, ~14% rhetoric, ~7% superlatives, ~5% social proof, ~5% wrong flags.
- **The seeds in `claims.json` were fetched with today's code.** The W1–W3 writers saw thinner seeds.

**Code references**
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_angle_gate/prompts.py:28` — "Adventure Asia (AA)" in the T8 system prompt
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_angle_gate/goals.py:60,67,82,89` — "AA" in the goal text sent to the writer
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_angle_gate/channel_style.py:36-38` — LinkedIn "premium positioning", "AA positioning"
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_angle_gate/brand_audience.py` — reads only segment and mindset
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_content_writing/prompts.py:142` — "a premium travel brand"; the FAQ-last rule; the #671 location rule
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_content_writing/generate.py:41` — `_MAX_TOKENS = 2048`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_content_writing/quality_gates.py` — F6 only checks that a CTA is configured; the GENERIC_AI_WORDING example; F9_brand_style does not block; the LinkedIn length band of 20–6,000 characters
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_produce/brand.py:54-98` — fallback to `AA_BRAND_IDENTITY_PROMPT`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/acp_content_writing/service.py` — `_fit_seo_meta` (#670), which calls `fit_seo_title` in `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/services/content_generation/seo_meta_utils.py:157`
- Data: `/home/nghiep/projects/AA-Ecosys/.tmp-session/s232/pieces_text.json`, `claims.json`, `jevinv_cmp.txt`