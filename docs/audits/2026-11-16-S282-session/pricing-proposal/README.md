# Đề xuất giá gói cho đại lý: Content, CRM, TripPlanner

*16/11/2026 (S282). Viết cho tech lead và chủ doanh nghiệp. Chỉ đọc repo, tài liệu và web công khai; không gọi AWS hay LLM, không đọc DB live.*

**Cách đọc số liệu**
- **[Dev]**: số đo trên môi trường Dev (chạy thử, chưa có khách thật), chỉ để thấy xu hướng.
- **[giả định]**: số mình tự đặt để tính. Đổi giả định thì bảng margin đổi theo (công thức ở mục 2.4).
- **[aggregator]**: giá đối thủ lấy từ trang tổng hợp (Capterra, review…), không phải trang giá của hãng. Có thể đã cũ.
- **[chưa kiểm được]**: không mở được nguồn gốc, hoặc nguồn không còn ghi con số đó (phản biện 16/11).
- Mọi giá **chưa gồm thuế** (ADR 0019 b17). Tỉ giá quy đổi **1 USD ≈ 26.000 đ** [giả định; chưa đối chiếu tỉ giá Vietcombank ngày 16/11]; giá VND làm tròn xuống thành giá đẹp (thường "…90.000"), **không bao giờ cao hơn** giá USD × 26.000.

---

## 1. Tóm tắt

1. **Hiện trạng.** Bảng `shared.plan` (CIS migration 355) đã có giá cho Content: Starter 299, Growth 799, Business 1.499 USD/tháng (ADR 0019 b2). **CRM Core/Pro và TripPlanner Hosted/Pro còn `NULL`.** Đây là số seed của migration, chưa kiểm DB live xem Plans API đã đổi chưa.
2. **Chi phí nền mỗi đại lý** khi có khoảng 10 đại lý: **~97 USD/tháng** (Starter), **~134** (Growth), **~198** (Business). Khi có 30 đại lý: ~50 / ~87 / ~151. Phần lớn là chi phí hạ tầng chia đều; AI tốn tối đa bằng trần AI của gói (15 / 40 / 80 USD) vì gateway tự chặn ở trần.
3. **AI thật tháng 10 [Dev]:** 36,92 USD cho 4 tenant có dùng, trung bình ~9 USD, cao nhất 14,82 USD. Đều dưới trần gói Growth (40 USD).
4. **Thị trường.** CRM ngành du lịch tính **19–59 USD/tháng** (TravelJoy Starter 19 cho một tài khoản, không AI; Tern 35–49/người; Travefy 39–59 cho người đầu, +20–39/người thêm). CRM chung rẻ hơn nhiều: HubSpot Starter 20, Odoo 9–20, CRM Việt Nam **55.000–175.000 đ/người** (2–7 USD). Công cụ lịch trình hoặc portal: **75–399 USD/tháng** (Wetu, Safari Portal 299–399 (199 giá hỗ trợ), Tourwriter 99–149/người).
5. **Giá Content hiện tại (299 / 799 / 1.499) hợp với đại lý Úc, Âu, Mỹ, nhưng cao với đại lý Việt Nam và Đông Nam Á.** Gói 799 USD bằng khoảng 20,8 triệu đồng/tháng, ngang hoặc hơn lương tháng của một nhân viên văn phòng ở Việt Nam.
6. **Ba phương án:**
   - **A (rẻ, vào nhanh):** Content 79 / 199 / 399 USD, CRM 12 USD/người. Gói Starter **lỗ** khi dưới ~13 đại lý.
   - **B (cân bằng):** Content 149 / 349 / 699 USD, CRM 19 USD/người, TripPlanner 49 / 99 USD. Margin gộp **35–72 %** khi có 10 đại lý, **66–78 %** khi có 30.
   - **C (cao cấp):** giữ 299 / 799 / 1.499 USD, CRM 29 USD/người, TripPlanner 99 / 199 USD. Margin trên 68 %, nhưng ít đại lý Việt Nam mua nổi.
7. **Khuyến nghị: phương án B làm bảng giá chung (USD và VND).** Giá C dùng làm mốc cho Enterprise và đại lý nước ngoài lớn.
   - Dùng thử 14 ngày khi gắn add-on (đã chốt).
   - Trả năm thì được 2 tháng miễn phí.
   - "Đại lý sáng lập": giảm 30 % trong 12 tháng đầu cho 10 đại lý đầu tiên.
   - Pilot trên Dev miễn phí cho tới ngày go-live.

---

## 2. Chi phí nền

### 2.1 Chi phí cố định của cả hệ thống (không phụ thuộc số đại lý)

