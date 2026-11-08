# Kiểm toán chi phí DataForSEO (S273, 08/11/2026)

> Chỉ đọc mã nguồn, lịch sử git và sổ chi phí. Không gọi AWS, không gọi DataForSEO, không gọi LLM.
> Số liệu sổ chi phí lấy từ bảng `shared.dfs_call_log`, tính từ 19/09, do orchestrator kéo ra (`.tmp-session/S273/dfs/dfs_spend.out`).
> Đường dẫn mã nguồn tính từ `apps/AA-CIS-App/`, trừ khi ghi khác.
> Chỗ nào ghi **"chưa kiểm được"** là chưa có bằng chứng chắc.

## Tóm tắt 5 dòng

1. Từ 19/09 tới nay đã tiêu **71,49 USD** cho DataForSEO (DFS). Riêng ngày **25/09 tốn 49,02 USD (69%)**.
2. Ngày 25/09 tốn nhiều vì một lỗi kích hoạt. Hồi đó, mỗi lần tenant bấm "viết lại tour" (T2) thì hệ thống tự đi nghiên cứu **toàn bộ 2.215 địa điểm của cả nền tảng × 3 thị trường US/UK/AU**. Cách mua lúc đó lại rất phí: mỗi lượt gửi chỉ chở trung bình 4,5 từ khoá, trong khi một lượt chở được 1.000.
3. **Hôm nay tenant viết blog KHÔNG làm chạy DFS.** Mọi đường của tenant (T2, T7, T8, T9) chỉ đọc dữ liệu đã mua sẵn. Hai bản sửa: 28/09 (`b0dd9bea1`) và 29/09 (`d3921934b`).
4. Tiền DFS tháng 10 (khoảng 18,6 USD) là do viết lại catalogue của chính AA (S1, AA-653), không phải do tenant. Hôm nay chỉ có 3 đường còn mua DFS, và cả 3 đều do admin bấm.
5. Vấn đề thật hôm nay là **thiếu dữ liệu chứ không phải tốn tiền**. Chỉ 8.662 trên 97.218 dòng xếp hạng có số lượt tìm, nên Blog hiếm khi có chủ đề. Đề xuất: một lượt nghiên cứu US có kiểm soát, khoảng **15–24 USD** theo giá thật đo hôm nay. Phải được anh duyệt trước.

## 1. DFS dùng để làm gì, "thị trường" là gì

**DFS (DataForSEO)** là dịch vụ trả phí, cho biết người ta gõ gì lên Google về các địa điểm trong tour của mình. Mình hỏi nó 3 loại câu:

| Hỏi DFS | Tên endpoint | Trả về |
|---|---|---|
| Cụm này mỗi tháng được tìm bao nhiêu lần? | `search_volume` | số lượt tìm / tháng |
| Người ta còn gõ những cụm liên quan nào? | `keywords_for_keywords` | danh sách từ khoá liên quan kèm số lượt tìm |
| Google hiện câu hỏi "Mọi người cũng hỏi" (PAA) nào, web nào đứng đầu? | `serp_advanced` | câu hỏi PAA + tên miền đứng top |

**"Thị trường" (market)** đơn giản là **nước của người đang tìm kiếm**. Cùng cụm "Tiger's Nest hike", số lượt tìm ở Mỹ khác ở Anh. Mã nguồn hỗ trợ 6 thị trường: US, UK, AU, DE, FR, NL (`services/seo_intelligence/seed_builder.py:50-57`).
- Thị trường lấy từ cấu hình của tenant (`target_market.countries`). Tenant không khai thì mặc định là US (`seed_builder.py:72, 390-445`).
- Khi admin chạy nghiên cứu, admin phải gõ rõ thị trường nào (`api/routers/admin_segment_research.py:46-63`).
- DFS bắt **mỗi thị trường một lượt gửi riêng**: một lượt chỉ hỏi được một nước (`services/seo_intelligence/dataforseo_client.py:269-294`).

Đường đi của dữ liệu:

```
Tour
 └─> Địa điểm trong tour (vd. "Paro Taktsang")
      └─> Từ khoá (vd. "tiger's nest hike")
           └─> [DFS, mỗi thị trường US/UK/AU... một lượt riêng]
                ├─> Số lượt tìm / tháng
                └─> Câu hỏi "Mọi người cũng hỏi" + web đứng top
                     └─> Lưu vào kho search_demand (dùng lại 182 ngày)
                          ├─> Xếp hạng Segment (trục "nhu cầu" + trục "câu hỏi")
                          └─> Chủ đề Blog: chỉ được đề xuất khi ≥1000 lượt tìm VÀ ≥3 câu hỏi
```

