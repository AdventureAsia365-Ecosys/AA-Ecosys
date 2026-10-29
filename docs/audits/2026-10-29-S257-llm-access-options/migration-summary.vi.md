# Tóm tắt phương án tài khoản AWS và AI (29/10/2026)

**Vấn đề:** AI bị chặn vì *đơn vị thanh toán hộ* (đại lý), không phải vì *dữ liệu nằm ở đâu*. TrueIDC (đại lý của tài khoản hạ tầng acc2) không có quyền bán Claude; tài khoản AI acc3 rời eCloudvalley hôm nay nên bị AWS khoá toàn bộ AI. Hiện chỉ có môi trường Dev, chưa có khách thật.
**Batch có dễ hơn khi gọi API trực tiếp không? Đúng.** Gọi thẳng Anthropic/OpenAI: một lệnh gửi cả lô, giảm 50 % giá, không cần AWS cấp quyền riêng. Trên AWS Bedrock, batch cần cấu hình phức tạp và AWS chưa duyệt sau ~40 ngày chờ.

**1. D: Gọi thẳng Anthropic + OpenAI cho AI, giữ nguyên AWS cho hệ thống** (làm ngay)
- Nghĩa là: trả tiền AI bằng thẻ công ty trực tiếp cho hãng AI, không qua đại lý AWS.
- Thời gian ~1 tuần; công sức 4–6 ngày kỹ sư; không gián đoạn dịch vụ.
- Chi phí: ~250 USD/tháng theo giá niêm yết (bằng giá Bedrock), batch giảm 50 %; hạ tầng không đổi.
- Rủi ro: hoá đơn USD nước ngoài, không có hoá đơn VAT Việt Nam (cần hỏi kế toán); tài khoản mới bị trần 500 USD/tháng ban đầu, phải xin nâng; thêm một bên xử lý dữ liệu.

**2. C2: Lập "tổ chức AWS" riêng của công ty, đưa acc2 + acc3 vào, đại lý chỉ xuất hoá đơn** (đề xuất lâu dài)
- Nghĩa là: công ty tự nắm quyền quản trị; đại lý có quyền bán Claude (Renova hoặc eCloudvalley VN) chỉ thu tiền qua tính năng chuyển thanh toán (Billing Transfer), không chạm vào hệ thống.
- Thời gian 4–10 tuần (thương lượng, chuyển đổi bắt đầu ngày 1 của tháng); công sức 4–8 ngày; không di chuyển dữ liệu, không gián đoạn.
- Chi phí: AWS giá niêm yết + phí đại lý; tài khoản quản lý mới miễn phí.
- Rủi ro: rời TrueIDC có thể làm AWS khoá AI trên acc2 như acc3 (ảnh hưởng tìm kiếm ngữ nghĩa, lọc dữ liệu CRM); đại lý phải hỗ trợ Billing Transfer (mặc định chưa bật); có thể có 1 tháng tự trả AWS bằng thẻ trước khi đại lý nhận.

**3. E1: Đưa acc2 vào tổ chức AWS của eCloudvalley** (ý của trưởng nhóm kỹ thuật)
- Nghĩa là: đổi đại lý từ TrueIDC sang eCloudvalley, eCloudvalley quản lý tài khoản như TrueIDC hiện nay.
- Thời gian 2–6 tuần; công sức 3–5 ngày; không di chuyển dữ liệu, không gián đoạn.
- Chi phí: AWS giá niêm yết + phí eCloudvalley.
- Rủi ro: lặp lại đúng sự cố acc3 hôm nay, lần này trên tài khoản chứa toàn bộ hệ thống; eCloudvalley có quyền quản trị và áp luật lên tài khoản; cũng có thể bị khoá AI khi rời TrueIDC. Chỉ chấp nhận nếu có điều khoản rút lui bằng văn bản.

**4. B: Giữ acc2 ở TrueIDC, chỉ đưa acc3 về một đại lý có quyền bán Claude**
- Thời gian 1–4 tuần (chờ AWS gỡ khoá acc3); công sức 0–1 ngày; không gián đoạn; chi phí: phí đại lý trên phần AI.
- Rủi ro: vẫn hai đại lý, hai hoá đơn; TrueIDC vẫn có quyền vào acc2; phụ thuộc AWS gỡ khoá, không biết khi nào.

**5. A: Chuyển toàn bộ hệ thống từ acc2 sang acc3, ký một đại lý cho acc3** (không khuyến nghị)
- Nghĩa là: dựng lại ~785 thành phần hạ tầng và chuyển cơ sở dữ liệu, file, tài khoản đăng nhập sang tài khoản khác.
- Thời gian 7–10 tuần; công sức 33–43 ngày kỹ sư (gần như dừng phát triển tính năng); gián đoạn 4–8 giờ + ít nhất 7 lần ngắt ngắn; mọi người dùng phải đặt lại mật khẩu/MFA.
- Chi phí: chạy song song hai hệ thống +150–200 USD, cộng phí đại lý như C2.
- Rủi ro: chuyển xong acc3 vẫn có thể bị khoá AI (vẫn phải qua bước đổi đại lý như C2); dễ sót cấu hình làm lỗi ngầm; lỗ hổng bảo mật tạm thời trong lúc chuyển.

**Khuyến nghị kỹ thuật:** làm **D ngay** để AI và batch chạy lại trong tuần này; song song hỏi Renova và eCloudvalley VN bằng văn bản (quyền bán Claude cho tài khoản Việt Nam, có hỗ trợ Billing Transfer không, phí, cam kết tối thiểu, điều khoản rút lui, hoá đơn VAT) rồi đi **C2**; chỉ chọn E1 nếu không đại lý nào hỗ trợ Billing Transfer. **Không làm A** — tốn gấp ~6 lần mà không giải quyết thêm gì so với C2.
