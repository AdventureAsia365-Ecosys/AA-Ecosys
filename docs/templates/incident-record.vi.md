---
id: OPS-04-inc-yyyy-mm-dd-slug
title: "Sự cố: <tiêu đề ngắn> (<YYYY-MM-DD>)"
description: <Một câu - cái gì hỏng, mức độ nghiêm trọng, kéo dài bao lâu, và có postmortem theo sau không.>
type: report
status: draft
owner: replace-me
audience: [engineer, devops, cto, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: [OPS-04]
lang: vi
translation_of: docs/templates/incident-record.md
---

# Sự cố: <tiêu đề ngắn> (<YYYY-MM-DD>)

<!-- Bản ghi sự cố gọn (playbook dự án mới, pha 7 Vận hành; quản lý sự cố của ITIL, đã rút gọn). Mở nó khi sự cố bắt đầu,
điền dần trong lúc xử lý, đóng khi dịch vụ được khôi phục. SEV1 và SEV2 còn có postmortem (postmortem.md) khi một điều
kiện ở mục đầu tiên của nó áp dụng. Không secret, account ID hay dữ liệu cá nhân. Xoá ghi chú này. -->

| Trường | Giá trị |
|---|---|
| Mức nghiêm trọng | <SEV1: người dùng không dùng được sản phẩm hoặc dữ liệu bị lộ hay mất / SEV2: suy giảm nhưng có cách lách / SEV3: chỉ nội bộ> |
| Trạng thái | <mở / đã giảm nhẹ / đã giải quyết> |
| Bắt đầu (UTC+7) | <hh:mm> |
| Phát hiện bởi | <alarm, người, người dùng báo> |
| Người dẫn xử lý | <vai trò> |
| Đã báo ai, khi nào | <chủ doanh nghiệp lúc hh:mm; tenant lúc hh:mm> |
| Khôi phục (UTC+7) | <hh:mm> |
| Postmortem | <có: link / không: vì sao> |

## Dòng thời gian

| Thời điểm | Chuyện gì xảy ra hoặc đã làm gì | Ai |
|---|---|---|
| <hh:mm> | <...> | <vai trò> |

## Tác động

<Ai bị ảnh hưởng, họ không làm được gì, dữ liệu liên quan, chi phí liên quan.>

## Giảm nhẹ

<Cái gì đã khôi phục dịch vụ: rollback, tắt cờ, scale up, sửa tay. Lệnh hoặc link.>

## Việc tiếp theo

| Hành động | Người phụ trách | Link công cụ theo dõi việc |
|---|---|---|
| <...> | <vai trò> | <issue> |