*Segment* là một cặp "địa điểm + hoạt động" trong tour, ví dụ "leo núi ở Paro".

**Kho lưu**
- `acp_contract.search_demand`: mỗi dòng là một (từ khoá, thị trường), không có cột tenant, nên mọi tenant dùng chung.
- `acp_contract.segment_research_log`: ghi (địa điểm, thị trường) nào đã nghiên cứu. Còn "tươi" trong 182 ngày (`services/acp_contract/segment_research.py:75, 597-608`).
- `silver_aa_internal.seo_context`: kho riêng theo từng tour, cho đường S1.

**Ai dùng kho này** (tất cả chỉ ĐỌC, không gọi DFS):
- **Xếp hạng (A3).** Chạy cho cả 6 thị trường (`services/recompute/stages.py:158-165`). Segment chưa đo nhu cầu thì nhận hạng "trung vị", không bị loại (`services/acp_contract/atom_ranking.py:144-153, 193-263`).
- **Thanh chắn Blog ở Slate (T7).** Cần nhu cầu ≥1000 và câu hỏi ≥3. Thiếu số liệu bị tính là 0, nên **trượt Blog** (`services/acp_shared/slate.py:115-140, 190-213`). Lý do trượt có được ghi lại nội bộ, nhưng tenant không bao giờ thấy chủ đề đó. Kênh mạng xã hội chỉ cần "said ≥150". Email/Landing/Ads không có thanh chắn.
- **Góc viết (T8).** Không có dữ liệu thì bỏ hẳn khối "nhu cầu tìm kiếm" khỏi prompt (`services/acp_angle_gate/service.py:308-323`, `services/acp_shared/dfs_relevance.py:154-162`).
- **FAQ blog (T9).** Lấy câu hỏi thật từ DB theo thứ tự: Segment → PAA của địa điểm → câu hỏi admin mua bù → PAA của tour (`services/acp_content_writing/service.py:1828-1844`, `services/acp_shared/real_questions.py:1-26`). Không có câu hỏi thật thì AI có tự viết FAQ hay không: chưa kiểm được trọn.
- **Viết lại tour cho tenant (T2).** Đọc từ khoá theo thị trường của tenant trong search_demand. Không có thì lấy bản US. Vẫn không có thì viết không cần từ khoá (`services/seo_intelligence/s1_prefetch.py:421-467`, `services/jobs/t2_rewrite_job.py:149-203`).
- **"Contested" ở Slate.** Dùng tên miền top trong search_demand. Thiếu dữ liệu thì không bao giờ cắt (`atom_ranking.py:389-405`, `slate.py:643`). Điểm này do bước kiểm chứng bổ sung.

**Dữ liệu đang có theo thị trường** (số dòng trong search_demand): US 2.000 dòng (785 dòng có số lượt tìm), UK 1.484, AU 1.214, DE/FR/NL mỗi nước 263. Số 2.000 của US là số thật, không phải giới hạn truy vấn (`.tmp-session/S273/dfs/dfs_spend.py:47-52`).

## 2. Đã tiêu bao nhiêu, vào việc gì

Tổng sổ chi phí: **71,49 USD**. Trong đó 52,00 USD không gắn tenant và 19,49 USD gắn tenant.

