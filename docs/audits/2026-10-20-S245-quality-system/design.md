# Quality System v1 — hệ thống viết + chấm điểm CIS có hệ thống

> Thiết kế (audit cho Nghiệp) · S245 · 20/10/2026 · Tác nhân: Claude Code
> Trạng thái: **ĐỀ XUẤT, bản 2** (đã xử lý 2 vòng phản biện, tổng 32 ý, xem §12). Chưa có code. Các quyết định chờ Nghiệp nằm ở §10 và `decisions.json`.
> Xây trên: Writing Memory v1 (`docs/audits/2026-10-20-S245-writing-learning-loop/`, AA-915..AA-923, đã duyệt D1–D16, E1–E4) và golden set AA-729.
> Định hướng gốc (Nghiệp, S245): *hệ thống viết + chấm điểm phải có hệ thống. Lỗi không lặp lại. Sửa chỗ này không sinh lỗi chỗ khác. Hệ thống tự học, tự cải thiện thay vì đội ngũ đi vá lỗi lặt vặt.*

---

## 0. Tóm tắt một trang

**Vấn đề gốc.** Trong 28 phiên (S218–S245) có 9 kiểu lỗi lặp lại (§1.2). Chúng có chung năm nguyên nhân:

1. Không có bộ mẫu cố định gán **nhãn đúng/sai** (truth). Không có bước replay $0 trên dữ liệu thật.
2. Gate và fixer được thêm theo từng triệu chứng. Không ai kiểm chúng tương tác với nhau thế nào trong **cả chuỗi** xử lý.
3. Cùng một luật được chép riêng cho từng writer (A1, T2, T9).
4. Judge LLM không tất định. Ta vá bằng cache thay vì đo và hiệu chỉnh. Chính verifier cũng chưa được đo.
5. Đường fail-open không có bộ đếm. Bài học nằm dưới dạng văn xuôi, không thành guard.

Writing Memory v1 đã giải phần "writer học từ chỉnh sửa". Nhưng nó **chỉ gác release của bộ nhớ**. Có bốn thứ nó không gác:

- PR code sửa gate, prompt, repair.
- PR code sửa **bộ chọn input** (selector): thứ quyết định writer được thấy gì (bài học AA-779).
- Chất lượng của chính các judge, gate và verifier.
- Một bảng phân loại lỗi dùng chung.

**Quality System v1 thêm 5 khối.** Cả 5 dùng chung **một engine đánh giá** với Writing Memory (mở rộng `services/eval/regression.py`, không viết engine thứ hai):

| # | Khối | Một câu |
|---|---|---|
| Q-TAX | Taxonomy lỗi gọn (~12 lớp writer + 3 an toàn + 2 phụ trợ) | Mọi mã gate, mã validate, reason chip, câu hỏi Jev, và cả selector map vào lớp (nhiều–nhiều). CI lint. |
| Q-GATE | Cổng hồi quy theo bậc, giá theo đúng nhịp PR thật | Q0 $0 trong CI mọi PR (nhãn truth, cả chuỗi xử lý). Q2 chấm lại khi judge đổi. R0 replay sau merge trên Dev ($0). Q3 viết lại **gom theo release train tháng**. |
| Q-CAL | Hiệu chỉnh judge, gate và verifier | Precision đo từ tín hiệu sản xuất ($0). Recall lớp `hard` từ golden + cấy lỗi. κ, test–retest, canary chống trôi model. Bảng công suất theo lớp. |
| Q-FIX | Quy trình sửa theo lớp | (a) lớp → (b) mẫu → (c) case **đỏ trên merge-base** (CI kiểm) → (d) sửa. Done-when theo chỉ số lớp. |
| Q-LEARN | Vòng tự học cho **writer** và **scorer** | Writer qua Writing Memory. Scorer: tỉ lệ FP/FN theo gate × lớp từ SQL $0 trong job KPI tuần, vào hàng chờ bất đồng. Có chỉ số đối trọng chống "học cách gian lận chỉ số" (Goodhart). |

Không có trang admin mới: thêm 2 mục vào tab Metrics của WM-31 và một loại ứng viên vào WM-22 (§8).

**Lộ trình.** 2 issue mới (Q-1, Q-2), khoảng 2 phiên agent. Phần còn lại gộp vào AA-916, AA-918, AA-919, AA-922, AA-779 và AA-729 (§9). Phiên làm trước: `repair_contract` + sửa fitter AA-740 + bộ đếm `degraded[]` + oracle ngày + corpus Q0 gọn. Đây là các phần nhắm vào hai kiểu lỗi đắt nhất: AA-777 (7 ngày, 3 PR, 2 vòng trả tiền) và Jev 402 âm thầm (~48k lần).

**Không thêm bảng, không thêm migration** riêng cho Quality System. Dùng `shared.spend_budget`, `shared.prompt_eval_runs` (WM-17 mở rộng), `shared.job.result`, `llm_call_log.job_id`, `acp_shared.audit_log`.

**Chi phí Dev, đã tính lại theo nhịp PR đo được** (§9.3): Quality System thường **~$27/tháng** (khoảng $17–48), cộng WM thường ~$7. Đề xuất **một trần chung $40/tháng, $10/lần chạy** cho cả học và chất lượng, thi hành bằng `shared.spend_budget` (§9.4).

---

## 1. Hiện trạng (tóm từ 4 bản nghiên cứu)

### 1.1 Pipeline và chỗ một thay đổi làm vỡ chỗ khác

| # | Điểm nối ngầm | Hệ quả khi sửa một chỗ |
|---|---|---|
| 1 | Ngưỡng 7.0 bị chép thành **5 literal** (`graph.MIN_QUALITY`, `judge_node._MIN_QUALITY`, `tenant_pipeline._T3_PASS_LINE`, `t2_rewrite_job.py:237`, `debate.BRAND_FIT_CUT_THRESHOLD`), cộng thêm `_REPEAT_BAND (6,8)` | Sửa một chỗ thì A1 retry, trạng thái T2, T3 và bước cắt Slate T7 lệch nhau. |
| 2 | `brand_fit.py` phục vụ 3 stage: A1 judge, T2 judge, T7 Debate. Cache Debate không có key theo rubric hay model. | Đổi rubric làm dịch tỉ lệ pass A1, `needs_review` của T2 và kết quả cắt Slate. Điểm cũ vẫn nằm trong cache. |
| 3 | `_HARD_BLOCK_CODES` và `validate_node` phục vụ 3 caller | Đổi severity là A1 và T2/T3 cùng đổi. |
| 4 | `find_novel_numeric_claims` phục vụ 5 consumer | Sửa grounding một nơi thì cả 5 nơi cùng đổi. |
| 5 | Danh sách từ dùng chung cho cả 2 writer và 2 chồng gate | Một từ thêm vào làm đổi prompt lẫn gate cùng lúc. |
| 6 | Tên gate là chuỗi literal ở khoảng 8 chỗ, không có registry | Đổi tên hoặc bỏ gate (như AA-787) thì dashboard và routing repair đọc tên không còn tồn tại, mà không báo lỗi gì. |
| 7 | Fixer và gate dùng chung helper theo vòng import (`hygiene` ↔ `trip_facts` ↔ `text_integrity`) | Đổi một helper là đổi cả thứ được sửa lẫn thứ bị gắn cờ. |
| 8 | Toàn bộ luồng T9 nằm trong `run_write_background` (~620 dòng) | Chuyển một gate sang tập severity khác là đổi đường repair và đổi kết quả held/approved. |
| 9 | Prompt A1 có byte pin, nhưng DB vẫn chèn thêm lesson, brand rule và route model | Model hoặc prompt đổi mà không có PR, không có test nào chạy. |
| 10 | T2 chạy trên graph của A1. Byte pin chỉ phủ A1. | Mọi node sửa trong `graph.py` đều tác động T2. |
| 11 | Env flag `T2_*` và `T3_*` không được ghi lên dòng output | Điểm số đổi mà không truy được do flag nào. |
| 12 | Harness AA-729 monkeypatch tên private. Dòng Jev eval rơi vào dashboard sản xuất. | Eval có thể làm bẩn số liệu sản xuất. |
| 13 | Tín hiệu học bị mất: chỉnh sửa T9 của tenant không giữ bản trước/sau, lesson tự động không bao giờ vào prompt, output không mang version | Không học được gì, và cũng không truy được nguyên nhân. |
| 14 | **Selector input** (lọc PAA theo phạm vi, seed builder, chọn segment, match keyword `search_demand`, `_estimate_day_count`) quyết định writer thấy gì, nhưng không có bộ keep/drop gán nhãn | AA-779: sửa "bỏ nhầm" thì sinh "giữ nhầm" (Karakoram, Darkhan, Mongolian beef, Burmese python). Gate output không thấy được loại lỗi này. |
| 15 | Kiểm ngày S1 (`ITINERARY_DAY_COUNT_MISMATCH`, `graph.py` ~L880) chỉ bắt ngày nguồn bị thiếu, trừ −1.0 điểm, không nằm trong `_HARD_BLOCK_CODES`, và **tự tắt** khi `parse_source_day_word_counts` dùng fallback | Ngày thừa, ngày trùng, "Departure" giữa chuyến, "14 days" mà 12 mục đều lọt, và lúc check tắt thì không ai biết. |
| 16 | Đã có sẵn một engine eval: `services/eval/regression.py` (AA-289, fixture xlsx 20 tour trên S3, ghi `shared.prompt_eval_runs`), `.github/workflows/eval-regression.yml` (workflow_dispatch, OIDC + ECS exec), `tests/unit/test_aa792_a1_prompt_golden.py`, fault set AA-791 | Nếu thiết kế mới bỏ qua, ta có hai engine và hai người ghi `prompt_eval_runs`. |

### 1.2 Chín kiểu lỗi lặp lại (S218–S245) và nguyên nhân

