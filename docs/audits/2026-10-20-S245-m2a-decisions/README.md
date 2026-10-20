# M2a — ba bản ghi nhớ quyết định (AA-729, AA-787, AA-845)

Ngày 20/10/2026, phiên S245, tác nhân: Claude Code. Chỉ đọc: không đổi Linear, Jira, Notion, GitHub hay AWS, không chạy
gì tốn tiền. Mỗi bản ghi: quyết định cần chốt, phương án + chi phí, khuyến nghị, câu Nghiệp cần trả lời, việc agent làm
ngay sau đó, và vướng mắc không cần Nghiệp quyết. Nghiệp chốt S245: làm sản phẩm hoàn chỉnh, không MVP — các khuyến nghị
dưới đây theo hướng đó.

**Trả lời nhanh (gửi một dòng):** `AA-729: a / có / có · AA-787: có · AA-845: c` là đúng theo khuyến nghị.

| Issue | Câu cần trả lời | Khuyến nghị |
|---|---|---|
| AA-729 | (1) phương án a/b/c; (2) có/không: 1 lần chạy baseline 100 mẫu, trần $15, + 1 lần before/after sau này; (3) có/không: thay dòng 3 Done-when | **a / có / có** |
| AA-787 | Bỏ gate `promises_an_option` trong AA-787? có/không | **có** (bỏ) |
| AA-845 | Nguồn nhãn cho `a1_claim_supported`: a / b / c | **c** |

---

## 1. AA-729 — golden set, nhãn và chi phí chạy

**Quyết định cần chốt:** phạm vi golden set và duyệt chi phí một lần chạy baseline có trả phí, khoảng $10, trần $15 mỗi lần.

### Phương án

| | a. Harness hoàn chỉnh (khuyến nghị) | b. Chỉ chấm (judge-only) | c. Bộ nhỏ S241 P1-5 |
|---|---|---|---|
| Mẫu | 100: 50 tour S1/Master, 10 T2, 15 blog T9, 15 LinkedIn T9, 10 prompt-injection | Cùng 100 mẫu | 20–30 T2/T9 + injection |
| Cách chấm | Hai chế độ trong một script: **sinh lại + chấm**, và **chỉ chấm** trên output đã đóng băng | Chỉ chấm | Sinh lại + chấm |
| Chi phí mỗi lần chạy | **~$8,6–10,4.** Thử 3 mẫu < $0,5. Before/after cần lần chạy thứ hai, hoặc chỉ chạy lớp bị ảnh hưởng (riêng S1 ~$3) | ~$1–2 (`s1_judge` ~$0,008/tour) | ~$2–4. Lộ trình đặt mục tiêu ≤ $1 nhưng giá từng mẩu không cho phép |
| Công sức | L (~2 phiên) | M | S–M |
| Rủi ro | 100 mẫu vượt luật "khoảng 50" cho lần chạy trả phí → cần Nghiệp đồng ý | Không đo được thay đổi writer/prompt → không đạt dòng 3 Done-when | Không phủ trục A; đây chính là MVP Nghiệp đã loại |
| Mở khoá | Dòng 3 Done-when, AA-900, số before/after cho AA-748/AA-714, chỉ số Jev của AA-756 | Chỉ chỉnh judge và ngưỡng | Chỉ trục T |

Nguồn giá đơn vị: S1 $0,048–0,06/tour (`docs/audits/2026-10-08-S218-a-series-pipeline-audit.html`); T2 $0,38/tour, blog
~$0,14, LinkedIn ~$0,057 (`docs/audits/2026-10-12-S231-t-series-pilot.md`); blog $0,094–0,104 ở S234
(`docs/audits/2026-10-13-S234-t-series-rounds/09-next-step-plan.md`). Số T2 có từ trước khi đổi prompt AA-792, nên giá
hiện tại của T2 chưa biết.

### Khuyến nghị

**a.** Nghiệp yêu cầu sản phẩm hoàn chỉnh, không MVP; (a) phủ đủ, và chế độ chỉ-chấm của (b) đã nằm sẵn trong (a).

### Nghiệp cần trả lời

