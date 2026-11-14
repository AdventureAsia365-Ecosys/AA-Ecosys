---
id: TPL-01-retirement-checklist
title: Checklist ngừng
description: Cách đóng một sản phẩm, app, tính năng hay môi trường cho gọn, không còn gì chạy, lưu trữ hay bị tính tiền.
type: template
status: draft
owner: nghiep
audience: [owner, engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01]
lang: vi
translation_of: docs/templates/retirement-checklist.md
---

# Checklist ngừng

Playbook dự án mới, pha 9 Ngừng, cổng G8. Chép danh sách vào issue ngừng. Chủ doanh nghiệp chịu trách nhiệm cuối; tech
lead thực hiện. Cổng G8 chỉ qua khi hoá đơn cloud và inventory cho thấy không còn gì. Các trường hợp AA làm nền cho nó:
việc gỡ một tài khoản khỏi hệ sinh thái (ADR 0001a), lan truyền khi ngừng tour (ADR 0015) và sổ bảng chết.

## 1. Quyết định

- [ ] ADR ngừng: ngừng cái gì, vì sao, ngày nào, cái gì thay thế, ai bị ảnh hưởng.
- [ ] Đã ghi lại lời đồng ý của chủ doanh nghiệp, kèm thời hạn báo trước.

## 2. Báo

- [ ] Báo người dùng và tenant trước ít nhất 30 ngày (hoặc theo thời hạn trong hợp đồng), kèm đường xuất dữ liệu.
- [ ] Đã báo bên dùng hợp đồng; phiên bản lớn cuối cùng của hợp đồng được phục vụ song song ít nhất 30 ngày.
- [ ] Đã báo nhà cung cấp; đặt ngày kết thúc cho các gói đăng ký và hợp đồng.

## 3. Dữ liệu

- [ ] Đã giao bản xuất dữ liệu cho chủ của nó, ở định dạng mở, kèm checksum.
- [ ] Mỗi loại dữ liệu được giữ hoặc xoá theo luật lưu giữ của nó (giữ các bản ghi bị giữ vì pháp lý và kế toán theo yêu cầu).
- [ ] Việc xoá theo quy trình chạy thử: đưa số đếm chính xác, chụp snapshot, ghi lại lời duyệt, kiểm lại.
- [ ] Bảng và schema được chuyển vào cách ly trước, drop sau thời gian chờ; đã cập nhật các dòng sổ đăng ký.

## 4. Lưu lượng

- [ ] Route trả về tombstone (HTTP 410 kèm một thông điệp ngắn) hoặc chuyển hướng tới bản thay thế.
- [ ] Gỡ bản ghi DNS, chứng chỉ và luật load balancer sau thời gian tombstone.
- [ ] Dừng và xoá job theo lịch, hàng đợi và webhook; huỷ đăng ký callback của bên thứ ba.

## 5. Hạ tầng

- [ ] Kế hoạch destroy của hạ tầng dạng code đã được review (liệt kê từng resource), rồi áp từ CI.
- [ ] Tìm resource ngoài IaC theo tag và theo inventory, rồi gỡ.
- [ ] Xoá secret (xoay trước nếu chúng từng được dùng chung); gỡ IAM role, client danh tính và credential CI.
- [ ] Xoá hoặc đặt hết hạn image container, bucket, snapshot và log group, theo thời hạn lưu.
- [ ] Gỡ ngân sách và alarm của phần đã ngừng sau hoá đơn cuối cùng.

## 6. Chứng minh bằng không

- [ ] Inventory và tìm theo tag cho thấy không còn resource nào.
- [ ] Sau một ngày tính tiền trọn vẹn, chi phí theo tag và theo dịch vụ là 0 USD cho phần đã ngừng.

## 7. Đóng

- [ ] Tài liệu chuyển `deprecated` hoặc `archived` kèm con trỏ tới bản thay thế; đã cập nhật danh mục.
- [ ] Chỉ dẫn, skill và hook cho agent không còn nhắc tới nó.
- [ ] Một dòng bài học cuối: lần sau làm khác đi ở đâu.
