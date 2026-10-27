# AA-784 — Đánh giá lại model viết và kiểm place card (S252, 26/10/2026)

Người làm: Claude Code (S252). Người duyệt: Nghiệp.

**Vì sao làm lại.** Lựa chọn ở S234 (GPT-5.6 Luna viết nháp, Haiku 4.5 kiểm) chỉ dựa vào LLM tự chấm. Không có nguồn web, không có đáp án đúng. Câu "Sonnet sai 11, Luna sai 2" là so hai giám khảo khác nhau. Place card tệ sẽ lan sang mọi bài viết dùng nó, nên lần này mọi fact được chấm bằng nguồn thật trên web, mù với tên model.

## Kết luận

| | Hiện tại (live) | Đề xuất |
|---|---|---|
| Viết nháp (`a3_place_card`) | GPT-5.6 Luna | **GPT-6 Luna** |
| Kiểm (`a3_place_card_check`) | Haiku 4.5 | **Haiku 4.5 (giữ)** |
| Fact sai lọt vào thẻ (FK) | 5/125 = 4,0% (lần 2: 3/124) | **0/97 = 0%** (Wilson 95%: 0–3,8%) |
| Model bịa fact (trên mọi fact nó viết) | 7/132 = 5,3% | **0/107 = 0%** |
| Thẻ sai danh tính | 0 | 0 |
| Fact dùng được mỗi thẻ (U) | 3,73 | 3,44 |
| Chi phí dựng toàn bộ 9.186 thẻ | ≈ $16 | **≈ $13** |
| Qua 8 cổng của luật | Không (FK > 3%) | **Có** |

Đề xuất là đổi model viết nháp sang GPT-6 Luna và giữ Haiku 4.5 làm checker. Việc đổi cần một migration route (giống mig 222).

Sau đó dựng thẻ theo từng nước, trần chi phí $17 (= $13 × 1,3, theo luật §7). Phải có Nghiệp OK mới chạy, vì đây là lần chạy trả tiền trên toàn catalogue.

## Cách làm (luật viết và khoá trước khi có kết quả)

