---
id: GUIDE-14-metrics
title: Chỉ số của playbook
description: Cách một dự án đo giao hàng (DORA), luồng (Kanban) và mức sẵn sàng AI (năng lực AI của DORA), và đo bao lâu một lần.
type: reference
status: draft
owner: nghiep
audience: [cto, pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-operate, GUIDE-14-adoption]
lang: vi
translation_of: docs/playbook/metrics.md
---

# Chỉ số của playbook

Chỉ số là câu hỏi, không phải mục tiêu. Chúng được một script tính từ các bản ghi đội đã có sẵn; không ai gõ tay, và
không mua công cụ trả phí nào trước khi có lưu lượng prod. Mẫu báo cáo:
[báo cáo chỉ số giao hàng](../templates/delivery-metrics-report.vi.md).

## Giao hàng: năm chỉ số DORA

| Chỉ số | Định nghĩa | Nguồn | Nhịp |
|---|---|---|---|
| Change lead time | Từ commit tới lúc chạy trên môi trường live, trung vị | Git và các lượt deploy | hằng tuần |
| Deployment frequency | Số lần deploy lên môi trường live mỗi ngày | Các lượt deploy | hằng tuần |
| Failed deployment recovery time | Từ một lần deploy hỏng tới lúc dịch vụ được khôi phục, trung vị | Các lượt deploy và bản ghi sự cố | hằng tuần |
| Change fail rate | Số lần deploy gây rollback, hotfix hay sự cố, trên tổng số lần deploy | Các lượt deploy và bản ghi sự cố | hằng tuần |
| Deployment rework rate | Số lần deploy ngoài kế hoạch để sửa một vấn đề người dùng thấy, trên tổng số lần deploy | Các lượt deploy và công cụ theo dõi việc | hằng tuần |

## Luồng: bốn chỉ số Kanban

| Chỉ số | Định nghĩa |
|---|---|
| Work in progress | Số issue đang In Progress (mặc định giới hạn 8) |
| Throughput | Số issue Done mỗi tuần |
| Work item age | Số ngày một issue In Progress đã mở; cái cũ nhất là cái cần nhìn |
| Cycle time | Từ In Progress tới Done, trung vị |

## Mức sẵn sàng AI: bảy năng lực AI của DORA

Chấm mỗi năng lực từ 0 tới 3 một lần cho mỗi dự án và ở mỗi đợt rà soát 90 ngày.

| Năng lực | Tốt trông thế nào trong bộ kit |
|---|---|
| Lập trường về AI rõ ràng và được truyền đạt | `AGENTS.md` cùng luật của dự án: agent được làm gì, không bao giờ làm gì |
| Hệ sinh thái dữ liệu lành mạnh | Data standards, mỗi thực thể một bên ghi, hợp đồng |
| Dữ liệu nội bộ AI truy cập được | Một reference schema sinh tự động, một danh mục tài liệu và một mục lục `llms.txt` |
| Quản lý phiên bản mạnh | Luồng trunk-based, merge queue, image bất biến |
| Làm theo lô nhỏ | Mỗi issue một sản phẩm bàn giao; 3 tới 5 issue mỗi phiên |
| Tập trung vào người dùng | Một chỉ số thành công trong điều lệ; UAT cho tính năng thấy được |
| Nền tảng nội bộ chất lượng | Repo mẫu, skill chung, hook và công cụ ship |

## Đọc các con số

- So với baseline của chính dự án (lấy trước ngày 60), không so với đội khác.
- Change fail rate tăng cùng lúc với deployment frequency tăng nghĩa là test và check không theo kịp.
- Work item age tăng nghĩa là bắt đầu quá nhiều việc; làm xong rồi mới bắt đầu.
