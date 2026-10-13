# T9 commercial quality panel, S234 round 3: 20 pieces vs S233 r1, S234 r1 and S234 r2

**Input.** `.tmp-session/s234/pieces_r3.json`: 20 pieces across 6 cells, 4 tenants and 2 channels. Piece numbers are the 0-based index in that file. They do **not** match the r1 or r2 numbering.

| Brief | Tenant / channel | Pieces | Gate (`status`, `failed`) |
|---|---|---|---|
| Punakha Dzong (day 4) | WildKind LinkedIn | #1, #6, #10 | 3 approved |
| Punakha Dzong (day 4) | A&H LinkedIn | #2, #7, #13 | 3 approved |
| Tiger's Nest (day 9) | Terra LinkedIn | #3, #8, #11 | #11 approved; #3 held (F14_first_line); #8 held (F17_trip_fact) |
| Kuang Si Falls (day 2) | Trail Pulse LinkedIn | #5, #9, #15 | 3 approved |
| Mongolia days 3–14 | A&H blog | #4, #12, #16, #18 | #16 and #18 approved; #4 and #12 held (F9_cta_fact) |
| Mongolia days 3–14 | Terra blog | #0, #14, #17, #19 | #19 approved; #0 and #14 held (F9); #17 held (F4_seo_surface + F9) |

**Method.** Same as S233, S234 r1 and S234 r2:
- **4 lenses:** editor (E), tenant brand lead (B), channel specialist (C) and paying client (K). That gives 80 votes.
- **Verdict:** the majority of the 4 votes. A 2–2 tie takes the stricter label.
- **Light edit:** ≤10 minutes, ≤3 sentences changed and no fact research. **Publish as-is:** a paying tenant would post the piece unchanged.
- **Scores:** 7 dimensions plus overall, each /10. A piece's overall is the mean of the 4 lenses.
- **Fidelity audit:** a separate auditor checked every claim against the seed, the "Place background" lines and the brand pack. Its /10 score is reported apart from the mean of the lens fidelity scores.
- **Hard errors:** deterministic. All four rounds were re-measured with the same script, `measure_r3.py`. It is the round-3 implementer's script plus simulated `trip_places`, and it reads the main e902a49 hygiene.

**Caveat.**
- S233 r1 was **one rater simulating 4 lenses**. All three S234 rounds used **4 independent agents**, one per lens, plus a separate fidelity auditor.
  - Independent raters disagree more. That produces more 2–2 ties and so more strict labels. On the other hand, the raters do not anchor on each other.
  - Compare S233 with S234 directionally, not to the decimal.
- Each S234 round used different agent instances on different pieces. Read changes of about ±0.2 in overall, or ±1 piece in a cell, as noise.
- The hard-error totals in this report come from `measure_r3.py`, so they do **not** match the totals in the r1 and r2 reports, which used `measure.py` and `measure_r2.py`.
  - The r3 repeat detector finds more repeats: S233 r1 has 68 core errors here vs 65 there, and S234 r2 has 7 here vs 2 there.
  - Compare rounds within this report only.
- The new `x_scope_trip_places` rule uses a **simulated** trip-place list. Its 7 hits in r3 are Ulaanbaatar ×6, which is in the seed's Mörön airport fact, and Thimphu ×1, which is in the seed's Je Khenpo fact. Treat them as rule noise, not as writer errors.

---

## 0. Bottom line

1. **Still not commercial-grade, but r3 is the best round so far on every headline number except as-is.**
   - Results: 0/20 publish as-is, 12 light edit (60%), 8 heavy edit (40%), 0 reject. The r2 split was 0/50/50/0.
   - Overall is 5.64 (r2 5.57, r1 5.52, S233 5.33). The best piece is #11 (Terra Tiger's Nest) at 6.60.
   - D1 bar: ≥80% as-is or light, and ≥30% as-is.
     - All pieces: 60% and 0%.
     - **LinkedIn alone: 83% (10/12) and 0%.**
   - There were **0 as-is votes out of 80** (r2: 1).
