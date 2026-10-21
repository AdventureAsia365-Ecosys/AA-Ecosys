# AA-803 (mở lại): đánh giá từng câu hỏi Jev trên dữ liệu Dev thật

- Phiên: S246, 21/10/2026. Tác nhân: Claude Code (bảng đánh giá + phản biện theo nhóm, 6 nhóm).
- Chế độ: **chỉ đọc**. Không ghi DB, không đổi mode, không push. Mọi thay đổi mode dưới đây là **đề xuất chờ anh duyệt**.
- Dữ liệu: `shared.decision_question` + `shared.decision_log` trên Dev, lấy 21/10 12:12 UTC
  (`.tmp-session/s246-data/aa803-jev.json`: 30 ngày + toàn thời gian). Code: AA-CIS-App `origin/main` 302e2e51.
- Bằng chứng thêm: calibration trong `apps/AA-CIS-App/docs/calibration/` (+ `data/*.json`), panel AA-845
  (`docs/audits/2026-10-21-S246-eval-panels/aa-845.md`), S223 / S224 / S228, CloudWatch Logs Insights `/ecs/aa-cis-dev`
  (chỉ đọc), drill AA-925.
- Trang duyệt: `decisions.json` cùng thư mục (25 mục, mỗi mục có lựa chọn + giá trị đề xuất).

## 1. Tóm tắt

Luật anh chốt lại: **câu nào có tác dụng thật và tin được thì giữ, còn lại tắt.**

| Đề xuất | Số câu | Câu hỏi |
|---|---|---|
| KEEP (giữ nguyên) | 9 | `a0_row_kind`, `a0_itinerary_usable`, `a0_country`, `a3_keyword_belongs`, `a3_atom_in_text`, `a3_same_place`, `a3_demand_belongs`, `a3_landing_belongs`, `a3_question_about_here` |
| RECALIBRATE | 2 | `a1_keyword_about_tour` (reject 0.30 → 0.40), `a3_activity_type` (gắn nhãn kiểm lại floor 0.90) |
| SHADOW | 0 | Không câu nào. Shadow tốn tiền như enforce mà không đo thêm được gì: zone đã được tính theo floor ở mọi mode, và cache hit không ghi dòng log. |
| OFF, tắt mới | 5 | `a1_claim_supported`, `a1_promise_unsupported`, `a1_brand_fit`, `a3_question_foreign`, `a3_idea_traveller` (3 câu tắt sau một bước kiểm $0, xem §3) |
| OFF, giữ như cũ | 9 | `t7_topic_fits_brand`, `t8_angle_answers`, `t9_fact_relevant`, 6 câu `t10_*`: đã OFF từ 13/10, **không gửi PUT** |

**Chi phí Jev.**

| | Sổ cái 30 ngày (30/09–21/10) | Tốc độ hiện tại (sau đợt trim AA-756, 10/10) |
|---|---|---|
| Bây giờ | $9.87 (74% là cặp A1 grounding, phần lớn chi trước 10/10) | khoảng $3.5–4/tháng: A1 grounding ~$2.5, trục Score A3 ~$1–1.5, phần còn lại ~$0 |
| Sau đề xuất | khoảng $2.3 nếu áp cho cùng 30 ngày đó | khoảng $1–1.5/tháng, cộng chi phí từng đợt: re-atomize toàn bộ ~$0.9, prefetch SEO toàn catalog ~$0.30, mỗi file upload ~$0.04 |

Tiết kiệm thật khoảng **$2.5/tháng**, không phải $7.3. Lợi ích lớn hơn tiền: tắt cặp A1 grounding bỏ được kịch bản Jev hết
credit đẩy cả wave A vào `manual_check` (lần thứ ba). Credit hiện còn khoảng $8.19.

## 2. Bảng từng câu hỏi

Cột "30 ngày" là số call / chi phí / số quyết định thực sự đổi kết quả (enforce, zone accept hoặc reject, đúng chiều mà code
dùng). Số call gồm cả call lỗi và call `skipped`. Từ #597 (09/10), cache hit không ghi từng dòng, nên số quyết định ở A3 là
**cận dưới**.

### G1. A0 ingest (preview upload + Commit)

