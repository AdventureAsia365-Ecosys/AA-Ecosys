# Anthropic Usage Policy (effective 12/11/2026) vs AA_Ecosys use cases — S236


**Nguồn đã đọc (14/10/2026):**
- Bản mới: https://www.anthropic.com/legal/aup, trang ghi **"Effective November 12, 2026"**. Mình đọc được trực tiếp, không phải làm việc từ bản cũ.
- Bản trước để so sánh: https://www.anthropic.com/legal/archive/22742366-2ef0-4c7a-a833-6523f10d3944, **hiệu lực 15/09/2025**.
- Trang không có changelog, nên phần "điều gì thay đổi" bên dưới là mình tự so hai bản.
- Mình chưa đọc nội dung AWS Health notice.

Ký hiệu: **[Văn bản]** là trích nguyên văn chính sách. **[Diễn giải]** là ý kiến của mình, chưa phải ý kiến pháp lý.

### (a) Điều gì thay đổi / quy tắc liên quan tới mình

1. **Phạm vi áp dụng**
   - [Văn bản] Áp dụng cho "customers accessing Claude through cloud providers… and the end users of products or services integrating Claude".
   - [Diễn giải] Như vậy chính sách áp dụng cho AA (qua Bedrock acc3/acc1), và qua AA áp dụng tiếp cho tenant và khách TripPlanner.
   - [Diễn giải] Model không phải của Anthropic (GPT Luna làm judge, Jev/TypeSafe, Cohere embed) không thuộc AUP này, nhưng vẫn chịu AUP của AWS và của nhà cung cấp đó.

2. **"High-Risk Use Case Requirements" được viết lại**
   - Thay đổi chính: danh sách mới gồm 11 lĩnh vực. Hai lĩnh vực đáng chú ý với mình:
     - "Finance and investment/tax advice" (tư vấn tài chính, đầu tư, thuế)
     - "Insurance underwriting and claims" (thẩm định bảo hiểm và bồi thường)
   - Các lĩnh vực còn lại (pháp lý, y tế, tín dụng, nhà ở, tuyển dụng, giáo dục, phúc lợi, di trú) không liên quan tới mình.
   - **Bản 09/2025 có "Media/Journalistic Content" trong nhóm high-risk. Bản mới đã bỏ mục này.**
   - Hai yêu cầu bắt buộc:
     - [Văn bản] Human-in-the-loop: "A qualified person must meaningfully review a High-risk AI Recommendation, with the authority to change or modify it, before it is delivered as advice…"
     - [Văn bản] Disclosure: "An individual who receives advice or who is the subject of a decision based on a High-risk AI Recommendation must be clearly told that AI was used to produce it."
   - [Diễn giải] Các use case hiện tại (nội dung du lịch, lịch trình) không nằm trong nhóm high-risk. Việc bỏ mục Media làm blog/social T9 nhẹ ràng buộc hơn bản cũ.

3. **Chatbot hướng tới người tiêu dùng (Additional use case guidelines)**
   - [Văn bản] "All consumer-facing chatbots or AI agents that communicate directly with external users must disclose to users that they are interacting with AI rather than a human. This disclosure must be provided at a minimum at the beginning of each chat session **or in the product interface**. The disclosure does not need to identify Anthropic, Claude, or the model used."
   - Thay đổi: bản cũ chỉ yêu cầu "at session start". Bản mới cho phép đặt trong giao diện sản phẩm.

4. **"Do Not Engage in Deceptive Campaigns or Artificial Activity"** (phần mở rộng đáng chú ý)
   - [Văn bản] Cấm "Create or operate fake personas… or impersonate real people, organizations… to mislead people about their origin or attribution, how widely a view is held, or whether they are interacting with a human (e.g., sockpuppets, astroturfing, fake reviews, or bots that claim to be human)".
   - [Văn bản] Cấm "misrepresent or intentionally conceal the sponsorship of content…".
   - [Văn bản] Cấm "networks of fake or ostensibly independent outlets, websites, or accounts to hide that it comes from a common source".
   - [Văn bản] Mới, liên quan SEO: cấm "Manipulate the sources from which search engines or AI systems draw answers by seeding them with content that misrepresents its origin, authorship, or independence".
   - [Văn bản] Cấm spam và hạ tầng phục vụ "coordinated inauthentic behavior".

