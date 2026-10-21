# Place pipeline trial: Claude Haiku 5.5 (S246, 16:31 UTC)

Same runner and 3 Laos tours as the Haiku 4.5 / Luna trial (`place_model_trial.py`, stage `adhoc_aa847`, reference Sonnet 4.6). Cost: $0.0099, about $0.0033 per tour.

| | Haiku 4.5 (live since migration 260) | Haiku 5.5 |
|---|---|---|
| Days: decided overnight / anchor | 0.95 / 0.89 | **not valid**: 2 of 3 day calls failed |
| Locate within radius (confirmed) | 0.53 | 0.63 |
| Locate median / p90 km | 20.8 / 76.4 | **4.3** / 43.9 (Sonnet: 5.0 / 18.3) |
| $ per tour | 0.011 | 0.0033 |

**Why the day calls failed:** both stopped with `stopReason=max_tokens`, one with no text and one with truncated JSON.
- Haiku 5.5 runs adaptive thinking at its default effort, and those thinking tokens count against `maxTokens`.
- `services/places` sends `max_tokens=4000`, so the thinking used up the budget.
- The S246 migration 259 notes listed this as a risk.

**Next (S247, before the place build):**
1. Let the gateway set the effort, or raise `max_tokens` for the place stages, when the model is a Claude 5.5 model.
2. Rerun this trial.
3. If Haiku 5.5 passes, it beats Haiku 4.5 on both coordinates and cost. Moving to it then needs the owner's approval and a migration like 260.

Until then the live route stays Haiku 4.5.