| Kiểu lặp | Ví dụ | Nguyên nhân hệ thống | Khối QS chặn nó |
|---|---|---|---|
| Repair đưa lại lỗi đã bị gỡ | AA-641/736/738/740. T9: 20% lần retry thêm fail mới. AA-777 kéo 7 ngày, 3 PR, 2 vòng trả tiền, vẫn còn 10.7%. | Không có "hợp đồng repair" chung, chỉ có các gate chạy sau | Q-GATE: `repair_contract` + test cả chuỗi trong Q0 |
| F9 tự đổi ý | Khoảng 40% "fail mới" của F9 là judge đổi đáp án. 8 PR trong 8 ngày. | Judge chưa được hiệu chỉnh hay đo độ ổn định | Q-CAL: test–retest khi judge đổi, κ, canary |
| Filter: lần sửa sau giữ quá nhiều, lần sau nữa lại bỏ quá nhiều | AA-779: 5 vòng sửa trong một phiên | Không có bộ keep/drop gán nhãn hai chiều cho **selector** | Q-TAX loại artefact "selector" + Q0 bộ hai chiều + bộ sinh đối kháng |
| Gate thêm nhanh hơn tốc độ được kiểm, rồi bị bỏ | 27 gate, 6 gate không fire lần nào, rồi AA-787 bỏ đi | Không đo precision khi thêm gate | Q-CAL: detector **mới** chạy shadow; precision từ tín hiệu sản xuất |
| Cùng một lỗi sửa riêng cho từng writer | SEO meta (5 PR), em-dash (2 PR), từ cấm | Mỗi writer một đường code | Q-TAX: lint coverage parity theo writer |
| Fail-open âm thầm | Jev trả 402 khoảng 48k lần trong 14 ngày; segment rỗng cho 566 tour; check ngày S1 tự tắt | Không có bộ đếm "degraded" | `degraded[]` + luật riêng cho detector lớp `hard` (§6.3) |
| Nhiễu ngang cỡ hiệu ứng | Nhánh control 5.00 → 3.20. Mỗi vòng là một batch n=20 mới. | Không có bộ cố định, không so cặp, không đo nhiễu writer | Q-GATE: so cặp; nhiễu judge **và** nhiễu writer đo được |
| Sửa nhầm vì không xem input | AA-768 seed chỉ là nhãn 26 ký tự | Sửa bắt đầu từ verdict, không từ input | Q-FIX bước 0: dump `writer_input` |
| Done khống, rồi mở lại | AA-769/771/772, AA-825… | Done-when gắn với tên vòng | Q-FIX: Done-when theo chỉ số lớp trên golden version cố định |

### 1.3 Phân bố lỗi thật (panel AA-729, 82 mẫu)

Đếm theo số mẫu mà lớp đó **quyết định fail**:

- `fact.inclusion` (F5): 25
- `fact.number`, `fact.misbinding`, `fact.name` (F1/F2/F3): 17 mỗi lớp
- `fact.embellish` (F8): 11
- `struct.truncated` (S2): 10
- `struct.day_structure` (S1): 8
- `fact.direction` (F4): 7
- C4, C2, F9: 5 mỗi lớp
- Phần lớn các lớp còn lại: khoảng 0

Lỗi S1 gần như toàn là **fact fidelity**. T2 fail do F5 + C4 (persona biến thành lời hứa). Blog fail do lỗi cấu trúc (S4/S5/S6) và luật brief (C3).

Ba điểm cần nhớ:

- Panel đổi kết luận đa số ở **14/82** mẫu. Trong 26 mẫu, judge chỉ đọc trích đoạn thay vì nguồn đầy đủ (J1). Vì vậy nhãn phải do **full-source verifier** chốt, và verifier cũng phải được đo (§5.4).
- Ma trận bắt/sót cho thấy đường S1/T2 gần như mù với F2/F3/F4/F9/C1/C4. Riêng S2 do chính fitter meta của AA-740 sinh ra (một bản sửa đẻ ra lỗi mới).
- Với cỡ mẫu này, chỉ **F5** có ≥ 20 mẫu dương. Mọi luật thống kê theo lớp phải tính tới điều đó (§5.2, bảng công suất).

---

## 2. Nguyên tắc thiết kế

1. **Lỗi theo lớp, không theo triệu chứng.** Mọi việc (detector, mẫu, rule học được, KPI, Done-when) đều gắn với một `class_id`.
2. **Một engine đánh giá, hai loại ứng viên.** Ứng viên là *code trên `main`* (sau merge, hoặc gom theo train) hoặc *release bộ nhớ* (Writing Memory). Cả hai đi qua cùng R0/R2 (WM-15, WM-19), cùng tiêu chí theo lớp. Engine là `services/eval/regression.py` mở rộng; chỉ nó ghi `prompt_eval_runs`.
3. **$0 trước, trả tiền sau, và trả tiền theo lô.** Luật tất định, oracle, replay dữ liệu đã lưu, cache verdict. Phần viết lại trả tiền gom theo release train, không chạy cho từng PR.
4. **So với sự thật, không chỉ so với hôm qua.** Case Q0 mang nhãn truth. Snapshot chỉ dùng cho case chưa có nhãn. Lớp kiểm được bằng oracle thì dùng oracle trên **toàn bộ** output đã lưu, không chỉ golden.
5. **So cặp, đo nhiễu cả hai phía.** Cùng input, cùng judge. Dung sai lấy từ nhiễu judge (test–retest) **và** nhiễu writer (viết lại control hai lần).
6. **Dụng cụ đo phải được hiệu chỉnh, kể cả verifier.** Detector **mới** chạy shadow tới khi có số đo. Gate đang chặn được giữ, trừ khi tỉ lệ bị gỡ cờ cao.
7. **Sửa chung, không sửa theo từng writer.** Detector khai báo nó phủ writer nào. Lint báo lỗ hổng parity.
8. **Truy được mọi output, không chép dữ liệu.** Output chỉ mang `job_id`, `release_id`, `degraded[]`. Phần còn lại (code SHA, route, flag, prompt version, taxonomy version) ghi một lần ở `shared.job.result` và join qua `job_id`.
9. **Không có gì tự bật** (Writing Memory D6 a). Tự động: đo, đề xuất, rollback, revert PR trên Dev. Cần một cú click của Nghiệp: kích hoạt release, đổi ngưỡng enforce, duyệt lô nhãn golden, quyết định theo lô cho gate có tỉ lệ gỡ cờ cao.
10. **Repo app là public.** Văn bản golden thật không vào repo. CI chỉ dùng corpus tổng hợp. Comment và status trên PR chỉ chứa số đếm và `class_id`.
11. **Chống gian lận chỉ số (Goodhart).** Mỗi chỉ số được tối ưu phải có chỉ số đối trọng không được giảm (§7.4).

---

## 3. Q-TAX — Bảng phân loại lỗi

### 3.1 Vị trí và định dạng

- File nguồn: `AA-CIS-App/quality/taxonomy.yaml`, version `qtax-v1`. Có thể public vì chỉ chứa định nghĩa và ví dụ tổng hợp.
- Registry Python `services/quality/registry.py` đọc YAML. Nó gồm:
  - hằng số tên gate, thay ~8 chỗ đang dùng literal;
  - map detector → các `class_id` (nhiều–nhiều, §3.4);
  - **một** file ngưỡng `quality/thresholds.yaml` (§5.3), thay 5 literal 7.0. Không có `thresholds.py` riêng.
- **Không có bảng mirror DB.** API admin đọc `taxonomy.yaml` có sẵn trong image.

**Đặt tên.** Dùng slug có chấm (`fact.inclusion`) để không đụng tên gate (`F1_grounding`) hay lớp fact cũ của WM (B-class, C1). Mã ngắn của panel AA-729 (F1…X1) giữ lại làm `alias`.

### 3.2 Schema mỗi lớp (gọn)

| Trường | Ý nghĩa | Ví dụ (`fact.inclusion`) |
|---|---|---|
| `id`, `alias`, `since` | Mã ổn định, mã panel, version thêm vào | `fact.inclusion`, `F5`, `qtax-v1` |
| `definition` | 1–3 câu, nêu ranh giới với lớp gần | "Bịa dịch vụ, bữa ăn, tiện ích, mức phù hợp hay tính độc quyền mà nguồn không có. Khác `fact.optional_as_firm`: ở lớp đó, mục *có* trong nguồn nhưng là tuỳ chọn." |
| `severity` | `hard` / `block` / `warn` | `hard` |
| `checkability` | `oracle` (truth suy ra được từ cấu trúc nguồn) hoặc `judgement` | `judgement` |
| `artefact` | `output` hoặc `selector` | `output` |
| `writers` | Writer áp dụng | `[A1, T2, T9_blog, T9_social]` |
| `detectors[]` | `{ref, kind: rule\|oracle\|llm\|jev, writers, mode: enforce\|shadow\|warn}` | `ITINERARY_MEAL_TIME_INVENTED` (rule, A1); `a1_claim_supported` (jev, A1); `F9_cta_fact` (llm, T9) |
| `synthetic_examples` | 2–5 ví dụ dương và âm tổng hợp, kèm nhãn truth | "Lunch included on Day 2" khi nguồn ghi "lunch not included" |

Đã bỏ: `golden_ids` (truy vấn bảng golden theo `class_id`), `coverage` (suy ra từ `detectors[].writers`), `metric` và `tolerance` (mặc định theo severity, §4.2), `owner_gate` (suy ra từ detector có `mode: enforce`).

### 3.3 Danh mục v1 (gọn)

Luật chọn: lớp có **≥ 5 mẫu dương golden** hoặc severity `hard`, cộng các lớp `safety.*`, cộng 2 lớp phụ trợ có lý do riêng. Mọi lớp khác của panel (F6, F7, S3, S4, S5, S7, C1, C3, C5, V1) vào nhóm `other.<alias>` với severity `warn` cho tới khi có ví dụ thật; detector đang có của chúng vẫn chạy như cũ, chỉ không tính vào tiêu chí cổng.

