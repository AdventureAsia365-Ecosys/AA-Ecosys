---
id: GUIDE-15-planning
title: Quy tắc làm việc - kế hoạch và issue
description: Các quy tắc chuẩn về thứ tự backlog, issue Linear (tạo, Definition of Ready, hạn mức, cập nhật) và khi nào một issue là Done.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15, GUIDE-15-sessions, GUIDE-15-stakeholders, CAT-01, AA-1104]
lang: vi
translation_of: docs/guides/working-rules/planning-and-issues.md
---

# Quy tắc làm việc - kế hoạch và issue

Trang này giữ **quy tắc** về kế hoạch và issue Linear. Quy trình, kèm lệnh và mẫu, là các skill
[`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md) (issue) và
[`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) (merge, deploy, Done). Nếu một skill và trang này lệch
nhau, áp dụng quy tắc chặt hơn cho tới khi một PR sửa cả hai.

## Thứ tự công việc

- **Một hàng đợi có thứ tự.** [Backlog sống](../../backlog/README.md) giữ thứ tự và tracker master plan giữ slot của
  từng phiên. Linear giữ trạng thái của từng issue. Kanban, không chia sprint
  ([sổ tay §2.1](../../engineering-handbook.vi.md#21-mô-hình)).
- **Slot là thứ tự, không phải cổng chặn.** Kéo một việc sau lên sớm khi điều kiện kỹ thuật của nó đã đủ (W2). Chỉ phụ
  thuộc thật mới chặn: một migration phải áp trước, một bảng job đang bận hay một wave đang mở, một phiên MFA, tiền,
  hoặc một quyết định chỉ tech lead hay chủ doanh nghiệp đưa ra được.
- **Việc đang làm có trần.** Tối đa 8 issue In Progress cho cả nhóm. Một issue In Progress hoặc hội tụ (Done kèm bằng
  chứng, làm xong, hoặc trả về backlog kèm lý do) hoặc ghi rõ cái gì chặn nó.

## Tạo issue

| Quy tắc | Chi tiết |
|---|---|
| Hỏi tech lead trước | Đưa sẵn tiêu đề, vấn đề và phạm vi đề xuất bằng lời thường, gom nhiều issue một lần, để chỉ cần một câu đồng ý |
| Kiểm trùng | Tìm bằng hai, ba từ khoá chính, gồm cả backlog. Có issue gần giống thì mở rộng hoặc comment vào đó, không tạo bản sao |
| Mỗi issue một project | Mọi issue thuộc đúng một project; mỗi project giữ dưới khoảng 100 issue đang mở |
| Một issue là một lát việc giao được | Khoảng một PR hoặc một nhóm PR nhỏ. Chi tiết nằm trong plan và checklist của phiên, không tách thêm issue |
| Tiếng Anh | Tiêu đề, mô tả và comment viết tiếng Anh; tiêu đề có dạng `[Area] việc cần làm - chi tiết chính` và không có mã Jira |
| Ưu tiên theo tác động | Urgent: production hỏng hoặc mất dữ liệu. High: chặn việc kế tiếp hoặc rủi ro bảo mật. Medium: cải tiến có ích. Low: để sau |

Thân issue theo mẫu Problem, Scope (kèm out of scope), Done when, Related. Các dòng Done-when kiểm được trên môi trường
thật (một lệnh curl, một query, một trang, một lượt chạy workflow), không bao giờ là "code đã merge".

## Definition of Ready

Một issue chỉ được giao cho lane, subagent hay Kiro khi đã Ready: mục tiêu, path (fix, small, feature, risky), appetite
tính bằng phiên (kèm trần USD nếu có chạy trả phí), phạm vi, 3 đến 6 dòng Done-when, lệnh verify, lớp rủi ro, phụ thuộc,
ảnh hưởng tới tài liệu và chi phí. Checklist đầy đủ là [mẫu Definition of Ready](../../templates/definition-of-ready.md).
Nếu việc vượt appetite, dừng lại và cắt bớt hoặc tách ra; không làm tiếp.

## Giữ gói miễn phí

Linear chạy gói miễn phí, có trần số issue đang mở của cả workspace, và không nâng gói.

- Issue đã đóng được xuất vào `docs/linear-export/` trong root PR của phiên, rồi lưu trữ qua API.
- Không bao giờ xoá issue để lấy chỗ: issue bị xoá và các comment bằng chứng của nó mất hẳn sau 30 ngày.
- Không bao giờ đặt một issue kế hoạch làm issue con của một issue sắp đóng: lưu trữ issue cha là lưu trữ luôn các issue
  con đang mở. Dùng liên kết "related" thay thế.

## Cập nhật issue

- Trước khi ghi vào một issue, đọc nó và kiểm tiêu đề khớp với điều sắp ghi. Không tin số issue nhớ từ đầu phiên.
- Phát hiện mới là một comment có ngày và bằng chứng, không lặng lẽ sửa mô tả.
- Việc ngoài phạm vi thành issue mới (hỏi trước) có liên kết related, không bao giờ nhồi vào issue hiện tại.
- Khi thứ tự là bắt buộc (một migration trước code đọc cột của nó), liên kết các issue bằng blocks và blocked by.

## Khi nào một issue là Done

- **Done nghĩa là đã verify live.** Đã merge và CI xanh là chưa đủ: thay đổi đã deploy, rollout đã hoàn tất, và endpoint
  hay trang live cho thấy kết quả. Comment đóng ghi PR, phiên bản đã deploy, bước kiểm live và kết quả, tài liệu đã sửa
  và chi phí.
- **Các dòng Done-when được đóng băng** khi issue sang In Progress. Phạm vi mới phát hiện giữa chừng thành issue mới.
  Được sửa câu chữ cho rõ; không được đổi nghĩa.
- **Done với phạm vi.** Một issue được đóng khi chỉ giao một phần phạm vi nếu phần đã giao được verify live và mọi phần
  còn lại có issue follow-up riêng hoặc một trigger đã ghi (một điều kiện hay một ngày). Nếu không, issue vẫn mở.
- **Commit và PR chỉ tham chiếu, không đóng.** Thân có một dòng `Refs` với các mã issue. Không mã issue trong tiêu đề,
  không từ khoá đóng issue (Linear sẽ đóng issue khi merge). Sau mỗi lần merge, deploy hay migration của một issue còn
  mở, kiểm Linear có tự đóng nó không và mở lại nếu có.
- Thiếu bằng chứng thì issue ở In Review và ghi rõ còn thiếu gì.

## Liên quan

- [Quy tắc phiên làm việc](sessions.vi.md) và [quy tắc giao tiếp với người liên quan](stakeholder-communication.vi.md)
- [Sổ tay kỹ thuật, Definition of Ready và Done](../../engineering-handbook.vi.md#64-definition-of-ready-và-done)
