# Bức tranh toàn hệ thống AA-CIS (S273, 09/11/2026)

Đo trên Dev lúc 08/11 khoảng 17:45 UTC, chạy trong container api của CIS với role `cis_app` (chỉ đọc). Mọi con số lấy từ 4 file đầu ra (`system_funnel.out`, `system_funnel_stats.out`, `recompute_health.out`, `propagation_check.out`), `prep_findings.json`, báo cáo DFS và `previews.jsonl`. Số nào là phép tính của mình (chia, cộng) thì ghi rõ "tự tính". Tên metric cho từng số nằm ở Phụ lục.

Cách viết số: dấu phẩy là phần thập phân, dấu chấm ngăn hàng nghìn (giống báo cáo DFS). Trong Phụ lục giữ nguyên dạng metric gốc.

Vài thuật ngữ dùng xuyên suốt:

- **Tour thô (raw tour)**: một dòng tour lấy từ file Excel của nhà cung cấp.
- **S1**: bước AI viết lại tour thô. **Master**: bản tour đã được chấp nhận và đang phục vụ.
- **Atom**: mẩu thông tin nhỏ tách ra từ Master (một hoạt động, một địa điểm…). **Segment**: nhóm atom theo địa điểm.
- **Ranking / Score**: bảng xếp hạng segment theo từng thị trường (US, UK, AU, DE, FR, NL).
- **Route**: tuyến tour nối các hub (điểm trung chuyển).
- **Recompute**: job tính lại segment, ranking, route và câu hỏi tìm kiếm.
- **Demand**: số lượt tìm kiếm mua từ DataForSEO (DFS). **Research**: lượt mua demand + câu hỏi (PAA) cho địa điểm.
- **Tenant**: đại lý dùng nền tảng. **T2**: bản tour viết riêng cho tenant. **T7 / Slate**: danh sách chủ đề đề xuất. **T8**: chọn góc viết (angle). **T9**: viết bài (piece). Bài **held** là bài bị cổng chất lượng giữ lại.

## Tóm tắt 7 dòng

1. Phần nền tảng chạy tốt: 917 tour thô đang sống → 892 Master (97,3%) → 892 có atom (100%) → 883 có ranking (99,0%) → 699 có route (79,2% số đã xếp hạng).
2. Chỗ hẹp lớn nhất phía nền tảng là dữ liệu demand: chỉ 4,4% (DE/FR/NL) tới 19,1% (US) dòng ranking có số lượt tìm; chỉ 1,1–4,9% địa điểm có research còn mới.
3. Recompute chạy ổn khi được gọi: 116/118 lần thành công trong 60 ngày, lần lỗi cuối cách đây khoảng 33 ngày, p95 là 291,3 giây, không job nào đang chờ.
4. Lỗ hổng chính của recompute là có thay đổi không gọi nó: research/demand mới không có trigger tự động trong code, và cặp bật/tắt tour ngày 05/11 phải chờ khoảng 74 giờ mới có recompute chạy xong.
5. Bật/tắt tour hiện sạch: mọi bộ đếm rò rỉ đều bằng 0. Chỉ GAP 2 đang xảy ra và nhỏ: 7 chủ đề đã dùng nằm trên route cũ, 3 yêu cầu góc viết nằm trên atom đã xoá.
6. Phía tenant hẹp mạnh: 28 tour có T2 (3,1% Master), 67/1.250 chủ đề được dùng (5,4%), Blog bị giữ 54,9%, và chỉ 6/254 bài đã duyệt từng được đăng (2,4%), hiện còn 1 bài đang đăng.
7. Chi phí LLM 30 ngày: S1 68,41 USD lớn nhất, kế đến adhoc 40,04; không đo được chi phí theo tour. Research 6 thị trường lượt đầu: trần 165,48 USD; phần DFS theo giá thật đo được khoảng 90,26 USD, còn số dư DFS chỉ 27,41 USD.

## 1. Dòng chảy từ tour thô tới bài đăng

Đơn vị đổi theo bước (tour → chủ đề → yêu cầu → bài), nên cột % chỉ so được trong cùng đơn vị.