| Ngày | Việc | Số lần gọi | USD | Vì sao |
|---|---|---|---|---|
| 21/09 | 5 tour lấy SEO theo kiểu cũ (3 lượt mua/tour) | 16 | 0,91 | Có thể là S1, cũng có thể là đường T2 cũ (T2 tự gọi `process_seo` khi thiếu dữ liệu). **Chưa kiểm được** là đường nào. |
| **25/09** | **Nghiên cứu toàn nền tảng: 2.215 địa điểm × AU/US/UK** | **1.169** | **49,02** | Tenant thử nghiệm (WanderLux) bấm viết lại tour (T2). 35 giây sau, nghiên cứu tự chạy, 2 đợt (563 + 605 lần gọi). Chia ra: số lượt tìm 39,24 + từ khoá liên quan 9,00 + SERP 0,84. Sổ ghi "không tenant", vì đoạn mã nghiên cứu không truyền tenant_id. |
| 25/09 (kèm) | Haiku (AI) chạy vòng nghiên cứu | 7.856 | ~10,27 | Không phải tiền DFS. Theo ghi chú trong mã (`segment_research.py:71-72`). Bảng gốc tính cho 30 ngày, nên con số chính xác của riêng 25/09 **chưa kiểm được**. |
| 28/09 | Thử chế độ "gom lô" ở Bhutan: 50 địa điểm × 3 thị trường | ~99 | 0,55 | Thử cách mua mới (AA-648): 0,27 số lượt tìm + 0,19 SERP + 0,09 từ khoá liên quan. |
| 01–08/10 | Viết lại catalogue của AA (S1, AA-653, 14 nước) | 925 | 18,58 | Chủ yếu là `keywords_for_keywords`: 205 lượt, 16,65 USD cả tháng 10. Theo ngày: 01/10 2,342 · 02/10 0,294 · 03/10 1,132 · 05/10 5,786 · 06/10 0,892 · 07/10 1,460 · 08/10 6,674. |
| 12/10 | Admin nghiên cứu DE/FR/NL | (nằm trong 2,47 USD "khác") | — | Lần chạy tay cuối cùng trước hôm nay. |
| 20/10 | Admin mua bù câu hỏi PAA (script) | 8 | 0,018 | Trần trọn đời 3 USD. |
| **08/11** | Admin nghiên cứu US cho tenant audit (154 địa điểm cũ) | ~125 | 0,508 | 1 lượt số lượt tìm (395 từ khoá, 0,09) + 119 SERP (0,238) + 2 lượt từ khoá liên quan (0,18). Theo bước kiểm chứng là job `287e1c14`. Sổ không có cột job, nên chưa nối trực tiếp được. |
| 27/10, 28/10, 01/11 | **Không có trong sổ** | — | ~0,7–1,5 | Số dư giảm (28,15 → 27,97 → 27,75 → 27,41) vào những ngày sổ không ghi lần gọi nào. Có một nguồn tiêu DFS không đi qua sổ. **Chưa kiểm được** là nguồn nào. |

Số dư tài khoản DFS: khoảng 49 USD trước 25/09 → 24,86 (ảnh chụp 25/09) → **−0,12** (26/09). Nạp thêm lên 49,88 ngày 28/09. **Hiện còn 27,41 USD.**

## 3. Vì sao tốn: nguyên nhân gốc

**Cách DFS tính tiền, nói đơn giản.** DFS tính theo **lượt gửi (task)**, không tính theo số từ khoá. Một lượt hỏi số lượt tìm chở được **tới 1.000 từ khoá cho MỘT thị trường**. Giá mỗi lượt khoảng **0,06–0,09 USD**, dù gửi 1 từ hay 1.000 từ. Giống thuê xe tải: trả tiền theo chuyến, không theo số thùng hàng.
- Trong sổ, lượt gửi 1 từ khoá vẫn bị tính 0,09.
- Riêng ngày 25/09 các lượt nhỏ chỉ bị tính khoảng 0,058. Đây là điểm lạ chưa giải thích được.
- Vậy nên an toàn nhất là coi **0,09 USD/lượt** (`dataforseo_client.py:252-256, 300`; số liệu sổ).

**Các nguyên nhân, xếp theo mức nặng:**

1. **Kích hoạt sai chỗ, không ai quyết định mua.**
   - Trước 28/09, mỗi lần tenant bấm viết lại tour (T2), `v1_tours.py` lại chạy ngầm `run_segment_research` (commit `b0dd9bea1` gỡ đoạn này).
   - Từ 06/09, AA-545 (`15743a96`) đã biến Segment thành dùng chung toàn nền tảng. Câu truy vấn địa điểm không còn lọc tenant (`SELECT canonical_place ... FROM acp_contract.atom_segment`, không có WHERE).
   - Kết quả: một cú bấm của một tenant mua cho cả nền tảng, theo 3 thị trường của chính tenant đó.
   - Đúng điều tài liệu của chị Thư cảnh báo: nghiên cứu phải là việc "chủ động mua", không được nối tự động sau bước khác.

2. **Xe tải chạy gần như rỗng.**
   - Vòng lặp cũ chỉ chạy 4 địa điểm một lúc và chờ cố định 5 giây để gom (`segment_research.py:83, 201-258`).
   - Kết quả: **678 lượt hỏi số lượt tìm, mỗi lượt trung bình 4,5 từ khoá (tối đa 13), tốn 39,24 USD** (`segment_research_batch.py:3-6`).
   - Cũng khoảng 3.050 cặp (từ khoá, thị trường) đó, nếu gom đầy thì chỉ cần khoảng 2 lượt mỗi thị trường, tức khoảng **0,54 USD**.
   - **Phí khoảng 38–39 USD**, tức hơn một nửa tổng tiền DFS từ trước tới nay.

