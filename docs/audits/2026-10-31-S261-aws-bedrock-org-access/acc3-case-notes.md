---
id: OPS-08-s261-acc3-case-notes
title: "acc3 Bedrock Error 002: facts for the AWS Support case and steps after the reply"
description: "Dữ kiện đã kiểm (Cost Explorer, CloudTrail, hoá đơn, probe) về việc acc3 bị Error 002 sau khi rời org eCloudvalley, đoạn tiếng Anh để dán vào case, và việc cần làm khi AWS trả lời."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1004, AA-1002, docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md]
---

# acc3 Bedrock Error 002: thông tin cho case AWS (S261, 31/10/2026)

Viết cho tech lead. Case AWS mở ngày 29/10/2026 (gói Basic, không đọc được bằng API), hẹn trả lời khoảng 04–06/11.
Tech lead chốt S261: chưa nhắc case, chờ vài ngày; acc3 giữ độc lập, chưa cần vào org AA.

## 1. Dữ kiện đã kiểm

| Dữ kiện | Kết quả | Nguồn, lúc kiểm |
|---|---|---|
| acc3 đứng độc lập, tự trả, gọi Claude | 10–17/08/2026: Claude Sonnet 4.6 16,19 USD + Haiku 4.5 0,62 USD + thuế 1,68 = **18,49 USD** | Cost Explorer acc3, 31/10 |
| Hoá đơn tháng 8 | 18,49 USD, phát hành 01/09/2026, **Paid**: thanh toán bằng thẻ Mastercard ngày 02/09 (Completed); số dư nợ hiện tại **0,00 USD** | Console Billing › Payments (ảnh của tech lead, 31/10) |
| Vào org eCloudvalley | 17/08/2026 15:40 (giờ VN), `AcceptHandshake` INVITE ACCEPTED | CloudTrail acc3 |
| Thử rời org | 25/09 06:29 và 06/10 08:57: root gọi `LeaveOrganization`, SCP của eCloudvalley từ chối | CloudTrail acc3 |
| Rời org | 29/10/2026 13:50, phía eCloudvalley đưa ra (role của org bị xoá) | CloudTrail acc3 |
| Tháng 9–10 | 0 USD trên acc3 (eCloudvalley là bên trả trong thời gian đó) | Cost Explorer |
| Bedrock hiện tại | Error 002 với mọi model, kể cả Amazon Nova, mọi region đã thử | probe 29/10, 31/10 |
| Thông tin liên hệ chính | đã điền (công ty, địa chỉ, điện thoại, quốc gia VN) | `account get-contact-information`, 31/10 |
| Liên hệ phụ Billing / Operations / Security | Billing + Operations **đã thêm 31/10** (tech lead); Security chưa thêm | Console Account (ảnh của tech lead, 31/10) |
| Form Anthropic, agreement Marketplace | có (S257) | postmortem |
| Đối chứng acc4 (account mới, org AA) | Nova + Cohere chạy; Claude "account is being verified (<2 h)" lúc 07:35Z; kết quả lần gọi lại ghi ở mục 4 | probe 31/10 |

Loại trừ: "account đứng riêng thì không được Bedrock", "account chưa từng tự trả" (tháng 8 đứng riêng vẫn chạy) và
"còn nợ hoá đơn" (tháng 8 đã trả, nợ 0 USD).

## 2. Việc tech lead tự kiểm được (không cần chờ case)

- Đã kiểm 31/10: hoá đơn 08/2026 đã trả, nợ 0 USD. Liên hệ phụ Billing + Operations đã thêm. Không còn việc nào tech
  lead phải tự làm trước khi AWS trả lời.

## 3. Đoạn tiếng Anh để dán khi nhắc lại case

> Since 29/10/2026 every Bedrock model call on this account returns "Error 002: Access to Bedrock models is not allowed
> for this account", including Amazon Nova, in every region we tried. Facts: this account was standalone and paid its
> own bill in August 2026, and Claude Sonnet 4.6 and Haiku 4.5 worked then (invoice of 02/09/2026, 18.49 USD). It joined
> a reseller's AWS Organization on 17/08/2026 and was removed by that organization on 29/10/2026 13:50 (UTC+7); the
> errors started within minutes. The payment method is valid, the Anthropic use-case form and the Marketplace
> agreements are in place, and the contact information is complete. Please (1) tell us what blocks Bedrock on this
> account and restore access, (2) confirm that our model quotas are kept, and (3) tell us whether we should wait for
> your fix before moving the account into our own AWS Organization.

## 4. Khi AWS trả lời

1. Ghi câu trả lời (tóm tắt, không dán thông tin cá nhân) vào mục 5 dưới đây và vào postmortem
   `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md` (Timeline + Root cause).
2. Agent gọi thử lại toàn bộ ma trận model trên acc3 (`maxTokens` 5, dưới 0,001 USD), lệnh ở
   `model-access-matrix-2026-10-31.md`; cập nhật cột acc3.
3. Nếu đã gỡ: đọc lại quota acc3 (so với `acc3-quota-snapshot-2026-10-31.md`), kiểm thẻ trạng thái LLM trong CIS admin
   (Settings › LLM Models) về `ok`, chạy một probe qua gateway (stage `adhoc_*`, có ghi `shared.llm_call_log`), rồi
   cập nhật AA-1004 và AA-1002.
4. Nếu AWS yêu cầu thêm giấy tờ / xác minh: chỉ tech lead làm (đăng nhập root, thẻ, thuế).

## 5. Phản hồi của AWS

Case AWS (Account and billing, mở 29/10/2026 09:27 UTC, người mở: tech lead; trạng thái 31/10: **Pending Amazon action**):

| Thời điểm (giờ VN) | Nội dung |
|---|---|
| 30/10 (chat, Nayana) | AWS đã liên hệ team dịch vụ để **gỡ hạn chế** trên account; ước tính **3–5 ngày làm việc** |
| 30/10 16:20 (Charalma, AWS Accounts and Billing) | Đã chuyển cho team dịch vụ điều tra; "might take some time"; sẽ cập nhật qua case |
| 30/10 | Tech lead gửi thêm phát hiện: chặn ở mức account, cả Nova; form + agreement đã có; account đứng riêng khác gọi được |

Mốc chờ: 3–5 ngày làm việc từ 30/10 (thứ Sáu) → khoảng **05–06/11**. Tech lead chốt: không nhắc case trước đó.

### Lần gọi lại Claude trên acc4

09:40Z 31/10: Claude Haiku 4.5 + Sonnet 4.6 chạy (acc4 đã qua xác minh); Claude đời 5 (Sonnet 5/5.5, Haiku 5.5,
Opus 5.5) "not available for this account", như acc1. Nghĩa là: account mới đứng riêng vẫn gọi được Claude 4.x sau
xác minh, nên Error 002 của acc3 là tình trạng riêng của acc3 (đúng như case đang xử lý).
