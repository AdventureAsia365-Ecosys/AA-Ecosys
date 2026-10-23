# Vòng hiệu chuẩn và tự học cho toàn hệ thống: một bàn gán nhãn chung cho mọi stage

> Bản tư vấn cho Nghiệp · S248 · 23/10/2026 · Tác nhân: Claude Code (lane `aa985-f17`) · Refs AA-985
> Trạng thái: **ĐỀ XUẤT**. Chưa tạo issue, chưa có migration. Các quyết định chờ Nghiệp ở §9.
> Nguồn yêu cầu, ghi chú duyệt S248 của Nghiệp:
> - **d17:** "đây là vấn đề cần suy nghĩ cơ chế hay 1 trang cho việc đánh nhãn, hoặc huấn luyện hệ thống cho toàn bộ các stage/flow khác không chỉ phần viết tour"
> - **d18:** "phân tích kỹ để xem lỗi có tính hệ thống và các lỗi tương tự để hướng tới hiệu chuẩn, huấn luyện tự học cho cả hệ thống"
>
> Bản này **xây tiếp** trên Quality System v1 (`../2026-10-20-S245-quality-system/design.md`, gọi tắt **QS**) và Writing Memory v1
> (`../2026-10-20-S245-writing-learning-loop/`, gọi tắt **WM**). Nó không viết lại hai bản đó. Nó chỉ thêm ba thứ hai bản đó chưa phủ:
> (1) **mọi stage**, không chỉ ba writer A1, T2, T9; (2) **một bàn gán nhãn chung**; (3) **một họ lỗi mới** do AA-985 lộ ra.

---

## 0. Tóm tắt một trang

**Trả lời d17: cần cả cơ chế lẫn một trang.**

- **Trang:** dựng *một* "Label Desk" chung, theo đúng mẫu AA-783: artifact claude.ai lưu nhãn bằng db, rồi một script xuất vào DB.
  Mỗi đơn vị gán nhãn là *một quyết định của một detector ở một stage*: finding của gate, quyết định Jev, keep/drop của selector,
  kết quả extract, verdict của judge, hoặc lỗi bị bỏ sót. Đơn vị không phải "một bài viết".
- **Cơ chế:** nhãn → precision/recall theo từng (stage × detector × lớp lỗi) → regression gate trong CI → phản hồi ngược về
  luật, ngưỡng Jev, rubric và few-shot của judge, writer. Mỗi đường phản hồi có lan can riêng (§6).
  Đây chính là vòng Q-CAL/Q-LEARN của QS, mở rộng từ 3 writer ra **25+ điểm quyết định** của A0–A4, T0–T11 và TripPlanner (§2).

**Trả lời d18: lỗi AA-985 có tính hệ thống.**

Nó thuộc một họ lỗi chung: **luật tất định dùng dấu hiệu từ vựng thay cho danh tính** ("identity binding"). Luật thấy đúng từ khoá
nhưng gắn nó vào sai thực thể, sai vai trò, sai thời điểm hoặc sai phạm vi. Ca này: câu nói "government offices for district
administration", tức một vai trò cấp huyện *hiện có*, bị coi là vai trò quốc gia *đã chấm dứt*.

Ít nhất **7 lỗi đã sửa trước đây** thuộc cùng họ: AA-779 (Karakoram, "Mongolian beef"), AA-914, Thimphu S234, AA-785, AA-984,
AA-768 r2, AA-694 (§1.3). Mỗi lần ta vá bằng regex cho một ca. Bài học AA-779 D10 đã ghi rằng vá kiểu đó không hội tụ.

**Đề xuất chính:**

1. Thêm họ lớp `identity.*` (5 lớp) vào taxonomy QS (AA-926). Gắn nó cho mọi detector có dùng dấu hiệu từ vựng.
2. Một bàn gán nhãn chung (§4), lưu ở **một bảng nhãn mức item** `shared.quality_label`. Đây là quyết định E1, vì nó lệch với
   nguyên tắc "không thêm bảng" của QS.
3. Mỗi FP được gán nhãn của một luật tất định sẽ thành **test tham số hoá hai chiều**, cộng **census trước/sau** trên ledger đã
   lưu, giống census AA-985 làm mẫu (§5.3).
4. Ngưỡng Jev hiệu chỉnh bằng nhãn. Bảng `shared.decision_question` đã có sẵn cột `accept_floor`, `reject_ceiling`,
   `threshold_version` và `calibration_ref`, chỉ chưa dùng tới.

**Chi phí:** khoảng $2–8/tháng, nằm trong trần chung $40/tháng của QS D3. Không dịch vụ AWS mới. Chi phí lớn nhất là **thời gian
gán nhãn của Nghiệp**, đề xuất 20–30 item/tuần (~20–30 phút).

**Lộ trình:** 6 lát việc. 2 lát làm được ngay ở $0. 4 lát gộp vào issue có sẵn (AA-923, AA-926, AA-918, AA-922), theo đúng luật
"ít issue" của Linear Free. Chỉ đề xuất **2 issue mới**, và chưa tạo (§8).

---

## 1. Ca AA-985 và họ lỗi "identity binding"

### 1.1 Chuyện gì đã xảy ra

