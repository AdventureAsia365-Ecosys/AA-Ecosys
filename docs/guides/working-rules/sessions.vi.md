---
id: GUIDE-15-sessions
title: Quy tắc làm việc - phiên làm việc
description: Các quy tắc chuẩn để chạy một phiên làm việc của nhóm agent - đọc và kiểm gì khi bắt đầu, công việc chạy thế nào trong phiên, và thứ tự cố định khi chốt phiên.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15, GUIDE-15-planning, GUIDE-15-stakeholders, CAT-01, GUIDE-02, AA-1104]
lang: vi
translation_of: docs/guides/working-rules/sessions.md
---

# Quy tắc làm việc - phiên làm việc

Một phiên là một lượt làm việc của nhóm agent: phiên điều phối (phiên Claude Code chính) và các lane nó mở. Trang này
giữ **quy tắc**. Quy trình từng bước, kèm lệnh, là skill phiên
[`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) mà agent nạp. Nếu hai bên lệch nhau, áp dụng quy tắc
chặt hơn cho tới khi một PR sửa cả hai.

Các quy tắc W1 đến W7 của [sổ tay kỹ thuật](../../engineering-handbook.vi.md#24-hai-luật-làm-việc-tự-quyết-không-hỏi-không-tự-đặt-cổng-chặn)
áp dụng trong mọi phiên; trang này không nhắc lại chúng.

## Nguồn trạng thái

| Quy tắc | Vì sao |
|---|---|
| Đọc trạng thái đã ghi trước: memory của phiên, log phiên gần nhất, [backlog sống](../../backlog/README.md) và master plan | Phiên sau bắt đầu từ chỗ phiên trước dừng, không từ trí nhớ |
| Khi các nguồn lệch nhau, repo thắng trang Notion chuẩn, trang đó thắng memory, memory thắng skill. Báo chỗ lệch; không bao giờ lặng lẽ chọn một bên | Một thứ tự chung cho mọi người đọc ([sổ tay §2.2](../../engineering-handbook.vi.md#22-nguồn-sự-thật-cho-trạng-thái-quy-trình)) |
| Kiểm trạng thái thật trước khi làm: danh tính của AWS profile, các service ECS, các bảng job, AI gateway, các lượt chạy guard theo lịch | Một trạng thái có thể đổi thì được kiểm live, hoặc ghi là "chưa kiểm" (W5) |
| Ghi giờ hết hạn của phiên MFA và xử lý trước giờ đó | Một chuỗi merge dài chết giữa chừng khi phiên hết hạn |

## Bắt đầu phiên

1. **Đề xuất danh sách issue từ master plan.** Issue đã xếp cho phiên này trước, rồi slot kế tiếp, rồi theo thứ tự
   milestone. Slot là thứ tự, không phải cổng chặn (W2): kéo một việc lên sớm khi điều kiện của nó đã đủ. Nói rõ vì sao
   bỏ qua hay kéo lên sớm việc nào.
2. **Cỡ phiên.** 3 đến 5 issue cho phiên thường; 8 đến 10 khi chạy lane song song.
3. **Hội tụ trước.** Liệt kê mọi issue In Progress. Đóng việc đã đạt Done-when, làm xong việc gần xong, và ghi rõ cái
   gì chặn phần còn lại. Cả nhóm giữ tối đa 8 issue In Progress (trần do tech lead đặt); vượt trần thì phiên hội tụ
   trước khi bắt đầu việc mới.
4. **Rà soát định kỳ.** Khi đến hạn, rà soát truy vấn hằng tuần, rà soát dung lượng và chi phí hằng tháng, rà soát quyền
   hằng quý được đưa vào danh sách của phiên (data standards C4.3, C8, DM-8.10).
5. **Cập nhật master plan trước khi mở lane.** Khi tech lead chốt danh sách, tracker hiện các issue của phiên này, rồi
   mới mở lane.

## Trong phiên

| Quy tắc | Chi tiết |
|---|---|
| Giữ một checklist sống | Một file cho mỗi phiên, cập nhật sau mỗi bước; đó là nguồn của log phiên |
| Ghi bài học ngay khi tìm ra nguyên nhân gốc | Một dòng trong file bài học chờ ngay lúc tìm ra nguyên nhân, chuyển vào sổ bài học khi chốt phiên ([bài học](../../../skill/aa-lessons/SKILL.md)) |
| Giải thích mỗi issue khi bắt đầu | Ba đến sáu dòng lời thường: vấn đề, sẽ làm gì, ai làm, kiểm thế nào |
| Phiên điều phối giữ quyền thao tác live | Chỉ phiên điều phối push, mở và merge PR, chạy workflow, Terraform apply, DB Migrate và ECS exec. Một lane viết code, test và runbook trong worktree và thư mục scratch riêng của nó và trả bước live về (có hook chặn) |
| Câu hỏi kèm sẵn đề xuất trả lời | Bối cảnh bằng lời thường cộng câu trả lời mà agent sẽ chọn; nhiều câu hỏi gom thành một trang quyết định. Câu hỏi mở không phải lý do để dừng (W1) |
| Dev không chờ | Dev chỉ có dữ liệu thử và không có traffic thật: tạo bằng chứng ngay thay vì chờ một khoảng thời gian |
| Lưu thứ phiên tạo ra | Audit, báo cáo và trang quyết định vào `docs/audits/<date>-S<nnn>-<slug>/` và root PR của phiên |
| Làm xong rồi mới chốt | Việc làm được (issue In Progress, phát hiện phụ, bước kiểm live) được làm trong phiên, không liệt kê lại thành lời nhắc |
| Không bao giờ bật tắt hạ tầng | Agent không khởi động, dừng hay đổi quy mô ECS, RDS hay NAT. Service đang tắt thì báo tech lead |

## Chốt phiên

Thứ tự cố định: **chốt việc, kiểm trạng thái thật, bài học, bài Jira đã duyệt, rồi mới ghi log**. Log viết sau cùng để
mọi con số trong đó đều đã được kiểm, không phải nhớ lại.

1. **Chốt việc trên Linear.** Issue đã verify sang Done kèm comment bằng chứng; issue chưa xong giữ In Progress kèm phần
   còn lại và cái gì chặn. Rồi rà mọi issue vừa sang Done xem có bằng chứng không.
2. **Chụp trạng thái thật** trước khi viết bất kỳ log nào: task definition và phiên bản image của từng service, các
   endpoint health, migration mới nhất của mỗi chủ schema, các bảng job và wave đang mở, head và PR đang mở của từng
   repo, và những gì được cố ý để bật cho phiên sau. Chỉ tên và số, không bao giờ account ID hay giá trị secret.
3. **Bài học** chuyển từ file chờ vào sổ bài học.
4. **Nháp Jira** đưa tech lead xem một lần, nguyên văn, được duyệt rồi mới đăng
   ([quy tắc giao tiếp](stakeholder-communication.vi.md)).
5. **Rồi mới viết**, từ bản chụp trạng thái và kết quả Jira: log phiên, block memory (chỉ thêm lên đầu, không bao giờ
   xoá block cũ), backlog sống và master plan.
6. **Đóng gói các skill đã đổi**, xuất và lưu trữ các issue Linear đã đóng, và merge root PR của phiên khi docs lint xanh.
7. **Để mọi repo sạch** trên nhánh mặc định, và để môi trường tiếp tục chạy.
8. **Tóm tắt ba dòng:** đã làm, còn lại (và cái gì chặn), phiên sau bắt đầu từ đâu.

## Liên quan

- [Quy tắc kế hoạch và issue](planning-and-issues.vi.md) và [quy tắc giao tiếp với người liên quan](stakeholder-communication.vi.md)
- [Mục lục chỉ dẫn cho agent](../../agents.md)
- [Sổ tay kỹ thuật, mô hình làm việc](../../engineering-handbook.vi.md#2-mô-hình-làm-việc)
