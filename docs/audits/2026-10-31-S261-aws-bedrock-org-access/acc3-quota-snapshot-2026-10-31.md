---
id: OPS-08-s261-acc3-quota-snapshot
title: "acc3 Bedrock quota snapshot after leaving the reseller organization (31/10/2026)"
description: "Bằng chứng chỉ đọc: quota áp dụng của acc3 cho Claude 5.x về 0 (mặc định AWS 6 triệu TPM) trong khi Claude 4.x giữ nguyên; lịch sử gọi thật trong sổ gateway."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1004, AA-1002, docs/ops/playbooks/llm-access-denied.md]
---

# acc3 quota snapshot (31/10/2026, read-only)

Lệnh: `aws service-quotas list-service-quotas --service-code bedrock --region us-west-1 --profile nghiep_aa365` và
`list-aws-default-service-quotas` (chỉ đọc). Lịch sử gọi: `shared.llm_call_log` (account = acc3).

## Quota áp dụng hôm nay so với mặc định AWS (us-west-1)

| Model | Quota áp dụng của acc3 | Mặc định AWS |
|---|---|---|
| Claude Sonnet 4.6 (cross-region / global) | 6.000.000 TPM, 10.000 RPM | — |
| Claude Sonnet 4.5 V1 | 5.000.000 TPM, 10.000 RPM | — |
| Claude Haiku 4.5 | 5.000.000 TPM | — |
| **Claude Sonnet 5.5** (cross-region / global) | **0 TPM** | **6.000.000 TPM** |
| Claude Sonnet 5 | 0 TPM | — |
| Claude Haiku 5.5 | 0 TPM | — |
| Claude Opus 5 / 5.5 | 0 TPM | — |

## Lịch sử gọi thật của acc3 (sổ gateway, từ 01/09/2026)

| Tuần | Model | Số lệnh |
|---|---|---|
| 14/09–26/10 | haiku-4-5 (gồm satellite) | ~39.500 |
| 28/09, 12/10 | sonnet-5 | 5 |
| 19/10 | sonnet-5-5 | 2.316 |
| 19/10 | haiku-5-5 | 43 |
| 26/10 | sonnet-5-5 | 182 |
| 26/10 | haiku-5-5 | 30 |
| 26/10 | opus-5-5 | 75 |

Lệnh thành công cuối cùng: 29/10/2026 07:11 UTC (acc3 rời org của đại lý 06:50 UTC cùng ngày).

## Đọc thế nào

- acc3 đã gọi Claude 5.5 thật (~2.500 lệnh Sonnet 5.5) khi còn trong org đại lý, nên lúc đó quota 5.x lớn hơn 0.
- Hôm nay quota áp dụng của cả họ 5.x là 0, thấp hơn mặc định AWS (6 triệu TPM cho Sonnet 5.5), trong khi họ 4.x giữ
  nguyên. Đây là giới hạn đặt ở mức account sau khi đổi payer (suy luận; chỉ AWS xác nhận được).
- Lịch sử dùng (CloudWatch của acc3, sổ gateway) không mất; quota 4.x giữ nguyên. Phần cần lấy lại là quota 5.x và lệnh
  chặn "Error 002".

## Đoạn bổ sung cho case AWS (dán vào case đang mở)

```text
Additional evidence (read-only, 31 Oct 2026, us-west-1): the applied Service Quotas of this account for the Claude 5.x
family are 0 (e.g. "Cross-region model inference tokens per minute for Anthropic Claude Sonnet 5.5" = 0, AWS default
6,000,000), while Claude 4.x quotas are unchanged (Sonnet 4.6 6,000,000 TPM / 10,000 RPM). Before 29 Oct 2026
06:50 UTC this account ran ~2,500 Claude Sonnet 5.5 calls and ~75 Opus 5.5 calls successfully; the last successful call
was at 07:11 UTC that day, shortly after the account left its reseller's organization. Please restore model access
and the Claude 5.x quotas to at least the AWS defaults, or tell us what is required.
```
