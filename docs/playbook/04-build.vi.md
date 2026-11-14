---
id: GUIDE-14-build
title: "Pha 4: Xây dựng"
description: Biến các issue nhỏ, đã sẵn sàng thành thay đổi đã được review - Definition of Ready, các đường đi, appetite, lane và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [engineer, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-test, GUIDE-14-agents, TPL-01-dor]
lang: vi
translation_of: docs/playbook/04-build.md
---

# Pha 4: Xây dựng

**Mục tiêu:** các issue nhỏ, đã sẵn sàng được biến thành thay đổi đã review. **Người chịu trách nhiệm cuối:** tech lead.
**Theo:** Kanban (làm cho thấy được, giới hạn WIP, quản lý luồng), Shape Up (appetite, circuit breaker), trunk-based
development, Scrum (Definition of Done). Không sprint: một hàng đợi có thứ tự, các phiên kéo việc từ đầu hàng.

## Cổng G4, cho từng issue: Definition of Ready

Việc chỉ bắt đầu khi issue qua [Definition of Ready](../templates/definition-of-ready.md): vấn đề có bằng chứng, mục
tiêu, phạm vi có phần "ngoài", 3 tới 6 dòng Done-when kiểm được trên môi trường thật, cách kiểm, lớp rủi ro, phụ thuộc,
ảnh hưởng tài liệu, chi phí, **đường đi** và **appetite**.

## Các đường đi

Đường đi quyết định một issue cần bao nhiêu quy trình, để một lần sửa lỗi chính tả không phải trả giá bằng nghi thức của
một tính năng.

| Đường đi | Khi nào | Các bước và sản phẩm | Review |
|---|---|---|---|
| `fix` | Một lỗi có triệu chứng đã biết | Test hỏng trước, rồi mới sửa; ghi chú triển khai ngắn | CI; một góc nhìn (đúng đắn) |
| `small` | Không có hợp đồng, bảng hay trang mới | Ghi chú triển khai | CI; một góc nhìn |
| `feature` | Hành vi mới người dùng thấy được | Mục Plan ở đầu ghi chú triển khai, rồi mới xây; kiểm UI khi thấy được | CI; góc nhìn đúng đắn |
| `risky` | Xác thực hay phân quyền, migration hay schema, CI hay secret, xoá dữ liệu | Như `feature`, cộng review độc lập trước khi merge | CI; góc nhìn đúng đắn cộng bảo mật và dữ liệu |

## Sản phẩm bàn giao

- Thay đổi trên các nhánh hoặc worktree ngắn tạo từ main mới nhất; tiêu đề commit theo conventional commit; mã issue
  trong thân.
- Mỗi issue một [ghi chú triển khai](../templates/implementation-note.md), viết trong lúc làm: Plan, Decisions,
  Changed, Tradeoffs, Should know.
- Migration theo expand / contract ([mẫu migration](../templates/migration-file.vi.md)).
- Hợp đồng được cập nhật kèm mẫu dữ liệu ([mẫu hợp đồng](../templates/contract.vi.md)).
- Dòng settings cho mọi ngưỡng mới ([mẫu settings](../templates/settings-entry.vi.md)); dòng sổ đăng ký cờ cho mọi cờ
  mới.
- Một dòng bài học mỗi khi tìm ra nguyên nhân gốc, kèm guard sẽ chặn lỗi đó lần sau.

## Luật về luồng

- Tối đa 8 issue In Progress. Làm xong rồi mới bắt đầu: một issue bị đứng thì đóng kèm bằng chứng, làm cho xong, hoặc
  trả về backlog kèm lý do.
- Vượt appetite: dừng, định hình lại hoặc tách (circuit breaker). Không lặng lẽ làm tiếp.
- Done-when đóng băng khi issue sang In Progress; phạm vi mới thành một issue mới có liên kết.
- Một issue là một lát việc bàn giao được: khoảng một PR hoặc một nhóm PR nhỏ.

## Lỗi hay gặp

- Bắt đầu từ một issue có Done-when ghi "code đã merge".
- Một `fix` không có test hỏng, nên cùng lỗi đó có thể quay lại mà không ai thấy.
- Một diff đụng tới file mà Plan chưa từng nêu, không cập nhật Plan.
- Ngưỡng viết cứng trong code thay vì settings.
- Viết ghi chú triển khai ở cuối, theo trí nhớ.
