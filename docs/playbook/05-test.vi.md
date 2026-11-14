---
id: GUIDE-14-test
title: "Pha 5: Kiểm thử"
description: Chứng minh một thay đổi chạy đúng trước khi người dùng thấy nó - các lớp kiểm thử, checklist cổng G5, kiểm bảo mật, UAT và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-build, GUIDE-14-release]
lang: vi
translation_of: docs/playbook/05-test.md
---

# Pha 5: Kiểm thử

**Mục tiêu:** chứng minh thay đổi chạy đúng trước khi người dùng thấy nó. **Người chịu trách nhiệm cuối:** tech lead;
chủ doanh nghiệp được hỏi ý kiến cho UAT. **Theo:** OWASP ASVS 5.0 mức 1 (mức 2 cho xác thực, thanh toán và dữ liệu cá
nhân), ISO/IEC 25010:2023, phát hiện của DORA rằng việc giao hàng có AI hỗ trợ chỉ ổn định khi có test mạnh và phản hồi
nhanh.

## Sản phẩm bàn giao

| Sản phẩm | Mẫu |
|---|---|
| Chiến lược kiểm thử: kiểm gì ở lớp nào, cái gì chặn merge | [Chiến lược kiểm thử](../templates/test-strategy.vi.md) |
| Unit test và integration test; mẫu dữ liệu hợp đồng; UI smoke | theo từng repo |
| Kiểm end-to-end về giao diện và có đăng nhập ở bề rộng desktop và điện thoại, sáng và tối | theo từng repo |
| Eval regression cho thay đổi AI (prompt, model hay route) | theo từng repo |
| Probe cách ly cho thay đổi về tenancy | theo từng repo |
| Checklist bảo mật cho vùng bị đụng tới | [Checklist bảo mật](../templates/security-checklist.vi.md) |
| Báo cáo UAT cho tính năng kinh doanh thấy được | [Báo cáo UAT](../templates/uat-report.md) |

## Cổng G5: sẵn sàng phát hành

| # | Câu hỏi |
|---|---|
| 1 | Mọi check có xanh, không chỉ các check bắt buộc, và không còn gì đang chờ không? |
| 2 | Một lớp rủi ro đã có agent review độc lập chưa, và mọi phát hiện đã sửa hoặc ghi lại chưa? |
| 3 | Các mục ASVS mức 1 của vùng bị đụng tới đã kiểm chưa (mức 2 khi áp dụng)? |
| 4 | Với một `fix`: test từng hỏng trước khi sửa giờ có qua không? |
| 5 | Với một thay đổi AI: eval regression có xanh trên tập cố định không? |
| 6 | Với một thay đổi tenancy: probe cách ly có qua không? |
| 7 | Với một tính năng thấy được: UI đã kiểm ở cả hai bề rộng và hai chủ đề màu, không có lỗi console chưa? |

## Lỗi hay gặp

- Chạy lại một test chập chờn tới khi nó qua thay vì sửa hoặc cách ly nó.
- Gọi một model hay API trả phí từ CI thay vì một response đã ghi sẵn.
- Chép dữ liệu khách hàng thật vào fixture của test.
- Merge khi "check bắt buộc xanh" trong khi một check không bắt buộc đang đỏ.
- UAT một tính năng mà chủ doanh nghiệp chưa từng thấy mô tả.
