---
id: PROD-00-raid-replace-me
title: Sổ RAID - <dự án>
description: <Một câu - các rủi ro, giả định, vấn đề và phụ thuộc đang mở, và ai phụ trách từng cái.>
type: reference
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 30
related: []
lang: vi
translation_of: docs/templates/risk-register.md
---

# Sổ RAID - <dự án>

<!-- Playbook dự án mới, pha 1 và mọi pha sau đó. RAID = rủi ro, giả định, vấn đề, phụ thuộc. Mục 11 của arc42 trỏ về
đây. Rà soát ở mỗi lần đóng phiên và ở mỗi cổng. Một rủi ro xảy ra thì thành vấn đề; một giả định hoá ra sai thì thành
rủi ro hoặc vấn đề. Xoá ghi chú này. -->

## Thang đo

- **Khả năng** và **tác động**: 1 thấp, 2 trung bình, 3 cao. **Điểm** = khả năng x tác động. Xử lý điểm 6 và 9 trước.
- **Trạng thái:** mở, theo dõi, đóng (kèm ngày và lý do).

## Rủi ro

| ID | Rủi ro (nếu ... thì ...) | K | T | Điểm | Người phụ trách | Giảm thiểu | Dấu hiệu để hành động | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| R1 | <Nếu X xảy ra, thì Y> | <1-3> | <1-3> | <1-9> | <vai trò> | <cái gì làm giảm nó> | <tín hiệu> | mở |

## Giả định

| ID | Giả định | Kiểm thế nào và khi nào | Người phụ trách | Trạng thái |
|---|---|---|---|---|
| A1 | <...> | <...> | <vai trò> | mở |

## Vấn đề

| ID | Vấn đề (đang xảy ra) | Tác động | Người phụ trách | Hành động và link công cụ theo dõi việc | Trạng thái |
|---|---|---|---|---|---|
| I1 | <...> | <...> | <vai trò> | <mã issue> | mở |

## Phụ thuộc

| ID | Chúng ta phụ thuộc vào | Để làm gì | Cần trước | Người phụ trách | Trạng thái |
|---|---|---|---|---|---|
| D1 | <đội, nhà cung cấp, quyết định, migration> | <...> | <YYYY-MM-DD> | <vai trò> | mở |
