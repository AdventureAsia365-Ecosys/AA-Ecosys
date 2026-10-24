---
id: PROD-01-s1-wave50
title: "S1 catalogue rewrite: real wave ≤50 (writer v2 × Sonnet 5.5, A3 on), S249"
description: "Báo cáo wave thật ≤50 tour của lần viết lại S1 cả catalogue (AA-645, quyết định d04): kết quả, điều kiện dừng, chất lượng d13, chi phí theo stage, slug 308, khôi phục công tắc."
type: report
status: active
owner: nghiep
audience: [engineer, cto, agent]
applies_to: [cis-core]
last_reviewed: 2026-10-24
review_every_days: 180
related: [AA-645, PROD-01-s1-go-no-go]
---

# Wave thật ≤50 — S1 writer v2 (S249, 24/10/2026)

Wave `fb2b1739-6fb7-4d79-a4e2-8e2ccaa9565c`, t0 07:05:28Z, đóng 08:15:20Z; 50 tour / 13 nước; snapshot RDS trước:
`aa-cis-dev-db-pre-s1-wave50-20261024`. Checkpoint 2 của Nghiệp (quyết định d04): sau báo cáo này, các wave theo nước tự
chạy tiếp khi không có điều kiện dừng.

## Kết quả (4 cột)

| S1 job ok | Lên Master | Chờ duyệt | Atomized |
|---|---|---|---|
| 50 | 50 | 0 | 50 |

Trash / failed / interrupted / chưa chạy: 0. Jev coverage 50/50.

## Điều kiện dừng (≥ 10 tour → luật 10%)

Không điều kiện nào bật: ở lại v1 0; mất ngày, legacy itinerary path, brand leak, atomize fail, S1 job fail, fallback v1,
Bedrock throttle, place pipeline, foreign write job: 0. Lần kiểm +40′ bật `published_not_atomized` /
`atoms_on_days_past_new_count` chỉ vì 9 tour còn xếp hàng A3 (cap 1); kiểm lại sau khi hàng đợi chạy hết: sạch.

## Chất lượng (d13 `scripts.aa645.wave_report`)

| Country | Tours | Published | Stayed v1 | Gate pages before → after | Unsupported before → after | Figure cov. before → after | Brand fit before → after (report-only) | $ / tour | Clearly better |
|---|---|---|---|---|---|---|---|---|---|
| Bhutan | 2 | 2 | 0 | 0/2 → 0/2 | 0 → 0 | 0.521 → 0.812 | 7.5 → 4.0 | 0.073 | no |
| China | 6 | 6 | 0 | 2/6 → 0/6 | 0 → 0 | 0.21 → 0.272 | 7.5 → 8.667 | 0.062 | yes |
| India | 9 | 9 | 0 | 4/9 → 0/9 | 0 → 0 | 0.349 → 0.647 | 7.556 → 6.222 | 0.079 | yes |
| Japan | 5 | 5 | 0 | 0/5 → 0/5 | 0 → 0 | 0.646 → 0.938 | 7.8 → 7.2 | 0.048 | no |
| Laos | 3 | 3 | 0 | 1/3 → 0/3 | 0 → 0 | 0.403 → 0.403 | 7.333 → 10.0 | 0.062 | yes |
| Mongolia | 2 | 2 | 0 | 0/2 → 0/2 | 0 → 0 | 0.5 → 0.834 | 7.5 → 6.0 | 0.056 | no |
| Nepal | 5 | 5 | 0 | 0/5 → 1/5 | 0 → 0 | 0.311 → 0.776 | 7.8 → 6.8 | 0.082 | no |
| Pakistan | 2 | 2 | 0 | 1/2 → 1/2 | 0 → 0 | 0.483 → 0.966 | 7.5 → 8.0 | 0.099 | no |
| Philippines | 3 | 3 | 0 | 0/3 → 0/3 | 0 → 0 | 0.0 → 1.0 | 7.333 → 7.333 | 0.042 | no |
| South Korea | 2 | 2 | 0 | 1/2 → 1/2 | 0 → 0 | 0.887 → 0.887 | 7.5 → 8.0 | 0.063 | no |
| Sri Lanka | 6 | 6 | 0 | 2/6 → 0/6 | 0 → 0 | 0.263 → 0.557 | 7.833 → 9.0 | 0.064 | yes |
| Taiwan | 2 | 2 | 0 | 0/2 → 0/2 | 0 → 0 | 0.644 → 0.76 | 7.5 → 10.0 | 0.058 | no |
| Thailand | 3 | 3 | 0 | 2/3 → 1/3 | 0 → 0 | 0.73 → 0.905 | 7.333 → 7.333 | 0.098 | yes |
| ALL | 50 | 50 | 0 | 13/50 → 4/50 | 0 → 0 | 0.415 → 0.672 | 7.58 → 7.56 | 0.068 | yes |

- Trang bị gate còn lại sau wave (4): Pakistan K2 Concordia, South Korea Bike tour (`DAY_*`, đã có từ trước);
  mới: Kailash Mansarovar via Lhasa (`META_CUT`), Adventure itinerary to Northern Thailand (`DAY_*`) — đã publish, cần đọc tay.
- Brand fit chỉ để tham khảo (rubric v1 và `a1-voice-v2/1` khác nhau); 7 tour 4,0 theo v2, không phải gate.

## Kiểm live

- Cả 50 tour đổi tên → 50 slug đổi; TripPlanner `/tours/<cũ>` → 308 `/tours/<mới>`, slug mới 200: 50/50.
- `published_at` giữ nguyên, `updated_at` đổi; component không đổi (PLACE_PIPELINE_AUTO tắt).

## Chi phí (`shared.llm_call_log`)

| Stage | USD |
|---|---|
| s1_generate (sonnet-5-5, acc3) | 3,0010 |
| s1_judge (gpt-5.6-luna) | 0,2725 |
| s1_flag_fix (haiku-4-5, 27 tour) | 0,1473 |
| s1_grounding (Jev) | 0,1230 |
| a3_atomize (gpt-6-luna) | 0,2606 |
| a3_atomize (Jev) | 0,0324 |
| a3_segment_match (Jev) | 0,0017 |
| DataForSEO | 0 |
| **Tổng wave** | **3,8386** (0,0768 / tour; S1 trung bình 0,0709, trần mô hình 0,12) |

Luỹ kế từ pilot thật: 0,2678 + 3,8386 = **4,11 / trần 120 USD**.

## Khôi phục công tắc

Worker :367 → :368 (revision sạch, không `S1_WRITER_V2`, image `50fd6258`); route `s1_generate` về haiku (08:15:05Z);
wave đóng (mở lại DB Migrate).

Dữ liệu: `rp-report.json` (từng tour: job, ngày, atom, slug, chi phí), `wave-report-d13.json` (theo nước + từng tour).
