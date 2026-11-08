# Thiết kế mới cho dữ liệu SEO / DataForSEO (S273)

> Đây là bản thiết kế, chỉ dựa trên việc đọc mã nguồn. Không gọi AWS, DB, LLM hay DataForSEO.
> Đầu vào: kiểm toán `docs/audits/2026-11-08-S273-session/dfs-cost-audit/report.vi.md`, issue AA-1055 kèm 2 comment, số đo live ngày 08–09/11, và 3 hướng thiết kế đã được 9 lượt giám khảo chấm.
> Chỉ dùng những con số mà các giám khảo tính lại và khớp nhau. Số nào chưa đo được thì ghi rõ "chưa kiểm".

**Thuật ngữ (giải thích một lần):**
- **DFS (DataForSEO):** dịch vụ trả phí cho biết người ta gõ gì lên Google.
- **Volume:** số lượt tìm mỗi tháng của một cụm từ khoá. DFS bán theo **task**: mỗi task chở tối đa 1.000 từ khoá cho MỘT nước, giá 0,09 USD.
- **SERP:** trang kết quả Google của một từ khoá, 0,002 USD mỗi lần. Từ một SERP mình lấy được:
  - **PAA (People Also Ask):** các câu hỏi "Mọi người cũng hỏi";
  - **related searches:** các cụm tìm kiếm liên quan;
  - các tên miền đứng top.
- **keywords_for_keywords:** DFS gợi ý từ khoá liên quan, 0,09 USD mỗi lần gọi (tối đa 20 hạt giống).
- **Thị trường (market):** nước của người đang tìm. Mã nguồn hỗ trợ 6 nước: US, UK, AU, DE, FR, NL.
- **Kho nhu cầu `search_demand`:** bảng lưu mỗi (từ khoá, thị trường) một dòng, dùng chung cho mọi tenant.
- **`seo_context`:** bảng SEO riêng theo từng tour. Hiện chỉ S1 ghi vào, và chỉ cho US.
- **Segment:** một cặp "địa điểm + hoạt động" trong tour.
- **Slate:** danh sách chủ đề đề xuất cho tenant (T7). Kênh Blog chỉ nhận chủ đề có ≥1.000 lượt tìm VÀ ≥3 câu hỏi.
- **Recompute:** job tính lại xếp hạng. Slate chỉ thấy dữ liệu mới sau khi recompute chạy.
- **Jev:** dịch vụ AI trả phí, mình dùng để duyệt "từ khoá này có đúng của địa điểm này không".
- **Debounce:** gộp nhiều yêu cầu sát nhau thành một lần chạy.

## Tóm tắt (5 dòng)

1. Hôm nay mỗi gói dữ liệu Google bị mua hai lần, dưới hai dạng. S1 mua theo từng tour (chỉ US, người khác không thấy). Nghiên cứu mua theo địa điểm × nước (S1, T8, T9 không đọc). T2 của đại lý UK/DE thì lấy từ khoá US. Slate không thấy dữ liệu mới cho tới khi có recompute.
2. Đề xuất chọn **hướng A, "một người mua, một kho, mọi bước đều đọc"**, có ghép thêm ý hay của hai hướng kia (mục 9). Chỉ job nghiên cứu được mua DFS. S1 và T2 thôi mua và chỉ đọc kho. Volume mua cho cả 6 nước. **Mỗi địa điểm chỉ mua 1 SERP**, bằng tiếng Anh, không mua lại theo từng nước.
3. T2 được dùng mọi thị trường đại lý khai (không chỉ nước đầu tiên). Câu hỏi lấy từ bất kỳ nước nói tiếng Anh nào. Từ khoá được lọc trước khi vào prompt, để T2 không bị trừ điểm oan.
4. Chi phí lần đầu cho 6 nước khoảng **23,3 USD** theo giá live (DFS 21,5 + LLM 1,85). Trần thật là **DFS 30,2 USD, cao hơn số dư 27,41**, nên phải chạy theo đợt và duyệt từng đợt. Nếu giá "Standard queue" của DFS đúng như giám khảo nhớ (chưa kiểm), phần DFS giảm còn khoảng 10 USD.
5. Thứ tự đề xuất:
   - Sửa code an toàn trước (T2 + Slate + recompute).
   - R0 miễn phí.
   - R1: map từ khoá + volume US/UK/AU, khoảng 6,9 USD.
   - R2: SERP, khoảng 11,3 USD (3,4 USD nếu dùng queue).
   - R3: DE/FR/NL, chỉ chạy sau một phép thử 0,27 USD.
   - Hằng tháng sau đó: khoảng 2,9 USD.

## 1. Hôm nay mỗi bước dùng dữ liệu SEO thế nào

