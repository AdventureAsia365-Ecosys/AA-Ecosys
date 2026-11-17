# Giới hạn AI: hệ thống đã build đúng chính sách S283 chưa? (S283, 17/11/2026)

**Trả lời ngắn: chưa.**
- Dev đã đúng "hard cap".
- Cả 5 điểm của chính sách prod đều còn khoảng trống, trừ điểm 4 (AWS Budgets) đã đúng.
- Nặng nhất là điểm 2 và 3: nhiều cap mức nền tảng (cả app, cả connection) vẫn **chặn cứng mọi đại lý**, và chưa có circuit breaker theo chi tiêu bất thường.

**Cách kiểm:** chỉ đọc code và migration. Không ghi DB, không gọi AWS, không gọi trả phí. Số live lấy từ `.tmp-session/ecsx/20261116T233600-15940-gateway_status.out` (16/11).

**Chưa kiểm live:**
- cờ `hard_stop` thật của từng connection;
- giá trị `tp.ai_sessions` thật trên CIS Plans;
- CRM đã đặt daily budget cho app chưa;
- #271 của TripPlanner đã deploy lên Lambda chưa.

Viết tắt đường dẫn: `CIS=apps/AA-CIS-App`, `TP=apps/AA-TripPlanner-Web`, `CRM=apps/AA-Partner`, `INFRA=infra/AA-CIS-Infra`.

---

## 1. Bảng tổng hợp: 5 điểm chính sách

