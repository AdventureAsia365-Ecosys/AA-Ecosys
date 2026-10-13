# Place-card drafter A/B (S234, AA-772)

Same 30 places that already had a card, same draft prompt. Identity and kept facts by the production check (GPT-5.6 Luna); Luna arms also checked by Claude Haiku (cross-vendor).

| Drafter | named | identity ok | facts | kept | wrong | Haiku-check kept | Haiku-check wrong | draft cost |
|---|---|---|---|---|---|---|---|---|
| sonnet | 28 | 28 | 167 | 152 | 11 | – | – | $0.2734 |
| haiku | 28 | 24 | 154 | 128 | 23 | – | – | $0.0724 |
| gpt-6-luna | 26 | 25 | 104 | 98 | 2 | 92 | 1 | $0.0111 |
| gpt-5.6-luna | 27 | 27 | 146 | 145 | 0 | 134 | 2 | $0.0226 |

Decision: draft on GPT-5.6 Luna, check on Claude Haiku (migration 222). Haiku as drafter failed (Takin Zoo → 'National Zoo of Bhutan', spellings not normalised). Live Nepal tour after deploy: 40 drafts → 37 cards, $0.082 ($0.0022/card vs $0.0176 in S233).

Raw rows: `.tmp-session/s234/s234_pc_ab_out.json`, `s234_pc_ab_luna_out.json`; scripts `pc_ab.py`, `pc_ab_luna.py`.
