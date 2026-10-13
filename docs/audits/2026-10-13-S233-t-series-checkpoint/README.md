# S233 — T-series checkpoint after AA-768/769/770/771/772

Real tenant flow on Dev after #674–#686 (api :554 → :555): Slate pick → T8 goal (fresh angles with the
brand pack + place cards) → recommended angle → T9 write. 4 pilot tenants; Trail Pulse and WildKind had no
blog subject clearing the Slate bar, so blogs come from one Mongolia route brief (A&H + Terra).

## Round 1 — 20 pieces (12 LinkedIn, 8 blog), $1.58
| | S232 (last rounds) | S233 |
|---|---|---|
| Approved by gates | 4/10 | **12/20** (LinkedIn 10/12, blog 2/8) |
| Hard fails: cut-off / AA leak / invented brand / social markdown / "There is a moment" | 5/20 cut, 2 brands, 3 markdown, 13/49 | **0 / 0 / 0 / 0 / 0** |
| Place card in seed / writer input stored | — | 20/20 / 20/20 |
| Panel: as-is / light / heavy / reject | 0 / 24 / 67 / 8 % | 0 / **30** / 70 / **0** % |
| Panel overall / fidelity / AI-tells | 5.20 / 5.0 / 4.75 | 5.33 / **5.80** / 4.45 |
| Approval precision (approved that are as-is/light) | 33% | 42% |

Panel report (single rater, 4 lenses, S232 method): `01-commercial-panel-round1.md`.

## Blog SEO rounds (4–8 blogs each, same Mongolia brief)
| Round | Change deployed | Blog approved | Blocking fails |
|---|---|---|---|
| 1 | #674–#678 | 2/8 | F9 8, F4 4 (keyword "…mongolia price") |
| 2 | #682 skip transactional keywords; F4 no longer blocks attempt 3 | 1/8 | F4 6 (keyword "…reviews", verbatim + accent match), F9 3 |
| 3 | #683 keyword coverage (accent-insensitive) | 0/4 | F4 2 (scope: "gobi tour tourist camp"), F9 2 |
| 4 | #684 keyword scoped to the moment; SEO fit retry | 1/4 | F4 3 (generic word match, plural, accented slug), F9 1 |
| 5 | #685 location-only match, plurals, ASCII slug | 1/4 | F4 3 (metas 157–185: model overshoots), F9 2 |
| 6 | #686 meta target 130–145 | **2/4** | F4 1 (one 65-char title), F9 1 — metas 139–154 |

## What is left (ranked, from the panel)
1. Scope check for every place in title/meta/body; keyword from the scoped moments only (partly done).
2. Angles must not anchor on a moment with < 3 place facts; trim "other trips" lines.
3. Deterministic checks: duplicate sentences (repair re-inserts the seed "why it matters" line), "content seed"
   leaking into text, hashtag spelling; repair edits in place.
4. LinkedIn spec per brand type (120–250 words, ≤3 hashtags, first line ≤140); angle tone bound to brand voice.
5. FAQ only for questions the seed answers; block social-proof phrasing.
6. F9 v2 (typed claims) — some flags are true background (1937 purges) judged over-strict.
7. Seed: conflicting place facts (Khövsgöl water share 2% / 0.4% / 1–2%), day-order sanity.