| Khoản | USD/tháng | Nguồn |
|---|---:|---|
| AWS Dev (acc2), tháng 10 | 213,87 | `docs/audits/2026-11-03-S265-capacity-review/README.md` |
| Mức chạy đủ tháng: tốc độ cuối tháng 10 khoảng 7–8 USD/ngày (đã gồm CRM và Booking, nên **không cộng thêm** phần CRM/Booking lần nữa) → 210–240; cộng TripPlanner trên ECS Spot + CloudFront + WAF (~15–17, chưa chạy trong tháng 10); trừ ~10 nhờ cắt bớt cảnh báo CloudWatch từ 01/11 | **Dev ~230–260**, bảng dùng **260** (bảo thủ) | Cùng file (dòng budget acc2: "late-October rate ≈ 7–8 USD/day"; cột "≈ full month"); ADR 0019 d23 (TripPlanner + 2 app staff ~20–22 USD) |
| Prod (`aa-prod`, khi có ngày go-live), đã tính tiết kiệm | 280–410 (+0–110 dịch vụ bảo mật) → **~350** | `docs/audits/2026-11-03-S265-ecosystem-restructure/clarifications.md` §5 |
| AI chạy nền không gắn tenant (bảo trì catalogue, đánh giá chất lượng) | **~80** [giả định, chưa có tháng "sạch" nào để đo]. Tháng 10 là 229,45 (345.982 lượt gọi), có hai đợt viết lại cả catalogue (sự kiện một lần). Phần Claude trên Bedrock trả bằng thẻ, credit Lift không trả | FI-08 tháng 10; `S265-capacity-review` |
| **Tổng cố định F** | **~700** (khoảng 550–900) | |

**F không gồm lương đội sản phẩm.** Margin gộp ở các bảng dưới là phần còn lại để trả lương và lãi. F cũng gánh cả Booking và pipeline catalogue của chính AA (không bán cho đại lý), nên chia hết F cho đại lý là cách tính bảo thủ.

### 2.2 Chi phí biến đổi theo từng đại lý

| Khoản | Số dùng để tính | Nguồn / lý do |
|---|---|---|
| AI của Content | **Bằng trần AI của gói** (trường hợp xấu nhất): 15 / 40 / 80 USD | `ai.budget_usd_monthly` trong migration 355 (b19). Gateway dừng ở 100 % ("approval 100 %, stop" trong FI-08); chỉ vượt được khi staff duyệt tay hoặc đặt override ở Tenant 360 |
| AI thật hôm nay [Dev] | ~9 USD/tenant/tháng (36,92 / 4); cao nhất 14,82 | Báo cáo FI-08 tháng 10 (`docs/audits/2026-11-15-S281-session/verify/aa1003/FI-08.md`) |
| Đơn giá AI (tham khảo khi đặt hạn mức) | Một lần viết lại tour (T2) ≈ **0,078 USD**; một bài blog ≈ **0,137 USD**; một blog được duyệt ≈ 0,55 USD; một lượt chat TripPlanner **~0,011 USD** đo được (0,067 USD / 6 lượt), 0,025 là trần dự chi đã duyệt cho smoke (0,2 USD / 8 lượt) | AA-741 phase 3 (`docs/audits/2026-11-10-S276-aa741-phase3/`, T2 p50 0,0782; blog 0,1367; blog duyệt 0,5467); log phiên S277 (ledger 0,067 USD) + `docs/audits/2026-11-11-S277-tp-chat-smoke/` |
| AI của TripPlanner | **Trừ vào trần AI của tenant** (ADR 0019, sửa đổi S272). Vì vậy add-on TripPlanner nên **cộng thêm** vào trần: +10 USD (Hosted), +25 USD (Pro) | `catalog.v_tenant_ai_budget_v1` (CIS 390) |
| Hạ tầng riêng của CRM | ~25 USD/tháng chia cho số đại lý dùng CRM (giả định 5) → ~5 USD; AI soạn nháp ~1 USD/người | S265 capacity review (CRM ≈ 25/tháng) [giả định cho AI] |
| Hạ tầng riêng của TripPlanner | ~20 USD/tháng chia cho 5 site → ~4 USD | ADR 0019 d23 |
| Tên miền riêng | Hạ tầng **~0 USD** (ACM và CNAME trên CloudFront miễn phí); khoảng 1 giờ cài đặt một lần + kiểm định kỳ → **~3 USD/tháng** | `docs/audits/2026-11-15-S281-tp-custom-domain/` |
| Hỗ trợ khách hàng | **8 USD/giờ** đã tính đủ chi phí [giả định: lương CSKH nói tiếng Anh ~18–20 triệu đồng × 1,5 = 27–30 triệu ≈ 1.040–1.150 USD / ~160 giờ ≈ 6,5–7,2 USD/giờ; 8 là có dư cho giờ không làm việc trực tiếp với khách. Lương CSKH phổ thông ở Việt Nam thấp hơn, nên đây là số bảo thủ]. Content: 1,5 / 3 / 6 giờ mỗi tháng (gói Business được chăm sóc kỹ, b13); CRM +1 giờ; TripPlanner +0,5–1 giờ; công onboarding chia đều vào 12 tháng | [giả định] |

### 2.3 Chi phí nền mỗi đại lý (Content), tính bằng USD/tháng

| Gói | AI (trần) | Hỗ trợ | Phần cố định, 10 đại lý | **Tổng, 10 đại lý** | Phần cố định, 30 đại lý | **Tổng, 30 đại lý** |
|---|---:|---:|---:|---:|---:|---:|
| Starter | 15 | 12 | 70 | **97** | 23 | **50** |
| Growth | 40 | 24 | 70 | **134** | 23 | **87** |
| Business | 80 | 48 | 70 | **198** | 23 | **151** |

