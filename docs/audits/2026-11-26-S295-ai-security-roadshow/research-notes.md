# AI Security Roadshow 2026 (26/11/2026): research notes

Prep page (private artifact): https://claude.ai/artifact/VhWV6pXCHGFMn5uKwQPBgq

Public-safe copy: the internal sections (AA security posture, what not to disclose) live only in the artifact. Research by a fact-checked multi-agent workflow on 26/11/2026; legal points need a lawyer's confirmation.


> "AI Governance and Security At Scale", G-AsiaPacific Việt Nam × AWS, tầng 26 Bitexco, 13:30–17:00.
> Số liệu kiểm ngày 26/11/2026. Mỗi mốc ngày có nguồn ở cột/ngoặc. "(chưa xác minh)" = chưa đối chiếu được nguồn gốc, đừng trích như sự thật.

---

## 1. Tóm tắt 5 phút

1. **EU AI Act đã đổi lịch.** Digital Omnibus on AI là **Regulation (EU) 2026/1744** (đăng OJ 24/07/2026, hiệu lực 27/07/2026). Mốc "high-risk từ 8/2026" trên slide cũ đã lỗi thời: Annex III dời sang **02/12/2027**, Annex I sang **02/08/2028**. **Art. 50 (minh bạch)** áp dụng từ **02/08/2026**. Hệ thống GenAI đã có mặt trên thị trường trước đó được tới **02/12/2026** cho phần đánh dấu máy đọc được (50(2)). Use case của AA không thuộc Annex III. Việc AA phải làm là minh bạch, và AA đã gắn dấu AI trên mọi kênh từ 20/11.
2. **Việt Nam đã có đủ bộ khung pháp lý:**
   - PDPL 91/2025/QH15 và NĐ 356/2025: hiệu lực 01/01/2026.
   - NĐ 330/2026 xử phạt: hiệu lực 19/08/2026, không có thời gian chuyển tiếp.
   - Luật AI 134/2025/QH15: hiệu lực 01/03/2026. Kèm NĐ 142/2026, QĐ 33/2026 và cổng một cửa **ai.dda.gov.vn** (chạy từ 28/08/2026).
   - Luật An ninh mạng 116/2025/QH15: hiệu lực 01/07/2026, cùng NĐ 327–333/2026.
3. **Điểm nóng nhất với AA là chuyển dữ liệu ra nước ngoài.** Dữ liệu nằm ở US, các lời gọi LLM đi Bedrock và Anthropic/OpenAI API, nên tất cả đều là chuyển dữ liệu xuyên biên giới. AA cần hồ sơ đánh giá tác động chuyển dữ liệu (TIA) gửi A05/Bộ Công an. Miễn trừ 5 năm cho startup chỉ miễn DPIA và DPO (Điều 21, 22, 33(2)), **không miễn Điều 20 (TIA) và Điều 23 (báo vi phạm)**. AA cũng có thể mất cả miễn trừ đó vì làm "dịch vụ xử lý dữ liệu" cho đại lý (CRM). Câu này cần luật sư xác nhận.
4. **Theo Luật AI VN, chat trip-planner và CRM AI drafts nhiều khả năng ở mức "rủi ro trung bình"** (người dùng có thể không biết mình đang làm việc với AI). AA cần tự phân loại, rồi tự khai báo trên cổng ai.dda.gov.vn. Hệ thống đã chạy trước 01/03/2026 có hạn tới **01/03/2027**. QĐ 33/2026 liệt kê 46 hệ thống rủi ro cao trong 6 ngành (giáo dục, dân tộc và tôn giáo, y tế, ngân hàng, tư pháp, giao thông), **không nêu du lịch hay chatbot**.
5. **OWASP Top 10 for LLM có bản 2026** (công bố 04/08/2026): Excessive Agency lên #3, System Prompt Leakage đổi thành **Hidden Context Exposure** (#8), Improper Output Handling xuống #10. Thêm **OWASP Top 10 for Agentic Applications** (ASI01–ASI10, 09/12/2025) và **MITRE ATLAS 2026.10** (16 tactics, 129 techniques). Khi nói chuyện, dùng ID chuẩn.
6. **Sự cố thật 2025–2026 đi theo cùng một mẫu: indirect prompt injection kết hợp "lethal trifecta"** (có dữ liệu riêng, nhận nội dung không tin cậy, gửi được ra ngoài). Ví dụ: EchoLeak, GitHub MCP, postmark-mcp, s1ngularity (mã độc gọi các AI CLI), Amazon Q extension. Với startup, bề mặt rủi ro thật nằm ở **coding agents, MCP và npm**.
7. **Bedrock Guardrails đã dùng được cho tiếng Việt.** Standard tier ghi tiếng Việt là "Optimized and supported", kể cả bộ lọc PII, nhưng tier này cần cross-region inference. **ApplyGuardrail** và **InvokeGuardrailChecks** (06/2026) cho phép đặt một chính sách chung cho mọi provider ngay tại gateway. Áp guardrail toàn tổ chức GA từ 03/04/2026, và đã có thể áp ở cấp từng tài khoản. Giá khoảng $0.40 cho 1.000 text units khi bật 3 bộ lọc.
8. **Lưu trú dữ liệu (data residency):** Claude Sonnet 5 có **in-Region inference tại Singapore** (AWS ngày 29/09/2026). Hanoi Local Zone GA ngày 19/06/2026 nhưng **không có Bedrock**. Việt Nam vẫn chưa có AWS Region.
9. **Phát hiện tấn công:** **GuardDuty AI Protection** (14/07/2026) bắt các lời gọi bất thường, cost harvesting và prompt injection (phần này cần Guardrails); có trial 30 ngày. **AWS Continuum for Penetration Testing** (tên mới của AWS Security Agent) giá $50/task-hour, trial 2 tháng.
10. **ISO:** 42001:2023 không có bản sửa đổi. **27090:2026** (10/2026) là danh mục mối đe dọa cho AI, dạng hướng dẫn. **42005:2025** là khung cho AI impact assessment. AWS có chứng chỉ 42001 cho Bedrock, AA dùng được làm bằng chứng nhà cung cấp (tải từ AWS Artifact). AA chỉ đi chứng nhận khi khách hàng yêu cầu.

---

## 2. Bản đồ tiêu chuẩn & luật

### Việt Nam

