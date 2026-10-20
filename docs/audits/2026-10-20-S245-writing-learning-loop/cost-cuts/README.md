# Writing Memory v1: cắt chi phí hằng tháng, giữ nguyên độ an toàn và giá trị học

Phiên S245 (vòng 2), 20/10/2026. Tác nhân: Claude Code (subagent). Chỉ đọc: không truy vấn DB, không gọi LLM, không
sửa repo. Chi phí $0.

Đầu vào đã đọc đầy đủ: `.tmp-session/s245-r2/owner-input.md`;
`docs/audits/2026-10-20-S245-writing-learning-loop/README.md` (§0, §5, §8, §9, §10, §13) và `research/01-current-state.md`,
`02-state-of-the-art.md`, `03-measurement-design.md`, phần `monthly_cost` / `safety` / `phases` của option A trong
`research/options.json`; memo `docs/audits/2026-10-20-S245-m2a-decisions/README.md` §1 (giá đơn vị AA-729).

Code: AA-CIS-App `origin/main` **b7e6da66**. Riêng `shared/llm_client/` giống hệt checkout local `f9fc32d6`
(đã kiểm bằng `git diff`), nên số dòng ở thư mục đó đúng cho cả hai. Trạng thái route live lấy từ
`docs/audits/2026-10-14-S235-ecosystem-team-pilot/ai-governance-audit/ai_audit.json` (snapshot 14/10/2026, mục `routes`).
Từ đó tới nay không migration nào đổi các route writer.

Giá: link nguồn kèm ngày truy cập 20/10/2026. Số nào không có trang giá chính thức thì ghi "ước tính".

---

## 0. Tóm tắt

1. **Con số +17–21% mỗi bài S1 là tính sai giá.** README §10 tính 1,5k token × giá Sonnet ($3/1M). Nhưng writer S1 và
   flag_fix là **Haiku 4.5 ($1/1M)**: `s1_generate` và `s1_flag_fix` = `haiku` trong route live. Tính lại thì
   2 × 1.500 × $1/1M = **$0,003/tour, tức +5–6%**. Với bộ cắt đề xuất còn khoảng **+$0,0005/tour (~1%)**.
2. **Chi phí Dev hằng tháng: ~$39 (giữa khoảng $30–50) → ~$4–18, thường ~$8–10.** Hai đòn bẩy lớn nhất:
   - **Gộp release thành một đợt mỗi tháng.** Đường nhanh L0 (từ vựng, $0) vẫn chạy bất kỳ lúc nào.
   - **Shadow 20 input có chủ đích** thay cho 50 input, và chỉ chạy cho release có luật viết, ví dụ hoặc tóm tắt sở thích.
3. **Prompt caching giúp rất ít ở quy mô Dev.**
   - Haiku 4.5 chỉ cache khi tiền tố ≥ 4.096 token. System prompt A1 chỉ ~1,4k token, nên S1 không bao giờ cache.
   - System của T9 (~1,3k token, Sonnet 4.6, ngưỡng 1.024) đã được đánh dấu cache sẵn. Chỉ cần **đặt** HOUSE RULES vào đó,
     không phải viết code mới.
4. **Bedrock Batch (giảm 50%) không dùng được cho vòng học bây giờ:**
   - mỗi job cần tối thiểu 100 bản ghi, trong khi R2 và shadow đều ≤ 50;
   - batch không có prompt caching;
   - hai model judge Luna không có trong danh sách hỗ trợ batch;
   - chỉ lượt viết đầu batch được, vòng judge và sửa vẫn chạy on-demand.
5. **Quy trình an toàn giữ nguyên:** replay $0 → golden → shadow → một cú bấm duyệt, kèm kiểm tra sau khi bật trên mọi bài
   mới. Chỗ đổi: ít lượt release hơn và shadow có chủ đích hơn. Rủi ro còn lại được tính bằng số ở §3.
6. **Câu trả lời D cần chỉnh:**
   - **D8**: trần $60 → **$25/tháng**, R2 $15 → **$10/lượt release**.
   - D10, D12, D14, D15 giữ "có", chỉ chỉnh chi tiết (§6).
   - Thêm 4 câu chốt mới E1–E4 (§7).

---

## 1. Tính lại điểm xuất phát

### 1.1 Ai viết bằng model nào (route live 14/10/2026)

| Stage | Model | Giá vào/ra (1M token) | Đường gọi | Nguồn |
|---|---|---|---|---|
| `s1_generate` (A1) | `haiku` = Claude Haiku 4.5 | $1 / $5 | legacy chain → satellite `invoke_claude` | ai_audit.json `routes[8]`; `pricing.py:37-39` |
| `s1_flag_fix`, `t2_flag_fix` | `haiku` | $1 / $5 | như trên | ai_audit.json `routes[7]`, `[15]` |
| `t2_generate` | `sonnet` = Sonnet 4.6 trên satellite | $3 / $15 | như trên | `routes[16]`; `bedrock_satellite.py:138` |
| `t9_write` | `sonnet` | $3 / $15 | như trên | `routes[22]` |
| `t9_repair` | `haiku` → `sonnet` | $1 / $5 | như trên | `routes[21]` |
| judge (`s1_judge`, `t10_judge`, `t2_judge`…) | `gpt-5.6-luna` → `gpt-6-luna` → `gpt-6-luna-openai` | $0,20/$1,20 và $0,10/$0,50 (**ước tính**: giá list OpenAI, Bedrock chưa công bố) | Converse | `api/migrations/170_llm_stage_routes_and_prices.sql` (UPDATE gpt-5.6-luna; INSERT gpt-6-luna); `224_openai_last_resort_only.sql` |

Giá Claude lấy từ catalog repo (`api/migrations/169_llm_model_catalog.sql`, hàng `haiku` $1/$5 và `sonnet` $3/$15) và
khớp giá list Anthropic: Haiku 4.5 $1/$5, Sonnet 4.6 $3/$15 (bảng model của skill claude-api, cache 06/10/2026).
Trang <https://aws.amazon.com/bedrock/pricing/> (truy cập 20/10/2026) không hiện được bảng giá Anthropic khi tải về,
nên **giá Bedrock của từng model Claude coi là ước tính bằng giá list**. Hệ số cache: ghi 1,25×, đọc 0,1× giá vào
(`shared/llm_client/pricing.py:47-48`).

### 1.2 Phụ phí mỗi bài: README so với tính lại

README §10 giả định mỗi lời gọi có chèn bộ nhớ thêm ≈ 1,5k token (≤ 20 dòng luật + 3 ví dụ), giá **$3/1M**.

| Loại bài | Giá gốc / bài | README | Tính lại đúng giá model, giữ thiết kế cũ |
|---|---|---|---|
| S1 tour (Haiku) | $0,048–0,06 | 2 lời gọi × $0,0045 ≈ +$0,01 = **+17–21%** | 2 × 1.500 × $1/1M = **$0,003 = +5,0–6,3%** |
| T9 blog (Sonnet) | $0,094–0,104 | 1–3 lời gọi → +$0,005–0,02 = +5–21% | đúng (Sonnet $3/1M), nhưng lượt sửa câu `t9_repair` là Haiku → trần thật ≈ 2 × $0,0045 + $0,0015 = $0,0105 (≈ +10–11%) |
| T9 LinkedIn (Sonnet) | ~$0,057 | không tính | 1–2 lượt × $0,0045 + sửa $0,0015 = $0,006–0,0105 = **+11–18%** |
| T2 tour (Sonnet + Haiku fix) | $0,38 (số cũ, trước AA-792) | không tính | $0,0045 + $0,0015 = $0,006 ≈ +1,6% |

