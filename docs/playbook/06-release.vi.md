---
id: GUIDE-14-release
title: "Pha 6: Phát hành"
description: Đưa thay đổi lên Dev (sau này prod) và chứng minh chúng live - thứ tự deploy, Definition of Done, ghi chú phát hành và lỗi hay gặp.
type: how-to
status: draft
owner: nghiep
audience: [owner, engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-test, GUIDE-14-operate, TPL-01-release-checklist]
lang: vi
translation_of: docs/playbook/06-release.md
---

# Pha 6: Phát hành

**Mục tiêu:** thay đổi tới được Dev (sau này prod) và được chứng minh là live. **Người chịu trách nhiệm cuối:** tech
lead; chủ doanh nghiệp được báo. **Theo:** Scrum (Definition of Done), ITIL 4 (một PR xanh theo luật quyền merge là một
standard change; không có hội đồng thay đổi), trunk-based development, đánh phiên bản ngữ nghĩa với release-please.

Đã merge và xanh chưa phải là xong. Một thay đổi xong khi nó chạy trên môi trường live và một phép kiểm cho ra đúng kết
quả.

## Sản phẩm bàn giao

| Sản phẩm | Mẫu |
|---|---|
| Checklist phát hành được đánh dấu kèm bằng chứng | [Checklist phát hành](../templates/release-checklist.vi.md) |
| Migration được áp theo thứ tự qua CI | [File migration](../templates/migration-file.vi.md) |
| Cờ được đặt sang trạng thái phát hành một cách có chủ đích | Sổ đăng ký cờ của dự án |
| Kết quả kiểm sau deploy và một comment "đã kiểm live" trên issue | Checklist phát hành, mục "Đã kiểm live" |
| Ghi chú phát hành chỉ gồm việc đã kiểm | [Ghi chú phát hành](../templates/release-note.md) |
| Cập nhật cho kinh doanh bằng ngôn ngữ của chủ doanh nghiệp | Ghi chú phát hành, phần kinh doanh |

## Thứ tự deploy

1. Migration expand trước, do workflow migrate của CI áp.
2. Code chạy được với cả hình dạng cũ và mới.
3. Lật cờ khi code đã live ở mọi nơi.
4. Migration contract chỉ sau khi mọi bên đọc đã chuyển xong.

Deploy chờ trong lúc còn một job hay lượt chạy lô mà nó sẽ làm hỏng (một cổng deploy trong CI). Rollback là image bất
biến trước đó, không bao giờ build lại.

## Cổng G6: Definition of Done, đã kiểm live

| # | Câu hỏi |
|---|---|
| 1 | Đã merge với mọi check xanh chưa? |
| 2 | Rollout đã hoàn tất, mọi service của app trên cùng một commit chưa? |
| 3 | `/health` trả về SHA của commit mới và `/health/ready` xanh chưa? |
| 4 | Endpoint hay trang bị đổi có trả về đúng hình dạng mong đợi trên môi trường live, với lệnh và kết quả được giữ lại không? |
| 5 | UI đã kiểm khi thay đổi thấy được chưa? |
| 6 | Bằng chứng đã đăng lên issue, và chỉ tới lúc này mới đóng issue bằng tay chưa? |

## Quyền merge theo giai đoạn

| Giai đoạn | Ai merge |
|---|---|
| Giai đoạn dev (chưa có prod, chưa có tenant trả tiền) | Agent điều phối tự merge PR của mình sau khi CI xanh; lớp rủi ro sau một agent review độc lập. Subagent không bao giờ merge |
| Từ prod đầu tiên hoặc tenant trả tiền đầu tiên (cổng G7) | Tech lead duyệt trước khi merge các PR về IaC và IAM, migration, xác thực và bảo mật, xoá dữ liệu; các PR khác như cũ |

## Lỗi hay gặp

- Đóng issue khi merge, trước lần kiểm live.
- Một ghi chú phát hành liệt kê việc đã merge nhưng chưa bao giờ được kiểm.
- Deploy trong lúc một job dài đang chạy, làm hỏng lô của nó.
- Build lại image để rollback thay vì deploy lại tag trước đó.