| Bước | Số lượng | % so với bước trước | Ghi chú |
|---|---|---|---|
| Tour thô, tổng số dòng | 987 | — | Từ 46 file Excel, file khai báo 1.063 dòng |
| Tour thô chưa xoá | 943 | 95,5% (tự tính) | 26 bị thay thế (superseded), 44 bị bỏ vào thùng rác |
| Tour thô đang sống (source active) | 917 | 97,2% (tự tính) | 14 nước, không dòng nào thiếu nước |
| S1: tour có bản viết lại / bản mới nhất được duyệt | 918 / 889 | 96,8% (889/918) | 2.312 bản viết; bản mới nhất: 27 chờ người duyệt (hitl), 2 bị từ chối |
| Master đang hoạt động | 892 | 97,3% của 917 | 25 tour thô sống chưa có Master (IN 18, LK 4, PH 2, NP 1) |
| Master có atom | 892 | 100% | 25.989 atom sống, trung bình 29,14 atom/tour |
| Master có segment | 883 | 99,0% | 9 tour có atom nhưng không có segment |
| Master có ranking (mỗi thị trường) | 883 | 100% của 883 | 16.203 dòng/thị trường, 14.055 xếp được; loại: transit 2.074, không tên 74 |
| Master có route | 699 | 79,2% của 883 | 1.267 route, dùng 21/87 hub |
| Tour có T2 (bản cho tenant) | 28 | 3,1% của 892 Master | 93 bản, 9 tenant, 50 cặp tenant–tour |
| T7: chủ đề trong Slate / đã dùng | 1.250 / 67 | 5,4% | 1.174 đề xuất, 7 đã chọn, 2 bị cắt |
| T8: yêu cầu góc viết / đã duyệt | 77 / 70 | 90,9% | 5 chờ mục tiêu, 2 chờ chọn |
| T9: bài viết / đã duyệt / bị giữ | 405 / 254 / 151 | 62,7% duyệt | Từ 70 yêu cầu; trung bình 2,21 lần viết/bài |
| Đã gửi đăng (bài khác nhau trong publish_log) | 6 | 2,4% của 254 | 9 dòng log, 2 tenant, 1 dòng lỗi |
| Đang đăng hiện tại | 1 | — | Blog: 1 đăng, 1 lỗi, 6 gỡ; Facebook: 1 gỡ. Chỉ có 1 WordPress kết nối |

Một số điều cần biết thêm:

- Cột `review_status` (985 dòng pending_review) và `lifecycle_stage` (987 dòng "active", kể cả dòng đã xoá) của tour thô không theo dòng chảy. Không tìm thấy code nào ghi `lifecycle_stage`.
- Điểm chất lượng S1 đã bão hoà: trung bình mọi bản 8,38, nhưng trung bình trên Master được chấp nhận là 9,81; 820/2.312 bản đạt ≥ 9,9.
- `prompt_version` trống trên cả 1.219 bản S1 trong 30 ngày, nên không truy được bản nào viết bằng prompt nào.
- 25 tour sống chưa có Master trùng số với 25 mục chờ duyệt trên key chưa từng được phục vụ. 25 mục này là phần không phải T2 trong hàng chờ duyệt (43 tổng − 18 T2). Script không ghép hai tập, nên đây chỉ là gợi ý, chưa chứng minh.
- Ranking được tính lại khoảng 58–59 phút trước khi đo.
- Booking có 892 trip plan (mỗi Master một plan) nhưng chỉ 2 bán được. TripPlanner 30 ngày: 102 phiên, 7 yêu cầu báo giá (6,9%), khớp 7 case Booking từ TripPlanner.

**Demand và research (chỗ hẹp lớn nhất phía nền tảng):**

| Thị trường | Dòng ranking có demand (trên 16.203) | Dòng qua thanh Blog (≥1000 lượt tìm và ≥3 câu hỏi) | Địa điểm có research mới, 182 ngày (trên 7.323) | Demand mới nhất cách đây |
|---|---|---|---|---|
| US | 3.090 (19,1%) | 893 | 361 (4,9%) | 0,1 ngày |
| UK | 2.237 (13,8%) | 494 | 178 (2,4%) | 41,3 ngày |
| AU | 2.059 (12,7%) | 442 | 178 (2,4%) | 41,3 ngày |
| DE | 709 (4,4%) | 124 | 80 (1,1%) | 27,4 ngày |
| FR | 714 (4,4%) | 125 | 80 (1,1%) | 27,4 ngày |
| NL | 714 (4,4%) | 113 | 80 (1,1%) | 27,4 ngày |

Cả 6 thị trường: 9.523/97.218 dòng có demand (9,8%), tăng so với 8.662 trong báo cáo DFS.

**Theo nước** (raw = tour thô sống; route % = có route / có ranking, tự tính):

| Nước | Raw | Master | Có atom | Có ranking | Có route | Route % | Có T2 |
|---|---|---|---|---|---|---|---|
| IN | 236 | 218 | 218 | 218 | 187 | 85,8% | 7 |
| LK | 126 | 122 | 122 | 121 | 102 | 84,3% | 6 |
| CN | 121 | 121 | 121 | 120 | 82 | 68,3% | 2 |
| NP | 86 | 85 | 85 | 85 | 74 | 87,1% | 2 |
| JP | 79 | 79 | 79 | 75 | 22 | 29,3% | 3 |
| LA | 46 | 46 | 46 | 46 | 44 | 95,7% | 1 |
| PH | 46 | 44 | 44 | 44 | 41 | 93,2% | 3 |
| TH | 43 | 43 | 43 | 41 | 33 | 80,5% | 0 |
| TW | 36 | 36 | 36 | 35 | 23 | 65,7% | 0 |
| BT | 32 | 32 | 32 | 32 | 32 | 100% | 2 |
| KR | 30 | 30 | 30 | 30 | 30 | 100% | 0 |
| PK | 18 | 18 | 18 | 18 | 17 | 94,4% | 1 |
| MN | 17 | 17 | 17 | 17 | 11 | 64,7% | 1 |
| VN | 1 | 1 | 1 | 1 | 1 | 100% | 0 |