| Tên | Loại | Trạng thái & mốc (as of 11/2026) | Ý nghĩa với AA | Nguồn |
|---|---|---|---|---|
| Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 (PDPL) | Luật | Thông qua 26/06/2025; hiệu lực 01/01/2026. Đ.20: hồ sơ chuyển dữ liệu ra nước ngoài. Đ.23: báo vi phạm. Đ.38: miễn trừ 5 năm cho startup/DN nhỏ, chỉ với Đ.21, 22, 33(2); không áp dụng nếu xử lý dữ liệu nhạy cảm trực tiếp, xử lý ≥100.000 chủ thể, hoặc cung cấp dịch vụ xử lý | Áp trực tiếp. Hosting US và gọi LLM nước ngoài đều là chuyển dữ liệu ra nước ngoài. CRM có thể khiến AA thành "bên cung cấp dịch vụ xử lý" (cần luật sư) | https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Law-91-2025-QH15-Personal-Data-Protection-665440.aspx |
| Nghị định 356/2025/NĐ-CP | Luật (NĐ) | Ban hành 31/12/2025, hiệu lực 01/01/2026, thay NĐ 13/2023. Báo vi phạm cho A05 trong 72h (với vi phạm thuộc diện). Đồng ý phải kiểm chứng được: không tick sẵn, không mặc định | Kiểm UX đồng ý trên trip planner và form booking. Thời điểm nộp TIA có hai cách đọc: luật Đ.20(2) ghi trong 60 ngày từ lần chuyển đầu; EY đọc NĐ 356 là thẩm định trước (A05 xem trong 15 ngày, DN có 30 ngày bổ sung). Hướng an toàn: **nộp trước khi có dữ liệu pilot thật** | https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/legal-alert-march-2026-decree-no-356-2025-nd-cp-providing-detailed-guidance-for-implementation-of-personal-data-protection-law |
| Nghị định 330/2026/NĐ-CP (xử phạt an ninh mạng + DLCN) | Luật (NĐ) | Ban hành và hiệu lực 19/08/2026, không chuyển tiếp. Vi phạm chuyển dữ liệu ra nước ngoài gây mất hoặc lộ: phạt 1–5% doanh thu VN năm trước (hoặc tới 3 tỷ đồng). Xử lý không có đồng ý: tới 50 triệu; sau khi người dùng rút đồng ý hoặc coi im lặng là đồng ý: 50–70 triệu. Mức 100 triệu (DPIA) và 30 triệu (DPO) (chưa xác minh) | Chế tài đã thi hành được ngay. Rủi ro lớn hơn tiền phạt là bị buộc dừng luồng dữ liệu ra nước ngoài, tức dừng cả nền tảng | https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/legal-alert-decree-330-2026-nd-cp-providing-sanctions-for-personal-data-protection-law-violations |
| Luật Trí tuệ nhân tạo 134/2025/QH15 | Luật | Thông qua 10/12/2025, hiệu lực 01/03/2026. 3 mức rủi ro (cao / trung bình / thấp). Hệ thống chạy trước 01/03/2026: hạn 01/03/2027, riêng y tế/giáo dục/tài chính 01/09/2027. Hệ thống tương tác trực tiếp với người phải cho biết là AI; nội dung sinh ra phải gắn nhãn. Bãi bỏ Chương IV (AI) của Luật 71/2025. Chưa có NĐ xử phạt riêng cho AI (chưa xác minh). NĐ 401/2026 (CNCN số, hiệu lực 22/12/2026) có phủ nghĩa vụ AI hay không (chưa xác minh) | Chat và CRM drafts nhiều khả năng ở mức trung bình (minh bạch). Writer ở mức thấp đến trung bình | https://www.allenandgledhill.com/perspectives/publications/bulletins-vietnam/2026/vietnam-s-new-law-on-artificial-intelligence-risk-based-regulatory-framework-in-force-1-march-2026/ |
| Nghị định 142/2026/NĐ-CP + cổng ai.dda.gov.vn | Luật (NĐ) + công cụ | NĐ ban hành 30/04/2026, hiệu lực 01/05/2026. Hệ thống rủi ro trung bình hoặc cao phải lập hồ sơ phân loại và tự khai báo với Bộ KH&CN trước khi triển khai. Cổng một cửa chạy từ 28/08/2026: thông báo phân loại, cấp mã hệ thống, báo sự cố nghiêm trọng, đăng ký sandbox. Có thể gộp DPIA theo PDPL vào hồ sơ | Việc cụ thể trước pilot: tự phân loại chat và CRM drafts, rồi khai báo nếu ở mức trung bình | https://lsvn.vn/chinh-thuc-van-hanh-cong-thong-tin-mot-cua-ve-tri-tue-nhan-tao-a178433.html |
| QĐ 33/2026/QĐ-TTg (danh mục AI rủi ro cao) | Luật (QĐ) | Ban hành 30/06/2026, hiệu lực 15/08/2026. 46 hệ thống trong 6 ngành. Nhiều mục chỉ bị xếp rủi ro cao khi đầu ra AI là căn cứ duy nhất để quyết định, không có người xem xét thực chất | Du lịch và chatbot không có trong danh sách, nên AA nhiều khả năng không thuộc rủi ro cao | https://lsvn.vn/chinh-thuc-van-hanh-cong-thong-tin-mot-cua-ve-tri-tue-nhan-tao-a178433.html |
| Luật An ninh mạng 116/2025/QH15 | Luật | Thông qua 10/12/2025, hiệu lực 01/07/2026; 8 chương, 45 điều. Thay Luật ATTTM 2015 và Luật ANM 2018. Gỡ nội dung trong 24h khi Bộ Công an yêu cầu (6h trong tình huống khẩn). Cấm dùng AI giả mạo hình ảnh hoặc giọng nói người khác | Phải phân loại cấp độ hệ thống thông tin (AA nhiều khả năng ở cấp 1–2) | https://www.rajahtannasia.com/viewpoints/law-on-cybersecurity-comes-into-operation-on-1-july-2026-establishing-a-unified-legal-framework-on-cybersecurity-and-network-information-security-in-vietnam/ |
| NĐ 327–333/2026/NĐ-CP (hướng dẫn Luật ANM) | Luật (NĐ) | Ban hành 19/08/2026. NĐ 333 quy định lưu trữ dữ liệu trong nước và hiện diện tại VN, thay NĐ 53/2022, bỏ "dữ liệu quan hệ người dùng", và liệt kê rõ ứng dụng trực tuyến là dịch vụ thuộc diện | Cần kiểm AA có thuộc "doanh nghiệp cung cấp dịch vụ" phải lưu dữ liệu tại VN khi Bộ Công an yêu cầu hay không | https://english.luatvietnam.vn/decree-no-333-2026-nd-cp-dated-august-19-2026-of-the-government-detailing-a-number-of-articles-and-measures-for-implementation-of-the-law-on-cyberse-445089-doc1.html |
| Luật Dữ liệu 60/2024/QH15 + QĐ 20/2025/QĐ-TTg + NĐ 363/2026 | Luật | Luật hiệu lực 01/07/2025. QĐ 20/2025 (01/07/2025) ban hành danh mục dữ liệu quan trọng và dữ liệu cốt lõi; dữ liệu cốt lõi phải được chấp thuận trước khi chuyển ra nước ngoài. NĐ 363/2026 xử phạt lĩnh vực dữ liệu, hiệu lực 11/11/2026 | Catalog du lịch khó thuộc dữ liệu cốt lõi hay quan trọng. Làm tốt DPIA/TIA theo PDPL là đủ cho phần dữ liệu cá nhân | https://digitalpolicyalert.org/event/31582-prime-minister-issued-decision-no-202025qd-ttg-promulgating-the-list-of-important-data-and-core-data-in-accordance-with-the-law-on-government-organisation-and-the-law-on-data |
| Luật Công nghiệp công nghệ số 71/2025/QH15 | Luật | Thông qua 14/06/2025. Đ.11, 28, 29 hiệu lực 01/07/2025, phần còn lại 01/01/2026. Chương IV (AI) đã bị Luật AI bãi bỏ | Chỉ còn ý nghĩa ưu đãi (doanh nghiệp công nghệ số) | https://english.luatvietnam.vn/law-no-134-2025-qh15-dated-december-10-2025-of-the-national-assembly-on-artificial-intelligence-422299-doc1.html |

### ISO / IEC

