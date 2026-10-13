# T9 commercial quality panel, S234 round 4: 20 pieces vs S233 r1 and S234 r1–r3

**Input.** `.tmp-session/s234/pieces_r4.json`: 20 pieces across 6 cells, 4 tenants and 2 channels. Piece numbers are the 0-based index in that file. They do **not** match the numbering of earlier rounds.

| Brief | Tenant / channel | Pieces | Gate (`status`, `failed`) |
|---|---|---|---|
| Punakha Dzong (day 4) | A&H LinkedIn | #0, #8, #12 | #0 approved; #8 and #12 held (F9_cta_fact) |
| Punakha Dzong (day 4) | WildKind LinkedIn | #1, #9, #13 | 3 approved |
| Tiger's Nest (day 9) | Terra LinkedIn | #2, #7, #10 | 3 approved |
| Kuang Si Falls (day 2) | Trail Pulse LinkedIn | #3, #6, #11 | 3 approved |
| Mongolia days 3–14 | Terra blog | #4, #14, #16, #18 | #16 approved; #4, #14 and #18 held (F9) |
| Mongolia days 3–14 | A&H blog | #5, #15, #17, #19 | all 4 held: #5, #15 and #19 on F17_trip_fact; #17 on F9 + F13_repeat |

**Method.** Same as S233 r1 and S234 r1–r3:
- **4 lenses:** editor (E), tenant brand lead (B), channel specialist (C) and paying client (K). That gives 80 votes.
- **Verdict:** the majority of the 4 votes. A 2–2 tie takes the stricter label. An as-is vote counts toward light-or-better. A piece is as-is only with ≥3 as-is votes.
- **Light edit:** ≤10 minutes, ≤3 sentences changed and no fact research. **Publish as-is:** a paying tenant would post the piece unchanged.
- **Scores:** 7 dimensions plus overall, each /10. A piece's overall is the mean of the 4 lenses.
- **Fidelity audit:** a separate auditor checked every claim against the seed, the "Place background" lines and the brand pack. Its /10 score is reported apart from the mean of the lens fidelity scores.
- **Hard errors:** deterministic. All five sets were re-measured with one script, `measure_r4.py`, against AA-CIS-App main 20a2387. Its totals differ a little from the earlier reports, which used older scripts (S233 r1 shows 70 core errors here). Compare rounds with §1.5 only.

**Caveat.**
- S233 r1 was **one rater simulating 4 lenses**. All four S234 rounds used **4 independent agents**, one per lens, plus a separate fidelity auditor.
  - Independent raters disagree more. That produces more 2–2 ties and so more strict labels (4 ties this round). On the other hand, the raters do not anchor on each other.
  - Compare S233 with S234 directionally, not to the decimal.
- Each S234 round used different agent instances on different pieces. Read changes of about ±0.2 in overall, or ±1 piece in a cell, as noise.
- The LinkedIn pieces in r4 carry no SEO title and no meta. Every LinkedIn piece is the same, so this is probably by design. The lenses did not score it.
- Two lens complaints are probably noise:
  - **Ulaanbaatar.** It is in the seed's Mörön-airport fact. The FAQ mentions are therefore grounded. The **body comparison** in #15 ("distinct from Ulaanbaatar") is not grounded.
  - **"Talk to an Atlas & Hearth travel designer…".** The fidelity auditor flagged this as a service promise. It is the tenant's configured CTA line (`check_cta_ok` passes 20/20), so it is a tenant-config question, not a writer error.

---

## 0. Bottom line

1. **Still not commercial-grade.** The mean score is the best yet, but the light share fell slightly.
   - Results: 0/20 publish as-is, 11 light edit (55%), 9 heavy edit (45%), 0 reject. The r3 split was 0/60/40/0.
   - Overall is **5.74** (r3 5.64, r2 5.57, r1 5.52, S233 5.33). The best piece is #2 (Terra Tiger's Nest) at 6.62.
   - D1 bar: ≥80% as-is or light, and ≥30% as-is.
     - All pieces: 55% and 0%.
     - LinkedIn alone: 83% (10/12) and 0%.
   - **The first 2 as-is votes since S234 r2:** #2 (channel lens) and #3 (client lens).
