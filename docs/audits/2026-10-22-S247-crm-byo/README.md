# CRM: tích hợp do đại lý tự mang (BYO) và trách nhiệm chia sẻ (S247, 22/10/2026)

Tác nhân: Claude Code (subagent của phiên S247). Chỉ tài liệu, $0, không gọi dịch vụ trả phí, không ghi Linear/Jira.
Nguồn: hướng sản phẩm Nghiệp chốt 22/10/2026 (đại lý tự mang tài khoản Twilio/WhatsApp, Stripe, hộp thư, e-sign;
đại lý là bên kiểm soát dữ liệu; AA là bên xử lý và giữ việc bảo mật nền tảng; câu chữ pháp lý là đề xuất cho chị Thư).

| File | Nội dung |
|---|---|
| [ADR 0010 quyết định 9](../../adr/0010-aa-partner-app.md) | Luật BYO, bảng ai làm gì (đại lý / AA / chị Thư), hệ quả từng module; trỏ từ 0008a và 0006b. Vẫn Proposed |
| [Đính chính thiết kế](../2026-10-21-S246-crm-design-v3/final/errata-s247-byo.md) | Thay đổi theo từng card/issue, trang "Connections", danh sách thư hệ thống của AA, chi phí §8, công sức §7, rủi ro §9 |
| [AA-930 readiness](../2026-10-22-S247-crm-readiness/README.md) | Check 11 (Twilio ISV) → **resolved by BYO**, kèm thay đổi kế hoạch và điểm theo dõi còn lại |
| [Đề xuất cho chị Thư](proposal-thu.md) | Song ngữ EN–VI, dạng phiếu khảo sát: ai làm gì bằng lời đơn giản, các công ty khác ghi gì (nguồn công khai), 5 câu hỏi có đề xuất |
| [Ghi chú triển khai](../../implementation-notes/AA-928-s247-byo.md) | Quyết định, thay đổi so với yêu cầu, đánh đổi |

**Hai lựa chọn đã chốt (Nghiệp, S247, 22/10/2026):**

1. Stripe: v1 dùng **khoá restricted (`rk_`) của chính đại lý** (AA không chạy tài khoản platform / Connect Stripe),
   Connect để sau. **Đã duyệt.**
2. Bản đồ: **đảo lại đề xuất BYO**. Bản đồ là tính năng sản phẩm, không phải tài khoản nhà cung cấp mang rủi ro pháp
   lý, nên **AA cung cấp bản đồ** (Mapbox bằng token của AA, giới hạn theo host CRM; free tier ~50.000 lượt tải bản
   đồ web/tháng, Dev $0; vượt ~$5/1.000 lượt, có budget alarm sẵn theo dõi). Đại lý không gắn token bản đồ. Mapbox
   vẫn là sub-processor của AA. Builder danh sách ngày (CRM-21a) vẫn là lõi; bản đồ trong builder (CRM-20) là phần
   tăng cường, không chặn M3.