| Tên | Loại | Trạng thái & mốc (as of 11/2026) | Ý nghĩa với AA | Nguồn |
|---|---|---|---|---|
| ISO/IEC 42001:2023 (AIMS) | Tiêu chuẩn (chứng nhận được) | Chưa sửa đổi. CEN-CENELEC chấp nhận nguyên văn thành EN ISO/IEC 42001:2026 (13/03/2026, hiệu lực quốc gia 30/09/2026). **Không** mang presumption of conformity theo AI Act | AIMS-lite của AA map vào 42001:2023 + Annex A (38 control) là đúng | https://digitalpolicyalert.org/event/42657-cen-cenelec-adopted-standard-on-management-system-for-artificial-intelligence-en-isoiec-420012026 |
| EN 18286:2026 (AI QMS) | Tiêu chuẩn hài hòa EU | Tiêu chuẩn hài hòa đầu tiên của AI Act, được dẫn chiếu bởi Implementing Decision (EU) 2026/2274 ngày 14/10/2026. Cho presumption of conformity với QMS Art. 17 | Chỉ liên quan nếu AA có hệ thống high-risk ở EU (hiện không) | (theo fact-check lane standards) https://eur-lex.europa.eu/eli/reg/2026/1744/oj |
| ISO/IEC 42005:2025 | Tiêu chuẩn hướng dẫn | Công bố 28/05/2025, không chứng nhận | Mẫu cho AI impact assessment của chat và writer | https://webstore.iec.ch/en/publication/107659 |
| ISO/IEC 42006:2025 | Tiêu chuẩn cho tổ chức chứng nhận (CB) | Công bố 07/2025 (ngày 7/7 chưa xác minh) | Nếu đi chứng nhận, chọn CB được công nhận cho 42001 theo 42006 | https://www.iso.org/standard/42006 |
| ISO/IEC 27001:2022 + Amd 1:2024 | Tiêu chuẩn (chứng nhận được) | Hạn chuyển đổi từ bản 2013 hết 31/10/2025. Amd 1 (02/2024) thêm câu "biến đổi khí hậu có phải vấn đề liên quan" vào mục 4.1, và NOTE 2 ở 4.2 | ISMS-lite đã theo bản này. Thêm một dòng về khí hậu vào tài liệu bối cảnh | https://www.iso.org/standard/88435.html |
| ISO/IEC 27701:2025 | Tiêu chuẩn (chứng nhận được) | Công bố 14/10/2025, đứng độc lập, không còn đòi 27001. Hạn chuyển đổi (khoảng 2028) chưa xác minh | Chứng chỉ quyền riêng tư rẻ hơn cho đại lý. Có control cho cả controller lẫn processor, hợp với AA | https://www.dnv.com/news/2025/iso-iec-27701-standard-update-release/ |
| ISO/IEC 27090:2026 | Tiêu chuẩn hướng dẫn | Ấn bản 1, 10/2026, không chứng nhận. Ngày cụ thể 14/10 và số trang chưa xác minh. ISO 27091 (AI privacy) chưa rõ đã công bố (chưa xác minh) | Danh mục mối đe dọa chuẩn ISO cho red-team hằng tháng của AA | https://www.boutique.afnor.org/en-gb/standard/iso-iec-270902026/cybersecurity-artificial-intelligence-ai-addressing-security-threats-and-co/xs147261/606717 |
| Chứng chỉ ISO/IEC 42001 của AWS | Bằng chứng nhà cung cấp | Schellman (công nhận ANAB), công bố 11/2024, phủ Bedrock, Q Business, Textract, Transcribe. Lần giám sát đầu (11/2025) không có phát hiện. Phạm vi hiện tại xem trong AWS Artifact | Ghi vào danh sách nhà cung cấp của AIMS cho tuyến Bedrock. Không phủ tuyến Anthropic/OpenAI API, và AA không được chứng nhận "ăn theo" | https://aws.amazon.com/compliance/iso-42001-faqs/ |

### NIST (Mỹ)

| Tên | Loại | Trạng thái & mốc | Ý nghĩa với AA | Nguồn |
|---|---|---|---|---|
| AI RMF 1.0 (NIST AI 100-1) | Khung | Vẫn là bản hiện hành. NIST ghi "being revised", chưa có draft. Concept note profile cho hạ tầng trọng yếu ra 07/04/2026 | Ngôn ngữ chung GOVERN/MAP/MEASURE/MANAGE | https://www.nist.gov/itl/ai-risk-management-framework |
| NIST AI 600-1 (GenAI Profile) | Khung | 26/07/2024, vẫn hiện hành. 12 rủi ro GenAI | Checklist cho writer (bịa thông tin tour) và chat | https://www.nist.gov/itl/ai-risk-management-framework |
| NIST IR 8596 (Cyber AI Profile) | Khung (draft) | Chỉ có Initial Preliminary Draft 16/12/2025; góp ý đóng 30/01/2026. 3 trục: Secure / Defend / Thwart | Nhìn gateway AI theo kiểu CSF 2.0 | https://csrc.nist.gov/pubs/ir/8596/iprd |
| COSAiS → COSIS (SP 800-53 overlays) | Khung | Đổi tên ngày 20/10/2026 sau EO 29/09/2026. Tài liệu Mỹ từ nay dùng "Super Intelligence/SI". Overlay cho GenAI và agent chưa có draft công khai. Nguyên văn EO chưa xác minh | Khi ra, đây là danh mục control cụ thể nhất cho gateway và agent | https://csrc.nist.gov/Projects/cosis |

### EU AI Act

| Tên | Loại | Trạng thái & mốc | Ý nghĩa với AA | Nguồn |
|---|---|---|---|---|
| AI Act (Reg. 2024/1689), mốc gốc | Luật | Lệnh cấm và AI literacy từ 02/02/2025; GPAI từ 02/08/2025; phần lớn còn lại, gồm Art. 50 và quyền cưỡng chế GPAI, từ 02/08/2026. Phạt GPAI tới €15m hoặc 3% doanh thu toàn cầu | Art. 2(1): AA vẫn thuộc phạm vi nếu đầu ra AI được dùng ở EU (khách EU dùng chat, đại lý EU đăng nội dung) | https://eur-lex.europa.eu/eli/reg/2024/1689/oj |
| Digital Omnibus on AI, Reg. (EU) 2026/1744 | Luật | Ký 08/07/2026, đăng OJ 24/07/2026, hiệu lực 27/07/2026. Annex III high-risk 02/12/2027; Annex I 02/08/2028; Art. 50(2) cho hệ thống có sẵn tới 02/12/2026; lệnh cấm mới (deepfake khiêu dâm không đồng thuận, CSAM) từ 02/12/2026; sandbox quốc gia trước 02/08/2027; ưu đãi SME mở rộng sang small mid-caps | Mốc high-risk 8/2026 trên slide cũ đã sai. AA không thuộc Annex III | https://eur-lex.europa.eu/eli/reg/2026/1744/oj |
| Art. 4 AI literacy (bản sửa) | Luật | Nay là nghĩa vụ "take measures to support" AI literacy, không đòi mức cụ thể với từng người | Đào tạo ngắn về dùng AI cho staff và đại lý, có lưu hồ sơ, là đủ. Cần sửa câu chữ trong AI policy của AA cho khớp | https://artificialintelligenceact.eu/ai-act-explorer/digital-omnibus/ |
| Art. 50 (minh bạch) + Code of Practice | Luật + bộ quy tắc tự nguyện | Áp dụng từ 02/08/2026. Code of Practice về đánh dấu và gắn nhãn nội dung AI công bố 10/06/2026; Commission và AI Board coi là đủ (08–09/07/2026); Art. 50 Guidelines ra 20/07/2026. Khoảng 190 bên ký (chưa xác minh) | Chat phải báo "bạn đang trò chuyện với trợ lý AI". Nội dung tour viết bằng AI: có dấu máy đọc được, cộng dòng "AI hỗ trợ, AA đã duyệt". Đã người duyệt và chịu trách nhiệm biên tập thì thường thoát 50(4) (cần luật sư xác nhận) | https://digital-strategy.ec.europa.eu/en/news/commission-publishes-code-practice-marking-and-labelling-ai-generated-content |
| GPAI Code of Practice | Bộ quy tắc tự nguyện | Danh sách bên ký (cập nhật 25/11/2026) khoảng 22 tổ chức, gồm Amazon, Anthropic, OpenAI, Google, Mistral, Cohere. Meta không ký; xAI chỉ ký chương Safety & Security | Nhà cung cấp model của AA đều đã ký: một dòng due-diligence nhà cung cấp gần như miễn phí | https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai |

### Khu vực

| Tên | Loại | Trạng thái & mốc | Ý nghĩa với AA | Nguồn |
|---|---|---|---|---|
| Singapore Model AI Governance Framework for Agentic AI | Khung (tự nguyện) | Ra mắt 22/01/2026 (Davos); v1.5 ngày 20/05/2026 (cập nhật 05/06/2026). 4 trục: giới hạn rủi ro từ đầu, con người chịu trách nhiệm thật, control kỹ thuật theo vòng đời, minh bạch với người dùng cuối | Mẫu thực dụng nhất cho CRM AI drafts và agent booking sau này | https://www.imda.gov.sg/assets/d1e45a56-d898-4b9f-972e-8ae94be1a5a5.pdf |
| ASEAN Expanded Guide on AI Governance & Ethics, GenAI | Khung (tự nguyện) | Ra mắt tại ADGMIN, 16–17/01/2025. 6 rủi ro GenAI, 9 khuyến nghị | Ngôn ngữ chung khi làm với đại lý nhiều nước ASEAN | https://asean.org/wp-content/uploads/2025/01/Expanded-ASEAN-Guide-on-AI-Governance-and-Ethics-Generative-AI.pdf |
| Dự thảo Luật AI Thái Lan (ETDA) | Dự thảo luật | Lấy ý kiến từ khoảng 02–09/07/2026 (nguồn lệch nhau) tới 14/08/2026. Dựa trên rủi ro, có hiệu lực ngoài lãnh thổ. Tình trạng sau lấy ý kiến chưa xác minh | Theo dõi nếu phục vụ đại lý hoặc khách Thái | https://www.bakermckenzie.com/en/insight/publications/2026/07/thailand-draft-ai-act--seven-key-implications |
| Malaysia PDP (Amendment) Act 2024 | Luật | Hiệu lực theo đợt: 01/01, 01/04, 01/06/2025. Có DPO, báo vi phạm, quyền mang dữ liệu đi (portability), nghĩa vụ trực tiếp cho processor | Áp lên CRM nếu xử lý dữ liệu đại lý hoặc khách Malaysia | https://insightplus.bakermckenzie.com/bm/data-technology/malaysia-personal-data-protection-amendment-act-2024-to-come-into-force |

