# Chất lượng nội dung: chẩn đoán và hướng đi (S246)

*Tác nhân: Claude Code. Bản này chỉ đọc, không sửa repo, không chạy gì tốn tiền. Mọi số đều có nguồn. Số nào là ước tính thì ghi rõ "ước tính".*

## 0. Trả lời ngắn

- **Vì sao chưa hiệu quả.** Gần như toàn bộ công sức từ S218 đến nay dồn vào khâu *sau* người viết: thêm cổng, thêm judge, thêm vòng sửa, thêm Jev. Rồi mình lại đo kết quả bằng chính các cổng đó. Nhưng các cổng không phân biệt được bài tốt với bài xấu. Ở chế độ regenerate, pipeline cho qua 84,0% bài có nhãn đạt và 85,3% bài có nhãn hỏng. Riêng S1 thì ngược hẳn: 84,1% bài hỏng được qua, trong khi bài đạt chỉ qua 50%. Số "duyệt" tăng từ 4/10 lên 20/20, còn thước đo độc lập thì đứng yên.
- **Chất lượng được quyết ở đầu vào và ở người viết S1, và chỗ đó lại ít được chăm nhất.** Có bốn vấn đề:
  - Prompt S1 tự mâu thuẫn. Nó đòi "khoảng cách, địa hình, đưa đón, một con số thật", trong khi rule 6 cấm bịa.
  - Đầu vào sai ngay từ đầu: "3 hours" bị hiểu thành 3 ngày, từ khoá SEO lạc đề, T2 không được đọc phần inclusions.
  - Người viết là Haiku và nhận 0 ví dụ mẫu.
  - Từ S229, T9 có 58 commit, S1 chỉ có 16. Trong khi đó T9 chỉ phục vụ 4 tenant giả.
- **Mình chưa có "sự thật" từ người.** Trong 100 nhãn golden chỉ có 1 nhãn do người gán. 82 nhãn đến từ panel AI, mà rubric của panel đổi qua các vòng. Ý chị Thư chưa bao giờ đi vào vòng đo. Thêm một điều trung thực: trong 50 bài S1, chưa bài nào đăng nguyên văn được. 6 bài "đạt" đều vẫn cần sửa nhẹ.
- **Nên đổi gì.** Thứ tự nên là: dữ kiện trước, văn sau.
  - Mỗi tour có một bảng dữ kiện (fact sheet) do code kiểm, mỗi giá trị trỏ về câu gốc trong nguồn.
  - Người viết chỉ viết từ bảng đó, có 3–5 ví dụ mẫu, prompt hết mâu thuẫn.
  - Code kiểm số, tên, số ngày, độ dài meta. Lỗi nào code tìm ra thì gửi cho đúng một lượt sửa.
  - Ngừng thêm cổng. Đóng băng tinh chỉnh T9 cho tới khi S1 khá lên thật.
- **Cách đo.** Chỉ số chính là tỷ lệ bài "đăng nguyên văn hoặc chỉ sửa nhẹ" và số lỗi bịa nghiêm trọng. Hai số này do một panel có rubric cố định chấm, đọc toàn bộ nguồn, và anh phân xử những chỗ panel bất đồng. Tỷ lệ cổng duyệt không còn được báo như số chất lượng nữa.
- **Việc đầu tiên (S247).** Anh duyệt lại thứ tự kế hoạch (15 phút). Sau đó mình làm bảng dữ kiện, gộp luôn day-count oracle của Q-2, và viết bộ kiểm bằng code. Bộ kiểm chạy thử offline trên 50 bài S1 golden, tốn $0 đến tối đa $1.
- **Phép thử quyết định (S248–S249).** A/B người viết S1 trên 50 tour golden. Lần này có nhánh control chạy lặp để đo độ nhiễu, đúng bài học #103. Tổng ước tính khoảng $12–15, chia 2 lần chạy, mỗi lần ≤ $10. Mình cũng đặt sẵn tiêu chí dừng và phương án B nếu không nhánh nào thắng.

## 1. Đã làm gì và kết quả thật

Bối cảnh chung: chất lượng nội dung là việc chính trong khoảng 20 phiên. A-series gồm S203–S206, S208, S218–S219, S222–S224, S227–S228. T-series gồm S229, S231–S235, S239–S240, S245–S246. Khoảng 135 commit của AA-CIS-App nhắc tới issue chất lượng T-series (riêng AA-768 có 38) và khoảng 77 commit nhắc tới A-series. Riêng `quality_gates.py` bị sửa 37 lần kể từ 25/09. Tiền không phải giới hạn. Thứ thực sự bị tiêu là số phiên và sự chú ý của anh.

