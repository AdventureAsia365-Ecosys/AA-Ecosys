# Người liên quan và giọng văn

| Người | Vai trò | Kênh | Giọng |
|---|---|---|---|
| Chị Thư — Ms. Thu (Jira `@thule`) | Chủ doanh nghiệp: yêu cầu nghiệp vụ, quyết định kinh doanh / pháp lý, quyền duyệt; admin org | Jira PR/KAN/CON (kênh chính, kể cả link trang làm cho chị xem); Zalo cho câu hỏi nhanh; DOCX cho tài liệu chính thức | Xem dưới |
| Đại lý AWS / reseller (TrueIDC, eCloudvalley, Sunny Cloud…) | Payer/organization AWS, billing, bán lại model Bedrock | Zalo / nhóm chat | Xem "Viết cho đại lý / nhà cung cấp" |
| Leigh | Commercial lead | Email / báo cáo | Tiếng Anh, số liệu trước, không rào đón |
| Trang | Nội dung nội bộ | | Tiếng Việt, theo quy trình |

## Viết cho chị Thư

- **Jira:** theo `aa-jira-update` (mẫu mở đầu, mention, bảng số liệu) — nháp → Nghiệp duyệt → đăng; nói tính năng đã
  làm và chỗ xem; không "như đã hứa", không rải "ạ"; không mã nội bộ (Linear, tên rule).
- **Zalo:** mở "Dạ chị,", xưng em/chị, text thuần (không in đậm/markdown), ít "ạ"/"nhé". Tình huống + ví dụ thật → lý
  do (luật) → phương án → đề xuất → "Chị chốt giúp em để em …". Tin chỉ báo tin (không hỏi quyết định) thì kết bằng
  lời mời góp ý, không "Em cảm ơn chị!".
- **Trang hỏi ý kiến:** như một phiếu khảo sát — chỉ câu hỏi và lựa chọn, nhóm theo mảng (giá, pháp lý, dịch vụ trả phí…),
  mỗi câu gắn với phần spec nó phục vụ; văn viết trung tính (không dạ/ạ/nha), có thể gắn nhãn "Khuyến nghị"; không
  nhắc Nghiệp, không mã nội bộ.
- **Việc pháp lý / kinh doanh:** đưa đề xuất bình tĩnh (phương án + khuyến nghị) để chị quyết; không tạo áp lực hạn
  chót, không mặc định cần luật sư. Phần kỹ thuật của việc đó vẫn làm như thường.
  Chọn nhà cung cấp / đại lý: đưa **đủ mọi phương án** cạnh nhau, văn trung tính (thời gian, chi phí, phí, cọc, ràng
  buộc, có cần hợp đồng mới không) để chị chọn. Hợp đồng TrueIDC đã ký: tech chỉ tư vấn phương án kỹ thuật tốt nhất,
  không đẩy ký thêm, không làm tăng chi phí. Đã đưa khuyến nghị thì giữ, không sửa tới sửa lui.
- **Guide cho chị Thư và guide theo vai trò:** song ngữ EN–VI, hai bản đủ ý như nhau.
- **Tài liệu chính thức:** trang trọng, tiêu đề rõ, không viết tắt.

## Viết cho đại lý / nhà cung cấp

Tin chat (Zalo, nhóm với đại lý), Nghiệp đứng tên:

- **Khung:** Tình hình (2–3 dòng, lời thường) → Nhu cầu của bên mình → câu hỏi đánh số; cần gọn thì đánh dấu nhóm ưu tiên.
- **Lời:** chat đời thường, câu ngắn, "mình / bên mình / bên bạn". Chủ doanh nghiệp gọi là "sếp mình", không tên, không
  chức danh. Text thuần, dòng đánh số được. Đóng "Mình cảm ơn.". TrueIDC: mở "Chào @Jade - Hoài,", kèm đường bấm cụ thể.
- **Chỉ dán thông tin công khai được:** link artifact claude.ai chỉ người trong tổ chức mở được và chứa account/org ID,
  chi phí, đề xuất nội bộ (ví dụ mua trực tiếp) → tóm lại bằng lời. Account ID, mã Linear, số chi phí nội bộ cũng vậy.

Checklist câu hỏi chuẩn cho đại lý AWS / Bedrock (mỗi ý một câu, điền số của lần hỏi):

1. Bán lại model của hãng nào trên Bedrock ở region của mình; xác nhận bằng văn bản.
2. Có SCP / Private Marketplace nào chặn model hay dịch vụ.
3. Giữ organization riêng (Billing Transfer) hay phải vào org của họ; quyền root/IAM.
4. Chuyển 2–3 tài khoản: quy trình, thời gian, gián đoạn.
5. Phí tính trên gì (gồm Bedrock/Marketplace?), phí tối thiểu, cọc, cam kết.
6. Hoá đơn: tiền tệ, tỷ giá, VAT, hạn thanh toán.
7. Đề cử credit AWS; credit có dùng cho model bên thứ ba không.
8. "Miễn phí dịch vụ" gồm gì; có mở case AWS thay mình không, thời gian phản hồi.
9. Rời đi: báo trước, phí; tài khoản và quyền truy cập model còn nguyên không.
10. Tự xem chi phí/budget được không; dịch vụ AWS nào họ không hỗ trợ.

Bộ câu hỏi đầy đủ + nghiên cứu đối tác: `docs/audits/2026-10-29-S257-llm-access-options/angle1-aws-partners-vn.md` §5.
Mẫu đã gửi (Sunny Cloud, S260): bản nháp lưu trong `docs/audits/2026-10-30-S260-session-close/`. Comment Jira:
`aa-jira-update`. Dịch vụ AWS trả phí mới: `aa-lessons/lessons.md` mục Cách làm việc.

## Review tiếng Anh (khi Nghiệp viết English)

Format 3 tầng:

```
❌ Original  : "We have done the deploy and now the system was working."
✅ Suggested : "The deployment is complete and the system is now running."
💡 Why       : noun phrase thay "have done"; thống nhất thì; tránh dịch sát tiếng Việt
```

Lỗi hay gặp: thiếu mạo từ ("deploy to **the** ECS cluster"), trộn thì, dịch sát ("We have done the fix" → "The fix is in place"), giới từ ("depend **on**"), lạm dụng bị động.

Khi giải thích thuật ngữ bằng tiếng Việt: kèm nghĩa, một câu ví dụ tiếng Anh trong ngữ cảnh AA, và khi nào dùng.
