# S294 — Jira drafts (Vietnamese, for the business owner)

Status: **drafts, not posted** — waiting for the tech lead's approval (aa-jira-update rule 1).
Numbers read live on 25–26/11/2026 (state-snapshot.md, ledger, Product map page 03:09 26/11).
Last comments read before drafting: PR-26 (24/11 19:24), PR-22 (25/11 18:14), PR-27 (25/11 18:15).

---

## 1. PR-22 — CIS nội dung & pipeline

Why: two shipped, live-checked changes the business owner can open herself.
Images: `live/jira/product-map-1440-light.png` (1), `live/ws390/content-workspace-new__390__light.png` (2).

> @thule Cập nhật CIS ngày 26/11:
>
> - Trang **Platform › Product map** đã cập nhật theo code mới nhất: 5 app, 136 tính năng (128 đang chạy), 38 liên kết giữa các app, 4 hành trình, 146 kịch bản UAT gắn kèm. Trang tự làm mới mỗi khi có thay đổi được merge (ảnh 1).
> - Trang soạn tour (Content workspace) giờ dùng được trên điện thoại: không còn phải kéo ngang ở màn 390 px (ảnh 2).
> - Bài viết AI: nếu model chèn một câu ghi chú trước hoặc sau nội dung, hệ thống tách câu đó ra, không để lọt vào bài, và ghi lại thành tín hiệu để nhóm kỹ thuật theo dõi.
>
> Ảnh: (1) Product map, (2) Content workspace trên điện thoại.

| Claim | Evidence |
|---|---|
| 136 features, 128 live, 38 links, 4 journeys, 146 UAT | Product map live 26/11 03:15, catalogue build 03:09 (image 1) |
| No sideways scroll at 390 px | CIS visual run green at 390, image 2 (live, 25/11 19:29) |
| Writer note split out | CIS PR merged + deployed (api/worker same SHA, snapshot); unit tests; not yet seen on a real tour run |

---

## 2. PR-26 — CRM cho đại lý

Why: the calendar card is live; Google connection not tried with a real account, so the draft says so.
Image: none (the card is behind the studio login; the post-deploy smoke checked it, no shot saved).

> @thule Cập nhật CRM ngày 26/11:
>
> - Trang **Integrations** có thêm thẻ **Lịch**: mỗi nhân viên đại lý kết nối lịch Google hoặc Microsoft 365 của mình một lần, các chuyến khởi hành và việc cần làm trong CRM sẽ tự đẩy sang lịch đó (một chiều, CRM → lịch cá nhân).
> - Đã có trong hệ thống và trang mở bình thường; chưa thử kết nối bằng tài khoản Google / Microsoft thật vì cần đăng ký quyền truy cập lịch phía Google trước.

| Claim | Evidence |
|---|---|
| Card live on Integrations | CRM web Deploy Web Dev green incl. studio smoke 25/11 23:50 (snapshot: crm-web :195) |
| Departures + tasks, Google or Microsoft 365, one-way | Partner #395 (feat: one-way push of departures and tasks into a member's own Google or Microsoft 365 calendar), crm-089/090 applied |
| Not tried with real Google | stated |

---

## 3. PR-27 — Nền tảng (đăng nhập, bảo mật, hạ tầng)

Why: first AI safety test run + security fix, short, no tech decisions (memory jira-no-tech-decisions).

> @thule Cập nhật nền tảng ngày 26/11:
>
> - Chạy lượt kiểm tra an toàn AI đầu tiên cho phần viết nội dung (thử các câu lệnh cố tình lừa model): 12 ca đạt, 1 ca báo nhầm, 3 ca chưa chạy được; không ca nào lộ dữ liệu hay làm sai hướng dẫn. Chi phí lượt chạy dưới 0,40 USD.
> - Các trang bị chặn bởi tường lửa (ví dụ truy cập lạ) giờ trả về đủ các header bảo mật như trang thường; bản quét bảo mật tự động hằng tháng không còn báo nhầm ở các trang này.

| Claim | Evidence |
|---|---|
| 12 pass / 1 false positive / 3 not run | red-team report 25/11 (private ISMS evidence), ledger total 0.3949 USD |
| Blocked answers carry headers | curl without UA → 403 + headers on admin hosts; single HSTS after the gateway fix (26/11) |
| Monthly scan no longer false-flags | ZAP re-run after the WAF change (zap-baseline.md, WAF update section) |

---

## Posting log

- PR-22: not posted yet
- PR-26: not posted yet
- PR-27: not posted yet