| Bước | Đọc gì | Thiếu thì sao | Tự mua DFS? |
|---|---|---|---|
| **S1**: viết lại catalogue AA (`process_seo`) | Dòng `seo_context` của tour còn hạn 180 ngày. Không có thì xem cache Redis 7 ngày. Không có nữa thì **gọi DFS live**: 1 SERP + 1 keywords_for_keywords. Thị trường chỉ là US (thị trường của tenant AA). | Writer viết không có từ khoá. Không lỗi. | **Có.** Admin bấm. Khoảng 0,092 USD/tour, trần 0,50 USD/tour. |
| **S1**: job `s1_seo_prefetch` (trước một wave) | Đọc `search_demand` trước. Đủ ≥5 ý tưởng thì không mua. Thiếu thì mua keywords_for_keywords theo lô và 1 SERP/tour. **Chỉ ghi vào `seo_context`, không ghi vào kho chung.** | Tour vẫn có dòng, nhưng từ khoá chỉ là tên tour. | **Có.** Admin bấm. |
| S1: writer dùng dữ liệu | Writer v2 dùng tối đa 3 từ khoá có trong nguồn, chỉ cho seo_title/meta, và không dùng PAA. Writer cũ dùng 5 từ khoá + 3 PAA. | Không có khối SEO. | Không. |
| **T2**: viết lại tour cho đại lý | Dòng `seo_context` US của AA. Sau đó tra `search_demand` theo **chỉ 1 thị trường đầu tiên** của đại lý. PAA chỉ lấy từ cùng nước đó. | Lùi về từ khoá US của AA. Không có nữa thì viết không SEO. Có từ khoá mà không đưa vào title/meta thì **bị trừ 1,0 điểm validate**. Điểm validate hiện là điểm duy nhất của T2 (tạm thời từ S271). | Không. Có test chặn. |
| **T7**: Slate, thanh chắn Blog | Nhu cầu của **nước có tổng hạng tốt nhất**. Segment chưa đo thì nhận hạng trung vị, nên một nước rỗng dữ liệu như DE có thể "thắng" và che mất số thật của US/UK. | Không có số thì coi là 0, trượt Blog trong im lặng. | Không. |
| T7: kế hoạch quý (`dfs_relevance`) | `seo_context` US của tour. | Xếp mức trung bình (MED). | Không. |
| **T8**: góc viết | `seo_context` US của tour, không phân theo thị trường. Riêng Blog, PAA lấy qua chuỗi câu hỏi thật. | Tour S1 chưa từng mua thì **mất hẳn khối "nhu cầu tìm kiếm"**. | Không. |
| **T9**: viết blog | Từ khoá SEO lấy từ related searches trong snapshot của T8 (tức US). FAQ lấy câu hỏi thật từ kho, bất kỳ nước nào, chỉ giữ tiếng Anh. | Viết không từ khoá. FAQ do AI tự đặt câu hỏi. | Không. Riêng script bù câu hỏi US là việc admin chạy tay. |
| **Xếp hạng A3** | Volume tính riêng cho từng nước (cả 6 nước). Câu hỏi **gộp mọi nước**, nên PAA tiếng Đức/Pháp vẫn được đếm. | Hạng trung vị, volume rỗng. **Nghiên cứu xong không tự kích recompute.** | Không. |
| Debate: cắt chủ đề "cạnh tranh" | `atom_segment.contested`. | **Không có chỗ nào trong code ghi giá trị vào cột này**, nên bước cắt không bao giờ chạy. Tên miền mua về đang bị bỏ phí (chưa kiểm trên DB live). | Không. |
| **Admin: nghiên cứu Segment** | Bước duy nhất ghi vào `search_demand`. Mỗi lần chạy tối đa 200 địa điểm. Mua 1 SERP **cho mỗi nước** có volume. Map từ khoá do LLM đề xuất không được lưu lại. | Không áp dụng (đây là bước mua). | **Có.** Admin bấm. |

Bằng chứng ngày 08/11: sau một lượt nghiên cứu US cho 154 địa điểm và một recompute chạy tay, Blog của tenant kiểm toán tăng từ **4 lên 31 trên 176 Segment**. Số Segment không có nhu cầu giảm từ 134 xuống 28.

## 2. Thiết kế đề xuất

```
                 ┌──────────── CHỈ MỘT NGƯỜI MUA ────────────┐
Danh sách việc   │ Job nghiên cứu (admin duyệt từng đợt)      │
(view tính được, │  1. Map từ khoá: LLM, 1 lần/địa điểm, LƯU  │
không cần bảng   │     lại (place_keyword + kết quả Jev)      │
hàng đợi):       │  2. Volume: mọi từ khoá × nước được chọn,  │
địa điểm của     │     gói đầy 1.000 từ khoá/task, mỗi nước   │
tour đang chạy   │     một job                                │
− trung chuyển/  │  3. SERP: 1 lần/địa điểm, US/tiếng Anh,    │
  vô danh/mồ côi │     từ khoá tốt nhất có volume>0 ở bất kỳ  │
− đã tươi        │     nước nào, chia lô ~1.500 địa điểm      │
                 │  4. keywords_for_keywords: TẮT             │
                 └─────────────────┬──────────────────────────┘
                                   ▼
          acp_contract.search_demand  (từ khoá × nước)
          volume 6 nước + PAA / related searches / tên miền
          (lưu trên dòng US, kèm ngày lấy PAA và vị trí lấy)
                                   │
          ┌────────────────────────┼─────────────────────────┐
          ▼                        ▼                         ▼
  Recompute (gộp, 1 lần     Hàm đọc chung              Slate T7
  sau mỗi đợt mua)          demand_profile(tour,       MAX nhu cầu qua
  → xếp hạng A3 → Slate     các nước) → S1, T2,        các nước của đại lý
                            T8, T9, kế hoạch quý       + lý do no_data /
                            (miễn phí, không lưu       below_bar
                            bảng riêng)
```

