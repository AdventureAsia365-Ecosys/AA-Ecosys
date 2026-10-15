# AA-712 trial run (a) — 3 Laos tours of the frozen 56-tour set (S237, 14/10/2026)

Jobs: place_extract ×3 → place_geocode ×1 → tour_graph_build ×1 on worker :152 (dev-44443ec), enqueued 15:39Z by the orchestrator (`created_by=backfill:admin:s237-trial`), all succeeded by 15:46Z. Script: `aa712_parity.py` (read-only, ECS exec), raw output `parity.json`.

| Tour | Days CIS/TP | Components CIS/TP | Overnights same / compared | Geocode ≤ 25 km | Graph stops CIS/TP (shared) | LLM cost |
|---|---|---|---|---|---|---|
| fde65bf0 Mekong Valley, Elephants & Temple Towns 10D | 10 / 0 (TP has no day rows) | 35 / 72 | n/a | 16/17 | 10 / 0 | $0.0174 |
| 2bc45c55 Laos North to South 16D | 16 / 16 | 43 / 47 | 12 / 13 (all ≤ 25 km) | 16/16 | 16 / 15 (8) | $0.0254 |
| 16548cba Village Cycling & Trek 5D | 5 / 5 | 15 / 9 | 2 / 2 | 4/4 | 5 / 5 (3) | $0.0079 |

- Total LLM $0.0708 (9 calls: a3_place_days 4, a3_place_locate 2, a3_place_embed 3) = **$0.024/tour** (design estimate $0.039). Geoapify 18 requests, $0.
- The only > 25 km pair: CIS "Night Market (Vientiane)" vs TP "Night Market" 219 km — TP merged every "Night Market" into one point; CIS keeps the locality. CIS is right.
- Overnight differences on the 16-day tour: day 8 Kong Lor, day 14 Don Khong (CIS has them, TP null), day 16 Pakse Airport vs Pakse International Airport (name variant).
- 22 place names stay `pending` (`unknown_to_model` after 1 try): mostly generic ("Hmong village", "Information Center", "Socialization Area") but some real ones ("Wat Phra Baht", "Tham Theung", "Tad E-Tu Waterfall", "Hor Tay Phidok Library"). They need the /admin/places fix action (portal slice) or a second geocoder pass.
- 3 `shared.destinations` rows created by TP were re-located by CIS since the trial (expected: CIS owns place data per ADR 0007); the TP writers are removed in TP slice 6a before batch (b).
- Embeddings: 93/93 CIS components have one.

Verdict: pass for run (a). Batch (b) = rest of Laos (≤ 50) after TP slice 6a is deployed (decision D6).