Đọc bảng:

- Raw → Master: chỉ IN mất 18, LK 4, PH 2, NP 1.
- Master → ranking: JP mất 4, TH 2, LK/CN/TW mỗi nước 1. Cộng lại đúng 9 tour không có segment.
- Ranking → route, theo số tuyệt đối: JP 75→22 (−53), CN 120→82 (−38), IN 218→187 (−31), LK 121→102 (−19), TW 35→23 (−12). Theo tỷ lệ: JP mất 71%, MN 35%, TW 34%, CN 32%. Các file này không cho biết vì sao JP thấp.
- Chỉ BT, KR và VN sạch tới bước route. LA thiếu 2, PK thiếu 1.

**T9 theo kênh:**

| Kênh | Đã duyệt | Bị giữ | % giữ (tự tính) |
|---|---|---|---|
| blog | 93 | 113 | 54,9% |
| linkedin | 137 | 36 | 20,8% |
| email | 2 | 2 | 50% |
| facebook | 6 | 0 | 0% |
| ads, instagram, landing_page, tiktok | mỗi kênh 4 | 0 | 0% |

Blog tháng 11 tệ hơn: 7 duyệt / 17 giữ trên 24 bài, so với tháng 10 là 86 / 96 trên 182. Lý do giữ hàng đầu là F9_cta_fact: 63/151 bài giữ (41,7%). Kế đến F4_seo_surface 24, F4_extreme_length 11, F17_trip_fact 10.

## 2. Recompute có chạy ổn không

**Kết luận: chạy ổn khi được gọi. Vấn đề là có những thay đổi không gọi nó.**

| Chỉ số | Giá trị | Ý nghĩa |
|---|---|---|
| Lần chạy toàn nền tảng, 60 ngày (thành công / lỗi) | 116 / 2 | Hai lần lỗi cùng ngày 06/10, ở lần thử thứ 2, chưa ghi bước nào. Không lỗi thêm từ đó (khoảng 33,4 ngày) |
| Lần chạy theo tour, 60 ngày | 12 thành công | Tất cả ngày 27/10; lần cuối cách đây khoảng 12,5 ngày |
| Thời gian chạy p50 / p95 / max | 150,3 / 291,3 / 543,2 giây | Không lần nào vượt mức chờ 1.800 giây; p50 theo tuần đi ngang |
| Thời gian chờ trong hàng p50 / p95 / max | 411,8 / 1.203,7 / 1.204,7 giây | Đúng thiết kế: gom việc 180 giây, trần 1.200 giây |
| Gom việc (coalescing) | 86 job gom 1.092 lần yêu cầu | Cơ chế gom chạy tốt |
| Đang chờ / đang chạy | 0 / 0 | Không tồn đọng, không khoá hết hạn |
| Lần thành công cuối | 3.456,7 giây trước khi đo | Khoảng 58 phút |
| Phiên bản Score | 135 ở cả 6 thị trường, 1 bản sống, 0 dòng cũ sót | Cơ chế đổi phiên bản (AA-734) hoạt động đúng |
| Rò rỉ (tour tắt vẫn có ranking/route) | 0 / 0 / 0 | Chỉ đúng tại thời điểm đo |
| Segment chưa từng nhận câu hỏi | 1.272 / 10.527 segment sống | Trục Questions trống ở các segment này |
| Segment nhận câu hỏi trước demand mới nhất | 7.786 / 10.527 | Là cận trên: "mới nhất" là mốc chung (research US 08/11) |
| Master có atom nhưng không có segment | 9 | Giống số trong ảnh chụp S252 (theo prep_findings) |
| segment_gc lần cuối | mode apply: 1.067 segment mồ côi, xoá được 0, giữ 1.067 | 1.067 = 11.594 segment tổng − 10.527 segment sống |
| Chi phí ghi trên job recompute | 0,000 USD / 117 lần | Chưa gán chi phí; sổ LLM có a3_question_landing 0,317 và a3_demand 0,216 USD/30 ngày (chưa xác minh thuộc recompute) |

Thời gian tính tới Score: một tour mới thường mất khoảng 9–10 phút (chờ p50 khoảng 6,9 phút + chạy p50 khoảng 2,5 phút). Tệ nhất khoảng 20 phút chờ cộng thời gian chạy.

**Các vấn đề:**

