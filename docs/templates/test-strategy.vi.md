---
id: ARCH-00-test-strategy-replace-me
title: Chiến lược kiểm thử - <dự án hoặc repo>
description: <Một câu - kiểm gì ở lớp nào, cái gì chặn merge và cái gì chạy sau deploy.>
type: explanation
status: draft
owner: replace-me
audience: [engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 180
related: []
lang: vi
translation_of: docs/templates/test-strategy.md
---

# Chiến lược kiểm thử - <dự án hoặc repo>

<!-- Playbook dự án mới, pha 5 Kiểm thử, cổng G5. Một trang nói kiểm gì ở đâu, để không ai phải tranh luận lại ở từng PR.
Cổng là "mọi check đều xanh, không chỉ các check bắt buộc". Xoá ghi chú này. -->

## 1. Các lớp

| Lớp | Chứng minh điều gì | Công cụ | Chạy khi | Chặn merge? |
|---|---|---|---|---|
| Unit | Logic thuần: luật, bộ phân tích, phép tính | <pytest, vitest> | mỗi PR | có |
| Integration | Code chạy với một cơ sở dữ liệu hay dịch vụ thật trong container | <pytest + service Postgres> | mỗi PR | có |
| Hợp đồng | Hình dạng tạo ra và dùng khớp với hợp đồng đã công bố và các mẫu của nó | <JSON Schema, OpenAPI diff> | mỗi PR đụng tới một hợp đồng | có |
| UI smoke | Các trang chính hiện ra, không lỗi console, thao tác chính chạy được | <Playwright> | mỗi PR đụng tới web app | có |
| E2E giao diện và có đăng nhập | Bố cục ở bề rộng desktop và điện thoại, sáng và tối; luồng đăng nhập thật | <Playwright> | trước khi phát hành | có, cho bản phát hành |
| Probe cách ly | Một tenant không đọc hay ghi được dữ liệu của tenant khác | <script probe> | mỗi thay đổi tenancy; hằng đêm | có |
| Eval regression AI | Chất lượng đầu ra LLM trên một tập cố định không giảm | <eval runner, golden set> | thay đổi prompt, model hay route | có |
| Kiểm sau deploy | Endpoint live trả đúng hình dạng và commit mới | <script smoke> | sau mỗi lần deploy | thay đổi chưa Done tới khi xanh |

## 2. Luật

- Sửa một lỗi bắt đầu bằng một test hỏng tái hiện lỗi đó (đường đi `fix`).
- Test cần một lần gọi trả phí thì dùng response đã ghi sẵn, không bao giờ gọi trả phí thật trong CI.
- Dữ liệu test là dữ liệu bịa; không bao giờ là bản chép dữ liệu khách hàng thật.
- Test chập chờn được sửa hoặc cách ly kèm một issue trong vòng một phiên; không bao giờ chạy lại tới khi xanh.
- Giới hạn độ phủ và sức khoẻ code chỉ đi lên (ratchet); một PR không được làm chúng giảm.

## 3. Những gì không kiểm, và vì sao

<Các vùng để cho UAT thủ công hoặc giám sát, kèm lý do và người chịu rủi ro.>

## 4. UAT

Tính năng kinh doanh thấy được có một báo cáo UAT (`uat-report.md`) được chủ doanh nghiệp hoặc vai trò dùng tính năng đó
ký xác nhận.