| Hướng đã thử | Công | Tiền | Số đo độc lập có đổi không | Nguồn |
|---|---|---|---|---|
| Các vòng cổng T-series r1–r8: F9, F13–F18, retry, sửa từng câu | ~10 phiên (S231–S240), ~135 commit | ~$35 cho các lần chạy có log, S232 không có dòng chi phí | **Không.** Tỷ lệ duyệt tăng 4/10 → 20/20 và retry-added về 0/28, nhưng đó là số do chính cổng chấm. brand_voice LinkedIn r5 là 6,32, S246 là 6,20. Vòng r6–r8 không chạy panel nào. | `docs/audits/2026-10-13-S234-t-series-rounds/README.md`; `docs/linear-export/.../AA-777.md`, `AA-865.md`; `docs/audits/2026-10-21-S246-eval-panels/aa-780.md` |
| Sửa đầu vào cho T9: seed, brand pack, max_tokens, trạng thái OFFERED, loại place card | Nằm trong S232–S235 | Nằm trong dòng trên | **Có, nhưng chưa tách được nguyên nhân.** Tỷ lệ chỉ cần sửa nhẹ tăng 24% → 70%. Hai số này đo trên hai bộ khác nhau (n=49 so với 6 request dùng lại) và rubric cũng khác. Thêm cổng ở r2–r4 thì đứng ở 50–60%. | `S234 README` ("further gains need writer-side changes, not more gates"); `docs/audits/2026-10-14-S235-ecosystem-team-pilot/r5/00-r5-summary.md` |
| Vệ sinh cơ học: lỗi cứng tất định | Nằm trong S234–S235 | — | **Có, thật.** Lỗi cứng giảm 70 → 4 → 2. | S234 README; r5 summary |
| Jev chấm văn xuôi (a1_claim_supported) | ~6 phiên cùng AA-756, AA-720 | ~$11,81 đã tiêu trên $20 nạp trước | **Không.** Jev trả "problem=False" cho 48/48 lần chạy golden S1. Giữa nền địa danh được phép và lời hứa bị cấm, AUC chỉ 0,51. Không ngưỡng nào đạt precision ≥ 0,95. Với A3 (phân loại có cấu trúc) thì Jev tốt. | `docs/audits/2026-10-21-S246-eval-panels/aa-845.md`; `docs/audits/2026-10-10-S223-jev-audit.html` |
| Vá luật cho bộ lọc câu hỏi FAQ/PAA (AA-779) | 5 vòng, thêm 3 vòng sửa và một lượt review đối kháng | ~$0 | **Không.** Nhánh luật không hơn main (McNemar p = 0,68). Precision của main là 0,64. Nguyên nhân gốc nằm ở đầu vào: PAA lấy theo tên cả tour. | `aa-779.md`; `docs/audits/2026-10-20-S245-aa779-paa/README.md` |
| Structured facts cho S1 (AA-748) | S224, 2 vòng | Nhỏ | **Chưa kết luận được.** Hiệu ứng nằm trong độ nhiễu, vì control lặp lại cũng tự lệch −36%. Issue bị đóng với tiền đề "grounding bắt hết", trong khi golden set cho thấy tiền đề đó sai. | `docs/linear-export/cis-core-pipeline-llm-platform/AA-748.md` |
| A/B nhiệt độ của người viết (0,4) | S224 | Nhỏ | **Không.** Lần đầu vô hiệu vì tham số không tới được Bedrock. | sessions index S224; `AA-756.md` |
| Ổn định judge: median-of-3, tie-break bằng Jev, anchors | Nhiều PR (riêng F9 có 8 PR trong 8 ngày) | Thêm call mỗi bài | **Không.** Cùng một bản nháp được chấm brand_fit từ 4 đến 8. Median-of-3 nhiễu ngang một lần chấm. | `judge_node.py:62-66`; `brand_fit.py:258-262`; `docs/audits/2026-10-20-S245-quality-system/design.md §1.2` |
| Chạy lại toàn bộ A-series | S218 | ~$98,6 (LLM $80 + DFS $18,6) | **Ảo.** Báo cáo ghi "94% tự lên Master", nhưng nhãn cho thấy chỉ 6/50 bài S1 ở mức sửa nhẹ và 0/50 đăng nguyên văn được. | `docs/audits/2026-10-08-S218-a-series-pipeline-audit.html`; `fixture-1.1.0.json` |
| Golden set và baseline (AA-729) | S245 | $5,41 | **Có ích.** Đây là thước đo trung thực đầu tiên. Nó chỉ ra các cổng đang mù. | `docs/audits/2026-10-20-S245-aa729-baseline/` |
| Panel S246: aa-779, aa-780, aa-845 | S246 | ~$0,34 | Xác nhận thêm. Cổng duyệt 15/15 bài LinkedIn, panel chỉ cho qua 4/15. Có 11 bài qua sai, và 73% bài dùng câu sáo. | `docs/audits/2026-10-21-S246-eval-panels/` |
| Thiết kế Quality System v1 và Writing Memory | S245 (thiết kế, chưa có code) | Dự kiến ~$27/tháng cho QS và $30–50/tháng cho WM | Chưa chạy. Theo kế hoạch, thay đổi đầu tiên chạm vào khâu viết rơi vào khoảng phiên thứ 4. | `docs/audits/2026-10-20-S245-quality-system/design.md`; `docs/audits/2026-10-20-S245-writing-learning-loop/README.md` |