2. **Blogs moved for the first time: 2/8 light (#0, #18).** In S233 r1, S234 r1 and S234 r2, blogs were 0/8 light.
   - **The FAQ contract is fixed.** All 8 blogs have 3–5 FAQs (r2: 7/8 had fewer than 3). The CTA comes before the FAQ in 8/8.
   - Light votes on blogs went from 0% (r2) to 34%.
   - Blog lens fidelity is flat at 5.00. The blog fidelity audit rose from 6.44 to 6.56.
   - The deciding blog defects have changed:
     - The thin monastery moment (0 place facts) is over-weighted in 6/8 blogs: it gets its own H2 or is used as the climax.
     - Repair artifacts in 4/8: #19 has three duplicated sentences, #12 has a doubled CTA, #4 has a broken sentence, and #17 has an orphan sentence.
     - Invented trip details in 8/8. The worst is #14's "Sod Camp Base" as the lake base.
     - Storm risk is waved away in Terra family pieces (#0, #14).
3. **Hygiene is nearly done.** Core hard errors fell from 68 (S233) to 10 to 7 to **4**. Clean pieces went from 2 to 14 to 14 to **16/20**.
   - LinkedIn: all 12 posts are in the word band (mean 184), all have exactly 3 hashtags, and all have the CTA line.
   - `check_cta_ok` passes on 20/20 pieces (r2: 17/20).
   - The trip-fact detector fires on only 1 piece (r2: 12) and the rarity detector on 0 (r2: 8).
   - **But the detector misses the most visible defects:** #19's three duplicated sentences and #12's doubled CTA.
4. **AI-tells moved slightly but are still the ceiling** (4.60; r2 4.45, r1 4.54, S233 4.45).
   - 0/20 pieces score ≥7.
   - Contrast frames or stock lines appear in 19/20 pieces.
   - S233's "not an afterthought" is back (#15). "Not a monument" appears in 3 Punakha posts.
5. **The gate's error moved back to false passes.**
   - Approval rate 65% (13/20; r2 50%).
   - Precision 77% (10/13; r2 80%). Recall 83% (10/12; r2 80%).
   - Gate–panel agreement 15/20 (r2 16/20). Holding everything would agree on 8/20.
   - **2 blog false passes:**
     - #19 has three visible repair duplicates, school framing and a duplicated SEO title.
     - #16 names Khatgal in its FAQ (out of scope), and its meta is nonsense: "volcanic terrain shaped by centuries of culture".
   - These blogs pass now because F16 no longer holds them (the FAQs are fixed), and no other gate catches what is left.

**Decision.**
- **LinkedIn:** ship WildKind and A&H Punakha with a light human pass. Both are 3/3 light, 3/3 approved and 100% light votes. Terra and Trail Pulse are 2/3 light each.
- **Blogs: do not ship yet.** They are now within reach: 2/8 light, and #17 missed light only on a 2–2 tie.
- **Next fixes, in order:**
  1. Repair integrity, which would also hold #19.
  2. An anchor-weight rule for the thin moment.
  3. Trip and scope grounding for blogs, including the FAQ.
  4. Safety tone for family brands.

  Anti-template work remains the only route to as-is.

---

## 1. Commercial verdict

### 1.1 Overall

| | Publish as-is | Light edit | Heavy edit | Reject |
|---|---|---|---|---|
| Pieces (n=20) | 0 (0%) | 12 (60%) | 8 (40%) | 0 (0%) |
| Lens votes (n=80) | 0% (0) | 69% (55) | 31% (25) | 0% (0) |

Three pieces split 2–2 and took the stricter label:
- #3: E L, B H, C H, K L → heavy
- #9: E L, B H, C L, K H → heavy
- #17: E H, B L, C H, K L → heavy

If ties counted as light, LinkedIn would be 12/12 and blogs 3/8.

### 1.2 By channel and tenant

| Cell | n | Approved | Approved: L/H/R | Held: L/H/R | Light votes | Overall /10 |
|---|---|---|---|---|---|---|
| WildKind LinkedIn (Punakha) | 3 | 3 | 3/0/0 | – | 100% | 6.06 |
| A&H LinkedIn (Punakha) | 3 | 3 | 3/0/0 | – | 100% | 6.01 |
| Terra LinkedIn (Tiger's Nest) | 3 | 1 | 1/0/0 | 1/1/0 | 83% | 5.91 |
| Trail Pulse LinkedIn (Kuang Si) | 3 | 3 | 2/1/0 | – | 83% | 5.67 |
| A&H blog (Mongolia) | 4 | 2 | 1/1/0 | 0/2/0 | 31% | 5.31 |
| Terra blog (Mongolia) | 4 | 1 | 0/1/0 | 1/2/0 | 38% | 5.13 |
| **LinkedIn** | 12 | 10 | 9/1/0 | 1/1/0 | 92% | 5.91 |
| **Blog** | 8 | 3 | 1/2/0 | 1/4/0 | 34% | 5.22 |
| **All** | 20 | 13 (65%) | 10/3/0 | 2/5/0 | 69% | 5.64 |

"Light votes" counts as-is and light votes together. There were no as-is votes this round.

By tenant, with both channels pooled. Brackets show S234 r2, S234 r1 and S233 r1, in that order.

| Tenant | Light | Overall |
|---|---|---|
| WildKind | 3/3 (3/3, 3/3, 1/3) | 6.06 (6.15, 6.12, 5.80) |
| Trail Pulse | 2/3 (1/3, 2/3, 0/3) | 5.67 (5.29, 5.18, 4.93) |
| A&H | 4/7 (3/7, 3/7, 2/7) | 5.61 (5.41, 5.67, 5.13) |
| Terra | 3/7 (3/7, 3/7, 3/7) | 5.47 (5.60, 5.25, 5.50) |

### 1.3 Per piece

| # | Cell | Gate | Votes E/B/C/K | Verdict | Overall | Fidelity audit | Deciding defects |
|---|---|---|---|---|---|---|---|
| 11 | Terra LI | approved | L L L L | Light | 6.60 | 8.5 | "These aren't decorative details —" frame; the history paragraph is a list of dates. The best on-brand pacing line in the set. |
| 6 | WildKind LI | approved | L L L L | Light | 6.17 | 8.5 | **Meta missing**; gilded roofs moved from the temples to the assembly hall; "not a preserved monument"; heritage-led, no habitat |
| 1 | WildKind LI | approved | L L L L | Light | 6.15 | 9.0 | Flat geographic hook; "That history does not sit quietly."; meta implies an administrative role continues after 1955 |
| 2 | A&H LI | approved | L L L L | Light | 6.12 | 6.5 | **Meta "400-year legacy as Bhutan's capital"** (it was 318 years); invented "every valley had a defensible ridge"; aphorism close |
| 13 | A&H LI | approved | L L L L | Light | 6.10 | 8.0 | "The setting is part of the meaning."; speculative "a hilltop or a valley floor could not provide"; "narrow strip" (seed: long peninsula) |
| 8 | Terra LI | **held** (F17) | L L L L | Light | 6.05 | 7.5 | "in the morning" timing is invented, so F17 is right; written to parents only; clunky "checkpoint" hook |
| 15 | Trail LI | approved | L L L L | Light | 6.05 | 8.0 | "Not squeezed in. Planned in." and "not an afterthought" (S233 template); "Day 2" in the SEO title; no social energy |
| 10 | WildKind LI | approved | L L L L | Light | 5.85 | 9.0 | **No SEO title and no meta**; abstract hook "administrative, religious, and geographic"; "chose that site deliberately"; "along this route" |
| 5 | Trail LI | approved | L L L L | Light | 5.80 | 8.0 | "That's not coincidence. It's how pacing works"; corporate brand line; "the plan gives it to you" implies time for the viewpoint trail and the bear centre |
| 7 | A&H LI | approved | L L L L | Light | 5.80 | 7.0 | "fortress-monastery" twice in the opening; the "two named rivers" angle leaks into the copy; meta "winter residence since 1637"; "well over three centuries" |
| 18 | A&H blog | approved | H L L L | Light | 5.78 | 7.0 | "This boundary is not metaphor."; invented "quality of the silence" and nomads "close to the lakeshore"; stray leading spaces ×2; "considered access" in the CTA |
| 0 | Terra blog | **held** (F9) | H L L L | Light | 5.68 | 7.5 | **Storm hazard waved away** ("feel real rather than managed"); "a different kind of classroom"; "smallest distinct ethnic groups"; SEO title identical to #19 |
| 16 | A&H blog | **approved** | H H H L | Heavy | 5.30 | 7.0 | **Meta "volcanic terrain shaped by centuries of culture"**; Khatgal in the FAQ (out of scope); "## Day Fourteen" H2 for the thin moment; "That is not scenery. That is consequence." |
| 17 | Terra blog | held (F4, F9) | H L H L | Heavy (tie) | 5.30 | 5.5 | National-park sentence orphaned inside the Mörön section; invented "grassland on one side… boreal forest on the other"; "nothing about it is rushed"; recap repeat (hard error) |
| 12 | A&H blog | held (F9) | H H L H | Heavy | 5.20 | 6.5 | **Doubled CTA sentence**; repaired Tsaatan sentence duplicated; monastery used as the climax; "among the most… distinct journeys the region offers" |
| 9 | Trail LI | **approved** | L H L H | Heavy (tie) | 5.17 | 7.5 | Consultancy voice ("energy delivered sustainably, for presence across the full trip"); pacing point repeated across 2 paragraphs; falls get 1 paragraph |
| 3 | Terra LI | held (F14) | L H H L | Heavy (tie) | 5.08 | 7.5 | Leading blank lines and a 283-character first line (hard error); "the return takes… two to three hours each way"; no children; generic close |
| 4 | A&H blog | held (F9) | H H H H | Heavy | 4.97 | 7.0 | **Broken repair sentence** "They mean that this single body of water…"; numbers spelled out; blank lines; "Edge of the World" H2; Khatgal in the FAQ; monastery H2 |
| 19 | Terra blog | **approved** | H H H L | Heavy | 4.80 | 6.5 | **Three repair duplicates** (steppe/taiga, "register immediately", Sod Camp spring); "the landscape itself becomes a teaching tool"; Khatgal in the FAQ; SEO title identical to #0 |
| 14 | Terra blog | held (F9) | H H H H | Heavy | 4.75 | 5.5 | **H2 "The Sod Camp Base"** (Sod Camp is the day-3 stop, not the lake base); naming-note leak ("phonetic approximation… best avoided"); caldera trek "optional"; storms dismissed |

### 1.4 S233 r1 vs S234 r1 vs S234 r2 vs S234 r3

| Metric | S233 r1 | S234 r1 | S234 r2 | **S234 r3** | r2 → r3 |
|---|---|---|---|---|---|
| Publish as-is | 0% | 0% | 0% | **0%** | = |
| Light edit | 30% | 55% | 50% | **60%** | +10 pp |
| Heavy edit | 70% | 40% | 50% | **40%** | −10 pp |
| Reject | 0% | 5% | 0% | **0%** | = |
| As-is + light (D1 bar ≥80%) | 30% | 55% | 50% | **60%** | +10 pp |
| Light votes (including as-is) | 35% | 57% | 51% | **69%** | +18 pp |
| As-is votes | 0 | 1 | 1 | **0** | −1 |
| Overall /10 | 5.33 | 5.52 | 5.57 | **5.64** | +0.07 |
| Best piece | 6.2 | 6.5 | 6.28 | **6.60** | +0.32 |
| LinkedIn / blog overall | 5.64 / 4.86 | 5.88 / 4.97 | 5.85 / 5.16 | **5.91 / 5.22** | +0.06 / +0.06 |
| Fidelity (lens mean) | 5.80 | 5.89 | 5.85 | **5.99** | +0.14 |
| Fidelity, LinkedIn / blog | 6.62 / 4.56 | 6.44 / 5.08 | 6.41 / 5.02 | **6.66 / 5.00** | +0.25 / −0.02 |
| Fidelity audit | – | 7.10 (LI 7.67, blog 6.25) | 7.08 (LI 7.50, blog 6.44) | **7.38 (LI 7.92, blog 6.56)** | +0.30 |
| Pieces with lens fidelity ≥7 | 6/20 | – | 4/20 | **4/20** (#1, #5, #11, #15) | = |
| AI-tells | 4.45 | 4.54 | 4.45 | **4.60** (LI 4.98, blog 4.03) | +0.15 |
| Pieces with AI-tells ≥7 | 0/20 | 0/20 | 0/20 | **0/20** | = |
| Gate approval rate | 60% (12/20) | 85% (17/20) | 50% (10/20) | **65% (13/20)** | +15 pp |
| Approval precision (approved pieces that are as-is or light) | 42% (5/12) | 59% (10/17) | 80% (8/10) | **77% (10/13)** | −3 pp |
| Light-edit recall | 83% (5/6) | 91% (10/11) | 80% (8/10) | **83% (10/12)** | +3 pp |
| Gate–panel agreement | 12/20 | 12/20 | 16/20 | **15/20** | −1 |
| False passes (approved but heavy) | 7 | 7 | 2 | **3** (#9, #16, #19) | +1 |
| Blog false passes | 2 | 6 | 0 | **2** (#16, #19) | +2 |
| False holds (held but light) | 1 | 1 | 2 | **2** (#0, #8) | = |
| LinkedIn light (pieces) | 6/12 (50%) | 11/12 (92%) | 10/12 (83%) | **10/12 (83%)** | = |
| Blog light (pieces) | 0/8 | 0/8 | 0/8 | **2/8 (25%)** | **+2** |
| Blog light votes | 6% | 16% | 0% | **34%** | +34 pp |
| Blogs with ≥3 FAQs | – | 2/8 | 1/8 | **8/8** | +7 |

### 1.5 Hard errors (deterministic, same `measure_r3.py` on all four sets)

| Category | S233 r1 | S234 r1 | S234 r2 | S234 r3 |
|---|---|---|---|---|
| Scope in title / meta | 8 / 8 | 0 / 0 | 0 / 0 | 0 / 0 |
| Scope in body | 21 | 2 | 0 | 0 |
| Leak ("content seed") | 2 | 0 | 0 | 0 |
| Social proof | 2 | 0 | 0 | 1 (#18, "everyone who enters it", borderline) |
| Repeat | 13 | 6 | 7 | 2 (#12, #17 closing recaps) |
| Misspelt hashtag | 2 | 0 | 0 | 0 |
| LinkedIn >3 hashtags | 8 | 0 | 0 | 0 |
| LinkedIn first line >140 | 4 | 2 | 0 | 1 (#3, 283 characters) |
| Truncated / LinkedIn markdown | 0 | 0 | 0 | 0 |
| **Core total** | **68** | **10** | **7** | **4** (3 if #18 is excluded) |
| Pieces clean (core) | 2/20 | 14/20 | 14/20 | **16/20** |
| LinkedIn clean / blog clean | 2/12 / 0/8 | 10/12 / 4/8 | 11/12 / 3/8 | **11/12 / 5/8** |
| Extended (x_*) hits on top of core | 25 | 21 | 3 | 10 (7 are simulated trip-places noise; 3 are journey-end, and #4's is borderline) |
| LinkedIn words in band (mean) | 1/12 (356) | 12/12 (194) | 11/12 (181) | **12/12 (184)** |
| `check_cta_ok` / CTA line present | 18 / 20 | 19 / 20 | 17 / 19 | **20 / 20** |
| Info: trip-fact pieces / rarity pieces (r3 detectors) | 5 / 3 | 4 / 5 | 12 / 8 | **1 / 0** |

**What the detector misses.** It counts 4 core errors, but the visible defects that decide the heavy verdicts are mostly not counted:
- #19's three duplicated sentences and #12's doubled CTA. The CTA sentence is exempt from the repeat check, and paraphrased duplicates slip past it.
- #4's broken repair sentence.
- Khatgal in the FAQ of #4, #16 and #19. The FAQ is not scope-checked against the seed's SCOPE.
- Formatting artifacts: stray leading spaces (#18), blank lines after an H2 (#4) and trailing whitespace (#19).
- Duplicate SEO titles between sibling pieces (#0 = #19).
- A missing SEO title or meta on LinkedIn (#6, #10).

8 of the 16 clean pieces are still heavy or carry deciding defects. Hard errors no longer explain the verdicts. That was true in r2 and is more so now.

---

## 2. Top remaining defect classes

| # | Defect class | Pieces | Count | Detected today? |
|---|---|---|---|---|
| 1 | **Contrast frames and stock AI lines.** "not X, it is Y" ("That is not scenery. That is consequence.", "This boundary is not metaphor."), "not a monument" (#1, #6, #10), "not an afterthought" returns (#15), "That's not coincidence" (#5), aphorism closes ("The setting is part of the meaning.") | all except #8 | 19/20 | No (AI-tells 4.60; 0/20 ≥7) |
| 2 | **Invented trip, place or product details.** #14 Sod Camp as the lake base, caldera "optional", "longer drive north"; #17 shoreline split and "full day… nothing rushed"; #18 "quality of the silence", nomads by the shore; #16 "partnership… visible in how the community moves"; #0 "smallest distinct ethnic groups"; #12 "always lived at that convergence"; #19 "crossed from one ecosystem into another"; #2 "every valley had a defensible ridge"; #5 "the plan gives it to you"; #8 "in the morning"; #10/#13 siting intent | 8/8 blogs plus #2, #5, #8, #10, #13 | 13/20 | Partly (F9 held #0, #4, #12, #14, #17; F17 held #8; missed on #16, #18, #19 and the LinkedIn posts) |
| 3 | **Thin monastery moment over-weighted.** The anchor moment has 0 place facts but gets its own H2 (#0, #4, #14, #16 "Day Fourteen", #19) or is used as the climax or coda (#12, #16); unsupported extrapolation ("shaped… for generations", "northern Mongolia still carries") | #0, #4, #12, #14, #16, #19 (#18 handles it in one sentence) | 6/8 blogs | No |
| 4 | **Repair artifacts.** Three duplicated sentences (#19); doubled CTA from the CTA-literal restore plus a duplicated Tsaatan sentence (#12); broken "They mean that this single body of water…" (#4); orphan national-park sentence in the Mörön section (#17); garbled "return… each way" (#3) | #3, #4, #12, #17, #19 | 5 (4/8 blogs) | Partly (repeat catches the #12 and #17 recaps only; #19 is **approved**) |
| 5 | **Seed metadata wrong or missing on SEO surfaces.** Meta "400-year legacy as capital" (#2), "since 1637" (#7), "volcanic terrain shaped by centuries of culture" (#16), "Luang Prabang trek" (#9), "administrative… still in use" (#1); meta missing (#6), no title and no meta (#10); duplicate title #0 = #19; "Day 2" in the title (#15); title 65 characters (#17) | #0, #1, #2, #6, #7, #9, #10, #15, #16, #17, #19 | 11/20 | Partly (F4 held #17 only) |
| 6 | **Tenant voice miss.** Trail Pulse reads as a calm or corporate pacing essay with no social energy (#5, #9, #15). Terra uses classroom or school framing (#0, #19) or leaves children out (#3, #8). WildKind is architecture-led with no habitat (#1, #6, #10). | 10 pieces | 10/20 | No (no voice gate; Trail Pulse #9 is a false pass again) |
| 7 | **Out-of-scope or misplaced places.** Khatgal in the FAQ (#4, #16, #19); "plains / steppe journeys further south" (#0, #16); Uran Togoo "in Khövsgöl Province" (#4); national park around Mörön (#17); the ruins assigned to "northern Mongolia" (#12, #18) | #0, #4, #12, #16, #17, #18, #19 | 7/8 blogs | No (the FAQ is not scope-checked, and the trip-places rule flags Ulaanbaatar, which is in the seed, instead) |
| 8 | **Family safety tone.** Storm hazard downplayed against the seed's "potentially hazardous" (#0, #14); the multi-hour horse or reindeer ride to the Tsaatan pitched to children with no pacing or safety framing (#0, #19) | #0, #14, #19 | 3/4 Terra blogs | Partly (F9 held #0 and #14; #19 approved) |
| 9 | **Formatting artifacts.** Leading blank lines (#3), blank lines after an H2 (#4), stray leading spaces (#18), trailing whitespace (#19); numbers spelled out ("sixteen hundred and forty-five metres", "early nineteen-nineties") (#4, #16) | #3, #4, #16, #18, #19 | 5 | Partly (F14 caught #3's first line; novel word-numbers flagged on #16 as info only) |
| 10 | **Seed internal notes leaking into the copy.** Mörön naming note ("one phonetic approximation… best avoided") (#14); angle wording "two named rivers" (#7) | #7, #14 | 2 | No |
| 11 | **Self-superlatives and rarity drift.** "among the most intellectually and aesthetically distinct journeys" (#12); "a way of life that most of the world has never seen" (#17); "terrain that most family travel never reaches" (#0); "considered access" (#18, which breaks A&H's avoid list) | #0, #12, #17, #18 | 4/8 blogs (r2: 6/8) | No (r3 rarity detector: 0 pieces) |

**Changes since r2.**
- Gone: the FAQ shortfall (r2 class 2, 7/8 → 0/8), instruction leaks (r2: #19 → 0) and missing CTA lines (1 → 0). The Tsaatan physical-demand omission dropped from 4/4 Terra blogs to 2/4.
- New or worse: the thin-moment over-weighting (6/8), meta fact errors (r2 class 5, now on blogs too) and the doubled CTA, a new artifact of the CTA-literal restore.

## 3. Gate behaviour

- **Approved but heavy (3):**
  - **#19 (Terra blog).** Three visible repair duplicates, school framing, Khatgal in the FAQ and a duplicated SEO title. This is the worst false pass of the round. No gate checks near-duplicate sentences after a repair.
  - **#16 (A&H blog).** Nonsense meta, Khatgal in the FAQ and an H2 for the thin moment. F4 did not catch the meta and F9 did not see the FAQ.
  - **#9 (Trail Pulse LinkedIn, 2–2 tie).** Consultancy voice. Trail Pulse has been a false-pass cell in every round, because there is still no voice gate.
- **Held but light (2), both correct flags with the wrong action:**
  - #0 (F9): the storm contradiction is real, and one sentence fixes it.
  - #8 (F17): "in the morning" is invented, and deleting 3 words fixes it.

  Sentence-level repair (AA-769) would turn both into approvals.
- **Held and heavy (5), correct holds:** #3 (F14), #4, #12, #14 (F9) and #17 (F4 + F9).
- **What changed in blogs.** In r2, F16 held all 8 blogs. In r3, F16 fires on none because the FAQs are fixed. The gate's blog decisions now rest on F9 and F4:
  - 5/8 blogs held, all of them correctly (4 heavy; #0 light but correctly flagged).
  - 3/8 approved, 2 of them wrongly (#16, #19).
  - Blog precision is 1/3. LinkedIn precision is 9/10.

## 4. Next fixes, ranked

| Rank | Fix | Targets (class) | Expected effect |
|---|---|---|---|
| 1 | **Repair-pass integrity, fail closed.** After any repair and after the CTA-literal restore, run a normalised near-duplicate sentence check that does **not** exempt the CTA. Check that sentences are grammatical and not orphaned (a sentence must stay under its moment's H2). If the restore would duplicate a CTA the writer already paraphrased, replace the paraphrase instead of appending. | 4 | Would have held #19, the worst false pass, and removes the main defect of #4 and #12. 4/8 blogs affected. |
| 2 | **Anchor-weight rule for moments with 0 place facts.** At most 1–2 sentences, no own H2, not the climax or coda, no extrapolation beyond the seed's location. Enforce it in the writer prompt and with a deterministic check: an H2 whose content maps to a fact-less moment fails. | 3 | 6/8 blogs. It is the most common deciding defect on the blogs that are now just short of light (#16, #17, #12). |
| 3 | **Trip and scope grounding for blogs, including the FAQ.** Run the scope check on FAQ text (Khatgal ×3). Have F9/F17 flag "optional" being dropped or added, an overnight stop moved to another day (the Sod Camp base), "further south" legs, and protected-area placement. Whitelist names that appear in the seed's place-background facts (Ulaanbaatar, Thimphu) in `trip_places`, so the rule stops producing noise. | 2, 7 | Targets the invented-trip cluster (8/8 blogs) and the 7/8 scope or misplacement hits. Turns the extended count into signal. |
| 4 | **Hazard-polarity check for family brands.** If the seed carries a hazard (storms, a multi-hour ride, terrain), the copy must not negate or minimise it ("not a limitation", "not a reason for caution"). Terra copy must frame a demanding ride with pacing or safety. | 8 | #0, #14, #19. Small and deterministic. Removes a brand-safety risk on the family tenant. |
| 5 | **SEO-surface fact check and completeness.** Validate the meta and title against seed dates and spans (318 years, 1955, no "since 1637"), and reject incoherent metas. Require a title and meta on every piece (#6, #10), forbid "Day N" in titles, and make titles unique across sibling pieces of the same tenant (#0 = #19). | 5 | 11/20 pieces. Mostly deterministic. Moves Punakha LinkedIn (#1, #2, #7) closer to as-is. |
| 6 | **Anti-template and contrast-frame density (open since S233).** Make more than 1 contrast frame per 150 words a blocking warning. Maintain a stock-line list ("not a monument", "not an afterthought", "That's not coincidence", "X is part of the meaning", "This is not metaphor"). Check n-gram overlap across sibling pieces. | 1 | The only lever for as-is (0% in all 4 rounds; 0/20 pieces have AI-tells ≥7 in every round). |
| 7 | **Tenant voice rubric as a blocking check (open since S233).** Trail Pulse: energetic and social, not a pacing essay. Terra: no classroom framing, and the child's experience must be present. WildKind: habitat present. | 6 | Closes the Trail Pulse false pass (#9), the only cell with a false pass in all 4 rounds. Lifts LinkedIn from 10/12 toward 12/12 light. |
| 8 | **Text normaliser.** Strip leading and trailing whitespace and blank lines around headings. Write numbers as digits when the seed has digits. Remove internal seed notes (naming notes, angle wording such as "two named rivers") before they reach the writer. | 9, 10 | 7 pieces. Purely mechanical. |
| 9 | **Sentence-level repair on correct F9/F17 flags (AA-769).** Rewrite the flagged sentence instead of holding the piece. | gate | Converts #0 and #8 (light, correctly flagged) into approvals. Recall goes from 83% to 100%. |

Fixes 1–4 are what blogs need to cross into light. Two more blog pieces (#16, #17) sit one or two of those defects away. Fix 1 alone would have prevented the round's worst false pass. Fix 5 and fix 8 are cheap, deterministic polish. Fix 6 is still the only path to the ≥30% as-is bar on either channel.

---

*Scratch: `panel/r3/synth_r3.py` (vote tally, cell, tenant and gate metrics). Hard errors: `panel/measure_r3_s234r3.json`, `measure_r3_s234r2.json`, `measure_r3_s234r1.json` and `measure_r3_s233r1.json`.*
