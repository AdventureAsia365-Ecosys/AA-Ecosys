---
id: GUIDE-15-stakeholders
title: Quy tắc làm việc - giao tiếp với người liên quan
description: Các quy tắc chuẩn khi viết cho người ngoài nhóm kỹ thuật - bài báo tiến độ cho chủ doanh nghiệp, yêu cầu quyết định gửi tech lead, câu hỏi kinh doanh và tin nhắn cho nhà cung cấp.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15, GUIDE-15-sessions, GUIDE-15-planning, CAT-01, GUIDE-04, AA-1104]
lang: vi
translation_of: docs/guides/working-rules/stakeholder-communication.md
---

# Quy tắc làm việc - giao tiếp với người liên quan

Một tin nhắn gửi người ngoài nhóm kỹ thuật đi thẳng tới người ra quyết định. Vì vậy mọi quy tắc dưới đây đặt một bước
duyệt trước khi gửi. Trang này giữ **quy tắc**. Quy trình, kèm định dạng, cách mention và các bước tải ảnh, là các skill
[`skill/aa-jira-update/SKILL.md`](../../../skill/aa-jira-update/SKILL.md) (Jira) và
[`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) cùng hướng dẫn giọng văn của nó (các kênh khác). Nếu một
skill và trang này lệch nhau, áp dụng quy tắc chặt hơn cho tới khi một PR sửa cả hai.

## Ai đọc gì

| Người đọc | Kênh | Họ nhận được gì |
|---|---|---|
| Chủ doanh nghiệp | Jira: mỗi app một epic, tính năng là story, một báo cáo nền tảng hằng tuần | Tiến độ sản phẩm: cái gì đã ship và xem ở đâu |
| Chủ doanh nghiệp, khi cần quyết định | Một trang báo cáo hoặc một form câu hỏi trung tính, gắn link trong nháp Jira | Các phương án, một khuyến nghị, dữ kiện đứng sau |
| Tech lead, khi cần quyết định | Một trang quyết định có câu trả lời đề xuất cho từng câu hỏi | Bối cảnh bằng lời thường và câu trả lời mà agent sẽ chọn |
| Nhà cung cấp và đại lý bán lại | Chat, đứng tên tech lead | Tình hình, nhu cầu, các câu hỏi đánh số |

## Tiến độ cho chủ doanh nghiệp

1. **Nháp, duyệt, rồi mới đăng.** Mọi comment Jira, sửa comment và đổi trạng thái đều được soạn nháp, đưa tech lead xem
   nguyên văn, và chỉ đăng sau một câu "đăng" rõ ràng. "Chưa đăng vội, làm xong rồi đăng" nghĩa là chờ làm xong, không
   phải bỏ bước duyệt.
2. **Agent không bao giờ tạo issue Jira hay đổi trạng thái của chúng** để báo tiến độ. Một yêu cầu mới chỉ được đặt dưới
   đúng epic của app khi tech lead bảo.
3. **Chỉ báo những gì đã ship.** Không "đã ghi nhận, sẽ làm". Chỉ nói "chạy được" cho kênh đã thử live trọn vòng, có ảnh
   chụp; nếu không thì nói cái gì đã có trong hệ thống và cái gì chưa thử, vì sao.
4. **Tiếng Việt dễ hiểu, câu ngắn, đứng tên tech lead.** Không tên agent, tên bảng hay tên hàm, mã Linear hay mã quyết
   định nội bộ. Mô tả tính năng và chỗ xem nó; không "như đã hứa", không rải lời lễ phép thừa.
5. **Số liệu lấy trong phiên này**: một query, một endpoint hay bản chụp trạng thái của phiên, mỗi số kèm ngày và giờ.
6. **Chỉ tiến độ sản phẩm.** Lựa chọn hạ tầng và kiến trúc là việc của tech lead và không được đăng thành câu hỏi cho chủ
   doanh nghiệp. Chi tiết chi phí nội bộ và lỗi đã tự xử lý xong để ngoài, trừ khi tech lead muốn.
7. **Gom các bản nháp.** Mọi bản nháp của một phiên đưa xem một lần, cùng lúc, khi chốt phiên, trước khi viết log
   ([quy tắc phiên](sessions.vi.md#chốt-phiên)). Trang làm cho chủ doanh nghiệp được đưa vào bản nháp của đúng issue nó
   thuộc về, không gửi lẻ trong chat.
8. **Tài liệu để ra quyết định là một trang báo cáo** có bảng, số liệu Dev được đánh dấu là chưa ổn định, lời khuyên dài
   hạn trước (W6).

## Câu hỏi kinh doanh và pháp lý

- Trước hết hỏi xem một thay đổi trong hệ thống có bỏ được câu hỏi không. Chỉ câu hỏi thật sự cần chủ doanh nghiệp mới
  gửi tới họ: giá, phí, hợp đồng, tư vấn pháp lý.
- Viết thành một đề xuất bình tĩnh: các phương án cạnh nhau, một khuyến nghị, không áp lực hạn chót, không mặc định là
  cần luật sư. Phần kỹ thuật của việc đó vẫn tiếp tục trong lúc chờ.
- Trang câu hỏi là một form khảo sát trung tính, nhóm theo mảng, mỗi câu gắn với phần spec nó phục vụ, có lựa chọn rõ
  ràng.
- Khi chọn nhà cung cấp hay đại lý bán lại, đưa mọi phương án theo cùng tiêu chí (thời gian, chi phí, phí, cọc, cam kết,
  có cần hợp đồng mới không). Khi đã có hợp đồng ký rồi, đưa phương án kỹ thuật tốt nhất, không đẩy sang hợp đồng mới
  hay thêm chi phí. Đã đưa khuyến nghị thì giữ.

## Quyết định cần tech lead

- Không bao giờ là một câu hỏi trống: bối cảnh bằng lời thường cộng câu trả lời đề xuất. Làm theo đề xuất và báo lại để
  tech lead có thể đảo (W1); câu hỏi mở không phải lý do để dừng.
- Nhiều câu hỏi gom thành một trang quyết định, mỗi câu trả lời là một lần bấm và lời duyệt được lưu lại. Trang dùng được
  trên điện thoại, và một thao tác hàng loạt hỏi lần bấm thứ hai ngay trong trang (khung trang chặn hộp thoại xác nhận
  của trình duyệt).

## Nhà cung cấp và đại lý bán lại

- Chat đời thường, câu ngắn, câu hỏi đánh số, đứng tên tech lead. Gọi chủ doanh nghiệp là "sếp mình", không bao giờ
  bằng tên hay chức danh.
- Chỉ dán những gì được phép ra khỏi công ty: không account ID, số chi phí nội bộ, mã issue hay link tới trang nội bộ.
  Tóm tắt các trang đó bằng lời.

## Liên quan

- [Quy tắc phiên làm việc](sessions.vi.md) và [quy tắc kế hoạch và issue](planning-and-issues.vi.md)
- [Hướng dẫn cho CEO](../ceo.vi.md), điểm vào riêng của chủ doanh nghiệp
- [Mẫu release note](../../templates/release-note.md), phần nháp Jira của nó