Tóm lại, hai thứ thật sự có tác dụng là sửa đầu vào và vệ sinh cơ học. Mọi hướng "thêm thứ để bắt lỗi" đều không làm đổi số đo độc lập.

## 2. Chẩn đoán gốc

**Nguyên nhân 1. Thước đo mù, và mình đã tối ưu theo chính thước đo đó (Goodhart).**
- Ở chế độ regenerate, pipeline cho qua 84,0% bài có nhãn đạt và 85,3% bài có nhãn hỏng. Với S1: 84,1% bài hỏng được qua, bài đạt chỉ qua 50%. Với LinkedIn thì cả hai loại đều qua 100% (`report-regenerate.md`). Ở chế độ chỉ chấm điểm, cổng lệch với nhãn trên 43,6% của 94 mẫu.
- Tín hiệu quyết định của A1 là `min(validate, judge)`. Judge này chỉ chấm brand_fit và **không hề nhìn thấy nguồn** (`judge_node.py:107-119, :233`; `brand_fit.py:422-450`). Các mã được phép chặn cứng đều là lỗi định dạng hoặc lỗi từ cấm (`graph.py:189-193`).
- Phần nội dung bịa không phải con số (tên, cấp thác, lời hứa dịch vụ) không có bộ dò nào đang chạy, vì ngưỡng reject của Jev là NULL (`grounding.py:222-243`).

**Nguyên nhân 2. Người viết bị chính prompt và đầu vào đẩy đi bịa.**
- Prompt tự mâu thuẫn:
  - day_body đòi "route type, distance, terrain, transfers, included activities" (`prompts.py:399-405`).
  - Ví dụ meta "GOOD" lại hứa "expert local guides and comfortable transfers" (`:408-411`).
  - Rule 8 bảo "expand it with concrete detail".
  - Brand rule `s1:default` đòi "a real distance, a real number".
  - Rule 6 thì cấm tất cả những thứ trên. Model giải mâu thuẫn bằng cách đoán.
- Đầu vào sai trước khi viết:
  - Nguồn không có mốc "Day N" thì số ngày lấy từ số nguyên đầu tiên của trường duration, nên "3 hours" thành 3 ngày. Trong 9 mẫu golden rơi vào nhánh này, 8 mẫu hỏng (`prompts.py:57-96`).
  - Từ khoá DataForSEO thô được đưa vào làm từ khoá đích, ví dụ "bicycle shop in tokyo" cho một tour đạp xe.
  - T2 không đọc inclusions và T3 kiểm tra dựa trên chính bản master. Vì vậy cái gì A1 bịa ra thì mọi tenant đều coi là "có nguồn" (`t2_rewrite_job.py:28-55`).
- Người viết S1 là Haiku, chưa từng được A/B về chất lượng. `few_shots=[]` ở cả 3 nơi gọi (`s1_batch.py:154`, `admin_pipeline.py:1062`, `v1_pipeline.py:171`).
- Ép độ dài: mỗi ngày phải dài 0,6–1,5 lần ngày nguồn, kèm tối đa 3 lần nhắc mở rộng. Ngày nguồn mỏng thì chỉ còn cách độn chữ hoặc bịa.

**Nguyên nhân 3. Các bước sửa sau khi viết tự đẻ ra lỗi.**
- Retry và HITL được quyết trước khi chạy grounding. flag_fix lại chạy *sau* grounding, nên viết thêm chữ mà không ai kiểm (`graph.py:1151-1175`).
- Bước cắt chữ cho meta để lại câu cụt. Khoảng 10/50 meta S1 bị cắt cụt, ví dụ "...on a single 20-kilometre.".
- Ở T9, 20% lần retry thêm lỗi mới. Khoảng 40% "lỗi mới" của F9 là do judge tự đổi ý trên đúng đoạn văn cũ (`08-pipeline-stats-thu-jev.md §2`).
- S1 tốn 4,36 lần gọi người viết mỗi tour, T2 tốn 6,6. Phần viết và cổng có khoảng 10.600 dòng code và 112 commit kể từ 20/09.