Các điểm chính:

- **Một người mua.** Chỉ job nghiên cứu (và script bù câu hỏi đang có) được tạo client DFS. Một test import sẽ chặn mọi module T2, T7, T8, T9, S1 hay prefetch tự mua.
- **Một kho.** Mọi thứ mua về đều vào `search_demand`. `seo_context` chỉ còn là bản chép từ kho, để trang admin và file DOCX vẫn chạy được.
- **Hàng đợi là một view, không phải bảng.** Danh sách việc được tính từ: địa điểm của tour đang chạy, trừ những nơi đã tươi theo từng tầng (volume, PAA), cộng những nơi chưa có map từ khoá. Atomize lại hay đổi tên địa điểm thì nơi đó tự hiện ra trong danh sách. Không có bảng hàng đợi nên không có gì bị lệch.
- **Liên kết với recompute.** Mỗi đợt mua thành công gọi một recompute nền tảng có debounce, dùng cơ chế gộp đã có. Recompute chạy ngoài giờ làm việc, vì một recompute lớn có thể dài vài giờ và chặn deploy theo luật DM-11.4.
- **Ngân sách và an toàn:**
  - Bỏ trần 200 địa điểm, thay bằng **trần USD cho mỗi job**.
  - Kiểm số dư DFS **so với dự toán của job**. Hôm nay code so với "ngân sách còn lại", nên các job nhỏ sẽ bị từ chối oan khi số dư thấp.
  - Mỗi dòng sổ chi phí ghi `job_id` và lý do mua.
  - **Không ghi log "đã nghiên cứu" khi DFS lỗi hoặc hết tiền.** Đây đúng là kiểu hỏng của ngày 25/09.
  - Trần mặc định hiện tại (5 USD/job, 10 USD/ngày; chưa đọc dòng live) được **giữ nguyên**. Job được chia nhỏ để vừa trần.
- **Không tự tiêu tiền.** Hệ thống chỉ tự lập "kế hoạch chờ duyệt" kèm dự toán, miễn phí. Anh bấm duyệt thì mới mua.

## 3. Mỗi bước được gì

**S1 (catalogue AA)**: thôi mua.
- `process_seo` và `s1_seo_prefetch` dựng gói SEO miễn phí từ kho: từ khoá có volume của các địa điểm trong tiêu đề tour và trong atom, PAA tiếng Anh, related searches, mức liên quan. Gói giữ nguyên dạng cũ, nên writer v2, writer cũ, flag_fix và brand_audit không cần đổi.
- Đường mua live đặt sau công tắc `S1_SEO_LIVE_BUY`, mặc định tắt. Khi bật, kết quả mua phải ghi vào kho chung.
- Tiết kiệm: một lần chạy lại toàn catalogue khi `seo_context` đã hết hạn (khoảng tháng 4/2027) hôm nay tốn **13 USD (mua theo lô) đến 82 USD (892 tour × 0,092)**. Với thiết kế mới là **0 USD**.
- Ba lỗ hổng các giám khảo chỉ ra, và cách vá:
  1. **Tour mới chưa có atom**, vì S1 chạy trước atomize. Cách vá: lấy địa điểm từ văn bản nguồn của tour (dùng `seed_builder` có sẵn), rồi tra kho theo các tên đó. Không khớp gì thì viết không từ khoá, lần chạy sau sẽ có.
  2. **Mất từ khoá cấp tour**, kiểu "bhutan cultural tour". Cách vá: thêm cụm "nước + hoạt động" và tên địa điểm trong tiêu đề làm từ khoá chỉ mua volume. Khoảng 1.800 từ khoá, tức 2 task mỗi nước, **khoảng 1 USD cho 6 nước**. Các cụm này vẫn có volume trong kho, nên S1 vẫn có từ khoá "đầu" để viết title.
  3. **Không ghi đè dữ liệu tháng 10.** Chỉ gộp thêm vào các ý tưởng cấp tour đã mua. Có thêm bước miễn phí: chép `seo_context` tháng 10 (keyword_ideas, PAA, related) vào `search_demand`, để mọi bước khác cũng dùng được số tiền đã trả.

**T2 (viết lại tour cho đại lý)**: đây là thay đổi quan trọng nhất cho đại lý.
- Đọc **mọi thị trường đại lý khai**, có nước thay thế cho nước chưa hỗ trợ (mục 4). Mỗi từ khoá lấy volume cao nhất trong các nước đó. Hoà nhau thì ưu tiên nước chính của đại lý.
- PAA lấy từ **bất kỳ nước nói tiếng Anh nào**. Như vậy đại lý UK/AU/DE vẫn có câu hỏi, dù SERP chỉ mua một lần ở US.
- Từ khoá qua bộ lọc `relevant_keywords` của S1 v2 (bỏ cụm mang tính mua bán, chỉ giữ cụm có đủ chữ trong nguồn), tối đa 3–5 từ khoá.
- **Nếu ngôn ngữ viết lại không phải tiếng Anh**, không đưa từ khoá DFS vào prompt. Có thể chỉ giữ tên địa điểm, vì tên không đổi theo ngôn ngữ. Từ khoá tiếng Anh không bao giờ nằm trong meta tiếng Đức được, nên đưa vào chỉ để bị trừ điểm.
- **Luật trừ 1,0 điểm (`DFS_INTENT_UNDERUSED`)**: chỉ trừ khi đã có một từ khoá hợp lệ mà writer bỏ qua, hoặc chuyển sang chỉ báo cáo cho T2. Phạt này **đang chạy hôm nay** với các tour S1 viết lại hồi tháng 10 (nhãn `admin_us_fallback`). Vì vậy phải sửa trước khi có thêm dữ liệu.
- Nhãn nguồn ghi vào kết quả job: `tenant_market`, `proxy_market`, `platform_us` hoặc `none`. T2 vẫn không gọi DFS.