---

## 3. Rủi ro AI chính

### OWASP Top 10 for LLM Applications 2025 (bản trước, vẫn được trích nhiều nhất)

| ID | Rủi ro | Chạm AA ở đâu |
|---|---|---|
| LLM01 | Prompt Injection (trực tiếp và gián tiếp) | Writer đọc text nhà cung cấp (gián tiếp); chat trip-planner (trực tiếp); tin nhắn khách vào CRM |
| LLM02 | Sensitive Information Disclosure | CRM drafts (lộ dữ liệu giữa các tenant); chat chứa dữ liệu khách |
| LLM03 | Supply Chain | Model provider, package npm/PyPI, MCP server dùng trong dev |
| LLM04 | Data and Model Poisoning | Nguồn tour sai hoặc bị cài cắm đi thẳng vào nội dung đã xuất bản |
| LLM05 | Improper Output Handling | HTML/Markdown do AI sinh ra hiển thị cho staff và khách (link, ảnh tự render) |
| LLM06 | Excessive Agency | Nếu CRM draft được tự gửi, hoặc chat có tool ghi dữ liệu |
| LLM07 | System Prompt Leakage | Chat công khai. Prompt của AA nằm trong repo public nên vốn không chứa bí mật |
| LLM08 | Vector and Embedding Weaknesses | Embeddings/RAG: truy xuất phải lọc quyền theo từng tenant |
| LLM09 | Misinformation | Writer bịa thông tin tour (giờ, dịch vụ, cảnh quan) |
| LLM10 | Unbounded Consumption | Gateway tính tiền theo token: lạm dụng chat làm đốt chi phí |

**Bản 2026 (04/08/2026), thứ tự mới:** LLM01 Prompt Injection · LLM02 Sensitive Info Disclosure · **LLM03 Excessive Agency** · LLM04 Supply Chain · LLM05 Data & Model Poisoning · LLM06 Unbounded Consumption · LLM07 Misinformation · **LLM08 Hidden Context Exposure** · LLM09 Vector & Embedding · LLM10 Improper Output Handling (thêm ví dụ lộ dữ liệu qua ảnh Markdown tự render, rất sát với chat UI). Đây là bản đầu tiên có trọng số dữ liệu sự cố (75% phiếu chuyên gia, 25% dữ liệu từ 6.639 sự cố phân loại được). Nguồn: https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/README.md · https://cloudsecurityalliance.org/articles/the-owasp-top-10-for-llm-applications-2026-what-changed-and-why-it-matters

### OWASP Top 10 for Agentic Applications (09/12/2025)

ASI01 Agent Goal Hijack · ASI02 Tool Misuse · ASI03 Identity & Privilege Abuse · ASI04 Agentic Supply Chain · ASI05 Unexpected Code Execution · ASI06 Memory & Context Poisoning · ASI07 Insecure Inter-Agent Communication · ASI08 Cascading Failures · ASI09 Human-Agent Trust Exploitation · ASI10 Rogue Agents.
Với AA: ASI01/02 nếu chat có thêm tool. ASI03 cho gateway assume role chéo tài khoản. ASI04/05 cho coding agents và MCP. ASI09 khi staff tin bản nháp AI mà không đọc lại. Nguồn: https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/

**Khung bổ trợ nên biết tên:**
- OWASP AI Testing Guide v1 (26/11/2025): ID kiểu AITG-APP-01 (prompt injection), AITG-APP-02 (indirect injection). https://owasp.org/www-project-ai-testing-guide/
- MITRE ATLAS 2026.10 (28/10/2026): 16 tactics, 129 techniques, 44 mitigations, 77 case studies. Có AML.T0110 (AI Agent Tool Poisoning) và case study MCP AML.CS0053/0054. https://github.com/mitre-atlas/atlas-data/blob/main/CHANGELOG.md
- CSA AI Controls Matrix v1.1: 247 control objectives, 18 domain; phát hành 06/2026, công bố 14/07/2026. Map sang 42001: 59% không có gap, 39% gap một phần, 2% gap toàn phần. https://cloudsecurityalliance.org/blog/2026/07/14/ai-controls-matrix-v1-1-strengthening-the-foundation-for-trustworthy-ai
- Google SAIF 2.0 (06/10/2025): 3 nguyên tắc cho agent: có người điều khiển rõ ràng, quyền bị giới hạn, hành động và kế hoạch quan sát được. https://blog.google/technology/safety-security/ai-security-frontier-strategy-tools/
- MCP spec 2026-07-28: stateless; bỏ dần DCR, thay bằng Client ID Metadata Documents; bắt buộc kiểm `iss`; credentials gắn với authorization server đã cấp. Không token passthrough. https://modelcontextprotocol.io/specification/2026-07-28/changelog
- OWASP AIVSS: v0.8 là tài liệu mới nhất; bản 1.0 chính thức chưa xác minh. https://aivss.owasp.org/

### Sự cố đáng nhớ 2025–2026

- **EchoLeak** (CVE-2025-32711, CVSS 9.3): zero-click indirect injection qua email trong M365 Copilot; công bố 11/06/2025, sửa phía server, không thấy bị khai thác. https://www.securityweek.com/echoleak-ai-attack-enabled-theft-of-sensitive-data-via-microsoft-365-copilot/
- **MCP tool poisoning / rug pull** (Invariant Labs, 01/04/2025): chỉ dẫn ẩn trong mô tả tool, có thể đổi sau khi người dùng đã duyệt. https://invariantlabs.ai/blog/mcp-security-notification
- **GitHub MCP** (26/05/2025): một issue public chiếm quyền agent và làm lộ repo private. https://invariantlabs.ai/blog/mcp-github-vulnerability
- **postmark-mcp** (09/2025): package giả mạo (không phải của Postmark), 15 bản sạch rồi bản v1.0.16 lén BCC mọi email. Được coi là MCP server độc hại đầu tiên ngoài thực tế. https://www.theregister.com/2025/09/29/postmark_mcp_server_code_hijacked/
- **s1ngularity / Nx** (26/08/2025): mã độc gọi Claude Code `--dangerously-skip-permissions`, Gemini `--yolo`, Q `--trust-all-tools` để lục secret trên máy dev. https://socket.dev/blog/nx-packages-compromised
- **Shai-Hulud** (phát hiện 15/09/2025): worm npm tự lây; CISA cảnh báo ngày 23/09/2025 với hơn 500 package. https://threats.wiz.io/all-incidents/shai-hulud-ongoing-package-supply-chain-compromise-delivering-data-stealing-malware
- **Amazon Q Developer VS Code v1.84.0** (CVE-2025-8217, bulletin AWS-2025-015, 23/07/2025): prompt xoá dữ liệu bị cài vào qua GitHub token có quyền quá rộng trong CodeBuild. Bản sửa là v1.85.0. https://aws.amazon.com/security/security-bulletins/AWS-2025-015/
- **Claude Code CVE-2026-21852** (dưới 2.0.65, Moderate, CVSS 4.0 5.3): repo độc đặt `ANTHROPIC_BASE_URL` để lấy API key trước khi hiện trust prompt. Công bố 01/2026, Check Point phân tích 02/2026. https://github.com/advisories/GHSA-jh7p-qr78-84p7
- **Semantic Kernel CVE-2026-25592 / CVE-2026-26030**: từ prompt đến RCE trong framework agent (Microsoft, 07/05/2026). https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
- **GTG-1002** (Anthropic, 13/11/2025): chiến dịch gián điệp dùng Claude Code làm agent, khoảng 30 mục tiêu. Con số "AI làm 80–90% thao tác" là tự đánh giá của Anthropic và bị giới nghiên cứu tranh luận. https://assets.anthropic.com/m/ec212e6566a0d47/original/Disrupting-the-first-reported-AI-orchestrated-cyber-espionage-campaign.pdf
- **Model Namespace Reuse** (Unit 42, 03/09/2025): đăng ký lại tên model đã xoá trên Hugging Face. Rủi ro với AA thấp vì AA không tải weights. https://unit42.paloaltonetworks.com/model-namespace-reuse/