Add-on, mỗi đại lý mỗi tháng:
- **CRM Core**, 3 người dùng: ~16 USD. Mỗi người thêm: ~1,5 USD. **CRM Pro**: ~19 USD (thêm ~3 USD cho tên miền riêng của portal; WhatsApp/SMS và Stripe do đại lý tự mang tài khoản nên không tính).
- **TripPlanner Hosted:** ~18 USD (đã gồm +10 USD AI).
- **TripPlanner Pro:** ~40 USD (đã gồm +25 USD AI và tên miền).
- **Tên miền riêng** (mua lẻ): ~3 USD.

**Một đợt dùng thử 14 ngày** tốn tối đa khoảng nửa trần AI của gói cộng 1,5–2 giờ hỗ trợ, tức **~32–36 USD với gói Growth** (20 + 12–16). Con số này chỉ đúng khi đã đặt override 50 % trần; không có override thì AI tối đa là cả trần 40 USD → ~52–56 USD (xem mục 4, chính sách dùng thử).

### 2.4 Công thức

- Chi phí nền = trần AI + giờ hỗ trợ × 8 + F / N, với N là số đại lý.
- Margin gộp = (giá − chi phí nền) / giá.

---

## 3. So sánh thị trường

| Sản phẩm | Loại | Giá công bố (USD, chưa thuế) | Dùng thử | Nguồn |
|---|---|---|---|---|
| Travefy | CRM + lịch trình cho đại lý | Core 39/tháng người đầu (trả năm), +20/người thêm; Premium 59, +39/người; gói Agency liên hệ sales; New Travel Agent 25/tháng; tên miền riêng có sẵn trong Premium (Core chỉ nối tên miền tự có) | 10 ngày | <https://travefy.com/pricing> (trang hãng, phản biện mở lại 16/11: khớp) |
| TravelJoy | CRM cho travel advisor | Giá theo tài khoản, không theo người: Starter 19/tháng (không AI, không thành viên nhóm, 12 chuyến/năm); Pro 39/tháng (32 nếu trả năm), có AI; thành viên nhóm là add-on chưa công bố giá; Premium không công bố giá | 7 ngày, không cần thẻ | <https://traveljoy.com/pricing> (trang hãng, phản biện mở lại 16/11: khớp) |
| Tern | CRM + lịch trình | 49/người/tháng trả tháng, 35 nếu trả quý hoặc năm; giá tự đổi theo bậc số người (3–24, 25–99…) nhưng trang không ghi số từng bậc; Tern Pro (thêm AI) là add-on không ghi giá. Mức "25–33/người cho 3–24 người" và "Tern Pro từ 19" của bản trước [chưa kiểm được] nên đã bỏ | Có dùng thử, trang không ghi số ngày | <https://tern.travel/pricing> (trang hãng, phản biện mở được 16/11) |
| Tourwriter | Lịch trình + báo giá cho tour operator | Starter 99/người/tháng; Pro 149/người (2–5 người), trả năm; Premium liên hệ; **phí setup từ 1.199** | Có demo | <https://www.tourwriter.com/software-pricing-plans/> (trang hãng, đọc 16/11) |
| Safari Portal | Portal lịch trình | Essentials 299/tháng (1 người, +50/người thêm); Pro 399 (3 người, +50/người); Enterprise liên hệ; giá hỗ trợ 199 cho advisor mới hoặc thuộc host agency; trả năm được 1 tháng miễn phí. Trang hãng **không nhắc tên miền riêng** (bản trước ghi "tên miền riêng ở gói 399": [chưa kiểm được]) | — | <https://www.safariportal.app/pricing> (trang hãng, phản biện mở 16/11; G2 chặn bot) |
| Wetu | Lịch trình + nội dung điểm đến | Lite 75/người (+35/người thêm); Premium 150 (+65); Enterprise ~395/tháng cho 5 người | 14 ngày, không cần thẻ | <https://www.capterra.com/p/149603/Wetu> [aggregator; Capterra chặn bot, các trang tổng hợp khác (fitgap, itechguides) khớp; trang hãng chưa mở được] |
| WeTravel | Thanh toán + đặt chỗ cho tour operator | Basic 0; Pro 79/tháng mỗi tổ chức; Enterprise liên hệ; phí xử lý thanh toán tuỳ phương thức (mức "từ 1 % + 0,30" [chưa kiểm được]) | — | <https://product.wetravel.com/pricing> (trang hãng, phản biện mở 16/11) |
| TripCreator | Trip planner white-label | Bản trước: Standard 59/người/tháng (trả năm) hoặc 69; Pro 99 [chưa kiểm được: Capterra chặn bot; trang hãng ghi giá **theo tài khoản doanh nghiệp, không theo người**, bảng giá tải bằng script nên không đọc được số] | — | <https://www.tripcreator.com/pricing> |
| mTrip | App/planner white-label | **Không công bố giá** ("no public rate card"), báo giá sau demo theo số lịch trình; Trip Agent trả tháng, white-label hợp đồng 1 năm + phí setup. Mức "79–350" của bản trước đã bỏ | — | <https://www.mtrip.com/en/pricing/> (trang hãng, phản biện mở 16/11) |
| Tourplan | Back office cho DMC (để tham khảo) | Không công bố, báo giá theo dự án | — | <https://www.capterra.com/p/2489/Tourplan-iS/> |
| Lemax | Back office cho DMC (để tham khảo) | Khoảng 10.000/năm (≈ 830/tháng) [aggregator, chưa kiểm được: phản biện không mở lại] | Có | <https://www.g2.com/products/lemax/pricing>, <https://www.softwareadvice.com/hotel-management/lemax-profile/> [aggregator] |
| HubSpot Starter | CRM chung | 20/người/tháng (giá thường); khuyến mãi khách mới 7 (trả năm) / 10 (trả tháng); Free cho 2 người | — | <https://www.hubspot.com/pricing/crm> (trang hãng, phản biện mở lại 16/11: khớp) |
| Odoo | ERP/CRM chung | Standard 8,95–11,20; Custom 16,40–20,40 /người/tháng (số thấp có thể là giá giảm 12 tháng đầu); một app miễn phí | — | <https://www.odoo.com/pricing> (trang hãng, giá cho người xem ở Mỹ; phản biện mở lại 16/11: khớp) |
| MISA AMIS CRM (Việt Nam) | CRM chung | Từ 55.000 đ/người/tháng; mua tối thiểu 1 năm, gói từ 10 người: 6,6 / 10,2 / 12,6 / 14,4 triệu đồng/năm | — | <https://amis.misa.vn/13038/2-cach-tinh-gia-phan-mem-crm-pho-bien-nhat/> (phản biện mở lại 16/11: khớp; bài có thể cũ) |
| Getfly (Việt Nam) | CRM chung | 78.000–175.000 đ/người/tháng; gói 3 người ~521.000 đ/tháng | — | Cùng bài MISA ở trên (là đối thủ của Getfly nên cần đọc thận trọng) |
| Jasper | Viết nội dung bằng AI (chung) | Pro 69/người/tháng, hoặc 59 nếu trả năm | 7 ngày | <https://www.jasper.ai/pricing> (trang hãng, phản biện mở 16/11: khớp) |
| Copy.ai | Viết nội dung bằng AI (chung) | Chat 29/tháng, hoặc **24** nếu trả năm (bản trước ghi 23), **tối đa 5 người** (giá theo gói, không theo người); gói Growth từ 1.000/tháng | Trang giá không còn nhắc gói miễn phí | <https://www.copy.ai/prices> (trang hãng, phản biện mở 16/11) |