Kết luận: phụ phí S1 thấp hơn 3 lần so với README. Chỗ thật sự sát ngưỡng dừng mềm +20% là **T9 LinkedIn**, vì bài ngắn
mà giá đơn vị rẻ.

### 1.3 Hai câu trong README §10 cần sửa

- **"Caching: tra được, vì `LLMClient` ghi `cache_read_tokens` / `cache_write_tokens` … → truy `shared.llm_call_log`" là
  sai.** Bảng `shared.llm_call_log` **không có** cột cache (`docs/architecture/db-schema-reference.md:2708-2727`), và
  `shared/llm_client/call_log.py` không ghi trường cache nào. Số cache chỉ nằm ở:
  - `generated_content.metadata.cache_read_tokens` / `cache_write_tokens`, chỉ cho S1
    (`api/routers/admin_pipeline.py:269, 284-285`);
  - dòng log CloudWatch `llm_success` (`shared/llm_client/client.py:423-426, 477-480, 605-608`).

  `cost_usd` trong `llm_call_log` thì **đã** tính giá cache (`pricing.py:112-113`), nên tổng tiền vẫn đúng.
- **"Tính lại … ≈ +17–21% cho S1"** (§5.3 và §10) dùng nhầm giá Sonnet (xem §1.2).

### 1.4 Ngân sách Dev hằng tháng theo README, làm cơ sở so sánh

README §10 không cộng ra từng dòng, nên dưới đây là kịch bản "giữa" để so sánh. Tổng $39 nằm trong khoảng $30–50 README đã nêu.

| Dòng | Giả định (từ README §10) | Kịch bản giữa |
|---|---|---|
| Mine luật | hằng tuần (4,3 lượt) × $0,3–1 | **$3** |
| R2 golden | 2–3 release × $3–10 (chỉ tầng bị ảnh hưởng) | 2,5 × $6,5 = **$16,25** |
| Shadow | ≤ 50 input × $0,05–0,10 = $5–10 / release | 2,5 × $7,5 = **$18,75** |
| R0, R1, embedding | $0–2 | **$1** |
| **Tổng** | | **$39** |

Giá đơn vị một mẫu golden, dùng cho mọi phép tính sau (memo M2a §1):

| Tầng | Giá / mẫu | Số mẫu | Tiền cả tầng |
|---|---|---|---|
| S1 | $0,06 | 50 | $3,0 |
| T2 (số cũ, trước AA-792) | $0,38 | 10 | $3,8 |
| blog | $0,10 | 15 | $1,5 |
| LinkedIn | $0,057 | 15 | $0,86 |

---

## 2. Danh sách tối ưu, xếp theo số tiền tiết kiệm

Số "tiết kiệm" tính **riêng từng mục** so với kịch bản giữa $39. Khi gộp, các mục chồng lên nhau, nên tổng gộp nằm ở §4,
không phải tổng cộng dồn của bảng này. "Công" tính theo phiên agent.

### #1. Release theo đợt hằng tháng (release train), L0 vẫn chạy bất kỳ lúc nào

- **Đổi gì:**
  - Luật `writer_instruction`, `repair_hint`, ví dụ và tóm tắt sở thích gom vào **một release mỗi tháng** cho mỗi người viết.
  - Luật `lexicon` vẫn đi đường nhanh L0 (R0 $0 + cú bấm) bất kỳ lúc nào.
  - Rút lại là lật con trỏ, $0, không chờ đợt.
  - Chỉ có release "khẩn" khi cần sửa gấp một dừng cứng.
- **Tiết kiệm:**
  - R2: (2,5 − 1) × $6,5 = $9,75.
  - Shadow: (2,5 − 1) × $7,5 = $11,25.
  - **Cộng ≈ −$21/tháng (39 → 18).** Mỗi bài: $0.
- **An toàn / giá trị học:**
  - Mọi cổng giữ nguyên.
  - Thiệt: luật viết chờ tối đa ~30 ngày mới chạm bài.
  - Bù lại: L0, phần chị Thư nhìn thấy rõ nhất ("không còn viết X"), vẫn đi ngay. Dữ liệu Dev cũng ít (4 tenant thử, ~48
    bản T2, ~251 bài T9; README §11), nên mỗi tuần hiếm khi có cụm đủ ngưỡng (luật tenant cần ≥ 2 lần sửa trên ≥ 2 bài).
  - Gộp nhiều luật vào một release làm khó quy công cho từng luật. Khắc phục: R0 replay từng luật riêng ($0). Chỉ khi
    release trượt mới chạy loại-bỏ-từng-luật, và chỉ trên tầng bị trượt.
- **Công:** ~0 (chính sách + lịch job; nút "đóng đợt" trên tab Releases).
- **Bằng chứng:** README §10 ghi "2–3 release/tháng"; ngân sách R2 và shadow tính theo release (README §10;
  options.json A `safety[4]`).

### #2. Shadow: 20 input có chủ đích, chỉ cho loại release cần

- **Đổi gì:**
  - Shadow replay chạy trên **20** input thật gần nhất (không phải 50) của người viết bị ảnh hưởng. Ưu tiên input mà gate
    hoặc cụm mục tiêu từng bắn, và loại input đã có trong golden set.
  - **Bỏ shadow** cho release chỉ có `lexicon` (đã bỏ sẵn ở README §5.4) và release chỉ có `repair_hint`. `repair_hint` chỉ
    chèn khi gate bắn, nên R2 đã đo đủ.
  - Release tenant: shadow chỉ trên input của chính tenant đó.
- **Tiết kiệm:**
  - Mỗi release-người viết: 50 × $0,05–0,10 = $2,5–5 → 20 × $0,05–0,10 = **$1–2**.
  - Kịch bản giữa ($7,5/release ≈ 1,5 người viết): còn ~$2,25.
  - Riêng mục này, giữ 2,5 release: 18,75 → 5,6 = **−$13/tháng**. Gộp với #1: 7,5 → 2,25 = −$5,25 thêm.
- **An toàn (tính ra số):**
  - Shadow là lớp kiểm **trước khi bật** cho dừng cứng 2 (rò tenant) và 3 (dấu vết QA). Hai dừng này đều tất định.
  - Với tỉ lệ vi phạm p trên mỗi bài, xác suất bắt được ≥ 1 ca = 1 − (1 − p)^n:
    - p = 5%: n = 50 → 92%; n = 20 → 64%.
    - p = 10%: n = 50 → 99,5%; n = 20 → 88%.
    - p = 15%: n = 20 → 96%.
  - Có giảm, nhưng còn hai lớp khác:
    - **R2 golden** đã có isolation probe và grep dấu vết QA;
    - README §8.2 đã có **kiểm sau khi bật trên mọi bài mới**, vi phạm thì tự rút lại.

    Nên một lỗi lọt shadow chỉ sống tới bài đầu tiên vi phạm. Trên Dev, tenant là dữ liệu thử.
  - Chọn input "có chủ đích" làm p của đúng hành vi đang đổi cao hơn p ngẫu nhiên.
  - Giá trị học: không đổi, vì shadow không sinh luật.
- **Công:** −0,05 (job đơn giản hơn).
- **Bằng chứng:** README §5.4 (L0 bỏ qua R2/shadow), §8.2 ("Theo dõi sau khi bật (có từ P3…)"), §10 dòng Shadow.

### #3. Chặn chi tiêu R2 vô ích: lọc $0 trước, dừng sớm khi trượt