| class_id | Alias | Sev | Kiểm | S1 | T2 | T9 | Lỗ hổng chính |
|---|---|---|---|---|---|---|---|
| `fact.inclusion` | F5 | hard | judgement | P | **M** | P | T2 chỉ có điểm brand-fit |
| `fact.number` | F1 | hard | một phần oracle | P | P | P | Số viết bằng chữ, số La Mã. T3 so với master nên số master bịa vẫn lọt. |
| `fact.misbinding` | F2 | hard | judgement | P | M | P | Số đúng nhưng gắn sai chủ thể |
| `fact.name` | F3 | hard | judgement | P | M | P | Không có check tất định |
| `fact.direction` | F4 | hard | judgement | P | M | M | Không có gì kiểm hướng |
| `fact.embellish` | F8 | block | judgement | P | M | P | Phần lớn dựa vào F9 |
| `fact.self_contradiction` | F9 | block | judgement | M | M | M | Không check nào so field với field |
| `struct.day_structure` | S1 | block | **oracle** | P(soft) | M | – | Ngày thừa, trùng, Departure giữa chuyến, duration ≠ số mục; check hiện có tự tắt khi fallback |
| `struct.truncated` | S2 | block | **oracle** | P | P | P | **Do fitter AA-740 sinh ra** |
| `struct.leaked_instruction` | S6 | hard | **oracle** | M | M | P | "earns its length" |
| `scope.framing` | C2 | block | judgement | M | M | P | Title/meta không block |
| `scope.persona_promise` | C4 | hard | judgement | – | **M** | C | `audience_leaks` chỉ có ở T9 |
| `safety.tenant_isolation` | — | hard | oracle | – | – | – | Hard stop 2 của WM |
| `safety.qa_trace_visible` | — | hard | oracle | – | – | – | Hard stop 3 của WM (WM-26) |
| `safety.prompt_injection` | — | hard | judgement | – | – | – | 10 mẫu injection AA-729 |
| `scope.faq_question_offtopic` | — | block | judgement (selector) | – | – | P | **Lớp selector**, tạo ngay trong qtax-v1 (bài học AA-779) |
| `source.contradiction` | X1 | warn (ghi nhận) | oracle một phần | M | M | M | Lỗi do nguồn. Gắn nhãn để **không tính lỗi cho writer** (§6.4). |

Hai lớp đo judge (`judge.excerpt_artifact` J1, `judge.missed` J2) giữ nguyên, chỉ dùng trong Q-CAL.

**Đối chiếu với WM.** Hard stop 1 của Writing Memory ("B-class hoặc C1 fact error") được định nghĩa lại thành *mọi lớp `fact.*` có `severity: hard`*. Sửa README WM §8.2 trong cùng PR với Q-1.

### 3.4 Lint CI cho taxonomy (thuộc Q0, $0)

1. Mọi detector trong registry, mọi mã `validate_node`, mọi reason chip (WM-06) và mọi `decision_question.key` map vào **ít nhất một** `class_id`, hoặc ghi `class: none` kèm lý do. Một detector được phủ nhiều lớp (Jev `a1_claim_supported` phủ mọi `fact.*`, F9 phủ fact và voice). Khi đó **mỗi violation phải mang `class_id` riêng**, như AA-924 đã định; precision/recall tính theo (detector, lớp) từ lớp của violation.
2. Không còn literal tên gate hay ngưỡng 7.0 ngoài `registry.py` / `thresholds.yaml`. Kiểm bằng grep test.
3. Gate bị xoá được đánh dấu `retired: true`, không xoá khỏi registry. Ledger cũ vẫn đọc được.
4. **Coverage parity.** Lớp `hard`/`block` có detector ở writer X mà writer Y thì `M` → in cảnh báo trong báo cáo, không fail.
5. Mỗi lớp `hard`/`block` có ≥ 2 `synthetic_examples` có nhãn truth (1 dương, 1 âm), chạy được trong corpus Q0.
6. Mỗi file trong `paths.yaml` loại `selector` phải có bộ keep/drop trong corpus Q0.

### 3.5 Tầm với của taxonomy

- **Ledger gate (AA-924).** Mỗi violation mang `class_id` và severity riêng. AA-924 làm *sau* Q-1.
- **Writing Memory.** Rule WM-09 key theo `class_id`. 8 chip của WM-06 là tập con có tên thân thiện.
- **KPI north-star** "tỉ lệ lỗi lặp lại" (WM §8.1) đo theo `class_id`, so được giữa A1, T2 và T9.

---

## 4. Q-GATE — Cổng hồi quy cho mọi thay đổi

### 4.1 Các tầng, giá theo nhịp PR thật

Nhịp đo trên `origin/main` của AA-CIS-App, 30 ngày (squash, 1 commit = 1 PR): **454 PR**, trong đó 152 chạm path chất lượng; ~46 chạm path writer/repair (Q3), ~40 chạm path judge (Q2). Bản trước giả định ít hơn khoảng 10 lần. Thiết kế dưới đây đi theo nhịp thật.

| Tầng | Chạy ở đâu, khi nào | Chi phí | Kiểm gì |
|---|---|---|---|
| **Q0** | GitHub Actions CI, **mọi PR**, là một bước trong job pytest unit đang bắt buộc (không thêm required check, không đổi branch protection) | $0 | (1) Lint taxonomy. (2) Corpus ~50–60 case có nhãn truth chạy qua **cả chuỗi tất định** (§4.4). (3) Bộ keep/drop hai chiều cho selector. (4) `repair_contract`. (5) Kiểm thứ tự chuỗi. (6) Case mới phải đỏ trên merge-base (§6.1). (7) Byte pin prompt lấy từ WM-20. |
| **Q2** | Dev, runner score-only, **trước merge**, khi PR đổi judge prompt, rubric, anchor hoặc route judge; kích hoạt bằng label `ready-for-quality`, không chạy mỗi lần push | ~$0.3–1/lần | Chấm lại **tune split** của tier bị ảnh hưởng bằng judge cũ và judge mới. Cache verdict (§4.6). Không đụng holdout (§7.5). |
| **R0 sau merge** | Dev, job worker sau mỗi deploy có PR chạm path Q1 (= WM-15 R0, gộp vào AA-918) | $0 (worker sẵn có) | Chạy gate tất định và oracle **của `main` mới** trên output đã lưu (≈ 900 tour A1, ~300 piece T9, ~48 version T2) và trên cache ứng viên SERP/PAA cho selector. So verdict với ledger đã lưu. Lớp oracle biết ngay chiều tốt/xấu; flip ở lớp `hard` loại judgement gom tuần, ≤ 10 mục/lớp, gửi verifier. Hồi quy → agent mở PR revert (giai đoạn dev, không có người dùng). |
| **Q3** | Dev, runner R2 (WM-19), **một lần mỗi release train tháng (E1)** | ~$9–13/train, tách theo tier, mỗi lần ≤ $10 | Viết lại các tier bị ảnh hưởng bởi **mọi** PR writer/repair đã merge kể từ train trước. Control = output của train trước. Thứ tự probe 3 → tune → holdout (holdout chỉ chạy ở đây). Fail → tìm PR gây lỗi bằng revert từng PR (Dev không có người dùng). |

**Q1 trước merge (branch image chạy ECS task qua OIDC) được hoãn** tới prod đầu tiên. Lý do: build image cho mỗi PR, chạy code chưa merge trên Dev với quyền DB, và trùng với R0. Khi làm lại, phải theo §11.2 (chỉ branch cùng repo, role DB chỉ đọc trên view replay, không secret khác).

**Thay đổi không đi qua PR.** Đổi route `llm_role_config` hoặc env flag trên Dev:

- Endpoint admin đổi route ghi một dòng `acp_shared.audit_log` và đặt trạng thái **`reverify`** (WM-18). Không có bảng `quality_change`.
- Banner "route đổi, chưa có eval" hiện tới khi có một lần Q2 (judge) hoặc Q3 (writer) gắn với sự kiện đó.
- Route trước được lưu để rollback một cú click.

### 4.2 Tiêu chí pass theo lớp

So cặp trên cùng input. Với mỗi lớp, đếm **new** (baseline không có, ứng viên có) và **fixed** (ngược lại).

| Severity | Q0 / R0 (tất định, oracle) | Q2 / Q3 (LLM) |
|---|---|---|
| `hard` | Case có nhãn truth: flip **xa truth** = fail, không file nào ghi đè được. Lớp oracle trên toàn bộ output đã lưu: 0 lỗi mới. | **0 lỗi mới đã xác minh, chỉ tính trên mẫu mà cả hai lần viết control đều sạch** (nhiễu writer, §5.2). Lỗi judge gắn cờ phải qua verifier trước khi tính. Bất kỳ detector `hard` nào degraded trong lần chạy → run **INVALID**, không PASS cũng không FAIL. |
| `block` | Như trên | `new − fixed ≤ 0` **và** `new ≤ noise_k`. `noise_k = 1` chung cho tới khi tier có ≥ 20 mẫu và đã đo test–retest. |
| `warn`, `other.*` | Chỉ báo cáo | Chỉ báo cáo |
| Tổng thể | — | 4 soft stop của WM, cộng **first-pass rate** (đo trên bộ gate đóng băng ở taxonomy version của release) không giảm, **số vòng repair** không tăng, và **các chỉ số đối trọng** §7.4 không giảm. |

**Lớp dưới ngưỡng công suất** (§5.2): không dùng dung sai thống kê, chỉ "verifier xác minh, chỉ báo cáo".

### 4.3 Bất biến repair (khoá kiểu lỗi lặp số 1)

Module `services/quality/repair_contract.py`. A1 (`flag_fix_node`, `revalidate_node`) và T9 (`sentence_repair`, `rewrite_with_feedback`, truth cut, FAQ regen) đều gọi nó tại các điểm splice có sẵn.

1. **Không thêm chi tiết mới.** `new_specifics(before, after, source)` rỗng.
2. **Diff chỉ nằm trong span bị gắn cờ**, được nới tới biên câu.
3. **Không gỡ bằng chứng pass của gate khác.** Chạy lại gate tất định trên vùng đổi; gate từng pass mà nay fail thì revert span (tổng quát hoá AA-528).
4. **Không làm cụt.** Câu cuối mọi field phải hoàn chỉnh. Fitter meta AA-740 bỏ kiểu "cắt rồi thêm dấu chấm", thay bằng sinh lại ngắn hơn hoặc cắt ở ranh giới câu. Đây là bản sửa đi cùng Q-2.
5. **Không làm nhạt.** Repair không được giảm độ phủ fact bắt buộc của nguồn (§7.4). Chặn kiểu "xoá chi tiết cho an toàn".

Vi phạm lúc chạy: revert span và ghi `degraded: repair_contract`.

### 4.4 Corpus Q0 (repo public → dữ liệu giả)

