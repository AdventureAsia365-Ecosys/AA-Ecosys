---
id: TPL-01-session
title: Mẫu checklist phiên và log phiên
description: Các bước bắt đầu, trong phiên và đóng phiên của một phiên làm việc của agent, và hình dạng log phiên nó để lại.
type: template
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, skill/aa-session/SKILL.md]
lang: vi
translation_of: docs/templates/session-checklist.md
---

# Mẫu checklist phiên và log phiên

Nghi thức phiên chung (playbook dự án mới, trang agent). Bản riêng của AA, kèm kho memory, các phép kiểm live và cập nhật
kinh doanh, là skill `skill/aa-session/SKILL.md`. Giữ checklist sống thành một file nháp trong phiên; log chỉ viết một
lần, lúc đóng phiên, từ trạng thái đã kiểm.

## Bắt đầu

- [ ] Đọc log phiên gần nhất, backlog sống và file kế hoạch.
- [ ] Kiểm trạng thái live: danh tính cloud, các service và commit của chúng, lượt chạy job đang mở, PR đang mở, CI trên
  nhánh main.
- [ ] Đề xuất 3 tới 5 issue từ kế hoạch, theo thứ tự slot, mỗi issue một tới ba dòng lời thường; nói vì sao bỏ qua issue
  nào.
- [ ] Bắt đầu checklist sống với danh sách đã duyệt.

## Trong phiên

- [ ] Mỗi issue bắt đầu bằng việc kiểm Definition of Ready và mở ghi chú triển khai.
- [ ] Checklist được cập nhật sau mỗi bước xong.
- [ ] Tìm ra nguyên nhân gốc nghĩa là viết ngay một dòng bài học, kèm guard sẽ chặn nó lần sau.
- [ ] Việc còn lại làm được thì làm trong phiên, không liệt kê thành lời nhắc.

## Đóng phiên

1. Làm xong việc, rồi đồng bộ công cụ theo dõi việc kèm bằng chứng.
2. Chụp trạng thái live (service và commit, health, migration mới nhất, bảng job, PR đang mở).
3. Bài học: các dòng chờ được thêm vào sổ bài học, mỗi dòng có trường guard.
4. Soạn nháp cập nhật kinh doanh, tech lead duyệt, rồi mới đăng.
5. Sau đó viết log phiên và backlog, dùng số liệu từ snapshot.
6. Mọi repo về nhánh main với cây sạch.

## Hình dạng log phiên

```markdown
# S<nnn> — <ngày> — <chủ đề>

Tác nhân: <công cụ và model>. Issue: <các mã>.

## Đã xong (đã kiểm)
- <issue>: <cái gì, link bằng chứng>

## Đang làm
- <issue>: <trạng thái, còn lại gì, ai gỡ chặn>

## Quyết định
- <quyết định, do ai>

## Trạng thái live
<link tới snapshot>

## Bài học
- <dòng bài học, guard>

## Tiếp theo
- <issue đầu tiên của phiên sau và vì sao>
```