| # | Điểm chính sách | Đã build gì (người dùng thấy gì) | Dev | Prod cần gì | Khoảng trống | Mức độ | Đề xuất + cỡ việc |
|---|---|---|---|---|---|---|---|
| 1 | **Quota theo gói tenant phải HARD, UI nói rõ, có đường nâng gói** | **Content studio (CIS):**<br>- `shared.tenant_ai_budget` hard theo mặc định: plan 15/40/80 USD (`CIS/shared/cost_guard.py:603-615`), `ai_hard_stop_default=True`.<br>- Gate chạy trước mọi call T-stage (`CIS/shared/llm_client/client.py:1553-1563`).<br>- Chạm ngưỡng thì job thành `stopped_budget`, chờ staff duyệt (`tenant_budget.py:10-18`).<br>- Đại lý chỉ thấy **"Writing failed" + Retry** (`CRM/web/app/(studio)/portal/_components/catalogApi.ts:110`). Retry sẽ dừng y như cũ. Chuông/e-mail chỉ gửi staff (`cost_guard.py:797-813`).<br><br>**TripPlanner:**<br>- `tp.ai_sessions` chặn đúng logic: theo tháng, có advisory lock, phiên đã đếm thì chạy tiếp (`TP/backend/shared/tenant_sessions.py:101-129`).<br>- Nhưng seed = NULL (không giới hạn) cho Hosted và Pro (`CIS/api/migrations/355_…sql:196,199`).<br>- Traveller thấy câu **"Today's AI writing limit is reached"**, sai chu kỳ vì quota tính theo tháng (`TP/frontend/lib/aiNotices.ts:20-22`).<br>- Chat cap tenant 2 USD không gắn với gói (`TP/backend/shared/monthly_spend.py:99-102`, `TP/backend/config.py:299`).<br>- Đại lý không thấy gì: chỉ có log stdout (`tenant_sessions.py:122`).<br><br>**CRM:**<br>- Hard 100 %, có lock theo agency (`CRM/api/app/llm/gateway.py:331-414`).<br>- UI rõ ràng: "This month's AI budget is used up. Write this reply by hand." (`CRM/web/lib/i18nAiDraft.ts:44`), có meter và banner 75/90/100 (`AiSettingsView.tsx:72-106`).<br>- Mặc định = trần = 2 USD (`CRM/api/migrations/064_crm_settings_registry.sql:420-421`). Không gắn gói. Đường nâng gói chỉ là chữ "contact AA support" (`i18nAi.ts:18,43`). | Đúng (hard). | Hard theo gói; báo lý do cho đại lý; có link Billing/Upgrade; báo trước ở 75/90 %; không fail closed vì lỗi hạ tầng. | - CIS: đại lý không biết lý do bị dừng, Retry vô ích.<br>- TP: quota chưa có giá trị, câu thông báo sai, đại lý không được báo.<br>- CRM: budget không theo gói, trần 2 USD, không có flow nâng gói; cảnh báo 75/90 % API có trả nhưng web không hiển thị (`agency_ai.py:277`). | **Cao** (chạm thẳng khách trả tiền) | **AA-1117:**<br>(a) CIS/Studio: trạng thái riêng "Dừng vì hết ngân sách AI" + link Upgrade + ẩn Retry + thông báo cho owner đại lý (M).<br>(b) TP: sửa câu "Today's" thành câu theo tháng/theo gói; đặt quota cho từng gói; hiện usage TP trong Tenant 360 / CRM (M).<br>(c) CRM: budget lấy từ entitlement gói, trần theo gói, nút Upgrade, hiện cảnh báo 75/90 % trong panel draft (M). |
| 2 | **Cap connection (acc1, acc3, anthropic-direct, openai-direct) không được chặn khách; alert + tự failover** | **CIS gateway:**<br>- Cap ở `shared.llm_provider_connection.monthly_budget_usd`, policy `hard_stop` ở `shared.llm_connection_cost_policy` (`CIS/shared/cost_guard.py:418-475`). Không có hàng policy thì mặc định hard (`cost_guard.py:422,437`).<br>- Seed: acc3 100, anthropic-direct 150, openai-direct 10, acc1 100, tất cả **hard_stop=true** (`366_…sql:93-96,415-424`; `327_…sql:43-44,223`; `406_…sql:146,153-155`).<br>- Live 16/11: openai-direct 3,11/10 USD (925 call/24h).<br>- `hard_stop=true`: bỏ connection, failover sang deployment/rung kế (`vendor_route.py:419-427`, `client.py:1903-1908`). Nhưng **khi mọi rung đều cạn** thì `ConnectionBudgetExceeded` → job `stopped_budget` → đại lý thấy "Writing failed" (`client.py:443-450`).<br>- `hard_stop=false`: chỉ alert, **không failover**, vẫn tiêu tiếp trên connection đó (`cost_guard.py:452-454`).<br><br>**TP:** không đọc cap connection, chỉ đọc breaker lỗi (`TP/backend/shared/llm_breaker.py:3-17`). Route chỉ có Bedrock acc2/acc3, không có acc1 hay vendor API (`llm_gateway.py:611-621`).<br><br>**CRM:** không dùng `shared.llm_*`. Chỉ có 1 route Nova Lite acc2, là ngoại lệ "Dev only" (`INFRA/modules/environment/crm_llm.tf:1-10`). 1 `role_arn` mỗi process nên không failover chéo account được (`CRM/api/app/llm/providers/bedrock.py:104,160-164`). | Đúng (hard, có failover một phần). | Chế độ thứ ba: **bỏ connection khi chạm cap, failover, nhưng không bao giờ chặn ở rung cuối**; alert on-call khi rung cuối vượt cap. | - Hiện chỉ có 2 chế độ: hard (failover, nhưng cạn hết thì chặn khách) hoặc alert-only (không chặn, nhưng cũng không failover).<br>- Seed không phân biệt môi trường.<br>- TP và CRM không có chuỗi failover đa account/vendor. | **Cao** | **AA-1113:**<br>(a) thêm `on_cap = failover_then_continue` (cờ theo connection, sửa trong admin Providers › Connections), alert on-call ở rung cuối; prod mặc định chế độ này (M).<br>(b) TP: thêm acc1 (role invoker + ExternalId) và vendor API vào route, đọc cap connection như CIS (M–L).<br>(c) CRM: route prod được duyệt + failover acc1 → acc3 → vendor (L, gắn **AA-1004**). |
| 3 | **Chỉ circuit breaker theo bất thường được dừng call** (bội số chi tiêu ngày, giá trị trong Platform Settings, alert on-call) | **Chưa có.**<br>- `CIS/shared/llm_client/breaker.py:1-40` chỉ ngắt theo **lỗi** (bị từ chối, throttle, outage), không đọc chi tiêu.<br>- Central cap `llm/app:cis` = p95 × 1,5 nhưng là số USD cố định lúc seed và chỉ alert (`340_…sql:25,103-105`).<br><br>**Ngược lại, đang có cap USD cố định chặn MỌI tenant:**<br>- TP app 5 USD/ngày (`CIS/api/migrations/414_…sql:93-94`; `TP/backend/shared/llm_gateway.py:1417-1437`): chạm thì traveller mọi đại lý nhận narration cơ bản, kèm câu "Today's AI writing limit".<br>- TP chat 2 USD/tháng cho cả app (`TP/backend/config.py:298`, `monthly_spend.py:95-98`).<br>- CRM daily app budget, nếu đặt, chặn mọi agency với `app_budget_exhausted`. UI báo nhầm thành "This month's AI budget is used up" (`CRM/web/lib/aiDraft.ts:86-89`).<br>- TP và CRM fail closed khi không đọc được chi tiêu (`llm_gateway.py:1424-1430`). | Cap cố định là chấp nhận được ở Dev. | Breaker: chi tiêu ngày > baseline × bội số (key Platform Settings) thì dừng + alert on-call + nút reset; mọi cap cố định khác chuyển sang alert-only ở prod. | - Chưa có breaker theo bất thường.<br>- Các cap cố định đang đóng đúng vai mà prod cấm.<br>- CRM báo sai lý do. | **Cao** | **AA-1113:**<br>(a) breaker chi tiêu bất thường dùng chung (gói core `aa_llm`), key `platform.llm.anomaly_multiple`, cửa sổ baseline 14 ngày, alert SNS on-call, reset trong admin (M–L).<br>(b) TP/CRM: cap app chuyển sang alert-only khi env = prod, hoặc thay bằng breaker (S).<br>(c) CRM: thêm câu riêng cho `app_budget_exhausted` / `spend_unreadable` (S). |
| 4 | **AWS Budgets = chỉ e-mail cảnh báo** | **Đúng.** Không có `aws_budgets_budget_action`, SCP hay SSM stop nào.<br>- acc1 `INFRA/accounts/acc1-bedrock/cost_guard.tf:11,101-126` (ghi "NO budget action").<br>- acc3 `acc3-bedrock/cost_guard.tf:23,52-85`, anomaly immediate ≥ 15 USD (`cost_anomaly_immediate.tf:20-80`).<br>- acc2 `aa365/observability.tf:145-189,225-258`, anomaly ≥ 5 USD (`cost_anomaly.tf:41-70`).<br>- acc4 `management/budgets.tf:30-83`.<br>- Có test cấm budget action (`tools/terraform/tests/test_aa1096_acc1_cost_guard.py:71`). | Đúng. | Giữ nguyên; tách budget dev/prod. | - Budget theo app chỉ lọc tag `App` (`observability.tf:225-240`), nên dev + prod sẽ dùng chung một budget (ví dụ crm 35 USD).<br>- AWS Budgets không thấy chi tiêu Anthropic API / OpenAI trực tiếp. | Thấp | **AA-1004:** thêm lọc tag `Environment` hoặc budget riêng cho prod (S). Chi tiêu vendor trực tiếp sẽ được breaker ở điểm 3 che. |
| 5 | **Batch nội bộ (wave, A/B, writer proof) giữ hard cap mỗi run** | **Writer proof:** hard đầy đủ (`CIS/services/writer_proof/spend.py:1-16,64-98`):<br>- cần `--confirm` + `--cap-usd`;<br>- cap ≤ D12 (5/8/5/15/33 USD);<br>- tính cả tiền đang giữ chỗ;<br>- fail closed.<br><br>**Writing memory:** cap tháng 25 USD (`writing_memory/budget.py:35-49`).<br><br>**Wave S1:** **không có cap USD tự động mỗi run/wave phía LLM**. Chỉ có:<br>- trần số tour 2000 (`admin_waves.py:46-52`);<br>- ước tính trước khi chạy;<br>- điều kiện dừng **sau** wave (`skill/aa-wave-rerun/SKILL.md:88-93`).<br>Central cap `job:s1_rewrite` / `adhoc` / `eval` chưa được seed; cap mới mặc định alert-only (`BudgetsTab.tsx:16`).<br><br>TP và CRM không có batch. | Writer proof đúng; wave dựa vào quy trình tay. | Mỗi wave/A-B/adhoc có cap USD hard tự động. | Thiếu hard cap tự động cho wave và adhoc. Hiện chỉ cap connection chặn wave, mà đó là tình cờ. | Trung bình (rủi ro tiền, không chạm khách) | **AA-1113:** seed central cap hard cho `job:s1_rewrite` (mỗi run/wave, lấy từ trần đã duyệt), `adhoc_*`, `eval`; wave object ghi `cap_usd` bắt buộc (S–M). |