**Rút ra từ bảng:**
- **CRM:**
  - Các sản phẩm riêng cho ngành du lịch có ba cách tính. Một là theo từng người, 35–49 USD (Tern). Hai là "người đầu + người thêm" (Travefy 39 + 20). Ba là theo tài khoản (TravelJoy 19–39, thành viên nhóm tính thêm).
  - CRM chung và CRM Việt Nam rẻ hơn 3–10 lần.
  - Vì vậy CRM của AA phải bán bằng những phần chỉ ngành du lịch mới có: proposal, departure, portal cho khách đi tour, tour AA có sẵn, lead đổ về từ TripPlanner. Đừng so CRM của AA với CRM chung.
- **Content:**
  - Chưa thấy sản phẩm nào cùng loại: viết lại tour có sẵn theo thương hiệu của đại lý rồi đăng thẳng lên WordPress và Facebook.
  - Công cụ AI chung chỉ 24–69 USD (Copy.ai tính cho cả nhóm tối đa 5 người, Jasper theo người), nhưng đại lý phải tự viết từ đầu.
  - Portal lịch trình (Safari Portal, Wetu) ở mức 75–399 USD. Đây là khoảng tham chiếu hợp lý cho Content.
- **TripPlanner:** trip planner white-label hiếm khi công bố giá. mTrip ghi rõ không có bảng giá công khai; TripCreator không đọc được số. **Chưa có mốc giá TripPlanner nào kiểm được trên trang hãng**; mốc gần nhất là WeTravel Pro 79 (mảng khác: thanh toán/đặt chỗ) và Safari Portal 299–399 (portal lịch trình).
- **Thời gian dùng thử:** 7–14 ngày là chuẩn chung. 14 ngày như đã chốt là hợp lý.

---

## 4. Đề xuất 3 phương án giá

Phần chung cho cả ba phương án:
- Tên gói giữ đúng enum hiện có: Starter / Growth / Business; Enterprise là "liên hệ sales".
- Giá nhập qua Plans API là dữ liệu, đổi giá không cần sửa code (ADR 0019 d2: app chỉ kiểm feature key).
- Margin tính theo chi phí nền ở mục 2.3, với 10 và 30 đại lý.

### Phương án A: rẻ để vào nhanh

Dành cho đại lý nhỏ ở Việt Nam và Đông Nam Á, mục tiêu có nhiều đại lý dùng sớm.

| Mục | USD/tháng | VND/tháng | Gồm những gì | Chi phí nền (10 / 30 đại lý) | Margin gộp (10 / 30) |
|---|---:|---:|---|---:|---:|
| Content Starter | 79 | 1.990.000 | 30 lượt viết lại tour, AI 10 USD, blog + social, WordPress/Facebook | 92 / 45 | **−16 %** / 43 % |
| Content Growth | 199 | 4.990.000 | 120 lượt viết lại, AI 25 USD, API | 119 / 72 | 40 % / 64 % |
| Content Business | 399 | 9.990.000 | 300 lượt viết lại, AI 50 USD, chăm sóc riêng | 168 / 121 | 58 % / 70 % |
| CRM (một gói) | 12 / người, tối thiểu 3 | 290.000 / người | Toàn bộ CRM Core | 3 người: 16 | 56 % (người thêm: 88 %) |
| TripPlanner Hosted | 29 | 750.000 | Trang `/{slug}/plan`, launcher, +5 USD AI | 13 | 55 % |
| TripPlanner Pro | 59 | 1.490.000 | Gồm tên miền riêng, embed, API, +15 USD AI | 30 | 49 % |
| Tên miền riêng (lẻ) | 9 | 190.000 | Cho TripPlanner Hosted hoặc portal CRM | 3 | 67 % |