Mở rộng `tests/unit/aa791_t9_fault_set.py` thành `tests/quality/corpus/`, chạy trong job pytest unit hiện có.

| Nhóm | Số case | Nội dung |
|---|---|---|
| AA-791 có sẵn | 30 | Giữ nguyên, thêm nhãn truth |
| 9 kiểu lỗi lặp | ~9 | Một case cho mỗi kiểu ở §1.2 |
| Lớp `hard` | ~2 mỗi lớp (~16) | Một dương, một âm |
| Selector | bộ sinh | Bộ keep/drop tổng hợp + bộ sinh đối kháng (§4.5) |
| **Tổng** | **~55–60** + selector | Chỉ lớn thêm qua Q-FIX bước (c) |

- **Nhãn truth bắt buộc.** Mỗi case mang `expected: fire|no_fire|keep|drop`. Flip **về phía truth** miễn phí. Flip **xa truth** ở lớp `hard`/`block` là fail, không có mục YAML nào ghi đè được.
- **Snapshot + `expected_changes.yaml`** chỉ áp cho case chưa có nhãn. Có flip xa truth, hoặc YAML thêm > 5 dòng → cần một subagent reviewer độc lập (thay luật "> 10 verdict" cũ).
- **Cả chuỗi, đúng thứ tự sản xuất.** Mỗi case chạy hygiene → fixer → splice → dropper → `text_integrity.final_pass` → gate. Assert bất biến của văn bản cuối và quyết định held/approved cuối. Test thứ tự fail nếu có fixer chạy sau `final_pass`. Đây là chỗ bắt các lỗi tương tác đã ghi nhận: dropper S234 với hợp đồng FAQ F16, khôi phục CTA sinh CTA trùng, fitter AA-740 sinh câu cụt.
- **Không có cassette.** Q0 chỉ phủ gate tất định, oracle, selector và repair splice. Gate LLM thuộc Q2.
- **Byte pin** lấy từ WM-20 (release 0 byte-identical cho cả 4 writer), không làm lại.

### 4.5 Selector: loại artefact mới

Selector là mọi hàm quyết định writer thấy gì: lọc PAA theo phạm vi (`real_questions.py`: `paa_for_scope`, `place_variant_match`, `country_travel_question`, hiện ở nhánh `fix/real-questions-scope-variants`), seed builder, chọn segment, match keyword `search_demand`, `_estimate_day_count`.

- Mỗi selector có **bộ hai chiều có nhãn** (truth keep, truth drop), chấm bằng precision và recall, có sàn theo lớp.
- **Bộ sinh đối kháng, $0:** hàng xóm edit-distance của mỗi tên địa danh riêng; demonym hoặc tên nước ghép danh từ thường (beef, BBQ, hot pot, python, mastiff, gerbil, spot, "china"). Luật: PR sửa "bỏ nhầm" không được làm tăng số "giữ nhầm" trên bộ này, và ngược lại.
- Bộ ~150 câu PAA thật có nhãn (D10/AA-779) nằm private trên Dev, chạy ở R0 sau merge cùng cache ứng viên SERP/PAA. CI chỉ chạy bộ tổng hợp và bộ sinh.
- `real_questions.py`, seed builder và module `search_demand` vào `paths.yaml` với Q0 + R0.

### 4.6 Báo cáo, luật merge và giữ rẻ

**Báo cáo trên PR** chỉ chứa: tầng đã chạy, `run_id`, bảng theo `class_id` (new/fixed/Δ), chi phí, PASS/FAIL. Báo cáo đầy đủ nằm trong `shared.prompt_eval_runs` (WM-17 mở rộng), xem ở WM-22.

**Thi hành, không chỉ là quy ước** (bài học AA-779):

- Một bước trong job CI bắt buộc hiện có đọc `paths.yaml` và tính **hash của diff trên các path chất lượng**. Nếu PR chạm path Q2, bước này đòi commit status `quality/q2` có mô tả mang đúng hash đó.
- Status do workflow `quality-eval.yml` đăng. Workflow chạy `workflow_dispatch` **từ `main`** (cùng mẫu OIDC + ECS exec đã có ở `eval-regression.yml`), dùng `GITHUB_TOKEN` quyền `statuses: write`. Không cần secret mới, và code của PR không chạy với quyền AWS.
- **PASS mang sang SHA mới** khi hash diff trên path của tầng đó không đổi. Commit fixup ngoài path chất lượng không buộc chạy lại.
- Q3 không gắn với PR: train tháng. R0 sau merge không chặn merge, nó sinh PR revert.

| Kỹ thuật giữ rẻ | Tiết kiệm |
|---|---|
| Q3 gom theo train, không theo PR | Từ ~46 lần/tháng xuống 1 |
| Q2 chỉ khi judge/rubric/anchor/route đổi, chỉ tune split, theo label | Từ ~40 lần/tháng xuống ước ~10–20, mỗi lần rẻ hơn |
| PASS theo hash diff path chất lượng | Fixup không tốn thêm |
| Cache verdict, key `(text_sha, source_pack_sha, judge_prompt_sha gồm rubric+anchor, model_id + version thực, params)` | Chấm lại khi chỉ đổi gate tất định ~$0, và không trả verdict cũ khi nguồn hay pack đổi |
| Mẫu phân tầng ở Q3: tier `hard_cases` luôn chạy, phần còn lại ~50% | Giữ độ nhạy lớp `hard`, giảm ~40% chi phí |
| Oracle trên toàn bộ output đã lưu | Lớp `struct.*` kiểm ở $0 trên ~900 tour thay vì 8 mẫu golden |
| Stage cố định `eval_q2`, `eval_q3`, `eval_verify`, `eval_cal`; nối chi phí về run qua `llm_call_log.job_id` | Không sinh chuỗi `stage` mới cho mỗi run (index `idx_llm_call_log_stage_created`). Reader dashboard và `decision_log` loại `eval_%`, `adhoc_%`. |

---

## 5. Q-CAL — Hiệu chỉnh judge, gate và verifier

### 5.1 Dụng cụ cần đo

| Dụng cụ | Stage | Lớp chính | Nguồn đo |
|---|---|---|---|
| Brand-fit judge (A1/T2/T7) | `s1_judge`, `t2_judge`, debate | `scope.*` | AA-729 (S1 50, T2 7) |
| Brand audit A1 | `brand_audit` | `fact.inclusion` | AA-729 |
| Jev `a1_claim_supported` | `a1_grounding`, `t3_grounding` | `fact.*` | 424 claim của verifier; `decision_log.outcome` (AA-845) |
| F9 `cta_fact` / `brand_voice` | `t10_judge` | `fact.*` | AA-729 T9 25; `content_piece_label` (AA-783, chưa gán) |
| Gate tất định, oracle | — | Theo registry | `gate_ledger` + chip sản xuất ($0) |
| **Full-source verifier** | `eval_verify` (mới) | Mọi lớp `hard` | Bộ audit 30–40 claim do Nghiệp gán (§5.4) |

### 5.2 Chỉ số

| Chỉ số | Đo thế nào | Ngưỡng |
|---|---|---|
| **Precision** theo (detector × lớp) | **Từ tín hiệu sản xuất, $0**: `gate_ledger` cộng Dismiss / `style_only` / override của admin (WM-06). n hàng trăm. | Detector mới lên enforce khi precision ≥ 0.70 (cận dưới Wilson 95% ≥ 0.55). |
| **Recall** lớp `hard` | Golden (phân bố thật) + **mẫu cấy lỗi**: cấy lỗi theo kiểu lesson vào output sạch thật (private DB), ≥ 30 mẫu mỗi lớp. Với detector rule/oracle: $0. Với detector LLM: chỉ lớp `fact.*` hard, khi hiệu chỉnh. Gộp qua writer khi detector dùng chung. | Recall ≥ 0.80 trên mẫu cấy; golden dùng để kiểm phân bố thật. Mẫu dương đếm ở mức claim/instance. |
| **Bảng công suất** theo lớp | Với n hiện có: hồi quy nhỏ nhất phát hiện được | Lớp dưới công suất → "verifier xác minh, chỉ báo cáo" |
| κ judge so với nhãn | pass/fail mức mẫu | ≥ 0.6 mới tính vào stop (WM-19). Vào Done-when của AA-919. |
| Test–retest judge | 20 văn bản × 3 lần, **bỏ qua cache** (cờ rõ ràng) | Flip ≤ 10%. Chỉ chạy khi judge hoặc route đổi. |
| **Test–retest writer** | Ở train: viết lại control 2 lần trên tier `hard_cases` (S1 + T9), cache theo (`prompt_version`, `model`) | Dùng cho luật `hard` của Q3 (§4.2) |
| **Canary chống trôi** | Hằng tuần: 10 anchor đóng băng mỗi judge, chấm lại **không cache** | Flip > `noise_k` hoặc κ giảm → báo động + `reverify` |
| `noise_k` | Một số chung = 1 cho tới khi tier có ≥ 20 mẫu | — |

### 5.3 Ngưỡng chọn từ dữ liệu

- **Một file** `quality/thresholds.yaml`: mỗi ngưỡng kèm `calibration_run_id`, `precision`, `recall`, `n`.
- CI (repo public, không có DB) chỉ kiểm `calibration_run_id` có mặt và đúng định dạng. Lần chạy eval trên Dev kiểm nó tồn tại trong `prompt_eval_runs`.
- Điểm vận hành chọn trên tune, báo cáo trên holdout.
- Ngưỡng 7.0 giữ nguyên, đo lại trong lần hiệu chỉnh đầu. Nếu số liệu ủng hộ, đề xuất ngưỡng riêng A1/T2/T7.
- Kết quả hiệu chỉnh ghi vào `prompt_eval_runs` với `kind='calibration'` (cột do WM-17 thêm khi nới check `pipeline`).

### 5.4 Verifier cũng là dụng cụ đo

- Nghiệp gán một **bộ audit 30–40 claim** (một lần, ~40 phút). Đo precision, recall và κ của verifier trên bộ này.
- Verifier phải **khác họ model** với judge đang được kiểm, để lỗi không tương quan.
- Đo lại khi prompt hoặc model của verifier đổi.
- Verifier chạy trên ECS qua `LLMClient` (stage `eval_verify`), không còn chạy trong Claude Code. Nhờ đó Q3 chạy hết không cần người và chi phí được ghi.

