---
id: FIN-00-cost-sheet-replace-me
title: Bảng chi phí - <dự án>
description: <Một câu - dự báo chi phí chạy hằng tháng, chi phí đơn vị và mọi mục trả phí kèm lời duyệt.>
type: reference
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 30
related: []
lang: vi
translation_of: docs/templates/cost-sheet.md
---

# Bảng chi phí - <dự án>

<!-- Playbook dự án mới, pha 1 (báo giá ở cổng G1), rồi pha 7 (rà soát hằng tháng). FinOps Framework ở mức crawl /
walk: inform (tag, một nguồn chi phí), optimise (đòn bẩy rẻ nhất trước), operate (rà soát hằng tháng, ngân sách). Giá
lấy từ trang giá hoặc công cụ tính giá của nhà cung cấp cloud cho đúng region, kèm ngày đọc. Không ghi account ID ở đây.
Xoá ghi chú này. -->

## 1. Dự báo hằng tháng

| Mục | Hình dạng (kích thước, số lượng, giờ) | USD mỗi tháng | Nguồn và ngày đọc |
|---|---|---|---|
| Container | <2 task nhỏ, luôn bật> | <...> | <trang giá, YYYY-MM-DD> |
| Cơ sở dữ liệu | <instance nhỏ nhất, 20 GB> | <...> | <...> |
| Load balancer, NAT, IPv4 công khai | <dùng chung hoặc riêng> | <...> | <...> |
| Log, secret, kho image | <...> | <...> | <...> |
| LLM và API trả phí | <stage, số lần gọi mỗi ngày, đơn giá> | <...> | <...> |
| **Tổng Dev** | | **<...>** | |
| **Tổng khi có prod đầu tiên** | | **<...>** | |

## 2. Chi phí đơn vị

<USD trên mỗi tenant, mỗi booking, mỗi trang được sinh, ...> = <công thức từ ledger hoặc hoá đơn>.

## 3. Các mục trả phí và lời duyệt

Mỗi dịch vụ hay tính năng trả phí mới cần một lời đồng ý riêng sau khi báo giá; một lời duyệt chung không được tính.

| Mục | Chi phí hằng tháng | Báo giá ngày | Ai duyệt và ngày nào | Link công cụ theo dõi việc |
|---|---|---|---|---|
| <dịch vụ> | <...> | <YYYY-MM-DD> | <chủ doanh nghiệp, YYYY-MM-DD> | <issue> |

## 4. Guard

| Guard | Ngưỡng | Gửi tới |
|---|---|---|
| Ngân sách tài khoản hoặc app | <USD mỗi tháng; 80 % và 100 % thực tế, 100 % dự báo> | <e-mail, chat> |
| Cảnh báo bất thường | <tác động tính bằng USD> | <...> |
| Trần chi tiêu theo nhà cung cấp hoặc stage | <USD mỗi ngày hoặc mỗi lượt; dừng cứng hoặc chỉ cảnh báo> | <trang admin> |

## 5. Rà soát hằng tháng

| Tháng | Dự báo | Thực tế | Chênh lệch và nguyên nhân | Quyết định |
|---|---|---|---|---|
| <YYYY-MM> | <...> | <...> | <...> | <...> |
