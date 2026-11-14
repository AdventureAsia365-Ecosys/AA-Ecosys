---
id: GUIDE-14-setup
title: "Pha 3: Dựng khung"
description: Dựng một khung chạy được, build được, deploy lên Dev và được quan sát, với mọi guard bật - sản phẩm bàn giao, checklist cổng G3 và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-architecture, GUIDE-14-adoption, GUIDE-08]
lang: vi
translation_of: docs/playbook/03-setup.md
---

# Pha 3: Dựng khung

**Mục tiêu:** một khung chạy được (walking skeleton): một sản phẩm rỗng build được, deploy lên Dev và được quan sát, với
mọi guard bật ngay từ commit đầu tiên. **Người chịu trách nhiệm cuối:** tech lead. **Theo:** Twelve-Factor App (cấu hình
deploy nằm trong môi trường), trunk-based development, AGENTS.md (chỉ dẫn cho agent), FinOps (tag và ngân sách từ ngày
đầu).

Trang này cũng lấp chỗ "Thêm một app mới" (GUIDE-08) trong danh mục. Với một app mới bên trong AA-Ecosys,
[bản áp dụng AA](aa-profile.vi.md) bổ sung playbook mười hai bước của ADR 0008.

## Sản phẩm bàn giao

| Vùng | Sản phẩm |
|---|---|
| Repo | Sinh từ repo mẫu (đã lên kế hoạch, AA-1103); bật branch protection và merge queue |
| CI | Xanh trên một PR rỗng: test, lint, check tiêu đề PR, quét secret (PR và toàn lịch sử), docs lint, workflow lint |
| Guard local | Hook pre-push với các check nhanh; ratchet sức khoẻ code và độ phủ với baseline rỗng |
| Agent | `AGENTS.md` là nguồn chỉ dẫn, `CLAUDE.md` import nó, các hook guardrail kèm test |
| Công cụ theo dõi việc | Project, file kế hoạch và backlog đầu tiên |
| Cloud | Tài khoản và role qua hạ tầng dạng code; OIDC từ CI tới cloud (không key tĩnh); tag và một cảnh báo ngân sách |
| Secret | Các mục trong kho secret và một sổ đăng ký secret (chỉ tên) |
| Danh tính | Mỗi app một client của nhà cung cấp danh tính |
| Cơ sở dữ liệu | Schema với role chủ và role runtime; migration đầu tiên `<prefix>-001` áp từ CI ([mẫu migration](../templates/migration-file.vi.md)) |
| Dịch vụ nền tảng | Bảng job và worker; registry settings ([mẫu settings](../templates/settings-entry.vi.md)) |
| Quan sát | Log có cấu trúc, theo dõi lỗi, `/health` (trả về SHA của commit) và `/health/ready` |

## Cổng G3: khung chạy được

| # | Câu hỏi |
|---|---|
| 1 | `/health` trên Dev có trả về SHA của commit, do CI deploy (không phải deploy tay) không? |
| 2 | Mọi check có xanh trên một PR rỗng không? |
| 3 | Đã có cảnh báo ngân sách ở đúng con số đã báo giá ở G1 chưa? |
| 4 | Nếu nhiều tenant: probe cách ly có qua không (tenant A không thấy tenant B)? |
| 5 | Không có key cloud tĩnh nào trong CI hay trên một profile máy cá nhân mà CI dùng chứ? |
| 6 | Mọi resource đã gắn tag app và môi trường chưa? |
| 7 | Một bản clone mới có chạy được local chỉ bằng các bước "Chạy local" trong `CONTEXT.md` không? |

## Lỗi hay gặp

- Xây tính năng trước khi khung deploy được; mọi bước sau đó chứng minh chậm hơn.
- Bật guard "để sau": một ratchet bắt đầu rỗng thì miễn phí, thêm nó vào một codebase lớn là cả một dự án.
- Key cloud dài hạn trong CI thay vì OIDC.
- Một `/health` trả 200 mà không nói commit nào đang chạy.
- Áp migration đầu tiên từ máy cá nhân.
