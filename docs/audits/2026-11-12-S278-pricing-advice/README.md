# Tư vấn giá tour B2B và "phiên bản giá" cho AA-1091

*12/11/2026, viết cho tech lead. Nguồn: 4 nhánh research, đọc code AA-Booking (HEAD 69c4ffb, bk-048) và một vòng critic.*

**Cách đọc số liệu.** Số có ghi **[ví dụ]** lấy từ blog của hãng phần mềm (dmcquote, phptravels, Softrip, Peakflo…). Chỉ dùng để hình dung, không phải chuẩn ngành; số thật phải lấy theo hợp đồng NCC của mình. Số có ghi **[snippet]** chỉ thấy qua kết quả tìm kiếm, chưa mở được trang gốc.

---

## 1. Tóm tắt (10 dòng)

1. Ngành bán cho đại lý bằng giá **NET**: không hoa hồng, bảo mật, tính bằng USD; đại lý tự cộng lời. Mình đang đúng hướng này (ADR 0019, RRP = net + 25% chỉ là giá gợi ý).
2. Giá bắt đầu từ **hợp đồng NCC theo năm**. Mỗi NCC có năm hợp đồng riêng (theo năm dương lịch, 11–10 hoặc 4–3). Đông Nam Á không có một "năm giá" chung.
3. **Mùa** là các khoảng ngày nằm trong hợp đồng, có thể lặp lại; ở qua ranh mùa thì tính giá từng đêm. Có thêm các khoản lễ bắt buộc: gala 24/25 và 31/12, phụ thu Tết.
4. Không phần mềm ngành nào sửa đè giá. Mỗi thay đổi tạo bản mới, có ngày hiệu lực và lịch sử ai đổi.
5. Báo giá và booking ghim giá tại lúc tạo. **Booking đã xác nhận không đổi giá**, trừ phụ thu nhiên liệu, thuế hoặc tỉ giá khi điều khoản cho phép, báo trước ≥ 20 ngày, có cách tính, và khi chi phí giảm thì cũng trả lại cho đại lý.
6. Hệ thống mình đã có nhiều mảnh đúng: hợp đồng NCC khoá khi publish; quy tắc, tỉ giá, hạng đại lý và thẻ giá có người thứ hai duyệt; lịch sử ma trận giá; báo giá có `price_hash`.
7. Lỗ hổng lớn nhất nằm ở **giá nhập tay** (`PUT …/prices`), đúng chỗ CSKH sẽ dùng: không cần duyệt, không bắt ghi lý do, có hiệu lực ngay.
8. Còn thiếu thêm: lịch mùa có cấu trúc (hiện "peak" được nhận ra bằng cách dò chữ, và báo giá B2B chạy với `peak = false`); bảng giá đại lý chưa có phiên bản; không xem trước tác động trước khi duyệt; chưa có xuất Excel.
9. Đề xuất: tạo một thực thể **"phiên bản bảng giá"** cho mỗi tour và kỳ, đi qua các trạng thái nháp → chờ duyệt → phát hành → bị thay. Mỗi bản có lý do, bảng so sánh với bản trước và phần tác động. Báo giá và bảng giá đại lý ghim theo id phiên bản.
10. Trước khi code, chủ doanh nghiệp cần chốt khoảng 12 chính sách (năm bảng giá, hạn báo giá, đổi giá sau xác nhận, cọc và huỷ mùa cao, đoàn, hạng đại lý…). Mục 7 có sẵn đáp án gợi ý cho từng câu.

---

## 2. Ngành làm giá tour B2B thế nào

