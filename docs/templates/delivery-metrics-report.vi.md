---
id: OPS-00-delivery-yyyy-ww
title: Chỉ số giao hàng <YYYY>-W<ww>
description: <Một câu - các chỉ số DORA và luồng của tuần so với baseline, và một thay đổi chúng gợi ý.>
type: report
status: draft
owner: replace-me
audience: [engineer, cto, pm, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: []
lang: vi
translation_of: docs/templates/delivery-metrics-report.md
---

# Chỉ số giao hàng <YYYY>-W<ww>

<!-- Playbook dự án mới, pha 7 Vận hành (trang chỉ số). Một script tính từ git, các lượt deploy, bản ghi sự cố và công
cụ theo dõi việc; không ai gõ tay số liệu. So với baseline lấy trước ngày 60. Một chỉ số là một câu hỏi, không phải mục
tiêu: không bao giờ thưởng theo một con số. Xoá ghi chú này. -->

## 1. DORA

| Chỉ số | Định nghĩa | Tuần này | Trung vị 4 tuần | Baseline | Xu hướng |
|---|---|---|---|---|---|
| Change lead time | Từ commit tới lúc chạy trên môi trường live, trung vị | <...> | <...> | <...> | <tăng / giảm / đi ngang> |
| Deployment frequency | Số lần deploy lên môi trường live mỗi ngày | <...> | | | |
| Failed deployment recovery time | Từ lần deploy hỏng tới lúc khôi phục, trung vị | <...> | | | |
| Change fail rate | Số lần deploy gây rollback, hotfix hay sự cố / tổng số lần deploy | <...> | | | |
| Deployment rework rate | Số lần deploy ngoài kế hoạch để sửa vấn đề người dùng thấy / tổng số lần deploy | <...> | | | |

## 2. Luồng

| Chỉ số | Tuần này | Trung vị 4 tuần |
|---|---|---|
| Work in progress (số issue In Progress) | <...> | <...> |
| Throughput (số issue Done) | <...> | |
| Work item age, issue In Progress cũ nhất | <ngày> | |
| Cycle time (In Progress tới Done), trung vị | <ngày> | |

## 3. Đọc số

- <Cái gì đã đổi và nguyên nhân có khả năng.>
- <Một thay đổi để thử tuần tới, hoặc "không có".>

## 4. Nguồn

<Tên và phiên bản script, các query hoặc file nó đọc, thời điểm nó chạy.>
