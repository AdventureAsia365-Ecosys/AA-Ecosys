# AA-919: rà nhãn và rubric của 13 cặp hiệu chuẩn judge (t9_social)

Phiên S256, 28/10/2026. Tác nhân: Claude Code (lane AA-919). Bản tư vấn cho tech lead.

## Bối cảnh

- R2 bước D (writer `t9_social`) đo độ khớp giữa judge và nhãn golden bằng kappa trên 13 cặp: 15 bài LinkedIn có nhãn, trừ 2 bài đã được người sửa (`t9l-006`, `t9l-007`).
- Kappa phải đạt ≥ 0,6 thì judge mới được tính (`judge_counts`).
- Kết quả S255:
  - Run `7811e7c5` (judge cũ): kappa −0,073.
  - Sau CIS #1096, run `de6265e6`: kappa 0,235, chi phí $0,221.
- Với 10 nhãn Đạt và 3 nhãn Trượt, kappa 0,235 chỉ ra được từ đúng một ma trận nhầm lẫn: judge cho Đạt 4/10 bài nhãn Đạt và đánh Trượt cả 3/3 bài nhãn Trượt. Như vậy judge vẫn khắt khe hơn nhãn ở 6 bài.
- Nguồn đọc cho bản rà này:
  - fixture `docs/eval/aa729/fixture-1.1.0.json`, cùng byte với bản trên S3. Mỗi bài đọc đủ seed, scope, brief, output và 4 phiếu panel.
  - kết quả chẩn đoán `.tmp-session/S255/aa919/kappa_diag_out.txt` (run `7811e7c5`, có verdict của judge cho từng bài).
- Còn thiếu: verdict từng bài của run `de6265e6`. Script đọc $0 `.tmp-session/S256/aa919/kappa_diag_s256.py` đã chuẩn bị sẵn để điều phối chạy và điền vào.

## Phát hiện chính: panel tự mâu thuẫn với chính nó

Rubric cũ định nghĩa hai mức:

- **Đạt** = "sửa nhẹ (vài phút, không đổi fact hay cấu trúc)".
- **Trượt** = "fact bịa hoặc sai, hứa điều nguồn không hứa…".

Một câu hứa về chuyến đi mà sửa được trong một phút thì thuộc cả hai mức. Vì vậy panel chấm cùng một loại lỗi theo hai kiểu:

| Loại lỗi | Panel chấm **Trượt nặng** | Panel chấm **Đạt nhẹ** |
|---|---|---|
| Hứa hoặc khẳng định điều nguồn không có, chỉ trong 1 câu hoặc 1 trường | `t9l-002` (meta "remains Bhutan's … administrative center"), `t9l-009` (câu mở "Day 2 ends at…"), `t9l-010` ("the plan gives it to you") | `t9l-001` (seo_title "…Your Bhutan Meditation Retreat"), `t9l-003` ("Children can watch a discipline being learned") |

Judge làm theo câu chữ của rubric thì không thể khớp cùng lúc với cả hai nhóm này. Quy tắc sản phẩm đã có là không hứa điều nguồn không có, nên cách đọc đúng là **Trượt**.

## Bảng 13 cặp

Ghi chú về các cột:

- **Judge cũ**: run `7811e7c5`, gồm verdict, điểm và mã lỗi. Đây là prompt trước #1096, chưa thấy brief và scope.
- **Judge `de6265e6`**: chỉ biết số tổng (4/10 bài Đạt được cho qua, 3/3 bài Trượt bị chặn). Cột này chờ script diag điền từng bài.
- **Kết luận** có 4 loại:
  - **nhãn sai**: sửa nhãn;
  - **rubric mơ hồ**: nhãn giữ nguyên, rubric được viết rõ thêm;
  - **judge sai**: nhãn đúng, judge chấm lệch;
  - **khớp**.