### Lethal trifecta (Simon Willison, 16/06/2025) / Agents Rule of Two (Meta, 31/10/2025)

Ba yếu tố nguy hiểm khi gộp lại: **(1) có dữ liệu riêng + (2) nhận nội dung không tin cậy + (3) giao tiếp được ra ngoài hoặc đổi được trạng thái**. Mỗi phiên agent chỉ nên có tối đa 2/3. Kiểm theo từng bề mặt:
- **Writer:** có (1) và (2), không có (3), vì nội dung được duyệt trước khi đăng. Giữ nguyên như vậy.
- **Chat trip-planner:** input của khách, cộng dữ liệu khách hoặc booking, cộng link/ảnh tự render, là đủ bộ ba. Cần strip hoặc allowlist URL và ảnh trong output.
- **CRM drafts:** dữ liệu tenant, cộng tin nhắn khách gửi vào, cộng nút "gửi", là đủ bộ ba. Bắt buộc người duyệt trước khi gửi (AA đang làm đúng).
- **Coding agents:** secret trong repo, cộng issue/web, cộng mạng, là đủ bộ ba. Hạn chế egress, không chạy cờ skip-permission ngoài sandbox. Repo public nên issue và PR comment luôn là input không tin cậy.

Nguồn: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ · https://ai.meta.com/blog/practical-ai-agent-security/

---

## 4. AWS cho bảo mật GenAI

| Dịch vụ / hướng dẫn | Làm gì | AA đang dùng? | Chi phí / ghi chú | Nguồn |
|---|---|---|---|---|
| Generative AI Security Scoping Matrix | Chia use case GenAI thành 5 scope (1 Consumer app … 3 Pre-trained qua API … 5 Self-trained) | Một phần (AA nằm ở **Scope 3**, chưa chính thức dùng khung này) | Miễn phí | https://aws.amazon.com/ai/generative-ai/security/scoping-matrix/ |
| Agentic AI Security Scoping Matrix | 4 scope (No / Prescribed / Supervised / Full Agency), 6 chiều bảo mật. Ngày ra mắt chưa xác minh (khoảng cuối 2025) | Không. CRM drafts thuộc Scope 2, chat thuộc Scope 1 | Miễn phí | https://aws.amazon.com/ai/security/agentic-ai-scoping-matrix/ |
| Well-Architected Generative AI Lens + Responsible AI Lens | Checklist best practice. Cả hai có ngày công bố 19/11/2025 | Không | Miễn phí (import custom lens vào WA Tool). Responsible AI Lens không phải checklist tuân thủ | https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/responsible-ai-lens.html |
| Bedrock Guardrails (inline / ApplyGuardrail) | Lọc nội dung, prompt attack, denied topics, PII, contextual grounding. ApplyGuardrail kiểm được text của bất kỳ model nào | Một phần: CRM dùng bộ lọc PII ở detect mode | Content $0.15, denied topics $0.15, PII $0.10, grounding $0.10 cho mỗi 1.000 text units (1 unit ≤ 1.000 ký tự). Regex và word filter miễn phí. Hai tier cùng giá | https://aws.amazon.com/bedrock/pricing/ |
| Guardrails Standard tier | Hỗ trợ tiếng Việt "Optimized and supported" (content, prompt attack, denied topics, grounding, PII). Recall prompt attack +30% so với Classic. Classic chỉ có EN/FR/ES | Không rõ tier đang dùng | Cần guardrail cross-region inference (trong cùng geography, không tính thêm phí). Standard cho grounding **không có** ở us-west-1 và Singapore | https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html |
| InvokeGuardrailChecks API (06/2026) | Kiểm từng loại (content, prompt attack, PII) theo từng request, detect-only, không cần tạo guardrail resource | Không | Content $0.07, prompt attack $0.08, PII $0.10 /1.000 text units. Hợp với gateway nhiều provider | https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeGuardrailChecks.html |
| Guardrails enforcement (account-level + org-wide, GA 03/04/2026) | Ép một guardrail lên mọi lời gọi Bedrock trong account hoặc OU. Kết quả là hợp các guardrail, cái chặt nhất thắng | Không | Tính phí guardrail cho mỗi lời gọi bị ép. Chỉ phủ lời gọi Bedrock, không phủ Anthropic/OpenAI API. Có áp lên chính management account hay không: chưa xác minh | https://aws.amazon.com/about-aws/whats-new/2026/04/bedrock-guardrails-cross-account-safeguards/ |
| Automated Reasoning checks (GA 06/08/2025) | Kiểm chứng hình thức câu trả lời theo luật do mình viết ("tới 99%" theo AWS) | Không | $0.17 /1.000 text units cho mỗi policy. Chỉ có ở US East/West-2, EU, Sydney; **không có ở us-west-1** | https://aws.amazon.com/about-aws/whats-new/2025/08/automated-reasoning-checks-amazon-bedrock-guardrails/ |
| Bedrock AgentCore (GA 13/10/2025); Policy GA 03/03/2026; Evaluations GA 31/03/2026 | Runtime, Identity, Gateway (MCP), Memory, Observability. Policy viết bằng Cedar, chặn ở từng tool call | Không | Policy $0.000025/request; Gateway $0.005/1.000 lần gọi; Evaluations $0.0024/$0.012 cho mỗi 1.000 token in/out | https://aws.amazon.com/bedrock/agentcore/pricing/ |
| Model access (auto-enable từ 15/10/2025) | Model serverless tự bật. Anthropic vẫn cần form First Time Use; nộp form ở management account là áp cho cả org | Có | Lỗi "not available for this account … contact AWS Sales" là hạn chế entitlement ở cấp tài khoản: IAM, SCP hay console đều không sửa được, chỉ AWS Support | https://repost.aws/knowledge-center/bedrock-access-denied-exception |
| Cross-Region inference (geographic / global) | Geographic giữ xử lý trong một vùng địa lý. Global rẻ hơn khoảng 10%. Log nằm ở Region nguồn. Trường `inferenceRegion` cho biết request thực sự chạy ở đâu | Có (CRM chỉ dùng profile `us.`) | Lưu dữ liệu phục vụ phát hiện lạm dụng có thể nằm ở Region đích | https://docs.aws.amazon.com/bedrock/latest/userguide/global-cross-region-inference.html |
| In-Region Claude (Singapore) | Claude Sonnet 5 xử lý chỉ trong Singapore (AWS ngày 29/09/2026) | Không | Câu chuyện residency gọn nhất cho dữ liệu khách Đông Nam Á | https://aws.amazon.com/about-aws/whats-new/2026/09/claude-region-expansion-in-sk/ |
| Hanoi Local Zone (GA 19/06/2026) | EC2, S3 One Zone-IA, EBS, ECS, EKS, ALB, Direct Connect | Không | **Không có Bedrock**. VN chưa có Region; chưa thấy kế hoạch (chưa xác minh) | https://aws.amazon.com/about-aws/whats-new/2026/06/aws-local-zones-hanoi-vietnam/ |
| Điều khoản dữ liệu của Bedrock | Không dùng prompt/output để train, không chia sẻ cho model provider. Nằm trong phạm vi SOC 1/2/3, ISO 27001/27017/27018/27701, CSA STAR L2 | Có (dựa vào) | Chỉ áp cho tuyến Bedrock | https://aws.amazon.com/bedrock/faqs/ |
| CloudTrail cho Bedrock | InvokeModel/Converse là management event (mặc định có). ApplyGuardrail, agents, KB Retrieve là data event (phải bật). Model invocation logging là phần riêng, mặc định tắt | Một phần (có trail đa Region; data events chưa rõ) | Ledger của AA cộng CloudTrail là hai lớp bằng chứng audit | https://docs.aws.amazon.com/bedrock/latest/userguide/logging-using-cloudtrail.html |
| GuardDuty AI Protection (14/07/2026) | Phân tích event của Bedrock, SageMaker, AgentCore: lời gọi bất thường, cost harvesting, prompt injection (cần Guardrails) | Không (tạm hoãn vì chi phí) | Khoảng $1/GB CloudTrail data events (ví dụ us-east-1). Trial 30 ngày. Extended Threat Detection cho EC2/ECS miễn phí từ 02/12/2025 | https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-guardduty-ai-protection-aws/ |
| AWS Security Hub bản mới (GA 02/12/2025) | Tương quan tín hiệu GuardDuty, Inspector, CSPM; exposure findings, đường tấn công | Không | Tính theo resource unit (ví dụ $3.75/unit; 1 EC2 = 1 unit, 12 Lambda = 1, 125 IAM role = 1). Trial 30 ngày cho gói Essentials | https://aws.amazon.com/about-aws/whats-new/2025/12/security-hub-near-real-time-risk-analytics/ |
| AWS Continuum for Penetration Testing (trước là Security Agent; GA 31/03/2026) | Pentest tự động bằng AI | Không | $50/task-hour, tính theo giây. Trial 2 tháng (tới 400 task-hour/tháng). Chỉ ở 6 Region (us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-2, ap-northeast-1) | https://aws.amazon.com/about-aws/whats-new/2026/11/continuum-pentest-pause-resume/ |
| AWS Security Incident Response | Hỗ trợ ứng cứu sự cố | Không | Từ 21/11/2025: 10.000 finding/tháng đầu miễn phí | https://aws.amazon.com/about-aws/whats-new/2025/11/security-incident-response-metered-pricing-free-tier/ |
| IAM Access Analyzer | Phát hiện truy cập từ ngoài, quyền không dùng, truy cập nội bộ | Có (external access) | External miễn phí; unused $0.20/role/tháng; internal $9/resource/Region/tháng | https://aws.amazon.com/iam/access-analyzer/pricing/ |
| Amazon Macie | Tìm dữ liệu nhạy cảm trong S3 | Không | $0.10/bucket/tháng + $1/GB quét | https://aws.amazon.com/macie/pricing/ |
| AWS WAF | Rate limit, managed rules trước API | Có | — | (baseline nội bộ) |
| PrivateLink cho Bedrock | Gọi Bedrock không đi Internet; điều kiện `aws:SourceVpce` | Không (chưa) | Mẫu gọi chéo tài khoản cần AWS xác nhận | https://docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html |
| Chứng chỉ ISO 42001 của AWS (AWS Artifact) | Bằng chứng nhà cung cấp | Chưa tải | Miễn phí | https://aws.amazon.com/compliance/iso-42001-faqs/ |

