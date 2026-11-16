---
id: OPS-00-delivery-yyyy-ww
title: Chỉ số giao hàng <YYYY>-W<ww>
description: <Một câu - các chỉ số DORA và luồng của tuần so với baseline, và một thay đổi chúng gợi ý.>
type: report
status: draft
owner: replace-me
audience: [engineer, cto, pm, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-16
related: []
lang: vi
translation_of: docs/templates/delivery-metrics-report.md
---

# Chỉ số giao hàng <YYYY>-W<ww>

<!-- Playbook dự án mới, pha 7 Vận hành (trang chỉ số). Một script tính từ git, các lượt deploy, bản ghi sự cố và công
cụ theo dõi việc; không ai gõ tay số liệu. So với baseline lấy trước ngày 60. Một chỉ số là một câu hỏi, không phải mục
tiêu: không bao giờ thưởng theo một con số. Xoá ghi chú này. -->

## 1. DORA

<!-- Mỗi app và mỗi môi trường một bảng (`dev` tới khi go-live, sau đó thêm `prod`): không bao giờ trộn môi trường trong
một con số. Ghi n (số sự kiện đứng sau một con số) cạnh mỗi giá trị; n dưới mức tối thiểu đã thống nhất thì ghi "quá
ít sự kiện" và không đọc xu hướng. Định nghĩa: mục 4. -->

Môi trường: <dev / prod>

| Chỉ số | Định nghĩa | Tuần này (n) | Trung vị 4 tuần | Baseline | Xu hướng |
|---|---|---|---|---|---|
| Deployment frequency | Số lần deploy xanh mỗi tuần (job deploy và post-deploy verify đều đạt) | <...> (<n>) | <...> | <...> | <tăng / giảm / đi ngang> |
| Change lead time | Từ lúc mở PR tới post-deploy verify của lần deploy xanh đầu tiên chứa nó, trung vị | <...> (<n>) | | | |
| Change fail rate | Số lần deploy hỏng / số lần deploy đã lên môi trường | <...> (<n>) | | | |
| Failed deployment recovery time | Từ lần deploy hỏng tới lần deploy xanh sửa nó, trung vị | <...> (<n>) | | | |
| Deployment rework rate | Số lần deploy rollback, revert và hotfix / số lần deploy đã lên môi trường | <...> (<n>) | | | |

Các khúc lead time (trung vị số giờ, để thấy bước chậm):

| Mở tới CI xanh đầu tiên | CI xanh tới vào hàng merge | Hàng merge tới đã merge | Đã merge tới đã deploy | Đã deploy tới đã verify |
|---|---|---|---|---|
| <...> | <...> | <...> | <...> | <...> |

## 2. Luồng

| Chỉ số | Tuần này | Trung vị 4 tuần |
|---|---|---|
| Work in progress (số issue In Progress) | <...> | <...> |
| Throughput (số issue Done) | <...> | |
| Work item age, issue In Progress cũ nhất | <ngày> | |
| Cycle time (In Progress tới Done), trung vị | <ngày> | |

## 3. Đọc số

- <Cái gì đã đổi và nguyên nhân có khả năng.>
- <Một thay đổi để thử tuần tới, hoặc "không có".>

## 4. Định nghĩa

- **Deploy**: một lượt chạy workflow deploy của app trên nhánh mặc định mà job deploy đã chạy. Các lượt chạy cùng một
  commit chồng nhau (các service của một lần push) là một lần deploy. Xanh = các job deploy và post-deploy verify đều
  đạt. Một lượt chạy sau của chính commit đang chạy là deploy lại: không tính, nhưng có thể là một lần khôi phục.
- **Thay đổi**: một pull request được merge vào nhánh mặc định. Pull request của bot và pull request chỉ đổi tài liệu,
  không gây deploy, không tính vào lead time và được đếm riêng.
- **Deploy hỏng**: post-deploy verify đỏ, một job deploy lỗi, bị rollback (một lần deploy sau đưa lên commit cũ hơn),
  pull request của nó bị revert trong 48 giờ, hoặc một pull request `fix` nhắc tới pull request của nó được merge
  trong 48 giờ. Từ prod trở đi, một sự cố gắn với lần deploy cũng tính.
- **Khôi phục**: từ lần deploy hỏng tới lần deploy xanh sửa nó (lần deploy xanh kế tiếp, lần rollback, hoặc lần deploy
  mang bản revert hay hotfix).
- **Làm lại**: một lần deploy mà chính nó là sửa chữa ngoài kế hoạch (một rollback, hoặc một lần mang bản revert hay
  hotfix).
- **Môi trường**: là một chiều của mọi con số ngay từ đầu; không bao giờ cộng số của hai môi trường.

## 5. Nguồn

<Tên và phiên bản script, các file sự kiện thô nó đọc, phiên bản định nghĩa, thời điểm nó chạy. Giữ sự kiện thô
(lượt chạy workflow, job, pull request, deployment) lâu hơn nhà cung cấp CI giữ, để khi đổi định nghĩa thì tính lại
được.>
