---
id: TPL-01-release-checklist
title: Checklist phát hành
description: Những gì một thay đổi phải qua từ lúc merge tới lúc đã kiểm live - Definition of Done thành một checklist, theo từng vùng chất lượng.
type: template
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, TPL-01-dor, skill/aa-ship/SKILL.md]
lang: vi
translation_of: docs/templates/release-checklist.md
---

# Checklist phát hành

Dạng chung của Definition of Done (playbook dự án mới, pha 6 Phát hành, cổng G6). Quy trình riêng của AA, kèm công cụ và
lệnh, là skill `skill/aa-ship/SKILL.md`. Chép danh sách vào PR hoặc issue phát hành và đánh dấu kèm bằng chứng; một dòng
chưa đánh dấu thì hoặc làm xong, hoặc ghi "không áp dụng: <vì sao>".

## Trước khi merge

- [ ] Mọi check đều xanh, không chỉ các check bắt buộc; không còn gì đang chờ.
- [ ] Một lớp rủi ro (xác thực hay phân quyền, migration hay schema, CI hay secret, xoá dữ liệu) đã có review độc lập.
- [ ] Ảnh hưởng tài liệu đã làm trong cùng PR: `CONTEXT.md`, ADR, runbook, hợp đồng, trang danh mục.
- [ ] Chi phí: một mục trả phí mới đã được báo giá và có lời đồng ý riêng; resource mới đã gắn tag.
- [ ] Thay đổi AI: đã tăng phiên bản prompt hay model; eval regression xanh; đã cập nhật dòng sổ đăng ký dùng AI.
- [ ] Tiêu đề PR đọc như một dòng changelog; thân PR nói cách rollback.

## Deploy

- [ ] Không còn job hay lượt chạy lô nào đang mở mà lần deploy sẽ làm hỏng (cổng deploy xanh).
- [ ] Migration được áp theo thứ tự qua CI: expand trước code cần nó, contract sau.
- [ ] Cờ được đặt sang trạng thái phát hành có chủ đích; cờ fail-closed được đặt tắt trước khi code vào.
- [ ] Rollout hoàn tất; mọi service của app chạy cùng một commit.

## Đã kiểm live (Done)

- [ ] `/health` trả về SHA của commit mới; `/health/ready` xanh.
- [ ] Endpoint hay trang bị đổi trả về đúng hình dạng mong đợi trên môi trường live (giữ lại lệnh và kết quả).
- [ ] UI đã kiểm ở bề rộng desktop và điện thoại, sáng và tối, không lỗi console, khi thay đổi thấy được.
- [ ] Bằng chứng đã đăng lên issue trong công cụ theo dõi việc; chỉ tới lúc này mới đóng issue bằng tay.

## Các vùng chất lượng (ISO/IEC 25010:2023), khi liên quan

| Vùng | Câu hỏi cho bản phát hành này |
|---|---|
| Functional suitability | Nó có làm đúng điều Done-when nói, và không làm gì nó không nên làm không? |
| Performance efficiency | Có query chậm, lời gọi N+1 hay payload lớn mới nào không? |
| Compatibility | Client cũ và bên dùng hợp đồng có còn chạy không? |
| Interaction capability | Chữ trên UI rõ ràng, cơ bản về bàn phím và trình đọc màn hình, bề rộng điện thoại? |
| Reliability | Retry, timeout, idempotency, alarm cho đường mới? |
| Security | Các mục ASVS mức 1 của vùng bị đụng tới đã kiểm chưa? |
| Maintainability | Sức khoẻ code và độ phủ không giảm chứ? |
| Flexibility | Ngưỡng là settings, không phải hằng số? |
| Safety | Một giá trị sai có thể gây hại cho người, tiền hay dữ liệu không, và cái gì chặn nó? |

## Báo cho kinh doanh

- [ ] Một ghi chú phát hành cho phía kinh doanh, chỉ gồm việc đã kiểm, bằng ngôn ngữ của chủ doanh nghiệp.