### 5.5 Khi nào đo lại

- Judge prompt, rubric, anchor hoặc route model judge đổi → test–retest + precision/recall.
- Golden version hoặc taxonomy version đổi → precision/recall.
- Canary báo động → test–retest.
- **Không** đo lại định kỳ hàng tháng nếu không có gì đổi (canary làm việc đó rẻ hơn).

Trong lúc chờ đo lại (`reverify`), judge vẫn chạy nhưng chỉ có tác dụng thông tin.

### 5.6 Detector mới chạy shadow; gate cũ được giữ

- **Detector mới** có `mode: shadow`. Lên `enforce` khi đạt ngưỡng §5.2 và R0 cho thấy không đổi verdict ngoài lớp nó sở hữu. Lớp oracle thường đạt nhanh vì precision đo được trên toàn bộ output.
- **Gate đang chặn được giữ nguyên.** Chỉ gate có tỉ lệ bị gỡ cờ > ~30% (Dismiss / `style_only` / override) mới được đưa Nghiệp, **gộp thành một quyết định theo lô**, không duyệt từng gate.

---

## 6. Q-FIX — Quy trình sửa theo lớp

### 6.1 Trình tự bắt buộc

| Bước | Việc | Sản phẩm | Kiểm bởi |
|---|---|---|---|
| 0 | **Dump input thật** của 3 mẫu lỗi trước khi giả thuyết (lessons dòng 112). | Ghi chú trong implementation notes | Mục bắt buộc trong PR template |
| a | **Phân lớp.** Lớp đã có thì thêm ví dụ; lớp mới thì thêm vào `taxonomy.yaml`. | Diff taxonomy | Lint Q0 |
| b | **Thêm mẫu golden** (private) vào tune split, nếu lớp cần | `golden_candidate` | Bảng golden WM-17 |
| c | **Case có nhãn truth** trong corpus Q0 (hoặc vào bộ selector). Case phải **đỏ trên merge-base**. | Test đỏ | Bước CI: checkout merge-base, chạy các case mới của PR, đòi ít nhất một case fail ở đó |
| d | **Sửa.** Test chuyển xanh. Không lớp nào xấu đi. | PR | Q0 (+ Q2 nếu path judge) |
| e | **Done-when** theo chỉ số đứng: "`fact.inclusion` trên `gs-v1.2` T2: recall ≥ X, rate ≤ Y, không lớp `hard` nào có lỗi mới". | Linear | skill `aa-linear-issue` |

PR template của AA-CIS-App thêm mục **Quality class**: `class_id`, case Q0 đã thêm, `run_id` Q2 nếu có. CI kiểm rằng PR chạm path chất lượng thì phải sửa corpus/taxonomy **hoặc** khai `no-new-case: <lý do>`.

### 6.2 Bài học thành guard

Mỗi dòng trong `skill/aa-lessons/lessons.md` thuộc vùng writer/gate dần chuyển thành case Q0, lint registry, hoặc bộ đếm `degraded`. Chuyển xong thì xoá dòng.

### 6.3 Fail-open có bộ đếm (kiểu lỗi lặp số 6)

- Mỗi đường fail-open (Jev lỗi, judge vắng, segment best-effort, ghi log lỗi, `repair_contract` revert, **check ngày bị bỏ qua: `day_check_skipped`**) ghi tên vào `degraded[]` trên output.
- **Detector lớp `hard` bị degraded:** output bị giữ lại hoặc xếp hàng chạy lại (có backoff), **không bao giờ tính là pass**. Nếu cả wave bị (ví dụ Jev hết credit), wave dừng và báo, thay vì đi tiếp âm thầm.
- **Detector `warn`/`block` bị degraded:** áp ngưỡng 5% theo wave. Vượt thì job đánh dấu `degraded` và admin hiện banner đỏ.
- Trong eval: detector `hard` degraded → run INVALID.

### 6.4 Oracle ngày S1 và gate nguồn

- **Oracle ngày** (tất định, $0): tập ngày output = tập ngày nguồn; không trùng; đúng thứ tự; "Departure" chỉ ở ngày cuối; số ngày = duration khi nguồn nhất quán.
- Chạy trên **toàn bộ** output A1 đã lưu (~900 tour) ở R0, và trên mọi output viết lại ở Q3.
- **Gate nhất quán nguồn trước khi viết** (X1): nguồn tự mâu thuẫn ("14 days" mà 12 mục) được gắn `source.contradiction`, không tính lỗi cho writer.
- **Property test** cho đọc duration: "14 days/13 nights", "2 weeks", "half day", "Day 1–2", khoảng ngày.

---

## 7. Q-LEARN — Tự học cho writer **và** scorer

### 7.1 Sơ đồ luồng

```
signal (edit tenant/admin, chip, label panel, gate ledger, verifier)
   │  map → class_id (taxonomy)
   ├──► Writing Memory (đã duyệt): fact filter → mine → rule/ví dụ/preference
   │        └─► ứng viên release ─┐
   ├──► SQL $0 trong job KPI tuần (WM-30): FP rate + ứng viên FN   │
   │        └─► hàng chờ bất đồng WM-31 → ứng viên scorer ─────────┤
   └──► Golden candidates ──► panel + verifier ──► Nghiệp duyệt    │
                                                                   ▼
             ENGINE ĐÁNH GIÁ CHUNG (Q0 → Q2 → R0 sau merge → Q3 train ≡ WM R0/R2)
                                     │ PASS theo lớp
                                     ▼
                     1 click Nghiệp → active (pointer) → post-check WM-26
                                     │ hard/soft stop, control chart
                                     ▼
                     rollback (pointer flip, $0) hoặc PR revert (code)
```

### 7.2 Writer học (Writing Memory, giữ nguyên, chỉ nối thêm)

- Rule (WM-09) key theo `class_id`. Bộ mine (WM-12) gom cụm theo lớp.
- Release đi qua cổng chung: R0 = R0, R2 = Q3, cùng tiêu chí §4.2. Code và release bộ nhớ cùng đi train: Q3 code chạy trước (train mới so với train cũ), rồi R2 của release bộ nhớ chạy trên code đã qua.
- Thêm KPI vào WM-30: **first-pass rate** (trên bộ gate đóng băng theo taxonomy version) và **số vòng repair** theo writer × release.
- Corpus Q0 dùng làm test cho rule: rule mới không được làm đỏ case âm (`PREDICT` của WM-12 ở $0).
- Không fine-tune (D2) cho tới khi có ~1k cặp sạch mỗi writer.

### 7.3 Scorer học (gọn, bắt đầu ở $0)

Hai đầu ra SQL $0 thêm vào job KPI tuần WM-30:

1. **Tỉ lệ false positive theo gate × lớp**: Dismiss / `style_only` / override.
2. **Ứng viên false negative**: chip hoặc edit trúng lớp X khi không detector nào fire.

Cả hai vào hàng chờ bất đồng WM-31 (5–10 mục/tuần). Từ đó sinh ứng viên scorer: gỡ từ khỏi lexicon, hạ severity, thêm ngoại lệ có ví dụ, hoặc mục backlog detector. Ứng viên phải qua Q-CAL rồi R0, rồi một cú click.

**Hoãn:** bộ đào bằng LLM, làm mới anchor judge (chờ mỗi judge có ≥ 30 mục tune), optimiser kiểu GEPA (xét lại khi golden ≥ 300). Q-8 vẫn gộp vào AA-922, scope nhỏ hơn.

### 7.4 Chống gian lận chỉ số (Goodhart)

Rule WM và repair được chỉnh trên chính các judge và detector gác chúng. `repair_contract` bất biến 1 và việc giảm tỉ lệ lỗi fact đều thưởng cho văn bản nhạt: xoá chi tiết làm giảm mọi tỉ lệ `fact.*` và tăng first-pass rate. Nới gate cũng tăng first-pass rate. Vì vậy:

- **Chỉ số đối trọng không được giảm:** độ phủ fact nguồn (fact bắt buộc được giữ, số chi tiết cụ thể / 100 từ), độ dài so với mục tiêu, giọng văn.
- First-pass rate tính trên bộ gate **đóng băng** theo taxonomy version của release.
- **Judge sentinel** (khác họ model) chỉ chạy trên holdout ở train. Không bao giờ dùng để chọn, làm anchor hay học.
- KPI sự thật bên ngoài: **khoảng cách chỉnh sửa** của tenant/admin trên output.

### 7.5 Golden set: lớn lên có chừng mực

**Version.** `gs-v1` là ~100 mẫu AA-729 sau khi verifier chốt nhãn. Thêm lô thì tăng version phụ; đổi holdout thì tăng version chính.

**gs-v2 chỉ nuôi hai tier đang không chặn được release:**

| Tier | Hiện tại | gs-v2 |
|---|---|---|
| S1 | 50 | 50 (giữ) |
| T2 | 7 | **15** |
| T9 blog | 12 | 12 (giữ) |
| LinkedIn | 13 | 13 (giữ) |
| Facebook | 0 | **10** |
| Injection / isolation | ~10 | 10 |
| **Tổng** | ~92 | **~110** |

Không đặt mục tiêu gs-v3 trong v1. Thiếu mẫu dương cho recall được bù bằng **mẫu cấy lỗi** (§5.2), không bằng cách phình golden.

**Nguồn mẫu:** lỗi thật qua Q-FIX (b); chip/reject và edit "heavy" (WM-06, WM-32); bất đồng từ WM-31.

**Chất lượng nhãn:** panel + verifier (đã hiệu chỉnh, §5.4); lưu `label_source`, `verifier_claims`, `panel_agreement`; bất đồng panel–verifier đưa Nghiệp.

**Nguồn đổi:** lưu `source_sha256`. **Không có job hằng đêm**: kiểm SHA lúc chạy eval, mẫu có nguồn đổi bị bỏ qua và báo.

**Split và chống rò holdout.** 70/30 tune/holdout, phân tầng theo tier × lớp.

- Q2 trên PR chỉ báo **tune**.
- Holdout chỉ chạy ở train tháng (và khi tăng golden version).
- Ghi số lần truy cập holdout theo golden version. Đổi holdout (tăng version chính) sau 12 lần truy cập (~1 năm train).