**Nguyên nhân 4. Công sức đặt lệch khỏi chỗ quyết định chất lượng.**
- S1 là gốc. Nó đi thẳng lên TripPlanner (892 trang) và nuôi atom, T2, T9. Hiện TripPlanner mới ở Dev, chưa có người đọc thật.
- Trong 18 mẫu S1 rải đều theo nước (lát ít thiên lệch nhất), 14 mẫu hỏng. Các lỗi chạm thẳng tới khách: "6,000 warriors" trong khi nguồn ghi gần 2.000, tàu "3 giờ" tự bịa, lịch trình đứt ở ngày 9/13.
- Từ 11/10, T9 có 58 commit, S1 có 16.

**Nguyên nhân 5. Không có sự thật từ người và không có người đọc thật.**
- Golden set có 1/100 nhãn của người. Gói 40 bài AA-783 chưa được gán nhãn. Hàng đợi review có 0 quyết định của người.
- Panel AI đồng thuận với nhau ở mức κ 0,48 (aa-780). 26/82 lỗi panel nêu ra hoá ra là do chỉ đọc đoạn trích.
- Cả 4 tenant đều là tenant giả.
- Những thứ agency cần nhất (độ khó, thể lực, cỡ đoàn, loại trừ) phần lớn **không có trong nguồn nhà cung cấp**. Đây là vấn đề dữ liệu sản phẩm, viết văn không giải quyết được. Ở các bài đã viết, người viết hoặc bịa ra (ví dụ "fitness" xuất hiện trong 4 nguồn nhưng 7 bài viết ra), hoặc bỏ đi ("not included" có trong 6 nguồn nhưng chỉ còn trong 2 bài).

Phân bổ lỗi theo nguyên nhân chính, trên 66 bài có nhãn hỏng (một agent mã hoá, coi là ước lượng, không phải tỷ lệ cho cả catalog):

| Nguyên nhân | Tỷ lệ |
|---|---|
| Người viết lệch dữ kiện | 47% |
| Brief, angle hoặc đầu vào sai | 20% |
| Hỏng cấu trúc do bước sửa | 15% |
| Lấp chỗ trống khi nguồn mỏng | 14% |
| Giọng văn hoặc câu sáo là lỗi quyết định | 5% |

Nguồn: `.tmp-session/s246-quality-advisory/content-lens-coding.json`.

## 3. Nội dung tốt cho AA trông như thế nào

Nguyên tắc: dữ kiện đứng trước. Chỗ nào nguồn thiếu thì nói thẳng là thiếu. Giữ một điểm hút có thật. Viết ngắn. Các bản "SAU" bên dưới do agent viết, chỉ dùng dữ kiện trong nguồn. Đây là bản mẫu để anh và chị Thư góp ý, chưa phải bản cuối.

**Ví dụ 1: S1 tour nửa ngày, s1-045 "Route P: Perfect Days – Asakusa, Oshiage where Hirayama lives"**
- TRƯỚC (đã ship, panel đánh hỏng vì sai phạm vi):
  - Tên: "Tokyo Backstreets: Asakusa & Oshiage by Bike — Half Day".
  - Mô tả: "A three-hour cycling route… following local commute paths".
  - Từ khoá: "nakahechi route", "mountain biking japan".
  - Bài viết làm mất luôn bộ phim, tức là lý do duy nhất người ta mua tour này.
- SAU:
  - Tên: "Perfect Days by Bike: Hirayama's Tokyo in Asakusa and Oshiage (Half Day)".
  - Mở bài: "The ride starts the way the film does, with a can of coffee. Then you follow Hirayama's Tokyo: the Route 6 expressway he commutes on, his apartment in Kameido (outside only), Denki-yu bathhouse (no bathing), Sakurabashi bridge, Bar Nobu, Chikyu-do bookshop and Fukuchan."
  - Dữ kiện: xuất phát 09:00 hoặc 13:00, về lúc 12:00 hoặc 16:00. Người lớn ¥9.000, trẻ em ¥5.000. Bao gồm xe, mũ bảo hiểm, nước, hướng dẫn viên.
  - *Hỏi nhà cung cấp trước khi bán:* cự ly đạp, tuổi tối thiểu, có vào bên trong bar/hiệu sách/quán ăn hay không.

