---
id: PROD-00-raci-replace-me
title: Bản đồ các bên liên quan và RACI - <dự án>
description: <Một câu - ai bị dự án ảnh hưởng, ai quyết định, và ai chịu trách nhiệm cuối cho từng pha.>
type: reference
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 90
related: []
lang: vi
translation_of: docs/templates/stakeholder-raci.md
---

# Bản đồ các bên liên quan và RACI - <dự án>

<!-- Playbook dự án mới, pha 1 Khám phá. Mỗi pha một người chịu trách nhiệm cuối (luật RACI phổ biến). Agent có thể là
người làm, không bao giờ là người chịu trách nhiệm cuối (luật riêng của AA). Tài liệu công ty gọi theo vai trò, không gọi
tên người. Xoá ghi chú này. -->

## 1. Các bên liên quan

| Bên liên quan (vai trò hoặc nhóm) | Mối quan tâm | Ảnh hưởng | Họ cần gì từ chúng ta | Kênh và nhịp |
|---|---|---|---|---|
| Chủ doanh nghiệp | <...> | cao | <quyết định, tóm tắt chi phí> | <báo cáo hằng tuần> |
| <người dùng> | <...> | <...> | <...> | <...> |
| <nhà cung cấp, đối tác, cơ quan quản lý> | <...> | <...> | <...> | <...> |

## 2. Hình dạng đội

<tech lead cùng agent | nhiều kỹ sư cùng agent | chỉ kỹ sư> (mục lục playbook, "Các hình dạng đội khác").

## 3. RACI theo pha

A = chịu trách nhiệm cuối (mỗi dòng một), R = người làm, C = được hỏi ý kiến, I = được báo.

| Pha | Chủ doanh nghiệp | Tech lead | Agent điều phối | Subagent / agent thứ hai | CI | Nhà cung cấp |
|---|---|---|---|---|---|---|
| 1 Khám phá | A | R | R | C | - | C |
| 2 Kiến trúc | C | A | R | C | - | C |
| 3 Dựng khung | I | A | R | R | R | C |
| 4 Xây dựng | I | A | R | R | R | - |
| 5 Kiểm thử | C | A | R | R | R | - |
| 6 Phát hành | I | A | R | - | R | - |
| 7 Vận hành | I | A | R | C | R | C |
| 8 Mở rộng | A | R | R | C | - | C |
| 9 Ngừng | A | R | R | C | R | C |

Chỉ đổi các giá trị mặc định ở trên khi có lý do ghi ở cột cuối của một bản ghi quyết định.

## 4. Quyền quyết định

| Quyết định | Ai quyết | Ai được hỏi ý kiến |
|---|---|---|
| Làm / không làm, phạm vi, chi tiêu mới | Chủ doanh nghiệp | Tech lead |
| Kiến trúc, ADR, merge lớp rủi ro sau khi có prod đầu tiên | Tech lead | Agent điều phối |
| Merge và deploy thường ngày trong giai đoạn dev | Agent điều phối | CI |