1. Phương án **a / b / c**?
2. **Có/không:** cho phép một lần chạy baseline 100 mẫu, trần $15, cộng một lần before/after sau này?
3. **Có/không:** thay dòng 3 của Done-when bằng: "*The next S1 or T9 prompt, model or threshold change after the
   baseline (e.g. AA-748, AA-714) cites before/after numbers on the same fixture version.*" AA-724 đã Done từ 07/10 nên
   dòng hiện tại không thể đạt.

### Agent làm ngay sau đó

1. Sửa Done-when trên Linear, mở `docs/implementation-notes/AA-729.md`.
2. Chọn mẫu ở chế độ chỉ đọc qua `cis_app`.
3. Lấy nhãn từ kết quả review queue, phản hồi của chị Thư và kết luận các audit. Mẫu chưa có nhãn thì panel agent gán,
   Nghiệp chỉ kiểm các chỗ panel bất đồng.
4. Mở PR AA-CIS-App với fixture có version (id, nhãn, nguồn nhãn, input đóng băng, không PII) và script chấm. Mọi lời gọi
   qua `LLMClient` với `stage="adhoc_aa729"`.
5. Chạy thử 3 mẫu, báo chi phí; rồi chạy baseline đầy đủ bằng một ECS task một lần.
6. Viết báo cáo vào `docs/audits/<date>-S<nnn>-aa729-baseline/`, chi phí lấy từ `llm_call_log` đối chiếu với dashboard nhà
   cung cấp (lessons.md).

### Vướng mắc không cần Nghiệp quyết

- Master plan cho M2a bắt đầu sau khi M1 xong (`docs/audits/2026-10-19-S244-master-plan/README.md:44`); AA-729 xếp ở S247.
- Nhãn người cho T9 của AA-783 (Backlog) chưa có, nên nhãn T9 ban đầu là "panel AI, Nghiệp duyệt".
- Jev của `t10_gates` đang tắt, nên độ đồng thuận Jev chỉ đo được ở các stage trục A.
- Lessons cấm chạy trả phí khi còn PR backend chờ merge hoặc còn job trong hàng đợi.
- Số nhãn review queue dùng được chưa query live.

Nguồn (đọc 20/10/2026): Linear AA-729 (chưa có comment), AA-724, AA-783; `docs/sessions/2026-10-17-S241-decisions.md`
(D-19, D-23); `docs/audits/2026-10-17-S241-sdlc-review/unified-roadmap.md` (U-29, P1-5);
`docs/audits/2026-10-15-S238-backlog-audit/README.md:22`; `skill/aa-lessons/lessons.md`; memory `paid-runs-subset`.

---

## 2. AA-787 — xác nhận lại việc bỏ `promises_an_option`

**Quyết định cần chốt:** AA-787 có còn bỏ warn gate `promises_an_option` không, khi AA-773 đã làm nó hiểu Status và nó
đã im lặng?

### Dữ kiện (đọc 20/10/2026)

- Nghiệp duyệt bỏ ở S234 vì gate bắn 32/32 blog (8/8 blog r4, 23 dương tính giả). Nguồn:
  `docs/audits/2026-10-13-S234-t-series-rounds/11-next-session-team-pilot.md:58`, `08-pipeline-stats-thu-jev.md:358`,
  Linear AA-787 (chưa có comment).
