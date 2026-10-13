# T9 commercial quality panel, S233 round 1: 20 pieces vs the S232 bar

**Input.** `.tmp-session/s233/pieces_r1.json`: 20 pieces across 5 briefs, 4 tenants and 2 channels. WildKind is included for the first time.

| Brief | Tenant / channel | Pieces | Seed |
|---|---|---|---|
| Tiger's Nest (day 9) | Terra LinkedIn | #0, #7, #11 | 1 moment, 9 place-background facts |
| Kuang Si Falls (day 2) | Trail Pulse LinkedIn | #1, #6, #10 | 1 moment, 10 place-background facts |
| Punakha Dzong (day 4) | A&H LinkedIn | #2, #9, #14 | 1 moment, 9 place-background facts |
| Punakha Dzong (day 4) | WildKind LinkedIn | #3, #8, #12 | same seed as A&H |
| Mongolia days 3–14 | A&H blog | #4, #15, #17, #18 | 9 moments, about 60 facts; **the anchor moment (monastery ruins) has 0 place facts** |
| Mongolia days 3–14 | Terra blog | #5, #13, #16, #19 | same seed |

Piece numbers are the 0-based index in `pieces_r1.json`.

**Method.** Same as S232:
- **4 lenses:** editor, tenant brand lead, channel specialist, paying client. That gives 80 votes.
- **Verdict:** the majority vote. A 2–2 tie gets the stricter label.
- **Light edit:** ≤10 minutes, ≤3 sentences changed, no fact research.
- **Scores:** 7 dimensions plus an overall score, each /10.
- **Fidelity:** I checked every claim against the seed, the "Place background" lines and the brand pack.

**Caveat.** This is one rater simulating 4 lenses, and the S232 panel was a separate run. Compare the two directionally, not to the decimal (see §7).

---

## 0. Bottom line

1. **Still not commercial-grade.**
   - 0/20 pieces are publish-as-is. 6 (30%) are light edit, 14 (70%) heavy edit, 0 reject.
   - Overall is 5.33 (S232: 5.20). The best piece scores 6.2; S232's best was 7.0.
   - The D1 bar needs ≥80% as-is or light and ≥30% as-is. We are at 30% and 0%.
2. **The S232 P0 fixes worked on the fatal defects.**
   - Truncation 0/20 (S232: 5/20 blogs).
   - Blog CTA before `## FAQ` 8/8 (S232: 7/20).
   - Brand-name leaks 0/20, forbidden words 0/20, mislocated places 0/20 (S232: 7/20 Pawangka).
   - LinkedIn fidelity rose to 6.6, because the Place background lines are used and mostly respected.
3. **The two channels moved in opposite directions.**
   - LinkedIn: 6/12 light (50%). Terra Tiger's Nest is 3/3 light.
   - Blogs: 0/8 light (S232: 5/20). Every blog is heavy edit, with new defect classes:
     - "Gobi" and "price" in 8/8 titles and metas, although the scope excludes the Gobi and no piece contains a price;
     - invented physical state of the ruins in 6/8;
     - "content seed" printed in 2/8.