**T7 Slate**:
- Thanh chắn Blog đọc **MAX nhu cầu qua các nước của đại lý**, không còn đọc nước có hạng tốt nhất.
- Lý do trượt được tách ra: `no_data` (chưa có số), `below_bar` (có số nhưng thấp), `few_questions` (thiếu câu hỏi). Lý do này chỉ dành cho nội bộ và admin, vì tenant chỉ thấy nội dung.
- Thứ tự xếp hạng không đổi.

**T7 kế hoạch quý**: mức HIGH/MED/LOW tính từ volume cao nhất của tour trong các nước của đại lý. `seo_context` chỉ còn là đường lùi.

**T8 góc viết**:
- Tín hiệu "nhu cầu tìm kiếm" lấy từ hàm đọc chung theo nước của đại lý. Tour S1 chưa từng mua giờ cũng có khối này, miễn là kho biết các địa điểm của tour.
- Chỉ lùi về `seo_context` khi **không có dòng nào**. Không dựa vào `expires_at` 7 ngày, vì gần như dòng nào cũng đã "quá hạn" theo trường đó.

**T9 viết blog**:
- Ứng viên từ khoá lấy từ các địa điểm của chính bài viết (ý `keyword_by_place` của hướng B), cộng related searches. Luật `choose_keyword` giữ nguyên.
- Chuỗi FAQ không đổi. Nó vốn đã đọc mọi nước và chỉ giữ tiếng Anh, nên một SERP tiếng Anh cho mỗi địa điểm đã nuôi được FAQ cho mọi đại lý.

**Xếp hạng A3**: volume vẫn tính cho cả 6 nước, chỉ là giờ có số thật. Recompute tự chạy sau mỗi đợt mua. Việc lọc câu hỏi chỉ tiếng Anh làm thành issue riêng, vì nó đổi kết quả Slate (mục 7).

**Hàm đọc chung `demand_profile`**:
- Nối địa điểm với từ khoá qua bảng `place_keyword` và kết quả duyệt của Jev, không so tên bằng ILIKE. Nhờ vậy "Kyoto" (165 nghìn lượt) không bị gán nhầm cho "Kyoto làm nhang".
- Có trạng thái độ phủ `ok`, `thin` hoặc `empty`, ghi vào kết quả job. Ý này lấy từ hướng B.
- Trả cả `keyword_ideas` có volume, để `dfs_relevance` vẫn chia được mức HIGH/MED/LOW.

## 4. Chính sách thị trường

- **6 nước mặc định** là US, UK, AU, DE, FR, NL. Đại lý đang khai: UK 4, AU 4, US 3 (cộng 4 không khai, mặc định US), DE 3, FR 3, NL 3.
- **Volume**: mua cho các nước được duyệt, mỗi nước khoảng 1,7 USD cho một lượt đầy đủ. Đây không phải khoản chính.
- **SERP (PAA, related searches, tên miền)**: **mua 1 lần cho mỗi địa điểm**, US/tiếng Anh, không bao giờ mua theo từng nước. Lý do: nội dung viết bằng tiếng Anh, T9 vốn đã bỏ PAA không phải tiếng Anh, và SERP của DE/FR/NL ra phần lớn câu hỏi tiếng Đức/Pháp/Hà Lan.
- **Ngưỡng mua SERP là volume > 0**, không phải ≥100. Các giám khảo phản đối ngưỡng 100: PAA của các địa điểm ít lượt tìm vẫn nuôi FAQ của Route và T2.
- **DE/FR/NL** hôm nay chỉ mua volume cho từ khoá tiếng Anh, với `language_code 'en'`. Kết quả có thể phần lớn là 0 hoặc rất nhỏ. Vì vậy **thử trước** bằng 1 task mỗi nước trên khoảng 300 địa điểm (0,27 USD) rồi mới quyết mua đủ (5,13 USD). Có thể thử thêm cách bỏ lọc ngôn ngữ (cần kiểm tài liệu DFS).
- **Nước chưa hỗ trợ dùng nước thay thế (proxy):** CA→US, NZ→AU, SG/HK/AE→UK. Hiện có 7 lượt khai: CA 2, SG 2, AE 1, HK 1, NZ 1. Nhãn kiểu "dữ liệu UK dùng cho Singapore" chỉ hiện trong admin và trong lý do Slate nội bộ. `unmapped_market_requests` tiếp tục là hàng đợi. Chỉ thêm nước thật khi có đại lý trả tiền cần nó, khoảng 1,7 USD lần đầu cộng phần làm mới.
- **Rủi ro chấp nhận:** đại lý UK/AU nhận PAA US. Câu hỏi về địa điểm phần lớn dùng chung được, nhưng có câu mang tính Mỹ (visa, chuyến bay). Nếu một đại lý trả tiền cần, có thể mua thêm SERP UK/AU cho top địa điểm của họ, 0,002 USD mỗi địa điểm.

