---
id: GUIDE-14-principles
title: Nguyên tắc và dung sai của playbook
description: Bảy nguyên tắc của bộ kit dự án mới và bảng dung sai cho agent biết việc gì được làm mà không cần hỏi.
type: explanation
status: draft
owner: nghiep
audience: [owner, engineer, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, CAT-01, docs/research/new-project-playbook/README.md]
lang: vi
translation_of: docs/playbook/principles.md
---

# Nguyên tắc và dung sai của playbook

## Bảy nguyên tắc

1. **Bản áp dụng đặt trên chuẩn.** Mỗi trang của bộ kit nêu chuẩn nó theo và nói nó giữ hay bỏ phần nào. Không tự đặt
   ra phương pháp mới khi đã có một phương pháp quen thuộc.
2. **Mỗi dữ kiện một nhà.** Mẫu chỉ nằm một chỗ, trong [`docs/templates/`](../templates/README.vi.md). Các trang pha trỏ
   tới chúng; repo mẫu chép chúng dưới một guard so từng byte, nên bản chép không bao giờ lệch khỏi bản gốc.
3. **Sổ tay trước.** Một luật đổi ở trang bộ kit trước, rồi mới tới skill và các bản chép. Trang học liệu dựng từ chính
   các trang này.
4. **Lõi chung cộng lớp phủ.** Bộ kit không mang tên dự án nào. Mỗi dự án giữ một lớp phủ (tài khoản, service, người,
   công cụ theo dõi việc) trỏ về các trang chung; lớp phủ của AA là [bản áp dụng AA](aa-profile.vi.md).
5. **Dung sai, không phải xin duyệt.** Agent làm trong giới hạn đã thoả thuận và chỉ báo lên khi dự báo cho thấy một
   giới hạn sẽ bị vượt (PRINCE2 "manage by exception").
6. **Công tắc theo giai đoạn.** Các biện pháp chỉ dành cho prod (error budget, trực sự cố, code owner được ép, role agent
   quyền tối thiểu) được viết sẵn từ giờ và bật ở cổng G7, không sớm hơn.
7. **Cắt tỉa.** Mỗi trang có chủ sở hữu và chu kỳ rà soát. Luật bị thay thế thì xoá, không giữ cạnh luật mới.

## Dung sai

Bản điều lệ đặt các giới hạn cho từng dự án. Trong giới hạn đó agent làm mà không hỏi và báo lại việc đã làm. Khi dự báo
cho thấy một giới hạn sẽ bị vượt, agent dừng phần đó và mang một trang quyết định tới người chịu trách nhiệm cuối: bối
cảnh bằng lời thường, các phương án, và một câu trả lời đề xuất.

| Dung sai | Giới hạn cái gì | Mặc định của bộ kit | Báo lên khi |
|---|---|---|---|
| Thời gian | Lượng việc mỗi phiên và đang làm dở | 3 tới 5 issue mỗi phiên; tối đa 8 issue In Progress; mỗi issue một appetite | Một issue sắp vượt appetite của nó |
| Chi phí | Tiền chi ra | Báo giá chi phí hằng tháng, và một lời đồng ý riêng cho từng mục trả phí mới; lượt chạy lô tốn tiền: thử khoảng 3, rồi tối đa khoảng 50 | Một mục trả phí mới, hoặc một lượt chạy vượt trần |
| Phạm vi | Một issue bàn giao gì | Done-when đóng băng khi issue sang In Progress; phạm vi mới thành một issue mới có liên kết | Không thể đạt Done-when như đã viết |
| Chất lượng | "Xong" nghĩa là gì | Mọi check đều xanh, không chỉ các check bắt buộc; Definition of Done đã kiểm live | Một check không thể làm xanh trong phạm vi issue |
| Rủi ro | Các thay đổi có thể gây hại | Lớp rủi ro (xác thực hay phân quyền, migration hay schema, CI hay secret, xoá dữ liệu) có một agent review độc lập; bước phá huỷ cần tech lead đồng ý sau một lần chạy thử (dry run) | Mọi bước phá huỷ; mọi rủi ro mà review đánh giá cao |
| Lợi ích | Giá trị kinh doanh | Câu hỏi kinh doanh tới chủ doanh nghiệp dưới dạng các phương án kèm khuyến nghị | Một lựa chọn làm thay đổi thứ người dùng nhận được hoặc số tiền họ trả |

### Những gì không phải là lý do để dừng

- Một câu hỏi mở đã có câu trả lời hợp lý: viết câu trả lời đề xuất, làm theo nó, báo lại.
- Một slot kế hoạch hay một ngày chỉ là thứ tự: kéo việc lên sớm khi điều kiện kỹ thuật đã đủ.
- Một kiểu "nên hỏi ai đó cho chắc": những phép kiểm agent tự chạy được (một lệnh gọi live, một lần đăng nhập thử, một
  lần chạy thử) thì cứ chạy.

Chặn thật thì ít: một bước credential hay MFA chỉ người làm được, tiền, một quyết định chỉ người chịu trách nhiệm cuối
đưa ra được, và một bước không đảo ngược được.

## Hai loại cấu hình

| Loại | Ví dụ | Nằm ở đâu |
|---|---|---|
| Cấu hình deploy | Endpoint, tham chiếu secret, công tắc theo môi trường | Môi trường (Twelve-Factor factor III) |
| Giá trị chính sách | Ngưỡng, giới hạn, trần, ngân sách, thời hạn lưu, giá | Một registry settings sửa được trên trang admin có lịch sử, gieo sẵn giá trị mặc định đã duyệt ([mẫu settings](../templates/settings-entry.vi.md)) |

Hai luật không mâu thuẫn khi cấu hình được tách như vậy: người vận hành đổi một giá trị chính sách trên trang admin, không
cần deploy.

## Cổng ngắn và trung thực

- Một cổng là một checklist tối đa khoảng mười câu hỏi, chấm đỏ, vàng hoặc xanh.
- Vàng cần một việc tiếp theo có người phụ trách và ngày trong công cụ theo dõi việc; đỏ thì dừng pha.
- Người chịu trách nhiệm cuối ký cổng; agent chuẩn bị bằng chứng cho từng dòng.
