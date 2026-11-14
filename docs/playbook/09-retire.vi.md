---
id: GUIDE-14-retire
title: "Pha 9: Ngừng"
description: Đóng một sản phẩm, app hay tính năng cho gọn và thôi trả tiền cho nó - các bước ngừng, cổng G8 và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-operate, TPL-01-retirement-checklist]
lang: vi
translation_of: docs/playbook/09-retire.md
---

# Pha 9: Ngừng

**Mục tiêu:** đóng một sản phẩm, app hay tính năng cho gọn và thôi trả tiền cho nó. **Người chịu trách nhiệm cuối:** chủ
doanh nghiệp; tech lead thực hiện. **Theo:** pha retirement của UK GDS; luật lưu giữ và xoá trong sổ đăng ký quyền riêng
tư của dự án.

## Các bước

Danh sách đầy đủ, để chép vào issue ngừng, là [checklist ngừng](../templates/retirement-checklist.vi.md). Tóm tắt:

1. **Quyết định:** một ADR ngừng (cái gì, vì sao, khi nào, cái gì thay thế, ai bị ảnh hưởng) và lời đồng ý của chủ doanh
   nghiệp.
2. **Báo:** người dùng, tenant, bên dùng hợp đồng và nhà cung cấp, trước ít nhất 30 ngày; phiên bản lớn cuối cùng của
   hợp đồng được phục vụ song song ít nhất 30 ngày.
3. **Dữ liệu:** xuất cho chủ của nó; giữ hoặc xoá từng loại theo thời hạn lưu; xoá qua một lần chạy thử với số đếm chính
   xác, một snapshot và một lời duyệt; cách ly trước khi drop.
4. **Lưu lượng:** tombstone (HTTP 410) hoặc chuyển hướng; sau đó gỡ DNS, chứng chỉ và luật định tuyến; dừng job, hàng
   đợi và webhook.
5. **Hạ tầng:** kế hoạch destroy của IaC được review và áp từ CI; resource ngoài IaC tìm theo tag; gỡ secret, role và
   client danh tính; xoá hoặc đặt hết hạn image, bucket, snapshot và log.
6. **Chứng minh bằng không:** inventory và tìm theo tag rỗng; sau một ngày tính tiền trọn vẹn, phần đã ngừng là 0 USD.
7. **Đóng:** tài liệu chuyển deprecated hoặc archived, chỉ dẫn cho agent được dọn, một dòng bài học cuối.

## Cổng G8: ngừng hoàn tất

| # | Câu hỏi |
|---|---|
| 1 | Inventory có cho thấy không còn resource nào của phần đã ngừng không? |
| 2 | Hoá đơn, sau một ngày tính tiền trọn vẹn kể từ lúc destroy, có cho thấy 0 USD cho nó không? |
| 3 | Mọi loại dữ liệu đã được giữ hoặc xoá theo thời hạn lưu, có bằng chứng chưa? |
| 4 | Người dùng và bên dùng hợp đồng đã được báo, và thời hạn báo trước đã qua chưa? |
| 5 | Secret, role và credential của phần đã ngừng đã xoá chưa? |
| 6 | Tài liệu và chỉ dẫn cho agent đã hết tham chiếu còn sống tới nó chưa? |

## Lỗi hay gặp

- Xoá app nhưng không xoá job theo lịch, alarm, bản ghi DNS hay secret của nó.
- Drop bảng mà không xuất dữ liệu hay qua thời gian cách ly.
- Dừng ở "đã destroy" mà không kiểm hoá đơn.
- Quên chỉ dẫn cho agent, thứ vẫn tiếp tục bảo agent gọi một service đã chết.