1. **Research và demand mới không gọi recompute (mức cao).** Trong code, `segment_research_job.py` không xếp recompute vào hàng. Làm mới search_demand chỉ đặt `questions_count` về NULL. Metric trigger gộp mọi lý do lạ vào nhóm "other" (14 job platform, 12 job theo tour), nên không tách được. Theo prep_findings (bài học S273, không phải số đo live), một lần recompute tay sau research đã nâng số segment đủ điều kiện Blog từ 4 lên 31.
2. **Recompute sau bật/tắt tour không có lưới quét (mức trung bình).** Thường mất khoảng 3–4 phút (p50: paused 178,9 giây, restored 201,5 giây, retired 238,3 giây). Nhưng cặp retire/restore ngày 05/11 phải chờ khoảng 74 giờ. Chỉ có 1 sự kiện retired và 1 sự kiện restored bị chờ lâu; các sự kiện khác đều dưới khoảng 4,6 phút. Trong 7 ngày có 0 recompute do đổi trạng thái gọi. Các lần chạy ngày 08/11 không do sự kiện này gọi; theo prep_findings, một trong số đó là lần recompute tay sau research. Chưa xác định được nguyên nhân vì chưa đọc log.
3. **Có thể có hai recompute chạy cùng lúc sau deploy (từ code, chưa thấy live).** Kind recompute không có độ trễ nhả job và không có khoá liên tiến trình như a3_atomize. Metric chồng lấn (0) không bắt được trường hợp cùng một dòng job bị nhận lại.
4. **9 Master không có segment và 1.272 segment chưa từng nhận câu hỏi.**
5. **segment_gc chạy apply nhưng không xoá gì (mức thấp).** Các file không cho biết quy tắc nào giữ 1.067 segment này.
6. **Cửa sổ lệch phiên bản giữa các thị trường.** Các thị trường được đổi lần lượt: US tính lúc 16:46:19, NL lúc 16:47:55, cách nhau khoảng 96 giây. Đây là suy luận từ thời điểm tính, không phải thời điểm commit được ghi lại.
7. **Thử lại không cứu được lần lỗi:** 2 lần thử lại, 0 lần thành công sau thử lại.

## 3. Bật/tắt tour: lan truyền và lỗ hổng

Nền hôm nay: cả 892 key đều đang được phục vụ (không key nào bị tạm dừng hay ngừng bán). 0 Master hoạt động nằm trên nguồn đã chết, 0 key có hai tour sống. Lịch sử có 12 sự kiện (23/10 → 05/11): 5 retired, 6 restored, 1 paused.

Các phần chạy tốt:

- 0 atom, 0 ranking và 0 route trên tour không sống.
- 0/17.474 thành viên segment nằm trên atom chết (S252 có 10.547).
- Mỗi sự kiện đều có thông báo tenant gửi qua mail tổng hợp (1 retired, 1 restored, không trễ).
- Mọi job phụ trong 30 ngày đều thành công.
- Có 4/12 sự kiện không có job purge TripPlanner và 9/11 sự kiện retired/restored không có job fan-out. Từ số đếm, có vẻ chúng xảy ra trước khi hai tính năng này ra đời: 4 sự kiện ngày 23/10, và 2 sự kiện ngày 05/11 đều có fan-out. Đây là suy luận, script không nhóm theo ngày.

| Lỗ hổng | Đang xảy ra bao nhiêu | Ảnh hưởng | Cách sửa |
|---|---|---|---|
| Recompute sau bật/tắt không có lưới quét (cặp 05/11) | 2 sự kiện; tính tới khi recompute kế tiếp **chạy xong**: retired max 266.724,2 giây, restored max 266.662,4 giây (khoảng 74 giờ). Đã lành lại. Metric `events_not_followed_by_recompute` báo 0/12 nên che mất | Nếu lúc retire đã xoá ranking/route thì tour được khôi phục vắng khỏi Slate và chủ đề tenant khoảng 3 ngày | Đọc shared.job và log quanh 05/11 12:05; quét 2 giờ một lần cho sự kiện chưa có recompute; cảnh báo khi quá 30 phút không có recompute; test cho retire_source/restore_source |
| GAP 1: chủ đề Segment theo sống/chết của một tour đại diện | 0 hiện tại; phạm vi: 1.237 chủ đề Segment | Khi retire tour đại diện mà địa điểm vẫn có tour khác bán: chặn ghi/đăng (409), gắn cờ bài, chuyển trang WordPress về nháp sau 7 ngày, gửi mail "không còn bán" | Dùng quy tắc của Subject (segment còn ít nhất một thành viên được phục vụ) ở các cổng liveness; hoặc trỏ lại sang thành viên khác |
| GAP 2: không trỏ lại sau khi thay thế/viết lại | 7 chủ đề đã dùng trên route cũ; 3 yêu cầu góc viết trên atom đã xoá (2 approved, 1 pending_choice); 0 bản T2 | Chủ đề/yêu cầu trỏ vào id cũ; yêu cầu pending_choice đang kẹt | Thêm bước trỏ lại trong supersede/rewrite; chạy một lần cho 7 + 3 dòng |
| GAP 3: tour tạm dừng im lặng với bên ngoài | 0 key tạm dừng; đề xuất của CRM không đo được (no access) | Tạm dừng lâu giống ngừng bán không báo trước | Chốt chính sách: sau N ngày tạm dừng thì coi như ngừng bán; báo nhân viên Booking; CRM cảnh báo cả "paused" |
| GAP 4: CRM biết tin ngừng bán muộn | Không đo được (`g.crm_catalog_by_state` = no access) | CRM có thể giữ trạng thái cũ | CRM kéo outbox lifecycle như Booking; đo một lần qua DB Migrate run-script |
| GAP 5: đường publish bỏ một phần việc sau commit | 0; không có sự kiện nào đi qua publish | Ranking/route/trang chuyến đi có thể sót khi Master tắt lúc đang publish | Gọi đủ `run_after_commit` từ `services/export/handler.py` |
| Cache trên atom chết | 6.390 embedding, 785 place card, 9.438 atom_matches | Chỉ tốn chỗ lưu | GC cache cho atom đã tắt quá N ngày |
| `lifecycle_stage` không có code ghi | 892 tour sống đều "active" | Đang ngủ | Đưa vào lifecycle service hoặc bỏ khỏi hợp đồng catalog.v_tour |
| place_extract khi bật lại không qua `auto_allowed()` | 6 job / 30 ngày, 0,000 USD | Có thể tốn tiền nếu tắt PLACE_PIPELINE_AUTO | Thêm kiểm `auto_allowed()` |
| (Ngoài lề) Ghim TripPlanner không còn component | 105/201 | Có vẻ do id component đổi, không phải bật/tắt | Điều tra riêng |