- Ưu điểm: dễ chốt, CRM chỉ đắt hơn CRM Việt Nam khoảng 2 lần.
- Nhược điểm:
  - Starter lỗ cho tới khi có khoảng 13 đại lý (79 = 22 + 700/N → N ≈ 12,3).
  - Sau này tăng giá rất khó.
  - Trần AI thấp nên viết được ít bài.
  - Cần khoảng **12 đại lý** dùng combo Growth + CRM + TripPlanner thì mới bù được F cộng một suất lương 1.500 USD [giả định].

### Phương án B: cân bằng (khuyến nghị)

| Mục | USD/tháng | VND/tháng | Gồm những gì | Chi phí nền (10 / 30 đại lý) | Margin gộp (10 / 30) |
|---|---:|---:|---|---:|---:|
| Content Starter | 149 | 3.790.000 | 50 lượt viết lại tour, AI 15 USD, blog + social, WordPress/Facebook, Book with AA | 97 / 50 | 35 % / 66 % |
| Content Growth | 349 | 8.990.000 | 200 lượt viết lại, AI 40 USD, API 20.000 lượt gọi | 134 / 87 | 62 % / 75 % |
| Content Business | 699 | 17.990.000 | 500 lượt viết lại, AI 80 USD, chăm sóc riêng, SLA 99,5 %, phản hồi trong 4 giờ (b18) | 198 / 151 | 72 % / 78 % |
| Content Enterprise | Liên hệ, sàn 699 | — | Theo hợp đồng; tuỳ chọn lưu dữ liệu ở EU có tính phí (b11) | — | — |
| CRM Core | 19 / người, tối thiểu 3 | 490.000 / người | Pipeline, khách hàng, proposal, hoá đơn, NCC, departure, portal cho khách, AI soạn nháp, tìm kiếm | 3 người: 16 | 72 % (người thêm: 92 %) |
| CRM Pro | 29 / người, tối thiểu 3 | 750.000 / người | Core + campaigns, WhatsApp/SMS, Stripe Connect, xuất insights, portal CRM trên tên miền riêng | 3 người: 19 | 78 % |
| TripPlanner Hosted | 49 | 1.250.000 | `/{slug}/plan`, launcher, lead đổ vào CRM, +10 USD AI | 18 | 63 % |
| TripPlanner Pro | 99 | 2.490.000 | Hosted + tên miền riêng + embed + API, +25 USD AI | 40 | 60 % |
| Tên miền riêng (lẻ) | 15 | 390.000 | Cho Hosted hoặc portal CRM Core; cài đặt miễn phí | 3 | 80 % |
| Gói AI thêm | 19 cho +10 USD AI | 490.000 | Mua khi chạm trần; xuất hoá đơn tay, không tự động trừ tiền (b19) | 10 | 47 % |

- **Combo hay mua:** Growth + CRM Core 3 người + TripPlanner Hosted = 455 USD (~11,8 triệu đồng).
  - Đề xuất giảm 10 % khi mua cả ba sản phẩm: **409 USD / 10.490.000 đ**.
  - Phần đóng góp sau chi phí biến đổi (khoảng 98 USD) còn khoảng 310 USD mỗi đại lý.
  - Khoảng **3 đại lý** là bù được F; khoảng **7–8 đại lý** thì bù được F cộng một suất lương 1.500 USD [giả định].
- **So với thị trường:**
  - CRM 19 USD/người thấp hơn Tern (35–49/người) và Travefy (39–59 người đầu, +20–39/người thêm), dưới khoảng 25–35 USD ví dụ trong b3 ("rẻ hơn đối thủ chính"). TravelJoy Starter cũng 19 nhưng cho cả tài khoản, không AI, không thành viên nhóm, nên không so thẳng được.
  - Content Starter 149 USD thấp hơn Safari Portal (299–399; 199 giá hỗ trợ) và ngang Wetu Premium (150/người, aggregator).
- **Ưu điểm:** margin dương ngay khi có 10 đại lý; giá còn chỗ để khuyến mãi; khớp các mức AI đã chốt ở b19 (15 / 40 / 80).
- **Nhược điểm:** CRM 490.000 đ/người vẫn đắt gấp 3–9 lần CRM Việt Nam. Phải bán bằng tính năng ngành du lịch và lead từ TripPlanner.

### Phương án C: cao cấp

Giữ đúng số trong ADR 0019 b2 và chốt giá cho add-on.