- **Đổi gì:**
  - **(a) Lọc R0 $0 trước R2.** Ứng viên chỉ được vào R2 khi replay trên `gate_ledger` / `repair_log` / `writing_signal`
    đã lưu cho thấy cụm mục tiêu **còn tái diễn ≥ k lần trong 30 ngày** (k là config, đề xuất 3). Với luật `lexicon` và
    `repair_hint`, R0 còn đếm được số lần luật sẽ kích hoạt. Ứng viên không có tác dụng dự kiến thì dừng ở R0.
  - **(b) Chạy R2 theo thứ tự, dừng ngay khi trượt.** Trình tự: thử 3 mẫu → phần tune (70%) của **đúng tầng bị ảnh hưởng**
    → holdout (30%), chỉ khi tune đạt.

    Dừng ngay khi có dừng cứng 1 (≥ 1 lỗi B-class/C1 mới), hoặc khi tune cho thấy chỉ số mục tiêu không tốt hơn
    (futility). **Không bao giờ dừng sớm vì "thấy tốt"**: promote vẫn cần đủ tune + holdout.
  - **(c) Không bao giờ sinh lại nhánh đối chứng.** Đối chứng là output đã lưu của release đang active. Release 0 chính là
    baseline AA-729 (README §8.1: "Đo baseline AA-729 trước release đầu tiên"). Chỉ khi release ở trạng thái `reverify`
    (đổi route model, đổi gate theo AA-787, đổi fixture) mới sinh lại đối chứng.
- **Tiết kiệm:**
  - (c) không giảm so với ước tính README (vì $3–10/lượt của README đã là một nhánh), nhưng **chặn rủi ro nhân đôi R2** nếu
    runner sinh lại cả hai nhánh.
  - (a) + (b), **ước tính:**
    - Giả sử 1/3 ứng viên dừng ở R0, và 1/3 số còn lại trượt ở tune (tiêu ~0,7 + phần thử 3 mẫu). Chi phí R2 kỳ vọng ≈
      (2/3) × [(2/3) × 1 + (1/3) × 0,75] = 0,61 của mức cũ.
    - Riêng mục này: 16,25 → ~10 = **−$6/tháng**. Gộp với #1: 6,5 → ~4.
- **An toàn / giá trị học:**
  - Dừng sớm chỉ theo hướng **từ chối**, nên không tăng rủi ro bật nhầm.
  - Dùng output đối chứng đã lưu thì không đo được độ ngẫu nhiên của chính lần sinh đối chứng. Phép so cặp (McNemar,
    Wilcoxon) vẫn đúng trên cùng mẫu. Độ nhiễu được bù bằng quy tắc "gộp ≥ 2 vòng" đã có (README §8.2 Promote).
  - Ứng viên bị loại ở R0 vẫn nằm ở tab Candidates; tháng sau cụm quay lại thì được xét lại.
