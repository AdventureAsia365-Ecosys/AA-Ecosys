---
id: GUIDE-14-architecture
title: "Pha 2: Kiến trúc"
description: Chọn và ghi lại các ranh giới khó đảo ngược trước khi viết code - sản phẩm bàn giao, checklist cổng G2, mẫu và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [cto, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-discovery, GUIDE-14-setup]
lang: vi
translation_of: docs/playbook/02-architecture.md
---

# Pha 2: Kiến trúc

**Mục tiêu:** chọn các ranh giới khó đảo ngược, và viết chúng ra trước khi viết code. **Người chịu trách nhiệm cuối:**
tech lead. **Theo:** arc42 (canvas một trang, không phải cả mười hai mục ngay ngày đầu), C4 (view context, container và
deployment dạng code), MADR (ADR tối giản), ISO/IEC 25010:2023 (tên các đặc tính chất lượng), OWASP ASVS 5.0 (mức bảo
mật theo từng vùng).

## Sản phẩm bàn giao

| Sản phẩm | Mẫu |
|---|---|
| `CONTEXT.md` trên canvas arc42, có view C4 context và container | [Mẫu `CONTEXT.md`](../templates/context-arc42.vi.md) |
| Các ADR đầu tiên: stack, quyền sở hữu dữ liệu, danh tính, tenancy, môi trường | [ADR](../templates/adr.md) |
| Quy ước HTTP API | [ADR quy ước HTTP API](../templates/adr-http-api-conventions.md) |
| Yêu cầu chất lượng theo chín tên của ISO 25010 | Mục 11 của `CONTEXT.md` |
| Danh sách hợp đồng và mỗi lần đọc chéo app một thư mục hợp đồng | [Hợp đồng](../templates/contract.vi.md) |
| Dòng sở hữu schema: repo nào ghi schema nào, với dải số của nó | Trang sở hữu schema của dự án |
| Mô hình mối đe doạ gọn | [Mô hình mối đe doạ](../templates/threat-model.vi.md) |
| Dòng sổ đăng ký quyền riêng tư cho mỗi thực thể có dữ liệu cá nhân, kèm thời hạn lưu | Sổ đăng ký quyền riêng tư của dự án |
| Dòng sổ đăng ký dùng AI, nếu sản phẩm dùng AI | Sổ đăng ký dùng AI của dự án |

## Cổng G2: thiết kế được chấp nhận

| # | Câu hỏi |
|---|---|
| 1 | Mỗi thực thể có đúng một bên ghi không? |
| 2 | Mỗi lần đọc chéo app có đi qua một hợp đồng có tên và có phiên bản không? |
| 3 | Mức bảo mật đã chọn theo từng vùng chưa: ASVS mức 1, mức 2 cho xác thực, thanh toán và dữ liệu cá nhân? |
| 4 | Mỗi thực thể có dữ liệu cá nhân đã có dòng trong sổ đăng ký quyền riêng tư với thời hạn lưu chưa? Đánh giá tác động đã làm khi G1 nói rủi ro cao chưa? |
| 5 | Chi phí chạy đã được ước lượng theo từng môi trường và thêm vào bảng chi phí chưa? |
| 6 | Mô hình môi trường đã chọn chưa (bao nhiêu môi trường, mỗi cái chứa gì, một thay đổi đi qua thế nào)? |
| 7 | Các ADR đầu tiên đã được viết và tech lead chấp nhận chưa? |
| 8 | `CONTEXT.md` có nằm dưới trần dung lượng, phần chi tiết module ở các trang liên kết không? |

## Lỗi hay gặp

- Hai service cùng ghi một bảng "tạm thời thôi".
- Đọc thẳng bảng của app khác thay vì qua một view hợp đồng hay API.
- Một mô hình mối đe doạ liệt kê sáu chữ STRIDE nhưng không có mối đe doạ thật nào.
- Viết mọi mục arc42 ngay ngày đầu; điền canvas, phần còn lại lớn dần theo code.
- Quyết định đưa ra trong chat và không bao giờ được viết thành ADR.

## AA làm thế nào

[Kiến trúc hệ sinh thái](../ecosystem-architecture.md), [mục lục ADR](../adr/README.md), [hợp
đồng](../contracts/README.md), [data standards](../architecture/data-standards/README.md) và [sở hữu
schema](../database/schema-ownership.md); xem [bản áp dụng AA](aa-profile.vi.md).