| Mẫu | Nhãn 1.1.0 | Judge cũ | Kết luận | Bằng chứng (trích văn bản) | Nhãn 1.2.0 |
|---|---|---|---|---|---|
| t9l-001 | Đạt (nhẹ) | Trượt 6, embellish + persona_promise | **Nhãn sai** | seo_title "Punakha Dzong and Your Bhutan Meditation Retreat" nói chuyến đi là khoá thiền. Itinerary chỉ có "Visit Punakha Dzong's courtyards and assembly hall". "Bhutan meditation retreat" là keyword SEO do brief giao, nhưng luật 5 vẫn đánh trượt keyword dùng như một lời hứa chuyến đi mà nguồn không có. (Review độc lập S256: bỏ ý "continuous institutional use" khỏi lý do vì bằng chứng yếu.) Panel cũng ghi nhận cái tít này là "suggests a retreat the trip does not offer" nhưng vẫn chấm nhẹ. | **Trượt (nặng)** |
| t9l-002 | Trượt (nặng) | Trượt 0 | Khớp | Meta "remains Bhutan's spiritual and administrative center" trái nguồn ("until 1955, when the capital was moved to Thimphu"). | Trượt |
| t9l-003 | Đạt (nhẹ) | Trượt 4, embellish + inclusion + persona_promise | **Nhãn sai** | "Children can watch a discipline being learned" hứa một hoạt động (xem học viên làm việc). Nguồn chỉ ghi trường nghề là một điểm trong buổi sáng tham quan Thimphu. Phiếu voice của panel đã chấm Trượt nặng; phiếu facts và reader cũng nói câu này "needs a tweak". Riêng câu nối với dzong và tu viện là brief yêu cầu, nên chỉ là lỗi nhẹ (quy tắc 5). | **Trượt (nặng)** |
| t9l-004 | Đạt (nhẹ) | Trượt 0, không mã lỗi | Rubric mơ hồ + judge cũ sai | "the sacred relics housed within" nằm trong danh sách "what you notice", chỉ ngụ ý chứ không khẳng định là khách được xem thánh tích. "where the context arrived with shapes everything encountered after" là câu hỏng ngữ pháp nhưng không sai fact. Mọi fact khác (1637, hơn ba thế kỷ, 1955, Je Khenpo) đều có trong nguồn. Judge cũ chấm Trượt điểm 0 mà không nêu mã lỗi, do luật cũ "publishable as is". | Đạt (giữ) |
| t9l-005 | Đạt (nhẹ, panel chia 2–2, tech lead quyết ở S245) | Trượt 0, embellish + misbinding + number | Rubric mơ hồ (cấu trúc), nhãn giữ | Bài mở bằng dòng trắng và nói quy định trước khi nêu tên điểm đến. "the return takes most visitors around two to three hours each way" là câu rối, nhưng con số 2–3 giờ mỗi chiều vẫn đúng nguồn. "a place of pilgrimage since the 8th century" là suy ra từ truyền thuyết thế kỷ 8 (câu có ghi "according to Bhutanese tradition"). Đây là nhãn người quyết nên không lật. Quy tắc 3 mới coi câu rối nhưng vẫn đúng là lỗi nhẹ. | Đạt (giữ) |
| t9l-008 | Đạt (nhẹ) | Trượt 8, embellish | Judge cũ sai | Điểm 8 tức là sửa nhẹ, nhưng luật cũ ép Trượt khi có mã fact. Có hashtag sai chính tả "#PasTaktsang" và cụm "built around that cave" chưa giới thiệu cái hang. Việc tắm đá nóng sau khi leo là brief yêu cầu và có trong itinerary ngày 9 (quy tắc 5). | Đạt (giữ) |
| t9l-009 | Trượt (nặng) | Trượt 6, embellish + inclusion | Khớp | "Day 2 ends at a set of turquoise limestone pools" trái nguồn, vì nguồn ghi bơi và nghỉ trước bữa trưa ở View Café. | Trượt |
| t9l-010 | Trượt (nặng) | **Đạt** 0 | Judge cũ sai (#1096 đã sửa) | Bài kể đường mòn lên viewpoint và trại gấu rồi viết "All of that is worth time. And the plan gives it to you". Meta còn hứa "time to swim and explore". Nguồn chỉ cho thời gian bơi và nghỉ. Ở run `de6265e6`, cả 3 bài nhãn Trượt đều bị chặn. | Trượt |
| t9l-011 | Đạt (nhẹ) | Trượt 6, embellish + persona_promise | Judge cũ sai | Mọi fact (đường đi bộ ngắn, hồ travertine, calcium carbonate, thác 50 m, bơi và nghỉ trước bữa trưa) đều có trong nguồn. Câu về nhịp nghỉ của Trail Pulse là brief yêu cầu. Lỗi chỉ ở câu chữ: "the same limestone that feeds the waterfall" và mô tả hồ hai lần. | Đạt (giữ) |
| t9l-012 | Đạt (nhẹ) | Đạt 9 | Khớp | Fact đầy đủ, CTA lặp chữ "journey". | Đạt |
| t9l-013 | Đạt (nhẹ) | Trượt 2, embellish + inclusion + framing | Judge cũ sai (chưa thấy brief) | Cụm "narrow strip of land" lấy từ brief ("the narrow peninsula"). "bounded, protected, given a presence…" là câu suy ngẫm, không phải khẳng định fact (quy tắc 4). Lưu ý: ý "symbolic and protective significance" là do brief T8 tự đưa ra, không có trong fact địa điểm. Lỗi này thuộc chất lượng brief (AA-790). | Đạt (giữ) |
| t9l-014 | Đạt (nhẹ) | Đạt 8 | Khớp | Fact đúng. Câu về thương hiệu ("local knowledge and a light footprint") nằm trong brief. | Đạt |
| t9l-015 | Đạt (nhẹ) | Trượt 6, embellish | Rubric mơ hồ, nhãn giữ | Meta "built in 1637 as both an administrative and religious centre still in use today" là câu mơ hồ, đọc theo hướng "toà nhà vẫn đang được dùng" thì đúng nguồn (Je Khenpo về mỗi mùa đông). Khác với t9l-002 nói thẳng "remains Bhutan's … administrative center". "Visitors enter it wearing traditional Bhutanese dress" thiếu vế "or equivalent formal attire": diễn đạt chưa chính xác nhưng không sai. Đây là cặp sát ranh nhất, quy tắc 3 xếp nó vào lỗi nhẹ. | Đạt (giữ) |

Tổng kết:

- **2 nhãn sai** (`t9l-001`, `t9l-003`), chuyển Đạt → Trượt.
- **3 nhãn đúng nhưng rubric mơ hồ** (`004`, `005`, `015`).
- **4 bài judge cũ chấm sai** (`008`, `010`, `011`, `013`). `010` đã được #1096 sửa; ba bài còn lại phụ thuộc judge có đọc brief hay không, và #1096 đã đưa brief vào nguồn cho judge.
- **4 bài khớp** (`002`, `009`, `012`, `014`).

## Đã sửa

Bước tiếp theo trên Dev là chạy lại kappa. Thay đổi gồm 3 phần:

1. **Rubric viết rõ thêm (CIS, branch `fix/aa-919-calibration-labels`, commit `af2c846c`).**
   - Thêm 5 quy tắc vào `scripts/aa729/labels.RUBRIC["rules"]`.
   - Cũng 5 quy tắc đó có trong `eval_judge.LABEL_RUBRIC["rules"]` (test ghim cho hai bản giống nhau) và trong prompt judge.
   - Nội dung tóm tắt:
     1. Mọi trường khách đọc đều tính: thân bài, tít, SEO title, meta, hashtag.
     2. Một khẳng định nguồn không đỡ, hoặc một lời hứa về chuyến đi mà itinerary không có, thì **Trượt**, kể cả khi chỉ cần sửa một cụm.
     3. Sửa nhẹ là chỉ sửa câu chữ: lỗi chính tả, lặp từ, dòng trắng, câu rối nhưng vẫn đúng, diễn đạt chưa chính xác nhưng không sai, bỏ sót một ý của brief.
     4. Câu suy ngẫm không nêu fact là giọng văn, không tính là fact.
     5. Brief và brand pack là một phần của nguồn. Nhắc tới phần khác của chuyến đi mà itinerary có, vì brief yêu cầu, thì là lỗi nhẹ. Hứa phần mà itinerary không có thì Trượt.
   - Câu prompt "a flaw a light edit removes (one phrase, one field)" ngầm coi lỗi fact một cụm là lỗi nhẹ, nên đổi thành "a flaw a wording fix removes".
   - `JUDGE_VERSION` đổi theo prompt mới.
2. **Lệnh `relabel` mới** (`python -m scripts.aa729.labels relabel …`).
   - Chỉ sửa nhãn `agent_panel`, không động tới nhãn từ người sửa, nhãn tay hay nhãn synthetic.
   - Từ chối review cũ: `from` phải khớp verdict hiện tại.
   - Bắt buộc có lý do, người duyệt và nơi ghi review.
   - Giữ nhãn cũ trong `evidence.previous` và ghi `label_history` với `source: calibration_review`.
3. **Fixture 1.2.0** (`docs/eval/aa729/fixture-1.2.0.json`, repo gốc, chưa commit).
   - Sinh bằng lệnh relabel từ [relabel-review.json](relabel-review.json), sha256 `b4b3f269…1971`.
   - Chỉ khác 1.1.0 ở 2 nhãn, số version và một dòng `label_history`.
   - Importer DRY RUN (không DB) chạy được: t9_social có 8 Đạt / 5 Trượt, tune 11, holdout 4, trap 2.

## Kappa kỳ vọng sau khi sửa (8 Đạt / 5 Trượt)

Bảng dưới là kappa theo số bài nhãn Đạt được judge cho qua (hàng) và số bài nhãn Trượt bị chặn (cột):

| Bài nhãn Đạt được cho qua | Chặn 3/5 | Chặn 4/5 | Chặn 5/5 |
|---|---|---|---|
| 4/8 | 0,093 | 0,270 | 0,435 |
| 5/8 | 0,217 | 0,395 | 0,562 |
| 6/8 | 0,350 | 0,530 | **0,698** |
| 7/8 | 0,494 | 0,675 | 0,843 |

- Muốn đạt ≥ 0,6, judge phải chặn đủ 5/5 bài Trượt và cho qua ít nhất 6/8 bài Đạt.
- Nếu `de6265e6` đã chặn `001` và `003`, chỉ riêng việc sửa nhãn đã đưa kappa lên khoảng 0,435. Phần còn lại phụ thuộc rubric mới có giúp judge cho qua `004`, `008`, `011`, `013`, `015` hay không.
- Nếu vẫn dưới 0,6, bước tiếp theo là sửa **nguồn cho judge** (cho judge thấy brand core idea như panel đã thấy), không hạ ngưỡng.

## Việc điều phối chạy (theo thứ tự)

1. Đọc $0: chạy `kappa_diag_s256.py` qua `exec_svc.sh aa-cis-dev-worker`, rồi điền cột "judge `de6265e6`" vào bảng trên.
2. Merge và deploy CIS PR (prompt judge mới). Không có migration.
3. Upload `docs/eval/aa729/fixture-1.2.0.json` lên S3 bronze `scripts/out/aa729/fixture-1.2.0.json`.
4. Chạy `import_dry.py`, rồi `import_apply.py`: set 1.2.0 thay 1.1.0, release xây trên 1.1.0 sẽ bị gắn `reverify` nhưng vẫn phục vụ bình thường.
5. Chạy `r2_dry.py` và kiểm `calibration_labels` = {pass 8, fail 5}.
6. Chạy `r2_run.py` (trả phí, trần $0,30, dự kiến khoảng $0,22, cùng dạng run `de6265e6`).
7. Chạy lại `kappa_diag_s256.py` để xem run mới và so 3 run.
8. Commit lên repo gốc: fixture 1.2.0, `relabel-review.json` và README này.