- **Thiết kế và luật quyết định:** `design.md` (§5 panel, §6 chỉ số, §7 cổng). Hash sha256 cùng giờ sửa cuối được ghi trong `rule-freeze.txt`. File được sửa lần cuối lúc 10:50, còn lần chạy trả tiền bắt đầu khoảng 10:55.
- **Mẫu:** 30 nhóm địa điểm khó, lấy tất định, trải trên 13 nước. Có 5 lớp: tên chung chung, biến thể chính tả, trùng tên với nơi ở nước khác, landmark, nơi nhỏ ở địa phương.
- **Model viết nháp:** GPT-5.6 Luna (chạy 2 lần), Sonnet 4.6, Sonnet 5.5, GPT-6 Luna, Haiku 5.5.
- **Model kiểm:** Haiku 4.5, GPT-5.6 Luna, Sonnet 5.5, Opus 5.5.
- **Thẻ cài lỗi:** 26 thẻ, có fact bị sửa năm/số hoặc bịa thêm, và nửa số thẻ bị đổi locality. Dùng để đo khả năng bắt lỗi của checker.
- **Chi phí chạy:** $1,839, khớp `shared.llm_call_log` (682 dòng). Không tầng nào bị cắt vì trần.
- **Panel mù:**
  - 2 người gán nhãn độc lập cho mỗi nhóm, có tra web và bắt buộc trích URL kèm câu nguyên văn. 1 trọng tài xử lý các điểm A và B lệch nhau.
  - Panel chỉ thấy gói mù. Kết quả và key giải mã được tải về sau khi nhãn đã chốt.
  - Tổng cộng 30 agent, 777 fact, 94 biến thể danh tính.
  - Độ đồng thuận A–B (Cohen's κ): danh tính 0,99; verdict 0,77; trip-leak 0,72.
- **Kiểm chứng đối kháng các nhãn quyết định:** 14 nhãn có thể lật kết quả, mỗi nhãn danh tính 3 giám khảo, mỗi fact 2 giám khảo, được dặn cố bác bỏ.
  - 8/8 fact "sai" được giữ, ví dụ: Spa Land mở 2009 chứ không phải 2005; không có "Lijiang Naxi Autonomous Prefecture"; trạm radar Basco vẫn hoạt động.
  - 2 lỗi region của Sonnet 5.5 được giữ (Haidian, Haeundae là quận, không phải cấp vùng).
  - 4 nhãn "other_entity" bị lật thành "same" theo đa số: "Lijiang Old Town" cho Lijiang, và "Khamar Monastery" cho "bell pavilion of Hamulin Temple". Chi tiết trong `recheck-votes.json` và `recheck-overrides.json`.

## Bảng chính (sau kiểm chứng, coverage trên 25 nhóm xác định được)

| Cặp (viết × kiểm) | FK | LK | WI | Coverage | U | $ toàn bộ | Cổng trượt |
|---|---|---|---|---|---|---|---|
| GPT-5.6 Luna #1 × Haiku 4.5 (live) | 4,0% | 0 | 0 | 100% | 3,73 | 16 | 3 (FK) |
| GPT-5.6 Luna #2 × Haiku 4.5 (live, lần 2) | 2,4% | 4,1% | 0 | 96% | 3,58 | 15 | 4 (LK) |
| GPT-5.6 Luna × Opus 5.5 | 1,7% | 0 | 0 | 100% | 3,65 | 72 | — |
| Sonnet 5.5 × GPT-5.6 Luna | 1,5% | 1,5% | 8,3% | 92% | 4,75 | 85 | 2 (2 thẻ sai region) |
| Sonnet 4.6 × GPT-5.6 Luna | 3,3% | 6,8% | 0 | 92% | 3,56 | 78 | 3, 4 |
| **GPT-6 Luna × Haiku 4.5** | **0** | **0** | **0** | **88%** | **3,44** | **13** | **—** |
| GPT-6 Luna × Sonnet 5.5 | 0 | 0 | 0 | 88% | 3,70 | 31 | — |
| GPT-6 Luna × Opus 5.5 | 0 | 0 | 0 | 88% | 3,83 | 42 | — |
| Haiku 5.5 × GPT-5.6 Luna | 7,1% | 2,4% | 0 | 96% | 3,59 | 8 | 3, 4 |

FK = fact sai trong số fact được giữ; LK = lộ thông tin chuyến đi; WI = thẻ sai danh tính; U = fact dùng được mỗi thẻ. Đầy đủ (kể cả cặp cùng vendor, khoảng tin cậy Wilson) trong `metrics.json`.

**Cách luật chọn:** 4 cặp qua đủ 8 cổng. FK thấp nhất là 0 (các cặp GPT-6 Luna); vùng hoà ±2 điểm % gồm cả 4. Tiêu chí phụ thứ nhất là U, cần chênh ≥ 0,5; cao nhất 3,83 và thấp nhất 3,44 chênh 0,39 nên vẫn hoà. Tiêu chí phụ thứ hai là WI, cả 4 bằng 0. Tiêu chí cuối là chi phí, thắng là **GPT-6 Luna × Haiku 4.5** với $13.

## Những điểm cần biết trước khi duyệt

1. **Coverage nhạy với định nghĩa.**
   - Luật ghi "coverage ≥ 85% trên các nhóm *xác định được*" (panel gán `identifiable = yes` cho 25 nhóm, `ambiguous` 4, `no` 1). Tôi tính theo đúng chữ: chỉ nhóm `yes`.
   - Nếu đếm cả 4 nhóm `ambiguous` thì GPT-6 Luna chỉ còn 79% và trượt cổng 5. Khi đó cặp thắng là GPT-5.6 Luna × Opus 5.5 ($72).
   - 3 nhóm "yes" mà GPT-6 Luna từ chối đặt tên là "The Self-Guided Trail", "Food Street in Old Lahore" và "the Himalayan ranges". Đều là tên mơ hồ, và từ chối vẫn an toàn hơn đoán bừa.
2. **Checker gần như không bắt được lỗi tự nhiên.**
   - Haiku 4.5 bắt 8/34 fact sai tự nhiên, nhưng bắt 22/23 lỗi cài sẵn. Lỗi danh tính tự nhiên: không checker nào bắt được (0/2).
   - Opus 5.5 tốt nhất (5/7 tự nhiên) nhưng đắt gấp khoảng 5 lần.
   - Nghĩa là **chất lượng phải đến từ model viết nháp**; checker chỉ chặn được lỗi thô. Đây là lý do nên đổi drafter thay vì chỉ đổi checker.
3. **Ít fact hơn một chút.** GPT-6 Luna viết khoảng 4,7 fact mỗi thẻ (Luna 5.6 khoảng 5,1). U thấp hơn live 0,3, vẫn trên sàn 2,5.
4. **Độ ổn định của live:** chạy Luna 5.6 hai lần thì 19/30 nhóm ra cùng danh tính, FK dao động 2,4–4,0%. Mẫu 30 nhóm (khoảng 100–130 fact mỗi ô) có sai số khoảng ±2 điểm %, nên luật mới dùng vùng hoà.
5. **Nếu không đổi model:** route hiện tại sẽ để lọt khoảng 4% fact sai. Với khoảng 9.186 thẻ × 4,8 fact, tức khoảng 1.700 fact sai trên toàn catalogue.

## Bước tiếp theo đề xuất (chờ Nghiệp OK)

1. Migration CIS đổi route `a3_place_card` → `gpt-6-luna`; `a3_place_card_check` giữ `haiku`. Migration được review trước khi merge, Infra copy, rồi DB Migrate.
2. Dựng thẻ theo từng nước (AA-784 B): thử 3 thẻ, rồi ≤ 50, rồi theo nước. Trần $17; báo cáo chi phí từng lô từ `llm_call_log`.
3. Kiểm mẫu sau khi dựng: 20 thẻ ngẫu nhiên qua panel web như trên.

## File trong thư mục này

- `design.md`, `history.md`, `critic.md`: thiết kế và luật đã khoá, kèm phản biện.
- `rule-freeze.txt`: hash và giờ sửa cuối của luật.
- `cardeval_run.py`: script chạy (dry/paid/resume).
- `panel_wf.js`: workflow panel mù.
- `score.py`: script tính chỉ số.
- `labels/`: 30 file nhãn đã chốt (A/B/trọng tài), có nguồn và câu trích.
- `recheck-votes.json`, `recheck-overrides.json`: kiểm chứng đối kháng 14 nhãn quyết định.
- `metrics.json`: toàn bộ chỉ số.

Tên bucket và account trong các file đã được thay bằng `<bronze-bucket>` / `<acct>`.
