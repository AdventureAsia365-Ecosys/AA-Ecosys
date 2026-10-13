# T9 commercial quality panel, S234 round 2: 20 pieces vs S233 r1 and S234 r1

**Input.** `.tmp-session/s234/pieces_r2.json`: 20 pieces across 6 cells, 4 tenants and 2 channels. Piece numbers are the 0-based index in that file, so they do **not** match the r1 numbering.

| Brief | Tenant / channel | Pieces | Gate |
|---|---|---|---|
| Punakha Dzong (day 4) | WildKind LinkedIn | #0, #9, #13 | 2 approved; #13 held (F1_grounding) |
| Punakha Dzong (day 4) | A&H LinkedIn | #1, #7, #12 | 2 approved; #7 held (F9_cta_fact) |
| Tiger's Nest (day 9) | Terra LinkedIn | #2, #6, #10 | 3 approved |
| Kuang Si Falls (day 2) | Trail Pulse LinkedIn | #3, #8, #11 | 3 approved |
| Mongolia days 3–14 | A&H blog | #4, #14, #16, #18 | 4 held (F16_faq) |
| Mongolia days 3–14 | Terra blog | #5, #15, #17, #19 | 4 held (#5 F9+F16, #15 F15+F16, #17 F16, #19 F9) |

**Method.** Same as S233 and S234 r1:
- **4 lenses:** editor (E), tenant brand lead (B), channel specialist (C) and paying client (K), which gives 80 votes.
- **Verdict:** the majority of the 4 votes. A 2–2 tie takes the stricter label.
- **Light edit:** ≤10 minutes, ≤3 sentences changed and no fact research. **Publish as-is:** a paying tenant would post the piece unchanged.
- **Scores:** 7 dimensions plus overall, each /10. The per-piece overall is the mean of the 4 lenses.
- **Fidelity audit:** a separate audit checked every claim against the seed, the "Place background" lines and the brand pack. Its /10 score is reported apart from the lens fidelity mean.
- **Hard errors:** deterministic, from `measure_r2.py`, which is `measure.py` plus the `leak` list on main 5ecff79. S233 r1 and S234 r1 were re-measured with it. The core totals match the earlier runs exactly (65 and 10), so all 3 rounds are like for like.

