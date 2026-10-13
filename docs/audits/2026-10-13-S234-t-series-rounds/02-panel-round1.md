# T9 commercial quality panel, S234: 20 pieces vs S233 round 1

**Input.** `.tmp-session/s234/pieces.json`: 20 pieces across 6 cells, 4 tenants and 2 channels. Piece numbers are the 0-based index in that file.

| Brief | Tenant / channel | Pieces | Gate |
|---|---|---|---|
| Punakha Dzong (day 4) | WildKind LinkedIn | #0, #6, #11 | 3 approved |
| Punakha Dzong (day 4) | A&H LinkedIn | #5, #12, #15 | 2 approved, #12 held (F1_grounding) |
| Tiger's Nest (day 9) | Terra LinkedIn | #4, #8, #13 | 3 approved |
| Kuang Si Falls (day 2) | Trail Pulse LinkedIn | #3, #7, #14 | 3 approved (#7 shows F15_voice in `failed` but is approved) |
| Mongolia days 3–14 | A&H blog | #1, #10, #16, #18 | 4 approved |
| Mongolia days 3–14 | Terra blog | #2, #9, #17, #19 | 2 approved; #9 held (F9_cta_fact), #19 held (F1_grounding) |

**Method.** Same as S233 (and S232):
- **4 lenses:** editor (E), tenant brand lead (B), channel specialist (C), paying client (K). That gives 80 votes.
- **Verdict:** the majority vote. A 2–2 tie gets the stricter label.
- **Light edit:** ≤10 minutes, ≤3 sentences changed, no fact research. **Publish as-is:** a paying tenant would post it unchanged.
- **Scores:** 7 dimensions plus overall, each /10. The per-piece overall is the mean of the 4 lenses.
- **Fidelity:** a separate fidelity audit checked every claim against the seed, the "Place background" lines and the brand pack. Its own /10 score is reported separately from the lens fidelity mean.
- **Hard errors:** deterministic, from `measure.py` (hygiene.find_issues + claim_rules + LinkedIn checks). S233 r1 was re-measured with the same script, so raw vs raw is like for like.

**Caveat.** S233 r1 was **one rater simulating 4 lenses**. S234 used **4 independent agents**, one per lens, plus a separate fidelity auditor. Independent raters disagree more, which pushes more pieces to 2–2 ties (and so to the stricter label), but they also do not anchor on each other. Compare the two rounds directionally, not to the decimal. The lens-fidelity mean (5.89) is comparable to S233's 5.80. The audit score (7.10) has no S233 equivalent.

---

## 0. Bottom line