**Lưu trữ.** Bảng golden WM-17 (private). Mẫu tenant bị xoá khi offboard (WM-33).

### 7.6 Tự động và cần duyệt

| Việc | Tự động | Cần Nghiệp |
|---|---|---|
| Capture signal, map lớp, mine, soạn ứng viên | ✔ | |
| Chạy Q0, Q2, R0, Q3 trong trần ngân sách | ✔ | Vượt trần |
| Thêm lớp `warn`/`block` và ví dụ | ✔ (báo trong PR) | |
| Thêm/đổi lớp `hard` | | ✔ |
| Detector mới `shadow` → `enforce` | | ✔ (1 click) |
| Gate cũ có tỉ lệ gỡ cờ > 30%: giữ hay hạ | | ✔ (một quyết định theo lô) |
| Kích hoạt release bộ nhớ (D6 a) | | ✔ (1 click) |
| Rollback release khi stop | ✔ (pointer flip, $0) | Báo sau |
| PR revert code khi R0 hoặc control chart báo hồi quy lớp `hard` | ✔ (agent mở và tự merge, giai đoạn dev) | Báo sau |
| Lô nhãn golden, bộ audit verifier | | ✔ |

### 7.7 Phát hiện hồi quy sau deploy (control chart)

Trong job KPI tuần (WM-30): `rate_per_100` theo lớp `hard` trên output Dev mới, so với trung bình 8 tuần trước + 3σ.

- Lớp oracle: kiểm trên **toàn bộ** output, $0.
- Lớp judgement: verifier chạy trên mẫu ≤ 20 mục/tuần, trong trần chung.
- Vượt ngưỡng → tìm PR/release gần nhất chạm path của lớp đó → PR revert hoặc rollback pointer.

---

## 8. Quan sát (không có trang mới)

Bỏ `/admin/quality` 6 tab (trùng WM-22 Releases, WM-17 bảng golden, WM-18 reverify, WM-30/31 Metrics, và `/admin/content-quality`). Thay bằng:

- **WM-31 tab Metrics** thêm 2 mục:
  - **Ma trận coverage taxonomy**: lớp × writer (C/P/F/M, suy ra từ registry), mode detector, số mẫu golden, lỗ hổng parity, bảng công suất.
  - **Calibration**: precision (từ sản xuất), recall (golden + cấy lỗi), κ, test–retest, canary, verifier.
- **WM-22 Releases** thêm loại ứng viên **"PR / train code"**: Q2 theo PR, Q3 theo train, R0 sau merge, bảng new/fixed theo lớp.
- Bộ đếm `degraded_rate`, first-pass rate, số vòng repair, chỉ số đối trọng nằm trong KPI tuần WM-30.

Tiết kiệm ~1 phiên và 1 issue Linear.

---

## 9. Lộ trình, issue và chi phí

### 9.1 Hai issue mới, phần còn lại gộp

| # | Issue | Map | Phase | Done when (rút gọn) |
|---|---|---|---|---|
| **Q-2** (làm trước) | `repair_contract` (5 bất biến) + sửa fitter AA-740 + `degraded[]` (gồm `day_check_skipped`, luật detector `hard`) + oracle ngày S1 + corpus Q0 ~55–60 case có nhãn truth, cả chuỗi, test thứ tự + bước CI red-on-merge-base + PR template | **Mới** | P0 | Bước Q0 chạy trong job pytest unit. Một PR thử làm flip xa truth bị chặn. Oracle ngày chạy trên ~900 tour A1 đã lưu, có số. Gây lỗi Jev giả thì output bị giữ và `degraded` tăng. |
| **Q-1** | Taxonomy gọn (~17 lớp, `other.*`) + `registry.py` + `thresholds.yaml` duy nhất + lint (nhiều–nhiều, selector) + `paths.yaml` + bước CI hash diff | **Mới**. Sửa README WM §8.2. | P0 | Lint xanh. 0 literal tên gate hay 7.0 ngoài registry. Mọi gate, chip, Jev key map lớp. |

**Gộp vào issue có sẵn (cập nhật scope khi cập nhật Linear):**

| Từ bản trước | Gộp vào | Phần thêm |
|---|---|---|
| Q-3 `quality_context` | **AA-916** | P0 chỉ stamp T9 (WM-08) và A1. T2 chờ WM-25 (`generation_meta` + denylist). Output chỉ mang `job_id`, `release_id`, `degraded[]`; phần còn lại ghi một lần ở `shared.job.result`. |
| Q-5 replay | **AA-918** | R0 sau merge là job worker; selector replay trên cache SERP/PAA; oracle trên toàn bộ output; gom flip `hard` judgement gửi verifier hằng tuần. |
| Q-6 hiệu chỉnh + R2 cho code | **AA-919** | Q2 theo PR và Q3 theo train; κ ≥ 0.6 trong Done-when; test–retest judge và writer; verifier trên ECS + bộ audit; canary; cấy lỗi; bảng công suất; cache key mới; workflow `quality-eval.yml` + status. |
| Q-8 scorer learning | **AA-922** | 2 đầu ra SQL $0, hàng chờ WM-31, control chart. |
| Selector, D10 | **AA-779** | Bộ keep/drop hai chiều + bộ sinh đối kháng, sửa một lần theo số. |
| Golden | **AA-729** | Như bản trước (score-only S1 có `grounding_node`, loại `eval_%`/`adhoc_%`, hook thay monkeypatch, gắn `class_id`), cộng gs-v2 T2 15 + Facebook 10. |
| Q-7 `/admin/quality` | **Bỏ** | Thay bằng 2 mục WM-31 + loại ứng viên WM-22 |

Liên quan: **AA-924** làm sau Q-1; replay Done-when của nó dùng R0. **AA-777**: test–retest F9 trong AA-919; flip > 10% thì đổi chiến lược thay vì thêm cache. **AA-915**: ADR 0009 nhắc Quality System.

### 9.2 Thứ tự ghép với Writing Memory

| Phase | Writing Memory (đã duyệt) | Quality System | Ghi chú |
|---|---|---|---|
| **P0** (S246–S247) | AA-915, AA-916 (+ stamp A1/T9) | **Q-2 trước**, rồi Q-1; AA-729 chốt | Toàn bộ $0, trừ phần còn lại của AA-729 (trần $15) |
| **P1** | AA-917, AA-918 (+ R0 sau merge), L0 lexicon | AA-779 theo Q-FIX | L0 vẫn ship trước golden (D11) |
| **P2** | AA-919 (+ Q2, Q3 train, hiệu chỉnh), AA-920 | — | Release 0 byte-identical (WM-20) |
| **P3** | AA-921, AA-922 (+ scorer SQL, control chart), AA-923, WM-25 (+ stamp T2) | — | Luật dừng của WM vẫn áp |

Q-2 và Q-1: khoảng **2 phiên** agent. Phần gộp vào AA-916/918/919/922 thêm khoảng 1 phiên rải trong các issue đó. Tổng thêm ~3 phiên, thay vì 4–5 ở bản trước, và hai thứ đem lại cải thiện sớm nhất (repair contract, bộ đếm degraded) nằm ở phiên đầu.

### 9.3 Chi phí hằng tháng trên Dev (tính lại)

Phải xác nhận bằng `llm_call_log` sau lần chạy đầu. **Trước khi chốt trần, đo lại đơn giá T2 sau AA-792** từ `llm_call_log` (số $0.38 dưới đây là trước AA-792). Không có dịch vụ AWS mới.

**Q3 theo tier, ở gs-v2 (chi phí viết lại, chưa gồm chấm):**

| Tier | n | Đơn giá | Viết lại toàn bộ | Phân tầng (`hard_cases` + 50% còn lại) |
|---|---|---|---|---|
| S1 | 50 | $0.06 | $3.00 | ~$1.9 |
| T2 | 15 | $0.38 (trước AA-792) | $5.70 | ~$3.8 |
| T9 blog | 12 | $0.10 | $1.20 | ~$0.8 |
| LinkedIn | 13 | ~$0.057 | $0.74 | ~$0.5 |
| Facebook | 10 | ~$0.057 | $0.57 | $0.57 (chạy hết) |
| **Cộng** | | | **$11.2** | **~$7.6** |

Cộng chấm (~$1), viết lại control lần 2 trên `hard_cases` S1+T9 (~$1–2), judge sentinel trên holdout (~$0.5) → **~$10–11 mỗi train**, tách thành các run theo tier, mỗi run ≤ $10.

**Tổng tháng:**

| Hạng mục | Đơn giá | Tần suất/tháng | $/tháng |
|---|---|---|---|
| Q0 CI | $0 | mọi PR (~454) | 0 |
| R0 sau merge (job worker) | $0 | sau mỗi deploy có path Q1 | 0 |
| Verifier cho flip `hard` từ R0 (gom tuần, ≤ 10/lớp) | ~$0.03/mục | 4 lô | 0.5–2 |
| Q2 score-only, tune split, theo label | $0.3–1 | ~10–20 (trong ~40 PR chạm path judge) | 3–20, thường ~8 |
| Q3 train | ~$10–11 | 1 | 9–13 |
| Q-CAL (test–retest bỏ cache, cấy lỗi LLM) | $1–3 | 0–2 (chỉ khi judge/route đổi) | 0–6, thường ~2 |
| Canary judge (10 mục × ~4 judge, không cache) | ~$0.4/tuần | 4 | ~1.7 |
| Control chart, verifier ≤ 20 mục/tuần | ~$0.5–0.9/tuần | 4 | 2–3.5 |
| **Tổng Quality System** | | | **~$17–48, thường ~$27** |
| Writing Memory (đã duyệt) | | | ~$2.5–20, thường ~$7 |
| **Cộng cả hai** | | | **thường ~$34**; trần chung chặn phần vượt |

### 9.4 Một trần chung, một bộ đếm

