---
id: GUIDE-14-discovery
title: "Pha 1: Khám phá"
description: Hiểu vấn đề và quyết định có nên xây hay không - sản phẩm bàn giao, checklist cổng G1, mẫu và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-principles, GUIDE-14-architecture]
lang: vi
translation_of: docs/playbook/01-discovery.md
---

# Pha 1: Khám phá

**Mục tiêu:** hiểu vấn đề và quyết định có nên xây hay không. **Người chịu trách nhiệm cuối:** chủ doanh nghiệp.
**Theo:** pha discovery của UK GDS (diễn đạt lại giải pháp thành vấn đề, ước lượng chi phí của vấn đề, dừng lại không
phải là thất bại), hướng dẫn mua hay tự xây của 18F, bốn domain của PMBOK 7 (các bên liên quan, lập kế hoạch, đo lường,
bất định).

## Sản phẩm bàn giao

| Sản phẩm | Mẫu | Người phụ trách |
|---|---|---|
| Bản tóm tắt khám phá: vấn đề, bằng chứng, chi phí của vấn đề, các phương án | [Bản tóm tắt khám phá](../templates/discovery-brief.vi.md) | Tech lead và agent điều phối soạn nháp; chủ doanh nghiệp xem lại |
| Điều lệ dự án: product goal, chỉ số thành công, appetite, dung sai, ngoài phạm vi | [Điều lệ dự án](../templates/project-charter.vi.md) | Chủ doanh nghiệp |
| Bản đồ các bên liên quan và RACI | [Bản đồ các bên liên quan và RACI](../templates/stakeholder-raci.vi.md) | Tech lead |
| Sổ RAID đầu tiên | [Sổ RAID](../templates/risk-register.vi.md) | Agent điều phối |
| Bảng chi phí v0, có chi phí chạy hằng tháng của khung trên Dev | [Bảng chi phí](../templates/cost-sheet.vi.md) | Tech lead |
| Ghi chú mua hay tự xây, so sánh nhà cung cấp khi mua | [Chọn nhà cung cấp](../templates/vendor-selection.vi.md) | Tech lead |
| Cái nhìn đầu tiên về dữ liệu và sàng lọc quyền riêng tư | Mục 4 của bản tóm tắt khám phá | Tech lead |

## Cổng G1: làm / không làm

Chấm mỗi dòng đỏ, vàng hoặc xanh. Chủ doanh nghiệp ký.

| # | Câu hỏi |
|---|---|
| 1 | Vấn đề có bằng chứng, kèm nguồn không? |
| 2 | Đã có một chỉ số thành công, với giá trị gốc và mục tiêu chưa? |
| 3 | Appetite đã đặt theo số phiên và USD chưa? |
| 4 | Đây là hình dạng nào: một app mới, một module của app đang có, hay một API client của app đó? |
| 5 | "Dừng" có phải là một lựa chọn thật, và trường hợp không làm đã được ghi lại chưa? |
| 6 | Sàng lọc quyền riêng tư: các loại dữ liệu cá nhân, các nước, dữ liệu nằm ở đâu, cơ sở pháp lý cho từng mục đích, và có cần một đánh giá tác động đầy đủ không |
| 7 | Chi phí chạy hằng tháng của khung trên Dev đã được báo giá chưa ([áp dụng](adoption.vi.md), chi phí chạy)? |
| 8 | Các dung sai trong điều lệ đã được điền chưa? |

## Lỗi hay gặp

- Bắt đầu bằng một giải pháp ("chúng ta cần một CRM") thay vì vấn đề nó giải quyết.
- Không có giá trị gốc cho chỉ số thành công, nên không bao giờ chứng minh được thành công.
- Coi chi phí xây là toàn bộ chi phí; chi phí chạy hằng tháng cũng được báo giá ở G1.
- Bỏ qua sàng lọc quyền riêng tư vì sản phẩm "chỉ lưu vài trường".
- Để pha khám phá kéo dài không giới hạn: cho nó một appetite riêng.

## AA làm thế nào

Cổng quyết định của ADR 0008 (app mới, module hay API client) và các ghi chú nghiên cứu trong `docs/research/` đóng vai
trò khám phá; xem [bản áp dụng AA](aa-profile.vi.md).
