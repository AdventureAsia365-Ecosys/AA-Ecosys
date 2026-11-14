---
id: PROD-00-discovery-replace-me
title: Bản tóm tắt khám phá - <sản phẩm hoặc tính năng>
description: <Một câu - vấn đề, ai gặp nó, và quyết định làm / không làm cần đưa ra ở cổng G1.>
type: report
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: []
lang: vi
translation_of: docs/templates/discovery-brief.md
---

# Bản tóm tắt khám phá - <sản phẩm hoặc tính năng>

<!-- Playbook dự án mới, pha 1 Khám phá (docs/playbook/01-discovery.md). Dựa trên pha discovery của UK GDS (diễn đạt
lại giải pháp thành vấn đề, ước lượng chi phí của vấn đề, dừng lại không phải là thất bại) và hướng dẫn mua hay tự xây
của 18F. Điền cùng chủ doanh nghiệp; tech lead và agent bổ sung phần nghiên cứu. Giữ trong hai trang. Lưu trong tài liệu
của dự án (với AA: docs/product/<slug>/). Xoá ghi chú này. -->

## 1. Vấn đề

- **Ai gặp nó:** <nhóm người dùng, bao nhiêu người, bao lâu một lần>.
- **Hôm nay diễn ra thế nào:** <cách làm hiện tại, các cách lách>.
- **Bằng chứng:** <phỏng vấn, ticket, số liệu, ghi chú nghiên cứu; mỗi cái kèm nguồn>.
- **Chi phí của vấn đề:** <thời gian, tiền hay rủi ro mỗi tháng nếu không có gì thay đổi>.

## 2. Thành công trông thế nào

Một kết quả đo được, với giá trị hôm nay và mục tiêu: <chỉ số, giá trị gốc, mục tiêu, tới khi nào>.

## 3. Các phương án

| Phương án | Là gì | Chi phí thô (xây và chạy mỗi tháng) | Thời gian tới giá trị đầu tiên | Rủi ro |
|---|---|---|---|---|
| Không làm gì | Giữ cách làm hôm nay | 0 | ngay | <...> |
| Mua hoặc dùng lại | <sản phẩm, module của app đang có, API client> | <...> | <...> | <khoá chặt nhà cung cấp, nơi lưu dữ liệu> |
| Tự xây | <app hoặc module mới> | <...> | <...> | <...> |

Câu hỏi mua hay tự xây: đây có phải điểm khác biệt cốt lõi không? Có sản phẩm nào phủ ít nhất 80 % nhu cầu không? Ai vận
hành nó sau khi ra mắt? Dữ liệu có rời đi được nếu nhà cung cấp thất bại không?

## 4. Sàng lọc dữ liệu và quyền riêng tư

| Câu hỏi | Trả lời |
|---|---|
| Có xử lý dữ liệu cá nhân không? | <có / không> |
| Các loại dữ liệu | <liên hệ, đặt chỗ, thanh toán, giấy tờ tuỳ thân, sức khoẻ, văn bản tự do> |
| Quốc gia của chủ thể dữ liệu và nơi dữ liệu sẽ nằm | <...> |
| Cơ sở pháp lý cho từng mục đích | <hợp đồng, đồng ý, lợi ích hợp pháp> |
| Rủi ro cao (cần một đánh giá tác động đầy đủ)? | <có / không, kèm lý do> |

## 5. Ràng buộc và giả định

- <Hạn chót, ngân sách, đội, công nghệ, hợp đồng.>
- <Giả định cần kiểm, và kiểm thế nào.>

## 6. Khuyến nghị cho cổng G1

- **Khuyến nghị:** <làm theo phương án X / không làm / khám phá thêm N phiên>.
- **Appetite:** <số phiên và USD chủ doanh nghiệp chấp nhận cho pha tiếp theo>.
- **Chi phí chạy đã báo giá:** <chi phí hằng tháng của khung trên Dev, lấy từ bảng chi phí>.
- **Tiếp theo:** nếu làm, điền điều lệ dự án.