5. **Thông tin sai lệch**
   - [Văn bản] Cấm "deceptive or misleading information about a group, entity, or person, or about events, laws, regulations, procedures…".
   - [Văn bản] Cấm "Plagiarize or submit AI-assisted work without proper permission or attribution".

6. **Quyền riêng tư**
   - [Văn bản] Cấm "compile, aggregate, or enrich personal data from multiple sources to build profiles of individuals for sale… without those individuals' awareness and agreement".
   - [Diễn giải] Liên quan tới "taste vector" của TripPlanner, nhưng hiện chỉ dùng nội bộ, không bán, nên ổn.

7. **Agentic use**
   - [Văn bản] "Users are responsible for ensuring that agents they build or deploy, including actions those agents take through tools… comply with this Usage Policy."

### (b) Bảng use case → quy tắc → trạng thái → hành động

| Use case | Quy tắc liên quan | Trạng thái | Hành động cụ thể |
|---|---|---|---|
| **1. A-series** (S1 viết lại tour của AA, có judge) cho adventure.asia | Disinformation; search-engine seeding; plagiarize/attribution | **OK** [Diễn giải]: AA là tác giả thật, viết trên site của chính mình | Giữ chính sách bám sát nguồn: không hứa hoạt động, dịch vụ hay giờ giấc mà nguồn không có. Không đăng nội dung đứng tên "người viết độc lập" hay "review khách hàng" giả. Tuỳ chọn: thêm câu "Content created with AI assistance and reviewed by Adventure Asia" vào trang About/Editorial. |
| **2. T-series** (T2 viết lại tour theo giọng tenant, T9 blog/LinkedIn/Facebook đăng dưới tên tenant; tenant không thấy phần AI bên trong) | Deceptive campaigns (fake personas, astroturfing, fake reviews, che giấu tài trợ, mạng outlet giả); spam/CIB; search seeding; "end users… integrating Claude" | **Cần hành động** | (i) Thêm điều khoản AUP vào Terms tenant: tenant phải tuân thủ Anthropic AUP; cấm dùng output cho fake reviews, testimonial, sockpuppet, mạng tài khoản/site giả, đăng đứng tên cá nhân không có thật, che giấu nội dung tài trợ, spam. (ii) Nói rõ trong Terms và trong portal rằng nội dung do AI tạo, tenant chịu trách nhiệm duyệt trước khi đăng. Điều này không mâu thuẫn với quy tắc "tenant chỉ thấy content": chỉ là một dòng ghi chú, không lộ gate hay điểm số. (iii) Giữ guard trong prompt T9 (`services/acp_angle_gate/prompts.py` đã có "Never invent… testimonials") và thêm check: không sinh nội dung giả làm review hay viết ở ngôi người dùng/khách. (iv) Giới hạn tần suất/khối lượng publish mỗi tenant (chống spam) và lưu `publish_log` làm bằng chứng. (v) Có quy trình khoá tenant vi phạm (đã có deactivate). |
| T2/T9 đăng dưới tên tenant (không ghi "AI") | Impersonation, "mislead about origin or attribution" | **Chưa rõ, nghiêng về OK** [Diễn giải] | Tenant là tác giả và pháp nhân thật, tự duyệt và đứng tên, nên thường không bị coi là "impersonate". Chính sách không bắt buộc gắn nhãn AI cho nội dung marketing ngoài nhóm high-risk. Rủi ro chỉ phát sinh nếu tenant dùng persona giả. Gửi legal xác nhận. |
| **3. TripPlanner** (khách công khai, không đăng nhập; tường thuật theo ngày + semantic search) | Disclosure cho chatbot/AI agent; disinformation | **OK nếu badge luôn hiển thị** | Tường thuật không phải chat, nhưng [Diễn giải] nên coi như "AI agent communicating with external users" cho an toàn. Badge "AA + AI" / "AI-assisted" đã đáp ứng tiêu chí "in the product interface", vì chính sách cho phép ghi chú trong UI. Cần: badge hiện trên mọi khối văn bản AI sinh ra, kể cả mobile và bản share/print/export. Nếu sau này có ô chat, hiện câu thông báo AI ở đầu mỗi phiên. Semantic search (Cohere) không thuộc AUP Anthropic. Thêm một câu nhắc người dùng kiểm tra lại giờ giấc, visa, sức khoẻ, vì đây là thông tin thực tế có thể sai. |
| **4.** LLM-as-judge, bản nháp place-card fact, Jev decisions | Không thuộc high-risk; quy tắc agentic | **OK** | Chỉ chấm điểm và duyệt nội dung nội bộ, không phải quyết định về con người. Giữ `llm_call_log` / `decision_log` làm audit trail. Judge GPT và Jev nằm ngoài AUP Anthropic [Diễn giải]. Place-card facts vẫn đi qua review queue của người. |
| **5. AA-Booking** (proposal/báo giá tương lai, chưa có AI quyết định giá) | High-risk: "Finance… advice", "Insurance underwriting and claims"; chatbot disclosure | **OK hiện tại; cần chặn trước khi mở rộng** | [Diễn giải] Báo giá tour không phải tư vấn tài chính. Nhưng nếu sau này AI gợi ý mua hay chọn **bảo hiểm du lịch**, gói **trả góp/tín dụng**, xử lý **claims/hoàn tiền**, hoặc tư vấn **visa/di trú** thì thuộc high-risk: bắt buộc nhân viên có chuyên môn duyệt và có quyền sửa trước khi gửi, kèm thông báo AI cho khách. Ghi điều này vào ADR hoặc CONTEXT của Booking. Proposal do AI soạn: giữ cơ chế nhân viên duyệt trước khi gửi. Nếu có chat với khách, hiện thông báo AI ở đầu phiên. |

