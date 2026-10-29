# Dùng Claude + OpenAI ổn định: chọn đường nào, đối tác nào (S257, 29/10/2026)

**Gốc vấn đề.** Trên Bedrock, model bên thứ ba (Claude, OpenAI) là gói AWS Marketplace, tính tiền vào account trả tiền (payer). Nếu payer là reseller (AWS Solution Provider), quyền dùng model phụ thuộc reseller đó. Từ 10/2025 AWS cho reseller bán lại Bedrock, nhưng **riêng Claude, reseller phải có giấy phép bán lại của Anthropic** (chú thích trong danh sách dịch vụ SPP, cập nhật 24/09/2026). Model OpenAI không open-weight thì AWS cho bán lại mà không cần giấy riêng. Vì vậy acc2 (TrueIDC) không gọi được Claude: không tìm thấy dấu hiệu TrueIDC có giấy này. Việc TrueIDC chặn luôn OpenAI nhiều khả năng do chính sách riêng của họ (SCP/Marketplace) [chưa kiểm]. eCloudvalley có giấy Anthropic cho "Đài Loan và Đông Nam Á" (thông cáo 09/02/2026, không nêu tên Việt Nam), nên acc3 từng chạy được. Lỗi "Error 002" của acc3 lúc này là chuyện khác: nó chặn **mọi** model, kể cả Amazon Nova và Cohere, nên là khoá ở cấp account phía AWS, chỉ AWS Support gỡ được. Nhận định này dựa trên re:Post, AWS không có tài liệu chính thức về lỗi này. Một điểm cần biết: AWS **không chiết khấu** cho reseller trên Claude và OpenAI độc quyền, nên mua qua reseller không rẻ hơn giá niêm yết. Lợi ích của reseller chỉ là hoá đơn VND, hạn thanh toán và credit.

## 3 phương án, xếp theo mức thực tế
**1. Mua thẳng từ hãng: Anthropic API + OpenAI API** (không qua reseller, không cần account AWS nào).
- Làm gì: tạo tổ chức trên platform.claude.com và platform.openai.com, nạp credit bằng thẻ công ty, cất key vào Secrets Manager. OpenAI: bật lại dòng catalog `openai` (adapter `_call_openai` đã có), nhưng cần chốt bỏ chính sách "chỉ dùng Bedrock" (S235). Anthropic: viết adapter `anthropic_native` và thêm 1 migration sửa CHECK của cột `provider`.
- Ưu: Việt Nam nằm trong danh sách hỗ trợ của cả hai hãng. Anthropic có Batch giảm 50% và prompt caching. Một adapter Anthropic dùng lại được cho Claude Platform on AWS, Azure Foundry và Vertex.
- Nhược: hoá đơn nước ngoài bằng USD (Stripe), không có hoá đơn VAT Việt Nam [cách xử lý thuế chưa kiểm]. Credit trả trước hết hạn sau 1 năm. Thêm một bên xử lý dữ liệu. Liên hệ: tự đăng ký trên console; muốn trả theo hoá đơn hàng tháng thì làm việc với Anthropic Sales.
- Công sức code: OpenAI vài giờ. Anthropic khoảng 3–5 ngày dev, gồm chuyển phần batch và 5 chỗ đang gọi satellite trực tiếp. Chi phí: khoảng $250/tháng như hiện nay, vì giá niêm yết global của Anthropic bằng Bedrock global (giá Bedrock chính xác chưa đối chiếu). Dùng batch hoặc caching thì còn thấp hơn.

**2. Reseller Việt Nam có giấy Anthropic, theo hình thức Billing Transfer.**
- Làm gì: reseller trả tiền thay cho org AWS của mình. Mình vẫn giữ management account và SCP. Bên nào cũng rút được bất cứ lúc nào, hiệu lực vào cuối tháng này hoặc tháng sau.
- Ứng viên:
  - **Renova Cloud** (Premier, tự công bố là "một trong các reseller được Anthropic ủy quyền tại Việt Nam", info@renovacloud.com).
  - **eCloudvalley VN** (Premier, văn phòng HCM; phải xin xác nhận bằng văn bản là giấy phép có áp dụng cho Việt Nam).
  - **CMC Telecom** (Advanced, aws@cmctelecom.vn): bên duy nhất công khai xuất hoá đơn VND có VAT và tự lo FCT, nhưng chưa thấy họ có giấy Anthropic.