---

## 2. Cái sẽ làm đau một đại lý trả tiền nếu lên prod hôm nay

1. **Cap cố định cấp app chặn mọi đại lý.**
   - TP 5 USD/ngày và chat 2 USD/tháng (`414:93-94`, `TP/backend/config.py:298`): một đại lý đông khách hay một bot là đủ làm cạn AI của tất cả đại lý.
   - CRM daily app budget (nếu đặt) chặn mọi agency, kèm câu báo sai "hết budget tháng của bạn" (`CRM/web/lib/aiDraft.ts:86-89`).
2. **Connection cap mặc định hard stop.** openai-direct chỉ có 10 USD, live đã 3,11. Cạn hết rung failover thì job Studio thành `stopped_budget`, đại lý thấy "Writing failed" (`client.py:443-450`).
3. **Dừng vì budget ở Content studio là "im lặng" với đại lý.** Không nói lý do, Retry vô ích, phải chờ staff duyệt tay (`catalogApi.ts:110`, `cost_guard.py:797-813`).
4. **CRM: 2 USD/tháng mỗi agency, không gắn gói, không có nút nâng gói.** AI mặc định tắt và cần staff cấp `ai_assist` (`agency_ai.py:228-230`, `ai_drafts.py:52-60`). Route AI là Nova Lite acc2 "Dev only": một lần acc2 throttle là hiện "reply by hand" (`crm_llm.tf:10`, `providers/bedrock.py:1-6`).
5. **TP fail closed khi không đọc được quota/budget/chi tiêu.** AI của đại lý tắt vì lỗi hạ tầng mà đại lý không hay (`tenant_sessions.py:110-116,126-128`; `llm_gateway.py:1424-1430`). Thêm vào đó, route TP chỉ có acc2/acc3, mà acc3 đang bị AWS chặn 7 model.
6. **Session TP tạo tự do** (`TP/backend/assembly/guest_session.py:118-122`), mỗi session mới tốn 1 suất `tp.ai_sessions`. Bot nhiều IP có thể đốt hết quota tháng của một đại lý. WAF có giảm bớt (`INFRA/accounts/aa365/tripplanner_web_edge.tf:35-47`), nhưng narration không có giới hạn theo IP trong app.
7. **Seed migration không phân biệt môi trường, và prod chưa có root Terraform** (`INFRA/accounts/aa365/environment.tf:2-3`). Chạy migration y như Dev thì prod thừa hưởng toàn bộ hard cap của Dev. Số dự phòng trong code cũng là số Dev (`TP/backend/config.py:245,298-299`).

