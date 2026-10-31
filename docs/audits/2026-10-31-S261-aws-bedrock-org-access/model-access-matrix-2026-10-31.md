---
id: OPS-08-s261-model-access-matrix
title: "Bedrock model access matrix per account (31/10/2026)"
description: "Gọi thử 5 token mỗi model trên acc3, acc2 và acc1: acc3 bị chặn toàn bộ (Error 002), acc2 chỉ Amazon Nova chạy, acc1 Claude 4.x + Nova chạy; lý do từ chối từng loại."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1004, AA-1002, docs/ops/playbooks/llm-access-denied.md]
---

# Bedrock model access matrix (31/10/2026 ~05:00Z, us-west-1)

Lệnh: `aws bedrock-runtime converse --model-id <id> --inference-config '{"maxTokens":5}'` từ IAM admin của từng
account (playbook llm-access-denied bước 3–5, 8). Lệnh bị từ chối không tính tiền; lệnh thành công dưới 0,001 USD.
acc1 (account cá nhân, đã gỡ khỏi hệ sinh thái theo AA-998) chỉ được gọi thử theo yêu cầu của tech lead, không định
tuyến gì sang đó.

| Model (profile) | acc3 (AI, đứng riêng) | acc2 (Dev, org TrueIDC) | acc1 (cá nhân, đứng riêng) | acc4 (quản lý org AA, 07:35Z) |
|---|---|---|---|---|
| Claude Haiku 4.5 (`us.`) | Error 002 | "not available for channel program accounts" | **OK** | đang xác minh account |
| Claude Sonnet 4.5 (`us.`) | Error 002 | — | — | đang xác minh account |
| Claude Sonnet 4.6 (`global.`) | Error 002 | "not available for channel program accounts" | **OK** | đang xác minh account |
| Claude Opus 4.6 (`us.`) | Error 002 | — | — | đang xác minh account |
| Claude Sonnet 5 / 5.5, Haiku 5.5, Opus 5.5 | Error 002 | — | Sonnet 5.5: "not available for this account" | đang xác minh account |
| OpenAI GPT-5.4 / 5.5 / 5.6 Luna / 6 Luna (`global.`) | Error 002 | GPT-5.5: "not available for this account" | GPT-5.5: "not available for this account" | "not available for this account" |
| Amazon Nova Lite / Pro (`us.`) | Error 002 | **OK** | Nova Lite: **OK** | **OK** |
| Amazon Nova 2 Lite (`us.` / `global.`) | Error 002 | **OK** | — | **OK** |
| Cohere Embed v4 (`global.`) | Error 002 | (đang dùng tại chỗ, chạy) | — | **OK** (1536 chiều) |
| Meta Llama 4 Maverick / Scout | — | cần inference profile (không có on-demand) | — | — |
| Claude Haiku 4.5 ở **us-east-1** | Error 002 | — | — | — |

## acc4 (account quản lý của org AA), gọi thật 31/10/2026 07:35Z

Đơn Anthropic đã nộp từ acc4 (đọc lại OK, `authorizationStatus AUTHORIZED`). Gọi thật (`aa-mgmt`, `maxTokens` 5):
Nova Lite / Pro / Nova 2 Lite và Cohere Embed v4 **chạy**; mọi Claude trả `AccessDeniedException` "Your account is
currently being verified. Verification normally takes less than 2 hours" (bước xác minh account mới của AWS, acc4 tạo
29/10 — không phải lệnh chặn kiểu Error 002 của acc3); GPT trên Bedrock "not available for this account" như acc1/acc2.
Gọi lại Claude sau khoảng 2 giờ: kết quả ở mục dưới.

**Gọi lại 09:40Z:** Claude Haiku 4.5 + Sonnet 4.6 **OK** (acc4 đã qua xác minh account). Claude Sonnet 5 / 5.5,
Haiku 5.5, Opus 5.5: "not available for this account" — giống acc1: đời 5 được mở theo từng account. Chi phí lần thử: dưới 0,001 USD (Nova + embed vài token).
Ghi nhớ: account quản lý không nên chạy workload; lần thử chỉ để biết đường acc4 có mở hay không.

## acc2: các họ model ngoài Claude / GPT (gọi thật 31/10/2026 ~08:20Z, us-west-1, `maxTokens` 40)

| Model (profile `us.`) | acc2 | Ghi chú |
|---|---|---|
| Amazon Nova Lite / Pro / Nova 2 Lite | **OK** | trả lời tiếng Việt |
| Meta Llama 4 Maverick / Scout | **OK** | trả lời tiếng Việt tự nhiên |
| Moonshot Kimi K3 | **OK** | model suy luận: 40 token dùng hết cho phần suy nghĩ, chưa ra chữ (cần `maxTokens` lớn hơn) |
| Z.AI GLM-5.3, xAI Grok 4.6 / 4.7 | "not available for this account" | như Claude / GPT trên acc2 (chương trình đại lý) |
| Writer Palmyra X4 / X5 | Legacy, không dùng 30 ngày → từ chối | — |

Chi phí lần thử: dưới 0,01 USD. Đây chỉ là kiểm quyền truy cập, chưa phải kiểm chất lượng.

## Đọc thế nào

- **acc3:** chặn ở mức account, mọi provider (kể cả Amazon Nova, model AWS tự bán), mọi region, cả embedding. Quay
  về model cũ trên acc3 không giúp được. Thêm vào đó quota họ Claude 5.x đã về 0
  (`acc3-quota-snapshot-2026-10-31.md`). Chỉ case AWS gỡ được.
- **acc2:** Claude bị chặn vì TrueIDC thuộc chương trình đại lý (AWS Solution Provider) chưa được bán Anthropic; GPT
  không mở cho account; **Amazon Nova chạy được** (model AWS tự bán, không qua Marketplace).
- **acc1:** account đứng riêng trả thẻ: Claude 4.x và Nova chạy, Claude 5.5 và GPT-5.5 chưa mở (account không được cấp
  model mới). Cho thấy "đứng riêng trả thẻ" tự nó không làm Bedrock bị chặn; lệnh chặn của acc3 là riêng acc3.