Blog 4b58f52c (Bhutan, request 3c9dc7bb) bị giữ ở `F17_trip_fact`:

> says it still holds a role the source dates as ended (the capital and seat of government of Bhutan, until 1955)

cho câu "Like all dzongs, it houses both monk bodies and government offices for district administration".

Nguồn chỉ ghi vai trò **thủ đô và nơi đặt chính phủ quốc gia** đã chấm dứt năm 1955. Câu viết nói về văn phòng hành chính
**cấp huyện**, một vai trò dzong vẫn giữ tới nay. Câu viết đúng, gate sai.

### 1.2 Nguyên nhân gốc (trong code)

`trip_facts.date_authority_claims` → `_gov_claim`:

- Luật bỏ cụm "cấp địa phương" chỉ theo **một thứ tự từ**: `<district> [từ] <government>`. Câu thật dùng thứ tự ngược:
  "government offices **for** district administration". Luật xoá "district administration" và còn sót lại "government offices".
- "government" đứng một mình được xếp vào nhóm từ **mạnh**, tức luôn bị coi là vai trò quốc gia. Cộng với động từ hiện tại
  "houses", luật fire.

Câu luật thực sự hỏi là "nơi này còn chức năng chính quyền nào không?". Câu nó cần hỏi là "nơi này còn giữ **đúng vai trò** mà
nguồn ghi là đã chấm dứt không?". Luật nhận ra **địa điểm** nhưng không xét **vai trò**.

**Đã sửa** (CIS, nhánh `fix/aa985-f17-role-identity`):

- Hàm `role_claim` quyết định theo danh tính vai trò.
- Cụm địa phương được nhận ở **cả hai** thứ tự từ, và kéo cả mệnh đề về vai trò địa phương trừ khi có phạm vi quốc gia.
- "government offices/officials" (cơ quan *được đặt* trong toà nhà) và "spiritual/cultural capital" (một loại thủ đô khác)
  chỉ tính khi có phạm vi quốc gia.
- Khi vai trò đã chấm dứt *là* vai trò địa phương, luật so cụm địa phương với cụm địa phương.
- Kiểm khoảng năm (span) chỉ chạy trên câu nói về chính vai trò đó.
- Test hai chiều: 8 câu "vai trò khác, còn hiện hữu" không fire; 7 câu "đúng vai trò đã chấm dứt" vẫn fire.

Replay offline $0 trên 40 bài AA-783: 12 bài có vai trò đã chấm dứt, trước 1 finding, sau 1 finding. Finding đó là true positive
("why it remains Bhutan's spiritual and administrative center") và vẫn được giữ. Census trên toàn bộ ledger từ 01/10 do agent
điều phối chạy (§5.3).

### 1.3 Các lỗi tương tự: một họ, không phải một ca

| Ca (phiên, issue) | Luật thấy gì (dấu hiệu từ vựng) | Danh tính bị nhầm | Đã vá thế nào |
|---|---|---|---|
| AA-985 (S248) | "government" + động từ hiện tại | **vai trò**: huyện ↔ quốc gia | `role_claim` (bản này) |
| S234 r3, Thimphu | "capital" + "today" | **thực thể**: nơi kế nhiệm ↔ nơi này | `EndedRole.successor` |
| S234 r3, "almost four centuries ago" | "N centuries" | **mốc thời gian**: tính từ nay ↔ khoảng của vai trò | bỏ qua khi có "ago" |
| AA-779 (S245) | tên riêng, tính từ quốc tịch | **địa danh**: Karakoram, "Mongolian beef", "Burmese python" | 3 vòng vá + review đối kháng, *không hội tụ*, dừng theo D10 |
| AA-914 (S245) | địa danh trùng tên | **quốc gia**: Segment của nước khác | route guard theo nước |
| AA-785 (S235) | chuỗi năm "1652", "1880s" | **dạng số**: năm ↔ thập kỷ ↔ số thường | dạng năm riêng cho F1 |
| AA-768 r2 | "six hundred" ↔ "600" | **giá trị**: cùng số, khác cách viết | chuẩn hoá số chữ |
| AA-984 (S248) | câu bị F9 gắn cờ | **vị trí**: heading ↔ thân bài | `locate_heading` |
| AA-694 (S223) | từ khoá trong tên tour | **chủ thể**: keyword về tour ↔ về nơi | gán nhãn tay rồi chuyển sang Jev |
| AA-771 (S234) | câu khẳng định trong bài | **người nói**: brand tự mô tả ↔ fact về chuyến | tách nhãn "BRAND CORE IDEA" |

**Điểm chung.** Cả 10 ca:

- Một luật (hoặc một prompt) quyết định "câu này nói về X" chỉ dựa trên việc **từ của X có mặt**.
- Lỗi chỉ lộ ra khi có ai đọc tận tay một bài bị giữ.
- Ta sửa từng ca bằng thêm một nhánh regex.

**Vì sao đây là lỗi hệ thống, không phải lỗi lặt vặt:**

1. Không có **bộ mẫu gán nhãn theo detector**. Ta không biết precision của `date_authority_claims` hay bất kỳ luật F17 nào khác.
   Chỉ có nhãn mức *bài* (AA-729 golden, AA-783).