---

## 3. Đề xuất lát việc

Cỡ việc: S ≈ ½–1 ngày, M ≈ 2–3 ngày, L ≈ 1 tuần.

| Issue | Lát việc | Repo | Cỡ |
|---|---|---|---|
| **AA-1113** (gateway) | G1. Chế độ cap connection `failover_then_continue` + alert on-call ở rung cuối; cờ sửa trong admin Providers › Connections | CIS (+ migration) | M |
| AA-1113 | G2. Breaker chi tiêu bất thường dùng chung (`aa_llm` core): baseline × bội số trong Platform Settings, alert SNS, reset trong admin; CIS + TP + CRM gọi chung | CIS, TP, CRM | M–L |
| AA-1113 | G3. Cap app TP/CRM đổi sang alert-only ở prod; CRM thêm câu riêng cho `app_budget_exhausted` / `spend_unreadable` | TP, CRM | S |
| AA-1113 | G4. Seed central cap hard cho `job:s1_rewrite` / `adhoc_*` / `eval`; wave bắt buộc có `cap_usd` | CIS | S–M |
| AA-1113 | G5. Route TP thêm acc1 + vendor API, đọc cap connection như CIS (sửa luôn docstring "acc1 retired" ở `llm_gateway.py:23-24`) | TP, INFRA | M–L |
| **AA-1117** (go-live) | L1. Studio: trạng thái "Dừng vì hết ngân sách AI" + link Upgrade + ẩn Retry + thông báo cho owner đại lý | CRM web, CIS | M |
| AA-1117 | L2. TP: câu thông báo theo tháng/theo gói, giá trị quota cho từng gói, usage + cảnh báo phía đại lý | TP, CIS, CRM | M |
| AA-1117 | L3. CRM: budget AI lấy từ entitlement gói, nút Upgrade, cảnh báo 75/90 % trong panel draft + e-mail owner | CRM | M |
| AA-1117 | L4. Đổi fail closed thành degrade có alert khi lỗi đọc quota/budget cho tenant trả tiền (giữ fail closed ở Dev) | TP, CIS | S |
| **AA-1004** (prod) | P1. Root Terraform prod + cấu hình riêng cho prod (seed settings/policy prod, không chép Dev) | INFRA, migrations | L |
| AA-1004 | P2. Route LLM CRM được duyệt cho prod + failover chéo account (bỏ ngoại lệ Nova Lite "Dev only") | CRM, INFRA | L |
| AA-1004 | P3. AWS Budgets tách theo tag `Environment` (dev/prod) | INFRA | S |

Thứ tự gợi ý:
1. **G1 + G2 + G3** trước, vì đây là phần đúng nhất với chính sách và chặn khách nặng nhất.
2. Rồi **L1–L4**, phần UI cho khách.
3. **P1–P3** đi cùng AA-1004.
4. **G4** làm được ngay ở Dev, rủi ro thấp.