3. **Mua "từ khoá liên quan" từng địa điểm một, gần như vô ích.**
   - AI chọn gọi `keywords_for_keywords` với 1 từ gốc cho mỗi địa điểm không có số liệu. Khoảng 100 lượt × 0,09 = **9,00 USD**.
   - Lượt nào chỉ có 1–4 từ gốc lạ thì DFS chỉ trả lại đúng các từ gốc, không có ý tưởng mới nào (`segment_research_batch.py:55-58`).

4. **Không có trần chi tiêu.** Ngày 25/09, phanh duy nhất là tài khoản hết tiền. Trần chi tiêu (AA-649, `bd5c01ce`) và ngân sách từng lần chạy mới có từ 28/09.

5. **Hết tiền nhưng vòng lặp vẫn chạy, và làm hỏng kho.**
   - Lỗi mua bị nuốt im lặng. Hệ thống lưu **14.691 số lượt tìm rỗng** và đánh dấu **1.795 địa điểm "đã nghiên cứu" trong 182 ngày** dù không có dữ liệu.
   - Ngày 28/09 phải sửa tay: xoá 16.311 dòng rỗng và 5.859 dòng nhật ký (1.953 địa điểm). Giữ lại 1.311 dòng có số thật.
   - Địa điểm thực sự nghiên cứu xong ngày đó ít hơn nhiều so với 2.215. Bước kiểm chứng ước lượng tối đa khoảng 270, tức khoảng **≥0,18 USD/địa điểm**, gấp 1,5–2 lần mức của chị Thư. Ước lượng này **chưa đo trực tiếp**.

6. **Mua cho cả địa điểm vô dụng.**
   - Phạm vi nghiên cứu không loại địa điểm trung chuyển hay địa điểm không tên cụ thể (`segment_research.py:610-643`).
   - Phạm vi còn đọc cả Segment "mồ côi" sau khi tách lại địa điểm (`segment_research.py:628-633`).
   - Trong khi đó bước xếp hạng lại loại các địa điểm này (`atom_ranking.py:59, 787-788`). Tiền mua cho chúng không bao giờ tới được Slate.

7. **Đường S1 mua theo từng tour, có lúc không có trần.**
   - Tháng 10, viết lại catalogue mua DFS qua `process_seo` và job `s1_seo_prefetch`.
   - Job prefetch có ngân sách từ 01/10. Riêng `process_seo` **không có trần tới 31/10** (`3cfba249`). Từ đó mới có trần 0,50 USD/tour (`services/seo_intelligence/handler.py:40-55, 224-241`).

8. **Về chuyện "3 thị trường".** Mỗi thị trường vốn phải có lượt riêng, nên 3 thị trường đúng là tốn gấp 3 số lượt (AU + UK cộng lại 27,03 USD). Nhưng 3 thị trường không phải nguyên nhân chính. Cái phí là **xe rỗng × 3**: nếu gom đầy, 3 thị trường chỉ thêm vài lượt.

**Chứng minh cách gom lô rẻ hơn:** thử ở Bhutan ngày 28/09 hết 0,55 USD cho 50 địa điểm × 3 thị trường, khoảng **0,011 USD/địa điểm, rẻ hơn khoảng 10 lần** so với 25/09. Khi đã gom lô, khoản lớn còn lại là SERP và từ khoá liên quan, không còn là số lượt tìm.

## 4. Tenant viết blog có làm chạy DFS không?

**Trả lời: KHÔNG** (tính tới mã nguồn ngày 08/11/2026).

| Đường | Hôm nay có mua DFS? | Bằng chứng |
|---|---|---|
| T2 – tenant viết lại tour | **Không.** Chỉ đọc seo_context / search_demand. | `services/jobs/t2_rewrite_job.py:149-203`; test `tests/unit/test_aa646_t2_no_dfs.py:34-38` |
| T7 – Slate, đề xuất chủ đề Blog | **Không.** Chỉ đọc atom_ranking. | `services/acp_shared/slate.py:115-118, 236-268` |
| T8 – chọn góc viết | **Không** | grep `services/acp_angle_gate` không có DFS client |
| T9 – viết blog, FAQ | **Không.** Câu hỏi lấy từ DB. | `services/acp_shared/real_questions.py:20-23` |
| A3 – xuất / tách địa điểm / xếp hạng lại | **Không** | `services/export/handler.py` không import DFS |
| Admin – nghiên cứu Segment | **Có**, chỉ khi admin bấm. Cần mã bí mật admin, tối đa 200 địa điểm/lần, chạy từng lần một, có ngân sách, kiểm số dư trước. | `api/routers/admin_segment_research.py:36-49, 101-137` |
| Admin – S1 viết lại catalogue AA | **Có**, trần 0,50 USD/tour từ 31/10 | `handler.py:227`; `services/jobs/s1_seo_prefetch_job.py:62` |
| Admin – script mua bù câu hỏi PAA | **Có**, chỉ chạy bằng script, trần trọn đời 3 USD | `services/acp_shared/question_topup.py:15-24, 229-258` |
| Việc chạy theo lịch | **Không** mua. Chỉ đọc số dư, miễn phí. | grep `shared/jobs`, `worker` |