- **Công:** +0,2 (R0 counterfactual theo mẫu `s245_f9_counterfactual.py`; hai checkpoint trong runner R2).
- **Bằng chứng:** README §5.4, §8.2; `research/03-measurement-design.md` §5 (R0 "current rule must reproduce observed
  numbers first"); memo M2a §1 (one-arm $8,6–10,4 cho 100 mẫu; "Before/after cần lần chạy thứ hai, hoặc chỉ chạy lớp bị
  ảnh hưởng (riêng S1 ~$3)").

### #4. Ngân sách token và chỗ chèn: giảm phụ phí mỗi bài

- **Đổi gì:**
  1. **Trần token cứng theo người viết:**
     - luật nền tảng ≤ 400 token (12 dòng × ≤ 25 từ, không phải ≤ 300 ký tự như `writing_rule.instruction` trong options.json A `data_model[2]`);
     - luật tenant ≤ 250 token;
     - ví dụ ≤ 2 × 150 token.
  2. **A1/S1 không chèn ví dụ ở v1**, chỉ luật nền tảng. Lỗi A1 chủ yếu là sự thật, từ cấm và cấu trúc (README §6). A1 là
     nội dung trung tính, không có giọng tenant, nên ví dụ giọng mang ít giá trị.
  3. Ví dụ **chỉ ở lượt viết đầu** (README đã nêu). Lượt 2 (`rewrite_with_feedback`) chỉ có luật.
  4. `repair_hint` chỉ chèn khi gate tương ứng bắn (README đã nêu). Flag_fix chỉ nhận hint của mã bị cờ (~60 token), không
     nhận khối HOUSE RULES.
  5. Lọc theo `applies_to`: luật chỉ cho social (dòng mở đầu, hashtag) không vào blog, và ngược lại.
- **Tiết kiệm mỗi bài** (Sonnet $3/1M, Haiku $1/1M; tính trên đường xấu nhất, chưa có cache hit):
  - **S1:** 1,1 lượt viết × 400 × $1/1M + 60 × $1/1M = $0,00044 + $0,00006 = **$0,0005 (+0,8–1,0%)**, thay vì $0,003.
    Hệ số 1,1 lượt viết/tour là ước tính từ "94% tới Master ngay" (03-measurement-design §1).
  - **T9 blog**, lượt 1 = 400 (luật nền tảng) + 250 (luật tenant) + 300 (ví dụ) = 950 token:
    - lượt 1: 950 × $3/1M = $0,00285;
    - lượt 2 (giả định 50% bài cần): 650 × $3/1M × 0,5 = $0,00098;
    - sửa câu (Haiku): $0,00006.

    Cộng ≈ **$0,0039 (+3,8–4,1%)**, thay vì tới +10–21%.
  - **T9 LinkedIn:** cùng phép tính ≈ $0,0039 trên $0,057 = **+6,8%**, thay vì +11–18%.
  - **T2:** 950 × $3/1M + 60 × $1/1M = $0,0029 (≈ +0,8% của $0,38).
  - **Tháng trên Dev:** không đáng kể (vài chục bài).
- **An toàn / giá trị học:**
  - Trần token ép luật ngắn, hợp với khuyến cáo "context collapse" của ACE (research/02 §2.1).
  - Bỏ ví dụ ở A1 làm mất một kênh học giọng nền tảng. Vì vậy cần đo: nếu sau P3 chỉ số "sửa nhẹ trở xuống" của A1 không
    tốt lên, bật lại ví dụ cho A1 bằng một release riêng.
- **Công:** ~0 (P3 vốn đã có "trần token", README §9 P3).
- **Bằng chứng:**
  - điểm chèn A1: lessons nối vào `brand_rules["system_prompt"]` ở `api/routers/admin_pipeline.py:560-583` và
    `services/content_generation/s1_batch.py:108-122`;
  - system A1: `services/content_generation/batch_prompt.py:158-176`;
  - T9 write và rewrite: `services/acp_content_writing/generate.py:201-202, 264-265`;
  - repair: `generate.py:277, 339-340`;
  - `_repair_feedback`: `service.py:1031-1039`;
  - flag_fix: `services/content_generation/flag_fix_node.py:560-568`.

### #5. Bộ ví dụ "ghim" theo release thay cho truy xuất kNN mỗi lời gọi

- **Đổi gì:**
  - Mỗi release tenant chứa một **bộ cố định 2 ví dụ / (tenant × người viết × kênh)**, chọn và che thực thể lúc đúc
    release, được duyệt cùng release.
  - Không truy xuất k=3 theo độ gần ở mỗi lời gọi, nên v1 không cần index ivfflat và không cần embedding mỗi bài.
- **Tiết kiệm:**
  - Tiền: embedding (README: < $0,10/tháng) và token ví dụ thay đổi theo từng lời gọi.
  - Quan trọng hơn: bộ cố định đứng yên theo release, nên đặt được trong tiền tố ổn định để cache (#7). Ví dụ kNN thì
    không, vì nó đổi mỗi lời gọi.
  - Công: **−0,25 phiên ở P4** (bỏ ivfflat + đường truy xuất).
- **An toàn / giá trị học:**
  - **An toàn tăng.** Ví dụ được duyệt một lần, shadow và R2 thấy đúng bộ ví dụ sẽ chạy. Không còn "truy xuất lúc chạy
    lấy nhầm đoạn". Test cách ly đơn giản: release tenant A chỉ chứa id của tenant A.
  - Giá trị học giảm nhẹ: Liu et al. (2101.06804) cho thấy ví dụ gần nghĩa tốt hơn ví dụ ngẫu nhiên. Nhưng ở đây ví dụ chỉ
    dùng để học **giọng**, đã che thực thể. Có thể quay lại kNN khi có tenant thật, bằng một release thử A/B.
- **Bằng chứng:** README §5.1 ("lấy 3 đoạn gần nhất"), §9 P4 ("`writing_exemplar` + ivfflat; … k=3"); options.json A
  `data_model[3]`.

### #6. Mỏ luật: chạy khi đủ tín hiệu, soạn bằng model judge rẻ hơn

- **Đổi gì:**
  - `writing_memory_mine` chỉ chạy khi có **≥ 10 tín hiệu mới đã qua lọc sự thật** kể từ lượt trước, tối đa 2 lượt/tháng,
    và luôn có một lượt trước ngày đóng đợt release.
  - Chỉ cụm đã vượt ngưỡng (đếm bằng SQL, $0) mới được gửi LLM.
  - Model soạn: route `gpt-6-luna` → `gpt-5.6-luna` → `gpt-6-luna-openai`, thay cho `gpt-5.6-luna` đứng đầu. Vẫn là model
    không phải Anthropic, nên giữ luật vendor của app ADR 0006 §5.
  - Trước khi đổi: chạy kiểm κ một lần, cùng 20 cụm cho cả hai model soạn. Tiêu chí: tỉ lệ luật qua lint + PREDICT (luật
    giải thích được ≥ 2 lần sửa) không thấp hơn quá 10 điểm. Chi phí kiểm ≈ 40 lời gọi × $0,006–0,02 ≈ $0,25–0,8, một lần.
- **Tiết kiệm:**
  - Giá: gpt-6-luna $0,10/$0,50 so với gpt-5.6-luna $0,20/$1,20, nên rẻ ~50–58% (ước tính, giá list OpenAI theo
    migration 170).
  - Mỗi lượt: $0,3–1 → ~$0,15–0,5. Số lượt: 4,3 → ≤ 2.
  - Tháng: $3 → 2 × $0,15–0,5 = **$0,3–1,0 (−$2–2,7)**.
- **An toàn / giá trị học:**
  - Luật soạn ra vẫn qua lint chỉ-hạn-chế, chặn 5-gram, PREDICT, R0–R2 và cú bấm duyệt, nên model soạn kém hơn chỉ làm tụt
    phễu ứng viên, không làm bật luật xấu.
  - Nếu κ trượt thì giữ route cũ.
  - Lưu ý: gpt-6-luna đã là model chính ở nhiều stage validate (`a3_atomize`, `s1_source_facts`, `t10_claims`) và là shadow
    10% của các judge (ai_audit.json `routes`). Nó đã chạy ổn trên acc3.
- **Công:** ~0,05 (một dòng seed `llm_role_config`, điều kiện kích hoạt job).
- **Bằng chứng:** README §5.5, §10 (≤ 50 lệnh/lượt, $0,3–1/lượt); `api/migrations/170_llm_stage_routes_and_prices.sql`
  (giá Luna).

### #7. Prompt caching: chỉ cần đặt đúng chỗ, không viết code mới

- **Hiện trạng code:**
  - Đường satellite (`invoke_claude`) gắn `cache_control: ephemeral` lên **toàn bộ** khối `system`
    (`shared/llm_client/bedrock_satellite.py:315-331` → `prompt_cache.py:9-17`). Mọi writer Claude hiện chạy đường này,
    vì `haiku` / `sonnet` là key legacy (`client.py:180-185, 314-316`).
  - User prompt gửi dạng chuỗi trần, không có điểm cache (`bedrock_satellite.py:306-310`).
  - Đường Converse (Luna judge) **không** gửi `cachePoint` (`client.py:524-529`). Bedrock tự cache ngầm các tiền tố Luna
    (`client.py:597-602`).
- **Ngưỡng tối thiểu** (AWS, <https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html>, truy cập 20/10/2026):
  - Claude Haiku 4.5: **4.096** token mỗi checkpoint;
  - Claude Sonnet 4.6 và Claude Sonnet 5: **1.024**;
  - GPT-5.6 Luna: 1.024, TTL 30 phút, Converse không hỗ trợ cache tường minh;
  - TTL Claude: 5 phút hoặc 1 giờ.
- **Áp vào từng người viết** (đếm token bằng ký tự / 4, **ước tính**):
  - **A1/S1 (Haiku):**
    - `SYSTEM_PROMPT` = 4.924 ký tự ≈ 1.231 token (`services/content_generation/prompts.py:191`). Cộng dòng ngôn ngữ và
      khối từ cấm (`batch_prompt.py:179-211`), system ≈ 1,4k token.
    - Thêm 400 token luật vẫn ≈ 1,8k, **dưới 4.096 → không bao giờ cache**. Không có gì để tối ưu ở đây; #4 đã làm phần này
      rẻ (~$0,0004/tour).
  - **T9 (Sonnet 4.6):**
    - System là `SYSTEM_PROMPT` tĩnh, chung mọi tenant, 5.201 ký tự ≈ 1,3k token (`acp_content_writing/prompts.py:184`;
      gửi ở `generate.py:201`). Vượt 1.024, nên **đã được cache** khi hai lời gọi cách nhau < 5 phút.
    - Khối brand tenant nằm trong **user** prompt (`prompts.py:334-345`, `render_brand_block` ở dòng 344).
    - → Đặt **luật nền tảng ngay sau `SYSTEM_PROMPT`** trong system: dùng chung cache mọi tenant.
    - → Đặt luật tenant và ví dụ trong user prompt, **sau** khối brand, trước CONTENT SEED.
    - Giá cho 400 token luật nền tảng:

      | Trường hợp | Giá / 1M | 400 token |
      |---|---|---|
      | Ghi cache | 1,25 × $3 = $3,75 | $0,0015 |
      | Đọc cache | 0,1 × $3 = $0,30 | $0,00012 |
      | Không cache | $3 | $0,0012 |

    - Với lượt 2 (cache hit) và các bài trong cùng đợt (wave), phụ phí T9 blog từ $0,0039 (#4) còn **$0,0023–0,0037
      (+2,2–3,9%)**. Mức thấp là khi lượt 1 cũng trúng cache.
  - **T2 (Sonnet 4.6):** system = T2 base + khối CLIENT BRAND của tenant (`batch_prompt.py:114-136`), ổn định theo tenant,
    nên luật nền tảng + tenant đặt cuối system sẽ cache trong một đợt T2 của cùng tenant.
- **Tiết kiệm:** vài phần nghìn đô mỗi bài; mỗi tháng trên Dev ≈ $0. Đây là bước "đặt đúng chỗ" để prod rẻ, không phải
  đòn bẩy cho Dev.
- **Cảnh báo:** ghi cache đắt hơn không cache (1,25×). Lưu lượng thưa (mỗi bài cách nhau > 5 phút) thì chèn vào system bị
  tính giá ghi nhiều lần, đắt hơn ~25% so với để trong user. Ở Dev chênh lệch < $0,0003/bài, chấp nhận được. Nếu sau này
  muốn cache cả lớp tenant cho T9 thì phải cho `invoke_claude` nhận user content dạng block có `cache_control` (công S–M).
  **Không đề xuất làm bây giờ.**
- **Đo trước khi tin** (read-only, chưa chạy):
  - S1 lấy từ `generated_content.metadata`:
    `SELECT count(*) FILTER (WHERE (metadata->>'cache_read_tokens')::int > 0) AS hit, count(*) FROM silver_aa_internal.generated_content WHERE created_at > now() - interval '30 days';`
    Kỳ vọng hit ≈ 0 vì dưới ngưỡng Haiku.
  - T9 lấy từ CloudWatch Logs Insights trên `/ecs/aa-cis-dev`:
    `fields @timestamp, cache_read, cache_write, in_tokens | filter event = "llm_success" and provider = "bedrock-satellite" and model = "sonnet-4-6" | stats sum(cache_read), sum(cache_write), sum(in_tokens)`

### #8. Golden set nhỏ hơn: hầu như KHÔNG nên

- Các tầng đã nhỏ: T2 10, blog 15, LinkedIn 15. Holdout 30% của T2 chỉ còn 3 mẫu (README §8.2). Cắt thêm làm mất khả năng
  chặn, mà mỗi tầng chỉ tốn $0,86–3,8.
- Cái đáng làm, và đã nằm trong #3, là **chỉ chạy tầng bị ảnh hưởng**. Release chỉ cho T9 thì không chạy tầng S1 50 mẫu
  (tiết kiệm $3). Ngoại lệ: release đụng S1 hoặc T2 phải chạy tầng "fact-dense" và "tour dài ≥ 9 ngày", vì T2 dùng chung
  graph S1 (README §6).
- Một lựa chọn nhỏ: với release **chỉ tenant**, tầng S1 không chạy, và tầng T2/T9 chỉ chạy mẫu của đúng tenant đó cộng mẫu
  isolation probe.

### #9. Bedrock Batch Inference (−50%): KHÔNG làm bây giờ

- **Giảm giá có thật:** "batch inference at a 50% lower price compared to on-demand"
  (<https://aws.amazon.com/bedrock/pricing/>, truy cập 20/10/2026).
- **Lý do không dùng:**
  1. **Tối thiểu 100 bản ghi mỗi job** (quota "Minimum number of records per batch inference job",
     <https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-data.html>; code giữ `MIN_BATCH_RECORDS = 100`
     ở `shared/llm_client/bedrock_batch.py:65-68`). R2 một tầng là 10–50 mẫu, shadow 20.
     - Gộp cả đợt tháng theo model: Haiku = 50 (S1) + 20 shadow = 70; Sonnet = 10 + 15 + 15 + 40 = 80. Cả hai vẫn < 100.
  2. **Batch không có prompt caching:** "Prompt caching is only supported for on-demand inference endpoints. It is not
     supported with the batch inference API." (trang prompt-caching ở trên).
  3. **Model judge không có trong danh sách batch.** Bảng
     <https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-supported.html> (truy cập 20/10/2026) có Claude
     Haiku 4.5 và Sonnet 4.6 (cross-region, gồm us-west-1). Nó **không** có GPT-5.6 Luna, GPT-6 Luna hay Claude Sonnet 5.
  4. **Chỉ lượt viết đầu batch được.** Vòng judge ↔ viết lại vẫn on-demand (`bedrock_batch.py:1-5`). Lượt viết chiếm
     khoảng một nửa giá một mẫu, nên mức giảm thật ≈ 25%, không phải 50%.
  5. **Quyền batch trên acc3 chưa chắc.** `bedrock_satellite.py:72-79` ghi role acc3 *không có* quyền batch, còn
     `bedrock_batch.py:20-23` ghi *có* (AA-399). AA-606 STEP0 còn mở (`bedrock_batch.py:65-67`). Profile batch cho
     `global.` chưa được trang AWS xác nhận.
- **Xem lại khi:** prod có ≥ 100 bản ghi / model / đợt. Ví dụ R2 chạy lại toàn bộ golden set sau khi đổi route model.

### Mục nhỏ đi kèm (≤ $0,5/tháng)

- Đặt `shadow_sample_pct = 0` cho stage `memory_eval` / `memory_shadow`. Seed stage mới bằng cách copy route writer/judge
  thì không copy shadow 10% gpt-6-luna của judge (ai_audit.json: `s1_judge` shadow 10%). Lý do: shadow model trên lượt eval
  không mang thông tin gì.
- Embedding cho ví dụ: bỏ hẳn ở v1 nhờ #5.

---

## 3. An toàn: thứ tự cổng giữ nguyên, rủi ro còn lại

| Cổng (README §5.4, §8.2) | Trước | Sau bộ cắt | Thay đổi rủi ro |
|---|---|---|---|
| R0 replay $0 | Có | Có, mạnh hơn (lọc ứng viên, #3a) | Không |
| R2 golden + holdout 30% | 2–3 lần/tháng, tầng bị ảnh hưởng | 1 lần/tháng, tầng bị ảnh hưởng, dừng sớm **chỉ khi trượt** | Không, vì promote vẫn cần đủ tune + holdout |
| Shadow | 50 input / người viết / release | 20 input có chủ đích; bỏ cho release `lexicon` / `repair_hint`-only | Bắt vi phạm hiếm kém hơn trước khi bật: p = 5% → 92% còn 64% (§2 #2). Bù bằng kiểm sau khi bật trên mọi bài mới, có tự rút lại |
| Cú bấm duyệt (D6 a) | Có | Có, gom một lần/tháng | Người duyệt đỡ tải hơn |
| Kiểm sau khi bật (isolation + grep QA) | Có từ P3 | Không đổi | Không |
| Rút lại = lật con trỏ | $0 | $0, không chờ đợt | Không |
| Ví dụ | kNN lúc chạy | Bộ ghim, được duyệt trong release | **Rủi ro giảm** |

Giá trị học thay đổi:
- Luật viết chậm tối đa ~30 ngày; L0 không chậm.
- A1 tạm không có ví dụ, có cửa bật lại (§2 #4).
- Ví dụ ít "đúng ngữ cảnh" hơn kNN (§2 #5).

KPI và tiêu chí dừng ở README §8 giữ nguyên, gồm dừng mềm "chi phí/bài +20%".

---

## 4. Ngân sách Dev hằng tháng với bộ đề xuất (#1–#7)

| Dòng | Trước (kịch bản giữa) | Sau | Cách tính |
|---|---|---|---|
| Mine luật | $3 | **$0,3–1,0** | ≤ 2 lượt × $0,15–0,5 (#6) |
| R2 golden | $16,25 | **$1,3–6** | 1 release/tháng × tầng bị ảnh hưởng: T9 social + blog = $0,86 + $1,5 = $2,36; thêm S1 $3; thêm T2 $3,8 (số cũ); × 0,61 do lọc R0 + dừng sớm (#3); + thử 3 mẫu ~$0,3. Thấp: một tầng LinkedIn ≈ $0,86 × 0,61 + 0,3 = $0,8–1,3. Cao: đủ 4 người viết ≈ $9,2 × 0,61 + 0,3 ≈ $6 |
| Shadow | $18,75 | **$0–4** | 20 × $0,05–0,10 × 1–2 người viết (#2); $0 khi release chỉ L0 / `repair_hint` |
| R0, R1, embedding | $1 | **$0–0,5** | R0 $0; embedding bỏ (#5); R1 ~$0,1–0,5 khi có |
| Dự phòng `reverify` (AA-787 đổi gate, đổi route) | (nằm trong trần $60) | **$1–3** | ~1 lần/quý × chạy lại tầng bị ảnh hưởng $3–9 |
| Kiểm κ model soạn luật (một lần) | — | $0,25–0,8 một lần | §2 #6 |
| **Tổng / tháng** | **$39 ($30–50)** | **≈ $3–15, thường ~$7–10** | |
| Trần đề xuất (D8) | $60/tháng, $15/lượt R2 | **$25/tháng, $10/lượt R2 release** | Lượt baseline/reverify toàn bộ (≤ $15) vẫn theo D4/AA-729 và cần duyệt riêng |

Một lần, không tính vào tháng: baseline AA-729 $8,6–10,4 (trần $15, đã duyệt qua D4).

### Phụ phí mỗi bài (khi chạy thật)

| Loại bài | Giá gốc | README | Tính lại (thiết kế cũ, đúng giá) | **Bộ đề xuất** |
|---|---|---|---|---|
| S1 tour | $0,048–0,06 | +$0,01 (+17–21%) | +$0,003 (+5–6%) | **+$0,0005 (+0,8–1,0%)** |
| T9 blog | $0,094–0,104 | +$0,005–0,02 (+5–21%) | tới +$0,0105 (+10–11%) | **+$0,0023–0,0039 (+2,2–4,1%)** |
| T9 LinkedIn | ~$0,057 | — | +$0,006–0,0105 (+11–18%) | **+$0,0023–0,0039 (+4,0–6,8%)** |
| T2 tour | $0,38 (số cũ) | — | +$0,006 (+1,6%) | **+$0,003 (+0,8%)** |

Cách tính chi tiết ở §2 #4 và #7. Mức thấp là khi luật nền tảng trúng cache trên lượt 1 (bài trong cùng đợt); mức cao là
không trúng cache. Mọi bài đều xa ngưỡng dừng mềm +20%.

---

## 5. Công và thứ tự làm

| Mục | Công (phiên) | Pha |
|---|---|---|
| #1 release train + lịch đóng đợt | ~0 | P2 (tab Releases) |
| #2 shadow 20 có chủ đích + bỏ cho L0/hint | −0,05 | P2 |
| #3 lọc R0, dừng sớm khi trượt, đối chứng đã lưu | +0,2 | P1b/P2 |
| #4 trần token + chỗ chèn + A1 không ví dụ | ~0 | P3 |
| #5 ví dụ ghim theo release | **−0,25** | P4 |
| #6 mỏ luật chạy theo tín hiệu + gpt-6-luna + kiểm κ | +0,05 | P1 |
| #7 caching đặt đúng chỗ + 2 truy vấn kiểm | ~0 | P3 |
| **Tổng** | **≈ −0,05 phiên** | Kế hoạch vẫn 6,5–7,5 phiên + dự phòng ≈ 8 |

---

## 6. Câu trả lời D nào thay đổi

| D | Nghiệp đã trả lời | Đề xuất sau bản này |
|---|---|---|
| D8 | có ($60/tháng, $15/lượt R2) | **Đổi thành $25/tháng, $10/lượt R2 release**; lượt baseline hoặc `reverify` toàn bộ (≤ $15) duyệt riêng |
| D10 | có (route judge không phải Anthropic) | Giữ "có". Model soạn luật đổi thứ tự route thành `gpt-6-luna` → `gpt-5.6-luna` → `gpt-6-luna-openai` sau khi qua kiểm κ (§2 #6) |
| D12 | có (ví dụ chỉ cho chính tenant) | Giữ "có". Cơ chế đổi: **bộ 2 ví dụ ghim theo release** thay cho kNN k=3 mỗi lời gọi (§2 #5) |
| D14 | có (18 issue) | Giữ "có", sửa nội dung 3 issue: #12 (thêm lọc R0 + dừng sớm khi trượt + đối chứng đã lưu), #13 (shadow 20 có chủ đích, release train hằng tháng), #15 (ví dụ ghim, bỏ ivfflat) |
| D15 | có (≤ 30 phút/tuần) | Giữ "có". Cú bấm duyệt release gom vào một lần/tháng; hàng đợi bất đồng vẫn hằng tuần |
| D1–D7, D9, D11, D13, D16 | có / a | Không đổi |

Chỗ sửa cần làm trong README audit khi đưa vào repo:
- §0 dòng 6 và §10: con số chi phí.
- §5.3 dòng "Chi phí tăng thêm mỗi bài": +17–21% → +5–6% theo thiết kế cũ, ~1% theo bộ đề xuất.
- §10 câu "Caching: tra được … `shared.llm_call_log`": sai, xem §1.3.

---

## 7. Câu cần Nghiệp chốt (đề xuất trả lời sẵn)

| # | Câu hỏi | Đề xuất |
|---|---|---|
| E1 | Release luật/ví dụ theo **đợt hằng tháng** (L0 từ vựng vẫn bật bất kỳ lúc nào, rút lại không chờ đợt)? | **có** |
| E2 | Shadow **20 input có chủ đích** thay cho 50; bỏ shadow cho release chỉ `lexicon` / `repair_hint`? | **có** |
| E3 | A1/S1 v1 **chỉ chèn luật, không chèn ví dụ**; ví dụ cho T2/T9 là **bộ 2 ví dụ ghim theo release**? | **có** |
| E4 | Trần mới **$25/tháng, $10/lượt R2 release** (sửa D8)? | **có** |

---

## 8. Chưa biết / cần đo

- Token thật của các system prompt: ở đây đếm bằng ký tự / 4. Nên đếm lại bằng tokenizer Claude trước P3.
- Tỉ lệ cache hit hiện tại của `t9_write` và `t2_generate`: chưa đo, truy vấn ở §2 #7.
- Giá đơn vị T2 sau AA-792: số $0,38 là số cũ. Baseline AA-729 sẽ có số mới.
- Giá Bedrock chính thức cho Haiku 4.5, Sonnet 4.6 và hai Luna: trang giá không hiện được bảng khi tải về, nên coi là ước
  tính bằng giá list (catalog migration 169/170).
- Tỉ lệ ứng viên dừng ở R0 và trượt ở tune (1/3 và 1/3 ở §2 #3) là giả định. Sau 2 đợt release, thay bằng số thật từ phễu
  ứng viên (KPI "Sức khoẻ vòng", README §8.1).

---

## Kiểm chứng độc lập

Người kiểm: Claude Code (subagent kiểm phản biện), 20/10/2026. Chỉ đọc: không truy vấn DB, không gọi LLM, không sửa repo.
Chi phí $0. Code đọc ở AA-CIS-App `origin/main` **b7e6da66** (xuất bằng `git show` / `git archive`, vì checkout local
`f9fc32d6` lệch 13 file trong `services/` so với `origin/main`; `shared/llm_client/` thì giống hệt). Mọi trang AWS dưới đây
truy cập ngày **20/10/2026**.

### K0. Sự thật nền đã kiểm

- **Đường gọi là `global.`, không phải `us.`.** Satellite gọi profile `global.anthropic.claude-sonnet-4-6` và
  `global.anthropic.claude-haiku-4-5-20251001-v1:0` (`shared/llm_client/bedrock_satellite.py:138-139`, ghép ARN ở
  `:142-155`); Luna trên acc3 dùng `global.openai.gpt-6-luna` (`api/migrations/170_llm_stage_routes_and_prices.sql:84-85`).
  Hằng `us.` trong `shared/llm_client/pricing.py:30` chỉ dành cho nhánh acc2-native, đã tắt mặc định (AA-843,
  `client.py:263-270`). Vì vậy mọi phép tính ở bản trên đã đúng mức giá rẻ nhất có thể.
  - AWS: global rẻ hơn geo khoảng 10% cả đầu vào lẫn đầu ra
    (<https://docs.aws.amazon.com/bedrock/latest/userguide/global-cross-region-inference.html>).
  - **Cảnh báo:** quyết định CRM D12 ("Bedrock acc3 `us.` only") chỉ áp cho app CRM. Nếu áp sang vòng học của CIS thì mọi số
    ở đây **+10%** (Luna geo $0,11/$0,55 và $0,22/$1,32, xem K1).
- **Route writer** (snapshot `ai_audit.json` 14/10, `routes[7,8,15,16,21,22]`) khớp bản trên. Từ migration 225 tới 250
  trên `origin/main` không có migration nào đổi route writer: 226 chỉ thêm stage geo, 240 chỉ đổi fallback embed.
- **Prompt:** đo bằng `len()` trên `origin/main`.
  - `services/content_generation/prompts.py:191` `SYSTEM_PROMPT` = **4.924** ký tự.
  - `services/acp_content_writing/prompts.py:184` = **5.201** ký tự.

  Khớp bản trên. Token vẫn là ước tính ký tự/4.
- **Cache:** satellite gắn `cache_control: ephemeral` lên khối `system` (`bedrock_satellite.py:315-331` →
  `prompt_cache.py:9-17`), còn user prompt là chuỗi trần (`bedrock_satellite.py:306-310`). Khớp.
- **Cột cache:** `shared.llm_call_log` không có cột cache (`docs/architecture/db-schema-reference.md:2708-2726`).
  `pricing.py:112-113` đã cộng tiền cache vào `cost_usd`. Khớp §1.3.
- **Ngưỡng cache** (<https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html>, cùng thẻ model Haiku 4.5
  và Sonnet 4.6):

  | Model | Tối thiểu / checkpoint | TTL |
  |---|---|---|
  | Haiku 4.5 | 4.096 | 5 phút / 1 giờ |
  | Sonnet 4.6 | 1.024 | 5 phút / 1 giờ |
  | GPT-5.6 Luna | 1.024 | 30 phút |

  Converse không hỗ trợ cache tường minh cho Luna. Batch không có prompt caching. Tất cả khớp.
- **Bổ sung bản trên chưa nêu:**
  - Model Anthropic trên Bedrock **cũng có cache ngầm** (implicit caching).
  - AWS ghi rõ cross-Region "may lead to increased cache writes".

  Vì vậy mức thấp của #7 (lượt 1 trúng cache) phải **đo** trước khi tin.

### K1. Giá: nâng hạng nguồn

| Model | Giá Global CRIS (đầu vào / đầu ra, 1M token) | Nguồn | Trạng thái |
|---|---|---|---|
| GPT-5.6 Luna | $0,20 / $1,20; đọc cache $0,02; Geo/US $0,22 / $1,32 | <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-56-luna.html> | **Đã xác nhận** (bản trên ghi "ước tính") |
| GPT-6 Luna | $0,10 / $0,50; đọc cache $0,01; US Geo $0,11 / $0,55 | <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-luna.html> | **Đã xác nhận** |
| Claude Haiku 4.5 | $1 / $5 | Trang giá AWS không render bảng Anthropic khi tải; thẻ model chỉ trỏ về trang giá | Ước tính. Global bằng giá list Anthropic; trang global CRIS ở trên xác nhận geo đắt hơn ~10% |
| Claude Sonnet 4.6 | $3 / $15 | như trên | Ước tính, như trên |

**Kết luận:** mức tiết kiệm 50% (đầu vào) và 58% (đầu ra) của #6 nay có nguồn AWS chính thức.

### K2. Phán quyết từng mục

| Mục | Phán quyết | Lý do (đã kiểm) | Số đúng |
|---|---|---|---|
| §1.2 tính lại phụ phí mỗi bài | **giữ** | `s1_generate` và `s1_flag_fix` = `haiku` (routes[8], [7]); `pricing.py:39` = $1/$5 cho mỗi 1M token. 2 × 1.500 × $1/1M = $0,003 = 5,0–6,3% | LinkedIn thiết kế cũ: +10,5–18,4% (bản trên ghi 11–18%, lệch làm tròn) |
| §1.3 câu "caching tra được trong `llm_call_log`" là sai | **giữ** | Xem K0 | — |
| #1 release theo đợt tháng | **giữ** | Số học đúng: (2,5−1) × (6,5 + 7,5) = $21. Mọi cổng giữ nguyên; rút lại vẫn $0 | −$21/tháng |
| #2 shadow 20 | **sửa** | (a) Số học sai. (b) Vi phạm luật T2/Facebook. (c) Bỏ shadow cho `repair_hint` là sai. (d) Thiếu kiểm cách ly. Chi tiết dưới bảng | Shadow/release ≈ **$3,0**; riêng mục: **−$11,25/tháng**; gộp với #1: **−$4,5**. Ngân sách xem K3 |
| #3 lọc R0 + dừng sớm + đối chứng đã lưu | **sửa** | (a) Hệ số 0,61 trộn hai đơn vị. (b) Ngưỡng k = 3 làm đói vòng học. (c) Đối chứng phải chấm lại bằng judge hiện hành. Chi tiết dưới bảng | R2 = chi phí tầng × **0,92** + $0,3 thử |
| #4 trần token + chỗ chèn | **giữ** | Số học kiểm lại khớp: S1 $0,0005 (0,8–1,0%); T9 blog $0,0039 (3,7–4,1%); LinkedIn 6,8%; T2 $0,0029 (0,8%). Điểm chèn khớp code. Bỏ ví dụ ở A1 là đổi thiết kế đã duyệt, nên phải qua E3 (đã có) | Như bản trên |
| #5 ví dụ ghim theo release | **giữ, sửa lý do cache** | Lý do an toàn và công vẫn đúng. Lợi ích cache **không thành hiện thực** với code hiện tại: user prompt là chuỗi trần (`bedrock_satellite.py:306-310`), và trong user prompt T9 các dòng CHANNEL / GOAL đứng trước khối brand (`acp_content_writing/prompts.py:334-344`), nên tiền tố tenant đổi theo kênh và mục tiêu. Bỏ câu "đặt được trong tiền tố ổn định để cache" | Tiền: ~$0 |
| #6 mỏ luật theo tín hiệu + `gpt-6-luna` | **giữ** | Giá đã xác nhận (K1). Profile `global.` (migration 170:85). `gpt-6-luna` là model chính của `a3_atomize`, `s1_source_facts`, `t10_claims` (routes[1], [11], [12]). Đòn bẩy phụ (**ước tính**, không tính vào ngân sách): đặt reasoning effort `low` cho lượt soạn luật. Mặc định là `medium` theo thẻ model; hiện client không gửi tham số này qua Converse (`client.py:518-529`) | $0,3–1,0/tháng |
| #7 đặt luật nền tảng sau `SYSTEM_PROMPT` T9 | **giữ** | Thông số khớp. Số tính: lượt 1 trúng cache $0,00177 + lượt 2 × 0,5 = $0,000435 + sửa $0,00006 = $0,0023; không trúng = $0,0036. Thêm cảnh báo: global CRIS có thể làm tăng ghi cache (K0); đo bằng 2 truy vấn trước khi tin mức thấp | +2,2–3,9% (blog) |
| #8 không thu nhỏ golden set | **giữ** | Khớp README §8.2: holdout T2 chỉ 3 mẫu | — |
| #9 Bedrock Batch: không làm | **giữ kết luận, sửa ý 5** | Ý 1–4 đúng: tối thiểu 100 bản ghi (`bedrock_batch.py:65-68`); batch không có cache; danh sách batch có Haiku 4.5 và Sonnet 4.6 (us-west-1, cross-region) nhưng không có GPT-5.6/6 Luna (<https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-supported.html>). Ý 5 sai một nửa: trang global CRIS ghi "Global inference profile is supported for … Batch inference". Mâu thuẫn quyền batch acc3 vẫn đúng: `bedrock_satellite.py:72-79` nói không có, `bedrock_batch.py:20-23` nói có | — |
| Mục nhỏ `shadow_sample_pct = 0` cho stage eval | **giữ** | Shadow judge chạy theo cấu hình stage (`client.py:175-177`). Nếu R2 dùng lại tên stage judge cũ (`s1_judge` shadow 10%) thì tốn thêm, nên stage eval riêng phải seed với shadow 0 | <$0,5 |
| **Mới: Flex tier (−50%)** | **bỏ** (đã xét, không dùng được) | Flex không hỗ trợ Haiku 4.5, Sonnet 4.6, GPT-5.6 Luna, GPT-6 Luna (mục "Service Tiers" của từng thẻ model ở K1; <https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html>) | — |
| **Mới: giữ `global.`** | **giữ (mặc định đã đúng)** | Xem K0. Không chuyển writer CIS sang `us.` nếu không tính thêm +10% | Nếu chuyển: +10% mọi dòng |

**Chi tiết #2 (shadow 20):**
- **(a) Số học sai.** Từ 50 xuống 20 là ×0,4. Nên 7,5 → **3,0**, không phải 2,25: bản trên dùng $0,10/input cho mức cũ
  nhưng $0,075 cho mức mới. Riêng mục này 18,75 → 7,5.
- **(b) Vi phạm luật đã duyệt của README §8.2** (`docs/audits/2026-10-20-S245-writing-learning-loop/README.md:379-381`):
  "release T2 và Facebook luôn dùng quy tắc dự phòng … (cộng shadow 50 input thật)", vì holdout T2 chỉ có 3 mẫu và
  không có tầng Facebook. **Phải giữ 50 cho T2 và Facebook.**
- **(c) Bỏ shadow cho release chỉ có `repair_hint` là sai.** Hint chỉ chèn khi gate bắn, mà golden set ít ca gate bắn, nên R2
  có thể không chạm hint lần nào. Thay bằng shadow có chủ đích ≤ 10 input mà gate đó từng bắn (~$0,5–1), hoặc replay
  riêng lượt sửa (Haiku, ~$0,0015/lượt) trên bản nháp và cờ đã lưu.
- **(d) Thêm 1–2 input của tenant khác** vào shadow của release tenant, làm probe cách ly (~$0,2). Lý do: shadow chỉ trên
  input của chính tenant đó không bắt được lỗi chọn release sai tenant.
- Xác suất bắt lỗi 64% / 88% / 96% tính đúng.

**Chi tiết #3:**
- **(a) Hệ số 0,61 trộn hai đơn vị.** "1/3 dừng ở R0" là tỉ lệ theo **ứng viên**, nhưng R2 chạy theo **release**. Khi
  gộp đợt tháng (#1), một release chỉ bị bỏ R2 khi *mọi* ứng viên rớt R0, tức xác suất (1/3)^k, rất nhỏ. Hệ số đúng khi
  gộp với #1 chỉ còn phần dừng sớm do trượt: 1 − (1/3)(0,25) ≈ **0,92**.
- **(b) k = 3 lần trong 30 ngày có thể làm đói vòng học trên Dev.** Ngưỡng mỏ luật là ≥ 2 lần sửa trên ≥ 2 bài. Nên đặt k
  bằng đúng ngưỡng mỏ luật.
- **(c) Đối chứng đã lưu phải được chấm lại bằng judge đang dùng.** Chi phí Luna không đáng kể. Nếu không, độ lệch giữa
  các phiên bản judge làm sai phép so cặp.
- Hướng an toàn (dừng chỉ để từ chối) đúng.

### K3. Bảng ngân sách Dev đã sửa (thay §4)

| Dòng | Bản trên | **Sau kiểm chứng** | Cách tính |
|---|---|---|---|
| Mine luật | $0,3–1,0 | **$0,3–1,0** | Không đổi; giá Luna đã xác nhận |
| R2 golden | $1,3–6 | **$1,1–8,7** (thường ~$2,5) | 1 release/tháng; hệ số 0,92 (không phải 0,61) + thử 3 mẫu $0,3. Thấp: LinkedIn $0,86 × 0,92 + 0,3. Thường: blog + LinkedIn $2,36 × 0,92 + 0,3. Cao: 4 tầng $9,16 × 0,92 + 0,3 |
| Shadow | $0–4 | **$0–7** (thường ~$1,5) | 20 input × $0,05–0,10 cho A1 / blog / LinkedIn; **50 input cho T2 và Facebook** (README §8.2); +$0,2 probe cách ly; ≤ 10 input có chủ đích cho `repair_hint`. Cao: T2 50 × $0,10 + một người viết 20 × $0,10 = $7 |
| R0, R1, embedding | $0–0,5 | **$0–0,5** | Không đổi |
| Dự phòng `reverify` | $1–3 | **$1–3** | Không đổi |
| Kiểm κ (một lần) | $0,25–0,8 | **$0,25–0,8 một lần** | Không đổi |
| **Tổng / tháng** | §0: "$4–18, thường $8–10"; §4: "$3–15, thường $7–10" (**hai chỗ tự mâu thuẫn**) | **≈ $2,5–20, thường ~$7** | 0,3 + 1,1 + 0 + 0 + 1 = 2,4; 1,0 + 8,7 + 7 + 0,5 + 3 = 20,2; 0,6 + 2,5 + 1,5 + 0,2 + 2 = 6,8 |
| Nếu chuyển sang profile `us.` | — | ≈ $2,7–22 | +10% (K0) |
| Trần (D8 / E4) | $25/tháng, $10/lượt R2 | **Giữ $25/tháng, $10/lượt R2** | Còn ~$5 khoảng trống trên mức cao. Nếu giá T2 sau AA-792 > ~$0,50/tour thì R2 đủ 4 tầng vượt $10: khi đó tách release hoặc xin duyệt riêng |

Phụ phí mỗi bài (§4 bảng thứ hai): **giữ nguyên**, số học kiểm lại đúng.

So với README ($30–50): vẫn giảm khoảng **80%**, nhưng mức cao là $20 chứ không phải $15. Phần tăng chủ yếu do giữ đúng
luật shadow 50 cho T2 và Facebook.

### K4. Câu chốt E sửa theo kiểm chứng

| # | Đề xuất sau kiểm chứng |
|---|---|
| E1 | **có**, không đổi |
| E2 | **có, sửa nội dung:** shadow 20 input có chủ đích cho A1, blog và LinkedIn. **T2 và Facebook giữ 50** cho tới khi golden set mở rộng hai tầng này. Release chỉ có `repair_hint` dùng shadow ≤ 10 input mà gate từng bắn, không bỏ hẳn. Release tenant thêm 1–2 input của tenant khác làm probe cách ly |
| E3 | **có**, không đổi. Ghi rõ lợi ích là an toàn và công, không phải cache |
| E4 | **có**: $25/tháng, $10/lượt R2. Mức cao dự kiến $20 |

Thêm vào issue #12 (D14): **k = ngưỡng mỏ luật** (không phải 3); **chấm lại đối chứng đã lưu bằng judge hiện hành**.

### K5. Còn chưa kiểm được

- Bảng giá Claude trên Bedrock (Haiku 4.5, Sonnet 4.6): trang giá không render khi tải về, nên vẫn là ước tính bằng giá list.
- Token thật của hai `SYSTEM_PROMPT`: tính bằng ký tự/4. T9 ≈ 1,3k, sát ngưỡng 1.024 của Sonnet. Nếu tokenizer cho số dưới
  1.024 thì T9 hiện **không** cache, và #7 mất mức thấp.
- Tỉ lệ cache hit thật của `t9_write` / `t2_generate`: chưa đo. Hai truy vấn ở #7 là cách đo.
