---
id: GUIDE-15
title: Quy tắc làm việc
description: Mục lục các quy tắc làm việc chuẩn bằng tiếng Anh của nhóm agent - phiên làm việc, kế hoạch và issue, giao tiếp với người liên quan - và nơi đặt các quy tắc W1 đến W7.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15-sessions, GUIDE-15-planning, GUIDE-15-stakeholders, CAT-01, GUIDE-02, GUIDE-13-lms, AA-1104]
lang: vi
translation_of: docs/guides/working-rules/README.md
---

# Quy tắc làm việc

Các quy tắc mà agent tuân theo trước đây nằm trong các skill tiếng Việt gắn với đường dẫn trong repo. Các trang này là
bản chuẩn bằng tiếng Anh của chúng, để con người, agent và các bài học của AA Academy cùng đọc một quy tắc (khoảng
trống G6 của AA Academy, [nghiên cứu §6.6](../../research/lms/README.md#66-one-source-for-humans-and-agents)).

**Trang quy tắc giữ quy tắc; skill giữ quy trình.** Agent vẫn nạp skill để làm việc. Khi một quy tắc thay đổi, sửa
trang và skill trong cùng một PR; nếu trong lúc đó hai bên lệch nhau, áp dụng bên chặt hơn.

| Trang | Quy tắc về | Quy trình (skill) |
|---|---|---|
| [Phiên làm việc](sessions.vi.md) | Nguồn trạng thái, bắt đầu phiên, công việc trong phiên, thứ tự chốt phiên | [`aa-session`](../../../skill/aa-session/SKILL.md) |
| [Kế hoạch và issue](planning-and-issues.vi.md) | Thứ tự backlog, tạo issue, Definition of Ready, hạn mức Linear, cập nhật, Done | [`aa-linear-issue`](../../../skill/aa-linear-issue/SKILL.md), [`aa-ship`](../../../skill/aa-ship/SKILL.md) |
| [Giao tiếp với người liên quan](stakeholder-communication.vi.md) | Bài báo tiến độ cho chủ doanh nghiệp, câu hỏi kinh doanh, trang quyết định, tin nhắn cho nhà cung cấp | [`aa-jira-update`](../../../skill/aa-jira-update/SKILL.md), [`ai-nghiep`](../../../skill/ai-nghiep/SKILL.md) |

Bảy quy tắc đánh số W1 đến W7 áp dụng cho cả ba trang. Chúng nằm trong
[sổ tay kỹ thuật](../../engineering-handbook.vi.md): W1 "tự quyết, không hỏi" và W2 "không tự đặt cổng chặn" ở
[§2.4](../../engineering-handbook.vi.md#24-hai-luật-làm-việc-tự-quyết-không-hỏi-không-tự-đặt-cổng-chặn), W3 đến W7 ở
[§2.5](../../engineering-handbook.vi.md#25-thêm-các-quy-tắc-làm-việc-cho-agent).

Những nơi khác giữ quy tắc, không lặp lại ở đây: quy tắc viết tài liệu và quy tắc lệnh (AWS CLI một dòng, tên biến có
dấu gạch dưới) trong [hướng dẫn văn phong](../../STYLE.md); chi tiêu và báo giá trong [FinOps](../../ops/finops.md);
quyền merge ở [sổ tay §6.5](../../engineering-handbook.vi.md#65-quyền-merge-theo-giai-đoạn); chồng chỉ dẫn cho agent trong
[mục lục agent](../../agents.md).