1. **Still not commercial-grade, but LinkedIn has crossed the light-edit line.**
   - 0/20 publish-as-is. 11 (55%) light, 8 (40%) heavy, 1 (5%) reject.
   - Overall is 5.52 (S233: 5.33). Best piece 6.5 (#13; S233 best 6.2).
   - D1 bar: ≥80% as-is or light and ≥30% as-is. All: 55% and 0%. **LinkedIn alone: 92% (11/12) and 0%.**
   - #13 (Terra Tiger's Nest) got the first as-is vote in either round (channel lens).
2. **The S233 deterministic fixes landed.**
   - Hard errors 65 → 10 raw (9 after false-positive review). Pieces clean 2/20 → 14/20 (15/20).
   - Scope in title and meta 16 → 0; "content seed" leaks 2 → 0; social proof 2 → 0; misspelt hashtags 2 → 0; LinkedIn >3 hashtags 8 → 0.
   - LinkedIn words: mean 356 → 194, in band 1/12 → 12/12.
3. **The channels still split.**
   - LinkedIn: 11/12 light (S233: 6/12). WildKind and A&H Punakha are 3/3 and 3/3 light by majority; Terra Tiger's Nest 3/3.
   - Blogs: 0/8 light again (S233: 0/8). 7 heavy, 1 reject (#19). New blog defect classes have replaced the old ones: missing or 1-item FAQ (6/8), writer-instruction headings (#10, #16), "fifteen-day" trip length (4/4 Terra blogs), repair artifacts (#19).
4. **AI-tells barely moved** (4.54; S233: 4.45). 0/20 score ≥7. Contrast frames ("not X, it is Y") are flagged in 18/20 pieces, and the same brief still produces the same stock line (Kuang Si "filler" 3/3).
5. **Gates approve even more; precision rose but is far from target.**
   - Approval rate 85% (17/20; S233: 60%). Precision 10/17 = 59% (S233: 42%). Recall 10/11 = 91% (S233: 83%).
   - LinkedIn approvals are 10/11 light (91%). **Blog approvals are 0/6** light: every approved blog is heavy edit.
   - Gate vs panel agreement 12/20 (S233: 12/20). "Hold everything" would agree 9/20.

**Decision.** LinkedIn is close to shippable with a light human pass; the remaining blocker for as-is is AI phrasing and the "Bhutan meditation retreat" meta keyword. Do not ship blogs: fix the FAQ contract, instruction leaks, trip-length leak and seed contradictions first (§5, fixes 1–5), and stop the gate approving blogs that fail them.

---

## 1. Commercial verdict

### 1.1 Overall

| | Publish as-is | Light edit | Heavy edit | Reject |
|---|---|---|---|---|
| Pieces (n=20) | 0 (0%) | 11 (55%) | 8 (40%) | 1 (5%) |
| Lens votes (n=80) | 1% (1) | 56% (45) | 40% (32) | 3% (2) |

Two pieces split 2–2 and took the stricter label: #10 (L/H → heavy) and #19 (H/R → reject). If ties went the lenient way, blogs would be 1/8 light (13%) and LinkedIn is unchanged at 11/12.

### 1.2 By channel and tenant

| Cell | n | Approved | Approved: L/H/R | Held: L/H/R | Light votes | Overall /10 |
|---|---|---|---|---|---|---|
| Terra LinkedIn (Tiger's Nest) | 3 | 3 | 3/0/0 | – | 92% | 6.12 |
| WildKind LinkedIn (Punakha) | 3 | 3 | 3/0/0 | – | 100% | 6.12 |
| A&H LinkedIn (Punakha) | 3 | 2 | 2/0/0 | 1/0/0 | 100% | 6.09 |
| Trail Pulse LinkedIn (Kuang Si) | 3 | 3 | 2/1/0 | – | 50% | 5.18 |
| A&H blog (Mongolia) | 4 | 4 | 0/4/0 | – | 31% | 5.36 |
| Terra blog (Mongolia) | 4 | 2 | 0/2/0 | 0/1/1 | 0% | 4.59 |
| **LinkedIn** | 12 | 11 | 10/1/0 | 1/0/0 | 85% | 5.88 |
| **Blog** | 8 | 6 | 0/6/0 | 0/1/1 | 16% | 4.97 |
| **All** | 20 | 17 (85%) | 10/7/0 | 1/1/1 | 57% | 5.52 |

"Light votes" counts as-is and light votes together (the single as-is vote is on #13).

By tenant, both channels pooled (S233 in brackets):

| Tenant | Light | Overall |
|---|---|---|
| WildKind | 3/3 (1/3) | 6.12 (5.80) |
| A&H | 3/7 (2/7) | 5.67 (5.13) |
| Terra | 3/7 (3/7) | 5.25 (5.50) |
| Trail Pulse | 2/3 (0/3) | 5.18 (4.93) |

### 1.3 Per piece

| # | Cell | Gate | Votes E/B/C/K | Verdict | Overall | Deciding defects |
|---|---|---|---|---|---|---|
| 13 | Terra LI | approved | L L A L | Light | 6.5 | Brand name twice back to back in the close; "The place has real weight to it."; no child's-eye view |
| 0 | WildKind LI | approved | L L L L | Light | 6.2 | Meta "Bhutan meditation retreat"; invented siting intent and river symbolism ("placement was deliberate"); architecture, not nature |
| 11 | WildKind LI | approved | L L L L | Light | 6.2 | "chosen as the foundation for a country"; "dual purpose still legible" (admin role ended 1955); meta retreat |
| 5 | A&H LI | approved | L L L L | Light | 6.2 | "chosen with precision, not chance"; "not decoration for its own sake"; meta retreat; 241–251 words |
| 4 | Terra LI | approved | L L L L | Light | 6.1 | First line 165 chars (hard error); 8th-century tradition stated as fact; parents only |
| 15 | A&H LI | approved | L L L L | Light | 6.1 | Flat hook; invented confluence symbolism; "read differently once the founding logic…" shared with #12; meta retreat |
| 6 | WildKind LI | approved | L L L L | Light | 6.0 | Invented "defensibility"; circular hook; agreement error in CTA; meta retreat |
| 12 | A&H LI | **held** (F1) | L L L L | Light | 6.0 | First line 209 chars (hard error); "the same argument about where power and devotion are properly placed"; meta retreat |
| 8 | Terra LI | approved | H L L L | Light | 5.8 | "It was founded in the 8th century" (temples 1692); checkpoint misplaced "on the trail"; 2 contrast frames |
| 3 | Trail LI | approved | L L L H | Light | 5.5 | "Day 2 ends at … pools" (lunch follows); "That's not filler. It's a structural choice."; pacing essay, not Trail energy |
| 14 | Trail LI | approved | H L L L | Light | 5.5 | 4 contrast frames in 161 words; same "filler" template as #3/#7; corporate close |
| 7 | Trail LI | approved (F15 listed) | H H H H | Heavy | 4.6 | "If you're a 25–40 traveller" (brand segment leaked); consultancy opener; title "Rest Day" is false |
| 10 | A&H blog | approved | H L L H | Heavy (tie) | 5.7 | H2 "A Single Sentence on What Time Has Taken" (instruction leak); meta "cultures thrive" contradicts decline; optional activities as structure; duplicated sentence |
| 1 | A&H blog | approved | H H H L | Heavy | 5.4 | 1 FAQ; 6+ contrast frames ("This is not a metaphor."); "exist almost nowhere else on earth"; spelled-out numbers |
| 18 | A&H blog | approved | H H H L | Heavy | 5.3 | "This piece traces one route" (self-reference); doubled CTA; 1 FAQ; meta "ancient geology" vs "geologically recent" |
| 9 | Terra blog | **held** (F9) | H H H H | Heavy | 5.2 | "short-seasoned", "zero point four percent"; "Children who want to be on horseback can be"; "fifteen-day"; 1,663 words; 2 repeats |
| 16 | A&H blog | approved | H H H L | Heavy | 5.1 | H2 "A Sentence on Loss" (instruction leak); "before any human presence at all" (false); "the access to understand"; 1 FAQ |
| 17 | Terra blog | approved | H H H H | Heavy | 5.0 | No FAQ; blank-gap artifact; invented shore viewpoint; "something ancient"; "fifteen-day"; trip "closes on day fourteen" |
| 2 | Terra blog | approved | H H H H | Heavy | 4.3 | Opens on "the Gobi" (scope, hard error); "two percent" vs 0.4%; "The lake was established as … National Park"; no FAQ; "seven-to-sixteen range" leak; contradictory day order |
| 19 | Terra blog | **held** (F1) | H R R H | Reject (tie) | 3.8 | Broken opener with no antecedent (repair artifact); duplicated caldera sentence; "Gobi Desert" in CTA; "classroom material" framing; 1 FAQ |

### 1.4 S233 round 1 vs S234

| Metric | S233 r1 (n=20) | S234 (n=20) | Change |
|---|---|---|---|
| Publish as-is | 0% | 0% | = |
| Light edit | 30% | 55% | +25 pp |
| Heavy edit | 70% | 40% | −30 pp |
| Reject | 0% | 5% | +5 pp |
| Light votes (incl. as-is) | 35% | 57% | +22 pp |
| Overall /10 | 5.33 | 5.52 | +0.19 |
| Best piece | 6.2 | 6.5 | +0.3 |
| Fidelity (lens mean) | 5.80 | 5.89 | +0.09 |
| Fidelity, LinkedIn / blog | 6.62 / 4.56 | 6.44 / 5.08 | −0.18 / +0.52 |
| Fidelity audit score | – | 7.10 (LI 7.67, blog 6.25) | new |
| AI-tells | 4.45 | 4.54 | +0.09 |
| Pieces AI-tells ≥7 | 0/20 | 0/20 | = |
| Gate approval rate | 60% (12/20) | 85% (17/20) | +25 pp |
| Approval precision (approved that are as-is/light) | 42% (5/12) | 59% (10/17) | +17 pp |
| Light-edit recall | 83% (5/6) | 91% (10/11) | +8 pp |
| Gate–panel agreement | 12/20 | 12/20 | = |
| LinkedIn light (pieces) | 6/12 (50%) | 11/12 (92%) | up |
| Blog light (pieces) | 0/8 (0%) | 0/8 (0%) | = |
| LinkedIn overall / blog overall | 5.64 / 4.86 | 5.88 / 4.97 | +0.24 / +0.11 |

### 1.5 Hard errors (deterministic), S233 r1 vs S234

| Category | S233 r1 instances (pieces) | S234 instances (pieces) |
|---|---|---|
| Scope in title | 8 (8) | 0 |
| Scope in meta | 8 (8) | 0 |
| Scope in body | 21 (7) | 2 (2: #2, #19, "Gobi") |
| Leak ("content seed") | 2 (2) | 0 |
| Social proof | 2 (2) | 0 |
| Repeat | 10 (7) | 6 (4: #2, #9, #17, #19); #17 is a false positive |
| Misspelt hashtag | 2 (2) | 0 |
| LinkedIn >3 hashtags | 8 (8) | 0 |
| LinkedIn first line >140 | 4 (4) | 2 (2: #4 165, #12 209) |
| Truncated | 0 | 0 |
| **Total** | **65** | **10 raw / 9 after FP review** |
| Pieces with any hard error | 18/20 | 6/20 raw, 5/20 after FP review |
| Pieces clean | 2/20 | 14/20 raw, 15/20 after FP review |
| LinkedIn clean / blog clean | 2/12 / 0/8 | 10/12 / 4/8 (5/8) |
| LinkedIn words in band | 1/12 (mean 356) | 12/12 (mean 194) |
| CTA present / blog CTA before FAQ | 20/20 / 8/8 | 20/20 / 6/6 blogs with a FAQ |

Info only (not counted): "fifteen-day" trip length in 4/4 Terra blogs (#2, #9, #17, #19), taken from the trip name and not in the seed.

**Hard errors no longer predict the verdict.** 15 pieces are clean, yet 4 clean blogs (#1, #10, #16, #18) are heavy edit. The detector does not see the defects that now decide blog verdicts (missing FAQ, instruction-style headings, self-reference, brand-segment numbers, repair artifacts).

---

## 2. Top remaining defect classes

| # | Defect class | Pieces | Count | Detected today? |
|---|---|---|---|---|
| 1 | Contrast frames / stock AI lines ("not X, it is Y", "This is not a metaphor.", "That's the detail worth…") | all except #11, #13 | 18/20 | No (AI-tells 4.54, 0/20 ≥7) |
| 2 | Meta keyword "Bhutan meditation retreat": a product the trip does not have, in the link preview | #0, #5, #6, #11, #12, #15 | 6/6 Punakha | No (keyword is assigned upstream) |
| 3 | Invented siting intent / river symbolism for Punakha (the angle forbids it) | #0, #5, #6, #11, #12, #15 | 6/6 Punakha | No (F1 held only #12) |
| 4 | Blog FAQ missing (#2, #17) or only 1 item (#1, #16, #18, #19) | #1, #2, #16, #17, #18, #19 | 6/8 blogs | No |
| 5 | Writer-instruction or internal-data leaks: "A Single Sentence on…", "A Sentence on Loss", "This piece traces", "25–40 traveller", "seven-to-sixteen range" | #2, #7, #10, #16, #18 | 5/20 | No (leak detector covers "content seed" only) |
| 6 | Trip length / end-of-trip invented: "fifteen-day", "the journey concludes / route closes on day fourteen" | #2, #9, #17, #18, #19 | 5/8 blogs | Info only |
| 7 | Seed contradictions and day order: 2% vs 0.4%; Sod Camp vs Mörön order; "down to the lakeshore"; "ancient" vs "geologically recent"; "before any human presence" | #1, #2, #9, #16, #17, #18 | 6/8 blogs | No |
| 8 | Cross-piece templated lines within a brief: Kuang Si "filler" (#3, #7, #14); "A well-prepared family arrives…" (#8, #13); "read differently once the founding logic…" (#12, #15); A&H blog opener "not simply remote" / same H2 (#1, #10, #16, #18) | 11 pieces | 4 templates | No |
| 9 | Tenant voice miss: Terra LinkedIn with no child's-eye view (#4, #8, #13); Trail Pulse calm explainer, not energetic (#3, #7, #14); Terra classroom framing (#2, #19) | 8 pieces | 8/20 | No (no core-theme check) |
| 10 | Implied promises / optional activities as fixed: horseback for children (#9), shamanism "documented part of what visitors experience" (#2), optional boat and horse rides as structure (#10), "the access to understand" (#16) | #2, #9, #10, #16, #17 | 5/20 | Partly (F9 held #9) |
| 11 | Repair artifacts: dangling antecedent and duplicate sentence (#19), duplicated sentence (#10), restated facts (#9), blank gap (#17) | #9, #10, #17, #19 | 4/8 blogs | Partly (repeat detector) |
| 12 | Tradition stated as fact (8th century) | #4, #8 | 2/3 Terra LI | No |
| 13 | Scope "Gobi" in body | #2, #19 | 2 | Yes (hard error), but #2 was still approved |

---

## 3. Gate behaviour

- **Approved but heavy (7):** #1, #2, #7, #10, #16, #17, #18. Six are blogs. #2 carries 2 hard errors (scope "Gobi" + repeat) and was approved. #7 lists F15_voice in `failed` yet has status approved (attempt 3); check whether a later attempt cleared the flag or the flag is ignored.
- **Held but light (1):** #12 (F1_grounding). Its real defects (209-char first line, invented symbolism) are the same as approved #5 and #15, so the hold is right in outcome but inconsistent across siblings.
- **Held and correct (2):** #9 (F9_cta_fact), #19 (F1_grounding).
- **Blog approval precision 0/6.** The gates do not check the blog-specific defects in §2 (classes 4–7, 11).

---

## 4. What improved and what did not

- **Improved:** every deterministic class targeted in S233 (scope, leaks, social proof, hashtags, length). LinkedIn light 50% → 92%. WildKind and Trail Pulse rose the most (+2 light each). Blog fidelity +0.5.
- **Flat:** AI-tells (+0.09), as-is (0%), blog light (0/8), gate–panel agreement (12/20).
- **Worse or new:** 1 reject (#19, repair broke the opener); instruction-style headings (2 blogs); meta keyword mispositioning across all 6 Punakha posts.

---

## 5. Next fixes, ranked

| Rank | Fix | Targets (class) | Expected effect |
|---|---|---|---|
| 1 | **Blog FAQ contract.** Deterministic check: blog must have `## FAQ` with ≥3 Q/A pairs; block approval otherwise. Repair by regenerating the FAQ section only. | 4 | 6/8 blogs lose their single deciding structural defect. Cheap. |
| 2 | **Extend the leak detector** to writer-instruction and internal-data patterns: headings with "Sentence on", "A Single Sentence"; "This piece / this guide covers"; brand-pack segment numbers ("25–40", "seven-to-sixteen", age ranges); day-number scope mechanics. Hard error, blocks approval. | 5 | Removes 5 embarrassing pieces' main defect; deterministic. |
| 3 | **Ground the keyword before T8.** The SEO keyword must be supported by the seed (or trip): reject "meditation retreat" for a dzong visit. Add a meta check: product nouns in meta ("retreat", "guides you") must appear in the seed or body. | 2 | Fixes the link-preview false promise on 6/6 Punakha posts; moves them toward as-is. |
| 4 | **Trip-name hygiene for scoped briefs.** Strip duration and out-of-scope places from `trip_name` given to the writer when scope ≠ full trip; promote novel word-number "fifteen-day" to a hard error in that case; forbid "the journey concludes" unless the last scoped day is the trip end. | 6, 13 | Removes "fifteen-day" (4/4 Terra blogs) and "Gobi" in the CTA (#19). |
| 5 | **Seed hygiene (S233 fix 8, still open).** One canonical value per fact across a place's cards (0.4% vs 2%), day order validated against geography and listed by day, "geologically recent" carried into the meta prompt. | 7 | Removes the contradiction cluster in 6/8 blogs. |
| 6 | **Anti-template + contrast-frame density (S233 fix 6, still open).** Blocking warning at >1 contrast frame per 150 words; stock-line list (from §2 class 1 and 8); n-gram overlap check across sibling pieces in the same brief; T8 must not seed a literal opener. | 1, 8 | The only path to as-is: AI-tells 4.5 → ~6+. |
| 7 | **Repair-pass integrity.** After any repair, re-run repeat + a dangling-antecedent check (paragraph or piece opening with "It/This/What they…" whose referent was removed); fail closed. | 11 | Prevents rejects like #19 and duplicates like #10. |
| 8 | **Tenant core-theme rubric in F9/Jev (S233 fix 7, still open).** Terra: child's-eye view required, no classroom framing; Trail Pulse: social/energetic, no consultancy opener; WildKind: habitat/nature present; A&H: no access promises. Make F15_voice blocking. | 9, 10 | Approval precision 59% → ~75%; catches #7-type false passes. |
| 9 | **Siting-rationale and tradition guard in F1.** Flag "deliberate / chosen because / founded in the 8th century" claims that the seed gives only as tradition or not at all. | 3, 12 | Fidelity on Punakha and Tiger's Nest LinkedIn. Lower priority: these are already light. |

Fixes 1–5 are deterministic or upstream and address blogs; together they should move blogs from 0/8 to roughly half light. Fix 6 is the only lever for the ≥30% as-is bar, on both channels.
