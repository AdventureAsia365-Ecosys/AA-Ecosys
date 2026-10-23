# S1-first bước 0/1: bảng dữ kiện + bộ kiểm bằng code trên 50 bài S1 (S248)

*Tác nhân: Claude Code (lane s1-step01, S248). $0: không gọi LLM, không đọc DB (dùng fixture golden 1.1.0, đã có
nguồn đầy đủ + trang đã viết + nhãn). Refs AA-645 (bước 2 của chuỗi). Code: AA-CIS-App nhánh
`feat/s1-step01-code-checks`.*

## 0. Trả lời ngắn

- **Bước 0/1 là gì** (định nghĩa trong `docs/audits/2026-10-21-S246-content-quality-advisory/README.md` §5 và
  `q4-q8-followup.md` §2.2 + §5): (a) bảng dữ kiện cho mỗi tour, mỗi giá trị trỏ về câu gốc, có MISSING / CONFLICT /
  DO NOT USE, tách "trích nguyên văn" và "tóm tắt có trỏ câu gốc", gộp day-count oracle; (b) bộ kiểm bằng code (đếm
  ngày, số không có trong nguồn, meta cụt / quá dài, tên ngoài bảng) chạy trên 50 bài S1 cũ, báo TPR/TNR theo loại
  lỗi; (c) panel chấm lại 10–15 trang hai lần để đo độ lặp; (d) chốt rubric. Phần "duyệt lại thứ tự + đóng băng"
  của bước 0 đã chốt ở S246 (Q1 = a, backlog §3 đặt S1 lên đầu).
- **Đã xong:** (a) 50/50 bảng dữ kiện, **8.673 giá trị nguyên văn, 0 giá trị lệch nguồn** (`verify_pointers`); 9/9
  tour không có mốc "Day N" có cấu trúc ngày đúng (1 ngày hoặc dưới 1 ngày). (b) bộ kiểm chạy trên 50 bài, có
  TPR/TNR theo 6 loại lỗi + chấm tay từng phát hiện (119 phát hiện). (d) rubric panel v1 đã chốt (`panel/rubric.md`).
- **Chưa xong, chỉ thiếu một hành động:** (c) hai lượt panel. Gói đã dựng sẵn (`panel/build_packet.py`, 12 trang:
  4 đạt + 8 trượt, seed 248, thứ tự khác nhau mỗi lượt) và script đo độ lặp (`panel/score_repeatability.py`).
  Lane không được tự sinh subagent → **orchestrator cần chạy 2 agent độc lập** (mỗi agent 1 gói, context mới), $0.
- **Kết luận cho bước 2:** code bắt chắc các lỗi **cấu trúc** (ngày, meta cụt, thân bị cắt, bao gồm bị loại trừ) với
  độ chính xác cao; bắt được **một phần lỗi số**; **không** bắt được lỗi nghĩa (39/50 bài có lỗi nghĩa — bịa lời hứa,
  sai hướng, sai phạm vi). Vì vậy đúng như kế hoạch: code là **cổng** (phải về ~0 ở A+, W, E), thước chính của A/B là
  panel đếm lỗi nghĩa.
- **Hai lỗi thật trong code đang chạy, đã sửa trong cùng nhánh:** day oracle (AA-925) đọc "Day 05 & 06" /
  "Day 11, 12 & 13" thành một ngày nên phạt oan writer `DAY_OUTPUT_EXTRA` (s1-004); `meta_complete_sentence` coi
  meta kết thúc bằng "…Hoi An." là cụt (từ "An"), làm bật mã cứng A1 `META_INCOMPLETE_SENTENCE` (s1-016).

## 1. Bảng dữ kiện (fact table) — `services/quality/s1_facts.py`

Dựng hoàn toàn bằng code từ nguồn thô (11 trường S1 đọc). File đầy đủ: `fact-tables.json` (50 bảng).