2. Không có **lớp lỗi** cho kiểu "nhận đúng từ, gắn sai danh tính". Vì vậy mỗi ca được coi là một bug riêng.
3. Không có **replay** trên finding đã lưu. Mỗi lần sửa, ta chỉ biết ca của mình đã hết, không biết ca nào khác đổi theo. Ngoại
   lệ duy nhất là census AA-984 và AA-985, đều viết tay.

### 1.4 Nơi khác có cùng rủi ro (chưa có số, cần census)

Các luật tất định dùng cùng kiểu dấu hiệu từ vựng, trong `trip_facts.py` / `hygiene.py`:

| Luật | Dấu hiệu | Danh tính dễ nhầm |
|---|---|---|
| `optional_as_fixed` | tên hoạt động trong câu | hoạt động tuỳ chọn ↔ hoạt động khác cùng từ |
| `timing_claims` | "first night", "mid-morning" | thời điểm của chuyến ↔ thời điểm chung của nơi chốn |
| `background_bases` | tên địa danh + "gateway / base" | nơi chuyến tới ↔ nơi chỉ nêu làm bối cảnh |
| `missing_family_caveat` (`names_moment`) | tên moment | moment này ↔ moment cùng tên vùng |
| `rarity_claims` | "most", "no equivalent" | lượng từ của nguồn ↔ lượng từ của câu khác |
| `pace_claims`, `service_claims` | từ về nhịp / dịch vụ | nguồn của moment này ↔ của moment khác |
| F12 scope (`hygiene`) | tên địa danh ngoài phạm vi | trong phạm vi ↔ trùng tên ngoài phạm vi |

**Đề xuất:** mở rộng census AA-985 thành census cho **mọi** kiểu finding của F17/F12 (lát C1, §8). Đếm theo tiền tố problem, rút
mẫu cho bàn gán nhãn. Chỉ sửa luật nào có FP rate thật cao, không sửa theo cảm giác.

---

## 2. Kiểm kê các điểm quyết định theo stage

**Nguồn:** `skill/aa-ecosys-repos/references/pipeline.md`, `CONTEXT.md` của CIS, các migration `decision_question` (181–211),
`db-schema-reference.md` (dump 23/10). Cột "Đo hôm nay" chỉ ghi những gì **có chỗ lưu**. Kiểm kê này theo code và tài liệu,
chưa kiểm số live.

**Ký hiệu:**

- Kiểu: **R** = luật tất định, **L** = judge/LLM, **J** = Jev `decide()`, **H** = người.
- Nhãn: **có** = có bộ nhãn dùng được để đo precision/recall; **bài** = chỉ có nhãn mức bài; **—** = chưa có.

