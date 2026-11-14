---
id: ARCH-00-contract-replace-me
title: Hợp đồng <tên>.v<bản lớn>
description: <Một câu - hợp đồng này chở dữ liệu hay sự kiện gì, ai tạo ra và ai dùng nó.>
type: reference
status: draft
owner: replace-me
audience: [engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 180
related: []
lang: vi
translation_of: docs/templates/contract.md
---

# Hợp đồng <tên>.v<bản lớn>

<!-- Mẫu thư mục hợp đồng (playbook dự án mới, pha 2 và 4). Hợp đồng là cách duy nhất để một app đọc dữ liệu của app
khác: một view cơ sở dữ liệu, một HTTP API hoặc một sự kiện. Bố cục thư mục:
  contracts/<name>.v<major>/README.md       trang này
  contracts/<name>.v<major>/schema.json     JSON Schema (hoặc <name>.openapi.yaml cho HTTP)
  contracts/<name>.v<major>/samples/valid/*.json và samples/invalid/*.json
và một dòng trong contracts/README.md (sổ đăng ký). CI kiểm mọi mẫu hợp lệ phải qua và mọi mẫu không hợp lệ phải bị từ
chối. Xoá ghi chú này. -->

## 1. Nó chở gì

<Các thực thể và trường, bằng lời thường. Trỏ tới file schema để biết hình dạng chính xác.>

## 2. Bên tạo và bên dùng

| Vai trò | App | Đọc hoặc ghi thế nào | Từ phiên bản |
|---|---|---|---|
| Bên tạo (một) | <app> | <view, endpoint, topic sự kiện> | <1.0> |
| Bên dùng | <app> | <...> | <1.0> |

## 3. Loại và quyền truy cập

- **Loại:** <view cơ sở dữ liệu | HTTP | sự kiện>.
- **Quyền truy cập:** <role hoặc token được đọc; phạm vi tenant>.
- **Dữ liệu cá nhân:** <không có | các loại, kèm luật lưu giữ>.

## 4. Phiên bản

| Phiên bản | Ngày | Thay đổi | Phá vỡ tương thích? |
|---|---|---|---|
| 1.0 | <YYYY-MM-DD> | Phiên bản đầu tiên | - |

Phiên bản nhỏ chỉ thêm trường tuỳ chọn. Một thay đổi phá vỡ tương thích là một bản lớn mới, phục vụ song song ít nhất 30
ngày sau khi bên dùng cuối cùng đã chuyển.

## 5. Mẫu dữ liệu

- Hợp lệ: `samples/valid/<case>.json` (<mỗi ca cho thấy gì>).
- Không hợp lệ: `samples/invalid/<case>.json` (<mỗi ca phải hỏng ở điểm nào>).