| Key | Giai đoạn | Mode hiện tại | 30 ngày | Độ tin cậy | Đề xuất | Lý do ngắn | Rủi ro nếu tắt |
|---|---|---|---|---|---|---|---|
| `a0_row_kind` | A0 ingest | enforce, accept 0.95 | 1,510 / $0.029 / 455 accept (01/10), số drop chưa đo | 9/9 đúng ở p≥0.95, 0 lỗi, 2 đỉnh rõ | **KEEP** | Gần như miễn phí (chung call với itinerary_usable), chỉ tác động khi gần như chắc chắn, chỉ với dòng mới, lỗi Jev thì cho qua. Hiệu lực riêng nhỏ: theo calibration ~1/763 dòng có itinerary. | Dòng POI hoặc dịch vụ có ít text vào `raw_tours` rồi sang S1. Thấp. |
| `a0_itinerary_usable` | A0 ingest | enforce, reject 0.20 | 1,510 / $0.029 / 0 reject (01/10) | 33/33 đúng ở p≤0.20, Nghiệp lật 0/55 | **KEEP** | Câu có hiệu lực riêng rõ nhất nhóm: ~8/763 dòng có itinerary là rác (bài báo, trang shop, dòng test). Ví dụ "Trip 3 – Meiji-no-Yakata" từng bị publish rồi phải trash. Không luật nào khác bắt được. | Itinerary rác lọt vào S1, tốn tiền viết hoặc bị publish. |
| `a0_country` | A0 ingest | enforce, accept 0.95 | 1,055 / $0.019 / 0 (chưa từng được hỏi ở enforce) | Khớp 738/745; 7 chỗ lệch chủ yếu do country lưu sai | **KEEP** | Chỉ điền khi resolver không ra, không ghi đè. Gần như $0. | Commit lưu dòng với country NULL (Commit không có check missing-field), phải dọn tay. Không phải rủi ro an toàn. |

Ghi chú G1: 49 "reject" trong calibration là số câu trả lời (có call lặp), không phải số dòng. 25/33 dòng rác có itinerary
rỗng, luật `empty_itinerary` đã chặn. Preview và Commit dùng `subject_key` khác nhau nên mỗi file trả tiền hai lần (~$0.04),
không đáng kể. Follow-up $0: sau lần upload thật kế tiếp, đọc `not_a_tour` / `thin_itinerary` trong `ingest_details`.

### G2. A1/S1 viết văn: grounding và judge (vùng Q7)

| Key | Giai đoạn | Mode hiện tại | 30 ngày | Độ tin cậy | Đề xuất | Lý do ngắn | Rủi ro nếu tắt |
|---|---|---|---|---|---|---|---|
| `a1_claim_supported` | S1 grounding | enforce, accept 0.85, không có reject | 87,682 / $6.87 / ~100 waiver số (~50% sai) + waiver bữa ăn chưa đo | Phía accept 60/62 (S223). Phía reject không dùng được (precision 0.48, AUC 0.51, AA-845). 13.4% lỗi, gần hết do hết credit | **OFF** (sau khi đếm $0) | Chỉ cho câu qua, không bao giờ chặn. Dưới 1% câu trả lời đổi kết quả. Check số và check bữa ăn vẫn fail-closed khi không có Jev. | Mất ~50 waiver số đúng mỗi tháng (đi repair, vài câu có thể vào `manual_check`). Mất waiver bữa ăn: tour có nguồn ghi bữa ăn sẽ bị `ITINERARY_MEAL_TIME_INVENTED` và thêm một lần rewrite itinerary trả phí. Cần đo trước khi tắt. |
| `a1_promise_unsupported` | S1 grounding | shadow, không floor | 13,661 / $0.45 / 0 | Chưa calibration: 11 nhãn, 3 dương, AUC 0.833 | **OFF** | Không code nào đọc kết quả, nhưng nó giữ cho call trả phí chung còn chạy. Phát hiện hứa hẹn bịa (type-B) chuyển sang code check (S250). | Không mất gì đang chạy. Mất tín hiệu ứng viên duy nhất cho type-B (chưa từng được dùng). |
| `a1_brand_fit` | S1 judge tie-break | shadow, không floor | 47 / $0.0003 / 0 | 7 câu trả lời, đều p 0.8–1.0 | **OFF** | Không phân biệt được bản tốt với bản xấu, hành vi y như shadow. brand_fit thôi làm cổng ở S250. | Không có. Chỉ là dọn dẹp. |