| Mục | USD/tháng | VND/tháng | Gồm những gì | Chi phí nền (10 / 30 đại lý) | Margin gộp (10 / 30) |
|---|---:|---:|---|---:|---:|
| Content Starter | 299 | 7.690.000 | Như seed 355: 50 lượt viết lại, AI 15 USD | 97 / 50 | 68 % / 83 % |
| Content Growth | 799 | 20.490.000 | 200 lượt viết lại, AI 40 USD | 134 / 87 | 83 % / 89 % |
| Content Business | 1.499 | 38.490.000 | 500 lượt viết lại, AI 80 USD, chăm sóc riêng | 198 / 151 | 87 % / 90 % |
| CRM Core | 29 / người, tối thiểu 3 | 750.000 / người | Như ở B | 16 | 82 % |
| CRM Pro | 39 / người, tối thiểu 3 | 990.000 / người | Như ở B | 19 | 84 % |
| TripPlanner Hosted | 99 | 2.490.000 | Như ở B | 18 | 82 % |
| TripPlanner Pro | 199 | 4.990.000 | Như ở B | 40 | 80 % |
| Tên miền riêng (lẻ) | 25 | 650.000 | | 3 | 88 % |

- Ưu điểm: margin cao; ngang Safari Portal (299–399) và Tourwriter (99–149/người, cộng setup từ 1.199); hợp với đại lý Úc, Âu, Mỹ.
- Nhược điểm:
  - Gói Growth 20,5 triệu đồng/tháng nằm ngoài tầm của hầu hết đại lý Việt Nam.
  - Vòng bán dài; cần case study trước khi bán được.
  - Nếu chỉ có 1–3 đại lý thì F (700 USD) vẫn chiếm phần lớn doanh thu.

### Chính sách chung, áp cho phương án được chọn

| Chính sách | Đề xuất | Ghi chú |
|---|---|---|
| Dùng thử khi gắn add-on | **14 ngày** (tech lead đã chốt); Content cũng 14 ngày (b2) | Trong thời gian thử, đặt trần AI bằng **50 % trần của gói** qua override ở Tenant 360. Resolver hiện tính quyền lợi trong thời gian thử theo đúng gói (migration 361), nên muốn trần thấp hơn thì phải đặt override (**cần kiểm** xem override có tự hết khi hết hạn thử không). Không đặt override thì một đợt thử Growth tốn tới ~52–56 USD, không phải ~35 |
| Trả theo năm | **Trả 10 tháng, dùng 12 tháng** (giảm ~17 %) | Đỡ việc xuất hoá đơn tay (b14) và phí chuyển tiền quốc tế. Với B: Starter còn margin ~22 % khi có 10 đại lý |
| Pilot trên Dev | **0 đ** cho tới ngày go-live (d16: không SLA, tối đa 8 tuần) | Không thu tiền khi hệ thống chưa có SLA |
| Ưu đãi ra mắt "đại lý sáng lập" | **Giảm 30 % trong 12 tháng** cho 10 đại lý đầu tiên, áp cho Growth, Business và add-on; **Starter không giảm** | Với B: Growth giảm 30 % còn 244 USD so với chi phí 134 → margin 45 %. Đổi lại đại lý góp ý hằng tháng và đồng ý làm khách tham chiếu (có văn bản đồng ý) |
| Vượt trần AI | Giữ cách dừng mềm (b19). Bán **gói AI thêm** hoặc gợi ý lên gói | Không tự động thu tiền phần vượt cho tới khi có Stripe (b14) |
| Tiền tệ | USD cho đại lý nước ngoài; VND cho đại lý Việt Nam theo bảng giá VND cố định, xem lại mỗi quý | Thông tư 32 và VAT phần mềm: kế toán xác nhận (b17) |
| Ghế CRM | Tính theo người dùng đang hoạt động, tối thiểu 3. Seed hiện có `seats_included = 10` cho `crm.core` và `crm.pro`, cần đổi thành 3 nếu chọn B hoặc C | Đổi dữ liệu qua Plans API |

---

## 5. Khuyến nghị

1. **Chọn phương án B làm bảng giá công khai, bằng USD và VND.** Đổi giá Content từ 299 / 799 / 1.499 xuống 149 / 349 / 699. Nhập giá CRM (19 / 29 USD mỗi người, tối thiểu 3) và TripPlanner (49 / 99 USD) vào `shared.plan`. Giữ trần AI 15 / 40 / 80 USD.
2. **Giá C dùng làm mốc cho Enterprise** và cho đại lý lớn ở Úc, Âu, Mỹ. Sàn Enterprise là 699 USD; thực tế nên chào từ khoảng 1.500 USD khi có SLA cao hoặc lưu dữ liệu ở EU.
3. **Không chọn A làm bảng giá chung.** Chỉ dùng cách của A (giảm sâu) cho một hai đại lý chiến lược, ghi trong hợp đồng có ngày hết hạn.
4. **Ra mắt:**
   - pilot miễn phí trên Dev;
   - tới go-live: giảm 30 % trong 12 tháng cho 10 đại lý đầu tiên;
   - thử 14 ngày khi gắn add-on;
   - trả năm thì 2 tháng miễn phí;
   - combo cả ba sản phẩm giảm 10 %.