| Mục | Loại | Nội dung | Tổng trên 50 tour |
|---|---|---|---|
| duration | tóm tắt có trỏ câu gốc | loại thời lượng (hours / one_day / multi_day) + số ngày/đêm | 41 nhiều ngày, 6 một ngày, 3 dưới một ngày |
| days | nguyên văn | dòng "Day N" của nguồn (khoảng "Day 2 & 3" mở rộng) + địa danh trong khối ngày | 428 dòng, 3.864 địa danh theo ngày |
| schedule | nguyên văn | dòng giờ ("09:00 – …") và điểm dừng đánh số của tour không có "Day N" | 16 |
| places | nguyên văn | tên riêng trong nguồn, kèm câu chứa nó | 2.216 |
| numbers | nguyên văn | số + đơn vị / danh từ đi sau ("20km", "30 species of mammals"), vai trò (số liệu / thứ tự / giờ / nhãn) | 1.684 |
| included / excluded / optional | nguyên văn | dòng bao gồm / loại trừ, câu "not included" ở mọi trường, câu điều kiện ("optional", "if time permits", "we will try to") | 299 / 120 / 43 |
| conflicts | tóm tắt có trỏ câu gốc | nguồn tự mâu thuẫn | 4 thời lượng ≠ số mốc ngày (s1-005, 006, 016, 021); 1 bữa ăn vừa gồm vừa trừ có phạm vi (s1-041) |
| missing | tóm tắt | trường agency cần mà nguồn không có = danh sách "hỏi nhà cung cấp" | cỡ đoàn thiếu 44/50, tuổi tối thiểu 41, giờ xuất phát 36, loại trừ 27, độ khó 32, giá 18, bữa ăn 6, chỗ ở 3, phương tiện 3 |
| do_not_use | nguyên văn | URL, e-mail, điện thoại, tên nhà cung cấp lọt trong nguồn | 3 (Temple Tiger, Venture Travel ×2 tour) |

- Số "missing" khớp đếm thô của q4-q8 §3 (cỡ đoàn có ở 6–9/50, tuổi 7–9/50, độ khó 17–18/50, giờ 14–15/50, bữa ăn
  43–44/50, chỗ ở 46–47/50).
- **4 mâu thuẫn thời lượng chính là các ca nhãn golden từng phạt writer** (s1-006 "9 Days" mà có Day 10, s1-016,
  s1-021): khi bảng dữ kiện ghi rõ CONFLICT, người viết mới không phải đoán, và lỗi đó thành câu hỏi nhà cung cấp.
- `raw_tours.group_size` và `best_time_to_go` là cột riêng, **writer S1 hiện không nhận** (không có trong
  `SOURCE_FIELDS`, `prompts.py` không đọc). Bước 2 nên đưa vào bảng dữ kiện; số cỡ đoàn trong catalog cần đọc DB
  (script `heldout/fetch_heldout.py` có đếm sẵn, xem §5).
