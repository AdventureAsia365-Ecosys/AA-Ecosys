# S295 — Jira drafts (Vietnamese, for the business owner)

Status: **draft, waiting for the tech lead's approval** (not posted).
Numbers read live on 27/11/2026 (state-snapshot.md). Last comment read before drafting: PR-23 (21/11 19:54).
Skipped on purpose: commercial site, USD-only, Well-Architected, AWS security services (tech-lead decisions or not shipped; Jira carries product progress only).

---

## 1. PR-23 — Portal tenant (Content studio)

Why: a shipped, live-checked change that protects supplier data on the agency app.
Image: none (the change is a missing field and a 404, nothing to show on screen).

> @thule Bảo vệ dữ liệu nhà cung cấp trên app đại lý (27/11, Dev):
>
> - App đại lý chỉ nhận đúng các thông tin tour được phép: nước, số ngày, bao gồm / không bao gồm, quy mô nhóm, mùa đẹp, hoạt động và nội dung AA đã viết. Tên nhà cung cấp, mã nhà cung cấp và dòng giá gốc trong file nguồn không còn được gửi tới đại lý, kể cả khi mở công cụ lập trình của trình duyệt.
> - App đại lý chỉ chuyển tiếp những yêu cầu mà các màn hình thật sự dùng; mọi đường khác trả "không tìm thấy" và không chạm tới hệ thống nội dung.
> - Giá ở trang "In my catalog" giờ lấy từ giá "From" của hệ thống đặt tour, không còn ước tính từ dòng giá trong file nguồn. Tour chưa có giá trong hệ thống đặt tour sẽ không hiện giá.
> - Đã thử 27/11 trên Dev: đường lấy toàn bộ dữ liệu một tour trả "không tìm thấy", các trang của đại lý vẫn yêu cầu đăng nhập như cũ. Phần lọc dữ liệu đã kiểm bằng bộ test tự động; chưa thử bằng tài khoản đại lý thật.

| Claim | Evidence |
|---|---|
| Internal source fields no longer sent | CIS #1718 merged `dd1a441d`, deployed (`/health` git_sha `dd1a441d`); 912 unit + 17 integration tests; key-walk test poisons supplier/price fields |
| Only used routes forwarded | Partner #404 merged `7a972268`, `/healthz` `7a972268`; live 27/11: `/api/tenant/v1/tours/{id}/full` → 404, `/v1/billing` → 401 |
| In my catalog price from Booking | CIS #1718 (marketplace reads `price.from.v1`); not checked live with a tenant login |