## 4. Chi phí đơn vị và tổng

**LLM theo tháng:** tháng 9: 41,69 USD; tháng 10: 269,35 USD; tháng 11 (tới 08/11): 15,44 USD. Từ 01/10 tổng là 284,79 USD.

**LLM 30 ngày theo bước (tiền tố tên stage):**

| Bước | USD |
|---|---|
| s1 | 68,41 |
| adhoc (script chạy tay) | 40,04 |
| a3 | 30,12 |
| t9 | 24,94 |
| t2 | 14,42 |
| t5 | 12,67 |
| t10 | 2,88 |
| t8 | 2,35 |
| writing | 1,41 |
| t7 | 0,23 |
| f10, supply, tp, t3 | mỗi bước < 0,12 |

Tổng 30 ngày là khoảng 197,65 USD (tự cộng). Bốn bước s1, adhoc, a3 và t9 chiếm khoảng 83%. Adhoc chiếm khoảng 20%.

**Chi phí đơn vị:**

| Đơn vị | USD | Ghi chú |
|---|---|---|
| S1 mỗi tour | không đo được | `tour_id` không được ghi trên dòng nào từ 01/10. Ước lượng tự tính: 0,0706 USD mỗi job s1_rewrite (68,4050/969) |
| T2 mỗi job | 0,1568 | 92 job |
| T8 mỗi yêu cầu | 0,0318 | Chỉ phần chọn góc viết |
| Chuỗi T8 → T10 mỗi yêu cầu góc viết | 0,3640 | 74 yêu cầu |
| T9 mỗi yêu cầu | 0,3505 | Viết bài là phần đắt |
| T9 mỗi bài (tự tính) | 0,069 / 0,110 mỗi bài được duyệt | Metric đo trực tiếp 0,0110 chỉ phủ 66 bài (khoảng 3% chi phí t9), không đại diện |
| Place card | tổng 13,59 cho 4.785 thẻ | Khoảng 0,0028 USD/thẻ (tự tính) |

Lưu ý: `shared.job.cost_usd` bằng 0 cho mọi kind viết có trả tiền (s1_rewrite, t2_rewrite, t8_angles, t9_write). Tổng mọi thời gian là 19,57 USD. 187.773 lần gọi (182,20 USD) trong 30 ngày không gắn app.

**DFS theo tháng:** tháng 9: 51,68 USD; tháng 10: 19,30 USD; tháng 11: 0,51 USD. Cộng 3 tháng là 71,49 USD (tự cộng). Số dư theo báo cáo DFS: **27,41 USD**. Cột stage trống trên mọi dòng DFS từ 01/10.

**Dự toán research 6 thị trường, lượt đầu (tắt gợi ý từ khoá liên quan, không lọc địa điểm):**

Mỗi bản xem trước là 200 địa điểm: trần 0,49 USD DFS + 0,28 USD LLM. Phần "thật" chỉ có cho DFS, theo giá thật báo cáo DFS đo được (0,0021 USD/địa điểm khi tắt gợi ý). Chưa có số đo LLM thật cho research, nên LLM chỉ có mức trần. Tất cả số trong bảng là tự tính, nhân tuyến tính theo số địa điểm quá hạn.

| Thị trường | Địa điểm quá hạn | Trần (DFS + LLM) | DFS theo giá thật | LLM trần |
|---|---|---|---|---|
| US | 6.962 | 26,80 | 14,62 | 9,75 |
| UK | 7.145 | 27,51 | 15,00 | 10,00 |
| AU | 7.145 | 27,51 | 15,00 | 10,00 |
| DE | 7.243 | 27,89 | 15,21 | 10,14 |
| FR | 7.243 | 27,89 | 15,21 | 10,14 |
| NL | 7.243 | 27,89 | 15,21 | 10,14 |
| **Tổng** | — | **165,48** | **90,26** | **60,17** |