- Giới hạn: danh sách địa danh là heuristic (chữ hoa trừ từ đầu câu); nguồn viết hoa kiểu tiêu đề ("Sleeping
  Tents") lọt từ thường. Đủ cho bộ kiểm; nếu làm đầu vào writer thì có thể cần một lượt trích bằng LLM sau.

## 2. Bộ kiểm bằng code — `services/quality/s1_checks.py`

Tái dùng đúng hàm pipeline đang dùng cho từng câu hỏi (day oracle, `meta_cut_signature`, `find_novel_numeric_claims`
trên `source_number_parts`, `find_novel_word_numbers`), thêm 3 kiểm mới: `DAY_PLACE_MISMATCH` (tiêu đề ngày đặt một
điểm dừng mà nguồn để ở ngày khác), `meta_list_cut` (danh sách cuối meta mất "and"), `NUMBER_NOUN_MISMATCH` (số có
trong nguồn nhưng với đơn vị khác loại: "50 minutes" vs "50 slate houses"). **Chỉ đo, không phải cổng:** không nối
vào `graph.py` (S1-first đóng băng cổng mới).

### 2.1 Theo mẫu (sample-level, 50 bài; nhãn golden làm chuẩn — `ground-truth.json`, viết TRƯỚC khi chạy kiểm)

| Loại lỗi | Bài có lỗi (nhãn) | Bắt đúng | TPR (Wilson 95%) | Báo nhầm trên bài không có nhãn loại đó | TNR (Wilson 95%) |
|---|---|---|---|---|---|
| Cấu trúc ngày | 8 | 7 | 0,88 (0,53–0,98) | 6 | 0,86 (0,72–0,93) |
| Meta cụt | 14 | 8 | 0,57 (0,33–0,79) | 0 | 1,00 (0,90–1,00) |
| Thân bị cắt | 1 | 1 | 1,00 | 0 | 1,00 |
| Số liệu | 19 | 8 | 0,42 (0,23–0,64) | 5 | 0,84 (0,67–0,93) |
| Tên riêng | 12 | 11 | 0,92 (0,65–0,99) | 19 | 0,50 (0,35–0,65) |
| Bao gồm sai | 6 | 2 | 0,33 (0,10–0,70) | 0 | 1,00 (0,92–1,00) |
| Lỗi nghĩa khác (bịa lời hứa, sai hướng, sai phạm vi…) | 39 | — | code không bắt (theo thiết kế) | — | — |

- **Chỉ có 6 bài đạt** (nhãn pass, đều "sửa nhẹ"), nên TNR trên riêng 6 bài đó gần như không nói lên gì; TNR ở bảng
  trên tính trên mọi bài không có nhãn loại đó. Trên 6 bài đạt, bộ kiểm có 9 phát hiện ở 3 bài: 3 đúng (meta cụt ở
  s1-011 và s1-035, số 5.200 m không có trong nguồn ở s1-015 — đúng chỗ nhãn ghi "sửa nhẹ"), 3 nền địa danh, 3 báo
  nhầm ("Stars", "Gurdwara Sis" do nguồn viết dính "SisGanj", "45 minutes" do nguồn viết "3h45m").
  Với các mã dùng làm cổng (§4.2) thì trên 6 bài đạt chỉ có 3 phát hiện, cả 3 đúng.
- Nhãn không liệt kê hết lỗi, nên "báo nhầm" ở bảng trên gồm cả lỗi thật chưa được gắn nhãn. Bảng 2.2 tách ra.
- s1-006 tính là "bắt đúng" cấu trúc ngày nhưng lỗi nhãn nêu (tiêu đề 9 ngày, có Day 10) là mâu thuẫn của nguồn,
  bộ kiểm báo `SOURCE_DAY_CONTRADICTION` (không phạt writer); cái bắt được ở s1-006 là một lỗi thật khác (đặt Than Bok
  Khorani vào vùng Phang Nga). s1-021 (bị trượt) cũng là mâu thuẫn nguồn.

### 2.2 Theo phát hiện (chấm tay 119 phát hiện so với nguồn đầy đủ — `adjudication.json`)

L = đúng lỗi nhãn nêu · R-sai = sai/không có trong nguồn, chưa gắn nhãn · R-nền = nền địa danh không có trong nguồn
(chính sách writer cho phép) · S = mâu thuẫn của nguồn · M = meta ngoài 140–155 ký tự · U = không rõ · F = báo nhầm.

| Mã | Tổng | L | R-sai | R-nền | S | M | U | F |
|---|---|---|---|---|---|---|---|---|
| DAY_SUBDAY_SPLIT / DAY_COUNT_VS_DURATION / DAY_DEPARTURE_MIDTRIP | 3 | 3 | | | | | | |
| DAY_PLACE_MISMATCH | 13 | 4 | 1 | | | | 2 | 6 |
| SOURCE_DAY_CONTRADICTION | 4 | | | | 4 | | | |
| META_CUT | 8 | 8 | | | | | | |
| META_LENGTH | 3 | | | | | 3 | | |
| TEXT_TRUNCATED | 1 | 1 | | | | | | |
| NUMBER_NOT_IN_SOURCE | 10 | 3 | 2 | 5 | | | | |
| NUMBER_NOUN_MISMATCH | 7 | 5 | | 1 | | | | 1 |
| INCLUSION_CONTRADICTED | 2 | 2 | | | | | | |
| NAME_NOT_IN_SOURCE | 68 | 8 | | 44 | | | | 16 |

Đọc bảng:
- **Cổng chắc chắn được (độ chính xác ~100% trên 50 bài):** cấu trúc ngày của oracle, meta cụt, thân bị cắt, bao
  gồm bị loại trừ, số không có trong nguồn (mọi phát hiện đều là "không có trong nguồn"; 5/10 là nền địa danh như
  "Sigiriya cao 200 m").
- **`DAY_PLACE_MISMATCH`:** 5/13 đúng, 6 báo nhầm (ngày trong nguồn không nêu tên nơi ở, từ chung như "Meadows").
  Dùng để soi, chưa đủ làm cổng.
- **`NAME_NOT_IN_SOURCE`:** 52/68 là tên thật không có trong nguồn, nhưng 44 trong đó là nền địa danh hợp lệ theo
  chính sách hiện tại. Chỉ thành cổng được nếu bước 2 **cấm tên ngoài bảng dữ kiện** (xem §4, quyết định D2).
- **Lỗi số bị trượt (11/19 bài):** chủ yếu là số CÓ trong nguồn nhưng gắn sai danh từ không đơn vị ("30 lakes" vs
  "30 species"), sai hướng ("descending 1,570 m" là độ cao leo), số La Mã ("Class III–IV"), đếm bằng chữ không có đơn
  vị ("three countries", "ten major stops"). Code không đọc nghĩa → để panel.

### 2.3 Lặp lại / dùng lại

```bash
cd apps/AA-CIS-App   # nhánh feat/s1-step01-code-checks
python3 -m scripts.s1_step01.fixture_report --fixture ../../docs/eval/aa729/fixture-1.1.0.json \
  --ground-truth ../../docs/audits/2026-10-23-S248-s1-step01/ground-truth.json --out /tmp/s1-results.json
# cùng script cho một nhánh A/B: --pages <list {sample_id, tour, output}>
```

**Giới hạn trung thực:** bộ kiểm được phát triển và đo trên **cùng** 50 bài (không có tập giữ lại), nên TPR ở đây lạc
quan. Lần đọc giữ lại đầu tiên là các nhánh A/B ở bước 3 (trang mới), hoặc 80 trang live ngoài golden (§5). Một người
chấm (lane này) cho bảng 2.2.

## 3. Panel chấm lại ×2 (đo độ lặp) — gói sẵn, chờ chạy

- `panel/rubric.md` — rubric v1 cố định cho cả bước 0/1 và A/B bước 3: 9 lớp lỗi nghĩa, mức nghiêm trọng, verdict 4
  mức, `checkable_claims` (mẫu số để chuẩn hoá theo độ dài), câu so cặp "agency đăng trang nào".
- `panel/selection.json` — 12 trang: s1-040, 049, 015, 035 (đạt) + s1-010, 006, 024, 014, 019, 050, 007, 008 (trượt).
- Chạy (orchestrator, $0):
  1. `cd docs/audits/2026-10-23-S248-s1-step01/panel && python3 build_packet.py --fixture ../../../eval/aa729/fixture-1.1.0.json`
     → `packet-a.json`, `packet-b.json` (không nhãn, không verdict pipeline, không phát hiện của code).
  2. Hai agent độc lập (context mới, không thấy file khác trong thư mục), mỗi agent: đọc `rubric.md` + một gói, ghi
     `pass-a.json` / `pass-b.json` đúng schema trong rubric.
  3. `python3 score_repeatability.py pass-a.json pass-b.json --labels ../../../eval/aa729/fixture-1.1.0.json`
     → đồng thuận verdict (κ 4 mức và đạt/trượt), tổng lỗi nghiêm trọng mỗi lượt và **tỉ số A/A** (dải nhiễu mà tỉ
     số W/A+ ở bước 3 phải vượt), chênh lệch tỉ lệ lỗi / khẳng định.

## 4. Bước 2 (AA-645) cần gì từ kết quả này

1. **Đầu vào writer = bảng dữ kiện**, không phải nguồn thô: `build_fact_table(tour)` đã có; bước 2 chỉ cần định dạng
   nó thành khối prompt (thời lượng + loại, ngày + điểm dừng, bao gồm / loại trừ / tuỳ chọn, CONFLICT, MISSING,
   DO NOT USE). Thêm `raw_tours.group_size` / `best_time_to_go` vào đầu vào.
2. **Cổng code cho A+, W, E** (phải về ~0 trước khi tính thắng/thua): `DAY_*` của oracle, `META_CUT` (+ list cut),
   `META_LENGTH`, `TEXT_TRUNCATED`, `NUMBER_NOT_IN_SOURCE`, `INCLUSION_CONTRADICTED`. Đo bằng
   `fixture_report --pages` trên từng nhánh. `DAY_PLACE_MISMATCH` và `NAME_NOT_IN_SOURCE` chỉ báo cáo.
3. **Quyết định cho Nghiệp (D2, cần trước khi viết prompt bước 2):** người viết mới có được thêm nền địa danh ngoài
   bảng dữ kiện không? Đề xuất: **cho phép như chính sách hiện tại** (writer-source-fidelity: nền về địa danh được,
   không hứa hoạt động) nhưng **cấm số liệu ngoài bảng** — code bắt chắc phần số; tên thì để panel. Nếu cấm luôn tên
   ngoài bảng thì `NAME_NOT_IN_SOURCE` thành cổng được ngay.
4. **Thước chính A/B = panel đếm lỗi nghĩa nghiêm trọng / khẳng định kiểm được** (rubric v1), vì 39/50 bài có lỗi
   nghĩa mà code không chạm tới. Dải nhiễu lấy từ hai lượt panel §3 — **phải chạy trước run 1**.
5. **Danh sách "hỏi nhà cung cấp"** = `missing` + `conflicts` của bảng dữ kiện — bước 4 hiện nó trong admin.
6. **A+ (control):** day oracle đã sửa (khoảng ngày dạng danh sách) + meta gọi riêng; meta cụt ở 14/50 bài cũ, và
   hai hàm pipeline hiện có (`meta_cut_signature` + `meta_complete_sentence`) chỉ bắt 3/14 (thêm `meta_list_cut`
   lên 8/14) → A+ cần bước meta riêng thật sự, không chỉ cắt chữ.
7. **12 tour ngoài golden cho sàng 3 model** và held-out cho bộ kiểm: `heldout/fetch_heldout.py` (SELECT, ghi 1 file
   JSON vào `s3://aa-cis-bronze-…/scripts/out/s248-s1-step01/`) — lane không chạy được vì hook chặn ECS exec cho
   subagent; orchestrator chạy theo §5.

## 5. Việc orchestrator chạy sau (tuỳ chọn, $0)

Held-out 80 trang live ngoài golden (SELECT only, `cis_app`, ssl=require):

```bash
aws s3 cp docs/audits/2026-10-23-S248-s1-step01/heldout/fetch_heldout.py s3://aa-cis-bronze-005097885195/scripts/s248_s1_fetch.py --profile aa365-admin --region us-west-1
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/s248_s1_fetch.py --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s248f.py && python3 /tmp/s248f.py'" --profile aa365-admin --region us-west-1
# in ra KEY=scripts/out/s248-s1-step01/<uuid>.json.gz và số thống kê catalog (group_size / best_time / exclusions / price)
aws s3 cp s3://aa-cis-bronze-005097885195/<KEY> .tmp-session/s248-s1/heldout.json.gz --profile aa365-admin --region us-west-1
python3 docs/audits/2026-10-23-S248-s1-step01/heldout/to_pages.py .tmp-session/s248-s1/heldout.json.gz .tmp-session/s248-s1/heldout-pages.json
cd apps/AA-CIS-App && python3 -m scripts.s1_step01.fixture_report --pages ../../.tmp-session/s248-s1/heldout-pages.json --out ../../.tmp-session/s248-s1/heldout-results.json
```

## 6. File

| File | Nội dung |
|---|---|
| `ground-truth.json` | nhãn theo loại lỗi cho 50 bài (từ lý do nhãn golden + đọc meta), viết trước khi chạy kiểm |
| `results.json` | mỗi bài: tóm tắt bảng dữ kiện, vi phạm con trỏ (0), mọi phát hiện; bảng nhầm lẫn theo loại |
| `fact-tables.json` | 50 bảng dữ kiện đầy đủ |
| `adjudication.json` | chấm tay 119 phát hiện |
| `panel/` | rubric v1, chọn 12 trang, dựng gói, đo độ lặp |
| `heldout/` | fetch 80 trang live ngoài golden (SELECT) + chuyển sang định dạng `--pages` |