### (c) Việc cần làm trước 12/11/2026 (theo ưu tiên)

1. **P0: Thêm điều khoản AUP vào Terms/hợp đồng tenant (T-series).** Gồm: tuân thủ Anthropic AUP; cấm fake reviews, sockpuppet, astroturfing, mạng site/tài khoản giả, che giấu tài trợ, spam; tenant chịu trách nhiệm duyệt và đăng; AA được quyền khoá tenant. Cần legal soạn.
2. **P0: Thêm dòng ghi chú trong portal tenant (T10 review / T11 publish).** Ví dụ: "This content was generated with AI. Review it before publishing; you are responsible for what you publish." Chỉ là một dòng, không lộ phần bên trong.
3. **P1: Kiểm tra badge AI trên TripPlanner** ở mọi chỗ có văn bản AI (trang trip, ngày, share/export, mobile). Cân nhắc thêm câu nhắc kiểm tra lại thông tin thực tế.
4. **P1: Thêm guard trong prompt và gate cho T9**: không viết dạng review/testimonial, không viết ở ngôi khách hàng, không tự nhận là "independent". Thêm giới hạn khối lượng publish mỗi tenant mỗi ngày.
5. **P2: Ghi ranh giới high-risk vào ADR hoặc CONTEXT của AA-Booking** (bảo hiểm, trả góp, claims, visa phải có người duyệt và thông báo AI).
6. **P2: Câu ghi chú editorial trên adventure.asia** (tuỳ chọn, theo quyết định thương hiệu).
7. **P2:** Đọc nguyên văn AWS Health notice cho acc3 (786888028788) để xác nhận không có điều khoản riêng của Bedrock. Lưu kết quả audit này vào `docs/audits/<date>-S236-aup-2026-11/`.

### (d) Cần đưa lên legal / stakeholder

- **Legal:**
  - Soạn điều khoản AUP trong Terms tenant (mục 1).
  - Xác nhận cách diễn giải rằng nội dung T2/T9 đăng dưới tên tenant mà không có nhãn AI thì không vi phạm điều khoản "attribution/origin" và "plagiarize… without attribution".
  - Xác nhận TripPlanner chỉ cần badge trong UI là đủ.
  - Kiểm tra luật địa phương về gắn nhãn nội dung AI (EU AI Act, quy định quảng cáo), vì các luật này có thể chặt hơn AUP. Mình không đánh giá phần này.
- **Business / chị Thư / Sales:**
  - Báo tenant hiện có về điều khoản mới.
  - Quyết định có ghi chú "AI-assisted" công khai trên adventure.asia hay không.
- **Product owner AA-Booking:** chốt rằng không đưa AI vào tư vấn bảo hiểm, tài chính hay visa khi chưa có quy trình người duyệt và thông báo AI.

Lưu ý: trang AUP không có changelog chính thức. Phần "thay đổi" ở trên, đặc biệt việc bỏ "Media/Journalistic" khỏi nhóm high-risk và cho phép "or in the product interface", là kết quả mình tự so hai bản.