5. **Xem lại sau 3 đại lý trả tiền** (như b2 đã ghi), dùng FI-08 và FI-09 thật: AI mỗi tenant so với trần và margin theo từng gói. Nếu AI trung bình vẫn dưới 30 % giá gói (mục tiêu của K-LLM-TENANT) và tỉ lệ chốt thấp, cân nhắc hạ Starter. Nếu chốt dễ, nâng dần lên phía C.
6. **Việc kỹ thuật kèm theo** (nhỏ, chỉ là dữ liệu):
   - giá và `seats_included` trên `shared.plan`;
   - `tp.ai_sessions` cho TripPlanner (đề xuất Hosted 300, Pro 1.500 phiên mỗi tháng);
   - trần AI cộng thêm khi gắn TripPlanner;
   - override trần AI trong thời gian thử.
   Tất cả qua Plans API, không cần migration nếu API đã hỗ trợ (**cần kiểm**).

---

## 6. Rủi ro và giả định

| # | Rủi ro / giả định | Ảnh hưởng | Cách giảm |
|---|---|---|---|
| 1 | Số AI và hạ tầng là số Dev [Dev]; tháng 10 có đợt viết lại cả catalogue | Chi phí cố định F có thể sai ±30 % | Tính lại theo hoá đơn tháng 11 (đọc từ 01/12) và tháng đầu chạy prod |
| 2 | F (~700 USD) gồm cả prod. Prod chưa tạo, đang chờ ngày go-live (b18) | Trước go-live, F chỉ khoảng 340 USD nên margin cao hơn bảng | — |
| 3 | Lương đội sản phẩm không nằm trong chi phí nền | Margin gộp cao vẫn có thể lỗ ròng khi có ít đại lý | Theo dõi điểm hoà vốn: B cần khoảng 7–8 đại lý dùng combo cho F cộng một suất lương |
| 4 | Tổng trần AI của mọi tenant có thể vượt ngân sách của các nhà cung cấp AI (Anthropic API trần 150 USD/tháng; Bedrock trên acc1 trả bằng thẻ, credit Lift không trả cho Claude) | 4 đại lý Growth đã đủ 160 USD trần AI | Mỗi khi thêm đại lý, nâng ngân sách connection theo tổng trần; theo dõi K-TEN-AICAP |
| 5 | Đơn giá AI của TripPlanner lấy từ một lần smoke test (≤ 0,025 USD/lượt) | Phiên chat dài thì tốn hơn | Có trần `tp.ai_sessions` và AI cộng thêm theo add-on; đo lại sau pilot |
| 6 | Chi phí bản đồ (Mapbox) khi lượng truy cập lớn chưa tính | TripPlanner Pro có nhiều lượt xem thì tốn thêm | Kiểm giá Mapbox trước go-live (đang chờ quyết định trong plan.json) |
| 7 | Giờ hỗ trợ 8 USD và số giờ mỗi gói là giả định | Business chăm sóc kỹ có thể tốn gấp đôi | Ghi lại giờ hỗ trợ theo từng tenant ngay từ pilot |
| 8 | Tỉ giá 26.000 đ/USD là giả định | Bảng giá VND lệch dần | Giá VND cố định, xem lại mỗi quý; hợp đồng nước ngoài để USD |
| 9 | Thuế: VAT dịch vụ phần mềm, thuế nhà thầu ở nước của đại lý, Thông tư 32 | Giá thực nhận giảm | Kế toán và luật sư xác nhận trước khi có đại lý trả tiền đầu tiên (b10, b17) |
| 10 | Giá đối thủ: phản biện 16/11 đã mở lại trang hãng của Travefy, TravelJoy, Tern, Tourwriter, Safari Portal, WeTravel, HubSpot, Odoo, Jasper, Copy.ai, mTrip. Còn [aggregator] / [chưa kiểm được]: Wetu, TripCreator, Lemax, phí giao dịch WeTravel | Safari Portal đã đổi bậc giá so với aggregator; các mốc còn lại có thể cũ | Kiểm lại Wetu và TripCreator (demo hoặc hỏi sales) trước khi chốt |
| 11 | Xuất hoá đơn tay, chưa có Stripe (b14); phí chuyển tiền quốc tế 15–30 USD mỗi lần | Gói rẻ trả theo tháng tốn công | Khuyến khích trả năm hoặc theo quý; hỏi lại câu Stripe khi khối lượng tăng |
| 12 | Giá seed 299 / 799 / 1.499 trên Dev chưa được kiểm live | Bảng `shared.plan` có thể đã khác seed | Đọc Plans API hoặc trang admin trước khi đổi |
| 13 | Đại lý đã dùng thử ở giá B thì khó nâng lên giá C sau này | Mất phần doanh thu ở đại lý lớn | Ghi rõ "giá ra mắt, xem lại sau 12 tháng"; khách cũ được giữ giá cũ một năm |

**File đã đọc:**
- `/home/nghiep/projects/AA-Ecosys/docs/adr/0019-b2b-only-ecosystem-model.md` (b2–b4, b14, b15, b18, b19)
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/api/migrations/355_tenant_plans_seed_and_entitlement_view.sql`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/api/migrations/361_tenant_entitlement_trial_grace.sql`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-15-S281-session/verify/aa1003/FI-08.md`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-03-S265-capacity-review/README.md`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-03-S265-ecosystem-restructure/` (README, clarifications, decisions.json)
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-10-S276-aa741-phase3/`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-15-S281-tp-custom-domain/`
- `/home/nghiep/projects/AA-Ecosys/docs/architecture/ai-gateway.md`
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-12-S278-pricing-advice/README.md` (giá tour B2B, không phải giá gói phần mềm)

---

## Ghi chú phản biện (16/11/2026)