**Vì sao anh có thể từng nghĩ "tenant viết là chạy lại DFS":** trước đây điều đó **đúng**, qua 2 đường:
- Đến 28/09: T2 tự chạy nghiên cứu toàn nền tảng. Đây là vụ 49 USD. AA-646 gỡ (`b0dd9bea1`).
- Đến 29/09: T2 tự gọi `process_seo` khi tour chưa có dữ liệu SEO, khoảng 0,18 USD/tour, không có trần. Gỡ ở `d3921934b`.

**Lưu ý:**
- Blog của tenant có ảnh hưởng gián tiếp. Danh sách "cần câu hỏi" của script mua bù lấy từ các chủ đề Blog của tenant (`question_topup.py:55-66`). Nhưng không mua gì cho tới khi admin chạy script.
- Admin chạy S1 có thể gắn tenant_id của đại lý (`admin_pipeline.py:635-636`). "Mặc định là AA" không có nghĩa "luôn là AA".
- Rào chắn bằng test: có test bắt mọi chỗ tạo DFS client phải truyền ngân sách (`tests/unit/test_aa642_s0_dfs_cap.py:264-275`). **Chưa có test cấm đường tenant gọi DFS.** Hiện chỉ T2 và đường SERP sâu có test riêng.
- Các app khác (Partner, Booking, TripPlanner) không có DFS client.
- **Hệ quả thật** khi không chạy DFS: dữ liệu cũ hoặc thiếu thì Blog **ít chủ đề, ít câu hỏi thật hơn**, chứ không tự mua thêm. 7.116 trên 7.323 địa điểm US đang quá hạn, và chỉ 8.662 trên 97.218 dòng xếp hạng có số lượt tìm.

## 5. So với cách làm của chị Thư

Repo `aa-social-media` của chị Thư không có trên GitHub, nhưng **có một bản sao đầy đủ trong repo CIS**: `apps/AA-CIS-App/docs/AI-gent-for automation works/aa-soscial-media-main/`. Bước kiểm chứng đã đọc trực tiếp bản này.

| Điểm | Chị Thư | CIS ngày 25/09 | CIS hôm nay |
|---|---|---|---|
| Ai bấm mua | Người chủ động mua; README cấm nối tự động | Tự chạy sau mỗi lần tenant viết lại | Chỉ admin |
| Phạm vi mỗi lần | 1 nước. Nhật: 24 trip, 581 địa điểm, nghiên cứu 368 | **Cả nền tảng**, 2.215 địa điểm | Admin chọn, tối đa 200/lần |
| Bỏ địa điểm trung chuyển / không tên | Có | Không | **Vẫn chưa** |
| Định giá trước toàn bộ tên địa điểm | Có, 1 lượt/thị trường/1.000 tên | Không | Có (chế độ gom lô) |
| Gom từ khoá vào một lượt | Tới 1.000, 16 luồng | **4,5**, 4 luồng, chờ cứng 5 giây | Tới 1.000 |
| Giới hạn tốc độ gọi | Có, theo giới hạn tài khoản | Không | Vẫn không |
| Bỏ qua địa điểm không đổi | Có (fingerprint) | Không | Theo nhật ký 182 ngày |
| Từ khoá liên quan | Labs `keyword_suggestions` ~0,0144 USD, 1 từ gốc/lượt | Google Ads `keywords_for_keywords` 0,09, 1 từ gốc/lượt | Google Ads, tới 20 từ gốc/lượt (tháng 10 trung bình 10,9, khoảng 0,0076 USD/từ gốc, rẻ hơn của chị) |
| Ngân sách | 0,12 USD/địa điểm, tối thiểu 1 USD | Không có trần | Ngân sách từng lần chạy |
| Thị trường | Cố định US/UK/AU | 3 thị trường của tenant | Admin chọn |