2. **LinkedIn holds at 10/12 light.** The cells moved:
   - **Terra Tiger's Nest is 3/3 light and 100% of its votes are light.** It is the best cell (6.31). This brand–seed pair is the closest to as-is.
   - A&H Punakha is 3/3 light (92% light votes). WildKind Punakha is 3/3 light, but its overall dropped to 5.73.
   - **Trail Pulse regressed to 1/3.** #6 (105 words) and #11 (113 words) are below the 120-word band, and both use the S233 staccato template ("That's not filler. That's structure.", "That is not a backdrop."). Both are 2–2 ties that went heavy.
3. **Blogs: 1/8 light (#15), down from 2/8.** The overall rose to 5.46 (r3 5.22), so the blogs are better written but not yet good enough to pass.
   - **The anchor-weight fix worked.** The thin monastery moment is now 1 mention per blog, with no own H2 in 8/8 (r3: over-weighted in 6/8). Only #17 (used as the climax) and #19 (placed in the wrong spot) still misuse it.
   - **Khatgal is gone** (r3: 3/8 FAQs).
   - **What now decides the heavy blogs:**
     - **Repair and FAQ integrity:** an orphan sentence in #16, FAQ non-answers in #5, #17 and #19, and a split paragraph in #18.
     - **"Optional" flipped:** #5, #14 and #17 present the boat as included, and #18 makes the Tsaatan day optional.
     - **Invented pace or product promises:** #14, #16 and #18.
4. **Hygiene is close to done.** Core hard errors fell from 70 (S233) to 11, 10, 8 and now **4**. Clean pieces: **18/20**; LinkedIn 12/12 clean.
   - All 4 errors are repeats, in the held blogs #17 and #19.
   - The extended total fell to 5 (r3: 18).
   - Two misses remain:
     - **#10's hashtag typo "#PaaTaktsang"**, which all 4 lenses flagged.
     - The two short Trail Pulse posts. The word band is not blocking.
5. **AI-tells improved again but are still the ceiling** (4.75; r3 4.60, S233 4.45).
   - 0/20 pieces score ≥7.
   - Contrast frames or stock lines appear in 17/20 pieces.
   - Four S233 stock lines are back: "worth sitting with" (#14), "worth pausing on" (#5), "That's not filler" (#6) and "That is not a backdrop" (#11).
6. **Fidelity is up.** The lens mean is 6.53 (r3 5.99) and the audit is 7.47 (r3 7.38). LinkedIn's audit score is 8.04. The remaining fidelity problems are interpretive:
   - Invented siting intent in 5/6 Punakha posts.
   - "Optional" flips and invented trip details in the blogs.
7. **The gate holds blogs well but now makes mistakes in both directions.**
   - The approval rate is 55% (11/20). Precision is 73% (8/11; r3 77%). Recall is 73% (8/11; r3 83%). The gate and the panel agree on 14/20 pieces (r3: 15/20).
   - **3 false passes:**
     - The two Trail Pulse ties (#6, #11). There is no voice gate and no length gate.
     - #16, a Terra blog with an orphan repair sentence, superlatives and a pace promise.
   - **3 false holds:** #8, #12 and #15. The flags are on sentences that are partly real, but each piece is light.

**Decision.**
- **LinkedIn:** ship Terra Tiger's Nest, A&H Punakha and WildKind Punakha with a light human pass. All three are 3/3 light.
  - First fix #10's hashtag.
  - Remove the "travel designer" CTA if A&H does not offer that service.
  - Hold Trail Pulse until the length floor and the stock-line fixes land.
- **Blogs: do not ship.** The structural fixes landed: anchor weight, FAQ count and scope. What is left is repair integrity and product truth ("optional"), and both are now mechanical to catch.

---

## 1. Commercial verdict

### 1.1 Overall

| | Publish as-is | Light edit | Heavy edit | Reject |
|---|---|---|---|---|
| Pieces (n=20) | 0 (0%) | 11 (55%) | 9 (45%) | 0 (0%) |
| Lens votes (n=80) | 2.5% (2) | 62.5% (50) | 35% (28) | 0% (0) |

Four pieces split 2–2 and took the stricter label:
- #4: E H, B H, C L, K L → heavy
- #6: E H, B L, C H, K L → heavy
- #11: E H, B H, C L, K L → heavy
- #18: E H, B L, C H, K L → heavy

If ties counted as light, LinkedIn would be 12/12 and blogs 3/8.

### 1.2 By channel and tenant

| Cell | n | Approved | Approved: L/H/R | Held: L/H/R | Light votes | Overall /10 |
|---|---|---|---|---|---|---|
| Terra LinkedIn (Tiger's Nest) | 3 | 3 | 3/0/0 | – | 100% | 6.31 |
| A&H LinkedIn (Punakha) | 3 | 1 | 1/0/0 | 2/0/0 | 92% | 6.06 |
| WildKind LinkedIn (Punakha) | 3 | 3 | 3/0/0 | – | 92% | 5.73 |
| Trail Pulse LinkedIn (Kuang Si) | 3 | 3 | 1/2/0 | – | 67% | 5.64 |
| Terra blog (Mongolia) | 4 | 1 | 0/1/0 | 0/3/0 | 31% | 5.62 |
| A&H blog (Mongolia) | 4 | 0 | – | 1/3/0 | 31% | 5.29 |
| **LinkedIn** | 12 | 10 | 8/2/0 | 2/0/0 | 88% | 5.93 |
| **Blog** | 8 | 1 | 0/1/0 | 1/6/0 | 31% | 5.46 |
| **All** | 20 | 11 (55%) | 8/3/0 | 3/6/0 | 65% | 5.74 |

"Light votes" counts as-is and light votes together. The 2 as-is votes are in Terra LinkedIn (#2) and Trail Pulse LinkedIn (#3).

By tenant, with both channels pooled. Brackets show S234 r3, r2, r1 and S233 r1, in that order.

| Tenant | Light | Overall |
|---|---|---|
| WildKind | 3/3 (3/3, 3/3, 3/3, 1/3) | 5.73 (6.06, 6.15, 6.12, 5.80) |
| Terra | 3/7 (3/7, 3/7, 3/7, 3/7) | **5.91** (5.47, 5.60, 5.25, 5.50) |
| A&H | 4/7 (4/7, 3/7, 3/7, 2/7) | 5.62 (5.61, 5.41, 5.67, 5.13) |
| Trail Pulse | **1/3** (2/3, 1/3, 2/3, 0/3) | 5.64 (5.67, 5.29, 5.18, 4.93) |

Dimension means (lens average), r4 with r3 in brackets:

| | All | LinkedIn | Blog |
|---|---|---|---|
| Fidelity (lens) | 6.53 (5.99) | 7.20 (6.66) | 5.53 (5.00) |
| Fidelity audit | 7.47 (7.38) | 8.04 (7.92) | 6.62 (6.56) |
| AI-tells | 4.75 (4.60) | 5.02 (4.98) | 4.34 (4.03) |

### 1.3 Per piece

| # | Cell | Gate | Votes E/B/C/K | Verdict | Overall | Fidelity audit | Deciding defects |
|---|---|---|---|---|---|---|---|
| 2 | Terra LI | approved | L L **A** L | Light | 6.62 | 9.0 | The camera/dress rule appears in the hook and again in paragraph 2; "honest expectations rather than optimism"; children's experience absent; the herbal hot stone bath from the seed is skipped |
| 0 | A&H LI | approved | L L L L | Light | 6.50 | 8.0 | Limp hook ("a choice of ground with meaning worth understanding"); "deliberate foundation" (siting intent); "The elaborateness is proportionate to the weight…"; no privacy or guiding cue |
| 3 | Trail LI | approved | L L L **A** | Light | 6.40 | 8.0 | Bear-rescue fact bolted onto the 50 m drop; filler "There's a lot happening before you even reach the water"; 2 contrast frames |
| 7 | Terra LI | approved | L L L L | Light | 6.38 | 7.0 | "isn't an inconvenience — it's the first sign" hook; "carefully restored"; "not rushing the ascent, building in rest" (invented pacing); "logistics already mapped" service promise |
| 8 | A&H LI | **held** (F9) | L L L L | Light | 6.22 | 6.0 | "narrow peninsula" contradicts the seed's "long"; "water on three sides", "single point of passage", "the dzong did not diminish" (inferred); "The annual return is institutional, not ceremonial sentiment."; 3–4 contrast frames |
| 15 | A&H blog | **held** (F17) | L L L L | Light | 6.15 | 7.0 | Best blog. "Those numbers carry weight. This is not simply…"; "does not perform for visitors. It simply continues."; Ulaanbaatar compared in the body; "home for generations"; "relative scarcity" interpretation in the FAQ |
| 10 | Terra LI | approved | L L L L | Light | 5.92 | 8.0 | **Hashtag typo "#PaaTaktsang"** (missed by the detector); "These aren't inconveniences — they're the shape of the place"; "restoration… returned it to use as… pilgrimage site" misframes the fact |
| 9 | WildKind LI | approved | L L L L | Light | 5.83 | 8.0 | "administrative" ×3 in 2 sentences; no habitat or nature angle; "relocate here each year" drops "in winter"; CTA "Day 4… wider journey" points out of scope |
| 13 | WildKind LI | approved | L L L L | Light | 5.83 | 9.0 | Flat date hook; the rivers are not named; a list paragraph (utse, relic, Rangjung Kharsapani); question plus ask in the CTA; off-core for WildKind |
| 1 | WildKind LI | approved | L H L L | Light | 5.53 | 7.0 | **Duplicated repair sentence** ("living religious seat" then "continues to function as a living religious institution"); "never an accident… considered foundation"; "travellers who read landscapes carefully before describing them" |
| 12 | A&H LI | **held** (F9) | H L L L | Light | 5.47 | 7.5 | **Garbled brand line** "where the context arrived with shapes everything encountered after"; "founding logic / founding geography" abstractions; "sacred relics" plural |
| 4 | Terra blog | held (F9) | H H L L | Heavy (tie) | 6.00 | 7.0 | Grammar error "Their number only a few hundred people"; invented rim walk and "first experience of camp life"; school framing ("intellectually compelling… children beginning to understand"); "facts that are hard to overstate" |
| 14 | Terra blog | held (F9) | H L H H | Heavy | 5.58 | 6.5 | **Boat presented as included** ("on foot, and by boat, and optionally on horseback"); "It is a number worth sitting with." (S233 tell); invented "not a technical climb" and pace promise; angle printed as an H2; only 3 FAQs |
| 18 | Terra blog | held (F9) | H L H L | Heavy (tie) | 5.55 | 6.5 | Split-paragraph repair artifact at Mörön; **Tsaatan day called "optional"** (the seed makes it a day-5 moment); invented Mörön town tour and "children can see the line between worlds"; one-line CTA; 3 FAQs |
| 16 | Terra blog | **approved** | H H H H | Heavy | 5.35 | 6.5 | **Orphan "Access requires a multi-hour horse or reindeer ride"** opens the Tsaatan section; superlatives "one of the most coherent and varied family itineraries", "unlike almost anything else on earth"; "changes at the waterline" contradicts "transition zone"; "full without being relentless" |
| 6 | Trail LI | **approved** | H L H L | Heavy (tie) | 5.30 | 9.5 | **105 words** (below the 120-word band); "That's not filler. That's structure." (S233 tell); a generic consultancy hook with no place in it |
| 19 | A&H blog | held (F17) | H L H H | Heavy | 5.28 | 6.5 | **Monastery placed in "the lake region"**; FAQ "What do the Tsaatan use their reindeer for?" not answered; "landscape has not entirely settled" implies volcanic risk; "a significant fraction" for 0.4%; 2 repeats (hard error) |
| 11 | Trail LI | **approved** | H H L L | Heavy (tie) | 5.22 | 9.5 | **113 words**; "That is not a backdrop. That is where…" plus "That kind of sequencing is deliberate."; flat, formal voice; swim and rest said twice |
| 5 | A&H blog | held (F17) | H H H H | Heavy | 5.03 | 6.5 | **Boat and trekking presented as included**, with only horse riding optional; **FAQ Q1 "Who are the Tsaatan?" not answered**; "zero point four percent", "sixteen hundred and forty-five metres"; "continues, in principle, to the Arctic"; ger upgraded to "well-made shelter" |
| 17 | A&H blog | held (F9, F13) | H H H H | Heavy | 4.70 | 6.5 | **Monastery made the closing beat** ("The journey closes with a single, sobering counterpoint"); "convergence" ×~6; "active feature of the deep past"; "tolerates them" repels a luxury buyer; weather FAQ truncated; boat implied included; 2 repeats (hard error) |

### 1.4 S233 r1 vs S234 r1–r4

| Metric | S233 r1 | S234 r1 | S234 r2 | S234 r3 | **S234 r4** | r3 → r4 |
|---|---|---|---|---|---|---|
| Publish as-is | 0% | 0% | 0% | 0% | **0%** | = |
| Light edit | 30% | 55% | 50% | 60% | **55%** | −5 pp |
| Heavy edit | 70% | 40% | 50% | 40% | **45%** | +5 pp |
| Reject | 0% | 5% | 0% | 0% | **0%** | = |
| As-is + light (D1 bar ≥80%) | 30% | 55% | 50% | 60% | **55%** | −5 pp |
| Light votes (including as-is) | 35% | 57% | 51% | 69% | **65%** | −4 pp |
| As-is votes | 0 | 1 | 1 | 0 | **2** | +2 |
| 2–2 ties (to heavy) | 5 | – | – | 3 | **4** | +1 |
| Overall /10 | 5.33 | 5.52 | 5.57 | 5.64 | **5.74** | +0.10 |
| Best piece | 6.2 | 6.5 | 6.28 | 6.60 | **6.62** | +0.02 |
| LinkedIn / blog overall | 5.64 / 4.86 | 5.88 / 4.97 | 5.85 / 5.16 | 5.91 / 5.22 | **5.93 / 5.46** | +0.02 / +0.24 |
| Fidelity (lens mean) | 5.80 | 5.89 | 5.85 | 5.99 | **6.53** | +0.54 |
| Fidelity, LinkedIn / blog | 6.62 / 4.56 | 6.44 / 5.08 | 6.41 / 5.02 | 6.66 / 5.00 | **7.20 / 5.53** | +0.54 / +0.53 |
| Fidelity audit | – | 7.10 (LI 7.67, blog 6.25) | 7.08 (LI 7.50, blog 6.44) | 7.38 (LI 7.92, blog 6.56) | **7.47 (LI 8.04, blog 6.62)** | +0.09 |
| Pieces with lens fidelity ≥7 | 6/20 | – | 4/20 | 4/20 | **8/20** | +4 |
| AI-tells | 4.45 | 4.54 | 4.45 | 4.60 | **4.75** (LI 5.02, blog 4.34) | +0.15 |
| Pieces with AI-tells ≥7 | 0/20 | 0/20 | 0/20 | 0/20 | **0/20** | = |
| Gate approval rate | 60% (12/20) | 85% (17/20) | 50% (10/20) | 65% (13/20) | **55% (11/20)** | −10 pp |
| Approval precision (approved pieces that are as-is or light) | 42% (5/12) | 59% (10/17) | 80% (8/10) | 77% (10/13) | **73% (8/11)** | −4 pp |
| Light-edit recall | 83% (5/6) | 91% (10/11) | 80% (8/10) | 83% (10/12) | **73% (8/11)** | −10 pp |
| Gate–panel agreement | 12/20 | 12/20 | 16/20 | 15/20 | **14/20** | −1 |
| "Hold everything" agreement | 14/20 | 9/20 | 10/20 | 8/20 | **9/20** | +1 |
| False passes (approved but heavy) | 7 | 7 | 2 | 3 | **3** (#6, #11, #16) | = |
| Blog false passes | 2 | 6 | 0 | 2 | **1** (#16) | −1 |
| False holds (held but light) | 1 | 1 | 2 | 2 | **3** (#8, #12, #15) | +1 |
| LinkedIn light (pieces) | 6/12 (50%) | 11/12 (92%) | 10/12 (83%) | 10/12 (83%) | **10/12 (83%)** | = |
| Blog light (pieces) | 0/8 | 0/8 | 0/8 | 2/8 (25%) | **1/8 (13%)** | −1 |
| Blog light votes | 6% | 16% | 0% | 34% | **31%** | −3 pp |
| Blogs with ≥3 FAQs | – | 2/8 | 1/8 | 8/8 | **8/8** (3 have exactly 3; 3 have a non-answer) | = |
| Blogs with the thin moment over-weighted | – | – | – | 6/8 | **2/8** (#17, #19) | −4 |
| Blogs with an out-of-scope place in the FAQ (Khatgal) | – | – | – | 3/8 | **0/8** | −3 |

### 1.5 Hard errors (deterministic, the same `measure_r4.py` on all five sets)

| Category | S233 r1 | S234 r1 | S234 r2 | S234 r3 | **S234 r4** |
|---|---|---|---|---|---|
| Scope in title / meta | 8 / 8 | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 0** |
| Scope in body | 21 | 2 | 0 | 0 | **0** |
| Leak ("content seed") | 2 | 0 | 0 | 0 | **0** |
| Social proof | 2 | 0 | 0 | 0 | **0** |
| Repeat | 15 | 7 | 10 | 7 | **4** (#17 ×2, #19 ×2) |
| Misspelt hashtag | 2 | 0 | 0 | 0 | **0** (but #10 "#PaaTaktsang" is missed) |
| LinkedIn >3 hashtags | 8 | 0 | 0 | 0 | **0** |
| LinkedIn first line >140 | 4 | 2 | 0 | 1 | **0** |
| Truncated / LinkedIn markdown | 0 | 0 | 0 | 0 | **0** |
| **Core total** | **70** | **11** | **10** | **8** | **4** |
| Pieces clean (core) | 1/20 | 13/20 | 12/20 | 16/20 | **18/20** |
| LinkedIn clean / blog clean | 1/12 / 0/8 | 9/12 / 4/8 | 10/12 / 2/8 | 11/12 / 5/8 | **12/12 / 6/8** |
| Extended total (core + x_*) | 94 | 33 | 16 | 18 | **5** (+1 journey end, #17) |
| LinkedIn words in band (mean) | 1/12 (356) | 12/12 (194) | 11/12 (181) | 12/12 (184) | **10/12 (177)**; #6 = 105, #11 = 113 |
| `check_cta_ok` / CTA line present | 18 / 20 | 19 / 20 | 17 / 19 | 20 / 20 | **20 / 20** |
| Blog CTA before the FAQ | 8/8 | 6/8 | 7/8 | 8/8 | **8/8** |
| Info: rarity tripwire / trip-fact pieces | 6 / 5 | 3 / 8 | 5 / 13 | 5 / 9 | **4 / 3** |

**What the detector misses.** It counts 4 core errors on 2 pieces, but 9 pieces are heavy. The visible defects that decide them are mostly not counted:
- **FAQ non-answers** (#5, #17, #19) and **repair orphans or splits** (#16, #18). These are not exact repeats, so the repeat check does not see them.
- **The paraphrased duplicate sentence in #1** ("living religious seat" / "living religious institution").
- **"Optional" flipped** (#5, #14, #17, #18). This is a product-truth error. F9/F17 held these pieces, but F9/F17 did not fire on #16's invented pace and town-visit claims.
- **The #10 hashtag typo**, which `hashtag_misspelt` does not see.
- **Under-length LinkedIn** (#6, #11). This is reported but not blocking.
- **Grammar breaks:** #4 "Their number only…" and #12 "the context arrived with shapes…".

---

## 2. Top remaining defect classes

| # | Defect class | Pieces | Count | Detected today? |
|---|---|---|---|---|
| 1 | **Contrast frames and stock AI lines.** S233 tells are back: "That's not filler. That's structure." (#6), "That is not a backdrop" (#11), "It is a number worth sitting with" (#14), "worth pausing on" (#5). Also "isn't an inconvenience — it's the first sign" (#7), "These aren't inconveniences — they're…" (#10), "does not perform for visitors" (#15), "tolerates them" (#17), "not simply seen" (#8) and "not a site frozen for visitors" (#1). "is not" or "not a" appears up to 4× in the blogs. | all except #2, #4, #13 | 17/20 | No (AI-tells 4.75; 0/20 ≥7) |
| 2 | **Repair and FAQ integrity.** FAQ answer does not answer its question (#5 Q1, #19 Q5, #17 weather); orphan sentence (#16 "Access requires…"); split paragraph (#18); paraphrased duplicate (#1); grammar breaks (#4, #12) | #1, #4, #5, #12, #16, #17, #18, #19 | 8/20 (6/8 blogs) | Partly (F13 and repeat catch only #17 and #19's exact fact repeats; **#16 approved**) |
| 3 | **Product truth: "optional" flipped, trip details invented.** Boat or trekking presented as included (#5, #14, #17); Tsaatan day made optional (#18); invented rim walk and "first experience of camp life" (#4, #16); Mörön town tour or lunch "at" Mörön when the seed says near it (#4, #5, #14, #15, #16, #18, #19); pace promises "full without being relentless" and "without… exhaustion" (#14, #16); "not rushing the ascent, building in rest" (#7) | 8/8 blogs plus #7 | 9/20 | Partly (F9/F17 held 7/8 blogs; missed #16 and #7) |
| 4 | **Invented siting intent and abstract interpretation (Punakha).** "deliberate foundation", "never an accident", "a considered act of founding logic", "founding argument, not a scenic preference", "geography and governance as inseparable"; "narrow peninsula" (the seed says long), "water on three sides", "single point of passage" | #0, #1, #8, #9, #12 | 5/6 Punakha posts | Partly (F9 held #8 and #12; #0, #1 and #9 approved) |
| 5 | **Tenant voice miss.** Trail Pulse is calm, formal and thin, not energetic or social (#6, #11). WildKind is architecture-led with no habitat (#1, #9, #13). Terra uses school framing (#4, #16) or leaves the child out (#2). A&H: "tolerates them" repels a comfort-seeking buyer (#17). | #1, #2, #4, #6, #9, #11, #13, #16, #17 | 9/20 | No (Trail Pulse false passes again: #6, #11) |
| 6 | **Under-length Trail Pulse LinkedIn.** 105 and 113 words, each with 1–2 facts, although unused seed material is available (the bear centre, the 50 m drop) | #6, #11 | 2/3 Trail Pulse | Reported, not blocking. **New regression in r4.** |
| 7 | **Overclaims, superlatives and number handling.** "one of the most coherent and varied family itineraries" and "unlike almost anything else on earth" (#16); "a landscape most of the world has never considered" (#17); "a significant fraction" for 0.4% (#19); "facts that are hard to overstate" (#4); spelled-out numbers ("zero point four percent", "sixteen hundred and forty-five metres") (#5, #17); "volcanic craters" in the plural in the meta (#14, #17) | #4, #5, #14, #16, #17, #19 | 6/8 blogs | Partly (novel word-numbers are info only, on 2 pieces; rarity tripwire on 4 pieces, all mild "most visitors") |
| 8 | **Thin moment and geography misplacement.** The monastery is the closing beat (#17, journey-end hard error) or placed in "the lake region" (#19); "the world changes at the waterline" contradicts "transition zone" (#16); taiga "continues… to the Arctic" (#5); Ulaanbaatar compared in the body (#15); a "landscape has not entirely settled" volcanic-risk implication (#19) | #5, #15, #16, #17, #19 | 5/8 blogs (thin moment 2/8, r3 6/8) | Partly (x_journey_end on #17; the gazetteer misses "Arctic") |
| 9 | **Place-name hashtag typo.** "#PaaTaktsang" (the S233 "#PajoTaktsang" class) | #10 | 1 | **No** (`hashtag_misspelt` = 0) |
| 10 | **Thin blog CTA and FAQ.** One-line CTA (#18); exactly 3 FAQs (#14, #18); the angle name printed as an H2 ("…as Mongolia's Family Anchor") (#14, #18) | #14, #18 | 2/4 Terra blogs | No |

**Changes since r3.**
- Gone or much reduced:
  - Thin-moment over-weighting: 6/8 → 2/8.
  - Khatgal and FAQ scope: 3/8 → 0/8.
  - Formatting artifacts (leading spaces, blank lines): 5 → 0.
  - Seed-note leaks: 2 → 0.
  - Meta fact errors: none deciding this round.
  - Core hard errors: 8 → 4.
- New or worse:
  - FAQ non-answers (a new defect class, 3/8 blogs).
  - "Optional" flipped in both directions (4 blogs).
  - Under-length Trail Pulse posts (2).
  - The return of four S233 stock lines.

## 3. Gate behaviour

- **Approved but heavy (3):**
  - **#16 (Terra blog).** An orphan repair sentence opens the Tsaatan section, plus superlatives, a pace promise and a "changes at the waterline" contradiction. F9/F17 did not fire, and the repeat check does not see orphans. This is the round's only blog false pass (r3: 2).
  - **#6 and #11 (Trail Pulse LinkedIn, both 2–2 ties).** Both are below the word band, use S233 staccato tells and have a flat voice. Trail Pulse has been a false-pass cell in every round, because there is still no voice gate, and the word band is info only.
- **Held but light (3):**
  - **#8 (A&H LinkedIn, F9).** The fidelity audit confirms real inferred claims ("narrow", "water on three sides", "single point of passage"). The flag is right, but 2–3 sentence edits fix it.
  - **#12 (A&H LinkedIn, F9).** It is light, but the garbled brand line has to be fixed.
  - **#15 (A&H blog, F17).** This is the best blog. The info trip-fact is "closes on a thin moment with added interpretation". It is a one-sentence fix.

  All three are correct flags with the wrong action. Sentence-level repair (AA-769) would turn them into approvals.
- **Held and heavy (6), correct holds:** #4, #5, #14, #17, #18 and #19. **The gate holds 7/8 blogs, and 6 of those holds are right.**
- **Split by channel:**
  - Blogs: precision 0/1 and recall 0/1. The gate holds almost every blog, which is right this round.
  - LinkedIn: precision 8/10, and 2 light pieces held.

## 4. Next fixes, ranked

| Rank | Fix | Targets (class) | Expected effect |
|---|---|---|---|
| 1 | **FAQ and repair integrity, fail closed.** (a) Every FAQ answer must contain the subject of its question (an entity or keyword overlap check); otherwise regenerate that answer. (b) After any repair, check for a sentence that opens a section with no subject or antecedent ("Access requires…"), a paragraph split mid-thought, and **paraphrased** duplicates (normalised token overlap, not exact match). (c) Run a grammar sanity pass on repaired sentences. | 2 | 6/8 blogs plus #1. Would have held #16, the only blog false pass, and removes a deciding defect from #5, #17, #18 and #19. |
| 2 | **Product-truth check for "optional".** Carry each seed moment's optional flag through to the writer and validate it after writing. An optional activity must not be written as included, and an included one must not be called optional. Also catch "lunch at X" when the seed says near, and invented sub-activities (a rim walk). Make pace or difficulty promises ("not a technical climb", "without exhaustion", "full without being relentless") blocking unless the seed has them. | 3 | All 8 blogs plus #7. Turns the current F9/F17 holds into targeted repairs and closes #16's miss. |
| 3 | **A LinkedIn length floor that blocks, plus a Trail Pulse voice rubric.** Below 120 words → regenerate with more seed facts (the bear centre and the 50 m drop are unused). Voice check: energetic and social, contractions, no consultancy maxims. | 5, 6 | Removes both LinkedIn false passes (#6, #11) and takes LinkedIn to 12/12 light. Trail Pulse has been a false-pass cell in every round. |
| 4 | **Stock-line blocklist plus contrast-frame density (open since S233).** Add the returning tells as blocking patterns: "not filler", "worth sitting with", "worth pausing on", "That is not a backdrop", "does not perform", "tolerates them", "isn't an inconvenience". Cap contrast frames at 1 per 150 words. Check n-gram overlap with sibling pieces (#5, #17 and #19 share an opener). | 1 | 17/20 pieces. Still the only route to as-is: 0/20 pieces score AI-tells ≥7, and there were only 2 as-is votes in r4. |
| 5 | **Siting-intent and interpretation guard for place facts.** Words such as deliberate, considered, chose, never an accident, founding argument, "inseparable" and "symbolic weight" need a seed fact that states intent. Block any adjective that contradicts the seed (narrow vs long) and any geometry the seed does not give ("three sides", "single point of passage"). | 4 | 5/6 Punakha posts. Moves A&H and WildKind LinkedIn from light toward as-is. It also clears the F9 holds on #8 and #12. |
| 6 | **Hashtag spelling check against seed place names.** Fuzzy-match each hashtag against the seed's names and aliases. A near-miss that is not an exact match is a hard error. | 9 | #10. The `hashtag_misspelt` detector does not catch it. Cheap and deterministic. |
| 7 | **Normaliser and overclaim list.** Write numbers as digits when the seed has digits. No plural when the seed has a single item ("volcanic craters"). Add the superlative patterns ("one of the most… available", "unlike almost anything on earth", "most of the world has never…", "significant fraction") to the rarity detector as blocking on blogs. | 7 | 6/8 blogs. Mechanical. |
| 8 | **Sentence-level repair on correct F9/F17 flags (AA-769).** Rewrite the flagged sentence instead of holding the piece. | gate | Converts #8, #12 and #15 into approvals. Recall goes from 73% to 100%, and blogs reach 1/8 approved-and-light for the first time. |
| 9 | **Geography guard for blogs.** The gazetteer should flag regions that are not in the seed ("Arctic"). Block body comparisons that use places the seed only mentions in passing (#15 Ulaanbaatar). The thin moment must not be the closing beat or be given a location (#17, #19). Require ≥4 FAQs and a CTA of at least 2 sentences on blogs. | 8, 10 | 5/8 blogs. Finishes the anchor-weight work that landed in r4. |

Fixes 1–2 are what the blogs need to cross into light. 4 of the 7 heavy blogs (#4, #14, #18, #19) are one or two of those defects away, and #4 and #18 missed light only on 2–2 ties. Fix 3 is the cheapest win: it closes both LinkedIn false passes. Fix 4 is still the only lever for the ≥30% as-is bar on either channel.

---

*Scratch: `panel/r4/synth_r4.py` (vote tally, cell, tenant and gate metrics). Hard errors: `panel/measure_r4_s234r4.json`, `measure_r4_s234r3.json`, `measure_r4_s234r2.json`, `measure_r4_s234r1.json` and `measure_r4_s233r1.json`. Fidelity audit: `panel/fidelity_r4.json`.*
