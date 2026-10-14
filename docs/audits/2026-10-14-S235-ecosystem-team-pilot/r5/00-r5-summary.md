# T9 checkpoint r5 (S235, 14/10/2026)

**Ran with:** real tenant path (public tenant API → `t9_write` jobs on the **worker**), 20 pieces, same 6 requests as S234 r4 (Terra LinkedIn angle regenerated — confound). Cost **$1.064** (pieces $1.032 + angle regen $0.032), hard stop $1.50. Code: main `dcd4e03` (AA-776, AA-785, AA-786, AA-774, AA-773, AA-775 deployed; api :584 / worker :139).
**Scored by:** deterministic `r5_measure.py` (same hard-error script as S234) + local Claude panel ($0): 4 independent lenses (editor, brand-lead, channel, client; majority verdict, tie → worse) + fidelity auditor + product-truth auditor.

| | S234 r4 | **S235 r5** |
|---|---|---|
| Light edit or better (majority) | 55% | **70%** (14/20; target ≥60%) |
| LinkedIn / blog light | 10/12 · 1/8 | **11/12 · 3/8** |
| Mean overall (4 lenses) | 5.74 | **5.96** |
| Core hard errors | 4 | **2** |
| Reverse flips offered↔included (product-truth) | 4/8 blogs | **0/8** |
| F1 year-form hits / F9 citation notes | – | 0 / 0 (prompt f9_v1.1) |
| Seed visiting/practical bullets | 8 per blog seed | **0** |
| Blog seeds with Status: OFFERED | 0/8 | **8/8** |
| promises_an_option warns | 8/8 (23 FP) | **0/8** |
| Pace sentences Terra / A&H | 10 / 2 | **1 / 0** (measure); panel: 2 + 2 clear-cut |
| Cost per 20 | $1.146 | **$1.032** |

## Remaining defects (root causes)
1. **Repair deletes a setup sentence** → openers/FAQ answers point at missing text (5/8 blogs: #14, #15, #19 openers; #5, #18 FAQ). `sentence_repair` cut/rewrites orphan a referent → AA-789 (F13 orphan) / post-repair integrity (AA-790).
2. **Tsaatan card fact mis-kinded** ("access requires a multi-hour horse or reindeer ride" stored as setting) → still in the seed; 4/4 Terra blogs copy it, #15 attaches it to the optional nomadic-family visit. AA-774 code works (0 practical bullets); fix = card data (re-kind) + Claude audit of card fact kinds.
3. **Location drift** "near Moron" → "in Mörön"/"here" (6/8 blogs, panel product-truth) — fidelity check on prepositions of place.
4. **Hashtag typos on place names** (#PadiDistrict held correctly; #PamiTaktsang, duplicate #ParoTaktsang approved) → deterministic hashtag check against seed place names (AA-780 scope).
5. **Terra voice** reads like a school trip ("textbook", "classroom") — brand fit (AA-771/AA-800); A&H "travel designer" CTA flagged by fidelity as not in the brand pack (same as r4).