- Ưu: code giữ nguyên (vẫn Bedrock). Có thể được hoá đơn VND/VAT, hạn thanh toán và credit.
- Nhược: vẫn phụ thuộc giấy phép của reseller, đúng chỗ đã gãy lần này. Chưa có tài liệu nói account theo Billing Transfer có bị coi là "channel account" ở cổng Anthropic hay không, nên cứ coi là có [chưa kiểm]. Phía mình mất CUR và Cost Anomaly Detection. Renova và eCloudvalley có xuất hoá đơn VND hay không thì chưa kiểm.
- Công sức code: 0. Chi phí: khoảng $250 cộng phí của reseller (reseller không được chiết khấu trên Claude/OpenAI).

**3. acc3 đứng riêng, AWS tính tiền thẳng.**
- Làm gì: gắn thẻ thanh toán trên acc3, nộp lại form FTU của Anthropic ngay trên acc3 (form cũ kế thừa từ org eCloudvalley đã mất), kiểm quyền Marketplace, giữ case Support và nêu rõ bị chặn cả Nova/Cohere. Chỉ tin khi gọi model thật chạy được, vì `GetFoundationModelAvailability` vẫn có thể báo AUTHORIZED dù account đang bị chặn.
- Ưu: code 0, không có reseller. Nhược: thời gian do AWS quyết (trên re:Post có người chờ 1–2 tuần trở lên). AWS Inc. chỉ xuất hoá đơn thương mại bằng USD, VAT 10% (0% nếu khai đủ các số theo Thông tư 103), **không** xuất hoá đơn VAT điện tử Việt Nam. Chi phí: khoảng $250 theo giá niêm yết.

Ghi chú Azure: đối tác CSP Việt Nam (ví dụ FPT) bán được GPT kèm hoá đơn trong nước nhưng **không bán được Claude**, vì Microsoft không cho thuê bao CSP mua model bên thứ ba. Muốn dùng Claude trên Azure thì phải có tài khoản do Microsoft tính tiền thẳng.

## Khuyến nghị
- **Ngay bây giờ (case acc3 còn chờ):** dùng phương án 1 làm cầu nối. Bật OpenAI trực tiếp cho judge (vài giờ, cần chốt bỏ chính sách "chỉ Bedrock"), rồi viết adapter `anthropic_native` cho Claude. Song song, làm các bước của phương án 3 trên acc3.
- **Trung hạn:** giữ hai đường song song (Bedrock và mua thẳng từ hãng), chuyển qua lại bằng catalog để không còn phụ thuộc một account. Nếu kế toán bắt buộc hoá đơn VND/VAT: lấy báo giá của Renova và eCloudvalley VN (thêm CMC nếu họ chứng minh được giấy Anthropic), và chỉ ký theo hình thức Billing Transfer. Đồng thời hỏi kế toán: hoá đơn nước ngoài cộng kê khai FCT theo Thông tư 103 có đủ để tính chi phí hợp lệ không.

## Câu hỏi bắt buộc trước khi ký với reseller Việt Nam
1. Bên bạn có phải Anthropic Authorized Reseller cho Amazon Bedrock tại Việt Nam không (xin xác nhận bằng văn bản)? Account bán lại có gọi được Claude Sonnet/Haiku 5.5 ở us-west-1, kể cả cross-region profile không?
2. Account bán lại có gọi được model OpenAI không open-weight trên Bedrock không? Có SCP hay Private Marketplace nào chặn `aws-marketplace:Subscribe` hoặc `bedrock:InvokeModel` không?
3. Có hỗ trợ Billing Transfer (bên mình giữ org) không, hay bắt chuyển account vào org của bên bạn?
4. Có xuất hoá đơn VND và hoá đơn VAT điện tử cho **mọi** khoản, kể cả phí Bedrock/Marketplace, không? Tỷ giá tính theo đâu, hạn thanh toán bao lâu?
5. Claude và OpenAI tính theo giá niêm yết, có cộng phí hay có hoàn tiền không? Bên bạn đề cử được credit AWS nào (GenAI/POC), điều kiện ra sao?
6. Điều khoản thoát: phải báo trước bao lâu? Khi hết hợp đồng hoặc hết credit thì account và quyền dùng model ra sao (để không lặp lại chuyện acc3)? Ai mở và theo dõi case AWS Support cho account bán lại?

Nguồn chi tiết, mỗi ý có URL: angle1-aws-partners-vn.md và angle2-alternatives.md (cùng thư mục). Nguồn chính: [danh sách SPP](https://solution-provider-program-legal-documents.s3-us-west-2.amazonaws.com/Solution+Provider+Program+List+of+Services.pdf), [Renova](https://renovacloud.com/en/renova-cloud-accelerates-enterprise-ai-as-anthropic-authorized-reseller-in-vietnam/), [Billing Transfer](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html), [thuế AWS tại VN](https://aws.amazon.com/tax-help/vietnam/), [Azure/Claude với CSP](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude).
