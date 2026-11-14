---
id: TPL-01
title: Mẫu tài liệu
description: Mọi mẫu tài liệu của AA-Ecosys và bộ kit dự án mới, theo pha vòng đời, kèm công dụng của từng mẫu.
type: reference
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [CAT-00, TPL-02, TPL-03, GUIDE-14]
lang: vi
translation_of: docs/templates/README.md
---

# Mẫu tài liệu

Mỗi mẫu một nhà (nguyên tắc 2 của playbook). Chép một mẫu, điền vào, và xoá ghi chú hướng dẫn của nó. Mẫu mang ID giữ
chỗ và không bao giờ được xuất bản lên trình đọc tài liệu. Schema front-matter là
[`frontmatter.schema.json`](frontmatter.schema.json); luật văn phong nằm trong [hướng dẫn văn phong](../STYLE.md). Mẫu có
bản tiếng Việt khi nó có front-matter; ADR và ghi chú triển khai không có bản dịch.

## Theo pha vòng đời

| Pha | Mẫu | Dùng cho |
|---|---|---|
| 1 Khám phá | [Bản tóm tắt khám phá](discovery-brief.vi.md) | Vấn đề, chi phí của nó, các phương án và quyết định làm / không làm ở G1 |
| 1 Khám phá | [Điều lệ dự án](project-charter.vi.md) | Product goal, chỉ số thành công, appetite và dung sai |
| 1 Khám phá | [Bản đồ các bên liên quan và RACI](stakeholder-raci.vi.md) | Ai bị ảnh hưởng, ai quyết, mỗi pha một người chịu trách nhiệm cuối |
| 1, rồi mọi pha | [Sổ RAID](risk-register.vi.md) | Rủi ro, giả định, vấn đề và phụ thuộc kèm người phụ trách |
| 1, rồi 7 | [Bảng chi phí](cost-sheet.vi.md) | Dự báo hằng tháng, chi phí đơn vị, các mục trả phí kèm lời duyệt |
| 1, 2 | [Chọn nhà cung cấp](vendor-selection.vi.md) | Các phương án đặt cạnh nhau trước khi ký hợp đồng |
| 2 Kiến trúc | [`CONTEXT.md` trên canvas arc42](context-arc42.vi.md) | Ranh giới repo, view C4, quyết định, chạy local |
| 2, rồi mọi pha | [ADR](adr.md) | Một quyết định khó đảo ngược (dạng đầy đủ và dạng MADR tối giản, bước cắt tỉa) |
| 2 | [ADR quy ước HTTP API](adr-http-api-conventions.md) | URL, phiên bản, lỗi, danh sách, idempotency cho một API mới |
| 2 | [Mô hình mối đe doạ](threat-model.vi.md) | Tài sản, ranh giới tin cậy, STRIDE theo container |
| 2, 4 | [Hợp đồng](contract.vi.md) | Một view, API hay sự kiện chéo app, kèm schema và mẫu dữ liệu |
| 3, 4 | [File migration](migration-file.vi.md) | Header, transaction, tự đăng ký, expand / contract |
| 3, 4 | [Mục registry settings](settings-entry.vi.md) | Một ngưỡng hay giá trị chính sách thành setting sửa được trên trang admin |
| 4 Xây dựng | [Definition of Ready](definition-of-ready.md) | Một issue cần gì trước khi bắt đầu, có đường đi và appetite |
| 4 Xây dựng | [Ghi chú triển khai](implementation-note.md) | Plan, quyết định, thay đổi và đánh đổi, viết trong lúc làm |
| 5 Kiểm thử | [Chiến lược kiểm thử](test-strategy.vi.md) | Kiểm gì ở lớp nào và cái gì chặn merge |
| 5, 6 | [Checklist bảo mật](security-checklist.vi.md) | ASVS 5.0 mức 1 (mức 2 cho xác thực, thanh toán, dữ liệu cá nhân) |
| 5 Kiểm thử | [Báo cáo UAT](uat-report.md) | Phía kinh doanh ký xác nhận một tính năng thấy được |
| 6 Phát hành | [Checklist phát hành](release-checklist.vi.md) | Từ merge tới đã kiểm live, theo vùng chất lượng |
| 6 Phát hành | [Ghi chú phát hành](release-note.md) | Góc nhìn kinh doanh của một bản phát hành |
| 7 Vận hành | [Runbook](runbook.md) | Các bước chính xác cho một việc, kèm luật đã kiểm |
| 7 Vận hành | [Bản ghi sự cố](incident-record.vi.md) | Một bản ghi gọn mở ngay khi sự cố bắt đầu |
| 7 Vận hành | [Postmortem](postmortem.md) | Rà soát không đổ lỗi, kèm danh sách khi nào bắt buộc phải có |
| 7 Vận hành | [Rà soát chi phí và dung lượng](cost-report.md), [rà soát dung lượng](capacity-review.md) | Chi phí và dung lượng hằng tháng |
| 7 Vận hành | [Rà soát quyền truy cập](access-review.md) | Hằng quý: ai truy cập được gì |
| 7 Vận hành | [Báo cáo chỉ số giao hàng](delivery-metrics-report.vi.md) | Chỉ số DORA và luồng hằng tuần |
| 8 Mở rộng | [Chính sách SLO và error budget](slo-error-budget.vi.md) | Viết từ sớm, bật khi có prod đầu tiên |
| 9 Ngừng | [Checklist ngừng](retirement-checklist.vi.md) | Không còn gì chạy, lưu trữ hay bị tính tiền |
| Mọi pha | [Checklist phiên và log phiên](session-checklist.vi.md) | Bắt đầu, trong phiên và đóng một phiên của agent |

## Hình dạng trang

| Mẫu | Dùng cho |
|---|---|
| [How-to](how-to.md) | Các bước để đạt một mục tiêu |
| [Reference](reference.md) | Dữ kiện để tra cứu |
| [Explanation](explanation.md) | Vì sao một thứ lại như vậy |
| [Guide theo vai trò](role-guide.md) | Trang vào của một vai trò người đọc |
