## T-series social path on Dev: cost and latency, 2026-10-12 (since 00:00Z)

Read-only queries only (scripts: `/home/nghiep/projects/AA-Ecosys/.tmp-session/s232/s232_tcost_profile.py`, `s232_tcost_channel.py`, `s232_tcost_stop.py`).

Jev calls are logged twice: once in `shared.llm_call_log` (provider jev) and once in `shared.decision_log`, with the same counts and costs. The figures below count each call once.

### Jobs today
| kind | n | status | avg s | max s | `shared.job.cost_usd` |
|---|---|---|---|---|---|
| t2_rewrite | 14 | succeeded | 277.1 | 495.5 | **0 (all)** |
| t7_slate | 1 | succeeded | 5.6 | 5.6 | 0 |
| t8_angles | 2 | succeeded | 14.9 | 15.3 | 0 |
| t9_write | 45 (18 blog / 27 LinkedIn) | succeeded | 59.9 (blog 91.9, LinkedIn 38.6) | 134.3 | **0 (all)** |

### Cost by stage key (T path, about $7.75 total)
| stage | role / model | calls | cost $ | share | per job / piece |
|---|---|---|---|---|---|
| t2_generate (t2 jobs) | writer sonnet-4-6 | 101 | 4.906 | 63.3% | $0.350 per t2 job, 7.2 calls per job |
| t9_write | writer sonnet-4-6 | 92 | 2.055 | 26.5% | $0.0457 per piece, 2.0 calls per piece |
| t10_judge | gpt-5.6-luna 182 + gpt-6-luna 11 (10 shadow, 1 fallback) | 193 (+3 no-job) | 0.290 | 3.7% | $0.0064 per piece, 4.3 calls per piece |
| s1_judge (logged inside t2 jobs) | gpt-5.6-luna | 96 | 0.161 | 2.1% | $0.0115 per t2 job |
| t8_angle_gen | sonnet-4-6 | 7 (5 with no job) | 0.144 | 1.9% | about $0.02 per call |
| s1_itinerary_nudge (inside t2 jobs) | haiku-4-5 | 117 | 0.103 | 1.3% | |
| t2_judge / t2_itinerary_nudge / s1+t2_flag_fix | luna / haiku | 10 / 13 / 5 | 0.031 | 0.4% | |
| **Jev, all stages** | jev-1.13.0 | 1,021 | **0.051** | **0.65%** | |
|  of which t10_gates (shadow) | rubric_met 352, faq_restates 105, brand_voice 88, cta_clear 88 | 633 | 0.0351 | | 14 per piece, about $0.0008 per piece |
|  of which t3_grounding (enforce, in t2) | a1_claim_supported | 98 | 0.0079 | | |
|  of which t7_debate (no job) | t7_topic_fits_brand | 272 | 0.0069 | | |
|  of which t9_facts / t8_angle_rank / t2_judge_tiebreak / s1_grounding | | 15 / 7 / 4 / 1 | 0.0009 | | |
| f10_embed | cohere-embed-v4 | 88 | 0.008 | 0.1% | 2 per piece |

### t9_write per piece, by channel (45 jobs)
| channel | jobs | writer $ | judge $ | Jev $ | embed $ | **total per piece** | avg s / p50 s |
|---|---|---|---|---|---|---|---|
| blog | 18 | 0.0803 | 0.0086 | 0.0013 | 0.0003 | **$0.0905** | 91.9 / 91.6 |
| LinkedIn | 27 | 0.0226 | 0.0049 | 0.0004 | 0.0001 | **$0.0280** | 38.6 / 38.9 |

Typical calls per t9 job:
- 2 writer calls (3 on some blogs)
- 4–6 judge calls
- 2 embeds
- 12–21 Jev calls (about 14 on average)

Jev latency adds up to only about 2.0 s per job (about 140 ms per call). The rest of the 35–130 s is the Sonnet writer plus the luna judge.

### Writer/judge stop reasons (t9 jobs)
| channel | stage | end_turn | max_tokens (2048 cap) |
|---|---|---|---|
| blog | t9_write | 17 | **20** |
| blog | t10_judge | 74 | 4 |
| LinkedIn | t9_write | 55 | 0 |
| LinkedIn | t10_judge | 114 | 1 |

### tenant_id / job_id completeness since 10:40Z
| table | stage | rows | missing tenant_id | missing job_id |
|---|---|---|---|---|
| llm_call_log | t9_write / t10_judge / t10_gates / f10_embed | 29 / 64 / 209 / 29 | 0 | 0 |
| decision_log | t10_gates | 209 | 0 | 0 |

No t2, t7 or t8 activity after 10:40Z, so only t9 rows could be checked. Before 10:40, these synchronous calls had no job_id:
- t7_debate: 272
- t8_angle_gen: 5
- t8_angle_rank: 7
- t9_facts: 5
- t10_judge: 3, and these 3 also had no tenant_id

### Observations
- **Where the money goes:** T2 rewrite is about 67% of today's T spend ($5.21 for 14 jobs, $0.37 per job, 4.6 min on average), driven by t2_generate at about 7 Sonnet calls per job. T9 is about 31% ($2.39 for 45 pieces). The Sonnet writer is 86% of T9 cost; the judge is 12%; Jev and embeds together are under 2%. Jev is cheap: 1,021 calls for $0.05 in total, so adding more Jev questions costs almost nothing.
- **Abnormal 1: blogs are cut off by the token limit.** 20 of 37 blog `t9_write` calls stopped at the 2048-token cap (`max_tokens`); LinkedIn had none. That likely explains part of the F3/F5 structure holds and the cut-off endings, and it means paying for output that gets thrown away. Raising the blog writer token cap (or splitting the generation) should come before the F9 calibration. A few judge calls also hit 2048: 4 blog, 1 LinkedIn, and 3 of those 5 were F9.
- **Abnormal 2: job cost is never filled in.** `shared.job.cost_usd = 0` for every job today (all kinds: t2, t7, t8, t9, revalidate). Per-job cost exists only by summing `llm_call_log` by job_id.
- **Abnormal 3: stage labels are mixed.** Inside t2_rewrite jobs most judge and nudge calls are logged under S1 stage names (`s1_judge` 96, `s1_itinerary_nudge` 117, `s1_flag_fix` 4) rather than `t2_*` (t2_judge only 10). Per-stage T2 dashboards will undercount T2.
- **Jev in T9 only observes.** Every t10_gates/t9_facts question (rubric_met, brand_voice, faq_restates, cta_clear, fact_relevant) runs in `mode=shadow`. Only t3_grounding (`a1_claim_supported`, inside t2) enforces. There were no Jev errors and 0 cached hits; caching was 0% even on repeated rubric questions.