4. **AI-tells did not improve** (4.45; S232: 4.75). 0/20 pieces score ≥7. The same brief still produces the same opening line, word for word.
5. **The gates approve far more and are slightly more precise.**
   - Approval rate 60% (S232: 18%), precision 42% (S232: 33%), recall 83% (S232: 25%).
   - Both approved blogs (#5, #17) are heavy edit with scope and product-truth fails.
   - "Hold everything" would still agree with the panel more often (14/20) than the gates do (12/20).

**Decision.** Do not ship blogs. LinkedIn is close for brand–seed pairs with a rich place card (Terra Tiger's Nest, A&H and WildKind Punakha). The remaining blockers are length, hashtags, templated openers and repair duplicates; all of them can be fixed deterministically. Fix the blog keyword/scope and the anchor-moment problem (§6, fixes 1–2) before the next round.

---

## 1. Commercial verdict

### 1.1 Overall

| | Publish as-is | Light edit | Heavy edit | Reject |
|---|---|---|---|---|
| Pieces (n=20) | 0 (0%) | 6 (30%) | 14 (70%) | 0 (0%) |
| Lens votes (n=80) | 0% | 35% (28) | 61% (49) | 4% (3) |

Five pieces split 2–2 and took the stricter label: #3, #10, #12, #14 and #19. If every tie counted as light, light would be 83% on LinkedIn (10/12) and 13% on blogs (1/8).

### 1.2 By channel and tenant

| Cell | n | Approved | Approved: L/H/R | Held: L/H/R | Light votes | Overall /10 |
|---|---|---|---|---|---|---|
| Terra LinkedIn (Tiger's Nest) | 3 | 3 | 3/0/0 | – | 75% | 6.07 |
| A&H LinkedIn (Punakha) | 3 | 1 | 1/0/0 | 1/1/0 | 67% | 5.77 |
| WildKind LinkedIn (Punakha) | 3 | 3 | 1/2/0 | – | 58% | 5.80 |
| Trail Pulse LinkedIn (Kuang Si) | 3 | 3 | 0/3/0 | – | 17% | 4.93 |
| Terra blog (Mongolia) | 4 | 1 | 0/1/0 | 0/3/0 | 12% | 5.08 |
| A&H blog (Mongolia) | 4 | 1 | 0/1/0 | 0/3/0 | 0% | 4.65 |
| **LinkedIn** | 12 | 10 | 5/5/0 | 1/1/0 | 54% | 5.64 |
| **Blog** | 8 | 2 | 0/2/0 | 0/6/0 | 6% | 4.86 |
| **All** | 20 | 12 (60%) | 5/7/0 | 1/7/0 | 35% | 5.33 |

By tenant, both channels pooled:

| Tenant | Light | Overall |
|---|---|---|
| Terra | 3/7 | 5.50 |
| WildKind | 1/3 | 5.80 |
| A&H | 2/7 | 5.13 |
| Trail Pulse | 0/3 | 4.93 |

### 1.3 Per piece

| # | Cell | Gate | Votes E/B/C/K | Verdict | Overall | Deciding defects |
|---|---|---|---|---|---|---|
| 0 | Terra LI | approved | L L H L | Light | 6.2 | 463 words; 8 hashtags including "#PakoTaktsang"; first paragraph 278 characters |
| 7 | Terra LI | approved | L L H L | Light | 6.1 | 433 words; "That detail is worth sitting with."; first paragraph 391 characters |
| 11 | Terra LI | approved | L L H L | Light | 5.9 | "#PajoTaktsang"; "formally known in Dzongkha as 'Taktsang'" (wrong); 7 hashtags |
| 2 | A&H LI | approved | L L H L | Light | 5.9 | Duplicated confluence sentence (a repair artifact); 4 contrast frames |
| 9 | A&H LI | **held** | L L H L | Light | 5.9 | Duplicate sentence; "difficult to overstate"; "continuous institutional use since its founding" (unsupported) |
| 8 | WildKind LI | approved | L H L L | Light | 6.0 | 5 hashtags; "worth sitting with"; architecture rather than nature |
| 14 | A&H LI | held | H L H L | Heavy (tie) | 5.5 | Duplicate sentence; dzong "intended to be … the winter home of the Je Khenpo" from its founding (anachronism); "It is argument." |
| 3 | WildKind LI | approved | L H H L | Heavy (tie) | 5.8 | 439 words; "He did not choose that site by accident"; off-core for the brand (no habitat or nature) |
| 12 | WildKind LI | approved | L H H L | Heavy (tie) | 5.6 | "gho for men, kira for women among those who choose it" (misstates the rule); 6 hashtags |
| 10 | Trail LI | approved | L H L H | Heavy (tie) | 5.2 | Calm consultancy voice for an "energetic, lightly playful" brand; two-line contrast hook |
| 1 | Trail LI | approved | H H H H | Heavy | 4.9 | Operator-to-operator essay; invented fatigue timeline ("day four and five"); off-voice |
| 6 | Trail LI | approved | H H H H | Heavy | 4.7 | "Not as filler. Not as an afterthought."; "clients in the 25–40 range" (brand segment leaked) |
| 19 | Terra blog | held | L L H H | Heavy (tie) | 5.6 | Gobi and "Price" in title and meta with no price; "visitors may witness shamanistic practices during their time" |
| 5 | Terra blog | approved | H H H H | Heavy | 5.2 | Trip name with "Gobi" in the body; broken meta; social proof; duplicate sentence; classroom framing |
| 17 | A&H blog | approved | H H H H | Heavy | 5.2 | "ruins that have never been rebuilt"; "the kind of access that takes time to arrange"; Gobi in the CTA |
| 4 | A&H blog | held | H H H H | Heavy | 4.9 | "There is no interpretive reconstruction here"; only 2 FAQs; meta 164 characters; Gobi |
| 16 | Terra blog | held | H H H H | Heavy | 4.9 | "The walls are gone because someone decided they should be gone."; invented pacing promise; textbook/exam framing |
| 13 | Terra blog | held | H H H R | Heavy | 4.6 | **"The content seed describes…"**; "no reconstruction"; invented permit handling |
| 15 | A&H blog | held | H H H R | Heavy | 4.3 | Title "…Price of Memory"; ungrammatical meta; "Its destruction was total." |
| 18 | A&H blog | held | H H H R | Heavy | 4.2 | **"The content seed for this journey notes…"**; invented "foundations, scattered stone"; meta 174 characters |

### 1.4 S232 vs S233 side by side

| Metric | S232 (n=49) | S233 r1 (n=20) | Change |
|---|---|---|---|
| Publish as-is | 0% | 0% | = |
| Light edit | 24% | 30% | +6 pp |
| Heavy edit | 67% | 70% | +3 pp |
| Reject | 8% | 0% | −8 pp |
| Light votes | 31% | 35% | +4 pp |
| Overall /10 | 5.20 | 5.33 | +0.13 |
| Best piece | 7.0 | 6.2 | −0.8 |
| Fidelity | 5.0 | 5.80 | +0.8 |
| AI-tells | 4.75 | 4.45 | −0.3 |
| Approval rate | 18% | 60% | +42 pp |
| Approval precision | 33% | 42% | +9 pp |
| Light-edit recall | 25% | 83% | +58 pp |
| LinkedIn light (pieces) | 7/29 (24%) | 6/12 (50%) | up |
| Blog light (pieces) | 5/20 (25%) | 0/8 (0%) | **down** |

---

## 2. Dimension averages (/10)

| Dimension | S232 | S233 all | S233 LinkedIn | S233 blog | Change | r with overall (S233) |
|---|---|---|---|---|---|---|
| Fidelity | 5.0 | **5.80** | 6.62 | 4.56 | +0.8 | 0.88 |
| Specificity | 5.2 | **6.72** | 6.67 | 6.81 | +1.5 | 0.50 |
| AI-tells | 4.75 | **4.45** | 4.50 | 4.38 | −0.3 | 0.70 |
| CTA | 5.6 | 6.05 | 6.21 | 5.81 | +0.45 | 0.59 |
| Channel craft | 5.8 | **4.70** | 5.04 | 4.19 | −1.1 | 0.47 |
| Brand voice | 6.4 | 5.90 | 5.79 | 6.06 | −0.5 | 0.43 |
| Hook | 6.4 | 5.97 | 5.83 | 6.19 | −0.4 | 0.18 |
| **Overall** | 5.20 | **5.33** | 5.64 | 4.86 | +0.13 | – |

**What moved**
- **Specificity +1.5 and LinkedIn fidelity +1.6** are the clearest gains, and they come from the Place background lines.
  - Terra Tiger's Nest uses about 12 checked facts in about 440 words (≈2.7 per 100 words), with 0 invented place facts.
  - The Punakha posts use 8–10 facts each.
- **Fidelity is still the strongest predictor (r=0.88).** Blogs fell to 4.56 because their angle is anchored on the one moment with no place card (§4, G2).
- **Channel craft −1.1** has two causes:
  - LinkedIn posts got longer: 233–463 words, mean 369. Only 1 of 12 is in the 120–250 band; S232's range was 183–330.
  - 8/12 posts carry more than 3 hashtags, and every blog has "Gobi"/"price" SEO surfaces.
- **Brand voice −0.5** is pulled down by Trail Pulse (4.33): the angle prescribed a "calm, considered LinkedIn voice" for an energetic brand.
  - A&H is the best fit: 6.83 on LinkedIn and 6.0 on blogs.
- **AI-tells −0.3.**
  - With the same conservative regex style as S232, I count 52 contrast frames, 2.6 per piece (S232: 2.8). 8/20 pieces have 3 or more (S232: 23/49).
  - Stock lines and identical openers persist (§4, G4).
- **Thresholds:**
  - 0/20 pieces score ≥7 on AI-tells; 6/20 score ≥7 on fidelity (S232: 3/49).
  - Only specificity (6.72) clears the D1 floor of 6.5 on average; every other dimension is below it.

---

## 3. Gate vs panel

| | Panel light | Panel heavy | Panel reject |
|---|---|---|---|
| Approved (12) | 5 (#0, #2, #7, #8, #11) | 7 (#1, #3, #5, #6, #10, #12, #17; 3 of them ties) | 0 |
| Held (8) | 1 (#9) | 7 | 0 |

- **Approval precision 5/12 = 42%** (S232: 33%; D1 target ≥85%).
  - LinkedIn 5/10 = 50%; blog 0/2 = 0%.
- **Recall 5/6 = 83%** (S232: 25%; target ≥70%). Recall now meets the bar because the gates approve much more.
- **Agreement:** the gates agree with the panel on 12/20 pieces. "Hold everything" would agree on 14/20.
- **Repeated false pass: Trail Pulse 3/3 approved, panel 0/3 light.**
  - No gate checks brand voice against the tenant rubric.
  - The brand packs in this input still have `system_prompt: null` for all 4 tenants. If F9 and Jev still fall back to `AA_BRAND_IDENTITY_PROMPT`, the rubric half of S232 P0-1 is not live. **Verify.**
- **Blog false passes: #5 and #17 were approved with:**
  - Gobi in the title, meta and body;
  - "ruins that have never been rebuilt" (#17);
  - "tends to stay with children longest" (#5);
  - "the kind of access that takes time to arrange properly" (#17, which breaks A&H's "Avoid: overpromise rare access").
  
  F9 does not treat keyword/scope as a fact, and no deterministic scope gate exists.
- **False hold: #9.** F9_cta_fact held it for one superlative ("difficult to overstate") and one unsupported clause. This is the same "correct flag, wrong action" pattern as S232 §B2.
- **Gates on the final attempt:**
  - F9_cta_fact fired on 8/20 (40%; S232: 80%).
  - F4_seo_surface fired on 4/8 blogs (#4, #13, #15, #18). It did not fire on #5, whose meta is broken ("Planning a Khovsgol and Gobi tour Mongolia price research starts here"), so F4 still checks format only.
- **No gate caught:**
  - the "content seed" leaks (#13 and #18 were held for other codes);
  - the repair-inserted duplicate sentences (#2, #9, #14, #5);
  - the misspelled place hashtags (#0, #11);
  - LinkedIn length or hashtag count.

---

## 4. Top remaining quality gaps, ranked by impact

### G1. The SEO keyword overrides the scope: "Khovsgol and Gobi tour Mongolia price" (8/8 blogs)
**Impact:** every blog fails D2 Scope, and the "price" title is misleading because no piece has a price.
- #15 title: "Khovsgol and Gobi Tour Mongolia Price of Memory". Meta: "Discover what a Khövsgöl and Gobi tour Mongolia price in cultural depth — from volcanic craters to Tsaatan camps…" (ungrammatical).
- #5 body: "This piece follows the route from Day 3 through Day 14 of the *Mongolia: Khövsgöl Lake and Gobi Desert — 15 Days* itinerary". The scope says "must not promise, name or imply any place … even if the TRIP name does".
- #15 CTA: "The Khövsgöl and Gobi tour Mongolia price in terms of cultural depth is not measured in distance covered…"
- Gobi also appears in the body or FAQ of 7/8 blogs, and "price" in 8/8 titles.

**Related:** all 6 Punakha LinkedIn titles say "Bhutan Meditation Retreat". The seed says nothing about meditation, and the WildKind #3 meta sells it: "a WildKind Travel Bhutan meditation retreat brings you to Punakha Dzong". This needs checking against the tour record.

**Cause:** the keyword is taken from the trip, not from the scoped moments. F4 rewards the keyword being present, and the writer is asked to obey both the keyword and the scope, so the keyword wins. **(keyword source + gate)**

### G2. The angle anchors the blog on the one moment with no place card, so the writer invents the ruins (6/8 blogs)
**Impact:** blog fidelity is 4.56. The seed's location line is "ruins of an ancient monastery, Mongolia", with no name, no place background and no facts beyond "destroyed during the political purges of 1937". Both angles ("What Silence Leaves Behind", "What One Ruined Monastery Tells Families") make it the hook and the climax.
- Invented state of the ruins, in 6 of 8:
  - "There is no reconstruction here, no interpretive comfort offered by heritage management." (#15)
  - "There is no interpretive reconstruction here" (#4); "There is no reconstruction here, no interpretive centre" (#13)
  - "the quiet weight of ruins that have never been rebuilt" (#17)
  - "What remains at the site is the architecture of loss: foundations, scattered stone, the outline of a place…" (#18)
  - "The walls are gone because someone decided they should be gone." (#16)
  
  "There is no reconstruction" is the same invented claim S232 found in #22.
- Facts borrowed from the "other trips" lines: Erdene Zuu is used in 5/8 (#4, #5, #15, #17, #18). In #18 the borrowing is misattributed and leaks the prompt: "The content seed for this journey notes that thousands of monks once lived within such complexes".

**Cause:** the angle step (T8) is allowed to pick a moment with zero facts as the anchor. The sibling lines are the only rich text about monasteries in the seed. **(angle + seed)**

### G3. Blog product-truth and social-proof inventions (7/8 blogs, 0/12 LinkedIn)
- Social proof:
  - "This is the section of the journey that tends to stay with children longest" (#5)
  - "the one that tends to sit longest in the mind afterward" (#16)
- Invented service: "Permit logistics are part of the planning conversation and not something families need to organise independently." (#13)
- Trip-design promise built from the brand segment: "The trip is designed for families with children aged 7 to 16 … paced to be engaging … without being physically overwhelming for younger ones" (#16)
- Access overpromise, against an A&H "Avoid" rule: "the kind of access that takes time to arrange properly" (#17); "depth, comfort, and meaningful access" (#18)
- Optional activities presented as included: "The day also includes visits to local nomadic families" (#13). The seed lists them as "Optional activities".

**Cause:** the FAQ prompt invites questions the seed cannot answer (age suitability, physical demand, what the price includes). The writer answers them from the brand pack's `customer_segment`, and F9 passed two of these pieces. **(prompt + gate)**

### G4. Templated openers and AI phrasing (AI-tells 4.45, 0/20 ≥7)
- The same brief produces the same first line:
  - Terra LinkedIn, 3/3 word for word: "There is a checkpoint before you reach the inner temples of Paro Taktsang." (#0, #7, #11)
  - A&H LinkedIn #2 and #14, identical: "There is a question worth sitting with before you arrive at Punakha Dzong: why here?" (#9: "…: why here?")
  - Trail Pulse 3/3 open on the industry: "Most active travel brands don't struggle with…" (#1); "Active travel brands have a pacing problem." (#6); "There's a mistake active travel brands make…" (#10)
  - A&H blogs 3/4 open "1937." Terra blogs 4/4 open "On Day 14 of…".
- Stock phrases and contrast frames:
  - "worth sitting with" in 4 pieces (#2, #7, #8, #14)
  - "Not as filler. Not as an afterthought. As a built-in recovery window" (#6)
  - "The setting is no longer backdrop. It is argument." (#14)
  - "That's not filler. That's a structural decision." (#10)

**Cause:** the angle's `best_final_style` dictates the opening literally ("Open with the concrete operational fact … cameras and bags…", "Open with the weight of the date — 1937"). The banned list does not cover contrast frames or these stock lines, and F9_brand_style still does not block. **(angle + prompt + gate)**

### G5. LinkedIn channel craft (craft 5.04)
- **Length:** 1/12 posts within 120–250 words. #0 has 463 and #3 has 439.
- **Hashtags:** 8/12 have more than 3. Two misspell the place: "#PakoTaktsang" (#0), "#PajoTaktsang" (#11).
- **Mobile fold:** the first paragraph is over 140 characters in 4/12 (#0 278, #7 391, #11 326, #12 280).
- **Trail Pulse writes to competitors in a B2B register:**
  - "If you work in travel planning, operate active itineraries, or recommend trips to clients in the 25–40 range…" (#6). The brand segment leaks verbatim.
  - "Most active travel brands don't struggle with choosing good destinations." (#1)
- **Positive:** 0/12 use markdown, and 4/12 now contain a real question (S232: 0/29).

**Cause:** there is still one LinkedIn spec with no length or hashtag cap, and no per-brand-type variant (S232 P1-7 not done). **(channel spec + gate)**

### G6. Brand themes drift even with the brand pack
- **Trail Pulse (brand voice 4.33):** the angle prescribed "Calm, considered LinkedIn voice — direct sentences, no hype". The brand voice is "Energetic, Fresh, … Lightly playful", and its themes are social, group and food. The 3 posts never mention the group or other travellers, and only #1 names food ("lunch … at the View Café").
- **Terra blogs, 4/4 use classroom framing** although the angle said "Do not use classroom or school-trip framing":
  - "gives children a physical sense of geological scale that no diagram in a textbook can replicate" (#16)
  - "arriving not in a classroom but in the field" (#5)
  - also #13 "For a child who has studied geology in school", #16 "answering a question about it in an exam" and #19 "a book or a documentary".
- **WildKind** got a dzong-architecture brief. The posts are respectful but not nature-led: "the decision to place power and practice at a confluence rather than on a summit or behind a wall" (#8).

**Cause:** the angle tone overrides the brand voice, and the slate assigns a seed that does not fit the brand. Nothing checks the tenant's core themes. **(angle + slate + gate)**

### G7. The repair loop inserts duplicate sentences (4/20; all 3 A&H Punakha posts at attempt 3)
- #2: "Punakha Dzong stands at the confluence of the Pho Chhu and Mo Chhu — a setting that is as striking in its physical beauty as it is significant…" This comes one paragraph after the confluence was already described.
- #14: "That choice was not incidental. Punakha Dzong was founded at the confluence of the Pho Chhu and Mo Chhu rivers…" This immediately repeats the previous paragraph.
- Also #9 ("The Pho Chhu and Mo Chhu — the Male and Female Rivers — meet at the foot of a structure…") and #5 (the optional-activities sentence twice).

**Cause:** the repair satisfies F9_cta_fact by pasting the seed's "Why it matters" line instead of editing in place. **(repair prompt)**

### G8. Seed hygiene errors reach the text
- **Conflicting place cards:** Lake Khövsgöl holds "two percent", "0.4 percent" or "1–2 percent" of the world's fresh surface water, depending on the line. #5 and #17 print "two percent".
- **Impossible day order:** Sod Camp (Khövsgöl) is labelled Day 3 and Mörön lunch Day 4.
  - #5, #13, #17 and #19 follow the seed and imply a backtrack of about 100 km.
  - #15, #16 and #18 silently reorder the stops.
- **Scope line order:** it lists "ruins of an ancient monastery → Sod Camp → …", with Day 14 first.
- **Naming slip:** "Paro Taktsang is formally known in Dzongkha as 'Taktsang'" (#11) inverts the naming line.

**Cause:** the seed builder does not reconcile facts across cards, or validate the order of days. **(seed)**

---

## 5. D2 hard fails

| Check | S233 r1 | Which pieces | S232 |
|---|---|---|---|
| Brand integrity (other or invented brand, AA expansion) | **0/20** | – | 2/49 |
| Place integrity (place moved) | **0/20** | – | 7/20 Pawangka posts |
| Scope (title, meta or body outside the seed scope) | **8/8 blogs** confirmed (Gobi + "price") | #4, #5, #13, #15, #16, #17, #18, #19 | 10/10 Terra blogs |
| Scope, unverified: "Bhutan Meditation Retreat" title/meta not supported by the seed | 6/6 Punakha posts | #2, #3, #8, #9, #12, #14 | – |
| Product truth (trip promises, social proof, access) | **7/20** (7/8 blogs, 0/12 LinkedIn) | #4, #5, #13, #16, #17, #18, #19 | ~80% flagged by F9 |
| Completeness (truncation, artifacts) | **0/20** | – | 5/20 blogs |
| CTA (once; blog CTA before `## FAQ`) | **0/20** fail | – | 13/20 blogs |
| Sensitive naming (display names) | **2/20**; Mörön is spelled correctly in 8/8 | #0 "#PakoTaktsang", #11 "#PajoTaktsang" | 5/8 Pawangka "in China" |
| *New:* prompt leakage ("content seed") | **2/20** | #13, #18 | – |
| *New:* invented place facts (no card or sibling line supports them) | **6/8 blogs** | #4, #13, #15, #16, #17, #18 | – |
| *New:* duplicate sentence (repair artifact) | **4/20** | #2, #5, #9, #14 | – |

**Pieces with at least one confirmed hard fail: 10/20** (all 8 blogs, plus #0 and #11). Counting the unverified "meditation retreat" titles, it is 16/20. **LinkedIn without hard fails: #1, #6, #7, #10.**

---

## 6. Next fixes, ranked by expected effect

| # | Fix | Addresses | Expected effect (estimate) |
|---|---|---|---|
| 1 | **Scope the SEO keyword.** Build the blog keyword from the scoped moments (e.g. "Lake Khövsgöl tour with Tsaatan reindeer herders"), never from the trip name. Drop "price" unless the seed carries price data. Add a deterministic scope gate: every place token in the title, meta, H2s and body must belong to the scope; "Gobi" or the trip name triggers a fail. Check the "Bhutan meditation retreat" keyword against the tour record. | G1, D2 Scope | Removes 8/8 blog scope fails. #19 and #17 would likely move to light. Craft 4.2 → ~5.5 on blogs. |
| 2 | **Anchor contract at T8.** The hook or climax moment must have ≥3 place-card facts; otherwise pick another moment, or generate and verify a card first. For "ruins of an ancient monastery" the site has to be identified, or the moment dropped. Strip the "other trips" lines from the writer's seed, or reduce them to one line. Ban sibling proper nouns (Erdene Zuu, Gandan) in the body. | G2 | Removes the invented ruin state (6/8) and Erdene Zuu borrowing (5/8). Blog fidelity 4.6 → ~6.5. This is the largest single lever for blogs. |
| 3 | **Deterministic hygiene gates.** Ban "content seed", "the seed", "source itinerary". Add a duplicate-sentence detector (Jaccard >0.6 within a piece). Spell-check hashtags against place-data names. Change the repair prompt to "edit in place, never append the seed line". | G7, D2 leakage/naming | Hard fails 10 → ~2 on this set. A&H Punakha 3/3 light. |
| 4 | **LinkedIn spec v2 by brand type.** Hard caps: 120–250 words (A&H ≤300), ≤3 hashtags, first line ≤140 characters. Trail Pulse gets a consumer/social register, or LinkedIn is off by default. The angle's `best_final_style` may not set a tone outside the brand's voice adjectives (validate at T8). | G5, G6 | LinkedIn craft 5.0 → ~6.5. Trail Pulse 0/3 → ~2/3 light. LinkedIn light 50% → ~75%. |
| 5 | **FAQ and product-truth guard.** Allow only FAQ questions whose answer is in the seed (no age suitability, "what the price includes" or "how demanding" without data). Regex-block social proof ("tends to stay", "most families", "children generally") and service promises ("not something families need to organise"). `customer_segment` describes the audience and must never become a trip claim. | G3 | Product-truth fails 7/8 → ≤2/8 blogs. |
| 6 | **Anti-template.** T8 must not prescribe a literal first sentence. Rotate opener types per brief. Add blocking warnings for contrast-frame density (>1 per 150 words) and stock lines ("worth sitting with", "That's the … worth paying attention to", "It is argument") that feed the repair. | G4 | AI-tells 4.45 → ~6. It removes the 3/3 identical openers. |
| 7 | **Tenant rubric live in F9 and Jev.** All 4 brand packs here have `system_prompt: null`. Confirm the judges are not on the AA fallback. If they are, compile the rubric at T0 (S232 P0-1). Add a core-theme check (Trail: group/food/active; WildKind: habitat/nature; A&H: guiding/stays/no rare access; Terra: no classroom framing). | G6, §3 Trail false passes | Approval precision 42% → ~65%. |
| 8 | **Seed hygiene.** Reconcile numeric conflicts across a place's cards and keep one canonical value. Validate the day order against geography. Order the scope line by day. | G8 | Removes the 2% error and the route backtrack; small effect on overall. |

**Expected trajectory:**
- Fixes 1–3 bring blogs from 0/8 to ~3/8 light and LinkedIn to ~8/12.
- Adding 4–6 gets close to the D1 light share (~75–80%), but not the ≥30% publish-as-is bar. As-is needs AI-tells ≥7, and that only fixes 4 and 6 address.
- Re-run the same 5 briefs, plus 1 thin and 1 rich new brief, to confirm.

---

## 7. Caveats

- One rater simulated 4 lenses. Votes within a piece are correlated, so the 2–2 ties (5 of them) carry most of the uncertainty.
- n=20 covers 5 briefs at about 3–4 samples each. Brief effects (Tiger's Nest rich vs Mongolia ruins thin) dominate the tenant and channel effects. Blogs here are all one Mongolia brief, so "blogs 0/8" means "this brief", not blogs in general.
- My scoring is likely somewhat stricter than S232 on channel craft (length and hashtags are counted against the D3 bar). The fidelity and specificity gains are robust to this, because they rest on traceable facts.
- The contrast-frame counts come from a conservative regex and are only roughly comparable to S232's.
- "Bhutan meditation retreat" may be the real tour name. I could not verify it from the seed.
- **Not checked:** the attempt-1 vs final diffs, and the F9 reasons (`failed` holds codes only).
