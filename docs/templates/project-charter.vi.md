---
id: PROD-00-charter-replace-me
title: Điều lệ dự án - <dự án>
description: <Một câu - product goal, chỉ số thành công và appetite mà chủ doanh nghiệp đã chấp nhận.>
type: reference
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 90
related: []
lang: vi
translation_of: docs/templates/project-charter.md
---

# Điều lệ dự án - <dự án>

<!-- Playbook dự án mới, pha 1 Khám phá, cổng G1. Dựa trên Product Goal của Scrum, bốn performance domain của PMBOK 7
(các bên liên quan, lập kế hoạch, đo lường, bất định) và dung sai của PRINCE2. Một trang. Chủ doanh nghiệp chịu trách
nhiệm cuối; tech lead và agent soạn nháp. Chỉ đổi qua một quyết định được ghi lại. Xoá ghi chú này. -->

## 1. Product goal

<Một câu: trạng thái tương lai của sản phẩm mà đội hướng tới.>

## 2. Chỉ số thành công

| Chỉ số | Giá trị gốc | Mục tiêu | Đo bằng | Rà soát |
|---|---|---|---|---|
| <kết quả chính> | <...> | <...> | <query, báo cáo, khảo sát> | <hằng tháng> |

## 3. Phạm vi

- **Trong:** <năng lực, người dùng, kênh>.
- **Ngoài:** <những gì dự án này sẽ không làm, kèm lý do>.

## 4. Appetite

- **Thời gian:** <N phiên hoặc tuần tới bản phát hành đầu tiên>.
- **Tiền:** <chi phí xây, và chi phí chạy hằng tháng trên Dev và khi có prod đầu tiên>.
- Khi dự báo vượt appetite, dừng và lập lại kế hoạch với chủ doanh nghiệp (circuit breaker).

## 5. Dung sai

Các giới hạn mà trong đó đội và agent của đội làm mà không hỏi (nguyên tắc của playbook, bảng dung sai).

| Dung sai | Giới hạn cho dự án này |
|---|---|
| Thời gian | <số issue mỗi phiên, giới hạn WIP, appetite cho mỗi issue> |
| Chi phí | <trần hằng tháng; mỗi mục trả phí mới được báo giá và duyệt riêng; lượt chạy tốn tiền: thử, rồi tối đa N> |
| Phạm vi | <Done-when đóng băng khi bắt đầu làm; phạm vi mới thành issue mới> |
| Chất lượng | <mọi check xanh; Done = đã kiểm live> |
| Rủi ro | <lớp rủi ro được review độc lập; bước phá huỷ sau một lần chạy thử và một lời đồng ý> |
| Lợi ích | <câu hỏi kinh doanh tới chủ doanh nghiệp dưới dạng phương án kèm khuyến nghị> |

## 6. Vai trò

Ai chịu trách nhiệm cuối cho từng pha: xem bản đồ các bên liên quan và RACI (`<link>`).

## 7. Rủi ro chính

Ba rủi ro hàng đầu từ sổ RAID (`<link>`), mỗi rủi ro kèm người phụ trách.

## 8. Phê duyệt

| Vai trò | Quyết định | Ngày |
|---|---|---|
| Chủ doanh nghiệp | <làm / không làm> | <YYYY-MM-DD> |
| Tech lead | <chấp nhận> | <YYYY-MM-DD> |