| Stage | Điểm quyết định (detector) | Kiểu | Verdict lưu ở | Đo hôm nay | Nhãn | Lỗ hổng chính |
|---|---|---|---|---|---|---|
| A0 ingest | `a0_row_kind`, `a0_country`, `a0_itinerary_usable`, `a0_column_map` | J/L | `decision_log` | zone, cost | — | Nhầm nước, nhầm dòng làm hỏng cả chuỗi phía sau mà không ai thấy |
| A1 viết Master | validate (`_HARD_BLOCK_CODES`), `s1_judge` brand_fit, `brand_audit`, `a1_claim_supported`, `a1_promise_unsupported`, `s1_source_facts`, oracle ngày | R/L/J | `quality_scores`, `generated_content`, `decision_log` | điểm, zone | **bài** (AA-729 S1 50) | κ của judge mới đo một lần. Precision của từng mã validate chưa đo |
| A2 review | flag_fix ≤2 vòng, review queue | R/L/**H** | `review_queue.review_status`, `reviewer_notes` | trạng thái review | **H có sẵn, chưa dùng làm nhãn** | Quyết định duyệt/trả của người là tín hiệu nhãn miễn phí nhưng chưa được map về detector |
| A3 atomize | `a3_atomize` (Luna validate), `a3_atom_in_text` | L/J | `tour_atoms`, `decision_log` | zone | — | Atom bịa hay atom thiếu không đo được |
| A3 segment / rank | `a3_activity_type`, `a3_same_place`, `a3_landing_belongs`, `a3_idea_traveller`, exclusion | J/R | `atom_ranking`, `decision_log` | zone | AA-694 (CSV cũ) | Bài học S223: luật loại phải khớp quyết định *cuối* |
| A3 research | `a3_keyword_belongs`, `a3_demand_belongs`, `a3_question_about_here`, `a3_question_foreign` | J | `decision_log`, cache `search_demand` | zone | **có** (AA-779 ~150 câu PAA) | Bộ AA-779 chỉ phủ PAA |
| A3 place cards | `a3_place_card`, `a3_place_card_check`, `a3_place_locate`, `a3_place_dedupe(_check)`, `a3_place_embed`, `a3_place_days` | L/J | `place_card`, `place_card_alias`, `place_card_miss` | cost, miss | AA-691/AA-774 (một lần) | Thẻ dùng chung cho TripPlanner, nên một lỗi ở đây lan sang cả B2C |
| A4 oversight | trang Social Content, Content Quality | H | — | — | — | Người xem nhưng không để lại nhãn có cấu trúc |
| T0 brand | brand brief parser | L | `tenant_brand_rules` | — | — | Rule brand parse sai thì mọi bài T9 đều lệch |
| T2/T3 | `t2_judge`, `t2_brand_audit`, `t2_flag_fix`, `t2_itinerary_nudge`, T3 QA gate | L/R | `tenant_tour_versions`, `quality_scores` | điểm, `needs_review`, tỉ lệ tenant sửa | **bài** (AA-729 T2 7) | n quá nhỏ; T2 mù với F2–F4 (QS §1.3) |
| T7 slate | `t7_debate_judge`, `t7_topic_fits_brand`, brand-fit cache | L/J | `subject`, `debate_brand_fit_cache` | — | — | Cache không mang version rubric (QS §1.1 #2) |
| T8 angle | `t8_angle_answers`, `t8_angle_gen` | J/L | `angle_gate_option` | — | — | Không ai đo angle có trả lời đúng câu hỏi hay không |
| T9 write | `t9_fact_relevant`, `t9_faq_filter`, `t9_faq_answer_fit` (shadow) | J/L | `content_piece.writer_input` | verdict shadow | AA-779 S246 panel | — |
| T9/T10 gates | ~25 gate F1–F19: R như F12, F13, F14, F16, **F17**, F18, F19; L như F9 `t10_claims`, `t10_brand_voice`; J như `t10_*` | R/L/J | `content_piece.gate_ledger`, `repair_log`, `discarded_attempts` | verdict theo gate (`/admin/content-quality`) | **bài** (AA-729 T9 25, AA-783 40 bài) | **Không có nhãn mức finding**, nên FP của F17 chỉ lộ khi người đọc tay (AA-985) |
| T9 repair | `t9_repair`, truth cut, `repair_contract` | L/R | `repair_log`, `degraded[]` | degraded | — | — |
| T11 publish | idempotency, kênh | R | `publish_log` | trạng thái | — | Không phải chất lượng nội dung (ngoài phạm vi) |
| TripPlanner | browse: thẻ nơi chốn đọc từ CIS (không LLM); assembly: compose / renarrate (Bedrock) | L | event log TP | throttle, cache (AA-805) | — | Văn renarrate chưa có gate fact nào |
| Booking | giá, hold, quote B2B, hợp đồng `booking.b2b.v1` | R | `booking.*` | contract test | n/a | **Không có LLM.** Phần "hiệu chuẩn" ở đây là contract test và property test, không cần bàn gán nhãn |

**Đếm:** khoảng 40 khoá stage/câu hỏi Jev, cộng ~25 gate T10, cộng các mã validate A1. Hôm nay **chỉ 3 chỗ có nhãn dùng được
mức detector**: AA-779 PAA, AA-845 `decision_log.outcome` cho `a1_claim_supported`, và AA-694. Mọi chỗ khác chỉ có nhãn mức bài,
hoặc không có gì.

Hai tín hiệu nhãn **miễn phí đang bị bỏ phí:**

- **A2:** `review_queue.review_status` + `reviewer_notes` (người duyệt/trả).
- **T2/T9:** tenant/admin sửa câu (AA-802 silent correction, chip WM-06 khi AA-916 xong).

Cả hai nên map về detector (§4.4).

---

## 3. Bảng phân loại lỗi: thêm trục stage và họ `identity.*`

QS đã định `qtax-v1` (~17 lớp, đang nằm ở nhánh `feat/aa-926-quality-registry`, chờ go/no-go S253). Đề xuất **ba bổ sung nhỏ**,
không phải một taxonomy thứ hai:

**(a) Họ mới `identity.*`.** Severity `block`, checkability `judgement` (một phần oracle khi nguồn có cấu trúc).

| class_id | Định nghĩa (ranh giới) | Ví dụ thật |
|---|---|---|
| `identity.place` | Đúng tên, sai thực thể địa lý (đồng âm, biến thể chính tả, tính từ quốc tịch) | AA-779 Karakoram, "Mongolian beef"; AA-914 |
| `identity.role` | Đúng thực thể, sai vai trò / chức năng (quốc gia ↔ địa phương, chính quyền ↔ tôn giáo) | **AA-985**; Thimphu S234 |
| `identity.time` | Đúng sự kiện, sai mốc / khoảng (tính từ nay ↔ khoảng của vai trò; đã chấm dứt ↔ hiện tại) | "almost four centuries ago" |
| `identity.subject` | Câu nói về X bị gán cho Y (brand ↔ chuyến; keyword ↔ nơi; claim ↔ người nói) | AA-771, AA-694 |
| `identity.form` | Cùng giá trị, khác dạng viết (số chữ ↔ số; năm ↔ thập kỷ) | AA-768 r2, AA-785 |

Khác `fact.misbinding` (F2) của QS: F2 là lỗi của **writer** (gắn số đúng vào sai chủ thể). `identity.*` là lỗi của **detector**
(luật hoặc judge hiểu sai danh tính). Nhờ vậy precision của detector đo được theo lớp mà không lẫn với lỗi writer.

**(b) Trục `stage` trên mọi detector** trong registry: `A0…A4`, `T0…T11`, `TP`. Lint QS §3.4 mở rộng: mọi `question_key` Jev và mọi
`stage` trong `llm_role_config` phải map ít nhất một lớp. Hôm nay lint chỉ phủ gate T10, mã validate và chip.

**(c) Bốn họ lớp cho stage không phải writer.** Đặt trong `other.*` warn cho tới khi có ≥ 5 mẫu dương:

- `select.*`: keep/drop sai. Đã có `scope.faq_question_offtopic`; thêm `select.keyword`, `select.segment`, `select.exclusion`.
- `classify.*`: phân loại sai (`a0_row_kind`, `a0_country`, `a3_activity_type`, `a3_same_place`).
- `extract.*`: trích bịa hoặc thiếu (`a3_atom_in_text`, `a3_place_locate`, place card fact).
- `rank.*`: thứ hạng sai làm writer thấy sai input (`t8_angle_answers`, T7 debate).

---

## 4. Một bàn gán nhãn chung (Label Desk)

### 4.1 Đơn vị gán nhãn = một quyết định, không phải một bài

```
item = {
  stage, detector,                 # 'T10', 'F17_trip_fact' | 'A3', 'a3_same_place' | ...
  subject_ref,                     # piece_id / tour_id / atom_id / decision_log.id (nội bộ)
  decision,                        # fire / no_fire / keep / drop / choice / score
  evidence: { input_excerpt,       # câu hoặc đoạn đầu vào
              source_excerpt,      # đúng đoạn nguồn detector đọc (đầy đủ, không cắt: bài học AA-729 J1)
              problem_text },      # nguyên văn finding
  sampled_because                  # 'disagreement' | 'new_detector' | 'random' | 'rare_class' | 'census'
}
nhãn = { verdict: TP | FP | FN | TN | unsure,
         class_id (nếu sai),       # ví dụ identity.role
         note, labelled_by, label_source: human | panel | verifier }
```

Nhãn mức bài của AA-783 (`as_is / light / heavy / reject`) vẫn giữ nguyên làm **một loại item** (`detector = piece_verdict`).
Lý do: mức bài đo chất lượng giao cho tenant, mức quyết định đo dụng cụ đo. Hai thứ bổ sung cho nhau.

### 4.2 Một trang, nhiều loại item

Dùng lại mẫu AA-783 (`.tmp-session/aa783-page/index.html`): artifact claude.ai có capability `db` + `user`, nhãn lưu ở db của
artifact, chạy cả chế độ "memory" khi không có db, rồi script xuất (`aa783_export.py`) ghi vào DB. Thay đổi so với AA-783:

- **Hàng chờ trộn nhiều stage.** Mỗi thẻ hiển thị theo loại item: finding gate (câu, nguồn, problem), quyết định Jev (subject,
  câu hỏi, xác suất), selector (câu hỏi PAA, phạm vi), extract (đoạn nguồn và atom). Nút bấm luôn chỉ có TP / FP / unsure,
  cộng chọn lớp khi FP. Nghiệp không phải đọc một bài 1.500 từ để chấm một câu.
- **Bộ lọc theo stage / detector** để làm theo đợt ("hôm nay 20 finding F17").
- **Ghi rõ nguồn của item.** Đề xuất 1 dòng "vì sao item này ở đây" (`sampled_because`).
- **Không lộ văn tenant ra repo public.** Trang là artifact private. File export chỉ đi vào DB, không vào repo.

### 4.3 Rút mẫu (giữ việc của Nghiệp ở 20–30 item/tuần)

| Nguồn item | Tỉ lệ | Vì sao |
|---|---|---|
| Bất đồng: panel agent ↔ detector, hoặc người (A2/AA-802) ↔ detector | ~40% | Chỗ precision/recall thật sự sai |
| Detector mới hoặc mới đổi (shadow, hoặc vừa sửa như F17 sau AA-985) | ~25% | QS §5.6: lên enforce phải có số |
| Lớp hiếm hoặc `hard` | ~15% | Bảng công suất QS §5.2 |
| Ngẫu nhiên phân tầng theo stage | ~20% | Ước lượng không lệch, chống chỉ nhìn chỗ đã biết sai |

**Panel agent gán trước** (`label_source = panel`, Claude Code hoặc `eval_verify` trên ECS). Nghiệp chỉ gán: (1) các item panel
không chắc hoặc bất đồng, (2) 10 item ngẫu nhiên mỗi tuần để đo κ panel ↔ Nghiệp. Khi κ ≥ 0.6 ổn định 3 tuần, nhãn panel được
tính vào precision mà không cần Nghiệp gán từng item. Đây là cách AA-783 đã làm với nhãn `claude-draft`.

### 4.4 Tín hiệu nhãn miễn phí (map về item, không cần người gán thêm)

| Tín hiệu | Thành nhãn gì |
|---|---|
| A2 `review_queue` trả về kèm lý do trùng mã validate | TP của mã đó; duyệt mà mã còn → ứng viên FP |
| Admin "Dismiss" / `style_only` trên finding (`/admin/content-quality`) | ứng viên FP (QS §5.2) |
| AA-802 silent correction / tenant sửa đúng câu bị gắn cờ | TP |
| Tenant sửa câu **không** bị gắn cờ, có chip lớp X | ứng viên FN của lớp X |
| `decision_log.outcome` (AA-845) | TP/FP của câu hỏi Jev |
| Census replay (luật cũ fire, luật mới không) | item `census` để xác nhận |

Ứng viên vào hàng chờ, chưa phải nhãn. Một người hoặc verifier xác nhận mới tính.

### 4.5 Lưu ở đâu

Hôm nay `acp_shared.content_piece_label` chỉ có mức bài và chỉ cho T9. `decision_log.outcome` chỉ cho Jev. Tính precision theo
(stage × detector × lớp) cần **một bảng mức item**. Đề xuất (quyết định **E1**):

```
shared.quality_label (CIS, owner cis_owner, migration CIS NNN)
  item_key text            -- hash ổn định của (stage, detector, subject_ref, evidence_sha)
  stage text, detector text, subject_ref text, tenant_id uuid NULL
  decision text, verdict text CHECK (TP|FP|FN|TN|unsure), class_id text NULL
  label_source text CHECK (human|panel|verifier|signal), labelled_by text, note text
  evidence_sha256 text, taxonomy_version text, detector_version text, created_at timestamptz
  PRIMARY KEY (item_key, labelled_by)
```

- Có RLS theo tenant như `content_piece`, để nhãn trên văn tenant bị xoá khi offboard (WM-33).
- Grant `cis_app` (worker xuất nhãn, job KPI đọc).
- Không lưu văn bản: chỉ lưu `evidence_sha256` + `subject_ref`; văn đọc lại từ bảng gốc khi cần.

QS chọn "không thêm bảng" vì lúc đó chỉ có nhãn mức bài và `prompt_eval_runs`. Bảng này là ngoại lệ duy nhất. Lý do: không bảng
có sẵn nào giữ được nhãn TP/FP **theo detector cho mọi stage**. Phương án không có bảng là để nhãn chỉ trong db của artifact rồi
export JSON. Phương án đó không join được với `gate_ledger` / `decision_log`, và mất khi artifact bị xoá.

---

## 5. Từ nhãn ra số, rồi ra regression gate

### 5.1 Chỉ số theo (stage × detector × lớp)

- **Precision** = TP / (TP + FP) trên item gán nhãn. Bổ sung bằng tín hiệu Dismiss (QS §5.2). Báo cận dưới Wilson 95%.
- **Recall** = TP / (TP + FN). FN đến từ item `missed` và từ mẫu cấy lỗi (QS §5.2). Với luật tất định, cấy lỗi tốn $0.
- **κ** (judge/Jev ↔ người) cho detector L/J; **test–retest** cho L (QS §5.2).
- **FP rate theo lớp `identity.*`**: con số trực tiếp trả lời d18 ("lỗi có tính hệ thống không").

Báo cáo nằm ở **WM-31 tab Metrics** (QS §8), thêm cột `stage`. Không thêm trang admin mới.

### 5.2 Regression gate trong CI (repo app public → dữ liệu tổng hợp)

- **Mỗi FP có nhãn của luật tất định thành một test tham số hoá.** Câu được **viết lại tổng hợp** cùng shape, không chép văn
  tenant. Test kèm **ít nhất một câu TP cùng shape** để giữ chiều ngược lại. Mẫu là `tests/unit/test_aa985_f17_role_identity.py`:
  8 không-fire + 7 vẫn-fire.
- Test vào corpus Q0 của QS (`tests/quality/corpus/`, mỗi case có `expected` = truth). Flip xa truth là fail, không ghi đè được.
- Test phải **đỏ trên merge-base** (QS §6.1 c). Bước CI đó đã thiết kế trong AA-926/Q-2.
- **Sàn precision** cho detector đang enforce nằm trong `quality/thresholds.yaml` kèm `calibration_run_id`. Bản đo mới thấp hơn sàn
  thì báo đỏ trên WM-31 và mở ứng viên "hạ severity / sửa luật". Không tự tắt gate.

### 5.3 Replay trên ledger đã lưu (census): bản tổng quát hoá của AA-985

Census AA-985 (`.tmp-session/S248-lanes/aa985_census.py`, chỉ đọc, $0, chạy trong task api) làm mẫu cho R0 của QS (AA-918):

1. Đọc mọi finding đã lưu (`gate_ledger`, `repair_log`, `discarded_attempts`) của một detector từ một ngày.
2. Chạy lại **luật cũ** (bản sao đóng băng) và **luật mới** (bản đã deploy) offline trên đúng câu và nguồn đã lưu
   (`writer_input.seed`).
3. Báo old-only, new-only, both; các bài bị giữ *chỉ* vì luật đó; mẫu cho bàn gán nhãn.

Tổng quát hoá (lát C4): một module `services/eval/ledger_replay.py` nhận `(detector, old_fn, new_fn)`, chạy trên ledger T9 và
trên `decision_log` (Jev: chạy lại với ngưỡng mới, $0 vì xác suất đã lưu). Kết quả: ghi `prompt_eval_runs` và đẩy item `census`
vào hàng chờ gán nhãn. Mọi PR sửa luật F-series kèm bảng "trước/sau" lấy từ đây, thay cho các script census viết tay.

---

## 6. Nhãn quay lại hệ thống thế nào (tự học) và lan can

| Đối tượng | Đường phản hồi | Lan can |
|---|---|---|
| **Luật tất định** (F12–F19, validate A1, oracle) | FP/FN có nhãn → test hai chiều đỏ → sửa → replay trước/sau → merge | **Luật dừng D10 (AA-779):** 2 vòng sửa mà replay không hội tụ (giảm FP làm tăng FN) thì ngừng vá regex; chuyển detector sang câu hỏi Jev hoặc judge có nhãn. Mỗi PR sửa luật phải kèm số replay. |
| **Ngưỡng Jev** | Nhãn + xác suất đã lưu → chọn `accept_floor` / `reject_ceiling` trên tune split → ghi `threshold_version` + `calibration_ref` (cột **đã có** trong `decision_question`) | Chọn trên tune, báo trên holdout. Đổi ngưỡng qua migration hoặc admin PATCH có audit_log và trạng thái `reverify`. Một cú click của Nghiệp. |
| **Judge LLM** (F9, `s1_judge`, `t2_judge`, debate, `t8_angle_answers`) | (1) **few-shot exemplars** lấy từ item có nhãn, ghim theo version; (2) **rubric version**; (3) ngưỡng điểm từ đường cong precision/recall | Exemplar chỉ lấy từ tune split, không bao giờ từ holdout. κ ≥ 0.6 mới được chặn. Đổi rubric hay exemplar là "đổi judge", nên chạy Q2 (QS §4.1). Exemplar không chứa văn tenant khác (cô lập tenant). |
| **Selector** (PAA, keyword, segment, exclusion) | Bộ keep/drop có nhãn hai chiều + bộ sinh đối kháng (QS §4.5) | PR sửa "bỏ nhầm" không được làm tăng "giữ nhầm" trên bộ có nhãn, và ngược lại |
| **Writer** (A1, T2, T9) | Writing Memory (AA-915..923): rule và ví dụ theo `class_id`, release có cổng | Không tự bật (D6 a); hard/soft stop; chỉ số đối trọng chống văn nhạt (QS §7.4) |
| **Taxonomy** | Cụm FP/FN lặp ≥ 5 lần mà chưa có lớp → đề xuất lớp mới (như `identity.*` ở đây) | Thêm lớp `hard` cần Nghiệp duyệt; lớp `warn`/`block` agent thêm, báo trong PR |

**Lan can chung:**

- **Không có gì tự bật.** Tự động: đo, đề xuất, mở PR test, replay, rollback. Cần một click: ngưỡng enforce, release, lớp `hard`.
- **Chống học vẹt nhãn.** Holdout ≥ 30% mỗi detector, chỉ đọc ở train tháng (QS §7.5).
- **Đo chính người đo.** Panel agent có κ với Nghiệp. Verifier có bộ audit (QS §5.4).
- **Nhãn hết hạn.** Nhãn mang `detector_version`. Khi luật hay prompt đổi, nhãn cũ vẫn dùng để đo, nhưng item có `evidence_sha`
  đổi (nguồn đổi) bị bỏ qua và báo.
- **Cô lập tenant.** Item của tenant A không thành exemplar cho tenant B. Nhãn mức platform (A0–A4) dùng chung được.
- **Không thêm gate mới trong 4 tuần** (luật L1 S246). Bản này chỉ *đo* và *sửa luật sai*, không thêm detector chặn mới.

---

## 7. Chi phí (Dev, theo tháng)

| Hạng mục | Cách tính | $/tháng |
|---|---|---|
| Label Desk (artifact + db) | Hạ tầng claude.ai, không phải AWS | 0 |
| Bảng `shared.quality_label` | Vài nghìn dòng, không văn bản, trên RDS có sẵn | ~0 |
| Replay / census (ECS exec trên task có sẵn, hoặc job worker) | Không gọi LLM | 0 |
| Panel gán trước bằng `eval_verify` (nếu chạy trên ECS thay vì Claude Code) | ~$0.01–0.03/item × 100–250 item/tháng | 1–7.5 |
| Hiệu chỉnh ngưỡng Jev | Dùng xác suất đã lưu | 0 |
| κ test–retest judge khi đổi rubric | Đã tính trong Q-CAL của QS | (đã tính) |
| **Cộng** | | **~$2–8**, nằm trong trần chung $40/tháng (QS D3) |

Không dịch vụ AWS mới, không resource mới, không đổi chi phí cố định. **Thời gian người:** Nghiệp 20–30 item/tuần
(~20–30 phút), giảm dần khi κ panel ổn định.

---

## 8. Lộ trình: lát việc cỡ issue (đề xuất, chưa tạo)

Tuân thủ: Linear Free (ít issue, mỗi issue một lát giao được), L1 "không gate mới 4 tuần", go/no-go S253 của Q1 (AA-926, AA-916,
AA-924 đang giữ).

| Lát | Nội dung | Gộp vào | Khi nào | Chi phí | Done when |
|---|---|---|---|---|---|
| **C0** | AA-985: sửa `role_claim` + test hai chiều + census + memo này | AA-985 (đang làm) | S248–S249 | $0 (+ ≤ $0.2 regenerate 3c9dc7bb) | Census trước/sau; 3c9dc7bb không bị giữ vì lý do này |
| **C1** | Census mọi kiểu finding F17/F12 (§1.4) + panel gán ~60 item → FP rate theo luật | AA-985 (mở rộng scope) hoặc **issue mới #1** | S249–S250 | $0 replay; panel trong Claude Code | Bảng FP rate từng luật F17; luật có FP > 30% thành lát sửa riêng |
| **C2** | Label Desk v1: trang chung (mẫu AA-783), export, bảng `shared.quality_label` (migration → agent review), map tín hiệu A2/AA-802/Dismiss | **AA-923** (đang là "Labels for T2/A1…") mở rộng thành "Label desk for every stage" | Sau S253 nếu go; trang không cần migration có thể làm trước bằng db artifact | ~$0 | Nghiệp gán 20 item 3 stage khác nhau trên một trang; nhãn vào DB; κ panel ↔ Nghiệp có số |
| **C3** | Registry: trục `stage` + họ `identity.*`, `select/classify/extract/rank.*` + lint phủ `question_key` Jev | **AA-926** (nhánh đang giữ) | Cùng go S253 | $0 | Lint xanh; mọi `question_key` và gate map lớp |
| **C4** | `ledger_replay.py` tổng quát (T9 ledger + `decision_log`) | **AA-918** (R0) | P1 WM | $0 | Một PR sửa luật F17 chạy replay bằng module, không bằng script tay |
| **C5** | Precision/recall theo stage × detector × lớp trên WM-31 + hàng chờ bất đồng | **AA-922** | P3 WM | $0 SQL | Tab Metrics có cột stage; 5 detector có số |
| **C6** | Hiệu chỉnh ngưỡng Jev A3 từ nhãn (`a3_same_place`, `a3_activity_type`, `a3_landing_belongs`, `a3_atom_in_text`) bằng `calibration_ref` | **issue mới #2** "A3 Jev calibration set" | Sau C2 | $0 (xác suất đã lưu) + thời gian gán ~80 item | 4 câu hỏi có `calibration_ref`; precision trên holdout báo cáo |

**Để sau, ghi nhận để không quên:**

- TripPlanner renarrate gate fact: chờ TP có lưu lượng thật.
- Booking: contract/property test (đã có `contracts.yml`), không cần bàn gán nhãn.
- T0 brand parser: lấy nhãn từ việc tenant sửa brand rule.

---

## 9. Quyết định chờ Nghiệp (mỗi câu có đề xuất)

| # | Câu hỏi | Lựa chọn | **Đề xuất** |
|---|---|---|---|
| E1 | Lưu nhãn mức item ở đâu? | (a) bảng mới `shared.quality_label`; (b) chỉ db artifact + export JSON; (c) mở rộng `content_piece_label` | **(a)**: join được với ledger và `decision_log`, xoá theo tenant được; (c) chỉ phủ T9 |
| E2 | Ai gán nhãn? | (a) Nghiệp gán hết; (b) panel agent gán trước, Nghiệp gán bất đồng + 10 ngẫu nhiên/tuần; (c) chỉ panel | **(b)**: 20–30 item/tuần; khi κ ≥ 0.6 ổn định 3 tuần thì nhãn panel được tính |
| E3 | Họ lớp `identity.*` | (a) thêm 5 lớp vào qtax (AA-926); (b) gộp vào `fact.misbinding` | **(a)**: lỗi của detector khác lỗi của writer; tách ra mới đo được precision |
| E4 | Sửa FP của luật tất định có phải chờ go/no-go S253 không? | (a) không, đây là sửa luật sai, không phải gate mới; (b) chờ | **(a)**: kèm replay trước/sau, đúng như AA-985 |
| E5 | Luật dừng vá regex | (a) 2 vòng không hội tụ thì chuyển sang Jev hoặc judge có nhãn; (b) không có luật | **(a)**: tổng quát hoá D10 của AA-779 cho mọi detector |
| E6 | Issue | 2 mới (C1 nếu không gộp AA-985, C6) + mở rộng scope AA-923/926/918/922 | Như §8; hỏi trước khi tạo (luật Linear) |

---

## 10. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Gán nhãn thành gánh nặng, rồi bỏ dở (AA-783 vẫn chưa có nhãn của Nghiệp) | Item nhỏ (một câu, một quyết định), 20–30/tuần, panel gán trước; trang làm được trên điện thoại |
| Nhãn panel sai một cách có hệ thống | κ với Nghiệp mỗi tuần; panel đọc nguồn đầy đủ (bài học AA-729 J1); verifier khác họ model |
| Vá luật theo từng FP lại thành vòng không hội tụ | Test hai chiều bắt buộc + replay trước/sau + luật dừng E5 |
| Văn tenant lọt vào repo public | Test là câu viết lại tổng hợp; export chỉ vào DB; memo chỉ có id rút gọn và câu đã nêu trong Linear |
| Bảng mới phình | Không lưu văn, chỉ sha + ref; thêm một dòng vào sổ retention khi tạo bảng |
| Đo precision từ mẫu thiên về bất đồng làm lệch số | Báo riêng phần ngẫu nhiên phân tầng (~20%) làm ước lượng không lệch; phần bất đồng chỉ dùng để tìm lỗi |