Điểm mấu chốt G2:

- `a1_claim_supported` và `a1_promise_unsupported` **đi chung một call** (`grounding.py _judge_all`). Tiền chủ yếu nằm ở
  phần text nguồn dùng chung, nên tắt một câu một mình gần như không tiết kiệm. Hai câu phải tắt cùng một bước.
- **Hold AA-925 không phải lớp bảo vệ** (phản biện đã kiểm trong code). Với `reject_ceiling` NULL, Jev chỉ có thể cho qua.
  Khi Jev sập, check số và check bữa ăn vẫn chặn. Hold chỉ biến outage thành tour bị giữ: drill AA-925 cố ý chọn tour không có
  number hit, và tour đó vẫn publish được trên code cũ. OFF trả `skipped`, không tính là outage, nên không hold.
  `GROUNDING_NOT_RUN` vẫn là hard hold. Điểm em đã nêu trước ("tắt a1_claim_supported là mất chốt AA-925") được đính chính ở
  đây: tắt không mất lớp an toàn nào.
- Tiết kiệm thật: khoảng $0.07 cho 1,000 câu, khoảng $1.8 mỗi wave đầy đủ, khoảng $2.5/tháng. Con số "$6.42 mỗi wave" trong
  aa-845.md là giá trước đợt trim.

### G3. Keyword SEO (A1 prefetch + A3 segment research)

| Key | Giai đoạn | Mode hiện tại | 30 ngày | Độ tin cậy | Đề xuất | Lý do ngắn | Rủi ro nếu tắt |
|---|---|---|---|---|---|---|---|
| `a1_keyword_about_tour` | A1 SEO prefetch | enforce, accept 0.80, reject 0.30 | 18,086 / $0.30 / 0 (enforce từ 10/10 nhưng prefetch chưa chạy lại từ 08/10). Replay offline: ~1.5 drop + ~1.4 add mỗi tour | S224: 1.000 ở hai ngưỡng hiện tại. Trên drop thật sự có tác dụng: ≤0.40 là 6/7 | **RECALIBRATE**: reject 0.40, accept giữ 0.80 | Chốt duy nhất chặn keyword lạc đề (địa điểm khác cùng nước, tên khách sạn, hoạt động tour không có) vào `top_keywords` mà writer phải dùng. Đây chính là loại "hứa điều nguồn không có". Chỉ ngưỡng 0.40 bắt được tên khách sạn. Accept 0.65 chỉ 1/9 đúng. | Writer được bảo đưa vào địa điểm, khách sạn hoặc hoạt động tour không có. Mất cả phần bù từ đồng nghĩa ("tiger's nest" cho Taktsang). |
| `a3_keyword_belongs` | A3 segment research | enforce, accept 0.85, reject 0.45 | 170 / $0.0025 / 34 reject | 66/67 ở reject≤0.45, nhưng đo trên quần thể khác cổng live. 34 reject live chưa gắn nhãn | **KEEP** | Gần như $0. Chặn keyword chung chung (vd "hot springs", 368k) chiếm suất SERP/PAA duy nhất của địa điểm và thổi phồng demand. Reject sai ít hại vì tên địa điểm gốc luôn được giữ. | Keyword chung chung chiếm suất PAA của địa điểm, trục demand bị thổi phồng. |
| `a3_idea_traveller` | A3 research | enforce, reject 0.20 | 396 / $0.0067 / 214 reject (30/09, trước khi có luật lodging) | 19/19 đúng, Nghiệp lật 0/132 | **OFF** (sau khi kiểm $0) | Theo luật mới: trên mẫu, cả 19 reject đều đã bị `is_lodging_search` bắt trước (luật chạy trước Jev), 0/132 dòng không phải lodging bị reject. Hiệu lực biên ~0. | Thấp: tìm kiếm đặt phòng không có từ "hotel/stay" có thể lọt. `a3_demand_belongs` là chốt phía sau. |

Ghi chú G3:

