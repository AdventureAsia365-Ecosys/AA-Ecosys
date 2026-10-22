# CRM: tích hợp do đại lý tự mang (BYO) và trách nhiệm chia sẻ (S247, 22/10/2026)

Tác nhân: Claude Code (subagent của phiên S247). Chỉ tài liệu, $0, không gọi dịch vụ trả phí, không ghi Linear/Jira.
Nguồn: hướng sản phẩm Nghiệp chốt 22/10/2026 (đại lý tự mang tài khoản Twilio/WhatsApp, Stripe, hộp thư, e-sign, bản
đồ; đại lý là bên kiểm soát dữ liệu; AA là bên xử lý và giữ việc bảo mật nền tảng; câu chữ pháp lý là đề xuất cho chị Thư).

| File | Nội dung |
|---|---|
| [ADR 0010 quyết định 9](../../adr/0010-aa-partner-app.md) | Luật BYO, bảng ai làm gì (đại lý / AA / chị Thư), hệ quả từng module; trỏ từ 0008a và 0006b. Vẫn Proposed |
| [Đính chính thiết kế](../2026-10-21-S246-crm-design-v3/final/errata-s247-byo.md) | Thay đổi theo từng card/issue, trang "Connections", danh sách thư hệ thống của AA, chi phí §8, công sức §7, rủi ro §9 |
| [AA-930 readiness](../2026-10-22-S247-crm-readiness/README.md) | Check 11 (Twilio ISV) → **resolved by BYO**, kèm thay đổi kế hoạch và điểm theo dõi còn lại |
| [Đề xuất cho chị Thư](proposal-thu.md) | Song ngữ EN–VI, dạng phiếu khảo sát: ai làm gì bằng lời đơn giản, các công ty khác ghi gì (nguồn công khai), 5 câu hỏi có đề xuất |
| [Ghi chú triển khai](../../implementation-notes/AA-928-s247-byo.md) | Quyết định, thay đổi so với yêu cầu, đánh đổi |

**Hai lựa chọn chờ Nghiệp (có đề xuất):**

1. Stripe: v1 dùng **khoá restricted của chính đại lý** (AA không cần tài khoản platform Stripe), Connect để sau. Đề xuất: đồng ý.
2. Bản đồ: chỉ hiện bản đồ khi đại lý gắn **token bản đồ riêng**; không có thì hiện danh sách ngày + link. Mapbox rời
   khỏi danh sách sub-processor của AA. Đề xuất: đồng ý.