- **Một trần cho học + chất lượng:** đề xuất **$40/tháng**, **$10/lần chạy**, báo ở 80%.
- **Thi hành bằng `shared.spend_budget`** (AA-649, `shared/cost_guard.py`). Ràng buộc bảng hiện có: `scope` chỉ là `global` hoặc `job:%`, `provider` chỉ thuộc `dfs/bedrock/openai/jev/geocoder`, và bảng chỉ có `per_run_usd`/`per_day_usd`. Vì vậy:
  - mỗi job kind eval/learning (`job:quality_eval`, `job:writing_memory_mine`, …) có dòng theo provider với `per_run_usd = 10`;
  - trần **tháng** thêm vào `cost_guard.py` dưới dạng một hàm cộng `llm_call_log.cost_usd` theo các job kind trong tháng, như `_KIND_DAY_SPEND_SQL` đã làm cho ngày. Chỉ là code, không migration;
  - helper ngân sách $25 của WM-12 **dùng chính hàm này**, không viết helper riêng.
- **Thứ tự ưu tiên khi gần trần:** xác minh lỗi `hard` và Q3 train trước; Q2 theo PR sau; canary và control chart giãn tần suất.

---

## 10. Quyết định Nghiệp cần đưa ra

Chi tiết lựa chọn và đề xuất nằm trong `decisions.json` (10 mục). Tóm tắt:

| # | Câu hỏi | **Đề xuất** |
|---|---|---|
| D1 | Thi hành cổng thế nào? | Q0 trong job CI có sẵn; Q2 thi hành bằng status `quality/q2` theo hash diff, đăng bởi workflow từ `main` (không secret mới) |
| D2 | Q3 và replay chạy lúc nào? | Q3 gom theo train tháng; R0 sau merge; hoãn Q1 trước merge tới prod |
| D3 | Ngân sách | Một trần chung $40/tháng, $10/lần, qua `spend_budget` |
| D4 | Cỡ taxonomy v1 | ~17 lớp, phần còn lại `other.*` warn |
| D5 | Khi nào gate được block | Detector mới shadow; precision từ sản xuất; recall `hard` từ golden + cấy lỗi; gate cũ giữ, trừ gỡ cờ > 30% (một lô) |
| D6 | Nuôi golden | Chỉ T2 → 15, Facebook → 10; không job đêm; không gs-v3 |
| D7 | Hiệu chỉnh verifier | Nghiệp gán 30–40 claim một lần; verifier khác họ model; chạy trên ECS |
| D8 | Đo nhiễu và trôi | Nhiễu writer ở train trên `hard_cases`; canary tuần 10 mục/judge |
| D9 | Issue Linear | 2 mới (Q-1, Q-2), còn lại gộp; Q-7 bỏ; Q-2 làm trước |
| D10 | AA-779 | Dừng vòng chỉnh luật; bộ selector hai chiều + bộ sinh đối kháng; sửa một lần theo số |

Các quyết định bản trước không đổi và không cần hỏi lại: taxonomy ở repo app + ADR 0009 (D2 cũ), luật dung sai theo severity (D3 cũ, đã chỉnh theo truth và nhiễu writer), phân quyền tự động/duyệt (D6 cũ), KPI first-pass + số vòng repair (D11 cũ, thêm chỉ số đối trọng), làm trong P0 cùng WM (D12 cũ).

---

## 11. Rủi ro và giới hạn

### 11.1 Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Corpus tổng hợp lệch khỏi lỗi thật | Mỗi case từ một lỗi thật qua Q-FIX (c). R0 và oracle chạy trên toàn bộ output thật. |
| Golden nhỏ nên tiêu chí theo lớp vẫn nhiễu | Bảng công suất; lớp dưới công suất chỉ báo cáo; recall đo trên mẫu cấy lỗi; lớp `hard` xác minh từng lỗi mới. |
| Train tháng phát hiện muộn lỗi writer | Dev không có người dùng; R0 + oracle + control chart tuần bắt phần tất định ngay; revert theo PR khi train fail. |
| Agent tự duyệt hồi quy của mình | Nhãn truth không ghi đè được; YAML > 5 dòng hoặc flip xa truth cần reviewer độc lập; status CI theo hash. |
| Taxonomy phình to | Luật chọn lớp (≥ 5 dương hoặc `hard`); lớp mới phải nêu ranh giới; thêm lớp `hard` cần duyệt. |
| Eval làm bẩn số sản xuất | Stage `eval_*` cố định; reader loại `eval_%`/`adhoc_%`. |
| Tối ưu làm văn nhạt | Chỉ số đối trọng, judge sentinel, khoảng cách chỉnh sửa (§7.4). |
| Giữ output khi detector `hard` degraded làm nghẽn wave | Xếp hàng chạy lại có backoff; wave dừng và báo thay vì đi tiếp. Đây là chủ đích: thà dừng còn hơn 48k lần im lặng. |
| Phụ thuộc nhãn AA-729/AA-783 | Q-2 và Q-1 không cần nhãn. Hiệu chỉnh T9 chờ AA-783. |
| `run_write_background` quá lớn | `repair_contract` chỉ gắn ở điểm splice có sẵn. Tách hàm là việc riêng. |

### 11.2 Điều kiện khi làm lại Q1 trước merge (lúc có prod)

- Chỉ branch cùng repo, không bao giờ fork.
- Role DB riêng chỉ đọc trên các view replay, cộng một role ghi hẹp chỉ cho bảng eval.
- Không secret nào khác. Ước lượng công việc role/view trước khi làm.

---

### Phụ lục A: Map path → tầng (`quality/paths.yaml`, bản nháp)

| Path | Q0 | Q2 (trước merge) | R0 (sau merge) | Q3 train (tier) |
|---|---|---|---|---|
| `content_generation/prompts.py`, `batch_prompt.py` | ✔ | | | A1 (+T2 nếu `T2_SYSTEM_PROMPT` đổi) |
| `content_generation/graph.py`, `validate`, `forbidden_strip`, `seo_meta_utils` | ✔ | | ✔ (+ oracle ngày) | A1+T2 nếu đụng node writer hoặc repair |
| `judge_node.py`, `brand_fit.py`, `brand_audit_node.py` | ✔ | ✔ (A1, T2, T7) | | |
| `grounding.py`, `acp_shared/grounding.py` | ✔ | ✔ nếu đổi câu hỏi/route | ✔ | |
| `flag_fix_node.py`, `sentence_repair.py`, `t2_repair.py` | ✔ | | ✔ | repair replay |
| `acp_content_writing/prompts.py`, `channel_spec.py`, `generate.py` | ✔ | | | T9 kênh bị ảnh hưởng |
| `quality_gates.py`, `hygiene.py`, `trip_facts.py`, `text_integrity.py`, `authenticity.py` | ✔ | (✔ nếu F9) | ✔ | |
| `service.py::run_write_background` | ✔ | | ✔ | repair replay T9 |
| `signature_vocabulary.py`, `forbidden_words` | ✔ | | ✔ | A1+T2+T9 mẫu nhỏ |
| **Selector:** `real_questions.py`, seed builder, `search_demand`, `_estimate_day_count` | ✔ (bộ hai chiều + bộ sinh) | | ✔ (cache SERP/PAA, bộ ~150 câu thật) | |
| `shared/llm_client/decide.py`, migration `decision_question` | ✔ | ✔ | | |
| Route `llm_role_config` hoặc env flag (ngoài PR) | — | ✔ (judge) qua `reverify` | | ✔ (writer) qua `reverify` |

---

## 12. Phản biện đã xử lý

Hai vòng phản biện, 32 ý. **Nhận** = áp nguyên ý; **Nhận, chỉnh** = áp nhưng sửa một chi tiết (lý do kèm theo); **Bác** = không áp (lý do một dòng).

**Vòng 1 — chi phí và độ gọn (15 ý)**

| # | Ý | Xử lý |
|---|---|---|
| 1 | Chi phí giả định nhịp PR thấp ~10 lần | **Nhận.** Đã kiểm lại trên `origin/main` (~39–46 PR/tháng chạm path judge/writer). Q2 chỉ khi judge đổi; Q3 gom theo train; `run_id` theo hash diff path chất lượng; §9.3 tính lại. |
| 2 | Trần riêng trùng guard có sẵn; stage `eval_<run_id>` | **Nhận, chỉnh.** Dùng `spend_budget`, nhưng scope phải là `job:<kind>` (CHECK constraint chỉ cho `global` hoặc `job:%`), và trần tháng là hàm mới trong `cost_guard.py` vì bảng chỉ có per_run/per_day. Trần chung $40 thay vì $35 vì số tính lại thường ~$34. |
| 3 | Q3 chưa tính golden lớn lên | **Nhận.** Bảng giá theo tier; T2 gs-v2 = 15; mẫu phân tầng; đo lại đơn giá T2 sau AA-792 trước khi chốt trần. |
| 4 | Giá Q-CAL sai; `noise_k` chưa đo được | **Nhận.** $1–3 với cờ bỏ cache; chỉ khi judge/route đổi; `noise_k=1` tới khi tier ≥ 20. |
| 5 | `/admin/quality` trùng trang WM | **Nhận.** Bỏ Q-7; thêm 2 mục WM-31 và loại ứng viên WM-22. |
| 6 | Không cần 3 bảng mới | **Nhận.** Đọc YAML trong image; calibration vào `prompt_eval_runs` (cần cột/check do WM-17 nới); sự kiện route vào `acp_shared.audit_log`. |
| 7 | Taxonomy quá chi tiết | **Nhận, chỉnh.** ~12 lớp writer + 3 safety, cộng 2 lớp phụ trợ (`scope.faq_question_offtopic` theo ý vòng 2 số 1, `source.contradiction` để không tính lỗi nguồn cho writer). Bỏ các trường trùng/suy ra được. |
| 8 | Luật block D4 không đạt được | **Nhận.** Precision từ tín hiệu sản xuất; golden chỉ cho recall `hard` (cộng cấy lỗi, vòng 2 số 5); shadow chỉ cho detector mới; gate cũ > 30% gỡ cờ thành một lô. |
| 9 | Q1 branch image quá nặng | **Nhận, chỉnh.** Hoãn và dùng R0 sau merge. Chỉnh một dữ kiện: trust GitHub→AWS qua OIDC đã có sẵn (`eval-regression.yml`), nên rủi ro mới nằm ở việc chạy code chưa merge với quyền DB, không ở trust. |
| 10 | Q0 quá lớn, cassette sẽ gãy liên tục | **Nhận.** ~55–60 case, không cassette, byte pin từ WM-20, chạy trong job pytest unit. |
| 11 | `quality_context` phá phasing WM | **Nhận.** P0 chỉ T9 + A1; T2 chờ WM-25; output mang 3 trường, phần còn lại ở `shared.job.result`. |
| 12 | Ngưỡng ở hai file; CI không kiểm được DB | **Nhận.** Một file `thresholds.yaml`; CI kiểm định dạng, Dev kiểm tồn tại. |
| 13 | Scorer learning bắt đầu được ở $0 | **Nhận.** 2 đầu ra SQL trong WM-30, vào WM-31; hoãn miner LLM và anchor refresh. |
| 14 | Nuôi golden tốn thời gian Nghiệp | **Nhận.** Chỉ T2 và Facebook; bỏ job đêm; bỏ gs-v3. |
| 15 | Tổng công quá lớn | **Nhận.** 2 issue mới, ~2 phiên, Q-2 làm trước. Ghi chú: ý vòng 2 (oracle ngày, selector, verifier) thêm ~1 phiên rải trong các issue gộp. |