**Về câu "chị Thư chạy cả trăm tour cũng đâu tốn":**
- Theo **chính số của chị**: khoảng 0,10–0,12 USD/địa điểm, và mỗi trip thêm khoảng 24 địa điểm mới. Vậy lần chạy **đầu tiên** cho 100 trip mới sẽ tốn **cỡ vài trăm USD**, trừ khi địa điểm đã nằm sẵn trong kho.
- Rẻ là ở **lần chạy lại**, nhờ kho 182 ngày và bỏ qua địa điểm không đổi.
- Hoặc chị nhớ tới chi phí **viết**: khoảng 0,08 USD/bài blog (README:121-126).
- Chị muốn nói ý nào: **chưa kiểm được**.

**Mật độ địa điểm:** CIS khoảng 9 địa điểm/tour (7.323 / khoảng 793 tour). Nhật của chị khoảng 24/trip. So 7.323 với 368 là so cả catalogue với một nước, không phải so hai cách làm.

**Sự cố tương tự bên chị:** ngày 28/08 bên chị cũng có một sự cố: khoảng 1.460 lượt gọi từ khoá liên quan, 21 USD, do lỗi giới hạn tốc độ bị hiểu thành "không có lượt tìm" (README:196-200, 247-251).

**Kết luận:** về đơn giá, cách mua gom lô hiện tại của mình **đã ngang hoặc rẻ hơn** cách của chị. Ngày 25/09 tốn là do ba thứ: **bấm sai chỗ, mua cả nền tảng, xe chạy rỗng**.

## 6. Đề xuất

**Kế hoạch đề xuất (một kế hoạch):** chạy một lượt nghiên cứu **US trước**, theo lô, có kiểm soát. Đo độ phủ Blog trên tenant audit. Rồi mới quyết UK/AU.

Thứ tự:
1. Chỉ lấy địa điểm thuộc tour đang dùng. Bỏ địa điểm trung chuyển, không tên và Segment mồ côi.
2. Mua SERP **chỉ khi kho chưa có PAA còn tươi**. Giữ ngưỡng "có lượt tìm > 0".
   - Không nên hạ xuống "chỉ ≥1000", vì PAA còn nuôi FAQ của bài Route và T2 (`real_questions.py:9-12, 386-411`, `s1_prefetch.py:449-457`).
3. Lượt đầu tắt `keywords_for_keywords`, đo độ phủ, rồi mới quyết có bật lại không.
   - Tắt sẽ làm giảm độ phủ của địa điểm không có số liệu, nhưng giảm bao nhiêu **chưa đo**.
4. **Chạy xếp hạng lại (recompute) sau mỗi lượt nghiên cứu.**
   - Hiện job nghiên cứu không làm việc này (`services/jobs/segment_research_job.py:44-80`).
   - Vì vậy dữ liệu mua về chưa tới được thanh chắn Blog. Đây có thể là một phần lý do 8.662/97.218.

**Chi phí ước tính cho mỗi thị trường** (7.116 địa điểm quá hạn của US; số địa điểm quá hạn của UK/AU **chưa đo**, tạm coi tương đương):

| Cách tính | US | UK | AU |
|---|---|---|---|
| Trần lý thuyết (`estimate_cost`, có từ khoá liên quan) | 48,9 | ≤ 48,9 | ≤ 48,9 |
| Trần lý thuyết, tắt từ khoá liên quan | 16,8 | ≤ 16,8 | ≤ 16,8 |
| **Theo giá thật đo hôm nay** (0,0033 USD/địa điểm, có từ khoá liên quan) | **~23,5** | chưa có số thật | chưa có số thật |
| **Theo giá thật, tắt từ khoá liên quan** (0,0021 USD/địa điểm) | **~15** | chưa có số thật | chưa có số thật |
| AI (Haiku) đề xuất từ khoá, trần | ~10 mỗi lần chạy | trả lại nếu chạy riêng | trả lại nếu chạy riêng |

Ghi chú bảng:
- Hôm nay chi phí thật chỉ bằng khoảng 45% mức trần (0,508 so với 1,118).
- SERP là khoản lớn nhất (47%), từ khoá liên quan 35%, số lượt tìm 18%.
- Con số "60 USD cho US" trong AA-1055 là **mức trần**. Theo giá thật thì khoảng 24 USD.
- Lọc bỏ địa điểm vô dụng (bước 1) sẽ làm mọi con số trên giảm theo. Giảm bao nhiêu **chưa đo**.
- UK/AU có khả năng rẻ hơn US: ít từ khoá có lượt tìm hơn nên ít SERP hơn. **Chưa kiểm được.**
- Số dư hiện tại 27,41 USD. Một lượt US có từ khoá liên quan (~23,5) gần như tiêu hết.