**Ví dụ 2: S1 tour trong ngày, s1-008 "1 Day Trishuli River Rafting"**
- TRƯỚC: "Four-hour run… on Class III–IV rapids", cấp thác lặp lại ở 5 trường. Nguồn **không hề** ghi cấp thác, nên đây là một lời khẳng định an toàn không có căn cứ.
- SAU: "After an early breakfast you're driven 3–4 hours to the put-in at Fishling. After a safety briefing you raft about four hours down the Trishuli to Mugling, with lunch on the riverbank. From Mugling you can return to Kathmandu or continue to Chitwan or Pokhara."
  - Bao gồm: chèo bè có hướng dẫn và đội lái, đồ nghề, bữa trưa.
  - Không bao gồm: đồ uống, phí máy ảnh, bảo hiểm.
  - *Hỏi nhà cung cấp:* cấp thác theo tháng, tuổi tối thiểu và yêu cầu biết bơi, xe đưa đón có bao gồm không, giờ ăn trưa (hai chỗ trong nguồn ghi khác nhau), đơn vị nào vận hành (nguồn ghi hai tên).

**Ví dụ 3: T9 LinkedIn, Terra Family, t9l-005 Tiger's Nest**
- TRƯỚC (cổng duyệt, panel chấm source_fidelity 4):
  - "The elevation gain is significant, roughly 900 metres above the Paro Valley floor". Con số 900 m là độ cao vách đá, bị biến thành độ cao phải leo. Sai này đến từ angle T8.
  - Câu kết rỗng: "Terra Family Expeditions plans this kind of detail…".
- SAU (khoảng 150 từ, chỉ dùng dữ kiện trong seed): "Three things to tell your kids before Tiger's Nest. 1) It's a long walk: most visitors take two to three hours each way through blue pine and rhododendron. 2) Bags and cameras stay at a checkpoint. 3) Dress modestly. Why it's worth it: the monastery clings to a cliff about 900 metres above the Paro Valley floor…"
  - Con số 900 m giờ gắn đúng danh từ. Bài có nội dung thực dụng cho gia đình và không còn câu sáo kiểu "thương hiệu làm chủ ngữ".

Ba ví dụ có chung một bài học: bài tốt đến từ việc **đưa đúng dữ kiện cho người viết và cho phép nói "chưa rõ"**. Thêm cổng kiểm không tạo ra được điều đó.

## 4. Các hướng đi

### Phương án A: Đơn giản hoá triệt để
Nội dung: bảng dữ kiện, một người viết mạnh, kiểm bằng code, người là thước đo. Chỉ làm S1, đóng băng phần còn lại.

**Điểm mạnh**
- Gọi đúng tên mẫu hình sai.
- Bỏ đúng các dòng prompt gây bịa.
- Bỏ bước sửa chạy sau grounding.
- Có ngân sách luật và các lượt xoá code.
- Biến chỗ "không có trong nguồn" thành danh sách câu hỏi cho nhà cung cấp. Trong hai phương án, chỉ ý này chạm tới giá trị thật cho agency.

**Điểm yếu, sau phản biện**
- Mốc so sánh sai. Phương án lấy "đăng nguyên văn 20% → 70% trong 4 tuần", nhưng lát rải đều có 18 bài chứ không phải 20. Cả 6 bài "đạt" đều cần sửa nhẹ, nên mốc đăng nguyên văn thật gần bằng 0 và mục tiêu 70% là ảo.
- Bắt anh chấm 20 bài mỗi tuần. Điều này trái với nếp "Claude làm audit, anh duyệt", và gói AA-783 cũng đã nằm im 8 phiên.
- Kiểm bằng code không bắt được các lỗi nghĩa: gắn số nhầm danh từ, kiến thức của model đè lên nguồn, tô vẽ. Trong khi đó chính sách lại cho phép viết nền về địa danh.
- A/B không có control lặp, nên dễ lặp lại kết cục của AA-748.
- Chạy nhỏ giọt 50 tour mỗi tuần đi vòng qua quy tắc "chạy tập con" và "chạy lại sạch một lần". Mỗi lần đổi S1 còn kéo theo a3_atomize và tính lại Segment/Route.
- Lấy ví dụ mẫu từ chính golden set gây rò rỉ: bài kiểm tra trùng với bài mẫu.

### Phương án B: Tiến hoá có hệ thống, nhắm lại vào khâu viết
Nội dung: giữ golden set, QS v1 và WM, nhưng đổi thứ tự: bảng dữ kiện, bộ kiểm bằng code và phẫu thuật prompt S1 làm trước, kèm một scorecard hằng tuần.