---

## 6. Câu hỏi nên hỏi

### A. AWS solution architects (xếp theo giá trị cho AA)

1. **Khách hàng AWS ở VN đang đưa gì vào hồ sơ đánh giá tác động chuyển dữ liệu ra nước ngoài (TIA) gửi A05 theo PDPL và NĐ 356, khi dữ liệu và inference nằm ở Region US? AWS có mẫu hay case tham chiếu không?**
   *What do Vietnamese AWS customers put in the cross-border transfer impact assessment filed with A05 under the PDPL and Decree 356 when data and inference sit in US Regions? Is there an AWS template or reference case?*

2. **Với dữ liệu cá nhân của khách Việt, AWS khuyên route nào: in-Region Singapore (Sonnet 5), APAC geographic hay global? Có thể khoá bằng SCP mà vẫn dùng được Guardrails Standard tier (vốn cần cross-region) không?**
   *For Vietnamese travellers' personal data, which Bedrock routing do you recommend: in-Region Singapore, APAC geographic or global? Can we lock it with an SCP and still use the Guardrails Standard tier, which needs cross-Region inference?*

3. **Bedrock trả "not available for this account … contact AWS Sales" trong khi API báo AUTHORIZED và case đã đóng. AWS dùng tiêu chí gì cho hạn chế cấp tài khoản này, và đường escalate đúng là gì?**
   *Bedrock returns "not available for this account … contact AWS Sales" while the availability API says AUTHORIZED and the support case is closed. What criteria drive this account-level entitlement restriction, and what is the right escalation path?*

4. **Khi một tài khoản chuyển tổ chức hoặc payer (Billing Transfer), quyền dùng model bên thứ ba trên Bedrock (Anthropic, OpenAI, tính qua Marketplace) và TPM quota có đi theo tài khoản hay theo payer? Cần kiểm gì trước?**
   *When an account moves to another Organization or payer, do third-party Bedrock models billed through Marketplace and their TPM quotas stay with the account or follow the payer? What should we check first?*

5. **Detector PII của Guardrails được version và thông báo thay đổi thế nào? Có cách pin hành vi không? Chúng tôi thấy kết quả với tên người Việt trùng địa danh thay đổi dù phiên bản guardrail giữ nguyên.**
   *How are Guardrails PII detector updates versioned and announced? Can we pin detector behaviour? We saw results change for Vietnamese personal names that are also place names under an unchanged guardrail version.*

6. **Với gateway gọi cả Bedrock lẫn Anthropic/OpenAI API, ApplyGuardrail hay InvokeGuardrailChecks là cách khuyên dùng để có một chính sách chung? Độ trễ với text tiếng Việt là bao nhiêu? Gửi cả lịch sử hội thoại mỗi lượt thì chi phí tăng thế nào?**
   *For a gateway that calls Bedrock and the Anthropic/OpenAI APIs, is ApplyGuardrail or InvokeGuardrailChecks the recommended single-policy pattern? What latency should we expect for Vietnamese text, and how does cost scale if we send the full conversation each turn?*

7. **Bedrock có watermark, C2PA hay provenance metadata sẵn cho Art. 50(2) (hạn 02/12/2026 với hệ thống có sẵn) và cho yêu cầu gắn nhãn của Luật AI VN không, hay phải tự làm ở gateway?**
   *Does Bedrock offer built-in watermarking, C2PA or provenance metadata for EU Art. 50(2) and Vietnam's AI-labelling duty, or must we add it at our gateway?*

8. **Startup nhỏ chạy Fargate, Lambda và Bedrock nên bật GuardDuty plan nào trước? AI Protection cần CloudTrail data events không, đã có ở us-west-1 chưa, và chi phí thực tế mỗi tháng với vài nghìn lời gọi Bedrock một ngày?**
   *For a small Fargate/Lambda/Bedrock footprint, which GuardDuty plans first? Does AI Protection need CloudTrail data events, is it in us-west-1, and what is a realistic monthly cost at a few thousand Bedrock calls a day?*

9. **AWS khuyên mẫu nào cho AI coding agents và MCP tools có quyền AWS (role read-only mặc định, session tags, permission boundary, phiên ngắn)? Sau AWS-2025-015, AWS đã đổi gì trong CI của chính mình?**
   *What pattern do you recommend for AI coding agents and MCP tools with AWS access (read-only default role, session tags, permission boundaries, short sessions)? What did AWS change in its own CI after AWS-2025-015?*

10. **Có tài liệu nào (báo cáo trong Artifact hay điều khoản DPA) mà auditor chấp nhận, ghi rằng prompt trên Bedrock không bị lưu, không dùng để train, không lộ cho model provider? Cross-region inference có làm thay đổi cam kết vị trí dữ liệu không?**
    *Is there an auditor-ready document (Artifact report or DPA clause) stating Bedrock prompts are not stored, not used for training and not visible to model providers? Does cross-Region inference change any data-location commitment?*

### B. G-AsiaPacific (partner)

11. **Khách hàng của anh chị ở VN đã có ai tự khai báo hệ thống AI rủi ro trung bình trên ai.dda.gov.vn theo NĐ 142 chưa? Mất bao lâu, và cơ quan đang xếp chatbot hay nội dung do LLM sinh ra vào mức nào?**
   *Have any of your Vietnamese customers self-declared a medium-risk AI system on ai.dda.gov.vn under Decree 142? How long did it take, and which tier are regulators applying to chatbots and LLM-generated content?*