**Thay đổi mã nguồn, gắn vào AA-1055:**

| # | Thay đổi | Chỗ sửa |
|---|---|---|
| 1 | Sau job nghiên cứu, tự xếp hạng lại | `services/jobs/segment_research_job.py:44-80` → `services/jobs/recompute_job.py:156` |
| 2 | Phạm vi = địa điểm của tour đang dùng; bỏ trung chuyển, không tên, mồ côi | `services/acp_contract/segment_research.py:610-643` (dùng lại quy tắc ở `atom_ranking.py:59, 787-788`) |
| 3 | Kiểm kho trước khi mua SERP | `segment_research.py:382-421` (giống `s1_prefetch.py:15-16`) |
| 4 | `use_suggestions` mặc định tắt ở lượt đầu | `api/routers/admin_segment_research.py:55`, `segment_research.py:653` |
| 5 | Lưu sẵn "địa điểm → từ khoá" để chạy lại hoặc đổi thị trường không phải trả tiền AI lần nữa | `services/acp_contract/segment_research_batch.py:182-210` |
| 6 | Chỉnh `estimate_cost` cho gần giá thật (hiện báo cao khoảng 2 lần) | `segment_research_batch.py:131-147` |
| 7 | Bỏ giới hạn 200 địa điểm/lần, thay bằng cổng theo USD | `admin_segment_research.py:44-49` |
| 8 | Gắn tenant_id/job_id vào lần gọi DFS của nghiên cứu, để sổ biết ai gây ra chi phí | `segment_research.py:710` |
| 9 | Test cấm đường tenant (T2/T7/T8/T9, router `v1_*`) gọi DFS | mở rộng `tests/unit/test_aa642_s0_dfs_cap.py` |
| 10 | Blog: tách "chưa có dữ liệu" và "dưới ngưỡng" (đã có trong AA-1055). Kiểm lỗi chọn thị trường "tốt nhất" theo hạng thấp nhất: thị trường mỏng như DE/FR/NL có thể thắng với nhu cầu rỗng | `slate.py:272-300` (chưa kiểm với dữ liệu thật) |
| 11 | Sửa docstring sai: "cache 7 ngày" (thực tế 182); "đường duy nhất mua DFS" (S1 cũng mua) | `segment_research_job.py:5`, `admin_segment_research.py:1-14` |
| 12 | Tìm nguồn tiêu DFS ngoài sổ (~0,7–1,5 USD) | kiểm các công cụ dùng chung tài khoản DFS |

**Cần anh duyệt:**
1. Số tiền cho lượt US: khoảng 15 USD (tắt từ khoá liên quan) hoặc khoảng 24 USD (bật). Có nạp thêm DFS không.
2. Có mua UK/AU không, và mua lúc nào (sau khi xem độ phủ US).
3. Thanh chắn Blog 1000 lượt tìm là chép nguyên từ `channels.toml` của chị Thư, vốn làm cho catalogue Nhật dày. Chỉ 178 trên 785 từ khoá US có lượt tìm đạt ≥1000. Giữ 1000 hay đổi sang ngưỡng tương đối (ví dụ nhóm 25% cao nhất, sàn 100–200)? Đây là quyết định sản phẩm.
4. Bỏ giới hạn 200 địa điểm/lần, thay bằng cổng theo USD.
5. S1 có nên chỉ đọc kho nghiên cứu như T2 (không tự mua) không.

Ngân sách thật trong `shared.spend_budget` (dự phòng: 5 USD/lần chạy, 10 USD/ngày) **chưa đọc trực tiếp**.

## Phụ lục: bằng chứng