- **Thời điểm có tác dụng.** Mọi tour prefetch 01–08/10 đã có `seo_context` dựng lúc shadow, tái dùng 180 ngày. Đổi ngưỡng
  hay enforce chỉ áp cho tour mới cho tới khoảng 29/03–04/04/2027. Muốn bảo vệ catalog hiện tại thì phải dựng lại
  `seo_context`: issue riêng, chỉ tốn DataForSEO vì verdict Jev đã cache.
- Lỗ nhỏ trong code: accept thêm lại candidate qua `keep.setdefault` mà không kiểm lại filter transfer / foreign. Mẫu chưa
  gặp. Một dòng guard là đủ (follow-up).
- Số `jev_ideas_rejected` trong kết quả job đếm trước pre-filter lodging, không dùng để đo được.

### G4. A3 atom và hình thành Segment

| Key | Giai đoạn | Mode hiện tại | 30 ngày | Độ tin cậy | Đề xuất | Lý do ngắn | Rủi ro nếu tắt |
|---|---|---|---|---|---|---|---|
| `a3_atom_in_text` | A3 atomize | enforce, reject 0.30 | 27,037 / $0.53 / 119 drop (01–10/10) | 127/127, Nghiệp lật 0/47, biên rộng (atom tốt thấp nhất p 0.53) | **KEEP**, xem lại sau lần re-atomize Luna đầy đủ đầu tiên | Chặn atomizer gán địa điểm highlight vào sai ngày (lỗi 63% ngày 30/09). "0 drop từ 10/10" chưa nói lên gì: từ đó mới có ~354 atom mới (kỳ vọng ~1.6 drop). ~27k atom hiện có vẫn là bản trước #644, nên rủi ro đổi model còn ở phía trước. | Địa điểm sai ngày hoặc chỉ là highlight làm lệch recurrence / "said" trong Score. Filter logistics không bắt loại lỗi này. |
| `a3_same_place` | A3 segment matching | enforce, reject 0.10 | 7,413 / $0.11 / 1,266 cặp được tách (chỉ call mới) | 30/30, Nghiệp lật 0/150. Nới 0.20 thì thêm 2 lỗi trên 61 | **KEEP** | Chốt duy nhất ngăn luật moment gộp hai địa điểm khác nhau (Bukchon / Jeonju Hanok Village, Wat Saket / Wat Si Saket). | Segment trộn, canonical place sai, Score / Route / PAA bị nhiễm. Lỗi tích luỹ dần khi atom mới nối các Segment cũ. |
| `a3_activity_type` | A3 segment type | enforce, accept 0.90 | 32,700 / $0.29 / 6,460 pick. Log: changed=654 Segment / 2,317 moment tranh chấp (20/10) | v2: 90/92 (S223). 53.8% lỗi, toàn do credit | **RECALIBRATE** (chỉ kiểm, không đổi mode) | Hiệu lực Segment lớn nhất A3: quyết transit hay experience cho ~650 Segment mỗi lần recompute. Quần thể tranh chấp tăng ~5x từ re-atomize 08/10, và lời hứa spot-check ở S223 chưa làm. Gắn nhãn ~60 pick; nếu dưới 95% thì nâng floor lên 0.95. | ~650 Segment quay về kết luận của luật động từ: experience rơi khỏi Score / PAA / Route, logistics vẫn được xếp hạng. |

Ghi chú G4: `decide()` đã ưu tiên cache 180 ngày trước breaker, nên outage chỉ ảnh hưởng moment chưa từng được hỏi. Đề xuất
"tái dùng verdict cũ khi Jev lỗi" đã có sẵn, bỏ. Ở volume hiện tại, tắt cả nhóm tiết kiệm khoảng $0.

### G5. Trục Score A3 (sở hữu demand + PAA landing)