**Caveat.**
- S233 r1 was **one rater simulating 4 lenses**. Both S234 rounds used **4 independent agents**, one per lens, plus a separate fidelity auditor. Independent raters disagree more, which produces more 2–2 ties and so more strict labels, but they also do not anchor on each other.
- S234 r1 and r2 used different agent instances on different pieces. Read changes of about ±0.2 in overall or ±1 piece in a cell as noise.
- The fidelity audit counts the configured tenant CTAs as unsupported promises: A&H "travel designer" (A&H pieces #1, #4, #7, #12, #16, #18) and Trail Pulse "itinerary and dates" (#3, #8, #11). These CTAs come from the S231 per-tenant CTA in `s234_checkpoint_r2.py`, not from the writer. They lower the A&H audit scores slightly and should be fixed in the CTA config, not in the writer.

---

## 0. Bottom line

1. **Still not commercial-grade. The headline numbers are flat against r1, but the gate is now much more honest.**
   - 0/20 pieces are publish-as-is. 10 (50%) are light edit, 10 (50%) heavy, 0 reject. In r1 the split was 55/40/5.
   - Overall is 5.57 (r1 5.52, S233 5.33). The best piece is #0 at 6.28, below r1's best of 6.5.
   - The D1 bar is ≥80% as-is or light and ≥30% as-is. All pieces: 50% and 0%. **LinkedIn alone: 83% (10/12) and 0%.** In r1 LinkedIn was 92%; the drop is one tie (#3) and #8.
2. **The deterministic hygiene work is essentially finished.**
   - Core hard errors fell from 65 (S233) to 10 (r1) to **2** (r2). Clean pieces went from 2 to 14 to **18/20**.
   - All 12 LinkedIn posts are clean, and so are 6/8 blogs.
   - The 2 remaining errors are both a repeat of the "70% of Mongolia's fresh water" figure (#14, #16).
   - Extended (x_*) hits fell from 89 to 27 to 3. 1 of the 3 is a false positive.
   - Gone completely: "meditation retreat" in metas, "Gobi" anywhere, "fifteen-day", scope leaks and writer-instruction headings. One instruction leak remains in body text (#19).
3. **Blogs are still 0/8 light, and every lens now agrees.**
   - 32/32 blog votes are heavy. r1 had 16% light votes on blogs.
   - The FAQ contract still fails: 7/8 blogs have fewer than 3 FAQs (r1: 6/8).
   - New invented-trip details appear: "first night", "southern tip", optional activities written as fixed, "systematic erasure".
   - Rarity overclaims appear in 6/8 blogs ("no equivalent elsewhere", seed "many" becomes "most").
   - Family pieces omit that the Tsaatan access is physically demanding (#5, #15, #17, #19).
   - Repair duplicates remain in 4/8 blogs.
4. **AI-tells did not move** (4.45 vs r1 4.54 and S233 4.45). 0/20 pieces score ≥7.
   - Contrast frames appear in 16/20 pieces.
   - Stock lines are reused across pieces: "worth sitting with" ×3, "isn't filler" again, and "movement and energy delivered well" pasted from the brand pack ×2.
5. **The gates are now selective and mostly right.**
   - Approval rate fell from 85% to **50% (10/20)**. Approval precision rose from 59% to **80% (8/10)**. Recall fell from 91% to 80% (8/10).
   - **The gates and the panel agree on 16/20 pieces** (r1: 12/20). Holding everything would agree on only 10/20.
   - All 8 blogs were held, which is correct, so blog false passes fell from 6 to 0.
   - The remaining errors:
     - 2 false passes: Trail Pulse #3 and #8, approved but heavy. There is still no voice gate for an energetic brand.
     - 2 false holds: #7 (F9) and #13 (F1). Both are light edits, and both flags point at real defects.

**Decision.** LinkedIn is shippable with a light human pass for Terra, WildKind and A&H: 8/9 pieces are light, and 7 of those 8 are approved. Trail Pulse is not shippable (1/3 light). Do not ship blogs. The gate now stops them, so the next work is to make blogs pass rather than to block them better: fix the FAQ generation, repair integrity and trip-fact grounding (§4, fixes 1–3). Only anti-template work (fix 4) can move the as-is rate.

---

## 1. Commercial verdict

### 1.1 Overall

| | Publish as-is | Light edit | Heavy edit | Reject |
|---|---|---|---|---|
| Pieces (n=20) | 0 (0%) | 10 (50%) | 10 (50%) | 0 (0%) |
| Lens votes (n=80) | 1% (1) | 50% (40) | 49% (39) | 0% (0) |

One piece split 2–2 and took the stricter label: #3 (E H, B L, C L, K H, so heavy). Counting the tie as light would make LinkedIn 11/12 (92%) and leave blogs at 0/8.

### 1.2 By channel and tenant

| Cell | n | Approved | Approved: L/H/R | Held: L/H/R | Light votes | Overall /10 |
|---|---|---|---|---|---|---|
| Terra LinkedIn (Tiger's Nest) | 3 | 3 | 3/0/0 | – | 100% | 6.23 |
| WildKind LinkedIn (Punakha) | 3 | 2 | 2/0/0 | 1/0/0 | 100% | 6.15 |
| A&H LinkedIn (Punakha) | 3 | 2 | 2/0/0 | 1/0/0 | 92% | 5.71 |
| Trail Pulse LinkedIn (Kuang Si) | 3 | 3 | 1/2/0 | – | 50% | 5.29 |
| A&H blog (Mongolia) | 4 | 0 | – | 0/4/0 | 0% | 5.19 |
| Terra blog (Mongolia) | 4 | 0 | – | 0/4/0 | 0% | 5.13 |
| **LinkedIn** | 12 | 10 | 8/2/0 | 2/0/0 | 85% | 5.85 |
| **Blog** | 8 | 0 | – | 0/8/0 | 0% | 5.16 |
| **All** | 20 | 10 (50%) | 8/2/0 | 2/8/0 | 51% | 5.57 |

"Light votes" counts as-is and light votes together. The single as-is vote is from the channel lens on #6.

By tenant, both channels pooled. Brackets show S234 r1, then S233 r1.

| Tenant | Light | Overall |
|---|---|---|
| WildKind | 3/3 (3/3, 1/3) | 6.15 (6.12, 5.80) |
| Terra | 3/7 (3/7, 3/7) | 5.60 (5.25, 5.50) |
| A&H | 3/7 (3/7, 2/7) | 5.41 (5.67, 5.13) |
| Trail Pulse | 1/3 (2/3, 0/3) | 5.29 (5.18, 4.93) |

### 1.3 Per piece

| # | Cell | Gate | Votes E/B/C/K | Verdict | Overall | Deciding defects |
|---|---|---|---|---|---|---|
| 0 | WildKind LI | approved | L L L L | Light | 6.28 | "Two rivers framing a structure on three sides" plus landscape symbolism the angle forbids; "most honest form of travel" aphorism; little habitat content |
| 2 | Terra LI | approved | L L L L | Light | 6.25 | Template hook ("asks something of every visitor… gives back"); "Knowing them in advance" has no antecedent; brand name twice in the close |
| 6 | Terra LI | approved | L L A L | Light | 6.25 | Para 1 restates the hook; filler line "Each layer of that history shapes…"; "surrendered"; #ParoDistrict |
| 10 | Terra LI | approved | L L L L | Light | 6.20 | Non sequitur "history deserves more than a rushed arrival"; "These aren't… they're" frame; brand name twice in the close |
| 9 | WildKind LI | approved | L L L L | Light | 6.15 | Invented "practical defensibility"; "remains of Zhabdrung" (seed: sacred relic); meta "active… center today" |
| 13 | WildKind LI | **held** (F1) | L L L L | Light | 6.03 | "understood exactly what that meant" (mind-reading, F1 is right); meta "remains Bhutan's… administrative center"; #PhoChhu/#MoChhu without #Bhutan |
| 1 | A&H LI | approved | L L L L | Light | 5.88 | "heart" twice in the opening; "That permanence endures" (dzong rebuilt; capital moved 1955); rivers not named |
| 12 | A&H LI | approved | H L L L | Light | 5.75 | **"nearly three centuries"** (1637–1955 is more than three); "a kingdom's founding"; "narrow" (seed: long); stacked contrast frames |
| 11 | Trail LI | approved | L H L L | Light | 5.52 | **"That stop isn't filler."** (S233 template returns); invented "mid-morning" swim; brand pack pasted as copy |
| 7 | A&H LI | **held** (F9) | L L L L | Light | 5.50 | Hook does not name the dzong or the rivers; "founding purpose… never been set aside" (contradicts 1955); "deliberate" ×3 |
| 18 | A&H blog | held (F16) | H H H H | Heavy | 5.33 | 2 FAQs; optional activities listed as fixed; "mirror-still", "Mörön: The Gateway Province"; 4+ "not X" frames; SEO title identical to #4 |
| 4 | A&H blog | held (F16) | H H H H | Heavy | 5.30 | 1 FAQ; **Sod Camp duplicated inside the lake section** (repair artifact, misplaced); opening says the same thing twice |
| 8 | Trail LI | **approved** | H H L H | Heavy | 5.30 | Rest thesis stated 3×; wellness-coach voice for an energetic brand; CTA points at the whole trip |
| 17 | Terra blog | held (F16) | H H H H | Heavy | 5.28 | "only a few hundred people" twice; classroom framing; Ulaanbaatar named (out of scope, not detected); Tsaatan as "logical endpoint"; 2 FAQs |
| 14 | A&H blog | held (F16) | H H H H | Heavy | 5.25 | 1 FAQ; Uran Togoo placed "in Khövsgöl Province"; "first night"; "southern tip"; 70% figure repeated (hard error); "measure of its integrity" |
| 19 | Terra blog | held (F9) | H H H H | Heavy | 5.22 | **Instruction leak** "One ruined site, one date, one fact."; "first night in real Mongolia"; "darkening treeline"; configured CTA line missing |
| 15 | Terra blog | held (F15, F16) | H H H H | Heavy | 5.08 | Invented supervision promise ("without either having to wait"); "stays with families long after"; "worth sitting with"; 1 FAQ; 1,374 words |
| 3 | Trail LI | **approved** | H L L H | Heavy (tie) | 5.05 | **Orphan repair line "The itinerary builds it in."**; 124 words; flat hook; "movement and energy delivered well" |
| 5 | Terra blog | held (F9, F16) | H H H H | Heavy | 4.95 | Invented "same day, adjustable pace" family promise; omits the multi-hour horse ride; "worth sitting with"; 1 FAQ, which is about Ulaanbaatar |
| 16 | A&H blog | held (F16) | H H H H | Heavy | 4.90 | **"Uran Togoo arrives on day three. On day three…"** (repair); "The mountain remembers"; "systematic erasure"; 70% repeat (hard error); 2 FAQs |

### 1.4 S233 r1 vs S234 r1 vs S234 r2

| Metric | S233 r1 | S234 r1 | S234 r2 | r1 → r2 |
|---|---|---|---|---|
| Publish as-is | 0% | 0% | 0% | = |
| Light edit | 30% | 55% | 50% | −5 pp (1 piece) |
| Heavy edit | 70% | 40% | 50% | +10 pp |
| Reject | 0% | 5% | 0% | −5 pp |
| Light votes (incl. as-is) | 35% | 57% | 51% | −6 pp |
| Overall /10 | 5.33 | 5.52 | 5.57 | +0.05 |
| Best piece | 6.2 | 6.5 | 6.28 | −0.2 |
| Fidelity (lens mean) | 5.80 | 5.89 | 5.85 | −0.04 |
| Fidelity, LinkedIn / blog | 6.62 / 4.56 | 6.44 / 5.08 | 6.41 / 5.02 | ≈ |
| Fidelity audit | – | 7.10 (LinkedIn 7.67, blog 6.25) | 7.08 (LinkedIn 7.50, blog 6.44) | ≈ |
| Pieces with lens fidelity ≥7 | 6/20 | – | 4/20 | – |
| AI-tells | 4.45 | 4.54 | 4.45 | −0.09 |
| Pieces with AI-tells ≥7 | 0/20 | 0/20 | 0/20 | = |
| Gate approval rate | 60% (12/20) | 85% (17/20) | **50% (10/20)** | −35 pp |
| Approval precision (approved pieces that are as-is or light) | 42% (5/12) | 59% (10/17) | **80% (8/10)** | +21 pp |
| Light-edit recall | 83% (5/6) | 91% (10/11) | 80% (8/10) | −11 pp |
| Gate–panel agreement | 12/20 | 12/20 | **16/20** | +4 |
| Blog false passes (approved but heavy) | 2 | 6 | **0** | −6 |
| LinkedIn light (pieces) | 6/12 (50%) | 11/12 (92%) | 10/12 (83%) | −1 |
| Blog light (pieces) | 0/8 | 0/8 | 0/8 | = |
| Blog light votes | 6% | 16% | 0% | −16 pp |
| LinkedIn / blog overall | 5.64 / 4.86 | 5.88 / 4.97 | 5.85 / 5.16 | −0.03 / +0.19 |

### 1.5 Hard errors (deterministic, `measure_r2.py`)

| Category | S233 r1 instances (pieces) | S234 r1 | S234 r2 |
|---|---|---|---|
| Scope in title | 8 (8) | 0 | 0 |
| Scope in meta | 8 (8) | 0 | 0 |
| Scope in body | 21 (7) | 2 (2) | 0 |
| Leak ("content seed") | 2 (2) | 0 | 0 |
| Social proof | 2 (2) | 0 | 0 |
| Repeat | 10 (7) | 6 (4) | 2 (2: #14, #16) |
| Misspelt hashtag | 2 (2) | 0 | 0 |
| LinkedIn >3 hashtags | 8 (8) | 0 | 0 |
| LinkedIn first line >140 | 4 (4) | 2 (2) | 0 (max 131) |
| Truncated / LinkedIn markdown | 0 | 0 | 0 |
| **Core total** | **65** | **10** | **2** |
| Pieces clean (core) | 2/20 | 14/20 | **18/20** |
| LinkedIn clean / blog clean | 2/12 / 0/8 | 10/12 / 4/8 | **12/12 / 6/8** |
| Extended (x_*) total | 89 | 27 | 3 (1 false positive: #15 "journey ends" is figurative) |
| LinkedIn words in band 120–250 | 1/12 (mean 356) | 12/12 (mean 194) | 11/12 (mean 181; #3 has 119) |
| CTA line present | 20/20 | 20/20 | 19/20 (#19 paraphrases it, and `check_cta` still passes) |

**Hard errors no longer explain the verdicts.** 18/20 pieces are clean, but 8 clean pieces are heavy edit: 6 blogs plus Trail Pulse #3 and #8. The defects that now decide verdicts are invisible to the detector: FAQ count (caught by the F16 gate, not by `measure`), repair artifacts that are not verbatim repeats (#3, #4, #16, #17), invented trip details, rarity overclaims and out-of-scope places such as Ulaanbaatar (#5, #17).

---

## 2. Top remaining defect classes

| # | Defect class | Pieces | Count | Detected today? |
|---|---|---|---|---|
| 1 | Contrast frames and stock AI lines ("not X, it is Y", "worth sitting with", "isn't filler", "The mountain remembers", aphorism closes) | #0, #1, #4, #5, #7, #8, #9, #10, #11, #12, #14, #15, #16, #17, #18, #19 | 16/20 | No (AI-tells 4.45; 0/20 ≥7) |
| 2 | Blog FAQ below 3 items (1: #4, #5, #14, #15; 2: #16, #17, #18) | 7 blogs | 7/8 | **Yes: F16 holds them**, but the writer and repair do not fix it |
| 3 | Invented trip or product details: optional activities as fixed (#14, #16, #18); "first night" (#14, #19); "southern tip" (#14); "darkening treeline" (#19); "same day, adjustable pace" and parallel supervision (#5, #15); "families can calibrate" (#17); "mid-morning" (#11) | #5, #11, #14, #15, #16, #17, #18, #19 | 8 (7/8 blogs) | Partly (F9 on #5, #19) |
| 4 | Rarity and uniqueness overclaims; seed "many" becomes "most" or "no equivalent" ("unlike anything else in Central Asia", "almost anywhere else on earth", "categorically different", "farther south") | #5, #14, #15, #17, #18, #19 | 6/8 blogs | No (the rarity tripwire flags informationally only) |
| 5 | Punakha siting intent, symbolism or present-tense authority: "three sides" and landscape symbolism (#0); "permanence endures" (#1); "never been set aside" (#7); "defensibility" (#9); "three centuries", "kingdom's founding" (#12); "understood exactly" (#13). Meta says "still active / remains… center" in #1, #9 and #13. | #0, #1, #7, #9, #12, #13 | 6/6 Punakha | Partly (F1 held #13 only) |
| 6 | Repair artifacts: orphan duplicate line (#3), Sod Camp duplicated into the wrong section (#4), "day three. On day three" (#16), "few hundred" twice (#17), 70% figure repeated (#14, #16) | #3, #4, #14, #16, #17 | 5 | Partly (repeat detector catches #14 and #16 only) |
| 7 | Family brand omits that the Tsaatan access is physically demanding and multi-hour, while pitching the visit to children | #5, #15, #17, #19 | 4/4 Terra blogs | No |
| 8 | Tenant voice miss. Trail Pulse is a calm or coach explainer and pastes "movement and energy delivered well" (#3, #8, #11). Terra uses classroom framing (#5, #17, #19). WildKind lacks habitat content (#0, #9, #13). | 9 pieces | 9/20 | No (F15 fired only on #15) |
| 9 | Wrong place or scope: Uran Togoo or Bulgan written as part of Khövsgöl (#14, #16); "Mörön… Province" (#18); Ulaanbaatar named (#5, #17); Soviet layout misattributed (#16, #19) | #5, #14, #16, #17, #18, #19 | 6/8 blogs | No (Ulaanbaatar is not on the out-of-scope list) |
| 10 | Cross-piece templates: "That single fact is worth sitting with" (#5 = #15); the "worth sitting with" family ×3 (#5, #15, #16); SEO title #4 = #18; Kuang Si "filler" frame again (#11); "movement and energy delivered well" (#3, #11) | 7 pieces | 5 templates | No |
| 11 | Instruction leak: "One ruined site, one date, one fact. It does not need more than that." | #19 | 1 (r1: 5) | No (x_instruction_leak missed it) |
| 12 | Configured CTA line missing (paraphrased) | #19 | 1 | No (`check_cta` passes; F9 held it for other reasons) |

## 3. Gate behaviour

- **Approved but heavy (2):** #3 and #8, both Trail Pulse. #3 carries a visible repair artifact. No gate checks Trail Pulse's energetic voice, and the brand-pack phrase pasted in as copy is not flagged.
- **Held but light (2):**
  - #7 (F9_cta_fact). The flag is correct: "never been set aside" contradicts the seed. The defect is a one-sentence fix.
  - #13 (F1_grounding). The flag is correct ("understood exactly what that meant"). Same "correct flag, wrong action" pattern as S233 #9.
  - Sentence-level repair (AA-769) on these flags would turn both into approvals.
- **Blogs:** 8/8 held, and 8/8 are heavy, so the gate is right on every blog. 7 of the holds include F16_faq. #19 was held on F9 only, and it is the one blog with 3 FAQs.
- **Trail Pulse is the only cell where the gate is worse than the panel**: 3/3 approved, panel 1/3 light. This matches S233 (3/3 approved, 0/3 light).

## 4. Next fixes, ranked

| Rank | Fix | Targets (class) | Expected effect |
|---|---|---|---|
| 1 | **FAQ generation, not just the FAQ gate.** F16 now blocks correctly, but the writer still produces 1–2 FAQs. Make "≥3 Q/A" a hard writer contract, and when F16 fails, regenerate only the FAQ section (grounded in the seed, scoped days only). | 2 | Removes the structural reason all 7 F16 blogs are held. Necessary, but not enough for light. |
| 2 | **Repair-pass integrity.** After any repair, run a near-duplicate sentence check (normalised n-gram, not verbatim), a section-placement check (a moment's place must stay under its own H2) and the dangling-antecedent check. Fail closed. | 6 | Removes #3's artifact (the main defect of a false pass) and 4 blog artifacts. |
| 3 | **Trip-fact grounding in F9/F1 for blogs.** Flag as unsupported: "optional" dropped from activities, ordinal-night claims ("first night"), standing-position claims, parallel-activity or supervision promises, and the claim that an access caveat in the seed was omitted for a family brand. Add Ulaanbaatar and other places outside the scoped days to the scope list. | 3, 7, 9 | Fixes the invented-trip cluster on 7/8 blogs and the Terra safety omission. |
| 4 | **Anti-template and contrast-frame density (S233 fix 6, still open).** Blocking warning above 1 contrast frame per 150 words; stock-line list ("worth sitting with", "isn't filler", "The X remembers", "not a metaphor"); n-gram overlap across sibling pieces; ban verbatim brand-pack phrases in copy. | 1, 10 | The only lever for as-is (0% in all 3 rounds). AI-tells has been stuck at 4.45–4.54. |
| 5 | **Rarity quantifier guard.** A deterministic check that the seed's quantifier is kept ("many" must not become "most", "no equivalent" or "anywhere on earth"), and promote unsourced "unlike anything… / almost anywhere" to a hard error. | 4 | 6/8 blogs; cheap and deterministic. |
| 6 | **Tenant voice rubric as a blocking check (S233 fix 7, still open).** Trail Pulse: energetic and social, no wellness-coach thesis, no pasted core idea. Terra: no classroom framing, include the child's experience. WildKind: habitat present. | 8 | Closes the last false-pass cell (Trail Pulse) and lifts approval precision from 80% toward ~90%. |
| 7 | **Sentence-level repair on correct F1/F9 flags (AA-769).** Rewrite the flagged sentence instead of holding the piece. | gate | Converts #7 and #13 (light, correctly flagged) to approved. Recall goes from 80% to ~100%. |
| 8 | **Punakha present-tense authority check.** The seed already says the capital moved to Thimphu in 1955. Add an F1/meta check that flags "remains / still active… administrative / governmental" and computed spans ("three centuries") that contradict seed dates, and give the writer the span as a stated fact (1637/38–1955). | 5 | Fixes 3 Punakha metas plus #7 and #12; moves Punakha LinkedIn closer to as-is. |
| 9 | **CTA configuration.** Make `check_cta` require the literal CTA line (#19). Review the A&H "travel designer" and Trail Pulse "itinerary and dates" CTAs: the fidelity audit reads them as unsupported promises. | 12 | Small; removes a recurring audit flag on 9 pieces. |

Fixes 1–3 are needed before any blog can be light. Fix 4 is the only path to the ≥30% as-is bar on either channel. Fixes 6–7 are about the gate: it is now selective (agrees with the panel on 16/20), and what remains is to stop the Trail Pulse false passes and to repair, rather than hold, light pieces that are correctly flagged.