**Điểm mạnh**
- Giữ được kế hoạch anh vừa duyệt. Q-2 (AA-925) đã chứa sẵn day-count oracle và phần sửa meta fitter.
- Đặt fidelity làm tín hiệu quyết định, brand fit chỉ dùng để xếp hạng.
- T2 đọc bảng dữ kiện và T3 kiểm dựa trên bảng đó. Đây là sửa lỗi có ích nhất cho B2B.
- FAQ lấy câu hỏi theo từng địa điểm (search_demand) thay cho PAA theo tên tour.
- Thêm 10 tour ngẫu nhiên mỗi tuần để tránh khớp quá mức vào golden set.

**Điểm yếu, sau phản biện**
- Chỉ số "pass-all" ghép ba thước có độ tin khác nhau, và không có mốc tương đương để so.
- Bài kiểm của bộ checker dựa trên 6 bài đạt, nghĩa là 1 bài đã bằng 17%. Thống kê như vậy gần như rỗng.
- A/B không có control lặp, và chỉ so Haiku với Sonnet, trái bài học #96: Luna từng thắng Sonnet ở place card.
- Cũng lấy ví dụ mẫu từ golden set.
- Mang theo nhiều bề mặt hạ tầng. Bước "gom lại ở phiên 5" dễ bị trượt.

### Khuyến nghị: B đã sửa, tức là "Sửa đầu vào và người viết S1, đo bằng nhãn có neo người"

Lấy khung của B để giữ kế hoạch đã duyệt và làm Q-2 trước. Lấy phần lõi của A: đóng băng T9, ngân sách luật, xoá máy móc thừa, danh sách hỏi nhà cung cấp. Đồng thời sửa các lỗi mà phản biện đã chỉ ra:

