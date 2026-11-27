## Lịch chiều nay và việc cần làm {#lich}

| Giờ | Phần | Anh làm gì |
|---|---|---|
| 13:15 | Tới Bitexco, sảnh tầng trệt | Đến sớm 10–15 phút: nhận thẻ khách ở lễ tân, rồi check-in ở quầy an ninh tầng 26. Không thấy ban tổ chức thì gọi Sylvie (G-AsiaPacific): **+84 367 642 670** |
| 13:30 | Đón khách, networking | Dùng [giới thiệu 30 giây](#gioi-thieu). Hỏi peers các câu C1–C4 (mục [Câu hỏi](#cau-hoi) › C) |
| 14:00 | Opening Remarks | — |
| 14:10 | Keynote: Security for AI – What Leaders Must Prepare | Nghe để đối chiếu với [Tóm tắt 5 phút](#tom-tat). Nếu slide ghi mốc EU high-risk "08/2026" là lịch cũ (đã dời sang 12/2027) |
| 14:40 | Q&A: Securing AI Adoption | Chọn tối đa 2 câu có giá trị cao và an toàn khi hỏi công khai: **A1 (TIA chuyển dữ liệu ra nước ngoài)** và **A5 (PII detector của Guardrails đổi hành vi với tên tiếng Việt)** |
| 15:10 | Coffee break | Tìm AWS SA: hỏi riêng A2, A3, A4 (không nêu tài khoản cụ thể) |
| 15:25 | Live demo: Amazon Quick | Câu hỏi ở mục [Amazon Quick](#amazon-quick) |
| 16:10 | Executive 1:1 & Offer | Làm theo [Checklist 1:1 và ưu đãi](#offer): nhận review miễn phí, không ký gì |

## Amazon Quick: biết trước khi xem demo {#amazon-quick}

**Là gì:** không gian làm việc AI của AWS, ra mắt 10/2025 dưới tên "Amazon Quick Suite". Từ 09/11/2026 đổi tên thành **AWS Quick**. Gồm chat agents, Spaces, Quick Research (báo cáo có trích nguồn), Quick Flows, Quick Automate, Quick Sight (BI), knowledge base, Apps (preview), app desktop và mobile. Kết nối tới các app ngoài qua action connector, REST/OpenAPI và MCP (khoảng 68 tích hợp trong tài liệu chính thức). [Nguồn](https://aws.amazon.com/about-aws/whats-new/2026/11/amazon-quick-aws-quick/)

**Giá (trang pricing, 26/11/2026):**

| Gói | Giá | Ghi chú |
|---|---|---|
| Free / Plus / Max (cá nhân, không cần tài khoản AWS) | $0 / $20–25 / $100–125 mỗi người mỗi tháng | Nằm ngoài quản trị AWS (không có IAM Identity Center) |
| Essentials (tổ chức) | $3/người/tháng + **$250/tài khoản/tháng** | 1 agent hour/người (3 giờ tới 31/01/2027) |
| Professional | $20/người/tháng + $250/tài khoản/tháng | 8 agent hours/người |
| Enterprise | $40/người/tháng + $250/tài khoản/tháng | 18 agent hours; Automate, tạo dashboard, KMS key riêng |
| Vượt mức | $3/agent hour (tính theo giây); index $5/GB/tháng | — |

Ước tính cho AA: Professional 10 người khoảng $450/tháng, 30 người khoảng $850/tháng. [Nguồn](https://aws.amazon.com/quick/pricing/)

**Cảnh báo về bản dùng thử:** dùng thử 30 ngày cho tối đa 25 người, đủ tính năng Enterprise, không cần thẻ. **Hết 30 ngày, tài khoản có AWS account tự bị tính gói Enterprise.** Không bật trên tài khoản mà đơn vị bán lại hiện tại còn trả tiền (tới 01/12). Chỉ bật trong tài khoản của tổ chức công ty, sau khi đã đồng ý chi phí bằng văn bản, và đặt lịch nhắc dừng trước ngày 30.

**Dữ liệu và bảo mật:**
- AWS không train model trên dữ liệu khách hàng, ở mọi gói.
- Region gần nhất là Singapore (agentic từ 10/2026). Trang Regions ghi inference ở Singapore là **"Global CRIS"**: dữ liệu lưu ở Singapore nhưng prompt có thể được xử lý ở bất cứ đâu, và không tắt được (SCP và control của Bedrock không áp dụng). [Nguồn](https://docs.aws.amazon.com/quick/latest/userguide/outbound-connections.html)
- Guardrails mặc định chỉ có tối đa 50 từ bị chặn. "Enterprise Guardrails" (có PII, denied topics) đang ở public preview, phải xin qua AWS account team. [Nguồn](https://docs.aws.amazon.com/quick/latest/userguide/guardrails.html)
- Truy xuất theo quyền (ACL) chỉ có với knowledge base trên S3, Google Drive, SharePoint, Confluence, OneDrive. Gmail, Jira, Linear, Notion chỉ là action connector, không index được làm kiến thức.
- Nội dung chat không nằm trong CloudTrail. Phải bật log delivery sang CloudWatch/S3 ngay từ đầu.
- KMS key riêng cần Enterprise, và phải chọn trước lần chat đầu tiên (không đổi được sau).
- Tính năng AI mới tự bật cho mọi người dùng nếu admin không chặn trước (custom permissions cần Enterprise).

**Hợp với AA đến đâu:** yếu đến trung bình. Google Workspace đã có Gemini; AA có gateway và admin riêng; Kiro và Claude Code lo phần code. Nếu thử, chỉ thử hẹp: 3–5 người, sau 01/12, trong tài khoản công ty, để tra cứu nội bộ và hỏi đáp trên một thư mục Drive chứa SOP và policy. Không nối với Booking, CRM (dữ liệu cá nhân của khách) hay API của AA qua MCP.

**Câu hỏi trong demo:**
1. Với home Region Singapore, inference thực tế chạy ở đâu? Trang Regions ghi "Global CRIS" nhưng bài ra mắt ghi "processed locally". Có lộ trình cho inference chỉ trong APAC không?
   *With a Singapore home Region, where does inference actually run? The Regions page says Global CRIS, the launch post says processed locally. Is APAC-only inference on the roadmap?*
2. Ngày 31 của bản dùng thử: tự chuyển sang Enterprise cho mọi người dùng thử, hay phải chọn? Huỷ hoặc hạ gói thế nào, và phí $250 có tính theo ngày không?
   *What happens on day 31 of the trial: automatic Enterprise billing for every trial user, or opt-in? How do we cancel or downgrade, and is the $250 fee pro-rated?*
3. Có phát hiện hoặc che PII (như sensitive-information filter của Bedrock Guardrails) cho chat và flows không, hay chỉ có 50 từ bị chặn?
   *Is there PII detection or redaction for chat and flows, or only the 50 blocked words?*
4. Admin có thể ghim hoặc loại một model, hoặc dùng model Bedrock từ tài khoản của chính mình không?
   *Can an admin pin or exclude a model, or bring Bedrock models from our own account?*
5. Với Google Workspace: knowledge base Google Drive có ACL hỗ trợ Shared Drives không? Gmail có bao giờ được index làm kiến thức không?
   *Does an ACL-aware Google Drive knowledge base support Shared Drives? Can Gmail ever be indexed as knowledge?*
6. Flows và Automate chạy bằng quyền service, không phải quyền người tạo. Giới hạn phạm vi và xem audit từng lần chạy thế nào?
   *Automated workflows run with service-level credentials. How do we scope them and see per-run audit records?*

## Kiro: điều đáng hỏi {#kiro}

- Gói cá nhân (26/11/2026): Free $0 (50 credits), Pro $20 (1.000), Pro+ $40 (2.000), Pro Max $100 (5.000), Power $200 (10.000); credit thêm $0,04. [Nguồn](https://kiro.dev/docs/billing/)
- **Bản dùng thử của sự kiện không thêm gì cho AA:** từ 01/11/2026, trial chỉ áp cho lần nâng cấp đầu tiên từ Free (phần còn lại của tháng trên Pro + 500 credit, cần thẻ). AA đã trả tiền nên không được hưởng. [Nguồn](https://kiro.dev/docs/billing/)
- Thứ có giá trị là **Kiro Enterprise**: đăng nhập qua IAM Identity Center, nội dung doanh nghiệp không dùng để cải tiến dịch vụ, admin kiểm soát model và danh sách MCP được phép, CloudTrail và báo cáo sử dụng, gộp credit, tính tiền trên hoá đơn AWS (credit AWS bù được).
- **Kiro for Startups:** tới 1 năm credit Pro+, nhận đơn tới 31/12/2026. Không áp cho công ty đang có AWS Activate credit. [Nguồn](https://kiro.dev/startups/terms/)
- Hai trang chính thức nói khác nhau về việc dùng nội dung gói cá nhân để train. Cần kiểm kiro-cli của AA đăng nhập kiểu gì và đã bật opt-out chưa.
- Model mới trên Enterprise (Claude Fable 5.2 tính 6x credit, GPT 6.2 Astra 7.2x) đốt credit rất nhanh. Chuyển lên Enterprise thì phải đặt danh sách model và giới hạn trước.

**Câu hỏi:**
1. "Dùng thử Kiro" của sự kiện là credit AWS, ghế Kiro Enterprise hay trial gói cá nhân? Cần thẻ không, có tự gia hạn không?
   *Is the event's Kiro trial AWS promotional credit, Kiro Enterprise seats or an individual-plan trial? Card needed? Does it renew by itself?*
2. Gói cá nhân trả tiền (Pro trở lên): câu nào là ràng buộc về việc dùng nội dung để train? Opt-out có phủ phiên kiro-cli không?
   *For paid individual plans, which statement on training is binding, and does the opt-out cover kiro-cli sessions?*
3. Chuyển các subscription cá nhân hiện tại sang Kiro Enterprise trên Identity Center của công ty mà không trả trùng tháng chuyển được không?
   *Can we move current individual subscriptions to Kiro Enterprise on our own Identity Center without paying twice in the switch month?*

## Phiên 1:1 và ưu đãi lúc 16:10 {#offer}

**Đồng ý ngay (miễn phí, không cam kết):** buổi review AI Security 1-1 với AWS Specialist, tài liệu đọc thêm (Scoping Matrix, Generative AI Lens, tài liệu Guardrails), hẹn buổi gặp tiếp với AWS.

**Mang về quyết định:**
- Mọi thứ đổi đơn vị xuất hoá đơn AWS: partner of record, đơn vị bán lại mới, thư uỷ quyền.
- Mọi chương trình credit (Activate, Kiro for Startups, credit review Well-Architected hay POC của partner, ARRC) và việc credit vào tài khoản nào.
- Mọi bản dùng thử tự chuyển sang trả tiền: Amazon Quick (Enterprise $40/người + $250/tài khoản sau 30 ngày), AWS Continuum pentest ($50/task-hour sau 2 tháng trial), Kiro Enterprise.

**Không ký trên đó:** order form, hợp đồng MAP/POC, thư uỷ quyền. AA đang có hợp đồng đã ký với đơn vị bán lại, và tài khoản sẽ chuyển sang tổ chức AWS của công ty ngày 01/12.

**Về thời điểm credit:** credit cấp trước 01/12 vào tài khoản còn nằm trong tổ chức của đơn vị bán lại có thể bị dùng trên hoá đơn của họ tới hết kỳ. Xin cấp sau 01/12, vào tài khoản AA chỉ định. Các chương trình credit loại trừ nhau (AWS Lift đòi chưa từng nhận Activate; Kiro for Startups loại công ty đang có Activate), nên phải xếp thứ tự trước khi nộp.

**Mang vào phiên 1:1:** kiến trúc một trang mô tả theo vai trò (tài khoản quản lý, tài khoản workload, tài khoản phục vụ model, dự phòng), không account ID, ARN hay hostname; danh sách bề mặt AI (writer, chat, CRM drafts, coding agents); loại dữ liệu đi qua mỗi bề mặt; control hiện có; 3 câu hỏi chính (A1, A2, A6).

**Review thường dựa trên:** Generative AI Security Scoping Matrix và Agentic AI Security Scoping Matrix; 6 vùng bảo mật của Well-Architected Generative AI Lens (endpoint security, kiểm response, giám sát sự kiện, prompt security, excessive agency, data poisoning); Bedrock Guardrails ép bằng `bedrock:GuardrailIdentifier` trong IAM/SCP; điều khoản không train và invocation logging của Bedrock.

**Câu hỏi trong 1:1:**
1. Kết quả review có thành báo cáo viết AA giữ được, không cần NDA, không chia sẻ dữ liệu, không bắt mua tiếp không? Ai ở AWS (không phải partner) theo dõi tiếp?
   *Will the review produce a written report we keep, with no NDA, no data-sharing agreement and no follow-up purchase? Who at AWS owns the follow-up?*
2. Với gateway gọi Claude và GPT qua Bedrock và API nhà cung cấp, 3 control nào nên làm trước: Guardrails ép bằng SCP, invocation logging, hay VPC endpoint? Chi phí mỗi tháng với lưu lượng nhỏ?
   *For our gateway, which three controls first: Guardrails enforced via SCP, invocation logging or VPC endpoints? Monthly cost at our volume?*
3. AWS review mẫu gọi Bedrock chéo tài khoản (role của app assume role có ExternalId ở tài khoản khác) thế nào? Nên đổi gì trước production?
   *How do you review a cross-account Bedrock invoker pattern (app role assuming a role with ExternalId)? What to change before production?*
4. Coding agent được push branch nhưng không merge thì thuộc scope nào trong Agentic Scoping Matrix, và AWS mong control gì thêm?
   *Which Agentic Scoping Matrix scope fits coding agents that push branches but never merge, and what extra controls apply?*
5. Ưu đãi nào của partner (credit review, tài trợ POC, ARRC) đòi đổi partner of record, cam kết chi tiêu tối thiểu hay chia sẻ dữ liệu hoá đơn?
   *Does any partner offer require a partner-of-record change, minimum spend, term commitment or sharing billing data?*