- AA-773 (CIS #714) làm gate hiểu Status. Ở r5 nó cảnh báo **0/8** blog, panel đếm **0/8** lật offered↔included. Nguồn:
  `docs/audits/2026-10-14-S235-ecosystem-team-pilot/r5/00-r5-summary.md`, `measure_r5.json`.
- Trên CIS main `5486a0ee` gate là tất định, chỉ cảnh báo: không giữ, không sửa mẩu nào, không gọi LLM. Cùng lỗi đó đã
  được `F17_trip_fact` phủ — gate chặn và sửa được. Nguồn: `services/acp_content_writing/quality_gates.py:416-459, 2039, 1705-1723`.
- Log admin S239: gate pass 0 vi phạm trên mọi ledger (6 lần chạm). Nguồn:
  `docs/audits/2026-10-16-S239-in-progress-audit/aa668-verify/rerun/logs/admin-pieces-social.json`.
- Giới hạn đã biết của F17: offline nó bỏ sót câu rào đón cùng mệnh đề ở r4 (F17 thấy 0/8, panel thấy 3). Nguồn: `r5/README.md:92`.

### Phương án

| | Chi phí (USD) | Công sức | Rủi ro | Mở khoá |
|---|---|---|---|---|
| **a. Bỏ gate (giữ quyết định S234)** | $0. Gate tất định nên before/after là replay offline | Nằm trong ~1 ngày của AA-787 | Thấp. Nếu F17 bỏ sót một ca thì mất lớp kiểm còn lại — mà lớp đó đã im lặng (0/8) | Số gate từ 27 xuống ~18 như đã viết; AA-788 và AA-741 G7 |
| b. Giữ làm cảnh báo | $0 | −0,1 ngày | Thêm một dòng trong Content Quality, trùng F17 | AA-787 vẫn làm F8/F3/F5 và các gộp, còn ~19 gate |
| c. Gộp vào F17 thành kiểm phụ không chặn | $0 | +0,5 ngày, vì logic `body_blocking` của F17 phải giữ nó ở mức cảnh báo | Trung bình: đụng vào một gate chặn | Như (a), và giữ được khả năng phát hiện |

### Khuyến nghị

**a.** Vấn đề nhiễu đã hết, nhưng F17 giờ phủ cùng lỗi với cơ chế chặn + sửa. Một gate riêng bắn 0/8 không thêm tín hiệu.
Kèm một chốt chặn: nếu replay golden set tìm ra lỗi thật mà `promises_an_option` bắt được còn F17 bỏ sót, agent chuyển sang
(c) và báo lại.

### Nghiệp cần trả lời

**Bỏ `promises_an_option` trong AA-787? có / không.** "Không" nghĩa là phương án (b).

### Agent làm ngay sau đó

1. Tạo branch từ `origin/main`, gỡ gate (hoặc giữ nếu trả lời b). Bỏ F8 (bỏ luôn lời gọi LLM của nó), F3 và F5; áp các
   gộp (F7→F16, F15_voice_warn→F15, các biến thể F2 + danh sách stock → một gate lexicon, F13_hygiene repeat → F13_repeat).
2. Thêm ghi chú sửa đổi ADR 0023/0026; cập nhật `frontend/app/admin/content-quality/shared.ts:274` và thống kê gate.
3. Chạy replay offline $0 để có số before/after, rồi CI, merge, deploy, kiểm tab Content Quality trên UI.

### Vướng mắc không cần Nghiệp quyết

- Số before/after trên golden set cần AA-729 (còn Backlog; việc duyệt mẫu và chi phí của nó là quyết định riêng ở §1).
  Trong lúc chờ, replay chỉ chạy trên các mẩu S234/r5.
- Trong master plan, M2a (S247) chỉ bắt đầu sau khi M1 đóng.
- AA-777 sửa cùng danh sách `run_quality_gates`, nên sẽ có xung đột merge dạng văn bản. Nguồn:
  `apps/AA-CIS-App/docs/implementation-notes/AA-786.md:93`.
- Tỉ lệ bắn live hiện tại trên Dev chưa biết (không query DB).

---

## 3. AA-845 — nguồn nhãn cho `a1_claim_supported`

**Quyết định cần chốt:** ground truth mức câu cho `a1_claim_supported` lấy từ đâu. (a) Một hành động của reviewer đánh
dấu một câu là "unsupported". (b) Một bộ khoảng 100 câu vùng xám do panel agent Claude gán nhãn một lần, Nghiệp duyệt.
Nguồn: mục Scope của AA-845 (chưa có comment tính tới 20/10/2026).

### Phương án

| | (a) Hành động từng câu của reviewer | (b) Bộ nhãn panel agent | (c) b ngay bây giờ, rồi a làm vòng lặp lâu dài |
|---|---|---|---|
| LLM trả phí | $0 | $0 nếu chạy bằng subagent Claude Code. Sau đó một wave đo, < $1 Jev (~12,7k lời gọi × $0,00007878, theo lessons dòng 26; đếm số lời gọi trước khi chạy) | Như (b) |
| Công sức | M–L: API + UI Review Queue + `record_rejected_outcome` + kiểm UI. Hiện frontend chưa có hành động claim từng câu (grep CIS `origin/main`) | M: lấy mẫu, panel, báo cáo, duyệt | L |
| Rủi ro | Dev không có reviewer thật; reviewer bấm Regenerate thay vì duyệt nên `approved_versions = 0` (S228 Part 6). Nhãn có thể mất vài tuần, hoặc không bao giờ có | Bộ một lần, cũ dần khi writer đổi (AA-748). Nhãn AI, không phải người | Công sức cao nhất |
| Mở khoá | Lâu dần có outcome | Trần reject 0,15 ở S252. Cùng lượt gán nhãn luôn cho AA-803 (`a1_promise_unsupported`) | Cả hai, cộng vòng lặp chạy tiếp sau khi ra mắt |

Thiết kế mẫu cho (b): phân tầng ~60 câu có p ≤ 0,20 và ~40 câu trong 0,20–0,85. Kể cả đúng 100/100, cận dưới Wilson
khoảng 96%, nên 100 là tối thiểu cho ngưỡng precision 95%.

### Khuyến nghị

**c.** Nghiệp yêu cầu sản phẩm hoàn chỉnh, không MVP. (b) một mình chỉ là làm một lần; (a) một mình không sinh nhãn trên
Dev. Dùng (b) để hiệu chỉnh ngay, và ship (a) làm vòng lặp ground truth lâu dài.

### Nghiệp cần trả lời

**a, b hay c?**

### Agent làm ngay sau đó

- **(b) hoặc (c):** rút mẫu phân tầng từ `decision_log`; gán nhãn `claim_supported` và `promise_unsupported` trong một
  lượt panel; lưu bộ vào `docs/calibration/`, liệt kê các chỗ bất đồng để Nghiệp duyệt. Sau đó áp reject ≤ 0,15 qua
  `PUT /admin/decisions/questions/a1_claim_supported`, chạy một wave ≤ ~50 tour, báo % vùng xám và chi phí trước/sau.
- **(c):** thêm việc xây hành động "unsupported" từng câu và ghi outcome, deploy, kiểm outcome > 0.

### Vướng mắc và cờ không cần Nghiệp quyết

1. **Lỗi 402 có vẻ là chuyện cũ.** Lambda hằng ngày `aa-cis-dev-dfs-balance-check` báo `/admin/jev/402-sweep`
   `errors_24h: 0` và canary `credit_ok: true` mỗi ngày từ 05/10 đến 19/10 (CloudWatch, đọc 20/10/2026). Con số ~47,9k của
   S234 tính cho 29/09–13/10 (`docs/audits/2026-10-13-S234-t-series-rounds/08-pipeline-stats-thu-jev.md:723,746`), gồm cả
   sự cố hết credit 03/10, trước khi AA-720 ship ngày 05/10 (log S209, S210). Chưa đối chiếu với đếm `decision_log` theo
   ngày hay các dòng `jev_credit_topup` (ước 12), nên vẫn chưa xác nhận. Việc kiểm này là việc của agent.
2. **Xung đột phạm vi.** Mục 2 của AA-845 ghi truth=False cho **mọi** câu khi một Review bị reject. S228 Part 6 nói reject
   là chấm cả version, nên làm vậy sẽ gán nhãn sai hàng loạt. Cách sửa: chỉ ghi truth=False cho câu reviewer đánh dấu —
   chính là phương án (a).
3. **AA-720 và ledger.** AA-720 đã quyết "không làm ledger", nhưng AA-845 lại so 402 với `jev_credit_topup`. Bảng có tồn
   tại (`docs/architecture/db-schema-reference.md:2598`) nhưng có dữ liệu hay không thì chưa biết.
4. **Wave đo** chỉ chạy được khi các bảng job rảnh (DM-11.4).

Nguồn: Linear AA-845, AA-803, AA-720; `docs/audits/2026-10-11-S228-jev-aseries-closeout.md` (Item 1, Part 6);
`docs/audits/2026-10-19-S244-master-plan/README.md:128,177`; `skill/aa-lessons/lessons.md:26-27`. Đọc 20/10/2026.