1. **Mốc trung thực.** Trên 50 bài S1: 0 bài đăng nguyên văn, 6/50 sửa nhẹ (12%). Trên lát rải đều: 4/18. Báo cả hai mức "nguyên văn" và "nguyên văn hoặc sửa nhẹ", kèm số lỗi bịa nghiêm trọng.
2. **Nhãn.** Claude chạy panel với một rubric cố định, đọc toàn bộ nguồn và không biết bài thuộc nhánh nào. Anh chỉ phân xử các bài panel bất đồng cộng 10 bài ngẫu nhiên, khoảng 30 phút mỗi vòng. Chị Thư chỉ xem một lần, sau khi xong bảng hỏi CRM.
3. **A/B có control lặp** (A và A'), n = 50 mỗi nhánh. Thử cả ba nhà: Haiku, Sonnet, Luna. Nhánh thắng phải vượt khoảng nhiễu A–A'.
4. **Ví dụ mẫu lấy từ tour ngoài golden set** để không rò rỉ.
5. **Không chạy lại catalog** cho tới khi có kết luận. Khi có kết luận thì chạy sạch một lần theo nước, và xin duyệt chi phí riêng.
6. **Tiêu chí dừng và phương án B.** Nếu không nhánh nào vượt nhiễu: (i) trang S1 ngắn, chỉ dữ kiện cộng một câu hút; hoặc (ii) dùng thẻ lịch trình có cấu trúc thay cho văn xuôi; hoặc (iii) người biên tập nhẹ cho khoảng 50 tour bán chạy, còn lại để nguyên.
7. **Không hứa "bắt hết bịa bằng code".** Code bắt số, tên ngoài bảng, số ngày, câu cụt. Phần nghĩa thì để một câu hỏi LLM hẹp ("lời hứa hoặc dịch vụ không có trong bảng dữ kiện") chạy ở chế độ shadow, chỉ thành cổng khi có ≥ 100 nhãn và precision ≥ 0,9.

## 5. Kế hoạch 3–5 phiên tới

| Phiên | Bước | Ai làm | Chi phí | Số đo thành công |
|---|---|---|---|---|
| S247 | **0.** Duyệt lại thứ tự kế hoạch. Đóng băng: không thêm cổng/regex/lexicon/vòng sửa; dừng tinh chỉnh T9 (AA-779 vòng luật, AA-780, AA-789, AA-790, AA-924, G7 của AA-741). Giữ AA-915 (đóng băng pipeline_lessons). | Anh 15 phút; Claude cập nhật `docs/backlog/README.md` | $0 | Backlog §3 đặt S1 lên đầu. 0 commit thêm cổng trong 4 tuần. |
| S247 | **1.** Bảng dữ kiện cho mỗi tour: loại thời lượng (theo giờ/1 ngày/nhiều ngày), danh sách ngày, điểm dừng, số gắn với danh từ, địa danh, bao gồm/tuỳ chọn/loại trừ, mâu thuẫn trong nguồn, danh sách "không có trong nguồn". Mỗi giá trị trỏ về câu gốc, code kiểm từng câu. Gộp day-count oracle (Q-2). Viết bộ kiểm bằng code và chạy trên 50 bài S1 cũ. | Claude, khoảng 1 phiên | $0–1 (Haiku trích xuất, 3 rồi 50 tour) | 100% giá trị có câu gốc khớp nguyên văn. 9 tour bị lỗi day-count có cấu trúc ngày đúng. Báo TPR/TNR theo từng loại lỗi; ghi rõ chỉ có n = 6 bài đạt. |
| S248 | **2.** Phẫu thuật prompt S1, đặt sau flag: bỏ dòng day_body, ví dụ meta có lời hứa, rule 8 "expand", "real number", khối brand-diff/contrast, phần append lessons. Mẫu lịch trình theo loại thời lượng; ngày mỏng được phép ngắn (bỏ tỷ lệ 0,6–1,5 và các lần nhắc mở rộng). Meta viết bằng một call riêng, code kiểm và cho viết lại một lần, không cắt chữ. Từ khoá phải qua ngưỡng liên quan. Thêm 3–5 ví dụ mẫu từ tour **ngoài** golden set. | Claude 1 phiên; anh sửa ví dụ mẫu khoảng 1 giờ. Đây là PR rủi ro nên có subagent review độc lập. | $0 để xây; chạy thử 3 tour khoảng $0,1 | ≤ 3 lần gọi LLM mỗi tour (hiện 4,36). Ba tour thử: 0 vi phạm theo bộ kiểm, 0 meta cụt. |
| S248–S249 | **3.** A/B quyết định trên 50 tour golden S1. A = pipeline hiện tại chạy mới. A' = chạy lại y hệt để đo nhiễu. B = đường mới với Haiku. C = đường mới với Sonnet. D = đường mới với Luna. Thử 3 tour trước, rồi 50. Panel rubric cố định, đọc toàn nguồn, không biết nhánh. Anh phân xử khoảng 30 bài. | Claude 0,5–1 phiên; anh khoảng 30–45 phút | Ước tính $12–15 tổng (A và A' khoảng $3, B khoảng $1,5, C khoảng $7–9, D chưa đo). Chia 2 lần chạy, mỗi lần ≤ $10. | Nhánh thắng phải vượt khoảng nhiễu A–A'. Mục tiêu: "nguyên văn hoặc sửa nhẹ" trên lát rải đều từ 4/18 lên ≥ 10/18; lỗi bịa nghiêm trọng giảm ít nhất một nửa. Không đạt thì chuyển sang phương án B ở mục 4. |
| S250 | **4.** Nối nhánh thắng vào đường S1, đặt sau flag, ở chế độ **shadow hoặc review**, chưa publish lên Master để tránh kéo theo a3_atomize. A1 quyết bằng bộ kiểm code; brand_fit thôi làm cổng; tắt flag_fix nhắc mở rộng và vòng sửa meta. Danh sách "hỏi nhà cung cấp" hiện trong admin. T2 đọc bảng dữ kiện, T3 kiểm theo bảng. | Claude 1 phiên, có review độc lập và guard bảng job | ~$1–9 cho ≤ 50 tour | Vi phạm theo bộ kiểm giảm ≥ 50% so với A. 0 meta cụt. Golden T2: 0 lỗi inclusion. |
| S251 | **5.** Gom lại: xoá các cổng mà bộ kiểm đã làm thừa (≥ 5 cổng); chỉ giữ phần P0 của WM (lưu diff chỉnh sửa, AA-916). Anh quyết: có chạy lại catalog không, theo nước, với chi phí nêu rõ; QS và WM P1+ có làm tiếp không. | Claude 1 phiên; anh 20 phút | $0. Chạy lại catalog là quyết định riêng (Sonnet ước tính $100–160; Haiku khoảng $15–20) | Số cổng giảm. Có quyết định go/no-go bằng văn bản kèm chi phí. |