### 2.1 Hợp đồng NCC theo năm
- **Hai loại giá khách sạn tồn tại song song.**
  - Giá tĩnh theo hợp đồng ("FIT / seasonal net"), ký trước 6–12 tháng và không đổi trong suốt hợp đồng ([Duetto](https://www.duettocloud.com/en-us/library/dynamic-wholesale-rates-new-frontier-hotel-distribution)).
  - Giá động bám theo giá công khai hằng ngày, gọi là BAR ([Hotelbeds](https://hotelhelpcentre.hotelbeds.com/inventory/portalpartner)).
- **Mỗi NCC một năm hợp đồng.**
  - Asian Trails Thái: đi 1/4–31/10/2025 ([link](https://www.asiantrails.travel/?p=1043033)).
  - WebBeds Bali: 01/04/26–31/03/27 ([link](https://apac-marketing.webbeds.com/current-hotel-deals)).
  - Chatrium: hiệu lực đến 31/10/2026, chặn bán 20/12/2025–5/1/2026 ([link](https://lacolkhaoyai.chatrium.com/2025-11-11-End-of-Year-EN/index.html)).
  - Một khách sạn Hà Nội để giá 2026 là *"provisional rollover from 2025 contract"* ([link](https://vietnambookingcenter.com/hotel/acoustic-hotel-spa)).
  - → Năm hợp đồng là thuộc tính của từng hợp đồng. Trạng thái "tạm dùng giá năm cũ" là chuyện bình thường. Mô hình hiện tại của mình (`valid_from`/`valid_to` trên mỗi hợp đồng) đã đúng.
- **Rủi ro khi giữ giá tĩnh.** Khi thị trường yếu, giá công khai có thể xuống thấp hơn giá net mình đã ký ([dmcquote](https://dmcquote.com/blog/post/dynamic-static-hotel-pricing-what-agents-should-know), [ví dụ]). Với công ty tour, cách thực tế là gắn cờ "NCC giá động → định giá tay trên báo giá" như [Tourwriter](https://learn.tourwriter.com/portal/en/kb/articles/how-should-i-manage-dynamic-priced-suppliers), không cần làm feed BAR.
- **Rủi ro NCC xé hợp đồng.** Năm 2012, khách sạn ở Yangon phát hành lại hợp đồng giữa kỳ, có nơi tăng tới 300% ([TravelMole](https://travelmole.com/news/myanmar-hotels-accused-of-tearing-up-contracts)). → Nên đàm phán hợp đồng 12 tháng giá cố định, không có điều khoản "NCC được tự tăng giá".

### 2.2 Mùa
- Mùa là các khoảng ngày, không cần liền nhau và có thể lặp lại, ví dụ mùa cao xuất hiện 2 lần trong năm ([Travelbooster](https://www.assets.travelbooster.com/Help/Contracts.htm), [Tourpaq](https://manual.tourpaq.com/hotel-contracts/periods-hotel-contract-configuration)).
- **Bảng giá mẫu [ví dụ]** ([dmcquote](https://dmcquote.com/blog/post/hotel-b2b-rate-sheet-format-how-to-read)):
  - hiệu lực 1/11–31/10, Peak 20/12–10/1;
  - ở tối thiểu 3 đêm trong Peak, 5 đêm nếu kỳ ở có 31/12;
  - chặn bán 28/12–2/1: lúc đó allotment không dùng được, mọi yêu cầu đều phải hỏi lại NCC.
- **Ở qua ranh mùa thì tính từng đêm.** TourPlan còn hiện cảnh báo "Service rate crosses season" ([link](https://goway.freshdesk.com/support/solutions/articles/44002538566-how-to-load-and-update-product-setup)). Một số khách sạn lại tính cả kỳ theo mùa của ngày đến, nên đây phải là một cờ trên từng hợp đồng, mặc định là tính từng đêm.
- **Bẫy ngày cuối.** Ví dụ của Lemax: nhập nguyên văn hai khoảng 7.10–15.11 và 16.11–24.12 theo quy ước "ngày cuối không tính" thì đêm 15.11 và 24.12 không có giá ([Lemax](https://support.lemax.net/price-list-schedules)).
- **Lễ bắt buộc.**
  - **Gala 24/25 và 31/12** bị thu dù khách không dự, không trả tại chỗ được, DMC xuất hoá đơn trước ([Asian Trails](https://www.asiantrails.travel/destinations/vietnam-terms-and-conditions/)). Giá thật: Sukhothai Bangkok NYE 6.900++ THB/người, 2025 ([link](https://bangkok.sukhothai.com/file/webpage/shared/20251126-tsb-festive-booklet.pdf)); Athenée 16.500 THB net/người, 2024 ([link](https://assetworldcorp-th.com/en/newsroom/news-activities/859/awc-affiliated-hotels-festive-season-promotion-2024)).
  - **Tết:** giá tour cao hơn năm trước 5–15% ([Vietnam News](https://bizhub.vietnamnews.vn/rising-tet-travel-prices-fail-to-dampen-spending-on-experiences-post398569.html)); Amara Tours phụ thu 15% cho 20/1–5/2/2025 ([link](https://amaratours.vn/en/vung-tau-2-days-tour.html)).
  - **Songkran** lên xuống theo cầu: +33% năm này, −2,3% năm khác ([SiteMinder](https://www.siteminder.com/news/songkran-thailand-hotel-room-rates/)); năm 2026 khách sạn Thái giảm 20–40% ([TTG Asia](https://www.ttgasia.com/?p=116548)).
  - → Tết và Lebaran đổi ngày mỗi năm. Không được viết cứng ngày vào code.

### 2.3 Giá net và hoa hồng
- Asian Trails và Destination Asia ghi rõ: *"All rates quoted are nett and non-commissionable"*, giá bảo mật, tính bằng USD. Đại lý không được hiển thị giá hay bán online, trừ khi đã đóng gói cùng dịch vụ khác ([Asian Trails](https://www.asiantrails.travel/?p=1025009), [Destination Asia](https://onlinebooking.destination-asia.com/DNN_DA_LIVE/Terms)).
- Hotelbeds hợp tác với RateGain để săn giá net bị rò ra kênh bán lẻ, và loại khỏi hệ thống những đại lý vi phạm nhiều lần ([Travolution](https://travolution.com/articles/113527/hotelbeds-and-rategain-join-forces-to-hunt-down-opaque-rates-in-consumer-channels)).
- Mô hình hoa hồng (Gross = Net + hoa hồng; chuỗi ITO 30% / wholesaler 20% / đại lý lẻ 10%, theo [Tourism Australia](https://www.tourism.australia.com/en/resources/industry-resources/trade-show-tips/the-travel-distribution-system.html)) dành cho NCC bán qua đại lý bán lẻ. **Mình không cần xây phần hoa hồng.** Giữ RRP làm số gợi ý, và ghi điều khoản bảo mật cùng luật "chỉ bán khi đóng gói" vào điều khoản đối tác.

### 2.4 Markup và margin (hay bị nhầm)
- Markup = (bán − net) / net. Margin = (bán − net) / bán.
  - Markup 25% chỉ cho margin 20%.
  - Muốn margin 25% thì phải markup 33,3%.
  - Markup 20% chỉ cho margin 16,7% ([Patriot](https://www.patriotsoftware.com/blog/accounting/margin-vs-markup-chart-infographic/)).
- Engine của mình đang tính theo **margin trên giá bán**: `sell = net / (1 − margin − card_fee)`. Ví dụ net 100 USD, margin 20%, phí thẻ 3% thì giá bán là 129,87 USD, tương đương markup 29,9%. Màn hình CSKH nên hiện cả hai con số để khỏi nhầm.
- Chưa có benchmark margin đáng tin cho DMC.
  - Các hãng phần mềm nêu 20–35% [ví dụ].
  - Con số duy nhất do chính doanh nghiệp công bố: Exoticca khoảng 20% năm 2019 ([PhocusWire](https://www.phocuswire.com/pcw-europe-2024-evolution-of-tours)).

### 2.5 Nhóm số khách
- Tour riêng tính giá mỗi người theo nhóm số khách, ở phòng đôi, cộng phụ thu phòng đơn. Amara Tours chia 2–3 / 4–5 / 6–7 / 8+ ([link](https://amaratours.vn/en/vung-tau-2-days-tour.html)). EXO coi 1–8 khách là FIT, từ 9 khách là đoàn ([EXO T&C 01/2026](https://www.exotravel.com/assets/pdf/EXO%20-Terms-and-Conditions-January-2026.pdf)).
- **Chi phí cố định (hướng dẫn viên, xe, thuyền) chia theo đầu người.** Lấy giá của nhóm 2 khách áp cho 1 khách thì lỗ, áp cho 6 khách thì bán quá đắt.
- **Số khách thực đi quyết định lời lỗ** [ví dụ, Peakflo](https://peakflo.co/blog/tour-operator-departure-margin-visibility-automation): đoàn tính giá cho 20 khách lời 25%, nếu chỉ đi 12 khách thì còn khoảng 5%.
- **Trẻ em:** em bé 0 đến dưới 2 tuổi, trẻ em 2 đến dưới 12, và chỉ được giảm khi có 2 người lớn trả đủ giá ([Asian Trails](https://www.asiantrails.travel/destinations/vietnam-terms-and-conditions/)). Có sản phẩm lại dùng 4–10 tuổi ([Asian Trails Phuket](https://www.asiantrails.travel/?p=1043033)). → Khung tuổi phải theo từng sản phẩm, không để một tỉ lệ % chung.
- **FOC trưởng đoàn** thường là 1 suất miễn phí trên 15 khách trả tiền, hoặc 2 trên 30 [ví dụ]. Lấy theo từng hợp đồng.

### 2.6 Hiệu lực giá: hai trục ngày
- **Ngày đi** quyết định mùa. Câu của TripWorks: *"Seasons match on when the trip runs, not when it's booked"* ([link](https://help.tripworks.com/en_US/experience-pricing/raise-your-prices)).
- **Ngày đặt** chỉ dùng cho ưu đãi đặt sớm và khuyến mãi. Travelbooster còn cho hai mùa trùng ngày đi miễn khác ngày đặt ([link](https://www.assets.travelbooster.com/Help/Editing_a_price_list_for_a_hotel_contract.htm)).
- **Hạn báo giá.**
  - Khiri: 30 ngày (đã kiểm, [link](https://khiri.com/quotation-terms)).
  - EXO: tối đa 7 ngày [snippet, chưa kiểm PDF].
  - Mình: mặc định 48 giờ (`DEFAULT_VALID_HOURS = 48`), code cho tối đa 720 giờ tức 30 ngày.
- **Giá NCC hết hạn.** Theo dữ liệu khách hàng của TourConnect, khoảng 5% yêu cầu gửi tới DMC có dịch vụ đã hết hạn giá (01–09/2025). Cách xử lý của họ: lấy giá năm trước cùng mùa, cộng % tăng, gắn cờ "tạm tính" ([link](https://tourconnect-ai.squarespace.com/resources/new-expired-rate-automation-for-tourplan)).

### 2.7 Allotment, release, stop-sale
- **Các loại tồn kho** ([Lemax](https://support.lemax.net/article/types-of-capacities/)):
  - Allotment: đặt thẳng khi còn chỗ và còn trong hạn release;
  - Fixed: mua trước, bán được hay không vẫn trả tiền;
  - On request: lần nào cũng phải hỏi NCC;
  - Free sale.
- **Release và stop-sale** ([Tourpaq](https://manual.tourpaq.com/stop-sales)):
  - Ngày release = ngày của allotment trừ đi số ngày release.
  - Stop-sale chặn allotment nhưng không chặn phòng đã bảo đảm.
  - Phòng bị huỷ trong thời gian stop-sale không được mở lại để bán.
- Các ràng buộc khác: CTA/CTD (không cho đến / không cho đi vào ngày đó), số đêm tối thiểu và tối đa ([SiteMinder](https://help-platform.siteminder.com/en/articles/9458959-set-up-and-manage-restrictions)).
- Release thường 14–21 ngày, mùa cao 21–45 ngày [ví dụ]. Giảm giá cho allotment thường 10–50% ([Wikipedia](https://en.wikipedia.org/wiki/Allotment_(travel_industry))).
- Mình hiện chỉ có release cho allotment của đại lý trên departure (`b2b/allotments.py`), chưa có trên giá khách sạn.

### 2.8 Tỉ giá
- Trả NCC bằng VND, THB, IDR; bán bằng USD. DMC trong vùng ghi rõ không bảo đảm tỉ giá quy đổi ([Asian Trails](https://www.asiantrails.travel/?p=1024461), [Destination Asia](https://destination-asia.com/terms-conditions)). Phí thanh toán thẻ 3–5%.
- Tourwriter: dùng tỉ giá cố định theo ngày cộng một khoản đệm. Ví dụ đệm 5% biến 1,7320 thành 1,8186. Đổi bảng tỉ giá không làm đổi các báo giá đã có ([link](https://learn.tourwriter.com/portal/en/kb/articles/organisation-default-tab-explained)).
- Một wholesaler châu Á lỗ 15% với khách châu Âu đặt trước 6–10 tháng ([TTG Asia 2016](https://www.ttgasia.com/2016/06/03/coping-with-currency-woes/)).
- **Việt Nam:** Thông tư 32/2013 (sửa bởi Thông tư 03/2019) bắt niêm yết và báo giá bằng VND, trừ các ngoại lệ. Bên cư trú bán dịch vụ cho bên không cư trú được báo giá và thu ngoại tệ qua chuyển khoản ([Mondaq](https://www.mondaq.com/financial-services/314242/circular-32-provides-guidance-on-the-restrictions-on-the-use-of-foreign-currencies-in-vietnam), [DFDL](https://www.dfdl.com/insights/legal-and-tax-updates/vietnam-legal-update-additional-permitted-cases-on-the-use-of-foreign-currency-in-the-territory-of-vietnam)). **Cần luật sư hoặc kế toán kiểm**, nhất là VAT cho dịch vụ tour tiêu dùng tại Việt Nam (0% hay 8/10%) và tiền tệ trên hoá đơn điện tử.
- Mình đã có: bảng tỉ giá (số đơn vị trên 1 USD, đệm, ngày `as_of`, nguồn), báo giá khoá tỉ giá, chụp tỉ giá lúc xác nhận và lúc xuất hoá đơn (bk-045).

### 2.9 Bảng giá năm và báo giá theo yêu cầu
- Asian Trails công bố giá 2027 ngày 21/8/2026, năm trước công bố ngày 22/8/2025 cho kỳ "11/2025 đến 2026" ([2027](https://www.asiantrails.travel/?p=1051893), [2025](https://www.asiantrails.travel/?p=1047131)). Tức là họ phát hành khoảng 2–3 tháng trước khi kỳ bắt đầu.
- Họ tách công cụ xem giá (Cloud Tariff) khỏi công cụ đặt chỗ live có API (eConnect). EXO Create cũng có tariff, bảng tình trạng chỗ, đặt ngay hoặc "Book with Review" do tư vấn viên duyệt ([link](https://www.exotravel.com/exo-create)).
- Các tổng cục du lịch khuyên chốt giá trước 12–18 tháng ([Destination NSW](https://destinationnsw.com.au/destination-nsw-business-support/nsw-first-program/how-to-create-your-sales-kit), [Travel Alberta](https://industry.travelalberta.com/test/becoming-export-ready)).
- Báo giá theo yêu cầu (tour riêng, đoàn) không giữ chỗ: *"nothing is booked"* cho tới khi xác nhận ([Khiri](https://khiri.com/quotation-terms)).

### 2.10 FIT và đoàn
- **Huỷ với khách lẻ, tối đa 8 người** ([EXO](https://www.exotravel.com/assets/pdf/EXO%20-Terms-and-Conditions-January-2026.pdf)):

  | Trước ngày đến | Phí huỷ |
  |---|---|
  | từ 31 ngày | chỉ mất cọc không hoàn |
  | 30–22 ngày | 10% |
  | 21–15 ngày | 25% |
  | 14–8 ngày | 50% |
  | 7 ngày đến 48 giờ | 75% |
  | dưới 48 giờ | 100% |

- **Đoàn từ 9 người**, cùng các mốc ngày trên: 20% / 40% / 60% / 75% / 100%.
- **Khiri với đoàn:** cọc 25% trước 8 tuần, rooming list nộp trước 10 tuần ([link](https://khiri.com/terms-conditions/)).
- Mình có nhóm số khách nhưng chưa có bảng giá đoàn, quy tắc FOC hay bảng huỷ riêng cho đoàn.

### 2.11 Hạng đại lý
- Arival khuyên **tối đa 4 mức giá**, hạn chế deal riêng lẻ vì các đối tác so giá với nhau và sinh mâu thuẫn ([Arival](https://arival.travel/how-to-set-net-rates-for-tours/)). Họ cũng đưa khoảng giảm so với giá lẻ cho từng kênh (đây là ngành tour và hoạt động trải nghiệm):

  | Kênh | Giảm so với giá lẻ |
  |---|---|
  | ITO | 25–30% |
  | Wholesaler hoặc OTA | 20–25% |
  | Đại lý | 10–15% |

- Asian Trails: *"Special rates depend on the client delivering the agreed business volume"*.
- Mình hiện có 3 hạng (0 / 3 / 6%) cộng thẻ giá riêng cho từng đối tác, vậy là đủ. Không cần thêm hạng. Nên siết thẻ giá riêng: có ngày hết hạn, có cam kết sản lượng, xét lại mỗi năm.

---

## 3. Cách bán cho đại lý

- **Bảng giá và cổng B2B.**
  - Đại lý xem bảng giá online, đặt live trong phần allotment; ngoài allotment thì gửi yêu cầu và chờ xác nhận ([Destination Asia](https://destination-asia.com/terms-conditions)).
  - Có lựa chọn "đặt có tư vấn viên duyệt". API hoặc XML cho wholesaler để sau.
  - Phát hành bảng giá năm sau khoảng 3 tháng trước khi kỳ bắt đầu, cho bản hiện hành và bản năm sau chạy song song.
- **Cọc và thanh toán.**
  - Asian Trails: trả đủ 30 ngày trước ngày đến nếu không có hạn mức tín dụng; quá hạn có thể tự huỷ.
  - Destination Asia: 14 ngày.
  - EXO: số dư trả 30 ngày trước; đặt trong vòng 30 ngày thì trả khi nhận hoá đơn.
  - Indochina Voyages: cọc 30%, phần còn lại trả trước 45 ngày ([link](https://www.indochinavoyages.com/?p=2529)).
  - Mùa lễ chặt hơn nhiều. Mandarin Oriental Bangkok bắt trả đủ tiền phòng lễ và gala NYE trước 30/9, không hoàn ([link](https://photos.mandarinoriental.com/is/content/MandarinOriental/bangkok-festive-tandc)). Thang huỷ thường của Asian Trails không áp cho mùa cao điểm.
  - Hạn mức tín dụng gắn theo từng đại lý và được kiểm lúc đặt.
- **Ưu đãi đặt sớm.** Tính theo ngày đặt, kèm cờ "có cộng dồn với ưu đãi khác không" (hợp đồng mẫu của [Clock](https://support.clock-software.com/en/support/solutions/articles/9000270814-sample-tour-operator-contract-preparation) ghi: đặt sớm không cộng với ở dài). Mình đã có `early_days` và `early_discount_pts`.
  - Không cần định giá động kiểu bán lẻ (giữ giá 3 ngày của Trafalgar, giảm giá phút chót). Mình bán B2B; bảng giá mà đại lý bán lại thì càng ít đổi càng tốt.
- **Giữ giá trên báo giá.**
  - Báo giá là lời hứa giá cho tới khi hết hạn. Hết hạn thì tính lại và cho đại lý thấy chênh lệch.
  - Booking đã xác nhận thì khoá giá ([G Adventures](https://www.gadventures.com/terms), [Intrepid](https://www.intrepidtravel.com/uk-booking-conditions)).
  - Xu hướng 2026–27: Intrepid ([link](https://www.intrepidtravel.com/en/newsroom/releases/commits-to-no-surcharges-on-trips-booked-in-2026-reinforcing-transparent-pricing-and-traveller-confidence)), Goway ([link](https://www.travelmarketreport.com/packaged-travel/articles/goway-commits-to-no-surcharges-on-confirmed-2026-bookings)) và Back Roads (đến hết 2027, [link](https://travelweekly.com.au/back-roads-guarantees-no-surcharges-on-bookings-through-to-end-of-2027/)) công khai cam kết **không phụ thu sau khi đã xác nhận**. Đại lý coi "chắc giá" là một lý do để chọn nhà cung cấp.
- **Đổi giá giữa năm.**
  - Giá mới chỉ áp cho báo giá và booking mới.
  - Với booking đã xác nhận, theo luật du lịch trọn gói EU (PTD Art. 10) và Anh (PTR 2018 reg. 10):
    - chỉ được tăng vì nhiên liệu, thuế hoặc phí của bên thứ ba, hoặc tỉ giá;
    - hợp đồng phải ghi sẵn quyền này, và phải có cả quyền giảm khi chi phí giảm;
    - báo trên văn bản, kèm cách tính, ít nhất 20 ngày trước khởi hành;
    - tăng quá 8% thì khách được huỷ miễn phí ([EUR-Lex](https://eur-lex.europa.eu/eli/dir/2015/2302/oj/eng), [legislation.gov.uk](https://www.legislation.gov.uk/uksi/2018/634/regulation/10)).
  - Luật này ràng buộc đại lý EU/UK chứ không ràng buộc trực tiếp AA. Nhưng Art. 20/22, và reg. 29B của Anh (áp từ 6/4/2027, [gov.uk](https://assets.publishing.service.gov.uk/media/6ae0b2c9779378370fd80a19/guidance-on-the-package-travel-and-linked-travel-arrangements-regulations-2018-amended-2026.pdf)), cho phép họ đòi lại mình phần thiệt hại. Vì vậy điều khoản B2B của mình nên viết khớp luật này.
  - Bản sửa PTD năm 2026 *chưa kiểm* với văn bản cuối xem có đổi mốc 8% và 20 ngày hay không. Cần luật sư xác nhận trước khi ghi vào điều khoản.
- **Lỗi giá.**
  - Asian Trails được sửa giá khi chênh lệch từ 70% giá đúng hoặc từ 500 USD/EUR mỗi booking; chênh dưới 20% thì bỏ qua; đại lý có 7 ngày để xác nhận lại ([link](https://www.asiantrails.travel/?p=36)).
  - Mình đã có clause `price_error` trong partner terms, kèm số ngày huỷ miễn phí. Nội dung clause nằm trong DB, cần đối chiếu trước khi đề xuất ngưỡng mới.

---

## 4. Phần mềm trong ngành quản lý phiên bản giá ra sao

| Phần mềm | Cách làm | Mình nên học gì |
|---|---|---|
| **Recranet** ([link](https://help.recranet.com/en/articles/520845-new-pricing-structure-version-control)) | Mỗi lần lưu giá là một bản: thời gian, người, loại thay đổi (tay, batch, CSV), số giá bị đổi. Xem bản cũ có tô các ô đã đổi. Không ghi nhận có nút quay lại | Lịch sử và diff theo từng ô |
| **Travelbooster** ([link](https://www.assets.travelbooster.com/Help/Editing_a_price_list_for_a_hotel_contract.htm)) | "Track Changes" ghi ai, khi nào, đổi gì; "Show History" hiện các mùa đã hết. Khuyên gỡ publish khi sửa rồi publish lại. Mùa tính theo ngày đi hoặc ngày đặt | Cổng publish, hai trục ngày |
| **Lemax** ([link](https://support.lemax.net/?p=7271)) | Đặt năm vào tên lịch giá. "Keep selling price" (05/2025): cập nhật giá vốn trên booking nhưng giữ nguyên giá bán và hoa hồng. Đổi lịch giá không hoàn tác được | Tách giá vốn khỏi giá đã hứa |
| **Tourwriter** ([lock](https://learn.tourwriter.com/portal/en/kb/articles/editing-locking-booking-prices), [CSV](https://learn.tourwriter.com/portal/en/kb/articles/how-to-import-supplier-rates-csv)) | Đổi giá trong thư viện không tự sửa hành trình đã có. Khoá theo net, markup, gross hoặc tất cả. Nhập CSV: xuất template, ngày dạng YYYY-MM-DD, một dòng lỗi thì không nhập dòng nào, cấm chồng lấn. Cập nhật hàng loạt cần quyền admin | Vòng xuất → sửa → nhập; "một lỗi là dừng cả file" |
| **TourConnect** (lớp giá cho Tourplan) ([link](https://intercom.help/tourconnect/en/articles/1140838-update-a-season)) | Mỗi kỳ hợp đồng một template. Giá hết hạn thì dùng giá cũ + % tăng, gắn cờ tạm tính. Gửi cập nhật cho đối tác | Giá tạm tính, báo cho đối tác |
| **Tourpaq** ([link](https://manual.tourpaq.com/booking/new-booking/history)) | Lịch sử chỉ đọc; sửa nghĩa là thêm dòng mới. Có log riêng cho stop-sale và release | Lịch sử chỉ được thêm, không sửa |
| **TripWorks, Rezdy** | Booking giữ giá lúc đặt. Sửa hàng loạt không đụng tới lịch đã có đơn | Không tính lại giá booking cũ |
| **Bokun** [snippet] | Đại lý chọn "giá mới nhất của NCC" hay "giá chụp lúc ký hợp đồng" | Ghim theo snapshot |

**Điểm chung.** Không hãng nào sửa đè giá. Đơn vị phiên bản thường là hợp đồng hoặc kỳ giá; hiếm hãng đánh số phiên bản chính thức. **Không hãng nào công bố quy trình hai người duyệt.** Họ chỉ có phân quyền, cổng publish và một bước kiểm tra chất lượng riêng (Open Destinations, [link](https://www.opendestinations.com/contract-loading-structure/)). Ở điểm này mình đang chặt hơn ngành.

**Nhập giá sai rất phổ biến.**
- Lanyon tìm thấy sai lệch trong 32% lần kiểm giá khách sạn (số của mảng công tác doanh nghiệp, [snippet]).
- Ví dụ của TourWriter: một báo giá lấy từ bảng giá tháng 3 bị hụt €360 so với giá vốn (€45 × 8 đêm), và công ty phải tự chịu ([link](https://www.tourwriter.com/?p=21147)).

**Chưa xác nhận được:** Tourplan NX, Kaptio, Juniper, Travelify để tài liệu sau đăng nhập. Không nên chép theo các hãng này khi chưa xem demo.

---

## 5. Hệ thống mình hôm nay so với cách làm của ngành

| # | Hạng mục | Đã có | Thiếu | Nên làm |
|---|---|---|---|---|
| 1 | Hợp đồng NCC | Có hiệu lực từ–đến; publish xong thì trigger DB khoá; người publish phải khác người viết (bk-008) | Không ghi hợp đồng mới thay hợp đồng nào; không diff; không có trạng thái từ chối; hai hợp đồng chồng nhau thì âm thầm lấy bản có `valid_from` mới nhất | Thêm `supersedes_id`; diff từng dòng giá (ví dụ "85 → 92 USD từ 01/04") khi duyệt |
| 2 | Mùa | Nhãn chữ tự do trên từng dòng giá | Không có lịch mùa; "peak" nhận ra bằng cách dò chữ "peak"; báo giá B2B chạy `peak = false`, nên RRP và giá đại lý đi theo hai logic mùa khác nhau | Lịch mùa theo hợp đồng và theo điểm đến, có chặn bán và sự kiện lễ theo từng năm; một logic mùa chung |
| 3 | Hai trục ngày | Chỉ có ngày đi; đặt sớm tính theo ngày báo giá | Không có cửa sổ ngày bán, không có stop-sale | Thêm ngày bán từ–đến trên giá và ưu đãi |
| 4 | **Giá tay của CSKH** | Lịch sử ghi ai sửa (`trip_plan_price_history`) | Không cần duyệt, không bắt lý do (trừ khi dưới sàn), có hiệu lực ngay, mỗi lần thay cả bộ | Nháp → chờ duyệt → phát hành, lý do bắt buộc, diff |
| 5 | Quy tắc, tỉ giá, hạng, thẻ giá | Chỉ thêm không sửa, có người duyệt thứ hai | Quy tắc không có ngày hết hạn và không giới hạn theo tour hay mùa; bản đang chờ không từ chối hay rút lại được; ghi chú không bắt buộc | Áp khuôn của bk-048 |
| 6 | Điều chỉnh giá theo departure (bk-048) | **Đầy đủ nhất:** lý do bắt buộc, chuỗi `replaces_id`, duyệt hai người, các trạng thái rejected/withdrawn | Không thiếu gì | Lấy làm khuôn chung cho mọi loại giá |
| 7 | Báo giá | Ghim đầu vào (id giá NCC, quy tắc, tỉ giá, hạng, thẻ); `price_hash`; hạn 48 giờ; trả 409 `price_changed` khi giá đổi | Không ghim id phiên bản (quy tắc chỉ lưu theo giá trị); 48 giờ ngắn hơn ngành | Thêm `price_version_id` và `tariff_version_id`; hạn báo giá theo chính sách (mục 7) |
| 8 | Xác nhận booking | Khoá phiên bản trip case, khoá chính sách huỷ, chụp tỉ giá | Chưa có quy tắc phụ thu sau xác nhận dưới dạng dữ liệu | Dòng phụ thu riêng theo điều khoản (6.8) |
| 9 | Bảng giá đại lý | Tính live với `priced_on` = hôm nay | Không id, không phiên bản; CRM không biết khi giá đổi; không có bản năm sau | Bản chụp đã phát hành, có id, ngày hiệu lực, ghi chú thay đổi và ETag; chạy hai bản song song |
| 10 | Xem trước tác động | Dry-run của rate sheet cho biết plan nào sẽ chuyển sang có giá | Duyệt hợp đồng, quy tắc hay tỉ giá là `bk_price_recompute` chạy ngay; không ai thấy giá cũ và giá mới trước khi lên | Bước xem trước: cũ → mới, % mỗi tour, cờ dưới sàn |
| 11 | Excel | Nhập từng hợp đồng một, có dry-run, một lỗi là không ghi gì, người thứ hai publish | Không xuất được; không nhập ma trận hay mùa; file không mang phiên bản | Xuất có id phiên bản và id dòng, nhập ra bản nháp mới, chép sang năm sau |
| 12 | Giá tạm tính | Giá tham khảo CIS là chữ, phân tích một lần, có cờ đã xem | Plan chỉ có giá tay (`hand_priced`) không bán được cho đại lý; "tạm tính" chưa có định nghĩa | Định nghĩa trạng thái tạm tính (6.11) |
| 13 | Trẻ em, phòng đơn, đoàn | `child %` và phí em bé chung; nhóm số khách | Khung tuổi theo sản phẩm, điều kiện 2 người lớn, phụ thu đơn, giường phụ, FOC, bảng huỷ đoàn | Đưa vào phiên bản hợp đồng và phiên bản giá |
| 14 | Gala và phụ thu lễ | Không có | Chưa có gì | Phụ thu bắt buộc theo ngày, tự thêm khi kỳ ở chạm ngày đó |
| 15 | Allotment và release khách sạn | Chỉ có allotment của đại lý theo departure | Release trên giá NCC, loại tồn kho | `inventory_type` và `release_days` (giai đoạn sau) |
| 16 | Thuế và hoá đơn | `booking.tax_rule` theo loại hoá đơn và nước, có hiệu lực | Giá net đã gồm VAT chưa; VAT 0% hay 8/10%; tiền tệ trên hoá đơn | Ghi `tax_rule` áp dụng vào phiên bản giá; kế toán Việt Nam kiểm |
| 17 | Markup và margin | Engine dùng margin trên giá bán | Màn hình chưa hiện cả hai | Hiện cả hai % |

**Bối cảnh quan trọng.** Hôm nay chỉ 2 trên 892 plan có giá; 890 plan ở trạng thái `no_components`. Nút thắt bán hàng trước mắt là dữ liệu thành phần tour, chưa phải phiên bản. Chính vì vậy nên xây phiên bản ngay trong workbench AA-1091, để 890 plan khi có giá thì có phiên bản luôn từ đầu, không phải sửa lại sau.

---

## 6. Thiết kế đề xuất cho "phiên bản giá" trong AA-1091

### 6.1 Năm nguyên tắc
1. Không sửa đè. Mọi thay đổi giá là một bản mới.
2. Một bản chỉ có hiệu lực khi người thứ hai duyệt. Tự duyệt đã bị chặn trong code, giữ nguyên.
3. Báo giá và bảng giá đại lý ghim theo id phiên bản.
4. Booking đã xác nhận không bao giờ bị tính lại giá.
5. Ngày đi quyết định mùa và phiên bản. Ngày đặt chỉ quyết định ưu đãi.

### 6.2 Thực thể `price_list_version` (Booking, migration bk-049 trở đi)
- **Phạm vi:** `trip_plan_id` cho ma trận giá bán. Với giá NCC thì **chính hợp đồng là phiên bản**: chỉ cần thêm `supersedes_id` và diff, không tạo bảng mới.
- **Định danh:** `version_no` tăng dần trong phạm vi, `label` dễ đọc (ví dụ "2027 v3"), `tariff_year`.
- **Trạng thái:** `draft` → `pending` → `published` → `superseded`, thêm `rejected` và `withdrawn`, theo đúng khuôn bk-048.
- **Hiệu lực:** `travel_from`/`travel_to` (ngày đi; bên trong lưu dạng nửa mở, xem 6.10) và `sale_from`/`sale_to` (ngày đặt, không bắt buộc).
- **Người và lý do:** `created_by` (người nhập), `approved_by`/`approved_at`, `reason` bắt buộc (≤ 300 ký tự), `replaces_id`.
- **Nguồn:** `staff` / `import` / `cost_sheet` / `provisional`, kèm hash của file Excel nếu nhập từ file.
- **Đi kèm:** `diff` và `impact` (json) được tính lúc gửi duyệt.
- **Dòng giá:** dùng lại hình dạng ma trận hiện tại, thêm `version_id` và `season_id` (thay cho nhãn chữ). `trip_plan_price_history` trở thành các dòng thuộc từng phiên bản.
- Quy tắc, tỉ giá, hạng và thẻ giá giữ cấu trúc hiện tại, chỉ bổ sung từ chối và rút lại cho bản đang chờ, bắt buộc ghi lý do, và thêm `valid_to` cho quy tắc.

### 6.3 Mùa
- `season_calendar` theo hợp đồng (mùa của NCC) và theo điểm đến (mùa của bảng giá bán AA).
- Mỗi lịch gồm các khoảng ngày Low / High / Peak / Festive, cho phép lặp; khoảng chặn bán; sự kiện lễ có ngày riêng cho từng năm (Tết, Songkran, Lebaran, Tết Trung Hoa, Giáng sinh và năm mới).
- Cờ peak lấy từ lịch, bỏ cách dò chữ "peak". Báo giá B2B và RRP dùng cùng một logic mùa.
- Mỗi hợp đồng có cờ "tính từng đêm" (mặc định) hoặc "tính cả kỳ theo mùa của ngày đến".

### 6.4 Bản nào áp cho báo giá
Bản áp dụng là **bản đã phát hành tại thời điểm báo giá và có hiệu lực cho ngày đi**. Ưu đãi đặt sớm xét theo ngày báo giá. Khi có bản năm sau đã phát hành, đại lý báo giá năm sau thì dùng bản đó.

### 6.5 Ai nhập, ai duyệt
| Vai trò | Việc |
|---|---|
| CSKH | Người nhập: tạo bản nháp, nhập Excel, gửi duyệt |
| Trưởng sản phẩm / định giá | Người duyệt: phát hành hoặc từ chối, kèm lý do |
| `finance` (ADR 0019 d3) | Duyệt tỉ giá, quy tắc thuế, phụ thu |

Tuỳ chính sách, có thể cho bản do `bk_price_recompute` sinh ra tự phát hành nếu nằm trong ngưỡng ±X%. Ngoài ngưỡng thì vào hàng chờ duyệt (câu 4, mục 7). Sau khi phát hành, hệ thống tự kiểm 4 ngày mẫu: ngày đầu, ngày cuối, một ngày peak và một ngày không bị ảnh hưởng.

### 6.6 Lý do, so sánh, tác động
- **Diff từng dòng:** mùa × nhóm số khách × kênh, giá cũ → giá mới, %. Tô đậm những dòng thay đổi lớn hơn X%; gắn cờ những dòng dưới sàn margin.
- **Impact:** số báo giá đang mở sẽ bị tính lại khi hết hạn, số dòng bảng giá đại lý thay đổi, giá "from" công khai thay đổi, và margin mỗi khách ở số khách dự kiến.
- Người duyệt chỉ thấy nút "Phát hành" sau khi đã xem diff.

### 6.7 Báo giá ghim phiên bản
- `b2b_quotes` thêm `price_version_id` và `tariff_version_id`; vẫn giữ `price_hash`.
- Hạn báo giá theo chính sách, code cho tối đa 30 ngày.
- Báo giá hết hạn thì tính lại và hiện cho đại lý "giá cũ X, giá mới Y". Muốn giữ giá cũ thì dùng điều chỉnh giá đã có sẵn (bk-048), kèm lý do.

### 6.8 Booking đã xác nhận
- Không bao giờ tính lại giá. Nếu giá vốn NCC đổi, nhân viên thấy phần chênh dưới dạng **chênh lệch margin** (cách "Keep selling price" của Lemax); đại lý không thấy gì.
- Ngoại lệ duy nhất là một **dòng phụ thu theo điều khoản**:
  - nguyên nhân chỉ là nhiên liệu, thuế hoặc tỉ giá;
  - có cách tính, được duyệt;
  - báo đại lý ≥ 20 ngày trước khởi hành;
  - khi chi phí giảm thì cũng trả lại;
  - tăng quá 8% thì đại lý được huỷ miễn phí.
- Mọi thay đổi khác do mình tự chịu.

### 6.9 Bảng giá đại lý có phiên bản
- `tariff_version` là bản chụp được dựng từ các phiên bản giá đã phát hành: có id, ngày hiệu lực, ghi chú thay đổi, ETag.
- Bản hiện hành và bản năm sau chạy song song. CRM nhận ra khi bảng giá đổi qua ETag hoặc qua event.
- Cập nhật hợp đồng `booking.b2b.v1` (lên bản 1.9).

### 6.10 Excel có phiên bản
- **Xuất:** từ bản đã phát hành ra .xlsx, mang `version_id` và `row_id`, ngày dạng YYYY-MM-DD **tính cả ngày cuối** giống bảng giá NCC. Hệ thống tự đổi sang nửa mở ở bên trong, để tránh bẫy "đêm không có giá" như ví dụ Lemax.
- **Nhập:** tạo bản nháp mới với `replaces_id` = bản đã xuất. Nếu bản gốc không còn là bản mới nhất thì báo xung đột và không nhập.
- Một dòng lỗi thì không nhập dòng nào. Dry-run cho thấy diff và impact.
- **"Chép sang năm sau +x%":** tạo bản nháp có trạng thái tạm tính.

### 6.11 Giá tạm tính
- `source = provisional`, lấy từ giá năm trước cùng mùa + % tăng, hoặc từ giá tham khảo CIS đã có cấu trúc (AA-1091 mục 5).
- Cờ "tạm tính" hiện cho cả CSKH và đại lý. Báo giá có dòng tạm tính thì đi theo luồng "cần xác nhận / đặt có duyệt", không tự xác nhận.
- Cách này cũng giải bài toán plan chỉ có giá tay không bán được cho đại lý.

### 6.12 Màn hình workbench
- Dòng thời gian phiên bản cho mỗi tour, ví dụ: "v3 · phát hành 01/09 · nhập: A · duyệt: B · lý do: hợp đồng KS 2027".
- Xem diff giữa hai bản bất kỳ; hàng chờ duyệt cho người duyệt; trạng thái sẵn sàng (readiness) như hiện nay.

**ADR.** Thay đổi chạm cả Booking, CRM (đọc bảng giá có phiên bản) và hợp đồng API, nên cần viết ADR ở repo gốc (0005b, bổ sung cho 0005). Đây là PR chạm schema và hợp đồng API, nên cho agent review trước khi merge.

---

## 7. Câu hỏi cho chủ doanh nghiệp (chính sách giá là việc kinh doanh)

*Mỗi câu kèm đáp án gợi ý. Chủ doanh nghiệp chọn hoặc sửa; kỹ thuật làm theo.*

| # | Câu hỏi | Gợi ý | Vì sao |
|---|---|---|---|
| 1 | Năm bảng giá bán cho đại lý | 1/11–31/10, công bố cuối tháng 8. Hợp đồng NCC vẫn theo từng NCC | Khớp mùa du lịch khu vực và cách của Asian Trails |
| 2 | Hạn báo giá B2B | 14 ngày cho tour thường; 3 ngày cho dịp lễ (Tết, Giáng sinh, năm mới) | 48 giờ hiện tại ngắn hơn ngành (Khiri 30 ngày); dịp lễ giá NCC đổi nhanh |
| 3 | Booking đã xác nhận có được đổi giá không | Cam kết không đổi. Chỉ giữ quyền với thuế nhà nước và tỉ giá biến động quá X% (đề nghị 5%; ngành không có chuẩn), báo ≥ 20 ngày, có cả giảm | Đại lý EU/UK bắt buộc; thị trường đang chuyển sang "chắc giá" |
| 4 | Ngưỡng tự phát hành | Mọi giá nhập tay cần duyệt. Tính lại tự động trong ±3% thì tự phát hành, ngoài ngưỡng thì chờ duyệt | Giữ an toàn mà không nghẽn việc |
| 5 | Ai duyệt giá | Trưởng sản phẩm hoặc điều hành duyệt giá; kế toán duyệt tỉ giá và thuế | Tách người nhập và người duyệt |
| 6 | Mùa của bảng giá bán | Một bộ mùa chung theo điểm đến (Low / High / Peak / Festive), hợp đồng NCC giữ mùa riêng | Đại lý dễ đọc; giá vốn vẫn đúng |
| 7 | Gala và phụ thu lễ | Gala bắt buộc tính nguyên giá cộng margin chuẩn; phụ thu Tết theo từng khách sạn | Bỏ sót gala là lỗ trực tiếp |
| 8 | Cọc và huỷ | Khách lẻ trả đủ 30 ngày trước; thang huỷ 30–22 ngày 10%, 21–15 ngày 25%, 14–8 ngày 50%, 7 ngày–48 giờ 75%, dưới 48 giờ 100%. Đoàn cọc 25% trước 8 tuần. Dịp lễ không hoàn trong 30 ngày | Phỏng theo EXO, Khiri và Asian Trails |
| 9 | Đoàn từ 9 khách | Năm đầu báo giá theo yêu cầu; FOC theo hợp đồng NCC (thường 1/15) | Chưa đủ dữ liệu để làm bảng giá đoàn |
| 10 | Hạng đại lý | Giữ 3 hạng 0 / 3 / 6%. Thẻ giá riêng chỉ cho đối tác lớn, có hạn và cam kết sản lượng, xét lại mỗi năm | Arival khuyên tối đa 4 mức |
| 11 | Tiền tệ | USD cho đại lý nước ngoài, VND cho đại lý Việt Nam; khoá tỉ giá lúc báo giá cộng khoản đệm hiện có | Thông tư 32 và VAT cần luật sư hoặc kế toán xác nhận |
| 12 | Giá tạm tính khi NCC chưa gửi giá năm mới | Cho phép: giá năm trước + 5%, gắn cờ, chỉ "cần xác nhận" | Không để báo giá bị kẹt (khoảng 5% yêu cầu gặp tình huống này) |

Nên hỏi thêm một câu ngoài bảng: **margin mục tiêu và margin sàn cho từng kênh** (b2b, fixed departure), ghi rõ là margin trên giá bán.

---

## 8. Thứ tự triển khai

1. **Chốt chính sách.** Câu 1–5 cần có trước khi code; các câu còn lại chốt dần.
2. **ADR 0005b và hợp đồng API.** Mô hình phiên bản, hai trục ngày, quy tắc sau xác nhận, `booking.b2b.v1` bản 1.9. Agent review trước khi merge.
3. **Giá tay của CSKH thành phiên bản** (lỗ hổng lớn nhất, rủi ro thấp): nháp → duyệt → phát hành, lý do bắt buộc, diff. Làm cùng workbench AA-1091.
4. **Lịch mùa có cấu trúc** và sự kiện lễ theo năm; bỏ dò chữ "peak"; thống nhất peak giữa báo giá và RRP.
5. **Xem trước tác động** trước khi duyệt hợp đồng, quy tắc, tỉ giá; tính lại ngoài ngưỡng thì vào hàng chờ. Thêm từ chối và rút lại cho bản đang chờ; thêm `supersedes_id` cho hợp đồng.
6. **Báo giá ghim `price_version_id`**; hạn báo giá theo chính sách; màn hình báo lại giá có diff.
7. **Bảng giá đại lý có phiên bản** (id, ETag, bản năm sau); CRM đọc theo phiên bản.
8. **Excel xuất và nhập có phiên bản**, chép sang năm sau, giá tạm tính (gộp với mục nhập Excel và mục giá tạm tính của AA-1091).
9. **Sau đó:**
   - khung tuổi trẻ em, phụ thu đơn và giường phụ, FOC, bảng huỷ đoàn;
   - phụ thu gala tự động;
   - loại tồn kho và release cho khách sạn;
   - dòng phụ thu sau xác nhận;
   - báo cáo chênh lệch hoá đơn NCC so với báo giá;
   - KPI: tỉ lệ báo giá thành booking theo từng đại lý, % báo giá dùng giá tạm tính, % chênh lệch giá vốn, số lần đổi giá sau xác nhận.

**File chính đã đối chiếu:**
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/CONTEXT.md`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/b2b/quotes.py` (`DEFAULT_VALID_HOURS = 48`, `MAX_VALID_HOURS = 720`)
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/pricing/engine.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/catalog/price_history.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/b2b/price_adjustments.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/b2b/tariff.py`
- `/home/nghiep/projects/AA-Ecosys/docs/adr/0005-pricing-and-supplier-rates.md`
- `/home/nghiep/projects/AA-Ecosys/docs/adr/0019-b2b-only-ecosystem-model.md`
- `/home/nghiep/projects/AA-Ecosys/docs/contracts/booking.b2b.v1.openapi.yaml`