Một lượt phản biện độc lập đã đối chiếu từng số với nguồn trong repo (migration 355/361/390, FI-08, S265 capacity review và clarifications, ADR 0019, AA-741 phase 3, S277 TP chat smoke, S281 tên miền riêng) và mở lại trang giá của đối thủ. Kết luận chung: **phương án B vẫn là khuyến nghị**; số học margin ở mục 2.3 và mục 4 khớp (sai lệch ≤ 1 điểm do làm tròn). Đã sửa:

1. **Dev ~260 bị cộng trùng.** Mức chạy cuối tháng 10 (7–8 USD/ngày) đã gồm CRM và Booking; cộng thêm phần CRM/Booking là tính hai lần. Sửa thành Dev ~230–260, bảng vẫn dùng 260 (bảo thủ), nên F ~700 không đổi.
2. **Chat TripPlanner:** 0,025 USD/lượt là trần dự chi đã duyệt, không phải số đo. Số đo là ~0,011 USD/lượt (0,067 / 6, log phiên S277).
3. **Dùng thử 14 ngày, gói Growth:** 25–35 → **32–36 USD** khi có override 50 % trần; **52–56 USD** nếu quên override (resolver 361 cấp đủ trần của gói trong thời gian thử).
4. **Điểm hoà vốn của Starter ở phương án A:** ~15 → **~13 đại lý** (79 = 22 + 700/N).
5. **CRM Pro:** chi phí 16 → 19 USD (thêm tên miền riêng cho portal); margin B 82 → 78 %, C 86 → 84 %.
6. **Giá VND:** TripPlanner Hosted B 1.290.000 đ cao hơn 49 × 26.000 = 1.274.000 đ (trái với quy tắc làm tròn xuống), sửa thành 1.250.000 đ. Quy tắc làm tròn ghi lại là "giá đẹp, không vượt giá quy đổi" (vài dòng dùng 17.990.000 / 9.990.000 thay vì "…90.000" sát hơn; không sai hướng).
7. **Câu "799 USD = một năm lương sau vài tháng"** khó hiểu, viết lại: ~20,8 triệu đ/tháng, ngang hoặc hơn lương tháng một nhân viên văn phòng.
8. **Đối thủ:**
   - Safari Portal đã đổi giá: Essentials **299** (1 người), Pro **399** (3 người), 199 chỉ là giá hỗ trợ; trang hãng không nhắc tên miền riêng.
   - Tern: mở được trang hãng (49 trả tháng, 35 trả quý/năm). Bỏ "25–33/người" và "Tern Pro từ 19" vì không kiểm được.
   - TravelJoy tính theo tài khoản, không theo người, nên khoảng "CRM ngành du lịch" đổi thành 19–59 USD và câu so sánh CRM 19 USD được viết lại.
   - mTrip không công bố giá. Bỏ mốc "79–350" và câu "TripPlanner công khai 59–350 USD". Chưa có mốc giá TripPlanner nào kiểm được.
   - TripCreator tính theo tài khoản doanh nghiệp, không đọc được số → [chưa kiểm được].
   - Copy.ai: trả năm 24 (không phải 23), và giá cho cả nhóm tối đa 5 người.
   - Đã kiểm lại trang hãng và thấy khớp: Travefy, Tourwriter, WeTravel Pro 79, HubSpot, Odoo, Jasper, MISA/Getfly (bài của MISA).
   - Còn [aggregator] / [chưa kiểm được]: Wetu, Lemax, phí giao dịch WeTravel.
9. **Hỗ trợ 8 USD/giờ:** lương 27–30 triệu đ (sau hệ số 1,5) tương đương ~6,5–7,2 USD/giờ, nên 8 là bảo thủ. Mức 18–20 triệu cao hơn lương CSKH phổ thông ở Việt Nam, vẫn là giả định.
10. **Trần AI không tuyệt đối:** FI-08 ghi "approval 100 %, stop", nên staff duyệt tay hoặc override thì vẫn vượt được. Câu "không vượt được" đã sửa.
11. **F chia hết cho đại lý là bảo thủ:** F gánh cả Booking và pipeline catalogue của AA.

**Điểm cần chủ doanh nghiệp cân nhắc (không sửa số, chỉ nêu):**

- **Đại lý nhỏ ở Việt Nam:** B Starter + CRM Core 3 người ≈ 3,79 + 1,47 = **5,26 triệu đ/tháng**. Riêng CRM 3 người (1,47 triệu) đã gần gấp 3 Getfly 3 người (0,52 triệu); MISA 10 người ≈ 0,55–1,2 triệu/tháng. Tổng 5,26 triệu chỉ hợp lý khi Content thay được một phần công viết bài, khoảng 8–12 triệu đ/tháng [giả định].
- **Ưu đãi "đại lý sáng lập"** đang không áp cho Starter, trong khi đại lý Việt Nam nhỏ nhiều khả năng chọn Starter. Có thể cho đại lý sáng lập ở Việt Nam dùng Starter trả năm (≈ 124 USD/tháng, margin ~22 % khi có 10 đại lý), thay vì giảm 30 % làm Starter lỗ.
- **Không có mốc giá TripPlanner kiểm được.** Mức 49 / 99 USD của B là giá tự đặt theo chi phí (margin 60–63 %), chưa có mốc thị trường để dựa vào.
