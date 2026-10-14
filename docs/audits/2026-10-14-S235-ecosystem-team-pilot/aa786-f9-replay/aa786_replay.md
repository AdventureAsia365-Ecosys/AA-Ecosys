# AA-786 — F9 v1.1 replay + 3-run stability

- mode: PAID, model: gpt-5.6-luna, prompt: f9_v1.1, runs: 3
- calls: 69, charged $0.1336 of cap $0.50
- notes mentioning citation/marker: **0** (Done-when: 0)
- prompts that still carried a tag: 0
- fallback pieces ending as an unquoted blocking fail: **none**
- verdict classes: {'pass': 49, 'block_quoted': 19, 'warn_title_meta': 1}
- mean verdict agreement: 0.87 (15/23 unanimous); mean pairwise Jaccard of flagged sentences: 0.676

| piece | fallback | run classes | agreement | Jaccard |
|---|---|---|---|---|
| r1#9 | yes | pass, pass, pass | 1.0 | 1.0 |
| r3#4 | yes | pass, block_quoted, block_quoted | 0.67 | 0.0 |
| r3#12 | yes | block_quoted, block_quoted, block_quoted | 1.0 | 0.45 |
| r4#12 | yes | block_quoted, block_quoted, block_quoted | 1.0 | 0.67 |
| r4#0 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#1 |  | block_quoted, pass, pass | 0.67 | 0.33 |
| r4#2 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#3 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#4 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#5 |  | block_quoted, pass, pass | 0.67 | 0.33 |
| r4#6 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#7 |  | pass, pass, block_quoted | 0.67 | 0.33 |
| r4#8 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#9 |  | pass, block_quoted, pass | 0.67 | 0.33 |
| r4#10 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#11 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#13 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#14 |  | block_quoted, pass, warn_title_meta | 0.33 | 0.17 |
| r4#15 |  | block_quoted, block_quoted, pass | 0.67 | 0.17 |
| r4#16 |  | block_quoted, block_quoted, block_quoted | 1.0 | 0.44 |
| r4#17 |  | block_quoted, pass, pass | 0.67 | 0.33 |
| r4#18 |  | pass, pass, pass | 1.0 | 1.0 |
| r4#19 |  | pass, pass, pass | 1.0 | 1.0 |

Classes: pass; block_quoted (claim or TEXT_INTEGRITY sentence — repairable); block_cta; block_unquoted (must be 0 on fallback pieces); warn_reasonless (no checkable reason — ships flagged); warn_title_meta (title/meta claim only — ships flagged).