## 5. Làm mới dữ liệu

| Lớp dữ liệu | Hạn | Ghi ở đâu |
|---|---|---|
| Map từ khoá của địa điểm | Vĩnh viễn. Đề xuất lại chỉ khi địa điểm mới, đổi tên, hoặc tăng phiên bản prompt. Đổi tên thì mang map theo qua alias của Segment. | `place_keyword` (mới) |
| Volume | **Đề xuất 365 ngày** (hôm nay là 182). Volume của Google Ads là trung bình 12 tháng nên làm mới 2 lần/năm gần như không mua được gì mới. Từ khoá volume 0 cũng 365 ngày. | `segment_research_log`, thêm cột tầng (tier) |
| PAA, related searches, tên miền | 365 ngày | cột mới `paa_retrieved_on`. Migration chép giá trị từ `retrieved_on`. |
| Gói SEO của tour | Không có hạn riêng. Dựng lại mỗi lần đọc. | không lưu bảng |

**Cái gì tự động (đều miễn phí):**
- Atomize lại, gộp hoặc dời địa điểm: view danh sách việc tự cập nhật. Cuối mỗi job như vậy, một hàm cập nhật dự toán chạy ở chế độ cố gắng hết sức: không bao giờ làm hỏng atomize, và có gộp nhiều lần gọi thành một.
- Kiểm hằng ngày (chỉ đọc): tỉ lệ địa điểm cũ theo từng nước và từng tầng. Vượt ngưỡng thì báo qua `ops_checks.alert_all` (chuông admin + 1 email SNS mỗi ngày) và hiện số trên trang độ phủ dữ liệu. Job worker trong repo public không có token để mở issue GitHub.
- Sau mỗi đợt mua: tự gọi một recompute có debounce.

**Cái gì anh duyệt:**
- **Kế hoạch tháng**, đề xuất ngày 1. Gồm địa điểm mới, cộng **khoảng 1/12 catalogue cũ nhất**, để không bị một cú làm mới 10–11 USD cùng lúc vào tháng 5/2027. Trần 5 USD/tháng. Không có khoản tự động tiêu: anh bấm thì mới mua.
- Trước một wave S1: một lượt nghiên cứu cho riêng các tour trong wave, có báo giá. Thường gần 0 USD vì lượt đầu đã phủ.
- Chạy theo tháng, không theo tuần, vì mỗi lần chạy tốn ít nhất 1 task cho mỗi nước (0,54 USD cho 6 nước).

## 6. Dự toán chi phí đầy đủ 6 thị trường

**Tỉ lệ đo ngày 08/11** (154 địa điểm US):
- 395 từ khoá, tức **2,565 từ khoá/địa điểm**;
- 119 SERP, tức **77,3% địa điểm có SERP**;
- LLM 0,039 USD, tức **0,000253 USD/địa điểm**.

**Số địa điểm cũ** (stale): US 6.962; UK và AU 7.145; DE, FR và NL 7.243. Trong phạm vi: 7.323. Đây là số **trước** khi lọc bỏ địa điểm trung chuyển, vô danh và mồ côi, nên mọi con số dưới đây là mức trên. R0 sẽ đo số thật miễn phí.

**Cách tính:**
- Số task volume = làm tròn lên (địa điểm cũ × 2,565 / 1.000). Mỗi task 0,09 USD.
- SERP = 7.323 × 0,773 × 0,002.
- Trần = 4 từ khoá/địa điểm (giới hạn `KEYWORDS_PER_PLACE` trong code), cộng SERP cho mọi địa điểm.

**Lần đầu, theo giá live:**

| Hạng mục | US | UK | AU | DE | FR | NL | Chung | Tổng |
|---|---|---|---|---|---|---|---|---|
| Volume (mức thật) | 1,62 (18 task) | 1,71 (19) | 1,71 | 1,71 | 1,71 | 1,71 | | **10,17** |
| Volume (trần, 4 từ khoá/địa điểm) | 2,52 | 2,61 | 2,61 | 2,61 | 2,61 | 2,61 | | 15,57 |
| SERP, 1 lần/địa điểm | | | | | | | 11,32 (trần 14,65) | **11,32** |
| Map từ khoá LLM, 1 lần cho mọi nước | | | | | | | 1,85 (trần 10,25) | **1,85** |
| Từ khoá "nước + hoạt động" cho S1 | | | | | | | ≈1 | ≈1 |
| **Tổng mức thật** | | | | | | | | **≈23,3** (DFS 21,5 + LLM 1,85), cộng ≈1 nếu thêm từ khoá S1 |
| **Tổng trần** | | | | | | | | **DFS ≈30,2 (> số dư 27,41)**, tất cả ≈40,5 |

**Theo đợt, và số dư DFS sau mỗi đợt** (LLM trả qua AI gateway, không trừ vào số dư DFS):

