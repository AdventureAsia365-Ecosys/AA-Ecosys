---
id: OPS-00-slo-replace-me
title: Chính sách SLO và error budget - <service>
description: <Một câu - mục tiêu mức dịch vụ của service và đội làm gì khi error budget cạn.>
type: reference
status: draft
owner: replace-me
audience: [owner, engineer, devops, cto]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 90
related: []
lang: vi
translation_of: docs/templates/slo-error-budget.md
---

# Chính sách SLO và error budget - <service>

<!-- Playbook dự án mới, pha 8 Mở rộng. Viết từ sớm, BẬT ở cổng G7 (prod đầu tiên hoặc tenant trả tiền đầu tiên, quyết
định D10 của bộ kit); trên Dev nó vẫn là bản nháp. Dựa trên Google SRE workbook (triển khai SLO, chính sách error
budget). Chủ doanh nghiệp đồng ý mục tiêu; tech lead phụ trách việc đo. Xoá ghi chú này. -->

## 1. Service và người dùng

<Service làm gì và cho ai; hành trình người dùng mà SLO bảo vệ.>

## 2. SLI và SLO

| SLI (đo cái gì) | Sự kiện tốt | Sự kiện hợp lệ | SLO (mục tiêu trong 28 ngày) | Nguồn |
|---|---|---|---|---|
| Độ sẵn sàng | <request được trả lời với status không phải 5xx> | <mọi request trừ health check> | <99,5 %> | <log load balancer> |
| Độ trễ | <request được trả lời trong 800 ms> | <mọi request> | <95 %> | <...> |
| Độ mới (job) | <job xong trong cửa sổ của nó> | <mọi job theo lịch> | <99 %> | <bảng job> |

Error budget = 100 % trừ SLO. Ở mức 99,5 % trong 28 ngày, đó là khoảng 3 giờ 22 phút "phút xấu".

## 3. Chính sách

| Budget còn lại trong cửa sổ | Đội làm gì |
|---|---|
| Trên 50 % | Ship như bình thường |
| 25 % tới 50 % | Vẫn phát hành; việc về độ tin cậy lên đầu hàng đợi |
| Dưới 25 % | Chỉ ship bản sửa và việc về độ tin cậy; thay đổi rủi ro phải chờ |
| Đã cạn | Đóng băng tính năng cho service tới khi budget hồi lại hoặc chủ doanh nghiệp chấp nhận rủi ro bằng văn bản |

- Một sự cố đơn lẻ dùng hơn 20 % budget thì có postmortem.
- Ngoại lệ do chủ doanh nghiệp và tech lead cùng quyết và ghi lại kèm ngày.

## 4. Rà soát

Hằng tháng, cùng đợt rà soát chi phí và dung lượng; mục tiêu chỉ đổi qua một quyết định được ghi lại.
