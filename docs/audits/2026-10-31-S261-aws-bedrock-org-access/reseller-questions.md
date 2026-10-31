# Câu hỏi gửi đại lý AWS: Billing Transfer + Bedrock (S261)

Dán được nguyên văn cho đại lý. Nhờ trả lời bằng văn bản (email hoặc phụ lục hợp đồng); các câu đánh dấu ★ nên được
ghi vào hợp đồng trước khi ký. Nguồn và lý do của từng câu: `README.md` mục 7 và `claims.json`.

---

Chào bạn,

Bên mình đang chuẩn bị dựng AWS Organization riêng và muốn bên bạn trả hoá đơn AWS theo kiểu Billing Transfer. Bên
mình dùng Amazon Bedrock khá nhiều (Claude, GPT, Cohere, Nova) ở region us-west-1, nên cần hỏi kỹ mấy điểm dưới đây
trước khi ký. Nhờ bạn trả lời theo số thứ tự giúp bên mình; câu nào hỏi Có/Không thì nhờ trả lời Có/Không trước rồi
mới giải thích thêm.

**A. Hình thức thanh toán**

1. ★ Bên bạn có làm được Billing Transfer (AWS Billing Transfer) không: org của bên mình giữ nguyên, account quản trị
   của bên mình (bill-source account) nhận lời mời từ account quản trị của bên bạn (bill-transfer account)? Bên mình
   **không** muốn đưa account vào org của bên bạn (consolidated billing kiểu member account).
2. ★ Hợp đồng có điều khoản nào cho bên bạn giữ root, giữ quyền quản trị, hoặc đặt SCP (Service Control Policy) lên
   account của bên mình không? Bên mình cần giữ toàn quyền quản trị.
3. Bên bạn đã được AWS mở hạn mức nhận Billing Transfer (inbound billing transfer) chưa? (Có/Chưa)
3b. ★ Amazon Bedrock có nằm trong danh sách dịch vụ bên bạn được bán lại (SPP Authorized Services List) không? (Có/Không)
4. Ngày bắt đầu sớm nhất bên bạn gửi được lời mời là ngày nào? (AWS chỉ cho bắt đầu ngày 1 của tháng; bên mình cần
   chấp nhận trước ít nhất 24 giờ.)
5. Khi muốn dừng (withdraw transfer), bên mình cần báo trước bao lâu theo hợp đồng? Có phí phạt hay tiền cọc không?

**B. Claude, OpenAI và các khoản Marketplace**

6a. ★ Bên bạn có giấy phép bán lại của Anthropic (Anthropic resale authority, theo AWS Solution Provider Program) cho
    Claude trên Bedrock không? (Có/Không, nhờ gửi bản xác nhận)
6b. ★ Giấy phép đó có áp cho **khách ở Việt Nam** dùng theo **Billing Transfer** (account không nằm trong org của bên
    bạn) không? (Có/Không; nếu chỉ áp cho account trong org của bên bạn thì nhờ ghi rõ)
7. Các "giới hạn" (limitations) khi bán lại model Anthropic mà AWS nhắc tới là gì, và có ảnh hưởng tới bên mình không?
8. ★ Account của bên bạn có chấp nhận thanh toán các khoản AWS Marketplace phát sinh từ Bedrock (Claude của
   Anthropic, GPT của OpenAI, Cohere Embed) không? (Có/Không cho từng provider) Có chặn hay giới hạn provider nào
   không?
9. Bên bạn có đặt chính sách nào (SCP, Private Marketplace, chặn đơn hàng Marketplace) ảnh hưởng tới việc account của
   bên mình tự đăng ký model Bedrock lần đầu (auto-subscription on first invocation) không?
10. Bên mình gọi được những provider nào qua bên bạn: Anthropic, OpenAI (bản thương mại và gpt-oss), Amazon Nova,
    Meta, Mistral, Cohere, DeepSeek? Có model nào bên bạn biết là không gọi được không?