**Những việc nên DỪNG**
- Báo tỷ lệ cổng duyệt, "% tự lên Master" hay số retry như thể đó là số chất lượng.
- Thêm cổng, regex, lexicon, vòng sửa, hay thêm call để ổn định judge. Áp dụng ngân sách luật: chỉ thêm luật khi một loại lỗi vẫn còn trên golden set sau khi đã sửa prompt hoặc đầu vào, và thêm một luật thì bỏ một luật.
- Dùng brand_fit, vốn không thấy nguồn, để quyết retry hay HITL cho A1.
- Chạy bước sửa sau grounding; cắt chữ cho meta.
- Ép độ dài: tỷ lệ theo ngày, sàn 4.700 ký tự cho blog, sàn 120 từ cho LinkedIn.
- Đưa từ khoá DFS thô và PAA theo tên tour vào người viết.
- Calib Jev cho văn xuôi (AA-845, AA-803). Jev chỉ giữ cho A3.
- Tinh chỉnh T9 cho 4 tenant giả.
- Dùng lại một bộ dev 6 request cho mọi vòng; dùng panel đổi rubric làm sự thật.
- Xây hạ tầng meta (taxonomy, registry, replay, WM P1+) trước khi người viết được sửa.

## 6. Cách đo để chị Thư thấy chất lượng

Chị Thư không cần thấy F9 hay κ. Chị cần thấy bài trước và sau, và một vài con số đời thường.

1. **Một trang so sánh 10 tour, trước và sau, đặt cạnh nhau** (sau A/B ở S249). Mỗi tour chỉ hỏi ba câu, theo dạng phiếu khảo sát trung tính như chị quen: "Gửi được cho agency không? (được / sửa nhẹ / không)", "Thiếu hay sai gì?", "Danh sách hỏi nhà cung cấp có dùng được cho vận hành không?". Thời gian khoảng 20 phút. Gửi sau khi chị xong bảng hỏi CRM, không dồn hai việc một lúc.
2. **Ba con số mỗi tháng, viết bằng lời thường:**
   - Trong 20 tour ngẫu nhiên, bao nhiêu tour đăng được nguyên văn, bao nhiêu chỉ cần sửa nhẹ.
   - Bao nhiêu tour có lỗi bịa nghiêm trọng (sai số liệu, sai số ngày, hứa dịch vụ không có).
   - Bao nhiêu câu hỏi đang chờ nhà cung cấp trả lời.
3. **Danh sách "hỏi nhà cung cấp trước khi bán"** theo từng tour. Đây là giá trị chị thấy ngay. Đề xuất nhẹ: thêm các trường độ khó, thể lực, cỡ đoàn, tuổi tối thiểu, loại trừ vào khâu nhập Excel (A0). AA-Booking cũng dùng được các trường này. Việc có làm hay không là chị quyết.
4. **Khi có agency thật:** nhờ 1–2 nhân viên agency đọc 10 bài một lần ("có dán vào trang của mình không?") để hiệu chỉnh panel AI. Video UAT vẫn làm sau cùng như đã thống nhất (AA-855).

## 7. Quyết định cần anh duyệt

1. **Đổi thứ tự kế hoạch S245?** Đề xuất: có. S1 (bảng dữ kiện, bộ kiểm code, prompt, A/B người viết) làm trước. QS taxonomy, registry và WM P1+ để sau khi S1 có kết quả. Giữ Q-2 và AA-915.
2. **Đóng băng tinh chỉnh T9 và cấm thêm cổng mới?** Đề xuất: có, cho tới khi S1 đạt mục tiêu hoặc có tenant thật.
3. **Ai gán nhãn?** Đề xuất: Claude chạy panel với rubric cố định, đọc toàn nguồn, không biết nhánh. Anh chỉ phân xử bất đồng cộng 10 bài ngẫu nhiên, khoảng 30 phút mỗi vòng.
4. **A/B người viết S1 làm thế nào?** Đề xuất: 4 nhánh cộng control lặp (A, A', Haiku, Sonnet, Luna), 50 tour golden, ước tính $12–15, chia 2 lần chạy mỗi lần ≤ $10.
5. **Xử lý dữ kiện agency cần mà nguồn không có thế nào?** Đề xuất: không cho người viết suy ra. Xuất danh sách "hỏi nhà cung cấp" và đề xuất nhẹ với chị Thư về các trường dữ liệu có cấu trúc ở A0.
6. **Có chạy lại cả catalog không?** Đề xuất: chưa. Chỉ chạy sạch một lần theo nước sau khi A/B thắng rõ, và xin duyệt chi phí riêng.
7. **Jev cho văn xuôi?** Đề xuất: tắt các câu hỏi văn xuôi (a1_claim_supported, a1_promise_unsupported), ngừng calib. Jev chỉ giữ cho A3.
8. **Không nhánh nào vượt nhiễu thì sao?** Đề xuất: chuyển sang trang S1 ngắn chỉ dữ kiện cộng một câu hút, và người biên tập nhẹ cho khoảng 50 tour ưu tiên. Không mở thêm vòng gate.