**Vòng 2 — độ chặt (17 ý)**

| # | Ý | Xử lý |
|---|---|---|
| 1 | Cổng bỏ sót hồi quy ở selector (AA-779) | **Nhận.** Loại artefact `selector`, bộ hai chiều, bộ sinh đối kháng, `paths.yaml`, lớp `scope.faq_question_offtopic` trong qtax-v1. Replay chạy ở R0 sau merge vì Q1 trước merge đã hoãn. |
| 2 | Snapshot ghi hành vi hiện tại, tác giả tự duyệt hồi quy | **Nhận.** Nhãn truth; flip xa truth không ghi đè được; YAML > 5 dòng cần reviewer độc lập. |
| 3 | Đếm flip không có chiều | **Nhận, chỉnh.** Lớp oracle biết chiều ở $0. Chỉ flip `hard` loại judgement mới gửi verifier, gom theo tuần để giữ trong trần. |
| 4 | Lỗi ngày S1 phần lớn không được kiểm, check tự tắt | **Nhận.** Đã đối chiếu `graph.py` ~L870–890. Chia oracle/judgement; oracle ngày trên ~900 tour; `day_check_skipped`; gate X1; property test duration. |
| 5 | Luật enforce không đạt được với golden đã định | **Nhận, chỉnh.** Cấy lỗi ≥ 30/lớp, đếm mức claim, gộp writer, bảng công suất. Với detector LLM chỉ cấy cho lớp `fact.*` hard để giữ chi phí. |
| 6 | Không đo nhiễu writer | **Nhận, chỉnh.** Đo ở train (không phải mỗi lần hiệu chỉnh), chỉ `hard_cases` S1 + T9, cache theo (`prompt_version`, `model`). T2 dùng luật mẫu nhỏ. |
| 7 | Verifier chưa được hiệu chỉnh | **Nhận.** Bộ audit 30–40 claim (đưa thành quyết định D7 vì tốn thời gian Nghiệp), khác họ model, chạy trên ECS stage `eval_verify`. |
| 8 | Cache che trôi judge | **Nhận, chỉnh.** Cache key mới. Canary 10 mục/judge mỗi tuần thay vì 20, để giữ trong trần. |
| 9 | Gian lận chỉ số | **Nhận.** Chỉ số đối trọng, first-pass trên bộ gate đóng băng, judge sentinel holdout-only, khoảng cách chỉnh sửa. Thêm bất biến 5 "không làm nhạt" vào `repair_contract`. |
| 10 | Holdout rò qua nhìn lặp | **Nhận, chỉnh.** PR chỉ báo tune; holdout ở train. Đổi holdout sau 12 lần truy cập thay vì K nhỏ hơn, vì golden nhỏ và đổi holdout tốn nhãn. |
| 11 | Luật merge chỉ là quy ước; PASS theo SHA nổ chi phí | **Nhận, chỉnh.** Status `quality/q2` + bước CI theo hash diff; label `ready-for-quality`. Status do workflow chạy từ `main` đăng bằng `GITHUB_TOKEN`, không phải runner trên Dev, để không phải đưa token GitHub vào Dev. Không có `quality/q1`/`q3` vì Q1 hoãn và Q3 chạy theo train. |
| 12 | Q0 kiểm từng gate, hồi quy đến từ tương tác chuỗi | **Nhận.** Cả chuỗi theo thứ tự sản xuất, assert văn bản cuối và held/approved, test thứ tự. |
| 13 | Bỏ qua engine eval có sẵn | **Nhận.** Mở rộng `services/eval/regression.py`; gộp hoặc bỏ fixture xlsx khi golden chốt; một người ghi `prompt_eval_runs`. |
| 14 | Chạy branch image từ repo public | **Nhận.** Ghi vào §11.2 làm điều kiện khi làm lại Q1 trước merge; hiện tại không áp dụng vì đã hoãn. |
| 15 | Ngưỡng fail-open 5% quá lỏng cho lớp `hard` | **Nhận.** Detector `hard` degraded → giữ/xếp hàng lại, không tính pass; 5% chỉ cho warn/block; eval INVALID. |
| 16 | Lint ép 1 detector 1 lớp | **Nhận.** Nhiều–nhiều; mỗi violation mang `class_id`; đo theo (detector, lớp). |
| 17 | Hai cơ chế chưa được định nghĩa | **Nhận.** (a) Bước CI checkout merge-base, đòi ≥ 1 case mới fail. (b) Control chart tuần: trung bình 8 tuần + 3σ, oracle trên toàn bộ, judgement qua verifier ≤ 20 mục/tuần. |

**Ý bị bác hoàn toàn:** không có. Các chỗ **Nhận, chỉnh** ở trên là nơi ý đúng về hướng nhưng một chi tiết vướng ràng buộc có thật (CHECK constraint của `spend_budget`, trust OIDC đã có, trần ngân sách) hoặc mâu thuẫn với ý của vòng kia (vòng 1 đòi cắt, vòng 2 đòi thêm). Khi mâu thuẫn, cách chọn là: giữ cơ chế, giảm tần suất hoặc phạm vi.

## 13. Các loop writer–judge hiện có (S1/A1, T2/T3, T9/T10) trong Quality System

**Hai tầng loop.**
- **Loop trong:** chạy cho từng bài: viết → kiểm → judge → sửa → thử lại. Loop này giữ nguyên.
- **Loop ngoài (Quality System):** chạy cho từng thay đổi và từng release. Nó đo, hiệu chỉnh và cho chính các loop trong học dần.

Loop trong lo cho một bài không lỗi. Loop ngoài lo cho cả loop trong không sai lặp lại.

| Loop hiện có | Cách chạy hôm nay | Vấn đề hệ thống (bản đồ code §5 phần nghiên cứu) | Quality System làm gì |
|---|---|---|---|
| **S1/A1** `graph.py` | generate → validate (điểm luật từ 10) → judge `brand_fit` → retry ≤3, mốc 7.0 → brand_audit → grounding → flag_fix → revalidate | Mốc 7.0 chép ở 5 chỗ. `brand_fit` dùng chung cho A1, T2 và T7 Debate (cache không mang version rubric). `_HARD_BLOCK_CODES` dùng chung cho 3 nơi gọi. Lesson ghi `stage='audit'` nhưng chỉ đọc `S1_*`, nên **không bao giờ vào prompt**. `few_shots` luôn `[]`. Golden 1.1.0: S1 trượt 44/50. | Một nguồn ngưỡng (`thresholds.py`) và registry gate. Mã validate được gắn lớp lỗi (`struct.day_count`, `fact.invented`…). Kiểm số ngày thành oracle tất định, chạy lại trên khoảng 900 tour A1 đã lưu. Judge `brand_fit` được hiệu chỉnh precision/recall trên golden; cache Debate mang version rubric. Lesson/ví dụ đi qua Writing Memory thay cho đường `pipeline_lessons` đang hở. |
| **T2 + T3** (`t2_drafts`, `run_t3_qa_gate`) | Chạy lại graph A1 với `is_tenant_rewrite`, best-draft; T3 sửa tối đa 2 lần | Mọi thay đổi node trong `graph.py` đều chạm T2. Byte pin prompt A1 không bao phủ T2. Cờ env `T2_*`/`T3_*` không ghi lên output. | Ghim byte prompt T2 trong Q0. Cờ env, route và prompt version ghi vào `shared.job.result` (truy qua `job_id`). Mọi thay đổi `graph.py` chạy case Q0 của cả A1 lẫn T2. |
| **T9/T10** `run_write_background` | Một hàm khoảng 620 dòng: viết → fix tất định → 23–25 gate → sửa câu, viết lại, cắt truth, chặn hồi quy AA-528, F9 sticky → `_final_integrity`; tối đa 3 lần | Tập severity (`STYLE_ONLY_GATES`, `CHEAP_REPAIR_GATES`…) quyết định đường sửa ở xa chỗ sửa code. Fixer và gate dùng chung helper (vòng import). Tên gate là chuỗi rải ở khoảng 8 chỗ. Bài không mang prompt hay code version. **Tenant sửa bài T9 thì bản gốc bị ghi đè.** | Repair contract: một lần sửa không được làm hỏng gate đã đạt (tổng quát hoá AA-528 cho mọi loop, test ở Q0). Registry gate + lint. Gate hiệu chỉnh trên golden trước khi được chặn. Giữ bản trước/sau khi tenant sửa (nguồn học tốt nhất). Tách `run_write_background` thành các bước có tên là việc riêng, làm sau khi Q0 phủ đủ để tách an toàn. |
| **Jev** (`decide()`) | Mỗi câu hỏi có mode off/shadow/enforce; fail open | Fail open nên số lần gọi không chứng minh Jev đã chạy. Dòng eval `adhoc_aa729` có thể lọt vào dashboard. | Bộ đếm `degraded` cho mọi đường fail-open. Dashboard lọc `adhoc_%`. Nhãn `decision_log.outcome` dùng để hiệu chỉnh. |

**Ba "loop học" đang hở, phải nối trước khi nói tới tự học:**
1. Lesson tự động không vào prompt (lệch stage).
2. Tenant sửa bài T9 thì mất bản gốc.
3. Output không mang version, nên không biết thay đổi nào gây ra lỗi.

Writing Memory (AA-915/916) và Q-3 nối mục 3. Mục 1 và 2 cần nối trong P0 (quyết định D11).