| Key | Giai đoạn | Mode hiện tại | 30 ngày | Độ tin cậy | Đề xuất | Lý do ngắn | Rủi ro nếu tắt |
|---|---|---|---|---|---|---|---|
| `a3_demand_belongs` | A3 demand | enforce, reject 0.70 | 50,577 / $0.50 / 20,358 reject | 117/119; dưới 0.40 là 88/88; dải 0.50–0.70 chỉ 18/20 (90%) | **KEEP**, spot-check dải 0.50–0.70 | Hiệu lực lớn nhất hệ thống. Luật word-overlap phía dưới chỉ đúng 34/100. Dải 0.50–0.70 dưới chuẩn ≥97% ghi trong notes của chính dòng config: live có 2,761 verdict ở dải này, có thể ~270 reject sai keyword giá trị mỗi 30 ngày. | Demand thổi phồng sai (vd "fisherman's village", 40,500, gán cho Humayun's Tomb). |
| `a3_landing_belongs` | A3 question landing | enforce, reject 0.40 | 26,883 / $0.42 / 17,663 reject | 139/140, Nghiệp lật 1/62 | **KEEP** | Chốt duy nhất giữ số câu hỏi PAA trung thực. | Câu hỏi được tính cho mọi Segment trùng một chữ, số câu hỏi tăng ~7 lần. |
| `a3_question_about_here` | A3 question scope | enforce, reject 0.30 | 5,167 / $0.05 / 3,029 reject | Một mình: 137 drop, sai 2, bắt 135/149. Nghiệp lật 1/54 | **KEEP** | Làm gần hết việc lọc phạm vi quốc gia, và là câu duy nhất bắt câu hỏi chung chung ("What do Buddhists eat?"). | Câu hỏi chung chung và câu hỏi về nước khác lại được tính. |
| `a3_question_foreign` | A3 question scope | enforce, accept 0.90 | 5,167 / $0.05 (phần token trong call chung) / 2,147 accept, gần hết trùng với about_here | Trên 200 cặp có nhãn: thêm 3 drop, 2 sai. Ở 0.95 thêm 0 | **OFF** (sau join $0) | Gần như không drop gì mà about_here chưa drop, và phần thêm vào phần lớn sai ("Is Kerung in China or Nepal?"). Khôi phục 0.95 không khác OFF. | Gần như không có. |

Ghi chú G5:

- **Tự sửa sau outage chỉ đúng với demand.** Với landing và scope, `questions_count` ghi lúc outage được giữ cho tới một lượt
  landing toàn platform (`segment_ids=None`). Mọi đổi mode hay floor của 3 key này cũng chỉ tới Segment cũ sau lượt đó.
  Kiểm tồn dư $0:
  `SELECT count(*) FROM acp_contract.atom_segment WHERE questions_computed_at BETWEEN '2026-10-03 09:29Z' AND '2026-10-10 05:00Z';`.
  Khác 0 thì chạy một lượt landing toàn platform.
- Alert 402 và breaker (AA-720) đã có trên main. AA-845 chỉ thêm cảnh báo sớm khi credit dưới $3.

### G6. T-series tenant (T7 / T8 / T9 / T10)

| Key | Giai đoạn | Mode hiện tại | 30 ngày | Độ tin cậy | Đề xuất | Lý do ngắn | Rủi ro nếu tắt |
|---|---|---|---|---|---|---|---|
| `t7_topic_fits_brand` | T7 debate | off | 390 / $0.007 / 0 | 226/275 ở p 0.6–0.9 (không chắc), chưa calibration | **OFF** như cũ | Luna + check contested đã làm việc này. Nếu enforce thì quyết định chỉ dựa vào Jev. | Không |
| `t8_angle_answers` | T8 angle rank | off | 18 / $0.0003 / 0 | n=18, không nhãn | **OFF** như cũ | 17/18 ở p<0.4, gợi ý vài khớp nguyên văn là claim chứ không phải câu trả lời thật. Đáng kiểm sau, phía Bedrock. | Không |
| `t9_fact_relevant` | T9 facts | off | 21 / $0.0005 / 0 | Không nhãn | **OFF** như cũ | Không còn call site (#757). | Không |
| `t10_rubric_met` | T10 gates | off | 1,732 / $0.086 / 0 | 1,099/1,448 ở p≥0.8, kiểu đóng dấu cho qua | **OFF** như cũ | Không call site. F8 mà nó định thay đã bị AA-787 bỏ. | Không |
| `t10_brand_voice` | T10 gates | off | 433 / $0.031 / 0 | r=0.11 | **OFF** như cũ | Không call site. Từng được cho identity của AA, không phải brand của tenant. | Không |
| `t10_cta_clear` | T10 gates | off | 433 / $0.022 / 0 | 359/362 ở p≥0.9 | **OFF** như cũ | Nói "có" với mọi thứ. F9 + F6_cta_present đã bao. | Không |
| `t10_faq_restates` | T10 gates | off | 711 / $0.046 / 0 | Có 2 đỉnh nhưng không nhãn | **OFF** như cũ | Hỏi sai luật: FAQ được nhắc lại fact, chỉ cấm chép câu. F16 (`answer_copies_body`, `drop_restated_faq`) đã làm. | Không |
| `t10_offer_as_certain` | T10 gates | off | 136 / $0.006 / 0 | Không nhãn | **OFF** như cũ | Regex nó kiểm đã bị bỏ (AA-787, CIS ADR 0009). F17_trip_fact chặn và sửa lỗi này. | Không |
| `t10_same_piece` | T10 gates | off | 43 / $0.007 / 0 | p 0.3–0.8 | **OFF** như cũ | Gate cosine cross-tenant (≥0.92) đã chặn. | Không |

Không gửi PUT cho 9 key này: giá trị đã đúng, PUT chỉ ghi đè `updated_by` / `updated_at` và mất dấu audit S234.
Dọn tuỳ chọn (PR code riêng): bỏ `decide()` chết ở T7 (`debate.py`) và T8 `verify_answers` (đang ghi dòng `skipped` $0), sửa
`tests/unit/test_aa700_t7_t8_t9_jev.py` + `test_aa771_s234_voice_contract.py:359`, đánh dấu retired trong `notes` cho 7 dòng
T9/T10 (không xoá).

## 3. Các câu cần anh chọn

Giá trị đề xuất được in đậm. Các bước "kiểm $0" đều chỉ đọc (ECS exec với `DATABASE_URL` = `cis_app`, không gọi LLM).

1. **`a1_claim_supported` + `a1_promise_unsupported` (J04, J05).** **Đếm $0 trước**: bao nhiêu accept xoá được number hit,
   bao nhiêu tour được xoá meal code, và bao nhiêu tour mà waiver bữa ăn là code duy nhất được xoá (so chi phí rewrite thêm với
   ~$1.8/wave). Nếu waiver bữa ăn đáng kể thì ship luật bữa ăn (1 PR CIS nhỏ: coi claim bữa ăn là có nguồn khi INCLUSIONS hoặc
   text của ngày có cùng bữa hoặc mã B/L/D), **rồi OFF cả hai cùng một bước**. Hai lựa chọn khác: OFF ngay, hoặc giữ.
2. **Thử lần cuối `a1_promise_unsupported`?** Hỏi lại trên 100 câu đã gắn nhãn AA-845, khoảng **$0.01**, stage
   `adhoc_aa803`, ghi `llm_call_log`. Đây là lượt chạy trả phí, cần anh duyệt, và phải chạy **trước** khi OFF. Chỉ giữ câu này
   nếu có ngưỡng đạt ≥95% precision và có code dùng kết quả. Đề xuất: **không chạy, OFF cùng bước 1** (type-B chuyển sang code
   check ở S250).
3. **`a1_keyword_about_tour` (J07).** **Apply reject 0.40, accept 0.80** (đã duyệt ở AA-845, chưa apply). Kèm câu hỏi riêng:
   có dựng lại `seo_context` cho catalog hiện tại để ngưỡng mới có tác dụng trước 03/2027 không (issue riêng, chỉ tốn
   DataForSEO). Đề xuất: để sau, quyết cùng kế hoạch A1 S250.
4. **`a3_idea_traveller` (J09).** **Kiểm $0**: áp `is_lodging_search` lên 214 reject ngày 30/09; nếu số reject không phải
   lodging ≈ 0 thì OFF ngay, còn không thì giữ.
5. **`a3_question_foreign` (J16).** **Chạy join $0** trên `decision_log` (foreign-only = foreign ≥0.90 và about_here >0.30)
   rồi gắn nhãn; nếu ít hoặc phần lớn sai thì **OFF thẳng, không qua shadow**.
6. **`a3_demand_belongs` (J13).** **Gắn nhãn 30 reject live ở p 0.50–0.70**; nếu sai quá 2 thì hạ `reject_ceiling` xuống
   **0.50** (không phải 0.60). Lựa chọn khác: hạ 0.50 ngay, hoặc giữ 0.70.
7. **`a3_landing_belongs` (J14).** **Giữ 0.40** hay hạ 0.35 (131/131 đúng, bỏ ca sai Pak Ou / Mekong, đổi lại mất 8 lượt
   bắt). Đề xuất giữ 0.40. Nếu đổi thì phải kèm một lượt landing toàn platform.
8. **`a3_activity_type` (J12).** **Gắn nhãn ~60 pick p≥0.90** (30 transit, 30 experience) từ 2,317 moment đang tranh chấp;
   nếu dưới 95% thì nâng `accept_floor` lên 0.95.
9. **`a3_atom_in_text` (J10).** **Giữ**, xem lại khi có lần re-atomize Luna đầy đủ đầu tiên. OFF chỉ khi vẫn ~0 drop trên
   ≥10k atom.

Các câu còn lại (G1 ×3, `a3_keyword_belongs`, `a3_same_place`, `a3_question_about_here`, `a1_brand_fit`, 9 key T) không cần
anh quyết gì thêm ngoài duyệt chung.

**Cách áp mode (khi anh duyệt).** `PUT /admin/decisions/questions/{key}` ghi đè `accept_floor`, `reject_ceiling` và
`calibration_ref` đúng như body gửi lên: thiếu trường nào thì trường đó thành NULL, còn `notes` thì được giữ. Mọi PUT phải gửi
lại floor + `calibration_ref` hiện tại để quay lại được. Body đầy đủ cho từng key nằm trong `decisions.json` (`evidence.put_body`).
Enforce bắt buộc có `calibration_ref` và ít nhất một floor.

## 4. Q7 được tinh chỉnh thế nào

- **Q7(a) cũ:** "tắt Jev cho văn xuôi, Jev chỉ dùng cho A3".
- **Q7 mới (đề xuất):** Jev là **cổng phân loại dữ liệu có calibration**, không phải giám khảo văn xuôi.
  - **Tắt**: mọi câu chấm văn xuôi A1/S1 (`a1_claim_supported`, `a1_promise_unsupported`, `a1_brand_fit`). Việc chống bịa
    chuyển sang code check trên source facts có cấu trúc (S250). Check số và check bữa ăn vẫn fail-closed.
  - **Giữ ngoài A3**: 3 câu A0 ingest (phân loại dòng dữ liệu, ~$0) và `a1_keyword_about_tour`. Câu này nằm ở A1 nhưng chấm
    keyword chứ không chấm văn xuôi, và chặn đúng loại hứa hẹn bịa mà chính sách source-fidelity cấm.
  - **A3**: giữ 7/9. Tắt `a3_question_foreign` và `a3_idea_traveller` vì không có hiệu lực biên, mỗi câu sau một bước kiểm $0.
  - **T-series**: giữ OFF (chính sách S232: không đưa Jev vào đường T khi chưa có DPA/ZDR, allow-list rỗng).
- Hệ quả với AA-925: hold A1 hết lý do tồn tại cùng lúc với OFF. Cập nhật `docs/calibration/a1_claim_supported.md`, ghi chú
  drill `scripts/aa925/jev_drill.py`, và đóng mục "outcome > 0 live" của AA-845. Cột Jev trong golden set AA-729 sẽ thành
  `skipped`.

## 5. Điểm lệch dữ liệu (không đổi kết luận)

- `errors_30d` ghi 275 lỗi "breaker open" cho `a1_promise_unsupported`, nhưng `by_q_30d` / `by_q_all` không có dòng
  `zone=error` nào cho key này. Câu này ở shadow nên không ảnh hưởng.
- `a3_same_place`: có reject trong sổ cái ngày 16/10 nhưng log không có `segment_matching_done` hôm đó. Có thể do một script
  repair hoặc recompute.
- 117 lỗi `a3_same_place` có chuỗi lỗi rỗng (nhiều khả năng là `asyncio.TimeoutError`). Follow-up ngoài AA-803.
- `a3_activity_type`: 15,098 câu trả lời không lỗi trên 3,393 subject, tức ~4.4 câu trả lời mới mỗi subject. Có thể cache
  bị trượt do scope theo tenant hoặc do hash câu hỏi. Đáng xem nếu muốn giảm chi phí.