- Cần 218 lần chạy (mỗi lần tối đa 200 địa điểm), khoảng 18,4 giờ worker theo p50 (p50 chỉ dựa trên 2 job).
- Bỏ mức "45% trần" mà brief dùng. Con số đó so với trần **có** gợi ý từ khoá. Với bản xem trước đã tắt gợi ý, giá thật bằng khoảng 86% trần chứ không phải 45%, nên dùng 45% sẽ tính thiếu DFS khoảng 2 lần.
- Bỏ mức "LLM 18%": không có nguồn. Số 18% duy nhất trong báo cáo DFS là tỷ trọng của khoản số lượt tìm.
- Số dư 27,41 USD chỉ đủ khoảng một thị trường theo giá thật (US 14,62 DFS). Báo cáo DFS cũng ước US khoảng 15 USD khi tắt gợi ý, khớp với số này.
- Hai bộ lọc chưa áp vào các số trên: bỏ địa điểm transit/không tên/mồ côi, và chỉ mua SERP khi chưa có PAA mới. Cả hai đều làm giảm chi phí, nhưng chưa ai đo giảm bao nhiêu.

## 5. Việc nên làm, xếp theo tác động

1. **Cho research và làm mới demand tự gọi recompute, thêm lưới quét.**
   - Tác động: demand mua về mới tới được Score, trục Questions và thanh Blog. Hiện 1.272 segment chưa từng nhận câu hỏi.
   - Chi phí: chỉ code. Recompute tốn ít tiền LLM (chưa gán được).
2. **Chạy research US có kiểm soát (cần anh duyệt chi).**
   - Tác động: US hiện chỉ 4,9% địa điểm có research mới và 893 dòng qua thanh Blog.
   - Chi phí: khoảng 14,62 USD DFS theo giá thật, cộng LLM tối đa 9,75 USD. Làm sau việc 1, nếu không dữ liệu không tới được Score.
3. **Lưới quét recompute sau bật/tắt tour và metric độ trễ.**
   - Tác động: tránh lặp lại khoảng 74 giờ tour vắng khỏi Slate. Thay metric hiện tại vì nó che mất độ trễ.
   - Chi phí: chỉ code. Việc đầu tiên là đọc log 05/11 (chỉ đọc).
4. **Giảm tỷ lệ giữ bài Blog (F9_cta_fact, F4).**
   - Tác động: Blog giữ 54,9%; tháng 11 chỉ 7/24 bài được duyệt.
   - Chi phí: các wave chất lượng viết theo ADR 0020, tốn tiền LLM theo wave (T9 khoảng 0,35 USD/yêu cầu).
5. **Dựng tích hợp WordPress (và Facebook) thử nghiệm lâu dài.**
   - Tác động: 254 bài duyệt mà chỉ 6 bài từng đăng, 1 bài đang đăng. Cũng để chạy kiểm tra retire → restore trên bài WordPress thật.
   - Chi phí: thời gian dựng. Các file không có số chi phí.
6. **Sửa GAP 1 trước khi có lần retire tiếp theo.**
   - Tác động: hiện đang ngủ nhưng phạm vi lớn (1.237 chủ đề Segment): đại lý có thể bị chặn đăng và nhận mail sai.
   - Chi phí: chỉ code + test.
7. **Gán chi phí đúng chỗ.**
   - Tác động: ghi `tour_id` cho các lần gọi s1/a1/a3/t5, `content_piece_id` cho t9/t10, `job_id` cho recompute và các kind viết, `app` và `stage` bắt buộc khi ghi (cả DFS); ghi `prompt_version` cho S1. Không có những thứ này thì không đo được chi phí mỗi tour.
   - Chi phí: chỉ code.
8. **Thêm độ trễ nhả job và khoá liên tiến trình cho recompute (như a3_atomize).**
   - Tác động: chặn hai lần chạy cùng lúc sau deploy; ghi mã lỗi cố định.
   - Chi phí: chỉ code.
9. **Sửa GAP 2: trỏ lại 7 chủ đề và 3 yêu cầu góc viết, thêm bước retarget.**
   - Tác động: nhỏ nhưng đang xảy ra; một yêu cầu đang kẹt.
   - Chi phí: chỉ code.
10. **Dọn phần sót của nền tảng.**
    - Việc: sửa 9 Master không có segment; dọn hàng chờ duyệt 25 mục rồi ghép để xác nhận với 25 tour chưa có Master; điều tra route JP (22/79), CN và TW; xem quy tắc giữ của segment_gc.
    - Chi phí: truy vấn chỉ đọc + chạy segment theo phạm vi.
11. **Booking chỉ bán được 2/892 trip plan.**
    - Tác động: cần quyết định sản phẩm và nguồn cung (giá, ngày khởi hành), không phải lỗi pipeline.
    - Chi phí: ngoài phạm vi kỹ thuật.

## Phụ lục: tên metric cho mỗi con số

