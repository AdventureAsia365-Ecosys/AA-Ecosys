---
id: SEC-00-asvs-replace-me
title: Checklist bảo mật - <vùng hoặc bản phát hành>
description: <Một câu - các mục ASVS mức 1 đã kiểm cho vùng bị đụng tới, kèm kết quả và khoảng trống.>
type: report
status: draft
owner: replace-me
audience: [engineer, cto, cio, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: []
lang: vi
translation_of: docs/templates/security-checklist.md
---

# Checklist bảo mật - <vùng hoặc bản phát hành>

<!-- Playbook dự án mới, pha 5 và 6, cổng G5 và G6. OWASP ASVS 5.0 mức 1 là cổng phát hành cho mọi vùng; mức 2 cho xác
thực, thanh toán và dữ liệu cá nhân (quyết định D9 của bộ kit). Các dòng dưới là lời nhắc ngắn, gom theo các chương của
ASVS, không phải bản chép của chuẩn: mở bản phát hành ASVS 5.0 từ repository của OWASP để lấy đúng mã yêu cầu và ghi vào
cột "Mã ASVS". Chỉ kiểm các chương mà thay đổi đụng tới. Phát hiện bảo mật về repo public thì viết ở nơi riêng tư. Xoá ghi
chú này. -->

- **Vùng và thay đổi:** <route, trang, job, dữ liệu bị đụng tới>.
- **Mức:** <L1 | L2 vì xác thực / thanh toán / dữ liệu cá nhân>.

## Các phép kiểm

| Nhóm | Cần xác nhận | Mã ASVS | Kết quả | Bằng chứng |
|---|---|---|---|---|
| Mã hoá đầu ra và injection | Query có tham số; đầu ra được mã hoá theo ngữ cảnh; không dựng lệnh shell từ đầu vào | <...> | <đạt / khoảng trống / không áp dụng> | <test, file> |
| Kiểm đầu vào | Đầu vào được kiểm theo danh sách cho phép ở phía server; file tải lên bị giới hạn kiểu và kích thước | <...> | | |
| Xác thực | Đăng nhập qua nhà cung cấp danh tính; không tự lưu mật khẩu; giới hạn tần suất khi đăng nhập | <...> | | |
| Phiên | Token sống ngắn, được xoay, bị thu hồi khi đăng xuất; cookie `Secure`, `HttpOnly`, `SameSite` | <...> | | |
| Phân quyền | Mọi route kiểm vai trò và tenant ở server; mặc định từ chối | <...> | | |
| Bảo vệ dữ liệu | Biết các loại dữ liệu cá nhân; mã hoá khi truyền và khi lưu; không có secret hay dữ liệu cá nhân trong log | <...> | | |
| Secret và cấu hình | Secret chỉ ở kho secret; không có gì trong repo; quét secret xanh | <...> | | |
| Lỗi và log | Lỗi không hiện stack trace hay ID nội bộ; sự kiện bảo mật được log kèm ai và khi nào | <...> | | |
| Front end web | Đặt header bảo mật (CSP, HSTS, frame options); từ chối ghi chéo site | <...> | | |
| API | Lỗi dạng problem details; giới hạn kích thước danh sách và tần suất request; idempotency key cho các lần dịch chuyển tiền | <...> | | |
| Thư viện phụ thuộc | Quét lỗ hổng đã biết xanh; ghim phiên bản; action ghim theo SHA | <...> | | |

## Khoảng trống

| Khoảng trống | Rủi ro | Người phụ trách | Link công cụ theo dõi việc | Chấp nhận tới |
|---|---|---|---|---|
| <...> | <...> | <vai trò> | <issue> | <YYYY-MM-DD hoặc "sửa trước khi phát hành"> |

## Tự kiểm SAMM gọn (mỗi dự án một lần, rồi hằng năm)

Chấm mỗi business function của OWASP SAMM v2 từ 0 tới 3 và nêu một bước tiếp theo: governance, design, implementation,
verification, operations. Ở cỡ startup, đặt mục tiêu mức 1 gần như ở mọi nơi.