12. **Partner có thể hỗ trợ escalate case quyền model hoặc quota Bedrock không? Có chương trình nào có tài trợ (GenAI security assessment, Well-Architected GenAI Lens review, credit) cho startup giai đoạn pilot, và giá bao nhiêu?**
   *Can you help escalate Bedrock model-access or quota cases? Are there funded programmes (GenAI security assessment, Well-Architected GenAI Lens review, credits) for pilot-stage startups, and at what price?*

13. **Ở VN, CB nào được công nhận để chứng nhận ISO/IEC 42001 (theo 42006)? Chi phí và thời gian cho audit 42001 + 27001 kết hợp với đội dưới 10 người, phạm vi hẹp (gateway AI + 1 app)?**
   *Which accredited CBs certify ISO/IEC 42001 in Vietnam under 42006? Typical cost and duration for a combined 42001 + 27001 audit for a team under 10, narrow scope?*

14. **Partner có đối tác pháp lý hay tư vấn tuân thủ cho PDPL, Luật AI và NĐ 333 (lưu trữ dữ liệu tại VN) không?**
   *Do you have legal or compliance partners for the PDPL, the AI Law and Decree 333 on data localisation?*

### C. Diễn giả / peers

15. **Theo NĐ 356, làm processor cho đại lý trong một SaaS CRM có bị tính là "cung cấp dịch vụ xử lý dữ liệu" và mất miễn trừ startup không? Các anh chị nộp TIA trước khi chuyển dữ liệu hay trong 60 ngày sau?**
   *Under Decree 356, does acting as processor for agencies in a SaaS CRM count as a "data processing service" that removes the startup exemption? Do you file the TIA before transfers start or within 60 days after?*

16. **Ai đang dùng Anthropic hay OpenAI API trực tiếp làm dự phòng cho Bedrock? Các anh chị xử lý DPA, zero retention và việc ghi tuyến này vào TIA thế nào?**
   *Who uses the Anthropic or OpenAI API directly as a fallback to Bedrock, and how do you cover DPA, zero retention and listing that path in the TIA?*

17. **Với chat công khai có tool read-only, các anh chị cắt chân "exfiltration" của lethal trifecta (link, ảnh tự render) thế nào mà vẫn hiện được bản đồ và link booking? Đo hiệu quả control ra sao?**
   *For a public chat with read-only tools, how do you cut the exfiltration leg of the lethal trifecta (auto-rendered links and images) while still showing maps and booking links? How do you measure that it works?*

18. **Promptfoo đang được OpenAI mua lại. Mọi người đang dùng gì để red-team liên tục cho app Claude/GPT trên Bedrock (garak, PyRIT, RAMPART, Bedrock Evaluations), và hiệu chỉnh LLM-as-judge thế nào?**
   *With Promptfoo being acquired by OpenAI, what do you use for continuous red-teaming of Claude/GPT apps on Bedrock (garak, PyRIT, RAMPART, Bedrock Evaluations), and how do you calibrate LLM-as-judge?*

---

## 8. Giới thiệu 30 giây

**Tiếng Việt**
> Em là Nghiệp, tech lead ở Adventure Asia, một startup travel-tech tại Việt Nam. Bọn em xây một nền tảng trên AWS gồm bốn ứng dụng: sinh nội dung tour bằng LLM, trip planner có trợ lý AI cho khách, back office booking và CRM cho đại lý có bản nháp AI. Mọi lời gọi AI đi qua một AI gateway duy nhất, route Claude và GPT qua Amazon Bedrock và API của nhà cung cấp, có ngân sách, nhật ký từng lời gọi và scrub dữ liệu cá nhân. Con người luôn duyệt trước khi nội dung được đăng hay gửi đi. Bọn em vận hành theo hướng ISO 27001/42001 (chưa chứng nhận) và red-team AI hằng tháng. Hôm nay em muốn học cách các bên làm governance AI ở quy mô lớn, đặc biệt về dữ liệu xuyên biên giới và Luật AI mới của Việt Nam.

**English**
> I'm Nghiep, tech lead at Adventure Asia, a Vietnamese travel-tech startup. We run a platform on AWS with four apps: LLM-generated tour content, a trip planner with an AI assistant for travellers, a booking back office, and an agency CRM with AI drafts. Every AI call goes through one AI gateway that routes Claude and GPT via Amazon Bedrock and the vendor APIs, with budgets, per-call logging and personal-data scrubbing. A human always approves before anything is published or sent. We follow an ISO 27001/42001-aligned approach (not certified yet) and red-team our AI monthly. I'm here to learn how others run AI governance at scale, especially cross-border data and Vietnam's new AI law.

---

## 9. Thuật ngữ nhanh

- **AIMS**: AI Management System, hệ thống quản lý AI theo ISO/IEC 42001.
- **ISMS**: hệ thống quản lý an toàn thông tin theo ISO/IEC 27001.
- **SoA (Statement of Applicability)**: bảng tuyên bố control nào áp dụng và trạng thái của từng control.
- **DPIA**: đánh giá tác động xử lý dữ liệu cá nhân (PDPL Đ.21).
- **TIA / CTIA**: đánh giá tác động chuyển dữ liệu cá nhân ra nước ngoài (PDPL Đ.20), nộp A05.
- **A05**: Cục An ninh mạng và phòng chống tội phạm công nghệ cao, Bộ Công an; cơ quan nhận hồ sơ và thông báo vi phạm.
- **Prompt injection (trực tiếp / gián tiếp)**: chèn lệnh vào input. Kiểu gián tiếp đi qua tài liệu, email, web mà model đọc vào.
- **Lethal trifecta**: dữ liệu riêng + nội dung không tin cậy + kênh gửi ra ngoài; có đủ cả ba thì có thể bị rút dữ liệu.
- **Excessive Agency**: AI có quá nhiều quyền hoặc tool để tự hành động.
- **Hidden Context Exposure**: tên mới (OWASP 2026) của System Prompt Leakage, phạm vi rộng hơn: mọi ngữ cảnh ẩn bị lộ.
- **Guardrails**: lớp lọc input/output độc lập với model (Bedrock Guardrails).
- **ApplyGuardrail / InvokeGuardrailChecks**: API kiểm text bằng guardrail mà không cần gọi model trên Bedrock.
- **Cross-Region inference (geographic / global)**: Bedrock định tuyến request sang Region khác trong cùng vùng địa lý (geographic) hoặc toàn cầu (global).
- **Cost harvesting / denial-of-wallet**: lạm dụng credential hoặc endpoint để đốt tiền token.
- **MCP**: Model Context Protocol, giao thức nối agent với tool và dữ liệu.
- **Tool poisoning / rug pull**: mô tả tool chứa lệnh ẩn, hoặc tool đổi thành độc hại sau khi đã được duyệt.
- **AI-BOM / ML-BOM**: danh mục model, dataset và route AI (CycloneDX 1.7 = ECMA-424 bản 2, 12/2025).
- **C2PA / Content Credentials**: chuẩn gắn nguồn gốc nội dung bằng chữ ký. Bản 2.3 (05/01/2026) hỗ trợ cả văn bản thuần.
- **GPAI**: general-purpose AI model. Nghĩa vụ GPAI rơi vào Anthropic, OpenAI…, không rơi vào AA.
- **Presumption of conformity**: tuân thủ một tiêu chuẩn hài hòa thì được suy định là tuân thủ luật (EU). EN 18286 có, ISO 42001 không có.

---

## 10. Nguồn