Tiền tố: `FUNNEL` = system_funnel.out, `stats` = system_funnel_stats.out, `RECOMPUTE` = recompute_health.out, `PROP` = propagation_check.out.

**Dòng chảy**
- 987 / 943 / 917: `FUNNEL s01_raw raw_tours_total`, `raw_tours.live_rows`, `raw_tours.live_active_source`
- 26 / 44: `FUNNEL s01_raw by_source_status.superseded`, `by_source_status.trashed`
- 46 file, 1.063 dòng: `FUNNEL s01_raw excel_sources.files`, `excel_sources.rows_declared`
- 985 / 987: `FUNNEL s01_raw by_review_status.pending_review`, `by_lifecycle_stage.active`
- 2.312 / 918 / 889 / 27 / 2: `FUNNEL s02_s1 generated_content.rows`, `generated_content.distinct_tours`, `gc_latest_version_by_status.approved|hitl|rejected`
- 8,38 / 9,81 / 820: `FUNNEL s02_s1 quality_scores.avg_overall`, `accepted_quality.avg_overall_accepted`; `stats s1.quality_scores score_ge_9_9`
- 1.219: `FUNNEL s02_s1 gc_by_prompt_version_30d.none`
- 892: `FUNNEL s03_master by_master_status.active`; 25: `FUNNEL s03_master raw_live_active_without_master`
- 43 / 18 / 25: `FUNNEL s02_s1 review_queue_by_status.pending`, `FUNNEL s09_t2 review_queue_t2_by_status.pending`, `PROP f.review_pending_by_key_state[state=never]`
- 892 / 25.989 / 29,14: `FUNNEL s04_atoms active_view.tours_with_atoms`, `active_view.real_atoms`, `avg_atoms_per_tour`
- 883 / 9: `RECOMPUTE masters.active.with_segment`, `masters.active.atoms_but_no_segment`
- 16.203 / 14.055 / 2.074 / 74: `RECOMPUTE ranking.US.current_rows`, `ranking.US.current_ranked`; `FUNNEL s06_ranking excluded_reason_by_market.US.transit|unnamed_place`
- 58–59 phút: `RECOMPUTE ranking.NL.age_s=3460.5` đến `ranking.US.age_s=3556.3`
- Demand theo thị trường: `FUNNEL s06_ranking current_by_market.<M>.with_demand_volume`; thanh Blog: `stats ranking.by_market blog_bar`; research mới: `stats research.place_coverage fresh_places`; tuổi demand: `RECOMPUTE demand.<M>.newest_age_d`; 8.662: báo cáo DFS report.vi.md
- 699 / 1.267 / 21 / 87: `FUNNEL s06_ranking routes.tours_with_route`, `routes.current_routes`; `RECOMPUTE route.current_hubs`, `hub.count`
- Theo nước: `FUNNEL s18_country_funnel country.<CC>.raw_live_active|master_active|with_atoms|ranked_any_market|with_route|with_t2`
- T2 93 / 9 / 28 / 50: `FUNNEL s09_t2 totals.rows|tenants|tours|tenant_tour_pairs`
- T7 1.250 / 67 / 1.174 / 7 / 2: `FUNNEL s10_t7 subject_totals.rows`, `subject_by_channel_x_state.*`
- T8 77 / 70 / 5 / 2: `FUNNEL s11_t8 request_totals.rows`, `request_by_channel_x_status.*`
- T9 405 / 254 / 151 / 70 / 2,21: `FUNNEL s12_t9 piece_totals.rows|requests|avg_attempt`, `piece_by_channel_x_status.*`; theo tháng: `stats t9.pieces_by_month`; lý do giữ: `FUNNEL s12_t9 held_reason_code_top10.*`
- Đăng 9 / 6 / 2 / 1 lỗi / 1 WordPress: `FUNNEL s13_publish publish_totals.rows|pieces|tenants|with_error`, `publish_log_by_channel_x_status.*`, `integrations_by_type.wordpress.connected`
- Booking 892 / 2: `FUNNEL s17_crossapp booking_data_totals_view.trip_plans|trip_plans_sellable`; TripPlanner 102 / 7: `FUNNEL s17_crossapp tripplanner_traffic_30d_view.*`, `tripplanner_inquiries_view`
- Không đọc được (no access): `booking_trip_cases_by_status_channel`, `booking_customers_count`, `tripplanner_trip_drafts_by_status`, `tripplanner_customers_count`, `crm_traveler_count`, `crm_trip_by_stage`, `crm_channel_account_rows`, `g.catalog_v_tour`, `g.catalog_v_tour_retired`, `g.crm_catalog_by_state`. Bảng job của Booking/CRM cũng không đọc được; chỉ biết `shared.job` có 0 job đang chờ/đang chạy (`FUNNEL s14_jobs now_by_status.rows=0`).

