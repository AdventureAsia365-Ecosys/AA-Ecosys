---
id: OPS-08-s262-ai-gateway-step0
title: "AI gateway step 0: measurements before the build (S262)"
description: "Read-only measurements of the LLM ledger, routes, budgets and jobs taken before the AI gateway v2 build in S262; sets the seed caps and the route snapshot hash."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-642, AA-804, AA-1017, AA-1018]
---

# Bước 0 của cổng AI v2: số đo trước khi dựng (S262, 31/10/2026)

Chạy chỉ đọc (ECS exec, role `cis_app`, `default_transaction_read_only`), 0 USD. Câu SQL: kế hoạch lát việc S262 mục 1
(Q0–Q12). Bản đầy đủ có ARN nên chỉ giữ ở máy (không đưa vào repo public).

## Mã băm route (Q0)

`d13dd30e60453c4fa11a870e6b1fdc83` trên 79 dòng (role_config + deployment + connection + catalog + alias). Mỗi lần
deploy CIS trong phiên phải ra đúng mã này (không đổi route).

## Gán tài khoản (Q4, 90 ngày)

| provider | account_null | calls | usd |
|---|---|---|---|
| bedrock-native | False | 5959 | 0.1557 |
| bedrock-satellite | False | 78346 | 288.3893 |
| bedrock-satellite | True | 505 | 0.3480 |
| openai | False | 1 | 0.0003 |
| openai | True | 592 | 2.4494 |
| typesafe | True | 301203 | 19.6890 |

Dòng `account_null = True` là lỗi gán tài khoản (bước 1 sửa cho lần gọi mới; không backfill).

## Chi OpenAI theo tháng (Q5)

| month | openai_usd |
|---|---|
| 2026-09-01 | 1.7170 |
| 2026-10-01 | 0.7327 |

Đề xuất trần OpenAI API (đường ấm cho stage chấm): **10 USD/tháng** (gấp ~6 lần tháng cao nhất), cảnh báo 80 %.

## Trần mới (Q6 → migration 318)

- Jev/ngày: max 3.84, p95 2.20, TB 0.89 USD → trần **5,00 USD/ngày** (2 × p95, làm tròn lên).
- DataForSEO mỗi tour (693 tour, 60 ngày): p50 0.002, p99 0.099, max 0.642 USD → trần **0,50 USD mỗi lượt** cho job S1.

## Route còn dùng khoá cũ (Q1)

21 stage: a0_column_map, a3_atomize, a3_place_card_check, a3_place_days, a3_place_dedupe_check, a3_place_locate, s1_atom_writer, s1_flag_fix, s1_itinerary_nudge, s1_source_facts, supply_content_writer, t2_flag_fix, t2_generate, t2_itinerary_nudge, t8_angle_gen, t9_faq_answer_fit, t9_faq_filter, t9_repair, t9_write, tp_compose, tp_extract. Chuyển sang model 5.5 là đổi route → cần duyệt + chạy thử trả phí (S11, không làm trong phiên này).

## 15 nhóm chi lớn nhất (Q2, 30 ngày, không tính shadow)

| stage | role | model | provider | calls | usd |
|---|---|---|---|---|---|
| s1_generate | writer | sonnet-5-5 | bedrock-satellite | 2013 | 47.0145 |
| t5_atomize | writer | haiku-4-5 | bedrock-satellite | 9515 | 40.1266 |
| s1_generate | writer | haiku-4-5 | bedrock-satellite | 1660 | 24.7112 |
| t9_write | writer | sonnet-4-6 | bedrock-satellite | 793 | 18.3935 |
| adhoc_aa790 | writer | sonnet-4-6 | bedrock-satellite | 258 | 10.8337 |
| t2_generate | writer | sonnet-4-6 | bedrock-satellite | 238 | 10.7752 |
| s1_judge | judge | gpt-5.6-luna | bedrock-satellite | 4940 | 9.5946 |
| a3_place_card_check | validate | haiku-4-5 | bedrock-satellite | 7282 | 9.0366 |
| s1_flag_fix | writer | haiku-4-5 | bedrock-satellite | 2729 | 7.8933 |
| adhoc_aa645 | writer | sonnet-5-5 | bedrock-satellite | 327 | 7.5521 |
| s1_itinerary_nudge | writer | haiku-4-5 | bedrock-satellite | 4686 | 6.7444 |
| s1_grounding | validate | jev-1.13.0 | typesafe | 69740 | 6.5254 |
| a3_place_locate | validate | sonnet-4-6 | bedrock-satellite | 284 | 5.0401 |
| s1_generate | writer | sonnet-4-6 | bedrock-satellite | 91 | 4.5062 |
| a3_atomize | validate | gpt-6-luna | bedrock-satellite | 6528 | 4.2198 |

## Lỗi job 14 ngày (Q8)

| kind | status | prefix | n |
|---|---|---|---|
| supply_content_draft | failed | NonRetryable | 3 |
| place_dedupe | failed | lease expired (worker stopped); no attempts left | 2 |
| llm_cost_reconcile | failed | NonRetryable | 1 |

## Chia theo app (Q11, 30 ngày)

| app | shadow | eval_run | adhoc | calls | usd |
|---|---|---|---|---|---|
| cis | False | False | False | 318317 | 222.7949 |
| cis | False | False | True | 15409 | 35.3040 |
| cis | True | False | False | 5523 | 2.4908 |
| cis | False | True | False | 519 | 1.4076 |
| cis | False | True | True | 3 | 0.1069 |
| tripplanner | False | False | False | 1512 | 0.0268 |