**Việt Nam**
- https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Law-91-2025-QH15-Personal-Data-Protection-665440.aspx
- https://english.luatvietnam.vn/legal-updates/the-latest-law-on-personal-data-protection-and-the-guiding-documents-892-106778-article.html
- https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/legal-alert-march-2026-decree-no-356-2025-nd-cp-providing-detailed-guidance-for-implementation-of-personal-data-protection-law
- https://www.vietnam-briefing.com/news/vietnam-personal-data-protection-regulation-decree-356.html
- https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/legal-alert-decree-330-2026-nd-cp-providing-sanctions-for-personal-data-protection-law-violations
- https://english.luatvietnam.vn/decree-no-330-2026-nd-cp-dated-august-19-2026-of-the-government-on-sanctioning-of-administrative-violations-in-the-fields-of-cybersecurity-and-perso-445214-doc1.html
- https://www.allenandgledhill.com/perspectives/publications/bulletins-vietnam/2026/vietnam-s-new-law-on-artificial-intelligence-risk-based-regulatory-framework-in-force-1-march-2026/
- https://english.luatvietnam.vn/law-no-134-2025-qh15-dated-december-10-2025-of-the-national-assembly-on-artificial-intelligence-422299-doc1.html
- https://www.legal500.com/intelligence/vietnam/technology/vietnam-takes-major-step-in-ai-governance-with-new-guiding-decree
- https://lsvn.vn/chinh-thuc-van-hanh-cong-thong-tin-mot-cua-ve-tri-tue-nhan-tao-a178433.html
- https://www.rajahtannasia.com/viewpoints/law-on-cybersecurity-comes-into-operation-on-1-july-2026-establishing-a-unified-legal-framework-on-cybersecurity-and-network-information-security-in-vietnam/
- https://english.luatvietnam.vn/decree-no-333-2026-nd-cp-dated-august-19-2026-of-the-government-detailing-a-number-of-articles-and-measures-for-implementation-of-the-law-on-cyberse-445089-doc1.html
- https://kpmg.com/vn/en/insights/2024/12/vietnam-enacts-its-first-ever-data-law.html
- https://digitalpolicyalert.org/event/31582-prime-minister-issued-decision-no-202025qd-ttg-promulgating-the-list-of-important-data-and-core-data-in-accordance-with-the-law-on-government-organisation-and-the-law-on-data

**ISO / NIST**
- https://digitalpolicyalert.org/event/42657-cen-cenelec-adopted-standard-on-management-system-for-artificial-intelligence-en-isoiec-420012026
- https://webstore.iec.ch/en/publication/107659
- https://www.iso.org/standard/42006
- https://www.iso.org/standard/88435.html
- https://www.dnv.com/news/2025/iso-iec-27701-standard-update-release/
- https://www.boutique.afnor.org/en-gb/standard/iso-iec-270902026/cybersecurity-artificial-intelligence-ai-addressing-security-threats-and-co/xs147261/606717
- https://aws.amazon.com/compliance/iso-42001-faqs/
- https://aws.amazon.com/blogs/machine-learning/aws-achieves-iso-iec-420012023-artificial-intelligence-management-system-accredited-certification
- https://aws.amazon.com/blogs/security/aws-successfully-completed-its-first-surveillance-audit-for-iso-420012023-with-no-findings
- https://www.nist.gov/itl/ai-risk-management-framework
- https://csrc.nist.gov/pubs/ir/8596/iprd
- https://csrc.nist.gov/Projects/cosis

**EU**
- https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- https://eur-lex.europa.eu/eli/reg/2026/1744/oj
- https://artificialintelligenceact.eu/ai-act-explorer/digital-omnibus/
- https://digital-strategy.ec.europa.eu/en/news/commission-publishes-code-practice-marking-and-labelling-ai-generated-content
- https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content
- https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai
- https://cooley.com/news/insight/2026/2026-08-03-eu-ai-act-transparency-obligations-take-effect-2-august-2026

**Khu vực**
- https://www.mddi.gov.sg/newsroom/singapore-launches-new-model-ai-governance-framework-for-agentic-ai--/
- https://www.imda.gov.sg/assets/d1e45a56-d898-4b9f-972e-8ae94be1a5a5.pdf
- https://asean.org/wp-content/uploads/2025/01/Expanded-ASEAN-Guide-on-AI-Governance-and-Ethics-Generative-AI.pdf
- https://www.bakermckenzie.com/en/insight/publications/2026/07/thailand-draft-ai-act--seven-key-implications
- https://insightplus.bakermckenzie.com/bm/data-technology/malaysia-personal-data-protection-amendment-act-2024-to-come-into-force

**Mối đe dọa & khung**
- https://genai.owasp.org/llm-top-10/
- https://raw.githubusercontent.com/GenAI-Security-Project/GenAI-LLM-Top10/main/README.md
- https://cloudsecurityalliance.org/articles/the-owasp-top-10-for-llm-applications-2026-what-changed-and-why-it-matters
- https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/
- https://owasp.org/www-project-ai-testing-guide/
- https://aivss.owasp.org/
- https://github.com/mitre-atlas/atlas-data/blob/main/CHANGELOG.md
- https://cloudsecurityalliance.org/blog/2026/07/14/ai-controls-matrix-v1-1-strengthening-the-foundation-for-trustworthy-ai
- https://blog.google/technology/safety-security/ai-security-frontier-strategy-tools/
- https://modelcontextprotocol.io/specification/2026-07-28/changelog
- https://invariantlabs.ai/blog/mcp-security-notification
- https://invariantlabs.ai/blog/mcp-github-vulnerability
- https://www.theregister.com/2025/09/29/postmark_mcp_server_code_hijacked/
- https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- https://ai.meta.com/blog/practical-ai-agent-security/
- https://www.securityweek.com/echoleak-ai-attack-enabled-theft-of-sensitive-data-via-microsoft-365-copilot/
- https://socket.dev/blog/nx-packages-compromised
- https://threats.wiz.io/all-incidents/shai-hulud-ongoing-package-supply-chain-compromise-delivering-data-stealing-malware
- https://aws.amazon.com/security/security-bulletins/AWS-2025-015/
- https://github.com/advisories/GHSA-jh7p-qr78-84p7
- https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files/
- https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
- https://assets.anthropic.com/m/ec212e6566a0d47/original/Disrupting-the-first-reported-AI-orchestrated-cyber-espionage-campaign.pdf
- https://unit42.paloaltonetworks.com/model-namespace-reuse/
- https://openai.com/index/openai-to-acquire-promptfoo/
- https://github.com/NVIDIA/garak/releases
- https://ecma-international.org/publications-and-standards/standards/ecma-424/

**AWS**
- https://aws.amazon.com/ai/generative-ai/security/scoping-matrix/
- https://aws.amazon.com/ai/security/agentic-ai-scoping-matrix/
- https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/responsible-ai-lens.html
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html
- https://aws.amazon.com/bedrock/pricing/
- https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-tiers.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.html
- https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeGuardrailChecks.html
- https://aws.amazon.com/about-aws/whats-new/2026/04/bedrock-guardrails-cross-account-safeguards/
- https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-enforcements.html
- https://aws.amazon.com/about-aws/whats-new/2025/08/automated-reasoning-checks-amazon-bedrock-guardrails/
- https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-agentcore-available/
- https://aws.amazon.com/bedrock/agentcore/pricing/
- https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-automatic-enablement-serverless-foundation-models/
- https://repost.aws/knowledge-center/bedrock-access-denied-exception
- https://docs.aws.amazon.com/bedrock/latest/userguide/global-cross-region-inference.html
- https://aws.amazon.com/about-aws/whats-new/2026/09/claude-region-expansion-in-sk/
- https://aws.amazon.com/about-aws/whats-new/2026/06/aws-local-zones-hanoi-vietnam/
- https://aws.amazon.com/bedrock/faqs/
- https://docs.aws.amazon.com/bedrock/latest/userguide/logging-using-cloudtrail.html
- https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-guardduty-ai-protection-aws/
- https://aws.amazon.com/about-aws/whats-new/2025/12/security-hub-near-real-time-risk-analytics/
- https://aws.amazon.com/about-aws/whats-new/2026/03/aws-security-agent-ondemand-penetration/
- https://aws.amazon.com/about-aws/whats-new/2026/11/continuum-pentest-pause-resume/
- https://aws.amazon.com/about-aws/whats-new/2025/11/security-incident-response-metered-pricing-free-tier/
- https://aws.amazon.com/iam/access-analyzer/pricing/
- https://aws.amazon.com/macie/pricing/
- https://docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html
- https://aws.amazon.com/about-aws/whats-new/2025/11/billing-transfer-multi-organization-billing-cost-management/
