# Stage A/B: the 7 GPT-5.6 Luna stages vs GPT-6 Luna (S246, 21/10/2026)

Runner: AA-CIS-App `scripts/aa729` `stage_ab.py`. Inputs: golden fixture 1.1.0, n=10 per stage. Arms: current#1, then gpt-6-luna, then current#2. Reports: `ab-gpt6-a.json` and `ab-gpt6-b.json`, run d2329335 and run 73bf961f. Spend: $0.35 according to the runner and $0.65 in the `llm_call_log` delta, which includes both current arms. The cap was $1 per batch.

| Stage | Agreement with current | Bar | Schema | Runner says | Decision |
|---|---|---|---|---|---|
| s1_judge | 0.85 | 0.90 | 1.0 | keep | keep |
| t2_judge | 0.70 | 0.90 | 1.0 | keep | keep |
| t7_debate_judge | 0.70 | 0.80 | 1.0 | keep | keep |
| a3_place_card | 0.85 | 0.90 | 0.9 (1 failure) | keep | keep |
| s1_brand_audit | 0.80 | 0.90 | 1.0 | keep | keep |
| t2_brand_audit | 0.80 | 0.80 | 1.0 | switch | **keep** (see below) |
| t10_judge | 0.50 | 0.70 | 1.0 | keep | keep |

**Why t2_brand_audit stays on GPT-5.6 Luna even though the runner says switch:**

- GPT-6 Luna finds fewer problems. It flags about half as many issue codes per article: 4.0 against 7.6 to 8.2 for current.
- Its text is not similar to the current output (0.18).
- It is about 3 times slower: 17.8 s against 4.8 to 6.8 s.
- The saving is small: about $0.0003 per call, or roughly 20%.
- The stage is a judge, and a judge that misses half the issues is not worth that saving.
- n=10 is too small for a judge switch.

**Result:** every route stays as it is. Look at this again only with n ≥ 30 and a per-code recall check against labels.