**Recompute**
- 116 / 2 / 12: `RECOMPUTE jobs.platform.succeeded|failed`, `jobs.tour.succeeded`
- 33,4 ngày: `RECOMPUTE since_last_failure_s.platform=2882580.6`; 12,5 ngày: `since_last_success_s.tour=1079091.6`
- 150,3 / 291,3 / 543,2: `RECOMPUTE duration.platform.p50_s|p95_s|max_s`; vượt mức: `duration.platform.over_expected=0`
- 411,8 / 1.203,7 / 1.204,7: `RECOMPUTE duration.platform.wait_p50_s|wait_p95_s|wait_max_s`
- 86 / 1.092: `RECOMPUTE trigger.a3_atomize.a3_atomize.platform`; nhóm other: `trigger.other.other.platform|tour`
- 0 / 0: `PROP c.recompute_now.queued|running`; 3.456,7: `RECOMPUTE since_last_success_s.platform`
- 135 / 1 / 0: `RECOMPUTE ranking.<M>.current_version|live_versions|superseded_rows`
- Rò rỉ: `RECOMPUTE leak.ranking_tours_not_active|ranking_rows_not_active|route_tours_not_active`
- 1.272 / 7.786 / 10.527 / 11.594: `RECOMPUTE landing.live_never_landed|live_landed_before_newest_demand|live_segments|segments`
- segment_gc: `RECOMPUTE segment_gc.mode|orphans|deletable|kept`
- 117 lần, 0,000 USD: `jobs.kind_status_30d recompute`; 0,317 / 0,216: sổ LLM stage a3_question_landing, a3_demand
- 96 giây: `FUNNEL s06_ranking current_by_market.US.newest_computed`, `current_by_market.NL.newest_computed`
- Thử lại: `attempts.retried=2`, `attempts.retried_then_ok=0`

**Bật/tắt tour**
- 892 key: `PROP a.key_state[state=served,reason=null]`; bất biến: `PROP a.invariant.active_master_on_dead_source`, `a.invariant.keys_with_two_live_tours`
- 12 sự kiện: `PROP a.lifecycle_events_all.n`, `a.lifecycle_events_30d[...]`
- Độ trễ: `RECOMPUTE lifecycle_lag.<event>.lag_p50_s|lag_p95_s|lag_max_s` (đo từ lúc xảy ra sự kiện tới khi recompute platform thành công đầu tiên bắt đầu sau đó **kết thúc**); 0 do đổi trạng thái: `PROP c.recompute_timing_7d.status_triggered`
- 0/17.474: `PROP b.segment_members.member_rows|member_rows_on_dead_atoms`
- Purge / fan-out: `PROP e.events_purge_job[...]`, `e.events_fanout_job[...]`; thông báo tenant: `PROP d.tenant_tour_notice[...]`
- GAP 1: `PROP d.segment_pick_wrongly_dead.*`; GAP 2: `PROP d.subjects_on_nonlive_route[state=used,route_current=False,tour_live=True]`, `d.angle_requests_on_inactive_atom[...]`, `d.t2_on_superseded_master_key_served.versions`; GAP 3: `PROP d.live_posts_on_dead_key`, `d.pieces_on_dead_key`; GAP 4: `PROP g.crm_catalog_by_state`; GAP 5: `PROP d.trip_pages_alive_on_dead_key.*`
- Cache: `PROP b.caches_on_dead_atoms.atom_embedding_rows|atom_place_card_rows|atom_matches_rows`
- Ghim TripPlanner: `PROP g.tripplanner_pins.pins_no_component|pinned_components`
- place_extract: `PROP e.place_extract_status_trigger_30d[...]`

**Chi phí**
- Theo tháng: `FUNNEL s15_llm cost_by_month_all.<YYYY-MM>.cost_usd`; từ 01/10: `since_1oct_total.cost_usd`
- Theo bước 30 ngày: `FUNNEL s15_llm cost_30d_by_stage_prefix.<prefix>.cost_usd`
- T8 / T9 mỗi yêu cầu: `FUNNEL s15_llm per_request_since_1oct_by_stage_prefix.t8|t9.cost_per_request`
- T2 mỗi job, chuỗi T8–T10: `stats llm.per_object_30d`
- Không đo được theo tour: `FUNNEL s15_llm per_tour_since_1oct_by_stage_prefix.rows=0`
- 969 job S1: `FUNNEL s14_jobs kind_x_status_30d.s1_rewrite.succeeded`
- T9 mỗi bài (66 bài): `FUNNEL s15_llm per_piece_since_1oct_by_stage_prefix.t9.*`
- Place card: `FUNNEL s05_places place_card_cost.cost_usd_total|cards`
- 19,57: `FUNNEL s14_jobs all_time.cost_usd_total`; 187.773 lần gọi, 182,20 USD: `FUNNEL s15_llm cost_30d_by_app_shadow.none.False.*`
- DFS theo tháng: `FUNNEL s16_dfs by_month.<YYYY-MM>.cost_usd`; số dư 27,41 và giá thật 0,0021 USD/địa điểm: báo cáo DFS report.vi.md
- Research: `previews.jsonl` (stale, sel=200, dfs_usd=0.49, llm_usd=0.28, idea_tasks=0); p50 303,2 giây: `FUNNEL s14_jobs duration_s_30d.segment_research.p50_s`