| Đợt | Việc | DFS | LLM | Số dư DFS còn lại (mức thật / trần) |
|---|---|---|---|---|
| R0 | Xem trước với phạm vi mới, đo chi phí Jev, đo số từ khoá/địa điểm gộp, đối chiếu số dư | 0 | 0 | 27,41 |
| R1 | Map từ khoá + volume US, UK, AU (mỗi nước một job, vừa trần 5 USD/job) | 5,04 | 1,85 | 22,37 / 19,67 |
| R2 | SERP, chia khoảng 5 lô × 1.500 địa điểm (≈2,3 USD/lô, vừa trần 10 USD/ngày) | 11,32 (có thể 11,3–12,5, vì "có volume ở bất kỳ nước nào" ≥77,3%) | 0 | 11,05 / 5,02 |
| R3 | Thử DE/FR/NL (0,27), rồi mới quyết mua đủ | 0,27, sau đó tới 5,13 | 0 | 5,9 / không đủ nếu chạm trần |

- Số dư còn bị trừ thêm một khoản rò ngoài sổ, khoảng 0,7–1,5 USD (đã thấy ngày 27/10, 28/10 và 01/11). Nghi phạm cần kiểm: connector DataforSEO trên claude.ai dùng chung tài khoản DFS (**chưa kiểm**).
- **Cần nạp thêm DFS** trước kế hoạch tháng đầu tiên, hoặc trước R3 nếu R1/R2 chạm trần.

**Đòn bẩy lớn nhất (chưa kiểm):**
- Hôm nay mọi lệnh gọi đều dùng endpoint `/live`. DFS có thêm **Standard queue**: gửi task, chờ, rồi lấy kết quả; việc hỏi trạng thái miễn phí. Việc nghiên cứu là xử lý theo lô, không ai ngồi chờ, nên chậm không sao.
- Giá theo trí nhớ của giám khảo, **phải kiểm bằng 1 task thử**: SERP khoảng 0,0006 thay vì 0,002; volume khoảng 2/3 giá live.
- Nếu đúng: SERP còn khoảng 3,4 USD, volume khoảng 6,8 USD, **DFS lần đầu khoảng 10 USD thay vì 21,5**. Khi đó ngưỡng SERP ≥100 cũng không còn đáng làm.

**Hằng tháng** (giả định khoảng 300 địa điểm mới/tháng, chưa đo):

| Khoản | Cách tính | USD/tháng |
|---|---|---|
| Volume địa điểm mới | 1 task/nước × 6 nước × 0,09 | 0,54 |
| SERP địa điểm mới | 300 × 0,773 × 0,002 | 0,46 |
| LLM địa điểm mới | 300 × 0,000253 | 0,08 |
| Làm mới volume, cuốn chiếu 365 ngày | 10,17 / 12 | 0,85 |
| Làm mới PAA, cuốn chiếu 365 ngày | 11,32 / 12 | 0,94 |
| **Tổng (đề xuất)** | | **≈2,9** (≈35 USD/năm) |
| Nếu giữ hạn volume 182 ngày | | ≈3,6 |
| Gói tiết kiệm: chỉ địa điểm mới, làm mới duyệt riêng | | ≈1,1 |

- Nước không có đại lý thật có thể bỏ làm mới volume, giảm thêm khoảng 0,14 USD/nước/tháng.
- **So với cách hôm nay** trên cùng phạm vi (SERP theo nước, trần 200 địa điểm/lần, gợi ý từ khoá bật): các giám khảo tính ra từ **khoảng 45 đến 95 USD** tùy cách chạy. Điểm chắc chắn: đắt hơn ít nhất gấp đôi. Gần như toàn bộ khoản tiết kiệm đến từ "1 SERP cho mỗi địa điểm" và "bỏ trần 200".

**Chưa tính, phải đo trước khi duyệt R1:**
- Chi phí Jev cho khoảng 18–29 nghìn lần duyệt từ khoá, cộng phần Jev và Cohere (embedding câu hỏi) trong recompute sau đợt mua. Đọc miễn phí từ `llm_call_log` của job 287e1c14. Jev có trần ngày: nếu chạm giữa chừng thì job dừng, nên phải chia lô theo ngày.
- Giá một task đầy 1.000 từ khoá: task lớn nhất từng thấy chỉ 395 từ khoá. Task đầu tiên của R1 phải được kiểm trong `dfs_call_log`, và dừng ngay nếu tính quá 0,10 USD.
- LLM 1,85 USD đo trên Haiku. acc3 đang bị chặn, nên tuyến thật đi qua gateway (OpenAI hoặc acc2) và giá có thể khác.

## 7. Thay đổi code theo đợt

**PR 1: sửa phía đọc, không migration. Ship TRƯỚC mọi đợt mua.**
- T2: lọc `relevant_keywords` (chuyển hàm sang `services/seo_intelligence/keyword_fit.py` để dùng chung), chặn theo ngôn ngữ viết lại, đổi luật trừ điểm `DFS_INTENT_UNDERUSED` cho T2.
- Slate: MAX nhu cầu qua các nước của đại lý, tách lý do `no_data` / `below_bar` / `few_questions`.
- Test import: không bước nào ngoài job nghiên cứu được tạo client DFS.
- Rủi ro: thấp–vừa. Kết quả Slate đổi (nhiều Blog hơn). So sánh trên tenant kiểm toán trước và sau.

