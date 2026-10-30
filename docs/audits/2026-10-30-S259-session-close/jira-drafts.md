---
id: OPS-08-s259-jira-drafts
title: "S259 Jira drafts (S258 carried over + S259)"
description: "Nháp comment Jira cuối phiên S259, chờ tech lead duyệt trước khi đăng."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-952, AA-994, AA-996]
---

# S259 — nháp Jira (chờ duyệt, CHƯA đăng)

Gộp nháp S258 (tech lead bảo gom sang phiên sau cùng ngày) với việc S259. Mỗi comment mở bằng mention node @thule khi
đăng; không mã Linear; đứng tên Nghiệp. Bỏ PR-27: hạ tầng (tài khoản quản trị AWS mới, CI) là việc kỹ thuật tech lead
tự quyết (memory `jira-no-tech-decisions`).

## 1. PR-22 (CIS — Nội dung & pipeline) — nháp S258, giữ nguyên, thêm 1 dòng trạng thái AI

@thule Cập nhật ảnh bìa tour trên Marketplace đại lý (29–30/10):
- Ghép ảnh với điểm đến tốt hơn: thêm 326 ảnh được gắn đúng điểm đến (tổng 1.919 ảnh), 336 điểm đến có ảnh bìa.
- Tour trong kho cho đại lý có ảnh bìa: **302 → 444 / 892 tour**.
- 448 tour còn thiếu chủ yếu thuộc India (215), Japan (79), Laos (45), Philippines (44), Thailand (43): các nước này
  chưa có thư mục ảnh nguồn, cần bổ sung ảnh chứ không phải sửa code.
- Phần AI viết nội dung vẫn tạm dừng: AWS vẫn chặn Bedrock trên tài khoản AI, và tài khoản OpenAI dự phòng đã hết
  credit (kiểm lại toàn bộ model ngày 30/10, 11:20). Hệ thống báo trạng thái này trên trang quản trị và dừng các việc
  AI ngay thay vì thử lại.

| Câu | Bằng chứng |
|---|---|
| 302 → 444 / 892, 1.919 ảnh, 336 điểm đến | S258 apply (log S258, AA-671 theo sau) |
| AI tạm dừng, OpenAI hết credit | probe 30/10 11:20: mọi model sinh văn bản FAIL (Error 002 / 429 "no credits remaining"); chỉ embedding chạy |

## 2. PR-24 (TripPlanner) — nháp S258, giữ nguyên

@thule Trang điểm đến tải nhanh hơn trên điện thoại (đo thật trên bản production, 5 lần):

| Trang | Trước | Sau |
|---|---|---|
| /destinations/bhutan | 3,95 s | 2,49 s |
| /destinations | 2,46 s | 1,38 s |

Cách làm: ảnh nằm dưới màn hình đầu chỉ tải khi khách cuộn tới; ảnh đầu trang dùng đúng kích cỡ.

## 3. PR-25 (Booking) — mới S259

@thule Hai phần giao diện Booking theo bản thiết kế Figma đã lên bản Dev (30/10):
- **Khách sạn** mở dạng lưới ảnh: mỗi khách sạn có ảnh đầu tiên của nhà cung cấp (hoặc ô "No photo"), số ảnh, địa
  điểm, hạng sao, nhà cung cấp, số loại phòng và giá đang áp dụng, trạng thái; có nút chuyển sang dạng bảng như cũ.
- **Hoá đơn và Thanh toán**: mỗi dòng có menu thao tác (xem hoá đơn, mở hồ sơ chuyến, huỷ hoá đơn khi được phép; với
  thanh toán: xem, tải chứng từ, huỷ khi được phép), không cần mở trang chi tiết trước.
- Toàn bộ ô nhập liệu trong Booking đổi sang bộ giao diện chung với các app khác (cùng kiểu, cùng trạng thái lỗi).

Ảnh đính kèm (theo thứ tự): 1. lưới khách sạn; 2. bảng hoá đơn có menu dòng. Ảnh chụp từ bản chạy thử giao diện với dữ
liệu mẫu trên màn hình 1440 px; bản Dev với dữ liệu thật chưa chụp lại.

| Câu | Bằng chứng |
|---|---|
| Lưới ảnh khách sạn + menu dòng hoá đơn/thanh toán | Booking #156 `45de036`, Deploy Dev xanh; bộ test bố cục 281/281 |
| Ảnh | `evidence/booking-hotels-luoi-anh.png`, `evidence/booking-hoa-don-menu.png` (dữ liệu mẫu) |

## 4. PR-26 (CRM cho đại lý) — nháp S258 cập nhật: bước xác nhận đã xong

@thule Kiểm thử đầy đủ trên môi trường Dev (30/10) với đại lý thử:
- Một chuyến đi chạy trọn từ Yêu cầu → Báo giá → Đặt cọc → Đã đặt → Đang đi → **Hoàn tất**, có dịch vụ của nhà cung cấp
  riêng của đại lý.
- Tài khoản trợ lý của đại lý đọc 7 trang có tiền: **không thấy lãi / giá net / hoa hồng**; chủ đại lý vẫn thấy đủ.
- **Sản phẩm Adventure Asia trong đề xuất, trọn vòng:** báo giá theo giá Booking thật → giữ chỗ → khách chấp nhận →
  hệ thống tự tạo dòng dịch vụ AA với giá vốn đã khoá → khách đặt cọc (540 USD) → chuyến chuyển sang **Đã đặt** →
  **Booking xác nhận đặt chỗ** cho cả bộ dịch vụ (16/16 bước đạt). Giữ chỗ hết hạn thì hệ thống từ chối và mời báo giá
  lại.
- Tài khoản quản trị nội bộ không vào được cổng của đại lý.

| Câu | Bằng chứng |
|---|---|
| Hoàn tất, nhà cung cấp riêng, trợ lý không thấy lãi, quản trị không vào được cổng | S258 proofs (evidence S258) |
| Báo giá → giữ chỗ → chấp nhận → dòng AA → cọc → Đã đặt → Booking xác nhận | S259 `20261030T043644Z-cm3-confirm.json`, 16/16 PASS; Booking #155, Partner #128 |

## Kết quả đăng

**Chưa đăng:** tech lead 30/10 ~13:45 bảo gom tiếp sang phiên sau (S260). Phiên sau rà lại số liệu trước khi đưa duyệt.