11. OpenAI trên Bedrock giới hạn theo danh sách quốc gia của OpenAI (Supported Countries). Bên bạn có xác nhận khách
    Việt Nam dùng được không? (Có/Không)
12. Nếu nhà cung cấp model có giá riêng (private offer, ví dụ CPPO), nhờ phát offer cho account quản trị của bên mình
    để bên mình chia cho các account con (managed entitlements). Bên bạn làm được không?

**C. Quyền truy cập theo từng account**

13. AWS ghi là một số model cần "quyền bổ sung ở mức account" (additional account-level access), quyết riêng cho từng
    account, kể cả trong cùng org. Bên mình sẽ có 3–4 account (quản trị, nonprod, ai, sau này prod). Bên bạn có giúp
    xin quyền này với AWS cho từng account không, ai đứng ra liên hệ AWS Sales, và thường mất bao lâu?
14. Một account của bên mình đang bị lỗi "Error 002: Access to Bedrock models is not allowed for this account" sau khi
    rời org của đại lý cũ. Bên bạn đã gặp trường hợp này chưa, và có giúp đẩy nhanh với AWS không?
15. Khi account chuyển vào org của bên mình hoặc khi đổi bên trả tiền (payer), bên bạn có biết account có bị khoá lại
    quyền Bedrock hay mất đăng ký Marketplace không? Có cần làm gì trước để tránh không?
16. Account của bên mình không gắn thẻ riêng (bên bạn trả). AWS có coi đó là "phương thức thanh toán hợp lệ cho
    Marketplace" (valid payment method for AWS Marketplace purchases) không, hay account quản trị của bên mình vẫn cần
    thẻ?

**D. Quota**

17. Bên bạn có hỗ trợ xin tăng quota Bedrock (Service Quotas, ví dụ "Cross-Region InvokeModel tokens per minute") cho
    Claude Sonnet/Haiku 5.5 ở us-west-1 không? Thời gian thường mất bao lâu?
18. Account mới thường nhận quota thấp. Bên bạn có cách nào giúp account mới có mức hợp lý ngay từ đầu không?

**E. Giá, hoá đơn, credit**

19. ★ Giá tính theo giá niêm yết AWS hay có phí dịch vụ? Bao nhiêu %, cộng VAT bao nhiêu? Có mức tối thiểu không?
20. ★ Các khoản Claude, GPT, Cohere (Marketplace) có nằm chung trên hoá đơn VAT VND với phần hạ tầng không?
21. Bên bạn dùng gói giá nào trong Billing Conductor: AWS managed (miễn phí) hay customer managed (50 USD/org/tháng)?
    Nếu có phí này thì ai chịu? Bên mình thấy giá niêm yết hay giá của bên bạn trong Cost Explorer?
22. ★ Credit AWS của bên mình (ví dụ AWS Lift khoảng 250 USD, hết hạn 31/12/2026) do AWS trừ vào hoá đơn gửi bên bạn.
    Bên bạn có đồng ý ghi vào hợp đồng là sẽ giảm đúng số đó trên hoá đơn cho bên mình không? (Có/Không)
23. Bên mình có còn xem được báo cáo chi phí chi tiết (Cost and Usage Report pro forma, lọc theo cost allocation tag)
    không? Bên bạn có gửi CUR cho bên mình không?

**F. Hỗ trợ**

24. Bên bạn có bán lại gói hỗ trợ AWS (Resold Support hoặc Partner-Led Support) không? Nếu có, bên mình còn tự mở case
    với AWS Support được không (case tài khoản/billing, case tăng quota)?
25. Khi có sự cố Bedrock bị từ chối, quy trình phối hợp giữa bên mình, bên bạn và AWS thế nào, thời gian phản hồi bao
    lâu?

Cảm ơn bạn. Bên mình chỉ ký khi các câu có dấu ★ có trong hợp đồng hoặc phụ lục.