**Sổ chi phí** (`.tmp-session/S273/dfs/dfs_spend.out`)
- Tổng 71,49 USD. Không gắn tenant: 1.730 lần gọi / 52,00. Gắn tenant: 1.035 lần gọi / 19,49.
- `d=2026-09-25 n=1169 live=1169 usd=49.020 markets=3 tenants=0`
- Gắn tenant: 21/09 0,910 + 01/10 2,342 + 02/10 0,294 + 03/10 1,132 + 05/10 5,786 + 06/10 0,892 + 07/10 1,460 + 08/10 6,674 = 19,490. 94 dòng gắn tenant còn lại chưa giải thích.
- 2026-10 `keywords_for_keywords n=205 kw=2229 usd=16.65`. Tổng `keywords_for_keywords` cả thời gian 318 lượt / 26,82 USD (37,5%).
- Theo vị trí: 2036 (AU) 13,564; 2826 (UK) 13,466.
- 2026-11-08: 1 `search_volume_bulk` 395 từ khoá 0,09 + 119 SERP 0,238 + 2 `keywords_for_keywords` 0,18 = 0,508.
- `serp_advanced_paa_deep` 8 lần gọi / 0,018 USD (20/10).
- Bản ghi chú 01/10 trùng sổ: `docs/sessions/2026-10-01-S207` dòng 56, "DFS $2,34".

**Kích hoạt và các bản sửa**
- AA-545 dùng chung toàn nền tảng: commit `15743a96` (06/09).
- Gỡ nghiên cứu khỏi T2, thêm giới hạn admin: `b0dd9bea1` (28/09, AA-646/647). Phần bị gỡ là `_run_research_only` trong `api/routers/v1_tours.py`.
- Câu truy vấn không lọc tenant: `git show bbfd5c6f:services/acp_contract/segment_research.py:537`.
- Thời điểm 25/09: `docs/sessions/2026-09-28-S199-ecosystem-architecture-review.md:24-34, 117-155`.
- T2 thôi gọi `process_seo`: `d3921934b` (29/09). Ghi chú ~0,18 USD/tour ở `services/jobs/t2_rewrite_job.py:152-155`.
- Gom lô AA-648: `c319f2565` (28/09). Trần chi tiêu AA-649: `bd5c01ce`. Trần S1 0,50 USD/tour: `3cfba249` (31/10), migration 318 `49f0d7b1`.

**Cách mua và giá**
- `segment_research.py:83` (4 luồng), `:211` (chờ 5 giây), `:75` (182 ngày), `:571-583` (chỉ ghi nhật ký khi mua thành công, sau sửa), `:710` (client không có tenant_id).
- `segment_research_batch.py:3-6` (678 lượt, 4,5 từ khoá, 39 USD), `:53` (1.000 từ khoá/lượt), `:55-58` (lượt ít từ gốc chỉ trả lại từ gốc), `:131-147` (ước tính trần), `:316-324` (SERP khi có lượt tìm > 0).
- `shared/cost_guard.py:37-41` (ngân sách dự phòng), `:47-55` (bảng giá ước tính).
- Repo mẫu của chị Thư: `aa-soscial-media-main/src/aa_social/stages/research.py:8-22, 81-116, 621-680`; `reference/search-spend.toml:7-31`; `README.md:111-126, 196-228, 247-311`; `search/dataforseo.py:81, 119, 159`.
- Sửa kho 28/09: comment Linear AA-647 lúc 08:34 UTC (xoá 16.311 + 5.859 dòng). Thử Bhutan: comment AA-648 lúc 09:34 UTC.

**Dùng dữ liệu**
- `atom_ranking.py:27-30, 144-153, 193-263, 389-405, 919`; `recompute/stages.py:158-165`.
- `slate.py:95-96, 115-140, 190-213, 272-300, 643`.
- `real_questions.py:1-26`; `acp_content_writing/service.py:1814-1844`.
- `s1_prefetch.py:1-48, 421-467`; `handler.py:101-133, 224-241`; `s1_seo_prefetch_job.py:19, 44, 62`.

**Rào chắn bằng test**
- `tests/unit/test_aa646_t2_no_dfs.py:34-38`
- `tests/unit/test_aa779_real_first.py:665-681`
- `tests/unit/test_aa642_s0_dfs_cap.py:264-275`

**Chưa kiểm được**
- Tenant_id cụ thể trên 1.035 dòng gắn tenant.
- Đường nào gây ra 0,91 USD ngày 21/09.
- Nguồn tiêu DFS ngoài sổ (~0,7–1,5 USD).
- Số địa điểm thực sự nghiên cứu xong ngày 25/09.
- Trong 7,116 địa điểm quá hạn, bao nhiêu là do đổi tên và bao nhiêu là chưa từng nghiên cứu.
- Giá DFS khi gửi đúng 1.000 từ khoá một lượt (chưa từng thấy lượt nào lớn hơn 395).
- Ngân sách thật trong `spend_budget`.
- Chưa đọc các issue Linear AA-515/545/625/646–649. Bằng chứng ở trên lấy từ mã nguồn, commit, log phiên và sổ chi phí.