---
id: GUIDE-14-operate
title: "Pha 7: Vận hành"
description: Giữ sản phẩm chạy, học từ mọi lỗi và theo dõi chi phí - các đợt rà soát định kỳ, sự cố, runbook và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-release, GUIDE-14-scale, GUIDE-14-metrics]
lang: vi
translation_of: docs/playbook/07-operate.md
---

# Pha 7: Vận hành

**Mục tiêu:** giữ nó chạy, học từ mọi lỗi, theo dõi chi phí. **Người chịu trách nhiệm cuối:** tech lead. **Theo:**
Google SRE (postmortem không đổ lỗi, có danh sách điều kiện kích hoạt), ITIL 4 (quản lý sự cố gọn), FinOps Framework
(inform, optimise, operate ở mức crawl / walk), DORA (chỉ số giao hàng).

Pha này không có cổng cố định: các đợt rà soát định kỳ là biện pháp kiểm soát.

## Sản phẩm bàn giao

| Sản phẩm | Mẫu | Nhịp |
|---|---|---|
| Alarm, mỗi alarm trỏ tới một runbook | [Runbook](../templates/runbook.md) | mỗi alarm |
| Bản ghi sự cố | [Bản ghi sự cố](../templates/incident-record.vi.md) | mỗi sự cố |
| Postmortem | [Postmortem](../templates/postmortem.md) | khi một điều kiện kích hoạt xảy ra |
| Diễn tập các runbook quan trọng (khôi phục, rollback, break-glass, xoay secret) | Runbook có `last_tested` | khi quy trình đổi, và trước prod |
| Báo cáo chỉ số giao hàng | [Báo cáo chỉ số giao hàng](../templates/delivery-metrics-report.vi.md) | hằng tuần |
| Rà soát chi phí và dung lượng | [Rà soát chi phí và dung lượng](../templates/cost-report.md), [bảng chi phí](../templates/cost-sheet.vi.md) | hằng tháng |
| Rà soát quyền truy cập | [Rà soát quyền truy cập](../templates/access-review.md) | hằng quý |
| Bài học được biến thành guard | Sổ bài học của dự án | lúc tìm ra nguyên nhân gốc |

## Luật

- Một runbook chưa từng chạy được đánh dấu chưa kiểm và không được tin dùng trong sự cố.
- Một bài học máy kiểm được thì thành test, luật lint, hook hay bước CI; rồi dòng bài học được gỡ.
- Mỗi alarm có một runbook; alarm không ai xử lý thì xoá hoặc sửa.
- Chi phí có một nguồn sự thật cho mỗi loại (hoá đơn cloud, ledger model); báo cáo nêu rõ nguồn nào.

## Lịch rà soát

| Rà soát | Đầu vào | Đầu ra |
|---|---|---|
| Giao hàng hằng tuần | Git, các lượt deploy, sự cố, công cụ theo dõi việc | Báo cáo chỉ số giao hàng |
| Chi phí và dung lượng hằng tháng | Hoá đơn theo tag và dịch vụ, ledger theo stage, dung lượng cơ sở dữ liệu và hàng đợi | Rà soát chi phí và dung lượng kèm quyết định |
| Quyền truy cập hằng quý | Nền tảng code, role cloud, người dùng danh tính, role cơ sở dữ liệu, ai đọc secret | Rà soát quyền truy cập kèm phát hiện |
| Retro playbook 90 ngày | Playbook này, các chỉ dẫn, các ADR | Một lượt cắt tỉa; các issue về playbook được nêu |

## Lỗi hay gặp

- Coi một dashboard xanh là bằng chứng trong khi probe phía sau đã cũ.
- Viết một postmortem nêu tên một người thay vì guard còn thiếu.
- Để runbook chưa kiểm dồn lại cho tới đúng sự cố cần một cái.
- Đọc chi phí từ hai nguồn lệch nhau mà không nói nguồn nào thắng.