**PR 2: phía mua, có migration (thuộc nhóm rủi ro, cần reviewer độc lập).**
- Migration CIS: bảng `place_keyword` (có kết quả Jev và phiên bản prompt; khoá chấp nhận cả cụm "nước + hoạt động" không gắn địa điểm); thêm vào `search_demand` các cột `related_searches`, `paa_retrieved_on`, `serp_location`; thêm cột tầng vào `segment_research_log`, kèm backfill.
- Phạm vi qua `v_active_tour_atoms` và `resolve_exclusions`. SERP 1 lần/địa điểm, bỏ qua chỉ khi cả PAA lẫn related searches còn tươi (để bổ sung related searches cho 154 địa điểm đã mua). Mặc định tắt gợi ý từ khoá. Thay trần 200 địa điểm bằng trần USD. Dự toán gồm mức thật và mức trần (4 từ khoá/địa điểm).
- Kiểm số dư theo dự toán. Không ghi log khi lỗi. Ghi log theo từng địa điểm ngay khi xong, để job có thể chạy tiếp sau khi hỏng. Tách đôi task 1.000 từ khoá khi bị lỗi. Làm sạch từ khoá trước khi gửi.
- Nghiên cứu xong tự gọi recompute có debounce. Script miễn phí chép `seo_context` tháng 10 vào kho.
- Nếu anh duyệt: client Standard queue cho volume và SERP.
- Đợi PR `bot/db-schema-reference` merge xong mới code dựa trên cột mới. DB Migrate chỉ chạy khi các bảng job rảnh.
- Rủi ro: vừa. Job dài: phải chia lô và chạy ngoài giờ.

→ **Chạy R0, rồi R1, recompute, đo Blog; rồi R2, recompute, đo lại.**

**PR 3: mọi writer đọc kho.**
- Hàm `demand_profile`. S1 chỉ đọc (công tắc mua tắt, xử lý tour mới, gộp không ghi đè). `s1_seo_prefetch` chuyển thành job miễn phí. T2 đọc nhiều nước. T8 và T9 lùi về kho khi không có `seo_context`. Kế hoạch quý đọc kho. Thêm bảng nước thay thế.
- Trước khi bật S1 hẳn: thử 3 tour, so `seo_keywords_used` và số lần bị trừ điểm.
- Rủi ro: vừa. Chất lượng meta S1/T2 có thể đổi; theo dõi bằng phép thử 3 tour.

**PR 4: làm mới và giám sát.**
- View danh sách việc, hàm cập nhật dự toán (gắn vào atomize, gộp và dời địa điểm), kế hoạch tháng với nút duyệt trong admin, trang độ phủ dữ liệu, kiểm hằng ngày qua `alert_all`, đối chiếu số dư DFS với sổ chi phí sau mỗi job (lệch quá 0,10 USD thì báo).
- Nếu có job kind mới, phải khai rõ là chặn hay không chặn deploy, và sửa danh sách miễn trừ bên Infra trong cùng đợt.
- Rủi ro: thấp.

**Issue riêng, làm sau và chạy chế độ shadow trước:**
- Ghi cột `contested` để bước cắt của Debate chạy được.
- Lọc câu hỏi chỉ tiếng Anh trong xếp hạng.
- Cả hai đổi kết quả Slate, nên phải đo riêng từng cái. Không gộp vào đợt này.

## 8. Các quyết định cần anh duyệt

1. **Chọn thiết kế A cộng các phần ghép thêm** như trên. Đề xuất: **duyệt**. Chi phí code: 4 PR. Không tốn tiền dịch vụ.
2. **Thử Standard queue** bằng 1 task volume và 1 task SERP (khoảng 0,1 USD). Nếu giá đúng thì chuyển R1/R2 sang queue. Đề xuất: **duyệt**. Có thể tiết kiệm khoảng 11 USD lần đầu và khoảng 1/3 chi phí hằng tháng.
3. **R0 (0 USD) và R1 (DFS 5,04 + LLM 1,85, trần job DFS 5 USD mỗi nước)** sau khi PR 1 và PR 2 đã chạy live. Đề xuất: **duyệt**. Dừng nếu chi phí Jev đo ở R0 bất thường, hoặc task đầu tiên tính quá 0,10 USD.
4. **R2: SERP 1 lần/địa điểm, ngưỡng volume > 0**, khoảng 11,3 USD live (trần 14,65) hoặc khoảng 3,4 USD theo queue. Báo giá chính xác có ngay sau R1. Đề xuất: **duyệt ngưỡng > 0, không dùng ≥100**.
5. **DE/FR/NL**: thử 0,27 USD trước, mua đủ 5,13 USD chỉ khi tỉ lệ có số đủ cao. Đề xuất: **thử trước, chưa mua đủ**.
6. **Thanh chắn Blog**: giữ mức tuyệt đối 1.000 hay chuyển sang mức tương đối theo nước (ví dụ top 25% của nước đó, có sàn). Đề xuất: **giữ 1.000 cho tới sau R2, đo xong rồi quyết**. Đây là quyết định sản phẩm. Không tốn tiền.
7. **Luật trừ điểm của T2**: chỉ trừ khi đã có từ khoá hợp lệ mà writer bỏ qua; viết lại bằng ngôn ngữ khác tiếng Anh thì không đưa từ khoá DFS. Đề xuất: **duyệt, ship trong PR 1**. Không tốn tiền.
8. **Bảng nước thay thế** CA→US, NZ→AU, SG/HK/AE→UK, nhãn chỉ trong nội bộ và admin. Đề xuất: **duyệt**. Không tốn tiền.
9. **Làm mới**: volume 365 ngày, PAA 365 ngày, kế hoạch tháng cuốn chiếu do anh bấm duyệt, trần 5 USD/tháng, không có khoản tự động tiêu. Đề xuất: **duyệt**. Khoảng 2,9 USD/tháng, hoặc khoảng 1,1 USD theo gói tiết kiệm.
10. **Trần chi tiêu**: giữ 5 USD/job và 10 USD/ngày, chia job cho vừa (không nâng trần). Đề xuất: **duyệt**. Không tốn tiền.
11. **Nạp thêm DFS**: quyết sau R2. Mức thật còn khoảng 11 USD; nếu chạm trần chỉ còn khoảng 5 USD. Đề xuất: **quyết sau R2**.
12. **Từ khoá "nước + hoạt động" cho S1** (khoảng 1 USD cho 6 nước, đi cùng R1 cho 3 nước). Đề xuất: **duyệt**.
13. **Tìm khoản rò ngoài sổ** (kiểm connector DataforSEO trên claude.ai và mọi công cụ dùng chung tài khoản). Đề xuất: **làm ngay**. Không tốn tiền.
14. **Google Ads Keyword Planner**: miễn phí khi có tài khoản Ads, nhưng không có PAA hay tên miền, cần developer token cấp Basic cộng OAuth và tài khoản quản lý. Tài khoản ít chi quảng cáo chỉ nhận khoảng số (ví dụ 1K–10K), đủ cho thanh chắn ≥1.000 nhưng không đủ cho trục xếp hạng. Có quota và điều khoản cần đọc. Thay được tối đa khoảng 10 USD mỗi lượt volume. Đề xuất: **chưa làm**. Chỉ xem lại nếu làm mới volume trở nên thường xuyên.

## 9. Vì sao không chọn 2 hướng còn lại

**Hướng B: lưu sẵn một gói SEO cho mỗi (tour × nước) trong bảng `tour_seo_pack`.**
- Chi phí DFS bằng hướng A, vì khoản tiết kiệm đều đến từ "1 SERP cho mỗi địa điểm". Đổi lại phải thêm một bảng, job dựng lại, quét đêm, dấu vân tay và 5 loại kích hoạt.
- Kiểm dấu vân tay tốn gần bằng dựng lại gói. Các bước của tenant sẽ phải ghi vào bảng nền tảng (cần cấp quyền mới). Gói bị ghi đè làm hỏng khả năng phát lại prompt T2.
- Đã lấy từ B:
  - chép miễn phí `seo_context` tháng 10 vào kho;
  - log độ tươi theo từng tầng (volume và PAA riêng);
  - trạng thái độ phủ `ok`/`thin`/`empty`;
  - `keyword_by_place` cho T9;
  - nối từ khoá chính xác qua map, không dùng ILIKE.

**Hướng C: mua SERP chỉ cho "danh sách rút gọn Blog", cộng hàng đợi do tenant kích.**
- Chỉ rẻ hơn A khoảng 6 USD một lần theo giá live. Theo giá queue thì không rẻ hơn.
- Việc mua bị móc vào thanh chắn Blog, vốn chưa được quyết. Pass đầu phải chạy chuỗi: volume, recompute, tính thanh chắn, SERP, recompute.
- Hàng đợi do tenant ghi **mở lại đường "hành động của tenant dẫn tới tiêu tiền"**. Đó đúng là bài học AA-646 của vụ 49 USD ngày 25/09.
- Thêm 4 bảng mới.
- Đã lấy từ C:
  - không ghi log khi DFS lỗi hoặc hết tiền;
  - gắn tầng, job và tenant vào sổ chi phí;
  - S1 dựng `seo_context` từ kho;
  - giữ ý thanh chắn Blog tương đối theo nước làm quyết định số 6.

**Ý của các giám khảo ghép vào A** (chung cho cả ba hướng):
- thử Standard queue;
- trần tính với 4 từ khoá/địa điểm;
- đo chi phí Jev trước khi duyệt;
- chia job cho vừa trần 5 và 10 USD;
- kiểm số dư theo dự toán;
- volume làm mới 365 ngày;
- làm mới cuốn chiếu, tránh một cú lớn cùng lúc;
- thử DE/FR/NL trước khi mua;
- chặn theo ngôn ngữ cho T2;
- vá lỗ hổng tour mới của S1;
- báo động qua `alert_all` thay vì issue GitHub;
- tách ghi `contested` và lọc câu hỏi tiếng Anh thành issue riêng.

Ba hướng có điểm giám khảo gần nhau. Điểm "đơn giản" đều thấp, khoảng 4/10. A thắng vì phủ đủ mọi writer với ít phần chuyển động nhất. Bản ghép ở trên còn cắt bớt độ phức tạp của A: không có bảng `research_plan`, không có khoản tự động tiêu, và ship theo 4 PR mỏng.